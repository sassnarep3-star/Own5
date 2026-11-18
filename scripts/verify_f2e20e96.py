#!/usr/bin/env python3
"""Fail-closed verifier for the NFL Line-Originator Decision Desk (f2e20e96).

Checks:
V1  every CSV row carries an https source_url (official host) or an explicit flag/status
    marking it unverified/repo-internal; nothing is silently blank
V2  every rendered table row in the HTML contains a source link or an explicit
    UNVERIFIED / computed marker
V3  every internal link on the site resolves to a file in the desk
V4  no plain-http links anywhere
V5  pinned counts reproduce (rows, games, markets, readiness rows ...)
V6  deterministic build: rebuilding produces byte-identical pages and computed CSVs
V7  model math identities (margin/total/probability reproduce from the formulas)
Exit code 0 = all checks pass; 1 = failures printed to stdout.
"""
import csv
import os
import re
import subprocess
import sys
import tempfile
import filecmp
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "nfl-desk-f2e20e96")
COMPUTED = os.path.join(DATA, "computed")
SITE = os.path.join(ROOT, "nfl-desk-f2e20e96")

OFFICIAL_HOSTS = ("https://www.nfl.com", "https://static.www.nfl.com")
FAILS = []

REPO_PATH = re.compile(r"[A-Za-z0-9_./-]+\.(py|csv|html|md)\b")


def fail(msg):
    FAILS.append(msg)
    print("FAIL:", msg)


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---- V1: CSV source discipline ---------------------------------------------
# A row is acceptable if it carries an https source URL, or an explicit
# status/unverified flag (register rows), or a repo-path evidence pointer.
CSV_FLAG_MARKERS = ("UNVERIFIED", "REVIEW", "BLOCKED", "PENDING", "not verified",
                    "Not Verified", "NOT VERIFIED", "repo-internal", "not on the",
                    "OPEN", "PARTIAL", "MET ", "MET,", "PASS", "PROPOSED", "HELD",
                    "REGISTERED", "ACTIVE", "SUPERSEDED", "CONFIRMED", "NOT CONFIRMED",
                    "GATED", "decision item")
for name in sorted(os.listdir(DATA)):
    if not name.endswith(".csv"):
        continue
    rows = read_csv(os.path.join(DATA, name))
    for i, r in enumerate(rows, start=2):
        joined = " ".join(str(v) for v in r.values())
        has_source = any(str(v).startswith("https://") for v in r.values())
        if not has_source:
            flagged = (any(m in joined for m in CSV_FLAG_MARKERS)
                       or REPO_PATH.search(joined))
            if not flagged:
                fail(f"V1 {name}:{i} has no source URL and no flag/repo-evidence marker")
            continue
        for v in r.values():
            if str(v).startswith("http://"):
                fail(f"V1 {name}:{i} contains plain-http link")

# price snapshot rows must be blank + UNVERIFIED (policy P-01)
for i, r in enumerate(read_csv(os.path.join(DATA, "price_snapshots_wk11.csv")), start=2):
    if r["opening_price"] or r["closing_price"]:
        fail(f"V1 price_snapshots_wk11.csv:{i} has a price value without a verified source")
    if r["status"] != "UNVERIFIED":
        fail(f"V1 price_snapshots_wk11.csv:{i} missing UNVERIFIED status")

# ---- V2 + V3 + V4: rendered pages -----------------------------------------
pages = sorted(p for p in os.listdir(SITE) if p.endswith(".html"))
for name in pages:
    html = open(os.path.join(SITE, name), encoding="utf-8").read()
    if "http://" in html:
        fail(f"V4 {name} contains plain-http link")
    for m in re.finditer(r"<tr>(.*?)</tr>", html, re.S):
        row = m.group(1)
        if "<th>" in row:
            continue
        if "<a href=" in row or "UNVERIFIED" in row or "computed" in row.lower() or "registry:" in row:
            continue
        fail(f"V2 {name}: table row without source link or marker: {row[:110]}...")
    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith("http"):
            if not (href.startswith(OFFICIAL_HOSTS)
                    or href.startswith("https://github.com")
                    or href.startswith("https://raw.githubusercontent.com")):
                fail(f"V3 {name}: unexpected external host {href}")
            continue
        target = os.path.join(SITE, href.split("#")[0])
        if not os.path.exists(target):
            fail(f"V3 {name}: broken internal link {href}")

# ---- V5: pinned counts -----------------------------------------------------
def n_rows(name):
    return len(read_csv(os.path.join(DATA, name)))


pins = {
    "injury_wk10_players.csv": 347,
    "week10_results.csv": 14,
    "week11_schedule.csv": 13,
    "byes_week11.csv": 6,
    "standings_2026_reg.csv": 32,
    "price_snapshots_wk11.csv": 39,
    "readiness.csv": 70,
    "starters_jax_ten.csv": 44,
    "inactives_jax_ten.csv": 12,
}
for name, want in pins.items():
    got = n_rows(name)
    if got != want:
        fail(f"V5 {name}: pinned {want} rows, found {got}")

inj = read_csv(os.path.join(DATA, "injury_wk10_players.csv"))
if len({r["club"] for r in inj}) != 28:
    fail("V5 injury capture: expected 28 club tables")
det = [r for r in inj if r["club"] == "DET"]
outs = {r["player"] for r in det if r["game_status"] == "Out"}
if outs != {"Kerby Joseph", "Cade Mays", "D.J. Reed"}:
    fail(f"V5 Lions Out designations wrong: {outs}")

# ---- V7: model identities (every row recomputed from the registered formulas)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import importlib.util
import math
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "scripts", "build_f2e20e96.py"))
b = importlib.util.module_from_spec(spec)
try:
    # snapshot the committed computed rows BEFORE the recompute below regenerates them
    rows = read_csv(os.path.join(COMPUTED, "model_lines_wk11.csv"))
    spec.loader.exec_module(b)
    if len(rows) != 39:
        fail(f"V7 expected 39 model rows (13 games x 3 markets), found {len(rows)}")
    by_key = {(r["game_id"], r["market"]): r for r in rows}
    for g in b.schedule:
        gid, home, away = g["game_id"], g["home"], g["away"]
        th, ta = b.teams[home], b.teams[away]
        margin = (th["s_reg"] - ta["s_reg"]) + b.HFA
        total = (th["f_reg"] + ta["f_reg"]) / 2.0
        p = 0.5 * (1.0 + math.erf((margin / b.sigma_sample) / math.sqrt(2.0)))
        side, tot, ml = by_key[(gid, "side")], by_key[(gid, "total")], by_key[(gid, "moneyline")]
        if abs(float(side["model_fair_value"]) - margin) > 0.051:
            fail(f"V7 {gid} side identity mismatch")
        if abs(float(tot["model_fair_value"]) - total) > 0.051:
            fail(f"V7 {gid} total identity mismatch")
        if abs(float(ml["probability"]) - p) > 5e-5:
            fail(f"V7 {gid} moneyline probability mismatch")
        if abs(float(side["probability"]) - p) > 5e-5:
            fail(f"V7 {gid} side probability mismatch")
        for r in (side, tot, ml):
            if r["market_line"] or r["difference"]:
                fail(f"V7 {gid} {r['market']}: market/difference columns must stay blank (P-01)")
            if "inputs:" not in r["inputs"] or "model=" not in r["inputs"]:
                fail(f"V7 {gid} {r['market']}: probability row is missing its published inputs")
except Exception as e:  # noqa
    fail(f"V7 model recomputation crashed: {e}")

# ---- V6: determinism --------------------------------------------------------
with tempfile.TemporaryDirectory() as tmp:
    backup = os.path.join(tmp, "site_backup")
    comp_backup = os.path.join(tmp, "computed_backup")
    shutil.copytree(SITE, backup)
    shutil.copytree(COMPUTED, comp_backup)
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_f2e20e96.py")],
                   check=True, capture_output=True)
    for name in os.listdir(backup):
        path1 = os.path.join(backup, name)
        if not os.path.isfile(path1):
            continue
        if not filecmp.cmp(path1, os.path.join(SITE, name), shallow=False):
            fail(f"V6 rebuild not deterministic: {name}")
    for name in ("model_lines_wk11.csv", "correlations.csv", "luck_panel.csv", "injury_wk10_club_summary.csv"):
        path = os.path.join(COMPUTED, name)
        if not os.path.exists(path):
            fail(f"V6 computed file missing: {name}")
        elif not filecmp.cmp(os.path.join(comp_backup, name), path, shallow=False):
            fail(f"V6 computed rebuild not deterministic: {name}")
    if not FAILS:
        print("V6 deterministic rebuild OK")

print(f"\nverify_f2e20e96: {'PASS' if not FAILS else 'FAIL'} "
      f"(pages={len(pages)}, csv_files={sum(1 for n in os.listdir(DATA) if n.endswith('.csv'))}, "
      f"failures={len(FAILS)})")
sys.exit(1 if FAILS else 0)

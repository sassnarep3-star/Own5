#!/usr/bin/env python3
"""Fail-closed verifier for the 7e228db8 desk.

Checks (any failure exits non-zero):
  1. every page exists and internal links/anchors resolve (no broken links);
  2. external links are https and point to official or repo hosts;
  3. pinned data counts (drift alarm): standings 32, results feed 150, schedule 13,
     injuries 255 (incl. 2 'No Injuries Reported' markers), lines 13, snapshots 39,
     correlations 4 (n=32 each), readiness 80, flagged 19, questions 10, suggestions 12,
     leaderboard 6, sweep 37;
  4. model invariants: fair-cover/fair-over probabilities near 0.5, decimal odds = 1/p,
     inputs hash present on every row, snapshot ids match line markets;
  5. every data row of the desk's CSVs carries a source_url, or the row is a policy
     blank whose flag text names the flag register (F7-P01/F7-xx);
  6. reconciliation gate: build_context standings_reconciled is true.
"""
from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "nfl-desk-7e228db8"

ALLOWED_HOSTS = {
    "www.nfl.com", "nfl.com", "static.www.nfl.com",
    "github.com", "sassnarep3-star.github.io",
    "operations.nfl.com", "media.nfl.com", "api.nfl.com",
}

failures: list[str] = []
checks = 0


def check(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        failures.append(msg)


def rows(rel: str) -> list[dict]:
    with io.open(DATA / rel, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---- pinned counts (drift alarm) -------------------------------------------
PINNED = {
    "standings_2026_wk10.csv": 32,
    "results_feed_2026_through_wk10.csv": 150,
    "schedule_2026_week11.csv": 13,
    "injuries_2026_week11.csv": 255,
    "lines_week11.csv": 13,
    "price_snapshots.csv": 39,
    "correlations.csv": 4,
    "readiness.csv": 80,
    "flagged.csv": 19,
    "questions.csv": 10,
    "suggestions.csv": 12,
    "leaderboard.csv": 6,
    "verifier_sweep.csv": 37,
}
for name, n in PINNED.items():
    r = rows(name)
    check(len(r) == n, f"drift alarm: {name} has {len(r)} rows, pinned count is {n}")

# ---- reconciliation gate ----------------------------------------------------
import json

ctx = json.loads((DATA / "build_context.json").read_text(encoding="utf-8"))
check(ctx.get("standings_reconciled") is True, "build_context: standings reconciliation gate is not true")
check(ctx.get("n_finals") == 150, "build_context: n_finals drifted from 150")

# ---- model invariants -------------------------------------------------------
for g in rows("lines_week11.csv"):
    gid = g["game_id"]
    check(bool(re.fullmatch(r"[0-9a-f]{64}", g["inputs_sha256"])), f"{gid}: inputs_sha256 malformed")
    check(g["market_spread"] == "" and g["market_total"] == "" and g["market_p_home"] == "",
          f"{gid}: market columns must be blank (F7-P01)")
    check(g["spread_diff"] == "" and g["total_diff"] == "", f"{gid}: diff columns must be blank")
    p = float(g["p_home_win_novig"])
    check(0.05 < p < 0.95, f"{gid}: p_home_win outside plausible range: {p}")
    odh, oda = float(g["fair_odds_home_decimal"]), float(g["fair_odds_away_decimal"])
    # published odds are rounded to 2dp; p is stored to 3dp, so allow (1/p)^2*dp of slack
    tol_h = max(0.006, odh ** 2 * 0.001)
    tol_a = max(0.006, oda ** 2 * 0.001)
    check(abs(odh - 1.0 / p) < tol_h, f"{gid}: home decimal odds != 1/p")
    check(abs(oda - 1.0 / (1.0 - p)) < tol_a, f"{gid}: away decimal odds != 1/(1-p)")
    pc, po = float(g["p_home_cover_fair"]), float(g["p_over_fair"])
    check(0.45 <= pc <= 0.55, f"{gid}: p_cover at fair line not ~0.5: {pc}")
    check(0.45 <= po <= 0.55, f"{gid}: p_over at fair line not ~0.5: {po}")
    check(g["kickoff_utc"] >= "2026-11-20T01:15:00Z", f"{gid}: kickoff before first Week 11 game")

markets = {s["snapshot_id"] for s in rows("price_snapshots.csv")}
line_ids = {g["game_id"] for g in rows("lines_week11.csv")}
for gid in line_ids:
    for mk in ("SIDE_SPREAD", "TOTAL", "MONEYLINE"):
        check(f"{gid}:{mk}" in markets, f"snapshot missing for {gid}:{mk}")

for c in rows("correlations.csv"):
    check(int(c["n"]) == 32, f"correlation {c['pair']}: n != 32")
    check(bool(c["ci95_low"]) and bool(c["ci95_high"]), f"correlation {c['pair']}: missing CI")
    check("nfl.com" in c["source_url"], f"correlation {c['pair']}: source not nfl.com")

# ---- row provenance: source_url or explicit flag ----------------------------
FLAG_RE = re.compile(r"F7-(P01|\d{2})")
for name in ("lines_week11.csv", "price_snapshots.csv", "standings_2026_wk10.csv",
             "results_feed_2026_through_wk10.csv", "schedule_2026_week11.csv",
             "injuries_2026_week11.csv", "readiness.csv", "flagged.csv",
             "questions.csv", "suggestions.csv", "correlations.csv", "ratings_2026_wk11.csv"):
    for i, r in enumerate(rows(name), 2):
        src = r.get("source_url", "")
        joined = " ".join(str(v) for v in r.values())
        has_flag = bool(FLAG_RE.search(joined))
        check(bool(src) or has_flag,
              f"{name} row {i}: no source_url and no explicit flag")

# ---- pages and links --------------------------------------------------------
PAGES = ["index.html", "lines.html", "price-store.html", "results.html", "ratings.html",
         "correlations.html", "injuries.html", "schedule.html", "leaderboard.html",
         "readiness.html", "suggestions.html", "questions.html", "flagged.html",
         "sources.html", "executive-summary.html"]
for p in PAGES:
    check((HERE / p).exists(), f"missing page {p}")

href_re = re.compile(r'(?:href|src)="([^"]+)"')
for p in PAGES:
    text = (HERE / p).read_text(encoding="utf-8")
    for m in href_re.finditer(text):
        url = m.group(1)
        if url.startswith(("#", "mailto:")):
            continue
        if url.startswith("http"):
            host = urlparse(url).netloc
            check(host in ALLOWED_HOSTS, f"{p}: external link to non-allowed host {host}")
            check(url.startswith("https://"), f"{p}: non-https external link {url}")
        else:
            target = url.split("#")[0]
            check(target == "" or (HERE / target).exists() or (HERE / target).is_dir(),
                  f"{p}: broken internal link {url}")

# raw excerpts must exist and be hashed in the manifest
man = rows("raw/manifest.csv")
for m in man:
    ex = HERE.parent / "data" / "nfl-desk-7e228db8" / m["excerpt_file"]
    if m["excerpt_file"] == "(file in repo)":
        check(m["excerpt_sha256"] == "n/a", "manifest: repo-file row must carry hash n/a")
        continue
    check(ex.exists(), f"manifest excerpt missing: {m['excerpt_file']}")
    if m["excerpt_sha256"] not in ("n/a",):
        check(re.fullmatch(r"[0-9a-f]{64}", m["excerpt_sha256"] or "") is not None,
              f"manifest: malformed hash for {m['excerpt_file']}")

# pre-registration artefacts exist
check((DATA / "model_inputs.json").exists(), "model_inputs.json missing")
spec = json.loads((DATA / "model_inputs.json").read_text(encoding="utf-8"))
check(spec["model_spec_version"].startswith("v1-frozen-2026-11-19"), "model spec version drifted")
check(spec["order"] == "side first, then total, then moneyline", "spec: origination order drifted")
check(spec["corpus_finals"] == 150, "spec: corpus drifted from 150")

print(f"verify: {checks} checks, {len(failures)} failures")
for f in failures[:40]:
    print("FAIL", f)
if failures:
    sys.exit(1)
print("PASS all desk checks")

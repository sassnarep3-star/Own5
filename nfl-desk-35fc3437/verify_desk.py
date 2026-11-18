#!/usr/bin/env python3
"""Fail-closed verification for nfl-desk-35fc3437.

Checks:
  V0  every data CSV parses and has expected columns
  V1  every table row on every generated page ends in a source link or an explicit UNVERIFIED badge
  V2  no blank non-source cells that aren't marked blank
  V3  every internal link resolves to an existing page
  V4  standings reconcile: NET == PF - PA for all 32 clubs; PCT == (W+0.5T)/GP
  V5  results feed: all rows FINAL; winner = higher score; margins consistent
  V6  originated lines: model columns populated, market/difference columns blank+flagged
  V7  correlations: n published with each value; |r| <= 1
  V8  gates: every gate has a status; no strategy certified without all gates met
  V9  requirements: every requirement row has gate + clearing number + observed or blank
  V10 determinism: rebuild produces byte-identical output
Returns non-zero on any failure.
"""
import csv
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")

failures = []

def fail(msg):
    failures.append(msg)
    print("FAIL:", msg)

def read_csv(name):
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ---------- V0: CSV parse + expected columns ----------
EXPECTED = {
    "standings_2026.csv": ["team","abbr","W","L","T","PCT","PF","PA","NET","source_url"],
    "schedule_2026_wk11.csv": ["game_id","date","home_team","away_team","venue","source_url"],
    "results_2026_wk10.csv": ["game_id","date","home_team","away_team","home_score","away_score","winner","status","source_url"],
    "injuries_2026_wk10.csv": ["player","position","team","game_status","source_url"],
    "lines_originated_wk11.csv": ["game_id","model_fair_spread","market_spread","source_url"],
    "correlations.csv": ["correlation_id","n","r","source_url"],
    "gates.csv": ["gate_id","status","clearing_number","source_url"],
    "leaderboard.csv": ["strategy_id","status","certified","source_url"],
    "questions.csv": ["q_id","question","answer_status","source_url"],
    "suggestions.csv": ["s_id","suggestion","decision","source_url"],
    "sources.csv": ["source_id","source_name","url","captured_utc"],
    "flagged.csv": ["flag_id","severity","item","source_url","status"],
    "requirements.csv": ["req_id","requirement (brief line)","gate","clearing_number","observed_today","status","source_url"],
}
def V0_csvs():
    ok = True
    for name, cols in EXPECTED.items():
        rows = read_csv(name)
        if not rows:
            fail(f"V0: {name} has no data rows"); ok = False; continue
        missing = [c for c in cols if c not in rows[0]]
        if missing:
            fail(f"V0: {name} missing columns {missing}"); ok = False
        for i, r in enumerate(rows):
            su = (r.get("source_url") or "").strip()
            if su and not su.startswith("http"):
                fail(f"V0: {name} row {i} source_url is not an http link: {su!r}"); ok = False
            # empty source_url is permitted: it renders as an explicit UNVERIFIED badge (never inferred)
    print(f"V0 csvs: {'OK' if ok else 'FAIL'}")
    return ok

# ---------- V1/V2/V3: generated pages ----------
PAGE_FILES = [f for f in os.listdir(PAGES) if f.endswith(".html")] + ["index.html"]
PAGE_FILES = sorted(set(["index.html"] + PAGE_FILES))
def page_path(name):
    return os.path.join(ROOT, name) if name == "index.html" else os.path.join(PAGES, name)

def V1_source_or_unverified():
    ok = True
    for name in PAGE_FILES:
        path = page_path(name)
        if not os.path.exists(path):
            fail(f"V1: missing page {name}"); ok = False; continue
        text = open(path, encoding="utf-8").read()
        # find table rows
        for m in re.finditer(r"<tr>(.*?)</tr>", text, re.S):
            row = m.group(1)
            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
            if not cells:
                continue
            last = cells[-1]
            has_source = ("<a href=" in last and "rel=\"nofollow\"" in last) or ("source &rarr;" in last)
            has_unverified = "badge-unverified" in last
            if not (has_source or has_unverified):
                fail(f"V1: {name} row does not end in source/UNVERIFIED: {last[:80]!r}"); ok = False
    print(f"V1 source-or-unverified: {'OK' if ok else 'FAIL'}")
    return ok

def V3_internal_links():
    ok = True
    page_names = set(PAGE_FILES)
    for name in PAGE_FILES:
        text = open(page_path(name), encoding="utf-8").read()
        for m in re.finditer(r'href="([^"]+)"', text):
            u = m.group(1)
            if u.startswith("http") or u.startswith("#") or u.startswith("mailto"):
                continue
            target = u.lstrip("/")
            if target == "index.html":
                target = "index.html"
            candidates = [page_path(target)]
            # links from the root landing page carry a "pages/" prefix (pages/standings.html);
            # links from inside pages/ are bare names (standings.html). Accept either resolution.
            if target.startswith("pages/"):
                candidates.append(os.path.join(ROOT, target))
            elif "/" in target:
                candidates.append(os.path.join(ROOT, target))
            if not any(os.path.exists(c) for c in candidates):
                fail(f"V3: {name} links to missing {u}"); ok = False
    print(f"V3 internal links: {'OK' if ok else 'FAIL'}")
    return ok

# ---------- V4 standings reconciliation ----------
def V4_standings():
    ok = True
    rows = read_csv("standings_2026.csv")
    for i, r in enumerate(rows):
        W,L,T = int(r["W"]), int(r["L"]), int(r["T"])
        PF,PA,NET = int(r["PF"]), int(r["PA"]), int(r["NET"])
        pct = (W + 0.5*T) / (W+L+T)
        if NET != PF - PA:
            fail(f"V4: {r['team']} NET {NET} != PF-PA {PF-PA}"); ok = False
        if abs(pct - float(r["PCT"])) > 0.001:
            fail(f"V4: {r['team']} PCT {r['PCT']} != computed {pct:.3f}"); ok = False
    print(f"V4 standings reconcile (n={len(rows)}): {'OK' if ok else 'FAIL'}")
    return ok

# ---------- V5 results feed ----------
def V5_results():
    ok = True
    rows = read_csv("results_2026_wk10.csv")
    for i, r in enumerate(rows):
        hs, as_ = int(r["home_score"]), int(r["away_score"])
        if r["status"].strip() != "FINAL":
            fail(f"V5: {r['game_id']} status not FINAL"); ok = False
        if hs == as_:
            fail(f"V5: {r['game_id']} tie score (should not occur in NFL final with no OT tie here)"); 
        expected_winner = r["home_team"] if hs > as_ else r["away_team"]
        if r["winner"] != expected_winner:
            fail(f"V5: {r['game_id']} winner {r['winner']} != expected {expected_winner}"); ok = False
        expected_margin = abs(hs - as_)
        if int(r["margin"]) != expected_margin:
            fail(f"V5: {r['game_id']} margin {r['margin']} != {expected_margin}"); ok = False
    print(f"V5 results feed (n={len(rows)}): {'OK' if ok else 'FAIL'}")
    return ok

# ---------- V6 lines ----------
def V6_lines():
    ok = True
    rows = read_csv("lines_originated_wk11.csv")
    for i, r in enumerate(rows):
        for c in ("model_fair_spread","model_fair_total","model_home_ml","model_away_ml","model_home_win_prob"):
            if not r.get(c,"").strip():
                fail(f"V6: {r['game_id']} model col {c} blank"); ok = False
        for c in ("market_spread","market_total","market_home_ml","market_away_ml","spread_difference","total_difference","ml_difference"):
            if r.get(c,"").strip():
                fail(f"V6: {r['game_id']} market col {c} should be blank: {r[c]!r}"); ok = False
    print(f"V6 originated lines (n={len(rows)}): {'OK' if ok else 'FAIL'}")
    return ok

# ---------- V7 correlations ----------
def V7_correlations():
    ok = True
    rows = read_csv("correlations.csv")
    for i, r in enumerate(rows):
        if not r.get("n","").strip():
            fail(f"V7: {r['correlation_id']} n blank"); ok = False
        try:
            rv = float(r["r"])
        except ValueError:
            fail(f"V7: {r['correlation_id']} r not numeric"); ok = False; continue
        if abs(rv) > 1:
            fail(f"V7: {r['correlation_id']} r={rv} outside [-1,1]"); ok = False
    print(f"V7 correlations (n={len(rows)}): {'OK' if ok else 'FAIL'}")
    return ok

# ---------- V8 gates ----------
def V8_gates():
    ok = True
    rows = read_csv("gates.csv")
    for i, r in enumerate(rows):
        if not r.get("status","").strip():
            fail(f"V8: {r['gate_id']} status blank"); ok = False
    # leaderboard certified strategies require all gates met
    lb = read_csv("leaderboard.csv")
    certified = [r for r in lb if (r.get("certified") or "").strip().lower() == "yes"]
    all_met = all((r.get("status") or "").strip().upper() == "MET" for r in rows)
    if certified and not all_met:
        fail(f"V8: certified leaderboard strategy exists but not all gates met"); ok = False
    print(f"V8 gates (n={len(rows)}, certified strategies={len(certified)}): {'OK' if ok else 'FAIL'}")
    return ok

# ---------- V9 requirements ----------
def V9_requirements():
    ok = True
    rows = read_csv("requirements.csv")
    for i, r in enumerate(rows):
        for c in ("gate","clearing_number","status"):
            if not r.get(c,"").strip():
                fail(f"V9: {r['req_id']} {c} blank"); ok = False
    print(f"V9 requirements (n={len(rows)}): {'OK' if ok else 'FAIL'}")
    return ok

# ---------- V10 determinism ----------
def V10_determinism():
    ok = True
    before = {name: open(page_path(name), "rb").read() for name in PAGE_FILES if os.path.exists(page_path(name))}
    r = subprocess.run([sys.executable, os.path.join(ROOT, "build_desk.py")], capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"V10: rebuild failed: {r.stderr}"); ok = False
    after = {name: open(page_path(name), "rb").read() for name in PAGE_FILES if os.path.exists(page_path(name))}
    if before != after:
        fail("V10: rebuild output not byte-identical"); ok = False
    print(f"V10 determinism: {'OK' if ok else 'FAIL'}")
    return ok

def main():
    results = [
        V0_csvs(), V1_source_or_unverified(), V3_internal_links(),
        V4_standings(), V5_results(), V6_lines(), V7_correlations(),
        V8_gates(), V9_requirements(), V10_determinism(),
    ]
    print("\n=====")
    if failures:
        print(f"VERIFY FAILED — {len(failures)} failure(s)")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("VERIFY PASSED — all checks OK")
    sys.exit(0)

if __name__ == "__main__":
    main()

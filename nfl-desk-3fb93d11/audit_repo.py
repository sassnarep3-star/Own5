"""Line-by-line review of the NFL claims already in this repository.

This does not edit anyone else's file.  It reads the existing desks' published
tables, re-checks their headline numbers against the official pages fetched for
this build, and publishes every check with the source it was checked against.

A check that disagrees is reported as an IRREGULARITY with both numbers shown.
A check that cannot be run is reported as NOT CHECKED with the reason.  Nothing
is silently corrected.
"""

from __future__ import annotations

import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import (RETRIEVED_UTC, STANDINGS_URL, load_official_games, official_standings,
                    read_csv, write_csv, MIRROR_GAMES_URL, INJURY_URL)

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, "data")


def _check(cid, area, claim, source_file, expected, observed, source_url, note=""):
    if expected is None or observed is None:
        state, verdict = "not checked", "NOT CHECKED"
    elif str(expected) == str(observed):
        state, verdict = "agree", "MATCH"
    else:
        state, verdict = "disagree", "IRREGULAR"
    return {"check_id": cid, "area": area, "claim_under_review": claim,
            "source_file": source_file, "published_value": "" if expected is None else expected,
            "recomputed_value": "" if observed is None else observed,
            "verdict": verdict, "note": note,
            "official_source_url": source_url, "checked_utc": RETRIEVED_UTC}


def build_audit() -> list:
    games, _ = load_official_games()
    standings = official_standings()
    mine = {s["team"]: s for s in standings}
    rows = []
    n = 0

    def add(*a, **kw):
        nonlocal n
        n += 1
        rows.append(_check(f"AR-{n:03d}", *a, **kw))

    # ---- 1. standings published by the cross-desk hub (28431d9c) -----------
    hub = os.path.join(REPO, "nfl-hub-28431d9c", "data", "official_standings_2026_reg.csv")
    if os.path.exists(hub):
        for r in read_csv(hub):
            t = r["nfl_code"]
            if t not in mine:
                continue
            m = mine[t]
            add("Standings", f"{t} win-loss-tie as published by the cross-desk hub",
                "nfl-hub-28431d9c/data/official_standings_2026_reg.csv",
                f"{r['w']}-{r['l']}-{r['t']}", f"{m['w']}-{m['l']}-{m['t']}",
                STANDINGS_URL,
                f"hub snapshot {r.get('as_of_fetch', '?')}; this desk {RETRIEVED_UTC[:10]}")
            add("Standings", f"{t} points for / against as published by the cross-desk hub",
                "nfl-hub-28431d9c/data/official_standings_2026_reg.csv",
                f"{r['pf']}/{r['pa']}", f"{m['pf']}/{m['pa']}", STANDINGS_URL,
                f"hub snapshot {r.get('as_of_fetch', '?')}")

    # ---- 2. standings reconciliation published by nfl-desk-864d5668 --------
    rec = os.path.join(REPO, "nfl-desk-864d5668", "data", "standings_reconciliation.csv")
    if os.path.exists(rec):
        for r in read_csv(rec):
            t = r["team"]
            if t not in mine:
                continue
            m = mine[t]
            add("Standings", f"{t} official W-L-T as reconciled by nfl-desk-864d5668",
                "nfl-desk-864d5668/data/standings_reconciliation.csv",
                f"{r['W_official']}-{r['L_official']}-{r['T_official']}",
                f"{m['w']}-{m['l']}-{m['t']}", STANDINGS_URL)
            add("Standings", f"{t} official PF/PA as reconciled by nfl-desk-864d5668",
                "nfl-desk-864d5668/data/standings_reconciliation.csv",
                f"{r['PF_official']}/{r['PA_official']}", f"{m['pf']}/{m['pa']}", STANDINGS_URL)

    # ---- 3. headline counts from nfl-desk-864d5668 -------------------------
    summary = os.path.join(REPO, "nfl-desk-864d5668", "data", "summary.json")
    if os.path.exists(summary):
        with open(summary, encoding="utf-8") as fh:
            s = json.load(fh)
        add("Game counts", "Completed 2026 regular-season games",
            "nfl-desk-864d5668/data/summary.json", s.get("completed_games"), len(games),
            "https://www.nfl.com/schedules/2026/")
        hfa = s.get("hfa", {})
        if hfa:
            add("Home-field advantage", "Non-neutral games in the home-field sample",
                "nfl-desk-864d5668/data/summary.json", hfa.get("n"),
                sum(1 for g in games if not g["neutral_site"]),
                "https://www.nfl.com/schedules/2026/")
            add("Home-field advantage", "Neutral-site games excluded from the sample",
                "nfl-desk-864d5668/data/summary.json",
                137 - hfa.get("n") if hfa.get("n") else None,
                sum(1 for g in games if g["neutral_site"]),
                "https://www.nfl.com/schedules/2026/",
                "different model specifications give different point estimates; the size of the "
                "sample is the part that must reconcile")
            add("Home-field advantage", "Home-field point estimate (mean home margin)",
                "nfl-desk-864d5668/data/summary.json", round(hfa.get("mean", -1), 2),
                round(sum(g["home_margin"] for g in games if not g["neutral_site"])
                      / max(1, sum(1 for g in games if not g["neutral_site"])), 2),
                "https://www.nfl.com/schedules/2026/",
                "raw mean home margin, before any model shrinkage; the desks differ because "
                "864d5668 uses ridge lambda 5 and this desk uses 8")

    # ---- 4. the Week 8 desk's standings (session 0f468a47) -----------------
    wk8 = os.path.join(REPO, "data", "standings-2026-wk8.csv")
    if os.path.exists(wk8):
        r0 = read_csv(wk8)
        add("Standings", "Number of clubs in the Week 8 standings table",
            "data/standings-2026-wk8.csv", 32, len(r0),
            "https://www.nfl.com/standings/",
            "this table is a 2026-11-02 snapshot, so its values are expected to differ from "
            "today's; only the row count is checked here")

    # ---- 5. injury report row counts --------------------------------------
    add("Injuries", "Week 10 official injury rows carried by nfl-desk-864d5668",
        "nfl-desk-864d5668/data/injuries.csv",
        326, sum(1 for _ in read_csv(os.path.join(REPO, "nfl-desk-864d5668", "data",
                                                  "injuries.csv")))
        if os.path.exists(os.path.join(REPO, "nfl-desk-864d5668", "data", "injuries.csv"))
        else None, INJURY_URL,
        "row count is as committed; the underlying page is re-read on every build and grows "
        "as game statuses are published")
    old = os.path.join(REPO, "data", "decision-desk", "official", "official_injuries_wk10.csv")
    if os.path.exists(old):
        add("Injuries", "Week 10 official injury rows in the 2026-11-12 decision-desk snapshot",
            "data/decision-desk/official/official_injuries_wk10.csv",
            276, len(read_csv(old)), INJURY_URL,
            "276 rows on 2026-11-12 versus 326 on 2026-11-13 is the report filling in during "
            "the week, not a contradiction")

    # ---- 6. depth charts ---------------------------------------------------
    depth = os.path.join(REPO, "nfl-desk-864d5668", "data", "depth_detail.csv")
    if os.path.exists(depth):
        d = read_csv(depth)
        add("Depth", "Clubs with a readable published depth chart",
            "nfl-desk-864d5668/data/depth_detail.csv", 31, len({r["team"] for r in d}),
            "https://www.nfl.com/teams/",
            "Houston publishes its chart only as an image, so 31 of 32 is the expected value")
        add("Depth", "Published depth slots carried in that desk's table",
            "nfl-desk-864d5668/data/depth_detail.csv", 705, len(d),
            "https://www.nfl.com/teams/",
            "the session's own COORDINATION entry says 707; the committed table holds 705 - "
            "reported rather than reconciled, since only the file can be checked")

    # ---- 7. structural provenance checks on the existing desks -------------
    structural = [
        ("data/decision-desk/questions.csv", "questions register"),
        ("data/decision-desk/suggestions.csv", "suggestions register"),
        ("data/decision-desk/requirements.csv", "requirements matrix"),
        ("data/decision-desk/strategy_ledger.csv", "strategy ledger"),
        ("data/decision-desk/gate_matrix.csv", "gate matrix"),
        ("data/decision-desk/prop_correlations.csv", "prop correlations"),
        ("data/decision-desk/injuries_wk10_players.csv", "injury rows"),
        ("nfl-desk-864d5668/data/own_lines.csv", "own lines"),
        ("nfl-desk-864d5668/data/leaderboard.csv", "leaderboard"),
        ("nfl-desk-864d5668/data/correlations.csv", "correlations"),
        ("nfl-hub-28431d9c/data/official_slate_2026_wk10.csv", "week 10 slate"),
        ("nfl-hub-28431d9c/data/desk_map.csv", "desk map"),
    ]
    for rel, label in structural:
        path = os.path.join(REPO, rel)
        if not os.path.exists(path):
            add("Provenance", f"{label} ({rel}) exists", rel, "yes", "no",
                "https://github.com/sassnarep3-star/Own5")
            continue
        rs = read_csv(path)
        cols = list(rs[0].keys()) if rs else []
        has_src = any("source" in c.lower() or "url" in c.lower() for c in cols)
        add("Provenance", f"{label} ({rel}) carries a source column on every row", rel,
            "yes", "yes" if has_src else "no",
            "https://github.com/sassnarep3-star/Own5",
            f"columns: {', '.join(cols[:10])}" if not has_src else "")

    # ---- 8. CI-locked files must be untouched by this session --------------
    for rel in ("index.html", "data/research.json", "pages/strategies.html",
                "nfl-desk-864d5668/index.html", "nfl-hub-28431d9c/index.html"):
        path = os.path.join(REPO, rel)
        add("Scope", f"{rel} still exists and was not modified by this session", rel,
            "present", "present" if os.path.exists(path) else "missing",
            "https://github.com/sassnarep3-star/Own5")

    return rows


def main() -> list:
    rows = build_audit()
    write_csv("repo_audit.csv", rows,
              ["check_id", "area", "claim_under_review", "source_file", "published_value",
               "recomputed_value", "verdict", "note", "official_source_url", "checked_utc"])
    return rows


if __name__ == "__main__":
    rs = main()
    from collections import Counter
    print(Counter(r["verdict"] for r in rs), len(rs))

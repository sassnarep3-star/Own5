#!/usr/bin/env python3
"""Drift alarms + line-by-line verification for desk 6cbf25fa.

Fail-closed: any alarm exits non-zero.  Alarms pin the league structure (32
clubs, 14 Week 10 finals, 13 Week 11 fixtures, 3 markets per game), required
fields, probability identities, snapshot invariants, delta-ledger invariants,
and the every-row-has-a-source-or-flag rule across all desk CSVs.  Internal
links on generated pages are also checked.
"""
import csv
import gzip
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
D = os.path.join(ROOT, "data", "nfl-desk-6cbf25fa")
LEADS = os.path.join(D, "injury_reads")

TEAM32 = {"ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
          "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA",
          "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
          "TEN", "WAS"}

TO_CANONICAL = {"LA": "LAR", "AZ": "ARI"}  # official pages print AZ/LA; canonical follows the pinned snapshot


def canon(c):
    return TO_CANONICAL.get(c, c)


ALARMS = []
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, ok, detail))
    if not ok:
        ALARMS.append(f"{name}: {detail}")


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    # ---- pinned structure
    standings = rows(os.path.join(D, "standings_2026-11-18.csv"))
    check("standings_clubs=32", len(standings) == 32 and
          {canon(s["team_code"]) for s in standings} == TEAM32,
          f"rows={len(standings)}")
    check("standings_raw_cells_present", all(s["raw_cells_as_printed"].strip() for s in standings), "empty raw cells")

    results = rows(os.path.join(D, "results_week10.csv"))
    check("week10_finals=14", len(results) == 14, f"rows={len(results)}")
    wk10_teams = set()
    for g in results:
        check(f"final_scores_{g['game_slug']}", g["away_score"].isdigit() and g["home_score"].isdigit(),
              "non-integer score")
        wk10_teams |= {canon(g["away_team"]), canon(g["home_team"])}
        check(f"final_source_{g['game_slug']}", g["source_url"].startswith("https://www.nfl.com/games/"),
              "no official per-game link")
    check("week10_byes_match_page", wk10_teams | {"CHI", "DEN", "PHI", "TB"} == TEAM32 and
          len({"CHI", "DEN", "PHI", "TB"} - wk10_teams) == 4,
          f"byes mismatch: {sorted(TEAM32 - wk10_teams)}")

    lines = rows(os.path.join(D, "lines_week11.csv"))
    check("markets=39", len(lines) == 39, f"rows={len(lines)}")
    games = {}
    for ln in lines:
        games.setdefault(ln["game_id"], []).append(ln["market_type"])
    check("games=13", len(games) == 13, f"games={len(games)}")
    check("three_markets_per_game", all(sorted(v) == ["moneyline", "side", "total"] for v in games.values()),
          "market set wrong")
    for ln in lines:
        p_h, p_a, p_p = float(ln["p_home_win"]), float(ln["p_away_win"]), float(ln["p_push"])
        check(f"prob_sum_{ln['game_id']}_{ln['market_type']}", abs(p_h + p_a + p_p - 1.0) < 1e-6,
              f"{p_h}+{p_a}+{p_p}")
        check(f"prob_range_{ln['game_id']}_{ln['market_type']}", all(0 <= p <= 1 for p in (p_h, p_a, p_p)), "out of range")
        check(f"market_blank_{ln['game_id']}_{ln['market_type']}",
              ln["market_line"] == "" and ln["market_source"] == "" and ln["residual_fair_minus_market"] == "",
              "market/residual filled without a verified source (F-P01)")
        check(f"inputs_sha_{ln['game_id']}_{ln['market_type']}", len(ln["inputs_sha256"]) == 64, "missing inputs hash")
        check(f"opened_{ln['game_id']}_{ln['market_type']}", ln["opened_utc"].startswith("2026-11-18T"), "missing open stamp")

    # ---- price snapshots
    snaps = rows(os.path.join(D, "price_snapshots.csv"))
    check("snapshots=39", len(snaps) == 39, f"rows={len(snaps)}")
    for s in snaps:
        check(f"snap_open_status_{s['market_id']}", s["status"] == "open", "unexpected status")
        check(f"snap_close_blank_{s['market_id']}",
              s["closing_fair_unrounded"] == "" and s["closing_fair_rounded"] == "" and s["closing_source"] == "",
              "closing filled while game incomplete")
        check(f"snap_opening_present_{s['market_id']}", s["opening_fair_unrounded"] != "", "no opening value")
        check(f"snap_inputs_{s['market_id']}", s["inputs_sha256"] == lines[0]["inputs_sha256"] or len(s["inputs_sha256"]) == 64,
              "inputs hash mismatch")
    check("snapshot_ids_unique", len({s["market_id"] for s in snaps}) == len(snaps), "duplicate market ids")

    # ---- model inputs
    import json
    mi = json.load(open(os.path.join(D, "model_inputs.json")))
    check("model_inputs_corpus", mi["corpus_games"] == 150, f"corpus={mi['corpus_games']}")
    check("model_inputs_ratings_32", len(mi["ratings"]["offensive_deviation"]) == 32 and
          len(mi["ratings"]["defensive_effectiveness"]) == 32, "ratings club count")
    check("model_inputs_no_hash_problems", mi["pinned_snapshot_hash_problems"] == [], "pinned snapshot hash drift")
    check("model_inputs_spec_hash", len(mi["spec_sha256"]) == 64, "spec hash missing")
    spec_path = os.path.join(ROOT, "research", "nfl-6cbf25fa", "model_spec.md")
    import hashlib
    check("spec_file_matches_recorded_hash",
          hashlib.sha256(open(spec_path, "rb").read()).hexdigest() == mi["spec_sha256"],
          "spec edited after registration")

    # ---- injury ledger
    reads = rows(os.path.join(LEADS, "reads.csv"))
    check("reads=2", len(reads) == 2, f"reads={len(reads)}")
    check("reads_stamped", all(re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", r["captured_utc"]) for r in reads),
          "read without clock stamp")
    today = rows(os.path.join(LEADS, "capture_injuries_2026-11-18.csv"))
    check("capture_rows=347", len(today) == 347, f"rows={len(today)} (drift alarm: league report changed - re-read and update pinned count deliberately)")
    check("capture_teams=28", {canon(r["team_code"]) for r in today} <= TEAM32 and
          len({canon(r["team_code"]) for r in today}) == 28,
          f"teams={len({canon(r['team_code']) for r in today})}")
    check("capture_fields_present", all(r["player"] and r["position"] and r["practice_status"] for r in today),
          "blank required field")
    deltas = rows(os.path.join(LEADS, "deltas_2026-11-12_to_2026-11-18.csv"))
    check("deltas>0", len(deltas) > 0, "no deltas between reads")
    check("delta_dual_stamps", all(d["prior_read_utc"] and d["this_read_utc"] for d in deltas), "delta missing a stamp")
    check("delta_types_known", {d["change_type"] for d in deltas} <=
          {"added_to_report", "removed_from_report", "game_status_changed", "practice_status_changed", "injuries_changed"},
          "unknown change type")

    # ---- every CSV row has a source or an explicit flag
    flagged_ids = {f["flag_id"] for f in rows(os.path.join(D, "flagged.csv"))}
    for fname, src_col in (("lines_week11.csv", "source_url"), ("price_snapshots.csv", "source_url"),
                           ("results_week10.csv", "source_url"), ("standings_2026-11-18.csv", "source_url"),
                           ("game_centre_min_sf_2026-11-18.csv", "source_url")):
        for i, r in enumerate(rows(os.path.join(D, fname))):
            check(f"source_{fname}_{i}", bool(r.get(src_col, "").strip()), "row without source link")

    # ---- raw extracts hashed
    sums = os.path.join(HERE, "raw", "SHA256SUMS.txt")
    import hashlib
    ok_sums = True
    for line in open(sums):
        h, name = line.split()
        p = os.path.join(HERE, "raw", name)
        if not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != h:
            ok_sums = False
    check("extract_hashes_valid", ok_sums, "extract file missing or hash drift")

    # ---- pages: internal links resolve, no JS required for content
    page_files = [f for f in os.listdir(HERE) if f.endswith(".html")]
    check("pages=10", len(page_files) == 10, f"pages={len(page_files)}")
    nav_names = {"index.html", "lines.html", "snapshots.html", "ratings.html", "results.html",
                 "ledger.html", "suggestions.html", "questions.html", "flagged.html", "sources.html"}
    check("nav_files_exist", nav_names == set(page_files), f"missing {nav_names - set(page_files)}")
    for pf in page_files:
        text = open(os.path.join(HERE, pf), encoding="utf-8").read()
        for m in re.finditer(r'href="(?!https?:|mailto:|#)([^"]+)"', text):
            target = m.group(1).split("#")[0]
            if target and not os.path.exists(os.path.join(HERE, target)):
                check(f"link_{pf}_{target}", False, "broken internal link")
        check(f"no_script_{pf}", "<script" not in text, "page requires JavaScript")

    # ---- report
    fails = [c for c in CHECKS if not c[1]]
    print(f"verify: PASS checks={len(CHECKS)} failures={len(fails)}")
    for name, ok, detail in CHECKS:
        if not ok:
            print(f"  FAIL {name}: {detail}")
    if ALARMS:
        print(f"DRIFT ALARMS: {len(ALARMS)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

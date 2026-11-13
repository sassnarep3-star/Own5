"""Build derived research outputs from the frozen official snapshot.

This is intentionally separate from evidence collection. Running it cannot
invent market quotes or turn an unvalidated model into an eligible strategy.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "own5_desk"
DECISION_DESK = ROOT / "data" / "decision-desk"


def read_csv(name: str) -> list[dict]:
    with open(DECISION_DESK / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(value: str):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# Official sources relevant to each suggestion/question. These are links for
# manual review; no value in a row is inferred from them.
SUGGESTION_OFFICIAL_SOURCES: dict[str, list[str]] = {
    "S01": ["https://www.nfl.com/schedules/2026/by-week/week-9", "https://support.fanduel.com/s/article/Betting-football-with-FanDuel"],
    "S02": ["https://www.nfl.com/schedules/2026/by-week/week-9"],
    "S03": ["https://academic.oup.com/rfs/issue/29/1"],
    "S04": ["https://www.nfl.com/schedules/2026/by-week/week-9"],
    "S05": ["https://www.nfl.com/injuries/"],
    "S06": ["https://www.nfl.com/injuries/"],
    "S07": ["https://www.nfl.com/injuries/"],
    "S08": ["https://academic.oup.com/rfs/issue/29/1"],
    "S09": ["https://www.nfl.com/injuries/", "https://www.nfl.com/standings/league/2026/REG"],
    "S10": ["https://www.nfl.com/standings/league/2026/REG"],
    "S11": ["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"],
    "S12": ["https://www.nfl.com/"],
    "S13": ["https://www.nfl.com/injuries/", "https://www.nfl.com/standings/league/2026/REG"],
    "S14": ["https://academic.oup.com/rfs/issue/29/1"],
    "S15": ["https://www.nfl.com/schedules/2026/by-week/week-9"],
    "S16": ["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"],
}

QUESTION_OFFICIAL_SOURCES: dict[str, list[str]] = {
    "Q01": ["https://www.nfl.com/schedules/2026/by-week/week-9"],
    "Q02": ["https://www.nfl.com/schedules/2026/by-week/week-9"],
    "Q03": ["https://support.fanduel.com/s/article/Betting-football-with-FanDuel", "https://www.nfl.com/"],
    "Q04": ["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"],
    "Q05": ["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"],
    "Q06": ["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"],
    "Q07": ["https://www.nfl.com/injuries/"],
    "Q08": ["https://www.nfl.com/injuries/", "https://www.nfl.com/standings/league/2026/REG"],
    "Q09": ["https://www.nfl.com/injuries/"],
    "Q10": ["https://www.nfl.com/injuries/"],
    "Q11": ["https://academic.oup.com/rfs/issue/29/1"],
    "Q12": ["https://academic.oup.com/rfs/issue/29/1"],
    "Q13": ["https://www.nfl.com/standings/league/2026/REG"],
    "Q14": ["https://www.nfl.com/schedules/2026/by-week/week-9"],
    "Q15": ["https://www.nfl.com/standings/league/2026/REG"],
    "Q16": ["https://www.nfl.com/injuries/", "https://www.nfl.com/standings/league/2026/REG"],
    "Q17": ["https://www.nfl.com/standings/league/2026/REG"],
    "Q18": ["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"],
}


def build_suggestions() -> list[dict]:
    rows = []
    for r in read_csv("suggestions.csv"):
        rows.append(dict(
            id=r["id"], title=r["title"], problem=r["problem"],
            recommendation=r["recommendation"], impact=r["impact"],
            effort=r["effort"], confidence=r["confidence"],
            evidence=r["evidence"], decision=r["decision"],
            owner=r["owner"], review_test=r["review_test"],
            official_sources=SUGGESTION_OFFICIAL_SOURCES.get(r["id"], []),
        ))
    return rows


def build_questions() -> list[dict]:
    rows = []
    for r in read_csv("questions.csv"):
        rows.append(dict(
            id=r["id"], question=r["question"], why=r["why"],
            have=r["have"], missing=r["missing"], resolve=r["resolve"],
            blocks=r["blocks"], status=r["status"], related=r["related"],
            official_sources=QUESTION_OFFICIAL_SOURCES.get(r["id"], []),
        ))
    return rows


def build_injuries() -> list[dict]:
    rows = []
    for r in read_csv("injuries_wk10_players.csv"):
        rows.append(dict(
            team=r["team"], team_name=r["team_name"], player=r["player"],
            position=r["position"], pos_group=r["pos_group"], injury=r["injury"],
            practice_status=r["practice_status"], game_status=r["game_status"],
            season_snap_share=_f(r["season_snap_share"]),
            depth_string=r["depth_string"], is_starter=r["is_starter"].lower() == "true",
            next_man_up_share=_f(r["next_man_up_share"]),
            replacement_drop=_f(r["replacement_drop"]),
            availability_weight=_f(r["availability_weight"]),
            weight_basis=r["weight_basis"],
            injury_report_match=r["injury_report_match"],
            source_url=r["source_url"], retrieved_utc=r["retrieved_utc"],
        ))
    return rows


def build_deficiencies() -> list[dict]:
    rows = []
    for r in read_csv("team_deficiency_wk10.csv"):
        rows.append(dict(
            team=r["team"], team_name=r["team_name"],
            players_listed=_f(r["players_listed"]),
            players_with_snap_profile=_f(r["players_with_snap_profile"]),
            starters_unavailable_or_limited=_f(r["starters_unavailable_or_limited"]),
            off_replacement_drop=_f(r["off_replacement_drop"]),
            def_replacement_drop=_f(r["def_replacement_drop"]),
            total_replacement_drop=_f(r["total_replacement_drop"]),
            source_url=r["source_url"], retrieved_utc=r["retrieved_utc"],
        ))
    return rows
sys.path.insert(0, str(ROOT))
from nfl_model.audit import audit_data
from nfl_model.correlation import analyze_pair
from nfl_model.ratings import project_game, team_ratings
from nfl_model.strategies import registered_strategies
from nfl_model.validation import GATE_SPECS, build_leaderboard


def dump(name: str, value: object) -> None:
    (DATA / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def main() -> None:
    snapshot = json.loads((ROOT / "research/official_snapshot.json").read_text())
    ratings, mu = team_ratings(snapshot["teams"])
    lines = [project_game(g, ratings, mu) for g in snapshot["schedule"]]
    correlation = analyze_pair(snapshot["paired_player_games"])
    strategies = registered_strategies()
    leaderboard = build_leaderboard(strategies)
    gate_definitions = [dict(id=i, name=n, requirement=r, classification="Project policy",
                               source_ids=["S16", "S17"],
                               source_urls=["https://academic.oup.com/rfs/issue/29/1", "https://journals.ametsoc.org/view/journals/mwre/148/9/mwrD190076.xml?tab_body=fulltext-display"])
                        for i, n, r, _ in GATE_SPECS]
    dump("derived_lines.json", lines)
    dump("correlations.json", correlation)
    dump("strategies.json", strategies)
    dump("leaderboard.json", leaderboard)
    dump("gate_definitions.json", gate_definitions)
    report = audit_data(ROOT)
    dump("audit_report.json", report)
    if report["status"] != "pass":
        raise SystemExit("\n".join(report["failures"]))
    summary = {
        "snapshot_date": snapshot["retrieved_utc"], "season": 2026, "week": 9,
        "official_sources": len(json.loads((ROOT / "data/own5_desk/source_register.json").read_text())),
        "verified_fact_rows": len(json.loads((ROOT / "data/own5_desk/verified_facts.json").read_text())),
        "teams": len(snapshot["teams"]), "research_lines": len(lines),
        "historical_paired_games": len(snapshot["paired_player_games"]),
        "strategies": len(strategies), "qualified_strategies": len(leaderboard),
        "reward_points_awarded": sum(r["reward_points"] for r in leaderboard),
        "review_items": len(json.loads((ROOT / "data/own5_desk/review_items.json").read_text())),
        "verified_market_quotes": len(snapshot["market_quotes"]),
        "league_mean_points_per_team_game": mu,
        "pearson_r": correlation["pearson_r"], "binary_phi": correlation["binary_phi"],
        "joint_hits": correlation["joint_hits"], "joint_rate": correlation["joint_rate"],
        "independence_product": correlation["independence_product"],
        "audit_status": report["status"],
    }
    dump("suggestions.json", build_suggestions())
    dump("questions.json", build_questions())
    dump("injuries.json", build_injuries())
    dump("deficiencies.json", build_deficiencies())
    dump("summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

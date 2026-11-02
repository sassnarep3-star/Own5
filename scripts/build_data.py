"""Build derived research outputs from the frozen official snapshot.

This is intentionally separate from evidence collection. Running it cannot
invent market quotes or turn an unvalidated model into an eligible strategy.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "own5_desk"
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
    dump("summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

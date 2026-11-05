"""Run the frozen offline analysis and write deterministic derived artifacts."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from . import model

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DATA = ROOT / "data"
DERIVED = DATA / "derived"


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> dict:
    protocol = json.loads((DATA / "protocol.json").read_text(encoding="utf-8"))
    teams = model.read_csv(DATA / "team_snapshot.csv")
    schedule = model.read_csv(DATA / "schedule.csv")
    games = model.read_csv(DATA / "player_games.csv")
    lines, sensitivity = model.team_lines(teams, schedule, protocol)
    forecasts, skill = model.player_forecasts(games, protocol)
    corr = model.correlations(games, protocol)
    combos = model.prop_combos(games, protocol)
    luck = model.luck_planning(protocol)
    strategies, gates, leaderboard = model.strategies_and_gates(protocol, skill, lines)
    artifacts = {
        "lines": lines, "sensitivity": sensitivity, "player_forecasts": forecasts,
        "skill_summary": skill, "correlations": corr, "prop_combos": combos,
        "strategies": strategies, "gates": gates, "leaderboard": leaderboard,
    }
    for name, rows in artifacts.items():
        write_csv(DERIVED / f"{name}.csv", rows)
    (DERIVED / "luck.json").write_text(json.dumps(luck, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    input_hashes = {p.name: sha256(p) for p in sorted(DATA.glob("*.csv"))}
    input_hashes["protocol.json"] = sha256(DATA / "protocol.json")
    summary = {
        "protocol_id": protocol["protocol_id"],
        "team_rows": len(teams), "current_teams": sum(1 for t in teams if t["season"] == "2026-27"),
        "player_games": len(games), "players": len({g['player_id'] for g in games}),
        "schedule_games": len(schedule), "research_lines": len(lines),
        "sensitivity_rows": len(sensitivity), "forecast_rows": len(forecasts),
        "skill_series": len(skill), "predictive_gate_passes": sum(1 for s in skill if s["passes_predictive_gate"]),
        "correlation_rows": len(corr), "combo_rows": len(combos),
        "two_prop_rows": sum(1 for c in combos if c["legs"] == 2),
        "three_prop_rows": sum(1 for c in combos if c["legs"] == 3),
        "strategies": len(strategies), "eligible_strategies": sum(1 for s in strategies if s["eligible"]),
        "graded_bets": 0, "rewards_paid": 0,
        "input_sha256": input_hashes,
    }
    out = {"summary": summary, "luck": luck, **artifacts}
    (DERIVED / "outputs.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(DERIVED / "summary.csv", [{"metric": k, "value": json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v} for k, v in summary.items()])
    print(json.dumps(summary, indent=2, sort_keys=True))
    return out


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Transparent NBA research-line model. Standard library only.

Official NBA values enter only through the reviewed CSV snapshot. Every projection,
correlation, probability and American price below is analyst-derived, not NBA-published.
No function in this module turns a projection into a qualified betting signal.
"""
from __future__ import annotations

import csv
import itertools
import json
import math
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
AS_OF = "2026-11-03T23:39:30Z"
SEASON = "2026-27"
PRIOR_GAMES = 10.0
HOME_ADVANTAGE = 0.0
LOGISTIC_SCALE = 6.0
MIN_OUT_OF_SAMPLE = 100
REWARD_POINTS = (100, 60, 40)
OFFICIAL_HOSTS = {"www.nba.com", "official.nba.com", "ak-static.cms.nba.com"}

GATES = [
    {"id": "G00", "name": "Official provenance", "requirement": "Every factual input row has a reviewable official NBA URL.", "source_id": "S02"},
    {"id": "G01", "name": "Frozen specification", "requirement": "Snapshot, formulas, parameters and exclusions are fixed before grading.", "source_id": "S02"},
    {"id": "G02", "name": "Availability resolved", "requirement": "A current official report is joined; Out players are suppressed and unknown never passes.", "source_id": "S10"},
    {"id": "G03", "name": "Market and settlement", "requirement": "Timestamped prices, combo payouts and settlement rules exist before value is claimed.", "source_id": "S01"},
    {"id": "G04", "name": "Prospective ledger", "requirement": "Pregame forecasts and subsequent official results are stored without retroactive selection.", "source_id": "S01"},
    {"id": "G05", "name": "Out-of-sample size", "requirement": f"At least {MIN_OUT_OF_SAMPLE} graded prospective forecasts per strategy; current count is zero.", "source_id": "S02"},
    {"id": "G06", "name": "Predictive skill", "requirement": "Predeclared Brier/log-loss or price-aware metrics beat a baseline with uncertainty reported.", "source_id": "S11"},
    {"id": "G07", "name": "Luck screen", "requirement": "Exact/simulated null tests and multiple-comparison control reject random variation; no result yet.", "source_id": "S04"},
    {"id": "G08", "name": "Combo dependence", "requirement": "Joint-hit dependence and correlation are estimated for parlays/prop combos; marginal multiplication is not enough.", "source_id": "S04"},
    {"id": "G09", "name": "Risk and leakage policy", "requirement": "No stake while unqualified; fixed evaluation windows, no cherry-picking and responsible-gambling controls are documented.", "source_id": "S12"},
]


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def decimal(value: object) -> Decimal:
    return Decimal(str(value))


def round_half_up(value: object, digits: int = 1) -> float:
    quantum = Decimal("1").scaleb(-digits)
    return float(decimal(value).quantize(quantum, rounding=ROUND_HALF_UP))


def round_to_half(value: object) -> float:
    rounded = float((decimal(value) * 2).quantize(Decimal("1"), rounding=ROUND_HALF_UP) / 2)
    return 0.0 if rounded == 0 else rounded


def american_odds(probability: float) -> int:
    """No-vig American price from a model probability; not a sportsbook quote."""
    if not 0.0 < probability < 1.0:
        raise ValueError("probability must be strictly between zero and one")
    price = 100 * (1 - probability) / probability if probability <= 0.5 else -100 * probability / (1 - probability)
    return int(decimal(price).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def logistic_probability(margin: float, scale: float = LOGISTIC_SCALE) -> float:
    if scale <= 0:
        raise ValueError("logistic scale must be positive")
    return 1.0 / (1.0 + math.exp(-margin / scale))


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("Pearson inputs need equal lengths of at least two")
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    xdev = [x - xbar for x in xs]
    ydev = [y - ybar for y in ys]
    denominator = math.sqrt(sum(x * x for x in xdev) * sum(y * y for y in ydev))
    if denominator == 0:
        return None
    return sum(x * y for x, y in zip(xdev, ydev)) / denominator


def exact_permutation_p(xs: list[float], ys: list[float]) -> float | None:
    """Two-sided exact label-permutation p-value, counting all label permutations."""
    observed = pearson(xs, ys)
    if observed is None:
        return None
    extreme = 0
    total = 0
    tolerance = 1e-12
    for permuted in itertools.permutations(ys):
        statistic = pearson(xs, list(permuted))
        total += 1
        if abs(statistic) + tolerance >= abs(observed):
            extreme += 1
    return extreme / total


def holm_adjust(rows: list[dict], p_key: str = "p_permutation") -> None:
    """Adjust a set of non-null p-values in place with Holm's step-down method."""
    valid = sorted((row for row in rows if row.get(p_key) is not None), key=lambda row: row[p_key])
    m = len(valid)
    running = 0.0
    for index, row in enumerate(valid):
        adjusted = min(1.0, (m - index) * row[p_key])
        running = max(running, adjusted)
        row["p_holm"] = running
    for row in rows:
        if row.get(p_key) is None:
            row["p_holm"] = None


def binomial_upper_tail(k: int, n: int, probability: float = 0.5) -> float:
    """P[X >= k] for a binomial null; used for future preregistered skill tests."""
    if not 0 <= k <= n:
        raise ValueError("require 0 <= k <= n")
    if not 0 <= probability <= 1:
        raise ValueError("invalid binomial probability")
    return sum(math.comb(n, i) * probability**i * (1 - probability) ** (n - i) for i in range(k, n + 1))


def binomial_critical_hits(n: int, alpha: float = 0.01, probability: float = 0.5) -> int | None:
    for hits in range(n + 1):
        if binomial_upper_tail(hits, n, probability) <= alpha:
            return hits
    return None


def load_data() -> dict:
    data = {name: read_csv(f"{name}.csv") for name in ("sources", "teams", "schedule", "players", "player_games", "strategies", "flags")}
    data["source_map"] = {row["source_id"]: row for row in data["sources"]}
    data["team_map"] = {row["abbr"]: row for row in data["teams"]}
    data["player_map"] = {row["player_id"]: row for row in data["players"]}
    validate_data(data)
    return data


def validate_data(data: dict) -> None:
    teams, schedule, players, games = data["teams"], data["schedule"], data["players"], data["player_games"]
    sources = data["source_map"]
    assert len(teams) == 30 and len({row["abbr"] for row in teams}) == 30
    assert len({row["team_id"] for row in teams}) == 30
    assert len(schedule) == 16 and len({row["game_id"] for row in schedule}) == 16
    assert len(players) == 4 and len(games) == 26
    for source in data["sources"]:
        assert source["source_id"] and source["source_id"] not in sources or sources[source["source_id"]] == source
        assert urlparse(source["url"]).scheme == "https"
        assert urlparse(source["url"]).hostname in OFFICIAL_HOSTS
        assert source["retrieved_at"] == AS_OF
    for team in teams:
        gp, wins, losses = int(team["gp"]), int(team["wins"]), int(team["losses"])
        assert gp == wins + losses and gp > 0
        assert float(team["minutes"]) >= 48 * gp
        assert abs((float(team["off_rtg"]) - float(team["def_rtg"])) - float(team["net_rtg"])) <= 0.101
        assert team["source_id"] in sources
    scheduled_teams = set()
    for game in schedule:
        away, home = data["team_map"][game["away"]], data["team_map"][game["home"]]
        assert game["game_id"].startswith("00226") and game["slug"].endswith(game["game_id"])
        assert game["date"] in {"2026-11-04", "2026-11-05"}
        for side, team in (("away", away), ("home", home)):
            assert int(game[f"{side}_wins"]) == int(team["wins"])
            assert int(game[f"{side}_losses"]) == int(team["losses"])
        scheduled_teams.update((game["away"], game["home"]))
    assert scheduled_teams == set(data["team_map"])
    by_player = defaultdict(list)
    for row in games:
        by_player[row["player_id"]].append(row)
        assert row["player_id"] in data["player_map"]
        assert row["result"] in {"W", "L"}
        assert row["game_id"].startswith("00226")
        parsed = urlparse(row["source_url"])
        assert parsed.scheme == "https" and parsed.hostname == "www.nba.com"
        assert row["game_id"] in row["source_url"]
    schedule_map = {row["game_id"]: row for row in schedule}
    for player in players:
        rows = by_player[player["player_id"]]
        assert len(rows) == int(player["gp"])
        assert player["upcoming_game_id"] in schedule_map
        upcoming = schedule_map[player["upcoming_game_id"]]
        assert player["team_abbr"] in {upcoming["away"], upcoming["home"]}
        for stat, official_key in (("pts", "ppg"), ("reb", "rpg"), ("ast", "apg"), ("threepm", "threepm")):
            mean = Decimal(sum(int(row[stat]) for row in rows)) / Decimal(len(rows))
            reconciled = mean.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            assert reconciled == decimal(player[official_key]), (player["player"], stat, reconciled, player[official_key])
        assert player["source_id"] in sources
        assert player["availability"] in {"", "Out"}
    for collection in ("strategies", "flags"):
        for row in data[collection]:
            assert row["source_id"] in sources


def league_metrics(teams: list[dict]) -> dict[str, float]:
    total_poss = sum(int(row["poss"]) for row in teams)
    return {
        "off_rtg": sum(float(row["off_rtg"]) * int(row["poss"]) for row in teams) / total_poss,
        "def_rtg": sum(float(row["def_rtg"]) * int(row["poss"]) for row in teams) / total_poss,
        "pace": sum(float(row["pace"]) * int(row["poss"]) for row in teams) / total_poss,
        "poss": total_poss,
    }


def shrunk(value: float, league: float, gp: int, prior: float = PRIOR_GAMES) -> float:
    weight = gp / (gp + prior)
    return league + weight * (value - league)


def project_game(game: dict, team_map: dict, league: dict) -> dict:
    away, home = team_map[game["away"]], team_map[game["home"]]
    adjusted = {}
    for label, team in (("away", away), ("home", home)):
        gp = int(team["gp"])
        adjusted[label] = {
            "off": shrunk(float(team["off_rtg"]), league["off_rtg"], gp),
            "def": shrunk(float(team["def_rtg"]), league["def_rtg"], gp),
            "pace": shrunk(float(team["pace"]), league["pace"], gp),
        }
    possessions = (adjusted["away"]["pace"] + adjusted["home"]["pace"]) / 2
    away_eff = adjusted["away"]["off"] + adjusted["home"]["def"] - league["off_rtg"]
    home_eff = adjusted["home"]["off"] + adjusted["away"]["def"] - league["off_rtg"]
    away_points = possessions * away_eff / 100
    home_points = possessions * home_eff / 100 + HOME_ADVANTAGE
    margin = home_points - away_points
    home_probability = logistic_probability(margin)
    away_probability = 1 - home_probability
    return {
        **{key: game[key] for key in ("date", "time_et", "game_id", "away", "home", "slug")},
        "expected_possessions": possessions,
        "away_points": away_points,
        "home_points": home_points,
        "home_margin": margin,
        "away_spread": round_to_half(margin),
        "home_spread": -round_to_half(margin),
        "total": round_to_half(away_points + home_points),
        "away_probability": away_probability,
        "home_probability": home_probability,
        "away_fair_american": american_odds(away_probability),
        "home_fair_american": american_odds(home_probability),
        "market_spread": None,
        "market_total": None,
        "edge": None,
        "release_status": "RESEARCH ONLY — availability/market/validation gates open",
        "source_id": "S01",
        "ratings_source_id": "S02",
    }


def calculate_lines(data: dict) -> list[dict]:
    league = league_metrics(data["teams"])
    return [project_game(game, data["team_map"], league) for game in data["schedule"]]


def calculate_correlations(data: dict) -> list[dict]:
    rows = []
    team_pairs = (
        ("NetRtg", "Win%", lambda t: float(t["net_rtg"]), lambda t: int(t["wins"]) / int(t["gp"])),
        ("OffRtg", "Win%", lambda t: float(t["off_rtg"]), lambda t: int(t["wins"]) / int(t["gp"])),
        ("DefRtg", "Win%", lambda t: float(t["def_rtg"]), lambda t: int(t["wins"]) / int(t["gp"])),
        ("PACE", "OffRtg", lambda t: float(t["pace"]), lambda t: float(t["off_rtg"])),
        ("PACE", "Win%", lambda t: float(t["pace"]), lambda t: int(t["wins"]) / int(t["gp"])),
    )
    for x_name, y_name, x_func, y_func in team_pairs:
        rows.append({
            "scope": "Team", "subject": "All 30 teams", "pair": f"{x_name} × {y_name}", "n": 30,
            "r": pearson([x_func(row) for row in data["teams"]], [y_func(row) for row in data["teams"]]),
            "p_permutation": None, "p_holm": None, "source_id": "S02",
            "note": "Contemporaneous descriptive association; not predictive or causal.",
        })
    grouped = defaultdict(list)
    for row in data["player_games"]:
        grouped[row["player_id"]].append(row)
    player_rows = []
    for player in data["players"]:
        games = grouped[player["player_id"]]
        for x_name, y_name, x_key, y_key in (("PTS", "AST", "pts", "ast"), ("PTS", "REB", "pts", "reb"), ("PTS", "3PM", "pts", "threepm"), ("REB", "AST", "reb", "ast")):
            xs = [float(row[x_key]) for row in games]
            ys = [float(row[y_key]) for row in games]
            player_rows.append({
                "scope": "Player-game", "subject": player["player"], "pair": f"{x_name} × {y_name}", "n": len(games),
                "r": pearson(xs, ys), "p_permutation": exact_permutation_p(xs, ys), "source_id": player["source_id"],
                "note": "Exploratory continuous-stat association, not a same-game prop-hit correlation.",
            })
    holm_adjust(player_rows)
    rows.extend(player_rows)
    return rows


def calculate_player_props(data: dict) -> tuple[list[dict], list[dict]]:
    grouped = defaultdict(list)
    for row in data["player_games"]:
        grouped[row["player_id"]].append(row)
    props = []
    for player in data["players"]:
        games = grouped[player["player_id"]]
        means = {stat: sum(int(row[stat]) for row in games) / len(games) for stat in ("pts", "reb", "ast", "threepm")}
        suppressed = player["availability"] == "Out"
        props.append({
            **{key: player[key] for key in ("player_id", "player", "team_abbr", "gp", "upcoming_game_id", "availability", "availability_note", "source_id")},
            "means": means,
            "reference_lines": {stat: round_to_half(value) for stat, value in means.items()},
            "playable_lines": None,
            "joint_probability": None,
            "release_status": "SUPPRESSED — official report lists Out" if suppressed else "HELD — availability not confirmed",
        })
    by_name = {row["player"]: row for row in props}
    combo_specs = (
        ("PC01", "Luka Dončić", ("pts", "ast")),
        ("PC02", "Tyrese Maxey", ("pts", "ast")),
        ("PC03", "Shai Gilgeous-Alexander", ("pts", "reb")),
        ("PC04", "Anthony Edwards", ("pts", "threepm")),
    )
    combos = []
    for combo_id, name, markets in combo_specs:
        parent = by_name[name]
        combos.append({
            "combo_id": combo_id, "player": name, "player_id": parent["player_id"], "game_id": parent["upcoming_game_id"],
            "legs": [{ "market": market, "reference_line": parent["reference_lines"][market], "direction": None} for market in markets],
            "joint_probability": None, "payout": None,
            "release_status": "SUPPRESSED — player Out" if parent["availability"] == "Out" else "HELD — availability, thresholds, dependence and prices unresolved",
            "source_id": parent["source_id"],
        })
    return props, combos


def evaluate_strategies(data: dict) -> tuple[list[dict], list[dict]]:
    gate_map = {gate["id"]: gate for gate in GATES}
    leaderboard = []
    gate_rows = []
    for strategy in data["strategies"]:
        required = strategy["required_gates"].split(";")
        passed = set(strategy["evidence_pass"].split(";")) if strategy["evidence_pass"] else set()
        assert set(required) <= set(gate_map) and passed <= set(required)
        for gate_id in required:
            gate_rows.append({
                "strategy_id": strategy["strategy_id"], "strategy": strategy["strategy"], "gate_id": gate_id,
                "gate": gate_map[gate_id]["name"], "status": "PASS" if gate_id in passed else "FAIL",
                "evidence": gate_map[gate_id]["requirement"], "source_id": gate_map[gate_id]["source_id"],
            })
        qualified = all(gate_id in passed for gate_id in required)
        leaderboard.append({
            **{key: strategy[key] for key in ("strategy_id", "strategy", "category", "hypothesis", "source_id")},
            "rank": None, "qualified": qualified, "status": "QUALIFIED" if qualified else "NOT QUALIFIED",
            "passed_gates": len(passed), "required_gates": len(required),
            "failed_gate_ids": [gate_id for gate_id in required if gate_id not in passed],
            "observed_n": 0, "brier_skill": None, "roi": None, "clv": None, "reward_points": 0 if not qualified else None,
        })
    assert not any(row["qualified"] for row in leaderboard)
    return leaderboard, gate_rows


def build_derived(data: dict | None = None) -> dict:
    data = data or load_data()
    props, combos = calculate_player_props(data)
    leaderboard, gate_rows = evaluate_strategies(data)
    correlations = calculate_correlations(data)
    return {
        "metadata": {
            "as_of": AS_OF, "season": SEASON, "prior_games": PRIOR_GAMES, "home_advantage": HOME_ADVANTAGE,
            "logistic_scale": LOGISTIC_SCALE, "min_out_of_sample": MIN_OUT_OF_SAMPLE,
            "team_rows": len(data["teams"]), "schedule_rows": len(data["schedule"]), "player_game_rows": len(data["player_games"]),
            "qualified_strategies": sum(row["qualified"] for row in leaderboard),
            "player_holm_rejections_005": sum(row["p_holm"] is not None and row["p_holm"] < 0.05 for row in correlations),
        },
        "league": league_metrics(data["teams"]), "lines": calculate_lines(data), "correlations": correlations,
        "player_props": props, "prop_combos": combos, "leaderboard": leaderboard, "gate_rows": gate_rows,
        "gates": GATES, "flags": data["flags"],
    }


def write_derived(path: Path | None = None) -> dict:
    derived = build_derived()
    destination = path or DATA / "derived.json"
    destination.write_text(json.dumps(derived, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return derived


if __name__ == "__main__":
    result = write_derived()
    print(json.dumps(result["metadata"], indent=2))

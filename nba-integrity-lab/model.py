#!/usr/bin/env python3
"""Reproducible, deliberately non-executable NBA research calculations.

The NBA publishes the inputs, not these lines, thresholds, correlations, or
policies. Inputs are a reviewed, fixed snapshot: there is no live data feed,
no bookmaker quotation, no injury adjustment, and no certified strategy.
"""
from __future__ import annotations

import csv
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
NBA_LOG = "https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26"
NBA_ADVANCED = "https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season"
NBA_INJURY = "https://official.nba.com/nba-injury-report-2026-27-season/"
NBA_INJURY_SNAPSHOT = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf"
NIST_BINOMIAL = "https://www.itl.nist.gov/div898/handbook/eda/section3/eda366i.htm"
SPORTSBOOK_SGP = "https://sportsbook.draftkings.com/same-game-parlay"
REPO = "https://github.com/sassnarep3-star/Own5"

# Analyst choices made after examining the dataset, not validated parameters.
PRIOR_GAMES = 20
HOME_COURT_POINTS = 0.0
MIN_GRADED_BETS = 200
ALPHA = 0.05


def load_csv(filename: str) -> list[dict[str, str]]:
    with (DATA / filename).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def is_nba_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        return parsed.scheme == "https" and (host == "nba.com" or host.endswith(".nba.com"))
    except ValueError:
        return False


def load_inputs() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    teams = load_csv("team_snapshot.csv")
    games = load_csv("schedule_snapshot.csv")
    logs = load_csv("edwards_sample.csv")
    validate_inputs(teams, games, logs)
    return teams, games, logs


def validate_inputs(teams: list[dict[str, str]], games: list[dict[str, str]],
                    logs: list[dict[str, str]]) -> None:
    """Integrity checks are not a substitute for independent source review."""
    if len(teams) != 18 or len(games) != 9 or len(logs) != 25:
        raise ValueError("unexpected reviewed snapshot size")
    by_abbr = {row["abbr"]: row for row in teams}
    if len(by_abbr) != len(teams) or len({r["team_id"] for r in teams}) != len(teams):
        raise ValueError("duplicate team")
    for row in teams:
        if not is_nba_url(row["source_url"]):
            raise ValueError("missing official NBA team source")
        gp = int(row["gp"])
        off, defense, net, pace = (float(row[k]) for k in ("off_rtg", "def_rtg", "net_rtg", "pace"))
        if gp <= 0 or not all(math.isfinite(v) for v in (off, defense, net, pace)) or pace <= 0:
            raise ValueError("invalid team data")
        # Each rating is separately rounded by the NBA; their displayed
        # difference can differ by 0.1 and must not be silently rewritten.
        if abs((off - defense) - net) > 0.16:
            raise ValueError("displayed net rating outside rounding tolerance")
    used = set()
    for game in games:
        a, h = game["away"], game["home"]
        if a == h or a not in by_abbr or h not in by_abbr or a in used or h in used:
            raise ValueError("invalid or duplicate slate team")
        used.update((a, h))
        if game["game_date"] != "2026-11-06" or not all(
            is_nba_url(game[k]) for k in ("source_url", "time_source_url")
        ):
            raise ValueError("missing official NBA schedule source")
    if used != set(by_abbr):
        raise ValueError("slate and team snapshot do not match")
    seen = set()
    for row in logs:
        game_id = row["game_id"]
        if game_id in seen or not (len(game_id) == 10 and game_id.isdigit()):
            raise ValueError("duplicate or invalid game ID")
        seen.add(game_id)
        if not is_nba_url(row["source_url"]) or not is_nba_url(row["game_url"]):
            raise ValueError("missing official player-log source")
        if row["result"] not in ("W", "L"):
            raise ValueError("invalid result")
        if any(int(row[k]) < 0 for k in ("minutes", "points", "three_made", "rebounds", "assists")):
            raise ValueError("invalid player statistic")
        if int(row["points"]) < 3 * int(row["three_made"]):
            raise ValueError("points lower than points from made threes")


def pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("paired samples of equal length >= 2 required")
    if not all(math.isfinite(v) for v in x + y):
        raise ValueError("non-finite sample")
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy)


def binary_stats(a: list[bool], b: list[bool]) -> dict:
    if len(a) != len(b) or not a:
        raise ValueError("matched non-empty binary vectors required")
    if any(type(v) is not bool for v in a + b):
        raise ValueError("binary vectors must contain bools")
    n = len(a)
    n11 = sum(x and y for x, y in zip(a, b))
    n10 = sum(x and not y for x, y in zip(a, b))
    n01 = sum(not x and y for x, y in zip(a, b))
    n00 = n - n11 - n10 - n01
    p_a, p_b = sum(a) / n, sum(b) / n
    joint, product = n11 / n, p_a * p_b
    denominator = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    return {"n": n, "n11": n11, "n10": n10, "n01": n01, "n00": n00,
            "p_a": p_a, "p_b": p_b, "joint": joint, "product": product,
            "lift": joint / product if product else None,
            "phi": (n11 * n00 - n10 * n01) / denominator if denominator else None}


def joint_from_phi(p_a: float, p_b: float, phi: float) -> float:
    if not all(math.isfinite(v) for v in (p_a, p_b, phi)):
        raise ValueError("non-finite probability or phi")
    if not 0 < p_a < 1 or not 0 < p_b < 1 or not -1 <= phi <= 1:
        raise ValueError("phi requires non-degenerate marginal probabilities and must be in [-1, 1]")
    joint = p_a * p_b + phi * math.sqrt(p_a * (1 - p_a) * p_b * (1 - p_b))
    lower, upper = max(0.0, p_a + p_b - 1), min(p_a, p_b)
    if joint < lower - 1e-12 or joint > upper + 1e-12:
        raise ValueError("infeasible joint probability for the supplied marginals")
    return min(upper, max(lower, joint))


def american_decimal(odds: int) -> float:
    """Decimal odds; no commission, taxes, voids or pushes are included."""
    if isinstance(odds, bool) or not isinstance(odds, int) or -100 < odds < 100:
        raise ValueError("American odds must be an integer <= -100 or >= 100")
    return 1 + (odds / 100 if odds > 0 else 100 / abs(odds))


def log_score_lift(outcome: int, model_p: float, benchmark_p: float) -> float:
    """Log-score improvement for one binary outcome, not a payout or ROI.

    Probability forecasts must be frozen before the event, and the benchmark
    must be an independently recorded, comparable no-push market. Aggregation,
    uncertainty and qualification require separate audited evidence.
    """
    if isinstance(outcome, bool) or not isinstance(outcome, int) or outcome not in (0, 1):
        raise ValueError("outcome must be integer 0 or 1")
    if not all(not isinstance(p, bool) and isinstance(p, (int, float)) and math.isfinite(p) and 0 < p < 1
               for p in (model_p, benchmark_p)):
        raise ValueError("probabilities must be finite and strictly between 0 and 1")
    return (math.log(model_p / benchmark_p) if outcome == 1
            else math.log((1 - model_p) / (1 - benchmark_p)))


def binomial_tail(k: int, n: int, p: float) -> float:
    """P(X >= k), with X~Binomial(n,p), summing PMFs in the log domain."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 0 or not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError("invalid binomial parameters")
    if isinstance(k, bool) or not isinstance(k, int):
        raise ValueError("k must be an integer")
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if p == 0:
        return 0.0
    if p == 1:
        return 1.0
    terms = (math.exp(math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                      + i * math.log(p) + (n - i) * math.log1p(-p))
             for i in range(k, n + 1))
    return min(1.0, max(0.0, math.fsum(terms)))


def critical_wins(n: int, p_null: float, alpha: float) -> int:
    """First k with P_null(X >= k) <= alpha, including the no-rejection k=n+1."""
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    # binomial_tail also validates n/p_null.
    binomial_tail(0, n, p_null)
    lo, hi = 0, n + 1
    while lo < hi:
        mid = (lo + hi) // 2
        if binomial_tail(mid, n, p_null) <= alpha:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _utc(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.astimezone(timezone.utc) if result.tzinfo is not None else None
    except (ValueError, OverflowError):
        return None


def evaluate_gates(evidence: dict) -> dict[str, bool]:
    """Fail-closed policy checks on supplied evidence, NOT external verification.

    True attestations must be backed by independently audited source/ledger
    records; this helper cannot obtain or authenticate them. All gates apply
    to all divisions; dependence means stake/result dependence for singles and
    joint-leg dependence for combos. P-values must be generated by a valid,
    registered test for the actual outcome/price/dependence structure.
    """
    cutoff = _utc(evidence.get("feature_cutoff"))
    decision = _utc(evidence.get("decision_time"))
    event = _utc(evidence.get("event_time"))
    quote = _utc(evidence.get("quote_time"))
    freeze = _utc(evidence.get("registered_at"))
    holdout = _utc(evidence.get("holdout_start"))
    n = evidence.get("graded_bets")
    trials = evidence.get("registered_trials")
    p = evidence.get("raw_p_value")
    valid_p = (not isinstance(p, bool) and isinstance(p, (int, float))
               and math.isfinite(p) and 0 <= p <= 1)
    valid_trials = not isinstance(trials, bool) and isinstance(trials, int) and trials >= 1
    return {
        "G01": evidence.get("source_reviewed") is True,
        "G02": bool(cutoff and decision and event and quote and cutoff <= decision < event and quote <= decision),
        "G03": bool(freeze and holdout and decision and event and freeze < holdout <= decision < event
                    and evidence.get("registration_audited") is True),
        "G04": evidence.get("quote_and_rules_reviewed") is True,
        "G05": evidence.get("outcomes_reviewed") is True and evidence.get("holdout_disjoint") is True,
        "G06": not isinstance(n, bool) and isinstance(n, int) and n >= MIN_GRADED_BETS,
        "G07": evidence.get("dependence_reviewed") is True,
        "G08": bool(valid_p and valid_trials and p <= ALPHA / trials and evidence.get("test_validated") is True),
        "G09": evidence.get("independent_replication") is True,
        "G10": evidence.get("reproducible") is True and evidence.get("risk_and_reward_controls") is True,
    }


def originate(teams: list[dict[str, str]], games: list[dict[str, str]]) -> list[dict]:
    """Research-only point spread/total; no odds, win probabilities or picks.

    Equal blend of each offense and the opposing defense for raw total.
    Spread separately shrinks each displayed net rating toward zero with a
    20-game analyst prior. Zero home-court effect is an explicit assumption.
    Team PACE is per 48 minutes; there is no separate overtime adjustment.
    """
    lookup = {r["abbr"]: r for r in teams}
    results = []
    for game in games:
        away, home = lookup[game["away"]], lookup[game["home"]]
        pace = (float(away["pace"]) + float(home["pace"])) / 2
        total = pace / 100 * ((float(home["off_rtg"]) + float(away["def_rtg"])) / 2
                              + (float(away["off_rtg"]) + float(home["def_rtg"])) / 2)
        wh = int(home["gp"]) / (int(home["gp"]) + PRIOR_GAMES)
        wa = int(away["gp"]) / (int(away["gp"]) + PRIOR_GAMES)
        margin = pace / 200 * (wh * float(home["net_rtg"]) - wa * float(away["net_rtg"])) + HOME_COURT_POINTS
        results.append({**game, "model_home_margin": margin, "model_home_spread": -margin,
                        "model_total": total, "pace_blend": pace, "market_spread": None,
                        "market_total": None, "market_odds": None,
                        "source_url": game["source_url"],
                        "team_source_home": home["source_url"], "team_source_away": away["source_url"]})
    return results


def analyze(logs: list[dict[str, str]]) -> dict:
    columns = {k: [float(r[k]) for r in logs] for k in ("points", "three_made", "rebounds", "assists", "minutes")}
    pairs = [("Points × made threes", "points", "three_made"),
             ("Points × rebounds", "points", "rebounds"),
             ("Points × assists", "points", "assists"),
             ("Rebounds × assists", "rebounds", "assists"),
             ("Minutes × points", "minutes", "points")]
    continuous = [{"pair": name, "n": len(logs), "r": pearson(columns[a], columns[b])}
                  for name, a, b in pairs]
    chronological = sorted(logs, key=lambda r: r["game_date"])
    pts = [float(r["points"]) for r in chronological]
    continuous.append({"pair": "Points in consecutive appearances (lag 1)",
                       "n": len(pts) - 1, "r": pearson(pts[:-1], pts[1:])})
    a = [int(r["points"]) >= 25 for r in logs]
    threes = [int(r["three_made"]) >= 3 for r in logs]
    rebounds = [int(r["rebounds"]) >= 5 for r in logs]
    assists = [int(r["assists"]) >= 5 for r in logs]
    binary = []
    for label, other in (("Points ≥25 AND threes ≥3", threes),
                         ("Points ≥25 AND rebounds ≥5", rebounds),
                         ("Points ≥25 AND assists ≥5", assists)):
        binary.append({"pair": label, **binary_stats(a, other)})
    three_count = sum(x and y and z for x, y, z in zip(a, rebounds, assists))
    product3 = sum(a) / len(a) * sum(rebounds) / len(a) * sum(assists) / len(a)
    triple = {"name": "Points ≥25 AND rebounds ≥5 AND assists ≥5", "n": len(a),
              "joint_count": three_count, "joint": three_count / len(a), "product": product3,
              "lift": three_count / len(a) / product3 if product3 else None}
    p_null = 1 / american_decimal(-110)
    examples = []
    for n, m in ((50, 1), (200, 1), (1000, 1), (2243, 1), (2243, 6)):
        level = ALPHA / m
        k = critical_wins(n, p_null, level)
        examples.append({"n": n, "trials": m, "alpha": level, "critical_wins": k,
                         "null_tail": binomial_tail(k, n, p_null),
                         "power_at_55": binomial_tail(k, n, 0.55)})
    return {"continuous": continuous, "binary": binary, "triple": triple,
            "p_null_minus_110": p_null, "tail_30_of_50": binomial_tail(30, 50, p_null),
            "binomial_examples": examples}


def build_results() -> dict:
    teams, games, logs = load_inputs()
    return {"teams": teams, "games": games, "logs": logs, "lines": originate(teams, games),
            "analysis": analyze(logs), "gates_without_evidence": evaluate_gates({})}

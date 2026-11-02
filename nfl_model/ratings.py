"""Transparent, unvalidated points-rating and independent-Poisson baseline."""
from __future__ import annotations

import math
from .math_utils import probability_to_american

MODEL_VERSION = "points-poisson-v0.1"
SHRINKAGE_PSEUDOGAMES = 8.0
MAX_SCORE = 100


def team_ratings(teams: list[dict], k: float = SHRINKAGE_PSEUDOGAMES) -> tuple[dict[str, dict], float]:
    if k < 0 or not teams:
        raise ValueError("Nonnegative shrinkage and at least one team are required")
    games = []
    for t in teams:
        n = t["wins"] + t["losses"] + t["ties"]
        if n <= 0 or t["points_for"] < 0 or t["points_against"] < 0:
            raise ValueError("Invalid official team totals")
        games.append(n)
    mu = sum(t["points_for"] for t in teams) / sum(games)
    if mu <= 0:
        raise ValueError("League scoring rate must be positive")
    ratings = {}
    for t, n in zip(teams, games):
        ratings[t["team_code"]] = {
            "games": n,
            "points_for_per_game": t["points_for"] / n,
            "points_against_per_game": t["points_against"] / n,
            "attack": (t["points_for"] + k * mu) / (n + k),
            "defense": (t["points_against"] + k * mu) / (n + k),
        }
    return ratings, mu


def poisson_pmf(lam: float, maximum: int = MAX_SCORE) -> list[float]:
    if not math.isfinite(lam) or lam <= 0 or maximum < 1:
        raise ValueError("Positive finite rate and positive maximum required")
    probs = [math.exp(-lam)]
    for x in range(1, maximum + 1):
        probs.append(probs[-1] * lam / x)
    return probs


def median_from_pmf(pmf: list[float]) -> int:
    cumulative = 0.0
    for i, p in enumerate(pmf):
        cumulative += p
        if cumulative >= 0.5:
            return i
    return len(pmf) - 1


def project_game(game: dict, ratings: dict[str, dict], league_mean: float,
                 *, k: float = SHRINKAGE_PSEUDOGAMES) -> dict:
    """Return derived research quantities. Never reads or invents market prices."""
    away, home = ratings[game["away"]], ratings[game["home"]]
    lam_away = away["attack"] * home["defense"] / league_mean
    lam_home = home["attack"] * away["defense"] / league_mean
    pa, ph = poisson_pmf(lam_away), poisson_pmf(lam_home)
    win = tie = loss = over = under = total_push = 0.0
    margin_pmf: dict[int, float] = {}
    total_pmf: dict[int, float] = {}
    # Exact truncated convolution; no sampling and no sportsbook input.
    convolution = [0.0] * (2 * MAX_SCORE + 1)
    for a, x in enumerate(pa):
        for h, y in enumerate(ph):
            p = x * y
            margin = h - a
            margin_pmf[margin] = margin_pmf.get(margin, 0.0) + p
            total_pmf[a + h] = total_pmf.get(a + h, 0.0) + p
            convolution[a + h] += p
            if margin > 0:
                win += p
            elif margin == 0:
                tie += p
            else:
                loss += p
    fair_total = median_from_pmf(convolution)
    margin_median_index = median_from_pmf([margin_pmf.get(m, 0.0) for m in range(-MAX_SCORE, MAX_SCORE + 1)])
    median_margin_home = margin_median_index - MAX_SCORE
    fair_spread = -median_margin_home
    for total, p in total_pmf.items():
        if total > fair_total:
            over += p
        elif total < fair_total:
            under += p
        else:
            total_push += p
    no_tie = win + loss
    home_two_way = win / no_tie if no_tie > 0 else None
    away_two_way = loss / no_tie if no_tie > 0 else None
    return {
        "game_id": game["game_id"], "away": game["away"], "home": game["home"],
        "away_name": game["away_name"], "home_name": game["home_name"],
        "date": game["date"], "local_time": game["local_time"],
        "neutral_site": game["neutral_site"],
        "lambda_away": lam_away, "lambda_home": lam_home,
        "expected_margin_home": lam_home - lam_away,
        "fair_spread_home": fair_spread, "fair_total": fair_total,
        "home_win_probability": win, "tie_probability": tie, "away_win_probability": loss,
        "home_two_way_probability": home_two_way, "away_two_way_probability": away_two_way,
        "home_fair_american": probability_to_american(home_two_way),
        "away_fair_american": probability_to_american(away_two_way),
        "over_probability_at_fair_total": over, "under_probability_at_fair_total": under,
        "total_push_probability": total_push,
        "truncation_tail_mass": max(0.0, 1 - sum(pa) * sum(ph)),
        "market_spread": None, "market_total": None, "market_american": None,
        "market_edge": None, "clv": None, "injury_adjustment": None,
        "weather_adjustment": None, "empirical_home_advantage": None,
        "model_version": MODEL_VERSION, "shrinkage_pseudogames": k,
        "home_advantage_assumption": 0.0,
        "status": "Research only — not validated",
        "source_ids": ["S10", "S11"],
        "source_urls": [
            "https://www.nfl.com/standings/league/2026/REG", game["source_url"]
        ],
        "derived": True,
    }

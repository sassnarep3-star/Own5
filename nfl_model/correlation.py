"""Descriptive paired-player correlation; never a universal SGP coefficient."""
from __future__ import annotations

import math
from .math_utils import bootstrap_ci, joint_bounds, mean, pearson, phi, spearman, wilson

PASS_THRESHOLD = 250
RECEIVING_THRESHOLD = 75


def analyze_pair(games: list[dict], *, draws: int = 10000) -> dict:
    x = [g["burrow_passing_yards"] for g in games]
    y = [g["chase_receiving_yards"] for g in games]
    a = [int(v >= PASS_THRESHOLD) for v in x]
    b = [int(v >= RECEIVING_THRESHOLD) for v in y]
    n = len(games)
    hits_b = sum(b)
    joint = sum(i * j for i, j in zip(a, b))
    pa, pb = mean(a), mean(b)
    pj = joint / n if n else None
    independent = pa * pb if n else None
    r = pearson(x, y)
    rows = list(zip(x, y))
    r_ci = bootstrap_ci(rows, lambda s: pearson([v[0] for v in s], [v[1] for v in s]), draws=draws)
    j_ci = wilson(joint, n) if n else None
    phi_ci = bootstrap_ci(list(zip(a, b)), lambda s: phi([v[0] for v in s], [v[1] for v in s]), draws=draws)
    return {
        "id": "burrow-chase-2024", "season": 2024, "n_games": n,
        "passing_threshold": PASS_THRESHOLD, "receiving_threshold": RECEIVING_THRESHOLD,
        "pearson_r": r, "pearson_ci95": list(r_ci),
        "spearman_r": spearman(x, y),
        "binary_phi": phi(a, b), "binary_phi_ci95": list(phi_ci),
        "passing_hits": sum(a), "receiving_hits": hits_b, "joint_hits": joint,
        "passing_rate": pa, "receiving_rate": pb, "joint_rate": pj,
        "joint_wilson_ci95": list(j_ci) if j_ci else [None, None],
        "independence_product": independent,
        "joint_minus_independent": pj - independent if n else None,
        "joint_lift": pj / independent if independent else None,
        "joint_frechet_bounds": list(joint_bounds(pa, pb)) if n else [None, None],
        "fair_joint_decimal": 1 / pj if pj else None,
        "source_ids": ["S12", "S13"],
        "source_urls": ["https://www.nfl.com/players/joe-burrow/stats/logs/2024/", "https://www.nfl.com/players/ja-marr-chase/stats/logs/2024/"],
        "derived": True, "status": "Descriptive; not a current betting signal",
        "current_pair_correlation": None, "sgp_fair_price": None,
        "bootstrap_draws": draws, "bootstrap_seed": 20261102,
        "limitations": "One selected QB–WR pair, one season, 17 games. No current participation, operator price, or out-of-sample joint calibration. Bootstrap intervals do not cure selection bias.",
    }

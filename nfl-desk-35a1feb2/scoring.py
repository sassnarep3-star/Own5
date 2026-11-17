"""scoring.py — the leaderboard scorer, implemented and tested before any week settles.

Kept deliberately small and deterministic (no RNG): the uncertainty bound is a normal approximation on
game-cluster residuals, which is what the "game-cluster lower bound" rule in the brief asks for. It is used
by no page until a registered week has settled.
"""
from __future__ import annotations
import math
from collections import defaultdict

Z = 1.959963984540054


def brier(pairs):
    """pairs: iterable of (predicted_probability_of_the_outcome, outcome 0/1)."""
    n = len(list(pairs))
    if not n:
        raise ValueError("no forecasts")
    s = sum((p - y) ** 2 for p, y in pairs)
    return s / n


def constant_brier(outcomes):
    ys = [y for _, y in outcomes]
    base = sum(ys) / len(ys)
    return sum((base - y) ** 2 for y in ys) / len(ys)


def log_loss(pairs):
    """Mean negative log likelihood, eps-clipped. The brief asks for a Brier benchmark, so the scoring rule
    is Brier; log loss is published alongside because it is strictly proper and a constant forecast cannot
    beat it by being confident."""
    e = 1e-12
    return -sum((y * math.log(max(p, e)) + (1 - y) * math.log(max(1 - p, e))) for p, y in pairs) / len(pairs)


def skill(pairs):
    """Brier skill against the base-rate benchmark. >0 means better than always guessing the base rate."""
    return 1.0 - brier(pairs) / constant_brier(pairs)


def clustered_se(pairs, clusters):
    """(mean squared error, standard error of that mean, number of clusters), with the standard error taken
    ACROSS CLUSTERS. Which cluster label you use changes the answer, and that is the point: a parlay whose
    legs all settle on one game has the information content of that one game, not of four rows. A hedged
    bettor whose every game nets the same score has a standard error of zero and has learned nothing - the
    game-cluster view exposes it, the per-row view hides it."""
    by = defaultdict(list)
    for (p, y), c in zip(pairs, clusters):
        by[c].append((p - y) ** 2)
    means = [sum(v) / len(v) for v in by.values()]
    m = len(means)
    if m < 2:
        return (sum(means) / m, float("inf"), m)   # one cluster: the standard error does not exist
    pt = sum(means) / m
    var = sum((x - pt) ** 2 for x in means) / (m - 1)
    return (pt, math.sqrt(var / m), m)


def clustered_lower_bound(pairs, clusters, z=Z):
    """Point estimate minus z * se, where se is computed on cluster means (all legs of one game move
    together, so per-forecast independence would overstate the information in a parlay)."""
    pt, se, m = clustered_se(pairs, clusters)
    if m < 2:
        return float("nan")
    return pt - z * se


def bonferroni(alpha, trials):
    return alpha / trials if trials else float("nan")


def wilson(k, n, z=Z):
    if not n:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def power_bets(p_true, p_break_even=0.5, power=0.80, alpha=0.05):
    """Bets needed to tell a p_true bettor off a break-even one, one-sided normal approximation.
    Documents the sample the brief's 'remove luck' rule actually requires."""
    za = 1.6448536269514722 if alpha == 0.05 else Z
    zb = 0.8416212335729143 if power == 0.80 else 1.2815515655446004
    sd = 0.5
    return math.ceil(((za + zb) * sd / (p_true - p_break_even)) ** 2)

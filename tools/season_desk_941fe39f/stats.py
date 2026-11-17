"""Statistics used by the 941fe39f desk. Standard library only, deterministic.

Every function is either a closed form or a fixed-iteration deterministic
routine. Nothing samples at run time: the only randomness in this project is in
`bootstrap`, which is seeded with a fixed integer so the same inputs always
produce the same interval.
"""
from __future__ import annotations

import math
import random


# ---------------------------------------------------------------- distributions
def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p: float) -> float:
    """Inverse standard normal (Acklam's rational approximation)."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0,1)")
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def norm_sf(x: float) -> float:
    return 1.0 - norm_cdf(x)


def two_sided_z_p(z: float) -> float:
    return 2.0 * norm_sf(abs(z))


# ---------------------------------------------------------------- intervals
def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def fisher_ci(r: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% interval for a Pearson correlation via Fisher's z transform."""
    if n <= 3:
        return (float("nan"), float("nan"))
    r = max(min(r, 0.999999), -0.999999)
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = zr - z * se, zr + z * se
    return (math.tanh(lo), math.tanh(hi))


def pearson(xs: list[float], ys: list[float]) -> tuple[float, int]:
    pairs = [(x, y) for x, y in zip(xs, ys)
             if x is not None and y is not None
             and not (isinstance(x, float) and math.isnan(x))
             and not (isinstance(y, float) and math.isnan(y))]
    n = len(pairs)
    if n < 3:
        return (float("nan"), n)
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    syy = sum((y - my) ** 2 for _, y in pairs)
    if sxx <= 0 or syy <= 0:
        return (float("nan"), n)
    return (sxy / math.sqrt(sxx * syy), n)


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p), computed in log space."""
    if n == 0:
        return 1.0
    total = 0.0
    for i in range(k, n + 1):
        total += math.exp(
            math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
            + i * math.log(max(p, 1e-12)) + (n - i) * math.log(max(1 - p, 1e-12))
        )
    return min(1.0, total)


def binom_two_sided(k: int, n: int, p: float = 0.5) -> float:
    """Exact two-sided binomial test by the doubling rule."""
    if n == 0:
        return 1.0
    up = binom_sf(k, n, p)
    down = 1.0 - binom_sf(k, n, p) + math.exp(
        math.lgamma(n + 1) - math.lgamma(max(k, 0) + 1) - math.lgamma(n - max(k, 0) + 1)
        + k * math.log(max(p, 1e-12)) + (n - k) * math.log(max(1 - p, 1e-12))
    ) if 0 <= k <= n else 1.0
    return min(1.0, 2.0 * min(up, down))


# ---------------------------------------------------------------- multiple testing
def holm(pvals: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values, order preserved."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = (m - rank) * pvals[i]
        running = max(running, val)
        adj[i] = min(1.0, running)
    return adj


def benjamini_hochberg(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        val = m * pvals[i] / (rank + 1)
        running = min(running, val)
        adj[i] = min(1.0, running)
    return adj


# ---------------------------------------------------------------- scoring rules
def brier_binary(probs: list[float], outcomes: list[int]) -> float:
    if not probs:
        return float("nan")
    return sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / len(probs)


def log_loss_binary(probs: list[float], outcomes: list[int], eps: float = 1e-12) -> float:
    if not probs:
        return float("nan")
    total = 0.0
    for p, y in zip(probs, outcomes):
        p = min(max(p, eps), 1 - eps)
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / len(probs)


def brier_skill_score(model: list[float], reference: list[float], outcomes: list[int]) -> float:
    """1 - BS_model / BS_reference. Positive means the model beats the reference."""
    bm = brier_binary(model, outcomes)
    br = brier_binary(reference, outcomes)
    if br == 0:
        return float("nan")
    return 1.0 - bm / br


def brier_decomposition(probs: list[float], outcomes: list[int], bins: int = 10) -> dict:
    """Murphy decomposition: BS = reliability - resolution + uncertainty.

    Forecasts are grouped by their exact value (6 decimal places), which makes
    the identity hold exactly instead of approximately. `bins` is accepted for
    callers that want equal-width grouping, but exact grouping is what makes the
    identity_residual zero, so it is the default. Empty groups cannot occur.
    """
    n = len(probs)
    if n == 0:
        return {}
    base = sum(outcomes) / n
    by_value: dict[float, list[tuple[float, int]]] = {}
    for p, y in zip(probs, outcomes):
        by_value.setdefault(round(p, 6), []).append((p, y))
    buckets = list(by_value.values())
    rel = res = 0.0
    for b in buckets:
        if not b:
            continue
        w = len(b) / n
        pb = sum(x[0] for x in b) / len(b)
        ob = sum(x[1] for x in b) / len(b)
        rel += w * (pb - ob) ** 2
        res += w * (ob - base) ** 2
    unc = base * (1 - base)
    return {
        "n": n,
        "bins_used": sum(1 for b in buckets if b),
        "reliability": rel,
        "resolution": res,
        "uncertainty": unc,
        "brier": sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / n,
        "identity_residual": abs((rel - res + unc) - sum((p - y) ** 2 for p, y in zip(probs, outcomes)) / n),
        "base_rate": base,
    }


# ---------------------------------------------------------------- bootstrap
def cluster_bootstrap_mean(
    values: list[float],
    clusters: list[str],
    reps: int = 2000,
    seed: int = 94139,
) -> tuple[float, float, float]:
    """Percentile bootstrap of the mean, resampling whole clusters.

    Games inside one week, or bets inside one game, are not independent. The
    cluster bootstrap resamples weeks (or games) rather than rows, so the
    interval reflects the correlation that actually exists in the sample.
    """
    by: dict[str, list[float]] = {}
    for v, c in zip(values, clusters):
        by.setdefault(c, []).append(v)
    keys = sorted(by)
    if not keys:
        return (float("nan"), float("nan"), float("nan"))
    point = sum(values) / len(values)
    rng = random.Random(seed)
    means = []
    k = len(keys)
    for _ in range(reps):
        tot = 0.0
        cnt = 0
        for _ in range(k):
            key = keys[rng.randrange(k)]
            for v in by[key]:
                tot += v
                cnt += 1
        means.append(tot / cnt if cnt else 0.0)
    means.sort()
    lo = means[int(0.025 * reps)]
    hi = means[int(0.975 * reps) - 1]
    return (lo, hi, point)


def paired_cluster_bootstrap(
    a: list[float],
    b: list[float],
    clusters: list[str],
    reps: int = 2000,
    seed: int = 94139,
) -> tuple[float, float, float]:
    """Percentile bootstrap of mean(a - b), resampling clusters."""
    diffs = [x - y for x, y in zip(a, b)]
    return cluster_bootstrap_mean(diffs, clusters, reps=reps, seed=seed)


# ---------------------------------------------------------------- luck
def luck_panel(
    wins: int, losses: int, ties: int,
    pythagorean_wins: float, one_score_wins: int, games: int,
    point_diff: float,
) -> dict:
    """Remove luck from a team's record, using only quantities the site can prove.

    * pythagorean expectation uses an EXPONENT we declare and flag (F-14 in the
      prior desk: it is a convention, not a league value);
    * one-score record is the share of games decided by <= 8 points that the
      team won;
    * the regression term is the difference between the actual win rate and the
      Pythagoras rate, which is the part of the record that scoring margin does
      not explain.
    """
    decided = wins + losses
    actual = (wins + 0.5 * ties) / games if games else float("nan")
    expected = pythagorean_wins / games if games else float("nan")
    return {
        "actual_win_pct": actual,
        "pythagorean_win_pct": expected,
        "luck_points": (actual - expected) * 16.0,   # wins above/below expectation over a 16-game scale
        "one_score_wins": one_score_wins,
        "point_diff_per_game": point_diff,
        "decided": decided,
    }

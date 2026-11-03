"""Pure statistics for the NBA Line Desk (standard library only).

Every function is deterministic. Permutation tests use an explicit seed.
Nothing here fetches data; inputs come from the verified CSVs in data/nba-2026-27/.
"""
from __future__ import annotations

import math
import random
from statistics import NormalDist

_N = NormalDist()


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def pearson(x, y):
    """Pearson product-moment correlation. Raises if either series is constant."""
    x = list(x)
    y = list(y)
    if len(x) != len(y) or len(x) < 3:
        raise ValueError("need two equal-length series with n >= 3")
    mx, my = mean(x), mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        raise ValueError("constant series has no correlation")
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n, level=0.95):
    """Approximate CI for r via Fisher z (normal approximation)."""
    if n <= 3:
        raise ValueError("Fisher CI needs n > 3")
    z = math.atanh(max(min(r, 0.999999), -0.999999))
    se = 1.0 / math.sqrt(n - 3)
    q = _N.inv_cdf(0.5 + level / 2)
    return math.tanh(z - q * se), math.tanh(z + q * se)


def fisher_p_two_sided(r, n):
    """Two-sided p-value for H0: rho = 0 via Fisher z (normal approximation)."""
    z = math.atanh(max(min(r, 0.999999), -0.999999)) * math.sqrt(n - 3)
    return 2 * (1 - _N.cdf(abs(z)))


def permutation_p(x, y, n_perm=10000, seed=20261103):
    """Two-sided permutation p-value for |r| with y shuffled. Add-one correction."""
    x = list(x)
    y = list(y)
    r_obs = abs(pearson(x, y))
    rng = random.Random(seed)
    shuffled = y[:]
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(shuffled)
        if abs(pearson(x, shuffled)) >= r_obs - 1e-12:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def ols_fit(x, y):
    """Return (slope, intercept) of y ~ x by least squares."""
    x = list(x)
    y = list(y)
    mx, my = mean(x), mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    if sxx == 0:
        raise ValueError("constant x")
    slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx
    return slope, my - slope * mx


def binom_two_sided_p(k, n, p=0.5):
    """Exact two-sided binomial p-value (sum of probabilities no larger than observed)."""
    if not 0 <= k <= n:
        raise ValueError("k out of range")
    probs = [math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(n + 1)]
    observed = probs[k]
    total = sum(pr for pr in probs if pr <= observed * (1 + 1e-9))
    return min(1.0, total)


def wilson_ci(k, n, level=0.95):
    """Wilson score interval for a binomial proportion."""
    if n <= 0:
        raise ValueError("n must be positive")
    z = _N.inv_cdf(0.5 + level / 2)
    phat = k / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return centre - half, centre + half


def required_n_two_proportions_vs_half(p1, p0=0.5, alpha=0.05, power=0.8):
    """Normal-approximation sample size to detect p1 vs p0 (two-sided alpha)."""
    if p1 == p0:
        raise ValueError("p1 must differ from p0")
    za = _N.inv_cdf(1 - alpha / 2)
    zb = _N.inv_cdf(power)
    num = za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))
    return math.ceil((num / abs(p1 - p0)) ** 2)


def games_for_half_width(half_width, p=0.5, level=0.95):
    """Sample size so that a binomial proportion has a CI half-width <= half_width."""
    z = _N.inv_cdf(0.5 + level / 2)
    return math.ceil((z / half_width) ** 2 * p * (1 - p))


def american_breakeven(odds):
    """Break-even win probability implied by American odds (arithmetic identity)."""
    if odds == 0:
        raise ValueError("odds cannot be zero")
    if odds < 0:
        return -odds / (-odds + 100)
    return 100 / (odds + 100)


def bonferroni_alpha(alpha, k):
    if k < 1:
        raise ValueError("k must be >= 1")
    return alpha / k

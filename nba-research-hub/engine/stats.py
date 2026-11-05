"""Small standard-library statistical helpers used by the frozen protocol."""
from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Callable, Iterable, Sequence


def mean(xs: Sequence[float]) -> float:
    if not xs:
        raise ValueError("mean requires at least one value")
    return sum(xs) / len(xs)


def sd(xs: Sequence[float], ddof: int = 1) -> float:
    if len(xs) <= ddof:
        raise ValueError("not enough values for requested ddof")
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - ddof))


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    mx, my = mean(xs), mean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def normal_cdf(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    if sigma <= 0:
        return 1.0 if x >= mu else 0.0
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2.0))))


def normal_sf(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    return 1.0 - normal_cdf(x, mu, sigma)


def log_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return -math.inf
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def binom_pmf(k: int, n: int, p: float) -> float:
    if k < 0 or k > n:
        return 0.0
    if p <= 0:
        return 1.0 if k == 0 else 0.0
    if p >= 1:
        return 1.0 if k == n else 0.0
    return math.exp(log_choose(n, k) + k * math.log(p) + (n - k) * math.log1p(-p))


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k), summing upward from the requested tail for stability."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    term = binom_pmf(k, n, p)
    total = term
    for i in range(k, n):
        term *= (n - i) / (i + 1) * p / (1 - p)
        total += term
    return min(1.0, max(0.0, total))


def binom_critical(n: int, p: float, alpha: float) -> int:
    lo, hi = 0, n + 1
    while lo < hi:
        mid = (lo + hi) // 2
        if binom_sf(mid, n, p) <= alpha:
            hi = mid
        else:
            lo = mid + 1
    return lo


def power_normal(p0: float, p1: float, alpha: float, power: float) -> int:
    # One-sided normal approximation for a single proportion.
    from statistics import NormalDist

    nd = NormalDist()
    za = nd.inv_cdf(1 - alpha)
    zb = nd.inv_cdf(power)
    num = za * math.sqrt(p0 * (1 - p0)) + zb * math.sqrt(p1 * (1 - p1))
    return math.ceil((num / (p1 - p0)) ** 2)


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for [[a,b],[c,d]] by summing tables no more likely."""
    n = a + b + c + d
    r1, r2 = a + b, c + d
    c1, c2 = a + c, b + d
    if n == 0:
        return 1.0

    def lp(x: int) -> float:
        return log_choose(c1, x) + log_choose(c2, r1 - x) - log_choose(n, r1)

    observed = lp(a)
    lo = max(0, r1 - c2)
    hi = min(r1, c1)
    total = 0.0
    for x in range(lo, hi + 1):
        lx = lp(x)
        if lx <= observed + 1e-12:
            total += math.exp(lx)
    return min(1.0, total)


def holm(pvalues: Sequence[float | None]) -> list[float | None]:
    """Holm step-down over the declared family.

    Undefined p-values remain None but still consume family size, which is the
    conservative choice when a planned test cannot be computed.
    """
    indexed = [(i, p) for i, p in enumerate(pvalues) if p is not None]
    indexed.sort(key=lambda t: t[1])
    out: list[float | None] = [None] * len(pvalues)
    running = 0.0
    m = len(pvalues)
    for rank, (i, p) in enumerate(indexed):
        running = max(running, min(1.0, (m - rank) * p))
        out[i] = running
    return out


def percentile(xs: Sequence[float], q: float) -> float:
    if not xs:
        raise ValueError("percentile requires values")
    s = sorted(xs)
    pos = (len(s) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return s[lo]
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def cluster_bootstrap_mean_diff(
    dates: Sequence[str],
    diffs: Sequence[float],
    replicates: int,
    seed: int,
) -> dict:
    """Paired bootstrap of mean candidate-minus-baseline loss, clustered by date."""
    if len(dates) != len(diffs) or not diffs:
        raise ValueError("aligned nonempty inputs required")
    groups: dict[str, list[float]] = defaultdict(list)
    for date, d in zip(dates, diffs):
        groups[date].append(d)
    keys = sorted(groups)
    rng = random.Random(seed)
    observed = mean(diffs)
    boots: list[float] = []
    for _ in range(replicates):
        total = 0.0
        n = 0
        for _ in range(len(keys)):
            g = groups[rng.choice(keys)]
            total += sum(g)
            n += len(g)
        boots.append(total / n)
    # Bootstrap-null p: recenter bootstrap distribution at zero and compare observed.
    centered = [b - observed for b in boots]
    ge = sum(1 for b in centered if b >= observed)
    le = sum(1 for b in centered if b <= observed)
    p = min(1.0, 2.0 * min((ge + 1) / (replicates + 1), (le + 1) / (replicates + 1)))
    return {
        "mean_diff": observed,
        "ci_lo": percentile(boots, 0.025),
        "ci_hi": percentile(boots, 0.975),
        "p_bootstrap": p,
        "clusters": len(keys),
        "n": len(diffs),
    }


def permutation_p_pearson(
    xs: Sequence[float], ys: Sequence[float], replicates: int, seed: int
) -> float | None:
    observed = pearson(xs, ys)
    if observed is None:
        return None
    rng = random.Random(seed)
    ys_list = list(ys)
    count = 0
    target = abs(observed)
    for _ in range(replicates):
        rng.shuffle(ys_list)
        r = pearson(xs, ys_list)
        if r is not None and abs(r) >= target - 1e-12:
            count += 1
    return (count + 1) / (replicates + 1)


def brier(p: float, y: int) -> float:
    return (p - y) ** 2


def log_loss(p: float, y: int) -> float:
    eps = 1e-12
    p = min(1 - eps, max(eps, p))
    return -(y * math.log(p) + (1 - y) * math.log1p(-p))


def mae(pred: Sequence[float], actual: Sequence[float]) -> float:
    return mean([abs(p - a) for p, a in zip(pred, actual)])


def rmse(pred: Sequence[float], actual: Sequence[float]) -> float:
    return math.sqrt(mean([(p - a) ** 2 for p, a in zip(pred, actual)]))


def phi_coefficient(a: int, b: int, c: int, d: int) -> float | None:
    denom = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
    if denom == 0:
        return None
    return (a * d - b * c) / denom


def half_point_line(x: float) -> float:
    """Nearest half-integer line, always ending in .5 (ties round upward)."""
    return math.floor(x) + 0.5


def logistic(x: float, scale: float) -> float:
    return 1.0 / (1.0 + math.exp(-x / scale))

"""Dependency-free statistics primitives for the Own5 price-snapshot desk.

Everything is implemented against the Python standard library only so the
desk rebuilds deterministically in CI.  Every routine is exercised against a
closed-form or brute-force value in tests/test_desk.py.

Nothing here estimates a gambling result: these are the same primitives any
forecast-grader needs (a normal CDF for turning a margin distribution into a
moneyline, a binomial tail for asking whether a hit rate is distinguishable
from noise, Pearson/Fisher for correlations with a published n).
"""

from __future__ import annotations

import math
from typing import Sequence, Tuple

SQRT2 = math.sqrt(2.0)


# --------------------------------------------------------------------------
# Normal distribution
# --------------------------------------------------------------------------
def norm_cdf(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    """Standard normal CDF via the error function."""
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    z = (x - mu) / (sigma * SQRT2)
    return 0.5 * (1.0 + math.erf(z))


def norm_pdf(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    z = (x - mu) / sigma
    return math.exp(-0.5 * z * z) / (sigma * math.sqrt(2.0 * math.pi))


def _acklam_ppf(p: float) -> float:
    """Inverse normal CDF (Acklam's rational approximation, |err| < 1.15e-9)."""
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0, 1)")
    a = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
    b = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01)
    c = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00)
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


def norm_ppf(p: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    return mu + sigma * _acklam_ppf(p)


# --------------------------------------------------------------------------
# Student t (regularized incomplete beta)
# --------------------------------------------------------------------------
def _betacf(a: float, b: float, x: float) -> float:
    MAXIT, EPS, FPMIN = 300, 3.0e-16, 1.0e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < FPMIN:
        d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN:
            d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN:
            c = FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < EPS:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta + b * math.log1p(-x) + a * math.log(x)) * _betacf(b, a, 1.0 - x) / b


def t_sf(t: float, df: float) -> float:
    """Upper-tail P(T > t) for Student t with df degrees of freedom."""
    if df <= 0:
        raise ValueError("df must be positive")
    x = df / (df + t * t)
    p = 0.5 * betainc(df / 2.0, 0.5, x)
    return p if t > 0 else 1.0 - p


def t_two_sided_p(t: float, df: float) -> float:
    """Two-sided p-value for a t statistic."""
    return 2.0 * t_sf(abs(t), df)


# --------------------------------------------------------------------------
# Binomial
# --------------------------------------------------------------------------
def binom_pmf(k: int, n: int, p: float) -> float:
    return math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                    + k * math.log(p) + (n - k) * math.log1p(-p))


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p)."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(binom_pmf(i, n, p) for i in range(k, n + 1))


def binom_two_sided_p(k: int, n: int, p: float) -> float:
    """Exact two-sided binomial p-value (method of small p-values)."""
    if n == 0:
        return 1.0
    observed = binom_pmf(k, n, p)
    total = 0.0
    for i in range(n + 1):
        pi = binom_pmf(i, n, p)
        if pi <= observed * (1 + 1e-12):
            total += pi
    return min(1.0, total)


def wilson_interval(k: int, n: int, z: float = 1.959963985) -> Tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    phat = k / n
    denom = 1 + z * z / n
    centre = (phat + z * z / (2 * n)) / denom
    half = z * math.sqrt(phat * (1 - phat) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


# --------------------------------------------------------------------------
# Correlation
# --------------------------------------------------------------------------
def pearson(xs: Sequence[float], ys: Sequence[float]) -> Tuple[float, float, int]:
    """Pearson r, two-sided p (t with n-2 df) and n.  Returns (nan, nan, n) if
    either series has zero variance or fewer than 3 paired points."""
    n = len(xs)
    if n != len(ys) or n < 3:
        return (float("nan"), float("nan"), n)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return (float("nan"), float("nan"), n)
    r = sxy / math.sqrt(sxx * syy)
    r = max(-1.0, min(1.0, r))
    if abs(r) >= 1.0:
        return (r, 0.0, n)
    t = r * math.sqrt((n - 2) / (1 - r * r))
    return (r, t_two_sided_p(t, n - 2), n)


def fisher_ci(r: float, n: int, z: float = 1.959963985) -> Tuple[float, float]:
    """Fisher z confidence interval for a Pearson correlation."""
    if n < 4 or abs(r) >= 1.0 or math.isnan(r):
        return (float("nan"), float("nan"))
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo = math.tanh(zr - z * se)
    hi = math.tanh(zr + z * se)
    return (lo, hi)


def fisher_z(r: float) -> float:
    return 0.5 * math.log((1 + r) / (1 - r)) if abs(r) < 1 else float("nan")


# --------------------------------------------------------------------------
# American odds
# --------------------------------------------------------------------------
def american_to_decimal(a: float) -> float:
    if a == 0:
        raise ValueError("american odds cannot be zero")
    return 1 + a / 100.0 if a > 0 else 1 + 100.0 / abs(a)


def decimal_to_american(d: float) -> float:
    if d <= 1.0:
        raise ValueError("decimal odds must exceed 1")
    return (d - 1) * 100 if d >= 2 else -100 / (d - 1)


def implied_prob(a: float) -> float:
    """Raw implied probability of one American price (includes the vig)."""
    return 1.0 / american_to_decimal(a)


def devig_two_way(a: float, b: float) -> Tuple[float, float]:
    """Remove the overround from a two-sided American price pair."""
    pa, pb = implied_prob(a), implied_prob(b)
    s = pa + pb
    if s <= 0:
        return (float("nan"), float("nan"))
    return (pa / s, pb / s)


def breakeven_prob(a: float) -> float:
    """Win rate needed to break even at the given American price."""
    return implied_prob(a)


# --------------------------------------------------------------------------
# Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014)
# --------------------------------------------------------------------------
def deflated_sharpe(sharpe: float, n_trials: int, n_obs: int,
                    skew: float = 0.0, kurtosis: float = 3.0) -> float:
    """Probabilistic Sharpe ratio: P(observed SR exceeds the expected maximum
    SR of `n_trials` unskilled strategies).  Returns a value in [0, 1]; the
    desk requires >= 0.95 to treat a result as more than a search artifact."""
    if n_obs < 3 or n_trials < 1:
        return float("nan")
    euler = 0.5772156649015329
    sr0 = math.sqrt(max(n_obs - 1.0, 1.0)) * (
        (1 - euler) * _z_inv(1 - 1.0 / n_trials) + euler * _z_inv(1 - 1.0 / (n_trials * math.e))
    ) if n_trials > 1 else 0.0
    se = math.sqrt(max(
        (1 - skew * sharpe + (kurtosis - 1) / 4.0 * sharpe * sharpe) / max(n_obs - 1, 1), 1e-12))
    return norm_cdf((sharpe - sr0) / se)


def _z_inv(q: float) -> float:
    return _acklam_ppf(q)


def sharpe_ratio(returns: Sequence[float]) -> float:
    n = len(returns)
    if n < 2:
        return float("nan")
    mu = sum(returns) / n
    var = sum((r - mu) ** 2 for r in returns) / (n - 1)
    if var <= 0:
        return float("nan")
    return mu / math.sqrt(var)


# --------------------------------------------------------------------------
# Linear algebra -- ridge regression by normal equations (Gaussian elimination)
# --------------------------------------------------------------------------
def ridge_solve(X: Sequence[Sequence[float]], y: Sequence[float], lam: float) -> list:
    """Solve (X'X + lam I) b = X'y.  X is n x p; an intercept column is NOT
    added automatically -- callers append it if they want one."""
    n = len(X)
    if n == 0:
        raise ValueError("no rows")
    p = len(X[0])
    A = [[0.0] * p for _ in range(p)]
    b = [0.0] * p
    for i in range(n):
        xi = X[i]
        yi = y[i]
        for a in range(p):
            b[a] += xi[a] * yi
            for c in range(p):
                A[a][c] += xi[a] * xi[c]
    for a in range(p):
        A[a][a] += lam
    return _gauss(A, b)


def solve_normal(A: Sequence[Sequence[float]], b: Sequence[float]) -> list:
    """Solve a pre-built normal-equation system A x = b by Gaussian elimination
    with partial pivoting.  Used by the incremental ridge models, which
    accumulate X'X and X'y row by row and only solve once per fold."""
    return _gauss([list(row) for row in A], list(b))


def _gauss(A: list, b: list) -> list:
    p = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(p):
        piv = max(range(col, p), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            continue
        M[col], M[piv] = M[piv], M[col]
        pivval = M[col][col]
        for r in range(p):
            if r == col:
                continue
            factor = M[r][col] / pivval
            if factor == 0:
                continue
            for c in range(col, p + 1):
                M[r][c] -= factor * M[col][c]
    out = []
    for r in range(p):
        out.append(M[r][p] / M[r][r] if abs(M[r][r]) > 1e-12 else 0.0)
    return out


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def stdev(xs: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def log_loss(probs: Sequence[float], outcomes: Sequence[int]) -> float:
    """Mean log-loss with probabilities clipped away from 0 and 1."""
    if not probs:
        return float("nan")
    total = 0.0
    for p, o in zip(probs, outcomes):
        p = min(max(p, 1e-9), 1 - 1e-9)
        total += -(math.log(p) if o == 1 else math.log(1 - p))
    return total / len(probs)


def brier(probs: Sequence[float], outcomes: Sequence[int]) -> float:
    if not probs:
        return float("nan")
    return sum((p - o) ** 2 for p, o in zip(probs, outcomes)) / len(probs)

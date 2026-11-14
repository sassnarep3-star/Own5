"""Statistics used by the desk, implemented with the standard library only.

The sandbox and the CI runner both have a bare Python 3.11 with no numpy or
scipy, so every function here is implemented from its definition and each one
is checked against a closed-form value in ``tests/test_statslib.py``.

Conventions
-----------
* American odds: ``+124`` means a 100 stake returns 124; ``-118`` means 118
  staked returns 100.
* Probabilities are returned as fractions (0-1), never percentages.
* Every interval returned is a 95% interval unless the name says otherwise.
"""
from __future__ import annotations

import math

SQRT2 = math.sqrt(2.0)


# --------------------------------------------------------------------------
# pricing
# --------------------------------------------------------------------------
def american_to_prob(odds):
    """Implied probability from American odds, vig included. None in -> None out."""
    if odds is None:
        return None
    odds = float(odds)
    if odds == 0:
        return None
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return (-odds) / ((-odds) + 100.0)


def prob_to_american(p):
    """Fair American price for a probability p (no vig). None for p<=0 or p>=1."""
    if p is None or p <= 0.0 or p >= 1.0:
        return None
    if p >= 0.5:
        return round(-100.0 * p / (1.0 - p))
    return round(100.0 * (1.0 - p) / p)


def devig_two_way(p_a, p_b):
    """Normalise two implied probabilities to a no-vig pair. Returns (pa, pb)."""
    if p_a is None or p_b is None:
        return (None, None)
    s = p_a + p_b
    if s <= 0:
        return (None, None)
    return (p_a / s, p_b / s)


def hold_pct(p_a, p_b):
    """Book percentage (overround) of a two-way market, in percent."""
    if p_a is None or p_b is None:
        return None
    return (p_a + p_b - 1.0) * 100.0


def breakeven_prob(odds):
    """Win probability needed to break even at a given American price."""
    return american_to_prob(odds)


# --------------------------------------------------------------------------
# normal / binomial
# --------------------------------------------------------------------------
def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / SQRT2))


def norm_pdf(z):
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def norm_ppf(p):
    """Acklam's inverse normal CDF; |error| < 1.15e-9 over (0,1)."""
    if p <= 0.0 or p >= 1.0:
        raise ValueError("norm_ppf needs 0 < p < 1")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


def _betacf(a, b, x, itmax=300, eps=3e-16, fpmin=1e-300):
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def betainc(a, b, x):
    """Regularised incomplete beta I_x(a, b) (Numerical Recipes continued fraction)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta + b * math.log(1.0 - x) + a * math.log(x)) * _betacf(b, a, 1.0 - x) / b


def t_sf2(t, df):
    """Two-sided Student t p-value."""
    if df <= 0:
        return None
    return betainc(0.5 * df, 0.5, df / (df + t * t))


def binom_pmf(n, k, p):
    if k < 0 or k > n:
        return 0.0
    return math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                    + k * math.log(p) + (n - k) * math.log1p(-p)) if 0 < p < 1 else (
        1.0 if (p in (0.0, 1.0) and (k == n if p == 1.0 else k == 0)) else 0.0)


def binom_two_sided(n, k, p0):
    """Exact two-sided binomial test: sum of P(X=x) for every x with P <= P(k)."""
    if n <= 0:
        return None
    pk = binom_pmf(n, k, p0)
    tot = 0.0
    for x in range(n + 1):
        px = binom_pmf(n, x, p0)
        if px <= pk * (1 + 1e-9):
            tot += px
    return min(1.0, tot)


def binom_greater(n, k, p0):
    """One-sided P(X >= k)."""
    if n <= 0:
        return None
    return sum(binom_pmf(n, x, p0) for x in range(k, n + 1))


def wilson_ci(k, n, z=1.959963984540054):
    """Wilson score interval for a binomial proportion."""
    if n <= 0:
        return (None, None)
    ph = k / n
    d = 1 + z * z / n
    c = ph + z * z / (2 * n)
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def binom_power(n, p0, p1, alpha=0.05):
    """Power of a one-sided exact binomial test rejecting 'rate <= p0' when true rate is p1."""
    lo, hi = 0, n
    crit = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if binom_greater(n, mid, p0) <= alpha:
            crit = mid
            lo = mid + 1
        else:
            hi = mid - 1
    if crit is None:
        return 0.0
    return sum(binom_pmf(n, x, p1) for x in range(crit, n + 1))


# --------------------------------------------------------------------------
# correlation
# --------------------------------------------------------------------------
def pearson(xs, ys):
    n = len(xs)
    if n != len(ys) or n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for t in range(i, j + 1):
                rk[order[t]] = avg
            i = j + 1
        return rk
    return pearson(ranks(xs), ranks(ys))


def fisher_z_ci(r, n, z=1.959963984540054):
    """Fisher-z 95% CI for a Pearson r, plus a two-sided p for r != 0."""
    if r is None or n < 4:
        return (None, None, None)
    rr = max(-0.9999999999, min(0.9999999999, r))
    zh = 0.5 * math.log((1 + rr) / (1 - rr))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = math.tanh(zh - z * se), math.tanh(zh + z * se)
    p = 2.0 * (1.0 - norm_cdf(abs(zh / se)))
    return (lo, hi, p)


def phi_table(a, b, c, d):
    """2x2 association: rows=x, cols=y. Returns (phi, chi2, p, n)."""
    n = a + b + c + d
    if n <= 0:
        return (None, None, None, n)
    r1, r2 = a + b, c + d
    c1, c2 = a + c, b + d
    denom = math.sqrt(r1 * r2 * c1 * c2) if min(r1, r2, c1, c2) > 0 else 0
    phi = ((a * d - b * c) / denom) if denom > 0 else None
    chi2 = 0.0
    for obs, exp in ((a, r1 * c1 / n), (b, r1 * c2 / n), (c, r2 * c1 / n), (d, r2 * c2 / n)):
        if exp > 0:
            chi2 += (obs - exp) ** 2 / exp
    p = 1.0 - norm_cdf(math.sqrt(max(chi2, 0.0)))  # chi2 with df=1 == z^2
    return (phi, chi2, p, n)


def mcnemar_exact(n01, n10):
    """Exact McNemar test on discordant pairs; returns two-sided p."""
    n = n01 + n10
    if n == 0:
        return 1.0
    return binom_two_sided(n, min(n01, n10), 0.5)


# --------------------------------------------------------------------------
# linear algebra (ridge)
# --------------------------------------------------------------------------
def solve(A, b):
    """Gaussian elimination with partial pivoting. A is a list of rows."""
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            return None
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        for r in range(n):
            if r == col:
                continue
            f = M[r][col] / pv
            if f:
                for c in range(col, n + 1):
                    M[r][c] -= f * M[col][c]
    return [M[i][n] / M[i][i] for i in range(n)]


def ridge_solve(X, y, lam, protect=None):
    """Ridge least squares: (X'X + lam*R) beta = X'y.

    ``protect`` is a set of column indices left unpenalised (e.g. the intercept).
    """
    p = len(X[0])
    XtX = [[sum(X[i][a] * X[i][b] for i in range(len(X))) for b in range(p)] for a in range(p)]
    Xty = [sum(X[i][a] * y[i] for i in range(len(X))) for a in range(p)]
    protect = protect or set()
    for a in range(p):
        if a not in protect:
            XtX[a][a] += lam
    return solve(XtX, Xty)


# --------------------------------------------------------------------------
# deflated Sharpe ratio (Bailey, Borwein, Lopez de Prado, Zhu 2014)
# --------------------------------------------------------------------------
def skewness(xs):
    n = len(xs)
    if n < 3:
        return 0.0
    m = sum(xs) / n
    s = math.sqrt(sum((x - m) ** 2 for x in xs) / n)
    if s == 0:
        return 0.0
    return sum(((x - m) / s) ** 3 for x in xs) / n


def kurtosis_excess(xs):
    n = len(xs)
    if n < 4:
        return 0.0
    m = sum(xs) / n
    s = math.sqrt(sum((x - m) ** 2 for x in xs) / n)
    if s == 0:
        return 0.0
    return sum(((x - m) / s) ** 4 for x in xs) / n - 3.0


def expected_max_sharpe(variance_of_trials, n_trials, n_obs):
    """SR* threshold a trial must beat, given the spread of trial Sharpe ratios."""
    if n_trials < 2 or n_obs < 3 or variance_of_trials <= 0:
        return 0.0
    sd = math.sqrt(variance_of_trials)
    z1 = norm_ppf(1.0 - 1.0 / n_trials)
    z2 = norm_ppf(1.0 - 1.0 / (n_trials * math.e))
    return sd * ((1 - 1 / n_trials) * z1 + (1 / n_trials) * z2) - 1.645 / math.sqrt(n_obs)


def deflated_sharpe(sr_per_obs, n_obs, n_trials, var_trials, skew=0.0, kurt=3.0):
    """Probability that the observed SR exceeds the best of `n_trials` under the null.

    Inputs use per-observation (not annualised) Sharpe units.
    """
    if n_obs < 5:
        return None
    sr0 = expected_max_sharpe(var_trials, n_trials, n_obs)
    denom = math.sqrt(max(1e-12, 1 - skew * (sr_per_obs - sr0)
                          + (kurt - 1) / 4.0 * (sr_per_obs - sr0) ** 2))
    z = (sr_per_obs - sr0) * math.sqrt(n_obs - 1) / denom
    return norm_cdf(z)


# --------------------------------------------------------------------------
# money management
# --------------------------------------------------------------------------
def units_pnl(results, prices):
    """Unit P&L series: 1 unit staked; a win pays the decimal profit of the price."""
    out = []
    for res, price in zip(results, prices):
        if res == 'push':
            out.append(0.0)
            continue
        p = american_to_prob(price)
        if p is None:
            out.append(None)
            continue
        win_pay = (100.0 / (-price)) if price < 0 else (price / 100.0)
        out.append(win_pay if res == 'win' else -1.0)
    return [v for v in out if v is not None]


def max_drawdown(pnl):
    peak, mdd = 0.0, 0.0
    cum = 0.0
    for x in pnl:
        cum += x
        peak = max(peak, cum)
        mdd = min(mdd, cum - peak)
    return mdd


def longest_losing_streak(pnl):
    best = cur = 0
    for x in pnl:
        cur = cur + 1 if x < 0 else 0
        best = max(best, cur)
    return best


def kelly_fraction(p_win, b):
    """Full Kelly fraction for a binary bet paying b (decimal profit) at win prob p."""
    if p_win is None or b is None or b <= 0:
        return None
    f = (p_win * (b + 1.0) - 1.0) / b
    return max(0.0, f)


# --------------------------------------------------------------------------
# formatting helpers (stable rendering)
# --------------------------------------------------------------------------
def median(xs):
    """Median of a non-empty sequence; None when empty (so blanks stay blanks)."""
    xs = sorted(xs)
    if not xs:
        return None
    n = len(xs)
    return float(xs[n // 2]) if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0


def num(x, nd=2):
    if x is None:
        return ""
    return f"{float(x):.{nd}f}"


def signed(x, nd=2):
    if x is None:
        return ""
    v = float(x)
    return f"{v:+.{nd}f}"


def pct(x, nd=1):
    if x is None:
        return ""
    return f"{100.0 * float(x):.{nd}f}%"


def pfmt(p):
    if p is None:
        return ""
    if p < 1e-4:
        return "<0.0001"
    return f"{p:.4f}"

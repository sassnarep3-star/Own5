"""Pure-Python statistics helpers (no third-party dependencies).

Every function is exact/closed-form where a closed form exists. Where a numeric
approximation is required (normal CDF/quantile) the algorithm used is named in
the docstring. Nothing here invents data.
"""
from __future__ import annotations
import math
from functools import lru_cache


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def variance(xs, ddof=1):
    n = len(xs)
    if n - ddof <= 0:
        return 0.0
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / (n - ddof)


def stdev(xs, ddof=1):
    return math.sqrt(variance(xs, ddof))


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = mean(xs), mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_z(r, n):
    """Fisher z-transform and its 95% CI for a Pearson r."""
    if r is None or n < 4:
        return None
    if abs(r) >= 1.0:
        return None
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    return (z, z - 1.959963985 * se, z + 1.959963985 * se)


def pearson_p(r, n):
    """Two-sided p-value for a Pearson r via the t-distribution.

    Uses the standard t = r*sqrt((n-2)/(1-r^2)) statistic and evaluates
    Student's t survival function with the regularized incomplete beta
    function (continued-fraction expansion, Lentz's method).
    """
    if r is None or n < 3 or abs(r) >= 1.0:
        return None
    df = n - 2
    t = r * math.sqrt(df / (1 - r * r))
    return 2.0 * _t_sf(abs(t), df)


def _betacf(a, b, x):
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
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            break
    return h


def betai(a, b, x):
    """Regularized incomplete beta function I_x(a,b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta + b * math.log(1.0 - x) + a * math.log(x)) * _betacf(b, a, 1.0 - x) / b


def _t_sf(t, df):
    """P(T > t) for Student's t with df degrees of freedom."""
    if df <= 0:
        return float("nan")
    x = df / (df + t * t)
    return 0.5 * betai(df / 2.0, 0.5, x)


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def norm_ppf(p):
    """Inverse standard normal CDF.

    Acklam's rational approximation (relative error < 1.15e-9) followed by one
    Halley refinement step.
    """
    if not 0.0 < p < 1.0:
        raise ValueError("p must be in (0,1)")
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
        x = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    elif p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        x = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    else:
        q = p - 0.5
        r = q * q
        x = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    e = norm_cdf(x) - p
    u = e * math.sqrt(2 * math.pi) * math.exp(x * x / 2)
    return x - u / (1 + x * u / 2)


def binom_pmf(k, n, p):
    if k < 0 or k > n:
        return 0.0
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def binom_sf(k, n, p):
    """P(X >= k) exactly, by summing the pmf."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return sum(binom_pmf(i, n, p) for i in range(k, n + 1))


def binom_two_sided_p(k, n, p):
    """Exact two-sided binomial p-value (method of small p-values)."""
    if n == 0:
        return None
    obs = binom_pmf(k, n, p)
    if obs <= 0.0:
        return 0.0
    return sum(binom_pmf(i, n, p) for i in range(n + 1)
               if binom_pmf(i, n, p) <= obs * (1 + 1e-12))


def wilson_ci(k, n, z=1.959963985):
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (None, None)
    ph = k / n
    den = 1 + z * z / n
    centre = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def skewness(xs):
    """Sample skewness g1 = m3 / m2^{3/2} using population moments.

    m_k = (1/n) * sum((x - mean)^k). This is the definition scipy.stats.skew
    uses with bias=True and the one the deflated Sharpe ratio expects.
    """
    n = len(xs)
    if n < 3:
        return None
    m = mean(xs)
    m2 = sum((x - m) ** 2 for x in xs) / n
    if m2 <= 0:
        return None
    m3 = sum((x - m) ** 3 for x in xs) / n
    return m3 / (m2 ** 1.5)


def kurtosis(xs):
    """Excess kurtosis g2 = m4 / m2^2 - 3 using population moments.

    Fisher definition; a normal distribution gives 0.
    """
    n = len(xs)
    if n < 4:
        return None
    m = mean(xs)
    m2 = sum((x - m) ** 2 for x in xs) / n
    if m2 <= 0:
        return None
    m4 = sum((x - m) ** 4 for x in xs) / n
    return m4 / (m2 * m2) - 3.0


def deflated_sharpe(sr, n, skew, kurt, n_trials, gamma_e=0.5772156649):
    """Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014).

    sr        : observed annualised-or-per-bet Sharpe ratio (same frequency as n)
    n         : number of observations
    skew, kurt: realised skew and *excess* kurtosis of the returns
    n_trials  : number of strategies tried (for the multiple-testing haircut)
    Returns   : P(true Sharpe > 0) after deflating for trials, i.e. the DSR.
    """
    if n < 2 or n_trials < 1 or skew is None or kurt is None:
        return None
    var_sr = (1 - skew * sr + (kurt - 1.0) / 4.0 * sr * sr) / (n - 1)
    if var_sr <= 0:
        var_sr = 1.0 / (n - 1)
    se = math.sqrt(var_sr)
    q1 = norm_ppf(1.0 - 1.0 / n_trials)
    q2 = norm_ppf(1.0 - 1.0 / (n_trials * math.e))
    sr0 = se * ((1 - gamma_e) * q1 + gamma_e * q2)
    return norm_cdf((sr - sr0) / se)


def holm_bonferroni(pvals, alpha=0.05):
    """Holm-Bonferroni step-down. Returns list of (index, p, adj_p, reject)."""
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    out = [None] * len(pvals)
    m = len(pvals)
    still = True
    max_adj = 0.0
    for rank, idx in enumerate(order):
        p = pvals[idx]
        adj = min(1.0, (m - rank) * p)
        max_adj = max(max_adj, adj)
        adj = max_adj
        if still and adj <= alpha:
            rej = True
        else:
            still = False
            rej = False
        out[idx] = (idx, p, adj, rej)
    return out


def solve_linear(A, b):
    """Gaussian elimination with partial pivoting. A is n x n, b length n."""
    n = len(A)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            raise ValueError("singular matrix")
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        for r in range(col + 1, n):
            f = M[r][col] / pv
            if f == 0:
                continue
            for c in range(col, n + 1):
                M[r][c] -= f * M[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = M[r][n] - sum(M[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / M[r][r]
    return x


def ridge_solve(X, y, lam):
    """Ridge regression: (X'X + lam*I) w = X'y. lam shrinks team ratings to 0."""
    k = len(X[0])
    XtX = [[0.0] * k for _ in range(k)]
    Xty = [0.0] * k
    for row, yi in zip(X, y):
        for i in range(k):
            Xty[i] += row[i] * yi
            for j in range(k):
                XtX[i][j] += row[i] * row[j]
    for i in range(k):
        XtX[i][i] += lam
    return solve_linear(XtX, Xty)


def required_n(p_alt, p_null, alpha=0.05, power=0.80):
    """Bets needed to detect p_alt vs p_null at -110 (approximately).

    Normal approximation, two-sided:
      n = ((z_{1-a/2}*sqrt(p0(1-p0)) + z_{power}*sqrt(p1(1-p1)))/(p1-p0))^2
    """
    if p_alt == p_null:
        return None
    z_a = norm_ppf(1 - alpha / 2)
    z_b = norm_ppf(power)
    num = z_a * math.sqrt(p_null * (1 - p_null)) + z_b * math.sqrt(p_alt * (1 - p_alt))
    return (num / (p_alt - p_null)) ** 2

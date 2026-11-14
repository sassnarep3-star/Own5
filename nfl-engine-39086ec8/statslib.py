"""Dependency-free statistics used by the Own5 NFL engine.

No numpy/scipy is available in the build environment, so every routine here is
implemented from its closed form and checked against a known value in
tests/test_engine.py. Nothing in this module reads data or knows about football.

Conventions
-----------
* American odds are integers (e.g. -110, +145). Decimal odds are floats.
* All p-values are two-sided unless the function name says otherwise.
* "n" always means the number of independent observations that entered a
  calculation. Callers must pass it explicitly; nothing is inferred.
"""

import math

# ---------------------------------------------------------------- odds


def american_to_decimal(american):
    """Convert American odds to decimal odds. Raises on 0 or |odds| < 100."""
    if american == 0:
        raise ValueError("American odds cannot be 0")
    if abs(american) < 100:
        raise ValueError("American odds must be >= +100 or <= -100")
    if american > 0:
        return 1.0 + american / 100.0
    return 1.0 + 100.0 / abs(american)


def decimal_to_american(dec):
    """Convert decimal odds (>= 1.0) to American odds, rounded to an integer."""
    if dec <= 1.0:
        raise ValueError("decimal odds must exceed 1.0")
    if dec >= 2.0:
        return int(round((dec - 1.0) * 100.0))
    return -int(round(100.0 / (dec - 1.0)))


def implied_probability(american):
    """Raw (vig-inclusive) implied probability of American odds."""
    return 1.0 / american_to_decimal(american)


def no_vig_two_way(american_a, american_b):
    """Multiplicative de-vig of a two-way market with no push.

    Returns (p_a, p_b) summing to 1. This is a *convention*, not ground truth:
    it assumes the operator's margin is proportional. Use it to compare our fair
    probability with the market, never as an estimate of the true probability.
    """
    pa = implied_probability(american_a)
    pb = implied_probability(american_b)
    total = pa + pb
    if total <= 0:
        raise ValueError("sum of implied probabilities must be positive")
    return pa / total, pb / total


def ev_per_unit(p_win, p_push, decimal_odds):
    """Expected profit per 1 unit staked with possible push (stake returned)."""
    if not (0.0 <= p_win <= 1.0 and 0.0 <= p_push <= 1.0):
        raise ValueError("probabilities must lie in [0, 1]")
    if p_win + p_push > 1.0 + 1e-12:
        raise ValueError("p_win + p_push cannot exceed 1")
    return p_win * (decimal_odds - 1.0) - (1.0 - p_win - p_push)


def breakeven_win_rate(decimal_odds, p_push=0.0):
    """Win rate required for EV = 0, allowing pushes.

    Solves p*(d-1) - (1-p-pp) = 0  ->  p = (1-pp)/d.
    At -110 (d = 1.909..., pp = 0) this is 0.5238..., the familiar 52.38%.
    """
    return (1.0 - p_push) / decimal_odds


# ------------------------------------------------------- distributions


def _betacf(a, b, x, max_iter=300, eps=3e-14):
    """Continued fraction for the regularized incomplete beta (Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betainc(a, b, x):
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_two_sided_p(t, df):
    """Two-sided p-value for Student t with df degrees of freedom."""
    if df <= 0:
        raise ValueError("df must be positive")
    x = df / (df + t * t)
    return betainc(df / 2.0, 0.5, x)


def norm_sf(z):
    """Upper tail of the standard normal: P(Z > z)."""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def two_sided_z_p(z):
    return 2.0 * norm_sf(abs(z))


# ------------------------------------------------------- correlations


def pearson(xs, ys):
    """Pearson r. Returns (r, n). Raises on mismatched lengths or zero variance."""
    n = len(xs)
    if n != len(ys):
        raise ValueError("xs and ys must have equal length")
    if n < 3:
        raise ValueError("n must be >= 3")
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx == 0 or syy == 0:
        raise ValueError("zero variance; r is undefined")
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy), n


def fisher_ci(r, n, z_crit=1.959963984540054):
    """Fisher z transformation 95% CI for Pearson r. Undefined for n < 4."""
    if n < 4:
        return None, None
    r = max(min(r, 1.0 - 1e-12), -1.0 + 1e-12)
    z = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = math.tanh(z - z_crit * se), math.tanh(z + z_crit * se)
    return lo, hi


def pearson_p(r, n):
    """Two-sided p-value for H0: rho = 0 (t distribution, df = n-2)."""
    if n < 3:
        return None
    if abs(r) >= 1.0:
        return 0.0
    t = r * math.sqrt((n - 2) / (1.0 - r * r))
    return t_two_sided_p(t, n - 2)


def stouffer_z(r_list, n_list):
    """Stouffer's weighted combination of independent two-sided p-values.

    Used to test one hypothesis across several seasons without pretending the
    observations are independent within a season. Weights are sqrt(n).
    Returns (z, two_sided_p).
    """
    if len(r_list) != len(n_list) or not r_list:
        raise ValueError("need equal, non-empty lists")
    num = 0.0
    den = 0.0
    for r, n in zip(r_list, n_list):
        p = pearson_p(r, n)
        p = min(max(p, 1e-300), 1 - 1e-16)
        num += math.sqrt(n) * z_from_p(p)
        den += n
    z = num / math.sqrt(den)
    return z, two_sided_z_p(z)


def z_from_p(p):
    """Inverse of the upper tail: returns z with P(Z > z) = p.

    Starts from Acklam's approximation and then bisects on [0, 10] against
    norm_sf, which is exactly monotone here. Bisection is used rather than Newton
    because erfc loses relative precision far into the tail, and a silently wrong
    z there would quietly distort every p-value upstream.
    """
    if not (0.0 < p < 1.0):
        raise ValueError("p must lie strictly between 0 and 1")
    if p == 0.5:
        return 0.0
    lo, hi = 0.0, 10.0          # P(Z>10) < 1e-23, so the root is inside
    z = min(max(_acklam(1.0 - p), lo), hi)
    if abs(norm_sf(z) - p) < 1e-14:
        return z
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if norm_sf(mid) > p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-13:
            break
    return (lo + hi) / 2.0


def _acklam(p):
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow = 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


# ------------------------------------------------------------- binomial


def binom_pmf(k, n, p):
    if k < 0 or k > n:
        return 0.0
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def binom_two_sided_p(k, n, p):
    """Exact two-sided binomial p-value (probability-ordering method)."""
    if n <= 0:
        raise ValueError("n must be positive")
    obs = binom_pmf(k, n, p)
    total = 0.0
    for i in range(n + 1):
        pm = binom_pmf(i, n, p)
        if pm <= obs * (1 + 1e-7):
            total += pm
    return min(total, 1.0)


def wilson_interval(k, n, z=1.959963984540054):
    """Wilson score interval for a binomial proportion. Returns (low, high)."""
    if n <= 0:
        return None, None
    ph = k / n
    denom = 1.0 + z * z / n
    centre = (ph + z * z / (2 * n)) / denom
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def required_n_to_detect(p_true, p_null, alpha=0.05, power=0.80):
    """Bets needed for a one-sided test of p_true > p_null at alpha with power.

    Normal approximation with the null standard error under p_null.
    Returns an integer (rounded up), never fewer than 1.
    """
    if not (0 < p_null < 1) or not (0 < p_true < 1):
        raise ValueError("probabilities must lie in (0, 1)")
    if p_true <= p_null:
        raise ValueError("p_true must exceed p_null for a power calculation")
    z_a = z_from_p(alpha)
    z_b = z_from_p(1.0 - power)
    num = z_a * math.sqrt(p_null * (1 - p_null)) + z_b * math.sqrt(p_true * (1 - p_true))
    return max(1, int(math.ceil((num / (p_true - p_null)) ** 2)))


# --------------------------------------------- sequential testing (SPRT)


def sprt_boundaries(p0, p1, alpha=0.05, beta=0.20):
    """Wald SPRT boundaries on the cumulative log-likelihood ratio.

    Returns (lower, upper). Decide "demote to paper" at/below lower, decide
    "keep live" at/above upper, otherwise keep sampling.
    """
    if not (0 < p0 < 1 and 0 < p1 < 1) or p0 == p1:
        raise ValueError("need distinct p0, p1 in (0, 1)")
    lower = math.log(beta / (1 - alpha))
    upper = math.log((1 - beta) / alpha)
    return lower, upper


def sprt_step(p0, p1, won):
    """Log-likelihood increment of one graded bet under p1 vs p0."""
    if not (0 < p0 < 1 and 0 < p1 < 1):
        raise ValueError("probabilities must lie in (0, 1)")
    if won:
        return math.log(p1 / p0)
    return math.log((1 - p1) / (1 - p0))


# ------------------------------------------------------- staking / money


def kelly_fraction(p, decimal_odds):
    """Full Kelly stake fraction f* = (bp - q)/b with b = decimal - 1.

    Clipped at 0: a negative Kelly means "no bet", never "bet the other side".
    """
    b = decimal_odds - 1.0
    if b <= 0:
        raise ValueError("decimal odds must exceed 1.0")
    f = (b * p - (1.0 - p)) / b
    return max(0.0, f)


def realised_growth(stakes, bankroll_start):
    """Final bankroll after a list of (p_win, decimal_odds, won) unit stakes.

    `stakes` is a list of dicts with keys stake (bankroll fraction or units),
    won (bool). This is a *simulation* used to show that staking can mask a
    signal; it is not a forecast.
    """
    bank = bankroll_start
    for s in stakes:
        bank += s["stake"] * ((s["decimal_odds"] - 1.0) if s["won"] else -1.0)
        if bank <= 0:
            return 0.0
    return bank


def max_drawdown(equity):
    """Largest peak-to-trough fall of an equity curve, in the curve's units."""
    peak = equity[0] if equity else 0.0
    worst = 0.0
    for v in equity:
        peak = max(peak, v)
        worst = max(worst, peak - v)
    return worst

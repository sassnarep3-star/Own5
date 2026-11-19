"""Pure-stdlib numeric core for the 9e54d765 desk.

No numpy in this sandbox: normal equations are solved with Gaussian elimination and
distributions with the complementary error function. Everything here is deterministic.

Sign conventions (measured, not assumed):
  * ``games.csv.gz`` ``spread_line`` is stored HOME-FAVOURED POSITIVE. This is verified at
    build time by comparing mean absolute error under both conventions and the result is
    written to data/sign_convention.csv. The printer's convention used in the origination
    table is home-negative (a home favourite is printed "-7").
"""
import math

# ----------------------------------------------------------------------------- basics
SQRT2 = math.sqrt(2.0)


def norm_cdf(x):
    return 0.5 * math.erfc(-x / SQRT2)


def norm_ppf(p):
    """Inverse normal CDF (Acklam's rational approximation, |rel err| < 1.2e-9)."""
    if not (0.0 < p < 1.0):
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


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float('nan')


def sd(xs):
    xs = list(xs)
    n = len(xs)
    if n < 2:
        return float('nan')
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def quantile(xs, q):
    xs = sorted(xs)
    if not xs:
        return float('nan')
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


# ------------------------------------------------------------------- odds conversion
def american_to_prob(a):
    """Implied probability of an American price (vig included)."""
    a = float(a)
    if a == 0:
        raise ValueError("zero american price")
    return (-a) / (-a + 100.0) if a < 0 else 100.0 / (a + 100.0)


def prob_to_american(p):
    if not (0 < p < 1):
        raise ValueError("p out of range")
    dec = 1.0 / p
    if dec >= 2.0:
        return round((dec - 1) * 100.0, 1)
    return round(-100.0 / (dec - 1.0), 1)


def devig_two_way(p_a, p_b):
    """Proportional de-vig of a two-way market; returns the normalised first side."""
    s = p_a + p_b
    return p_a / s


# ------------------------------------------------------------------------- linear algebra
def solve(a, b):
    """Gaussian elimination with partial pivoting. a is NxN (list of lists), b is N."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ZeroDivisionError("singular normal equations")
        if piv != col:
            m[col], m[piv] = m[piv], m[col]
        inv = 1.0 / m[col][col]
        for j in range(col, n + 1):
            m[col][j] *= inv
        for r in range(n):
            if r == col:
                continue
            f = m[r][col]
            if f == 0.0:
                continue
            for j in range(col, n + 1):
                m[r][j] -= f * m[col][j]
    return [m[i][n] for i in range(n)]


# ------------------------------------------------------------------- the rating model
class Ratings:
    """Additive offence/defence ratings plus a home-field term, fitted by ridge.

    Model (points domain, REG games only):
        home_points = mu + off[h] - def[a] + hfa
        away_points = mu + off[a] - def[h]
    Both markets fall out of the same fit:
        expected margin (home - away) = (off[h] - off[a]) + (def[h] - def[a]) + hfa
        expected total                = 2*mu + off[h] + off[a] - def[h] - def[a] + hfa
    Priors are shrunk to the league mean, which is what a club with no games gets.
    """

    def __init__(self, teams, mu, hfa, off, deff, sigma_margin, sigma_total, n_games):
        self.teams = teams
        self.mu = mu
        self.hfa = hfa
        self.off = off            # dict club -> points per game above/below mean
        self.deff = deff          # dict club -> points allowed per game above/below mean
        self.sigma_margin = sigma_margin
        self.sigma_total = sigma_total
        self.n_games = n_games

    def expected_margin(self, home, away):
        return ((self.off[home] - self.off[away]) + (self.deff[home] - self.deff[away])
                + self.hfa)

    def expected_total(self, home, away):
        return (2 * self.mu + self.off[home] + self.off[away]
                - self.deff[home] - self.deff[away] + self.hfa)

    def p_home_win(self, home, away):
        m = self.expected_margin(home, away)
        return norm_cdf(m / self.sigma_margin)

    def p_over(self, home, away, line):
        t = self.expected_total(home, away)
        return 1.0 - norm_cdf((line - t) / self.sigma_total)


def fit_ratings(games, teams, ridge=3.0, seasons_used=5):
    """`games`: iterable of dicts with season, week, away, home, away_score, home_score.

    Recency weighting: the most recent season gets weight 1.0 and each earlier season is
    multiplied by 0.75**, capped at ``seasons_used`` seasons back from the newest game.
    """
    games = list(games)
    if not games:
        raise ValueError("no games to fit")
    newest = max(g['season'] for g in games)
    cut = newest - seasons_used + 1
    used = [g for g in games if g['season'] >= cut]
    idx = {t: i for i, t in enumerate(teams)}
    n_team = len(teams)
    # parameters: [0]=mu, [1]=hfa, then off[0..n-1], def[0..n-1]
    n_par = 2 + 2 * n_team
    ata = [[0.0] * n_par for _ in range(n_par)]
    atb = [0.0] * n_par
    for g in used:
        h, a = idx[g['home']], idx[g['away']]
        w = 0.75 ** (newest - g['season'])
        # two observations per game, each row sparse in 4 rating columns
        rows = []
        # home points: mu + off[h] - def[a] + hfa
        rows.append((0.5 * w, float(g['home_score']), [(0, 1.0), (1, 1.0),
                                                       (2 + h, 1.0), (2 + n_team + a, -1.0)]))
        # away points: mu + off[a] - def[h]
        rows.append((0.5 * w, float(g['away_score']), [(0, 1.0),
                                                       (2 + a, 1.0), (2 + n_team + h, -1.0)]))
        for ww, y, cols in rows:
            for i, vi in cols:
                atb[i] += ww * vi * y
                for j, vj in cols:
                    ata[i][j] += ww * vi * vj
    for i in range(2, n_par):
        ata[i][i] += ridge
    ata[0][0] += 1e-6
    beta = solve(ata, atb)
    mu, hfa = beta[0], beta[1]
    off = {t: beta[2 + i] for t, i in idx.items()}
    deff = {t: beta[2 + n_team + i] for t, i in idx.items()}
    r = Ratings(teams, mu, hfa, off, deff, float('nan'), float('nan'), len(used))
    # residual scales, measured on the same weighted window (unweighted residuals)
    resid_m, resid_t = [], []
    for g in used:
        pm = r.expected_margin(g['home'], g['away'])
        pt = r.expected_total(g['home'], g['away'])
        resid_m.append((g['home_score'] - g['away_score']) - pm)
        resid_t.append((g['home_score'] + g['away_score']) - pt)
    r.sigma_margin = sd(resid_m)
    r.sigma_total = sd(resid_t)
    return r


def fit_with_availability(games, teams, availability, ridge=3.0, seasons_used=5,
                          shrinkage=10.0):
    """Same fit as ``fit_ratings`` plus an availability term for each club.

    ``availability`` maps (club, season, week) -> (n_out, n_doubtful, n_questionable).
    The term is a single points coefficient per designation level, applied as
    ``+coef_out * n_out`` to that club's expected points on both sides of the ball, shrunk
    towards zero by ``shrinkage`` pseudo-observations. Nothing is a fixed penalty: the
    coefficient is estimated from the same data the ratings are estimated from, and the
    ablation reports the difference between this fit and the plain fit.
    """
    games = list(games)
    newest = max(g['season'] for g in games)
    cut = newest - seasons_used + 1
    used = [g for g in games if g['season'] >= cut]
    idx = {t: i for i, t in enumerate(teams)}
    n_team = len(teams)
    n_par = 2 + 2 * n_team + 3   # mu, hfa, off*, def*, coef_out, coef_doubt, coef_quest
    k_out, k_dbt, k_qst = 2 + 2 * n_team, 3 + 2 * n_team, 4 + 2 * n_team
    ata = [[0.0] * n_par for _ in range(n_par)]
    atb = [0.0] * n_par
    for g in used:
        h, a = idx[g['home']], idx[g['away']]
        w = 0.75 ** (newest - g['season'])
        bo = availability.get((g['home'], g['season'], g['week']), (0, 0, 0))
        do = availability.get((g['away'], g['season'], g['week']), (0, 0, 0))
        rows = [
            (0.5 * w, float(g['home_score']),
             [(0, 1.0), (1, 1.0), (2 + h, 1.0), (2 + n_team + a, -1.0),
              (k_out, -float(bo[0])), (k_dbt, -float(bo[1])), (k_qst, -float(bo[2]))]),
            (0.5 * w, float(g['away_score']),
             [(0, 1.0), (2 + a, 1.0), (2 + n_team + h, -1.0),
              (k_out, -float(do[0])), (k_dbt, -float(do[1])), (k_qst, -float(do[2]))]),
        ]
        for ww, y, cols in rows:
            for i, vi in cols:
                atb[i] += ww * vi * y
                for j, vj in cols:
                    ata[i][j] += ww * vi * vj
    for i in range(2, 2 + 2 * n_team):
        ata[i][i] += ridge
    for i in (k_out, k_dbt, k_qst):
        ata[i][i] += shrinkage
    ata[0][0] += 1e-6
    beta = solve(ata, atb)
    r = Ratings(teams, beta[0], beta[1],
                {t: beta[2 + i] for t, i in idx.items()},
                {t: beta[2 + n_team + i] for t, i in idx.items()},
                float('nan'), float('nan'), len(used))
    r.coef = {'out': beta[k_out], 'doubtful': beta[k_dbt], 'questionable': beta[k_qst]}
    resid_m, resid_t = [], []
    for g in used:
        bo = availability.get((g['home'], g['season'], g['week']), (0, 0, 0))
        do = availability.get((g['away'], g['season'], g['week']), (0, 0, 0))
        adj = (r.coef['out'] * (bo[0] - do[0]) + r.coef['doubtful'] * (bo[1] - do[1])
               + r.coef['questionable'] * (bo[2] - do[2]))
        resid_m.append((g['home_score'] - g['away_score']) - r.expected_margin(g['home'], g['away']) + adj)
        resid_t.append((g['home_score'] + g['away_score']) - r.expected_total(g['home'], g['away'])
                       - (r.coef['out'] * (bo[0] + do[0]) + r.coef['doubtful'] * (bo[1] + do[1])
                          + r.coef['questionable'] * (bo[2] + do[2])))
    r.sigma_margin = sd(resid_m)
    r.sigma_total = sd(resid_t)
    r.availability = availability
    return r


def p_home_win_with_availability(r, g):
    bo = r.availability.get((g['home'], g['season'], g['week']), (0, 0, 0))
    do = r.availability.get((g['away'], g['season'], g['week']), (0, 0, 0))
    adj = (r.coef['out'] * (bo[0] - do[0]) + r.coef['doubtful'] * (bo[1] - do[1])
           + r.coef['questionable'] * (bo[2] - do[2]))
    return norm_cdf((r.expected_margin(g['home'], g['away']) + adj) / r.sigma_margin)


# --------------------------------------------------------------------------- scoring
def brier(probs, outs):
    return sum((p - o) ** 2 for p, o in zip(probs, outs)) / len(probs)


def logloss(probs, outs, eps=1e-12):
    tot = 0.0
    for p, o in zip(probs, outs):
        p = min(max(p, eps), 1 - eps)
        tot += -(o * math.log(p) + (1 - o) * math.log(1 - p))
    return tot / len(probs)


def brier_skill(model_probs, bench_probs, outs):
    bm = brier(model_probs, outs)
    bb = brier(bench_probs, outs)
    return 1.0 - bm / bb, bm, bb


def cluster_bootstrap_skill(rows, reps=2000, seed=20261119, alpha=0.05, level=None):
    """Bootstrap the Brier-skill ratio by resampling whole game clusters (season, week).

    ``rows``: list of (cluster_key, p_model, p_bench, outcome).
    Returns dict with point, lo, hi, n_games, n_clusters. Percentile interval.
    """
    groups = {}
    for key, pm, pb, o in rows:
        groups.setdefault(key, []).append((pm, pb, o))
    keys = list(groups)
    point = brier_skill([r[1] for r in rows], [r[2] for r in rows], [r[3] for r in rows])[0]
    rng = Lcg(seed)
    stats = []
    for _ in range(reps):
        sample = []
        for _ in range(len(keys)):
            sample.extend(groups[keys[rng.below(len(keys))]])
        try:
            stats.append(brier_skill([s[0] for s in sample], [s[1] for s in sample],
                                     [s[2] for s in sample])[0])
        except ZeroDivisionError:
            continue
    a = alpha / 2 if level is None else (1 - level) / 2
    return {'point': point, 'lo': quantile(stats, a), 'hi': quantile(stats, 1 - a),
            'n_games': len(rows), 'n_clusters': len(keys), 'reps': reps}


def paired_diff_ci(rows, reps=2000, seed=20261119, alpha=0.05):
    """Cluster bootstrap of mean(model - bench) squared-error difference.

    Positive values mean the model has HIGHER squared error than the benchmark (worse).
    """
    groups = {}
    for key, pm, pb, o in rows:
        groups.setdefault(key, []).append(((pm - o) ** 2 - (pb - o) ** 2))
    keys = list(groups)
    point = mean([v for g in groups.values() for v in g])
    rng = Lcg(seed)
    stats = []
    for _ in range(reps):
        acc = []
        for _ in range(len(keys)):
            acc.extend(groups[keys[rng.below(len(keys))]])
        stats.append(sum(acc) / len(acc))
    return {'point': point, 'lo': quantile(stats, alpha / 2), 'hi': quantile(stats, 1 - alpha / 2),
            'n_games': sum(len(v) for v in groups.values()), 'n_clusters': len(keys)}


def holm(pvals):
    """Holm step-down adjusted p-values, preserving input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = min(1.0, (m - rank) * pvals[i])
        running = max(running, val)
        adj[i] = running
    return adj


def normal_two_sided_p(z):
    return math.erfc(abs(z) / SQRT2)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float('nan'), float('nan'), float('nan'))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, max(0.0, centre - half), min(1.0, centre + half))


def pearson(xs, ys):
    xs, ys = list(xs), list(ys)
    n = len(xs)
    if n < 3:
        return (float('nan'), float('nan'), n)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return (float('nan'), float('nan'), n)
    r = sxy / math.sqrt(sxx * syy)
    # Fisher z interval
    if abs(r) < 1:
        z = 0.5 * math.log((1 + r) / (1 - r))
        se = 1 / math.sqrt(n - 3)
        lo = math.tanh(z - 1.96 * se)
        hi = math.tanh(z + 1.96 * se)
    else:
        lo = hi = r
    return (r, (lo, hi), n)


class Lcg:
    """Deterministic 64-bit LCG so every bootstrap is reproducible without numpy."""

    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def next(self):
        self.state = (6364136223846793005 * self.state + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        return self.state >> 11

    def below(self, n):
        return self.next() % n

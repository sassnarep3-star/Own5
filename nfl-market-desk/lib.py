#!/usr/bin/env python3
"""Shared helpers: CSV I/O, statistics, and provenance conventions.

Stdlib only. Every function that produces a published number is pure, so the
deterministic rebuild check in verify.py can re-run it.
"""
import csv
import gzip
import hashlib
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
ROOT = os.path.dirname(HERE)

# ---- tier vocabulary (used in every table) -----------------------------------
OFFICIAL = "OFFICIAL"
DERIVED = "DERIVED"
AGGREGATOR = "AGGREGATOR"
UNVERIFIED = "UNVERIFIED"


def wcsv(name, rows, fields=None):
    """Write rows (list of dicts) to data/<name>. Returns row count."""
    path = os.path.join(DATA, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not rows:
        raise ValueError("refusing to write an empty table: %s" % name)
    if fields is None:
        fields = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def rcsv(name):
    path = os.path.join(DATA, name)
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def rcsv_path(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def mirror_games():
    """The pinned nflverse games mirror already in the repository (AGGREGATOR tier)."""
    path = os.path.join(ROOT, "data", "decision-desk", "raw", "games.csv.gz")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def wjson(name, obj):
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")


def f(x, nd=4):
    """Format a float for publication; None -> ''."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return ("%%.%df" % nd) % x


# ---- statistics -------------------------------------------------------------
def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def sd(xs):
    xs = list(xs)
    if len(xs) < 2:
        return None
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pairs)
    if n < 3:
        return None, None, n
    mx = mean([p[0] for p in pairs])
    my = mean([p[1] for p in pairs])
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pairs)
    sxx = sum((p[0] - mx) ** 2 for p in pairs)
    syy = sum((p[1] - my) ** 2 for p in pairs)
    if sxx <= 0 or syy <= 0:
        return None, None, n
    r = sxy / math.sqrt(sxx * syy)
    p = two_sided_p_from_r(r, n)
    return r, p, n


def _betacf(a, b, x):
    MAXIT, EPS, FPMIN = 200, 3e-12, 1e-300
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


def betainc(a, b, x):
    """Regularised incomplete beta I_x(a,b)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1 - x) / b


def two_sided_p_from_r(r, n):
    if n < 3 or r is None:
        return None
    if abs(r) >= 1:
        return 0.0
    df = n - 2
    t = r * math.sqrt(df / (1 - r * r))
    return two_sided_p_from_t(t, df)


def two_sided_p_from_t(t, df):
    x = df / (df + t * t)
    return betainc(df / 2.0, 0.5, x)


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def norm_ppf(p):
    """Inverse normal CDF (Acklam's rational approximation)."""
    if p <= 0.0:
        return -float("inf")
    if p >= 1.0:
        return float("inf")
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


def american_to_prob(ml):
    """Implied probability of an American moneyline (with vig)."""
    if ml is None:
        return None
    ml = float(ml)
    if ml == 0:
        return None
    return (-ml) / (-ml + 100.0) if ml < 0 else 100.0 / (ml + 100.0)


def prob_to_american(p):
    if p is None or p <= 0 or p >= 1:
        return None
    return -100.0 * p / (1 - p) if p > 0.5 else 100.0 * (1 - p) / p


def devig_two(p_a, p_b):
    s = p_a + p_b
    return p_a / s, p_b / s


def brier(ps, ys):
    return mean([(p - y) ** 2 for p, y in zip(ps, ys)])


def wilson(k, n, z=1.96):
    if n == 0:
        return None, None
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)


def brier_skill_score(b, b_ref):
    if b is None or b_ref in (None, 0):
        return None
    return 1.0 - b / b_ref


def boot_ci(values, cluster_ids, n_boot=2000, seed=20261115):
    """Cluster bootstrap CI of the mean. Deterministic (seeded), stdlib-only.

    Clusters by cluster_ids so that two bets on the same game are not treated as
    independent observations.
    """
    if not values:
        return None, None
    groups = {}
    for v, c in zip(values, cluster_ids):
        groups.setdefault(c, []).append(v)
    keys = sorted(groups)
    state = seed
    means = []
    for _ in range(n_boot):
        acc = []
        for _k in keys:
            state = (1103515245 * state + 12345) % (2 ** 31)
            idx = state % len(keys)
            acc.extend(groups[keys[idx]])
        means.append(sum(acc) / len(acc))
    means.sort()
    lo = means[int(0.025 * (len(means) - 1))]
    hi = means[int(0.975 * (len(means) - 1))]
    return lo, hi


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, same order as input."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    out = [None] * m
    running = 0.0
    for rank, i in enumerate(idx):
        adj = min(1.0, (m - rank) * pvals[i])
        running = max(running, adj)
        out[i] = running
    return out


def binom_test_two_sided(k, n, p=0.5):
    """Exact two-sided binomial test (equal-tail, i.e. doubled smaller tail)."""
    if n == 0:
        return None
    def pmf(i):
        return math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    lo = sum(pmf(i) for i in range(0, k + 1))
    hi = sum(pmf(i) for i in range(k, n + 1))
    return min(1.0, 2 * min(lo, hi))


def normal_two_sided_p(z):
    return 2 * (1 - norm_cdf(abs(z)))

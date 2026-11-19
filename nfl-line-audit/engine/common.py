"""Shared helpers for the NFL verified line desk (stdlib only, deterministic).

Nothing here reads the network or the clock: every number is a pure function of committed
files, so a rebuild is byte-identical and a reviewer can reproduce it.
"""
import csv
import gzip
import hashlib
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(os.path.dirname(HERE), "data")
RAW = os.path.join(ROOT, "data", "decision-desk", "raw")

# ---------------------------------------------------------------- io


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def read_gz_csv(path):
    with gzip.open(path, "rt", encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.DictReader(f))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_json(obj):
    return sha256_bytes(canonical_json(obj).encode("utf-8"))


def f(x, nd=6):
    """Stable decimal formatting for CSV output."""
    if x is None or x == "":
        return ""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return ""
    if v != v or v in (float("inf"), float("-inf")):
        return ""
    return f"{v:.{nd}f}"


# ---------------------------------------------------------------- stats


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def sd(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pairs)
    if n < 3:
        return None, n
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    sxx = sum((p[0] - mx) ** 2 for p in pairs)
    syy = sum((p[1] - my) ** 2 for p in pairs)
    if sxx <= 0 or syy <= 0:
        return None, n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pairs)
    return sxy / math.sqrt(sxx * syy), n


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def norm_ppf(p):
    """Acklam's rational approximation; accurate to ~1e-9 over (0,1)."""
    if p <= 0.0:
        return float("-inf")
    if p >= 1.0:
        return float("inf")
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


def solve_linear(a, b):
    """Gauss-Jordan with partial pivoting on a small dense system."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            return None
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for j in range(col, n + 1):
            m[col][j] /= pv
        for r in range(n):
            if r != col and m[r][col] != 0.0:
                factor = m[r][col]
                for j in range(col, n + 1):
                    m[r][j] -= factor * m[col][j]
    return [m[i][n] for i in range(n)]


# ---------------------------------------------------------------- prices


def american_to_prob(a):
    """Implied probability from an American price (vig included)."""
    a = float(a)
    if a > 0:
        return 100.0 / (a + 100.0)
    if a < 0:
        return (-a) / (-a + 100.0)
    return None


def prob_to_american(p):
    if p is None or p <= 0 or p >= 1:
        return None
    if p >= 0.5:
        return -100.0 * p / (1.0 - p)
    return 100.0 * (1.0 - p) / p


def american_to_decimal(a):
    a = float(a)
    return 1.0 + (a / 100.0 if a > 0 else 100.0 / (-a))


def devig_two(p1, p2):
    """Normalise two complementary implied probabilities so they sum to 1."""
    if p1 is None or p2 is None:
        return None, None
    s = p1 + p2
    if s <= 0:
        return None, None
    return p1 / s, p2 / s


def payout_units(american, won):
    """Return profit in units of a 1-unit stake."""
    if won:
        a = float(american)
        return a / 100.0 if a > 0 else 100.0 / (-a)
    return -1.0


# ---------------------------------------------------------------- inference


def wilson_ci(k, n, z=1.959963984540054):
    if n <= 0:
        return None, None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def cluster_bootstrap(values, clusters, iterations=1000, seed=20261119, stat="mean", level=(5, 95)):
    """Cluster bootstrap over games. `values` and `clusters` are parallel lists."""
    by = {}
    for v, c in zip(values, clusters):
        by.setdefault(c, []).append(v)
    keys = sorted(by)
    rng = random.Random(seed)
    draws = []
    for _ in range(iterations):
        sample = [keys[rng.randrange(len(keys))] for _ in keys]
        flat = []
        for k in sample:
            flat.extend(by[k])
        if not flat:
            continue
        if stat == "mean":
            draws.append(sum(flat) / len(flat))
    if len(draws) < 10:
        return None, None
    draws.sort()
    lo = draws[int(level[0] / 100.0 * (len(draws) - 1))]
    hi = draws[int(level[1] / 100.0 * (len(draws) - 1))]
    return lo, hi


def holm(pvalues):
    """Holm-Bonferroni adjusted p-values, order preserved."""
    idx = sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    m = len(pvalues)
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(idx):
        val = (m - rank) * pvalues[i]
        running = max(running, val)
        adj[i] = min(1.0, running)
    return adj


def two_sided_p_from_z(z):
    return 2.0 * (1.0 - norm_cdf(abs(z)))

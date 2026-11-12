"""Shared, stdlib-only statistics and IO helpers for the Decision Desk."""
from __future__ import annotations

import csv
import gzip
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "decision-desk", "raw")
OUTDIR = os.path.join(ROOT, "data", "decision-desk")


# ---------------------------------------------------------------- IO
def read_csv_gz(path: str) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


DERIVED_SOURCE = ("https://github.com/sassnarep3-star/Own5/blob/main/"
                  "tools/decision_desk/")


def _caller_script() -> str:
    import sys
    for arg in sys.argv:
        if arg.endswith(".py"):
            return os.path.basename(arg)
    return "build_all.py"


def write_csv(name: str, rows: list[dict], fields: list[str],
              derived: bool = True) -> str:
    """Write a CSV. Derived tables get a per-row methodology link so that the
    "every row carries a source link" rule holds for computed tables too."""
    if derived and rows and "source_url" not in fields:
        fields = list(fields) + ["source_url"]
        link = DERIVED_SOURCE + _caller_script()
        for r in rows:
            r["source_url"] = link
    path = os.path.join(OUTDIR, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return path


def write_json(name: str, obj) -> str:
    path = os.path.join(OUTDIR, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def fnum(x):
    """Format a float for CSV output without inventing precision."""
    if x is None:
        return ""
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return ""
        return f"{x:.6g}"
    return x


# ---------------------------------------------------------------- stats
def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")


def sd(xs):
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return float("nan")
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def two_sided_p(z: float) -> float:
    return 2.0 * (1.0 - norm_cdf(abs(z)))


def wilson(k: int, n: int, z: float = 1.959963985) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def binom_p_exact(k: int, n: int, p0: float) -> float:
    """Exact two-sided binomial test in log space (stable for large n)."""
    if n == 0:
        return float("nan")
    if p0 <= 0 or p0 >= 1:
        return float("nan")
    lp, lq = math.log(p0), math.log(1 - p0)
    lg = math.lgamma
    logs = [lg(n + 1) - lg(i + 1) - lg(n - i + 1) + i * lp + (n - i) * lq
            for i in range(n + 1)]
    mx = max(logs)
    pmf = [math.exp(v - mx) for v in logs]
    obs = pmf[k]
    tol = obs * 1e-9 + 1e-15
    return min(1.0, sum(v for v in pmf if v <= obs + tol))


def fisher_ci(r: float, n: int, z: float = 1.959963985):
    if n is None or n < 4 or r is None:
        return (float("nan"), float("nan"))
    r = max(min(r, 0.999999), -0.999999)
    zr = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    return (math.tanh(zr - z * se), math.tanh(zr + z * se))


def pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys)
             if x is not None and y is not None
             and not (isinstance(x, float) and math.isnan(x))
             and not (isinstance(y, float) and math.isnan(y))]
    n = len(pairs)
    if n < 3:
        return (float("nan"), float("nan"), n)
    mx = mean([p[0] for p in pairs])
    my = mean([p[1] for p in pairs])
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    syy = sum((y - my) ** 2 for _, y in pairs)
    if sxx == 0 or syy == 0:
        return (float("nan"), float("nan"), n)
    r = sxy / math.sqrt(sxx * syy)
    # t statistic -> p via normal approximation for large n
    if abs(r) >= 1:
        return (r, 0.0, n)
    t = r * math.sqrt((n - 2) / (1 - r * r))
    return (r, two_sided_p(t), n)


def ols(y, X, names=None):
    """Ordinary least squares with heteroskedasticity-robust (HC1) errors.

    ``X`` must already contain a leading 1.0 column for the intercept.
    Returns dict with coefficients, robust SEs, t, p, n, r2.
    """
    n = len(y)
    k = len(X[0])
    # normal equations
    XtX = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    Xty = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
    inv = _inv(XtX)
    if inv is None:
        return None
    beta = [sum(inv[a][b] * Xty[b] for b in range(k)) for a in range(k)]
    resid = [y[i] - sum(beta[a] * X[i][a] for a in range(k)) for i in range(n)]
    # HC1 covariance: (X'X)^-1 (X' diag(e^2) X) (X'X)^-1 * n/(n-k)
    Xe = [[X[i][a] * resid[i] for a in range(k)] for i in range(n)]
    meat = [[sum(Xe[i][a] * Xe[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    tmp = [[sum(inv[a][c] * meat[c][b] for c in range(k)) for b in range(k)] for a in range(k)]
    cov = [[sum(tmp[a][c] * inv[c][b] for c in range(k)) for b in range(k)] for a in range(k)]
    scale = n / (n - k) if n > k else 1.0
    se = [math.sqrt(max(cov[a][a], 0) * scale) for a in range(k)]
    ss_tot = sum((v - mean(y)) ** 2 for v in y)
    ss_res = sum(e * e for e in resid)
    return {
        "names": names or [f"x{i}" for i in range(k)],
        "beta": beta, "se": se, "n": n,
        "t": [beta[a] / se[a] if se[a] else float("nan") for a in range(k)],
        "p": [two_sided_p(beta[a] / se[a]) if se[a] else float("nan") for a in range(k)],
        "r2": 1 - ss_res / ss_tot if ss_tot else float("nan"),
        "resid": resid,
    }


def _inv(m):
    n = len(m)
    a = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[piv][col]) < 1e-12:
            return None
        a[col], a[piv] = a[piv], a[col]
        pv = a[col][col]
        a[col] = [v / pv for v in a[col]]
        for r in range(n):
            if r != col and a[r][col] != 0:
                fac = a[r][col]
                a[r] = [v - fac * w for v, w in zip(a[r], a[col])]
    return [row[n:] for row in a]


def sharpe(returns):
    m = mean(returns)
    s = sd(returns)
    return (m / s * math.sqrt(len(returns))) if s and s == s and s > 0 else float("nan")


def required_n_for_power(p1: float, p0: float, alpha: float = 0.05, power: float = 0.80) -> int:
    """One-sided sample size for a binomial proportion vs a null (normal approx)."""
    z_a = _z(1 - alpha)
    z_b = _z(power)
    pbar = (p1 + p0) / 2
    num = (z_a * math.sqrt(p0 * (1 - p0)) + z_b * math.sqrt(p1 * (1 - p1))) ** 2
    den = (p1 - p0) ** 2
    return int(math.ceil(num / den)) if den else 0


def _z(p: float) -> float:
    """Inverse normal CDF via bisection (stdlib has no ppf)."""
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

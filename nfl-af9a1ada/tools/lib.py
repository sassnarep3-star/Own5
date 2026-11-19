"""Shared numeric helpers for the NFL line-gate desk.

Deterministic, standard library only, unit-tested in ``nfl-af9a1ada/tests``.
Nothing here reads the network.

Conventions
-----------
* A **printed home spread** of -6.0 means the home club is favoured by six
  points; the away line is its mirror (+6.0). This is the operators' print
  convention.
* **American price** +525 pays 525 on a 100 stake; -750 risks 750 to win 100.
* Probabilities are floats in [0, 1]. Two-way markets are de-vigged
  multiplicatively (proportional method) and the residual overround is
  published beside every de-vigged number.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Iterable, Sequence


def american_to_decimal(price: float) -> float:
    if price == 0:
        raise ValueError("an American price of 0 is not a price")
    return 1.0 + (price / 100.0 if price > 0 else 100.0 / abs(price))


def american_to_prob(price: float) -> float:
    if price > 0:
        return 100.0 / (price + 100.0)
    return abs(price) / (abs(price) + 100.0)


def prob_to_american(p: float) -> float:
    if not 0.0 < p < 1.0:
        raise ValueError(f"probability out of range: {p}")
    return -100.0 * p / (1.0 - p) if p >= 0.5 else 100.0 * (1.0 - p) / p


def devig_two_way(price_a: float, price_b: float) -> tuple[float, float, float]:
    """Return (p_a, p_b, overround) for a two-way market."""
    pa, pb = american_to_prob(price_a), american_to_prob(price_b)
    total = pa + pb
    return pa / total, pb / total, total - 1.0


def brier_binary(p: float, outcome: int) -> float:
    if outcome not in (0, 1):
        raise ValueError("outcome must be 0 or 1")
    return (p - outcome) ** 2


def mean(xs: Iterable[float]) -> float:
    xs = list(xs)
    if not xs:
        raise ValueError("mean of an empty sequence")
    return sum(xs) / len(xs)


def stdev(xs: Iterable[float]) -> float:
    xs = list(xs)
    if len(xs) < 2:
        return float("nan")
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def pearson(xs: Sequence, ys: Sequence) -> tuple[float, int]:
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pairs)
    if n < 3:
        return float("nan"), n
    mx = mean(x for x, _ in pairs)
    my = mean(y for _, y in pairs)
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    syy = sum((y - my) ** 2 for _, y in pairs)
    if sxx == 0 or syy == 0:
        return float("nan"), n
    return sxy / math.sqrt(sxx * syy), n


def cluster_bootstrap_ci(clusters: dict, stat, draws: int = 2000,
                         seed: int = 20261119) -> tuple[float, float]:
    """Percentile bootstrap that resamples whole games, not individual bets."""
    import random
    keys = sorted(clusters)
    if not keys:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    estimates = []
    for _ in range(draws):
        flat = []
        for _ in range(len(keys)):
            flat.extend(clusters[keys[rng.randrange(len(keys))]])
        if flat:
            try:
                estimates.append(stat(flat))
            except ValueError:
                continue
    estimates = [v for v in estimates if v == v]
    if len(estimates) < 10:
        return float("nan"), float("nan")
    estimates.sort()
    return estimates[int(0.025 * (len(estimates) - 1))], estimates[int(0.975 * (len(estimates) - 1))]


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def inputs_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def pick_spread_winner(margin_home: float, home_spread: float) -> str:
    """Who covered, given the realised home margin and the printed home line."""
    adj = margin_home + home_spread
    return "home" if adj > 0 else ("away" if adj < 0 else "push")


def total_result(total_points: float, line: float) -> str:
    if total_points > line:
        return "over"
    if total_points < line:
        return "under"
    return "push"

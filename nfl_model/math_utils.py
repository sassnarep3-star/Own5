"""Small, deterministic statistical primitives (standard library only)."""
from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Callable, Iterable, Sequence


def finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def pearson(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) != len(y) or len(x) < 2:
        return None
    mx, my = mean(x), mean(y)
    sx = sum((v - mx) ** 2 for v in x)
    sy = sum((v - my) ** 2 for v in y)
    if sx <= 0 or sy <= 0:
        return None
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sx * sy)


def ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        rank = (i + 1 + j) / 2
        for k in range(i, j):
            out[order[k]] = rank
        i = j
    return out


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    return pearson(ranks(x), ranks(y))


def phi(a: Sequence[int], b: Sequence[int]) -> float | None:
    if len(a) != len(b) or not a or any(v not in (0, 1) for v in [*a, *b]):
        return None
    p, q = mean(a), mean(b)
    denominator = math.sqrt(p * (1 - p) * q * (1 - q))
    if denominator == 0:
        return None
    return (sum(x * y for x, y in zip(a, b)) / len(a) - p * q) / denominator


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float] | None:
    if n <= 0 or not 0 <= successes <= n:
        return None
    p = successes / n
    d = 1 + z * z / n
    center = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, center - half), min(1.0, center + half)


def bootstrap_ci(values: Sequence[float], statistic: Callable[[Sequence[float]], float | None],
                 *, draws: int = 10000, seed: int = 20261102,
                 confidence: float = 0.95) -> tuple[float | None, float | None]:
    """IID percentile bootstrap. Use only for independent observations."""
    if len(values) < 2 or draws < 1 or not 0 < confidence < 1:
        return None, None
    rng = random.Random(seed)
    estimates = []
    n = len(values)
    for _ in range(draws):
        estimate = statistic([values[rng.randrange(n)] for _ in range(n)])
        if estimate is not None and finite(estimate):
            estimates.append(estimate)
    if len(estimates) < max(20, draws * 0.8):
        return None, None
    estimates.sort()
    alpha = (1 - confidence) / 2
    return estimates[int(alpha * (len(estimates) - 1))], estimates[int((1 - alpha) * (len(estimates) - 1))]


def cluster_bootstrap_ci(records: Sequence[dict], statistic: Callable[[list[dict]], float | None],
                         *, cluster_key: str = "season_week", draws: int = 10000,
                         seed: int = 20261102, confidence: float = 0.95,
                         stationary_block: bool = False, mean_block: int = 4) -> tuple[float | None, float | None]:
    """Resample whole clusters; optionally use circular stationary blocks of clusters.

    Records in the same season-week are never separated. The caller supplies a
    statistic that aggregates all tickets/legs itself (e.g. sum(profit)/sum(stake)).
    """
    if not records or draws < 1 or not 0 < confidence < 1 or mean_block < 1:
        return None, None
    groups: dict[object, list[dict]] = defaultdict(list)
    for record in records:
        if cluster_key not in record:
            raise ValueError(f"Missing cluster key: {cluster_key}")
        groups[record[cluster_key]].append(record)
    keys = sorted(groups, key=str)
    if len(keys) < 2:
        return None, None
    rng = random.Random(seed)
    estimates = []
    n = len(keys)
    for _ in range(draws):
        sample = []
        if stationary_block:
            i = rng.randrange(n)
            while len(sample) < n:
                sample.extend(groups[keys[i % n]])
                i = i + 1 if rng.random() >= 1 / mean_block else rng.randrange(n)
        else:
            for _ in range(n):
                sample.extend(groups[keys[rng.randrange(n)]])
        estimate = statistic(sample[:])
        if estimate is not None and finite(estimate):
            estimates.append(estimate)
    if len(estimates) < max(20, draws * 0.8):
        return None, None
    estimates.sort()
    alpha = (1 - confidence) / 2
    return estimates[int(alpha * (len(estimates) - 1))], estimates[int((1 - alpha) * (len(estimates) - 1))]


def american_to_decimal(price: int | float) -> float:
    if not finite(price) or price == 0 or abs(price) < 100:
        raise ValueError("American odds must be nonzero and at least 100 in absolute value")
    return 1 + (price / 100 if price > 0 else 100 / abs(price))


def decimal_to_american(decimal: float) -> int | None:
    if not finite(decimal) or decimal <= 1:
        return None
    return round((decimal - 1) * 100) if decimal >= 2 else round(-100 / (decimal - 1))


def probability_to_american(probability: float) -> int | None:
    if not finite(probability) or not 0 < probability < 1:
        return None
    return decimal_to_american(1 / probability)


def devig_two_way(prices: Sequence[float]) -> list[float] | None:
    """Proportional de-vig of decimal prices; not appropriate for push markets."""
    if len(prices) != 2 or any(not finite(p) or p <= 1 for p in prices):
        return None
    raw = [1 / p for p in prices]
    total = sum(raw)
    return [p / total for p in raw]


def binary_ev(probability: float, decimal_price: float) -> float | None:
    """EV per unit stake for a binary no-push market."""
    if not finite(probability) or not 0 <= probability <= 1 or not finite(decimal_price) or decimal_price <= 1:
        return None
    return probability * decimal_price - 1


def push_aware_ev(p_win: float, p_loss: float, decimal_price: float) -> float | None:
    if any(not finite(v) for v in (p_win, p_loss, decimal_price)):
        return None
    if min(p_win, p_loss) < 0 or p_win + p_loss > 1 + 1e-12 or decimal_price <= 1:
        return None
    return p_win * (decimal_price - 1) - p_loss


def joint_bounds(p: float, q: float) -> tuple[float, float]:
    if not 0 <= p <= 1 or not 0 <= q <= 1:
        raise ValueError("Marginal probabilities must be in [0, 1]")
    return max(0.0, p + q - 1), min(p, q)


def settle_binary(outcome: str, decimal_price: float, stake: float = 1.0) -> float:
    if outcome not in {"win", "loss", "push", "void"} or not finite(stake) or stake < 0:
        raise ValueError("Invalid settlement input")
    if not finite(decimal_price) or decimal_price <= 1:
        raise ValueError("Invalid decimal price")
    return stake * (decimal_price - 1) if outcome == "win" else -stake if outcome == "loss" else 0.0


def settle_parlay(outcomes: Sequence[str], decimal_prices: Sequence[float], *,
                  same_game: bool = False,
                  sgp_reprice: Callable[[Sequence[int]], Sequence[float]] | None = None,
                  stake: float = 1.0) -> float:
    """Settle a paper ticket; SGP void/push repricing must be supplied explicitly.

    Cross-game pushes/voids remove the leg. A loss dominates remaining pushes/voids.
    For an SGP, any non-win leg requires the operator's exact repricing function;
    there is deliberately no universal default.
    """
    if len(outcomes) != len(decimal_prices) or not outcomes:
        raise ValueError("Each leg needs one outcome and one price")
    if any(o not in {"win", "loss", "push", "void"} for o in outcomes):
        raise ValueError("Invalid leg outcome")
    if any(not finite(p) or p <= 1 for p in decimal_prices) or not finite(stake) or stake < 0:
        raise ValueError("Invalid price or stake")
    if "loss" in outcomes:
        return -stake
    active = [i for i, o in enumerate(outcomes) if o == "win"]
    if not active:
        return 0.0
    prices = list(decimal_prices)
    if len(active) != len(outcomes):
        if same_game:
            if sgp_reprice is None:
                raise ValueError("Operator-specific SGP repricing is required")
            prices = list(sgp_reprice(active))
            if len(prices) != len(active) or any(not finite(p) or p <= 1 for p in prices):
                raise ValueError("Invalid operator repricing")
        else:
            prices = [decimal_prices[i] for i in active]
    combined = math.prod(prices)
    return stake * (combined - 1)


def brier(probabilities: Sequence[float], outcomes: Sequence[int]) -> float | None:
    if not probabilities or len(probabilities) != len(outcomes):
        return None
    if any(not finite(p) or not 0 <= p <= 1 or o not in (0, 1) for p, o in zip(probabilities, outcomes)):
        return None
    return sum((p - o) ** 2 for p, o in zip(probabilities, outcomes)) / len(probabilities)


def log_loss(probabilities: Sequence[float], outcomes: Sequence[int], epsilon: float = 1e-15) -> float | None:
    if not probabilities or len(probabilities) != len(outcomes):
        return None
    if any(not finite(p) or not 0 <= p <= 1 or o not in (0, 1) for p, o in zip(probabilities, outcomes)):
        return None
    return -sum(o * math.log(max(epsilon, p)) + (1 - o) * math.log(max(epsilon, 1 - p))
                for p, o in zip(probabilities, outcomes)) / len(probabilities)


def calibration_error(probabilities: Sequence[float], outcomes: Sequence[int], bins: int = 10) -> float | None:
    if not probabilities or len(probabilities) != len(outcomes) or bins < 1:
        return None
    if any(not finite(p) or not 0 <= p <= 1 or o not in (0, 1) for p, o in zip(probabilities, outcomes)):
        return None
    buckets: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for p, o in zip(probabilities, outcomes):
        buckets[min(bins - 1, int(p * bins))].append((p, o))
    return sum(len(b) / len(probabilities) * abs(mean([p for p, _ in b]) - mean([o for _, o in b]))
               for b in buckets if b)


def max_drawdown_units(profits_in_time_order: Iterable[float]) -> float:
    equity = peak = drawdown = 0.0
    for profit in profits_in_time_order:
        if not finite(profit):
            raise ValueError("Non-finite profit")
        equity += profit
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown

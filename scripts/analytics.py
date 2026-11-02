"""Input-checked math utilities. No fitted model, observations, or NFL estimates.

Derivations and assumptions: research/METHODOLOGY.md.
Primary methodology refs: SciPy pearsonr, sklearn calibration, statsmodels multipletests.
"""
import math


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('A finite numeric value is required')
    return float(value)


def probability(value):
    value = finite(value)
    if not 0 <= value <= 1:
        raise ValueError('Probability must be in [0, 1]')
    return value


def decimal_from_american(odds):
    odds = finite(odds)
    if abs(odds) < 100:
        raise ValueError('Conventional American odds require absolute magnitude >= 100')
    return 1 + (odds / 100 if odds > 0 else 100 / abs(odds))


def fair_decimal(win, push=0):
    win, push = probability(win), probability(push)
    if win + push > 1 or win == 0:
        raise ValueError('Positive win probability and win + push <= 1 required')
    return (1 - push) / win


def expected_return(win, decimal, push=0):
    win, push, decimal = probability(win), probability(push), finite(decimal)
    if win + push > 1 or decimal <= 1:
        raise ValueError('Invalid win/push distribution or decimal odds')
    return win * decimal + push - 1


def proportional_devig(prices):
    prices = [finite(x) for x in prices]
    if len(prices) < 2 or any(x <= 1 for x in prices):
        raise ValueError('Supply a complete no-push market with >= 2 decimal prices > 1')
    total = sum(1 / x for x in prices)
    return [(1 / x) / total for x in prices]


def pearson(x, y):
    x, y = [finite(v) for v in x], [finite(v) for v in y]
    if len(x) != len(y) or len(x) < 2:
        raise ValueError('Matched arrays with at least two observations required')
    mx, my = sum(x) / len(x), sum(y) / len(y)
    dx, dy = [a - mx for a in x], [b - my for b in y]
    sx, sy = sum(a*a for a in dx), sum(b*b for b in dy)
    if sx == 0 or sy == 0:
        return None  # Undefined, not zero correlation.
    return max(-1.0, min(1.0, sum(a*b for a,b in zip(dx,dy)) / math.sqrt(sx*sy)))


def joint_bounds(a, b):
    a, b = probability(a), probability(b)
    return max(0, a + b - 1), min(a, b)


def settlement_ev(states):
    """States contain (probability, net return per unit) and must exhaust outcomes."""
    states = [(probability(p), finite(r)) for p, r in states]
    if not states or not math.isclose(sum(p for p, _ in states), 1, abs_tol=1e-10):
        raise ValueError('Exhaustive state probabilities must sum to one')
    if any(r < -1 for _,r in states):
        raise ValueError('Unit-stake loss cannot exceed one')
    return sum(p*r for p,r in states)


def brier(predictions, outcomes):
    predictions = [probability(p) for p in predictions]
    outcomes = list(outcomes)
    if not predictions or len(predictions) != len(outcomes) or any(type(y) is not int or y not in (0,1) for y in outcomes):
        raise ValueError('Matched probabilities and binary integer outcomes required')
    return sum((p-y)**2 for p,y in zip(predictions,outcomes)) / len(predictions)


def holm(pvalues):
    """Holm step-down adjusted p-values in original order; assumes valid raw p-values."""
    values = [probability(p) for p in pvalues]
    ordered = sorted(range(len(values)), key=lambda i: values[i])
    adjusted, previous = [0.0] * len(values), 0.0
    for rank, index in enumerate(ordered):
        previous = max(previous, min(1.0, (len(values)-rank)*values[index]))
        adjusted[index] = previous
    return adjusted


def gate_decision(evidence):
    """Fail closed. Evidence values must be actual booleans, not truthy strings.

    This checks audit declarations only; it does not verify an empirical audit.
    """
    keys = [f'G{i:02}' for i in range(1,8)]
    missing = [k for k in keys if evidence.get(k) is not True]
    return {'eligible': not missing, 'action': 'PAPER_RESEARCH_ONLY' if not missing else 'ABSTAIN', 'blocked_gates': missing}

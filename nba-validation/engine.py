"""Research-only pricing primitives. No external data or certification inferred."""
import math
from statistics import median

GATES = ('provenance', 'asof', 'settlement', 'preregistered', 'holdout',
         'calibration', 'multiplicity', 'net_edge', 'dependence', 'replication')

def probability(p):
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
        raise ValueError('Finite probability required')
    return p

def fair_decimal(p):
    probability(p)
    if p == 0: raise ValueError('Zero probability has no finite fair price')
    return 1 / p

def expected_return(p_win, p_push, decimal):
    probability(p_win); probability(p_push)
    if p_win + p_push > 1 or not math.isfinite(decimal) or decimal <= 1:
        raise ValueError('Invalid outcomes or price')
    return p_win * decimal + p_push - 1

def joint_bounds(a, b):
    probability(a); probability(b)
    return max(0, a+b-1), min(a,b)

def joint_from_phi(a, b, phi):
    probability(a); probability(b)
    if not math.isfinite(phi) or not -1 <= phi <= 1: raise ValueError('Invalid phi')
    if a in (0,1) or b in (0,1): raise ValueError('Phi undefined for constant outcome')
    joint = a*b + phi*math.sqrt(a*(1-a)*b*(1-b))
    lo, hi = joint_bounds(a,b)
    if joint < lo-1e-12 or joint > hi+1e-12: raise ValueError('Infeasible Bernoulli correlation')
    return min(hi,max(lo,joint))

def empirical_line(draws):
    """Median fair threshold from a supplied forecast distribution, not historical claims."""
    if not draws or any(isinstance(x,bool) or not math.isfinite(x) for x in draws):
        raise ValueError('Finite forecast draws required')
    return median(draws)

def holm(p_values, alpha=0.05):
    if not 0 < alpha < 1: raise ValueError('Invalid alpha')
    for p in p_values: probability(p)
    result = [False]*len(p_values)
    for rank, i in enumerate(sorted(range(len(p_values)), key=lambda i:p_values[i])):
        if p_values[i] > alpha/(len(p_values)-rank): break
        result[i] = True
    return result

def eligible(evidence):
    """Administrative gate aggregation only; evidence review happens upstream."""
    return all(evidence.get(key) is True for key in GATES)

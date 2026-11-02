"""Separating skill from luck.

A positive backtest ROI is not evidence of skill. This module quantifies how
much of an observed result could plausibly be noise, and refuses to promote a
strategy that cannot clear the bar.

Techniques
----------
1. Break-even benchmark from the ACTUAL prices taken (not a fixed 52.4%).
2. Exact binomial test of wins vs that break-even rate.
3. Stationary (cluster) bootstrap of ROI, resampling whole weeks so that
   same-week correlation is preserved.
4. Benjamini-Hochberg FDR control across the whole strategy family, because
   testing many strategies manufactures winners.
5. Deflated Sharpe Ratio: the Sharpe expected from the best of N noise-only
   trials is subtracted before declaring skill.
6. Luck share: fraction of outcome variance explained by pure binomial noise.
7. Minimum detectable edge: how many bets would be needed to distinguish the
   observed edge from zero at 80% power.
8. Season-split stability: does the sign survive in independent eras?
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats

from common import OUT, american_to_decimal, write_csv, write_json

RNG = np.random.default_rng(20261102)
N_BOOT = 10000
FDR_ALPHA = 0.10


def breakeven_prob(prices: np.ndarray) -> float:
    """Stake-weighted break-even win probability for the prices actually taken."""
    dec = american_to_decimal(prices)
    # For 1 unit staked, break-even p satisfies p*(dec-1) = (1-p)
    return float(np.mean(1.0 / dec))


def cluster_bootstrap_roi(df: pd.DataFrame, n_boot: int = N_BOOT) -> dict:
    """Resample whole (season, week) clusters, preserving within-week dependence."""
    if df.empty:
        return {"roi_ci_low": None, "roi_ci_high": None, "p_roi_positive": None}
    clusters = (df.season.astype(str) + "_" + df.week.astype(str)).values
    uniq = np.unique(clusters)
    prof = df.profit.values
    stake = np.where(df.result.values != 0, df.stake.values, 0.0)
    idx_by = {c: np.where(clusters == c)[0] for c in uniq}
    rois = np.empty(n_boot)
    for i in range(n_boot):
        pick = RNG.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by[c] for c in pick])
        s = stake[idx].sum()
        rois[i] = prof[idx].sum() / s if s > 0 else 0.0
    lo, hi = np.percentile(rois, [2.5, 97.5])
    return {
        "roi_ci_low": round(float(lo), 5),
        "roi_ci_high": round(float(hi), 5),
        "p_roi_positive": round(float((rois > 0).mean()), 5),
    }


def deflated_sharpe(returns: np.ndarray, n_trials: int) -> tuple[float, float]:
    """Deflated Sharpe Ratio (Bailey & Lopez de Prado).

    SR0 is the Sharpe we would expect the BEST of ``n_trials`` pure-noise
    strategies to show. A strategy must beat that hurdle, not zero.
    """
    r = np.asarray(returns, dtype=float)
    n = len(r)
    if n < 10 or r.std() == 0:
        return float("nan"), float("nan")
    sr = r.mean() / r.std(ddof=1)
    skew = float(stats.skew(r))
    kurt = float(stats.kurtosis(r, fisher=False))
    euler = 0.5772156649
    # Expected maximum Sharpe over n_trials independent noise trials, expressed
    # in the same per-period units as the observed Sharpe. The variance of the
    # Sharpe estimate across trials is ~1/(n-1) for noise-only returns, so the
    # expected maximum is scaled by that standard error.
    z1 = stats.norm.ppf(1.0 - 1.0 / max(n_trials, 2))
    z2 = stats.norm.ppf(1.0 - 1.0 / (max(n_trials, 2) * math.e))
    sr_se = 1.0 / math.sqrt(max(n - 1, 2))
    sr0 = ((1 - euler) * z1 + euler * z2) * sr_se
    denom = math.sqrt(max(1e-12, 1 - skew * sr + (kurt - 1) / 4.0 * sr ** 2))
    dsr = stats.norm.cdf(((sr - sr0) * math.sqrt(n - 1)) / denom)
    return float(dsr), float(sr0)


def luck_share(wins: int, losses: int, p_breakeven: float) -> float:
    """Share of the observed win-count deviation that noise alone can explain.

    Compares |observed - expected| to the binomial standard deviation. A value
    at or above 1 means the deviation is within one sigma of pure luck.
    """
    n = wins + losses
    if n == 0:
        return float("nan")
    expected = n * p_breakeven
    sd = math.sqrt(n * p_breakeven * (1 - p_breakeven))
    if sd == 0:
        return float("nan")
    z = abs(wins - expected) / sd
    # Noise-explained share: 1 when z<=1, decaying as evidence accumulates.
    return round(float(min(1.0, 1.0 / max(z, 1e-9))), 5)


def required_sample(edge: float, p0: float = 0.5238, power: float = 0.80,
                    alpha: float = 0.05) -> int | None:
    """Bets needed to detect a true win-rate edge at the given power."""
    if not np.isfinite(edge) or edge <= 0:
        return None
    p1 = min(0.999, p0 + edge)
    za = stats.norm.ppf(1 - alpha / 2)
    zb = stats.norm.ppf(power)
    pbar = (p0 + p1) / 2
    num = (za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2
    return int(math.ceil(num / (p1 - p0) ** 2))


def benjamini_hochberg(pvals: list[float], alpha: float = FDR_ALPHA) -> list[bool]:
    """Return a mask of discoveries at the given false-discovery rate."""
    m = len(pvals)
    order = np.argsort(pvals)
    out = [False] * m
    kmax = -1
    for rank, i in enumerate(order, start=1):
        if pvals[i] <= alpha * rank / m:
            kmax = rank
    for rank, i in enumerate(order, start=1):
        if rank <= kmax:
            out[i] = True
    return out


def analyse(bets: pd.DataFrame) -> pd.DataFrame:
    strategies = sorted(bets.strategy.unique())
    n_trials = len(strategies)
    rows = []
    for name in strategies:
        sub = bets[bets.strategy == name].copy()
        dec = sub[sub.result != 0]
        wins = int((dec.result > 0).sum())
        losses = int((dec.result < 0).sum())
        n = wins + losses
        if n == 0:
            continue
        p0 = breakeven_prob(dec.price_american.values)
        wr = wins / n
        roi = float(sub.profit.sum() / dec.stake.sum())
        # One-sided test: is the true win rate above break-even?
        pval = float(stats.binomtest(wins, n, p0, alternative="greater").pvalue)
        boot = cluster_bootstrap_roi(sub)
        dsr, sr0 = deflated_sharpe(sub.profit.values, n_trials)
        # Era stability: first half vs second half of seasons.
        mid = int(np.median(sub.season))
        e1 = sub[sub.season <= mid]
        e2 = sub[sub.season > mid]
        r1 = float(e1.profit.sum() / max(1e-9, e1[e1.result != 0].stake.sum())) if len(e1) else None
        r2 = float(e2.profit.sum() / max(1e-9, e2[e2.result != 0].stake.sum())) if len(e2) else None
        stable = bool(r1 is not None and r2 is not None and np.sign(r1) == np.sign(r2) and r1 > 0)
        rows.append({
            "strategy": name, "bets": len(sub), "decided": n,
            "wins": wins, "losses": losses, "pushes": int((sub.result == 0).sum()),
            "win_rate": round(wr, 5),
            "breakeven_win_rate": round(p0, 5),
            "win_rate_edge": round(wr - p0, 5),
            "roi": round(roi, 5),
            **boot,
            "binom_p_one_sided": round(pval, 6),
            "deflated_sharpe": round(dsr, 5) if np.isfinite(dsr) else None,
            "noise_sharpe_hurdle": round(sr0, 5) if np.isfinite(sr0) else None,
            "luck_share": luck_share(wins, losses, p0),
            "bets_needed_for_80pct_power": required_sample(max(0.0, wr - p0), p0),
            "roi_era1": round(r1, 5) if r1 is not None else None,
            "roi_era2": round(r2, 5) if r2 is not None else None,
            "era_stable_positive": stable,
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["bh_fdr_significant"] = benjamini_hochberg(df.binom_p_one_sided.tolist())
    return df


def main() -> None:
    bets = pd.read_csv(OUT / "bets.csv")
    df = analyse(bets)
    write_csv(df, "skill_luck.csv")
    cols = ["strategy", "decided", "win_rate", "breakeven_win_rate", "roi",
            "roi_ci_low", "roi_ci_high", "binom_p_one_sided", "bh_fdr_significant",
            "deflated_sharpe", "luck_share", "era_stable_positive"]
    print("=== SKILL VS LUCK ===")
    print(df[cols].to_string(index=False))
    write_json("skill_luck_summary.json", {
        "strategies_tested": int(len(df)),
        "bootstrap_replicates": N_BOOT,
        "fdr_alpha": FDR_ALPHA,
        "surviving_fdr": int(df.bh_fdr_significant.sum()),
        "positive_roi": int((df.roi > 0).sum()),
        "note": "Luck cannot be removed from outcomes; it can only be bounded. "
                "No strategy is promoted on point estimate alone.",
    })


if __name__ == "__main__":
    main()

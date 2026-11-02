"""Validation gates and the strategy leaderboard.

A strategy is only eligible for a reward tier if it clears EVERY hard gate.
Gates are defined before looking at results and are applied mechanically.

Hard gates
----------
G1  Sample size          >= 500 decided bets (parlays >= 300)
G2  Positive ROI         point estimate > 0
G3  Bootstrap CI         95% cluster-bootstrap lower bound on ROI > 0
G4  Significance         exact binomial p < 0.05 vs actual break-even
G5  Multiple testing     survives Benjamini-Hochberg FDR at 10%
G6  Deflated Sharpe      DSR > 0.95 (beats best-of-N noise hurdle)
G7  Era stability        positive ROI in both halves of the sample
G8  Price integrity      >= 90% of bets at real (non-assumed) prices
G9  Official verification >= 50% of bets traceable to official NFL.com scores
G10 No lookahead         model priced strictly walk-forward (structural, asserted)

The leaderboard ranks only gate-passing strategies by risk-adjusted return.
Strategies that fail are still shown, with the reason, because a graveyard of
failed ideas is the actual product of honest research.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import OUT, write_csv, write_json

GATES = [
    ("G1", "Sample size", ">=500 decided bets (>=300 for combination markets)"),
    ("G2", "Positive ROI", "ROI point estimate > 0"),
    ("G3", "Bootstrap CI", "95% cluster-bootstrap lower bound on ROI > 0"),
    ("G4", "Statistical significance", "exact binomial p < 0.05 vs realised break-even rate"),
    ("G5", "Multiple-testing control", "survives Benjamini-Hochberg FDR at 10%"),
    ("G6", "Deflated Sharpe", "DSR > 0.95 (clears best-of-N noise hurdle)"),
    ("G7", "Era stability", "positive ROI in both chronological halves"),
    ("G8", "Price integrity", ">=90% of bets graded at real, non-assumed prices"),
    ("G9", "Official verification", ">=50% of bets traceable to official NFL.com scores"),
    ("G10", "No lookahead", "walk-forward pricing, structurally enforced"),
]


def evaluate() -> tuple[pd.DataFrame, pd.DataFrame]:
    sl = pd.read_csv(OUT / "skill_luck.csv")
    bets = pd.read_csv(OUT / "bets.csv")
    rows = []
    for r in sl.itertuples():
        sub = bets[bets.strategy == r.strategy]
        min_n = 300 if r.strategy.startswith("P") else 500
        real_price_share = float((sub.assumed_price == 0).mean())
        ver_share = float(sub.official_verified.mean())
        g = {
            "G1": bool(r.decided >= min_n),
            "G2": bool(r.roi > 0),
            "G3": bool(pd.notna(r.roi_ci_low) and r.roi_ci_low > 0),
            "G4": bool(r.binom_p_one_sided < 0.05),
            "G5": bool(r.bh_fdr_significant),
            "G6": bool(pd.notna(r.deflated_sharpe) and r.deflated_sharpe > 0.95),
            "G7": bool(r.era_stable_positive),
            "G8": bool(real_price_share >= 0.90),
            "G9": bool(ver_share >= 0.50),
            "G10": True,   # enforced by construction in engine/originate.py
        }
        failed = [k for k, v in g.items() if not v]
        rows.append({
            "strategy": r.strategy, "decided_bets": r.decided, "roi": r.roi,
            "win_rate": r.win_rate, "breakeven_win_rate": r.breakeven_win_rate,
            "roi_ci_low": r.roi_ci_low, "roi_ci_high": r.roi_ci_high,
            "binom_p": r.binom_p_one_sided, "deflated_sharpe": r.deflated_sharpe,
            "luck_share": r.luck_share,
            "real_price_share": round(real_price_share, 4),
            "official_verified_share": round(ver_share, 4),
            **g,
            "gates_passed": len(GATES) - len(failed),
            "gates_total": len(GATES),
            "failed_gates": "; ".join(failed) if failed else "",
            "status": "VALIDATED" if not failed else "REJECTED",
        })
    res = pd.DataFrame(rows)
    gate_df = pd.DataFrame(
        [{"gate_id": i, "name": n, "requirement": d, "type": "hard"} for i, n, d in GATES]
    )
    return res, gate_df


def leaderboard(res: pd.DataFrame) -> pd.DataFrame:
    """Rank gate-passing strategies; list rejected ones with reasons."""
    out = res.copy()
    # Risk-adjusted score: ROI scaled by the width of its bootstrap interval.
    width = (out.roi_ci_high - out.roi_ci_low).replace(0, np.nan)
    out["risk_adjusted_score"] = (out.roi / width).round(5)
    out["reward_tier"] = np.where(out.status == "VALIDATED", "TBD", "None")
    valid = out[out.status == "VALIDATED"].sort_values("risk_adjusted_score", ascending=False)
    for i, idx in enumerate(valid.index):
        out.loc[idx, "reward_tier"] = "Tier 1" if i < 3 else ("Tier 2" if i < 7 else "Tier 3")
    out["rank"] = None
    for i, idx in enumerate(valid.index, start=1):
        out.loc[idx, "rank"] = i
    out = out.sort_values(["status", "roi"], ascending=[True, False])
    return out


def main() -> None:
    res, gate_df = evaluate()
    write_csv(gate_df, "validation_gates.csv")
    write_csv(res, "gate_results.csv")
    lb = leaderboard(res)
    write_csv(lb, "leaderboard_empirical.csv")

    print("=== VALIDATION GATES ===")
    print(res[["strategy", "decided_bets", "roi", "gates_passed", "gates_total",
               "failed_gates", "status"]].to_string(index=False))
    n_valid = int((res.status == "VALIDATED").sum())
    print(f"\nVALIDATED: {n_valid} of {len(res)} strategies")
    print("\n=== LEADERBOARD ===")
    print(lb[["rank", "strategy", "roi", "risk_adjusted_score", "reward_tier", "status"]].to_string(index=False))

    write_json("gates_summary.json", {
        "strategies_evaluated": int(len(res)),
        "validated": n_valid,
        "rejected": int(len(res) - n_valid),
        "hard_gates": len(GATES),
        "reward_tiers_paid": 0 if n_valid == 0 else None,
        "headline": (
            "No strategy cleared all hard gates. No reward tier is awarded and no "
            "profitable edge is claimed."
            if n_valid == 0 else
            f"{n_valid} strategies cleared all hard gates."
        ),
    })


if __name__ == "__main__":
    main()

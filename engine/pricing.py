"""Fair pricing of correlated combinations, and NFL key-number analysis.

Two deliverables that do not require inventing a sportsbook price:

1. FAIR COMBO PRICE. Given the empirically measured joint hit rate of two
   correlated legs, compute the fair decimal/American price and compare it to
   the price a book would post if it (incorrectly) multiplied the marginals.
   The gap is the maximum exploitable margin — and the reason correlated
   same-game legs are restricted or re-priced by operators.

2. KEY NUMBERS. The distribution of NFL margins and totals around 3 and 7.
   This is what makes a point of spread worth more at some numbers than others,
   and it is measured directly from final scores.

All probabilities are estimated walk-forward (prior seasons only) wherever they
are used to price a later season.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from common import OUT, write_csv, write_json


def prob_to_american(p: float) -> float:
    """Fair probability -> American odds (no vig)."""
    if p <= 0 or p >= 1:
        return float("nan")
    if p >= 0.5:
        return -100.0 * p / (1.0 - p)
    return 100.0 * (1.0 - p) / p


def combo_fair_prices() -> pd.DataFrame:
    """Fair price of each measured pair vs the naive independence price."""
    c = pd.read_csv(OUT / "correlations_empirical.csv")
    rows = []
    for r in c.itertuples():
        joint = r.observed_joint
        naive = r.naive_independent_joint
        if not np.isfinite(joint) or joint <= 0:
            continue
        fair_dec = 1.0 / joint
        naive_dec = 1.0 / naive if naive > 0 else float("nan")
        rows.append({
            "pair_id": r.pair_id, "label": r.label, "scope": r.scope, "n": r.n,
            "observed_joint": round(joint, 5),
            "fair_decimal": round(fair_dec, 4),
            "fair_american": round(prob_to_american(joint), 1),
            "naive_independent_joint": round(naive, 5),
            "naive_decimal": round(naive_dec, 4),
            "naive_american": round(prob_to_american(naive), 1),
            "mispricing_pct_of_stake": round((joint - naive) / naive * 100.0, 3) if naive > 0 else None,
            "phi_correlation": r.phi_correlation,
            "independence_rejected": r.independence_rejected,
            "source_url": r.source_url,
        })
    return pd.DataFrame(rows)


def walk_forward_combo_edge() -> pd.DataFrame:
    """Out-of-sample test of the correlated QB+WR1 combo.

    For each season we estimate the joint hit rate from PRIOR seasons only and
    compare it to the independence product also estimated from prior seasons.
    A book pricing at the naive product would be offering value; a book pricing
    at the true joint would not. We report the edge available against the naive
    price, and the break-even payout multiple required.
    """
    from strategies import load_player_weekly
    pw = load_player_weekly()
    if pw.empty:
        return pd.DataFrame()
    pw = pw.rename(columns={"Player": "player", "Pos": "pos", "Tm": "team"})
    pw["team"] = pw["team"].replace({"OAK": "LV", "SD": "LAC", "STL": "LAR", "WSH": "WAS"})
    pw = pw.sort_values(["player", "season", "week"])
    for col, new in [("PassingYds", "pass_line"), ("ReceivingYds", "rec_line")]:
        pw[new] = (pw.groupby(["player", "season"])[col]
                     .transform(lambda s: s.shift(1).expanding(min_periods=3).median()))
    pw["pass_over"] = (pw.PassingYds > pw.pass_line).astype(float).where(pw.pass_line.notna())
    pw["rec_over"] = (pw.ReceivingYds > pw.rec_line).astype(float).where(pw.rec_line.notna())
    qb = pw[(pw.pos == "QB") & pw.pass_over.notna()]
    wr = pw[(pw.pos == "WR") & pw.rec_over.notna()]
    top = wr.sort_values("rec_line", ascending=False).drop_duplicates(["season", "week", "team"])
    m = qb.merge(top, on=["season", "week", "team"], suffixes=("_qb", "_wr"))
    if m.empty:
        return pd.DataFrame()
    m["joint_hit"] = ((m.pass_over_qb == 1) & (m.rec_over_wr == 1)).astype(int)

    rows = []
    for season in sorted(m.season.unique()):
        tr = m[m.season < season]
        te = m[m.season == season]
        if len(tr) < 200 or len(te) < 30:
            continue
        j_tr = float(tr.joint_hit.mean())
        naive_tr = float((tr.pass_over_qb == 1).mean() * (tr.rec_over_wr == 1).mean())
        j_te = float(te.joint_hit.mean())
        # Value if the book paid the naive (independence) fair decimal price.
        naive_dec = 1.0 / naive_tr
        ev = j_te * (naive_dec - 1.0) - (1.0 - j_te)
        lo, hi = stats.beta.ppf([0.025, 0.975], te.joint_hit.sum() + 0.5,
                                len(te) - te.joint_hit.sum() + 0.5)
        rows.append({
            "season": int(season), "train_n": len(tr), "test_n": len(te),
            "train_joint_prior": round(j_tr, 5),
            "train_naive_prior": round(naive_tr, 5),
            "test_joint_actual": round(j_te, 5),
            "test_joint_ci_low": round(float(lo), 5),
            "test_joint_ci_high": round(float(hi), 5),
            "naive_decimal_offered": round(naive_dec, 4),
            "breakeven_decimal": round(1.0 / j_te, 4) if j_te > 0 else None,
            "ev_per_unit_vs_naive_price": round(float(ev), 5),
            "source_url": "https://www.nfl.com/stats/player-stats/",
        })
    return pd.DataFrame(rows)


def key_numbers() -> pd.DataFrame:
    """Distribution of final margins and totals — the basis of spread value."""
    p = pd.read_csv(OUT / "originated_lines.csv")
    p = p.dropna(subset=["result", "total"])
    n = len(p)
    abs_margin = p.result.abs()
    rows = []
    for k in range(0, 25):
        cnt = int((abs_margin == k).sum())
        rows.append({
            "metric": "absolute_final_margin", "value": k, "count": cnt,
            "frequency": round(cnt / n, 5), "n_games": n,
            "source_url": "https://www.nfl.com/scores/",
        })
    tot = p.total.astype(int)
    for k in [37, 41, 43, 44, 47, 51]:
        cnt = int((tot == k).sum())
        rows.append({
            "metric": "final_total", "value": k, "count": cnt,
            "frequency": round(cnt / n, 5), "n_games": n,
            "source_url": "https://www.nfl.com/scores/",
        })
    return pd.DataFrame(rows)


def push_and_vig_cost() -> dict:
    """How often pushes occur, and what the vig costs at observed prices."""
    p = pd.read_csv(OUT / "originated_lines.csv").dropna(subset=["spread_line", "total_line"])
    return {
        "games": int(len(p)),
        "spread_push_rate": round(float((p.home_cover_margin == 0).mean()), 5),
        "total_push_rate": round(float((p.total_margin == 0).mean()), 5),
        "pct_spreads_on_key_3_or_7": round(float(p.spread_line.abs().isin([3.0, 7.0]).mean()), 5),
        "mean_abs_spread": round(float(p.spread_line.abs().mean()), 4),
        "two_way_110_110_hold_pct": round((1 / 1.909090909) * 2 * 100 - 100, 4),
    }


def main() -> None:
    fair = combo_fair_prices()
    write_csv(fair, "combo_fair_prices.csv")
    wf = walk_forward_combo_edge()
    if not wf.empty:
        write_csv(wf, "combo_walk_forward.csv")
    kn = key_numbers()
    write_csv(kn, "key_numbers.csv")
    pv = push_and_vig_cost()
    write_json("market_structure.json", pv)

    print("=== FAIR COMBO PRICES (empirical joint vs naive independence) ===")
    print(fair[["pair_id", "label", "observed_joint", "fair_american",
                "naive_american", "mispricing_pct_of_stake", "independence_rejected"]].to_string(index=False))
    if not wf.empty:
        print("\n=== WALK-FORWARD CORRELATED COMBO (QB pass + WR1 rec) ===")
        print(wf.to_string(index=False))
        print(f"\nMean out-of-sample EV vs naive pricing: {wf.ev_per_unit_vs_naive_price.mean():.5f} per unit")
    print("\n=== KEY NUMBERS (top 8 absolute margins) ===")
    am = kn[kn.metric == "absolute_final_margin"].sort_values("frequency", ascending=False)
    print(am.head(8)[["value", "count", "frequency"]].to_string(index=False))
    print("\n=== MARKET STRUCTURE ===")
    for k, v in pv.items():
        print(f"  {k:32s} {v}")


if __name__ == "__main__":
    main()

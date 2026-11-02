"""Empirical correlation measurement for singles, parlays and prop combos.

Three questions actually matter when originating combination prices:

1. Are two legs from DIFFERENT games independent? (cross-game parlays)
2. How dependent are two legs inside the SAME game? (same-game parlays)
3. How dependent are two PLAYER props in the same game? (prop combos)

For each pair we report the marginal rates, the naive independence product, the
observed joint rate, the lift, and the phi coefficient (the Pearson correlation
of two binary variables). Phi is the correct correlation measure for binary
bet legs; a Pearson r on continuous stats is reported separately for props.

A block bootstrap over games gives a confidence interval, because games in the
same week are not fully independent.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from common import OUT, write_csv, write_json

RNG = np.random.default_rng(20261102)
N_BOOT = 4000


def phi_coefficient(a: np.ndarray, b: np.ndarray) -> float:
    """Correlation of two binary variables (2x2 phi)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def bootstrap_joint_ci(a: np.ndarray, b: np.ndarray, groups: np.ndarray,
                       n_boot: int = N_BOOT) -> tuple[float, float]:
    """Cluster bootstrap of P(A and B) resampling whole weeks."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    uniq = np.unique(groups)
    idx_by_g = {g: np.where(groups == g)[0] for g in uniq}
    vals = []
    for _ in range(n_boot):
        pick = RNG.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by_g[g] for g in pick])
        vals.append(float((a[idx] * b[idx]).mean()))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def pair_row(pair_id: str, label: str, a, b, groups, scope: str,
             source_url: str, note: str = "") -> dict:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n = len(a)
    pa, pb = float(a.mean()), float(b.mean())
    joint = float((a * b).mean())
    naive = pa * pb
    lo, hi = bootstrap_joint_ci(a, b, groups)
    return {
        "pair_id": pair_id, "label": label, "scope": scope, "n": n,
        "p_a": round(pa, 5), "p_b": round(pb, 5),
        "naive_independent_joint": round(naive, 5),
        "observed_joint": round(joint, 5),
        "joint_ci_low": round(lo, 5), "joint_ci_high": round(hi, 5),
        "lift_vs_independent": round(joint - naive, 5),
        "lift_ratio": round(joint / naive, 5) if naive > 0 else None,
        "phi_correlation": round(phi_coefficient(a, b), 5),
        "independence_rejected": bool(joint < lo or joint > hi) if False else
                                 bool(naive < lo or naive > hi),
        "source_url": source_url, "note": note,
    }


def game_correlations(p: pd.DataFrame) -> pd.DataFrame:
    d = p.dropna(subset=["spread_line", "total_line"]).copy()
    d = d[(d.home_cover_margin != 0) & (d.total_margin != 0)]
    d["fav_cover"] = np.where(d.spread_line > 0,
                              (d.home_cover_margin > 0).astype(int),
                              (d.home_cover_margin < 0).astype(int))
    d["dog_cover"] = 1 - d["fav_cover"]
    d["over"] = (d.total_margin > 0).astype(int)
    d["under"] = 1 - d["over"]
    d["home_win"] = (d.result > 0).astype(int)
    d["home_cover"] = (d.home_cover_margin > 0).astype(int)
    grp = (d.season.astype(str) + "_" + d.week.astype(str)).values
    src = "https://www.nfl.com/scores/"
    rows = [
        pair_row("X01", "Favorite covers & OVER", d.fav_cover, d.over, grp,
                 "same game", src, "Same-game parlay staple. Naive product misprices this."),
        pair_row("X02", "Favorite covers & UNDER", d.fav_cover, d.under, grp,
                 "same game", src, ""),
        pair_row("X03", "Underdog covers & OVER", d.dog_cover, d.over, grp,
                 "same game", src, ""),
        pair_row("X04", "Underdog covers & UNDER", d.dog_cover, d.under, grp,
                 "same game", src, ""),
        pair_row("X05", "Home wins & OVER", d.home_win, d.over, grp,
                 "same game", src, "Moneyline + total combo."),
        pair_row("X06", "Home covers & OVER", d.home_cover, d.over, grp,
                 "same game", src, ""),
    ]

    # Cross-game: pair each game with the next game in the same week (different game).
    d = d.sort_values(["season", "week", "game_id"])
    a_fav, b_fav, a_ov, b_ov, cg = [], [], [], [], []
    for (s, w), sub in d.groupby(["season", "week"]):
        v = sub.reset_index(drop=True)
        for i in range(len(v) - 1):
            a_fav.append(v.fav_cover[i]); b_fav.append(v.fav_cover[i + 1])
            a_ov.append(v.over[i]); b_ov.append(v.over[i + 1])
            cg.append(f"{s}_{w}")
    cg = np.array(cg)
    rows.append(pair_row("X07", "Favorite covers (game A) & favorite covers (game B)",
                         a_fav, b_fav, cg, "cross game", src,
                         "Different games, same week. Tests the independence assumption used for cross-game parlays."))
    rows.append(pair_row("X08", "OVER (game A) & OVER (game B)",
                         a_ov, b_ov, cg, "cross game", src,
                         "Weather/league-wide scoring environment can induce weak dependence."))
    return pd.DataFrame(rows)


def prop_correlations() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Player-prop dependence inside the same game.

    Prop LINES are not officially published, so we originate a line per player
    as that player's trailing season-to-date median (minimum 3 prior games),
    then ask whether the player cleared it. This makes the binary "prop hits"
    event well defined without inventing a sportsbook price.
    """
    from strategies import load_player_weekly
    pw = load_player_weekly()
    if pw.empty:
        return pd.DataFrame(), pd.DataFrame()
    pw = pw.rename(columns={"Player": "player", "Pos": "pos", "Tm": "team"})
    pw["team"] = pw["team"].replace({"OAK": "LV", "SD": "LAC", "STL": "LAR", "WSH": "WAS"})
    pw = pw.sort_values(["player", "season", "week"])

    # Trailing median, strictly prior games only (no lookahead).
    for col, new in [("PassingYds", "pass_line"), ("ReceivingYds", "rec_line"),
                     ("RushingYds", "rush_line")]:
        pw[new] = (pw.groupby(["player", "season"])[col]
                     .transform(lambda s: s.shift(1).expanding(min_periods=3).median()))
        pw[new + "_n"] = (pw.groupby(["player", "season"])[col]
                            .transform(lambda s: s.shift(1).expanding(min_periods=3).count()))

    pw["pass_over"] = (pw.PassingYds > pw.pass_line).astype(float).where(pw.pass_line.notna())
    pw["rec_over"] = (pw.ReceivingYds > pw.rec_line).astype(float).where(pw.rec_line.notna())
    pw["rush_over"] = (pw.RushingYds > pw.rush_line).astype(float).where(pw.rush_line.notna())

    src = "https://www.nfl.com/stats/player-stats/"
    rows, cont_rows = [], []
    grp_key = (pw.season.astype(str) + "_" + pw.week.astype(str))

    # QB passing & same-team RB rushing (typically negatively correlated).
    qb = pw[(pw.pos == "QB") & pw.pass_over.notna()]
    rb = pw[(pw.pos == "RB") & pw.rush_over.notna()]
    m = qb.merge(rb, on=["season", "week", "team"], suffixes=("_qb", "_rb"))
    if len(m) > 50:
        rows.append(pair_row("PP01", "QB passing over & same-team RB rushing over",
                             m.pass_over_qb, m.rush_over_rb,
                             (m.season.astype(str) + "_" + m.week.astype(str)).values,
                             "same game, same team", src,
                             "Game-script substitution: passing and rushing volume compete."))
        cont_rows.append({
            "pair_id": "PC01", "label": "QB passing yards vs same-team RB rushing yards",
            "n": len(m), "pearson_r": round(float(m.PassingYds_qb.corr(m.RushingYds_rb)), 5),
            "spearman_r": round(float(m.PassingYds_qb.corr(m.RushingYds_rb, method="spearman")), 5),
            "source_url": src,
        })

    # QB passing & same-team top WR receiving (positively correlated).
    wr = pw[(pw.pos == "WR") & pw.rec_over.notna()]
    top = (wr.sort_values("rec_line", ascending=False)
             .drop_duplicates(["season", "week", "team"]))
    m2 = qb.merge(top, on=["season", "week", "team"], suffixes=("_qb", "_wr"))
    if len(m2) > 50:
        rows.append(pair_row("PP02", "QB passing over & same-team WR1 receiving over",
                             m2.pass_over_qb, m2.rec_over_wr,
                             (m2.season.astype(str) + "_" + m2.week.astype(str)).values,
                             "same game, same team", src,
                             "Shared cause: the same completions drive both legs."))
        cont_rows.append({
            "pair_id": "PC02", "label": "QB passing yards vs same-team WR1 receiving yards",
            "n": len(m2), "pearson_r": round(float(m2.PassingYds_qb.corr(m2.ReceivingYds_wr)), 5),
            "spearman_r": round(float(m2.PassingYds_qb.corr(m2.ReceivingYds_wr, method="spearman")), 5),
            "source_url": src,
        })

    # WR1 & WR2 same team (competition for targets).
    wr2 = (wr.sort_values("rec_line", ascending=False)
             .groupby(["season", "week", "team"]).nth([0, 1]).reset_index())
    pairs = []
    for (s, w, t), sub in wr2.groupby(["season", "week", "team"]):
        if len(sub) == 2:
            pairs.append({
                "season": s, "week": w, "team": t,
                "a": sub.rec_over.iloc[0], "b": sub.rec_over.iloc[1],
                "ya": sub.ReceivingYds.iloc[0], "yb": sub.ReceivingYds.iloc[1],
            })
    if len(pairs) > 50:
        pp = pd.DataFrame(pairs)
        rows.append(pair_row("PP03", "WR1 receiving over & WR2 receiving over (same team)",
                             pp.a, pp.b,
                             (pp.season.astype(str) + "_" + pp.week.astype(str)).values,
                             "same game, same team", src,
                             "Target competition between two receivers on the same offense."))
        cont_rows.append({
            "pair_id": "PC03", "label": "WR1 vs WR2 receiving yards (same team)",
            "n": len(pp), "pearson_r": round(float(pp.ya.corr(pp.yb)), 5),
            "spearman_r": round(float(pp.ya.corr(pp.yb, method="spearman")), 5),
            "source_url": src,
        })

    # Cross-game player props: same position, different team, same week.
    q = qb.sort_values(["season", "week", "team"]).reset_index(drop=True)
    ax, bx, gg = [], [], []
    for (s, w), sub in q.groupby(["season", "week"]):
        v = sub.reset_index(drop=True)
        for i in range(len(v) - 1):
            if v.team[i] == v.team[i + 1]:
                continue
            ax.append(v.pass_over[i]); bx.append(v.pass_over[i + 1]); gg.append(f"{s}_{w}")
    if len(ax) > 50:
        rows.append(pair_row("PP04", "QB passing over (team A) & QB passing over (team B)",
                             ax, bx, np.array(gg), "cross game", src,
                             "Different games. Baseline for cross-game prop parlays."))

    return pd.DataFrame(rows), pd.DataFrame(cont_rows)


def main() -> None:
    p = pd.read_csv(OUT / "originated_lines.csv")
    gc = game_correlations(p)
    pc, cc = prop_correlations()
    allc = pd.concat([gc, pc], ignore_index=True)
    write_csv(allc, "correlations_empirical.csv")
    if not cc.empty:
        write_csv(cc, "prop_continuous_correlations.csv")
    print("=== BINARY LEG CORRELATIONS (bootstrap CI, cluster by week) ===")
    cols = ["pair_id", "label", "n", "naive_independent_joint", "observed_joint",
            "lift_vs_independent", "phi_correlation", "independence_rejected"]
    print(allc[cols].to_string(index=False))
    if not cc.empty:
        print("\n=== CONTINUOUS PROP CORRELATIONS ===")
        print(cc.to_string(index=False))
    write_json("correlation_summary.json", {
        "pairs_measured": int(len(allc)),
        "bootstrap_replicates": N_BOOT,
        "seed": 20261102,
        "same_game_pairs_rejecting_independence": int(
            allc[(allc.scope.str.startswith("same")) & allc.independence_rejected].shape[0]),
        "cross_game_pairs_rejecting_independence": int(
            allc[(allc.scope == "cross game") & allc.independence_rejected].shape[0]),
    })


if __name__ == "__main__":
    main()

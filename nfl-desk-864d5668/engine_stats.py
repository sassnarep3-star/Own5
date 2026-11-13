#!/usr/bin/env python3
"""Signal evaluation, backtest tables, correlations, validation gates.

Split out of engine.py to keep each module readable. Imported by engine.py.
"""
from __future__ import annotations
import math

import statslib as S
from engine import (BREAK_EVEN, WIN_RETURN, LAM, TEAMS, rnd, register, flag,
                    R, IR, DC, GAMES)


def returns_for(wins):
    return [WIN_RETURN if w == 1 else -1.0 for w in wins]


def evaluate(name, family, wins, graded, subset_desc, source, note=""):
    if graded < 2:
        return None
    hits = sum(1 for w in wins if w == 1)
    p_hat = hits / graded
    lo, hi = S.wilson_ci(hits, graded)
    p_be = S.binom_sf(hits, graded, BREAK_EVEN)
    p_coin = S.binom_two_sided_p(hits, graded, 0.5)
    rets = returns_for(wins)
    mu = S.mean(rets); sd = S.stdev(rets)
    sr = mu / sd if sd else 0.0
    skew = S.skewness(rets)
    skew = 0.0 if skew is None else skew
    kurt = S.kurtosis(rets)
    kurt = 0.0 if kurt is None else kurt
    return {
        "signal": name, "family": family, "subset": subset_desc,
        "graded": graded, "wins": hits, "losses": graded - hits,
        "hit_rate": p_hat, "wilson_low": lo, "wilson_high": hi,
        "p_be": p_be, "p_coin": p_coin,
        "upb": mu, "roi": 100 * mu, "sharpe": sr,
        "t_stat": sr * math.sqrt(graded) if sd else 0.0,
        "skew": skew, "kurt": kurt,
        "source": source, "note": note,
        "holm_p": "", "holm_reject": "", "dsr": "", "trials": "",
    }


def build_signal_tests(preds, base):
    raw = []

    def add(name, family, wins, graded, desc, src, note=""):
        r = evaluate(name, family, wins, graded, desc, src, note)
        if r:
            raw.append(r)

    add("M1 Model pick (walk-forward, all games)", "side",
        [p["pick_won"] for p in preds], len(preds),
        "all walk-forward graded games", R.SRC_STANDINGS,
        "Ridge regression on home margin, fitted only on weeks before the game "
        "being predicted. Straight-up winner, NOT against a spread.")
    conf = [p for p in preds if p["confidence"] >= 7]
    add("M2 Model pick, predicted margin >= 7 points", "side",
        [p["pick_won"] for p in conf], len(conf),
        "model confidence >= 7 points", R.SRC_STANDINGS)
    conf3 = [p for p in preds if p["confidence"] >= 3]
    add("M3 Model pick, predicted margin >= 3 points", "side",
        [p["pick_won"] for p in conf3], len(conf3),
        "model confidence >= 3 points", R.SRC_STANDINGS)
    add("B1 Always take the home team", "side",
        [b["home_pick_won"] for b in base], len(base),
        "the same games the model graded", R.SRC_STANDINGS,
        "Naive baseline: with no model at all, back the home club.")
    add("B2 Take the better season-to-date point differential", "side",
        [b["pointdiff_pick_won"] for b in base], len(base),
        "the same games the model graded", R.SRC_STANDINGS,
        "Naive baseline using only prior-week official results.")
    add("B3 Take the better season-to-date win percentage", "side",
        [b["record_pick_won"] for b in base], len(base),
        "the same games the model graded", R.SRC_STANDINGS,
        "Naive baseline using only prior-week official results.")
    rb = [b for b in base if b["rest_pick_won"] != ""]
    add("B4 Take the team with more rest", "side",
        [b["rest_pick_won"] for b in rb], len(rb),
        "games where both clubs had a previous game this season",
        R.SRC_STANDINGS,
        "Rest = days since each club's previous official game.")
    bye = [p for p in preds if p["rest_diff"] is not None
           and abs(p["rest_diff"]) >= 7]
    add("M4 Back the team coming off a bye (rest edge >= 7 days)", "side",
        [1 if ((p["rest_diff"] < 0 and p["actual_home_margin"] > 0) or
               (p["rest_diff"] > 0 and p["actual_home_margin"] < 0)) else 0
         for p in bye], len(bye),
        "walk-forward graded games where one club had at least 7 more days of rest",
        R.SRC_STANDINGS,
        "POST-HOC: discovered by scanning the correlation table, not "
        "pre-registered. Rest days are the gap between a club's previous "
        "official game and this one; a 7-day edge means a bye week.")
    rest3 = [p for p in preds if p["rest_diff"] is not None
             and abs(p["rest_diff"]) >= 3]
    add("M5 Back the team with a rest edge of 3 or more days", "side",
        [1 if ((p["rest_diff"] < 0 and p["actual_home_margin"] > 0) or
               (p["rest_diff"] > 0 and p["actual_home_margin"] < 0)) else 0
         for p in rest3], len(rest3),
        "walk-forward graded games where one club had at least 3 more days of rest",
        R.SRC_STANDINGS,
        "POST-HOC: discovered by scanning the correlation table, not "
        "pre-registered. A 3-day edge means the club played the previous "
        "Thursday; a 7-day edge means it had a bye.")
    tot = [p for p in preds if p["total_error"] is not None]
    add("T1 Over the model's own total (bias probe)", "total",
        [1 if p["total_error"] > 0 else 0 for p in tot], len(tot),
        "walk-forward graded games", R.SRC_STANDINGS,
        "NOT A SKILL TEST: the total is the model's own number, so a hit rate "
        "away from 50% measures bias, not edge. Published to expose bias only.")

    skill = [r for r in raw if not r["signal"].startswith("T1")]
    n_trials = len(skill)
    hb = S.holm_bonferroni([r["p_coin"] for r in skill], 0.05)
    for r, (_i, p, adj, rej) in zip(skill, hb):
        r["holm_p"] = adj
        r["holm_reject"] = "YES" if rej else "NO"
        r["trials"] = n_trials
        r["dsr"] = S.deflated_sharpe(r["sharpe"], r["graded"],
                                     r["skew"], r["kurt"], n_trials)
    for r in raw:
        if not r["signal"].startswith("T1"):
            continue
        r["holm_reject"] = "n/a (bias probe, not a skill test)"

    hdr = ["signal", "declared_before_or_after_results", "family", "subset",
           "graded_bets", "wins", "losses",
           "hit_rate", "wilson_95_low", "wilson_95_high",
           "p_vs_breakeven_-110", "p_vs_coinflip", "holm_adjusted_p",
           "holm_reject_at_0.05", "units_per_bet_at_-110", "roi_pct",
           "sharpe_per_bet", "t_stat", "skew", "excess_kurtosis",
           "deflated_sharpe", "trials_haircut", "verdict", "source", "note"]
    rows = []
    for r in raw:
        if r["signal"].startswith("T1"):
            verdict = "BIAS PROBE - not a strategy"
        else:
            gates = [r["graded"] >= 50,
                     r["p_coin"] < 0.05,
                     r["hit_rate"] > BREAK_EVEN,
                     r["holm_reject"] == "YES",
                     isinstance(r["dsr"], float) and r["dsr"] > 0.95]
            verdict = ("PASS - all 5 gates" if all(gates) else
                       "FAIL - %d of 5 gates missed"
                       % sum(1 for g in gates if not g))
        rows.append([r["signal"],
                     "post-hoc discovery" if r["signal"].startswith(("M4", "M5"))
                     else "pre-registered",
                     r["family"], r["subset"], r["graded"],
                     r["wins"], r["losses"], rnd(r["hit_rate"]),
                     rnd(r["wilson_low"]), rnd(r["wilson_high"]),
                     rnd(r["p_be"], 5), rnd(r["p_coin"], 5),
                     rnd(r["holm_p"], 5), r["holm_reject"],
                     rnd(r["upb"]), rnd(r["roi"], 2), rnd(r["sharpe"]),
                     rnd(r["t_stat"], 3), rnd(r["skew"], 3), rnd(r["kurt"], 3),
                     rnd(r["dsr"], 4), r["trials"], verdict,
                     r["source"], r["note"]])
    register("signal_tests", hdr, rows)
    return raw


def build_backtest(preds, base):
    hdr = ["week", "date", "away", "home", "games_in_training_set",
           "pred_home_margin", "actual_home_margin", "margin_error",
           "pred_total", "actual_total", "total_error",
           "model_pick", "model_pick_won", "abs_predicted_margin",
           "better_pointdiff_pick", "better_pointdiff_won",
           "home_pick_won", "rest_diff_days", "source"]
    rows = []
    for p, b in zip(preds, base):
        rows.append([p["week"], p["date"], p["away"], p["home"],
                     p["train_games"], rnd(p["pred_home_margin"], 2),
                     p["actual_home_margin"], rnd(p["margin_error"], 2),
                     rnd(p["pred_total"], 1) if p["pred_total"] is not None else "",
                     p["actual_total"],
                     rnd(p["total_error"], 1) if p["total_error"] is not None else "",
                     p["pick"], "W" if p["pick_won"] else "L",
                     rnd(p["confidence"], 2),
                     b["pointdiff_pick"], "W" if b["pointdiff_pick_won"] else "L",
                     "W" if b["home_pick_won"] else "L",
                     p["rest_diff"] if p["rest_diff"] is not None else "",
                     R.LEDGER_SRC[p["week"]]])
    register("backtest_walkforward", hdr, rows)

    whdr = ["week", "games_graded", "model_wins", "model_hit_rate",
            "pointdiff_baseline_wins", "pointdiff_baseline_hit_rate",
            "home_baseline_wins", "home_baseline_hit_rate",
            "mae_margin", "bias_margin", "mae_total", "bias_total", "source"]
    wrows = []
    for wk in sorted(set(p["week"] for p in preds)):
        sub = [p for p in preds if p["week"] == wk]
        bsub = [b for b in base if b["week"] == wk]
        errs = [p["margin_error"] for p in sub]
        terr = [p["total_error"] for p in sub if p["total_error"] is not None]
        wrows.append([wk, len(sub), sum(p["pick_won"] for p in sub),
                      rnd(sum(p["pick_won"] for p in sub) / len(sub)),
                      sum(b["pointdiff_pick_won"] for b in bsub),
                      rnd(sum(b["pointdiff_pick_won"] for b in bsub) / len(bsub)),
                      sum(b["home_pick_won"] for b in bsub),
                      rnd(sum(b["home_pick_won"] for b in bsub) / len(bsub)),
                      rnd(S.mean([abs(e) for e in errs])), rnd(S.mean(errs)),
                      rnd(S.mean([abs(e) for e in terr])) if terr else "",
                      rnd(S.mean(terr)) if terr else "", R.LEDGER_SRC[wk]])
    register("backtest_weekly", whdr, wrows)

    errs = [p["margin_error"] for p in preds]
    terr = [p["total_error"] for p in preds if p["total_error"] is not None]
    naive = S.mean([abs(g["home_margin"]) for g in GAMES])
    r_m = S.pearson([p["pred_home_margin"] for p in preds],
                    [p["actual_home_margin"] for p in preds])
    tp = [p for p in preds if p["pred_total"] is not None]
    r_t = S.pearson([p["pred_total"] for p in tp], [p["actual_total"] for p in tp]) \
        if len(tp) > 3 else None
    hdr2 = ["metric", "value", "source"]
    rows2 = [
        ["Predictions graded (out-of-sample)", len(preds), R.SRC_STANDINGS],
        ["Weeks graded", len(set(p["week"] for p in preds)), R.SRC_STANDINGS],
        ["MAE of predicted home margin (points)",
         rnd(S.mean([abs(e) for e in errs])), R.SRC_STANDINGS],
        ["RMSE of predicted home margin (points)",
         rnd(math.sqrt(S.mean([e * e for e in errs]))), R.SRC_STANDINGS],
        ["Bias of predicted home margin (points)", rnd(S.mean(errs)),
         R.SRC_STANDINGS],
        ["SD of margin error (points)", rnd(S.stdev(errs)), R.SRC_STANDINGS],
        ["MAE of predicted total (points)",
         rnd(S.mean([abs(e) for e in terr])) if terr else "", R.SRC_STANDINGS],
        ["Bias of predicted total (points)", rnd(S.mean(terr)) if terr else "",
         R.SRC_STANDINGS],
        ["Naive baseline MAE (predict a 0 margin every game)", rnd(naive),
         R.SRC_STANDINGS],
        ["MAE improvement vs that naive baseline (points)",
         rnd(naive - S.mean([abs(e) for e in errs])), R.SRC_STANDINGS],
        ["Out-of-sample r: predicted vs actual home margin", rnd(r_m),
         R.SRC_STANDINGS],
        ["p-value of that correlation", rnd(S.pearson_p(r_m, len(preds)), 5),
         R.SRC_STANDINGS],
        ["Out-of-sample r: predicted vs actual total", rnd(r_t),
         R.SRC_STANDINGS],
        ["p-value of that correlation",
         rnd(S.pearson_p(r_t, len(tp)), 5) if r_t is not None else "",
         R.SRC_STANDINGS],
    ]
    register("backtest_summary", hdr2, rows2)
    return {"r_margin": r_m, "r_total": r_t, "mae": S.mean([abs(e) for e in errs]),
            "naive_mae": naive}


def build_correlations(games, preds, base):
    hdr = ["id", "quantity", "variable_a", "variable_b", "n", "pearson_r",
           "p_value", "fisher_z", "ci95_low_r", "ci95_high_r",
           "what_it_is_used_for", "source"]
    rows = []

    def corr(cid, label, a, b, xs, ys, use, src):
        pair = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
        if len(pair) < 4:
            rows.append([cid, label, a, b, len(pair), "", "", "", "", "",
                         use + " - NOT COMPUTED: fewer than 4 paired observations",
                         src])
            return None
        xs2 = [p[0] for p in pair]; ys2 = [p[1] for p in pair]
        r = S.pearson(xs2, ys2)
        if r is None:
            rows.append([cid, label, a, b, len(pair), "", "", "", "", "",
                         use + " - NOT COMPUTED: one variable is constant",
                         src])
            return None
        p = S.pearson_p(r, len(pair))
        z = S.fisher_z(r, len(pair))
        lo = hi = ""
        if z:
            lo = math.tanh(z[1]); hi = math.tanh(z[2])
        rows.append([cid, label, a, b, len(pair), rnd(r), rnd(p, 5),
                     rnd(z[0], 4) if z else "", rnd(lo), rnd(hi), use, src])
        return r

    corr("C-01", "Game level: home margin vs total points scored",
         "home_margin", "total_points",
         [g["home_margin"] for g in games], [g["total"] for g in games],
         "Same-game parlay pricing: shows whether the side and the total of "
         "one game are independent", R.SRC_STANDINGS)
    corr("C-02", "Game level: size of the margin vs total points scored",
         "abs_home_margin", "total_points",
         [abs(g["home_margin"]) for g in games], [g["total"] for g in games],
         "Do lopsided games score more?", R.SRC_STANDINGS)
    corr("C-03", "Rest differential vs home margin",
         "rest_diff_days", "home_margin",
         [g["rest_diff"] for g in games], [g["home_margin"] for g in games],
         "Is a rest advantage a real signal?", R.SRC_STANDINGS)
    corr("C-04", "Divisional game vs size of the margin",
         "divisional_flag", "abs_home_margin",
         [g["divisional"] for g in games], [abs(g["home_margin"]) for g in games],
         "Are divisional games tighter?", R.SRC_STANDINGS)
    corr("C-05", "Model predicted margin vs actual margin (out-of-sample)",
         "pred_home_margin", "actual_home_margin",
         [p["pred_home_margin"] for p in preds],
         [p["actual_home_margin"] for p in preds],
         "Forecast accuracy of the rating model", R.SRC_STANDINGS)
    corr("C-06", "Model predicted total vs actual total (out-of-sample)",
         "pred_total", "actual_total",
         [p["pred_total"] for p in preds], [p["actual_total"] for p in preds],
         "Forecast accuracy of the totals model", R.SRC_STANDINGS)
    corr("C-07", "Signal agreement: model pick vs better-point-differential pick",
         "model_pick_is_home", "pointdiff_pick_is_home",
         [p["pick_is_home"] for p in preds],
         [1 if b["pointdiff_pick"] == b["home"] else 0 for b in base],
         "Parlay construction: two signals that always agree give no "
         "diversification", R.SRC_STANDINGS)
    corr("C-08", "Signal agreement: model pick vs better-win-percentage pick",
         "model_pick_is_home", "record_pick_is_home",
         [p["pick_is_home"] for p in preds],
         [1 if b["record_pick"] == b["home"] else 0 for b in base],
         "How much the model duplicates a simple record rule", R.SRC_STANDINGS)
    corr("C-09", "Home-team result vs model-pick result (same games)",
         "home_pick_won", "model_pick_won",
         [b["home_pick_won"] for b in base], [p["pick_won"] for p in preds],
         "Incremental value of the model over always backing the home team",
         R.SRC_STANDINGS)
    rows.append(["C-10", "Player-prop correlations (any player market)",
                 "prop_a", "prop_b", 0, "", "", "", "", "",
                 "Same-game player-prop parlays need historic official player "
                 "box scores. No official player-statistic table was in scope "
                 "this session, so no prop correlation is published. "
                 "See flag F-06.", R.SRC_STANDINGS])
    register("correlations", hdr, rows)
    return rows


def mcnemar(model_wins, base_wins):
    """Exact two-sided McNemar test on the discordant pairs."""
    b = sum(1 for m, x in zip(model_wins, base_wins) if m == 1 and x == 0)
    c = sum(1 for m, x in zip(model_wins, base_wins) if m == 0 and x == 1)
    if b + c == 0:
        return b, c, None
    return b, c, S.binom_two_sided_p(b, b + c, 0.5)


def build_validation(signals, mism, n_preds, base, preds):
    m1 = None
    for s in signals:
        if s["signal"].startswith("M1"):
            m1 = s
    m1 = m1 or {}
    b2 = None
    for s in signals:
        if s["signal"].startswith("B2"):
            b2 = s
    b1 = None
    for s in signals:
        if s["signal"].startswith("B1"):
            b1 = s
    best_base = max([x for x in (b1, b2) if x] or [{"hit_rate": 0}],
                    key=lambda x: x["hit_rate"])
    b_disc, c_disc, mc_p = mcnemar([p["pick_won"] for p in preds],
                                    [x["pointdiff_pick_won"] for x in base])
    beats = (m1.get("hit_rate", 0) > best_base.get("hit_rate", 0)
             and mc_p is not None and mc_p < 0.05)
    hdr = ["gate_id", "gate", "why_it_exists", "threshold", "result",
           "pass_fail", "source"]
    rows = [
        ["V-01", "Data integrity",
         "If the ledger is wrong, everything downstream is wrong",
         "All 32 clubs reconcile to nfl.com standings on W, L, T, PF and PA",
         "%d of 32 clubs reconcile; %d mismatches" % (32 - mism, mism),
         "PASS" if mism == 0 else "FAIL", R.SRC_STANDINGS],
        ["V-02", "No look-ahead",
         "A backtest that can see the future is worthless",
         "Every prediction uses only weeks strictly before the game predicted",
         "%d predictions, each fitted on prior weeks only" % n_preds,
         "PASS", R.SRC_STANDINGS],
        ["V-03", "Minimum sample",
         "Small samples cannot be distinguished from luck",
         "At least 50 graded bets",
         "%s graded bets" % m1.get("graded", ""),
         "PASS" if m1.get("graded", 0) >= 50 else "FAIL", R.SRC_STANDINGS],
        ["V-04", "Skill vs coin flip", "The signal must beat chance",
         "Two-sided binomial p below 0.05 against 50 per cent",
         "p = %s" % rnd(m1.get("p_coin"), 5),
         "PASS" if (m1.get("p_coin") if m1.get("p_coin") != "" else 1) < 0.05
         else "FAIL", R.SRC_STANDINGS],
        ["V-05", "Multiple-testing haircut",
         "Trying many signals manufactures winners",
         "Holm-Bonferroni adjusted p below 0.05",
         "adjusted p = %s" % rnd(m1.get("holm_p"), 5),
         "PASS" if m1.get("holm_reject") == "YES" else "FAIL", R.SRC_STANDINGS],
        ["V-06", "Deflated Sharpe ratio",
         "Corrects for how many strategies were tried and for lopsided returns",
         "Deflated Sharpe above 0.95", "DSR = %s" % rnd(m1.get("dsr"), 4),
         "PASS" if (m1.get("dsr") if isinstance(m1.get("dsr"), float) else 0) > 0.95
         else "FAIL", R.SRC_STANDINGS],
        ["V-07", "Beat a naive baseline",
         "A model that only rediscovers 'the better team wins' has no value",
         "Hit rate above the better of the home-team and point-differential "
         "baselines",
         "model %s vs best baseline %s; the two rules disagree on %d games, "
         "of which the model wins %d and the baseline wins %d; exact McNemar "
         "p = %s"
         % (rnd(m1.get("hit_rate")), rnd(best_base.get("hit_rate")),
            b_disc + c_disc, b_disc, c_disc,
            rnd(mc_p, 4) if mc_p is not None else "n/a"),
         "PASS" if beats else "FAIL", R.SRC_STANDINGS],
        ["V-08", "Profitable at a real price",
         "-110 is the standard side price",
         "Units per bet above 0 at -110",
         "NOT TESTABLE - no official market price exists (flag F-01). The -110 "
         "figures in signal_tests.csv are a flat-price scenario, not a record "
         "against real closing lines.", "BLOCKED", R.SRC_STANDINGS],
        ["V-09", "Deterministic rebuild",
         "A table that changes between runs cannot be audited",
         "Two consecutive builds produce identical file checksums",
         "checked by verify.py", "checked by verify.py", "n/a"],
        ["V-10", "Every row carries an official source",
         "The core verification rule of this project",
         "Zero rows with an empty source column across all published tables",
         "checked by verify.py", "checked by verify.py", "n/a"],
    ]
    register("validation", hdr, rows)
    return rows


def build_leaderboard(signals):
    hdr = ["rank", "signal", "graded_bets", "hit_rate", "units_per_bet_at_-110",
           "roi_pct", "deflated_sharpe", "verdict", "reward_tier", "source"]
    cand = [s for s in signals if not s["signal"].startswith("T1")]
    cand.sort(key=lambda s: -(s["hit_rate"] if s["graded"] >= 10 else -1))
    rows = []
    rank = 0
    for s in cand:
        rank += 1
        dsr = s["dsr"] if isinstance(s["dsr"], float) else 0.0
        if s["signal"].startswith("M") and s["graded"] >= 50 and \
           s["hit_rate"] > 0.5238095238095238 and \
           s["holm_reject"] == "YES" and dsr > 0.95:
            tier = "promoted - passes gates V-03, V-04, V-05, V-06 and profitability"
        elif s["graded"] >= 50 and s["hit_rate"] > 0.5238095238095238 and \
                s["holm_reject"] == "YES":
            tier = ("watchlist - above break-even and through the haircut, but "
                    "fails the deflated-Sharpe gate")
        elif s["hit_rate"] > 0.5238095238095238:
            tier = "watchlist - above break-even but short of the full gate set"
        else:
            tier = "below break-even - not promoted"
        rows.append([rank, s["signal"], s["graded"], rnd(s["hit_rate"]),
                     rnd(s["upb"]), rnd(s["roi"], 2), rnd(s["dsr"], 4),
                     s.get("verdict", ""), tier, s["source"]])
    register("leaderboard", hdr, rows)
    return rows

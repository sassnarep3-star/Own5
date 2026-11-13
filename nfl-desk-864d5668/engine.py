#!/usr/bin/env python3
"""Own5 NFL Own-Line Lab - compute engine (session 864d5668).

Deterministic and dependency-free (pure standard library). Reads the pinned
official inputs in raw_inputs.py / injuries_raw.py / depthcharts_raw.py and
writes every derived table to data/.

Discipline: nothing is inferred. Any quantity that cannot be computed from an
official input is emitted as an EMPTY cell and is accompanied by a row in
flags.csv. Market prices (spreads, totals, moneylines) are NOT published by any
official NFL source, so every market column is blank + flagged.
"""
from __future__ import annotations
import csv
import datetime as dt
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import raw_inputs as R
import injuries_raw as IR
import depthcharts_raw as DC
import statslib as S

OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

BREAK_EVEN = 0.5238095238095238      # -110 American
WIN_RETURN = 100.0 / 110.0           # units won per 1 unit risked at -110
LAM = 5.0                            # ridge penalty on team ratings
TEAMS = sorted(R.TEAMS.keys())
IDX = {t: i for i, t in enumerate(TEAMS)}
RIDGE_GRID = (1.0, 3.0, 5.0, 10.0, 20.0)

TABLES = {}   # name -> (header, rows)
FLAGS = []
GAMES = []


def rnd(x, n=4):
    if x is None or x == "":
        return ""
    return round(x, n) if isinstance(x, float) else x


def flag(fid, area, severity, what, why, source):
    FLAGS.append({"flag_id": fid, "area": area, "severity": severity,
                  "issue": what, "why_it_matters": why, "source_or_action": source})


def register(name, header, rows):
    TABLES[name] = (header, rows)
    return rows


# ---------------------------------------------------------------------------
# 0. source registry
# ---------------------------------------------------------------------------
def build_sources():
    hdr = ["source_id", "publisher", "title", "url", "fetched",
           "used_for", "verification_status"]
    rows = [
        ["S-01", "NFL.com", "2026 NFL Standings (all games through Week 10 TNF)",
         R.SRC_STANDINGS, R.FETCH_DATE,
         "Official W-L-T, PF, PA for all 32 teams; reconciliation benchmark",
         "verified - read directly"],
        ["S-12", "NFL.com", "Official NFL Week 10 Injury Report (2026, Reg 10)",
         IR.SRC_INJURY, R.FETCH_DATE,
         "Practice status and issued game status for every listed player",
         "verified - 326 rows transcribed"],
        ["S-13", "NFL Football Operations", "2026 NFL Rulebook",
         "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
         R.FETCH_DATE, "Rules that create scoring and strategy effects",
         "NOT FETCHED - see flag F-13"],
    ]
    for wk in sorted(R.LEDGER_SRC):
        rows.append(["S-W%02d" % wk, "NFL.com",
                     "2026 NFL Schedule - Week %d" % wk, R.LEDGER_SRC[wk],
                     R.FETCH_DATE,
                     "Week %d game dates, matchups and final scores" % wk,
                     "verified - transcribed"])
    for tm in TEAMS:
        meta = DC.DC_META.get(tm)
        if meta is None:
            rows.append(["S-DC-" + tm, R.TEAMS[tm][0],
                         R.TEAMS[tm][0] + " official depth chart",
                         DC.HOU_DC_URL, R.FETCH_DATE,
                         tm + " published depth order by position",
                         "NOT AVAILABLE - the page publishes the chart as an "
                         "image only (flag F-09)"])
            continue
        url, stamp = meta
        rows.append(["S-DC-" + tm, R.TEAMS[tm][0],
                     R.TEAMS[tm][0] + " official depth chart"
                     + (" (" + stamp + ")" if stamp else ""), url,
                     R.FETCH_DATE, tm + " published depth order by position",
                     "verified - transcribed"])
    return register("sources", hdr, rows)


# ---------------------------------------------------------------------------
# 1. ledger
# ---------------------------------------------------------------------------
def build_ledger():
    hdr = ["week", "date", "away", "home", "away_pts", "home_pts",
           "home_margin", "total_pts", "neutral_site", "site_note",
           "divisional_game", "rest_days_away", "rest_days_home", "rest_diff",
           "status", "source"]
    prev = {}
    rows = []
    for wk, a, h, ap, hp, date, neutral in sorted(R.LEDGER,
                                                  key=lambda g: (g[5], g[0])):
        d = dt.date.fromisoformat(date)
        ra = (d - prev[a]).days if a in prev else ""
        rh = (d - prev[h]).days if h in prev else ""
        prev[a] = d
        prev[h] = d
        div = "yes" if (R.TEAMS[a][1] == R.TEAMS[h][1] and
                        R.TEAMS[a][2] == R.TEAMS[h][2]) else "no"
        played = ap is not None and hp is not None
        rows.append([wk, date, a, h,
                     ap if played else "", hp if played else "",
                     (hp - ap) if played else "", (hp + ap) if played else "",
                     "yes" if neutral else "no", neutral or "",
                     div, ra, rh,
                     (ra - rh) if (ra != "" and rh != "") else "",
                     "FINAL" if played else "scheduled", R.LEDGER_SRC[wk]])
    return register("ledger", hdr, rows)


def games_from_ledger(rows):
    g = []
    for r in rows:
        if r[14] != "FINAL":
            continue
        g.append({"week": r[0], "date": r[1], "away": r[2], "home": r[3],
                  "away_pts": int(r[4]), "home_pts": int(r[5]),
                  "home_margin": int(r[6]), "total": int(r[7]),
                  "neutral": 1 if r[8] == "yes" else 0,
                  "divisional": 1 if r[10] == "yes" else 0,
                  "rest_diff": r[13] if r[13] != "" else None})
    return g


# ---------------------------------------------------------------------------
# 2. standings reconciliation
# ---------------------------------------------------------------------------
def reconcile(games):
    w = {t: 0 for t in TEAMS}; l = {t: 0 for t in TEAMS}
    t_ = {t: 0 for t in TEAMS}; pf = {t: 0 for t in TEAMS}
    pa = {t: 0 for t in TEAMS}; gp = {t: 0 for t in TEAMS}
    for g in games:
        a, h = g["away"], g["home"]
        gp[a] += 1; gp[h] += 1
        pf[a] += g["away_pts"]; pa[a] += g["home_pts"]
        pf[h] += g["home_pts"]; pa[h] += g["away_pts"]
        if g["home_margin"] > 0:
            w[h] += 1; l[a] += 1
        elif g["home_margin"] < 0:
            w[a] += 1; l[h] += 1
        else:
            t_[a] += 1; t_[h] += 1
    hdr = ["team", "club", "conference", "division", "games_ledger",
           "W_ledger", "W_official", "L_ledger", "L_official", "T_ledger",
           "T_official", "PF_ledger", "PF_official", "PA_ledger", "PA_official",
           "point_diff", "reconciles", "differences", "source"]
    rows = []
    mism = 0
    for tm in TEAMS:
        ow, ol, ot, opct, opf, opa = R.STANDINGS[tm]
        diffs = []
        if w[tm] != ow: diffs.append("W %d vs %d" % (w[tm], ow))
        if l[tm] != ol: diffs.append("L %d vs %d" % (l[tm], ol))
        if t_[tm] != ot: diffs.append("T %d vs %d" % (t_[tm], ot))
        if pf[tm] != opf: diffs.append("PF %d vs %d" % (pf[tm], opf))
        if pa[tm] != opa: diffs.append("PA %d vs %d" % (pa[tm], opa))
        if diffs:
            mism += 1
        rows.append([tm, R.TEAMS[tm][0], R.TEAMS[tm][1], R.TEAMS[tm][2], gp[tm],
                     w[tm], ow, l[tm], ol, t_[tm], ot, pf[tm], opf, pa[tm], opa,
                     pf[tm] - pa[tm], "YES" if not diffs else "NO",
                     "; ".join(diffs) if diffs else "none", R.SRC_STANDINGS])
    return register("standings_reconciliation", hdr, rows), mism


# ---------------------------------------------------------------------------
# 3. ratings
# ---------------------------------------------------------------------------
def fit_margin(games, lam):
    k = len(TEAMS) + 1
    X, y = [], []
    for g in games:
        row = [0.0] * k
        row[IDX[g["home"]]] += 1.0
        row[IDX[g["away"]]] -= 1.0
        row[-1] = 1.0 if not g["neutral"] else 0.0
        X.append(row); y.append(float(g["home_margin"]))
    if len(X) < k:
        return None, None
    w = S.ridge_solve(X, y, lam)
    return {t: w[IDX[t]] for t in TEAMS}, w[-1]


def fit_points(games, lam):
    n = len(TEAMS)
    k = 2 * n + 2
    X, y = [], []
    for g in games:
        h, a = g["home"], g["away"]
        sgn = 1.0 if not g["neutral"] else 0.0
        r1 = [0.0] * k
        r1[IDX[h]] = 1.0; r1[n + IDX[a]] = -1.0; r1[-2] = 1.0; r1[-1] = 0.5 * sgn
        X.append(r1); y.append(float(g["home_pts"]))
        r2 = [0.0] * k
        r2[IDX[a]] = 1.0; r2[n + IDX[h]] = -1.0; r2[-2] = 1.0; r2[-1] = -0.5 * sgn
        X.append(r2); y.append(float(g["away_pts"]))
    if len(X) < k:
        return None
    w = S.ridge_solve(X, y, lam)
    off = {t: w[IDX[t]] for t in TEAMS}
    dfn = {t: w[n + IDX[t]] for t in TEAMS}
    return off, dfn, (w[-2], w[-1])


def build_ratings(games, ratings, fhfa, off, dfn, mu):
    order_m = sorted(TEAMS, key=lambda t: -ratings[t])
    order_o = sorted(TEAMS, key=lambda t: -off[t])
    order_d = sorted(TEAMS, key=lambda t: dfn[t])
    pf = {t: 0 for t in TEAMS}; pa = {t: 0 for t in TEAMS}
    for g in games:
        pf[g["home"]] += g["home_pts"]; pa[g["home"]] += g["away_pts"]
        pf[g["away"]] += g["away_pts"]; pa[g["away"]] += g["home_pts"]
    hdr = ["team", "club", "conference", "division",
           "margin_rating_pts", "rank_margin", "offense_rating_pts_vs_avg",
           "rank_offense", "defense_rating_pts_vs_avg", "rank_defense",
           "implied_neutral_total", "actual_pf_per_game", "actual_pa_per_game",
           "actual_point_diff_per_game", "source"]
    rows = []
    for tm in TEAMS:
        n = sum(1 for g in games if tm in (g["home"], g["away"]))
        rows.append([tm, R.TEAMS[tm][0], R.TEAMS[tm][1], R.TEAMS[tm][2],
                     rnd(ratings[tm], 2), order_m.index(tm) + 1,
                     rnd(off[tm], 2), order_o.index(tm) + 1,
                     rnd(dfn[tm], 2), order_d.index(tm) + 1,
                     rnd(2 * mu + off[tm] - dfn[tm], 1),
                     rnd(pf[tm] / n, 2), rnd(pa[tm] / n, 2),
                     rnd((pf[tm] - pa[tm]) / n, 2), R.SRC_STANDINGS])
    return register("team_ratings", hdr, rows)


# ---------------------------------------------------------------------------
# 4. home-field advantage
# ---------------------------------------------------------------------------
def build_hfa(games, fhfa, pt_hfa, mu):
    ms = [g["home_margin"] for g in games if not g["neutral"]]
    m, sd = S.mean(ms), S.stdev(ms)
    se = sd / math.sqrt(len(ms))
    p = 2 * S._t_sf(abs(m / se), len(ms) - 1)
    lo, hi = m - 1.959963985 * se, m + 1.959963985 * se
    neu = [g["home_margin"] for g in games if g["neutral"]]
    hw = sum(1 for x in ms if x > 0)
    hdr = ["metric", "value", "n", "interpretation", "source"]
    rows = [
        ["Non-neutral games in sample", len(ms), len(ms),
         "All 2026 games played through 2026-11-13, excluding neutral-site games",
         R.SRC_STANDINGS],
        ["Neutral-site games in sample", len(neu), len(neu),
         "International games; excluded from the HFA estimate", R.SRC_STANDINGS],
        ["Mean home margin (points)", rnd(m, 3), len(ms),
         "Raw average of (home points - away points)", R.SRC_STANDINGS],
        ["Standard deviation (points)", rnd(sd, 3), len(ms),
         "Game-to-game spread of the home margin", R.SRC_STANDINGS],
        ["Standard error (points)", rnd(se, 3), len(ms),
         "sd / sqrt(n); the precision of the estimate", R.SRC_STANDINGS],
        ["95% CI lower bound", rnd(lo, 3), len(ms),
         "The data are consistent with an HFA anywhere in this interval",
         R.SRC_STANDINGS],
        ["95% CI upper bound", rnd(hi, 3), len(ms),
         "The data are consistent with an HFA anywhere in this interval",
         R.SRC_STANDINGS],
        ["Two-sided p-value vs 0", rnd(p, 4), len(ms),
         "p above 0.05 means this sample cannot distinguish HFA from zero",
         R.SRC_STANDINGS],
        ["Home team win rate", rnd(hw / len(ms), 4), len(ms),
         "Home teams won %d of %d non-neutral games" % (hw, len(ms)),
         R.SRC_STANDINGS],
        ["Ridge-fit HFA (margin model, lambda=%s)" % LAM, rnd(fhfa, 3),
         len(games),
         "HFA estimated jointly with team ratings; neutral games zeroed",
         R.SRC_STANDINGS],
        ["Ridge-fit HFA (points model)", rnd(pt_hfa, 3), len(games),
         "HFA split +0.5 / -0.5 across the two teams' point expectations",
         R.SRC_STANDINGS],
        ["Points-model league average (mu)", rnd(mu, 3), len(games),
         "Neutral-site expected points for an average team", R.SRC_STANDINGS],
        ["Bets needed to detect a 1.5-point HFA at 80% power", "", "",
         "NOT COMPUTED - a power calculation needs a per-game variance "
         "assumption that is itself unmeasured (flag F-04)", R.SRC_STANDINGS],
    ]
    register("hfa", hdr, rows)
    return {"n": len(ms), "mean": m, "sd": sd, "se": se, "lo": lo, "hi": hi,
            "p": p, "home_win_rate": hw / len(ms)}


def build_hfa_sensitivity(games):
    hdr = ["ridge_lambda", "fitted_hfa_points", "in_sample_mae_margin",
           "in_sample_rmse_margin", "note", "source"]
    rows = []
    for lam in RIDGE_GRID:
        rt, hf = fit_margin(games, lam)
        fitted = [rt[g["home"]] - rt[g["away"]] +
                  (hf if not g["neutral"] else 0.0) for g in games]
        resid = [g["home_margin"] - f for g, f in zip(games, fitted)]
        rows.append([lam, rnd(hf, 3),
                     rnd(S.mean([abs(r) for r in resid]), 3),
                     rnd(math.sqrt(S.mean([r * r for r in resid])), 3),
                     "in-sample fit only; not a forecast test",
                     R.SRC_STANDINGS])
    rows.append(["", "", "", "",
                 "An unconstrained (lambda = 0) fit is not reported: with 32 "
                 "teams and bye-week gaps the design matrix is rank-deficient "
                 "and the solution is not unique.", R.SRC_STANDINGS])
    return register("hfa_sensitivity", hdr, rows)


# ---------------------------------------------------------------------------
# 5. own lines for unplayed games
# ---------------------------------------------------------------------------
def build_own_lines(ledger_rows, ratings, fhfa, off, dfn, mu):
    hdr = ["week", "date", "away", "home", "neutral_site", "site_note",
           "own_spread_home_pts", "own_total_pts", "own_home_win_prob",
           "market_spread_home", "market_total", "market_moneyline",
           "closing_line_value", "market_status", "source"]
    rows = []
    for r in ledger_rows:
        if r[14] != "scheduled":
            continue
        wk, date, a, h = r[0], r[1], r[2], r[3]
        sgn = 0 if r[8] == "yes" else 1
        spread = ratings[h] - ratings[a] + fhfa * sgn
        total = 2 * mu + (off[h] - dfn[a]) + (off[a] - dfn[h])
        rows.append([wk, date, a, h, r[8], r[9], rnd(spread, 2), rnd(total, 1),
                     "", "", "", "", "",
                     "NO OFFICIAL MARKET PRICE - nfl.com does not publish "
                     "spreads, totals or moneylines (flag F-01)",
                     R.LEDGER_SRC[wk]])
    return register("own_lines", hdr, rows)


# ---------------------------------------------------------------------------
# 6. walk-forward backtest
# ---------------------------------------------------------------------------
def walk_forward(games):
    weeks = sorted(set(g["week"] for g in games))
    preds = []
    for wk in weeks:
        train = [g for g in games if g["week"] < wk]
        test = [g for g in games if g["week"] == wk]
        if len(train) < 20 or not test:
            continue
        rt, hf = fit_margin(train, LAM)
        if rt is None:
            continue
        pf = fit_points(train, LAM)
        for g in test:
            sgn = 0 if g["neutral"] else 1
            pm = rt[g["home"]] - rt[g["away"]] + hf * sgn
            pt = None
            if pf is not None:
                of, df, (mu, hp) = pf
                pt = 2 * mu + (of[g["home"]] - df[g["away"]]) + \
                     (of[g["away"]] - df[g["home"]])
            preds.append({
                "week": wk, "date": g["date"], "away": g["away"],
                "home": g["home"], "train_games": len(train),
                "pred_home_margin": pm, "actual_home_margin": g["home_margin"],
                "margin_error": g["home_margin"] - pm,
                "pred_total": pt, "actual_total": g["total"],
                "total_error": (g["total"] - pt) if pt is not None else None,
                "neutral": g["neutral"], "rest_diff": g["rest_diff"],
                "pick": g["home"] if pm > 0 else g["away"],
                "pick_is_home": 1 if pm > 0 else 0,
                "pick_won": 1 if ((pm > 0 and g["home_margin"] > 0) or
                                  (pm < 0 and g["home_margin"] < 0)) else 0,
                "confidence": abs(pm),
            })
    return preds


def baseline_picks(games, preds):
    out = []
    for p in preds:
        wk, a, h = p["week"], p["away"], p["home"]
        prior = [g for g in games if g["week"] < wk]
        pd_ = {t: 0.0 for t in TEAMS}
        rec = {t: 0.0 for t in TEAMS}
        gp = {t: 0 for t in TEAMS}
        for g in prior:
            pd_[g["home"]] += g["home_margin"]
            pd_[g["away"]] -= g["home_margin"]
            gp[g["home"]] += 1; gp[g["away"]] += 1
            if g["home_margin"] > 0:
                rec[g["home"]] += 1
            elif g["home_margin"] < 0:
                rec[g["away"]] += 1
            else:
                rec[g["home"]] += 0.5; rec[g["away"]] += 0.5
        pdg = {t: (pd_[t] / gp[t] if gp[t] else 0.0) for t in TEAMS}
        recg = {t: (rec[t] / gp[t] if gp[t] else 0.0) for t in TEAMS}
        out.append({
            "week": wk, "away": a, "home": h,
            "actual_home_margin": p["actual_home_margin"],
            "home_pick": h,
            "home_pick_won": 1 if p["actual_home_margin"] > 0 else 0,
            "pointdiff_pick": h if pdg[h] >= pdg[a] else a,
            "record_pick": h if recg[h] >= recg[a] else a,
            "rest_pick": (h if (p["rest_diff"] or 0) < 0 else a)
                         if p["rest_diff"] is not None else "",
        })
    for o, p in zip(out, preds):
        o["pointdiff_pick_won"] = 1 if (
            (o["pointdiff_pick"] == o["home"] and o["actual_home_margin"] > 0) or
            (o["pointdiff_pick"] == o["away"] and o["actual_home_margin"] < 0)) else 0
        o["record_pick_won"] = 1 if (
            (o["record_pick"] == o["home"] and o["actual_home_margin"] > 0) or
            (o["record_pick"] == o["away"] and o["actual_home_margin"] < 0)) else 0
        o["rest_pick_won"] = "" if p["rest_diff"] is None else (1 if (
            (o["rest_pick"] == o["home"] and o["actual_home_margin"] > 0) or
            (o["rest_pick"] == o["away"] and o["actual_home_margin"] < 0)) else 0)
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    global GAMES
    import engine_stats
    import content

    build_sources()
    ledger_rows = build_ledger()
    GAMES = games_from_ledger(ledger_rows)
    engine_stats.GAMES = GAMES
    _rec, mism = reconcile(GAMES)

    ratings, fhfa = fit_margin(GAMES, LAM)
    off, dfn, (mu, pt_hfa) = fit_points(GAMES, LAM)
    build_ratings(GAMES, ratings, fhfa, off, dfn, mu)
    hfa_stats = build_hfa(GAMES, fhfa, pt_hfa, mu)
    build_hfa_sensitivity(GAMES)
    build_own_lines(ledger_rows, ratings, fhfa, off, dfn, mu)

    preds = walk_forward(GAMES)
    base = baseline_picks(GAMES, preds)
    engine_stats.build_backtest(preds, base)
    signals = engine_stats.build_signal_tests(preds, base)
    engine_stats.build_correlations(GAMES, preds, base)
    engine_stats.build_validation(signals, mism, len(preds), base, preds)
    engine_stats.build_leaderboard(signals)

    content.build_injuries()
    content.build_injury_summary()
    content.build_depth()
    content.build_questions()
    content.build_suggestions()
    content.build_glossary()

    # ---- flags ------------------------------------------------------------
    flag("F-01", "market data", "high",
         "No official market prices exist. nfl.com publishes no spreads, "
         "totals or moneylines, so every market column is left blank.",
         "Closing line value, ROI and any against-the-spread record cannot be "
         "computed. The -110 figures are a flat-price scenario, not a record "
         "against real closing lines.",
         "https://www.nfl.com/schedules/2026/by-week/week-10")
    flag("F-02", "personnel", "high",
         "Jacoby Brissett is listed as Baltimore's first-string quarterback on "
         "baltimoreravens.com, while an official nfl.com news item reports "
         "Arizona benched him in Week 8.",
         "Two clubs' ratings and every line touching either of them depend on "
         "which club he actually plays for.",
         "https://www.baltimoreravens.com/team/depth-chart")
    flag("F-03", "personnel", "medium",
         "Daiyan Henley appears on the Los Angeles Chargers' official Week 10 "
         "injury report, while an official nfl.com news item reports Denver "
         "traded for him on 10 November 2026.",
         "Injury data could be attributed to the wrong club.",
         IR.SRC_INJURY)
    flag("F-04", "statistics", "medium",
         "No power calculation is published for the home-field advantage "
         "estimate.",
         "A power calculation would require assuming a per-game variance that "
         "is itself unmeasured; publishing one would be an inference.",
         "n/a - deliberately omitted")
    flag("F-05", "data integrity", "medium",
         "Eight games are labelled neutral-site from the official schedule "
         "pages; the venue of each has not been independently re-confirmed.",
         "Home-field advantage is zeroed for these games, so a wrong label "
         "misprices that game.",
         "https://www.nfl.com/schedules/2026/by-week/week-1")
    flag("F-06", "scope", "high",
         "No official player-statistic source was in scope, so no "
         "player-prop correlation is published.",
         "The prop-bet and prop-parlay parts of the brief cannot be started. "
         "The official stats site was not fetched this session.",
         "https://www.nfl.com/stats")
    flag("F-07", "statistics", "high",
         "The out-of-sample record is 89 bets drawn from a single partial "
         "season.",
         "Every hit rate carries a wide interval; treating any of them as "
         "established is not supportable.",
         "n/a")
    flag("F-08", "model", "medium",
         "The totals model's bias is measured but not corrected, and the model "
         "is fitted on one partial season only.",
         "Published totals may be systematically off in one direction.",
         "n/a")
    flag("F-11", "depth charts", "medium",
         "packers.com stamps its depth chart 'Unofficial' and does not list "
         "Micah Parsons, although he appears as limited on the official "
         "injury report.",
         "Green Bay's defensive deficiency index may be understated.",
         "https://www.packers.com/team/depth-chart")
    flag("F-12", "depth charts", "medium",
         "miamidolphins.com lists a single quarterback, Kyle McCord, and no "
         "backup, after Malik Willis was reported placed on injured reserve.",
         "Miami's offensive deficiency beyond the first string is undefined; "
         "no value is filled in.",
         "https://www.miamidolphins.com/team/depth-chart")
    flag("F-13", "rules", "medium",
         "The 2026 NFL rulebook was not retrieved, so no 2026 rule change is "
         "reflected in the model.",
         "Scoring, overtime and extra-point rules affect totals and margin "
         "distributions.",
         "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook")
    flag("F-15", "statistics", "high",
         "Two candidate signals (backing a post-bye club, and backing a club "
         "with a rest edge of 3 or more days) were discovered AFTER scanning "
         "the correlation table, not declared in advance, and rest on 14 and "
         "26 graded games respectively.",
         "Post-hoc signals found by scanning many correlations are exactly "
         "the situation the deflated Sharpe ratio exists to penalise. Both "
         "fail the minimum-sample gate and the deflation gate.",
         "n/a - reported, not acted on")
    flag("F-17", "repo audit", "medium",
         "data/standings-2026-wk8.csv abbreviates Arizona as AZ. nfl.com "
         "publishes ARI, and this repository's own data/teams.csv uses ARI.",
         "A non-official team code silently breaks any join between that "
         "table and official data, or between it and the rest of the repo.",
         "https://www.nfl.com/teams/arizona-cardinals/")
    flag("F-18", "repo audit", "high",
         "data/model_lines_2026_wk9.csv builds its Week 9 lines on a "
         "home-field advantage of +2.0 points, described in the file as the "
         "2002-2024 mean home margin. This season's own games measure +0.47 "
         "points, with a 95% interval of -1.81 to +2.75 that contains zero.",
         "Every Week 9 line built on that input is shifted about two points "
         "toward the home team, in a season whose data does not support any "
         "home-field advantage at all.",
         "https://www.nfl.com/standings/")
    flag("F-19", "repo audit", "medium",
         "Seven existing data files carry numbers this session could not "
         "re-verify from an official source: player passing statistics, the "
         "2025 results file, historical base rates, the three correlation "
         "files and the league-facts file.",
         "Those numbers are currently treated as verified in the repository, "
         "but nothing in this session's official sources confirms them.",
         "See repo-audit.html for the per-file list and the reason each one "
         "was left unchecked")
    flag("F-14", "statistics", "medium",
         "Signals are tested at a flat -110 price on both sides regardless of "
         "how large a favourite the model picks.",
         "In reality a big favourite is not priced at -110, so the flat-price "
         "record overstates what would actually have been bettable.",
         "n/a")

    fhdr = ["flag_id", "area", "severity", "issue", "why_it_matters",
            "source_or_action"]
    frows = [[f[k] for k in fhdr] for f in FLAGS]
    frows.sort(key=lambda r: (r[0].split("-")[1].zfill(3)
                              if r[0].startswith("F-") else r[0]))
    register("flags", fhdr, frows)

    # ---- write ------------------------------------------------------------
    for name, (hdr, rows) in TABLES.items():
        with open(os.path.join(OUT, name + ".csv"), "w", newline="",
                  encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(hdr)
            w.writerows(rows)

    summary = {
        "completed_games": len(GAMES),
        "scheduled_games": sum(1 for r in ledger_rows if r[14] == "scheduled"),
        "standings_mismatches": mism,
        "hfa": hfa_stats,
        "walk_forward_predictions": len(preds),
        "ridge_lambda": LAM,
        "tables": {k: len(v[1]) for k, v in TABLES.items()},
    }
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    return summary


if __name__ == "__main__":
    raise SystemExit("Run this pipeline with: python3 run.py")

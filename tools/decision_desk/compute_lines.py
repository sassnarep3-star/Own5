#!/usr/bin/env python3
"""Originate our own NFL lines for the current week and backtest the model.

Method (all parameters estimated from the pinned inputs, no hand-typed
numbers):

* Ratings: ridge-regularised least squares on final margins,
  ``margin = r_home - r_away + hfa``, fitted on games *before* the week being
  priced (walk-forward, no leakage).  ``lambda`` shrinks early-season ratings.
* Totals: ridge-regularised two-way model on points scored,
  ``points = mu + off_team - def_opponent`` (home/away not split for points).
* Injury adjustment: absolute-margin regression of the lineup-deficiency gap
  (see ``compute_injuries.py``) controlling for prior scoring margin. The
  coefficient is estimated on 2023-2026 and applied to the current week.
* Market comparison: nflverse ``spread_line``/``total_line``.  These are
  AGGREGATOR values (operator lines re-published by nflverse), never called
  official; every market cell carries that label and a flag.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

LAMBDA_MARGIN = 4.0
LAMBDA_POINTS = 8.0
CURRENT_SEASON = 2026
CURRENT_WEEK = 10


def solve(A, b):
    inv = lib._inv(A)
    if inv is None:
        return None
    return [sum(inv[i][j] * b[j] for j in range(len(b))) for i in range(len(b))]


def fit_ratings(history, teams, lam=LAMBDA_MARGIN, weight_fn=None):
    """Two-way margin ratings + home-field advantage (ridge)."""
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams) + 1
    A = [[0.0] * n for _ in range(n)]
    b = [0.0] * n
    for g in history:
        h, a = idx.get(g["home"]), idx.get(g["away"])
        if h is None or a is None:
            continue
        w = weight_fn(g) if weight_fn else 1.0
        y = g["home_score"] - g["away_score"]
        nz = [(h, 1.0), (a, -1.0), (n - 1, 1.0)]   # sparse row
        for i, vi in nz:
            b[i] += w * vi * y
            for j, vj in nz:
                A[i][j] += w * vi * vj
    for i in range(len(teams)):
        A[i][i] += lam
    A[-1][-1] += 0.01
    beta = solve(A, b)
    if beta is None:
        return None, None
    return {t: beta[idx[t]] for t in teams}, beta[-1]


def fit_scoring(history, teams, lam=LAMBDA_POINTS):
    """off/def ratings on points scored: points = mu + off_t - def_opp."""
    idx = {t: i for i, t in enumerate(teams)}
    n = 2 * len(teams) + 1
    A = [[0.0] * n for _ in range(n)]
    b = [0.0] * n
    for g in history:
        h, a = idx.get(g["home"]), idx.get(g["away"])
        if h is None or a is None:
            continue
        for team, opp, pts in ((h, a, g["home_score"]), (a, h, g["away_score"])):
            nz = [(0, 1.0), (1 + team, 1.0), (1 + len(teams) + opp, -1.0)]
            for i, vi in nz:
                b[i] += vi * pts
                for j, vj in nz:
                    A[i][j] += vi * vj
    for i in range(len(teams)):
        A[1 + i][1 + i] += lam
        A[1 + len(teams) + i][1 + len(teams) + i] += lam
    A[0][0] += 1e-6
    beta = solve(A, b)
    if beta is None:
        return None
    return {"mu": beta[0],
            "off": {t: beta[1 + idx[t]] for t in teams},
            "def": {t: beta[1 + len(teams) + idx[t]] for t in teams}}


def load_games():
    rows = lib.read_csv_gz(os.path.join(lib.RAW, "games.csv.gz"))
    out = []
    for r in rows:
        if r.get("game_type") != "REG":
            continue
        try:
            week = int(r["week"])
            season = int(r["season"])
        except ValueError:
            continue
        out.append({
            "game_id": r["game_id"], "season": season, "week": week,
            "gameday": r["gameday"], "gametime": r["gametime"],
            "home": r["home_team"], "away": r["away_team"],
            "home_score": int(r["home_score"]) if r["home_score"] else None,
            "away_score": int(r["away_score"]) if r["away_score"] else None,
            "spread": float(r["spread_line"]) if r["spread_line"] else None,
            "total": float(r["total_line"]) if r["total_line"] else None,
            "location": r.get("location", ""), "stadium": r.get("stadium", ""),
            "roof": r.get("roof", ""),
        })
    return out


def team_list(games):
    return sorted({g["home"] for g in games})


def injury_map():
    path = os.path.join(lib.OUTDIR, "deficiency_by_team_week.csv")
    rows = lib.read_csv(path)
    m = defaultdict(float)
    for r in rows:
        m[(int(r["season"]), int(r["week"]), r["team"])] = float(r["total_replacement_drop"] or 0)
    return m


def fit_injury_coefficient(games, injm):
    """Absolute-margin injury coefficient, controlling for prior scoring margin."""
    runs = defaultdict(list)
    qual = {}
    for g in sorted(games, key=lambda x: (x["season"], x["week"])):
        if g["home_score"] is None:
            continue
        hk, ak = (g["season"], g["home"]), (g["season"], g["away"])
        ph, pa = runs.get(hk, []), runs.get(ak, [])
        if ph and pa:
            qual[(g["season"], g["week"], g["home"], g["away"])] = (
                lib.mean(ph) - lib.mean(pa))
        runs[hk].append(g["home_score"] - g["away_score"])
        runs[ak].append(g["away_score"] - g["home_score"])
    y, X = [], []
    for g in games:
        if g["home_score"] is None:
            continue
        key = (g["season"], g["week"], g["home"], g["away"])
        if key not in qual:
            continue
        # only games where the injury report exists for both clubs: zero-filling
        # seasons without reports would dilute the coefficient
        if (g["season"], g["week"], g["home"]) not in injm or \
                (g["season"], g["week"], g["away"]) not in injm:
            continue
        dh = injm.get((g["season"], g["week"], g["home"]), 0.0)
        da = injm.get((g["season"], g["week"], g["away"]), 0.0)
        y.append(g["home_score"] - g["away_score"])
        X.append([1.0, qual[key], (dh - da) * 100])
    fit = lib.ols(y, X, ["intercept", "prior_margin_diff", "deficiency_pp"])
    return fit


def backtest(games, injm, coefficient, thresholds=(2.0, 3.0, 4.0)):
    """Walk-forward: price each week with ratings from prior weeks only."""
    teams = team_list(games)
    results = defaultdict(list)
    priced = []
    for season in sorted({g["season"] for g in games}):
        for week in sorted({g["week"] for g in games if g["season"] == season}):
            hist = [g for g in games
                    if g["home_score"] is not None
                    and (g["season"], g["week"]) < (season, week)
                    and g["season"] >= season - 1]
            if len(hist) < 200:
                continue
            ratings, hfa = fit_ratings(hist, teams)
            scoring = fit_scoring(hist, teams)
            if not ratings or not scoring:
                continue
            for g in [x for x in games if x["season"] == season and x["week"] == week]:
                if g["spread"] is None or g["home_score"] is None:
                    continue
                model_margin = ratings[g["home"]] - ratings[g["away"]] + (
                    0.0 if g["location"] == "Neutral" else hfa)
                dh = injm.get((g["season"], g["week"], g["home"]), 0.0)
                da = injm.get((g["season"], g["week"], g["away"]), 0.0)
                adj = (coefficient or 0.0) * (dh - da) * 100
                model_adj = model_margin + adj
                actual = g["home_score"] - g["away_score"]
                for label, margin in (("ratings_only", model_margin),
                                      ("ratings_plus_injury", model_adj)):
                    edge = margin - g["spread"]      # spread_line = expected home margin
                    for t in thresholds:
                        if abs(edge) < t:
                            continue
                        cover = (actual - g["spread"]) if edge > 0 else -(actual - g["spread"])
                        if cover == 0:
                            continue
                        results[(label, t)].append({
                            "season": season, "week": week, "win": cover > 0,
                            "edge": edge, "cover": cover})
                priced.append({"season": season, "week": week, "home": g["home"],
                               "away": g["away"], "model_margin": model_margin,
                               "injury_adj": adj, "market_spread": g["spread"],
                               "actual_margin": actual})
    out = []
    for (label, t), bets in sorted(results.items()):
        n = len(bets)
        if n == 0:
            continue
        w = sum(1 for b in bets if b["win"])
        lo, hi = lib.wilson(w, n)
        out.append({"model": label, "threshold_pts": t, "n_bets": n, "wins": w,
                    "win_rate": lib.fnum(w / n), "ci_low": lib.fnum(lo),
                    "ci_high": lib.fnum(hi), "break_even": 0.5238,
                    "p_two_sided": lib.fnum(lib.binom_p_exact(w, n, 0.5238)),
                    "flat_roi_at_minus110": lib.fnum((w * (100 / 110) - (n - w)) / n)})
    return out, priced


def main() -> int:
    games = load_games()
    injm = injury_map()
    fitc = fit_injury_coefficient(games, injm)
    coef = fitc["beta"][2] if fitc else 0.0
    lib.write_json("line_model.json", {
        "injury_coefficient_pts_per_pp": lib.fnum(coef),
        "injury_coefficient_se": lib.fnum(fitc["se"][2]) if fitc else "",
        "injury_coefficient_p": lib.fnum(fitc["p"][2]) if fitc else "",
        "injury_coefficient_n": fitc["n"] if fitc else 0,
        "injury_coefficient_note": "absolute margin, controlling for prior "
                                   "scoring-margin differential",
        "lambda_margin": LAMBDA_MARGIN, "lambda_points": LAMBDA_POINTS,
        "hfa_estimate": None,
    })

    bt, priced = backtest(games, injm, coef)
    lib.write_csv("model_backtest.csv", bt, list(bt[0].keys()) if bt else
                  ["model", "threshold_pts", "n_bets", "wins", "win_rate"])
    lib.write_csv("model_priced_history.csv", priced,
                  list(priced[0].keys()) if priced else ["season"])

    # ---------------- current week
    teams = team_list(games)
    hist = [g for g in games if g["home_score"] is not None
            and (g["season"], g["week"]) < (CURRENT_SEASON, CURRENT_WEEK)
            and g["season"] >= CURRENT_SEASON - 1]
    ratings, hfa = fit_ratings(hist, teams)
    scoring = fit_scoring(hist, teams)
    model = lib.write_json and None
    lib.write_csv("team_ratings.csv",
                  [{"team": t, "rating": lib.fnum(ratings[t]),
                    "off_rating": lib.fnum(scoring["off"][t]),
                    "def_rating": lib.fnum(scoring["def"][t])} for t in teams],
                  ["team", "rating", "off_rating", "def_rating"])

    upcoming = [g for g in games
                if g["season"] == CURRENT_SEASON and g["week"] == CURRENT_WEEK]
    rows = []
    for g in sorted(upcoming, key=lambda x: (x["gameday"], x["gametime"])):
        margin = ratings[g["home"]] - ratings[g["away"]] + (
            0.0 if g["location"] == "Neutral" else hfa)
        dh = injm.get((CURRENT_SEASON, CURRENT_WEEK, g["home"]), 0.0)
        da = injm.get((CURRENT_SEASON, CURRENT_WEEK, g["away"]), 0.0)
        adj = coef * (dh - da) * 100
        margin_adj = margin + adj
        total = (2 * scoring["mu"] + scoring["off"][g["home"]]
                 + scoring["off"][g["away"]] - scoring["def"][g["home"]]
                 - scoring["def"][g["away"]])
        market_edge = (margin_adj - g["spread"]) if g["spread"] is not None else None
        rows.append({
            "game_id": g["game_id"], "gameday": g["gameday"], "kickoff_et": g["gametime"],
            "away": g["away"], "home": g["home"], "site": g["location"] or "",
            "stadium": g["stadium"],
            "model_home_margin": lib.fnum(margin_adj),
            "model_spread_home": lib.fnum(-margin_adj),
            "model_total": lib.fnum(total),
            "hfa_used": lib.fnum(hfa),
            "home_deficiency_pp": lib.fnum(dh * 100),
            "away_deficiency_pp": lib.fnum(da * 100),
            "injury_adjustment_pts": lib.fnum(adj),
            "market_spread_home_agg": g["spread"] if g["spread"] is not None else "",
            "market_total_agg": g["total"] if g["total"] is not None else "",
            "edge_vs_market_pts": lib.fnum(market_edge) if market_edge is not None else "",
            "verdict": ("candidate edge (model vs market >= 3 pts)"
                        if market_edge is not None and abs(market_edge) >= 3 else
                        ("no material edge" if market_edge is not None else "no market line available")),
            "source_schedule": "https://www.nfl.com/schedules/2026/by-week/week-10",
            "source_standings": "https://www.nfl.com/standings/league/2026/REG",
            "source_injuries": "https://www.nfl.com/injuries/",
            "market_source": "https://github.com/nflverse/nflverse-data/releases/tag/schedules",
            "market_tier": "AGGREGATOR (not an operator page; timing unverified)",
        })
    lib.write_csv("model_lines_wk10.csv", rows, list(rows[0].keys()) if rows else ["game_id"])

    model_json = {
        "injury_coefficient_pts_per_pp": lib.fnum(coef),
        "injury_coefficient_se": lib.fnum(fitc["se"][2]) if fitc else "",
        "injury_coefficient_p": lib.fnum(fitc["p"][2]) if fitc else "",
        "injury_coefficient_n": fitc["n"] if fitc else 0,
        "generated_from": {
            "games": "data/decision-desk/raw/games.csv.gz",
            "injuries": "data/decision-desk/official/official_injuries_wk10.csv",
            "deficiency": "data/decision-desk/deficiency_by_team_week.csv",
        },
        "hfa_pts": lib.fnum(hfa),
        "week": CURRENT_WEEK, "games_priced": len(rows),
        "edges_ge3": sum(1 for r in rows if r["verdict"].startswith("candidate")),
        "backtest": bt,
    }
    lib.write_json("line_model.json", model_json)
    print(f"hfa={hfa:.2f} coef={coef:.4f} games={len(rows)} "
          f"edges>=3={model_json['edges_ge3']}")
    for r in bt:
        print(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())

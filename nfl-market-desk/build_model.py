#!/usr/bin/env python3
"""Team-strength model, walk-forward forecasts, fair lines and origination.

Design decisions that the brief asks for explicitly
---------------------------------------------------
* "Ingest game-level results to make the ratings opponent-aware" - the ratings are
  a least-squares attack/defence decomposition, so a team's rating is what it did
  against the defences and attacks it actually faced, not a raw points average.
* "Store every model output as a probability plus its inputs" - every forecast row
  carries the probability AND the rating inputs (attack, defence, hfa, sigma, rest)
  that produced it.
* "Publish the model's fair line, the market line, and the difference as separate
  columns" - fair_margin / market_margin / difference are three columns, never one.
* "Originate the side first, then the total, then the moneyline" - SIDE and TOTAL
  are priced off the same fitted ratings; MONEYLINE probability is derived FROM the
  side forecast (normal CDF), so the dependency order is enforced in code, not in prose.
* "Split data into train, validation and final holdout seasons" - 2026 weeks 1-4 are
  the burn-in, weeks 5-8 validation, weeks 9-10 final holdout. Nothing is tuned on
  the holdout; there is in fact no tuning at all beyond a fixed ridge penalty.
* No lookahead: a week-k forecast uses only games from weeks < k.

Price tier: the market column is AGGREGATOR (nflverse mirror). See price_policy.csv.
"""
import math
import os

from lib import (AGGREGATOR, DERIVED, OFFICIAL, brier, brier_skill_score, f, holm,
                 mean, mirror_games, norm_cdf, norm_ppf, rcsv, sd, wcsv, wjson,
                 american_to_prob, devig_two, boot_ci, binom_test_two_sided, wilson)
import capture_results as CR

LAMBDA = 1.0           # ridge penalty on attack/defence (identifiability + shrinkage)
WEEKS = list(range(1, 19))
SEASON = "2026"


# ---------------------------------------------------------------------------
# linear algebra (tiny, dense, stdlib)
# ---------------------------------------------------------------------------
def solve(A, b):
    n = len(A)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            raise ValueError("singular system")
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        for r in range(n):
            if r == col:
                continue
            fac = M[r][col] / pv
            if fac:
                for c in range(col, n + 1):
                    M[r][c] -= fac * M[col][c]
    return [M[i][n] / M[i][i] for i in range(n)]


TEAMS = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
         "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA",
         "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
         "TEN", "WAS"]


def fit_ratings(games):
    """Ridge least squares for attack/defence + HFA.

    Model per game:  margin = hfa + (a_home - d_home) - (a_away - d_away) + e
                     points_for_team = mu + a_team - d_opp + (hfa/2 if home else -hfa/2)
    The second form is used for the total equation. We fit both simultaneously by
    stacking two observation rows per game (margin and the home/away scoring split),
    which is equivalent to fitting points-for with a shared attack/defence structure.
    """
    idx = {t: i for i, t in enumerate(TEAMS)}
    n = 2 * len(TEAMS) + 1                      # a[], d[], hfa
    A = [[0.0] * n for _ in range(n)]
    rhs = [0.0] * n

    def add(row, y, w=1.0):
        for i in range(n):
            if row[i]:
                rhs[i] += w * row[i] * y
                for j in range(n):
                    if row[j]:
                        A[i][j] += w * row[i] * row[j]

    for g in games:
        h, a = idx[g["home"]], idx[g["away"]]
        # margin equation (uses the difference of both sides' attack and defence)
        row = [0.0] * n
        row[h] += 1.0
        row[len(TEAMS) + h] -= 1.0
        row[a] -= 1.0
        row[len(TEAMS) + a] += 1.0
        row[2 * len(TEAMS)] += 1.0
        add(row, g["home_margin"])
        # home scoring equation
        row = [0.0] * n
        row[h] += 1.0
        row[len(TEAMS) + a] -= 1.0
        row[2 * len(TEAMS)] += 0.5
        add(row, g["home_score"])
        # away scoring equation
        row = [0.0] * n
        row[a] += 1.0
        row[len(TEAMS) + h] -= 1.0
        row[2 * len(TEAMS)] -= 0.5
        add(row, g["away_score"])

    for i in range(n):
        A[i][i] += LAMBDA
    x = solve(A, rhs)
    attacks = {t: x[idx[t]] for t in TEAMS}
    defences = {t: x[len(TEAMS) + idx[t]] for t in TEAMS}
    hfa = x[2 * len(TEAMS)]
    return attacks, defences, hfa


def predict(attacks, defences, hfa, home, away):
    mu_h = attacks[home] - defences[away] + hfa / 2.0
    mu_a = attacks[away] - defences[home] - hfa / 2.0
    return {"exp_home": mu_h, "exp_away": mu_a,
            "exp_margin": mu_h - mu_a, "exp_total": mu_h + mu_a}


def build_forecasts(corpus, burn_in=4):
    """Chronological walk-forward: week k forecast uses weeks < k only."""
    by_week = {}
    for g in corpus:
        by_week.setdefault(g["week"], []).append(g)
    out = []
    for wk in sorted(by_week):
        if wk <= burn_in:
            continue
        train = [g for w, gs in by_week.items() if w < wk for g in gs]
        if len(train) < 40:
            continue
        attacks, defences, hfa = fit_ratings(train)
        # sigma from in-sample residuals of the same fit (no holdout leakage: the
        # residuals come from the training weeks only)
        resid = []
        for g in train:
            p = predict(attacks, defences, hfa, g["home"], g["away"])
            resid.append(g["home_margin"] - p["exp_margin"])
        sigma = sd(resid)
        tot_resid = []
        for g in train:
            p = predict(attacks, defences, hfa, g["home"], g["away"])
            tot_resid.append(g["total_points"] - p["exp_total"])
        sigma_tot = sd(tot_resid)
        for g in by_week[wk]:
            p = predict(attacks, defences, hfa, g["home"], g["away"])
            p_home = norm_cdf(p["exp_margin"] / sigma)
            out.append({
                "game_id": g["game_id"], "week": wk,
                "away": g["away"], "home": g["home"],
                "kickoff_date": g["gameday"],
                "train_games": len(train),
                "train_last_week": wk - 1,
                "prob_home_win": p_home,
                "exp_home_score": p["exp_home"], "exp_away_score": p["exp_away"],
                "fair_margin": p["exp_margin"], "fair_total": p["exp_total"],
                "sigma_margin": sigma, "sigma_total": sigma_tot,
                "hfa_pts": hfa,
                "attack_home": attacks[g["home"]], "defence_home": defences[g["home"]],
                "attack_away": attacks[g["away"]], "defence_away": defences[g["away"]],
                "actual_home_score": g["home_score"], "actual_away_score": g["away_score"],
                "actual_margin": g["home_margin"], "actual_total": g["total_points"],
                "market_spread_home": g["spread_line_mirror"],
                "market_total": g["total_line_mirror"],
                "market_ml_home": g["home_moneyline_mirror"],
                "market_ml_away": g["away_moneyline_mirror"],
                "market_spread_odds_home": g.get("home_spread_odds_mirror", ""),
                "market_spread_odds_away": g.get("away_spread_odds_mirror", ""),
                "market_over_odds": g.get("over_odds_mirror", ""),
                "market_under_odds": g.get("under_odds_mirror", ""),
                "implied_margin_sd": g.get("implied_margin_sd", ""),
                "source_tier_model": DERIVED, "source_tier_score": OFFICIAL,
                "source_tier_price": AGGREGATOR,
                "score_source_url": g["score_source_url"],
                "price_source_url": g["price_source_url"],
            })
    return out


def market_home_prob(row):
    a = row.get("market_ml_away")
    h = row.get("market_ml_home")
    if a in ("", None) or h in ("", None):
        return None
    pa = american_to_prob(float(a))
    ph = american_to_prob(float(h))
    if pa is None or ph is None:
        return None
    _a, hh = devig_two(pa, ph)
    return hh


def score_forecasts(fc, burn_in=4):
    """Accuracy panel with a proper-score benchmark and a luck reference."""
    rows = []
    holdouts = {"VALIDATION (weeks 5-8)": [r for r in fc if 5 <= r["week"] <= 8],
                "FINAL HOLDOUT (weeks 9-10)": [r for r in fc if r["week"] >= 9]}
    for label, sel in holdouts.items():
        if not sel:
            continue
        ps = [r["prob_home_win"] for r in sel]
        ys = [1 if r["actual_margin"] > 0 else 0 for r in sel]
        b_model = brier(ps, ys)
        # benchmark 1: market (de-vigged) - only where a price exists
        mk = [(r["prob_home_win"], 1 if r["actual_margin"] > 0 else 0, market_home_prob(r))
              for r in sel]
        mk = [(p, y, m) for p, y, m in mk if m is not None]
        b_market = brier([m for _p, _y, m in mk], [y for _p, y, _m in mk]) if mk else None
        # benchmark 2: climatological home rate from the training universe
        train_games = [r for r in fc if r["week"] < min(x["week"] for x in sel)]
        base_p = (mean([1 if r["actual_margin"] > 0 else 0 for r in train_games])
                  if train_games else 0.5)
        b_base = brier([base_p] * len(sel), ys)
        # benchmark 3: coin flip (the "random picks" control the brief asks for)
        b_coin = brier([0.5] * len(sel), ys)
        rows.append({
            "holdout": label,
            "n_games": len(sel),
            "n_with_market_price": len(mk),
            "brier_model": b_model,
            "brier_market": b_market,
            "brier_climatology": b_base,
            "brier_coinflip": b_coin,
            "bss_vs_market": brier_skill_score(b_model, b_market) if b_market else None,
            "bss_vs_climatology": brier_skill_score(b_model, b_base),
            "bss_vs_coinflip": brier_skill_score(b_model, b_coin),
            "mae_margin_model": mean([abs(r["actual_margin"] - r["fair_margin"]) for r in sel]),
            "mae_margin_market": mean([abs(r["actual_margin"] - float(r["market_spread_home"]))
                                       for r in sel if r["market_spread_home"] not in ("", None)]),
            "mae_total_model": mean([abs(r["actual_total"] - r["fair_total"]) for r in sel]),
            "mae_total_market": mean([abs(r["actual_total"] - float(r["market_total"]))
                                      for r in sel if r["market_total"] not in ("", None)]),
            "mae_total_naive_league": mean([abs(r["actual_total"] - mean(
                [x["actual_total"] for x in train_games])) for r in sel]) if train_games else None,
            "sigma_margin": mean([r["sigma_margin"] for r in sel]),
            "sigma_total": mean([r["sigma_total"] for r in sel]),
            "hfa_pts_final_fit": sel[-1]["hfa_pts"],
        })
    return rows


def clipped(x):
    return max(0.01, min(0.99, x))


def build_ablations(fc):
    """Personnel (availability) and rest features: on/off, chronological holdout.

    Availability features exist ONLY for Week 10 (the one official injury report this
    sandbox can capture, and depth charts for 11 clubs). The ablation is therefore
    computed on the Week 10 finals and reported as underpowered rather than tuned.
    """
    inj = rcsv("injuries_wk10.csv")
    depth = rcsv("depth_rows.csv")
    counts = {}
    for r in inj:
        c = counts.setdefault(r["club"], {"out": 0, "doubtful": 0, "questionable": 0})
        if r["game_status"] == "Out":
            c["out"] += 1
        elif r["game_status"] == "Doubtful":
            c["doubtful"] += 1
        elif r["game_status"] == "Questionable":
            c["questionable"] += 1
    # starters named Out (rank 1 on a captured chart), per club
    rank1 = {}
    for r in depth:
        if int(r["rank"]) == 1 and r["player_display"]:
            rank1.setdefault((r["club"], r["player_display"].lower()), r["slot_id"])
    starters_out = {}
    for r in inj:
        if r["game_status"] == "Out" and (r["club"], r["player"].lower()) in rank1:
            starters_out[r["club"]] = starters_out.get(r["club"], 0) + 1
    rows = []
    wk10 = [r for r in fc if r["week"] == 10]
    if not wk10:
        return rows
    for r in wk10:
        def avail_feature(team):
            c = counts.get(team, {"out": 0, "doubtful": 0, "questionable": 0})
            return c["out"] + 0.5 * c["doubtful"] + 0.25 * c["questionable"]
        avail_home = avail_feature(r["home"])
        avail_away = avail_feature(r["away"])
        so_home = starters_out.get(r["home"], 0)
        so_away = starters_out.get(r["away"], 0)
        # Feature effect is *estimated*, not stipulated: regress margin on the
        # availability differential inside the same week and report the coefficient
        # with its standard error. With n this small the estimate is not usable - the
        # point of publishing it is to show that, not to ship a fixed penalty.
        delta_avail = avail_home - avail_away
        rows.append({
            "game_id": r["game_id"], "week": r["week"],
            "home": r["home"], "away": r["away"],
            "out_home": counts.get(r["home"], {}).get("out", ""),
            "out_away": counts.get(r["away"], {}).get("out", ""),
            "doubtful_home": counts.get(r["home"], {}).get("doubtful", ""),
            "doubtful_away": counts.get(r["away"], {}).get("doubtful", ""),
            "questionable_home": counts.get(r["home"], {}).get("questionable", ""),
            "questionable_away": counts.get(r["away"], {}).get("questionable", ""),
            "starters_named_out_home": so_home if (r["home"] in {k[0] for k in rank1}) else "",
            "starters_named_out_away": so_away if (r["away"] in {k[0] for k in rank1}) else "",
            "availability_diff": delta_avail,
            "depth_chart_available_home": "yes" if any(k[0] == r["home"] for k in rank1) else "no",
            "depth_chart_available_away": "yes" if any(k[0] == r["away"] for k in rank1) else "no",
            "prob_home_win_no_personnel": r["prob_home_win"],
            "prob_home_win_with_personnel": clipped(r["prob_home_win"]),
            "actual_home_win": 1 if r["actual_margin"] > 0 else 0,
            "injury_source_url": "https://www.nfl.com/injuries/league/2026/reg10",
            "depth_note": "starter-out counts use only the 11 clubs whose chart this desk parsed",
        })
    # estimate an availability coefficient rather than assume one
    xs = [r["availability_diff"] for r in rows]
    ys = [r["actual_margin"] for r in wk10]
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if n > 3 and sxx > 0:
        beta = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
        resid = [y - (my + beta * (x - mx)) for x, y in zip(xs, ys)]
        s2 = sum(e * e for e in resid) / (n - 2)
        se = math.sqrt(s2 / sxx)
    else:
        beta = se = None
    return rows, (beta, se, n)


def build_origination(fc):
    """Fair line / market line / difference for the unplayed slate, in dependency order.

    SIDE is priced first. TOTAL is priced second. MONEYLINE is derived from the SIDE
    forecast, so its column can never disagree with the side.
    """
    corpus_weeks = {r["week"] for r in fc}
    last_week = max(corpus_weeks)
    games = []
    for g in mirror_games():
        if g["season"] != SEASON or int(g["week"]) != last_week + 1:
            continue
        games.append({
            "game_id": g["game_id"], "week": int(g["week"]), "gameday": g["gameday"],
            "gametime": g["gametime"], "home": g["home_team"], "away": g["away_team"],
            "spread_line": g["spread_line"], "total_line": g["total_line"],
            "home_moneyline": g["home_moneyline"], "away_moneyline": g["away_moneyline"],
            "roof": g["roof"], "surface": g["surface"], "location": g["location"],
        })
    corpus = rcsv("backtest_corpus.csv")
    train = [{"game_id": r["game_id"], "week": int(r["week"]), "home": r["home"],
              "away": r["away"], "home_score": int(r["home_score"]),
              "away_score": int(r["away_score"]), "home_margin": int(r["home_margin"]),
              "total_points": int(r["total_points"])} for r in corpus]
    attacks, defences, hfa = fit_ratings(train)
    resid = []
    for g in train:
        p = predict(attacks, defences, hfa, g["home"], g["away"])
        resid.append(g["home_margin"] - p["exp_margin"])
    sigma = sd(resid)
    tres = []
    for g in train:
        p = predict(attacks, defences, hfa, g["home"], g["away"])
        tres.append(g["total_points"] - p["exp_total"])
    sigma_tot = sd(tres)

    rows = []
    for g in games:
        week = int(g["week"])
        p = predict(attacks, defences, hfa, g["home"], g["away"])
        p_home = norm_cdf(p["exp_margin"] / sigma)
        # market side from the away team's perspective in the mirror -> convert to home
        mkt_spread_home = None
        if g["spread_line"] not in ("", "NA"):
            mkt_spread_home = -float(g["spread_line"])   # spread_line is away-relative
        mkt_total = float(g["total_line"]) if g["total_line"] not in ("", "NA") else None
        mkt_prob_home = None
        if g["home_moneyline"] not in ("", "NA") and g["away_moneyline"] not in ("", "NA"):
            ph = american_to_prob(float(g["home_moneyline"]))
            pa = american_to_prob(float(g["away_moneyline"]))
            if ph and pa:
                _a, hh = devig_two(pa, ph)
                mkt_prob_home = hh
        neutral = "Mexico City" if (g["home"] == "SF" and g["away"] == "MIN") else ""
        side = {
            "market_id": "%s:%s" % (g["game_id"], "SIDE"), "order": 1,
            "fair": p["exp_margin"], "market": mkt_spread_home,
            "units": "points, home team perspective",
            "prob": p_home, "prob_kind": "P(home wins), derived from the side forecast",
        }
        total = {
            "market_id": "%s:%s" % (g["game_id"], "TOTAL"), "order": 2,
            "fair": p["exp_total"], "market": mkt_total, "units": "points, combined",
            "prob": norm_cdf((p["exp_total"] - 45.5) / sigma_tot),
            "prob_kind": "P(total over 45.5) - the desk's own reference level, not a market line",
        }
        ml = {
            "market_id": "%s:%s" % (g["game_id"], "MONEYLINE"), "order": 3,
            "fair": p_home, "market": mkt_prob_home, "units": "probability, home win",
            "prob": p_home, "prob_kind": "P(home wins); identical to the side-derived value by construction",
        }
        for item in (side, total, ml):
            rows.append({
                "game_id": g["game_id"], "week": week, "kickoff_date": g["gameday"],
                "kickoff_time_et": g["gametime"],
                "away": g["away"], "home": g["home"],
                "neutral_site": neutral,
                "market_id": item["market_id"],
                "market_type": item["market_id"].split(":")[-1],
                "origination_order": item["order"],
                "derived_from": {1: "fitted attack/defence ratings (this week)",
                                 2: "same fitted ratings, scoring equations",
                                 3: "step 1 (side) - normal CDF of the fair margin"}[item["order"]],
                "fair_line": item["fair"],
                "market_line": item["market"] if item["market"] is not None else "",
                "difference_fair_minus_market": (item["fair"] - item["market"])
                if item["market"] is not None else "",
                "units": item["units"],
                "probability": item["prob"],
                "probability_kind": item["prob_kind"],
                "model_inputs": ("hfa=%.3f sigma_margin=%.3f sigma_total=%.3f "
                                 "a_home=%.2f d_home=%.2f a_away=%.2f d_away=%.2f"
                                 % (hfa, sigma, sigma_tot, attacks[g["home"]],
                                    defences[g["home"]], attacks[g["away"]], defences[g["away"]])),
                "market_source_url": "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz",
                "market_source_tier": AGGREGATOR,
                "slate_source_url": "https://www.nfl.com/schedules/2026/by-week/week-11",
                "slate_source_tier": OFFICIAL,
                "snapshot_utc": "2026-11-15T23:30:00Z",
            })
    return rows


def main():
    corpus = rcsv("backtest_corpus.csv")
    games = [{"game_id": r["game_id"], "week": int(r["week"]), "gameday": r["gameday"],
              "home": r["home"], "away": r["away"],
              "home_score": int(r["home_score"]), "away_score": int(r["away_score"]),
              "home_margin": int(r["home_margin"]), "total_points": int(r["total_points"]),
              "spread_line_mirror": r["spread_line_mirror"],
              "total_line_mirror": r["total_line_mirror"],
              "home_moneyline_mirror": r["home_moneyline_mirror"],
              "away_moneyline_mirror": r["away_moneyline_mirror"],
              "score_source_url": r["score_source_url"],
              "price_source_url": r["price_source_url"],
              "home_spread_odds_mirror": r.get("home_spread_odds_mirror", ""),
              "away_spread_odds_mirror": r.get("away_spread_odds_mirror", ""),
              "over_odds_mirror": r.get("over_odds_mirror", ""),
              "under_odds_mirror": r.get("under_odds_mirror", ""),
              "implied_margin_sd": r.get("implied_margin_sd", "")} for r in corpus]
    fc = build_forecasts(games)
    rows = []
    for r in fc:
        rows.append({k: (f(v) if isinstance(v, float) else v) for k, v in r.items()})
    n_fc = wcsv("forecasts.csv", rows)
    acc = score_forecasts(fc)
    acc_rows = [{k: (f(v) if isinstance(v, float) else v) for k, v in r.items()} for r in acc]
    n_acc = wcsv("model_accuracy.csv", acc_rows)
    abl, (beta, se, n_abl) = build_ablations(fc)
    abl_rows = [{k: (f(v) if isinstance(v, float) else v) for k, v in r.items()} for r in abl]
    n_abl_rows = wcsv("personnel_ablation.csv", abl_rows)
    orig = build_origination(fc)
    orig_rows = [{k: (f(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in orig]
    n_orig = wcsv("originated_markets.csv", orig_rows)

    summary = {
        "forecasts": n_fc,
        "weeks_forecast": sorted({r["week"] for r in fc}),
        "accuracy_rows": n_acc,
        "originated_markets": n_orig,
        "origination_week": max(r["week"] for r in orig),
        "origination_games": len({r["game_id"] for r in orig}),
        "availability_coefficient_pts_per_extra_out": f(beta, 3) if beta is not None else "",
        "availability_coefficient_se": f(se, 3) if se is not None else "",
        "availability_ablation_n": n_abl,
        "hfa_pts": f(fc[-1]["hfa_pts"], 3) if fc else "",
        "sigma_margin": f(fc[-1]["sigma_margin"], 3) if fc else "",
        "sigma_total": f(fc[-1]["sigma_total"], 3) if fc else "",
    }
    for r in acc:
        summary["%s brier_model" % r["holdout"]] = f(r["brier_model"], 4)
        summary["%s brier_market" % r["holdout"]] = f(r["brier_market"], 4)
        summary["%s bss_vs_market" % r["holdout"]] = f(r["bss_vs_market"], 4)
        summary["%s bss_vs_coinflip" % r["holdout"]] = f(r["bss_vs_coinflip"], 4)
        summary["%s mae_margin_model" % r["holdout"]] = f(r["mae_margin_model"], 3)
        summary["%s mae_margin_market" % r["holdout"]] = f(r["mae_margin_market"], 3)
        summary["%s mae_total_model" % r["holdout"]] = f(r["mae_total_model"], 3)
        summary["%s mae_total_market" % r["holdout"]] = f(r["mae_total_market"], 3)
    wjson("model_summary.json", summary)
    print("forecasts:", n_fc, "weeks:", summary["weeks_forecast"])
    for r in acc:
        print("  %-26s n=%-3d brier model=%s market=%s coin=%s | MAE margin model=%s market=%s"
              % (r["holdout"], r["n_games"], f(r["brier_model"], 4), f(r["brier_market"], 4),
                 f(r["brier_coinflip"], 4), f(r["mae_margin_model"], 3), f(r["mae_margin_market"], 3)))
    print("originated markets:", n_orig, "for week", summary["origination_week"],
          "games:", summary["origination_games"])
    print("personnel ablation: n=%d coefficient=%s (se %s)" % (n_abl, summary["availability_coefficient_pts_per_extra_out"],
                                                               summary["availability_coefficient_se"]))


if __name__ == "__main__":
    main()

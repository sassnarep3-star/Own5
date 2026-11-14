"""Own-line origination engine (session d38e90c5).

The model originates its OWN NFL lines from officially sourced numbers only:
  * official standings (W-L-T, PF, PA)                    -> raw_inputs.STANDINGS
  * official final scores for every completed game        -> raw_inputs.RESULTS
  * official Week 10 injury report and club depth charts   -> injuries_raw / depth_raw

Nothing in this module reads a betting price. NFL.com does not publish spreads,
totals or moneylines and no primary operator price feed was reachable from this
environment, so every market-price field (market line, market price, CLV, ROI)
is emitted as blank and flagged rather than estimated.

Model (every parameter is explicit and printed into the published artefacts):

  1. Team ratings by alternating least squares on the official final scores.

       expected_home = L + HFA/2 + off_home - def_away
       expected_away = L - HFA/2 + off_away - def_home

     off_t = points scored above the league mean (offensive rating)
     def_t = points conceded above the league mean (defensive rating)
     L     = league points per team per game from the official results
     HFA   = HOME_FIELD_POINTS (model assumption, not an official statistic)
     The off/def parameters are re-centred after every sweep so that the
     weighted league mean of each is exactly zero.

  2. Shrinkage toward the league mean (small-sample protection):
       w(t) = G(t) / (G(t) + SHRINKAGE_K),  off_s = w*off, def_s = w*def

  3. Probability calibration. Two estimators are used and both are produced
     walk-forward:
       logistic : p(home) = 1 / (1 + exp(-(a + b * margin))) with a,b fitted on
                  the model's own earlier out-of-sample predictions.
       normal  : p(home) = Phi(margin / SIGMA) with SIGMA the SD of the earlier
                  out-of-sample margin residuals (used until 20 out-of-sample
                  predictions exist, which is the minimum needed to fit a,b).
     The total market uses the same residual scale with a normal model.

  4. Lines
       spread : home line = -round_half(margin)
       total  : round_half(expected_home + expected_away)
       moneyline: p(home) from the calibrated model, fair American odds

  5. Backtest discipline: every published backtest number comes from a
     walk-forward loop. Ratings and calibration for week w use ONLY games and
     predictions from weeks < w, so no result ever informs its own prediction.
"""

import math

# ---------------------------------------------------------------- parameters
SHRINKAGE_K = 6.0           # pseudo-games of league-average prior
HOME_FIELD_POINTS = 2.0     # model assumption (points added to the home side)
MIN_HISTORY_GAMES = 3      # games required before a team's rating is used
BACKTEST_FIRST_WEEK = 5    # first week with enough history for walk-forward
LOGISTIC_MIN_TRAIN = 20    # out-of-sample predictions needed to fit a and b
RATING_ITERATIONS = 80     # alternating least-squares sweeps

# Publication order required by the brief: side first, total second,
# moneyline third.
MARKET_ORDER = ("spread", "total", "moneyline")
MARKET_SEQUENCE = {m: i + 1 for i, m in enumerate(MARKET_ORDER)}
MARKET_LABEL = {
    "spread": "Side / spread",
    "total": "Total",
    "moneyline": "Moneyline",
}

PRICE_STATUS = "unavailable_no_primary_price_source"


# ------------------------------------------------------------------ helpers
def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def logistic(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def round_half(x):
    """Round to the nearest half point, ties away from zero."""
    v = math.floor(abs(x) * 2 + 0.5) / 2
    return v if x >= 0 else -v


def american_odds(p):
    """American odds for a two-sided probability p (no vig)."""
    if not (0 < p < 1):
        return None
    if p >= 0.5:
        return int(round(-100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))


def decimal_odds(p):
    if not (0 < p < 1):
        return None
    return round(1.0 / p, 4)


def implied_prob_from_american(odds):
    if odds is None:
        return None
    if odds < 0:
        return round(-odds / (-odds + 100.0), 6)
    return round(100.0 / (odds + 100.0), 6)


# --------------------------------------------------------------- rating core
def _team_rates(results):
    rates = {}
    for _wk, _date, away, home, ap, hp, _sid, _url in results:
        for team, scored, allowed in ((away, ap, hp), (home, hp, ap)):
            r = rates.setdefault(team, {"gp": 0, "pf": 0, "pa": 0})
            r["gp"] += 1
            r["pf"] += scored
            r["pa"] += allowed
    return rates


def league_points_per_team_per_game(results):
    total = 0
    for _wk, _date, away, home, ap, hp, _sid, _url in results:
        total += ap + hp
    return total / (2.0 * len(results)) if results else 0.0


def compute_ratings(results, hfa=HOME_FIELD_POINTS, iterations=RATING_ITERATIONS):
    """Alternating least-squares offensive and defensive ratings."""
    rates = _team_rates(results)
    if not rates:
        return {}
    league_ppg = league_points_per_team_per_game(results)
    teams = list(rates)
    off = {t: 0.0 for t in teams}
    dfn = {t: 0.0 for t in teams}

    for _ in range(iterations):
        for t in teams:
            num = 0.0
            den = 0
            for _wk, _date, away, home, ap, hp, _sid, _url in results:
                if away == t:
                    num += ap - (league_ppg - hfa / 2.0) + dfn[home]
                    den += 1
                elif home == t:
                    num += hp - (league_ppg + hfa / 2.0) + dfn[away]
                    den += 1
            if den:
                off[t] = num / den
        for t in teams:
            num = 0.0
            den = 0
            for _wk, _date, away, home, ap, hp, _sid, _url in results:
                if away == t:
                    num += (league_ppg + hfa / 2.0) + off[home] - hp
                    den += 1
                elif home == t:
                    num += (league_ppg - hfa / 2.0) + off[away] - ap
                    den += 1
            if den:
                dfn[t] = num / den
        # re-centre: weighted league means of off and def are exactly zero
        wsum = sum(rates[t]["gp"] for t in teams) or 1
        moff = sum(off[t] * rates[t]["gp"] for t in teams) / wsum
        mdef = sum(dfn[t] * rates[t]["gp"] for t in teams) / wsum
        for t in teams:
            off[t] -= moff
            dfn[t] -= mdef

    ratings = {}
    for t in teams:
        r = rates[t]
        gp = r["gp"]
        w = gp / (gp + SHRINKAGE_K)
        ratings[t] = {
            "gp": gp,
            "pf": r["pf"],
            "pa": r["pa"],
            "off_adj": round(off[t], 4),
            "def_adj": round(dfn[t], 4),
            "off_s": round(off[t] * w, 4),
            "def_s": round(dfn[t] * w, 4),
            "weight": round(w, 4),
            "usable": gp >= MIN_HISTORY_GAMES,
            "note": "" if gp >= MIN_HISTORY_GAMES else "fewer than %d games" % MIN_HISTORY_GAMES,
        }
    return ratings


def expected_matchup(ratings, home, away, league_ppg, hfa=HOME_FIELD_POINTS):
    rh = ratings.get(home, {"off_s": 0.0, "def_s": 0.0, "usable": False})
    ra = ratings.get(away, {"off_s": 0.0, "def_s": 0.0, "usable": False})
    exp_home = league_ppg + hfa / 2.0 + rh["off_s"] - ra["def_s"]
    exp_away = league_ppg - hfa / 2.0 + ra["off_s"] - rh["def_s"]
    margin = exp_home - exp_away
    total = exp_home + exp_away
    return {
        "exp_home": exp_home,
        "exp_away": exp_away,
        "margin": margin,
        "total": total,
        "home_usable": bool(rh.get("usable")),
        "away_usable": bool(ra.get("usable")),
    }


# ------------------------------------------------------------- calibration
def fit_logistic(pairs):
    """Newton-Raphson fit of p(y=1) = logistic(a + b*x). pairs = [(x, y)]."""
    if len(pairs) < LOGISTIC_MIN_TRAIN:
        return None
    a, b = 0.0, 0.05
    for _ in range(80):
        g0 = g1 = 0.0
        h00 = h01 = h11 = 1e-9
        for x, y in pairs:
            p = logistic(a + b * x)
            r = y - p
            w = p * (1 - p)
            g0 += r
            g1 += r * x
            h00 += w
            h01 += w * x
            h11 += w * x * x
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            break
        da = (h11 * g0 - h01 * g1) / det
        db = (h00 * g1 - h01 * g0) / det
        a += da
        b += db
        if abs(da) < 1e-9 and abs(db) < 1e-9:
            break
    return {"a": round(a, 6), "b": round(b, 6), "n": len(pairs)}


def residual_sigma(preds, key="margin"):
    res = [p["margin"] - p["pred_margin"] for p in preds
           if p["home_usable"] and p["away_usable"]]
    if len(res) < 2:
        return None, len(res)
    mean = sum(res) / len(res)
    var = sum((r - mean) ** 2 for r in res) / (len(res) - 1)
    return math.sqrt(var), len(res)


def total_residual_sigma(preds):
    res = [p["total_pts"] - p["pred_total"] for p in preds
           if p["home_usable"] and p["away_usable"]]
    if len(res) < 2:
        return None, len(res)
    mean = sum(res) / len(res)
    var = sum((r - mean) ** 2 for r in res) / (len(res) - 1)
    return math.sqrt(var), len(res)


def margin_sd(results):
    """SD of official final margins in the supplied games (an officially sourced scale)."""
    if len(results) < 2:
        return None
    vals = [g[5] - g[4] for g in results]
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / (len(vals) - 1)
    return math.sqrt(var)


def probability_model(train_preds, fallback_sigma=None):
    """Return a callable margin -> p(home wins) plus a description.

    The logistic calibration is fitted on the model's own earlier out-of-sample
    predictions. Until enough of those exist (LOGISTIC_MIN_TRAIN) the model
    falls back to a normal mapping scaled by the SD of official final margins.
    """
    pairs = [(p["pred_margin"], 1 if p["margin"] > 0 else 0) for p in train_preds
             if p["home_usable"] and p["away_usable"]]
    fit = fit_logistic(pairs)
    sigma, n = residual_sigma(train_preds)
    if fit is not None:
        def prob(margin, _fit=fit):
            return logistic(_fit["a"] + _fit["b"] * margin)
        return prob, {"mode": "logistic", "a": fit["a"], "b": fit["b"], "train_n": fit["n"],
                      "sigma": round(sigma, 4) if sigma else "",
                      "fallback_sigma": round(fallback_sigma, 4) if fallback_sigma else ""}
    if fallback_sigma:
        def prob(margin, _s=fallback_sigma):
            return norm_cdf(margin / _s)
        return prob, {"mode": "normal", "a": "", "b": "", "train_n": n,
                      "sigma": round(sigma, 4) if sigma else "",
                      "fallback_sigma": round(fallback_sigma, 4)}
    def prob(margin):
        return 0.5
    return prob, {"mode": "no_history", "a": "", "b": "", "train_n": 0, "sigma": ""}


# ------------------------------------------------------------ walk-forward
def walk_forward_predictions(results, first_week=BACKTEST_FIRST_WEEK):
    """Out-of-sample predictions, week by week, using only earlier data."""
    weeks = sorted({g[0] for g in results})
    preds = []
    for w in weeks:
        if w < first_week:
            continue
        history = [g for g in results if g[0] < w]
        if not history:
            continue
        ratings = compute_ratings(history)
        league_ppg = league_points_per_team_per_game(history)
        prob, cal = probability_model(preds, margin_sd(history))
        for wk, date, away, home, ap, hp, sid, url in results:
            if wk != w:
                continue
            mu = expected_matchup(ratings, home, away, league_ppg)
            preds.append({
                "week": wk, "date": date, "away": away, "home": home,
                "away_pts": ap, "home_pts": hp,
                "margin": hp - ap, "total_pts": ap + hp,
                "pred_margin": round(mu["margin"], 4),
                "pred_total": round(mu["total"], 4),
                "pred_home_pts": round(mu["exp_home"], 4),
                "pred_away_pts": round(mu["exp_away"], 4),
                "p_home": round(prob(mu["margin"]), 6),
                "calibration_mode": cal["mode"],
                "calibration_train_n": cal["train_n"],
                "home_usable": mu["home_usable"],
                "away_usable": mu["away_usable"],
                "source_id": sid, "source_url": url,
            })
    return preds


# --------------------------------------------------------------- origination
def originate_game(ratings, league_ppg, home, away, prob_home, sigma, game_id, week, date,
                    kickoff, network, source_url, venue=""):
    """Originate the three markets for one game in the required publish order."""
    mu = expected_matchup(ratings, home, away, league_ppg)
    margin = mu["margin"]
    total = mu["total"]
    p_home = prob_home(margin)
    p_away = 1.0 - p_home
    spread_line = round_half(-margin)          # home team line
    total_line = round_half(total)
    p_over = 1.0 - norm_cdf((total_line - total) / sigma) if sigma else 0.5
    note = ("" if (mu["home_usable"] and mu["away_usable"])
            else "one or both clubs below minimum history")
    common = {
        "game_id": game_id, "week": week, "date": date, "kickoff": kickoff,
        "network": network, "venue": venue, "away": away, "home": home,
        "market_line": "", "market_price": "", "difference": "",
        "market_price_status": PRICE_STATUS, "model_rating_note": note,
        "source_url": source_url,
    }

    rows = [{
        **common,
        "market": "spread", "market_label": MARKET_LABEL["spread"],
        "publish_seq": MARKET_SEQUENCE["spread"],
        "side": f"{home} {spread_line:+.1f}" if spread_line else f"{home} 0",
        "model_fair_line": f"{spread_line:+.1f}",
        "model_fair_prob": round(p_home, 4),
        "model_fair_price": american_odds(p_home),
    }, {
        **common,
        "market": "total", "market_label": MARKET_LABEL["total"],
        "publish_seq": MARKET_SEQUENCE["total"],
        "side": f"Over {total_line:.1f}",
        "model_fair_line": f"{total_line:.1f}",
        "model_fair_prob": round(p_over, 4),
        "model_fair_price": american_odds(p_over),
    }, {
        **common,
        "market": "moneyline", "market_label": MARKET_LABEL["moneyline"],
        "publish_seq": MARKET_SEQUENCE["moneyline"],
        "side": f"{home} {american_odds(p_home)}",
        "model_fair_line": f"{home} {american_odds(p_home)}",
        "model_fair_prob": round(p_home, 4),
        "model_fair_price": american_odds(p_home),
    }]
    return rows


def game_id_for(week, away, home):
    return f"W{week:02d}-{away}-at-{home}"

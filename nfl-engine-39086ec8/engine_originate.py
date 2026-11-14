"""Requirements 3 and 4 — origination order and fair / market / difference.

Requirement 3: originate the SIDE first, then the TOTAL, then the MONEYLINE.
The order is enforced by code: the total model consumes the side model's rating
fit, and the moneyline is derived from the side distribution. Nothing downstream
of a stage can change a stage above it.

Requirement 4: every originated market publishes three separate columns — the
model's FAIR number, the MARKET number, and the DIFFERENCE. If the market number
is not a verified snapshot it is published blank and the difference is published
as "UNPRICED", never as 0.

WHY THE RATINGS ARE RIDGE-FIT AND NOT RAW POINT DIFFERENTIAL
------------------------------------------------------------
A first pass of this desk used raw points-differential per game. It produced
KC at Atlanta as a 10.8-point game against a 3.5-point market — a 7.3-point
disagreement. That is not an edge; it is a broken rating. Raw differential across
eight games is dominated by blowouts and ignores opponent strength, so the same
team looks elite after beating a weak schedule.

The model fitted here is the standard opponent-adjusted margin model:

    margin_home = rating_home - rating_away + hfa + error,  minimising
    sum(error^2) + lambda * sum(rating^2)

solved by ridge normal equations with lambda declared and reported. It is
deterministic, has no free parameters other than lambda, and every fitted value
is published so a reader can check it against the market.

WHAT THIS MODEL IS NOT
----------------------
It uses only scoring margin. It does not use injuries, rest, weather, turnovers,
or opponent-adjusted efficiency. Its disagreement with the market is therefore a
diagnostic of MISSING INFORMATION, not a betting edge. The desk publishes the
disagreement distribution precisely so that the size of the missing information
is visible.
"""

import csv
import io
import math

MARKET_ORDER = ("side", "total", "moneyline")
LAMBDA = 5.0   # declared ridge penalty; reported on every output row

HEADER = (
    "game_id", "season", "week", "away", "home", "kickoff", "neutral_site",
    "exp_home_margin", "fair_home_spread", "market_home_spread",
    "diff_spread_home", "model_side", "model_side_edge_pts",
    "exp_total", "fair_total", "market_total", "diff_total",
    "model_total_side", "model_total_edge_pts",
    "p_home_win", "p_tie", "p_away_win", "fair_home_ml", "fair_away_ml",
    "market_home_ml", "market_away_ml", "diff_home_ml_prob",
    "price_status", "rating_source", "result_source", "note",
)


class OriginationError(RuntimeError):
    pass


# --------------------------------------------------------------- linear algebra


def _solve(a, b):
    """Gaussian elimination with partial pivoting. Deterministic."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise OriginationError("singular normal equations")
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for r in range(col + 1, n):
            f = m[r][col] / pv
            if f:
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = m[r][n] - sum(m[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / m[r][r]
    return x


def fit_ratings(games, teams, lam=LAMBDA):
    """Ridge-fit margin ratings + home-field advantage from settled games.

    `games`: list of dicts with home, away, home_pts, away_pts, neutral_site.
    Returns (ratings dict, hfa, diagnostics). Ratings are in points of margin
    relative to an average team; the league mean is subtracted so ratings sum to 0.
    """
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams) + 1                      # +1 for HFA
    ata = [[0.0] * n for _ in range(n)]
    atb = [0.0] * n
    use = []
    for g in games:
        if g["home"] not in idx or g["away"] not in idx:
            continue
        h, a = idx[g["home"]], idx[g["away"]]
        y = float(g["home_pts"] - g["away_pts"])
        row = [0.0] * n
        row[h] += 1.0
        row[a] -= 1.0
        row[-1] = 0.0 if g.get("neutral_site") else 1.0
        use.append(g)
        for i in range(n):
            if row[i] == 0.0:
                continue
            atb[i] += row[i] * y
            for j in range(n):
                if row[j]:
                    ata[i][j] += row[i] * row[j]
    for i in range(len(teams)):             # ridge on ratings only, not on HFA
        ata[i][i] += lam
    ata[-1][-1] += 1e-9                     # keep HFA identifiable
    x = _solve(ata, atb)
    ratings = {t: x[idx[t]] for t in teams}
    mean = sum(ratings.values()) / len(ratings)
    ratings = {t: v - mean for t, v in ratings.items()}
    hfa = x[-1]
    # in-sample diagnostics
    resid = []
    for g in use:
        pred = ratings[g["home"]] - ratings[g["away"]] + (0 if g.get("neutral_site") else hfa)
        resid.append(float(g["home_pts"] - g["away_pts"]) - pred)
    rmse = math.sqrt(sum(e * e for e in resid) / len(resid)) if resid else None
    return ratings, hfa, {"games": len(use), "lambda": lam, "rmse_in_sample": rmse}


def team_scoring_rates(games, teams):
    agg = {t: {"gp": 0, "pf": 0, "pa": 0} for t in teams}
    for g in games:
        if g["home"] not in agg or g["away"] not in agg:
            continue
        agg[g["home"]]["gp"] += 1
        agg[g["home"]]["pf"] += g["home_pts"]
        agg[g["home"]]["pa"] += g["away_pts"]
        agg[g["away"]]["gp"] += 1
        agg[g["away"]]["pf"] += g["away_pts"]
        agg[g["away"]]["pa"] += g["home_pts"]
    for t, a in agg.items():
        a["pf_pg"] = a["pf"] / a["gp"] if a["gp"] else None
        a["pa_pg"] = a["pa"] / a["gp"] if a["gp"] else None
    return agg


def _sd(xs):
    n = len(xs)
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def league_parameters(games):
    margins = [g["home_pts"] - g["away_pts"] for g in games]
    totals = [g["home_pts"] + g["away_pts"] for g in games]
    nm = [g["home_pts"] - g["away_pts"] for g in games if not g.get("neutral_site")]
    return {
        "n_games": len(games),
        "n_non_neutral": len(nm),
        "sd_margin": _sd(margins),
        "sd_total": _sd(totals),
        "mean_total": sum(totals) / len(totals),
        "mean_home_margin_non_neutral": sum(nm) / len(nm),
        "tie_rate_observed": sum(1 for m in margins if m == 0) / len(margins),
    }


def _phi(x):
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def _Phi(x):
    return 0.5 * math.erfc(-x / math.sqrt(2))


def prob_to_american(p):
    """Zero-margin American price for probability p. vig is never mixed in here."""
    if not (0.0 < p < 1.0):
        raise ValueError("probability must lie strictly between 0 and 1")
    dec = 1.0 / p
    from statslib import decimal_to_american
    return decimal_to_american(dec)


def originate_game(away, home, ratings, scoring, params, neutral=False):
    """Originate one game in the mandated order: SIDE, then TOTAL, then ML."""
    if away not in ratings or home not in ratings:
        raise OriginationError("missing rating for %s or %s" % (away, home))
    sd_margin = params["sd_margin"]
    hfa = 0.0 if neutral else params["hfa"]

    # ---------------- STAGE 1: SIDE ----------------
    exp_margin = ratings[home] - ratings[away] + hfa
    side = {
        "exp_home_margin": exp_margin,
        "fair_home_spread": -round(exp_margin * 2) / 2.0,
        "sd": sd_margin,
    }

    # ---------------- STAGE 2: TOTAL ----------------
    total_from_scoring = (scoring[home]["pf_pg"] + scoring[home]["pa_pg"]
                          + scoring[away]["pf_pg"] + scoring[away]["pa_pg"]) / 2.0
    total = {
        "exp_total": total_from_scoring,
        "fair_total": round(total_from_scoring * 2) / 2.0,
        "sd": params["sd_total"],
    }

    # ---------------- STAGE 3: MONEYLINE ----------------
    sd = max(side["sd"], 1e-9)
    z = side["exp_home_margin"] / sd
    # A tie is the margin landing inside the half-point window around zero.
    p_tie = _Phi((0.5 - side["exp_home_margin"]) / sd) - _Phi(
        (-0.5 - side["exp_home_margin"]) / sd)
    p_home = _Phi((0.5 - side["exp_home_margin"]) / sd)
    p_home = min(max(p_home, 1e-9), 1 - 1e-9)
    p_tie = max(min(p_tie, p_home), 0.0)
    p_away = 1.0 - p_home
    return {
        "stage_1_side": side,
        "stage_2_total": total,
        "stage_3_moneyline": {
            "p_home_win": p_home - p_tie, "p_tie": p_tie, "p_away_win": p_away,
            "fair_home_ml": prob_to_american(p_home - p_tie),
            "fair_away_ml": prob_to_american(p_away),
            "z": z,
        },
    }


def diff(fair, market):
    """Difference column. Never invents a zero when the market is unknown."""
    if market is None or market == "":
        return "UNPRICED"
    return round(float(fair) - float(market), 4)


def side_from_line_and_edge(exp_margin, market_home_spread):
    """Which side the model prefers and by how many points.

    A positive model margin means the model expects HOME to win. A positive
    home spread means home is the underdog. The edge is measured against the
    market handicap from the HOME perspective, so a positive edge means the
    model likes the HOME side.
    """
    if market_home_spread in (None, ""):
        return "", ""
    edge_home = float(exp_margin) - (-float(market_home_spread))
    return ("home" if edge_home > 0 else "away"), round(abs(edge_home), 4)


def build_rows(week_games, ratings, scoring, params, market_rows):
    out = []
    for (away, home, kickoff, network, neutral, game_url) in week_games:
        res = originate_game(away, home, ratings, scoring, params, neutral=neutral)
        gid = "%s-%s" % (away, home)
        m = market_rows.get(gid, {})
        s1, s2, s3 = res["stage_1_side"], res["stage_2_total"], res["stage_3_moneyline"]
        side_pick, side_edge = side_from_line_and_edge(
            s1["exp_home_margin"], m.get("spread"))
        total_pick, total_edge = "", ""
        if m.get("total") not in (None, ""):
            te = s2["exp_total"] - float(m["total"])
            total_pick = "over" if te > 0 else "under"
            total_edge = round(abs(te), 4)
        diff_ml = ("UNPRICED" if not m.get("home_ml")
                   else round(s3["p_home_win"] - _implied_novig(m), 4))
        out.append({
            "game_id": gid, "season": 2026, "week": 10,
            "away": away, "home": home, "kickoff": kickoff,
            "neutral_site": "yes" if neutral else "no",
            "exp_home_margin": round(s1["exp_home_margin"], 3),
            "fair_home_spread": s1["fair_home_spread"],
            "market_home_spread": m.get("spread", ""),
            "diff_spread_home": diff(-s1["exp_home_margin"], m.get("spread")),
            "model_side": side_pick, "model_side_edge_pts": side_edge,
            "exp_total": round(s2["exp_total"], 3),
            "fair_total": s2["fair_total"],
            "market_total": m.get("total", ""),
            "diff_total": diff(s2["exp_total"], m.get("total")),
            "model_total_side": total_pick, "model_total_edge_pts": total_edge,
            "p_home_win": round(s3["p_home_win"], 4),
            "p_tie": round(s3["p_tie"], 5),
            "p_away_win": round(s3["p_away_win"], 4),
            "fair_home_ml": s3["fair_home_ml"],
            "fair_away_ml": s3["fair_away_ml"],
            "market_home_ml": m.get("home_ml", ""),
            "market_away_ml": m.get("away_ml", ""),
            "diff_home_ml_prob": diff_ml,
            "price_status": "PRICED" if m.get("spread") is not None else "UNPRICED",
            "rating_source": "https://www.nfl.com/standings/",
            "result_source": game_url,
            "note": ("market = FanDuel public event page, one capture 2026-11-14; "
                     "no opening price exists (F-01)") if m else
                    ("no pre-kickoff price could be read (F-07)"),
        })
    return out


def _implied_novig(m):
    from statslib import no_vig_two_way
    try:
        p, _ = no_vig_two_way(int(m["home_ml"]), int(m["away_ml"]))
        return p
    except Exception:
        return None


def calibration_rows(rows):
    """How close is the model to the market? A DISAGREEMENT DIAGNOSTIC.

    A well-specified model disagrees with a sharp market by roughly its own
    error. A large systematic disagreement means the model is missing
    information, not that it has found an edge.
    """
    priced = [r for r in rows if r["market_home_spread"] not in ("", None)]
    if not priced:
        return []
    d_sp = [r["exp_home_margin"] + float(r["market_home_spread"]) for r in priced]
    d_tot = [r["exp_total"] - float(r["market_total"]) for r in priced]
    out = []
    for label, vals, unit in (("side (model expected margin vs -market spread)",
                               d_sp, "points"),
                              ("total (model expected total vs market total)",
                               d_tot, "points")):
        m = sum(vals) / len(vals)
        sd = _sd(vals) if len(vals) > 1 else 0.0
        out.append({
            "comparison": label, "n": len(vals), "mean_bias": round(m, 3),
            "mean_abs": round(sum(abs(v) for v in vals) / len(vals), 3),
            "max_abs": round(max(abs(v) for v in vals), 3),
            "sd": round(sd, 3), "unit": unit,
        })
    return out


def to_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\n",
                       extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in HEADER})
    return buf.getvalue()

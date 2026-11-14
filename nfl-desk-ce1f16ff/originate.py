"""Line origination in the mandated order: SIDE, then TOTAL, then MONEYLINE.

Why an order at all: each stage consumes the previous stage's output instead of
re-fitting the raw data. That makes the sheet auditable - a change to the side
model mechanically moves the total and the moneyline, and ``data/derivation.csv``
records the chain so a reviewer can see what was derived from what.

The common rating core
----------------------
One ridge-regularised least-squares fit per week, two parameters per club
(attacking points, points allowed), an unpenalised intercept and an unpenalised
home-field term. Both equations of a game are fitted:

    home_points = b0 + hfa*(1-neutral) + attack[home] + allowed[away]
    away_points = b0                    + attack[away] + allowed[home]

so the model has one coherent scoring environment rather than two unrelated
halves. It is solved exactly (normal equations + Gaussian elimination in
``statslib.ridge_solve``); no gradient descent, no tuning knobs beyond the two
constants below, which are pre-registered in ``validation.py`` and never
re-selected after seeing a result.

Stage 1 - SIDE       expected margin -> fair home spread at the market's 0.5 tick.
Stage 2 - TOTAL      sum of the two team expectations -> fair total at 0.5.
Stage 3 - MONEYLINE  derived from stage 1's margin distribution only. The spread
                     mass at a tie is taken from the observed tie rate in the
                     results feed and excluded, then the two-sided probability is
                     converted to a no-vig American price.

No look-ahead
-------------
Ratings for a game in week w are fitted on games strictly before week w. There
is no global fit anywhere in this module: a fit that could see the target game
would be worthless as evidence.
"""
from __future__ import annotations

import csv
import datetime
import os

import statslib as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

LAMBDA = 8.0        # ridge strength on attack/allowed, in points per game
PRIOR_SEASONS = 2   # seasons of history carried into a season's fit
PRIOR_WEIGHT = 0.40  # weight of each prior-season game (current season = 1.0)
TICK = 0.5

COLS = 2 + 32 + 32   # intercept, hfa, attack x32, allowed x32
TEAMS = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB",
         "HOU", "IND", "JAX", "KC", "LAR", "LV", "LAC", "MIA", "MIN", "NE", "NO", "NYG",
         "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS"]
TIX = {t: i for i, t in enumerate(TEAMS)}
A_COL = {t: 2 + TIX[t] for t in TEAMS}
D_COL = {t: 2 + 32 + TIX[t] for t in TEAMS}


def _d(s):
    return datetime.date.fromisoformat(s[:10]) if s else None


class Ratings:
    """A fitted scoring model. ``fit`` is exact; ``predict`` returns margin and total."""

    def __init__(self, games):
        self.n = len(games)
        self.b = [0.0] * COLS
        self.sigma = 13.0
        self.sumatt = 0.0
        if games:
            self._fit(games)

    def _rows(self, games):
        """Sparse design rows: (weight, [(col, value), ...], y)."""
        for g in games:
            wt = g.get("wt", 1.0)
            if wt <= 0:
                continue
            hfa_h = 0.0 if g.get("neutral") else 1.0
            nh, na = g["home"], g["away"]
            yield (wt, [(0, 1.0), (1, hfa_h), (A_COL[nh], 1.0), (D_COL[na], 1.0)], float(g["home_pts"]))
            yield (wt, [(0, 1.0), (1, 0.0), (A_COL[na], 1.0), (D_COL[nh], 1.0)], float(g["away_pts"]))

    def _fit(self, games):
        xtx = {}
        xty = [0.0] * COLS
        sw = 0.0
        for wt, terms, y in self._rows(games):
            sw += wt
            for a, va in terms:
                xty[a] += wt * va * y
                xtx[(a, a)] = xtx.get((a, a), 0.0) + wt * va * va
                for b, vb in terms:
                    if not (a < b):
                        continue          # each unordered pair once; a > b is the mirror entry
                    xtx[(a, b)] = xtx.get((a, b), 0.0) + wt * va * vb
        A = [[0.0] * COLS for _ in range(COLS)]
        for (i, j), v in xtx.items():
            A[i][j] = v
            if i != j:
                A[j][i] = v
        for i in range(2, COLS):
            A[i][i] += LAMBDA
        sol = st.solve(A, xty)
        if sol is None:
            return
        self.b = sol
        # residual scale of one team's points (weighted, df-corrected)
        num = num2 = den = 0.0
        for wt, terms, y in self._rows(games):
            pred = sum(self.b[c] * v for c, v in terms)
            e = y - pred
            num += wt * e
            num2 += wt * e * e
            den += wt
        if den > 1:
            mean = num / den
            self.sigma = max(4.0, (max(0.0, num2 / den - mean * mean) * den / (den - 1)) ** 0.5)
        self.n_rows = int(den)

    # -- predictions ------------------------------------------------------
    def predict(self, home, away, neutral=False):
        eh = self.b[0] + (0.0 if neutral else self.b[1]) + self.b[A_COL[home]] + self.b[D_COL[away]]
        ea = self.b[0] + self.b[A_COL[away]] + self.b[D_COL[home]]
        return dict(home_pts=eh, away_pts=ea, margin=eh - ea, total=eh + ea,
                    sd_points=self.sigma, sd_margin=(2 ** 0.5) * self.sigma,
                    sd_total=(2 ** 0.5) * self.sigma)

    def table(self):
        out = []
        for t in TEAMS:
            out.append(dict(team=t, attack=round(self.b[A_COL[t]], 3), allowed=round(self.b[D_COL[t]], 3),
                            net=round(self.b[A_COL[t]] - self.b[D_COL[t]], 3)))
        out.sort(key=lambda r: -r["net"])
        return out


def round_tick(x):
    return round(x / TICK) * TICK


# ---------------------------------------------------------------------------
# data plumbing
# ---------------------------------------------------------------------------
def feed_games():
    rows = []
    p = os.path.join(DATA, "results_feed.csv")
    with open(p, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(dict(week=int(r["week"]), date=r["date"], away=r["away"], home=r["home"],
                             home_pts=int(r["home_pts"]) if r["home_pts"] else None,
                             away_pts=int(r["away_pts"]) if r["away_pts"] else None,
                             neutral=(r["neutral"] == "True"), status=r["status"],
                             game_key=r["game_key"], official_url=r["official_url"]))
    return rows


def mirror_games(seasons):
    """Prior seasons from the pinned mirror. Labelled AGGREGATOR wherever used."""
    import inputs
    out = []
    for g in inputs.read_gz_csv(inputs.PINNED["nflverse_games"]):
        if g.get("season") not in seasons or g.get("game_type") != "REG":
            continue
        if not (g.get("away_score") or "").strip():
            continue
        if g["away_team"] not in TIX or g["home_team"] not in TIX:
            continue
        out.append(dict(week=int(g["week"]), date=g["gameday"], away=g["away_team"], home=g["home_team"],
                        home_pts=int(g["home_score"]), away_pts=int(g["away_score"]),
                        neutral=False, status="FINAL", wt=PRIOR_WEIGHT, season=g["season"],
                        spread_line=(float(g["spread_line"]) if (g.get("spread_line") or "").strip() else None),
                        total_line=(float(g["total_line"]) if (g.get("total_line") or "").strip() else None),
                        home_spread_odds=g.get("home_spread_odds", ""),
                        away_spread_odds=g.get("away_spread_odds", ""),
                        over_odds=g.get("over_odds", ""), under_odds=g.get("under_odds", ""),
                        home_moneyline=g.get("home_moneyline", ""), away_moneyline=g.get("away_moneyline", ""),
                        game_key=f"{g['away_team']}@{g['home_team']}-{g['season']}-w{g['week']}"))
    return out


def tie_rate(games):
    fin = [g for g in games if g.get("status") == "FINAL"]
    if not fin:
        return 0.0, 0
    return sum(1 for g in fin if g["home_pts"] == g["away_pts"]) / len(fin), len(fin)


# ---------------------------------------------------------------------------
# the three stages
# ---------------------------------------------------------------------------
def stage_side(rat, home, away, neutral):
    p = rat.predict(home, away, neutral)
    spread = round_tick(-p["margin"])
    z = (0.0 - p["margin"]) / p["sd_margin"]
    return dict(model_expected_margin_home=round(p["margin"], 2),
                model_sd_margin=round(p["sd_margin"], 2),
                fair_spread_home=round(spread, 1),
                model_p_home_cover_fair=round(st.norm_cdf(-spread / p["sd_margin"]), 4),
                model_p_home_su=round(1.0 - st.norm_cdf(z), 4),
                stage1_inputs=f"{rat.n} games fitted strictly before kickoff; lambda={LAMBDA}")


def stage_total(rat, home, away, neutral, side):
    p = rat.predict(home, away, neutral)
    fair = round_tick(p["total"])
    return dict(fair_total=round(fair, 1), model_expected_total=round(p["total"], 2),
                model_sd_total=round(p["sd_total"], 2),
                fair_home_points=round(p["home_pts"], 2), fair_away_points=round(p["away_pts"], 2),
                stage2_reuses_stage1_margin_pts=round(abs((p["home_pts"] - p["away_pts"])
                                                          - side["model_expected_margin_home"]), 2),
                stage2_inputs="sum of the same two team expectations that produced stage 1")


def stage_moneyline(side, total, tie_frac, sd):
    """Moneyline from stage 1's margin distribution; tie mass removed, no re-fit."""
    mu = side["model_expected_margin_home"]
    s = max(1e-6, sd)
    p_tie = max(0.0, st.norm_cdf(0.5 / s - mu / s) - st.norm_cdf(-0.5 / s - mu / s))
    p_tie = max(p_tie, tie_frac)
    p_home_raw = 1.0 - st.norm_cdf((0.0 - mu) / s)
    p_away_raw = st.norm_cdf((0.0 - mu) / s)
    denom = max(1e-9, p_home_raw + p_away_raw)
    p_home = p_home_raw / denom * (1.0 - p_tie)
    p_away = 1.0 - p_tie - p_home
    return dict(model_p_tie=round(p_tie, 4), model_p_home_ml=round(p_home, 4),
                model_p_away_ml=round(p_away, 4),
                fair_home_ml=st.prob_to_american(min(0.995, max(0.005, p_home))),
                fair_away_ml=st.prob_to_american(min(0.995, max(0.005, p_away))),
                stage3_inputs="no new fit: derived from stage 1's margin distribution; "
                              "tie mass from the observed tie rate")


# ---------------------------------------------------------------------------
# walk-forward driver
# ---------------------------------------------------------------------------
def build_weekly_models(target_weeks, current, history):
    """Ratings fitted on everything strictly before each target week."""
    models = {}
    for wk in sorted(set(target_weeks)):
        cutoff = min(_d(g["date"]) for g in current if g["week"] == wk and g.get("date"))
        cur = [g for g in current if g["status"] == "FINAL" and g["week"] < wk]
        sea = {g["date"][:4] for g in cur}
        yrs = sorted({_d(g["date"]).year for g in cur if g.get("date")})
        keep = [str(y) for y in yrs[-PRIOR_SEASONS:]] if yrs else []
        hist = [g for g in history if g.get("date") and _d(g["date"]) < cutoff
                and g["season"] in keep]
        models[wk] = Ratings(cur + hist)
    return models


def originate_slate():
    current = feed_games()
    completed = [g for g in current if g["status"] == "FINAL"]
    tr, n = tie_rate(current)
    hist = mirror_games({str(y) for y in (2021, 2022, 2023, 2024, 2025)})
    targets = [g for g in current if g["status"] == "PENDING" and g["week"] in (10, 11)]
    models = build_weekly_models([g["week"] for g in targets], current, hist)
    rows = []
    from pinned import capture as cap
    for g in targets:
        rat = models[g["week"]]
        side = stage_side(rat, g["home"], g["away"], g["neutral"])
        tot = stage_total(rat, g["home"], g["away"], g["neutral"], side)
        ml = stage_moneyline(side, tot, tr, side["model_sd_margin"])
        row = dict(game_key=g["game_key"], week=g["week"], date=g["date"],
                   away=g["away"], home=g["home"], neutral="yes" if g["neutral"] else "no",
                   official_url=g["official_url"], model_games_fitted=rat.n,
                   tie_rate_used=round(tr, 4), tie_rate_n=n, **side, **tot, **ml)
        mk = next((p for p in cap.PRICES if p["game"] == f"{g['away']}@{g['home']}"), None)
        if mk:
            row.update(
                market_spread_home=mk["home_spread"], market_home_spread_price=mk["home_spread_price"],
                market_away_spread_price=mk["away_spread_price"], market_total=mk["total"],
                market_over_price=mk["over_price"], market_under_price=mk["under_price"],
                market_home_ml=mk["home_ml"], market_away_ml=mk["away_ml"],
                market_opening_spread_home=mk["open_spread_home"], market_opening_total=mk["open_total"],
                market_provider=cap.PROVIDER, market_captured_at=cap.CAPTURE_STAMPS["CAP-03"],
                market_source_url=cap.URLS["CAP-03"], market_stage="pre_game")
            row["diff_spread_pts"] = round(row["fair_spread_home"] - mk["home_spread"], 2)
            row["diff_total_pts"] = round(row["fair_total"] - mk["total"], 2)
            pa = st.devig_two_way(st.american_to_prob(mk["away_ml"]), st.american_to_prob(mk["home_ml"]))
            row["market_p_home_novig"] = None if pa[1] is None else round(pa[1], 4)
            row["diff_home_ml_prob"] = ("" if pa[1] is None else round(ml["model_p_home_ml"] - pa[1], 4))
            row["market_hold_pct"] = round(st.hold_pct(st.american_to_prob(mk["away_ml"]),
                                                        st.american_to_prob(mk["home_ml"])), 2)
            row["edge_grade"] = grade_edge(row)
        else:
            row.update(market_spread_home="", market_total="", market_home_ml="", market_away_ml="",
                       market_provider="", market_captured_at="", market_source_url="",
                       market_stage="NOT CAPTURED", market_opening_spread_home="", market_opening_total="",
                       market_home_spread_price="", market_away_spread_price="",
                       market_over_price="", market_under_price="",
                       diff_spread_pts="", diff_total_pts="", market_p_home_novig="",
                       diff_home_ml_prob="", market_hold_pct="",
                       edge_grade="BLANK - no captured price for this game (never filled in)")
        rows.append(row)
    rows.sort(key=lambda r: (r["week"], r["date"], r["game_key"]))
    return rows, models, dict(tie_rate=tr, tie_n=n)


def grade_edge(row):
    """Difference classification. Uses the 0.5 tick, not a feeling."""
    out = []
    for label, key in (("side", "diff_spread_pts"), ("total", "diff_total_pts")):
        v = row.get(key)
        if v == "" or v is None:
            out.append(f"{label}: blank")
            continue
        a = abs(float(v))
        cls = "none" if a < 1.0 else ("small" if a < 2.0 else ("medium" if a < 3.5 else "large"))
        out.append(f"{label}: {cls} ({float(v):+.1f} pts)")
    d = row.get("diff_home_ml_prob")
    if d not in ("", None):
        out.append(f"moneyline: {'+' if float(d) > 0 else ''}{100 * float(d):.1f} prob pts vs no-vig market")
    else:
        out.append("moneyline: blank")
    return "; ".join(out)


def backtest_history(window=("2021", "2022", "2023", "2024", "2025")):
    """Walk-forward predictions for the mirror's completed games, week by week.

    Ratings for a week see that season's earlier weeks plus the two previous
    seasons at reduced weight - the same recipe used for the live slate, so the
    historical numbers describe the model that prices Week 10 rather than a
    different one fitted for the demo.
    """
    hist = mirror_games(set(window))
    by_week = {}
    for g in hist:
        by_week.setdefault((g["season"], g["week"]), []).append(g)
    seasons = sorted(window, key=int)
    out = []
    for si, season in enumerate(seasons):
        priors = []
        for k in range(max(0, si - PRIOR_SEASONS), si):
            priors += [g for g in hist if g["season"] == seasons[k]]
        for wk in range(1, 19):
            games = by_week.get((season, wk))
            if not games:
                continue
            cur = [g for g in hist if g["season"] == season and g["week"] < wk]
            rat = Ratings(cur + priors)
            tr, _ = tie_rate(cur)
            for g in games:
                side = stage_side(rat, g["home"], g["away"], g["neutral"])
                tot = stage_stage = stage_total(rat, g["home"], g["away"], g["neutral"], side)
                ml = stage_moneyline(side, tot, tr, side["model_sd_margin"])
                actual_margin = g["home_pts"] - g["away_pts"]
                actual_total = g["home_pts"] + g["away_pts"]
                out.append(dict(game_key=g["game_key"], season=g["season"], week=wk, date=g["date"],
                                away=g["away"], home=g["home"], games_fitted=rat.n,
                                fair_spread_home=side["fair_spread_home"],
                                model_expected_margin_home=side["model_expected_margin_home"],
                                model_sd_margin=side["model_sd_margin"],
                                model_sd_total=tot["model_sd_total"],
                                model_expected_total=tot["model_expected_total"],
                                fair_total=tot["fair_total"],
                                fair_home_ml=ml["fair_home_ml"], fair_away_ml=ml["fair_away_ml"],
                                model_p_home_su=side["model_p_home_su"],
                                model_p_home_ml=ml["model_p_home_ml"],
                                market_spread_home=g.get("spread_line"),
                                market_total=g.get("total_line"),
                                market_home_spread_price=g.get("home_spread_odds"),
                                market_away_spread_price=g.get("away_spread_odds"),
                                market_over_price=g.get("over_odds"), market_under_price=g.get("under_odds"),
                                market_home_ml=g.get("home_moneyline"), market_away_ml=g.get("away_moneyline"),
                                actual_margin=actual_margin, actual_total=actual_total,
                                actual_home_win=1 if actual_margin > 0 else (0 if actual_margin == 0 else -1),
                                diff_spread_pts=round(side["model_expected_margin_home"] + g["spread_line"], 2)
                                if g.get("spread_line") is not None else "",
                                diff_spread_rounded_pts=round(side["fair_spread_home"] - g["spread_line"], 2)
                                if g.get("spread_line") is not None else "",
                                diff_total_pts=round(tot["fair_total"] - g["total_line"], 2)
                                if g.get("total_line") is not None else "",
                                market_source="nflverse mirror (AGGREGATOR; vintage undocumented)",
                                market_source_url="https://github.com/nflverse/nflverse-data/releases/tag/schedules"))
    out.sort(key=lambda r: (r["season"], int(r["week"]), r["game_key"]))
    return out


def write():
    os.makedirs(DATA, exist_ok=True)
    rows, models, meta = originate_slate()
    cols = ["game_key", "week", "date", "away", "home", "neutral", "official_url",
            "model_games_fitted", "tie_rate_used", "tie_rate_n",
            "model_expected_margin_home", "model_sd_margin", "fair_spread_home",
            "model_p_home_cover_fair", "model_p_home_su", "stage1_inputs",
            "fair_total", "model_expected_total", "model_sd_total", "fair_home_points",
            "fair_away_points", "stage2_reuses_stage1_margin_pts", "stage2_inputs",
            "model_p_tie", "model_p_home_ml", "model_p_away_ml", "fair_home_ml", "fair_away_ml",
            "stage3_inputs",
            "market_provider", "market_stage", "market_captured_at", "market_source_url",
            "market_spread_home", "market_home_spread_price", "market_away_spread_price",
            "market_total", "market_over_price", "market_under_price",
            "market_home_ml", "market_away_ml", "market_opening_spread_home", "market_opening_total",
            "market_hold_pct", "market_p_home_novig",
            "diff_spread_pts", "diff_total_pts", "diff_home_ml_prob", "edge_grade"]
    with open(os.path.join(DATA, "fair_lines.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})

    with open(os.path.join(DATA, "model_ratings.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["week", "rank", "team", "attack_pts", "allowed_pts", "net_pts",
                    "source", "note"])
        for wk, rat in sorted(models.items()):
            for i, r in enumerate(rat.table(), start=1):
                w.writerow([wk, i, r["team"], r["attack"], r["allowed"], r["net"],
                            "computed by nfl-desk-ce1f16ff/originate.py",
                            "fitted on games strictly before this week's kickoffs"])

    bt = backtest_history()
    bcols = list(bt[0].keys()) if bt else []
    with open(os.path.join(DATA, "backtest_predictions.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=bcols)
        w.writeheader()
        w.writerows(bt)

    # derivation register: what each column came from
    der = [
        ("stage 1", "fair_spread_home", "ridge ratings fit on prior games", "-expected margin, rounded to 0.5"),
        ("stage 2", "fair_total", "same fit, sum of team expectations", "no refit; 0.5 tick"),
        ("stage 3", "fair_home_ml / fair_away_ml", "stage-1 margin distribution", "normal on model residual sd; tie mass removed using the observed tie rate; converted at no vig"),
        ("market", "market_* columns", "operator capture (DraftKings via MK-S-04)", "pre-game stage only; opening where the page carries it; blank when it does not"),
        ("difference", "diff_* columns", "fair minus market", "points for side/total, probability points for the moneyline"),
    ]
    with open(os.path.join(DATA, "derivation.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stage", "columns", "input", "rule"])
        w.writerows(der)
    return rows, bt, meta


if __name__ == "__main__":
    rows, bt, meta = write()
    print("slate rows", len(rows), "backtest rows", len(bt), "tie", meta)
    for r in rows[:6]:
        print(r["game_key"], "fair", r["fair_spread_home"], "mkt", r["market_spread_home"],
              "diff", r["diff_spread_pts"], "| total", r["fair_total"], r["market_total"], r["diff_total_pts"],
              "| ml", r["fair_home_ml"], r["market_home_ml"], r.get("diff_home_ml_prob"))

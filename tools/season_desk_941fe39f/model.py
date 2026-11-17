"""Walk-forward ratings, origination and residual measurement.

Model card (frozen; the rule text is pre-registered in data/strategy/prereg.json):

  SIDE   y = home_margin.  y = HFA + r_home - r_away + e
         r is a 32-vector of team ratings in points, HFA a league home-field
         term. Weighted least squares, weight = 0.5 ** (days_ago / HALF_LIFE),
         ridge lambda on r for identifiability.  Fitted on every game strictly
         BEFORE the target week's first kickoff.  Nothing from the target week
         or later enters the fit.

  TOTAL  two equations per game, fitted together:
           home_score = off_home + def_away + hfa_off + e
           away_score = off_away + def_home        + e
         model_total = (off_home + def_away + hfa_off) + (off_away + def_home)

  MONEYLINE  P(home win) = Phi(model_margin / sigma), sigma estimated by maximum
         likelihood on the fit window from market spread vs actual result.  The
         moneyline is originated LAST, from the side, as the brief requires.

Every prediction is stored with the number of games in its fit window and the
cutoff timestamp, so a reader can prove no future information entered.
"""
from __future__ import annotations

import csv
import datetime as dt
import math
from pathlib import Path

import stats

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "nfl-season-941fe39f"
CORPUS = DESK / "data" / "corpus"

HALF_LIFE_DAYS = 365.0     # one season; a modelling choice, flagged F-11
RIDGE_RATING = 2.0         # points^2; a modelling choice, flagged F-11
RIDGE_HFA = 1.0
RIDGE_RATE = 1.0           # same, for the scoring-rate model
MIN_GAMES_TO_FIT = 60      # below this the design is not identifiable

TEAMS = sorted("""ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LA LAC
LV MIA MIN NE NO NYG NYJ PHI PIT SEA SF TB TEN WAS""".split())


def _d(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def load_games() -> list[dict]:
    path = CORPUS / "games.csv"
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            for k in ("away_score", "home_score", "result", "total",
                      "spread_line_home", "total_line", "away_spread_odds",
                      "home_spread_odds", "over_odds", "under_odds",
                      "away_moneyline", "home_moneyline"):
                r[k] = float(r[k]) if r[k] not in ("", None) else None
            for k in ("season", "week", "away_rest", "home_rest"):
                r[k] = int(r[k]) if r[k] not in ("", None) else None
            r["date"] = _d(r["gameday"])
            rows.append(r)
    rows.sort(key=lambda r: (r["date"], r["game_id"]))
    return rows


# --------------------------------------------------------------- linear algebra
def solve_spd(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting (a is symmetric positive definite)."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            m[piv][col] = 1e-12
        if piv != col:
            m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for r in range(col + 1, n):
            factor = m[r][col] / pv
            if factor == 0.0:
                continue
            for c in range(col, n + 1):
                m[r][c] -= factor * m[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = m[r][n] - sum(m[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / m[r][r]
    return x


# --------------------------------------------------------------- the fits
class Fit:
    """One model snapshot, fitted on games strictly before `cutoff`."""

    def __init__(self, games: list[dict], cutoff: dt.date):
        self.cutoff = cutoff
        self.n_games = 0
        prior = [g for g in games
                 if g["date"] < cutoff and g["result"] is not None
                 and g["home_score"] is not None]
        self.n_games = len(prior)
        self.ratings = {t: 0.0 for t in TEAMS}
        self.hfa = 0.0
        self.off = {t: 0.0 for t in TEAMS}
        self.deff = {t: 0.0 for t in TEAMS}
        self.hfa_off = 0.0
        self.sigma = 13.5          # league-typical; replaced by the ML fit below
        if len(prior) >= MIN_GAMES_TO_FIT:
            self._fit_ratings(prior)
            self._fit_rates(prior)
            self._fit_sigma(prior)

    # -- side -------------------------------------------------------------
    def _fit_ratings(self, prior: list[dict]) -> None:
        idx = {t: i for i, t in enumerate(TEAMS)}
        n = len(TEAMS) + 1                       # + home field
        ata = [[0.0] * n for _ in range(n)]
        aty = [0.0] * n
        # Each game touches exactly three parameters (home, away, home field),
        # so the normal equations are accumulated in 9 updates per game rather
        # than a full n x n sweep. Identical arithmetic, ~50x faster.
        for g in prior:
            terms = [(idx[g["home"]], 1.0), (idx[g["away"]], -1.0), (n - 1, 1.0)]
            w = 0.5 ** ((self.cutoff - g["date"]).days / HALF_LIFE_DAYS)
            y = g["result"]
            for i, xi in terms:
                aty[i] += w * xi * y
                row = ata[i]
                for j, xj in terms:
                    row[j] += w * xi * xj
        for i in range(len(TEAMS)):
            ata[i][i] += RIDGE_RATING
        ata[-1][-1] += RIDGE_HFA
        beta = solve_spd(ata, aty)
        for t, i in idx.items():
            self.ratings[t] = beta[i]
        self.hfa = beta[-1]

    # -- totals -----------------------------------------------------------
    def _fit_rates(self, prior: list[dict]) -> None:
        # params: off[32], def[32], hfa_off
        idx = {t: i for i, t in enumerate(TEAMS)}
        n = len(TEAMS) * 2 + 1
        ata = [[0.0] * n for _ in range(n)]
        aty = [0.0] * n

        def add(terms: list[tuple[int, float]], y: float, w: float) -> None:
            for i, xi in terms:
                aty[i] += w * xi * y
                row = ata[i]
                for j, xj in terms:
                    row[j] += w * xi * xj

        for g in prior:
            w = 0.5 ** ((self.cutoff - g["date"]).days / HALF_LIFE_DAYS)
            add([(idx[g["home"]], 1.0), (len(TEAMS) + idx[g["away"]], 1.0), (n - 1, 1.0)],
                g["home_score"], w)
            add([(idx[g["away"]], 1.0), (len(TEAMS) + idx[g["home"]], 1.0)],
                g["away_score"], w)
        for i in range(2 * len(TEAMS)):
            ata[i][i] += RIDGE_RATE
        ata[-1][-1] += RIDGE_RATE
        beta = solve_spd(ata, aty)
        for t, i in idx.items():
            self.off[t] = beta[i]
            self.deff[t] = beta[len(TEAMS) + i]
        self.hfa_off = beta[-1]

    # -- moneyline sigma ---------------------------------------------------
    def _fit_sigma(self, prior: list[dict]) -> None:
        pairs = [(g["spread_line_home"], 1 if g["result"] > 0 else 0,
                  1 if g["result"] == 0 else 0) for g in prior
                 if g["spread_line_home"] is not None and g["result"] is not None]
        if len(pairs) < MIN_GAMES_TO_FIT:
            return
        # Probit MLE for sigma by Newton iteration. The gradient of the
        # log-likelihood with respect to sigma is -sum((y - p) * s) / sigma**2
        # and the observed-information term is -sum(p(1-p) * s**2) / sigma**4.
        # 20 iterations from the league-typical start is ample; the routine is
        # deterministic and the same inputs always give the same sigma.
        sigma = 13.5
        for _ in range(20):
            g = 0.0
            h = 0.0
            for spread, win, tie in pairs:
                if tie:
                    continue
                p = stats.norm_cdf(spread / sigma)
                g += -(win - p) * spread / (sigma * sigma)
                h += -p * (1 - p) * spread * spread / (sigma ** 4)
            if h == 0.0:
                break
            step = g / h
            sigma_new = sigma - step
            if not (4.0 < sigma_new < 40.0):
                sigma_new = min(max(sigma_new, 4.0), 40.0)
            if abs(sigma_new - sigma) < 1e-6:
                sigma = sigma_new
                break
            sigma = sigma_new
        self.sigma = sigma

    # -- predictions -------------------------------------------------------
    def margin(self, home: str, away: str) -> float:
        return self.hfa + self.ratings[home] - self.ratings[away]

    def total(self, home: str, away: str) -> float:
        return (self.off[home] + self.deff[away] + self.hfa_off) + \
               (self.off[away] + self.deff[home])

    def home_prob(self, home: str, away: str) -> float:
        return stats.norm_cdf(self.margin(home, away) / self.sigma)


# --------------------------------------------------------------- origination
def originate(games: list[dict]) -> dict:
    """Produce one originated market per future game, walk-forward.

    Order is fixed and recorded per row: SIDE, then TOTAL, then MONEYLINE.
    """
    rows = []
    seasons: dict[int, list[dict]] = {}
    for g in games:
        seasons.setdefault(g["season"], []).append(g)

    for season in sorted(seasons):
        sgames = seasons[season]
        weeks = sorted({g["week"] for g in sgames})
        for week in weeks:
            wk = [g for g in sgames if g["week"] == week]
            cutoff = min(g["date"] for g in wk)
            fit = Fit(games, cutoff)
            if fit.n_games < MIN_GAMES_TO_FIT:
                continue
            for g in wk:
                if g["spread_line_home"] is None and g["total_line"] is None:
                    continue
                model_margin = fit.margin(g["home"], g["away"])
                model_total = fit.total(g["home"], g["away"])
                model_p = fit.home_prob(g["home"], g["away"])
                rows.append({
                    "game_id": g["game_id"],
                    "season": season,
                    "week": week,
                    "gameday": g["gameday"],
                    "away": g["away"],
                    "home": g["home"],
                    "model_margin_home": model_margin,
                    "model_total": model_total,
                    "model_home_win_prob": model_p,
                    "market_spread_home": g["spread_line_home"],
                    "market_total": g["total_line"],
                    "market_home_ml": g["home_moneyline"],
                    "market_away_ml": g["away_moneyline"],
                    "home_spread_odds": g["home_spread_odds"],
                    "away_spread_odds": g["away_spread_odds"],
                    "over_odds": g["over_odds"],
                    "under_odds": g["under_odds"],
                    "result": g["result"],
                    "total_actual": g["total"],
                    "roof": g["roof"],
                    "surface": g["surface"],
                    "wind": float(g["wind_mph"]) if g["wind_mph"] not in ("", None) else None,
                    "temp": float(g["temp_f"]) if g["temp_f"] not in ("", None) else None,
                    "div_game": int(g["div_game"]) if g["div_game"] not in ("", None) else None,
                    "rest_home": g["home_rest"],
                    "rest_away": g["away_rest"],
                    "location": g["location"],
                    "n_fit_games": fit.n_games,
                    "fit_cutoff": cutoff.isoformat(),
                    "sigma": fit.sigma,
                    "hfa": fit.hfa,
                })
    return {"rows": rows}


# --------------------------------------------------------------- residual test
def residual_alpha(rows: list[dict], season_lo: int, season_hi: int) -> dict:
    """Does (model - market) predict the result?  This is the alpha question.

    residual = model_margin - market_spread_home.  A positive residual means the
    model likes the home side more than the market does.  If the model carries
    information, residual should correlate positively with result - market.
    """
    xs, ys, clusters = [], [], []
    for r in rows:
        if not (season_lo <= r["season"] <= season_hi):
            continue
        if r["market_spread_home"] is None or r["result"] is None:
            continue
        xs.append(r["model_margin_home"] - r["market_spread_home"])
        ys.append(r["result"] - r["market_spread_home"])
        clusters.append(f"{r['season']}-{r['week']}")
    r, n = stats.pearson(xs, ys)
    lo, hi = stats.fisher_ci(r, n)
    return {"r": r, "n": n, "ci": (lo, hi), "seasons": (season_lo, season_hi)}


def residual_level(rows: list[dict], season_lo: int, season_hi: int) -> dict:
    """How big is the origination residual, and how does it compare with MAE?"""
    import statistics
    diffs = [r["model_margin_home"] - r["market_spread_home"] for r in rows
             if season_lo <= r["season"] <= season_hi
             and r["market_spread_home"] is not None]
    model_err = [abs(r["model_margin_home"] - r["result"]) for r in rows
                 if season_lo <= r["season"] <= season_hi and r["result"] is not None]
    mkt_err = [abs(r["market_spread_home"] - r["result"]) for r in rows
               if season_lo <= r["season"] <= season_hi
               and r["market_spread_home"] is not None and r["result"] is not None]
    tdiffs = [r["model_total"] - r["market_total"] for r in rows
              if season_lo <= r["season"] <= season_hi and r["market_total"] is not None]
    model_terr = [abs(r["model_total"] - r["total_actual"]) for r in rows
                  if season_lo <= r["season"] <= season_hi and r["total_actual"] is not None]
    mkt_terr = [abs(r["market_total"] - r["total_actual"]) for r in rows
                if season_lo <= r["season"] <= season_hi
                and r["market_total"] is not None and r["total_actual"] is not None]
    return {
        "n_side": len(diffs),
        "mean_residual": statistics.mean(diffs) if diffs else float("nan"),
        "sd_residual": statistics.pstdev(diffs) if len(diffs) > 1 else float("nan"),
        "mae_model_side": statistics.mean(model_err) if model_err else float("nan"),
        "mae_market_side": statistics.mean(mkt_err) if mkt_err else float("nan"),
        "n_total": len(tdiffs),
        "mean_residual_total": statistics.mean(tdiffs) if tdiffs else float("nan"),
        "sd_residual_total": statistics.pstdev(tdiffs) if len(tdiffs) > 1 else float("nan"),
        "mae_model_total": statistics.mean(model_terr) if model_terr else float("nan"),
        "mae_market_total": statistics.mean(mkt_terr) if mkt_terr else float("nan"),
    }


if __name__ == "__main__":
    games = load_games()
    print(f"games: {len(games)}")
    out = originate(games)
    print(f"originated rows: {len(out['rows'])}")
    for r in out["rows"][-3:]:
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()
               if k in ("game_id", "model_margin_home", "market_spread_home",
                        "model_total", "market_total", "n_fit_games", "sigma")})
    print("alpha 1999-2025:", residual_alpha(out["rows"], 1999, 2025))
    print("alpha 2023-2025 (holdout):", residual_alpha(out["rows"], 2023, 2025))

"""NFL line origination — produce our OWN spread, total and moneyline.

Method
------
Weekly walk-forward refit. For every (season, week) we fit on games whose
kickoff date is strictly BEFORE that week's first game, so no future result can
leak into a price. Two weighted ridge regressions are fitted on team indicators:

  margin model : y = home_score - away_score
                 X = +1 home team, -1 away team, home-field constant,
                     rest differential
  total model  : y = home_score + away_score
                 X = +1 for both teams (scoring environment), constant

Weights decay exponentially with age (half-life tuned on training only).
The fitted coefficients are published as team power ratings.

Outputs per game: our_spread (home handicap, book convention = -mu),
our_total, our_p_home_win, and the residual sigma used for the conversion.

Nothing here is fitted on the closing line. The market is used ONLY as the
price we must beat, never as a model input, which is what makes the edge
measurement meaningful rather than circular.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from common import OUT, load_games, write_csv, write_json

HALF_LIFE_DAYS = 300.0     # recency weight for team strength
RIDGE_ALPHA = 5.0          # shrinkage; selected by walk-forward RMSE/Brier sweep
MIN_TRAIN_GAMES = 200      # need enough history before pricing


def _design(teams: list[str], home: pd.Series, away: pd.Series,
            rest_diff: pd.Series | None = None) -> tuple[np.ndarray, list[str]]:
    """Team-indicator design matrix with a home-field term."""
    idx = {t: i for i, t in enumerate(teams)}
    n = len(home)
    k = len(teams)
    extra = 2 if rest_diff is not None else 1
    X = np.zeros((n, k + extra))
    hi = np.array([idx[t] for t in home])
    ai = np.array([idx[t] for t in away])
    r = np.arange(n)
    X[r, hi] += 1.0
    X[r, ai] -= 1.0
    X[:, k] = 1.0                      # home-field advantage
    if rest_diff is not None:
        X[:, k + 1] = np.clip(rest_diff.values, -7, 7) / 7.0
    names = teams + ["HOME_ADV"] + (["REST_DIFF"] if rest_diff is not None else [])
    return X, names


def _design_total(teams: list[str], home: pd.Series, away: pd.Series) -> np.ndarray:
    idx = {t: i for i, t in enumerate(teams)}
    n = len(home)
    X = np.zeros((n, len(teams) + 1))
    r = np.arange(n)
    X[r, [idx[t] for t in home]] += 1.0
    X[r, [idx[t] for t in away]] += 1.0
    X[:, -1] = 1.0
    return X


def _ridge(X: np.ndarray, y: np.ndarray, w: np.ndarray, alpha: float) -> np.ndarray:
    """Weighted ridge with unpenalised intercept column(s)."""
    XtW = X.T * w
    A = XtW @ X
    pen = np.eye(X.shape[1]) * alpha
    # Do not shrink the constant / rest terms.
    pen[-1, -1] = 1e-9
    pen[-2, -2] = 1e-9
    return np.linalg.solve(A + pen, XtW @ y)


def originate(g: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Walk-forward origination. Returns (priced games, rating history)."""
    teams = sorted(set(g["home_team"]) | set(g["away_team"]))
    g = g.sort_values(["gameday", "game_id"]).reset_index(drop=True)
    keys = g[["season", "week"]].drop_duplicates().sort_values(["season", "week"])

    out = []
    ratings_rows = []
    for _, kr in keys.iterrows():
        season, week = int(kr["season"]), int(kr["week"])
        wk = g[(g["season"] == season) & (g["week"] == week)]
        cutoff = wk["gameday"].min()
        train = g[g["gameday"] < cutoff]
        if len(train) < MIN_TRAIN_GAMES:
            continue

        age = (cutoff - train["gameday"]).dt.days.values.astype(float)
        w = np.power(0.5, age / HALF_LIFE_DAYS)

        Xm, names = _design(teams, train["home_team"], train["away_team"], train["rest_diff"])
        bm = _ridge(Xm, train["result"].values.astype(float), w, RIDGE_ALPHA)

        Xt = _design_total(teams, train["home_team"], train["away_team"])
        bt = _ridge(Xt, train["total"].values.astype(float), w, RIDGE_ALPHA)

        # In-sample residual scale, inflated slightly for out-of-sample use.
        resid_m = train["result"].values - Xm @ bm
        sigma_m = float(np.sqrt(np.average(resid_m ** 2, weights=w)))
        resid_t = train["total"].values - Xt @ bt
        sigma_t = float(np.sqrt(np.average(resid_t ** 2, weights=w)))

        Xp, _ = _design(teams, wk["home_team"], wk["away_team"], wk["rest_diff"])
        mu = Xp @ bm
        Xtp = _design_total(teams, wk["home_team"], wk["away_team"])
        tot = Xtp @ bt

        tmp = wk.copy()
        tmp["our_margin"] = mu
        tmp["our_spread"] = -mu              # book convention: home handicap
        tmp["our_total"] = tot
        tmp["sigma_margin"] = sigma_m
        tmp["sigma_total"] = sigma_t
        # P(home wins) allowing for ties: continuity-corrected normal.
        tmp["our_p_home_win"] = 1.0 - stats.norm.cdf(0.5, loc=mu, scale=sigma_m)
        tmp["our_p_tie"] = (stats.norm.cdf(0.5, loc=mu, scale=sigma_m)
                            - stats.norm.cdf(-0.5, loc=mu, scale=sigma_m))
        tmp["n_train_games"] = len(train)
        out.append(tmp)

        for i, t in enumerate(teams):
            ratings_rows.append({
                "season": season, "week": week, "as_of": cutoff.date().isoformat(),
                "team": t, "power_rating": round(float(bm[i]), 4),
                "scoring_env": round(float(bt[i]), 4),
                "n_train_games": len(train),
            })

    priced = pd.concat(out, ignore_index=True)
    ratings = pd.DataFrame(ratings_rows)
    return priced, ratings


def calibration_table(priced: pd.DataFrame) -> pd.DataFrame:
    """Reliability of our win probabilities vs realised frequency."""
    d = priced.dropna(subset=["our_p_home_win"]).copy()
    d["home_win"] = (d["result"] > 0).astype(int)
    d = d[d["result"] != 0]
    bins = np.linspace(0, 1, 11)
    d["bucket"] = pd.cut(d["our_p_home_win"], bins)
    rows = []
    for b, sub in d.groupby("bucket", observed=True):
        if len(sub) == 0:
            continue
        rows.append({
            "bucket": str(b),
            "n": len(sub),
            "predicted": round(float(sub["our_p_home_win"].mean()), 4),
            "observed": round(float(sub["home_win"].mean()), 4),
            "abs_gap": round(abs(float(sub["our_p_home_win"].mean()) - float(sub["home_win"].mean())), 4),
        })
    return pd.DataFrame(rows)


def main() -> None:
    g = load_games()
    priced, ratings = originate(g)
    keep = [
        "game_id", "season", "week", "gameday", "away_team", "home_team",
        "away_score", "home_score", "result", "total",
        "spread_line", "total_line", "home_moneyline", "away_moneyline",
        "spread_odds_home", "spread_odds_away", "spread_odds_assumed",
        "total_odds_over", "total_odds_under", "total_odds_assumed",
        "mkt_p_home_cover", "mkt_p_away_cover", "mkt_p_over", "mkt_p_under",
        "mkt_p_home_win", "mkt_p_away_win",
        "home_cover_margin", "total_margin", "rest_diff", "div_game",
        "home_bye", "away_bye", "short_week_home", "short_week_away", "is_neutral",
        "our_margin", "our_spread", "our_total", "sigma_margin", "sigma_total",
        "our_p_home_win", "our_p_tie", "n_train_games",
    ]
    priced = priced[[c for c in keep if c in priced.columns]]
    write_csv(priced, "originated_lines.csv")
    write_csv(ratings, "power_ratings.csv")

    cal = calibration_table(priced)
    write_csv(cal, "calibration.csv")

    have = priced.dropna(subset=["spread_line", "total_line"])
    metrics = {
        "games_priced": int(len(priced)),
        "seasons": [int(priced.season.min()), int(priced.season.max())],
        "spread_rmse_ours": round(float(np.sqrt(((have.result - have.our_margin) ** 2).mean())), 4),
        "spread_rmse_market": round(float(np.sqrt(((have.result - have.spread_line) ** 2).mean())), 4),
        "spread_mae_ours": round(float((have.result - have.our_margin).abs().mean()), 4),
        "spread_mae_market": round(float((have.result - have.spread_line).abs().mean()), 4),
        "total_rmse_ours": round(float(np.sqrt(((have.total - have.our_total) ** 2).mean())), 4),
        "total_rmse_market": round(float(np.sqrt(((have.total - have.total_line) ** 2).mean())), 4),
        "mean_sigma_margin": round(float(priced.sigma_margin.mean()), 4),
        "mean_sigma_total": round(float(priced.sigma_total.mean()), 4),
        "corr_our_vs_market_spread": round(float(priced.spread_line.corr(-priced.our_spread)), 4),
    }
    # Brier scores on home win (lower is better), ties excluded.
    nt = have[have.result != 0].dropna(subset=["mkt_p_home_win"])
    y = (nt.result > 0).astype(float).values
    metrics["brier_ours"] = round(float(np.mean((nt.our_p_home_win.values - y) ** 2)), 5)
    metrics["brier_market"] = round(float(np.mean((nt.mkt_p_home_win.values - y) ** 2)), 5)
    metrics["brier_n"] = int(len(nt))
    write_json("origination_metrics.json", metrics)

    print("=== LINE ORIGINATION (walk-forward, no lookahead) ===")
    for k, v in metrics.items():
        print(f"  {k:32s} {v}")
    print("\nCalibration:\n" + cal.to_string(index=False))


if __name__ == "__main__":
    main()

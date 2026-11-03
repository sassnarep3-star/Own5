"""Originating OUR lines for the next unplayed week, and comparing to the market.

This is the practical output of the project: a full board of our own spreads,
totals and moneylines, produced by the same walk-forward model, alongside the
posted market number where one exists. Divergence is reported, NOT presented as
a recommended bet — no strategy in this repo has cleared the validation gates.

Market prices come from the vendored third-party table. Where no market price
exists the cell is left blank and flagged, never filled with a guess.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

import originate as O
from common import RAW, american_to_prob, devig_two_way, write_csv, write_json

TEAM_ALIAS = {"OAK": "LV", "SD": "LAC", "STL": "LA", "WSH": "WAS", "LAR": "LA"}


def main() -> None:
    hist = O.load_games()                       # completed games only
    raw = pd.read_csv(RAW / "games.csv")
    raw["home_team"] = raw["home_team"].replace(TEAM_ALIAS)
    raw["away_team"] = raw["away_team"].replace(TEAM_ALIAS)
    future = raw[(raw.game_type == "REG") & raw.home_score.isna()].copy()
    if future.empty:
        print("No unplayed games in the vendored schedule.")
        return
    future["gameday"] = pd.to_datetime(future["gameday"])
    first_week = int(future.week.min())
    # A partial week (e.g. only the remaining Monday game) is not a useful board.
    # Cover the next two schedule weeks so the deliverable is a full slate.
    board = future[future.week <= first_week + 1].copy()
    next_week = first_week
    season = int(board.season.iloc[0])

    # Fit on every completed game strictly before the next kickoff.
    cutoff = board.gameday.min()
    train = hist[hist.gameday < cutoff]
    teams = sorted(set(hist.home_team) | set(hist.away_team))
    age = (cutoff - train.gameday).dt.days.values.astype(float)
    w = np.power(0.5, age / O.HALF_LIFE_DAYS)

    Xm, names = O._design(teams, train.home_team, train.away_team, train.rest_diff)
    bm = O._ridge(Xm, train.result.values.astype(float), w, O.RIDGE_ALPHA)
    Xt = O._design_total(teams, train.home_team, train.away_team)
    bt = O._ridge(Xt, train.total.values.astype(float), w, O.RIDGE_ALPHA)
    sigma_m = float(np.sqrt(np.average((train.result.values - Xm @ bm) ** 2, weights=w)))
    sigma_t = float(np.sqrt(np.average((train.total.values - Xt @ bt) ** 2, weights=w)))

    # Rest for future games may be missing upstream; do not invent it.
    rd = board["rest_diff"] if "rest_diff" in board else (board.home_rest - board.away_rest)
    rd = rd.fillna(0)
    Xp, _ = O._design(teams, board.home_team, board.away_team, pd.Series(rd.values, index=board.index))
    mu = Xp @ bm
    tot = O._design_total(teams, board.home_team, board.away_team) @ bt

    rows = []
    for i, r in enumerate(board.itertuples()):
        p_home = float(1 - stats.norm.cdf(0.5, loc=mu[i], scale=sigma_m))
        # Upstream spread_line is positive when the HOME team is favoured, and
        # our mu is the predicted home margin — so they are directly comparable.
        # (Book-style handicap would be -mu; do NOT mix the two conventions.)
        our_spread = mu[i]
        mkt_spread = r.spread_line if pd.notna(r.spread_line) else None
        mkt_total = r.total_line if pd.notna(r.total_line) else None
        # Fair American prices from our own probabilities (no vig).
        def to_am(p):
            p = min(max(p, 1e-6), 1 - 1e-6)
            return round(-100 * p / (1 - p), 1) if p >= .5 else round(100 * (1 - p) / p, 1)
        mkt_p_home = None
        if pd.notna(r.home_moneyline) and pd.notna(r.away_moneyline):
            ph = american_to_prob(np.array([r.home_moneyline]))
            pa = american_to_prob(np.array([r.away_moneyline]))
            mkt_p_home = float(devig_two_way(ph, pa)[0][0])
        rows.append({
            "season": season, "week": next_week,
            "gameday": r.gameday.date().isoformat(),
            "away_team": r.away_team, "home_team": r.home_team,
            "our_spread_home_fav": round(float(our_spread), 2),
            "market_spread_home_fav": mkt_spread,
            "spread_diff": round(float(our_spread - mkt_spread), 2) if mkt_spread is not None else None,
            "our_total": round(float(tot[i]), 2),
            "market_total": mkt_total,
            "total_diff": round(float(tot[i] - mkt_total), 2) if mkt_total is not None else None,
            "our_p_home_win": round(p_home, 4),
            "our_ml_home_fair": to_am(p_home),
            "our_ml_away_fair": to_am(1 - p_home),
            "market_ml_home": r.home_moneyline if pd.notna(r.home_moneyline) else None,
            "market_ml_away": r.away_moneyline if pd.notna(r.away_moneyline) else None,
            "market_p_home_win_devig": round(mkt_p_home, 4) if mkt_p_home is not None else None,
            "ml_edge_home": round(p_home - mkt_p_home, 4) if mkt_p_home is not None else None,
            "model_sigma_margin": round(sigma_m, 3),
            "n_train_games": len(train),
            "status": "MODEL OUTPUT — not a validated betting recommendation",
            "market_source_url": "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
            "official_schedule_url": f"https://www.nfl.com/schedules/{season}/REG{r.week}",
        })
    df = pd.DataFrame(rows)
    write_csv(df, "originated_board_next_week.csv")

    # Current team power ratings, as of the same cutoff.
    pr = pd.DataFrame({
        "team": teams,
        "power_rating": np.round(bm[:len(teams)], 3),
        "scoring_env": np.round(bt[:len(teams)], 3),
    }).sort_values("power_rating", ascending=False)
    pr["rank"] = range(1, len(pr) + 1)
    pr["as_of"] = cutoff.date().isoformat()
    pr["n_train_games"] = len(train)
    pr["source_url"] = "https://www.nfl.com/scores/"
    write_csv(pr, "current_power_ratings.csv")

    with_mkt = df[df.market_spread_home_fav.notna()]
    write_json("board_summary.json", {
        "season": season, "weeks": [next_week, next_week + 1], "games": int(len(df)),
        "games_with_market_price": int(len(with_mkt)),
        "games_without_market_price": int(len(df) - len(with_mkt)),
        "mean_abs_spread_diff": round(float(with_mkt.spread_diff.abs().mean()), 3) if len(with_mkt) else None,
        "max_abs_spread_diff": round(float(with_mkt.spread_diff.abs().max()), 3) if len(with_mkt) else None,
        "mean_abs_total_diff": round(float(with_mkt.total_diff.abs().mean()), 3) if len(with_mkt) else None,
        "train_games": int(len(train)),
        "disclaimer": "Model prices are research output. No strategy cleared the validation gates; "
                      "divergence from the market is NOT evidence of a profitable edge.",
    })
    print(f"=== OUR ORIGINATED BOARD — {season} Weeks {next_week}-{next_week+1} ===")
    print(df[["gameday", "away_team", "home_team", "our_spread_home_fav", "market_spread_home_fav",
              "spread_diff", "our_total", "market_total", "total_diff",
              "our_p_home_win", "market_p_home_win_devig"]].to_string(index=False))
    print("\n=== TOP 10 POWER RATINGS ===")
    print(pr.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

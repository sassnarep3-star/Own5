"""Strategy backtests: singles, cross-game parlays, and player-prop combos.

Every strategy is a deterministic rule that maps pregame information to a bet
or to no bet. Bets are graded against the actual closing price recorded in the
game table, using real American odds where present and an explicitly flagged
-110 assumption otherwise.

Discipline enforced here
------------------------
* Walk-forward prices only (engine/originate.py never sees the future).
* Thresholds are fixed a priori, not optimised on the test window.
* Pushes refund the stake (they are not counted as wins).
* Parlay legs from the SAME game are priced with the empirical joint
  probability, never by multiplying marginals.
* Every result carries its sample size so the skill/luck layer can judge it.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from common import (OUT, american_to_decimal, attach_verification, write_csv,
                    write_json)


@dataclass
class Bet:
    strategy: str
    game_id: str
    season: int
    week: int
    market: str
    selection: str
    price: float          # American odds
    stake: float
    result: float         # +1 win, -1 loss, 0 push
    model_p: float
    market_p: float
    edge: float
    legs: int = 1
    assumed_price: int = 0
    notes: str = ""

    @property
    def profit(self) -> float:
        if self.result == 0:
            return 0.0
        if self.result > 0:
            return self.stake * (american_to_decimal(self.price) - 1.0)
        return -self.stake


# --------------------------------------------------------------------------
# Singles
# --------------------------------------------------------------------------

def strategy_spread_value(p: pd.DataFrame, min_edge: float = 0.03) -> list[Bet]:
    """Bet the spread when our calibrated cover probability beats the de-vigged
    market probability by at least ``min_edge``."""
    from scipy import stats
    bets = []
    for r in p.itertuples():
        if not np.isfinite(r.spread_line) or not np.isfinite(r.our_margin):
            continue
        # Our cover prob for the HOME side: result - spread_line > 0.
        # Our margin estimate is N(our_margin, sigma), shifted by the posted line.
        mu = r.our_margin - r.spread_line
        s = r.sigma_margin
        p_home = 1.0 - stats.norm.cdf(0.0, loc=mu, scale=s)
        p_away = 1.0 - p_home
        for side, prob, mkt, price, assumed in (
            ("HOME", p_home, r.mkt_p_home_cover, r.spread_odds_home, r.spread_odds_assumed),
            ("AWAY", p_away, r.mkt_p_away_cover, r.spread_odds_away, r.spread_odds_assumed),
        ):
            edge = prob - mkt
            if edge < min_edge:
                continue
            margin = r.home_cover_margin if side == "HOME" else -r.home_cover_margin
            bets.append(Bet(
                strategy="S1_spread_value", game_id=r.game_id, season=r.season, week=r.week,
                market="spread", selection=f"{r.home_team if side=='HOME' else r.away_team} {r.spread_line:+.1f}",
                price=float(price), stake=1.0, result=float(np.sign(margin)),
                model_p=float(prob), market_p=float(mkt), edge=float(edge),
                assumed_price=int(assumed),
            ))
    return bets


def strategy_total_value(p: pd.DataFrame, min_edge: float = 0.03) -> list[Bet]:
    """Bet the total when our total projection differs enough from the line."""
    from scipy import stats
    bets = []
    for r in p.itertuples():
        if not np.isfinite(r.total_line) or not np.isfinite(r.our_total):
            continue
        mu = r.our_total - r.total_line
        p_over = 1.0 - stats.norm.cdf(0.0, loc=mu, scale=r.sigma_total)
        p_under = 1.0 - p_over
        for side, prob, mkt, price in (
            ("OVER", p_over, r.mkt_p_over, r.total_odds_over),
            ("UNDER", p_under, r.mkt_p_under, r.total_odds_under),
        ):
            edge = prob - mkt
            if edge < min_edge:
                continue
            margin = r.total_margin if side == "OVER" else -r.total_margin
            bets.append(Bet(
                strategy="S2_total_value", game_id=r.game_id, season=r.season, week=r.week,
                market="total", selection=f"{side} {r.total_line:.1f}",
                price=float(price), stake=1.0, result=float(np.sign(margin)),
                model_p=float(prob), market_p=float(mkt), edge=float(edge),
                assumed_price=int(r.total_odds_assumed),
            ))
    return bets


def strategy_rest_edge(p: pd.DataFrame) -> list[Bet]:
    """Back the better-rested team off a bye against a short-week opponent.

    A classic situational signal, tested honestly rather than assumed.
    """
    bets = []
    for r in p.itertuples():
        if not np.isfinite(r.spread_line):
            continue
        if r.home_bye and r.short_week_away:
            side, margin, price, mkt = "HOME", r.home_cover_margin, r.spread_odds_home, r.mkt_p_home_cover
            team = r.home_team
        elif r.away_bye and r.short_week_home:
            side, margin, price, mkt = "AWAY", -r.home_cover_margin, r.spread_odds_away, r.mkt_p_away_cover
            team = r.away_team
        else:
            continue
        bets.append(Bet(
            strategy="S3_rest_edge", game_id=r.game_id, season=r.season, week=r.week,
            market="spread", selection=f"{team} (bye vs short wk)",
            price=float(price), stake=1.0, result=float(np.sign(margin)),
            model_p=float("nan"), market_p=float(mkt), edge=float("nan"),
            assumed_price=int(r.spread_odds_assumed),
        ))
    return bets


def strategy_division_dog(p: pd.DataFrame) -> list[Bet]:
    """Divisional underdog of 3+ points — a frequently claimed situational edge."""
    bets = []
    for r in p.itertuples():
        if not r.div_game or not np.isfinite(r.spread_line):
            continue
        # spread_line > 0 => home favored; dog is away, and vice versa.
        if r.spread_line >= 3.0:
            team, margin, price, mkt = r.away_team, -r.home_cover_margin, r.spread_odds_away, r.mkt_p_away_cover
        elif r.spread_line <= -3.0:
            team, margin, price, mkt = r.home_team, r.home_cover_margin, r.spread_odds_home, r.mkt_p_home_cover
        else:
            continue
        bets.append(Bet(
            strategy="S4_division_dog", game_id=r.game_id, season=r.season, week=r.week,
            market="spread", selection=f"{team} (div dog)",
            price=float(price), stake=1.0, result=float(np.sign(margin)),
            model_p=float("nan"), market_p=float(mkt), edge=float("nan"),
            assumed_price=int(r.spread_odds_assumed),
        ))
    return bets


def strategy_fade_public_favorite(p: pd.DataFrame, big: float = 7.0) -> list[Bet]:
    """Bet the dog when the market lays a touchdown or more."""
    bets = []
    for r in p.itertuples():
        if not np.isfinite(r.spread_line) or abs(r.spread_line) < big:
            continue
        if r.spread_line >= big:
            team, margin, price, mkt = r.away_team, -r.home_cover_margin, r.spread_odds_away, r.mkt_p_away_cover
        else:
            team, margin, price, mkt = r.home_team, r.home_cover_margin, r.spread_odds_home, r.mkt_p_home_cover
        bets.append(Bet(
            strategy="S5_fade_big_favorite", game_id=r.game_id, season=r.season, week=r.week,
            market="spread", selection=f"{team} (dog >= {big:g})",
            price=float(price), stake=1.0, result=float(np.sign(margin)),
            model_p=float("nan"), market_p=float(mkt), edge=float("nan"),
            assumed_price=int(r.spread_odds_assumed),
        ))
    return bets


# --------------------------------------------------------------------------
# Parlays (cross-game, independence approximately valid)
# --------------------------------------------------------------------------

def strategy_cross_game_parlay(p: pd.DataFrame, min_edge: float = 0.03) -> list[Bet]:
    """Two-leg parlays of the strongest independent spread edges in the same week.

    Legs are always from DIFFERENT games. Cross-game outcomes are close to
    independent (measured in engine/correlations.py); the small residual
    dependence is reported rather than assumed away.
    Standard two-leg parlay pricing is used conservatively at 2.6-to-1.
    """
    singles = strategy_spread_value(p, min_edge=min_edge)
    by_week: dict[tuple[int, int], list[Bet]] = {}
    for b in singles:
        by_week.setdefault((b.season, b.week), []).append(b)
    bets = []
    for (season, week), group in sorted(by_week.items()):
        group = sorted(group, key=lambda b: -b.edge)
        used = set()
        for a, b in itertools.combinations(group, 2):
            if a.game_id in used or b.game_id in used:
                continue
            if a.game_id == b.game_id:
                continue
            used.update({a.game_id, b.game_id})
            joint_p = a.model_p * b.model_p          # independence, cross-game
            mkt_p = a.market_p * b.market_p
            res = 1.0 if (a.result > 0 and b.result > 0) else (
                0.0 if (a.result == 0 or b.result == 0) else -1.0)
            bets.append(Bet(
                strategy="P1_cross_game_2leg", game_id=f"{a.game_id}+{b.game_id}",
                season=season, week=week, market="parlay",
                selection=f"{a.selection} & {b.selection}",
                price=160.0, stake=1.0, result=res,
                model_p=float(joint_p), market_p=float(mkt_p),
                edge=float(joint_p - mkt_p), legs=2,
                assumed_price=int(a.assumed_price or b.assumed_price),
                notes="cross-game; independence measured, not assumed",
            ))
            break  # one parlay per week: keep the sample honest and uncorrelated
    return bets


# --------------------------------------------------------------------------
# Same-game combination (correlation matters — priced empirically)
# --------------------------------------------------------------------------

def strategy_same_game_combo(p: pd.DataFrame) -> list[Bet]:
    """Favorite + Over same-game combo, priced with the EMPIRICAL joint rate.

    This is the case where multiplying marginals is wrong. We estimate
    P(favorite covers AND over) from the training seasons only, then apply that
    fixed rate forward, so the estimate is out-of-sample.
    """
    d = p.dropna(subset=["spread_line", "total_line"]).copy()
    d["fav_cover"] = np.where(
        d.spread_line > 0,
        (d.home_cover_margin > 0).astype(int),
        (d.home_cover_margin < 0).astype(int),
    )
    d["over"] = (d.total_margin > 0).astype(int)
    bets = []
    for season in sorted(d.season.unique()):
        train = d[d.season < season]
        test = d[d.season == season]
        if len(train) < 400:
            continue
        joint = float(((train.fav_cover == 1) & (train.over == 1)).mean())
        p_fav = float((train.fav_cover == 1).mean())
        p_ov = float((train.over == 1).mean())
        for r in test.itertuples():
            if abs(r.spread_line) < 3:
                continue
            fav_team = r.home_team if r.spread_line > 0 else r.away_team
            win = 1.0 if (r.fav_cover == 1 and r.over == 1) else -1.0
            bets.append(Bet(
                strategy="P2_same_game_fav_over", game_id=r.game_id, season=int(season),
                week=r.week, market="same_game_parlay",
                selection=f"{fav_team} covers & OVER {r.total_line:.1f}",
                price=260.0, stake=1.0, result=win,
                model_p=joint, market_p=p_fav * p_ov, edge=joint - p_fav * p_ov,
                legs=2, assumed_price=1,
                notes=f"empirical joint from {len(train)} prior games; naive product would misprice",
            ))
    return bets


# --------------------------------------------------------------------------
# Player prop combos
# --------------------------------------------------------------------------

def load_player_weekly() -> pd.DataFrame:
    """Weekly player stat lines (third-party, PFR-derived)."""
    base = OUT.parent / "raw" / "player_weekly"
    rows = []
    for year_dir in sorted(base.glob("*")):
        if not year_dir.is_dir():
            continue
        for f in sorted(year_dir.glob("week*.csv"), key=lambda x: int(x.stem.replace("week", ""))):
            df = pd.read_csv(f)
            df["season"] = int(year_dir.name)
            df["week"] = int(f.stem.replace("week", ""))
            rows.append(df)
    if not rows:
        return pd.DataFrame()
    p = pd.concat(rows, ignore_index=True)
    return p


def strategy_prop_combo(p: pd.DataFrame) -> list[Bet]:
    """QB passing-yards + same-team WR receiving-yards combo.

    Prop LINES are not published by any official source, so we do NOT invent a
    sportsbook price. Instead we originate our own line from each player's
    trailing median and measure whether the two legs clear their originated
    line together more often than independence predicts. The measured lift is
    the deliverable; ROI is left blank because no verified market price exists.
    """
    return []  # handled analytically in engine/correlations.py (no invented prices)


STRATEGIES = {
    "S1_spread_value": strategy_spread_value,
    "S2_total_value": strategy_total_value,
    "S3_rest_edge": strategy_rest_edge,
    "S4_division_dog": strategy_division_dog,
    "S5_fade_big_favorite": strategy_fade_public_favorite,
    "P1_cross_game_2leg": strategy_cross_game_parlay,
    "P2_same_game_fav_over": strategy_same_game_combo,
}


def run_all() -> pd.DataFrame:
    p = pd.read_csv(OUT / "originated_lines.csv")
    p = attach_verification(p)
    all_bets: list[Bet] = []
    for name, fn in STRATEGIES.items():
        b = fn(p)
        all_bets.extend(b)
        print(f"  {name:26s} {len(b):6d} bets")
    df = pd.DataFrame([{
        "strategy": b.strategy, "game_id": b.game_id, "season": b.season, "week": b.week,
        "market": b.market, "selection": b.selection, "price_american": b.price,
        "stake": b.stake, "result": b.result, "profit": round(b.profit, 6),
        "model_p": b.model_p, "market_p": b.market_p, "edge": b.edge,
        "legs": b.legs, "assumed_price": b.assumed_price, "notes": b.notes,
    } for b in all_bets])
    # Attach official verification per bet (parlays: all legs must be verified).
    v = p.set_index("game_id")["official_verified"].to_dict()
    u = p.set_index("game_id")["official_source_url"].to_dict()

    def _ver(gid: str) -> bool:
        return all(bool(v.get(x, False)) for x in gid.split("+"))

    def _src(gid: str) -> str:
        return "; ".join(sorted({u.get(x, "") for x in gid.split("+") if u.get(x, "")}))

    df["official_verified"] = df["game_id"].map(_ver)
    df["official_source_url"] = df["game_id"].map(_src)
    write_csv(df, "bets.csv")
    return df


def main() -> None:
    print("=== STRATEGY BACKTESTS ===")
    df = run_all()
    rows = []
    for name, sub in df.groupby("strategy"):
        decided = sub[sub.result != 0]
        n = len(sub)
        wins = int((decided.result > 0).sum())
        losses = int((decided.result < 0).sum())
        pushes = int((sub.result == 0).sum())
        staked = float(decided.stake.sum())
        profit = float(sub.profit.sum())
        rows.append({
            "strategy": name, "bets": n, "wins": wins, "losses": losses, "pushes": pushes,
            "win_rate": round(wins / max(1, wins + losses), 5),
            "profit_units": round(profit, 4),
            "roi": round(profit / staked, 5) if staked else None,
            "avg_edge": round(float(sub.edge.mean()), 5) if sub.edge.notna().any() else None,
            "official_verified_bets": int(sub.official_verified.sum()),
        })
    summary = pd.DataFrame(rows)
    write_csv(summary, "strategy_summary.csv")
    print("\n" + summary.to_string(index=False))


if __name__ == "__main__":
    main()

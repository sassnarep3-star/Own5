"""Settled legs, the registered strategy list, and how a bet is graded.

One place decides what "win" means, so that the signal table, the staking table,
the gates and the demotion gate are all grading the same object.

Legs available for every settled game
-------------------------------------
``side_home`` / ``side_away``  the market's posted spread for that club, at that
                               club's posted price.
``over`` / ``under``           the market's posted total, at its posted price.
``ml_home`` / ``ml_away``      the moneyline, a tie being a push.
``parlay2_*``                  two legs of the same game, paid at the product of
                               the two captured decimal odds.

Grading conventions actually used here (all of them stated, none of them quiet)
-------------------------------------------------------------------------------
* Spread and total are graded on the score at the end of regulation plus any
  overtime, because the NFL's own standings record the game as final at that
  point - the results feed carries no separate "end of first half" state.
* A whole-number line landing exactly on the result is a push and the stake is
  returned (0 units). Pushes are excluded from the hit-rate denominator and kept
  in the units denominator.
* A parlay containing a push leg is voided here (stake returned). Operator house
  rules differ on whether the parlay is reduced instead; that is open question
  MK-Q-06 and the difference is quantified in ``data/parlay_push_sensitivity.csv``.
* Odds are the ones the source displayed. No -110 is assumed anywhere in this
  file; where a price is missing the bet is dropped and the drop count is
  published, never silently replaced.
"""
from __future__ import annotations

import csv
import os

import statslib as st

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BT = os.path.join(DATA, "backtest_predictions.csv")


def _f(x):
    if x in ("", None):
        return None
    try:
        return float(x)
    except ValueError:
        return None


def dec(price):
    """Decimal profit per 1 unit staked (so -110 -> 0.9091)."""
    if price in ("", None):
        return None
    p = float(price)
    return (100.0 / abs(p)) if p < 0 else (p / 100.0)


def load_bt():
    with open(BT, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def legs_for(bt):
    """Every settled leg, one row per game per leg, with result and price."""
    rows = []
    for r in bt:
        sp = _f(r["market_spread_home"])
        tl = _f(r["market_total"])
        am = _f(r["actual_margin"])
        at = _f(r["actual_total"])
        if sp is None or am is None:
            continue
        home_res = "push" if am == sp else ("win" if am > sp else "loss")
        away_res = "push" if am == sp else ("win" if am < sp else "loss")
        over_res = under_res = None
        if tl is not None:
            over_res = "push" if at == tl else ("win" if at > tl else "loss")
            under_res = "push" if at == tl else ("win" if at < tl else "loss")
        ml_home = "push" if am == 0 else ("win" if am > 0 else "loss")
        ml_away = "push" if am == 0 else ("win" if am < 0 else "loss")
        d = dict(game_key=r["game_key"], season=r["season"], week=r["week"], date=r["date"],
                 away=r["away"], home=r["home"],
                 diff_spread=_f(r["diff_spread_pts"]), diff_total=_f(r["diff_total_pts"]),
                 model_p_home_su=_f(r["model_p_home_su"]),
                 fair_spread_home=_f(r["fair_spread_home"]), fair_total=_f(r["fair_total"]),
                 market_spread_home=sp, market_total=tl, actual_margin=am, actual_total=at,
                 source_url=r["market_source_url"], source=r["market_source"],
                 side_home_result=home_res, side_home_price=_f(r["market_home_spread_price"]),
                 side_away_result=away_res, side_away_price=_f(r["market_away_spread_price"]),
                 over_result=over_res, over_price=_f(r["market_over_price"]),
                 under_result=under_res, under_price=_f(r["market_under_price"]),
                 ml_home_result=ml_home, ml_home_price=_f(r["market_home_ml"]),
                 ml_away_result=ml_away, ml_away_price=_f(r["market_away_ml"]))
        rows.append(d)
    return rows


def _parlay(b, legs):
    """legs: list of (result_key, price_key). Returns (result, price_decimal, ok)."""
    res = []
    prices = []
    for rk, pk in legs:
        r_, p_ = b.get(rk), b.get(pk)
        if r_ is None or p_ is None:
            return None, None, False
        res.append(r_)
        prices.append(p_)
    if any(r_ == "push" for r_ in res):
        return "push", prices[0], 0.0, True
    offer = 1.0
    won = 1.0
    for r_, p_ in zip(res, prices):
        d = dec(p_)
        if d is None:
            return None, None, None, False
        offer *= (1.0 + d)                      # the parlay's own decimal odds
        won *= (1.0 + d) if r_ == "win" else 0.0
    # The break-even rate must come from the price on offer, not from the outcome,
    # or losses would silently drop out of the denominator.
    if len(res) == 1:
        return ("win" if won > 1.0 else "loss"), prices[0], (won - 1.0) if won > 1.0 else -1.0, True
    return ("win" if won > 1.0 else "loss"), american_from_decimal(offer - 1.0), \
        (won - 1.0) if won > 1.0 else -1.0, True


PARLAY_DEFS = {
    "side_home+over": (("side_home_result", "side_home_price"), ("over_result", "over_price")),
    "side_home+under": (("side_home_result", "side_home_price"), ("under_result", "under_price")),
    "side_away+over": (("side_away_result", "side_away_price"), ("over_result", "over_price")),
    "side_away+under": (("side_away_result", "side_away_price"), ("under_result", "under_price")),
}

# name -> (filter, legs, division, one-line hypothesis, registered parameters)
STRATEGIES = [
    ("S1 Side: model likes home by >= 1.5 pts",
     lambda b: (b["diff_spread"] or 0) >= 1.5,
     [("side_home_result", "side_home_price")], "singles",
     "when our fair home spread is at least 1.5 points better than the market's, the home side is worth taking", 1),
    ("S2 Side: model likes home by >= 3.0 pts",
     lambda b: (b["diff_spread"] or 0) >= 3.0,
     [("side_home_result", "side_home_price")], "singles",
     "the same claim at a bigger disagreement: bigger edge, fewer bets", 1),
    ("S3 Side: fade the market home price by >= 3.0 pts",
     lambda b: (b["diff_spread"] or 0) <= -3.0,
     [("side_away_result", "side_away_price")], "singles",
     "the mirror image of S2; if the model is right in one direction it should be right in the other", 1),
    ("S4 Total: over when our total is >= 3 pts above the market",
     lambda b: (b["diff_total"] or 0) >= 3.0,
     [("over_result", "over_price")], "singles",
     "the scoring model's disagreement about pace is tradable on the over side", 1),
    ("S5 Total: under when our total is <= -3 pts vs the market",
     lambda b: (b["diff_total"] or 0) <= -3.0,
     [("under_result", "under_price")], "singles",
     "the same disagreement, other side of the number", 1),
    ("S6 Side: take the model's side at any size",
     lambda b: b["diff_spread"] is not None and abs(b["diff_spread"]) >= 0.25,
     None, "singles",
     "no threshold at all: the raw model-vs-market sign, which is the honest measure of the signal itself", 0),
    ("S7 Moneyline: back home when model p >= 0.62",
     lambda b: (b["model_p_home_su"] or 0) >= 0.62,
     [("ml_home_result", "ml_home_price")], "singles",
     "the stage-3 derivation is tradable directly as a moneyline, not only as a spread", 1),
    ("S8 Moneyline: back away when model p_home <= 0.38",
     lambda b: 0 < (b["model_p_home_su"] or 1) <= 0.38,
     [("ml_away_result", "ml_away_price")], "singles",
     "the away mirror of S7", 1),
    ("P1 Parlay: model home side + over",
     lambda b: (b["diff_spread"] or 0) >= 1.5 and (b["diff_total"] or 0) >= 1.5,
     [("side_home_result", "side_home_price"), ("over_result", "over_price")], "parlays",
     "two legs the model likes in the same game, priced off the two captured leg prices", 2),
    ("P2 Parlay: model home side + under",
     lambda b: (b["diff_spread"] or 0) >= 1.5 and (b["diff_total"] or 0) <= -1.5,
     [("side_home_result", "side_home_price"), ("under_result", "under_price")], "parlays",
     "a cover on a small total: the legs are not obviously redundant", 2),
    ("P3 Parlay: model away side + over",
     lambda b: (b["diff_spread"] or 0) <= -1.5 and (b["diff_total"] or 0) >= 1.5,
     [("side_away_result", "side_away_price"), ("over_result", "over_price")], "parlays",
     "dog plus over, the classic same-game combo, priced rather than assumed", 2),
    ("P4 Parlay: model away side + under",
     lambda b: (b["diff_spread"] or 0) <= -1.5 and (b["diff_total"] or 0) <= -1.5,
     [("side_away_result", "side_away_price"), ("under_result", "under_price")], "parlays",
     "dog plus under", 2),
]


def _legs_for_leg_strategy(b):
    """S6 picks the side the model prefers, so its legs vary by game."""
    d = b["diff_spread"] or 0
    if d > 0:
        return [("side_home_result", "side_home_price")]
    if d < 0:
        return [("side_away_result", "side_away_price")]
    return []


def grade():
    """Returns (strategy_bets, leg_rows). strategy_bets: name -> list of bet dicts."""
    rows = legs_for(load_bt())
    with open(os.path.join(DATA, "settled_legs.csv"), "w", newline="", encoding="utf-8") as f:
        cols = list(rows[0].keys())
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r[k] is None else r[k]) for k in cols})

    by_strategy = {}
    for name, pred, legs, division, hypo, npar in STRATEGIES:
        bets = []
        skipped = 0
        for b in rows:
            if not pred(b):
                continue
            use = _legs_for_leg_strategy(b) if legs is None else legs
            if not use:
                continue
            res, price, pay, ok = _parlay(b, use)
            if not ok or res is None:
                skipped += 1
                continue
            n_legs = len(use)
            bets.append(dict(game_key=b["game_key"], season=b["season"], week=b["week"], date=b["date"],
                             selection=("multi-leg" if n_legs > 1 else use[0][0].split("_result")[0]),
                             legs=n_legs, result=res, price=price, pay_decimal=pay,
                             diff_spread=b["diff_spread"], diff_total=b["diff_total"],
                             model_p=b["model_p_home_su"], source_url=b["source_url"]))
        by_strategy[name] = dict(bets=bets, dropped_missing_price=skipped, division=division,
                                 hypothesis=hypo, thresholds=npar)
    return by_strategy, rows


def payout(bet):
    """Units won/lost on 1 unit staked. A push returns the stake (0).

    Multi-leg bets are paid from the exact product of the captured leg decimals,
    so the parlay payout reflects the two prices the source actually displayed.
    """
    if bet["result"] == "push":
        return 0.0
    if bet.get("pay_decimal") is not None:
        return bet["pay_decimal"]
    if bet.get("price") in (None, ""):
        return None
    d = dec(bet["price"])
    if d is None:
        return None
    return d if bet["result"] == "win" else -1.0


def american_from_decimal(mult):
    """Combined parlay multiplier -> an American price for display."""
    if mult is None:
        return None
    return round(-100.0 / mult) if mult < 1.0 else round(100.0 * mult)


def write():
    by_strategy, rows = grade()
    return by_strategy, rows


if __name__ == "__main__":
    bs, rows = write()
    for k, v in bs.items():
        print(f"{k[:46]:46s} n={len(v['bets']):5d} dropped={v['dropped_missing_price']}")

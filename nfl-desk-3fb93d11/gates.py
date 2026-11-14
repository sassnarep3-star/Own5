"""Validation gates, strategy backtests, the demotion gate, and a leaderboard
that scores SIGNAL separately from STAKING.

The separation is the point of this desk.  A leaderboard that mixes the two
lets a lucky staking run promote a signal that has no evidence behind it, so
here the two are scored on different axes, ranked independently, and only the
signal axis can certify or reward anything.
"""

from __future__ import annotations

import csv
import math
import os

from statslib import (american_to_decimal, binom_two_sided_p, deflated_sharpe,
                      implied_prob, mean, norm_cdf, pearson, sharpe_ratio,
                      stdev, wilson_interval)
from engine import (MarginModel, TotalsModel, TEAM_INDEX, fmt, INJURY_WK11_URL,
                    MIRROR_GAMES_URL, RETRIEVED_UTC)

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)

OFFICIAL_SCHEDULE_URL = "https://www.nfl.com/schedules/2026/"
GATES_SOURCE_URL = ("https://github.com/sassnarep3-star/Own5/blob/main/"
                    "nfl-desk-3fb93d11/gates.py")

FLAT_PRICE = -110.0                 # grading convention, see flag F-07
BREAKEVEN = implied_prob(FLAT_PRICE)
PARLAY_PRICE = american_to_decimal(-110.0) ** 2
PARLAY_BREAKEVEN = 1.0 / PARLAY_PRICE
N_FAMILIES = 8                      # families that produce graded bets
HOLM_ALPHA = 0.05


# --------------------------------------------------------------------------
# Pre-registered strategy families
# --------------------------------------------------------------------------
FAMILIES = [
    {"id": "S1", "name": "Model side edge >= 3.0 pts", "bet_class": "single",
     "market": "side",
     "rule": "Bet the side when the model's expected home margin differs from the "
             "reference line by at least 3.0 points.",
     "pre_registered": "yes", "parameters": "threshold = 3.0 pts (fixed before any result was seen)"},
    {"id": "S2", "name": "Model total edge >= 3.0 pts", "bet_class": "single",
     "market": "total",
     "rule": "Bet over/under when the model total differs from the reference total by at least 3.0 points.",
     "pre_registered": "yes", "parameters": "threshold = 3.0 pts"},
    {"id": "S3", "name": "Moneyline value >= 5 pp", "bet_class": "single",
     "market": "moneyline",
     "rule": "Bet the moneyline when the model's home win probability differs from the "
             "de-vigged market probability by at least 5 percentage points.",
     "pre_registered": "yes", "parameters": "threshold = 0.05 probability"},
    {"id": "S4", "name": "Home underdog >= 2.5", "bet_class": "single", "market": "side",
     "rule": "Back the home team when it is getting 2.5 points or more.",
     "pre_registered": "yes", "parameters": "handicap <= -2.5"},
    {"id": "S5", "name": "Rest edge >= 3 days", "bet_class": "single", "market": "side",
     "rule": "Back the team with at least three more days of rest than its opponent.",
     "pre_registered": "yes", "parameters": "rest differential >= 3 days"},
    {"id": "S6", "name": "Divisional home underdog", "bet_class": "single", "market": "side",
     "rule": "Back the home team in a divisional game when it is not favoured.",
     "pre_registered": "yes", "parameters": "divisional game and home handicap <= 0"},
    {"id": "S7", "name": "Fade large home favourite >= 10", "bet_class": "single", "market": "side",
     "rule": "Back the away team when the home side is favoured by 10 or more.",
     "pre_registered": "yes", "parameters": "home handicap >= 10"},
    {"id": "S8", "name": "Same-game side+total parlay", "bet_class": "parlay",
     "market": "side+total",
     "rule": "When the side and total models both fire on the same game, combine the two "
             "legs into a two-leg parlay.",
     "pre_registered": "yes",
     "parameters": "both S1 and S2 thresholds met; legs priced independently at -110"},
    {"id": "S9", "name": "Same-game prop combination", "bet_class": "prop combo",
     "market": "player props",
     "rule": "NOT TESTABLE - no official or otherwise sourced player-prop lines exist in "
             "this repo, so no leg can be priced or graded.",
     "pre_registered": "yes", "parameters": "none - blocked on data, see flag F-08"},
]


# --------------------------------------------------------------------------
# Backtest harness
# --------------------------------------------------------------------------
def _grade_side(handicap: float, home_margin: float) -> str:
    """handicap = points the home team is favoured by."""
    if home_margin > handicap:
        return "home"
    if home_margin < handicap:
        return "away"
    return "push"


def _grade_total(total_line: float, total_points: float) -> str:
    if total_points > total_line:
        return "over"
    if total_points < total_line:
        return "under"
    return "push"


def run_universe(games: list, universe: str, first_eval: int,
                 source_tier: str, source_url: str) -> dict:
    """Walk forward and grade every pre-registered family.

    `games` is chronological and carries a `period` key (a week for the official
    2026 feed, a season for the mirror history).  A period is only ever graded
    with parameters fitted on periods strictly earlier than it, and only once
    at least `first_eval` periods of history exist.
    """
    bets = {f["id"]: [] for f in FAMILIES}
    mm, tm = MarginModel(), TotalsModel()
    history: list = []
    periods = sorted({g["period"] for g in games})
    periods_done = 0
    sigma = 13.0                      # replaced by an out-of-sample estimate as soon as we have one

    for period in periods:
        cur = [g for g in games if g["period"] == period]
        if periods_done >= first_eval:
            mm.fit()
            tm.fit()
            window = history[-400:]
            resid = [g["home_margin"] - mm.predict(g["home"], g["away"], not g["neutral"])
                     for g in window]
            if len(resid) > 2:
                sigma = stdev(resid)
            for g in cur:
                _grade_game(g, mm, tm, sigma, bets, universe, source_tier, source_url)
        for g in cur:
            mm.add(g["home"], g["away"], float(g["home_margin"]), not g["neutral"])
            tm.add(g["home"], g["away"], float(g["total_points"]))
            history.append(g)
        periods_done += 1
    return {"bets": bets, "sigma": sigma, "graded_periods":
            sorted({b["period"] for v in bets.values() for b in v})}


def _grade_game(g, mm, tm, sigma, bets, universe, source_tier, source_url) -> None:
    home, away = g["home"], g["away"]
    neutral = bool(g["neutral"])
    model_side = mm.predict(home, away, neutral)
    model_total = tm.predict(home, away)
    market_side = g.get("market_side")
    market_total = g.get("market_total")
    home_margin = float(g["home_margin"])
    total_points = float(g["total_points"])
    season, period = g["season"], g["period"]
    gid = g["game_id"]

    # ---- S1 side ----
    if market_side is not None:
        diff = model_side - market_side
        if abs(diff) >= 3.0:
            pick = "home" if diff > 0 else "away"
            res = _grade_side(market_side, home_margin)
            win = 1 if res == pick else (0 if res != "push" else -1)
            rec = {"game_id": gid, "season": season, "period": period, "selection": pick,
                   "price": FLAT_PRICE, "breakeven": BREAKEVEN, "clv": abs(diff),
                   "universe": universe, "source_tier": source_tier, "source_url": source_url,
                   "result": win}
            bets["S1"].append(rec)
    # ---- S2 total ----
    if market_total is not None:
        tdiff = model_total - market_total
        if abs(tdiff) >= 3.0:
            pick = "over" if tdiff > 0 else "under"
            res = _grade_total(market_total, total_points)
            win = 1 if res == pick else (0 if res != "push" else -1)
            bets["S2"].append({"game_id": gid, "season": season, "period": period,
                               "selection": pick, "price": FLAT_PRICE, "breakeven": BREAKEVEN,
                               "clv": abs(tdiff), "universe": universe, "source_tier": source_tier,
                               "source_url": source_url, "result": win})
    # ---- S3 moneyline ----
    mp_home = g.get("market_prob_home")
    if market_side is not None and mp_home == mp_home:
        model_prob = norm_cdf(model_side / sigma)
        if abs(model_prob - mp_home) >= 0.05:
            pick = "home" if model_prob > mp_home else "away"
            won_home = home_margin > 0
            win = 1 if (pick == "home") == won_home else 0
            if home_margin == 0:
                win = -1      # a tie is a push on the moneyline
            bets["S3"].append({"game_id": gid, "season": season, "period": period,
                               "selection": pick, "price": FLAT_PRICE, "breakeven": BREAKEVEN,
                               "clv": abs(model_prob - mp_home) * 100, "universe": universe,
                               "source_tier": source_tier, "source_url": source_url, "result": win})
    # ---- S4 home underdog ----
    if market_side is not None and market_side <= -2.5:
        res = _grade_side(market_side, home_margin)
        win = 1 if res == "home" else (0 if res != "push" else -1)
        bets["S4"].append({"game_id": gid, "season": season, "period": period, "selection": "home",
                           "price": FLAT_PRICE, "breakeven": BREAKEVEN, "clv": "",
                           "universe": universe, "source_tier": source_tier,
                           "source_url": source_url, "result": win})
    # ---- S5 rest edge ----
    hr, ar = g.get("home_rest"), g.get("away_rest")
    if hr is not None and ar is not None and market_side is not None:
        if hr - ar >= 3:
            res = _grade_side(market_side, home_margin)
            win = 1 if res == "home" else (0 if res != "push" else -1)
            bets["S5"].append({"game_id": gid, "season": season, "period": period,
                               "selection": "home", "price": FLAT_PRICE, "breakeven": BREAKEVEN,
                               "clv": "", "universe": universe, "source_tier": source_tier,
                               "source_url": source_url, "result": win})
        elif ar - hr >= 3:
            res = _grade_side(market_side, home_margin)
            win = 1 if res == "away" else (0 if res != "push" else -1)
            bets["S5"].append({"game_id": gid, "season": season, "period": period,
                               "selection": "away", "price": FLAT_PRICE, "breakeven": BREAKEVEN,
                               "clv": "", "universe": universe, "source_tier": source_tier,
                               "source_url": source_url, "result": win})
    # ---- S6 divisional home dog ----
    if str(g.get("div_game", "")) == "1" and market_side is not None and market_side <= 0:
        res = _grade_side(market_side, home_margin)
        win = 1 if res == "home" else (0 if res != "push" else -1)
        bets["S6"].append({"game_id": gid, "season": season, "period": period, "selection": "home",
                           "price": FLAT_PRICE, "breakeven": BREAKEVEN, "clv": "",
                           "universe": universe, "source_tier": source_tier,
                           "source_url": source_url, "result": win})
    # ---- S7 fade big home favourite ----
    if market_side is not None and market_side >= 10:
        res = _grade_side(market_side, home_margin)
        win = 1 if res == "away" else (0 if res != "push" else -1)
        bets["S7"].append({"game_id": gid, "season": season, "period": period, "selection": "away",
                           "price": FLAT_PRICE, "breakeven": BREAKEVEN, "clv": "",
                           "universe": universe, "source_tier": source_tier,
                           "source_url": source_url, "result": win})
    # ---- S8 same-game parlay (side leg + total leg) ----
    if market_side is not None and market_total is not None:
        sdiff = model_side - market_side
        tdiff = model_total - market_total
        if abs(sdiff) >= 3.0 and abs(tdiff) >= 3.0:
            spick = "home" if sdiff > 0 else "away"
            tpick = "over" if tdiff > 0 else "under"
            sres = _grade_side(market_side, home_margin)
            tres = _grade_total(market_total, total_points)
            s_win = (sres == spick)
            t_win = (tres == tpick)
            pushed = (sres == "push" or tres == "push")
            if pushed:
                win = -1
            else:
                win = 1 if (s_win and t_win) else 0
            bets["S8"].append({"game_id": gid, "season": season, "period": period,
                               "selection": f"{spick} + {tpick}", "price": (PARLAY_PRICE - 1) * 100,
                               "breakeven": PARLAY_BREAKEVEN, "clv": abs(sdiff) + abs(tdiff),
                               "universe": universe, "source_tier": source_tier,
                               "source_url": source_url, "result": win})


def summarise(bets: list) -> dict:
    """Grade a family's bet log.  Pushes (result == -1) are excluded from the
    hit rate and from ROI, and reported separately."""
    graded = [b for b in bets if b.get("result") is not None]
    decided = [b for b in graded if b["result"] >= 0]
    pushes = [b for b in graded if b["result"] < 0]
    n = len(decided)
    wins = sum(1 for b in decided if b["result"] == 1)
    if n == 0:
        return {"n_bets": 0, "n_decided": 0, "n_pushes": 0, "wins": 0}
    breakeven = decided[0]["breakeven"]
    hit = wins / n
    p_be = binom_two_sided_p(wins, n, breakeven)
    p_flip = binom_two_sided_p(wins, n, 0.5)
    lo, hi = wilson_interval(wins, n)
    # flat-stake ROI in units of stake
    returns = []
    for b in decided:
        price = b["price"]
        dec = american_to_decimal(price)
        returns.append((dec - 1) if b["result"] == 1 else -1.0)
    roi = mean(returns)
    sr = sharpe_ratio(returns)
    dsr = deflated_sharpe(sr if sr == sr else 0.0, N_FAMILIES, n)
    clvs = [b["clv"] for b in decided if isinstance(b["clv"], (int, float))]
    return {
        "n_bets": len(graded), "n_decided": n, "n_pushes": len(pushes), "wins": wins,
        "hit_rate": hit, "breakeven": breakeven,
        "p_vs_breakeven": p_be, "p_vs_coinflip": p_flip,
        "ci95_low": lo, "ci95_high": hi,
        "flat_roi_per_unit": roi, "roi_pct": roi * 100,
        "sharpe": sr, "deflated_sharpe": dsr,
        "mean_clv": mean(clvs) if clvs else float("nan"),
        "returns": returns,
    }


def holm_adjust(rows: list) -> list:
    """Holm-Bonferroni step-down across the families that produced bets."""
    testable = [r for r in rows if r.get("p_vs_breakeven") == r.get("p_vs_breakeven")
                and r.get("n_decided", 0) > 0]
    testable.sort(key=lambda r: r["p_vs_breakeven"])
    m = len(testable)
    running = 0.0
    for i, r in enumerate(testable):
        adj = min(1.0, (m - i) * r["p_vs_breakeven"])
        running = max(running, adj)
        r["holm_p"] = running
        r["holm_significant"] = "yes" if running <= HOLM_ALPHA else "no"
    for r in rows:
        r.setdefault("holm_p", float("nan"))
        r.setdefault("holm_significant", "no")
    return rows


# --------------------------------------------------------------------------
# Gates
# --------------------------------------------------------------------------
GATES = [
    {"gate_id": "G0", "name": "Pre-registration",
     "source_url": GATES_SOURCE_URL, "provenance": "desk rule, committed in gates.py",
     "test": "The rule, its parameters and its bet class were written down before any "
             "result was inspected, with the commit that froze them.",
     "hard": "yes"},
    {"gate_id": "G1", "name": "Minimum sample",
     "source_url": GATES_SOURCE_URL, "provenance": "desk rule, committed in gates.py",
     "test": "At least 300 graded, non-pushed bets in the certification universe.",
     "hard": "yes"},
    {"gate_id": "G2", "name": "Price provenance",
     "source_url": GATES_SOURCE_URL, "provenance": "desk rule, committed in gates.py",
     "test": "Every graded bet links to a verified opening AND closing price snapshot in "
             "the price store with a UTC timestamp.",
     "hard": "yes"},
    {"gate_id": "G3", "name": "Out-of-sample only",
     "source_url": GATES_SOURCE_URL, "provenance": "desk rule, committed in gates.py",
     "test": "Each bet was produced by parameters fitted strictly before the period graded.",
     "hard": "yes"},
    {"gate_id": "G4", "name": "Beats the price",
     "source_url": GATES_SOURCE_URL, "provenance": "desk rule, committed in gates.py",
     "test": "Hit rate beats the break-even rate at the graded price, two-sided exact "
             "binomial, Holm-adjusted across the families.",
     "hard": "yes"},
    {"gate_id": "G5", "name": "Deflation",
     "source_url": GATES_SOURCE_URL, "provenance": "desk rule, committed in gates.py",
     "test": "Deflated Sharpe ratio >= 0.95 against 8 pre-registered families.",
     "hard": "yes"},
    {"gate_id": "G6", "name": "Economic realism",
     "source_url": GATES_SOURCE_URL, "provenance": "desk rule, committed in gates.py",
     "test": "Edge survives the documented -110 grading convention and a stated limit on "
             "stake size; no claim of unlimited liquidity.",
     "hard": "yes"},
    {"gate_id": "G7", "name": "Correlation audit (parlays / prop combos only)",
     "source_url": GATES_SOURCE_URL, "provenance": "desk rule, committed in gates.py",
     "test": "Every leg pair has a published joint estimate from an official source, or the "
             "family is refused.  Independent pricing of correlated legs is not permitted.",
     "hard": "yes"},
    {"gate_id": "G8", "name": "Certification universe is official",
     "source_url": GATES_SOURCE_URL, "provenance": "desk rule, committed in gates.py",
     "test": "The bets being certified were graded against results from an official "
             "publisher, not a mirror.",
     "hard": "yes"},
]

DEMOTION_GATE = {
    "gate_id": "D1",
    "name": "Demotion gate - live back to paper",
    "purpose": "A strategy that has been promoted to live staking is returned to paper the "
               "moment any one of the triggers below fires.  Demotion is automatic: it does "
               "not wait for a review meeting and it cannot be overridden by a good week.",
    "triggers": [
        ("D1a", "Rolling 200-bet closing-line value <= 0.00",
         "the market now agrees with us, so the edge we were paid for is gone"),
        ("D1b", "Drawdown from peak >= 20% of the reference bankroll",
         "the realised path is outside the risk the owner agreed to"),
        ("D1c", "Most recent 100 graded bets fail to beat break-even at p < 0.10 one-sided",
         "recent results are inconsistent with the certified edge"),
        ("D1d", "Any parameter or rule changed from the pre-registered commit",
         "the thing being traded is no longer the thing that was validated"),
        ("D1e", "Any graded bet lacks a verified opening or closing price snapshot",
         "the evidence chain is broken, so the result cannot be audited"),
        ("D1f", "The certification universe's official results feed lags by more than one week",
         "we would be marking our own homework against stale data"),
    ],
    "re_promotion": "Re-promotion requires a fresh pass through G0-G8 on bets logged after "
                    "the demotion, with the demotion and its trigger recorded in the decision log.",
    "current_state": "Armed. No strategy has ever been promoted to live, so no trigger has "
                     "fired; every family sits in PAPER.",
}


def evaluate_gates(summary: dict, fam: dict, universe_tier: str) -> list:
    rows = []
    n = summary.get("n_decided", 0)
    hit = summary.get("hit_rate", float("nan"))
    holm = summary.get("holm_p", float("nan"))
    dsr = summary.get("deflated_sharpe", float("nan"))
    checks = [
        ("G0", "pass" if fam["pre_registered"] == "yes" else "fail",
         "rule and parameters fixed before results were seen"),
        ("G1", "pass" if n >= 300 else f"fail (n = {n})",
         "minimum 300 graded bets"),
        ("G2", "fail", "no verified opening/closing operator price exists - flag F-01"),
        ("G3", "pass" if n else "not evaluated",
         "walk-forward fit; parameters predate every graded bet"),
        ("G4", "pass" if (holm == holm and holm <= HOLM_ALPHA and hit == hit and hit > summary.get("breakeven", 1))
          else "fail", f"holm p = {fmt(holm, 4)} at alpha {HOLM_ALPHA}"),
        ("G5", "pass" if (dsr == dsr and dsr >= 0.95) else f"fail ({fmt(dsr, 3)})",
         "deflated Sharpe >= 0.95 over 8 families"),
        ("G6", "not evaluated",
         "no bankroll or limit has been declared by the owner - question Q-03"),
        ("G7", "pass" if fam["bet_class"] == "single" else "fail",
         "parlay/prop legs have no officially sourced joint estimate - flag F-08"
         if fam["bet_class"] != "single" else "single bet, no leg pair to audit"),
        ("G8", "pass" if universe_tier == "OFFICIAL" else "fail",
         f"graded against {universe_tier} results"),
    ]
    for gid, result, note in checks:
        rows.append({"strategy_id": fam["id"], "strategy": fam["name"], "gate_id": gid,
                     "result": result, "note": note,
                     "universe_tier": universe_tier,
                     "source_url": "https://www.nfl.com/schedules/2026/by-week/"})
    return rows


# --------------------------------------------------------------------------
# Leaderboard: signal and staking scored apart
# --------------------------------------------------------------------------
def score_signal(s: dict) -> float:
    """Signal quality only.  Deliberately blind to the size of the profit a
    staking rule happened to produce.

    Direction matters: a strategy that is significantly WORSE than break-even
    has strong evidence against it, so significance is rewarded only when the
    hit rate is on the right side of the price and penalised when it is not.
    """
    if not s.get("n_decided"):
        return float("nan")
    n = s["n_decided"]
    excess = s["hit_rate"] - s["breakeven"]
    shrink = n / (n + 300.0)          # shrink the observed excess toward zero
    dsr = s.get("deflated_sharpe", float("nan"))
    dsr_term = max(0.0, min(1.0, dsr)) if dsr == dsr else 0.0
    sig = 0.45 * (100 * excess * shrink)
    sig += 0.35 * 100 * dsr_term
    sig += 0.20 * 100 * shrink
    if s.get("holm_significant") == "yes":
        sig += 10 if excess > 0 else -15      # significantly bad is worse than inconclusive
    return sig


def score_staking(s: dict) -> float:
    """Realised money only.  This is the axis a lucky run can win."""
    if not s.get("n_decided"):
        return float("nan")
    roi = s.get("roi_pct", float("nan"))
    if roi != roi:
        return float("nan")
    sr = s.get("sharpe", float("nan"))
    return roi * 2.0 + (10.0 * min(max(sr, -3.0), 3.0) if sr == sr else 0.0)


def build_leaderboard(rows: list) -> list:
    """Rank within a board, never across universes.

    Two boards exist:
      * CERTIFICATION - bets graded against the official results feed.  This is
        the only board that can certify a strategy or pay a reward.
      * RESEARCH - bets graded against the pinned mirror.  Context and sample
        size only; a research-board rank has no standing.

    On every board the signal axis and the staking axis are ranked separately.
    """
    for r in rows:
        r["board"] = ("CERTIFICATION" if r["universe"].startswith("OFFICIAL")
                      else "RESEARCH (context only)")
        r["source_url"] = (OFFICIAL_SCHEDULE_URL if r["board"] == "CERTIFICATION"
                           else MIRROR_GAMES_URL)
        r["source_tier"] = ("OFFICIAL (nfl.com)" if r["board"] == "CERTIFICATION"
                            else "AGGREGATOR (pinned mirror)")
    for board in ("CERTIFICATION", "RESEARCH (context only)"):
        group = [r for r in rows if r["board"] == board and r.get("n_decided", 0) > 0]
        for r in group:
            r["signal_score"] = score_signal(r)
            r["staking_score"] = score_staking(r)
        by_signal = sorted(group, key=lambda r: (
            r["signal_score"] != r["signal_score"],
            -(r["signal_score"] if r["signal_score"] == r["signal_score"] else 0)))
        by_staking = sorted(group, key=lambda r: (
            r["staking_score"] != r["staking_score"],
            -(r["staking_score"] if r["staking_score"] == r["staking_score"] else 0)))
        s_rank = {r["row_id"]: i + 1 for i, r in enumerate(by_signal)}
        k_rank = {r["row_id"]: i + 1 for i, r in enumerate(by_staking)}
        for r in group:
            r["signal_rank"] = s_rank[r["row_id"]]
            r["staking_rank"] = k_rank[r["row_id"]]
            r["rank_gap"] = r["signal_rank"] - r["staking_rank"]
            r["board_size"] = len(group)
            gates_ok = r.get("gates_passed", 0) >= r.get("gates_hard", 1)
            r["certified"] = "no"
            r["state"] = "PAPER"
            r["note"] = ("certification needs verified opening and closing prices (gate G2) and "
                         "an official-universe sample (G8); neither exists yet")
            if not gates_ok and r["staking_rank"] == 1 and r["signal_rank"] > 1:
                r["note"] = (f"STAKING-ONLY LEADER on {r['n_decided']} bets - first on realised "
                             f"money, {r['signal_rank']} of {len(group)} on signal. On this board "
                             "the staking axis cannot certify or reward anything. This is exactly "
                             "the case the split was built to expose.")
        for r in [x for x in rows if x["board"] == board and x.get("n_decided", 0) == 0]:
            r["note"] = ("no graded bets - the rule never fired, or the data required to price "
                         "it does not exist (see the family's rule text)")
    return rows

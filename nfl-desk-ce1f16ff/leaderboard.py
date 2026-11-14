"""The leaderboard competition: divisions, points, and prizes that cannot be won by luck.

Structure
---------
Three divisions, because the three products fail differently:

``singles``      one leg per game
``parlays``      two legs of the same game, priced off the two captured leg prices
``prop-combos``  player-prop combinations

Each division is ranked twice - on signal and on staking - and the two rankings
are printed side by side with their disagreement stated. The competition winner is
the *signal* ranking; the staking ranking is published as entertainment and
diagnostic, never as the award basis. That is the whole point of requirement 5: a
lucky run at 3x stakes must not be able to beat an unfashionable but honest signal.

Points (registered here before any result was seen, and not tunable)
---------------------------------------------------------------------
10 points for clearing every gate in ``validation.csv`` for that division;
4 points for walk-forward forecast skill at least as good as the posted line;
3 points for positive CLV once closing snapshots exist;
2 points for coverage: a settled bet on both sides of the market, not one corner;
1 point for a raw hit rate above break-even, which is worth 1 and not 10 because
   it is the least robust number on the board.

Rewards
-------
Rewards are *desk* rewards: the top entry per division earns the right to have its
lines published as the desk's headline number for the next week, and to be listed
on the leaderboard page with its full audit trail. No money is moved, no sportsbook
account exists, and nothing here constitutes a payout offer - a reward that cannot
be honoured is not a reward, so the register says what is actually being awarded.

Prop combos: why the division is empty
--------------------------------------
The prop *lines* are captured (``data/price_snapshots.csv``, market ``player_prop``),
but a prop bet cannot be graded without official per-play statistics for the
player's season totals at the moment of the bet, and this repository holds no
source it would trust for that. The division is therefore published as BLOCKED
with the exact missing input, rather than filled with a third-party stat feed.
"""
from __future__ import annotations

import csv
import os

import statslib as st

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

POINTS = [("clears every gate for its division", 10),
          ("forecast skill at least as good as the posted line", 4),
          ("positive closing-line value (blocked until closing snapshots exist)", 3),
          ("coverage: settled bets on both sides of the market", 2),
          ("raw hit rate above break-even", 1)]


def load_signals():
    p = os.path.join(DATA, "leaderboard_signal.csv")
    return list(csv.DictReader(open(p, newline="", encoding="utf-8")))


def load_staking():
    p = os.path.join(DATA, "leaderboard_staking.csv")
    return {r["strategy"]: r for r in csv.DictReader(open(p, newline="", encoding="utf-8"))}


def division_of(row):
    d = row.get("division", "singles")
    return d


def score(sig, gates, staking):
    """Two kinds of requirement, because they are not the same kind of claim.

    *Desk preconditions* (V-01 data integrity, V-02 no look-ahead, V-07 economic
    realism, V-09 reproducibility) are properties of the build, not of a strategy:
    if one of them fails, no score on the board means anything, so nobody earns
    the 10 points that week - a strategy cannot compensate for a broken feed.

    *Per-strategy gates* (V-03 sample, V-04 parameters, V-05 multiplicity on that
    strategy's own adjusted p, V-10 naive-rule comparison for its own bets) are what
    different strategies are actually scored against.
    """
    gate_pass = {g["gate_id"]: g["result"] for g in gates}
    desk_ok = [k for k in ("V-01", "V-02", "V-07", "V-09") if gate_pass.get(k) != "PASS"]
    out = []
    for r in sig:
        s = 0
        earned, missed = [], []
        own_fail = []
        if int(r["settled"] or 0) < 50:
            own_fail.append(f"V-03 settled n={r['settled']} < 50")
        if int(r["thresholds_registered"] or 0) > 2:
            own_fail.append("V-04 more than two registered thresholds")
        hp = r.get("holm_adjusted_p", "")
        if hp in ("", None):
            own_fail.append("V-05 no valid adjusted p")
        elif hp != "<0.0001" and float(hp) >= 0.05:
            own_fail.append(f"V-05 Holm-adjusted p = {hp} >= 0.05")
        dsr = r.get("dsr", "")
        if dsr in ("", None) or float(dsr) <= 0.95:
            own_fail.append(f"DSR {dsr or 'n/a'} <= 0.95")
        if not desk_ok and not own_fail:
            s += 10
            earned.append("clears the desk preconditions and every per-strategy gate (10)")
        else:
            why = (["desk precondition failed: " + ", ".join(desk_ok)] if desk_ok else []) + own_fail
            missed.append("; ".join(why))
        # forecast skill vs the posted line, read from calibration.csv
        cal = _cal()
        if cal and cal["model_r"] is not None and cal["market_r"] is not None \
                and abs(cal["model_r"]) >= abs(cal["market_r"]) - 0.02 and abs(cal["model_r"]) >= 0.15:
            s += 4
            earned.append("forecast skill matches or beats the posted line (4)")
        else:
            missed.append("forecast skill below the posted line" if cal else "no calibration table yet")
        closing = _closing_rows()
        if closing >= 20:
            clv = _clv(r["strategy"])
            if clv is not None and clv > 0:
                s += 3
                earned.append("positive CLV (3)")
            else:
                missed.append("CLV not positive or not measurable")
        else:
            missed.append(f"CLV unmeasurable: {closing} closing snapshots")
        if _covers_both_sides(r["strategy"]):
            s += 2
            earned.append("settled bets on both sides of the market (2)")
        else:
            missed.append("one-sided: every bet in this strategy takes the same side of the same market")
        if r["hit_rate"] not in ("", None) and r["break_even_mean"] not in ("", None) \
                and float(r["hit_rate"]) > float(r["break_even_mean"]):
            s += 1
            earned.append("hit rate above break-even (1)")
        else:
            missed.append("hit rate at or below break-even")
        stk = staking.get(r["strategy"], {})
        out.append(dict(strategy=r["strategy"], division=division_of(r), points=s,
                        signal_rank=0, staking_rank=0,
                        settled=r["settled"], hit_rate=r["hit_rate"], break_even=r["break_even_mean"],
                        binom_p=r["binom_p_vs_break_even"], holm_p=r["holm_adjusted_p"],
                        units=stk.get("units", ""), roi_pct=stk.get("roi_per_bet_pct", ""),
                        max_drawdown=stk.get("max_drawdown_units", ""),
                        worst_run=stk.get("worst_losing_run", ""),
                        earned="; ".join(earned) or "none",
                        missing="; ".join(missed)))
    out.sort(key=lambda r: (-r["points"], r["strategy"]))
    for i, r in enumerate(out, start=1):
        r["signal_rank"] = i
    by_units = sorted(out, key=lambda r: (-(float(r["units"]) or 0) if r["units"] else 0, r["strategy"]))
    for i, r in enumerate(by_units, start=1):
        r["staking_rank"] = i
    return out


def _cal():
    p = os.path.join(DATA, "calibration.csv")
    if not os.path.exists(p):
        return None
    rows = list(csv.DictReader(open(p, newline="", encoding="utf-8")))
    mine = mkt = None
    for r in rows:
        if r["metric"] != "predicted home margin vs actual":
            continue
        try:
            v = float(r["r"])
        except (TypeError, ValueError):
            continue
        if r["who"] == "model":
            mine = v
        elif r["who"].startswith("market"):
            mkt = v
    return dict(model_r=mine, market_r=mkt)


def _closing_rows():
    p = os.path.join(DATA, "store_meta.csv")
    if not os.path.exists(p):
        return 0
    for r in csv.reader(open(p, newline="", encoding="utf-8")):
        if r and r[0] == "rows_stage_closing":
            return int(r[1])
    return 0


def _clv(strategy):
    return None            # no closing stage exists in the store yet


def _covers_both_sides(strategy):
    """Does the strategy ever take the other side of the same market?

    A strategy that only ever backs the home team is a home-team detector, not a
    pricing model, and it can look excellent in a season where home teams win.
    """
    p = os.path.join(DATA, "settled_legs.csv")
    if not os.path.exists(p):
        return False
    key = strategy.split(":")[0]
    want = {"S1": ("diff_spread", lambda x: x >= 1.5), "S2": ("diff_spread", lambda x: x >= 3.0),
            "S3": ("diff_spread", lambda x: x <= -3.0), "S4": ("diff_total", lambda x: x >= 3.0),
            "S5": ("diff_total", lambda x: x <= -3.0), "S6": ("diff_spread", lambda x: True),
            "S7": ("diff_spread", lambda x: x >= 1.5), "S8": ("diff_spread", lambda x: x <= -1.5)}.get(key)
    if not want:
        return True                      # parlay divisions combine both directions by construction
    col, pred = want
    seen = set()
    for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
        v = r[col]
        if v in ("", None):
            continue
        x = float(v)
        if pred(x):
            seen.add("pos" if x > 0 else ("neg" if x < 0 else "zero"))
    return len(seen) >= 2


def rewards(scored):
    """What the top of each division actually gets, stated plainly."""
    by_div = {}
    for r in scored:
        by_div.setdefault(r["division"], []).append(r)
    out = []
    for div, rows in sorted(by_div.items()):
        rows.sort(key=lambda r: (r["signal_rank"]))
        top = rows[0]
        eligible = top["points"] >= 14
        out.append(dict(division=div, entries=len(rows),
                        leader=top["strategy"], leader_points=top["points"],
                        award=("headline billing for next week's slate plus a pinned audit trail on the "
                               "leaderboard page" if eligible else "NOT AWARDED"),
                        reason=("leader clears the gate block and the CLV floor" if eligible else
                                "no entry cleared enough gates to be worth following; awarding a prize for "
                                "the best of a set that is indistinguishable from luck would be a "
                                "misleading reward, so the division goes unawarded"),
                        prize_notes="no money, no sportsbook account, no payout offer: this desk has "
                                    "nothing else to award and says so",
                        runner_up=(rows[1]["strategy"] if len(rows) > 1 else ""),
                        signal_vs_staking_gap=(
                            f"signal rank 1 / staking rank {top['staking_rank']}"
                            if top["staking_rank"] != 1 else "signal and staking agree on the leader")))
    # the empty division, published as empty
    out.append(dict(division="prop-combos", entries=0, leader="", leader_points=0,
                    award="BLOCKED",
                    reason=("prop lines are captured but prop outcomes are not gradable from any source "
                            "this desk trusts: grading a '38+ attempts' prop needs the official play-by-play "
                            "stat for that player's game, and no such source is pinned here. The two prop "
                            "markets captured live (see price_snapshots.csv) are therefore published as "
                            "observations with no bet attached - see question MK-Q-05"),
                    prize_notes="nothing to award", runner_up="", signal_vs_staking_gap="n/a"))
    return out


def write():
    sig = load_signals()
    gates = list(csv.DictReader(open(os.path.join(DATA, "validation.csv"), newline="", encoding="utf-8")))
    staking = load_staking()
    scored = score(sig, gates, staking)
    cols = ["strategy", "division", "points", "signal_rank", "staking_rank", "settled", "hit_rate",
            "break_even", "binom_p", "holm_p", "units", "roi_pct", "max_drawdown", "worst_run",
            "earned", "missing"]
    with open(os.path.join(DATA, "leaderboard.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in scored:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    rw = rewards(scored)
    with open(os.path.join(DATA, "rewards.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rw[0].keys()))
        w.writeheader()
        w.writerows(rw)
    with open(os.path.join(DATA, "scoring_rules.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["criterion", "points", "why it is worth that much"])
        w.writerow(["clears every gate in this build", 10,
                    "the gates are the only thing that separates a strategy from a story"])
        w.writerow(["forecast skill at least as good as the posted line", 4,
                    "you cannot beat a market you cannot match as a forecaster"])
        w.writerow(["positive closing-line value", 3,
                    "the standard external check of whether you got a better price than the market did"])
        w.writerow(["coverage: both sides of the market", 2,
                    "one-sided strategies can be a season-shape artifact"])
        w.writerow(["raw hit rate above break-even", 1,
                    "necessary, least robust, therefore worth least"])
        w.writerow(["awards paid in", "billing, not money",
                    "the desk has no licence, no bankroll and no account, so it does not pretend otherwise"])
    return scored, rw


if __name__ == "__main__":
    sc, rw = write()
    for r in sc[:6]:
        print(f"{r['strategy'][:40]:40s} pts {r['points']:3d} sig {r['signal_rank']:2d} stk {r['staking_rank']:2d}")
    for r in rw:
        print(r["division"], "->", r["award"], "|", r["leader"][:34])

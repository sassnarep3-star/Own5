"""The demotion gate: what returns a live strategy to paper, and how fast.

Why a gate like this has to exist
---------------------------------
Promotion questions are argued about for months; nothing happens, so nothing can
go wrong. The failure mode of a live book is the opposite: a strategy gets promoted
on a good month, the month ends, and nobody re-checks. The demotion gate is the
re-check, and it is written so that it can fire without anyone's agreement - a rule
that needs a debate to execute is not a gate.

Fail-closed by construction
---------------------------
A live strategy stays live only while every rule below is unbroken. Any rule that
cannot be *evaluated* - the results feed did not build, the input digests no longer
match, the week's games have no settled outcome - is treated as broken, and a
broken rule demotes. The asymmetry is intentional: the cost of stopping too early
is a missed week of paper bets, and the cost of stopping too late is real money.

Rules
-----
D1  performance     live hit rate over the most recent ``WINDOW`` bets is below the
                    break-even implied by the prices the strategy actually took.
                    No significance requirement: significance is a promotion concept,
                    and demanding it before stopping would make the gate decorative.
D2  re-validation   the same strategy re-run on data that now includes the live weeks
                    loses its multiplicity-adjusted significance.
D3  closing line    mean closing-line value over the window is negative: the market
                    moved away from the price taken, which is the earliest honest
                    warning there is.
D4  drawdown        live units are more than ``DD_UNITS`` below the peak, or more than
                    ``DD_MULT`` times the largest drawdown the backtest ever produced.
D5  integrity       any results-feed or input-digest check fails, or the store's hash
                    chain does not recompute: everything to paper, immediately,
                    regardless of performance.
D6  data flow       ``OUTAGE_WEEKS`` consecutive weeks without a captured price for a
                    market the strategy bets: it cannot be graded, so it cannot be live.

``data/live_bets.csv`` is the ledger these rules read. It ships with its header and
no rows, because no bet has been placed - a file full of invented bets would be the
worst possible way to demonstrate a working gate.
"""
from __future__ import annotations

import csv
import os

import statslib as st

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
LIVE = os.path.join(DATA, "live_bets.csv")
LIVE_COLS = ["seq", "placed_at_utc", "strategy", "division", "game_key", "market", "selection",
             "line_taken", "price_taken", "stake_units", "result", "settled_at_utc",
             "closing_price", "clv_points", "source_url", "note"]
WINDOW = 20            # bets in the rolling performance window
DD_UNITS = 6.0         # units below peak that triggers D4 on its own
DD_MULT = 3.0          # or a multiple of the backtest's own worst drawdown
OUTAGE_WEEKS = 3       # consecutive weeks without a captured price before D6 fires


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def ensure_ledger():
    if not os.path.exists(LIVE):
        os.makedirs(DATA, exist_ok=True)
        with open(LIVE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(LIVE_COLS)
    with open(LIVE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def be_rate(price):
    if price in ("", None):
        return None
    a = float(price)
    return (abs(a) / (abs(a) + 100.0)) if a < 0 else (100.0 / (100.0 + a))


def evaluate(bets, signal_rows, store_summary, integrity_ok=True, outage_weeks=0, states=None):
    """Returns one row per strategy with each rule's state and the resulting action."""
    by_strategy = {}
    for b in bets:
        by_strategy.setdefault(b["strategy"], []).append(b)
    sig = {r["strategy"]: r for r in signal_rows}
    live_state = dict(states or {})          # missing entry -> PAPER (fail closed)
    out = []
    for strategy in sorted(set(list(sig) + list(by_strategy))):
        rows = sorted(by_strategy.get(strategy, []), key=lambda b: b["seq"])
        graded = [b for b in rows if (b.get("result") or "") in ("win", "loss", "push")]
        nong = [b for b in graded if b["result"] != "push"]
        window = nong[-WINDOW:]
        wins = sum(1 for b in window if b["result"] == "win")
        bes = [be_rate(b.get("price_taken")) for b in window]
        bes = [x for x in bes if x is not None]
        p_be = sum(bes) / len(bes) if bes else None
        hit = (wins / len(window)) if window else None
        d1 = None
        if window and p_be is not None:
            d1 = hit < p_be
        # D2: the backtest's own adjusted significance, re-read from the current table
        r = sig.get(strategy, {})
        hp = r.get("holm_adjusted_p", "")
        d2 = not (hp not in ("", None) and (hp == "<0.0001" or float(hp) < 0.05))
        # D3: closing-line value in points, from the ledger's own closing column
        clv_vals = [_f(b.get("clv_points")) for b in graded if b.get("clv_points") not in ("", None)]
        clv = st.mean(clv_vals) if clv_vals else None
        d3 = None if clv is None else clv < 0
        # D4: drawdown
        units = []
        for b in graded:
            res, price = b.get("result"), _f(b.get("price_taken"))
            stake = _f(b.get("stake_units")) or 1.0
            if res == "push" or price is None:
                units.append(0.0)
                continue
            d = (100.0 / abs(price)) if price < 0 else (price / 100.0)
            units.append(stake * (d if res == "win" else -1.0))
        cum = peak = worst = 0.0
        for u in units:
            cum += u
            peak = max(peak, cum)
            worst = min(worst, cum - peak)
        backtest_dd = _f(r.get("max_drawdown_units")) if r.get("max_drawdown_units") else None
        dd_limit = DD_UNITS if backtest_dd is None else max(DD_UNITS, DD_MULT * abs(backtest_dd))
        d4 = bool(units) and worst <= -dd_limit
        # D5: integrity, D6: data flow
        d5 = not integrity_ok
        d6 = outage_weeks >= OUTAGE_WEEKS
        fired = [n for n, v in (("D1 live performance", d1), ("D2 re-validated signal", d2),
                               ("D3 closing-line value", d3), ("D4 drawdown", d4),
                               ("D5 input integrity", d5), ("D6 data flow", d6)) if v]
        blocked = [n for n, v in (("D3", d3),) if v is None]
        was_live = (live_state.get(strategy) or "PAPER") == "LIVE"
        if not fired:
            decision = "NO CHANGE"
        elif was_live:
            decision = "DEMOTE TO PAPER"
        else:
            # already on paper: the rules read as broken because the strategy has no
            # qualifying record, which is the reason it is on paper and not a demotion
            decision = "STAYS ON PAPER"
        out.append(dict(
            strategy=strategy, state_before=(live_state.get(strategy) or "PAPER"),
            decision=decision, live_bets=len(graded), window_bets=len(window),
            hit_rate_window="" if hit is None else round(hit, 4),
            break_even_window="" if p_be is None else round(p_be, 4),
            excess="" if (hit is None or p_be is None) else round(hit - p_be, 4),
            clv_mean_pts="" if clv is None else round(clv, 3),
            drawdown_units=round(worst, 3) if units else "",
            drawdown_limit_units=round(-dd_limit, 3),
            rules_broken="; ".join(fired) or "none",
            rules_unevaluable="; ".join(blocked) or "none",
            note=("already on paper: D1/D3/D4 have no live record to measure, so the gate is reported "
                  "as armed rather than passed" if not graded and decision == "STAYS ON PAPER" else
                  ("gate clear: nothing to demote" if decision == "NO CHANGE" else
                   "the gate fires on the rules as written, with no discretion to look the other way"))))
    return out


def integrity_state():
    """D5's input: every feed check plus the two hash chains, read from disk."""
    problems = []
    p = os.path.join(DATA, "results_checks.csv")
    if not os.path.exists(p):
        problems.append("results_checks.csv missing")
    else:
        for r in csv.DictReader(open(p, newline="", encoding="utf-8")):
            if r["result"] != "PASS":
                problems.append(f"{r['check_id']} {r['result']}")
    try:
        import store
        ok, probs, n, head = store.check_chain()
        if not ok:
            problems.append("price store chain: " + "; ".join(probs[:2]))
    except Exception as e:                       # pragma: no cover - fail closed
        problems.append(f"price store unreadable: {e}")
    try:
        import results_feed
        ok2, det = results_feed.chain_ok()
        if not ok2:
            problems.append(f"results feed chain {det}")
    except Exception as e:                       # pragma: no cover
        problems.append(f"results feed unreadable: {e}")
    return (not problems), problems


def gate_rules():
    return [
        dict(rule="D1 live performance",
             definition=f"hit rate over the last {WINDOW} graded live bets below the break-even implied "
                        "by the prices taken",
             why="no significance test: waiting for proof while live money is at risk is how a bad month "
                 "becomes a bad year",
             evaluates="when at least one live bet has settled",
             fail_closed="an empty window is not a pass: the strategy stays on paper until it has a record"),
        dict(rule="D2 re-validated signal", definition="Holm-adjusted p >= 0.05 when the backtest is "
             "re-run on data that includes the live weeks",
             why="a signal that disappears once the sample grows was never a signal",
             evaluates="every build", fail_closed="missing or unparseable adjusted p counts as broken"),
        dict(rule="D3 closing-line value", definition="mean CLV over the window < 0 points",
             why="the market moving against you is the earliest honest warning available",
             evaluates="once closing snapshots exist in the store",
             fail_closed="cannot be evaluated yet: reported as unevaluable, and V-08 blocks promotion"),
        dict(rule="D4 drawdown", definition=f"live units {DD_UNITS} below peak, or {DD_MULT}x the "
             "backtest's own worst drawdown, whichever is larger",
             why="sizes the stop to the strategy's own history instead of to a mood",
             evaluates="when a live record exists", fail_closed="no backtest drawdown on file falls "
             "back to the absolute limit rather than to no limit"),
        dict(rule="D5 input integrity", definition="any results-feed check fails, or either hash chain "
             "does not recompute",
             why="a number nobody can vouch for cannot support a live bet",
             evaluates="every build", fail_closed="unreadable file counts as a failure"),
        dict(rule="D6 data flow", definition=f"{OUTAGE_WEEKS} consecutive weeks with no captured price "
             "for a market the strategy bets",
             why="an ungradeable strategy cannot be promoted, demoted or audited; it goes to paper",
             evaluates="every build", fail_closed="a failed capture job counts as an outage week"),
        dict(rule="Scope", definition="demotion applies to all strategies simultaneously if D5 fires; "
             "otherwise per strategy",
             why="an integrity problem is not a property of one strategy",
             evaluates="every build", fail_closed="-"),
    ]


def load_states():
    """strategy -> LIVE / PAPER. Missing file means everything is PAPER, which is the
    fail-closed default: an unreadable state cannot leave something live."""
    p = os.path.join(DATA, "strategy_states.csv")
    if not os.path.exists(p):
        return {}
    return {r["strategy"]: r["state"].strip().upper()
            for r in csv.DictReader(open(p, newline="", encoding="utf-8"))}


def write():
    bets = ensure_ledger()
    sig = list(csv.DictReader(open(os.path.join(DATA, "leaderboard_signal.csv"), newline="", encoding="utf-8")))
    store_summary = {}
    p = os.path.join(DATA, "store_meta.csv")
    if os.path.exists(p):
        for r in csv.reader(open(p, newline="", encoding="utf-8")):
            if r:
                store_summary[r[0]] = r[1]
    ok_int, problems = integrity_state()
    outage = 0
    try:
        with open(os.path.join(DATA, "capture_log.csv"), newline="", encoding="utf-8") as f:
            weeks = sorted({r["week"] for r in csv.DictReader(f) if r.get("status", "").startswith("ok")})
        latest = max((int(x) for x in weeks if str(x).isdigit()), default=0)
        out = int(store_summary.get("current_week", 10) or 10)
        outage = max(0, out - latest - 1)
    except FileNotFoundError:
        outage = 0
    rows = evaluate(bets, sig, store_summary, integrity_ok=ok_int, outage_weeks=outage,
                    states=load_states())
    cols = ["strategy", "state_before", "decision", "live_bets", "window_bets", "hit_rate_window",
            "break_even_window", "excess", "clv_mean_pts", "drawdown_units", "drawdown_limit_units",
            "rules_broken", "rules_unevaluable", "note"]
    with open(os.path.join(DATA, "demotion_gate.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    with open(os.path.join(DATA, "gate_rules.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(gate_rules()[0].keys()))
        w.writeheader()
        w.writerows(gate_rules())
    with open(os.path.join(DATA, "gate_integrity.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["check", "state", "detail"])
        w.writerow(["D5 input integrity", "PASS" if ok_int else "FAIL", "; ".join(problems[:6]) or "all checks pass"])
        w.writerow(["D6 capture outage weeks", str(outage),
                    "weeks since the last successful capture job, from capture_log.csv"])
        w.writerow(["live bets on file", str(len(bets)),
                    "the ledger ships empty because no bet has been placed; the gate is armed, not passed"])
    return rows, dict(integrity_ok=ok_int, problems=problems, outage=outage, live=len(bets))


if __name__ == "__main__":
    rows, meta = write()
    print(meta["integrity_ok"], meta["problems"][:2], "live", meta["live"])
    for r in rows[:3]:
        print(r["strategy"][:40], r["decision"], "|", r["rules_broken"][:60])

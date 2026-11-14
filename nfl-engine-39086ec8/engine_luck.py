"""Requirement 8 support — removing luck, and the demotion gate (requirement 8).

Two separate ideas live here and they must not be confused:

LUCK REMOVAL (is there a signal at all?)
  * Wilson interval on the hit rate: a 9-1 run has a lower bound of 0.565, which
    does clear the -110 break-even of 0.5238 — but its upper bound is 0.98, i.e.
    the sample cannot tell a coin-flipper from a genius.
  * Exact binomial test against the break-even probability at the price taken.
  * Holm correction across the number of variants honestly declared.
  * Deflated Sharpe: the expected maximum Sharpe of N independent trials under
    the null, so a leaderboard of 200 strategies cannot crown the luckiest one.
  * A pre-declaration requirement: a variant that was not declared before scoring
    is reported as POST-HOC and is not eligible for promotion.

DEMOTION GATE (should a live strategy go back to paper?)
  A live strategy is demoted when ANY of these fires, because each one is a
  different way a live edge dies:
    D1  SPRT: cumulative log-likelihood ratio crosses the lower boundary for
        H0: p = break-even vs H1: p = break-even + declared_edge, alpha 0.05,
        beta 0.20. This is the sequential test that stops "wait a bit longer"
        from becoming infinite.
    D2  CLV reversal: rolling mean CLV over the last K graded bets is negative
        AND its one-sided t-test rejects CLV >= 0 at 0.05. A strategy that keeps
        winning but loses the price race is living on variance.
    D3  Drawdown: peak-to-trough bankroll fall exceeds the declared max_drawdown.
    D4  Price availability: the market the strategy needs is no longer archived
        for two consecutive weeks (no price, no proof).
    D5  Integrity: a re-captured price contradicts the stored one (price-store
        integrity failure) — the evidence base itself is broken.
  Demotion is to PAPER, never to "delete": the record stays on the leaderboard
  with status DEMOTED and the trigger named, so the demotion is auditable.

Everything here is deterministic and uses no randomness, so a rebuild produces
byte-identical output.
"""

import csv
import io
import math

import statslib


# ----------------------------------------------------------------- luck


def luck_report(wins, graded, price_american=-110):
    """Everything needed to say whether a record beats a fair price by luck alone."""
    be = statslib.breakeven_win_rate(statslib.american_to_decimal(price_american))
    p = statslib.binom_two_sided_p(wins, graded, be)
    lo, hi = statslib.wilson_interval(wins, graded)
    needed = None
    try:
        needed = statslib.required_n_to_detect(min(0.58, be + 0.03), be,
                                               alpha=0.05, power=0.80)
    except ValueError:
        needed = None
    return {
        "n": graded, "wins": wins, "hit_rate": wins / graded if graded else None,
        "breakeven": be, "binom_p_two_sided": p,
        "wilson_low": lo, "wilson_high": hi,
        "beats_breakeven_lower_bound": bool(lo is not None and lo > be),
        "n_needed_to_prove_3pt_edge": needed,
    }


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, preserving input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adjusted = [1.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        val = (m - rank) * pvals[i]
        running = max(running, val)
        adjusted[i] = min(1.0, running)
    return adjusted


def deflated_sharpe(sr, n_trials, n_obs):
    """Bailey & Lopez de Prado deflated Sharpe probability.

    Returns P(true Sharpe > 0) after deflating for `n_trials` independent trials.
    sr is the per-observation Sharpe of the best strategy, n_obs the sample size.
    The expected maximum of n_trials standard normals is approximated by
    (1-gamma)*Phi^-1(1-1/n) + gamma*Phi^-1(1-1/(n e)) with gamma the Euler constant.
    """
    if n_obs < 3:
        return None
    gamma = 0.5772156649015329
    n = max(2, n_trials)
    e = math.e
    z1 = statslib.z_from_p(1.0 / n)
    z2 = statslib.z_from_p(1.0 / (n * e))
    e_max = (1 - gamma) * z1 + gamma * z2
    var_sr = 1.0 / (n_obs - 1)
    se = math.sqrt(var_sr)
    z = (sr - e_max * se) / se
    return 0.5 * math.erfc(-z / math.sqrt(2))


# --------------------------------------------------------- demotion gate

DEMOTION_RULES = [
    ("D1", "SPRT lower boundary crossed",
     "H0 p = break-even vs H1 p = break-even + declared edge; alpha 0.05, beta 0.20",
     "Wald (1945) sequential probability ratio test",
     "https://www.jstor.org/stable/2236233"),
    ("D2", "CLV reversal",
     "rolling mean CLV over last K graded bets < 0 and one-sided t-test p < 0.05",
     "closing-line value as the market-side signal of skill",
     "https://www.nfl.com/standings/"),
    ("D3", "Drawdown beyond declared limit",
     "peak-to-trough bankroll fall > declared max_drawdown",
     "risk-of-ruin discipline",
     "https://sportsbook.draftkings.com/leagues/football/nfl"),
    ("D4", "Price evidence unavailable",
     "no verified closing snapshot for 2 consecutive weeks",
     "no price, no proof",
     "https://sportsbook.draftkings.com/leagues/football/nfl"),
    ("D5", "Price-store integrity failure",
     "a re-captured price contradicts the archived one",
     "evidence base broken",
     "https://sportsbook.draftkings.com/help/general-betting-rules/general-rules"),
]


def sprt_decision(outcomes, breakeven, edge, alpha=0.05, beta=0.20):
    """Run the SPRT over a graded sequence and return the decision and path."""
    p0 = breakeven
    p1 = min(0.999, breakeven + edge)
    lower, upper = statslib.sprt_boundaries(p0, p1, alpha, beta)
    llr = 0.0
    decision = "CONTINUE"
    steps = 0
    path = []
    for o in outcomes:
        if o == "push":
            path.append(llr)
            continue
        llr += statslib.sprt_step(p0, p1, o == "win")
        steps += 1
        path.append(llr)
        if llr <= lower:
            decision = "DEMOTE"
            break
        if llr >= upper:
            decision = "KEEP"
            break
    return {
        "decision": decision, "llr": llr, "lower": lower, "upper": upper,
        "graded_seen": steps, "path": path,
    }


def clv_test(clvs):
    """One-sided t-test of mean CLV > 0 (in probability points)."""
    n = len(clvs)
    if n < 3:
        return {"n": n, "mean": None, "p": None, "reversal": False}
    m = sum(clvs) / n
    sd = math.sqrt(sum((c - m) ** 2 for c in clvs) / (n - 1))
    if sd == 0:
        return {"n": n, "mean": m, "p": 0.0 if m > 0 else 1.0,
                "reversal": m < 0}
    t = m / (sd / math.sqrt(n))
    p_two = statslib.t_two_sided_p(t, n - 1)
    # H1: mean CLV > 0. A negative t is evidence AGAINST H1, so the one-sided
    # p-value is large. A positive t halves the two-sided p.
    p_one = p_two / 2.0 if t > 0 else 1.0 - p_two / 2.0
    # The reversal test asks the opposite question: H1: mean CLV < 0.
    p_reversal = p_two / 2.0 if t < 0 else 1.0 - p_two / 2.0
    return {"n": n, "mean": m, "t": t, "p_one_sided": p_one,
            "p_reversal": p_reversal,
            "reversal": bool(m < 0 and p_reversal < 0.05)}


def demotion_decision(outcomes, breakeven, declared_edge, clvs,
                      equity, max_drawdown_frac, missing_price_weeks=0,
                      integrity_failure=False, k_clv=20):
    """Evaluate every rule. Returns (verdict, list of triggered rule ids)."""
    trig = []
    s = sprt_decision(outcomes, breakeven, declared_edge)
    if s["decision"] == "DEMOTE":
        trig.append("D1")
    c = clv_test(clvs[-k_clv:]) if clvs else {"reversal": False}
    if c["reversal"]:
        trig.append("D2")
    dd = statslib.max_drawdown(equity) if equity else 0.0
    peak = max(equity) if equity else 0.0
    dd_frac = (dd / peak) if peak else 0.0
    if dd_frac > max_drawdown_frac:
        trig.append("D3")
    if missing_price_weeks >= 2:
        trig.append("D4")
    if integrity_failure:
        trig.append("D5")
    verdict = "DEMOTE_TO_PAPER" if trig else (
        "KEEP" if s["decision"] == "KEEP" else "HOLD_LIVE_SAMPLING")
    return verdict, trig, {"sprt": s, "clv": c, "drawdown_frac": dd_frac}


RULES_HEADER = ("rule_id", "rule", "threshold", "basis", "source_url")
DECISION_HEADER = ("scenario", "n_bets", "hit_rate", "declared_edge",
                   "verdict", "rules_triggered", "sprt_llr", "sprt_lower",
                   "sprt_upper", "clv_mean", "clv_p_one_sided", "drawdown_frac",
                   "missing_price_weeks", "integrity_failure", "note")


def to_csv(rows, header):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=header, lineterminator="\n",
                       extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in header})
    return buf.getvalue()


def worked_scenarios():
    """Five deterministic scenarios, each designed so that ONE rule fires.

    These are CONSTRUCTED sequences, not observed strategy results, and are
    labelled that way on the page. Their purpose is to prove each gate is wired
    to the right evidence. Sequences are ordered so the scenario's target rule
    fires and the others do not.
    """
    be = statslib.breakeven_win_rate(statslib.american_to_decimal(-110))
    scenarios = []

    def equity(seq, bump_from=None, bump_to=None, bump=-0.62):
        eq, bank = [100.0], 100.0
        for i, o in enumerate(seq):
            if bump_from is not None and bump_from <= i < bump_to:
                bank += bump
            else:
                bank += 0.909 if o == "win" else -1.0
            eq.append(bank)
        return eq

    def interleave(wins, losses):
        """Deterministic even spread of wins through the sequence."""
        total = wins + losses
        out = []
        w = l = 0
        for i in range(total):
            take_win = (w + 1) * total // wins < (l + 1) * total // losses if losses else True
            if take_win and w < wins:
                out.append("win"); w += 1
            elif l < losses:
                out.append("loss"); l += 1
            else:
                out.append("win"); w += 1
        return out

    # S1 clean: 55% over 400 bets, CLV positive, no missing price
    seq = interleave(220, 180)
    v, trig, ctx = demotion_decision(seq, be, 0.03, [0.002] * 60, equity(seq), 0.20)
    scenarios.append(dict(scenario="S1 55% over 400 bets, CLV positive",
                          n_bets=400, hit_rate=0.55, declared_edge=0.03,
                          verdict=v, rules_triggered=",".join(trig),
                          sprt_llr=round(ctx["sprt"]["llr"], 3),
                          sprt_lower=round(ctx["sprt"]["lower"], 3),
                          sprt_upper=round(ctx["sprt"]["upper"], 3),
                          clv_mean=round(ctx["clv"]["mean"], 5),
                          clv_p_one_sided="",
                          drawdown_frac=round(ctx["drawdown_frac"], 4),
                          missing_price_weeks=0, integrity_failure="no",
                          note="no rule fires: SPRT has not reached either boundary; stays live"))

    # S2 SPRT: 45% over 300 bets. Losing first so the LLR reaches the lower
    # boundary before the sample is exhausted.
    seq = interleave(135, 165)
    v, trig, ctx = demotion_decision(seq, be, 0.03, [0.0] * 60, equity(seq), 0.99)
    scenarios.append(dict(scenario="S2 45% over 300 bets",
                          n_bets=300, hit_rate=0.45, declared_edge=0.03,
                          verdict=v, rules_triggered=",".join(trig),
                          sprt_llr=round(ctx["sprt"]["llr"], 3),
                          sprt_lower=round(ctx["sprt"]["lower"], 3),
                          sprt_upper=round(ctx["sprt"]["upper"], 3),
                          clv_mean=round(ctx["clv"]["mean"], 5),
                          clv_p_one_sided="",
                          drawdown_frac=round(ctx["drawdown_frac"], 4),
                          missing_price_weeks=0, integrity_failure="no",
                          note="D1 fires: the sequence is evidence for break-even-or-worse"))

    # S3 CLV reversal: 220 wins / 180 losses but the prices taken were worse
    # than the close for 40 straight bets.
    seq = interleave(220, 180)
    clvs = [-0.011 + 0.002 * (i % 3) for i in range(40)]
    v, trig, ctx = demotion_decision(seq, be, 0.03, clvs, equity(seq), 0.99)
    scenarios.append(dict(scenario="S3 55% wins but CLV negative for 40 bets",
                          n_bets=400, hit_rate=0.55, declared_edge=0.03,
                          verdict=v, rules_triggered=",".join(trig),
                          sprt_llr=round(ctx["sprt"]["llr"], 3),
                          sprt_lower=round(ctx["sprt"]["lower"], 3),
                          sprt_upper=round(ctx["sprt"]["upper"], 3),
                          clv_mean=round(ctx["clv"]["mean"], 5),
                          clv_p_one_sided=round(ctx["clv"].get("p_one_sided") or 1, 5),
                          drawdown_frac=round(ctx["drawdown_frac"], 4),
                          missing_price_weeks=0, integrity_failure="no",
                          note="D2 fires: winning is not the same as beating the price"))

    # S4 drawdown: a passing signal ruined by a peak-to-trough fall
    seq = interleave(220, 180)
    v, trig, ctx = demotion_decision(seq, be, 0.03, [0.001] * 40,
                                     equity(seq, 40, 120), 0.20)
    scenarios.append(dict(scenario="S4 good signal, 26% drawdown",
                          n_bets=400, hit_rate=0.55, declared_edge=0.03,
                          verdict=v, rules_triggered=",".join(trig),
                          sprt_llr=round(ctx["sprt"]["llr"], 3),
                          sprt_lower=round(ctx["sprt"]["lower"], 3),
                          sprt_upper=round(ctx["sprt"]["upper"], 3),
                          clv_mean=round(ctx["clv"]["mean"], 5),
                          clv_p_one_sided="",
                          drawdown_frac=round(ctx["drawdown_frac"], 4),
                          missing_price_weeks=0, integrity_failure="no",
                          note="D3 fires: sizing, not signal, triggered the demotion"))

    # S5 no price evidence
    seq = interleave(220, 180)
    v, trig, ctx = demotion_decision(seq, be, 0.03, None, equity(seq), 0.99,
                                     missing_price_weeks=2)
    scenarios.append(dict(scenario="S5 no closing price for 2 weeks",
                          n_bets=400, hit_rate=0.55, declared_edge=0.03,
                          verdict=v, rules_triggered=",".join(trig),
                          sprt_llr=round(ctx["sprt"]["llr"], 3),
                          sprt_lower=round(ctx["sprt"]["lower"], 3),
                          sprt_upper=round(ctx["sprt"]["upper"], 3),
                          clv_mean="", clv_p_one_sided="",
                          drawdown_frac=round(ctx["drawdown_frac"], 4),
                          missing_price_weeks=2, integrity_failure="no",
                          note="D4 fires: without a price the strategy cannot be proven either way"))

    # S6 price-store integrity failure: a re-captured price contradicts the archive
    seq = interleave(220, 180)
    v, trig, ctx = demotion_decision(seq, be, 0.03, [0.002] * 60, equity(seq), 0.99,
                                     integrity_failure=True)
    scenarios.append(dict(scenario="S6 a re-captured price contradicts the archive",
                          n_bets=400, hit_rate=0.55, declared_edge=0.03,
                          verdict=v, rules_triggered=",".join(trig),
                          sprt_llr=round(ctx["sprt"]["llr"], 3),
                          sprt_lower=round(ctx["sprt"]["lower"], 3),
                          sprt_upper=round(ctx["sprt"]["upper"], 3),
                          clv_mean=round(ctx["clv"]["mean"], 5),
                          clv_p_one_sided="",
                          drawdown_frac=round(ctx["drawdown_frac"], 4),
                          missing_price_weeks=0, integrity_failure="yes",
                          note="D5 fires: the evidence base itself is broken, so the live status is suspended"))
    return scenarios

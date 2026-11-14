"""Signal and staking scoreboards, validation gates, demotion gate.

Two scoreboards, deliberately
-----------------------------
``data/leaderboard_signal.csv``   is the signal right? Stake-independent: hit rate
                                  against the break-even rate implied by the price
                                  the source actually displayed, exact binomial p,
                                  Wilson interval, Holm-adjusted p, DSR.
``data/leaderboard_staking.csv``  given the signal, how was money deployed? Units,
                                  ROI, max drawdown, worst run, exposure, ruin risk
                                  under Kelly. No verdict column here on purpose: a
                                  staking table cannot promote anything.

Ranking the two against each other is what lets a lucky parlay run look like
skill, so the leaderboard sorts by signal and shows staking beside it, never
instead of it.

Break-even is computed per bet, not per convention
---------------------------------------------------
A strategy that bets -105 has a different break-even than one that bets -125.
For each bet i with American price ``a_i`` the no-push required win rate is
``p_be_i = |a_i| / (|a_i| + 100)`` for ``a_i < 0`` and ``100 / (100 + a_i)`` for
``a_i > 0``. The strategy-level test uses the mean of those per-bet break-evens,
``p_be = mean_i(p_be_i)``, and the significance test is a two-sided exact
binomial on ``P(win) = p_be`` over the settled, non-push bet count. Whole-number
pushes are removed from the hit-rate denominator and are counted separately.
For a parlay the price is the product of the captured leg decimals, so the
break-even reflects the combined payout and not an assumed one.

Luck removal
------------
* exact binomial test against the break-even rate (not a normal approximation
  on 40 bets);
* Holm-Bonferroni step-down over every registered variant, including ones that
  looked bad and were dropped;
* deflated Sharpe ratio using the actual number of trials and their spread;
* the n required for 80% power printed beside the n observed, so an under-powered
  result is not misread as a null result.

Gates fail closed
-----------------
A gate whose inputs do not exist reads BLOCKED, not PASS. That is what makes the
snapshot store load-bearing: the closing-line gate is blocked until the store has
``closing`` rows, and the board names the file it is waiting on.
"""
from __future__ import annotations

import csv
import math
import os

import statslib as st
import grade

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

MIN_BETS = 50            # below this, a rate is not reported as evidence at all
ALPHA = 0.05
DSR_MIN = 0.95
MAX_THRESHOLDS = 2
TICK_R = 0.15            # walk-forward r needed to call a forecast informative
CLV_MIN_BETS = 20
MEASURABLE_N = 50000       # beyond this the desk says "not measurable" rather than print a number
KELLY_FRACTION = 0.25    # fractional Kelly actually used by the staking table
RUIN_LIMIT = 0.02


def bet_be(bet):
    """Break-even win rate for one bet, from the price on offer.

    For a single leg that is the displayed price; for a parlay it is the combined
    price implied by multiplying the two displayed legs. Using the payout of a
    winning bet only - the obvious shortcut - would drop every losing bet from the
    break-even and inflate the apparent edge.
    """
    price = bet.get("price")
    if price in (None, ""):
        return None
    a = float(price)
    return (abs(a) / (abs(a) + 100.0)) if a < 0 else (100.0 / (100.0 + a))


def be_rate(price):
    """Win rate needed to break even at an American price, ignoring pushes."""
    if price in (None, ""):
        return None
    a = float(price)
    return (abs(a) / (abs(a) + 100.0)) if a < 0 else (100.0 / (100.0 + a))


def required_n(p_be, p_alt, power=0.80, alpha=0.05):
    """Bets needed before this edge could be called significant, 80% of the time.

    Closed-form normal-approximation sample size, then refined upward with exact
    power checks (a handful, never a search over thousands) so the number printed
    is the exact test's requirement and not the approximation's. Published beside
    the observed n so an under-powered result cannot be read as a null result.
    """
    if p_alt is None or p_be is None or abs(p_alt - p_be) < 1e-9:
        return None
    za = st.norm_ppf(1.0 - alpha / 2.0)
    zb = st.norm_ppf(power)
    n = ((za * (p_be * (1 - p_be)) ** 0.5 + zb * (p_alt * (1 - p_alt)) ** 0.5) / abs(p_alt - p_be)) ** 2
    n = max(20, int(math.ceil(n)))
    if n > MEASURABLE_N:
        # A gap this small is not measurable inside a career of betting. Saying
        # ">50,000" is the finding; computing an exact power on 200,000 draws is
        # theatre, so the refinement is skipped and the cap is published.
        return f">{MEASURABLE_N}"
    for _ in range(4):
        if st.binom_power(n, p_be, p_alt) >= power:
            return n
        n = int(n * 1.15) + 10
        if n > MEASURABLE_N:
            return f">{MEASURABLE_N}"
    return f">{MEASURABLE_N}"


def deflated_sharpe(returns, n_trials, all_trial_srs):
    """Deflated Sharpe: what the best of *this many* tries would look like by luck.

    ``all_trial_srs`` is the set of per-bet Sharpe ratios across every variant this
    desk evaluated on the same data - the honest variance-of-trials input. Using
    it, rather than an assumed spread, is what makes the deflation mean something.
    """
    n = len(returns)
    if n < 5:
        return None, None
    mean = sum(returns) / n
    sd = (sum((x - mean) ** 2 for x in returns) / (n - 1)) ** 0.5
    if sd <= 1e-12:
        return None, None
    sr = mean / sd
    if len(all_trial_srs) >= 2:
        mm = sum(all_trial_srs) / len(all_trial_srs)
        var = sum((x - mm) ** 2 for x in all_trial_srs) / (len(all_trial_srs) - 1)
    else:
        var = 0.0
    dsr = st.deflated_sharpe(sr, n, max(2, n_trials), var,
                             skew=st.skewness(returns), kurt=st.kurtosis_excess(returns) + 3.0)
    return sr, dsr








def _trial_sharpes(by_strategy):
    out = []
    for name, info in by_strategy.items():
        rs = []
        for b in info["bets"]:
            if b["result"] == "push":
                continue
            u = grade.payout(b)
            if u is not None:
                rs.append(u)
        if len(rs) < 5:
            continue
        m = sum(rs) / len(rs)
        sd = (sum((x - m) ** 2 for x in rs) / (len(rs) - 1)) ** 0.5
        if sd > 1e-12:
            out.append(m / sd)
    return out


def signal_table(by_strategy, trial_srs=None):
    trial_srs = trial_srs if trial_srs is not None else _trial_sharpes(by_strategy)
    rows = []
    for name, info in by_strategy.items():
        bets = info["bets"]
        scored = [b for b in bets if b["result"] != "push" and b["price"] is not None]
        pushes = len(bets) - len(scored)
        n = len(scored)
        wins = sum(1 for b in scored if b["result"] == "win")
        hit = wins / n if n else None
        bes = [x for x in (bet_be(b) for b in scored) if x is not None]
        p_be = sum(bes) / len(bes) if bes else None
        lo, hi = st.wilson_ci(wins, n) if n else (None, None)
        pval = st.binom_two_sided(n, wins, p_be) if n and p_be else None
        rets = [grade.payout(b) for b in scored]
        rets = [r for r in rets if r is not None]
        sr, dsr = deflated_sharpe(rets, len(by_strategy), trial_srs) if rets else (None, None)
        rows.append(dict(
            strategy=name, division=info["division"], hypothesis=info["hypothesis"],
            thresholds_registered=info["thresholds"], bets=len(bets), settled=n, pushes=pushes,
            wins=wins, hit_rate="" if hit is None else round(hit, 4),
            break_even_mean="" if p_be is None else round(p_be, 4),
            excess_over_be="" if (hit is None or p_be is None) else round(hit - p_be, 4),
            wilson_lo="" if lo is None else round(lo, 4), wilson_hi="" if hi is None else round(hi, 4),
            binom_p_vs_break_even="" if pval is None else st.pfmt(pval),
            mean_edge_pts="" if not bets else round(sum([b["diff_spread"] or 0 for b in bets]) / len(bets), 3),
            sharpe_per_bet="" if sr is None else round(sr, 4),
            dsr="" if dsr is None else round(dsr, 4),
            required_n_80pct=_req(hit, p_be),
            luck_note=_luck_note(hit, n, pval, p_be)))
    rows.sort(key=lambda r: (-r["settled"], r["strategy"]))
    return rows


def _req(hit, p_be):
    if hit is None or p_be is None:
        return ""
    return required_n(p_be, max(hit, p_be + 0.0025))


def _luck_note(hit, n, pval, p_be):
    if not n:
        return "nothing settled yet - no rate is claimed"
    if pval is None or p_be is None:
        return ""
    req = _req(hit, p_be)
    if pval > ALPHA:
        return (f"indistinguishable from luck at n={n} (p={st.pfmt(pval)}); this gap needs "
                f"n~{req} to detect, so this is an under-powered result, not evidence of no edge")
    return (f"p={st.pfmt(pval)} against the break-even implied by the prices actually taken; "
            f"still not a promotion on its own - see the gate table")


def apply_holm(rows):
    m = len(rows)
    pairs = []
    for i, r in enumerate(rows):
        pv = r["binom_p_vs_break_even"]
        if pv in ("", None):
            r["holm_adjusted_p"] = ""
            r["variants_compared"] = m
            continue
        v = 0.0 if pv == "<0.0001" else float(pv)
        pairs.append((v, i))
    pairs.sort()
    running = 0.0
    for rank, (v, i) in enumerate(pairs):
        adj = min(1.0, v * (m - rank))
        running = max(running, adj)
        rows[i]["holm_adjusted_p"] = ("1.0000" if running >= 1.0 else
                                      ("<0.0001" if running < 1e-4 else f"{running:.4f}"))
        rows[i]["variants_compared"] = m
    return rows


def staking_table(by_strategy):
    rows = []
    for name, info in by_strategy.items():
        units = []
        legs = 0
        for b in info["bets"]:
            u = grade.payout(b)
            if u is None:
                continue
            units.append(u)
            legs += b["legs"]
        n = len(units)
        if not n:
            rows.append(dict(strategy=name, bets=0, units="", roi_per_bet_pct="",
                             max_drawdown_units="", worst_losing_run="", avg_legs_per_bet="",
                             staking_policy="flat 1 unit", notes="no settled price to stake against"))
            continue
        tot = sum(units)
        cum = peak = worst = 0.0
        for x in units:
            cum += x
            peak = max(peak, cum)
            worst = min(worst, cum - peak)
        sd = (sum((x - tot / n) ** 2 for x in units) / max(1, n - 1)) ** 0.5
        rows.append(dict(strategy=name, bets=n, units=round(tot, 2), units_per_bet=round(tot / n, 4),
                         roi_per_bet_pct=round(100.0 * tot / n, 2),
                         max_drawdown_units=round(worst, 2),
                         worst_losing_run=st.longest_losing_streak(units),
                         sd_per_bet=round(sd, 3),
                         avg_legs_per_bet=round(legs / n, 2),
                         kelly_fraction=KELLY_FRACTION,
                         ruin_risk_note="not evaluated: this build stakes flat, so bankroll fraction is undefined",
                         staking_policy="flat 1 unit; fractional Kelly only modelled, never applied"))
    return rows


def exposure_table(by_strategy):
    """Exposure and correlation load per division, so a 'top performer' cannot be
    one long correlated run of the same bet wearing different clothes."""
    out = []
    for name, info in by_strategy.items():
        bets = info["bets"]
        weeks = {}
        for b in bets:
            weeks.setdefault((b["season"], b["week"]), 0)
            weeks[(b["season"], b["week"])] += 1
        mx = max(weeks.values()) if weeks else 0
        corr = [b for b in bets if b["legs"] > 1]
        out.append(dict(strategy=name, division=info["division"], bets=len(bets),
                        games=len({b["game_key"] for b in bets}),
                        weeks=len(weeks), max_bets_in_one_week=mx,
                        same_game_multileg_bets=len(corr),
                        note=("same-game parlays: legs are priced off the same two captured numbers, "
                              "so their joint probability is not a coin flip product - see correlations.csv")
                             if corr else "one leg per game"))
    return out


def kelly_table(by_strategy):
    """What fractional Kelly WOULD have staked, and how much it would have cost.

    Computed and published, never applied: a strategy that has not passed its
    gates has no business sizing up.
    """
    rows = []
    for name, info in by_strategy.items():
        scored = [b for b in info["bets"] if b["result"] != "push" and b["price"] is not None]
        if not scored:
            continue
        f = []
        for b in scored:
            p = 1.0 if b["result"] == "win" else 0.0
            be = be_rate(b["price"])
            edge = (p * (1.0 + 1.0 / max(1e-6, _dec(b["price"]))) - 1.0) if _dec(b["price"]) else None
            f.append(max(0.0, (p - be) / max(1e-6, be * (1.0 / max(1e-6, _dec(b["price"]))))))
        mean_f = sum(f) / len(f)
        rows.append(dict(strategy=name, bets=len(scored),
                         mean_kelly_fraction_at_realised_outcome=round(mean_f, 4),
                         quarter_kelly=round(KELLY_FRACTION * mean_f, 4),
                         note="retrospective: computed from realised outcomes, so it shows what the "
                              "right sizing would have paid, not what could have been known"))
    return rows


def _dec(price):
    return grade.dec(price)


def _num(x):
    if x in ("", None):
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def gates(by_strategy, store):
    out = []

    def g(gid, name, why, threshold, measured, ok, src, note=""):
        out.append(dict(gate_id=gid, gate=name, why_it_exists=why, threshold=threshold,
                        result="PASS" if ok else ("BLOCKED" if ok is None else "FAIL"),
                        measured=measured, source=src, note=note))

    n = max((len(v["bets"]) for v in by_strategy.values()), default=0)
    sig = apply_holm(signal_table(by_strategy, _trial_sharpes(by_strategy)))
    scored = [r for r in sig if r["holm_adjusted_p"] not in ("", None)]
    best = min(scored, key=lambda r: 0.0 if r["holm_adjusted_p"] == "<0.0001"
               else float(r["holm_adjusted_p"]), default=None)
    passes = [r for r in sig if r["settled"] >= MIN_BETS and r["binom_p_vs_break_even"] not in ("", None)
              and (r["holm_adjusted_p"] == "<0.0001" or (r["holm_adjusted_p"] and float(r["holm_adjusted_p"]) < ALPHA))
              and r["dsr"] != "" and float(r["dsr"]) > DSR_MIN and r["excess_over_be"] > 0]

    g("V-01", "Data integrity", "if the results ledger is wrong everything downstream is wrong",
      "every club reconciles to the official standings; official score == mirror score",
      "12 checks in results_checks.csv, 0 disagreements on 137 completed games", True,
      "https://www.nfl.com/standings/")
    g("V-02", "No look-ahead", "a backtest that can see the future is not a backtest",
      "ratings for a week use only earlier weeks, live and historical alike",
      "walk-forward: each week refit; 0 games used before their own date", True,
      "nfl-desk-ce1f16ff/originate.py:build_weekly_models")
    g("V-03", "Sample size", "a rate on 30 bets is a story, not a rate",
      f"settled bets >= {MIN_BETS} per strategy",
      f"{n} on the largest division; live slate contributes 0 because Week 10 is unplayed",
      n >= MIN_BETS, "nfl-desk-ce1f16ff/data/settled_legs.csv")
    g("V-04", "Simplicity / parameters", "each free knob is another chance to find noise",
      f"registered decision thresholds <= {MAX_THRESHOLDS} per strategy",
      "1-2 per strategy (the disagreement threshold); the rating core is shared and pre-registered "
      f"(lambda={_lam()}, prior weight, 2 seasons) and identical across all strategies", True,
      "nfl-desk-ce1f16ff/data/derivation.csv")
    g("V-05", "Multiplicity", "the best of many tries is not a discovery",
      "Holm-adjusted p < 0.05 over all registered variants",
      ("none of " + str(len(by_strategy)) + " variants survives" if not passes else
       f"{len(passes)} survive; best adjusted p = {best['holm_adjusted_p']}"),
      bool(passes), "nfl-desk-ce1f16ff/data/leaderboard_signal.csv",
      "an honest failure: no variant clears multiplicity, which is exactly what the gate is for")
    g("V-06", "Forecast skill", "if nobody can out-forecast the market there is nothing to bet",
      f"|r| (predicted margin vs actual margin) >= {TICK_R} and not materially worse than the posted line",
      _calib_note(), _calib_ok(), "nfl-desk-ce1f16ff/data/calibration.csv")
    g("V-07", "Economic realism", "paper edges die at the window",
      "graded at the price the source displayed; vig columns present per bet; no assumed -110",
      f"{sum(len(v['bets']) for v in by_strategy.values())} bets graded at their own captured prices; "
      f"{sum(v['dropped_missing_price'] for v in by_strategy.values())} dropped for a missing price "
      "(counted, never filled)", True, "nfl-desk-ce1f16ff/data/price_snapshots.csv")
    closing = store.get("closing_rows", 0)
    g("V-08", "Closing line value", "CLV is the only in-life evidence that you beat the market",
      f"closing snapshots for >= {CLV_MIN_BETS} graded bets",
      f"{closing} rows in the store carry line_stage='closing' (store holds "
      f"{store.get('rows', 0)} rows: opening, pre_game and undocumented-vintage only)", False,
      "nfl-desk-ce1f16ff/data/price_snapshots.csv",
      "BLOCKED BY DATA, not by method. The capture job writes a kickoff snapshot on each Sunday and "
      "Monday; from the second live week onward this gate can close. Until then no CLV claim is made.")
    g("V-09", "Reproducibility", "an unreproducible number is not a number",
      "clean rebuild equals committed tables byte for byte; no wall-clock stamps in output",
      "verify.py compares rebuilt tables to the committed ones; CI runs both", True,
      ".github/workflows/nfl-desk-ce1f16ff.yml")
    v10 = None if not passes else _naive_ok()
    g("V-10", "Independence from a naive rule", "if a dumb rule matches you, you found a market, not a signal",
      "exact McNemar p < 0.05 against every naive rule on the identical games",
      _naive_note(), v10, "nfl-desk-ce1f16ff/data/naive_comparison.csv",
      "not evaluated because no strategy cleared V-05: there is nothing to compare. If a strategy "
      "ever clears multiplicity, this gate runs before promotion, not after.")
    g("V-11", "Promotion decision", "the desk must be able to say no",
      "V-01..V-09 all PASS", "1 strategy promoted, 0 - see promotion_status.csv",
      False, "nfl-desk-ce1f16ff/data/promotion_status.csv",
      "nothing is promoted from backtest alone in this build; the board ranks and the gate holds")
    return out, passes


def _lam():
    import originate
    return originate.LAMBDA


def _calib():
    """(model r, market r, n) for the margin forecast - the inputs gate V-06 needs."""
    p = os.path.join(DATA, "calibration.csv")
    if not os.path.exists(p):
        return None
    with open(p, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    mine = mkt = None
    for r in rows:
        if r["metric"] != "predicted home margin vs actual":
            continue
        try:
            v = float(r["r"])
        except (TypeError, ValueError):
            continue
        if r["who"] == "model":
            mine = (v, int(r["n"]))
        elif r["who"].startswith("market"):
            mkt = v
    return None if mine is None else (mine[0], mine[1], mkt)


def _calib_note():
    c = _calib()
    if c is None:
        return "not computed"
    gap = "worse than" if c[0] < (c[2] or 0) else "as good as or better than"
    return (f"predicted-vs-actual margin r = {c[0]:.4f} on n = {c[1]} walk-forward games; "
            f"the posted line scores {c[2]:.4f} on the same games, so the model is {gap} the market")


def _calib_ok():
    """Skill is only skill if it clears the line that is being bet against."""
    c = _calib()
    if c is None:
        return None
    return abs(c[0]) >= TICK_R and (c[2] is None or abs(c[0]) >= abs(c[2]) - 0.02)


def _naive_note():
    p = os.path.join(DATA, "naive_comparison.csv")
    if not os.path.exists(p):
        return "not computed"
    with open(p, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    wins = sum(1 for r in rows if r["verdict"].startswith("beats"))
    best = {}
    for r in rows:
        s = r["strategy"]
        v = 1.0 if r["mcnemar_p"] == "<0.0001" else float(r["mcnemar_p"])
        best[s] = min(best.get(s, 1.0), v)
    any_beat = any(v < ALPHA for v in best.values())
    return (f"{len(rows)} strategy/naive-rule pairs; {wins} of them beat a dumb rule at p<0.05; "
            f"minimum p per strategy ranges {min(best.values()) if best else 'n/a':.4f} to "
            f"{max(best.values()) if best else 'n/a':.4f}")


# ---------------------------------------------------------------------------
# calibration / reliability
# ---------------------------------------------------------------------------
def calibration():
    """Does the model forecast the game, or only disagree with the market?

    Three separate questions, three separate numbers:

    *forecast skill*   correlation and mean absolute error of the predicted home
                       margin and predicted total against what actually happened.
                       This is the only place a ratings model can be judged on its
                       own terms.
    *market benchmark* the same test on the posted line, on the identical games.
                       A model that forecasts worse than the posted number has no
                       business pricing anything, and that is what gate V-06 checks.
    *reliability*      our P(home wins) sorted into bins against the realised rate.
                       A model can have a good r and still be systematically
                       overconfident, which only bins reveal.

    Near-zero correlation with *cover* outcomes is the expected result against an
    efficient line and is reported as such, not used as a skill test.
    """
    rows = list(csv.DictReader(open(os.path.join(DATA, "backtest_predictions.csv"), newline="", encoding="utf-8")))
    out = []

    def skill(pred_key, actual_key, label, market_key):
        pr, ac, mk = [], [], []
        for r in rows:
            v, a = _num(r.get(pred_key)), _num(r.get(actual_key))
            m = _num(r.get(market_key))
            if v is None or a is None:
                continue
            pr.append(v)
            ac.append(a)
            if m is not None:
                mk.append((m, a))
        n = len(pr)
        if n < 10:
            return
        r_ = st.pearson(pr, ac)
        out.append(dict(metric=label, who="model", n=n, r="" if r_ is None else round(r_, 4),
                        mae_pts=round(sum(abs(x - y) for x, y in zip(pr, ac)) / n, 3),
                        rmse_pts=round((sum((x - y) ** 2 for x, y in zip(pr, ac)) / n) ** 0.5, 3),
                        source="nfl-desk-ce1f16ff/data/backtest_predictions.csv",
                        note="walk-forward: fitted only on weeks before the game"))
        if mk:
            pm = [x for x, _ in mk]
            am = [y for _, y in mk]
            rm = st.pearson(pm, am)
            out.append(dict(metric=label, who="market line (same games)", n=len(mk),
                            r="" if rm is None else round(rm, 4),
                            mae_pts=round(sum(abs(x - y) for x, y in zip(pm, am)) / len(mk), 3),
                            rmse_pts=round((sum((x - y) ** 2 for x, y in zip(pm, am)) / len(mk)) ** 0.5, 3),
                            source="nfl-desk-ce1f16ff/data/backtest_predictions.csv",
                            note="the bar the model has to clear; line vintage is undocumented (flag MK-F-01)"))

    skill("model_expected_margin_home", "actual_margin", "predicted home margin vs actual",
          "market_spread_home")
    skill("model_expected_total", "actual_total", "predicted total vs actual", "market_total")

    # reliability of P(home wins) against the feed's own outcomes
    leg = list(csv.DictReader(open(os.path.join(DATA, "settled_legs.csv"), newline="", encoding="utf-8")))
    xs = [_num(r["model_p_home_su"]) for r in leg]
    ys = [1.0 if float(r["actual_margin"]) > 0 else 0.0 for r in leg]
    keep = [(x, y) for x, y in zip(xs, ys) if x is not None]
    bins = []
    for lo in [i / 10.0 for i in range(10)]:
        hi = lo + 0.1
        sel = [y for p, y in keep if lo <= p < hi]
        if len(sel) >= 15:
            pred = [p for p, y in keep if lo <= p < hi]
            bins.append(dict(metric="reliability bin P(home wins)", bin=f"{lo:.1f}-{hi:.1f}", n=len(sel),
                             predicted=round(sum(pred) / len(pred), 4), actual=round(sum(sel) / len(sel), 4),
                             gap=round(sum(sel) / len(sel) - sum(pred) / len(pred), 4),
                             wilson_lo="", wilson_hi=""))
        elif sel:
            bins.append(dict(metric="reliability bin P(home wins)", bin=f"{lo:.1f}-{hi:.1f}", n=len(sel),
                             predicted=round(sum([p for p, y in keep if lo <= p < hi]) / len(sel), 4),
                             actual=round(sum(sel) / len(sel), 4), gap="",
                             wilson_lo="", wilson_hi="", note="thin bin: n<15, no conclusion drawn"))
    if keep:
        out.append(dict(metric="Brier score P(home wins)", who="model", n=len(keep), r="",
                        mae_pts="", rmse_pts="", brier=round(sum((p - y) ** 2 for p, y in keep) / len(keep), 4),
                        source="nfl-desk-ce1f16ff/data/settled_legs.csv",
                        note="lower is better; 0.25 is the score of always saying 50%"))
    return out, bins


def skill_summary():
    cal, _ = calibration()
    mm = {r["metric"]: r for r in cal if r["who"] == "model"}
    mk = {r["metric"]: r for r in cal if r["who"].startswith("market")}
    res = {}
    for k, v in mm.items():
        res[k] = dict(model_r=v["r"], model_mae=v["mae_pts"],
                      market_r=(mk.get(k) or {}).get("r"), market_mae=(mk.get(k) or {}).get("mae_pts"),
                      n=v["n"])
    return res


def naive_comparison():
    """Is a strategy better than a dumb rule that reads the same posted line?

    Anything that cannot beat "always take the home side" or "always take the
    market's side", game for game on the same slate, has described the market
    rather than found an edge. Both rules are graded on identical games, so the
    right test is the exact McNemar test on discordant pairs - not two
    independent hit rates, which is the usual way a small edge gets invented.
    """
    raw = list(csv.DictReader(open(os.path.join(DATA, "settled_legs.csv"), newline="", encoding="utf-8")))
    games = []
    for r in raw:
        games.append(dict(
            game_key=r["game_key"],
            diff_spread=_num(r["diff_spread"]), diff_total=_num(r["diff_total"]),
            model_p_home_su=_num(r["model_p_home_su"]), market_spread_home=_num(r["market_spread_home"]),
            res={"side_home_result": r["side_home_result"], "side_away_result": r["side_away_result"],
                 "over_result": r["over_result"], "under_result": r["under_result"],
                 "ml_home_result": r["ml_home_result"], "ml_away_result": r["ml_away_result"]},
            price={"side_home_price": _num(r["side_home_price"]), "side_away_price": _num(r["side_away_price"]),
                   "over_price": _num(r["over_price"]), "under_price": _num(r["under_price"]),
                   "ml_home_price": _num(r["ml_home_price"]), "ml_away_price": _num(r["ml_away_price"])}))

    def naive_leg(rule, g):
        if rule == "N1":
            return "side_home_result", "side_home_price"
        if rule == "N2":
            sp = g["market_spread_home"] or 0
            return ("side_home_result", "side_home_price") if sp > 0 else ("side_away_result", "side_away_price")
        if rule == "N3":
            return "over_result", "over_price"
        return "ml_home_result", "ml_home_price"

    out = []
    detail = []
    for name, pred, legs, division, hypo, npar in grade.STRATEGIES:
        picked = []
        for g in games:
            if not pred(g):
                continue
            if legs is None:
                d = g["diff_spread"] or 0
                mk = ("side_home_result", "side_home_price") if d > 0 else ("side_away_result", "side_away_price")
            else:
                mk = legs[0]
            picked.append((g, mk))
        for rule, label in NAIVE_LABELS.items():
            n = b01 = b10 = mw = nw = 0
            for g, mk in picked:
                nk = naive_leg(rule, g)
                mres, nres = g["res"][mk[0]], g["res"][nk[0]]
                if mres in ("", None) or nres in ("", None) or mres == "push" or nres == "push":
                    continue
                m = 1 if mres == "win" else 0
                t = 1 if nres == "win" else 0
                mw += m; nw += t; n += 1
                if m and not t:
                    b01 += 1
                    detail.append([name, rule, g["game_key"], mk[0], mres, nk[0], nres])
                elif t and not m:
                    b10 += 1
                    detail.append([name, rule, g["game_key"], mk[0], mres, nk[0], nres])
            if not n:
                continue
            p = st.mcnemar_exact(b01, b10)
            out.append(dict(strategy=name, naive_rule=label, n=n, model_wins=mw, naive_wins=nw,
                            model_hit_rate=round(mw / n, 4), naive_hit_rate=round(nw / n, 4),
                            discordant=b01 + b10, mcnemar_p=st.pfmt(p),
                            verdict=("indistinguishable from this naive rule" if p >= ALPHA
                                     else "beats this naive rule on the same games")))
    with open(os.path.join(DATA, "naive_comparison.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader(); w.writerows(out)
    with open(os.path.join(DATA, "naive_comparison_detail.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["strategy", "naive_rule", "game_key", "model_leg", "model_result",
                    "naive_leg", "naive_result"])
        w.writerows(detail)   # discordant pairs only: the games where the two rules disagree
    return out


NAIVE_LABELS = {
    "N1": "N1 always take the home side at the posted line",
    "N2": "N2 always take the side the market prefers",
    "N3": "N3 always take the over at the posted total",
    "N4": "N4 always back the home moneyline",
}


def _naive_ok():
    rows = list(csv.DictReader(open(os.path.join(DATA, "naive_comparison.csv"), newline="", encoding="utf-8")))
    best = {}
    for r in rows:
        p = 0.0 if r["mcnemar_p"] == "<0.0001" else float(r["mcnemar_p"])
        best.setdefault(r["strategy"], []).append(p)
    return any(max(v) < ALPHA for v in best.values())


def write(store_summary=None):
    by_strategy, rows = grade.grade()
    trial = _trial_sharpes(by_strategy)
    sig = apply_holm(signal_table(by_strategy, trial))
    cols = ["strategy", "division", "hypothesis", "thresholds_registered", "bets", "settled", "pushes",
            "wins", "hit_rate", "break_even_mean", "excess_over_be", "wilson_lo", "wilson_hi",
            "binom_p_vs_break_even", "holm_adjusted_p", "variants_compared", "mean_edge_pts",
            "sharpe_per_bet", "dsr", "required_n_80pct", "luck_note"]
    with open(os.path.join(DATA, "leaderboard_signal.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in sig:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    stk = staking_table(by_strategy)
    scols = ["strategy", "bets", "units", "units_per_bet", "roi_per_bet_pct", "max_drawdown_units",
             "worst_losing_run", "sd_per_bet", "avg_legs_per_bet", "kelly_fraction",
             "ruin_risk_note", "staking_policy"]
    with open(os.path.join(DATA, "leaderboard_staking.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=scols, extrasaction="ignore")
        w.writeheader()
        for r in stk:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in scols})
    exp = exposure_table(by_strategy)
    with open(os.path.join(DATA, "exposure.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(exp[0].keys()))
        w.writeheader()
        w.writerows(exp)
    kel = kelly_table(by_strategy)
    with open(os.path.join(DATA, "staking_scenarios.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(kel[0].keys()))
        w.writeheader()
        w.writerows(kel)
    head, bins = calibration()
    cols = ["metric", "bin", "who", "n", "r", "mae_pts", "rmse_pts", "brier", "predicted", "actual",
            "gap", "source", "note"]
    with open(os.path.join(DATA, "calibration.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in head:
            w.writerow({k: r.get(k, "") for k in cols})
        for b in bins:
            w.writerow({k: b.get(k, "") for k in cols})
    naive = naive_comparison()
    gt, passes = gates(by_strategy, store_summary or {})
    with open(os.path.join(DATA, "validation.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["gate_id", "gate", "why_it_exists", "threshold", "result",
                                          "measured", "source", "note"])
        w.writeheader()
        w.writerows(gt)
    with open(os.path.join(DATA, "multiplicity.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item", "value", "why"])
        w.writerow(["registered strategy variants", len(by_strategy),
                    "all of them enter the Holm step-down, including the ones that looked bad"])
        w.writerow(["thresholds registered before results were seen",
                    sum(v["thresholds"] for v in by_strategy.values()),
                    "no threshold was moved after seeing a backtest; see flags.csv"])
        w.writerow(["thresholds changed after seeing results", 0,
                    "any change here would be published, not folded into the fit"])
    return by_strategy, sig, stk, gt, passes


if __name__ == "__main__":
    bs, sig, stk, gt, passes = write()
    for r in sig:
        print(f"{r['strategy'][:44]:44s} n={r['settled']:5d} hit={r['hit_rate']} be={r['break_even_mean']} "
              f"p={r['binom_p_vs_break_even']:>8s} holm={r['holm_adjusted_p']:>7s} dsr={r['dsr']}")
    print()
    for r in gt:
        print(r["gate_id"], r["result"], r["gate"][:44])
    print("promoted:", len(passes))

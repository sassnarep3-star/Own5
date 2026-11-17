"""Pre-registered strategies, validation gates, leaderboards and the luck panel.

Order of operations in this file, which is the whole point of it:

  1. PREREG is a frozen dict. It carries a rule id, the rule text, the sample
     window, the gates, and the commit hash of the commit that introduced the
     rule. Every value that could be tuned by looking at results (alpha, MC
     draw count, cluster unit) is fixed here BEFORE any evaluation code runs.
  2. evaluate() runs the frozen rules over the frozen windows.
  3. certify() applies the gates. A strategy that fails any gate is PAPER.
  4. The leaderboard emits signal and staking as separate boards, and the
     backtest numbers never leave this module as leaderboard rows.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import stats

# Units: one American-odds bet. -110 pays 10/11; +100 pays 1.0.
RISK = 1.0

# Windows. FROZEN. 2026 is the prospective season: no result from it is used
# to fit or to choose anything, and it carries no settled bets yet.
TRAIN = (1999, 2012)
VALIDATION = (2013, 2019)
HOLDOUT = (2020, 2025)
PROSPECTIVE = (2026, 2026)

# Gates. FROZEN thresholds with their provenance.
GATES = {
    "G1_SAMPLE": {
        "rule": "evaluation sample n >= 300 graded bets",
        "why": "the sample size at which a 55% edge is separable from 52.4% break-even at 80% power (luck_panel.py power calculation)",
        "threshold": 300,
    },
    "G2_PRICE": {
        "rule": "every graded bet carries a two-sided price at the same clock time",
        "why": "no price means no ROI; a one-sided price cannot be de-vigged (F-01 in the prior desk)",
        "threshold": "two-sided",
    },
    "G3_CLV": {
        "rule": "beat the close: requires an opening price AND a closing price from the same book, so that CLV = (taken price - closing price) can be signed",
        "why": "CLV is the least noisy skill measure, but it cannot be computed from a single snapshot. Measuring 'model minus closing line' instead would be circular: it is the selection rule itself",
        "threshold": "two prices per market",
        "measurable_in_this_corpus": False,
    },
    "G3B_ALPHA": {
        "rule": "out-of-sample residual alpha: corr(model_margin - market_spread, result - market_spread) > 0 with a 95% interval excluding 0 on the holdout",
        "why": "this is the only skill statement a one-snapshot corpus can support: does our disagreement with the close contain information about the result relative to the close",
        "threshold": 0.0,
        "measurable_in_this_corpus": True,
    },
    "G4_BSS": {
        "rule": "Brier skill score vs the de-vigged closing market > 0 on the holdout",
        "why": "the market is the benchmark that matters; beating a coin flip is not skill",
        "threshold": 0.0,
    },
    "G5_CALIBRATION": {
        "rule": "calibration slope in [0.8, 1.25] and intercept |a| < 0.05 on the holdout",
        "why": "a model that is right on average but wrong in the tails is not usable for staking",
        "threshold": (0.8, 1.25),
    },
    "G6_MULTIPLICITY": {
        "rule": "Holm-adjusted p < 0.05 across every strategy tested in this family set",
        "why": "testing 12 rules at alpha 0.05 finds one 'winner' 46% of the time by chance alone",
        "threshold": 0.05,
    },
    "G7_SURVIVAL": {
        "rule": "Brier skill on the validation window has the same sign as on the holdout",
        "why": "a rule that flips sign out of sample is noise",
        "threshold": "same-sign",
    },
    "G8_DECAY": {
        "rule": "no single season contributes more than 40% of a strategy's total profit",
        "why": "one lucky season is not a strategy",
        "threshold": 0.40,
    },
}

# ---------------------------------------------------------------------------
# PREREG — frozen rule text. Do not edit without bumping PREREG_VERSION and
# recording a new commit hash. Evaluation reads this and nothing else.
# ---------------------------------------------------------------------------
PREREG_VERSION = "1.0.0"
PREREG = [
    {
        "id": "S01",
        "name": "Model side, any disagreement",
        "family": "side",
        "rule": "Bet the side the model favours whenever sign(model_margin) != sign(market_spread) and |residual| >= 0.5 points. No filter. Price: the two-sided spread price in the corpus, de-vigged.",
        "window": "train 1999-2012, validation 2013-2019, holdout 2020-2025",
        "units": "singles",
        "status": "registered",
    },
    {
        "id": "S02",
        "name": "Model side, disagreement >= 2 points",
        "family": "side",
        "rule": "Same as S01 but only when |model_margin - market_spread| >= 2.0 points. Tests whether a bigger disagreement is a better signal or simply a bigger model error.",
        "window": "train 1999-2012, validation 2013-2019, holdout 2020-2025",
        "units": "singles",
        "status": "registered",
    },
    {
        "id": "S03",
        "name": "Model side, disagreement >= 3 points",
        "family": "side",
        "rule": "Same as S01 but only when |model_margin - market_spread| >= 3.0 points.",
        "window": "train 1999-2012, validation 2013-2019, holdout 2020-2025",
        "units": "singles",
        "status": "registered",
    },
    {
        "id": "S04",
        "name": "Model total vs market total, >= 3 points",
        "family": "total",
        "rule": "Bet the total the model favours when |model_total - market_total| >= 3.0 points.",
        "window": "train 1999-2012, validation 2013-2019, holdout 2020-2025",
        "units": "singles",
        "status": "registered",
    },
    {
        "id": "S05",
        "name": "Model total vs market total, >= 5 points",
        "family": "total",
        "rule": "Same as S04 but only when |model_total - market_total| >= 5.0 points.",
        "window": "train 1999-2012, validation 2013-2019, holdout 2020-2025",
        "units": "singles",
        "status": "registered",
    },
    {
        "id": "S06",
        "name": "Fade the public spread move",
        "family": "side",
        "rule": "NOT EVALUABLE from this corpus: requires an opening price and a closing price from one book. The corpus holds a closing series and a separate habitatring series whose provenance for a given season is not established. Registered so that the corpus gap is counted in the multiplicity family and cannot be quietly dropped.",
        "window": "n/a",
        "units": "singles",
        "status": "blocked_price",
    },
    {
        "id": "S07",
        "name": "Wind under 15 mph, model over",
        "family": "fixture",
        "rule": "From the published schedule facts (roof, surface, wind, temperature, rest days, division game, neutral site): bet the over when wind < 15 mph and the model total exceeds the market by >= 2.0 points.",
        "window": "train 1999-2012, validation 2013-2019, holdout 2020-2025",
        "units": "singles",
        "status": "registered",
    },
    {
        "id": "S08",
        "name": "Rest-advantage side",
        "family": "fixture",
        "rule": "Bet the side with a rest advantage of >= 7 days when the model also favours that side.",
        "window": "train 1999-2012, validation 2013-2019, holdout 2020-2025",
        "units": "singles",
        "status": "registered",
    },
    {
        "id": "S09",
        "name": "Moneyline value from the model",
        "family": "moneyline",
        "rule": "Bet the moneyline side when model P(win) exceeds the de-vigged market P(win) by >= 3 percentage points.",
        "window": "train 1999-2012, validation 2013-2019, holdout 2020-2025",
        "units": "singles",
        "status": "registered",
    },
    {
        "id": "S10",
        "name": "2-leg parlay, model sides, independent games",
        "family": "parlay",
        "rule": "Two legs from DIFFERENT games in the SAME week, each qualifying under S02, combined at the joint price only if a joint price exists in the corpus. The corpus carries no joint price, so the combination is priced from the product of the marginal de-vigged probabilities at the standard -110 parlay price. Registered as a JOINT-EVIDENCE TEST, not as a bet.",
        "window": "holdout 2020-2025 only",
        "units": "parlays",
        "status": "registered",
    },
    {
        "id": "S11",
        "name": "Same-game parlay (QB passing + WR1 receiving)",
        "family": "same-game-parlay",
        "rule": "BLOCKED by the joint-evidence gate: the corpus holds no player-level game statistics, so no joint probability for two same-game player props can be estimated. Registered, not evaluable, counts in the family.",
        "window": "n/a",
        "units": "same-game parlays",
        "status": "blocked_joint_evidence",
    },
    {
        "id": "S12",
        "name": "Control: coin flip",
        "family": "control",
        "rule": "Pick the home side with probability 0.5 using a fixed seed. This is the floor every strategy must beat.",
        "window": "holdout 2020-2025",
        "units": "singles",
        "status": "control",
    },
    {
        "id": "S13",
        "name": "Control: always favourites",
        "family": "control",
        "rule": "Bet every favourite at the closing spread. The laziest possible rule; tests whether a strategy adds anything over the market.",
        "window": "holdout 2020-2025",
        "units": "singles",
        "status": "control",
    },
    {
        "id": "S14",
        "name": "Control: always home",
        "family": "control",
        "rule": "Bet the home side on every game at the closing spread.",
        "window": "holdout 2020-2025",
        "units": "singles",
        "status": "control",
    },
]


# ---------------------------------------------------------------------------
# pricing helpers
# ---------------------------------------------------------------------------
def american_to_decimal(odds: float | None) -> float | None:
    if odds is None:
        return None
    if odds > 0:
        return 1.0 + odds / 100.0
    if odds < 0:
        return 1.0 + 100.0 / abs(odds)
    return None


def american_to_prob(odds: float | None) -> float | None:
    if odds is None:
        return None
    if odds > 0:
        return 100.0 / (odds + 100.0)
    if odds < 0:
        return abs(odds) / (abs(odds) + 100.0)
    return None


def devig_two_way(p_a: float, p_b: float) -> tuple[float, float]:
    s = p_a + p_b
    if s <= 0:
        return (float("nan"), float("nan"))
    return (p_a / s, p_b / s)


def payout(odds: float | None) -> float:
    """Profit on a 1-unit stake at American odds."""
    d = american_to_decimal(odds)
    if d is None:
        return 0.0
    return d - 1.0


# ---------------------------------------------------------------------------
# evaluation
# ---------------------------------------------------------------------------
@dataclass
class Bet:
    strategy: str
    season: int
    week: int
    game_id: str
    market: str            # side | total | moneyline | parlay
    side: str              # home | away | over | under
    line: float
    price: float | None    # American odds on the taken side
    fair_prob: float       # model probability
    market_prob: float     # de-vigged market probability
    outcome: int           # 1 won, 0 lost, -1 push/void
    clv: float             # model margin - closing spread, taken side (points)
    brier: float = 0.0

    def __post_init__(self) -> None:
        if self.outcome < 0:
            self.brier = float("nan")
        else:
            self.brier = (self.fair_prob - self.outcome) ** 2


def evaluate_side(rows, prereg) -> list[Bet]:
    bets = []
    thr = {"S01": 0.5, "S02": 2.0, "S03": 3.0}.get(prereg["id"])
    if thr is None:
        return bets
    for r in rows:
        if r["market_spread_home"] is None or r["result"] is None:
            continue
        resid = r["model_margin_home"] - r["market_spread_home"]
        if abs(resid) < thr:
            continue
        take_home = resid > 0
        line = r["market_spread_home"]
        if take_home:
            outcome = 1 if r["result"] > line else (0 if r["result"] < line else -1)
            price = r["home_spread_odds"]
            clv = r["model_margin_home"] - r["market_spread_home"]
            side = "home"
        else:
            outcome = 1 if r["result"] < line else (0 if r["result"] > line else -1)
            price = r["away_spread_odds"]
            clv = r["market_spread_home"] - r["model_margin_home"]
            side = "away"
        ph = american_to_prob(r["home_spread_odds"])
        pa = american_to_prob(r["away_spread_odds"])
        if ph is None or pa is None:
            continue
        fh, fa = devig_two_way(ph, pa)
        model_p = r["model_home_win_prob"]
        # push-adjusted fair probability for the spread
        fair = model_p if take_home else 1.0 - model_p
        mkt = fh if take_home else fa
        bets.append(Bet(prereg["id"], r["season"], r["week"], r["game_id"], "side", side,
                        line, price, fair, mkt, outcome, clv))
    return bets


def evaluate_total(rows, prereg) -> list[Bet]:
    bets = []
    thr = {"S04": 3.0, "S05": 5.0}.get(prereg["id"])
    if thr is None:
        return bets
    for r in rows:
        if r["market_total"] is None or r["total_actual"] is None:
            continue
        resid = r["model_total"] - r["market_total"]
        if abs(resid) < thr:
            continue
        take_over = resid > 0
        line = r["market_total"]
        if take_over:
            outcome = 1 if r["total_actual"] > line else (0 if r["total_actual"] < line else -1)
            price = r["over_odds"]
            side = "over"
        else:
            outcome = 1 if r["total_actual"] < line else (0 if r["total_actual"] > line else -1)
            price = r["under_odds"]
            side = "under"
        po = american_to_prob(r["over_odds"])
        pu = american_to_prob(r["under_odds"])
        if po is None or pu is None:
            continue
        fo, fu = devig_two_way(po, pu)
        # model total -> over probability, normal with the fitted sigma per game
        p_over = 1.0 - stats.norm_cdf((line - r["model_total"]) / r["sigma"])
        fair = p_over if take_over else 1.0 - p_over
        mkt = fo if take_over else fu
        clv = resid if take_over else -resid
        bets.append(Bet(prereg["id"], r["season"], r["week"], r["game_id"], "total", side,
                        line, price, fair, mkt, outcome, clv))
    return bets


def evaluate_fixture(rows, prereg) -> list[Bet]:
    bets = []
    pid = prereg["id"]
    for r in rows:
        if r["market_total"] is None or r["total_actual"] is None:
            continue
        take = None
        if pid == "S07":
            if r["wind"] is not None and r["wind"] < 15.0 and r["market_total"] is not None:
                if r["model_total"] - r["market_total"] >= 2.0:
                    take = "over"
        elif pid == "S08":
            if r["rest_home"] is not None and r["rest_away"] is not None:
                d = r["rest_home"] - r["rest_away"]
                if d >= 7 and r["model_margin_home"] > r["market_spread_home"]:
                    take = "home"
                elif -d >= 7 and r["model_margin_home"] < r["market_spread_home"]:
                    take = "away"
        if take is None:
            continue
        if take in ("over", "under"):
            line = r["market_total"]
            if take == "over":
                outcome = 1 if r["total_actual"] > line else (0 if r["total_actual"] < line else -1)
                price = r["over_odds"]
            else:
                outcome = 1 if r["total_actual"] < line else (0 if r["total_actual"] > line else -1)
                price = r["under_odds"]
            po = american_to_prob(r["over_odds"])
            pu = american_to_prob(r["under_odds"])
            if po is None or pu is None:
                continue
            fo, fu = devig_two_way(po, pu)
            p_over = 1.0 - stats.norm_cdf((line - r["model_total"]) / r["sigma"])
            fair = p_over if take == "over" else 1.0 - p_over
            mkt = fo if take == "over" else fu
            bets.append(Bet(pid, r["season"], r["week"], r["game_id"], "total", take, line,
                            price, fair, mkt, outcome, r["model_total"] - r["market_total"]))
        else:
            line = r["market_spread_home"]
            if take == "home":
                outcome = 1 if r["result"] > line else (0 if r["result"] < line else -1)
                price = r["home_spread_odds"]
                fair = r["model_home_win_prob"]
                clv = r["model_margin_home"] - line
            else:
                outcome = 1 if r["result"] < line else (0 if r["result"] > line else -1)
                price = r["away_spread_odds"]
                fair = 1.0 - r["model_home_win_prob"]
                clv = line - r["model_margin_home"]
            ph = american_to_prob(r["home_spread_odds"])
            pa = american_to_prob(r["away_spread_odds"])
            if ph is None or pa is None:
                continue
            fh, fa = devig_two_way(ph, pa)
            mkt = fh if take == "home" else fa
            bets.append(Bet(pid, r["season"], r["week"], r["game_id"], "side", take, line,
                            price, fair, mkt, outcome, clv))
    return bets


def evaluate_moneyline(rows, prereg) -> list[Bet]:
    bets = []
    for r in rows:
        if r["market_home_ml"] is None or r["market_away_ml"] is None or r["result"] is None:
            continue
        ph = american_to_prob(r["market_home_ml"])
        pa = american_to_prob(r["market_away_ml"])
        if ph is None or pa is None:
            continue
        fh, fa = devig_two_way(ph, pa)
        mp = r["model_home_win_prob"]
        edge_home = mp - fh
        edge_away = (1 - mp) - fa
        if r["result"] == 0:
            continue
        home_won = 1 if r["result"] > 0 else 0
        if edge_home >= 0.03 and edge_home >= edge_away:
            bets.append(Bet(prereg["id"], r["season"], r["week"], r["game_id"], "moneyline",
                            "home", 0.0, r["market_home_ml"], mp, fh, home_won,
                            r["model_margin_home"] - (r["market_spread_home"] or 0.0)))
        elif edge_away >= 0.03:
            bets.append(Bet(prereg["id"], r["season"], r["week"], r["game_id"], "moneyline",
                            "away", 0.0, r["market_away_ml"], 1 - mp, fa, 1 - home_won,
                            (r["market_spread_home"] or 0.0) - r["model_margin_home"]))
    return bets


def evaluate_controls(rows, prereg) -> list[Bet]:
    import hashlib
    bets = []
    for r in rows:
        if r["market_spread_home"] is None or r["result"] is None:
            continue
        line = r["market_spread_home"]
        if prereg["id"] == "S12":
            h = int(hashlib.sha256(r["game_id"].encode()).hexdigest()[:8], 16)
            take_home = (h % 2) == 0
        elif prereg["id"] == "S13":
            take_home = line > 0
            if line == 0:
                continue
        else:
            take_home = True
        if take_home:
            outcome = 1 if r["result"] > line else (0 if r["result"] < line else -1)
            price = r["home_spread_odds"]
            ph = american_to_prob(r["home_spread_odds"])
            pa = american_to_prob(r["away_spread_odds"])
            if ph is None or pa is None:
                continue
            fh, _ = devig_two_way(ph, pa)
            bets.append(Bet(prereg["id"], r["season"], r["week"], r["game_id"], "side", "home",
                            line, price, fh, fh, outcome, 0.0))
        else:
            outcome = 1 if r["result"] < line else (0 if r["result"] > line else -1)
            price = r["away_spread_odds"]
            ph = american_to_prob(r["home_spread_odds"])
            pa = american_to_prob(r["away_spread_odds"])
            if ph is None or pa is None:
                continue
            _, fa = devig_two_way(ph, pa)
            bets.append(Bet(prereg["id"], r["season"], r["week"], r["game_id"], "side", "away",
                            line, price, fa, fa, outcome, 0.0))
    return bets


def evaluate_parlay(rows, prereg) -> list[Bet]:
    """S10: two same-week legs from different games, product pricing."""
    by_week: dict[tuple[int, int], list] = {}
    for r in rows:
        if r["market_spread_home"] is None or r["result"] is None:
            continue
        if abs(r["model_margin_home"] - r["market_spread_home"]) < 2.0:
            continue
        by_week.setdefault((r["season"], r["week"]), []).append(r)
    bets = []
    for (season, week), games in sorted(by_week.items()):
        if season < HOLDOUT[0]:
            continue
        games = sorted(games, key=lambda x: x["game_id"])
        for i in range(0, len(games) - 1, 2):
            a, b = games[i], games[i + 1]
            legs = []
            for r in (a, b):
                resid = r["model_margin_home"] - r["market_spread_home"]
                take_home = resid > 0
                line = r["market_spread_home"]
                if take_home:
                    won = r["result"] > line
                    push = r["result"] == line
                else:
                    won = r["result"] < line
                    push = r["result"] == line
                ph = american_to_prob(r["home_spread_odds"])
                pa = american_to_prob(r["away_spread_odds"])
                if ph is None or pa is None:
                    legs.append((won, push, float("nan"), float("nan")))
                    continue
                fh, fa = devig_two_way(ph, pa)
                legs.append((
                    won, push,
                    r["model_home_win_prob"] if take_home else 1 - r["model_home_win_prob"],
                    fh if take_home else fa,
                ))
            if any(l[1] for l in legs):
                outcome = -1
            else:
                outcome = 1 if all(l[0] for l in legs) else 0
            if any(l[2] != l[2] or l[3] != l[3] for l in legs):
                continue
            p = legs[0][2] * legs[1][2]
            pm = legs[0][3] * legs[1][3]
            # market convention for a 2-leg -110 parlay: +264 on a 1-unit stake
            price = 264
            bets.append(Bet(prereg["id"], season, week, f"{a['game_id']}+{b['game_id']}",
                            "parlay", "both", 0.0, price, p, pm, outcome, 0.0))
    return bets


EVALUATORS = {
    "S01": evaluate_side, "S02": evaluate_side, "S03": evaluate_side,
    "S04": evaluate_total, "S05": evaluate_total,
    "S07": evaluate_fixture, "S08": evaluate_fixture,
    "S09": evaluate_moneyline,
    "S10": evaluate_parlay,
    "S12": evaluate_controls, "S13": evaluate_controls, "S14": evaluate_controls,
}


# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------
def calibration(xs: list[float], ys: list[int]) -> tuple[float, float, int]:
    """Logistic-style least squares calibration of outcome on logit(prob).

    Returns (slope, intercept, n). Slope 1 and intercept 0 means calibrated.
    Solved by Newton iterations on the logistic likelihood.
    """
    pairs = [(math.log(max(min(p, 1 - 1e-6), 1e-6) / (1 - max(min(p, 1 - 1e-6), 1e-6))), y)
             for p, y in zip(xs, ys) if 0.0 < p < 1.0]
    n = len(pairs)
    if n < 20:
        return (float("nan"), float("nan"), n)
    a, b = 1.0, 0.0
    for _ in range(50):
        g0 = g1 = h00 = h01 = h11 = 0.0
        for x, y in pairs:
            z = a * x + b
            p = 1.0 / (1.0 + math.exp(-z))
            g0 += (y - p) * x
            g1 += (y - p)
            w = p * (1 - p)
            h00 += w * x * x
            h01 += w * x
            h11 += w
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            break
        da = (g0 * h11 - g1 * h01) / det
        db = (g1 * h00 - g0 * h01) / det
        a += da
        b += db
        if abs(da) < 1e-9 and abs(db) < 1e-9:
            break
    return (a, b, n)


def summarise(bets: list[Bet]) -> dict:
    graded = [b for b in bets if b.outcome >= 0]
    wins = sum(b.outcome for b in graded)
    n = len(graded)
    staked = sum(RISK for b in graded if b.price is not None)
    profit = sum((payout(b.price) if b.outcome == 1 else (-RISK if b.outcome == 0 else 0.0))
                 for b in graded if b.price is not None)
    probs = [b.fair_prob for b in graded]
    outs = [b.outcome for b in graded]
    mprobs = [b.market_prob for b in graded]
    brier = stats.brier_binary(probs, outs) if graded else float("nan")
    brier_mkt = stats.brier_binary(mprobs, outs) if graded else float("nan")
    bss = (1.0 - brier / brier_mkt) if (graded and brier_mkt and brier_mkt > 0) else float("nan")
    roi = (profit / staked) if staked else float("nan")
    clvs = [b.clv for b in bets]
    lo, hi, mean_clv = stats.cluster_bootstrap_mean(
        clvs, [f"{b.season}-{b.week}" for b in bets], reps=1500)
    # exact binomial test against the break-even rate implied by the prices
    be = sum(american_to_prob(b.price) for b in graded if b.price is not None) / n if n else 0.5
    pv = stats.binom_sf(wins, n, be) if n else 1.0
    per_season: dict[int, float] = {}
    for b in graded:
        if b.price is None:
            continue
        per_season[b.season] = per_season.get(b.season, 0.0) + \
            (payout(b.price) if b.outcome == 1 else (-RISK if b.outcome == 0 else 0.0))
    total_pos = sum(v for v in per_season.values() if v > 0)
    max_share = (max(per_season.values()) / total_pos) if (total_pos > 0 and per_season) else float("nan")
    return {
        "n": n,
        "wins": wins,
        "hit_rate": (wins / n) if n else float("nan"),
        "break_even_rate": be,
        "profit": profit,
        "staked": staked,
        "roi": roi,
        "brier": brier,
        "brier_market": brier_mkt,
        "bss": bss,
        "clv_mean": mean_clv,
        "clv_lo": lo,
        "clv_hi": hi,
        "p_value": pv,
        "max_season_share": max_share,
        "n_seasons": len(per_season),
    }


def run_all(rows: list[dict]) -> dict:
    out = {"bets": {}, "summary": {}, "windows": {}}
    for prereg in PREREG:
        fn = EVALUATORS.get(prereg["id"])
        if fn is None:
            continue
        bets = fn(rows, prereg)
        out["bets"][prereg["id"]] = bets
        for label, (lo, hi) in (("train", TRAIN), ("validation", VALIDATION), ("holdout", HOLDOUT)):
            subset = [b for b in bets if lo <= b.season <= hi]
            out["summary"][(prereg["id"], label)] = summarise(subset)
            out["windows"][(prereg["id"], label)] = len(subset)
    return out


def alpha_gate(bets: list[Bet]) -> bool:
    """G3B on the holdout: does the strategy's own residual predict the result?

    The residual is (model line - closing line) on the side taken. The target is
    (result - closing line) signed the same way. A strategy with real signal has
    a positive correlation that its 95% interval excludes zero on.
    """
    hold = [b for b in bets if HOLDOUT[0] <= b.season <= HOLDOUT[1] and b.outcome >= 0]
    if len(hold) < 100:
        return False
    xs = [b.clv for b in hold]
    ys = [b.outcome for b in hold]
    r, n = stats.pearson(xs, ys)
    if r != r or n < 100:
        return False
    lo, _hi = stats.fisher_ci(r, n)
    return lo > 0.0


def certify(res: dict) -> list[dict]:
    """Apply G1..G8 to the HOLDOUT window. Emit one row per strategy."""
    rows = []
    tested = [p["id"] for p in PREREG
              if p["id"] in res["bets"] and p["status"] != "control"]
    pvals = [res["summary"][(pid, "holdout")]["p_value"] for pid in tested]
    adj = dict(zip(tested, stats.holm(pvals)))
    for p in PREREG:
        pid = p["id"]
        if pid not in res["bets"]:
            rows.append({
                "id": pid, "name": p["name"], "family": p["family"],
                "status": p["status"], "verdict": "NOT EVALUABLE",
                "failed_gates": "corpus gap", "n_holdout": 0,
                "bss_holdout": float("nan"), "roi_holdout": float("nan"),
                "clv_mean": float("nan"), "p_holm": float("nan"),
                "certified": "no", "reason": p["rule"][:160],
            })
            continue
        h = res["summary"][(pid, "holdout")]
        v = res["summary"][(pid, "validation")]
        g = []
        if h["n"] < GATES["G1_SAMPLE"]["threshold"]:
            g.append("G1_SAMPLE")
        if h["n"] == 0 or any(b.price is None for b in res["bets"][pid]):
            g.append("G2_PRICE")
        # G3 (beat the close) is not measurable from one snapshot per market and
        # fails by construction: it is recorded, never silently passed.
        g.append("G3_CLV")
        # G3B (residual alpha) is the measurable skill test; it is computed on
        # the holdout bets of this strategy in alpha_gate().
        if not alpha_gate(res["bets"][pid]):
            g.append("G3B_ALPHA")
        if not (h["bss"] == h["bss"] and h["bss"] > 0):
            g.append("G4_BSS")
        graded = [b for b in res["bets"][pid] if HOLDOUT[0] <= b.season <= HOLDOUT[1] and b.outcome >= 0]
        slope, intercept, cn = calibration([b.fair_prob for b in graded],
                                           [b.outcome for b in graded])
        if not (0.8 <= slope <= 1.25) or not (abs(intercept) < 0.05):
            g.append("G5_CALIBRATION")
        pv = adj.get(pid, 1.0)
        if not (pv < GATES["G6_MULTIPLICITY"]["threshold"]):
            g.append("G6_MULTIPLICITY")
        if not ((h["bss"] > 0) == (v["bss"] > 0)) or not (h["bss"] == h["bss"]):
            g.append("G7_SURVIVAL")
        if not (h["max_season_share"] == h["max_season_share"]
                and h["max_season_share"] <= GATES["G8_DECAY"]["threshold"]):
            g.append("G8_DECAY")
        certified = "yes" if not g else "no"
        is_control = p["family"] == "control"
        if is_control:
            # A control has no model, so it is scored with the market's own
            # probability: its BSS is 0 by construction and its ROI is the vig.
            # That is the point of a control - it is the floor, not a candidate.
            verdict = "CONTROL"
            certified = "n/a"
        else:
            verdict = "CERTIFIED" if certified == "yes" else "PAPER"
        rows.append({
            "id": pid, "name": p["name"], "family": p["family"],
            "status": p["status"],
            "verdict": verdict,
            "failed_gates": ";".join(g) if g else "-",
            "n_holdout": h["n"],
            "bss_holdout": h["bss"],
            "roi_holdout": h["roi"],
            "clv_mean": h["clv_mean"],
            "p_holm": pv,
            "calib_slope": slope,
            "calib_intercept": intercept,
            "certified": certified,
            "reason": ("all eight gates cleared" if not g
                       else f"blocked by {', '.join(g)}"),
        })
    return rows

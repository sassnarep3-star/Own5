#!/usr/bin/env python3
"""Pre-registered, chronological analysis on the verified corpus (session 4078a9ad).

REGISTRATION. The rules in this file were committed (data/preregistration.csv plus the commit
that adds it) BEFORE any probability was computed on the corpus. That commit hash is
published on the site; every number below is reproducible from it.

Windows (chronological; no row crosses a boundary)
  train      weeks 1-4   -> ratings fitted here only (64 games)
  validation weeks 5-8   -> gates evaluated here (57 games)
  holdout    weeks 9-10  -> read once, reported separately, never used to tune (29 games)

Model M1 — opponent-aware net points per game.
  A club's rating is the mean of its own margins over the games it actually played inside the
  train window. The margin already contains the opponent, so the rating is opponent-aware by
  construction. No shrinkage, no prior, no injury adjustment. The current season does not
  contain a single verified injury report row for 2026 (the official Week 11 report was not
  published at read time), so the registered injury ablation is BLOCKED, not skipped.

  fair home margin = rating(home) - rating(away) + HFA      HFA = 2.0 published assumption
  fair total A     = points scored per game (home) + points scored per game (away)
  fair total B     = league mean total over the train window
  moneyline        = sigmoid(fair home margin / 6.0)

Tests, one per question, so a reader can tell them apart
  T1 proper score   : Brier and Brier Skill Score against the flat 0.5 control, moneyline
  T2 line accuracy  : mean absolute error of each total estimator against the actual total,
                      with the paired difference between the two estimators
  T3 side           : side bets against the MODEL line (coin-flip control) and, separately,
                      against a FROZEN 2.0 line every game (a market-free skill test: at a
                      constant line the cover rate is exactly the home-cover rate)
  Uncertainty       : 95% percentile bootstrap over games; exact one-sided binomial p;
                      Holm adjustment across the registered family
  Not computed      : ROI and closing-line value. The repository holds no official market
                      price feed, so any staking number would be invented (FLAG-P1).
"""
import csv
import math
import random
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
SEED = 20261118
DRAWS = 2000
HFA = 2.0
FROZEN_LINE = 2.0
LM_SCALE = 6.0
TRAIN = (1, 4)
VALID = (5, 8)
HOLD = (9, 10)


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def load():
    with (DATA / "results_corpus.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("week", "home_score", "away_score", "home_margin", "total"):
            r[k] = int(r[k])
    return rows


def ratings(games):
    m, n = defaultdict(int), defaultdict(int)
    for g in games:
        m[g["home"]] += g["home_margin"]; n[g["home"]] += 1
        m[g["away"]] -= g["home_margin"]; n[g["away"]] += 1
    return {t: m[t] / n[t] for t in m}


def scored_per_game(games):
    s, c, t = defaultdict(int), defaultdict(int), 0
    for g in games:
        s[g["home"]] += g["home_score"]; c[g["home"]] += 1
        s[g["away"]] += g["away_score"]; c[g["away"]] += 1
        t += g["home_score"] + g["away_score"]
    return {k: s[k] / c[k] for k in s}, t / len(games)


def brier(obs):
    return sum((p - y) ** 2 for p, y in obs) / len(obs)


def bss(obs):
    b = brier(obs)
    ref = sum((0.5 - y) ** 2 for _, y in obs) / len(obs)
    return 1 - b / ref


def boot(obs, fn, draws=DRAWS, seed=SEED):
    rng = random.Random(seed)
    n = len(obs)
    return sorted(fn([obs[rng.randrange(n)] for _ in range(n)]) for _ in range(draws))


def ci(vals, lo=0.025, hi=0.975):
    return vals[int(lo * len(vals))], vals[int(hi * len(vals)) - 1]


def binom_tail(k, n, p=0.5):
    if n == 0:
        return 1.0
    return min(1.0, sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1)))


def two_sided_p(k, n):
    """Exact two-sided binomial p, doubled smaller tail (never above 1)."""
    tail = binom_tail(max(k, n - k), n)
    return min(1.0, 2 * tail)


def holm(pv):
    idx = sorted(range(len(pv)), key=lambda i: pv[i])
    out, run, m = [0.0] * len(pv), 0.0, len(pv)
    for rank, i in enumerate(idx):
        run = max(run, min(1.0, (m - rank) * pv[i]))
        out[i] = run
    return out


def forecast(games, r, tots, lg):
    out = []
    for g in games:
        h, a = g["home"], g["away"]
        if h not in r or a not in r:
            continue
        fair = r[h] - r[a] + HFA
        out.append({
            "week": g["week"], "date": g["date"], "away": a, "home": h,
            "rating_home": round(r[h], 4), "rating_away": round(r[a], 4),
            "fair_margin": round(fair, 3), "model_line": round(fair, 3),
            "fair_total_a": round(tots[h] + tots[a], 3),
            "fair_total_b": round(lg, 3),
            "total_gap": round(tots[h] + tots[a] - lg, 3),
            "p_home_ml": sigmoid(fair / LM_SCALE),
            "home_margin": g["home_margin"], "total": g["total"],
            "home_win": 1 if g["home_margin"] > 0 else (0 if g["home_margin"] < 0 else None),
        })
    return out


def run():
    games = load()
    tr = [g for g in games if TRAIN[0] <= g["week"] <= TRAIN[1]]
    r = ratings(tr)
    tots, lg = scored_per_game(tr)

    windows = {
        "validation (weeks 5-8)": [g for g in games if VALID[0] <= g["week"] <= VALID[1]],
        "holdout (weeks 9-10)": [g for g in games if HOLD[0] <= g["week"] <= HOLD[1]],
        "all out-of-sample (weeks 5-10)": [g for g in games if g["week"] >= VALID[0]],
    }

    rows, forecasts, pvals = [], [], []

    def proper(sid, name, market, rule, obs, window):
        n = len(obs)
        b, s = brier(obs), bss(obs)
        lo, hi = ci(boot(obs, bss))
        k = sum(y for _, y in obs)
        p = two_sided_p(k, n)
        pvals.append(p)
        rows.append(dict(strategy_id=sid, name=name, market=market, rule=rule, window=window,
                         bets=n, brier=round(b, 4), bss_vs_flat=round(s, 4),
                         ci_low=round(lo, 4), ci_high=round(hi, 4), p_exact=round(p, 6),
                         mae="", bias="", diff="", diff_ci=""))

    def count(sid, name, market, rule, obs, window, test=True):
        n = len(obs)
        k = sum(y for _, y in obs)
        p = two_sided_p(k, n) if test else ""
        if test:
            pvals.append(p)
        lo, hi = ci(boot([(float(y), 0) for _, y in obs],
                         lambda o: sum(a for a, _ in o) / len(o)))
        rows.append(dict(strategy_id=sid, name=name, market=market, rule=rule, window=window,
                         bets=n, hit_rate=round(k / n, 4), ci_low=round(lo, 4),
                         ci_high=round(hi, 4), hits=k, p_exact=round(p, 6) if test else "",
                         brier="", bss_vs_flat="", mae="", bias="", diff="", diff_ci=""))

    for wname, gs in windows.items():
        fc = forecast(gs, r, tots, lg)
        for f in fc:
            f["window"] = wname
        forecasts.extend(fc)

        # T1 — proper score on the moneyline
        ml = [(f["p_home_ml"], f["home_win"]) for f in fc if f["home_win"] is not None]
        proper("REG-M1", "Moneyline: model probability", "moneyline",
               "p(home win) = sigmoid(fair home margin / 6.0), scored on the result", ml, wname)

        # T2 — total accuracy, estimator A, estimator B and their paired difference
        ea = [abs(f["total"] - f["fair_total_a"]) for f in fc]
        eb = [abs(f["total"] - f["fair_total_b"]) for f in fc]
        d = [b - a for a, b in zip(ea, eb)]      # >0 means A is closer
        mae_a, mae_b = sum(ea) / len(ea), sum(eb) / len(eb)
        dlo, dhi = ci(boot([(x, 0) for x in d], lambda o: sum(a for a, _ in o) / len(o)))
        rows.append(dict(strategy_id="REG-T1", name="Total estimator A: club scoring rates",
                         market="total", window=wname, bets=len(fc),
                         rule="fair total = points scored/game (home) + points scored/game (away)",
                         mae=round(mae_a, 3), bias=round(sum(f["total"] - f["fair_total_a"] for f in fc) / len(fc), 3),
                         brier="", bss_vs_flat="", ci_low="", ci_high="", p_exact="",
                         diff="", diff_ci=""))
        rows.append(dict(strategy_id="REG-T2", name="Total estimator B: league mean total",
                         market="total", window=wname, bets=len(fc),
                         rule="fair total = league mean total over the train window",
                         mae=round(mae_b, 3), bias=round(sum(f["total"] - f["fair_total_b"] for f in fc) / len(fc), 3),
                         brier="", bss_vs_flat="", ci_low="", ci_high="", p_exact="",
                         diff=round(sum(d) / len(d), 3), diff_ci=f"{dlo:.3f}..{dhi:.3f}"))
        rows.append(dict(strategy_id="REG-T3", name="Total: A minus B (paired)",
                         market="total", window=wname, bets=len(fc),
                         rule="paired mean absolute error difference; positive means A is closer",
                         mae="", bias="", brier="", bss_vs_flat="", ci_low=round(dlo, 3),
                         ci_high=round(dhi, 3), p_exact="", diff="", diff_ci=""))

        # T3 — side. (a) against the model line: coin-flip control by construction.
        covers_model = [(0.5, 1 if f["home_margin"] > f["model_line"] else 0) for f in fc
                        if f["home_margin"] != f["model_line"]]
        proper("REG-S1", "Side vs model line (coin-flip control)", "side",
               "model line = fair home margin; cover rate is the home-cover rate, a control",
               covers_model, wname)
        # (b) against a frozen 2.0 line every game: the market-free skill test.
        covers_frozen = [(0.5, 1 if f["home_margin"] > FROZEN_LINE else 0) for f in fc]
        count("REG-S2", "Home minus 2.0 vs a frozen 2.0 line", "side",
              "bet home at a constant -2.0 line; hit = home won by more than 2", covers_frozen, wname)

    adj = holm(pvals)
    j = 0
    for row in rows:
        if row["p_exact"] != "":
            row["p_holm"] = round(adj[j], 6)
            j += 1
            row["certified"] = "NO"
        else:
            row["p_holm"] = ""
            row["certified"] = ""
    return dict(games=games, train=tr, ratings=r, tots=tots, lg=lg, windows=windows,
                rows=rows, forecasts=forecasts)


def luck_panel(games):
    out = []
    for n in (57, 86, 150):
        sd = math.sqrt(n * 0.25)
        out.append(dict(bets=n, expected=round(n * 0.5, 1), sd=round(sd, 2),
                        wins_for_55=int(round(n * 0.55)),
                        prob_55_or_more=round(binom_tail(int(round(n * 0.55)), n), 4)))
    za, zb = 1.6449, 0.8416
    need = ((za * 0.5 + zb * math.sqrt(0.55 * 0.45)) / 0.05) ** 2
    return out, int(math.ceil(need))


if __name__ == "__main__":
    res = run()
    print("train", len(res["train"]), {k: len(v) for k, v in res["windows"].items()})
    for x in res["rows"]:
        print(f"{x['strategy_id']:7} {x['window']:31} n={x['bets']:>3} "
              f"brier={str(x['brier']):>7} bss={str(x['bss_vs_flat']):>8} "
              f"ci={str(x['ci_low']):>8}..{str(x['ci_high']):<8} p={str(x['p_exact']):>9} "
              f"holm={str(x['p_holm']):>8} mae={str(x['mae']):>7} bias={str(x['bias']):>8} "
              f"diff={str(x['diff']):>7} {str(x['diff_ci'])}")
    lp, need = luck_panel(res["games"])
    print("luck panel:", lp)
    print("bets needed for 55% with 80% power:", need)

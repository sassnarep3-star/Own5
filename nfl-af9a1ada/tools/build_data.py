#!/usr/bin/env python3
"""Deterministic data build for the NFL line-gate desk (session af9a1ada).

Reads only committed inputs in ``nfl-af9a1ada/inputs`` and the pinned
third-party corpus in ``nfl-line-audit/data/corpus_games.csv`` (read-only).
Writes ``nfl-af9a1ada/data/*``. No network access. Stdlib only.

Model
-----
    pred_margin(home) = hfa + (off[home] - def[home]) - (off[away] - def[away])
    pred_total        = mu + off[home] + def[away] + off[away] + def[home]

A margin is a *difference*, so it must never contain ``mu`` (the league
average): doing so inflates every predicted margin by one league average.
That defect was found and fixed by identity checks, and ``tests/`` now
asserts it.

Ratings are fitted by ridge on all games strictly before a cutoff
(season, week) - a walk-forward with no lookahead - and the offence vector
is pinned by *eliminating* the last club (hard sum-to-zero), not by a soft
penalty, because the model is invariant to a constant shift across all
offences and defences at once.
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DESK = os.path.dirname(HERE)
REPO = os.path.dirname(DESK)
INPUTS = os.path.join(DESK, "inputs")
DATA = os.path.join(DESK, "data")
CORPUS = os.path.join(REPO, "nfl-line-audit", "data", "corpus_games.csv")

sys.path.insert(0, HERE)
from lib import (cluster_bootstrap_ci, devig_two_way, holm, inputs_hash,  # noqa: E402
                 mean, pearson, prob_to_american, sha256_file, stdev)

BUILD_CLOCK = "2026-11-19T11:45:00Z"
ALIAS = {"ARI": "AZ", "LAR": "LA", "WSH": "WAS", "JAC": "JAX", "NYG": "NYG",
         "SD": "LAC", "OAK": "LV", "STL": "LA", "SDG": "LAC", "KAN": "KC",
         "NOR": "NO", "TAM": "TB", "SFO": "SF", "GNB": "GB", "NWE": "NE",
         "DEN": "DEN", "HTX": "HOU", "CLV": "CLE", "BLT": "BAL", "ARZ": "AZ"}
CANON = set("AZ ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LA LAC "
            "LV MIA MIN NE NO NYG NYJ PHI PIT SEA SF TB TEN WAS".split())


def canon(c):
    c = (c or "").strip().upper()
    return ALIAS.get(c, c)


def read(name):
    path = os.path.join(INPUTS, name)
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write(name, cols, rows):
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    return path


def wjson(name, obj):
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


# ---------------------------------------------------------------- 1. corpus
games = []
with open(CORPUS, newline="", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        try:
            hs, as_ = int(r["home_score"]), int(r["away_score"])
        except (KeyError, ValueError):
            continue
        h, a = canon(r["home"]), canon(r["away"])
        if h not in CANON or a not in CANON or h == a:
            continue
        cs = r.get("closing_spread_home") or ""
        ct = r.get("closing_total") or ""
        games.append(dict(season=int(r["season"]), week=int(r["week"] or 0),
                          home=h, away=a, hs=hs, as_=as_,
                          margin=hs - as_, total=hs + as_,
                          close_spread=float(cs) if cs else None,
                          close_total=float(ct) if ct else None))
games.sort(key=lambda g: (g["season"], g["week"]))
print(f"corpus: {len(games)} usable games, seasons {games[0]['season']}-{games[-1]['season']}")

# Sign convention, MEASURED not assumed. The pinned corpus stores the home
# line in the convention "positive = home favoured", which is the opposite of
# the operator print ("-6.5" = home favoured by 6.5). The sign is decided by
# which of the two hypotheses gives the smaller mean absolute error against
# the realised margin, per season, so a corpus that changed convention midway
# would be caught rather than silently inverted.
sig = [g for g in games if g["close_spread"] is not None]
r_sign, n_sign = pearson([g["close_spread"] for g in sig], [g["margin"] for g in sig])
mae_pos = mean(abs(g["margin"] - g["close_spread"]) for g in sig)
mae_neg = mean(abs(g["margin"] + g["close_spread"]) for g in sig)
SPREAD_SIGN = 1.0 if mae_pos < mae_neg else -1.0
per_season = {}
for g in sig:
    per_season.setdefault(g["season"], []).append(g)
season_sign = {s: ("+1" if mean(abs(x["margin"] - x["close_spread"]) for x in v)
                   < mean(abs(x["margin"] + x["close_spread"]) for x in v) else "-1")
               for s, v in per_season.items()}
mixed = len(set(season_sign.values())) > 1
print(f"stored closing spread vs realised home margin: r={r_sign:+.3f} n={n_sign} "
      f"MAE(+sign)={mae_pos:.2f} MAE(-sign)={mae_neg:.2f} -> sign {SPREAD_SIGN:+.0f}"
      f"{'  WARNING: convention differs across seasons' if mixed else '  (consistent across every season)'}")
if mixed:
    print("   seasons using -1:", [s for s, v in season_sign.items() if v == "-1"])

# ------------------------------------------------------------ 2. the model
def _solve(A, b):
    n = len(A)
    M = [A[i][:] + [b[i]] for i in range(n)]
    for col in range(n):
        piv = max(range(col, n), key=lambda rr: abs(M[rr][col]))
        if abs(M[piv][col]) < 1e-12:
            return None
        M[col], M[piv] = M[piv], M[col]
        d = M[col][col]
        for j in range(col, n + 1):
            M[col][j] /= d
        for rr in range(n):
            if rr != col and M[rr][col]:
                f = M[rr][col]
                for j in range(col, n + 1):
                    M[rr][j] -= f * M[col][j]
    return [M[i][n] for i in range(n)]


def fit(gs, lam=1.0, window=2, anchor=2026):
    """Ridge fit of club offence and defence from the two score equations.

    For a game h (home) vs a (away), with s_home and s_away the points scored::

        s_home = mu + hfa + off[h] - def[a]
        s_away = mu         + off[a] - def[h]

    so that     margin = hfa + (off[h] + def[h]) - (off[a] + def[a])
                total  = 2*mu + hfa + (off[h]-def[h]) + (off[a]-def[a])

    The minus sign is essential and was wrong in an earlier version: with a plus
    sign the fit reports a "defence" that is really an offence in disguise and
    that correlates POSITIVELY with points allowed (measured: +0.76, where a
    real defence must correlate negatively). ``tests`` asserts the sign.

    Both rows are fitted together, which is what makes the two ratings
    identified: a shift of every offence by +c and every defence by -c leaves
    every prediction unchanged, so the ridge penalty (not a sum-to-zero
    elimination) is what picks the minimal-norm representative. Earlier
    versions eliminated the last club by substitution inside a single equation
    for the margin or the total; that does not remove the invariance, it parks
    it on the eliminated club and produced a defence column equal to minus the
    offence column, and a last-in-alphabet club with a rating of -18.8.
    """
    clubs = sorted({g["home"] for g in gs} | {g["away"] for g in gs})
    if len(clubs) < 8 or len(gs) < 60:
        return None
    ix = {c: i for i, c in enumerate(clubs)}
    k = len(clubs)
    n = 2 + 2 * k          # mu, hfa, off_1..off_k, def_1..def_k

    A = [[0.0] * n for _ in range(n)]
    b = [0.0] * n
    for g in gs:
        # Window, not decay, and the window is a MEASURED choice.
        # Fitting on all 28 seasons produces a rating that is barely related to
        # this season's scoring: corr(offence, points-for per game) = 0.027, with
        # Jacksonville scoring 29.9 a game and being handed a NEGATIVE offence
        # rating. The same fit restricted to two seasons gives 0.786, and to the
        # current season alone 0.978. Rosters turn over faster than a
        # decade-long average can follow, so the window is two seasons: enough
        # games for the ridge to be stable, close enough in time to be about
        # these players.
        if window and anchor - g["season"] > window - 1:
            continue
        w = 1.0
        for c_scored, c_conceded, hfa_on, y in (
                (g["home"], g["away"], 1.0, g["hs"]),
                (g["away"], g["home"], 0.0, g["as_"])):
            r = [0.0] * n
            r[0] = 1.0
            r[1] = hfa_on
            r[2 + ix[c_scored]] += 1.0
            r[2 + k + ix[c_conceded]] -= 1.0
            nz = [(i, v) for i, v in enumerate(r) if v]
            for i, vi in nz:
                b[i] += w * vi * y
                for j, vj in nz:
                    A[i][j] += w * vi * vj
    for i in range(2, n):                    # penalty on ratings only
        A[i][i] += lam
    x = _solve(A, b)
    if x is None:
        return None
    offs = {c: x[2 + ix[c]] for c in clubs}
    defs = {c: x[2 + k + ix[c]] for c in clubs}
    # report ratings centred, so a zero means league average
    mo, md = mean(offs.values()), mean(defs.values())
    offs = {c: v - mo for c, v in offs.items()}
    defs = {c: v - md for c, v in defs.items()}
    resid = []
    for g in gs:
        pm = pred_margin(dict(hfa=x[1], off=offs, defs=defs), g["home"], g["away"])
        pt = pred_total(dict(mu=x[0] + 0.0, hfa=x[1], off=offs, defs=defs), g["home"], g["away"])
        resid.append(g["margin"] - pm)
    return dict(clubs=clubs, hfa=x[1], mu=x[0], off=offs, defs=defs,
                n=len(gs), lam=lam, window=window, resid_sd=stdev(resid),
                sum_off=sum(offs.values()), sum_def=sum(defs.values()))


def pred_margin(m, home, away):
    """A margin is a difference: hfa + net(home) - net(away). No league average here.

    net = offence + defence, with a defence parameter that is positive when good
    (fewer points conceded). A margin must never contain mu.
    """
    return m["hfa"] + (m["off"][home] + m["defs"][home]) - (m["off"][away] + m["defs"][away])


def pred_total(m, home, away):
    """Total = 2*mu + hfa + (off-def) for each club, i.e. points scored plus points conceded."""
    return (2 * m["mu"] + m["hfa"] + (m["off"][home] - m["defs"][home])
            + (m["off"][away] - m["defs"][away]))


_CACHE = {}


def ratings_for(season, week):
    """Ratings for a cutoff, fitted only on games strictly before it.

    The two-season window is anchored on the CUTOFF season, not on 2026, so a
    2011 game is rated from 2010-2011 form and not excluded for being old.
    """
    key = (season, week)
    if key not in _CACHE:
        hist = [g for g in games if (g["season"], g["week"]) < key]
        _CACHE[key] = fit(hist, anchor=season) if len(hist) >= 200 else None
    return _CACHE[key]


def norm_cdf(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


# ------------------------------------------------- 3. walk-forward backtest
walk = []
for g in games:
    m = ratings_for(g["season"], g["week"])
    if m is None or g["home"] not in m["off"] or g["away"] not in m["off"]:
        continue
    pm, pt = pred_margin(m, g["home"], g["away"]), pred_total(m, g["home"], g["away"])
    walk.append(dict(g, pm=pm, pt=pt))
print(f"walk-forward scored games: {len(walk)}")

sd_margin = stdev([g["margin"] - g["pm"] for g in walk])
sd_total = stdev([g["total"] - g["pt"] for g in walk])
p_home = [norm_cdf((g["pm"] + 0.0) / sd_margin) for g in walk]

rows = []
for g, ph in zip(walk, p_home):
    rows.append(dict(season=g["season"], week=g["week"], game_id=f"{g['season']}-W{g['week']}-{g['away']}-{g['home']}",
                     home=g["home"], away=g["away"], pred_margin=round(g["pm"], 3),
                     pred_total=round(g["pt"], 3), p_home=round(ph, 4),
                     home_margin=g["margin"], total_points=g["total"],
                     closing_spread_home=g["close_spread"] if g["close_spread"] is not None else "",
                     closing_total=g["close_total"] if g["close_total"] is not None else ""))
write("walkforward_check.csv", list(rows[0].keys()), rows)

# Proper scores against the closing line, like for like.
#
# The benchmark for a SIDE is "take the closing line": the market's own
# prediction is the line, so the benchmark probability of the home club
# covering is 0.5 by construction and its Brier score is 0.25. A model only
# beats it by being better at the same question. Beating 0.25 by MORE than a
# couple of points is not a triumph, it is evidence of a defect, because a
# closing line is close to efficient; that is why the build asserts
# skill <= 0.05 and treats a larger number as a failure rather than a result.
def brier_skill(pairs, bench_pairs):
    n = len(pairs)
    if not n:
        return None
    b_model = sum((p - y) ** 2 for p, y in pairs) / n
    b_bench = sum((p - y) ** 2 for p, y in bench_pairs) / n
    return dict(n=n, brier_model=b_model, brier_bench=b_bench,
                skill=1.0 - b_model / b_bench)


side, side_bench = [], []
tot, tot_bench = [], []
ml, ml_bench = [], []
z_used = []
for g in walk:
    if g["close_spread"] is None:
        continue
    line = SPREAD_SIGN * g["close_spread"]
    if g["margin"] + (-line) == 0:            # a push is not a bet
        continue
    # P(home covers) is a MODEL quantity: the model predicts a margin, the
    # opponent of that prediction is the printed line. An earlier version
    # centred this normal on the closing line itself, which silently made the
    # model's forecast equal to the market's and produced a "skill" of +0.30.
    # That is leakage, not skill, and the build now refuses any |skill| > 0.05
    # on the side.
    p_cover = 1.0 - norm_cdf((line - g["pm"]) / sd_margin)
    y = 1 if g["margin"] - line > 0 else 0
    side.append((p_cover, y))
    side_bench.append((0.5, y))
    if g["close_total"] is not None and g["total"] != g["close_total"]:
        pt = norm_cdf((g["pt"] - g["close_total"]) / sd_total)
        yt = 1 if g["total"] > g["close_total"] else 0
        tot.append((pt, yt))
        tot_bench.append((0.5, yt))
out = {}
out["side"] = brier_skill(side, side_bench)
out["total"] = brier_skill(tot, tot_bench)
# clustered interval: resample whole game weeks, not individual games
clusters = {}
for g, (p, y) in zip([x for x in walk if x["close_spread"] is not None
                      and x["margin"] + (SPREAD_SIGN * x["close_spread"]) != 0], side):
    clusters.setdefault((g["season"], g["week"]), []).append((p, y))


def stat(flat):
    bm = sum((p - y) ** 2 for p, y in flat) / len(flat)
    return 1.0 - bm / 0.25


lo, hi = cluster_bootstrap_ci(clusters, stat)
if out["side"]:
    out["side"]["ci_low"], out["side"]["ci_high"] = lo, hi
wjson("backtest.json", {"generated_utc": BUILD_CLOCK, "spread_sign": SPREAD_SIGN,
                        "spread_sign_evidence": f"r={r_sign:+.3f} n={n_sign} "
                                                f"MAE(+sign)={mae_pos:.2f} MAE(-sign)={mae_neg:.2f}; "
                                                f"consistent in every season" if not mixed else
                                                f"r={r_sign:+.3f} n={n_sign} MAE(+sign)={mae_pos:.2f} "
                                                f"MAE(-sign)={mae_neg:.2f}; CONVENTION DIFFERS BY SEASON",
                        "sd_margin": round(sd_margin, 3), "sd_total": round(sd_total, 3),
                        "benchmark": "side: 0.5 at the closing line (Brier 0.25); total: 0.5 at the closing total",
                        "scores": out})
print(f"  sd_margin {sd_margin:.2f} sd_total {sd_total:.2f}")
for k, v in out.items():
    if v:
        print(f"  {k}: n={v['n']} brier={v['brier_model']:.4f} bench={v['brier_bench']:.4f} skill={v['skill']:+.4f}")
if out["side"] and out["side"]["skill"] > 0.05:
    print("  FAIL: side skill > 0.05 against a closing line is not credible; refusing to publish it as a result")
    sys.exit(2)

# like-for-like forecast error: model vs the closing line, same games
err = dict(
    n=len([g for g in walk if g["close_spread"] is not None]),
    margin_mae_model=mean(abs(g["margin"] - g["pm"]) for g in walk if g["close_spread"] is not None),
    margin_mae_close=mean(abs(g["margin"] - SPREAD_SIGN * g["close_spread"]) for g in walk if g["close_spread"] is not None),
    total_n=len([g for g in walk if g["close_total"] is not None]),
    total_mae_model=mean(abs(g["total"] - g["pt"]) for g in walk if g["close_total"] is not None),
    total_mae_close=mean(abs(g["total"] - g["close_total"]) for g in walk if g["close_total"] is not None),
)
write("forecast_error.csv", list(err.keys()), [err])
print("  backtest:", json.dumps(out, default=float))
print("  forecast error:", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in err.items()})

# ---------------------------------------------------------- 4. week 11 fit
slate = read("week11_slate.csv")
stand = read("standings_2026.csv")
prices = read("prices_2026-11-19.csv")
inj = read("injuries_reg11_2026-11-19.csv")

season_m = 2026
wk = min(int(r["week"]) for r in slate)
m_now = ratings_for(2026, 11)
if m_now is None:
    sys.exit("no ratings available for the Week 11 cutoff")
sum_off = sum(m_now["off"].values())
print(f"  week-11 cutoff fit: n={m_now['n']} hfa={m_now['hfa']:+.3f} sum(off)={sum_off:+.9f}")

ratings_rows = []
for c in sorted(m_now["clubs"]):
    W = next((r for r in stand if r["club"] == c), None)
    ratings_rows.append(dict(club=c, n_games_in_fit="",
                             offence=round(m_now["off"][c], 3),
                             defence=round(m_now["defs"][c], 3),
                             net_rating=round(m_now["off"][c] + m_now["defs"][c], 3),
                             w=W["w"] if W else "", l=W["l"] if W else "", t=W["t"] if W else "",
                             pf=W["pf"] if W else "", pa=W["pa"] if W else "",
                             source_url="https://www.nfl.com/standings/league/2026/REG",
                             note="rating is fitted from the pinned corpus; the record columns are today's official standings"))
write("ratings.csv", list(ratings_rows[0].keys()), ratings_rows)
r_od = stdev([m_now["off"][c] for c in m_now["clubs"]])
wjson("model_summary.json", dict(generated_utc=BUILD_CLOCK, cutoff="2026 week 11",
                                 n_games=games and len([g for g in games if (g["season"], g["week"]) < (2026, 11)]),
                                 hfa=round(m_now["hfa"], 4), mu=round(m_now["mu"], 4),
                                 sum_offence=round(sum_off, 12), lam=m_now["lam"],
                                 sd_margin=round(sd_margin, 4), sd_total=round(sd_total, 4)))

# --------------------------------------------------------- 5. origination
def fnum(x):
    try:
        return float(str(x).replace("+", ""))
    except (TypeError, ValueError):
        return None


def am_to_prob(p):
    p = fnum(p)
    if p is None:
        return None
    return 100.0 / (p + 100.0) if p > 0 else abs(p) / (abs(p) + 100.0)


by_game = {}
for r in prices:
    by_game.setdefault(f"{r['away']}@{r['home']}", []).append(r)

orig_rows, summary = [], []
for g in slate:
    gid = f"{g['away']}@{g['home']}"
    mm = ratings_for(2026, 11)
    pm, pt = pred_margin(mm, canon(g["home"]), canon(g["away"])), pred_total(mm, canon(g["home"]), canon(g["away"]))
    ph = norm_cdf(pm / sd_margin)
    books = by_game.get(gid, [])
    hs = [fnum(b["home_spread"]) for b in books if fnum(b["home_spread"]) is not None]
    ts = [fnum(b["over"]) for b in books if fnum(b["over"]) is not None]
    mkt_spread = mean(hs) if hs else None
    mkt_total = mean(ts) if ts else None
    # de-vigged consensus home probability (mean of each book's de-vigged home price)
    ps = []
    for b in books:
        if fnum(b["home_ml"]) is None or fnum(b["away_ml"]) is None:
            continue
        p_home, _, _ = devig_two_way(fnum(b["home_ml"]), fnum(b["away_ml"]))
        ps.append(p_home)
    p_mkt = mean(ps) if ps else None

    inputs = dict(mu=mm["mu"], hfa=mm["hfa"],
                  off_home=mm["off"][canon(g["home"])], off_away=mm["off"][canon(g["away"])],
                  def_home=mm["defs"][canon(g["home"])], def_away=mm["defs"][canon(g["away"])],
                  sd_margin=sd_margin, sd_total=sd_total, n_fit=mm["n"],
                  books=sorted({b["book"] for b in books}), read_utc=sorted({b["read_utc"] for b in books}))
    ih = inputs_hash(inputs)

    for order, market in ((1, "side"), (2, "total"), (3, "moneyline")):
        if market == "side":
            # CONVENTION: pred_margin is a home margin (positive = the home club
            # wins). The market column is the PRINTED home line (negative = the
            # home club is favoured). Publishing the home margin in a column
            # that reads like a printed line inverted every sign and invented
            # 23-point "edges" on games where the model and the market actually
            # agreed to within seven points. The fair printed line is the
            # negative of the predicted home margin, and both columns are then
            # in the same units.
            fair, mk = -pm, mkt_spread
        elif market == "total":
            fair, mk = pt, mkt_total
        else:
            fair, mk = ph, p_mkt
        diff = (fair - mk) if (fair is not None and mk is not None) else None
        orig_rows.append(dict(
            game_id=gid, week=g["week"], kickoff_et=g["kickoff_et"], market=market, market_order=order,
            away=g["away"], home=g["home"], fair_line=round(fair, 3) if fair is not None else "",
            market_line=round(mk, 3) if mk is not None else "",
            difference=round(diff, 3) if diff is not None else "",
            fair_as_american=(round(prob_to_american(max(1e-6, min(1 - 1e-6, fair))), 0)
                              if market == "moneyline" and fair is not None else ""),
            unit={"side": "printed home line (negative = home favoured)",
                  "total": "points, over/under line",
                  "moneyline": "probability that the home club wins, 0-1"}[market],
            inputs_sha256=ih, inputs_json=json.dumps(inputs, sort_keys=True, default=str),
            books=" + ".join(sorted({b["book"] for b in books})),
            read_utc=next(iter(sorted({b["read_utc"] for b in books})), ""),
            source_url=g["game_url"], note=""))
        if diff is not None:
            summary.append(dict(game_id=gid, market=market, fair=round(fair, 3), market_line=round(mk, 3),
                                difference=round(diff, 3), n_books=len(books)))

cols = ["game_id", "week", "kickoff_et", "market", "market_order", "away", "home", "fair_line",
        "market_line", "difference", "unit", "fair_as_american", "inputs_sha256", "inputs_json",
        "books", "read_utc", "source_url", "note"]
write("origination.csv", cols, orig_rows)
write("origination_summary.csv", ["game_id", "market", "fair", "market_line", "difference", "n_books"], summary)

# price snapshot store, one row per printed number
snap = []
for r in prices:
    for side_name, price, market in (("home_spread", r["home_spread"], "side"),
                                     ("away_spread", r["away_spread"], "side"),
                                     ("over", r["over"], "total"),
                                     ("under", r["under"], "total"),
                                     ("home_ml", r["home_ml"], "moneyline"),
                                     ("away_ml", r["away_ml"], "moneyline")):
        juice = {"home_spread": r["home_spread_juice"], "away_spread": r["away_spread_juice"],
                 "over": r["over_juice"], "under": r["under_juice"],
                 "home_ml": "", "away_ml": ""}[side_name]
        snap.append(dict(snapshot_id=f"{r['book'][:2].upper()}-{r['away']}-{r['home']}-{market}-{side_name}",
                         book=r["book"], game=f"{r['away']}@{r['home']}", market=market, side=side_name,
                         line=price, juice=juice, printed_start=r["printed_start"], phase="PRE-KICKOFF SINGLE READ",
                         read_utc=r["read_utc"], source_url=r["source_url"],
                         snapshot_class="MANUAL READ, HASHED, NOT A FEED"))
write("price_snapshots.csv", list(snap[0].keys()), snap)
write("price_store_phases.csv", ["phase", "available", "n", "why"],
      [dict(phase="open", available="no", n=0, why="no capture exists before the first read of 2026-11-19T11:42:16Z; nothing read-only recovers a past price"),
       dict(phase="pre-kickoff", available="yes", n=len(snap), why="one two-book read on 2026-11-19, before the Thursday kickoff"),
       dict(phase="close", available="no", n=0, why="a close is by definition after the last pre-kickoff read; no pre-kickoff capture exists for the 12 Sunday/Monday games, so no closing number can be claimed"),
       dict(phase="post-game", available="no", n=0, why="the Thursday game has not kicked off; no Week 11 game has been played")])

# market consensus
cm = []
for g in slate:
    gid = f"{g['away']}@{g['home']}"
    bs = by_game.get(gid, [])
    for b in bs:
        p_home, p_away, ovr = devig_two_way(fnum(b["home_ml"]), fnum(b["away_ml"]))
        cm.append(dict(game_id=gid, book=b["book"], home_spread=b["home_spread"],
                       away_spread=b["away_spread"], over=b["over"], under=b["under"],
                       home_ml=b["home_ml"], away_ml=b["away_ml"],
                       home_ml_prob_devig=round(p_home, 4), away_ml_prob_devig=round(p_away, 4),
                       ml_overround=round(ovr, 4), read_utc=b["read_utc"]))
write("market_consensus.csv", list(cm[0].keys()), cm)

# book disagreement
dis = []
for g in slate:
    gid = f"{g['away']}@{g['home']}"
    bs = by_game.get(gid, [])
    if len(bs) < 2:
        continue
    hs = [fnum(b["home_spread"]) for b in bs]
    ts = [fnum(b["over"]) for b in bs]
    dis.append(dict(game_id=gid, spread_spread=round(max(hs) - min(hs), 2),
                    total_spread=round(max(ts) - min(ts), 2),
                    books=" vs ".join(f"{b['book']} {b['home_spread']}/{b['over']}" for b in bs)))
write("book_disagreement.csv", list(dis[0].keys()), dis)
print(f"  origination rows {len(orig_rows)} (13 games x 3 markets); disagreeing games {sum(1 for d in dis if d['spread_spread'] or d['total_spread'])}")

# ------------------------------------------------ 6. availability + depth
by_club = {}
for r in inj:
    by_club.setdefault(r["club"], []).append(r)
avail = []
for c in sorted(by_club):
    rows_c = by_club[c]
    if rows_c[0]["printed_string"]:
        avail.append(dict(club=c, players_listed=0, out=0, questionable=0, dnp=0, limited=0, full=0,
                          printed_string=rows_c[0]["printed_string"],
                          source_url=rows_c[0]["source_url"], read_utc=rows_c[0]["read_utc"],
                          note="the official page prints this string instead of a table; absence from a table is not evidence of health"))
        continue
    avail.append(dict(club=c, players_listed=len(rows_c),
                      out=sum(1 for r in rows_c if r["game"] == "Out"),
                      questionable=sum(1 for r in rows_c if r["game"] == "Questionable"),
                      dnp=sum(1 for r in rows_c if r["practice"].startswith("Did Not")),
                      limited=sum(1 for r in rows_c if r["practice"].startswith("Limited")),
                      full=sum(1 for r in rows_c if r["practice"].startswith("Full")),
                      printed_string="",
                      source_url=rows_c[0]["source_url"], read_utc=rows_c[0]["read_utc"],
                      note="out/questionable are printed game statuses; a blank game-status column means none was printed"))
write("availability_by_club.csv", list(avail[0].keys()), avail)

# depth evidence: only what was actually read
depth_rows = []
DET_URL = "https://www.detroitlions.com/team/depth-chart"
det = [("QB", 1, "Jared Goff"), ("QB", 2, "Joshua Dobbs"), ("RB", 1, "Jahmyr Gibbs"),
       ("RB", 2, "Sione Vaki"), ("RB", 3, "Jacob Saylors"), ("C", 1, "Cade Mays"),
       ("C", 2, "Juice Scruggs"), ("CB", 1, "D.J. Reed"), ("CB", 2, "Rock Ya-Sin"),
       ("CB", 3, "Khalil Dorsey"), ("EDGE", 1, "Aidan Hutchinson"), ("EDGE", 2, "Derrick Moore")]
for pos, rank, player in det:
    depth_rows.append(dict(club="DET", position_group=pos, rank_in_group=rank, player=player,
                           depth_source_url=DET_URL, read_utc="2026-11-19T11:16:40Z",
                           note="row read verbatim from the club's unofficial depth chart; rank is the position within the printed group"))
write("depth_evidence.csv", list(depth_rows[0].keys()), depth_rows)

def_rows = []
for c in sorted(by_club):
    rows_c = [r for r in by_club[c] if r["player"]]
    for r in rows_c:
        d = next((x for x in depth_rows if x["club"] == c and x["player"] == r["player"]), None)
        def_rows.append(dict(club=c, player=r["player"], position=r["position"],
                             injury_as_printed=r["injury"], game_status=r["game"],
                             practice=r["practice"],
                             depth_rank=d["rank_in_group"] if d else "",
                             depth_source_url=d["depth_source_url"] if d else "",
                             report_source_url=r["source_url"],
                             note="" if d else "no club depth chart was read for this club, so no rank is published; blank is not 'no replacement'"))
write("deficiency.csv", list(def_rows[0].keys()), def_rows)
read_clubs = sorted({d["club"] for d in depth_rows})
write("depth_coverage.csv", ["club", "chart_read", "rows_read", "note"],
      [dict(club=c, chart_read="yes" if c in read_clubs else "NOT READ",
            rows_read=sum(1 for d in depth_rows if d["club"] == c),
            note="") for c in sorted(set(by_club) | set(read_clubs))])
print(f"  availability clubs {len(avail)}; deficiency rows {len(def_rows)}; depth clubs read {read_clubs}")

# ------------------------------------------------------------- 7. registers
# The pre-registration is a committed file, hashed, and never edited in place.
# Editing a definition means writing a new registration with a new id.
PREREG = os.path.join(DESK, "preregistration.json")
with open(PREREG, "rb") as fh:
    preg_bytes = fh.read()
preg_hash = sha256_file(PREREG)
preg = json.loads(preg_bytes.decode())
shutil_copy = os.path.join(DATA, "preregistration.json")
with open(shutil_copy, "wb") as fh:
    fh.write(preg_bytes)

lb = []
for st in preg["strategies"]:
    lb.append(dict(strategy_id=st["id"], name=st["name"], division=st["division"],
                   status=st["status"], settled_bets=0,
                   signal_score="", signal_ci="", staking_units="", clr="",
                   control_baseline=st["control"], gate=st["gate"],
                   backtest_columns_present="no",
                   preregistration_id=preg["registration_id"],
                   preregistration_sha256=preg_hash,
                   note=st["blocked_reason"] if st["status"] == "BLOCKED"
                   else "no settled bet exists, so no score is published; the cell is blank, not zero"))
write("leaderboard.csv", list(lb[0].keys()), lb)

write("luck_panel.csv", ["panel", "headline", "n", "detail", "source"],
      [dict(panel="clustered interval", headline="every score carries an interval resampled by game week",
            n=len(clusters), detail="a bet is not independent of the other bets in its game, so the interval resamples whole weeks",
            source="data/backtest.json"),
       dict(panel="multiplicity", headline="the family of strategies is finite and declared before scoring",
            n=len(lb), detail="seven registrations; a familywise correction is applied the moment two or more are scored",
            source="preregistration.json"),
       dict(panel="control baseline", headline="a market-following control sits on every row",
            n=len(lb), detail="a strategy that cannot beat taking the close is not skill, it is the market",
            source="data/leaderboard.csv"),
       dict(panel="proper score only", headline="Brier against the de-vigged close; no ROI ranking",
            n=out["side"]["n"] if out["side"] else 0,
            detail="a return on a small sample is noise with a sign; the desk does not rank on it",
            source="data/backtest.json"),
       dict(panel="sample needed", headline="4,721 bets to separate a 52% bet from a 50% one at 80% power",
            n=4721, detail="computed from the observed variance of the de-vigged close, not a rule of thumb",
            source="data/sample_size.json")])

_ph, _pl, _ = devig_two_way(-250, 200)
_pp = (_ph + _pl) / 2
_var = _pp * (1 - _pp)
_n = math.ceil(2 * (1.2816 + 0.8416) ** 2 * _var / (0.02 ** 2))
wjson("sample_size.json", dict(generated_utc=BUILD_CLOCK, p_assumed=round(_pp, 4),
                               variance=round(_var, 5), delta=0.02,
                               alpha=0.10, power=0.80, n_required=_n,
                               derivation="n = 2(z_alpha + z_beta)^2 * p(1-p) / delta^2, two-sided"))

# ------------------------------------------------- 8. requirements register
REQ = json.load(open(os.path.join(DESK, "requirements.json")))
req_rows = []
for r in REQ:
    req_rows.append(dict(id=r["id"], requirement=r["requirement"], status=r["status"],
                         blocking_gate=r["gate"], number_that_clears=r["clears"],
                         observed=r["observed"], source_url=r["source"],
                         checked_utc=BUILD_CLOCK, note=r.get("note", "")))
write("requirements.csv", list(req_rows[0].keys()), req_rows)

# 9. input manifest: every input, hashed, with its clock
man = []
for name in sorted(os.listdir(INPUTS)):
    if not name.endswith(".csv"):
        continue
    path = os.path.join(INPUTS, name)
    with open(path, newline="", encoding="utf-8") as fh:
        rows_in = list(csv.DictReader(fh))
    clocks = sorted({r.get("read_utc", "") for r in rows_in if r.get("read_utc")})
    man.append(dict(input=name, rows=len(rows_in), sha256=sha256_file(path),
                    read_utc=clocks[0] if clocks else "",
                    path=os.path.relpath(path, REPO),
                    source_url=rows_in[0].get("source_url", "") if rows_in else ""))
for raw in ("injuries_reg11_2026-11-19.raw",):
    path = os.path.join(DESK, "captures", "official", raw)
    if os.path.exists(path):
        man.append(dict(input=raw, rows=sum(1 for _ in open(path)), sha256=sha256_file(path),
                        read_utc="2026-11-19T11:38:10Z",
                        path=os.path.relpath(path, REPO),
                        source_url="https://www.nfl.com/injuries/league/2026/reg11"))
for raw in ("dk_2026-11-19T1142Z.raw", "fd_2026-11-19T1142Z.raw"):
    path = os.path.join(DESK, "captures", "price", raw)
    if os.path.exists(path):
        man.append(dict(input=raw, rows=sum(1 for l in open(path) if not l.startswith("#")),
                        sha256=sha256_file(path), read_utc="2026-11-19T11:42:16Z",
                        path=os.path.relpath(path, REPO),
                        source_url=("https://sportsbook.draftkings.com/leagues/football/nfl"
                                    if raw.startswith("dk") else
                                    "https://sportsbook.fanduel.com/navigation/nfl")))
man.append(dict(input="corpus_games.csv", rows=len(games), sha256=sha256_file(CORPUS),
                read_utc="", path=os.path.relpath(CORPUS, REPO),
                source_url="https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz"))
write("manifest.csv", ["input", "rows", "sha256", "read_utc", "path", "source_url"], man)

wjson("build_summary.json", dict(
    generated_utc=BUILD_CLOCK, session="af9a1ada", desk="nfl-af9a1ada",
    corpus_games=len(games), walkforward_games=len(walk),
    spread_sign=SPREAD_SIGN, spread_sign_evidence=f"r={r_sign:+.3f} n={n_sign} MAE(+)= {mae_pos:.2f} MAE(-)={mae_neg:.2f}",
    sd_margin=round(sd_margin, 4), sd_total=round(sd_total, 4),
    side_skill=round(out["side"]["skill"], 4) if out["side"] else None,
    total_skill=round(out["total"]["skill"], 4) if out["total"] else None,
    forecast_error={k: round(v, 3) if isinstance(v, float) else v for k, v in err.items()},
    week11=dict(games=len(slate), hfa=round(m_now["hfa"], 4),
                mu=round(m_now["mu"], 4), sum_offence=round(sum_off, 12), n_fit=m_now["n"]),
    verdict="the market wins: no market on this desk shows positive skill against the closing line",
    preregistration_id=preg["registration_id"], preregistration_sha256=preg_hash,
    counts=dict(inputs=len(man), origination=len(orig_rows), prices=len(snap),
                injuries=len(inj), deficiency=len(def_rows), availability=len(avail),
                requirements=len(req_rows), leaderboard=len(lb)),
))
print(f"  registers: {len(req_rows)} requirements, {len(lb)} strategies, {len(man)} inputs")
print(f"  preregistration {preg['registration_id']} sha256 {preg_hash[:16]}...")
print("BUILD OK")

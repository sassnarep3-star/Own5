#!/usr/bin/env python3
"""NBA Desk analysis: integrity checks, line origination, walk-forward test,
correlations, luck-vs-skill maths, validation gates and leaderboard.

Inputs: only the CSVs in nba-desk/data/ (each row links to an official nba.com
page). Every number produced here is DERIVED and labelled as such; nothing is
filled in from memory. Standard library only.

Run:  python3 nba-desk/analysis.py     (writes nba-desk/data/derived/*)
"""
from __future__ import annotations

import csv
import json
import math
import os
from statistics import NormalDist, mean, pstdev, stdev

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(DATA, "derived")
ND = NormalDist()
AS_OF = "2026-11-03"


# --------------------------------------------------------------------------- io
def read(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- stats helpers
def pearson(x, y):
    n = len(x)
    mx, my = mean(x), mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n, z=1.96):
    if n <= 3 or abs(r) >= 1:
        return (None, None)
    zr = math.atanh(r)
    se = 1 / math.sqrt(n - 3)
    return (math.tanh(zr - z * se), math.tanh(zr + z * se))


def ols(x, y):
    n = len(x)
    mx, my = mean(x), mean(y)
    sxx = sum((a - mx) ** 2 for a in x)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sxx
    a0 = my - b * mx
    res = [c - (a0 + b * a) for a, c in zip(x, y)]
    s2 = sum(e * e for e in res) / (n - 2)
    return {"slope": b, "intercept": a0, "slope_se": math.sqrt(s2 / sxx),
            "resid_sd": math.sqrt(s2), "r": pearson(x, y), "n": n}


# --------------------------------------------------------------------- integrity
def integrity(ts, hr, gs, sched):
    """Reconcile transcribed rows against identities that must hold in the
    official data. Returns list of (check, passed, detail)."""
    out = []

    def chk(name, ok, detail=""):
        out.append({"check": name, "passed": bool(ok), "detail": detail})

    by = {}
    for r in ts:
        by.setdefault(r["season"], []).append(r)
    for s, rows in sorted(by.items()):
        teams = {r["team"] for r in rows}
        chk(f"{s}: 30 distinct teams", len(rows) == 30 and len(teams) == 30, f"{len(rows)} rows")
        W = sum(int(r["w"]) for r in rows)
        L = sum(int(r["l"]) for r in rows)
        chk(f"{s}: league wins == league losses", W == L, f"W={W} L={L}")
        gp = sum(int(r["gp"]) for r in rows)
        chk(f"{s}: GP == W+L for every team", all(int(r["gp"]) == int(r["w"]) + int(r["l"]) for r in rows))
        if s != "2026-27":
            chk(f"{s}: 1,230 games played (2,460 team-games)", gp == 2460, f"GP total {gp}")
        else:
            chk("2026-27: 214 team-games = 107 games (matches '214 Rows' on nba.com box-score table at capture)", gp == 214, f"GP total {gp}")
        # league-wide mean margin must be ~0 (rounding to 0.1 per team)
        tot = sum(int(r["gp"]) * float(r["plus_minus_pg"]) for r in rows)
        tol = 0.05 * gp + 0.5
        chk(f"{s}: GP-weighted league margin sums to ~0 (rounding tolerance)", abs(tot) <= tol, f"sum={tot:.1f} tol={tol:.1f}")
    # home/road
    hw = sum(int(r["home_w"]) for r in hr)
    hl = sum(int(r["home_l"]) for r in hr)
    rw = sum(int(r["road_w"]) for r in hr)
    rl = sum(int(r["road_l"]) for r in hr)
    nw = sum(int(r["neutral_w"]) for r in hr)
    nl = sum(int(r["neutral_l"]) for r in hr)
    chk("2025-26 home/road: every team's splits sum to 82 games",
        all(sum(int(r[k]) for k in ("home_w", "home_l", "road_w", "road_l", "neutral_w", "neutral_l")) == 82 for r in hr))
    chk("2025-26 home/road: league home wins == league road losses", hw == rl, f"home W {hw}, road L {rl}")
    chk("2025-26 home/road: league home losses == league road wins", hl == rw, f"home L {hl}, road W {rw}")
    chk("2025-26 home/road: neutral wins == neutral losses", nw == nl, f"{nw} vs {nl}")
    ts2526 = {r["team"]: r for r in ts if r["season"] == "2025-26"}
    chk("2025-26 home/road wins agree with team-season wins for all teams",
        all(int(r["home_w"]) + int(r["road_w"]) + int(r["neutral_w"]) == int(ts2526[r["team"]]["w"]) for r in hr))
    # game sample
    chk("game sample: 44 team-rows = 22 games", len(gs) == 44)
    byg = {}
    for r in gs:
        byg.setdefault(r["game_id"], []).append(r)
    chk("game sample: exactly two rows per game", all(len(v) == 2 for v in byg.values()))
    chk("game sample: PTS == 2*FGM + 3PM + FTM on every row",
        all(int(r["pts"]) == 2 * int(r["fgm"]) + int(r["fg3m"]) + int(r["ftm"]) for r in gs))
    ok_pm = ok_wl = ok_home = ok_min = True
    for v in byg.values():
        a, b = v
        ok_pm &= int(a["plus_minus"]) == int(a["pts"]) - int(b["pts"]) and int(b["plus_minus"]) == int(b["pts"]) - int(a["pts"])
        ok_wl &= {a["result"], b["result"]} == {"W", "L"} and (a["result"] == "W") == (int(a["pts"]) > int(b["pts"]))
        ok_home &= int(a["home"]) + int(b["home"]) == 1
        ok_min &= a["min"] == b["min"] and int(a["min"]) in (240, 265)
    chk("game sample: +/- equals point difference in both rows", ok_pm)
    chk("game sample: W/L consistent with score", ok_wl)
    chk("game sample: exactly one home team per game", ok_home)
    chk("game sample: minutes equal in both rows (240 reg., 265 = one OT)", ok_min)
    chk("game sample: every opp field mirrors the other row",
        all(v[0]["opp"] == v[1]["team"] and v[1]["opp"] == v[0]["team"] for v in byg.values()))
    # schedule
    chk("schedule: 14 games on 2026-11-04 and 2 on 2026-11-05 (matches nba.com day counts)",
        sum(r["date"] == "2026-11-04" for r in sched) == 14 and sum(r["date"] == "2026-11-05" for r in sched) == 2)
    teams = {r["team"] for r in ts}
    chk("schedule: all team codes valid", all(r["away"] in teams and r["home"] in teams for r in sched))
    chk("every data row carries an nba.com source URL",
        all("nba.com" in r["source_url"] for rows in (ts, hr, gs, sched) for r in rows))
    return out


# ----------------------------------------------------------------------- model
def season_map(ts, season):
    return {r["team"]: r for r in ts if r["season"] == season}


def total_of(r):
    """Points for + points against per game = 2*PTS - (+/-)."""
    return 2 * float(r["pts_pg"]) - float(r["plus_minus_pg"])


def league_total(rows):
    gp = sum(int(r["gp"]) for r in rows)
    return sum(int(r["gp"]) * total_of(r) for r in rows) / gp


def build_model(ts, hr, gs):
    s24, s25, s26 = (season_map(ts, s) for s in ("2024-25", "2025-26", "2026-27"))
    teams = sorted(s25)
    # ---- persistence (TRAIN pair: 2024-25 -> 2025-26 ; TEST pair: 2025-26 -> 2026-27 to date)
    x = [float(s24[t]["plus_minus_pg"]) for t in teams]
    y = [float(s25[t]["plus_minus_pg"]) for t in teams]
    fit_m = ols(x, y)
    lt24, lt25 = league_total(list(s24.values())), league_total(list(s25.values()))
    lt26 = league_total(list(s26.values()))
    dx = [total_of(s24[t]) - lt24 for t in teams]
    dy = [total_of(s25[t]) - lt25 for t in teams]
    fit_t = ols(dx, dy)
    # ---- home-court advantage from official 2025-26 home/road splits
    hw = sum(int(r["home_w"]) for r in hr)
    hl = sum(int(r["home_l"]) for r in hr)
    home_pct = hw / (hw + hl)
    # ---- game-level noise: sigma = RMSE of the prior-only margin model on the 22-game sample,
    # computed after HFA is added (so it includes rating error: conservative/upper bound)
    games = {}
    for r in gs:
        games.setdefault(r["game_id"], {})["home" if r["home"] == "1" else "away"] = r
    sig_guess = 12.0  # only used to convert home win% to points; replaced by sample sigma below
    hfa0 = sig_guess * ND.inv_cdf(home_pct)
    beta = fit_m["slope"]
    resid = []
    for g in games.values():
        h, a = g["home"], g["away"]
        pred = beta * (float(s25[h["team"]]["plus_minus_pg"]) - float(s25[a["team"]]["plus_minus_pg"])) + hfa0
        resid.append((int(h["pts"]) - int(a["pts"])) - pred)
    sigma = math.sqrt(mean(e * e for e in resid))
    hfa = sigma * ND.inv_cdf(home_pct)
    # Posterior weight on in-season margin: w = G/(G+K),  K = sigma^2 / tau_p^2
    # tau_p^2 = Var(resid of training regression) - sigma^2/82   (sampling noise of a full-season margin)
    tau_p2 = max(fit_m["resid_sd"] ** 2 - sigma ** 2 / 82.0, 1.0)
    K = sigma ** 2 / tau_p2
    # totals: noise = RMSE of the prior-only total model on the 22 games
    tresid = []
    for g in games.values():
        h, a = g["home"], g["away"]
        pt = lt25 + fit_t["slope"] * ((total_of(s25[h["team"]]) - lt25) + (total_of(s25[a["team"]]) - lt25)) / 1.0
        tresid.append((int(h["pts"]) + int(a["pts"])) - pt)
    sigma_t = math.sqrt(mean(e * e for e in tresid))
    tau_tp2 = max(fit_t["resid_sd"] ** 2 - sigma_t ** 2 / 82.0, 1.0)
    K_t = sigma_t ** 2 / tau_tp2
    return {
        "teams": teams, "s24": s24, "s25": s25, "s26": s26, "games": games,
        "fit_margin": fit_m, "fit_total": fit_t, "lt24": lt24, "lt25": lt25, "lt26": lt26,
        "home_w": hw, "home_l": hl, "home_pct": home_pct, "hfa0": hfa0, "hfa": hfa,
        "sigma": sigma, "tau_p2": tau_p2, "K": K, "sigma_t": sigma_t, "tau_tp2": tau_tp2, "K_t": K_t,
        "beta": beta, "beta_t": fit_t["slope"],
    }


def rating(M, team, K=None, beta=None):
    """Posterior team margin rating (points per game vs average team)."""
    K = M["K"] if K is None else K
    beta = M["beta"] if beta is None else beta
    cur = M["s26"][team]
    G = int(cur["gp"])
    prior = beta * float(M["s25"][team]["plus_minus_pg"])
    return (G * float(cur["plus_minus_pg"]) + K * prior) / (G + K)


def total_dev(M, team, K=None):
    K = M["K_t"] if K is None else K
    cur = M["s26"][team]
    G = int(cur["gp"])
    prior = M["beta_t"] * (total_of(M["s25"][team]) - M["lt25"])
    d_cur = total_of(cur) - M["lt26"]
    return (G * d_cur + K * prior) / (G + K)


def own_line(M, home, away, K=None, beta=None, K_t=None):
    sp = rating(M, home, K, beta) - rating(M, away, K, beta) + M["hfa"]  # expected home margin
    tot = M["lt26"] + total_dev(M, home, K_t) + total_dev(M, away, K_t)
    return sp, tot


def half(x):
    return round(x * 2) / 2


def lines(M, sched):
    rows = []
    for g in sched:
        h, a = g["home"], g["away"]
        sp, tot = own_line(M, h, a)
        lo = [own_line(M, h, a, K=k, beta=b)[0] for k in (M["K"] / 2, M["K"], M["K"] * 2) for b in (0.5, M["beta"], 1.0)]
        wp = ND.cdf(sp / M["sigma"])
        rows.append({
            "game_id": g["game_id"], "date": g["date"], "tip_et_24h": g["tip_et_24h"], "away": a, "home": h,
            "home_gp": M["s26"][h]["gp"], "away_gp": M["s26"][a]["gp"],
            "home_rating": round(rating(M, h), 2), "away_rating": round(rating(M, a), 2),
            "own_home_margin": round(sp, 1), "own_spread_home": f"{h} {-half(sp):+.1f}",
            "own_home_win_prob": round(wp, 3), "own_total": round(tot, 1), "own_total_rounded": half(tot),
            "sens_spread_min": round(min(lo), 1), "sens_spread_max": round(max(lo), 1),
            "market_spread": "", "market_total": "", "market_source": "BLANK - no verifiable official market quote (flag F03)",
            "source_url": g["source_url"],
        })
    return rows


# ---------------------------------------------------------------- walk-forward
def walk_forward(M):
    """Prior-only (2025-26 information) predictions of the 22 sampled 2026-27 games."""
    s25 = M["s25"]
    rows = []
    for gid, g in sorted(M["games"].items()):
        h, a = g["home"], g["away"]
        act_m = int(h["pts"]) - int(a["pts"])
        act_t = int(h["pts"]) + int(a["pts"])
        pm = M["beta"] * (float(s25[h["team"]]["plus_minus_pg"]) - float(s25[a["team"]]["plus_minus_pg"])) + M["hfa"]
        nm = M["hfa"]
        pt = M["lt25"] + M["beta_t"] * ((total_of(s25[h["team"]]) - M["lt25"]) + (total_of(s25[a["team"]]) - M["lt25"]))
        rows.append({"game_id": gid, "date": h["date"], "home": h["team"], "away": a["team"], "actual_margin": act_m,
                     "pred_margin": round(pm, 2), "naive_margin": round(nm, 2), "actual_total": act_t,
                     "pred_total": round(pt, 2), "naive_total": round(M["lt25"], 2),
                     "source_url": h["source_url"]})
    n = len(rows)

    def summ(pred_key, act_key):
        e = [r[pred_key] - r[act_key] for r in rows]
        return {"mae": mean(abs(v) for v in e), "rmse": math.sqrt(mean(v * v for v in e)), "bias": mean(e)}

    res = {"n": n}
    res["margin_model"] = summ("pred_margin", "actual_margin")
    res["margin_naive"] = summ("naive_margin", "actual_margin")
    res["total_model"] = summ("pred_total", "actual_total")
    res["total_naive"] = summ("naive_total", "actual_total")
    res["margin_su_model"] = sum((r["pred_margin"] > 0) == (r["actual_margin"] > 0) for r in rows)
    res["margin_su_naive"] = sum(r["actual_margin"] > 0 for r in rows)  # always pick home
    res["margin_corr"] = pearson([r["pred_margin"] for r in rows], [r["actual_margin"] for r in rows])
    res["total_corr"] = pearson([r["pred_total"] for r in rows], [r["actual_total"] for r in rows])
    for k in ("margin", "total"):
        d = [abs(r[f"naive_{k}"] - r[f"actual_{k}"]) - abs(r[f"pred_{k}"] - r[f"actual_{k}"]) for r in rows]
        res[f"{k}_abs_err_gain"] = {"mean": mean(d), "se": stdev(d) / math.sqrt(n)}
        res[f"{k}_abs_err_gain"]["z"] = res[f"{k}_abs_err_gain"]["mean"] / res[f"{k}_abs_err_gain"]["se"]
    res["actual_home_margin_mean"] = mean(r["actual_margin"] for r in rows)
    res["actual_home_margin_sd"] = stdev([r["actual_margin"] for r in rows])
    res["actual_total_mean"] = mean(r["actual_total"] for r in rows)
    # season-to-date team test (n=30): prior season margin vs 2026-27 margin to date
    teams = M["teams"]
    xs = [float(M["s25"][t]["plus_minus_pg"]) for t in teams]
    ys = [float(M["s26"][t]["plus_minus_pg"]) for t in teams]
    f = ols(xs, ys)
    lo, hi = fisher_ci(f["r"], 30)
    res["team_test"] = {"n": 30, "r": f["r"], "r_ci": [lo, hi], "slope": f["slope"], "slope_se": f["slope_se"],
                        "pred_rmse_beta": math.sqrt(mean((M["beta"] * x - y) ** 2 for x, y in zip(xs, ys))),
                        "pred_rmse_zero": math.sqrt(mean(y * y for y in ys)),
                        "pred_rmse_one": math.sqrt(mean((x - y) ** 2 for x, y in zip(xs, ys)))}
    return rows, res


# ---------------------------------------------------------------- correlations
def correlations(M, gs, wf_rows):
    out = {"team_season": [], "team_game": [], "game_level": [], "parlay": []}
    ts_all = []
    for s in ("2024-25", "2025-26", "2026-27"):
        m = M["s24"] if s == "2024-25" else M["s25"] if s == "2025-26" else M["s26"]
        rows = [m[t] for t in M["teams"]]
        gp = [int(r["gp"]) for r in rows]
        pm = [float(r["plus_minus_pg"]) for r in rows]
        wp = [int(r["w"]) / int(r["gp"]) for r in rows]
        pts = [float(r["pts_pg"]) for r in rows]
        opp = [p - q for p, q in zip(pts, pm)]
        for a, b, la, lb in ((pm, wp, "margin/G", "win%"), (pts, pm, "PTS/G", "margin/G"), (opp, pm, "opp PTS/G", "margin/G"), (pts, opp, "PTS/G", "opp PTS/G")):
            r = pearson(a, b)
            lo, hi = fisher_ci(r, 30)
            out["team_season"].append({"season": s, "x": la, "y": lb, "r": r, "ci_lo": lo, "ci_hi": hi, "n": 30})
    # persistence correlations
    for lab, fit in (("margin 2024-25 -> 2025-26", M["fit_margin"]), ("game total dev 2024-25 -> 2025-26", M["fit_total"])):
        lo, hi = fisher_ci(fit["r"], 30)
        out["team_season"].append({"season": "pair", "x": lab, "y": "", "r": fit["r"], "ci_lo": lo, "ci_hi": hi, "n": 30})
    # team-game (n=44)
    cols = {k: [float(r[k]) for r in gs] for k in ("pts", "fga", "fg3m", "fg3a", "fta", "oreb", "reb", "ast", "tov")}
    for k in ("fga", "fg3m", "fta", "ast", "tov", "oreb", "reb"):
        r = pearson(cols["pts"], cols[k])
        lo, hi = fisher_ci(r, len(gs))
        out["team_game"].append({"x": "team PTS", "y": {"fga": "FGA", "fg3m": "3PM", "fta": "FTA", "ast": "AST", "tov": "TOV", "oreb": "OREB", "reb": "REB"}[k], "r": r, "ci_lo": lo, "ci_hi": hi, "n": len(gs)})
    # game level (n=22): spread leg vs total leg
    am = [r["actual_margin"] - r["pred_margin"] for r in wf_rows]
    at = [r["actual_total"] - r["pred_total"] for r in wf_rows]
    r = pearson(am, at)
    lo, hi = fisher_ci(r, len(wf_rows))
    out["game_level"].append({"x": "spread-leg residual (actual home margin - model)", "y": "total-leg residual (actual total - model)", "r": r, "ci_lo": lo, "ci_hi": hi, "n": len(wf_rows)})
    r = pearson([r_["actual_margin"] for r_ in wf_rows], [r_["actual_total"] for r_ in wf_rows])
    lo, hi = fisher_ci(r, len(wf_rows))
    out["game_level"].append({"x": "actual home margin", "y": "actual game total", "r": r, "ci_lo": lo, "ci_hi": hi, "n": len(wf_rows)})
    # home vs away team points within game (two sides of same game)
    hp = [int(g["home"]["pts"]) for g in M["games"].values()]
    ap = [int(g["away"]["pts"]) for g in M["games"].values()]
    r = pearson(hp, ap)
    lo, hi = fisher_ci(r, len(hp))
    out["game_level"].append({"x": "home team PTS", "y": "away team PTS (same game)", "r": r, "ci_lo": lo, "ci_hi": hi, "n": len(hp)})
    # parlay arithmetic (pure maths)
    for p, q in ((0.5, 0.5), (0.55, 0.55)):
        for phi in (-0.2, -0.1, 0.0, 0.1, 0.2, 0.3):
            joint = p * q + phi * math.sqrt(p * (1 - p) * q * (1 - q))
            if 0 < joint < min(p, q):
                out["parlay"].append({"p_leg1": p, "p_leg2": q, "phi": phi, "joint": joint, "independent": p * q, "ratio": joint / (p * q)})
    return out


# ------------------------------------------------------------ luck vs skill
def binom_pmf(n, p):
    lp, lq = math.log(p), math.log(1 - p)
    return [math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * lp + (n - k) * lq) for k in range(n + 1)]


def binom_sf(n, k, p):
    """P(X >= k)."""
    return sum(binom_pmf(n, p)[max(k, 0):])


def required_n(p_true, p0, alpha=0.05, power=0.8, nmax=12000):
    """Smallest n (searched in steps of 1 up to 200, then 5) such that the exact one-sided
    binomial test of H0: p=p0 at level alpha has power >= `power` when the true rate is p_true."""
    n = 20
    while n <= nmax:
        pm0 = binom_pmf(n, p0)
        acc, k = 0.0, n + 1
        while k > 0 and acc + pm0[k - 1] <= alpha:
            acc += pm0[k - 1]
            k -= 1
        if k <= n:
            pw = sum(binom_pmf(n, p_true)[k:])
            if pw >= power:
                return n, k
        n += 1 if n < 200 else 5
    return None, None


def luck_skill():
    be = 110 / 210  # break-even hit rate at -110 odds (pure arithmetic)
    out = {"breakeven_110": be, "single_bettor": [], "leaderboard_luck": [], "required_n": []}
    for n in (50, 100, 250, 500, 1000, 2500):
        k55 = math.ceil(0.55 * n)
        kbe = math.ceil(be * n)
        out["single_bettor"].append({
            "n": n,
            "p_fair_coin_ge_55pct": binom_sf(n, k55, 0.5),
            "p_fair_coin_ge_breakeven": binom_sf(n, kbe, 0.5),
            "p_true55_ge_breakeven": binom_sf(n, kbe, 0.55),
        })
    for M in (10, 50, 100, 500):
        for n in (50, 100, 250, 1000):
            pmf = binom_pmf(n, 0.5)
            cdf, c = [], 0.0
            for v in pmf:
                c += v
                cdf.append(c)
            emax = sum(k * (cdf[k] ** M - (cdf[k - 1] ** M if k else 0.0)) for k in range(n + 1))
            k60 = math.ceil(0.6 * n)
            out["leaderboard_luck"].append({"entrants": M, "bets_each": n, "expected_best_hit_rate": emax / n,
                                            "p_any_ge_60pct": 1 - (cdf[k60 - 1] ** M)})
    for ptrue in (0.54, 0.55, 0.56, 0.58):
        n, k = required_n(ptrue, be)
        out["required_n"].append({"true_hit_rate": ptrue, "n_bets": n, "k_critical": k})
    return out


# -------------------------------------------------------- strategies / gates
GATES = [
    ("G1", "Source integrity", "Every input row links to an official page and reconciles to league identities (this session's integrity suite).", "Automatable now"),
    ("G2", "Pre-registration", "Rule, parameters and data cut-off frozen and timestamped BEFORE games start; edits create a new strategy ID.", "Automatable now"),
    ("G3", "Minimum sample", "At least N settled, pre-registered bets where N gives 80% power at one-sided 5% vs the break-even hit rate for the claimed edge (see Luck vs Skill).", "Needs settled ledger"),
    ("G4", "Closing-line value", "Mean CLV > 0 with a lower 95% bound above 0 over the sample. Needs timestamped market quotes and a closing line from an auditable source.", "Blocked: no official market feed in scope"),
    ("G5", "Multiple-testing deflation", "p-value must clear Bonferroni threshold alpha / (number of strategies and parameter variants ever tried).", "Needs settled ledger"),
    ("G6", "Out-of-sample holdout", "Positive edge on data never used to choose parameters (this desk: all parameters fitted on 2024-25 -> 2025-26, tested on 2026-27).", "Partially met (n=22 games, underpowered)"),
    ("G7", "Calibration", "Model probabilities beat the naive baseline on log-loss / Brier on the holdout.", "Needs settled ledger"),
    ("G8", "Correlation discipline (parlays/props)", "Any multi-leg ticket must use a measured joint probability, not a product of independent legs; legs with unmeasured correlation are rejected.", "Partially met (see Correlations)"),
    ("G9", "Risk of ruin", "Stake sizing rule fixed in advance; simulated max drawdown under the claimed edge within limit.", "Needs settled ledger"),
]

STRATEGIES = [
    ("S1", "Single - spread edge", "Single", "Back the side whose own spread differs from the market by at least a pre-set threshold.", "Own spread (model)", "Official market spread + timestamp"),
    ("S2", "Single - total edge", "Single", "Over/under when own total differs from market total by at least a pre-set threshold.", "Own total (model)", "Official market total + timestamp"),
    ("S3", "Single - moneyline value", "Single", "Back a side when own win probability exceeds the de-vigged market probability by a threshold.", "Own win probability (Phi(spread/sigma))", "Official moneyline + timestamp"),
    ("S4", "Parlay - two independent game edges", "Parlay", "Combine two single edges from different games; ticket price must use measured joint probability.", "S1/S2/S3 signals", "Market prices for both legs; cross-game correlation estimate"),
    ("S5", "Parlay - same-game spread + total", "Parlay (SGP)", "Only if own spread and total edges agree AND measured leg correlation is not adverse.", "S1 + S2", "SGP pricing (not published by an official source)"),
    ("S6", "Player-prop combo", "Prop combo", "Combine props whose measured same-game correlation is positive and whose price does not already embed it.", "Player-level projections (not built)", "Player prop lines + player game logs at scale"),
]


def strategy_status(wf):
    rows = []
    for sid, name, typ, rule, signal, need in STRATEGIES:
        blocked = "Blocked - " + need
        rows.append({"id": sid, "name": name, "type": typ, "rule": rule, "signal": signal, "missing_input": need,
                     "bets_settled": 0, "gates_passed": "G1,G2 only (rule frozen; sources verified)",
                     "status": "NOT QUALIFIED (fails closed)", "reason": blocked, "reward": "none awarded"})
    return rows


# --------------------------------------------------------------------- driver
def main():
    ts, hr, gs, sched = (read(f) for f in ("team_seasons.csv", "home_road_2025_26.csv", "games_sample_2026_27.csv", "schedule_2026_11_04_05.csv"))
    integ = integrity(ts, hr, gs, sched)
    M = build_model(ts, hr, gs)
    L = lines(M, sched)
    wf_rows, wf = walk_forward(M)
    corr = correlations(M, gs, wf_rows)
    ls = luck_skill()
    ratings = []
    for t in M["teams"]:
        ratings.append({"team": t, "gp": M["s26"][t]["gp"], "w": M["s26"][t]["w"], "l": M["s26"][t]["l"],
                        "pm_2024_25": M["s24"][t]["plus_minus_pg"], "pm_2025_26": M["s25"][t]["plus_minus_pg"],
                        "pm_2026_27_to_date": M["s26"][t]["plus_minus_pg"],
                        "prior": round(M["beta"] * float(M["s25"][t]["plus_minus_pg"]), 2),
                        "weight_on_current": round(int(M["s26"][t]["gp"]) / (int(M["s26"][t]["gp"]) + M["K"]), 3),
                        "rating": round(rating(M, t), 2)})
    ratings.sort(key=lambda r: -r["rating"])
    params = {k: M[k] for k in ("beta", "beta_t", "hfa", "hfa0", "home_w", "home_l", "home_pct", "sigma", "tau_p2", "K", "sigma_t", "tau_tp2", "K_t", "lt24", "lt25", "lt26")}
    params["fit_margin"] = M["fit_margin"]
    params["fit_total"] = M["fit_total"]
    result = {"as_of": AS_OF, "integrity": integ, "params": params, "ratings": ratings, "walk_forward": wf,
              "correlations": corr, "luck_skill": ls, "gates": [dict(zip(("id", "name", "rule", "status"), g)) for g in GATES],
              "strategies": strategy_status(wf), "n_lines": len(L)}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "analysis.json"), "w") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    for name, rows in (("lines_2026_11_04_05.csv", L), ("walk_forward_22_games.csv", wf_rows), ("ratings_2026_11_03.csv", ratings)):
        with open(os.path.join(OUT, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    bad = [c for c in integ if not c["passed"]]
    print(f"integrity: {len(integ) - len(bad)}/{len(integ)} passed")
    for c in bad:
        print("  FAIL", c["check"], c["detail"])
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

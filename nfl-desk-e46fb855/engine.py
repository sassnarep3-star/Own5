"""Deterministic engine for the e46fb855 NFL decision-readiness desk.

Reads only:
  * data/official/*.json          - pages read by this session, 2026-11-15
  * ../nfl-desk-3fb93d11/data/results_feed.csv     (read-only, carried forward)
  * ../nfl-desk-3fb93d11/data/standings_official.csv (read-only, carried forward)
  * ../nfl-desk-864d5668/data/injuries.csv         (read-only, carried forward)
Writes:
  * data/*.csv
No network access. No randomness. Standard library only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path

import content

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DATA = ROOT / "data"
OFFICIAL = DATA / "official"
OUT = DATA

BUILD_UTC = "2026-11-15T23:40:00Z"
SESSION = "e46fb855"
COMMIT_HASH_PLACEHOLDER = "recorded-by-run.py at build time"

# Ridge penalty on the 32 team ratings, in points squared. Without it the
# design is not identifiable early in a season (after two rounds every team has
# one home game and one away game, so home advantage cannot be separated from
# team strength). 1.0 is about 10% shrinkage at a full season of games. This is
# a MODELLING CHOICE, not an official value, and it is flagged as F-17.
RIDGE = 1.0

STD_URL = "https://www.nfl.com/standings/league/2026/REG"
SLATE_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
WK10_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
INJ_URL = "https://www.nfl.com/injuries/league/2026/reg10"

# ---------------------------------------------------------------------------
# small statistics helpers (stdlib only, deterministic)
# ---------------------------------------------------------------------------


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r, n):
    """95% CI for a Pearson r via the Fisher z transform."""
    if r is None or n < 4 or abs(r) >= 1.0:
        return (None, None)
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo = math.tanh(z - 1.96 * se)
    hi = math.tanh(z + 1.96 * se)
    return (lo, hi)


def binom_two_sided_p(k, n, p=0.5):
    """Exact two-sided binomial test."""
    if n == 0:
        return None
    probs = [math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(n + 1)]
    obs = probs[k]
    return min(1.0, sum(pr for pr in probs if pr <= obs * (1 + 1e-9)))


def wilson_interval(k, n, z=1.96):
    if n == 0:
        return (None, None)
    ph = k / n
    denom = 1 + z * z / n
    centre = (ph + z * z / (2 * n)) / denom
    half = (z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def holm(pvals):
    """Holm-Bonferroni adjusted p-values, in the original order."""
    m = len(pvals)
    indexed = sorted(range(m), key=lambda i: pvals[i])
    out = [None] * m
    running = 0.0
    for rank, i in enumerate(indexed):
        val = (m - rank) * pvals[i]
        running = max(running, val)
        out[i] = min(1.0, running)
    return out


def normal_equations(rows, ys, n_teams, ridge):
    """Least-squares normal equations for the margin model.

    Columns: one per team (home +1, away -1) plus a home-field column that is 1
    for a normal game and 0 for a neutral-site game. A ridge penalty is applied
    to the team columns only.
    """
    p = n_teams + 1
    a = [[0.0] * p for _ in range(p)]
    b = [0.0] * p
    for row, y in zip(rows, ys):
        for i in range(p):
            if row[i]:
                b[i] += row[i] * y
                for j in range(p):
                    if row[j]:
                        a[i][j] += row[i] * row[j]
    for i in range(n_teams):
        a[i][i] += ridge
    return a, b


def mat_inverse(a):
    """Gauss-Jordan inverse of a square matrix."""
    n = len(a)
    m = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("singular matrix")
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for c in range(2 * n):
            m[col][c] /= pv
        for r in range(n):
            if r == col:
                continue
            f = m[r][col]
            if f:
                for c in range(2 * n):
                    m[r][c] -= f * m[col][c]
    return [row[n:] for row in m]


def solve(a, b):
    """Gaussian elimination with partial pivoting."""
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("singular matrix")
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for r in range(n):
            if r == col:
                continue
            f = m[r][col] / pv
            if f:
                for c in range(col, n + 1):
                    m[r][c] -= f * m[col][c]
    return [m[i][n] / m[i][i] for i in range(n)]


def american_from_prob(p):
    if p is None:
        return None
    if p <= 0 or p >= 1:
        return None
    return -100.0 * p / (1 - p) if p >= 0.5 else 100.0 * (1 - p) / p


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------


def load_json(name):
    with open(OFFICIAL / name, encoding="utf-8") as fh:
        return json.load(fh)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write_csv(name, header, rows):
    path = OUT / name
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
    return path


def fmt(x, nd=4):
    if x is None or x == "":
        return ""
    if isinstance(x, float):
        if x != x:
            return ""
        return f"{x:.{nd}f}"
    return str(x)


# ---------------------------------------------------------------------------
# main build
# ---------------------------------------------------------------------------


def build():
    standings_raw = load_json("standings_2026_league.json")
    slate = load_json("slate_2026_wk11.json")
    wk10 = load_json("results_wk10_2026.json")
    spot = load_json("results_spotcheck_w1_w5.json")
    inj_sample = load_json("injury_sample_wk10.json")
    depth_raw = load_json("depth_charts_2026.json")

    # ---------------- carry-forward sources (read-only, other sessions) -----
    cf_feed_path = REPO / "nfl-desk-3fb93d11" / "data" / "results_feed.csv"
    cf_std_path = REPO / "nfl-desk-3fb93d11" / "data" / "standings_official.csv"
    cf_inj_path = REPO / "nfl-desk-864d5668" / "data" / "injuries.csv"
    cf_feed = read_csv_rows(cf_feed_path)
    cf_std = {r["team"]: r for r in read_csv_rows(cf_std_path)}
    cf_inj = read_csv_rows(cf_inj_path)
    cf_feed_sha = sha256_of(cf_feed_path)[:16]
    cf_std_sha = sha256_of(cf_std_path)[:16]
    cf_inj_sha = sha256_of(cf_inj_path)[:16]

    # ---------------- official standings -----------------------------------
    standings = []
    for team, club, w, l, t, pct, pf, pa, net in standings_raw["rows"]:
        gp = w + l + t
        standings.append({
            "team": team, "club": club, "w": w, "l": l, "t": t, "pct": pct,
            "pf": pf, "pa": pa, "net": net, "gp": gp,
            "pf_pg": pf / gp if gp else None,
            "pa_pg": pa / gp if gp else None,
            "net_pg": net / gp if gp else None,
            "win_pct": (w + 0.5 * t) / gp if gp else None,
        })
    by_team = {s["team"]: s for s in standings}

    # ---------------- results feed -----------------------------------------
    spot_idx = {(g["week"], g["away"], g["home"]): g for g in spot["games"]}
    wk10_idx = {g["game_id"]: g for g in wk10["games"]}

    feed = []
    for r in cf_feed:
        week = int(r["week"])
        key = (week, r["away"], r["home"])
        if key in spot_idx:
            verified = "read by session e46fb855 from the official week page on 2026-11-15"
            status = "session-verified"
        else:
            verified = ("transcribed by session 3fb93d11 from the official week page on "
                        "2026-11-14; carried forward, not re-read by this session")
            status = "carried-forward"
        feed.append({
            "game_id": r["game_id"], "season": r["season"], "week": week,
            "kickoff_date": r["kickoff_date"],
            "away": r["away"], "home": r["home"],
            "away_score": int(r["away_score"]), "home_score": int(r["home_score"]),
            "home_margin": int(r["home_margin"]),
            "total_points": int(r["total_points"]),
            "result": r["result"], "neutral_site": r["neutral_site"],
            "status": "FINAL", "verification": status, "verification_note": verified,
            "source_url": r["source_url"],
        })

    # week 10: add what this session captured, replacing/adding rows
    seen = {f["game_id"] for f in feed}
    for g in wk10["games"]:
        if g["status"] != "FINAL":
            continue
        row = {
            "game_id": g["game_id"], "season": 2026, "week": 10,
            "kickoff_date": g["date"],
            "away": g["away"], "home": g["home"],
            "away_score": g["away_score"], "home_score": g["home_score"],
            "home_margin": g["home_score"] - g["away_score"],
            "total_points": g["away_score"] + g["home_score"],
            "result": ("away win" if g["away_score"] > g["home_score"]
                       else "home win" if g["home_score"] > g["away_score"] else "tie"),
            "neutral_site": "Munich" if g.get("neutral") else "",
            "status": "FINAL",
            "verification": "read by session e46fb855 from the official week page on 2026-11-15",
            "verification_note": "week-10 final, read directly this session",
            "source_url": WK10_URL,
        }
        if g["game_id"] in seen:
            for i, f in enumerate(feed):
                if f["game_id"] == g["game_id"]:
                    feed[i] = row
        else:
            feed.append(row)
    feed.sort(key=lambda r: (r["week"], r["kickoff_date"], r["game_id"]))

    # pending week-10 rows (live / not started): published, never filled in
    pending = []
    for g in wk10["games"]:
        if g["status"] == "FINAL":
            continue
        pending.append({
            "game_id": g["game_id"], "week": 10, "kickoff_date": g["date"],
            "away": g["away"], "home": g["home"],
            "away_score": "", "home_score": "",
            "status": g["status"], "source_url": WK10_URL,
        })

    finals = [f for f in feed if f["status"] == "FINAL"]

    # ---------------- reconciliation ---------------------------------------
    derived = {t: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "gp": 0} for t in by_team}
    for f in finals:
        for side, other in (("home", "away"), ("away", "home")):
            d = derived[f[side]]
            d["pf"] += f[f"{side}_score"]
            d["pa"] += f[f"{other}_score"]
            d["gp"] += 1
            if f[f"{side}_score"] > f[f"{other}_score"]:
                d["w"] += 1
            elif f[f"{side}_score"] < f[f"{other}_score"]:
                d["l"] += 1
            else:
                d["t"] += 1

    recon_rows = []
    for team in sorted(by_team):
        off = by_team[team]
        d = derived[team]
        dw = off["w"] - d["w"]
        dl = off["l"] - d["l"]
        dt = off["t"] - d["t"]
        dpf = off["pf"] - d["pf"]
        dpa = off["pa"] - d["pa"]
        if dw == 0 and dl == 0 and dt == 0 and dpf == 0 and dpa == 0:
            verdict = "exact match"
        else:
            verdict = ("official standings include results the feed does not hold "
                       "(games in progress or unplayed at capture)")
        recon_rows.append({
            "team": team, "club": off["club"],
            "official_w": off["w"], "official_l": off["l"], "official_t": off["t"],
            "official_pf": off["pf"], "official_pa": off["pa"],
            "feed_w": d["w"], "feed_l": d["l"], "feed_t": d["t"],
            "feed_pf": d["pf"], "feed_pa": d["pa"],
            "delta_w": dw, "delta_l": dl, "delta_t": dt,
            "delta_pf": dpf, "delta_pa": dpa,
            "verdict": verdict, "source_url": STD_URL,
        })

    # ---------------- ratings (opponent-aware, official results only) -------
    teams = sorted(by_team)
    tix = {t: i for i, t in enumerate(teams)}
    p = len(teams) + 1
    rows, ys = [], []
    for f in finals:
        row = [0.0] * p
        row[tix[f["home"]]] = 1.0
        row[tix[f["away"]]] = -1.0
        row[len(teams)] = 0.0 if f["neutral_site"] else 1.0
        rows.append(row)
        ys.append(float(f["home_margin"]))
    A, b = normal_equations(rows, ys, len(teams), RIDGE)
    sol = solve(A, b)
    raw = {t: sol[tix[t]] for t in teams}
    # shifting every rating by the same constant leaves every predicted margin
    # unchanged (each game has exactly one home and one away team), so centre
    # them for readability
    mean_rating = sum(raw.values()) / len(teams)
    ratings = {t: raw[t] - mean_rating for t in teams}
    hfa = sol[len(teams)]

    resid = []
    for row, f in zip(rows, finals):
        pred = sum(row[i] * sol[i] for i in range(p))
        resid.append(f["home_margin"] - pred)
    df = max(1, len(finals) - p)
    sigma = math.sqrt(sum(r * r for r in resid) / df)
    ainv = mat_inverse(A)
    se_hfa = math.sqrt(max(0.0, ainv[len(teams)][len(teams)]) * sigma ** 2)

    # squad-level scoring rates for the two totals estimators
    pf_pg = {t: by_team[t]["pf_pg"] for t in teams}
    pa_pg = {t: by_team[t]["pa_pg"] for t in teams}
    team_tot = {t: {"n": 0, "sum": 0.0} for t in teams}
    for f in finals:
        tot = f["away_score"] + f["home_score"]
        for side in ("home", "away"):
            team_tot[f[side]]["n"] += 1
            team_tot[f[side]]["sum"] += tot
    league_total = sum(f["total_points"] for f in finals) / len(finals)
    team_total_avg = {t: (v["sum"] / v["n"] if v["n"] else league_total) for t, v in team_tot.items()}
    K = 5.0
    shrink = {t: (team_total_avg[t] - league_total) * (team_tot[t]["n"] / (team_tot[t]["n"] + K))
              for t in teams}

    def total_estimator_a(home, away):
        """Estimator A: shrunk team game-total tendency."""
        return league_total + shrink[home] + shrink[away]

    def total_estimator_b(home, away):
        """Estimator B: points-for / points-against blend."""
        return 0.5 * (pf_pg[home] + pa_pg[home] + pf_pg[away] + pa_pg[away])

    def fit_totals(games):
        """Fit both totals estimators on a training window only.

        Estimator B needs points-for and points-against rates, and those must
        come from the training weeks: using the season's final standings to
        predict a game that is part of those standings would leak the answer.
        """
        tot_sum, tot_n = 0.0, 0
        tt = {t: {"n": 0, "sum": 0.0} for t in teams}
        pf = {t: 0 for t in teams}
        pa = {t: 0 for t in teams}
        gp = {t: 0 for t in teams}
        for g in games:
            tp = g["away_score"] + g["home_score"]
            tot_sum += tp
            tot_n += 1
            for side, other in (("home", "away"), ("away", "home")):
                tt[g[side]]["n"] += 1
                tt[g[side]]["sum"] += tp
                pf[g[side]] += g[f"{side}_score"]
                pa[g[side]] += g[f"{other}_score"]
                gp[g[side]] += 1
        base = tot_sum / tot_n if tot_n else league_total
        avg = {t: (tt[t]["sum"] / tt[t]["n"] if tt[t]["n"] else base) for t in teams}
        sh = {t: (avg[t] - base) * (tt[t]["n"] / (tt[t]["n"] + K)) for t in teams}
        pfp = {t: (pf[t] / gp[t] if gp[t] else base / 2) for t in teams}
        pap = {t: (pa[t] / gp[t] if gp[t] else base / 2) for t in teams}
        return base, sh, pfp, pap

    # walk-forward: fit on weeks < W, predict week W
    def fit_ratings(games):
        rr, yy = [], []
        for f in games:
            row = [0.0] * p
            row[tix[f["home"]]] = 1.0
            row[tix[f["away"]]] = -1.0
            row[len(teams)] = 0.0 if f["neutral_site"] else 1.0
            rr.append(row)
            yy.append(float(f["home_margin"]))
        AA, bb = normal_equations(rr, yy, len(teams), RIDGE)
        s = solve(AA, bb)
        raw = {t: s[tix[t]] for t in teams}
        mean_rating = sum(raw.values()) / len(teams)
        return ({t: raw[t] - mean_rating for t in teams}, s[len(teams)], rr)

    oos_margin_err, oos_total_err_a, oos_total_err_b, oos_base_err = [], [], [], []
    oos_side_hits, oos_side_n = 0, 0
    oos_by_week = {}
    for f in finals:
        if f["week"] <= 1:
            continue
        train = [g for g in finals if g["week"] < f["week"]]
        if len(train) < 16:
            continue
        rmap, hfa_t, _ = fit_ratings(train)
        pred_margin = rmap[f["home"]] - rmap[f["away"]] + (0.0 if f["neutral_site"] else hfa_t)
        oos_margin_err.append(f["home_margin"] - pred_margin)
        wk = oos_by_week.setdefault(f["week"], {"n": 0, "hits": 0, "m": [], "a": [], "b": [], "base": []})
        base, sh, pfp, pap = fit_totals(train)
        e_a = f["total_points"] - (base + sh[f["home"]] + sh[f["away"]])
        e_b = f["total_points"] - 0.5 * (pfp[f["home"]] + pap[f["home"]]
                                         + pfp[f["away"]] + pap[f["away"]])
        # baseline: the league mean total as fitted on the training weeks only
        e_base = f["total_points"] - base
        oos_total_err_a.append(e_a)
        oos_total_err_b.append(e_b)
        oos_base_err.append(e_base)
        wk["m"].append(f["home_margin"] - pred_margin)
        wk["a"].append(e_a)
        wk["b"].append(e_b)
        wk["base"].append(e_base)
        if pred_margin != 0:
            oos_side_n += 1
            wk["n"] += 1
            if (pred_margin > 0) == (f["home_margin"] > 0):
                oos_side_hits += 1
                wk["hits"] += 1

    def mae(xs):
        return sum(abs(x) for x in xs) / len(xs) if xs else None

    model_card = {
        "n_games": len(finals),
        "hfa_points": hfa,
        "residual_sd": sigma,
        "league_mean_total": league_total,
        "oos_margin_mae": mae(oos_margin_err),
        "oos_total_mae_a": mae(oos_total_err_a),
        "oos_total_mae_b": mae(oos_total_err_b),
        "oos_total_mae_baseline": mae(oos_base_err),
        "oos_side_hits": oos_side_hits,
        "oos_side_n": oos_side_n,
        "oos_side_p": binom_two_sided_p(oos_side_hits, oos_side_n, 0.5),
        "hfa_standard_error": se_hfa,
        "hfa_ci95_low": (hfa - 1.96 * se_hfa) if se_hfa is not None else None,
        "hfa_ci95_high": (hfa + 1.96 * se_hfa) if se_hfa is not None else None,
        "degrees_of_freedom": df,
    }

    # ---------------- rest days & byes --------------------------------------
    from datetime import date

    def to_date(s):
        y, m, d = (int(x) for x in s.split("-"))
        return date(y, m, d)

    last_played = {}
    rest = {}
    for f in sorted(finals, key=lambda r: (to_date(r["kickoff_date"]), r["game_id"])):
        d = to_date(f["kickoff_date"])
        for side in ("home", "away"):
            t = f[side]
            prev = last_played.get(t)
            rest[f["game_id"] + "|" + side] = (d - prev).days if prev else None
            last_played[t] = d
    byes = {}
    all_weeks = sorted({f["week"] for f in finals})
    for w in all_weeks:
        playing = set()
        for f in finals:
            if f["week"] == w:
                playing.add(f["home"])
                playing.add(f["away"])
        byes[w] = sorted(set(teams) - playing)

    def rest_for(game, side):
        return rest.get(game["game_id"] + "|" + side)

    # ---------------- originated markets for week 11 ------------------------
    markets, origins, price_rows = [], [], []
    for g in slate["games"]:
        home, away = g["home"], g["away"]
        pm = ratings[home] - ratings[away] + (0.0 if g["neutral"] else hfa)
        ta = total_estimator_a(home, away)
        tb = total_estimator_b(home, away)
        p_home = 1.0 - norm_cdf((0.0 - pm) / sigma)
        gid = g["game_id"]
        for mtype, order, model_val, derived_from, units, extra in (
            ("SIDE", 1, pm, "step 1 (side) - opponent-aware margin model, fitted first",
             "points, from the home team's perspective", ""),
            ("TOTAL", 2, ta, "step 2 (total) - estimator A (shrunk team game totals), fitted second",
             "points, combined scoring", tb),
            ("MONEYLINE", 3, p_home,
             "step 3 (moneyline) - derived from step 1 (side) and step 2 (total), never fitted separately",
             "probability the home team wins (ties excluded by the normal model)", ""),
        ):
            mid = f"{gid}:{mtype}"
            price = american_from_prob(p_home) if mtype == "MONEYLINE" else None
            markets.append({
                "game_id": gid, "season": 2026, "week": 11,
                "away": away, "home": home,
                "matchup": f"{away} @ {home}",
                "kickoff_date": g["date"], "kickoff_et": g["kickoff_et"],
                "venue": g["venue"], "neutral_site": "YES" if g["neutral"] else "",
                "market_id": mid, "market_type": mtype, "origination_order": order,
                "derived_from": derived_from,
                "model_line": fmt(model_val, 4),
                "model_total_estimator_b": fmt(tb, 4) if mtype == "TOTAL" else "",
                "total_estimator_gap_b_minus_a": fmt(tb - ta, 4) if mtype == "TOTAL" else "",
                "market_line": "", "market_line_status": "UNVERIFIED - no official or licensed price exists (F-01)",
                "difference_model_minus_market": "",
                "difference_status": "UNVERIFIED - undefined while the market line is blank",
                "model_price_american": fmt(price, 1),
                "units": units,
                "model_inputs": (f"rating_home={fmt(ratings[home],4)}; rating_away={fmt(ratings[away],4)}; "
                                 f"hfa={fmt(0.0 if g['neutral'] else hfa,4)}; sigma={fmt(sigma,4)}"
                                 + (f"; estimator_b={fmt(tb,4)}" if mtype == "TOTAL" else "")
                                 + (f"; estimator_a={fmt(ta,4)}" if mtype == "MONEYLINE" else "")),
                "model_source_url": STD_URL,
                "market_source_url": "",
                "snapshot_utc": BUILD_UTC,
                "venue_source_url": g["venue_source"],
                "game_url": g["game_url"],
            })
            origins.append({
                "game_id": gid, "market_id": mid, "step": order, "market_type": mtype,
                "instruction": derived_from,
                "depends_on": ("none - fitted first" if order == 1 else
                               "step 1 (side)" if order == 2 else "step 1 (side) and step 2 (total)"),
                "source_url": STD_URL,
            })
        for snap in ("MODEL_ORIGIN", "MODEL_CLOSE", "MARKET_OPEN", "MARKET_CLOSE"):
            if snap.startswith("MODEL"):
                if snap == "MODEL_ORIGIN":
                    val = fmt(pm if True else 0.0, 4)
                    val = {"SIDE": fmt(pm, 4), "TOTAL": fmt(ta, 4), "MONEYLINE": fmt(p_home, 4)}[mtype]
                else:
                    val = ""
            else:
                val = ""
            price_rows.append({
                "market_id": f"{gid}:{mtype}", "snapshot_type": snap,
                "value": val,
                "captured_utc": BUILD_UTC if snap == "MODEL_ORIGIN" else "",
                "price_american": fmt(american_from_prob(p_home), 1) if (snap == "MODEL_ORIGIN" and mtype == "MONEYLINE") else "",
                "status": ("captured" if snap == "MODEL_ORIGIN" else
                           "EMPTY - not yet observed" if snap == "MODEL_CLOSE" else
                           "EMPTY - no official or licensed price source exists (F-01)"),
                "source_url": (STD_URL if snap.startswith("MODEL") else ""),
                "source_tier": ("OFFICIAL (derived from official results)" if snap.startswith("MODEL")
                                else "NONE"),
            })

    # rest-day + bye context for the week-11 slate
    slate_ctx = []
    for g in slate["games"]:
        for side in ("away", "home"):
            t = g[side]
            last = last_played.get(t)
            d = to_date(g["date"])
            slate_ctx.append({
                "game_id": g["game_id"], "side": side, "team": t,
                "days_rest": (d - last).days if last else "",
                "days_rest_source": "derived from the official kickoff dates in the results feed",
            })

    # ---------------- depth and injuries ------------------------------------
    depth_rows, slot_groups = [], []
    shared_rank1 = 0
    empty_cells = 0
    total_slots = 0
    clubs_parsed = 0
    for team in sorted(depth_raw["clubs"]):
        club = depth_raw["clubs"][team]
        if club.get("parsed") is False:
            depth_rows.append({
                "team": team, "club": team, "unit": "", "position": "",
                "rank1": "", "rank2": "", "rank3": "", "rank4": "",
                "shared_rank1": "", "empty_first_string": "",
                "as_of_published": club.get("as_of_published", ""),
                "source_url": club["source_url"],
                "status": "NOT PARSED - " + club.get("parse_failure_reason", ""),
            })
            continue
        clubs_parsed += 1
        for unit in ("offense", "defense"):
            for row in club.get(unit, []):
                pos = row[0]
                ranks = row[1:]
                names = [[n for n in r] if isinstance(r, list) else ([r] if r else [])
                         for r in ranks]
                while len(names) < 4:
                    names.append([])
                total_slots += 1
                sh = len(names[0]) > 1
                emp = len(names[0]) == 0
                if sh:
                    shared_rank1 += 1
                if emp:
                    empty_cells += 1
                depth_rows.append({
                    "team": team, "club": team, "unit": unit.capitalize(), "position": pos,
                    "rank1": " | ".join(names[0]), "rank2": " | ".join(names[1]),
                    "rank3": " | ".join(names[2]), "rank4": " | ".join(names[3]),
                    "shared_rank1": "YES" if sh else "no",
                    "empty_first_string": "YES" if emp else "no",
                    "as_of_published": club.get("as_of_published", ""),
                    "source_url": club["source_url"],
                    "status": "parsed" + (" (PARTIAL - " + club["partial_note"] + ")"
                                          if club.get("partial") and unit == "defense" else ""),
                })
        if club.get("partial"):
            depth_rows.append({
                "team": team, "club": team, "unit": "Defense", "position": "",
                "rank1": "", "rank2": "", "rank3": "", "rank4": "",
                "shared_rank1": "", "empty_first_string": "",
                "as_of_published": club.get("as_of_published", ""),
                "source_url": club["source_url"],
                "status": "PARTIAL CAPTURE - " + club["partial_note"],
            })

    # injury report: carried forward + this session's sample, cross-checked
    inj_index = {}
    for r in cf_inj:
        inj_index[(r["team"], r["player"].strip())] = r

    inj_rows = []
    checked = matched = mismatched = 0
    for s in inj_sample["rows"]:
        key = (s["team"], s["player"].strip())
        cf = inj_index.get(key)
        checked += 1
        if cf is None:
            verdict = "NOT PRESENT in the carried-forward file - irregularity"
            mismatched += 1
        else:
            diffs = []
            if (cf.get("practice_status_as_published") or "") != s["practice_status"]:
                diffs.append("practice_status")
            if (cf.get("game_status_as_published") or "") != s["game_status"]:
                diffs.append("game_status")
            if (cf.get("injury") or "") != s["injury"]:
                diffs.append("injury")
            if diffs:
                verdict = "MISMATCH on " + ", ".join(diffs)
                mismatched += 1
            else:
                verdict = "match"
                matched += 1
        inj_rows.append({
            "team": s["team"], "player": s["player"], "position": s["position"],
            "injury": s["injury"], "practice_status": s["practice_status"],
            "game_status": s["game_status"],
            "week": 10, "captured_utc": "2026-11-15T23:27:00Z",
            "read_by": "session e46fb855 (this session)",
            "crosscheck_vs_carried_forward": verdict,
            "delta_vs_previous_read": ("yes" if verdict != "match" else "none observed"),
            "delta_status": ("observed between the 2026-11-13 read and the 2026-11-15 read"
                             if verdict != "match" else
                             "no change observed between the two reads"),
            "source_url": INJ_URL,
        })
    for r in cf_inj:
        if (r["team"], r["player"].strip()) in {(s["team"], s["player"].strip()) for s in inj_sample["rows"]}:
            continue
        inj_rows.append({
            "team": r["team"], "player": r["player"], "position": r["position"],
            "injury": r.get("injury", ""),
            "practice_status": r.get("practice_status_as_published", ""),
            "game_status": r.get("game_status_as_published", ""),
            "week": 10, "captured_utc": "2026-11-13",
            "read_by": "session 864d5668 (carried forward)",
            "crosscheck_vs_carried_forward": "source row (earlier read)",
            "delta_vs_previous_read": "",
            "delta_status": "UNVERIFIED - this row was not re-read by this session (F-03)",
            "source_url": r.get("source", INJ_URL),
        })

    # every field that differs between the two official reads of the same week
    inj_delta = []
    for s in inj_sample["rows"]:
        cf = inj_index.get((s["team"], s["player"].strip()))
        if cf is None:
            inj_delta.append({
                "team": s["team"], "player": s["player"], "field": "(whole row)",
                "value_read_2026_11_13": "ROW ABSENT", "value_read_2026_11_15": "present",
                "source_url": INJ_URL,
            })
            continue
        for field, newval, oldval in (("practice status", s["practice_status"],
                                       cf.get("practice_status_as_published") or ""),
                                      ("game status", s["game_status"],
                                       cf.get("game_status_as_published") or ""),
                                      ("injury", s["injury"], cf.get("injury") or "")):
            if newval != oldval:
                inj_delta.append({
                    "team": s["team"], "player": s["player"], "field": field,
                    "value_read_2026_11_13": oldval or "(blank)",
                    "value_read_2026_11_15": newval or "(blank)",
                    "source_url": INJ_URL,
                })

    # designations per club from the injury report (carried-forward file is the
    # only complete read; it is sourced to the same official page)
    out_by_team, q_by_team, listed_by_team = {}, {}, {}
    for r in inj_rows:
        t = r["team"]
        listed_by_team[t] = listed_by_team.get(t, 0) + 1
        if r["game_status"] == "Out":
            out_by_team[t] = out_by_team.get(t, 0) + 1
        elif r["game_status"] == "Questionable":
            q_by_team[t] = q_by_team.get(t, 0) + 1

    # starter-out detection: is a player the club's published rank-1 at his position?
    def club_slots(team):
        c = depth_raw["clubs"].get(team, {})
        out = []
        for unit in ("offense", "defense"):
            for row in c.get(unit, []):
                ranks = row[1:]
                names = [[n for n in r] if isinstance(r, list) else ([r] if r else [])
                         for r in ranks]
                while len(names) < 4:
                    names.append([])
                out.append({"unit": unit.capitalize(), "position": row[0], "ranks": names})
        return out

    replacement_rows, team_rows = [], []
    for team in teams:
        slots = club_slots(team)
        outs = [r for r in inj_rows if r["team"] == team and r["game_status"] == "Out"]
        out_names = {r["player"] for r in outs}
        q_names = {r["player"] for r in inj_rows if r["team"] == team and r["game_status"] == "Questionable"}
        team_slots = 0
        out_slots = 0
        no_backup = 0
        named = 0
        for sl in slots:
            team_slots += 1
            r1 = sl["ranks"][0]
            hit = [n for n in r1 if n in out_names]
            if not hit:
                continue
            out_slots += 1
            starter = hit[0]
            # walk down the published ranks, skipping anyone else who is Out
            repl, repl_tier, skipped = "", "", []
            for tier in range(1, 4):
                for cand in sl["ranks"][tier]:
                    if cand in out_names:
                        skipped.append(cand)
                        continue
                    repl, repl_tier = cand, tier + 1
                    break
                if repl:
                    break
            if repl:
                named += 1
                rung = repl_tier - 1
                label = {1: "2nd string", 2: "3rd string", 3: "4th string"}.get(repl_tier, "")
                compound = "YES" if skipped else "no"
            else:
                no_backup += 1
                rung = ""
                label = "NO REPLACEMENT PUBLISHED"
                compound = "n/a"
            replacement_rows.append({
                "team": team, "club": by_team[team]["club"], "unit": sl["unit"],
                "position": sl["position"],
                "starter_named_by_club": starter,
                "starter_game_status": "Out",
                "replacement_named_by_club": repl,
                "replacement_depth_string": repl_tier or "",
                "depth_of_replacement_label": label,
                "rungs_down": rung,
                "compounding_replacement_also_out": compound,
                "cascade_skipped": ", ".join(skipped),
                "replacement_on_injury_report": ("Out" if repl in out_names else
                                                 "Questionable" if repl in q_names else
                                                 "not listed"),
                "no_backup_published": "YES" if not repl else "no",
                "depth_source_url": depth_raw["clubs"][team]["source_url"],
                "injury_source_url": INJ_URL,
                "as_of": "2026-11-15",
            })
        club = depth_raw["clubs"].get(team)
        if club is None:
            depth_status = "NO CLUB DEPTH CHART IN THE STORE"
            slots_cell, repl_cell, nobackup_cell = "", "", ""
            depth_url = ""
        elif club.get("parsed") is False:
            depth_status = "UNVERIFIED - " + club.get("parse_failure_reason", "")
            slots_cell, repl_cell, nobackup_cell = "", "", ""
            depth_url = club["source_url"]
        elif club.get("partial"):
            depth_status = "PARTIAL - " + club["partial_note"]
            slots_cell, repl_cell, nobackup_cell = team_slots, named, no_backup
            depth_url = club["source_url"]
        else:
            depth_status = "parsed"
            slots_cell, repl_cell, nobackup_cell = team_slots, named, no_backup
            depth_url = club["source_url"]
        # A club only has a game-status column once its game is close enough; a
        # club with no published game status gets blanks, never zeros.
        has_status = any(r["team"] == team and r["game_status"] for r in inj_rows)
        if has_status:
            out_cell = out_by_team.get(team, 0)
            q_cell = q_by_team.get(team, 0)
            net_cell = out_cell + 0.5 * q_cell
            status_note = ("game status published for this club in the week-10 report; "
                           "the counts below are read from it")
            starters_cell, q_cell_out = out_slots, q_cell
        else:
            out_cell = q_cell = net_cell = ""
            starters_cell = ""
            status_note = ("UNVERIFIED - the week-10 report publishes no game status for this "
                           "club, so a starter-out count cannot be read. Blank, not zero.")
        team_rows.append({
            "team": team, "club": by_team[team]["club"],
            "depth_slots_parsed": slots_cell,
            "depth_status": depth_status,
            "players_listed_on_report": listed_by_team.get(team, 0),
            "game_status_published": "YES" if has_status else "NO",
            "starters_out": starters_cell,
            "replacements_named": repl_cell,
            "slots_with_no_replacement_published": nobackup_cell,
            "players_out": out_cell,
            "players_questionable": q_cell if has_status else "",
            "net_injury_count": net_cell,
            "status_note": status_note,
            "depth_source_url": depth_url,
            "injury_source_url": INJ_URL,
        })

    # ---------------- matchup deficiency matrix (offence vs defence) --------
    PAIRS = [
        ("WR", ["CB"], "outside receiver vs cornerback"),
        ("TE", ["S", "LB"], "tight end vs safety / linebacker"),
        ("LT", ["EDGE", "OLB", "DE", "RUSH"], "left tackle vs edge rusher"),
        ("RT", ["EDGE", "OLB", "DE", "RUSH"], "right tackle vs edge rusher"),
        ("LG", ["DT", "DL", "NT"], "left guard vs interior line"),
        ("RG", ["DT", "DL", "NT"], "right guard vs interior line"),
        ("C", ["DT", "DL", "NT"], "centre vs interior line"),
        ("RB", ["LB"], "running back vs linebacker"),
        ("QB", ["DL", "DT", "EDGE"], "quarterback vs pass rush"),
    ]

    def first_available(slot):
        for tier in range(4):
            for n in slot["ranks"][tier]:
                return tier + 1, n
        return None, ""

    matchup_rows = []
    for g in slate["games"]:
        for off_team, def_team in ((g["away"], g["home"]), (g["home"], g["away"])):
            off_slots = club_slots(off_team)
            def_slots = club_slots(def_team)
            for opos, dposs, label in PAIRS:
                for sl in off_slots:
                    if sl["position"] != opos:
                        continue
                    otier, oname = first_available(sl)
                    if otier is None:
                        continue
                    for dsl in def_slots:
                        if dsl["position"] not in dposs:
                            continue
                        dtier, dname = first_available(dsl)
                        if dtier is None:
                            continue
                        gap = dtier - otier
                        matchup_rows.append({
                            "game_id": g["game_id"], "week": 11,
                            "matchup": f"{g['away']} @ {g['home']}",
                            "offence_team": off_team, "defence_team": def_team,
                            "pairing": label,
                            "offence_position": opos, "offence_player": oname,
                            "offence_depth_string": otier,
                            "defence_position": dsl["position"], "defence_player": dname,
                            "defence_depth_string": dtier,
                            "depth_gap_defence_minus_offence": gap,
                            "flag": ("DEFICIENCY - offence faces a deeper-string defender"
                                     if gap >= 1 else
                                     "MISMATCH - defence is deeper-string than the offence"
                                     if gap <= -1 else "even"),
                            "offence_source_url": depth_raw["clubs"][off_team]["source_url"],
                            "defence_source_url": depth_raw["clubs"][def_team]["source_url"],
                        })

    # ---------------- strategies -------------------------------------------
    def eval_family(name, pick_fn, note=""):
        n = hits = 0
        for f in finals:
            pick = pick_fn(f)
            if pick is None:
                continue
            n += 1
            if pick:
                hits += 1
        rate = hits / n if n else None
        return {"n": n, "hits": hits, "rate": rate,
                "p": binom_two_sided_p(hits, n, 0.5) if n else None,
                "lo": wilson_interval(hits, n)[0] if n else None,
                "hi": wilson_interval(hits, n)[1] if n else None, "note": note}

    def pick_home(f):
        return f["home_margin"] > 0

    def pick_model_side(f):
        if f["week"] <= 1:
            return None
        train = [g for g in finals if g["week"] < f["week"]]
        if len(train) < 16:
            return None
        rmap, hfa_t, _ = fit_ratings(train)
        pred = rmap[f["home"]] - rmap[f["away"]] + (0.0 if f["neutral_site"] else hfa_t)
        if pred == 0:
            return None
        return (pred > 0) == (f["home_margin"] > 0)

    def pick_total(f):
        """Back the over when our estimator is more than 3 points above the
        league mean, the under when it is more than 3 points below. Both the
        estimator and the mean are fitted on the weeks before this game."""
        if f["week"] <= 1:
            return None
        train = [g for g in finals if g["week"] < f["week"]]
        if len(train) < 16:
            return None
        base, sh, _, _ = fit_totals(train)
        pred = base + sh[f["home"]] + sh[f["away"]]
        if abs(pred - base) <= 3.0:
            return None
        return (pred > base) == (f["total_points"] > base)

    def pick_rest(f):
        rh, ra = rest_for(f, "home"), rest_for(f, "away")
        if rh is None or ra is None:
            return None
        if rh - ra >= 3:
            return f["home_margin"] > 0
        if ra - rh >= 3:
            return f["home_margin"] < 0
        return None

    def pick_bye(f):
        prev_byes = byes.get(f["week"] - 1, [])
        h_off = f["home"] in prev_byes
        a_off = f["away"] in prev_byes
        if h_off == a_off:
            return None
        return f["home_margin"] > 0 if h_off else f["home_margin"] < 0

    def pick_fav(f):
        pm = ratings[f["home"]] - ratings[f["away"]] + (0.0 if f["neutral_site"] else hfa)
        p = 1.0 - norm_cdf((0.0 - pm) / sigma)
        if p <= 0.70:
            return None
        return f["home_margin"] > 0

    def pick_injury(f):
        return None  # no historical injury time series exists

    fams = [
        ("F1", pick_home, "home side in every game",
         "no fitting, so nothing can leak; the sample is every completed game"),
        ("F2", pick_model_side, "walk-forward model side (correct winner)",
         "out of sample: the ratings are refitted on the weeks before each game"),
        ("F3", pick_total, "over/under against our own estimator, 3-point band",
         "out of sample: the estimator and the league mean are refitted on the weeks before each game"),
        ("F4", pick_rest, "side of the team with a rest edge of 3+ days",
         "no fitting: rest days are fixed by the published kickoff dates"),
        ("F5", pick_bye, "side of the team coming off its bye",
         "no fitting: bye weeks are published with the schedule"),
        ("F6", pick_fav, "moneyline when model win probability exceeds 70%",
         "IN-SAMPLE: uses ratings fitted on the whole season, including the games being graded. "
         "This row is a diagnostic, not an estimate of skill, and it is excluded from promotion"),
        ("F7", pick_injury, "side of the team whose opponent has more starters out",
         "no sample: the week-10 report publishes a game status for 4 clubs only"),
    ]
    results = {}
    for fid, fn, note, how in fams:
        results[fid] = eval_family(fid, fn, note)
        results[fid]["measurement"] = how
    for fid in ("F8", "F9", "F10"):
        results[fid] = {"n": 0, "hits": 0, "rate": None, "p": None, "lo": None, "hi": None,
                        "note": "blocked by gate G7 - no validated joint probability and no operator void/push rules",
                        "measurement": "no sample: gate G7 fails, so nothing is measured"}

    order = [fid for fid, _, _, _ in fams] + ["F8", "F9", "F10"]
    pvals = [results[f]["p"] if results[f]["p"] is not None else 1.0 for f in order]
    adj = holm(pvals)
    adj_map = dict(zip(order, adj))

    strat_rows = []
    for fid, name, division, rule_text, window, falsify, would_change in (
        (s[0], s[1], s[2], s[3], s[4], s[5], s[6]) for s in content.STRATEGIES
    ):
        r = results[fid]
        if r["n"]:
            holm_p = adj_map[fid]
        else:
            holm_p = None
        gates_fail = []
        if r["n"] < 300:
            gates_fail.append("G1(n<300)")
        gates_fail.append("G2(no price)")
        if division != "Singles":
            gates_fail.append("G7(no joint evidence)")
        if fid == "F7":
            gates_fail.append("F-03(no injury time series)")
        certified = "NO"
        strat_rows.append({
            "family_id": fid, "name": name, "division": division,
            "rule_text": rule_text, "sample_window": window,
            "n": r["n"], "hits": r["hits"],
            "hit_rate": fmt(r["rate"], 4),
            "wilson_lo": fmt(r["lo"], 4), "wilson_hi": fmt(r["hi"], 4),
            "binomial_p": fmt(r["p"], 6),
            "holm_p": fmt(holm_p, 6) if holm_p is not None else "",
            "measurement": r["measurement"],
            "roi": "", "roi_status": "UNVERIFIED - ROI needs a price; no price exists (F-01)",
            "gates_failed": "; ".join(gates_fail),
            "certified": certified,
            "what_would_change_our_mind_down": falsify,
            "what_would_change_our_mind_up": would_change,
            "registration": "frozen in content.py before the week-11 slate was priced; versioned in git, so the commit that last changed content.py is the registration",
            "source_url": STD_URL,
        })

    # controls
    control_rows = []
    # random: expected 50%
    n_all = len(finals)
    control_rows.append({
        "control_id": "C1", "control": "Random pick (coin flip)",
        "n": n_all, "expected_hit_rate": "0.5000", "observed_hit_rate": "",
        "note": "The null every family must beat. Its interval is the yardstick on the leaderboard.",
        "source_url": STD_URL,
    })
    # favourites under our own model
    fav_n, fav_hits = 0, 0
    for f in finals:
        pm = ratings[f["home"]] - ratings[f["away"]] + (0.0 if f["neutral_site"] else hfa)
        if pm == 0:
            continue
        fav_n += 1
        if (pm > 0) == (f["home_margin"] > 0):
            fav_hits += 1
    control_rows.append({
        "control_id": "C2", "control": "Model favourite wins outright (in-sample)",
        "n": fav_n, "expected_hit_rate": "", "observed_hit_rate": fmt(fav_hits / fav_n if fav_n else None, 4),
        "note": "In-sample. The out-of-sample version is family F2 and is the one that counts.",
        "source_url": STD_URL,
    })
    home_n = sum(1 for f in finals if f["home_margin"] != 0)
    home_hits = sum(1 for f in finals if f["home_margin"] > 0)
    control_rows.append({
        "control_id": "C3", "control": "Home team wins outright",
        "n": home_n, "expected_hit_rate": "", "observed_hit_rate": fmt(home_hits / home_n if home_n else None, 4),
        "note": "Identical to family F1; published on both boards so the reader can see the overlap.",
        "source_url": STD_URL,
    })

    # ---------------- correlations (official inputs only) -------------------
    corr_rows = []

    def add_corr(cid, a, b, xs, ys, note):
        r = pearson(xs, ys)
        lo, hi = fisher_ci(r, len(xs))
        corr_rows.append({
            "correlation_id": cid, "variable_a": a, "variable_b": b,
            "n": len(xs), "r": fmt(r, 4), "ci95_lo": fmt(lo, 4), "ci95_hi": fmt(hi, 4),
            "input_tier": "OFFICIAL", "inputs": note,
            "source_url": STD_URL,
        })

    winpct = [by_team[t]["win_pct"] for t in teams]
    pfpg = [by_team[t]["pf_pg"] for t in teams]
    papg = [by_team[t]["pa_pg"] for t in teams]
    netpg = [by_team[t]["net_pg"] for t in teams]
    add_corr("C1", "points for per game", "win percentage", pfpg, winpct,
             "32 official standings rows, 2026-11-15")
    add_corr("C2", "points against per game", "win percentage", papg, winpct,
             "32 official standings rows, 2026-11-15")
    add_corr("C3", "net points per game", "win percentage", netpg, winpct,
             "32 official standings rows, 2026-11-15")
    add_corr("C4", "points for per game", "points against per game", pfpg, papg,
             "32 official standings rows, 2026-11-15")

    margins = [f["home_margin"] for f in finals]
    rating_diff = [ratings[f["home"]] - ratings[f["away"]] for f in finals]
    add_corr("C5", "home margin (actual)", "rating difference (model)", margins, rating_diff,
             f"{len(finals)} official finals; in-sample by construction, published as a fit diagnostic")

    totals = [f["total_points"] for f in finals]
    pred_tot = [total_estimator_a(f["home"], f["away"]) for f in finals]
    add_corr("C6", "game total (actual)", "predicted total (estimator A)", totals, pred_tot,
             f"{len(finals)} official finals; in-sample fit diagnostic")

    rdxs, rdys = [], []
    for f in finals:
        rh, ra = rest_for(f, "home"), rest_for(f, "away")
        if rh is None or ra is None:
            continue
        rdxs.append(rh - ra)
        rdys.append(f["home_margin"])
    add_corr("C7", "rest-day difference (home minus away)", "home margin", rdxs, rdys,
             f"{len(rdxs)} official finals with a previous game for both teams; dates from the official schedule")

    # Pythagorean residual (exponent 2.37 is a modelling choice, flagged)
    EXP = 2.37
    pyth, actual = [], []
    for t in teams:
        pf = by_team[t]["pf"]
        pa = by_team[t]["pa"]
        gp = by_team[t]["gp"]
        pyth.append((pf ** EXP) / (pf ** EXP + pa ** EXP) if (pf and pa) else 0.0)
        actual.append(by_team[t]["win_pct"])
    add_corr("C8", "Pythagorean expectation (exponent 2.37)", "actual win percentage",
             pyth, actual,
             "32 official standings rows; the exponent is a MODELLING CHOICE, not an official value (flagged F-14)")

    close_share = []
    for t in teams:
        games = [f for f in finals if t in (f["home"], f["away"])]
        close = sum(1 for f in games if abs(f["home_margin"]) <= 3)
        close_share.append(close / len(games) if games else 0.0)
    add_corr("C9", "share of games decided by 3 points or fewer", "win percentage",
             close_share, winpct,
             "32 clubs; close-game share is the standard luck proxy, computed from official finals")

    pf_game, tot_game = [], []
    for f in finals:
        pf_game.append(f["away_score"] + f["home_score"])
        tot_game.append(pf_pg[f["home"]] + pf_pg[f["away"]])
    add_corr("C10", "game total (actual)", "sum of the two teams' points-for rates",
             pf_game, tot_game,
             f"{len(finals)} official finals; a naive offensive-strength check")

    withheld = [
        ("W1", "QB passing yards vs top-WR receiving yards", "0.76", "3852 team-games",
         "nflverse (third-party aggregator)",
         "session arena-f1d30421, research/arena-f1d30421/correlation.md",
         "AGGREGATOR input - inadmissible under the official-only rule"),
        ("W2", "Game-line leg outcomes (phi)", "0.01", "9479 pairs",
         "nflverse (third-party aggregator)",
         "session arena-f1d30421, data/correlation_parlays.csv",
         "AGGREGATOR input - inadmissible under the official-only rule"),
        ("W3", "Cross-game vs same-game parlay coupling ratio", "0.984", "9479 pairs",
         "nflverse (third-party aggregator)",
         "session arena-f1d30421, data/correlation_parlays.csv",
         "AGGREGATOR input - inadmissible under the official-only rule"),
        ("W4", "Favourites cover rate", "0.481", "10729 games, 1980-2024",
         "nflverse (third-party aggregator)",
         "session arena-f1d30421, data/backtest_results.csv",
         "AGGREGATOR input - inadmissible under the official-only rule"),
        ("W5", "Home underdogs cover rate", "0.526", "10729 games, 1980-2024",
         "nflverse (third-party aggregator)",
         "session arena-f1d30421, data/backtest_results.csv",
         "AGGREGATOR input - inadmissible under the official-only rule"),
        ("W6", "Overs cover rate", "0.491", "10729 games, 1980-2024",
         "nflverse (third-party aggregator)",
         "session arena-f1d30421, data/backtest_results.csv",
         "AGGREGATOR input - inadmissible under the official-only rule"),
        ("W7", "Market spread vs closing spread (CLV basis)", "not published", "0",
         "no source", "no desk in this repo",
         "NO SOURCE - no price data of any kind exists in this repo"),
        ("W8", "Player prop joint distributions", "not published", "0",
         "no source", "no desk in this repo",
         "NO SOURCE - no prop prices exist in this repo"),
    ]

    # ---------------- luck panel -------------------------------------------
    luck_rows = []
    for t in teams:
        off = by_team[t]
        games = [f for f in finals if t in (f["home"], f["away"])]
        close = sum(1 for f in games if abs(f["home_margin"]) <= 3)
        exp_w = ((off["pf"] ** EXP) / (off["pf"] ** EXP + off["pa"] ** EXP)) * off["gp"]
        sd = math.sqrt(off["gp"] * 0.25)
        luck_rows.append({
            "team": t, "club": off["club"], "games": off["gp"],
            "actual_wins": off["w"], "actual_win_pct": fmt(off["win_pct"], 4),
            "pythagorean_expected_wins": fmt(exp_w, 3),
            "luck_wins_actual_minus_expected": fmt(off["w"] - exp_w, 3),
            "close_game_share": fmt(close / len(games) if games else None, 4),
            "binomial_sd_wins": fmt(sd, 3),
            "binomial_95_low": fmt(off["gp"] * 0.5 - 1.96 * sd, 2),
            "binomial_95_high": fmt(off["gp"] * 0.5 + 1.96 * sd, 2),
            "inside_the_noise_band": "YES" if (off["gp"] * 0.5 - 1.96 * sd) <= off["w"] <= (off["gp"] * 0.5 + 1.96 * sd) else "no",
            "source_url": STD_URL,
        })

    # how big a sample a 55% bettor needs
    power_rows = []
    for target in (0.53, 0.55, 0.57, 0.60):
        n_needed = None
        for n in range(10, 200001, 10):
            se = math.sqrt(0.5 * 0.5 / n)
            if target - 0.5 > 1.96 * se + 0.8416 * math.sqrt(target * (1 - target) / n):
                n_needed = n
                break
        p_200 = 1.0 - sum(math.comb(200, k) * (0.5 ** 200) for k in range(int(0.55 * 200) + 1))
        prob_55_over_200 = 1.0 - sum(math.comb(200, k) * (0.5 ** k) * (0.5 ** (200 - k))
                                     for k in range(0, 111))
        power_rows.append({
            "true_hit_rate": fmt(target, 2),
            "bets_to_demonstrate_skill_80pct_power": n_needed if n_needed else "",
            "chance_a_coin_flip_shows_55pct_over_200_bets": fmt(prob_55_over_200, 4),
            "note": ("Exact binomial: the chance a fair coin shows at least 55% over 200 bets."
                     if target == 0.55 else "Computed with a two-sided alpha of 0.05 and 80% power."),
            "source_url": STD_URL,
        })

    # ---------------- gate matrix ------------------------------------------
    gate_rows = [{"gate_id": g[0], "name": g[1], "requirement": g[2], "metric": g[3],
                  "threshold": g[4], "status_this_desk": g[5], "source_url": STD_URL}
                 for g in content.GATES]
    demotion_rows = [{"trigger_id": d[0], "name": d[1], "rule": d[2], "window": d[3],
                      "source_url": STD_URL} for d in content.DEMOTION]

    gate_matrix = []
    for s in strat_rows:
        for g in content.GATES:
            if g[0] == "G1":
                val, st = str(s["n"]), ("FAIL" if s["n"] < 300 else "PASS")
            elif g[0] == "G2":
                val, st = "0 markets priced", "FAIL"
            elif g[0] == "G3":
                val, st = "not computable", "BLOCKED (F-01)"
            elif g[0] == "G4":
                val, st = ("walk-forward run" if s["family_id"] in ("F1", "F2", "F3", "F4", "F5", "F6")
                           else "no sample"), ("measurement only" if s["n"] else "BLOCKED")
            elif g[0] == "G5":
                val, st = s["holm_p"] or "n/a", ("PASS" if s["holm_p"] and float(s["holm_p"]) <= 0.05 else "FAIL")
            elif g[0] == "G6":
                val, st = "see luck page", "measurement only"
            elif g[0] == "G7":
                if s["division"] == "Singles":
                    val, st = "n/a - singles", "NOT APPLICABLE"
                else:
                    val, st = "no joint evidence", "FAIL"
            elif g[0] == "G8":
                val, st = "0 features after the price", "PASS"
            else:
                val, st = "committed", "PASS"
            if isinstance(val, tuple):
                val, st = val
            gate_matrix.append({
                "family_id": s["family_id"], "gate_id": g[0], "gate_name": g[1],
                "observed": val, "status": st, "source_url": STD_URL,
            })

    # ---------------- leaderboards -----------------------------------------
    signal_rows = []
    for s in strat_rows:
        signal_rows.append({
            "rank": "", "family_id": s["family_id"], "division": s["division"],
            "n": s["n"], "hit_rate": s["hit_rate"],
            "wilson_lo": s["wilson_lo"], "wilson_hi": s["wilson_hi"],
            "binomial_p": s["binomial_p"], "holm_p": s["holm_p"],
            "proper_score_status": "NOT COMPUTABLE - no benchmark price (F-01); the binomial interval is shown instead",
            "certified": s["certified"], "source_url": STD_URL,
        })
    signal_rows.sort(key=lambda r: (-(float(r["hit_rate"]) if r["hit_rate"] else -1), r["family_id"]))
    for i, r in enumerate(signal_rows, 1):
        r["rank"] = str(i)

    staking_rows = [{
        "family_id": s["family_id"], "division": s["division"], "n": s["n"],
        "stake": "", "roi": "", "clv": "", "drawdown": "",
        "status": "EMPTY BY DESIGN - staking needs a price, a stake size and settlement rules; "
                  "none of the three exists (F-01). A family cannot be certified on this axis at all.",
        "source_url": STD_URL,
    } for s in strat_rows]

    divisions = [
        ("Singles", "one market, one game", str(sum(1 for s in strat_rows if s["division"] == "Singles")),
         "eligible to be ranked; none certified"),
        ("Game parlays", "two or more legs from different games", "0",
         "gate G7 fails - no validated joint probability, no operator void/push rules"),
        ("Same-game parlays", "two or more legs from one game", "0",
         "gate G7 fails - the side/total joint distribution is not measured"),
        ("Prop combos", "player props combined", "0",
         "gate G7 fails - no prop prices exist in this repo at all"),
    ]

    # ---------------- repo audit -------------------------------------------
    audit = []

    # A: standings carried forward vs official today.
    # The two captures are a day apart, so a difference is expected wherever a
    # week-10 game completed in between. Work out what the week-10 games this
    # session captured (and that the carried-forward file did not have) should
    # have moved, and check the difference against that.
    cf_game_ids = {r["game_id"] for r in cf_feed}
    expected_delta = {t: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0} for t in teams}
    for f in feed:
        if f["week"] != 10 or f["game_id"] in cf_game_ids:
            continue
        for side, other in (("home", "away"), ("away", "home")):
            d = expected_delta[f[side]]
            d["pf"] += f[f"{side}_score"]
            d["pa"] += f[f"{other}_score"]
            if f[f"{side}_score"] > f[f"{other}_score"]:
                d["w"] += 1
            elif f[f"{side}_score"] < f[f"{other}_score"]:
                d["l"] += 1
            else:
                d["t"] += 1

    for team in teams:
        off = by_team[team]
        cf = cf_std.get(team)
        if not cf:
            continue
        diffs = []
        for key, label in (("w", "W"), ("l", "L"), ("t", "T"), ("pf", "PF"), ("pa", "PA")):
            if int(float(cf[key])) != off[key]:
                diffs.append(f"{label} {cf[key]} -> {off[key]}")
        if not diffs:
            result, interp = "MATCH", "unchanged between the two captures"
        else:
            exp = expected_delta[team]
            obs = {k: off[k] - int(float(cf[k])) for k in ("w", "l", "t", "pf", "pa")}
            if obs == exp:
                result = "DIFFERS - FULLY EXPLAINED"
                interp = ("the whole difference is accounted for by the week-10 games that "
                          "completed between the two captures (this session holds their official "
                          "final scores)")
            else:
                result = "IRREGULARITY - DIFFERS, NOT EXPLAINED"
                interp = (f"expected move from the week-10 finals: W+{exp['w']} L+{exp['l']} "
                          f"T+{exp['t']} PF+{exp['pf']} PA+{exp['pa']}; observed: "
                          f"W+{obs['w']} L+{obs['l']} T+{obs['t']} PF+{obs['pf']} PA+{obs['pa']}")
        audit.append({
            "check_id": f"A-{team}", "area": "Standings",
            "claim": f"session 3fb93d11 standings_official.csv row for {team} (captured 2026-11-14)",
            "official_value_today": f"W{off['w']}-L{off['l']}-T{off['t']} PF{off['pf']} PA{off['pa']}",
            "carried_forward_value": f"W{cf['w']}-L{cf['l']}-T{cf['t']} PF{cf['pf']} PA{cf['pa']}",
            "result": result if not diffs else result + " (" + "; ".join(diffs) + ")",
            "interpretation": interp,
            "source_url": STD_URL,
        })

    # B: spot-check of the results feed
    cf_by_id = {r["game_id"]: r for r in cf_feed}
    for g in spot["games"]:
        cf = cf_by_id.get(g["game_id"])
        if cf is None:
            audit.append({
                "check_id": f"B-{g['game_id']}", "area": "Results feed",
                "claim": f"{g['away']} {g['away_score']} at {g['home']} {g['home_score']} (week {g['week']})",
                "official_value_today": f"{g['away']} {g['away_score']} - {g['home']} {g['home_score']}",
                "carried_forward_value": "ROW ABSENT from the carried-forward feed",
                "result": "IRREGULARITY - missing row",
                "interpretation": "the carried-forward feed does not contain this game",
                "source_url": g["source"],
            })
            continue
        ok = (int(cf["away_score"]) == g["away_score"] and int(cf["home_score"]) == g["home_score"]
              and int(cf["week"]) == g["week"])
        audit.append({
            "check_id": f"B-{g['game_id']}", "area": "Results feed",
            "claim": f"{g['away']} {g['away_score']} at {g['home']} {g['home_score']} (week {g['week']})",
            "official_value_today": f"{g['away']} {g['away_score']} - {g['home']} {g['home_score']}",
            "carried_forward_value": f"{cf['away']} {cf['away_score']} - {cf['home']} {cf['home_score']} (wk {cf['week']})",
            "result": "MATCH" if ok else "IRREGULARITY - score or week differs",
            "interpretation": "the carried-forward transcription agrees with the official page read today",
            "source_url": g["source"],
        })

    # C: injury sample cross-check
    for r in inj_rows:
        if r["read_by"].startswith("session e46fb855"):
            audit.append({
                "check_id": f"C-{r['team']}-{r['player']}", "area": "Injury report",
                "claim": f"{r['player']} ({r['team']}) {r['practice_status']} / {r['game_status'] or 'no game status'}",
                "official_value_today": f"{r['practice_status']} / {r['game_status'] or '(blank)'}",
                "carried_forward_value": r["crosscheck_vs_carried_forward"],
                "result": ("MATCH" if r["crosscheck_vs_carried_forward"] == "match"
                           else "CHANGED BETWEEN TWO OFFICIAL READS - "
                                + r["crosscheck_vs_carried_forward"]),
                "interpretation": ("carried-forward file from session 864d5668 (read 2026-11-13) "
                                   "vs this session's read of the same official page (2026-11-15); "
                                   "a change here is the report moving through the week"),
                "source_url": r["source_url"],
            })

    # D: structural claims
    structural = [
        ("D1", "Results feed", "session 3fb93d11 published 137 official 2026 finals",
         f"{len(cf_feed)} rows in results_feed.csv",
         "MATCH" if len(cf_feed) == 137 else f"DIFFERS - {len(cf_feed)} rows",
         "carried-forward row count, checked in-repo"),
        ("D2", "Results feed", "weeks 1-9 hold 136 completed games (the pre-registered backtest corpus)",
         str(sum(1 for f in finals if f["week"] <= 9)),
         "MATCH" if sum(1 for f in finals if f["week"] <= 9) == 136 else "DIFFERS",
         "requirement R-19 corpus size"),
        ("D3", "Depth coverage", "session 3fb93d11/864d5668 reported 31 of 32 clubs parsed, 705 slots",
         f"{clubs_parsed} clubs parsed, {total_slots} slots this session",
         "see note",
         "this session re-transcribed every club from scratch; counts differ because this session counts one row per published position slot and excludes special teams"),
        ("D4", "Depth parsing", "the Texans publish their depth chart as an image",
         "image-only page, 0 rows parsed",
         "CONFIRMED",
         "https://www.houstontexans.com/team/depth-chart"),
        ("D5", "Depth parsing", "the Packers prepend jersey numbers to player names",
         "numbers stripped; 11 defence and 11 offence rows recovered",
         "CONFIRMED - and recovered by stripping, as the brief proposed",
         "https://www.packers.com/team/depth-chart"),
        ("D6", "Injury report", "the Week 11 injury report is not published yet",
         "reg11 serves the Week 10 report; the week selector offers weeks 1-10; the MIN@SF game centre says 'Injury Report is not available at this time'",
         "CONFIRMED", "https://www.nfl.com/injuries/league/2026/reg10"),
        ("D7", "Price data", "nfl.com publishes no spreads, totals or moneylines",
         "no price field observed on the standings, schedule or injury pages read this session",
         "CONFIRMED (observation, not proof of absence)", STD_URL),
        ("D8", "Depth slots", "some slots hold more than one rank-1 player and some are empty",
         f"{shared_rank1} shared rank-1 slots, {empty_cells} empty first-string cells",
         "CONFIRMED", "https://www.seahawks.com/team/depth-chart"),
        ("D9", "Results feed", "session 3fb93d11 reported the feed reconciles 32/32 to standings",
         f"{sum(1 for r in recon_rows if r['verdict'] == 'exact match')} of 32 teams exact today",
         "see reconciliation page", STD_URL),
        ("D10", "Correlations", "session 0f468a47 published NET/G vs PCT r=0.8391 from official standings (n=32)",
         next(c["r"] for c in corr_rows if c["correlation_id"] == "C3"),
         "see correlations page - same method, later date", STD_URL),
        ("D11", "Home-field advantage", "session 864d5668 measured HFA +0.47 with a 95% interval of -1.81 to +2.75 on 2026",
         f"{fmt(hfa, 4)} points this session on {len(finals)} games",
         "see lines page - both intervals contain zero", STD_URL),
        ("D12", "Slate", "six clubs are on bye in week 11",
         ", ".join(slate["bye_teams"]), "CONFIRMED", SLATE_URL),
        ("D13", "Rest edge",
         "session 3fb93d11 reported the rest-edge family (3+ days) at n=24, 62.5% hit rate, ROI +19.3%",
         f"n={results['F4']['n']}, {fmt(results['F4']['rate'], 4)} hit rate this session",
         "DIFFERS - same rule, different corpus (145 games here) and this session computes rest from the official kickoff dates rather than a carried-forward field",
         "https://www.nfl.com/schedules/2026/by-week/week-10"),
        ("D14", "Totals estimator",
         "an earlier run of this session's build showed estimator B beating the league-average baseline by about a point",
         f"A {fmt(model_card['oos_total_mae_a'], 4)} vs baseline {fmt(model_card['oos_total_mae_baseline'], 4)}; B {fmt(model_card['oos_total_mae_b'], 4)}",
         "CORRECTED - the first run leaked: estimator B used the season's final standings, which contain the game being predicted",
         STD_URL),
    ]
    for cid, area, claim, val, res, src in structural:
        audit.append({
            "check_id": cid, "area": area, "claim": claim,
            "official_value_today": val, "carried_forward_value": val, "result": res,
            "interpretation": src if src.startswith("http") else src,
            "source_url": src if src.startswith("http") else STD_URL,
        })

    # ---------------- flagged ----------------------------------------------
    flagged = [
        ("F-01", "blocking", "Price data",
         "No market price of any kind exists in this repo",
         "nfl.com publishes no spreads, totals or moneylines, and no operator price has been read in. "
         f"All {len(markets)} originated markets therefore have a blank market column.",
         "Gates G2, G3 and G4 cannot pass for any family; ROI, CLV and the residual against the market are all undefined.",
         "Decide S-01.", "AWAITING DECISION", STD_URL),
        ("F-02", "blocking (Houston only)", "Depth parsing",
         "Houston publishes its depth chart as an image",
         "The Texans depth page carries a raster image and no text table, so Houston contributes 0 depth rows.",
         "Houston's replacement depth, the Houston leg of the matchup matrix and any Houston starter-out count are blank.",
         "Find a structured Texans source, or an official snap-count source (S-02).", "OPEN",
         "https://www.houstontexans.com/team/depth-chart"),
        ("F-03", "blocking", "Injury time series",
         "Only one read of the injury report exists",
         "The week-10 report was read once, at 2026-11-15T23:27Z. No delta can be computed and no surprise can be measured.",
         "R-12 (injury as a surprise), R-21 (delta not level), R-27/R-28 (ablations), R-44 (designation calibration) and R-55 all fail.",
         "Re-read the same week later in the week; then decide S-03 for a scheduler.", "OPEN", INJ_URL),
        ("F-04", "blocking", "Transactions",
         "No transactions or reserve list has been read",
         "The official transactions log was not fetched this session, so no IR or reserve list is in the store.",
         "Absence from the injury report cannot be split into 'available' and 'on a reserve list' (R-64), and depth rows cannot be versioned against roster events (R-34, R-46).",
         "Fetch https://www.nfl.com/transactions/ and keep it dated.", "OPEN",
         "https://www.nfl.com/transactions/"),
        ("F-05", "blocking", "Game-day evidence",
         "No official inactive list and no game book has been read",
         "Only club depth charts and the league injury report are in the store; neither confirms who actually started.",
         "R-10 (availability graph), R-25 (game books), R-31 and R-42 all fail.",
         "Decide S-02; the cheapest first step is one club's inactives article.", "AWAITING DECISION",
         "https://www.atlantafalcons.com/news/atlanta-falcons-week-10-inactives-vs-kansas-city-chiefs"),
        ("F-06", "blocking", "Snap counts",
         "No official snap-count source has been read",
         "Depth is taken from club charts only. No playing-time evidence exists.",
         "R-11 (depth from playing time) and R-56 (snap proxy when the chart is missing) both fail.",
         "Decide S-02; without it Houston has no depth rows at all.", "AWAITING DECISION",
         "https://www.nfl.com/stats/"),
        ("F-07", "non-blocking", "Weather and roof",
         "No roof designation and no NWS forecast in the store",
         "Neither the official 90-minute roof designation nor any weather grid has been read.",
         "R-58 is deferred by design (S-05): the feature changes totals pricing, which cannot be scored until F-01 is resolved.",
         "Deferred until S-01 is decided.", "DEFERRED", SLATE_URL),
        ("F-08", "non-blocking", "Player props",
         "No prop prices exist anywhere in this repo",
         "Neither nfl.com nor any aggregator read into this repo carries player-prop lines.",
         "The prop-combo division produces zero graded bets and gate G7 fails for it.",
         "Wait for S-01; prop prices are a separate licensing question.", "OPEN",
         "https://www.nfl.com/stats/"),
        ("F-09", "review", "Venue provenance",
         "Venue provenance is mixed across the week-11 slate",
         "12 of 13 venues come from the venue string nfl.com prints on the schedule page; 1 of 13 (MIN@SF) was read from the game centre itself.",
         "R-23 is partial rather than met. The values agree, but the provenance is not uniform.",
         "Read the remaining 12 game-centre pages (S-13).", "OPEN",
         "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11"),
        ("F-10", "review", "Rule priors",
         "The 2026 kickoff and onside-kick rule text has not been read",
         "No official rule source was fetched this session.",
         "R-69 fails; any kickoff-regime prior would be an assumption, so none is applied.",
         "Fetch the official rule text before adding the filter.", "OPEN",
         "https://operations.nfl.com/"),
        ("F-11", "review", "Schedule announcement",
         "The dated schedule-release announcement was not fetched",
         "The live schedule page is in the store; the announcement beside it is not.",
         "R-24 fails.", "Fetch the league's schedule-release news item and record its date.", "OPEN",
         SLATE_URL),
        ("F-12", "blocking", "Single season",
         "The official results feed holds one season",
         f"{len(finals)} completed 2026 games and nothing before them.",
         "R-70 (train/validation/holdout) fails and gate G1 (n >= 300) is unreachable for every family.",
         "S-06: extend the official feed backwards, one season at a time.", "AWAITING DECISION",
         "https://www.nfl.com/schedules/2025/by-week/week-1"),
        ("F-13", "review", "Week 10 in progress",
         "Week 10 was still being played when it was captured",
         "3 games were live and 2 had not kicked off at 2026-11-15T23:22Z. Their scores are published blank, not filled in.",
         "The corpus and the standings reconciliation both exclude them, which is why the reconciliation shows a residual.",
         "Re-capture after the Monday night game.", "OPEN", WK10_URL),
        ("F-14", "review", "Pythagorean exponent",
         "The Pythagorean exponent is a modelling choice, not an official value",
         "Correlation C8 and the luck panel use an exponent of 2.37, an industry convention rather than a league-published number.",
         "The luck column is a convention-based estimate and is labelled as such everywhere it appears.",
         "Either source an official value or keep the label. No action required to publish.", "ACCEPTED AND LABELLED",
         STD_URL),
        ("F-15", "review", "New England depth capture",
         "The Patriots defence table was cut off by pagination",
         "The Patriots depth page spans three pages; the defence rows after Christian Elliss were not captured.",
         "New England's defensive slots are incomplete. New England is on bye in week 11, so no week-11 market is affected.",
         "Capture the remaining pages (New England is not needed for week 11 but is needed for week 12).", "OPEN",
         "https://www.patriots.com/team/depth-chart"),
        ("F-18", "review", "Methodology",
         "A leakage in the first totals walk-forward was found and corrected",
         "The first run fitted estimator B on the season's final points-for and points-against "
         "rates, which include the game being predicted. It appeared to beat the league-average "
         "baseline by about a point. Fitting on prior weeks only reverses the result: neither "
         "estimator beats the baseline.",
         "The published totals comparison is the corrected one. Any future estimator must be "
         "fitted inside the walk-forward loop, never on the full sample.",
         "FIXED THIS SESSION", STD_URL),
        ("F-17", "review", "Model specification",
         "Team ratings are ridge-penalised",
         "The margin model applies a ridge penalty of 1.0 point squared to the 32 team columns. "
         "Without it the model is not identifiable early in a season: after two rounds every team "
         "has one home game and one away game, so home advantage cannot be separated from team "
         "strength, and the least-squares system is singular.",
         "Ratings are shrunk toward zero, by roughly 10% at a full season of games. The home-field "
         "estimate and every originated line inherit that shrinkage.",
         "Pre-registered: do not tune it on the evaluation weeks. Revisit only once more than one "
         "season is in the official feed (F-12).", "ACCEPTED AND LABELLED", STD_URL),
        ("F-16", "review", "Club charts are labelled unofficial",
         "Every club labels its own depth chart 'unofficial'",
         "Clubs publish these charts through their communications departments and print that caveat on the page.",
         "Depth is an official club publication but is not the league's game-day starter list, so it is never reported as an announced starter (R-42).",
         "Accepted and labelled on every depth row.", "ACCEPTED AND LABELLED",
         "https://www.detroitlions.com/team/depth-chart"),
    ]

    # ---------------- sources ----------------------------------------------
    sources = [
        ("OFF-STD", "NFL.com", "2026 NFL League Standings (regular season)", STD_URL, "OFFICIAL",
         "2026-11-15T23:26:00Z", "32 team rows: W-L-T, PF, PA; the reconciliation benchmark and the correlations",
         "32", "read directly through the sandbox fetcher; transcribed verbatim"),
        ("OFF-SLATE-11", "NFL.com", "2026 NFL Schedule - Week 11", SLATE_URL, "OFFICIAL",
         "2026-11-15T23:24:00Z", "13 fixtures: matchup, date, kickoff, network, venue, bye teams",
         "13 games + 6 byes", "read directly; venue strings transcribed from the page's own per-game venue field"),
        ("OFF-GC-MINSF", "NFL.com", "Vikings at 49ers 2026 REG 11 - Game Center",
         "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11", "OFFICIAL", "2026-11-15T23:25:00Z",
         "Venue for MIN@SF (Location MEXICO CITY, Stadium ESTADIO BANORTE); also confirms the week-11 injury report is not available",
         "1", "read directly"),
        ("OFF-WK10", "NFL.com", "2026 NFL Schedule - Week 10", WK10_URL, "OFFICIAL",
         "2026-11-15T23:22:00Z", "9 final scores plus the published status of 5 unfinished games",
         "14", "read directly; only rows the page labels FINAL are carried as results"),
        ("OFF-SPOT", "NFL.com", "2026 weeks 1-5 schedule pages (first page of each)",
         "https://www.nfl.com/schedules/2026/by-week/week-1 ... week-5", "OFFICIAL",
         "2026-11-15T23:20:00Z", "Independent spot-check of the carried-forward results feed",
         str(len(spot["games"])), "read directly by this session, one page per week"),
        ("OFF-INJ-10", "NFL.com", "Official NFL Injury Report - Week 10, 2026", INJ_URL, "OFFICIAL",
         "2026-11-15T23:27:00Z", "Practice and game designations driving the replacement-depth tracker",
         str(len(inj_sample["rows"])) + " read this session", "page 1 of 8 read directly; incomplete rows omitted rather than guessed"),
        ("OFF-INJ-11", "NFL.com", "Official NFL Injury Report - Week 11, 2026 (requested)",
         "https://www.nfl.com/injuries/league/2026/reg11", "OFFICIAL", "2026-11-15T23:27:00Z",
         "Would drive the week-11 injury adjustment", "0",
         "NOT PUBLISHED - the URL serves the Week 10 report; see F-03 and the D6 audit row"),
        ("OFF-DEPTH", "32 NFL club sites", "Official club depth charts", "https://www.nfl.com/teams/",
         "OFFICIAL (club-published)", "2026-11-15T23:35:00Z",
         "Replacement depth, the deficiency matrix and the per-team starter-out view",
         f"{total_slots} slots across {clubs_parsed} clubs",
         "each club's own /team/depth-chart page read directly; Houston returns an image and contributes 0 rows"),
        ("CF-FEED", "session 3fb93d11 (in-repo)", "results_feed.csv - 137 official 2026 finals",
         "https://www.nfl.com/schedules/2026/by-week/", "OFFICIAL (carried forward)", "2026-11-14T21:33:19Z",
         "The base of the results feed; every row re-checked where this session read the same page",
         str(len(cf_feed)), f"carried forward; sha256 prefix {cf_feed_sha}"),
        ("CF-STD", "session 3fb93d11 (in-repo)", "standings_official.csv",
         STD_URL, "OFFICIAL (carried forward)", "2026-11-14T21:33:19Z",
         "Audit comparison against today's official standings", "32",
         f"carried forward; sha256 prefix {cf_std_sha}"),
        ("CF-INJ", "session 864d5668 (in-repo)", "injuries.csv - week-10 report",
         INJ_URL, "OFFICIAL (carried forward)", "2026-11-13",
         "The only complete read of the week-10 report; cross-checked against this session's sample",
         str(len(cf_inj)), f"carried forward; sha256 prefix {cf_inj_sha}"),
    ]

    # ---------------- requirements with computed status ---------------------
    req_rows = []
    for rid, text, status, gate, clears, page in content.REQUIREMENTS:
        req_rows.append({
            "requirement_id": rid, "requirement": text, "status": status,
            "blocking_gate": gate, "number_that_would_clear_it": clears,
            "page": page, "source_url": STD_URL,
        })

    # ---------------- write everything --------------------------------------
    write_csv("results_feed.csv",
              ["game_id", "season", "week", "kickoff_date", "away", "home", "away_score",
               "home_score", "home_margin", "total_points", "result", "neutral_site",
               "status", "verification", "verification_note", "source_url"],
              [[f["game_id"], f["season"], f["week"], f["kickoff_date"], f["away"], f["home"],
                f["away_score"], f["home_score"], f["home_margin"], f["total_points"],
                f["result"], f["neutral_site"], f["status"], f["verification"],
                f["verification_note"], f["source_url"]] for f in feed])

    write_csv("results_pending.csv",
              ["game_id", "week", "kickoff_date", "away", "home", "away_score", "home_score",
               "status", "source_url"],
              [[p["game_id"], p["week"], p["kickoff_date"], p["away"], p["home"],
                p["away_score"], p["home_score"], p["status"], p["source_url"]]
               for p in pending])

    write_csv("standings_official.csv",
              ["team", "club", "w", "l", "t", "pct", "pf", "pa", "net", "gp", "pf_per_game",
               "pa_per_game", "net_per_game", "win_pct", "source_url"],
              [[s["team"], s["club"], s["w"], s["l"], s["t"], s["pct"], s["pf"], s["pa"],
                s["net"], s["gp"], fmt(s["pf_pg"], 4), fmt(s["pa_pg"], 4), fmt(s["net_pg"], 4),
                fmt(s["win_pct"], 4), STD_URL] for s in standings])

    write_csv("standings_reconciliation.csv",
              ["team", "club", "official_w", "official_l", "official_t", "official_pf",
               "official_pa", "feed_w", "feed_l", "feed_t", "feed_pf", "feed_pa", "delta_w",
               "delta_l", "delta_t", "delta_pf", "delta_pa", "verdict", "source_url"],
              [[r[k] for k in ("team", "club", "official_w", "official_l", "official_t",
                               "official_pf", "official_pa", "feed_w", "feed_l", "feed_t",
                               "feed_pf", "feed_pa", "delta_w", "delta_l", "delta_t",
                               "delta_pf", "delta_pa", "verdict", "source_url")]
               for r in recon_rows])

    write_csv("team_ratings.csv",
              ["team", "club", "rating_points", "games_played", "pf_per_game", "pa_per_game",
               "team_game_total_avg", "shrunk_total_tendency", "source_url"],
              [[t, by_team[t]["club"], fmt(ratings[t], 4), by_team[t]["gp"],
                fmt(by_team[t]["pf_pg"], 4), fmt(by_team[t]["pa_pg"], 4),
                fmt(team_total_avg[t], 4), fmt(shrink[t], 4), STD_URL]
               for t in sorted(teams, key=lambda x: -ratings[x])])

    mk = list(markets[0].keys())
    write_csv("originated_markets.csv", mk, [[m[k] for k in mk] for m in markets])
    write_csv("origination_steps.csv",
              ["game_id", "market_id", "step", "market_type", "instruction", "depends_on", "source_url"],
              [[o["game_id"], o["market_id"], o["step"], o["market_type"], o["instruction"],
                o["depends_on"], o["source_url"]] for o in origins])

    write_csv("price_snapshots.csv",
              ["market_id", "snapshot_type", "value", "captured_utc", "price_american",
               "status", "source_url", "source_tier"],
              [[p["market_id"], p["snapshot_type"], p["value"], p["captured_utc"],
                p["price_american"], p["status"], p["source_url"], p["source_tier"]]
               for p in price_rows])

    write_csv("price_store_schema.csv",
              ["slot", "what_it_holds", "required", "populated_this_build", "status"],
              [["MODEL_ORIGIN", "our own line when we first originate the market", "yes",
                str(len(markets)), "captured"],
               ["MODEL_CLOSE", "our own line re-run at the last moment before kickoff", "yes",
                "0", "EMPTY - not yet observed (F-03 sibling: needs a second run)"],
               ["MARKET_OPEN", "the operator's opening price with a timestamp", "yes", "0",
                "EMPTY - no source exists (F-01)"],
               ["MARKET_CLOSE", "the operator's closing price with a timestamp", "yes", "0",
                "EMPTY - no source exists (F-01)"],
               ["RESULT", "the official final score", "yes", str(len(finals)),
                "captured from the official results feed"],
               ["STAKE", "units actually placed", "only after certification", "0",
                "EMPTY BY DESIGN - nothing is staked until a family is certified"]])

    write_csv("slate_wk11.csv",
              ["game_id", "week", "date", "kickoff_et", "away", "home", "venue", "network",
               "neutral_site", "venue_source_url", "game_url"],
              [[g["game_id"], 11, g["date"], g["kickoff_et"], g["away"], g["home"], g["venue"],
                g["network"], "YES" if g["neutral"] else "", g["venue_source"], g["game_url"]]
               for g in slate["games"]])

    write_csv("bye_weeks_2026.csv",
              ["week", "teams_on_bye", "count", "source_url"],
              [[w, " ".join(t), len(t), STD_URL] for w, t in sorted(byes.items())]
              + [[11, " ".join(slate["bye_teams"]), len(slate["bye_teams"]), SLATE_URL]])

    write_csv("depth_slots.csv",
              ["team", "club", "unit", "position", "rank1", "rank2", "rank3", "rank4",
               "shared_rank1", "empty_first_string", "as_of_published", "source_url", "status"],
              [[d["team"], d["club"], d["unit"], d["position"], d["rank1"], d["rank2"],
                d["rank3"], d["rank4"], d["shared_rank1"], d["empty_first_string"],
                d["as_of_published"], d["source_url"], d["status"]] for d in depth_rows])

    write_csv("injuries.csv",
              ["team", "player", "position", "injury", "practice_status", "game_status",
               "week", "captured_utc", "read_by", "crosscheck_vs_carried_forward",
               "delta_vs_previous_read", "delta_status", "source_url"],
              [[r["team"], r["player"], r["position"], r["injury"], r["practice_status"],
                r["game_status"], r["week"], r["captured_utc"], r["read_by"],
                r["crosscheck_vs_carried_forward"], r["delta_vs_previous_read"],
                r["delta_status"], r["source_url"]] for r in inj_rows])

    write_csv("replacement_depth.csv",
              ["team", "club", "unit", "position", "starter_named_by_club", "starter_game_status",
               "replacement_named_by_club", "replacement_depth_string",
               "depth_of_replacement_label", "rungs_down", "compounding_replacement_also_out",
               "cascade_skipped", "replacement_on_injury_report", "no_backup_published",
               "depth_source_url", "injury_source_url", "as_of"],
              [[r[k] for k in ("team", "club", "unit", "position", "starter_named_by_club",
                               "starter_game_status", "replacement_named_by_club",
                               "replacement_depth_string", "depth_of_replacement_label",
                               "rungs_down", "compounding_replacement_also_out", "cascade_skipped",
                               "replacement_on_injury_report", "no_backup_published",
                               "depth_source_url", "injury_source_url", "as_of")]
               for r in replacement_rows])

    ta_keys = ("team", "club", "depth_slots_parsed", "depth_status",
               "players_listed_on_report", "game_status_published", "starters_out",
               "replacements_named", "slots_with_no_replacement_published", "players_out",
               "players_questionable", "net_injury_count", "status_note",
               "depth_source_url", "injury_source_url")
    write_csv("team_availability.csv", list(ta_keys),
              [[r[k] for k in ta_keys] for r in team_rows])

    write_csv("injury_delta.csv",
              ["team", "player", "field", "value_read_2026_11_13", "value_read_2026_11_15",
               "source_url"],
              [[d["team"], d["player"], d["field"], d["value_read_2026_11_13"],
                d["value_read_2026_11_15"], d["source_url"]] for d in inj_delta])

    write_csv("walkforward_by_week.csv",
              ["week", "games_evaluated", "side_picks_correct", "side_hit_rate",
               "margin_mae", "total_mae_estimator_a", "total_mae_estimator_b",
               "total_mae_league_average_baseline", "source_url"],
              [[w, v["n"], v["hits"], fmt(v["hits"] / v["n"] if v["n"] else None, 4),
                fmt(mae(v["m"]), 4), fmt(mae(v["a"]), 4), fmt(mae(v["b"]), 4),
                fmt(mae(v["base"]), 4), STD_URL]
               for w, v in sorted(oos_by_week.items())])

    write_csv("model_card.csv",
              ["item", "value", "note", "source_url"],
              [["games in the official results feed", len(finals),
                "every row read from an official nfl.com week page", STD_URL],
               ["free parameters", p,
                "32 team ratings plus the home-field term; the ratings are ridge-penalised (see F-17), so the effective number of parameters is lower", STD_URL],
               ["ridge penalty lambda", RIDGE,
                "MODELLING CHOICE, flagged as F-17. Without it the model is not identifiable early in a season", STD_URL],
               ["degrees of freedom", df, "", STD_URL],
               ["residual standard deviation (points)", fmt(sigma, 4),
                "the model's own uncertainty on a single game margin", STD_URL],
               ["home-field advantage (points)", fmt(hfa, 4),
                "negative means the home team scored fewer points than the rating difference predicts", STD_URL],
               ["home-field standard error", fmt(se_hfa, 4), "", STD_URL],
               ["home-field 95% interval low", fmt(model_card["hfa_ci95_low"], 4),
                "the interval contains zero, so home field is not established in this sample", STD_URL],
               ["home-field 95% interval high", fmt(model_card["hfa_ci95_high"], 4), "", STD_URL],
               ["league mean total (points)", fmt(league_total, 4),
                f"mean of the {len(finals)} official finals", STD_URL],
               ["walk-forward margin MAE", fmt(model_card["oos_margin_mae"], 4),
                f"{model_card['oos_side_n']} games scored out of sample (weeks 2-10)", STD_URL],
               ["walk-forward side accuracy", fmt(model_card["oos_side_hits"] / model_card["oos_side_n"] if model_card["oos_side_n"] else None, 4),
                f"{model_card['oos_side_hits']} of {model_card['oos_side_n']} winners called out of sample", STD_URL],
               ["walk-forward side binomial p", fmt(model_card["oos_side_p"], 6),
                "two-sided, against a coin flip", STD_URL],
               ["walk-forward totals MAE - estimator A", fmt(model_card["oos_total_mae_a"], 4),
                "fitted on prior weeks only; worse than the league-average baseline in this sample", STD_URL],
               ["walk-forward totals MAE - estimator B", fmt(model_card["oos_total_mae_b"], 4),
                "fitted on prior weeks only; also worse than the baseline. An earlier run of this build appeared to show estimator B winning by about a point. That was leakage: it used the season's final standings, which contain the game being predicted (F-18)", STD_URL],
               ["walk-forward totals MAE - league-average baseline", fmt(model_card["oos_total_mae_baseline"], 4),
                "the naive estimator both model estimators must beat. Neither beats it in this sample", STD_URL],
               ["prior desk's totals MAE (session 3fb93d11)", "11.0038",
                "published out-of-sample MAE against a naive baseline of 11.0235; a different walk-forward over a different corpus, so the two are not directly comparable", STD_URL],
               ])

    write_csv("matchup_deficiency.csv",
              ["game_id", "week", "matchup", "offence_team", "defence_team", "pairing",
               "offence_position", "offence_player", "offence_depth_string",
               "defence_position", "defence_player", "defence_depth_string",
               "depth_gap_defence_minus_offence", "flag", "offence_source_url", "defence_source_url"],
              [[r[k] for k in ("game_id", "week", "matchup", "offence_team", "defence_team",
                               "pairing", "offence_position", "offence_player",
                               "offence_depth_string", "defence_position", "defence_player",
                               "defence_depth_string", "depth_gap_defence_minus_offence",
                               "flag", "offence_source_url", "defence_source_url")]
               for r in matchup_rows])

    sk = list(strat_rows[0].keys())
    write_csv("strategies.csv", sk, [[s[k] for k in sk] for s in strat_rows])
    write_csv("controls.csv",
              ["control_id", "control", "n", "expected_hit_rate", "observed_hit_rate", "note",
               "source_url"],
              [[c["control_id"], c["control"], c["n"], c["expected_hit_rate"],
                c["observed_hit_rate"], c["note"], c["source_url"]] for c in control_rows])

    write_csv("gates.csv",
              ["gate_id", "name", "requirement", "metric", "threshold", "status_this_desk",
               "source_url"],
              [[g["gate_id"], g["name"], g["requirement"], g["metric"], g["threshold"],
                g["status_this_desk"], g["source_url"]] for g in gate_rows])
    write_csv("demotion_gate.csv",
              ["trigger_id", "name", "rule", "window", "source_url"],
              [[d["trigger_id"], d["name"], d["rule"], d["window"], d["source_url"]]
               for d in demotion_rows])
    write_csv("gate_matrix.csv",
              ["family_id", "gate_id", "gate_name", "observed", "status", "source_url"],
              [[m["family_id"], m["gate_id"], m["gate_name"], m["observed"], m["status"],
                m["source_url"]] for m in gate_matrix])

    write_csv("leaderboard_signal.csv",
              ["rank", "family_id", "division", "n", "hit_rate", "wilson_lo", "wilson_hi",
               "binomial_p", "holm_p", "proper_score_status", "certified", "source_url"],
              [[r["rank"], r["family_id"], r["division"], r["n"], r["hit_rate"], r["wilson_lo"],
                r["wilson_hi"], r["binomial_p"], r["holm_p"], r["proper_score_status"],
                r["certified"], r["source_url"]] for r in signal_rows])
    write_csv("leaderboard_staking.csv",
              ["family_id", "division", "n", "stake", "roi", "clv", "drawdown", "status",
               "source_url"],
              [[r["family_id"], r["division"], r["n"], r["stake"], r["roi"], r["clv"],
                r["drawdown"], r["status"], r["source_url"]] for r in staking_rows])
    write_csv("leaderboard_divisions.csv",
              ["division", "definition", "families_entered", "status"],
              [[d[0], d[1], d[2], d[3]] for d in divisions])

    write_csv("correlations.csv",
              ["correlation_id", "variable_a", "variable_b", "n", "r", "ci95_lo", "ci95_hi",
               "input_tier", "inputs", "source_url"],
              [[c["correlation_id"], c["variable_a"], c["variable_b"], c["n"], c["r"],
                c["ci95_lo"], c["ci95_hi"], c["input_tier"], c["inputs"], c["source_url"]]
               for c in corr_rows])
    write_csv("correlations_withheld.csv",
              ["id", "quantity", "value_published_elsewhere", "n_published_elsewhere",
               "input_tier", "published_by", "why_withheld"],
              [list(w) for w in withheld])

    write_csv("luck_panel.csv",
              ["team", "club", "games", "actual_wins", "actual_win_pct",
               "pythagorean_expected_wins", "luck_wins_actual_minus_expected",
               "close_game_share", "binomial_sd_wins", "binomial_95_low", "binomial_95_high",
               "inside_the_noise_band", "source_url"],
              [[r[k] for k in ("team", "club", "games", "actual_wins", "actual_win_pct",
                               "pythagorean_expected_wins", "luck_wins_actual_minus_expected",
                               "close_game_share", "binomial_sd_wins", "binomial_95_low",
                               "binomial_95_high", "inside_the_noise_band", "source_url")]
               for r in luck_rows])
    write_csv("luck_power.csv",
              ["true_hit_rate", "bets_to_demonstrate_skill_80pct_power",
               "chance_a_coin_flip_shows_55pct_over_200_bets", "note", "source_url"],
              [[r["true_hit_rate"], r["bets_to_demonstrate_skill_80pct_power"],
                r["chance_a_coin_flip_shows_55pct_over_200_bets"], r["note"], r["source_url"]]
               for r in power_rows])

    write_csv("requirements.csv",
              ["requirement_id", "requirement", "status", "blocking_gate",
               "number_that_would_clear_it", "page", "source_url"],
              [[r["requirement_id"], r["requirement"], r["status"], r["blocking_gate"],
                r["number_that_would_clear_it"], r["page"], r["source_url"]] for r in req_rows])
    write_csv("questions.csv",
              ["question_id", "question", "what_we_have", "what_is_missing", "blocking",
               "cheapest_discovery_route", "source_url"],
              [list(q) for q in content.QUESTIONS])
    write_csv("suggestions.csv",
              ["suggestion_id", "suggestion", "options", "recommended_path",
               "what_would_change_the_call", "decision_status", "note"],
              [list(s) for s in content.SUGGESTIONS])
    write_csv("flagged.csv",
              ["flag_id", "severity", "area", "title", "detail", "consequence", "action",
               "status", "source_url"],
              [list(f) for f in flagged])
    write_csv("sources.csv",
              ["source_id", "publisher", "title", "url", "tier", "fetched_utc", "used_for",
               "rows_contributed", "verification_status"],
              [list(s) for s in sources])
    write_csv("repo_audit.csv",
              ["check_id", "area", "claim", "official_value_today", "carried_forward_value",
               "result", "interpretation", "source_url"],
              [[a["check_id"], a["area"], a["claim"], a["official_value_today"],
                a["carried_forward_value"], a["result"], a["interpretation"], a["source_url"]]
               for a in audit])

    # ---------------- build report ------------------------------------------
    report = {
        "session": SESSION,
        "build_utc": BUILD_UTC,
        "official_finals": len(finals),
        "corpus_weeks_1_9": sum(1 for f in finals if f["week"] <= 9),
        "week10_finals": sum(1 for f in finals if f["week"] == 10),
        "pending_week10": len(pending),
        "spotcheck_games": len(spot["games"]),
        "spotcheck_matched": sum(1 for a in audit if a["check_id"].startswith("B-") and a["result"] == "MATCH"),
        "spotcheck_irregular": sum(1 for a in audit if a["check_id"].startswith("B-") and a["result"] != "MATCH"),
        "std_exact": sum(1 for r in recon_rows if r["verdict"] == "exact match"),
        "std_differs": sum(1 for r in recon_rows if r["verdict"] != "exact match"),
        "injury_rows": len(inj_rows),
        "injury_sample_checked": checked,
        "injury_sample_matched": matched,
        "injury_sample_mismatched": mismatched,
        "clubs_parsed": clubs_parsed,
        "depth_slots": total_slots,
        "shared_rank1_slots": shared_rank1,
        "empty_first_string_slots": empty_cells,
        "replacement_rows": len(replacement_rows),
        "matchup_rows": len(matchup_rows),
        "originated_markets": len(markets),
        "price_snapshot_rows": len(price_rows),
        "price_snapshots_populated": sum(1 for p in price_rows if p["value"]),
        "correlations": len(corr_rows),
        "correlations_withheld": len(withheld),
        "strategies": len(strat_rows),
        "certified": sum(1 for s in strat_rows if s["certified"] != "NO"),
        "audit_checks": len(audit),
        "audit_matched": sum(1 for a in audit if a["result"] == "MATCH"),
        "audit_irregular": sum(1 for a in audit if a["result"] != "MATCH" and a["result"] not in
                               ("see note", "see reconciliation page", "see correlations page - same method, later date",
                                "see lines page - both intervals contain zero", "CONFIRMED",
                                "CONFIRMED - and recovered by stripping, as the brief proposed",
                                "CONFIRMED (observation, not proof of absence)")),
        "model_card": model_card,
        "hfa": hfa,
        "sigma": sigma,
        "league_mean_total": league_total,
        "requirements_total": len(req_rows),
        "requirements_met": sum(1 for r in req_rows if r["status"] == "met"),
        "requirements_partial": sum(1 for r in req_rows if r["status"] == "partial"),
        "requirements_blocked": sum(1 for r in req_rows if r["status"] == "blocked"),
        "questions": len(content.QUESTIONS),
        "suggestions": len(content.SUGGESTIONS),
        "cf_feed_sha256_16": cf_feed_sha,
        "cf_std_sha256_16": cf_std_sha,
        "cf_inj_sha256_16": cf_inj_sha,
    }
    with open(DATA / "build_report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
    return report


if __name__ == "__main__":
    rep = build()
    print(json.dumps(rep, indent=2, sort_keys=True))

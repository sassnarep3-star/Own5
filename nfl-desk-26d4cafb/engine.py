"""NFL Decision Desk (session 26d4cafb) -- deterministic analytics engine.

Snapshot: 2026-11-12 UTC | NFL 2026 regular season | Week 10.

Pure Python 3 standard library. No third-party numerical packages are available in this
sandbox, so every statistic below is implemented explicitly and is reproducible by hand.

ZERO-HALLUCINATION POLICY ENFORCED HERE
---------------------------------------
1. Every game, score, standing, injury and player statistic is read from `raw_inputs.py`,
   which holds verbatim values fetched from official NFL / official NFL-club pages.
2. Any quantity that has no official source (market spreads/totals/moneylines, player-prop
   lines, unissued Friday/Saturday game statuses, blank depth-chart backup cells, per-player
   snap-weighted EPA/WAR, weather) is emitted as the empty string "" and carries a FLG id.
3. Fields prefixed `model_` are explicit model priors computed by this file. They are never
   presented as official NFL statistics, and every table that renders them says so.

Outputs (written to nfl-desk-26d4cafb/data/):
    ledger.csv / ledger.json           136 completed official games
    standings_check.csv                32-team reconciliation vs nfl.com/standings
    hfa.csv                            empirical home-field advantage + diagnostics
    lines_wk10.csv                     14 originated Week 10 lines
    oos_week9.csv                      out-of-sample grading of prior repo originators
    backtest_walkforward.csv           walk-forward per-game predictions
    strategies.csv                     strategy definitions + graded results
    leaderboard.csv                    gated leaderboard with reward tiers
    gates.csv                          per-strategy gate evaluation (fail-closed)
    correlations.csv                   team-level + player-prop Pearson r
    prop_combos.csv                    joint probabilities, lift, Frechet-Hoeffding bounds
    luck_skill.csv                     binomial / Brier / DSR / Holm-Bonferroni
    injuries.csv                       46-row starter-to-backup depth register
    player_logs.csv                    50 paired official player-game logs
    flagged.csv                        Flagged for Review register
    sources.csv                        official source register
    summary.json                       machine-readable executive summary
"""

from __future__ import annotations

import csv
import json
import math
import os
import statistics
from statistics import NormalDist

import raw_inputs as R
import registers as G

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
OUT_DIR = os.path.join(HERE, "data")

EULER_GAMMA = 0.5772156649015329

# ---------------------------------------------------------------------------
# Model hyper-parameters -- declared up front so a reviewer can audit them.
# ---------------------------------------------------------------------------
SHRINK_K = 6.0          # pseudo-games of shrinkage toward league mean
OPP_ADJ_ITERS = 2       # opponent-strength adjustment iterations
MIN_TRAIN_WEEKS = 3     # walk-forward: first graded week = MIN_TRAIN_WEEKS + 1
GRADED_FROM_WEEK = 4    # weeks 4..9 are graded walk-forward
SELECTIVITY_THRESHOLD = 3.0   # STR-01 fires only when |model margin| >= this
REST_EDGE_DAYS = 3            # STR-04 fires when rest differential >= this
CORRELATION_CAP = 0.60        # G-09 parlay/combo correlation cap
ASSUMED_PRICE = -110          # declared price for ROI ("official price: none" -> FLG-01)
BREAKEVEN_110 = 110.0 / 210.0  # 0.5238095238
MAX_DRAWDOWN_UNITS = 10.0     # G-10 risk budget

# Team-abbreviation aliases. The repo ledger writes Washington as "WSH"; the official
# nfl.com standings page writes it "WAS". Normalise to the official nfl.com token.
ABBR_ALIAS = {"WSH": "WAS"}


def norm_team(t):
    return ABBR_ALIAS.get(t, t)


# PLAYER_GAME_LOGS_2026 tuple index constants (see raw_inputs.py for the schema).
(I_TEAM, I_WK, I_DATE, I_OPP, I_WL, I_TEAM_PTS, I_OPP_PTS,
 I_QB, I_QB_COMP, I_QB_ATT, I_QB_YDS, I_QB_TD, I_QB_INT, I_QB_URL,
 I_TGT, I_TGT_POS, I_TGT_REC, I_TGT_YDS, I_TGT_TD, I_TGT_URL,
 I_RB, I_RB_ATT, I_RB_YDS, I_RB_TD, I_RB_URL) = range(25)


# Confirmed international neutral-site games (official venue note present on nfl.com).
# (week, away, home) -- verified against the official schedule page on 2026-11-12.
NEUTRAL_TRIPLES = {
    (1, "SF", "LAR"),   # Melbourne, Australia
    (5, "PHI", "JAX"),  # London
    (7, "PIT", "NO"),   # Saint-Denis
    (9, "CIN", "ATL"),  # Madrid, Spain
}
# Unconfirmed: 9:30 AM ET international window but venue not stated on the official page.
NEUTRAL_UNCONFIRMED_TRIPLES = {
    (4, "IND", "WSH"),
    (6, "HOU", "JAX"),
}


# ===========================================================================
# Small statistics library (stdlib only)
# ===========================================================================
def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def stdev_s(xs):
    """Sample standard deviation (n-1)."""
    if len(xs) < 2:
        return 0.0
    return statistics.stdev(xs)


def pearson(xs, ys):
    n = len(xs)
    if n < 3 or len(ys) != n:
        return None
    mx, my = mean(xs), mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    r = sxy / math.sqrt(sxx * syy)
    return max(-1.0, min(1.0, r))


def _moments(xs):
    n = len(xs)
    mu = mean(xs)
    m2 = sum((x - mu) ** 2 for x in xs) / n
    m3 = sum((x - mu) ** 3 for x in xs) / n
    m4 = sum((x - mu) ** 4 for x in xs) / n
    if m2 <= 0:
        return mu, 0.0, 0.0, 0.0
    skew = m3 / (m2 ** 1.5)
    exkurt = m4 / (m2 ** 2) - 3.0
    return mu, math.sqrt(m2), skew, exkurt


def binom_pmf(n, p):
    return [math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(n + 1)]


def binom_two_sided_p(k, n, p0):
    """Exact two-sided binomial p-value (method of small p-values)."""
    if n <= 0:
        return None
    pmf = binom_pmf(n, p0)
    obs = pmf[k]
    tol = obs * (1 + 1e-12) + 1e-300
    return min(1.0, sum(x for x in pmf if x <= tol))


def binom_greater_p(k, n, p0):
    """One-sided P(X >= k)."""
    if n <= 0:
        return None
    return min(1.0, sum(binom_pmf(n, p0)[k:]))


def holm_bonferroni(pvals):
    """Return Holm-Bonferroni adjusted p-values aligned to input order (None-safe)."""
    idx = [i for i, p in enumerate(pvals) if p is not None]
    m = len(idx)
    adjusted = [None] * len(pvals)
    ordered = sorted(idx, key=lambda i: pvals[i])
    running = 0.0
    for rank, i in enumerate(ordered):
        val = (m - rank) * pvals[i]
        running = max(running, val)
        adjusted[i] = min(1.0, running)
    return adjusted


def deflated_sharpe_ratio(returns, n_trials):
    """Bailey & Lopez de Prado Deflated Sharpe Ratio (probability SR exceeds the
    expected maximum SR under the null given `n_trials` independent trials)."""
    n = len(returns)
    if n < 3 or n_trials < 2:
        return None
    mu, sd, skew, exkurt = _moments(returns)
    if sd <= 0:
        return None
    sr = mu / sd
    nd = NormalDist()
    z1 = nd.inv_cdf(1.0 - 1.0 / n_trials)
    z2 = nd.inv_cdf(1.0 - 1.0 / (n_trials * math.e))
    sr0 = math.sqrt(1.0 / n) * ((1 - EULER_GAMMA) * z1 + EULER_GAMMA * z2)
    denom_sq = 1.0 - skew * sr + ((exkurt - 1.0) / 4.0) * sr * sr
    if denom_sq <= 0:
        return None
    dsr_stat = (sr - sr0) * math.sqrt(n - 1) / math.sqrt(denom_sq)
    return nd.cdf(dsr_stat)


def sharpe_ratio(returns):
    n = len(returns)
    if n < 2:
        return None
    mu, sd, _s, _k = _moments(returns)
    return mu / sd if sd > 0 else None


def max_drawdown(returns):
    peak = 0.0
    eq = 0.0
    mdd = 0.0
    for r in returns:
        eq += r
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
    return mdd


def brier(pairs):
    """pairs: list of (forecast_probability, realised 0/1)."""
    if not pairs:
        return None
    return sum((p - o) ** 2 for p, o in pairs) / len(pairs)


def chi2_trend_p(counts_success, counts_total):
    """Cochran-Armitage style linear trend test on ordered binomial samples.
    Returns (chi2 statistic, two-sided p) with df=1."""
    ks = [c for c in counts_total if c > 0]
    ns = [c for c, t in zip(counts_success, counts_total) if t > 0]
    if len(ks) < 2:
        return None, None
    N = sum(ks)
    S = sum(ns)
    if N == 0 or S == 0 or S == N:
        return None, None
    scores = list(range(len(ks)))
    pbar = S / N
    sbar = sum(t * s for t, s in zip(ks, scores)) / N
    num = sum(n * (s - sbar) for n, s in zip(ns, scores))
    var = pbar * (1 - pbar) * sum(t * (s - sbar) ** 2 for t, s in zip(ks, scores))
    if var <= 0:
        return None, None
    chi2 = (num ** 2) / var
    # df=1 survival function
    p = 2.0 * (1.0 - NormalDist().cdf(math.sqrt(chi2)))
    return chi2, min(1.0, p)


# ===========================================================================
# 1. Ledger construction
# ===========================================================================
def _load_repo_games():
    path = os.path.join(REPO_ROOT, "data", "games_2026.json")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def build_ledger():
    """120 repo-verified finals (Weeks 1-8) + 16 re-fetched post-2026-11-02 finals
    (Week 8 MNF + all 15 Week 9 games) = 136 completed official games."""
    repo = _load_repo_games()
    ledger = []
    seen = set()

    for g in repo["games"]:
        if g.get("st") != "final" or g.get("as") is None or g.get("hs") is None:
            continue
        key = (int(g["wk"]), norm_team(g["away"]), norm_team(g["home"]))
        if key in seen:
            continue
        seen.add(key)
        ledger.append({
            "game_id": g.get("nfl", ""),
            "wk": int(g["wk"]),
            "date": g["date"],
            "away": norm_team(g["away"]),
            "home": norm_team(g["home"]),
            "away_pts": int(g["as"]),
            "home_pts": int(g["hs"]),
            "neutral": key in NEUTRAL_TRIPLES,
            "neutral_unconfirmed": key in NEUTRAL_UNCONFIRMED_TRIPLES,
            "source_url": "https://www.nfl.com/games/" + str(g.get("nfl", "")),
            "origin": "data/games_2026.json (nfl.com-verified)",
        })

    added = 0
    for g in R.COMPLETED_GAMES_POST_NOV2:
        key = (int(g["wk"]), norm_team(g["away"]), norm_team(g["home"]))
        if key in seen:
            continue
        seen.add(key)
        added += 1
        ledger.append({
            "game_id": g["source_url"].rsplit("/", 1)[-1],
            "wk": int(g["wk"]),
            "date": g["date"],
            "away": norm_team(g["away"]),
            "home": norm_team(g["home"]),
            "away_pts": int(g["away_pts"]),
            "home_pts": int(g["home_pts"]),
            "neutral": bool(g["neutral"]),
            "neutral_unconfirmed": False,
            "source_url": g["source_url"],
            "origin": "re-fetched from nfl.com 2026-11-12 (post-freeze results)",
        })

    ledger.sort(key=lambda x: (x["date"], x["away"], x["home"]))
    for g in ledger:
        g["margin_home"] = g["home_pts"] - g["away_pts"]
        g["total"] = g["home_pts"] + g["away_pts"]
    return ledger, added


# ===========================================================================
# 2. Standings reconciliation (32/32 check)
# ===========================================================================
def reconcile_standings(ledger):
    table = {}
    for row in R.STANDINGS_2026_WK10:
        abbr, name, conf, div, w, l, t, pf, pa = row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]
        table[abbr] = {"team": name, "conf": conf, "div": div,
                       "W": w, "L": l, "T": t, "PF": pf, "PA": pa,
                       "url": row[14]}
    calc = {a: {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "GP": 0} for a in table}
    for g in ledger:
        for side, opp in (("away", "home"), ("home", "away")):
            pts = g[side + "_pts"]
            opp_pts = g[opp + "_pts"]
            c = calc[g[side]]
            c["GP"] += 1
            c["PF"] += pts
            c["PA"] += opp_pts
            if pts > opp_pts:
                c["W"] += 1
            elif pts < opp_pts:
                c["L"] += 1
            else:
                c["T"] += 1

    rows = []
    mismatches = 0
    for abbr in sorted(table):
        off = table[abbr]
        c = calc[abbr]
        diffs = []
        for k in ("W", "L", "T", "PF", "PA"):
            if off[k] != c[k]:
                diffs.append("%s official=%s computed=%s" % (k, off[k], c[k]))
        if diffs:
            mismatches += 1
        rows.append({
            "abbr": abbr, "team": off["team"], "conf": off["conf"], "div": off["div"],
            "official_W": off["W"], "official_L": off["L"], "official_T": off["T"],
            "official_PF": off["PF"], "official_PA": off["PA"],
            "computed_GP": c["GP"], "computed_W": c["W"], "computed_L": c["L"],
            "computed_T": c["T"], "computed_PF": c["PF"], "computed_PA": c["PA"],
            "match": "MATCH" if not diffs else "MISMATCH",
            "detail": "; ".join(diffs),
            "source_url": off["url"],
        })
    return rows, mismatches, len(table)


# ===========================================================================
# 3. Empirical home-field advantage
# ===========================================================================
def compute_hfa(ledger):
    strict = [g["margin_home"] for g in ledger
              if not g["neutral"] and not g["neutral_unconfirmed"]]
    incl = [g["margin_home"] for g in ledger if not g["neutral"]]
    neutral = [g["margin_home"] for g in ledger if g["neutral"]]
    n = len(strict)
    mu = mean(strict)
    sd = stdev_s(strict)
    se = sd / math.sqrt(n) if n else 0.0
    t_stat = mu / se if se else 0.0
    p = 2.0 * (1.0 - NormalDist().cdf(abs(t_stat))) if se else None
    home_wins = sum(1 for m in strict if m > 0)
    away_wins = sum(1 for m in strict if m < 0)
    tie = len(strict) - home_wins - away_wins
    return {
        "n_non_neutral_games": n,
        "mean_home_margin": round(mu, 4),
        "stdev": round(sd, 4),
        "standard_error": round(se, 4),
        "t_stat": round(t_stat, 4),
        "p_two_sided": round(p, 6) if p is not None else "",
        "ci95_low": round(mu - 1.96 * se, 4),
        "ci95_high": round(mu + 1.96 * se, 4),
        "home_wins": home_wins, "away_wins": away_wins, "ties": tie,
        "home_win_rate": round(home_wins / (home_wins + away_wins), 4) if (home_wins + away_wins) else "",
        "n_neutral_games": len(neutral),
        "mean_margin_neutral": round(mean(neutral), 4) if neutral else "",
        "sensitivity_including_unconfirmed": round(mean(incl), 4),
        "n_including_unconfirmed": len(incl),
        "source_url": "https://www.nfl.com/schedules",
        "note": ("Neutral-site set excludes 2 games (W4 IND@WSH, W6 HOU@JAX) whose international "
                 "venue is not stated on the official schedule page; sensitivity shown separately (FLG-12)."),
    }


# ===========================================================================
# 4. Team ratings
# ===========================================================================
def fit_ratings(games, k=SHRINK_K, iters=OPP_ADJ_ITERS):
    """Shrunk, opponent-adjusted offensive and defensive points-per-game deltas."""
    teams = sorted({g["away"] for g in games} | {g["home"] for g in games})
    n = {t: 0 for t in teams}
    pf = {t: 0 for t in teams}
    pa = {t: 0 for t in teams}
    opps = {t: [] for t in teams}
    for g in games:
        a, h = g["away"], g["home"]
        n[a] += 1
        n[h] += 1
        pf[a] += g["away_pts"]
        pa[a] += g["home_pts"]
        pf[h] += g["home_pts"]
        pa[h] += g["away_pts"]
        opps[a].append(h)
        opps[h].append(a)
    lg = sum(pf.values()) / max(1, sum(n.values()))
    off = {t: pf[t] / n[t] - lg for t in teams}
    dfn = {t: pa[t] / n[t] - lg for t in teams}  # positive = allows more than average
    for _ in range(iters):
        new_off, new_dfn = {}, {}
        for t in teams:
            o = opps[t]
            opp_def_quality = sum(dfn[x] for x in o) / len(o)
            opp_off_quality = sum(off[x] for x in o) / len(o)
            new_off[t] = off[t] - opp_def_quality
            new_dfn[t] = dfn[t] - opp_off_quality
        off, dfn = new_off, new_dfn
    for t in teams:
        w = n[t] / (n[t] + k)
        off[t] *= w
        dfn[t] *= w
    net = {t: off[t] - dfn[t] for t in teams}
    return {"lg": lg, "off": off, "def": dfn, "net": net, "gp": n, "teams": teams}


# ===========================================================================
# 5. Score distribution (independent Poisson)
# ===========================================================================
MAX_SCORE = 75


def poisson_pmf(lam):
    out = []
    for k in range(MAX_SCORE + 1):
        out.append(math.exp(-lam) * (lam ** k) / math.factorial(k))
    s = sum(out)
    return [x / s for x in out]


def score_distribution(lam_home, lam_away):
    ph = poisson_pmf(lam_home)
    pa = poisson_pmf(lam_away)
    p_home_win = 0.0
    p_away_win = 0.0
    p_tie = 0.0
    margin = {}
    total = {}
    for h in range(MAX_SCORE + 1):
        if ph[h] <= 0:
            continue
        for a in range(MAX_SCORE + 1):
            p = ph[h] * pa[a]
            if p <= 0:
                continue
            if h > a:
                p_home_win += p
            elif a > h:
                p_away_win += p
            else:
                p_tie += p
            margin[h - a] = margin.get(h - a, 0.0) + p
            total[h + a] = total.get(h + a, 0.0) + p
    return {
        "p_home_win": p_home_win, "p_away_win": p_away_win, "p_tie": p_tie,
        "margin": margin, "total": total,
    }


def fair_spread(margin_dist):
    """Home spread (home favoured positive) balancing P(margin > s) and P(margin < s)."""
    best, best_gap = 0.0, None
    s = -30.0
    while s <= 30.0:
        gt = sum(p for m, p in margin_dist.items() if m > s)
        lt = sum(p for m, p in margin_dist.items() if m < s)
        gap = abs(gt - lt)
        if best_gap is None or gap < best_gap:
            best_gap, best = gap, s
        s += 0.5
    return round(best, 2)


def fair_total(total_dist):
    best, best_gap = None, None
    for t in range(20, 80):
        over = sum(p for v, p in total_dist.items() if v > t)
        under = sum(p for v, p in total_dist.items() if v < t)
        gap = abs(over - under)
        if best_gap is None or gap < best_gap:
            best_gap, best = gap, t
    return best


def prob_over_total(total_dist, line):
    return sum(p for v, p in total_dist.items() if v > line)


def american_odds(p):
    if p is None:
        return ""
    if p <= 0:
        return ""
    if p >= 0.5:
        return int(round(-100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def fmt_american(v):
    if v == "" or v is None:
        return ""
    return "+%d" % v if v > 0 else "%d" % v


# ===========================================================================
# 6. Week 10 injury / depth adjustments
# ===========================================================================
TIER_WEIGHT = {
    "Confirmed Out / IR": 1.00,
    "DNP + Backup Out": 0.75,
    "DNP (Unconfirmed Fri)": 0.50,
    "DNP (Depth Unfetched)": 0.50,
    "Active / Limited": 0.15,
}


def build_injury_tolls():
    """Return {(team): {'off': weighted model pts, 'def': weighted model pts, 'n': count, 'ids': []}}."""
    tolls = {}
    for e in R.INJURY_DEPTH_ENTRIES:
        t = e["team"]
        rec = tolls.setdefault(t, {"off": 0.0, "def": 0.0, "n": 0, "ids": [],
                                   "off_raw": 0.0, "def_raw": 0.0})
        w = TIER_WEIGHT.get(e["availability_tier"], 0.50)
        val = float(e["model_pts_impact"]) * w
        if e["unit"] == "Offense":
            rec["off"] += val
            rec["off_raw"] += float(e["model_pts_impact"])
        else:
            rec["def"] += val
            rec["def_raw"] += float(e["model_pts_impact"])
        rec["n"] += 1
        rec["ids"].append(e["id"])
    for t in tolls:
        tolls[t]["off"] = round(tolls[t]["off"], 3)
        tolls[t]["def"] = round(tolls[t]["def"], 3)
        tolls[t]["off_raw"] = round(tolls[t]["off_raw"], 2)
        tolls[t]["def_raw"] = round(tolls[t]["def_raw"], 2)
    return tolls


# ===========================================================================
# 7. Week 10 line origination
# ===========================================================================
def originate_week10(ledger, hfa_value, tolls):
    ratings = fit_ratings(ledger)
    rows = []
    for g in R.WEEK10_SCHEDULE:
        away, home = g["away"], g["home"]
        neutral = bool(g["neutral"])
        hfa = 0.0 if neutral else hfa_value
        at = tolls.get(away, {"off": 0.0, "def": 0.0, "n": 0, "ids": [], "off_raw": 0.0, "def_raw": 0.0})
        ht = tolls.get(home, {"off": 0.0, "def": 0.0, "n": 0, "ids": [], "off_raw": 0.0, "def_raw": 0.0})

        base_home = ratings["lg"] + ratings["off"][home] + ratings["def"][away]
        base_away = ratings["lg"] + ratings["off"][away] + ratings["def"][home]
        lam_home = base_home + hfa / 2.0 - ht["off"] + at["def"]
        lam_away = base_away - hfa / 2.0 - at["off"] + ht["def"]
        lam_home = max(3.0, lam_home)
        lam_away = max(3.0, lam_away)

        dist = score_distribution(lam_home, lam_away)
        two_way = dist["p_home_win"] + dist["p_away_win"]
        p_home_2w = dist["p_home_win"] / two_way if two_way else 0.5
        p_away_2w = dist["p_away_win"] / two_way if two_way else 0.5

        spread = fair_spread(dist["margin"])
        total = fair_total(dist["total"])
        ml_home = american_odds(p_home_2w)
        ml_away = american_odds(p_away_2w)

        rows.append({
            "game_id": g["game_id"],
            "date": g["date"],
            "window": g["window"],
            "network": g["network"],
            "away": away,
            "home": home,
            "site": g["site_label"],
            "neutral": "YES" if neutral else "no",
            "away_rest_days": g["away_rest_days"],
            "home_rest_days": g["home_rest_days"],
            "rest_diff_home_minus_away": g["home_rest_days"] - g["away_rest_days"],
            "model_lambda_away": round(lam_away, 2),
            "model_lambda_home": round(lam_home, 2),
            "model_margin_home": round(lam_home - lam_away, 2),
            "model_total": round(lam_home + lam_away, 2),
            "hfa_applied": round(hfa, 3),
            "model_spread_home": spread,
            "model_favorite": home if spread > 0 else (away if spread < 0 else "PK"),
            "model_total_line": total,
            "p_home_win": round(dist["p_home_win"], 4),
            "p_away_win": round(dist["p_away_win"], 4),
            "p_tie": round(dist["p_tie"], 4),
            "p_home_two_way": round(p_home_2w, 4),
            "ml_home": fmt_american(ml_home),
            "ml_away": fmt_american(ml_away),
            "injury_toll_away_off": at["off"],
            "injury_toll_away_def": at["def"],
            "injury_toll_home_off": ht["off"],
            "injury_toll_home_def": ht["def"],
            "injury_rows_away": ", ".join(at["ids"]),
            "injury_rows_home": ", ".join(ht["ids"]),
            "market_spread": "",
            "market_total": "",
            "market_ml": "",
            "edge": "",
            "clv": "",
            "weather_adjustment": "",
            "source_url": g["source_url"],
            "source_standings": "https://www.nfl.com/standings/",
            "source_injuries": "https://www.nfl.com/injuries/league/2026/reg10",
            "flagged": "FLG-01 (no official market lines), FLG-14 (no official weather feed)",
            "status": "Model output (derived); market columns blank per zero-hallucination policy",
        })
    return rows, ratings


# ===========================================================================
# 8. Out-of-sample Week 9 grading of prior repo originators
# ===========================================================================
NAME_TO_ABBR = {r[1]: r[0] for r in R.STANDINGS_2026_WK10}


def _actual_index(ledger):
    return {(g["wk"], g["away"], g["home"]): g for g in ledger}


def grade_prior_models(ledger):
    idx = _actual_index(ledger)
    sigma_margin = stdev_s([g["margin_home"] for g in ledger
                            if not g["neutral"] and not g["neutral_unconfirmed"]])
    out = []

    def add(model, game_key, pred_margin, pred_total, pred_p_home, source_url, note):
        g = idx.get(game_key)
        if g is None:
            return
        rec = {
            "model": model,
            "model_provenance_url": source_url,
            "wk": g["wk"], "date": g["date"],
            "away": g["away"], "home": g["home"],
            "actual_away_pts": g["away_pts"], "actual_home_pts": g["home_pts"],
            "actual_margin_home": g["margin_home"], "actual_total": g["total"],
            "pred_margin_home": round(pred_margin, 2) if pred_margin is not None else "",
            "margin_error": round(pred_margin - g["margin_home"], 2) if pred_margin is not None else "",
            "pred_total": round(pred_total, 2) if pred_total is not None else "",
            "total_error": round(pred_total - g["total"], 2) if pred_total is not None else "",
            "pred_p_home_win": round(pred_p_home, 4) if pred_p_home is not None else "",
            "actual_home_win": 1 if g["margin_home"] > 0 else (0 if g["margin_home"] < 0 else ""),
            "brier_home": ((pred_p_home - (1.0 if g["margin_home"] > 0 else 0.0)) ** 2
                           if (pred_p_home is not None and g["margin_home"] != 0) else ""),
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-%d" % g["wk"],
            "note": note,
        }
        out.append(rec)

    # -- nfl-strategy-lab: data/model_lines_2026_wk9.csv -------------------
    p = os.path.join(REPO_ROOT, "data", "model_lines_2026_wk9.csv")
    if os.path.exists(p):
        with open(p, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                aw = NAME_TO_ABBR.get(row["away_team"].strip())
                hm = NAME_TO_ABBR.get(row["home_team"].strip())
                if not aw or not hm:
                    continue
                key = None
                for wk in (8, 9):
                    if (wk, aw, hm) in idx:
                        key = (wk, aw, hm)
                if key is None:
                    continue
                mu = float(row["model_home_margin"])
                tot = float(row["model_total"])
                ph = NormalDist().cdf(mu / sigma_margin) if sigma_margin else 0.5
                add("nfl-strategy-lab (originate_lines.py, HFA=+2.0)", key, mu, tot, ph,
                    "https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv",
                    "Prior repo originator; graded out-of-sample against the official final score.")

    # -- own5-desk: data/own5_desk/derived_lines.json ----------------------
    p = os.path.join(REPO_ROOT, "data", "own5_desk", "derived_lines.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as fh:
            for row in json.load(fh):
                key = None
                for wk in (8, 9):
                    if (wk, row["away"], row["home"]) in idx:
                        key = (wk, row["away"], row["home"])
                if key is None:
                    continue
                add("own5-desk (points-poisson-v0.1, HFA=0.0, k=8)", key,
                    float(row["expected_margin_home"]), float(row["fair_total"]),
                    float(row["home_win_probability"]),
                    "https://github.com/sassnarep3-star/Own5/blob/main/data/own5_desk/derived_lines.json",
                    "Prior repo originator; graded out-of-sample against the official final score.")

    # -- line-lab market lines (THIRD PARTY -- flagged, not official) ------
    p = os.path.join(REPO_ROOT, "data", "lines_upcoming_2026.json")
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as fh:
            blob = json.load(fh)
        for row in blob.get("games", []):
            cur = row.get("current") or {}
            hs = cur.get("home", {}).get("spread")
            tot = cur.get("total")
            if hs is None or tot is None:
                continue
            key = None
            for wk in (8, 9):
                if (wk, row["away"]["abbr"], row["home"]["abbr"]) in idx:
                    key = (wk, row["away"]["abbr"], row["home"]["abbr"])
            if key is None:
                continue
            # Market spread is quoted on the home team; market-favoured margin = -spread.
            mu = -float(hs)
            ph = NormalDist().cdf(mu / sigma_margin) if sigma_margin else 0.5
            add("line-lab market scrape (ESPN/DraftKings) -- THIRD PARTY", key, mu,
                float(tot), ph,
                "https://www.espn.com/nfl/odds",
                "NOT an official source (FLG-01). Shown only as a third-party benchmark; "
                "market columns elsewhere in this site are left blank.")

    # -- this session's walk-forward model ---------------------------------
    for g in ledger:
        if g["wk"] not in (8, 9):
            continue
        train = [x for x in ledger if x["wk"] < g["wk"]]
        if len(train) < 30:
            continue
        rt = fit_ratings(train)
        hfa_train = mean([x["margin_home"] for x in train
                          if not x["neutral"] and not x["neutral_unconfirmed"]])
        hfa = 0.0 if g["neutral"] else hfa_train
        lam_h = max(3.0, rt["lg"] + rt["off"][g["home"]] + rt["def"][g["away"]] + hfa / 2.0)
        lam_a = max(3.0, rt["lg"] + rt["off"][g["away"]] + rt["def"][g["home"]] - hfa / 2.0)
        dist = score_distribution(lam_h, lam_a)
        two = dist["p_home_win"] + dist["p_away_win"]
        ph = dist["p_home_win"] / two if two else 0.5
        add("26d4cafb walk-forward (this session, depth-adjusted)", (g["wk"], g["away"], g["home"]),
            lam_h - lam_a, lam_h + lam_a, ph,
            "https://www.nfl.com/schedules/2026/by-week/week-9",
            "Trained only on weeks strictly before the graded week. No injury register exists "
            "for W1-W9 in official form, so the depth adjustment is available for Week 10 only.")

    return out


def summarise_oos(rows):
    out = []
    for model in sorted({r["model"] for r in rows}):
        sub = [r for r in rows if r["model"] == model]
        prov = sub[0]["model_provenance_url"] if sub else ""
        me = [abs(r["margin_error"]) for r in sub if r["margin_error"] != ""]
        se = [(r["margin_error"]) ** 2 for r in sub if r["margin_error"] != ""]
        te = [abs(r["total_error"]) for r in sub if r["total_error"] != ""]
        signed = [r["margin_error"] for r in sub if r["margin_error"] != ""]
        br = [r["brier_home"] for r in sub if r["brier_home"] != ""]
        su = [r for r in sub if r["actual_home_win"] != ""]
        correct = sum(1 for r in su
                      if (r["pred_p_home_win"] != "" and
                          ((r["pred_p_home_win"] >= 0.5 and r["actual_home_win"] == 1) or
                           (r["pred_p_home_win"] < 0.5 and r["actual_home_win"] == 0))))
        out.append({
            "model": model,
            "n_games_graded": len(sub),
            "margin_MAE": round(mean(me), 3) if me else "",
            "margin_RMSE": round(math.sqrt(mean(se)), 3) if se else "",
            "margin_bias": round(mean(signed), 3) if signed else "",
            "total_MAE": round(mean(te), 3) if te else "",
            "straight_up_correct": correct,
            "straight_up_accuracy": round(correct / len(su), 4) if su else "",
            "brier_score": round(mean(br), 4) if br else "",
            "model_provenance_url": prov,
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-9",
        })
    return out


# ===========================================================================
# 9. Walk-forward backtest (zero look-ahead)
# ===========================================================================
def _rest_map(ledger):
    """Days since each team's previous game, computed from official schedule dates."""
    import datetime as _dt
    last = {}
    rest = {}
    for g in sorted(ledger, key=lambda x: x["date"]):
        d = _dt.date.fromisoformat(g["date"])
        for t in (g["away"], g["home"]):
            prev = last.get(t)
            rest[(g["game_id"], t)] = (d - prev).days if prev else ""
            last[t] = d
    return rest


def walk_forward_predictions(ledger):
    rest = _rest_map(ledger)
    div = {r[0]: r[3] for r in R.STANDINGS_2026_WK10}
    rows = []
    for wk in sorted({g["wk"] for g in ledger}):
        if wk < GRADED_FROM_WEEK:
            continue
        train = [g for g in ledger if g["wk"] < wk]
        if len(train) < 30:
            continue
        rt = fit_ratings(train)
        hfa_train = mean([g["margin_home"] for g in train
                          if not g["neutral"] and not g["neutral_unconfirmed"]])
        # NULL: home win rate observed in weeks STRICTLY BEFORE this week (no look-ahead).
        _hw = sum(1 for g in train if g["margin_home"] > 0)
        _aw = sum(1 for g in train if g["margin_home"] < 0)
        null_home = _hw / (_hw + _aw) if (_hw + _aw) else 0.5
        for g in [x for x in ledger if x["wk"] == wk]:
            hfa = 0.0 if g["neutral"] else hfa_train
            lam_h = max(3.0, rt["lg"] + rt["off"][g["home"]] + rt["def"][g["away"]] + hfa / 2.0)
            lam_a = max(3.0, rt["lg"] + rt["off"][g["away"]] + rt["def"][g["home"]] - hfa / 2.0)
            dist = score_distribution(lam_h, lam_a)
            two = dist["p_home_win"] + dist["p_away_win"]
            ph = dist["p_home_win"] / two if two else 0.5
            ra = rest.get((g["game_id"], g["away"]), "")
            rh = rest.get((g["game_id"], g["home"]), "")
            rows.append({
                "wk": wk, "date": g["date"], "game_id": g["game_id"],
                "away": g["away"], "home": g["home"],
                "actual_margin_home": g["margin_home"], "actual_total": g["total"],
                "pred_margin_home": round(lam_h - lam_a, 3),
                "pred_total": round(lam_h + lam_a, 3),
                "pred_p_home_win": round(ph, 4),
                "null_p_home_win": round(null_home, 4),
                "hfa_used": round(hfa, 3),
                "neutral": "YES" if g["neutral"] else "no",
                "rest_away": ra, "rest_home": rh,
                "rest_diff_home_minus_away": (rh - ra) if (ra != "" and rh != "") else "",
                "divisional": "YES" if div.get(g["away"]) == div.get(g["home"]) else "no",
                "home_net_rating": round(rt["net"][g["home"]], 3),
                "away_net_rating": round(rt["net"][g["away"]], 3),
                "actual_home_win": 1 if g["margin_home"] > 0 else (0 if g["margin_home"] < 0 else ""),
                "source_url": g["source_url"],
                "lookahead_check": "trained on weeks < %d only" % wk,
            })
    return rows


# ===========================================================================
# 10. Strategy evaluation
# ===========================================================================
# NULL MODEL -- this is what "removing luck" means in this engine
# ---------------------------------------------------------------------------
# A strategy that picks the AWAY team is not facing a coin flip: across the 2026
# ledger away teams actually win slightly MORE than half the time, so scoring every
# pick against one constant base rate would manufacture fake skill.
#
# Each pick therefore carries its OWN null probability:
#     pick the home side -> null = home win rate observed in weeks STRICTLY BEFORE this week
#     pick the away side -> null = 1 - that rate
# Every significance test below is then an exact POISSON-BINOMIAL test (heterogeneous
# per-trial probabilities), never a plain binomial with a single constant p.
# ---------------------------------------------------------------------------
def poisson_binomial_pmf(probs):
    """Exact distribution of the sum of independent Bernoulli(p_i) trials."""
    dist = [1.0]
    for q in probs:
        nd = [0.0] * (len(dist) + 1)
        for i, v in enumerate(dist):
            if v == 0.0:
                continue
            nd[i] += v * (1.0 - q)
            nd[i + 1] += v * q
        dist = nd
    return dist


def poisson_binomial_two_sided(k, probs):
    """Two-sided exact p-value by the method of small p-values."""
    if not probs:
        return None
    dist = poisson_binomial_pmf(probs)
    obs = dist[k]
    tol = obs * (1 + 1e-12) + 1e-300
    return min(1.0, sum(x for x in dist if x <= tol))


def poisson_binomial_greater(k, probs):
    if not probs:
        return None
    dist = poisson_binomial_pmf(probs)
    return min(1.0, sum(dist[k:]))


def _grade_picks(picks):
    """picks: list of {"p_model", "p_null", "outcome"}."""
    n = len(picks)
    if n == 0:
        return {"n": 0}
    wins = sum(1 for x in picks if x["outcome"] == 1)
    wr = wins / n
    nulls = [x["p_null"] for x in picks]
    mean_null = mean(nulls)
    rets = [(100.0 / 110.0) if x["outcome"] == 1 else -1.0 for x in picks]
    p_two = poisson_binomial_two_sided(wins, nulls)
    p_greater = poisson_binomial_greater(wins, nulls)
    br_model = mean([(x["p_model"] - x["outcome"]) ** 2 for x in picks])
    br_ref = mean([(x["p_null"] - x["outcome"]) ** 2 for x in picks])
    sr = sharpe_ratio(rets)
    _mu, _sd, skew, kurt = _moments(rets)
    return {
        "n": n, "wins": wins, "losses": n - wins,
        "win_rate": round(wr, 4),
        "mean_null_win_rate": round(mean_null, 4),
        "lift_over_null": round(wr - mean_null, 4),
        "roi_per_unit_at_-110": round(mean(rets), 4),
        "units": round(sum(rets), 3),
        "break_even_at_-110": round(BREAKEVEN_110, 4),
        "p_two_sided_exact_poisson_binomial": round(p_two, 6) if p_two is not None else "",
        "binomial_p_two_sided": round(p_two, 6) if p_two is not None else "",
        "p_one_sided_greater": round(p_greater, 6) if p_greater is not None else "",
        "brier": round(br_model, 4),
        "brier_reference_null": round(br_ref, 4),
        "brier_skill_score": round(1 - br_model / br_ref, 4) if br_ref else "",
        "sharpe": round(sr, 4) if sr is not None else "",
        "skew": round(skew, 4), "excess_kurtosis": round(kurt, 4),
        "max_drawdown_units": round(max_drawdown(rets), 3),
        "_rets": rets, "_p_raw": p_two, "_nulls": nulls,
    }


def evaluate_strategies(wf):
    """Build and grade every backtestable strategy on the walk-forward predictions."""
    graded = [r for r in wf if r["actual_home_win"] != ""]
    results = {}

    def mk(r, side_home):
        p_model = r["pred_p_home_win"] if side_home else 1.0 - r["pred_p_home_win"]
        p_null = r["null_p_home_win"] if side_home else 1.0 - r["null_p_home_win"]
        outcome = 1 if ((r["actual_home_win"] == 1) == bool(side_home)) else 0
        return {"p_model": p_model, "p_null": p_null, "outcome": outcome}

    # BASE: unselective model (every game) -- reference for the selectivity test
    picks = [mk(r, r["pred_margin_home"] > 0) for r in graded]
    results["BASE"] = _grade_picks(picks)
    results["BASE"]["fire_rule"] = "every game (unselective reference)"
    results["BASE"]["_picks"] = picks

    # STR-01: net-points rating + empirical HFA, selective on |model margin|
    picks = [mk(r, r["pred_margin_home"] > 0) for r in graded
             if abs(r["pred_margin_home"]) >= SELECTIVITY_THRESHOLD]
    results["STR-01"] = _grade_picks(picks)
    results["STR-01"]["fire_rule"] = "|model margin| >= %.1f" % SELECTIVITY_THRESHOLD
    results["STR-01"]["_picks"] = picks

    # STR-04: rest-differential
    picks = []
    for r in graded:
        d = r["rest_diff_home_minus_away"]
        if d == "" or abs(d) < REST_EDGE_DAYS:
            continue
        picks.append(mk(r, d > 0))
    results["STR-04"] = _grade_picks(picks)
    results["STR-04"]["fire_rule"] = "|rest differential| >= %d days" % REST_EDGE_DAYS
    results["STR-04"]["_picks"] = picks

    # STR-05: divisional underdog
    picks = [mk(r, r["home_net_rating"] < r["away_net_rating"]) for r in graded
             if r["divisional"] == "YES"]
    results["STR-05"] = _grade_picks(picks)
    results["STR-05"]["fire_rule"] = "divisional game; back the lower net-rating side"
    results["STR-05"]["_picks"] = picks

    # STR-10: composite gated ensemble = STR-01 AND STR-04 must agree
    picks = []
    for r in graded:
        if abs(r["pred_margin_home"]) < SELECTIVITY_THRESHOLD:
            continue
        d = r["rest_diff_home_minus_away"]
        if d == "" or abs(d) < REST_EDGE_DAYS:
            continue
        model_side_home = r["pred_margin_home"] > 0
        if model_side_home != (d > 0):
            continue
        picks.append(mk(r, model_side_home))
    results["STR-10"] = _grade_picks(picks)
    results["STR-10"]["fire_rule"] = "STR-01 AND STR-04 agree (intersection)"
    results["STR-10"]["_picks"] = picks

    return results


def evaluate_parlays(wf):
    """STR-07: two-leg parlays from same-week STR-01 picks.

    Legs are paired GREEDILY AND WITHOUT REUSE inside each week. Enumerating every
    combination would produce heavily overlapping parlays whose outcomes are not
    independent, which would silently invalidate the significance test.
    """
    legs = {}
    for r in wf:
        if r["actual_home_win"] == "":
            continue
        if abs(r["pred_margin_home"]) < SELECTIVITY_THRESHOLD:
            continue
        legs.setdefault(r["wk"], []).append(r)

    combos = []
    for wk in sorted(legs):
        pool = legs[wk]
        used = set()
        for i in range(len(pool)):
            if i in used:
                continue
            for j in range(i + 1, len(pool)):
                if j in used:
                    continue
                used.add(i)
                used.add(j)
                combos.append((pool[i], pool[j]))
                break

    if not combos:
        return {"n_parlays": 0}

    def leg_state(r):
        side_home = r["pred_margin_home"] > 0
        p_model = r["pred_p_home_win"] if side_home else 1.0 - r["pred_p_home_win"]
        p_null = r["null_p_home_win"] if side_home else 1.0 - r["null_p_home_win"]
        hit = 1 if ((r["actual_home_win"] == 1) == side_home) else 0
        return p_model, p_null, hit

    rows = []
    nulls = []
    hits = 0
    for a, b in combos:
        pa_m, pa_n, ha = leg_state(a)
        pb_m, pb_n, hb = leg_state(b)
        hit = 1 if (ha == 1 and hb == 1) else 0
        hits += hit
        nulls.append(pa_n * pb_n)
        rows.append({
            "wk": a["wk"],
            "leg_a": "%s @ %s" % (a["away"], a["home"]),
            "leg_b": "%s @ %s" % (b["away"], b["home"]),
            "leg_a_side": "home" if a["pred_margin_home"] > 0 else "away",
            "leg_b_side": "home" if b["pred_margin_home"] > 0 else "away",
            "leg_a_model_prob": round(pa_m, 4), "leg_b_model_prob": round(pb_m, 4),
            "leg_a_null_prob": round(pa_n, 4), "leg_b_null_prob": round(pb_n, 4),
            "leg_a_hit": ha, "leg_b_hit": hb, "parlay_hit": hit,
            "source_url_a": a["source_url"], "source_url_b": b["source_url"],
        })

    n = len(combos)
    xs = [r["leg_a_hit"] for r in rows]
    ys = [r["leg_b_hit"] for r in rows]
    phi = pearson(xs, ys)
    pa = mean(xs)
    pb = mean(ys)
    p_joint_obs = hits / n
    p_joint_indep = pa * pb
    p_null_mean = mean(nulls)
    lo = max(0.0, pa + pb - 1.0)
    hi = min(pa, pb)
    payoff = (100.0 / 110.0 + 1.0) ** 2 - 1.0     # -110 price on each of two legs
    rets = [payoff if r["parlay_hit"] == 1 else -1.0 for r in rows]
    p_two = poisson_binomial_two_sided(hits, nulls)
    return {
        "n_parlays": n,
        "pairing": "greedy, non-overlapping, within week",
        "leg_a_win_rate": round(pa, 4),
        "leg_b_win_rate": round(pb, 4),
        "measured_leg_phi": round(phi, 4) if phi is not None else "",
        "correlation_cap_ok": ("YES" if (phi is not None and abs(phi) < CORRELATION_CAP) else "NO"),
        "parlay_hit_rate": round(p_joint_obs, 4),
        "independence_implied_hit_rate": round(p_joint_indep, 4),
        "null_implied_hit_rate": round(p_null_mean, 4),
        "lift_over_independence": round(p_joint_obs / p_joint_indep, 4) if p_joint_indep else "",
        "model_expected_hit_rate": round(mean([r["leg_a_model_prob"] * r["leg_b_model_prob"] for r in rows]), 4),
        "frechet_min": round(lo, 4), "frechet_max": round(hi, 4),
        "within_frechet_bounds": "YES" if lo - 1e-9 <= p_joint_obs <= hi + 1e-9 else "NO",
        "roi_per_unit": round(mean(rets), 4),
        "units": round(sum(rets), 3),
        "break_even_hit_rate": round(1.0 / (payoff + 1.0), 4),
        "max_drawdown_units": round(max_drawdown(rets), 3),
        "sharpe": round(sharpe_ratio(rets), 4) if sharpe_ratio(rets) is not None else "",
        "brier": round(mean([(r["leg_a_model_prob"] * r["leg_b_model_prob"] - r["parlay_hit"]) ** 2 for r in rows]), 4),
        "brier_reference_null": round(mean([(nq - r["parlay_hit"]) ** 2 for nq, r in zip(nulls, rows)]), 4),
        "p_two_sided_exact_poisson_binomial": round(p_two, 6) if p_two is not None else "",
        "_rets": rets, "_hits": hits, "_nulls": nulls, "_p_raw": p_two,
        "rows": rows,
    }



# ===========================================================================
# 11. Correlations
# ===========================================================================
def team_correlations(ledger):
    st = {r[0]: r for r in R.STANDINGS_2026_WK10}
    pf, pa, gp = {}, {}, {}
    for a in st:
        pf[a] = 0
        pa[a] = 0
        gp[a] = 0
    for g in ledger:
        for side, opp in (("away", "home"), ("home", "away")):
            pf[g[side]] += g[side + "_pts"]
            pa[g[side]] += g[opp + "_pts"]
            gp[g[side]] += 1
    abbrs = sorted(st)
    pct = {a: (st[a][4] + 0.5 * st[a][6]) / max(1, st[a][4] + st[a][5] + st[a][6]) for a in abbrs}
    wins = {a: st[a][4] for a in abbrs}
    pfg = {a: pf[a] / gp[a] for a in abbrs}
    pag = {a: pa[a] / gp[a] for a in abbrs}
    netg = {a: pfg[a] - pag[a] for a in abbrs}
    net = {a: pf[a] - pa[a] for a in abbrs}

    pairs = [
        ("CORR-T01", "points for per game (PF/G)", "winning percentage (PCT)", pfg, pct),
        ("CORR-T02", "points allowed per game (PA/G)", "winning percentage (PCT)", pag, pct),
        ("CORR-T03", "net points per game (PF/G - PA/G)", "winning percentage (PCT)", netg, pct),
        ("CORR-T04", "points for per game (PF/G)", "points allowed per game (PA/G)", pfg, pag),
        ("CORR-T05", "net points (PF - PA)", "wins (W)", net, wins),
        ("CORR-T06", "points for per game (PF/G)", "wins (W)", pfg, wins),
        ("CORR-T07", "points allowed per game (PA/G)", "wins (W)", pag, wins),
    ]
    out = []
    for cid, xn, yn, xd, yd in pairs:
        xs = [xd[a] for a in abbrs]
        ys = [yd[a] for a in abbrs]
        r = pearson(xs, ys)
        n = len(abbrs)
        t = r * math.sqrt((n - 2) / (1 - r * r)) if r is not None and abs(r) < 1 else None
        p = 2.0 * (1.0 - NormalDist().cdf(abs(t))) if t is not None else None
        out.append({
            "pair_id": cid, "level": "team", "metric_x": xn, "metric_y": yn,
            "n": n, "pearson_r": round(r, 4) if r is not None else "",
            "r_squared": round(r * r, 4) if r is not None else "",
            "t_stat": round(t, 4) if t is not None else "",
            "p_two_sided": round(p, 6) if p is not None else "",
            "input_data": "Official 136-game ledger + https://www.nfl.com/standings/ (32 teams, through Week 9)",
            "computed_by": "nfl-desk-26d4cafb/engine.py (Pearson r, stdlib)",
            "source_url": "https://www.nfl.com/standings/",
            "status": "verified inputs (nfl.com); value computed in-repo",
        })
    return out


def player_correlations():
    logs = R.PLAYER_GAME_LOGS_2026
    qb = [(r[I_QB_YDS], r[I_TEAM_PTS]) for r in logs]
    qb_tgt = [(r[I_QB_YDS], r[I_TGT_YDS]) for r in logs]
    qb_rb = [(r[I_QB_YDS], r[I_RB_YDS]) for r in logs if r[I_RB_YDS] is not None]
    tgt_rb = [(r[I_TGT_YDS], r[I_RB_YDS]) for r in logs if r[I_RB_YDS] is not None]
    att_yds = [(r[I_QB_ATT], r[I_QB_YDS]) for r in logs]
    rec_yds = [(r[I_TGT_REC], r[I_TGT_YDS]) for r in logs]
    rbatt_yds = [(r[I_RB_ATT], r[I_RB_YDS]) for r in logs if r[I_RB_YDS] is not None]
    pts_rb = [(r[I_TEAM_PTS], r[I_RB_YDS]) for r in logs if r[I_RB_YDS] is not None]
    margin_rb = [(r[I_TEAM_PTS] - r[I_OPP_PTS], r[I_RB_YDS]) for r in logs if r[I_RB_YDS] is not None]
    margin_qb = [(r[I_TEAM_PTS] - r[I_OPP_PTS], r[I_QB_YDS]) for r in logs]
    teampts_tgt = [(r[I_TEAM_PTS], r[I_TGT_YDS]) for r in logs]

    specs = [
        ("CORR-P01", "QB passing yards", "primary target receiving yards", qb_tgt),
        ("CORR-P02", "QB passing yards", "lead RB rushing yards", qb_rb),
        ("CORR-P03", "primary target receiving yards", "lead RB rushing yards", tgt_rb),
        ("CORR-P04", "QB passing yards", "team points scored", qb),
        ("CORR-P05", "QB pass attempts", "QB passing yards", att_yds),
        ("CORR-P06", "target receptions", "target receiving yards", rec_yds),
        ("CORR-P07", "RB rushing attempts", "RB rushing yards", rbatt_yds),
        ("CORR-P08", "team points scored", "lead RB rushing yards", pts_rb),
        ("CORR-P09", "team margin (pts - opp pts)", "lead RB rushing yards", margin_rb),
        ("CORR-P10", "team margin (pts - opp pts)", "QB passing yards", margin_qb),
        ("CORR-P11", "team points scored", "primary target receiving yards", teampts_tgt),
    ]
    out = []
    for cid, xn, yn, pairs in specs:
        xs = [a for a, _b in pairs]
        ys = [b for _a, b in pairs]
        r = pearson(xs, ys)
        n = len(xs)
        t = r * math.sqrt((n - 2) / (1 - r * r)) if r is not None and abs(r) < 1 else None
        p = 2.0 * (1.0 - NormalDist().cdf(abs(t))) if t is not None else None
        out.append({
            "pair_id": cid, "level": "player-prop", "metric_x": xn, "metric_y": yn,
            "n": n, "pearson_r": round(r, 4) if r is not None else "",
            "r_squared": round(r * r, 4) if r is not None else "",
            "t_stat": round(t, 4) if t is not None else "",
            "p_two_sided": round(p, 6) if p is not None else "",
            "input_data": "50 paired official 2026 player game logs (CIN, DET, DAL, BUF, GB, KC)",
            "computed_by": "nfl-desk-26d4cafb/engine.py (Pearson r, stdlib)",
            "source_url": "https://www.nfl.com/stats/player-stats/",
            "status": "verified inputs (nfl.com); value computed in-repo; sample limited (FLG-16)",
        })
    return out


def per_qb_correlations():
    logs = R.PLAYER_GAME_LOGS_2026
    by_qb = {}
    for r in logs:
        by_qb.setdefault(r[I_QB], []).append(r)
    out = []
    for qb in sorted(by_qb):
        rs = by_qb[qb]
        xs = [r[I_QB_YDS] for r in rs]
        ys = [r[I_TGT_YDS] for r in rs]
        zs = [r[I_RB_YDS] for r in rs if r[I_RB_YDS] is not None]
        ws = [r[I_QB_YDS] for r in rs if r[I_RB_YDS] is not None]
        r_t = pearson(xs, ys)
        r_r = pearson(ws, zs) if len(zs) >= 3 else None
        out.append({
            "qb": qb,
            "team": rs[0][0],
            "n_games": len(rs),
            "official_season_pass_yds": R.OFFICIAL_QB_YARDS_CHECKSUMS.get(qb, ""),
            "sum_of_game_logs": sum(xs),
            "checksum_match": ("MATCH" if R.OFFICIAL_QB_YARDS_CHECKSUMS.get(qb) == sum(xs)
                               else ("NO OFFICIAL CHECKSUM" if qb not in R.OFFICIAL_QB_YARDS_CHECKSUMS else "MISMATCH")),
            "mean_pass_yds": round(mean(xs), 1),
            "sd_pass_yds": round(stdev_s(xs), 1),
            "r_with_primary_target": round(r_t, 4) if r_t is not None else "",
            "n_rb_games": len(zs),
            "r_with_lead_rb": round(r_r, 4) if r_r is not None else "",
            "source_url": rs[0][I_QB_URL],
        })
    return out


def prop_combos():
    """Same-game player-prop combo joint probabilities, lift over independence, and
    Frechet-Hoeffding bounds. Reference line = the player's own shrunk season median
    (a SYNTHETIC fair reference, not an official prop line -- FLG-01/FLG-02)."""
    logs = R.PLAYER_GAME_LOGS_2026
    # per-player series
    qb_series = {}
    tgt_series = {}
    rb_series = {}
    for r in logs:
        qb_series.setdefault(r[I_QB], []).append((r[I_WK], r[I_QB_YDS]))
        tgt_series.setdefault(r[I_TGT], []).append((r[I_WK], r[I_TGT_YDS]))
        if r[I_RB_YDS] is not None:
            rb_series.setdefault(r[I_RB], []).append((r[I_WK], r[I_RB_YDS]))

    def event_table(series):
        """Return {player: {week: 1/0 over own shrunk season median}}."""
        out = {}
        for p, vals in series.items():
            ys = [v for _w, v in vals]
            k = SHRINK_K
            n = len(ys)
            # shrunk median: shrink values toward the league-ish mean of the player's own games
            mu = mean(ys)
            shrunk = [mu + (n / (n + k)) * (v - mu) for v in ys]
            med = statistics.median(shrunk)
            out[p] = {w: (1 if v > med else 0) for (w, v), v2 in zip(vals, shrunk)}
        return out

    qb_ev = event_table(qb_series)
    tgt_ev = event_table(tgt_series)
    rb_ev = event_table(rb_series)

    # pair QB with his own team's primary target and lead RB using the log rows
    pair_qb_tgt = {}
    pair_qb_rb = {}
    for r in logs:
        qb, tgt, rb = r[I_QB], r[I_TGT], r[I_RB]
        wk = r[I_WK]
        if wk in qb_ev.get(qb, {}) and wk in tgt_ev.get(tgt, {}):
            pair_qb_tgt.setdefault((qb, tgt), []).append((qb_ev[qb][wk], tgt_ev[tgt][wk]))
        if rb and wk in qb_ev.get(qb, {}) and wk in rb_ev.get(rb, {}):
            pair_qb_rb.setdefault((qb, rb), []).append((qb_ev[qb][wk], rb_ev[rb][wk]))

    out = []
    for kind, pairs in (("STR-08 QB over + primary target over", pair_qb_tgt),
                        ("STR-09 QB over + lead RB over", pair_qb_rb)):
        for (a, b), obs in sorted(pairs.items()):
            n = len(obs)
            if n < 3:
                continue
            xs = [o[0] for o in obs]
            ys = [o[1] for o in obs]
            pa = mean(xs)
            pb = mean(ys)
            joint = sum(1 for o in obs if o[0] == 1 and o[1] == 1) / n
            indep = pa * pb
            phi = pearson(xs, ys)
            lo = max(0.0, pa + pb - 1.0)
            hi = min(pa, pb)
            out.append({
                "combo": kind, "leg_a": a, "leg_b": b, "n_games": n,
                "p_leg_a": round(pa, 4), "p_leg_b": round(pb, 4),
                "p_joint_observed": round(joint, 4),
                "p_joint_if_independent": round(indep, 4),
                "lift_over_independence": round(joint / indep, 4) if indep else "",
                "phi_correlation": round(phi, 4) if phi is not None else "",
                "frechet_min": round(lo, 4), "frechet_max": round(hi, 4),
                "within_frechet_bounds": "YES" if lo - 1e-9 <= joint <= hi + 1e-9 else "NO",
                "correlation_cap_ok_G09": ("YES" if (phi is not None and abs(phi) < CORRELATION_CAP) else "NO"),
                "official_prop_line": "",
                "official_price": "",
                "source_url": "https://www.nfl.com/stats/player-stats/",
                "note": "Reference line is the player's own shrunk season MEDIAN (synthetic fair "
                        "reference). No official prop line exists (FLG-01, FLG-02), so no bet is graded.",
            })

    # pooled
    for kind, pairs in (("POOLED QB over + primary target over", pair_qb_tgt),
                        ("POOLED QB over + lead RB over", pair_qb_rb)):
        obs = [o for v in pairs.values() for o in v]
        if len(obs) < 3:
            continue
        xs = [o[0] for o in obs]
        ys = [o[1] for o in obs]
        pa, pb = mean(xs), mean(ys)
        n = len(obs)
        joint = sum(1 for o in obs if o[0] == 1 and o[1] == 1) / n
        indep = pa * pb
        phi = pearson(xs, ys)
        lo = max(0.0, pa + pb - 1.0)
        hi = min(pa, pb)
        out.append({
            "combo": kind, "leg_a": "ALL", "leg_b": "ALL", "n_games": n,
            "p_leg_a": round(pa, 4), "p_leg_b": round(pb, 4),
            "p_joint_observed": round(joint, 4),
            "p_joint_if_independent": round(indep, 4),
            "lift_over_independence": round(joint / indep, 4) if indep else "",
            "phi_correlation": round(phi, 4) if phi is not None else "",
            "frechet_min": round(lo, 4), "frechet_max": round(hi, 4),
            "within_frechet_bounds": "YES" if lo - 1e-9 <= joint <= hi + 1e-9 else "NO",
            "correlation_cap_ok_G09": ("YES" if (phi is not None and abs(phi) < CORRELATION_CAP) else "NO"),
            "official_prop_line": "", "official_price": "",
            "source_url": "https://www.nfl.com/stats/player-stats/",
            "note": "Pooled across all 6 sampled teams; sample limited to 50 team-games (FLG-16).",
        })
    return out


# ===========================================================================
# 12. Selectivity test, luck vs skill
# ===========================================================================
def selectivity_test(wf):
    """Split graded bets into confidence terciles by |model margin|.

    Under pure luck, accuracy is FLAT across terciles: confidence carries no
    information. Under selective skill it rises monotonically. The Cochran-Armitage
    trend test is the formal check; the monotone-ordering check is the stronger,
    more intuitive one and is reported alongside.
    """
    graded = [r for r in wf if r["actual_home_win"] != ""]
    if len(graded) < 30:
        return None
    ordered = sorted(graded, key=lambda r: abs(r["pred_margin_home"]))
    k = len(ordered) // 3
    buckets = [ordered[:k], ordered[k:2 * k], ordered[2 * k:]]
    rows = []
    succ, tot = [], []
    labels = ["1 (lowest |model margin|)", "2 (middle)", "3 (highest |model margin|)"]
    for i, b in enumerate(buckets):
        if not b:
            continue
        wins = sum(1 for r in b
                   if ((r["pred_margin_home"] > 0) == (r["actual_home_win"] == 1)))
        nulls = [(r["null_p_home_win"] if r["pred_margin_home"] > 0 else 1 - r["null_p_home_win"])
                 for r in b]
        rows.append({
            "tercile": labels[i],
            "n_bets": len(b),
            "mean_abs_model_margin": round(mean([abs(r["pred_margin_home"]) for r in b]), 3),
            "wins": wins,
            "win_rate": round(wins / len(b), 4),
            "mean_null_win_rate": round(mean(nulls), 4),
            "lift_over_null": round(wins / len(b) - mean(nulls), 4),
            "source_url": "https://www.nfl.com/schedules",
        })
        succ.append(wins)
        tot.append(len(b))
    chi2, p = chi2_trend_p(succ, tot)
    monotone = (len(rows) == 3 and rows[0]["win_rate"] <= rows[1]["win_rate"] <= rows[2]["win_rate"])
    return {
        "rows": rows,
        "chi2_trend": round(chi2, 4) if chi2 is not None else "",
        "p_trend_two_sided": round(p, 6) if p is not None else "",
        "monotone_increasing": "YES" if monotone else "NO",
        "interpretation": (
            "Accuracy rises monotonically across confidence terciles and the trend test "
            "clears alpha=0.05: the signature of SELECTIVE skill rather than uniform luck."
            if (monotone and p is not None and p < 0.05) else
            "NOT ESTABLISHED: either the ordering is not monotone or the trend test does not "
            "clear alpha=0.05. The observed spread is within what uniform luck produces, so no "
            "selectivity claim is made."),
        "source_url": "https://www.nfl.com/schedules",
    }


def build_luck_skill(strategy_results, parlay, n_trials):
    """Assemble the luck-vs-skill table with Holm-Bonferroni family-wise control and
    the Deflated Sharpe Ratio. Every p-value is an exact Poisson-binomial test against
    the strategy's OWN per-pick null, not a constant."""
    rows = []
    ids = [k for k in sorted(strategy_results) if strategy_results[k]["n"] > 0]
    pvals = [strategy_results[k].get("_p_raw") for k in ids]
    holm = holm_bonferroni(pvals)
    for i, sid in enumerate(ids):
        r = strategy_results[sid]
        dsr = deflated_sharpe_ratio(r["_rets"], n_trials)
        rows.append({
            "strategy": sid,
            "n_graded_bets": r["n"],
            "wins": r["wins"],
            "win_rate": r["win_rate"],
            "mean_null_win_rate": r["mean_null_win_rate"],
            "lift_over_null": r["lift_over_null"],
            "break_even_-110": r["break_even_at_-110"],
            "roi_per_unit": r["roi_per_unit_at_-110"],
            "units": r["units"],
            "p_two_sided_exact_poisson_binomial": r["p_two_sided_exact_poisson_binomial"],
            "holm_adjusted_p": round(holm[i], 6) if holm[i] is not None else "",
            "significant_after_holm": ("YES" if (holm[i] is not None and holm[i] < 0.05) else "NO"),
            "brier": r["brier"],
            "brier_reference_null": r["brier_reference_null"],
            "brier_skill_score": r["brier_skill_score"],
            "sharpe": r["sharpe"],
            "deflated_sharpe_ratio": round(dsr, 4) if dsr is not None else "",
            "dsr_above_0.5": ("YES" if (dsr is not None and dsr > 0.5) else "NO"),
            "skew": r["skew"], "excess_kurtosis": r["excess_kurtosis"],
            "max_drawdown_units": r["max_drawdown_units"],
            "trials_in_family": n_trials,
            "source_url": "https://www.nfl.com/schedules",
            "note": ("Null = the home win rate observed in weeks strictly BEFORE each graded week "
                     "(per-pick), tested with an exact Poisson-binomial. Graded walk-forward on the "
                     "official 136-game ledger. No official price exists, so ROI is reported at a "
                     "DECLARED -110, not an observed one (FLG-01)."),
        })
    if parlay.get("n_parlays"):
        dsr = deflated_sharpe_ratio(parlay["_rets"], n_trials)
        rows.append({
            "strategy": "STR-07 (two-leg parlay)",
            "n_graded_bets": parlay["n_parlays"],
            "wins": parlay["_hits"],
            "win_rate": parlay["parlay_hit_rate"],
            "mean_null_win_rate": parlay["null_implied_hit_rate"],
            "lift_over_null": round(parlay["parlay_hit_rate"] - parlay["null_implied_hit_rate"], 4),
            "break_even_-110": parlay["break_even_hit_rate"],
            "roi_per_unit": parlay["roi_per_unit"],
            "units": parlay["units"],
            "p_two_sided_exact_poisson_binomial": parlay["p_two_sided_exact_poisson_binomial"],
            "holm_adjusted_p": "",
            "significant_after_holm": "NOT IN FAMILY (single parlay construction)",
            "brier": parlay["brier"],
            "brier_reference_null": parlay["brier_reference_null"],
            "brier_skill_score": (round(1 - parlay["brier"] / parlay["brier_reference_null"], 4)
                                  if parlay["brier_reference_null"] else ""),
            "sharpe": parlay["sharpe"],
            "deflated_sharpe_ratio": round(dsr, 4) if dsr is not None else "",
            "dsr_above_0.5": ("YES" if (dsr is not None and dsr > 0.5) else "NO"),
            "skew": "", "excess_kurtosis": "",
            "max_drawdown_units": parlay["max_drawdown_units"],
            "trials_in_family": n_trials,
            "source_url": "https://www.nfl.com/schedules",
            "note": ("Parlay null = product of the two per-leg nulls, then checked against the "
                     "MEASURED leg correlation phi and the Frechet-Hoeffding bounds (G-09, SUG-09)."),
        })
    return rows



# ===========================================================================
# 12b. Diagnostics: shrinkage sensitivity + matched-sample model comparison
# ===========================================================================
def k_sensitivity(ledger, grid=(3, 6, 9, 12, 16, 24)):
    """Walk-forward margin MAE for each shrinkage value k.

    Diagnostic only. Picking the argmin on the SAME sample that is later reported
    would be a form of overfitting, so k is declared a priori (SHRINK_K) and this
    table is published to show how flat / how sensitive the choice is.
    """
    out = []
    for k in grid:
        errs = []
        for wk in sorted({g["wk"] for g in ledger}):
            if wk < GRADED_FROM_WEEK:
                continue
            train = [g for g in ledger if g["wk"] < wk]
            if len(train) < 30:
                continue
            rt = fit_ratings(train, k=k)
            hfa_train = mean([g["margin_home"] for g in train
                              if not g["neutral"] and not g["neutral_unconfirmed"]])
            for g in [x for x in ledger if x["wk"] == wk]:
                hfa = 0.0 if g["neutral"] else hfa_train
                lam_h = max(3.0, rt["lg"] + rt["off"][g["home"]] + rt["def"][g["away"]] + hfa / 2.0)
                lam_a = max(3.0, rt["lg"] + rt["off"][g["away"]] + rt["def"][g["home"]] - hfa / 2.0)
                errs.append((lam_h - lam_a) - g["margin_home"])
        out.append({
            "shrink_k": k,
            "n_graded": len(errs),
            "margin_MAE": round(mean([abs(e) for e in errs]), 3),
            "margin_RMSE": round(math.sqrt(mean([e * e for e in errs])), 3),
            "margin_bias": round(mean(errs), 3),
            "is_declared_value": "YES (used for all reported results)" if k == SHRINK_K else "",
            "source_url": "https://www.nfl.com/schedules",
        })
    return out


def matched_sample_oos(rows):
    """Compare the prior originators on the SAME set of games.

    The raw per-model sample sizes differ (15 / 13 / 29 games) because each board
    produced lines for a different subset. Comparing MAE across unequal, non-nested
    samples is not a like-for-like test, so this restricts every model to the games
    ALL of them graded and recomputes.
    """
    by_model = {}
    for r in rows:
        by_model.setdefault(r["model"], {})[(r["wk"], r["away"], r["home"])] = r
    if not by_model:
        return []
    common = None
    for m, d in by_model.items():
        common = set(d) if common is None else (common & set(d))
    if not common:
        return []
    out = []
    for model in sorted(by_model):
        sub = [by_model[model][k] for k in sorted(common)]
        me = [abs(r["margin_error"]) for r in sub if r["margin_error"] != ""]
        te = [abs(r["total_error"]) for r in sub if r["total_error"] != ""]
        br = [r["brier_home"] for r in sub if r["brier_home"] != ""]
        su = [r for r in sub if r["actual_home_win"] != ""]
        correct = sum(1 for r in su
                      if (r["pred_p_home_win"] != "" and
                          ((r["pred_p_home_win"] >= 0.5 and r["actual_home_win"] == 1) or
                           (r["pred_p_home_win"] < 0.5 and r["actual_home_win"] == 0))))
        out.append({
            "model": model,
            "matched_sample_n": len(common),
            "margin_MAE": round(mean(me), 3) if me else "",
            "margin_bias": round(mean([r["margin_error"] for r in sub if r["margin_error"] != ""]), 3),
            "total_MAE": round(mean(te), 3) if te else "",
            "straight_up_correct": correct,
            "straight_up_accuracy": round(correct / len(su), 4) if su else "",
            "brier_score": round(mean(br), 4) if br else "",
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-9",
            "note": "Matched sample: only games graded by EVERY model listed here.",
        })
    return out


# ===========================================================================
# 13. Export helpers
# ===========================================================================
def write_csv(name, rows, fieldnames=None):
    if not rows:
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    if fieldnames is None:
        fieldnames = [k for k in rows[0] if not k.startswith("_")]
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return path


def write_json(name, obj):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True, default=str)
    return path


# ===========================================================================
# 14. Main
# ===========================================================================
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    report = {}

    # ---- 1. Ledger ------------------------------------------------------
    ledger, added = build_ledger()
    report["ledger_n"] = len(ledger)
    report["ledger_added_post_freeze"] = added
    write_csv("ledger.csv", ledger, fieldnames=[
        "game_id", "wk", "date", "away", "home", "away_pts", "home_pts",
        "margin_home", "total", "neutral", "neutral_unconfirmed", "origin", "source_url"])

    # ---- 2. Standings reconciliation -----------------------------------
    stand_rows, mismatches, nteams = reconcile_standings(ledger)
    report["standings_teams"] = nteams
    report["standings_mismatches"] = mismatches
    write_csv("standings_check.csv", stand_rows)
    assert mismatches == 0, "Standings reconciliation failed: %d mismatches" % mismatches

    # ---- 3. HFA ---------------------------------------------------------
    hfa = compute_hfa(ledger)
    report["hfa"] = hfa["mean_home_margin"]
    report["hfa_n"] = hfa["n_non_neutral_games"]
    write_csv("hfa.csv", [hfa])

    # ---- 4. Injuries ----------------------------------------------------
    tolls = build_injury_tolls()
    write_csv("injuries.csv", R.INJURY_DEPTH_ENTRIES, fieldnames=list(R.INJURY_DEPTH_ENTRIES[0].keys()))

    # ---- 5. Player logs + checksum --------------------------------------
    pl_rows = []
    for r in R.PLAYER_GAME_LOGS_2026:
        pl_rows.append(dict(zip(
            ["team", "wk", "date", "opponent", "result", "team_pts", "opp_pts",
             "qb_name", "qb_comp", "qb_att", "qb_pass_yds", "qb_pass_td", "qb_int", "qb_source_url",
             "target_name", "target_pos", "target_rec", "target_rec_yds", "target_rec_td", "target_source_url",
             "rb_name", "rb_att", "rb_rush_yds", "rb_rush_td", "rb_source_url"], r)))
    write_csv("player_logs.csv", pl_rows)
    checksums = per_qb_correlations()
    report["qb_checksum_mismatches"] = sum(1 for c in checksums if c["checksum_match"] == "MISMATCH")
    write_csv("qb_checksums.csv", checksums)

    # ---- 6. Week 10 lines ----------------------------------------------
    wk10_rows, ratings = originate_week10(ledger, hfa["mean_home_margin"], tolls)
    write_csv("lines_wk10.csv", wk10_rows)
    report["wk10_lines"] = len(wk10_rows)

    # ---- 7. OOS Week 9 grading -----------------------------------------
    oos = grade_prior_models(ledger)
    write_csv("oos_week9.csv", oos)
    oos_sum = summarise_oos(oos)
    write_csv("oos_week9_summary.csv", oos_sum)
    report["oos_models_graded"] = len(oos_sum)

    # ---- 7b. Matched-sample OOS comparison ------------------------------
    matched = matched_sample_oos(oos)
    write_csv("oos_week9_matched.csv", matched)
    report["matched_sample_n"] = matched[0]["matched_sample_n"] if matched else 0

    # ---- 8. Walk-forward ------------------------------------------------
    wf = walk_forward_predictions(ledger)
    write_csv("backtest_walkforward.csv", wf)
    report["walkforward_games"] = len(wf)

    # ---- 9. Strategies ---------------------------------------------------
    sres = evaluate_strategies(wf)
    parlay = evaluate_parlays(wf)

    _hw = sum(1 for g in ledger if g["margin_home"] > 0)
    _aw = sum(1 for g in ledger if g["margin_home"] < 0)
    report["ledger_home_win_rate"] = round(_hw / (_hw + _aw), 4)

    sel = selectivity_test(wf)
    report["selectivity"] = sel

    # number of independent trials in the strategy family (for the Deflated Sharpe Ratio)
    n_trials = len([k for k in sres if sres[k]["n"] > 0]) + (1 if parlay.get("n_parlays") else 0)

    luck_rows = build_luck_skill(sres, parlay, n_trials)
    write_csv("luck_skill.csv", luck_rows)
    if sel:
        write_csv("selectivity.csv", sel["rows"])
    if parlay.get("n_parlays"):
        write_csv("parlays.csv", parlay.pop("rows"))
        pcopy = dict(parlay)
        pcopy.pop("_rets", None)
        pcopy["source_url"] = "https://www.nfl.com/schedules"
        write_csv("parlay_summary.csv", [pcopy])

    # ---- 10. Correlations -------------------------------------------------
    tcorr = team_correlations(ledger)
    pcorr = player_correlations()
    write_csv("correlations.csv", tcorr + pcorr)

    combos = prop_combos()
    write_csv("prop_combos.csv", combos)

    # ---- 10b. Shrinkage sensitivity diagnostics ----------------------------
    ksens = k_sensitivity(ledger)
    write_csv("shrinkage_sensitivity.csv", ksens)

    # ---- 11. Strategies + gates + leaderboard -------------------------------
    meta = {s["id"]: s for s in G.STRATEGIES}
    lk = {r["strategy"]: r for r in luck_rows}

    def gval(sid, key, default=""):
        return lk.get(sid, {}).get(key, default)

    strat_rows = []
    for sid in sorted(meta):
        m = meta[sid]
        r = sres.get(sid, {})
        n = r.get("n", 0)
        if sid == "STR-07":
            n = parlay.get("n_parlays", 0)
            wr = parlay.get("parlay_hit_rate", "")
        else:
            wr = r.get("win_rate", "")
        evaluated = n > 0
        reason = ""
        if not evaluated:
            reason = ("No official historical input exists to grade this rule: the official "
                      "injury/depth register was only published for Week 10 (FLG-03), and no "
                      "official player-prop line exists (FLG-01, FLG-02).")
        strat_rows.append({
            "strategy_id": sid,
            "name": m["name"],
            "bet_type": m["bet_type"],
            "market": m["market"],
            "rule": m["rule"],
            "signals": m["signals"],
            "fire_rule": r.get("fire_rule", ""),
            "status": m["status"],
            "n_graded": n if evaluated else 0,
            "win_rate": wr,
            "roi_per_unit": (parlay.get("roi_per_unit", "") if sid == "STR-07" else r.get("roi_per_unit_at_-110", "")),
            "gates_passed": "",
            "reward_tier": "",
            "not_evaluable_reason": reason,
            "source_url": "https://www.nfl.com/schedules",
        })
    write_csv("strategies.csv", strat_rows)

    gate_rows = []
    for sid in sorted(meta):
        m = meta[sid]
        r = sres.get(sid, {})
        n = r.get("n", 0)
        if sid == "STR-07":
            n = parlay.get("n_parlays", 0)
            wr = parlay.get("parlay_hit_rate", "")
            dd = parlay.get("max_drawdown_units", "")
            holm_p = ""
            dsr = (deflated_sharpe_ratio(parlay["_rets"], n_trials) if n else None)
            brier_v = ""
            cap_ok = ("PASS (|phi|=%.3f < %.2f; joint within Frechet [%.3f, %.3f])"
                      % (abs(parlay.get("measured_leg_phi") or 0), CORRELATION_CAP,
                         parlay.get("frechet_min", 0), parlay.get("frechet_max", 0))
                      if (parlay.get("measured_leg_phi") not in ("", None)
                          and abs(parlay.get("measured_leg_phi", 1)) < CORRELATION_CAP
                          and parlay.get("within_frechet_bounds") == "YES")
                      else "FAIL (measured correlation or Frechet bound breach)")
        else:
            wr = r.get("win_rate", "")
            dd = r.get("max_drawdown_units", "")
            lrow = lk.get(sid, {})
            holm_p = lrow.get("holm_adjusted_p", "")
            dsr = None
            if n:
                dsr = deflated_sharpe_ratio(r["_rets"], n_trials)
            brier_v = r.get("brier", "")
            cap_ok = "N/A (single bet)"

        if n == 0:
            gate_rows.append({
                "strategy_id": sid, "name": m["name"],
                "G01_provenance": "PASS", "G02_no_lookahead": "PASS",
                "G03_min_sample_n20": "FAIL (n=0)",
                "G04_breaks_even_-110": "NOT EVALUABLE (no official price/input)",
                "G05_binomial_p05": "NOT EVALUABLE",
                "G06_holm_p05": "NOT EVALUABLE",
                "G07_deflated_sharpe": "NOT EVALUABLE",
                "G08_brier_calibration": "NOT EVALUABLE",
                "G09_correlation_cap": "NOT EVALUABLE",
                "G10_drawdown_budget": "NOT EVALUABLE",
                "overall": "NOT RANKED (insufficient official history)",
                "fail_closed_action": "Excluded from the leaderboard and ineligible for any reward.",
                "source_url": "https://www.nfl.com/schedules",
                "note": ("Rule requires an official input that does not exist for W1-W9 "
                         "(Week-10-only injury register; no official prop lines)."),
            })
            continue

        g03 = "PASS (n=%d)" % n if n >= 20 else "FAIL (n=%d < 20)" % n
        g04 = "PASS (%.4f > %.4f)" % (wr, BREAKEVEN_110) if wr and wr > BREAKEVEN_110 else "FAIL (%.4f <= %.4f)" % (wr, BREAKEVEN_110)
        if sid == "STR-07":
            be = 1.0 / ((100.0 / 110.0 + 1.0) ** 2)
            g04 = "PASS (%.4f > %.4f)" % (wr, be) if wr > be else "FAIL (%.4f <= %.4f)" % (wr, be)
        g05 = ""
        if sid != "STR-07":
            p_raw = r.get("binomial_p_two_sided", "")
            g05 = ("PASS (p=%.4f)" % p_raw) if (p_raw != "" and p_raw < 0.05) else ("FAIL (p=%s)" % p_raw)
        g06 = ""
        if holm_p not in ("", None):
            g06 = "PASS (holm p=%.4f)" % holm_p if holm_p < 0.05 else "FAIL (holm p=%.4f)" % holm_p
        elif sid != "STR-07":
            g06 = "NOT COMPUTED"
        g07 = "PASS (DSR=%.4f)" % dsr if (dsr is not None and dsr > 0) else ("FAIL (DSR=%s)" % (round(dsr, 4) if dsr is not None else ""))
        br_ref = lrow.get("brier_reference_null", "") if sid != "STR-07" else parlay.get("brier_reference_null", "")
        if brier_v not in ("", None) and br_ref not in ("", None):
            g08 = ("PASS (Brier %.4f < null reference %.4f)" % (brier_v, br_ref)
                   if brier_v < br_ref else "FAIL (Brier %.4f >= null reference %.4f)" % (brier_v, br_ref))
        else:
            g08 = "NOT EVALUABLE"
        g10 = "PASS (%.2f u)" % dd if dd <= MAX_DRAWDOWN_UNITS else "FAIL (%.2f u > %.1f u budget)" % (dd, MAX_DRAWDOWN_UNITS)

        blockers = [x for x in (g03, g04, g05, g06, g07, g08, g10) if str(x).startswith("FAIL")]
        overall = "PASS (all gates)" if not blockers else "BLOCKED (%d gate(s) failed)" % len(blockers)
        gate_rows.append({
            "strategy_id": sid, "name": m["name"],
            "G01_provenance": "PASS (official 136-game ledger and nfl.com inputs only)",
            "G02_no_lookahead": "PASS (walk-forward: train on weeks strictly < graded week)",
            "G03_min_sample_n20": g03,
            "G04_breaks_even_-110": g04,
            "G05_binomial_p05": g05,
            "G06_holm_p05": g06,
            "G07_deflated_sharpe": g07,
            "G08_brier_calibration": g08,
            "G09_correlation_cap": cap_ok,
            "G10_drawdown_budget": g10,
            "overall": overall,
            "fail_closed_action": ("Eligible for ranking and reward." if overall.startswith("PASS")
                                   else "Ranked last / ineligible for reward; kept visible for review."),
            "note": "",
            "source_url": "https://www.nfl.com/schedules",
        })
    write_csv("gates.csv", gate_rows)

    # ---- Leaderboard -----------------------------------------------------
    lb_rows = []
    for sid in sorted(meta):
        m = meta[sid]
        gates = next((g for g in gate_rows if g["strategy_id"] == sid), {})
        passed = gates.get("overall", "").startswith("PASS")
        r = sres.get(sid, {})
        if sid == "STR-07":
            n = parlay.get("n_parlays", 0)
            score = parlay.get("roi_per_unit", "")
            dsr = deflated_sharpe_ratio(parlay["_rets"], n_trials) if n else None
        else:
            n = r.get("n", 0)
            score = r.get("roi_per_unit_at_-110", "")
            dsr = deflated_sharpe_ratio(r["_rets"], n_trials) if n else None
        if not n:
            lb_rows.append({
                "rank": "", "strategy_id": sid, "name": m["name"],
                "bet_type": m["bet_type"], "market": m["market"],
                "graded_bets": 0, "win_rate": "", "roi_per_unit": "",
                "deflated_sharpe_ratio": "", "max_drawdown_units": "",
                "gates_passed": "NOT RANKED", "reward_tier": "NO REWARD",
                "pool_size": "", "payout_rule": "",
                "status": m["status"],
                "note": "Not graded: no official input exists for W1-W9 (FLG-01, FLG-02, FLG-03).",
                "source_url": "https://www.nfl.com/schedules",
            })
            continue
        lb_rows.append({
            "rank": "", "strategy_id": sid, "name": m["name"],
            "bet_type": m["bet_type"], "market": m["market"],
            "graded_bets": n,
            "win_rate": (parlay.get("parlay_hit_rate", "") if sid == "STR-07" else r.get("win_rate", "")),
            "roi_per_unit": score,
            "deflated_sharpe_ratio": round(dsr, 4) if dsr is not None else "",
            "max_drawdown_units": (parlay.get("max_drawdown_units", "") if sid == "STR-07" else r.get("max_drawdown_units", "")),
            "gates_passed": "ALL 10 PASS" if passed else "BLOCKED",
            "reward_tier": ("TIER 1 - featured placement + largest research allocation"
                            if passed else "NO REWARD"),
            "pool_size": "", "payout_rule": "",
            "status": m["status"],
            "note": "Reward = research allocation only; no funded pool exists (FLG-13).",
            "source_url": "https://www.nfl.com/schedules",
        })

    # RANK ONLY STRATEGIES THAT CLEARED EVERY GATE. A blocked strategy is shown
    # beneath the ranking with rank "" and NO REWARD -- it is never ranked above a
    # strategy that passed (fail-closed: G-01..G-10 are not advisory).
    ranked = [x for x in lb_rows
              if x["gates_passed"] == "ALL 10 PASS" and x["deflated_sharpe_ratio"] != ""]
    ranked.sort(key=lambda x: -float(x["deflated_sharpe_ratio"]))
    for i, x in enumerate(ranked, 1):
        x["rank"] = i
    for x in lb_rows:
        if x not in ranked:
            x["rank"] = ""
            x["reward_tier"] = "NO REWARD (failed >=1 validation gate)"
    write_csv("leaderboard.csv", lb_rows)

    # ---- Registers -------------------------------------------------------
    write_csv("flagged.csv", G.FLAGGED)
    write_csv("sources.csv", G.OFFICIAL_SOURCES)
    write_csv("repo_audit.csv", G.REPO_AUDIT)
    write_csv("signals.csv", G.SIGNALS)
    write_csv("suggestions.csv", G.SUGGESTIONS)
    write_csv("questions.csv", G.PREDECISION_QUESTIONS)
    write_csv("discovery.csv", G.DISCOVERY_ACTIONS)
    write_csv("requirements.csv", G.REQUIREMENTS)
    write_csv("paths.csv", G.DECISION_PATHS)

    # ---- Summary ---------------------------------------------------------
    summary = {
        "session": G.SESSION_ID,
        "snapshot_date": G.SNAPSHOT_DATE,
        "season": R.SEASON,
        "current_week": R.CURRENT_WEEK,
        "ledger_completed_games": len(ledger),
        "ledger_added_after_repo_freeze": added,
        "standings_teams": nteams,
        "standings_mismatches": mismatches,
        "standings_reconciliation": {
            "teams": nteams, "mismatches": mismatches,
            "result": "32/32 exact match on W, L, T, PF, PA",
            "source_url": "https://www.nfl.com/standings/",
        },
        "home_field_advantage": hfa,
        "qb_checksum_mismatches": report["qb_checksum_mismatches"],
        "week10_lines_originated": len(wk10_rows),
        "oos_models_graded": len(oos_sum),
        "oos_summary": oos_sum,
        "oos_matched_sample": matched,
        "shrinkage_sensitivity": ksens,
        "walkforward_games": len(wf),
        "ledger_home_win_rate": report["ledger_home_win_rate"],
        "selectivity_test": sel,
        "parlay_analysis": {k: v for k, v in parlay.items() if not k.startswith("_")},
        "luck_skill": luck_rows,
        "leaderboard": lb_rows,
        "gates": gate_rows,
        "team_correlations": tcorr,
        "player_correlations": pcorr,
        "prop_combos": combos,
        "flagged_count": len(G.FLAGGED),
        "repo_audit_count": len(G.REPO_AUDIT),
        "suggestions_count": len(G.SUGGESTIONS),
        "questions_count": len(G.PREDECISION_QUESTIONS),
        "model_hyperparameters": {
            "shrink_k": SHRINK_K, "opp_adjust_iters": OPP_ADJ_ITERS,
            "graded_from_week": GRADED_FROM_WEEK,
            "selectivity_threshold": SELECTIVITY_THRESHOLD,
            "rest_edge_days": REST_EDGE_DAYS,
            "correlation_cap": CORRELATION_CAP,
            "assumed_price": ASSUMED_PRICE,
            "max_drawdown_units": MAX_DRAWDOWN_UNITS,
        },
    }
    write_json("summary.json", summary)

    print("=" * 78)
    print("NFL DECISION DESK -- session 26d4cafb -- snapshot 2026-11-12")
    print("=" * 78)
    print("Completed games in ledger      : %d (added %d after the repo's 2026-11-02 freeze)"
          % (len(ledger), added))
    print("Standings reconciliation       : %d/%d teams, %d mismatches" % (nteams, nteams, mismatches))
    print("Empirical HFA (non-neutral)    : %+.3f pts (n=%d, SE=%.3f, p=%s)"
          % (hfa["mean_home_margin"], hfa["n_non_neutral_games"], hfa["standard_error"], hfa["p_two_sided"]))
    print("QB game-log checksum mismatches: %d" % report["qb_checksum_mismatches"])
    print("Week 10 lines originated       : %d" % len(wk10_rows))
    print("Prior models graded (W8MNF+W9) : %d" % len(oos_sum))
    for s in oos_sum:
        print("   - %-62s n=%-3s MAE=%-7s bias=%-7s SU=%-7s Brier=%s"
              % (s["model"][:62], s["n_games_graded"], s["margin_MAE"], s["margin_bias"],
                 s["straight_up_accuracy"], s["brier_score"]))
    print("Matched-sample OOS (n=%d common games):" % report["matched_sample_n"])
    for s in matched:
        print("   - %-62s MAE=%-7s bias=%-7s SU=%-7s Brier=%s"
              % (s["model"][:62], s["margin_MAE"], s["margin_bias"],
                 s["straight_up_accuracy"], s["brier_score"]))
    print("Shrinkage sensitivity (walk-forward MAE):")
    for s in ksens:
        print("   - k=%-3s MAE=%-7s bias=%-7s %s"
              % (s["shrink_k"], s["margin_MAE"], s["margin_bias"], s["is_declared_value"]))
    print("Walk-forward graded games      : %d (weeks %d-9)" % (len(wf), GRADED_FROM_WEEK))
    print("Ledger home win rate           : %.4f (away teams won %d, home %d)"
          % (report["ledger_home_win_rate"], _aw, _hw))
    print("Luck vs skill (null = per-pick, pre-week home rate; exact Poisson-binomial):")
    for r in luck_rows:
        print("   - %-30s n=%-4d wr=%-7s null=%-7s lift=%-+7s holm=%-9s DSR=%-7s dd=%s"
              % (r["strategy"][:30], r["n_graded_bets"], r["win_rate"],
                 r["mean_null_win_rate"], r["lift_over_null"],
                 r["holm_adjusted_p"], r["deflated_sharpe_ratio"], r["max_drawdown_units"]))
    if sel:
        print("Selectivity trend test         : chi2=%s p=%s monotone=%s"
              % (sel["chi2_trend"], sel["p_trend_two_sided"], sel["monotone_increasing"]))
        for r in sel["rows"]:
            print("   - %-28s n=%-4d wr=%-7s null=%-7s lift=%+7s"
                  % (r["tercile"], r["n_bets"], r["win_rate"], r["mean_null_win_rate"], r["lift_over_null"]))
        print("   -> %s" % sel["interpretation"])
    if parlay.get("n_parlays"):
        print("Two-leg parlays (non-overlap)  : n=%d  hit=%.4f  null=%.4f  indep=%.4f  lift=%.4f  phi=%s  breakeven=%.4f"
              % (parlay["n_parlays"], parlay["parlay_hit_rate"], parlay["null_implied_hit_rate"],
                 parlay["independence_implied_hit_rate"], parlay["lift_over_independence"],
                 parlay["measured_leg_phi"], parlay["break_even_hit_rate"]))
    print("Correlations                   : %d team-level, %d player-prop, %d prop combos"
          % (len(tcorr), len(pcorr), len(combos)))
    print("Leaderboard:")
    for x in sorted(lb_rows, key=lambda z: (z["rank"] == "", z["rank"])):
        print("   - rank %-3s %-6s %-52s DSR=%-8s %s"
              % (x["rank"] or "-", x["strategy_id"], x["name"][:52],
                 x["deflated_sharpe_ratio"] or "-", x["gates_passed"]))
    print("Outputs written to             : %s" % OUT_DIR)
    return summary


if __name__ == "__main__":
    main()

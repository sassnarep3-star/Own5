"""NBA Line Commission — deterministic engine.

Session arena-a46d621e, snapshot 2026-11-05 (UTC).

Everything in data/outputs.json is either
  (a) transcribed from an official NBA page (data/*.csv, per-row source_url), or
  (b) computed here from (a) by the formulas documented in research/nba-commission/methodology.md.

No market odds, no ROI, no skill claim is produced. Parameters that are model choices
(K_BLEND, K_PROP, HFA, PRIOR_PSEUDO) are flagged as such in outputs["flags"].

Run: python3 nba-commission/compute.py
"""
from __future__ import annotations

import csv
import functools
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = DATA / "outputs.json"

SNAPSHOT = "2026-11-05"
URL_STANDINGS = "https://www.nba.com/standings"
URL_TEAM_STATS = "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season"
URL_SCHEDULE = "https://www.nba.com/schedule?date=2026-11-05"
URL_EDWARDS_2627 = "https://www.nba.com/stats/player/1630162/boxscores?Season=2026-27"
URL_DONCIC_2627 = "https://www.nba.com/stats/player/1629029/boxscores?Season=2026-27"
URL_EDWARDS_2526 = "https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26&DateFrom=2025-10-01&DateTo=2025-11-20"
URL_PRIORS_2526 = "https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season"

# Model parameters (explicit choices, not official statistics) -----------------
K_BLEND = 20.0        # shrinkage: w = gp / (gp + K) on the 2026-27 sample
K_PROP = 20.0         # shrinkage: prior season counts as K_PROP pseudo-games
HFA = 2.5             # home-court scoring advantage in points (total), split +/- HFA/2
PRIOR_PSEUDO = 25.0   # pseudo-bets used for the deflated (shrunken) win rate

Z95 = 1.959963984540054


# --------------------------------------------------------------------------- io
def read_csv(name: str) -> list[dict]:
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # one prior-session CSV header contains U+0430 (Cyrillic 'a') in blkа_pg.
    # Normalise keys so downstream code never depends on that defect (see flags).
    return [{k.replace("\u0430", "a"): v for k, v in row.items()} for row in rows]


def f(x) -> float:
    return float(x)


def r2(x: float, nd: int = 2) -> float:
    return round(x, nd)


def round_half_up(x: float, nd: int = 1) -> float:
    """Official nba.com pages round .5 up (33.25 -> 33.3); Python's round() does not."""
    factor = 10 ** nd
    return math.floor(abs(x) * factor + 0.5) / factor * (1 if x >= 0 else -1)


def normal_n(p0: float, p1: float, alpha: float = 0.05, power: float = 0.80) -> int:
    est = ((_z(1 - alpha) * math.sqrt(p0 * (1 - p0)) + _z(power) * math.sqrt(p1 * (1 - p1)))
           / (p1 - p0)) ** 2
    return int(round(est))


# ---------------------------------------------------------------- statistics
def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3 or len(ys) != n:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def fisher_ci(r: float | None, n: int) -> tuple[float | None, float | None]:
    """95% Fisher-z interval. Requires n > 3; undefined for |r| == 1."""
    if r is None or n <= 3 or abs(r) >= 1:
        return None, None
    z = math.atanh(r)
    se = 1.0 / math.sqrt(n - 3)
    return math.tanh(z - Z95 * se), math.tanh(z + Z95 * se)


def phi(a: int, b: int, c: int, d: int) -> float | None:
    den = (a + b) * (c + d) * (a + c) * (b + d)
    if den <= 0:
        return None
    return (a * d - b * c) / math.sqrt(den)


def binom_pmf(k: int, n: int, p: float) -> float:
    if k < 0 or k > n:
        return 0.0
    return math.comb(n, k) * p**k * (1 - p) ** (n - k)


def binom_cdf(k: int, n: int, p: float) -> float:
    return sum(binom_pmf(i, n, p) for i in range(0, min(k, n) + 1))


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) computed with a multiplicative recurrence (stable and fast)."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0
    q = 1.0 - p
    log_term = (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                + k * math.log(p) + (n - k) * math.log(q))
    term = math.exp(log_term)
    total = term
    i = k
    while i < n:
        term *= (n - i) / (i + 1) * p / q
        total += term
        i += 1
    return min(1.0, total)


def binom_p_two_sided(k: int, n: int, p: float) -> float:
    """Exact two-sided binomial test (probability-ordering definition)."""
    obs = binom_pmf(k, n, p)
    total = 0.0
    for i in range(0, n + 1):
        pi = binom_pmf(i, n, p)
        if pi <= obs + 1e-15:
            total += pi
    return min(1.0, total)


def _z(p_: float) -> float:
    """Inverse standard normal CDF (Acklam's rational approximation)."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p_ <= 0 or p_ >= 1:
        raise ValueError("alpha out of range")
    if p_ < plow:
        q = math.sqrt(-2 * math.log(p_))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p_ > phigh:
        q = math.sqrt(-2 * math.log(1 - p_))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p_ - 0.5
    rr = q * q
    return (((((a[0] * rr + a[1]) * rr + a[2]) * rr + a[3]) * rr + a[4]) * rr + a[5]) * q / \
           (((((b[0] * rr + b[1]) * rr + b[2]) * rr + b[3]) * rr + b[4]) * rr + 1)


@functools.lru_cache(maxsize=None)
def critical_value(n: int, p0: float, alpha: float) -> int | None:
    """Smallest k such that P(X >= k | n, p0) <= alpha."""
    approx = n * p0 + _z(1 - alpha) * math.sqrt(n * p0 * (1 - p0))
    k = max(1, int(math.floor(approx)) - 2)
    steps = 0
    while k <= n and binom_sf(k, n, p0) > alpha and steps < 200:
        k += 1
        steps += 1
    if k > n:
        return None
    while k > 1 and binom_sf(k - 1, n, p0) <= alpha:
        k -= 1
    return k


@functools.lru_cache(maxsize=None)
def required_n(p0: float, p1: float, alpha: float = 0.05, power: float = 0.80,
               cap: int = 25000) -> int | None:
    """Smallest n for which a one-sided exact binomial test of p0 rejects at `alpha`
    with probability >= `power` when the true rate is p1.

    The normal approximation locates the answer; the exact tail is then scanned over a
    narrow window around it (the exact answer is monotone in n near that window).
    Returns None when the requirement exceeds `cap` (reported via the approximation).
    """
    if p1 <= p0:
        return None
    est = ((_z(1 - alpha) * math.sqrt(p0 * (1 - p0)) + _z(power) * math.sqrt(p1 * (1 - p1)))
           / (p1 - p0)) ** 2
    if est > cap:
        return None
    lo = max(10, int(est * 0.85))
    hi = min(cap, int(est * 1.30) + 60)
    for n in range(lo, hi + 1):
        crit = critical_value(n, p0, alpha)
        if crit is None:
            continue
        if binom_sf(crit, n, p1) >= power:
            return n
    return None


def breakeven_from_american(price: int) -> float:
    """Break-even win rate for a single -110 style price: 110/(110+100)."""
    return abs(price) / (abs(price) + 100.0)


# --------------------------------------------------------------------- engine
def main() -> None:
    standings = read_csv("standings_2026_27.csv")
    team_stats = read_csv("team_stats_2026_27.csv")
    priors = read_csv("team_priors_2025_26.csv")
    slate = read_csv("slate_2026_11_05_06.csv")
    logs_2526 = read_csv("game_logs_2025_26.csv")
    logs_2627 = read_csv("game_logs_2026_27.csv")

    checks: list[dict] = []

    def check(cid: str, claim: str, passed: bool, detail: str) -> None:
        checks.append({"id": cid, "claim": claim, "passed": bool(passed), "detail": detail})

    # ---- 1. cross-page agreement: W-L on standings vs team-stats page -------
    st_by = {r["abbr"]: r for r in standings}
    mism = [r["abbr"] for r in team_stats
            if (int(r["w"]), int(r["l"])) != (int(st_by[r["abbr"]]["w"]), int(st_by[r["abbr"]]["l"]))]
    check("X01", "2026-27 W-L agree on both official pages (standings vs team traditional)",
          not mism and len(standings) == 30 and len(team_stats) == 30,
          f"30 team rows compared; mismatches: {mism or 'none'}")

    # ---- 2. record identities ----------------------------------------------
    bad_gp = [r["abbr"] for r in team_stats if int(r["gp"]) != int(r["w"]) + int(r["l"])]
    check("X02", "GP = W + L on every team-stats row", not bad_gp, f"failures: {bad_gp or 'none'}")

    split_bad = []
    for s in standings:
        hw, hl = (int(x) for x in s["home_rec"].split("-"))
        rw, rl = (int(x) for x in s["road_rec"].split("-"))
        nw, nl = (int(x) for x in s["neutral_rec"].split("-"))
        if (hw + rw + nw, hl + rl + nl) != (int(s["w"]), int(s["l"])):
            split_bad.append(s["abbr"])
    check("X03", "HOME + ROAD + NEUTRAL splits sum to the team record", not split_bad,
          f"failures: {split_bad or 'none'}")

    net_sum = sum(f(r["plus_minus_pg"]) * int(r["gp"]) for r in team_stats)
    check("X04", "Sum of (net points/game x GP) over 30 teams is ~0 (rounding tolerance +-2)",
          abs(net_sum) < 2.0, f"sum = {r2(net_sum)} over {sum(int(r['gp']) for r in team_stats)} team-games")

    # ---- 3. game-log identities and official-average checksums -------------
    for tag, rows, expect in (
        ("2025-26", logs_2526, {"1630162": (28.8, 5.0, 3.7), "1629029": (33.5, 7.7, 8.3)}),
        ("2026-27", logs_2627, {"1630162": (33.3, 4.8, 3.5), "1629029": (38.5, 8.1, 8.0)}),
    ):
        bad_id = []
        for r in rows:
            pts = 2 * (int(r["fgm"]) - int(r["tpm"])) + 3 * int(r["tpm"]) + int(r["ftm"])
            if pts != int(r["pts"]) or int(r["oreb"]) + int(r["dreb"]) != int(r["reb"]):
                bad_id.append(r["game_id"])
        check(f"X05-{tag}", f"PTS and REB identities hold on every {tag} game-log row",
              not bad_id, f"{len(rows)} rows checked; failures: {bad_id or 'none'}")

        detail = []
        ok = True
        for pid, (mp, mr, ma) in expect.items():
            sub = [r for r in rows if r["player_id"] == pid]
            got = (round_half_up(statistics.mean(int(r["pts"]) for r in sub), 1),
                   round_half_up(statistics.mean(int(r["reb"]) for r in sub), 1),
                   round_half_up(statistics.mean(int(r["ast"]) for r in sub), 1))
            detail.append(f"{pid} n={len(sub)} computed {got} vs official {expect[pid]}")
            if got != expect[pid]:
                ok = False
        check(f"X06-{tag}", f"{tag} log averages reproduce the official nba.com headline averages",
              ok, "; ".join(detail))

    dup = len(logs_2526) + len(logs_2627) - len({(r["player_id"], r["game_id"]) for r in logs_2526 + logs_2627})
    check("X07", "No duplicate (player_id, game_id) rows across the 2025-26 and 2026-27 logs",
          dup == 0, f"duplicates: {dup}")

    prior_bad = [p["team"] for p in priors if int(p["gp"]) != int(p["w"]) + int(p["l"])]
    prior_net = sum(f(p["plus_minus_pg"]) * int(p["gp"]) for p in priors)
    check("X08", "Reused 2025-26 prior table is internally consistent (GP = W + L; net sums to ~0 +-20)",
          not prior_bad and abs(prior_net) < 20.0,
          f"failures: {prior_bad or 'none'}; sum(net x GP) = {r2(prior_net, 1)} over "
          f"{sum(int(p['gp']) for p in priors)} games")

    slate_ids = [s["game_id"] for s in slate]
    check("X09", "Slate has 11 unique game ids and every listed team exists in the standings table",
          len(set(slate_ids)) == 11 and all(s["home_abbr"] in st_by and s["away_abbr"] in st_by for s in slate),
          f"{len(slate)} games: {len([s for s in slate if s['date']=='2026-11-05'])} on 2026-11-05, "
          f"{len([s for s in slate if s['date']=='2026-11-06'])} on 2026-11-06")

    # ---- 4. team ratings ---------------------------------------------------
    gp_all = sum(int(r["gp"]) for r in team_stats)
    lg_pts = sum(f(r["pts_pg"]) * int(r["gp"]) for r in team_stats) / gp_all
    lg_pts_prior = sum(f(p["pts_pg"]) * int(p["gp"]) for p in priors) / sum(int(p["gp"]) for p in priors)
    prior_by = {p["team"]: p for p in priors}

    ratings = {}
    for r in team_stats:
        n = int(r["gp"])
        off_cur = f(r["pts_pg"]) - lg_pts
        pa_cur = f(r["pts_pg"]) - f(r["plus_minus_pg"])
        def_cur = pa_cur - lg_pts
        p = prior_by[r["team"]]
        off_pri = f(p["pts_pg"]) - lg_pts_prior
        def_pri = (f(p["pts_pg"]) - f(p["plus_minus_pg"])) - lg_pts_prior
        w = n / (n + K_BLEND)
        ratings[r["abbr"]] = {
            "team": r["team"], "abbr": r["abbr"], "team_id": r["team_id"],
            "gp": n, "w": int(r["w"]), "l": int(r["l"]),
            "pts_pg": f(r["pts_pg"]), "plus_minus_pg": f(r["plus_minus_pg"]), "pa_pg": r2(pa_cur),
            "off_cur": r2(off_cur), "def_cur": r2(def_cur),
            "off_prior": r2(off_pri), "def_prior": r2(def_pri),
            "prior_w": int(p["w"]), "prior_l": int(p["l"]),
            "weight": r2(w, 3),
            "off_est": r2(w * off_cur + (1 - w) * off_pri),
            "def_est": r2(w * def_cur + (1 - w) * def_pri),
            "source_url_current": URL_TEAM_STATS, "source_url_prior": URL_PRIORS_2526,
        }

    # ---- 5. own lines ------------------------------------------------------
    def project(home: str, away: str, hfa: float, k: float, lg: float,
                use_prior: bool = True) -> tuple[float, float]:
        h, a = ratings[home], ratings[away]
        # recompute the blend for a sensitivity run without touching the stored value
        def blend(cur, pri, gp):
            if not use_prior:
                return cur
            w = gp / (gp + k)
            return w * cur + (1 - w) * pri
        # prior deviations are already centred on the prior-season league average
        h_off = blend(f(h["pts_pg"]) - lg, h["off_prior"], h["gp"])
        h_def = blend((f(h["pts_pg"]) - f(h["plus_minus_pg"])) - lg, h["def_prior"], h["gp"])
        a_off = blend(f(a["pts_pg"]) - lg, a["off_prior"], a["gp"])
        a_def = blend((f(a["pts_pg"]) - f(a["plus_minus_pg"])) - lg, a["def_prior"], a["gp"])
        home_pts = lg + (h_off + a_def) / 2 + hfa / 2
        away_pts = lg + (a_off + h_def) / 2 - hfa / 2
        return home_pts, away_pts

    def half(x: float) -> float:
        return math.floor(x * 2 + 0.5) / 2

    lines = []
    for s in slate:
        home_pts, away_pts = project(s["home_abbr"], s["away_abbr"], HFA, K_BLEND, lg_pts)
        variants = [
            ("blend K=10, HFA 2.5", True, 10.0, 2.5),
            ("blend K=20, HFA 2.5 (default)", True, 20.0, 2.5),
            ("blend K=40, HFA 2.5", True, 40.0, 2.5),
            ("blend K=20, HFA 0.0", True, 20.0, 0.0),
            ("blend K=20, HFA 3.0", True, 20.0, 3.0),
            ("current-only, HFA 0.0", False, 0.0, 0.0),
            ("current-only, HFA 2.5", False, 0.0, 2.5),
        ]
        grid = []
        cur_only_spread = cur_only_total = None
        for label, use_prior, k, hfa in variants:
            hp, ap = project(s["home_abbr"], s["away_abbr"], hfa, k, lg_pts, use_prior)
            grid.append({"variant": label, "prior": use_prior, "k": k, "hfa": hfa,
                         "home_pts": r2(hp), "away_pts": r2(ap),
                         "spread_home": r2(hp - ap), "total": r2(hp + ap)})
            if label == "current-only, HFA 0.0":
                cur_only_spread, cur_only_total = r2(hp - ap), r2(hp + ap)
        lines.append({
            "game_id": s["game_id"], "date": s["date"], "tip_et": s["tip_et"],
            "away": s["away_team"], "home": s["home_team"],
            "away_abbr": s["away_abbr"], "home_abbr": s["home_abbr"],
            "venue": s["venue"], "city": s["city"], "comp": s["comp"],
            "own_home_pts": r2(home_pts), "own_away_pts": r2(away_pts),
            "own_spread_home": r2(home_pts - away_pts),
            "own_spread_home_half": half(home_pts - away_pts),
            "own_total": r2(home_pts + away_pts),
            "own_total_half": half(home_pts + away_pts),
            "spread_min": min(g["spread_home"] for g in grid),
            "spread_max": max(g["spread_home"] for g in grid),
            "spread_current_only_no_hfa": cur_only_spread,
            "total_current_only_no_hfa": cur_only_total,
            "total_min": min(g["total"] for g in grid),
            "total_max": max(g["total"] for g in grid),
            "market_spread": "", "market_total": "", "market_url": "",
            "sensitivity": grid,
            "source_url": s["source_url"],
        })

    # ---- 6. team-level correlations ---------------------------------------
    xs = [f(r["plus_minus_pg"]) for r in team_stats]
    ys = [f(r["win_pct"]) for r in team_stats]
    team_corr = []

    def add_team_corr(cid: str, label: str, xv: list[float], yv: list[float], unit: str) -> None:
        rr = pearson(xv, yv)
        lo, hi = fisher_ci(rr, len(xv))
        team_corr.append({"id": cid, "pair": label, "n": len(xv), "unit": unit,
                          "r": r2(rr, 4) if rr is not None else None,
                          "ci_low": r2(lo, 4) if lo is not None else None,
                          "ci_high": r2(hi, 4) if hi is not None else None,
                          "source_url": URL_TEAM_STATS})

    add_team_corr("TC1", "Net points/game x win%", xs, ys, "2026-27 team rows (n=30)")
    add_team_corr("TC2", "Points/game x win%", [f(r["pts_pg"]) for r in team_stats], ys, "2026-27 team rows (n=30)")
    add_team_corr("TC3", "Points allowed/game x win%",
                  [f(r["pts_pg"]) - f(r["plus_minus_pg"]) for r in team_stats], ys, "2026-27 team rows (n=30)")
    add_team_corr("TC4", "3P% x win%", [f(r["tp_pct"]) for r in team_stats], ys, "2026-27 team rows (n=30)")
    add_team_corr("TC5", "FG% x win%", [f(r["fg_pct"]) for r in team_stats], ys, "2026-27 team rows (n=30)")
    add_team_corr("TC6", "Turnovers/game x win%", [f(r["tov_pg"]) for r in team_stats], ys, "2026-27 team rows (n=30)")
    add_team_corr("TC7", "Net points/game x FG%", xs, [f(r["fg_pct"]) for r in team_stats], "2026-27 team rows (n=30)")

    home_w = sum(int(s["home_rec"].split("-")[0]) for s in standings)
    home_l = sum(int(s["home_rec"].split("-")[1]) for s in standings)
    road_w = sum(int(s["road_rec"].split("-")[0]) for s in standings)
    road_l = sum(int(s["road_rec"].split("-")[1]) for s in standings)
    home_rate = home_w / (home_w + home_l)
    hfa_test = {
        "home_wins": home_w, "home_losses": home_l, "road_wins": road_w, "road_losses": road_l,
        "home_win_rate": r2(home_rate, 4),
        "p_vs_0_5_two_sided": r2(binom_p_two_sided(home_w, home_w + home_l, 0.5), 5),
        "points_used": "HFA constant 2.5 remains a model choice (flag F02): the home/road split proves a home edge exists but does not measure its size in points.",
        "source_url": URL_STANDINGS,
    }

    # ---- 7. player-level correlations -------------------------------------
    pool = logs_2526 + logs_2627
    pairs = [("pts", "tpm", "PTS x 3PM"), ("pts", "reb", "PTS x REB"), ("pts", "ast", "PTS x AST"),
             ("pts", "min", "PTS x MIN"), ("reb", "ast", "REB x AST"), ("pts", "tov", "PTS x TOV"),
             ("fga", "pts", "FGA x PTS")]
    player_pairs = []
    for a, b, label in pairs:
        xv = [f(r[a]) for r in pool]
        yv = [f(r[b]) for r in pool]
        rr = pearson(xv, yv)
        lo, hi = fisher_ci(rr, len(pool))
        sub = {}
        for tag, rows in (("2025-26", logs_2526), ("2026-27", logs_2627)):
            r2v = pearson([f(r[a]) for r in rows], [f(r[b]) for r in rows])
            l2, h2 = fisher_ci(r2v, len(rows))
            sub[tag] = {"n": len(rows), "r": r2(r2v, 4) if r2v is not None else None,
                        "ci_low": r2(l2, 4) if l2 else None, "ci_high": r2(h2, 4) if h2 else None}
        player_pairs.append({"id": f"PP-{a}-{b}", "pair": label, "n": len(pool),
                             "r": r2(rr, 4) if rr is not None else None,
                             "ci_low": r2(lo, 4) if lo is not None else None,
                             "ci_high": r2(hi, 4) if hi is not None else None,
                             "by_season": sub, "source_url": URL_EDWARDS_2627})

    # ---- 8. prop-combo joint pricing --------------------------------------
    combos = [
        ("PC1", "PTS >= 25 and 3PM >= 3", lambda r: int(r["pts"]) >= 25, lambda r: int(r["tpm"]) >= 3),
        ("PC2", "PTS >= 25 and REB >= 6", lambda r: int(r["pts"]) >= 25, lambda r: int(r["reb"]) >= 6),
        ("PC3", "PTS >= 25 and AST >= 5", lambda r: int(r["pts"]) >= 25, lambda r: int(r["ast"]) >= 5),
        ("PC4", "3PM >= 3 and FTM >= 6", lambda r: int(r["tpm"]) >= 3, lambda r: int(r["ftm"]) >= 6),
        ("PC5", "PTS >= 30 and MIN >= 35", lambda r: int(r["pts"]) >= 30, lambda r: int(r["min"]) >= 35),
    ]
    prop_combos = []
    for cid, label, fa, fba in combos:
        a = b = c = d = 0
        for row in pool:
            x, y = fa(row), fba(row)
            if x and y:
                a += 1
            elif x:
                b += 1
            elif y:
                c += 1
            else:
                d += 1
        n = a + b + c + d
        pa, pb = (a + b) / n, (a + c) / n
        joint, prod = a / n, pa * pb
        prop_combos.append({
            "id": cid, "combo": label, "n": n,
            "both": a, "only_a": b, "only_b": c, "neither": d,
            "p_both": r2(joint, 4), "p_a": r2(pa, 4), "p_b": r2(pb, 4),
            "p_independent": r2(prod, 4),
            "lift": r2(joint / prod, 3) if prod > 0 else None,
            "phi": r2(phi(a, b, c, d), 4) if phi(a, b, c, d) is not None else None,
            "fair_decimal_if_independent": r2(1 / prod, 2) if prod > 0 else None,
            "fair_decimal_empirical": r2(1 / joint, 2) if joint > 0 else None,
            "source_url": URL_DONCIC_2627,
        })

    # ---- 9. serial independence (cross-game parlay assumption) ------------
    def lag1(rows: list[dict], stat: str) -> dict:
        out = {}
        for pid, name in (("1630162", "Anthony Edwards"), ("1629029", "Luka Doncic")):
            seq = sorted([r for r in rows if r["player_id"] == pid], key=lambda r: r["game_date"])
            vals = [f(r[stat]) for r in seq]
            out[name] = {"n": len(vals),
                         "lag1_r": r2(pearson(vals[:-1], vals[1:]), 4) if len(vals) > 3 else None}
        return out

    independence = {
        "lag1_pts_2025_26": lag1(logs_2526, "pts"),
        "lag1_pts_2026_27": lag1(logs_2627, "pts"),
        "note": "Lag-1 correlation of a player's own PTS across consecutive games. Small |r| supports "
                "treating legs from different games as approximately independent; it cannot prove independence.",
        "source_url": URL_EDWARDS_2627,
    }

    # ---- 10. own player prop lines ---------------------------------------
    props = []
    spec = [
        ("1630162", "Anthony Edwards", "MIN", "MIN @ NOP 2026-11-06", ["pts", "reb", "ast", "tpm"]),
        ("1629029", "Luka Doncic", "LAL", "POR @ LAL 2026-11-06", ["pts", "reb", "ast", "tpm"]),
    ]
    for pid, name, team, fixture, stats_ in spec:
        cur = [r for r in logs_2627 if r["player_id"] == pid]
        pri = [r for r in logs_2526 if r["player_id"] == pid]
        for stat in stats_:
            prior_mean = statistics.mean(f(r[stat]) for r in pri)
            cur_mean = statistics.mean(f(r[stat]) for r in cur)
            post = (K_PROP * prior_mean + len(cur) * cur_mean) / (K_PROP + len(cur))
            pooled = sorted(f(r[stat]) for r in pool if r["player_id"] == pid)
            line = half(post)
            over = sum(1 for v in pooled if v > line) / len(pooled)
            push = sum(1 for v in pooled if v == line) / len(pooled)
            props.append({
                "player_id": pid, "player": name, "team": team, "fixture": fixture,
                "stat": stat.upper(), "n_prior": len(pri), "n_current": len(cur),
                "prior_mean": r2(prior_mean), "current_mean": r2(cur_mean),
                "own_line": line, "own_mean": r2(post),
                "sd": r2(statistics.stdev(f(r[stat]) for r in pri), 2),
                "pooled_n": len(pooled),
                "empirical_over_rate": r2(over, 4),
                "empirical_push_rate": r2(push, 4),
                "market_line": "", "market_url": "",
                "source_url": URL_EDWARDS_2627 if pid == "1630162" else URL_DONCIC_2627,
            })

    availability = {
        "MIN_gp": int(team_stats_by_abbr(team_stats, "MIN")["gp"]),
        "MIN_edwards_log_rows": len([r for r in logs_2627 if r["player_id"] == "1630162"]),
        "LAL_gp": int(team_stats_by_abbr(team_stats, "LAL")["gp"]),
        "LAL_doncic_log_rows": len([r for r in logs_2627 if r["player_id"] == "1629029"]),
        "source_url": URL_EDWARDS_2627,
    }

    # ---- 11. luck vs skill engine ----------------------------------------
    be = breakeven_from_american(-110)
    power_rows = []
    for p1 in (0.55, 0.58, 0.60, 0.65):
        power_rows.append({"true_rate": p1,
                           "required_n_80pct": required_n(be, p1),
                           "required_n_90pct": required_n(be, p1, power=0.90),
                           "normal_approx_n_80pct": normal_n(be, p1),
                           "note": "exact one-sided binomial power search"})
    power_rows.insert(0, {"true_rate": 0.53, "required_n_80pct": None, "required_n_90pct": None,
                          "normal_approx_n_80pct": normal_n(be, 0.53),
                          "note": "beyond the 25,000-bet cap: a 53% true edge is not certifiable in any realistic window; approximation only"})
    m_tests = 8
    luck = {
        "breakeven_110": r2(be, 6),
        "breakeven_formula": "110 / (110 + 100) for a -110 price (arithmetic, not an NBA statistic)",
        "power_vs_breakeven": power_rows,
        "alpha_family": {"tests": m_tests, "alpha": 0.05,
                         "bonferroni_alpha": r2(0.05 / m_tests, 5),
                         "sidak_alpha": r2(1 - (1 - 0.05) ** (1 / m_tests), 5),
                         "source": "https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html"},
        "illustrations": [
            {"scenario": "Break-even bettor (p = break-even) goes 55-45 over 100 bets",
             "p_value_two_sided": r2(binom_p_two_sided(55, 100, be), 4),
             "reading": "Not evidence of skill at alpha=0.05."},
            {"scenario": "Break-even bettor reaches at least 55% over 200 bets",
             "probability": r2(binom_sf(110, 200, be), 4),
             "reading": "Runs this hot purely by chance a large fraction of the time."},
            {"scenario": "True 55% bettor, 200 bets, one-sided alpha=0.05",
             "probability_of_detection": r2(binom_sf(next(k for k in range(201) if binom_sf(k, 200, be) <= 0.05), 200, 0.55), 4),
             "reading": "Power is far below 80% — 200 bets cannot certify a 55% edge."},
        ],
        "deflation_rule": {
            "prior_pseudo_bets": PRIOR_PSEUDO,
            "formula": "(wins + K*p0) / (n + K) with K = 25, p0 = break-even rate",
            "example": {"wins": 55, "n": 100, "deflated_rate": r2((55 + PRIOR_PSEUDO * be) / (100 + PRIOR_PSEUDO), 4)},
            "note": "Shrinks a short hot streak toward break-even before it can enter the leaderboard.",
        },
        "citations": [
            {"id": "M1", "title": "Bailey, Borwein, Lopez de Prado, Zhu (2014) — Pseudo-Mathematics and Financial Charlatanism",
             "url": "https://www.ams.org/notices/201405/rnoti-p458.pdf", "checked": "fetched 2026-11-05"},
            {"id": "M2", "title": "Bailey & Lopez de Prado (2014) — The Deflated Sharpe Ratio",
             "url": "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf", "checked": "search metadata 2026-11-05"},
            {"id": "M3", "title": "Kaunitz, Zhong, Kreiner (2017) — Beating the bookies with their own numbers",
             "url": "https://arxiv.org/abs/1710.02824", "checked": "search metadata 2026-11-05"},
            {"id": "M4", "title": "statsmodels — multiple-testing corrections (Holm, Sidak, Bonferroni)",
             "url": "https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html", "checked": "fetched 2026-11-05"},
        ],
    }

    # ---- 12. gates --------------------------------------------------------
    gates = [
        ("G01", "Provenance", "Every value has an official nba.com URL and a snapshot date; no value is inferred.", "all rows", "PASS this session", URL_STANDINGS),
        ("G02", "As-of integrity", "Snapshot taken before tip-off of the listed games; no post-game information in features.", "all", "PASS (snapshot 2026-11-05; games tip 2026-11-05 21:00 ET / 2026-11-06)", URL_SCHEDULE),
        ("G03", "Pre-registration", "Strategy rules frozen before any price is observed; the rule text is published verbatim.", "all", "PASS (rules frozen in strategies.csv before any pricing)", URL_SCHEDULE),
        ("G04", "Sample adequacy", "n must exceed the exact-binomial requirement for the claimed edge at alpha=0.05 / power 0.80.", "all", "FAIL (n=0 graded bets)", URL_STANDINGS),
        ("G05", "Out-of-sample", "Second, non-overlapping evaluation window after the rule is frozen.", "all", "FAIL (no evaluation window)", URL_STANDINGS),
        ("G06", "Calibration", "Held-out Brier score must beat the no-vig market baseline; reliability inspected.", "moneyline/spread", "BLOCKED (no market baseline)", URL_STANDINGS),
        ("G07", "Market price", "A timestamped, de-viggable price from a named book is required for any edge, CLV or ROI.", "all", "BLOCKED (no verified odds source)", URL_SCHEDULE),
        ("G08", "Joint pricing", "Combo legs priced from empirical joint outcomes, not the product of marginals.", "parlays/combos", "PARTIAL (joint rates computed; no price)", URL_DONCIC_2627),
        ("G09", "Multiple testing", "Holm/Bonferroni-adjusted alpha across every candidate tried.", "all", "PENDING (no p-values yet)", "https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html"),
        ("G10", "Luck deflation", "Deflated (shrunken) rate and deflated Sharpe framework applied before ranking.", "leaderboard", "PASS (rule implemented)", "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf"),
        ("G11", "Robustness", "Sensitivity across model parameters (K, HFA) published for every line.", "own lines", "PASS (3x3 grid per game)", URL_TEAM_STATS),
        ("G12", "Prospective replication", "Frozen paper-trading window with a pre-committed stopping rule.", "all", "PENDING (not started)", "https://arxiv.org/abs/1710.02824"),
    ]
    gates_out = [{"id": g[0], "name": g[1], "rule": g[2], "applies": g[3], "status": g[4], "source_url": g[5]}
                 for g in gates]

    # ---- 13. strategies ---------------------------------------------------
    def gate_state(extra: dict | None = None) -> list[dict]:
        base = {g["id"]: g["status"] for g in gates_out}
        if extra:
            base.update(extra)
        return [{"id": k, "status": v} for k, v in base.items()]

    strategies = [
        {"id": "S01", "family": "Single", "name": "Own-line spread disagreement",
         "rule": "Bet the side where |own spread - market spread| >= 2.0 points, only if the market is at least 30 minutes old and the price is at -110 or better.",
         "inputs": "own_spread_home (lines table); market spread (missing)", "corr": "n/a (single leg)",
         "required_n": required_n(be, 0.55), "graded_bets": 0, "status": "PENDING", "blocked_by": "G07"},
        {"id": "S02", "family": "Single", "name": "Own-line total disagreement",
         "rule": "Bet over/under where |own total - market total| >= 3.0 points, price at -110 or better.",
         "inputs": "own_total (lines table); market total (missing)", "corr": "spread x total within a game is not modelled",
         "required_n": required_n(be, 0.55), "graded_bets": 0, "status": "PENDING", "blocked_by": "G07"},
        {"id": "S03", "family": "Single", "name": "Moneyline value",
         "rule": "Bet the moneyline side whose de-vigged market probability is below the model probability by >= 3 percentage points.",
         "inputs": "moneyline model (BLOCKED: margin SD constant unverified)", "corr": "n/a",
         "required_n": required_n(be, 0.55), "graded_bets": 0, "status": "BLOCKED", "blocked_by": "G07 / F08"},
        {"id": "S04", "family": "Parlay (2-leg)", "name": "Two cross-game spread singles",
         "rule": "Combine two S01 qualifiers from different games; only if the offered parlay price beats the independence price by >= 3%.",
         "inputs": "two S01 legs", "corr": "cross-game independence assumed, tested only weakly (lag-1 table)",
         "required_n": required_n(be, 0.55), "graded_bets": 0, "status": "PENDING", "blocked_by": "G07"},
        {"id": "S05", "family": "Parlay (3-leg)", "name": "Three cross-game singles",
         "rule": "As S04 with three legs; independence price = product of leg probabilities.",
         "inputs": "three S01 qualifiers", "corr": "cross-game independence",
         "required_n": required_n(be, 0.55), "graded_bets": 0, "status": "PENDING", "blocked_by": "G07"},
        {"id": "S06", "family": "Prop combo (same game)", "name": "PTS + 3PM, Edwards",
         "rule": "Same-game combo PTS >= L and 3PM >= K for Anthony Edwards; price from the empirical joint rate (PC1), never from the product of marginals.",
         "inputs": "prop table (Edwards) + PC1 joint rate", "corr": "see PP-pts-tpm and PC1",
         "required_n": required_n(be, 0.55), "graded_bets": 0, "status": "PENDING", "blocked_by": "G07 / G08"},
        {"id": "S07", "family": "Prop combo (same game)", "name": "PTS + AST, Doncic",
         "rule": "Same-game combo PTS >= L and AST >= K for Luka Doncic; price from the empirical joint rate (PC3).",
         "inputs": "prop table (Doncic) + PC3 joint rate", "corr": "see PP-pts-ast and PC3",
         "required_n": required_n(be, 0.55), "graded_bets": 0, "status": "PENDING", "blocked_by": "G07 / G08"},
        {"id": "S08", "family": "Prop parlay (cross-game)", "name": "Edwards PTS + Doncic PTS",
         "rule": "Two-leg cross-game prop parlay; independence allowed only while the lag-1 table shows |r| < 0.10 for both players.",
         "inputs": "prop table (both players)", "corr": "lag-1 table (both players)",
         "required_n": required_n(be, 0.55), "graded_bets": 0, "status": "PENDING", "blocked_by": "G07"},
    ]
    for s in strategies:
        s["gates"] = [{"id": gid, "status": st} for gid, st in (
            ("G01", "PASS"), ("G02", "PASS"), ("G03", "PASS"), ("G04", "FAIL"), ("G05", "FAIL"),
            ("G06", "BLOCKED"), ("G07", "BLOCKED"), ("G08", "PARTIAL" if s["family"].startswith(("Prop", "Parlay")) else "n/a"),
            ("G09", "PENDING"), ("G10", "PASS"), ("G11", "PASS"), ("G12", "PENDING"))]
        s["certified"] = False

    # ---- 14. leaderboard -------------------------------------------------
    leaderboard = {
        "unit": "audit unit (1 unit = 1 flat stake at the observed price)",
        "scoring": "score = deflated_rate * sqrt(n) * mean_de_vigged_CLV_sign, with deflated_rate = (wins + 25*p0)/(n + 25)",
        "tiers": [{"place": 1, "share": "50% of pool", "amount": "", "amount_status": "blank — pool unfunded (F09)"},
                  {"place": 2, "share": "30% of pool", "amount": "", "amount_status": "blank — pool unfunded (F09)"},
                  {"place": 3, "share": "20% of pool", "amount": "", "amount_status": "blank — pool unfunded (F09)"}],
        "minimum_bets_to_rank": required_n(be, 0.55),
        "entries": [],
        "entries_note": "No entry is graded: no strategy has a settled bet (G04/G07 fail closed).",
        "anti_gaming": [
            "Only pre-registered rules may be scored; a rule changed mid-window restarts its sample at zero.",
            "Legs must be priced from the same snapshot; any leg without a verified price voids the entry.",
        ],
        "source_url": URL_STANDINGS,
    }

    # ---- 15. flags ------------------------------------------------------
    flags = [
        ("F01", "No verified market odds", "High", "No timestamped price from a named sportsbook was obtained in this session (sandbox outbound access is limited to GitHub hosts; nba.com is reachable only through the page fetcher, which does not serve book prices). Every edge, CLV, ROI and reward cell is therefore blank.", "lines, props, strategies, leaderboard", URL_SCHEDULE),
        ("F02", "Home-court advantage is a constant", "Medium", "HFA = 2.5 points is a model choice. The official 2026-27 home/road split (62-59, two-sided p = 0.856) does not even establish a home edge at this sample size, let alone measure its size in points.", "own lines", URL_STANDINGS),
        ("F03", "Small samples", "High", "2026-27 teams have played 6-9 games; prop logs contain 4 (Edwards) and 8 (Doncic) 2026-27 games. Shrinkage is applied and flagged.", "own lines, props, correlations", URL_TEAM_STATS),
        ("F04", "Edwards participation", "High", "Anthony Edwards appears in 4 of Minnesota's 9 games on the official box-score page; the reason is not on the page and no official injury report was accessed. Availability is unverified.", "props, S06, S08", URL_EDWARDS_2627),
        ("F05", "Games page static render is empty", "Low", "https://www.nba.com/games?date=2026-11-05 renders 'No Games Scheduled' while the official month calendar on the same page shows 2 games for 2026-11-05. The slate was transcribed from /schedule instead; the discrepancy is recorded, not resolved.", "slate", "https://www.nba.com/games?date=2026-11-05"),
        ("F06", "NBA Cup treatment unverified", "Medium", "Nine of the eleven slate games are Emirates NBA Cup group-play games listed on the regular-season schedule. Whether/how they count toward the standings is NOT verified in this session.", "slate, standings", URL_SCHEDULE),
        ("F07", "2025-26 prior table is secondhand", "Medium", "The prior-season team table was transcribed by session 6d508fee and reused here. Internal consistency was re-checked (X08); the underlying page was not re-fetched in this session.", "own lines", URL_PRIORS_2526),
        ("F08", "Moneyline model blocked", "High", "A win-probability model needs a margin standard deviation and a calibration constant; neither is verified from an official source, so moneyline probabilities are left blank.", "S03", URL_STANDINGS),
        ("F09", "Prize pool unfunded", "Medium", "Reward tiers are proposals. No sponsor, budget or payout mechanism exists; amounts stay blank.", "leaderboard", URL_STANDINGS),
        ("F10", "Prop settlement rules unverified", "High", "Void, DNP, stat-correction and overtime/OT-inclusive scoring rules for player props were not verified against any operator's published rules.", "props", URL_DONCIC_2627),
        ("F11", "No injury/availability feed", "High", "No official NBA injury report or official availability feed was accessed; all prop lines are unconditional on participation.", "props", URL_EDWARDS_2627),
        ("F12", "Prior table net does not sum to zero", "Low", "Sum of (net points/game x GP) in the reused 2025-26 table is -16.4 over 2,460 team-games; consistent with 1-decimal rounding per row but recorded as an irregularity.", "own lines", URL_PRIORS_2526),
        ("F13", "Cyrillic character in an inherited CSV header", "Low", "nba-signal-lab/data/teams_2025_26.csv and teams_2026_27.csv name a column 'blkа_pg' with U+0430 CYRILLIC SMALL LETTER A instead of ASCII 'a'. This session's copy normalises the key; the source files are owned by another session and were not edited.", "repo audit", "https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season"),
        ("F15", "Independence inference is weak by construction", "High", "Session eeddab9b's independent audit (2026-11-05) flags that inferring cross-game independence from two players with wide intervals is too strong, and that pooled two-player prop rates need clustered and out-of-sample validation. This board agrees: its own lag-1 table (n = 61 and 64 games, |r| < 0.06) is published with the explicit caveat that it cannot prove independence, and every cross-game parlay (S04, S05, S08) stays blocked. No certification anywhere in this board rests on the independence assumption.", "independence, parlays, leaderboard", "https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26"),
        ("F14", "Standings GB column is win%-based", "Low", "Conference leaders show GB '--' even when their records differ in games played (POR 6-1 above LAL/HOU 7-2 in the West). GB is computed against win% rank, not games behind; read it with care.", "standings", URL_STANDINGS),
    ]
    flags.sort(key=lambda f: int(f[0][1:]))
    flags_out = [{"id": f[0], "title": f[1], "severity": f[2], "detail": f[3], "scope": f[4], "source_url": f[5]}
                 for f in flags]

    # ---- 16. sources ----------------------------------------------------
    sources = [
        {"id": "E1", "publisher": "NBA.com", "title": "2026-27 regular-season standings",
         "url": URL_STANDINGS, "used_for": "30 team rows: W-L, GB, CONF/DIV/HOME/ROAD/NEUTRAL/OT/L10/STREAK", "fetched": SNAPSHOT},
        {"id": "E2", "publisher": "NBA.com", "title": "Team traditional stats, 2026-27 regular season (per game)",
         "url": URL_TEAM_STATS, "used_for": "30 team rows: GP, W-L, shooting, rebounds, turnovers, net points", "fetched": SNAPSHOT},
        {"id": "E3", "publisher": "NBA.com", "title": "Schedule, 2026-11-05 / 2026-11-06",
         "url": URL_SCHEDULE, "used_for": "11 slate games: date, tip time (ET), venue, city, competition", "fetched": SNAPSHOT},
        {"id": "E4", "publisher": "NBA.com", "title": "Anthony Edwards 2026-27 game log",
         "url": URL_EDWARDS_2627, "used_for": "4 player-game rows; headline averages used as a checksum", "fetched": SNAPSHOT},
        {"id": "E5", "publisher": "NBA.com", "title": "Luka Doncic 2026-27 game log",
         "url": URL_DONCIC_2627, "used_for": "8 player-game rows; headline averages used as a checksum", "fetched": SNAPSHOT},
        {"id": "E6", "publisher": "NBA.com", "title": "Anthony Edwards 2025-26 game log (early-window re-fetch)",
         "url": URL_EDWARDS_2526, "used_for": "independent re-fetch of 6 rows already present in the inherited 2025-26 log", "fetched": SNAPSHOT},
        {"id": "E7", "publisher": "NBA.com", "title": "Team traditional stats, 2025-26 regular season",
         "url": URL_PRIORS_2526, "used_for": "prior-season team means used only as the shrinkage prior (transcribed by session 6d508fee; not re-fetched)", "fetched": "2026-11-03 (inherited)"},
        {"id": "M1", "publisher": "Notices of the AMS", "title": "Pseudo-Mathematics and Financial Charlatanism (Bailey, Borwein, Lopez de Prado, Zhu 2014)",
         "url": "https://www.ams.org/notices/201405/rnoti-p458.pdf", "used_for": "backtest-overfitting / multiple-testing framing", "fetched": SNAPSHOT},
        {"id": "M2", "publisher": "David H. Bailey (author copy)", "title": "The Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014)",
         "url": "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf", "used_for": "deflation concept (implemented only as a shrunken rate)", "fetched": "search metadata only"},
        {"id": "M3", "publisher": "arXiv", "title": "Beating the bookies with their own numbers (Kaunitz, Zhong, Kreiner 2017)",
         "url": "https://arxiv.org/abs/1710.02824", "used_for": "context for market efficiency and account limiting; no result imported", "fetched": "search metadata only"},
        {"id": "M4", "publisher": "statsmodels", "title": "multipletests — Holm / Sidak / Bonferroni corrections",
         "url": "https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html", "used_for": "family-wise error corrections", "fetched": SNAPSHOT},
    ]

    outputs = {
        "meta": {
            "session": "arena-a46d621e",
            "snapshot": SNAPSHOT,
            "snapshot_note": "Official pages fetched 2026-11-05 (UTC) through the platform page fetcher; "
                             "the sandbox cannot reach nba.com over curl.",
            "parameters": {"K_BLEND": K_BLEND, "K_PROP": K_PROP, "HFA": HFA, "PRIOR_PSEUDO": PRIOR_PSEUDO},
            "league_avg_points": r2(lg_pts),
            "league_avg_points_prior": r2(lg_pts_prior),
            "team_games_in_sample": gp_all,
            "games_originated": len(lines),
            "props_originated": len(props),
            "strategies": len(strategies),
            "strategies_certified": sum(1 for s in strategies if s["certified"]),
            "graded_bets": 0,
        },
        "checks": checks,
        "team_ratings": list(ratings.values()),
        "lines": lines,
        "team_correlations": team_corr,
        "hfa_test": hfa_test,
        "player_pairs": player_pairs,
        "prop_combos": prop_combos,
        "independence": independence,
        "props": props,
        "availability": availability,
        "luck": luck,
        "gates": gates_out,
        "strategies": strategies,
        "leaderboard": leaderboard,
        "flags": flags_out,
        "sources": sources,
    }
    OUT.write_text(json.dumps(outputs, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    failed = [c for c in checks if not c["passed"]]
    print(f"wrote {OUT.relative_to(ROOT.parent)}")
    print(f"checks: {len(checks)} run, {len(failed)} failed")
    for c in failed:
        print("  FAIL", c["id"], c["detail"])
    print(f"lines: {len(lines)}  props: {len(props)}  correlations: {len(team_corr)}+{len(player_pairs)}+{len(prop_combos)}")
    print(f"certified strategies: {outputs['meta']['strategies_certified']} / {len(strategies)}")


def team_stats_by_abbr(rows: list[dict], abbr: str) -> dict:
    for r in rows:
        if r["abbr"] == abbr:
            return r
    raise KeyError(abbr)


if __name__ == "__main__":
    main()

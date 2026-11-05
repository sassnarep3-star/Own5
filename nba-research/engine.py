#!/usr/bin/env python3
"""Deterministic NBA research engine (standard library only).

This module originates experimental lines and evaluates governance gates. It never
places a bet, invents a missing outcome, or certifies a strategy from an empty ledger.
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
AS_OF = "2026-11-05"
MODEL_VERSION = "nba-research-1.0.0"
SHRINKAGE_GAMES = 20.0  # disclosed analyst policy, not an NBA estimate
HOME_POINTS = 0.0       # neutral baseline; sensitivity below is not an estimate
SENSITIVITY_HOME_POINTS = (-2.0, 0.0, 2.0)
BOOTSTRAP_REPS = 1000
BOOTSTRAP_BLOCK = 5
SEED = 20261105
NBA_ADV = "https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular+Season&PerMode=PerGame"
NBA_PRIOR = "https://www.nba.com/stats/teams/advanced?Season=2025-26&SeasonType=Regular+Season&PerMode=PerGame"
NBA_GLOSSARY = "https://www.nba.com/stats/help/glossary"
NBA_SCHEDULE = "https://www.nba.com/schedule?date=2026-11-05"
FD_BOARD = "https://sportsbook.fanduel.com/navigation/nba?tab=parlay-builder"
DSR_URL = "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf"
PBO_URL = "https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf"
NIST_URL = "https://www.itl.nist.gov/div898/handbook/prc/section2/old.prc271.htm"


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name: str, fields: Sequence[str], rows: Iterable[dict]) -> None:
    with (DATA / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def fnum(x: object, default: float | None = None) -> float | None:
    if x is None or x == "":
        return default
    return float(x)


def rounded(x: float | None, digits: int = 3) -> str:
    return "" if x is None else f"{x:.{digits}f}"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_hash(obj: object) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    n = len(xs)
    if n != len(ys) or n < 3:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    dx, dy = [x - mx for x in xs], [y - my for y in ys]
    den = math.sqrt(math.fsum(x * x for x in dx) * math.fsum(y * y for y in dy))
    return math.fsum(x * y for x, y in zip(dx, dy)) / den if den else None


def block_bootstrap_ci(rows: Sequence[dict], xkey: str, ykey: str,
                       reps: int = BOOTSTRAP_REPS, block: int = BOOTSTRAP_BLOCK,
                       seed: int = SEED) -> tuple[float | None, float | None]:
    """Conditional moving-block CI, stratified by player.

    Blocks preserve short within-player dependence. With only two selected players,
    this is NOT a population CI for NBA players and does not validate parlay legs.
    """
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r["player_id"]].append(r)
    for g in groups.values():
        g.sort(key=lambda r: (r["game_date"], r["game_id"]))
    if any(len(g) < block + 2 for g in groups.values()):
        return None, None
    rng = random.Random(seed)
    vals: list[float] = []
    for _ in range(reps):
        xs, ys = [], []
        for g in groups.values():
            drawn = 0
            while drawn < len(g):
                start = rng.randrange(len(g) - block + 1)
                take = min(block, len(g) - drawn)
                for r in g[start:start + take]:
                    xs.append(float(r[xkey])); ys.append(float(r[ykey]))
                drawn += take
        v = pearson(xs, ys)
        if v is not None:
            vals.append(v)
    if len(vals) < reps * 0.95:
        return None, None
    vals.sort()
    def quantile(q: float) -> float:
        pos = (len(vals) - 1) * q
        lo, hi = math.floor(pos), math.ceil(pos)
        return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)
    return quantile(0.025), quantile(0.975)


def binom_pmf(k: int, n: int, p: float) -> float:
    if k < 0 or k > n:
        return 0.0
    if p <= 0:
        return 1.0 if k == 0 else 0.0
    if p >= 1:
        return 1.0 if k == n else 0.0
    logp = (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
            + k * math.log(p) + (n - k) * math.log1p(-p))
    return math.exp(logp)


def binom_cdf(k: int, n: int, p: float) -> float:
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    return max(0.0, min(1.0, 1.0 - binom_sf(k + 1, n, p)))


def binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k), including k, by summing the smaller tail with a stable recurrence."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    terms: list[float] = []
    if k > n * p:
        term = binom_pmf(k, n, p)
        i = k
        while True:
            terms.append(term)
            if i == n:
                break
            term *= (n - i) / (i + 1) * p / (1 - p)
            i += 1
            if term < 1e-18 * max(math.fsum(terms), 1e-300):
                break
        return min(1.0, math.fsum(terms))
    # Sum P(X < k) downward from k-1, then complement.
    term = binom_pmf(k - 1, n, p)
    i = k - 1
    while True:
        terms.append(term)
        if i == 0:
            break
        term *= i / (n - i + 1) * (1 - p) / p
        i -= 1
        if term < 1e-18 * max(math.fsum(terms), 1e-300):
            break
    return max(0.0, min(1.0, 1.0 - math.fsum(terms)))


def critical_successes(n: int, p0: float, alpha: float) -> int:
    lo, hi = 0, n + 1
    while lo < hi:
        mid = (lo + hi) // 2
        if binom_sf(mid, n, p0) <= alpha:
            hi = mid
        else:
            lo = mid + 1
    return lo


def exact_power(n: int, p0: float, p1: float, alpha: float) -> float:
    k = critical_successes(n, p0, alpha)
    return binom_sf(k, n, p1) if k <= n else 0.0


def minimum_n(p0: float, p1: float, alpha: float = 0.05, power: float = 0.80) -> int:
    if not (0 < p0 < p1 < 1 and 0 < alpha < 1 and 0 < power < 1):
        raise ValueError("require 0<p0<p1<1 and valid alpha/power")
    z_a, z_b = 1.6448536269514722, 0.8416212335729143  # one-sided .05 and .80 starts only
    start = ((z_a * math.sqrt(p0 * (1-p0)) + z_b * math.sqrt(p1 * (1-p1))) / (p1-p0)) ** 2
    n = max(2, int(start * 0.75))
    while exact_power(n, p0, p1, alpha) < power:
        n += 1
    # The normal approximation is only a starting point; verify local exact minimum.
    while n > 2 and exact_power(n - 1, p0, p1, alpha) >= power:
        n -= 1
    return n


def clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    if n <= 0 or not 0 <= k <= n:
        raise ValueError("invalid binomial counts")
    def lower() -> float:
        if k == 0:
            return 0.0
        lo, hi = 0.0, 1.0
        for _ in range(70):
            mid = (lo + hi) / 2
            if binom_sf(k, n, mid) > alpha / 2:
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2
    def upper() -> float:
        if k == n:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(70):
            mid = (lo + hi) / 2
            if binom_cdf(k, n, mid) > alpha / 2:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    return lower(), upper()


def american_to_decimal(price: int | float) -> float:
    p = float(price)
    if p == 0:
        raise ValueError("American price cannot be zero")
    return 1 + (p / 100 if p > 0 else 100 / abs(p))


def american_to_prob(price: int | float) -> float:
    p = float(price)
    return 100 / (p + 100) if p > 0 else abs(p) / (abs(p) + 100)


def no_vig(prices: Sequence[int | float]) -> list[float]:
    raw = [american_to_prob(p) for p in prices]
    s = math.fsum(raw)
    if s <= 1:
        raise ValueError("two-sided market must have positive overround for this snapshot")
    return [q / s for q in raw]


def holm_adjust(pvals: Sequence[float], alpha: float = 0.05) -> list[dict]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adjusted, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adjusted[i] = running
    return [{"index": i, "p": pvals[i], "adjusted_p": adjusted[i],
             "reject": adjusted[i] <= alpha} for i in range(m)]


def _skew_kurt(x: Sequence[float]) -> tuple[float, float]:
    n = len(x)
    m = statistics.mean(x)
    m2 = math.fsum((v-m)**2 for v in x) / n
    if m2 <= 0:
        return 0.0, 3.0
    m3 = math.fsum((v-m)**3 for v in x) / n
    m4 = math.fsum((v-m)**4 for v in x) / n
    return m3 / m2**1.5, m4 / m2**2  # Pearson kurtosis, normal = 3


def deflated_sharpe(returns: Sequence[float], trial_sharpes: Sequence[float]) -> float | None:
    """Per-period DSR using the paper's expected-maximum threshold.

    trial_sharpes must contain the full comparable trial family on the same return
    frequency. Independence/effective-N is an external modeling requirement; this
    function cannot repair an undisclosed search history.
    """
    n = len(returns)
    if n < 30 or len(trial_sharpes) < 2:
        return None
    sd = statistics.stdev(returns)
    if sd <= 0:
        return None
    sr = statistics.mean(returns) / sd
    skew, kurt = _skew_kurt(returns)
    denom = 1 - skew * sr + ((kurt - 1) / 4) * sr * sr
    if denom <= 0:
        return None
    var = statistics.variance(trial_sharpes)
    if var <= 0:
        return None
    gamma = 0.5772156649015329
    N = len(trial_sharpes)
    # Expected max of N standard normals, Euler approximation used in the paper.
    emax = ((1-gamma) * _norm_ppf(1 - 1/N) + gamma * _norm_ppf(1 - 1/(N*math.e))) if N > 1 else 0.0
    sr0 = math.sqrt(var) * emax
    z = (sr - sr0) * math.sqrt(n - 1) / math.sqrt(denom)
    return _norm_cdf(z)


def _norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _norm_ppf(p: float) -> float:
    if not 0 < p < 1:
        raise ValueError("p outside (0,1)")
    lo, hi = -10.0, 10.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if _norm_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def cscv_pbo(trial_returns: Sequence[Sequence[float]], blocks: int = 8) -> float | None:
    """Combinatorially symmetric cross-validation PBO for an aligned trial matrix.

    Rows are time periods, columns are strategies/trials. Contiguous blocks preserve
    local order inside each partition. Returns None when evidence is insufficient.
    """
    t = len(trial_returns)
    if blocks < 4 or blocks % 2 or t < blocks * 4:
        return None
    n_trials = len(trial_returns[0])
    if n_trials < 2 or any(len(r) != n_trials for r in trial_returns):
        return None
    bounds = [round(i*t/blocks) for i in range(blocks+1)]
    parts = [trial_returns[bounds[i]:bounds[i+1]] for i in range(blocks)]
    logits = []
    for train_idx in itertools.combinations(range(blocks), blocks//2):
        train_set = set(train_idx)
        train = [r for i, part in enumerate(parts) if i in train_set for r in part]
        test = [r for i, part in enumerate(parts) if i not in train_set for r in part]
        def sharpes(mat: list[Sequence[float]]) -> list[float]:
            out = []
            for j in range(n_trials):
                col = [r[j] for r in mat]
                sd = statistics.stdev(col)
                out.append(statistics.mean(col)/sd if sd > 0 else 0.0)
            return out
        tr, te = sharpes(train), sharpes(test)
        best = max(range(n_trials), key=lambda j: tr[j])
        rank = sum(v <= te[best] for v in te)  # 1=worst, n=best
        w = rank / (n_trials + 1)
        logits.append(math.log(w / (1-w)))
    return sum(v <= 0 for v in logits) / len(logits) if logits else None


GATES = [
    ("G01", "Official provenance and schema", "Every factual input has an official source link; unknowns stay blank; integrity checks pass."),
    ("G02", "Frozen pre-registration and trial count", "Rules/thresholds and the complete comparable trial family are hashed before outcome evaluation."),
    ("G03", "Point-in-time leakage audit", "Walk-forward features use only information available before the archived decision; no future data or survivor substitution."),
    ("G04", "Power and effective sample size", "Predeclared economically meaningful effect reaches >=80% exact/dependence-aware power with adequate independent settlement clusters."),
    ("G05", "Dependence and exact joint pricing", "The actual legs' joint distribution is validated; shared games/overlaps and pushes/voids are handled; no blind marginal multiplication."),
    ("G06", "Out-of-sample market calibration", "Frozen holdout probabilities beat the applicable no-vig market benchmark on paired log loss/Brier with uncertainty."),
    ("G07", "Net economics and uncertainty", "Timestamped prices, fees, voids and settlement yield a positive lower uncertainty bound on net ROI; CLV is recorded separately."),
    ("G08", "Selection-bias control", "Holm-adjusted primary tests plus DSR>=0.95 with full effective trial count; CSCV/PBO<=0.50 when a valid trial matrix exists."),
    ("G09", "Prospective replication and execution", "A predeclared live/paper window replicates the result with auditable quotes and decisions; no retroactive rule changes."),
    ("G10", "Reproducible fail-closed release", "Deterministic build, tests, links and review flags pass; missing evidence blocks certification rather than filling values."),
]


def verify_inputs(d: dict[str, list[dict]]) -> list[dict]:
    checks: list[dict] = []
    def add(name: str, ok: bool, detail: str, url: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": detail, "source_url": url})
    cur, prior, trad, stand = d["team_advanced_2026_27.csv"], d["team_advanced_2025_26.csv"], d["team_traditional_2026_27.csv"], d["standings_2026_27.csv"]
    ids = lambda rows: {r["team_id"] for r in rows}
    add("Thirty-team coverage", all(len(r)==30 and len(ids(r))==30 for r in (cur,prior,trad,stand)) and ids(cur)==ids(prior)==ids(trad)==ids(stand), "Four official tables contain the same 30 unique team IDs.", NBA_ADV)
    cmap = {r["team_id"]: r for r in cur}; tmap = {r["team_id"]: r for r in trad}; smap = {r["team_id"]: r for r in stand}
    add("Current record reconciliation", all((int(cmap[i]["w"]),int(cmap[i]["l"]))==(int(tmap[i]["w"]),int(tmap[i]["l"]))==(int(smap[i]["w"]),int(smap[i]["l"])) for i in cmap), "W-L agrees across advanced, traditional and standings for all 30 teams.", "https://www.nba.com/standings?Season=2026-27")
    add("Games equal wins plus losses", all(int(r["gp"])==int(r["w"])+int(r["l"]) for r in cur+prior+trad) and all(int(cmap[r["team_id"]]["gp"])==int(r["w"])+int(r["l"]) for r in stand), "All 120 team-table rows reconcile GP to W+L.", NBA_ADV)
    def split_ok(r: dict) -> bool:
        hw,hl=map(int,r["home_rec"].split("-")); rw,rl=map(int,r["road_rec"].split("-")); nw,nl=map(int,r["neutral_rec"].split("-"))
        return hw+rw+nw==int(r["w"]) and hl+rl+nl==int(r["l"])
    add("Standings split reconciliation", all(split_ok(r) for r in stand), "Home+road+neutral equals total W-L; OT is a subset and is not added again.", "https://www.nba.com/standings?Season=2026-27")
    add("League win-loss balance", all(sum(int(r["w"]) for r in rows)==sum(int(r["l"]) for r in rows) for rows in (cur,prior)), "League wins equal losses in both seasons.", NBA_PRIOR)
    add("Official rating identity", all(abs(float(r["off_rating"])-float(r["def_rating"])-float(r["net_rating"]))<=0.11 for r in cur+prior), "NetRtg equals OffRtg-DefRtg within one-decimal rounding tolerance.", NBA_GLOSSARY)
    add("Traditional scoring identity", all(abs(2*float(r["fgm"])+float(r["tpm"])+float(r["ftm"])-float(r["pts"]))<=0.21 for r in trad), "PTS equals 2*FGM+3PM+FTM within the 0.20 bound from four one-decimal inputs plus display rounding.", "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular+Season&PerMode=PerGame")
    add("Rebound identity", all(abs(float(r["oreb"])+float(r["dreb"])-float(r["reb"]))<=0.11 for r in trad), "OREB+DREB equals REB within rounding tolerance.", NBA_GLOSSARY)
    def pct_interval_ok(r: dict, a: str, b: str, pct: str) -> bool:
        # Official percentages use season totals; per-game makes/attempts are rounded.
        # Propagate +/-0.05 through the ratio rather than assume exact per-game inputs.
        av,bv,pv=float(r[a]),float(r[b]),float(r[pct])
        lo=100*(av-0.05)/(bv+0.05); hi=100*(av+0.05)/(bv-0.05)
        return lo-0.051 <= pv <= hi+0.051
    shooting = all(pct_interval_ok(r,a,b,pct) for r in trad for a,b,pct in (("fgm","fga","fg_pct"),("tpm","tpa","tp_pct"),("ftm","fta","ft_pct")))
    add("Shooting percentage identities", shooting, "All 90 displayed FG/3P/FT percentages lie within ratio intervals propagated from rounded per-game makes/attempts.", "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular+Season&PerMode=PerGame")
    logs, players = d["player_games.csv"], d["players.csv"]
    add("Player log coverage and uniqueness", len(logs)==125 and len({(r["player_id"],r["game_id"]) for r in logs})==125 and all(sum(r["player_id"]==p["player_id"] for r in logs)==int(p["gp"]) for p in players), "61 Edwards + 64 Dončić rows; no duplicate player-game keys; counts match official leaders.", "https://www.nba.com/stats/leaders?Season=2025-26")
    mean_ok = True
    details=[]
    for p in players:
        g=[r for r in logs if r["player_id"]==p["player_id"]]
        for k in ("pts","reb","ast","tpm"):
            mean_ok &= round(statistics.mean(float(r[k]) for r in g),1)==float(p[k])
        mean_ok &= abs(statistics.mean(float(r["min"]) for r in g)-float(p["minutes"]))<=0.06
        details.append(f'{p["player"]}: {len(g)} games')
    add("Player season-mean reconciliation", mean_ok, "; ".join(details)+". Rounded PTS/REB/AST/3PM match official leaders; minutes match within rounding.", "https://www.nba.com/stats/leaders?Season=2025-26")
    sched=d["schedule.csv"]
    add("Schedule coverage", len(sched)==2 and len({r["game_id"] for r in sched})==2 and all(r["home_id"] in cmap and r["away_id"] in cmap for r in sched), "Exactly the two officially listed November 5 games; both participants exist in team tables.", NBA_SCHEDULE)
    inj=d["injuries.csv"]
    add("Injury report scope", len(inj)==11 and all(r["game_id"] in {s["game_id"] for s in sched} for r in inj) and sum(r["status"]=="NOT YET SUBMITTED" for r in inj)==2, "Nine named Out rows plus two unsubmitted team rows; no availability inference.", "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_12_00PM.pdf")
    market=d["market_snapshot.csv"]
    pairs=defaultdict(list)
    for r in market: pairs[(r["game_id"],r["market"])].append(r)
    market_ok=len(market)==12 and len(pairs)==6 and all(len(v)==2 for v in pairs.values())
    for v in pairs.values():
        if v[0]["market"]=="total": market_ok &= v[0]["line"]==v[1]["line"]
        elif v[0]["market"]=="spread": market_ok &= abs(float(v[0]["line"])+float(v[1]["line"]))<1e-9
    add("Market pair completeness", market_ok, "Six two-sided markets; spread/total thresholds match within each pair. Prices are archived, not executable.", FD_BOARD)
    add("No fabricated ledger", len(d["bets.csv"])==0, "The settled/prospective bet ledger is intentionally empty; performance and rewards remain blank.", DSR_URL)
    return checks


def project_lines(d: dict) -> tuple[list[dict], list[dict], list[dict]]:
    cur={r["team_id"]:r for r in d["team_advanced_2026_27.csv"]}
    prior={r["team_id"]:r for r in d["team_advanced_2025_26.csv"]}
    def weighted(rows: dict, key: str) -> float:
        return math.fsum(float(r[key])*int(r["possessions"]) for r in rows.values())/math.fsum(int(r["possessions"]) for r in rows.values())
    centers={k:(weighted(cur,k),weighted(prior,k)) for k in ("off_rating","def_rating","pace")}
    ratings={}
    rating_rows=[]
    for tid,c in cur.items():
        p=prior[tid]; gp=int(c["gp"]); w=gp/(gp+SHRINKAGE_GAMES)
        vals={}
        for k in centers:
            cc,pc=centers[k]
            vals[k]=w*(float(c[k])-cc)+(1-w)*(float(p[k])-pc)+cc
        ratings[tid]=vals
        rating_rows.append({"team_id":tid,"team":c["team"],"gp":gp,"current_weight":rounded(w),"off_rating":rounded(vals["off_rating"]),"def_rating":rounded(vals["def_rating"]),"pace":rounded(vals["pace"]),"method":f"Derived; K={SHRINKAGE_GAMES:g}; possession-weighted league centers; HFA={HOME_POINTS:g}","source_url":NBA_ADV,"flag_id":"R02;R03"})
    lines=[]; sensitivity=[]
    for g in d["schedule.csv"]:
        h,a=ratings[g["home_id"]],ratings[g["away_id"]]
        pace=(h["pace"]+a["pace"])/2
        # Each rating is points per 100 possessions for ONE team. Average the
        # team's offense and opponent's defense before applying expected pace.
        hp=((h["off_rating"]+a["def_rating"])/2)*pace/100
        ap=((a["off_rating"]+h["def_rating"])/2)*pace/100
        total=hp+ap; spread=ap-hp
        lines.append({"game_id":g["game_id"],"away":cur[g["away_id"]]["team"],"home":cur[g["home_id"]]["team"],"projected_away_points":rounded(ap,2),"projected_home_points":rounded(hp,2),"fair_home_spread":rounded(spread,2),"fair_total":rounded(total,2),"model_win_probability":"","expected_value":"","status":"Experimental line; not a validated bet","source_url":NBA_SCHEDULE,"flag_id":"R02;R03;R04"})
        for delta in SENSITIVITY_HOME_POINTS:
            sensitivity.append({"game_id":g["game_id"],"home_point_scenario":rounded(delta,1),"home_points":rounded(hp+delta/2,2),"away_points":rounded(ap-delta/2,2),"home_spread":rounded(spread-delta,2),"total":rounded(total,2),"label":"Analyst sensitivity, not an estimated home advantage","source_url":NBA_GLOSSARY,"flag_id":"R03"})
    return lines,rating_rows,sensitivity


def compare_markets(d: dict, lines: list[dict]) -> list[dict]:
    lmap={r["game_id"]:r for r in lines}; sched={r["game_id"]:r for r in d["schedule.csv"]}
    teams={r["team_id"]:r["team"] for r in d["team_advanced_2026_27.csv"]}
    abbr={"1610612753":"ORL","1610612756":"PHX","1610612748":"MIA","1610612744":"GSW"}
    groups=defaultdict(list)
    for r in d["market_snapshot.csv"]: groups[(r["game_id"],r["market"])].append(r)
    out=[]
    for (gid,market),rows in groups.items():
        probs=no_vig([int(r["american_price"]) for r in rows]); over=math.fsum(american_to_prob(int(r["american_price"])) for r in rows)-1
        line=lmap[gid]; game=sched[gid]
        for r,q in zip(rows,probs):
            model_line=""; edge=""; margin=""
            if market=="total":
                model_line=line["fair_total"]; mt=float(model_line); ml=float(r["line"])
                edge=mt-ml if r["selection"]=="Over" else ml-mt
            elif market=="spread":
                model_line=line["fair_home_spread"]
                home = r["selection"]==abbr[game["home_id"]]
                fair=float(model_line) if home else -float(model_line)
                margin=-float(line["fair_home_spread"]) if home else float(line["fair_home_spread"])
                model_line=rounded(fair,2); edge=margin+float(r["line"])
            out.append({"game_id":gid,"matchup":f'{teams[game["away_id"]]} at {teams[game["home_id"]]}',"market":market,"selection":r["selection"],"market_line":r["line"],"american_price":r["american_price"],"no_vig_market_probability":rounded(q,4),"market_overround":rounded(over,4),"model_line":model_line,"model_edge_points":rounded(edge,2) if edge!="" else "","model_probability":"","expected_value":"","status":"Archived comparison only","source_url":r["source_url"],"flag_id":"R03;R05"})
    return out


def correlation_analysis(d: dict) -> tuple[list[dict],list[dict],list[dict]]:
    logs=d["player_games.csv"]
    pairs=[("pts","tpm"),("pts","reb"),("pts","ast"),("reb","ast"),("pts","min"),("pts","plus_minus")]
    scopes=[("Pooled (descriptive)",logs),("Player-centered pooled",None)]
    for p in d["players.csv"]: scopes.append((p["player"],[r for r in logs if r["player_id"]==p["player_id"]]))
    corr=[]
    for label,subset in scopes:
        if subset is None:
            centered=[]
            for pid in {r["player_id"] for r in logs}:
                g=[r for r in logs if r["player_id"]==pid]
                means={k:statistics.mean(float(r[k]) for r in g) for k in {x for pair in pairs for x in pair}}
                centered += [{**r,**{k:str(float(r[k])-means[k]) for k in means}} for r in g]
            subset=centered
        for x,y in pairs:
            xs=[float(r[x]) for r in subset]; ys=[float(r[y]) for r in subset]
            r=pearson(xs,ys); lo,hi=block_bootstrap_ci(logs if label=="Player-centered pooled" else subset,x,y) if label!="Player-centered pooled" else (None,None)
            # Centered bootstrap must resample raw rows then recenter; omit CI rather than bootstrap centered values as raw stats.
            corr.append({"scope":label,"x":x,"y":y,"n":len(subset),"pearson_r":rounded(r),"ci_low":rounded(lo),"ci_high":rounded(hi),"interval_method":"Conditional player-stratified moving-block bootstrap; not population-generalizable" if lo is not None else "No interval: centered pooled statistic or insufficient blocks","source_url":d["players.csv"][0]["source_url"],"flag_id":"R06;R07"})
    combos=[("PTS>=25 + AST>=5",lambda r:float(r["pts"])>=25 and float(r["ast"])>=5,[("pts",25),("ast",5)]),
            ("PTS>=25 + REB>=5",lambda r:float(r["pts"])>=25 and float(r["reb"])>=5,[("pts",25),("reb",5)]),
            ("PTS>=25 + 3PM>=3",lambda r:float(r["pts"])>=25 and float(r["tpm"])>=3,[("pts",25),("tpm",3)]),
            ("PTS>=25 + AST>=5 + REB>=5",lambda r:float(r["pts"])>=25 and float(r["ast"])>=5 and float(r["reb"])>=5,[("pts",25),("ast",5),("reb",5)]),
            ("PTS>=25 + AST>=5 + REB>=5 + 3PM>=3",lambda r:float(r["pts"])>=25 and float(r["ast"])>=5 and float(r["reb"])>=5 and float(r["tpm"])>=3,[("pts",25),("ast",5),("reb",5),("tpm",3)])]
    prop=[]
    for p in d["players.csv"]:
        g=[r for r in logs if r["player_id"]==p["player_id"]]
        for name,pred,legs in combos:
            hits=sum(pred(r) for r in g); n=len(g); joint=hits/n
            marg=[sum(float(r[k])>=v for r in g)/n for k,v in legs]; indep=math.prod(marg)
            flags=[[float(r[k])>=v for r in g] for k,v in legs]
            # Phi for two legs; for >2 legs leave blank rather than misuse a pairwise coefficient.
            phi=pearson([float(v) for v in flags[0]],[float(v) for v in flags[1]]) if len(legs)==2 else None
            lo,hi=clopper_pearson(hits,n)
            prop.append({"player":p["player"],"combination":name,"n":n,"joint_hits":hits,"joint_probability":rounded(joint,4),"independence_product":rounded(indep,4),"joint_lift":rounded(joint/indep,4) if indep else "","pairwise_phi":rounded(phi),"exact_ci_low":rounded(lo,4),"exact_ci_high":rounded(hi,4),"ci_scope":"Exact binomial interval assumes independent games within this player; descriptive only","market_probability":"","edge":"","source_url":p["source_url"],"flag_id":"R06;R07"})
    lag=[]
    for p in d["players.csv"]:
        g=sorted([r for r in logs if r["player_id"]==p["player_id"]],key=lambda r:(r["game_date"],r["game_id"]))
        x=[float(r["pts"]) for r in g[:-1]]; y=[float(r["pts"]) for r in g[1:]]
        lag.append({"player":p["player"],"diagnostic":"Adjacent logged-game points lag-1","n_pairs":len(x),"pearson_r":rounded(pearson(x,y)),"interpretation":"Diagnostic only; not evidence of parlay-leg independence; missed games remain adjacent in the log","source_url":p["source_url"],"flag_id":"R07"})
    return corr,prop,lag


def persistence_signal(d: dict) -> list[dict]:
    cur={r["team_id"]:r for r in d["team_advanced_2026_27.csv"]}
    prior={r["team_id"]:r for r in d["team_advanced_2025_26.csv"]}
    ids=sorted(cur)
    x=[float(prior[i]["net_rating"]) for i in ids]; y=[float(cur[i]["net_rating"]) for i in ids]
    mae=statistics.mean(abs(a-b) for a,b in zip(x,y))
    baseline=statistics.mean(float(prior[i]["net_rating"]) for i in ids)
    base_mae=statistics.mean(abs(baseline-b) for b in y)
    return [{"signal":"Prior-season net rating persistence","n_teams":len(ids),"pearson_r":rounded(pearson(x,y)),"current_net_mae_points_per_100":rounded(mae,3),"prior_league_mean_baseline_mae":rounded(base_mae,3),"scope":"Descriptive 30-team ecological check, not a game-level or betting backtest","source_url":NBA_PRIOR,"flag_id":"R02;R15"}]


def power_table() -> list[dict]:
    rows=[]
    # Explicit hypothetical break-even at -110; not a current recommendation or observed result.
    p0=110/210
    for p1 in (0.55,0.57,0.60):
        for alpha,label in ((0.05,"Unadjusted one-sided 5%"),(0.05/8,"Bonferroni 5%/8 screening scenario")):
            n=minimum_n(p0,p1,alpha,0.80)
            rows.append({"scenario":label,"null_hit_probability":rounded(p0,6),"alternative_hit_probability":rounded(p1,2),"alpha":rounded(alpha,6),"target_power":"0.800","minimum_independent_bets":n,"exact_power_at_n":rounded(exact_power(n,p0,p1,alpha),4),"price_assumption":"Hypothetical -110 decimal payout; not an observed ledger","source_url":NIST_URL,"flag_id":"R08"})
    for k,n in ((30,50),(60,100),(600,1000)):
        lo,hi=clopper_pearson(k,n)
        rows.append({"scenario":f"Illustrative {k}/{n} wins","null_hit_probability":rounded(p0,6),"alternative_hit_probability":"","alpha":"","target_power":"","minimum_independent_bets":"","exact_power_at_n":"","exact_p_value":rounded(binom_sf(k,n,p0),5),"exact_ci_low":rounded(lo,4),"exact_ci_high":rounded(hi,4),"price_assumption":"Illustration only; not an observed strategy result","source_url":NIST_URL,"flag_id":"R08"})
    return rows


def evaluate_strategies(config: dict, checks: list[dict], bets: list[dict]) -> tuple[list[dict],list[dict],list[dict],dict]:
    prereg={"version":config["version"],"registered_date":config["registered_date"],"family_size":config["family_size"],"strategies":config["strategies"],"sha256":canonical_hash(config)}
    integrity=all(c["status"]=="PASS" for c in checks)
    has_bets=len(bets)>0
    gate_rows=[]; strategy_rows=[]
    # This release has no outcome ledger or walk-forward market history. Missing gates
    # are explicit blocks, never optimistic defaults. Ingestion of a future ledger must
    # supply separate audited evidence for every gate before this evaluator can pass it.
    evidence={"G01":integrity,"G02":True,"G03":False,"G04":False,"G05":False,"G06":False,"G07":False,"G08":False,"G09":False,"G10":integrity}
    reasons={"G01":"Official snapshot integrity checks","G02":f'Frozen {config["family_size"]}-candidate registry; hash {prereg["sha256"][:12]}',"G03":"No point-in-time historical game/market backtest","G04":"No settled bets or independent settlement clusters","G05":"No validated joint model for actual offered legs","G06":"No frozen out-of-sample market calibration ledger","G07":"No executable/settled prices, ROI or CLV","G08":"No full trial-return matrix, DSR or PBO evidence","G09":"No prospective replication or execution audit","G10":"Deterministic engine/build checks; certification still requires all other gates"}
    for gid,name,rule in GATES:
        gate_rows.append({"gate_id":gid,"name":name,"rule":rule,"status":"PASS" if evidence[gid] else "BLOCKED","evidence":reasons[gid],"policy_label":"Analyst governance choice informed by cited methods","source_url":DSR_URL if gid in ("G04","G07","G08","G09") else PBO_URL if gid in ("G03","G05") else NBA_GLOSSARY,"flag_id":"" if evidence[gid] else "R01;R08"})
    for s in config["strategies"]:
        passed=sum(evidence.values()); blocked=[g for g,v in evidence.items() if not v]
        strategy_rows.append({**s,"status":"BLOCKED","passed_gates":passed,"total_gates":len(GATES),"blocked_gates":";".join(blocked),"settled_bets":0,"roi":"","clv":"","deflated_sharpe":"","pbo":"","rank":"","reward":"","flag_id":"R01;R08"})
    eligible=[r for r in strategy_rows if r["status"]=="CERTIFIED"]
    # No certified entries: leaderboard intentionally has no data rows.
    leaderboard=[]
    return strategy_rows,gate_rows,leaderboard,prereg


def build() -> dict:
    names=["team_advanced_2026_27.csv","team_advanced_2025_26.csv","team_traditional_2026_27.csv","standings_2026_27.csv","schedule.csv","injuries.csv","players.csv","player_games.csv","market_snapshot.csv","bets.csv","sources.csv","flags.csv"]
    d={n:read_csv(n) for n in names}
    checks=verify_inputs(d)
    write_csv("checks.csv",["check","status","detail","source_url"],checks)
    failed=[c for c in checks if c["status"]!="PASS"]
    if failed:
        raise ValueError("Input integrity failure: "+"; ".join(c["check"] for c in failed))
    lines,ratings,sensitivity=project_lines(d)
    write_csv("lines.csv",["game_id","away","home","projected_away_points","projected_home_points","fair_home_spread","fair_total","model_win_probability","expected_value","status","source_url","flag_id"],lines)
    write_csv("ratings.csv",["team_id","team","gp","current_weight","off_rating","def_rating","pace","method","source_url","flag_id"],ratings)
    write_csv("sensitivity.csv",["game_id","home_point_scenario","home_points","away_points","home_spread","total","label","source_url","flag_id"],sensitivity)
    comparison=compare_markets(d,lines)
    write_csv("market_comparison.csv",["game_id","matchup","market","selection","market_line","american_price","no_vig_market_probability","market_overround","model_line","model_edge_points","model_probability","expected_value","status","source_url","flag_id"],comparison)
    corr,prop,lag=correlation_analysis(d)
    write_csv("correlations.csv",["scope","x","y","n","pearson_r","ci_low","ci_high","interval_method","source_url","flag_id"],corr)
    write_csv("prop_combinations.csv",["player","combination","n","joint_hits","joint_probability","independence_product","joint_lift","pairwise_phi","exact_ci_low","exact_ci_high","ci_scope","market_probability","edge","source_url","flag_id"],prop)
    write_csv("dependence_diagnostics.csv",["player","diagnostic","n_pairs","pearson_r","interpretation","source_url","flag_id"],lag)
    persistence=persistence_signal(d)
    write_csv("signals.csv",["signal","n_teams","pearson_r","current_net_mae_points_per_100","prior_league_mean_baseline_mae","scope","source_url","flag_id"],persistence)
    power=power_table()
    pfields=["scenario","null_hit_probability","alternative_hit_probability","alpha","target_power","minimum_independent_bets","exact_power_at_n","exact_p_value","exact_ci_low","exact_ci_high","price_assumption","source_url","flag_id"]
    write_csv("power.csv",pfields,power)
    with (ROOT/"strategies.json").open(encoding="utf-8") as f: config=json.load(f)
    strategies,gates,leaderboard,prereg=evaluate_strategies(config,checks,d["bets.csv"])
    sfields=["id","name","division","signal","rule","hypothesis","source_url","status","passed_gates","total_gates","blocked_gates","settled_bets","roi","clv","deflated_sharpe","pbo","rank","reward","flag_id"]
    write_csv("strategies.csv",sfields,strategies)
    write_csv("gates.csv",["gate_id","name","rule","status","evidence","policy_label","source_url","flag_id"],gates)
    write_csv("leaderboard.csv",["rank","strategy_id","division","deflated_sharpe","net_roi_lower_bound","clv","reward","source_url","flag_id"],leaderboard)
    with (DATA/"preregistration.json").open("w",encoding="utf-8") as f: json.dump(prereg,f,indent=2,ensure_ascii=False);f.write("\n")
    summary={"as_of":AS_OF,"model_version":MODEL_VERSION,"integrity_checks":len(checks),"integrity_passed":sum(c["status"]=="PASS" for c in checks),"teams":30,"player_games":len(d["player_games.csv"]),"games":len(d["schedule.csv"]),"market_prices":len(d["market_snapshot.csv"]),"strategies":len(strategies),"certified_strategies":sum(s["status"]=="CERTIFIED" for s in strategies),"leaderboard_entries":len(leaderboard),"settled_bets":len(d["bets.csv"]),"flags":len(d["flags.csv"]),"preregistration_sha256":prereg["sha256"],"bootstrap_reps":BOOTSTRAP_REPS,"bootstrap_block":BOOTSTRAP_BLOCK,"seed":SEED}
    with (DATA/"summary.json").open("w",encoding="utf-8") as f: json.dump(summary,f,indent=2);f.write("\n")
    return summary


if __name__=="__main__":
    print(json.dumps(build(),indent=2))

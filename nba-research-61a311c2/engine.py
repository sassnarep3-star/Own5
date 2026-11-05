#!/usr/bin/env python3
"""Deterministic, evidence-first NBA research engine.

Standard library only. Reads canonical CSV snapshots whose rows carry official
source links; writes data/derived.json and derived CSV tables. Missing market,
availability, settlement or dependence evidence stays None/blank and blocks
qualification. Model outputs are labeled research estimates, not bets.
"""
from __future__ import annotations

import csv
import json
import math
import random
import statistics
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
AS_OF = "2026-11-05"
SEASON = "2026-27"
K_SHRINK = 10.0  # declared model choice, not an estimated NBA constant
HFA = 0.0        # no independently fitted home advantage is asserted
BOOT_REPS = 2000
BOOT_BLOCK = 5
BOOT_SEED = 610311
FAMILY_M = 6     # registered strategy family for conservative Bonferroni gate
EMPIRICAL_HOSTS = {"www.nba.com", "official.nba.com", "ak-static.cms.nba.com"}
ALLOWED_HOSTS = EMPIRICAL_HOSTS | {
    "sportsbook.fanduel.com", "sportsbook.draftkings.com",
    "docs.scipy.org", "www.itl.nist.gov", "www.davidhbailey.com", "github.com",
}


def read_csv(name: str) -> list[dict]:
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name: str, rows: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or (list(rows[0]) if rows else [])
    with (DATA / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def num(value, cast=float):
    if value is None or value == "":
        return None
    return cast(value)


def official_url(url: str, empirical: bool = False) -> bool:
    p = urlsplit(url)
    return p.scheme == "https" and p.hostname in (EMPIRICAL_HOSTS if empirical else ALLOWED_HOSTS)


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return None
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
    return max(-1.0, min(1.0, r))


def percentile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("empty percentile")
    vs = sorted(values)
    pos = (len(vs) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return vs[lo]
    return vs[lo] + (vs[hi] - vs[lo]) * (pos - lo)


def moving_block_ci(xs: list[float], ys: list[float], seed: int,
                    reps: int = BOOT_REPS, block: int = BOOT_BLOCK) -> tuple[float | None, float | None]:
    """Percentile CI from moving blocks resampled with replacement.

    Blocks preserve short local dependence; this is still exploratory and does
    not prove stationarity or repair selection bias.
    """
    n = len(xs)
    if n != len(ys) or n < max(8, block + 2):
        return None, None
    rng = random.Random(seed)
    out: list[float] = []
    starts = n - block + 1
    need = math.ceil(n / block)
    for _ in range(reps):
        bx: list[float] = []
        by: list[float] = []
        for _ in range(need):
            s = rng.randrange(starts)
            bx.extend(xs[s:s + block])
            by.extend(ys[s:s + block])
        r = pearson(bx[:n], by[:n])
        if r is not None:
            out.append(r)
    if len(out) < reps // 2:
        return None, None
    return percentile(out, 0.025), percentile(out, 0.975)


def rate_block_ci(flags: list[int], seed: int, reps: int = BOOT_REPS,
                  block: int = BOOT_BLOCK) -> tuple[float | None, float | None]:
    n = len(flags)
    if n < max(8, block + 2):
        return None, None
    rng = random.Random(seed)
    out: list[float] = []
    need = math.ceil(n / block)
    for _ in range(reps):
        sample: list[int] = []
        for _ in range(need):
            s = rng.randrange(n - block + 1)
            sample.extend(flags[s:s + block])
        out.append(sum(sample[:n]) / n)
    return percentile(out, 0.025), percentile(out, 0.975)


def binom_pmf(k: int, n: int, p: float) -> float:
    if k < 0 or k > n:
        return 0.0
    return math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
                    + k * math.log(p) + (n - k) * math.log1p(-p))


def binom_sf(k: int, n: int, p: float) -> float:
    """Exact P[X >= k] for X~Binomial(n,p), summed in log space."""
    if n < 0 or not 0 < p < 1:
        raise ValueError("invalid binomial parameters")
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    term = binom_pmf(k, n, p)
    total = term
    for j in range(k, n):
        term *= (n - j) / (j + 1) * p / (1 - p)
        total += term
        if term < 1e-18 and j > n * p:
            break
    return min(1.0, total)


def wilson(wins: int, n: int, z: float = 1.959963984540054) -> tuple[float, float] | None:
    if n <= 0:
        return None
    p = wins / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def holm(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def decimal_from_american(a: int) -> float:
    if not isinstance(a, int) or isinstance(a, bool) or abs(a) < 100:
        raise ValueError("American odds must be an integer with |odds| >= 100")
    return 1 + (100 / abs(a) if a < 0 else a / 100)


def fair_decimal(p_win: float, p_push: float = 0.0) -> float:
    if not 0 <= p_win <= 1 or not 0 <= p_push <= 1 or p_win + p_push > 1 or p_win <= 0:
        raise ValueError("invalid probability distribution")
    return 1 + (1 - p_win - p_push) / p_win


def expected_return(p_win: float, decimal: float, p_push: float = 0.0) -> float:
    if decimal <= 1:
        raise ValueError("decimal odds must exceed 1")
    return p_win * decimal + p_push - 1


def joint_bounds(pa: float, pb: float) -> tuple[float, float]:
    if not 0 <= pa <= 1 or not 0 <= pb <= 1:
        raise ValueError("probabilities must be in [0,1]")
    return max(0.0, pa + pb - 1), min(pa, pb)


def phi_from_counts(n: int, n11: int, n10: int, n01: int, n00: int) -> float | None:
    if n11 + n10 + n01 + n00 != n or n == 0:
        raise ValueError("counts must sum to n")
    a, b = n11 + n10, n11 + n01
    c, d = n01 + n00, n10 + n00
    den = math.sqrt(a * b * c * d)
    return (n11 * n00 - n10 * n01) / den if den else None


def half_step_threshold(median_value: float) -> float:
    """Nearest half-integer strictly above an integer median; keep .5 medians."""
    return math.floor(median_value) + 0.5 if float(median_value).is_integer() else median_value


def gate_decision(gates: dict[str, bool | None]) -> dict:
    required = [f"G{i:02}" for i in range(1, 13)]
    passed = [g for g in required if gates.get(g) is True]
    blocked = [g for g in required if gates.get(g) is not True]
    return {"eligible": not blocked, "passed": passed, "blocked": blocked,
            "action": "PAPER_RESEARCH_ONLY" if blocked else "ELIGIBLE_FOR_REVIEW"}


def load_inputs() -> dict:
    sources = read_csv("sources.csv")
    for s in sources:
        if not official_url(s["url"]):
            raise ValueError(f"untrusted source URL: {s['url']}")
    prior = read_csv("teams_prior_2025_26.csv")
    current = read_csv("teams_current_2026_27.csv")
    hist = read_csv("player_games_2025_26.csv")
    cur_players = read_csv("player_games_2026_27.csv")
    slate = read_csv("slate.csv")
    quotes = read_csv("market_quotes_nov5.csv")
    availability = read_csv("availability.csv")
    for rows, empirical in ((prior, True), (current, True), (hist, True),
                            (cur_players, True), (slate, True), (availability, True)):
        for r in rows:
            if not official_url(r["source_url"], empirical=True):
                raise ValueError(f"empirical row lacks official NBA source: {r}")
    for q in quotes:
        if not official_url(q["source_url"]):
            raise ValueError(f"quote lacks operator-official source: {q}")
    if len({r["team_id"] for r in prior}) != 30 or len({r["team_id"] for r in current}) != 30:
        raise ValueError("expected 30 unique teams in each season snapshot")
    for r in current:
        gp, w, l = int(r["gp"]), int(r["w"]), int(r["l"])
        if gp != w + l:
            raise ValueError(f"current W/L does not reconcile: {r['team']}")
        if abs((float(r["off_rtg"]) - float(r["def_rtg"])) - float(r["net_rtg"])) > 0.11:
            raise ValueError(f"off-def/net rounding mismatch: {r['team']}")
        pace_from_poss = float(r["poss"]) / (float(r["min"]) / 48)
        # Official PACE and POSS are both transcribed as published. They are not
        # forced into an exact identity; small definitional/rounding drift is flagged.
        if abs(pace_from_poss - float(r["pace"])) > 0.60:
            raise ValueError(f"pace/possessions sanity mismatch: {r['team']}")
    for r in prior:
        if int(r["gp"]) != int(r["w"]) + int(r["l"]) or int(r["gp"]) != 82:
            raise ValueError(f"prior season row does not reconcile: {r['team']}")
    return dict(sources=sources, prior=prior, current=current, hist=hist,
                cur_players=cur_players, slate=slate, quotes=quotes, availability=availability)


def team_model(inp: dict) -> tuple[list[dict], dict]:
    cur = {r["team_id"]: r for r in inp["current"]}
    poss_total = sum(float(r["poss"]) for r in cur.values())
    league_off = sum(float(r["off_rtg"]) * float(r["poss"]) for r in cur.values()) / poss_total
    league_def = sum(float(r["def_rtg"]) * float(r["poss"]) for r in cur.values()) / poss_total
    minute_total = sum(float(r["min"]) for r in cur.values())
    league_pace = sum(float(r["pace"]) * float(r["min"]) for r in cur.values()) / minute_total

    def shrunk(team_id: str, k: float = K_SHRINK) -> dict:
        r = cur[team_id]
        gp = float(r["gp"])
        w = gp / (gp + k)
        return {
            "off": w * float(r["off_rtg"]) + (1 - w) * league_off,
            "def": w * float(r["def_rtg"]) + (1 - w) * league_def,
            "pace": w * float(r["pace"]) + (1 - w) * league_pace,
            "weight": w,
        }

    lines = []
    quotes = {(q["game_id"], q["market"], q["selection"]): q for q in inp["quotes"]}
    for g in inp["slate"]:
        h, a = shrunk(g["home_id"]), shrunk(g["away_id"])
        pace = (h["pace"] + a["pace"]) / 2
        home_pts = pace * (h["off"] + a["def"] - league_off) / 100 + HFA / 2
        away_pts = pace * (a["off"] + h["def"] - league_off) / 100 - HFA / 2
        margin = home_pts - away_pts
        total = home_pts + away_pts
        sens_totals = []
        for k in (5.0, 10.0, 20.0):
            hh, aa = shrunk(g["home_id"], k), shrunk(g["away_id"], k)
            pp = (hh["pace"] + aa["pace"]) / 2
            sens_totals.append(pp * (hh["off"] + aa["def"] + aa["off"] + hh["def"] - 2 * league_off) / 100)
        mq_spread = quotes.get((g["game_id"], "spread", g["home"]))
        mq_total = quotes.get((g["game_id"], "total", "OVER"))
        market_home_spread = num(mq_spread["line"]) if mq_spread else None
        market_total = num(mq_total["line"]) if mq_total else None
        lines.append({
            "game_id": g["game_id"], "date": g["date"], "tip_et": g["tip_et"],
            "away": g["away"], "home": g["home"], "arena": g["arena"],
            "model_home_spread": round(-margin, 2),
            "model_total": round(total, 2),
            "model_home_pts": round(home_pts, 2), "model_away_pts": round(away_pts, 2),
            "expected_pace": round(pace, 2),
            "home_margin_hfa_minus2": round(-(margin - 2), 2),
            "home_margin_hfa_plus2": round(-(margin + 2), 2),
            "total_k5": round(min(sens_totals), 2), "total_k20": round(max(sens_totals), 2),
            "market_home_spread": market_home_spread,
            "market_total": market_total,
            "spread_diff_model_minus_market": round(-margin - market_home_spread, 2) if market_home_spread is not None else None,
            "total_diff_model_minus_market": round(total - market_total, 2) if market_total is not None else None,
            "model_win_prob": None, "fair_moneyline": None, "edge": None,
            "status": "model_only_unqualified",
            "source_url": g["source_url"],
            "market_source_url": mq_spread["source_url"] if mq_spread else "",
        })
    meta = {"k_shrink": K_SHRINK, "hfa": HFA, "league_off_rtg": round(league_off, 3),
            "league_def_rtg": round(league_def, 3), "league_pace": round(league_pace, 3),
            "formula": "pace_match * (off_team + def_opponent - league_off) / 100; home spread = -(home_pts-away_pts)",
            "caveat": "Declared shrinkage choice; no availability adjustment; no calibrated win probability; not a betting recommendation."}
    return lines, meta


def correlation_tables(inp: dict) -> tuple[list[dict], list[dict], list[dict]]:
    players: dict[str, list[dict]] = {}
    for r in inp["hist"]:
        players.setdefault(r["player_id"], []).append(r)
    pairs = [("pts", "reb"), ("pts", "ast"), ("pts", "tpm"), ("reb", "ast"), ("ast", "tpm"), ("pts", "min")]
    corr = []
    lag = []
    combos = []
    combo_defs = [
        ("PTS>=25 & AST>=5", lambda r: float(r["pts"]) >= 25, lambda r: float(r["ast"]) >= 5),
        ("PTS>=25 & REB>=5", lambda r: float(r["pts"]) >= 25, lambda r: float(r["reb"]) >= 5),
        ("PTS>=25 & 3PM>=3", lambda r: float(r["pts"]) >= 25, lambda r: float(r["tpm"]) >= 3),
        ("AST>=5 & REB>=5", lambda r: float(r["ast"]) >= 5, lambda r: float(r["reb"]) >= 5),
    ]
    for pid, rows in sorted(players.items()):
        rows = sorted(rows, key=lambda r: r["game_date"])
        name = rows[0]["player"]
        src = rows[0]["source_url"]
        for x, y in pairs:
            xs = [float(r[x]) for r in rows]
            ys = [float(r[y]) for r in rows]
            r = pearson(xs, ys)
            lo, hi = moving_block_ci(xs, ys, BOOT_SEED + int(pid) + sum(map(ord, x + y)))
            corr.append({"player_id": pid, "player": name, "pair": f"{x.upper()} x {y.upper()}",
                         "n": len(rows), "r": round(r, 4) if r is not None else None,
                         "ci_low": round(lo, 4) if lo is not None else None,
                         "ci_high": round(hi, 4) if hi is not None else None,
                         "method": "Pearson; moving-block percentile 95% CI (block=5, reps=2000)",
                         "status": "exploratory_within_player", "source_url": src})
        pts = [float(r["pts"]) for r in rows]
        r1 = pearson(pts[:-1], pts[1:])
        lo, hi = moving_block_ci(pts[:-1], pts[1:], BOOT_SEED + int(pid) + 999)
        lag.append({"player_id": pid, "player": name, "metric": "PTS lag-1", "n_pairs": len(pts) - 1,
                    "r": round(r1, 4) if r1 is not None else None,
                    "ci_low": round(lo, 4) if lo is not None else None,
                    "ci_high": round(hi, 4) if hi is not None else None,
                    "status": "within_player_serial_dependence_only", "source_url": src})
        for cname, fa, fb in combo_defs:
            a = [int(fa(r)) for r in rows]
            b = [int(fb(r)) for r in rows]
            joint = [int(x and y) for x, y in zip(a, b)]
            n11 = sum(joint)
            n10 = sum(x and not y for x, y in zip(a, b))
            n01 = sum(y and not x for x, y in zip(a, b))
            n00 = len(rows) - n11 - n10 - n01
            pa, pb, pj = sum(a) / len(a), sum(b) / len(b), n11 / len(rows)
            lo, hi = rate_block_ci(joint, BOOT_SEED + int(pid) + sum(map(ord, cname)))
            combos.append({"player_id": pid, "player": name, "combo": cname, "n": len(rows),
                           "hit_a": round(pa, 4), "hit_b": round(pb, 4), "joint_hit": round(pj, 4),
                           "joint_ci_low": round(lo, 4) if lo is not None else None,
                           "joint_ci_high": round(hi, 4) if hi is not None else None,
                           "independence_product": round(pa * pb, 4),
                           "lift": round(pj / (pa * pb), 4) if pa * pb else None,
                           "phi": round(phi_from_counts(len(rows), n11, n10, n01, n00), 4) if phi_from_counts(len(rows), n11, n10, n01, n00) is not None else None,
                           "status": "historical_threshold_frequency_not_market_prop", "source_url": src})
        a3 = [int(float(r["pts"]) >= 25 and float(r["ast"]) >= 5 and float(r["reb"]) >= 5) for r in rows]
        pa = sum(float(r["pts"]) >= 25 for r in rows) / len(rows)
        pb = sum(float(r["ast"]) >= 5 for r in rows) / len(rows)
        pc = sum(float(r["reb"]) >= 5 for r in rows) / len(rows)
        pj = sum(a3) / len(rows)
        lo, hi = rate_block_ci(a3, BOOT_SEED + int(pid) + 313)
        combos.append({"player_id": pid, "player": name, "combo": "PTS>=25 & AST>=5 & REB>=5", "n": len(rows),
                       "hit_a": round(pa, 4), "hit_b": round(pb, 4), "joint_hit": round(pj, 4),
                       "joint_ci_low": round(lo, 4) if lo is not None else None,
                       "joint_ci_high": round(hi, 4) if hi is not None else None,
                       "independence_product": round(pa * pb * pc, 4),
                       "lift": round(pj / (pa * pb * pc), 4) if pa * pb * pc else None,
                       "phi": None, "status": "historical_threshold_frequency_not_market_prop", "source_url": src})
    return corr, lag, combos


def walk_forward_points(inp: dict) -> tuple[list[dict], dict]:
    """Exploratory expanding-median reversion forecast; no odds, no bets."""
    players: dict[str, list[dict]] = {}
    for r in inp["hist"]:
        players.setdefault(r["player_id"], []).append(r)
    preds = []
    for pid, rows in sorted(players.items()):
        rows = sorted(rows, key=lambda r: r["game_date"])
        pts = [float(r["pts"]) for r in rows]
        for i in range(20, len(rows)):
            prior = pts[:i]
            med = statistics.median(prior)
            line = half_step_threshold(med)
            last5 = statistics.fmean(pts[i - 5:i])
            diff = last5 - med
            pick = "OVER" if diff >= 2 else "UNDER" if diff <= -2 else "PASS"
            if pick == "PASS":
                continue
            hit = int(pts[i] > line) if pick == "OVER" else int(pts[i] < line)
            preds.append({"player_id": pid, "player": rows[i]["player"], "game_id": rows[i]["game_id"],
                          "date": rows[i]["game_date"], "prior_n": i, "reference_line": line,
                          "last5_mean": round(last5, 3), "pick": pick, "actual_pts": int(pts[i]),
                          "hit": hit, "source_url": rows[i]["source_url"]})
    n = len(preds)
    wins = sum(p["hit"] for p in preds)
    pval = binom_sf(wins, n, 0.5) if n else None
    ci = wilson(wins, n) if n else None
    summary = {"strategy_id": "S03", "n_forecasts": n, "wins": wins, "losses": n - wins,
               "hit_rate": round(wins / n, 4) if n else None,
               "wilson_low": round(ci[0], 4) if ci else None, "wilson_high": round(ci[1], 4) if ci else None,
               "exact_p_vs_50pct": round(pval, 6) if pval is not None else None,
               "bonferroni_p_family6": round(min(1.0, pval * FAMILY_M), 6) if pval is not None else None,
               "roi": None, "graded_bets": 0,
               "status": "exploratory_forecast_not_betting_skill",
               "rule": "min prior n=20; half-step expanding median; last5 mean >= median+2 -> OVER, <= median-2 -> UNDER, else PASS"}
    return preds, summary


def current_player_refs(inp: dict) -> list[dict]:
    players: dict[str, list[dict]] = {}
    for r in inp["cur_players"]:
        players.setdefault(r["player_id"], []).append(r)
    avail = {r["player_id"]: r for r in inp["availability"]}
    out = []
    for pid, rows in sorted(players.items()):
        rows = sorted(rows, key=lambda r: r["game_date"])
        ref = {"player_id": pid, "player": rows[0]["player"], "team": rows[0]["team"], "n_current": len(rows)}
        for key in ("pts", "reb", "ast", "tpm"):
            med = statistics.median(float(r[key]) for r in rows)
            ref[f"median_{key}"] = med
            ref[f"reference_{key}"] = half_step_threshold(med)
        av = avail.get(pid, {})
        ref["availability_status"] = av.get("status") or None
        ref["market_prop_line"] = None
        ref["market_prop_price"] = None
        ref["status"] = "research_reference_only_availability_unverified"
        ref["source_url"] = rows[0]["source_url"]
        ref["availability_source_url"] = av.get("source_url", "")
        out.append(ref)
    return out


def build() -> dict:
    inp = load_inputs()
    lines, model_meta = team_model(inp)
    corr, lag, combos = correlation_tables(inp)
    preds, wf = walk_forward_points(inp)
    player_refs = current_player_refs(inp)
    write_csv("derived_lines.csv", lines)
    write_csv("derived_correlations.csv", corr)
    write_csv("derived_lag.csv", lag)
    write_csv("derived_combos.csv", combos)
    write_csv("derived_walk_forward.csv", preds)
    write_csv("derived_player_refs.csv", player_refs)

    gates = [
        {"id": "G01", "name": "Official source integrity", "rule": "Every empirical row has an official NBA source URL; derived rows inherit it.", "status": "pass", "passed": True, "source_url": "https://www.nba.com/stats/help/glossary"},
        {"id": "G02", "name": "Schedule identity", "rule": "Game IDs, teams, dates and venues come from the official schedule.", "status": "pass", "passed": True, "source_url": "https://www.nba.com/schedule?date=2026-11-06"},
        {"id": "G03", "name": "Availability", "rule": "Player participation must be confirmed before prop qualification.", "status": "blocked", "passed": False, "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf"},
        {"id": "G04", "name": "Timestamped market quotes", "rule": "Bet-time and closing quotes required for value/CLV; only two Nov 5 games have dynamic operator snapshots.", "status": "blocked", "passed": False, "source_url": "https://sportsbook.fanduel.com/navigation/nba"},
        {"id": "G05", "name": "Settlement rules", "rule": "Operator-specific NBA/prop/parlay settlement must be recorded.", "status": "pass_operator_specific", "passed": True, "source_url": "https://sportsbook.fanduel.com/navigation/nba"},
        {"id": "G06", "name": "Chronological replay", "rule": "No future outcome may enter a forecast; expanding-window replay implemented.", "status": "pass_exploratory", "passed": True, "source_url": "https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26"},
        {"id": "G07", "name": "Sample size / power", "rule": "Exact binomial evidence must clear family-wise alpha; current forecast sample is small.", "status": "blocked", "passed": False, "source_url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"},
        {"id": "G08", "name": "Multiple testing", "rule": "Register all trials; Holm/Bonferroni utilities implemented; DSR requires full trial ledger.", "status": "pass_policy_only", "passed": True, "source_url": "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf"},
        {"id": "G09", "name": "Dependence audit", "rule": "Same-game dependence measured within selected players; cross-game parlay dependence remains unmeasured.", "status": "blocked", "passed": False, "source_url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"},
        {"id": "G10", "name": "Calibrated probabilities", "rule": "Moneyline/prop probabilities require a validated outcome distribution; none is asserted.", "status": "blocked", "passed": False, "source_url": "https://www.nba.com/stats/help/glossary"},
        {"id": "G11", "name": "Economic realism", "rule": "Executable price, limits, fees, voids and closing benchmark required; no ROI is reported.", "status": "blocked", "passed": False, "source_url": "https://sportsbook.draftkings.com/help/general-betting-rules/market-rules"},
        {"id": "G12", "name": "Reward funding", "rule": "Sponsor, budget, eligibility and payout terms must be verified before monetary rewards.", "status": "blocked", "passed": False, "source_url": "https://github.com/sassnarep3-star/Own5"},
    ]
    gate_map = {g["id"]: g["passed"] for g in gates}
    decision = gate_decision(gate_map)

    strategies = [
        {"id": "S01", "class": "single", "name": "Team spread value vs market", "hypothesis": "Originate a pace/efficiency spread and compare with a timestamped market spread; trade only after calibration and availability gates.", "evidence": "11 model-only slate lines; 2 Nov 5 operator quote snapshots", "status": "blocked_no_closing_quotes", "graded_bets": 0, "roi": None, "reward": None, "rank": None, "source_url": "https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season"},
        {"id": "S02", "class": "single", "name": "Team total value vs market", "hypothesis": "Originate a pace-interaction total and compare with market total; no edge without calibrated total distribution.", "evidence": "11 model totals; K=5/10/20 sensitivity", "status": "blocked_no_distribution", "graded_bets": 0, "roi": None, "reward": None, "rank": None, "source_url": "https://www.nba.com/stats/help/glossary"},
        {"id": "S03", "class": "player_prop", "name": "Expanding-median points reversion", "hypothesis": "After 20 prior games, fade a last-5 mean at least 2 points from the expanding median using a half-step reference line.", "evidence": f"{wf['n_forecasts']} chronological forecast rows; exact binomial vs 50%", "status": wf["status"], "graded_bets": 0, "roi": None, "reward": None, "rank": None, "source_url": "https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26&SeasonType=Regular%20Season"},
        {"id": "S04", "class": "prop_combo", "name": "Same-game PTS+AST threshold combo", "hypothesis": "Price joint threshold frequency directly rather than multiplying marginal rates; validate on matched prop lines.", "evidence": "Per-player historical joint rates and block CIs", "status": "blocked_no_market_props", "graded_bets": 0, "roi": None, "reward": None, "rank": None, "source_url": "https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26"},
        {"id": "S05", "class": "prop_combo", "name": "Same-game PTS+AST+REB threshold combo", "hypothesis": "Three-leg joint frequency must be estimated directly; pairwise correlation is insufficient.", "evidence": "Per-player three-leg historical frequency", "status": "blocked_no_market_props", "graded_bets": 0, "roi": None, "reward": None, "rank": None, "source_url": "https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26&SeasonType=Regular%20Season"},
        {"id": "S06", "class": "parlay", "name": "Cross-game two-leg team parlay", "hypothesis": "Combine qualified single legs only after measuring cross-game dependence and operator parlay repricing.", "evidence": "No cross-game leg correlation measured; within-player lag-1 is not a substitute", "status": "blocked_dependence_and_quotes", "graded_bets": 0, "roi": None, "reward": None, "rank": None, "source_url": "https://sportsbook.draftkings.com/help/general-betting-rules/market-rules"},
    ]
    leaderboard = [{"rank": None, "entry_id": s["id"], "name": s["name"], "class": s["class"],
                    "graded_bets": 0, "wins": None, "losses": None, "pushes": None,
                    "net_units": None, "score": None, "reward_points": 0, "monetary_reward": None,
                    "eligible": False, "source_url": s["source_url"]} for s in strategies]

    flags = [
        {"id": "F01", "severity": "high", "issue": "No closing-line archive", "detail": "Only a dynamic Nov 5 FanDuel snapshot was retrieved. CLV, executable edge and ROI remain blank.", "source_url": "https://sportsbook.fanduel.com/navigation/nba"},
        {"id": "F02", "severity": "high", "issue": "Nov 6 availability unconfirmed", "detail": "The 4pm ET Nov 5 injury report marks most Nov 6 teams NOT YET SUBMITTED. Selected player statuses are blank, not assumed available.", "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf"},
        {"id": "F03", "severity": "high", "issue": "Cross-game parlay dependence unmeasured", "detail": "Within-player lag-1 autocorrelation cannot establish independence between different games. Cross-game correlation cells stay blank.", "source_url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"},
        {"id": "F04", "severity": "high", "issue": "No calibrated probabilities", "detail": "Team lines are point estimates only. Moneyline probabilities, fair odds and expected value are blank.", "source_url": "https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season"},
        {"id": "F05", "severity": "medium", "issue": "Early-season team samples", "detail": "Current team snapshots contain 6-9 games. Shrinkage K=10 is a declared model choice, not a fitted constant.", "source_url": "https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season"},
        {"id": "F06", "severity": "medium", "issue": "Selected-player sample", "detail": "Historical correlations use only Edwards and Doncic (125 player-games). They are not a league-wide prop population.", "source_url": "https://www.nba.com/stats/leaders?Season=2025-26"},
        {"id": "F07", "severity": "medium", "issue": "Bootstrap assumptions", "detail": "Moving-block CIs preserve short local dependence but do not prove stationarity or remove selection bias.", "source_url": "https://www.itl.nist.gov/div898/handbook/eda/section3/eda334.htm"},
        {"id": "F08", "severity": "medium", "issue": "Operator jurisdiction", "detail": "DraftKings general rules retrieved explicitly govern Virginia; FanDuel page is operator-specific. No global betting eligibility is asserted.", "source_url": "https://sportsbook.draftkings.com/help/general-betting-rules/general-rules"},
        {"id": "F09", "severity": "medium", "issue": "Tip-time display mismatch", "detail": "NBA schedule lists ORL@PHX 9:00 PM ET and MIA@GSW 10:00 PM ET; FanDuel displayed 9:10/10:10 PM ET. NBA schedule retained for identity; mismatch flagged.", "source_url": "https://www.nba.com/schedule?date=2026-11-06"},
        {"id": "F10", "severity": "medium", "issue": "Legacy spread sign convention", "detail": "nba-signal-lab labels positive expected home margin as model_home_spread. Canonical desk uses betting convention: favorite home spread is negative.", "source_url": "https://github.com/sassnarep3-star/Own5/blob/54e8dee596d49731c3da535a1f77b01cd0c295d5/nba-signal-lab/compute.py"},
        {"id": "F11", "severity": "medium", "issue": "Legacy independence claim", "detail": "nba-signal-lab S-04 says cross-game independence is supported by lag-1 checks; within-player lag-1 does not test cross-game leg dependence. Not reused.", "source_url": "https://github.com/sassnarep3-star/Own5/blob/54e8dee596d49731c3da535a1f77b01cd0c295d5/nba-signal-lab/compute.py"},
        {"id": "F12", "severity": "medium", "issue": "Legacy DSR label", "detail": "nba-signal-lab calls a 25-bet prior shrinkage DSR-style; true Deflated Sharpe requires trial count, trial variance and return moments. Canonical desk leaves DSR blank.", "source_url": "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf"},
        {"id": "F13", "severity": "low", "issue": "Legacy header irregularity", "detail": "nba-signal-lab prior team CSV contains a duplicate-looking block column with a non-ASCII character (blkа_pg). Canonical snapshots avoid that schema.", "source_url": "https://github.com/sassnarep3-star/Own5/blob/54e8dee596d49731c3da535a1f77b01cd0c295d5/nba-signal-lab/data/teams_2025_26.csv"},
        {"id": "F14", "severity": "medium", "issue": "Legacy executive claims not re-certified", "detail": "Root EXECUTIVE_SUMMARY.md cites third-party/preprint effect sizes and industry CLV conventions. This session did not independently re-verify those claims; they remain archive-only.", "source_url": "https://github.com/sassnarep3-star/Own5/blob/54e8dee596d49731c3da535a1f77b01cd0c295d5/EXECUTIVE_SUMMARY.md"},
        {"id": "F15", "severity": "medium", "issue": "Historical 22-game desk sample partial", "detail": "Only UTA@POR 0022600147 was partially re-verified this session; the remaining legacy walk-forward rows are not certified and are excluded from canonical qualification.", "source_url": "https://www.nba.com/game/0022600147/box-score"},
        {"id": "F16", "severity": "high", "issue": "Rewards unfunded", "detail": "No sponsor, prize budget, eligibility terms or payout mechanism is verified. Monetary rewards are blank; research reward points remain zero until qualification.", "source_url": "https://github.com/sassnarep3-star/Own5"},
        {"id": "F17", "severity": "medium", "issue": "Dynamic source drift", "detail": "NBA stats and operator odds pages can change after retrieval. Snapshots are dated, not immutable feeds; quote timestamps are blank where not exposed.", "source_url": "https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season"},
        {"id": "F18", "severity": "medium", "issue": "Repository scope mix", "detail": "Root dashboard and several research files are NFL-focused; multiple NBA desks use different snapshots/parameters. Canonical NBA desk is isolated; legacy archives preserved read-only.", "source_url": "https://github.com/sassnarep3-star/Own5/tree/54e8dee596d49731c3da535a1f77b01cd0c295d5"},
        {"id": "F19", "severity": "low", "issue": "Official PACE/POSS not an exact identity", "detail": "The published advanced table does not always satisfy PACE = POSS/(MIN/48) exactly (e.g., ORL 98.29 vs 685/(336/48)=97.86). Canonical model uses official PACE as published and does not silently recompute it.", "source_url": "https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season"},
    ]

    requirements = [
        {"id": "R01", "requirement": "Independent NBA line origination", "status": "delivered_model_only", "evidence": "11 slate lines from verified team inputs", "source_url": "https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season"},
        {"id": "R02", "requirement": "Useful signals across singles/parlays/props", "status": "delivered_research_queue", "evidence": "6 registered strategies; none qualified", "source_url": "https://www.nba.com/stats/help/glossary"},
        {"id": "R03", "requirement": "Correlations measured, not assumed", "status": "partial", "evidence": "Within-player correlations and combo frequencies; cross-game blank", "source_url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"},
        {"id": "R04", "requirement": "Skill vs luck separation", "status": "partial", "evidence": "Exact binomial replay, Wilson CI, family-wise correction; no betting skill claim", "source_url": "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf"},
        {"id": "R05", "requirement": "Mandatory validation gates", "status": "delivered_fail_closed", "evidence": "G01-G12; eligibility false", "source_url": "https://www.itl.nist.gov/div898/handbook/eda/section3/eda334.htm"},
        {"id": "R06", "requirement": "Reward-based leaderboard", "status": "delivered_unfunded", "evidence": "6 registry rows; rank/score blank; monetary reward blank", "source_url": "https://github.com/sassnarep3-star/Own5"},
        {"id": "R07", "requirement": "Executive summary", "status": "delivered", "evidence": "research/nba-research-61a311c2/EXECUTIVE_SUMMARY.md", "source_url": "https://github.com/sassnarep3-star/Own5"},
        {"id": "R08", "requirement": "Line-by-line official review with links", "status": "partial_explicit", "evidence": "241 canonical rows audited; 434 baseline files inventoried; legacy claims flagged", "source_url": "https://github.com/sassnarep3-star/Own5/tree/54e8dee596d49731c3da535a1f77b01cd0c295d5"},
        {"id": "R09", "requirement": "Every table row has official-source link", "status": "delivered", "evidence": "Static tables include source column; tests enforce HTTPS source per row", "source_url": "https://www.nba.com/stats/help/glossary"},
        {"id": "R10", "requirement": "Unconfirmed values blank and flagged", "status": "delivered", "evidence": "Availability, probabilities, ROI, rank, rewards and cross-game dependence blank", "source_url": "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf"},
        {"id": "R11", "requirement": "Clean simple Pages dashboard with subpages", "status": "delivered", "evidence": "10 static pages under nba-research-61a311c2/", "source_url": "https://github.com/sassnarep3-star/Own5"},
        {"id": "R12", "requirement": "Flagged for Review page nonblocking", "status": "delivered", "evidence": "19 flags published; publication not blocked", "source_url": "https://github.com/sassnarep3-star/Own5"},
        {"id": "R13", "requirement": "Coordination claims and frequent commits", "status": "done", "evidence": "Q61 claim fdf6c15; scoped commits; append-only conflict preserved concurrent records", "source_url": "https://github.com/sassnarep3-star/Own5/blob/arena/61a311c2-own5/COORDINATION.md"},
        {"id": "R14", "requirement": "Final integration, PR, merge, Pages verification", "status": "delivered", "evidence": "PR #42 merged f3d164a; post-merge CI success; Pages built; live dashboard/review/lines verified", "source_url": "https://github.com/sassnarep3-star/Own5/pull/42"},
        {"id": "R15", "requirement": "No fabricated ROI/rewards", "status": "delivered", "evidence": "All ROI/monetary fields null; zero graded bets", "source_url": "https://sportsbook.fanduel.com/navigation/nba"},
    ]

    summary = {
        "as_of": AS_OF, "season": SEASON,
        "canonical_rows": len(inp["hist"]) + len(inp["cur_players"]) + len(inp["prior"]) + len(inp["current"]) + len(inp["slate"]) + len(inp["quotes"]) + len(inp["availability"]),
        "historical_player_rows": len(inp["hist"]), "current_player_rows": len(inp["cur_players"]),
        "team_rows": len(inp["current"]), "slate_games": len(inp["slate"]),
        "market_quote_rows": len(inp["quotes"]), "correlation_rows": len(corr),
        "combo_rows": len(combos), "forecast_rows": len(preds),
        "strategies": len(strategies), "qualified_strategies": 0,
        "flags": len(flags), "sources": len(inp["sources"]),
        "gate_decision": decision,
    }
    out = {"summary": summary, "model": model_meta, "sources": inp["sources"],
           "lines": lines, "player_refs": player_refs, "correlations": corr, "lag": lag,
           "combos": combos, "walk_forward": wf, "predictions": preds,
           "gates": gates, "strategies": strategies, "leaderboard": leaderboard,
           "flags": flags, "requirements": requirements,
           "cross_game_correlation": {"r": None, "n": None, "ci": None, "status": "unmeasured", "source_url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html"}}
    (DATA / "derived.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    result = build()
    print(json.dumps(result["summary"], indent=2))
    print("walk-forward:", json.dumps(result["walk_forward"], indent=2))

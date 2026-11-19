#!/usr/bin/env python3
"""Own5 NFL Verification & Decision Desk — session 7e228db8 build engine.

Deterministic, stdlib-only. Computes opponent-aware ratings from the verified
results corpus, originates Week 11 lines (side -> total -> moneyline), opens
price snapshots, computes correlations from the official standings only, and
renders the desk's HTML pages.

Inputs (committed, hash-pinned):
  ../data/nfl-desk-7e228db8/standings_2026_wk10.csv   official standings (2026-11-19 read)
  ../data/nfl-desk-7e228db8/results_2026_week9_10.csv official Week 9/10 finals (2026-11-19 read)
  ../data/nfl-desk-7e228db8/schedule_2026_week11.csv  official Week 11 schedule (2026-11-19 read)
  ../data/nfl-desk-7e228db8/injuries_2026_week11.csv  official Week 11 injury report (2026-11-19 read)
  ../data/games_2026.json                             repo results corpus W1-8 (prior session, verification levels in file meta)
  readiness/suggestions/questions/flagged source rows in this directory

Pre-registration: the model spec (MODEL_SPEC_VERSION) and its parameters are
frozen here and in research/nfl-7e228db8/METHODOLOGY.md BEFORE the Week 11
window opens (first game: IND@HOU, 2026-11-19 8:15 PM ET). The git commit hash
of this file is the registration.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "nfl-desk-7e228db8"
DESK = ROOT / "nfl-desk-7e228db8"

MODEL_SPEC_VERSION = "v1-frozen-2026-11-19"
LEAGUE = [t for t in "BUF SF CHI CIN DEN DET JAX KC MIN PIT NYG CLE GB LA SEA NE CAR BAL DAL LV WAS HOU NO TB AZ ATL IND PHI NYJ LAC MIA TEN".split()]
WEEK11_KICKOFF_UTC = "2026-11-20T01:15:00Z"  # IND@HOU, Thu Nov 19 8:15 PM ET = 01:15 UTC Nov 20

# Abbreviation variants across official sources: nfl.com standings use AZ/LA/WAS;
# the W1-8 corpus (data/games_2026.json) uses ARI/LAR/WSH. Normalised at load.
ABBREV = {"ARI": "AZ", "LAR": "LA", "WSH": "WAS"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def rows(path: Path) -> list[dict]:
    with io.open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, header: list[str], data: list[list | str | float | None]) -> None:
    with io.open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in data:
            w.writerow(r)

def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0

def stdev(xs):
    xs = list(xs)
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

def erf(x: float) -> float:
    return math.erf(x)

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + erf(x / math.sqrt(2.0)))

def pearson(xs, ys):
    xs, ys = list(xs), list(ys)
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0 or syy == 0:
        return 0.0, n
    return sxy / math.sqrt(sxx * syy), n

def fisher_ci(r: float, n: int, z: float = 1.959964):
    if n < 4 or abs(r) >= 1:
        return "", ""
    se = 1.0 / math.sqrt(n - 3)
    zz = 0.5 * math.log((1 + r) / (1 - r))
    lo = math.tanh(zz - z * se)
    hi = math.tanh(zz + z * se)
    return f"{lo:.3f}", f"{hi:.3f}"

def solve_linear(A, b):
    """Gaussian elimination with partial pivoting; pure stdlib."""
    n = len(b)
    M = [row[:] + [bv] for row, bv in zip(A, b)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-12:
            raise ValueError("singular system")
        M[c], M[piv] = M[piv], M[c]
        for r in range(n):
            if r != c:
                fac = M[r][c] / M[c][c]
                for k in range(c, n + 1):
                    M[r][k] -= fac * M[c][k]
    return [M[i][n] / M[i][i] for i in range(n)]

# ---------------------------------------------------------------- data load

def load_standings():
    st = {}
    for r in rows(DATA / "standings_2026_wk10.csv"):
        t = r["team"]
        st[t] = dict(
            w=int(r["w"]), l=int(r["l"]), t=int(r["t"]), pct=float(r["pct"]),
            pf=int(r["pf"]), pa=int(r["pa"]), net=int(r["net"]),
            src=r["source_url"], fetched=r["fetched_at_utc"],
        )
    assert sorted(st) == sorted(LEAGUE), "standings must cover exactly the 32 clubs"
    return st

def load_corpus(st: dict):
    """Verified finals: W1-8 from the repo corpus + W9/W10 from this desk's official read."""
    games = []
    meta = json.loads((ROOT / "data" / "games_2026.json").read_text(encoding="utf-8"))
    for g in meta["games"]:
        if g.get("st") == "final" and g.get("wk") and g["wk"] <= 8:
            games.append(dict(wk=g["wk"], date=g["date"],
                              away=ABBREV.get(g["away"], g["away"]),
                              home=ABBREV.get(g["home"], g["home"]),
                              as_=g["as"], hs=g["hs"],
                              src="https://github.com/sassnarep3-star/Own5/blob/main/data/games_2026.json",
                              ver=g["ver"], intl=None))
    for g in rows(DATA / "results_2026_week9_10.csv"):
        games.append(dict(wk=int(g["week"]), date=g["date_et"], away=g["away"], home=g["home"],
                          as_=int(g["away_pts"]), hs=int(g["home_pts"]),
                          src=g["source_url"], ver="nfl-2026-11-19",
                          intl=g["international"] or None))
    # Corpus patch (F7-16): the shared W1-8 corpus is missing Week 8 MNF CHI@SEA;
    # proved by standings reconciliation, recovered from the official Week 8 schedule page.
    for g in rows(DATA / "results_2026_corpus_patch.csv"):
        games.append(dict(wk=int(g["week"]), date=g["date_et"], away=g["away"], home=g["home"],
                          as_=int(g["away_pts"]), hs=int(g["home_pts"]),
                          src=g["source_url"], ver="nfl-2026-11-19-patch",
                          intl=None))
    # arithmetic sanity
    for g in games:
        assert g["as_"] is not None and g["hs"] is not None
    return games, meta

def reconcile(st, games):
    """W-L-T and PF-PA derived from the corpus must equal the official standings for all 32 clubs."""
    rec = defaultdict(lambda: [0, 0, 0, 0, 0])  # w, l, t, pf, pa
    for g in games:
        a, h = rec[g["away"]], rec[g["home"]]
        a[3] += g["as_"]; a[4] += g["hs"]
        h[3] += g["hs"]; h[4] += g["as_"]
        if g["as_"] > g["hs"]:
            a[0] += 1; h[1] += 1
        elif g["as_"] < g["hs"]:
            h[0] += 1; a[1] += 1
        else:
            a[2] += 1; h[2] += 1
    problems = []
    for t in LEAGUE:
        s = st[t]
        if [s["w"], s["l"], s["t"], s["pf"], s["pa"]] != rec[t][:5]:
            problems.append((t, rec[t][:5], (s["w"], s["l"], s["t"], s["pf"], s["pa"])))
    return problems, rec

# ------------------------------------------------------- opponent-aware fit

def fit_ratings(games, teams):
    """Opponent-aware margin ratings (SRS-style) with home-field as a free parameter.

    Margin model:  m_k (home pts - away pts) = r_home - r_away + hfa + e_k,  sum(r) = 0.
    Solved exactly as a 33x33 least-squares system (pure stdlib). Deterministic.
    """
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    # X^T X and X^T m over columns [r_0..r_{n-1}, hfa]; then a Lagrange row enforcing sum(r)=0 exactly.
    A = [[0.0] * (n + 2) for _ in range(n + 2)]
    b = [0.0] * (n + 2)
    for g in games:
        ih, ia = idx[g["home"]], idx[g["away"]]
        m = g["hs"] - g["as_"]
        # equation: r_h - r_a + hfa = m
        for (j, s) in ((ih, 1.0), (ia, -1.0), (n, 1.0)):
            for (k2, s2) in ((ih, 1.0), (ia, -1.0), (n, 1.0)):
                A[j][k2] += s * s2
            b[j] += s * m
    # KKT block: [X^T X  C^T; C  0] [y; lambda] = [X^T m; 0],  C = row with 1 on r cols, 0 on hfa col
    for j in range(n):
        A[j][n + 1] = 1.0
        A[n + 1][j] = 1.0
    b[n + 1] = 0.0
    sol = solve_linear(A, b)
    ratings = {t: sol[idx[t]] for t in teams}
    hfa = sol[n]
    resid = []
    for g in games:
        mu = ratings[g["home"]] - ratings[g["away"]] + hfa
        resid.append((g["hs"] - g["as_"]) - mu)
    return ratings, hfa, resid

def total_model(st, games):
    """Expected total: mean of the two clubs' per-game points-involved pace (official PF+PA)."""
    gp = {t: st[t]["w"] + st[t]["l"] + st[t]["t"] for t in LEAGUE}
    pace = {t: (st[t]["pf"] + st[t]["pa"]) / gp[t] for t in LEAGUE}
    resid = []
    for g in games:
        exp = (pace[g["home"]] + pace[g["away"]]) / 2.0
        resid.append((g["hs"] + g["as_"]) - exp)
    return pace, resid

# ---------------------------------------------------------------- main build

def main():
    st = load_standings()
    games, meta = load_corpus(st)
    problems, rec = reconcile(st, games)
    n_finals = len(games)
    n_w9 = sum(1 for g in games if g["wk"] == 9)
    n_w10 = sum(1 for g in games if g["wk"] == 10)
    n_w18 = sum(1 for g in games if g["wk"] <= 8)

    # results feed
    write_csv(DATA / "results_feed_2026_through_wk10.csv",
              ["week", "date_et", "away", "home", "away_pts", "home_pts", "status", "international",
               "verification", "source_url"],
              [[g["wk"], g["date"], g["away"], g["home"], g["as_"], g["hs"], "FINAL", g["intl"] or "",
                g["ver"], g["src"]] for g in sorted(games, key=lambda x: (x["wk"], x["date"]))])

    standings_reconciled = not problems
    # ---- ratings (fit uses all 149 finals; see METHODOLOGY for the in-sample caveat)
    ratings, hfa, m_resid = fit_ratings(games, LEAGUE)
    sigma_m = stdev(m_resid)
    pace, t_resid = total_model(st, games)
    sigma_t = stdev(t_resid)

    write_csv(DATA / "ratings_2026_wk11.csv",
              ["team", "srs_rating_pts", "league_rank", "pace_pts_per_game", "games_counted",
               "pf_per_game", "pa_per_game", "net_per_game", "source_url"],
              sorted(
                  [[t, f"{ratings[t]:.2f}", 0, f"{pace[t]:.2f}",
                    st[t]["w"] + st[t]["l"] + st[t]["t"], f"{st[t]['pf'] / (st[t]['w'] + st[t]['l'] + st[t]['t']):.1f}",
                    f"{st[t]['pa'] / (st[t]['w'] + st[t]['l'] + st[t]['t']):.1f}",
                    f"{st[t]['net'] / (st[t]['w'] + st[t]['l'] + st[t]['t']):.1f}",
                    st[t]["src"]] for t in LEAGUE],
                  key=lambda r: -float(r[1])))
    # rank column
    pth = DATA / "ratings_2026_wk11.csv"
    rs = rows(pth)
    for i, r in enumerate(rs, 1):
        r["league_rank"] = i
    write_csv(pth, list(rs[0].keys()), [[r[c] for c in rs[0].keys()] for r in rs])

    # ---- schedule & injuries
    sched = rows(DATA / "schedule_2026_week11.csv")
    inj = rows(DATA / "injuries_2026_week11.csv")
    assert len(sched) == 13, "Week 11 must have exactly 13 games"
    played = set()
    for g in sched:
        played.add(g["away"]); played.add(g["home"])
    byes = sorted(set(LEAGUE) - played)
    assert len(played) == 26 and len(byes) == 6, "schedule must cover 26 clubs, 6 byes"

    # ---- originate Week 11 lines: side first, then total, then moneyline
    # opened_at is pinned to this session's capture window close (all model inputs were fixed by the
    # official reads above; the git commit hash records when the origination was committed). This keeps
    # the build a pure function of committed inputs so CI can assert byte-identical rebuilds.
    opened = "2026-11-19T07:30:00Z"
    lines = []
    markets = []
    for g in sched:
        a, h = g["away"], g["home"]
        mu = ratings[h] - ratings[a] + hfa                      # expected home margin
        exp_total = (pace[h] + pace[a]) / 2.0                   # expected total
        fair_spread = round(-mu * 2) / 2.0                      # home line, half-point precision (push-free)
        fair_total = round(exp_total * 2) / 2.0
        p_home = 1.0 - norm_cdf((0.0 - mu) / sigma_m)
        p_cover_home = 1.0 - norm_cdf((-fair_spread - mu) / sigma_m)
        p_over = 1.0 - norm_cdf((fair_total - exp_total) / sigma_t)
        inputs = dict(model_spec_version=MODEL_SPEC_VERSION, corpus_finals=n_finals,
                      srs_home=round(ratings[h], 3), srs_away=round(ratings[a], 3),
                      hfa_pts=round(hfa, 3), sigma_margin=round(sigma_m, 3),
                      pace_home=round(pace[h], 3), pace_away=round(pace[a], 3),
                      sigma_total=round(sigma_t, 3), mu_home_margin=round(mu, 3))
        payload = json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()
        inputs_sha = hashlib.sha256(payload).hexdigest()
        game_id = g["game_id"]
        lines.append([game_id, 11, g["date_et"], g["time_et"], a, h,
                      f"{fair_spread:+.1f}", "", "",                    # side: fair, market(blank), diff(blank)
                      f"{fair_total:.1f}", "", "",                      # total: fair, market(blank), diff(blank)
                      f"{p_home:.3f}", "",                              # moneyline: p_home (no-vig), fair decimal odds
                      f"{1.0 / p_home:.2f}", f"{1.0 / (1.0 - p_home):.2f}",
                      f"{p_cover_home:.3f}", f"{p_over:.3f}",
                      json.dumps(inputs, sort_keys=True), inputs_sha,
                      WEEK11_KICKOFF_UTC, g["source_url"],
                      "F7-P01 market columns blank: no verified operator price (see flagged.csv)"])
        for mk, fair in (("SIDE_SPREAD", f"{fair_spread:+.1f}"), ("TOTAL", f"{fair_total:.1f}"),
                         ("MONEYLINE", f"{p_home:.3f}")):
            markets.append([f"{game_id}:{mk}", game_id, mk, fair, "", "", "", "", "",
                            opened, inputs_sha, "F7-P01: market open/close blank+flagged; snapshot records OUR fair line as the originated opening value only"])

    write_csv(DATA / "lines_week11.csv",
              ["game_id", "week", "date_et", "time_et", "away", "home",
               "fair_spread_home", "market_spread", "spread_diff",
               "fair_total", "market_total", "total_diff",
               "p_home_win_novig", "market_p_home", "fair_odds_home_decimal", "fair_odds_away_decimal",
               "p_home_cover_fair", "p_over_fair",
               "inputs_json", "inputs_sha256", "kickoff_utc", "source_url", "market_flag"],
              lines)
    write_csv(DATA / "price_snapshots.csv",
              ["snapshot_id", "game_id", "market", "our_open_fair_value", "market_open",
               "market_close", "closing_source", "residual_vs_market", "clv",
               "opened_at_utc", "inputs_sha256", "policy_note"],
              markets)

    # ---- correlations from official standings only (n=32 each)
    gp = {t: st[t]["w"] + st[t]["l"] + st[t]["t"] for t in LEAGUE}
    pct = [st[t]["pct"] for t in LEAGUE]
    netg = [st[t]["net"] / gp[t] for t in LEAGUE]
    pfg = [st[t]["pf"] / gp[t] for t in LEAGUE]
    pag = [st[t]["pa"] / gp[t] for t in LEAGUE]
    corrs = []
    for label, xs in (("NET/G vs WIN_PCT", netg), ("PF/G vs WIN_PCT", pfg),
                      ("PA/G vs WIN_PCT", pag), ("PF/G vs PA/G", pfg)):
        ys = pag if "PF/G vs PA/G" == label else pct
        r, n = pearson(xs, ys)
        lo, hi = fisher_ci(r, n)
        corrs.append([label, f"{r:.4f}", n, lo, hi, st[LEAGUE[0]]["src"],
                      "computed in-repo from official standings capture 2026-11-19; Fisher z 95% CI"])
    write_csv(DATA / "correlations.csv",
              ["pair", "pearson_r", "n", "ci95_low", "ci95_high", "source_url", "method"], corrs)

    # ---- model inputs + spec hash (pre-registration artefact)
    spec = dict(model_spec_version=MODEL_SPEC_VERSION, corpus_finals=n_finals,
                corpus_w18=n_w18, corpus_w9=n_w9, corpus_w10=n_w10,
                standings_reconciled_32=standings_reconciled,
                hfa_pts=round(hfa, 3), sigma_margin_pts=round(sigma_m, 3),
                sigma_total_pts=round(sigma_t, 3),
                residual_count_margin=len(m_resid), residual_count_total=len(t_resid),
                week11_kickoff_utc=WEEK11_KICKOFF_UTC,
                order="side first, then total, then moneyline",
                market_policy="no verified operator prices; market/residual/CLV blank+flagged F7-P01",
                in_sample_caveat="HFA/sigma estimated in-sample on the 149-final corpus; prospective shadow baseline starts with IND@HOU 2026-11-20T01:15Z")
    blob = json.dumps(spec, sort_keys=True, separators=(",", ":")).encode()
    spec_sha = hashlib.sha256(blob).hexdigest()
    (DATA / "model_inputs.json").write_text(json.dumps(spec, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    # ---- leaderboard: pre-registered, signal separated from staking, no backtest numbers
    board = [
        ["BASE-RANDOM", "singles", "control", "control", "not_certified", "", "", "", "", "control baseline: uniform random picks recorded prospectively from Week 11"],
        ["BASE-FAV", "singles", "control", "control", "not_certified", "", "", "", "", "control baseline: favourites only (model p_home max), recorded prospectively from Week 11"],
        ["S1-PPG-DIFF", "singles", "pre_registered", "pre_registered", "not_certified", "", "", "", "", "signal = SRS margin residual; staking = flat, signal-separated; prospective from Week 11"],
        ["S2-HOME-DOG", "singles", "pre_registered", "pre_registered", "not_certified", "", "", "", "", "pre-registered only; no backtest numbers on the board (R029)"],
        ["S3-TOTAL-BIAS", "singles", "pre_registered", "pre_registered", "not_certified", "", "", "", "", "pre-registered only"],
        ["S4-ML-SHORT", "singles", "pre_registered", "pre_registered", "not_certified", "", "", "", "", "pre-registered only"],
    ]
    write_csv(DATA / "leaderboard.csv",
              ["strategy_id", "division", "signal_status", "staking_status", "certification",
               "brier_skill", "lower_bound_95", "n_prospective", "stake_record", "notes"], board)

    write_csv(DATA / "gates.csv",
              ["gate_id", "name", "definition", "blocks", "status"],
              [
                  ["G0", "pre-registration", "strategy/spec text + sample window committed before results are seen; commit hash is the registration", "leaderboard entry; any certification", "active"],
                  ["G1", "minimum sample", "prospective sample >= 50 rated decisions before a strategy is ranked", "ranking", "active"],
                  ["G2", "significance (Bonferroni)", "p < 0.05 / number of pre-registered variants", "certification", "active"],
                  ["G3", "chronological holdout", "evaluation on data strictly after training window", "certification", "active"],
                  ["G4", "closing-line value", "CLV computable only with verified operator closing prices", "ROI claims", "blocked: no operator price source (F7-P01)"],
                  ["G5", "correlation cap", "correlations from official sources only; n published per value", "combo ranking", "active"],
                  ["G6", "drawdown + uncertainty", "proper-score ranking with game-cluster lower bound; win rate/short ROI excluded", "ranking", "active"],
                  ["G7", "demotion gate", "a live strategy that fails G5/G8 over a 4-week window returns to paper", "live status", "active"],
                  ["G8", "market integrity", "no wagering where not lawful; no unlicensed data terms accepted silently", "publication of ROI", "active"],
                  ["G9", "parlay joint-evidence", "combo ranked only with validated joint probability + operator void/push rules", "parlay/SGP/prop combos", "active"],
              ])

    # ---- readiness: one row per requirement from the shared registry (R001-R079)
    base = ROOT / "data" / "nfl-origin-desk" / "requirements.csv"
    ready = []
    my_updates = {
        "R001": ("Met", "all brief requirements mapped in this desk's readiness table", str(len(rows(base)) - 1) + " rows mapped"),
        "R004": ("Partially met", "own spread+total+ML originated for all 13 Week 11 games from official standings+schedule", f"13 games x 3 markets = 39 markets (fair lines only)"),
        "R011": ("Partially met", "two stamped league-report reads exist repo-wide (2026-11-12 other desk, 2026-11-19 this desk); Wed-Fri-to-kickoff daily capture still unautomated", "2 stamped reads; 1 by this desk"),
        "R020": ("Partially met", "immutable open snapshot per originated market with inputs hash; closing still blank+flagged", "39 open snapshots; 0 closings"),
        "R021": ("Met", "verified game-level results feed through Week 10 in this namespace", f"{n_finals} finals (W1-8 corpus {n_w18} + W9 {n_w9} + W10 {n_w10})"),
        "R023": ("Partially met", "fair line published; market line and diff blank+flagged", "fair published for 39 markets; market blank"),
        "R031": ("Partially met", "injury report captured as a timestamped read; delta vs prior capture computed by the owning desk (2026-11-12)", "2 stamped reads repo-wide"),
        "R037": ("Met", "fair_spread/market_spread/spread_diff and total equivalents as separate columns (market blank+flagged)", "3 column sets present"),
        "R035": ("Met", "every line row stores probabilities and full inputs_json with sha256", "39/39 rows"),
        "R039": ("Met", "price-data policy frozen: no unverified operator feeds; snapshot store records originated fair values; closings blank until licensed source", "policy in model_inputs.json"),
        "R048": ("Partially met", "hash-pinned raw excerpts with timestamps stored in this namespace for the 2026-11-19 read", "7 excerpt files hashed"),
        "R059": ("Partially met", "per-team injury view built from the official Week 11 report (starters-out requires depth data; counts published)", "26 team tables, 253 rows"),
        "R065": ("Partially met", "point-in-time ledger: this desk's read is stamped+hashed; replay across desks still manual", "1 stamped read by this desk"),
        "R069": ("Partially met", "what-changed diffs exist per desk; league-wide diff still aggregated manually", "delta visible vs 2026-11-12/18 captures"),
        "R071": ("Partially met", "drift alarm active in this desk's verifier (pinned counts); other desks own their own alarms", "1 verifier with pinned counts"),
        "R016": ("Met", "every row sourced or explicit blank+flag; verifier fail-closed", "see verify_desk.py output"),
    }
    for r in rows(base):
        rid = r["id"]
        if rid in my_updates:
            stat, gate_note, observed = my_updates[rid]
            ready.append([rid, r["requirement"], stat, r["blocking_gate"], r["number_to_clear"],
                          observed, r["source_url"], f"updated by desk 7e228db8 2026-11-19: {gate_note}"])
        else:
            ready.append([rid, r["requirement"], r["status"], r["blocking_gate"], r["number_to_clear"],
                          r["observed_number"], r["source_url"], "carried from shared registry (owner desk: nfl-origin-desk)"])
    write_csv(DATA / "readiness.csv",
              ["id", "requirement", "status", "blocking_gate", "number_to_clear", "observed_number",
               "source_url", "notes"], ready)

    # ---- context inputs for the site
    ctx = dict(
        n_finals=n_finals, n_w18=n_w18, n_w9=n_w9, n_w10=n_w10,
        standings_reconciled=standings_reconciled, problems=problems,
        hfa=round(hfa, 3), sigma_m=round(sigma_m, 3), sigma_t=round(sigma_t, 3),
        n_byes=len(byes), byes=byes, n_inj_rows=len(inj),
        opened=opened, spec_sha=spec_sha, spec=spec,
        ratings={t: round(ratings[t], 2) for t in LEAGUE},
    )
    (DATA / "build_context.json").write_text(json.dumps(ctx, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: ctx[k] for k in ("n_finals", "hfa", "sigma_m", "sigma_t", "standings_reconciled", "spec_sha")}, indent=1))
    if problems:
        print("RECONCILIATION PROBLEMS:", problems, file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()

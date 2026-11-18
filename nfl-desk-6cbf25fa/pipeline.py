#!/usr/bin/env python3
"""Deterministic pipeline for the 6cbf25fa desk: ratings, Week 11 origination,
price-snapshot store, injury-read delta ledger, and register CSVs.

Determinism: no network, no clock.  Every timestamp comes from committed
capture files (read_utc).  Inputs:
  - data/decision-desk/raw/games.csv.gz          pinned nflverse snapshot (hash-verified
                                                 against data/decision-desk/raw/provenance.json)
  - data/nfl-desk-6cbf25fa/results_week10.csv    official NFL.com finals read 2026-11-18
  - data/nfl-desk-6cbf25fa/standings_2026-11-18.csv  official NFL.com standings read 2026-11-18
  - data/nfl-desk-6cbf25fa/game_centre_min_sf_2026-11-18.csv  official venue read
  - nfl-desk-3cb7800c/data/week11_schedule.csv   official Week-11 slate captured 2026-11-18T03:13Z
  - data/decision-desk/official/official_injuries_wk10.csv   prior injury read (2026-11-12T16:52:39Z)
  - data/nfl-desk-6cbf25fa/injury_reads/capture_injuries_2026-11-18.csv  this desk's read

Model specification (pre-registered): research/nfl-6cbf25fa/model_spec.md.
The spec file's SHA256 is recorded in model_inputs.json; the spec was written
before the Week 11 lines were computed and before any Week 11 result exists.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
D = os.path.join(ROOT, "data", "nfl-desk-6cbf25fa")
LEADS = os.path.join(D, "injury_reads")
RESEARCH = os.path.join(ROOT, "research", "nfl-6cbf25fa")

STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
SCORES_PAGE = "https://www.nfl.com/scores/2026/week-10"
INJ_URL = "https://www.nfl.com/injuries/league/2026/reg10"
GAME_URL = "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11"

TEAM32 = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
          "DET", "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA",
          "MIN", "NE", "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB",
          "TEN", "WAS"]

NICK_TO_CODE = {
    "Cardinals": "AZ", "Falcons": "ATL", "Ravens": "BAL", "Bills": "BUF",
    "Panthers": "CAR", "Bears": "CHI", "Bengals": "CIN", "Browns": "CLE",
    "Cowboys": "DAL", "Broncos": "DEN", "Lions": "DET", "Packers": "GB",
    "Texans": "HOU", "Colts": "IND", "Jaguars": "JAX", "Chiefs": "KC",
    "Chargers": "LAC", "Rams": "LAR", "Raiders": "LV", "Dolphins": "MIA",
    "Vikings": "MIN", "Patriots": "NE", "Saints": "NO", "Giants": "NYG",
    "Jets": "NYJ", "Eagles": "PHI", "Steelers": "PIT", "Seahawks": "SEA",
    "49ers": "SF", "Buccaneers": "TB", "Titans": "TEN", "Commanders": "WAS",
}


# Canonical codes follow the pinned nflverse snapshot (ARI, LAR).  Official
# pages print the Rams as LA (standings/scores pages) and Arizona as AZ; the
# league injury page prints LAR and AZ.  Both are normalized here.
TO_CANONICAL = {"LA": "LAR", "AZ": "ARI"}


def canon(code):
    return TO_CANONICAL.get(code, code)


def read_csv_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def verify_pinned_snapshot():
    """Verify the committed nflverse snapshot files against their recorded sha256."""
    prov = json.load(open(os.path.join(ROOT, "data", "decision-desk", "raw", "provenance.json")))
    problems = []
    for a in prov.get("assets", []):
        p = os.path.join(ROOT, a["committed_as"])
        if not os.path.exists(p):
            problems.append(f"missing {a['committed_as']}")
            continue
        got = sha256_file(p)
        if got != a["sha256"]:
            problems.append(f"hash mismatch {a['committed_as']}: committed={a['sha256'][:12]} got={got[:12]}")
    return prov, problems


def load_corpus():
    """2026 regular-season finals: weeks 1-9 from the pinned nflverse snapshot,
    week 10 from this desk's official NFL.com capture."""
    rows = list(csv.DictReader(gzip.open(os.path.join(ROOT, "data", "decision-desk", "raw", "games.csv.gz"), "rt")))
    corpus, provenance = [], []
    for r in rows:
        if r["season"] != "2026" or r["game_type"] != "REG":
            continue
        wk = int(r["week"])
        if wk <= 9 and r["home_score"] not in ("", None):
            corpus.append({
                "week": wk, "away": canon(r["away_team"]), "home": canon(r["home_team"]),
                "as": int(r["away_score"]), "hs": int(r["home_score"]),
                "neutral": r.get("location") == "Neutral",
                "source": "nflverse pinned snapshot (sha256-verified) https://github.com/nflverse/nflverse-data/releases/tag/injuries",
                "game_id": r["game_id"],
            })
    wk10 = read_csv_rows(os.path.join(D, "results_week10.csv"))
    for r in wk10:
        corpus.append({
            "week": 10, "away": canon(r["away_team"]), "home": canon(r["home_team"]),
            "as": int(r["away_score"]), "hs": int(r["home_score"]),
            "neutral": r["neutral_site"] == "yes",
            "source": f"official NFL.com scores page read 2026-11-18 ({SCORES_PAGE})",
            "game_id": r["game_slug"],
        })
    provenance = {
        "weeks_1_9": "nflverse pinned snapshot, sha256 re-verified this run against data/decision-desk/raw/provenance.json",
        "week_10": "official NFL.com scores page (https://www.nfl.com/scores/2026/reg10), read_utc 2026-11-18T03:55:13Z",
    }
    return corpus, provenance


def crosscheck_standings(corpus):
    """Recompute W-L-T, PF, PA, NET from the game corpus and compare to the
    official standings page as read on 2026-11-18.  Returns check rows."""
    st = {t: {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0, "gp": 0} for t in TEAM32}
    for g in corpus:
        for team, pf, pa in ((g["home"], g["hs"], g["as"]), (g["away"], g["as"], g["hs"])):
            s = st[team]
            s["gp"] += 1
            s["pf"] += pf
            s["pa"] += pa
            if pf > pa:
                s["w"] += 1
            elif pf < pa:
                s["l"] += 1
            else:
                s["t"] += 1
    checks = []
    std = read_csv_rows(os.path.join(D, "standings_2026-11-18.csv"))
    for r in std:
        code = TO_CANONICAL.get(r["team_code"], r["team_code"])
        cells = r["raw_cells_as_printed"].split(" | ")
        # printed column order: W, L, T, PCT, PF, PA, NET PTS, then ambiguous
        # record columns kept raw (not published) - see flagged F-P05
        w, l, t = int(cells[0]), int(cells[1]), int(cells[2])
        pct_printed = float(cells[3])
        pf, pa, net = int(cells[4]), int(cells[5]), int(cells[6])
        pct_expected = (w + 0.5 * t) / (w + l + t)
        ok_pct = abs(pct_printed - round(pct_expected, 3)) < 1e-9
        c = st[code]
        ok_wlt = (w, l, t) == (c["w"], c["l"], c["t"])
        ok_pfpa = (pf, pa, net) == (c["pf"], c["pa"], c["pf"] - c["pa"])
        ok_net = net == pf - pa
        checks.append({
            "team": code, "page_wlt": f"{w}-{l}-{t}", "computed_wlt": f"{c['w']}-{c['l']}-{c['t']}",
            "page_pf": pf, "computed_pf": c["pf"], "page_pa": pa, "computed_pa": c["pa"],
            "page_net": net, "computed_net": c["pf"] - c["pa"],
            "wlt_match": "yes" if ok_wlt else "NO",
            "pf_pa_net_match": "yes" if ok_pfpa else "NO",
            "net_identity": "yes" if ok_net else "NO",
            "pct_match": "yes" if ok_pct else "NO",
        })
    return checks, st


def compute_ratings(corpus):
    """Two-iteration opponent-adjusted scoring/defense ratings + one-pass HFA
    + residual sigma + empirical tie rate.  Spec: research/nfl-6cbf25fa/model_spec.md."""
    games_played = {t: 0 for t in TEAM32}
    o = {t: 0.0 for t in TEAM32}   # offensive deviation (points above league mean per game)
    e = {t: 0.0 for t in TEAM32}   # defensive effectiveness (points suppressed below mean per game)
    totals = []
    for g in corpus:
        totals.append(g["hs"] + g["as"])
        games_played[g["home"]] += 1
        games_played[g["away"]] += 1
    L = sum(totals) / 2.0 / len(corpus)  # league mean points per team-game
    for t in TEAM32:
        scored = [ (g["hs"] if g["home"] == t else g["as"]) for g in corpus if t in (g["home"], g["away"]) ]
        allowed = [ (g["as"] if g["home"] == t else g["hs"]) for g in corpus if t in (g["home"], g["away"]) ]
        o[t] = sum(scored) / len(scored) - L
        e[t] = L - sum(allowed) / len(allowed)

    # two opponent-adjustment iterations
    for _ in range(2):
        o_adj = {t: [] for t in TEAM32}
        e_adj = {t: [] for t in TEAM32}
        for g in corpus:
            h, a = g["home"], g["away"]
            o_adj[h].append(g["hs"] - L + e[a])
            o_adj[a].append(g["as"] - L + e[h])
            e_adj[h].append(o[a] - (g["as"] - L))
            e_adj[a].append(o[h] - (g["hs"] - L))
        o = {t: sum(v) / len(v) for t, v in o_adj.items() if v}
        e = {t: sum(v) / len(v) for t, v in e_adj.items() if v}
        # recenter so L remains the league mean
        mo = sum(o.values()) / len(o)
        me = sum(e.values()) / len(e)
        o = {t: v - mo for t, v in o.items()}
        e = {t: v - me for t, v in e.items()}

    def base_strength(t):
        return o[t] - e[t]

    # one-pass HFA over location=Home games only
    res_home = []
    for g in corpus:
        if g["neutral"]:
            continue
        pred = base_strength(g["home"]) - base_strength(g["away"])
        res_home.append((g["hs"] - g["as"]) - pred)
    hfa = sum(res_home) / len(res_home)

    # residual sigma over all games (HFA applied to home games, 0 at neutral)
    res_all = []
    for g in corpus:
        pred = base_strength(g["home"]) - base_strength(g["away"]) + (0.0 if g["neutral"] else hfa)
        res_all.append((g["hs"] - g["as"]) - pred)
    mean_res = sum(res_all) / len(res_all)
    sigma = math.sqrt(sum((x - mean_res) ** 2 for x in res_all) / len(res_all))

    ties = sum(1 for g in corpus if g["hs"] == g["as"])
    tie_rate = ties / len(corpus)
    return {
        "league_mean_points_per_team_game": round(L, 6),
        "offensive_deviation": {t: round(o[t], 6) for t in TEAM32},
        "defensive_effectiveness": {t: round(e[t], 6) for t in TEAM32},
        "hfa_points": round(hfa, 6),
        "hfa_n_home_games": len(res_home),
        "sigma_points": round(sigma, 6),
        "sigma_n_games": len(res_all),
        "residual_mean_points": round(mean_res, 6),
        "tie_rate": round(tie_rate, 6),
        "ties": ties,
        "games_in_corpus": len(corpus),
        "games_played": games_played,
        "method_iterations": "2 opponent-adjustment iterations, recentered; one-pass HFA on location=Home games; sigma = residual std over all games with HFA applied to home games and 0 at neutral-site games",
    }


def load_week11_fixtures():
    """Week 11 fixtures from the pinned nflverse schedule, cross-checked against
    the official slate captured by session 3cb7800c from nfl.com (2026-11-18T03:13Z)."""
    rows = list(csv.DictReader(gzip.open(os.path.join(ROOT, "data", "decision-desk", "raw", "games.csv.gz"), "rt")))
    fx = [r for r in rows if r["season"] == "2026" and r["game_type"] == "REG" and r["week"] == "11"]
    fixtures = []
    for r in fx:
        fixtures.append({
            "game_id": r["game_id"],
            "away": canon(r["away_team"]), "home": canon(r["home_team"]),
            "neutral": r.get("location") == "Neutral",
            "stadium_nflverse": r.get("stadium", ""),
            "gameday": r.get("gameday", ""),
        })
    official = read_csv_rows(os.path.join(ROOT, "nfl-desk-3cb7800c", "data", "week11_schedule.csv"))
    # official page prints AZ/LA; normalize to canonical ARI/LAR before comparing
    official_pairs = {(TO_CANONICAL.get(r["away_code"], r["away_code"]),
                       TO_CANONICAL.get(r["home_code"], r["home_code"])): r for r in official}
    nflverse_pairs = {(f["away"], f["home"]): f for f in fixtures}
    cross = {
        "official_slate_rows": len(official),
        "nflverse_fixture_rows": len(fixtures),
        "matchups_identical": "yes" if set(official_pairs) == set(nflverse_pairs) else "NO",
        "mismatches": sorted(
            [f"{a}@{h}" for (a, h) in set(official_pairs) ^ set(nflverse_pairs)]),
    }
    byes = sorted(set(TEAM32) - set(nflverse_pairs.keys().__iter__().__next__() if False else [t for p in nflverse_pairs for t in p]))
    return fixtures, official_pairs, cross, byes


def round_half(x):
    """Round to nearest 0.5, halves away from zero (documented convention)."""
    return math.copysign(math.floor(abs(x) * 2 + 0.5) / 2, x)


def american_odds(p):
    if p <= 0 or p >= 1:
        return None
    if p >= 0.5:
        return int(round(-100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def build_lines(ratings, fixtures, official_pairs, read_utc, inputs_sha):
    lines = []
    for f in fixtures:
        h, a = f["home"], f["away"]
        o, e = ratings["offensive_deviation"], ratings["defensive_effectiveness"]
        H = 0.0 if f["neutral"] else ratings["hfa_points"]
        margin = (o[h] - e[h]) - (o[a] - e[a]) + H
        total = 2 * ratings["league_mean_points_per_team_game"] + (o[h] + o[a]) - (e[h] + e[a])
        p_raw = norm_cdf(margin / ratings["sigma_points"])
        p_push = ratings["tie_rate"]
        p_home = p_raw * (1 - p_push)
        p_away = (1 - p_raw) * (1 - p_push)
        off = official_pairs.get((a, h), {})
        game_url = off.get("official_game_url", f"https://www.nfl.com/games/{h.lower()}-vs-{a.lower()}-2026-reg-11")
        kickoff = off.get("kickoff_as_printed", "")
        network = off.get("network_as_printed", "")
        common = {
            "game_id": f["game_id"], "away_team": a, "home_team": h,
            "neutral_site": "yes" if f["neutral"] else "no",
            "kickoff_as_printed": kickoff, "network_as_printed": network,
            "official_game_url": game_url,
            "p_home_win": f"{p_home:.6f}", "p_away_win": f"{p_away:.6f}", "p_push": f"{p_push:.6f}",
            "inputs_sha256": inputs_sha, "opened_utc": read_utc,
            "market_line": "", "market_source": "", "residual_fair_minus_market": "",
        }
        spec_note = "originated by desk 6cbf25fa; spec research/nfl-6cbf25fa/model_spec.md; inputs model_inputs.json"
        lines.append({**common, "market_type": "side", "direction": "home",
                      "fair_value_unrounded": f"{margin:.6f}", "fair_value_rounded": f"{round_half(margin):.1f}",
                      "source_url": game_url, "notes": "fair spread, home margin; market line blank+flagged F-P01; " + spec_note})
        lines.append({**common, "market_type": "total", "direction": "over",
                      "fair_value_unrounded": f"{total:.6f}", "fair_value_rounded": f"{round_half(total):.1f}",
                      "source_url": game_url, "notes": "fair total; market line blank+flagged F-P01; " + spec_note})
        lines.append({**common, "market_type": "moneyline", "direction": "home",
                      "fair_value_unrounded": f"{p_home:.6f}",
                      "fair_value_rounded": str(american_odds(p_home)),
                      "source_url": game_url,
                      "notes": ("fair ML home (American) = " + str(american_odds(p_home)) +
                                ", fair ML away (American) = " + str(american_odds(p_away)) +
                                "; decimal = (1-p_push)/p_win; market line blank+flagged F-P01; " + spec_note)})
    return lines


def build_snapshots(lines, read_utc):
    snaps = []
    for ln in lines:
        snaps.append({
            "market_id": f"{ln['game_id']}_{ln['market_type']}_{ln['direction']}",
            "game_id": ln["game_id"], "away_team": ln["away_team"], "home_team": ln["home_team"],
            "market_type": ln["market_type"], "direction": ln["direction"],
            "opened_utc": ln["opened_utc"],
            "opening_fair_unrounded": ln["fair_value_unrounded"],
            "opening_fair_rounded": ln["fair_value_rounded"],
            "closing_fair_unrounded": "",  # populated only post-kickoff per price policy
            "closing_fair_rounded": "",
            "closing_source": "",
            "market_line_open": "", "market_line_close": "",
            "residual_open": "", "residual_close": "",
            "status": "open",
            "inputs_sha256": ln["inputs_sha256"],
            "source_url": ln["source_url"],
            "notes": "closing columns intentionally blank until the game completes (policy: never inferred); market columns blank+flagged F-P01",
        })
    return snaps


def injury_deltas(read_utc):
    """Player-level delta between the prior committed read (2026-11-12T16:52:39Z,
    decision-desk capture) and this desk's 2026-11-18 read.  Deltas, never levels."""
    prior = read_csv_rows(os.path.join(ROOT, "data", "decision-desk", "official", "official_injuries_wk10.csv"))
    prior_map = {}
    for r in prior:
        code = TO_CANONICAL.get(NICK_TO_CODE.get(r["team_nickname"], ""), NICK_TO_CODE.get(r["team_nickname"]))
        prior_map[(code, r["player"])] = r
    today = read_csv_rows(os.path.join(LEADS, "capture_injuries_2026-11-18.csv"))
    today_map = {(r["team_code"], r["player"]): r for r in today}
    prior_utc = prior[0]["retrieved_utc"] if prior else ""
    deltas = []
    for key, cur in today_map.items():
        old = prior_map.get(key)
        if old is None:
            deltas.append(["added_to_report", key[0], key[1], cur["position"], "row", "", "present",
                           prior_utc, read_utc, INJ_URL])
            continue
        for field, pcol, ccol in (("injuries", "injury", "injuries"),
                                  ("practice_status", "practice_status", "practice_status"),
                                  ("game_status", "game_status", "game_status")):
            if (old[pcol] or "") != (cur[ccol] or ""):
                deltas.append([f"{field}_changed", key[0], key[1], cur["position"], field,
                               old[pcol], cur[ccol], prior_utc, read_utc, INJ_URL])
    for key, old in prior_map.items():
        if key not in today_map:
            deltas.append(["removed_from_report", key[0], key[1], old["position"], "row",
                           "present", "absent", prior_utc, read_utc, INJ_URL])
    delta_order = {"added_to_report": 0, "removed_from_report": 1, "game_status_changed": 2,
                   "practice_status_changed": 3, "injuries_changed": 4}
    deltas.sort(key=lambda d: (delta_order.get(d[0], 9), d[1], d[2]))
    return prior, today, prior_utc, deltas


def main():
    os.makedirs(D, exist_ok=True)
    os.makedirs(LEADS, exist_ok=True)
    os.makedirs(RESEARCH, exist_ok=True)

    prov, hash_problems = verify_pinned_snapshot()

    corpus, prov_notes = load_corpus()
    checks, standings_calc = crosscheck_standings(corpus)
    wlt_mismatch = [c for c in checks if c["wlt_match"] != "yes"]
    pfpa_mismatch = [c for c in checks if c["pf_pa_net_match"] != "yes"]
    pct_mismatch = [c for c in checks if c["pct_match"] != "yes"]

    ratings = compute_ratings(corpus)

    spec_path = os.path.join(RESEARCH, "model_spec.md")
    spec_sha = sha256_file(spec_path)
    read_utc = read_csv_rows(os.path.join(D, "results_week10.csv"))[0]["read_utc"]

    model_inputs = {
        "spec_file": "research/nfl-6cbf25fa/model_spec.md",
        "spec_sha256": spec_sha,
        "pre_registration": "spec frozen before any Week 11 result exists; commit hash is the registration",
        "corpus_games": len(corpus),
        "corpus_provenance": prov_notes,
        "pinned_snapshot_hash_problems": hash_problems,
        "ratings": ratings,
        "standings_crosscheck_mismatch_teams_wlt": [c["team"] for c in wlt_mismatch],
        "standings_crosscheck_mismatch_teams_pfpa": [c["team"] for c in pfpa_mismatch],
        "standings_crosscheck_mismatch_teams_pct": [c["team"] for c in pct_mismatch],
        "read_utc": read_utc,
    }
    inputs_path = os.path.join(D, "model_inputs.json")
    with open(inputs_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(model_inputs, f, indent=2, sort_keys=True)
        f.write("\n")
    inputs_sha = sha256_file(inputs_path)

    fixtures, official_pairs, cross, byes = load_week11_fixtures()
    lines = build_lines(ratings, fixtures, official_pairs, read_utc, inputs_sha)

    write_csv(os.path.join(D, "lines_week11.csv"),
              ["game_id", "away_team", "home_team", "neutral_site", "kickoff_as_printed",
               "network_as_printed", "official_game_url", "market_type", "direction",
               "fair_value_unrounded", "fair_value_rounded", "market_line", "market_source",
               "residual_fair_minus_market", "p_home_win", "p_away_win", "p_push",
               "inputs_sha256", "opened_utc", "source_url", "notes"],
              [[ln[k] for k in ["game_id", "away_team", "home_team", "neutral_site", "kickoff_as_printed",
                                "network_as_printed", "official_game_url", "market_type", "direction",
                                "fair_value_unrounded", "fair_value_rounded", "market_line", "market_source",
                                "residual_fair_minus_market", "p_home_win", "p_away_win", "p_push",
                                "inputs_sha256", "opened_utc", "source_url", "notes"]] for ln in lines])

    snaps = build_snapshots(lines, read_utc)
    snap_path = os.path.join(D, "price_snapshots.csv")
    write_csv(snap_path,
              ["market_id", "game_id", "away_team", "home_team", "market_type", "direction",
               "opened_utc", "opening_fair_unrounded", "opening_fair_rounded",
               "closing_fair_unrounded", "closing_fair_rounded", "closing_source",
               "market_line_open", "market_line_close", "residual_open", "residual_close",
               "status", "inputs_sha256", "source_url", "notes"],
              [[s[k] for k in ["market_id", "game_id", "away_team", "home_team", "market_type", "direction",
                               "opened_utc", "opening_fair_unrounded", "opening_fair_rounded",
                               "closing_fair_unrounded", "closing_fair_rounded", "closing_source",
                               "market_line_open", "market_line_close", "residual_open", "residual_close",
                               "status", "inputs_sha256", "source_url", "notes"]] for s in snaps])

    # ---- week 11 byes + fixture cross-check CSV
    NFLVERSE_URL = "https://github.com/nflverse/nflverse-data/releases/tag/games"
    SCHED_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
    write_csv(os.path.join(D, "week11_fixtures_crosscheck.csv"),
              ["check", "value", "source_url", "read_utc"],
              [["official_slate_rows", cross["official_slate_rows"], SCHED_URL, "2026-11-18T03:13:31Z"],
               ["nflverse_fixture_rows", cross["nflverse_fixture_rows"], NFLVERSE_URL, read_utc],
               ["matchups_identical", cross["matchups_identical"], NFLVERSE_URL, read_utc],
               ["week11_byes", ", ".join(byes), SCHED_URL, read_utc]])

    # ---- injury delta ledger
    prior, today, prior_utc, deltas = injury_deltas(read_utc)
    write_csv(os.path.join(LEADS, "deltas_2026-11-12_to_2026-11-18.csv"),
              ["change_type", "team_code", "player", "position", "field", "value_prior_read",
               "value_this_read", "prior_read_utc", "this_read_utc", "source_url"],
              deltas)
    prior_teams = sorted({NICK_TO_CODE.get(r["team_nickname"], "?") for r in prior})
    write_csv(os.path.join(LEADS, "reads.csv"),
              ["read_id", "captured_utc", "row_count", "teams_in_capture", "source_url", "captured_by", "storage"],
              [["read_2026-11-12", prior_utc, len(prior), len(prior_teams), INJ_URL,
                "decision-desk session (data/decision-desk/official/official_injuries_wk10.csv)",
                "committed CSV in another desk's namespace"],
               ["read_2026-11-18", read_utc, len(today), len({r['team_code'] for r in today}), INJ_URL,
                "desk 6cbf25fa", "data/nfl-desk-6cbf25fa/injury_reads/capture_injuries_2026-11-18.csv + raw extracts (SHA256SUMS)"]])

    print(f"corpus games: {len(corpus)}; hfa={ratings['hfa_points']:.3f} (n={ratings['hfa_n_home_games']}), "
          f"sigma={ratings['sigma_points']:.3f} (n={ratings['sigma_n_games']}), tie_rate={ratings['tie_rate']:.4f} "
          f"(ties={ratings['ties']})")
    print(f"standings crosscheck: wlt mismatches={len(wlt_mismatch)} pfpa mismatches={len(pfpa_mismatch)}")
    print(f"snapshot hash problems: {len(hash_problems)}")
    print(f"week11 fixtures: {len(fixtures)} (matchups identical to official slate: {cross['matchups_identical']}), byes={','.join(byes)}")
    print(f"lines: {len(lines)} markets; snapshots: {len(snaps)}")
    print(f"injury deltas: {len(deltas)} rows (prior {len(prior)} rows/{prior_utc}; today {len(today)} rows)")


if __name__ == "__main__":
    sys.exit(main())

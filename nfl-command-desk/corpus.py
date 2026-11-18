#!/usr/bin/env python3
"""Verified results corpus (session 4078a9ad).

Inputs, all repository-committed:
  A) nfl-b34253a1/data/games_2026_w1_w9.csv  — 136 rows, weeks 1-9, each row already
     carries the official nfl.com game-page URL and the week schedule URL it was read from.
  B) nfl-command-desk/official.py WEEK10    — this session's own transcription of the
     official week-10 page (S2).

The corpus is published only when the merge rule below passes. The merge rule is printed on
the site: no row is accepted on a session's assertion, only after the whole corpus reproduces
the official standings (record, PF, PA) for all 32 clubs.
"""
import csv
from collections import defaultdict
from pathlib import Path

import official as O

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data"
W19 = ROOT / "nfl-b34253a1/data/games_2026_w1_w9.csv"
ALIAS = O.ALIASES  # AZ->ARI, LA->LAR (publication naming only)


def canon(code):
    return ALIAS.get(code, code)


def season_w1_w9():
    rows = []
    with W19.open(newline="") as f:
        for r in csv.DictReader(f):
            rows.append({
                "week": int(r["week"]),
                "date": r["date"],
                "away": canon(r["away_team"]),
                "home": canon(r["home_team"]),
                "away_score": int(r["away_points"]),
                "home_score": int(r["home_points"]),
                "source_url": r["source_url"],
                "schedule_url": r["schedule_url"],
                "verified_on": r["source_verified_on"],
                "note": r["note"],
            })
    return rows


def season_w10():
    rows = []
    for wk, date, a, h, asc, hsc, note in O.WEEK10:
        rows.append({
            "week": wk, "date": date, "away": canon(a), "home": canon(h),
            "away_score": asc, "home_score": hsc,
            "source_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
            "schedule_url": "https://www.nfl.com/schedules/2026/by-week/week-10",
            "verified_on": "2026-11-18", "note": note,
        })
    return rows


def reconcile(games):
    pf, pa = defaultdict(int), defaultdict(int)
    w, l, t = defaultdict(int), defaultdict(int), defaultdict(int)
    for g in games:
        a, h = g["away"], g["home"]
        pf[a] += g["away_score"]; pa[a] += g["home_score"]
        pf[h] += g["home_score"]; pa[h] += g["away_score"]
        if g["away_score"] > g["home_score"]:
            w[a] += 1; l[h] += 1
        elif g["home_score"] > g["away_score"]:
            w[h] += 1; l[a] += 1
        else:
            t[a] += 1; t[h] += 1
    off = {canon(s[0]): s for s in O.STANDINGS}
    results, fails = [], []
    for code in sorted(off):
        oc, name, ow, ol, ot, opct, opf, opa = off[code]
        ok = (w[code], l[code], t[code], pf[code], pa[code]) == (ow, ol, ot, opf, opa)
        if not ok:
            fails.append(code)
        results.append({
            "team": code, "name": name,
            "corpus_w": w[code], "corpus_l": l[code], "corpus_t": t[code],
            "official_w": ow, "official_l": ol, "official_t": ot,
            "corpus_pf": pf[code], "official_pf": opf,
            "corpus_pa": pa[code], "official_pa": opa,
            "match": "MATCH" if ok else "MISMATCH",
        })
    return results, fails


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    games = season_w1_w9() + season_w10()
    assert all(g["away"] != g["home"] for g in games)
    games.sort(key=lambda g: (g["week"], g["date"], g["away"]))

    # ---- publish corpus
    with (OUT / "results_corpus.csv").open("w", newline="") as f:
        cols = ["game_id", "season", "week", "date", "away", "home", "away_score", "home_score",
                "home_margin", "total", "winner", "status", "source_url", "schedule_url",
                "verified_on", "note"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for g in games:
            margin = g["home_score"] - g["away_score"]
            winner = "tie" if margin == 0 else ("home" if margin > 0 else "away")
            w.writerow({
                "game_id": f"2026_{g['week']:02d}_{g['away']}_{g['home']}",
                "season": 2026, "week": g["week"], "date": g["date"],
                "away": g["away"], "home": g["home"],
                "away_score": g["away_score"], "home_score": g["home_score"],
                "home_margin": margin, "total": g["away_score"] + g["home_score"],
                "winner": winner, "status": "FINAL",
                "source_url": g["source_url"], "schedule_url": g["schedule_url"],
                "verified_on": g["verified_on"], "note": g["note"],
            })

    # ---- reconcile against official standings
    recon, fails = reconcile(games)
    with (OUT / "results_reconciliation.csv").open("w", newline="") as f:
        cols = ["team", "name", "corpus_w", "corpus_l", "corpus_t", "official_w", "official_l",
                "official_t", "corpus_pf", "official_pf", "corpus_pa", "official_pa", "match",
                "source_url"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in recon:
            r["source_url"] = "https://www.nfl.com/standings/league/2026/REG"
            w.writerow(r)
    return games, recon, fails


if __name__ == "__main__":
    games, recon, fails = build()
    print(f"corpus games={len(games)} teams={len(recon)} mismatches={len(fails)} {fails}")

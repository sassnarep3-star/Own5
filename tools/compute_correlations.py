#!/usr/bin/env python3
"""Compute Pearson correlation values in-repo from the OFFICIAL standings
snapshot (data/standings-2026-wk8.csv, sourced from https://www.nfl.com/standings/
on 2026-11-02). Output: data/correlations.csv.

Every input value is official (nfl.com); the correlation values themselves are
computed here, so the row cites both the input source and this script.
"""
import csv, math, os, datetime

ROOT = os.path.join(os.path.dirname(__file__), "..", "data")
SRC = os.path.join(ROOT, "standings-2026-wk8.csv")
OUT = os.path.join(ROOT, "correlations.csv")

def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x-mx)**2 for x in xs))
    dy = math.sqrt(sum((y-my)**2 for y in ys))
    return num/(dx*dy) if dx and dy else float("nan")

rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
# sanity checks against the official page: NET == PF - PA for every team
for r in rows:
    assert int(r["NET"]) == int(r["PF"]) - int(r["PA"]), r["team"]
    assert abs(float(r["PCT"]) - (int(r["W"]) + 0.5*int(r["T"]))/int(r["GP"])) < 0.001, r["team"]
assert sum(int(r["W"]) for r in rows) == sum(int(r["L"]) for r in rows), "W total must equal L total"

gp  = [int(r["GP"]) for r in rows]
pct = [float(r["PCT"]) for r in rows]
pfg = [int(r["PF"])/int(r["GP"]) for r in rows]
pag = [int(r["PA"])/int(r["GP"]) for r in rows]
netg= [int(r["NET"])/int(r["GP"]) for r in rows]
pf  = [int(r["PF"]) for r in rows]
pa  = [int(r["PA"]) for r in rows]
net = [int(r["NET"]) for r in rows]

pairs = [
    ("points scored per game (PF/G)", pfg, "winning percentage (PCT)", pct),
    ("points allowed per game (PA/G)", pag, "winning percentage (PCT)", pct),
    ("net points per game (NET/G)", netg, "winning percentage (PCT)", pct),
    ("total points for (PF)", pf, "total points against (PA)", pa),
    ("total net points (NET)", net, "winning percentage (PCT)", pct),
    ("points scored per game (PF/G)", pfg, "points allowed per game (PA/G)", pag),
]
SRC_URL = "https://www.nfl.com/standings/"
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["pair_id","metric_x","metric_y","n_teams","pearson_r","input_data","computed_by",
                "input_source_url","computed_on","status"])
    for i, (nx, xs, ny, ys) in enumerate(pairs, 1):
        w.writerow([f"CORR{i:02d}", nx, ny, len(xs), round(pearson(xs, ys), 4),
                    "data/standings-2026-wk8.csv (32 teams, 2026 season through Week 8)",
                    "tools/compute_correlations.py (Pearson r)", SRC_URL, "2026-11-02",
                    "verified inputs (nfl.com); value computed in-repo"])
print("wrote", OUT)
for i, (nx, xs, ny, ys) in enumerate(pairs, 1):
    print(f"CORR{i:02d} r({nx}, {ny}) = {pearson(xs,ys):.4f}  n={len(xs)}")

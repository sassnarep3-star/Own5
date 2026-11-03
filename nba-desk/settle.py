#!/usr/bin/env python3
"""Settle the frozen prospective ledger against OFFICIAL final scores.

Fill `final_home_pts` / `final_away_pts` in data/ledger_2026_11_04_05.csv ONLY from the
nba.com game page named in `result_source_url`. Rows left blank are reported as unsettled
and are never imputed. The own-line columns must not be edited after the first commit
(git history is the timestamp).

    python3 nba-desk/settle.py [ledger.csv]
"""
import csv
import math
import os
import sys
from statistics import mean

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "data", "ledger_2026_11_04_05.csv")


def settle(path=DEFAULT):
    rows = list(csv.DictReader(open(path, newline="")))
    done = [r for r in rows if r["final_home_pts"].strip() != "" and r["final_away_pts"].strip() != ""]
    out = {"games": len(rows), "settled": len(done), "unsettled": len(rows) - len(done)}
    if done:
        em, et, su = [], [], 0
        for r in done:
            hm = int(r["final_home_pts"]) - int(r["final_away_pts"])
            tot = int(r["final_home_pts"]) + int(r["final_away_pts"])
            em.append(float(r["own_home_margin"]) - hm)
            et.append(float(r["own_total"]) - tot)
            su += (float(r["own_home_margin"]) > 0) == (hm > 0)
        out.update({"margin_mae": mean(abs(e) for e in em), "margin_bias": mean(em),
                    "margin_rmse": math.sqrt(mean(e * e for e in em)),
                    "total_mae": mean(abs(e) for e in et), "total_bias": mean(et),
                    "straight_up_correct": su})
    return out


if __name__ == "__main__":
    res = settle(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
    for k, v in res.items():
        print(f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}")
    if res["settled"] < 30:
        print("NOTE: fewer than 30 settled games - accuracy numbers are descriptive only; no strategy can qualify.")

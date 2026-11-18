#!/usr/bin/env python3
"""Derive per-club injury-report COUNTS from every stored raw injury capture (pure function of raw bytes).

Output: own5-hub/captures/injury_counts_daily.csv, one row per (capture, club). No player names.
Re-running it always rewrites the same bytes for the same raw files (deterministic ordering).
"""
import csv, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_injuries import parse_file

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_GLOB = os.path.join(HERE, "captures", "raw", "injuries", "*.html.gz")
OUT = os.path.join(HERE, "captures", "injury_counts_daily.csv")
FIELDS = ["capture_stamp_utc", "club", "player_rows", "rows_with_injury_label", "rows_with_game_status",
          "game_status_out", "game_status_questionable", "game_status_doubtful", "game_status_other"]


def stamp_of(path):
    base = os.path.basename(path)
    return base.replace(".html.gz", "")  # e.g. 20261118T032838Z


def build():
    out_rows = []
    for path in sorted(glob.glob(RAW_GLOB)):
        rows, _ = parse_file(path)
        by = {}
        for r in rows:
            c = by.setdefault(r["team"], dict.fromkeys(FIELDS[2:], 0))
            c["player_rows"] += 1
            c["rows_with_injury_label"] += 1 if r["injuries"] else 0
            gs = r["game_status"]
            c["rows_with_game_status"] += 1 if gs else 0
            key = {"Out": "game_status_out", "Questionable": "game_status_questionable",
                   "Doubtful": "game_status_doubtful"}.get(gs, "game_status_other" if gs else None)
            if key:
                c[key] += 1
        for club in sorted(by):
            out_rows.append({"capture_stamp_utc": stamp_of(path), "club": club, **by[club]})
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)
    return len(out_rows)


if __name__ == "__main__":
    print("rows written:", build())

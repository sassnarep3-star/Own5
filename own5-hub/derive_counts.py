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


CONTENT_OUT = os.path.join(HERE, "captures", "parsed_content_daily.csv")
CONTENT_FIELDS = ["capture_stamp_utc", "raw_sha256", "parsed_rows_sha256", "tables", "rows", "parse_status"]


def build_content():
    """Raw-byte hash AND parsed-content hash per capture. A raw change with an unchanged parsed hash is a
    non-substantive change (for example a random page id), not a roster change.

    A capture whose page no longer parses is recorded with parse_status "failed: <reason>"
    instead of raising: the capture is evidence, and an unparsable page must stay in the
    ledger rather than breaking the whole build (integration repair, 2026-11-19)."""
    import gzip, hashlib, json
    out_rows = []
    for path in sorted(glob.glob(RAW_GLOB)):
        with gzip.open(path, "rb") as f:
            raw = f.read()
        try:
            rows, n_tables = parse_file(path)
        except Exception as e:  # noqa: BLE001 - the failure is recorded, not swallowed
            out_rows.append({"capture_stamp_utc": stamp_of(path),
                             "raw_sha256": hashlib.sha256(raw).hexdigest(),
                             "parsed_rows_sha256": "", "tables": 0, "rows": 0,
                             "parse_status": "failed: " + str(e)[:120]})
            continue
        canon = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
        out_rows.append({"capture_stamp_utc": stamp_of(path), "raw_sha256": hashlib.sha256(raw).hexdigest(),
                         "parsed_rows_sha256": hashlib.sha256(canon).hexdigest(),
                         "tables": n_tables, "rows": len(rows), "parse_status": "ok"})
    with open(CONTENT_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CONTENT_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)
    return len(out_rows)


def build():
    out_rows = []
    for path in sorted(glob.glob(RAW_GLOB)):
        try:
            rows, _ = parse_file(path)
        except Exception:  # noqa: BLE001 - a capture that does not parse contributes no club counts
            continue
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
    print("rows written:", build(), "content rows:", build_content())

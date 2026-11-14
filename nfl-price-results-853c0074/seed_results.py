#!/usr/bin/env python3
"""Normalize the repository's already sourced NFL results to a keyed feed."""
from __future__ import annotations
import csv
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "nfl-b34253a1/data/games_2026_w1_w9.csv"
DEST = ROOT / "data/official_results.csv"
FIELDS = ["event_id", "week", "date", "away_team", "home_team", "away_points", "home_points", "status", "official_source_url", "source_verified_on", "source_note"]

def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    normalized=[]
    for row in rows:
        url=row.get("source_url", "")
        if row.get("status") != "FINAL" or not row.get("away_points", "").isdigit() or not row.get("home_points", "").isdigit() or not url.startswith("https://www.nfl.com/"):
            raise SystemExit("source result row failed FINAL/score/official NFL URL checks")
        eid=f"2026-W{row['week']}-{row['away_team']}-{row['home_team']}"
        normalized.append({"event_id":eid,"week":row["week"],"date":row["date"],"away_team":row["away_team"],"home_team":row["home_team"],"away_points":row["away_points"],"home_points":row["home_points"],"status":row["status"],"official_source_url":url,"source_verified_on":row.get("source_verified_on", ""),"source_note":row.get("note", "")})
    DEST.parent.mkdir(parents=True, exist_ok=True)
    with DEST.open("w", newline="", encoding="utf-8") as stream:
        writer=csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader(); writer.writerows(normalized)
    print(f"Wrote {len(normalized)} source-linked official NFL result rows to {DEST.relative_to(ROOT)}")
if __name__ == "__main__": main()

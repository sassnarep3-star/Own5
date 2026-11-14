#!/usr/bin/env python3
"""Preserve existing linked quotes as unclassified observations, never open/close."""
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/"nfl-b34253a1/data/market_quotes_2026_w10.csv"
DEST=ROOT/"data/unclassified_market_quotes.csv"
FIELDS=["week","date","away_team","home_team","book","away_spread","away_spread_american_odds","home_spread","home_spread_american_odds","total_points","over_american_odds","under_american_odds","away_moneyline_american","home_moneyline_american","retrieved_date","retrieved_time_utc","source_url","board_url","timestamp_status","price_value_status","flag_id"]
def main():
    with SOURCE.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    for row in rows:
        if not row.get("source_url","").startswith("https://") or row.get("retrieved_time_utc",""):
            raise SystemExit("quote row is missing HTTPS provenance or violates date-only source limitation")
        row["price_value_status"]="UNVERIFIED_PRICE_BLANK"
        row["flag_id"]="F07" if "34118102" in row.get("source_url", "") else "F01"
        # Do not republish numeric quote cells without a retained snapshot or a
        # currently accessible official quote page. Preserve provenance only.
        for key in ("away_spread","away_spread_american_odds","home_spread","home_spread_american_odds","total_points","over_american_odds","under_american_odds","away_moneyline_american","home_moneyline_american"):
            row[key]=""
        row={key: row.get(key, "") for key in FIELDS}
    with DEST.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator="\n");w.writeheader();w.writerows(rows)
    print(f"Wrote {len(rows)} legacy quotes as explicitly unclassified observations")
if __name__=="__main__":main()

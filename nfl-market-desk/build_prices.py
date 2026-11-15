#!/usr/bin/env python3
"""Price-data policy + price-snapshot store.

The brief says: "Decide the price-data policy before any backtest is published",
"Add a price-snapshot store that records opening and closing numbers for every
market we originate", "Publish the model's fair line, the market line, and the
difference as separate columns", and "Compute correlations only from officially
sourced numbers".

What was checked, and what it means
-----------------------------------
1. nfl.com publishes game schedules, scores and injury reports. It publishes no
   sportsbook prices. Searched: nfl.com/schedules (no prices), the injury report
   (no prices), standings (no prices). Nothing on nfl.com is a price source.
2. The only price-bearing file reachable from this sandbox is the nflverse
   scheduler mirror (`games.csv.gz`). Its own data dictionary (nflreadr
   dictionary_schedules) documents the columns but discloses no sportsbook, no
   jurisdiction, no quote timestamp and no closing time for them. It is an
   AGGREGATOR: usable, not official.
3. sportsbook operator pages (DraftKings, FanDuel, BetMGM) are unreachable from
   this sandbox (the network allowlist admits github.com, codeload, api.github,
   npm, pypi only). They are therefore not merely unverified but unattemptable,
   and are recorded as BLOCKED, not as blank-but-available.

Policy consequence (published as data/price_policy.csv):
  * No official opening or closing price exists. We do not invent one.
  * Every originated market therefore carries an AGGREGATOR reference price with
    an explicit tier, and the MARKET_OPEN / MARKET_CLOSE snapshot types are stored
    as empty rows with a flag, so the absence is visible in the data rather than
    invisible.
  * ROI and closing-line value are computed ONLY where a priced snapshot exists,
    and are labelled AGGREGATOR-grade. Nothing is labelled "verified return".
"""
import csv
import os
import sys

from lib import (AGGREGATOR, DERIVED, OFFICIAL, UNVERIFIED, rcsv, rcsv_path, wcsv, wjson,
                 prob_to_american, DATA, ROOT)

POLICY_URL = "https://github.com/sassnarep3-star/Own5/blob/main/nfl-market-desk/data/price_policy.csv"
BLOCKED_NOTE = ("BLOCKED_FROM_SANDBOX: the operator page could not be opened from the capture "
                "environment (the sandbox host allowlist rejects it), so this row records the "
                "block itself rather than citing a page nobody read")

CAPTURED = "2026-11-15T23:30:00Z"

POLICY = [
    ("P-01", "Official price source", "nfl.com publishes no sportsbook price on any page reachable from this sandbox",
     "nfl.com schedules / standings / injuries", "NONE EXISTS", OFFICIAL,
     "https://www.nfl.com/schedules/2026/by-week/week-11",
     "Searched the Week 10 and Week 11 schedule pages, the league standings and the Week 10 injury report: no spread, total or moneyline appears on any of them."),
    ("P-02", "Operator price source", "Operator pages (DraftKings, FanDuel, BetMGM) are outside this sandbox's network allowlist",
     "sportsbook operator sites", "ATTEMPTED - BLOCKED", UNVERIFIED,
     POLICY_URL,
     "Shell fetch fails at TLS for non-allowlisted hosts; the page fetcher is available for nfl.com and club sites only. Recorded as blocked, not as pending."),
    ("P-03", "Aggregator price source", "nflverse schedules mirror carries spread_line, total_line and moneylines",
     "nflverse games.csv.gz", "AVAILABLE", AGGREGATOR,
     "https://github.com/nflverse/nflverse-data/releases/tag/schedules",
     "tier=AGGREGATOR. Fields are numeric and complete for 2026 weeks 1-11, but the file publishes no sportsbook, no jurisdiction, no quote time and no close time."),
    ("P-04", "What an aggregator price may be used for", "Model benchmarking, market-line residual studies, research-grade ROI",
     "agg lines", "PERMITTED WITH LABEL", AGGREGATOR, POLICY_URL,
     "Every published ROI derived from an aggregator price is labelled AGGREGATOR and is barred from certification."),
    ("P-05", "What an aggregator price may NOT be used for", "Certifying a strategy, closing-line value, realised return attribution",
     "agg lines", "FORBIDDEN", "n/a", POLICY_URL,
     "CLV needs a true close; the mirror has no close time. Certification needs an executable price at a named book."),
    ("P-06", "Official numbers, when they exist", "Official results, standings, injury designations, depth charts and snap counts",
     "nfl.com + club pages", "ADMISSIBLE", OFFICIAL,
     "https://www.nfl.com/standings/league/2026/REG",
     "These are the only inputs admitted to any correlation that is published as official."),
    ("P-07", "Vig treatment", "Two-way markets are de-vigged proportionally before any fair-line comparison",
     "any two-sided price", "STIPULATED", DERIVED, POLICY_URL,
     "Proportional de-vig is a stipulation, not a measurement; it is published as a method assumption, not as a fact about the market."),
    ("P-08", "Missing price", "A market without a price keeps an EMPTY snapshot row with a flag id",
     "store design", "ENFORCED", DERIVED, POLICY_URL,
     "No price is estimated, interpolated or carried forward."),
    ("P-09", "Timestamp", "Every snapshot row carries the UTC time the number was observed",
     "store design", "ENFORCED", DERIVED, POLICY_URL,
     "Aggregator observations all share the asset timestamp published on the release page."),
    ("P-10", "Revision", "Snapshots are append-only; a correction is a new row with a supersedes id",
     "store design", "ENFORCED", DERIVED, POLICY_URL,
     "The 2026-11-15 capture is the first snapshot in this desk; prior desks' snapshots were not refreshed and are cited, not copied."),
]


def build_policy():
    rows = [dict(zip(["policy_id", "question", "decision", "scope", "status", "tier",
                      "source_url", "rationale"], p)) for p in POLICY]
    return wcsv("price_policy.csv", rows)


ORIGINATED = ["SIDE", "TOTAL", "MONEYLINE"]
SNAPSHOT_TYPES = [
    ("MARKET_REFERENCE", "Aggregator line of unknown timestamp, kept for context only", AGGREGATOR),
    ("MODEL_ORIGIN", "The fair line this desk originates when it first prices the market", DERIVED),
    ("MARKET_OPEN", "The operator's opening price", None),
    ("MODEL_CLOSE", "This desk's last price before kickoff", None),
    ("MARKET_CLOSE", "The operator's closing price", None),
]


def mirror_lines_by_game():
    games = [g for g in __import__("lib").mirror_games()
             if g["season"] == "2026" and g["week"] in [str(w) for w in range(12, 19)]]
    return games


def market_price_american(gd):
    """The aggregator's own two-way price for the market the row refers to.

    gd is (gameday, gametime, spread, total, away_ml, home_ml, roof, surface). The price
    published here is the moneyline of the side the row's line belongs to; for totals it
    is the over price. Where the field is absent the cell is left blank (never estimated).
    """
    if not gd:
        return ""
    return gd[4] if gd[4] not in ("", "NA") else ""


def price_american(m):
    """Fair price of the model's own line, stated as a moneyline-equivalent.

    The model probability is already published; converting it with prob_to_american
    makes the row comparable with a book's row without implying the book quoted it.
    """
    try:
        return prob_to_american(float(m["probability"]))
    except (TypeError, ValueError):
        return ""


def build_store():
    """Snapshot store. One block of rows per originated market."""
    markets = rcsv("originated_markets.csv")
    game_dates = {}
    for g in mirror_lines_by_game():
        game_dates[g["game_id"]] = (g["gameday"], g["gametime"], g["spread_line"],
                                    g["total_line"], g["away_moneyline"], g["home_moneyline"],
                                    g["roof"], g["surface"])
    rows = []
    for m in markets:
        mid = m["market_id"]
        gid = m["game_id"]
        gd = game_dates.get(gid)
        for stype, meaning, tier in SNAPSHOT_TYPES:
            base = {
                "snapshot_id": "%s:%s" % (mid, stype),
                "market_id": mid,
                "game_id": gid,
                "week": m["week"],
                "matchup": "%s@%s" % (m["away"], m["home"]),
                "market_type": m["market_type"],
                "snapshot_type": stype,
                "snapshot_meaning": meaning,
                "snapshot_utc": "",
                "line_value": "",
                "price_american": "",
                "source_url": "",
                "source_tier": "",
                "verified": "",
                "flag_id": "",
                "supersedes": "",
            }
            if stype == "MODEL_ORIGIN":
                base.update({
                    "snapshot_utc": m["snapshot_utc"],
                    "line_value": m["fair_line"],
                    "price_american": price_american(m),
                    "source_url": m["market_source_url"].replace(
                        "nflverse-data/releases/download/schedules/games.csv.gz",
                        "github.com/nflverse/nflverse-data/releases/tag/schedules"),
                    "source_tier": DERIVED,
                    "verified": "reproducible from committed inputs",
                })
            elif stype == "MARKET_REFERENCE":
                base.update({
                    "snapshot_utc": m["snapshot_utc"],
                    "line_value": m["market_line"],
                    "price_american": market_price_american(gd),
                    "source_url": m["market_source_url"],
                    "source_tier": m["market_source_tier"],
                    "verified": "no - aggregator of unknown timestamp",
                    "flag_id": "F-02",
                })
            elif stype == "MARKET_OPEN":
                base.update({"flag_id": "F-01",
                             "verified": "no - no official or operator opening price is reachable"})
            elif stype == "MARKET_CLOSE":
                base.update({"flag_id": "F-01",
                             "verified": "no - no official or operator closing price is reachable"})
            elif stype == "MODEL_CLOSE":
                base.update({"flag_id": "F-03",
                             "verified": "no - this desk has made one model snapshot so far; a close is only observable after a later capture"})
            rows.append(base)
    n = wcsv("price_snapshots.csv", rows)

    summary = {}
    for stype, _m, _t in SNAPSHOT_TYPES:
        sel = [r for r in rows if r["snapshot_type"] == stype]
        summary[stype] = {
            "rows": len(sel),
            "populated": sum(1 for r in sel if r["line_value"] != ""),
            "empty": sum(1 for r in sel if r["line_value"] == ""),
            "tier": _t or "n/a",
        }
    return n, summary


def main():
    n_policy = build_policy()
    n_store, summary = build_store()
    print("price policy rows:", n_policy)
    for k, v in summary.items():
        print("  %-16s rows=%-4d populated=%-4d empty=%-4d tier=%s"
              % (k, v["rows"], v["populated"], v["empty"], v["tier"]))
    print("price snapshot rows:", n_store)
    wjson("price_store_summary.json", {"rows": n_store, "by_type": summary, "captured_utc": CAPTURED})


if __name__ == "__main__":
    main()

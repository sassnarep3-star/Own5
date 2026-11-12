#!/usr/bin/env python3
"""Fetch the official/primary inputs used by the NFL Decision Desk.

Two classes of input are retrieved, each recorded with full provenance
(URL, HTTP status, SHA-256, byte count, UTC timestamp) in
``data/decision-desk/raw/provenance.json``:

1. ``nflverse`` data mirrors (github.com/nflverse/nflverse-data releases).
   nflverse is an *aggregator*: it re-publishes data derived from official
   NFL sources (NFL injury reports, official gamebooks/snap counts).  It is
   therefore labelled AGGREGATOR everywhere and never called "official".

2. ``www.nfl.com`` pages (injury report, schedule, standings).  These are the
   OFFICIAL league pages.  The raw HTML is written to ``.work/official/`` and
   uploaded as a build artifact; only the parsed, per-row-sourced CSVs are
   committed.

The script is stdlib-only and is meant to run on a GitHub Actions runner
(the sandbox that develops this repo can only reach github.com; runners have
full egress).  It never invents a value: a failed fetch writes a *status*
row, not a placeholder fact.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(ROOT, "data", "decision-desk", "raw")
WORK = os.path.join(ROOT, ".work", "official")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")

NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"

# (release, asset) -> committed as raw/<asset>.gz
NFLVERSE_ASSETS = [
    ("injuries", "injuries_2026.csv.gz"),
    ("injuries", "injuries_2025.csv.gz"),
    ("injuries", "injuries_2024.csv.gz"),
    ("injuries", "injuries_2023.csv.gz"),
    ("snap_counts", "snap_counts_2026.csv.gz"),
    ("snap_counts", "snap_counts_2025.csv.gz"),
    ("snap_counts", "snap_counts_2024.csv.gz"),
    ("stats_player", "stats_player_week_2026.csv.gz"),
    ("stats_player", "stats_player_week_2025.csv.gz"),
    ("schedules", "games.csv.gz"),
]

OFFICIAL_PAGES = [
    ("injury_report_wk10", "https://www.nfl.com/injuries/"),
    ("schedule_wk10", "https://www.nfl.com/schedules/2026/by-week/week-10"),
    ("standings_reg_2026", "https://www.nfl.com/standings/league/2026/REG"),
]


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get(url: str, tries: int = 3) -> tuple[int, bytes]:
    last = (0, b"")
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,csv,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:  # keep the status, never guess content
            last = (e.code, e.read() or b"")
        except Exception as e:  # noqa: BLE001 - network variance is expected
            last = (0, str(e).encode())
        time.sleep(2 + 2 * attempt)
    return last


def main() -> int:
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    prov = {"retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "assets": [], "pages": []}

    for release, asset in NFLVERSE_ASSETS:
        url = f"{NFLVERSE}/{release}/{asset}"
        status, body = get(url)
        entry = {"release": release, "asset": asset, "url": url,
                 "http_status": status, "bytes": len(body), "sha256": sha256(body)}
        if status == 200 and body:
            with open(os.path.join(RAW, asset), "wb") as fh:
                fh.write(body)
            entry["committed_as"] = f"data/decision-desk/raw/{asset}"
            try:
                with gzip.open(os.path.join(RAW, asset), "rt", encoding="utf-8") as fh:
                    entry["header"] = fh.readline().strip()
            except Exception as exc:  # noqa: BLE001
                entry["header_error"] = str(exc)
        prov["assets"].append(entry)
        print(f"{asset}: http={status} bytes={len(body)}")

    for name, url in OFFICIAL_PAGES:
        status, body = get(url)
        path = os.path.join(WORK, f"{name}.html")
        if status == 200 and body:
            with open(path, "wb") as fh:
                fh.write(body)
        prov["pages"].append({"name": name, "url": url, "http_status": status,
                              "bytes": len(body), "sha256": sha256(body),
                              "saved": os.path.basename(path)})
        print(f"{name}: http={status} bytes={len(body)}")

    with open(os.path.join(RAW, "provenance.json"), "w", encoding="utf-8") as fh:
        json.dump(prov, fh, indent=2, sort_keys=True)
        fh.write("\n")

    ok_assets = sum(1 for a in prov["assets"] if a["http_status"] == 200)
    ok_pages = sum(1 for p in prov["pages"] if p["http_status"] == 200)
    print(f"OK assets={ok_assets}/{len(prov['assets'])} pages={ok_pages}/{len(prov['pages'])}")
    # A partial failure is data, not a crash: downstream code flags the gap.
    return 0



if __name__ == "__main__":
    sys.exit(main())

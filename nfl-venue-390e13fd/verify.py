#!/usr/bin/env python3
"""Fail-closed verification for the NFL Venue & Schedule-Announcement desk (390e13fd).

Exit 0 only when every check passes. Checks are pure functions of the
committed files: no network, no git, no clock.

Run: python3 nfl-venue-390e13fd/verify.py
"""
import csv
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

DESK = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DATA = os.path.join(DESK, "data")
RAW = os.path.join(DESK, "raw")

OFFICIAL_HOSTS = {"www.nfl.com", "nfl.com"}
ALLOWED_EXTERNAL_HOSTS = OFFICIAL_HOSTS | {"github.com", "sassnarep3-star.github.io"}

REQUIRED_COLUMNS = {
    "venues.csv": ["game_slug", "away_team", "away_code", "home_team", "home_code",
                   "weekday", "date_2026", "kickoff_as_printed", "network_as_printed",
                   "venue_location_as_printed", "venue_stadium_as_printed",
                   "official_game_url", "source_url", "raw_file", "read_utc", "venue_status"],
    "byes.csv": ["team_name", "code", "source_url", "read_utc"],
    "schedule_announcement.csv": ["item_id", "announcement_item",
                                  "announcement_date_as_published", "what_it_says",
                                  "official_url", "source_class", "raw_file", "read_utc"],
    "sources.csv": ["source_id", "title", "url", "source_class", "supports",
                    "read_utc", "raw_file", "caveat"],
    "flagged.csv": ["flag_id", "severity", "title", "detail", "evidence_url",
                    "source_class", "status"],
}

PAGES = ["index.html", "schedule.html", "announcement.html", "sources.html",
         "flagged.html", "summary.html"]


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def is_https_allowed(url, hosts=ALLOWED_EXTERNAL_HOSTS):
    p = urlparse(url)
    return p.scheme == "https" and p.hostname in hosts


def check_columns():
    fails = []
    for name, cols in REQUIRED_COLUMNS.items():
        path = os.path.join(DATA, name)
        if not os.path.isfile(path):
            fails.append(f"missing file {name}")
            continue
        with open(path, encoding="utf-8", newline="") as fh:
            header = next(csv.reader(fh))
        missing = [c for c in cols if c not in header]
        if missing:
            fails.append(f"{name}: missing columns {missing}")
    return fails


def check_venues():
    fails = []
    rows = load("venues.csv")
    if len(rows) != 13:
        fails.append(f"venues.csv: expected 13 fixtures, found {len(rows)}")
    seen = set()
    for r in rows:
        slug = r["game_slug"]
        if slug in seen:
            fails.append(f"venues.csv: duplicate game_slug {slug}")
        seen.add(slug)
        for field in ("venue_location_as_printed", "venue_stadium_as_printed"):
            if not r[field].strip():
                fails.append(f"venues.csv {slug}: blank {field} (must be blank+flagged, not silently empty)")
        if r["venue_status"] != "VERIFIED":
            fails.append(f"venues.csv {slug}: venue_status {r['venue_status']!r} (expected VERIFIED)")
        if not is_https_allowed(r["official_game_url"], OFFICIAL_HOSTS):
            fails.append(f"venues.csv {slug}: official_game_url not an official https URL: {r['official_game_url']}")
        if not is_https_allowed(r["source_url"], OFFICIAL_HOSTS):
            fails.append(f"venues.csv {slug}: source_url not an official https URL: {r['source_url']}")
        raw_path = os.path.join(DESK, r["raw_file"])
        if not os.path.isfile(raw_path):
            fails.append(f"venues.csv {slug}: raw file missing: {r['raw_file']}")
            continue
        raw = open(raw_path, encoding="utf-8").read()
        if f"LocationLOCATION{r['venue_location_as_printed']}" not in raw:
            fails.append(f"venues.csv {slug}: raw extract does not print the CSV location {r['venue_location_as_printed']!r}")
        if f"StadiumSTADIUM{r['venue_stadium_as_printed']}" not in raw:
            fails.append(f"venues.csv {slug}: raw extract does not print the CSV stadium {r['venue_stadium_as_printed']!r}")
        if r["official_game_url"] not in raw:
            fails.append(f"venues.csv {slug}: raw extract does not record the source URL")
    return fails


def check_announcement():
    fails = []
    rows = load("schedule_announcement.csv")
    if not rows:
        fails.append("schedule_announcement.csv: no rows")
    for r in rows:
        if not r["announcement_date_as_published"].strip():
            fails.append(f"schedule_announcement.csv {r['item_id']}: blank announcement date")
        if not is_https_allowed(r["official_url"], OFFICIAL_HOSTS):
            fails.append(f"schedule_announcement.csv {r['item_id']}: official_url not official: {r['official_url']}")
        raw_path = os.path.join(DESK, r["raw_file"])
        if not os.path.isfile(raw_path):
            fails.append(f"schedule_announcement.csv {r['item_id']}: raw file missing: {r['raw_file']}")
    texts = " ".join(r["what_it_says"] for r in rows)
    if "May 14" not in texts:
        fails.append("schedule_announcement.csv: no announcement item records the May 14 release date")
    return fails


def check_byes():
    fails = []
    rows = load("byes.csv")
    if len(rows) != 6:
        fails.append(f"byes.csv: expected 6 bye teams, found {len(rows)}")
    for r in rows:
        if not is_https_allowed(r["source_url"], OFFICIAL_HOSTS):
            fails.append(f"byes.csv {r['team_name']}: source_url not official: {r['source_url']}")
    return fails


def check_sources_and_flags():
    fails = []
    for r in load("sources.csv"):
        if not is_https_allowed(r["url"], OFFICIAL_HOSTS):
            fails.append(f"sources.csv {r['source_id']}: url not official: {r['url']}")
        if not os.path.isfile(os.path.join(DESK, r["raw_file"])):
            fails.append(f"sources.csv {r['source_id']}: raw file missing: {r['raw_file']}")
    for r in load("flagged.csv"):
        if not is_https_allowed(r["evidence_url"], OFFICIAL_HOSTS):
            fails.append(f"flagged.csv {r['flag_id']}: evidence_url not official: {r['evidence_url']}")
    return fails


class LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href":
                    self.links.append(value)


def check_pages():
    fails = []
    for page in PAGES:
        path = os.path.join(DESK, page)
        if not os.path.isfile(path):
            fails.append(f"missing page {page}")
            continue
        parser = LinkCollector()
        parser.feed(open(path, encoding="utf-8").read())
        for href in parser.links:
            if href.startswith("#"):
                continue
            if href.startswith("http"):
                if not is_https_allowed(href):
                    fails.append(f"{page}: external link not on an allowed https host: {href}")
                continue
            target = os.path.normpath(os.path.join(DESK, href.split("#")[0]))
            if not os.path.isfile(target):
                fails.append(f"{page}: broken internal link: {href}")
    return fails


def main():
    checks = [
        ("columns", check_columns()),
        ("venues", check_venues()),
        ("announcement", check_announcement()),
        ("byes", check_byes()),
        ("sources_and_flags", check_sources_and_flags()),
        ("pages_and_links", check_pages()),
    ]
    total_fail = 0
    for name, fails in checks:
        if fails:
            total_fail += len(fails)
            for f in fails:
                print(f"FAIL [{name}] {f}")
        else:
            print(f"PASS [{name}]")
    if total_fail:
        print(f"\n{total_fail} check(s) failed.")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

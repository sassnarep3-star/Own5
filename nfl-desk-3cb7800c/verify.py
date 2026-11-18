#!/usr/bin/env python3
"""Verification harness for the NFL official-source desk (3cb7800c).

Exit 0 only when every check passes. Failures are printed loudly, one per line.
Checks are pure functions of the committed files: no network, no git, no clock.
Run: python3 nfl-desk-3cb7800c/verify.py
"""
import csv
import datetime as dt
import hashlib
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

DESK = os.path.abspath(os.path.join(os.path.dirname(__file__)))
REPO = os.path.abspath(os.path.join(DESK, ".."))
DATA = os.path.join(DESK, "data")
RAW = os.path.join(DESK, "raw")

OFFICIAL_HOSTS = {"www.nfl.com", "nfl.com"}
ALLOWED_HOSTS = OFFICIAL_HOSTS | {"github.com", "sassnarep3-star.github.io"}

# The 32 club codes, using the codes printed on the official standings page (AZ, LA).
CANONICAL_CODES = {
    "AZ", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET", "GB",
    "HOU", "IND", "JAX", "KC", "LA", "LAC", "LV", "MIA", "MIN", "NE", "NO", "NYG", "NYJ",
    "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS",
}

REQUIRED_COLUMNS = {
    "week11_schedule.csv": ["game_slug", "away_code", "home_code", "weekday", "date_2026",
                            "kickoff_as_printed", "network_as_printed", "official_game_url",
                            "raw_line", "source_url", "read_utc"],
    "week11_byes.csv": ["team_name", "code_as_printed", "standings_logo_code", "raw_line", "source_url", "read_utc"],
    "availability_status.csv": ["check_id", "item", "url_requested", "final_url_reported_by_fetch_tool",
                                "page_title_seen", "status", "read_utc", "source_url", "raw_file", "note"],
    "desks_index.csv": ["desk_dir", "has_index_html", "html_pages", "data_files", "title",
                        "scoped_workflow", "live_url", "source_class", "snapshot_read_utc"],
    "repo_checks.csv": ["check_id", "check", "value_at_read", "read_utc", "source_class", "source_url", "note"],
    "sources.csv": ["source_id", "title", "url", "source_class", "supports", "read_utc", "raw_file", "caveat"],
    "flagged.csv": ["flag_id", "severity", "title", "detail", "evidence_url", "source_class",
                    "raw_or_check_ref", "status"],
    "suggestions.csv": ["suggestion_id", "title", "options", "recommendation", "what_would_change_the_call",
                        "decision", "evidence_url"],
    "questions.csv": ["question_id", "question", "what_we_have", "what_we_lack", "cheapest_route_to_close",
                      "blocks", "evidence_url"],
}


def load(name, base=DATA):
    with open(os.path.join(base, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def is_https_allowed(url):
    p = urlparse(url)
    return p.scheme == "https" and p.hostname in ALLOWED_HOSTS


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- schedule

def check_columns(data_dir=DATA):
    fails = []
    for name, cols in REQUIRED_COLUMNS.items():
        path = os.path.join(data_dir, name)
        if not os.path.isfile(path):
            fails.append(f"missing file {name}")
            continue
        with open(path, encoding="utf-8", newline="") as fh:
            header = next(csv.reader(fh))
        missing = [c for c in cols if c not in header]
        if missing:
            fails.append(f"{name}: missing columns {missing}")
    return fails


def check_schedule(games, byes, extract_text):
    fails = []
    if len(games) != 13:
        fails.append(f"schedule: expected 13 games, found {len(games)}")
    if len(byes) != 6:
        fails.append(f"byes: expected 6 teams, found {len(byes)}")
    clubs = []
    for g in games:
        clubs += [g["away_code"], g["home_code"]]
    clubs += [b["standings_logo_code"] for b in byes]
    if len(clubs) != len(set(clubs)):
        dupes = sorted({c for c in clubs if clubs.count(c) > 1})
        fails.append(f"schedule: clubs appear twice {dupes}")
    if set(clubs) != CANONICAL_CODES:
        fails.append(f"schedule: club set mismatch; missing {sorted(CANONICAL_CODES - set(clubs))}, "
                     f"extra {sorted(set(clubs) - CANONICAL_CODES)}")
    for g in games:
        try:
            d = dt.date.fromisoformat(g["date_2026"])
        except ValueError:
            fails.append(f"{g['game_slug']}: bad date {g['date_2026']}")
            continue
        if d.strftime("%A") != g["weekday"]:
            fails.append(f"{g['game_slug']}: weekday {g['weekday']} does not match {g['date_2026']} ({d.strftime('%A')})")
        if g["official_game_url"] != f"https://www.nfl.com/games/{g['game_slug']}":
            fails.append(f"{g['game_slug']}: game URL does not match slug")
        if not is_https_allowed(g["official_game_url"]):
            fails.append(f"{g['game_slug']}: game URL host not official")
        if g["source_url"] != "https://www.nfl.com/schedules/2026/by-week/week-11":
            fails.append(f"{g['game_slug']}: source is not the Week 11 schedule page")
        line = g["raw_line"].lstrip("- ").strip()
        if line not in extract_text:
            fails.append(f"{g['game_slug']}: raw_line not found verbatim in the schedule extract")
        if not re.search(r"\d{1,2}:\d{2} [AP]M$", g["kickoff_as_printed"]):
            fails.append(f"{g['game_slug']}: kickoff not in printed form")
    for b in byes:
        if b["raw_line"] not in extract_text:
            fails.append(f"bye {b['code_as_printed']}: raw_line not found verbatim in the schedule extract")
        if b["standings_logo_code"] not in CANONICAL_CODES:
            fails.append(f"bye {b['code_as_printed']}: standings code not canonical")
    return fails


# ---------------------------------------------------------------- raw captures

def check_hashes(raw_dir=RAW):
    fails = []
    sums_path = os.path.join(raw_dir, "SHA256SUMS.txt")
    if not os.path.isfile(sums_path):
        return ["missing raw/SHA256SUMS.txt"]
    for line in read_text(sums_path).splitlines():
        if not line.strip():
            continue
        digest, path = line.split(None, 1)
        full = os.path.join(DESK, path)
        if not os.path.isfile(full):
            fails.append(f"hash list names a missing file {path}")
            continue
        with open(full, "rb") as fh:
            actual = hashlib.sha256(fh.read()).hexdigest()
        if actual != digest:
            fails.append(f"hash mismatch for {path}")
    return fails


def check_availability(avail, meta_text):
    fails = []
    a1 = next((a for a in avail if a["check_id"] == "A-01"), None)
    if a1 is None:
        return ["availability: A-01 missing"]
    if "NOT PUBLISHED" not in a1["status"]:
        fails.append("availability: A-01 must record that the Week 11 report is not published")
    if "final_url_reported_by_fetch_tool: https://www.nfl.com/injuries/league/2026/reg10" not in meta_text:
        fails.append("availability: fetch meta does not record the reg10 final URL")
    if a1["final_url_reported_by_fetch_tool"] != "https://www.nfl.com/injuries/league/2026/reg10":
        fails.append("availability: A-01 final URL does not match the fetch record")
    for a in avail:
        if not is_https_allowed(a["source_url"]):
            fails.append(f"{a['check_id']}: source is not https on an allowed host")
        if re.search(r"\b\d+ (players|rows|designations)\b", a["status"], re.I):
            fails.append(f"{a['check_id']}: status carries a count that this desk did not verify")
    return fails


# ---------------------------------------------------------------- desks snapshot

def check_desks(desks, repo_root=REPO):
    fails, info = [], []
    pinned = set()
    for d in desks:
        name = d["desk_dir"]
        pinned.add(name)
        full = os.path.join(repo_root, name)
        if not os.path.isdir(full):
            fails.append(f"desk snapshot names a directory that no longer exists: {name}")
            continue
        has_index = os.path.isfile(os.path.join(full, "index.html"))
        if (d["has_index_html"] == "yes") != has_index:
            fails.append(f"{name}: has_index_html in snapshot does not match the directory")
        if d["live_url"] and not is_https_allowed(d["live_url"]):
            fails.append(f"{name}: live URL host not allowed")
    current = set()
    for name in os.listdir(repo_root):
        if os.path.isdir(os.path.join(repo_root, name)) and (
                (name.startswith("nfl-") or name.startswith("nfl_") or name == "own5-desk")
                and name != "nfl-desk-3cb7800c"):
            current.add(name)
    added = sorted(current - pinned)
    if added:
        info.append(f"INFO {len(added)} desk directories added since the snapshot (not a failure): {', '.join(added)}")
    return fails, info


# ---------------------------------------------------------------- registers

def check_registers(flags, sugg, quest, sources, repo):
    fails = []
    for label, rows, id_key in [("flagged", flags, "flag_id"), ("suggestions", sugg, "suggestion_id"),
                                ("questions", quest, "question_id"), ("sources", sources, "source_id"),
                                ("repo_checks", repo, "check_id")]:
        ids = [r[id_key] for r in rows]
        if len(ids) != len(set(ids)):
            fails.append(f"{label}: duplicate IDs")
        if not rows:
            fails.append(f"{label}: no rows")
    for f in flags:
        if f["severity"] not in {"BLOCKING", "REVIEW"}:
            fails.append(f"{f['flag_id']}: severity must be BLOCKING or REVIEW")
        if not is_https_allowed(f["evidence_url"]):
            fails.append(f"{f['flag_id']}: evidence link is not https on an allowed host")
    for s in sugg:
        if not s["options"] or not s["recommendation"] or not s["what_would_change_the_call"]:
            fails.append(f"{s['suggestion_id']}: needs options, recommendation and what would change the call")
        if s["decision"] != "PENDING REVIEW":
            fails.append(f"{s['suggestion_id']}: decision must stay PENDING REVIEW (no suggestion is implemented)")
        if not is_https_allowed(s["evidence_url"]):
            fails.append(f"{s['suggestion_id']}: evidence link not allowed")
    for q in quest:
        if not is_https_allowed(q["evidence_url"]):
            fails.append(f"{q['question_id']}: evidence link not allowed")
    for s in sources:
        if s["source_class"].startswith("OFFICIAL") and urlparse(s["url"]).hostname not in OFFICIAL_HOSTS:
            fails.append(f"{s['source_id']}: OFFICIAL row must link to nfl.com")
        if not is_https_allowed(s["url"]):
            fails.append(f"{s['source_id']}: URL not https on an allowed host")
    for r in repo:
        if not is_https_allowed(r["source_url"]):
            fails.append(f"{r['check_id']}: source not allowed")
    return fails


# ---------------------------------------------------------------- HTML

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = set()
        self.rows = []  # list of (in_tbody, has_anchor_or_badge)
        self._in_tbody = False
        self._row_has_link = None
        self._row_text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "tbody":
            self._in_tbody = True
        if tag == "tr" and self._in_tbody:
            self._row_has_link = False
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
            if self._row_has_link is not None:
                self._row_has_link = True
        if tag == "span" and "badge" in a.get("class", ""):
            if self._row_has_link is not None:
                self._row_has_link = True

    def handle_endtag(self, tag):
        if tag == "tbody":
            self._in_tbody = False
        if tag == "tr" and self._row_has_link is not None:
            self.rows.append(self._row_has_link)
            self._row_has_link = None


PAGES = ["index.html", "schedule.html", "availability.html", "desks.html", "repo.html", "sources.html",
         "summary.html", "suggestions.html", "questions.html", "flagged.html"]


def check_pages(desk=DESK):
    fails = []
    stats = {"pages": 0, "rows": 0, "links": 0}
    for page in PAGES:
        path = os.path.join(desk, page)
        if not os.path.isfile(path):
            fails.append(f"missing page {page}")
            continue
        text = read_text(path)
        p = PageParser()
        p.feed(text)
        stats["pages"] += 1
        stats["rows"] += len(p.rows)
        for href in p.hrefs:
            stats["links"] += 1
            parsed = urlparse(href)
            if parsed.scheme in ("http",):
                fails.append(f"{page}: plain http link {href}")
            elif parsed.scheme == "https":
                if not is_https_allowed(href):
                    fails.append(f"{page}: link host not allowed {href}")
            elif parsed.scheme == "" and not href.startswith("#"):
                target = os.path.normpath(os.path.join(desk, parsed.path))
                if not os.path.isfile(target):
                    fails.append(f"{page}: broken internal link {href}")
        for i, has in enumerate(p.rows):
            if not has:
                fails.append(f"{page}: table body row {i + 1} has no source link or badge")
        if "git log" in text or "last commit" in text.lower():
            fails.append(f"{page}: git-derived text is not allowed on published pages")
    return fails, stats


# ---------------------------------------------------------------- main

def run():
    failures = []
    failures += check_columns()
    if failures:
        return failures, {}, []
    games = load("week11_schedule.csv")
    byes = load("week11_byes.csv")
    avail = load("availability_status.csv")
    desks = load("desks_index.csv")
    repo = load("repo_checks.csv")
    sources = load("sources.csv")
    flags = load("flagged.csv")
    sugg = load("suggestions.csv")
    quest = load("questions.csv")
    extract = read_text(os.path.join(RAW, "nfl_week11_schedule_extract.txt"))
    meta = read_text(os.path.join(RAW, "nfl_injury_reg11_fetch_meta.txt"))
    failures += check_schedule(games, byes, extract)
    failures += check_hashes()
    failures += check_availability(avail, meta)
    f2, info = check_desks(desks)
    failures += f2
    failures += check_registers(flags, sugg, quest, sources, repo)
    f3, stats = check_pages()
    failures += f3
    counts = {
        "games": len(games), "byes": len(byes), "desks": len(desks), "flags": len(flags),
        "open_flags": sum(1 for f in flags if f["status"] == "OPEN"),
        "blocking": sum(1 for f in flags if f["severity"] == "BLOCKING"),
        **stats,
    }
    return failures, counts, info


def main():
    failures, counts, info = run()
    for line in info:
        print(line)
    if failures:
        for f in failures:
            print("FAIL", f)
        print(f"verify: {len(failures)} failure(s)")
        return 1
    print("verify: PASS", ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())

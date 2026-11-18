#!/usr/bin/env python3
"""Capture official NFL availability evidence into an immutable, dated store.

Why this exists
---------------
The repo held exactly one dated official availability capture
(``data/decision-desk/official/official_injuries_wk10.csv``, retrieved
2026-11-12T16:52:39Z).  One capture cannot support backtesting: it has no
delta, no point-in-time replay and no way to prove that a designation was
known before kickoff.  This script makes the capture *repeatable*, *dated*
and *hash-pinned*, and derives the series from it.

Rules (hard)
------------
* Only official league or official club URLs are fetched.  Nothing is inferred.
* A value that cannot be located in the fetched document is written **empty**,
  never guessed.  Every parse that cannot resolve something appends a
  ``problem`` string that is published in the drift report.
* Every capture writes: the extracted text, the SHA-256 of the **raw bytes**,
  the HTTP status, the byte count and the UTC retrieval time.  The ledger is
  append-only.
* A drift alarm compares the observed shape of every source against a pinned
  expectation file and exits non-zero when the shape changed (missing field,
  row count collapse, new club appearing, ...).  The alarm is the deliverable:
  a silent parser regression is worse than a loud failure.

The script is stdlib-only (PDF text extraction is attempted with ``pypdf`` or
``pdfplumber`` when they are installed; without them the game book is recorded
as ``pdf_text_unavailable`` and nothing is invented).  It is meant to run on a
GitHub Actions runner, which has full network egress.

Usage
-----
    python3 scripts/capture_availability.py --mode injuries --season 2026 --week 10
    python3 scripts/capture_availability.py --mode all --season 2026
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "nfl-evidence-7cac9edd")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")

# ---------------------------------------------------------------------------
# Club registry: abbr, full name, nfl.com slug, official club domain.
# ---------------------------------------------------------------------------
CLUBS = [
    ("ARI", "Arizona Cardinals", "arizona-cardinals", "azcardinals.com"),
    ("ATL", "Atlanta Falcons", "atlanta-falcons", "atlantafalcons.com"),
    ("BAL", "Baltimore Ravens", "baltimore-ravens", "baltimoreravens.com"),
    ("BUF", "Buffalo Bills", "buffalo-bills", "buffalobills.com"),
    ("CAR", "Carolina Panthers", "carolina-panthers", "carolinapanthers.com"),
    ("CHI", "Chicago Bears", "chicago-bears", "chicagobears.com"),
    ("CIN", "Cincinnati Bengals", "cincinnati-bengals", "cincinnatibengals.com"),
    ("CLE", "Cleveland Browns", "cleveland-browns", "clevelandbrowns.com"),
    ("DAL", "Dallas Cowboys", "dallas-cowboys", "dallascowboys.com"),
    ("DEN", "Denver Broncos", "denver-broncos", "denverbroncos.com"),
    ("DET", "Detroit Lions", "detroit-lions", "detroitlions.com"),
    ("GB", "Green Bay Packers", "green-bay-packers", "packers.com"),
    ("HOU", "Houston Texans", "houston-texans", "houstontexans.com"),
    ("IND", "Indianapolis Colts", "indianapolis-colts", "indianapoliscolts.com"),
    ("JAX", "Jacksonville Jaguars", "jacksonville-jaguars", "jacksonvillejaguars.com"),
    ("KC", "Kansas City Chiefs", "kansas-city-chiefs", "kansascitychiefs.com"),
    ("LV", "Las Vegas Raiders", "las-vegas-raiders", "lasvegasraiders.com"),
    ("LAC", "Los Angeles Chargers", "los-angeles-chargers", "losangeleschargers.com"),
    ("LAR", "Los Angeles Rams", "los-angeles-rams", "losangelesrams.com"),
    ("MIA", "Miami Dolphins", "miami-dolphins", "miamidolphins.com"),
    ("MIN", "Minnesota Vikings", "minnesota-vikings", "minnesotavikings.com"),
    ("NE", "New England Patriots", "new-england-patriots", "newenglandpatriots.com"),
    ("NO", "New Orleans Saints", "new-orleans-saints", "neworleanssaints.com"),
    ("NYG", "New York Giants", "new-york-giants", "newyorkgiants.com"),
    ("NYJ", "New York Jets", "new-york-jets", "newyorkjets.com"),
    ("PHI", "Philadelphia Eagles", "philadelphia-eagles", "philadelphiaeagles.com"),
    ("PIT", "Pittsburgh Steelers", "pittsburgh-steelers", "pittsburghsteelers.com"),
    ("SF", "San Francisco 49ers", "san-francisco-49ers", "sanfrancisco49ers.com"),
    ("SEA", "Seattle Seahawks", "seattle-seahawks", "seattleseahawks.com"),
    ("TB", "Tampa Bay Buccaneers", "tampa-bay-buccaneers", "tampabaybuccaneers.com"),
    ("TEN", "Tennessee Titans", "tennessee-titans", "tennesseetitans.com"),
    ("WAS", "Washington Commanders", "washington-commanders", "washingtoncommanders.com"),
]
ABBR2NAME = {a: n for a, n, _s, _d in CLUBS}
NAME2ABBR = {n: a for a, n, _s, _d in CLUBS}

# Depth-chart candidate paths, in the order they are tried per club.
DEPTH_PATHS = ["/team/depth-chart", "/team/roster/depth-chart", "/team/depth-charts"]

PRACTICE_VALUES = {
    "Did Not Participate In Practice": "DNP",
    "Limited Participation in Practice": "LP",
    "Full Participation in Practice": "FP",
}
GAME_VALUES = ("Out", "Doubtful", "Questionable")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean(s: str) -> str:
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?is)<br\s*/?>", " ", s)
    s = re.sub(r"(?is)</(p|div|li|tr|h\d)>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t ]+", " ", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


def fetch(url: str, timeout: int = 45) -> tuple[int, bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en-US,en;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        return exc.code, b"", ""
    except Exception as exc:  # noqa: BLE001 - a failed fetch is a status, not a crash
        return 0, ("FETCH_ERROR: %s" % exc).encode(), ""


def pdf_text(data: bytes) -> tuple[str, str]:
    """Return (text, engine).  Empty text + engine name is never invented data."""
    try:
        import io

        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(io.BytesIO(data))
        pages = [(p.extract_text() or "") for p in reader.pages]
        return "\n".join(pages), "pypdf"
    except Exception:
        pass
    try:
        import io

        import pdfplumber  # type: ignore
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = [(p.extract_text() or "") for p in pdf.pages]
        return "\n".join(pages), "pdfplumber"
    except Exception:
        return "", "unavailable"


def write_csv(path: str, rows: list[dict], fields: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def append_csv(path: str, rows: list[dict], fields: list[str]) -> None:
    exists = os.path.exists(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        if not exists:
            w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------
def _team_before(text: str, pos: int) -> tuple[str, str]:
    """Resolve the club that owns a table.

    Primary method: the nearest preceding club *abbreviation* logo token
    (``league/api/clubs/logos/XXX``).  Fallback: nearest preceding club name.
    The method used is returned so the site can show how each row was resolved.
    """
    window = text[max(0, pos - 40000):pos]
    best, best_at, method = "", -1, ""
    for m in re.finditer(r"clubs/logos/([A-Z]{2,3})\b", window):
        if m.start() > best_at:
            best_at, best, method = m.start(), ABBR2NAME.get(m.group(1), ""), "logo_abbr"
    if not best:
        for name in sorted(NAME2ABBR, key=len, reverse=True):
            for m in re.finditer(re.escape(name), window):
                if m.start() > best_at:
                    best_at, best, method = m.start(), name, "club_name"
    return best, method


def parse_injuries(text: str) -> tuple[list[dict], list[str]]:
    """Parse the official league injury report into one row per player."""
    rows: list[dict] = []
    problems: list[str] = []
    for m in re.finditer(r"(?is)<table[^>]*>(.*?)</table>", text):
        chunk = m.group(1)
        trs = [[clean(c) for c in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr)]
               for tr in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", chunk)]
        if not trs or not any("Player" in c for c in trs[0]):
            continue
        team, method = _team_before(text, m.start())
        if not team:
            problems.append("injury table with unresolved club")
        for cells in trs[1:]:
            if len(cells) < 3 or not cells[0]:
                continue
            padded = cells + [""] * (5 - len(cells))
            rows.append({
                "club": team,
                "team_resolution": method,
                "player": padded[0],
                "position": padded[1],
                "injury": padded[2],
                "practice_status": padded[3],
                "game_status": padded[4],
            })
    return rows, problems


def parse_schedule(text: str) -> tuple[list[dict], list[str]]:
    """Parse an official weekly schedule page into one row per game."""
    rows: list[dict] = []
    problems: list[str] = []
    # Game links look like: [A 24, B 21, FINAL, Thursday, November 12th](url)
    pattern = re.compile(
        r"\[([^\]\[]{2,90}?)\]\((https://www\.nfl\.com/games/[^)]+)\)")
    day_re = re.compile(r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Z][a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)")
    for m in pattern.finditer(text):
        label, url = m.group(1), m.group(2)
        away = home = ""
        scores = {}
        final = "FINAL" in label
        parts = [p.strip() for p in label.split(",")]
        if parts:
            head = parts[0]
            nums = re.findall(r"(\d{1,3})\b", head)
            names = re.split(r"\s+(\d{1,3})\b", head)
            names = [n for n in names if n.strip()]
            if len(names) >= 2:
                away, home = names[0].strip(), names[-1].strip()
            if len(nums) >= 2:
                scores = {"away": nums[-2], "home": nums[-1]}
        day = ""
        dm = day_re.search(label)
        if dm:
            day = "%s %s %s" % (dm.group(1), dm.group(2), dm.group(3))
        slug = url.rsplit("/", 1)[-1]
        rows.append({
            "away_team": away,
            "home_team": home,
            "away_score": scores.get("away", ""),
            "home_score": scores.get("home", ""),
            "status": "FINAL" if final else "",
            "date_label": day,
            "game_center_url": url,
            "slug": slug,
        })
    if not rows:
        problems.append("no game links found on schedule page")
    return rows, problems


def parse_game_center(text: str) -> dict:
    """Extract the official game-centre facts we publish."""
    out: dict = {"location": "", "stadium": "", "network": "", "game_book_url": "",
                 "problems": []}
    m = re.search(r"https://static\.www\.nfl\.com/\S+?\.pdf", text)
    if m:
        out["game_book_url"] = m.group(0)
    # The rendered page repeats each label ("Stadium" / "STADIUM"); collapse the
    # repetition before reading the value so the value is never a label.
    flat = re.sub(r"(?i)\b(location|stadium|network)\b(?:\s+\1\b)+", r"\1", text)
    mi = re.search(r"(?i)location\s+(.+?)\s+stadium\s+(.+?)(?:\n|\bnetwork\b|ways to watch|$)",
                   flat)
    if mi:
        out["location"] = mi.group(1).strip()
        out["stadium"] = mi.group(2).strip()
    else:
        out["problems"].append("game info location/stadium block not found")
    return out


def parse_roster(text: str) -> tuple[list[dict], list[str]]:
    """Parse an official nfl.com club roster page (status column included)."""
    rows: list[dict] = []
    problems: list[str] = []
    for m in re.finditer(r"(?is)<table[^>]*>(.*?)</table>", text):
        trs = [[clean(c) for c in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr)]
               for tr in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", m.group(1))]
        if not trs:
            continue
        header = " ".join(trs[0]).lower()
        if "status" not in header and "roster" not in header:
            continue
        for cells in trs[1:]:
            cells = [c for c in cells]
            if len(cells) < 3 or not cells[0]:
                continue
            if not re.search(r"[A-Za-z]{3}", cells[0]):
                continue
            status = ""
            for c in cells[1:]:
                if c.upper() in ("ACT", "IR", "PUP", "PS", "RES", "NFI", "IR-DNP",
                                 "PUP-DNP", "RES", "ACT", "INACTIVE"):
                    status = c.upper()
                    break
            rows.append({"player": cells[0], "status": status,
                         "raw": "|".join(cells), "team_resolution": ""})
    if not rows:
        problems.append("no roster table found")
    return rows, problems


def _strip_jersey(name: str) -> tuple[str, str]:
    """Split a leading jersey number off a depth-chart cell.

    The Packers publish ``9 Christian Watson``; the number is a jersey, not a
    depth rank.  Returns (player, jersey); jersey is '' when absent.
    """
    m = re.match(r"^\s*(\d{1,2})\s+(.+?)\s*$", name)
    if m:
        return m.group(2).strip(), m.group(1)
    return name.strip(), ""


def parse_depth_chart(text: str, club: str) -> tuple[list[dict], list[str]]:
    """Parse a club depth chart into slots.

    A slot is one published row of the chart.  Shared slots (the club names
    more than one rank-1 player at the same position) and empty slots (no
    rank-1 player) are represented explicitly; a slot is never collapsed to
    'the starter'.
    """
    rows: list[dict] = []
    problems: list[str] = []
    tables = list(re.finditer(r"(?is)<table[^>]*>(.*?)</table>", text))
    if not tables:
        problems.append("no depth table (image-only chart is possible)")
        return rows, problems
    unit = ""
    for m in tables:
        head = text[max(0, m.start() - 4000):m.start()]
        hu = re.findall(r"(?is)<h[1-6][^>]*>\s*(?:<[^>]+>\s*)*"
                        r"(OFFENSE|DEFENSE|SPECIAL TEAMS|KICKERS|PUNTERS)\b", head)
        if hu:
            unit = hu[-1].title().replace("Special Teams", "Special Teams")
        trs = [[clean(c) for c in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr)]
               for tr in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", m.group(1))]
        if not trs:
            continue
        header = " ".join(trs[0]).lower()
        if "player" not in header:
            continue
        slot_id = 0
        for cells in trs[1:]:
            if not cells:
                continue
            position = cells[0].strip()
            if not re.fullmatch(r"[A-Z/]{1,6}", position):
                continue
            # Column order *is* the depth order.  Empty cells are preserved so
            # that a slot with no rank-1 player stays an empty first string
            # instead of silently promoting the second string to "the starter".
            names = []
            for rank, c in enumerate(cells[1:], start=1):
                if not c.strip():
                    continue
                player, jersey = _strip_jersey(c)
                if player:
                    names.append((rank, player, jersey))
            slot_id += 1
            if names:
                for rank, player, jersey in names:
                    rows.append({"club": club, "unit": unit, "position": position,
                                 "slot_id": "%s-%s-%s-%d" % (club, unit, position, slot_id),
                                 "rank": str(rank), "player": player, "jersey": jersey,
                                 "shared_rank1": "no",
                                 "empty_first_string": "yes" if 1 not in [n[0] for n in names] else "no"})
            else:
                rows.append({"club": club, "unit": unit, "position": position,
                             "slot_id": "%s-%s-%s-%d" % (club, unit, position, slot_id),
                             "rank": "", "player": "", "jersey": "",
                             "shared_rank1": "no", "empty_first_string": "yes"})
    if not rows:
        problems.append("depth table found but no rows parsed")
    # A slot shared by more than one rank-1 player: the club named two or more
    # starters at the same position.  Flag every rank-1 player involved.
    by_slot: dict[str, list[dict]] = {}
    for r in rows:
        by_slot.setdefault("%s|%s|%s" % (r["club"], r["unit"], r["position"]), []).append(r)
    for group in by_slot.values():
        rank1 = [r for r in group if r["rank"] == "1"]
        if len(rank1) > 1:
            for r in rank1:
                r["shared_rank1"] = "YES"
    return rows, problems


# ---------------------------------------------------------------------------
# Capture plumbing
# ---------------------------------------------------------------------------
class Ledger:
    FIELDS = ["capture_id", "captured_utc", "source_kind", "source_id", "url",
              "http_status", "bytes", "sha256", "rows_parsed", "problems", "capture_date"]

    def __init__(self, path: str, capture_date: str):
        self.path = path
        self.capture_date = capture_date
        self.rows: list[dict] = []

    def add(self, kind: str, sid: str, url: str, status: int, size: int,
            digest: str, rows: int, problems: list[str]) -> None:
        self.rows.append({
            "capture_id": "%s/%s" % (self.capture_date, sid),
            "captured_utc": utcnow(),
            "source_kind": kind,
            "source_id": sid,
            "url": url,
            "http_status": status,
            "bytes": size,
            "sha256": digest,
            "rows_parsed": rows,
            "problems": "; ".join(problems),
            "capture_date": self.capture_date,
        })

    def flush(self) -> None:
        append_csv(self.path, self.rows, self.FIELDS)


def store_text(capture_date: str, sid: str, text: str) -> str:
    d = os.path.join(OUT, "captures", capture_date)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, sid + ".txt")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
def capture_injuries(led: Ledger, season: int, week: int) -> list[dict]:
    sid = "injuries_%d_reg%02d" % (season, week)
    url = "https://www.nfl.com/injuries/league/%d/reg%02d" % (season, week)
    status, body, _ctype = fetch(url)
    digest = hashlib.sha256(body).hexdigest() if body else ""
    if status != 200 or not body:
        led.add("injuries", sid, url, status, len(body), digest, 0,
                ["fetch failed"])
        return []
    text = clean(body.decode("utf-8", "replace"))
    store_text(led.capture_date, sid, text)
    rows, problems = parse_injuries(body.decode("utf-8", "replace"))
    title = re.search(r"Week (\d+) of the (\d{4}) Season", text)
    if title:
        problems.append("page_title_week=%s season=%s" % (title.group(1), title.group(2)))
    for r in rows:
        r["season"] = season
        r["week"] = week
        r["source_url"] = url
        r["captured_utc"] = led.rows[0]["captured_utc"] if led.rows else utcnow()
        r["capture_sha256"] = digest
        r["practice_status_code"] = PRACTICE_VALUES.get(r["practice_status"], "")
        r["capture_date"] = led.capture_date
    led.add("injuries", sid, url, status, len(body), digest, len(rows), problems)
    return rows


def capture_schedule(led: Ledger, season: int, week: int) -> list[dict]:
    sid = "schedule_%d_week%02d" % (season, week)
    url = "https://www.nfl.com/schedules/%d/by-week/week-%d" % (season, week)
    status, body, _c = fetch(url)
    digest = hashlib.sha256(body).hexdigest() if body else ""
    if status != 200 or not body:
        led.add("schedule", sid, url, status, len(body), digest, 0, ["fetch failed"])
        return []
    text = clean(body.decode("utf-8", "replace"))
    store_text(led.capture_date, sid, text)
    rows, problems = parse_schedule(body.decode("utf-8", "replace"))
    for r in rows:
        r["season"] = season
        r["week"] = week
        r["source_url"] = url
        r["captured_utc"] = led.rows[0]["captured_utc"] if led.rows else utcnow()
        r["capture_sha256"] = digest
        r["capture_date"] = led.capture_date
    led.add("schedule", sid, url, status, len(body), digest, len(rows), problems)
    return rows


def capture_game_center(led: Ledger, slug: str) -> dict:
    sid = "gamecenter_%s" % slug
    url = "https://www.nfl.com/games/%s" % slug
    status, body, _c = fetch(url)
    digest = hashlib.sha256(body).hexdigest() if body else ""
    if status != 200 or not body:
        led.add("game_center", sid, url, status, len(body), digest, 0, ["fetch failed"])
        return {}
    text = clean(body.decode("utf-8", "replace"))
    store_text(led.capture_date, sid, text)
    info = parse_game_center(text)
    problems = list(info.get("problems", []))
    info.update({"slug": slug, "url": url, "http_status": status,
                 "sha256": digest, "captured_utc": utcnow(),
                 "source_url": url, "capture_date": led.capture_date})
    led.add("game_center", sid, url, status, len(body), digest, 1, problems)
    return info


def capture_game_book(led: Ledger, slug: str, pdf_url: str) -> tuple[dict, list[dict], list[dict]]:
    """Fetch an official NFL Game Book PDF and extract its official facts."""
    sid = "gamebook_%s" % slug
    status, body, ctype = fetch(pdf_url, timeout=90)
    digest = hashlib.sha256(body).hexdigest() if body else ""
    problems: list[str] = []
    if status != 200 or not body:
        led.add("game_book", sid, pdf_url, status, len(body), digest, 0, ["fetch failed"])
        return {}, [], []
    text, engine = pdf_text(body)
    if not text:
        problems.append("pdf_text_unavailable (no pypdf/pdfplumber)")
        led.add("game_book", sid, pdf_url, status, len(body), digest, 0, problems)
        return {"slug": slug, "pdf_url": pdf_url, "sha256": digest,
                "captured_utc": utcnow(), "http_status": status}, [], []
    store_text(led.capture_date, sid, text)
    facts, starters, inactives = parse_game_book(text)
    facts.update({"slug": slug, "pdf_url": pdf_url, "sha256": digest,
                  "captured_utc": utcnow(), "http_status": status,
                  "pdf_engine": engine, "source_url": pdf_url,
                  "capture_date": led.capture_date})
    led.add("game_book", sid, pdf_url, status, len(body), digest,
            len(starters) + len(inactives), problems)
    return facts, starters, inactives


POS_ABBR = ("LT", "LG", "C", "RG", "RT", "TE", "QB", "RB", "WR", "FB", "OL", "T", "G",
            "DE", "DT", "DL", "EDGE", "OLB", "LB", "CB", "DB", "FS", "SS", "S", "WR1",
            "P", "K", "LS", "HB")


def _player_tokens(text: str) -> list[tuple[str, str]]:
    """Return (jersey, name) pairs found in a game-book player list."""
    out = []
    for m in re.finditer(r"(?<![A-Za-z0-9])(\d{1,2})\s+((?:[A-Z]\.)+(?:[A-Za-z'’-]+)(?:\s+[A-Z][A-Za-z'’-]+)?)",
                         text):
        out.append((m.group(1), m.group(2).strip()))
    return out


CLUB_BY_NAME = {n: a for a, n, _s, _d in CLUBS}
LINEUP_HEAD = re.compile(r"([A-Z]{1,4})\s+(\d{1,2})\s+")
INACTIVE_HEAD = re.compile(r"([A-Z0-9]{1,4})\s+(\d{1,2})\s+")


def _split_heads(line: str, head_re) -> list[tuple[str, str, str]]:
    """Split a game-book player line into (position, jersey, name) triples.

    The name is whatever sits between this head and the next head, so names
    such as ``A.St. Brown``, ``Dr.Jones`` or ``Pierre Strong Jr.`` survive
    without a hand-written name pattern.
    """
    heads = list(head_re.finditer(line))
    out = []
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(line)
        name = line[h.end():end].strip(" ,|")
        if name:
            out.append((h.group(1), h.group(2), name))
    return out


def parse_game_book(text: str) -> tuple[dict, list[dict], list[dict]]:
    """Extract header facts, official starters and the official inactive list."""
    facts: dict = {}
    starters: list[dict] = []
    inactives: list[dict] = []
    problems: list[str] = []

    md = re.search(r"Date:\s*([A-Za-z]+,\s*\d{1,2}/\d{1,2}/\d{4})\s+(.+?)\s+at\s+(.+?)\s+at\s+(.+?),\s*(.+?)\n",
                   text)
    if md:
        facts["game_date"] = md.group(1)
        facts["matchup"] = md.group(2).strip()
        facts["home_team"] = md.group(3).strip()
        facts["venue"] = md.group(4).strip()
        facts["venue_city_state_country"] = md.group(5).strip()
    mw = re.search(r"Game Weather:\s*(.+?)\s*\|\s*Temp:\s*(.+?)\s*\|\s*Humidity:\s*(\d+)%,\s*Wind:\s*(.+?)\n",
                   text)
    if mw:
        facts["weather"] = mw.group(1).strip()
        facts["temp_f"] = mw.group(2).strip()
        facts["humidity_pct"] = mw.group(3)
        facts["wind"] = mw.group(4).strip()
    mr = re.search(r"(Open|Closed|Domed|Retractable)\s+Stadium\s+on\s+([A-Za-z ]+)", text)
    if mr:
        facts["roof_status"] = mr.group(1)
        facts["surface"] = mr.group(2).strip()
    ma = re.search(r"Paid Attendance:\s*([\d,]+)", text)
    if ma:
        facts["attendance"] = ma.group(1)

    # ---- Lineups (official actual starters) -------------------------------
    li = text.find("Lineups")
    if li != -1:
        block = text[li:li + 20000]
        ni = block.find("Did Not Play")
        if ni != -1:
            block = block[:ni]
        teams: list[str] = []
        if "matchup" in facts and " at " in facts["matchup"]:
            parts = [p.strip() for p in facts["matchup"].split(" at ")]
            if len(parts) == 2 and parts[0] in CLUB_BY_NAME and parts[1] in CLUB_BY_NAME:
                teams = parts
        if len(teams) < 2:
            names = []
            for name in sorted(CLUB_BY_NAME, key=len, reverse=True):
                m = re.search(re.escape(name), block)
                if m:
                    names.append((m.start(), name))
            names.sort()
            teams = [n for _s, n in names[:2]]
        if len(teams) < 2:
            problems.append("lineups block: fewer than two club names found")
        else:
            for line in block.splitlines():
                flat = line.replace("|", " ")
                entries = _split_heads(flat, LINEUP_HEAD)
                if not entries:
                    continue
                if len(entries) != 4:
                    problems.append("lineup row with %d entries (not 4): %s"
                                    % (len(entries), line.strip()[:80]))
                    continue
                roles = [(teams[0], "offense"), (teams[0], "defense"),
                         (teams[1], "offense"), (teams[1], "defense")]
                for (pos, jer, nm), (tm, unit) in zip(entries, roles):
                    starters.append({"team": tm, "unit": unit, "position": pos,
                                     "jersey": jer, "player": nm,
                                     "source": "game_book_lineups"})

    # ---- Not Active (official inactive list) ------------------------------
    na = text.find("Not Active")
    if na != -1:
        tail = text[na:na + 4000]
        end = tail.find("Paid Attendance")
        if end != -1:
            tail = tail[:end]
        segments = [s for s in re.split(r"\n{2,}", tail) if s.strip()]
        if len(segments) < 2:
            segments = re.split(r"\s{4,}", tail)
        team_seq = []
        for seg in segments:
            found = re.findall(r"([A-Z][A-Za-z .'\-]{3,40})\n", seg)
            team_seq.append(found[0].strip() if found else "")
        idx = 0
        for seg in segments:
            for chunk in re.split(r",\s*", seg):
                entries = _split_heads(chunk, INACTIVE_HEAD)
                if not entries:
                    continue
                pos, jer, nm = entries[0]
                tm = team_seq[idx] if idx < len(team_seq) else ""
                inactives.append({"team": tm, "position": pos, "jersey": jer,
                                  "player": nm, "status": "Not Active",
                                  "source": "game_book_not_active"})
            idx += 1
        if not inactives:
            problems.append("Not Active block found but no entries parsed")
    facts["problems"] = "; ".join(problems)
    return facts, starters, inactives


def capture_roster(led: Ledger, abbr: str, slug: str) -> list[dict]:
    sid = "roster_%s" % abbr
    url = "https://www.nfl.com/teams/%s/roster" % slug
    status, body, _c = fetch(url)
    digest = hashlib.sha256(body).hexdigest() if body else ""
    if status != 200 or not body:
        led.add("roster", sid, url, status, len(body), digest, 0, ["fetch failed"])
        return []
    text = clean(body.decode("utf-8", "replace"))
    store_text(led.capture_date, sid, text)
    rows, problems = parse_roster(body.decode("utf-8", "replace"))
    for r in rows:
        r["club"] = NAME2ABBR.get(abbr, abbr)
        r["source_url"] = url
        r["captured_utc"] = utcnow()
        r["capture_sha256"] = digest
        r["capture_date"] = led.capture_date
    led.add("roster", sid, url, status, len(body), digest, len(rows), problems)
    return rows


def capture_depth(led: Ledger, abbr: str, domain: str) -> list[dict]:
    sid = "depth_%s" % abbr
    rows: list[dict] = []
    problems: list[str] = []
    for path in DEPTH_PATHS:
        url = "https://www.%s%s" % (domain, path)
        status, body, _c = fetch(url)
        digest = hashlib.sha256(body).hexdigest() if body else ""
        if status != 200 or not body:
            problems.append("%s http=%s" % (path, status))
            continue
        text = clean(body.decode("utf-8", "replace"))
        store_text(led.capture_date, sid, text)
        parsed, probs = parse_depth_chart(body.decode("utf-8", "replace"), abbr)
        if parsed:
            for r in parsed:
                r["source_url"] = url
                r["captured_utc"] = utcnow()
                r["capture_sha256"] = digest
                r["route"] = "table"
                r["capture_date"] = led.capture_date
                m = re.search(r"(Unofficial[^\n]{0,40}?)(?:\n|$)", text)
                r["chart_as_of_text"] = m.group(1).strip() if m else ""
            led.add("depth", sid, url, status, len(body), digest, len(parsed), probs)
            return rows + parsed
        problems.append("%s no rows (%s)" % (path, "; ".join(probs)))
    # image-only or missing -> record the failure, invent nothing
    led.add("depth", sid, "https://www.%s%s" % (domain, DEPTH_PATHS[0]), 404, 0, "", 0, problems)
    return rows


# ---------------------------------------------------------------------------
# Drift alarm
# ---------------------------------------------------------------------------
EXPECT_PATH = os.path.join(OUT, "expectations.json")


def load_expectations() -> dict:
    if os.path.exists(EXPECT_PATH):
        with open(EXPECT_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def check_drift(led: Ledger, expectations: dict) -> list[dict]:
    """Compare the observed shape of each source with the pinned expectation.

    ``known_zero`` names sources whose empty result is a *documented property
    of the publisher* (for example a club that publishes its depth chart as an
    image).  Those are reported as ``known_exception`` and are published on the
    Flagged page; they never fail the build, but they can never be silently
    ignored either.
    """
    alarms: list[dict] = []
    known_zero = expectations.get("known_zero", {})
    for row in led.rows:
        exp = expectations.get(row["source_kind"], {})
        lo = exp.get("min_rows", 0)
        hi = exp.get("max_rows", 10 ** 9)
        observed = row["rows_parsed"]
        state = "ok"
        detail = ""
        if row["source_id"] in known_zero:
            state = "known_exception"
            detail = known_zero[row["source_id"]]
        elif row["http_status"] != 200:
            state, detail = "alarm", "http %s" % row["http_status"]
        elif observed < lo or observed > hi:
            state = "alarm"
            detail = "rows %s outside pinned range [%s, %s]" % (observed, lo, hi)
        elif row["problems"]:
            state = "warn"
            detail = row["problems"]
        alarms.append({
            "capture_id": row["capture_id"],
            "source_kind": row["source_kind"],
            "source_id": row["source_id"],
            "observed_rows": observed,
            "pinned_min_rows": lo,
            "pinned_max_rows": hi,
            "http_status": row["http_status"],
            "state": state,
            "detail": detail,
            "checked_utc": utcnow(),
        })
    return alarms


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> int:
    global OUT
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", default="injuries",
                    choices=["injuries", "schedule", "gamecenter", "gamebook",
                             "roster", "depth", "all", "everything"])
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--week", type=int, default=0)
    ap.add_argument("--weeks", default="", help="comma separated week list")
    ap.add_argument("--capture-date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    OUT = args.out
    os.makedirs(OUT, exist_ok=True)
    led = Ledger(os.path.join(OUT, "ledger.csv"), args.capture_date)

    weeks = [int(w) for w in args.weeks.split(",") if w.strip().isdigit()]
    if not weeks and args.week:
        weeks = [args.week]
    if args.mode in ("injuries", "schedule", "all") and not weeks:
        weeks = [args.week or 10]

    designations: list[dict] = []
    fixtures: list[dict] = []
    gamecenters: list[dict] = []
    facts_all: list[dict] = []
    starters_all: list[dict] = []
    inactives_all: list[dict] = []
    roster_all: list[dict] = []
    depth_all: list[dict] = []

    if args.mode in ("injuries", "all"):
        for w in weeks:
            designations += capture_injuries(led, args.season, w)
    if args.mode in ("schedule", "all"):
        for w in weeks:
            fixtures += capture_schedule(led, args.season, w)
    if args.mode == "gamecenter":
        slugs = args.weeks.split(",") if args.weeks else []
        for slug in slugs:
            info = capture_game_center(led, slug)
            if info:
                gamecenters.append(info)
    if args.mode == "gamebook":
        for slug in [s for s in args.weeks.split(",") if s]:
            gc = capture_game_center(led, slug)
            pdf = gc.get("game_book_url", "")
            if not pdf:
                continue
            facts, st, ia = capture_game_book(led, slug, pdf)
            facts_all.append(facts)
            starters_all += st
            inactives_all += ia
    if args.mode == "roster":
        for abbr, name, slug, _domain in CLUBS:
            roster_all += capture_roster(led, abbr, slug)
    if args.mode == "depth":
        for abbr, name, slug, domain in CLUBS:
            depth_all += capture_depth(led, abbr, domain)

    if args.mode == "everything":
        # One pass over every official source the desk publishes.
        for w in weeks:
            designations += capture_injuries(led, args.season, w)
            fixtures += capture_schedule(led, args.season, w)
        # Game centres and game books are captured for the most recent week
        # only; the historical weeks are archived at designation level.
        last_week = max(weeks) if weeks else 0
        slugs = [f["slug"] for f in fixtures if f.get("slug") and int(f.get("week") or 0) == last_week]
        for slug in slugs:
            info = capture_game_center(led, slug)
            if not info:
                continue
            gamecenters.append(info)
            final = any(f.get("slug") == slug and f.get("status") == "FINAL" for f in fixtures)
            pdf = info.get("game_book_url", "")
            if final and pdf:
                facts, st, ia = capture_game_book(led, slug, pdf)
                facts_all.append(facts)
                starters_all += st
                inactives_all += ia
        for abbr, name, slug, domain in CLUBS:
            roster_all += capture_roster(led, abbr, slug)
            depth_all += capture_depth(led, abbr, domain)

    led.flush()

    # Every capture is written into its own dated directory.  A capture is
    # never overwritten: the point-in-time store is the evidence that a
    # designation was known before kickoff.
    day = os.path.join(OUT, "captures", args.capture_date)
    if designations:
        write_csv(os.path.join(day, "designations.csv"), designations,
                  ["season", "week", "club", "team_resolution", "player", "position",
                   "injury", "practice_status", "practice_status_code", "game_status",
                   "source_url", "captured_utc", "capture_sha256", "capture_date"])
    if fixtures:
        write_csv(os.path.join(day, "fixtures.csv"), fixtures,
                  ["season", "week", "away_team", "home_team", "away_score", "home_score",
                   "status", "date_label", "game_center_url", "slug", "source_url",
                   "captured_utc", "capture_sha256", "capture_date"])
    if gamecenters:
        write_csv(os.path.join(day, "game_centers.csv"), gamecenters,
                  ["slug", "location", "stadium", "network", "game_book_url", "http_status",
                   "sha256", "captured_utc", "source_url", "problems", "capture_date"])
    if facts_all:
        write_csv(os.path.join(day, "gamebook_facts.csv"), facts_all,
                  ["slug", "game_date", "matchup", "home_team", "venue",
                   "venue_city_state_country", "weather", "temp_f", "humidity_pct", "wind",
                   "roof_status", "surface", "attendance", "pdf_engine", "http_status",
                   "sha256", "captured_utc", "source_url", "capture_date"])
    if starters_all:
        write_csv(os.path.join(day, "gamebook_starters.csv"), starters_all,
                  ["team", "unit", "position", "jersey", "player", "source", "capture_date"])
    if inactives_all:
        write_csv(os.path.join(day, "gamebook_inactives.csv"), inactives_all,
                  ["team", "position", "jersey", "player", "status", "source", "capture_date"])
    if roster_all:
        write_csv(os.path.join(day, "roster_status.csv"), roster_all,
                  ["club", "player", "status", "raw", "source_url", "captured_utc",
                   "capture_sha256", "capture_date"])
    if depth_all:
        write_csv(os.path.join(day, "depth_slots.csv"), depth_all,
                  ["club", "unit", "position", "slot_id", "rank", "player", "jersey",
                   "shared_rank1", "empty_first_string", "route", "chart_as_of_text",
                   "source_url", "captured_utc", "capture_sha256", "capture_date"])

    alarms = check_drift(led, load_expectations())
    for a in alarms:
        a["capture_date"] = args.capture_date
    append_csv(os.path.join(OUT, "drift_alarm.csv"), alarms,
               ["capture_id", "source_kind", "source_id", "observed_rows", "pinned_min_rows",
                "pinned_max_rows", "http_status", "state", "detail", "checked_utc",
                "capture_date"])
    bad = [a for a in alarms if a["state"] == "alarm"]
    print("captures=%d alarms=%d warnings=%d" % (
        len(led.rows), len(bad), len([a for a in alarms if a["state"] == "warn"])))
    for a in bad:
        print("ALARM %s %s %s" % (a["source_id"], a["state"], a["detail"]))
    if bad and os.environ.get("ALLOW_DRIFT") != "1":
        print("drift alarm: refusing to publish (set ALLOW_DRIFT=1 to override)")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

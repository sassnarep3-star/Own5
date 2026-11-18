#!/usr/bin/env python3
"""Parse a captured nfl.com injury-report page (raw gzip) into team/player rows (stdlib only).

Structure relied on (checked against the raw bytes, not assumed):
  - one <table> per club with thead Player | Position | Injuries | Practice Status | Game Status
  - the club nickname in the <div class="d3-o-section-sub-title"><span>NAME</span></div> preceding the table
Returns a list of dicts. Raises ValueError if the expected structure is not found (drift alarm).
"""
import gzip, html, re, sys
from html.parser import HTMLParser

HEADER = ["Player", "Position", "Injuries", "Practice Status", "Game Status"]


class _P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.team = None
        self.in_title = False
        self.title_text = ""
        self.tables = []      # (team, header, rows)
        self._in_table = False
        self._cur = None
        self._cell = None
        self._row = None
        self._in_thead = False
        self._header = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "") or ""
        if tag == "div" and "d3-o-section-sub-title" in cls:
            self.in_title, self.title_text = True, ""
        if tag == "table":
            self._in_table = True
            self._cur = {"team": self.team, "header": None, "rows": []}
        if self._in_table and tag == "thead":
            self._in_thead = True
        if self._in_table and tag == "tr":
            self._row = []
        if self._in_table and tag in ("td", "th"):
            self._cell = []

    def handle_endtag(self, tag):
        if tag == "div" and self.in_title:
            self.in_title = False
            t = re.sub(r"\s+", " ", self.title_text).strip()
            if t:
                self.team = t
        if self._in_table and tag in ("td", "th") and self._cell is not None:
            self._row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None
        if self._in_table and tag == "tr" and self._row is not None:
            if self._in_thead:
                self._cur["header"] = self._row
            elif self._row:
                self._cur["rows"].append(self._row)
            self._row = None
        if tag == "thead":
            self._in_thead = False
        if tag == "table" and self._in_table:
            self.tables.append(self._cur)
            self._in_table = False

    def handle_data(self, data):
        if self.in_title:
            self.title_text += data
        if self._cell is not None:
            self._cell.append(data)


def parse_injury_html(text: str):
    p = _P()
    p.feed(text)
    out = []
    for t in p.tables:
        if t["header"] != HEADER:
            continue  # other tables on the page are not the injury report
        for r in t["rows"]:
            if len(r) != 5:
                raise ValueError(f"row with {len(r)} cells under {t['team']}: {r}")
            out.append({"team": t["team"], "player": r[0], "position": r[1], "injuries": r[2],
                        "practice_status": r[3], "game_status": r[4]})
    tables = [t for t in p.tables if t["header"] == HEADER]
    if not tables or not out:
        raise ValueError("injury-report table structure not found (drift)")
    if any(not t["team"] for t in tables):
        raise ValueError("a club table has no club name above it (drift)")
    return out, len(tables)


def parse_file(path: str):
    with gzip.open(path, "rb") as f:
        return parse_injury_html(f.read().decode("utf-8", "replace"))


if __name__ == "__main__":
    rows, n_tables = parse_file(sys.argv[1])
    print(f"tables={n_tables} rows={len(rows)}")

"""Line-by-line verification harness for the decision-readiness desk.

Fails the build (exit 1) if any of these invariants is broken:

1. **Source-or-flag** - every body-table row (``<tr>`` inside ``<tbody>``) on every
   generated page contains either a source link (an ``<a href>``) or an explicit
   UNVERIFIED blank badge.  A blank cell can never be mistaken for a sourced value.
2. **No broken internal links** - every local ``.html`` link resolves to a file
   that exists.
3. **Landing table present** - ``index.html`` and ``readiness.html`` both render the
   decision-readiness table (one row per requirement).

Stdlib only.  Deterministic.
"""

from __future__ import annotations

import os
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.abspath(__file__))

PAGES = ["index.html", "readiness.html", "questions.html", "suggestions.html",
         "sources.html", "flagged.html", "review.html"]


class RowParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_tbody = False
        self.in_tr = False
        self.in_a = False
        self.in_blank = False
        self.rows = []          # list of dicts
        self.links = []
        self._cur = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_tr = True
            self._cur = {"has_link": False, "has_unverified": False, "text": ""}
        elif tag == "a" and self._cur is not None:
            self.in_a = True
            if a.get("href"):
                self._cur["has_link"] = True
                self.links.append(a["href"])
        elif tag == "span" and a.get("class") == "blank":
            self.in_blank = True
        elif tag == "a" and not self.in_tbody:
            if a.get("href"):
                self.links.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        elif tag == "tr" and self.in_tr:
            self.in_tr = False
            if self._cur is not None:
                self.rows.append(self._cur)
                self._cur = None
        elif tag == "a":
            self.in_a = False
        elif tag == "span":
            self.in_blank = False

    def handle_data(self, data):
        if self._cur is not None:
            self._cur["text"] += data
            if "UNVERIFIED" in data:
                self._cur["has_unverified"] = True


def parse_file(name):
    p = RowParser()
    with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
        p.feed(fh.read())
    return p


def main():
    failures = []
    total_rows = 0
    linked = 0
    flagged = 0

    for name in PAGES:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            failures.append("{0}: file missing".format(name))
            continue
        p = parse_file(name)
        for row in p.rows:
            total_rows += 1
            if row["has_link"]:
                linked += 1
            elif row["has_unverified"]:
                flagged += 1
            else:
                failures.append("{0}: body row has neither a source link nor an UNVERIFIED badge "
                                "(text={1!r})".format(name, row["text"][:80]))
        # internal link check
        for href in p.links:
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            if href.endswith(".html"):
                target = os.path.normpath(os.path.join(ROOT, href))
                if not os.path.exists(target):
                    failures.append("{0}: broken internal link -> {1}".format(name, href))

    # landing table presence
    for name, marker in (("index.html", 'data-table="readiness_landing"'),
                         ("readiness.html", 'data-table="readiness"')):
        with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
            if marker not in fh.read():
                failures.append("{0}: decision-readiness table marker {1} not found".format(name, marker))

    print("verify.py: {0} pages, {1} body rows ({2} source-linked, {3} explicitly unverified)".format(
        len(PAGES), total_rows, linked, flagged))
    if failures:
        print("verify.py: FAIL ({0} problem(s))".format(len(failures)))
        for f in failures:
            print("  - " + f)
        return 1
    print("verify.py: PASS - every body row is source-linked or explicitly flagged; "
          "0 broken internal links; landing table present")
    return 0


if __name__ == "__main__":
    sys.exit(main())

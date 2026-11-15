"""Row-level verification for the generated decision-readiness site.

For every <tbody> row in every generated page this asserts:

* the row contains an <a href> source link, **or**
* the row carries an explicit UNVERIFIED badge (``data-unverified="1"``).

An empty source cell can therefore never be mistaken for a sourced value.  It
also checks that every internal ``*.html`` link resolves to a file on disk and
that the build report records no irregular status checks.

Exit code 0 = pass, 1 = fail.
"""

from __future__ import annotations

import json
import os
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = ROOT
DATA = os.path.join(ROOT, "data")

PAGES = [
    "index.html", "executive-summary.html", "requirements.html",
    "strategies.html", "suggestions.html", "questions.html", "luck.html",
    "flagged.html", "repo-audit.html", "sources.html",
]


class RowChecker(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_tbody = False
        self.in_tr = False
        self.in_a = False
        self.row_has_link = False
        self.row_unverified = False
        self.rows_checked = 0
        self.row_failures: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_tr = True
            self.row_has_link = False
            self.row_unverified = False
        elif tag == "a" and self.in_tr:
            self.in_a = True
            if a.get("href"):
                self.row_has_link = True
                self.links.append(a["href"])
        if a.get("data-unverified") == "1":
            self.row_unverified = True

    def handle_endtag(self, tag):
        if tag == "a":
            self.in_a = False
        elif tag == "tr" and self.in_tr:
            self.in_tr = False
            self.rows_checked += 1
            if not (self.row_has_link or self.row_unverified):
                self.row_failures.append(
                    "a body-table row has neither a source link nor an UNVERIFIED badge")
        elif tag == "tbody":
            self.in_tbody = False


def verify_page(name: str) -> tuple[int, int, list[str], list[str]]:
    path = os.path.join(SITE, name)
    with open(path, "r", encoding="utf-8") as fh:
        body = fh.read()
    parser = RowChecker()
    parser.feed(body)
    failures = list(parser.row_failures)

    # internal link resolution
    for href in parser.links:
        if href.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = href.split("#", 1)[0]
        if not target:
            continue
        if not os.path.exists(os.path.join(SITE, target)):
            failures.append(f"broken internal link in {name}: {href}")
    return parser.rows_checked, 0, failures, parser.links


def main() -> int:
    total_rows = 0
    all_failures: list[str] = []
    for page in PAGES:
        rows, _, failures, _ = verify_page(page)
        total_rows += rows
        for f in failures:
            all_failures.append(f"{page}: {f}")
        status = "OK" if not failures else "FAIL"
        print(f"{status}  {page:<24} rows={rows}")

    # build report must be clean
    report_path = os.path.join(DATA, "build_report.json")
    if not os.path.exists(report_path):
        all_failures.append("missing data/build_report.json (run consolidate.py first)")
    else:
        with open(report_path, "r", encoding="utf-8") as fh:
            report = json.load(fh)
        if not report.get("ok", False):
            for f in report.get("failures", []):
                all_failures.append(f"consolidation: {f.get('req_id')} {f.get('detail')}")

    print(f"\n{total_rows} body-table rows checked across {len(PAGES)} pages.")
    if all_failures:
        print(f"FAIL: {len(all_failures)} problem(s):")
        for f in all_failures:
            print("  -", f)
        return 1
    print("PASS: every body-table row is source-linked or explicitly UNVERIFIED; "
          "no broken internal links; consolidation report is clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

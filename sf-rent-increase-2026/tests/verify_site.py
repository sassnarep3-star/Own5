#!/usr/bin/env python3
"""Fail-closed checks for the SF rent review static site."""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PAGES = sorted(ROOT.glob("*.html"))
OFFICIAL_HOSTS = {
    "www.sf.gov", "sf.gov", "media.api.sf.gov", "leginfo.legislature.ca.gov",
    "uscode.house.gov", "calcivilrights.ca.gov", "sfplanninggis.org",
}
FORBIDDEN_NAMES = re.compile(r"\b(?:L\s+O|V\s+N|J\s+P|M\s+T|E\s+R|I\s+S)\b", re.I)
REQUIRED_FILES = {
    "index.html", "summary.html", "case-data.html", "rules.html", "practice.html",
    "notice.html", "flagged.html", "sources.html",
}

class AuditParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.href = None
        self.links = []
        self.row_depth = 0
        self.row_links = []
        self.rows = []
        self.in_tbody = False
        self.tbody_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a":
            self.href = a.get("href")
            if self.href is not None:
                self.links.append(self.href)
                if self.in_tbody and self.row_depth:
                    self.row_links.append(self.href)
        elif tag == "tbody":
            self.in_tbody = True
            self.tbody_depth += 1
        elif tag == "tr" and self.in_tbody:
            self.row_depth += 1
            self.row_links = []

    def handle_endtag(self, tag):
        if tag == "a":
            self.href = None
        elif tag == "tr" and self.in_tbody and self.row_depth:
            self.rows.append(list(self.row_links))
            self.row_depth -= 1
            self.row_links = []
        elif tag == "tbody" and self.tbody_depth:
            self.tbody_depth -= 1
            self.in_tbody = self.tbody_depth > 0


def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)

if not PAGES:
    fail("no HTML pages found")
missing = REQUIRED_FILES - {p.name for p in PAGES}
if missing:
    fail(f"required pages missing: {sorted(missing)}")

all_rows = 0
all_links = 0
for page in PAGES:
    text = page.read_text(encoding="utf-8")
    if FORBIDDEN_NAMES.search(text):
        fail(f"possible real tenant initials found in {page.name}")
    parser = AuditParser()
    parser.feed(text)
    all_rows += len(parser.rows)
    all_links += len(parser.links)
    for index, row_links in enumerate(parser.rows, 1):
        official = []
        for href in row_links:
            parsed = urlparse(href)
            if parsed.scheme in ("http", "https") and parsed.hostname in OFFICIAL_HOSTS:
                official.append(href)
        if not official:
            fail(f"table body row lacks an official source link: {page.name} row {index}")
    for href in parser.links:
        parsed = urlparse(href)
        if parsed.scheme in ("http", "https"):
            if parsed.hostname not in OFFICIAL_HOSTS:
                fail(f"non-official external link in {page.name}: {href}")
        elif parsed.scheme or href.startswith("//"):
            fail(f"unsupported link type in {page.name}: {href}")
        else:
            target = href.split("#", 1)[0]
            if target:
                resolved = (page.parent / target).resolve()
                if ROOT.resolve() not in resolved.parents and resolved != ROOT.resolve():
                    fail(f"path escapes site root in {page.name}: {href}")
                if not resolved.exists():
                    fail(f"broken internal link in {page.name}: {href}")

case = (ROOT / "case-data.html").read_text(encoding="utf-8")
for exact in ("February 1, 2025", "$3,995", "April 1, 2026", "June 1, 2019", "$3,150", "Tenant A", "Tenant D", "Tenant E", "Tenant F"):
    if exact not in case:
        fail(f"privacy-safe case data missing expected supplied detail: {exact}")
for phrase in ("Owner-reported", "not independently confirmed", "street address", "Placeholder names"):
    if phrase.lower() not in case.lower():
        fail(f"privacy / provenance disclosure missing: {phrase}")
for phrase in ("1.6%", "February 28, 2027", "Blank"):
    if phrase not in (ROOT / "rules.html").read_text(encoding="utf-8"):
        fail(f"verified rate or fail-closed blank missing from rules page: {phrase}")

print(f"PASS: {len(PAGES)} HTML pages, {all_rows} sourced table rows, {all_links} links; privacy, official host, local target, and case-data checks passed.")

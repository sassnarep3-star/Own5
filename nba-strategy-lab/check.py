#!/usr/bin/env python3
"""Static-site provenance, internal-link and completeness checker."""
from __future__ import annotations

import csv
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
OFFICIAL = {"www.nba.com", "official.nba.com"}


class AuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.rows = 0
        self.unsourced: list[int] = []
        self.in_tbody = 0
        self.in_row = False
        self.row_has_official = False
        self.title = False
        self.h1 = False
        self.has_none = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.links.append(values["href"] or "")
            if self.in_row and urlparse(values["href"]).hostname in OFFICIAL:
                self.row_has_official = True
        elif tag == "tbody":
            self.in_tbody += 1
        elif tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_has_official = False
        elif tag == "title":
            self.title = True
        elif tag == "h1":
            self.h1 = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "tbody":
            self.in_tbody -= 1
        elif tag == "tr" and self.in_row:
            self.rows += 1
            if not self.row_has_official:
                self.unsourced.append(self.rows)
            self.in_row = False

    def handle_data(self, data: str) -> None:
        if "None" in data or "PENDING_PLACEHOLDER" in data:
            self.has_none = True


def main() -> None:
    pages = sorted(ROOT.glob("*.html"))
    assert len(pages) == 11, f"expected 11 pages, got {len(pages)}"
    total_rows = total_links = 0
    for page in pages:
        parser = AuditParser()
        text = page.read_text(encoding="utf-8")
        parser.feed(text)
        assert parser.title and parser.h1, f"missing title/h1: {page.name}"
        assert not parser.has_none, f"placeholder leaked: {page.name}"
        assert not parser.unsourced, f"unsourced rows in {page.name}: {parser.unsourced}"
        for href in parser.links:
            parsed = urlparse(href)
            if parsed.scheme in {"https", "http"}:
                assert parsed.scheme == "https", f"non-HTTPS link {href}"
                continue
            if href.startswith(("#", "mailto:", "javascript:")):
                continue
            target = (page.parent / unquote(parsed.path)).resolve()
            assert ROOT.resolve() in target.parents or target == ROOT.resolve(), f"link escapes site: {href}"
            assert target.exists(), f"broken local link on {page.name}: {href}"
        total_rows += parser.rows
        total_links += len(parser.links)
        print(f"PASS {page.name}: {parser.rows} sourced rows / {len(parser.links)} links")
    summary = json.loads((ROOT / "data" / "summary.json").read_text())
    assert summary["audit_failures"] == 0 and summary["qualified"] == 0 and summary["rewards"] == 0
    for name in ("lines.csv", "strategies.csv", "correlations.csv", "leaderboard.csv", "flags.csv", "sources.csv", "audit_checks.csv"):
        with (ROOT / "data" / name).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert rows, name
        for i, row in enumerate(rows, 2):
            url = row.get("source_url") or row.get("url")
            assert url and urlparse(url).hostname in OFFICIAL, f"{name}:{i} lacks official source"
    assert total_rows >= 1100, f"unexpected incomplete tables: {total_rows}"
    print(f"ALL CHECKS PASSED: {len(pages)} pages, {total_rows} sourced body rows, {total_links} links, 0 broken internal links")


if __name__ == "__main__":
    main()

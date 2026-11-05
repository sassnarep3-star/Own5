#!/usr/bin/env python3
"""Check the new desk's static links, source-bearing rows and empty cells."""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from build import NAV, official_url

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.table_depth = 0
        self.row = None
        self.rows = []
        self.missing_cell = False
        self.missing_text = []
        self.empty_cells = []
        self.h1 = 0
        self.current_nav = 0

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if attr.get("id"):
            self.ids.append(attr["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "a" and attr.get("aria-current") == "page":
            self.current_nav += 1
        if tag in ("a", "link") and "href" in attr:
            self.links.append(attr["href"])
        if tag in ("script", "img") and "src" in attr:
            self.links.append(attr["src"])
        if tag == "table":
            self.table_depth += 1
        if tag == "tr" and self.table_depth and self.row is None:
            self.row = {"has_td": False, "links": []}
        if tag == "td" and self.row is not None:
            self.row["has_td"] = True
            if "missing" in attr.get("class", "").split():
                self.missing_cell = True
                self.missing_text = []
                if not attr.get("aria-label"):
                    self.empty_cells.append("missing accessible label")
        if tag == "a" and self.row is not None:
            self.row["links"].append(attr.get("href", ""))

    def handle_data(self, data):
        if self.missing_cell:
            self.missing_text.append(data)

    def handle_endtag(self, tag):
        if tag == "td" and self.missing_cell:
            if "".join(self.missing_text).strip():
                self.empty_cells.append("unverified cell contains text")
            self.missing_cell = False
        if tag == "tr" and self.row is not None:
            if self.row["has_td"]:
                self.rows.append(self.row)
            self.row = None
        if tag == "table":
            self.table_depth = max(0, self.table_depth - 1)


def check_site() -> dict:
    errors = []
    parsers = {}
    pages = [HERE / filename for filename, _, _ in NAV]
    for path in pages:
        if not path.is_file():
            errors.append(f"missing page: {path.name}")
            continue
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        parsers[path.resolve()] = parser
        if parser.h1 != 1:
            errors.append(f"{path.name}: expected exactly one h1")
        if parser.current_nav != 1:
            errors.append(f"{path.name}: expected exactly one current navigation item")
        if len(parser.ids) != len(set(parser.ids)):
            errors.append(f"{path.name}: duplicate IDs")
        if parser.empty_cells:
            errors.extend(f"{path.name}: {x}" for x in parser.empty_cells)
        if not parser.rows:
            errors.append(f"{path.name}: no data rows")
        for ordinal, row in enumerate(parser.rows, 1):
            if not any(official_url(link) for link in row["links"]):
                errors.append(f"{path.name}: data row {ordinal} lacks an official/context HTTPS link")

    local_count = 0
    for path, parser in parsers.items():
        for link in parser.links:
            if not link:
                continue
            parsed = urlparse(link)
            if parsed.scheme or parsed.netloc:
                continue  # External links are source-reviewed separately, not network-checked here.
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not target.is_relative_to(REPO.resolve()):
                errors.append(f"{path.name}: local link escapes repository: {link}")
                continue
            if target.is_dir():
                target = target / "index.html"
            if not target.is_file():
                errors.append(f"{path.name}: broken local link: {link}")
                continue
            local_count += 1
            if parsed.fragment and target.suffix == ".html":
                if target not in parsers:
                    other = PageParser()
                    other.feed(target.read_text(encoding="utf-8"))
                    ids = other.ids
                else:
                    ids = parsers[target].ids
                if unquote(parsed.fragment) not in ids:
                    errors.append(f"{path.name}: broken local fragment: {link}")
    return {"pages": len(parsers), "data_rows": sum(len(p.rows) for p in parsers.values()),
            "local_links": local_count, "errors": errors}


if __name__ == "__main__":
    result = check_site()
    if result["errors"]:
        print("\n".join(result["errors"]), file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS: {result['pages']} pages, {result['data_rows']} source-linked data rows, {result['local_links']} local links; no broken local links.")

#!/usr/bin/env python3
"""Audit generated HTML, official row links, local links and deterministic outputs."""
from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from build import NAV, build_pages
from model import OFFICIAL_HOSTS, ROOT, build_derived, load_data


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.rows: list[list[str]] = []
        self.in_tbody = False
        self.in_row = False
        self.current_row: list[str] = []
        self.scripts: list[str] = []
        self.title_depth = 0
        self.title = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if attrs_dict.get("id"):
            self.ids.add(attrs_dict["id"])
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_row = True
            self.current_row = []
        elif tag == "a" and attrs_dict.get("href"):
            href = attrs_dict["href"]
            self.links.append(href)
            if self.in_row:
                self.current_row.append(href)
        elif tag == "link" and attrs_dict.get("href"):
            self.links.append(attrs_dict["href"])
        elif tag == "script":
            self.scripts.append(attrs_dict.get("src") or "inline")
        elif tag == "title":
            self.title_depth = 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.in_row:
            self.rows.append(self.current_row)
            self.in_row = False
        elif tag == "tbody":
            self.in_tbody = False
        elif tag == "title":
            self.title_depth = 0

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title += data


def parse_page(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def audit() -> dict:
    data = load_data()
    derived = build_derived(data)
    committed_derived = json.loads((ROOT / "data" / "derived.json").read_text(encoding="utf-8"))
    assert committed_derived == derived, "derived.json is stale; run model.py/build.py"
    expected_pages = build_pages(data, derived)
    parsed = {}
    row_count = 0
    link_count = 0
    for filename, expected in expected_pages.items():
        path = ROOT / filename
        assert path.exists(), f"missing {filename}"
        assert path.read_text(encoding="utf-8") == expected, f"stale {filename}; run build.py"
        parser = parse_page(path)
        parsed[filename] = parser
        assert parser.title and "NBA Own Lines" in parser.title
        assert not parser.scripts, f"unexpected runtime script in {filename}"
        text = path.read_text(encoding="utf-8")
        assert "localhost" not in text and "127.0.0.1" not in text
        assert 'href="http://' not in text
        for row_links in parser.rows:
            row_count += 1
            official = [href for href in row_links if urlparse(href).scheme == "https" and urlparse(href).hostname in OFFICIAL_HOSTS]
            assert official, f"table row lacks official source in {filename}: {row_links}"
        for href in parser.links:
            link_count += 1
            if href.startswith(("https://", "#")):
                if href.startswith("#"):
                    assert href[1:] in parser.ids, f"broken fragment {href} in {filename}"
                continue
            assert not href.startswith(("http://", "javascript:")), f"unsafe link {href}"
            target, _, fragment = href.partition("#")
            target_path = (path.parent / target).resolve()
            assert target_path.exists(), f"broken internal link {href} in {filename}"
            assert ROOT in target_path.parents or target_path == ROOT, f"link escapes namespace: {href}"
            if fragment and target_path.suffix == ".html":
                target_parser = parsed.get(target_path.name) or parse_page(target_path)
                assert fragment in target_parser.ids, f"broken fragment {href}"
    assert len(expected_pages) == 11
    assert row_count == 199, f"unexpected table coverage: {row_count}"
    assert derived["metadata"]["team_rows"] == 30
    assert derived["metadata"]["schedule_rows"] == 16
    assert derived["metadata"]["player_game_rows"] == 26
    assert derived["metadata"]["qualified_strategies"] == 0
    assert derived["metadata"]["player_holm_rejections_005"] == 0
    assert len(derived["correlations"]) == 21 and len(derived["leaderboard"]) == 7
    assert len(derived["flags"]) == 11
    assert all(row["market_spread"] is None and row["market_total"] is None and row["edge"] is None for row in derived["lines"])
    assert all(row["playable_lines"] is None for row in derived["player_props"])
    assert all(row["joint_probability"] is None and row["payout"] is None for row in derived["prop_combos"])
    return {"pages": len(expected_pages), "table_rows": row_count, "links_checked": link_count, "lines": len(derived["lines"]), "qualified": 0}


if __name__ == "__main__":
    print("PASS " + json.dumps(audit(), sort_keys=True))

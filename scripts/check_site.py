"""Static-site integrity: internal links, fragments, assets, and row provenance."""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from nfl_model.contracts import official_url

DIST = ROOT / "dist"


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.assets: list[str] = []
        self.rows: list[list[str]] = []
        self.in_body_row = False
        self.current_row: list[str] = []
        self.table_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.in_body_row:
                self.current_row.append(a["href"])
        if tag in {"link", "script", "img"}:
            url = a.get("href") or a.get("src")
            if url:
                self.assets.append(url)
        if tag == "tbody":
            self.table_depth += 1
        if tag == "tr" and self.table_depth:
            self.in_body_row = True
            self.current_row = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.in_body_row:
            self.rows.append(self.current_row)
            self.in_body_row = False
        if tag == "tbody":
            self.table_depth -= 1


def main() -> None:
    if not DIST.exists():
        raise SystemExit("dist/ does not exist; run scripts/build_site.py first")
    pages: dict[Path, Page] = {}
    failures: list[str] = []
    row_count = 0
    for path in sorted(DIST.rglob("*.html")):
        text = path.read_text()
        parser = Page()
        parser.feed(text)
        pages[path.resolve()] = parser
        if "localhost" in text or "127.0.0.1" in text:
            failures.append(f"browser-facing loopback URL: {path.relative_to(DIST)}")
        for i, row in enumerate(parser.rows, 1):
            row_count += 1
            if not any(official_url(u) for u in row):
                failures.append(f"table row without official source: {path.relative_to(DIST)} row {i}")
    for path, parser in pages.items():
        for url in parser.links + parser.assets:
            parsed = urlparse(url)
            if parsed.scheme or parsed.netloc:
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not target.exists():
                failures.append(f"broken local link: {path.relative_to(DIST)} -> {url}")
                continue
            if parsed.fragment and target.suffix == ".html":
                target_parser = pages.get(target)
                if target_parser is None or parsed.fragment not in target_parser.ids:
                    failures.append(f"broken fragment: {path.relative_to(DIST)} -> {url}")
    if not (DIST / ".nojekyll").exists():
        failures.append("missing .nojekyll")
    if not (DIST / "index.html").exists():
        failures.append("missing landing page")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"PASS: {len(pages)} HTML pages; {row_count} data-table rows with official links; all internal links/fragments/assets resolve.")


if __name__ == "__main__":
    main()

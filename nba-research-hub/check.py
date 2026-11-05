"""Static-site and artifact integrity checks for the NBA Research Hub."""
from __future__ import annotations

import csv
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
ALLOWED_HOSTS = {
    "www.nba.com", "nba.com", "official.nba.com", "ak-static.cms.nba.com",
    "www.fanduel.com", "pubmed.ncbi.nlm.nih.gov", "www.itl.nist.gov",
    "www.davidhbailey.com", "github.com",
}


def trusted(url: str) -> bool:
    p = urlparse(url)
    if p.scheme not in {"http", "https"} or p.netloc not in ALLOWED_HOSTS:
        return False
    if p.netloc == "github.com" and not p.path.startswith("/sassnarep3-star/Own5"):
        return False
    return True


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.assets: list[str] = []
        self.rows: list[list[str]] = []
        self.row_texts: list[str] = []
        self.in_body_row = False
        self.current_row: list[str] = []
        self.current_text: list[str] = []
        self.table_depth = 0
        self.h1 = 0
        self.nav_links = 0
        self.in_nav = False
        self.blank_cells = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "nav":
            self.in_nav = True
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.in_nav:
                self.nav_links += 1
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
            self.current_text = []
        if tag == "span" and a.get("data-blank") == "true":
            self.blank_cells += 1

    def handle_data(self, data: str) -> None:
        if self.in_body_row:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "nav":
            self.in_nav = False
        if tag == "tr" and self.in_body_row:
            self.rows.append(self.current_row)
            self.row_texts.append(" ".join(self.current_text))
            self.in_body_row = False
        if tag == "tbody":
            self.table_depth -= 1


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    failures: list[str] = []
    pages: dict[Path, Page] = {}
    row_count = 0
    link_count = 0
    for path in sorted(ROOT.glob("*.html")):
        text = path.read_text(encoding="utf-8")
        parser = Page()
        parser.feed(text)
        pages[path.resolve()] = parser
        if parser.h1 != 1:
            failures.append(f"{path.name}: expected one h1, got {parser.h1}")
        if parser.nav_links != 13:
            failures.append(f"{path.name}: expected 13 nav links, got {parser.nav_links}")
        if "localhost" in text or "127.0.0.1" in text:
            failures.append(f"{path.name}: browser-facing loopback URL")
        for i, (row, rtext) in enumerate(zip(parser.rows, parser.row_texts), 1):
            row_count += 1
            if not any(trusted(u) for u in row):
                failures.append(f"{path.name} row {i}: no trusted official/source link")
            if "None" in rtext or "nan" in rtext.lower().split():
                failures.append(f"{path.name} row {i}: unrendered null/NaN text")
        link_count += len(parser.links) + len(parser.assets)
    for path, parser in pages.items():
        for url in parser.links + parser.assets:
            p = urlparse(url)
            if p.scheme or p.netloc:
                continue
            target = (path.parent / unquote(p.path)).resolve() if p.path else path
            if not target.exists():
                failures.append(f"broken local link: {path.name} -> {url}")
                continue
            if p.fragment and target.suffix == ".html":
                tp = pages.get(target)
                if tp is None or p.fragment not in tp.ids:
                    failures.append(f"broken fragment: {path.name} -> {url}")
    if len(pages) != 13:
        failures.append(f"expected 13 HTML pages, found {len(pages)}")
    if not (ROOT / ".nojekyll").exists():
        failures.append("missing .nojekyll")

    out = json.loads((ROOT / "data" / "derived" / "outputs.json").read_text(encoding="utf-8"))
    if out["summary"]["eligible_strategies"] != 0 or out["summary"]["graded_bets"] != 0:
        failures.append("unexpected eligible strategies or graded bets")
    if any(s["eligible"] for s in out["strategies"]):
        failures.append("a strategy is marked eligible despite blockers")
    if any(r["rank"] for r in out["leaderboard"]):
        failures.append("ineligible leaderboard entry has a rank")
    lines_page = pages.get((ROOT / "lines.html").resolve())
    if lines_page is None or lines_page.blank_cells < 27:
        failures.append("lines page missing blank market/odds flags")

    reqs = read_csv(ROOT / "data" / "requirements.csv")
    flags = read_csv(ROOT / "data" / "flags.csv")
    sources = read_csv(ROOT / "data" / "sources.csv")
    for name, rows, key in [("requirements", reqs, "req_id"), ("flags", flags, "flag_id"), ("sources", sources, "source_id")]:
        ids = [r[key] for r in rows]
        if len(ids) != len(set(ids)):
            failures.append(f"duplicate {name} IDs")
        if not all(trusted(r.get("source_url", r.get("url", ""))) for r in rows):
            failures.append(f"{name} row without trusted source link")

    field = read_csv(ROOT / "audit" / "field_audit.csv")
    if any(r["status"] == "MISMATCH" for r in field):
        failures.append("unexpected field audit mismatch")
    if any(r["status"] == "UNVERIFIED" and r["official_value"] != "" for r in field):
        failures.append("unverified field audit row has a filled official value")
    inv_summary = json.loads((ROOT / "audit" / "inventory_summary.json").read_text(encoding="utf-8"))
    line_inv = read_csv(ROOT / "audit" / "line_inventory.csv")
    file_inv = read_csv(ROOT / "audit" / "file_inventory.csv")
    if len(line_inv) != inv_summary["physical_lines"] or len(file_inv) != inv_summary["files"]:
        failures.append("inventory counts do not reconcile")
    if any(r["status"] not in {"INV", "LINK"} for r in line_inv):
        failures.append("line inventory uses an undefined status")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        raise SystemExit(1)
    print(f"PASS: {len(pages)} pages; {row_count} source-linked table rows; {link_count} links/assets checked; "
          f"{len(line_inv)} inventory lines; {len(field)} field comparisons; 0 eligible strategies; 0 graded bets.")


if __name__ == "__main__":
    main()

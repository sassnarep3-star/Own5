"""Fail-closed checks for the NFL integration hub and its source registers."""
from __future__ import annotations

import csv
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent

EXPECTED = {
    "sources.csv": ["source_id", "publisher", "title", "url", "checked_on", "verified_observation", "scope_limit"],
    "audit.csv": ["audit_id", "severity", "area", "observation", "decision_impact", "clearance_rule", "official_source_urls", "repository_evidence_urls", "source_status"],
    "questions.csv": ["question_id", "question", "known_from_verified_sources", "missing_information", "answer_needed_before_decision", "clearing_evidence", "official_source_urls", "repository_evidence_urls", "source_status"],
    "suggestions.csv": ["suggestion_id", "priority", "topic", "options", "recommended_path", "what_would_change_the_recommendation", "official_source_urls", "related_evidence_urls", "decision_status", "source_status"],
}
PAGES = ["index.html", "executive-summary.html", "audit.html", "questions.html", "suggestions.html", "leaderboard.html", "sources.html", "flagged.html"]
ALLOWED_HOSTS = {
    "nfl.com", "www.nfl.com", "media.nfl.com", "support.nfl.com", "static.www.nfl.com",
    "houstontexans.com", "www.houstontexans.com", "packers.com", "www.packers.com",
    "bengals.com", "www.bengals.com",
}

errors: list[str] = []
checks = 0


def check(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        errors.append(message)


def read_csv(name: str) -> list[dict[str, str]]:
    path = ROOT / "data" / name
    try:
        with path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            check(reader.fieldnames == EXPECTED[name], f"{name}: header mismatch: {reader.fieldnames}")
            rows = list(reader)
    except (OSError, csv.Error) as exc:
        errors.append(f"{name}: cannot read CSV: {exc}")
        return []
    check(bool(rows), f"{name}: has no data rows")
    for line_number, row in enumerate(rows, 2):
        check(None not in row and all(value is not None for value in row.values()), f"{name}:{line_number}: malformed CSV row")
        allowed_blank = {"official_source_urls"}
        check(all(value.strip() or field in allowed_blank for field, value in row.items()), f"{name}:{line_number}: required field is blank")
    return rows


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.open_rows = 0
        self.row_has_official = False
        self.table_rows_without_source = 0
        self.current_classes: list[str] = []
        self.source_links = 0
        self.missing_source_labels = 0
        self.in_thead = False
        self.links_by_class: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "thead":
            self.in_thead = True
        attrs_dict = dict(attrs)
        if tag == "a" and attrs_dict.get("href"):
            href = attrs_dict["href"] or ""
            self.hrefs.append(href)
            classes = attrs_dict.get("class", "") or ""
            self.links_by_class.append((classes, href))
            if "source-link" in classes.split():
                self.source_links += 1
                if self.open_rows:
                    self.row_has_official = True
        if tag == "span" and "source-missing" in (attrs_dict.get("class", "") or "").split():
            self.missing_source_labels += 1
            if self.open_rows:
                self.row_has_official = True
        if tag == "tr" and not self.in_thead:
            self.open_rows += 1
            self.row_has_official = False

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and not self.in_thead and self.open_rows:
            if not self.row_has_official:
                self.table_rows_without_source += 1
            self.open_rows -= 1
        if tag == "thead":
            self.in_thead = False


def main() -> int:
    registers = {name: read_csv(name) for name in EXPECTED}
    sources = registers["sources.csv"]
    audit = registers["audit.csv"]
    questions = registers["questions.csv"]
    suggestions = registers["suggestions.csv"]

    source_urls: dict[str, dict[str, str]] = {}
    source_ids: set[str] = set()
    for line_number, source in enumerate(sources, 2):
        check(source["source_id"] not in source_ids, f"sources.csv:{line_number}: duplicate source id {source['source_id']}")
        source_ids.add(source["source_id"])
        parsed = urlparse(source["url"])
        check(parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS, f"sources.csv:{line_number}: non-HTTPS or unapproved source host {source['url']}")
        check(re.fullmatch(r"2026-11-\d{2}", source["checked_on"]) is not None, f"sources.csv:{line_number}: invalid review date {source['checked_on']}")
        check(source["url"] not in source_urls, f"sources.csv:{line_number}: duplicate source URL")
        source_urls[source["url"]] = source
        check("http" not in source["scope_limit"].lower() or "https" in source["scope_limit"].lower(), f"sources.csv:{line_number}: suspicious URL warning")

    check(len(sources) == 18, f"expected 18 source records, found {len(sources)}")
    check(len(audit) == 13, f"expected 13 audit rows, found {len(audit)}")
    check(len(questions) == 10, f"expected 10 question rows, found {len(questions)}")
    check(len(suggestions) == 10, f"expected 10 suggestion rows, found {len(suggestions)}")

    for filename, rows in (("audit.csv", audit), ("questions.csv", questions), ("suggestions.csv", suggestions)):
        for line_number, row in enumerate(rows, 2):
            for field in ("official_source_urls",):
                for url in [part.strip() for part in row[field].split("|") if part.strip()]:
                    check(url in source_urls, f"{filename}:{line_number}: official URL missing from source register: {url}")
            evidence_field = "repository_evidence_urls" if "repository_evidence_urls" in row else "related_evidence_urls"
            for link in [part.strip() for part in row[evidence_field].split("|") if part.strip()]:
                target = (ROOT / link).resolve()
                check(target.exists(), f"{filename}:{line_number}: repository evidence path missing: {link}")
            if not row["official_source_urls"].strip():
                state = row["source_status"].lower()
                check("unverified" in state or "repository_state_only" in state, f"{filename}:{line_number}: blank official-source field is not explicitly flagged")

    sources_parser = Links()
    sources_parser.feed((ROOT / "sources.html").read_text(encoding="utf-8"))
    rendered_source_count = sum("source-link" in classes.split() for classes, _ in sources_parser.links_by_class)
    check(rendered_source_count == len(sources), "sources page does not render every source-register row")
    reviewed_text = " ".join(row.get("observation", row.get("known_from_verified_sources", "")) for row in audit + questions)
    check("2026-11-15T23:40Z" in reviewed_text, "leaderboard registration timestamp is missing from reviewed rows")
    chronology = next((row for row in audit if row["audit_id"] == "A62-01"), {})
    check("Week 10" in chronology.get("observation", "") and "not been audited" in chronology.get("observation", ""), "leaderboard chronology does not preserve the unresolved Week 10 overlap")

    for page_name in PAGES:
        path = ROOT / page_name
        check(path.is_file(), f"generated page missing: {page_name}")
        if not path.is_file():
            continue
        parser = Links()
        text = path.read_text(encoding="utf-8")
        parser.feed(text)
        check(parser.table_rows_without_source == 0, f"{page_name}: {parser.table_rows_without_source} table rows have neither an official-source link nor an explicit flagged source gap")
        for href in parser.hrefs:
            parsed = urlparse(href)
            if parsed.scheme or href.startswith("//") or href.startswith("#"):
                continue
            rel = unquote(parsed.path)
            if not rel:
                continue
            target = (path.parent / rel).resolve()
            if target.is_dir():
                target = target / "index.html"
            check(target.exists(), f"{page_name}: local link target is missing: {href}")
        for classes, href in parser.links_by_class:
            if "source-link" in classes.split():
                parsed = urlparse(href)
                check(parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS, f"{page_name}: source link is not an approved HTTPS URL: {href}")

    safe_board = (ROOT / "leaderboard.html").read_text(encoding="utf-8").lower()
    check("no strategy is ranked" in safe_board, "safe leaderboard does not state that no strategy is ranked")
    check("no historical hit rate" in safe_board, "safe leaderboard does not state that historical metrics are excluded")
    check("ranking locked" in safe_board, "safe leaderboard does not show the locked status")
    check(not re.search(r"\b\d+(?:\.\d+)?%", safe_board), "safe leaderboard contains a percentage performance metric")
    check("\u0024" not in safe_board and "roi " not in safe_board, "safe leaderboard contains a dollar amount or ROI metric")

    root_index = (REPO / "index.html").read_text(encoding="utf-8") if (REPO / "index.html").exists() else ""
    check("nfl-integration-a620f5a5/index.html" in root_index, "root landing page does not link to the integration hub")
    check((REPO / "README.md").is_file() and "nfl-integration-a620f5a5" in (REPO / "README.md").read_text(encoding="utf-8"), "README does not document the integration hub")

    if errors:
        print(f"FAIL: {len(errors)} issue(s) across {checks} checks")
        for error in errors:
            print(f" - {error}")
        return 1
    print(f"PASS: {checks} checks; {len(sources)} official-source records; {len(audit)} audit findings; {len(questions)} questions; {len(suggestions)} suggestions; {len(PAGES)} generated pages; no unflagged source gaps or broken local links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

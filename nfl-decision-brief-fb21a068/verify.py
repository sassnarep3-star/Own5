#!/usr/bin/env python3
"""Fail-closed checks for the scoped decision brief and its source register."""
from __future__ import annotations

import csv
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "data" / "decision_register.csv"
HTML_PATH = ROOT / "index.html"
OFFICIAL_HOSTS = {
    "nfl.com", "www.nfl.com", "media.nfl.com", "sportsbook.draftkings.com",
    "www.fanduel.com", "www.houstontexans.com", "www.igamingontario.ca",
}
REQUIRED = {
    "id", "kind", "priority", "area", "verified_finding", "unresolved_question",
    "minimum_evidence_to_clear", "recommendation", "what_would_change_our_mind",
    "status", "official_source_url", "repo_evidence_url",
}


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.rows = 0
        self.in_table_row = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "a" and attrs_dict.get("href"):
            self.hrefs.append(attrs_dict["href"] or "")
        if tag == "tr":
            self.rows += 1


def verify() -> list[str]:
    errors: list[str] = []
    if not CSV_PATH.exists():
        return [f"missing {CSV_PATH.relative_to(ROOT)}"]
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if set(reader.fieldnames or []) != REQUIRED:
            errors.append("decision_register.csv headers do not match the required schema")
            return errors
        rows = list(reader)
    if len(rows) != 12:
        errors.append(f"expected 12 register rows, found {len(rows)}")
    seen: set[str] = set()
    for line, row in enumerate(rows, start=2):
        if not row["id"] or row["id"] in seen:
            errors.append(f"line {line}: blank or duplicate ID {row['id']!r}")
        seen.add(row["id"])
        expected_kind = "Question" if row["id"].startswith("D") else "Suggestion"
        if row["kind"] != expected_kind:
            errors.append(f"line {line}: invalid kind for {row['id']}")
        for field in REQUIRED - {"repo_evidence_url"}:
            if not row[field].strip():
                errors.append(f"line {line}: {field} is blank for {row['id']}")
        src = urlparse(row["official_source_url"])
        if src.scheme != "https" or src.hostname not in OFFICIAL_HOSTS:
            errors.append(f"line {line}: source is not an allow-listed official HTTPS URL: {row['official_source_url']}")
        evidence = row["repo_evidence_url"]
        if not evidence:
            errors.append(f"line {line}: missing repository evidence link for {row['id']}")
        elif not evidence.startswith("../"):
            errors.append(f"line {line}: evidence link must be a root-relative sibling path: {evidence}")
        else:
            local = (ROOT / evidence).resolve()
            repo = ROOT.parent.resolve()
            if not local.is_relative_to(repo) or not local.exists():
                errors.append(f"line {line}: missing or unsafe repo evidence link: {evidence}")
        if row["kind"] == "Question" and not row["unresolved_question"].strip():
            errors.append(f"line {line}: question text missing for {row['id']}")
        if row["kind"] == "Suggestion" and row["status"] != "Proposed":
            errors.append(f"line {line}: suggestion {row['id']} must remain explicitly proposed")
    if not HTML_PATH.exists():
        errors.append("generated index.html is missing; run python3 build.py")
    else:
        parser = Links()
        parser.feed(HTML_PATH.read_text(encoding="utf-8"))
        html_text = HTML_PATH.read_text(encoding="utf-8")
        if parser.rows != len(rows) + 2:
            # Each data table has one header row; count explicit data rows below instead.
            data_rows = html_text.count('<tr><th scope="row">')
            if data_rows != len(rows):
                errors.append(f"HTML contains {data_rows} data rows; expected {len(rows)}")
        for row in rows:
            for link in (row["official_source_url"], row["repo_evidence_url"]):
                if link not in parser.hrefs:
                    errors.append(f"generated HTML omits a register link: {link}")
        for href in parser.hrefs:
            if href.startswith("../"):
                local = (ROOT / href.split("#", 1)[0]).resolve()
                if not local.exists():
                    errors.append(f"broken relative link in generated page: {href}")
    return errors


def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: 12 source-linked register rows, official HTTPS sources, repository evidence, and local page links verified")
    print("Scope note: source links are structurally checked; current page contents must be re-read when the review date changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

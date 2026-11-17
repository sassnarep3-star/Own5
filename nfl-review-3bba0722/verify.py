#!/usr/bin/env python3
"""Fail-closed validation for the generated NFL decision-review subsite."""
from __future__ import annotations

import hashlib
import html.parser
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DATA = ROOT / "data"
PAGES = ["index.html", "questions.html", "suggestions.html", "flagged.html", "sources.html", "summary.html"]
ALLOWED_HOSTS = (
    "nfl.com",
    "houstontexans.com",
    "packers.com",
    "fanduel.com",
    "weather.gov",
)


def read_json(name: str):
    with (DATA / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PageAudit(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []
        self.table_rows: list[dict[str, object]] = []
        self._in_tbody = False
        self._row: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.add(str(attributes["id"]))
        if tag == "tbody":
            self._in_tbody = True
        if tag == "tr" and self._in_tbody:
            self._row = {"links": [], "text": []}
        if tag == "a":
            href = attributes.get("href")
            if href:
                self.links.append(str(href))
                if self._row is not None:
                    self._row["links"].append(str(href))  # type: ignore[union-attr]

    def handle_data(self, data: str) -> None:
        if self._row is not None:
            self._row["text"].append(data)  # type: ignore[union-attr]

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self._row is not None:
            self.table_rows.append(self._row)
            self._row = None
        if tag == "tbody":
            self._in_tbody = False


def parse_page(path: Path) -> PageAudit:
    parser = PageAudit()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def validate_sources() -> tuple[int, list[str]]:
    errors: list[str] = []
    sources = read_json("sources.json")
    seen: set[str] = set()
    for source in sources:
        source_id = source.get("id", "")
        if not source_id or source_id in seen:
            errors.append(f"duplicate or empty source id: {source_id!r}")
        seen.add(source_id)
        url = source.get("url", "")
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not any(host == domain or host.endswith("." + domain) for domain in ALLOWED_HOSTS):
            errors.append(f"source {source_id} is not an HTTPS official-domain URL: {url}")
        if not source.get("checked_on") or not source.get("verification_status") or not source.get("observation"):
            errors.append(f"source {source_id} is missing check date/status/observation")
    return len(sources), errors


def validate_registers() -> tuple[int, list[str]]:
    errors: list[str] = []
    sources = {source["id"] for source in read_json("sources.json")}
    registers = {
        "questions.json": read_json("questions.json"),
        "suggestions.json": read_json("suggestions.json"),
        "flagged.json": read_json("flagged.json"),
        "readiness.json": read_json("readiness.json"),
    }
    count = 0
    for filename, rows in registers.items():
        ids: set[str] = set()
        for row in rows:
            count += 1
            row_id = row.get("id") or row.get("flag_id")
            if not row_id or row_id in ids:
                errors.append(f"{filename}: duplicate or empty row id {row_id!r}")
            ids.add(row_id)
            row_sources = row.get("source_ids", [])
            if not row_sources:
                status = str(row.get("status", row.get("decision_status", ""))).upper()
                if "UNVERIFIED" not in status and "UNKNOWN" not in status:
                    errors.append(f"{filename} {row_id}: no source id and no UNVERIFIED/UNKNOWN status")
            for source_id in row_sources:
                if source_id not in sources:
                    errors.append(f"{filename} {row_id}: unknown source id {source_id}")
            evidence = row.get("repo_evidence", [])
            if not isinstance(evidence, list):
                errors.append(f"{filename} {row_id}: repo_evidence must be a list")
            if filename == "suggestions.json":
                if len(row.get("options", [])) < 2:
                    errors.append(f"suggestion {row_id}: fewer than two options")
                for field in ("recommendation", "review_test", "what_would_change_our_mind", "decision_status"):
                    if not row.get(field):
                        errors.append(f"suggestion {row_id}: missing {field}")
                if "AWAITING REVIEW" not in row["decision_status"].upper():
                    errors.append(f"suggestion {row_id}: review docket row is not awaiting review")
            if filename == "questions.json":
                for field in ("question", "verified_answer", "missing_information", "blocking_gate", "clearance_number"):
                    if not row.get(field):
                        errors.append(f"question {row_id}: missing {field}")
            if filename == "readiness.json":
                if row.get("observed_value") not in (None, ""):
                    errors.append(f"readiness {row_id}: unconfirmed observed_value must stay blank")
                for field in ("blocking_gate", "clear_when", "observed_note"):
                    if not row.get(field):
                        errors.append(f"readiness {row_id}: missing {field}")
    return count, errors


def validate_html_tables() -> tuple[int, list[str]]:
    errors: list[str] = []
    row_count = 0
    for page_name in PAGES:
        path = ROOT / page_name
        if not path.is_file():
            errors.append(f"generated page missing: {page_name}")
            continue
        audit = parse_page(path)
        for index, row in enumerate(audit.table_rows, start=1):
            row_count += 1
            links = row["links"]
            text = " ".join(row["text"])
            external = [link for link in links if urlsplit(link).scheme in ("https", "http")]
            if not external and "UNVERIFIED" not in text.upper():
                errors.append(f"{page_name} table row {index} has neither an official-source link nor UNVERIFIED")
            for link in external:
                parsed = urlsplit(str(link))
                host = (parsed.hostname or "").lower()
                if parsed.scheme != "https" or not any(host == domain or host.endswith("." + domain) for domain in ALLOWED_HOSTS):
                    errors.append(f"{page_name} table row {index} has a non-approved external source {link}")
    return row_count, errors


def validate_local_links() -> tuple[int, list[str]]:
    errors: list[str] = []
    checked = 0
    for page_name in PAGES:
        page_path = ROOT / page_name
        if not page_path.is_file():
            continue
        audit = parse_page(page_path)
        for href in audit.links:
            parsed = urlsplit(href)
            if parsed.scheme or href.startswith("//"):
                continue
            checked += 1
            relative = unquote(parsed.path)
            if not relative:
                target = page_path
            else:
                target = (page_path.parent / relative).resolve()
            if not target.exists():
                errors.append(f"{page_name}: broken local link {href}")
                continue
            if parsed.fragment and target.suffix.lower() in {".html", ".htm"}:
                target_ids = parse_page(target).ids
                if unquote(parsed.fragment) not in target_ids:
                    errors.append(f"{page_name}: missing anchor #{parsed.fragment} in {relative or page_name}")
    return checked, errors


def verify_deterministic_build() -> list[str]:
    errors: list[str] = []
    before = {name: sha256(ROOT / name) for name in PAGES if (ROOT / name).exists()}
    result = subprocess.run(
        [sys.executable, str(ROOT / "build_site.py")],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        return [f"build failed: {result.stderr.strip() or result.stdout.strip()}"]
    after = {name: sha256(ROOT / name) for name in PAGES if (ROOT / name).exists()}
    if before and before != after:
        changed = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))
        errors.append(f"site build is not deterministic; changed: {', '.join(changed)}")
    return errors


def run_checks() -> list[str]:
    errors = []
    errors.extend(verify_deterministic_build())
    _, found = validate_sources()
    errors.extend(found)
    _, found = validate_registers()
    errors.extend(found)
    _, found = validate_html_tables()
    errors.extend(found)
    _, found = validate_local_links()
    errors.extend(found)
    return errors


def main() -> int:
    source_count, source_errors = validate_sources()
    register_count, register_errors = validate_registers()
    page_rows, table_errors = validate_html_tables()
    local_links, link_errors = validate_local_links()
    deterministic_errors = verify_deterministic_build()
    errors = source_errors + register_errors + table_errors + link_errors + deterministic_errors
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"FAILED: {len(errors)} issue(s).", file=sys.stderr)
        return 1
    print(
        f"PASS: {source_count} official-source records; {register_count} register rows; "
        f"{page_rows} table rows source-linked/flagged; {local_links} local links; "
        "deterministic rebuild; 0 failures."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

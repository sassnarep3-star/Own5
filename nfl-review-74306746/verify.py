#!/usr/bin/env python3
"""Fail-closed checks for the isolated NFL cross-desk review.

The verifier reads local repository files and validates URLs structurally. It
never requests NFL, club, operator, GitHub Pages or other external webpages.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import html.parser
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

SITE = Path(__file__).resolve().parent
REPO = SITE.parent
RESEARCH = REPO / "research" / "nfl-review-74306746"
EXPECTED_SNAPSHOT = "2f02e1e7975ee61780b39e1ef9bc83591ccb55e2"
PAGES = (
    "index.html",
    "readiness.html",
    "sources.html",
    "questions.html",
    "suggestions.html",
    "flagged.html",
)
ALLOWED_HOSTS = {
    "www.nfl.com",
    "nfl.com",
    "static.www.nfl.com",
    "media.nfl.com",
    "sportsbook.fanduel.com",
    "github.com",
    "nflverse.nflreadr.com",
    "sassnarep3-star.github.io",
}


class AuditParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.h1 = 0
        self.title = 0
        self.rows: list[str] = []
        self._row: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self.title += 1
        if tag == "tr":
            self._row = [tag]
        elif self._row is not None:
            self._row.append(tag)
            if tag == "a" and attrs.get("class") and "official-source" in attrs["class"].split():
                self._row.append("OFFICIAL_SOURCE_LINK")
            if tag == "span" and attrs.get("class") and "source-gap" in attrs["class"].split():
                self._row.append("FLAGGED_SOURCE_GAP")

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self._row is not None:
            self.rows.append(" ".join(self._row))
            self._row = None
        elif self._row is not None:
            self._row.append("/" + tag)


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def evidence_paths(records: list[dict]) -> list[str]:
    out: list[str] = []
    for item in records:
        for entry in item.get("evidence", []):
            out.append(entry["path"])
    return out


def check_url(url: str, label: str, errors: list[str]) -> None:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https":
        errors.append(f"{label}: URL must use HTTPS: {url}")
    if host not in ALLOWED_HOSTS:
        errors.append(f"{label}: unexpected host {host!r}: {url}")


def validate_data() -> tuple[dict[str, int], list[str]]:
    errors: list[str] = []
    summary = read_json(RESEARCH / "summary.json")
    sources = read_json(RESEARCH / "source-coverage.json")
    readiness = read_json(RESEARCH / "readiness.json")
    questions = read_json(RESEARCH / "questions.json")
    suggestions = read_json(RESEARCH / "suggestions.json")
    flags = read_json(RESEARCH / "flagged.json")

    if summary.get("evidence_snapshot") != EXPECTED_SNAPSHOT:
        errors.append("summary: evidence_snapshot must remain the reviewed base commit")
    if "No official or operator webpage was fetched" not in summary.get("freshness_notice", ""):
        errors.append("summary must disclose that no official/operator page was fetched")
    if not sources or not readiness or not questions or not suggestions or not flags:
        errors.append("all review registers must contain at least one row")

    source_ids = [item.get("id") for item in sources]
    if len(source_ids) != len(set(source_ids)):
        errors.append("source-coverage IDs are not unique")
    if len(readiness) != 10:
        errors.append(f"expected 10 readiness rows, found {len(readiness)}")
    for group_name, records in (("source", sources), ("readiness", readiness),
                                ("question", questions), ("suggestion", suggestions)):
        for i, item in enumerate(records, start=1):
            url = item.get("official_url", "")
            if not url:
                errors.append(f"{group_name} row {i} has no official source URL and is not explicitly blank+flagged")
            else:
                check_url(url, f"{group_name} row {i}", errors)
            if item.get("primary_url"):
                check_url(item["primary_url"], f"{group_name} row {i} primary source", errors)
            for entry in item.get("evidence", []):
                path = entry.get("path", "")
                evidence = REPO / path
                if not path or not evidence.exists():
                    errors.append(f"{group_name} row {i} repository evidence missing: {path}")
    for i, item in enumerate(flags, start=1):
        links = item.get("official_sources", [])
        if not links:
            errors.append(f"flag row {i} has no official-source reference; explicitly blank and flag if unavailable")
        for source in links:
            check_url(source.get("url", ""), f"flag row {i}", errors)
        for path in evidence_paths([item]):
            if not (REPO / path).exists():
                errors.append(f"flag row {i} repository evidence missing: {path}")
    for item in suggestions:
        if not item.get("would_change_our_mind_up") or not item.get("would_change_our_mind_down"):
            errors.append(f"suggestion {item.get('id')} must state two-sided change conditions")
        if not item.get("status", "").startswith("AWAITING OWNER REVIEW"):
            errors.append(f"suggestion {item.get('id')} is not clearly review-only")
    for item in questions:
        if not item.get("answer_status") or not item.get("missing_information") or not item.get("route"):
            errors.append(f"question {item.get('id')} lacks answer state, missing information or discovery route")
    for item in flags:
        if not item.get("status", "").startswith("OPEN"):
            errors.append(f"flag {item.get('id')} is not clearly open")

    metrics = inspect_repository(errors)
    return {
        "sources": len(sources),
        "readiness": len(readiness),
        "questions": len(questions),
        "suggestions": len(suggestions),
        "flags": len(flags),
        **metrics,
    }, errors


def inspect_repository(errors: list[str] | None = None) -> dict[str, int]:
    """Reproduce the cross-desk counts/discrepancies described in the report."""
    if errors is None:
        errors = []

    cmd_req = read_csv(REPO / "nfl-command-desk/data/requirements.csv")
    market_req = read_csv(REPO / "nfl-market-desk/data/requirements.csv")
    cmd_orig = read_csv(REPO / "nfl-command-desk/data/origination_wk11.csv")
    cmd_fixtures = read_csv(REPO / "nfl-command-desk/data/fixtures_wk11.csv")
    lines_35 = read_csv(REPO / "nfl-desk-35fc3437/data/lines_originated_wk11.csv")
    market_orig = read_csv(REPO / "nfl-market-desk/data/originated_markets.csv")
    engine_prices = read_csv(REPO / "nfl-engine-39086ec8/data/price_snapshots.csv")
    market_prices = read_csv(REPO / "nfl-market-desk/data/price_snapshots.csv")
    roster = read_csv(REPO / "nfl-market-desk/data/roster_sweep_32.csv")
    market_readiness = read_csv(REPO / "nfl-market-desk/data/decision_readiness.csv")
    game_results = read_csv(REPO / "data/nfl-desk-f2e20e96/week10_results.csv")
    starters = read_csv(REPO / "data/nfl-desk-f2e20e96/starters_jax_ten.csv")
    inactives = read_csv(REPO / "data/nfl-desk-f2e20e96/inactives_jax_ten.csv")
    cmd_results = read_csv(REPO / "nfl-command-desk/data/results_corpus.csv")
    market_results = read_csv(REPO / "nfl-market-desk/data/results_feed.csv")
    snap_path = REPO / "data/decision-desk/raw/snap_counts_2026.csv.gz"
    with gzip.open(snap_path, "rt", encoding="utf-8-sig", newline="") as handle:
        aggregator_snaps = list(csv.DictReader(handle))
    aggregator_games = {row.get("game_id", "") for row in aggregator_snaps}
    aggregator_teams = {row.get("team", "") for row in aggregator_snaps}
    aggregator_weeks = {int(row["week"]) for row in aggregator_snaps if row.get("week", "").isdigit()}

    expected_counts = {
        "command_requirements": (len(cmd_req), 73),
        "market_requirements": (len(market_req), 78),
        "command_origination_rows": (len(cmd_orig), 12),
        "command_fixture_game_rows": (sum(bool(r.get("away") and r.get("home")) for r in cmd_fixtures), 13),
        "origination_35fc_game_rows": (len(lines_35), 13),
        "market_originated_rows": (len(market_orig), 39),
        "engine_price_rows": (len(engine_prices), 78),
        "roster_sweep_rows": (len(roster), 32),
        "week10_gamebook_rows": (len(game_results), 14),
        "week10_starter_rows": (len(starters), 44),
        "week10_inactive_rows": (len(inactives), 12),
        "aggregator_snap_rows": (len(aggregator_snaps), 12693),
        "command_results_rows": (len(cmd_results), 150),
        "market_results_rows": (len(market_results), 145),
    }
    for label, (actual, expected) in expected_counts.items():
        if actual != expected:
            errors.append(f"{label}: expected {expected}, found {actual}")

    aggregator_game_types = {row.get("game_type", "") for row in aggregator_snaps}
    if len(aggregator_games) != 136 or len(aggregator_teams) != 32 or aggregator_weeks != set(range(1, 10)) or aggregator_game_types != {"REG"}:
        errors.append("nflverse snap-count snapshot scope changed; re-review its weeks 1-9 limitation")
    provenance = read_json(REPO / "data/decision-desk/raw/provenance.json")
    snap_asset = next((asset for asset in provenance.get("assets", []) if asset.get("asset") == snap_path.name), None)
    snap_hash = hashlib.sha256(snap_path.read_bytes()).hexdigest()
    if not snap_asset or snap_asset.get("sha256") != snap_hash or snap_asset.get("bytes") != snap_path.stat().st_size:
        errors.append("nflverse snap-count file no longer matches its local provenance manifest")
    if not provenance.get("retrieved_utc", "").startswith("2026-11-12T"):
        errors.append("nflverse snap-count retrieval date changed; re-review the staleness wording")
    source_records = read_csv(REPO / "data/decision-desk/sources.csv")
    snap_source = next((row for row in source_records if row.get("id") == "S-05"), None)
    if not snap_source or snap_source.get("tier") != "AGGREGATOR":
        errors.append("decision-desk snap-count source tier changed; re-review the official/aggregator distinction")

    engine_status = Counter(r.get("status", "") for r in engine_prices)
    engine_event = Counter(r.get("event", "") for r in engine_prices)
    engine_time = {r.get("captured_at_utc", "") for r in engine_prices}
    engine_games = {r.get("game_id", "") for r in engine_prices}
    engine_ops = {r.get("source_operator", "") for r in engine_prices}
    engine_regions = {r.get("source_region", "") for r in engine_prices}
    if engine_status != {"VERIFIED": 78}:
        errors.append(f"engine price statuses changed: {engine_status}")
    if engine_event != {"close": 78}:
        errors.append(f"engine price events are not all close-labelled: {engine_event}")
    if engine_time != {"2026-11-14T12:00:00Z"}:
        errors.append(f"engine price timestamps changed: {engine_time}")
    if len(engine_games) != 13 or engine_ops != {"FanDuel"} or engine_regions != {"US-UNSPECIFIED"}:
        errors.append("engine price game/operator/region scope changed")

    archive_hashes: dict[str, set[str]] = {}
    for row in engine_prices:
        archive_hashes.setdefault(row["archive_path"], set()).add(row["raw_sha256"])
    if len(archive_hashes) != 13:
        errors.append(f"expected 13 unique engine price archives, found {len(archive_hashes)}")
    for relative, expected in archive_hashes.items():
        path = REPO / relative
        if not path.is_file():
            errors.append(f"engine price archive missing: {relative}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected != {actual}:
            errors.append(f"engine price archive hash mismatch: {relative}")
    sample_archive = (REPO / "nfl-engine-39086ec8/data/archive/NE-DET.txt")
    if sample_archive.exists():
        text = sample_archive.read_text(encoding="utf-8")
        if "Reading note:" not in text or "transcribed exactly" not in text:
            errors.append("engine sample archive no longer matches the described text-summary format")
    engine_doc = (REPO / "nfl-engine-39086ec8/engine_price.py").read_text(encoding="utf-8")
    if "EMPTY-BY-DESIGN" not in engine_doc:
        errors.append("engine price-store documentation no longer contains the empty-by-design statement")

    market_types = Counter(r.get("snapshot_type", "") for r in market_prices)
    for required, expected in (("MARKET_OPEN", 39), ("MARKET_CLOSE", 39)):
        rows = [r for r in market_prices if r.get("snapshot_type") == required]
        populated = sum(bool(r.get("line_value") or r.get("price_american")) for r in rows)
        if len(rows) != expected or populated != 0:
            errors.append(f"market price {required}: expected {expected} empty rows, found {len(rows)} rows / {populated} populated")
    if market_types.get("MARKET_REFERENCE") != 39:
        errors.append("market desk reference-line row count changed")

    roster_counts = [r for r in roster if r.get("roster_rows_captured", "").strip()]
    roster_urls = [r for r in roster if r.get("roster_url", "").strip()]
    if len(roster_counts) != 1 or len(roster_urls) != 1 or roster_counts[0].get("club") != "NE":
        errors.append("roster sweep no longer reproduces the one-populated-row discrepancy")
    r13 = next((r for r in market_readiness if r.get("requirement_id") == "R-13"), None)
    if not r13 or "32/32" not in (r13.get("current_number", "") + r13.get("what_would_clear_it", "")):
        errors.append("market-desk R-13 statement is missing or changed; re-review the finding")

    game_ids = {(r.get("away", "").upper(), r.get("home", "").upper()) for r in cmd_fixtures if r.get("away") and r.get("home")}
    orig_ids = {(r.get("away", "").upper(), r.get("home", "").upper()) for r in cmd_orig}
    if ("AZ", "KC") not in game_ids or ("AZ", "KC") in orig_ids:
        errors.append("command-desk AZ-KC fixture/origination mismatch changed; re-review the finding")
    if not any(r.get("away_abbr") == "AZ" and r.get("home_abbr") == "KC" for r in lines_35):
        errors.append("35fc3437 comparison no longer contains AZ-KC; re-review the finding")
    if len({r.get("game_id") for r in market_orig}) != 13:
        errors.append("market desk no longer contains 13 unique Week 11 games")

    if sum(bool(r.get("game_book_url", "").strip()) for r in game_results) != 14:
        errors.append("Week 10 result table must keep 14 Game Book URLs")
    if {r.get("club") for r in starters} != {"JAX", "TEN"}:
        errors.append("starter extraction scope changed; re-review the coverage statement")
    if {r.get("club") for r in inactives} != {"JAX", "TEN"}:
        errors.append("inactive extraction scope changed; re-review the coverage statement")

    metrics = {
        "engine_snapshots": len(engine_prices),
        "engine_games": len(engine_games),
        "engine_archives": len(archive_hashes),
        "rosters_populated": len(roster_counts),
        "command_week11_rows": len(cmd_orig),
        "week11_fixture_games": len(game_ids),
        "week10_gamebooks": len(game_results),
        "week10_starter_rows": len(starters),
        "week10_inactive_rows": len(inactives),
        "aggregator_snap_rows": len(aggregator_snaps),
        "aggregator_snap_games": len(aggregator_games),
        "aggregator_snap_teams": len(aggregator_teams),
        "aggregator_snap_week_max": max(aggregator_weeks),
        "command_results": len(cmd_results),
        "market_results": len(market_results),
    }
    return metrics


def validate_pages() -> tuple[int, int, list[str]]:
    errors: list[str] = []
    page_count = 0
    row_count = 0
    for page_name in PAGES:
        path = SITE / page_name
        if not path.is_file():
            errors.append(f"generated page missing: {page_name}")
            continue
        page_count += 1
        text = path.read_text(encoding="utf-8")
        parser = AuditParser()
        parser.feed(text)
        if parser.h1 != 1:
            errors.append(f"{page_name}: expected one h1, found {parser.h1}")
        if parser.title != 1:
            errors.append(f"{page_name}: expected one title, found {parser.title}")
        for link in parser.links:
            parsed = urlsplit(link)
            if parsed.scheme:
                if parsed.scheme != "https":
                    errors.append(f"{page_name}: non-HTTPS external URL {link}")
                elif (parsed.hostname or "").lower() not in ALLOWED_HOSTS:
                    errors.append(f"{page_name}: unapproved external host in {link}")
                continue
            if link.startswith("#"):
                anchor = unquote(link[1:])
                if anchor and anchor not in parser.ids:
                    errors.append(f"{page_name}: missing fragment target {link}")
                continue
            target_path = unquote(parsed.path)
            target = (path.parent / target_path).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{page_name}: broken local link {link}")
        for row in parser.rows:
            if "td" not in row:
                continue
            row_count += 1
            if "OFFICIAL_SOURCE_LINK" not in row and "FLAGGED_SOURCE_GAP" not in row:
                errors.append(f"{page_name}: factual table row has no official source link or explicit flagged blank")
    css = SITE / "assets/style.css"
    if not css.is_file():
        errors.append("site stylesheet is missing")
    return page_count, row_count, errors


def main() -> int:
    metrics, errors = validate_data()
    pages, rows, page_errors = validate_pages()
    errors.extend(page_errors)
    if errors:
        print(f"NFL REVIEW VERIFY FAILED — {len(errors)} issue(s)")
        for error in errors:
            print("  FAIL:", error)
        return 1
    print(
        "NFL REVIEW VERIFY PASSED — "
        f"{pages} pages, {rows} cited table rows; "
        f"{metrics['sources']} source groups, {metrics['readiness']} readiness rows, "
        f"{metrics['questions']} questions, {metrics['suggestions']} suggestions, {metrics['flags']} flags."
    )
    print(
        "Reproduced repo-only discrepancies: "
        f"{metrics['engine_snapshots']} close-labelled engine rows / {metrics['engine_archives']} hash-matching text archives; "
        f"market desk open/close rows empty; {metrics['rosters_populated']}/32 roster rows populated; "
        f"command origination {metrics['command_week11_rows']}/{metrics['week11_fixture_games']} fixtures; "
        f"{metrics['week10_gamebooks']} Week 10 Game Book references, with 44 starters / 12 inactives extracted for JAX–TEN only; "
        f"nflverse aggregator snap counts {metrics['aggregator_snap_rows']} rows / {metrics['aggregator_snap_games']} games through REG Week {metrics['aggregator_snap_week_max']}."
    )
    print("No external requests were made; passing means the review reproduces repository evidence, not external source truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Verify the f5ce620e evidence dossier without fetching live sources."""
from __future__ import annotations

import csv
import gzip
import hashlib
import html.parser
from collections import Counter
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402


class Checks:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.passes: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if condition:
            self.passes.append(message)
        else:
            self.errors.append(message)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_repo_path(relative: str) -> Path:
    return (ROOT / relative).resolve()


def ids_for(items: list[dict], key: str) -> list[str]:
    return [str(value) for item in items for value in item.get(key, [])]


def utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError(f"timestamp has no UTC offset: {value}")
    return parsed


class HtmlAuditParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.anchors: set[str] = set()
        self.table_rows = 0
        self.rows_without_link = 0
        self._in_tbody = False
        self._in_row = False
        self._row_has_link = False
        self.external_target_errors: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_dict = dict(attrs)
        if tag == "tbody":
            self._in_tbody = True
        if tag == "tr" and self._in_tbody:
            self.table_rows += 1
            self._in_row = True
            self._row_has_link = False
        if "id" in attrs_dict:
            self.anchors.add(attrs_dict["id"])
        if tag == "a" and attrs_dict.get("href"):
            href = attrs_dict["href"]
            self.links.append((href, attrs_dict.get("rel", "")))
            if self._in_row:
                self._row_has_link = True
            if attrs_dict.get("target") == "_blank":
                rel_tokens = set(attrs_dict.get("rel", "").lower().split())
                if not {"noopener", "noreferrer"}.issubset(rel_tokens):
                    self.external_target_errors.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self._in_row:
            if not self._row_has_link:
                self.rows_without_link += 1
            self._in_row = False
            self._row_has_link = False
        if tag == "tbody":
            self._in_tbody = False


def validate_source_registry(checks: Checks, sources: list[dict]) -> dict[str, dict]:
    source_ids = [item.get("id", "") for item in sources]
    checks.require(len(source_ids) == len(set(source_ids)), "source IDs are unique")
    known = set(source_ids)
    for item in sources:
        checks.require(bool(re.fullmatch(r"SRC(?:-VEN)?-[A-Z0-9-]+", item.get("id", ""))), f"source ID format: {item.get('id')}")
        checks.require(item.get("url", "").startswith("https://"), f"HTTPS source URL: {item.get('id')}")
        checks.require(bool(item.get("source_class")), f"explicit source class: {item.get('id')}")
        checks.require(bool(item.get("scope_limit")), f"source scope limit: {item.get('id')}")
        checks.require(bool(item.get("read_window_utc")), f"source read window / inherited timestamp: {item.get('id')}")
        raw_ref = resolve_repo_path(item.get("raw_ref", ""))
        checks.require(raw_ref.is_file(), f"source local reference exists: {item.get('id')} -> {item.get('raw_ref')}")
    return {item["id"]: item for item in sources}


def validate_review_records(checks: Checks, sources: dict[str, dict], findings: list[dict], questions: list[dict], suggestions: list[dict]) -> None:
    finding_ids = [item.get("id", "") for item in findings]
    checks.require(len(finding_ids) == len(set(finding_ids)), "finding IDs are unique")
    known_findings = set(finding_ids)
    for item in findings:
        checks.require(bool(item.get("claim_checked")), f"finding {item['id']} states claim checked")
        checks.require(bool(item.get("observed")), f"finding {item['id']} has observed evidence")
        checks.require(bool(item.get("not_verified")), f"finding {item['id']} states what is not verified")
        checks.require(bool(item.get("decision_effect")), f"finding {item['id']} states decision effect")
        checks.require(bool(item.get("gate")) and bool(item.get("clearance_number")), f"finding {item['id']} has a clearance gate")
        checks.require(bool(item.get("source_ids")), f"finding {item['id']} has source links")
        for source_id in item.get("source_ids", []):
            checks.require(source_id in sources, f"finding {item['id']} source exists: {source_id}")
        for evidence in item.get("repo_evidence", []):
            checks.require(resolve_repo_path(evidence.get("path", "")).is_file(), f"finding {item['id']} evidence exists: {evidence.get('path')}")
    for item in questions:
        checks.require(bool(item.get("question")) and bool(item.get("answer_status")), f"question {item.get('id')} has text/status")
        checks.require(bool(item.get("owner_decision")), f"question {item.get('id')} states decision owner")
        checks.require(bool(item.get("source_ids")), f"question {item.get('id')} has source links")
        for source_id in item.get("source_ids", []):
            checks.require(source_id in sources, f"question {item['id']} source exists: {source_id}")
        for finding_id in item.get("related_findings", []):
            checks.require(finding_id in known_findings, f"question {item['id']} finding exists: {finding_id}")
    suggestion_ids = [item.get("id", "") for item in suggestions]
    checks.require(len(suggestion_ids) == len(set(suggestion_ids)), "suggestion IDs are unique")
    for item in suggestions:
        checks.require(len(item.get("options", [])) >= 2, f"suggestion {item.get('id')} compares at least two options")
        checks.require(len(item.get("what_would_change_our_mind_if", {})) == 2, f"suggestion {item.get('id')} has two-sided change criteria")
        checks.require("PROPOSAL ONLY" in item.get("implementation_state", ""), f"suggestion {item.get('id')} remains unimplemented")
        checks.require(bool(item.get("recommendation")) and bool(item.get("what_supports_recommendation")), f"suggestion {item.get('id')} has recommendation and rationale")
        for source_id in item.get("source_ids", []):
            checks.require(source_id in sources, f"suggestion {item['id']} source exists: {source_id}")
        for finding_id in item.get("related_findings", []):
            checks.require(finding_id in known_findings, f"suggestion {item['id']} finding exists: {finding_id}")


def validate_venues_and_result(checks: Checks, sources: dict[str, dict]) -> None:
    venues = read_csv(ROOT / "data/venues_week11.csv")
    checks.require(len(venues) == 13, "Week 11 venue table has 13 rows")
    game_ids = [row.get("game_id", "") for row in venues]
    checks.require(len(game_ids) == len(set(game_ids)), "Week 11 venue game IDs are unique")
    urls_in_registry = {item["url"]: item["id"] for item in sources.values()}
    for row in venues:
        checks.require(bool(row.get("location")) and bool(row.get("stadium")), f"venue values present for {row.get('game_id')}")
        checks.require(row.get("venue_source_url", "").startswith("https://www.nfl.com/games/"), f"official Game Center URL for {row.get('game_id')}")
        source_id = urls_in_registry.get(row.get("venue_source_url", ""))
        checks.require(source_id is not None and source_id.startswith("SRC-VEN-"), f"one-to-one venue source record for {row.get('game_id')}")
    reliants = [row for row in venues if row.get("stadium") == "RELIANT STADIUM"]
    checks.require(len(reliants) == 1 and reliants[0].get("game_id") == "2026_11_IND_HOU", "RELIANT STADIUM label preserved for Colts-Texans")
    checks.require("Reliant name returned" in sources["SRC-15"]["observation"], "Houston official stadium page cross-check is recorded")

    results = read_csv(ROOT / "data/results_increment_week10.csv")
    checks.require(len(results) == 1, "Week 10 result update is explicitly a one-row delta")
    if results:
        row = results[0]
        checks.require((row.get("away_score"), row.get("home_score"), row.get("status")) == ("23", "20", "FINAL"), "Week 10 Chargers-Ravens final is 23-20")
        checks.require(row.get("result_source_url", "").startswith("https://www.nfl.com/games/"), "result delta has official Game Center link")
        checks.require(row.get("independent_schedule_source_url", "").startswith("https://www.nfl.com/schedules/"), "result delta has independent official schedule link")


def validate_inherited_claims(checks: Checks) -> None:
    desk = REPO / "nfl-desk-35a1feb2"
    delta = read_csv(desk / "data/injury_read_delta.csv")
    checks.require(len(delta) == 1, "prior injury read delta has one summary row")
    if delta:
        start = utc(delta[0]["value_read_1"])
        end = utc(delta[0]["value_read_2"])
        seconds = int((end - start).total_seconds())
        checks.require(seconds == 25 * 3600 + 13 * 60, "saved injury-read timestamps span 25 hours 13 minutes")
        questions = read_csv(desk / "data/questions_register.csv")
        q01 = next(item for item in questions if item["id"] == "Q-01")
        checks.require("49 hours" in q01["what_we_already_have"], "prior Q-01 still records the 49-hour prose claim")
        availability = (desk / "availability.html").read_text(encoding="utf-8")
        summary = (desk / "executive-summary.html").read_text(encoding="utf-8")
        checks.require("49 hours" in availability, "prior availability page still records the 49-hour prose claim")
        checks.require("1 hour 13 minutes" in summary, "prior executive summary still records the 1-hour-13-minute prose claim")

    with gzip.open(REPO / "data/decision-desk/raw/games.csv.gz", "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        game_rows = list(reader)
    spread_total = [row for row in game_rows if row.get("spread_line") not in (None, "") and row.get("total_line") not in (None, "")]
    moneyline = [row for row in game_rows if row.get("home_moneyline") not in (None, "") and row.get("away_moneyline") not in (None, "")]
    season_2026 = [row for row in game_rows if row.get("season") == "2026"]
    priced_2026 = [row for row in season_2026 if row.get("spread_line") not in (None, "") and row.get("total_line") not in (None, "")]
    checks.require((len(game_rows), len(spread_total), len(moneyline), len(season_2026), len(priced_2026)) == (7548, 7439, 5458, 272, 163), "third-party market counts reproduce from the committed gzip")
    inventory = read_csv(desk / "data/third_party_inventory.csv")
    inv = {row["quantity"]: row["value"] for row in inventory}
    checks.require(inv.get("games in the multi-season log") == "7548", "prior inventory count agrees with raw game file")
    checks.require(inv.get("rows carrying a spread and total") == "7439", "prior inventory spread/total count agrees with raw game file")

    originated = read_csv(desk / "data/originated_wk11.csv")
    prices = read_csv(desk / "data/price_snapshots.csv")
    checks.require(len(originated) == 13, "prior origination table has 13 Week 11 rows")
    checks.require(all(not row["market_line"] and not row["market_open"] and not row["market_close"] for row in originated), "all prior Week 11 market quote fields are blank")
    checks.require(len(prices) == 39 and all(row["stage"] == "MODEL_RECORD" for row in prices), "39 prior price-store rows are model records, not operator snapshots")

    requirements = read_csv(desk / "data/requirements_master.csv")
    req04 = next(item for item in requirements if item["id"] == "REQ-04")
    checks.require(req04["status"] == "MET" and "undefined" in req04["gate_blocking"].lower(), "REQ-04 MET label conflicts with its undefined gate text")

    model_card = read_csv(desk / "data/model_card.csv")
    hfa = next(item["value"] for item in model_card if item["field"] == "fitted home-field advantage")
    q05 = next(item for item in read_csv(desk / "data/questions_register.csv") if item["id"] == "Q-05")
    checks.require(hfa == "-0.52 points" and "-0.46" in q05["answer_or_next_number"], "prior model card and Q-05 report conflicting home-field coefficients")

    reserve = read_csv(desk / "data/reserve_register_2026_10_11.csv")
    checks.require(len(reserve) == 50, "prior reserve register has 50 stored rows")
    checks.require(all("position" not in row for row in reserve), "prior reserve register does not contain a position field")
    checks.require(max(row["date_official"] for row in reserve if row["month_read"] == "2026-11") == "2026-11-16", "prior November reserve snapshot ends at official date Nov. 16")
    bal = [row for row in reserve if row["club"] == "BAL"]
    checks.require(len(bal) == 1 and bal[0]["player"] == "Tavius Robinson", "prior partial reserve capture has one BAL row and no position field")

    older_feed = read_csv(REPO / "nfl-desk-e46fb855/data/results_feed.csv")
    current_standings = read_csv(desk / "data/standings_2026_read2.csv")
    official_codes = {row["team"] for row in current_standings}
    old_appearances = Counter(row[field] for row in older_feed for field in ("away", "home"))
    unmatched_appearances = sum(count for code, count in old_appearances.items() if code not in official_codes)
    checks.require((len(older_feed), old_appearances["LAR"], old_appearances["ARI"], unmatched_appearances) == (145, 9, 9, 18), "older carried-forward feed exact-code join misses 18 LAR/ARI club appearances")
    newer_feed = read_csv(desk / "data/results_feed_2026.csv")
    newer_codes = {row[field] for row in newer_feed for field in ("away", "home")}
    checks.require("LAR" not in newer_codes and "ARI" not in newer_codes and {"LA", "AZ"}.issubset(newer_codes), "newer 35a1feb2 feed uses the LA/AZ aliases")

    leaderboard = read_csv(desk / "data/leaderboard_signal.csv")
    reviewed = [row for row in leaderboard if row["strategy"] in {"P-01", "P-02", "P-03"}]
    checks.require(len(reviewed) == 3 and all(row["forecasts_recorded"] == "13" and row["settled"] == "0" for row in reviewed), "P-01/P-02/P-03 each have 13 forecasts and zero settled")
    checks.require(all(not row["mean_brier"] for row in reviewed), "reviewed leaderboard score cells are blank, not zero performance")


def validate_html(checks: Checks) -> None:
    pages = ["index.html", "audit.html", "questions.html", "suggestions.html", "flagged.html", "sources.html"]
    parser_by_path: dict[Path, HtmlAuditParser] = {}
    for relative in pages:
        page_path = ROOT / relative
        checks.require(page_path.is_file(), f"generated page exists: {relative}")
        if not page_path.is_file():
            continue
        parser = HtmlAuditParser()
        parser.feed(page_path.read_text(encoding="utf-8"))
        parser_by_path[page_path.resolve()] = parser
        checks.require(parser.table_rows > 0 or relative in {"index.html", "audit.html", "questions.html", "suggestions.html", "flagged.html"}, f"HTML parses: {relative}")
        checks.require(parser.rows_without_link == 0, f"every table body row has a provenance or local artifact link: {relative}")
        checks.require(not parser.external_target_errors, f"external target links are safe: {relative}")

    for page_path, parser in parser_by_path.items():
        relative = page_path.relative_to(ROOT).as_posix()
        for href, _rel in parser.links:
            parts = urlsplit(href)
            if parts.scheme in {"http", "https", "mailto", "tel"}:
                if parts.scheme in {"http", "https"}:
                    checks.require(parts.scheme == "https", f"external link uses HTTPS: {relative} -> {href}")
                continue
            if parts.scheme:
                checks.errors.append(f"unsupported URL scheme in {relative}: {href}")
                continue
            target_text = unquote(parts.path)
            target = (page_path.parent / target_text).resolve() if target_text else page_path
            checks.require(target.is_relative_to(REPO), f"internal link remains in repository: {relative} -> {href}")
            if target_text:
                checks.require(target.is_file(), f"internal target exists: {relative} -> {href}")
            if parts.fragment and target.suffix == ".html" and target.is_file():
                target_parser = parser_by_path.get(target)
                if target_parser is None:
                    target_parser = HtmlAuditParser()
                    target_parser.feed(target.read_text(encoding="utf-8"))
                    parser_by_path[target] = target_parser
                checks.require(parts.fragment in target_parser.anchors, f"HTML fragment exists: {relative} -> {href}")
            elif parts.fragment and not target_text:
                checks.require(parts.fragment in parser.anchors, f"same-page anchor exists: {relative} -> {href}")


def main() -> int:
    checks = Checks()
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "build.py"), "--check"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        checks.require(result.returncode == 0, "generated HTML and manifest match deterministic build")
        if result.returncode != 0:
            checks.errors.append("build.py --check: " + (result.stderr.strip() or result.stdout.strip()))

        sources = load_json(ROOT / "data/sources.json")
        findings = load_json(ROOT / "data/audit_findings.json")
        questions = load_json(ROOT / "data/questions.json")
        suggestions = load_json(ROOT / "data/suggestions.json")
        source_map = validate_source_registry(checks, sources)
        validate_review_records(checks, source_map, findings, questions, suggestions)
        validate_venues_and_result(checks, source_map)
        validate_inherited_claims(checks)
        validate_html(checks)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, csv.Error, gzip.BadGzipFile) as exc:
        checks.errors.append(f"verification input/runtime error: {exc}")

    if checks.errors:
        print(f"verify: FAIL — {len(checks.errors)} error(s)")
        for error in checks.errors:
            print("  FAIL " + error)
        return 1
    findings = load_json(ROOT / "data/audit_findings.json")
    print(f"verify: PASS — {len(checks.passes)} assertions; {len(findings)} findings; {sum(1 for item in findings if item['flagged'])} flagged")
    print("verify: source IDs, local evidence, manifest hashes, row-level links, internal targets, interval/count checks and proposal gates passed")
    print("verify: live source URLs were not fetched; manual/source-rights review remains required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

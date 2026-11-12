#!/usr/bin/env python3
"""Offline integrity checks for the isolated NFL Week 10 snapshot and static site."""
from __future__ import annotations
import csv
import hashlib
import json
from collections import defaultdict, Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DATA = ROOT / "data"
EXPECTED_PAGES = {
    "index.html", "results.html", "lines.html", "injuries.html", "sources.html",
    "correlations.html", "strategies.html", "validation.html", "leaderboard.html",
    "questions.html", "suggestions.html", "flagged.html", "audit.html",
}
TEAM_HOSTS = {
    "commanders.com","patriots.com","baltimoreravens.com","seahawks.com","azcardinals.com","miamidolphins.com","therams.com","49ers.com","dallascowboys.com","packers.com","vikings.com","detroitlions.com","giants.com","neworleanssaints.com","steelers.com","clevelandbrowns.com","colts.com","houstontexans.com","chiefs.com","atlantafalcons.com","panthers.com","buffalobills.com","newyorkjets.com","jaguars.com","tennesseetitans.com","raiders.com","bengals.com","chargers.com","chicagobears.com","denverbroncos.com","philadelphiaeagles.com","buccaneers.com"
}
BOOK_HOSTS = {"sportsbook.draftkings.com", "sportsbook.fanduel.com"}


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def require(condition: bool, message: str):
    if not condition:
        raise AssertionError(message)


def official_https(url: str) -> bool:
    p = urlparse(url or "")
    if p.scheme != "https" or not p.hostname:
        return False
    host = p.hostname.lower()
    if host.startswith("www."):
        host = host[4:]
    return (
        host in {"nfl.com", "operations.nfl.com", "sportsbook.draftkings.com", "sportsbook.fanduel.com"}
        or host.endswith(".nfl.com") or host in TEAM_HOSTS or host in BOOK_HOSTS
    )


def verify_source_fields() -> int:
    manifests = {
        "games_2026_w1_w9.csv": ["source_url", "schedule_url"],
        "standings_2026_w10.csv": ["source_url"],
        "team_stats_2026_w10.csv": ["source_url", "source_offense_passing_url", "source_offense_rushing_url", "source_defense_passing_url", "source_defense_rushing_url"],
        "schedule_2026_w10.csv": ["source_url", "source_schedule_url"],
        "market_quotes_2026_w10.csv": ["source_url", "board_url"],
        "depth_chart_coverage_2026_w10.csv": ["chart_source_url", "source_schedule_url", "source_injury_index_url"],
        "injuries_depth_w10.csv": ["source_url", "injury_source_url"],
        "model_lines_2026_w10.csv": ["source_url", "source_standings_url", "source_market_urls", "source_injury_report_url"],
        "walk_forward_2026_w2_w9.csv": ["source_url", "input_standings_source_url"],
        "correlations_2026.csv": ["source_url"],
        "strategies_2026.csv": ["source_url", "secondary_source_url"],
        "validation_gates_2026.csv": ["source_url"],
        "leaderboard_2026.csv": ["source_url", "strategy_source_url"],
        "luck_skill_2026.csv": ["source_url"],
        "sources_registry.csv": ["official_url"],
        "site_suggestions.csv": ["source_url", "supporting_source_url"],
        "decision_questions.csv": ["source_url", "supporting_source_url"],
        "flagged_review.csv": ["source_url", "secondary_source_url"],
        "repo_audit.csv": ["official_source_url"],
    }
    checks = 0
    for filename, fields in manifests.items():
        rows = read_csv(filename)
        require(bool(rows), f"{filename}: expected nonempty rows")
        for line_number, row in enumerate(rows, start=2):
            urls = [u.strip() for field in fields for u in row.get(field, "").split(";") if u.strip()]
            require(bool(urls), f"{filename}:{line_number}: no source URL or explicit row-level provenance field")
            for url in urls:
                require(official_https(url), f"{filename}:{line_number}: non-HTTPS or unapproved publisher URL: {url}")
                checks += 1
    return checks


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.ids = set()
        self.tables = []
        self._table = None
        self._caption_depth = 0
        self._th_depth = 0
        self.th_without_scope = 0
        self.lang = None
        self.has_viewport = False
        self.has_main = False
        self.has_skip = False
        self.external_errors = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag in {"a", "link", "script", "img"}:
            attr = "href" if tag in {"a", "link"} else "src"
            if a.get(attr):
                self.links.append((tag, a.get(attr), a))
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "meta" and a.get("name", "").lower() == "viewport":
            self.has_viewport = True
        if tag == "main" and a.get("id") == "main":
            self.has_main = True
        if tag == "a" and "skip-link" in a.get("class", ""):
            self.has_skip = True
        if tag == "table":
            self._table = {"caption": False, "headers": 0, "bad_headers": 0}
            self.tables.append(self._table)
        elif tag == "caption" and self._table is not None:
            self._table["caption"] = True
        elif tag == "th" and self._table is not None:
            self._table["headers"] += 1
            if a.get("scope") != "col":
                self._table["bad_headers"] += 1

    def handle_endtag(self, tag):
        if tag == "table":
            self._table = None


def verify_html() -> tuple[int, int]:
    pages = sorted(p for p in ROOT.glob("*.html"))
    require({p.name for p in pages} == EXPECTED_PAGES, f"Expected exactly the overview plus 12 category pages; got {[p.name for p in pages]}")
    local_count = 0
    external_count = 0
    for page in pages:
        parser = PageParser()
        raw = page.read_text(encoding="utf-8")
        parser.feed(raw)
        require(parser.lang == "en", f"{page.name}: missing lang=en")
        require(parser.has_viewport, f"{page.name}: missing responsive viewport meta")
        require(parser.has_main and parser.has_skip, f"{page.name}: missing skip link or main landmark")
        require("localhost" not in raw.lower() and "127.0.0.1" not in raw.lower(), f"{page.name}: contains a local-service URL")
        for t in parser.tables:
            require(t["caption"], f"{page.name}: every data table needs a caption")
            require(t["headers"] > 0 and t["bad_headers"] == 0, f"{page.name}: every table header needs scope=col")
        for tag, href, attrs in parser.links:
            p = urlparse(href)
            if p.scheme in {"https", "http"}:
                require(p.scheme == "https" and official_https(href), f"{page.name}: external link not HTTPS/approved: {href}")
                if tag == "a":
                    require(attrs.get("target") == "_blank", f"{page.name}: external anchor should open separately")
                    rel = set(attrs.get("rel", "").split())
                    require({"noopener", "noreferrer"}.issubset(rel), f"{page.name}: external anchor lacks safe rel")
                external_count += 1
                continue
            require(not p.scheme and not p.netloc, f"{page.name}: unsafe/local URI {href}")
            if href.startswith("#"):
                require(href[1:] in parser.ids, f"{page.name}: missing fragment target {href}")
                local_count += 1
                continue
            target = (page.parent / p.path).resolve()
            require(target.is_relative_to(ROOT.resolve()), f"{page.name}: local link escapes isolated namespace: {href}")
            require(target.exists(), f"{page.name}: broken local link {href}")
            if p.fragment and target.suffix.lower() == ".html":
                target_parser = PageParser()
                target_parser.feed(target.read_text(encoding="utf-8"))
                require(p.fragment in target_parser.ids, f"{page.name}: broken fragment {href}")
            local_count += 1
    require((ROOT / "style.css").is_file(), "site stylesheet missing")
    return local_count, external_count


def verify_audit() -> tuple[int, int]:
    summary = read_json("repo_audit_summary.json")
    rows = read_csv("repo_audit.csv")
    require(len(rows) == summary["physical_lines"], "audit summary physical line count does not match CSV")
    require(len(summary["files_inventory"]) == summary["files"], "audit inventory count mismatch")
    allowed_basis = {
        "ROW_SOURCE_FIELD", "ROW_SOURCE_URLS_FIELD", "OFFICIAL_GAME_LINK_FROM_RECORD_CONTEXT",
        "HTTPS_OFFICIAL_LINK_IN_LINE", "OFFICIAL_SCOPE_REFERENCE_FALLBACK_NOT_ROW_PROVENANCE",
        "OFFICIAL_COUNTERPART_FOR_FLAGGED_INPUT_NOT_INPUT_PROVENANCE",
    }
    by_file: dict[str, list[dict[str, str]]] = defaultdict(list)
    ids = set()
    for row in rows:
        require(row["audit_id"] not in ids, f"duplicate audit id {row['audit_id']}")
        ids.add(row["audit_id"])
        require(official_https(row["official_source_url"]), f"audit row lacks official HTTPS reference: {row['audit_id']}")
        require(row["source_basis"] in allowed_basis, f"unknown source basis: {row['source_basis']}")
        require(len(row["line_sha256"]) == 64, f"bad line SHA: {row['audit_id']}")
        by_file[row["repository_path"]].append(row)
    file_checks = 0
    for rel, indexed in by_file.items():
        indexed.sort(key=lambda row: int(row["physical_line"]))
        path = (REPO / rel).resolve()
        require(path.is_relative_to(REPO.resolve()) and path.is_file(), f"audit path missing or unsafe: {rel}")
        actual_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        require(len(indexed) == len(actual_lines), f"audit line count mismatch for {rel}: {len(indexed)} != {len(actual_lines)}")
        for expected_line, row in enumerate(indexed, start=1):
            require(int(row["physical_line"]) == expected_line, f"non-contiguous line index in {rel}")
            content = actual_lines[expected_line - 1]
            require(hashlib.sha256(content.encode("utf-8")).hexdigest() == row["line_sha256"], f"line hash mismatch: {rel}:{expected_line}")
            excerpt = content.strip().replace("\t", " ")
            if len(excerpt) > 240:
                excerpt = excerpt[:237] + "..."
            require(row["excerpt"] == excerpt, f"line excerpt mismatch: {rel}:{expected_line}")
            file_checks += 1
    nonempty_inventory = {item["path"] for item in summary["files_inventory"] if item["physical_lines"] > 0}
    empty_inventory = [item["path"] for item in summary["files_inventory"] if item["physical_lines"] == 0]
    require(set(by_file) == nonempty_inventory, "audit inventory path set mismatch")
    for rel in empty_inventory:
        path = (REPO / rel).resolve()
        require(path.is_relative_to(REPO.resolve()) and path.is_file() and path.stat().st_size == 0, f"expected empty in-scope file: {rel}")
    return len(rows), file_checks


def verify_data() -> dict[str, int]:
    expected_counts = {
        "games_2026_w1_w9.csv": 136, "standings_2026_w10.csv": 32, "team_stats_2026_w10.csv": 32,
        "schedule_2026_w10.csv": 18, "market_quotes_2026_w10.csv": 28, "depth_chart_coverage_2026_w10.csv": 32,
        "injuries_depth_w10.csv": 76, "model_lines_2026_w10.csv": 14, "walk_forward_2026_w2_w9.csv": 120,
        "correlations_2026.csv": 7, "strategies_2026.csv": 6, "validation_gates_2026.csv": 11,
        "leaderboard_2026.csv": 6, "luck_skill_2026.csv": 3, "sources_registry.csv": 58,
        "site_suggestions.csv": 12, "decision_questions.csv": 16, "flagged_review.csv": 20,
    }
    counts = {}
    data = {}
    for name, expected in expected_counts.items():
        rows = read_csv(name)
        counts[name] = len(rows)
        data[name] = rows
        require(len(rows) == expected, f"{name}: expected {expected} rows, found {len(rows)}")

    recon = read_json("game_reconciliation.json")
    require(recon["status"] == "PASS" and recon["games"] == 136 and recon["teams"] == 32, "result reconciliation failed")
    require(recon["teams_reconciled"] == 32 and recon["mismatches"] == [], "standings mismatch exists")
    require(sum(recon["week_counts"].values()) == 136, "weekly result counts do not add up")
    schedule = data["schedule_2026_w10.csv"]
    require(Counter(r["status"] for r in schedule) == {"SCHEDULED": 14, "BYE": 4}, "Week 10 schedule/bye count mismatch")
    quotes = data["market_quotes_2026_w10.csv"]
    require(all(not r["retrieved_time_utc"] and "DATE_ONLY" in r["timestamp_status"] for r in quotes), "market quote timing is incorrectly represented")
    quote_keys = Counter((r["away_team"], r["home_team"]) for r in quotes)
    require(len(quote_keys) == 14 and set(quote_keys.values()) == {2}, "each Week 10 game must have one quote from each of two books")
    coverage = data["depth_chart_coverage_2026_w10.csv"]
    require(Counter(r["week10_status"] for r in coverage) == {"PLAYING": 28, "BYE": 4}, "32-team chart coverage must align to schedule")
    require({r["team"] for r in coverage if r["week10_status"] == "BYE"} == {"CHI", "DEN", "PHI", "TB"}, "bye-team chart coverage mismatch")
    injuries = data["injuries_depth_w10.csv"]
    require(len({r["team"] for r in injuries}) == 17, "injury tracker team count mismatch")
    require(all(not r["actual_week10_participation"] and not r["expected_starter_after_report"] for r in injuries), "unconfirmed participation/replacement populated")
    lines = data["model_lines_2026_w10.csv"]
    adjusted_fields = ["injury_adjustment_away_points", "injury_adjustment_home_points", "injury_adjusted_home_spread", "injury_adjusted_total"]
    require(all(not row[key] for row in lines for key in adjusted_fields), "unvalidated injury adjustment must stay blank")
    require(all("NOT INJURY_ADJUSTED" in row["line_status"] for row in lines), "line status omits non-adjustment caveat")
    wf = read_json("walk_forward_summary.json")
    require(wf["n_games"] == 120 and wf["status"] == "EXPLORATORY_DESCRIPTIVE_ONLY", "walk-forward scope/status mismatch")
    require(wf["mae_points"] == "10.4048", "walk-forward MAE changed")
    corr = data["correlations_2026.csv"]
    computed = [r for r in corr if r["status"] == "COMPUTED_DESCRIPTIVE"]
    uncomputed = [r for r in corr if r["status"].startswith("NOT_COMPUTABLE")]
    require(len(computed) == 4 and len(uncomputed) == 3, "correlation computed/blank row count mismatch")
    for row in computed:
        require(0 < float(row["p_value_two_sided"]) < 1, f"invalid correlation p-value {row['correlation_id']}")
        require(float(row["ci95_low_fisher_z"]) <= float(row["pearson_r"]) <= float(row["ci95_high_fisher_z"]), f"correlation CI does not contain estimate: {row['correlation_id']}")
    for row in uncomputed:
        require(not row["pearson_r"] and not row["n"] and row["caveat"], f"uncomputable correlation must remain blank with caveat: {row['correlation_id']}")
    gates = data["validation_gates_2026.csv"]
    require(sum(r["status"] == "PASS" for r in gates) == 1 and all(r["status"] == "BLOCKED" for r in gates if r["gate_id"] != "G0"), "only G0 should pass")
    leaderboard = data["leaderboard_2026.csv"]
    require(all(r["rank"] == "" and r["graded_bets"] == "0" and r["net_roi"] == "" and r["status"] == "NO_QUALIFIED_ENTRY" for r in leaderboard), "leaderboard fabricated a rank or return")
    require(all(not r["estimate"] and not r["n"] and "NOT_COMPUTABLE" in r["status"] or "BLOCKED" in r["status"] for r in data["luck_skill_2026.csv"]), "luck/skill field should remain unavailable")
    return counts


def main() -> None:
    counts = verify_data()
    url_count = verify_source_fields()
    local_links, external_links = verify_html()
    audit_rows, audit_hashes = verify_audit()
    print(json.dumps({
        "status": "PASS", "html_pages": len(EXPECTED_PAGES), "data_files_checked": len(counts),
        "data_rows": sum(counts.values()), "source_urls_checked": url_count,
        "local_links_checked": local_links, "external_links_checked": external_links,
        "repository_audit_rows": audit_rows, "repository_line_hashes_checked": audit_hashes,
        "limits": "Structural/provenance verification only; does not refetch dynamic external sources or establish betting skill."
    }, indent=2))


if __name__ == "__main__":
    main()

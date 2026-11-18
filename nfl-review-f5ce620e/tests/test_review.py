from __future__ import annotations

import csv
import gzip
import json
from collections import Counter
import subprocess
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))
import build  # noqa: E402
import verify  # noqa: E402


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class ReviewDossierTests(unittest.TestCase):
    def test_render_is_byte_deterministic(self):
        self.assertEqual(build.render_outputs(), build.render_outputs())

    def test_generated_pages_and_manifest_are_current(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "build.py"), "--check"],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_all_table_rows_link_to_evidence_or_artifact(self):
        for name in ("index.html", "audit.html", "questions.html", "suggestions.html", "flagged.html", "sources.html"):
            parser = verify.HtmlAuditParser()
            parser.feed((ROOT / name).read_text(encoding="utf-8"))
            self.assertEqual(parser.rows_without_link, 0, name)
            self.assertFalse(parser.external_target_errors, name)

    def test_saved_injury_read_interval_is_25_hours_13_minutes(self):
        rows = read_csv(REPO / "nfl-desk-35a1feb2/data/injury_read_delta.csv")
        self.assertEqual(len(rows), 1)
        first = datetime.fromisoformat(rows[0]["value_read_1"].replace("Z", "+00:00"))
        second = datetime.fromisoformat(rows[0]["value_read_2"].replace("Z", "+00:00"))
        self.assertEqual((second - first).total_seconds(), 25 * 3600 + 13 * 60)
        finding = next(item for item in read_json(ROOT / "data/audit_findings.json") if item["id"] == "A02")
        self.assertIn("25 hours 13 minutes", finding["observed"])
        self.assertTrue(finding["flagged"])

    def test_third_party_market_inventory_counts_reproduce(self):
        with gzip.open(REPO / "data/decision-desk/raw/games.csv.gz", "rt", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        spread_total = [r for r in rows if r.get("spread_line") and r.get("total_line")]
        moneyline = [r for r in rows if r.get("home_moneyline") and r.get("away_moneyline")]
        season_2026 = [r for r in rows if r.get("season") == "2026"]
        priced_2026 = [r for r in season_2026 if r.get("spread_line") and r.get("total_line")]
        self.assertEqual((len(rows), len(spread_total), len(moneyline), len(season_2026), len(priced_2026)), (7548, 7439, 5458, 272, 163))
        finding = next(item for item in read_json(ROOT / "data/audit_findings.json") if item["id"] == "A03")
        self.assertIn("third-party", finding["observed"])
        self.assertTrue(finding["flagged"])

    def test_week11_venue_table_is_row_sourced(self):
        rows = read_csv(ROOT / "data/venues_week11.csv")
        sources = {item["url"]: item["id"] for item in read_json(ROOT / "data/sources.json")}
        self.assertEqual(len(rows), 13)
        for row in rows:
            self.assertTrue(row["venue_source_url"].startswith("https://www.nfl.com/games/"))
            self.assertTrue(sources[row["venue_source_url"]].startswith("SRC-VEN-"))
        reliant = next(row for row in rows if row["stadium"] == "RELIANT STADIUM")
        self.assertEqual(reliant["game_id"], "2026_11_IND_HOU")

    def test_one_game_result_delta_has_two_official_links(self):
        rows = read_csv(ROOT / "data/results_increment_week10.csv")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row["away_score"], row["home_score"], row["status"]), ("23", "20", "FINAL"))
        self.assertTrue(row["result_source_url"].startswith("https://www.nfl.com/games/"))
        self.assertTrue(row["independent_schedule_source_url"].startswith("https://www.nfl.com/schedules/"))

    def test_suggestions_have_options_two_sides_and_no_implementation(self):
        suggestions = read_json(ROOT / "data/suggestions.json")
        self.assertGreaterEqual(len(suggestions), 8)
        for suggestion in suggestions:
            with self.subTest(suggestion=suggestion["id"]):
                self.assertGreaterEqual(len(suggestion["options"]), 2)
                self.assertEqual(len(suggestion["what_would_change_our_mind_if"]), 2)
                self.assertIn("PROPOSAL ONLY", suggestion["implementation_state"])
                self.assertTrue(suggestion["source_ids"])

    def test_model_and_requirement_inconsistencies_remain_explicitly_flagged(self):
        findings = {item["id"]: item for item in read_json(ROOT / "data/audit_findings.json")}
        self.assertTrue(findings["A13"]["flagged"])
        self.assertIn("-0.52", findings["A13"]["observed"])
        self.assertIn("-0.46", findings["A13"]["observed"])
        self.assertTrue(findings["A14"]["flagged"])
        self.assertIn("undefined", findings["A14"]["observed"])

    def test_manifest_scope_excludes_live_source_responses(self):
        manifest = read_json(ROOT / "data/manifest.json")
        self.assertIn("not authenticate source-server", manifest["scope"])
        self.assertEqual(
            {item["path"] for item in manifest["entries"]},
            {"raw/official_reads_2026-11-18.md", "data/venues_week11.csv", "data/results_increment_week10.csv"},
        )
        for item in manifest["entries"]:
            payload = (ROOT / item["path"]).read_bytes()
            import hashlib
            self.assertEqual(item["bytes"], len(payload))
            self.assertEqual(item["sha256"], hashlib.sha256(payload).hexdigest())

    def test_legacy_team_alias_join_mismatch_is_explicit(self):
        older = read_csv(REPO / "nfl-desk-e46fb855/data/results_feed.csv")
        standings = read_csv(REPO / "nfl-desk-35a1feb2/data/standings_2026_read2.csv")
        official_codes = {row["team"] for row in standings}
        appearances = Counter(row[field] for row in older for field in ("away", "home"))
        unmatched = sum(count for code, count in appearances.items() if code not in official_codes)
        self.assertEqual((len(older), appearances["LAR"], appearances["ARI"], unmatched), (145, 9, 9, 18))
        finding = next(item for item in read_json(ROOT / "data/audit_findings.json") if item["id"] == "A20")
        self.assertTrue(finding["flagged"])
        self.assertIn("18 club-game appearances", finding["observed"])

    def test_stadium_name_cross_check_is_not_marked_as_an_open_flag(self):
        findings = {item["id"]: item for item in read_json(ROOT / "data/audit_findings.json")}
        self.assertFalse(findings["A18"]["flagged"])
        self.assertIn("CORROBORATED", findings["A18"]["status"])
        sources = {item["id"]: item for item in read_json(ROOT / "data/sources.json")}
        self.assertIn("Reliant name returned", sources["SRC-15"]["observation"])


if __name__ == "__main__":
    unittest.main()

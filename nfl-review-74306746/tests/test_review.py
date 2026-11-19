from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import verify  # noqa: E402


class CrossDeskReviewTests(unittest.TestCase):
    def test_review_registers_and_repository_claims_validate(self) -> None:
        metrics, errors = verify.validate_data()
        self.assertEqual(errors, [])
        self.assertEqual(metrics["sources"], 10)
        self.assertEqual(metrics["readiness"], 10)
        self.assertEqual(metrics["questions"], 8)
        self.assertEqual(metrics["suggestions"], 7)
        self.assertEqual(metrics["flags"], 8)

    def test_price_conflict_is_reproduced_without_asserting_external_truth(self) -> None:
        metrics = verify.inspect_repository()
        self.assertEqual(metrics["engine_snapshots"], 78)
        self.assertEqual(metrics["engine_games"], 13)
        self.assertEqual(metrics["engine_archives"], 13)
        self.assertEqual(metrics["rosters_populated"], 1)
        self.assertEqual(metrics["command_week11_rows"], 12)
        self.assertEqual(metrics["week11_fixture_games"], 13)

    def test_every_engine_archive_matches_its_committed_hash(self) -> None:
        errors: list[str] = []
        metrics = verify.inspect_repository(errors)
        self.assertEqual(errors, [])
        self.assertEqual(metrics["engine_archives"], 13)

    def test_gamebook_coverage_claim_is_scoped(self) -> None:
        metrics = verify.inspect_repository()
        self.assertEqual(metrics["week10_gamebooks"], 14)
        self.assertEqual(metrics["week10_starter_rows"], 44)
        self.assertEqual(metrics["week10_inactive_rows"], 12)
        results = verify.read_csv(verify.REPO / "data/nfl-desk-f2e20e96/week10_results.csv")
        jax_ten = next(row for row in results if row["away"] == "JAX" and row["home"] == "TEN")
        pdf = jax_ten["game_book_url"]
        starters = verify.read_csv(verify.REPO / "data/nfl-desk-f2e20e96/starters_jax_ten.csv")
        inactives = verify.read_csv(verify.REPO / "data/nfl-desk-f2e20e96/inactives_jax_ten.csv")
        self.assertEqual({row["source_url"] for row in starters}, {pdf})
        self.assertEqual({row["source_url"] for row in inactives}, {pdf})

    def test_third_party_snap_count_snapshot_is_not_current_week_gamebook_coverage(self) -> None:
        metrics = verify.inspect_repository()
        self.assertEqual(metrics["aggregator_snap_rows"], 12693)
        self.assertEqual(metrics["aggregator_snap_games"], 136)
        self.assertEqual(metrics["aggregator_snap_teams"], 32)
        self.assertEqual(metrics["aggregator_snap_week_max"], 9)
        sources = verify.read_json(verify.RESEARCH / "source-coverage.json")
        snap_source = next(item for item in sources if item["id"] == "SRC-10")
        self.assertIn("Aggregator", snap_source["source_class"])
        self.assertIn("no Week 10 or Week 11 rows", snap_source["repository_coverage"])

    def test_every_factual_html_table_row_has_an_official_link_or_flagged_blank(self) -> None:
        pages, rows, errors = verify.validate_pages()
        self.assertEqual(errors, [])
        self.assertEqual(pages, 6)
        self.assertGreaterEqual(rows, 18)

    def test_a_non_https_or_unapproved_source_is_rejected(self) -> None:
        errors: list[str] = []
        verify.check_url("http://www.nfl.com/standings/", "bad test", errors)
        verify.check_url("https://example.invalid/page", "bad test", errors)
        self.assertEqual(len(errors), 2)

    def test_review_pin_and_staleness_caveat_are_explicit(self) -> None:
        summary = verify.read_json(verify.RESEARCH / "summary.json")
        self.assertEqual(summary["evidence_snapshot"], verify.EXPECTED_SNAPSHOT)
        self.assertIn("No official or operator webpage was fetched", summary["freshness_notice"])
        self.assertIn("commits after that snapshot are outside scope", summary["freshness_notice"])
        self.assertIn("PAPER", summary["decision"])

    def test_new_workflow_is_scoped_and_fetch_free(self) -> None:
        workflow = (verify.REPO / ".github/workflows/nfl-review-74306746.yml").read_text(encoding="utf-8")
        verifier = (verify.SITE / "verify.py").read_text(encoding="utf-8")
        self.assertIn("nfl-review-74306746/**", workflow)
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("never requests", verifier)
        self.assertNotIn("requests.get(", verifier)


if __name__ == "__main__":
    unittest.main()

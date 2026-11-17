from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import verify  # noqa: E402


class ReviewHubTests(unittest.TestCase):
    def test_every_source_is_an_https_official_publisher_link(self) -> None:
        count, errors = verify.validate_sources()
        self.assertEqual(errors, [])
        self.assertGreaterEqual(count, 10)

    def test_every_register_row_has_a_source_or_explicit_unknown(self) -> None:
        count, errors = verify.validate_registers()
        self.assertEqual(errors, [])
        self.assertGreater(count, 25)

    def test_all_generated_table_rows_are_sourced_or_flagged(self) -> None:
        rows, errors = verify.validate_html_tables()
        self.assertEqual(errors, [])
        self.assertGreater(rows, 40)

    def test_local_pages_and_repository_evidence_links_resolve(self) -> None:
        count, errors = verify.validate_local_links()
        self.assertEqual(errors, [])
        self.assertGreater(count, 40)

    def test_suggestions_are_review_items_not_approvals(self) -> None:
        suggestions = verify.read_json("suggestions.json")
        for row in suggestions:
            self.assertIn("AWAITING REVIEW", row["decision_status"].upper())
            self.assertGreaterEqual(len(row["options"]), 2)
            self.assertTrue(row["what_would_change_our_mind"].strip())
            self.assertTrue(row["review_test"].strip())

    def test_unconfirmed_observed_values_are_blank(self) -> None:
        readiness = verify.read_json("readiness.json")
        self.assertTrue(readiness)
        self.assertTrue(all(row["observed_value"] == "" for row in readiness))

    def test_wrong_week_source_is_explicitly_mismatched(self) -> None:
        sources = {row["id"]: row for row in verify.read_json("sources.json")}
        self.assertIn("MISMATCH", sources["NFL-INJURY-REQUESTED-WEEK12"]["verification_status"])
        flags = verify.read_json("flagged.json")
        self.assertTrue(any(row["flag_id"] == "F-01" for row in flags))

    def test_gamebook_reuse_restriction_is_published(self) -> None:
        sources = {row["id"]: row for row in verify.read_json("sources.json")}
        book = sources["NFL-GAMEBOOK-RAMS-CARDINALS-W10"]
        self.assertIn("permission", book["observation"].lower())
        flags = verify.read_json("flagged.json")
        self.assertTrue(any(row["flag_id"] == "F-04" for row in flags))

    def test_unsupported_suggestion_metrics_are_not_copied(self) -> None:
        pages = [ROOT / name for name in ("index.html", "questions.html", "suggestions.html", "flagged.html", "sources.html", "summary.html")]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in pages)
        self.assertNotIn("57.4%", combined)
        self.assertNotIn("51.4%", combined)
        self.assertNotIn("-0.039", combined)

    def test_data_files_are_valid_json(self) -> None:
        for path in (ROOT / "data").glob("*.json"):
            with path.open(encoding="utf-8") as handle:
                json.load(handle)


if __name__ == "__main__":
    unittest.main()

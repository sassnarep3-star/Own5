"""Unit tests for the decision-readiness desk."""

from __future__ import annotations

import csv
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import consolidate  # noqa: E402
import build_site  # noqa: E402
import registers  # noqa: E402

DATA = os.path.join(ROOT, "data")


def _rows(name):
    with open(os.path.join(DATA, name + ".csv"), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class ConsolidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rc = consolidate.main()

    def test_consolidation_succeeds(self):
        self.assertEqual(self.rc, 0)

    def test_all_csvs_written(self):
        for name in registers.REGISTER_SETS:
            self.assertTrue(os.path.exists(os.path.join(DATA, name + ".csv")),
                            f"missing CSV {name}")

    def test_no_irregular_status_checks(self):
        report = consolidate.__dict__  # noqa: F841
        with open(os.path.join(DATA, "build_report.json"), encoding="utf-8") as fh:
            import json
            r = json.load(fh)
        self.assertTrue(r["ok"], f"consolidation failures: {r['failures']}")
        self.assertEqual(r["status_counts"]["IRREGULAR"], 0)

    def test_standings_identity_holds(self):
        pf = sum(r[4] for r in consolidate.OFFICIAL_STANDINGS_2026_11_15)
        pa = sum(r[5] for r in consolidate.OFFICIAL_STANDINGS_2026_11_15)
        self.assertEqual(pf, pa)
        self.assertEqual(len(consolidate.OFFICIAL_STANDINGS_2026_11_15), 32)


class RegisterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readiness = _rows("readiness")
        cls.suggestions = _rows("suggestions")
        cls.questions = _rows("questions")
        cls.luck = _rows("luck_panel")
        cls.strat = _rows("strategy_falsification")

    def test_requirement_ids_unique(self):
        ids = [r["req_id"] for r in self.readiness]
        self.assertEqual(len(ids), len(set(ids)))

    def test_status_values_valid(self):
        allowed = {"Met", "Partially met", "Absent", "Rejected (by design)",
                   "Proposed", "In progress"}
        for r in self.readiness:
            self.assertIn(r["status"], allowed, r["req_id"])

    def test_blocking_gate_and_clearing_number_present(self):
        for r in self.readiness:
            self.assertTrue(r["blocking_gate"].strip(), r["req_id"])
            self.assertTrue(r["clearing_number"].strip(), r["req_id"])

    def test_met_rows_cite_a_file(self):
        for r in self.readiness:
            if r["status"] in ("Met", "Partially met"):
                self.assertTrue(r["implemented_where"].strip(), r["req_id"])

    def test_every_strategy_has_two_sided_field(self):
        for r in self.strat:
            self.assertTrue(r["confirm_side"].strip(), r["strategy_id"])
            self.assertTrue(r["refute_side"].strip(), r["strategy_id"])

    def test_suggestions_have_options_and_review_test(self):
        for r in self.suggestions:
            self.assertTrue(r["option_a"].strip(), r["sug_id"])
            self.assertTrue(r["review_test"].strip(), r["sug_id"])

    def test_questions_have_have_and_missing(self):
        for r in self.questions:
            self.assertTrue(r["what_we_have"].strip(), r["q_id"])
            self.assertTrue(r["what_is_missing"].strip(), r["q_id"])

    def test_luck_values_carry_n_and_source(self):
        for r in self.luck:
            self.assertTrue(r["n"].strip(), r["metric"])
            self.assertTrue(r["source_url"].strip(), r["metric"])


class BuildAndVerifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = build_site.build()

    def test_all_pages_written(self):
        for name in build_site.NAV:
            self.assertTrue(os.path.exists(os.path.join(ROOT, name[0])), name[0])

    def test_verify_passes(self):
        sys.path.insert(0, ROOT)
        import verify
        self.assertEqual(verify.main(), 0)


if __name__ == "__main__":
    unittest.main()

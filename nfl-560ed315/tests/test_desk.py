"""Unit tests for the decision-readiness desk (stdlib unittest only).

Run from this directory:  python3 -m unittest discover -s tests -v
"""

import csv
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, ROOT)

import readiness  # noqa: E402
import registers  # noqa: E402


def _read(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class ReadinessRegisterTests(unittest.TestCase):
    def test_row_count(self):
        rows = readiness.build_register()
        self.assertEqual(len(rows), len(readiness.REQUIREMENTS))
        self.assertGreaterEqual(len(rows), 70)

    def test_every_row_has_required_fields(self):
        for r in readiness.build_register():
            for key in ("req_id", "category", "requirement", "status", "blocking_gate",
                        "clearing_number", "how_it_is_met", "gap_or_caveat", "source_url"):
                self.assertTrue(r[key].strip(), "missing {0} on {1}".format(key, r["req_id"]))

    def test_results_feed_metric_is_computed(self):
        rows = {r["req_id"]: r for r in readiness.build_register()}
        self.assertEqual(rows["DR-02"]["current_number"], "137 official games")

    def test_price_store_metric_is_computed(self):
        rows = {r["req_id"]: r for r in readiness.build_register()}
        self.assertEqual(rows["DR-01"]["current_number"], "156/390 populated")

    def test_unverified_rows_are_blank(self):
        for r in readiness.build_register():
            if r["flag"] == "UNVERIFIED":
                self.assertEqual(r["current_number"], "")
            else:
                self.assertTrue(r["current_number"].strip())

    def test_blocking_gate_and_clearing_number_present(self):
        for r in readiness.build_register():
            self.assertTrue(r["blocking_gate"].strip())
            self.assertTrue(r["clearing_number"].strip())

    def test_deterministic(self):
        a = readiness.build_register()
        b = readiness.build_register()
        self.assertEqual(a, b)


class RegisterTests(unittest.TestCase):
    def test_counts(self):
        q = _read("questions.csv")
        s = _read("suggestions.csv")
        src = _read("sources.csv")
        fl = _read("flagged.csv")
        self.assertEqual(len(q), 14)
        self.assertEqual(len(s), 8)
        self.assertEqual(len(src), 6)
        self.assertEqual(len(fl), 12)

    def test_every_register_row_has_source(self):
        for name in ("questions.csv", "suggestions.csv", "sources.csv", "flagged.csv"):
            for row in _read(name):
                url = row.get("source_url", "") or row.get("url", "")
                self.assertTrue(url.strip(), "{0} row without source: {1}".format(name, row))


class SiteBuildTests(unittest.TestCase):
    def test_pages_exist(self):
        for p in ("index.html", "readiness.html", "questions.html", "suggestions.html",
                  "sources.html", "flagged.html", "review.html"):
            self.assertTrue(os.path.exists(os.path.join(ROOT, p)), "missing {0}".format(p))

    def test_landing_has_readiness_table(self):
        with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as fh:
            self.assertIn('data-table="readiness_landing"', fh.read())

    def test_verify_passes(self):
        proc = subprocess.run([sys.executable, "verify.py"], cwd=ROOT,
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()

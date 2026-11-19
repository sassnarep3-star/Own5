#!/usr/bin/env python3
"""Unit tests for the NFL Brief Traceability & Decision Desk (6e13b9ff).

Includes negative controls: corrupted inputs and broken links MUST make
verify_desk.py fail. Run:  python3 -m unittest discover -s nfl-desk-6e13b9ff/tests -v
"""
import csv
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

DESK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(DESK)
DATA = os.path.join(REPO, "data", "nfl-desk-6e13b9ff")
VERIFY = os.path.join(DESK, "verify_desk.py")
BUILD = os.path.join(DESK, "build_desk.py")
PAGES = ["index.html", "requirements.html", "captures.html", "verification.html",
         "questions.html", "suggestions.html", "flagged.html", "sources.html",
         "executive-summary.html"]


def run(args):
    return subprocess.run([sys.executable] + args, capture_output=True, text=True)


def verify(root=REPO, desk=DESK, data=DATA):
    return run([VERIFY, "--root", root, "--desk", desk, "--data", data])


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


class DeskTests(unittest.TestCase):
    def test_verify_clean_tree_passes(self):
        r = verify()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("0 failures", r.stdout)

    def test_build_is_deterministic(self):
        self.assertEqual(run([BUILD]).returncode, 0)
        first = {p: digest(os.path.join(DESK, p)) for p in PAGES}
        self.assertEqual(run([BUILD]).returncode, 0)
        second = {p: digest(os.path.join(DESK, p)) for p in PAGES}
        self.assertEqual(first, second)

    def _mutate_data(self, fn):
        tmp = tempfile.mkdtemp(prefix="desk-data-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        dst = os.path.join(tmp, "data")
        shutil.copytree(DATA, dst)
        fn(dst)
        return dst

    def _read_csv(self, d, name):
        path = os.path.join(d, name)
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        return path, rows

    def _write_csv(self, path, rows):
        with open(path, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh, lineterminator="\n").writerows(rows)

    def test_negative_dropped_coverage_row_fails(self):
        def mutate(d):
            path, rows = self._read_csv(d, "requirements_coverage.csv")
            self._write_csv(path, rows[:-1])  # 84 -> 83
        r = verify(data=self._mutate_data(mutate))
        self.assertNotEqual(r.returncode, 0, "dropped row must fail the pinned count")
        self.assertIn("expected 84 rows", r.stdout)

    def test_negative_bad_source_url_fails(self):
        def mutate(d):
            path, rows = self._read_csv(d, "verification.csv")
            rows[1][3] = "https://example.com/not-official"
            self._write_csv(path, rows)
        r = verify(data=self._mutate_data(mutate))
        self.assertNotEqual(r.returncode, 0, "non-official source_url must fail")
        self.assertIn("source not official", r.stdout)

    def test_negative_mismatch_result_fails(self):
        def mutate(d):
            path, rows = self._read_csv(d, "verification.csv")
            rows[1][6] = "MISMATCH"
            self._write_csv(path, rows)
        r = verify(data=self._mutate_data(mutate))
        self.assertNotEqual(r.returncode, 0, "a MISMATCH row must block publication")
        self.assertIn("MISMATCH", r.stdout)

    def test_negative_unknown_flag_fails(self):
        def mutate(d):
            path, rows = self._read_csv(d, "requirements_coverage.csv")
            rows[1][9] = "F6-99"  # first data row, flag column
            self._write_csv(path, rows)
        r = verify(data=self._mutate_data(mutate))
        self.assertNotEqual(r.returncode, 0, "unknown flag reference must fail")
        self.assertIn("unknown flag", r.stdout)

    def test_negative_corrupt_pct_fails(self):
        def mutate(d):
            path, rows = self._read_csv(d, "standings_fresh_2026-11-19.csv")
            hdr, body = rows[0], rows[1:]
            i_pct = hdr.index("pct")
            body[0][i_pct] = "0.500"  # BUF 8-1-0 -> 0.889, not 0.500
            self._write_csv(path, [hdr] + body)
        r = verify(data=self._mutate_data(mutate))
        self.assertNotEqual(r.returncode, 0, "bad PCT must fail arithmetic recompute")
        self.assertIn("PCT", r.stdout)

    def test_negative_suggestion_implemented_fails(self):
        def mutate(d):
            path, rows = self._read_csv(d, "suggestions.csv")
            hdr, body = rows[0], rows[1:]
            body[0][hdr.index("status")] = "IMPLEMENTED"
            self._write_csv(path, [hdr] + body)
        r = verify(data=self._mutate_data(mutate))
        self.assertNotEqual(r.returncode, 0, "a suggestion marked implemented without a decision must fail")

    def test_negative_broken_internal_link_fails(self):
        tmp = tempfile.mkdtemp(prefix="desk-html-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        dst = os.path.join(tmp, "desk")
        shutil.copytree(DESK, dst, ignore=shutil.ignore_patterns("__pycache__"))
        idx = os.path.join(dst, "index.html")
        with open(idx, encoding="utf-8") as fh:
            txt = fh.read()
        txt = txt.replace('href="requirements.html"', 'href="requirements-missing.html"', 1)
        with open(idx, "w", encoding="utf-8") as fh:
            fh.write(txt)
        r = verify(desk=dst)
        self.assertNotEqual(r.returncode, 0, "broken internal href must fail")
        self.assertIn("broken internal link", r.stdout)

    def test_negative_missing_evidence_file_fails(self):
        tmp = tempfile.mkdtemp(prefix="desk-root-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        r = verify(root=tmp)  # empty root: every in-repo evidence path is missing
        self.assertNotEqual(r.returncode, 0, "missing evidence paths must fail")
        self.assertIn("evidence path missing", r.stdout)

    def test_negative_landing_without_readiness_row_fails(self):
        tmp = tempfile.mkdtemp(prefix="desk-index-")
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        dst = os.path.join(tmp, "desk")
        shutil.copytree(DESK, dst, ignore=shutil.ignore_patterns("__pycache__"))
        idx = os.path.join(dst, "index.html")
        with open(idx, encoding="utf-8") as fh:
            txt = fh.read()
        txt = txt.replace('id="K-001"', 'id="K-XXX"', 1)
        with open(idx, "w", encoding="utf-8") as fh:
            fh.write(txt)
        r = verify(desk=dst)
        self.assertNotEqual(r.returncode, 0, "landing page must carry every requirement row")
        self.assertIn("missing requirement row", r.stdout)


if __name__ == "__main__":
    unittest.main()

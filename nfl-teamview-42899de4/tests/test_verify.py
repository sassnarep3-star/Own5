#!/usr/bin/env python3
"""Negative controls for the team-view desk verifier (session 42899de4).

Each test copies the desk's inputs into a temp tree, injects one specific
corruption, runs verify.py there, and asserts the verifier FAILS. This proves
the fail-closed behaviour instead of assuming it.

Run from repo root:  python3 -m pytest nfl-teamview-42899de4/tests/test_verify.py -q
(or plain:           python3 nfl-teamview-42899de4/tests/test_verify.py)
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DESK = "nfl-teamview-42899de4"
DATA = "data/nfl-teamview-42899de4"
VERIFIER = Path(DESK) / "verify.py"


def make_tree(tmp: Path) -> None:
    """Copy everything verify.py reads into an isolated tree."""
    shutil.copytree(REPO / DESK, tmp / DESK)
    shutil.copytree(REPO / DATA, tmp / DATA)


def run_verify(tmp: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(tmp / VERIFIER)],
                          cwd=tmp, capture_output=True, text=True)


def edit_csv(path: Path, fn) -> None:
    """Apply fn(rows) -> rows and rewrite the CSV with the same header."""
    import csv as _csv
    with open(path, newline="", encoding="utf-8") as fh:
        reader = _csv.DictReader(fh)
        fields = reader.fieldnames
        rows = list(reader)
    rows = fn(rows)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = _csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


class NegativeControls(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        make_tree(self.tmp)
        self.addCleanup(self._tmp.cleanup)

    def assert_fails(self, needle=""):
        proc = run_verify(self.tmp)
        self.assertNotEqual(proc.returncode, 0,
                            f"verifier should fail but passed.\n{proc.stdout}")
        if needle:
            self.assertIn(needle, proc.stdout + proc.stderr)

    def test_clean_tree_passes(self):
        """Control: unmodified tree must pass (guards against a broken harness)."""
        proc = run_verify(self.tmp)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_corrupted_count_fails(self):
        """Inflate IND's W11 listed count -> independent recomputation must catch it."""
        p = self.tmp / DATA / "team_view_w11.csv"
        edit_csv(p, lambda rows: [
            {**r, "players_listed": str(int(r["players_listed"]) + 1)}
            if r["club"] == "IND" else r for r in rows])
        self.assert_fails("listed/practice counts mismatch")

    def test_starter_value_fails(self):
        """Any non-blank starters_out must be rejected (F-TV-01)."""
        p = self.tmp / DATA / "team_view_w11.csv"
        edit_csv(p, lambda rows: [
            {**r, "starters_out": "Patrick Mahomes"} if r["club"] == "KC" else r
            for r in rows])
        self.assert_fails("starters_out")

    def test_zero_fill_of_unpublished_designations_fails(self):
        """Blank net_injury_count replaced by 0 must fail (F-TV-03 blank-not-zero)."""
        p = self.tmp / DATA / "team_view_w11.csv"
        edit_csv(p, lambda rows: [
            {**r, "net_injury_count": "0", "out_count": "0",
             "questionable_count": "0", "doubtful_count": "0"}
            if r["club"] == "PIT" else r for r in rows])
        self.assert_fails()

    def test_bad_source_url_fails(self):
        """Non-nfl.com source on a data row must fail the allowlist."""
        p = self.tmp / DATA / "injury_report_w11.csv"
        edit_csv(p, lambda rows: [
            {**r, "source_url": "https://example.com/injuries"}
            if i == 0 else r for i, r in enumerate(rows)])
        self.assert_fails("source not on allowlist")

    def test_blank_source_without_flag_fails(self):
        """Blank source_url with no flag reference must fail."""
        p = self.tmp / DATA / "fixtures_w11.csv"
        edit_csv(p, lambda rows: [
            {**r, "source_url": "", "note": "silent blank"} for r in rows])
        self.assert_fails("blank source without flag")

    def test_deleted_row_fails_row_pin(self):
        """Dropping one report row must fail the frozen row pin."""
        p = self.tmp / DATA / "injury_report_w11.csv"
        edit_csv(p, lambda rows: rows[:-1])
        self.assert_fails("row pin")

    def test_forged_delta_fails(self):
        """Hand-editing a delta so it does not equal w11-w10 must fail."""
        p = self.tmp / DATA / "team_delta_w10_w11.csv"
        edit_csv(p, lambda rows: [
            {**r, "delta_listed": "99"} if r["club"] == "PIT" else r
            for r in rows])
        self.assert_fails("delta_listed")

    def test_bye_club_report_values_fail(self):
        """A BYE row carrying report numbers must fail (F-TV-06)."""
        p = self.tmp / DATA / "team_view_w11.csv"
        edit_csv(p, lambda rows: [
            {**r, "players_listed": "5", "report_state": "listed"}
            if r["club"] == "ATL" else r for r in rows])
        self.assert_fails()

    def test_undefined_flag_fails(self):
        """Using a flag id that flagged.csv does not define must fail."""
        p = self.tmp / DATA / "team_view_w11.csv"
        edit_csv(p, lambda rows: [
            {**r, "flags": (r["flags"] + ";F-TV-99").strip(";")}
            if r["club"] == "IND" else r for r in rows])
        self.assert_fails("F-TV-99")

    def test_tampered_html_fails_rebuild_check(self):
        """Editing a generated page must fail the byte-identical rebuild check."""
        p = self.tmp / DESK / "pages" / "index.html"
        p.write_text(p.read_text(encoding="utf-8").replace(
            "Dashboard", "Dashboard TAMPERED"), encoding="utf-8")
        self.assert_fails("non-deterministic rebuild")


if __name__ == "__main__":
    unittest.main(verbosity=2)

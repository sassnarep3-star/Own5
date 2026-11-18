"""Unit + negative-control tests for the NFL Line-Originator Decision Desk (f2e20e96).

The verifier must pass on the pristine desk and FAIL when:
  - a source URL is stripped from a data row
  - a price value is filled without a verified source (policy P-01)
  - pinned row counts drift (a row is deleted)
  - a rendered table row loses its source link/marker
  - an internal link breaks
Negative controls run the real verifier against a corrupted scratch copy of the
repo subset (scripts + data + site), so the rules themselves are under test.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERIFY = os.path.join(ROOT, "scripts", "verify_f2e20e96.py")
BUILD = os.path.join(ROOT, "scripts", "build_f2e20e96.py")


def run_verify(root=None):
    script = os.path.join(root, "scripts", "verify_f2e20e96.py") if root else VERIFY
    return subprocess.run([sys.executable, script], capture_output=True, text=True)


class TestPristineDesk(unittest.TestCase):
    def test_verify_passes_on_committed_desk(self):
        p = run_verify()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            site1 = os.path.join(tmp, "a")
            shutil.copytree(os.path.join(ROOT, "nfl-desk-f2e20e96"), site1)
            subprocess.run([sys.executable, BUILD], check=True, capture_output=True)
            site2 = os.path.join(ROOT, "nfl-desk-f2e20e96")
            for name in os.listdir(site1):
                p1 = os.path.join(site1, name)
                if not os.path.isfile(p1):
                    continue
                with open(p1, "rb") as f:
                    first = f.read()
                with open(os.path.join(site2, name), "rb") as f:
                    second = f.read()
                self.assertEqual(first, second, f"non-deterministic page: {name}")

    def test_every_rendered_row_has_provenance(self):
        site = os.path.join(ROOT, "nfl-desk-f2e20e96")
        for name in os.listdir(site):
            if not name.endswith(".html"):
                continue
            html = open(os.path.join(site, name), encoding="utf-8").read()
            for m in re.finditer(r"<tr>(.*?)</tr>", html, re.S):
                row = m.group(1)
                if "<th>" in row:
                    continue
                self.assertTrue(
                    "<a href=" in row or "UNVERIFIED" in row
                    or "computed" in row.lower() or "registry:" in row,
                    f"{name}: row without provenance: {row[:80]}",
                )

    def test_no_market_price_values_anywhere(self):
        # policy P-01: market columns must stay blank + UNVERIFIED
        import csv
        with open(os.path.join(ROOT, "data", "nfl-desk-f2e20e96", "price_snapshots_wk11.csv"),
                  newline="") as f:
            for r in csv.DictReader(f):
                self.assertEqual(r["opening_price"], "")
                self.assertEqual(r["closing_price"], "")
                self.assertEqual(r["status"], "UNVERIFIED")


class TestNegativeControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for sub in ("scripts", "data"):
            shutil.copytree(os.path.join(ROOT, sub), os.path.join(self.tmp, sub),
                            ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(os.path.join(ROOT, "nfl-desk-f2e20e96"),
                        os.path.join(self.tmp, "nfl-desk-f2e20e96"))
        self.data = os.path.join(self.tmp, "data", "nfl-desk-f2e20e96")
        self.site = os.path.join(self.tmp, "nfl-desk-f2e20e96")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_stripping_a_source_url_fails(self):
        path = os.path.join(self.data, "week10_results.csv")
        rows = open(path, encoding="utf-8").read().splitlines()
        # strip every source URL from the first data row
        rows[1] = re.sub(r"https://[^,\"]*", "", rows[1])
        open(path, "w", encoding="utf-8").write("\n".join(rows) + "\n")
        p = run_verify(self.tmp)
        self.assertEqual(p.returncode, 1, "verifier must fail when a source URL is stripped")
        self.assertIn("V1", p.stdout)

    def test_filling_a_price_without_source_fails(self):
        path = os.path.join(self.data, "price_snapshots_wk11.csv")
        txt = open(path, encoding="utf-8").read()
        rows = txt.splitlines()
        cols = rows[1].split(",")
        cols[3] = "-110"  # opening_price
        rows[1] = ",".join(cols)
        open(path, "w", encoding="utf-8").write("\n".join(rows) + "\n")
        p = run_verify(self.tmp)
        self.assertEqual(p.returncode, 1)
        self.assertIn("price_snapshots_wk11.csv", p.stdout)

    def test_deleting_a_data_row_fails_count_pin(self):
        path = os.path.join(self.data, "injury_wk10_players.csv")
        rows = open(path, encoding="utf-8").read().splitlines()
        open(path, "w", encoding="utf-8").write("\n".join(rows[:-1]) + "\n")
        p = run_verify(self.tmp)
        self.assertEqual(p.returncode, 1)
        self.assertIn("V5", p.stdout)

    def test_row_without_provenance_marker_fails(self):
        path = os.path.join(self.site, "correlations.html")
        html = open(path, encoding="utf-8").read()
        # strip the source link + computed badge from the first data row
        corrupted = html.replace('href="https://www.nfl.com/standings/league/2026/REG"', "",
                                1)
        corrupted = corrupted.replace('class="badge computed"', 'class="badge"', 1)
        corrupted = corrupted.replace("computed in-repo", "ok", 1)
        open(path, "w", encoding="utf-8").write(corrupted)
        p = run_verify(self.tmp)
        self.assertEqual(p.returncode, 1)
        self.assertIn("V2", p.stdout)

    def test_broken_internal_link_fails(self):
        path = os.path.join(self.site, "index.html")
        html = open(path, encoding="utf-8").read()
        open(path, "w", encoding="utf-8").write(html.replace("gates.html", "gates-missing.html"))
        p = run_verify(self.tmp)
        self.assertEqual(p.returncode, 1)
        self.assertIn("V3", p.stdout)

    def test_planted_model_value_without_inputs_fails(self):
        # a model row must publish probability + inputs; tamper with computed output
        path = os.path.join(self.data, "computed", "model_lines_wk11.csv")
        rows = open(path, encoding="utf-8").read().splitlines()
        header = rows[0].split(",")
        pi = header.index("probability")
        parts = rows[1].split(",")
        parts[pi] = "0.9000"
        rows[1] = ",".join(parts)
        open(path, "w", encoding="utf-8").write("\n".join(rows) + "\n")
        p = run_verify(self.tmp)
        self.assertEqual(p.returncode, 1, "verifier must catch a tampered model output")


if __name__ == "__main__":
    unittest.main()

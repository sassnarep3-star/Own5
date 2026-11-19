"""Unit tests for the 715e2cd4 desk, including negative controls.

Run from the repo root:
    python3 -m unittest discover -s nfl-desk-715e2cd4/tests -v

The negative controls matter more than the happy paths: they prove the verifier
actually fails when the data is wrong.
"""

import csv
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

DESK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DESK)


def load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(DESK, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pipeline = load("pipeline")
verify = load("verify")
build = load("build")


class TestMath(unittest.TestCase):
    def test_norm_cdf_symmetry(self):
        self.assertAlmostEqual(pipeline.norm_cdf(0.0), 0.5, places=12)
        self.assertAlmostEqual(pipeline.norm_cdf(1.96) + pipeline.norm_cdf(-1.96), 1.0, places=12)

    def test_norm_cdf_known_values(self):
        self.assertAlmostEqual(pipeline.norm_cdf(1.0), 0.8413447, places=6)
        self.assertAlmostEqual(pipeline.norm_cdf(-2.0), 0.0227501, places=6)

    def test_pearson_perfect(self):
        self.assertAlmostEqual(pipeline.pearson([1, 2, 3, 4], [2, 4, 6, 8]), 1.0, places=12)
        self.assertAlmostEqual(pipeline.pearson([1, 2, 3, 4], [8, 6, 4, 2]), -1.0, places=12)

    def test_wilson_brackets_estimate(self):
        lo, hi = pipeline.wilson(64, 136)
        self.assertLess(lo, 64 / 136.0)
        self.assertGreater(hi, 64 / 136.0)
        self.assertAlmostEqual((lo + hi) / 2.0, 64 / 136.0, places=1)

    def test_fisher_ci_shrinks_with_n(self):
        lo_s, hi_s = pipeline.fisher_ci(0.5, 20)
        lo_l, hi_l = pipeline.fisher_ci(0.5, 2000)
        self.assertLess(hi_l - lo_l, hi_s - lo_s)

    def test_solve_linear_system(self):
        # 2x + y = 5 ; x + 3y = 10  ->  x=1, y=3
        out = pipeline.solve([[2.0, 1.0], [1.0, 3.0]], [5.0, 10.0])
        self.assertAlmostEqual(out[0], 1.0, places=9)
        self.assertAlmostEqual(out[1], 3.0, places=9)

    def test_singular_system_raises(self):
        with self.assertRaises(ValueError):
            pipeline.solve([[1.0, 1.0], [1.0, 1.0]], [1.0, 2.0])


class TestModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.standings = pipeline.load_standings()
        cls.corpus = pipeline.load_corpus()
        cls.teams = sorted(cls.standings)
        cls.model = pipeline.fit_ratings(cls.corpus, cls.teams, 5.0)
        cls.sigma = pipeline.fit_sigma(cls.model, cls.corpus)

    def test_corpus_is_136(self):
        self.assertEqual(len(self.corpus), 136)

    def test_ratings_are_centred(self):
        # a ridge fit on a balanced design leaves the mean rating near zero
        self.assertLess(abs(sum(self.model["off"].values()) / 32.0), 1.0)
        self.assertLess(abs(sum(self.model["def"].values()) / 32.0), 1.0)

    def test_predictions_are_sane(self):
        hp, ap = pipeline.predict(self.model, "TEN", "BUF")
        self.assertTrue(30 < hp + ap < 60, (hp, ap))
        self.assertGreater(hp - ap, 3)          # Buffalo is far stronger

    def test_stronger_team_gets_better_margin(self):
        # predict(away, home) -> (home_points, away_points)
        hp, ap = pipeline.predict(self.model, "MIA", "BUF")   # BUF at home
        self.assertGreater(hp - ap, 3)
        hp2, ap2 = pipeline.predict(self.model, "BUF", "MIA")  # BUF on the road
        self.assertLess(hp2 - ap2, -3)
        # the home club gains the same HFA in both directions
        self.assertAlmostEqual((hp - ap) + (hp2 - ap2), 2 * self.model["h"], places=6)

    def test_sigma_is_plausible(self):
        self.assertTrue(8 < self.sigma < 16, self.sigma)

    def test_reconciliation_has_no_mismatch(self):
        rec, bad, _ = pipeline.reconcile(self.standings, self.corpus, pipeline.load_results_wk10())
        self.assertEqual(bad, 0)
        self.assertEqual(len(rec), 32)

    def test_reconciliation_detects_a_tampered_score(self):
        corpus = [dict(g) for g in self.corpus]
        corpus[0]["home_pts"] += 7           # break one game
        _, bad, _ = pipeline.reconcile(self.standings, corpus, pipeline.load_results_wk10())
        self.assertGreaterEqual(bad, 2)      # both clubs in that game break


class TestPinnedData(unittest.TestCase):
    def test_counts(self):
        for fn, n in verify.REQUIRED_COUNTS.items():
            with open(os.path.join(DESK, "data", fn), encoding="utf-8") as fh:
                got = len(list(csv.DictReader(fh)))
            self.assertEqual(got, n, "%s: %d != %d" % (fn, got, n))

    def test_injury_counts_are_internally_consistent(self):
        with open(os.path.join(DESK, "data", "availability_week11.csv"), encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        out = sum(1 for r in rows if r["game_status"] == "Out")
        q = sum(1 for r in rows if r["game_status"] == "Questionable")
        with open(os.path.join(DESK, "data", "availability_summary.csv"), encoding="utf-8") as fh:
            summ = list(csv.DictReader(fh))
        self.assertEqual(out, sum(int(r["designated_out"]) for r in summ))
        self.assertEqual(q, sum(int(r["designated_questionable"]) for r in summ))

    def test_no_market_price_anywhere(self):
        with open(os.path.join(DESK, "data", "lines_week11.csv"), encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for r in rows:
            for f in ("market_home_spread", "market_total", "market_home_ml",
                      "spread_residual", "total_residual", "ml_residual"):
                self.assertEqual(r[f], "", "%s %s should be blank" % (r["game_id"], f))


class TestDeterminism(unittest.TestCase):
    def test_build_is_byte_identical(self):
        before = {p: open(os.path.join(DESK, p), "rb").read()
                  for p in verify.PAGES + ["style.css"]}
        build.main()
        for p, blob in before.items():
            self.assertEqual(blob, open(os.path.join(DESK, p), "rb").read(),
                             "%s changed on rebuild" % p)


class TestNegativeControls(unittest.TestCase):
    """Copy the desk to a scratch dir, break one thing, and prove verify fails."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="desk715-")
        self.dest = os.path.join(self.tmp, "desk")
        shutil.copytree(DESK, self.dest,
                        ignore=shutil.ignore_patterns("tests", "__pycache__"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_verify(self):
        proc = subprocess.run([sys.executable, os.path.join(self.dest, "verify.py")],
                              capture_output=True, text=True)
        return proc.returncode, proc.stdout + proc.stderr

    def _mutate(self, fn, old, new):
        path = os.path.join(self.dest, "data", fn)
        text = open(path, encoding="utf-8").read()
        self.assertIn(old, text, "mutation anchor not found in %s" % fn)
        open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))

    def test_clean_copy_passes(self):
        rc, out = self._run_verify()
        self.assertEqual(rc, 0, out)

    def test_injected_market_price_fails(self):
        self._mutate("lines_week11.csv", "W11-01,2026-11-19,8:15 PM,IND,HOU",
                     "W11-01,2026-11-19,8:15 PM,IND,HOU")
        # write a price into the first row's market_home_spread
        path = os.path.join(self.dest, "data", "lines_week11.csv")
        lines = open(path, encoding="utf-8").read().split("\n")
        header = lines[0].split(",")
        idx = header.index("market_home_spread")
        cells = lines[1].split(",")
        cells[idx] = "-2.5"
        lines[1] = ",".join(cells)
        open(path, "w", encoding="utf-8").write("\n".join(lines))
        rc, out = self._run_verify()
        self.assertEqual(rc, 1, "injected market price was not caught")
        self.assertIn("V7", out)

    def test_invented_depth_fails(self):
        path = os.path.join(self.dest, "data", "availability_week11.csv")
        lines = open(path, encoding="utf-8").read().split("\n")
        header = lines[0].split(",")
        idx = header.index("depth_rank")
        cells = lines[1].split(",")
        cells[idx] = "1"
        lines[1] = ",".join(cells)
        open(path, "w", encoding="utf-8").write("\n".join(lines))
        rc, out = self._run_verify()
        self.assertEqual(rc, 1, "invented depth rank was not caught")
        self.assertIn("V9", out)

    def test_row_count_drift_fails(self):
        path = os.path.join(self.dest, "data", "results_corpus.csv")
        lines = open(path, encoding="utf-8").read().rstrip("\n").split("\n")
        open(path, "w", encoding="utf-8").write("\n".join(lines[:-1]) + "\n")
        rc, out = self._run_verify()
        self.assertEqual(rc, 1)
        self.assertIn("V5", out)

    def test_leaderboard_performance_figure_fails(self):
        self._mutate("leaderboard.csv", "Zero scored bets so far.", "56.3% ATS in shadow")
        rc, out = self._run_verify()
        self.assertEqual(rc, 1, "a win rate on the leaderboard was not caught")
        self.assertIn("V6", out)

    def test_dropped_source_url_fails(self):
        self._mutate("correlations.csv",
                     "https://www.nfl.com/standings/league/2026/REG",
                     "https://example.invalid/nothing")
        rc, out = self._run_verify()
        # a replacement URL still counts as a URL, so this must still pass V1
        # but the *real* failure mode is a blanked source; test that instead
        path = os.path.join(self.dest, "data", "correlations.csv")
        text = open(path, encoding="utf-8").read()
        open(path, "w", encoding="utf-8").write(
            text.replace("https://example.invalid/nothing", "", 1))
        rc, out = self._run_verify()
        self.assertEqual(rc, 1, "a blanked source URL was not caught")
        self.assertIn("V1", out)

    def test_broken_internal_link_fails(self):
        path = os.path.join(self.dest, "index.html")
        text = open(path, encoding="utf-8").read()
        open(path, "w", encoding="utf-8").write(text.replace('href="luck.html"', 'href="luckk.html"'))
        rc, out = self._run_verify()
        self.assertEqual(rc, 1, "a broken internal link was not caught")
        self.assertIn("V3", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)

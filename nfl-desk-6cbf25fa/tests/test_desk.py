#!/usr/bin/env python3
"""Unit tests for desk 6cbf25fa: rebuild determinism, model identities,
negative controls (alarms must fire when data is corrupted)."""
import csv
import math
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import pipeline  # noqa: E402

D = os.path.join(ROOT, "data", "nfl-desk-6cbf25fa")


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class BuildTests(unittest.TestCase):
    def test_build_and_verify_pass(self):
        r1 = subprocess.run([sys.executable, os.path.join(HERE, "build.py")], capture_output=True, text=True)
        self.assertEqual(r1.returncode, 0, r1.stderr)
        r2 = subprocess.run([sys.executable, os.path.join(HERE, "verify.py")], capture_output=True, text=True)
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)

    def test_build_deterministic(self):
        import hashlib
        def snap():
            out = {}
            for f in sorted(os.listdir(HERE)):
                if f.endswith(".html"):
                    out[f] = hashlib.sha256(open(os.path.join(HERE, f), "rb").read()).hexdigest()
            return out
        a = snap()
        subprocess.run([sys.executable, os.path.join(HERE, "build.py")], capture_output=True, text=True, check=True)
        self.assertEqual(a, snap(), "rebuild changed page bytes (build is not deterministic)")


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus, _ = pipeline.load_corpus()
        cls.ratings = pipeline.compute_ratings(cls.corpus)

    def test_corpus_size_and_integrity(self):
        self.assertEqual(len(self.corpus), 150)
        for g in self.corpus:
            self.assertGreaterEqual(g["hs"], 0)
            self.assertGreaterEqual(g["as"], 0)
            self.assertIn(g["home"], pipeline.TEAM32)
            self.assertIn(g["away"], pipeline.TEAM32)

    def test_ratings_recentered_and_sigma_positive(self):
        r = self.ratings
        mo = sum(r["offensive_deviation"].values()) / 32
        me = sum(r["defensive_effectiveness"].values()) / 32
        self.assertAlmostEqual(mo, 0.0, places=6)
        self.assertAlmostEqual(me, 0.0, places=6)
        self.assertGreater(r["sigma_points"], 8.0)
        self.assertLess(r["sigma_points"], 22.0)
        self.assertEqual(r["hfa_n_home_games"] + 8, len(self.corpus), "8 neutral games expected in corpus")

    def test_probability_identity_via_norm(self):
        r = self.ratings
        p_raw = pipeline.norm_cdf(r["offensive_deviation"]["KC"] / r["sigma_points"])
        self.assertTrue(0.0 < p_raw < 1.0)
        self.assertEqual(r["ties"], 1)
        self.assertAlmostEqual(r["tie_rate"], r["ties"] / r["games_in_corpus"], places=4)
        # tie rate must reproduce exactly from the counts it is derived from
        self.assertAlmostEqual(r["tie_rate"] * r["games_in_corpus"], r["ties"], places=2)

    def test_round_half_convention(self):
        self.assertEqual(pipeline.round_half(2.3), 2.5)
        self.assertEqual(pipeline.round_half(2.2), 2.0)
        self.assertEqual(pipeline.round_half(-2.3), -2.5)
        self.assertEqual(pipeline.round_half(0.0), 0.0)

    def test_american_odds(self):
        self.assertEqual(pipeline.american_odds(0.5), -100)  # even odds price as -100
        self.assertEqual(pipeline.american_odds(0.75), -300)
        self.assertEqual(pipeline.american_odds(0.25), 300)


class NegativeControlTests(unittest.TestCase):
    """Corrupt a copy of the data in-memory patterns and ensure verify fails."""

    def test_verify_fails_on_missing_market(self):
        import shutil, tempfile
        with tempfile.TemporaryDirectory() as td:
            fake_root = td
            # copy the data tree, drop one snapshot, run a modified verify on it
            shutil.copytree(os.path.join(ROOT, "data", "nfl-desk-6cbf25fa"),
                            os.path.join(fake_root, "data", "nfl-desk-6cbf25fa"))
            snap_csv = os.path.join(fake_root, "data", "nfl-desk-6cbf25fa", "price_snapshots.csv")
            with open(snap_csv) as f:
                lines = f.readlines()
            os.remove(snap_csv)
            with open(snap_csv, "w") as f:
                f.writelines(lines[:-1])
            r = subprocess.run(
                [sys.executable, "-c",
                 "import sys,os;sys.path.insert(0,%r);os.chdir(%r);" % (HERE, fake_root) +
                 "import runpy;sys.argv=['verify.py'];" +
                 "import importlib.util;spec=importlib.util.spec_from_file_location('v',%r);" % os.path.join(HERE, "verify.py") +
                 "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);" +
                 "m.D=os.path.join(%r,'data','nfl-desk-6cbf25fa');sys.exit(m.main())" % fake_root],
                capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0, "verify passed despite a removed snapshot row")

    def test_verify_fails_on_filled_market_line(self):
        import shutil, tempfile
        with tempfile.TemporaryDirectory() as td:
            shutil.copytree(os.path.join(ROOT, "data", "nfl-desk-6cbf25fa"),
                            os.path.join(td, "data", "nfl-desk-6cbf25fa"))
            lines_csv = os.path.join(td, "data", "nfl-desk-6cbf25fa", "lines_week11.csv")
            text = open(lines_csv).read().replace(
                ",,0.470496", ",-1.0,0.470496", 1)  # fill market_line on first side row
            open(lines_csv, "w").write(text)
            r = subprocess.run(
                [sys.executable, "-c",
                 "import sys,os;os.chdir(%r);" % td +
                 "import importlib.util;spec=importlib.util.spec_from_file_location('v',%r);" % os.path.join(HERE, "verify.py") +
                 "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);" +
                 "m.D=os.path.join(%r,'data','nfl-desk-6cbf25fa');sys.exit(m.main())" % td],
                capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0, "verify passed despite a filled market line (F-P01 breach)")


class LedgerTests(unittest.TestCase):
    def test_deltas_reference_both_reads(self):
        ds = rows(os.path.join(D, "injury_reads", "deltas_2026-11-12_to_2026-11-18.csv"))
        self.assertGreater(len(ds), 0)
        for d in ds:
            self.assertEqual(d["prior_read_utc"], "2026-11-12T16:52:39Z")
            self.assertEqual(d["this_read_utc"], "2026-11-18T03:55:13Z")

    def test_capture_has_28_teams_playing_week10(self):
        rs = rows(os.path.join(D, "injury_reads", "capture_injuries_2026-11-18.csv"))
        teams = {r["team_code"] for r in rs}
        res = rows(os.path.join(D, "results_week10.csv"))
        playing = set()
        for g in res:
            playing |= {g["away_team"], g["home_team"]}
        self.assertEqual(teams, playing, "injury capture teams must equal week-10 participants")


if __name__ == "__main__":
    unittest.main()

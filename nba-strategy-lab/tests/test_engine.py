from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nba_strategy_engine", ROOT / "engine.py")
engine = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(engine)


class MathTests(unittest.TestCase):
    def test_pearson(self):
        self.assertAlmostEqual(engine.pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(engine.pearson([1, 2, 3], [6, 4, 2]), -1.0)
        self.assertIsNone(engine.pearson([1, 1], [2, 3]))

    def test_binomial_tail(self):
        self.assertAlmostEqual(engine.binomial_tail(2, 2, 0.5), 0.25)
        self.assertAlmostEqual(engine.binomial_tail(0, 10, 0.5), 1.0)
        with self.assertRaises(ValueError):
            engine.binomial_tail(11, 10, 0.5)

    def test_wilson_contains_observed_rate(self):
        lo, hi = engine.wilson(9, 14)
        self.assertLess(lo, 9 / 14)
        self.assertGreater(hi, 9 / 14)

    def test_american_roundtrip(self):
        self.assertEqual(engine.american(0.5), 100)
        self.assertEqual(engine.american(0.75), -300)
        with self.assertRaises(ValueError):
            engine.american(1.0)


class OutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads((ROOT / "data" / "summary.json").read_text())

    def rows(self, name):
        with (ROOT / "data" / name).open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def test_counts(self):
        self.assertEqual(self.summary["official_source_rows"], 275)
        self.assertEqual(self.summary["audit_checks"], 547)
        self.assertEqual(self.summary["lines"], 16)
        self.assertEqual(self.summary["candidates"], 9)
        self.assertEqual(self.summary["correlation_rows"], 22)

    def test_no_qualified_or_ranked_or_rewarded(self):
        self.assertEqual(self.summary["qualified"], 0)
        for row in self.rows("leaderboard.csv"):
            self.assertEqual(row["eligible"], "NO")
            for key in ("rank", "deflated_score", "roi", "reward"):
                self.assertEqual(row[key], "")

    def test_market_cells_blank(self):
        for row in self.rows("lines.csv"):
            for key in ("market_spread", "market_total", "market_price", "market_edge"):
                self.assertEqual(row[key], "")

    def test_all_strategies_fail_closed(self):
        for row in self.rows("strategies.csv"):
            self.assertEqual(row["qualification"], "NOT QUALIFIED")
            self.assertGreater(int(row["failed_gates"]), 0)
            self.assertEqual(row["p_holm"], "1.0")

    def test_pooled_combo_arithmetic(self):
        row = next(r for r in self.rows("correlations.csv") if r["group"] == "Pooled two players" and r["analysis"] == "25+ PTS & 3+ 3PM")
        self.assertEqual(row["n"], "125")
        self.assertEqual(row["joint_hit_rate"], "0.648")
        self.assertEqual(row["independence_product"], "0.5591")
        self.assertEqual(row["lift"], "1.159")

    def test_blank_schedule_fields_preserved(self):
        with (ROOT / "data" / "raw" / "schedule.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(all(r["venue"] == "" for r in rows))
        self.assertEqual(sum(r["tip_et_24h"] == "" for r in rows), 2)

    def test_deterministic_rebuild(self):
        paths = sorted((ROOT / "data").glob("*.csv")) + sorted(ROOT.glob("*.html"))
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        subprocess.run([sys.executable, str(ROOT / "engine.py")], check=True, capture_output=True)
        subprocess.run([sys.executable, str(ROOT / "build.py")], check=True, capture_output=True)
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()

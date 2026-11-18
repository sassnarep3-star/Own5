#!/usr/bin/env python3
"""Stdlib unit tests for nfl-desk-35fc3437 data integrity."""
import csv
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

def read_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

class StandingsTests(unittest.TestCase):
    def test_thirty_two_clubs(self):
        rows = read_csv("standings_2026.csv")
        self.assertEqual(len(rows), 32)
    def test_net_equals_pf_minus_pa(self):
        for r in read_csv("standings_2026.csv"):
            self.assertEqual(int(r["NET"]), int(r["PF"]) - int(r["PA"]))
    def test_pct_matches(self):
        for r in read_csv("standings_2026.csv"):
            w, l, t = int(r["W"]), int(r["L"]), int(r["T"])
            expected = (w + 0.5 * t) / (w + l + t)
            self.assertAlmostEqual(float(r["PCT"]), expected, places=3)

class ResultsTests(unittest.TestCase):
    def test_all_final(self):
        for r in read_csv("results_2026_wk10.csv"):
            self.assertEqual(r["status"], "FINAL")
    def test_winner_matches_score(self):
        for r in read_csv("results_2026_wk10.csv"):
            hs, as_ = int(r["home_score"]), int(r["away_score"])
            expected = r["home_team"] if hs > as_ else r["away_team"]
            self.assertEqual(r["winner"], expected)

class LinesTests(unittest.TestCase):
    def test_model_populated_market_blank(self):
        for r in read_csv("lines_originated_wk11.csv"):
            self.assertTrue(r["model_fair_spread"].strip())
            self.assertTrue(r["model_fair_total"].strip())
            self.assertEqual(r["market_spread"].strip(), "")
            self.assertEqual(r["market_total"].strip(), "")
            self.assertEqual(r["spread_difference"].strip(), "")

class CorrelationsTests(unittest.TestCase):
    def test_n_published(self):
        for r in read_csv("correlations.csv"):
            self.assertTrue(r["n"].strip())
            self.assertTrue(abs(float(r["r"])) <= 1.0)

class GatesTests(unittest.TestCase):
    def test_all_gates_have_status(self):
        for r in read_csv("gates.csv"):
            self.assertTrue(r["status"].strip())

class RequirementsTests(unittest.TestCase):
    def test_every_row_has_gate_and_clearing_number(self):
        for r in read_csv("requirements.csv"):
            self.assertTrue(r["gate"].strip())
            self.assertTrue(r["clearing_number"].strip())

if __name__ == "__main__":
    unittest.main()

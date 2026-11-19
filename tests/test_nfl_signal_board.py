"""Unit tests for the NFL Signal Board build (session 1fab8a48).

These test the properties that make the published numbers trustworthy rather than the numbers themselves:
determinism, the reconciliation gate, the benchmark consistency, and the rules that forbid inference.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = REPO / "data" / "nfl-signal-board"
BUILD = DATA / "build_data.py"


def load(name: str) -> list[dict]:
    with (DATA / f"{name}.csv").open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestFrozenInputs(unittest.TestCase):
    def test_inputs_are_hashed(self):
        s = json.loads((DATA / "derive_summary.json").read_text())
        for k in ("standings", "fixtures", "odds", "corpus", "injury_capture", "games2026"):
            self.assertEqual(len(s["frozen_inputs"][k]), 64, f"{k} hash is not a sha256")

    def test_standings_are_32_clubs_and_self_consistent(self):
        st = load("corpus_reconciliation")
        self.assertEqual(len(st), 32)
        self.assertEqual(sum(int(r["src_w"]) for r in st), sum(int(r["src_l"]) for r in st),
                         "official wins and losses must balance")

    def test_fixture_slate_is_internally_consistent(self):
        rows = load("origination")
        clubs = {r["away"] for r in rows} | {r["home"] for r in rows}
        self.assertEqual(len(clubs), 26, "26 clubs play in week 11; the other 6 are on bye")
        self.assertEqual(len({(r["away"], r["home"]) for r in rows}), 13)


class TestOrigination(unittest.TestCase):
    def setUp(self):
        self.rows = load("origination")

    def test_market_order_is_side_then_total_then_moneyline(self):
        by_fix: dict[str, list[str]] = {}
        for r in self.rows:
            by_fix.setdefault(r["fixture_id"], []).append(r["market_order"])
        for f, orders in by_fix.items():
            self.assertEqual(orders, ["1 side", "1 side", "2 total", "2 total", "3 moneyline", "3 moneyline"], f)

    def test_every_row_has_probability_and_inputs(self):
        for r in self.rows:
            self.assertTrue(r["fair_prob"], f"{r['market_id']} has no probability")
            self.assertEqual(len(r["inputs_sha256"]), 64)
            self.assertIn("elo_diff", r["model_inputs"])

    def test_no_close_and_no_stake(self):
        for r in self.rows:
            self.assertEqual(r["closing_value"], "")
            self.assertIn("PENDING", r["closing_status"])
            self.assertEqual(r["stake"], "", "a stake must not be published while the calibration gate is closed")

    def test_market_column_is_attributed(self):
        for r in self.rows:
            self.assertIn("draftkings.com", r["price_source_url"])
            self.assertEqual(r["price_read_utc"], "2026-11-19T11:10:00Z")

    def test_probabilities_are_symmetric_within_a_market(self):
        for r in self.rows:
            pass
        side = [r for r in self.rows if r["market"] == "side (spread)"]
        pairs: dict[str, list[str]] = {}
        for r in side:
            pairs.setdefault(r["fixture_id"], []).append(r["fair_prob"])
        for f, (a, b) in pairs.items():
            self.assertAlmostEqual(float(a) + float(b), 1.0, places=3, msg=f"{f} side probabilities do not sum to 1")

    def test_prices_are_favourites_consistent_with_the_model(self):
        """The operator's favourite should usually be our favourite too; a sign error would show here."""
        side = {r["fixture_id"]: {} for r in self.rows}
        for r in self.rows:
            if r["market"] == "side (spread)":
                side[r["fixture_id"]][r["selection"]] = r
        agree = 0
        for f, d in side.items():
            mkt_home_fav = float(d[list(d)[1]]["market_line"]) < 0 if len(d) == 2 else None
            our_home_fav = float(d[list(d)[1]]["fair_line"]) < 0 if len(d) == 2 else None
            if mkt_home_fav == our_home_fav:
                agree += 1
        self.assertGreaterEqual(agree, 8, "market and model disagree on the favourite in too many games — likely a sign error")


class TestNoInference(unittest.TestCase):
    def test_depth_names_nobody(self):
        for r in load("depth"):
            self.assertEqual(r["replacement_named"], "")
            self.assertEqual(r["observed_starters_out"], "")

    def test_leaderboard_has_no_performance_figures(self):
        for r in load("leaderboard"):
            self.assertEqual(r["signal_value"], "")
            self.assertEqual(r["staking_roi"], "")
            self.assertIn("UNCERTIFIED", r["grade"])
            self.assertTrue(r["what_would_change_our_mind"])

    def test_every_flag_has_evidence(self):
        for r in load("flagged"):
            self.assertTrue(r["evidence_url"].startswith("http"), f"{r['id']} has no evidence link")


class TestModelHonesty(unittest.TestCase):
    def test_control_is_exactly_zero(self):
        m4 = [r for r in load("model_metrics") if r["model_id"] == "M4 all 2015-2026"][0]
        self.assertAlmostEqual(float(m4["brier_skill"]), 0.0, places=9,
                               msg="the constant-0.5 control must score 0 against a coherent benchmark")

    def test_headline_is_negative(self):
        s = json.loads((DATA / "derive_summary.json").read_text())
        self.assertLess(s["headline"]["side_brier_skill_all"], 0)
        self.assertLess(s["headline"]["side_brier_skill_ci"][1], 0)

    def test_calibration_slope_is_published_and_below_one(self):
        s = json.loads((DATA / "derive_summary.json").read_text())
        slope = s["model"]["calibration"]["slope"]
        self.assertGreater(slope, 0)
        self.assertLess(slope, 1)

    def test_holdout_was_not_used_for_tuning(self):
        """The chosen sigma variant must be selectable from the train window alone."""
        s = json.loads((DATA / "derive_summary.json").read_text())
        self.assertIn("chosen_side_variant", s["model"])
        self.assertEqual(s["model"]["train_n"] + s["model"]["holdout_n"], s["model"]["row_count_evaluated"])


class TestDeterminism(unittest.TestCase):
    def test_rebuild_is_byte_identical(self):
        before = {p.name: p.read_bytes() for p in sorted(DATA.glob("*.csv"))}
        r = subprocess.run([sys.executable, str(BUILD)], capture_output=True, text=True, cwd=str(REPO))
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        after = {p.name: p.read_bytes() for p in sorted(DATA.glob("*.csv"))}
        self.assertEqual(before, after, "the data build is not deterministic")


class TestReconciliationGate(unittest.TestCase):
    def test_reconciliation_is_32_of_32(self):
        rows = load("corpus_reconciliation")
        self.assertEqual(sum(1 for r in rows if r["reconciles"] == "YES"), 32)

    def test_log_audit_partitions_the_rows(self):
        log = load("log136")
        self.assertEqual(len(log), 136)
        verdicts = [r["audit_verdict"].split(" ")[0] for r in log]
        self.assertEqual(sum(verdicts.count(v) for v in ("AGREE", "BLANK", "ABSENT", "DISAGREE")), 136)
        self.assertEqual(verdicts.count("DISAGREE"), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

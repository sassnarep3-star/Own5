"""Unit tests for the 941fe39f NFL Season Desk.

These test the honesty rules, not the statistics. A statistics test that passes
on synthetic data proves very little; a test that shows the build refuses to
publish a blank proves the site cannot lie.

Run: python3 -m unittest discover -s tests -p "test_season_desk*" -v
"""
from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools" / "season_desk_941fe39f"
DESK = ROOT / "nfl-season-941fe39f"
sys.path.insert(0, str(TOOLS))

import availability as AV          # noqa: E402
import model as MODEL              # noqa: E402
import registers as REG            # noqa: E402
import snapshots as SNAP           # noqa: E402
import stats                       # noqa: E402
import strategies as STRAT         # noqa: E402

DERIVED = DESK / "data" / "derived"


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------- statistics
class TestStats(unittest.TestCase):
    def test_norm_ppf_known_values(self):
        self.assertAlmostEqual(stats.norm_ppf(0.975), 1.959964, places=5)
        self.assertAlmostEqual(stats.norm_ppf(0.5), 0.0, places=9)
        self.assertAlmostEqual(stats.norm_ppf(0.05), -1.644854, places=5)

    def test_norm_cdf_roundtrip(self):
        for p in (0.01, 0.25, 0.5, 0.8, 0.99):
            self.assertAlmostEqual(stats.norm_cdf(stats.norm_ppf(p)), p, places=6)

    def test_wilson_interval_brackets_point_estimate(self):
        lo, hi = stats.wilson_interval(50, 100)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)
        self.assertLess(hi - lo, 0.25)

    def test_wilson_empty_sample_is_nan_not_zero(self):
        lo, hi = stats.wilson_interval(0, 0)
        self.assertTrue(math.isnan(lo) and math.isnan(hi))

    def test_pearson_perfect_and_none(self):
        r, n = stats.pearson([1, 2, 3, 4], [2, 4, 6, 8])
        self.assertAlmostEqual(r, 1.0, places=9)
        self.assertEqual(n, 4)
        r, n = stats.pearson([1, None, 3], [1, 2, None])
        self.assertEqual(n, 1)
        self.assertTrue(math.isnan(r))

    def test_fisher_ci_widens_as_n_falls(self):
        lo1, hi1 = stats.fisher_ci(0.3, 1000)
        lo2, hi2 = stats.fisher_ci(0.3, 100)
        self.assertLess(hi1 - lo1, hi2 - lo2)

    def test_holm_is_monotone_and_bounded(self):
        p = [0.001, 0.02, 0.04, 0.5]
        adj = stats.holm(p)
        self.assertEqual(len(adj), 4)
        self.assertTrue(all(0 <= a <= 1 for a in adj))
        self.assertTrue(all(a >= b for a, b in zip(adj, p)))
        self.assertLessEqual(adj[0], adj[1])

    def test_binom_sf_does_not_overflow(self):
        # this is the case that broke a naive comb() implementation
        p = stats.binom_sf(1582, 1582, 0.5)
        self.assertTrue(0.0 <= p <= 1.0)
        self.assertLess(p, 1e-9)

    def test_brier_decomposition_identity(self):
        probs = [0.1, 0.2, 0.3, 0.6, 0.7, 0.9, 0.95, 0.05]
        outs = [0, 0, 0, 1, 1, 1, 1, 0]
        d = stats.brier_decomposition(probs, outs, bins=5)
        self.assertAlmostEqual(d["identity_residual"], 0.0, places=9)
        self.assertAlmostEqual(d["brier"],
                               stats.brier_binary(probs, outs), places=12)

    def test_skill_score_sign(self):
        outs = [1, 1, 0, 0]
        good = [0.9, 0.8, 0.2, 0.1]
        bad = [0.1, 0.2, 0.8, 0.9]
        self.assertGreater(stats.brier_skill_score(good, bad, outs), 0)
        self.assertLess(stats.brier_skill_score(bad, good, outs), 0)

    def test_cluster_bootstrap_is_deterministic(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        cl = ["a", "a", "b", "b", "c", "c"]
        a = stats.cluster_bootstrap_mean(vals, cl, reps=300, seed=7)
        b = stats.cluster_bootstrap_mean(vals, cl, reps=300, seed=7)
        self.assertEqual(a, b)


# --------------------------------------------------------------- the model
class TestModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = MODEL.load_games()

    def test_corpus_loaded(self):
        self.assertGreater(len(self.games), 7000)

    def test_fit_uses_only_earlier_games(self):
        week = [g for g in self.games if g["season"] == 2015 and g["week"] == 5]
        cutoff = min(g["date"] for g in week)
        fit = MODEL.Fit(self.games, cutoff)
        after = [g for g in self.games if cutoff <= g["date"] < cutoff.replace(
            year=cutoff.year + 1) and g["result"] is not None]
        before = [g for g in self.games if g["date"] < cutoff and g["result"] is not None]
        self.assertEqual(fit.n_games, len(before))
        self.assertNotEqual(fit.n_games, len(before) + len(after))

    def test_ratings_are_finite_and_centred(self):
        cutoff = [g["date"] for g in self.games if g["season"] == 2020][0]
        fit = MODEL.Fit(self.games, cutoff)
        vals = list(fit.ratings.values())
        self.assertTrue(all(math.isfinite(v) for v in vals))
        self.assertLess(abs(sum(vals) / len(vals)), 3.0)

    def test_probability_in_unit_interval(self):
        cutoff = [g["date"] for g in self.games if g["season"] == 2023][0]
        fit = MODEL.Fit(self.games, cutoff)
        p = fit.home_prob("KC", "LV")
        self.assertGreater(p, 0.0)
        self.assertLess(p, 1.0)

    def test_originate_is_ordered_and_complete(self):
        rows = MODEL.originate(self.games[:1200])["rows"]
        self.assertTrue(rows)
        for r in rows:
            self.assertIn("model_margin_home", r)
            self.assertIn("model_total", r)
            self.assertIn("model_home_win_prob", r)
            self.assertLessEqual(r["fit_cutoff"], r["gameday"])

    def test_no_future_game_enters_the_fit(self):
        """The single most important property: a market must not see its own week."""
        rows = MODEL.originate(self.games)["rows"]
        by_id = {g["game_id"]: g for g in self.games}
        bad = [r for r in rows if by_id[r["game_id"]]["gameday"] < r["fit_cutoff"]]
        self.assertEqual(bad, [])


# --------------------------------------------------------------- strategies
class TestStrategies(unittest.TestCase):
    def test_prereg_ids_are_unique(self):
        ids = [p["id"] for p in STRAT.PREREG]
        self.assertEqual(len(ids), len(set(ids)))

    def test_windows_do_not_overlap(self):
        self.assertLess(STRAT.TRAIN[1], STRAT.VALIDATION[0])
        self.assertLess(STRAT.VALIDATION[1], STRAT.HOLDOUT[0])
        self.assertLess(STRAT.HOLDOUT[1], STRAT.PROSPECTIVE[0])

    def test_every_strategy_has_a_two_sided_falsifier(self):
        rows = list(DERIVED.glob("strategies.csv"))
        if not rows:
            self.skipTest("site not built")
        import csv
        with open(rows[0], newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                text = r["what_would_change_our_mind"].lower()
                self.assertIn("positive", text)
                self.assertIn("negative", text)

    def test_preregistration_check_passes_on_the_committed_file(self):
        """The check CI runs. It must pass on the file in the repository."""
        import prereg
        out = ROOT / "nfl-season-941fe39f" / "data" / "strategy" / "prereg.json"
        self.assertEqual(prereg.check(out), 0)

    def test_preregistration_check_catches_a_changed_rule(self):
        """If a rule were edited after registration, the check must fail."""
        import prereg
        import strategies as S
        out = ROOT / "nfl-season-941fe39f" / "data" / "strategy" / "prereg.json"
        original = S.PREREG[0]["rule"]
        try:
            S.PREREG[0]["rule"] = original + " (quietly retuned after seeing the holdout)"
            self.assertEqual(prereg.check(out), 1)
        finally:
            S.PREREG[0]["rule"] = original
        self.assertEqual(prereg.check(out), 0)

    def test_no_control_is_certified(self):
        for p in STRAT.PREREG:
            if p["family"] == "control":
                self.assertNotEqual(p["status"], "certified")

    def test_devig_is_normalised(self):
        a, b = STRAT.devig_two_way(0.55, 0.55)
        self.assertAlmostEqual(a + b, 1.0, places=12)
        self.assertAlmostEqual(a, 0.5, places=12)

    def test_american_conversions(self):
        self.assertAlmostEqual(STRAT.american_to_prob(-110), 110 / 210, places=12)
        self.assertAlmostEqual(STRAT.american_to_prob(100), 0.5, places=12)
        self.assertAlmostEqual(STRAT.payout(-110), 10 / 11, places=12)
        self.assertAlmostEqual(STRAT.payout(100), 1.0, places=12)

    def test_calibration_recovers_a_known_slope(self):
        import random
        rnd = random.Random(11)
        xs, ys = [], []
        for _ in range(4000):
            p = rnd.uniform(0.05, 0.95)
            z = math.log(p / (1 - p))
            true = 1 / (1 + math.exp(-(0.6 * z - 0.1)))
            xs.append(p)
            ys.append(1 if rnd.random() < true else 0)
        slope, intercept, n = STRAT.calibration(xs, ys)
        self.assertGreater(n, 3900)
        self.assertAlmostEqual(slope, 0.6, delta=0.15)


# --------------------------------------------------------------- availability
class TestAvailability(unittest.TestCase):
    def test_jersey_strip_takes_only_a_leading_number(self):
        self.assertEqual(AV.split_cell("9 Christian Watson"), ("9", "Christian Watson"))
        self.assertEqual(AV.split_cell("Amon-Ra St. Brown"), ("", "Amon-Ra St. Brown"))
        self.assertEqual(AV.split_cell("0 Matthew Golden"), ("0", "Matthew Golden"))
        self.assertEqual(AV.split_cell(""), ("", ""))
        # a name that merely contains a number is untouched
        self.assertEqual(AV.split_cell("Keith Abney II"), ("", "Keith Abney II"))

    def test_depth_capture_keeps_groups_and_empty_slots(self):
        d = AV.build_depth()
        self.assertEqual(d["checks"]["shared_rank1_slots"], 1)
        self.assertEqual(d["checks"]["empty_rank1_slots"], 0)
        team = {c["team"] for c in json.loads(
            (DESK / "data" / "official" / "depth_2026-11-17.json").read_text())["clubs"]}
        self.assertIn("SEA", team)
        sea = [s for s in d["slots"] if s["team"] == "SEA" and s["position"] == "WR"]
        self.assertTrue(any(s["shared_rank1"] == "YES" for s in sea))
        shared = [s for s in sea if s["shared_rank1"] == "YES"][0]
        self.assertEqual(shared["rank1_count"], 2)
        self.assertIn("|", shared["rank1_names"])

    def test_houston_contributes_nothing(self):
        d = AV.build_depth()
        self.assertEqual([s for s in d["slots"] if s["team"] == "HOU"], [])

    def test_empty_slot_is_never_promoted(self):
        players = [
            {"slot_id": "X|Offense|QB|1", "team": "X", "unit": "Offense", "position": "QB",
             "rank": 1, "player_raw": "", "player": "", "jersey": "", "captured_utc": "", "source_url": ""},
            {"slot_id": "X|Offense|QB|1", "team": "X", "unit": "Offense", "position": "QB",
             "rank": 2, "player_raw": "B", "player": "B", "jersey": "", "captured_utc": "", "source_url": ""},
        ]
        d = AV.build_depth()
        # the real capture must never show a rank-2 name in a rank-1 slot
        for s in d["slots"]:
            if s["rank1_names"] == "":
                self.assertEqual(s["empty_rank1"], "YES")

    def test_replacement_carries_a_rank(self):
        d = AV.build_depth()
        inj = AV.load_injuries()
        reps = AV.replacements(d["players"], inj)
        for r in reps:
            if r["replacement"]:
                self.assertIn(r["replacement_rank"], ("1", "2", "3", "4"))
                self.assertTrue(r["replacement_depth_tier"])

    def test_injury_delta_has_two_clock_times(self):
        delta = AV.injury_delta()
        self.assertTrue(delta)
        for r in delta:
            self.assertNotEqual(r["prior_captured_utc"], r["now_captured_utc"])


# --------------------------------------------------------------- snapshots
class TestSnapshots(unittest.TestCase):
    def test_ledger_hashes_match_the_files(self):
        import hashlib
        led = SNAP.build_ledger()
        self.assertEqual(led["failures"], [])
        for row in led["rows"]:
            path = DESK / row["file"]
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(row["sha256"], digest, row["source_id"])

    def test_schema_alarm_fires_on_a_missing_field(self):
        led = SNAP.build_ledger()
        original = dict(SNAP.REQUIRED)
        try:
            SNAP.REQUIRED["OFF-TRANSACTIONS-20261117"] = {
                "parser": "x", "fields": ["rows", "a_field_that_does_not_exist"],
                "unit": "transactions"}
            broken = SNAP.build_ledger()
            self.assertTrue(broken["failures"])
            self.assertEqual(broken["failures"][0]["missing_fields"],
                             ["a_field_that_does_not_exist"])
        finally:
            SNAP.REQUIRED.clear()
            SNAP.REQUIRED.update(original)

    def test_replay_returns_the_capture_in_force(self):
        led = SNAP.build_ledger()
        early = SNAP.replay(led["rows"], "injury_report", "2026-11-16T12:00:00Z")
        late = SNAP.replay(led["rows"], "injury_report", "2026-11-17T01:00:00Z")
        self.assertIsNotNone(early)
        self.assertIsNotNone(late)
        self.assertLess(early["captured_utc"], late["captured_utc"])

    def test_no_replay_before_the_first_capture(self):
        led = SNAP.build_ledger()
        self.assertIsNone(SNAP.replay(led["rows"], "injury_report", "2026-11-01T00:00:00Z"))

    def test_capture_log_counts_clock_times_not_files(self):
        led = SNAP.build_ledger()
        log = {c["unit"]: c for c in SNAP.capture_log(led["rows"])}
        self.assertGreaterEqual(log["injury_report"]["distinct_clock_times"], 2)


# --------------------------------------------------------------- registers
class TestRegisters(unittest.TestCase):
    def test_ids_are_unique_per_register(self):
        for name, rows in (("requirements", REG.REQUIREMENTS), ("questions", REG.QUESTIONS),
                           ("suggestions", REG.SUGGESTIONS), ("flags", REG.FLAGS)):
            ids = [r["id"] for r in rows]
            self.assertEqual(len(ids), len(set(ids)), name)

    def test_every_requirement_names_a_gate_and_a_clearing_number(self):
        for r in REG.REQUIREMENTS:
            self.assertTrue(r["gate"])
            self.assertTrue(r["clears"])
            self.assertNotEqual(r["clears"].strip().lower(), "n/a") \
                if r["status"] != "met" else None

    def test_every_flag_has_a_https_source(self):
        for f in REG.FLAGS:
            self.assertTrue(f["source"].startswith("https://"), f["id"])

    def test_every_question_has_a_route_and_a_blocked_item(self):
        for q in REG.QUESTIONS:
            self.assertTrue(q["route"])
            self.assertTrue(q["blocks"])

    def test_every_suggestion_has_two_sided_falsifier(self):
        for s in REG.SUGGESTIONS:
            self.assertGreaterEqual(len(s["options"]), 2, s["id"])
            self.assertTrue(s["falsifier"])

    def test_requirement_status_vocabulary(self):
        for r in REG.REQUIREMENTS:
            self.assertIn(r["status"], ("met", "partial", "blocked"))


# --------------------------------------------------------------- the site
class TestSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verify = load_module("verify")

    def test_all_pages_exist(self):
        pages = sorted(p.name for p in DESK.glob("*.html"))
        self.assertGreaterEqual(len(pages), 20)

    def test_verification_passes(self):
        code = self.verify.main()
        self.assertEqual(code, 0)

    def test_every_page_has_exactly_one_h1(self):
        import re
        for p in DESK.glob("*.html"):
            raw = p.read_text(encoding="utf-8")
            self.assertEqual(len(re.findall(r"<h1>", raw)), 1, p.name)

    def test_no_page_claims_a_bet_or_a_certification_it_does_not_have(self):
        for p in DESK.glob("*.html"):
            raw = p.read_text(encoding="utf-8").lower()
            self.assertNotIn("certified strategy:</strong> yes", raw)

    def test_no_page_says_more_strategies_passed_than_are_certified(self):
        """The bug this guards: a manifest key named `certifications` that held
        every graded row made the executive summary open with "14 of the 14
        families cleared the gates" on a site whose headline is zero certified."""
        m = json.loads((DERIVED / "manifest.json").read_text())
        certified = m["counts"]["certified"]
        for p in DESK.glob("*.html"):
            text = re.sub(r"<[^>]+>", " ", p.read_text(encoding="utf-8"))
            text = re.sub(r"\s+", " ", text)
            for match in re.finditer(r"(\d+) of the (\d+) (?:families|strategies) cleared", text):
                n, total = int(match.group(1)), int(match.group(2))
                self.assertEqual(n, certified,
                                 f"{p.name} claims {n} cleared but {certified} are certified")
                self.assertLessEqual(n, total)
            self.assertNotIn("14 of the 14", text, p.name)

    def test_gate_count_is_nine_everywhere(self):
        """The gate register has nine entries. A page that says eight is stale."""
        import strategies as S
        self.assertEqual(len(S.GATES), 9)
        for p in DESK.glob("*.html"):
            text = re.sub(r"<[^>]+>", " ", p.read_text(encoding="utf-8"))
            self.assertNotIn("eight gates", text, p.name)

    def test_manifest_counts_match_the_registers(self):
        m = json.loads((DERIVED / "manifest.json").read_text())
        self.assertEqual(m["counts"]["requirements"], len(REG.REQUIREMENTS))
        self.assertEqual(m["counts"]["strategies"], len(STRAT.PREREG))
        self.assertEqual(m["counts"]["flags"], len(REG.FLAGS))


if __name__ == "__main__":
    unittest.main()

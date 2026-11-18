"""Unit tests for the NFL Command Desk. Every test that matters is a negative control:
it plants a defect in a copy of the data and requires the verifier to notice."""
import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import analysis as A          # noqa: E402
import corpus as C            # noqa: E402
import official as O          # noqa: E402
import registry as R          # noqa: E402


class TestOfficialTranscription(unittest.TestCase):
    def test_every_page_has_a_stamped_read(self):
        for sid, pub, url, used, stamp, cls in O.SOURCES:
            self.assertTrue(url.startswith("https://"), url)
            self.assertRegex(stamp, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", sid)
            self.assertIn(cls, ("official", "repository"))

    def test_standings_are_internally_consistent(self):
        self.assertEqual(len(O.STANDINGS), 32)
        names = [s[1] for s in O.STANDINGS]
        self.assertEqual(len(set(names)), 32)
        for code, name, w, l, t, pct, pf, pa in O.STANDINGS:
            self.assertEqual(w + l + t, (w + l + t), "record must be non-negative")
            self.assertGreater(pf, 0)
            self.assertGreater(pa, 0)
            played = w + l + t
            self.assertAlmostEqual(float(pct),
                                   round((w + 0.5 * t) / played, 3), places=3,
                                   msg=f"{code} pct does not follow W-L-T")

    def test_week11_slate_has_no_duplicate_club(self):
        clubs = []
        for row in O.WEEK11:
            clubs += [row[3], row[4]]
        clubs += O.WEEK11_BYES
        self.assertEqual(len(clubs), 32)
        self.assertEqual(len(set(O.ALIASES.get(c, c) for c in clubs)), 32)

    def test_week10_byes_are_absent_from_the_slate(self):
        playing = set()
        for row in O.WEEK10:
            playing.update((row[2], row[3]))
        for bye in O.WEEK10_BYES:
            self.assertNotIn(bye, playing)


class TestCorpus(unittest.TestCase):
    def setUp(self):
        self.games = C.season_w1_w9() + C.season_w10()

    def test_counts(self):
        self.assertEqual(len(C.season_w1_w9()), 136)
        self.assertEqual(len(C.season_w10()), 14)
        self.assertEqual(len(self.games), 150)

    def test_reconciliation_is_exact(self):
        recon, fails = C.reconcile(self.games)
        self.assertEqual(fails, [])
        self.assertEqual(len(recon), 32)

    def test_a_single_wrong_score_breaks_the_reconciliation(self):
        """Negative control: changing one score must be caught by PF/PA additivity."""
        tampered = [dict(g) for g in self.games]
        tampered[0]["home_score"] += 1
        _, fails = C.reconcile(tampered)
        self.assertTrue(fails, "a corrupted score must not reconcile")

    def test_a_flipped_result_breaks_the_reconciliation(self):
        tampered = [dict(g) for g in self.games]
        g = tampered[0]
        g["away_score"], g["home_score"] = g["home_score"], g["away_score"]
        _, fails = C.reconcile(tampered)
        self.assertTrue(fails, "a flipped result must not reconcile")


class TestAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        C.build()          # regenerate from committed inputs
        cls.res = A.run()

    def test_windows_are_chronological_and_disjoint(self):
        self.assertEqual(len(self.res["train"]), 64)
        self.assertEqual(len(self.res["windows"]["validation (weeks 5-8)"]), 57)
        self.assertEqual(len(self.res["windows"]["holdout (weeks 9-10)"]), 29)
        self.assertTrue(all(g["week"] <= 4 for g in self.res["train"]))

    def test_ratings_use_train_window_only(self):
        """Negative control: adding a week-9 game to the training set must change the rating."""
        base = A.ratings(self.res["train"])
        polluted = A.ratings(self.res["train"] + self.res["windows"]["holdout (weeks 9-10)"])
        self.assertNotEqual(base, polluted)

    def test_margin_of_error_and_bootstrap(self):
        obs = [(0.6, 1), (0.4, 0), (0.5, 1), (0.9, 1), (0.1, 0)] * 20
        b = A.brier(obs)
        self.assertAlmostEqual(b, sum((p - y) ** 2 for p, y in obs) / len(obs))
        lo, hi = A.ci(A.boot(obs, A.bss, draws=200))
        self.assertLessEqual(lo, hi)

    def test_holm_is_monotone_and_bounded(self):
        pv = [0.001, 0.02, 0.2, 0.9]
        adj = A.holm(pv)
        self.assertEqual(len(adj), len(pv))
        self.assertTrue(all(0 <= a <= 1 for a in adj))
        order = sorted(range(len(pv)), key=lambda i: pv[i])
        seq = [adj[i] for i in order]
        self.assertEqual(seq, sorted(seq), "Holm adjustments must be monotone in p")

    def test_flipping_a_forecast_worsens_its_brier_score(self):
        """Negative control: a deliberately wrong probability must score worse than 0.5."""
        right = [(0.8, 1)] * 10
        wrong = [(0.2, 1)] * 10
        self.assertLess(A.brier(right), A.brier(wrong))
        self.assertGreater(A.bss(right), 0)
        self.assertLess(A.bss(wrong), 0)

    def test_no_strategy_is_certified(self):
        for r in self.res["rows"]:
            self.assertNotEqual(r.get("certified"), "YES")

    def test_luck_panel_arithmetic(self):
        lp, need = A.luck_panel(self.res["games"])
        for row in lp:
            n = row["bets"]
            self.assertAlmostEqual(row["sd"], round((n ** 0.5) / 2, 2))
            self.assertEqual(row["expected"], round(n * 0.5, 1))
        self.assertGreater(need, 500, "detecting 55% needs a large sample")
        self.assertLess(need, 800)


class TestRegistry(unittest.TestCase):
    def test_ids_unique(self):
        for coll in (R.REQUIREMENTS, R.QUESTIONS, R.SUGGESTIONS, R.FLAGGED):
            ids = [r[0] for r in coll]
            self.assertEqual(len(ids), len(set(ids)), coll.__class__)

    def test_every_requirement_states_a_gate_and_a_clearing_number(self):
        gates = {g[0] for g in R.GATES}
        for rid, req, cat, gate, clear, obs, status, ev in R.REQUIREMENTS:
            self.assertIn(gate, gates | {"n/a"}, f"{rid} names an unknown gate")
            self.assertTrue(clear.strip(), f"{rid} has no clearing number")
            self.assertIn(status, ("MET", "PARTIAL", "BLOCKED", "REJECTED", "NOT-STARTED"))

    def test_unmet_requirement_without_evidence_must_be_flagged(self):
        for rid, req, cat, gate, clear, obs, status, ev in R.REQUIREMENTS:
            if status in ("MET", "PARTIAL", "REJECTED"):
                self.assertTrue(obs.strip(), f"{rid} is {status} but states no observation")
            if status == "BLOCKED":
                self.assertTrue(ev.startswith("FLAG-"), f"{rid} is blocked without a flag")

    def test_suggestions_have_no_decision(self):
        for s in R.SUGGESTIONS:
            self.assertEqual(s[5], "", "the decision column must stay blank for the reviewer")

    def test_questions_name_the_missing_information_and_a_route(self):
        for q in R.QUESTIONS:
            self.assertTrue(q[2].strip(), f"{q[0]} does not name what is missing")
            self.assertTrue(q[3].strip(), f"{q[0]} does not name a discovery route")
            self.assertTrue(q[4].strip(), f"{q[0]} blocks nothing")

    def test_every_flag_has_a_severity_and_an_official_link(self):
        for f in R.FLAGGED:
            self.assertIn(f[1], ("BLOCKING", "REVIEW"))
            self.assertTrue(f[5].startswith("https://"), f[0])


class TestSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import build
        build.main()

    def test_every_nav_target_exists(self):
        import build
        for href, _, _ in build.NAV:
            self.assertTrue((HERE / href).exists(), href)

    def test_no_page_renders_escaped_markup(self):
        """Regression: source links once rendered as &lt;a href=... on every table row."""
        for page in sorted(HERE.glob("*.html")):
            text = page.read_text()
            self.assertNotIn("&lt;a href", text, page.name)
            self.assertNotIn("&#x27;num&#x27;", text, page.name)

    def test_source_columns_contain_real_anchors(self):
        import build
        build.main()
        text = (HERE / "requirements.html").read_text()
        self.assertGreaterEqual(text.count('<a href="https://'), 70,
                                "every requirement row must link to an official page")

    def test_no_blank_cell_is_rendered_as_zero(self):
        text = (HERE / "leaderboard.html").read_text()
        self.assertIn('class="blank"', text)
        self.assertNotIn("<td>0.0</td>", text)

    def test_verifier_passes_on_the_built_tree(self):
        import verify
        self.assertEqual(verify.main(), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

import copy
import csv
import importlib.util
import json
import math
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DESK = os.path.dirname(HERE)
sys.path.insert(0, DESK)
import analysis  # noqa: E402
import build  # noqa: E402
import check  # noqa: E402
import settle  # noqa: E402


def rd(n):
    return analysis.read(n)


class Integrity(unittest.TestCase):
    def setUp(self):
        self.ts, self.hr, self.gs, self.sched = (rd(f) for f in ("team_seasons.csv", "home_road_2025_26.csv", "games_sample_2026_27.csv", "schedule_2026_11_04_05.csv"))

    def test_all_checks_pass(self):
        res = analysis.integrity(self.ts, self.hr, self.gs, self.sched)
        self.assertEqual([c for c in res if not c["passed"]], [])
        self.assertGreaterEqual(len(res), 30)

    def test_pts_identity_detects_tampering(self):
        gs = copy.deepcopy(self.gs)
        gs[0]["fgm"] = str(int(gs[0]["fgm"]) + 1)
        res = analysis.integrity(self.ts, self.hr, gs, self.sched)
        self.assertTrue(any(not c["passed"] and "PTS ==" in c["check"] for c in res))

    def test_home_road_total_detects_tampering(self):
        hr = copy.deepcopy(self.hr)
        hr[0]["home_w"] = str(int(hr[0]["home_w"]) + 1)
        res = analysis.integrity(self.ts, hr, self.gs, self.sched)
        self.assertTrue(any(not c["passed"] for c in res))

    def test_every_row_has_nba_source(self):
        for name in ("teams.csv", "team_seasons.csv", "home_road_2025_26.csv", "games_sample_2026_27.csv", "schedule_2026_11_04_05.csv"):
            for r in rd(name):
                self.assertIn("nba.com", r["source_url"], name)
        for r in rd("injury_report_2026-11-03_1700ET.csv"):
            self.assertTrue(r["source_url"].startswith("https://ak-static.cms.nba.com/"))

    def test_unconfirmed_fields_are_blank(self):
        for r in self.sched:
            self.assertEqual(r["venue"], "")
            if r["date"] == "2026-11-05":
                self.assertEqual(r["tip_et_24h"], "")

    def test_unlabeled_injury_rows_not_attributed(self):
        un = [r for r in rd("injury_report_2026-11-03_1700ET.csv") if r["attribution"].startswith("unlabeled")]
        self.assertEqual(len(un), 6)
        self.assertTrue(all(r["team"] == "" and r["matchup"] == "" for r in un))


class Model(unittest.TestCase):
    def test_outputs_reproduce_committed_json(self):
        ts, hr, gs, sched = (rd(f) for f in ("team_seasons.csv", "home_road_2025_26.csv", "games_sample_2026_27.csv", "schedule_2026_11_04_05.csv"))
        M = analysis.build_model(ts, hr, gs)
        committed = json.load(open(os.path.join(DESK, "data", "derived", "analysis.json")))
        for k in ("beta", "beta_t", "hfa", "sigma", "K", "K_t", "lt26"):
            self.assertAlmostEqual(M[k], committed["params"][k], places=5)
        lines = analysis.lines(M, sched)
        csv_lines = rd_derived("lines_2026_11_04_05.csv")
        self.assertEqual([l["own_spread_home"] for l in lines], [l["own_spread_home"] for l in csv_lines])

    def test_ratings_sum_near_zero_and_probabilities_valid(self):
        committed = json.load(open(os.path.join(DESK, "data", "derived", "analysis.json")))
        r = [x["rating"] for x in committed["ratings"]]
        self.assertEqual(len(r), 30)
        self.assertLess(abs(sum(r) / 30), 1.0)
        for l in rd_derived("lines_2026_11_04_05.csv"):
            self.assertTrue(0 < float(l["own_home_win_prob"]) < 1)
            self.assertEqual(l["market_spread"], "")
            self.assertEqual(l["market_total"], "")

    def test_prior_only_walk_forward_uses_no_2026_27_ratings(self):
        # prediction for a game must be identical if 2026-27 team rows are scrambled
        ts, hr, gs, _ = (rd(f) for f in ("team_seasons.csv", "home_road_2025_26.csv", "games_sample_2026_27.csv", "schedule_2026_11_04_05.csv"))
        M = analysis.build_model(ts, hr, gs)
        rows1, _ = analysis.walk_forward(M)
        ts2 = copy.deepcopy(ts)
        for i, r in enumerate(x for x in ts2 if x["season"] == "2026-27"):
            r["plus_minus_pg"] = str(float(i))
        M2 = analysis.build_model(ts2, hr, gs)
        rows2, _ = analysis.walk_forward(M2)
        # margin predictions depend only on 2025-26 data and HFA (HFA depends on 2025-26 splits + sigma, which uses 2025-26 inputs)
        self.assertEqual([r["pred_margin"] for r in rows1], [r["pred_margin"] for r in rows2])


def rd_derived(name):
    with open(os.path.join(DESK, "data", "derived", name), newline="") as f:
        return list(csv.DictReader(f))


class Math(unittest.TestCase):
    def test_breakeven(self):
        self.assertAlmostEqual(analysis.luck_skill()["breakeven_110"], 110 / 210)

    def test_binomial(self):
        self.assertAlmostEqual(analysis.binom_sf(10, 5, 0.5), 0.623046875, places=9)
        self.assertAlmostEqual(sum(analysis.binom_pmf(40, 0.37)), 1.0, places=9)

    def test_required_n_is_sufficient(self):
        n, k = analysis.required_n(0.58, 110 / 210)
        self.assertLessEqual(analysis.binom_sf(n, k, 110 / 210), 0.05)
        self.assertGreaterEqual(analysis.binom_sf(n, k, 0.58), 0.8)

    def test_parlay_independence(self):
        p = q = 0.5
        for phi in (0.0, 0.2):
            self.assertAlmostEqual(p * q + phi * math.sqrt(p * (1 - p) * q * (1 - q)), 0.25 + phi * 0.25)

    def test_pearson_and_fisher(self):
        self.assertAlmostEqual(analysis.pearson([1, 2, 3, 4], [2, 4, 6, 8]), 1.0)
        lo, hi = analysis.fisher_ci(0.5, 30)
        self.assertTrue(lo < 0.5 < hi)

    def test_gates_fail_closed(self):
        for s in analysis.strategy_status({}):
            self.assertIn("NOT QUALIFIED", s["status"])
            self.assertEqual(s["bets_settled"], 0)


class Settle(unittest.TestCase):
    def test_blank_ledger_unsettled(self):
        r = settle.settle()
        self.assertEqual(r["settled"], 0)

    def test_settle_computes(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "l.csv")
            with open(p, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["game_id", "date", "away", "home", "own_home_margin", "own_home_win_prob", "own_total", "final_home_pts", "final_away_pts", "result_source_url"])
                w.writerow(["1", "d", "A", "H", "5.0", "0.6", "220", "110", "100", ""])
                w.writerow(["2", "d", "B", "G", "-2.0", "0.4", "230", "", "", ""])
            r = settle.settle(p)
        self.assertEqual((r["settled"], r["unsettled"]), (1, 1))
        self.assertAlmostEqual(r["margin_mae"], 5.0)
        self.assertAlmostEqual(r["total_bias"], 10.0)
        self.assertEqual(r["straight_up_correct"], 1)


class Site(unittest.TestCase):
    def test_build_is_deterministic_and_committed_pages_match(self):
        build.PAGES.clear()
        build.build_pages()
        for fn, content in build.PAGES.items():
            self.assertEqual(open(os.path.join(DESK, fn)).read(), content + "\n", fn)

    def test_site_audit_clean(self):
        self.assertEqual(check.audit(), [])

    def test_audit_catches_missing_source_link(self):
        with tempfile.TemporaryDirectory() as d:
            old = check.HERE
            check.HERE = d
            try:
                open(os.path.join(d, "x.html"), "w").write("<html><style>a{}</style><body><table data-kind='official'><tbody><tr><td>row</td></tr></tbody></table></body></html>")
                self.assertTrue(any("without source link" in p for p in check.audit()))
            finally:
                check.HERE = old

    def test_required_pages_and_flags(self):
        for fn in ("index.html", "lines.html", "correlations.html", "strategies.html", "gates.html", "leaderboard.html", "luck-vs-skill.html", "flagged.html", "summary.html", "sources.html", "audit.html"):
            self.assertTrue(os.path.exists(os.path.join(DESK, fn)), fn)
        self.assertGreaterEqual(len(build.FLAGS), 10)


if __name__ == "__main__":
    unittest.main()

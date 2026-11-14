"""The arithmetic the whole desk leans on, checked against hand-computable cases."""
import unittest

from helpers import DESK  # noqa: F401  (path setup)
import statslib as st


class TestPrices(unittest.TestCase):
    def test_american_to_prob(self):
        self.assertAlmostEqual(st.american_to_prob(-110), 110 / 210, places=10)
        self.assertAlmostEqual(st.american_to_prob(+100), 0.5, places=10)
        self.assertAlmostEqual(st.american_to_prob(+150), 100 / 250, places=10)
        self.assertAlmostEqual(st.american_to_prob(-120), 120 / 220, places=10)
        self.assertIsNone(st.american_to_prob(""))
        self.assertIsNone(st.american_to_prob(0))

    def test_prob_to_american_round_trip(self):
        for p in (0.52, 0.55, 0.6, 0.7, 0.35, 0.2):
            a = st.prob_to_american(p)
            back = st.american_to_prob(a)
            self.assertLessEqual(abs(back - p), 0.005, f"p={p} -> {a} -> {back}")

    def test_devig_and_hold(self):
        pa, pb = st.american_to_prob(-110), st.american_to_prob(-110)
        da, db = st.devig_two_way(pa, pb)
        self.assertAlmostEqual(da, 0.5, places=9)
        self.assertAlmostEqual(db, 0.5, places=9)
        self.assertAlmostEqual(st.hold_pct(pa, pb), 100 * (pa + pb - 1.0), places=9)
        self.assertGreater(st.hold_pct(pa, pb), 4.0)      # a -110/-110 pair holds ~4.54%

    def test_devig_ignores_nothing(self):
        # an unbalanced 2-way market must not devig to a fair 50/50
        da, db = st.devig_two_way(st.american_to_prob(-200), st.american_to_prob(+160))
        self.assertGreater(da, db)
        self.assertAlmostEqual(da + db, 1.0, places=9)


class TestDistributions(unittest.TestCase):
    def test_norm_cdf_known_values(self):
        self.assertAlmostEqual(st.norm_cdf(0.0), 0.5, places=9)
        self.assertAlmostEqual(st.norm_cdf(1.959964), 0.975, places=5)
        self.assertAlmostEqual(st.norm_cdf(-1.0), 0.158655, places=5)

    def test_norm_ppf_inverse(self):
        for p in (0.01, 0.1, 0.25, 0.5, 0.9, 0.975):
            self.assertAlmostEqual(st.norm_cdf(st.norm_ppf(p)), p, places=5)

    def test_binom_exact_two_sided(self):
        # ten heads in a row: the only equally-extreme outcome is ten tails
        self.assertAlmostEqual(st.binom_two_sided(10, 10, 0.5), 2 * 0.5 ** 10, places=12)
        self.assertGreater(st.binom_two_sided(10, 6, 0.5), 0.5)

    def test_wilson_contains_point_estimate(self):
        lo, hi = st.wilson_ci(50, 100)
        self.assertLess(lo, 0.5)
        self.assertGreater(hi, 0.5)
        lo2, hi2 = st.wilson_ci(500, 1000)
        self.assertLess(hi2 - lo2, hi - lo)               # more data, narrower interval

    def test_mcnemar(self):
        self.assertEqual(st.mcnemar_exact(0, 0), 1.0)
        # 12-0 discordance is the classic small-sample case where a chi-square
        # approximation would overstate significance and the exact test does not
        p = st.mcnemar_exact(12, 0)
        self.assertLess(p, 0.001)
        self.assertAlmostEqual(p, 2 * 0.5 ** 12, places=9)
        self.assertGreater(st.mcnemar_exact(7, 5), 0.4)

    def test_phi_and_chi(self):
        phi, chi, p, n = st.phi_table(50, 50, 50, 50)
        self.assertAlmostEqual(phi, 0.0, places=9)
        self.assertGreater(p, 0.9)
        self.assertEqual(n, 200)
        phi2, _, p2, _ = st.phi_table(90, 10, 10, 90)
        self.assertGreater(phi2, 0.5)
        self.assertLess(p2, 1e-9)

    def test_solve_small_system(self):
        A = [[2.0, 1.0], [1.0, 3.0]]
        x = st.solve(A, [3.0, 5.0])
        self.assertAlmostEqual(x[0], 0.8, places=9)
        self.assertAlmostEqual(x[1], 1.4, places=9)


class TestMoney(unittest.TestCase):
    def test_units_pnl(self):
        # -110 pays 10/11 per unit; a loss costs exactly one unit; a push returns the stake
        out = st.units_pnl(["win", "loss", "push"], [-110, -110, -110])
        self.assertAlmostEqual(out[0], 100 / 110, places=9)
        self.assertEqual(out[1], -1.0)
        self.assertEqual(out[2], 0.0)

    def test_drawdown_and_streak(self):
        pnl = [1.0, -0.5, -0.5, -0.5, 2.0]
        self.assertAlmostEqual(st.max_drawdown(pnl), -1.5, places=9)
        self.assertEqual(st.longest_losing_streak(pnl), 3)

    def test_kelly(self):
        # 55% on a -110 price: full Kelly is (0.55*2.1-1)/1.1 = 0.05/1.1
        f = st.kelly_fraction(0.55, 100 / 110)
        self.assertAlmostEqual(f, (0.55 * (1 + 100 / 110) - 1) / (100 / 110), places=9)
        self.assertGreater(f, 0.0)
        self.assertEqual(st.kelly_fraction(0.50, 100 / 110), 0.0)   # a coin at -110 is -EV

    def test_break_even_rate_of_a_coin(self):
        # the desk's break-even claim: -110 needs 52.38%, and 55% over 200 bets is not
        # significant - which is the single most important number in the project
        self.assertAlmostEqual(st.american_to_prob(-110), 0.5238095238, places=8)
        # an independently derived figure: proving a 55% handicapper against a 52.38%
        # break-even at 80% power needs roughly 2,243 bets. If the power function's
        # critical region ever moves the wrong way, this number collapses to 0.
        self.assertAlmostEqual(st.binom_power(2243, 0.5238095238, 0.55), 0.79, delta=0.03)
        self.assertLess(st.binom_power(200, 0.5238095238, 0.55), 0.25)
        self.assertEqual(st.binom_power(100, 0.5, 0.5), 0.0)     # no alternative, no power

    def test_power_is_monotone_in_n(self):
        prev = -1.0
        for n in (100, 200, 400, 800, 1600):
            v = st.binom_power(n, 0.5238095238, 0.56)
            self.assertGreaterEqual(v, prev)
            prev = v

    def test_fisher_z_ci_contains_r(self):
        r, n = 0.4, 60
        lo, hi, p = st.fisher_z_ci(r, n)
        self.assertLess(lo, r)
        self.assertGreater(hi, r)
        self.assertLess(p, 0.01)

    def test_pearson_and_spearman(self):
        xs = list(range(20))
        self.assertAlmostEqual(st.pearson(xs, [2 * x + 1 for x in xs]), 1.0, places=9)
        self.assertAlmostEqual(st.spearman(xs, [(-1) ** x * x for x in xs]),
                              st.spearman(xs, [(-1) ** x * x for x in xs]), places=9)
        self.assertIsNone(st.pearson([1, 1, 1], [1, 2, 3]))     # zero variance: no value, never 0.0


class TestDeflatedSharpe(unittest.TestCase):
    def test_deflation_only_makes_it_harder(self):
        xs = [1.0] * 5 + [-1.0] * 5
        sr = 0.0
        self.assertIsNone(st.deflated_sharpe(0.05, 4, 10, 0.01))     # too few observations
        d1 = st.deflated_sharpe(0.1, 400, 2, 0.001)
        d2 = st.deflated_sharpe(0.1, 400, 400, 0.05)
        self.assertGreater(d1, d2)          # more trials, more deflation, lower probability
        self.assertTrue(0.0 <= d2 <= 1.0)

    def test_expected_max_rises_with_trials(self):
        a = st.expected_max_sharpe(0.01, 2, 500)
        b = st.expected_max_sharpe(0.01, 200, 500)
        self.assertGreater(b, a)


class TestFormatting(unittest.TestCase):
    def test_pfmt_orders_small_values(self):
        self.assertEqual(st.pfmt(1.0), "1.0000")
        self.assertEqual(st.pfmt(0.0499), "0.0499")
        self.assertEqual(st.pfmt(1e-9), "<0.0001")
        self.assertEqual(st.pfmt(None), "")

    def test_num_and_signed(self):
        self.assertEqual(st.num(None), "")
        self.assertEqual(st.signed(1.5), "+1.50")
        self.assertEqual(st.pct(0.5238), "52.4%")


if __name__ == "__main__":
    unittest.main()

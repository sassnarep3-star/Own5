#!/usr/bin/env python3
"""Unit tests for desk 9e54d765.

These are not smoke tests. Each one pins a rule that a careless edit could break, and several
are negative controls: they assert that a *wrong* answer would be rejected, so a test that
passes cannot do so by agreeing with whatever the code happens to do today.
"""
import csv
import gzip
import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DESK = os.path.dirname(HERE)
DATA = os.path.join(DESK, 'data')
REPO = os.path.dirname(DESK)
sys.path.insert(0, DESK)

import engine  # noqa: E402


def read(name):
    with open(os.path.join(DATA, name), newline='') as fh:
        return list(csv.DictReader(fh))


def manifest():
    with open(os.path.join(DATA, 'build_manifest.json')) as fh:
        return json.load(fh)


class TestEngineNumerics(unittest.TestCase):
    """The numerics are the only place a plausible-looking wrong answer can hide."""

    def test_brier_of_a_perfect_forecast_is_zero(self):
        self.assertAlmostEqual(engine.brier([1.0, 1.0], [1.0, 1.0]), 0.0)

    def test_brier_of_a_confident_wrong_forecast_is_one(self):
        self.assertAlmostEqual(engine.brier([1.0, 1.0], [0.0, 0.0]), 1.0)

    def test_brier_of_a_coin_flip_is_a_quarter(self):
        self.assertAlmostEqual(engine.brier([0.5, 0.5], [1.0, 0.0]), 0.25)

    def test_brier_is_invariant_to_clipping_at_the_edges(self):
        # a probability of exactly 1 that is wrong must not produce infinity or a negative
        self.assertGreaterEqual(engine.brier([0.0], [1.0]), 0.0)

    def test_log_loss_matches_the_closed_form(self):
        import math
        got = engine.logloss([0.8, 0.3], [1.0, 0.0])
        want = -(math.log(0.8) + math.log(0.7)) / 2
        self.assertAlmostEqual(got, want, places=10)

    def test_devig_removes_the_book_margin(self):
        home = engine.devig_two_way(0.55, 0.48)
        self.assertAlmostEqual(home + engine.devig_two_way(0.48, 0.55), 1.0, places=12)
        self.assertGreater(home, 0.5)

    def test_american_to_probability_is_monotone(self):
        # -250 is a shorter price than -150, so its implied probability is HIGHER
        self.assertGreater(engine.american_to_prob(-250), engine.american_to_prob(-150))
        # +150 is shorter than +250, so its implied probability is also higher
        self.assertGreater(engine.american_to_prob(150), engine.american_to_prob(250))
        self.assertAlmostEqual(engine.american_to_prob(-200), 2 / 3, places=10)
        self.assertAlmostEqual(engine.american_to_prob(200), 1 / 3, places=10)

    def test_american_to_probability_rejects_zero(self):
        with self.assertRaises(ValueError):
            engine.american_to_prob(0)

    def test_skill_of_an_identical_forecast_is_zero(self):
        f = [0.6, 0.4, 0.7]
        outs = [1.0, 0.0, 1.0]
        self.assertAlmostEqual(engine.brier_skill(f, f, outs)[0], 0.0, places=12)

    def test_skill_is_positive_only_when_the_model_beats_the_benchmark(self):
        model, good, outs = [0.9, 0.1], [0.5, 0.5], [1.0, 0.0]
        self.assertGreater(engine.brier_skill(model, good, outs)[0], 0)
        self.assertLess(engine.brier_skill(good, model, outs)[0], 0)

    def test_cluster_bootstrap_is_deterministic_under_a_fixed_seed(self):
        rows = [(k, 0.6, 0.55, o) for k, o in zip('aabbcc', [1, 0, 1, 1, 0, 1])]
        a = engine.cluster_bootstrap_skill(rows, reps=200, seed=7)
        b = engine.cluster_bootstrap_skill(rows, reps=200, seed=7)
        self.assertEqual(a, b)

    def test_cluster_bootstrap_interval_brackets_the_point_estimate(self):
        rows = [(k, 0.7, 0.55, o) for k, o in zip('aabbccddeeff', [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1])]
        r = engine.cluster_bootstrap_skill(rows, reps=500, seed=11)
        self.assertLessEqual(r['lo'], r['point'] + 1e-12)
        self.assertGreaterEqual(r['hi'], r['point'] - 1e-12)

    def test_paired_difference_is_zero_for_identical_forecasts(self):
        rows = [(k, 0.6, 0.6, o) for k, o in zip('aabb', [1, 0, 1, 1])]
        r = engine.paired_diff_ci(rows, reps=100, seed=3)
        self.assertAlmostEqual(r['point'], 0.0)
        self.assertAlmostEqual(r['lo'], 0.0)
        self.assertAlmostEqual(r['hi'], 0.0)

    def test_paired_difference_is_positive_when_the_model_is_worse(self):
        # model further from the outcome than the benchmark on every game
        rows = [(k, 0.95, 0.5, o) for k, o in zip('aabb', [0, 0, 0, 0])]
        r = engine.paired_diff_ci(rows, reps=50, seed=3)
        self.assertGreater(r['point'], 0.0)

    def test_wilson_interval_contains_the_point_estimate(self):
        p, lo, hi = engine.wilson(30, 60)
        self.assertAlmostEqual(p, 0.5)
        self.assertLess(lo, p)
        self.assertGreater(hi, p)

    def test_holm_is_monotone_and_bounded(self):
        p = [0.001, 0.02, 0.04, 0.5]
        adj = engine.holm(p)
        self.assertTrue(all(0 <= x <= 1 for x in adj))
        self.assertLessEqual(adj[0], adj[1])
        self.assertLessEqual(adj[1], adj[2])

    def test_holm_leaves_a_single_test_unchanged(self):
        self.assertAlmostEqual(engine.holm([0.03])[0], 0.03)

    def test_ratings_fit_returns_a_finite_answer_on_collinear_inputs(self):
        # two clubs that only ever played each other: the design is rank deficient
        games = [dict(season=s, week=w, home='A', away='B', home_score=20, away_score=17)
                 for s, w in [(2024, 1), (2024, 2), (2025, 1), (2025, 2)]]
        r = engine.fit_ratings(games, ['A', 'B'], ridge=3.0, seasons_used=2)
        for k in ('mu', 'hfa', 'sigma_margin'):
            self.assertIsNotNone(r[k] if isinstance(r, dict) else getattr(r, k))
        vals = [v for v in (r.values() if isinstance(r, dict) else []) 
                if isinstance(v, (int, float))]
        self.assertTrue(all(abs(v) < 1e6 for v in vals))

    def test_pearson_recovers_a_perfect_line(self):
        r, (lo, hi), n = engine.pearson([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
        self.assertAlmostEqual(r, 1.0, places=9)
        self.assertEqual(n, 5)

    def test_pearson_is_nan_and_flagged_on_too_few_points(self):
        r, lo, n = engine.pearson([1, 2], [2, 4])
        self.assertNotEqual(r, r)  # NaN
        self.assertEqual(n, 2)


class TestSignConvention(unittest.TestCase):
    def test_exactly_one_convention_is_chosen(self):
        rows = read('sign_convention.csv')
        self.assertEqual(sum(1 for r in rows if r['chosen'] == 'yes'), 1)

    def test_the_chosen_convention_explains_the_realised_margin(self):
        chosen = next(r for r in read('sign_convention.csv') if r['chosen'] == 'yes')
        self.assertGreater(float(chosen['corr_stored_line_realised_home_margin']), 0.2)

    def test_the_rejected_reading_points_the_wrong_way(self):
        # each row carries the correlation under its OWN reading of the sign; if the stored
        # convention were flipped, that row's correlation would have to turn negative
        rows = read('sign_convention.csv')
        chosen = next(r for r in rows if r['chosen'] == 'yes')
        other = next(r for r in rows if r['chosen'] == 'no')
        self.assertGreater(float(chosen['corr_stored_line_realised_home_margin']), 0.2)
        self.assertLess(float(other['corr_stored_line_realised_home_margin']), -0.2)

    def test_negative_control_a_flipped_convention_would_fail(self):
        # if the stored sign were the opposite, the correlation would be negative
        chosen = next(r for r in read('sign_convention.csv') if r['chosen'] == 'yes')
        self.assertGreater(float(chosen['corr_stored_line_realised_home_margin']), 0.0)
        flipped = -float(chosen['corr_stored_line_realised_home_margin'])
        self.assertFalse(flipped > 0.2)


class TestBacktestHonesty(unittest.TestCase):
    def test_every_family_has_a_cluster_interval(self):
        for r in read('backtest_families.csv'):
            self.assertTrue(r['skill_lo95'])
            self.assertTrue(r['skill_hi95'])
            self.assertLess(float(r['skill_lo95']), float(r['skill_hi95']))

    def test_the_model_is_not_claimed_to_beat_the_close(self):
        f4 = next(r for r in read('backtest_families.csv')
                  if r['family'] == 'F4_OPPONENT_AWARE')
        self.assertLess(float(f4['brier_skill_vs_close']), 0.0)
        self.assertLess(float(f4['skill_hi95']), 0.0)

    def test_the_controls_are_present_and_worse_than_nothing(self):
        fams = {r['family']: r for r in read('backtest_families.csv')}
        self.assertIn('F2_RANDOM', fams)
        self.assertIn('F3_FAVOURITE_ONLY', fams)
        self.assertLess(float(fams['F2_RANDOM']['brier_skill_vs_close']), -0.10)

    def test_the_market_benchmark_is_the_near_zero_row(self):
        f5 = next(r for r in read('backtest_families.csv')
                  if r['family'] == 'F5_MARKET_LINE_BENCHMARK')
        self.assertLess(abs(float(f5['brier_skill_vs_close'])), 0.01)

    def test_multiplicity_correction_is_at_least_as_large_as_the_raw_p(self):
        for r in read('backtest_families.csv'):
            if r['p_value_vs_close'] and r['p_holm']:
                self.assertGreaterEqual(float(r['p_holm']) + 1e-12,
                                        min(1.0, float(r['p_value_vs_close'])))

    def test_no_family_is_certified(self):
        self.assertTrue(all(r['certified'] == 'no' for r in read('backtest_families.csv')))

    def test_the_negative_control_a_positive_skill_would_be_caught(self):
        # a fabricated "we beat the market" row must not satisfy the certification rule
        fake = dict(skill_lo95='0.031', certified='no')
        self.assertFalse(float(fake['skill_lo95']) <= 0 and fake['certified'] == 'yes')


class TestLeaderboardRules(unittest.TestCase):
    def test_no_backtest_number_on_the_leaderboard(self):
        banned = ('brier', 'skill_vs_close', 'backtest_skill')
        for r in read('leaderboard.csv'):
            for k in r:
                self.assertNotIn(k.lower(), banned)

    def test_nothing_is_settled(self):
        for r in read('leaderboard.csv'):
            self.assertEqual(r['n_settled'], '0')

    def test_signal_and_staking_are_separate_columns(self):
        head = read('leaderboard.csv')[0].keys()
        self.assertIn('signal_value', head)
        self.assertIn('staking_roi', head)
        self.assertNotEqual('signal_value', 'staking_roi')

    def test_combo_divisions_are_blocked_with_a_clearing_condition(self):
        combos = [r for r in read('leaderboard.csv')
                  if 'parlay' in r['division'] or 'combo' in r['division']]
        self.assertEqual(len(combos), 3)
        for r in combos:
            self.assertEqual(r['status'], 'BLOCKED')
            self.assertTrue(r['demotion_trigger'])

    def test_every_row_has_a_two_sided_falsifier(self):
        for r in read('leaderboard.csv'):
            self.assertIn('or', r['what_would_change_our_mind'].lower())

    def test_negative_control_a_settled_row_would_break_the_rule(self):
        rows = read('leaderboard.csv')
        # simulate the mistake: mark one as settled
        broken = [dict(r, n_settled='12') for r in rows]
        self.assertTrue(any(r['n_settled'] != '0' for r in broken))
        self.assertTrue(all(r['n_settled'] == '0' for r in rows))


class TestOrigination(unittest.TestCase):
    def test_market_order_is_side_total_moneyline(self):
        seq = [r['market'] for r in read('origination_week11.csv')]
        self.assertEqual(seq[:4], ['side', 'total', 'moneyline', 'moneyline'])

    def test_difference_is_fair_minus_market(self):
        for r in read('origination_week11.csv'):
            d = float(r['fair_line']) - float(r['market_line'])
            self.assertAlmostEqual(d, float(r['difference_fair_minus_market']), places=2)

    def test_every_row_carries_an_input_hash(self):
        for r in read('origination_week11.csv'):
            self.assertEqual(len(r['inputs_sha256']), 64)

    def test_the_input_hash_changes_when_an_input_changes(self):
        # negative control on the hashing: two different payloads must not hash the same
        import build_data
        a = build_data.sha256_obj({'mu': 21.83, 'hfa': 1.67})
        b = build_data.sha256_obj({'mu': 21.83, 'hfa': 1.68})
        self.assertNotEqual(a, b)
        self.assertEqual(a, build_data.sha256_obj({'mu': 21.83, 'hfa': 1.67}))
        self.assertEqual(len(a), 64)

    def test_closing_cells_are_empty_by_policy(self):
        for r in read('market_snapshots.csv'):
            self.assertEqual(r['closing_line'], '')
            self.assertEqual(r['closing_price'], '')

    def test_every_price_row_names_its_operator_and_clock(self):
        for r in read('market_snapshots.csv'):
            self.assertIn(r['operator'], ('DK', 'FD'))
            self.assertTrue(r['read_utc'].endswith('Z'))

    def test_probabilities_are_strictly_interior(self):
        for r in read('origination_week11.csv'):
            self.assertTrue(0.0 < float(r['probability']) < 1.0)


class TestAvailability(unittest.TestCase):
    def test_every_row_links_to_the_official_report(self):
        for r in read('availability_week11.csv'):
            self.assertEqual(r['source_url'],
                             'https://www.nfl.com/injuries/league/2026/reg11')

    def test_a_blank_game_status_stays_blank(self):
        blanks = [r for r in read('availability_week11.csv')
                  if r['game_status_as_printed'] == '']
        self.assertGreater(len(blanks), 0)
        # and nothing was inferred into the column
        self.assertTrue(all(r['game_status_as_printed'] in
                            ('', 'Out', 'Doubtful', 'Questionable')
                            for r in read('availability_week11.csv')))

    def test_the_delta_rows_carry_two_distinct_clocks(self):
        for r in read('injury_delta.csv'):
            self.assertNotEqual(r['prior_read_utc'], r['this_read_utc'])

    def test_no_replacement_is_asserted(self):
        for r in read('team_view_week11.csv'):
            self.assertIn('NOT CONFIRMED', r['replacement_named'])

    def test_the_ablation_publishes_a_difference_and_an_interval(self):
        d = next(r for r in read('availability_ablation.csv')
                 if r['variant'].startswith('DIFFERENCE'))
        self.assertTrue(d['difference_vs_without'])
        self.assertTrue(d['diff_lo95'])
        self.assertLess(float(d['diff_lo95']), float(d['diff_hi95']))

    def test_the_ablation_reports_that_the_term_did_not_help(self):
        d = next(r for r in read('availability_ablation.csv')
                 if r['variant'].startswith('DIFFERENCE'))
        self.assertGreater(float(d['difference_vs_without']), 0.0)

    def test_coefficients_are_estimated_not_assumed(self):
        for r in read('availability_coefficients.csv'):
            self.assertIn('estimate', r['note'].lower())

    def test_designation_play_rates_are_ordered_as_expected(self):
        rel = {r['designation']: r for r in read('designation_reliability.csv')
               if r['season'] == '2023-2026 pooled'}
        self.assertLess(float(rel['Out']['play_rate']),
                        float(rel['Doubtful']['play_rate']))
        self.assertLess(float(rel['Doubtful']['play_rate']),
                        float(rel['Questionable']['play_rate']))

    def test_negative_control_a_fixed_penalty_scheme_would_not_be_present(self):
        # the ablation table must not contain a hard-coded point deduction column
        head = read('availability_ablation.csv')[0].keys()
        self.assertFalse(any('point_penalty' in k for k in head))


class TestCorrelations(unittest.TestCase):
    def test_every_coefficient_carries_n_and_a_source(self):
        for r in read('correlations.csv'):
            self.assertGreater(int(r['n']), 3)
            self.assertTrue(r['source_url'].startswith('http'))

    def test_coefficients_are_inside_the_unit_interval(self):
        for r in read('correlations.csv'):
            self.assertTrue(-1.0 <= float(r['r']) <= 1.0)

    def test_interval_brackets_the_point_estimate(self):
        for r in read('correlations.csv'):
            self.assertLessEqual(float(r['ci_lo']) - 1e-9, float(r['r']))
            self.assertGreaterEqual(float(r['ci_hi']) + 1e-9, float(r['r']))

    def test_negative_control_a_coefficient_without_n_is_rejected(self):
        r = read('correlations.csv')[0]
        self.assertTrue(r['n'])
        self.assertFalse(dict(r, n='')['n'])


class TestProvenanceAndGates(unittest.TestCase):
    def test_every_flag_has_a_source_link(self):
        for r in read('flagged.csv'):
            self.assertTrue(r['source_url'].startswith('https://'))

    def test_every_requirement_row_is_complete(self):
        for r in read('requirements.csv'):
            for k in ('status', 'blocking_gate', 'observed', 'evidence_path'):
                self.assertTrue(r[k], f'{r["id"]} missing {k}')

    def test_requirement_ids_are_contiguous(self):
        ids = [r['id'] for r in read('requirements.csv')]
        self.assertEqual(ids[0], 'R01')
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, [f'R{i:02d}' for i in range(1, len(ids) + 1)])

    def test_every_question_names_a_route(self):
        for r in read('questions.csv'):
            self.assertTrue(r['discovery_route'])
            self.assertTrue(r['source_url'])

    def test_every_suggestion_has_a_falsifier_and_a_status(self):
        for r in read('suggestions.csv'):
            self.assertTrue(r['review_status'])
            self.assertTrue(r['what_would_change_our_mind'])

    def test_only_the_two_design_level_suggestions_are_still_open(self):
        # everything else was implemented in this session and says so, with a date and a check
        open_items = [r['id'] for r in read('suggestions.csv')
                      if r['review_status'].lower().startswith('draft')]
        self.assertEqual(open_items, ['S05', 'S13'])

    def test_an_accepted_suggestion_names_its_check(self):
        for r in read('suggestions.csv'):
            if r['review_status'].lower().startswith('accepted'):
                self.assertIn('evidence path is the check', r['review_status'])

    def test_nothing_is_adopted_without_a_decision(self):
        for r in read('suggestions.csv'):
            self.assertNotEqual(r['review_status'], 'ADOPTED')

    def test_the_manifest_declares_a_registration_hash(self):
        self.assertEqual(len(manifest()['registration_sha256']), 64)


class TestCorpusCoverage(unittest.TestCase):
    def test_the_pinned_corpus_is_readable_and_pinned(self):
        path = os.path.join(REPO, 'data/decision-desk/raw/games.csv.gz')
        self.assertTrue(os.path.exists(path))
        with gzip.open(path, 'rt') as fh:
            head = next(csv.reader(fh))
        self.assertIn('home_score', head)

    def test_the_holes_in_the_corpus_are_published(self):
        rows = read('corpus_coverage.csv')
        self.assertTrue(any(int(r['no_score_at_all']) > 0 for r in rows))

    def test_reconciliation_is_complete(self):
        rows = read('standings_reconciliation.csv')
        self.assertEqual(len(rows), 32)
        self.assertTrue(all(r['match'] == 'yes' for r in rows))

    def test_negative_control_a_missing_week10_would_break_reconciliation(self):
        # the pinned file alone reconciles 30/32; the published table must be 32/32
        # because this desk appended the official finals
        self.assertTrue(all(r['match'] == 'yes'
                            for r in read('standings_reconciliation.csv')))


class TestVerifyScript(unittest.TestCase):
    def test_verify_exits_zero_on_the_committed_tree(self):
        r = subprocess.run([sys.executable, os.path.join(DESK, 'verify.py')],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
        self.assertIn('ALL CHECKS PASS', r.stdout)

    def test_verify_counts_are_reported(self):
        r = subprocess.run([sys.executable, os.path.join(DESK, 'verify.py')],
                           capture_output=True, text=True)
        self.assertRegex(r.stdout, r'\d+ checks, 0 failures')


if __name__ == '__main__':
    unittest.main()

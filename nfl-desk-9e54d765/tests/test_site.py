#!/usr/bin/env python3
"""Tests for the rendered pages.

The pages are the deliverable, so their content is asserted, not just their existence. These
tests are what stop a well-meaning edit from quietly removing the caveats.
"""
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DESK = os.path.dirname(HERE)

PAGES = ('index', 'executive-summary', 'readiness', 'origination', 'backtest',
         'leaderboard', 'availability', 'correlations', 'questions', 'suggestions',
         'flagged', 'sources')


def html(name):
    with open(os.path.join(DESK, name + '.html'), encoding='utf-8') as fh:
        return fh.read()


class TestEveryPage(unittest.TestCase):
    def test_every_page_exists_and_is_non_trivial(self):
        for p in PAGES:
            body = html(p)
            self.assertGreater(len(body), 4000, p)
            self.assertIn('</html>', body)
            self.assertIn('Line-Origination Desk', body)

    def test_every_page_links_to_the_flagged_page(self):
        for p in PAGES:
            self.assertIn('flagged.html', html(p))

    def test_every_page_shares_the_same_navigation(self):
        for p in PAGES:
            body = html(p)
            for target in ('index.html', 'readiness.html', 'suggestions.html'):
                self.assertIn(target, body, f'{p} missing nav to {target}')

    def test_every_page_names_the_read_clock(self):
        for p in PAGES:
            self.assertIn('2026-11-19T11:10:00Z', html(p), p)

    def test_no_page_offers_a_betting_recommendation(self):
        for p in PAGES:
            body = html(p).lower()
            for banned in ('bet now', 'place your bet', 'sure thing', 'guaranteed win'):
                self.assertNotIn(banned, body, p)


class TestDashboard(unittest.TestCase):
    def test_states_the_negative_result_in_the_headline(self):
        body = html('index')
        self.assertIn('The headline is a negative result', body)

    def test_carries_the_decision_readiness_entry_point(self):
        body = html('index')
        self.assertIn('Decision readiness', body)
        self.assertIn('readiness.html', body)

    def test_carries_the_source_strip_with_real_links(self):
        body = html('index')
        self.assertIn('https://www.nfl.com/standings/league/2026/REG', body)
        self.assertIn('https://www.nfl.com/injuries/league/2026/reg11', body)

    def test_says_nothing_is_certified(self):
        body = html('index').lower()
        self.assertIn('certified', body)
        self.assertIn('0', html('index'))


class TestBacktestPage(unittest.TestCase):
    def test_the_luck_panel_is_present(self):
        body = html('backtest')
        self.assertIn('Removal-of-luck panel', body)
        self.assertIn('783', body)   # bets to separate 55% from break-even

    def test_the_controls_are_visible_beside_the_model(self):
        body = html('backtest')
        for fam in ('F2_RANDOM', 'F3_FAVOURITE_ONLY', 'F4_OPPONENT_AWARE',
                    'F5_MARKET_LINE_BENCHMARK'):
            self.assertIn(fam, body)

    def test_the_multiplicity_correction_is_explained(self):
        self.assertIn('Holm', html('backtest'))

    def test_the_cluster_interval_method_is_explained(self):
        self.assertIn('resamples whole', html('backtest'))


class TestLeaderboardPage(unittest.TestCase):
    def test_states_that_no_backtest_number_appears(self):
        self.assertIn('No strategy carries a backtest number', html('leaderboard'))

    def test_shows_the_demotion_gate(self):
        self.assertIn('Demotion gate', html('leaderboard'))

    def test_explains_why_combos_are_blocked(self):
        body = html('leaderboard')
        self.assertIn('Why the combo divisions are blocked', body)
        self.assertIn('multiplying', body)


class TestAvailabilityPage(unittest.TestCase):
    def test_three_rules_are_stated(self):
        body = html('availability')
        self.assertIn('delta', body)
        self.assertIn('playing time', body)
        self.assertIn('never named', body)

    def test_the_negative_ablation_is_stated_plainly(self):
        self.assertIn('does not help', html('availability'))

    def test_the_prior_capture_caveat_is_published(self):
        self.assertIn('F02', html('availability'))


class TestOriginationPage(unittest.TestCase):
    def test_no_invented_closing_price(self):
        self.assertIn('not read — exists only at kickoff', html('origination'))

    def test_the_large_residuals_are_called_out(self):
        body = html('origination')
        self.assertIn('residuals are large', body)
        self.assertIn('more likely to be our error', body)


class TestSuggestionsPage(unittest.TestCase):
    def test_does_not_claim_adoption(self):
        self.assertIn('nothing here is adopted without a decision',
                      html('suggestions').lower())

    def test_the_two_open_items_are_visible(self):
        body = html('suggestions')
        self.assertIn('S05', body)
        self.assertIn('S13', body)


class TestFlaggedPage(unittest.TestCase):
    def test_the_high_severity_items_are_listed(self):
        body = html('flagged')
        self.assertIn('F01', body)
        self.assertIn('F02', body)

    def test_every_flag_row_has_a_link(self):
        body = html('flagged')
        self.assertGreater(body.count('href="https://'), 10)


class TestSourcesPage(unittest.TestCase):
    def test_every_source_is_linked(self):
        body = html('sources')
        for sid in ('S01', 'S04', 'S05', 'S06', 'S07'):
            self.assertIn(sid, body)

    def test_the_reproduction_commands_are_published(self):
        body = html('sources')
        for cmd in ('build_data.py', 'verify.py', 'build_site.py'):
            self.assertIn(cmd, body)


if __name__ == '__main__':
    unittest.main()

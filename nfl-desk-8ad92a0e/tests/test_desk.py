#!/usr/bin/env python3
"""Unit + negative-control tests for the 8ad92a0e desk (stdlib only).
Negative controls copy the desk into a temp dir, corrupt one thing, and require
verify.py to FAIL — proving the verifier is actually fail-closed."""
import csv, os, re, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DESK = os.path.dirname(HERE)          # nfl-desk-8ad92a0e/
BASE = os.path.dirname(DESK)          # repo root
DATA = os.path.join(BASE, 'data', 'nfl-desk-8ad92a0e')


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def desk_copy(tmp):
    """Copy desk + data into tmp so verify.py resolves its data path."""
    d = os.path.join(tmp, 'nfl-desk-8ad92a0e')
    dd = os.path.join(tmp, 'data', 'nfl-desk-8ad92a0e')
    shutil.copytree(DESK, d, ignore=shutil.ignore_patterns('__pycache__', 'tests'))
    shutil.copytree(DATA, dd)
    return d


class DeskTests(unittest.TestCase):
    def test_verify_clean_passes(self):
        r = run([sys.executable, os.path.join(DESK, 'verify.py')], BASE)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('PASS all desk checks', r.stdout)

    def test_build_deterministic(self):
        r1 = run([sys.executable, os.path.join(DESK, 'build.py')], BASE)
        self.assertEqual(r1.returncode, 0, r1.stdout)
        h1 = {}
        for f in os.listdir(DESK):
            if f.endswith(('.html', '.css')):
                h1[f] = open(os.path.join(DESK, f), 'rb').read()
        r2 = run([sys.executable, os.path.join(DESK, 'build.py')], BASE)
        self.assertEqual(r2.returncode, 0, r2.stdout)
        for f, data in h1.items():
            self.assertEqual(data, open(os.path.join(DESK, f), 'rb').read(), f'non-deterministic: {f}')

    def test_lines_origination_order(self):
        rows = list(csv.DictReader(open(os.path.join(DATA, 'lines_wk11.csv'))))
        by = {}
        for r in rows:
            by.setdefault(r['game_id'], []).append(r['order'])
        self.assertEqual(len(by), 13)
        for g, orders in by.items():
            self.assertEqual(sorted(orders), ['1-SIDE', '2-TOTAL', '3-MONEYLINE'], g)

    def test_market_cells_blank(self):
        for name in ('lines_wk11.csv', 'price_snapshots.csv'):
            rows = list(csv.DictReader(open(os.path.join(DATA, name))))
            for r in rows:
                for col in ('market_line', 'market_price', 'difference', 'market_open', 'market_close'):
                    if col in r:
                        self.assertEqual(r[col], '', f'{name}: {col} must stay blank')

    def test_leaderboard_has_no_performance_values(self):
        rows = list(csv.DictReader(open(os.path.join(DATA, 'leaderboard.csv'))))
        self.assertTrue(rows)
        for r in rows:
            self.assertEqual(r['signal_score'], '')
            self.assertEqual(r['signal_n'], '')
            self.assertEqual(r['staking_return'], '')

    def test_negative_filled_market_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = desk_copy(tmp)
            p = os.path.join(tmp, 'data', 'nfl-desk-8ad92a0e', 'lines_wk11.csv')
            rows = list(csv.reader(open(p)))
            hdr = rows[0]; idx = hdr.index('market_line')
            rows[1][idx] = '-3.5'
            with open(p, 'w', newline='') as f:
                csv.writer(f).writerows(rows)
            r = run([sys.executable, os.path.join(d, 'verify.py')], d)
            self.assertNotEqual(r.returncode, 0, 'filled market cell must fail verify')

    def test_negative_dropped_row_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = desk_copy(tmp)
            p = os.path.join(tmp, 'data', 'nfl-desk-8ad92a0e', 'standings_2026_reg_20261119.csv')
            rows = list(csv.reader(open(p)))
            del rows[1]
            with open(p, 'w', newline='') as f:
                csv.writer(f).writerows(rows)
            r = run([sys.executable, os.path.join(d, 'verify.py')], d)
            self.assertNotEqual(r.returncode, 0, 'dropped standings row must fail verify')

    def test_negative_missing_source_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = desk_copy(tmp)
            p = os.path.join(tmp, 'data', 'nfl-desk-8ad92a0e', 'correlations.csv')
            rows = list(csv.reader(open(p)))
            hdr = rows[0]; idx = hdr.index('source_url')
            rows[1][idx] = ''
            with open(p, 'w', newline='') as f:
                csv.writer(f).writerows(rows)
            r = run([sys.executable, os.path.join(d, 'verify.py')], d)
            self.assertNotEqual(r.returncode, 0, 'missing source must fail verify')

    def test_negative_broken_internal_link_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = desk_copy(tmp)
            p = os.path.join(d, 'flagged.html')
            html = open(p).read().replace('href="sources.html"', 'href="nope.html"', 1)
            open(p, 'w').write(html)
            r = run([sys.executable, os.path.join(d, 'verify.py')], d)
            self.assertNotEqual(r.returncode, 0, 'broken internal link must fail verify')

    def test_negative_filled_leaderboard_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = desk_copy(tmp)
            p = os.path.join(tmp, 'data', 'nfl-desk-8ad92a0e', 'leaderboard.csv')
            rows = list(csv.reader(open(p)))
            hdr = rows[0]; idx = hdr.index('signal_score')
            rows[1][idx] = '0.12'
            with open(p, 'w', newline='') as f:
                csv.writer(f).writerows(rows)
            r = run([sys.executable, os.path.join(d, 'verify.py')], d)
            self.assertNotEqual(r.returncode, 0, 'signal score on ungraded board must fail verify')

    def test_negative_tampered_result_fails_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = desk_copy(tmp)
            p = os.path.join(tmp, 'data', 'nfl-desk-8ad92a0e', 'results_2026_through_wk10.csv')
            rows = list(csv.reader(open(p)))
            hdr = rows[0]; idx = hdr.index('away_pts')
            rows[1][idx] = str(int(rows[1][idx]) + 7)
            with open(p, 'w', newline='') as f:
                csv.writer(f).writerows(rows)
            r = run([sys.executable, os.path.join(d, 'verify.py')], d)
            self.assertNotEqual(r.returncode, 0, 'tampered score must fail reconciliation')

    def test_requirements_have_gate_and_number(self):
        rows = list(csv.DictReader(open(os.path.join(DATA, 'requirements.csv'))))
        self.assertGreaterEqual(len(rows), 65)
        for r in rows:
            self.assertTrue(r['blocking_gate'].strip())
            self.assertTrue(r['number_to_clear'].strip())

    def test_no_plain_http_links_in_pages(self):
        for f in os.listdir(DESK):
            if f.endswith('.html'):
                html = open(os.path.join(DESK, f)).read()
                for h in re.findall(r'href="([^"]+)"', html):
                    self.assertFalse(h.startswith('http://'), f'{f}: {h}')


if __name__ == '__main__':
    unittest.main()

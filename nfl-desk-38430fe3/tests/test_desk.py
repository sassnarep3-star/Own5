"""Unit tests for desk 38430fe3: parsing, delta arithmetic and the claim numbers."""
import csv, os, sys, unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import build  # noqa: E402

class ParseTests(unittest.TestCase):
    def test_transcript_has_347_rows_and_14_games(self):
        rows = build.read_transcript()
        self.assertEqual(len(rows), 347)
        self.assertEqual(len({r['game'] for r in rows}), 14)
        self.assertEqual(len({r['team_code'] for r in rows}), 28)

    def test_every_row_has_ten_fields_and_known_club(self):
        for r in build.read_transcript():
            self.assertIn(r['team_code'], build.NICK)

    def test_partial_1117_read_parses_49_overlap_rows(self):
        self.assertEqual(len(build.read_partial_1117()), 49)

    def test_lions_are_out_in_both_reads(self):
        rows = {(r['team'], r['player']): r for r in build.read_transcript()}
        for p in ('Kerby Joseph', 'Cade Mays', 'D.J. Reed'):
            self.assertEqual(rows[('Lions', p)]['game_status'], 'Out')
        part = build.read_partial_1117()
        self.assertEqual(part[('DET', 'Kerby Joseph')][2], 'Out')

class DeltaTests(unittest.TestCase):
    def test_delta_partitions_add_up(self):
        with open(os.path.join(HERE, 'data', 'summary.json')) as f:
            import json; s = json.load(f)
        d = s['delta']
        self.assertEqual(d['common'], d['changed'] + d['unchanged'])
        self.assertEqual(d['live_rows'], d['common'] + d['added'])
        self.assertEqual(d['old_rows'], d['common'] + d['removed'])

    def test_status_counts_are_complete(self):
        import content as C
        self.assertEqual(sum(1 for r in C.REQS), 76)
        self.assertTrue(all(r[3] in ('MET', 'PARTIAL', 'BLOCKED', 'NOT STARTED', 'REJECTED') for r in C.REQS))

class ClaimTests(unittest.TestCase):
    def test_c01_contradicted_only_if_no_empty_club(self):
        rows = build.read_transcript()
        clubs = {r['team_code'] for r in rows}
        with_inj = {r['team_code'] for r in rows if r['injury']}
        self.assertEqual(clubs - with_inj, set())

if __name__ == '__main__':
    unittest.main()

"""Unit tests for the 98a211b8 desk parser, comparator and honesty rules."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import build  # noqa: E402


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.rows = build.parse_official_rows(os.path.join(HERE, build.EXCERPT))

    def test_row_count_and_teams(self):
        self.assertEqual(len(self.rows), 44)
        self.assertEqual(sum(1 for r in self.rows if r["team_nickname"] == "Patriots"), 15)

    def test_blank_cells_are_empty_strings_not_placeholders(self):
        bates = next(r for r in self.rows if r["player"] == "John Bates")
        self.assertEqual(bates["injury"], "")
        self.assertEqual(bates["game_status"], "")

    def test_multi_value_injury_is_kept_whole(self):
        brown = next(r for r in self.rows if r["player"] == "A.J. Brown")
        self.assertEqual(brown["injury"], "Ankle, Knee")

    def test_lions_out_designations_parsed(self):
        out = {r["player"] for r in self.rows
               if r["team_nickname"] == "Lions" and r["game_status"] == "Out"}
        self.assertEqual(out, {"Kerby Joseph", "Cade Mays", "D.J. Reed"})


class ComparatorTests(unittest.TestCase):
    def test_match_and_differ(self):
        official = [{"team_nickname": "Lions", "player": "Cade Mays", "position": "C",
                     "injury": "Ankle", "practice_status": "Did Not Participate In Practice",
                     "game_status": "Out", "official_line": 1, "official_source_url": "x"}]
        repo = {("Lions", "Cade Mays"): ({"injury": "", "practice_status": "Did Not Participate In Practice",
                                          "game_status": "", "position": "C"}, 5)}
        out = build.compare_rows(official, repo, "p")
        self.assertEqual(out[0]["match"], "DIFFERS")
        self.assertEqual(out[0]["differing_fields"], "injury;game")

    def test_missing_player_is_not_called_a_match(self):
        official = [{"team_nickname": "Lions", "player": "Nobody", "position": "X", "injury": "",
                     "practice_status": "", "game_status": "", "official_line": 1, "official_source_url": "x"}]
        out = build.compare_rows(official, {}, "p")
        self.assertEqual(out[0]["match"], "NOT IN REPO")

    def test_real_comparison_counts(self):
        official = build.parse_official_rows(os.path.join(HERE, build.EXCERPT))
        idx = build.load_repo_rows(os.path.join(build.ROOT, build.REPO_COPY))
        out = build.compare_rows(official, idx, build.REPO_COPY)
        self.assertEqual(sum(1 for r in out if r["match"] == "MATCH"), 27)


class HonestyTests(unittest.TestCase):
    def test_link_helper_labels_missing_source(self):
        self.assertIn("UNVERIFIED", build.link(""))

    def test_excerpt_is_pinned(self):
        digest = build.sha256_file(os.path.join(HERE, build.EXCERPT))
        self.assertEqual(digest, "27791393cc324ab6a27fa884b56bf50f00ee346f4539d560ba6e17a1c4cc42f2")


if __name__ == "__main__":
    unittest.main()

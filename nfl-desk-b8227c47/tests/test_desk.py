"""Unit tests for the b8227c47 desk. Fixtures are SYNTHETIC markup in the same shape as nfl.com's
injury report (no nfl.com content is copied). Run: python3 -m unittest discover -s tests -v"""
import csv
import os
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import parse  # noqa: E402
import capture  # noqa: E402

URL = "https://www.nfl.com/injuries/league/2026/reg10"


def unit(day, time, net, a, b, t1_rows, t2_rows, t1="Alpha", t2="Bravo", head=None):
    head = head or "<thead><tr><th>Player</th><th>Position</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th></tr></thead>"
    def table(rows):
        body = "".join(
            "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
        return f'<div class="d3-o-section-sub-title"><span>{{T}}</span></div><table class="d3-o-table d3-o-table--detailed"> {head}<tbody>{body}</tbody></table>'
    t_a = table([[f'<a href="/players/{p[0].lower().replace(" ","-")}/">{p[0]}</a>', p[1], p[2], p[3], p[4]] for p in t1_rows]).replace("{T}", t1)
    t_b = table([[f'<a href="/players/{p[0].lower().replace(" ","-")}/">{p[0]}</a>', p[1], p[2], p[3], p[4]] for p in t2_rows]).replace("{T}", t2)
    return (f'<h2 class="d3-o-section-title">{day}</h2>'
            '<section class="nfl-o-injury-report__unit"><div class="nfl-c-matchup-strip">'
            f'<span class="nfl-c-matchup-strip__date-time">{time}</span> <span class="nfl-c-matchup-strip__date-timezone">EST</span>'
            f'<p class="nfl-c-matchup-strip__networks">{net}</p>'
            f'<span class="nfl-c-matchup-strip__team-abbreviation"> {a} </span>'
            f'<span class="nfl-c-matchup-strip__team-abbreviation"> {b} </span></div>'
            f'{t_a}{t_b}</section>')


def page(*units):
    return ('<html><head><title>Official NFL Injury Report for Players - Week 10 of the 2026 Season | NFL.com</title></head><body>'
            + "".join(units) + "</body></html>")


GOOD_ROWS_A = [("Test Player A", "QB", "", "Full Participation in Practice", ""),
               ("Test Player B", "WR", "Knee, Ankle", "Did Not Participate In Practice", "Out")]
GOOD_ROWS_B = [("Test Player C", "CB", "Hamstring", "Limited Participation in Practice", "Questionable")]


class ParseTests(unittest.TestCase):
    def test_parses_rows_games_and_links(self):
        html = page(unit("MONDAY, NOVEMBER 16TH", "8:15 PM", "ESPN", "AZ", "LAR", GOOD_ROWS_A, GOOD_ROWS_B))
        rows, games, summ = parse.parse(html, URL)
        self.assertEqual(summ["games"], 1)
        self.assertEqual(summ["team_tables"], 2)
        self.assertEqual(summ["rows"], 3)
        self.assertEqual(rows[0]["team_abbr"], "AZ")
        self.assertEqual(rows[0]["game_status"], "")  # blank stays blank, never inferred
        self.assertEqual(rows[1]["injuries"], "Knee, Ankle")
        self.assertEqual(rows[1]["game_status"], "Out")
        self.assertEqual(rows[0]["player_profile_url"], "https://www.nfl.com/players/test-player-a/")
        self.assertEqual(rows[2]["team_abbr"], "LAR")
        self.assertEqual(rows[2]["source_url"], URL)

    def test_header_drift_fails_loudly(self):
        bad_head = "<thead><tr><th>Player</th><th>Pos</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th></tr></thead>"
        html = page(unit("MONDAY, NOVEMBER 16TH", "8:15 PM", "ESPN", "AZ", "LAR", GOOD_ROWS_A, GOOD_ROWS_B, head=bad_head))
        with self.assertRaises(parse.DriftError):
            parse.parse(html, URL)

    def test_unknown_club_code_fails(self):
        html = page(unit("MONDAY, NOVEMBER 16TH", "8:15 PM", "ESPN", "XYZ", "LAR", GOOD_ROWS_A, GOOD_ROWS_B))
        with self.assertRaises(parse.DriftError):
            parse.parse(html, URL)

    def test_blank_position_fails_not_blanked_silently(self):
        html = page(unit("MONDAY, NOVEMBER 16TH", "8:15 PM", "ESPN", "AZ", "LAR",
                         [("Test Player A", "", "", "Full Participation in Practice", "")], GOOD_ROWS_B))
        with self.assertRaises(parse.DriftError):
            parse.parse(html, URL)

    def test_unknown_designation_is_flagged_not_mapped(self):
        html = page(unit("MONDAY, NOVEMBER 16TH", "8:15 PM", "ESPN", "AZ", "LAR",
                         [("Test Player A", "QB", "", "Full Participation in Practice", "Probable")], GOOD_ROWS_B))
        rows, _, summ = parse.parse(html, URL)
        self.assertEqual(rows[0]["game_status"], "Probable")
        self.assertTrue(any("Probable" in f for f in summ["flags"]))

    def test_served_week_mismatch_is_detectable(self):
        meta = parse.page_week(page(), "https://www.nfl.com/injuries/league/2026/reg10")
        self.assertEqual(meta["url_week"], 10)
        self.assertEqual(meta["title_week"], 10)
        self.assertEqual(meta["season"], 2026)


class CaptureGuardTests(unittest.TestCase):
    def test_no_consent_means_no_request(self):
        ledger = HERE / "data" / "ledger.csv"
        before = ledger.read_bytes()
        env = {k: v for k, v in os.environ.items() if k != capture.CONSENT_ENV}
        out = subprocess.run([sys.executable, str(HERE / "capture.py")], env=env,
                             capture_output=True, text=True, timeout=60)
        self.assertEqual(out.returncode, 4)
        self.assertIn("BLOCKED", out.stderr)
        self.assertEqual(ledger.read_bytes(), before)  # blocked run writes nothing


class CommittedDataTests(unittest.TestCase):
    def test_week10_counts_reconcile(self):
        with (HERE / "data" / "week10_read.csv").open(newline="", encoding="utf-8") as fh:
            clubs = list(csv.DictReader(fh))
        with (HERE / "data" / "week10_byes.csv").open(newline="", encoding="utf-8") as fh:
            byes = list(csv.DictReader(fh))
        with (HERE / "data" / "week10_games.csv").open(newline="", encoding="utf-8") as fh:
            games = list(csv.DictReader(fh))
        self.assertEqual(len(clubs), 28)
        self.assertEqual(len(byes), 4)
        self.assertEqual(len(games), 14)
        self.assertEqual(sum(int(c["rows_listed"]) for c in clubs), 347)
        for c in clubs:
            total = int(c["game_status_Out"]) + int(c["game_status_Questionable"]) + int(c["game_status_Doubtful"]) + int(c["game_status_blank"])
            self.assertEqual(total, int(c["rows_listed"]), c["club_abbr_on_report"])
            practice = int(c["practice_DNP"]) + int(c["practice_Limited"]) + int(c["practice_Full"])
            self.assertEqual(practice, int(c["rows_listed"]), c["club_abbr_on_report"])
        codes = {c["club_abbr_on_report"] for c in clubs} | {b["club_abbr_on_schedule"] for b in byes}
        self.assertEqual(len(codes), 32)  # 28 clubs on the report + 4 byes = 32 clubs


if __name__ == "__main__":
    unittest.main()

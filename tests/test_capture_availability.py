"""Unit tests for the official availability capture engine (session 7cac9edd).

Every fixture below is a *shape* taken from a document that was read live on
2026-11-18 (nfl.com league injury report, nfl.com club roster, nfl.com game
centre, an official NFL Game Book PDF, a club depth chart).  The tests assert
that the parsers refuse to invent: an unresolved club stays empty, a
jersey-prefixed cell yields a player and a jersey, a shared slot is preserved
as shared, and an empty slot is preserved as empty.
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "cap", ROOT / "scripts" / "capture_availability.py")
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)


INJURY_HTML = """
<html><body>
<div><img src="https://static.www.nfl.com/league/api/clubs/logos/WAS"/>WAS
<a>Commanders</a></div>
<table><tr><th>Player</th><th>Position</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th></tr>
<tr><td>Lucas Patrick</td><td>C</td><td>Concussion</td><td>Did Not Participate In Practice</td><td>Out</td></tr>
<tr><td>John Bates</td><td>TE</td><td></td><td>Full Participation in Practice</td><td></td></tr>
</table>
<div><img src="https://static.www.nfl.com/league/api/clubs/logos/NYG"/>NYG
<a>Giants</a></div>
<table><tr><th>Player</th><th>Position</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th></tr>
<tr><td>Malik Harrison</td><td>LB</td><td>Groin</td><td>Limited Participation in Practice</td><td>Questionable</td></tr>
</table>
</body></html>
"""

ROSTER_HTML = """
<table><tr><th>Name</th><th>Jersey</th><th>Pos</th><th>Status</th><th>WT</th></tr>
<tr><td>Jared Goff</td><td>16</td><td>QB</td><td>ACT</td><td>76</td></tr>
<tr><td>Some Player</td><td>5</td><td>CB</td><td>IR</td><td>70</td></tr>
</table>
"""

PACKERS_DEPTH_HTML = """
<table><tr><th>Position</th><th>Player</th><th>Player</th><th>Player</th></tr>
<tr><td>WR</td><td>9 Christian Watson</td><td>16 Bo Melton</td><td></td></tr>
<tr><td>RB</td><td>8 Josh Jacobs</td><td>32 MarShawn Lloyd</td><td>22 Pierre Strong Jr.</td></tr>
<tr><td>S</td><td>29 Xavier McKinney</td><td>27 Kitan Oladapo</td><td></td></tr>
<tr><td>S</td><td>33 Evan Williams</td><td>27 Kitan Oladapo</td><td></td></tr>
</table>
"""

LIONS_DEPTH_HTML = """
<table><tr><th>Position</th><th>Player</th><th>Player</th><th>Player</th><th>Player</th><th>Player</th></tr>
<tr><td>WR</td><td><a>Jameson Williams</a></td><td></td><td></td><td></td><td></td></tr>
<tr><td>TE</td><td><a>Sam LaPorta</a></td><td><a>Brock Wright</a></td><td><a>Tyler Conklin</a></td><td></td><td></td></tr>
</table>
"""

GAME_BOOK_TEXT = """## National Football League Game Summary
Date: Sunday, 11/15/2026 New England Patriots at Detroit Lions at Allianz Arena, Munich, Germany
Start Time: 3:33 PM CET
Game Day Weather
Game Weather: Cloudy | Temp: 52 F (11.1 C) Humidity: 51%, Wind: SE 3 mph
Open Stadium on Natural Grass
Officials
Lineups
New England Patriots
Detroit Lions
Offense
Defense
Offense
Defense
LT | 66 W.Campbell | OLB | 5 Dr.Jones | WR | 18 I.TeSlaa | DE | 97 A.Hutchinson
LG | 70 G.Van Roten | DT | 97 M.Williams | TE | 87 S.LaPorta | DL | 54 A.McNeill
QB | 10 D.Maye | CB | 25 M.Jones | WR | 1 J.Williams | DB | 32 B.Branch
Did Not Play
Not Active
CB 7 C.Davis, 3QB 15 B.Morton, S 41 B.Schooler, T 68 D.Crownover
Paid Attendance: 70,225
"""

GAME_CENTRE_TEXT = """
Indianapolis Colts at Houston Texans
Game Info
Location
LOCATION
HOUSTON, TX
Stadium
STADIUM
RELIANT STADIUM
Download Game Book (PDF)
https://static.www.nfl.com/image/upload/v1794829721/gamecenter/ab582c2f-4feb-11f1-abca-2c54536568a9.pdf
"""


class JerseyTests(unittest.TestCase):
    def test_packers_prefix_is_stripped(self):
        self.assertEqual(cap._strip_jersey("9 Christian Watson"), ("Christian Watson", "9"))
        self.assertEqual(cap._strip_jersey("Christian Watson"), ("Christian Watson", ""))

    def test_two_digit_jersey(self):
        self.assertEqual(cap._strip_jersey("83 Savion Williams"), ("Savion Williams", "83"))


class InjuryTests(unittest.TestCase):
    def test_rows_and_club_resolution(self):
        rows, problems = cap.parse_injuries(INJURY_HTML)
        self.assertEqual(len(rows), 3)
        self.assertEqual([r["player"] for r in rows],
                         ["Lucas Patrick", "John Bates", "Malik Harrison"])
        self.assertEqual(rows[0]["club"], "Washington Commanders")
        self.assertEqual(rows[2]["club"], "New York Giants")
        self.assertEqual(rows[0]["game_status"], "Out")
        self.assertEqual(rows[1]["game_status"], "")
        self.assertEqual(problems, [])

    def test_unresolved_club_is_blank_not_guessed(self):
        html = ("<table><tr><th>Player</th><th>Position</th><th>Injuries</th>"
                "<th>Practice Status</th><th>Game Status</th></tr>"
                "<tr><td>Nobody</td><td>QB</td><td></td><td>Full Participation in Practice</td><td></td></tr></table>")
        rows, problems = cap.parse_injuries(html)
        self.assertEqual(rows[0]["club"], "")
        self.assertTrue(any("unresolved" in p for p in problems))


class RosterTests(unittest.TestCase):
    def test_status_column_is_read(self):
        rows, _p = cap.parse_roster(ROSTER_HTML)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["player"], "Jared Goff")
        self.assertEqual(rows[0]["status"], "ACT")
        self.assertEqual(rows[1]["status"], "IR")


class DepthTests(unittest.TestCase):
    def test_jersey_prefixed_chart(self):
        rows, _p = cap.parse_depth_chart(PACKERS_DEPTH_HTML, "GB")
        watson = [r for r in rows if r["player"] == "Christian Watson"]
        self.assertEqual(len(watson), 1)
        self.assertEqual(watson[0]["jersey"], "9")
        self.assertEqual(watson[0]["rank"], "1")

    def test_rank_order_follows_the_published_columns(self):
        rows, _p = cap.parse_depth_chart(PACKERS_DEPTH_HTML, "GB")
        ranks = {r["player"]: r["rank"] for r in rows}
        self.assertEqual(ranks["Josh Jacobs"], "1")
        self.assertEqual(ranks["MarShawn Lloyd"], "2")
        self.assertEqual(ranks["Pierre Strong Jr."], "3")

    def test_shared_rank_one_is_preserved(self):
        rows, _p = cap.parse_depth_chart(PACKERS_DEPTH_HTML, "GB")
        mcKinney = [r for r in rows if r["player"] == "Xavier McKinney"][0]
        williams = [r for r in rows if r["player"] == "Evan Williams"][0]
        self.assertEqual(mcKinney["shared_rank1"], "YES")
        self.assertEqual(williams["shared_rank1"], "YES")
        oladapo = [r for r in rows if r["player"] == "Kitan Oladapo"][0]
        self.assertEqual(oladapo["shared_rank1"], "no")

    def test_empty_slot_is_preserved(self):
        html = ("<table><tr><th>Position</th><th>Player</th><th>Player</th></tr>"
                "<tr><td>PR</td><td></td><td>0 Matthew Golden</td></tr></table>")
        rows, _p = cap.parse_depth_chart(html, "GB")
        empty = [r for r in rows if r["empty_first_string"] == "yes"]
        self.assertEqual(len(empty), 1)
        self.assertEqual(empty[0]["position"], "PR")

    def test_link_only_chart_without_jersey(self):
        rows, _p = cap.parse_depth_chart(LIONS_DEPTH_HTML, "DET")
        self.assertEqual(rows[0]["player"], "Jameson Williams")
        self.assertEqual(rows[0]["jersey"], "")
        self.assertEqual(rows[0]["rank"], "1")

    def test_image_only_chart_yields_no_rows_and_a_problem(self):
        rows, problems = cap.parse_depth_chart("<p>Unofficial Depth Chart</p>", "HOU")
        self.assertEqual(rows, [])
        self.assertTrue(problems)


class GameBookTests(unittest.TestCase):
    def test_header_facts(self):
        facts, starters, inactives = cap.parse_game_book(GAME_BOOK_TEXT)
        self.assertEqual(facts["game_date"], "Sunday, 11/15/2026")
        self.assertEqual(facts["venue"], "Allianz Arena")
        self.assertEqual(facts["roof_status"], "Open")
        self.assertEqual(facts["surface"], "Natural Grass")
        self.assertEqual(facts["attendance"], "70,225")
        self.assertTrue(starters)
        self.assertTrue(inactives)

    def test_starters_carry_position_jersey_and_player(self):
        _f, starters, _i = cap.parse_game_book(GAME_BOOK_TEXT)
        names = {(s["unit"], s["player"]) for s in starters}
        self.assertIn(("offense", "W.Campbell"), names)
        self.assertIn(("defense", "A.Hutchinson"), names)

    def test_inactive_list_is_read(self):
        _f, _s, inactives = cap.parse_game_book(GAME_BOOK_TEXT)
        self.assertIn("C.Davis", [i["player"] for i in inactives])
        self.assertEqual(inactives[0]["status"], "Not Active")


class GameCentreTests(unittest.TestCase):
    def test_location_and_stadium(self):
        info = cap.parse_game_center(GAME_CENTRE_TEXT)
        self.assertEqual(info["location"], "HOUSTON, TX")
        self.assertEqual(info["stadium"], "RELIANT STADIUM")
        self.assertIn("gamecenter/ab582c2f", info["game_book_url"])


class DriftTests(unittest.TestCase):
    def _ledger_row(self, kind, sid, status, rows):
        return {"source_kind": kind, "source_id": sid, "http_status": status,
                "rows_parsed": rows, "problems": "", "capture_id": "d/" + sid}

    def test_out_of_range_raises_alarm(self):
        led = cap.Ledger.__new__(cap.Ledger)
        led.rows = [self._ledger_row("injuries", "injuries_2026_reg10", 200, 3)]
        alarms = cap.check_drift(led, {"injuries": {"min_rows": 140, "max_rows": 420}})
        self.assertEqual(alarms[0]["state"], "alarm")

    def test_in_range_is_ok(self):
        led = cap.Ledger.__new__(cap.Ledger)
        led.rows = [self._ledger_row("injuries", "injuries_2026_reg10", 200, 276)]
        alarms = cap.check_drift(led, {"injuries": {"min_rows": 140, "max_rows": 420}})
        self.assertEqual(alarms[0]["state"], "ok")

    def test_documented_zero_is_a_known_exception_not_a_failure(self):
        led = cap.Ledger.__new__(cap.Ledger)
        led.rows = [self._ledger_row("depth", "depth_HOU", 404, 0)]
        alarms = cap.check_drift(led, {"depth": {"min_rows": 8, "max_rows": 80},
                                       "known_zero": {"depth_HOU": "image only"}})
        self.assertEqual(alarms[0]["state"], "known_exception")

    def test_http_failure_always_alarms(self):
        led = cap.Ledger.__new__(cap.Ledger)
        led.rows = [self._ledger_row("schedule", "schedule_2026_week11", 500, 0)]
        alarms = cap.check_drift(led, {"schedule": {"min_rows": 8, "max_rows": 18}})
        self.assertEqual(alarms[0]["state"], "alarm")


if __name__ == "__main__":
    unittest.main()

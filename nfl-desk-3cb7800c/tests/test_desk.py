"""Negative-control tests: each check must fail on a planted error, and pass on the committed data."""
import copy
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
DESK = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, DESK)

import verify  # noqa: E402


def committed():
    games = verify.load("week11_schedule.csv")
    byes = verify.load("week11_byes.csv")
    extract = verify.read_text(os.path.join(verify.RAW, "nfl_week11_schedule_extract.txt"))
    return games, byes, extract


class ScheduleChecks(unittest.TestCase):
    def test_committed_schedule_passes(self):
        games, byes, extract = committed()
        self.assertEqual(verify.check_schedule(games, byes, extract), [])

    def test_missing_game_is_caught(self):
        games, byes, extract = committed()
        fails = verify.check_schedule(games[:-1], byes, extract)
        self.assertTrue(any("expected 13 games" in f for f in fails))

    def test_weekday_mismatch_is_caught(self):
        games, byes, extract = committed()
        games = copy.deepcopy(games)
        games[0]["weekday"] = "Friday"
        fails = verify.check_schedule(games, byes, extract)
        self.assertTrue(any("weekday" in f for f in fails))

    def test_club_missing_is_caught(self):
        games, byes, extract = committed()
        games = copy.deepcopy(games)
        games[0]["home_code"] = "NO"  # NO appears twice, HOU disappears
        fails = verify.check_schedule(games, byes, extract)
        self.assertTrue(any("appear twice" in f or "mismatch" in f for f in fails))

    def test_altered_raw_line_is_caught(self):
        games, byes, extract = committed()
        games = copy.deepcopy(games)
        games[1]["raw_line"] = games[1]["raw_line"].replace("1:00 PM", "1:30 PM")
        fails = verify.check_schedule(games, byes, extract)
        self.assertTrue(any("verbatim" in f for f in fails))

    def test_non_official_game_url_is_caught(self):
        games, byes, extract = committed()
        games = copy.deepcopy(games)
        games[2]["official_game_url"] = "https://example.com/games/ravens-at-panthers-2026-reg-11"
        fails = verify.check_schedule(games, byes, extract)
        self.assertTrue(any("game URL" in f for f in fails))

    def test_bye_code_not_canonical_is_caught(self):
        games, byes, extract = committed()
        byes = copy.deepcopy(byes)
        byes[3]["standings_logo_code"] = "LAR"  # the schedule code must not be used as the join key
        fails = verify.check_schedule(games, byes, extract)
        self.assertTrue(any("not canonical" in f for f in fails))


class AvailabilityChecks(unittest.TestCase):
    def test_committed_availability_passes(self):
        avail = verify.load("availability_status.csv")
        meta = verify.read_text(os.path.join(verify.RAW, "nfl_injury_reg11_fetch_meta.txt"))
        self.assertEqual(verify.check_availability(avail, meta), [])

    def test_published_claim_without_evidence_is_caught(self):
        avail = verify.load("availability_status.csv")
        avail = copy.deepcopy(avail)
        avail[0]["status"] = "Published"
        meta = verify.read_text(os.path.join(verify.RAW, "nfl_injury_reg11_fetch_meta.txt"))
        fails = verify.check_availability(avail, meta)
        self.assertTrue(any("not published" in f.lower() for f in fails))

    def test_invented_count_is_caught(self):
        avail = copy.deepcopy(verify.load("availability_status.csv"))
        avail[1]["status"] = "Served; 254 players listed"
        meta = verify.read_text(os.path.join(verify.RAW, "nfl_injury_reg11_fetch_meta.txt"))
        fails = verify.check_availability(avail, meta)
        self.assertTrue(any("count" in f for f in fails))


class RegisterChecks(unittest.TestCase):
    def registers(self):
        return (verify.load("flagged.csv"), verify.load("suggestions.csv"), verify.load("questions.csv"),
                verify.load("sources.csv"), verify.load("repo_checks.csv"))

    def test_committed_registers_pass(self):
        self.assertEqual(verify.check_registers(*self.registers()), [])

    def test_suggestion_cannot_be_marked_decided(self):
        flags, sugg, quest, sources, repo = self.registers()
        sugg = copy.deepcopy(sugg)
        sugg[0]["decision"] = "IMPLEMENTED"
        fails = verify.check_registers(flags, sugg, quest, sources, repo)
        self.assertTrue(any("PENDING REVIEW" in f for f in fails))

    def test_official_row_must_link_to_nfl(self):
        flags, sugg, quest, sources, repo = self.registers()
        sources = copy.deepcopy(sources)
        sources[0]["url"] = "https://github.com/example"
        fails = verify.check_registers(flags, sugg, quest, sources, repo)
        self.assertTrue(any("must link to nfl.com" in f for f in fails))

    def test_flag_without_https_link_is_caught(self):
        flags, sugg, quest, sources, repo = self.registers()
        flags = copy.deepcopy(flags)
        flags[0]["evidence_url"] = "http://www.nfl.com/injuries/league/2026/reg11"
        fails = verify.check_registers(flags, sugg, quest, sources, repo)
        self.assertTrue(any("evidence link" in f for f in fails))

    def test_duplicate_ids_are_caught(self):
        flags, sugg, quest, sources, repo = self.registers()
        flags = copy.deepcopy(flags)
        flags[1]["flag_id"] = flags[0]["flag_id"]
        fails = verify.check_registers(flags, sugg, quest, sources, repo)
        self.assertTrue(any("duplicate" in f for f in fails))


class PageChecks(unittest.TestCase):
    def test_row_without_link_or_badge_is_caught(self):
        p = verify.PageParser()
        p.feed("<table><tbody><tr><td>no source here</td></tr>"
               "<tr><td><a href='https://www.nfl.com/x'>x</a></td></tr></tbody></table>")
        self.assertEqual(p.rows, [False, True])

    def test_badge_counts_as_source_class(self):
        p = verify.PageParser()
        p.feed("<table><tbody><tr><td><span class='badge b-unverified'>UNVERIFIED</span></td></tr></tbody></table>")
        self.assertEqual(p.rows, [True])

    def test_committed_pages_pass(self):
        fails, stats = verify.check_pages()
        self.assertEqual(fails, [])
        self.assertEqual(stats["pages"], 9)


class DeskCrossCheck(unittest.TestCase):
    def test_committed_cross_check_passes(self):
        repo = verify.load("repo_checks.csv")
        self.assertEqual(verify.check_desk_crosscheck(repo), [])

    def test_wrong_recorded_count_is_caught(self):
        repo = copy.deepcopy(verify.load("repo_checks.csv"))
        for r in repo:
            if r["check_id"] == "R-07":
                r["value_at_read"] = "24 (wrong)"
        fails = verify.check_desk_crosscheck(repo)
        self.assertTrue(any("recorded 24" in f for f in fails))


class HashChecks(unittest.TestCase):
    def test_committed_hashes_match(self):
        self.assertEqual(verify.check_hashes(), [])


class NoGitInBuild(unittest.TestCase):
    def test_build_script_makes_no_git_or_clock_calls(self):
        with open(os.path.join(DESK, "tools", "build_site.py"), encoding="utf-8") as fh:
            src = fh.read()
        for banned in ("import subprocess", "os.system", "datetime.now", "time.time", "urlopen", "import requests", "'git',"):
            self.assertNotIn(banned, src, f"build must be deterministic: found {banned!r}")


if __name__ == "__main__":
    unittest.main()

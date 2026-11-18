#!/usr/bin/env python3
"""One-time capture: official NFL.com reads by session 6cbf25fa on 2026-11-18.

Writes the raw extracts (verbatim cell sequences as fetched), a manifest, the
SHA256SUMS of the extracts, and the parsed capture CSVs.  No clock calls at
runtime: the read stamp is taken from the environment (READ_UTC) or from the
claim commit bound, never invented here.

Sources fetched with the sandbox page-fetch tool on 2026-11-18, after claim
commit a3624df88a671dd91f1d64c92e8cba16d64bdafb (2026-11-18T03:45:53Z):
  - https://www.nfl.com/standings/league/2026/REG            (2 chunks)
  - https://www.nfl.com/scores/2026/reg10                    (2 chunks; final URL week-10)
  - https://www.nfl.com/injuries/league/2026/reg11           (8 chunks; final URL reg10 -
                                                              requested reg11 but the page
                                                              served Week 10 content)
  - https://www.nfl.com/games/vikings-at-49ers-2026-reg-11   (1 chunk; game centre)

The fetch tool returns processed page text, not server bytes; hashes therefore
cover the extract files written here (verbatim cell sequences of the evidence
tables), not the server's raw HTML.  This limitation is published on the desk's
Flagged page (mirrors flag F-09 of session 3cb7800c).
"""
import csv
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
DATA = os.path.abspath(os.path.join(HERE, "..", "data", "nfl-desk-6cbf25fa"))
LEADS = os.path.join(DATA, "injury_reads")

CLAIM_COMMIT_UTC = "2026-11-18T03:45:53Z"
STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
SCORES_URL = "https://www.nfl.com/scores/2026/reg10"
INJ_URL = "https://www.nfl.com/injuries/league/2026/reg11"
INJ_FINAL_URL = "https://www.nfl.com/injuries/league/2026/reg10"
GAME_URL = "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11"


def now_utc():
    """Clock time of this capture write, from the environment, not the wall."""
    for var in ("READ_UTC",):
        if os.environ.get(var):
            return os.environ[var]
    return subprocess.check_output(
        ["git", "log", "-1", "--format=%cI", "--", os.path.relpath(__file__, os.path.abspath(os.path.join(HERE, "..")))],
        cwd=os.path.abspath(os.path.join(HERE, "..")),
        text=True,
    ).strip()


# ---------------------------------------------------------------- standings
# Verbatim cell sequences of the 32 league-view rows (page chunks 1-2).
# Cell order as printed on the page; column semantics are NOT assumed here —
# the pipeline verifies W/L/T and PF/PA/NET against game-derived values.
STANDINGS_ROWS = [
    ["Buffalo Bills", "BUF", "8", "1", "0", "0.889", "287", "199", "88", "3 - 1 - 0", "5 - 0 - 0", "1 - 1 - 0", "0.500", "5 - 1 - 0", "0.833", "3 - 0 - 0", "5W", "5 - 0 - 0"],
    ["San Francisco 49ers", "SF", "8", "1", "0", "0.889", "281", "196", "85", "5 - 0 - 0", "3 - 1 - 0", "3 - 0 - 0", "1.000", "5 - 1 - 0", "0.833", "3 - 0 - 0", "2W", "4 - 1 - 0"],
    ["Chicago Bears", "CHI", "7", "2", "0", "0.778", "241", "184", "57", "4 - 1 - 0", "3 - 1 - 0", "0 - 2 - 0", "0.000", "5 - 2 - 0", "0.714", "2 - 0 - 0", "4W", "4 - 1 - 0"],
    ["Cincinnati Bengals", "CIN", "7", "2", "0", "0.778", "278", "193", "85", "3 - 1 - 0", "4 - 1 - 0", "2 - 1 - 0", "0.667", "5 - 2 - 0", "0.714", "2 - 0 - 0", "5W", "5 - 0 - 0"],
    ["Denver Broncos", "DEN", "7", "2", "0", "0.778", "198", "186", "12", "4 - 0 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "3 - 1 - 0", "0.750", "4 - 1 - 0", "5W", "5 - 0 - 0"],
    ["Detroit Lions", "DET", "7", "2", "0", "0.778", "257", "199", "58", "5 - 0 - 0", "2 - 2 - 0", "2 - 0 - 0", "1.000", "4 - 1 - 0", "0.800", "3 - 1 - 0", "5W", "5 - 0 - 0"],
    ["Jacksonville Jaguars", "JAX", "7", "2", "0", "0.778", "269", "144", "125", "4 - 1 - 0", "3 - 1 - 0", "2 - 1 - 0", "0.667", "6 - 2 - 0", "0.750", "1 - 0 - 0", "3W", "4 - 1 - 0"],
    ["Kansas City Chiefs", "KC", "7", "2", "0", "0.778", "237", "156", "81", "4 - 0 - 0", "3 - 2 - 0", "3 - 1 - 0", "0.750", "6 - 1 - 0", "0.857", "1 - 1 - 0", "2W", "3 - 2 - 0"],
    ["Minnesota Vikings", "MIN", "7", "2", "0", "0.778", "176", "126", "50", "3 - 1 - 0", "4 - 1 - 0", "3 - 1 - 0", "0.750", "5 - 1 - 0", "0.833", "2 - 1 - 0", "1W", "3 - 2 - 0"],
    ["Pittsburgh Steelers", "PIT", "6", "3", "0", "0.667", "198", "182", "16", "4 - 0 - 0", "2 - 3 - 0", "2 - 2 - 0", "0.500", "3 - 3 - 0", "0.500", "3 - 0 - 0", "1L", "4 - 1 - 0"],
    ["New York Giants", "NYG", "5", "3", "1", "0.611", "203", "196", "7", "3 - 2 - 0", "2 - 1 - 1", "2 - 1 - 1", "0.625", "3 - 3 - 1", "0.500", "2 - 0 - 0", "1L", "2 - 2 - 1"],
    ["Cleveland Browns", "CLE", "6", "4", "0", "0.600", "188", "220", "-32", "4 - 0 - 0", "2 - 4 - 0", "2 - 1 - 0", "0.667", "4 - 3 - 0", "0.571", "2 - 1 - 0", "1W", "3 - 2 - 0"],
    ["Green Bay Packers", "GB", "6", "4", "0", "0.600", "226", "221", "5", "3 - 2 - 0", "3 - 2 - 0", "1 - 3 - 0", "0.250", "4 - 4 - 0", "0.500", "2 - 0 - 0", "1L", "3 - 2 - 0"],
    ["Los Angeles Rams", "LAR", "6", "4", "0", "0.600", "248", "187", "61", "2 - 3 - 0", "4 - 1 - 0", "1 - 2 - 0", "0.333", "4 - 2 - 0", "0.667", "2 - 2 - 0", "4W", "4 - 1 - 0"],
    ["Seattle Seahawks", "SEA", "6", "4", "0", "0.600", "223", "175", "48", "4 - 2 - 0", "2 - 2 - 0", "2 - 1 - 0", "0.667", "2 - 3 - 0", "0.400", "4 - 1 - 0", "2W", "3 - 2 - 0"],
    ["New England Patriots", "NE", "5", "5", "0", "0.500", "221", "242", "-21", "3 - 1 - 0", "2 - 4 - 0", "3 - 0 - 0", "1.000", "5 - 1 - 0", "0.833", "0 - 4 - 0", "2L", "2 - 3 - 0"],
    ["Carolina Panthers", "CAR", "4", "5", "0", "0.444", "219", "236", "-17", "1 - 3 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "4 - 3 - 0", "0.571", "0 - 2 - 0", "1W", "2 - 3 - 0"],
    ["Baltimore Ravens", "BAL", "4", "6", "0", "0.400", "209", "259", "-50", "1 - 4 - 0", "3 - 2 - 0", "0 - 2 - 0", "0.000", "2 - 5 - 0", "0.286", "2 - 1 - 0", "5L", "0 - 5 - 0"],
    ["Dallas Cowboys", "DAL", "4", "6", "0", "0.400", "286", "282", "4", "1 - 4 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "2 - 5 - 0", "0.286", "2 - 1 - 0", "1L", "2 - 3 - 0"],
    ["Las Vegas Raiders", "LV", "4", "6", "0", "0.400", "251", "289", "-38", "1 - 4 - 0", "3 - 2 - 0", "1 - 1 - 0", "0.500", "3 - 3 - 0", "0.500", "1 - 3 - 0", "2L", "1 - 4 - 0"],
    ["Washington Commanders", "WAS", "3", "5", "1", "0.389", "196", "223", "-27", "2 - 2 - 1", "1 - 3 - 0", "2 - 2 - 1", "0.500", "3 - 4 - 1", "0.438", "0 - 1 - 0", "1W", "2 - 2 - 1"],
    ["Houston Texans", "HOU", "3", "6", "0", "0.333", "233", "219", "14", "0 - 4 - 0", "3 - 2 - 0", "2 - 1 - 0", "0.667", "3 - 4 - 0", "0.429", "0 - 2 - 0", "1L", "3 - 2 - 0"],
    ["New Orleans Saints", "NO", "3", "6", "0", "0.333", "202", "236", "-34", "1 - 5 - 0", "2 - 1 - 0", "0 - 2 - 0", "0.000", "1 - 4 - 0", "0.200", "2 - 2 - 0", "1L", "2 - 3 - 0"],
    ["Tampa Bay Buccaneers", "TB", "3", "6", "0", "0.333", "202", "178", "24", "1 - 4 - 0", "2 - 2 - 0", "2 - 0 - 0", "1.000", "3 - 3 - 0", "0.500", "0 - 3 - 0", "1L", "3 - 2 - 0"],
    ["Arizona Cardinals", "AZ", "3", "7", "0", "0.300", "184", "289", "-105", "0 - 4 - 0", "3 - 3 - 0", "1 - 4 - 0", "0.200", "2 - 6 - 0", "0.250", "1 - 1 - 0", "2L", "2 - 3 - 0"],
    ["Atlanta Falcons", "ATL", "3", "7", "0", "0.300", "201", "258", "-57", "1 - 5 - 0", "2 - 2 - 0", "1 - 2 - 0", "0.333", "3 - 3 - 0", "0.500", "0 - 4 - 0", "3L", "1 - 4 - 0"],
    ["Indianapolis Colts", "IND", "3", "7", "0", "0.300", "208", "271", "-63", "2 - 3 - 0", "1 - 4 - 0", "1 - 2 - 0", "0.333", "2 - 5 - 0", "0.286", "1 - 2 - 0", "1W", "1 - 4 - 0"],
    ["Philadelphia Eagles", "PHI", "2", "7", "0", "0.222", "148", "221", "-73", "1 - 4 - 0", "1 - 3 - 0", "1 - 3 - 0", "0.250", "1 - 6 - 0", "0.143", "1 - 1 - 0", "7L", "0 - 5 - 0"],
    ["New York Jets", "NYJ", "2", "8", "0", "0.200", "194", "254", "-60", "1 - 4 - 0", "1 - 4 - 0", "0 - 3 - 0", "0.000", "2 - 5 - 0", "0.286", "0 - 3 - 0", "5L", "0 - 5 - 0"],
    ["Los Angeles Chargers", "LAC", "1", "8", "0", "0.111", "144", "239", "-95", "0 - 4 - 0", "1 - 4 - 0", "0 - 3 - 0", "0.000", "1 - 5 - 0", "0.167", "0 - 3 - 0", "1W", "1 - 4 - 0"],
    ["Miami Dolphins", "MIA", "1", "8", "0", "0.111", "148", "224", "-76", "0 - 4 - 0", "1 - 4 - 0", "1 - 1 - 0", "0.500", "1 - 5 - 0", "0.167", "0 - 3 - 0", "3L", "1 - 4 - 0"],
    ["Tennessee Titans", "TEN", "1", "8", "0", "0.111", "167", "239", "-72", "0 - 5 - 0", "1 - 3 - 0", "1 - 2 - 0", "0.333", "1 - 6 - 0", "0.143", "0 - 2 - 0", "3L", "1 - 4 - 0"],
]

# ---------------------------------------------------------------- week-10 finals
# Away/home, scores, and the printed date section; away_team is the visiting
# club as printed on the official scores page.  The Munich game is printed as
# "Sunday, November 15th, International Game".
RESULTS_WK10 = [
    # slug, away, home, away_pts, home_pts, printed_section, neutral
    ["commanders-at-giants-2026-reg-10", "WAS", "NYG", 24, 21, "Thursday Night Football, November 12th", "no"],
    ["patriots-at-lions-2026-reg-10", "NE", "DET", 10, 35, "Sunday, November 15th, International Game (Munich 2026 logo)", "yes"],
    ["chiefs-at-falcons-2026-reg-10", "KC", "ATL", 35, 13, "Sunday, November 15th", "no"],
    ["texans-at-browns-2026-reg-10", "HOU", "CLE", 24, 27, "Sunday, November 15th", "no"],
    ["vikings-at-packers-2026-reg-10", "MIN", "GB", 30, 10, "Sunday, November 15th", "no"],
    ["dolphins-at-colts-2026-reg-10", "MIA", "IND", 22, 24, "Sunday, November 15th", "no"],
    ["panthers-at-saints-2026-reg-10", "CAR", "NO", 20, 17, "Sunday, November 15th", "no"],
    ["bills-at-jets-2026-reg-10", "BUF", "NYJ", 31, 12, "Sunday, November 15th", "no"],
    ["jaguars-at-titans-2026-reg-10", "JAX", "TEN", 40, 23, "Sunday, November 15th", "no"],
    ["rams-at-cardinals-2026-reg-10", "LAR", "AZ", 34, 6, "Sunday, November 15th", "no"],
    ["seahawks-at-raiders-2026-reg-10", "SEA", "LV", 21, 13, "Sunday, November 15th", "no"],
    ["49ers-at-cowboys-2026-reg-10", "SF", "DAL", 46, 40, "Sunday, November 15th", "no"],
    ["steelers-at-bengals-2026-reg-10", "PIT", "CIN", 18, 38, "Sunday Night Football, November 15th", "no"],
    ["chargers-at-ravens-2026-reg-10", "LAC", "BAL", 23, 20, "Monday Night Football, November 16th", "no"],
]

WEEK10_BYES_PRINTED = ["CHI", "DEN", "PHI", "TB"]

# ---------------------------------------------------------------- game centre (MIN@SF)
MIN_SF_GAME_CENTRE = {
    "slug": "vikings-at-49ers-2026-reg-11",
    "away": "MIN", "home": "SF",
    "printed": {
        "location": "MEXICO CITY",
        "stadium": "ESTADIO BANORTE",
        "kickoff": "Nov 22, 8:20PM",
        "network": "NBC",
        "records_printed": {"MIN": "7-2", "SF": "8-1"},
    },
    "url": GAME_URL,
}

# ---------------------------------------------------------------- injuries (as printed, 28 tables)
# (team, [(player, position, injuries, practice_status, game_status), ...])
INJURIES = [
    ("WAS", [
        ("John Bates", "TE", "", "Full Participation in Practice", ""),
        ("Treylon Burks", "WR", "", "Did Not Participate In Practice", ""),
        ("Jayden Daniels", "QB", "", "Full Participation in Practice", ""),
        ("Matt Gulbin", "C", "", "Full Participation in Practice", ""),
        ("Chig Okonkwo", "TE", "", "Full Participation in Practice", ""),
        ("Lucas Patrick", "C", "Concussion", "Did Not Participate In Practice", "Out"),
        ("Amik Robertson", "CB", "", "Limited Participation in Practice", ""),
        ("Shy Tuttle", "DT", "", "Full Participation in Practice", ""),
        ("Colson Yankoff", "TE", "Knee", "Did Not Participate In Practice", "Out"),
    ]),
    ("NYG", [
        ("Abdul Carter", "LB", "", "Full Participation in Practice", ""),
        ("Jermaine Eluemunor", "T", "", "Full Participation in Practice", ""),
        ("Malik Harrison", "LB", "Groin", "Limited Participation in Practice", "Questionable"),
        ("Colton Hood", "CB", "", "Full Participation in Practice", ""),
        ("Theo Johnson", "TE", "", "Full Participation in Practice", ""),
        ("Charlie Jones", "WR", "", "Full Participation in Practice", ""),
        ("J.J. McCarthy", "QB", "", "Full Participation in Practice", ""),
        ("Darnell Mooney", "WR", "", "Full Participation in Practice", ""),
        ("Malik Nabers", "WR", "", "Full Participation in Practice", ""),
        ("Cam Skattebo", "RB", "", "Full Participation in Practice", ""),
        ("Andrew Thomas", "T", "", "Full Participation in Practice", ""),
    ]),
    ("NE", [
        ("Ben Brown", "C", "Knee", "Did Not Participate In Practice", "Out"),
        ("A.J. Brown", "WR", "Ankle, Knee", "Limited Participation in Practice", "Questionable"),
        ("Kevin Byard", "S", "Chest", "Full Participation in Practice", "Questionable"),
        ("Carlton Davis III", "CB", "Knee", "Did Not Participate In Practice", "Out"),
        ("Reggie Gilliam", "FB", "Knee", "Limited Participation in Practice", "Questionable"),
        ("TreVeyon Henderson", "RB", "Illness", "Did Not Participate In Practice", "Out"),
        ("Hunter Henry", "TE", "", "Limited Participation in Practice", ""),
        ("Cameron Latu", "TE", "Back", "Limited Participation in Practice", "Questionable"),
        ("Drake Maye", "QB", "", "Full Participation in Practice", ""),
        ("Morgan Moses", "T", "", "Full Participation in Practice", ""),
        ("Walter Rouse", "T", "Concussion", "Limited Participation in Practice", "Questionable"),
        ("Brenden Schooler", "S", "Hamstring", "Limited Participation in Practice", "Questionable"),
        ("Rhamondre Stevenson", "RB", "Knee", "Limited Participation in Practice", "Questionable"),
        ("Greg Van Roten", "G", "Hamstring", "Full Participation in Practice", "Questionable"),
        ("Charles Woods", "CB", "Hamstring", "Full Participation in Practice", "Questionable"),
    ]),
    ("DET", [
        ("Brian Branch", "S", "", "Full Participation in Practice", ""),
        ("Jared Goff", "QB", "", "Full Participation in Practice", ""),
        ("Kerby Joseph", "S", "Knee", "Did Not Participate In Practice", "Out"),
        ("Cade Mays", "C", "Ankle", "Did Not Participate In Practice", "Out"),
        ("D.J. Reed", "CB", "Hip", "Did Not Participate In Practice", "Out"),
        ("Jacob Saylors", "RB", "", "Full Participation in Practice", ""),
        ("Amon-Ra St. Brown", "WR", "Rib", "Limited Participation in Practice", "Questionable"),
        ("Sione Vaki", "RB", "Ankle", "Limited Participation in Practice", "Questionable"),
        ("DJ Wonnum", "DE", "", "Full Participation in Practice", ""),
    ]),
    ("KC", [
        ("Jeffrey Bassa", "LB", "", "Full Participation in Practice", ""),
        ("Mansoor Delane", "CB", "Shoulder", "Full Participation in Practice", "Questionable"),
        ("Justin Fields", "QB", "", "Full Participation in Practice", ""),
        ("Jaden Hicks", "S", "", "Full Participation in Practice", ""),
        ("Travis Kelce", "TE", "", "Full Participation in Practice", ""),
        ("Patrick Mahomes", "QB", "", "Full Participation in Practice", ""),
        ("Jaylon Moore", "T", "Ankle", "Did Not Participate In Practice", "Out"),
        ("Omarr Norman-Lott", "DT", "Knee", "Limited Participation in Practice", "Out"),
        ("Jaydn Ott", "RB", "Hamstring", "Limited Participation in Practice", "Questionable"),
        ("Rashee Rice", "WR", "", "Full Participation in Practice", ""),
        ("Kenneth Walker III", "RB", "Groin", "Did Not Participate In Practice", "Questionable"),
        ("Peter Woods", "DT", "Neck", "Did Not Participate In Practice", "Out"),
        ("Xavier Worthy", "WR", "", "Full Participation in Practice", ""),
    ]),
    ("ATL", [
        ("Zachariah Branch", "WR", "Hamstring", "Did Not Participate In Practice", "Out"),
        ("Kendal Daniels", "LB", "", "Full Participation in Practice", ""),
        ("Divine Deablo", "LB", "Forearm", "Did Not Participate In Practice", "Doubtful"),
        ("Gervon Dexter Sr.", "DT", "Illness", "Limited Participation in Practice", "Questionable"),
        ("Jake Matthews", "T", "", "Limited Participation in Practice", ""),
        ("Liam McCullough", "LS", "", "Did Not Participate In Practice", ""),
        ("James Pearce Jr.", "DE", "Back", "Limited Participation in Practice", "Questionable"),
        ("Za'Darius Smith", "DE", "", "Full Participation in Practice", ""),
        ("Jawaan Taylor", "T", "", "Limited Participation in Practice", ""),
        ("Cameron Thomas", "DE", "", "Full Participation in Practice", ""),
        ("Josh Woods", "LB", "Ankle", "Full Participation in Practice", "Questionable"),
    ]),
    ("MIN", [
        ("Jordan Addison", "WR", "Thumb", "Limited Participation in Practice", "Questionable"),
        ("Blake Cashman", "LB", "Concussion", "Limited Participation in Practice", "Out"),
        ("Christian Darrisaw", "T", "", "Did Not Participate In Practice", ""),
        ("T.J. Hockenson", "TE", "Wrist, Chest", "Did Not Participate In Practice", "Out"),
        ("Tyrion Ingram-Dawkins", "DT", "Ankle", "Did Not Participate In Practice", "Out"),
        ("Theo Jackson", "S", "", "Full Participation in Practice", ""),
        ("Jauan Jennings", "WR", "Calf", "Did Not Participate In Practice", "Out"),
        ("Josh Metellus", "S", "Shoulder", "Limited Participation in Practice", "Questionable"),
        ("Kyler Murray", "QB", "Hamstring", "Did Not Participate In Practice", "Out"),
        ("Harrison Smith", "S", "", "Limited Participation in Practice", ""),
        ("Kyle Van Noy", "LB", "Calf", "Limited Participation in Practice", "Questionable"),
        ("Jay Ward", "S", "", "Full Participation in Practice", ""),
        ("Carson Wentz", "QB", "", "Full Participation in Practice", ""),
    ]),
    ("GB", [
        ("Aaron Banks", "G", "", "Limited Participation in Practice", ""),
        ("Chris Brooks", "RB", "Ankle", "Limited Participation in Practice", "Questionable"),
        ("Javon Bullard", "S", "Ankle, Knee", "Limited Participation in Practice", "Questionable"),
        ("Zaire Franklin", "LB", "Shin", "Did Not Participate In Practice", "Doubtful"),
        ("Travis Glover", "G", "Knee", "Limited Participation in Practice", "Questionable"),
        ("Ty'Ron Hopper", "LB", "", "Full Participation in Practice", ""),
        ("Josh Jacobs", "RB", "Finger", "Did Not Participate In Practice", "Out"),
        ("Xavier McKinney", "S", "Foot", "Limited Participation in Practice", "Questionable"),
        ("Bo Melton", "WR", "", "Full Participation in Practice", ""),
        ("Skyy Moore", "WR", "Ankle", "Limited Participation in Practice", "Questionable"),
        ("Micah Parsons", "LB", "Knee, Illness", "Limited Participation in Practice", "Out"),
        ("Sean Rhyan", "C", "Ankle", "Did Not Participate In Practice", "Out"),
        ("Trey Smack", "K", "", "Full Participation in Practice", ""),
        ("Lukas Van Ness", "LB", "Back", "Limited Participation in Practice", "Questionable"),
        ("Josh Whyle", "TE", "Concussion", "Did Not Participate In Practice", "Out"),
        ("Savion Williams", "WR", "", "Limited Participation in Practice", ""),
        ("Kevin Zeitler", "G", "Ankle, Triceps", "Did Not Participate In Practice", "Questionable"),
    ]),
    ("JAX", [
        ("Jessie Bates", "S", "Not injury related - resting player", "Limited Participation in Practice", "Out"),
        ("Ezra Cleveland", "G", "", "Full Participation in Practice", ""),
        ("Branson Combs", "LB", "", "Full Participation in Practice", ""),
        ("Jordan Davis", "DT", "Not injury related - resting player", "Limited Participation in Practice", "Out"),
        ("BJ Green II", "DE", "Forearm", "Full Participation in Practice", "Out"),
        ("Robert Hainsey", "C", "Concussion", "Limited Participation in Practice", "Questionable"),
        ("Antonio Johnson", "S", "", "Limited Participation in Practice", ""),
        ("Jakobi Meyers", "WR", "", "Limited Participation in Practice", ""),
        ("Chris Rodriguez Jr.", "RB", "", "Limited Participation in Practice", ""),
        ("Bhayshul Tuten", "RB", "", "Limited Participation in Practice", ""),
        ("Travon Walker", "DE", "", "Limited Participation in Practice", ""),
    ]),
    ("TEN", [
        ("Cody Barton", "LB", "Concussion", "Did Not Participate In Practice", "Out"),
        ("John Franklin-Myers", "DE", "", "Full Participation in Practice", ""),
        ("Marcus Harris", "CB", "", "Full Participation in Practice", ""),
        ("Anthony Hill Jr.", "LB", "Neck", "Did Not Participate In Practice", "Out"),
        ("Jaylon Jones", "CB", "", "Full Participation in Practice", ""),
        ("JC Latham", "T", "", "Full Participation in Practice", ""),
        ("Tony Pollard", "RB", "", "Full Participation in Practice", ""),
        ("Peter Skoronski", "G", "Hamstring", "Did Not Participate In Practice", "Out"),
        ("Tyjae Spears", "RB", "Knee", "Full Participation in Practice", "Questionable"),
        ("Carnell Tate", "WR", "Shoulder", "Did Not Participate In Practice", "Out"),
        ("Tommy Townsend", "P", "Knee, Achilles", "Did Not Participate In Practice", "Out"),
        ("Kevin Winston Jr.", "S", "", "Full Participation in Practice", ""),
    ]),
    ("BUF", [
        ("Alec Anderson", "G", "", "Full Participation in Practice", ""),
        ("Christian Benford", "CB", "Wrist", "Full Participation in Practice", "Questionable"),
        ("Terrel Bernard", "LB", "", "Did Not Participate In Practice", ""),
        ("Spencer Brown", "T", "Ankle", "Did Not Participate In Practice", "Doubtful"),
        ("Dion Dawkins", "T", "", "Full Participation in Practice", ""),
        ("Sam Franklin Jr.", "S", "Shoulder", "Limited Participation in Practice", "Questionable"),
        ("Greg Gaines", "DT", "", "Full Participation in Practice", ""),
        ("Jordan Hancock", "CB", "Hamstring", "Full Participation in Practice", "Questionable"),
        ("Dalton Kincaid", "TE", "", "Full Participation in Practice", ""),
        ("Connor McGovern", "C", "", "Full Participation in Practice", ""),
        ("Ed Oliver", "DE", "", "Did Not Participate In Practice", ""),
        ("Ar'maj Reed-Adams", "G", "", "Full Participation in Practice", ""),
        ("T.J. Sanders", "DE", "", "Full Participation in Practice", ""),
        ("Tyrell Shavers", "WR", "Knee", "Full Participation in Practice", "Questionable"),
    ]),
    ("NYJ", [
        ("Jarvis Brownlee Jr.", "CB", "Illness", "Limited Participation in Practice", "Questionable"),
        ("Omar Cooper Jr.", "WR", "Ankle", "Full Participation in Practice", "Questionable"),
        ("Adonai Mitchell", "WR", "Knee", "Full Participation in Practice", "Questionable"),
        ("Joseph Ossai", "DE", "Ankle", "Full Participation in Practice", "Questionable"),
        ("VJ Payne", "S", "Knee", "Full Participation in Practice", "Questionable"),
        ("Harrison Phillips", "DT", "Ankle", "Full Participation in Practice", "Questionable"),
        ("Trevin Wallace", "LB", "Groin", "Did Not Participate In Practice", "Out"),
        ("Garrett Wilson", "WR", "Concussion", "Full Participation in Practice", "Questionable"),
        ("Nahshon Wright", "CB", "Back", "Full Participation in Practice", "Questionable"),
    ]),
    ("MIA", [
        ("Tucker Addington", "LS", "", "Limited Participation in Practice", ""),
        ("Kaytron Allen", "RB", "", "Full Participation in Practice", ""),
        ("Darrell Baker Jr.", "CB", "Knee", "Full Participation in Practice", "Questionable"),
        ("Chris Bell", "WR", "Knee", "Did Not Participate In Practice", "Doubtful"),
        ("Aaron Brewer", "C", "Concussion", "Did Not Participate In Practice", "Out"),
        ("Malik Herring", "DE", "", "Full Participation in Practice", ""),
        ("Will Kacmarek", "TE", "", "Full Participation in Practice", ""),
        ("Michael Taaffe", "S", "", "Full Participation in Practice", ""),
        ("Dante Trader Jr.", "S", "", "Full Participation in Practice", ""),
        ("Jared Wayne", "WR", "Quadricep", "Did Not Participate In Practice", "Out"),
        ("Jaylen Wright", "RB", "", "Full Participation in Practice", ""),
    ]),
    ("IND", [
        ("Mo Alie-Cox", "TE", "Groin", "Did Not Participate In Practice", "Out"),
        ("CJ Allen", "LB", "", "Full Participation in Practice", ""),
        ("Jaylon Carlies", "LB", "Neck", "Did Not Participate In Practice", "Out"),
        ("Akeem Davis-Gaither", "LB", "Knee", "Did Not Participate In Practice", "Out"),
        ("A.J. Haulcy", "S", "", "Full Participation in Practice", ""),
        ("Arden Key", "DE", "", "Full Participation in Practice", ""),
        ("Will Mallory", "TE", "Hamstring", "Limited Participation in Practice", "Questionable"),
        ("Luke Rhodes", "LS", "Hamstring", "Did Not Participate In Practice", "Out"),
        ("Grover Stewart", "DT", "", "Full Participation in Practice", ""),
        ("Jonathan Taylor", "RB", "", "Full Participation in Practice", ""),
        ("Jerry Tillery", "DT", "Calf", "Did Not Participate In Practice", "Out"),
        ("Jalen Travis", "T", "Knee", "Did Not Participate In Practice", "Out"),
        ("Justin Walley", "CB", "", "Full Participation in Practice", ""),
        ("Charvarius Ward", "CB", "", "Full Participation in Practice", ""),
    ]),
    ("CAR", [
        ("Jonathon Brooks", "RB", "Groin", "Limited Participation in Practice", "Doubtful"),
        ("Brady Christensen", "G", "Hamstring", "Full Participation in Practice", "Questionable"),
        ("Trevor Etienne", "RB", "", "Full Participation in Practice", ""),
        ("Chuba Hubbard", "RB", "", "Full Participation in Practice", ""),
        ("Lee Hunter", "DT", "", "Full Participation in Practice", ""),
        ("Mike Jackson", "CB", "Groin", "Limited Participation in Practice", "Doubtful"),
        ("Will Lee III", "CB", "Hamstring", "Limited Participation in Practice", "Questionable"),
        ("Xavier Legette", "WR", "Knee", "Full Participation in Practice", "Questionable"),
        ("Damien Lewis", "G", "", "Full Participation in Practice", ""),
        ("Bobby Okereke", "LB", "Foot", "Did Not Participate In Practice", "Out"),
        ("Jaelan Phillips", "LB", "Hamstring", "Full Participation in Practice", "Questionable"),
        ("Torricelli Simpkins III", "G", "", "Full Participation in Practice", ""),
    ]),
    ("NO", [
        ("Kelvin Banks Jr.", "T", "", "Full Participation in Practice", ""),
        ("CJ Donaldson", "RB", "Shoulder", "Did Not Participate In Practice", "Out"),
        ("David Edwards", "G", "", "Full Participation in Practice", ""),
        ("Martin Emerson", "CB", "Shin", "Limited Participation in Practice", "Questionable"),
        ("Travis Etienne", "RB", "Hamstring", "Full Participation in Practice", "Questionable"),
        ("Noah Fant", "TE", "", "Full Participation in Practice", ""),
        ("Taliese Fuaga", "T", "Knee", "Did Not Participate In Practice", "Out"),
        ("Alvin Kamara", "RB", "", "Full Participation in Practice", ""),
        ("Erik McCoy", "C", "Biceps", "Did Not Participate In Practice", "Out"),
        ("Christen Miller", "DT", "Knee", "Did Not Participate In Practice", "Out"),
        ("Asim Richards", "T", "", "Full Participation in Practice", ""),
        ("Quincy Riley", "CB", "", "Full Participation in Practice", ""),
    ]),
    ("HOU", [
        ("Azeez Al-Shaair", "LB", "Groin, Not injury related - personal matter", "Did Not Participate In Practice", "Out"),
        ("Will Anderson Jr.", "DE", "Ankle", "Did Not Participate In Practice", "Questionable"),
        ("Reed Blankenship", "S", "", "Full Participation in Practice", ""),
        ("Trent Brown", "T", "Wrist, Illness", "Did Not Participate In Practice", "Questionable"),
        ("Tank Dell", "WR", "", "Full Participation in Practice", ""),
        ("Blake Fisher", "T", "", "Full Participation in Practice", ""),
        ("Marvin Harrison Jr.", "WR", "Hamstring", "Did Not Participate In Practice", "Out"),
        ("Jacob Hummel", "LB", "Groin", "Full Participation in Practice", "Questionable"),
        ("Danielle Hunter", "DE", "Hamstring", "Did Not Participate In Practice", "Out"),
        ("Brevin Jordan", "TE", "Finger, Foot", "Did Not Participate In Practice", "Out"),
        ("Woody Marks", "RB", "", "Full Participation in Practice", ""),
        ("David Montgomery", "RB", "Groin", "Full Participation in Practice", "Questionable"),
        ("Keylan Rutledge", "G", "Neck, Shoulder", "Did Not Participate In Practice", "Out"),
        ("Jaylin Smith", "CB", "Hamstring", "Full Participation in Practice", "Questionable"),
        ("Wyatt Teller", "G", "Illness, Back", "Limited Participation in Practice", "Questionable"),
        ("Tommy Togiai", "DT", "", "Full Participation in Practice", ""),
    ]),
    ("CLE", [
        ("Austin Barber", "T", "", "Full Participation in Practice", ""),
        ("Denzel Boston", "WR", "Toe", "Limited Participation in Practice", "Questionable"),
        ("Michael Burton", "FB", "Calf", "Did Not Participate In Practice", "Out"),
        ("Maliek Collins", "DT", "", "Full Participation in Practice", ""),
        ("Harold Fannin Jr.", "TE", "", "Full Participation in Practice", ""),
        ("Ronnie Hickman Jr.", "S", "Concussion", "Did Not Participate In Practice", "Out"),
        ("Tytus Howard", "T", "", "Full Participation in Practice", ""),
        ("Elgton Jenkins", "C", "", "Full Participation in Practice", ""),
        ("Donovan McMillon", "S", "", "Limited Participation in Practice", ""),
        ("Carson Schwesinger", "LB", "", "Full Participation in Practice", ""),
        ("Denzel Ward", "CB", "", "Limited Participation in Practice", ""),
        ("Quincy Williams", "LB", "", "Full Participation in Practice", ""),
    ]),
    ("LAR", [
        ("Davis Allen", "TE", "Oblique", "Limited Participation in Practice", "Questionable"),
        ("Steve Avila", "G", "Hamstring", "Did Not Participate In Practice", "Out"),
        ("Joe Cardona", "LS", "Ankle", "Limited Participation in Practice", "Questionable"),
        ("Kam Curl", "S", "Toe", "Limited Participation in Practice", "Questionable"),
        ("Aaron Donald", "DT", "", "Did Not Participate In Practice", ""),
        ("Terrance Ferguson", "TE", "Ankle, Hamstring", "Did Not Participate In Practice", "Out"),
        ("Braden Fiske", "DT", "", "Did Not Participate In Practice", ""),
        ("Myles Garrett", "LB", "Knee, Not injury related - resting player", "Did Not Participate In Practice", "Questionable"),
        ("Tyler Higbee", "TE", "", "Limited Participation in Practice", ""),
        ("Trent McDuffie", "CB", "Back", "Limited Participation in Practice", "Questionable"),
        ("Puka Nacua", "WR", "", "Did Not Participate In Practice", ""),
        ("Colby Parkinson", "TE", "", "Full Participation in Practice", ""),
        ("Matthew Stafford", "QB", "", "Full Participation in Practice", ""),
        ("Byron Young", "LB", "", "Did Not Participate In Practice", ""),
    ]),
    ("AZ", [
        ("Budda Baker", "S", "", "Full Participation in Practice", ""),
        ("Zachary Carter", "DT", "Knee", "Limited Participation in Practice", "Out"),
        ("Hjalte Froholdt", "C", "Concussion", "Did Not Participate In Practice", "Out"),
        ("Jon Gaines II", "G", "Ankle", "Did Not Participate In Practice", "Out"),
        ("Bam Knight", "RB", "", "Full Participation in Practice", ""),
        ("Hunter Long", "TE", "Knee", "Limited Participation in Practice", "Questionable"),
        ("Roy Lopez", "DT", "Toe, Ankle", "Limited Participation in Practice", "Questionable"),
        ("Max Melton", "CB", "Knee, Hand", "Limited Participation in Practice", "Questionable"),
        ("Darius Robinson", "DT", "Wrist", "Limited Participation in Practice", "Questionable"),
        ("Isaac Seumalo", "G", "", "Full Participation in Practice", ""),
        ("Dante Stills", "DT", "", "Full Participation in Practice", ""),
        ("Josh Sweat", "LB", "", "Full Participation in Practice", ""),
        ("Jayden Williams", "T", "Knee", "Limited Participation in Practice", "Questionable"),
        ("Mack Wilson", "LB", "", "Full Participation in Practice", ""),
        ("Andrew Wingard", "S", "Groin", "Did Not Participate In Practice", "Questionable"),
    ]),
    ("SEA", [
        ("AJ Barner", "TE", "", "Full Participation in Practice", ""),
        ("Anthony Bradford", "G", "", "Full Participation in Practice", ""),
        ("Charles Cross", "T", "Ankle", "Did Not Participate In Practice", "Out"),
        ("Sam Darnold", "QB", "Ribs, Quadricep", "Did Not Participate In Practice", "Out"),
        ("Derick Hall", "LB", "", "Did Not Participate In Practice", ""),
        ("Drew Lock", "QB", "", "Limited Participation in Practice", ""),
        ("Quenton Nelson", "G", "Knee", "Did Not Participate In Practice", "Out"),
        ("Uchenna Nwosu", "LB", "", "Full Participation in Practice", ""),
        ("Patrick O'Connell", "LB", "", "Full Participation in Practice", ""),
        ("Connor O'Toole", "LB", "", "Full Participation in Practice", ""),
        ("Brandon Pili", "DT", "", "Full Participation in Practice", ""),
        ("Jarran Reed", "DT", "", "Full Participation in Practice", ""),
        ("Rashid Shaheed", "WR", "", "Full Participation in Practice", ""),
        ("Jaxon Smith-Njigba", "WR", "", "Full Participation in Practice", ""),
        ("Leonard Williams", "DT", "Stinger", "Did Not Participate In Practice", "Out"),
    ]),
    ("LV", [
        ("Thomas Booker", "DT", "Ankle", "Full Participation in Practice", "Questionable"),
        ("Foley Fatukasi", "DT", "", "Full Participation in Practice", ""),
        ("Ian Thomas", "TE", "", "Full Participation in Practice", ""),
        ("Dont'e Thornton Jr.", "WR", "Back", "Did Not Participate In Practice", "Questionable"),
        ("Trey Zuhn III", "C", "", "Full Participation in Practice", ""),
    ]),
    ("SF", [
        ("Mike Evans", "WR", "Achilles", "Did Not Participate In Practice", "Out"),
        ("Renardo Green", "CB", "Back", "Limited Participation in Practice", "Questionable"),
        ("Dre Greenlaw", "LB", "Knee", "Limited Participation in Practice", "Questionable"),
        ("Nate Hobbs", "CB", "Groin", "Full Participation in Practice", "Questionable"),
        ("Deommodore Lenoir", "CB", "Foot", "Limited Participation in Practice", "Questionable"),
        ("Christian McCaffrey", "RB", "", "Full Participation in Practice", ""),
        ("Siran Neal", "S", "", "Full Participation in Practice", ""),
        ("Demarcus Robinson", "WR", "", "Full Participation in Practice", ""),
        ("Deebo Samuel Sr.", "WR", "", "Full Participation in Practice", ""),
        ("Upton Stout", "CB", "Shoulder, Neck", "Limited Participation in Practice", "Questionable"),
        ("C.J. West", "DT", "Knee", "Full Participation in Practice", "Questionable"),
        ("Trent Williams", "T", "Shoulder", "Did Not Participate In Practice", "Questionable"),
    ]),
    ("DAL", [
        ("DaRon Bland", "CB", "Ankle", "Limited Participation in Practice", "Questionable"),
        ("Jonathan Bullard", "DT", "Calf", "Full Participation in Practice", "Questionable"),
        ("Alijah Clark", "S", "Illness", "Did Not Participate In Practice", "Questionable"),
        ("Donovan Ezeiruaku", "LB", "Ankle", "Did Not Participate In Practice", "Out"),
        ("Jake Ferguson", "TE", "Knee, Ankle", "Did Not Participate In Practice", "Out"),
        ("Tyler Goodson", "RB", "Ankle, Knee", "Did Not Participate In Practice", "Out"),
        ("Malik Hooker", "S", "", "Did Not Participate In Practice", ""),
        ("Marist Liufau", "LB", "", "Full Participation in Practice", ""),
        ("P.J. Locke", "S", "Concussion", "Did Not Participate In Practice", "Out"),
        ("Von Miller", "LB", "", "Did Not Participate In Practice", ""),
        ("Jonathan Mingo", "WR", "Ankle", "Did Not Participate In Practice", "Out"),
        ("Devin Moore", "CB", "Hip", "Full Participation in Practice", "Questionable"),
        ("DeMarvion Overshown", "LB", "", "Full Participation in Practice", ""),
        ("George Pickens", "WR", "", "Full Participation in Practice", ""),
        ("Joey Porter Jr.", "CB", "Ankle, Foot", "Limited Participation in Practice", "Questionable"),
        ("Luke Schoonmaker", "TE", "", "Full Participation in Practice", ""),
        ("Brevyn Spann-Ford", "TE", "", "Full Participation in Practice", ""),
        ("Juanyeh Thomas", "S", "Hamstring", "Did Not Participate In Practice", "Doubtful"),
        ("KaVontae Turpin", "WR", "", "Full Participation in Practice", ""),
    ]),
    ("PIT", [
        ("Brandin Echols", "CB", "", "Full Participation in Practice", ""),
        ("DeShon Elliott", "S", "", "Full Participation in Practice", ""),
        ("Derrick Harmon", "DT", "Foot", "Full Participation in Practice", "Questionable"),
        ("Cameron Heyward", "DT", "", "Full Participation in Practice", ""),
        ("Ben Skowronek", "WR", "", "Full Participation in Practice", ""),
        ("Doneiko Slaughter", "CB", "", "Full Participation in Practice", ""),
        ("Darnell Washington", "TE", "", "Full Participation in Practice", ""),
        ("T.J. Watt", "LB", "", "Full Participation in Practice", ""),
    ]),
    ("CIN", [
        ("Jonathan Allen", "DT", "", "Limited Participation in Practice", ""),
        ("Jalen Davis", "CB", "Hamstring", "Full Participation in Practice", "Doubtful"),
        ("Kyle Dugger", "S", "Quadricep", "Did Not Participate In Practice", "Out"),
        ("Dylan Fairchild", "G", "", "Full Participation in Practice", ""),
        ("B.J. Hill", "DT", "", "Did Not Participate In Practice", ""),
        ("Andrei Iosivas", "WR", "Thumb", "Full Participation in Practice", "Doubtful"),
        ("Dexter Lawrence", "DT", "", "Did Not Participate In Practice", ""),
        ("Brian Parker II", "G", "Knee", "Full Participation in Practice", "Doubtful"),
        ("DJ Turner II", "CB", "", "Full Participation in Practice", ""),
    ]),
    ("LAC", [
        ("Kayode Awosika", "G", "Fibula", "Full Participation in Practice", "Questionable"),
        ("Bud Dupree", "DE", "", "Full Participation in Practice", ""),
        ("Justin Eboigbe", "DE", "Ankle", "Limited Participation in Practice", "Questionable"),
        ("Alex Harkey", "G", "", "Full Participation in Practice", ""),
        ("Tre Harris", "WR", "", "Full Participation in Practice", ""),
        ("Cam Hart", "CB", "", "Full Participation in Practice", ""),
        ("Daiyan Henley", "LB", "", "Full Participation in Practice", ""),
        ("Deane Leonard", "CB", "", "Full Participation in Practice", ""),
        ("Khalil Mack", "LB", "", "Full Participation in Practice", ""),
        ("Ladd McConkey", "WR", "Back", "Did Not Participate In Practice", "Questionable"),
        ("Keaton Mitchell", "RB", "", "Full Participation in Practice", ""),
        ("David Njoku", "TE", "Fibula", "Full Participation in Practice", "Questionable"),
        ("Denzel Perryman", "LB", "Pectoral", "Full Participation in Practice", "Questionable"),
        ("Trey Pipkins", "T", "Not injury related - personal matter, Knee", "Limited Participation in Practice", "Questionable"),
        ("Rodney Shelley", "CB", "", "Full Participation in Practice", ""),
        ("Branson Taylor", "G", "Ankle", "Did Not Participate In Practice", "Out"),
        ("Brenen Thompson", "WR", "Hamstring", "Did Not Participate In Practice", "Doubtful"),
        ("Isas Waxter", "CB", "Ankle", "Did Not Participate In Practice", "Out"),
        ("Kendall Williamson", "S", "Calf", "Did Not Participate In Practice", "Out"),
    ]),
    ("BAL", [
        ("Rasheen Ali", "RB", "", "Full Participation in Practice", ""),
        ("Rashod Bateman", "WR", "", "Full Participation in Practice", ""),
        ("Calais Campbell", "DT", "", "Did Not Participate In Practice", ""),
        ("Kyle Hamilton", "S", "", "Full Participation in Practice", ""),
        ("Jaylinn Hawkins", "S", "Knee", "Limited Participation in Practice", "Out"),
        ("Matthew Hibner", "TE", "", "Full Participation in Practice", ""),
        ("Olaivavega Ioane", "G", "", "Full Participation in Practice", ""),
        ("Adam Randall", "RB", "Neck, Hamstring", "Full Participation in Practice", "Questionable"),
        ("Ronnie Stanley", "T", "", "Did Not Participate In Practice", ""),
        ("Nate Wiggins", "CB", "", "Full Participation in Practice", ""),
    ]),
]

PAGE_TITLE_INJ = "Official NFL Injury Report for Players - Week 10 of the 2026 Season | NFL.com"
PAGE_TITLE_STAND = "2026 NFL League Standings"
PAGE_TITLE_SCORES = "NFL 2026 Week 10 Scores and Highlights: Live Updates, Results & Recaps"
PAGE_TITLE_GAME = "Minnesota Vikings at San Francisco 49ers 2026 REG 11 - Game Center"


def write_extract(name, lines):
    path = os.path.join(RAW, name)
    os.makedirs(RAW, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for ln in lines:
            f.write(ln + "\n")
    return path


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    read_utc = now_utc()
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(LEADS, exist_ok=True)
    extracts = {}

    # ---- standings extract (verbatim cell sequences)
    lines = [f"# extract: {STANDINGS_URL}", f"# page_title: {PAGE_TITLE_STAND}", f"# chunks_fetched: 2", f"# read_utc: {read_utc}", ""]
    for r in STANDINGS_ROWS:
        lines.append(" | ".join(r))
    write_extract("standings_2026-11-18.txt", lines)
    extracts["standings"] = {"url": STANDINGS_URL, "chunks": 2, "rows": len(STANDINGS_ROWS), "file": "raw/standings_2026-11-18.txt"}

    # ---- week-10 scores extract
    lines = [f"# extract: {SCORES_URL}", f"# page_title: {PAGE_TITLE_SCORES}", f"# chunks_fetched: 2", f"# read_utc: {read_utc}", ""]
    for g in RESULTS_WK10:
        lines.append(" | ".join(str(x) for x in g))
    lines.append("")
    lines.append("TEAMS_ON_BYE_PRINTED | " + ", ".join(WEEK10_BYES_PRINTED))
    write_extract("scores_wk10_2026-11-18.txt", lines)
    extracts["scores_wk10"] = {"url": SCORES_URL, "chunks": 2, "rows": len(RESULTS_WK10), "file": "raw/scores_wk10_2026-11-18.txt"}

    # ---- injuries extract (all 28 team tables, verbatim cell sequences)
    lines = [f"# extract: {INJ_URL}", f"# final_url_served: {INJ_FINAL_URL}",
             f"# page_title: {PAGE_TITLE_INJ}", f"# chunks_fetched: 8", f"# read_utc: {read_utc}",
             "# note: reg11 was requested; the page served Week 10 content (title 'Week 10').",
             ""]
    n_rows = 0
    for team, players in INJURIES:
        lines.append(f"## {team}")
        for p in players:
            lines.append(" | ".join(p))
            n_rows += 1
    write_extract("injuries_reg11_request_2026-11-18.txt", lines)
    extracts["injuries"] = {"url": INJ_URL, "served_url": INJ_FINAL_URL, "chunks": 8,
                            "rows": n_rows, "file": "raw/injuries_reg11_request_2026-11-18.txt"}

    # ---- game-centre extract (MIN@SF venue)
    lines = [f"# extract: {GAME_URL}", f"# page_title: {PAGE_TITLE_GAME}", f"# chunks_fetched: 1", f"# read_utc: {read_utc}", ""]
    for k, v in MIN_SF_GAME_CENTRE["printed"].items():
        lines.append(f"{k} | {v}")
    write_extract("game_vikings_at_49ers_2026-11-18.txt", lines)
    extracts["game_min_sf"] = {"url": GAME_URL, "chunks": 1, "file": "raw/game_vikings_at_49ers_2026-11-18.txt"}

    # ---- SHA256SUMS over the extracts
    sums_path = os.path.join(RAW, "SHA256SUMS.txt")
    with open(sums_path, "w", encoding="utf-8", newline="\n") as f:
        for name in sorted(os.listdir(RAW)):
            if name == "SHA256SUMS.txt" or name == "MANIFEST.json":
                continue
            f.write(f"{sha256_of(os.path.join(RAW, name))}  {name}\n")

    # ---- manifest
    manifest = {
        "session": "6cbf25fa",
        "claim_commit": "a3624df88a671dd91f1d64c92e8cba16d64bdafb",
        "claim_commit_utc": CLAIM_COMMIT_UTC,
        "read_utc_file_written": read_utc,
        "fetch_bound": "all fetches occurred after the claim commit timestamp and before this file's write time",
        "tool": "sandbox page-fetch tool (processed page text; server bytes not retained)",
        "extracts": extracts,
        "hash_scope_flag": "SHA256SUMS covers the extract files written by this capture, not the NFL.com server bytes (see flagged.csv F-P09).",
    }
    with open(os.path.join(RAW, "MANIFEST.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    # ---- parsed capture CSVs
    with open(os.path.join(DATA, "results_week10.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["game_slug", "away_team", "home_team", "away_score", "home_score",
                    "printed_section", "neutral_site", "source_url", "read_utc"])
        for slug, a, h, as_, hs, sec, neu in RESULTS_WK10:
            w.writerow([slug, a, h, as_, hs, sec, neu,
                        f"https://www.nfl.com/games/{slug}", read_utc])

    with open(os.path.join(DATA, "standings_2026-11-18.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["team_name", "team_code", "raw_cells_as_printed", "source_url", "read_utc"])
        for r in STANDINGS_ROWS:
            w.writerow([r[0], r[1], " | ".join(r[2:]), STANDINGS_URL, read_utc])

    cap_path = os.path.join(LEADS, "capture_injuries_2026-11-18.csv")
    with open(cap_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["team_code", "player", "position", "injuries", "practice_status",
                    "game_status", "source_url", "requested_url", "read_utc"])
        for team, players in INJURIES:
            for p in players:
                w.writerow([team, p[0], p[1], p[2], p[3], p[4], INJ_FINAL_URL, INJ_URL, read_utc])

    gc_path = os.path.join(DATA, "game_centre_min_sf_2026-11-18.csv")
    with open(gc_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["game_slug", "away_team", "home_team", "field", "value_as_printed", "source_url", "read_utc"])
        for k, v in MIN_SF_GAME_CENTRE["printed"].items():
            w.writerow([MIN_SF_GAME_CENTRE["slug"], "MIN", "SF", k, v, GAME_URL, read_utc])

    print(f"captured: standings=32 rows, wk10 finals=14, injury rows={n_rows}, extracts hashed")
    print(f"read_utc (write time) = {read_utc}")


if __name__ == "__main__":
    sys.exit(main())

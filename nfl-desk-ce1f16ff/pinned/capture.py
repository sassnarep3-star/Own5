"""Pinned verbatim captures used by this desk, with their provenance.

RULE: nothing in this file is inferred, modelled, estimated or filled in. Every
value was read by a human agent on the recorded date from the recorded URL and
transcribed exactly as displayed. Where a value was not visible on the page the
entry is ``None`` and a reason is recorded; the build never substitutes a
number for a blank.

Captures
--------
CAP-01  https://www.nfl.com/standings/                      2026-11-14T21:36Z  32 clubs
CAP-02  https://www.nfl.com/schedules/2026/by-week/week-10   2026-11-14T21:36Z  14 games + byes
CAP-03  https://www.espn.com/nfl/odds/_/date/20261115        2026-11-14T21:44Z  DraftKings lines
CAP-04  https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20261116
        2026-11-14T21:44Z                                     API cross-check, 1 game
CAP-05  https://www.espn.com/nfl/odds/_/gameId/401873064      2026-11-14T21:44Z  prop demo
CAP-06  https://www.nfl.com/schedules/2026/by-week/week-11    2026-11-14T21:33Z  Week 11 slate

Third-party mirrors already pinned in this repository (read-only, digests
recorded in ``data/input_register.csv`` by ``inputs.py``):

  data/decision-desk/raw/games.csv.gz        nflverse "games" release asset
  data/decision-desk/raw/injuries_2026.csv.gz
  data/decision-desk/raw/snap_counts_2026.csv.gz (+2025, 2024)
  data/raw/spreadspoke_scores.csv            tobycrabtree/spreadspoke @ 1d309cb

Those mirrors are labelled AGGREGATOR / THIRD-PARTY everywhere they are used and
are never presented as officially sourced values.
"""
from __future__ import annotations

SESSION = "ce1f16ff"
CAPTURE_UTC = "2026-11-14"          # date of every pinned capture below
CAPTURE_STAMPS = {
    "CAP-01": "2026-11-14T21:36Z",
    "CAP-02": "2026-11-14T21:36Z",
    "CAP-03": "2026-11-14T21:44Z",
    "CAP-04": "2026-11-14T21:44Z",
    "CAP-05": "2026-11-14T21:44Z",
    "CAP-06": "2026-11-14T21:33Z",
}
URLS = {
    "CAP-01": "https://www.nfl.com/standings/",
    "CAP-02": "https://www.nfl.com/schedules/2026/by-week/week-10",
    "CAP-03": "https://www.espn.com/nfl/odds/_/date/20261115",
    "CAP-04": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20261116",
    "CAP-05": "https://www.espn.com/nfl/odds/_/gameId/401873064",
    "CAP-06": "https://www.nfl.com/schedules/2026/by-week/week-11",
}
PROVIDER = "DraftKings Sportsbook (page attribution: \"Odds by draftkings\")"
PROVIDER_KEY = "DRAFTKINGS_VIA_ESPN"

# ---------------------------------------------------------------------------
# CAP-01  official 2026 standings, transcribed from the division view
# ---------------------------------------------------------------------------
# Column order read off the page: W | L | T | PCT | PF | PA | NET. The mapping
# is *not* assumed: `results_feed.py` asserts PF - PA == NET and PCT == W/(W+L+T/2)
# style consistency for all 32 rows, which pins the column identification.
STANDINGS = [
    # team, club, conf, div, W, L, T, PCT, PF, PA, NET
    ("BUF", "Buffalo Bills", "AFC", "East", 7, 1, 0, "0.875", 256, 187, 69),
    ("NE", "New England Patriots", "AFC", "East", 5, 4, 0, "0.556", 211, 207, 4),
    ("NYJ", "New York Jets", "AFC", "East", 2, 7, 0, "0.222", 182, 223, -41),
    ("MIA", "Miami Dolphins", "AFC", "East", 1, 7, 0, "0.125", 126, 200, -74),
    ("PIT", "Pittsburgh Steelers", "AFC", "North", 6, 2, 0, "0.750", 180, 144, 36),
    ("CIN", "Cincinnati Bengals", "AFC", "North", 6, 2, 0, "0.750", 240, 175, 65),
    ("CLE", "Cleveland Browns", "AFC", "North", 5, 4, 0, "0.556", 161, 196, -35),
    ("BAL", "Baltimore Ravens", "AFC", "North", 4, 5, 0, "0.444", 189, 236, -47),
    ("JAX", "Jacksonville Jaguars", "AFC", "South", 6, 2, 0, "0.750", 229, 121, 108),
    ("HOU", "Houston Texans", "AFC", "South", 3, 5, 0, "0.375", 209, 192, 17),
    ("IND", "Indianapolis Colts", "AFC", "South", 2, 7, 0, "0.222", 184, 249, -65),
    ("TEN", "Tennessee Titans", "AFC", "South", 1, 7, 0, "0.125", 144, 199, -55),
    ("DEN", "Denver Broncos", "AFC", "West", 7, 2, 0, "0.778", 198, 186, 12),
    ("KC", "Kansas City Chiefs", "AFC", "West", 6, 2, 0, "0.750", 202, 143, 59),
    ("LV", "Las Vegas Raiders", "AFC", "West", 4, 5, 0, "0.444", 238, 268, -30),
    ("LAC", "Los Angeles Chargers", "AFC", "West", 0, 8, 0, "0.000", 121, 219, -98),
    ("NYG", "New York Giants", "NFC", "East", 5, 3, 1, "0.611", 203, 196, 7),
    ("DAL", "Dallas Cowboys", "NFC", "East", 4, 5, 0, "0.444", 246, 236, 10),
    ("WAS", "Washington Commanders", "NFC", "East", 3, 5, 1, "0.389", 196, 223, -27),
    ("PHI", "Philadelphia Eagles", "NFC", "East", 2, 7, 0, "0.222", 148, 221, -73),
    ("CHI", "Chicago Bears", "NFC", "North", 7, 2, 0, "0.778", 241, 184, 57),
    ("DET", "Detroit Lions", "NFC", "North", 6, 2, 0, "0.750", 222, 189, 33),
    ("MIN", "Minnesota Vikings", "NFC", "North", 6, 2, 0, "0.750", 146, 116, 30),
    ("GB", "Green Bay Packers", "NFC", "North", 6, 3, 0, "0.667", 216, 191, 25),
    ("CAR", "Carolina Panthers", "NFC", "South", 3, 5, 0, "0.375", 199, 219, -20),
    ("NO", "New Orleans Saints", "NFC", "South", 3, 5, 0, "0.375", 185, 216, -31),
    ("TB", "Tampa Bay Buccaneers", "NFC", "South", 3, 6, 0, "0.333", 202, 178, 24),
    ("ATL", "Atlanta Falcons", "NFC", "South", 3, 6, 0, "0.333", 188, 223, -35),
    ("SF", "San Francisco 49ers", "NFC", "West", 7, 1, 0, "0.875", 235, 156, 79),
    ("SEA", "Seattle Seahawks", "NFC", "West", 5, 4, 0, "0.556", 202, 162, 40),
    ("LAR", "Los Angeles Rams", "NFC", "West", 5, 4, 0, "0.556", 214, 181, 33),
    ("ARI", "Arizona Cardinals", "NFC", "West", 3, 6, 0, "0.333", 178, 255, -77),
]
# The standings page renders the Rams as "LA" and the Cardinals as "AZ"; the
# abbreviations above are the internal keys this desk uses (matching the
# injury-report and depth-chart files). See flag MK-F-04.
STANDINGS_PAGE_ABBREV = {"LAR": "LA", "ARI": "AZ"}

# ---------------------------------------------------------------------------
# CAP-02 / CAP-06  official slate: game key, week, date, kickoff (local as
# displayed), broadcast, away, home, neutral, official game-page URL,
# final score if one had been played at capture time.
# ---------------------------------------------------------------------------
SLATE = [
    # week, date, time_displayed, broadcast, away, home, neutral, official_url, final
    (10, "2026-11-12", "Thursday, November 12th", "Prime", "WAS", "NYG", False,
     "https://www.nfl.com/games/commanders-at-giants-2026-reg-10", "24-21"),
    (10, "2026-11-15", "Sunday, November 15th, 9:30 AM", "FOX", "NE", "DET", True,
     "https://www.nfl.com/games/patriots-at-lions-2026-reg-10", None),
    (10, "2026-11-15", "Sunday, November 15th, 1:00 PM", "CBS", "KC", "ATL", False,
     "https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10", None),
    (10, "2026-11-15", "Sunday, November 15th, 1:00 PM", "FOX", "HOU", "CLE", False,
     "https://www.nfl.com/games/texans-at-browns-2026-reg-10", None),
    (10, "2026-11-15", "Sunday, November 15th, 1:00 PM", "FOX", "MIN", "GB", False,
     "https://www.nfl.com/games/vikings-at-packers-2026-reg-10", None),
    (10, "2026-11-15", "Sunday, November 15th, 1:00 PM", "CBS", "MIA", "IND", False,
     "https://www.nfl.com/games/dolphins-at-colts-2026-reg-10", None),
    (10, "2026-11-15", "Sunday, November 15th, 1:00 PM", "FOX", "CAR", "NO", False,
     "https://www.nfl.com/games/panthers-at-saints-2026-reg-10", None),
    (10, "2026-11-15", "Sunday, November 15th, 1:00 PM", "CBS", "BUF", "NYJ", False,
     "https://www.nfl.com/games/bills-at-jets-2026-reg-10", None),
    (10, "2026-11-15", "Sunday, November 15th, 1:00 PM", "FOX", "JAX", "TEN", False,
     "https://www.nfl.com/games/jaguars-at-titans-2026-reg-10", None),
    (10, "2026-11-15", "Sunday, November 15th, 4:05 PM", "CBS", "LAR", "ARI", False,
     "https://www.nfl.com/games/rams-at-cardinals-2026-reg-10", None),
    (10, "2026-11-15", "Sunday, November 15th, 4:05 PM", "CBS", "SEA", "LV", False,
     "https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10", None),
    (10, "2026-11-15", "Sunday, November 15th, 4:25 PM", "FOX", "SF", "DAL", False,
     "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10", None),
    (10, "2026-11-15", "Sunday, November 15th, 8:20 PM", "NBC", "PIT", "CIN", False,
     "https://www.nfl.com/games/steelers-at-bengals-2026-reg-10", None),
    (10, "2026-11-16", "Monday, November 16th, 8:15 PM", "ESPN", "LAC", "BAL", False,
     "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10", None),
    (11, "2026-11-19", "Thursday, November 19th, 8:15 PM", "PRIME", "IND", "HOU", False,
     "https://www.nfl.com/games/colts-at-texans-2026-reg-11", None),
]
BYES_WEEK_10 = [
    ("CHI", "7-2"), ("DEN", "7-2"), ("PHI", "2-7"), ("TB", "3-6"),
]
THURSDAY_FINAL_WAS_NYG = {"away": "WAS", "home": "NYG", "away_pts": 24, "home_pts": 21,
                         "line": "Commanders 24, Giants 21, FINAL, Thursday, November 12th",
                         "url": URLS["CAP-02"]}

# ---------------------------------------------------------------------------
# CAP-03  DraftKings lines as displayed on the ESPN odds page for the slate.
# `open_*` fields come from the page's "Open" column; the page shows the opening
# spread on the opening favourite's row and the opening total on the other row,
# both priced -110. The o/u prefix that the page attaches to the opening total is
# reproduced verbatim in `open_total_raw`; its convention is not stated by the
# source (flag MK-F-02, question MK-Q-02) so only the number is used.
# `cur_*` fields are the prices displayed at capture time: neither the opening
# price nor the closing price - they are labelled PRE_GAME.
# ---------------------------------------------------------------------------
PRICES = [
    # game, open_spread_home, open_total_raw, open_total,
    # away_spread, away_spread_price, home_spread, home_spread_price,
    # total, over_price, under_price, away_ml, home_ml
    dict(game="NE@DET", week=10, kickoff="2026-11-15T14:30Z", site="Munich (neutral)",
         open_spread_home=-1.5, open_total_raw="o48.5", open_total=48.5,
         away_spread=2.5, away_spread_price=-102, home_spread=-2.5, home_spread_price=-118,
         total=49.5, over_price=-112, under_price=-108, away_ml=124, home_ml=-148,
         away="NE", home="DET", neutral=True),
    dict(game="BUF@NYJ", week=10, kickoff="2026-11-15T18:00Z", site="",
         open_spread_home=7.0, open_total_raw="u46.5", open_total=46.5,
         away_spread=-7.5, away_spread_price=-112, home_spread=7.5, home_spread_price=-108,
         total=50.5, over_price=-115, under_price=-105, away_ml=-395, home_ml=310,
         away="BUF", home="NYJ", neutral=False),
    dict(game="CAR@NO", week=10, kickoff="2026-11-15T18:00Z", site="",
         open_spread_home=-1.5, open_total_raw="o43.5", open_total=43.5,
         away_spread=2.5, away_spread_price=-115, home_spread=-2.5, home_spread_price=-105,
         total=48.5, over_price=-115, under_price=-105, away_ml=114, home_ml=-135,
         away="CAR", home="NO", neutral=False),
    dict(game="HOU@CLE", week=10, kickoff="2026-11-15T18:00Z", site="",
         open_spread_home=4.5, open_total_raw="u38.5", open_total=38.5,
         away_spread=-4.5, away_spread_price=-108, home_spread=4.5, home_spread_price=-112,
         total=40.5, over_price=-108, under_price=-112, away_ml=-225, home_ml=185,
         away="HOU", home="CLE", neutral=False),
    dict(game="JAX@TEN", week=10, kickoff="2026-11-15T18:00Z", site="",
         open_spread_home=2.5, open_total_raw="u45.5", open_total=45.5,
         away_spread=-10.5, away_spread_price=-115, home_spread=10.5, home_spread_price=-105,
         total=46.5, over_price=-110, under_price=-110, away_ml=-700, home_ml=500,
         away="JAX", home="TEN", neutral=False),
    dict(game="KC@ATL", week=10, kickoff="2026-11-15T18:00Z", site="",
         open_spread_home=4.5, open_total_raw="u45.5", open_total=45.5,
         away_spread=-3.0, away_spread_price=-112, home_spread=3.0, home_spread_price=-108,
         total=47.5, over_price=-102, under_price=-118, away_ml=-166, home_ml=140,
         away="KC", home="ATL", neutral=False),
    dict(game="MIA@IND", week=10, kickoff="2026-11-15T18:00Z", site="",
         open_spread_home=6.5, open_total_raw="o47.5", open_total=47.5,
         away_spread=4.5, away_spread_price=-112, home_spread=-4.5, home_spread_price=-108,
         total=37.5, over_price=-110, under_price=-110, away_ml=180, home_ml=-218,
         away="MIA", home="IND", neutral=False),
    dict(game="MIN@GB", week=10, kickoff="2026-11-15T18:00Z", site="",
         open_spread_home=4.5, open_total_raw="o45.5", open_total=45.5,
         away_spread=2.5, away_spread_price=100, home_spread=-2.5, home_spread_price=-120,
         total=42.5, over_price=-105, under_price=-115, away_ml=124, home_ml=-148,
         away="MIN", home="GB", neutral=False),
    dict(game="LAR@ARI", week=10, kickoff="2026-11-15T22:05Z", site="",
         open_spread_home=10.5, open_total_raw="u47.5", open_total=47.5,
         away_spread=-9.5, away_spread_price=-112, home_spread=9.5, home_spread_price=-108,
         total=39.5, over_price=-108, under_price=-112, away_ml=-500, home_ml=380,
         away="LAR", home="ARI", neutral=False),
    dict(game="SEA@LV", week=10, kickoff="2026-11-15T22:05Z", site="",
         open_spread_home=7.0, open_total_raw="u43.5", open_total=43.5,
         away_spread=-6.5, away_spread_price=-112, home_spread=6.5, home_spread_price=-108,
         total=40.5, over_price=-112, under_price=-108, away_ml=-305, home_ml=245,
         away="SEA", home="LV", neutral=False),
    dict(game="SF@DAL", week=10, kickoff="2026-11-15T22:25Z", site="",
         open_spread_home=-1.5, open_total_raw="o52.5", open_total=52.5,
         away_spread=-3.5, away_spread_price=-115, home_spread=3.5, home_spread_price=-105,
         total=55.5, over_price=-118, under_price=-102, away_ml=-205, home_ml=170,
         away="SF", home="DAL", neutral=False),
    dict(game="PIT@CIN", week=10, kickoff="2026-11-16T01:20Z", site="",
         open_spread_home=-3.5, open_total_raw="o47.5", open_total=47.5,
         away_spread=3.5, away_spread_price=-112, home_spread=-3.5, home_spread_price=-108,
         total=49.5, over_price=-105, under_price=-115, away_ml=154, home_ml=-185,
         away="PIT", home="CIN", neutral=False),
    dict(game="LAC@BAL", week=10, kickoff="2026-11-17T01:15Z", site="",
         open_spread_home=-2.5, open_total_raw="o48.5", open_total=48.5,
         away_spread=4.5, away_spread_price=-112, home_spread=-4.5, home_spread_price=-108,
         total=38.5, over_price=-110, under_price=-110, away_ml=180, home_ml=-218,
         away="LAC", home="BAL", neutral=False),
    dict(game="IND@HOU", week=11, kickoff="2026-11-19T23:15Z", site="",
         open_spread_home=5.5, open_total_raw="o45.5", open_total=45.5,
         away_spread=10.0, away_spread_price=-110, home_spread=-10.0, home_spread_price=-110,
         total=44.5, over_price=-110, under_price=-110, away_ml=350, home_ml=-455,
         away="IND", home="HOU", neutral=False),
    dict(game="ARI@KC", week=11, kickoff="2026-11-22T18:00Z", site="",
         open_spread_home=11.5, open_total_raw="o44.5", open_total=44.5,
         away_spread=14.0, away_spread_price=-110, home_spread=-14.0, home_spread_price=-110,
         total=42.5, over_price=-105, under_price=-115, away_ml=625, home_ml=-950,
         away="ARI", home="KC", neutral=False),
    dict(game="BAL@CAR", week=11, kickoff="2026-11-22T18:00Z", site="",
         open_spread_home=-4.5, open_total_raw="u46.5", open_total=46.5,
         away_spread=1.5, away_spread_price=-110, home_spread=-1.5, home_spread_price=-110,
         total=44.5, over_price=-115, under_price=-105, away_ml=105, home_ml=None,
         away="BAL", home="CAR", neutral=False),
]
PRICE_NOTES = {
    "BAL@CAR": "home moneyline not transcribed: the rendered page chunk ended mid-row; left blank, not guessed",
    "MIA@IND": "open total 47.5 vs 37.5 at capture: a 10.0-point move, flagged MK-F-03 for second-source confirmation",
    "LAR@ARI": "open total 47.5 vs 39.5 at capture: an 8.0-point move, flagged MK-F-03 for second-source confirmation",
    "JAX@TEN": "open -2.5 vs -10.5 at capture: an 8.0-point side move, flagged MK-F-03",
    "IND@HOU": "open -5.5 vs -10.0 at capture: a 4.5-point side move (Week 11, 5 days out)",
}

# CAP-04  independent endpoint check for the same game, fetched seconds later.
API_CROSSCHECK = {
    "game": "LAC@BAL",
    "espn_event_id": "401873065",
    "provider_id": "100",
    "provider_name": "DraftKings",
    "details": "BAL -4.5",
    "overUnder": 38.5,
    "status": "STATUS_SCHEDULED / state=pre",
    "url": URLS["CAP-04"],
    "raw_snippet": ('"odds":[{"provider":{"id":"100","name":"DraftKings","priority":1,...},'
                    '"details":"BAL -4.5","overUnder":38.5,"spread":-4.5,...}'),
}

# CAP-05  prop-market capture, one game, to prove the store's schema carries props.
PROP_CAPTURE = [
    dict(game="PIT@CIN", market="player_prop", subject="Joe Burrow (CIN QB)",
         selection="38+ Passing Attempts Milestone", line=38.0, price=-120,
         section="Player Milestone Props > first tab as rendered (\"Passing Attempts Milestones\")",
         raw="[38+\\n\\n-120]"),
    dict(game="PIT@CIN", market="player_prop", subject="Aaron Rodgers (PIT QB)",
         selection="36+ Passing Attempts Milestone", line=36.0, price=-104,
         section="Player Milestone Props > first tab as rendered (\"Passing Attempts Milestones\")",
         raw="[36+\\n\\n-104]"),
    dict(game="PIT@CIN", market="player_prop", subject="Joe Burrow (CIN QB)",
         selection="Passing Yards Over 288.5", line=288.5, price=-111,
         section="Passing Props > Passing Yards",
         raw="[o288.5\\n\\n-111]"),
    dict(game="PIT@CIN", market="player_prop", subject="Joe Burrow (CIN QB)",
         selection="Passing Yards Under 288.5", line=288.5, price=-113,
         section="Passing Props > Passing Yards",
         raw="[u288.5\\n\\n-113]"),
]

# ---------------------------------------------------------------------------
# Sources register for the desk (rendered on sources.html).
# tier: OFFICIAL = published by the NFL or a club; OPERATOR = a licensed
# sportsbook price surfaced by its own site or a partner site; AGGREGATOR =
# re-publishes official data; THIRD-PARTY = community dataset.
# ---------------------------------------------------------------------------
SOURCES = [
    ("MK-S-01", "NFL.com", "2026 NFL standings (division view)", URLS["CAP-01"],
     "OFFICIAL", "W, L, T, PCT, PF, PA, NET for all 32 clubs through the Week 10 Thursday final",
     "verified - read directly; PF-PA==NET asserted for all 32 rows", CAPTURE_STAMPS["CAP-01"]),
    ("MK-S-02", "NFL.com", "2026 Week 10 schedule and results", URLS["CAP-02"],
     "OFFICIAL", "Week 10 slate, kickoff dates/times, broadcast, neutral-site marker, bye list, Thursday final",
     "verified - read directly; 14 games + 4 byes transcribed", CAPTURE_STAMPS["CAP-02"]),
    ("MK-S-03", "NFL.com", "2026 Week 11 schedule", URLS["CAP-06"],
     "OFFICIAL", "Confirmation that Week 10 is the live week and Week 11 opens 2026-11-19",
     "verified - read directly", CAPTURE_STAMPS["CAP-06"]),
    ("MK-S-04", "ESPN (prices attributed to DraftKings Sportsbook)",
     "NFL odds page for the 2026-11-15 slate", URLS["CAP-03"],
     "OPERATOR", "Opening and pre-game spread, total and moneyline for 16 games",
     "partially verified - transcribed verbatim; opening-total display convention unresolved (MK-F-02)",
     CAPTURE_STAMPS["CAP-03"]),
    ("MK-S-05", "ESPN site API", "Scoreboard JSON for 2026-11-16",
     "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=20261116",
     "OPERATOR", "Independent endpoint cross-check of the LAC@BAL side and total",
     "verified - agrees with the HTML capture on both fields", CAPTURE_STAMPS["CAP-04"]),
    ("MK-S-06", "ESPN (prices attributed to DraftKings Sportsbook)",
     "Game odds page, Pittsburgh at Cincinnati", URLS["CAP-05"],
     "OPERATOR", "Player-prop capture used to exercise the store's prop schema",
     "verbatim capture; tab identity inferred from page order (MK-F-05)", CAPTURE_STAMPS["CAP-05"]),
    ("MK-S-07", "nflverse", "games.csv.gz (2026 schedule, scores and market columns)",
     "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz",
     "AGGREGATOR", "Results feed history and the only source in-repo carrying prices for completed games",
     "digest verified against data/decision-desk/raw/provenance.json; upstream asset has since moved (MK-F-01)",
     "pinned 2026-11-12T16:52:39Z"),
    ("MK-S-08", "nflverse", "injuries_2026.csv.gz / injuries_2025 / injuries_2024",
     "https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_2026.csv.gz",
     "AGGREGATOR", "Weekly report_status and practice_status ladders used for availability base rates",
     "digest verified against provenance.json; 2026 Week-10 row count disagrees with the official page (MK-F-06)",
     "pinned 2026-11-12T16:52:39Z"),
    ("MK-S-09", "nflverse", "snap_counts_2026.csv.gz (plus 2025, 2024)",
     "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2026.csv.gz",
     "AGGREGATOR", "Whether a listed player actually took a snap; used to measure availability and depth used",
     "digest verified against provenance.json", "pinned 2026-11-12T16:52:39Z"),
    ("MK-S-10", "tobycrabtree/spreadspoke", "spreadspoke_scores.csv @ 1d309cb",
     "https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv",
     "THIRD-PARTY", "Cross-check that the repository copy of the dataset is the pinned upstream blob",
     "verified - git blob SHA of the committed file equals the upstream blob SHA",
     "pinned in-repo by session arena-f1d30421"),
    ("MK-S-11", "Session 864d5668 (vendored)", "Official Week 10 injury report transcription + club depth charts",
     "https://www.nfl.com/injuries/league/2026/reg10",
     "OFFICIAL (transcribed by another session)",
     "Depth-chart join for the replacement tracker",
     "vendored, not re-fetched by this session (MK-F-07); 326 report rows, 705 chart slots",
     "captured 2026-11-13"),
    ("MK-S-12", "GitHub REST API", "nflverse release asset metadata (digests)",
     "https://api.github.com/repos/nflverse/nflverse-data/releases/tags/schedules",
     "OFFICIAL (for file integrity)",
     "sha256 digest of the live release asset, compared with the pinned local copy",
     "verified - compared 2026-11-14; three assets differ because upstream republished",
     "2026-11-14T21:50Z"),
]

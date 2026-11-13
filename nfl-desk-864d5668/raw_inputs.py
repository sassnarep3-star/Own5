"""Pinned raw inputs for the Own5 NFL Own-Line Lab (session 864d5668).

Every value in this module was copied verbatim from an official source on
2026-11-13 UTC and carries the exact URL it came from. Nothing here is
inferred, modelled, estimated or filled in.

Source registry (see nfl-desk-864d5668/data/sources.csv for the rendered form):

  S-01  https://www.nfl.com/standings/                        32-team standings
        (fetched 2026-11-13; reflects all games through the Week 10 Thursday
         night final, WAS 24 @ NYG 21)
  S-02  https://www.nfl.com/schedules/2026/by-week/week-1     Week 1 finals
  S-03  .../week-2    Week 2 finals        S-04  .../week-3    Week 3 finals
  S-05  .../week-4    Week 4 finals        S-06  .../week-5    Week 5 finals
  S-07  .../week-6    Week 6 finals        S-08  .../week-7    Week 7 finals
  S-09  .../week-8    Week 8 finals        S-10  .../week-9    Week 9 finals
  S-11  .../week-10   Week 10 slate + Thursday-night final + byes
  S-12  https://www.nfl.com/injuries/league/2026/reg10        Official Week 10
        league-wide injury report (practice status / issued game status)
  S-13  https://operations.nfl.com/rules-officiating/2026-nfl-rulebook
  S-14  official club /team/depth-chart pages (one per club, listed per row)

Neutral-site games: the NFL played 2026 games in Melbourne, Rio de Janeiro,
London, Saint-Denis (Paris), Madrid and Munich. For those the schedule URL is
"<away>-at-<home>", i.e. the HOME column is the *nominal* home club, but the
game is not played at that club's stadium. `neutral` marks those rows and the
engine zeroes home-field advantage for them.
"""

from __future__ import annotations

FETCH_DATE = "2026-11-13"

# ---------------------------------------------------------------------------
# Teams (official abbreviations, nfl.com/standings/)
# ---------------------------------------------------------------------------
TEAMS = {
    "ARI": ("Arizona Cardinals", "NFC", "West"),
    "ATL": ("Atlanta Falcons", "NFC", "South"),
    "BAL": ("Baltimore Ravens", "AFC", "North"),
    "BUF": ("Buffalo Bills", "AFC", "East"),
    "CAR": ("Carolina Panthers", "NFC", "South"),
    "CHI": ("Chicago Bears", "NFC", "North"),
    "CIN": ("Cincinnati Bengals", "AFC", "North"),
    "CLE": ("Cleveland Browns", "AFC", "North"),
    "DAL": ("Dallas Cowboys", "NFC", "East"),
    "DEN": ("Denver Broncos", "AFC", "West"),
    "DET": ("Detroit Lions", "NFC", "North"),
    "GB": ("Green Bay Packers", "NFC", "North"),
    "HOU": ("Houston Texans", "AFC", "South"),
    "IND": ("Indianapolis Colts", "AFC", "South"),
    "JAX": ("Jacksonville Jaguars", "AFC", "South"),
    "KC": ("Kansas City Chiefs", "AFC", "West"),
    "LV": ("Las Vegas Raiders", "AFC", "West"),
    "LAC": ("Los Angeles Chargers", "AFC", "West"),
    "LAR": ("Los Angeles Rams", "NFC", "West"),
    "MIA": ("Miami Dolphins", "AFC", "East"),
    "MIN": ("Minnesota Vikings", "NFC", "North"),
    "NE": ("New England Patriots", "AFC", "East"),
    "NO": ("New Orleans Saints", "NFC", "South"),
    "NYG": ("New York Giants", "NFC", "East"),
    "NYJ": ("New York Jets", "AFC", "East"),
    "PHI": ("Philadelphia Eagles", "NFC", "East"),
    "PIT": ("Pittsburgh Steelers", "AFC", "North"),
    "SF": ("San Francisco 49ers", "NFC", "West"),
    "SEA": ("Seattle Seahawks", "NFC", "West"),
    "TB": ("Tampa Bay Buccaneers", "NFC", "South"),
    "TEN": ("Tennessee Titans", "AFC", "South"),
    "WAS": ("Washington Commanders", "NFC", "East"),
}

TEAM_URL = {abbr: "https://www.nfl.com/teams/%s/" % name.lower().replace(" ", "-")
            for abbr, (name, _c, _d) in TEAMS.items()}

# ---------------------------------------------------------------------------
# Official standings, nfl.com/standings/, fetched 2026-11-13 (S-01).
# Columns: W, L, T, PCT, PF, PA  (PF/PA are season totals through Week 10 TNF)
# ---------------------------------------------------------------------------
SRC_STANDINGS = "https://www.nfl.com/standings/"

STANDINGS = {
    # AFC East
    "BUF": (7, 1, 0, 0.875, 256, 187),
    "NE": (5, 4, 0, 0.556, 211, 207),
    "NYJ": (2, 7, 0, 0.222, 182, 223),
    "MIA": (1, 7, 0, 0.125, 126, 200),
    # AFC North
    "PIT": (6, 2, 0, 0.750, 180, 144),
    "CIN": (6, 2, 0, 0.750, 240, 175),
    "CLE": (5, 4, 0, 0.556, 161, 196),
    "BAL": (4, 5, 0, 0.444, 189, 236),
    # AFC South
    "JAX": (6, 2, 0, 0.750, 229, 121),
    "HOU": (3, 5, 0, 0.375, 209, 192),
    "IND": (2, 7, 0, 0.222, 184, 249),
    "TEN": (1, 7, 0, 0.125, 144, 199),
    # AFC West
    "DEN": (7, 2, 0, 0.778, 198, 186),
    "KC": (6, 2, 0, 0.750, 202, 143),
    "LV": (4, 5, 0, 0.444, 238, 268),
    "LAC": (0, 8, 0, 0.000, 121, 219),
    # NFC East
    "NYG": (5, 3, 1, 0.611, 203, 196),
    "DAL": (4, 5, 0, 0.444, 246, 236),
    "WAS": (3, 5, 1, 0.389, 196, 223),
    "PHI": (2, 7, 0, 0.222, 148, 221),
    # NFC North
    "CHI": (7, 2, 0, 0.778, 241, 184),
    "DET": (6, 2, 0, 0.750, 222, 189),
    "MIN": (6, 2, 0, 0.750, 146, 116),
    "GB": (6, 3, 0, 0.667, 216, 191),
    # NFC South
    "CAR": (3, 5, 0, 0.375, 199, 219),
    "NO": (3, 5, 0, 0.375, 185, 216),
    "TB": (3, 6, 0, 0.333, 202, 178),
    "ATL": (3, 6, 0, 0.333, 188, 223),
    # NFC West
    "SF": (7, 1, 0, 0.875, 235, 156),
    "SEA": (5, 4, 0, 0.556, 202, 162),
    "LAR": (5, 4, 0, 0.556, 214, 181),
    "ARI": (3, 6, 0, 0.333, 178, 255),
}

# ---------------------------------------------------------------------------
# Official game ledger.
# (week, away, home, away_pts, home_pts, date, neutral_site_label_or_None,
#  source_url)
# away_pts/home_pts is None for games that had not kicked off at fetch time.
# ---------------------------------------------------------------------------
W = "https://www.nfl.com/schedules/2026/by-week/week-%d"

LEDGER = [
    # ---------------------------- WEEK 1 -----------------------------------
    (1, "NE", "SEA", 10, 13, "2026-09-09", None),
    (1, "SF", "LAR", 27, 7, "2026-09-10", "Melbourne (East Melbourne 2026)"),
    (1, "CHI", "CAR", 59, 37, "2026-09-13", None),
    (1, "TB", "CIN", 27, 33, "2026-09-13", None),
    (1, "NO", "DET", 30, 31, "2026-09-13", None),
    (1, "BUF", "HOU", 36, 31, "2026-09-13", None),
    (1, "BAL", "IND", 41, 23, "2026-09-13", None),
    (1, "CLE", "JAX", 10, 34, "2026-09-13", None),
    (1, "ATL", "PIT", 13, 20, "2026-09-13", None),
    (1, "NYJ", "TEN", 23, 10, "2026-09-13", None),
    (1, "ARI", "LAC", 26, 14, "2026-09-13", None),
    (1, "MIA", "LV", 13, 27, "2026-09-13", None),
    (1, "GB", "MIN", 22, 39, "2026-09-13", None),
    (1, "WAS", "PHI", 22, 24, "2026-09-13", None),
    (1, "DAL", "NYG", 20, 28, "2026-09-13", None),
    (1, "DEN", "KC", 10, 31, "2026-09-14", None),
    # ---------------------------- WEEK 2 -----------------------------------
    (2, "DET", "BUF", 31, 41, "2026-09-17", None),
    (2, "CAR", "ATL", 34, 3, "2026-09-20", None),
    (2, "NO", "BAL", 24, 17, "2026-09-20", None),
    (2, "MIN", "CHI", 9, 3, "2026-09-20", None),
    (2, "CIN", "HOU", 20, 6, "2026-09-20", None),
    (2, "PIT", "NE", 3, 20, "2026-09-20", None),
    (2, "GB", "NYJ", 20, 17, "2026-09-20", None),
    (2, "CLE", "TB", 23, 19, "2026-09-20", None),
    (2, "PHI", "TEN", 24, 20, "2026-09-20", None),
    (2, "JAX", "DEN", 13, 20, "2026-09-20", None),
    (2, "LV", "LAC", 26, 14, "2026-09-20", None),
    (2, "SEA", "ARI", 31, 7, "2026-09-20", None),
    (2, "WAS", "DAL", 20, 37, "2026-09-20", None),
    (2, "MIA", "SF", 13, 35, "2026-09-20", None),
    (2, "IND", "KC", 30, 33, "2026-09-20", None),
    (2, "NYG", "LAR", 6, 28, "2026-09-21", None),
    # ---------------------------- WEEK 3 -----------------------------------
    (3, "ATL", "GB", 35, 14, "2026-09-24", None),
    (3, "LAC", "BUF", 16, 24, "2026-09-27", None),
    (3, "CAR", "CLE", 18, 21, "2026-09-27", None),
    (3, "NYJ", "DET", 24, 31, "2026-09-27", None),
    (3, "HOU", "IND", 17, 19, "2026-09-27", None),
    (3, "NE", "JAX", 6, 35, "2026-09-27", None),
    (3, "KC", "MIA", 24, 10, "2026-09-27", None),
    (3, "TEN", "NYG", 7, 12, "2026-09-27", None),
    (3, "CIN", "PIT", 27, 30, "2026-09-27", None),
    (3, "SEA", "WAS", 31, 33, "2026-09-27", None),
    (3, "ARI", "SF", 30, 36, "2026-09-27", None),
    (3, "MIN", "TB", 23, 16, "2026-09-27", None),
    (3, "LV", "NO", 35, 27, "2026-09-27", None),
    (3, "BAL", "DAL", 34, 31, "2026-09-27", "Rio de Janeiro 2026"),
    (3, "LAR", "DEN", 26, 30, "2026-09-27", None),
    (3, "PHI", "CHI", 7, 27, "2026-09-28", None),
    # ---------------------------- WEEK 4 -----------------------------------
    (4, "PIT", "CLE", 24, 27, "2026-10-01", None),
    (4, "IND", "WAS", 30, 13, "2026-10-04", "London 2026"),
    (4, "TEN", "BAL", 18, 24, "2026-10-04", None),
    (4, "NE", "BUF", 29, 26, "2026-10-04", None),
    (4, "NYJ", "CHI", 12, 23, "2026-10-04", None),
    (4, "JAX", "CIN", 22, 17, "2026-10-04", None),
    (4, "DAL", "HOU", 34, 30, "2026-10-04", None),
    (4, "ARI", "NYG", 24, 36, "2026-10-04", None),
    (4, "LAR", "PHI", 24, 20, "2026-10-04", None),
    (4, "GB", "TB", 17, 14, "2026-10-04", None),
    (4, "MIA", "MIN", 10, 15, "2026-10-04", None),
    (4, "KC", "LV", 30, 27, "2026-10-04", None),
    (4, "LAC", "SEA", 23, 30, "2026-10-04", None),
    (4, "DEN", "SF", 14, 24, "2026-10-04", None),
    (4, "DET", "CAR", 26, 32, "2026-10-04", None),
    (4, "ATL", "NO", 45, 24, "2026-10-05", None),
    # ---------------------------- WEEK 5 -----------------------------------
    (5, "TB", "DAL", 24, 16, "2026-10-08", None),
    (5, "PHI", "JAX", 17, 19, "2026-10-11", "London 2026"),
    (5, "CIN", "MIA", 31, 24, "2026-10-11", None),
    (5, "LV", "NE", 17, 45, "2026-10-11", None),
    (5, "MIN", "NO", 23, 13, "2026-10-11", None),
    (5, "CLE", "NYJ", 12, 17, "2026-10-11", None),
    (5, "IND", "PIT", 22, 34, "2026-10-11", None),
    (5, "HOU", "TEN", 26, 3, "2026-10-11", None),
    (5, "NYG", "WAS", 27, 27, "2026-10-11", None),
    (5, "CHI", "GB", 7, 31, "2026-10-11", None),
    (5, "DEN", "LAC", 23, 17, "2026-10-11", None),
    (5, "DET", "ARI", 45, 21, "2026-10-11", None),
    (5, "SF", "SEA", 32, 29, "2026-10-11", None),
    (5, "BAL", "ATL", 30, 23, "2026-10-11", None),
    (5, "BUF", "LAR", 37, 34, "2026-10-12", None),
    # ---------------------------- WEEK 6 -----------------------------------
    (6, "SEA", "DEN", 14, 17, "2026-10-15", None),
    (6, "HOU", "JAX", 34, 31, "2026-10-18", "London 2026"),
    (6, "CHI", "ATL", 31, 23, "2026-10-18", None),
    (6, "BAL", "CLE", 10, 13, "2026-10-18", None),
    (6, "TEN", "IND", 26, 20, "2026-10-18", None),
    (6, "NYJ", "NE", 19, 26, "2026-10-18", None),
    (6, "NO", "NYG", 34, 27, "2026-10-18", None),
    (6, "CAR", "PHI", 25, 14, "2026-10-18", None),
    (6, "PIT", "TB", 26, 19, "2026-10-18", None),
    (6, "ARI", "LAR", 18, 16, "2026-10-18", None),
    (6, "LAC", "KC", 6, 22, "2026-10-18", None),
    (6, "BUF", "LV", 33, 30, "2026-10-18", None),
    (6, "DAL", "GB", 13, 23, "2026-10-18", None),
    (6, "WAS", "SF", 17, 23, "2026-10-19", None),
    # ---------------------------- WEEK 7 -----------------------------------
    (7, "NE", "CHI", 24, 30, "2026-10-22", None),
    (7, "PIT", "NO", 16, 10, "2026-10-25", "Saint-Denis 2026"),
    (7, "SF", "ATL", 20, 29, "2026-10-25", None),
    (7, "CIN", "BAL", 35, 13, "2026-10-25", None),
    (7, "TB", "CAR", 43, 13, "2026-10-25", None),
    (7, "NYG", "HOU", 27, 21, "2026-10-25", None),
    (7, "IND", "MIN", 10, 16, "2026-10-25", None),
    (7, "MIA", "NYJ", 28, 25, "2026-10-25", None),
    (7, "CLE", "TEN", 27, 24, "2026-10-25", None),
    (7, "DEN", "ARI", 30, 16, "2026-10-25", None),
    (7, "GB", "DET", 17, 20, "2026-10-25", None),
    (7, "LAR", "LV", 35, 21, "2026-10-25", None),
    (7, "KC", "SEA", 3, 20, "2026-10-25", None),
    (7, "DAL", "PHI", 38, 21, "2026-10-26", None),
    # ---------------------------- WEEK 8 -----------------------------------
    (8, "CAR", "GB", 19, 27, "2026-10-29", None),
    (8, "BAL", "BUF", 10, 36, "2026-11-01", None),
    (8, "TEN", "CIN", 36, 43, "2026-11-01", None),
    (8, "ARI", "DAL", 33, 30, "2026-11-01", None),
    (8, "MIN", "DET", 15, 19, "2026-11-01", None),
    (8, "IND", "JAX", 7, 42, "2026-11-01", None),
    (8, "LV", "NYJ", 38, 33, "2026-11-01", None),
    (8, "CLE", "PIT", 6, 27, "2026-11-01", None),
    (8, "ATL", "TB", 0, 16, "2026-11-01", None),
    (8, "LAC", "LAR", 9, 24, "2026-11-01", None),
    (8, "KC", "DEN", 24, 28, "2026-11-01", None),
    (8, "NE", "MIA", 24, 19, "2026-11-01", None),
    (8, "PHI", "WAS", 10, 27, "2026-11-01", None),
    (8, "CHI", "SEA", 34, 17, "2026-11-02", None),
    # ---------------------------- WEEK 9 -----------------------------------
    (9, "JAX", "BAL", 33, 10, "2026-11-05", None),
    (9, "CIN", "ATL", 34, 17, "2026-11-08", "Madrid 2026"),
    (9, "DEN", "CAR", 26, 21, "2026-11-08", None),
    (9, "DAL", "IND", 27, 23, "2026-11-08", None),
    (9, "NYJ", "KC", 12, 35, "2026-11-08", None),
    (9, "DET", "MIA", 19, 9, "2026-11-08", None),
    (9, "CLE", "NO", 22, 23, "2026-11-08", None),
    (9, "NYG", "PHI", 19, 11, "2026-11-08", None),
    (9, "LAR", "WAS", 20, 13, "2026-11-08", None),
    (9, "HOU", "LAC", 44, 22, "2026-11-08", None),
    (9, "LV", "SF", 17, 38, "2026-11-08", None),
    (9, "GB", "NE", 45, 27, "2026-11-08", None),
    (9, "ARI", "SEA", 3, 17, "2026-11-08", None),
    (9, "TB", "CHI", 24, 27, "2026-11-08", None),
    (9, "BUF", "MIN", 23, 6, "2026-11-09", None),
    # ---------------------------- WEEK 10 ----------------------------------
    (10, "WAS", "NYG", 24, 21, "2026-11-12", None),
    (10, "NE", "DET", None, None, "2026-11-15", "Munich 2026"),
    (10, "KC", "ATL", None, None, "2026-11-15", None),
    (10, "HOU", "CLE", None, None, "2026-11-15", None),
    (10, "MIN", "GB", None, None, "2026-11-15", None),
    (10, "MIA", "IND", None, None, "2026-11-15", None),
    (10, "CAR", "NO", None, None, "2026-11-15", None),
    (10, "BUF", "NYJ", None, None, "2026-11-15", None),
    (10, "JAX", "TEN", None, None, "2026-11-15", None),
    (10, "LAR", "ARI", None, None, "2026-11-15", None),
    (10, "SEA", "LV", None, None, "2026-11-15", None),
    (10, "SF", "DAL", None, None, "2026-11-15", None),
    (10, "PIT", "CIN", None, None, "2026-11-15", None),
    (10, "LAC", "BAL", None, None, "2026-11-16", None),
]

LEDGER_SRC = {wk: W % wk for wk in range(1, 11)}

# ---------------------------------------------------------------------------
# Official bye weeks, read off the nfl.com by-week schedule pages.
# Only weeks that the league actually listed a "Teams on Bye" block are
# populated; every other week is an empty list (no byes were published).
# ---------------------------------------------------------------------------
BYES = {
    5: ["CAR", "KC"],
    6: ["CIN", "DET", "MIA", "MIN"],
    7: ["BUF", "JAX", "LAC", "WAS"],
    8: ["HOU", "NO", "NYG", "SF"],
    9: ["PIT", "TEN"],
    10: ["CHI", "DEN", "PHI", "TB"],
}

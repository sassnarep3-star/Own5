"""Official inputs transcribed from nfl.com by session d38e90c5 on 2026-11-14.

Every value in this module was read directly from the official NFL pages listed in
SOURCES below (retrieved with the session's page-fetch tool on 2026-11-14 UTC).
Nothing here is estimated, interpolated or inferred: if a published page did not
state a value, the field is left as an empty string in the row and the row is
flagged on the Flagged-for-Review page.

Naming note: NFL.com's own logo URLs abbreviate the Cardinals as "AZ" and the
Rams as "LA"; this project uses the league's standard abbreviations "ARI" and
"LAR" everywhere. The mapping is published in TEAM_ABBR_NOTE.
"""

FETCH_DATE = "2026-11-14"

TEAM_ABBR_NOTE = {
    "ARI": "NFL.com logo URLs render the Cardinals as AZ; this project uses ARI.",
    "LAR": "NFL.com logo URLs render the Rams as LA; this project uses LAR.",
}

TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}

# ---------------------------------------------------------------------------
# SOURCES (official publishers, captured 2026-11-14 UTC)
# ---------------------------------------------------------------------------
SOURCES = [
    ("S-01", "NFL.com", "2026 NFL League Standings",
     "https://www.nfl.com/standings/league/2026/REG", "2026-11-14",
     "W-L-T, PCT, PF, PA and net points for all 32 clubs (post Thursday 12 Nov game)"),
    ("S-02", "NFL.com", "2026 NFL Schedule - Week 1",
     "https://www.nfl.com/schedules/2026/by-week/week-1", "2026-11-14",
     "Week 1 matchups, dates and final scores"),
    ("S-03", "NFL.com", "2026 NFL Schedule - Week 2",
     "https://www.nfl.com/schedules/2026/by-week/week-2", "2026-11-14",
     "Week 2 matchups, dates and final scores"),
    ("S-04", "NFL.com", "2026 NFL Schedule - Week 3",
     "https://www.nfl.com/schedules/2026/by-week/week-3", "2026-11-14",
     "Week 3 matchups, dates and final scores"),
    ("S-05", "NFL.com", "2026 NFL Schedule - Week 4",
     "https://www.nfl.com/schedules/2026/by-week/week-4", "2026-11-14",
     "Week 4 matchups, dates and final scores"),
    ("S-06", "NFL.com", "2026 NFL Schedule - Week 5",
     "https://www.nfl.com/schedules/2026/by-week/week-5", "2026-11-14",
     "Week 5 matchups, dates and final scores"),
    ("S-07", "NFL.com", "2026 NFL Schedule - Week 6",
     "https://www.nfl.com/schedules/2026/by-week/week-6", "2026-11-14",
     "Week 6 matchups, dates and final scores"),
    ("S-08", "NFL.com", "2026 NFL Schedule - Week 7",
     "https://www.nfl.com/schedules/2026/by-week/week-7", "2026-11-14",
     "Week 7 matchups, dates and final scores"),
    ("S-09", "NFL.com", "2026 NFL Schedule - Week 8",
     "https://www.nfl.com/schedules/2026/by-week/week-8", "2026-11-14",
     "Week 8 matchups, dates and final scores"),
    ("S-10", "NFL.com", "2026 NFL Schedule - Week 9",
     "https://www.nfl.com/schedules/2026/by-week/week-9", "2026-11-14",
     "Week 9 matchups, dates and final scores"),
    ("S-11", "NFL.com", "2026 NFL Schedule - Week 10",
     "https://www.nfl.com/schedules/2026/by-week/week-10", "2026-11-14",
     "Week 10 matchups, dates, kickoff times, networks, final score for the "
     "completed Thursday game"),
    ("S-12", "NFL.com", "2026 NFL Schedule - Week 11",
     "https://www.nfl.com/schedules/2026/by-week/week-11", "2026-11-14",
     "Week 11 matchups, dates, kickoff times, networks and bye teams"),
    ("S-13", "NFL.com", "Official Week 10 NFL Injury Report (2026 regular season)",
     "https://www.nfl.com/injuries/", "2026-11-14",
     "Practice participation and game status for every player listed for Week 10"),
    ("S-14", "NFL.com", "NFL news roundups and Week 10 injury reports (official news index)",
     "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-saturday-nov-14",
     "2026-11-14",
     "Official league notes published on the injury page (QB changes, IR moves)"),
]

# ---------------------------------------------------------------------------
# STANDINGS  (team, W, L, T, PCT, PF, PA, DIFF)
# Source S-01. Values are exactly as published.
# ---------------------------------------------------------------------------
STANDINGS = [
    ("BUF", 7, 1, 0, "0.875", 256, 187, 69),
    ("SF", 7, 1, 0, "0.875", 235, 156, 79),
    ("CHI", 7, 2, 0, "0.778", 241, 184, 57),
    ("DEN", 7, 2, 0, "0.778", 198, 186, 12),
    ("CIN", 6, 2, 0, "0.750", 240, 175, 65),
    ("DET", 6, 2, 0, "0.750", 222, 189, 33),
    ("JAX", 6, 2, 0, "0.750", 229, 121, 108),
    ("KC", 6, 2, 0, "0.750", 202, 143, 59),
    ("MIN", 6, 2, 0, "0.750", 146, 116, 30),
    ("PIT", 6, 2, 0, "0.750", 180, 144, 36),
    ("GB", 6, 3, 0, "0.667", 216, 191, 25),
    ("NYG", 5, 3, 1, "0.611", 203, 196, 7),
    ("CLE", 5, 4, 0, "0.556", 161, 196, -35),
    ("LAR", 5, 4, 0, "0.556", 214, 181, 33),
    ("NE", 5, 4, 0, "0.556", 211, 207, 4),
    ("SEA", 5, 4, 0, "0.556", 202, 162, 40),
    ("BAL", 4, 5, 0, "0.444", 189, 236, -47),
    ("DAL", 4, 5, 0, "0.444", 246, 236, 10),
    ("LV", 4, 5, 0, "0.444", 238, 268, -30),
    ("WAS", 3, 5, 1, "0.389", 196, 223, -27),
    ("CAR", 3, 5, 0, "0.375", 199, 219, -20),
    ("HOU", 3, 5, 0, "0.375", 209, 192, 17),
    ("NO", 3, 5, 0, "0.375", 185, 216, -31),
    ("ARI", 3, 6, 0, "0.333", 178, 255, -77),
    ("ATL", 3, 6, 0, "0.333", 188, 223, -35),
    ("TB", 3, 6, 0, "0.333", 202, 178, 24),
    ("IND", 2, 7, 0, "0.222", 184, 249, -65),
    ("NYJ", 2, 7, 0, "0.222", 182, 223, -41),
    ("PHI", 2, 7, 0, "0.222", 148, 221, -73),
    ("MIA", 1, 7, 0, "0.125", 126, 200, -74),
    ("TEN", 1, 7, 0, "0.125", 144, 199, -55),
    ("LAC", 0, 8, 0, "0.000", 121, 219, -98),
]

# ---------------------------------------------------------------------------
# RESULTS FEED - completed 2026 regular-season games read off the official
# NFL.com by-week schedule pages (sources S-02 .. S-11).
# tuple = (week, date, away, home, away_pts, home_pts, source_id, game_url)
# The first team named on the NFL.com card is the away team (the game URL slug
# is "<away>-at-<home>-2026-reg-<week>", which was used to disambiguate).
# ---------------------------------------------------------------------------
RESULTS = [
    # Week 1
    (1, "2026-09-09", "NE", "SEA", 10, 13, "S-02", "https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1"),
    (1, "2026-09-10", "SF", "LAR", 27, 7, "S-02", "https://www.nfl.com/games/49ers-at-rams-2026-reg-1"),
    (1, "2026-09-13", "CHI", "CAR", 59, 37, "S-02", "https://www.nfl.com/games/bears-at-panthers-2026-reg-1"),
    (1, "2026-09-13", "TB", "CIN", 27, 33, "S-02", "https://www.nfl.com/games/buccaneers-at-bengals-2026-reg-1"),
    (1, "2026-09-13", "NO", "DET", 30, 31, "S-02", "https://www.nfl.com/games/saints-at-lions-2026-reg-1"),
    (1, "2026-09-13", "BUF", "HOU", 36, 31, "S-02", "https://www.nfl.com/games/bills-at-texans-2026-reg-1"),
    (1, "2026-09-13", "BAL", "IND", 41, 23, "S-02", "https://www.nfl.com/games/ravens-at-colts-2026-reg-1"),
    (1, "2026-09-13", "CLE", "JAX", 10, 34, "S-02", "https://www.nfl.com/games/browns-at-jaguars-2026-reg-1"),
    (1, "2026-09-13", "ATL", "PIT", 13, 20, "S-02", "https://www.nfl.com/games/falcons-at-steelers-2026-reg-1"),
    (1, "2026-09-13", "NYJ", "TEN", 23, 10, "S-02", "https://www.nfl.com/games/jets-at-titans-2026-reg-1"),
    (1, "2026-09-13", "ARI", "LAC", 26, 14, "S-02", "https://www.nfl.com/games/cardinals-at-chargers-2026-reg-1"),
    (1, "2026-09-13", "MIA", "LV", 13, 27, "S-02", "https://www.nfl.com/games/dolphins-at-raiders-2026-reg-1"),
    (1, "2026-09-13", "GB", "MIN", 22, 39, "S-02", "https://www.nfl.com/games/packers-at-vikings-2026-reg-1"),
    (1, "2026-09-13", "WAS", "PHI", 22, 24, "S-02", "https://www.nfl.com/games/commanders-at-eagles-2026-reg-1"),
    (1, "2026-09-13", "DAL", "NYG", 20, 28, "S-02", "https://www.nfl.com/games/cowboys-at-giants-2026-reg-1"),
    (1, "2026-09-14", "DEN", "KC", 10, 31, "S-02", "https://www.nfl.com/games/broncos-at-chiefs-2026-reg-1"),
    # Week 2
    (2, "2026-09-17", "DET", "BUF", 31, 41, "S-03", "https://www.nfl.com/games/lions-at-bills-2026-reg-2"),
    (2, "2026-09-20", "CAR", "ATL", 34, 3, "S-03", "https://www.nfl.com/games/panthers-at-falcons-2026-reg-2"),
    (2, "2026-09-20", "NO", "BAL", 24, 17, "S-03", "https://www.nfl.com/games/saints-at-ravens-2026-reg-2"),
    (2, "2026-09-20", "MIN", "CHI", 9, 3, "S-03", "https://www.nfl.com/games/vikings-at-bears-2026-reg-2"),
    (2, "2026-09-20", "CIN", "HOU", 20, 6, "S-03", "https://www.nfl.com/games/bengals-at-texans-2026-reg-2"),
    (2, "2026-09-20", "PIT", "NE", 3, 20, "S-03", "https://www.nfl.com/games/steelers-at-patriots-2026-reg-2"),
    (2, "2026-09-20", "GB", "NYJ", 20, 17, "S-03", "https://www.nfl.com/games/packers-at-jets-2026-reg-2"),
    (2, "2026-09-20", "CLE", "TB", 23, 19, "S-03", "https://www.nfl.com/games/browns-at-buccaneers-2026-reg-2"),
    (2, "2026-09-20", "PHI", "TEN", 24, 20, "S-03", "https://www.nfl.com/games/eagles-at-titans-2026-reg-2"),
    (2, "2026-09-20", "JAX", "DEN", 13, 20, "S-03", "https://www.nfl.com/games/jaguars-at-broncos-2026-reg-2"),
    (2, "2026-09-20", "LV", "LAC", 26, 14, "S-03", "https://www.nfl.com/games/raiders-at-chargers-2026-reg-2"),
    (2, "2026-09-20", "SEA", "ARI", 31, 7, "S-03", "https://www.nfl.com/games/seahawks-at-cardinals-2026-reg-2"),
    (2, "2026-09-20", "WAS", "DAL", 20, 37, "S-03", "https://www.nfl.com/games/commanders-at-cowboys-2026-reg-2"),
    (2, "2026-09-20", "MIA", "SF", 13, 35, "S-03", "https://www.nfl.com/games/dolphins-at-49ers-2026-reg-2"),
    (2, "2026-09-20", "IND", "KC", 30, 33, "S-03", "https://www.nfl.com/games/colts-at-chiefs-2026-reg-2"),
    (2, "2026-09-21", "NYG", "LAR", 6, 28, "S-03", "https://www.nfl.com/games/giants-at-rams-2026-reg-2"),
    # Week 3
    (3, "2026-09-24", "ATL", "GB", 35, 14, "S-04", "https://www.nfl.com/games/falcons-at-packers-2026-reg-3"),
    (3, "2026-09-27", "LAC", "BUF", 16, 24, "S-04", "https://www.nfl.com/games/chargers-at-bills-2026-reg-3"),
    (3, "2026-09-27", "CAR", "CLE", 18, 21, "S-04", "https://www.nfl.com/games/panthers-at-browns-2026-reg-3"),
    (3, "2026-09-27", "NYJ", "DET", 24, 31, "S-04", "https://www.nfl.com/games/jets-at-lions-2026-reg-3"),
    (3, "2026-09-27", "HOU", "IND", 17, 19, "S-04", "https://www.nfl.com/games/texans-at-colts-2026-reg-3"),
    (3, "2026-09-27", "NE", "JAX", 6, 35, "S-04", "https://www.nfl.com/games/patriots-at-jaguars-2026-reg-3"),
    (3, "2026-09-27", "KC", "MIA", 24, 10, "S-04", "https://www.nfl.com/games/chiefs-at-dolphins-2026-reg-3"),
    (3, "2026-09-27", "TEN", "NYG", 7, 12, "S-04", "https://www.nfl.com/games/titans-at-giants-2026-reg-3"),
    (3, "2026-09-27", "CIN", "PIT", 27, 30, "S-04", "https://www.nfl.com/games/bengals-at-steelers-2026-reg-3"),
    (3, "2026-09-27", "SEA", "WAS", 31, 33, "S-04", "https://www.nfl.com/games/seahawks-at-commanders-2026-reg-3"),
    (3, "2026-09-27", "ARI", "SF", 30, 36, "S-04", "https://www.nfl.com/games/cardinals-at-49ers-2026-reg-3"),
    (3, "2026-09-27", "MIN", "TB", 23, 16, "S-04", "https://www.nfl.com/games/vikings-at-buccaneers-2026-reg-3"),
    (3, "2026-09-27", "LV", "NO", 35, 27, "S-04", "https://www.nfl.com/games/raiders-at-saints-2026-reg-3"),
    (3, "2026-09-27", "BAL", "DAL", 34, 31, "S-04", "https://www.nfl.com/games/ravens-at-cowboys-2026-reg-3"),
    (3, "2026-09-27", "LAR", "DEN", 26, 30, "S-04", "https://www.nfl.com/games/rams-at-broncos-2026-reg-3"),
    (3, "2026-09-28", "PHI", "CHI", 7, 27, "S-04", "https://www.nfl.com/games/eagles-at-bears-2026-reg-3"),
    # Week 4
    (4, "2026-10-01", "PIT", "CLE", 24, 27, "S-05", "https://www.nfl.com/games/steelers-at-browns-2026-reg-4"),
    (4, "2026-10-04", "IND", "WAS", 30, 13, "S-05", "https://www.nfl.com/games/colts-at-commanders-2026-reg-4"),
    (4, "2026-10-04", "TEN", "BAL", 18, 24, "S-05", "https://www.nfl.com/games/titans-at-ravens-2026-reg-4"),
    (4, "2026-10-04", "NE", "BUF", 29, 26, "S-05", "https://www.nfl.com/games/patriots-at-bills-2026-reg-4"),
    (4, "2026-10-04", "NYJ", "CHI", 12, 23, "S-05", "https://www.nfl.com/games/jets-at-bears-2026-reg-4"),
    (4, "2026-10-04", "JAX", "CIN", 22, 17, "S-05", "https://www.nfl.com/games/jaguars-at-bengals-2026-reg-4"),
    (4, "2026-10-04", "DAL", "HOU", 34, 30, "S-05", "https://www.nfl.com/games/cowboys-at-texans-2026-reg-4"),
    (4, "2026-10-04", "ARI", "NYG", 24, 36, "S-05", "https://www.nfl.com/games/cardinals-at-giants-2026-reg-4"),
    (4, "2026-10-04", "LAR", "PHI", 24, 20, "S-05", "https://www.nfl.com/games/rams-at-eagles-2026-reg-4"),
    (4, "2026-10-04", "GB", "TB", 17, 14, "S-05", "https://www.nfl.com/games/packers-at-buccaneers-2026-reg-4"),
    (4, "2026-10-04", "MIA", "MIN", 10, 15, "S-05", "https://www.nfl.com/games/dolphins-at-vikings-2026-reg-4"),
    (4, "2026-10-04", "KC", "LV", 30, 27, "S-05", "https://www.nfl.com/games/chiefs-at-raiders-2026-reg-4"),
    (4, "2026-10-04", "LAC", "SEA", 23, 30, "S-05", "https://www.nfl.com/games/chargers-at-seahawks-2026-reg-4"),
    (4, "2026-10-04", "DEN", "SF", 14, 24, "S-05", "https://www.nfl.com/games/broncos-at-49ers-2026-reg-4"),
    (4, "2026-10-04", "DET", "CAR", 26, 32, "S-05", "https://www.nfl.com/games/lions-at-panthers-2026-reg-4"),
    (4, "2026-10-05", "ATL", "NO", 45, 24, "S-05", "https://www.nfl.com/games/falcons-at-saints-2026-reg-4"),
    # Week 5
    (5, "2026-10-08", "TB", "DAL", 24, 16, "S-06", "https://www.nfl.com/games/buccaneers-at-cowboys-2026-reg-5"),
    (5, "2026-10-11", "PHI", "JAX", 17, 19, "S-06", "https://www.nfl.com/games/eagles-at-jaguars-2026-reg-5"),
    (5, "2026-10-11", "CIN", "MIA", 31, 24, "S-06", "https://www.nfl.com/games/bengals-at-dolphins-2026-reg-5"),
    (5, "2026-10-11", "LV", "NE", 17, 45, "S-06", "https://www.nfl.com/games/raiders-at-patriots-2026-reg-5"),
    (5, "2026-10-11", "MIN", "NO", 23, 13, "S-06", "https://www.nfl.com/games/vikings-at-saints-2026-reg-5"),
    (5, "2026-10-11", "CLE", "NYJ", 12, 17, "S-06", "https://www.nfl.com/games/browns-at-jets-2026-reg-5"),
    (5, "2026-10-11", "IND", "PIT", 22, 34, "S-06", "https://www.nfl.com/games/colts-at-steelers-2026-reg-5"),
    (5, "2026-10-11", "HOU", "TEN", 26, 3, "S-06", "https://www.nfl.com/games/texans-at-titans-2026-reg-5"),
    (5, "2026-10-11", "NYG", "WAS", 27, 27, "S-06", "https://www.nfl.com/games/giants-at-commanders-2026-reg-5"),
    (5, "2026-10-11", "CHI", "GB", 7, 31, "S-06", "https://www.nfl.com/games/bears-at-packers-2026-reg-5"),
    (5, "2026-10-11", "DEN", "LAC", 23, 17, "S-06", "https://www.nfl.com/games/broncos-at-chargers-2026-reg-5"),
    (5, "2026-10-11", "DET", "ARI", 45, 21, "S-06", "https://www.nfl.com/games/lions-at-cardinals-2026-reg-5"),
    (5, "2026-10-11", "SF", "SEA", 32, 29, "S-06", "https://www.nfl.com/games/49ers-at-seahawks-2026-reg-5"),
    (5, "2026-10-11", "BAL", "ATL", 30, 23, "S-06", "https://www.nfl.com/games/ravens-at-falcons-2026-reg-5"),
    (5, "2026-10-12", "BUF", "LAR", 37, 34, "S-06", "https://www.nfl.com/games/bills-at-rams-2026-reg-5"),
    # Week 6
    (6, "2026-10-15", "SEA", "DEN", 14, 17, "S-07", "https://www.nfl.com/games/seahawks-at-broncos-2026-reg-6"),
    (6, "2026-10-18", "HOU", "JAX", 34, 31, "S-07", "https://www.nfl.com/games/texans-at-jaguars-2026-reg-6"),
    (6, "2026-10-18", "CHI", "ATL", 31, 23, "S-07", "https://www.nfl.com/games/bears-at-falcons-2026-reg-6"),
    (6, "2026-10-18", "BAL", "CLE", 10, 13, "S-07", "https://www.nfl.com/games/ravens-at-browns-2026-reg-6"),
    (6, "2026-10-18", "TEN", "IND", 26, 20, "S-07", "https://www.nfl.com/games/titans-at-colts-2026-reg-6"),
    (6, "2026-10-18", "NYJ", "NE", 19, 26, "S-07", "https://www.nfl.com/games/jets-at-patriots-2026-reg-6"),
    (6, "2026-10-18", "NO", "NYG", 34, 27, "S-07", "https://www.nfl.com/games/saints-at-giants-2026-reg-6"),
    (6, "2026-10-18", "CAR", "PHI", 25, 14, "S-07", "https://www.nfl.com/games/panthers-at-eagles-2026-reg-6"),
    (6, "2026-10-18", "PIT", "TB", 26, 19, "S-07", "https://www.nfl.com/games/steelers-at-buccaneers-2026-reg-6"),
    (6, "2026-10-18", "ARI", "LAR", 18, 16, "S-07", "https://www.nfl.com/games/cardinals-at-rams-2026-reg-6"),
    (6, "2026-10-18", "LAC", "KC", 6, 22, "S-07", "https://www.nfl.com/games/chargers-at-chiefs-2026-reg-6"),
    (6, "2026-10-18", "BUF", "LV", 33, 30, "S-07", "https://www.nfl.com/games/bills-at-raiders-2026-reg-6"),
    (6, "2026-10-18", "DAL", "GB", 13, 23, "S-07", "https://www.nfl.com/games/cowboys-at-packers-2026-reg-6"),
    (6, "2026-10-19", "WAS", "SF", 17, 23, "S-07", "https://www.nfl.com/games/commanders-at-49ers-2026-reg-6"),
    # Week 7
    (7, "2026-10-22", "NE", "CHI", 24, 30, "S-08", "https://www.nfl.com/games/patriots-at-bears-2026-reg-7"),
    (7, "2026-10-25", "PIT", "NO", 16, 10, "S-08", "https://www.nfl.com/games/steelers-at-saints-2026-reg-7"),
    (7, "2026-10-25", "SF", "ATL", 20, 29, "S-08", "https://www.nfl.com/games/49ers-at-falcons-2026-reg-7"),
    (7, "2026-10-25", "CIN", "BAL", 35, 13, "S-08", "https://www.nfl.com/games/bengals-at-ravens-2026-reg-7"),
    (7, "2026-10-25", "TB", "CAR", 43, 13, "S-08", "https://www.nfl.com/games/buccaneers-at-panthers-2026-reg-7"),
    (7, "2026-10-25", "NYG", "HOU", 27, 21, "S-08", "https://www.nfl.com/games/giants-at-texans-2026-reg-7"),
    (7, "2026-10-25", "IND", "MIN", 10, 16, "S-08", "https://www.nfl.com/games/colts-at-vikings-2026-reg-7"),
    (7, "2026-10-25", "MIA", "NYJ", 28, 25, "S-08", "https://www.nfl.com/games/dolphins-at-jets-2026-reg-7"),
    (7, "2026-10-25", "CLE", "TEN", 27, 24, "S-08", "https://www.nfl.com/games/browns-at-titans-2026-reg-7"),
    (7, "2026-10-25", "DEN", "ARI", 30, 16, "S-08", "https://www.nfl.com/games/broncos-at-cardinals-2026-reg-7"),
    (7, "2026-10-25", "GB", "DET", 17, 20, "S-08", "https://www.nfl.com/games/packers-at-lions-2026-reg-7"),
    (7, "2026-10-25", "LAR", "LV", 35, 21, "S-08", "https://www.nfl.com/games/rams-at-raiders-2026-reg-7"),
    (7, "2026-10-25", "KC", "SEA", 3, 20, "S-08", "https://www.nfl.com/games/chiefs-at-seahawks-2026-reg-7"),
    (7, "2026-10-26", "DAL", "PHI", 38, 21, "S-08", "https://www.nfl.com/games/cowboys-at-eagles-2026-reg-7"),
    # Week 8
    (8, "2026-10-29", "CAR", "GB", 19, 27, "S-09", "https://www.nfl.com/games/panthers-at-packers-2026-reg-8"),
    (8, "2026-11-01", "BAL", "BUF", 10, 36, "S-09", "https://www.nfl.com/games/ravens-at-bills-2026-reg-8"),
    (8, "2026-11-01", "TEN", "CIN", 36, 43, "S-09", "https://www.nfl.com/games/titans-at-bengals-2026-reg-8"),
    (8, "2026-11-01", "ARI", "DAL", 33, 30, "S-09", "https://www.nfl.com/games/cardinals-at-cowboys-2026-reg-8"),
    (8, "2026-11-01", "MIN", "DET", 15, 19, "S-09", "https://www.nfl.com/games/vikings-at-lions-2026-reg-8"),
    (8, "2026-11-01", "IND", "JAX", 7, 42, "S-09", "https://www.nfl.com/games/colts-at-jaguars-2026-reg-8"),
    (8, "2026-11-01", "LV", "NYJ", 38, 33, "S-09", "https://www.nfl.com/games/raiders-at-jets-2026-reg-8"),
    (8, "2026-11-01", "CLE", "PIT", 6, 27, "S-09", "https://www.nfl.com/games/browns-at-steelers-2026-reg-8"),
    (8, "2026-11-01", "ATL", "TB", 0, 16, "S-09", "https://www.nfl.com/games/falcons-at-buccaneers-2026-reg-8"),
    (8, "2026-11-01", "LAC", "LAR", 9, 24, "S-09", "https://www.nfl.com/games/chargers-at-rams-2026-reg-8"),
    (8, "2026-11-01", "KC", "DEN", 24, 28, "S-09", "https://www.nfl.com/games/chiefs-at-broncos-2026-reg-8"),
    (8, "2026-11-01", "NE", "MIA", 24, 19, "S-09", "https://www.nfl.com/games/patriots-at-dolphins-2026-reg-8"),
    (8, "2026-11-01", "PHI", "WAS", 10, 27, "S-09", "https://www.nfl.com/games/eagles-at-commanders-2026-reg-8"),
    (8, "2026-11-02", "CHI", "SEA", 34, 17, "S-09", "https://www.nfl.com/games/bears-at-seahawks-2026-reg-8"),
    # Week 9
    (9, "2026-11-05", "JAX", "BAL", 33, 10, "S-10", "https://www.nfl.com/games/jaguars-at-ravens-2026-reg-9"),
    (9, "2026-11-08", "CIN", "ATL", 34, 17, "S-10", "https://www.nfl.com/games/bengals-at-falcons-2026-reg-9"),
    (9, "2026-11-08", "DEN", "CAR", 26, 21, "S-10", "https://www.nfl.com/games/broncos-at-panthers-2026-reg-9"),
    (9, "2026-11-08", "DAL", "IND", 27, 23, "S-10", "https://www.nfl.com/games/cowboys-at-colts-2026-reg-9"),
    (9, "2026-11-08", "NYJ", "KC", 12, 35, "S-10", "https://www.nfl.com/games/jets-at-chiefs-2026-reg-9"),
    (9, "2026-11-08", "DET", "MIA", 19, 9, "S-10", "https://www.nfl.com/games/lions-at-dolphins-2026-reg-9"),
    (9, "2026-11-08", "CLE", "NO", 22, 23, "S-10", "https://www.nfl.com/games/browns-at-saints-2026-reg-9"),
    (9, "2026-11-08", "NYG", "PHI", 19, 11, "S-10", "https://www.nfl.com/games/giants-at-eagles-2026-reg-9"),
    (9, "2026-11-08", "LAR", "WAS", 20, 13, "S-10", "https://www.nfl.com/games/rams-at-commanders-2026-reg-9"),
    (9, "2026-11-08", "HOU", "LAC", 44, 22, "S-10", "https://www.nfl.com/games/texans-at-chargers-2026-reg-9"),
    (9, "2026-11-08", "LV", "SF", 17, 38, "S-10", "https://www.nfl.com/games/raiders-at-49ers-2026-reg-9"),
    (9, "2026-11-08", "GB", "NE", 45, 27, "S-10", "https://www.nfl.com/games/packers-at-patriots-2026-reg-9"),
    (9, "2026-11-08", "ARI", "SEA", 3, 17, "S-10", "https://www.nfl.com/games/cardinals-at-seahawks-2026-reg-9"),
    (9, "2026-11-08", "TB", "CHI", 24, 27, "S-10", "https://www.nfl.com/games/buccaneers-at-bears-2026-reg-9"),
    (9, "2026-11-09", "BUF", "MIN", 23, 6, "S-10", "https://www.nfl.com/games/bills-at-vikings-2026-reg-9"),
    # Week 10 (completed Thursday game only)
    (10, "2026-11-12", "WAS", "NYG", 24, 21, "S-11", "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"),
]

# ---------------------------------------------------------------------------
# UPCOMING SLATE - games not yet played as of the 2026-11-14 capture.
# tuple = (week, kickoff_date, kickoff_et, away, home, network, game_url, note)
# ---------------------------------------------------------------------------
SLATE = [
    (10, "2026-11-15", "9:30 AM", "NE", "DET", "FOX", "https://www.nfl.com/games/patriots-at-lions-2026-reg-10", "Munich, Germany"),
    (10, "2026-11-15", "1:00 PM", "KC", "ATL", "CBS", "https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10", ""),
    (10, "2026-11-15", "1:00 PM", "HOU", "CLE", "FOX", "https://www.nfl.com/games/texans-at-browns-2026-reg-10", ""),
    (10, "2026-11-15", "1:00 PM", "MIN", "GB", "FOX", "https://www.nfl.com/games/vikings-at-packers-2026-reg-10", ""),
    (10, "2026-11-15", "1:00 PM", "MIA", "IND", "CBS", "https://www.nfl.com/games/dolphins-at-colts-2026-reg-10", ""),
    (10, "2026-11-15", "1:00 PM", "CAR", "NO", "FOX", "https://www.nfl.com/games/panthers-at-saints-2026-reg-10", ""),
    (10, "2026-11-15", "1:00 PM", "BUF", "NYJ", "CBS", "https://www.nfl.com/games/bills-at-jets-2026-reg-10", ""),
    (10, "2026-11-15", "1:00 PM", "JAX", "TEN", "FOX", "https://www.nfl.com/games/jaguars-at-titans-2026-reg-10", ""),
    (10, "2026-11-15", "4:05 PM", "LAR", "ARI", "CBS", "https://www.nfl.com/games/rams-at-cardinals-2026-reg-10", ""),
    (10, "2026-11-15", "4:05 PM", "SEA", "LV", "CBS", "https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10", ""),
    (10, "2026-11-15", "4:25 PM", "SF", "DAL", "FOX", "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10", ""),
    (10, "2026-11-15", "8:20 PM", "PIT", "CIN", "NBC", "https://www.nfl.com/games/steelers-at-bengals-2026-reg-10", ""),
    (10, "2026-11-16", "8:15 PM", "LAC", "BAL", "ESPN", "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10", ""),
    (11, "2026-11-19", "8:15 PM", "IND", "HOU", "PRIME", "https://www.nfl.com/games/colts-at-texans-2026-reg-11", ""),
    (11, "2026-11-22", "1:00 PM", "MIA", "BUF", "CBS", "https://www.nfl.com/games/dolphins-at-bills-2026-reg-11", ""),
    (11, "2026-11-22", "1:00 PM", "BAL", "CAR", "FOX", "https://www.nfl.com/games/ravens-at-panthers-2026-reg-11", ""),
    (11, "2026-11-22", "1:00 PM", "NO", "CHI", "FOX", "https://www.nfl.com/games/saints-at-bears-2026-reg-11", ""),
    (11, "2026-11-22", "1:00 PM", "TEN", "DAL", "FOX", "https://www.nfl.com/games/titans-at-cowboys-2026-reg-11", ""),
    (11, "2026-11-22", "1:00 PM", "TB", "DET", "FOX", "https://www.nfl.com/games/buccaneers-at-lions-2026-reg-11", ""),
    (11, "2026-11-22", "1:00 PM", "ARI", "KC", "CBS", "https://www.nfl.com/games/cardinals-at-chiefs-2026-reg-11", ""),
    (11, "2026-11-22", "1:00 PM", "PIT", "PHI", "CBS", "https://www.nfl.com/games/steelers-at-eagles-2026-reg-11", ""),
    (11, "2026-11-22", "4:05 PM", "NYJ", "LAC", "FOX", "https://www.nfl.com/games/jets-at-chargers-2026-reg-11", ""),
    (11, "2026-11-22", "4:25 PM", "JAX", "NYG", "CBS", "https://www.nfl.com/games/jaguars-at-giants-2026-reg-11", ""),
    (11, "2026-11-22", "4:25 PM", "LV", "DEN", "CBS", "https://www.nfl.com/games/raiders-at-broncos-2026-reg-11", ""),
    (11, "2026-11-22", "8:20 PM", "MIN", "SF", "NBC", "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11", "Mexico City, Mexico"),
    (11, "2026-11-23", "8:15 PM", "CIN", "WAS", "ESPN", "https://www.nfl.com/games/bengals-at-commanders-2026-reg-11", ""),
]

# Bye weeks published on the official by-week schedule pages.
BYE_WEEKS = {
    5: ["CAR", "KC"],
    6: ["CIN", "DET", "MIA", "MIN"],
    7: ["BUF", "JAX", "LAC", "WAS"],
    8: ["HOU", "NO", "NYG", "SF"],
    9: ["PIT", "TEN"],
    10: ["CHI", "DEN", "PHI", "TB"],
    11: ["ATL", "CLE", "GB", "LAR", "NE", "SEA"],
}

#!/usr/bin/env python3
"""Verbatim transcription of official pages read by session 4078a9ad on 2026-11-18.

Every constant here is a transcription of text returned by the sandbox fetch tool from an
official publisher (nfl.com or media.nfl.com). Nothing is inferred, estimated or filled in.
Where a page did not supply a value the value is None and the consumer must publish a blank
cell plus an UNVERIFIED flag.

Sources (read 2026-11-18, UTC, processed text not server bytes):
  S1 https://www.nfl.com/standings/league/2026/REG              read 03:52Z
  S2 https://www.nfl.com/schedules/2026/by-week/week-10          read 03:50Z
  S3 https://www.nfl.com/schedules/2026/by-week/week-11          read 03:47Z
  S4 https://www.nfl.com/injuries/league/2026/reg11               read 03:45Z -> resolved to reg10
  S5 https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1   read 03:55Z
  S6 https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced  read 03:58Z
"""

READ_UTC = "2026-11-18T03:45:00Z"  # earliest read in the batch; per-source stamps below

SOURCES = [
    ("S1", "NFL", "https://www.nfl.com/standings/league/2026/REG",
     "League standings 2026 REG: W-L-T, PCT, PF, PA, NET, records, streak", "2026-11-18T03:52:00Z", "official"),
    ("S2", "NFL", "https://www.nfl.com/schedules/2026/by-week/week-10",
     "Week 10 finals (14 played games + 4 byes)", "2026-11-18T03:50:00Z", "official"),
    ("S3", "NFL", "https://www.nfl.com/schedules/2026/by-week/week-11",
     "Week 11 slate (13 games + 6 byes), networks, dates, venues via hotel link destination", "2026-11-18T03:47:00Z", "official"),
    ("S4", "NFL", "https://www.nfl.com/injuries/league/2026/reg11",
     "Availability: requested reg11, served Week 10 report (no Week 11 report published at read time)", "2026-11-18T03:45:00Z", "official"),
    ("S5", "NFL", "https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1",
     "Spot check of corpus row 1: final score, venue (Lumen Field, Seattle WA), Game Book PDF link", "2026-11-18T03:55:00Z", "official"),
    ("S6", "NFL Football Communications", "https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced",
     "Dated schedule announcement, 2026-05-14: 18 weeks, 272 games, 17+3, nine international games, venue names", "2026-11-18T03:58:00Z", "official"),
    ("S7", "GitHub", "https://api.github.com/repos/sassnarep3-star/Own5/pages",
     "Publication configuration: Pages served from main at /", "2026-11-18T03:41:00Z", "repository"),
]

# ----------------------------------------------------------------------------------
# S1 — official standings, 2026 REG, read 2026-11-18T03:52Z
# Column order as printed on the page: W, L, T, PCT, PF, PA, NET, DIV, HOME, AWAY, ...
# Club abbreviation is the nfl.com logo path token (AZ and LA are printed for Arizona and
# the Rams; the schedule page prints LAR in the bye block — see FLAG-A1).
# ----------------------------------------------------------------------------------
STANDINGS = [
    # code, name, w, l, t, pct, pf, pa
    ("BUF", "Buffalo Bills", 8, 1, 0, "0.889", 287, 199),
    ("SF", "San Francisco 49ers", 8, 1, 0, "0.889", 281, 196),
    ("CHI", "Chicago Bears", 7, 2, 0, "0.778", 241, 184),
    ("CIN", "Cincinnati Bengals", 7, 2, 0, "0.778", 278, 193),
    ("DEN", "Denver Broncos", 7, 2, 0, "0.778", 198, 186),
    ("DET", "Detroit Lions", 7, 2, 0, "0.778", 257, 199),
    ("JAX", "Jacksonville Jaguars", 7, 2, 0, "0.778", 269, 144),
    ("KC", "Kansas City Chiefs", 7, 2, 0, "0.778", 237, 156),
    ("MIN", "Minnesota Vikings", 7, 2, 0, "0.778", 176, 126),
    ("PIT", "Pittsburgh Steelers", 6, 3, 0, "0.667", 198, 182),
    ("NYG", "New York Giants", 5, 3, 1, "0.611", 203, 196),
    ("CLE", "Cleveland Browns", 6, 4, 0, "0.600", 188, 220),
    ("GB", "Green Bay Packers", 6, 4, 0, "0.600", 226, 221),
    ("LA", "Los Angeles Rams", 6, 4, 0, "0.600", 248, 187),
    ("SEA", "Seattle Seahawks", 6, 4, 0, "0.600", 223, 175),
    ("NE", "New England Patriots", 5, 5, 0, "0.500", 221, 242),
    ("CAR", "Carolina Panthers", 4, 5, 0, "0.444", 219, 236),
    ("BAL", "Baltimore Ravens", 4, 6, 0, "0.400", 209, 259),
    ("DAL", "Dallas Cowboys", 4, 6, 0, "0.400", 286, 282),
    ("LV", "Las Vegas Raiders", 4, 6, 0, "0.400", 251, 289),
    ("WAS", "Washington Commanders", 3, 5, 1, "0.389", 196, 223),
    ("HOU", "Houston Texans", 3, 6, 0, "0.333", 233, 219),
    ("NO", "New Orleans Saints", 3, 6, 0, "0.333", 202, 236),
    ("TB", "Tampa Bay Buccaneers", 3, 6, 0, "0.333", 202, 178),
    ("AZ", "Arizona Cardinals", 3, 7, 0, "0.300", 184, 289),
    ("ATL", "Atlanta Falcons", 3, 7, 0, "0.300", 201, 258),
    ("IND", "Indianapolis Colts", 3, 7, 0, "0.300", 208, 271),
    ("PHI", "Philadelphia Eagles", 2, 7, 0, "0.222", 148, 221),
    ("NYJ", "New York Jets", 2, 8, 0, "0.200", 194, 254),
    ("LAC", "Los Angeles Chargers", 1, 8, 0, "0.111", 144, 239),
    ("MIA", "Miami Dolphins", 1, 8, 0, "0.111", 148, 224),
    ("TEN", "Tennessee Titans", 1, 8, 0, "0.111", 167, 239),
]

# ----------------------------------------------------------------------------------
# S2 — Week 10 finals exactly as the official week page prints them, read 03:50Z.
# Header form: "<Away> <a>, <Home> <h>, FINAL, <weekday>, November <d>th".
# ----------------------------------------------------------------------------------
WEEK10 = [
    # week, date, away, home, away_score, home_score, kickoff_note
    (10, "2026-11-12", "WAS", "NYG", 24, 21, "Thursday Night Football"),
    (10, "2026-11-15", "NE", "DET", 10, 35, "International Game, Munich"),
    (10, "2026-11-15", "KC", "ATL", 35, 13, ""),
    (10, "2026-11-15", "HOU", "CLE", 24, 27, ""),
    (10, "2026-11-15", "MIN", "GB", 30, 10, ""),
    (10, "2026-11-15", "MIA", "IND", 22, 24, ""),
    (10, "2026-11-15", "CAR", "NO", 20, 17, ""),
    (10, "2026-11-15", "BUF", "NYJ", 31, 12, ""),
    (10, "2026-11-15", "JAX", "TEN", 40, 23, ""),
    (10, "2026-11-15", "LA", "AZ", 34, 6, ""),
    (10, "2026-11-15", "SEA", "LV", 21, 13, ""),
    (10, "2026-11-15", "SF", "DAL", 46, 40, ""),
    (10, "2026-11-15", "PIT", "CIN", 18, 38, "Sunday Night Football"),
    (10, "2026-11-16", "LAC", "BAL", 23, 20, "Monday Night Football"),
]
WEEK10_BYES = ["CHI", "DEN", "PHI", "TB"]  # printed on the official week-10 page

# ----------------------------------------------------------------------------------
# S3 — Week 11 slate as printed, read 03:47Z. Venue = the destination named in the
# page's own hotel link (documented method; the page does not print a venue column).
# neutral = the page prints an international/neutral flag image and city.
# ----------------------------------------------------------------------------------
VENUE_METHOD = "hotel link destination printed on the official week page"
WEEK11 = [
    # date, time_et, network, away, home, venue, venue_method, neutral, page_evidence
    ("2026-11-19", "20:15", "PRIME", "IND", "HOU", "NRG Stadium", VENUE_METHOD, "no", "Thursday Night Football"),
    ("2026-11-22", "13:00", "CBS", "MIA", "BUF", "Highmark Stadium", VENUE_METHOD, "no", ""),
    ("2026-11-22", "13:00", "FOX", "BAL", "CAR", "Bank of America Stadium", VENUE_METHOD, "no", ""),
    ("2026-11-22", "13:00", "FOX", "NO", "CHI", "Soldier Field", VENUE_METHOD, "no", ""),
    ("2026-11-22", "13:00", "FOX", "TEN", "DAL", "AT&T Stadium", VENUE_METHOD, "no", ""),
    ("2026-11-22", "13:00", "FOX", "TB", "DET", "Ford Field", VENUE_METHOD, "no", ""),
    ("2026-11-22", "13:00", "CBS", "AZ", "KC", "GEHA Field at Arrowhead Stadium", VENUE_METHOD, "no", ""),
    ("2026-11-22", "13:00", "CBS", "PIT", "PHI", "Lincoln Financial Field", VENUE_METHOD, "no", ""),
    ("2026-11-22", "16:05", "FOX", "NYJ", "LAC", "SoFi Stadium", VENUE_METHOD, "no", ""),
    ("2026-11-22", "16:25", "CBS", "JAX", "NYG", "MetLife Stadium", VENUE_METHOD, "no", ""),
    ("2026-11-22", "16:25", "CBS", "LV", "DEN", "Empower Field at Mile High", VENUE_METHOD, "no", ""),
    ("2026-11-22", "20:20", "NBC", "MIN", "SF", "Estadio Banorte", "page prints 'Mexico City' event banner; stadium name from the 2026-05-14 announcement (S6)", "yes", "Sunday Night Football, Mexico City"),
    ("2026-11-23", "20:15", "ESPN", "CIN", "WAS", "FedEx Field", VENUE_METHOD, "no", "Monday Night Football"),
]
WEEK11_BYES = ["ATL", "CLE", "GB", "LA", "NE", "SEA"]  # printed as LA / LAR in logo+label; see FLAG-A1

WEEK11_GAMES, WEEK10_GAMES = len(WEEK11), len(WEEK10)

# ----------------------------------------------------------------------------------
# S4 — Week 10 injury report rows for the four clubs fully visible in chunk 0,
# re-read 2026-11-18T03:45Z. The repository's capture of 2026-11-12T16:52Z shows
# several of these rows with an EMPTY injury and game status. Those rows are the
# verified stale-capture diff published on the availability page.
# format: club, player, position, injuries, practice, game_status
# ----------------------------------------------------------------------------------
INJURY_WEEK10_RE_READ = [
    ("WAS", "John Bates", "TE", "", "Full Participation in Practice", ""),
    ("WAS", "Treylon Burks", "WR", "", "Did Not Participate In Practice", ""),
    ("WAS", "Jayden Daniels", "QB", "", "Full Participation in Practice", ""),
    ("WAS", "Matt Gulbin", "C", "", "Full Participation in Practice", ""),
    ("WAS", "Chig Okonkwo", "TE", "", "Full Participation in Practice", ""),
    ("WAS", "Lucas Patrick", "C", "Concussion", "Did Not Participate In Practice", "Out"),
    ("WAS", "Amik Robertson", "CB", "", "Limited Participation in Practice", ""),
    ("WAS", "Shy Tuttle", "DT", "", "Full Participation in Practice", ""),
    ("WAS", "Colson Yankoff", "TE", "Knee", "Did Not Participate In Practice", "Out"),
    ("NYG", "Abdul Carter", "LB", "", "Full Participation in Practice", ""),
    ("NYG", "Jermaine Eluemunor", "T", "", "Full Participation in Practice", ""),
    ("NYG", "Malik Harrison", "LB", "Groin", "Limited Participation in Practice", "Questionable"),
    ("NYG", "Colton Hood", "CB", "", "Full Participation in Practice", ""),
    ("NYG", "Theo Johnson", "TE", "", "Full Participation in Practice", ""),
    ("NYG", "Charlie Jones", "WR", "", "Full Participation in Practice", ""),
    ("NYG", "J.J. McCarthy", "QB", "", "Full Participation in Practice", ""),
    ("NYG", "Darnell Mooney", "WR", "", "Full Participation in Practice", ""),
    ("NYG", "Malik Nabers", "WR", "", "Full Participation in Practice", ""),
    ("NYG", "Cam Skattebo", "RB", "", "Full Participation in Practice", ""),
    ("NYG", "Andrew Thomas", "T", "", "Full Participation in Practice", ""),
    ("NE", "Ben Brown", "C", "Knee", "Did Not Participate In Practice", "Out"),
    ("NE", "A.J. Brown", "WR", "Ankle, Knee", "Limited Participation in Practice", "Questionable"),
    ("NE", "Kevin Byard", "S", "Chest", "Full Participation in Practice", "Questionable"),
    ("NE", "Carlton Davis III", "CB", "Knee", "Did Not Participate In Practice", "Out"),
    ("NE", "Reggie Gilliam", "FB", "Knee", "Limited Participation in Practice", "Questionable"),
    ("NE", "TreVeyon Henderson", "RB", "Illness", "Did Not Participate In Practice", "Out"),
    ("NE", "Hunter Henry", "TE", "", "Limited Participation in Practice", ""),
    ("NE", "Cameron Latu", "TE", "Back", "Limited Participation in Practice", "Questionable"),
    ("NE", "Drake Maye", "QB", "", "Full Participation in Practice", ""),
    ("NE", "Morgan Moses", "T", "", "Full Participation in Practice", ""),
    ("NE", "Walter Rouse", "T", "Concussion", "Limited Participation in Practice", "Questionable"),
    ("NE", "Brenden Schooler", "S", "Hamstring", "Limited Participation in Practice", "Questionable"),
    ("NE", "Rhamondre Stevenson", "RB", "Knee", "Limited Participation in Practice", "Questionable"),
    ("NE", "Greg Van Roten", "G", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("NE", "Charles Woods", "CB", "Hamstring", "Full Participation in Practice", "Questionable"),
    ("DET", "Brian Branch", "S", "", "Full Participation in Practice", ""),
    ("DET", "Jared Goff", "QB", "", "Full Participation in Practice", ""),
    ("DET", "Kerby Joseph", "S", "Knee", "Did Not Participate In Practice", "Out"),
    ("DET", "Cade Mays", "C", "Ankle", "Did Not Participate In Practice", "Out"),
    ("DET", "D.J. Reed", "CB", "Hip", "Did Not Participate In Practice", "Out"),
    ("DET", "Jacob Saylors", "RB", "", "Full Participation in Practice", ""),
    ("DET", "Amon-Ra St. Brown", "WR", "Rib", "Limited Participation in Practice", "Questionable"),
    ("DET", "Sione Vaki", "RB", "Ankle", "Limited Participation in Practice", "Questionable"),
    ("DET", "DJ Wonnum", "DE", "", "Full Participation in Practice", ""),
]

# ----------------------------------------------------------------------------------
# S6 — 2026 NFL schedule announcement, media.nfl.com, dated 2026-05-14.
# Only the facts printed in the announcement are transcribed here.
# ----------------------------------------------------------------------------------
ANNOUNCEMENT = {
    "url": "https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced",
    "date": "2026-05-14",
    "title": "2026 NFL Schedule Announced",
    "weeks": 18,
    "games": 272,
    "regular_games_per_team": 17,
    "preseason_games_per_team": 3,
    "season_number": 107,
    "kickoff": "Wednesday, September 9, 2026, Seattle Seahawks host New England Patriots, Lumen Field, 8:20 p.m. ET, NBC",
    "international_games": 9,
    "new_cities": ["Melbourne (Australia)", "Paris (France)", "Rio de Janeiro (Brazil)"],
    "week11_mexico": "San Francisco vs Minnesota, Sunday night, 8:20 p.m. ET, NBC, at Estadio Banorte",
    "week18": "three on Saturday, January 9; 13 on Sunday, January 10",
    "flexible_scheduling": "https://www.nfl.com/legal/flexible-scheduling-procedures",
}

# Naming irregularity documented on the flagged page (FLAG-A1) and normalised for
# reconciliation only. The corpus publishes the repository's established codes
# (ARI/LAR/WSH); the standings page prints AZ/LA/WAS. The mapping is printed on the site.
ALIASES = {"AZ": "ARI", "LA": "LAR", "WSH": "WAS"}

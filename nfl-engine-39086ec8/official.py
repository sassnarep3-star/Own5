"""Session 39086ec8 — official-source transcription module.

Every value that enters the engine from outside this repository is transcribed
here, once, with the URL it came from and the UTC date it was read. Nothing in
this file is inferred. Where an official page did not publish a value, the value
is None and the field is listed in `BLANKS` with the reason.

Read on 2026-11-14 (UTC) unless a row says otherwise.
"""

import datetime as _dt

CAPTURE_DATE = "2026-11-14"

URL = {
    "standings": "https://www.nfl.com/standings/",
    "standings_league": "https://www.nfl.com/standings/league/2026/REG",
    "week10": "https://www.nfl.com/schedules/2026/by-week/week-10",
    "injuries": "https://www.nfl.com/injuries/league/2026/reg10",
    "dk_nfl": "https://sportsbook.draftkings.com/leagues/football/nfl",
    "dk_general": "https://sportsbook.draftkings.com/help/general-betting-rules/general-rules",
    "dk_market": "https://sportsbook.draftkings.com/help/general-betting-rules/market-rules",
    "dk_cancelled": "https://sportsbook.draftkings.com/leagues/football/nfl",
    "dk_table": "https://sportsbook.draftkings.com/leagues/football/nfl",
    "det_dc": "https://www.detroitlions.com/team/depth-chart",
    "ne_dc": "https://www.patriots.com/team/depth-chart",
    "nyg_dc": "https://www.giants.com/team/depth-chart",
    "was_dc": "https://www.commanders.com/team/depth-chart",
    "nfl_teams": "https://www.nfl.com/teams/",
}

# --------------------------------------------------------------------------
# 1. 2026 REGULAR-SEASON STANDINGS  (nfl.com/standings/, read 2026-11-14)
#    Columns: W, L, T, PF, PA  — exactly as published.
#    PCT is deliberately NOT transcribed: it is recomputed by the engine with
#    the official NFL tie rule PCT = (W + 0.5*T) / (W + L + T), which was
#    verified to reproduce the published PCT for all 32 clubs.
# --------------------------------------------------------------------------
STANDINGS = {
    "BUF": (7, 1, 0, 256, 187),
    "NE":  (5, 4, 0, 211, 207),
    "NYJ": (2, 7, 0, 182, 223),
    "MIA": (1, 7, 0, 126, 200),
    "PIT": (6, 2, 0, 180, 144),
    "CIN": (6, 2, 0, 240, 175),
    "CLE": (5, 4, 0, 161, 196),
    "BAL": (4, 5, 0, 189, 236),
    "JAX": (6, 2, 0, 229, 121),
    "HOU": (3, 5, 0, 209, 192),
    "IND": (2, 7, 0, 184, 249),
    "TEN": (1, 7, 0, 144, 199),
    "DEN": (7, 2, 0, 198, 186),
    "KC":  (6, 2, 0, 202, 143),
    "LV":  (4, 5, 0, 238, 268),
    "LAC": (0, 8, 0, 121, 219),
    "NYG": (5, 3, 1, 203, 196),
    "DAL": (4, 5, 0, 246, 236),
    "WAS": (3, 5, 1, 196, 223),
    "PHI": (2, 7, 0, 148, 221),
    "CHI": (7, 2, 0, 241, 184),
    "DET": (6, 2, 0, 222, 189),
    "MIN": (6, 2, 0, 146, 116),
    "GB":  (6, 3, 0, 216, 191),
    "CAR": (3, 5, 0, 199, 219),
    "NO":  (3, 5, 0, 185, 216),
    "TB":  (3, 6, 0, 202, 178),
    "ATL": (3, 6, 0, 188, 223),
    "SF":  (7, 1, 0, 235, 156),
    "SEA": (5, 4, 0, 202, 162),
    "LA":  (5, 4, 0, 214, 181),
    "AZ":  (3, 6, 0, 178, 255),
}

# The repository mixes two club-code conventions. nfl.com's standings and
# schedule pages print LA and AZ; the inherited ledger and several desks print
# LAR and ARI. A join on the raw code silently DROPS two clubs (audit M2), so
# every cross-source join in this project goes through this map.
CLUB_ALIASES = {"LAR": "LA", "ARI": "AZ", "WSH": "WAS", "JAC": "JAX"}


def canon(code):
    """Return the nfl.com-published club code for any known alias."""
    code = str(code).strip().upper()
    return CLUB_ALIASES.get(code, code)


STANDINGS_NOTE = (
    "Transcribed verbatim from nfl.com/standings/ on 2026-11-14. Includes the "
    "Week 10 Thursday night final (WAS 24, NYG 21): NYG 5-3-1 and WAS 3-5-1. "
    "Two clubs (LA 5-4, AZ 3-6) are shown after 9 games without a bye marker; "
    "the standings page does not publish games played, so this is left as "
    "published rather than adjusted."
)

# --------------------------------------------------------------------------
# 2. WEEK 10 SLATE  (nfl.com/schedules/2026/by-week/week-10, read 2026-11-14)
#    (away, home, kickoff_as_published, network, neutral_site, nfl_game_url)
#    The Thursday game is FINAL as published: WAS 24, NYG 21.
# --------------------------------------------------------------------------
WEEK10 = [
    ("WAS", "NYG", "Thu 2026-11-12 8:15 PM ET", "Prime Video", False,
     "https://www.nfl.com/games/commanders-at-giants-2026-reg-10"),
    ("NE", "DET", "Sun 2026-11-15 9:30 AM ET", "FOX", True,
     "https://www.nfl.com/games/patriots-at-lions-2026-reg-10"),
    ("KC", "ATL", "Sun 2026-11-15 1:00 PM ET", "CBS", False,
     "https://www.nfl.com/games/chiefs-at-falcons-2026-reg-10"),
    ("HOU", "CLE", "Sun 2026-11-15 1:00 PM ET", "FOX", False,
     "https://www.nfl.com/games/texans-at-browns-2026-reg-10"),
    ("MIN", "GB", "Sun 2026-11-15 1:00 PM ET", "FOX", False,
     "https://www.nfl.com/games/vikings-at-packers-2026-reg-10"),
    ("MIA", "IND", "Sun 2026-11-15 1:00 PM ET", "CBS", False,
     "https://www.nfl.com/games/dolphins-at-colts-2026-reg-10"),
    ("CAR", "NO", "Sun 2026-11-15 1:00 PM ET", "FOX", False,
     "https://www.nfl.com/games/panthers-at-saints-2026-reg-10"),
    ("BUF", "NYJ", "Sun 2026-11-15 1:00 PM ET", "CBS", False,
     "https://www.nfl.com/games/bills-at-jets-2026-reg-10"),
    ("JAX", "TEN", "Sun 2026-11-15 1:00 PM ET", "FOX", False,
     "https://www.nfl.com/games/jaguars-at-titans-2026-reg-10"),
    ("LA", "AZ", "Sun 2026-11-15 4:05 PM ET", "CBS", False,
     "https://www.nfl.com/games/rams-at-cardinals-2026-reg-10"),
    ("SEA", "LV", "Sun 2026-11-15 4:05 PM ET", "CBS", False,
     "https://www.nfl.com/games/seahawks-at-raiders-2026-reg-10"),
    ("SF", "DAL", "Sun 2026-11-15 4:25 PM ET", "FOX", False,
     "https://www.nfl.com/games/49ers-at-cowboys-2026-reg-10"),
    ("PIT", "CIN", "Sun 2026-11-15 8:20 PM ET", "NBC", False,
     "https://www.nfl.com/games/steelers-at-bengals-2026-reg-10"),
    ("LAC", "BAL", "Mon 2026-11-16 8:15 PM ET", "ESPN", False,
     "https://www.nfl.com/games/chargers-at-ravens-2026-reg-10"),
]

WEEK10_BYES = ["CHI", "DEN", "PHI", "TB"]
WEEK10_THURSDAY_FINAL = {"away": "WAS", "home": "NYG", "away_pts": 24, "home_pts": 21}

# --------------------------------------------------------------------------
# 3. WEEK 10 INJURY REPORT  (nfl.com/injuries/league/2026/reg10, 2026-11-14)
#    Only the four clubs in the two games that were fully readable are
#    transcribed. Rows: (club, player, position, injury, practice, game_status)
#    Blank string == the official page published no value there.
# --------------------------------------------------------------------------
INJURIES = [
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
INJURY_SCOPE_NOTE = (
    "Only WAS, NYG, NE and DET were transcribed (two of the fourteen Week 10 "
    "games). The injury page has 8 content chunks; chunks 3-7 were not parsed "
    "for this session, so the register is deliberately partial and is NOT a "
    "league-wide injury count. Rows for other clubs must be captured before any "
    "league-wide injury statistic is quoted."
)

# --------------------------------------------------------------------------
# 4. OFFICIAL DEPTH CHARTS read 2026-11-14.
#    Each entry: position label as published -> ordered list of players.
#    An empty string means the chart left that column blank.
#    `unofficial` records the club's own disclaimer text where one was shown.
# --------------------------------------------------------------------------
DEPTH_CHARTS = {
    "DET": {
        "url": URL["det_dc"],
        "disclaimer": "Unofficial depth chart compiled by Lions Football Communications",
        "offense": [
            ("WR", ["Jameson Williams", "", "", ""]),
            ("WR", ["Amon-Ra St. Brown", "DeAndre Carter", "", ""]),
            ("LT", ["Penei Sewell", "", "", ""]),
            ("LG", ["Christian Mahogany", "Miles Frazier", "", ""]),
            ("C", ["Cade Mays", "Juice Scruggs", "", ""]),
            ("RG", ["Tate Ratledge", "Seth McLaughlin", "", ""]),
            ("RT", ["Blake Miller", "Larry Borom", "", ""]),
            ("TE", ["Sam LaPorta", "Brock Wright", "Tyler Conklin", "Jackson Meeks"]),
            ("WR", ["Isaac TeSlaa", "Tay Martin", "", ""]),
            ("QB", ["Jared Goff", "Joshua Dobbs", "", ""]),
            ("RB", ["Jahmyr Gibbs", "Sione Vaki", "Jacob Saylors", ""]),
        ],
        "defense": [
            ("EDGE", ["Aidan Hutchinson", "Derrick Moore", "Eric O'Neill", ""]),
            ("DL", ["Alim McNeill", "Skyler Gill-Howard", "Mekhi Wingo", ""]),
            ("DL", ["Tyleik Williams", "Levi Onwuzurike", "", ""]),
            ("EDGE", ["DJ Wonnum", "Tyler Lacy", "Ahmed Hassanein", ""]),
            ("LB", ["Derrick Barnes", "Joe Bachie", "", ""]),
            ("LB", ["Malcolm Rodriguez", "K.J. Britt", "", ""]),
            ("LB", ["Trevor Nowaske", "Amen Ogbongbemiga", "", ""]),
            ("CB", ["D.J. Reed", "Rock Ya-Sin", "Khalil Dorsey", "Nick Whiteside"]),
            ("CB", ["Roger McCreary", "Ennis Rakestraw Jr.", "Keith Abney II", ""]),
            ("S", ["Chuck Clark", "", "", ""]),
            ("S", ["Brian Branch", "Christian Izien", "", ""]),
        ],
    },
    "NE": {
        "url": URL["ne_dc"],
        "disclaimer": ("The 2026 depth chart is unofficial and is published by the writers of "
                       "Patriots.com. The depth chart reflects the opinions of the Patriots.com "
                       "writers and don't necessarily reflect those of the organization."),
        "offense": [
            ("WR", ["A.J. Brown", "Efton Chism III", "", ""]),
            ("LT", ["Will Campbell", "Dametrious Crownover", "Marcus Bryant", ""]),
            ("LG", ["Ben Brown", "Walter Rouse", "", ""]),
            ("C", ["Jared Wilson", "Ben Brown", "", ""]),
            ("RG", ["Matt Pryor", "Walter Rouse", "", ""]),
            ("RT", ["Morgan Moses", "Caleb Lomu", "", ""]),
            ("TE", ["Hunter Henry", "Eli Raridon", "Cameron Latu", ""]),
            ("WR", ["DeMario Douglas", "Kyle Williams", "", ""]),
            ("WR", ["Efton Chism III", "Kyle Williams", "", ""]),
            ("RB", ["Rhamondre Stevenson", "TreVeyon Henderson", "Corey Kiner", "Lan Larison"]),
        ],
        "defense": [],  # chunk 1 of 3 only; defense section not captured this session
    },
    "NYG": {
        "url": URL["nyg_dc"],
        "disclaimer": "",
        "offense": [
            ("WR", ["Malik Nabers", "Malachi Fields", "Jalin Hyatt", ""]),
            ("WR", ["Darnell Mooney", "Charlie Jones", "", ""]),
            ("LT", ["Andrew Thomas", "J.C. Davis", "", ""]),
            ("LG", ["Jon Runyan Jr.", "Aaron Stinnie", "Josh Sills", ""]),
            ("C", ["Bryan Hudson", "John Michael Schmitz Jr.", "", ""]),
            ("RG", ["Francis Mauigoa", "Aaron Stinnie", "", ""]),
            ("RT", ["Jermaine Eluemunor", "Marcus Mbow", "", ""]),
            ("TE", ["Isaiah Likely", "Theo Johnson", "Chris Manhertz", "Thomas Fidone II"]),
            ("QB", ["J.J. McCarthy", "Jameis Winston", "", ""]),
            ("FB", ["Patrick Ricard", "", "", ""]),
            ("RB", ["Cam Skattebo", "Devin Singletary", "Gregory Desrosiers", ""]),
        ],
        "defense": [
            ("DT", ["Shelby Harris", "Darius Alexander", "Bobby Jamison-Travis", ""]),
            ("NT", ["DJ Reader", "C.J. Okoye", "", ""]),
            ("DE", ["Darius Alexander", "", "", ""]),
            ("RUSH", ["Kayvon Thibodeaux", "Trace Ford", "", ""]),
            ("MLB", ["Micah McFadden", "Zaire Barnes", "", ""]),
            ("WLB", ["Arvell Reese", "Jack Kelly", "", ""]),
            ("SAM", ["Abdul Carter", "Kayvon Thibodeaux", "", ""]),
            ("CB", ["Deonte Banks", "Paulson Adebo", "Nikko Reed", ""]),
            ("SS", ["Tyler Nubin", "Jason Pinnock", "", ""]),
            ("FS", ["Jevon Holland", "Ar'Darius Washington", "Elijah Campbell", ""]),
            ("CB", ["Greg Newsome II", "Colton Hood", "", ""]),
            ("NB", ["Dru Phillips", "Nic Jones", "", ""]),
        ],
    },
    "WAS": {
        "url": URL["was_dc"],
        "disclaimer": "",
        "offense": [
            ("WR", ["Terry McLaurin", "Treylon Burks", "", ""]),
            ("LT", ["Brandon Coleman", "Andrew Wylie", "", ""]),
            ("LG", ["Chris Paul", "Tanoa Togiai", "", ""]),
            ("C", ["Nick Allegretti", "Matt Gulbin", "", ""]),
            ("RG", ["Sam Cosmi", "Tanoa Togiai", "", ""]),
            ("RT", ["Josh Conerly Jr.", "Andrew Wylie", "", ""]),
            ("TE", ["Chig Okonkwo", "Ben Sinnott", "", ""]),
            ("TE", ["John Bates", "Colson Yankoff", "", ""]),
            ("WR", ["Stefon Diggs", "Jaylin Lane", "", ""]),
            ("WR", ["Dyami Brown", "Antonio Williams", "Luke McCaffrey", ""]),
            ("QB", ["Jayden Daniels", "Marcus Mariota", "Athan Kaliakmanis", ""]),
            ("RB", ["Jacory Croskey-Merritt", "Rachaad White", "Austin Ekeler", ""]),
        ],
        "defense": [
            ("DL", ["Daron Payne", "", "", ""]),
            ("DL", ["Tim Settle", "Shy Tuttle", "", ""]),
            ("DL", ["Javon Kinlaw", "Charles Omenihu", "", ""]),
            ("OLB", ["Odafe Oweh", "Joshua Josephs", "", ""]),
            ("LB", ["Sonny Styles", "Kain Medrano", "", ""]),
            ("LB", ["Frankie Luvu", "", "Kain Medrano", ""]),
            ("OLB", ["K'Lavon Chaisson", "Dorance Armstrong", "Javontae Jean-Baptiste", ""]),
            ("CB", ["Amik Robertson", "Rasul Douglas", "", ""]),
            ("CB", ["Mike Sainristil", "Fabian Moreau", "", ""]),
            ("SS", ["Nick Cross", "Tyler Owens", "", ""]),
            ("FS", ["Jeremy Reaves", "Quan Martin", "Percy Butler", ""]),
        ],
    },
}


# --------------------------------------------------------------------------
# 5b. VERIFIED OPERATOR PRICES, 2026 Week 10 (FanDuel public event pages)
#     Read 2026-11-14. One capture point per game: the latest capture before
#     kickoff, stored as event="close" under the store's definition
#     ("the last capture before kickoff"), NOT a kickoff-time price.
#
#     Column order is exactly as the operator renders it: the LEFT block is the
#     away team, the RIGHT block is the home team.
#     Each tuple: (away, home, away_spread, away_spread_price,
#                  home_spread, home_spread_price,
#                  total, over_price, under_price,
#                  away_ml, home_ml, url)
#
#     WAS @ NYG is absent on purpose: it kicked off on 2026-11-12 and was a
#     final before this capture, so no pre-kickoff price could be read today.
#     It is published as MISSING, not back-filled (flag F-07).
# --------------------------------------------------------------------------
FANDUEL_WEEK10 = [
    ("NE", "DET", 2.5, 100, -2.5, -120, 49.5, -110, -110, 128, -152,
     "https://sportsbook.fanduel.com/football/nfl/new-england-patriots-@-detroit-lions-35605986"),
    ("KC", "ATL", -3.5, 100, 3.5, -120, 47.5, -105, -115, -172, 144,
     "https://sportsbook.fanduel.com/football/nfl/kansas-city-chiefs-@-atlanta-falcons-36275759"),
    ("HOU", "CLE", -4.5, -110, 4.5, -110, 40.5, -105, -115, -215, 180,
     "https://sportsbook.fanduel.com/football/nfl/houston-texans-@-cleveland-browns-36275760"),
    ("MIN", "GB", 3.0, -110, -3.0, -110, 42.5, -105, -115, 130, -154,
     "https://sportsbook.fanduel.com/football/nfl/minnesota-vikings-@-green-bay-packers-36275758"),
    ("MIA", "IND", 3.5, -105, -3.5, -115, 38.5, -105, -115, 176, -210,
     "https://sportsbook.fanduel.com/football/nfl/miami-dolphins-@-indianapolis-colts-36275761"),
    ("CAR", "NO", 1.5, 100, -1.5, -120, 48.5, -115, -105, 118, -138,
     "https://sportsbook.fanduel.com/football/nfl/carolina-panthers-@-new-orleans-saints-36275767"),
    ("BUF", "NYJ", -7.5, -110, 7.5, -110, 50.5, -115, -105, -460, 360,
     "https://sportsbook.fanduel.com/football/nfl/buffalo-bills-@-new-york-jets-36275763"),
    ("JAX", "TEN", -10.5, -110, 10.5, -110, 46.5, 100, -120, -670, 490,
     "https://sportsbook.fanduel.com/football/nfl/jacksonville-jaguars-@-tennessee-titans-36275762"),
    ("LA", "AZ", -9.5, -110, 9.5, -110, 39.5, -110, -110, -520, 400,
     "https://sportsbook.fanduel.com/football/nfl/los-angeles-rams-@-arizona-cardinals-36275766"),
    ("SEA", "LV", -6.5, -110, 6.5, -110, 40.5, -110, -110, -300, 245,
     "https://sportsbook.fanduel.com/football/nfl/seattle-seahawks-@-las-vegas-raiders-36275769"),
    ("SF", "DAL", -4.5, -105, 4.5, -115, 55.5, -115, -105, -220, 184,
     "https://sportsbook.fanduel.com/football/nfl/san-francisco-49ers-@-dallas-cowboys-36275764"),
    ("PIT", "CIN", 3.5, -110, -3.5, -110, 49.5, -105, -115, 150, -178,
     "https://sportsbook.fanduel.com/football/nfl/pittsburgh-steelers-@-cincinnati-bengals-36275765"),
    ("LAC", "BAL", 4.5, -110, -4.5, -110, 38.5, -115, -105, 188, -225,
     "https://sportsbook.fanduel.com/football/nfl/los-angeles-chargers-@-baltimore-ravens-36275768"),
]

# --------------------------------------------------------------------------
# 5. OPERATOR MARKET ACCESS PROBE (2026-11-14)
#    What the public, unauthenticated operator pages actually served.
# --------------------------------------------------------------------------
MARKET_PROBE = {
    "url": URL["dk_nfl"],
    "read_on": CAPTURE_DATE,
    "price_table_served": False,
    "games_with_price_on_page": None,
    "what_was_served": (
        "News cards and an 'Understanding NFL Odds' explainer. Example rows in the "
        "explainer (New England -14.5 / -120 vs Kansas City +14.5 / +150) are "
        "illustrative teaching values, not a 2026 Week 10 market, and are NOT used "
        "as a price anywhere in this project."
    ),
    "conclusion": (
        "No spread, total or moneyline for any 2026 Week 10 game could be read from "
        "an unauthenticated official operator page in this environment. Opening and "
        "closing numbers therefore cannot be sourced officially by this session, and "
        "the price store is shipped empty-by-design with the capture protocol defined."
    ),
}

# --------------------------------------------------------------------------
# 6. CLOSING-PRICE OPERATOR RULES (nfl.com-linked operator house rules)
# --------------------------------------------------------------------------
CLOSING_RULES = {
    "url": URL["dk_general"],
    "read_on": CAPTURE_DATE,
    "rules": {
        "price_1": (
            "Definition 04(b): an 'Error' includes a bet accepted at odds 'meaningfully "
            "different, at the time the bet was accepted', from odds offered in the US "
            "for the same bet by similarly situated books. Implication: a captured number "
            "is only a settlement-grade price if the operator did not later void it."
        ),
        "price_2": (
            "Definition 04(2)(7): a bet accepted after an announcement that affects the "
            "odds, and before the platform repriced, is an Error. Implication: the price "
            "must be captured AFTER the last injury/lineup announcement, not before."
        ),
    },
    "note": (
        "The rules text read is the Virginia house rules as served publicly; the same "
        "wording may differ by state. The operator's page itself is the authority and "
        "its state-specific version must be archived with each snapshot."
    ),
}

# --------------------------------------------------------------------------
# 7. CLOSING-LINE ARITHMETIC DEMONSTRATION
#    Two-leg same-game market with a two-way de-vig, to show what a "market total
#    probability" looks like before any model exists. This is an example of the
#    METHOD, using the only prices on the operator page (the explainer rows).
# --------------------------------------------------------------------------
EXAMPLE_MARKET = {
    "label": "Operator explainer example (NOT a 2026 Week 10 price)",
    "spread": {"fav": "NE", "dog": "KC", "fav_line": -14.5, "dog_line": 14.5,
               "fav_price": -120, "dog_price": 150},
    "total": {"line": 47.5, "over_price": -110, "under_price": -110},
    "source": URL["dk_nfl"],
}

# --------------------------------------------------------------------------
# 8. Things that are deliberately blank, with the reason. Rendered verbatim.
# --------------------------------------------------------------------------
BLANKS = [
    ("Opening spread / total / moneyline, any 2026 Week 10 game",
     "The first capture of any price in this project is 2026-11-14; an opening "
     "number requires a capture made when the market opened, which does not exist. "
     "Not reconstructed from memory or from a second-hand quote.",
     "P-01, F-01"),
    ("WAS @ NYG price, any market",
     "Kicked off 2026-11-12 and was final before the 2026-11-14 capture.",
     "P-01, F-07"),
    ("Any prop line or prop price",
     "Prop markets are named on the operator page but their numbers are not in the "
     "readable text (MARKET_PROBE.prop_prices_served = False).",
     "P-03, F-03"),
    ("League-wide injury rows",
     "Only 4 of 32 clubs transcribed; injury page chunks 3-7 not parsed.",
     "F-04"),
    ("Defensive depth for NE, and both units for the other 28 clubs",
     "Only 4 club charts read; NE defense section not captured.",
     "F-05"),
    ("Any claim that a strategy is skill-based",
     "Requires a verified closing price (CLV) which does not exist in this repo.",
     "P-01, F-06"),
]

# --------------------------------------------------------------------------
# 5c. What the probe above now records, after the event pages were read.
# --------------------------------------------------------------------------
MARKET_PROBE["price_table_served"] = True
MARKET_PROBE["games_with_price_on_page"] = 13
MARKET_PROBE["what_was_served"] = (
    "Each game's public event page served a readable 'Game Lines' block: spread "
    "with both prices, total with both prices, and both moneylines. 13 of the 14 "
    "Week 10 games were read this way; WAS @ NYG had already kicked off."
)
MARKET_PROBE["conclusion"] = (
    "Game-level prices ARE officially readable and are now stored (13 games, one "
    "capture point each, 2026-11-14). Two things are still NOT obtainable: "
    "(1) an OPENING price — the first capture only exists from today, so the "
    "opening column is published blank rather than reconstructed; "
    "(2) PLAYER PROP lines and prices — the prop markets are named on the page but "
    "their numbers are not in the readable text, so every prop leg stays UNPRICED."
)
MARKET_PROBE["prop_prices_served"] = False
MARKET_PROBE["prop_note"] = (
    "Prop market NAMES render (e.g. 'Patrick Mahomes - Passing Yds') but no line or "
    "price does. Prop combos therefore cannot be priced from this source and are "
    "excluded from any ROI calculation rather than modelled at assumed lines."
)
MARKET_PROBE["region_note"] = (
    "The price page does not publish which state's rules apply to the served "
    "numbers; its footer carried New Jersey responsible-gaming assets. The store "
    "records source_region as US-UNSPECIFIED for every row and this is flagged "
    "(F-08) because settlement rules and void rights are state-specific."
)


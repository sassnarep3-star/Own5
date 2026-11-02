#!/usr/bin/env python3
"""Seed all Own5 data tables (CSV) deterministically.

Every factual value in these CSVs was verified on 2026-11-02 against the
official source listed in the row's `source_url` column (see data/sources.csv).
Values that could NOT be confirmed from an official source are left EMPTY and
logged in data/flagged.csv — never inferred.

Run:  python3 tools/seed_data.py
"""
import csv, os

ROOT = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(ROOT, exist_ok=True)
ACCESSED = "2026-11-02"

def write(name, header, rows):
    path = os.path.join(ROOT, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path} ({len(rows)} rows)")

# ---------------------------------------------------------------- sources
S = {
 "S01": ("NFL.com — official league site", "official NFL", "https://www.nfl.com/",
         "League news, standings, schedules, stats, injuries, teams"),
 "S02": ("NFL Media — football information (media.nfl.com)", "official NFL", "https://media.nfl.com/",
         "Official schedule announcements; official statistics reports courtesy of Elias Sports Bureau"),
 "S03": ("NFL Football Operations (operations.nfl.com)", "official NFL", "https://operations.nfl.com/",
         "Official Playing Rules, schedule-making, Next Gen Stats technology"),
 "S04": ("NFL Standings (2026, through Week 8)", "official NFL", "https://www.nfl.com/standings/",
         "W-L-T, PCT, PF, PA, NET PTS, streak for all 32 teams; snapshot accessed 2026-11-02"),
 "S05": ("NFL Schedules 2026", "official NFL", "https://www.nfl.com/schedules",
         "Week-by-week matchups, times, networks, results; bye teams; weather note on game cards"),
 "S06": ("NFL official injury report (Week 8, 2026)", "official NFL", "https://www.nfl.com/injuries/",
         "Official weekly injury report: player, position, injury, practice status, game status"),
 "S07": ("NFL player stats 2026", "official NFL", "https://www.nfl.com/stats/player-stats/",
         "Official 2026 player stat leaders (passing, rushing, receiving, ...), Elias Sports Bureau data"),
 "S08": ("NFL team stats 2026", "official NFL", "https://www.nfl.com/stats/team-stats/",
         "Official 2026 team offense/defense/special-teams stats"),
 "S09": ("NFL teams directory", "official NFL", "https://www.nfl.com/teams/",
         "All 32 clubs with links to official club websites"),
 "S10": ("NFL tiebreaking procedures", "official NFL", "https://www.nfl.com/standings/tie-breaking-procedures",
         "Official tiebreaking steps; tie game = half win / half loss"),
 "S11": ("2026 NFL schedule announced (May 14, 2026)", "official NFL",
         "https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced",
         "18-week, 272-game 2026 schedule; 17 games + 3 preseason per team; byes Weeks 5-14; kickoff Sept 9, 2026 Seattle; Week 18 Jan 9-10; 9 international games"),
 "S12": ("2026 schedule release: every team's bye week", "official NFL",
         "https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week",
         "Per-team bye weeks for 2026 (Weeks 5-14, none in Week 12)"),
 "S13": ("Owners approve expanding postseason to 14 teams", "official NFL",
         "https://www.nfl.com/news/owners-approve-expanding-postseason-to-14-teams-0ap3000001107961",
         "14-team playoff format since 2020; only No.1 seeds get a bye; 2v7, 3v6, 4v5 wild card matchups"),
 "S14": ("NFL announces 2026 salary cap set at $301.2 million per team", "official NFL",
         "https://www.nfl.com/news/nfl-announces-2026-salary-cap-set-at-301-2-million-per-team",
         "2026 cap $301.2M (first time over $300M); 2025 cap $279.2M; 2024 cap $255.4M; 2022 cap $208.2M"),
 "S15": ("2026 Official Playing Rules of the NFL (rulebook)", "official NFL",
         "https://operations.nfl.com/rules-officiating/2026-nfl-rulebook",
         "Rules in effect for 2026 season; Rule 4 game timing (60 min, four 15-min periods); Rule 16 overtime. PDF: https://media.nfl.com/content/dam/communications/Official%20Playing%20Rules/2026%20Official%20Playing%20Rules.pdf"),
 "S16": ("NFL Next Gen Stats technology", "official NFL",
         "https://operations.nfl.com/gameday/technology/nfl-next-gen-stats",
         "Player/ball tracking in every venue (Zebra Technologies, Wilson, AWS); location/speed/acceleration captured 10x per second; 200+ data points per play"),
 "S17": ("NFL stat corrections (Elias Sports Bureau)", "official NFL",
         "https://fantasy.nfl.com/research/statcorrections",
         "Official stat corrections released by the NFL League Office and the official statistician of the NFL, Elias Sports Bureau"),
 "S18": ("Making the schedule (operations.nfl.com)", "official NFL",
         "https://operations.nfl.com/calendar-events/nfl-schedule/making-the-schedule",
         "Scheduling formula: 17 games per team, 272 matchups, one bye; every team plays every division in the other conference once every four years"),
 "S19": ("DraftKings Sportsbook — NFL lines & bet types", "official sportsbook operator",
         "https://sportsbook.draftkings.com/leagues/football/nfl",
         "Operator definitions of NFL spread, moneyline, totals (over/under), live betting, parlays, props"),
 "S20": ("FanDuel — NFL betting guide", "official sportsbook operator",
         "https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl",
         "Operator definitions of spread, push, parlay, same game parlay, teaser; key margins 3 and 7 in NFL"),
 "S21": ("FanDuel — what is a parlay bet", "official sportsbook operator",
         "https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet",
         "Parlay = 2+ legs, all must win; SGP = legs from one game; SGP+ = multiple SGPs across games; correlated/duplicate legs not allowed unless offered"),
 "S22": ("FanDuel Sportsbook — NFL odds & grading FAQ", "official sportsbook operator",
         "https://sportsbook.fanduel.com/navigation/nfl",
         "Live NFL lines page; grading FAQ: OT counts for spread/ML/totals; tie after OT -> moneyline void, spread/total settled (push if on number); postponed before kickoff -> void; relocated but played on date -> action"),
 "S23": ("FanDuel Sportsbook house rules (Ontario)", "official sportsbook operator (regulator-filed)",
         "https://www.fanduel.com/fanduel-sportsbook-house-rules-on",
         "Parlay: all selections must win; void leg -> re-priced; whole-number spread/total landing on number -> refunded; correlated selections not permitted unless offered (e.g., SGP); OT counts for handicap/ML/totals"),
 "S24": ("BetMGM house rules approved by Massachusetts Gaming Commission", "official regulator-approved operator rules",
         "https://massgaming.com/wp-content/uploads/BetMGM-House-Rules-8.14.25.pdf",
         "Football results official after 55 minutes of play; postponed/cancelled game handling; same-game-parlay variants (24h/48h rules)"),
 "S25": ("NCPG — National Problem Gambling Helpline", "official responsible-gambling resource",
         "https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/",
         "1-800-GAMBLER (1-800-426-2537), text 800GAM, chat; 24/7, confidential, all 50 states"),
 "S26": ("NFL announces tri-exclusive sports betting partners", "official NFL",
         "https://www.nfl.com/news/nfl-announces-tri-exclusive-sports-betting-partners",
         "Caesars, DraftKings, FanDuel are Official Sports Betting Partners of the NFL; all three use the NFL's official league data feed"),
 "S27": ("NFL legal — flexible scheduling procedures", "official NFL",
         "https://www.nfl.com/legal/flexible-scheduling-procedures",
         "Flexible scheduling rules referenced on the 2026 schedule page (Weeks 16-18 Saturday designations)"),
}
write("sources.csv",
      ["source_id","name","type","url","what_it_verifies","accessed_on"],
      [[k, v[0], v[1], v[2], v[3], ACCESSED] for k, v in S.items()])

# ---------------------------------------------------------------- league facts
LF = [
 ("LF01","Structure","Teams in the NFL","32","teams","S09","https://www.nfl.com/teams/"),
 ("LF02","Structure","Conferences","2 (AFC, NFC)","","S04","https://www.nfl.com/standings/"),
 ("LF03","Structure","Divisions per conference","4 (East, North, South, West)","","S04","https://www.nfl.com/standings/"),
 ("LF04","Structure","Teams per division","4","","S04","https://www.nfl.com/standings/"),
 ("LF05","Season","Regular-season games per team","17","games","S11","https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"),
 ("LF06","Season","Regular-season weeks","18","weeks","S11","https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"),
 ("LF07","Season","Total regular-season games (2026)","272","games","S11","https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"),
 ("LF08","Season","Bye weeks per team","1","","S11","https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"),
 ("LF09","Season","Bye-week window (2026)","Weeks 5-14 (no byes in Week 12)","","S12","https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week"),
 ("LF10","Season","Preseason games per team (2026)","3","games","S11","https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"),
 ("LF11","Season","2026 regular-season kickoff","Wednesday, September 9, 2026, Seattle","","S11","https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"),
 ("LF12","Season","2026 Week 18 dates","Saturday Jan 9 - Sunday Jan 10, 2027; all 16 games are division games","","S11","https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"),
 ("LF13","Season","International regular-season games (2026)","9 (most ever in a season)","games","S11","https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"),
 ("LF14","Schedule formula","Each team plays every division in the other conference once every four years","","","S18","https://operations.nfl.com/calendar-events/nfl-schedule/making-the-schedule"),
 ("LF15","Playoffs","Playoff teams","14 (7 per conference), format since 2020 season","teams","S13","https://www.nfl.com/news/owners-approve-expanding-postseason-to-14-teams-0ap3000001107961"),
 ("LF16","Playoffs","First-round bye","Only the No. 1 seed in each conference","","S13","https://www.nfl.com/news/owners-approve-expanding-postseason-to-14-teams-0ap3000001107961"),
 ("LF17","Playoffs","Wild Card matchups","No.2 hosts No.7; No.3 hosts No.6; No.4 hosts No.5 (per conference)","","S13","https://www.nfl.com/news/owners-approve-expanding-postseason-to-14-teams-0ap3000001107961"),
 ("LF18","Standings","Tie game value","Counts as one-half win and one-half loss for both clubs","","S10","https://www.nfl.com/standings/tie-breaking-procedures"),
 ("LF19","Finance","2026 salary cap","$301.2 million per club (first time above $300M)","USD","S14","https://www.nfl.com/news/nfl-announces-2026-salary-cap-set-at-301-2-million-per-team"),
 ("LF20","Finance","2025 salary cap (comparison)","$279.2 million per club (+$22M to 2026)","USD","S14","https://www.nfl.com/news/nfl-announces-2026-salary-cap-set-at-301-2-million-per-team"),
 ("LF21","Rules","Length of an NFL game","60 minutes, four periods of 15 minutes each (Rule 4)","minutes","S15","https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"),
 ("LF22","Rules","Overtime","Governed by Rule 16 (Overtime Procedures), 2026 Official Playing Rules","","S15","https://operations.nfl.com/rules-officiating/2026-nfl-rulebook"),
 ("LF23","Data","Next Gen Stats tracking rate","Player location/speed/acceleration captured 10 times per second; 200+ data points per play","","S16","https://operations.nfl.com/gameday/technology/nfl-next-gen-stats"),
 ("LF24","Data","Official statistician of the NFL","Elias Sports Bureau; official stat corrections released by NFL League Office","","S17","https://fantasy.nfl.com/research/statcorrections"),
 ("LF25","Betting data","NFL Official Sports Betting Partners","Caesars, DraftKings, FanDuel; all use the NFL's official league data feed","","S26","https://www.nfl.com/news/nfl-announces-tri-exclusive-sports-betting-partners"),
 ("LF26","Responsible gambling","National Problem Gambling Helpline","1-800-GAMBLER (1-800-426-2537); text 800GAM; chat via NCPG; 24/7 confidential","","S25","https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/"),
]
write("league-facts.csv",
      ["fact_id","category","fact","value","unit","source_id","source_url","verified_on","status"],
      [[r[0],r[1],r[2],r[3],r[4],r[5],r[6],ACCESSED,"verified"] for r in LF])

# ---------------------------------------------------------------- teams
TEAMS = [
 # name, abbr, conf, div, site, bye week 2026
 ("Arizona Cardinals","ARI","NFC","West","https://www.azcardinals.com/",14),
 ("Atlanta Falcons","ATL","NFC","South","https://www.atlantafalcons.com/",11),
 ("Baltimore Ravens","BAL","AFC","North","https://www.baltimoreravens.com/",13),
 ("Buffalo Bills","BUF","AFC","East","https://www.buffalobills.com/",7),
 ("Carolina Panthers","CAR","NFC","South","https://www.panthers.com/",5),
 ("Chicago Bears","CHI","NFC","North","https://www.chicagobears.com/",10),
 ("Cincinnati Bengals","CIN","AFC","North","https://www.bengals.com/",6),
 ("Cleveland Browns","CLE","AFC","North","https://www.clevelandbrowns.com/",11),
 ("Dallas Cowboys","DAL","NFC","East","https://www.dallascowboys.com/",14),
 ("Denver Broncos","DEN","AFC","West","https://www.denverbroncos.com/",10),
 ("Detroit Lions","DET","NFC","North","https://www.detroitlions.com/",6),
 ("Green Bay Packers","GB","NFC","North","https://www.packers.com/",11),
 ("Houston Texans","HOU","AFC","South","https://www.houstontexans.com/",8),
 ("Indianapolis Colts","IND","AFC","South","https://www.colts.com/",13),
 ("Jacksonville Jaguars","JAX","AFC","South","https://www.jaguars.com/",7),
 ("Kansas City Chiefs","KC","AFC","West","https://www.chiefs.com/",5),
 ("Las Vegas Raiders","LV","AFC","West","https://www.raiders.com/",13),
 ("Los Angeles Chargers","LAC","AFC","West","https://www.chargers.com/",7),
 ("Los Angeles Rams","LAR","NFC","West","https://www.therams.com/",11),
 ("Miami Dolphins","MIA","AFC","East","https://www.miamidolphins.com/",6),
 ("Minnesota Vikings","MIN","NFC","North","https://www.vikings.com/",6),
 ("New England Patriots","NE","AFC","East","https://www.patriots.com/",11),
 ("New Orleans Saints","NO","NFC","South","https://www.neworleanssaints.com/",8),
 ("New York Giants","NYG","NFC","East","https://www.giants.com/",8),
 ("New York Jets","NYJ","AFC","East","https://www.nyjets.com/",13),
 ("Philadelphia Eagles","PHI","NFC","East","https://www.philadelphiaeagles.com/",10),
 ("Pittsburgh Steelers","PIT","AFC","North","https://www.steelers.com/",9),
 ("San Francisco 49ers","SF","NFC","West","https://www.49ers.com/",8),
 ("Seattle Seahawks","SEA","NFC","West","https://www.seahawks.com/",11),
 ("Tampa Bay Buccaneers","TB","NFC","South","https://www.buccaneers.com/",10),
 ("Tennessee Titans","TEN","AFC","South","https://www.tennesseetitans.com/",9),
 ("Washington Commanders","WAS","NFC","East","https://www.commanders.com/",7),
]
write("teams.csv",
      ["team","abbr","conference","division","official_site","bye_week_2026",
       "nfl_profile","source_id","source_url","verified_on","status"],
      [[t[0],t[1],t[2],t[3],t[4],t[5],
        f"https://www.nfl.com/teams/{t[0].lower().replace(' ','-')}/",
        "S09","https://www.nfl.com/teams/",ACCESSED,"verified"] for t in TEAMS])
# bye weeks cross-checked against S12
write("bye-weeks-2026.csv",
      ["week","teams_on_bye","source_id","source_url","verified_on","status"],
      [[5,"Carolina Panthers; Kansas City Chiefs","S12","https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week",ACCESSED,"verified"],
       [6,"Cincinnati Bengals; Detroit Lions; Miami Dolphins; Minnesota Vikings","S12","https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week",ACCESSED,"verified"],
       [7,"Buffalo Bills; Jacksonville Jaguars; Los Angeles Chargers; Washington Commanders","S12","https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week",ACCESSED,"verified"],
       [8,"Houston Texans; New Orleans Saints; New York Giants; San Francisco 49ers","S12","https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week",ACCESSED,"verified"],
       [9,"Pittsburgh Steelers; Tennessee Titans","S12","https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week",ACCESSED,"verified"],
       [10,"Chicago Bears; Denver Broncos; Philadelphia Eagles; Tampa Bay Buccaneers","S12","https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week",ACCESSED,"verified"],
       [11,"Atlanta Falcons; Cleveland Browns; Green Bay Packers; Los Angeles Rams; New England Patriots; Seattle Seahawks","S12","https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week",ACCESSED,"verified"],
       [12,"(none - every club plays)","S12","https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week",ACCESSED,"verified"],
       [13,"Baltimore Ravens; Indianapolis Colts; Las Vegas Raiders; New York Jets","S12","https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week",ACCESSED,"verified"],
       [14,"Arizona Cardinals; Dallas Cowboys","S12","https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week",ACCESSED,"verified"]])

# ---------------------------------------------------------------- standings snapshot (nfl.com/standings/, accessed 2026-11-02, through Week 8)
STAND = [
 ("Buffalo Bills","BUF","AFC","East",6,1,0,0.857,233,181,52,"3W"),
 ("New England Patriots","NE","AFC","East",5,3,0,0.625,184,162,22,"1W"),
 ("New York Jets","NYJ","AFC","East",2,6,0,0.250,170,188,-18,"3L"),
 ("Miami Dolphins","MIA","AFC","East",1,6,0,0.143,117,181,-64,"1L"),
 ("Pittsburgh Steelers","PIT","AFC","North",6,2,0,0.750,180,144,36,"4W"),
 ("Cincinnati Bengals","CIN","AFC","North",5,2,0,0.714,206,158,48,"3W"),
 ("Cleveland Browns","CLE","AFC","North",5,3,0,0.625,139,173,-34,"1L"),
 ("Baltimore Ravens","BAL","AFC","North",4,4,0,0.500,179,203,-24,"3L"),
 ("Jacksonville Jaguars","JAX","AFC","South",5,2,0,0.714,196,111,85,"1W"),
 ("Houston Texans","HOU","AFC","South",2,5,0,0.286,165,170,-5,"1L"),
 ("Indianapolis Colts","IND","AFC","South",2,6,0,0.250,161,222,-61,"4L"),
 ("Tennessee Titans","TEN","AFC","South",1,7,0,0.125,144,199,-55,"2L"),
 ("Denver Broncos","DEN","AFC","West",6,2,0,0.750,172,165,7,"4W"),
 ("Kansas City Chiefs","KC","AFC","West",5,2,0,0.714,167,131,36,"2L"),
 ("Las Vegas Raiders","LV","AFC","West",4,4,0,0.500,221,230,-9,"1W"),
 ("Los Angeles Chargers","LAC","AFC","West",0,7,0,0.000,99,175,-76,"7L"),
 ("New York Giants","NYG","NFC","East",4,2,1,0.643,163,161,2,"1W"),
 ("Dallas Cowboys","DAL","NFC","East",3,5,0,0.375,219,213,6,"1L"),
 ("Washington Commanders","WAS","NFC","East",2,4,1,0.357,159,182,-23,"1W"),
 ("Philadelphia Eagles","PHI","NFC","East",2,6,0,0.250,137,202,-65,"6L"),
 ("Minnesota Vikings","MIN","NFC","North",6,1,0,0.857,140,93,47,"1L"),
 ("Detroit Lions","DET","NFC","North",5,2,0,0.714,203,180,23,"3W"),
 ("Chicago Bears","CHI","NFC","North",5,2,0,0.714,180,143,37,"2W"),
 ("Green Bay Packers","GB","NFC","North",5,3,0,0.625,171,164,7,"1W"),
 ("Carolina Panthers","CAR","NFC","South",3,4,0,0.429,178,193,-15,"2L"),
 ("Tampa Bay Buccaneers","TB","NFC","South",3,5,0,0.375,178,151,27,"2W"),
 ("Atlanta Falcons","ATL","NFC","South",3,5,0,0.375,171,189,-18,"1L"),
 ("New Orleans Saints","NO","NFC","South",2,5,0,0.286,162,194,-32,"1L"),
 ("San Francisco 49ers","SF","NFC","West",6,1,0,0.857,197,139,58,"1L"),
 ("Seattle Seahawks","SEA","NFC","West",4,3,0,0.571,168,125,43,"1W"),
 ("Los Angeles Rams","LAR","NFC","West",4,4,0,0.500,194,168,26,"2W"),
 ("Arizona Cardinals","AZ","NFC","West",3,5,0,0.375,175,238,-63,"1W"),
]
rows = []
for t in STAND:
    gp = t[4]+t[5]+t[6]
    rows.append([t[0],t[1],t[2],t[3],t[4],t[5],t[6],gp,t[7],t[8],t[9],t[10],t[11],
                 "S04","https://www.nfl.com/standings/",ACCESSED,"verified"])
write("standings-2026-wk8.csv",
      ["team","abbr","conference","division","W","L","T","GP","PCT","PF","PA","NET","STRK",
       "source_id","source_url","snapshot_on","status"], rows)

# ---------------------------------------------------------------- Week 8 results (nfl.com/schedules, accessed 2026-11-02)
WK8 = [
 ("2026-REG-8","Thu Oct 29, 8:15 PM","Carolina Panthers","at","Green Bay Packers",19,27,"Final","Prime Video","https://www.nfl.com/games/panthers-at-packers-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 1:00 PM","Baltimore Ravens","at","Buffalo Bills",10,36,"Final","CBS","https://www.nfl.com/games/ravens-at-bills-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 1:00 PM","Tennessee Titans","at","Cincinnati Bengals",36,43,"Final","CBS","https://www.nfl.com/games/titans-at-bengals-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 1:00 PM","Arizona Cardinals","at","Dallas Cowboys",33,30,"Final","","https://www.nfl.com/games/cardinals-at-cowboys-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 1:00 PM","Minnesota Vikings","at","Detroit Lions",15,19,"Final","","https://www.nfl.com/games/vikings-at-lions-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 1:00 PM","Indianapolis Colts","at","Jacksonville Jaguars",7,42,"Final","CBS","https://www.nfl.com/games/colts-at-jaguars-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 1:00 PM","Las Vegas Raiders","at","New York Jets",38,33,"Final","","https://www.nfl.com/games/raiders-at-jets-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 1:00 PM","Cleveland Browns","at","Pittsburgh Steelers",6,27,"Final","CBS","https://www.nfl.com/games/browns-at-steelers-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 1:00 PM","Atlanta Falcons","at","Tampa Bay Buccaneers",0,16,"Final","","https://www.nfl.com/games/falcons-at-buccaneers-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 4:25 PM","Los Angeles Chargers","at","Los Angeles Rams",9,24,"Final","FOX","https://www.nfl.com/games/chargers-at-rams-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 4:25 PM","Kansas City Chiefs","at","Denver Broncos",24,28,"Final","CBS","https://www.nfl.com/games/chiefs-at-broncos-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 4:25 PM","New England Patriots","at","Miami Dolphins",24,19,"Final","CBS","https://www.nfl.com/games/patriots-at-dolphins-2026-reg-8"),
 ("2026-REG-8","Sun Nov 1, 8:20 PM (SNF)","Philadelphia Eagles","at","Washington Commanders",10,27,"Final","","https://www.nfl.com/games/eagles-at-commanders-2026-reg-8"),
 ("2026-REG-8","Mon Nov 2, 8:15 PM (MNF)","Chicago Bears","at","Seattle Seahawks","","","Scheduled as of 2026-11-02; game card shows weather: Clear, night","ESPN","https://www.nfl.com/games/bears-at-seahawks-2026-reg-8"),
]
write("week8-2026-results.csv",
      ["season_week","kickoff","away","at","home","away_pts","home_pts","status","network","source_id","source_url","verified_on","row_status"],
      [[r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],"S05","https://www.nfl.com/schedules",ACCESSED,
        "verified" if r[7]=="Final" else "verified (status only; score blank until played)"] for r in WK8])

# ---------------------------------------------------------------- player passing leaders (nfl.com/stats/player-stats/, 2026 REG, sorted by passing yards desc)
PASS = [
 (1,"Jordan Love",2246),(2,"Matthew Stafford",2146),(3,"Kirk Cousins",2124),(4,"Joe Burrow",2115),
 (5,"Dak Prescott",2046),(6,"Drake Maye",1983),(7,"Jared Goff",1964),(8,"Bryce Young",1921),
 (9,"Geno Smith",1913),(10,"Aaron Rodgers",1871),
]
write("player-passing-2026.csv",
      ["rank","player","passing_yards","season","stat_window","source_id","source_url","verified_on","status"],
      [[p[0],p[1],p[2],2026,"REG through Week 8 (as displayed 2026-11-02)","S07",
        "https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc",
        ACCESSED,"verified"] for p in PASS])

# ---------------------------------------------------------------- bet types (official operator sources)
BT = [
 ("BT01","Point spread","Wager on whether a team wins by more than a set number of points (favorite, minus) or loses by fewer / wins outright (underdog, plus). Half-point spreads prevent a push.","DraftKings example: NE -14.5 wins if NE wins by 15+; KC +14.5 wins if KC wins or loses by 14 or fewer. Whole-number spread landing exactly on the number = push, stake refunded.","S19","https://sportsbook.draftkings.com/leagues/football/nfl"),
 ("BT02","Moneyline","Wager on which team wins the game outright; margin does not matter.","Example sheet: NE -200 vs KC +200. If game ends tied after OT, moneyline wagers are void and stakes refunded (FanDuel FAQ).","S19; S22","https://sportsbook.draftkings.com/leagues/football/nfl"),
 ("BT03","Total (over/under)","Wager on combined points of both teams. Over wins if combined score is above the total; under if below. Whole-number total landing on the number = push.","Example: total 47.5 -> over wins at 48+, under at 47 or fewer. FanDuel notes these markets are powered by official NFL data.","S19; S22","https://sportsbook.draftkings.com/leagues/football/nfl"),
 ("BT04","Parlay","Combines two or more individual bets into one wager; every selection (leg) must win. Minimum two legs. Can mix spreads, moneylines, totals and eligible props across one or multiple games.","Void leg in a parlay -> remaining legs re-priced (house rules). Correlated selections are not permitted unless explicitly offered (e.g., as SGP); if accepted in error the book may void or settle as singles.","S19; S21; S23","https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet"),
 ("BT05","Same Game Parlay (SGP)","Parlay combining multiple bets from the SAME game (player props, spreads, totals). Sportsbooks build correlation assumptions into the odds.","SGP+ combines multiple SGPs across different games. One missed leg loses the whole bet.","S20; S21","https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl"),
 ("BT06","Teaser","Adjusts spread or total by a set number of points (typically 6) across multiple legs in exchange for reduced odds. Needs at least two legs; all legs must win.","FanDuel guide: most common NFL margins of victory are 3 and 7, so moving e.g. -8.5 to -2.5 crosses both key numbers.","S20","https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl"),
 ("BT07","Player prop","Wager on a specific player/team performance (e.g., passing yards, rushing yards, TDs, sacks).","If a player is not listed as active by the official league scoring source, the prop is void (BetMGM rules). Official stats: Elias Sports Bureau / NFL.com.","S19; S24; S17","https://sportsbook.draftkings.com/leagues/football/nfl"),
 ("BT08","Live (in-play) betting","Wagers placed after a game has started; markets may include game spread, moneyline, total, quarter/half, eligible player props; odds update continuously.","Example from DraftKings NFL page.","S19","https://sportsbook.draftkings.com/leagues/football/nfl"),
 ("BT09","Round robin","Builds multiple smaller parlays from one larger selection pool; you are covered if some but not all picks win.","FanDuel NFL guide.","S20","https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl"),
 ("BT10","Grading — overtime","Full-game spread, moneyline and totals are graded on the final official score INCLUSIVE of overtime (FanDuel FAQ; FanDuel house rules; BetMGM: OT included).","Quarter-specific markets do not include OT; second-half markets include OT if played (house rules).","S22; S23; S24","https://sportsbook.fanduel.com/navigation/nfl"),
 ("BT11","Grading — postponed / relocated","Game postponed before kickoff -> all wagers void (FanDuel FAQ). Relocated but played on the scheduled date -> bets remain live (graded on official league box score). BetMGM: football results official after 55 minutes of play.","","S22; S24","https://sportsbook.fanduel.com/navigation/nfl"),
 ("BT12","Grading — minimum play / incomplete games","BetMGM house rules: pro/college football results are official after 55 minutes of play unless an official result is declared earlier; incomplete matches settle per postponed/resumed rules.","","S24","https://massgaming.com/wp-content/uploads/BetMGM-House-Rules-8.14.25.pdf"),
]
write("bet-types.csv",
      ["bet_type_id","bet_type","definition","key_rules_examples","source_id","source_url","verified_on","status"],
      [[r[0],r[1],r[2],r[3],r[4],r[5],ACCESSED,"verified"] for r in BT])

# ---------------------------------------------------------------- bet combos (strategy-level; correlation discipline)
BC = [
 ("BC01","Single bet","1 leg (spread / ML / total / prop)","No correlation issue; base unit sizing applies.","allowed","S19; S23","https://sportsbook.draftkings.com/leagues/football/nfl"),
 ("BC02","2-leg cross-game parlay","2 legs, different games","Permitted; legs must be uncorrelated (no shared players/teams). Correlated selections not permitted unless offered as SGP (FanDuel house rules).","allowed with correlation cap","S21; S23","https://www.fanduel.com/fanduel-sportsbook-house-rules-on"),
 ("BC03","3+ leg cross-game parlay","3 or more legs, different games","Permitted but each added leg multiplies risk; leaderboard requires stricter validation gates for 3+ legs.","allowed with stricter gates","S21","https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet"),
 ("BC04","Same Game Parlay (SGP)","2+ legs, same game","Explicitly offered by sportsbooks; correlation is priced into the odds. Strategy must use reduced stake and treat as high-correlation.","allowed (book-priced correlation)","S20; S21; S23","https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl"),
 ("BC05","SGP+ (multi-game SGP)","Multiple SGPs across games","Same rules as SGP; check combined price before committing (FanDuel guide).","allowed (book-priced correlation)","S21","https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet"),
 ("BC06","Player prop combo — same player, same game","e.g., player passing yards + passing TDs","Directly correlated outcomes; NOT permitted unless explicitly offered by the sportsbook (house rules); flagged.","restricted / flagged","S23","https://www.fanduel.com/fanduel-sportsbook-house-rules-on"),
 ("BC07","Player prop combo — different players, same game","e.g., QB passing yards (Team A) + WR receiving yards (Team B)","Same-game legs: treat as SGP-type correlation; only combine within an offered SGP or cap stake.","restricted (SGP only)","S20; S21","https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl"),
 ("BC08","2-team teaser (6-pt)","2 legs, spread adjusted 6 points","Crosses key numbers 3 and 7 (most common NFL margins); all legs must win.","allowed","S20","https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl"),
 ("BC09","Round robin","Multiple parlays from a selection pool","Reduces all-or-nothing risk vs a single parlay; cost is higher total stake.","allowed","S20","https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl"),
]
write("bet-combos.csv",
      ["combo_id","combo_type","legs","correlation_note","allowed","source_id","source_url","verified_on","status"],
      [[r[0],r[1],r[2],r[3],r[4],r[5],r[6],ACCESSED,"verified (rules); strategy use pending validation"] for r in BC])

# ---------------------------------------------------------------- signals
SIG = [
 ("SIG01","Injuries","Official injury report delta","Count of Out/Doubtful/Questionable by team from the official weekly NFL injury report; compare against opponent's report and against the line.","NFL.com injury report","S06","https://www.nfl.com/injuries/","weekly (Wed-Sun)","verified"),
 ("SIG02","Injuries","Practice-status trend","Change in practice participation (DNP -> Limited -> Full) across the week for key positions (QB, LT, WR1, EDGE).","NFL.com injury report","S06","https://www.nfl.com/injuries/","weekly","verified"),
 ("SIG03","Team form","Points for / against and net points","PF, PA, NET PTS and per-game values from official standings; rank all 32 teams.","NFL.com standings","S04","https://www.nfl.com/standings/","updates after each game","verified"),
 ("SIG04","Team form","Winning percentage & streak","PCT and STRK from official standings (e.g., 2026-11-02 snapshot in data/standings-2026-wk8.csv).","NFL.com standings","S04","https://www.nfl.com/standings/","updates after each game","verified"),
 ("SIG05","Team stats","Offense/defense unit stats","Official team passing/rushing/receiving/scoring/downs and defensive equivalents (nfl.com team stats).","NFL.com team stats","S08","https://www.nfl.com/stats/team-stats/","updates after each game","verified"),
 ("SIG06","Player props","Player stat leaders & trends","Official player stat leaderboards (passing yards, rushing, receiving, ... 2026 leaders in data/player-passing-2026.csv).","NFL.com player stats","S07","https://www.nfl.com/stats/player-stats/","updates after each game","verified"),
 ("SIG07","Advanced","Next Gen Stats tracking metrics","NFL NGS: completion probability, expected rushing yards, win probability, speed, separation, etc. Captured 10x/second, 200+ data points per play, on AWS.","NFL Football Operations — NGS","S16","https://operations.nfl.com/gameday/technology/nfl-next-gen-stats","per play","verified"),
 ("SIG08","Schedule","Rest / bye / travel context","Rest days between games and bye placement from the official schedule and official bye list (2026 byes in data/bye-weeks-2026.csv).","NFL.com schedules + bye list","S05; S12","https://www.nfl.com/schedules","per week","verified"),
 ("SIG09","Data integrity","Official stat corrections","Use only corrected official stats (Elias Sports Bureau / NFL League Office) when grading any stat-based signal.","NFL stat corrections","S17","https://fantasy.nfl.com/research/statcorrections","as released","verified"),
 ("SIG10","Roster/cap","Salary cap & roster moves","2026 salary cap $301.2M per club; roster transactions on official club sites (linked from nfl.com/teams/).","NFL.com news + club sites","S14; S09","https://www.nfl.com/news/nfl-announces-2026-salary-cap-set-at-301-2-million-per-team","seasonal","verified"),
 ("SIG11","Market","Line vs. own model (value)","Compare the sportsbook line (official operator pages) against the strategy's own model price. Live line VALUES are dynamic and not snapshotted here — see flagged F02.","Official sportsbook NFL pages","S22; S19","https://sportsbook.fanduel.com/navigation/nfl","real-time","partial — value snapshot flagged"),
 ("SIG12","Market","Line movement / closing line value (CLV)","Historical line moves and closing lines are NOT published by any official NFL source. Signal defined but unverifiable from official sources — flagged F01.","(none official)","","","","flagged — unverified"),
 ("SIG13","Environment","Weather","nfl.com game cards show a weather note for upcoming games (e.g., MNF Nov 2: 'Clear, night'), but there is no structured official NFL weather field per game. Per-game values left blank — flagged F05.","NFL.com game cards","S05","https://www.nfl.com/schedules","per game","partial — flagged"),
 ("SIG14","Market","Public betting % / 'sharp' indicators","Not published by official sources. Excluded from all strategies — flagged F06.","(none official)","","","","flagged — excluded"),
]
write("signals.csv",
      ["signal_id","category","name","description","data_source","source_id","source_url","freshness","verification_status","verified_on"],
      [[r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],r[8],ACCESSED] for r in SIG])

# ---------------------------------------------------------------- validation gates
REPO_DOC = "https://github.com/sassnarep3-star/Own5/blob/main/research/validation-gates.md"
VG = [
 ("G01","Sample size","Every strategy must have at least 30 graded bets before any leaderboard ranking is shown.","n >= 30 graded bets","Small samples are dominated by luck (binomial variance); prevents luck-driven rankings.","Bet log (in-repo)","REPO",REPO_DOC),
 ("G02","Backtest significance","Backtest ROI must be > 0 AND the lower bound of a 95% confidence interval on win rate must exceed the break-even win rate for the odds used.","95% CI lower bound > break-even","Removes luck: a strategy must clear break-even with statistical confidence, not just a positive record.","Bet log + odds at placement (official sportsbook pages S22/S19)","S22; S19","https://sportsbook.fanduel.com/navigation/nfl"),
 ("G03","Out-of-sample / walk-forward","Last 25% of each strategy's bets are held out and must independently show ROI > 0.","walk-forward ROI > 0 on holdout","Guards against overfitting to the sample used to build the strategy.","Bet log","REPO",REPO_DOC),
 ("G04","Closing line value (CLV)","Average CLV >= 0 (bet price better than closing price).","CLV >= 0","Industry-standard skill proxy; BUT no official source publishes historical closing lines -> gate defined, data flagged F01, cannot be marked passed from official sources.","Historical lines","",""),
 ("G05","Correlation cap","Pearson correlation of a new strategy's bet outcomes vs. every live portfolio strategy must be |r| < 0.50, computed on overlapping graded bets.","|r| < 0.50","Prevents disguised duplicate exposure (the main source of parlay blow-ups).","Bet logs; computed values in data/correlations.csv where inputs are official","REPO",REPO_DOC),
 ("G06","Drawdown limit","Max drawdown of the strategy equity curve must be < 20% of allocated bankroll over the test window.","maxDD < 20%","Luck removal via risk control, not just entry selection.","Bet log","REPO",REPO_DOC),
 ("G07","Fractional Kelly sizing","Stake per bet <= 0.25 * Kelly fraction (quarter-Kelly), Kelly computed from model edge and price.","stake <= 0.25K","Caps variance from any single bet; keeps luck from compounding.","Model output","REPO",REPO_DOC),
 ("G08","Market integrity","Only official-source data enters the model: NFL.com stats/standings/injuries/schedules, NGS, operator-published rules and lines. Anything else is excluded or flagged.","100% of model inputs sourced or flagged","No hallucinated or third-party-only inputs in verified rows.","data/sources.csv","S01","https://www.nfl.com/"),
 ("G09","Parlay correlation rule","No correlated legs unless explicitly offered by the sportsbook (e.g., SGP). Same-player combos restricted.","0 unpermitted correlated legs","House rules void correlated parlays accepted in error (FanDuel).","Operator house rules","S23","https://www.fanduel.com/fanduel-sportsbook-house-rules-on"),
 ("G10","Grading integrity","All bets graded per official operator rules: OT included for full-game spread/ML/totals; pushes on whole numbers refund; postponed -> void; props void if player not active.","100% per operator rules","Prevents mis-graded results from contaminating performance.","Operator rules/FAQ","S22; S23; S24","https://sportsbook.fanduel.com/navigation/nfl"),
 ("G11","Liquidity / limits","Bet size must be within sportsbook limits and small relative to market depth; books may refuse or limit any bet at their discretion.","within posted limits","House rules reserve the right to refuse/limit bets.","Operator house rules","S23","https://www.fanduel.com/fanduel-sportsbook-house-rules-on"),
 ("G12","Responsible gambling","Only adults of legal gambling age in their jurisdiction; stake only what can be afforded to lose; help: 1-800-GAMBLER (24/7, confidential).","always on","Legal and harm-reduction gate; applies to every strategy and every page of this site.","NCPG","S25","https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/"),
]
write("validation-gates.csv",
      ["gate_id","name","criterion","threshold","rationale","data_needed","source_id","source_url","verified_on","status"],
      [[r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],ACCESSED,
        ("verified" if r[0] in ("G09","G10","G11","G12","G02","G08") else ("flagged — no official source" if r[0]=="G04" else "in-repo rule (defined in this repo; no external fact claimed)"))] for r in VG])

# ---------------------------------------------------------------- strategies (original design; no fabricated performance)
STR = [
 ("STR01","Rest-Edge Singles","Singles (spread/ML)","Teams coming off a bye or with more rest days vs. opponent, filtered by points-for/against rank.","SIG03; SIG04; SIG08","G01-G03, G05-G08, G12","","pending validation — no graded-bet data yet"),
 ("STR02","Net-Points Mismatch","Singles (spread)","Back the team with the better net points per game when the mismatch exceeds a set threshold vs. opponent.","SIG03; SIG04","G01-G03, G05-G08, G12","","pending validation — no graded-bet data yet"),
 ("STR03","QB Prop Value","Player props (passing yards/TDs)","Model QB prop lines from official player stat trends + NGS metrics; bet only when model price beats book price by threshold.","SIG05; SIG06; SIG07; SIG11","G01-G03, G05-G08, G12","","pending validation — line values flagged F02"),
 ("STR04","Injury-Adjusted Team Rating","Singles + totals","Adjust team strength by official injury report (Out/Questionable at key positions); bet totals/spreads off the adjusted matchup.","SIG01; SIG02; SIG03; SIG09","G01-G03, G05-G08, G12","","pending validation"),
 ("STR05","Two-Leg Cross-Game Parlays","Parlay (2 legs, different games)","Only uncorrelated games (no shared teams/players); both legs must pass single-bet gates; quarter-Kelly on combined price.","SIG03; SIG08","G01-G03, G05-G09, G12","","pending validation"),
 ("STR06","Same-Game Parlay (SGP) Selective","SGP","Use only where the book prices correlation (offered SGP); reduced stake (0.25x) due to high same-game correlation.","SIG01; SIG06; SIG11","G01-G03, G05, G07-G09, G12","","pending validation"),
 ("STR07","Cross-Player Prop Combos (SGP only)","Prop combo within SGP","Different players, same game, only inside an offered SGP; same-player combos excluded (BC06 restricted).","SIG06; SIG07","G01-G03, G05, G07-G09, G12","","pending validation"),
 ("STR08","Key-Number Teasers","Teaser (2-team, 6-pt)","Tease through key margins 3 and 7 (most common NFL margins per FanDuel guide); both legs must be model-validated.","SIG03; SIG04","G01-G03, G05-G08, G12","","pending validation"),
 ("STR09","Live Value After News","Live (in-play)","React to official injury/news flow during the week and in-game; bet live lines only when model price beats live price by threshold.","SIG01; SIG02; SIG11","G01-G03, G05-G08, G11, G12","","pending validation — live values flagged F02"),
 ("STR10","Division Dog Value","Singles (ML)","Underdog moneylines in division games where the dog's net-points rank is within a set band of the favorite's.","SIG03; SIG04; SIG08","G01-G03, G05-G08, G12","","pending validation"),
]
write("strategies.csv",
      ["strategy_id","name","bet_types","description","signals","gates_required","correlation_with_portfolio","status","source_url","verified_on"],
      [[r[0],r[1],r[2],r[3],r[4],r[5],r[6],r[7],
        "https://www.nfl.com/",ACCESSED] for r in STR])

# ---------------------------------------------------------------- leaderboard (metrics intentionally blank — no verified performance data exists)
LB = [
 ("LB-T1","Tier 1 (top 3 strategies by risk-adjusted return)","Reward: featured placement + largest research allocation","","","","","","",""),
 ("LB-T2","Tier 2 (next 4)","Reward: standard research allocation","","","","","","",""),
 ("LB-T3","Tier 3 (validated but lower ranked)","Reward: honorable mention","","","","","","",""),
 ("LB-STR01","STR01","Rest-Edge Singles","","","","","","","pending"),
 ("LB-STR02","STR02","Net-Points Mismatch","","","","","","","pending"),
 ("LB-STR03","STR03","QB Prop Value","","","","","","","pending"),
 ("LB-STR04","STR04","Injury-Adjusted Team Rating","","","","","","","pending"),
 ("LB-STR05","STR05","Two-Leg Cross-Game Parlays","","","","","","","pending"),
 ("LB-STR06","STR06","SGP Selective","","","","","","","pending"),
 ("LB-STR07","STR07","Cross-Player Prop Combos","","","","","","","pending"),
 ("LB-STR08","STR08","Key-Number Teasers","","","","","","","pending"),
 ("LB-STR09","STR09","Live Value After News","","","","","","","pending"),
 ("LB-STR10","STR10","Division Dog Value","","","","","","","pending"),
]
REPO_LB = "https://github.com/sassnarep3-star/Own5/blob/main/research/strategies.md"
LB_ROWS = []
for r in LB:
    if r[0].startswith("LB-T"):
        LB_ROWS.append([r[0], "", r[1], "", "", "", "", "", "", "", "", r[2], "tier rule",
                        "reward tier definition — no performance data", REPO_LB, ACCESSED])
    else:
        LB_ROWS.append([r[0], r[1], r[2], "", "", "", "", "", "", "", "", "", "pending",
                        "metric cells intentionally blank: no verified graded-bet data exists; flagged F07 — never fabricated",
                        REPO_LB, ACCESSED])
write("leaderboard.csv",
      ["entry_id","strategy_ref","name","rank","graded_bets","win_rate","roi","risk_adjusted_return","max_drawdown","clv","gates_passed","reward_tier","status","note","source_url","verified_on"],
      LB_ROWS)

# ---------------------------------------------------------------- flagged items (unverified / irregularities)
FL = [
 ("F01","Historical closing lines, line movement, CLV","signals SIG12; gate G04; leaderboard clv column","No official NFL or operator source publishes historical closing lines or line-movement history.","","left blank everywhere; gate G04 cannot be passed from official sources; CLV columns blank"),
 ("F02","Live sportsbook line values (spreads/odds/totals at a point in time)","signals SIG11; data tables","Lines are dynamic and operator-specific; no official static snapshot exists. Official pages to check: FanDuel/DraftKings NFL sportsbook pages.","https://sportsbook.fanduel.com/navigation/nfl ; https://sportsbook.draftkings.com/leagues/football/nfl","line value cells left blank; cite operator page instead of a value"),
 ("F03","Same-game leg correlation coefficients (numeric)","correlations page, SGP strategies","No official source publishes same-game outcome correlation coefficients.","","framework only; numeric cells blank"),
 ("F04","Sportsbook hold/vig percentage","bet-types analysis","Operators do not officially disclose hold percentages.","","blank"),
 ("F05","Per-game weather values","signals SIG13","nfl.com shows a weather note on some game cards (e.g., MNF Nov 2 2026 'Clear, night') but no structured official weather data field per game.","https://www.nfl.com/schedules","per-game weather cells blank; only the observed game-card note cited"),
 ("F06","Public betting percentages / sharp-money indicators","signals SIG14","Not published by any official source.","","signal excluded from all strategies"),
 ("F07","Strategy backtest / leaderboard performance metrics","leaderboard.csv; strategies.csv","No graded-bet history exists yet in this repo; fabricating results would violate the no-hallucination rule.","","all metric cells blank, status 'pending validation'"),
 ("F08","BetMGM house-rules URL is state-specific","bet-types BT12","The regulator-approved PDF cited is the Massachusetts version; other states have their own filings.","https://massgaming.com/wp-content/uploads/BetMGM-House-Rules-8.14.25.pdf","check the gaming commission of the relevant state for the applicable rules"),
 ("F09","nfl.com standings deep links with explicit week returned 'No Standings Available'","standings-2026-wk8.csv","https://www.nfl.com/standings/league/2026/reg8 and /REG9 rendered 'No Standings Available' to the fetcher on 2026-11-02; the default https://www.nfl.com/standings/ page rendered full data. Irregularity noted, not blocking.","https://www.nfl.com/standings/","snapshot taken from the default standings URL"),
 ("F10","Injury-report URL week labels vs. displayed week","signals SIG01/SIG02","nfl.com injury URLs use patterns like /injuries/league/2026/reg7-1 while the page displays 'Week 8'; labeling irregularity noted.","https://www.nfl.com/injuries/","used the displayed page title ('Week 8 of the 2026 Season')"),
 ("F11","Standings snapshot is time-stamped","standings-2026-wk8.csv","Values are the 2026-11-02 (Week 8) snapshot and change after every game.","https://www.nfl.com/standings/","re-snapshot weekly via the official URL"),
 ("F12","Network (TV) not captured for 4 of 13 played Week 8 games in the fetched page text","week8-2026-results.csv","Network text was not present in the fetched markup for ARI-DAL, MIN-DET, LV-NYJ, ATL-TB rows.","https://www.nfl.com/schedules/2026/by-week/week-8","network cells left blank for those rows"),
]
write("flagged.csv",
      ["flag_id","item","where","reason","source_url","action_taken","logged_on"],
      [[r[0],r[1],r[2],r[3],r[4],r[5],ACCESSED] for r in FL])

print("seed_data.py done")

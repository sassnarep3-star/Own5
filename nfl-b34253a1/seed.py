#!/usr/bin/env python3
"""Write the reviewed, source-linked NFL 2026 Week 10 snapshot inputs.

All values are hand-transcribed from the listed official pages. This script does not
fetch data or fill gaps. A reproducible recalculation lives in engine.py.
"""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)
AS_OF = "2026-11-12"

NFL_STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
NFL_INJURIES = "https://www.nfl.com/injuries/"
NFL_W10_REPORT = "https://www.nfl.com/news/nfl-week-10-injury-report-2026-season"
NFL_NEWS = "https://www.nfl.com/news/nfl-news-roundup-latest-league-updates-from-wednesday-nov-11"
NFL_GAME_STATS = "https://www.nfl.com/stats/team-stats/"
NFL_PASS = "https://www.nfl.com/stats/team-stats/offense/passing/2026/reg/all"
NFL_RUSH = "https://www.nfl.com/stats/team-stats/offense/rushing/2026/reg/all"
NFL_DEF_PASS = "https://www.nfl.com/stats/team-stats/defense/passing/2026/reg/all"
NFL_DEF_RUSH = "https://www.nfl.com/stats/team-stats/defense/rushing/2026/reg/all"
NFL_PLAYER_PASS = "https://www.nfl.com/stats/player-stats/category/passing/2026/reg/all/passingyards/desc"
NFL_PLAYER_RUSH = "https://www.nfl.com/stats/player-stats/category/rushing/2026/reg/all/rushingyards/desc"
NFL_PLAYER_REC = "https://www.nfl.com/stats/player-stats/category/receiving/2026/reg/all/receivingreceptions/desc"
NFL_OPS_SPOTTER = "https://operations.nfl.com/gameday/behind-the-scenes/at-spotters/"
NFL_OPS_HEALTH = "https://operations.nfl.com/game-operations-logistics/preparation-safety/health-safety"
NFL_OPS_PREP = "https://operations.nfl.com/game-operations-logistics/preparation-safety/game-and-stadium-prep"
NFL_DK = "https://sportsbook.draftkings.com/leagues/football/nfl?category=games&subcategory=game-lines&nav_1=all-games"
NFL_FD = "https://sportsbook.fanduel.com/navigation/nfl"

TEAM_NAMES = {
    "ARI":"Arizona Cardinals", "ATL":"Atlanta Falcons", "BAL":"Baltimore Ravens", "BUF":"Buffalo Bills",
    "CAR":"Carolina Panthers", "CHI":"Chicago Bears", "CIN":"Cincinnati Bengals", "CLE":"Cleveland Browns",
    "DAL":"Dallas Cowboys", "DEN":"Denver Broncos", "DET":"Detroit Lions", "GB":"Green Bay Packers",
    "HOU":"Houston Texans", "IND":"Indianapolis Colts", "JAX":"Jacksonville Jaguars", "KC":"Kansas City Chiefs",
    "LAC":"Los Angeles Chargers", "LAR":"Los Angeles Rams", "LV":"Las Vegas Raiders", "MIA":"Miami Dolphins",
    "MIN":"Minnesota Vikings", "NE":"New England Patriots", "NO":"New Orleans Saints", "NYG":"New York Giants",
    "NYJ":"New York Jets", "PHI":"Philadelphia Eagles", "PIT":"Pittsburgh Steelers", "SEA":"Seattle Seahawks",
    "SF":"San Francisco 49ers", "TB":"Tampa Bay Buccaneers", "TEN":"Tennessee Titans", "WSH":"Washington Commanders",
}

DEPTH_URLS = {
    "ARI":"https://www.azcardinals.com/team/depth-chart", "ATL":"https://www.atlantafalcons.com/team/depth-chart",
    "BAL":"https://www.baltimoreravens.com/team/depth-chart", "BUF":"https://www.buffalobills.com/team/depth-chart",
    "CAR":"https://www.panthers.com/team/depth-chart", "CHI":"https://www.chicagobears.com/team/depth-chart",
    "CIN":"https://www.bengals.com/team/depth-chart", "CLE":"https://www.clevelandbrowns.com/team/depth-chart",
    "DAL":"https://www.dallascowboys.com/team/depth-chart", "DEN":"https://www.denverbroncos.com/team/depth-chart/depth-chart-main",
    "DET":"https://www.detroitlions.com/team/depth-chart", "GB":"https://www.packers.com/team/depth-chart",
    "HOU":"https://www.houstontexans.com/team/depth-chart", "IND":"https://www.colts.com/team/depth-chart",
    "JAX":"https://www.jaguars.com/team/depth-chart", "KC":"https://www.chiefs.com/team/depth-chart",
    "LAC":"https://www.chargers.com/team/depth-chart", "LAR":"https://www.therams.com/team/depth-chart",
    "LV":"https://www.raiders.com/team/depth-chart", "MIA":"https://www.miamidolphins.com/team/depth-chart",
    "MIN":"https://www.vikings.com/team/depth-chart", "NE":"https://www.patriots.com/team/depth-chart",
    "NO":"https://www.neworleanssaints.com/team/depth-chart", "NYG":"https://www.giants.com/team/depth-chart",
    "NYJ":"https://www.newyorkjets.com/team/depth-chart", "PHI":"https://www.philadelphiaeagles.com/team/depth-chart",
    "PIT":"https://www.steelers.com/team/depth-chart", "SEA":"https://www.seahawks.com/team/depth-chart",
    "SF":"https://www.49ers.com/team/depth-chart", "TB":"https://www.buccaneers.com/team/depth-chart",
    "TEN":"https://www.tennesseetitans.com/team/depth-chart", "WSH":"https://www.commanders.com/team/depth-chart",
}

DEPTH_PAGE_NOTES = {
    "CHI":{"as_of":"2026-10-31","authority_note":"Page states Depth Chart as of 10/31/2026; Week 10 bye, not used for Week 10 injury observations."},
    "DEN":{"as_of":"","authority_note":"Current chart page has no displayed update date in retrieved text. A separate archive is labelled unofficial and dated 2026-09-22; this current-page chart is not used for Week 10 injury observations (bye)."},
    "PHI":{"as_of":"","authority_note":"Page explicitly labels chart unofficial, compiled by the Eagles communications department; no update date displayed. Week 10 bye, not used for Week 10 injury observations."},
    "TB":{"as_of":"","authority_note":"Current club page has no displayed update date in retrieved text. Week 10 bye, not used for Week 10 injury observations."},
    "HOU":{"as_of":"","authority_note":"Fetched chart was image-only; string assignments not verified from retrieved HTML."},
}

SCHEDULE_URLS = {w:f"https://www.nfl.com/schedules/2026/by-week/week-{w}" for w in range(1,11)}

def write_csv(name, rows, fields=None):
    if fields is None:
        fields = list(rows[0]) if rows else []
    with (DATA / name).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def slurp_csv(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# This table is transcribed from NFL.com league standings (as displayed before Week 10).
# rows: W, L, T, PF, PA
STANDINGS = {
"BUF":(7,1,0,256,187),"SF":(7,1,0,235,156),"CHI":(7,2,0,241,184),"DEN":(7,2,0,198,186),
"CIN":(6,2,0,240,175),"DET":(6,2,0,222,189),"JAX":(6,2,0,229,121),"KC":(6,2,0,202,143),
"MIN":(6,2,0,146,116),"PIT":(6,2,0,180,144),"NYG":(5,2,1,182,172),"GB":(6,3,0,216,191),
"CLE":(5,4,0,161,196),"LAR":(5,4,0,214,181),"NE":(5,4,0,211,207),"SEA":(5,4,0,202,162),
"BAL":(4,5,0,189,236),"DAL":(4,5,0,246,236),"LV":(4,5,0,238,268),"CAR":(3,5,0,199,219),
"HOU":(3,5,0,209,192),"NO":(3,5,0,185,216),"ARI":(3,6,0,178,255),"ATL":(3,6,0,188,223),
"TB":(3,6,0,202,178),"WSH":(2,5,1,172,202),"IND":(2,7,0,184,249),"NYJ":(2,7,0,182,223),
"PHI":(2,7,0,148,221),"MIA":(1,7,0,126,200),"TEN":(1,7,0,144,199),"LAC":(0,8,0,121,219),
}
write_csv("standings_2026_w10.csv", [
    {"team":t,"team_name":TEAM_NAMES[t],"wins":v[0],"losses":v[1],"ties":v[2],"points_for":v[3],"points_against":v[4],
     "as_of":"before_week_10","source_url":NFL_STANDINGS,"source_verified_on":AS_OF}
    for t,v in STANDINGS.items()
])

# W1-8 scores from the repository game log, whose source field points to nfl.com.
# Week 8 Monday Night Football and all Week 9 finals are set from official NFL.com schedule results.
W9 = {
("JAX","BAL"):(33,10), ("CIN","ATL"):(34,17), ("DEN","CAR"):(26,21), ("DAL","IND"):(27,23),
("NYJ","KC"):(12,35), ("DET","MIA"):(19,9), ("CLE","NO"):(22,23), ("NYG","PHI"):(19,11),
("LAR","WSH"):(20,13), ("HOU","LAC"):(44,22), ("LV","SF"):(17,38), ("GB","NE"):(45,27),
("ARI","SEA"):(3,17), ("TB","CHI"):(24,27), ("BUF","MIN"):(23,6),
}
with (ROOT.parent / "data/games_2026.json").open(encoding="utf-8") as f:
    old_games = __import__("json").load(f)["games"]
GAMES=[]
for g in old_games:
    if g["wk"] > 9:
        continue
    a,h=g["as"],g["hs"]
    if g["wk"] == 8 and g["away"] == "CHI" and g["home"] == "SEA":
        a,h=34,17
    elif g["wk"] == 9:
        a,h=W9[(g["away"],g["home"])]
    if a is None or h is None:
        raise ValueError(f"missing official final {g}")
    GAMES.append({
        "week":g["wk"],"date":g["date"],"away_team":g["away"],"home_team":g["home"],
        "away_points":a,"home_points":h,"status":"FINAL",
        "game_url":f"https://www.nfl.com/games/{g['nfl']}","schedule_url":SCHEDULE_URLS[g["wk"]],
        "source_url":f"https://www.nfl.com/games/{g['nfl']}","source_verified_on":AS_OF,
        "note":g.get("note","")
    })
if len(GAMES)!=136:
    raise ValueError(f"expected 136 finished games, found {len(GAMES)}")
write_csv("games_2026_w1_w9.csv", GAMES)

# NFL team stats pages (2026 regular season as of the Week 10 slate; 32 rows per category).
# passing: Att, Comp, Comp%, YPA, Yds, TD, INT, rating.
PASS={
"SF":(236,163,69.1,8.4,1980,17,5,109.8),"CHI":(312,211,67.6,7.4,2310,10,9,88.0),"CIN":(296,219,74.0,8.1,2386,23,6,114.8),
"BUF":(236,156,66.1,8.6,2027,12,6,99.3),"DEN":(287,174,60.6,6.0,1730,11,4,84.7),"CLE":(283,185,65.4,7.4,2105,9,3,93.7),
"TB":(240,146,60.8,5.9,1423,6,9,70.2),"ARI":(359,232,64.6,5.8,2080,13,7,84.0),"LAC":(243,146,60.1,6.6,1615,7,11,70.6),
"KC":(263,177,67.3,7.8,2037,14,4,101.8),"IND":(304,184,60.5,5.7,1730,6,10,69.1),"WSH":(266,164,61.6,6.7,1776,12,1,94.8),
"DAL":(336,218,64.9,7.1,2381,16,5,95.4),"MIA":(209,122,58.4,6.9,1442,6,6,77.1),"PHI":(303,179,59.1,5.7,1740,10,6,78.0),
"ATL":(256,156,60.9,6.9,1766,11,12,76.4),"NYG":(268,165,61.6,7.1,1900,12,6,88.5),"JAX":(227,147,64.8,8.6,1940,18,4,110.8),
"NYJ":(271,183,67.5,7.7,2078,12,3,100.4),"DET":(274,186,67.9,7.8,2145,15,2,106.5),"GB":(341,215,63.0,7.7,2618,19,6,97.9),
"CAR":(313,189,60.4,7.2,2244,16,6,91.3),"NE":(281,183,65.1,8.4,2349,18,11,96.2),"LV":(324,209,64.5,7.4,2401,20,8,97.0),
"LAR":(349,232,66.5,6.8,2387,16,9,90.5),"BAL":(247,165,66.8,7.5,1842,10,5,93.9),"NO":(308,204,66.2,6.4,1986,14,6,91.2),
"SEA":(288,182,63.2,7.2,2089,15,9,89.3),"PIT":(290,175,60.3,6.4,1871,13,6,85.6),"HOU":(285,182,63.9,7.9,2258,16,2,104.1),
"TEN":(248,155,62.5,6.0,1483,6,5,78.8),"MIN":(225,137,60.9,6.4,1437,8,5,82.0),
}
# Offense rushing: carries, yards, yards/carry, touchdowns.
RUSH={
"SF":(234,1082,4.6,12),"CHI":(303,1278,4.2,17),"CIN":(177,685,3.9,5),"BUF":(261,1173,4.5,17),"DEN":(223,823,3.7,9),"CLE":(233,876,3.8,6),
"TB":(294,1475,5.0,11),"ARI":(226,924,4.1,4),"LAC":(224,916,4.1,4),"KC":(217,1102,5.1,10),"IND":(249,1037,4.2,11),"WSH":(210,946,4.5,5),
"DAL":(233,932,4.0,11),"MIA":(215,940,4.4,7),"PHI":(213,797,3.7,8),"ATL":(258,1235,4.8,9),"NYG":(232,897,3.9,6),"JAX":(230,937,4.1,8),
"NYJ":(231,947,4.1,5),"DET":(230,1022,4.4,10),"GB":(202,614,3.0,6),"CAR":(189,810,4.3,7),"NE":(256,1079,4.2,7),"LV":(222,642,2.9,5),
"LAR":(242,1128,4.7,11),"BAL":(265,1240,4.7,11),"NO":(203,762,3.8,7),"SEA":(258,997,3.9,7),"PIT":(193,943,4.9,4),"HOU":(195,697,3.6,6),
"TEN":(189,796,4.2,8),"MIN":(211,848,4.0,3),
}
# Defense passing: YPA allowed, yards allowed, TD allowed, INT, passer rating allowed, sacks.
DEF_PASS={
"ARI":(8.0,2076,19,3,108.9,19),"LAR":(6.4,1882,11,7,82.3,16),"GB":(6.4,2087,13,13,77.6,26),"DAL":(7.2,2133,16,4,99.1,17),
"LV":(8.0,2238,20,7,103.6,19),"CAR":(6.4,1774,12,5,88.3,12),"CHI":(8.2,2120,13,7,93.1,26),"NO":(7.8,2045,13,4,99.6,23),
"IND":(8.1,2145,16,2,104.1,19),"PHI":(7.2,2150,13,3,92.2,16),"CIN":(7.3,1989,9,5,88.9,23),"PIT":(6.9,1936,7,7,83.3,26),
"SEA":(5.5,1519,9,8,77.3,21),"DEN":(6.5,2249,14,8,83.4,26),"HOU":(7.4,2056,12,4,95.3,29),"CLE":(6.7,1982,12,6,84.6,26),
"NE":(7.9,2256,14,5,100.2,25),"DET":(7.2,2265,18,6,97.5,27),"NYJ":(7.1,1909,16,1,103.5,22),"NYG":(6.0,1514,14,6,87.0,16),
"WSH":(6.9,2048,16,5,96.5,17),"KC":(6.4,1764,7,6,79.4,14),"ATL":(6.8,2171,14,3,96.3,20),"TEN":(8.0,2182,11,8,95.9,20),
"BAL":(7.6,2177,12,4,96.1,17),"LAC":(7.9,1845,13,7,95.9,13),"TB":(6.6,2040,12,16,72.7,17),"BUF":(6.7,2022,15,6,89.3,17),
"SF":(6.4,1783,11,6,88.7,15),"JAX":(7.3,1907,8,11,80.1,16),"MIN":(6.4,1495,5,9,67.9,29),"MIA":(8.1,1797,16,5,114.0,12),
}
# Defense rushing: carries allowed, yards, yards/carry, TD.
DEF_RUSH={
"SF":(194,647,3.3,4),"CHI":(185,820,4.4,8),"CIN":(201,1013,5.0,8),"BUF":(189,733,3.9,7),"DEN":(248,1119,4.5,6),"CLE":(249,1175,4.7,8),
"TB":(201,712,3.5,3),"ARI":(262,1097,4.2,10),"LAC":(240,976,4.1,11),"KC":(215,780,3.6,5),"IND":(250,1233,4.9,9),"WSH":(209,818,3.9,7),
"DAL":(266,1327,5.0,11),"MIA":(236,894,3.8,6),"PHI":(276,1135,4.1,10),"ATL":(242,1069,4.4,10),"NYG":(211,989,4.7,7),"JAX":(194,714,3.7,5),
"NYJ":(282,1152,4.1,10),"DET":(184,753,4.1,6),"GB":(244,981,4.0,11),"CAR":(231,1067,4.6,13),"NE":(225,870,3.9,8),"LV":(272,1361,5.0,12),
"LAR":(236,934,4.0,4),"BAL":(249,899,3.6,12),"NO":(237,1071,4.5,11),"SEA":(233,802,3.4,7),"PIT":(185,671,3.6,4),"HOU":(209,824,3.9,9),
"TEN":(239,993,4.2,10),"MIN":(224,951,4.2,5),
}
assert all(len(x)==32 for x in (STANDINGS,PASS,RUSH,DEF_PASS,DEF_RUSH))
team_stats=[]
for t in TEAM_NAMES:
    p=PASS[t]; r=RUSH[t]; dp=DEF_PASS[t]; dr=DEF_RUSH[t]
    team_stats.append({
        "team":t,"team_name":TEAM_NAMES[t],"period":"2026_REG_through_Week_9",
        "off_pass_att":p[0],"off_pass_comp":p[1],"off_pass_comp_pct":p[2],"off_pass_ypa":p[3],"off_pass_yards":p[4],"off_pass_td":p[5],"off_pass_int":p[6],"off_pass_rating":p[7],
        "off_rush_att":r[0],"off_rush_yards":r[1],"off_rush_ypc":r[2],"off_rush_td":r[3],
        "def_pass_ypa_allowed":dp[0],"def_pass_yards_allowed":dp[1],"def_pass_td_allowed":dp[2],"def_pass_int":dp[3],"def_pass_rating_allowed":dp[4],"def_pass_sacks":dp[5],
        "def_rush_att_allowed":dr[0],"def_rush_yards_allowed":dr[1],"def_rush_ypc_allowed":dr[2],"def_rush_td_allowed":dr[3],
        "source_url":NFL_PASS,"source_offense_passing_url":NFL_PASS,"source_offense_rushing_url":NFL_RUSH,
        "source_defense_passing_url":NFL_DEF_PASS,"source_defense_rushing_url":NFL_DEF_RUSH,"source_verified_on":AS_OF,
    })
write_csv("team_stats_2026_w10.csv", team_stats)

# Week 10 slate: schedule, venues and game links are sourced to nfl.com; the NFL injury report
# identifies the venue/time. Kickoff time is Eastern Time (official schedule label).
SLATE=[
("2026-11-12","20:15 ET","WSH","NYG","MetLife Stadium","commanders-at-giants-2026-reg-10"),
("2026-11-15","09:30 ET","NE","DET","FC Bayern Munich Stadium","patriots-at-lions-2026-reg-10"),
("2026-11-15","13:00 ET","KC","ATL","Mercedes-Benz Stadium","chiefs-at-falcons-2026-reg-10"),
("2026-11-15","13:00 ET","HOU","CLE","Huntington Bank Field","texans-at-browns-2026-reg-10"),
("2026-11-15","13:00 ET","MIN","GB","Lambeau Field","vikings-at-packers-2026-reg-10"),
("2026-11-15","13:00 ET","MIA","IND","Lucas Oil Stadium","dolphins-at-colts-2026-reg-10"),
("2026-11-15","13:00 ET","CAR","NO","Caesars Superdome","panthers-at-saints-2026-reg-10"),
("2026-11-15","13:00 ET","BUF","NYJ","MetLife Stadium","bills-at-jets-2026-reg-10"),
("2026-11-15","13:00 ET","JAX","TEN","Nissan Stadium","jaguars-at-titans-2026-reg-10"),
("2026-11-15","16:05 ET","LAR","ARI","State Farm Stadium","rams-at-cardinals-2026-reg-10"),
("2026-11-15","16:05 ET","SEA","LV","Allegiant Stadium","seahawks-at-raiders-2026-reg-10"),
("2026-11-15","16:25 ET","SF","DAL","AT&T Stadium","49ers-at-cowboys-2026-reg-10"),
("2026-11-15","20:20 ET","PIT","CIN","Paycor Stadium","steelers-at-bengals-2026-reg-10"),
("2026-11-16","20:15 ET","LAC","BAL","M&T Bank Stadium","chargers-at-ravens-2026-reg-10"),
]
schedule=[]
for date,kick,away,home,venue,slug in SLATE:
    url=f"https://www.nfl.com/games/{slug}"
    schedule.append({"week":10,"date":date,"kickoff_et":kick,"away_team":away,"away_team_name":TEAM_NAMES[away],"home_team":home,"home_team_name":TEAM_NAMES[home],"venue":venue,"status":"SCHEDULED","game_url":url,"source_url":url,"source_schedule_url":SCHEDULE_URLS[10],"source_injury_report_url":NFL_W10_REPORT,"source_verified_on":AS_OF})
for t in ("CHI","DEN","PHI","TB"):
    schedule.append({"week":10,"date":"","kickoff_et":"","away_team":t,"away_team_name":TEAM_NAMES[t],"home_team":"","home_team_name":"","venue":"","status":"BYE","game_url":"","source_url":SCHEDULE_URLS[10],"source_schedule_url":SCHEDULE_URLS[10],"source_injury_report_url":NFL_W10_REPORT,"source_verified_on":AS_OF})
write_csv("schedule_2026_w10.csv",schedule)

# A full 32-club chart-source coverage ledger. For the four bye teams, the chart URL
# is documented but no Week 10 injury row or line adjustment is inferred.
bye_teams={r["away_team"] for r in schedule if r["status"]=="BYE"}
depth_coverage=[]
for team in sorted(TEAM_NAMES):
    meta=DEPTH_PAGE_NOTES.get(team,{})
    note=meta.get("authority_note","Club-site depth chart page retrieved 2026-11-12; chart labels and update dates vary. Listed order is not confirmed active status or snap share.")
    depth_coverage.append({"team":team,"team_name":TEAM_NAMES[team],"week10_status":"BYE" if team in bye_teams else "PLAYING",
        "chart_source_url":DEPTH_URLS[team],"chart_retrieved_on":AS_OF,"chart_displayed_as_of":meta.get("as_of",""),
        "authority_note":note,"scope_use":"Chart order is reference only; no player is assumed active or assigned a point impact." if team not in bye_teams else "Chart source checked for complete team coverage; bye team excluded from Week 10 injury observations and line model.",
        "source_schedule_url":SCHEDULE_URLS[10],"source_injury_index_url":NFL_INJURIES})
write_csv("depth_chart_coverage_2026_w10.csv",depth_coverage)

# Two sportsbook boards, transcribed from their public NFL odds pages. The quote values are
# observed and source-linked; neither page exposed a preserved UTC retrieval timestamp.
# Fields: book, away spread/price, home spread/price, total, over/under prices, moneyline prices.
DK_IDS={"WSH":"34118102","NE":"34118220","JAX":"34118232","BUF":"34118183","KC":"34118132","HOU":"34118093","MIN":"34118179","MIA":"34118270","CAR":"34118165","LAR":"34118111","SEA":"34118249","SF":"34118134","PIT":"34118114","LAC":"34118177"}
FD_IDS={"WSH":"36275757","NE":"35605986","MIN":"36275758","HOU":"36275760","KC":"36275759","MIA":"36275761","JAX":"36275762","CAR":"36275767","BUF":"36275763","LAR":"36275766","SEA":"36275769","SF":"36275764","PIT":"36275765","LAC":"36275768"}
ODDS={
"WSH": {"DK":(2.5,-110,-2.5,-110,40.5,-118,-102,114,-135),"FD":(1.5,100,-1.5,-120,41.5,100,-120,112,-132)},
"NE":  {"DK":(2.5,100,-2.5,-120,51.5,100,-120,130,-155),"FD":(2.5,100,-2.5,-120,50.5,-115,-105,128,-152)},
"JAX": {"DK":(-10.5,-112,10.5,-108,46.5,-110,-110,-600,440),"FD":(-10.5,-110,10.5,-110,46.5,100,-120,-700,500)},
"BUF": {"DK":(-8.5,-108,8.5,-112,50.5,-118,-102,-440,340),"FD":(-7.5,-115,7.5,-105,50.5,-120,100,-480,370)},
"KC":  {"DK":(-3.0,-120,3.0,100,46.5,-110,-110,-185,154),"FD":(-3.5,100,3.5,-120,47.5,-105,-115,-172,144)},
"HOU": {"DK":(-4.5,-115,4.5,-105,40.5,-108,-112,-225,185),"FD":(-4.5,-115,4.5,-105,40.5,-115,-105,-235,194)},
"MIN": {"DK":(3.0,-108,-3.0,-112,42.5,-105,-115,136,-162),"FD":(3.0,-110,-3.0,-110,42.5,-105,-115,138,-164)},
"MIA": {"DK":(3.5,-102,-3.5,-118,38.5,-108,-112,170,-205),"FD":(3.5,-105,-3.5,-115,38.5,-105,-115,180,-215)},
"CAR": {"DK":(2.5,-112,-2.5,-108,48.5,-112,-108,110,-130),"FD":(2.5,-115,-2.5,-105,48.5,-115,-105,112,-132)},
"LAR": {"DK":(-9.5,-112,9.5,-108,39.5,-108,-112,-520,390),"FD":(-9.5,-110,9.5,-110,39.5,-110,-110,-550,410)},
"SEA": {"DK":(-6.5,-112,6.5,-108,40.5,-112,-108,-298,240),"FD":(-6.5,-105,6.5,-115,40.5,-110,-110,-290,235)},
"SF":  {"DK":(-3.5,-115,3.5,-105,55.5,-118,-102,-205,170),"FD":(-4.5,100,4.5,-120,55.5,-115,-105,-210,176)},
"PIT": {"DK":(3.5,-110,-3.5,-110,49.5,-108,-112,150,-180),"FD":(3.5,-110,-3.5,-110,49.5,-110,-110,154,-184)},
"LAC": {"DK":(4.5,-112,-4.5,-108,38.5,-110,-110,185,-225),"FD":(4.5,-110,-4.5,-110,38.5,-115,-105,188,-220)},
}
QUOTE_ROWS=[]
for date,kick,away,home,venue,slug in SLATE:
    for book,vals in ODDS[away].items():
        asp,ap, hsp,hp,total,overp,underp,aml,hml=vals
        if book=="DK":
            event=f"https://sportsbook.draftkings.com/event/{ {'WSH':'was-commanders-%40-ny-giants','NE':'ne-patriots-%40-det-lions','JAX':'jax-jaguars-%40-ten-titans','BUF':'buf-bills-%40-ny-jets','KC':'kc-chiefs-%40-atl-falcons','HOU':'hou-texans-%40-cle-browns','MIN':'min-vikings-%40-gb-packers','MIA':'mia-dolphins-%40-ind-colts','CAR':'car-panthers-%40-no-saints','LAR':'la-rams-%40-ari-cardinals','SEA':'sea-seahawks-%40-lv-raiders','SF':'sf-49ers-%40-dal-cowboys','PIT':'pit-steelers-%40-cin-bengals','LAC':'la-chargers-%40-bal-ravens'}[away]}/{DK_IDS[away]}"
        else:
            event=f"https://sportsbook.fanduel.com/football/nfl/{ {'WSH':'washington-commanders-@-new-york-giants','NE':'new-england-patriots-@-detroit-lions','JAX':'jacksonville-jaguars-@-tennessee-titans','BUF':'buffalo-bills-@-new-york-jets','KC':'kansas-city-chiefs-@-atlanta-falcons','HOU':'houston-texans-@-cleveland-browns','MIN':'minnesota-vikings-@-green-bay-packers','MIA':'miami-dolphins-@-indianapolis-colts','CAR':'carolina-panthers-@-new-orleans-saints','LAR':'los-angeles-rams-@-arizona-cardinals','SEA':'seattle-seahawks-@-las-vegas-raiders','SF':'san-francisco-49ers-@-dallas-cowboys','PIT':'pittsburgh-steelers-@-cincinnati-bengals','LAC':'los-angeles-chargers-@-baltimore-ravens'}[away]}-{FD_IDS[away]}"
        QUOTE_ROWS.append({"week":10,"date":date,"away_team":away,"home_team":home,"book":book,"away_spread":asp,"away_spread_american_odds":ap,"home_spread":hsp,"home_spread_american_odds":hp,"total_points":total,"over_american_odds":overp,"under_american_odds":underp,"away_moneyline_american":aml,"home_moneyline_american":hml,"retrieved_date":AS_OF,"retrieved_time_utc":"","source_url":event,"board_url":NFL_DK if book=="DK" else NFL_FD,"timestamp_status":"DATE_ONLY_TIME_NOT_EXPOSED_BY_SOURCE"})
write_csv("market_quotes_2026_w10.csv",QUOTE_ROWS)

# An explicitly selective list of week-10 availability cascades. Order is the club's
# published chart, not a guarantee of active status, snap share or actual participation.
# The point adjustment is deliberately not present: no official source supplies a validated
# conversion from these depth slots/statuses to expected score.
INJ=[]
def inj(team, side, pos, player, status, body, chain, note="", news=True, verified=True):
    INJ.append({"team":team,"side":side,"position":pos,"affected_player":player,"reported_status":status,"reported_body_part_or_reason":body,
      "published_depth_chain":chain,"deepest_listed_string_slot":max([int(x.split(':',1)[0]) for x in chain.split(';') if x[:1].isdigit()] or [0]),
      "actual_week10_participation":"","expected_starter_after_report":"","injury_source_url":NFL_INJURIES,
      "official_depth_chart_url":DEPTH_URLS.get(team,""),"news_source_url":NFL_NEWS if news else "",
      "source_url":NFL_INJURIES if verified else DEPTH_URLS.get(team,""),"verification_status":"VERIFIED_STATUS_AND_CHART_ORDER; PARTICIPATION_UNCONFIRMED" if verified else "DEPTH_ORDER_UNVERIFIED_IMAGE_ONLY",
      "note":note})
# WSH / NYG
inj("WSH","offense","C","Lucas Patrick","OUT","concussion","1:Nick Allegretti;2:Matt Gulbin","Patrick is OUT; listed chart ordering does not prove active-game usage.")
inj("WSH","offense","TE","Colson Yankoff","OUT","knee","1:John Bates","Yankoff is listed behind John Bates on the club chart.")
inj("WSH","offense","WR","Treylon Burks","DNP","","1:Terry McLaurin","Body part not preserved in the checked NFL report excerpt; left blank.")
inj("NYG","defense","LB","Malik Harrison","QUESTIONABLE","groin","","Omitted from the WLB/MLB two-deep on the club chart; replacement not asserted.")
# New England
inj("NE","offense","RB","Rhamondre Stevenson","DNP","knee","2:TreVeyon Henderson;3:Corey Kiner;4:Lan Larison","Henderson separately ruled OUT; chart shows further RB depth.")
inj("NE","offense","RB","TreVeyon Henderson","OUT","illness","3:Corey Kiner;4:Lan Larison","Depth chart chain begins after the listed OUT players.")
inj("NE","offense","LG","Ben Brown","OUT","knee","2:Walter Rouse","Rouse was DNP (concussion protocol); further replacement not assigned.")
inj("NE","defense","CB","Carlton Davis III","OUT","knee","2:Channing Canada;3:Charles Woods","Charles Woods was LP (hamstring); status is not final active/inactive.")
# Seattle
inj("SEA","offense","QB","Sam Darnold","OUT","ribs/quadricep","2:Drew Lock;3:Jalen Milroe","Lock was limited (right elbow/oblique); final active list not available.")
inj("SEA","offense","LT","Charles Cross","DNP","ankle","2:Josh Jones")
inj("SEA","offense","LG","Quenton Nelson","DNP","knee","2:Anthony Bradford","Bradford was limited (knee); chart's RG depth is not treated as LG replacement.")
inj("SEA","offense","WR","Jaxon Smith-Njigba","DNP","","2:Tory Horton","Body part left blank; DNP does not establish game absence.")
inj("SEA","defense","DT","Leonard Williams","DNP","stinger","2:Rylie Mills")
inj("SEA","defense","DE","Jarran Reed","DNP","NIR-personal","2:Mike Morris")
inj("SEA","defense","NT","Brandon Pili","DNP","","3:Deven Eastern","Depth chart lists Deven Eastern as third at NT; body part not confirmed.")
inj("SEA","defense","SLB","Uchenna Nwosu","LP","ankle","3:Connor O'Toole","Nwosu and O'Toole were limited; exposure only, not a confirmed replacement.")
# Miami
inj("MIA","offense","QB","Malik Willis","INJURED RESERVE","groin","1:Kyle McCord","Only QB listed on fetched club chart; game-start confirmation not represented here.")
inj("MIA","offense","C","Aaron Brewer","DNP","concussion","2:Andrew Meyer")
inj("MIA","offense","TE","Will Kacmarek","DNP","quad/knee","3:Seydou Traore;4:Justin Joly")
# Green Bay
inj("GB","offense","RB","Josh Jacobs","OUT","broken ring finger; surgery reported","2:MarShawn Lloyd;3:Pierre Strong Jr.;4:Kaleb Johnson","Official NFL report says he will miss Week 10; return estimate is not used.")
inj("GB","offense","C","Sean Rhyan","DNP","ankle","2:Jager Burton")
inj("GB","defense","EDGE","Lukas Van Ness","DNP","back","2:Brenton Cox Jr.","Micah Parsons was limited with illness; no availability adjustment assigned.")
inj("GB","defense","LB","Zaire Franklin","DNP","shin","2:Ty'Ron Hopper;3:Kristian Welch")
inj("GB","defense","NB","Javon Bullard","DNP","ankle/knee","2:Kamal Hadden")
# Minnesota
inj("MIN","offense","QB","Kyler Murray","DNP","hamstring","2:Carson Wentz;3:Max Brosmer","Wentz limited (ankle); Kirk Cousins was acquired Tuesday but absent from fetched club chart; starter unresolved.")
inj("MIN","offense","TE","T.J. Hockenson","DNP","wrist/chest","2:Gavin Bartholomew")
inj("MIN","offense","WR","Jauan Jennings","DNP","calf","2:Myles Price")
inj("MIN","defense","LB","Blake Cashman","DNP","concussion","2:Ivan Pace Jr.")
inj("MIN","defense","DL","Tyrion Ingram-Dawkins","DNP","ankle","2:Elijah Williams")
inj("MIN","defense","OLB","Kyle Van Noy","DNP","calf","3:Chaz Chambliss")
# San Francisco
inj("SF","offense","RB","Christian McCaffrey","DNP","","2:Kaelon Black;3:Jordan James","Injury/body part not stated in the checked report excerpt.")
inj("SF","offense","LT","Trent Williams","DNP","","2:Vederian Lowe;3:Enrique Cruz Jr.","Body part not stated in the checked report excerpt.")
inj("SF","offense","WR","Mike Evans","DNP; week-to-week","Achilles","2:Jordan Watkins;3:Brandin Cooks","Deebo Samuel separately limited (hamstring); no snap projection.")
inj("SF","defense","LCB","Renardo Green","DNP","back","","Club chart has no listed LCB2; status-to-replacement unresolved.")
inj("SF","defense","RCB","Deommodore Lenoir","DNP","foot","2:Ephesians Prysock","Jack Jones signed to practice squad; not treated as charted active depth.")
inj("SF","defense","WILL","Dre Greenlaw","DNP","","2:Garret Wallow","Body part not stated in the checked report excerpt.")
# Dallas
inj("DAL","offense","TE","Jake Ferguson","DNP","knee/ankle","1:Brevyn Spann-Ford;2:Luke Schoonmaker","Club chart lists co-TE1; line order alone does not imply Ferguson replacement.")
inj("DAL","offense","RB","Tyler Goodson","DNP","ankle/knee","","No exact replacement asserted from checked material.")
inj("DAL","offense","WR","Jonathan Mingo","DNP","ankle","","No exact replacement asserted from checked material.")
inj("DAL","defense","CB","Joey Porter Jr.","DNP","ankle","2:Shavon Revel Jr.;3:Ameer Speed")
inj("DAL","defense","S","Malik Hooker","DNP","","2:Alijah Clark","Body part not stated in the checked report excerpt.")
inj("DAL","defense","S","P.J. Locke","DNP","concussion","1:Markquese Bell;3:Juanyeh Thomas","Chart lists co-S1; actual starting assignment is unresolved.")
inj("DAL","defense","OLB","Donovan Ezeiruaku","DNP","ankle","2:James Houston;3:Tyrus Wheat")
inj("DAL","defense","OLB","Von Miller","DNP","","3:Marist Liufau","Body part not stated in the checked report excerpt.")
# Rams / Arizona
inj("LAR","offense","WR","Puka Nacua","DNP","knee/toe","2:Jordan Whittington;3:Tutu Atwell","NFL report says significant time expected; do not treat as a finalized return date.")
inj("LAR","offense","LG","Steve Avila","DNP","hamstring","2:Bill Murray")
inj("LAR","defense","CB","Trent McDuffie","DNP","back","2:Cam Lampkin")
inj("LAR","defense","S","Kamren Curl","DNP","toe","2:Jaylen McCollough")
inj("ARI","offense","QB","Carson Beck","NAMED STARTER","first NFL start; no injury stated","1:Carson Beck;2:Josh Johnson;3:Joey Aguilar","Starter statement from NFL roundup; depth chain from club chart.")
inj("ARI","offense","C","Hjalte Froholdt","DNP","concussion","2:Kingsley Eguakun")
inj("ARI","offense","LG","Isaac Seumalo","DNP","","2:Hayden Conner","Body part not stated in the checked report excerpt.")
inj("ARI","offense","RG","Jon Gaines II","DNP","ankle","2:Jon Gaines II","Chart lists Gaines as RG2; deeper replacement not asserted.")
inj("ARI","defense","NT","Roy Lopez","DNP","toe/ankle","2:Andrew Billings")
inj("ARI","defense","OLB","Josh Sweat","DNP","","2:Jordan Burch;3:Eku Leota","Body part not stated in the checked report excerpt.")
inj("ARI","defense","ILB","Mack Wilson Sr.","DNP","","2:Cody Simon","Body part not stated in the checked report excerpt.")
inj("ARI","defense","S","Budda Baker","DNP","","2:Dadrion Taylor-Demerson","Body part not stated in the checked report excerpt.")
# Detroit
inj("DET","defense","CB","D.J. Reed","DNP","hip","2:Rock Ya-Sin;3:Khalil Dorsey;4:Nick Whiteside")
inj("DET","offense","C","Cade Mays","DNP","ankle","2:Juice Scruggs")
inj("DET","offense","RB","Sione Vaki","DNP","ankle","3:Jacob Saylors")
# Pittsburgh
inj("PIT","defense","LOLB","T.J. Watt","DNP","","","Club chart leaves LOLB2 blank; backup string cannot be verified.")
inj("PIT","defense","DT","Cameron Heyward","DNP","","","Club chart leaves DT2 blank; backup string cannot be verified.")
inj("PIT","offense","TE","Darnell Washington","DNP","","2:Robert Tonyan")
# Cleveland / Houston
inj("CLE","offense","QB","Deshaun Watson","NAMED STARTER","","1:Deshaun Watson;2:Shedeur Sanders;3:Dillon Gabriel;4:Taylen Green","Starter announced by team; this is not an injury row and no performance forecast is inferred.")
inj("CLE","offense","C","Elgton Jenkins","DNP","knee","2:Luke Wypler;3:Parker Brailsford")
inj("CLE","defense","FS","Ronnie Hickman Jr.","DNP","concussion","2:Donovan McMillon")
inj("CLE","offense","FB/RB","Michael Burton","DNP","calf","4:Jaleel McLaughlin","Depth chart's position labels differ; do not assume workload equivalence.")
inj("HOU","offense","RB","David Montgomery","DNP","groin","","Houston's fetched depth chart is image-only; depth slot/chain unverified.",verified=False)
inj("HOU","defense","LB","Azeez Al-Shaair","DNP","groin/NIR-personal","","Houston's fetched depth chart is image-only; depth slot/chain unverified.",verified=False)
# Indianapolis / New Orleans
inj("IND","offense","RT","Jalen Travis","DNP","knee","2:Luke Tenuta")
inj("IND","defense","WLB","Jaylon Carlies","DNP","neck","2:Bryce Boettcher;3:Tahj Chambers")
inj("IND","defense","MLB","Akeem Davis-Gaither","DNP","knee","2:CJ Allen;3:Austin Ajiake")
inj("IND","defense","SS","A.J. Haulcy","DNP","ankle","2:Hunter Wohler")
inj("IND","special teams","LS","Luke Rhodes","DNP","hamstring","","Chart has no listed LS2; replacement unverified.")
inj("NO","offense","C","Erik McCoy","DNP","biceps","2:William Sherman")
inj("NO","offense","RB","Alvin Kamara","DNP","NIR-rest/back","2:Audric Estimé","CJ Donaldson also DNP (shoulder); Travis Etienne was limited on IR return. Actual rotation unresolved.")
inj("NO","offense","RB","CJ Donaldson","DNP","shoulder","2:Audric Estimé","Kamara also DNP (NIR-rest/back); Etienne limited on IR return; actual rotation unresolved.")

write_csv("injuries_depth_w10.csv",INJ)

# Provenance register. Scope is the exact fetched page or row family; link presence is not a claim
# that the linked source endorses a model or supplies player-impact coefficients.
SOURCES=[]
def source(sid,category,title,url,scope,caveat=""):
    SOURCES.append({"source_id":sid,"category":category,"title":title,"official_url":url,"checked_on":AS_OF,"scope_checked":scope,"caveat":caveat})
source("NFL-STAND","NFL","2026 regular-season league standings",NFL_STANDINGS,"All 32 teams W-L-T/PF/PA entering Week 10.")
for w in range(1,11): source(f"NFL-SCHED-W{w}","NFL","2026 NFL schedule Week "+str(w),SCHEDULE_URLS[w],f"Schedule/final links and Week {w} game slate; Week 10 venue/time details cross-checked with injury report.")
source("NFL-INJ","NFL","NFL player injury report index",NFL_INJURIES,"Week 10 player status information reviewed in page chunks 0-6.","Dynamic source; snapshot is partial and not a final inactive list.")
source("NFL-W10-IR","NFL","Week 10 injury report / game locations",NFL_W10_REPORT,"All 14 Week 10 matchups, kickoff times, venues and report page body.")
source("NFL-NEWS-NOV11","NFL","NFL news roundup, Wednesday Nov. 11",NFL_NEWS,"Selected Week 10 injuries, IR, starter announcements, signings and status notes.","Dynamic article content; not a complete team injury ledger.")
for sid,ttl,url,scope in [
 ("NFL-STAT-PASS","Team passing statistics",NFL_PASS,"32 team rows"),("NFL-STAT-RUSH","Team rushing statistics",NFL_RUSH,"32 team rows"),
 ("NFL-STAT-DEF-PASS","Team defense passing statistics",NFL_DEF_PASS,"32 team rows"),("NFL-STAT-DEF-RUSH","Team defense rushing statistics",NFL_DEF_RUSH,"32 team rows")]:
    source(sid,"NFL",ttl,url,scope+" for 2026 regular season at the Week 10 snapshot.")
source("NFL-PLAYER-PASS","NFL","2026 player passing statistics",NFL_PLAYER_PASS,"Player passing leaders page; not transcribed into the canonical data tables.","The displayed page is paginated; paired per-game prop outcomes were not available.")
source("NFL-PLAYER-RUSH","NFL","2026 player rushing statistics",NFL_PLAYER_RUSH,"Player rushing leaders page; not transcribed into the canonical data tables.","The displayed page is paginated; paired per-game prop outcomes were not available.")
source("NFL-PLAYER-REC","NFL","2026 player receiving statistics",NFL_PLAYER_REC,"Player receiving leaders page; not transcribed into the canonical data tables.","The displayed page is paginated; paired per-game prop outcomes were not available.")
source("NFL-OPS-SPOTTER","NFL Operations","AT spotters",NFL_OPS_SPOTTER,"NFL role of AT spotters in injury detection, not diagnosis.")
source("NFL-OPS-HEALTH","NFL Operations","Player health and safety",NFL_OPS_HEALTH,"General NFL health/safety context; no injury adjustments derived.")
source("NFL-OPS-PREP","NFL Operations","Game and stadium preparation",NFL_OPS_PREP,"General game-day medical/spotter procedures; not individual player status.")
source("BOOK-DK","Sportsbook","DraftKings NFL game lines",NFL_DK,"Week 10 game spread/total/moneyline quote rows transcribed from public board.","Page did not expose a persistent UTC quote time or jurisdiction; values are a dated snapshot only.")
source("BOOK-FD","Sportsbook","FanDuel NFL game lines",NFL_FD,"Week 10 game spread/total/moneyline quote rows transcribed from public board.","Page did not expose a persistent UTC quote time or jurisdiction; values are a dated snapshot only.")
bye_teams={r["away_team"] for r in schedule if r["status"]=="BYE"}
for t,url in DEPTH_URLS.items():
    meta=DEPTH_PAGE_NOTES.get(t,{})
    scope="Club-site chart page retrieved 2026-11-12; Week 10 team status: "+("bye" if t in bye_teams else "playing")+"."
    caveat=meta.get("authority_note","Some club pages label charts unofficial; listed order does not establish active status or snap share.")
    source("DEPTH-"+t,"Official club",TEAM_NAMES[t]+" depth chart",url,scope,caveat)
write_csv("sources_registry.csv",SOURCES)

print(f"Wrote reviewed inputs to {DATA}: {len(GAMES)} games, {len(STANDINGS)} standings, {len(team_stats)} team-stat rows, {len(schedule)} Week 10 schedule/bye rows, {len(depth_coverage)} depth-chart coverage rows, {len(QUOTE_ROWS)} sportsbook rows, {len(INJ)} selected injury/depth rows, {len(SOURCES)} sources.")

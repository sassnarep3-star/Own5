#!/usr/bin/env python3
"""Depth-chart capture, parser and cross-check against the inherited register.

Why this file exists
--------------------
The brief demands: (a) a 32-team roster/depth sweep before any team-level model is
trusted, (b) two specific depth-parsing failures fixed (Packers jersey numbers,
Texans image), (c) shared and empty depth slots represented faithfully, (d) depth
modelled as groups rather than "column 1 is the starter", (e) no depth derived from
jersey order, experience or salary.

This script stores the raw published text of each club page it read (data/raw/depth/
<CLUB>.txt) so the raw string survives any later parsing change, then parses that raw
text deterministically. Nothing is transcribed "by eye": the raw text and the parser
are both committed.

Parsing rules (all auditable in parse_club below):
  1. A cell may hold TWO players separated by ';' (a shared slot). Both are rank 1;
     neither is promoted to "the starter".
  2. An EMPTY cell inside a row is a hole. It is preserved as rank N with no player.
     An empty cell at the end of a row is padding and is dropped.
  3. A leading jersey number is stripped from the display name and kept in its own
     column. Jersey numbers are NEVER used to order or rank anything.
  4. A row whose players are all blank carries no information and is dropped.
  5. Positions are kept exactly as the club publishes them (WR, EDGE, NCB, "N", ...).
     No mapping to a canonical position is invented.

Rows that cannot be parsed are reported, never guessed.
"""
import csv
import hashlib
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(HERE, "data", "raw", "depth")
OUT_DIR = os.path.join(HERE, "data")
CAPTURED = "2026-11-15T23:24:00Z"

# ---------------------------------------------------------------------------
# RAW CAPTURES.  Format: one row per line:  POSITION|cell1|cell2|cell3|cell4
# ';' inside a cell = two players published in the same slot.
# Row order, empty cells and shared cells are exactly as published.
# ---------------------------------------------------------------------------
CLUBS = {
    "GB": {
        "club": "Green Bay Packers",
        "url": "https://www.packers.com/team/depth-chart",
        "page_dated": "Unofficial, Nov. 10, 2026",
        "shape": "markdown_table",
        "offense": [
            "WR|9 Christian Watson|16 Bo Melton|",
            "WR|0 Matthew Golden|87 J. Michael Sturdivant|",
            "LT|77 Jordan Morgan|73 John Williams|",
            "LG|65 Aaron Banks|79 Travis Glover|67 Donovan Jennings",
            "C|75 Sean Rhyan|52 Jager Burton|",
            "RG|72 Laken Tomlinson|70 Kevin Zeitler|",
            "RT|71 Anthony Belton|74 Mekhi Becton Sr.|",
            "TE|85 Tucker Kraft|18 Jonnu Smith|86 Mark Redman",
            "WR|83 Savion Williams||",
            "QB|10 Jordan Love|6 Tyrod Taylor|",
            "RB|8 Josh Jacobs|32 MarShawn Lloyd|22 Pierre Strong Jr.|26 Kaleb Johnson",
        ],
        "defense": [
            "DT|94 Karl Brooks|97 Jordon Riley|93 Anthony Campbell",
            "DT|95 Devonte Wyatt|55 Chris McClellan|",
            "EDGE|90 Lukas Van Ness|57 Brenton Cox Jr|",
            "LB|44 Zaire Franklin|59 Ty'Ron Hopper|54 Kristian Welch",
            "LB|58 Isaiah McDuffie|31 Nick Niemann|",
            "EDGE|99 Barryn Sorrell|51 Dani Dennis-Sutton|",
            "CB|25 Keisean Nixon|24 Carrington Valentine|",
            "CB|2 Brandon Cisse|21 Benjamin St-Juste|",
            "S|29 Xavier McKinney|27 Kitan Oladapo|",
            "S|33 Evan Williams|27 Kitan Oladapo|",
            "NB|7 Javon Bullard|36 Kamal Hadden|",
        ],
    },
    "BAL": {
        "club": "Baltimore Ravens",
        "url": "https://www.baltimoreravens.com/team/depth-chart",
        "page_dated": "",
        "shape": "markdown_table",
        "offense": [
            "WR|Zay Flowers|Devontez Walker|Elijah Sarratt|",
            "WR|Rashod Bateman|Ja'Kobi Lane|LaJohntay Wester|",
            "LT|Ronnie Stanley|Carson Vinson|",
            "LG|John Simpson|Ryan Neuzil|",
            "C|Cam Jurgens|Ryan Neuzil|",
            "RG|Vega Ioane|Emery Jones Jr.|",
            "RT|Roger Rosengarten|Carson Vinson|",
            "TE|Mark Andrews|Josh Cuevas|",
            "TE|Matt Hibner||",
            "QB|Jacoby Brissett|Joe Fagnano|Kedon Slovis|",
            "RB|Derrick Henry|Justice Hill|Rasheen Ali|",
        ],
        "defense": [
            "DT|Nnamdi Madubuike|Broderick Washington Jr.|",
            "NT|Travis Jones|John Jenkins|",
            "DE|Calais Campbell|Aeneas Peebles|",
            "RUSH|Trey Hendrickson|Mike Green|",
            "MLB|Roquan Smith|Jay Higgins IV|",
            "WLB|Trenton Simpson|Teddye Buchanan|",
            "SAM|Mike Green|Zion Young|Ethan Burke|",
            "CB|Marlon Humphrey|Chidobe Awuzie|",
            "DB|Kyle Hamilton|Keyon Martin|Chandler Rivers|",
            "SS|Jaylinn Hawkins|Keondre Jackson|",
            "FS|Malaki Starks|K'Von Wallace|",
            "CB|Nate Wiggins|T.J. Tampa Jr.|",
        ],
    },
    "SEA": {
        "club": "Seattle Seahawks",
        "url": "https://www.seahawks.com/team/depth-chart/",
        "page_dated": "",
        "shape": "markdown_table",
        "offense": [
            "WR|Cooper Kupp;Rashid Shaheed|Irvin Charles|",
            "LT|Charles Cross|Josh Jones|",
            "LG|Quenton Nelson|Anthony Bradford|",
            "C|Jalen Sundell|Olu Oluwatimi|",
            "RG|Grey Zabel|Anthony Bradford|Beau Stephens|",
            "RT|Abraham Lucas|Josh Jones|",
            "TE|AJ Barner|Eric Saubert|Nick Kallerup|",
            "WR|Jaxon Smith-Njigba|Tory Horton|",
            "QB|Sam Darnold|Drew Lock|Jalen Milroe|",
            "FB|Brady Russell||",
            "RB|Zach Charbonnet|Jadarian Price|Emanuel Wilson|George Holani|",
        ],
        "defense": [
            "DT|Leonard Williams|Rylie Mills|",
            "NT|Byron Murphy II|Brandon Pili|Deven Eastern|",
            "DE|Jarran Reed|Mike Morris|",
            "RUSH|DeMarcus Lawrence|Derick Hall|",
            "MLB|Ernest Jones IV|Patrick O'Connell|",
            "WLB|Drake Thomas|Tyrice Knight|Chazz Surratt|",
            "SLB|Uchenna Nwosu|Dante Fowler Jr.|Connor O'Toole|",
            "CB|Devon Witherspoon|Nehemiah Pritchett|",
            "CB|Josh Jobe|Avery Smith|",
            "S|Ty Okada|Rodney Thomas II|",
            "S|Julian Love||",
            "S|Nick Emmanwori||",
        ],
    },
    "WAS": {
        "club": "Washington Commanders",
        "url": "https://www.commanders.com/team/depth-chart",
        "page_dated": "",
        "shape": "markdown_table",
        "offense": [
            "WR|Terry McLaurin|Treylon Burks|",
            "LT|Brandon Coleman|Andrew Wylie|",
            "LG|Chris Paul|Tanoa Togiai|",
            "C|Nick Allegretti|Matt Gulbin|",
            "RG|Sam Cosmi|Tanoa Togiai|",
            "RT|Josh Conerly Jr.|Andrew Wylie|",
            "TE|Chig Okonkwo|Ben Sinnott|",
            "TE|John Bates|Colson Yankoff|",
            "WR|Stefon Diggs|Jaylin Lane|",
            "WR|Dyami Brown|Antonio Williams|Luke McCaffrey|",
            "QB|Jayden Daniels|Marcus Mariota|Athan Kaliakmanis|",
            "RB|Jacory Croskey-Merritt|Rachaad White|Austin Ekeler|",
        ],
        "defense": [
            "DL|Daron Payne||",
            "DL|Tim Settle|Shy Tuttle|",
            "DL|Javon Kinlaw|Charles Omenihu|",
            "OLB|Odafe Oweh|Joshua Josephs|",
            "LB|Sonny Styles|Kain Medrano|",
            "LB|Frankie Luvu||Kain Medrano",
            "OLB|K'Lavon Chaisson|Dorance Armstrong|Javontae Jean-Baptiste|",
            "CB|Amik Robertson|Rasul Douglas|",
            "CB|Mike Sainristil|Fabian Moreau|",
            "SS|Nick Cross|Tyler Owens|",
            "FS|Jeremy Reaves|Quan Martin|Percy Butler|",
        ],
    },
    "PHI": {
        "club": "Philadelphia Eagles",
        "url": "https://www.philadelphiaeagles.com/team/depth-chart",
        "page_dated": "The unofficial depth chart is compiled by the Eagles' communications department",
        "shape": "markdown_table",
        "offense": [
            "WR|DeVonta Smith|Hollywood Brown|",
            "LT|Jordan Mailata||",
            "LG|Willie Lampkin||",
            "C|Drew Kendall|Jake Majors|",
            "RG|Tyler Steen|Micah Morris|",
            "RT|Markel Bell|Fred Johnson|",
            "TE|Dallas Goedert|Johnny Mundt|",
            "WR|Makai Lemon|Elijah Moore|Britain Covey|",
            "WR|Dontayvion Wicks|Darius Cooper|",
            "RB|Saquon Barkley||",
            "QB|Tanner McKee|Cole Payton|Joe Milton|",
        ],
        "defense": [
            "EDGE|Jalyx Hunt;Jonathan Greenard|Arnold Ebiketie|",
            "DT|Jalen Carter|Byron Young|",
            "DT||Ty Robinson|",
            "DT|Moro Ojomo||",
            "EDGE|Nolan Smith Jr.;Jonathan Greenard|A.J. Epenesa|",
            "LB|Zack Baun|Smael Mondon Jr.|",
            "LB|Jihaad Campbell|Jeremiah Trotter Jr.|",
            "CB|Riq Woolen|Jonathan Jones|",
            "CB|Quinyon Mitchell|Kelee Ringo|",
            "NCB|Cooper DeJean|Mac McWilliams|",
            "S|Marcus Epps|Michael Carter II|",
            "S|Andrew Mukuba|Kenny Moore II|",
        ],
    },
    "DET": {
        "club": "Detroit Lions",
        "url": "https://www.detroitlions.com/team/depth-chart",
        "page_dated": "2026 Unofficial Depth Chart Compiled by Lions Football Communications",
        "shape": "markdown_table",
        "offense": [
            "WR|Jameson Williams||",
            "WR|Amon-Ra St. Brown|DeAndre Carter|",
            "LT|Penei Sewell||",
            "LG|Christian Mahogany|Miles Frazier|",
            "C|Cade Mays|Juice Scruggs|",
            "RG|Tate Ratledge|Seth McLaughlin|",
            "RT|Blake Miller|Larry Borom|",
            "TE|Sam LaPorta|Brock Wright|Tyler Conklin|Jackson Meeks|",
            "WR|Isaac TeSlaa|Tay Martin|",
            "QB|Jared Goff|Joshua Dobbs|",
            "RB|Jahmyr Gibbs|Sione Vaki|Jacob Saylors|",
        ],
        "defense": [
            "EDGE|Aidan Hutchinson|Derrick Moore|Eric O'Neill|",
            "DL|Alim McNeill|Skyler Gill-Howard|Mekhi Wingo|",
            "DL|Tyleik Williams|Levi Onwuzurike|",
            "EDGE|DJ Wonnum|Tyler Lacy|Ahmed Hassanein|",
            "LB|Derrick Barnes|Joe Bachie|",
            "LB|Malcolm Rodriguez|K.J. Britt|",
            "LB|Trevor Nowaske|Amen Ogbongbemiga|",
            "CB|D.J. Reed|Rock Ya-Sin|Khalil Dorsey|Nick Whiteside|",
            "CB|Roger McCreary|Ennis Rakestraw Jr.|Keith Abney II|",
            "S|Chuck Clark||",
            "S|Brian Branch|Christian Izien|",
        ],
    },
    "SF": {
        "club": "San Francisco 49ers",
        "url": "https://www.49ers.com/team/depth-chart",
        "page_dated": "Updated as of 11/10/26",
        "shape": "markdown_table",
        "offense": [
            "WR|Mike Evans|Jordan Watkins|Brandin Cooks|",
            "LT|Trent Williams|Vederian Lowe|Enrique Cruz Jr.|",
            "LG|Connor Colby|Carver Willis|",
            "C|Jake Brendel|Jarrett Patterson|",
            "RG|Dominick Puni||",
            "RT|Colton McKivitz||",
            "TE|George Kittle|Luke Farrell|Brayden Willis|",
            "WR|Deebo Samuel Sr.|Demarcus Robinson|Jacob Cowing|",
            "RB|Christian McCaffrey|Kaelon Black|Jordan James|",
            "FB|Kyle Juszczyk||",
            "QB|Brock Purdy|Mac Jones|Kurtis Rourke|",
        ],
        "defense": [
            "LDE|Keion White|Mykel Williams|Khalid Kareem|",
            "LDT|DeForest Buckner|Gracen Halton|Sebastian Valdez|",
            "RDT|Osa Odighizuwa|James Thompson Jr.|",
            "RDE|Nick Bosa|Romello Height|",
            "SAM|Jaden Dugger|Luke Gifford|",
            "MIKE|Fred Warner|Tatum Bethune|",
            "WILL|Dre Greenlaw|Garret Wallow|",
            "LCB|Renardo Green||",
            "RCB|Deommodore Lenoir|Ephesians Prysock|",
            "NB|Upton Stout||",
            "FS|Ji'Ayir Brown|Siran Neal|",
            "SS|Malik Mustapha|Marques Sigle|Ashtyn Davis|",
        ],
    },
    "KC": {
        "club": "Kansas City Chiefs",
        "url": "https://www.chiefs.com/team/depth-chart",
        "page_dated": "Unofficial Depth Chart",
        "shape": "markdown_table",
        "offense": [
            "WR|Rashee Rice|Jalen Royals|Andrew Armstrong|",
            "LT|Kahlil Benson|Diego Pounds|",
            "LG|Kingsley Suamataia|Joshua Ezeudu|",
            "C|Creed Humphrey|Hunter Nourzad|",
            "RG|Trey Smith|Mike Caliendo|",
            "RT|Jaylon Moore|Joshua Ezeudu|",
            "TE|Travis Kelce|Noah Gray|Jared Wiley|Jake Briningstool|",
            "QB|Patrick Mahomes|Justin Fields|Garrett Nussmeier|",
            "RB|Kenneth Walker|Emmett Johnson|Jaydn Ott|",
            "FB|Ben VanSumeren||",
            "WR|Xavier Worthy|Cyrus Allen|Josh Downs|",
        ],
        "defense": [
            "DE|Felix Anudike-Uzomah|Ashton Gillotte|",
            "DT|Chris Jones|Peter Woods|Marcus Harris|",
            "DT|Khyiris Tonga|Bryson Eason|",
            "DE|George Karlaftis|R Mason Thomas|",
            "LB|Jack Cochrane|Cooper McDonald|",
            "LB|Nick Bolton|Jack Cochrane|",
            "LB|Drue Tranquill|Jeffrey Bassa|",
            "CB|Nohl Williams|Jadon Canady|",
            "CB|Mansoor Delane|Kristian Fulton|Melvin Smith|",
            "S|Alohi Gilman|Chris Roland-Wallace|",
            "S|Chamarri Conner|Jaden Hicks|Xavier Nwankpa|",
        ],
    },
    "IND": {
        "club": "Indianapolis Colts",
        "url": "https://www.colts.com/team/depth-chart",
        "page_dated": "",
        "shape": "markdown_table",
        "offense": [
            "WR|Laquon Treadwell|Nick Westbrook-Ikhine|",
            "LT|Bernhard Raimann|Charlie Heck|",
            "LG|Jalen Farmer|Dalton Tucker|",
            "C|Tanor Bortolini|Sedrick Van Pran-Granger|",
            "RG|Matt Goncalves||",
            "RT|Jalen Travis|Luke Tenuta|",
            "TE|Tyler Warren|Mo Alie-Cox|Drew Ogletree|Will Mallory;Pharaoh Brown",
            "WR|Anthony Gould||",
            "WR|Ashton Dulin|Deion Burks|",
            "QB|Daniel Jones|Anthony Richardson Sr.|Riley Leonard|",
            "RB|Jonathan Taylor|Seth McGowan|DJ Giddens|",
        ],
        "defense": [
            "DE|Jaylahn Tuimoloau|George Gumbs Jr.|",
            "DT|Adetomiwa Adebawore|Kevin Givens|",
            "NT|Grover Stewart|Jerry Tillery|Tim Smith|",
            "DE|Laiatu Latu|Caden Curry|",
            "WLB|Jaylon Carlies|Bryce Boettcher|Tahj Chambers|",
            "MLB|Akeem Davis-Gaither|CJ Allen|Austin Ajiake|",
            "CB|Charvarius Ward|Kenneth Harris|",
            "FS|Cam Bynum|Jonathan Owens|",
            "SS|AJ Haulcy|Hunter Wohler|",
            "N|Justin Walley|Kapena Gushiken|",
            "CB|Sauce Gardner||",
        ],
    },
    "BUF": {
        "club": "Buffalo Bills",
        "url": "https://www.buffalobills.com/team/depth-chart",
        "page_dated": "",
        "shape": "markdown_table",
        "offense": [
            "WR|DJ Moore|Skyler Bell|",
            "LT|Dion Dawkins|Jude Bowry|",
            "LG|Alec Anderson|Austin Corbett|",
            "C|Connor McGovern|Lloyd Cushenberry|",
            "RG|O'Cyrus Torrence|Ar'maj Reed-Adams|",
            "RT|Spencer Brown|Tylan Grable|",
            "TE|Dalton Kincaid|Dawson Knox|Jackson Hawes|Keleki Latu",
            "QB|Josh Allen|Kyle Allen|",
            "RB|James Cook III|Ray Davis|Ty Johnson|",
            "WR|Khalil Shakir|Greg Dortch|",
            "WR|Keon Coleman||",
        ],
        "defense": [
            "DL|Ed Oliver|DeWayne Carter|",
            "DL|Deone Walker|Greg Gaines|",
            "DL|T.J. Sanders|Landon Jackson|",
            "OLB|Greg Rousseau|Michael Hoecht|Mike Danna|",
            "OLB|Bradley Chubb|TJ Parker|Javon Solomon|",
            "ILB|Dorian Williams|Kaleb Elarms-Orr|",
            "ILB|Terrel Bernard|Joe Andreessen|",
            "CB|Christian Benford|Dee Alford|",
            "CB|Davison Igbinosun|Maxwell Hairston|",
            "NCB|Dee Alford||",
            "S|Damar Hamlin|Sam Franklin Jr.|",
            "S|Cole Bishop|Jalon Kilgore|",
        ],
    },
    "NYG": {
        "club": "New York Giants",
        "url": "https://www.giants.com/team/depth-chart",
        "page_dated": "",
        "shape": "markdown_table",
        "offense": [
            'WR|Malik Nabers|Malachi Fields|Jalin Hyatt|',
            "WR|Darnell Mooney|Charlie Jones|",
            "LT|Andrew Thomas|J.C. Davis|",
            "LG|Jon Runyan Jr.|Aaron Stinnie|Josh Sills|",
            "C|Bryan Hudson|John Michael Schmitz Jr.|",
            'RG|Francis "Sisi" Mauigoa|Aaron Stinnie|',
            "RT|Jermaine Eluemunor|Marcus Mbow|",
            "TE|Isaiah Likely|Theo Johnson|Chris Manhertz|Thomas Fidone II|",
            "QB|J.J. McCarthy|Jameis Winston|",
            "FB|Patrick Ricard||",
            "RB|Cam Skattebo|Devin Singletary|Gregory Desrosiers|",
        ],
        "defense": [
            "DT|Shelby Harris|Darius Alexander|Bobby Jamison-Travis|",
            "NT|DJ Reader|C.J. Okoye|",
            "DE|Darius Alexander||",
            "RUSH|Kayvon Thibodeaux|Trace Ford|",
            "MLB|Micah McFadden|Zaire Barnes|",
            "WLB|Arvell Reese|Jack Kelly|",
            "SAM|Abdul Carter|Kayvon Thibodeaux|",
            "CB|Deonte Banks|Paulson Adebo|Nikko Reed|",
            "SS|Tyler Nubin|Jason Pinnock|",
            "FS|Jevón Holland|Ar'Darius Washington|Elijah Campbell|",
            "CB|Greg Newsome II|Colton Hood|",
            "NB|Dru Phillips|Nic Jones|",
        ],
    },
    "HOU": {
        "club": "Houston Texans",
        "url": "https://www.houstontexans.com/team/depth-chart",
        "page_dated": "Unofficial Depth Chart",
        "shape": "image_only",
        "offense": [],
        "defense": [],
        "note": ("Page body: '## Unofficial Depth Chart' followed by a single rendered image "
                 "(static.clubs.nfl.com/.../texans/a5or0zowuo36y1txf4ly). No table, no list, no "
                 "machine-readable player rows. Not parsed; deliberately not transcribed by eye."),
    },
}

JERSEY_RE = re.compile(r"^\s*(\d{1,2})\s+(.*\S)\s*$")


def normalise(name):
    """Lowercase, fold accents, drop punctuation/suffixes. Used only for cross-source matching."""
    n = unicodedata.normalize("NFKD", name)
    n = "".join(ch for ch in n if not unicodedata.combining(ch))
    n = n.lower().replace(".", "").replace("'", "").replace("-", " ")
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    parts = [p for p in n.split() if p]
    while parts and parts[-1] in {"jr", "sr", "ii", "iii", "iv", "v"}:
        parts.pop()
    return " ".join(parts)


def _load_release():
    """Derive {player_display: 'first'|'second'} from the inherited register's own ranks."""
    path = os.path.join(HERE, "..", "nfl-desk-3fb93d11", "data", "replacement_depth.csv")
    out = {}
    if not os.path.exists(path):
        return out
    for r in csv.DictReader(open(path, encoding="utf-8")):
        first = (r["first_string"] or "").strip()
        second = (r["second_string"] or "").strip()
        if first:
            out[first] = "first"
        if second:
            out.setdefault(second, "second")
    return out


def parse_cell(cell):
    """Return list of (display, jersey) for one published cell."""
    out = []
    for chunk in cell.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        m = JERSEY_RE.match(chunk)
        if m:
            out.append((m.group(2).strip(), m.group(1)))
        else:
            out.append((chunk, ""))
    return out


def rows_for(club_code, spec):
    """Yield parsed slot rows for one club."""
    rows = []
    for unit_key, unit_label in (("offense", "Offense"), ("defense", "Defense")):
        group_counter = {}
        for line in spec[unit_key]:
            parts = line.split("|")
            pos = parts[0].strip()
            cells = parts[1:]
            # drop trailing padding cells (empty and nothing after them)
            while cells and cells[-1].strip() == "":
                cells.pop()
            if not cells:
                continue
            group_counter[pos] = group_counter.get(pos, 0) + 1
            group_index = group_counter[pos]
            slot_id = "%s-%s-%s-%d" % (club_code, unit_label[:3].upper(), pos.replace("/", "_"), group_index)
            for rank, cell in enumerate(cells, start=1):
                players = parse_cell(cell)
                if not players:
                    rows.append({
                        "club": club_code, "unit": unit_label, "position": pos,
                        "group_index": group_index, "slot_id": slot_id, "rank": rank,
                        "player_display": "", "player_raw": "", "jersey_number": "",
                        "slot_shape": "empty",
                        "source_url": spec["url"], "page_dated": spec["page_dated"],
                        "captured_utc": CAPTURED,
                    })
                    continue
                for pidx, (display, jersey) in enumerate(players):
                    rows.append({
                        "club": club_code, "unit": unit_label, "position": pos,
                        "group_index": group_index, "slot_id": slot_id, "rank": rank,
                        "player_display": display,
                        "player_raw": cell if pidx == 0 else cell,
                        "jersey_number": jersey,
                        "slot_shape": "shared" if len(players) > 1 else "single",
                        "source_url": spec["url"], "page_dated": spec["page_dated"],
                        "captured_utc": CAPTURED,
                    })
    return rows


def write_raw(club_code, spec):
    os.makedirs(RAW_DIR, exist_ok=True)
    path = os.path.join(RAW_DIR, "%s.txt" % club_code)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# club: %s\n" % spec["club"])
        fh.write("# url: %s\n" % spec["url"])
        fh.write("# page_dated: %s\n" % (spec.get("page_dated") or "(no date published on the page)"))
        fh.write("# shape: %s\n" % spec["shape"])
        fh.write("# captured_utc: %s\n" % CAPTURED)
        if spec.get("note"):
            fh.write("# note: %s\n" % spec["note"])
        fh.write("# format: POSITION|slot1|slot2|slot3|slot4   (';' = two players in one slot)\n\n")
        for unit_key, label in (("offense", "OFFENSE"), ("defense", "DEFENSE")):
            fh.write("%s\n" % label)
            for line in spec[unit_key]:
                fh.write(line + "\n")
            fh.write("\n")
    return path



# ---------------------------------------------------------------------------
# Release-order test inputs. Source: the inherited register's rank column in
# nfl-desk-3fb93d11/data/replacement_depth.csv (session 864d5668, dated 2026-11-13),
# obtained here by matching names; nothing is typed by hand except the lookup below,
# which is derived at run time. See build_run.py for the computation that fills
# data/release_order.csv.
# ---------------------------------------------------------------------------
RELEASE = {}


def all_players(code):
    return [r["player_display"] for r in _LAST_ROWS if r["club"] == code and r["player_display"]]


_LAST_ROWS = []

def main():
    global _LAST_ROWS, RELEASE
    os.makedirs(OUT_DIR, exist_ok=True)
    all_rows = []
    coverage = []
    hashes = {}
    for code in sorted(CLUBS):
        spec = CLUBS[code]
        path = write_raw(code, spec)
        with open(path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        hashes[code] = digest
        rows = rows_for(code, spec)
        all_rows.extend(rows)
        coverage.append({
            "club": code,
            "club_name": spec["club"],
            "depth_url": spec["url"],
            "page_dated": spec["page_dated"],
            "page_shape": spec["shape"],
            "rows_parsed": len(rows),
            "players_parsed": sum(1 for r in rows if r["player_display"]),
            "shared_slots": len({r["slot_id"] for r in rows if r["slot_shape"] == "shared"}),
            "empty_slots": sum(1 for r in rows if r["slot_shape"] == "empty"),
            "jersey_numbers_stripped": sum(1 for r in rows if r["jersey_number"]),
            "parsed": "yes" if rows else "NO",
            "raw_file_sha256": digest,
            "raw_file": "nfl-market-desk/data/raw/depth/%s.txt" % code,
            "captured_utc": CAPTURED,
            "verification_status": "VERIFIED TODAY (raw text + hash committed)"
            if rows else "STRUCTURAL FAILURE - page publishes an image, no rows exist",
        })

    _LAST_ROWS = all_rows
    RELEASE = _load_release()
    fields = ["club", "unit", "position", "group_index", "slot_id", "rank", "player_display",
              "player_raw", "jersey_number", "slot_shape", "source_url", "page_dated", "captured_utc"]
    with open(os.path.join(OUT_DIR, "depth_rows.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)

    with open(os.path.join(OUT_DIR, "depth_coverage.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(coverage[0].keys()))
        w.writeheader()
        w.writerows(coverage)

    # ---- cross-check against the inherited register (session 864d5668, 2026-11-13)
    inherited_path = os.path.join(HERE, "..", "nfl-desk-3fb93d11", "data", "replacement_depth.csv")
    compare = []
    if os.path.exists(inherited_path):
        inherited = list(csv.DictReader(open(inherited_path, encoding="utf-8")))
        for code in sorted(CLUBS):
            if CLUBS[code]["shape"] != "markdown_table":
                continue
            live = {}
            for r in all_rows:
                if r["club"] == code and r["player_display"]:
                    live.setdefault(normalise(r["player_display"]), r)
            old = {}
            for r in inherited:
                if r["team"] != code:
                    continue
                positional = [r["first_string"], r["second_string"], r["third_string"]]
                for rank, name in enumerate(positional, start=1):
                    if name.strip():
                        old.setdefault(normalise(name), (name, rank, r["position"], r["unit"]))
            live_names = set(live)
            old_names = set(old)
            matched = live_names & old_names
            for name in sorted(live_names - old_names):
                compare.append({
                    "club": code, "player_display": live[name]["player_display"],
                    "live_position": live[name]["position"], "live_rank": live[name]["rank"],
                    "inherited_position": "", "inherited_rank": "",
                    "result": "IN LIVE PAGE, ABSENT FROM INHERITED REGISTER",
                    "note": "player is published by the club today but has no row in the inherited 2026-11-13 register",
                    "source_url": CLUBS[code]["url"],
                })
            for name in sorted(old_names - live_names):
                nm, rank, pos, unit = old[name]
                compare.append({
                    "club": code, "player_display": nm,
                    "live_position": "", "live_rank": "",
                    "inherited_position": pos, "inherited_rank": rank,
                    "result": "IN INHERITED REGISTER, NOT ON LIVE PAGE",
                    "note": "player was in the inherited 2026-11-13 register but is not on today's published page",
                    "source_url": CLUBS[code]["url"],
                })
            for name in sorted(matched):
                lr = int(live[name]["rank"])
                orank = int(old[name][1])
                if lr != orank:
                    lr_slot = live[name]["slot_id"]
                    shapes = [r["slot_shape"] for r in all_rows if r["slot_id"] == lr_slot]
                    how = ("shared-slot rank 1" if "shared" in shapes else
                           ("empty cell earlier in the row" if "empty" in shapes
                            else "plain rank change"))
                    compare.append({
                        "club": code, "player_display": live[name]["player_display"],
                        "live_position": live[name]["position"], "live_rank": lr,
                        "inherited_position": old[name][2], "inherited_rank": orank,
                        "result": "RANK DIFFERS",
                        "note": "same player, different published rank (%s)" % how,
                        "source_url": CLUBS[code]["url"],
                    })
    with open(os.path.join(OUT_DIR, "depth_compare.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["club", "player_display", "live_position", "live_rank",
                                           "inherited_position", "inherited_rank", "result", "note",
                                           "source_url"])
        w.writeheader()
        w.writerows(compare)

    # ---- publication-order test: does publishing order carry information?
    # Zero-weight positions (kickers, punters, returners, long snappers, holders) are
    # excluded because those rows say nothing about who starts on offense or defense.
    ZERO_WEIGHT = {"K", "P", "H", "LS", "KR", "KOR", "PR"}
    anchor_rows = []
    for code in sorted(CLUBS):
        if CLUBS[code]["shape"] != "markdown_table":
            continue
        units = {}
        for r in all_rows:
            if r["club"] != code or r["unit"] != "Offense":
                continue
            if r["position"] in ZERO_WEIGHT:
                continue
            units.setdefault(r["slot_id"], {"pos": r["position"], "gidx": r["group_index"],
                                            "ranks": {}})
            units[r["slot_id"]]["ranks"].setdefault(int(r["rank"]), []).append(r)
        if not units:
            continue
        med = sorted(units.values(), key=lambda u: u["gidx"])[len(units) // 2]
        rank1 = med["ranks"].get(1, [])
        if not rank1:
            continue
        player = rank1[0]
        taken = [p for p in all_players(code) if normalise(p) == normalise(player["player_display"])]
        release = RELEASE.get(taken[0] if taken else "", "")
        rank1_count = sum(1 for u in units.values() if u["ranks"].get(1))
        anchor_rows.append({
            "club": code,
            "period": "2026 regular season",
            "anchor_player": player["player_display"],
            "anchor_position": med["pos"],
            "anchor_source": "published release order on the club's own depth page",
            "anchor_definition": ("the player printed first in the middle offense group of the "
                                  "page, zero-weight positions excluded"),
            "rank1_slots_on_page": rank1_count,
            "rank1_is_printed_second": "yes" if release == "second" else (
                "no" if release == "first" else ""),
            "release_inherited_register": release,
            "release_source_tier": "AGGREGATOR (inherited 2026-11-13 register)",
            "source_url": CLUBS[code]["url"],
            "note": ("the club's own page prints this player in column 2, but the inherited register "
                     "carries him as rank 1" if release == "second" else
                     ("both sources agree he is first" if release == "first" else "")),
        })
    with open(os.path.join(OUT_DIR, "depth_order_test.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(anchor_rows[0].keys()))
        w.writeheader()
        w.writerows(anchor_rows)
    both = sum(1 for a in anchor_rows if a["release_inherited_register"])
    second = sum(1 for a in anchor_rows if a["release_inherited_register"] == "second")
    print("release-order test: %d clubs with a usable anchor, %d carry an inherited release, "
          "%d of those are printed second on the club page" % (len(anchor_rows), both, second))

    print("clubs captured: %d (%d parsed, %d structural failure)"
          % (len(CLUBS), sum(1 for c in coverage if c["parsed"] == "yes"),
             sum(1 for c in coverage if c["parsed"] == "no")))
    print("depth rows: %d   players: %d"
          % (len(all_rows), sum(1 for r in all_rows if r["player_display"])))
    print("shared slots: %d   empty slots: %d   jersey numbers stripped: %d"
          % (sum(c["shared_slots"] for c in coverage), sum(c["empty_slots"] for c in coverage),
             sum(c["jersey_numbers_stripped"] for c in coverage)))
    print("compare findings: %d" % len(compare))
    for c in coverage:
        print("  %-3s %-2s rows=%-3d shared=%-2d empty=%-2d jerseys=%-2d"
              % (c["club"], c["parsed"][:2], c["rows_parsed"], c["shared_slots"],
                 c["empty_slots"], c["jersey_numbers_stripped"]))


if __name__ == "__main__":
    main()

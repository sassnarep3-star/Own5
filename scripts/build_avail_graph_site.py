#!/usr/bin/env python3
"""Build the static site for the Official Availability Graph desk (session 47e3185b).

Deterministic: no clock, no network, no git.  Every page is rendered from the
committed CSVs under data/avail-graph/.  Every table row carries either a
source link or an explicit blank-and-flag badge.

Usage:  python3 scripts/build_avail_graph_site.py
"""
from __future__ import annotations

import csv
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "avail-graph"
OUT = ROOT / "nfl-avail-graph"

DESK_TITLE = "Official Availability Graph & Game-Day Ledger"
DESK_SUB = "Week 10 (2026) official capture, depth coverage and availability ledger"
CAPTURE_STAMP = "2026-11-18"

PAGES = [
    ("index.html", "Overview"),
    ("results.html", "Results"),
    ("venues.html", "Venues"),
    ("availability.html", "Availability"),
    ("depth.html", "Depth"),
    ("replacements.html", "Replacements"),
    ("gamebooks.html", "Game Books"),
    ("inactives.html", "Inactives"),
    ("week11.html", "Week 11"),
    ("injuries.html", "Injuries"),
    ("events.html", "Events"),
    ("flags.html", "Flagged"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("sources.html", "Sources"),
    ("executive-summary.html", "Executive summary"),
]


def read(name: str) -> list[dict]:
    path = DATA / name
    if not path.exists():
        return []
    with path.open() as fh:
        return list(csv.DictReader(fh))


def esc(value: str) -> str:
    return html.escape(value or "", quote=True)


def link(url: str, label: str | None = None) -> str:
    if not url:
        return ""
    text = label or url
    return f'<a href="{esc(url)}" rel="noopener">{esc(text)}</a>'


def cell(value: str, source_url: str = "", badge: str = "") -> str:
    """A table cell: value, or a blank-and-flag badge when the value is absent."""
    if value:
        body = esc(value)
        if source_url:
            body += " " + link(source_url, "source")
        return body
    if badge:
        return f'<span class="flag">{esc(badge)}</span>'
    return '<span class="blank">not published by the official source</span>'


def table(headers: list[str], rows: list[list[str]], caption: str = "") -> str:
    parts = ["<table>"]
    if caption:
        parts.append(f"<caption>{esc(caption)}</caption>")
    parts.append("<thead><tr>" + "".join(f"<th>{esc(h)}</th>" for h in headers) + "</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    parts.append("</tbody></table>")
    return "".join(parts)


def nav(current: str) -> str:
    items = []
    for filename, label in PAGES:
        cls = ' class="current"' if filename == current else ""
        items.append(f'<li{cls}><a href="{filename}">{esc(label)}</a></li>')
    return '<nav><ul>' + "".join(items) + "</ul></nav>"


def page(filename: str, title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} &mdash; {esc(DESK_TITLE)}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
<h1>{esc(DESK_TITLE)}</h1>
<p class="sub">{esc(DESK_SUB)}</p>
<p class="stamp">Capture stamp: {esc(CAPTURE_STAMP)} &middot; every value below is read from an official source and linked</p>
</header>
{nav(filename)}
<main>
{body}
</main>
<footer>
<p>Session <code>arena/47e3185b-own5</code>. Data namespace <code>data/avail-graph/</code>; site namespace <code>nfl-avail-graph/</code>.
Built by <code>scripts/build_avail_graph_site.py</code> from committed CSVs only &mdash; no clock, no network, no git at build time.
Where an official source does not publish a value the cell is left blank and flagged; nothing is inferred.</p>
</footer>
</body>
</html>
"""


# ---------------------------------------------------------------------------
def page_index() -> str:
    fixtures = read("gamecentre_captures_2026-11-18.csv")
    coverage = read("depth_coverage.csv")
    graph = read("availability_graph.csv")
    reps = read("replacements.csv")
    designated = read("injury_designations_2026-11-18.csv")
    delta = read("injury_delta.csv")
    flags = read("flags.csv")

    parsed = [c for c in coverage if c["page_shape"] != "image_only"]
    blank_expected = sum(1 for g in graph if not g["expected_starter"])
    stats = [
        ("Week 10 fixtures captured from the official game centres", str(len(fixtures)), "results.html"),
        ("Official club depth charts captured (all 32 clubs)", str(len(coverage)), "depth.html"),
        ("Depth charts that parse into rows", f"{len(parsed)} of {len(coverage)}", "depth.html"),
        ("Depth-chart slots transcribed", str(sum(int(c["rows_parsed"]) for c in coverage)) + " groups", "depth.html"),
        ("Official injury-report rows captured (all players)", str(len(read("injury_report_all_2026-11-18.csv"))), "injuries.html"),
        ("Players with an official designation (Out / Doubtful / Questionable)", str(len(designated)), "injuries.html"),
        ("Changes between the 2026-11-15 read and the 2026-11-18 read", str(len(delta)), "injuries.html"),
        ("Official inactive players captured (all 14 fixtures)", str(len(read("inactives_week10.csv"))), "inactives.html"),
        ("Official availability events with a dated official source", str(len(read("availability_events.csv"))), "events.html"),
        ("Availability-graph rows (one per official depth-chart group)", str(len(graph)), "availability.html"),
        ("Groups whose first slot has no available name (Out or officially inactive)", str(sum(1 for g in graph if "AG-18" in g["flags"])), "availability.html"),
        ("Out-designation replacements published", str(len(reps)), "replacements.html"),
        ("Open flags", str(sum(1 for f in flags if f["status"] != "closed")), "flags.html"),
        ("Official Week 11 fixtures with a game-centre venue", str(len(read("week11_slate_official.csv"))), "week11.html"),
    ]
    rows = [[esc(a), esc(b), link(c)] for a, b, c in stats]
    body = f"""
<h2>What this desk is</h2>
<p>This desk publishes the official, point-in-time record of who was available and who was expected to start for the
2026 NFL Week 10 slate, together with the official results and venues for the same 14 fixtures. Every row on every page
carries a link to the official page it was read from. Where an official source does not print a value the cell is
<strong>left blank and flagged</strong> &mdash; nothing on this site is inferred, and no depth order is modelled from
jersey number, salary, experience or snap count.</p>

<h2>Headline counts</h2>
{table(["Measure", "Value", "Page"], rows)}

<h2>What is deliberately blank</h2>
<p>Three things this desk could not obtain, each published with the reason and the official link that would close it:</p>
<ul>
<li><strong>Actual starters.</strong> The official NFL Game Book PDF could not be read in this environment
(<code>static.www.nfl.com</code> refuses a TLS handshake). Every availability row therefore shows an empty actual-starter
cell, the reason in words, and the official PDF link. <a href="flags.html">Flagged &rarr;</a></li>
<li><strong>Houston Texans depth.</strong> The club publishes its depth chart as a single image. Transcribing it by eye
would create an inferred depth order, so the Texans have no depth rows and their replacement cells are blank and flagged.</li>
<li><strong>The Week 11 league injury report.</strong> The league's own Week 11 URL still serves the Week 10 report, so
no Week 11 designation is published here.</li>
</ul>

<h2>How to read a depth group</h2>
<p>A depth chart row is a <em>group</em>, not a single starter. The club prints slots in order; a slot may hold more than
one name (a shared slot, printed with a semicolon) and may be empty. Both are preserved exactly as printed, and the
position family is only ever used as a join key between two official records &mdash; never as a depth model.</p>
{table(
    ["Slot", "Meaning as printed by the club", "Example official chart"],
    [
        ["1st", "the first name the club prints in the group", link("https://www.jaguars.com/team/depth-chart", "Jaguars chart")],
        ["2nd", "the next name the club prints in the group", link("https://www.jaguars.com/team/depth-chart", "Jaguars chart")],
        ["<em>empty slot</em>", "the club prints a slot with no name; it is preserved, not closed up with a guess", link("https://www.chicagobears.com/team/depth-chart", "Bears chart")],
        ["<em>shared slot</em>", "the club prints more than one name in the same slot; all of them are kept", link("https://www.49ers.com/team/depth-chart", "49ers chart")],
    ],
)}
"""
    return page("index.html", "Overview", body)


def page_results() -> str:
    fixtures = read("gamecentre_captures_2026-11-18.csv")
    rows = []
    for f in fixtures:
        rows.append([
            esc(f["game_id"]),
            esc(f["kickoff_date"]),
            f'{esc(f["away"])} {esc(f["away_score"])} &ndash; {esc(f["home_score"])} {esc(f["home"])}',
            esc(f["result"]),
            esc(f["home_margin"]),
            esc(f["total_points"]),
            esc(f["status"]),
            link(f["game_page_url"], "game centre"),
            link(f["schedule_source_url"], "schedule"),
            link(f["score_source_url"], "score source"),
        ])
    body = f"""
<h2>Official Week 10 results &mdash; all 14 fixtures</h2>
<p>Every score is printed by an official NFL page. The <em>score source</em> column names the page the score was read
from, because two official game centres render their scores as <em>Hidden Score</em> and the final was therefore taken
from the official by-week schedule page.</p>
{table(
    ["Game", "Date", "Final", "Result", "Home margin", "Total", "Status", "Game centre", "Schedule", "Score source"],
    rows,
    "2026 Week 10, 14 fixtures",
)}
<p class="note">Home margin is the home club's points minus the away club's points; a negative value means the away club
won. Total is the combined score. Both are arithmetic on the published scores, not separate official fields.</p>
"""
    return page("results.html", "Results", body)


def page_venues() -> str:
    fixtures = read("gamecentre_captures_2026-11-18.csv")
    rows = []
    for f in fixtures:
        rows.append([
            esc(f["game_id"]),
            esc(f["away"]), esc(f["home"]),
            cell(f["location_official"], f["game_page_url"]),
            cell(f["stadium_official"], f["game_page_url"]),
            link(f["game_page_url"], "official game centre"),
        ])
    body = f"""
<h2>Official venues</h2>
<p>Location and stadium are the official game centre's own <code>Game Info</code> fields. No venue is inferred from a
city, a stadium nickname or a ticket link.</p>
{table(
    ["Game", "Away", "Home", "Official location", "Official stadium", "Source"],
    rows,
    "Week 10 venues from the official game-centre Game Info block",
)}
<h3>Note on the Munich fixture</h3>
<p>The Patriots-Lions game was played in Munich: the official game centre prints Location <code>MUNICH</code> and Stadium
<code>FC BAYERN MUNICH STADIUM</code>. The official by-week schedule page carries a <em>Munich 2026</em> mark beside the same
fixture. An earlier note in this repository recorded a <em>Mexico City 2026</em> mark for it; that note is superseded by
the game-centre fields, which are the source of record. <a href="flags.html">Flagged &rarr;</a></p>
"""
    return page("venues.html", "Venues", body)


def page_availability() -> str:
    graph = read("availability_graph.csv")
    rows = []
    for g in graph:
        rows.append([
            esc(g["club"]),
            esc(g["unit"]),
            esc(g["group_position"]),
            esc(g["chart_slots_ordered"]),
            cell(g["designation_states"], g["designation_source_url"]),
            cell(g["official_inactive_list"], g["official_inactive_source_url"]),
            cell(g["announced_starter"], g["announced_starter_source_url"]),
            cell(g["expected_starter"], g["source_url"]),
            cell(g["actual_starter"], "", "BLANK &mdash; official Game Book not readable in this environment"),
            link(g["gamebook_pdf_url"], "official Game Book"),
            esc(g["flags"]) if g["flags"] else "",
        ])
    body = f"""
<h2>Availability graph &mdash; one row per official depth-chart group</h2>
<p>Each row joins four official records: the club's own depth chart, the league's official injury report, the league's
official game-day inactive list, and the league's official news where it announces a starter. The expected starter is the
first slot of the official group, minus any player the official report designates <em>Out</em> and minus any player on
the official inactive list; where the league has announced a starter, that announcement wins. The actual starter comes
from the official Game Book, which could not be read here, so that cell is blank and every row carries the official PDF
link.</p>
{table(
    ["Club", "Unit", "Group", "Official chart slots", "Official designation", "Officially inactive",
     "Announced starter", "Expected starter", "Actual starter", "Game Book", "Flags"],
    rows,
    f"{len(graph)} official depth-chart groups across 32 clubs",
)}
<p class="note">A shared slot keeps every name the club printed in it. An empty slot is preserved. No player is placed in a
group by inference, and no depth string is produced from jersey number, salary, experience or snap count.</p>
"""
    return page("availability.html", "Availability", body)


def page_depth() -> str:
    coverage = read("depth_coverage.csv")
    rows = []
    for c in coverage:
        rows.append([
            esc(c["club"]),
            esc(c["club_name"]),
            link(c["depth_url"], "official chart"),
            esc(c["page_dated"]),
            esc(c["chart_label"]),
            esc(c["page_shape"]),
            esc(c["rows_parsed"]),
            esc(c["players_parsed"]),
            esc(c["shared_slots"]),
            esc(c["empty_slots"]),
            esc(c["captured_utc"]),
            esc(c["raw_file_sha256"])[:16] + "&hellip;",
            esc(c["verification_status"]),
        ])
    body = f"""
<h2>Official depth-chart coverage &mdash; all 32 clubs</h2>
<p>Every club's own depth page was read. The chart label column reproduces the club's own wording, because most of these
pages describe the chart as unofficial or as compiled by the club's communications department. Presenting an
unofficial chart as an official ordering would overstate it.</p>
{table(
    ["Club", "Name", "Official chart", "Date printed on the page", "Club's own label", "Shape",
     "Groups", "Names", "Shared slots", "Empty slots", "Captured (UTC)", "sha256", "Verification"],
    rows,
    "32 clubs",
)}
<h3>What the numbers mean</h3>
<ul>
<li><strong>Groups</strong> &mdash; the number of position rows the club prints for offense and defense. Special teams rows
are not transcribed.</li>
<li><strong>Names</strong> &mdash; the number of player names printed across those groups.</li>
<li><strong>Shared slots</strong> &mdash; slots where the club prints more than one name.</li>
<li><strong>Empty slots</strong> &mdash; slots the club prints with no name. They are preserved, not closed up.</li>
</ul>
"""
    return page("depth.html", "Depth", body)


def page_replacements() -> str:
    reps = read("replacements.csv")
    rows = []
    for r in reps:
        rows.append([
            esc(r["club"]),
            esc(r["unit"]),
            esc(r["group_position"]),
            esc(r["out_player"]),
            cell(r["designation"], r["designation_source_url"]),
            esc(r["chart_depth_string"]),
            cell(r["replacement_named"], r["chart_source_url"], "BLANK &mdash; the official chart prints no further available name in this group"),
            esc(r["replacement_depth_string"]),
            cell(r["replacement_confirmed_by_official_announcement"], r["announcement_source_url"]),
            esc(r["flags"]),
        ])
    body = f"""
<h2>Replacements for every official <em>Out</em> designation</h2>
<p>One row per player the official Week 10 report designates <em>Out</em> who appears in the club's own depth chart. The
replacement is the next available name the club prints in the same group, with its depth string. It is not a claim that
the replacement started: the actual starter is only knowable from the official Game Book, which could not be read here.</p>
{table(
    ["Club", "Unit", "Group", "Player", "Designation", "Chart depth", "Replacement named",
     "Replacement depth", "Confirmed by an official announcement", "Flags"],
    rows,
    f"{len(reps)} Out designations with a published depth-chart row",
)}
"""
    return page("replacements.html", "Replacements", body)


def page_gamebooks() -> str:
    fixtures = read("gamecentre_captures_2026-11-18.csv")
    rows = []
    for f in fixtures:
        rows.append([
            esc(f["game_id"]),
            f'{esc(f["away"])} at {esc(f["home"])}',
            esc(f["kickoff_date"]),
            link(f["gamebook_pdf_url"], "official Game Book (PDF)"),
            '<span class="flag">UNVERIFIED &mdash; the PDF could not be read in this environment (the host refuses a TLS handshake)</span>',
        ])
    body = f"""
<h2>Official Game Books</h2>
<p>The Game Book is the NFL's own record of the starting lineup and the inactive list. Each PDF below was read from the
official game centre's <em>Download Game Book</em> link. The desk publishes the link for every fixture, but the PDF itself
could not be opened in this environment, so <strong>no starting lineup or inactive list is published</strong>. This is the
single largest gap in the desk and it is listed as a blocking flag.</p>
{table(
    ["Game", "Fixture", "Date", "Official Game Book", "Parsing status"],
    rows,
    "14 Week 10 Game Books",
)}
<p class="note">The Game Book link for each fixture is the URL the official game centre prints, so the link itself is an
official artefact even though the document could not be read here.</p>
"""
    return page("gamebooks.html", "Game Books", body)


def page_inactives() -> str:
    inactive = read("inactives_week10.csv")
    fixtures = read("gamecentre_captures_2026-11-18.csv")
    by_game: dict[str, list[dict]] = {}
    for row in inactive:
        by_game.setdefault(row["game_id"], []).append(row)
    blocks = []
    for f in fixtures:
        gid = f["game_id"]
        rows = by_game.get(gid, [])
        if not rows:
            continue
        rows.sort(key=lambda r: (r["club"], r["position"]))
        body = [
            f'<h3>{esc(f["away"])} at {esc(f["home"])} &mdash; {esc(f["kickoff_date"])}</h3>',
            table(
                ["Club", "Inactive", "Pos", "Note", "Source"],
                [[esc(r["club"]), esc(r["player"]), esc(r["position"]),
                  esc(r["note"]) if r["note"] else "",
                  link(r["source_url"], "official list")] for r in rows],
                f"{len(rows)} players deactivated by the clubs",
            ),
        ]
        blocks.append("".join(body))
    body = f"""
<h2>Official inactive lists &mdash; all 14 Week 10 fixtures</h2>
<p>The NFL publishes each club's game-day inactive list. A player on it did not play, so the club's own depth chart
cannot have started him. This is the official record that the unreadable Game Book would otherwise supply, and it is
joined into the availability graph: every chart name that appears here is excluded from the expected-starter
calculation, and the affected row says so.</p>
<p>These are the clubs' own declarations, published by the league. A player can be inactive without being injured
(a coaching decision) and a player can be active while carrying a designation, so an inactive list and an injury
report are not the same thing and both are published.</p>
{''.join(blocks)}
<p class="note">Total deactivated players captured: {len(inactive)} across {len(by_game)} fixtures. Sources: the
official NFL Week 10 inactives article and the official Thursday-night and Monday-night inactives articles, each linked
on its own row.</p>
"""
    return page("inactives.html", "Inactives", body)


def page_injuries() -> str:
    all_rows = read("injury_report_all_2026-11-18.csv")
    designated = read("injury_designations_2026-11-18.csv")
    delta = read("injury_delta.csv")
    normalised = read("injury_delta_normalised.csv")
    nrows = []
    for d in normalised:
        nrows.append([
            esc(d["club"]),
            esc(d["player"]),
            esc(d["field"]),
            esc(d["value_2026_11_15"]) if d["value_2026_11_15"] else '<span class="blank">empty</span>',
            esc(d["value_2026_11_18"]) if d["value_2026_11_18"] else '<span class="blank">empty</span>',
            esc(d["difference_class"]),
            esc(d["normalisation_applied"]),
            link(d["source_url"], "official report"),
        ])
    rows = []
    for d in designated:
        rows.append([
            esc(d["club"]),
            esc(d["player"]),
            esc(d["position"]),
            esc(d["injury_description"]) if d["injury_description"] else "",
            esc(d["practice_status"]),
            esc(d["game_status"]),
            link(d["source_url"], "official report"),
            esc(d["captured_utc"]),
        ])
    drows = []
    for d in delta:
        drows.append([
            esc(d["club"]),
            esc(d["player"]),
            esc(d["field"]),
            esc(d["value_2026_11_15"]),
            esc(d["value_2026_11_18"]),
            esc(d["change"]),
            esc(d["note"]),
            link(d["source_url"], "official report"),
        ])
    body = f"""
<h2>Official Week 10 injury report &mdash; designated players</h2>
<p>{len(designated)} of the {len(all_rows)} player rows on the official Week 10 report carry an <em>Out</em>,
<em>Doubtful</em> or <em>Questionable</em> designation. The designation level on its own is not a signal: the delta between
two dated reads is. The full all-player capture (including every row with no designation) is committed alongside this
table.</p>
{table(
    ["Club", "Player", "Pos", "Injury", "Practice status", "Game status", "Source", "Captured (UTC)"],
    rows,
    f"{len(designated)} designated players of {len(all_rows)} official rows across 28 clubs",
)}
<h2>Delta against the committed 2026-11-15 read</h2>
<p>This is the surprise signal: what <em>changed</em> between two dated reads of the same official page, not what the page
says in absolute terms.</p>
{table(
    ["Club", "Player", "Field", "Value on 2026-11-15", "Value on 2026-11-18", "Change", "Note", "Source"],
    drows,
    f"{len(drows)} field changes between the two reads",
)}
<p class="note">Four clubs (CHI, DEN, PHI, TB) were on bye in Week 10 and have no report rows at all, so they are absent
from both reads. That absence means 'no fixture', not 'no injury'.</p>
<h2>Normalisation audit &mdash; what the delta above deliberately does not show</h2>
<p>A delta that hides a normalisation is not a complete diff, so every difference the comparison normalises away is
published here. Two normalisations apply. First, an empty injury cell and the literal token
<em>BLANK</em> both mean the official page listed no injury; the committed 2026-11-15 read wrote the token and the
2026-11-18 capture writes an empty cell. Second, the official page prints more than one injury for some players and
separates the names with a comma; that separator is canonicalised to ", " before the two reads are compared, so a change
in the separator's whitespace could never register as a change.</p>
<p>The rows below are the ones those two rules touch. They are not hidden, and they are not changes: they are the
difference between how two reads wrote the same fact.</p>
{table(
    ["Club", "Player", "Field", "Value on 2026-11-15", "Value on 2026-11-18", "Class", "Normalisation applied", "Source"],
    nrows,
    f"{len(nrows)} rows the comparison normalises; {len(delta)} substantive changes are listed above",
)}
"""
    return page("injuries.html", "Injuries", body)


def page_week11() -> str:
    slate = read("week11_slate_official.csv")
    byes = read("week11_byes_official.csv")
    rows = []
    for f in slate:
        rows.append([
            esc(f["away"]),
            esc(f["home"]),
            esc(f["kickoff_date"]),
            esc(f["kickoff_time_et"]),
            esc(f["network"]),
            esc(f["location_official"]),
            esc(f["stadium_official"]),
            link(f["game_page_url"], "official game centre"),
        ])
    brows = [[esc(b["club"]), esc(b["club_name"]) if b.get("club_name") else "",
              link(b["source_url"], "official schedule")]
             for b in byes]
    body = f"""
<h2>Official Week 11 slate</h2>
<p>Every Week 11 fixture with the official game centre's own <em>Location</em> and <em>Stadium</em> fields. These are
read from the official game centre rather than inferred from the city name, so the two Mexico City and Landover entries
below carry the stadium the league prints, not a venue that was looked up.</p>
{table(
    ["Away", "Home", "Date", "Kickoff (ET)", "Network", "Location", "Stadium", "Source"],
    rows,
    f"{len(slate)} official Week 11 fixtures",
)}
<h2>Official Week 11 byes</h2>
<p>The NFL publishes the teams on bye for each week. A club on bye has no fixture and therefore no official report row,
no game-day inactive list and no game to read a starter from.</p>
{table(
    ["Club", "Club name", "Source"],
    brows,
    f"{len(byes)} clubs on bye in Week 11",
)}
<p class="note">The Week 11 availability graph is not published yet: the official Week 11 injury report, the official
Week 11 inactive lists and the Week 11 depth charts have not been captured. Publishing the slate and the byes now is
the honest starting point &mdash; the graph follows when those captures exist.</p>
"""
    return page("week11.html", "Week 11", body)


def page_events() -> str:
    events = read("availability_events.csv")
    rows = []
    for e in events:
        rows.append([
            esc(e["event_id"]),
            esc(e["published_date"]) if e["published_date"] else '<span class="blank">no date printed</span>',
            esc(e["club"]),
            esc(e["players"]),
            esc(e["event_type"]),
            esc(e["headline"]),
            link(e["source_url"], "official source"),
            esc(e["evidence_note"]),
        ])
    body = f"""
<h2>Official availability events</h2>
<p>Injured-reserve placements, trades, waivers, announced starters and in-game injuries, each with the official league or
club page that carries it. These events are what turn a designation into a change in the expected lineup: a player who is
on injured reserve does not appear on the weekly report at all, so "not listed" and "not available" are different things.</p>
{table(
    ["ID", "Published", "Club", "Player(s)", "Type", "Headline as published", "Source", "Note"],
    rows,
    f"{len(events)} official events",
)}
"""
    return page("events.html", "Events", body)


def page_flags() -> str:
    flags = read("flags.csv")
    rows = []
    for f in flags:
        sev = f["severity"]
        cls = {"BLOCKING": "blocking", "REVIEW": "review", "CLOSED": "closed"}.get(sev, "review")
        rows.append([
            esc(f["flag_id"]),
            f'<span class="sev {cls}">{esc(sev)}</span>',
            esc(f["area"]),
            esc(f["what"]),
            esc(f["why_it_matters"]),
            esc(f["what_would_clear_it"]),
            link(f["source_url"], "evidence"),
            esc(f["status"]),
        ])
    body = f"""
<h2>Flagged items</h2>
<p>Everything this desk could not verify, and everything that a careful reader should check. A flag is never a silent
omission: each one names what was seen, why it matters, what would clear it, and the official link that carries the
evidence.</p>
{table(
    ["ID", "Severity", "Area", "What", "Why it matters", "What would clear it", "Evidence", "Status"],
    rows,
    f"{len(flags)} flags",
)}
"""
    return page("flags.html", "Flagged", body)


def page_questions() -> str:
    qs = read("questions.csv")
    rows = []
    for q in qs:
        rows.append([
            esc(q["id"]),
            esc(q["question"]),
            esc(q["why_it_blocks_a_decision"]),
            esc(q["what_we_have"]),
            esc(q["what_is_missing"]),
            esc(q["how_to_discover_it"]),
            esc(q["answer_status"]),
            link(q["source_url"], "source"),
        ])
    body = f"""
<h2>Open questions</h2>
<p>Each question names what is blocked, what is already held, what is missing, and how it would be discovered. The answer
column is <em>open</em> for every row: none of these has been closed by this session.</p>
{table(
    ["ID", "Question", "Why it blocks a decision", "What we have", "What is missing",
     "How to discover it", "Status", "Source"],
    rows,
    f"{len(qs)} open questions",
)}
"""
    return page("questions.html", "Questions", body)


def page_suggestions() -> str:
    ss = read("suggestions.csv")
    rows = []
    for s in ss:
        rows.append([
            esc(s["id"]),
            esc(s["suggestion"]),
            esc(s["problem_it_solves"]),
            esc(s["expected_impact"]),
            esc(s["effort"]),
            esc(s["confidence"]),
            esc(s["decision_state"]),
            link(s["source_url"], "source"),
        ])
    body = f"""
<h2>Suggestions register</h2>
<p>Reviewable proposals for the next iteration. Nothing here has been actioned beyond what this desk already publishes,
and every proposal names the problem it solves and the evidence it rests on.</p>
{table(
    ["ID", "Suggestion", "Problem it solves", "Expected impact", "Effort", "Confidence", "State", "Source"],
    rows,
    f"{len(ss)} suggestions",
)}
"""
    return page("suggestions.html", "Suggestions", body)


def page_sources() -> str:
    prov = read("provenance.csv")
    coverage = read("depth_coverage.csv")
    rows = []
    for c in coverage:
        rows.append([
            esc(c["club"]),
            link(c["depth_url"], "official club depth chart"),
            esc(c["captured_utc"]),
            esc(c["raw_file"]),
            esc(c["raw_file_sha256"]),
        ])
    prows = []
    for p in prov:
        prows.append([
            esc(p["file"]),
            esc(p["sha256"]),
            esc(p["bytes"]),
            link(p["source_url"], "source"),
            esc(p["captured_utc"]),
            esc(p["method"]),
            esc(p["note"]),
        ])
    body = f"""
<h2>Sources</h2>
<h3>Official club depth charts &mdash; 32 clubs</h3>
{table(
    ["Club", "Official source", "Captured (UTC)", "Committed raw file", "sha256 of the raw file"],
    rows,
    "Every club's own depth page",
)}
<h3>Provenance of the derived captures</h3>
{table(
    ["File", "sha256", "Bytes", "Source", "Captured (UTC)", "Method", "Note"],
    prows,
    "Hashes over the stored extracts",
)}
<p class="note">The hashes cover the stored extract of each official page, not the server's response bytes, because the
pages are rendered and the raw response body is not obtainable here. That limitation is published as a flag rather than
glossed over.</p>
"""
    return page("sources.html", "Sources", body)


def page_executive_summary() -> str:
    fixtures = read("gamecentre_captures_2026-11-18.csv")
    coverage = read("depth_coverage.csv")
    graph = read("availability_graph.csv")
    reps = read("replacements.csv")
    designated = read("injury_designations_2026-11-18.csv")
    delta = read("injury_delta.csv")
    flags = read("flags.csv")
    blocking = [f for f in flags if f["severity"] == "BLOCKING"]

    body = f"""
<h2>Executive summary</h2>

<h3>What was delivered</h3>
<p>An official-source availability ledger for the 2026 Week 10 slate, published with every value linked to the page it was
read from, and every unverifiable value left blank and flagged rather than filled.</p>
<ul>
<li><strong>Results and venues for all 14 fixtures</strong> from the official game centres, including the official
<code>Location</code> and <code>Stadium</code> fields and the official Game Book link for each game.</li>
<li><strong>Official depth coverage for all 32 clubs</strong> &mdash; every club's own depth page read in one namespace,
{sum(1 for c in coverage if c['page_shape'] != 'image_only')} of them parsing into rows. The Texans publish an image and
are deliberately not transcribed by eye.</li>
<li><strong>An availability graph of {len(graph)} groups</strong> joining the official charts, the official injury report
and the league's official announcements, with the expected starter stated and the actual starter left blank.</li>
<li><strong>{len(reps)} replacement rows</strong> for every <em>Out</em> designation that appears in a chart, each naming
the next available name in the same official group and its depth string.</li>
<li><strong>An injury capture of {len(read('injury_report_all_2026-11-18.csv'))} official rows</strong> with
{len(designated)} designations, plus the {len(delta)}-field delta against the committed 2026-11-15 read and an explicit
audit of the {len(read('injury_delta_normalised.csv'))} rows that the comparison normalises away.</li>
<li><strong>The official inactive list for all 14 fixtures</strong> ({len(read('inactives_week10.csv'))} players). A player
on it did not play, so every chart name on it is excluded from the expected-starter calculation.</li>
<li><strong>{len(read('availability_events.csv'))} official availability events</strong> with a publication date, an official
source URL and an evidence note on every row.</li>
<li><strong>The official Week 11 slate</strong> &mdash; {len(read('week11_slate_official.csv'))} fixtures with the game
centre's own location and stadium fields, and {len(read('week11_byes_official.csv'))} official byes.</li>
<li><strong>{len(flags)} flags</strong>, of which {len(blocking)} are blocking.</li>
</ul>

<h3>The two decisions that mattered</h3>
<ol>
<li><strong>Depth is a group, never a single starter.</strong> Several clubs print shared slots (more than one name in
the same slot) and several print empty slots. Both are preserved exactly as printed. Presenting a shared slot as one
starter would fabricate a starter the club never named.</li>
<li><strong>An unconfirmable value stays blank.</strong> Two official game centres hide their scores and the official
Game Books could not be opened. The scores were taken from the official by-week schedule page instead, and every
actual-starter cell is blank with the reason and the PDF link. No cell anywhere on this site was filled by inference.</li>
<li><strong>A diff that normalises is not a complete diff.</strong> Comparing two dated reads of the official injury page
requires two normalisations: an empty cell and the literal token <em>BLANK</em> mean the same thing, and the comma
separating two injury names is canonicalised. Both are published row by row in the normalisation audit, so a reader can
see exactly which rows the six-row delta is silent about and why.</li>
</ol>

<h3>What is still blocked</h3>
{table(
    ["Flag", "Area", "What is blocked", "What would clear it", "Evidence"],
    [[esc(f["flag_id"]), esc(f["area"]), esc(f["what"]), esc(f["what_would_clear_it"]), link(f["source_url"], "official source")] for f in blocking],
    "Blocking flags",
)}

<h3>How the desk should be used</h3>
<p>Read it as a dated snapshot, not as a live board: the capture stamp is {esc(CAPTURE_STAMP)} and the injury report on it
is the Week 10 report. The delta table is the part that carries information &mdash; what changed between two dated reads
of the same official page &mdash; because the absolute designation level is already public. Nothing here is a model
output, a price or a backtest number, and nothing on this site has been used to select a bet.</p>
"""
    return page("executive-summary.html", "Executive summary", body)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "style.css").write_text(STYLE)
    written = []
    for filename, title in PAGES:
        if filename == "index.html":
            content = page_index()
        elif filename == "results.html":
            content = page_results()
        elif filename == "venues.html":
            content = page_venues()
        elif filename == "availability.html":
            content = page_availability()
        elif filename == "depth.html":
            content = page_depth()
        elif filename == "replacements.html":
            content = page_replacements()
        elif filename == "gamebooks.html":
            content = page_gamebooks()
        elif filename == "inactives.html":
            content = page_inactives()
        elif filename == "week11.html":
            content = page_week11()
        elif filename == "injuries.html":
            content = page_injuries()
        elif filename == "events.html":
            content = page_events()
        elif filename == "flags.html":
            content = page_flags()
        elif filename == "questions.html":
            content = page_questions()
        elif filename == "suggestions.html":
            content = page_suggestions()
        elif filename == "sources.html":
            content = page_sources()
        else:
            content = page_executive_summary()
        (OUT / filename).write_text(content)
        written.append(filename)
    print(f"wrote {len(written)} pages to {OUT.relative_to(ROOT)}")


STYLE = """/* Official Availability Graph desk - plain static stylesheet. */
:root {
  --ink: #16202c;
  --muted: #5a6b7d;
  --line: #d5dde5;
  --accent: #0b5cad;
  --flagbg: #fff4e5;
  --flagink: #8a4b00;
  --blockbg: #fdecec;
  --blockink: #9b1c1c;
  --okbg: #eaf6ec;
  --okink: #1f6b34;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--ink);
  background: #fff;
}
header, nav, main, footer { max-width: 1500px; margin: 0 auto; padding: 0 20px; }
header { padding-top: 26px; padding-bottom: 8px; border-bottom: 2px solid var(--ink); }
header h1 { margin: 0 0 4px; font-size: 25px; letter-spacing: -0.01em; }
header .sub { margin: 0; color: var(--muted); font-size: 16px; }
header .stamp { margin: 6px 0 0; color: var(--muted); font-size: 13px; }
nav { border-bottom: 1px solid var(--line); padding-top: 10px; padding-bottom: 10px; }
nav ul { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 4px 16px; }
nav a { color: var(--accent); text-decoration: none; font-size: 14px; }
nav a:hover { text-decoration: underline; }
nav li.current a { color: var(--ink); font-weight: 700; border-bottom: 2px solid var(--accent); }
main { padding-top: 18px; padding-bottom: 40px; }
h2 { font-size: 19px; margin: 26px 0 10px; padding-bottom: 5px; border-bottom: 1px solid var(--line); }
h3 { font-size: 16px; margin: 20px 0 8px; }
p { margin: 9px 0; }
p.note { color: var(--muted); font-size: 13px; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 18px; font-size: 13px; }
caption { text-align: left; color: var(--muted); font-size: 13px; padding-bottom: 6px; }
th, td { border: 1px solid var(--line); padding: 6px 8px; text-align: left; vertical-align: top; }
th { background: #f2f5f8; font-weight: 700; }
tbody tr:nth-child(even) { background: #fbfcfd; }
td a { color: var(--accent); word-break: break-all; }
a { color: var(--accent); }
code { background: #f2f5f8; padding: 1px 4px; border-radius: 3px; font-size: 12px; }
.flag { background: var(--flagbg); color: var(--flagink); padding: 1px 6px; border-radius: 3px; font-size: 12px; display: inline-block; }
.blank { color: var(--muted); font-style: italic; }
.sev { padding: 1px 6px; border-radius: 3px; font-size: 12px; font-weight: 700; display: inline-block; }
.sev.blocking { background: var(--blockbg); color: var(--blockink); }
.sev.review { background: var(--flagbg); color: var(--flagink); }
.sev.closed { background: var(--okbg); color: var(--okink); }
ul { padding-left: 22px; }
li { margin: 5px 0; }
footer { border-top: 1px solid var(--line); padding-top: 14px; padding-bottom: 30px; color: var(--muted); font-size: 13px; }
@media (max-width: 900px) { table { font-size: 12px; } th, td { padding: 4px 6px; } }
"""


if __name__ == "__main__":
    build()

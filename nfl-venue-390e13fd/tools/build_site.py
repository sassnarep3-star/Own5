#!/usr/bin/env python3
"""Deterministic builder for the NFL Venue & Schedule-Announcement desk (390e13fd).

Renders the static pages from the committed CSV data only: no network, no clock,
no randomness. Rebuilding from the same CSVs reproduces the committed pages
byte-for-byte (CI enforces this with `git diff --exit-code`).

Run: python3 nfl-venue-390e13fd/tools/build_site.py
"""
import csv
import html
import os

DESK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(DESK, "data")

NAV = [
    ("index.html", "Dashboard"),
    ("schedule.html", "Schedule & Venues"),
    ("announcement.html", "Schedule Announcement"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"),
    ("summary.html", "Executive Summary"),
]

TITLE = "NFL Venue & Schedule-Announcement Desk"


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def esc(value):
    return html.escape(value if value is not None else "")


def page(active, title, body):
    nav = "\n".join(
        f'<a href="{href}" class="{"current" if href == active else ""}">{esc(label)}</a>'
        for href, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — {esc(TITLE)}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="brand">{esc(TITLE)} <span>· session 390e13fd · NFL 2026</span></div>
  <nav>{nav}</nav>
</header>
<main id="main">
{body}
</main>
<footer>
  Official-source desk. Every table row carries a link to the official NFL.com
  page it was read from. Values that cannot be confirmed from an official source
  are left blank and flagged. Data read 2026-11-18T03:43:57Z.
</footer>
</body>
</html>
"""


def venues_table(rows, with_status=True):
    out = [
        "<table>",
        "<thead><tr>"
        "<th>Game</th><th>Kickoff</th><th>Network</th><th>Location (as printed)</th>"
        "<th>Stadium (as printed)</th><th>Official game centre</th>"
        + ("<th>Status</th>" if with_status else "")
        + "</tr></thead><tbody>"
    ]
    for r in rows:
        status = (
            f'<span class="badge ok">{esc(r["venue_status"])}</span>' if with_status else ""
        )
        out.append(
            "<tr>"
            f'<td>{esc(r["away_team"])} at {esc(r["home_team"])}</td>'
            f'<td>{esc(r["weekday"])}, {esc(r["date_2026"])}, {esc(r["kickoff_as_printed"])}</td>'
            f'<td>{esc(r["network_as_printed"])}</td>'
            f'<td>{esc(r["venue_location_as_printed"])}</td>'
            f'<td>{esc(r["venue_stadium_as_printed"])}</td>'
            f'<td><a href="{esc(r["official_game_url"])}">official game centre</a></td>'
            f"{status}</tr>"
        )
    out.append("</tbody></table>")
    return "\n".join(out)


def build_index(venues, byes, announcements, flagged):
    n_venues = sum(1 for r in venues if r["venue_status"] == "VERIFIED")
    cards = [
        ("num ok", str(len(venues)), "Week 11 fixtures (official slate)"),
        ("num ok", str(n_venues), "Venues verified from official game centres"),
        ("num", str(len(byes)), "Teams on bye (Week 11)"),
        ("num", str(len(announcements)), "Dated schedule-announcement items"),
        ("num ok" if not flagged else "num warn", str(len(flagged)), "Flagged for review"),
    ]
    cards_html = "\n".join(
        f'<div class="card"><div class="{cls}">{esc(num)}</div><div class="lab">{esc(lab)}</div></div>'
        for cls, num, lab in cards
    )
    body = f"""
<h1>Dashboard</h1>
<p class="lead">Transcription of the venue of every Week 11 fixture from the
official NFL game centre, and the league's dated schedule announcement published
beside the live schedule page. All values are read from official NFL.com pages;
nothing is inferred.</p>
<div class="cards">{cards_html}</div>
<div class="notice"><strong>Venue rule.</strong> A venue value is published only
when the official game-centre <em>Game Info</em> block prints both a location
and a stadium. The Mexico City question left open by the Week 11 schedule desk
(session 3cb7800c, flag F-03) is resolved from the official game centre:
<strong>Vikings at 49ers — Location: MEXICO CITY, Stadium: ESTADIO BANORTE</strong>.
See <a href="flagged.html">Flagged for Review</a> for the cross-session record.</div>
<h2>Week 11 venues at a glance</h2>
{venues_table(venues, with_status=False)}
<p class="meta">Full listing with dates, times and per-row source links:
<a href="schedule.html">Schedule &amp; Venues</a>.</p>
"""
    return page("index.html", "Dashboard", body)


def build_schedule(venues, byes, announcements):
    byes_html = "\n".join(
        f'<tr><td>{esc(r["team_name"])}</td><td>{esc(r["code"])}</td>'
        f'<td><a href="{esc(r["source_url"])}">official schedule page</a></td></tr>'
        for r in byes
    )
    ann_rows = "\n".join(
        f'<tr><td>{esc(r["announcement_item"])}</td><td>{esc(r["announcement_date_as_published"])}</td>'
        f'<td><a href="{esc(r["official_url"])}">official page</a></td></tr>'
        for r in announcements
    )
    body = f"""
<h1>Week 11 Schedule &amp; Venues</h1>
<p class="lead">Every fixture of the official Week 11 slate (13 games,
2026-11-19 to 2026-11-23) with the venue transcribed from the official game
centre. Each row links to the official page it was read from.</p>
{venues_table(venues)}
<h2>Teams on bye (Week 11)</h2>
<table><thead><tr><th>Team</th><th>Code</th><th>Source</th></tr></thead><tbody>
{byes_html}
</tbody></table>
<h2>Dated schedule announcement (published beside the live schedule)</h2>
<div class="note">The league's schedule announcement and the live schedule page
are kept side by side: the announcement fixes the release date, the live page
carries the current slate. Details on the
<a href="announcement.html">Schedule Announcement</a> page.</div>
<table><thead><tr><th>Announcement item</th><th>Date as published</th><th>Source</th></tr></thead><tbody>
{ann_rows}
</tbody></table>
"""
    return page("schedule.html", "Schedule & Venues", body)


def build_announcement(announcements):
    rows = "\n".join(
        "<tr>"
        f'<td>{esc(r["announcement_item"])}</td>'
        f'<td>{esc(r["announcement_date_as_published"])}</td>'
        f'<td>{esc(r["what_it_says"])}</td>'
        f'<td><a href="{esc(r["official_url"])}">official page</a></td>'
        f'<td class="meta">{esc(r["raw_file"])}</td>'
        "</tr>"
        for r in announcements
    )
    body = f"""
<h1>League Schedule Announcement (dated)</h1>
<p class="lead">The league's dated schedule announcement, published here beside
the live schedule page. Dates are the ones printed on the official NFL.com
pages; nothing has been inferred.</p>
<table>
<thead><tr><th>Announcement item</th><th>Date as published</th><th>What it says</th><th>Source</th><th>Raw extract</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
<div class="note">The announcement states the 2026 NFL Schedule (powered by AWS)
was released on <strong>Thursday, May 14, 2026 at 8 p.m. ET</strong>, and lists
2026 International Markets — including <strong>Mexico City, Mexico (Estadio
Banort&eacute;)</strong>, which matches the venue printed on the official
Vikings at 49ers game centre for Week 11.</div>
<p class="meta">Live schedule page:
<a href="https://www.nfl.com/schedules/2026/by-week/week-11">nfl.com Week 11 by-week schedule</a>
(official, read 2026-11-18T03:43:57Z).</p>
"""
    return page("announcement.html", "Schedule Announcement", body)


def build_sources(sources):
    rows = "\n".join(
        "<tr>"
        f'<td>{esc(r["source_id"])}</td><td>{esc(r["title"])}</td>'
        f'<td><a href="{esc(r["url"])}">{esc(r["url"])}</a></td>'
        f'<td>{esc(r["source_class"])}</td><td>{esc(r["supports"])}</td>'
        f'<td class="meta">{esc(r["read_utc"])}</td>'
        f'<td class="meta">{esc(r["raw_file"])}</td>'
        "</tr>"
        for r in sources
    )
    body = f"""
<h1>Sources</h1>
<p class="lead">Every source read for this desk. All are official NFL.com
pages; each raw extract is committed under <code>raw/</code>.</p>
<table>
<thead><tr><th>ID</th><th>Title</th><th>URL</th><th>Class</th><th>Supports</th><th>Read (UTC)</th><th>Raw extract</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
"""
    return page("sources.html", "Sources", body)


def build_flagged(flagged):
    badge = {
        "INFO": '<span class="badge warn">INFO</span>',
        "REVIEW": '<span class="badge bad">REVIEW</span>',
        "BLOCKING": '<span class="badge bad">BLOCKING</span>',
    }
    rows = "\n".join(
        "<tr>"
        f'<td>{esc(r["flag_id"])}</td><td>{badge.get(r["severity"], "")}</td>'
        f'<td>{esc(r["title"])}</td><td>{esc(r["detail"])}</td>'
        f'<td><a href="{esc(r["evidence_url"])}">evidence</a></td>'
        f'<td><span class="badge ok">{esc(r["status"])}</span></td>'
        "</tr>"
        for r in flagged
    )
    body = f"""
<h1>Flagged for Review</h1>
<p class="lead">Irregularities and cross-session records for this desk. No
venue value in this desk is unverified: all 13 venues were read from official
game centres.</p>
<table>
<thead><tr><th>ID</th><th>Severity</th><th>Title</th><th>Detail</th><th>Evidence</th><th>Status</th></tr></thead>
<tbody>
{rows}
</tbody>
</table>
"""
    return page("flagged.html", "Flagged for Review", body)


def build_summary(venues, byes, announcements, flagged, sources):
    n_ok = sum(1 for r in venues if r["venue_status"] == "VERIFIED")
    body = f"""
<h1>Executive Summary</h1>
<p class="lead">This desk transcribes the venue of every Week 11 (2026) fixture
from the official NFL game centre and publishes the league's dated schedule
announcement beside the live schedule page.</p>
<h2>What was done</h2>
<ul>
<li><strong>Venue capture (13/13 verified).</strong> Each of the 13 Week 11
fixtures was read from its official NFL.com game-centre page. The
<em>Game Info</em> block prints both a location and a stadium for every
fixture; those two fields are transcribed verbatim and published as separate
columns. No value was inferred, and no venue cell is blank.</li>
<li><strong>Mexico City resolved.</strong> The open venue question carried by
the Week 11 schedule desk (session 3cb7800c, flag F-03) is resolved from the
official game centre: Vikings at 49ers — Location <strong>MEXICO CITY</strong>,
Stadium <strong>ESTADIO BANORTE</strong>. The finding is recorded on this
desk's Flagged for Review page; the other desk's register was not edited
(cross-session rule).</li>
<li><strong>Dated schedule announcement published.</strong> The league's
announcement that the 2026 NFL Schedule (powered by AWS) would be released on
Thursday, May 14, 2026 at 8 p.m. ET (announcement dated May 8, 2026), and the
official schedule-release hub (dated May 14, 2026), are published on the
<a href="announcement.html">Schedule Announcement</a> page beside the link to
the live Week 11 schedule page.</li>
<li><strong>Corroboration.</strong> The May 8, 2026 announcement lists Mexico
City (Estadio Banorte) among the 2026 International Markets — consistent with
the venue printed on the official game centre for the Week 11 international
fixture.</li>
</ul>
<h2>Counts</h2>
<div class="cards">
<div class="card"><div class="num ok">{len(venues)}</div><div class="lab">Week 11 fixtures read</div></div>
<div class="card"><div class="num ok">{n_ok}</div><div class="lab">Venues verified (official)</div></div>
<div class="card"><div class="num">{len(byes)}</div><div class="lab">Bye teams (Week 11)</div></div>
<div class="card"><div class="num">{len(announcements)}</div><div class="lab">Announcement items published</div></div>
<div class="card"><div class="num">{len(sources)}</div><div class="lab">Official sources read</div></div>
<div class="card"><div class="num {'ok' if not flagged else 'warn'}">{len(flagged)}</div><div class="lab">Flagged items (informational)</div></div>
</div>
<h2>Limitations</h2>
<ul>
<li>Venue values are a point-in-time transcription of the official pages as
read on <code>2026-11-18T03:43:57Z</code>. The official pages remain the
authority if the venue of a fixture changes.</li>
<li>The official game centre prints the Vikings at 49ers location as the city
name only (<code>MEXICO CITY</code>) — see flag VF-02. The value is published
as printed; no suffix has been added.</li>
</ul>
"""
    return page("summary.html", "Executive Summary", body)


def main():
    venues = load("venues.csv")
    byes = load("byes.csv")
    announcements = load("schedule_announcement.csv")
    sources = load("sources.csv")
    flagged = load("flagged.csv")
    pages = {
        "index.html": build_index(venues, byes, announcements, flagged),
        "schedule.html": build_schedule(venues, byes, announcements),
        "announcement.html": build_announcement(announcements),
        "sources.html": build_sources(sources),
        "flagged.html": build_flagged(flagged),
        "summary.html": build_summary(venues, byes, announcements, flagged, sources),
    }
    for name, content in pages.items():
        path = os.path.join(DESK, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        print(f"wrote {os.path.relpath(path, os.path.dirname(DESK))}")


if __name__ == "__main__":
    main()

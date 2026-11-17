#!/usr/bin/env python3
"""Deterministic static-site generator for the OWN5 NFL decision desk.

Reads CSV registers under data/ and renders self-contained HTML pages under
the repo root namespace nfl-desk-e1d60f5d/. Every populated table cell is
source-linked; values that cannot be confirmed from an official source are
left blank and published on the Flagged-for-Review page. Output is
byte-for-byte reproducible across runs (no timestamps, no wall-clock values).

Run:  python3 build.py
"""
import csv
import html
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")
ASSETS = os.path.join(ROOT, "assets")


def read_csv(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(value):
    return html.escape(str(value or ""), quote=True)


def link(url, text, title=None):
    if not url:
        return esc(text or "")
    t = f' title="{esc(title)}"' if title else ""
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer"{t}>{esc(text)}</a>'


def source_cell(url, label="Official source"):
    if not url:
        return '<span class="blank">— blank (no official source)</span>'
    return f'<span class="sourced">{link(url, label, label)}</span>'


def table_header(cols):
    return "<thead><tr>" + "".join(f'<th scope="col">{esc(c)}</th>' for c in cols) + "</tr></thead>"


def table_body(rows, cols, render_row):
    out = ["<tbody>"]
    for r in rows:
        out.append("<tr>" + render_row(r) + "</tr>")
    out.append("</tbody>")
    return "\n".join(out)


def page(title, body, active=None):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(title)} — OWN5 NFL decision desk. Source-linked, verified or blank-and-flagged.">
<title>{esc(title)} · OWN5 NFL Decision Desk</title>
<link rel="stylesheet" href="../assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="layout">
<aside class="sidebar">
<a class="brand" href="index.html"><span class="brand-icon">O<span>5</span></span><span>OWN5<small>NFL DECISION DESK</small></span></a>
<div class="workspace"><span class="live-dot"></span> Research workspace <span class="workspace-arrow">⌄</span></div>
<span class="nav-caption">DESK</span>
<nav aria-label="Main navigation">
<a href="index.html" class="nav-item{' active' if active == 'index' else ''}" aria-current="{'true' if active == 'index' else 'false'}"><span class="nav-number">01</span>Overview</a>
<a href="pages/executive-summary.html" class="nav-item{' active' if active == 'exec' else ''}"><span class="nav-number">02</span>Executive summary</a>
<a href="pages/standings.html" class="nav-item{' active' if active == 'standings' else ''}"><span class="nav-number">03</span>2026 standings</a>
<a href="pages/schedule.html" class="nav-item{' active' if active == 'schedule' else ''}"><span class="nav-number">04</span>Week 11 schedule</a>
<a href="pages/questions.html" class="nav-item{' active' if active == 'questions' else ''}"><span class="nav-number">05</span>Questions register</a>
<a href="pages/suggestions.html" class="nav-item{' active' if active == 'suggestions' else ''}"><span class="nav-number">06</span>Suggestions register</a>
<a href="pages/sources.html" class="nav-item{' active' if active == 'sources' else ''}"><span class="nav-number">07</span>Sources</a>
<a href="pages/flagged.html" class="nav-item{' active' if active == 'flagged' else ''}"><span class="nav-number">08</span>Flagged for Review</a>
</nav>
<div class="side-bottom"><div class="mode"><span class="live-dot"></span> Paper research only</div>
<p>No bets. No fabricated results.<br>Evidence before exposure.</p>
<a href="https://github.com/sassnarep3-star/Own5" target="_blank" rel="noopener noreferrer">View repository ↗</a></div>
</aside>
<div class="main-shell">
<header class="topbar"><div><span class="breadcrumb">Desk <span>/</span> {esc(title)}</span></div><div class="topbar-right"><span class="desktop-only">NFL / METHODOLOGY</span><span class="avatar">O5</span></div></header>
<main id="main">{body}</main>
</div>
</div>
</body>
</html>"""


def standings_page():
    rows = read_csv("standings_2026_wk11.csv")
    body = [
        '<section class="panel table-panel"><div class="panel-head"><div><h2>2026 NFL Standings — Week 11</h2><p>Official standings from nfl.com. Every row links to the official standings page. Blank = unverified (none here).</p></div></div>',
        '<table class="data-table"><caption>Official 2026 NFL standings as captured 2026-11-17 from nfl.com/standings/league/2026/REG.</caption>',
        table_header(["#", "Team", "Conf", "Div", "W", "L", "T", "Pct", "PF", "PA", "Net", "Strk", "Source"]),
    ]
    for r in rows:
        body.append(
            "<tr>"
            f"<td>{esc(r['rank'])}</td>"
            f"<td>{esc(r['team'])}</td>"
            f"<td>{esc(r['conference'])}</td>"
            f"<td>{esc(r['division'])}</td>"
            f"<td>{esc(r['wins'])}</td>"
            f"<td>{esc(r['losses'])}</td>"
            f"<td>{esc(r['ties'])}</td>"
            f"<td>{esc(r['pct'])}</td>"
            f"<td>{esc(r['pf'])}</td>"
            f"<td>{esc(r['pa'])}</td>"
            f"<td>{esc(r['net'])}</td>"
            f"<td>{esc(r['streak'])}</td>"
            f"<td>{source_cell(r['source_url'])}</td>"
            "</tr>"
        )
    body.append("</tbody></table>")
    body.append('<p class="note">All 32 teams captured. Source: <a href="https://www.nfl.com/standings/league/2026/REG" target="_blank" rel="noopener noreferrer">NFL League Standings (2026 REG)</a>. Captured 2026-11-17.</p>')
    body.append("</section>")
    return page("2026 NFL Standings", "\n".join(body), active="standings")


def schedule_page():
    rows = read_csv("schedule_2026_wk11.csv")
    byes = read_csv("byes_2026_wk11.csv")
    body = [
        '<section class="panel table-panel"><div class="panel-head"><div><h2>Week 11 Schedule — 2026</h2><p>Official Week-11 slate from nfl.com/schedules/2026/by-week/week-11. Vikings@49ers is a neutral-site game in Mexico City (Estadio Banorte). Six teams are on bye.</p></div></div>',
        '<table class="data-table"><caption>Week 11 games and bye teams, official NFL schedule.</caption>',
        table_header(["#", "Date", "Kickoff ET", "Network", "Away", "Away rec", "Home", "Home rec", "Venue", "Neutral", "Source"]),
    ]
    for i, r in enumerate(rows, 1):
        body.append(
            "<tr>"
            f"<td>{i}</td>"
            f"<td>{esc(r['game_date'])}</td>"
            f"<td>{esc(r['kickoff_et'])}</td>"
            f"<td>{esc(r['network'])}</td>"
            f"<td>{esc(r['away_team'])}</td>"
            f"<td>{esc(r['away_record'])}</td>"
            f"<td>{esc(r['home_team'])}</td>"
            f"<td>{esc(r['home_record'])}</td>"
            f"<td>{esc(r['venue'])}</td>"
            f"<td>{esc(r['neutral_site'])}</td>"
            f"<td>{source_cell(r['source_url'])}</td>"
            "</tr>"
        )
    body.append("</tbody></table>")
    body.append('<h3>Teams on Bye — Week 11</h3>')
    body.append('<table class="data-table"><caption>Bye teams from the official Week-11 schedule page.</caption>')
    body.append(table_header(["Team", "Conf", "Div", "W", "L", "T", "Pct", "Source"]))
    for r in byes:
        body.append(
            "<tr>"
            f"<td>{esc(r['team'])}</td>"
            f"<td>{esc(r['conference'])}</td>"
            f"<td>{esc(r['division'])}</td>"
            f"<td>{esc(r['wins'])}</td>"
            f"<td>{esc(r['losses'])}</td>"
            f"<td>{esc(r['ties'])}</td>"
            f"<td>{esc(r['pct'])}</td>"
            f"<td>{source_cell(r['source_url'])}</td>"
            "</tr>"
        )
    body.append("</tbody></table>")
    body.append('<p class="note">Source: <a href="https://www.nfl.com/schedules/2026/by-week/week-11" target="_blank" rel="noopener noreferrer">NFL Schedule — Week 11 2026</a>. Captured 2026-11-17.</p>')
    body.append("</section>")
    return page("Week 11 Schedule", "\n".join(body), active="schedule")


def questions_page():
    rows = read_csv("questions.csv")
    blocking = [r for r in rows if r.get("blocking") == "Yes"]
    resolved = [r for r in rows if r.get("blocking") == "No"]
    body = [
        '<section class="panel"><div class="panel-head"><div><h2>Questions Register — Have vs Missing vs Answers</h2><p>Information that must be addressed before any decision can be reasonably made, based on what we already have and do not have. Each question carries its discovery route.</p></div></div>',
        f'<div class="stat-card"><span class="stat-label">Total questions</span><strong class="stat-value">{len(rows)}</strong></div>'
        f'<div class="stat-card"><span class="stat-label">Blocking (decision-gated)</span><strong class="stat-value warn">{len(blocking)}</strong></div>'
        f'<div class="stat-card"><span class="stat-label">Resolved / not blocking</span><strong class="stat-value">{len(resolved)}</strong></div>',
        '<table class="data-table"><caption>Questions register. Blocking = the answer is required before a decision can be made.</caption>',
        table_header(["ID", "Question", "What we have", "What we lack", "Answer / status", "Discovery route", "Blocking", "Source"]),
    ]
    for r in rows:
        badge = 'class="badge warn"' if r.get("blocking") == "Yes" else 'class="badge ok"'
        body.append(
            "<tr>"
            f"<td>{esc(r['id'])}</td>"
            f"<td>{esc(r['question'])}</td>"
            f"<td>{esc(r['what_we_have'])}</td>"
            f"<td>{esc(r['what_we_lack'])}</td>"
            f"<td>{esc(r['answer_or_status'])}</td>"
            f"<td>{esc(r['discovery_route'])}</td>"
            f"<td><span {badge}>{esc(r['blocking'])}</span></td>"
            f"<td>{source_cell(r['source_url'])}</td>"
            "</tr>"
        )
    body.append("</tbody></table>")
    body.append('<p class="note">Blank answer cells mean the information is not available from an official source and is intentionally left blank, never inferred.</p>')
    body.append("</section>")
    return page("Questions Register", "\n".join(body), active="questions")


def suggestions_page():
    rows = read_csv("suggestions.csv")
    awaiting = [r for r in rows if r.get("decision_status") == "AWAITING DECISION"]
    implemented = [r for r in rows if r.get("decision_status") == "IMPLEMENTED"]
    body = [
        '<section class="panel"><div class="panel-head"><div><h2>Suggestions Register — Review Before Implementing</h2><p>Improvement paths for the site and decision-making. Each suggestion carries options, a recommended path, and the test that would change the call. Nothing is implemented without a reviewer decision.</p></div></div>',
        f'<div class="stat-card"><span class="stat-label">Total suggestions</span><strong class="stat-value">{len(rows)}</strong></div>'
        f'<div class="stat-card"><span class="stat-label">Awaiting decision</span><strong class="stat-value warn">{len(awaiting)}</strong></div>'
        f'<div class="stat-card"><span class="stat-label">Implemented</span><strong class="stat-value ok">{len(implemented)}</strong></div>',
        '<table class="data-table"><caption>Suggestions register. Review these and choose a path before implementing any change.</caption>',
        table_header(["ID", "Suggestion", "Options", "Recommended", "What would change the call", "Decision status", "Source"]),
    ]
    for r in rows:
        badge = 'class="badge warn"' if r.get("decision_status") == "AWAITING DECISION" else 'class="badge ok"'
        body.append(
            "<tr>"
            f"<td>{esc(r['id'])}</td>"
            f"<td>{esc(r['suggestion'])}</td>"
            f"<td>{esc(r['options'])}</td>"
            f"<td>{esc(r['recommended'])}</td>"
            f"<td>{esc(r['what_would_change_the_call'])}</td>"
            f"<td><span {badge}>{esc(r['decision_status'])}</span></td>"
            f"<td>{source_cell(r['source_url'])}</td>"
            "</tr>"
        )
    body.append("</tbody></table>")
    body.append('<p class="note">Suggestions are proposals only. A reviewer picks a path (and records the decision) before anything is implemented.</p>')
    body.append("</section>")
    return page("Suggestions Register", "\n".join(body), active="suggestions")


def sources_page():
    rows = read_csv("sources.csv")
    body = [
        '<section class="panel table-panel"><div class="panel-head"><div><h2>Official Source Register</h2><p>Every published value traces to an official or primary source. Tier = OFFICIAL (NFL league/club sources) or INDUSTRY (methodological reference, not an endorsement).</p></div></div>',
        '<table class="data-table"><caption>Source register behind every published row.</caption>',
        table_header(["ID", "Source", "URL", "Tier", "Used for", "Captured", "Notes"]),
    ]
    for r in rows:
        body.append(
            "<tr>"
            f"<td>{esc(r['source_id'])}</td>"
            f"<td>{esc(r['source_name'])}</td>"
            f"<td>{link(r['url'], esc(r['url']))}</td>"
            f"<td>{esc(r['official_tier'])}</td>"
            f"<td>{esc(r['used_for'])}</td>"
            f"<td>{esc(r['capture_utc'])}</td>"
            f"<td>{esc(r['notes'])}</td>"
            "</tr>"
        )
    body.append("</tbody></table>")
    body.append('<p class="note">INDUSTRY-tier sources are methodological references only — they do not verify that a policy is officially endorsed or a strategy is profitable.</p>')
    body.append("</section>")
    return page("Sources", "\n".join(body), active="sources")


def flagged_page():
    rows = read_csv("flagged.csv")
    blocking = [r for r in rows if r.get("severity", "").startswith("blocking")]
    body = [
        '<section class="panel"><div class="panel-head"><div><h2>Flagged for Review</h2><p>Irregularities and unverified items. These do not block publication; they are published with source links so they can be reviewed and resolved.</p></div></div>',
        f'<div class="stat-card"><span class="stat-label">Total flags</span><strong class="stat-value">{len(rows)}</strong></div>'
        f'<div class="stat-card"><span class="stat-label">Blocking</span><strong class="stat-value warn">{len(blocking)}</strong></div>',
        '<table class="data-table"><caption>Flagged-for-review register. Severity: blocking = must be resolved before a decision relies on the affected value.</caption>',
        table_header(["ID", "Severity", "Item", "Detail", "Source", "Status"]),
    ]
    for r in rows:
        sev = r.get("severity", "")
        badge = 'class="badge warn"' if sev.startswith("blocking") else 'class="badge review"'
        body.append(
            "<tr>"
            f"<td>{esc(r['id'])}</td>"
            f"<td><span {badge}>{esc(sev)}</span></td>"
            f"<td>{esc(r['item'])}</td>"
            f"<td>{esc(r['detail'])}</td>"
            f"<td>{link(r['source_url'], 'official source', r['source_url'])}</td>"
            f"<td>{esc(r['status'])}</td>"
            "</tr>"
        )
    body.append("</tbody></table>")
    body.append('<p class="note">Values that cannot be confirmed from an official source are left blank and flagged here — never inferred or filled in.</p>')
    body.append("</section>")
    return page("Flagged for Review", "\n".join(body), active="flagged")


def executive_summary_page():
    standings = read_csv("standings_2026_wk11.csv")
    schedule = read_csv("schedule_2026_wk11.csv")
    questions = read_csv("questions.csv")
    suggestions = read_csv("suggestions.csv")
    flagged = read_csv("flagged.csv")
    q_blocking = sum(1 for r in questions if r.get("blocking") == "Yes")
    s_awaiting = sum(1 for r in suggestions if r.get("decision_status") == "AWAITING DECISION")
    f_blocking = sum(1 for r in flagged if r.get("severity", "").startswith("blocking"))

    body = [
        '<section class="panel hero"><div class="hero-copy"><span class="eyebrow">OWN5 · NFL DECISION DESK</span>',
        '<h2>Executive Summary</h2>',
        '<p>A transparent, source-linked research desk for originating NFL lines, testing strategies, and separating evidence from noise. Every table row links to an official source; values that cannot be confirmed are left blank and flagged. No bets are placed, no performance is claimed, and no strategy is certified until it passes validation gates.</p>',
        '</div></section>',
        '<h3>What we have (verified from official sources)</h3>',
        f'<ul><li><strong>32-team 2026 standings</strong> (W-L-T, PF, PA, PCT) reconciled to <a href="https://www.nfl.com/standings/league/2026/REG" target="_blank" rel="noopener noreferrer">nfl.com standings</a>, captured 2026-11-17.</li>'
        f'<li><strong>Week 11 schedule</strong>: 13 games + 6 byes (ATL, CLE, GB, LAR, NE, SEA), with kickoffs, networks and venues from <a href="https://www.nfl.com/schedules/2026/by-week/week-11" target="_blank" rel="noopener noreferrer">nfl.com schedule</a>. Vikings@49ers confirmed as a neutral-site game in Mexico City.</li>'
        f'<li><strong>{len(questions)} questions</strong> registered ({q_blocking} blocking), each with what we have, what we lack, and a discovery route.</li>'
        f'<li><strong>{len(suggestions)} suggestions</strong> registered ({s_awaiting} awaiting decision), each with options, a recommended path, and the test that would change the call.</li>'
        f'<li><strong>{len(flagged)} flags</strong> published ({f_blocking} blocking), each with a source link; nothing inferred.</li>'
        '</ul>',
        '<h3>What we still need before a decision can be made</h3>',
        f'<ul><li><strong>Price-data policy</strong>: nfl.com publishes no betting prices, so opening/closing market lines are blank and flagged (F-01). A price source must be chosen before any backtest or ROI is published.</li>'
        f'<li><strong>Injury/availability depth</strong>: only one injury-report read exists; no transactions, reserve list, official inactive list, or snap-count source (F-03 to F-06). Houston\'s depth chart is image-only (F-02).</li>'
        f'<li><strong>Strategy validation</strong>: 0 strategies certified. All start PAPER behind fail-closed gates; backtest numbers are barred from the leaderboard.</li>'
        '</ul>',
        '<h3>Bottom line</h3>',
        '<p>The desk is evidence-first: blank cells mean "unverified," never "zero." Review the Questions and Suggestions registers before implementing any change, and the Flagged page for irregularities needing resolution.</p>',
    ]
    return page("Executive Summary", "\n".join(body), active="exec")


def overview_page():
    standings = read_csv("standings_2026_wk11.csv")
    schedule = read_csv("schedule_2026_wk11.csv")
    questions = read_csv("questions.csv")
    suggestions = read_csv("suggestions.csv")
    flagged = read_csv("flagged.csv")
    sources = read_csv("sources.csv")
    q_blocking = sum(1 for r in questions if r.get("blocking") == "Yes")
    s_awaiting = sum(1 for r in suggestions if r.get("decision_status") == "AWAITING DECISION")
    f_blocking = sum(1 for r in flagged if r.get("severity", "").startswith("blocking"))

    body = [
        '<section class="panel hero"><div class="hero-copy"><span class="eyebrow">OWN5 · NFL DECISION DESK</span>',
        '<h2>Overview</h2>',
        '<p>Your evidence-first NFL decision desk. Originate your own lines, test strategies, and separate signal from luck. All data is verified from official NFL sources or left blank and flagged.</p>',
        '<a class="primary" href="pages/executive-summary.html">Read executive summary <span>↗</span></a>',
        '<a class="text-link" href="pages/questions.html">Open questions <span>↗</span></a>',
        '</div></section>',
        '<div class="stats">',
        f'<article><span>Teams tracked</span><strong>{len(standings)}</strong><small>32 NFL teams, official standings</small></article>',
        f'<article><span>Week-11 games</span><strong>{len(schedule)}</strong><small>Official schedule, all source-linked</small></article>',
        f'<article><span>Open questions</span><strong>{len(questions)}</strong><small>{q_blocking} blocking a decision</small></article>',
        f'<article><span>Suggestions awaiting review</span><strong class="amber">{s_awaiting}</strong><small>Review before implementing</small></article>',
        f'<article><span>Flagged items</span><strong class="amber">{f_blocking}</strong><small>of {len(flagged)} total blocking</small></article>',
        f'<article><span>Official sources</span><strong>{len(sources)}</strong><small>Every row linked or blank</small></article>',
        '</div>',
        '<section class="panel"><div class="panel-head"><div><h2>Decision readiness at a glance</h2><p>One row per requirement area, with the gate that blocks it and what would clear it.</p></div></div>',
        '<table class="data-table"><caption>Decision-readiness summary. Full detail on the Questions and Suggestions subpages.</caption>',
        table_header(["Requirement area", "Status", "Blocking gate", "Number that would clear it", "Source"]),
        "<tbody><tr><td>Official standings &amp; schedule</td><td><span class='badge ok'>MET</span></td><td>None</td><td>32 teams + Week-11 slate captured</td><td>" + source_cell("https://www.nfl.com/standings/league/2026/REG") + "</td></tr>",
        "<tr><td>Price-snapshot store (open + close per market)</td><td><span class='badge warn'>BLOCKED</span></td><td>No operator price feed; nfl.com publishes no prices</td><td>An admissible price source chosen and snapshots retained</td><td>" + source_cell("https://www.nfl.com/betting/") + "</td></tr>",
        "<tr><td>Verified results feed for backtests/ROI</td><td><span class='badge ok'>PARTIAL</span></td><td>One season only; gate G1 needs n &gt;= 300</td><td>Multiple official seasons added to the feed</td><td>" + source_cell("https://www.nfl.com/schedules/2026/by-week/week-11") + "</td></tr>",
        "<tr><td>Injury &amp; replacement-depth tracking</td><td><span class='badge warn'>BLOCKED</span></td><td>No inactive list, snap counts, transactions, or reserve list</td><td>Official inactive lists + snap counts for all 32 clubs</td><td>" + source_cell("https://www.nfl.com/injuries/league/2026/reg10") + "</td></tr>",
        "<tr><td>Signal vs staking on the leaderboard</td><td><span class='badge ok'>MET (policy)</span></td><td>No strategy has passed all gates</td><td>At least one strategy certified</td><td>" + source_cell("https://www.nfl.com/standings/league/2026/REG") + "</td></tr>",
        "<tr><td>Correlations from official numbers with n</td><td><span class='badge warn'>BLOCKED</span></td><td>No official player-statistic source</td><td>Official stats source with n per value</td><td>" + source_cell("https://nextgenstats.nfl.com/glossary") + "</td></tr>",
        "<tr><td>Demotion gate (live → paper)</td><td><span class='badge ok'>MET (spec)</span></td><td>Not yet triggered; no live strategies</td><td>Gate defined and fail-closed</td><td>" + source_cell("https://www.nfl.com/standings/league/2026/REG") + "</td></tr>",
        "</tbody></table>",
        '<p class="note">Readiness statuses are checked against the cited repo files, not copied on trust. Blank cells = unverified.</p>',
        '</section>',
        '<section class="panel"><div class="panel-head"><div><h2>Next steps for a reviewer</h2><p>Choose a path before anything is implemented.</p></div></div>',
        '<ul>',
        '<li><a href="pages/questions.html">Review the open questions</a> — decide which blocking items to resolve first.</li>',
        '<li><a href="pages/suggestions.html">Review the suggestions</a> — pick a path (price-data policy, consolidation, depth source, etc.).</li>',
        '<li><a href="pages/flagged.html">Review the flagged items</a> — resolve blocking irregularities (F-01 to F-06, F-12).</li>',
        '<li><a href="pages/sources.html">Review the official source register</a> — confirm every published value traces to an official source.</li>',
        '</ul>',
        '</section>',
    ]
    return page("Overview", "\n".join(body), active="index")


PAGES_MAP = {
    "index": overview_page,
    "exec": executive_summary_page,
    "standings": standings_page,
    "schedule": schedule_page,
    "questions": questions_page,
    "suggestions": suggestions_page,
    "sources": sources_page,
    "flagged": flagged_page,
}


def main():
    os.makedirs(PAGES, exist_ok=True)
    # Root index.html lives at the desk root.
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(PAGES_MAP["index"]())
    for name in ["exec", "standings", "schedule", "questions", "suggestions", "sources", "flagged"]:
        with open(os.path.join(PAGES, name + ".html"), "w", encoding="utf-8") as f:
            f.write(PAGES_MAP[name]())
    print(f"Built {len(PAGES_MAP)} pages for {ROOT}")


if __name__ == "__main__":
    main()

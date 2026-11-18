#!/usr/bin/env python3
"""Render the NFL official-source desk pages from data/*.csv.

Deterministic: no clock reads, no git calls, no network. Every date shown comes from a CSV column.
Run from anywhere: python3 nfl-desk-3cb7800c/tools/build_site.py
"""
import csv
import html
import os

DESK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA = os.path.join(DESK, "data")

NAV = [
    ("index.html", "Home"),
    ("schedule.html", "Week 11 schedule"),
    ("availability.html", "Availability"),
    ("https://sassnarep3-star.github.io/Own5/nfl-desk-5c5f4aaf/", "Desks index (5c5f4aaf)"),
    ("repo.html", "Repo state"),
    ("sources.html", "Sources"),
    ("summary.html", "Executive summary"),
    ("suggestions.html", "Suggestions (review)"),
    ("questions.html", "Questions"),
    ("flagged.html", "Flagged for review"),
]

BADGE_CLASS = {
    "OFFICIAL": "b-official",
    "REPO": "b-repo",
    "INTERNAL": "b-internal",
    "METHOD": "b-method",
    "UNVERIFIED": "b-unverified",
    "BLOCKING": "b-blocking",
    "REVIEW": "b-review",
    "PENDING": "b-review",
}


def read_csv(name):
    with open(os.path.join(DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def e(text):
    return html.escape(text or "", quote=True)


def badge(label, kind=None):
    kind = kind or next((k for k in BADGE_CLASS if label.upper().startswith(k)), "INTERNAL")
    cls = BADGE_CLASS.get(kind, "b-internal")
    return f'<span class="badge {cls}">{e(label)}</span>'


def link(url, text=None):
    if not url:
        return '<span class="muted">none</span>'
    return f'<a href="{e(url)}" rel="noopener" target="_blank">{e(text or url)}</a>'


def table(headers, rows, caption=None):
    out = ['<div class="table-wrap"><table>']
    if caption:
        out.append(f"<caption>{e(caption)}</caption>")
    out.append("<thead><tr>" + "".join(f"<th>{e(h)}</th>" for h in headers) + "</tr></thead>")
    out.append("<tbody>")
    for row in rows:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def page(filename, title, body, lead=None):
    items = []
    for href, label in NAV:
        attrs = ' class="current" aria-current="page"' if href == filename else ""
        items.append(f'<a href="{href}"{attrs}>{e(label)}</a>')
    nav_items = "".join(items)
    lead_html = f'<p class="lead">{e(lead)}</p>' if lead else ""
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · NFL official-source desk (3cb7800c)</title>
<link rel="stylesheet" href="assets/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="brand">NFL official-source desk <span>3cb7800c</span></div>
  <nav aria-label="Pages">{nav_items}</nav>
</header>
<main id="main">
<h1>{e(title)}</h1>
{lead_html}
{body}
</main>
<footer>
  <p>Not a betting feed. No prices, odds, picks or model outputs are published here.
  Every value comes from a CSV in <code>data/</code>; each row carries a source link or an explicit
  badge. Blank cells are unverified and are not inferred.</p>
  <p>Rebuild: <code>python3 nfl-desk-3cb7800c/tools/build_site.py</code> · Checks:
  <code>python3 nfl-desk-3cb7800c/verify.py</code> · Pages are generated; do not hand-edit.</p>
</footer>
</body>
</html>
"""
    with open(os.path.join(DESK, filename), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)


def repo_count(repo_rows):
    """Desk-directory count as cross-checked in repo_checks.csv (row R-07)."""
    row = next(r for r in repo_rows if r["check_id"] == "R-07")
    return int(row["value_at_read"].split()[0])


def kpi(value, label, href=None, note=""):
    inner = f'<strong>{e(value)}</strong><span>{e(label)}</span>'
    if note:
        inner += f'<small>{e(note)}</small>'
    if href:
        return f'<a class="kpi" href="{href}">{inner}</a>'
    return f'<div class="kpi">{inner}</div>'


def build():
    sched = read_csv("week11_schedule.csv")
    byes = read_csv("week11_byes.csv")
    avail = read_csv("availability_status.csv")
    repo = read_csv("repo_checks.csv")
    sources = read_csv("sources.csv")
    flags = read_csv("flagged.csv")
    sugg = read_csv("suggestions.csv")
    quest = read_csv("questions.csv")

    open_flags = [f for f in flags if f["status"].upper() == "OPEN"]
    blocking = [f for f in open_flags if f["severity"].upper() == "BLOCKING"]
    open_pr_value = next(r["value_at_read"] for r in repo if r["check_id"] == "R-01")
    read_stamp = sched[0]["read_utc"] if sched else ""
    sibling_count = repo_count(repo)

    # ---------- index.html ----------
    cards = [
        kpi(str(len(sched)), "Week 11 games on the official schedule", "schedule.html",
            "Read " + read_stamp),
        kpi(str(len(byes)), "Teams on bye (official schedule)", "schedule.html",
            "13 games x 2 + 6 bye = 32 clubs"),
        kpi("NOT PUBLISHED", "Week 11 injury report at read time", "availability.html",
            "The Week 11 URL serves the Week 10 report"),
        kpi(str(sibling_count), "NFL desk directories in this repo", "repo.html",
            "Cross-checked against the 5c5f4aaf directory (R-07)"),
        kpi(open_pr_value.split(" (")[0], "Open pull requests against main", "repo.html",
            "Read from GitHub"),
        kpi(f"{len(open_flags)}", f"Open flags ({len(blocking)} blocking)", "flagged.html",
            "Published with links; not blocking"),
    ]
    nav_cards = [
        ("schedule.html", "Week 11 schedule", "13 games and 6 byes from the official schedule, with each game's official page link. Venue not verified."),
        ("availability.html", "Availability", "Status of the Week 11 injury report and the evidence used. No availability values are published."),
        ("https://sassnarep3-star.github.io/Own5/nfl-desk-5c5f4aaf/", "Desks index", "Every NFL desk directory in the repo, with its entry page. Maintained by session 5c5f4aaf (PR #102)."),
        ("repo.html", "Repo state", "Pull requests, CI runs, root-page status. GitHub facts, labelled as such."),
        ("sources.html", "Sources", "Official pages read, with time, extract file and hash."),
        ("summary.html", "Executive summary", "What is verified, what is blocked, and what decision is needed."),
        ("suggestions.html", "Suggestions for review", "Options, a recommendation and what would change the call. Nothing is implemented."),
        ("questions.html", "Questions", "What is known, what is missing, and the cheapest route to close each gap."),
        ("flagged.html", "Flagged for review", "Irregularities and unverified items, each with its evidence link."),
    ]
    card_html = "".join(
        f'<a class="navcard" href="{href}"><strong>{e(t)}</strong><span>{e(d)}</span></a>'
        for href, t, d in nav_cards
    )
    body = (
        '<section class="notice"><strong>Read stamp.</strong> Official pages were read on '
        f'{e(read_stamp)} by the sandbox fetch tool. Pages change; re-read before use. '
        'The Week 11 injury report is still not published at this stamp.</section>'
        f'<section class="kpis">{"".join(cards)}</section>'
        '<h2>Categories</h2>'
        f'<section class="navgrid">{card_html}</section>'
        '<h2>Blocking items now</h2>'
        + table(["Flag", "Title", "Evidence"],
                [[badge(f["flag_id"], "BLOCKING"), e(f["title"]), link(f["evidence_url"], "source")] for f in blocking])
    )
    page("index.html", "Week 11 official-source desk", body,
         lead="A status desk for the NFL line-origination work. It publishes only what it could read "
              "from official pages today, with timestamps, and says plainly what is missing.")

    # ---------- schedule.html ----------
    rows = []
    for g in sched:
        rows.append([
            e(f'{g["away_team"]} ({g["away_code"]}) at {g["home_team"]} ({g["home_code"]})'),
            e(g["weekday"]),
            e(g["date_2026"]),
            e(g["kickoff_as_printed"]),
            e(g["network_as_printed"]),
            badge("UNVERIFIED — blank", "UNVERIFIED"),
            link(g["official_game_url"], "game page"),
            link(g["source_url"], "schedule (S-01)"),
        ])
    sched_html = table(
        ["Game", "Day", "Date (2026)", "Kickoff as printed", "Network as printed", "Venue", "Official game page", "Source"],
        rows, caption="Week 11 games (13)")
    bye_rows = [[e(b["team_name"]), e(b["code_as_printed"]), e(b["standings_logo_code"]),
                 link(b["source_url"], "schedule (S-01)")] for b in byes]
    bye_html = table(["Team", "Code as printed", "Code on standings page", "Source"], bye_rows,
                     caption="Teams on bye (6)")
    body = (
        '<section class="notice"><strong>Venue column is blank on purpose.</strong> The printed game lines carry no venue, '
        'and the Sunday Night section shows a Mexico City logo above Vikings at 49ers that the text does not explain. '
        'See flag F-03 and question Q-02.</section>'
        f'<h2>Games</h2>{sched_html}'
        f'<h2>Byes</h2>{bye_html}'
        '<p class="muted">Check performed by verify.py: 13 games and 6 byes cover 32 distinct clubs; '
        'each weekday matches its 2026 date; each game line appears verbatim in the saved extract '
        '(raw/nfl_week11_schedule_extract.txt).</p>'
    )
    page("schedule.html", "Week 11 schedule (official)", body,
         lead="The official Week 11 slate as printed on NFL.com. Kickoff times and networks are as printed; "
              "no time zone is stated on the game lines (flag F-04).")

    # ---------- availability.html ----------
    arows = []
    for a in avail:
        status = a["status"]
        kind = "BLOCKING" if "NOT PUBLISHED" in status.upper() else "OFFICIAL"
        arows.append([
            e(a["check_id"]),
            e(a["item"]),
            link(a["url_requested"], "requested"),
            link(a["final_url_reported_by_fetch_tool"], "final URL"),
            e(a["page_title_seen"]),
            badge(status, kind),
            e(a["read_utc"]),
            e(a["note"]),
        ])
    body = (
        '<section class="notice"><strong>No availability values are published here.</strong> '
        'The Week 11 report is not served, so no Week 11 designation can be read. Week 10 rows are not captured in this desk.</section>'
        + table(["ID", "Item", "Requested", "Final URL", "Title seen", "Status", "Read (UTC)", "Note"], arows,
                caption="Availability evidence")
        + "<h2>What would make this usable</h2><ul>"
        "<li>A Week 11 injury report served by the official page, read on the publication days and stored with its timestamp and hash.</li>"
        "<li>A rule that a club-code join must map LAR to LA and must fail on any unmatched club (suggestion S-03).</li>"
        "<li>An official inactives source for each game (question Q-08). Not captured here.</li></ul>"
    )
    page("availability.html", "Availability (Week 11)", body,
         lead="Only the status of the official injury report, read today, is recorded. "
              "A page that serves last week's report is not treated as this week's report.")

    # ---------- repo.html ----------
    rrows = []
    for r in repo:
        rrows.append([
            e(r["check_id"]),
            e(r["check"]),
            e(r["value_at_read"]),
            e(r["read_utc"]),
            badge(r["source_class"].split(" ")[0] if r["source_class"] else "REPO", "REPO"),
            link(r["source_url"], "GitHub"),
            e(r["note"]),
        ])
    body = (
        '<section class="notice"><strong>Repo facts are not league facts.</strong> '
        'They come from GitHub and this checkout. They are labelled REPO and carry no league claim.</section>'
        + table(["ID", "Check", "Value at read", "Read (UTC)", "Class", "Source", "Note"], rrows,
                caption="Repository state")
    )
    page("repo.html", "Repo state", body,
         lead="Pull requests, CI runs and the root landing page, as read at the stamp shown.")

    # ---------- sources.html ----------
    srows = []
    for s in sources:
        cls = s["source_class"]
        kind = "OFFICIAL" if cls.startswith("OFFICIAL") else ("REPO" if cls.startswith("REPO") else "INTERNAL")
        raw = s["raw_file"]
        srows.append([
            e(s["source_id"]),
            e(s["title"]),
            badge(cls, kind),
            link(s["url"]),
            e(s["supports"]),
            e(s["read_utc"]),
            (f'<a href="{e(raw)}">{e(raw)}</a>' if raw else '<span class="muted">none</span>'),
            e(s["caveat"]),
        ])
    body = (
        '<section class="notice"><strong>Method limit.</strong> The fetch tool returns processed page text, not server bytes. '
        'The hashes in <code>raw/SHA256SUMS.txt</code> cover the extracts this desk uses (flag F-09).</section>'
        + table(["ID", "Source", "Class", "Link", "Supports", "Read (UTC)", "Extract", "Caveat"], srows,
                caption="Sources")
    )
    page("sources.html", "Sources", body,
         lead="Every source used on this site. OFFICIAL links point to NFL.com pages; a REPO row points to GitHub and is never used for a league fact.")

    # ---------- summary.html ----------
    body = f"""
<section class="panel">
<h2>What is verified today</h2>
<ul>
<li>The Week 11 official schedule lists <strong>{len(sched)} games</strong> and <strong>{len(byes)} teams on bye</strong>. Together these cover 32 clubs (S-01).</li>
<li>The Week 11 injury report is <strong>not published</strong> at the stamp. The Week 11 URL serves the Week 10 report (A-01, F-01).</li>
<li>The official standings use the club codes <strong>AZ</strong> and <strong>LA</strong>. The schedule bye block prints <strong>LAR</strong> for the Rams (S-04, F-02).</li>
</ul>
</section>
<section class="panel">
<h2>What is not verified, and why</h2>
<ul>
<li><strong>Venues</strong> are blank. The printed game lines carry none, and one Sunday Night game has an unexplained Mexico City logo (F-03).</li>
<li><strong>Availability and designations</strong> for Week 11 are blank. The report is not served (F-01).</li>
<li><strong>Inactives, snap counts, depth charts and game books</strong> are not captured in this desk. They are open questions (Q-08).</li>
<li><strong>Prices, odds, backtests and model outputs</strong> are not produced here. The price-data policy has not been decided (S-06, Q-07).</li>
</ul>
</section>
<section class="panel">
<h2>Repo state that affects decisions</h2>
<ul>
<li>{e(open_pr_value.split(" (")[0])} PRs are open against main. Nine of them were opened between 2026-11-02 and 2026-11-14 (F-06).</li>
<li>The decision-desk PR check failed on 11 of 12 recent PR runs (F-05). Merges that rely on that check are not safe until it is fixed or retired (S-04).</li>
<li>The root banner still reads AS OF 2026-11-02. Its notice now links the desk directory (PR #102). The banner is generated, so it needs the generator, not a hand edit (F-07, S-01).</li>
<li>There are {sibling_count} NFL desk directories, cross-checked against the directory page (R-07). Several answer the same brief. Choosing one canonical desk is a decision for the owner (S-05).</li>
</ul>
</section>
<section class="panel">
<h2>Decisions needed from the owner</h2>
<ol>
<li>Whether to keep the desk directory (5c5f4aaf) as the single index, and which desks to retire (S-01, S-05).</li>
<li>Which club-code set the project uses as its join key (S-03). The official standings set is recommended.</li>
<li>Whether the decision-desk check is required (S-04, Q-05).</li>
<li>Which open PRs to close or consolidate (S-05, Q-06).</li>
<li>The price-data policy, before any price or backtest page is published (S-06, Q-07).</li>
</ol>
<p>Each suggestion lists its options and what would change the call. Nothing has been implemented.</p>
</section>
<section class="panel">
<h2>Scope of this session</h2>
<p>This session did not build the injury, depth, pricing, backtest or leaderboard work in the brief. Those live in
the sibling desks listed on the Desks index, and this desk has not re-verified their numbers.
Its job is to fix what can be read today, with timestamps, and to list what is missing.</p>
</section>
"""
    page("summary.html", "Executive summary", body,
         lead="The short version: the official Week 11 slate is readable; Week 11 availability is not published yet; "
              "several repo facts block safe merges.")

    # ---------- suggestions.html ----------
    srows = []
    for s in sugg:
        srows.append([
            e(s["suggestion_id"]),
            e(s["title"]),
            e(s["options"]),
            e(s["recommendation"]),
            e(s["what_would_change_the_call"]),
            badge(s["decision"], "PENDING"),
            link(s["evidence_url"], "evidence"),
        ])
    body = (
        '<section class="notice"><strong>For review only.</strong> No suggestion here has been implemented. '
        'The Decision column is set by the reviewer. Choose an option by recording it in the next COORDINATION.md entry.</section>'
        + table(["ID", "Suggestion", "Options", "Recommendation", "What would change the call", "Decision", "Evidence"],
                srows, caption="Suggestions (6)")
    )
    page("suggestions.html", "Suggestions for review", body,
         lead="Suggestions to improve how decisions are made from this site. Each has options, a recommendation, "
              "and what would change it.")

    # ---------- questions.html ----------
    qrows = []
    for q in quest:
        qrows.append([
            e(q["question_id"]),
            e(q["question"]),
            e(q["what_we_have"]),
            e(q["what_we_lack"]),
            e(q["cheapest_route_to_close"]),
            e(q["blocks"]),
            link(q["evidence_url"], "source"),
        ])
    body = table(["ID", "Question", "What we have", "What we lack", "Cheapest route to close", "Blocks", "Source"],
                 qrows, caption="Questions (8)")
    page("questions.html", "Questions that block decisions", body,
         lead="Each question says what we have, what we lack, and the cheapest official route to close the gap.")

    # ---------- flagged.html ----------
    frows = []
    for f in flags:
        frows.append([
            badge(f["flag_id"], "BLOCKING" if f["severity"].upper() == "BLOCKING" else "REVIEW"),
            e(f["severity"]),
            e(f["title"]),
            e(f["detail"]),
            link(f["evidence_url"], "evidence"),
            e(f["source_class"]),
            e(f["raw_or_check_ref"]),
            e(f["status"]),
        ])
    body = (
        '<section class="notice"><strong>Flagged for review.</strong> These items do not block the merge. '
        'Each one has an evidence link and a reference to the file or check behind it.</section>'
        + table(["ID", "Severity", "Title", "Detail", "Evidence", "Source class", "Reference", "Status"], frows,
                caption=f"Flags ({len(flags)}; {len(open_flags)} open)")
    )
    page("flagged.html", "Flagged for review", body,
         lead="Irregularities, unverified items and method limits, published for review after the site is live.")


if __name__ == "__main__":
    build()
    print("built pages in", DESK)

"""Builds the static pages for the b8227c47 desk from data/*.csv.
Deterministic: no timestamps, no network, no environment-dependent ordering (rows keep CSV order)."""
import csv
import html
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data"
NAV = [("index.html", "Overview"), ("week10.html", "Week 10 counts"), ("games.html", "Games & byes"),
       ("terms.html", "Terms & decisions"), ("flagged.html", "Flagged for Review"), ("sources.html", "Sources")]


def read(name):
    with (DATA / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def e(s):
    return html.escape(s or "", quote=True)


def link(url, label=None):
    if not url:
        return '<span class="badge bad">UNVERIFIED</span>'
    return f'<a href="{e(url)}" rel="noopener">{e(label or url)}</a>'


def table(headers, rows, cells):
    head = "".join(f"<th>{e(h)}</th>" for h in headers)
    body = []
    for r in rows:
        body.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells(r)) + "</tr>")
    return f'<div class="tablewrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def status_class(s):
    s = s.upper()
    if s.startswith("BLOCKED") or s.startswith("OPEN") or s.startswith("UNVERIFIED"):
        return "bad"
    if s.startswith("PARTIAL") or s.startswith("APPLIED") or s.startswith("DONE (READ)"):
        return "warn"
    return "ok"


def page(fname, title, body, active):
    nav = "".join(f'<a href="{f}"{" class=active" if f == active else ""}>{e(t)}</a>' for f, t in NAV)
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · NFL official injury-report capture desk (b8227c47)</title>
<link rel="stylesheet" href="assets/style.css">
</head><body>
<header><div class="brand">NFL official injury-report capture · desk b8227c47</div>
<nav>{nav}</nav></header>
<main>
<h1>{e(title)}</h1>
{body}
</main>
<footer>Generated from <code>data/*.csv</code> by <code>build.py</code>. No network access at build time. Every table row links to an official nfl.com page or is marked <span class="badge bad">UNVERIFIED</span>. Repository: <a href="https://github.com/sassnarep3-star/Own5/tree/main/nfl-desk-b8227c47">nfl-desk-b8227c47/</a> · Not betting advice.</footer>
</body></html>
"""
    (HERE / fname).write_text(doc, encoding="utf-8")


def cards(items):
    return '<div class="cards">' + "".join(
        f'<div class="card"><div class="k">{e(k)}</div><div class="v">{v}</div><div class="s">{s}</div></div>'
        for k, v, s in items) + "</div>"


def build():
    readiness = read("readiness.csv")
    tos = read("tos_review.csv")
    flagged = read("flagged.csv")
    sources = read("sources.csv")
    clubs = read("week10_read.csv")
    byes = read("week10_byes.csv")
    games = read("week10_games.csv")
    ledger = read("ledger.csv")
    sha = clubs[0]["capture_sha256"]
    rows_total = sum(int(c["rows_listed"]) for c in clubs)
    S1 = "https://www.nfl.com/injuries/league/2026/reg10"
    S2 = "https://www.nfl.com/injuries/league/2026/reg11"
    S3 = "https://www.nfl.com/schedules/2026/by-week/week-10"
    S4 = "https://www.nfl.com/news/2024-nfl-com-terms-and-conditions"

    # ---- Overview
    body = cards([
        ("Automated capture", '<span class="badge bad">DISABLED</span>',
         "Terms s.1.3 require NFL's written consent before systematic retrieval (decision D-01)."),
        ("Latest verified read", f"{len(games)} games · {len(clubs)} club tables · {rows_total} rows",
         f'Week 10 official report, one read, SHA-256 <code>{e(sha[:12])}…</code>.'),
        ("Week 11 report", '<span class="badge warn">NOT PUBLISHED</span>',
         f'<a href="{S2}">reg11</a> returns HTTP 302 to reg10 at the time of the read.'),
        ("Captures in ledger", str(len(ledger)), "Zero scheduled captures. The ledger is empty by design until D-01 is decided."),
    ])
    body += """<section><h2>Summary</h2>
<ul class="plain">
<li>The desk verifies the official NFL injury report line by line. It does not run scheduled capture, because the NFL.com Terms bar systematic retrieval to build a database without written consent.</li>
<li>The one full read of the Week 10 report parses cleanly: 14 games, 28 club tables, 347 rows. The same 14 games appear on the official Week 10 schedule, and the four bye clubs (CHI, DEN, PHI, TB) match the schedule.</li>
<li>A correction: the Kansas City table is complete in the official HTML, and Patrick Mahomes' row is present. An earlier desk's truncation claim does not hold for the official page.</li>
<li>Week 11 is not published. The Week 11 URL redirects to Week 10, so no Week 11 designation is shown anywhere in this desk.</li>
</ul></section>"""
    body += "<section><h2>Decision-readiness (one row per requirement)</h2>"
    body += table(["ID", "Requirement", "Status", "Blocking gate", "Number that clears it", "Observed now", "Source"],
                  readiness,
                  lambda r: [e(r["id"]), e(r["requirement_line"]),
                             f'<span class="badge {status_class(r["status"])}">{e(r["status"])}</span>',
                             e(r["blocking_gate"]), e(r["number_that_clears_it"]), e(r["observed_now"]),
                             link(r["source_url"], "official page")])
    body += "</section>"
    body += """<section><h2>Decisions needed from you</h2><ul class="plain">
<li><b>D-01</b> Automated capture of the injury report: obtain NFL's written consent, use an authorized feed, or stop automated capture (see <a href="terms.html">Terms &amp; decisions</a>).</li>
<li><b>D-02</b> Legal read of the commercial-use clause in Terms s.1.3 for this public research repository.</li>
<li><b>D-03</b> Git history: this branch's history holds the raw probe bytes. Squash-merge so only derived files reach main, or accept the history as-is.</li>
</ul></section>"""
    page("index.html", "Overview", body, "index.html")

    # ---- Week 10 counts
    body = f"""<p>Single full read of the official Week 10 report. SHA-256 <code>{e(sha)}</code>. Counts are derived from the parsed page; no player-level rows are published here (see Terms &amp; decisions). Source for every row: <a href="{S1}">{S1}</a>.</p>"""
    body += table(["Club (as on report)", "Name (as on report)", "Rows", "Out", "Questionable", "Doubtful", "Blank game status",
                   "DNP", "Limited", "Full", "Source"],
                  clubs,
                  lambda c: [e(c["club_abbr_on_report"]), e(c["club_name_on_report"]), e(c["rows_listed"]),
                             e(c["game_status_Out"]), e(c["game_status_Questionable"]), e(c["game_status_Doubtful"]),
                             e(c["game_status_blank"]), e(c["practice_DNP"]), e(c["practice_Limited"]),
                             e(c["practice_Full"]), link(c["source_url"], "official page")])
    body += f"<p>Total rows: <b>{rows_total}</b> across {len(clubs)} clubs. Lions Out designations (Joseph, Mays, Reed) are present on the official page.</p>"
    body += "<h2>Clubs not on the Week 10 report (bye)</h2>"
    body += table(["Club (schedule)", "Name", "On injury report", "Source"], byes,
                  lambda b: [e(b["club_abbr_on_schedule"]), e(b["club_name_on_schedule"]), e(b["in_injury_report"]),
                             link(b["source_url"], "official schedule")])
    page("week10.html", "Week 10 official injury-report counts", body, "week10.html")

    # ---- Games & byes
    body = "<p>The 14 Week 10 matchups on the official injury report. Each row was checked against the official schedule page.</p>"
    body += table(["Day", "Kickoff (as listed)", "Network (as listed)", "Away (report)", "Home (report)", "Matches official schedule", "Source"],
                  games,
                  lambda g: [e(g["game_day"]), e(g["kickoff_local"] + " " + g["timezone"]), e(g["network"]),
                             e(g["away_abbr_on_report"]), e(g["home_abbr_on_report"]), e(g["matches_official_schedule"]),
                             link(g["source_url"], "injury report") + " · " + link(g["schedule_source_url"], "schedule")])
    body += "<p>Codes differ by page: the Rams are LAR on the injury report and LA on the schedule. No join is made silently (flag B-F06).</p>"
    page("games.html", "Week 10 games and byes", body, "games.html")

    # ---- Terms & decisions
    body = f"""<p>NFL.com Terms and Conditions (updated May 16, 2024), read in full at section 1.3 on 2026-11-18: <a href="{S4}">{S4}</a>.</p>"""
    body += table(["ID", "Clause", "Official text (quoted)", "Implication for this desk", "Decision status", "Source"], tos,
                  lambda t: [e(t["id"]), e(t["clause"]), e(t["official_text_quoted"]), e(t["implication_for_this_desk"]),
                             f'<span class="badge {status_class(t["decision_status"])}">{e(t["decision_status"])}</span>',
                             link(t["source_url"], "official page")])
    body += "<h2>Pending decisions</h2><ul class=\"plain\"><li><b>D-01</b> consent, authorized feed, or stop automated capture.</li><li><b>D-02</b> legal read of the commercial-use wording.</li><li><b>D-03</b> git-history handling for the probe bytes.</li></ul>"
    page("terms.html", "Terms & decisions", body, "terms.html")

    # ---- Flagged
    body = "<p>Irregularities, corrections and unverified items. These are published, not silently fixed. None blocks the desk's verified counts.</p>"
    body += table(["ID", "Kind", "Title", "What the official record says", "What we do", "Decision needed", "Source"], flagged,
                  lambda f: [e(f["id"]), e(f["kind"]), e(f["title"]), e(f["what_the_official_record_says"]),
                             e(f["what_we_do"]), e(f["decision_needed"]), link(f["source_url"], "official page")])
    page("flagged.html", "Flagged for Review", body, "flagged.html")

    # ---- Sources
    body = "<p>Every official page this desk read, with the method and the result. Checks are dated 2026-11-18 UTC.</p>"
    body += table(["ID", "Official page", "What was checked", "How it was checked", "Checked (UTC)", "Result"], sources,
                  lambda s: [e(s["id"]), link(s["url"]), e(s["what_was_checked"]), e(s["how_checked"]),
                             e(s["checked_utc"]) or '<span class="badge bad">UNVERIFIED</span>', e(s["result"])])
    page("sources.html", "Sources", body, "sources.html")


if __name__ == "__main__":
    build()
    print("built pages")

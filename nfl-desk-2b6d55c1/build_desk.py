"""Deterministic static site builder for the NFL Origin Desk (session 2b6d55c1).

Reads every table from data/nfl-desk-2b6d55c1/*.csv and renders HTML pages.
No clock, no network, no git inside the builder. Output is byte-for-byte
reproducible for a given input set. No JavaScript is required for content.
"""
import csv, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "..", "data", "nfl-desk-2b6d55c1")
OUT = os.path.join(ROOT, "pages")

NAV = [
    ("index.html", "Landing"),
    ("origination.html", "Originated Lines"),
    ("snapshots.html", "Price Snapshots"),
    ("results.html", "Verified Results"),
    ("correlations.html", "Correlations"),
    ("availability.html", "Availability & Injury"),
    ("leaderboard.html", "Leaderboard"),
    ("questions.html", "Questions Register"),
    ("suggestions.html", "Suggestions Register"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
]


def read_csv(name):
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(s):
    return html.escape("" if s is None else str(s))


def nav_html(active=None):
    items = []
    for href, label in NAV:
        klass = ' class="nav-active"' if active == href else ""
        items.append('<a href="' + esc(href) + '"' + klass + ">" + esc(label) + "</a>")
    return "\n".join(items)


def table_html(rows, id_, caption, blank="(blank)"):
    if not rows:
        return ("<table id='" + id_ + "'><caption>" + esc(caption) + "</caption>"
                "<thead><tr></tr></thead><tbody></tbody></table>")
    cols = list(rows[0].keys())
    thead = "".join("<th scope='col'>" + esc(c) + "</th>" for c in cols)
    tbody = []
    for r in rows:
        cells = "".join(
            "<td>" + (esc(blank) if r.get(c, "") == "" else esc(r.get(c, ""))) + "</td>"
            for c in cols
        )
        tbody.append("<tr>" + cells + "</tr>")
    return ("<table id='" + id_ + "'><caption>" + esc(caption) + "</caption>"
            "<thead><tr>" + thead + "</tr></thead><tbody>" + "".join(tbody) + "</tbody></table>")


def page(title, body, active=None):
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>" + esc(title) + " &bull; OWN5 NFL Origin Desk</title>"
            "<link rel='stylesheet' href='style.css'></head><body>"
            "<a class='skip' href='#main'>Skip to content</a>"
            "<header class='topbar'><div class='brand'>OWN5<span>5</span></div>"
            "<div class='title'>NFL Origin Desk &mdash; session 2b6d55c1</div></header>"
            "<nav aria-label='Main'>" + nav_html(active) + "</nav>"
            "<main id='main'><h1>" + esc(title) + "</h1>" + body + "</main>"
            "<footer><p>OWN5 NFL Origin Desk &mdash; evidence-first, source-linked or "
            "blank-and-flagged, never inferred.</p>"
            "<p>Session 2b6d55c1 &bull; Additive namespace: nfl-desk-2b6d55c1/** &bull; "
            "No other session's files edited.</p></footer></body></html>")


def write_page(name, title, body, active=None):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(page(title, body, active))


def render():
    os.makedirs(OUT, exist_ok=True)

    sources = read_csv("sources.csv")
    standings = read_csv("standings.csv")
    results = read_csv("results_w10.csv")
    schedule = read_csv("schedule_w11.csv")
    origination = read_csv("origination.csv")
    snapshots = read_csv("price_snapshots.csv")
    correlations = read_csv("correlations.csv")
    availability = read_csv("availability.csv")
    leaderboard = read_csv("leaderboard.csv")
    gates = read_csv("gates.csv")
    readiness = read_csv("readiness.csv")
    questions = read_csv("questions.csv")
    suggestions = read_csv("suggestions.csv")
    flagged = read_csv("flagged.csv")

    # ---------- Landing ----------
    landing = ("<h2>Decision-readiness table</h2>"
               "<p>One row per requirement &rarr; blocking gate &rarr; number that would clear it "
               "&rarr; observed status.</p>"
               + table_html(readiness, "readiness",
                            "Decision-readiness table (one row per requirement)")
               + "<p class='muted'>Blank cells = unverified, not zero. Nothing is inferred.</p>")
    write_page("index.html", "OWN5 NFL Origin Desk &mdash; Landing", landing, "index.html")

    # ---------- Originated lines ----------
    orig_body = ("<h2>Originated lines &mdash; Week 11 (side &rarr; total &rarr; moneyline)</h2>"
                 "<p>Model fair line / market line / difference are separate columns. Market columns "
                 "are blank+flagged because no verified operator price source exists (price-data "
                 "policy P-01, flag FZ-04). Every row stores probability + inputs + inputs hash "
                 "(no pick without its inputs).</p>"
                 "<p class='muted'>Positive model_fair (side) = home team favoured. Home team is "
                 "listed second.</p>"
                 + table_html(origination, "origination",
                              "Originated lines (39 rows: 13 games x 3 markets)"))
    write_page("origination.html", "Originated Lines", orig_body, "origination.html")

    # ---------- Price snapshots ----------
    snap_body = ("<h2>Price-snapshot store (opening &amp; closing per market)</h2>"
                 "<p>Immutable opening snapshots for every originated market. Closings are "
                 "blank+pending by price-data policy (no operator price source). Each snapshot "
                 "carries its inputs hash.</p>"
                 + table_html(snapshots, "snapshots",
                              "Price snapshots (39 opening rows)"))
    write_page("snapshots.html", "Price Snapshots", snap_body, "snapshots.html")

    # ---------- Verified results ----------
    res_body = ("<h2>Verified results feed &mdash; Week 10 (reconciled to official standings)</h2>"
                "<p>14 finals from the official Week-10 schedule, plus CHI/DEN/PHI/TB byes. Ingested "
                "as game-level results for opponent-aware ratings.</p>"
                + table_html(results, "results", "Week-10 results (14 games, FINAL)"))
    write_page("results.html", "Verified Results", res_body, "results.html")

    # ---------- Correlations ----------
    corr_body = ("<h2>Correlations &mdash; officially sourced numbers only, n published with each "
                 "value</h2>"
                 "<p>Computed in-repo from the official 2026 standings (n=32 clubs). Pearson "
                 "product-moment with Fisher-z 95% confidence interval. n is published on every "
                 "row.</p>"
                 + table_html(correlations, "correlations",
                              "Correlations from official standings (n=32)"))
    write_page("correlations.html", "Correlations", corr_body, "correlations.html")

    # ---------- Availability ----------
    avail_body = ("<h2>Availability &amp; injury &mdash; deltas never levels</h2>"
                  "<p>Week-11 official injury report read with a UTC clock. 10 of 32 clubs read; the "
                  "rest are NOT READ (blank+flagged, never inferred). The injury signal is a "
                  "surprise (change), never a level; levels are not used as a model feature.</p>"
                  + table_html(availability, "availability",
                               "Week-11 injury &amp; availability reads"))
    write_page("availability.html", "Availability & Injury", avail_body, "availability.html")

    # ---------- Leaderboard ----------
    lead_body = ("<h2>Leaderboard &mdash; signal separated from staking</h2>"
                 "<p>Every strategy is pre-registered (registration hash frozen in git). Backtest "
                 "numbers are forbidden from ever appearing on the leaderboard (G03). No strategy "
                 "is certified until its validation gates pass; control baselines (random picks; "
                 "favorites only) are listed but not ranked for skill.</p>"
                 + table_html(leaderboard, "leaderboard",
                              "Leaderboard (pre-registered, not certified)")
                 + "<h3>Validation gates</h3>" + table_html(gates, "gates",
                              "Validation gates (G01-G13)"))
    write_page("leaderboard.html", "Leaderboard", lead_body, "leaderboard.html")

    # ---------- Questions ----------
    q_body = ("<h2>Questions / information / answers register</h2>"
              "<p>Open questions and missing information that must be resolved before any decision "
              "can reasonably be made. Suggestions for discovering missing information are logged "
              "here.</p>" + table_html(questions, "questions", "Questions register"))
    write_page("questions.html", "Questions Register", q_body, "questions.html")

    # ---------- Suggestions ----------
    sug_body = ("<h2>Suggestions register (review before implement)</h2>"
                "<p>Dedicated section for suggestions. Each suggestion carries a decision, a "
                "recommendation, and a two-sided 'what would change our mind' field. Nothing is "
                "implemented without an owner decision.</p>"
                + table_html(suggestions, "suggestions", "Suggestions register"))
    write_page("suggestions.html", "Suggestions Register", sug_body, "suggestions.html")

    # ---------- Flagged ----------
    flag_body = ("<h2>Flagged for Review</h2>"
                 "<p>Irregularities and unverified items. These do not block the merge; they are "
                 "published with source links so they can be reviewed after the site is live.</p>"
                 + table_html(flagged, "flagged", "Flagged irregularities"))
    write_page("flagged.html", "Flagged for Review", flag_body, "flagged.html")

    # ---------- Sources ----------
    src_body = ("<h2>Sources &amp; findings</h2>"
                "<p>Every table row is linked to an official source or explicitly "
                "blank-and-flagged. No values are inferred.</p>"
                + table_html(sources, "sources", "Source register")
                + "<h3>Standings snapshot (official, 32 clubs)</h3>"
                + table_html(standings, "standings",
                             "2026 NFL league standings (read 2026-11-19)"))
    write_page("sources.html", "Sources & Findings", src_body, "sources.html")

    # ---------- style.css ----------
    css = (
        ":root{--ink:#0f1f23;--surf:#ffffff;--panel:#eef4f5;--accent:#0b6e6b;"
        "--accent-2:#118ab2;--muted:#5b7a80;--line:#c9d6d9;}"
        "*{box-sizing:border-box}html{font-size:16px}"
        "body{margin:0;color:var(--ink);font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.5}"
        ".skip{position:absolute;left:-9999px;top:auto;width:1px;height:1px;overflow:hidden}"
        ".topbar{display:flex;align-items:center;gap:12px;padding:10px 16px;background:#d7e3e4;color:var(--ink)}"
        ".brand{font-weight:800;font-size:1.125rem;letter-spacing:0.06em}"
        ".brand span{color:var(--accent)}"
        ".title{font-size:0.9rem;color:var(--muted)}"
        "nav{border-bottom:1px solid var(--line);background:var(--panel);position:sticky;top:0;z-index:10}"
        "nav[aria-label='Main']{display:flex;gap:0;overflow-x:auto}"
        "nav a{display:block;padding:10px 14px;text-decoration:none;color:var(--ink);font-weight:600;"
        "font-size:0.85rem;white-space:nowrap;border-bottom:2px solid transparent}"
        "nav a.nav-active{color:var(--accent);border-bottom-color:var(--accent)}"
        "nav a:hover{background:#e3ecec}"
        "main{max-width:1200px;margin:0 auto;padding:16px}"
        "h1{font-size:1.5rem;margin:0 0 8px 0;border-bottom:2px solid var(--accent);padding-bottom:6px}"
        "h2{font-size:1.15rem;margin:24px 0 8px 0;color:var(--accent-2)}"
        "p.muted{color:var(--muted);font-size:0.85rem}"
        "caption{caption-side:top;text-align:left;font-weight:700;margin-bottom:6px;font-size:0.9rem;color:var(--muted)}"
        "table{width:100%;border-collapse:collapse;margin:10px 0 18px 0;background:var(--surf)}"
        "th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;font-size:0.86rem;vertical-align:top}"
        "th{background:var(--panel);color:var(--ink)}"
        "tr:nth-child(even) td{background:#f7fafb}"
        "footer{margin-top:30px;padding:16px;border-top:1px solid var(--line);color:var(--muted);font-size:0.8rem}"
        "a.skip:focus{position:static;width:auto;height:auto;padding:8px}"
    )
    with open(os.path.join(ROOT, "style.css"), "w", encoding="utf-8") as f:
        f.write(css)
    with open(os.path.join(OUT, "style.css"), "w", encoding="utf-8") as f:
        f.write(css)
    print("built pages:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    render()

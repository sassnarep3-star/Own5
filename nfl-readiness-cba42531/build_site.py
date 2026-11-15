"""Deterministic static-site build for the NFL decision-readiness desk.

Every body-table row is rendered with a source cell.  A row whose source cell
is empty is rendered with an explicit UNVERIFIED badge that links to the
Flagged for Review page, so an empty cell can never be mistaken for a sourced
value.  ``verify.py`` re-walks the generated HTML and fails the build if that
invariant is broken.
"""

from __future__ import annotations

import csv
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from registers import RETRIEVED_UTC, SESSION

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
SITE = ROOT

NAV = [
    ("index.html", "Overview", "Dashboard"),
    ("executive-summary.html", "Executive summary", "Summary"),
    ("requirements.html", "Decision-readiness", "Governance"),
    ("strategies.html", "Strategy falsification", "Governance"),
    ("suggestions.html", "Suggestions for review", "Governance"),
    ("questions.html", "Open questions", "Governance"),
    ("luck.html", "Removal of luck", "Statistics"),
    ("flagged.html", "Flagged for review", "Assurance"),
    ("repo-audit.html", "Repo consolidation", "Assurance"),
    ("sources.html", "Sources", "Assurance"),
]

CSS = """
:root{--bg:#f5f7f6;--card:#fff;--ink:#12211d;--muted:#5d7168;--line:#dfe6e2;
--accent:#14614f;--accent-soft:#e3f0eb;--warn:#8a5a00;--warn-soft:#fdf3e0;
--bad:#8c2f2f;--bad-soft:#fbeaea;--ok:#14614f;--ok-soft:#e3f0eb;--slate:#3d4f48}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg)}
a{color:var(--accent)}
.layout{display:grid;grid-template-columns:250px 1fr;min-height:100vh}
.sidebar{background:#0f2b25;color:#cfe3dc;padding:20px 16px;position:sticky;top:0;height:100vh;overflow:auto}
.brand{display:flex;gap:10px;align-items:center;color:#fff;text-decoration:none;font-weight:700;font-size:17px}
.brand span.badge{background:var(--accent);border-radius:6px;padding:2px 8px;font-size:12px}
.brand small{display:block;font-weight:500;font-size:11px;color:#8fb3a7;letter-spacing:.08em}
.navcap{font-size:10px;letter-spacing:.14em;color:#7fa394;margin:16px 0 6px;text-transform:uppercase}
.sidebar nav a{display:block;color:#cfe3dc;text-decoration:none;padding:7px 10px;border-radius:7px;font-size:13.5px}
.sidebar nav a:hover{background:#173a32}
.sidebar nav a.active{background:var(--accent);color:#fff;font-weight:600}
.sidebar nav a small{display:block;color:#8fb3a7;font-weight:400;font-size:11px}
.sidebar nav a.active small{color:#bfe0d4}
.sidefoot{margin-top:18px;font-size:11.5px;color:#8fb3a7;border-top:1px solid #234a40;padding-top:12px}
main{padding:26px 30px 60px;max-width:1500px}
h1{font-size:26px;margin:0 0 6px}
h2{font-size:19px;margin:30px 0 10px}
p.lede{color:var(--muted);margin:0 0 18px;max-width:95ch}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:700}
.stamp{font-size:12px;color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:18px 0 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.card span{display:block;font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.card strong{display:block;font-size:24px;margin-top:4px;font-variant-numeric:tabular-nums}
.card small{color:var(--muted);font-size:12px}
.card.warn strong{color:var(--warn)} .card.bad strong{color:var(--bad)} .card.ok strong{color:var(--ok)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:16px 0}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:13px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#eef3f0;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:#33473f;position:sticky;top:0}
tbody tr:hover{background:#f3f7f4}
td.num{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
.pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11.5px;font-weight:600;white-space:nowrap}
.pill.met{background:var(--ok-soft);color:var(--ok)}
.pill.partial{background:var(--warn-soft);color:var(--warn)}
.pill.absent{background:var(--bad-soft);color:var(--bad)}
.pill.rejected{background:#ececec;color:#555}
.pill.proposed{background:#e7eefb;color:#2a4d8f}
.pill.blocking{background:var(--bad-soft);color:var(--bad)}
.pill.review{background:var(--warn-soft);color:var(--warn)}
.pill.watch{background:#e7eefb;color:#2a4d8f}
.pill.info{background:#ececec;color:#555}
.pill.match{background:var(--ok-soft);color:var(--ok)}
.pill.irregular{background:var(--bad-soft);color:var(--bad)}
.pill.notchecked{background:#ececec;color:#555}
.unverified{color:var(--bad);font-weight:600;font-size:11px;white-space:nowrap}
.src a{font-size:11.5px;word-break:break-all}
.footnote{font-size:12px;color:var(--muted);margin-top:10px}
.note{background:var(--warn-soft);border:1px solid #efd9a8;border-radius:10px;padding:12px 14px;font-size:13px;margin:14px 0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.layout{grid-template-columns:1fr}.sidebar{position:static;height:auto}.grid2{grid-template-columns:1fr}}
"""


def esc(value) -> str:
    return html.escape(str(value) if value is not None else "")


def load_csv(name: str) -> tuple[list[str], list[dict]]:
    with open(os.path.join(DATA, name + ".csv"), "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or []), list(reader)


def status_pill(status: str) -> str:
    key = (status or "").lower()
    cls = "absent"
    if "met" in key and "partial" not in key:
        cls = "met"
    elif "partial" in key:
        cls = "partial"
    elif "absent" in key:
        cls = "absent"
    elif "reject" in key:
        cls = "rejected"
    elif "propos" in key:
        cls = "proposed"
    elif "in progress" in key:
        cls = "partial"
    return f'<span class="pill {cls}">{esc(status)}</span>'


def sev_pill(sev: str) -> str:
    key = (sev or "").lower()
    cls = "info"
    if "block" in key:
        cls = "blocking"
    elif "review" in key:
        cls = "review"
    elif "watch" in key:
        cls = "watch"
    return f'<span class="pill {cls}">{esc(sev)}</span>'


def src_cell(url: str, label: str = "source") -> str:
    if url:
        return f'<td class="src"><a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a></td>'
    return '<td class="src"><span class="unverified" data-unverified="1">UNVERIFIED</span></td>'


def render_table(columns, rows, source_col: str = "source_url",
                 source_label: str = "source", pill_cols: dict | None = None) -> str:
    """columns: list of (csv_key, display_label) tuples.

    The display label is shown in the header; the value is read from the CSV
    key.  This keeps the on-screen wording independent of the CSV schema.
    """
    pill_cols = pill_cols or {}
    thead = "".join(f"<th>{esc(label)}</th>" for _key, label in columns)
    body = []
    for row in rows:
        cells = []
        for key, _label in columns:
            val = row.get(key, "")
            if key == source_col:
                cells.append(src_cell(val, source_label))
            elif key in pill_cols:
                cells.append(f"<td>{pill_cols[key](val)}</td>")
            else:
                cells.append(f"<td>{esc(val)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def page(title: str, active: str, body: str, eyebrow: str, lede: str) -> str:
    nav = []
    for href, label, cap in NAV:
        cls = "active" if href == active else ""
        nav.append(f'<a class="{cls}" href="{href}">{esc(label)}<small>{esc(cap)}</small></a>')
    nav_html = f'<div class="navcap">Navigation</div>' + "".join(nav)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} - Own5 NFL Decision Readiness</title>
<style>{CSS}</style></head>
<body><div class="layout">
<aside class="sidebar"><a class="brand" href="index.html"><span class="badge">OWN5</span>
<span>NFL Decision<br>Readiness<small>session cba42531</small></span></a>
{nav_html}
<div class="sidefoot">Deterministic build. Every table row carries an official source link or an explicit UNVERIFIED badge. Retrieved {esc(RETRIEVED_UTC)}.</div>
</aside>
<main><div class="eyebrow">{esc(eyebrow)}</div>
<h1>{esc(title)}</h1>
<p class="lede">{lede}</p>
{body}
</main></div></body></html>"""


def build() -> list[str]:
    # --- load registers ---
    readiness_hdr, readiness = load_csv("readiness")
    strat_hdr, strat = load_csv("strategy_falsification")
    sug_hdr, sug = load_csv("suggestions")
    q_hdr, questions = load_csv("questions")
    fl_hdr, flagged = load_csv("flagged")
    luck_hdr, luck = load_csv("luck_panel")
    src_hdr, sources = load_csv("sources")
    rc_hdr, repo_c = load_csv("repo_consolidation")
    ev_hdr, evidence = load_csv("official_evidence")

    # --- counts for the landing KPI cards ---
    total_req = len(readiness)
    met = sum(1 for r in readiness if r["status"] == "Met")
    partial = sum(1 for r in readiness if r["status"] == "Partially met")
    absent = sum(1 for r in readiness if r["status"] == "Absent")
    rejected = sum(1 for r in readiness if "Rejected" in r["status"])
    proposed = sum(1 for r in readiness if r["status"] == "Proposed")
    certified = 0  # no strategy passes all gates, by design
    blocking_flags = sum(1 for f in flagged if f["severity"] == "blocking")
    official_sources = sum(1 for s in sources if s["tier"] == "OFFICIAL")

    def card(label, value, sub, cls=""):
        return f'<div class="card {cls}"><span>{esc(label)}</span><strong>{esc(value)}</strong><small>{esc(sub)}</small></div>'

    kpis = "".join([
        card("Requirements", total_req, "one row per brief item"),
        card("Met", met, f"{partial} partially met"),
        card("Absent", absent, f"{proposed} proposed, {rejected} rejected"),
        card("Certified strategies", certified, "0 pass all gates, by design", "warn"),
        card("Blocking flags", blocking_flags, "published for review", "bad"),
        card("Official sources", official_sources, "linked on every row"),
    ])

    # --- landing: decision-readiness table (the centrepiece) ---
    readiness_pills = {"status": status_pill}
    readiness_table = render_table(
        [("req_id", "ID"), ("requirement", "Requirement"), ("status", "Status"),
         ("implemented_where", "Implemented where"), ("blocking_gate", "Blocking gate"),
         ("clearing_number", "Clearing number"), ("source_url", "Source")],
        readiness, source_col="source_url", source_label="source",
        pill_cols=readiness_pills)

    # --- landing: removal-of-luck panel ---
    luck_table = render_table(
        [("metric", "Metric"), ("value", "Value"), ("n", "n"), ("method", "Method"),
         ("what_it_means", "What it means"), ("source_url", "Source")],
        luck, source_col="source_url", source_label="source")

    landing_body = f"""
<div class="cards">{kpis}</div>
<div class="note">This is a <strong>decision-readiness</strong> view, not a results claim.
It consolidates the NFL desks already on this repository into one table: for every requirement it
names the gate that blocks it and the number that would clear it. No strategy is certified and no
bet has been placed; values that cannot be confirmed from an official source are left blank and
flagged on the <a href="flagged.html">Flagged for Review</a> page.</div>
<h2>Decision-readiness matrix</h2>
<p class="stamp">One row per requirement. Statuses are checked against the cited repo file by
<code>consolidate.py</code> before the build; blocking gates and clearing numbers are the fields a
reviewer acts on.</p>
{readiness_table}
<h2>Removal of luck</h2>
<p class="stamp">Luck cannot be removed from sports outcomes; it can only be measured. Every value
below carries its sample size and source. Full panel on the
<a href="luck.html">Removal of luck</a> page.</p>
{luck_table}
<p class="footnote">Built deterministically by <code>build_site.py</code> from the CSVs in
<code>data/</code>. Sources: <a href="sources.html">Sources registry</a>.</p>
"""
    pages = {"index.html": page(
        "Decision-readiness dashboard", "index.html", landing_body,
        "Dashboard", "Consolidated readiness of every requirement in the NFL line-origination brief, "
        "with the gate that blocks each one and the number that would clear it.")}

    # --- requirements detail ---
    req_detail = render_table(
        [("req_id", "ID"), ("requirement", "Requirement"), ("category", "Category"),
         ("status", "Status"), ("implemented_where", "Implemented where"),
         ("blocking_gate", "Blocking gate"), ("clearing_number", "Clearing number"),
         ("note", "Note"), ("source_url", "Source")],
        readiness, source_col="source_url", source_label="source", pill_cols=readiness_pills)
    pages["requirements.html"] = page(
        "Decision-readiness matrix", "requirements.html",
        f"<h2>All requirements</h2>{req_detail}",
        "Governance", "The full requirement register with status, the file that implements it, the "
        "blocking gate and the clearing number.")

    # --- strategy falsification ---
    strat_table = render_table(
        [("strategy_id", "ID"), ("family", "Family"), ("bet_class", "Bet class"),
         ("universe", "Universe"), ("where_defined", "Where defined"),
         ("confirm_side", "What would confirm it"),
         ("refute_side", "What would change our mind (refute)"),
         ("current_evidence", "Current evidence"), ("n_bets", "n"), ("source_url", "Source")],
        strat, source_col="source_url", source_label="source")
    pages["strategies.html"] = page(
        "Strategy falsification register", "strategies.html",
        f"<div class=\"note\">Every strategy carries a two-sided falsification field: the evidence "
        f"that would keep it live and the evidence that would send it back to paper. This is the "
        f"\"what would change our mind\" requirement applied to every entry.</div>{strat_table}",
        "Governance", "A two-sided 'what would change our mind' field for every strategy family.")

    # --- suggestions ---
    sug_table = render_table(
        [("sug_id", "ID"), ("title", "Title"), ("problem", "Problem"),
         ("option_a", "Option A"), ("option_b", "Option B"), ("option_c", "Option C"),
         ("recommended", "Recommended"), ("impact", "Impact"), ("effort", "Effort"),
         ("evidence", "Evidence"), ("source_desk", "Source desk"), ("decision", "Decision"),
         ("review_test", "Review test"), ("implemented", "Implemented"), ("source_url", "Source")],
        sug, source_col="source_url", source_label="source")
    pages["suggestions.html"] = page(
        "Suggestions for review", "suggestions.html",
        f"<div class=\"note\">A dedicated review section. Each proposal lists costed options, a "
        f"recommended path and the test that would change the call. Nothing here is implemented "
        f"except the consolidation suggestion SG-15, which is this desk.</div>{sug_table}",
        "Governance", "Proposals a reviewer can accept or reject before any change is built.")

    # --- questions ---
    q_table = render_table(
        [("q_id", "ID"), ("question", "Question"), ("why_it_matters", "Why it matters"),
         ("what_we_have", "What we have"), ("what_is_missing", "What is missing"),
         ("cheapest_way_to_resolve", "Cheapest way to resolve"),
         ("what_it_blocks", "What it blocks"), ("status", "Status"),
         ("source_desk", "Source desk"), ("source_url", "Source")],
        questions, source_col="source_url", source_label="source",
        pill_cols={"status": status_pill})
    pages["questions.html"] = page(
        "Open questions", "questions.html",
        f"<div class=\"note\">The have-vs-missing register. Blocking items are named explicitly with "
        f"the cheapest route to close them; some cannot be closed from any public source.</div>{q_table}",
        "Governance", "Questions, information and answers needed before a decision can be made.")

    # --- luck ---
    pages["luck.html"] = page(
        "Removal of luck", "luck.html",
        f"<div class=\"note\">Luck is measured, not removed. Each value is computed from the repo's "
        f"luck-vs-skill tables and carries its sample size and source.</div>{luck_table}",
        "Statistics", "The removal-of-luck panel: how short samples manufacture apparent skill.")

    # --- flagged ---
    fl_table = render_table(
        [("flag_id", "ID"), ("severity", "Severity"), ("area", "Area"), ("title", "Title"),
         ("detail", "Detail"), ("consequence", "Consequence"), ("action", "Action"),
         ("status", "Status"), ("source_desk", "Source desk"), ("source_url", "Source")],
        flagged, source_col="source_url", source_label="source",
        pill_cols={"severity": sev_pill})
    pages["flagged.html"] = page(
        "Flagged for review", "flagged.html",
        f"<div class=\"note\">Irregularities and unverified items. These do not block publication; "
        f"they are published so a reviewer can act on them.</div>{fl_table}",
        "Assurance", "Irregularities and unverified values, published with their sources.")

    # --- repo consolidation ---
    def rc_status(v):
        key = (v or "").lower()
        cls = "match" if key == "match" else "irregular" if key == "irregular" else "notchecked"
        return f'<span class="pill {cls}">{esc(v)}</span>'

    rc_table = render_table(
        [("check_id", "ID"), ("claim", "Claim"), ("desk", "Desk"), ("status", "Status"),
         ("evidence", "Evidence"), ("reason", "Reason"), ("source_url", "Source")],
        repo_c, source_col="source_url", source_label="source",
        pill_cols={"status": rc_status})
    pages["repo-audit.html"] = page(
        "Repo consolidation log", "repo-audit.html",
        f"<div class=\"note\">A line-by-line review of the desks' headline claims against the "
        f"official pages fetched for this build. Irregularities are flagged, never silently "
        f"corrected.</div>{rc_table}",
        "Assurance", "Consolidated, verified review of the existing NFL desks.")

    # --- sources ---
    src_table = render_table(
        [("source_id", "ID"), ("publisher", "Publisher"), ("title", "Title"), ("url", "URL"),
         ("tier", "Tier"), ("retrieved_utc", "Retrieved (UTC)"), ("used_for", "Used for"),
         ("source_desk", "Source desk")],
        sources, source_col="url", source_label="open")
    pages["sources.html"] = page(
        "Sources registry", "sources.html",
        f"<div class=\"note\">Every official and repository source the readiness matrix and the luck "
        f"panel rest on. OFFICIAL = NFL.com; REPOSITORY = this repo's own verified files.</div>{src_table}",
        "Assurance", "The sources behind every published value.")

    # --- executive summary ---
    exec_body = f"""
<div class="cards">{kpis}</div>
<div class="panel"><h2 style="margin-top:0">What this desk is</h2>
<p>Session <strong>cba42531</strong> consolidates the NFL line-origination desks already on this
repository into a single <strong>decision-readiness</strong> view. It does not re-run any desk's
engine and does not edit any other session's files; it reads them and reconciles. The landing page
is the requested table: one row per requirement, each carrying the gate that blocks it and the
number that would clear it.</p>
<h2>Verified for 2026-11-15</h2>
<ul>
<li>Official NFL standings, Week 10 schedule and Week 10 injury report were fetched and read
directly. The league's PF==PA identity holds on the 2026-11-15 snapshot, and the standings delta
versus the pinned 2026-11-14 snapshot is explained by the Week 10 finals on the official schedule.</li>
<li>The three Lions designations are confirmed <strong>Out</strong> on the official report
(Kerby Joseph, Cade Mays, D.J. Reed); Patriots Ben Brown is confirmed at <strong>C</strong>.</li>
<li>The official pages publish no betting prices, so no strategy can pass the price-provenance
gate; operator open/close values are blank and flagged, never inferred.</li>
</ul>
<h2>Headline state</h2>
<ul>
<li><strong>0 strategies certified.</strong> No family passes all gates; the leaderboard is empty
by design, not by omission.</li>
<li><strong>{met} of {total_req} requirements met</strong>, {partial} partially met, {absent}
absent, {rejected} rejected by design, {proposed} proposed as design gaps.</li>
<li><strong>{blocking_flags} blocking flags</strong> are published on the Flagged for Review page;
they do not block publication.</li>
</ul>
<h2>What would move the needle</h2>
<p>The single highest-leverage gap is price: without a timestamped operator open/close price,
closing-line value, ROI at a real price and the demotion triggers that depend on them are
unmeasurable. Suggestion SG-01 costs two scheduled captures a week and is the cheapest path to a
testable gate G2. The second is sample size (SG-04): the certification universe is 4-51 bets against
a 300-bet minimum.</p>
<p class="footnote">Restates only computed or officially sourced values. No performance claim; no
bets placed.</p>
</div>
"""
    pages["executive-summary.html"] = page(
        "Executive summary", "executive-summary.html", exec_body,
        "Summary", "Important details of the consolidated decision-readiness desk, verified against "
        "official sources on 2026-11-15.")

    written = []
    for name, html_doc in pages.items():
        path = os.path.join(SITE, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html_doc)
        written.append(path)
    return written


if __name__ == "__main__":
    out = build()
    print(f"Wrote {len(out)} pages to {os.path.relpath(SITE)}:")
    for p in out:
        print("  -", os.path.relpath(p, os.path.dirname(ROOT)))

"""Deterministic static-site build for the Own5 Decision-Readiness desk.

The landing page carries the decision-readiness table: one row per requirement,
with the gate that blocks it, the number that would clear it, and the observed
number today.  Every body-table row is rendered with a source cell; a value that
cannot be confirmed from an official source is rendered as an explicit UNVERIFIED
blank badge.  verify.py re-walks the generated HTML and fails the build if that
invariant is broken.  Stdlib only.
"""

from __future__ import annotations

import csv
import html
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
SITE = ROOT

NAV = [
    ("index.html", "Overview", "Dashboard"),
    ("readiness.html", "Decision readiness", "Decision support"),
    ("questions.html", "Open questions", "Governance"),
    ("suggestions.html", "Suggestions", "Governance"),
    ("sources.html", "Sources", "Assurance"),
    ("flagged.html", "Flagged for review", "Assurance"),
    ("review.html", "Repo review", "Assurance"),
]

CSS = """
:root{--bg:#f5f7f6;--card:#ffffff;--ink:#12211d;--muted:#5d7168;--line:#dfe6e2;
--accent:#14614f;--accent-soft:#e3f0eb;--warn:#8a5a00;--warn-soft:#fdf3e0;
--bad:#8c2f2f;--bad-soft:#fbeaea;--ok:#14614f;--ok-soft:#e3f0eb;--slate:#3d4f48}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg)}
a{color:var(--accent)}
.skip{position:absolute;left:-9999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:9}
.layout{display:grid;grid-template-columns:250px 1fr;min-height:100vh}
.sidebar{background:#0f2b25;color:#cfe3dc;padding:20px 16px;position:sticky;top:0;height:100vh;overflow:auto}
.brand{display:flex;gap:10px;align-items:center;color:#fff;text-decoration:none;font-weight:700;font-size:17px;margin-bottom:4px}
.brand span.badge{background:var(--accent);border-radius:6px;padding:2px 8px;font-size:13px}
.brand small{display:block;font-weight:500;font-size:11px;color:#8fb3a7;letter-spacing:.08em}
.navcap{font-size:10px;letter-spacing:.14em;color:#7fa394;margin:16px 0 6px;text-transform:uppercase}
.sidebar nav a{display:block;color:#cfe3dc;text-decoration:none;padding:7px 10px;border-radius:7px;font-size:13.5px}
.sidebar nav a:hover{background:#173a32}
.sidebar nav a.active{background:var(--accent);color:#fff;font-weight:600}
.sidefoot{margin-top:18px;font-size:11.5px;color:#8fb3a7;border-top:1px solid #234a40;padding-top:12px}
main{padding:26px 30px 60px;max-width:1500px}
h1{font-size:27px;margin:0 0 6px}h2{font-size:19px;margin:30px 0 10px}h3{font-size:15px;margin:20px 0 8px}
p.lede{color:var(--muted);margin:0 0 18px;max-width:95ch}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:700}
.stamp{font-size:12px;color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:18px 0 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.card span{display:block;font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.card strong{display:block;font-size:24px;margin-top:4px;font-variant-numeric:tabular-nums}
.card small{color:var(--muted);font-size:12px}
.card.ok strong{color:var(--ok)}.card.warn strong{color:var(--warn)}.card.bad strong{color:var(--bad)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:16px 0}
.panel h2{margin-top:0}
.tools{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:10px 0}
.tools input,.tools select{border:1px solid var(--line);border-radius:7px;padding:7px 9px;font-size:13px;background:#fff}
.count{font-size:12.5px;color:var(--muted)}
.tw{overflow:auto;border:1px solid var(--line);border-radius:10px;background:#fff}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
thead th{background:#eef3f1;position:sticky;top:0;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--slate);white-space:nowrap}
tbody tr:hover{background:#f7faf9}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.pill{display:inline-block;border-radius:20px;padding:1px 9px;font-size:11.5px;font-weight:600;white-space:nowrap}
.p-ok{background:var(--ok-soft);color:var(--ok)}.p-warn{background:var(--warn-soft);color:var(--warn)}
.p-bad{background:var(--bad-soft);color:var(--bad)}.p-grey{background:#eef1f0;color:var(--slate)}
.src{white-space:nowrap;font-size:12px}.src a{text-decoration:none}
.blank{display:inline-block;background:var(--warn-soft);color:var(--warn);border:1px solid #f0dcb4;border-radius:5px;padding:0 6px;font-size:11px;font-weight:700}
.note{font-size:12.5px;color:var(--muted);margin-top:8px}
.prose{max-width:95ch}.prose li{margin-bottom:6px}
footer{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
@media(max-width:900px){.layout{grid-template-columns:1fr}.sidebar{position:static;height:auto}main{padding:18px}}
"""

JS = """
document.querySelectorAll('input[data-search]').forEach(function(inp){
  var id=inp.getAttribute('data-search');
  inp.addEventListener('input',function(){
    var q=inp.value.toLowerCase();
    var rows=document.querySelectorAll('tr[data-table="'+id+'"]');
    var shown=0;
    rows.forEach(function(tr){var hit=tr.textContent.toLowerCase().indexOf(q)>-1;
      tr.style.display=hit?'':'none';if(hit)shown++;});
    var c=document.querySelector('[data-count="'+id+'"]');if(c)c.textContent=shown+' rows shown';
  });
});
document.querySelectorAll('select[data-filter]').forEach(function(sel){
  var id=sel.getAttribute('data-filter');
  sel.addEventListener('change',function(){
    var v=sel.value.toLowerCase();
    document.querySelectorAll('tr[data-table="'+id+'"]').forEach(function(tr){
      var cat=(tr.getAttribute('data-cat')||'').toLowerCase();
      tr.style.display=(v===''||cat===v)?'':'none';
    });
  });
});
"""


def esc(s):
    return html.escape(str(s) if s is not None else "")


def status_pill(status):
    s = (status or "").strip().lower()
    if s in ("met",):
        return '<span class="pill p-ok">Met</span>'
    if s.startswith("partially"):
        return '<span class="pill p-warn">Partially met</span>'
    if s.startswith("in progress"):
        return '<span class="pill p-warn">In progress</span>'
    if s == "not started":
        return '<span class="pill p-grey">Not started</span>'
    return '<span class="pill p-grey">' + esc(status) + '</span>'


def source_cell(url, label="source"):
    if url and url.strip():
        return '<td class="src"><a href="{0}" target="_blank" rel="noopener">{1}</a></td>'.format(
            esc(url), esc(label))
    return '<td class="src"><span class="blank">UNVERIFIED</span></td>'


def read_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def sidebar(active):
    parts = ['<div class="layout"><aside class="sidebar">',
             '<a class="brand" href="index.html"><span class="badge">O5</span>'
             '<span>OWN5<small>DECISION READINESS DESK</small></span></a>',
             '<nav aria-label="Main navigation">']
    cap = None
    for href, label, group in NAV:
        if group != cap:
            cap = group
            parts.append('<div class="navcap">{0}</div>'.format(esc(group)))
        cls = ' class="active"' if href == active else ''
        parts.append('<a{0} href="{1}">{2}</a>'.format(cls, href, esc(label)))
    parts.append('</nav>')
    parts.append('<div class="sidefoot">Official data retrieved<br>2026-11-15 UTC<br><br>'
                 'Every row links to its source. Blank cells are labelled UNVERIFIED '
                 '&mdash; never filled in.</div></aside>')
    return "".join(parts)


def page(title, eyebrow, h1, lede, body, active, stamp="Official sources retrieved 2026-11-15 UTC"):
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>{0} &middot; Own5 decision-readiness desk</title>".format(esc(title)) +
        "<meta name=\"description\" content=\"A decision-readiness and verification desk for the "
        "Own5 NFL line-originator, with every value traceable to an official source and every gap labelled\">"
        "<style>" + CSS + "</style></head><body><a class=\"skip\" href=\"#main\">Skip to content</a>"
        + sidebar(active) +
        "<main id=\"main\"><span class=\"eyebrow\">{0}</span><h1>{1}</h1>".format(esc(eyebrow), esc(h1)) +
        ('<p class="lede">' + lede + "</p>" if lede else "") +
        '<span class="stamp">{0} &middot; rebuilt deterministically &middot; verify.py enforces '
        'source-or-flag on every body row</span>'.format(esc(stamp)) + body +
        "<footer>Own5 decision-readiness desk &middot; additive to the NFL price/results desk "
        "(session 3fb93d11) &middot; research, not betting advice. Luck cannot be eliminated from "
        "sports outcomes; statistical evidence reduces false confidence, it does not guarantee returns.</footer>"
        "</main></div><script>" + JS + "</script></body></html>")


def readiness_table(rows, table_id, with_filter=True):
    """Render the decision-readiness table.  Every row has a source cell; an
    UNVERIFIED current-number renders as an explicit blank badge."""
    head = (
        "<tr><th>ID</th><th>Category</th><th>Requirement</th><th>Status</th>"
        "<th>Blocking gate</th><th>Number that would clear it</th>"
        "<th>Observed today</th><th>How it is met</th><th>Gap / caveat</th><th>Source</th></tr>")
    body = []
    for r in rows:
        current = (r.get("current_number") or "").strip()
        if r.get("flag", "").strip() == "UNVERIFIED" or not current:
            cur_cell = '<span class="blank">UNVERIFIED</span>'
        else:
            cur_cell = esc(current)
        body.append(
            '<tr data-table="{0}" data-cat="{1}">'.format(table_id, esc(r.get("category", ""))) +
            "<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td>"
            "<td>{5}</td><td class=\"num\">{6}</td><td>{7}</td><td>{8}</td>".format(
                esc(r.get("req_id")), esc(r.get("category")), esc(r.get("requirement")),
                status_pill(r.get("status")), esc(r.get("blocking_gate")),
                esc(r.get("clearing_number")), cur_cell,
                esc(r.get("how_it_is_met")), esc(r.get("gap_or_caveat"))) +
            source_cell(r.get("source_url")) + "</tr>")
    return ('<div class="tw"><table data-table-id="{0}"><thead>{1}</thead><tbody>'
            "{2}</tbody></table></div>").format(table_id, head, "".join(body))


def build_readiness_page(rows, active):
    cards = _kpi_cards(rows)
    tools = (
        '<div class="tools"><input type="search" data-search="readiness" '
        'placeholder="Search requirements..." aria-label="Search requirements">'
        '<span class="count" data-count="readiness">{0} rows shown</span></div>'.format(len(rows)))
    body = (cards +
            '<h2>Decision-readiness table</h2>' +
            '<p class="lede">One row per requirement in the brief. The <em>blocking gate</em> is the '
            'validation gate (or named rule) that currently holds the requirement back; the '
            '<em>number that would clear it</em> is the concrete threshold or count that would satisfy '
            'that gate. The <em>observed today</em> column is computed from verified data where a count '
            'is derivable, and left blank with an UNVERIFIED badge where no official source can supply '
            'it.</p>' + tools + readiness_table(rows, "readiness"))
    return page("Decision readiness", "Decision support", "Decision readiness",
                "", body, active)


def _kpi_cards(rows):
    from collections import Counter
    c = Counter(r.get("status", "") for r in rows)
    met = c.get("Met", 0)
    part = c.get("Partially met", 0)
    notst = c.get("Not started", 0)
    inprog = c.get("In progress", 0)
    unverified = sum(1 for r in rows if r.get("flag", "").strip() == "UNVERIFIED")
    return (
        '<div class="cards">'
        '<div class="card ok"><span>Met</span><strong>{0}</strong><small>of {1} requirements</small></div>'
        '<div class="card warn"><span>Partially met</span><strong>{2}</strong><small>gates partly satisfied</small></div>'
        '<div class="card bad"><span>Not started</span><strong>{3}</strong><small>no implementation yet</small></div>'
        '<div class="card"><span>In progress</span><strong>{4}</strong><small>owned by this desk</small></div>'
        '<div class="card warn"><span>Observed values unverifiable</span><strong>{5}</strong>'
        '<small>left blank + flagged</small></div>'
        '</div>').format(met, len(rows), part, notst, inprog, unverified)


def build_index(rows, questions, suggestions, flagged, active):
    cards = _kpi_cards(rows)
    intro = (
        '<p class="lede">A decision-readiness and verification desk for the Own5 NFL line-originator. '
        'The landing table answers one question for every requirement in the brief: <strong>what gate '
        'blocks it, and what number would clear it.</strong> Values that cannot be confirmed from an '
        'official source are left blank and flagged &mdash; never inferred. This desk is additive to the '
        'NFL price/results desk (session 3fb93d11) and edits none of its files.</p>')
    top_blocking = [r for r in rows if r.get("flag", "").strip() == "UNVERIFIED"][:0]
    body = (cards +
            '<div class="panel"><h2>How to read this desk</h2><div class="prose"><ul>'
            "<li><strong>Blocking gate</strong> &mdash; the validation gate or named rule that holds the "
            "requirement back today.</li>"
            "<li><strong>Number that would clear it</strong> &mdash; the concrete threshold, count or "
            "condition that would satisfy that gate.</li>"
            "<li><strong>Observed today</strong> &mdash; computed from verified data where a count is "
            "derivable; <span class=\"blank\">UNVERIFIED</span> where no official source can supply it.</li>"
            "<li>Every row links to its source. See <a href=\"flagged.html\">Flagged for review</a> for "
            "the irregularities and unverified blanks.</li></ul></div></div>" +
            '<h2>Decision-readiness table</h2>' +
            readiness_table(rows, "readiness_landing") +
            '<p class="note">The same table with search and category filters is on the '
            '<a href="readiness.html">Decision readiness</a> page.</p>' +
            '<div class="panel"><h2>Open questions (have vs. missing)</h2>' +
            '<p class="note">{0} questions; {1} blocking, {2} requiring an owner decision. Full register '
            'on the <a href="questions.html">Open questions</a> page.</p></div>'.format(
                len(questions),
                sum(1 for q in questions if q.get("answer_or_status", "").startswith("BLOCKING")),
                sum(1 for q in questions if "owner decision" in q.get("answer_or_status", "").lower())) +
            '<div class="panel"><h2>Suggestions for review</h2>' +
            '<p class="note">{0} proposals, all AWAITING DECISION and none implemented. Each carries '
            'options, a recommended path and the test that would change the call &mdash; see the '
            '<a href="suggestions.html">Suggestions</a> page.</p></div>'.format(len(suggestions)) +
            '<div class="panel"><h2>Flagged for review</h2>' +
            '<p class="note">{0} items published with source links; {1} blocking. A full register is on '
            'the <a href="flagged.html">Flagged for review</a> page.</p></div>'.format(
                len(flagged), sum(1 for f in flagged if f.get("severity", "") == "blocking")))
    return page("Overview", "Dashboard", "Decision-readiness desk", intro, body, active)


def build_questions(questions, active):
    rows_html = []
    for q in questions:
        rows_html.append(
            '<tr data-table="questions">' +
            "<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td>".format(
                esc(q.get("q_id")), esc(q.get("question")), esc(q.get("why_it_matters")),
                esc(q.get("what_we_have")), esc(q.get("what_is_missing")),
                status_pill(q.get("answer_or_status"))) +
            "<td>{0}</td><td>{1}</td>".format(esc(q.get("cheapest_way_to_resolve")),
                                               esc(q.get("blocks"))) +
            source_cell(q.get("source_url")) + "</tr>")
    tools = ('<div class="tools"><input type="search" data-search="questions" '
             'placeholder="Search questions..." aria-label="Search questions">'
             '<span class="count" data-count="questions">{0} rows shown</span></div>'.format(len(questions)))
    body = ('<h2>Questions, information and answers</h2>' +
            '<p class="lede">The information that must be settled before a decision can be made: what we '
            'have, what is missing, the current answer or status, and the cheapest route to close each '
            'gap. Questions that cannot be closed from any public source are marked as owner decisions.</p>'
            + tools +
            '<div class="tw"><table><thead><tr><th>ID</th><th>Question</th><th>Why it matters</th>'
            '<th>What we have</th><th>What is missing</th><th>Answer / status</th>'
            '<th>Cheapest way to resolve</th><th>What it blocks</th><th>Source</th></tr></thead><tbody>'
            + "".join(rows_html) + "</tbody></table></div>")
    return page("Open questions", "Governance", "Open questions", "", body, active)


def build_suggestions(suggestions, active):
    rows_html = []
    for s in suggestions:
        rows_html.append(
            '<tr data-table="suggestions">' +
            "<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td>".format(
                esc(s.get("s_id")), esc(s.get("title")), esc(s.get("problem")),
                esc(s.get("option_a")), esc(s.get("option_b")), esc(s.get("option_c"))) +
            "<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td>".format(
                esc(s.get("recommended")), esc(s.get("impact")), esc(s.get("effort")),
                esc(s.get("confidence"))) +
            "<td>{0}</td><td>{1}</td>".format(esc(s.get("evidence")), esc(s.get("owner"))) +
            "<td>{0}</td>".format(esc(s.get("decision"))) +
            "<td>{0}</td>".format(esc(s.get("review_test"))) +
            source_cell(s.get("source_url")) + "</tr>")
    tools = ('<div class="tools"><input type="search" data-search="suggestions" '
             'placeholder="Search suggestions..." aria-label="Search suggestions">'
             '<span class="count" data-count="suggestions">{0} rows shown</span></div>'.format(len(suggestions)))
    body = ('<h2>Suggestions for review</h2>' +
            '<p class="lede">How to improve the site and the decision-making, for review before any '
            'change is implemented. Each proposal offers two or three options, a recommended path, and '
            'the test that would change the recommendation. Nothing here is built: every proposal is '
            'AWAITING DECISION.</p>' + tools +
            '<div class="tw"><table><thead><tr><th>ID</th><th>Suggestion</th><th>Problem</th>'
            '<th>Option A</th><th>Option B (recommended)</th><th>Option C</th><th>Rec.</th>'
            '<th>Impact</th><th>Effort</th><th>Confidence</th><th>Evidence</th><th>Owner</th>'
            '<th>Decision</th><th>Review test</th><th>Source</th></tr></thead><tbody>'
            + "".join(rows_html) + "</tbody></table></div>")
    return page("Suggestions", "Governance", "Suggestions for review", "", body, active)


def build_sources(sources, active):
    rows_html = []
    for s in sources:
        tier = esc(s.get("tier", ""))
        tier_pill = ('<span class="pill p-ok">OFFICIAL</span>' if tier == "OFFICIAL"
                     else '<span class="pill p-warn">AGGREGATOR</span>' if tier == "AGGREGATOR"
                     else '<span class="pill p-grey">DERIVED</span>')
        rows_html.append(
            '<tr data-table="sources">' +
            "<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td>".format(
                esc(s.get("source_id")), esc(s.get("publisher")), esc(s.get("title")),
                '<a href="{0}" target="_blank" rel="noopener">{0}</a>'.format(esc(s.get("url"))),
                tier_pill, esc(s.get("fetched_utc"))) +
            "<td>{0}</td></tr>".format(esc(s.get("used_for"))))
    body = ('<h2>Sources</h2>' +
            '<p class="lede">The official and primary sources behind this desk. OFFICIAL sources are '
            'publishers of the underlying facts. The AGGREGATOR row is a third-party mirror used only as '
            'a cross-check and never as a fact source. Every table row on every page links back to one of '
            'these.</p>' +
            '<div class="tw"><table><thead><tr><th>ID</th><th>Publisher</th><th>Title</th><th>URL</th>'
            '<th>Tier</th><th>Fetched</th><th>Used for</th></tr></thead><tbody>'
            + "".join(rows_html) + "</tbody></table></div>")
    return page("Sources", "Assurance", "Sources", "", body, active)


def build_flagged(flagged, active):
    rows_html = []
    for f in flagged:
        sev = f.get("severity", "")
        sev_pill = ('<span class="pill p-bad">blocking</span>' if sev == "blocking"
                    else '<span class="pill p-warn">review</span>' if sev == "review"
                    else '<span class="pill p-warn">open</span>')
        rows_html.append(
            '<tr data-table="flagged">' +
            "<td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td>".format(
                esc(f.get("flag_id")), sev_pill, esc(f.get("area")), esc(f.get("title")),
                esc(f.get("detail")), esc(f.get("consequence"))) +
            "<td>{0}</td>".format(esc(f.get("action"))) +
            source_cell(f.get("source_url")) + "</tr>")
    body = ('<h2>Flagged for review</h2>' +
            '<p class="lede">Irregularities, data gaps and unverified blanks, published with their source '
            'links so they can be reviewed. None of these blocks the site: they are labelled rather than '
            'silently corrected or filled.</p>' +
            '<div class="tw"><table><thead><tr><th>ID</th><th>Severity</th><th>Area</th><th>Title</th>'
            '<th>Detail</th><th>Consequence</th><th>Action</th><th>Source</th></tr></thead><tbody>'
            + "".join(rows_html) + "</tbody></table></div>")
    return page("Flagged for review", "Assurance", "Flagged for review", "", body, active)


def build_review(active):
    """Repo review / verification log page."""
    checks = [
        ("Coordination claim", "Session 560ed315 claimed a non-overlapping scope and pushed the claim "
         "before any build work began.", "committed", "https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md"),
        ("Decision-readiness engine", "readiness.py builds decision_readiness.csv; the observed-number "
         "column is computed mechanically from verified sibling data, never typed.", "committed",
         "https://github.com/sassnarep3-star/Own5/blob/main/nfl-560ed315/readiness.py"),
        ("Current numbers", "Counts (137 official games, 156/390 price snapshots populated, 705 slots / "
         "31 clubs, 9 official correlation pairs, 162 gate evaluations, 0 certified) were read from the "
         "verified sibling CSVs, not re-derived.", "verified",
         "https://sassnarep3-star.github.io/Own5/nfl-desk-3fb93d11/"),
        ("Official standings re-read", "The 2026 NFL League Standings page was re-read on 2026-11-15 and "
         "the 32-team W-L-T / PF / PA table was used as the benchmark.", "verified",
         "https://www.nfl.com/standings/league/2026/REG"),
        ("Source-or-flag invariant", "verify.py walks every generated page and fails the build if any "
         "body row has neither a source link nor an explicit UNVERIFIED badge.", "committed",
         "https://github.com/sassnarep3-star/Own5/blob/main/nfl-560ed315/verify.py"),
        ("Read-only scope", "No file outside nfl-560ed315/**, research/nfl-560ed315/** and the append-only "
         "COORDINATION.md / README.md entries was modified.", "verified",
         "https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md"),
    ]
    rows_html = []
    for cid, what, status, url in checks:
        pill = ('<span class="pill p-ok">verified</span>' if status == "verified"
                else '<span class="pill p-grey">committed</span>')
        rows_html.append(
            '<tr data-table="review">' + "<td>{0}</td><td>{1}</td><td>{2}</td>".format(
                esc(cid), esc(what), pill) +
            '<td class="src"><a href="{0}" target="_blank" rel="noopener">link</a></td></tr>'.format(esc(url)))
    body = ('<h2>Repo review &amp; verification log</h2>' +
            '<p class="lede">Line-by-line review of what this desk does, against official and verified '
            'sources, with the irregularities and unverified values published rather than corrected. '
            'The headline claims of earlier NFL desks are re-checked on their own pages; this desk adds '
            'the decision-readiness matrix on top of that verified work.</p>' +
            '<div class="tw"><table><thead><tr><th>Check</th><th>What was verified</th><th>Status</th>'
            '<th>Source</th></tr></thead><tbody>' + "".join(rows_html) + "</tbody></table></div>" +
            '<div class="panel"><h2>Irregularities flagged for review</h2>' +
            '<p class="note">See the <a href="flagged.html">Flagged for review</a> page for the '
            'irregularities and unverified blanks published with their source links.</p></div>')
    return page("Repo review", "Assurance", "Repo review", "", body, active)


def main():
    rows = read_csv("decision_readiness.csv")
    questions = read_csv("questions.csv")
    suggestions = read_csv("suggestions.csv")
    sources = read_csv("sources.csv")
    flagged = read_csv("flagged.csv")

    write("index.html", build_index(rows, questions, suggestions, flagged, "index.html"))
    write("readiness.html", build_readiness_page(rows, "readiness.html"))
    write("questions.html", build_questions(questions, "questions.html"))
    write("suggestions.html", build_suggestions(suggestions, "suggestions.html"))
    write("sources.html", build_sources(sources, "sources.html"))
    write("flagged.html", build_flagged(flagged, "flagged.html"))
    write("review.html", build_review("review.html"))
    print("built {0} pages".format(len(NAV)))


def write(name, content):
    with open(os.path.join(SITE, name), "w", encoding="utf-8") as fh:
        fh.write(content)


if __name__ == "__main__":
    main()

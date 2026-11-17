#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the Own5 NFL Decision Console static site (session c98c6270).

Deterministic: reads the CSVs written by engine.py and emits HTML. Every body
row of every table carries a provenance badge (SOURCE / COMPUTED / GOVERNANCE /
UNVERIFIED) and a resolvable link. verify.py proves that on the emitted HTML.
"""

from __future__ import annotations

import csv
import html
import json
import os
import re

import content as C  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

SESSION = C.SESSION
CAPTURE = C.CAPTURE_UTC

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def read(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def rows_of(text):
    lines = [l for l in text.strip().splitlines() if l.strip()]
    header = lines[0].split("|")
    return [dict(zip(header, l.split("|"))) for l in lines[1:]]


BADGE_HELP = {
    "SOURCE": "Value read from an official source; the link opens that page.",
    "COMPUTED": "Value computed by the deterministic engine from official inputs; "
                "the link opens the inputs.",
    "GOVERNANCE": "A rule, gate or decision, not a claim about the world; the link "
                  "opens the register that holds it.",
    "UNVERIFIED": "Value could not be confirmed from an official source. It is "
                  "published blank and flagged, never inferred.",
}

STATUS_CLASS = {
    "MET": "ok", "PARTIAL": "warn", "BLOCKED": "bad",
    "NOT MET": "bad", "withheld": "warn",
    "blocking": "bad", "non-blocking": "warn", "review": "warn",
    "PROPOSED": "warn", "APPROVED": "ok", "REJECTED": "bad", "DEFERRED": "warn",
    "PAPER": "warn", "LIVE": "ok",
    "yes": "ok", "no": "bad",
    "match": "ok", "confirmed": "ok", "resolved": "ok",
}


def badge(kind, href, label=None):
    k = kind.upper()
    return ('<a class="badge b-%s" href="%s" title="%s">%s</a>'
            % (k.lower(), esc(href), esc(BADGE_HELP.get(k, "")),
               esc(label or k)))


def ext(url):
    return url if url.startswith("http") else ""


def src_cell(url, kind="SOURCE", text="official source"):
    if url:
        return '<a href="%s">%s</a> %s' % (esc(url), esc(text), badge(kind, url))
    return badge("UNVERIFIED", "flagged.html", "no official source")


def evidence_link(ev, fallback="requirements.html"):
    """Render an evidence reference as a resolvable link plus a provenance badge.

    An evidence value is one of: an official URL, a page in this site, a CSV in
    data/, a flag id (F-nn), a source id (S-nn) or a plain governance note.
    Every one resolves to something a reviewer can open.
    """
    ev = (ev or "").strip()
    if ev.startswith("http"):
        return '<a href="%s">%s</a> %s' % (esc(ev), esc(ev), badge("SOURCE", ev))
    if ev.endswith(".html"):
        return '<a href="%s">%s</a> %s' % (esc(ev), esc(ev), badge("GOVERNANCE", ev))
    if ev.endswith((".csv", ".json", ".tsv")):
        href = ev if ev.startswith("data/") else "data/%s" % ev
        return '<a href="%s">%s</a> %s' % (esc(href), esc(ev), badge("COMPUTED", href))
    m = re.match(r"^flag (F-\d+)$", ev)
    if m:
        href = "flagged.html#%s" % m.group(1)
        return '<a href="%s">%s</a> %s' % (esc(href), esc(ev), badge("GOVERNANCE", href))
    m = re.match(r"^source (S-\d+)$", ev)
    if m:
        href = "sources.html#%s" % m.group(1)
        return '<a href="%s">%s</a> %s' % (esc(href), esc(ev), badge("SOURCE", href))
    return esc(ev) + " " + badge("GOVERNANCE", fallback)


def table(headers, rows, cls="", caption=""):
    out = ['<div class="tablewrap">']
    if caption:
        out.append('<p class="caption">%s</p>' % esc(caption))
    out.append('<table class="%s"><thead><tr>' % esc(cls))
    for h in headers:
        out.append("<th>%s</th>" % esc(h))
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def page(title, nav_key, body, subtitle="", wide=False):
    nav = NAV_ITEMS
    nav_html = "\n".join(
        '<a class="navlink%s" href="%s">%s</a>'
        % (" active" if k == nav_key else "", esc(p), esc(t))
        for k, t, p in nav)
    return PAGE_TPL % {
        "title": esc(title),
        "subtitle": esc(subtitle),
        "nav": nav_html,
        "body": body,
        "session": esc(SESSION),
        "capture": esc(CAPTURE),
        "wide": " wide" if wide else "",
    }


PAGE_TPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s · Own5 NFL Decision Console</title>
<meta name="description" content="Originate the line, prove the skill, publish the gap. Every row sourced or flagged.">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="topbar">
  <a class="brand" href="index.html"><span class="dot"></span>Own5 <em>NFL Decision Console</em></a>
  <button class="navtoggle" aria-label="Toggle navigation" onclick="document.body.classList.toggle('nav-open')">Menu</button>
  <nav class="nav" id="nav">%(nav)s</nav>
</header>
<main class="wrap%(wide)s">
  <div class="pagehead">
    <h1>%(title)s</h1>
    %(_subtitle)s
  </div>
%(body)s
</main>
<footer class="foot">
  <p><strong>Own5 NFL Decision Console</strong> · session <code>%(session)s</code> ·
  official pages captured %(capture)s · <a href="flagged.html">Flagged for Review</a> ·
  <a href="sources.html">Sources</a> · <a href="audit.html">Repo audit</a> ·
  <a href="../index.html">Own5 dashboard</a> ·
  <a href="../COORDINATION.md">Coordination log</a></p>
  <p class="fine">Research only. Nothing here is a bet, a tip, or advice. No strategy is
  certified, no reward is issued, and no market price exists anywhere in this repository.</p>
</footer>
<script src="assets/app.js"></script>
</body>
</html>
"""

NAV_ITEMS = [
    ("index", "Overview", "index.html"),
    ("summary", "Executive summary", "executive-summary.html"),
    ("suggestions", "Suggestions", "suggestions.html"),
    ("questions", "Questions", "questions.html"),
    ("requirements", "Decision readiness", "requirements.html"),
    ("lines", "Originated lines", "lines.html"),
    ("strategies", "Strategies", "strategies.html"),
    ("leaderboard", "Leaderboard", "leaderboard.html"),
    ("injuries", "Injuries", "injuries.html"),
    ("depth", "Depth charts", "depth.html"),
    ("deficiency", "Deficiency matrix", "deficiency.html"),
    ("correlations", "Correlations", "correlations.html"),
    ("luck", "Luck removal", "luck.html"),
    ("gates", "Gates", "gates.html"),
    ("audit", "Repo audit", "audit.html"),
    ("sources", "Sources", "sources.html"),
    ("flagged", "Flagged", "flagged.html"),
]

# ---------------------------------------------------------------------------
# assets
# ---------------------------------------------------------------------------

CSS = """
:root{
  --bg:#0f1115; --panel:#161a21; --panel2:#1c212a; --line:#262d38;
  --txt:#e6e9ef; --mut:#98a2b3; --acc:#4f9cf9; --ok:#2fbf71; --warn:#e0a32e; --bad:#e0604f;
  --radius:10px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);
 font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em;
 background:#0b0d11;border:1px solid var(--line);border-radius:4px;padding:1px 4px}
.topbar{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:14px;
 padding:10px 18px;background:#0c0e12;border-bottom:1px solid var(--line)}
.brand{font-weight:700;letter-spacing:.2px;color:#fff}
.brand em{font-style:normal;color:var(--mut);font-weight:500}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--acc);margin-right:8px}
.nav{display:flex;flex-wrap:wrap;gap:2px;margin-left:auto}
.navlink{padding:6px 9px;border-radius:7px;color:var(--mut);font-size:13px}
.navlink:hover{background:var(--panel);color:#fff;text-decoration:none}
.navlink.active{background:var(--panel2);color:#fff}
.navtoggle{display:none;margin-left:auto;background:var(--panel2);color:#fff;
 border:1px solid var(--line);border-radius:7px;padding:6px 10px;cursor:pointer}
.wrap{max-width:1240px;margin:0 auto;padding:22px 18px 60px}
.wrap.wide{max-width:1600px}
.pagehead{margin-bottom:18px}
.pagehead h1{margin:0 0 6px;font-size:26px;letter-spacing:-.2px}
.pagehead p{margin:0;color:var(--mut);max-width:90ch}
h2{font-size:19px;margin:26px 0 10px}
h3{font-size:15px;margin:18px 0 8px;color:#fff}
p{max-width:95ch}
.fine{color:var(--mut);font-size:12.5px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:16px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:14px}
.card .k{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.6px}
.card .v{font-size:26px;font-weight:700;margin-top:4px}
.card .n{color:var(--mut);font-size:12.5px;margin-top:4px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
 padding:16px;margin:14px 0}
.panel.warn{border-left:3px solid var(--warn)}
.panel.bad{border-left:3px solid var(--bad)}
.panel.ok{border-left:3px solid var(--ok)}
.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:var(--radius);
 background:var(--panel);margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--panel2);position:sticky;top:0;font-size:12.5px;color:var(--mut);
 text-transform:uppercase;letter-spacing:.5px;white-space:nowrap}
tbody tr:hover{background:#12161d}
td.wrapany{white-space:normal;min-width:210px}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.caption{color:var(--mut);font-size:12.5px;margin:10px 0 0}
.badge{display:inline-block;font-size:10.5px;letter-spacing:.5px;padding:2px 6px;
 border-radius:999px;border:1px solid;margin-left:6px;text-transform:uppercase;white-space:nowrap}
.badge:hover{text-decoration:none;opacity:.85}
.b-source{color:var(--ok);border-color:#255c40;background:#10281d}
.b-computed{color:var(--acc);border-color:#1f4a7a;background:#0e1c2c}
.b-governance{color:#b98cf0;border-color:#4a3271;background:#1a1226}
.b-unverified{color:var(--bad);border-color:#6d2b22;background:#25100d}
.pill{display:inline-block;font-size:11px;padding:2px 7px;border-radius:999px;
 border:1px solid var(--line);background:#0d1014;color:var(--mut)}
.pill.ok{color:#7fe0ab;border-color:#255c40}
.pill.warn{color:#f0c977;border-color:#6b5218}
.pill.bad{color:#f3a396;border-color:#6d2b22}
.filters{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0}
.filters input,.filters select{background:var(--panel2);color:var(--txt);
 border:1px solid var(--line);border-radius:7px;padding:7px 9px;font-size:13px}
.filters input{min-width:230px}
.suggestion{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
 padding:16px;margin:12px 0}
.suggestion h3{margin-top:0}
.optgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin:10px 0}
.opt{background:var(--panel2);border:1px solid var(--line);border-radius:8px;padding:10px}
.opt .t{font-size:12px;color:var(--mut);text-transform:uppercase;letter-spacing:.5px}
.decide{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:12px;
 padding-top:12px;border-top:1px dashed var(--line)}
.btn{background:var(--panel2);border:1px solid var(--line);color:var(--txt);
 border-radius:7px;padding:6px 11px;font-size:13px;cursor:pointer}
.btn:hover{border-color:var(--acc)}
.btn.on{background:#123049;border-color:#2b6ca8;color:#cfe6ff}
.tray{position:sticky;bottom:0;background:#0c0e12;border:1px solid var(--line);
 border-radius:var(--radius);padding:12px;margin-top:22px;display:none}
.tray.show{display:block}
.foot{border-top:1px solid var(--line);padding:18px;color:var(--mut);font-size:13px}
.foot a{color:var(--acc)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
ul.tight{margin:8px 0;padding-left:20px}
ul.tight li{margin:4px 0}
.kv{display:grid;grid-template-columns:170px 1fr;gap:6px 12px;font-size:13.5px}
.kv .k{color:var(--mut)}
@media (max-width:860px){
  .nav{display:none;position:absolute;top:52px;left:0;right:0;flex-direction:column;
   background:#0c0e12;border-bottom:1px solid var(--line);padding:8px}
  body.nav-open .nav{display:flex}
  .navtoggle{display:block}
  .kv{grid-template-columns:1fr}
}
"""

FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           '<rect width="64" height="64" rx="12" fill="#0f1115"/>'
           '<circle cx="32" cy="32" r="14" fill="#4f9cf9"/>'
           '<path d="M20 44 L44 20" stroke="#e6e9ef" stroke-width="4"/></svg>')

APP_JS = """
// Own5 Decision Console - client-side review tray (no backend, no tracking).
(function(){
  var KEY = 'own5-decisions-c98c6270';
  function load(){ try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch(e){ return {}; } }
  function save(d){ try { localStorage.setItem(KEY, JSON.stringify(d)); } catch(e){} }
  function refresh(){
    var d = load(), n = Object.keys(d).length, tray = document.getElementById('tray');
    if(!tray) return;
    tray.classList.toggle('show', n > 0);
    var list = document.getElementById('traylist');
    if(list){
      list.innerHTML = Object.keys(d).sort().map(function(k){
        return '<li><strong>'+k+'</strong> -> '+d[k].decision+
               ' <span class="fine">('+new Date(d[k].ts).toISOString().slice(0,10)+')</span>'+
               ' <button class="btn" data-clear="'+k+'">clear</button></li>';
      }).join('');
    }
    var c = document.getElementById('traycount'); if(c) c.textContent = n;
    document.querySelectorAll('[data-sugg]').forEach(function(box){
      var id = box.getAttribute('data-sugg'), cur = d[id] && d[id].decision;
      box.querySelectorAll('[data-dec]').forEach(function(b){
        b.classList.toggle('on', b.getAttribute('data-dec') === cur);
      });
    });
  }
  document.addEventListener('click', function(e){
    var b = e.target.closest('[data-dec]');
    if(b){
      var box = b.closest('[data-sugg]'), id = box.getAttribute('data-sugg');
      var d = load(); d[id] = {decision: b.getAttribute('data-dec'), ts: Date.now()};
      save(d); refresh(); return;
    }
    var c = e.target.closest('[data-clear]');
    if(c){ var d2 = load(); delete d2[c.getAttribute('data-clear')]; save(d2); refresh(); return; }
    if(e.target.id === 'trayexport'){
      var d3 = load(), lines = ['suggestion_id,decision,recorded_utc'];
      Object.keys(d3).sort().forEach(function(k){
        lines.push([k, d3[k].decision, new Date(d3[k].ts).toISOString()].join(','));
      });
      var blob = new Blob([lines.join('\\n')], {type:'text/csv'});
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = 'decision-log.csv'; a.click();
      return;
    }
    if(e.target.id === 'trayclear'){ save({}); refresh(); return; }
  });
  // generic table filter
  document.querySelectorAll('input[data-filter]').forEach(function(inp){
    inp.addEventListener('input', function(){
      var q = inp.value.toLowerCase(), tbl = document.querySelector(inp.getAttribute('data-filter'));
      if(!tbl) return;
      tbl.querySelectorAll('tbody tr').forEach(function(tr){
        tr.style.display = tr.textContent.toLowerCase().indexOf(q) === -1 ? 'none' : '';
      });
    });
  });
  refresh();
})();
"""


def write_assets():
    with open(os.path.join(ASSETS, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    with open(os.path.join(ASSETS, "favicon.svg"), "w", encoding="utf-8") as fh:
        fh.write(FAVICON)
    with open(os.path.join(ASSETS, "app.js"), "w", encoding="utf-8") as fh:
        fh.write(APP_JS)


def render(title, nav_key, body, subtitle="", wide=False, fname=None):
    tpl = PAGE_TPL.replace("%(_subtitle)s",
                           ("<p>%s</p>" % esc(subtitle)) if subtitle else "")
    out = tpl % {
        "title": esc(title),
        "nav": "\n".join(
            '<a class="navlink%s" href="%s">%s</a>'
            % (" active" if k == nav_key else "", esc(p), esc(t))
            for k, t, p in NAV_ITEMS),
        "body": body,
        "session": esc(SESSION),
        "capture": esc(CAPTURE),
        "wide": " wide" if wide else "",
    }
    name = fname or NAV_FILE[nav_key]
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
        fh.write(out)
    return name


NAV_FILE = {k: p for k, _, p in NAV_ITEMS}

# ---------------------------------------------------------------------------
# page builders
# ---------------------------------------------------------------------------

def build_index(rep, reqs, gates, flags, sources):
    met = sum(1 for r in reqs if r["status"] == "MET")
    part = sum(1 for r in reqs if r["status"] == "PARTIAL")
    blocked = sum(1 for r in reqs if r["status"] == "BLOCKED")
    gmet = sum(1 for g in gates if g["status"] == "MET")

    cards = [
        ("Requirements", "%d" % len(reqs),
         "%d met · %d partial · %d blocked" % (met, part, blocked)),
        ("Gates", "%d of %d met" % (gmet, len(gates)),
         "the gate that blocks each requirement is on the row itself"),
        ("Originated markets", "%d" % rep["originated_markets"],
         "13 week-11 games, 3 ordered steps, market column blank"),
        ("Market prices", "0",
         "no price exists anywhere in this repository (flag F-01)"),
        ("Clubs swept", "%d of 32" % rep["clubs_parsed"],
         "%d depth rows; Houston is image-only" % rep["depth_rows"]),
        ("Official finals", "%d" % rep["results_feed_finals"],
         "reconciles to the standings %s" % rep["standings_reconciled"]),
        ("Strategies", "%d registered · 0 certified" % rep["strategies_registered"],
         "all PAPER until gate G1 clears"),
        ("Graded bets", "0", "nothing is ranked until the gates clear"),
    ]
    body = ['<div class="cards">']
    for k, v, n in cards:
        body.append('<div class="card"><div class="k">%s</div><div class="v">%s</div>'
                    '<div class="n">%s</div></div>' % (esc(k), esc(v), esc(n)))
    body.append("</div>")

    body.append(
        '<div class="panel bad"><h3 style="margin-top:0">Read this first</h3>'
        '<p>This console answers one question: <strong>what would have to be true '
        'before any number here could justify a bet?</strong> '
        'The honest answer today is that it cannot. There is no market price '
        'anywhere in this repository, so no residual, no closing-line value and no '
        'return can be computed. Our own line is published for every game; the '
        'market column is blank and flagged. Nothing is certified, nothing is '
        'ranked, no reward is issued.</p></div>')

    body.append(
        '<div class="panel ok"><h3 style="margin-top:0">What this session added</h3>'
        '<ul class="tight">'
        '<li>A dedicated <a href="suggestions.html">Suggestions</a> section: '
        '18 reviewable paths, each with options, a recommendation and an explicit '
        '"what would change the call". Nothing is implemented without a decision, '
        'and the review tray records your choice locally.</li>'
        '<li>A <a href="questions.html">Questions</a> register: 22 questions split '
        'into what we have, what we do not have, and the cheapest route to '
        'discover each one.</li>'
        '<li>A fresh 32-club depth sweep (2026-11-17) with %d rows, a source URL '
        'and a capture date on every row, diffed against the 2026-11-15 read.</li>'
        '<li>Proof that two blocking gaps are closable: official inactives and '
        'official game books <em>are</em> published on club sites - links on the '
        '<a href="questions.html">questions page</a>.</li>'
        '</ul></div>' % rep["depth_rows"])

    body.append("<h2>Decision readiness: every requirement, the gate that blocks "
                "it, and the number that would clear it</h2>")
    body.append('<div class="filters"><input data-filter="#reqtable" '
                'placeholder="Filter requirements (try: markets, depth, blocked)">'
                '<select onchange="var t=document.getElementById(\'reqtable\');'
                'var v=this.value;t.querySelectorAll(\'tbody tr\').forEach(function(r){'
                'r.style.display=(v===\'\'||r.dataset.status===v)?\'\':\'none\'})">'
                '<option value="">all statuses</option>'
                '<option value="MET">MET</option><option value="PARTIAL">PARTIAL</option>'
                '<option value="BLOCKED">BLOCKED</option></select></div>')

    rows = []
    for r in reqs:
        rows.append([
            "<strong>%s</strong>" % esc(r["id"]),
            '<span class="pill">%s</span>' % esc(r["category"]),
            "<strong>%s</strong>" % esc(r["requirement"]),
            '<span class="pill %s">%s</span>'
            % (STATUS_CLASS.get(r["status"], ""), esc(r["status"])),
            "<code>%s</code>" % esc(r["blocking_gate"]),
            esc(r["clears_at"]),
            esc(r["observed"]),
            evidence_link(r["evidence"]),
        ])
    head = ('<div class="tablewrap"><table id="reqtable"><thead><tr>'
            + "".join("<th>%s</th>" % h for h in
                      ["ID", "Area", "Requirement", "Status", "Blocking gate",
                       "Number that would clear it", "Observed now", "Evidence"])
            + "</tr></thead><tbody>")
    trs = ['<tr data-status="%s">' % esc(r["status"])
           + "".join("<td>%s</td>" % c for c in row) + "</tr>"
           for r, row in zip(reqs, rows)]
    body.append(head + "".join(trs) + "</tbody></table></div>")

    body.append('<h2>Gates</h2>')
    grows = []
    for g in gates:
        grows.append([
            "<code>%s</code>" % esc(g["id"]),
            "<strong>%s</strong>" % esc(g["name"]),
            esc(g["threshold"]),
            esc(g["why"]),
            esc(g["measured"]),
            '<span class="pill %s">%s</span>'
            % (STATUS_CLASS.get(g["status"], ""), esc(g["status"])),
            badge("GOVERNANCE", "gates.html"),
        ])
    body.append(table(["Gate", "Name", "Threshold", "Why", "Measured", "Status",
                       "Provenance"], grows))

    blocking = [f for f in flags if f["severity"] == "blocking"]
    body.append('<h2>What is blocking (%d items)</h2>' % len(blocking))
    frows = []
    for f in flags:
        frows.append([
            "<code>%s</code>" % esc(f["id"]),
            '<span class="pill %s">%s</span>'
            % (STATUS_CLASS.get(f["severity"], ""), esc(f["severity"])),
            esc(f["area"]),
            esc(f["finding"]),
            esc(f["what_is_published_instead"]),
            badge("GOVERNANCE", "flagged.html"),
        ])
    body.append(table(["Flag", "Severity", "Area", "Finding",
                       "Published instead", "Provenance"], frows))
    return render("Overview", "index", "\n".join(body),
                  subtitle="One row per requirement, the gate that blocks it, and "
                           "the number that would clear it. Official pages captured "
                           "%s." % CAPTURE)


def build_exec_summary(rep, reqs, gates, flags, luck, corr, md, avail):
    met = sum(1 for r in reqs if r["status"] == "MET")
    part = sum(1 for r in reqs if r["status"] == "PARTIAL")
    blocked = sum(1 for r in reqs if r["status"] == "BLOCKED")
    blockers = [f for f in flags if f["severity"] == "blocking"]

    body = []
    body.append('<div class="panel"><h3 style="margin-top:0">The one-paragraph '
                'version</h3><p>We now originate our own NFL line for every game on '
                'the week-11 slate, from official league results only, and we publish '
                'it next to a blank market column. %d of %d requirements in the brief '
                'are met, %d are partial and %d are blocked. The blocking fact is '
                'simple and it is not a modelling problem: <strong>there is no market '
                'price anywhere in this repository</strong>, so no residual, no '
                'closing-line value and no return can be computed, and by our own '
                'rules no strategy may leave paper. Everything else - the %d-club '
                'depth sweep, the %d official finals, the %d originated markets, the '
                'correlations with n, the luck panel - is ready and waiting on that '
                'one missing input.</p></div>'
                % (met, len(reqs), part, blocked, rep["clubs_parsed"],
                   rep["results_feed_finals"], rep["originated_markets"]))

    body.append('<h2>Numbers that are settled</h2>')
    rows = [
        ["Week-11 games originated", str(rep["originated_markets"]) + " market rows",
         "side -> total -> moneyline, in that order, for 13 games",
         badge("COMPUTED", "lines.html")],
        ["Official finals ingested", str(rep["results_feed_finals"]),
         "reconciles to the official standings %s" % rep["standings_reconciled"],
         badge("SOURCE", "https://www.nfl.com/standings/league/2026/REG")],
        ["Measured home-field advantage", str(rep["home_field_advantage"]) + " pts",
         "negative: road sides have been marginally better in this 2026 sample "
         "(raw mean home margin -0.26 on non-neutral games, n=141)",
         badge("COMPUTED", "lines.html")],
        ["League points per team-game", str(rep["league_points_per_game"]),
         "from the official standings", badge("SOURCE",
         "https://www.nfl.com/standings/league/2026/REG")],
        ["Clubs with parsed depth", "%d of 32" % rep["clubs_parsed"],
         "%d rows; %d shared rank-1 slots; %d empty first-string slots"
         % (rep["depth_rows"], rep["shared_rank1_slots"],
            rep["empty_first_string_slots"]),
         badge("SOURCE", "https://www.seahawks.com/team/depth-chart")],
        ["Injury rows", str(rep["injury_rows"]),
         "%d re-read on 2026-11-17; no designation changed"
         % rep["injury_rows_re_read"],
         badge("SOURCE", "https://www.nfl.com/injuries/league/2026/reg10")],
        ["Matchup pairings", str(rep["matchup_pairings"]),
         "offense slot vs defense slot for the week-11 slate; 2 withheld for Houston",
         badge("COMPUTED", "deficiency.html")],
        ["Correlations published", "10 withheld 5",
         "every published value carries n and a 95% interval",
         badge("COMPUTED", "correlations.html")],
        ["Bets needed to prove a 55% edge", "2,243",
         "exact binomial, 80% power, alpha 0.05", badge("COMPUTED", "luck.html")],
        ["Strategies certified", "0 of %d" % rep["strategies_registered"],
         "all remain PAPER until gate G1 clears",
         badge("GOVERNANCE", "strategies.html")],
    ]
    body.append(table(["Item", "Value", "Basis", "Provenance"], rows))

    body.append('<h2>The %d blockers</h2>' % len(blockers))
    body.append('<ul class="tight">')
    for f in blockers:
        body.append("<li><code>%s</code> <strong>%s</strong> - %s "
                    "<em>Published instead:</em> %s</li>"
                    % (esc(f["id"]), esc(f["area"]), esc(f["finding"]),
                       esc(f["what_is_published_instead"])))
    body.append("</ul>")

    body.append('<h2>Two gaps we proved are closable</h2>')
    body.append('<div class="panel ok"><p>For two full sessions these were recorded '
                'as "no official source exists". This session found the source: club '
                'sites publish both.</p><ul class="tight">'
                '<li><strong>Official inactives</strong> - '
                '<a href="https://www.atlantafalcons.com/news/atlanta-falcons-week-10-inactives-vs-kansas-city-chiefs">'
                'Atlanta Falcons Week 10 inactives vs Kansas City Chiefs</a> '
                '<span class="badge b-source">source</span></li>'
                '<li><strong>Official game book</strong> - '
                '<a href="https://www.patriots.com/news/gamebook-patriots-vs-lions-week-10">'
                'Patriots vs Lions Week 10 game book</a> '
                '<span class="badge b-source">source</span></li>'
                '</ul><p>Neither is captured yet. Suggestions '
                '<a href="suggestions.html#S-01">S-01</a> and '
                '<a href="suggestions.html#S-02">S-02</a> propose a three-club pilot '
                'before scaling to 32.</p></div>')

    body.append('<h2>What we recommend, in order</h2>')
    body.append('<ol class="tight">'
                '<li>Decide the price policy and capture one operator '
                '(<a href="suggestions.html#S-06">S-06</a>). Nothing else matters '
                'until this is true.</li>'
                '<li>Pilot official inactives on three clubs '
                '(<a href="suggestions.html#S-01">S-01</a>).</li>'
                '<li>Automate the injury capture on the Wednesday-Friday cadence '
                '(<a href="suggestions.html#S-03">S-03</a>).</li>'
                '<li>Add parser drift alarms before automating anything '
                '(<a href="suggestions.html#S-18">S-18</a>).</li>'
                '<li>Resolve Houston with a structured source, never by transcribing '
                'the image (<a href="suggestions.html#S-04">S-04</a>).</li>'
                '</ol>')

    body.append('<h2>Limitations, stated plainly</h2>')
    body.append('<ul class="tight">'
                '<li>Clubs label their own depth charts unofficial. Depth order is a '
                'club statement, not a league one.</li>'
                '<li>Snap counts are not captured, so playing time is unmeasured and '
                'the brief\'s preferred depth signal is unavailable.</li>'
                '<li>Ratings are fitted on one season and ridge-penalised; that is '
                'necessary for identifiability and it shrinks every rating toward '
                'zero.</li>'
                '<li>The Pythagorean exponent (2.37) is a published convention, not '
                'a league value, and it is labelled as such everywhere it appears.</li>'
                '<li>Two depth reads two days apart differ on 62 of 730 like-for-like '
                'rows. A third read is needed before that is called a club-side '
                'change rather than a parser difference.</li>'
                '</ul>')
    return render("Executive summary", "summary", "\n".join(body),
                  subtitle="Only computed values or values read from an official "
                           "source appear here.")


def build_suggestions():
    sugg = rows_of(C.SUGGESTIONS_CSV)
    body = []
    body.append("""
<div class="panel ok">
<h3 style="margin-top:0">How to use this page</h3>
<p>Every suggestion below is a <strong>proposed path, not a decision and not an
implementation</strong>. Each one carries the problem it solves, two or three
options, a recommendation, and an explicit "what would change the call" so the
recommendation can be falsified rather than argued about.</p>
<p>Use the buttons on each card to record your choice. They are stored in this
browser only - there is no backend, no account and no network call - and you can
export the whole set to CSV with the button at the bottom. Nothing in this
repository changes until a decision is recorded and implemented deliberately in a
later session.</p>
<p class="fine">Decision status of every item today: <strong>PROPOSED</strong>.
Zero suggestions have been implemented in this session.</p>
</div>""")

    body.append('<div class="filters"><input data-filter="#suggwrap" '
                'placeholder="Filter suggestions (try: data, markets, competition)">'
                '</div><div id="suggwrap">')

    for s in sugg:
        body.append('<div class="suggestion" id="%s" data-sugg="%s">'
                    % (esc(s["id"]), esc(s["id"])))
        body.append('<h3>%s · %s <span class="pill">%s</span> '
                    '<span class="pill warn">%s</span></h3>'
                    % (esc(s["id"]), esc(s["title"]), esc(s["area"]),
                       esc(s["decision_status"])))
        body.append('<div class="kv">')
        body.append('<div class="k">Problem</div><div>%s</div>' % esc(s["problem"]))
        body.append('<div class="k">Recommendation</div><div><strong>%s</strong></div>'
                    % esc(s["recommendation"]))
        body.append('<div class="k">Effort</div><div>%s</div>' % esc(s["effort"]))
        body.append('<div class="k">Linked question</div><div><a href="questions.html#%s">%s</a></div>'
                    % (esc(s["linked_question"]), esc(s["linked_question"])))
        body.append('<div class="k">Evidence</div><div>%s</div>' % esc(s["evidence"]))
        body.append("</div>")
        body.append('<div class="optgrid">')
        for lab, key in (("Option A", "option_a"), ("Option B", "option_b"),
                         ("Option C", "option_c")):
            if s[key]:
                body.append('<div class="opt"><div class="t">%s</div>%s</div>'
                            % (lab, esc(s[key])))
        body.append("</div>")
        body.append('<div class="panel warn" style="margin:10px 0">'
                    '<strong>What would change the call:</strong> %s</div>'
                    % esc(s["what_would_change_the_call"]))
        body.append('<div class="decide"><strong>Record a decision:</strong>')
        for d in ("APPROVED", "REJECTED", "DEFERRED"):
            body.append('<button class="btn" data-dec="%s">%s</button>' % (d, d.title()))
        body.append('<span class="fine">stored in this browser only</span>')
        body.append(badge("GOVERNANCE", "suggestions.html#S-16"))
        body.append("</div></div>")
    body.append("</div>")

    body.append("""
<div class="tray" id="tray">
  <h3 style="margin-top:0">Decision tray (<span id="traycount">0</span> recorded)</h3>
  <ul class="tight" id="traylist"></ul>
  <button class="btn" id="trayexport">Export decision log (CSV)</button>
  <button class="btn" id="trayclear">Clear all</button>
  <p class="fine">These choices live in this browser's local storage. To make one
  permanent, paste the exported CSV into the repository as
  <code>data/decision_log.csv</code> or raise it in the coordination log.</p>
</div>""")
    return render("Suggestions", "suggestions", "\n".join(body),
                  subtitle="Reviewable paths. Nothing here is implemented until a "
                           "decision is recorded.")


def build_questions():
    qs = rows_of(C.QUESTIONS_CSV)
    blocking = sum(1 for q in qs if q["blocking"] == "yes")
    body = []
    body.append('<div class="panel"><p><strong>%d questions, %d of them '
                'blocking.</strong> For each one: what we already have, what we do '
                'not have, and the cheapest route to close the gap. A question is '
                '"blocking" if no sound decision can be taken until it is '
                'answered.</p></div>' % (len(qs), blocking))
    body.append('<div class="filters"><input data-filter="#qtable" '
                'placeholder="Filter questions (try: price, inactives, blocking)">'
                '</div>')
    rows = []
    for q in qs:
        rows.append([
            '<strong id="%s">%s</strong>' % (esc(q["id"]), esc(q["id"])),
            "<strong>%s</strong>" % esc(q["question"]),
            esc(q["what_we_have"]),
            esc(q["what_we_do_not_have"]),
            '<span class="pill %s">%s</span>'
            % ("bad" if q["blocking"] == "yes" else "", esc(q["blocking"])),
            esc(q["discovery_route"]),
            "<strong>%s</strong>" % esc(q["cheapest_first_step"]),
            '<span class="pill">%s</span>' % esc(q["cost"]),
            '<span class="pill %s">%s</span>'
            % (STATUS_CLASS.get(q["status"], ""), esc(q["status"])),
            badge("GOVERNANCE", "questions.html#" + q["id"]),
        ])
    body.append(table(["ID", "Question", "What we have", "What we do not have",
                       "Blocking", "Discovery route", "Cheapest first step",
                       "Cost", "Status", "Provenance"], rows, cls="q")
                .replace('<table class="q"', '<table id="qtable" class="q"'))
    return render("Questions", "questions", "\n".join(body),
                  subtitle="What we have, what we do not have, and the cheapest "
                           "route to find out.")


def build_requirements(reqs):
    body = []
    body.append('<div class="filters"><input data-filter="#rtable" '
                'placeholder="Filter requirements">'
                '<select onchange="var t=document.getElementById(\'rtable\');'
                'var v=this.value;t.querySelectorAll(\'tbody tr\').forEach(function(r){'
                'r.style.display=(v===\'\'||r.dataset.status===v||r.dataset.area===v)'
                '?\'\':\'none\'})"><option value="">all</option>')
    for a in sorted({r["category"] for r in reqs}):
        body.append('<option value="%s">%s</option>' % (esc(a), esc(a)))
    body.append("</select></div>")
    rows = []
    for r in reqs:
        rows.append([
            "<strong>%s</strong>" % esc(r["id"]),
            esc(r["category"]),
            "<strong>%s</strong>" % esc(r["requirement"]),
            '<span class="pill %s">%s</span>'
            % (STATUS_CLASS.get(r["status"], ""), esc(r["status"])),
            "<code>%s</code>" % esc(r["blocking_gate"]),
            esc(r["clears_at"]),
            esc(r["observed"]),
            evidence_link(r["evidence"]),
        ])
    head = ('<div class="tablewrap"><table id="rtable"><thead><tr>'
            + "".join("<th>%s</th>" % h for h in
                      ["ID", "Area", "Requirement", "Status", "Blocking gate",
                       "Clears at", "Observed", "Evidence"])
            + "</tr></thead><tbody>")
    trs = ['<tr data-status="%s" data-area="%s">' % (esc(r["status"]), esc(r["category"]))
           + "".join("<td>%s</td>" % c for c in row) + "</tr>"
           for r, row in zip(reqs, rows)]
    body.append(head + "".join(trs) + "</tbody></table></div>")
    return render("Decision readiness", "requirements", "\n".join(body),
                  subtitle="Every requirement line in the brief, with the gate that "
                           "blocks it and the number that would clear it.", wide=True)


def build_lines(markets, steps, ratings, slate, rep):
    body = []
    body.append('<div class="panel bad"><p><strong>The market column is empty on '
                'purpose.</strong> No market price exists anywhere in this '
                'repository, so no residual, no closing-line value and no return can '
                'be computed. Where a market value would sit, the cell is blank and '
                'marked UNVERIFIED rather than filled in.</p></div>')
    body.append('<div class="grid2">')
    body.append('<div class="panel"><h3>Origination order (R-03)</h3>'
                '<ol class="tight"><li><strong>Side</strong> - fitted ratings plus '
                'home-field advantage give the spread and p(home win).</li>'
                '<li><strong>Total</strong> - two estimators, published side by side '
                'with the gap, until a chronological walk-forward separates them '
                '(R-62).</li>'
                '<li><strong>Moneyline</strong> - derived from the step-1 '
                'probability only. It never feeds back into the side.</li></ol>'
                '<p class="fine">Spread sigma 13.5 is a published convention, not a '
                'league value.</p></div>')
    body.append('<div class="panel"><h3>Fitted inputs</h3><div class="kv">'
                '<div class="k">Games used</div><div>%d official finals</div>'
                '<div class="k">Home-field advantage</div><div>%s pts '
                '(negative: road sides marginally better in this sample)</div>'
                '<div class="k">Ridge penalty</div><div>1.0 pt², required for '
                'identifiability</div>'
                '<div class="k">League points per team-game</div><div>%s</div>'
                '</div></div>' % (rep["games_used_for_ratings"],
                                  rep["home_field_advantage"],
                                  rep["league_points_per_game"]))
    body.append("</div>")

    body.append("<h2>Originated markets</h2>")
    body.append('<div class="filters"><input data-filter="#mtable" '
                'placeholder="Filter by game, team or market"></div>')
    rows = []
    for m in markets:
        st = m["market_value_status"]
        rows.append([
            "<code>%s</code>" % esc(m["game_id"]),
            esc(m["market_step"]),
            esc(m["market"]),
            '<span class="num">%s</span>' % esc(m["model_value"]),
            esc(m["model_probability"]),
            ('<span class="pill bad">blank</span>' if not m["market_value"]
             else esc(m["market_value"])),
            ('<span class="pill bad">undefined</span>' if not m["difference"]
             else esc(m["difference"])),
            '<span class="fine">%s</span>' % esc(m["model_inputs"]),
            ('<a href="flagged.html">%s</a> %s'
             % (esc(st), badge("UNVERIFIED", "flagged.html"))
             if st.startswith("UNVERIFIED")
             else esc(st) + " " + badge("COMPUTED", "lines.html")),
        ])
    body.append(table(["Game", "Step", "Market", "Model", "Probability",
                       "Market", "Difference", "Model inputs", "Market status"],
                      rows, cls="m")
                .replace('<table class="m"', '<table id="mtable" class="m"'))

    body.append("<h2>Dependency chain</h2>")
    srows = [[esc(s["game_id"]), esc(s["step"]), esc(s["name"]),
              esc(s["depends_on"]) or "(none)", esc(s["what_is_computed"]),
              esc(s["value"]),
              src_cell(s["source_url"], "SOURCE", "official schedule page")]
             for s in steps]
    body.append(table(["Game", "Step", "Name", "Depends on", "What is computed",
                       "Value", "Source"], srows))

    body.append("<h2>Team ratings</h2>")
    rrows = [[esc(r["team"]), '<span class="num">%s</span>' % esc(r["rating"]),
              esc(r["games_used"]), esc(r["ridge_penalty"]),
              src_cell(r["source_url"], "SOURCE", "official standings")]
             for r in ratings]
    body.append(table(["Team", "Rating (pts vs average)", "Games used",
                       "Ridge penalty", "Source"], rrows))
    return render("Originated lines", "lines", "\n".join(body),
                  subtitle="Our own line for every week-11 game, originated "
                           "side then total then moneyline.", wide=True)


def build_strategies(strats, gates, gm, demotion, controls):
    body = []
    body.append('<div class="panel warn"><p><strong>%d families registered, %d '
                'certified.</strong> Every one is PAPER. A family leaves paper only '
                'when every gate reads MET, and gate G1 (%s) is not met: there are '
                'zero graded bets.</p></div>'
                % (len(strats), 0,
                   [g["threshold"] for g in gates if g["id"] == "G1"][0]))
    body.append('<div class="filters"><input data-filter="#stable" '
                'placeholder="Filter strategies"></div>')
    rows = []
    for s in strats:
        rows.append([
            "<strong>%s</strong>" % esc(s["id"]),
            esc(s["family"]),
            '<span class="pill">%s</span>' % esc(s["division"]),
            esc(s["frozen_definition"]),
            esc(s["registered_utc"]),
            '<span class="pill warn">%s</span>' % esc(s["status"]),
            esc(s["would_change_mind_up"]),
            esc(s["would_change_mind_down"]),
            "<code>%s</code>" % esc(s["gates_met"]),
            badge("GOVERNANCE", "strategies.html#" + s["id"]),
        ])
    body.append(table(["ID", "Family", "Division", "Frozen definition (registration)",
                       "Registered", "Status", "Would change our mind (for)",
                       "Would change our mind (against)", "Gates met",
                       "Provenance"], rows, cls="s")
                .replace('<table class="s"', '<table id="stable" class="s"'))

    body.append("<h2>Gate matrix</h2>")
    mrows = []
    for r in gm:
        mrows.append([esc(r["family"]), "<code>%s</code>" % esc(r["gate"]),
                      '<span class="pill %s">%s</span>'
                      % (STATUS_CLASS.get(r["status"], ""), esc(r["status"])),
                      esc(r["note"]), badge("GOVERNANCE", "gates.html")])
    body.append(table(["Family", "Gate", "Status", "Note", "Provenance"], mrows))

    body.append("<h2>Demotion gate</h2>")
    drows = [[esc(d["id"]), esc(d["trigger"]), esc(d["threshold"]),
              esc(d["action"]), esc(d["applies_from"]),
              badge("GOVERNANCE", "gates.html")] for d in demotion]
    body.append(table(["ID", "Trigger", "Threshold", "Action", "Applies from",
                       "Provenance"], drows))

    body.append("<h2>Controls on every leaderboard run</h2>")
    crows = [[esc(c["id"]), esc(c["name"]), esc(c["rule"]), esc(c["purpose"]),
              esc(c["source"]) + " " + badge("COMPUTED", "leaderboard.html")]
             for c in controls]
    body.append(table(["ID", "Control", "Rule", "Purpose", "Provenance"], crows))
    return render("Strategies", "strategies", "\n".join(body),
                  subtitle="Pre-registered, frozen before results, two-sided "
                           "falsification on every entry.", wide=True)


def build_leaderboard(divs, sig, stake):
    body = []
    body.append('<div class="panel warn"><p><strong>Every division is empty, and '
                'that is the correct state.</strong> Four divisions are defined and '
                'each one names the gate that blocks it. Ranking a strategy before '
                'its gate clears would publish noise, and a backtest number may never '
                'appear here at all (R-09).</p></div>')
    rows = [[esc(d["division"]), esc(d["registered_families"]),
             esc(d["graded_bets"]), esc(d["rows_ranked"]),
             esc(d["ranking_metric"]),
             '<span class="pill bad">%s</span>' % esc(d["blocking_gate"]),
             esc(d["note"]), badge("GOVERNANCE", "gates.html")] for d in divs]
    body.append(table(["Division", "Registered families", "Graded bets",
                       "Rows ranked", "Ranking metric", "Blocking gate", "Note",
                       "Provenance"], rows))

    body.append("<h2>Signal ledger (separate from staking by construction)</h2>")
    srows = [[esc(r["row"]), esc(r["division"]), esc(r["family"]) or "-",
              esc(r["graded_bets"]), esc(r["brier"]) or "-",
              esc(r["benchmark_brier"]) or "-", esc(r["brier_skill"]) or "-",
              esc(r["cluster_lower_bound"]) or "-",
              '<span class="pill warn">%s</span>' % esc(r["status"]),
              esc(r["note"]), badge("GOVERNANCE", "leaderboard.html")]
             for r in sig]
    body.append(table(["Row", "Division", "Family", "Graded bets", "Brier",
                       "Benchmark Brier", "Brier skill", "Cluster lower bound",
                       "Status", "Note", "Provenance"], srows))
    body.append("<h2>Staking ledger</h2>")
    krows = [[esc(r["row"]), esc(r["division"]), esc(r["family"]) or "-",
              esc(r["graded_bets"]), esc(r["brier"]) or "-",
              esc(r["benchmark_brier"]) or "-", esc(r["brier_skill"]) or "-",
              esc(r["cluster_lower_bound"]) or "-",
              '<span class="pill warn">%s</span>' % esc(r["status"]),
              esc(r["note"]), badge("GOVERNANCE", "leaderboard.html")]
             for r in stake]
    body.append(table(["Row", "Division", "Family", "Graded bets", "Brier",
                       "Benchmark Brier", "Brier skill", "Cluster lower bound",
                       "Status", "Note", "Provenance"], krows))
    body.append('<div class="panel"><p class="fine">The two ledgers are rendered '
                'separately so a lucky staking run can never be mistaken for a good '
                'signal (R-05). Both are graded on the same proper score.</p></div>')
    return render("Leaderboard", "leaderboard", "\n".join(body),
                  subtitle="Proper-score divisions, signal split from staking, "
                           "controls on every run.", wide=True)


def build_injuries(inj, rep):
    body = []
    body.append('<div class="panel bad"><p>%s</p></div>' % esc(C.WEEK11_INJURY_NOTE))
    body.append('<div class="panel warn"><p>The delta column is the point. A read '
                'with no earlier read to compare against is a level, and a level '
                'tells you nothing about what changed this week. Only %d of %d rows '
                'have a second read, all from the first chunk of the report '
                '(Washington, the Giants, New England and Detroit). Every other row '
                'says so.</p></div>'
                % (rep["injury_rows_re_read"], rep["injury_rows"]))
    body.append('<div class="filters"><input data-filter="#itable" '
                'placeholder="Filter by team, player or status"></div>')
    rows = []
    for r in inj:
        delta = r["delta"]
        cls = "ok" if delta.startswith("no change") else (
            "" if delta.startswith("not covered") else "bad")
        rows.append([
            esc(r["team"]), esc(r["player"]), esc(r["position"]),
            esc(r["injury"]), esc(r["practice_status"]),
            esc(r["game_status"]) or '<span class="pill">blank</span>',
            esc(r["week"]), esc(r["first_read_utc"]),
            esc(r["second_read_utc"]) or '<span class="pill warn">not re-read</span>',
            '<span class="pill %s">%s</span>' % (cls, esc(delta)),
            src_cell(r["source_url"], "SOURCE", "official injury report"),
        ])
    body.append(table(["Team", "Player", "Pos", "Injury", "Practice status",
                       "Game status", "Week", "First read (UTC)",
                       "Second read (UTC)", "Delta", "Source"], rows, cls="i")
                .replace('<table class="i"', '<table id="itable" class="i"'))
    return render("Injuries", "injuries", "\n".join(body),
                  subtitle="Official injury report, stored with its clock time and "
                           "published as a delta.", wide=True)


def build_depth(slots, delta, team_avail):
    body = []
    parsed = sum(1 for s in slots if s["club"] != "HOU")
    body.append('<div class="panel"><div class="kv">'
                '<div class="k">Clubs swept</div><div>32 of 32</div>'
                '<div class="k">Clubs parsed</div><div>31 of 32 (Houston is '
                'image-only)</div>'
                '<div class="k">Machine-readable rows</div><div>%d</div>'
                '<div class="k">Shared rank-1 slots</div><div>%d</div>'
                '<div class="k">Empty first-string slots</div><div>%d</div>'
                '<div class="k">Captured</div><div>%s</div></div></div>'
                % (parsed,
                   sum(1 for s in slots if s["shared_rank1"] == "yes"),
                   sum(1 for s in slots if s["empty_first_string"] == "yes"),
                   CAPTURE))
    body.append('<div class="panel warn"><p><strong>Two parsing notes.</strong> '
                'Green Bay prefixes every name with a jersey number; the number is '
                'stripped and the raw string is kept, but depth order is never '
                'derived from jersey numbers (rejection X-01). Houston renders the '
                'chart inside an image and is not transcribed by eye (rejection '
                'X-03).</p></div>')

    body.append("<h2>Per-club coverage</h2>")
    rows = []
    for t in team_avail:
        rows.append([
            "<strong>%s</strong>" % esc(t["club"]),
            esc(t["depth_rows"]),
            '<span class="pill %s">%s</span>'
            % ("" if t["depth_status"] == "parsed" else "bad", esc(t["depth_status"])),
            esc(t["players_out_last_official_report"]),
            esc(t["rank1_players_out"]),
            esc(t["replacements_named"]),
            esc(t["replacements_unknown"]),
            src_cell(t["source_url"], "SOURCE", "club depth chart"),
        ])
    body.append(table(["Club", "Depth rows", "Depth status", "Players out (last "
                       "official report)", "Rank-1 players out",
                       "Replacements named", "Replacements unknown", "Source"], rows))

    body.append("<h2>Depth slots</h2>")
    body.append('<div class="filters"><input data-filter="#dtable" '
                'placeholder="Filter by club, unit, position or player"></div>')
    drows = []
    for s in slots:
        if s["club"] == "HOU":
            drows.append(["<strong>HOU</strong>", "", "",
                          '<span class="pill bad">image-only</span>',
                          esc(s["note"]), "", "",
                          src_cell(s["source_url"], "SOURCE", "club depth chart")])
            continue
        drows.append([
            esc(s["club"]), esc(s["unit"]), esc(s["position"]),
            esc(s["rank1"]),
            esc(s["rank2"]) or '<span class="pill">blank</span>',
            esc(s["rank3"]) or '<span class="pill">blank</span>',
            esc(s["rank4"]) or '<span class="pill">blank</span>',
            src_cell(s["source_url"], "SOURCE", "club depth chart"),
        ])
    body.append(table(["Club", "Unit", "Position", "Rank 1", "Rank 2", "Rank 3",
                       "Rank 4", "Source"], drows, cls="d")
                .replace('<table class="d"', '<table id="dtable" class="d"'))

    body.append("<h2>Depth delta vs the 2026-11-15 read</h2>")
    body.append('<div class="panel warn"><p>Restricted to Offense and Defense so the '
                'two captures are compared like-for-like: session e46fb855 did not '
                'capture special teams, this session did (flag F-21). Of %d '
                'like-for-like rows, %d are unchanged, %d were added and %d were '
                'removed. That difference is <em>not yet</em> evidence of a club-side '
                'change - a third read is needed to rule out a parser difference '
                '(flag F-22).</p></div>'
                % (len(delta),
                   sum(1 for d in delta if d["delta"] == "unchanged"),
                   sum(1 for d in delta if d["delta"] == "added"),
                   sum(1 for d in delta if d["delta"] == "removed")))
    body.append('<div class="filters"><input data-filter="#ddtable" '
                'placeholder="Filter by club or position"></div>')
    ch = [d for d in delta if d["delta"] != "unchanged"]
    rows = [[esc(d["club"]), esc(d["unit"]), esc(d["position"]), esc(d["rank1"]),
             '<span class="pill %s">%s</span>'
             % ("" if d["delta"] == "unchanged" else "warn", esc(d["delta"])),
             esc(d["detail"]), esc(d["read_a_utc"]), esc(d["read_b_utc"]),
             src_cell(d["source_url"], "SOURCE", "club depth chart")]
            for d in ch]
    body.append(table(["Club", "Unit", "Position", "Rank 1", "Delta", "Detail",
                       "Read A (UTC)", "Read B (UTC)", "Source"], rows, cls="dd")
                .replace('<table class="dd"', '<table id="ddtable" class="dd"'))
    return render("Depth charts", "depth", "\n".join(body),
                  subtitle="Date and source on every row; shared and empty slots "
                           "preserved as published.", wide=True)


def build_deficiency(md, avail):
    body = []
    body.append('<div class="panel warn"><p><strong>What this table is.</strong> '
                'For each week-11 game, every offensive rank-1 slot is paired with '
                'the opposing defensive rank-1 slot at the position it faces. If the '
                'rank-1 player is <em>Out</em> on the last published official injury '
                'report, the next named player on the club depth chart becomes the '
                'expected starter and the "expected rank" moves to 2, 3 or 4. That is '
                'the deficiency the brief asks for.</p>'
                '<p><strong>What it is not.</strong> It is not snap-count depth '
                '(flag F-06) and it is not an official starters list (flag F-05). '
                'Clubs also label their own charts unofficial. Where either club has '
                'no machine-readable chart, the pairing is withheld rather than '
                'guessed.</p></div>')
    n_def = sum(1 for r in md if r["deficiency"] == "yes")
    n_hold = sum(1 for r in md if r["status"].startswith("withheld"))
    body.append('<div class="cards">'
                '<div class="card"><div class="k">Pairings</div><div class="v">%d</div>'
                '<div class="n">offense slot vs defense slot</div></div>'
                '<div class="card"><div class="k">Confirmed deficiency</div>'
                '<div class="v">%d</div><div class="n">expected starter below '
                'rank 1 on one side</div></div>'
                '<div class="card"><div class="k">Withheld</div><div class="v">%d</div>'
                '<div class="n">Houston publishes an image</div></div>'
                '</div>' % (len(md), n_def, n_hold))
    body.append('<div class="filters"><input data-filter="#mdtable" '
                'placeholder="Filter by game, club or position">'
                '<select onchange="var t=document.getElementById(\'mdtable\');'
                'var v=this.value;t.querySelectorAll(\'tbody tr\').forEach(function(r){'
                'r.style.display=(v===\'\'||r.dataset.def===v)?\'\':\'none\'})">'
                '<option value="">all pairings</option>'
                '<option value="yes">deficiency only</option>'
                '<option value="no">no deficiency</option></select></div>')
    rows = []
    for r in md:
        rows.append([
            "<code>%s</code>" % esc(r["game_id"]),
            esc(r["offense"]), esc(r["offense_slot"]),
            esc(r["offense_expected"]) or '<span class="pill bad">blank</span>',
            esc(r["offense_expected_rank"]),
            esc(r["defense"]), esc(r["defense_slot"]),
            esc(r["defense_expected"]) or '<span class="pill bad">blank</span>',
            esc(r["defense_expected_rank"]),
            '<span class="pill %s">%s</span>'
            % (STATUS_CLASS.get(r["deficiency"], ""), esc(r["deficiency"]) or "-"),
            esc(r["status"]),
            src_cell(r["source_url"], "SOURCE", "official schedule page"),
        ])
    head = ('<div class="tablewrap"><table id="mdtable"><thead><tr>'
            + "".join("<th>%s</th>" % h for h in
                      ["Game", "Offense", "Slot", "Expected starter", "Rank",
                       "Defense", "Slot", "Expected starter", "Rank", "Deficiency",
                       "Status", "Source"])
            + "</tr></thead><tbody>")
    trs = ['<tr data-def="%s">' % esc(r["deficiency"]) +
           "".join("<td>%s</td>" % c for c in row) + "</tr>"
           for r, row in zip(md, rows)]
    body.append(head + "".join(trs) + "</tbody></table></div>")

    body.append("<h2>Replacement depth</h2>")
    rows = [[esc(r["club"]), esc(r["player"]), esc(r["position"]),
             esc(r["depth_rank"]) or '<span class="pill">not rank 1</span>',
             esc(r["replacement_named"]) or '<span class="pill bad">blank</span>',
             esc(r["replacement_rank"]) or "-",
             esc(r["status"]),
             '<a href="%s">injury</a> ' % esc(r["source_url_injury"])
             + '<a href="%s">depth</a> ' % esc(r["source_url_depth"])
             + badge("SOURCE", r["source_url_injury"])]
            for r in avail]
    body.append(table(["Club", "Player out", "Position", "Depth rank",
                       "Replacement named", "Replacement rank", "Status",
                       "Sources"], rows))
    return render("Deficiency matrix", "deficiency", "\n".join(body),
                  subtitle="Offense slot against defense slot, 1st through 4th "
                           "string, for the week-11 slate.", wide=True)


def build_correlations(corr):
    pub = [c for c in corr if c["published"] == "yes"]
    wit = [c for c in corr if c["published"] == "withheld"]
    body = []
    body.append('<div class="panel"><p><strong>%d published, %d withheld.</strong> '
                'Every published value is computed from the official league '
                'standings only, and every one carries n and a 95%% interval. The '
                'withheld values are the ones the brief asks for but which cannot be '
                'computed from anything officially captured - each one names the '
                'missing input instead of being guessed.</p></div>' % (len(pub),
                                                                       len(wit)))
    rows = [[esc(c["pair"]), esc(c["n"]),
             '<span class="num">%s</span>' % esc(c["pearson_r"]),
             esc(c["ci95_low"]), esc(c["ci95_high"]), esc(c["note"]),
             src_cell(c["source_url"], "SOURCE" if c["source_url"] else "UNVERIFIED",
                      "official standings" if c["source_url"] else "no official source")]
            for c in pub]
    body.append(table(["Pair", "n", "Pearson r", "95% low", "95% high", "Note",
                       "Source"], rows))
    body.append("<h2>Withheld</h2>")
    rows = [[esc(c["pair"]), esc(c["note"]), esc(c["withheld_reason"]),
             badge("UNVERIFIED", "flagged.html")] for c in wit]
    body.append(table(["Pair", "Note", "Why it is withheld", "Provenance"], rows))
    return render("Correlations", "correlations", "\n".join(body),
                  subtitle="Official numbers only, n published with every value.")


def build_luck(luck, power):
    body = []
    body.append('<div class="panel"><p>Luck cannot be removed from a single game. '
                'What can be done is to measure how much of a record is not '
                'explained by performance, and to require enough bets that a skill '
                'claim survives a proper score. Both panels below are computed from '
                'the official standings and the verified results feed only.</p></div>')
    body.append("<h2>Removal-of-luck panel</h2>")
    body.append('<div class="filters"><input data-filter="#ltable" '
                'placeholder="Filter by club"></div>')
    rows = [[esc(r["team"]), esc(r["games"]), esc(r["actual_win_pct"]),
             esc(r["pythagorean_win_pct"]), esc(r["win_pct_residual"]),
             esc(r["expected_wins_minus_actual"]), esc(r["one_score_games"]),
             esc(r["one_score_wins"]), esc(r["one_score_win_pct"]) or "-",
             esc(r["points_for"]), esc(r["points_against"]),
             src_cell(r["source_url"], "SOURCE", "official standings")]
            for r in luck]
    body.append(table(["Team", "Games", "Actual win %", "Pythagorean win %",
                       "Residual", "Expected wins minus actual", "One-score games",
                       "One-score wins", "One-score win %", "PF", "PA", "Source"],
                      rows, cls="l")
                .replace('<table class="l"', '<table id="ltable" class="l"'))
    body.append('<p class="caption">The Pythagorean exponent (2.37) is a published '
                'convention, not a league value. A positive residual means the club '
                'has won more than its points suggest.</p>')

    body.append("<h2>How many bets before a record means anything</h2>")
    rows = [[esc(r["n_bets"]), esc(r["critical_hits_at_alpha_0.05"]),
             esc(r["break_even_runner_probability_of_passing"]),
             esc(r["power_at_true_55pct"]), esc(r["note"]),
             badge("COMPUTED", "luck.html")] for r in power]
    body.append(table(["Bets", "Hits needed to beat alpha 0.05",
                       "Chance a break-even bettor gets there",
                       "Power if the true rate is 55%", "Note", "Provenance"], rows))
    body.append('<div class="panel bad"><p>Read the second column: with 200 bets a '
                'break-even bettor clears the bar about one time in five. That is '
                'why gate G1 requires 300 graded prospective bets before any rank is '
                'published, and why the reward pool stays blank until then.</p></div>')
    return render("Luck removal", "luck", "\n".join(body),
                  subtitle="How much of a record is not performance, and how many "
                           "bets it takes to tell.", wide=True)


def build_gates(gates, demotion, controls, policy, layers, rejections):
    body = []
    rows = []
    for g in gates:
        rows.append(["<code>%s</code>" % esc(g["id"]),
                     "<strong>%s</strong>" % esc(g["name"]),
                     esc(g["threshold"]), esc(g["why"]), esc(g["measured"]),
                     '<span class="pill %s">%s</span>'
                     % (STATUS_CLASS.get(g["status"], ""), esc(g["status"])),
                     badge("GOVERNANCE", "gates.html#" + g["id"])])
    body.append(table(["Gate", "Name", "Threshold", "Why", "Measured", "Status",
                       "Provenance"], rows))

    body.append("<h2>Price-data policy (frozen before any backtest is published)</h2>")
    rows = [[esc(p["clause"]), esc(p["rule"]), esc(p["status"]), esc(p["reason"]),
             badge("GOVERNANCE", "gates.html")] for p in policy]
    body.append(table(["Clause", "Rule", "Status", "Reason", "Provenance"], rows))

    body.append("<h2>Data layers</h2>")
    rows = [[esc(l["layer"]), esc(l["contents"]), esc(l["where_it_lives_today"]),
             esc(l["target"]),
             '<span class="pill %s">%s</span>'
             % ("ok" if l["status"] == "done" else "bad", esc(l["status"])),
             badge("GOVERNANCE", "gates.html")] for l in layers]
    body.append(table(["Layer", "Contents", "Where it lives today", "Target",
                       "Status", "Provenance"], rows))

    body.append("<h2>Standing rejections</h2>")
    rows = [[esc(r["id"]), esc(r["rejected_shortcut"]), esc(r["reason"]),
             esc(r["recorded_utc"]),
             '<span class="pill bad">%s</span>' % esc(r["status"]),
             badge("GOVERNANCE", "gates.html#" + r["id"])] for r in rejections]
    body.append(table(["ID", "Rejected shortcut", "Reason", "Recorded", "Status",
                       "Provenance"], rows))

    body.append("<h2>Controls</h2>")
    rows = [[esc(c["id"]), esc(c["name"]), esc(c["rule"]), esc(c["purpose"]),
             badge("COMPUTED", "leaderboard.html")] for c in controls]
    body.append(table(["ID", "Control", "Rule", "Purpose", "Provenance"], rows))
    return render("Gates", "gates", "\n".join(body),
                  subtitle="Every gate, the price policy, the data layers and the "
                           "standing rejections.", wide=True)


def build_audit(audit):
    body = []
    body.append('<div class="panel"><p>Line-by-line checks of the repository against '
                'what this session could verify from official sources today. Nothing '
                'belonging to another session was changed; where a prior desk\'s data '
                'is stale or incomplete, the finding is published here and the '
                'corrected rows are published in this session\'s own scope.</p></div>')
    body.append('<div class="filters"><input data-filter="#atable" '
                'placeholder="Filter audit rows"></div>')
    rows = []
    for r in audit:
        rows.append([esc(r["check"]), esc(r["expected_or_prior_claim"]),
                     esc(r["observed_this_session"]),
                     '<span class="pill %s">%s</span>'
                     % (STATUS_CLASS.get(r["verdict"], ""), esc(r["verdict"])),
                     esc(r["note"]),
                     src_cell(r["source_url"], "SOURCE" if r["source_url"] else
                              "UNVERIFIED", "official source" if r["source_url"]
                              else "no official source")])
    body.append(table(["Check", "Expected or prior claim", "Observed this session",
                       "Verdict", "Note", "Source"], rows, cls="a")
                .replace('<table class="a"', '<table id="atable" class="a"'))
    return render("Repo audit", "audit", "\n".join(body),
                  subtitle="Line-by-line verification of the repository against "
                           "official sources.", wide=True)


def build_sources(sources, rep):
    body = []
    body.append('<div class="panel"><p>Every source below was read through the '
                'session fetcher on the date shown. Where a value could not be '
                'confirmed from an official source it is published blank and '
                'flagged; none of those blanks were filled in.</p></div>')
    rows = []
    for s in sources:
        tier = s["tier"]
        rows.append(["<code>%s</code>" % esc(s["id"]), esc(s["name"]),
                     '<a href="%s">%s</a>' % (esc(s["url"]), esc(s["url"])),
                     esc(s["captured_utc"]), esc(s["used_for"]),
                     '<span class="pill %s">%s</span>'
                     % ("" if tier == "OFFICIAL" else "warn", esc(tier)),
                     badge("SOURCE" if s["url"].startswith("http") else "GOVERNANCE",
                           s["url"] if s["url"].startswith("http") else "sources.html")])
    body.append(table(["ID", "Name", "URL", "Captured (UTC)", "Used for", "Tier",
                       "Provenance"], rows))

    body.append("<h2>Derived data files</h2>")
    files = sorted(f for f in os.listdir(DATA) if f.endswith(".csv"))
    rows = []
    for f in files:
        n = len(read(f))
        rows.append(["<code>data/%s</code>" % esc(f), str(n),
                     '<a href="data/%s">open</a>' % esc(f),
                     badge("COMPUTED", "data/%s" % f)])
    body.append(table(["File", "Rows", "Link", "Provenance"], rows))
    return render("Sources", "sources", "\n".join(body),
                  subtitle="Every source read, with what it was used for.", wide=True)


def build_flagged(flags):
    body = []
    body.append('<div class="panel"><p>Everything on this page is published rather '
                'than hidden. A blocking item means no sound decision can be taken '
                'until it is resolved. A review item means the value or the method '
                'needs a second opinion. None of these block the site; they block '
                'the conclusions.</p></div>')
    rows = []
    for f in flags:
        rows.append(["<code>%s</code>" % esc(f["id"]),
                     '<span class="pill %s">%s</span>'
                     % (STATUS_CLASS.get(f["severity"], ""), esc(f["severity"])),
                     esc(f["area"]), "<strong>%s</strong>" % esc(f["finding"]),
                     esc(f["what_is_published_instead"]), esc(f["evidence"]),
                     badge("GOVERNANCE", "flagged.html#" + f["id"])])
    body.append(table(["Flag", "Severity", "Area", "Finding",
                       "What is published instead", "Evidence", "Provenance"], rows))
    return render("Flagged for Review", "flagged", "\n".join(body),
                  subtitle="Irregularities and unverified blanks, published with "
                           "their sources.", wide=True)


# ---------------------------------------------------------------------------

def main():
    write_assets()
    rep = json.load(open(os.path.join(DATA, "build_report.json"), encoding="utf-8"))

    reqs = rows_of(C.REQUIREMENTS_CSV)
    gates = rows_of(C.GATES_CSV)
    flags = rows_of(C.FLAGS_CSV)
    sources = rows_of(C.SOURCES_CSV)
    strats = rows_of(C.STRATEGIES_CSV)
    demotion = rows_of(C.DEMOTION_CSV)
    controls = rows_of(C.CONTROLS_CSV)
    policy = rows_of(C.PRICE_POLICY_CSV)
    layers = rows_of(C.DATA_LAYERS_CSV)
    rejections = rows_of(C.REJECTIONS_CSV)

    markets = read("originated_markets.csv")
    steps = read("origination_steps.csv")
    ratings = read("team_ratings.csv")
    slate = read("slate_wk11.csv")
    corr = read("correlations.csv")
    luck = read("luck_panel.csv")
    power = read("luck_power.csv")
    inj = read("injuries.csv")
    slots = read("depth_slots.csv")
    delta = read("depth_delta.csv")
    team_avail = read("team_availability.csv")
    md = read("matchup_deficiency.csv")
    avail = read("replacement_depth.csv")
    divs = read("leaderboard_divisions.csv")
    sig = read("leaderboard_signal.csv")
    stake = read("leaderboard_staking.csv")
    gm = read("gate_matrix.csv")
    audit = read("repo_audit.csv")

    pages = [
        build_index(rep, reqs, gates, flags, sources),
        build_exec_summary(rep, reqs, gates, flags, luck, corr, md, avail),
        build_suggestions(),
        build_questions(),
        build_requirements(reqs),
        build_lines(markets, steps, ratings, slate, rep),
        build_strategies(strats, gates, gm, demotion, controls),
        build_leaderboard(divs, sig, stake),
        build_injuries(inj, rep),
        build_depth(slots, delta, team_avail),
        build_deficiency(md, avail),
        build_correlations(corr),
        build_luck(luck, power),
        build_gates(gates, demotion, controls, policy, layers, rejections),
        build_audit(audit),
        build_sources(sources, rep),
        build_flagged(flags),
    ]
    print("pages written: %d" % len(pages))
    for p in pages:
        print("  ", p)


if __name__ == "__main__":
    main()

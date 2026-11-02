#!/usr/bin/env python3
"""Build the Own5 static GitHub Pages site from data/*.csv + research/*.md.

Pages are generated; tables are rendered straight from the CSVs so the site
can never drift from the data. Blank cells render as an em-dash with an
"unverified / intentionally blank" marker. URL-ish columns become links.

Run:  python3 tools/build_site.py
"""
import csv, html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "research")

ACCESSED = "2026-11-02"
SITE = "https://sassnarep3-star.github.io/Own5/"

NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive Summary"),
    ("detail-strategies.html", "Strategies & Leaderboard"),
    ("signals.html", "Signals"),
    ("detail-validation.html", "Validation Gates"),
    ("detail-correlations.html", "Correlations"),
    ("bet-types.html", "Bet Types & Combos"),
    ("data.html", "Data & League Facts"),
    ("detail-sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"),
]

LINK_COLS = {"source_url", "url", "official_site", "nfl_profile", "input_source_url"}
STATUS_BADGE = {
    "verified": "ok", "verified (rules); strategy use pending validation": "ok",
}

def esc(s):
    return html.escape(str(s), quote=True)

def linkify(col, val):
    v = str(val).strip()
    if not v:
        return '<span class="empty" title="intentionally blank — not confirmable from an official source">—</span>'
    if col in LINK_COLS and "http" in v:
        parts = [p.strip() for p in v.split(";") if p.strip()]
        links = [f'<a href="{esc(p)}" target="_blank" rel="noopener">{esc(p)} &#8599;</a>'
                 for p in parts if p.startswith("http")]
        rest = " ".join(p for p in parts if not p.startswith("http"))
        inner = " ".join(links) + ((" " + esc(rest)) if rest else "")
        return f'<span class="src">{inner}</span>'
    return esc(v)

def badge(status):
    s = str(status).lower()
    if s.startswith("verified"):
        cls = "ok"
    elif "flagged" in s or "unverified" in s or "excluded" in s:
        cls = "warn"
    elif "pending" in s or "partial" in s or "restricted" in s:
        cls = "info"
    elif "in-repo" in s or "tier rule" in s:
        cls = "mut"
    else:
        cls = "mut"
    return f'<span class="badge {cls}">{esc(status)}</span>'

def render_table(fname):
    path = os.path.join(DATA, fname)
    rows = list(csv.reader(open(path, encoding="utf-8")))
    header, body = rows[0], rows[1:]
    tid = "tbl-" + re.sub(r"[^a-z0-9]+", "-", fname.lower())
    out = [f'<div class="table-tools"><input type="search" placeholder="Filter rows…" data-filter="{tid}">'
           f'<span class="count"></span></div>']
    out.append(f'<div class="tbl-scroll"><table class="data" id="{tid}"><thead><tr>')
    for h in header:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>")
        for h, cell in zip(header, r):
            cls = ' class="num"' if re.fullmatch(r"-?\d+(\.\d+)?", str(cell).strip()) else ""
            if h.lower() in ("status", "verification_status", "row_status", "allowed"):
                out.append(f"<td>{badge(cell)}</td>")
            else:
                out.append(f"<td{cls}>{linkify(h, cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)

# ---- minimal markdown -> html (headings, lists, bold, links, code, quotes, paragraphs)
def md2html(text):
    lines = text.split("\n")
    out, list_open, para = [], False, []
    def flush_para():
        nonlocal para
        if para:
            out.append("<p>" + " ".join(para) + "</p>")
            para = []
    def close_list():
        nonlocal list_open
        if list_open:
            out.append("</ul>")
            list_open = False
    def inline(s):
        s = esc(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1 &#8599;</a>', s)
        return s
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("<!--") and ln.strip().endswith("-->"):
            flush_para(); close_list()
            out.append(ln)  # pass through HTML comments (table markers) untouched
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", ln)
        if m:
            flush_para(); close_list()
            lvl = len(m.group(1)) + 1
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if re.match(r"^\s*-\s+", ln):
            flush_para()
            if not list_open:
                out.append('<ul class="tight">'); list_open = True
            out.append("<li>" + inline(ln.strip()[2:]) + "</li>")
            i += 1
            continue
        if re.match(r"^\s*\d+\.\s+", ln):
            flush_para(); close_list()
            out.append("<p>" + inline(ln.strip()) + "</p>")
            i += 1
            continue
        if ln.startswith("> "):
            flush_para(); close_list()
            out.append('<div class="note">' + inline(ln[2:]) + "</div>")
            i += 1
            continue
        if ln.startswith("|"):  # markdown table -> html table (consume the whole contiguous block)
            flush_para(); close_list()
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i]); i += 1
            out.append('<div class="tbl-scroll"><table class="data"><tbody>')
            for r in block:
                cells = [c.strip() for c in r.strip().strip("|").split("|")]
                if all(set(c) <= set("-: ") for c in cells):
                    continue
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
            out.append("</tbody></table></div>")
            continue
        if ln.strip() == "":
            flush_para(); close_list()
            i += 1
            continue
        para.append(inline(ln.strip()))
        i += 1
    flush_para(); close_list()
    return "\n".join(out)

TABLE_RE = re.compile(r"<!--\s*TABLE:([^>]+?)-->")

def load_md(name):
    """Convert research md to HTML, injecting CSV tables at <!-- TABLE:x --> markers."""
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        text = f.read()
    html_body = md2html(text)
    return TABLE_RE.sub(lambda m: render_table(m.group(1).strip()), html_body)

def page(title, body, active=""):
    nav_items = []
    for h, t in NAV:
        cls = ' class="active"' if h == active else ""
        nav_items.append(f'<a href="{h}"{cls}>{esc(t)}</a>')
    nav = "".join(nav_items)
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Own5</title>
<meta name="description" content="Own5 — NFL line origination & skill-based strategy lab. Fully sourced from official NFL and operator sources.">
<link rel="stylesheet" href="assets/css/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏈</text></svg>">
</head><body>
<header class="top"><div class="wrap">
  <a class="brand" href="index.html">Own5 <span>· NFL Line Originator</span></a>
  <nav class="main">{nav}</nav>
</div></header>
<main>{body}</main>
<footer><div class="wrap">
  <div><h4>Own5 — NFL Line Origination Lab</h4>
    Verified line-by-line against official sources on {ACCESSED}. Unverifiable values are blank and listed on the <a href="flagged.html">Flagged for Review</a> page. Live site: <a href="{SITE}">{SITE}</a></div>
  <div><h4>Responsible gambling</h4>
    Analytics research only. Legal age only; never wager more than you can afford to lose. 24/7 confidential help: <a href="https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/">1-800-GAMBLER (1-800-426-2537)</a>, text 800GAM — NCPG.</div>
  <div><h4>Data</h4>
    Machine-readable tables: <a href="data/">data/</a> (CSV + JSON). Every row carries its official <code>source_url</code>.</div>
</div></footer>
<script src="assets/js/site.js"></script>
</body></html>"""

def section(title, sub=""):
    s = f'<section class="page"><div class="wrap"><h2 class="sec">{esc(title)}</h2>'
    if sub:
        s += f'<p class="sub">{esc(sub)}</p>'
    return s + "</div>"

def kpi(v, l, src):
    return (f'<div class="kpi"><div class="v">{esc(v)}</div><div class="l">{esc(l)}</div>'
            f'<div class="s src">{src}</div></div>')

def src_link(url, label=None):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label or url)} &#8599;</a>'

# ---------------------------------------------------------------- read data
def read(name):
    return list(csv.DictReader(open(os.path.join(DATA, name), encoding="utf-8")))

facts = read("league-facts.csv")
standings = read("standings-2026-wk8.csv")
corr = read("correlations.csv")
flagged = read("flagged.csv")
strategies = read("strategies.csv")

def fact(fid):
    for r in facts:
        if r["fact_id"] == fid:
            return r["value"]
    return ""

# ---------------------------------------------------------------- pages from research md
pages = {
    "executive-summary.html": ("executive-summary.md", "Executive Summary"),
    "detail-strategies.html": ("strategies.md", "Strategies & Leaderboard"),
    "signals.html": ("signals.md", "Signals"),
    "detail-validation.html": ("validation-gates.md", "Validation Gates"),
    "detail-correlations.html": ("correlations.md", "Correlations"),
    "bet-types.html": ("bet-markets.md", "Bet Types & Combos"),
    "flagged.html": ("flagged.md", "Flagged for Review"),
}

for fname, (md, title) in pages.items():
    body = section(title, "All factual claims link to official sources; blanks are intentional (see flagged.html).") \
        + f'<div class="wrap"><div class="panel">{load_md(md)}</div></div>'
    html_out = page(title, body, active=fname)
    with open(os.path.join(ROOT, fname), "w", encoding="utf-8") as f:
        f.write(html_out)
    print("wrote", fname)

# ---------------------------------------------------------------- data.html (league structure + all core tables)
data_body = section("Data & League Facts", "Machine-readable mirrors: data/*.csv and data/*.json. Snapshot 2026-11-02. Full research write-up: research/league-structure.md.") + f"""<div class="wrap">
  <div class="panel"><h3>League facts</h3>{render_table("league-facts.csv")}</div>
  <div class="panel"><h3>Standings — 2026 through Week 8 <span class="src">({src_link("https://www.nfl.com/standings/")})</span></h3>{render_table("standings-2026-wk8.csv")}</div>
  <div class="panel"><h3>Week 8 results <span class="src">({src_link("https://www.nfl.com/schedules")})</span></h3>{render_table("week8-2026-results.csv")}</div>
  <div class="panel"><h3>Bye weeks 2026 <span class="src">({src_link("https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week")})</span></h3>{render_table("bye-weeks-2026.csv")}</div>
  <div class="panel"><h3>Teams & official sites <span class="src">({src_link("https://www.nfl.com/teams/")})</span></h3>{render_table("teams.csv")}</div>
</div>"""
with open(os.path.join(ROOT, "data.html"), "w", encoding="utf-8") as f:
    f.write(page("Data & League Facts", data_body, active="data.html"))
print("wrote data.html")

# ---------------------------------------------------------------- sources.html
sources_body = section("Source Registry", "27 official sources. Every data-table row references one of these via source_id + its own source_url.") \
    + f'<div class="wrap"><div class="panel">{render_table("sources.csv")}</div></div>'
with open(os.path.join(ROOT, "detail-sources.html"), "w", encoding="utf-8") as f:
    f.write(page("Sources", sources_body, active="detail-sources.html"))
print("wrote detail-sources.html")

# index.html is owned by session arena-cd43258e (CI-locked); this session does not regenerate it.

# ---------------------------------------------------------------- json mirrors + _config.yml
for fn in os.listdir(DATA):
    if fn.endswith(".csv"):
        rows = list(csv.DictReader(open(os.path.join(DATA, fn), encoding="utf-8")))
        with open(os.path.join(DATA, fn.replace(".csv", ".json")), "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=1, ensure_ascii=False)
        print("json", fn)

with open(os.path.join(ROOT, "_config.yml"), "w", encoding="utf-8") as f:
    f.write("""title: "Own5 — NFL Line Originator"
description: "Originate your own NFL lines. Fully sourced from official NFL and operator sources; unverifiable values are blank and flagged."
url: "https://sassnarep3-star.github.io/Own5"
exclude:
  - tools/
  - COORDINATION.md
  - README.md
""")
print("wrote _config.yml")
print("build_site.py done")

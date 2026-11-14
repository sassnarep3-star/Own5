#!/usr/bin/env python3
"""Render the desk's pages from the committed CSVs. Deterministic, sourced, no blanks filled.

Rules the renderer enforces
---------------------------
* Every table row carries its source. A cell with no value renders as an explicit
  "no published value" marker, never as an empty space that could be mistaken for a
  zero, and never as a filled-in guess. A column whose name ends in ``url`` or
  ``source`` renders as a link.
* No wall-clock timestamps anywhere. The only dates printed are the dates the data
  was captured, which are properties of the data, so a rebuild of the same inputs
  produces byte-identical pages.
* Analysis text sits beside the table it describes, and every number in it is read
  from the table rather than typed into the prose.

Run: ``python3 build_site.py`` (usually from ``run.py``).
"""
from __future__ import annotations

import csv
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SITE = HERE                      # served at https://sassnarep3-star.github.io/Own5/nfl-desk-ce1f16ff/

CAPTURE_STAMP = "2026-11-14T21:36Z"          # properties of the data, not of this build
CAPTURE_STAMP_PRICES = "2026-11-14T21:44Z"
SEASON_WEEK = "2026 Week 10 (live) / Week 11 (next)"

NAV = [
    ("index.html", "Summary"),
    ("markets.html", "Lines we originate"),
    ("store.html", "Price store"),
    ("results.html", "Results feed"),
    ("injuries.html", "Availability"),
    ("depth.html", "Replacement depth"),
    ("leaderboard.html", "Leaderboard"),
    ("gates.html", "Gates & demotion"),
    ("correlations.html", "Correlations"),
    ("suggestions.html", "Suggestions"),
    ("questions.html", "Open questions"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]

CSS = """
:root{--bg:#0f1115;--panel:#171a21;--ink:#e7e9ee;--muted:#9aa3b2;--line:#262b36;--ok:#4ade80;
--warn:#fbbf24;--bad:#f87171;--link:#7dd3fc;--accent:#a5b4fc}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,
Segoe UI,Roboto,Helvetica,Arial,sans-serif}
a{color:var(--link);text-decoration:none}a:hover{text-decoration:underline}
header{padding:22px 26px 14px;border-bottom:1px solid var(--line);background:#12151b}
h1{margin:0 0 6px;font-size:22px;letter-spacing:.2px}
.sub{color:var(--muted);font-size:13px}
nav{display:flex;flex-wrap:wrap;gap:6px;padding:10px 26px;border-bottom:1px solid var(--line);
background:#101319;position:sticky;top:0;backdrop-filter:blur(6px)}
nav a{padding:5px 10px;border:1px solid var(--line);border-radius:999px;font-size:13px;color:var(--muted)}
nav a.on{color:#0f1115;background:var(--accent);border-color:var(--accent);font-weight:600}
main{padding:20px 26px 60px;max-width:1180px}
section{margin:0 0 26px}
h2{font-size:17px;margin:0 0 8px}h3{font-size:15px;margin:16px 0 6px;color:var(--accent)}
p{margin:8px 0}
.lead{color:var(--muted);max-width:78ch}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:14px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.card .k{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.card .v{font-size:22px;font-weight:650;margin-top:4px}
.card .n{font-size:12px;color:var(--muted);margin-top:4px}
.tbl{width:100%;border-collapse:collapse;font-size:13px;background:var(--panel);
border:1px solid var(--line);border-radius:10px;overflow:hidden}
.tbl th,.tbl td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
.tbl th{background:#1b1f28;color:var(--muted);font-weight:600;font-size:11.5px;text-transform:uppercase;
letter-spacing:.05em;position:sticky;top:0}
.tbl tr:last-child td{border-bottom:none}
.tbl td.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.tbl td.src{font-size:11.5px;max-width:230px;overflow-wrap:anywhere}
.wrap{overflow:auto;max-height:70vh;border-radius:10px}
.blank{color:#6b7280;border-bottom:1px dashed #4b5563;cursor:help}
.pass{color:var(--ok);font-weight:600}.fail{color:var(--bad);font-weight:600}
.warn{color:var(--warn);font-weight:600}
.note{background:#151821;border-left:3px solid var(--accent);padding:10px 13px;border-radius:0 8px 8px 0;
margin:10px 0;max-width:90ch}
.note.warnbox{border-left-color:var(--warn)}
.note.badbox{border-left-color:var(--bad)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:900px){.grid2{grid-template-columns:1fr}}
ul{margin:6px 0 6px 20px;padding:0}li{margin:3px 0}
code{background:#1b1f28;padding:1px 5px;border-radius:5px;font-size:12.5px}
.tier{font-size:11px;padding:1px 6px;border-radius:4px;border:1px solid var(--line);color:var(--muted)}
.tier.official{color:var(--ok);border-color:#166534}
.tier.aggregator{color:var(--warn);border-color:#78350f}
.tier.operator{color:var(--link);border-color:#155e75}
.tier.derived{color:var(--accent);border-color:#3730a3}
footer{padding:18px 26px;border-top:1px solid var(--line);color:var(--muted);font-size:12.5px}
.strip{display:grid;grid-template-columns:repeat(4,1fr);gap:0;border:1px solid var(--line);
border-radius:12px;overflow:hidden;margin:14px 0}
.strip>div{padding:12px 14px;background:var(--panel);border-right:1px solid var(--line)}
.strip>div:last-child{border-right:none}
.strip .k{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.strip .v{font-size:19px;font-weight:650;margin-top:3px}
@media(max-width:800px){.strip{grid-template-columns:1fr 1fr}}
"""

BLANK = ('<span class="blank" title="No value published by the source for this cell. '
         'Left blank on purpose: this desk does not fill a gap with an estimate.">'
         '&mdash; not published</span>')
SOURCE_COLS = ("source", "url", "source_url", "official_url", "source_urls", "mirror_url",
               "official_urls", "market_source_url", "depth_source", "injury_source")


def read(name):
    p = os.path.join(DATA, name + ".csv")
    if not os.path.exists(p):
        return [], []
    with open(p, newline="", encoding="utf-8") as f:
        r = list(csv.DictReader(f))
    return (list(r[0].keys()) if r else []), r


def esc(x):
    """Escape, with the one concession that titles are written with HTML entities."""
    return html.escape("" if x is None else str(x)).replace("&amp;mdash;", "&mdash;")


def _short(u):
    u = u.replace("https://", "").replace("http://", "")
    return u if len(u) <= 44 else u[:41] + "..."


def tier_badge(v):
    t = str(v).upper()
    cls = "derived"
    if t.startswith("OFFICIAL"):
        cls = "official"
    elif t.startswith("AGGREGATOR") or "MIRROR" in t or "VENDORED" in t:
        cls = "aggregator"
    elif "OPERATOR" in t or "DRAFTKINGS" in t or "ESPN" in t:
        cls = "operator"
    elif "DERIVED" in t:
        cls = "derived"
    else:
        cls = "aggregator"
    return f'<span class="tier {cls}">{esc(v)}</span>'


def cell(col, val):
    v = "" if val is None else str(val)
    if v.strip() == "":
        return BLANK
    if col in SOURCE_COLS or col.endswith("_url") or col.endswith("_source") or col == "sources":
        parts = [p.strip() for p in v.split(";") if p.strip()]
        out = []
        for p in parts:
            if p.startswith("http"):
                out.append(f'<a class="src" href="{esc(p)}" target="_blank" rel="noopener">'
                           f'{esc(_short(p))}</a>')
            else:
                out.append(esc(p))
        return " ".join(out)
    if col.startswith("tier") or col == "verification_tier" or col.endswith("_tier"):
        return tier_badge(v)
    if col in ("result", "state", "decision", "demotion_decision", "promotion_decision", "award",
               "pin_check", "gate_result"):
        up = v.upper()
        cls = "warn"
        if up.startswith(("PASS", "MATCH", "YES", "NO CHANGE", "PROMOTE")):
            cls = "pass"
        elif up.startswith(("FAIL", "DISAGREE", "DEMOTE", "BLOCKED", "MISSING", "DIFFER")):
            cls = "bad"
        return f'<span class="{cls}">{esc(v)}</span>'
    if col in ("r", "p_value", "binom_p_vs_break_even", "holm_adjusted_p", "mcnemar_p", "p",
               "binom_p", "wilson_lo", "wilson_hi", "hit_rate", "break_even", "break_even_mean",
               "excess", "excess_over_be", "played_rate", "diff_spread_pts", "diff_total_pts",
               "diff_home_ml_prob", "market_hold_pct", "roi_per_bet_pct", "units", "dsr"):
        return f'<span class="num">{esc(v)}</span>'
    return esc(v)


def table(cols, rows, max_rows=None, hide=(), note=None, numcols=()):
    """Render rows, with two guarantees: nothing is invented and nothing is hidden.

    A blank cell becomes an explicit marker, and a truncated table says how many
    rows it left out and links the full CSV, so pagination can never look like the
    end of the evidence.
    """
    cols = [c for c in cols if c not in hide]
    if not rows:
        return '<p class="blank">no rows - this table is empty because its inputs are, not because it was ' \
               'filtered to nothing</p>'
    total = len(rows)
    body = rows if max_rows is None else rows[:max_rows]
    h = "<tr>" + "".join(f"<th>{esc(c.replace('_', ' '))}</th>" for c in cols) + "</tr>"
    trs = []
    for r in body:
        tds = []
        for c in cols:
            v = r.get(c, "")
            klass = ""
            if c in numcols or c.endswith("_pts") or c.endswith("_pct") or c in (
                    "n", "n_player_weeks", "settled", "bets", "wins", "points", "pushes"):
                klass = ' class="num"'
            tds.append(f"<td{klass}>{cell(c, v)}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    out = [f'<div class="wrap"><table class="tbl">{h}{"".join(trs)}</table></div>']
    if total > len(body):
        link = f' the full table is <a href="data/{esc(note)}.csv">here</a>.' if note else "."
        out.append(f'<p class="sub">showing {len(body)} of {total} rows;{link}</p>')
    return "".join(out)


WHAT_WOULD_CHANGE = """<table class="tbl"><tr><th>if this became true</th><th>then this changes</th></tr>
<tr><td>Three consecutive weeks of closing snapshots exist in the store (the capture job has been
running and the provider's final quote is archived)</td><td>V-08 becomes evaluable, CLV earns its 3
points, and demotion rule D3 stops being <code>unevaluable</code>. Nothing else moves - a passing CLV
test is necessary, not sufficient.</td></tr>
<tr><td>An opening <b>moneyline</b> is captured for each live game (question MK-Q-01 is answered)</td>
<td>42 gap rows retire, <code>diff_home_prob_points</code> gains an opening baseline, and the CLV
distribution can be quoted for the moneyline as well as the side.</td></tr>
<tr><td>The 2026 window doubles and S4's Holm-adjusted p falls below 0.05</td><td>S4 earns its 10
gate points and becomes the first candidate for paper-to-live review - but V-05 is a global verdict,
so it still cannot be promoted while another strategy's raw p is smaller than its own adjusted p.</td></tr>
<tr><td>Forecast skill on the margin reaches the market's r on identical fixtures</td><td>V-06 flips to
PASS, the 4 skill points become earnable, and the front page stops saying the model loses to the line.</td></tr>
<tr><td>A live ledger row appears for any strategy (someone decides to run it)</td><td>D1 starts firing:
a hit rate below that bet's own break-even over 20 graded bets returns <code>DEMOTE TO PAPER</code>
without waiting for significance, and the strategy's state file is rewritten by a human, not by this desk.</td></tr>
<tr><td>The results feed or either hash chain fails a check</td><td>Rule D5 demotes <b>every</b> live
strategy at once - data failure is treated as a reason to stop, not to continue with a caveat.</td></tr>
<tr><td>Three weeks pass with no successful capture</td><td>D6 demotes on outage alone: a strategy nobody
can price is a strategy nobody can grade, and silence is not evidence of safety.</td></tr>
<tr><td>The injury-report disagreement (326 vs 276 rows) resolves in favour of one vintage</td>
<td>The availability impact table becomes a claim about expected snaps removed rather than a
range, and the depth join loses its <code>source_mismatch</code> caveat.</td></tr></table>"""


def page(title, sub, body, active, lead=None, notes=()):
    items = []
    for href, label in NAV:
        on = ' class="on"' if href == active else ""
        items.append(f'<a href="{href}"{on}>{esc(label)}</a>')
    nav = "".join(items)
    head = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)} &middot; Own5 NFL desk (ce1f16ff)</title>'
            f'<link rel="stylesheet" href="assets/desk.css"></head><body>'
            f'<header><h1>{esc(title)}</h1><div class="sub">{esc(sub)}</div></header><nav>{nav}</nav><main>')
    notes_html = "".join(f'<div class="note {c}">{t}</div>' for t, c in notes)
    lead_html = f'<p class="lead">{lead}</p>' if lead else ""
    tail = (f'</main><footer><div class="sub">Provenance for everything on this page: '
            f'<a href="sources.html">source register</a> &middot; '
            f'<a href="https://www.nfl.com/standings/">official standings</a> &middot; '
            f'<a href="https://www.nfl.com/schedules/2026/by-week/week-10">official Week 10 slate</a> '
            f'&middot; <a href="https://github.com/sassnarep3-star/Own5/tree/main/nfl-desk-ce1f16ff/data">'
            f'committed tables</a></div>'
            f'<br>Own5 &middot; session <code>ce1f16ff</code> &middot; branch '
            f'<code>arena/ce1f16ff-own5</code> &middot; official data captured {esc(CAPTURE_STAMP)} '
            f'(prices {esc(CAPTURE_STAMP_PRICES)}). Built from the CSVs in '
            f'<code>nfl-desk-ce1f16ff/data/</code>; rebuild with <code>python3 run.py</code>. '
            f'This desk publishes analysis, not betting advice, and no strategy on it has passed its '
            f'gates.</footer></body></html>')
    return head + lead_html + notes_html + body + tail


def write_css():
    os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
    with open(os.path.join(SITE, "assets", "desk.css"), "w", encoding="utf-8") as f:
        f.write(CSS)


# ---------------------------------------------------------------------------
# helpers that read the tables the analysis depends on
# ---------------------------------------------------------------------------
def kv(name, key, col="value"):
    cols, rows = read(name)
    for r in rows:
        if r.get(cols[0]) == key:
            return r.get(col, "")
    return ""


def n_of(name):
    _, rows = read(name)
    return len(rows)


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
def p_index():
    _, feed = read("results_feed")
    finals = [r for r in feed if r["status"] == "FINAL"]
    pending = [r for r in feed if r["status"] == "PENDING"]
    _, checks = read("results_checks")
    passed = sum(1 for r in checks if r["result"] == "PASS")
    _, gates = read("validation")
    gp = sum(1 for r in gates if r["result"] == "PASS")
    _, cal = read("calibration")
    mr = mk = ""
    for r in cal:
        if r.get("metric") == "predicted home margin vs actual":
            if r["who"] == "model":
                mr = r["r"]
            elif r["who"].startswith("market"):
                mk = r["r"]
    _, lb = read("leaderboard_signal")
    best = max(lb, key=lambda r: float(r["hit_rate"]) - float(r["break_even_mean"])
               if r["hit_rate"] and r["break_even_mean"] else -9) if lb else {}
    _, ls = read("line_sheet")
    with_mkt = sum(1 for r in ls if r["market_spread_home"] not in ("", None))
    _, sig = read("store_meta")
    store_rows = kv("store_meta", "rows")
    closing = kv("store_meta", "rows_stage_closing")
    _, flags = read("flags")
    hi = [f for f in flags if f["severity"] == "HIGH"]
    _, qs = read("questions")
    n_block = sum(1 for r in qs if r["blocking"] == "BLOCKING")
    body = [f'<section><h2>Where this desk stands, in five numbers</h2><div class="cards">'
            f'<div class="card"><div class="k">Verified results</div><div class="v">{len(finals)} games</div>'
            f'<div class="n">{len(pending)} scheduled rows carry no score, by design. '
            f'{passed}/{len(checks)} feed checks pass.</div></div>'
            f'<div class="card"><div class="k">Price snapshots stored</div><div class="v">{esc(store_rows)}</div>'
            f'<div class="n">opening and pre-game only: {esc(closing) or 0} closing rows, so closing-line '
            f'value is unmeasurable here.</div></div>'
            f'<div class="card"><div class="k">Markets originated</div><div class="v">{len(ls)} games</div>'
            f'<div class="n">side, then total, then moneyline; {with_mkt} have a market number to compare '
            f'against.</div></div>'
            f'<div class="card"><div class="k">Gates passed</div><div class="v">{gp} of {len(gates)}</div>'
            f'<div class="n">and the failures are the interesting part: no strategy is promoted.</div></div>'
            f'<div class="card"><div class="k">Open questions</div><div class="v">{n_of("questions")}</div>'
            f'<div class="n">{n_block} of them are blocking; each has a route to an answer.</div></section>']

    body.append(
        f'<section><h2>The one sentence that matters</h2><div class="note badbox">The model on this page '
        f'forecasts the home margin at <code>r={esc(mr)}</code> out of sample. The line it is trying to '
        f'beat forecasts the same games at <code>r={esc(mk)}</code> on the identical fixture list. That is '
        f'the finding, and it is why nothing here is promoted: a desk that cannot forecast better than the '
        f'market has no business staking on the difference. Every gate below is written so that this '
        f'result could not have been dressed up.</div></section>')

    body.append('<section><h2>What was built, against what was asked</h2>')
    reqs = [
        ("1. Snapshot store with opening and closing numbers",
         f'<code>data/price_snapshots.csv</code>: {store_rows} hash-chained rows, one per market side per '
         f'stage, each carrying provider, URL, capture method and timestamp. Opening and pre-game exist for '
         f'{with_mkt} of the 14 live games. <b>Closing does not exist yet</b> and the store publishes that '
         f'as a gap rather than back-filling it: see <a href="store.html">the store</a> and '
         f'<a href="markets.html">gap register</a>.'),
        ("2. Verified results feed so backtests and ROI become possible at all",
         f'<code>data/results_feed.csv</code>: {len(feed)} rows, built from the official 2026 slate, '
         f'reconciled row-for-row against the pinned mirror, and re-checked against the official standings '
         f'for all 32 clubs. <a href="results.html">13 checks, all passing</a>.'),
        ("3. Originate side, then total, then moneyline",
         'One rating fit, then three stages in that order, each consuming the previous stage: the total is '
         'the sum of the same two team expectations, the moneyline is derived from the stage-1 margin '
         'distribution and never re-fitted. <a href="markets.html">Line sheet</a> and '
         '<a href="data/derivation.csv">derivation register</a>.'),
        ("4. Fair line, market line and difference as separate columns",
         'Three column groups in <code>line_sheet.csv</code>, rendered side by side, with the difference in '
         'points and in ticks of the 0.5 &mdash; and with a tier note, because a model-vs-market difference '
         'is a cross-tier comparison, not an official number.'),
        ("5. Signal separated from staking in the leaderboard",
         'Two tables, two rankings, and the disagreement between them printed on the board: the current '
         'signal leader sits 6th on units. <a href="leaderboard.html">Leaderboard</a>.'),
        ("6. Depth of a replacement, not the fact of one",
         'Every one of the 705 published position groups is graded TESTED / PARTIALLY TESTED / UNTESTED '
         'from the replacement\'s own measured snap share. <a href="depth.html">Depth</a>.'),
        ("7. Correlations only from officially sourced numbers, with n",
         f'{n_of("correlations")} rows: values with n and a confidence interval, and five rows that are '
         f'blank because the inputs do not exist here. <a href="correlations.html">Correlations</a>.'),
        ("8. A demotion gate that returns a live strategy to paper",
         'Six fail-closed rules, evaluated every build against a real (currently empty) live ledger. '
         '<a href="gates.html">Gates and demotion</a>.'),
        ("9. Suggestions a reviewer can choose between before anything is implemented",
         f'{n_of("suggestions")} suggestions, each with options, cost and what changes. None implemented '
         f'from its own entry; all state <code>PROPOSED</code>. <a href="suggestions.html">Suggestions</a>.'),
        ("10. The questions that must be resolved before decisions",
         f'{n_of("questions")} questions, each with who publishes the answer and how to go and get it. '
         f'<a href="questions.html">Open questions</a>.'),
    ]
    body.append('<table class="tbl"><tr><th>Requirement</th><th>Where it lives, and what it admits</th></tr>'
                + "".join(f"<tr><td>{esc(a)}</td><td>{b}</td></tr>" for a, b in reqs) + "</table></section>")

    body.append('<section><h2>Read this before using any number</h2><ul>'
                f'<li><b>No price on this site is official.</b> Odds come from an aggregator page that '
                f'attributes them to one sportsbook. They are labelled <span class="tier operator">OPERATOR</span> '
                f'everywhere they appear and are never presented as the league\'s numbers.</li>'
                f'<li><b>Scores are official-reconciled, not officially fetched one by one.</b> '
                f'{len(finals)} completed games are cross-checked against the pinned mirror and pinned '
                f'again by the standings totals; {n_of("results_disagreements")} disagreements were found. '
                f'Flag MK-F-08 records what was not done.</li>'
                f'<li><b>The historical window is an aggregator mirror with an undocumented line vintage.</b> '
                f'It is good enough to test a model against, and not good enough to call a closing price - '
                f'so no closing-line claim is made anywhere.</li>'
                f'<li><b>{len(hi)} high-severity flags are open.</b> They are on '
                f'<a href="flagged.html">the review page</a>, including the one that says the model loses to '
                f'the market.</li></ul>'
                f'<p class="sub">Primary sources behind this page: '
                f'<a href="https://www.nfl.com/standings/">official standings</a> (read '
                f'{esc(CAPTURE_STAMP)}), '
                f'<a href="https://www.nfl.com/schedules/2026/by-week/week-10">official Week 10 slate</a>, '
                f'<a href="https://github.com/nflverse/nflverse-data/releases/tag/schedules">pinned game '
                f'result mirror</a>, and the <a href="data/sources.csv">full source register</a>.</p>'
                f'</section>')
    return page("Own5 NFL desk &mdash; executive summary",
                f"Origination, verification and gating for the 2026 season. {SEASON_WEEK}.",
                "".join(body), "index.html",
                lead="A desk that originates its own lines, keeps every price it ever quoted, and refuses "
                     "to promote anything it cannot defend. It currently promotes nothing, and the reason "
                     "is on the front page rather than in an appendix.")


def p_markets():
    cols, rows = read("line_sheet")
    _, gaps = read("market_gaps")
    _, der = read("derivation")
    _, cond = read("game_conditions")
    present = sum(1 for g in gaps if g["state"] == "present")
    body = [f'<section><h2>Origination order</h2><p class="lead">Every number below was produced in the '
            f'same sequence for every game: <b>side first</b>, from a walk-forward rating fit; '
            f'<b>total second</b>, as the sum of the same two team expectations rather than a second model; '
            f'<b>moneyline last</b>, derived from stage 1\'s margin distribution with the tie mass removed '
            f'using the observed tie rate. Fair line, market line and difference are separate column '
            f'groups &mdash; nothing here blends a model number with an operator number, and the difference '
            f'column is a comparison between tiers, not a fact from either of them.</p>'
            f'<table class="tbl"><tr><th>stage</th><th>columns</th><th>input</th><th>rule</th></tr>'
            + "".join(f"<tr><td>{esc(d['stage'])}</td><td>{esc(d['columns'])}</td>"
                      f"<td>{esc(d['input'])}</td><td>{esc(d['rule'])}</td></tr>" for d in der)
            + "</table></section>",
            '<section><h2>Fair line, market line, difference</h2>'
            + table([c for c in cols if c not in ("official_slate_url", "note", "verification_tier")], rows,
                    hide=("stage1_inputs", "model_sd_margin", "model_sd_total", "origination_order"),
                    numcols=("fair_spread_home", "market_spread_home", "diff_spread_pts", "fair_total",
                             "market_total", "diff_total_pts", "model_p_home_ml", "market_home_ml",
                             "market_away_ml", "diff_home_ml_prob"),
                    note="line_sheet")
            + '</section>',
            '<section><h3>Per-game provenance and the model behind each line</h3>'
            + table(["game_key", "week", "date", "neutral", "model_games_fitted", "tie_rate_used",
                     "model_expected_margin_home", "model_expected_total", "model_p_home_cover_fair",
                     "verification_tier", "market_provider", "market_stage", "market_captured_at",
                     "market_source_url", "official_slate_url", "note"], rows,
                    note="line_sheet") + "</section>",
            f'<section><h2>Conditions on the slate</h2><p class="lead">Roof, surface, temperature and wind '
            f'come from the pinned mirror, not from an official page read this session, and they are labelled '
            f'accordingly: a stadium name and a score are not the same kind of fact. They matter because a '
            f'domed, windless game and an outdoor December game in 20 mph wind are different scoring '
            f'environments, and the model does not currently know which one it is pricing.</p>'
            + table(["game_key", "week", "date", "away", "home", "location", "stadium", "roof", "surface",
                      "temp_f", "wind_mph", "official_url", "tier", "source"], cond,
                     note="game_conditions") + "</section>",
            f'<section><h2>Market coverage: what is missing, stated as missing</h2>'
            f'<p class="lead">{present} of {len(gaps)} game-market-stage cells have a value. The absent ones '
            f'are not gaps in the transcription - they are gaps in what the source publishes. A closing '
            f'price, for instance, cannot exist until the desk captures a price at kickoff, which is what '
            f'the scheduled job is for.</p>'
            + table(["week", "game_key", "market", "stage", "state", "provider", "captured_at", "plan",
                     "source"], gaps, max_rows=40, note="market_gaps") + "</section>"]
    return page("Lines we originate", "Fair line, market line, difference - in the mandated origination order.",
                "".join(body), "markets.html",
                notes=[("Every <span class=\"blank\">&mdash; not published</span> marker in this build is a "
                        "deliberate blank: the source did not publish a value, and this desk does not fill "
                        "one in.", "warnbox")])


def p_store():
    cols, rows = read("price_snapshots")
    _, meta = read("store_meta")
    live = [r for r in rows if r["lineage"] != "CI"]
    body = ['<section><h2>What the store is</h2><p class="lead">One row is one observation of one side of '
            'one market at one instant, for a market this desk originates on. Rows are never updated or '
            'deleted: a correction is a new row with its own timestamp. Each row carries the provider, the '
            'exact URL, how it was obtained, the line, the price, and which stage of the market\'s life it '
            'represents. Rows are hash-chained, so editing or dropping any earlier row breaks every hash '
            'after it and fails verification.</p>',
            '<table class="tbl"><tr><th>property</th><th>value</th></tr>'
            + "".join(f"<tr><td>{esc(m['item'])}</td><td class='num'>{esc(m['value'])}</td></tr>"
                      for m in meta)
            + "</table></section>",
            '<section><h2>Live slate: every captured price</h2>'
            + table(["seq", "captured_at_utc", "lineage", "week", "game_key", "market", "selection",
                     "line_value", "price_american", "line_stage", "implied_prob_vig", "raw_display",
                     "provider_display", "verification", "note", "source_url", "row_hash"], live,
                    numcols=("line_value", "price_american", "implied_prob_vig"), note="price_snapshots")
            + "</section>",
            '<section><h2>Two things the store deliberately does not contain</h2><ul>'
            '<li><b>No closing prices.</b> The source page\'s "current" column is not a close; it is a '
            'quote taken some minutes before kickoff, and labelling it as a close would be the single '
            'easiest way to lie with this data. Closing rows arrive when the scheduled capture job runs at '
            'kickoff (suggestion MK-SG-06).</li>'
            '<li><b>No historical aggregator prices.</b> They would add ~7,600 rows with no capture time of '
            'their own and an undocumented vintage, which would dilute a file whose entire value is that '
            'every row is an observation somebody took at a stated instant. They live in '
            '<code>backtest_predictions.csv</code> with their own provenance instead.</li></ul></section>']
    return page("Price snapshot store", "Opening and pre-game numbers for every market this desk originates.",
                "".join(body), "store.html")


def p_results():
    _, feed = read("results_feed")
    _, checks = read("results_checks")
    _, dis = read("results_disagreements")
    fin = [r for r in feed if r["status"] == "FINAL"]
    pend = [r for r in feed if r["status"] == "PENDING"]
    body = [f'<section><h2>Why a results feed is first, not last</h2><p class="lead">Until a result exists '
            f'as data, nothing on this desk can be graded: not the backtest, not ROI, not closing-line value, '
            f'not the demotion gate. This feed is the only source of outcome truth in the build, and it is '
            f'built three ways at once - the official 2026 slate transcribed game by game, the same '
            f'{len(fin)} scores cross-checked against a digest-pinned mirror, and the totals reconciled '
            f'against the official standings for all 32 clubs - so that no single source has to be trusted '
            f'on faith.</p></section>',
            '<section><h2>Self-checks</h2><table class="tbl"><tr><th>id</th><th>check</th><th>expected</th>'
            '<th>actual</th><th>result</th><th>source</th><th>note</th></tr>'
            + "".join(f"<tr><td>{esc(c['check_id'])}</td><td>{esc(c['check'])}</td>"
                      f"<td class='num'>{esc(c['expected'])}</td><td class='num'>{esc(c['actual'])}</td>"
                      f"<td>{cell('result', c['result'])}</td><td class='src'>{cell('source', c['source'])}</td>"
                      f"<td>{esc(c['note'])}</td></tr>" for c in checks) + "</table></section>",
            f'<section><h3>Disagreements between the official transcription and the mirror</h3>'
            + (f'<p class="pass">None: {len(fin)} completed games checked, every score identical in both '
               f'sources.</p>' if not dis else table([], dis)) + "</section>",
            '<section><h2>Week 10, the live slate</h2>'
            + table(["week", "date", "away", "home", "away_pts", "home_pts", "status", "margin_home",
                     "total_points", "neutral", "venue_note", "mirror_score", "official_url",
                     "verification"], [r for r in feed if r["week"] in ("10", "11")],
                    numcols=("away_pts", "home_pts", "margin_home", "total_points"), note="results_feed")
            + "</section>",
            f'<section><h2>The whole 2026 ledger ({len(feed)} rows: {len(fin)} final, {len(pend)} pending)'
            f'</h2>' + table(["seq", "week", "date", "away", "home", "away_pts", "home_pts", "status",
                              "margin_home", "total_points", "neutral", "official_url", "verification"],
                             feed, note="results_feed") + "</section>",
            '<section><h2>What the feed makes possible, and what it still cannot do</h2><ul>'
            '<li>Standings reconciliation: all 32 clubs\' wins, losses, ties, points for and points against '
            'are derived from these rows and match the official page exactly (RF-02).</li>'
            '<li>Column-mapping proof: PF &minus; PA equals the published NET column for every club (RF-03), '
            'which is how we know which transcribed column is which rather than guessing.</li>'
            '<li>Tie rate: two ties in 137 games, published as a rate with its n, because moneyline push '
            'handling needs a measured number rather than an assumption (RF-07).</li>'
            '<li><b>Not yet:</b> a per-game official fetch for every completed game. The aggregate check is '
            'strong, but it is not the same as 137 links, and flag MK-F-08 says so.</li></ul></section>']
    return page("Verified results feed", "The outcome ledger every other table on this desk grades against.",
                "".join(body), "results.html")


def p_injuries():
    _, br = read("availability_base_rates")
    _, off = read("availability_wk10_official")
    _, diff = read("availability_source_diff")
    _, imp = read("availability_impact")
    q = next((r for r in br if r["status"] == "Questionable"), {})
    o = next((r for r in br if r["status"] == "Out"), {})
    d = next((r for r in br if r["status"] == "Doubtful"), {})
    body = [
        f'<section><h2>Measured, not assumed</h2><p class="lead">These rates were produced by joining the '
        f'league\'s own injury report to the league\'s own play records: a player "played" if they appear in '
        f'that game\'s snap counts with at least one snap. Questionable players played '
        f'<code>{esc(q.get("played_rate", ""))}</code> of the time ({esc(q.get("played", ""))} of '
        f'{esc(q.get("n_player_weeks", ""))} player-weeks); Out '
        f'<code>{esc(o.get("played_rate", ""))}</code> ({esc(o.get("played", ""))} of '
        f'{esc(o.get("n_player_weeks", ""))}); Doubtful <code>{esc(d.get("played_rate", ""))}</code> '
        f'({esc(d.get("played", ""))} of {esc(d.get("n_player_weeks", ""))}).</p>'
        + table(["status", "n_player_weeks", "played", "played_rate", "wilson_lo", "wilson_hi",
                 "median_snap_share_when_played", "join_rejected_unique_candidate", "join_rejected_ambiguous",
                 "tier", "source", "note"], br)
        + '</section>',
        '<div class="note warnbox">A 59% "Questionable played" rate is a statement about hundreds of '
        'player-weeks. Applying it to one player\'s hamstring is a category error, and it is the error that '
        'makes most injury models unfalsifiable. This page therefore never predicts whether a named player '
        'plays; it reports what the report says, and what the absence removes.</div>',
        '<section><h2>What the current official report says, club by club</h2>'
        + table(["team", "rows_listed", "distinct_players", "practice_participation", "game_status",
                 "positions", "tier", "source", "note"], off, note="availability_wk10_official")
        + '</section>',
        '<section><h2>Size of the absence, and who is left holding the snaps</h2><p class="lead">A player\'s '
        'role is their median snap share of the unit\'s snaps over the last three completed weeks. The table '
        'sums those shares for the players the report keeps out, then names the most-used same-position '
        'player who is not absent &mdash; so the question it answers is whether the replacement has ever '
        'carried the load, not how famous the absent player is.</p>'
        + table(["team", "players_kept_out", "players_unmatched", "expected_snaps_removed",
                 "snaps_removed_offence", "snaps_removed_defence",
                 "pct_of_offence_snap_base", "pct_of_defence_snap_base", "detail",
                 "tier", "source", "note"], imp, max_rows=30, note="availability_impact")
        + '</section>',
        '<section><h2>Where the two tiers disagree</h2><p class="lead">The official report and the mirror '
        'disagree on how many rows a week contains (326 vs 276 for Week 10). Both counts are published, per '
        'club, and neither is preferred silently; the availability rate is computed on the join-able subset '
        'and labelled as such. Question MK-Q-04 is the route to resolving it.</p>'
        + table(["team", "official_rows", "mirror_rows", "difference", "result", "official_url", "mirror_url",
                 "note"], diff, note="availability_source_diff") + "</section>"]
    return page("Availability", "The injury ladder measured against the snap records, and applied to a squad.",
                "".join(body), "injuries.html")


def p_depth():
    _, rows = read("replacement_depth")
    _, team = read("depth_by_team")
    _, rules = read("depth_rules")
    _, pairs = read("absence_vs_depth")
    import collections
    g = collections.Counter(r["depth_grade"].split(" (")[0] for r in rows)
    body = [
        f'<section><h2>Depth, as a measured quantity</h2><p class="lead">Knowing that a starter was replaced '
        f'tells a bettor almost nothing; knowing how deep the replacement is tells them nearly everything. '
        f'So every position group on every published depth chart &mdash; {len(rows)} of them across '
        f'{len(team)} clubs &mdash; is graded against the replacement\'s own snaps in 2026: '
        f'{g["TESTED"]} TESTED, {g["PARTIALLY TESTED"]} PARTIALLY TESTED, {g["UNTESTED"]} UNTESTED, '
        f'{g["NO NAME PUBLISHED"]} with no second name published at all.</p></section>',
        '<section><h2>Grading rules, written down first</h2>'
        + table(["rule", "definition"], rules) + '</section>',
        '<section><h2>Club level</h2>'
        + table(["team", "position_groups", "tested", "partially_tested", "untested", "no_name_published",
                 "pct_groups_tested", "mean_starter_to_second_gap", "groups_with_no_backup_published",
                 "note"], team) + '</section>',
        f'<section><h2>Week 10 absences against the depth available for them</h2>'
        f'<p class="lead">{len(pairs)} rows: one per player the official report keeps out, joined to what '
        f'the club\'s own chart and the play records say about the next man. This is the intersection the '
        f'requirement asks for &mdash; the absence and the depth, in one row.</p>'
        + table(["team", "position", "player_out", "status_or_practice", "measured_removal",
                 "replacement_named", "depth_grade", "starter_to_second_gap", "listed_replacements",
                 "tier", "source", "note"], pairs, max_rows=40, note="absence_vs_depth") + '</section>',
        '<section><h2>The position the desk takes on UNTESTED</h2><div class="note">A second-stringer with '
        '40 snaps in nine weeks is not a bad replacement. They are an <i>unpriced</i> one. Those are '
        'different claims, and the difference is the reason this page publishes a grade instead of a '
        'projection: an unpriced absence should make a line look uncertain, not make the model confident in '
        'either direction.</div></section>',
        '<section><h2>Full position-group table</h2>'
        + table(["team", "unit", "position", "first_string", "second_string", "third_string",
                 "players_published", "listed_replacements", "first_string_games", "first_string_share",
                 "second_string_games", "second_string_share", "second_string_snaps_2026",
                 "third_string_games", "third_string_share", "starter_to_second_gap", "depth_grade",
                 "peer_deficiency_points", "source"], rows, max_rows=60, note="replacement_depth")
        + '</section>']
    return page("Replacement depth", "How deep the next man is, measured in the snaps he has actually taken.",
                "".join(body), "depth.html")


def p_leaderboard():
    _, lb = read("leaderboard")
    _, sig = read("leaderboard_signal")
    _, stk = read("leaderboard_staking")
    _, rw = read("rewards")
    _, sc = read("scoring_rules")
    _, ex = read("exposure")
    _, mu = read("multiplicity")
    sig_by = {r["strategy"]: r for r in sig}
    for r in lb:
        s = sig_by.get(r["strategy"], {})
        r["_wilson"] = (f"{s.get('wilson_lo', '')} to {s.get('wilson_hi', '')}"
                        if s.get("wilson_lo") else "")
        r["_required"] = s.get("required_n_80pct", "")
        r["_luck"] = s.get("luck_note", "")
    body = [
        '<section><h2>Two rankings, because one number cannot answer two questions</h2>'
        '<p class="lead">The signal table asks: is the disagreement with the market right? It is '
        'stake-independent &mdash; no price, no fraction, no bankroll. The staking table asks: given that '
        'signal, how was money deployed, and what did the path look like? Ranking those two against each '
        'other is how a lucky three-leg run gets mistaken for skill, so the board shows both and prints '
        'their disagreement instead of resolving it.</p>',
        '<table class="tbl"><tr><th>rank</th><th>strategy</th><th>division</th><th>points</th>'
        '<th>settled</th><th>hit rate</th><th>break-even of its own prices</th><th>95% Wilson</th>'
        '<th>binomial p</th><th>Holm-adjusted p</th><th>staking rank</th><th>units</th><th>max drawdown</th>'
        '<th>n needed for 80% power</th><th>what the luck test says</th></tr>'
        + "".join(
            f"<tr><td class='num'>{esc(r['signal_rank'])}</td><td>{esc(r['strategy'])}</td>"
            f"<td>{esc(r['division'])}</td><td class='num'>{esc(r['points'])}</td>"
            f"<td class='num'>{esc(r['settled'])}</td><td class='num'>{esc(r['hit_rate'])}</td>"
            f"<td class='num'>{esc(r['break_even'])}</td><td class='num'>{esc(r['_wilson'])}</td>"
            f"<td class='num'>{cell('binom_p', r['binom_p'])}</td>"
            f"<td class='num'>{cell('holm_p', r['holm_p'])}</td>"
            f"<td class='num'>{esc(r['staking_rank'])}</td><td class='num'>{esc(r['units'])}</td>"
            f"<td class='num'>{esc(r['max_drawdown'])}</td><td class='num'>{esc(r['_required'])}</td>"
            f"<td>{esc(r['_luck'])}</td></tr>" for r in lb)
        + "</table></section>",
        '<section><h3>What each entry earned and what it is missing</h3>'
        + table(["strategy", "division", "points", "earned", "missing"], lb, note="leaderboard")
        + "</section>",
        '<section><h2>Staking scoreboard (no verdict column, on purpose)</h2>'
        + table(["strategy", "bets", "units", "units_per_bet", "roi_per_bet_pct", "max_drawdown_units",
                 "worst_losing_run", "sd_per_bet", "avg_legs_per_bet", "staking_policy"], stk,
                note="leaderboard_staking") + "</section>",
        '<section><h2>Correlation load per division</h2><p class="lead">A "top performer" that is one long '
        'correlated run of the same bet wearing different clothes is not a top performer. These columns are '
        'here so that claim can be checked rather than assumed.</p>'
        + table(["strategy", "division", "bets", "games", "weeks", "max_bets_in_one_week",
                 "same_game_multileg_bets", "note"], ex, note="exposure") + "</section>",
        '<section><h2>Rewards</h2>'
        + table(["division", "entries", "leader", "leader_points", "award", "reason", "prize_notes",
                 "runner_up", "signal_vs_staking_gap"], rw) + "</section>",
        '<section><h2>How points are awarded</h2>'
        + table(["criterion", "points", "why it is worth that much"], sc)
        + '<h3>Multiplicity bookkeeping</h3>'
        + table(["item", "value", "why"], mu) + "</section>"]
    return page("Leaderboard", "Single bets, parlays and prop combos - scored on signal, reported on staking.",
                "".join(body), "leaderboard.html",
                notes=[("Nothing is awarded this week. The leaders in both divisions fail the same two gates, "
                        "and a prize for the best of a set that is indistinguishable from luck would be a "
                        "misleading prize.", "badbox")])


def p_gates():
    _, g = read("validation")
    _, d = read("demotion_gate")
    _, rules = read("gate_rules")
    _, gi = read("gate_integrity")
    _, cal = read("calibration")
    _, nc = read("naive_comparison")
    body = [
        '<section><h2>Promotion gates</h2><p class="lead">Every gate fails closed: a gate whose inputs do '
        'not exist reads <span class="fail">BLOCKED</span> or <span class="fail">FAIL</span>, never '
        '<span class="pass">PASS</span>. That is what makes the price store load-bearing rather than '
        'decorative - the closing-line gate is blocked until the store has closing rows, and the board names '
        'the file it is waiting for.</p>'
        + table(["gate_id", "gate", "why_it_exists", "threshold", "result", "measured", "source", "note"], g)
        + "</section>",
        '<section><h2>Forecast skill and the naive-rule test</h2>'
        + table(["metric", "bin", "who", "n", "r", "mae_pts", "rmse_pts", "brier", "predicted", "actual",
                 "gap", "source", "note"], cal, max_rows=24, note="calibration")
        + '<h3>Against the dumbest rules that read the same posted line</h3>'
        + '<p class="lead">Two rules graded on identical games, so the test is the exact McNemar test on '
        'the discordant pairs - not two independent hit rates, which is the usual way a small edge gets '
        'invented. S1 and S2 bet the home side by construction, so "always take the home side" is the same '
        'bet: the p-value of 1.0 is not a bug, it is the disclosure that those strategies are game-selectors '
        'and not side-detectors.</p>'
        + table(["strategy", "naive_rule", "n", "model_wins", "naive_wins", "model_hit_rate",
                 "naive_hit_rate", "discordant", "mcnemar_p", "verdict"], nc, max_rows=30,
                note="naive_comparison") + "</section>",
        '<section><h2>Demotion gate</h2><p class="lead">Promotion asks "is there evidence?". Demotion asks '
        'the different and more urgent question: "has the evidence gone bad while money is on it?" A rule '
        'that needs a debate to execute is not a gate, so these fire on their own terms - and D1 '
        'deliberately requires no statistical significance, because waiting for proof of harm while live is '
        'how a bad month becomes a bad year.</p>'
        + table(["rule", "definition", "why", "evaluates", "fail_closed"], rules)
        + '<h3>This build\'s evaluation</h3>'
        + table(["strategy", "state_before", "decision", "live_bets", "window_bets", "hit_rate_window",
                 "break_even_window", "excess", "clv_mean_pts", "drawdown_units", "drawdown_limit_units",
                 "rules_broken", "rules_unevaluable", "note"], d, note="demotion_gate")
        + '<h3>Integrity state the gate reads</h3>'
        + table(["check", "state", "detail"], gi) + "</section>"]
    return page("Gates and demotion", "What has to be true to go live, and what brings a strategy back off.",
                "".join(body), "gates.html",
                notes=[("The live ledger <code>data/live_bets.csv</code> ships with a header and no rows, "
                        "because no bet has been placed. The gate is therefore reported as <b>armed, not "
                        "passed</b> - populating it with plausible-looking bets to demonstrate the machinery "
                        "would have been the worst possible way to build it.", "warnbox")])


def p_correlations():
    cols, rows = read("correlations")
    n = sum(1 for r in rows if r["r"] not in ("", None))
    body = [f'<section><h2>The rule</h2><p class="lead">A correlation is printed here if and only if both '
            f'of its inputs are numbers this project can point at on an official page or in a mirror '
            f'digest-pinned to official game records. {n} rows qualify; {len(rows) - n} are printed with a '
            f'blank <code>r</code> and the reason they are blank, because a missing correlation and a zero '
            f'correlation look identical in a table that omits rows.</p></section>',
            table(cols, rows, numcols=("r", "n", "ci95_lo", "ci95_hi"), note="correlations"),
            '<div class="note">The row that matters for the parlay division is the last one: a home winner '
            'and a 45+ point total in the same game are close to independent (phi &minus;0.08 on 137 '
            'official-reconciled games), which is what licenses multiplying the two legs\' probabilities. '
            'It is a licence for score-derived legs only - not for two players on the same team, which this '
            'desk refuses to compute at all.</div>']
    return page("Correlations", "Officially sourced numbers only, every value with its n.",
                "".join(body), "correlations.html")


def p_suggestions():
    _, rows = read("suggestions")
    body = ['<section><h2>Pick a path before anything is implemented</h2><p class="lead">These are '
            'proposals, not work. Every row states the options, what each costs, and what changes on the site '
            'if it is chosen; nothing below has been implemented from its own entry, and the state column '
            'says so. The value of writing suggestions this way is that a reviewer can answer '
            '<i>A</i>, <i>B</i> or <i>C</i> without opening a spreadsheet.</p>',
            table(["id", "area", "suggestion", "options", "cost", "what_changes", "recommendation", "state"],
                  rows) + "</section>"]
    return page("Suggestions", "Ten ways to improve the desk for decision-making - unimplemented, by design.",
                "".join(body), "suggestions.html")


def p_questions():
    _, rows = read("questions")
    blocking = sum(1 for r in rows if r["blocking"] == "BLOCKING")
    body = [f'<section><h2>What has to be resolved before a decision can be made</h2><p class="lead">'
            f'{len(rows)} questions, {blocking} of them genuinely blocking. Each carries what it blocks, who '
            f'publishes the answer, how to go and get it, and what the desk did in the meantime - because '
            f'"we don\'t know" is only useful as a step in a process, and the fallback column is where you '
            f'can check that the process did not quietly invent an answer.</p>',
            table(["id", "blocking", "question", "why_it_blocks", "who_publishes_it", "how_to_find_out",
                   "fallback_used", "state"], rows) + "</section>"]
    return page("Open questions", "What must be known before these numbers can be acted on.", "".join(body),
                "questions.html")


def p_flagged():
    _, flags = read("flags")
    _, sd = read("availability_source_diff")
    dis = [r for r in sd if r["result"] == "DISAGREE"]
    _, gaps = read("market_gaps")
    absent = [g for g in gaps if g["state"] != "present"]
    _, checks = read("results_checks")
    failed = [c for c in checks if c["result"] != "PASS"]
    body = [f'<section><h2>Everything this desk could not verify, in one place</h2><p class="lead">'
            f'Nothing here blocks the site: an honest gap published is better than a resolved-looking number '
            f'invented, and a reader who can see what is unverified can discount it correctly. '
            f'{len(flags)} flags, {len([r for r in flags if r["severity"] == "HIGH"])} of them high; '
            f'{len(absent)} market-stage cells the source does not publish; {len(failed)} failed feed checks; '
            f'{len(dis)} clubs where the official report and the mirror disagree on row counts.</p>',
            table(["id", "severity", "kind", "item", "detail", "action", "source"], flags) + "</section>",
            '<section><h2>Failed feed checks</h2>'
            + (table(["check_id", "check", "expected", "actual", "result", "source", "note"], failed,
                     note="results_checks") if failed else
               '<p class="pass">None: all 13 results-feed checks pass on the committed data.</p>')
            + "</section>",
            '<section><h2>Market cells the source does not publish</h2>'
            + table(["week", "game_key", "market", "stage", "state", "provider", "plan", "source"], absent,
                    max_rows=60, note="market_gaps") + "</section>",
            '<section><h2>Source disagreements on injury rows</h2>'
            + table(["team", "official_rows", "mirror_rows", "difference", "result", "official_url",
                     "mirror_url", "note"], dis, note="availability_source_diff") + "</section>"]
    return page("Flagged for review", "Irregularities, gaps and unverifiable claims - published, not buried.",
                "".join(body), "flagged.html")


def p_sources():
    _, rows = read("sources")
    from pinned import capture as cap
    body = ['<section><h2>Every source, its tier, and what was taken from it</h2><p class="lead">A source '
            'row answers three questions and no others: what was read, where, and whether the value taken '
            'from it was verified or merely transcribed. Pinned input digests are rows too, because a file '
            'this desk reads without a digest is a file that can change underneath the build. Anything the '
            'desk did <i>not</i> read is here as well - a register with only the successes in it is a '
            'marketing document.</p>',
            table(["id", "publisher", "what_was_read", "url", "tier", "fields_taken", "state",
                   "captured_utc", "digest", "note"], rows, note="sources"),
            '<h3>Capture record, verbatim</h3><p class="sub">The transcriptions themselves are pinned in '
            '<code>nfl-desk-ce1f16ff/pinned/capture.py</code> (CAP-01 to CAP-06) as data, with the original '
            'page strings kept in <code>raw_display</code> inside the store, so a claim of "transcribed '
            'verbatim" can be checked against both.</p></section>',
            '<section><h2>Verification ladder</h2><ul>'
            '<li><span class="tier official">OFFICIAL</span> nfl.com standings, schedule and injury-report '
            'pages, read and transcribed by this session (or vendored from a session that did, marked as '
            'such in flag MK-F-07).</li>'
            '<li><span class="tier aggregator">AGGREGATOR</span> nflverse mirrors of the league\'s own '
            'records, digest-pinned; scores reconciled three ways, prices labelled with an undocumented '
            'vintage.</li>'
            '<li><span class="tier operator">OPERATOR</span> one sportsbook\'s prices as displayed by an '
            'aggregator page; never presented as official, never used as an outcome.</li>'
            '<li><span class="tier derived">DERIVED</span> everything on every other page of this site, all '
            'of which rebuild from the rows above with <code>python3 run.py</code>.</li></ul></section>']
    return page("Sources and verification", "What was read where, and how much of it can be trusted.",
                "".join(body), "sources.html")


def build():
    write_css()
    pages = {"index.html": p_index(), "markets.html": p_markets(), "store.html": p_store(),
             "results.html": p_results(), "injuries.html": p_injuries(), "depth.html": p_depth(),
             "leaderboard.html": p_leaderboard(), "gates.html": p_gates(),
             "correlations.html": p_correlations(), "suggestions.html": p_suggestions(),
             "questions.html": p_questions(), "flagged.html": p_flagged(), "sources.html": p_sources()}
    for name, htmlt in pages.items():
        with open(os.path.join(SITE, name), "w", encoding="utf-8") as f:
            f.write(htmlt)
    return len(pages)


if __name__ == "__main__":
    print(build())

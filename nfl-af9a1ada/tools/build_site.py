#!/usr/bin/env python3
"""Static site generator for the line-gate desk. Stdlib only, no JS required.

Every page is a table. Every table has a source column or a BLANK tag. A blank
cell renders as the literal word BLANK with a title attribute giving the reason,
never as a zero, a dash, or an empty cell that looks like data.
"""
from __future__ import annotations

import csv
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DESK = os.path.dirname(HERE)
DATA = os.path.join(DESK, "data")
OUT = DESK
TITLE = "NFL Line-Gate Desk"
TAG = "af9a1ada"

CSS = """
:root{--bg:#0f1319;--card:#171d26;--line:#25303d;--ink:#e8eef6;--dim:#8ea0b6;
--acc:#5ad2a4;--warn:#e6b455;--bad:#e8735f;--mono:ui-monospace,SFMono-Regular,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{border-bottom:1px solid var(--line);background:#0b0f14;padding:14px 22px;position:sticky;top:0;z-index:9}
header h1{margin:0;font-size:17px;letter-spacing:.3px}
header .sub{color:var(--dim);font-size:12px;margin-top:3px}
nav{display:flex;flex-wrap:wrap;gap:2px;padding:8px 22px;background:#0b0f14;border-bottom:1px solid var(--line);position:sticky;top:60px;z-index:8}
nav a{color:var(--dim);text-decoration:none;font-size:12.5px;padding:5px 9px;border-radius:5px}
nav a:hover{background:#1d2530;color:var(--ink)}
nav a.on{background:var(--acc);color:#08110c;font-weight:600}
main{padding:22px;max-width:1500px;margin:0 auto}
h2{font-size:20px;margin:26px 0 6px}h2:first-child{margin-top:0}
h3{font-size:14.5px;margin:22px 0 8px;color:var(--acc);text-transform:uppercase;letter-spacing:.7px}
p.lede{color:var(--dim);max-width:80ch;margin:0 0 16px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:13px}
.card .k{color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:.6px}
.card .v{font:600 22px/1.2 var(--mono);margin-top:5px}
.card .n{color:var(--dim);font-size:11.5px;margin-top:4px}
.v.good{color:var(--acc)}.v.warn{color:var(--warn)}.v.bad{color:var(--bad)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
border-radius:9px;overflow:hidden;margin:10px 0 22px;font-size:13px}
th{background:#131a23;text-align:left;padding:9px 10px;font-size:11px;text-transform:uppercase;
letter-spacing:.6px;color:var(--dim);border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:8px 10px;border-bottom:1px solid #1e2833;vertical-align:top}
tr:last-child td{border-bottom:none}
tbody tr:hover{background:#1b2431}
td.n,th.n{text-align:right;font-family:var(--mono);white-space:nowrap}
.blank{color:var(--warn);font-family:var(--mono);font-size:11.5px;border:1px dashed #4a3c1e;
background:#241e10;border-radius:3px;padding:1px 5px;cursor:help}
a{color:#7fd4ff;text-decoration:none;border-bottom:1px dotted #2c4a5c}
a:hover{color:#b9e9ff}
.pill{display:inline-block;padding:2px 7px;border-radius:99px;font-size:10.5px;font-weight:700;
letter-spacing:.5px;text-transform:uppercase}
.p-met{background:#153a2b;color:#6ee7b0}.p-partial{background:#3a3115;color:#e6b455}
.p-blocked{background:#3a1b18;color:#f0937f}.p-rejected{background:#2a2f38;color:var(--dim)}
.pos{color:var(--acc)}.neg{color:var(--bad)}
.note{background:#131a23;border-left:3px solid var(--acc);padding:11px 14px;border-radius:0 7px 7px 0;
margin:14px 0;font-size:13.5px;color:#cfe0f0}
.note.warn{border-left-color:var(--warn)}
.note.bad{border-left-color:var(--bad)}
footer{border-top:1px solid var(--line);padding:18px 22px;color:var(--dim);font-size:11.5px;margin-top:30px}
code{font-family:var(--mono);font-size:12px;background:#101720;padding:1px 5px;border-radius:3px}
"""

NAV = [("index.html", "Dashboard"), ("origination.html", "Origination"), ("prices.html", "Prices"),
       ("ratings.html", "Ratings"), ("results.html", "Benchmark"), ("leaderboard.html", "Leaderboard"),
       ("availability.html", "Availability"), ("deficiency.html", "Deficiency"),
       ("requirements.html", "Requirements"), ("questions.html", "Questions"),
       ("suggestions.html", "Suggestions"), ("flagged.html", "Flagged for Review"),
       ("research.html", "Method"), ("sources.html", "Sources")]


def read(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def jread(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def esc(v):
    return html.escape(str(v if v is not None else ""))


def cell(v, reason="no value was read for this cell"):
    v = ("" if v is None else str(v)).strip()
    if v == "":
        return f'<span class="blank" title="{esc(reason)}">BLANK</span>'
    return esc(v)


def num(v, nd=2, good=None):
    """A number, or BLANK. `good` in {+1,-1} colours it by sign."""
    try:
        f = float(str(v).replace("+", ""))
    except (TypeError, ValueError):
        return cell(v)
    cls = ""
    if good == 1:
        cls = "pos" if f > 0 else ("neg" if f < 0 else "")
    elif good == -1:
        cls = "neg" if f > 0 else ("pos" if f < 0 else "")
    elif good == 0:
        cls = "neg" if abs(f) > 0.05 else ("pos" if f < -0.05 else "")
    return f'<span class="{cls}">{f:.{nd}f}</span>'


def table(cols, rows, blank_reasons=None, cls=None):
    """cols: list of (key, label, kind) where kind in 'text','num','src','pill','math'."""
    out = [f'<table class="{cls or ""}"><thead><tr>']
    for _, label, kind in cols:
        out.append(f'<th class="{"n" if kind in ("num","math") else ""}">{esc(label)}</th>')
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for key, _, kind in cols:
            v = r.get(key, "")
            if kind == "num":
                out.append(f'<td class="n">{num(v, 2)}</td>')
            elif kind == "math":
                out.append(f'<td class="n">{num(v, 3, good=0)}</td>')
            elif kind == "src":
                if str(v).startswith("http"):
                    out.append(f'<td><a href="{esc(v)}" rel="noopener">source</a></td>')
                else:
                    out.append(f'<td>{cell(v, "no source recorded")}</td>')
            elif kind == "pill":
                p = str(v).lower()
                out.append(f'<td><span class="pill p-{esc(p)}">{esc(v)}</span></td>')
            else:
                out.append(f'<td>{cell(v, (blank_reasons or {}).get(key, "not read"))}</td>')
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def page(name, body, active=None):
    cur = active or name
    links = []
    for h, t in NAV:
        cls = ' class="on"' if h == cur else ""
        links.append(f'<a href="{h}"{cls}>{esc(t)}</a>')
    nav = "".join(links)
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(TITLE)} &middot; {esc(name.replace('.html','').replace('-',' ').title())}</title>
<style>{CSS}</style></head><body>
<header><h1>NFL Line-Gate Desk</h1>
<div class="sub">Own lines, prices, ratings and a pre-registered competition &middot;
session {TAG} &middot; every number dated and sourced &middot; every blank labelled</div></header>
<nav>{nav}</nav><main>
{body}
</main>
<footer>Built from committed inputs only, by a deterministic stdlib generator.
A blank cell is a value that was <strong>not read</strong>, never a zero. Read the
<a href="flagged.html">Flagged for Review</a> page before quoting any number here.</footer>
</body></html>"""
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(doc)
    return name


# ------------------------------------------------------------------ pages
def build_index():
    s = jread("build_summary.json")
    bt = jread("backtest.json")
    fe = read("forecast_error.csv")
    fe = fe[0] if fe else {}
    side = (bt.get("scores") or {}).get("side") or {}
    tot = (bt.get("scores") or {}).get("total") or {}
    orig = read("origination.csv")
    sides = [r for r in orig if r["market"] == "side"]
    agree = sum(1 for r in sides
                if (float(r["fair_line"]) > 0) == (float(r["market_line"]) > 0)) if sides else 0
    big = sorted(sides, key=lambda r: -abs(float(r["difference"] or 0)))[:4] if sides else []

    body = f"""
<h2>Decision dashboard</h2>
<p class="lede">Thirteen Week 11 games, three markets each, priced from a two-season
opponent-adjusted rating. The first thing on this page is the honest verdict, not the
line that looks best.</p>

<div class="cards">
  <div class="card"><div class="k">Games priced</div><div class="v">{len({r['game_id'] for r in orig})}</div>
    <div class="n">side, total, moneyline</div></div>
  <div class="card"><div class="k">Side skill vs close</div>
    <div class="v bad">{num(side.get('skill'), 3)}</div>
    <div class="n">Brier {num(side.get('brier_model'),3)} vs 0.250</div></div>
  <div class="card"><div class="k">Total skill vs close</div>
    <div class="v bad">{num(tot.get('skill'), 3)}</div>
    <div class="n">Brier {num(tot.get('brier_model'),3)} vs 0.250</div></div>
  <div class="card"><div class="k">Margin error</div>
    <div class="v warn">{num(fe.get('margin_mae_model'),2)}</div>
    <div class="n">the close: {num(fe.get('margin_mae_close'),2)}</div></div>
  <div class="card"><div class="k">Settled bets</div><div class="v">0</div>
    <div class="n">no strategy can be certified yet</div></div>
  <div class="card"><div class="k">Agrees on favourite</div><div class="v warn">{agree}/13</div>
    <div class="n">where the model and the market agree</div></div>
</div>

<div class="note bad"><strong>Verdict: the market wins.</strong> The model's Brier skill against the
closing line is {num(side.get('skill'),3)} on the side and {num(tot.get('skill'),3)} on the total, both
negative, over {side.get('n', 'BLANK')} walk-forward games. Its margin error is
{num(fe.get('margin_mae_model'),2)} points against the closing line's {num(fe.get('margin_mae_close'),2)}.
Nothing here is an edge. The fair lines are published because the brief asks for origination,
not because they are better than the price.</div>

<h3>How to read this desk</h3>
<table><thead><tr><th>Column</th><th>Means</th><th>Does not mean</th></tr></thead><tbody>
<tr><td><b>fair line</b></td><td>one model's opinion, with its inputs hashed on the row</td>
<td>a prediction of the result</td></tr>
<tr><td><b>market line</b></td><td>the median of two operators, read at one clock time</td><td>the closing line</td></tr>
<tr><td><b>difference</b></td><td>fair minus market, in the same units, same sign convention</td>
<td>a recommendation to bet</td></tr>
<tr><td><b>signal score</b></td><td>Brier skill, and nothing else</td><td>a return, or a staking plan</td></tr>
<tr><td><b>BLANK</b></td><td>the value was not read, so it is not published</td><td>zero</td></tr>
</tbody></table>

<h3>Largest disagreements this week</h3>
<p class="lede">These are the rows where the model and the market are furthest apart. A large
gap is evidence the model is probably wrong, not evidence of value: the walk-forward says the
market is the better forecaster.</p>
{table([("game_id","Game","text"),("fair_line","Fair","num"),("market_line","Market","num"),
        ("difference","Difference","math"),("read_utc","Read (UTC)","text")],
       [dict(r, difference=float(r['difference']) if r['difference'] else "") for r in big],
       {"read_utc": "no read clock"})}

<h3>Readiness in one line each</h3>
<p class="lede">The full table is on <a href="requirements.html">Requirements</a>. Counts below
are computed from that register, not typed in.</p>
"""
    req = read("requirements.csv")
    from collections import Counter
    c = Counter(r["status"] for r in req)
    body += '<div class="cards">'
    for k, cls in (("MET", "good"), ("PARTIAL", "warn"), ("BLOCKED", "bad")):
        body += (f'<div class="card"><div class="k">{k.lower()}</div>'
                 f'<div class="v {cls}">{c.get(k,0)}</div>'
                 f'<div class="n">of {len(req)} requirements</div></div>')
    body += "</div>"
    blocked = [r for r in req if r["status"] == "BLOCKED"][:8]
    body += table([("id", "ID", "text"), ("requirement", "Blocked requirement", "text"),
                   ("blocking_gate", "Gate", "text"), ("number_that_clears", "Clears at", "text")],
                  blocked)
    body += f"""
<div class="note">The single most useful thing to fix is depth coverage: <b>1 of 32</b> club
charts has been read, which blocks the replacement columns, the injury ablation and the
per-team deficiency view at once. It is one page read per club.</div>
"""
    return page("index.html", body)


def build_origination():
    rows = read("origination.csv")
    games = {}
    for r in rows:
        games.setdefault(r["game_id"], {})[r["market"]] = r
    tbl = []
    for gid in sorted(games):
        d = games[gid]
        s, t, m = d.get("side", {}), d.get("total", {}), d.get("moneyline", {})
        tbl.append(dict(game=gid, kickoff=s.get("kickoff_et", ""),
                        side_fair=s.get("fair_line", ""), side_mkt=s.get("market_line", ""),
                        side_diff=s.get("difference", ""),
                        tot_fair=t.get("fair_line", ""), tot_mkt=t.get("market_line", ""),
                        tot_diff=t.get("difference", ""),
                        ml_fair=m.get("fair_line", ""), ml_mkt=m.get("market_line", ""),
                        ml_am=m.get("fair_as_american", ""),
                        books=s.get("books", ""), read=s.get("read_utc", ""),
                        url=s.get("source_url", "")))
    body = f"""
<h2>Origination: side, then total, then moneyline</h2>
<p class="lede">Numbers are computed in that order because that is the order in which a line is
built: the side sets the game's balance, the total sets its size, the moneyline is the price of
the side. Every row carries the hash of the exact inputs that produced it.</p>

<div class="note warn"><strong>Units matter, so they are in the table.</strong> A <em>side</em> is a
printed home line, where a negative number means the home club is favoured. A <em>total</em> is a
points line. A <em>moneyline</em> is the probability the home club wins, between 0 and 1.
An earlier version of this desk published the side fair line as a home margin while the market
column was a printed line; every sign inverted and it manufactured 23-point edges on games the
model and the market agreed about. Both columns now share one convention, and
<code>tests/test_model.py</code> fails if they ever stop.</div>

<h3>Week 11, all thirteen games</h3>
{table([("game","Game","text"),("kickoff","Kickoff ET","text"),
        ("side_fair","Side fair","num"),("side_mkt","Side market","num"),("side_diff","Diff","math"),
        ("tot_fair","Total fair","num"),("tot_mkt","Total market","num"),("tot_diff","Diff","math"),
        ("ml_fair","Home win p","num"),("ml_mkt","Market p","num"),("books","Books","text"),
        ("url","Game","src")], tbl)}

<h3>How the fair line is produced</h3>
<table><thead><tr><th>Step</th><th>What happens</th><th>Where it is asserted</th></tr></thead><tbody>
<tr><td>1 ratings</td><td>offence and defence per club, ridge-fitted on the two most recent seasons,
walk-forward, so a game is only ever priced by a fit that predates it</td>
<td><code>tests/test_model.py::TestRatings</code></td></tr>
<tr><td>2 margin</td><td>hfa + net(home) − net(away), with net = offence + defence and a defence
that is positive when good</td><td>sign of the defence parameter is tested</td></tr>
<tr><td>3 total</td><td>2&middot;mu + hfa + (off−def) for each club</td>
<td>the mean predicted total equals the mean actual total</td></tr>
<tr><td>4 probability</td><td>home win probability from a normal margin with the measured residual spread</td>
<td>the side skill is bounded, because an unbounded one means leakage</td></tr>
<tr><td>5 de-vig</td><td>each book's two-way moneyline removed of its margin, then averaged</td>
<td><code>devig_two_way</code> sums to one</td></tr>
</tbody></table>
<div class="note"><strong>What would change my mind:</strong> a walk-forward Brier skill above zero
with a clustered interval that excludes zero, on at least 4,721 bets. Nothing on this page comes
close, and the size of the gap is published rather than hidden.</div>
"""
    return page("origination.html", body)


def build_prices():
    snap = read("price_snapshots.csv")
    phases = read("price_store_phases.csv")
    dis = read("book_disagreement.csv")
    books = {}
    for r in snap:
        books.setdefault(r["book"], set()).add(r["game"])
    body = f"""
<h2>Prices: what was read, when, and from where</h2>
<p class="lede">A price is only a fact if it carries a clock, a source and a book. Each capture
below is a single manual read of the operator's own board, hashed, and it is explicitly not a
feed.</p>

<h3>Which phases of the market exist</h3>
{table([("phase","Phase","text"),("available","Available","text"),("n","Rows","num"),("why","Why","text")], phases)}
<div class="note bad">There is <strong>no open</strong> and <strong>no close</strong> on this desk,
and both are declared absent rather than estimated. The first read of this desk is
2026-11-19T11:42:16Z; anything earlier cannot be recovered read-only, and a close is by
definition after the last pre-kickoff capture.</div>

<h3>Coverage</h3>
<div class="cards">
{''.join(f'<div class="card"><div class="k">{esc(b)}</div><div class="v">{len(g)}</div><div class="n">games with a printed main line</div></div>' for b, g in sorted(books.items()))}
</div>

<h3>Where the two operators disagree</h3>
<p class="lede">A one-point spread difference is a real disagreement about the game, and publishing
the median hides it. The books are both shown.</p>
{table([("game_id","Game","text"),("spread_spread","Spread gap","num"),("total_spread","Total gap","num"),("books","Lines as printed","text")], dis)}

<h3>Data policy</h3>
<table><thead><tr><th>Question</th><th>Answer</th><th>Source</th></tr></thead><tbody>
<tr><td>May this desk scrape nfl.com?</td><td>No. Section 1.3 permits personal, non-commercial,
informational use and prohibits systematic retrieval to compile a database without written consent.</td>
<td><a href="https://www.nfl.com/legal/terms" rel="noopener">nfl.com terms</a></td></tr>
<tr><td>May it scrape the operators?</td><td>Unresolved. The operator terms pages returned 404 from
this environment, so the desk does not claim a permission it did not read.</td>
<td><span class="blank" title="two candidate terms URLs returned 404">BLANK</span></td></tr>
<tr><td>So what is a capture?</td><td>One manual read, hashed, dated, stored. Not a feed, not a
scrape, and the page says so on every row.</td><td>this page</td></tr>
</tbody></table>

<h3>Every printed number</h3>
<p class="lede">{len(snap)} rows: 13 games &times; 2 books &times; 6 printed prices. Filter by
book in the table.</p>
{table([("book","Book","text"),("game","Game","text"),("market","Market","text"),
        ("side","Side","text"),("line","Line","num"),("juice","Juice","text"),
        ("printed_start","Board prints","text"),("read_utc","Read UTC","text"),
        ("source_url","Source","src")], snap)}
"""
    return page("prices.html", body)


def build_ratings():
    r = read("ratings.csv")
    r = sorted(r, key=lambda x: -float(x["net_rating"] or 0))
    body = f"""
<h2>Ratings: offence, defence, and who they actually describe</h2>
<p class="lede">One row per club. The rating is opponent-adjusted: a club is judged on what it did
against the defences and offences it actually faced, not on raw points.</p>

<h3>Is the rating real?</h3>
<div class="cards">
  <div class="card"><div class="k">Offence vs points scored</div><div class="v good">0.79</div>
    <div class="n">correlation, must be strongly positive</div></div>
  <div class="card"><div class="k">Defence vs points allowed</div><div class="v good">&minus;0.75</div>
    <div class="n">correlation, must be strongly negative</div></div>
  <div class="card"><div class="k">Net rating vs win rate</div><div class="v good">0.70</div>
    <div class="n">the rating finds the good clubs</div></div>
  <div class="card"><div class="k">Window</div><div class="v">2</div>
    <div class="n">seasons, measured, not assumed</div></div>
</div>

<div class="note warn"><strong>Three defects this table caught, all now tested.</strong>
(1) A fit with a plus-signed defence returned a "defence" that correlated <em>positively</em> with
points allowed (+0.76) &mdash; it was a second offence wearing a different name.
(2) Eliminating one club by substitution to pin the sum-to-zero invariant parked the whole
invariant on the last club alphabetically, which came out at &minus;18.8.
(3) Fitting on all 28 seasons produced a rating barely related to this season's scoring
(correlation 0.027): Jacksonville scored 29.9 a game and was handed a negative offence.
A two-season window fixes it, and <code>tests/test_model.py</code> now fails on each of the three.</div>

<h3>All thirty-two clubs</h3>
{table([("club","Club","text"),("offence","Offence","num"),("defence","Defence","num"),
        ("net_rating","Net","num"),("w","W","text"),("l","L","text"),("t","T","text"),
        ("pf","PF","text"),("pa","PA","text"),("source_url","Standings","src")], r)}
<p class="lede">Record, points for and points against are today's official standings and are shown
next to the rating only so a reader can see the two agree. They were not used to fit the rating.</p>
"""
    return page("ratings.html", body)


def build_results():
    bt = jread("backtest.json")
    fe = read("forecast_error.csv")
    fe = fe[0] if fe else {}
    s = (bt.get("scores") or {}).get("side") or {}
    t = (bt.get("scores") or {}).get("total") or {}
    ms = jread("model_summary.json")

    def row(name, sc, bench, extra=""):
        return dict(name=name, n=sc.get("n", ""), bm=sc.get("brier_model", ""),
                    bb=sc.get("brier_bench", ""), sk=sc.get("skill", ""),
                    lo=sc.get("ci_low", ""), hi=sc.get("ci_high", ""), extra=extra)

    rows = [row("Side vs closing line", s, 0.25), row("Total vs closing total", t, 0.25)]
    body = f"""
<h2>Benchmark: does the model beat the closing line?</h2>
<p class="lede">No. The table below is the whole argument, and it is deliberately built so that
it cannot flatter the model.</p>

<div class="cards">
  <div class="card"><div class="k">Walk-forward games</div><div class="v">{s.get('n','BLANK')}</div>
    <div class="n">every game scored by a fit that predates it</div></div>
  <div class="card"><div class="k">Side skill</div><div class="v bad">{num(s.get('skill'),3)}</div>
    <div class="n">interval {num(s.get('ci_low'),3)} to {num(s.get('ci_high'),3)}</div></div>
  <div class="card"><div class="k">Total skill</div><div class="v bad">{num(t.get('skill'),3)}</div>
    <div class="n">over {t.get('n','BLANK')} games</div></div>
  <div class="card"><div class="k">Residual spread</div><div class="v">{num(ms.get('sd_margin'),2)}</div>
    <div class="n">points, margin</div></div>
</div>

{table([("name","Comparison","text"),("n","Games","num"),("bm","Brier, model","num"),
        ("bb","Brier, benchmark","num"),("sk","Skill","math"),("lo","CI low","num"),("hi","CI high","num")], rows)}

<div class="note bad"><strong>The interval excludes zero on the wrong side.</strong> A negative
skill with an interval of {num(s.get('ci_low'),3)} to {num(s.get('ci_high'),3)} is not a
disappointment, it is a finding: on this corpus the model is significantly worse than taking the
closing line. That is the honest answer to "does origination work", and it is the one that gets
published.</div>

<h3>Like-for-like forecast error</h3>
<p class="lede">The same games, the same target, two forecasters. If the model were better at
pointing at the score, its error would be smaller.</p>
{table([("x","Forecast","text"),("model","Model MAE","num"),("close","Closing line MAE","num")],
       [dict(x="Margin, points", model=fe.get("margin_mae_model",""), close=fe.get("margin_mae_close","")),
        dict(x="Total, points", model=fe.get("total_mae_model",""), close=fe.get("total_mae_close",""))])}
<p class="lede">n = {fe.get('n','BLANK')} games with a closing number. The model is closer on
neither.</p>

<h3>Why the benchmark is 0.25 and not the market's own Brier</h3>
<p class="lede">A side bet at a closing line is 50/50 by construction: the line <em>is</em> the
market's point forecast, so a forecast that takes the line scores a Brier of 0.25. Anything a model
adds has to beat that. The moneyline, being a two-way price, is benchmarked against the de-vigged
close instead, because a 50/50 coin is not the right comparator for a priced market.</p>
<div class="note warn"><strong>A skill above +0.05 is treated as a defect.</strong> An earlier
build reported +0.30 and the cause was a leak: the "model" probability was centred on the closing
line itself. The build now refuses to publish a side skill above +0.05 and the test suite fails
if one appears.</div>
"""
    return page("results.html", body)


def build_leaderboard():
    lb = read("leaderboard.csv")
    luck = read("luck_panel.csv")
    ss = jread("sample_size.json")
    body = f"""
<h2>Leaderboard: pre-registered, unscored, and honest about it</h2>
<p class="lede">Seven strategies were registered before a single bet was settled. None can be
scored yet, and the table says so with BLANK rather than a zero that would read like a result.</p>

<div class="note">A registration is a promise about how a strategy will be judged. Editing one
means writing a new registration with a new id; the id and a hash of the registration file are
stamped on every row below, so a future score can always be traced to the definition that
produced it. Registration: <code>{esc(lb[0]['preregistration_id']) if lb else 'BLANK'}</code>,
hash <code>{esc(lb[0]['preregistration_sha256'][:24]) if lb else 'BLANK'}&hellip;</code></div>

<h3>Registered strategies</h3>
{table([("strategy_id","ID","text"),("name","Strategy","text"),("division","Division","text"),
        ("status","Status","pill"),("settled_bets","Settled","num"),("signal_score","Signal","num"),
        ("staking_units","Staking","num"),("control_baseline","Control","text"),("gate","Gates","text"),
        ("note","Why blank","text")], lb,
       {"signal_score": "no settled bet exists, so no score is published; blank, not zero",
        "staking_units": "no bet has been staked, so there is nothing to show"})}

<h3>How luck is removed</h3>
<p class="lede">Each panel is a specific defence against a specific way of fooling yourself.</p>
{table([("panel","Panel","text"),("headline","What it does","text"),("n","n","text"),("detail","Detail","text")], luck)}

<h3>How many bets before a result means anything</h3>
<div class="cards">
  <div class="card"><div class="k">Bets required</div><div class="v">{ss.get('n_required','BLANK')}</div>
    <div class="n">at &delta; = {ss.get('delta','BLANK')}, power {ss.get('power','BLANK')}</div></div>
  <div class="card"><div class="k">Assumed p</div><div class="v">{num(ss.get('p_assumed'),3)}</div>
    <div class="n">from the observed de-vigged close</div></div>
  <div class="card"><div class="k">Variance</div><div class="v">{num(ss.get('variance'),4)}</div>
    <div class="n">p(1&minus;p)</div></div>
</div>
<div class="note warn">A strategy that looks good over 200 bets has not been validated, it has
been sampled. The desk will not score below {ss.get('n_required','the pre-registered')} bets, and
that number is derived above rather than chosen to suit a narrative.</div>

<h3>Blocked divisions</h3>
<table><thead><tr><th>Division</th><th>Why it cannot be priced yet</th></tr></thead><tbody>
<tr><td>Parlay</td><td>the dependence between two legs of one game must be measured on settled
same-game data; the product of two marginals is not a price.</td></tr>
<tr><td>Player props</td><td>no feed the desk is permitted to store. The boards print props; the
policy section of the registration forbids storing them without a licence.</td></tr>
</tbody></table>
"""
    return page("leaderboard.html", body)


def build_availability():
    av = read("availability_by_club.csv")
    inj = read("injuries_reg11_2026-11-19.csv") if os.path.exists(
        os.path.join(DESK, "inputs", "injuries_reg11_2026-11-19.csv")) else []
    body = f"""
<h2>Availability: what the official report actually says</h2>
<p class="lede">{len(inj)} player rows across 26 clubs that play this week. The report prints a
practice status for everyone and a game status for almost no one, and that distinction is the
whole point of this page.</p>

<div class="note warn"><strong>Absence from the report is not health.</strong> Two clubs print the
words "No Injuries Reported", which is a statement about the report, not about the roster. A player
on reserve appears on neither the report nor this table. Both clubs are shown with the official
string, never as zeroes.</div>

<h3>By club</h3>
{table([("club","Club","text"),("players_listed","Listed","num"),("out","Out","num"),
        ("questionable","Questionable","num"),("dnp","Did not practise","num"),
        ("limited","Limited","num"),("full","Full","num"),
        ("printed_string","Printed instead of a table","text"),("source_url","Source","src")], sorted(av, key=lambda x: x["club"]))}

<h3>Every player row, as printed</h3>
<p class="lede">The injury column is blank for most players because the report leaves it blank.
That is the official page's choice, and it is preserved rather than filled in.</p>
{table([("club","Club","text"),("player","Player","text"),("position","Pos","text"),
        ("injury","Injury, as printed","text"),("practice","Practice","text"),
        ("game","Game status","text"),("slot","Kickoff slot","text"),
        ("source_url","Source","src")], inj,
       {"injury": "the official report leaves this cell blank",
        "game": "no game status was printed for this player"})}
<p class="lede">{sum(1 for r in inj if r['game'])} player rows carry a printed game status.
The rest carry a practice status only, which is not a prediction of who plays.</p>
"""
    return page("availability.html", body)


def build_deficiency():
    d = read("deficiency.csv")
    cov = read("depth_coverage.csv")
    de = read("depth_evidence.csv")
    read_clubs = sorted({x["club"] for x in de})
    body = f"""
<h2>Deficiency: who is missing, and how good the replacement is</h2>
<p class="lede">This is the page the brief cares most about and the one this desk can least
support. One club's depth chart has been read. The other thirty-one are marked NOT READ, and
their rank and replacement columns are blank rather than guessed.</p>

<div class="cards">
  <div class="card"><div class="k">Clubs charted</div><div class="v bad">{len(read_clubs)}/32</div>
    <div class="n">{esc(', '.join(read_clubs))}</div></div>
  <div class="card"><div class="k">Ranked players</div><div class="v">{len(de)}</div>
    <div class="n">read verbatim from a club page</div></div>
  <div class="card"><div class="k">Injured players</div><div class="v">{len(d)}</div>
    <div class="n">from the official report</div></div>
  <div class="card"><div class="k">Inferred ranks</div><div class="v good">0</div>
    <div class="n">no jersey number, salary or experience used, ever</div></div>
</div>

<div class="note bad"><strong>The one substitution this desk can evidence.</strong> Detroit's centre
Cade Mays is listed by the official injury report as not practising, and the club's own depth chart
prints Juice Scruggs directly behind him. That is a replacement, read twice from two official-ish
sources. Thirty-one clubs have no equivalent row here, and the blank is a statement about this
desk's coverage rather than about the roster.</div>

<h3>Depth coverage</h3>
{table([("club","Club","text"),("chart_read","Chart read","text"),("rows_read","Rows","num"),("note","Note","text")], cov)}

<h3>What was actually read</h3>
{table([("club","Club","text"),("position_group","Group","text"),("rank_in_group","Rank","text"),
        ("player","Player","text"),("depth_source_url","Source","src")], de)}

<h3>Injured players against their depth slot</h3>
{table([("club","Club","text"),("player","Player","text"),("position","Pos","text"),
        ("injury_as_printed","Injury","text"),("practice","Practice","text"),
        ("game_status","Game status","text"),("depth_rank","Depth rank","text"),
        ("report_source_url","Report","src")], d,
       {"depth_rank": "no club depth chart was read for this club, so no rank is published; blank is not 'no replacement'",
        "injury_as_printed": "the report leaves this blank",
        "game_status": "no game status printed"})}
"""
    return page("deficiency.html", body)


def build_requirements():
    req = read("requirements.csv")
    from collections import Counter
    c = Counter(r["status"] for r in req)
    body = f"""
<h2>Requirements: one row per thing the brief asked for</h2>
<p class="lede">Every requirement has a status, the gate that blocks it, the number that would
clear it, and what was actually observed. Nothing here is marked done because it was attempted.</p>

<div class="cards">
{''.join(f'<div class="card"><div class="k">{k.lower()}</div><div class="v {v}">{c.get(k,0)}</div><div class="n">requirements</div></div>' for k, v in (("MET","good"),("PARTIAL","warn"),("BLOCKED","bad"),("REJECTED","")) if c.get(k))}
</div>

{table([("id","ID","text"),("requirement","Requirement","text"),("status","Status","pill"),
        ("blocking_gate","Blocking gate","text"),("number_that_clears","Clears at","text"),
        ("observed","Observed","text"),("source_url","Source","src")], req)}
"""
    return page("requirements.html", body)


def build_questions():
    qs = jread("questions.json")
    rows = qs if isinstance(qs, list) else qs.get("questions", [])
    body = f"""
<h2>Questions the brief asks, and what this desk knows</h2>
<p class="lede">Each question is split into what is known, what is missing, and the concrete route
to the answer. A question with no route is an opinion, so every row has one.</p>
{table([("id","ID","text"),("group","Group","text"),("question","Question","text"),
        ("have","What is known","text"),("missing","What is missing","text"),
        ("route","Route to the answer","text"),("answerable","Answerable now","text")], rows)}
"""
    return page("questions.html", body)


def build_suggestions():
    sg = jread("suggestions.json")
    rows = sg if isinstance(sg, list) else sg.get("suggestions", [])
    body = f"""
<h2>Suggestions for the owner</h2>
<p class="lede">Nothing on this page has been implemented. Each suggestion states what it costs,
what it risks, and what it unblocks, so it can be accepted or rejected without reading the code.</p>
{table([("id","ID","text"),("title","Suggestion","text"),("why","Why","text"),
        ("effort","Effort","text"),("risk","Risk","text"),("owner","Unblocks","text"),
        ("decision","Decision","text")], rows)}
<div class="note">The decision column is owned by the reader, not by this desk. No suggestion here
has been acted on.</div>
"""
    return page("suggestions.html", body)


def build_flagged():
    fl = jread("flags.json")
    rows = fl if isinstance(fl, list) else fl.get("flags", [])
    sev_order = {"BLOCKING": 0, "REVIEW": 1, "INFO": 2}
    rows = sorted(rows, key=lambda r: (sev_order.get(r.get("severity"), 3), r.get("id", "")))
    body = f"""
<h2>Flagged for Review</h2>
<p class="lede">Every item on this page is something a reader should know before quoting a number
from this desk. Nothing here blocks publication, and nothing here has been quietly fixed.</p>

<div class="cards">
  <div class="card"><div class="k">Blocking</div>
    <div class="v bad">{sum(1 for r in rows if r.get('severity')=='BLOCKING')}</div>
    <div class="n">prevents a published number</div></div>
  <div class="card"><div class="k">Review</div>
    <div class="v warn">{sum(1 for r in rows if r.get('severity')=='REVIEW')}</div>
    <div class="n">needs a human decision</div></div>
  <div class="card"><div class="k">Info</div>
    <div class="v">{sum(1 for r in rows if r.get('severity')=='INFO')}</div>
    <div class="n">context that changes a reading</div></div>
</div>

<h3>Index</h3>
{table([("id","ID","text"),("severity","Severity","text"),("title","Item","text"),
        ("blank_value_reason","What it leaves blank","text")], rows)}
"""
    for r in rows:
        srcs = " ".join(f'<a href="{esc(u)}" rel="noopener">source {i+1}</a>'
                        for i, u in enumerate(r.get("sources", [])))
        body += f"""
<h3>{esc(r.get('id',''))} &middot; {esc(r.get('title',''))}
<span class="pill p-{esc((r.get('severity') or 'info').lower().replace('blocking','blocked'))}">{esc(r.get('severity',''))}</span></h3>
<p class="lede">{esc(r.get('detail',''))}</p>
<p class="lede"><b>What it leaves blank:</b> {esc(r.get('blank_value_reason','nothing'))}</p>
<p class="lede">{srcs}</p>
"""
    return page("flagged.html", body)


def build_research():
    bt = jread("backtest.json")
    ms = jread("model_summary.json")
    body = f"""
<h2>Method: what was tried, what broke, and what was kept</h2>
<p class="lede">This page exists because a model that cannot say how it was wrong is not a
model. Every defect below shipped past a review of an earlier version of a desk like this one.</p>

<h3>Defects found by this desk's own invariants</h3>
<table><thead><tr><th>#</th><th>Defect</th><th>How it showed up</th><th>Fix</th></tr></thead><tbody>
<tr><td>1</td><td>A league average inside a <em>difference</em></td>
<td>every predicted margin inflated by about 22 points; probabilities saturated at 0.96</td>
<td>a margin expression may never contain mu; asserted in code</td></tr>
<tr><td>2</td><td>Defence fitted with a plus sign</td>
<td>the defence column correlated <b>positively</b> with points allowed (+0.76), i.e. it was a
second offence</td><td>minus sign in the score equations, with a test on the correlation</td></tr>
<tr><td>3</td><td>Sum-to-zero by elimination</td>
<td>the invariant parked on the last club alphabetically, which came out at &minus;18.8</td>
<td>ridge on both blocks together, which identifies them without eliminating anything</td></tr>
<tr><td>4</td><td>Fitting on 28 seasons</td>
<td>corr(offence, points-for) = 0.027; Jacksonville scored 29.9 a game and got a negative offence</td>
<td>two-season window, measured against 0.786 for the same test</td></tr>
<tr><td>5</td><td>Benchmark probability centred on the close</td>
<td>a side skill of +0.30 against a closing line, which is impossible</td>
<td>centre the model probability on the model's own margin; refuse any skill above +0.05</td></tr>
<tr><td>6</td><td>Sign convention between columns</td>
<td>fair line as a home margin, market line as a printed line: every sign inverted, 23-point
fake edges</td><td>one convention, tested</td></tr>
<tr><td>7</td><td>Reading a corpus field the wrong way round</td>
<td>closing-line MAE of 14.6, which no real closing line produces</td>
<td>the sign is now <em>measured</em> two ways, per season, and reported</td></tr>
</tbody></table>

<h3>Model as shipped</h3>
<table><thead><tr><th>Parameter</th><th>Value</th><th>Note</th></tr></thead><tbody>
<tr><td>mu (points per club per game)</td><td class="n">{num(ms.get('mu'),2)}</td>
<td>fitted, with the intercept of the totals equation</td></tr>
<tr><td>hfa (home advantage)</td><td class="n">{num(ms.get('hfa'),2)}</td>
<td>positive, i.e. the home club scores more; a negative value would be a defect</td></tr>
<tr><td>window</td><td class="n">2</td><td>seasons, measured</td></tr>
<tr><td>lambda</td><td class="n">{num(ms.get('lam'),2)}</td><td>ridge on ratings only, never on an intercept</td></tr>
<tr><td>residual spread, margin</td><td class="n">{num(bt.get('sd_margin'),2)}</td>
<td>points; the width of the normal used for probabilities</td></tr>
<tr><td>spread sign</td><td class="n">{num(bt.get('spread_sign'),0)}</td>
<td>{esc(bt.get('spread_sign_evidence',''))}</td></tr>
</tbody></table>

<h3>What has not been attempted</h3>
<ul class="lede">
<li>Weather, roof and surface overlays &mdash; no official file was read.</li>
<li>Snap counts as a starter proxy &mdash; the feed is not stored on this desk.</li>
<li>Injury as a surprise rather than a level &mdash; needs two dated reads, and there is one.</li>
<li>Any joint model for parlays &mdash; the dependence has not been measured.</li>
</ul>
"""
    return page("research.html", body)


def build_sources():
    man = read("manifest.csv")
    body = f"""
<h2>Sources: every input, hashed</h2>
<p class="lede">If a number on this site cannot be traced to a row in this table, it should not be
quoted. Each input has a row count, a sha256 and the clock time it was read.</p>

<div class="note warn"><strong>Two classes of source.</strong> <b>Official</b> means an NFL page or
a club page, read manually and hashed. <b>Third-party</b> means the pinned nflverse corpus, used
for the walk-forward because no official machine-readable closing-line history exists. Its Week 10
2026 rows were reconciled 14 of 14 against today's official finals, which is the only cross-check
available and is not the same as a guarantee.</div>

{table([("input","Input","text"),("rows","Rows","num"),("read_utc","Read UTC","text"),
        ("path","Path","text"),("source_url","Source","src")], man)}

<h3>Official pages read for this build</h3>
<table><thead><tr><th>Page</th><th>Used for</th><th>Link</th></tr></thead><tbody>
<tr><td>League standings, 2026 regular season</td><td>32-club record, points for and against,
and the league identities (wins equal losses; points for equal points against)</td>
<td><a href="https://www.nfl.com/standings/league/2026/REG" rel="noopener">nfl.com</a></td></tr>
<tr><td>Week 11 schedule</td><td>13 games, kickoff times, networks, bye clubs</td>
<td><a href="https://www.nfl.com/schedules/2026/by-week/week-11" rel="noopener">nfl.com</a></td></tr>
<tr><td>Week 11 official injury report</td><td>every player row, practice status and the few
printed game statuses</td>
<td><a href="https://www.nfl.com/injuries/league/2026/reg11" rel="noopener">nfl.com</a></td></tr>
<tr><td>Week 10 finals</td><td>the 14 completed games, used for the reconciliation</td>
<td><a href="https://www.nfl.com/schedules/2026/by-week/week-10" rel="noopener">nfl.com</a></td></tr>
<tr><td>Detroit Lions depth chart</td><td>the only club depth chart read in full</td>
<td><a href="https://www.detroitlions.com/team/depth-chart" rel="noopener">detroitlions.com</a></td></tr>
<tr><td>DraftKings NFL board</td><td>spread, total and both moneylines, one read</td>
<td><a href="https://sportsbook.draftkings.com/leagues/football/nfl" rel="noopener">draftkings.com</a></td></tr>
<tr><td>FanDuel NFL board</td><td>the same, from the second book</td>
<td><a href="https://sportsbook.fanduel.com/navigation/nfl" rel="noopener">fanduel.com</a></td></tr>
<tr><td>NFL.com terms of use</td><td>the data policy: section 1.3 governs what may be stored</td>
<td><a href="https://www.nfl.com/legal/terms" rel="noopener">nfl.com</a></td></tr>
</tbody></table>
"""
    return page("sources.html", body)


def main():
    pages = [build_index(), build_origination(), build_prices(), build_ratings(), build_results(),
             build_leaderboard(), build_availability(), build_deficiency(), build_requirements(),
             build_questions(), build_suggestions(), build_flagged(), build_research(),
             build_sources()]
    with open(os.path.join(OUT, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print(f"wrote {len(pages)} pages + style.css + .nojekyll")
    for p in pages:
        print(f"  {p:22s} {os.path.getsize(os.path.join(OUT,p)):>7d} bytes")


if __name__ == "__main__":
    main()

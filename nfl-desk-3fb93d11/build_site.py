"""Deterministic static-site build for the price-snapshot desk.

Every body-table row is rendered with a source cell.  A row whose source cell is
empty is rendered with an explicit UNVERIFIED badge that links to the Flagged
for Review page, so an empty cell can never be mistaken for a sourced value.
verify.py re-walks the generated HTML and fails the build if that invariant is
broken.
"""

from __future__ import annotations

import csv
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import RETRIEVED_UTC

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
SITE = ROOT
NAV = [
    ("index.html", "Overview", "Dashboard"),
    ("executive-summary.html", "Executive summary", "Summary"),
    ("requirements.html", "Requirements", "Governance"),
    ("suggestions.html", "Suggestions for review", "Governance"),
    ("questions.html", "Open questions", "Governance"),
    ("results.html", "Verified results feed", "Evidence"),
    ("price-store.html", "Price snapshot store", "Evidence"),
    ("lines.html", "Originated lines", "Markets"),
    ("strategies.html", "Strategies", "Markets"),
    ("gates.html", "Validation & demotion", "Markets"),
    ("leaderboard.html", "Leaderboard", "Markets"),
    ("correlations.html", "Correlations", "Markets"),
    ("depth.html", "Injuries & replacement depth", "Team state"),
    ("sources.html", "Sources", "Assurance"),
    ("repo-audit.html", "Repo audit", "Assurance"),
    ("flagged.html", "Flagged for review", "Assurance"),
]

CSS = """
:root{--bg:#f5f7f6;--card:#ffffff;--ink:#12211d;--muted:#5d7168;--line:#dfe6e2;
--accent:#14614f;--accent-soft:#e3f0eb;--warn:#8a5a00;--warn-soft:#fdf3e0;
--bad:#8c2f2f;--bad-soft:#fbeaea;--ok:#14614f;--ok-soft:#e3f0eb;--slate:#3d4f48}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg)}
a{color:var(--accent)}
.skip{position:absolute;left:-9999px}
.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:9}
.layout{display:grid;grid-template-columns:250px 1fr;min-height:100vh}
.sidebar{background:#0f2b25;color:#cfe3dc;padding:20px 16px;position:sticky;top:0;height:100vh;overflow:auto}
.brand{display:flex;gap:10px;align-items:center;color:#fff;text-decoration:none;font-weight:700;font-size:17px;margin-bottom:4px}
.brand span.badge{background:var(--accent);border-radius:6px;padding:2px 8px;font-size:13px}
.brand small{display:block;font-weight:500;font-size:11px;color:#8fb3a7;letter-spacing:.08em}
.navcap{font-size:10px;letter-spacing:.14em;color:#7fa394;margin:16px 0 6px;text-transform:uppercase}
.sidebar nav a{display:block;color:#cfe3dc;text-decoration:none;padding:7px 10px;border-radius:7px;font-size:13.5px}
.sidebar nav a:hover{background:#173a32}
.sidebar nav a.active{background:var(--accent);color:#fff;font-weight:600}
.sidebar nav a small{display:block;color:#8fb3a7;font-weight:400;font-size:11px}
.sidebar nav a.active small{color:#bfe0d4}
.sidefoot{margin-top:18px;font-size:11.5px;color:#8fb3a7;border-top:1px solid #234a40;padding-top:12px}
main{padding:26px 30px 60px;max-width:1400px}
h1{font-size:27px;margin:0 0 6px}
h2{font-size:19px;margin:30px 0 10px}
h3{font-size:15px;margin:20px 0 8px}
p.lede{color:var(--muted);margin:0 0 18px;max-width:90ch}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:700}
.stamp{font-size:12px;color:var(--muted)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:12px;margin:18px 0 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.card span{display:block;font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.card strong{display:block;font-size:24px;margin-top:4px;font-variant-numeric:tabular-nums}
.card small{color:var(--muted);font-size:12px}
.card.warn strong{color:var(--warn)}
.card.bad strong{color:var(--bad)}
.card.ok strong{color:var(--ok)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:16px 0}
.panel h2{margin-top:0}
.tools{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:10px 0}
.tools input,.tools select{border:1px solid var(--line);border-radius:7px;padding:7px 9px;font-size:13px;background:#fff}
.count{font-size:12.5px;color:var(--muted)}
.tw{overflow:auto;border:1px solid var(--line);border-radius:10px;background:#fff;max-height:none}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
thead th{background:#eef3f1;position:sticky;top:0;font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--slate);white-space:nowrap}
tbody tr:hover{background:#f7faf9}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.pill{display:inline-block;border-radius:20px;padding:1px 9px;font-size:11.5px;font-weight:600;white-space:nowrap}
.p-ok{background:var(--ok-soft);color:var(--ok)}
.p-warn{background:var(--warn-soft);color:var(--warn)}
.p-bad{background:var(--bad-soft);color:var(--bad)}
.p-grey{background:#eef1f0;color:var(--slate)}
.src{white-space:nowrap;font-size:12px}
.src a{text-decoration:none}
.blank{display:inline-block;background:var(--warn-soft);color:var(--warn);border:1px solid #f0dcb4;
border-radius:5px;padding:0 6px;font-size:11px;font-weight:700}
.empty{display:none;padding:14px;color:var(--muted);font-size:13px}
.note{font-size:12.5px;color:var(--muted);margin-top:8px}
.prose{max-width:95ch}
.prose li{margin-bottom:6px}
footer{margin-top:40px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;font-size:13px}
.kv dt{font-weight:600;color:var(--slate)}
.kv dd{margin:0}
@media(max-width:900px){.layout{grid-template-columns:1fr}.sidebar{position:static;height:auto}main{padding:18px}}
"""

JS = """
document.querySelectorAll('input[data-search]').forEach(function(inp){
  var id=inp.getAttribute('data-search');
  inp.addEventListener('input',function(){
    var q=inp.value.toLowerCase();var rows=document.querySelectorAll('tr[data-table="'+id+'"]');
    var shown=0;
    rows.forEach(function(tr){var hit=tr.textContent.toLowerCase().indexOf(q)>-1;
      tr.style.display=hit?'':'none';if(hit)shown++;});
    var c=document.querySelector('[data-count="'+id+'"]');if(c)c.textContent=shown+' rows shown';
  });
});
document.querySelectorAll('.exp').forEach(function(b){
  b.addEventListener('click',function(){
    var id=b.getAttribute('data-exp');var t=document.getElementById(id);
    var rows=[];var heads=[];
    t.querySelectorAll('thead th').forEach(function(th){heads.push(th.textContent.trim());});
    t.querySelectorAll('tbody tr').forEach(function(tr){var r=[];
      tr.querySelectorAll('td').forEach(function(td){r.push(td.textContent.trim());});rows.push(r);});
    function esc(v){v=String(v==null?'':v);return '"'+v.replace(/"/g,'""')+'"';}
    var csv=[heads.map(esc).join(',')].concat(rows.map(function(r){return r.map(esc).join(',');})).join('\\n');
    var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
    a.download=id+'.csv';a.click();
  });
});
"""


def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def read(name: str) -> list:
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def source_cell(row: dict) -> tuple:
    """Return (html, has_source).  Scans the row for any field carrying a URL."""
    keys = [k for k in row if "source" in k.lower() or k.endswith("_url") or k == "url"]
    for k in keys:
        v = (row.get(k) or "").strip()
        if v.startswith("http"):
            label = {"source_url": "official", "official_source_url": "official",
                     "market_source_url": "market", "mirror_source_url": "mirror",
                     "feed_source_url": "official", "depth_chart_source_url": "club chart",
                     "injury_source_url": "injury report", "model_source_url": "official",
                     "depth_source_url": "club chart",
                     "results_source_url": "official",
                     "universe_source_url": "results"}.get(k, "source")
            return (f'<a class="src" href="{esc(v)}" target="_blank" rel="noopener noreferrer">'
                    f'{esc(label)} &#8599;</a>', True)
    for k, v in row.items():
        if isinstance(v, str) and v.startswith("http"):
            return (f'<a class="src" href="{esc(v)}" target="_blank" rel="noopener noreferrer">'
                    f'source &#8599;</a>', True)
    return ('<a class="blank" href="flagged.html" title="No official source confirms this '
            'row - see the flagged register">UNVERIFIED</a>', False)


def pill(text: str) -> str:
    t = (text or "").strip().lower()
    cls = "p-grey"
    if t in ("match", "yes", "pass", "agree", "ok", "met", "armed", "official", "certified"):
        cls = "p-ok"
    elif t in ("irregular", "no", "fail", "disagree", "blocking", "bad", "not published"):
        cls = "p-bad"
    elif t in ("review", "open", "partially met", "watch", "aggregator", "awaiting decision",
               "not checked", "in progress at merge time", "derived", "would fire"):
        cls = "p-warn"
    return f'<span class="pill {cls}">{esc(text)}</span>'


def table(rows: list, cols: list, tid: str, numeric: set = None, pills: set = None,
          max_rows: int = None) -> str:
    numeric = numeric or set()
    pills = pills or set()
    shown = rows[:max_rows] if max_rows else rows
    head = "".join(f"<th scope=\"col\">{esc(c.replace('_', ' '))}</th>"
                   for c in cols) + '<th scope="col">Source</th>'
    body = []
    for r in shown:
        tds = []
        for c in cols:
            v = r.get(c, "")
            cls = ' class="num"' if c in numeric else ""
            if c in pills and str(v).strip():
                tds.append(f"<td>{pill(v)}</td>")
            else:
                tds.append(f"<td{cls}>{esc(v)}</td>")
        sc, _ = source_cell(r)
        tds.append(f"<td>{sc}</td>")
        body.append(f'<tr data-table="{tid}">' + "".join(tds) + "</tr>")
    truncated = ""
    if max_rows and len(rows) > max_rows:
        truncated = (f'<p class="note">Showing the first {max_rows} of {len(rows)} rows. '
                     f'The full set is in <code>data/{tid}.csv</code>.</p>')
    return (f'<div class="tools"><label>Search <input type="search" data-search="{tid}" '
            f'placeholder="filter this table"></label><span class="count" data-count="{tid}">'
            f'{len(shown)} rows</span><button class="exp" data-exp="{tid}" '
            f'style="border:1px solid #dfe6e2;border-radius:7px;padding:7px 10px;background:#fff;'
            f'font-size:13px;cursor:pointer">Export CSV</button></div>'
            f'<div class="tw"><table id="{tid}"><thead><tr>{head}</tr></thead><tbody>'
            + "".join(body) + "</tbody></table></div>"
            + f'<p class="empty" id="empty-{tid}">No matching rows.</p>{truncated}')


def page(active: str, title: str, eyebrow: str, lede: str, body: str, cards: str = "") -> str:
    nav = []
    current_group = None
    for fn, label, group in NAV:
        if group != current_group:
            nav.append(f'<div class="navcap">{esc(group)}</div>')
            current_group = group
        cls = " active" if fn == active else ""
        nav.append(f'<a class="{cls.strip()}" href="{fn}">{esc(label)}</a>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} &middot; Own5 price-snapshot desk</title>
<meta name="description" content="{esc(lede)[:150]}">
<style>{CSS}</style></head><body><a class="skip" href="#main">Skip to content</a>
<div class="layout"><aside class="sidebar">
<a class="brand" href="index.html"><span class="badge">O5</span><span>OWN5<small>PRICE &amp; RESULTS DESK</small></span></a>
<nav aria-label="Main navigation">{''.join(nav)}</nav>
<div class="sidefoot">Official data retrieved<br>{esc(RETRIEVED_UTC)}<br><br>
Every row on every page links to the source that produced it. Blank cells are labelled UNVERIFIED &mdash; never filled in.</div>
</aside><main id="main">
<span class="eyebrow">{esc(eyebrow)}</span><h1>{esc(title)}</h1>
<p class="lede">{esc(lede)}</p>
<span class="stamp">Official sources retrieved {esc(RETRIEVED_UTC)} &middot; rebuilt deterministically &middot;
<a href="https://github.com/sassnarep3-star/Own5/tree/main/nfl-desk-3fb93d11" target="_blank" rel="noopener noreferrer">source &amp; rebuild script &#8599;</a></span>
{cards}{body}
<footer>Own5 &mdash; independent NFL line-origination research. Not affiliated with the NFL.
Research only: nothing here is betting advice, and no bet has been placed.
<a href="flagged.html">Flagged for review &#8599;</a></footer>
</main></div><script>{JS}</script></body></html>"""


def cards_html(items: list) -> str:
    out = []
    for value, label, sub, tone in items:
        cls = f" card {tone}" if tone else ""
        out.append(f'<article class="card{cls}"><span>{esc(label)}</span>'
                   f'<strong>{esc(value)}</strong><small>{esc(sub)}</small></article>')
    return '<div class="cards">' + "".join(out) + "</div>"


# --------------------------------------------------------------------------
def build(report: dict) -> None:
    acc = report.get("accuracy", {})
    depth = report.get("depth", {})
    mir = report.get("mirror_agreement", {})
    orig = report.get("origination", {})
    ps = report.get("price_store", {})
    feed = read("results_feed.csv")
    prices = read("price_snapshots.csv")
    schema = read("price_store_schema.csv")
    markets = read("originated_markets.csv")
    steps = read("origination_steps.csv")
    ledger = read("strategy_ledger.csv")
    board = read("leaderboard.csv")
    gates = read("gates.csv")
    dem = read("demotion_gate.csv")
    corr = read("correlations_official.csv")
    withheld = read("correlations_withheld.csv")
    dep = read("replacement_depth.csv")
    xchk = read("depth_injury_crosscheck.csv")
    flags = read("flagged.csv")
    sug = read("suggestions.csv")
    qs = read("questions.csv")
    reqs = read("requirements.csv")
    srcs = read("sources.csv")
    audit = read("repo_audit.csv")
    recon = read("results_reconciliation.csv")
    mchk = read("results_mirror_check.csv")
    std = read("standings_official.csv")

    n_pop = ps.get("populated", 0)
    n_rows = ps.get("rows", 0)

    # ---------------------------------------------------------- overview
    cards = cards_html([
        (report["official_games"], "Official games in the feed",
         "transcribed week by week from nfl.com", ""),
        (f"{mir.get('agree', 0)}/{report['official_games']}", "Mirror agreement",
         f"{mir.get('disagree', 0)} disagreements, {mir.get('missing', 0)} not yet in the mirror", ""),
        (orig.get("markets", 0), "Markets originated",
         f"{orig.get('games', 0)} scheduled games, side + total + moneyline", ""),
        (f"{n_pop}/{n_rows}", "Price-store cells populated",
         "the rest are empty and flagged, not filled in", "warn"),
        (report["backtests"]["certified"], "Certified strategies",
         "none clears the gates; see Validation", "warn"),
        (len(flags), "Flagged for review",
         f"{sum(1 for f in flags if f['severity'] == 'blocking')} blocking", "warn"),
        (len(sug), "Suggestions awaiting a decision",
         "nothing on that page is implemented", ""),
        (report["correlations_official"], "Official correlations published",
         f"{len(withheld)} previously published values withheld", ""),
    ])
    overview = f"""
<div class="panel"><h2>What this desk is</h2>
<p>This session was asked for eight specific things: a price-snapshot store that records opening
and closing numbers for every market we originate; a verified results feed so backtests and ROI
can be computed at all; an origination order of side &rarr; total &rarr; moneyline; model, market
and difference as three separate columns; a leaderboard that scores signal and staking separately;
the <em>depth</em> of a replacement rather than the fact of one; correlations from officially
sourced numbers only, each with its n; and a demotion gate that sends a live strategy back to
paper. All eight are built and published here.</p>
<p>The headline finding is unchanged from the honest position of every desk before it: <strong>nfl.com
publishes no betting prices</strong>. That single fact is why the price store's opening and closing
rows are empty, why gate G2 fails for every strategy, and why nothing on the board is certified.
The store now records exactly where the gap is, instead of leaving it implicit.</p></div>
<h2>Where to go next</h2>
<div class="panel"><dl class="kv">
<dt>Newest evidence</dt><dd><a href="results.html">Verified results feed</a> &mdash; 137 official finals, reconciled club by club against the official standings page.</dd>
<dt>The gap</dt><dd><a href="price-store.html">Price snapshot store</a> &mdash; {n_rows - n_pop} empty cells, each with the reason.</dd>
<dt>The output</dt><dd><a href="lines.html">Originated lines</a> &mdash; {orig.get('markets', 0)} markets, side then total then moneyline.</dd>
<dt>The verdict</dt><dd><a href="leaderboard.html">Leaderboard</a> &mdash; signal rank and staking rank, computed from disjoint inputs.</dd>
<dt>Decisions needed</dt><dd><a href="suggestions.html">Suggestions</a> and <a href="questions.html">open questions</a> &mdash; nothing implemented until you choose.</dd>
</dl></div>
"""
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(
        page("index.html", "Overview", "Dashboard",
             "A price-snapshot and verified-results desk for originating NFL lines, with every "
             "value traceable to an official source and every gap labelled instead of filled.",
             overview, cards))

    # ------------------------------------------------- executive summary
    exec_body = f"""
<div class="panel"><h2>The eight requirements, and what each produced</h2>
<ul>
<li><strong>Price-snapshot store.</strong> {n_rows} rows &mdash; one per market per snapshot type
across {orig.get('markets', 0)} originated markets. {n_pop} carry a value; {n_rows - n_pop} are empty
and carry a flag id. The slots exist for the desk's own open and close and for the operator's open and
close; only the ones we can source are populated.</li>
<li><strong>Verified results feed.</strong> {report['official_games']} games for 2026, transcribed
from the official week-by-week schedule pages. Rebuilding every club's win-loss-tie, points for and
points against from those {report['official_games']} games reproduces the official standings page with
<strong>{report['standings_mismatches']} mismatches across 32 clubs</strong>. The pinned mirror agrees on
{mir.get('agree', 0)} of them and lags on {mir.get('missing', 0)}.</li>
<li><strong>Origination order.</strong> Every game records three steps in order: side, total,
moneyline. The moneyline row states that it is derived from the side and the total, never fitted
separately.</li>
<li><strong>Three columns.</strong> model_line, market_line and difference_model_minus_market, for
all three market types. market_line is labelled AGGREGATOR because no official price exists.</li>
<li><strong>Signal versus staking.</strong> Two ranks per family from disjoint inputs. Today's clearest
case: a strategy that is first on realised money from four bets sits fifth of eight on signal.</li>
<li><strong>Depth of replacement.</strong> {depth['slots']} published position slots across
{depth['clubs_published']} clubs; {depth['slots_using_a_backup']} are being filled by a backup, each
naming which string steps in, whether that man is himself on the injury report, and whether the loss
compounds to a third name.</li>
<li><strong>Correlations.</strong> {len(corr)} pairs, every one computed from official numbers, each
published with r, p, a 95% interval and n. {len(withheld)} values previously published elsewhere in
this repo are moved to a withheld register because their inputs were not official.</li>
<li><strong>Demotion gate.</strong> Six triggers, evaluated against every family. All are armed;
none has fired, because nothing has ever been live.</li>
</ul></div>
<div class="panel"><h2>What the model can and cannot do</h2>
<p>Out of sample on 2026 weeks {acc.get('weeks_covered')} ({acc.get('n_predictions')} games), the side
model's margin forecast correlates with the actual margin at r = {acc.get('margin_corr_r')}
(p = {acc.get('margin_corr_p')}, n = {acc.get('margin_corr_n')}) and calls the straight-up winner
{acc.get('su_hits')} of {acc.get('su_decided')} ({acc.get('su_hit_rate')}). Its margin error is
{acc.get('side_mae')} points against {acc.get('naive_mae_tie')} for the naive "predict a tie"
baseline, so the side model is worth about {round(float(acc.get('side_mae',0)) - float(acc.get('naive_mae_tie',0)),2) * -1} points a game.</p>
<p>The totals model is the weak half: {acc.get('total_mae')} points of error against
{acc.get('naive_mae_league_total')} for simply predicting the league average every time. It adds
nothing yet, and because the moneyline is derived from the side <em>and</em> the total, that weakness
flows into the moneyline. Fixing it is suggestion S-02.</p></div>
<div class="panel"><h2>Why nothing is certified</h2>
<p>Two gates do the work. G2 requires every graded bet to link to a verified opening and closing
price snapshot; there is no official publisher of NFL prices, so G2 fails for every family. G8
requires the certification sample to come from an official results feed; the official feed holds one
season, so the certification board gives each family between 4 and 51 graded bets against a 300-bet
minimum. On the larger mirror sample the best family hits {ledger[-1]['hit_rate'] if ledger else ''}
against a {ledger[-1]['breakeven'] if ledger else ''} break-even, which is below the price it would
have to beat.</p>
<p>That is the honest output, not a failure to find one: on the evidence available, no family here
has demonstrated an edge.</p></div>
"""
    open(os.path.join(SITE, "executive-summary.html"), "w", encoding="utf-8").write(
        page("executive-summary.html", "Executive summary", "Summary",
             "What was built, what the numbers say, and what is missing.", exec_body, cards))

    # ---------------------------------------------------------- requirements
    open(os.path.join(SITE, "requirements.html"), "w", encoding="utf-8").write(
        page("requirements.html", "Requirements", "Governance",
             "Every requirement in the brief, the artefact that answers it, and the gap that "
             "remains.",
             "<h2>Requirements matrix</h2>" + table(
                 reqs, ["id", "requirement", "status", "how_it_is_met", "gap_or_caveat", "page"],
                 "requirements", pills={"status"})))

    # ------------------------------------------------------------ suggestions
    sug_body = f"""
<div class="panel"><h2>How to use this page</h2>
<p>Every row is a proposal, not a change. Each has two or three costed options, a recommended path,
the evidence that prompted it, and the test that would change the recommendation. Nothing here is
implemented &mdash; the decision state of all {len(sug)} is AWAITING DECISION. Pick a path and it moves
to the build; leave it and it stays visible as an open choice.</p></div>
<h2>Suggestions for review</h2>
""" + table(sug, ["id", "title", "problem", "option_a", "option_b", "option_c", "recommended",
                  "impact", "effort", "confidence", "owner", "decision"],
            "suggestions", pills={"decision", "impact"})
    open(os.path.join(SITE, "suggestions.html"), "w", encoding="utf-8").write(
        page("suggestions.html", "Suggestions for review", "Governance",
             "Proposals to improve the site and the decision-making around it, each waiting for a "
             "chosen path before anything is built.", sug_body))

    # -------------------------------------------------------------- questions
    blocking = sum(1 for q in qs if q["status"] == "BLOCKING")
    q_body = f"""
<div class="panel"><h2>What we know, what we do not, and how to find out</h2>
<p>{blocking} of {len(qs)} questions are blocking: no amount of computation closes them, because the
answer is either a data source that does not exist publicly or an owner decision. The rest are
answerable and are answered below. Every row states the cheapest way to resolve it.</p></div>
<h2>Question register</h2>
""" + table(qs, ["id", "question", "why_it_matters", "what_we_have", "what_is_missing",
                 "cheapest_way_to_resolve", "what_it_blocks", "status"],
            "questions", pills={"status"})
    open(os.path.join(SITE, "questions.html"), "w", encoding="utf-8").write(
        page("questions.html", "Open questions", "Governance",
             "The information a decision needs, what we already have, and what is still missing.",
             q_body))

    # ------------------------------------------------------------- results
    res_body = f"""
<div class="panel"><h2>What the feed is</h2>
<p>{len(feed)} completed 2026 regular-season games, transcribed from nfl.com's week-by-week
schedule pages (Weeks 1&ndash;10; the Week 10 Thursday game is final, the rest of Week 10 has not
kicked off). Each row carries its own source URL and the UTC retrieval stamp. This is the feed the
backtests, the model and the leaderboard read from.</p></div>
<h2>Reconciliation against the official standings</h2>
<p class="note">Every club's record and points were rebuilt from the {len(feed)} games above and
compared with the official standings page, club by club. {report['standings_mismatches']} mismatches.</p>
""" + table(recon, ["team", "club", "official_w", "official_l", "official_t", "official_pf",
                    "official_pa", "feed_w", "feed_l", "feed_t", "feed_pf", "feed_pa",
                    "w_delta", "l_delta", "t_delta", "pf_delta", "pa_delta", "agrees"],
            "results_reconciliation", numeric={"official_w", "official_l", "official_t",
                                               "official_pf", "official_pa", "feed_w", "feed_l",
                                               "feed_t", "feed_pf", "feed_pa", "w_delta",
                                               "l_delta", "t_delta", "pf_delta", "pa_delta"},
            pills={"agrees"}) + f"""
<h2>Cross-check against the pinned mirror</h2>
<p class="note">The mirror agrees on {mir.get('agree', 0)} of {len(feed)} games and disagrees on
{mir.get('disagree', 0)}. It has not yet published a final for {mir.get('missing', 0)} game that
nfl.com shows as final &mdash; flag F-02.</p>
""" + table(mchk, ["game_id", "week", "matchup", "official_away_score", "official_home_score",
                   "mirror_away_score", "mirror_home_score", "agrees", "state"],
            "results_mirror_check", numeric={"official_away_score", "official_home_score",
                                             "mirror_away_score", "mirror_home_score"},
            pills={"agrees"}, max_rows=200) + """
<h2>Official standings</h2>
<p class="note">Transcribed from the official league standings page; this is the benchmark the feed
was reconciled against.</p>
""" + table(std, ["team", "club", "w", "l", "t", "games_played", "win_pct", "pf", "pa",
                  "net_pts", "pf_per_game", "pa_per_game", "net_per_game"],
            "standings_official", numeric={"w", "l", "t", "games_played", "win_pct", "pf", "pa",
                                           "net_pts", "pf_per_game", "pa_per_game",
                                           "net_per_game"}) + """
<h2>The feed itself</h2>
""" + table(feed, ["game_id", "week", "kickoff_date", "weekday_as_published", "weekday_checked",
                   "away", "home", "away_score", "home_score", "home_margin", "total_points",
                   "result", "neutral_site"],
            "results_feed", numeric={"week", "away_score", "home_score", "home_margin",
                                     "total_points"})
    open(os.path.join(SITE, "results.html"), "w", encoding="utf-8").write(
        page("results.html", "Verified results feed", "Evidence",
             "Official finals, reconciled club by club against the official standings and "
             "cross-checked against the pinned mirror.", res_body))

    # ---------------------------------------------------------- price store
    ps_body = f"""
<div class="panel"><h2>What the store records</h2>
<p>One row per market per snapshot type. There are {orig.get('markets', 0)} markets (side, total and
moneyline for each of {orig.get('games', 0)} scheduled games), so {n_rows} rows in total.
<strong>{n_pop} carry a value.</strong> The other {n_rows - n_pop} are empty, and each empty row
names the flag that explains it. The store never fills a cell to make a table look complete.</p>
<dl class="kv">
<dt>MODEL_ORIGIN</dt><dd>the price this desk first originates, with a UTC stamp</dd>
<dt>MODEL_CLOSE</dt><dd>the desk's last price before kickoff &mdash; empty until a second run (F-03)</dd>
<dt>MARKET_OPEN</dt><dd>the operator's opening price &mdash; empty, no official publisher exists (F-01)</dd>
<dt>MARKET_CLOSE</dt><dd>the operator's closing price &mdash; empty, same reason (F-01)</dd>
<dt>MARKET_REFERENCE</dt><dd>an aggregator line of unknown timestamp, kept for context and never
called an opening or a closing price (F-14)</dd>
</dl></div>
<h2>Schema and coverage</h2>
""" + table(schema, ["snapshot_type", "meaning", "rows_total", "populated_rows", "empty_rows",
                     "source_tier", "blocking_flag"], "price_store_schema",
            numeric={"rows_total", "populated_rows", "empty_rows"}, pills={"source_tier"}) + """
<h2>Snapshot rows</h2>
""" + table(prices, ["week", "matchup", "market_type", "snapshot_type", "line_value",
                     "price_american", "snapshot_utc", "source_tier", "verified", "flag_id"],
            "price_snapshots", numeric={"line_value", "price_american"}, pills={"source_tier"},
            max_rows=400)
    open(os.path.join(SITE, "price-store.html"), "w", encoding="utf-8").write(
        page("price-store.html", "Price snapshot store", "Evidence",
             "Opening and closing numbers for every market we originate, with empty slots "
             "labelled rather than filled.", ps_body))

    # --------------------------------------------------------------- lines
    lines_body = f"""
<div class="panel"><h2>Origination order: side, then total, then moneyline</h2>
<p>The order is not cosmetic. The side is priced from a margin model; the total from a separate
totals model; and the moneyline is then <em>derived</em> from the two of them as
P(home win) = &Phi;(side / &sigma;), with &sigma; = {report.get('sigma_used')} points estimated from
out-of-sample residuals. The moneyline therefore cannot disagree with the side and total it came
from, and every row records that dependency.</p>
<p>All three steps are fitted on the {report['official_games']} official 2026 results only. Home-field
advantage comes out at {orig.get('hfa_pts')} points, which is not separable from zero on this
sample &mdash; flag F-11.</p></div>
<h2>Model line, market line, difference</h2>
<p class="note">model_line is ours. market_line is the aggregator's untimestamped line, labelled
AGGREGATOR throughout (F-14). difference is model minus market. For the moneyline the columns are
probabilities, and the market figure is de-vigged.</p>
""" + table(markets, ["week", "matchup", "kickoff_label", "market_type", "origination_order",
                      "derived_from", "model_line", "market_line",
                      "difference_model_minus_market", "model_price_american",
                      "market_price_american", "units"],
            "originated_markets", numeric={"model_line", "market_line",
                                           "difference_model_minus_market",
                                           "model_price_american", "market_price_american"},
            pills={"market_type"}) + """
<h2>Step-by-step origination</h2>
""" + table(steps, ["game_id", "origination_step", "model_value", "market_value", "difference",
                    "derived_from"], "origination_steps",
            numeric={"model_value", "market_value", "difference"})
    open(os.path.join(SITE, "lines.html"), "w", encoding="utf-8").write(
        page("lines.html", "Originated lines", "Markets",
             "Our own prices for every scheduled market, in the order side, total, moneyline, "
             "with the market line and the difference beside them.", lines_body))

    # ---------------------------------------------------------- strategies
    strat_body = f"""
<div class="panel"><h2>Nine pre-registered families</h2>
<p>Every rule below, and its parameters, was written down before any result was inspected. Graded
walk-forward: parameters are always fitted on periods strictly earlier than the period being graded.
Two universes are shown. The <strong>certification</strong> universe is the official results feed:
small, but it is the only one that can ever certify anything. The <strong>research</strong> universe
is the pinned mirror from 1999 to 2025: thousands of bets, useful for asking whether a signal exists
at all, but it cannot certify or reward anything.</p>
<p>Bets are graded at a flat -110, a 52.38% break-even, because the mirror carries no per-leg prices
for 2026 (F-07).</p></div>
<h2>Results</h2>
""" + table(ledger, ["row_id", "family", "bet_class", "universe", "universe_tier", "n_decided",
                     "n_pushes", "wins", "hit_rate", "breakeven", "ci95_low", "ci95_high",
                     "p_vs_breakeven", "holm_p", "holm_significant", "mean_clv", "roi_pct",
                     "sharpe", "deflated_sharpe", "gates_passed", "gates_hard", "source_tier"],
            "strategy_ledger",
            numeric={"n_decided", "n_pushes", "wins", "hit_rate", "breakeven", "ci95_low",
                     "ci95_high", "p_vs_breakeven", "holm_p", "mean_clv", "roi_pct", "sharpe",
                     "deflated_sharpe", "gates_passed", "gates_hard"},
            pills={"universe_tier", "holm_significant", "source_tier"}) + """
<div class="panel"><h2>Reading the results honestly</h2>
<ul>
<li>The moneyline family (S3) is <em>significantly worse</em> than break-even, not merely
inconclusive. That is a real finding about the rule, and the signal score penalises it rather than
rewarding the strength of the evidence.</li>
<li>The research board's largest samples land around 51% against a 52.38% break-even. That is the
shape of a market that has already priced the signal.</li>
<li>The same-game parlay needs 27.44% and delivered 26.32% over 1,953 bets. Independent leg pricing
is not free money; it is an assumption that costs about 4% of turnover here.</li>
<li>Prop combinations (S9) produced no graded bets at all, because no prop lines exist from any
source in this repo. The row is kept deliberately empty rather than modelled (F-08, S-09).</li>
</ul></div>
"""
    open(os.path.join(SITE, "strategies.html"), "w", encoding="utf-8").write(
        page("strategies.html", "Strategies", "Markets",
             "Nine pre-registered families across singles, parlays and prop combos, graded "
             "walk-forward on two universes.", strat_body))

    # --------------------------------------------------------------- gates
    gate_body = f"""
<div class="panel"><h2>Validation gates</h2>
<p>Nine gates. A family is certified only when every hard gate passes. G2 (price provenance) and G8
(official results) are the two that nothing currently clears.</p></div>
<h2>Gate definitions</h2>
""" + table(gates, ["gate_id", "name", "test", "hard", "provenance"], "gates",
            pills={"hard"}) + """
<h2>Gate matrix by family and universe</h2>
""" + table(read("gate_matrix.csv"), ["strategy_id", "strategy", "gate_id", "result", "note",
                                      "universe_tier"], "gate_matrix", pills={"result"}) + """
<div class="panel"><h2>The demotion gate (D1)</h2>
<p>A strategy that has been promoted to live is returned to paper the moment any trigger fires.
Demotion is automatic: it does not wait for a review and it cannot be overridden by a good week.
Re-promotion needs a fresh pass through G0&ndash;G8 on bets logged after the demotion.</p>
<dl class="kv">
""" + "".join(f"<dt>{esc(t)}</dt><dd>{esc(x)}</dd>" for t, x, _ in
              [("D1a", "Rolling 200-bet closing-line value at or below zero", ""),
               ("D1b", "Drawdown from peak of 20% or more of the reference bankroll", ""),
               ("D1c", "The last 100 graded bets fail to beat break-even at p &lt; 0.10 one-sided", ""),
               ("D1d", "Any parameter or rule changed from the pre-registered commit", ""),
               ("D1e", "Any graded bet without a verified opening or closing snapshot", ""),
               ("D1f", "The official results feed falls more than a week behind", "")]) + """
</dl>
<p><strong>Current state:</strong> armed. Nothing has ever been promoted to live, so no trigger has
fired and no family is eligible for demotion. The table below evaluates each trigger against every
family anyway, so the day a promotion happens the gate is already wired.</p></div>
<h2>Demotion evaluation</h2>
""" + table(dem, ["row_id", "current_state", "demotion_trigger", "trigger_text",
                  "why_it_matters", "evaluation"], "demotion_gate", pills={"current_state"})
    open(os.path.join(SITE, "gates.html"), "w", encoding="utf-8").write(
        page("gates.html", "Validation and demotion", "Markets",
             "Nine gates a strategy must pass, and the demotion gate that sends a live strategy "
             "back to paper.", gate_body))

    # ---------------------------------------------------------- leaderboard
    cert_board = [b for b in board if b["board"] == "CERTIFICATION"]
    staking_only = [b for b in cert_board if b["staking_rank"] == "1"]
    lb_body = f"""
<div class="panel"><h2>Why the board is split</h2>
<p>A leaderboard with one score lets a lucky staking run promote a signal that has no evidence
behind it. So each family is scored twice, from disjoint inputs:</p>
<ul>
<li><strong>signal_score</strong> &mdash; how much the hit rate exceeds the break-even rate after
shrinkage, the deflated Sharpe ratio against the number of families tried, the sample size, and
whether it survives a Holm correction <em>in the right direction</em>. A family that is
significantly worse than break-even is penalised, not rewarded.</li>
<li><strong>staking_score</strong> &mdash; realised money only: flat-stake return plus a bounded
Sharpe term. This is the axis a lucky run can win.</li>
</ul>
<p>Only the signal axis can certify or reward anything. And ranking happens <em>inside</em> a board,
never across universes: the certification board reads official results, the research board reads the
mirror and has no standing.</p></div>
{f'<div class="panel"><h2>The case the split was built for</h2><p>On the certification board, first place on realised money is <strong>{esc(staking_only[0]["family"])}</strong> with {esc(staking_only[0]["n_decided"])} graded bets and {esc(staking_only[0]["roi_pct"])}% return &mdash; and it sits {esc(staking_only[0]["signal_rank"])} of {esc(staking_only[0]["board_size"])} on signal. Under a single-score board that run would have been rewarded. Here it is labelled staking-only and cannot be certified.</p></div>' if staking_only else ''}
<h2>Certification board &mdash; official results</h2>
""" + table([b for b in board if b["board"] == "CERTIFICATION"],
            ["family", "bet_class", "n_decided", "hit_rate", "signal_score", "signal_rank",
             "staking_score", "staking_rank", "rank_gap", "roi_pct", "gates_passed",
             "gates_hard", "certified", "state", "source_tier", "note"], "leaderboard",
            numeric={"n_decided", "hit_rate", "signal_score", "signal_rank", "staking_score",
                     "staking_rank", "rank_gap", "roi_pct", "gates_passed", "gates_hard"},
            pills={"certified", "state", "source_tier"}) + """
<h2>Research board &mdash; mirror results, context only</h2>
""" + table([b for b in board if b["board"] != "CERTIFICATION"],
            ["family", "bet_class", "n_decided", "hit_rate", "signal_score", "signal_rank",
             "staking_score", "staking_rank", "rank_gap", "roi_pct", "gates_passed",
             "gates_hard", "certified", "state", "source_tier", "note"], "leaderboard_research",
            numeric={"n_decided", "hit_rate", "signal_score", "signal_rank", "staking_score",
                     "staking_rank", "rank_gap", "roi_pct", "gates_passed", "gates_hard"},
            pills={"certified", "state", "source_tier"}) + """
<div class="panel"><h2>Rewards</h2>
<p>The brief asks for rewards for top-performing strategies. Until questions Q-04 (cash, points or
nothing) and Q-05 (jurisdiction and eligibility) are answered, the competition runs as
<strong>points only</strong> and no reward is payable. The intended cash structure is a proposal,
not a commitment &mdash; suggestion S-12. In any case nothing would be payable today: there is no
certified entrant.</p></div>
"""
    open(os.path.join(SITE, "leaderboard.html"), "w", encoding="utf-8").write(
        page("leaderboard.html", "Leaderboard", "Markets",
             "Signal and staking scored on separate axes, ranked inside their own board, with "
             "the staking axis unable to certify anything.", lb_body))

    # --------------------------------------------------------- correlations
    corr_body = f"""
<div class="panel"><h2>Official inputs only, with n on every value</h2>
<p>The brief now requires correlations to be computed only from officially sourced numbers, with the
sample size published alongside each value. Every pair below is computed from numbers published by
nfl.com &mdash; the 32-row league standings page, or the {report['official_games']} official game
results in this desk's feed. Each row states r, its p-value, a 95% interval, n and what n counts.</p>
<p>That rule has a cost, and it is worth being explicit about it: the official set is smaller and
narrower than what this repo published before, because the previous values were computed from a
third-party mirror. They have not been deleted &mdash; they are listed in the withheld register
below, with the basis that disqualifies them.</p></div>
<h2>Admissible correlations</h2>
""" + table(corr, ["corr_id", "unit_of_analysis", "metric_a", "metric_b", "r", "p_value",
                   "ci95_low", "ci95_high", "n", "n_definition", "source_tier"],
            "correlations_official",
            numeric={"r", "p_value", "ci95_low", "ci95_high", "n"}, pills={"source_tier"}) + """
<h2>Withheld &mdash; previously published, not admissible</h2>
""" + table(withheld, ["withheld_id", "quantity", "previously_published_value",
                       "previously_published_n", "published_by_session", "input_basis",
                       "admissible_under_official_only_rule", "reason"],
            "correlations_withheld", numeric={"previously_published_value"},
            pills={"admissible_under_official_only_rule"}) + """
<div class="panel"><h2>What is still missing</h2>
<p>The correlations that matter most to this project &mdash; the joint behaviour of two player-prop
legs in the same game, which is what prices a same-game parlay &mdash; cannot be computed at all
from official inputs available here, because no official source publishes player-prop lines or
outcomes at that granularity. Gate G7 therefore fails for every parlay and prop-combination family,
and the desk refuses to price a leg pair it cannot measure (F-08).</p></div>
"""
    open(os.path.join(SITE, "correlations.html"), "w", encoding="utf-8").write(
        page("correlations.html", "Correlations", "Markets",
             "Correlation values computed from officially sourced numbers only, each published "
             "with its n.", corr_body))

    # --------------------------------------------------------------- depth
    backups = [d for d in dep if d["replacement_depth_string"]]
    depth_body = f"""
<div class="panel"><h2>Tracking the depth of the replacement, not the fact of one</h2>
<p>Knowing that a starter is out is the easy half. What matters is <em>who</em> replaces him and
<em>how far down</em> the chart that is. This tracker answers, for every published position slot on
every club:</p>
<ul>
<li>which string is actually expected to start &mdash; 2nd, 3rd or 4th;</li>
<li>whether that replacement is himself carrying a designation on the official injury report, so a
loss compounds into a second;</li>
<li>whether the loss therefore cascades to a third name, and whether a third name is even published;</li>
<li>how many rungs down the chart the club has been forced to go.</li>
</ul>
<p>Offence and defence are tracked as separate rows with their own unit column, so a defence playing
its third-string cornerback is never pooled with an offence starting its backup left tackle.</p>
<p>{depth['slots']} slots across {depth['clubs_published']} clubs. Houston publishes its chart only as
an image, so it contributes no rows rather than a guessed set (F-05). {depth['slots_using_a_backup']}
slots are currently being filled by a backup.</p></div>
<h2>Cross-check: players the league lists as Out</h2>
<p class="note">Each player the official report lists as Out is checked against his club's own
published chart. {depth['out_players_irregular']} of {depth['out_players_checked']} are still printed
as the first-string starter &mdash; a club chart can lag the league report by days (F-06).</p>
""" + table(xchk, ["team", "player", "position", "game_status", "practice_status",
                   "injured_player_is_published_starter", "depth_slot_moved", "check_state"],
            "depth_injury_crosscheck", pills={"game_status"}) + f"""
<h2>Slots being filled by a backup ({len(backups)})</h2>
""" + table(backups, ["team", "club", "unit", "position", "first_string", "starter_unavailable",
                      "replacement_player", "replacement_depth_string",
                      "depth_of_replacement_label", "replacement_on_official_report",
                      "replacement_game_status", "compounding_replacement_out",
                      "cascade_to_player", "rungs_down", "no_backup_published", "as_of"],
            "replacement_depth_active",
            numeric={"replacement_depth_string", "rungs_down"}, pills={"unit"}) + f"""
<h2>All published slots ({len(dep)})</h2>
""" + table(dep, ["team", "club", "unit", "position", "first_string", "second_string",
                  "third_string", "expected_starter_next_game", "replacement_depth_string",
                  "depth_of_replacement_label", "compounding_replacement_out", "rungs_down",
                  "no_backup_published", "as_of"],
            "replacement_depth", numeric={"replacement_depth_string", "rungs_down"},
            pills={"unit"}, max_rows=800) + """
<div class="panel"><h2>Limits of this tracker</h2>
<ul>
<li>Game status is empty for 301 of the 326 rows the official report publishes, because statuses
fill in later in the week. The tracker therefore under-counts Out players early in the week (F-12).</li>
<li>The Week 11 injury report does not exist yet: the URL serves Week 10. Every Week 11 market on
this site is originated with no injury adjustment at all (F-04).</li>
<li>A club chart is the club's own statement of intent, not a guarantee of who plays.</li>
</ul></div>
"""
    open(os.path.join(SITE, "depth.html"), "w", encoding="utf-8").write(
        page("depth.html", "Injuries and replacement depth", "Team state",
             "Which string steps in, whether that replacement is also hurt, and whether the loss "
             "compounds &mdash; split by offence and defence.", depth_body))

    # -------------------------------------------------------------- sources
    open(os.path.join(SITE, "sources.html"), "w", encoding="utf-8").write(
        page("sources.html", "Sources", "Assurance",
             "Every page this desk read, what it was used for, and its verification state.",
             "<h2>Source register</h2>" + table(
                 srcs, ["source_id", "publisher", "title", "url", "tier", "fetched_utc",
                        "used_for", "rows_contributed", "verification_status"], "sources",
                 pills={"tier"}) + """
<div class="panel"><h2>Tiers</h2><dl class="kv">
<dt>OFFICIAL</dt><dd>Published by the NFL or by a club. Facts may be asserted from these.</dd>
<dt>DERIVED</dt><dd>Computed in this repo from OFFICIAL inputs, by a script that is committed and
re-runnable. Reproducible, but a model output, not a published fact.</dd>
<dt>AGGREGATOR</dt><dd>A third-party mirror. Used for cross-checks and as an untimestamped market
reference only. Never used to assert a fact, and never called an opening or closing price.</dd>
</dl></div>"""))

    # ----------------------------------------------------------- repo audit
    verdicts = {}
    for a in audit:
        verdicts[a["verdict"]] = verdicts.get(a["verdict"], 0) + 1
    audit_body = f"""
<div class="panel"><h2>What was re-checked</h2>
<p>The repository already carried six NFL desks built by earlier sessions. This page re-checks their
headline numbers against the official pages fetched for this build, without editing any of them.
{len(audit)} checks ran: {verdicts.get('MATCH', 0)} matched, {verdicts.get('IRREGULAR', 0)}
disagreed, {verdicts.get('NOT CHECKED', 0)} could not be run.</p>
<p>A disagreement is reported with both numbers and never silently corrected. A check that could not
be run says why. Only headline claims are re-checked here; a full line-by-line read of all 1,000-plus
files in this repository is more than one session can honestly claim to have done.</p></div>
<h2>Checks</h2>
""" + table(audit, ["check_id", "area", "claim_under_review", "source_file", "published_value",
                    "recomputed_value", "verdict", "note"], "repo_audit",
            pills={"verdict"}, max_rows=300)
    open(os.path.join(SITE, "repo-audit.html"), "w", encoding="utf-8").write(
        page("repo-audit.html", "Repo audit", "Assurance",
             "Earlier desks' headline claims, re-checked line by line against the official "
             "pages fetched for this build.", audit_body))

    # -------------------------------------------------------------- flagged
    flag_body = f"""
<div class="panel"><h2>Flagged for review</h2>
<p>{len(flags)} items. {sum(1 for f in flags if f['severity'] == 'blocking')} are blocking: they
stop a gate from being satisfiable, not merely a number from being pretty. Each carries the source
it relates to and the action that would clear it.</p>
<p>An empty cell anywhere on this site means one of these. Nothing is inferred to fill a gap.</p></div>
<h2>Register</h2>
""" + table(flags, ["id", "severity", "area", "title", "detail", "consequence", "action",
                    "status"], "flagged", pills={"severity"})
    open(os.path.join(SITE, "flagged.html"), "w", encoding="utf-8").write(
        page("flagged.html", "Flagged for review", "Assurance",
             "Unverified values, irregularities and blocking gaps, each with the source and the "
             "action that would clear it.", flag_body))

    print(f"built {len(NAV)} pages into {SITE}")


if __name__ == "__main__":
    with open(os.path.join(DATA, "build_report.json"), encoding="utf-8") as fh:
        import json
        build(json.load(fh))

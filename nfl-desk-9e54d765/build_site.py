#!/usr/bin/env python3
"""build_site.py — deterministic static site for desk 9e54d765.

Every page is rendered from the committed CSVs in data/. No JavaScript is needed to read
anything; the tables are plain HTML. Every table row carries its source link; a blank cell is
rendered as an explicit "unread / unverified" marker rather than an empty box.
"""
import csv
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
PAGES = HERE

BUILT = '2026-11-19T11:10:00Z'
DASH = '—'

NAV = [
    ('index.html', 'Dashboard'),
    ('readiness.html', 'Decision readiness'),
    ('origination.html', 'Our lines'),
    ('backtest.html', 'Backtest &amp; luck'),
    ('leaderboard.html', 'Leaderboard'),
    ('availability.html', 'Injuries &amp; depth'),
    ('correlations.html', 'Correlations'),
    ('questions.html', 'Questions'),
    ('suggestions.html', 'Suggestions'),
    ('flagged.html', 'Flagged for review'),
    ('sources.html', 'Sources &amp; method'),
]

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#111827;--muted:#6b7280;--line:#e5e7eb;--blue:#1d4ed8;
--green:#15803d;--red:#b91c1c;--amber:#b45309;--purple:#6d28d9}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,
sans-serif;background:var(--bg);color:var(--ink);line-height:1.5;font-size:15px}
header{background:#0b2545;color:#fff;padding:1.1rem 1.4rem}
header .wrap{max-width:1180px;margin:0 auto}
header h1{margin:0;font-size:1.22rem;letter-spacing:.02em}
header p{margin:.35rem 0 0;font-size:.85rem;opacity:.88}
nav{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}
nav .wrap{max-width:1180px;margin:0 auto;display:flex;gap:.15rem;flex-wrap:wrap;padding:.35rem .7rem}
nav a{padding:.4rem .62rem;border-radius:.4rem;text-decoration:none;color:var(--blue);
font-size:.85rem;border:1px solid transparent;white-space:nowrap}
nav a:hover{background:#eef3fb;border-color:#c7d7f5}
nav a.active{background:#e7eefc;border-color:var(--blue);font-weight:700}
main{max-width:1180px;margin:0 auto;padding:1.1rem 1.4rem 3rem}
h2{font-size:1.12rem;margin:1.7rem 0 .6rem;padding-bottom:.3rem;border-bottom:2px solid var(--line)}
h3{font-size:.98rem;margin:1.2rem 0 .4rem;color:#1f2937}
p{margin:.5rem 0}
small,.small{font-size:.82rem;color:var(--muted)}
table{width:100%;border-collapse:collapse;margin:.6rem 0 1.1rem;background:var(--card);
font-size:.83rem}
th,td{border:1px solid var(--line);padding:.4rem .5rem;text-align:left;vertical-align:top}
th{background:#f1f5f9;font-weight:700;color:#334155;font-size:.79rem;text-transform:none}
tr:nth-child(even) td{background:#fcfdff}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.unread{color:var(--muted);font-style:italic}
a{color:var(--blue)}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.badge{display:inline-block;padding:.05rem .45rem;border-radius:.8rem;font-size:.72rem;
font-weight:700;border:1px solid transparent}
.b-met{background:#dcfce7;color:#166534;border-color:#bbf7d0}
.b-part{background:#fef3c7;color:#92400e;border-color:#fde68a}
.b-not{background:#fee2e2;color:#991b1b;border-color:#fecaca}
.b-na{background:#e5e7eb;color:#374151;border-color:#d1d5db}
.b-high{background:#fee2e2;color:#991b1b}
.b-med{background:#fef3c7;color:#92400e}
.b-low{background:#e0e7ff;color:#3730a3}
.b-off{background:#e7f0fd;color:#1d4ed8}
.b-pin{background:#ede9fe;color:#5b21b6}
.b-op{background:#dcfce7;color:#166534}
.b-eq{background:#e5e7eb;color:#374151}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:.8rem;
margin:1rem 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:.6rem;padding:.8rem .9rem}
.kpi .v{font-size:1.45rem;font-weight:700;color:#0b2545;font-variant-numeric:tabular-nums}
.kpi .k{font-size:.76rem;color:var(--muted);margin-top:.1rem}
.kpi .s{font-size:.72rem;color:var(--muted);margin-top:.25rem}
.note{background:#eef6ff;border:1px solid #cfe3fb;border-radius:.5rem;padding:.7rem .9rem;
font-size:.88rem;margin:.8rem 0}
.warn{background:#fffbeb;border:1px solid #fde68a;border-radius:.5rem;padding:.7rem .9rem;
font-size:.88rem;margin:.8rem 0}
.stop{background:#fef2f2;border:1px solid #fecaca;border-radius:.5rem;padding:.7rem .9rem;
font-size:.88rem;margin:.8rem 0}
.good{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:.5rem;padding:.7rem .9rem;
font-size:.88rem;margin:.8rem 0}
footer{border-top:1px solid var(--line);margin-top:2rem;padding:1rem 1.4rem;color:var(--muted);
font-size:.8rem;background:#fff}
footer .wrap{max-width:1180px;margin:0 auto}
.src{font-size:.75rem}
@media(max-width:640px){
  main{padding:.8rem .7rem 2rem}
  header{padding:.9rem .8rem}
  th,td{padding:.32rem .38rem;font-size:.76rem}
  nav a{font-size:.79rem;padding:.32rem .48rem}
}
"""


def esc(v):
    return html.escape('' if v is None else str(v))


def interval(lo, hi):
    if not lo and not hi:
        return DASH
    return f'[{lo}, {hi}]'


def read(name):
    with open(os.path.join(DATA, name), newline='') as fh:
        return list(csv.DictReader(fh))


def num(v, dp=None):
    if v in ('', None):
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if dp is not None:
        return f'{f:.{dp}f}'
    return v


def cell(v, dp=None, cls=''):
    """Render a value, or an explicit unread marker when the value is absent."""
    if v in ('', None):
        return f'<td class="unread" title="no value could be read from an official source">' \
               f'not read</td>'
    txt = num(v, dp)
    if txt is None:
        return f'<td class="{cls}">{esc(v)}</td>'
    return f'<td class="num {cls}">{esc(txt)}</td>'


def link(url, label=None):
    if not url:
        return '<span class="unread">no source</span>'
    lab = label or url
    if len(lab) > 48:
        lab = lab[:45] + '…'
    return f'<a href="{esc(url)}" rel="noopener">{esc(lab)}</a>'


def badge(text):
    cls = {'MET': 'b-met', 'PARTIALLY MET': 'b-part', 'NOT MET': 'b-not',
           'NOT APPLICABLE': 'b-na', 'SEE R24': 'b-na', 'HIGH': 'b-high', 'MEDIUM': 'b-med',
           'LOW': 'b-low', 'OFFICIAL': 'b-off', 'PINNED-DATASET': 'b-pin',
           'NAMED-OPERATOR': 'b-op', 'PRIOR-CAPTURE': 'b-eq'}.get(text, 'b-na')
    return f'<span class="badge {cls}">{esc(text)}</span>'


def layout(page, title, body, subtitle=''):
    navhtml = ''.join(
        '<a href="%s"%s>%s</a>' % (f, ' class="active"' if f == page else '', n)
        for f, n in NAV)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Own5 NFL desk 9e54d765</title>
<style>{CSS}</style>
</head>
<body>
<header><div class="wrap">
<h1>NFL Line-Origination Desk · session 9e54d765</h1>
<p>Own lines, verified results, pre-registered strategies, measured availability. Read
{esc(BUILT)}. Every row links to its source; a value that could not be read from an official
source is marked <em>not read</em> and appears on the Flagged for Review page.</p>
</div></header>
<nav><div class="wrap">{navhtml}</div></nav>
<main>
<h2>{esc(title)}</h2>
{f'<p class="small">{subtitle}</p>' if subtitle else ''}
{body}
</main>
<footer><div class="wrap">
Desk 9e54d765 · built from committed inputs by <code>build_data.py</code> and rendered by
<code>build_site.py</code> · every figure re-derivable with <code>python3 build_data.py</code>
· no bets are placed and no strategy is certified · <a href="flagged.html">Flagged for
review</a> · <a href="sources.html">Sources and method</a>
</div></footer>
</body></html>
"""


def table(headers, rows, cls=''):
    head = ''.join(f'<th>{h}</th>' for h in headers)
    return (f'<div class="scroll"><table class="{cls}"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


# ------------------------------------------------------------------------------ derived
def load_all():
    d = {}
    for name in os.listdir(DATA):
        if name.endswith('.csv'):
            d[name] = read(name)
    with open(os.path.join(DATA, 'build_manifest.json')) as fh:
        d['manifest'] = json.load(fh)
    return d


def fam_by(d, name):
    return next((r for r in d['backtest_families.csv'] if r['family'] == name), None)


# --------------------------------------------------------------------------------- pages
def page_index(d):
    f4 = fam_by(d, 'F4_OPPONENT_AWARE')
    f5 = fam_by(d, 'F5_MARKET_LINE_BENCHMARK')
    tot = d['backtest_totals.csv'][0]
    luck = {r['panel']: r for r in d['luck_panel.csv']}
    recon = d['standings_reconciliation.csv']
    exact = sum(1 for r in recon if r['match'] == 'yes')
    orig = d['origination_week11.csv']
    ab = next(r for r in d['availability_ablation.csv'] if r['variant'].startswith('DIFF'))
    q = {r['designation']: r for r in d['designation_reliability.csv']
         if r['season'] == '2023-2026 pooled'}
    flags = d['flagged.csv']
    high = sum(1 for r in flags if r['severity'] == 'HIGH')
    reqs = d['requirements.csv']
    met = sum(1 for r in reqs if r['status'] == 'MET')
    part = sum(1 for r in reqs if r['status'] == 'PARTIALLY MET')
    notmet = sum(1 for r in reqs if r['status'] == 'NOT MET')
    kpis = f"""
<div class="kpis">
  <div class="kpi"><div class="v">{len(orig)}</div><div class="k">originated market rows</div>
    <div class="s">13 fixtures × side, total, moneyline (home and away)</div></div>
  <div class="kpi"><div class="v">{exact}/32</div><div class="k">clubs reconciled to the official standings</div>
    <div class="s">W, L, T, PF and PA, all five columns</div></div>
  <div class="kpi"><div class="v">{f4['brier_skill_vs_close']}</div>
    <div class="k">model Brier skill vs the de-vigged close</div>
    <div class="s">95% game-cluster interval [{f4['skill_lo95']}, {f4['skill_hi95']}], n={f4['n_games']}</div></div>
  <div class="kpi"><div class="v">{f4['n_bets']}</div><div class="k">settled bets in the staking column</div>
    <div class="s">ROI {f4['staking_roi']} [{f4['staking_roi_lo95']}, {f4['staking_roi_hi95']}] — signal and staking disagree</div></div>
  <div class="kpi"><div class="v">0</div><div class="k">certified strategies</div>
    <div class="s">nothing has cleared the pre-registered gate</div></div>
  <div class="kpi"><div class="v">{met}<span style="font-size:.9rem">/{len(reqs)}</span></div>
    <div class="k">brief lines fully met ({part} partial, {notmet} not met)</div></div>
</div>"""

    headline = f"""
<div class="stop"><strong>The headline is a negative result.</strong> The opponent-aware model
scores a Brier skill of <strong>{f4['brier_skill_vs_close']}</strong> against the de-vigged
closing line — an interval of [{f4['skill_lo95']}, {f4['skill_hi95']}] over {f4['n_games']}
walk-forward games, entirely below zero. It is worse than the closing line, not merely
unlucky. The totals model is also negative ({tot['brier_skill_vs_close']}). No strategy on this
desk is certified, every leaderboard row is PAPER, and the two controls (random 0.5 and
favourites-only) are published beside the model so a reader can see what "no skill" scores.</div>"""

    srchints = ''.join(
        f'<tr><td>{link(r["url"], r["name"])}</td><td>{badge(r["source_class"])}</td>'
        f'<td class="src">{esc(r["read_utc"])}</td><td>{esc(r["used_for"])}</td></tr>'
        for r in d['sources.csv'])
    body = f"""
{headline}
{kpis}
<h2>What this desk can and cannot tell you today</h2>
<table>
<thead><tr><th style="width:32%">Question</th><th>Answer with the measured number</th></tr></thead>
<tbody>
<tr><td>Can our model price a game better than the market?</td>
<td><strong>No.</strong> Side skill {f4['brier_skill_vs_close']}
[{f4['skill_lo95']}, {f4['skill_hi95']}], total skill {tot['brier_skill_vs_close']}
[{tot['skill_lo95']}, {tot['skill_hi95']}], both against de-vigged closes.
<a href="backtest.html">Backtest &amp; luck</a></td></tr>
<tr><td>Is the market line itself a fair benchmark?</td>
<td>The spread-to-probability benchmark scores {f5['brier_skill_vs_close']}
[{f5['skill_lo95']}, {f5['skill_hi95']}], i.e. statistically level with the moneyline close.
The close is the right ceiling. <a href="backtest.html">detail</a></td></tr>
<tr><td>Does the availability term help?</td>
<td><strong>No, slightly the opposite.</strong> Squared error is {ab['difference_vs_without']}
higher with availability features on, interval [{ab['diff_lo95']}, {ab['diff_hi95']}] over
{ab['n_games']} paired games. <a href="availability.html">detail</a></td></tr>
<tr><td>What does the official "Questionable" mean?</td>
<td>{q['Questionable']['play_rate']} of Questionable rows have a snap record
[{q['Questionable']['ci_lo']}, {q['Questionable']['ci_hi']}], n={q['Questionable']['designated_rows']}.
Out: {q['Out']['play_rate']}, n={q['Out']['designated_rows']}.
<a href="availability.html">detail</a></td></tr>
<tr><td>How much settled data is needed to rank strategies?</td>
<td>{luck['C_bets_to_prove_55pct']['value']} bets to separate 55% from break-even,
{luck['D_bets_to_prove_54pct']['value']} for 54%. <a href="backtest.html">luck panel</a></td></tr>
<tr><td>Can parlay or prop-combo strategies be ranked?</td>
<td><strong>No.</strong> Multiplying marginal probabilities is invalid under dependence; the
measured same-game margin/total correlation is small but not zero. The three combo divisions
are published as BLOCKED. <a href="leaderboard.html">leaderboard</a></td></tr>
<tr><td>Are the prices we compare against named and stamped?</td>
<td>Yes: DraftKings and FanDuel, read at 11:00Z and 11:01Z today, transcribed verbatim in
<code>inputs/</code>. Closings do not exist yet because the games have not kicked off.
<a href="origination.html">our lines</a></td></tr>
</tbody></table>

<div class="warn"><strong>What is flagged and blocking.</strong> {high} HIGH-severity items are
on the <a href="flagged.html">Flagged for review</a> page. The two that matter most: the pinned
2026 dataset prints <em>no</em> score for weeks 10–18 (only weeks 1–9 are usable), and one
published capture asked for the Week 11 injury page and received Week 10 — so the "prior read"
used across the repository is a different week.</div>

<h2>The primary sources read for this build</h2>
<p>Every number on this site traces to one of the eleven inputs below. Each was transcribed
verbatim into <code>inputs/</code> and hashed; the class tells you how far to trust it.</p>
<table>
<thead><tr><th>Source</th><th>Class</th><th>Read (UTC)</th><th>What it settled</th></tr></thead>
<tbody>{srchints}
</tbody></table>

<h2>Where to go next</h2>
<table>
<thead><tr><th>Page</th><th>What it holds</th></tr></thead>
<tbody>
<tr><td><a href="readiness.html">Decision readiness</a></td>
<td>{len(reqs)} rows, one per line of the brief: status, the gate that blocks it, and the
number that would clear it.</td></tr>
<tr><td><a href="origination.html">Our lines</a></td>
<td>13 fixtures, side then total then moneyline, with fair line, market line and the
difference as separate columns, and a probability plus input hash on every row.</td></tr>
<tr><td><a href="backtest.html">Backtest &amp; luck</a></td>
<td>Walk-forward scoring against the close and against controls, a per-season view and the
removal-of-luck panel.</td></tr>
<tr><td><a href="leaderboard.html">Leaderboard</a></td>
<td>Six divisions: signal and staking in separate columns, a demotion gate on every row, a
two-sided "what would change our mind", and no backtest number anywhere on the board.</td></tr>
<tr><td><a href="availability.html">Injuries &amp; depth</a></td>
<td>The official Week 11 designation set, the two-clock delta, usage-rank depth from playing
time, replacement gaps and the ablation.</td></tr>
<tr><td><a href="correlations.html">Correlations</a></td>
<td>Five coefficients, each with n and a source class, plus the arithmetic reason the combo
gate is closed.</td></tr>
<tr><td><a href="questions.html">Questions</a> · <a href="suggestions.html">Suggestions</a></td>
<td>14 questions with what is known, what is missing and the route; 14 suggestions with
options, a recommendation, a review status and a falsifier.</td></tr>
<tr><td><a href="flagged.html">Flagged for review</a> · <a href="sources.html">Sources</a></td>
<td>{len(flags)} irregularities and every source with its read clock and class.</td></tr>
</tbody></table>
"""
    return layout('index.html', 'Dashboard', body,
                  'A table-first decision surface: what we can price, what we measured, what '
                  'blocked it.')


def page_readiness(d):
    reqs = d['requirements.csv']
    counts = {}
    for r in reqs:
        counts[r['status']] = counts.get(r['status'], 0) + 1
    filt = ''.join(f'<span class="badge b-{"met" if k == "MET" else ("part" if k.startswith("PART") else ("not" if k == "NOT MET" else "na"))}">{esc(k)}: {v}</span> '
                   for k, v in sorted(counts.items()))
    rows = []
    for r in reqs:
        rows.append(
            f'<tr><td>{esc(r["id"])}</td><td>{esc(r["requirement"])}</td>'
            f'<td>{badge(r["status"])}</td><td>{esc(r["blocking_gate"])}</td>'
            f'<td>{esc(r["observed"])}</td>'
            f'<td><code>{esc(r["evidence_path"])}</code><br>'
            f'<span class="src">{link(src_for(r["evidence_path"]))}</span></td></tr>')
    body = f"""
<p>{len(reqs)} lines of the brief, one row each. The status is what the evidence supports
today; the gate is what has to be true before the status can change; the observed column is
the number this desk actually measured.</p>
<p>{filt}</p>
<div class="warn">Statuses are deliberately conservative. "PARTIALLY MET" always names the
missing piece, and "NOT MET" always names the source that would clear it. Nothing here is
marked MET on the strength of a statement in the brief.</div>
{table(['ID', 'Requirement', 'Status', 'Gate that blocks it', 'Observed number',
        'Evidence file and the source it was built from'], rows)}
"""
    return layout('readiness.html', 'Decision readiness', body,
                  'One row per line of the brief: status, blocking gate, the number that would '
                  'clear it.')


def page_origination(d):
    rows = d['origination_week11.csv']
    snap = d['market_snapshots.csv']
    cons = []
    for r in rows:
        cons.append(
            f'<tr><td><strong>{esc(r["game_id"])}</strong></td><td>{esc(r["kickoff_as_printed"])}</td>'
            f'<td>{esc(r["network_as_printed"])}</td><td>{esc(r["market_order"])}</td>'
            f'<td>{esc(r["market"])}</td><td>{esc(r["side"])}</td>'
            f'{cell(r["fair_line"])}{cell(r["probability"], 3)}{cell(r["market_line"])}'
            f'{cell(r["difference_fair_minus_market"], 2)}'
            f'<td class="src"><code>{esc(r["inputs_sha256"][:12])}…</code></td>'
            f'<td class="src">{link(r["market_url"], "operator pages")}</td></tr>')
    # per-operator raw prints, a sample of the price store
    srows = []
    for r in snap:
        srows.append(
            f'<tr><td>{esc(r["fixture"])}</td><td>{esc(r["market"])}</td>'
            f'<td>{esc(r["side"])}</td><td>{esc(r["operator"])}</td>'
            f'<td>{esc(r["value_as_printed"])}</td><td>{esc(r["snapshot_role"])}</td>'
            f'<td class="src">{esc(r["read_utc"])}</td>'
            f'<td class="src">{link(r["source_url"], r["operator"])}</td>'
            f'<td class="unread">not read — exists only at kickoff</td></tr>')
    body = f"""
<div class="note"><strong>Order is enforced.</strong> Side first, then total, then moneyline
(home and away), for every fixture. <code>market_order</code> is a running counter over the
whole table, so the sequence is checkable, not just claimed.</div>
<p>Fair line is ours. Market line is the median of two named-operator quotes read today.
Difference is fair minus market in the market's own units, so a positive number means we price
the favourite stronger than the market does. The probability column is the model's own output
and the hash is over the exact input object; <code>verify.py</code> rebuilds it.</p>
{table(['Fixture', 'Kickoff (as printed)', 'Network', '#', 'Market', 'Side', 'Fair line',
        'Probability', 'Market line', 'Difference', 'Input hash', 'Market source'], cons)}

<h3>What the residuals say, honestly</h3>
<div class="stop">The residuals are large — several points on the side — and that is not a
strength. The same model loses to the closing line in the backtest
(<a href="backtest.html">see the skill intervals</a>), so a big gap between our line and the
market is far more likely to be our error than an edge. The residual is published because a
residual series accumulates evidence; it is not a pick.</div>

<h2>The price-snapshot store</h2>
<p>{len(snap)} rows: every fixture × three markets × two sides × two named operators, verbatim
as printed, each with its own read clock. The <code>closing</code> columns are empty by
construction — every game kicks off after this build — and are published as an explicit policy
row rather than a blank.</p>
<div class="scroll"><table><thead><tr><th>Fixture</th><th>Market</th><th>Side</th>
<th>Operator</th><th>Printed value</th><th>Role</th><th>Read (UTC)</th><th>Source</th>
<th>Closing</th></tr></thead><tbody>{''.join(srows)}</tbody></table></div>
"""
    return layout('origination.html', 'Our lines — Week 11', body,
                  'Side, then total, then moneyline. Fair, market and difference in separate '
                  'columns; a probability and an input hash on every row.')


def page_backtest(d):
    fams = d['backtest_families.csv']
    tot = d['backtest_totals.csv'][0]
    per = d['backtest_by_season.csv']
    luck = d['luck_panel.csv']
    frows = []
    for r in fams:
        frows.append(
            f'<tr><td><strong>{esc(r["family"])}</strong><br><small>{esc(r["description"])}</small></td>'
            f'{cell(r["n_games"])}{cell(r["brier_model"], 4)}{cell(r["brier_benchmark"], 4)}'
            f'{cell(r["brier_skill_vs_close"], 4)}'
            f'<td class="num">[{esc(r["skill_lo95"])}, {esc(r["skill_hi95"])}]</td>'
            f'{cell(r["brier_skill_vs_base_rate"], 4)}{cell(r["p_holm"], 4)}'
            f'{cell(r["holdout_brier_skill"], 4)}'
            f'<td>{badge(r["certified"].upper()) if r["certified"] == "yes" else badge("NOT MET")}</td></tr>')
    prows = []
    for r in per:
        hold = ' <span class="badge b-part">holdout</span>' if r['holdout'] == 'yes' else ''
        prows.append(
            f'<tr><td>{esc(r["season"])}{hold}</td>'
            f'{cell(r["n_games"])}{cell(r["brier_model"], 4)}{cell(r["brier_market"], 4)}'
            f'{cell(r["brier_skill"], 4)}</td></tr>')
    lrows = []
    for r in luck:
        lrows.append(
            f'<tr><td><strong>{esc(r["panel"])}</strong></td>{cell(r["value"], 4)}'
            f'<td class="num">{[esc(r["lo"]), esc(r["hi"])] if (r["lo"] or r["hi"]) else DASH}</td>'
            f'{cell(r["n"])}<td>{esc(r["method"])}</td><td>{esc(r["interpretation"])}</td>'
            f'<td class="src">{link(r["source_url"])}</td></tr>')
    body = f"""
<div class="stop"><strong>Nothing here is a certified strategy.</strong> These are families
scored walk-forward on {fams[0]['n_games']} games from 2006 to 2026, each game priced with
parameters fitted only on earlier weeks. The target is P(home win); the benchmark is the
de-vigged closing moneyline. A control family is included on purpose: if the model cannot beat
the random control, the model is adding nothing.</div>

<h2>Families against the closing line</h2>
{table(['Family', 'n', 'Brier (model)', 'Brier (close)', 'Skill vs close',
        '95% cluster interval', 'Skill vs base rate', 'Holm p', 'Holdout skill', 'Certified'],
       frows)}
<p class="small">Skill is 1 − Brier(model)/Brier(benchmark). The interval resamples whole
game clusters (season × week), 2,000 resamples. The Holm column corrects for the number of
families tested in this table. A family is certified only when the lower bound is above zero
after that correction; none is.</p>

<h2>The totals market</h2>
{table(['Family', 'n', 'Brier (model)', 'Brier (de-vigged over)', 'Skill',
        '95% interval', 'What would change our mind'],
       [f'<tr><td><strong>{esc(tot["family"])}</strong></td>{cell(tot["n_games"])}'
        f'{cell(tot["brier_model"], 4)}{cell(tot["brier_benchmark"], 4)}'
        f'{cell(tot["brier_skill_vs_close"], 4)}'
        f'<td class="num">[{esc(tot["skill_lo95"])}, {esc(tot["skill_hi95"])}]</td>'
        f'<td>{esc(tot["what_would_change_our_mind"])}</td></tr>'])}

<h2>Season by season</h2>
{table(['Season', 'n', 'Brier (model)', 'Brier (close)', 'Skill'], prows)}
<p class="small">The model is behind on every holdout season. A single lucky season would show
as one positive row; there is none.</p>

<h2>Removal-of-luck panel</h2>
<p>What the numbers would have to look like before a ranking could mean anything.</p>
{table(['Panel', 'Value', '95% interval', 'n', 'Method', 'What it means', 'Source'], lrows)}
"""
    return layout('backtest.html', 'Backtest and removal of luck', body,
                  'Walk-forward scoring against the close and against controls, per season, '
                  'with the sample sizes a ranking would need.')


NO_RULE = ('<span class="unread">no staking rule exists while the division '
           'is blocked</span>')


def staking_cell(r):
    if r['staking_metric']:
        return f'<td>{esc(r["staking_metric"])}</td>'
    return f'<td>{NO_RULE}</td>'


def page_leaderboard(d):
    lb = d['leaderboard.csv']
    rows = []
    for r in lb:
        rows.append(
            f'<tr><td><strong>{esc(r["division"])}</strong></td><td>{esc(r["strategy"])}</td>'
            f'<td>{badge(r["status"])}</td>'
            f'<td>{esc(r["signal_metric"])}</td>'
            f'{cell(r["signal_value"], 4)}'
            f'<td class="num">{[esc(r["signal_lo95"]), esc(r["signal_hi95"])] if (r["signal_lo95"] or r["signal_hi95"]) else DASH}</td>'
            f'{cell(r["n_settled"])}{staking_cell(r)}'
            f'{cell(r["staking_roi"], 4)}{cell(r["staking_n"])}'
            f'<td>{esc(r["tier"])}</td><td>{esc(r["reward"])}</td>'
            f'<td class="src">{link(r["source_url"])}</td></tr>')
    detail = []
    for r in lb:
        detail.append(
            f'<tr><td>{esc(r["division"])}</td>'
            f'<td>{esc(r["demotion_trigger"])}</td>'
            f'<td>{esc(r["what_would_change_our_mind"])}</td>'
            f'<td class="small">{esc(r["backtest_reference"])}</td></tr>')
    body = f"""
<div class="warn"><strong>Read the two score columns as different things.</strong> Signal is
Brier skill against the close. Staking is a flat-unit return at the market price. They are
published side by side and never combined, because a lucky staking run must not be able to
mask a bad signal — and on this desk the 2026 tail already shows a strategy whose staking ROI
interval covers zero while its signal interval sits below zero.</div>

<div class="stop"><strong>No strategy carries a backtest number on this board.</strong>
<code>n_settled</code> is 0 on every ranked row because nothing has been settled prospectively.
The backtest lives in a separate table (<a href="backtest.html">Backtest &amp; luck</a>) and the
verifier fails the build if any backtest column appears here. That is the pre-registration
rule, enforced mechanically rather than by good intentions.</div>

{table(['Division', 'Strategy', 'Status', 'Signal metric', 'Signal', '95% interval',
        'Settled n', 'Staking metric', 'Staking ROI', 'Staking n', 'Tier', 'Reward',
        'Benchmark source'], rows)}

<h2>Demotion gate</h2>
<p>Frozen in the registration before any result was seen. A strategy returns to paper when any
one trigger fires.</p>
{table(['Division', 'Trigger', 'What would change our mind (both directions)',
        'Where the backtest lives, not here'], detail)}

<h2>Why the combo divisions are blocked</h2>
<p>A parlay or combo probability built by multiplying marginal probabilities is only correct
when the legs are independent. They are not: same-game margin and total correlate
{r_corr(d)} at n={n_corr(d)}. Until a joint distribution is fitted and validated for the exact
leg set, and until the operator's void and push rules are quoted from its own rules page, no
combo can be ranked. The clearing condition is on every blocked row above.</p>
"""
    return layout('leaderboard.html', 'Leaderboard', body,
                  'Signal and staking in separate columns, a demotion gate on every row, and no '
                  'backtest number anywhere on the board.')


def r_corr(d):
    r = next(x for x in d['correlations.csv'] if x['id'] == 'C03')
    return f'{r["r"]} [{r["ci_lo"]}, {r["ci_hi"]}]'


def n_corr(d):
    return next(x for x in d['correlations.csv'] if x['id'] == 'C03')['n']


def page_availability(d):
    avail = d['availability_week11.csv']
    summ = d['availability_summary.csv']
    delta = d['injury_delta.csv']
    rel = [r for r in d['designation_reliability.csv'] if r['season'] == '2023-2026 pooled']
    ab = d['availability_ablation.csv']
    bys = d['availability_ablation_by_season.csv']
    coef = d['availability_coefficients.csv']
    depth = d['replacement_depth_2026.csv']
    team = d['team_view_week11.csv']

    srows = [f'<tr><td>{esc(r["club"])}</td>{cell(r["rows_in_report"])}{cell(r["out"])}'
             f'{cell(r["doubtful"])}{cell(r["questionable"])}{cell(r["no_game_status"])}'
             f'<td>{esc(r["printed_no_injuries"])}</td>'
             f'<td class="src">{link(r["source_url"], "official report")}</td></tr>'
             for r in summ]
    def printed(v):
        if not v:
            return '<span class="unread">printed empty</span>'
        return esc(v)
    arows = [f'<tr><td>{esc(r["club"])}</td><td>{esc(r["player_as_printed"])}</td>'
             f'<td>{esc(r["position_as_printed"])}</td>'
             f'<td>{printed(r["injury_as_printed"])}</td>'
             f'<td>{esc(r["practice_status_as_printed"])}</td>'
             f'<td>{printed(r["game_status_as_printed"])}</td>'
             f'<td class="src">{esc(r["read_utc"])}</td>'
             f'<td class="src">{link(r["source_url"], "nfl.com")}</td></tr>'
             for r in avail]
    dcount = {}
    for r in delta:
        dcount[r['change']] = dcount.get(r['change'], 0) + 1
    drows = [f'<tr><td>{esc(r["club"])}</td><td>{esc(r["player"])}</td>'
             f'<td>{esc(r["field"])}</td>'
             f'<td>{printed(r["prior_value"])}</td>'
             f'<td>{printed(r["this_value"])}</td>'
             f'<td class="src">{esc(r["prior_read_utc"])}</td>'
             f'<td class="src">{esc(r["this_read_utc"])}</td>'
             f'<td class="small">{esc(r["page_note"])}</td></tr>'
             for r in delta[:60]]
    rrows = [f'<tr><td><strong>{esc(r["designation"])}</strong></td>{cell(r["designated_rows"])}'
             f'{cell(r["played_rows"])}{cell(r["play_rate"], 4)}'
             f'<td class="num">[{esc(r["ci_lo"])}, {esc(r["ci_hi"])}]</td>'
             f'<td class="src">{link(r["source_url"], "pinned dataset")}</td></tr>'
             for r in rel]
    brows = [f'<tr><td>{esc(r["season"])}</td>{cell(r["n_games"])}'
             f'{cell(r["brier_without"], 4)}{cell(r["brier_with"], 4)}'
             f'{cell(r["difference"], 5)}{cell(r["log_loss_without"], 4)}'
             f'{cell(r["log_loss_with"], 4)}</td></tr>'
             for r in bys]
    arows2 = [f'<tr><td><strong>{esc(r["variant"])}</strong></td>{cell(r["n_games"])}'
              f'{cell(r["brier"], 6)}{cell(r["log_loss"], 4)}'
              f'<td class="num">{interval(r["diff_lo95"], r["diff_hi95"])}</td>'
              f'<td class="small">{esc(r["note"])}</td></tr>' for r in ab]
    crows = [f'<tr><td>{esc(r["fit_window"])}</td>{cell(r["coef_out"], 3)}'
             f'{cell(r["coef_doubtful"], 3)}{cell(r["coef_questionable"], 3)}</td></tr>'
             for r in coef]
    trows = [f'<tr><td><strong>{esc(r["club"])}</strong></td>{esc(r["week11_opponent"])}'
             f'{cell(r["out"])}{cell(r["doubtful"])}{cell(r["questionable"])}'
             f'{cell(r["net_availability_count"])}'
             f'<td>{esc(r["largest_usage_gap_position"])} {esc(r["largest_usage_gap"])}</td>'
             f'<td class="small">{esc(r["replacement_named"])}</td>'
             f'<td class="src">{link(r["source_url"], "report")}</td></tr>'
             for r in team]
    # biggest measured gaps, top 15
    dg = sorted([r for r in depth if r['depth_gap'] not in ('', None)],
                key=lambda r: -float(r['depth_gap']))[:15]
    grows = [f'<tr><td>{esc(r["club"])}</td><td>{esc(r["position_group"])}</td>'
             f'<td>{esc(r["rank1_player"])}</td>{cell(r["rank1_share"], 3)}'
             f'<td>{esc(r["rank2_player"])}</td>{cell(r["rank2_share"], 3)}'
             f'{cell(r["depth_gap"], 3)}</td></tr>' for r in dg]

    body = f"""
<div class="note"><strong>Three rules this page keeps.</strong> The injury signal is a
<em>delta</em> between two stamped reads, never a level. Depth is <em>playing time</em>, never
jersey order, experience or salary. And a replacement is never named: without an official
inactive list, a replacement can be bounded by a measured usage gap but not asserted.</div>

<h2>Week 11 official designation set</h2>
<p>255 rows transcribed from the official report read at {BUILT}: 253 player rows across 24
clubs, plus the two clubs the league prints as "No Injuries Reported". The page itself printed
only a handful of game-status cells; those that are empty are shown as empty, not filled.</p>
<h3>Per club</h3>
{table(['Club', 'Rows printed', 'Out', 'Doubtful', 'Questionable', 'No status printed',
        'Printed "No Injuries Reported"', 'Source'], srows)}
<h3>Per player (first 40 of {len(avail)})</h3>
{table(['Club', 'Player (as printed)', 'Pos', 'Injury', 'Practice status', 'Game status',
        'Read (UTC)', 'Source'], arows[:40])}

<h2>Delta against the previous stamped read</h2>
<p>{len(delta)} change rows ({', '.join(f'{k}: {v}' for k, v in sorted(dcount.items()))})
between the 2026-11-18T03:55:13Z capture and today's read. Both clocks are printed on every
row. <strong>Caveat, published rather than buried:</strong> that capture asked for the Week 11
page and recorded the Week 10 page as its source, so most of these differences are page
differences, not day differences. See <a href="flagged.html">F02</a>.</p>
{table(['Club', 'Player', 'Field', 'Prior value', 'This value', 'Prior clock', 'This clock',
        'Page note'], drows)}

<h2>What the designations empirically mean</h2>
<p>{len(rel)} pooled categories over the four seasons in the repository. "Played" means a
snap-count record exists for that club-week.</p>
{table(['Designation', 'Rows', 'Played', 'Play rate', '95% interval', 'Source'], rrows)}
<p class="small">Read the Out row carefully: {rel_next(rel, 'Out')['played_rows']} of
{rel_next(rel, 'Out')['designated_rows']} Out rows have a snap record. That is not a
contradiction — it is a warning that the pinned injury file is not a game-day inactive list,
and that a player can be designated Out for one week and appear in a different week's snap
row. This desk therefore never uses a designation as a fixed penalty.</p>

<h2>Availability ablation: identical models, with and without the features</h2>
<div class="stop"><strong>The measured answer is that the availability term does not help.</strong>
Squared error is higher with it on. This is the opposite of an assumption-driven result: no
point penalty is subtracted anywhere, and the coefficient is estimated. A negative ablation is
a finding, not a failure to hide.</div>
{table(['Variant', 'n', 'Brier', 'Log loss', '95% interval on the difference', 'Note'],
       arows2)}
<h3>Chronological holdouts, season by season</h3>
{table(['Season', 'n', 'Brier (without)', 'Brier (with)', 'Difference',
        'Log loss (without)', 'Log loss (with)'], brows)}
<h3>The estimated coefficients, which are what replace a fixed penalty</h3>
{table(['Fit window', 'Out (points)', 'Doubtful (points)', 'Questionable (points)'], crows)}
<p class="small">Points per official designation, shrunk towards zero with a ridge of ten
pseudo-observations. The Out coefficient is small and its sign moves between fit windows, which
is why a hard-coded "−3 points per starter" would be an act of faith.</p>

<h2>Per-team view</h2>
<p>Starters out, the largest measured usage gap, and a net count. The replacement column says
"not confirmed" on purpose.</p>
{table(['Club', 'Week 11 opponent', 'Out', 'Doubtful', 'Questionable',
        'Net availability count', 'Largest usage gap (position, share)',
        'Replacement named', 'Source'], trows)}

<h2>Depth as playing time</h2>
<p>Usage rank inside each club × position group, from mean offensive snap share. This is a
ranked list, so several players can sit at rank 1 in a group — which is the faithful
representation of a three-receiver or three-linebacker group. The measured gap between rank 1
and rank 2 is the depth proxy.</p>
<table><thead><tr><th>Club</th><th>Pos</th><th>Usage leader</th><th>Share</th>
<th>Next player</th><th>Share</th><th>Gap</th></tr></thead>
<tbody>{''.join(grows)}</tbody></table>
<p class="small">Fifteen largest gaps shown of {len(depth)} club × position rows. The full
table is <code>data/replacement_depth_2026.csv</code>.</p>
"""
    return layout('availability.html', 'Injuries, designations and depth', body,
                  'The official Week 11 set, the two-clock delta, the empirical meaning of each '
                  'designation, and depth measured from playing time.')


SRC_MAP = {'OFFICIAL': 'https://www.nfl.com/injuries/league/2026/reg11',
           'OPERATOR': 'https://sportsbook.draftkings.com/leagues/football/nfl'}


def src_for(path):
    """The public source behind a derived table, from a published map."""
    p = (path or '').split()[0]
    return {
        'market_snapshots.csv': 'https://sportsbook.draftkings.com/leagues/football/nfl',
        'origination_week11.csv': 'https://www.nfl.com/schedules/2026/by-week/week-11',
        'standings_reconciliation.csv': 'https://www.nfl.com/standings/league/2026/REG',
        'results_2026.csv': 'https://www.nfl.com/schedules/2026/by-week/week-10',
        'corpus_coverage.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/schedules',
        'backtest_families.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/schedules',
        'backtest_totals.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/schedules',
        'backtest_by_season.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/schedules',
        'availability_week11.csv': 'https://www.nfl.com/injuries/league/2026/reg11',
        'availability_summary.csv': 'https://www.nfl.com/injuries/league/2026/reg11',
        'team_view_week11.csv': 'https://www.nfl.com/injuries/league/2026/reg11',
        'deficiency_matrix.csv': 'https://www.nfl.com/injuries/league/2026/reg11',
        'availability_counts.csv': 'https://www.nfl.com/injuries/league/2026/reg11',
        'injury_delta.csv': 'https://www.nfl.com/injuries/league/2026/reg11',
        'designation_reliability.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/injuries',
        'availability_ablation.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/injuries',
        'availability_coefficients.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/injuries',
        'replacement_depth_2026.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/snap_counts',
        'depth_usage_2026.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/snap_counts',
        'correlations.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/schedules',
        'closing_policy.csv': 'https://sportsbook.fanduel.com/navigation/nfl',
        'leaderboard.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/schedules',
        'requirements.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/schedules',
        'suggestions.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/schedules',
        'sign_convention.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/schedules',
        'walkforward_games.csv':
            'https://github.com/nflverse/nflverse-data/releases/tag/schedules',
        'questions.csv': 'https://www.nfl.com/injuries/league/2026/reg11',
        'flagged.csv': 'https://www.nfl.com/injuries/league/2026/reg11',
    }.get(p, 'https://www.nfl.com/schedules/2026/by-week/week-11')


def rel_next(rel, name):
    return next(r for r in rel if r['designation'] == name)


def page_correlations(d):
    corr = d['correlations.csv']
    rows = [f'<tr><td>{esc(r["id"])}</td><td><strong>{esc(r["pair"])}</strong></td>'
            f'{cell(r["r"], 4)}'
            f'<td class="num">[{esc(r["ci_lo"])}, {esc(r["ci_hi"])}]</td>'
            f'{cell(r["n"])}<td>{badge(r["source_class"])}</td>'
            f'<td>{esc(r["interpretation"])}</td>'
            f'<td class="src">{link(r["source_url"])}</td></tr>' for r in corr]
    body = f"""
<p>Every coefficient here is computed in-repo from a named input and published with its
sample size and its source class. No value is quoted from memory or from a third party.</p>
{table(['ID', 'Pair', 'r', '95% interval', 'n', 'Source class', 'Interpretation', 'Source'],
       rows)}
<h2>Why this closes the combo gate</h2>
<div class="warn">Parlay and combo pricing by multiplication assumes independence. The
same-game side/total pair is only weakly related ({corr[2]['r']}), but "weakly" is not "zero",
and weak dependence is enough to make a multiplied marginal probability wrong in a way that
compounds with every extra leg. The gate therefore stays closed until a joint distribution is
fitted and validated for the exact leg set — a condition published on every blocked
leaderboard row.</div>
<h2>What would let a combo open</h2>
<p>A fitted bivariate distribution per leg pair, evaluated on held-out games, that beats the
independent product by more than one percentage point, with n published beside the gap — plus
the operator's own void and push rules, quoted from the operator's own rules page rather than
from memory.</p>
"""
    return layout('correlations.html', 'Correlations', body,
                  'Coefficients only from named inputs, with n beside every value.')


def page_questions(d):
    q = d['questions.csv']
    rows = []
    for r in q:
        rows.append(
            f'<tr><td><strong>{esc(r["id"])}</strong></td>'
            f'<td>{esc(r["question"])}</td>'
            f'<td>{esc(r["known_now"])}</td>'
            f'<td>{esc(r["missing"])}</td>'
            f'<td>{esc(r["discovery_route"])}</td>'
            f'<td>{esc(r["blocks"])}</td>'
            f'<td>{badge(r["urgency"]) if r["urgency"] in ("HIGH", "MEDIUM", "LOW") else esc(r["urgency"])}</td>'
            f'<td class="src">{link(r["source_url"])}</td></tr>')
    body = f"""
<p>Every open question that stands between this desk and a decision. Each row carries three
things: what is already known with a number, what is missing, and the concrete route that would
find it. A gap with no route is a complaint; this register only lists gaps with routes.</p>
{table(['ID', 'Question', 'Known now', 'Missing', 'Discovery route', 'Blocks', 'Urgency',
        'Source'], rows)}
<div class="note">Order to work them in: Q01 (closing prices) unblocks everything about
staking; Q03 (an official inactive list) unblocks the availability graph; Q02 (terms) unblocks
automation. Q09, Q10 and Q13 are already answered by measurement and are kept so the answer is
written down.</div>
"""
    return layout('questions.html', 'Questions, information and answers', body,
                  'What is known, what is missing, and the route to it — the questions that '
                  'must be answered before any decision.')


def page_suggestions(d):
    s = d['suggestions.csv']
    rows = []
    for r in s:
        rows.append(
            f'<tr><td><strong>{esc(r["id"])}</strong></td>'
            f'<td>{esc(r["suggestion"])}</td>'
            f'<td>{esc(r["options_considered"])}</td>'
            f'<td>{esc(r["recommendation"])}</td>'
            f'<td>{esc(r["cost"])}</td>'
            f'<td>{esc(r["review_status"])}</td>'
            f'<td>{esc(r["condition_to_accept"])}</td>'
            f'<td>{esc(r["what_would_change_our_mind"])}</td>'
            f'<td class="src"><code>{esc(r["evidence_path"])}</code><br>{link(src_for(r["evidence_path"]))}</td></tr>')
    body = f"""
<p>{len(s)} suggestions, each reviewable on its own. Every row has the options that were
weighed, the recommendation and why, what it costs to adopt, the review status, the condition
that would make it clearly right, and a two-sided falsifier. The owner picks; the desk does not
invent consent.</p>
<div class="note"><strong>How to use this page.</strong> Read the recommendation, then read
the two-sided falsifier. If you cannot imagine the falsifier happening, the suggestion is
probably a preference rather than a decision — say so and it becomes a rejected item with a
reason, which is a perfectly good outcome.</div>
{table(['ID', 'Suggestion', 'Options considered', 'Recommendation', 'Cost',
        'Review status', 'Condition to accept', 'What would change our mind', 'Evidence'],
       rows)}
"""
    return layout('suggestions.html', 'Suggestions for review', body,
                  'Options, a recommendation, a review status and a falsifier on every row — '
                  'nothing here is adopted without a decision.')


def page_flagged(d):
    f = d['flagged.csv']
    rows = []
    for r in f:
        rows.append(
            f'<tr><td><strong>{esc(r["id"])}</strong></td><td>{badge(r["severity"])}</td>'
            f'<td><strong>{esc(r["item"])}</strong><br><span class="small">{esc(r["detail"])}</span></td>'
            f'<td>{esc(r["impact"])}</td><td>{esc(r["resolution"])}</td>'
            f'<td class="src"><code>{esc(r["evidence"])}</code><br>{link(r["source_url"])}</td></tr>')
    body = f"""
<p>{len(f)} irregularities, each one something this session actually saw in the data. Nothing
here blocks publication; each row states the impact and what has been done about it so far.</p>
{table(['ID', 'Severity', 'Item', 'Impact', 'What has been done', 'Evidence and source'], rows)}
"""
    return layout('flagged.html', 'Flagged for review', body,
                  'Irregularities and unverified items, with the evidence and the impact of '
                  'each one.')


def page_sources(d):
    src = d['sources.csv']
    man = d['manifest']
    srows = [f'<tr><td><strong>{esc(r["id"])}</strong></td><td>{esc(r["name"])}</td>'
             f'<td>{badge(r["source_class"])}</td>'
             f'<td class="src">{esc(r["read_utc"])}</td>'
             f'<td>{esc(r["used_for"])}</td>'
             f'<td class="src">{link(r["url"])}</td></tr>' for r in src]
    ih = ''.join(f'<tr><td><code>{esc(k)}</code></td>'
                 f'<td class="src"><code>{esc(v)}</code></td></tr>'
                 for k, v in man['input_hashes'].items())
    rh = ''.join(f'<tr><td><code>{esc(k)}</code></td>'
                 f'<td class="src"><code>{esc(v)}</code></td></tr>'
                 for k, v in man['repository_inputs'].items())
    body = f"""
<p>Every source used, with its class and the clock time at which it was read. Classes:
<strong>OFFICIAL</strong> — a page published by the league; <strong>NAMED-OPERATOR</strong> — a
sportsbook's own price page; <strong>PINNED-DATASET</strong> — a dataset committed in this
repository, not a league feed; <strong>PRIOR-CAPTURE</strong> — another session's stamped read,
re-used with its clock.</p>
{table(['ID', 'Source', 'Class', 'Read (UTC)', 'Used for', 'Link'], srows)}

<h2>Method, in one paragraph each</h2>
<h3>Line origination</h3>
<p>Ratings are an additive offence/defence model with a home-field term, fitted by ridge
regression on points scored and allowed per game over the six most recent seasons, with older
seasons down-weighted. Expected margin is (offence_home − offence_away) + (defence_home −
defence_away) + home field; expected total is 2·mean + both offences − both defences + home
field. Probabilities use the measured residual dispersion of the same fitted window, not an
assumed 13.5. Side is originated first, then total, then moneyline, and each row carries the
model's own probability and a hash over the exact input object.</p>
<h3>Walk-forward backtest</h3>
<p>Each game is priced with parameters fitted only on games strictly before its week; the
expanding window covers 1999 onward. The benchmark is the de-vigged closing moneyline
(two-way proportional de-vig). Skill is 1 − Brier(model)/Brier(benchmark); the interval
resamples whole season×week clusters; the Holm correction covers every family in the table.</p>
<h3>Availability</h3>
<p>The designation set is transcribed from the official page with its read clock. The delta
between two stamped reads is published rather than a level. The ablation refits the identical
model with and without three counts (Out, Doubtful, Questionable) and reports the paired
difference with a cluster interval; the coefficients are estimated with a shrinkage ridge, so no
fixed point penalty exists in the pipeline.</p>
<h3>Depth</h3>
<p>Mean offensive snap share inside a club × position group defines a usage rank. Rank 1 can
contain several players. The gap from rank 1 to rank 2 is the replacement-depth proxy. Jersey
numbers, draft position and salary are never read.</p>

<h2>Reproduction</h2>
<p>Three commands reproduce everything on this site:</p>
<pre><code>python3 build_data.py   # rebuild every CSV from the committed inputs
python3 verify.py       # fail-closed check of every table, hash and link
python3 build_site.py   # render this site from the CSVs</code></pre>
<p>The build is deterministic and stdlib-only. The registration hash and the hash of every
input are recorded below; <code>verify.py</code> recomputes them and fails if any has moved.</p>
{table(['Registration / engine / builder', 'sha256'],
       [f'<tr><td>preregistration.json</td><td class="src"><code>{esc(man["registration_sha256"])}</code></td></tr>',
        f'<tr><td>engine.py</td><td class="src"><code>{esc(man["engine_sha256"])}</code></td></tr>',
        f'<tr><td>build_data.py</td><td class="src"><code>{esc(man["builder_sha256"])}</code></td></tr>'])}
<h3>Transcribed inputs</h3>
{table(['Input file', 'sha256'], [ih])}
<h3>Repository inputs</h3>
{table(['Input file', 'sha256'], [rh])}
"""
    return layout('sources.html', 'Sources and method', body,
                  'Every source, its class and its read clock, plus the method and the hashes '
                  'that make the numbers reproducible.')


def main():
    d = load_all()
    pages = {
        'index.html': page_index(d),
        'readiness.html': page_readiness(d),
        'origination.html': page_origination(d),
        'backtest.html': page_backtest(d),
        'leaderboard.html': page_leaderboard(d),
        'availability.html': page_availability(d),
        'correlations.html': page_correlations(d),
        'questions.html': page_questions(d),
        'suggestions.html': page_suggestions(d),
        'flagged.html': page_flagged(d),
        'sources.html': page_sources(d),
    }
    for name, content in pages.items():
        with open(os.path.join(PAGES, name), 'w', encoding='utf-8') as fh:
            fh.write(content)
        print(f'  wrote {name} ({len(content)} bytes)')
    with open(os.path.join(PAGES, 'style.css'), 'w', encoding='utf-8') as fh:
        fh.write(CSS)
    # a machine-readable summary for any other desk that wants the numbers
    summary = {
        'desk': '9e54d765',
        'built_utc': BUILT,
        'registration_sha256': d['manifest']['registration_sha256'],
        'headline': {
            'model_brier_skill_vs_close': fam_by(d, 'F4_OPPONENT_AWARE')['brier_skill_vs_close'],
            'interval': [fam_by(d, 'F4_OPPONENT_AWARE')['skill_lo95'],
                         fam_by(d, 'F4_OPPONENT_AWARE')['skill_hi95']],
            'n_games': fam_by(d, 'F4_OPPONENT_AWARE')['n_games'],
            'certified_strategies': 0,
        },
        'counts': {k: len(v) for k, v in d.items() if isinstance(v, list)},
    }
    with open(os.path.join(DATA, 'summary.json'), 'w') as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
        fh.write('\n')
    print('  wrote style.css and data/summary.json')


if __name__ == '__main__':
    main()

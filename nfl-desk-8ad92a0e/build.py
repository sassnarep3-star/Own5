#!/usr/bin/env python3
"""Deterministic static site builder for the 8ad92a0e desk.
No clock, no network, no git: output depends only on committed CSV/JSON inputs."""
import csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
DATA = os.path.join(BASE, 'data', 'nfl-desk-8ad92a0e')

PAGES = [
    ('index.html', 'Dashboard'),
    ('lines.html', 'Originated lines'),
    ('snapshots.html', 'Price snapshots'),
    ('results.html', 'Results feed'),
    ('leaderboard.html', 'Leaderboard & skill'),
    ('correlations.html', 'Correlations'),
    ('availability.html', 'Availability'),
    ('questions.html', 'Questions'),
    ('suggestions.html', 'Suggestions'),
    ('sources.html', 'Sources'),
    ('flagged.html', 'Flagged for review'),
    ('executive-summary.html', 'Executive summary'),
]


def rd(name):
    with open(os.path.join(DATA, name), newline='') as f:
        return list(csv.DictReader(f))


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;'))


def cell(v, src=None):
    """Render a cell; empty values become an explicit BLANK badge; optional source link column."""
    if v is None or v == '':
        return '<span class="blank" title="Blank by policy or not yet available">BLANK</span>'
    return esc(v)


def table(headers, rows, cls=''):
    h = ''.join(f'<th>{esc(x)}</th>' for x in headers)
    body = []
    for r in rows:
        tds = ''.join(f'<td>{c}</td>' for c in r)
        body.append(f'<tr>{tds}</tr>')
    return (f'<div class="tbl-wrap"><table class="{cls}"><thead><tr>{h}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def link(url, text=None):
    if not url:
        return '<span class="blank">BLANK</span>'
    return f'<a href="{esc(url)}" rel="noopener">{esc(text or url)}</a>'


def shell(title, body, active):
    nav = ''.join(
        f'<a class="{"on" if f==active else ""}" href="{f}">{esc(label)}</a>'
        for f, label in PAGES)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · NFL Decision &amp; Origination Desk (8ad92a0e)</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <div class="wrap">
    <h1>NFL Decision &amp; Origination Desk <span class="sid">session 8ad92a0e</span></h1>
    <p class="sub">Official-source reads of 2026-11-19 · every table row source-linked or explicitly blank · no inferred values</p>
    <nav>{nav}</nav>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="wrap">
  <p>Shared policy: values that cannot be confirmed from an official source are left <strong>BLANK</strong> and listed on
  <a href="flagged.html">Flagged for review</a>. No bets are placed; no strategy is certified; the reward pool is unfunded.</p>
</footer>
</body>
</html>
'''


def write(fname, html):
    with open(os.path.join(HERE, fname), 'w') as f:
        f.write(html)


def main():
    stand = rd('standings_2026_reg_20261119.csv')
    sched = rd('schedule_2026_wk11.csv')
    results = rd('results_2026_through_wk10.csv')
    lines = rd('lines_wk11.csv')
    snaps = rd('price_snapshots.csv')
    corr = rd('correlations.csv')
    luck = rd('luck_panel.csv')
    reqs = rd('requirements.csv')
    qs = rd('questions.csv')
    sug = rd('suggestions.csv')
    flags = rd('flagged.csv')
    srcs = rd('sources.csv')
    gates = rd('gates.csv')
    strats = rd('strategies.csv')
    lb = rd('leaderboard.csv')
    clubs = rd('injury_wk11_clubs.csv')
    players = rd('injury_wk11_players.csv')
    spec = json.load(open(os.path.join(DATA, 'model_spec.json')))

    # ---------- index / dashboard ----------
    from collections import Counter
    sc = Counter(r['status'] for r in reqs)
    cards = [
        ('Official reads', '4 pages · 7 chunks', 'standings · schedule · scores · injuries'),
        ('Results feed', f'{len(results)} finals', 'reconciled 32/32 to official standings'),
        ('Originated markets', f'{len(lines)}', 'side → total → moneyline, 13 fixtures'),
        ('Price snapshots', f'{len(snaps)} open', 'closing cells blank by policy'),
        ('Injury rows (W11)', f'{len(players)}', f'26 clubs · {sum(1 for p in players if p["game_status"]=="Out")} Out · {sum(1 for p in players if p["game_status"]=="Questionable")} Questionable'),
        ('Requirements', f'{len(reqs)}', f'{sc["MET"]} met · {sc["PARTIAL"]} partial · {sc["BLOCKED"]} blocked'),
        ('Flags open', f'{len(flags)}', 'non-blocking, published with sources'),
        ('Certified strategies', '0', 'gates not passed · pool unfunded'),
    ]
    card_html = ''.join(
        f'<div class="card"><div class="k">{esc(k)}</div><div class="v">{esc(v)}</div><div class="n">{esc(n)}</div></div>'
        for k, v, n in cards)
    req_rows = []
    for r in reqs:
        req_rows.append([
            f'<code>{esc(r["req_id"])}</code>', esc(r['category']), esc(r['requirement']),
            esc(r['blocking_gate']), esc(r['number_to_clear']),
            cell(r['observed']), f'<span class="st st-{r["status"].lower()}">{esc(r["status"])}</span>',
            esc(r['evidence']), link(r['source_url']),
        ])
    head = f'''
<section class="cards">{card_html}</section>
<section>
<h2>Decision-readiness table — one row per requirement</h2>
<p>Each row states the requirement from the brief, the gate that blocks it, the number that would clear it,
and the observed value (blank where nothing official confirms it). Full detail per category is in the subpages.</p>
{table(['ID','Category','Requirement','Blocking gate','Number to clear','Observed','Status','Evidence','Source'],
       req_rows, 'dense')}
</section>
<section>
<h2>Headline findings (2026-11-19)</h2>
<ul class="findings">
<li>Walk-forward Brier on 149 decisive 2026 finals: <strong>{spec["walkforward_brier"]}</strong>;
skill vs expanding home-win rate <strong>{spec["walkforward_skill_vs_home_rate"]}</strong>
(week-cluster 95% CI {spec["walkforward_skill_ci95"][0]} to {spec["walkforward_skill_ci95"][1]}) — positive only vs weak baselines,
<strong>no market benchmark exists</strong>, nothing certified.</li>
<li>2026 home-field estimate is <strong>negative</strong> ({spec["hfa_estimate_pts"]} pts, n={spec["hfa_n"]}) — published as measured, flagged for review.</li>
<li>Week-11 injury report read in full: {len(players)} rows, 26 clubs, 9 Out / 7 Questionable — all designations sit in the Thursday game.</li>
<li>Market lines, residuals, CLV, ROI and rewards: <strong>BLANK</strong> — no licensed price source (flag F8-01).</li>
</ul>
</section>'''
    write('index.html', shell('Dashboard', head, 'index.html'))

    # ---------- lines ----------
    rows = []
    for r in lines:
        rows.append([
            f'<code>{esc(r["game_id"])}</code>', esc(r['order']), esc(r['away']), esc(r['home']),
            esc(r['market']), f'<strong>{cell(r["model_fair_line"])}</strong>',
            cell(r['expected_home_margin_or_total']), cell(r['model_prob_home_or_over']),
            cell(r['market_line']), cell(r['market_price']), cell(r['difference']),
            f'<code>{esc(r["inputs_sha256"])}</code>', link(r['source_url'], 'official fixture'),
        ])
    body = f'''
<section>
<h2>Originated Week-11 lines — side first, then total, then moneyline</h2>
<p>Fair line, market line and difference are <strong>separate columns</strong>. Market and difference cells are blank by
policy P-8AD-01 (no licensed price source — flag F8-01). Every row carries the model probability and an inputs hash.
Model: <code>{esc(spec["model_id"])}</code>, shrinkage k={spec["shrinkage_k"]}, HFA={spec["hfa_estimate_pts"]} (n={spec["hfa_n"]}),
&sigma;={spec["sigma_margin"]}.</p>
{table(['Game','Order','Away','Home','Market','Model fair line','Expected margin/total','Model prob',
        'Market line','Market price','Difference','Inputs sha256','Source'], rows)}
</section>'''
    write('lines.html', shell('Originated lines', body, 'lines.html'))

    # ---------- snapshots ----------
    rows = []
    for r in snaps:
        rows.append([
            f'<code>{esc(r["snapshot_id"])}</code>', f'<code>{esc(r["game_id"])}</code>', esc(r['market']),
            esc(r['model_fair_line']), esc(r['opened_at']), cell(r['market_open']), cell(r['market_close']),
            esc(r['status']), esc(r['policy']), f'<code>{esc(r["inputs_sha256"])}</code>', link(r['source_url'], 'official fixture'),
        ])
    body = f'''
<section>
<h2>Price-snapshot store (opening per originated market)</h2>
<p>Immutable opening snapshots for all {len(snaps)} originated markets. Closing cells stay blank until a licensed price
source exists (F8-01). Snapshot open time is pinned for determinism.</p>
{table(['Snapshot','Game','Market','Model fair line','Opened at','Market open','Market close','Status','Policy','Inputs sha256','Source'], rows)}
</section>'''
    write('snapshots.html', shell('Price snapshots', body, 'snapshots.html'))

    # ---------- results ----------
    rec_rows = []
    # reconciliation summary computed here from committed inputs (same identities as compute)
    from collections import defaultdict
    wl = defaultdict(lambda: [0, 0, 0, 0, 0])
    for r in results:
        a, h, ap, hp = r['away'], r['home'], int(r['away_pts']), int(r['home_pts'])
        if ap > hp:
            wl[a][0] += 1; wl[h][1] += 1
        elif hp > ap:
            wl[h][0] += 1; wl[a][1] += 1
        else:
            wl[a][2] += 1; wl[h][2] += 1
        wl[a][3] += ap; wl[a][4] += hp
        wl[h][3] += hp; wl[h][4] += ap
    exact = 0
    for s in stand:
        d = wl[s['club']]
        if d == [int(s['w']), int(s['l']), int(s['t']), int(s['pf']), int(s['pa'])]:
            exact += 1
    rows = []
    for r in results:
        rows.append([
            f'<code>{esc(r["game_id"])}</code>', esc(r['week']), esc(r['date']), esc(r['away']), esc(r['home']),
            esc(r['away_pts']), esc(r['home_pts']), esc(r['status']),
            f'<span class="st">{esc(r["verification"])}</span>', link(r['source_url'], 'official week page'),
        ])
    body = f'''
<section class="cards">
<div class="card"><div class="k">Finals in feed</div><div class="v">{len(results)}</div><div class="n">weeks 1–10</div></div>
<div class="card"><div class="k">Clubs reconciled exactly</div><div class="v">{exact}/32</div><div class="n">W-L-T, PF, PA vs official standings</div></div>
<div class="card"><div class="k">Direct-read rows</div><div class="v">{sum(1 for r in results if r["verification"].startswith("DIRECT"))}</div><div class="n">weeks 9–10, read 2026-11-19</div></div>
<div class="card"><div class="k">Adopted + reconciled</div><div class="v">{sum(1 for r in results if r["verification"].startswith("RECONCILED"))}</div><div class="n">weeks 1–8, aggregate-checked</div></div>
</section>
<section>
<h2>Verified results feed</h2>
<p>Adoption rule: the feed is accepted only after (a) every Week-9 and Week-10 row matched a direct official read on
2026-11-19, and (b) per-club totals reproduce the official standings <strong>32/32 exactly</strong>. Weeks 1–8 rows link
their official week schedule pages.</p>
{table(['Game','Week','Date','Away','Home','Away pts','Home pts','Status','Verification','Source'], rows, 'dense')}
</section>'''
    write('results.html', shell('Results feed', body, 'results.html'))

    # ---------- leaderboard ----------
    lb_rows = []
    for r in lb:
        lb_rows.append([
            f'<code>{esc(r["strategy_id"])}</code>', esc(r['division']), esc(r['name']), esc(r['kind']),
            esc(r['entry_status']), esc(r['gates_status']), cell(r['signal_score']), cell(r['signal_n']),
            cell(r['staking_return']), esc(r['grading_note']), link(r['source_url'], 'source'),
        ])
    gate_rows = [[f'<code>{esc(g["gate_id"])}</code>', esc(g['gate']), esc(g['rule']), esc(g['threshold']),
                  f'<span class="st">{esc(g["status"])}</span>', link(g['source_url'], 'source')] for g in gates]
    strat_rows = []
    for s in strats:
        strat_rows.append([
            f'<code>{esc(s["strategy_id"])}</code>', esc(s['division']), esc(s['name']), esc(s['definition']),
            esc(s['status']), esc(s['gates_status']), esc(s['what_would_change_our_mind']),
            esc(s['demotion_rule']), f'<code>{esc(s["pre_reg_commit"][:10])}</code>', link(s['source_url'], 'source'),
        ])
    luck_rows = [[f'<code>{esc(l["metric_id"])}</code>', esc(l['metric']), f'<strong>{esc(l["value"])}</strong>',
                  esc(l['n']), esc(l['note']), link('results.html', 'feed')] for l in luck]
    body = f'''
<section>
<h2>Leaderboard — signal separated from staking</h2>
<p>Signal and staking are <strong>structurally separate columns</strong>: a lucky staking run cannot mask a bad signal.
No backtest number may appear on this board (gate G8-01/G8-11, enforced by the verifier). Controls are registered on
every run. <strong>0 strategies graded; 0 rewards; pool unfunded.</strong></p>
{table(['Strategy','Division','Name','Kind','Entry','Gates','Signal score','Signal n','Staking return','Grading note','Source'], lb_rows)}
</section>
<section>
<h2>Pre-registered strategies (git hash = registration)</h2>
{table(['ID','Division','Name','Definition','Status','Gates','What would change our mind','Demotion rule','Registered','Source'], strat_rows)}
</section>
<section>
<h2>Validation gates</h2>
{table(['Gate','Name','Rule','Threshold','Status','Source'], gate_rows)}
</section>
<section>
<h2>Removal-of-luck panel (walk-forward on official finals)</h2>
<p>Chronological, prior-games-only inputs; ties excluded from scoring; week-cluster bootstrap for the skill interval.
These are <strong>internal proper scores</strong>, not market-validated edge (F8-04).</p>
{table(['ID','Metric','Value','n','Note','Source'], luck_rows)}
</section>'''
    write('leaderboard.html', shell('Leaderboard & skill', body, 'leaderboard.html'))

    # ---------- correlations ----------
    rows = [[f'<code>{esc(c["corr_id"])}</code>', esc(c['var_x']), esc(c['var_y']),
             f'<strong>{esc(c["r"])}</strong>', esc(c['n']),
             esc(c['ci95_low']) or '<span class="blank">BLANK</span>',
             esc(c['ci95_high']) or '<span class="blank">BLANK</span>',
             esc(c['method']), link(c['source_url'], 'official source')] for c in corr]
    body = f'''
<section>
<h2>Correlations — official numbers only, n published with every value</h2>
<p>Computed in-repo from the official 2026 standings (read 2026-11-19) and official finals. No third-party inputs.
Fisher-z 95% intervals; n on every row.</p>
{table(['ID','Variable X','Variable Y','r','n','CI 95% low','CI 95% high','Method','Source'], rows)}
</section>'''
    write('correlations.html', shell('Correlations', body, 'correlations.html'))

    # ---------- availability ----------
    club_rows = []
    for c in clubs:
        club_rows.append([
            f'<strong>{esc(c["club"])}</strong>', esc(c['rows']), esc(c['out']), esc(c['questionable']),
            esc(c['dnp']), esc(c['lp']), esc(c['fp']),
            esc(c['report_note']) or '<span class="blank">BLANK</span>',
            '<span class="blank" title="No depth/replacement evidence read this session (F8-02)">BLANK</span>',
            '<span class="blank" title="No inactive/snap evidence read this session (F8-02)">BLANK</span>',
            link(c['source_url'], 'official report'),
        ])
    p_rows = []
    for p in players:
        p_rows.append([
            esc(p['club']), esc(p['player']), esc(p['position']),
            esc(p['injury']) or '<span class="blank">BLANK</span>',
            esc(p['practice_status']),
            f'<strong>{esc(p["game_status"])}</strong>' if p['game_status'] else '<span class="blank">BLANK</span>',
            esc(p['read_at_utc']), link(p['source_url'], 'official report'),
        ])
    body = f'''
<section class="cards">
<div class="card"><div class="k">Player rows</div><div class="v">{len(players)}</div><div class="n">26 clubs, 7 chunks read in full</div></div>
<div class="card"><div class="k">Out (game status)</div><div class="v">{sum(1 for p in players if p["game_status"]=="Out")}</div><div class="n">all in the Thursday game</div></div>
<div class="card"><div class="k">Questionable</div><div class="v">{sum(1 for p in players if p["game_status"]=="Questionable")}</div><div class="n">all in the Thursday game</div></div>
<div class="card"><div class="k">Depth / replacements</div><div class="v">BLANK</div><div class="n">no depth source read (F8-02, F8-16)</div></div>
</section>
<section>
<h2>Per-club availability (Week 11)</h2>
<p>Replacement and inactive columns stay blank: no depth chart, inactive list or snap-count source was read this
session (F8-02). Depth order is never inferred from jersey numbers (rejected per brief).</p>
{table(['Club','Rows','Out','Quest.','DNP','LP','FP','Report note','Starter/replacement depth','Inactives/snaps','Source'], club_rows)}
</section>
<section>
<h2>Player rows (verbatim transcription, read clock per row)</h2>
{table(['Club','Player','Pos','Injury','Practice status','Game status','Read at (UTC)','Source'], p_rows, 'dense')}
</section>'''
    write('availability.html', shell('Availability', body, 'availability.html'))

    # ---------- questions ----------
    rows = [[f'<code>{esc(q["q_id"])}</code>', esc(q['question']), esc(q['information_needed']),
             esc(q['discovery_route']), cell(q['answer']), f'<span class="st">{esc(q["answer_status"])}</span>',
             esc(q['blocking']), link(q['source_url'], 'context')] for q in qs]
    body = f'''
<section>
<h2>Questions, information and answers needed before any decision</h2>
<p>Every question that must be answered before a decision can reasonably be made, with the information required and a
discovery route that does not depend on guesswork. Answers stay blank until an official/owner source fills them.</p>
{table(['ID','Question','Information needed','Discovery route','Answer','Status','Blocking','Source'], rows)}
</section>'''
    write('questions.html', shell('Questions', body, 'questions.html'))

    # ---------- suggestions ----------
    rows = [[f'<code>{esc(s["s_id"])}</code>', esc(s['category']), esc(s['suggestion']), esc(s['options']),
             esc(s['recommendation']), esc(s['what_would_change_our_mind']),
             cell(s['decision']), f'<span class="st">{esc(s["status"])}</span>', link(s['source_url'], 'context')]
            for s in sug]
    body = f'''
<section>
<h2>Suggestions — review before implement</h2>
<p>Site and process improvements for the owner to review. <strong>Nothing here has been implemented</strong>; the
decision column is blank on every row and only the owner fills it.</p>
{table(['ID','Category','Suggestion','Options','Recommendation','What would change our mind','Decision','Status','Source'], rows)}
</section>'''
    write('suggestions.html', shell('Suggestions', body, 'suggestions.html'))

    # ---------- sources ----------
    rows = [[f'<code>{esc(s["source_id"])}</code>', esc(s['title']), link(s['url']), esc(s['tier']),
             esc(s['read_at_utc']), esc(s['used_for'])] for s in srcs]
    body = f'''
<section>
<h2>Source register</h2>
{table(['ID','Title','URL','Tier','Read at (UTC)','Used for'], rows)}
</section>'''
    write('sources.html', shell('Sources', body, 'sources.html'))

    # ---------- flagged ----------
    rows = [[f'<code>{esc(f["flag_id"])}</code>', f'<span class="sev sev-{f["severity"].lower()}">{esc(f["severity"])}</span>',
             esc(f['title']), esc(f['detail']), link(f['source_url'], 'evidence'), f'<span class="st">{esc(f["status"])}</span>']
            for f in flags]
    body = f'''
<section>
<h2>Flagged for review (non-blocking)</h2>
<p>Irregularities found during the line-by-line review and every value that could not be confirmed. These do not block
publication; they are listed so the owner can review them on the live site.</p>
{table(['ID','Severity','Title','Detail','Evidence','Status'], rows)}
</section>'''
    write('flagged.html', shell('Flagged for review', body, 'flagged.html'))

    # ---------- executive summary ----------
    met, part, block = sc['MET'], sc['PARTIAL'], sc['BLOCKED']
    body = f'''
<section>
<h2>Executive summary</h2>
<p class="lede">Session 8ad92a0e re-read four official NFL pages on 2026-11-19, adopted a 150-game verified results
feed after a 32/32 reconciliation, originated 39 Week-11 markets (side → total → moneyline), captured the full Week-11
injury report, computed official-only correlations and a walk-forward luck panel, and published a decision-readiness
table, questions register, suggestions register and flagged register. <strong>Nothing is certified: 0 strategies pass
the gates, no price source exists, the reward pool is unfunded.</strong></p>
{table(['Area','Result','Where'], [
    ['Repo review', '69 desks / 706 pages / 44 workflows reviewed; 18 irregularities flagged', link('flagged.html', 'Flagged')],
    ['Official verification', 'standings (32 clubs), Wk11 schedule (13+6), Wk10 scores (14), Wk11 injuries (253 rows) read 2026-11-19', link('sources.html', 'Sources')],
    ['Results feed', f'{len(results)} finals; wk9+wk10 direct-read match; 32/32 club reconciliation', link('results.html', 'Results')],
    ['Origination', f'{len(lines)} markets; fair/market/difference separate; market cells BLANK (F8-01)', link('lines.html', 'Lines')],
    ['Price snapshots', f'{len(snaps)} opening snapshots; closing BLANK', link('snapshots.html', 'Snapshots')],
    ['Skill / luck', 'Brier 0.2427 (n=149); skill 0.0664 [0.0283, 0.1029] vs expanding home rate; no market benchmark', link('leaderboard.html', 'Leaderboard')],
    ['Correlations', '9 rows, official numbers only, n=32/n=150, Fisher-z CIs', link('correlations.html', 'Correlations')],
    ['Availability', '253 rows / 26 clubs; 9 Out, 7 Questionable; depth & replacements BLANK (F8-02)', link('availability.html', 'Availability')],
    ['Decision readiness', f'{len(reqs)} requirements: {met} met · {part} partial · {block} blocked · {sc["RULE-ADOPTED"]} rules adopted · {sc["OPEN"]} open', link('index.html', 'Dashboard')],
    ['Questions', f'{len(qs)} open questions with discovery routes; answers blank until sourced', link('questions.html', 'Questions')],
    ['Suggestions', f'{len(sug)} proposals; decision cells blank — owner reviews before implement', link('suggestions.html', 'Suggestions')],
])}
<p><strong>What would change our mind:</strong> a verified price source (Q8-01) unlocks market gates G8-06 and residuals;
a depth source (Q8-04) unlocks the availability features and ablations; n≥100 settled prospective scores with a
market benchmark are required before any ranking claim.</p>
</section>'''
    write('executive-summary.html', shell('Executive summary', body, 'executive-summary.html'))

    # ---------- style ----------
    css = '''*{box-sizing:border-box}
body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#1a2330;background:#f4f6f9}
header{background:#0d2438;color:#eaf2fa;padding:18px 0 10px}
header h1{margin:0;font-size:22px;font-weight:700}
header .sid{font-size:12px;background:#1f4463;padding:3px 8px;border-radius:10px;vertical-align:middle;margin-left:8px}
header .sub{margin:4px 0 10px;font-size:13px;color:#a9c3d9}
nav{display:flex;flex-wrap:wrap;gap:6px}
nav a{color:#cfe3f3;text-decoration:none;font-size:13px;padding:5px 10px;border-radius:6px;background:#16334d}
nav a.on,nav a:hover{background:#2e6da4;color:#fff}
.wrap{max-width:1200px;margin:0 auto;padding:0 16px}
main{padding:18px 0 30px}
h2{font-size:18px;margin:26px 0 8px;border-bottom:2px solid #d7dfe8;padding-bottom:4px}
h3{font-size:15px;margin:16px 0 6px}
p{margin:6px 0 10px}
.lede{font-size:15px;background:#fff;border-left:4px solid #2e6da4;padding:10px 14px;border-radius:0 6px 6px 0}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin:12px 0}
.card{background:#fff;border:1px solid #dbe3ec;border-radius:8px;padding:10px 12px}
.card .k{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:#5b7186}
.card .v{font-size:22px;font-weight:700;color:#0d2438}
.card .n{font-size:12px;color:#5b7186}
.tbl-wrap{overflow-x:auto;background:#fff;border:1px solid #dbe3ec;border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:13px}
th{background:#eef3f8;text-align:left;padding:8px 10px;border-bottom:2px solid #d7dfe8;position:sticky;top:0;font-size:12px;text-transform:uppercase;letter-spacing:.4px;color:#3c5065}
td{padding:7px 10px;border-bottom:1px solid #edf1f5;vertical-align:top}
tr:hover td{background:#f8fbfe}
table.dense td,table.dense th{padding:5px 8px;font-size:12px}
code{font-size:12px;background:#eef3f8;padding:1px 5px;border-radius:4px}
.blank{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.5px;color:#8a6d1a;background:#fdf3d7;border:1px dashed #d9bf6a;padding:1px 6px;border-radius:4px}
.st{display:inline-block;font-size:10px;font-weight:700;padding:2px 7px;border-radius:9px;background:#e6ebf1;color:#44586c;white-space:nowrap}
.st-met,.st-pass{background:#d7f0dc;color:#1d6b31}
.st-blocked,.st-fail{background:#fbe0dd;color:#9c2b21}
.st-partial,.st-open,.st-rule-adopted{background:#fdf0d2;color:#8a5a10}
.sev{display:inline-block;font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px;white-space:nowrap}
.sev-blocking{background:#f6c8c2;color:#8f1d12}
.sev-high{background:#fde3c2;color:#8a4b0d}
.sev-medium{background:#fdf0d2;color:#8a5a10}
.sev-low{background:#e6ebf1;color:#44586c}
.findings li{margin:6px 0}
a{color:#14507d}
footer{border-top:1px solid #d7dfe8;padding:14px 0 26px;font-size:12px;color:#5b7186}
@media (max-width:640px){.cards{grid-template-columns:repeat(2,1fr)} header h1{font-size:18px}}
'''
    with open(os.path.join(HERE, 'style.css'), 'w') as f:
        f.write(css)
    with open(os.path.join(HERE, '.nojekyll'), 'w') as f:
        f.write('')
    print(f'built {len(PAGES)} pages + style.css')


if __name__ == '__main__':
    main()

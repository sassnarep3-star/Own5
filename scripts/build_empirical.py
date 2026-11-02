#!/usr/bin/env python3
"""Generate the additive, static historical-study pages from the checked report."""
from __future__ import annotations
import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "empirical"
D = json.loads((ROOT / "data/derived/report.json").read_text(encoding="utf-8"))
M = D["metadata"]
SCORING_SOURCE = "https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html"


def e(value):
    return html.escape(str(value), quote=True)


def refs(*pairs):
    return '<span class="refs">' + ''.join(
        f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} ↗</a>'
        for label, url in pairs
    ) + '</span>'


def missing():
    return ''


def badge(label, kind="neutral"):
    return f'<span class="badge {e(kind)}">{e(label)}</span>'


def table(title, subtitle, heads, rows, ident):
    thead = ''.join(f'<th scope="col">{e(h)}</th>' for h in heads)
    body = ''.join('<tr>' + ''.join(f'<td>{cell}</td>' if cell else '<td class="missing" aria-label="Unverified; value intentionally blank"></td>' for cell in row) + '</tr>' for row in rows)
    return f'''<section class="panel table-panel" aria-labelledby="{ident}-title">
<div class="panel-head"><div><h2 id="{ident}-title">{e(title)}</h2><p>{e(subtitle)}</p></div><button type="button" class="export" data-export="{ident}">Export CSV <span>↗</span></button></div>
<div class="table-tools"><label class="search"><span aria-hidden="true">⌕</span><span class="sr-only">Search {e(title)}</span><input type="search" data-search="{ident}" placeholder="Search entries"></label><span class="row-count" data-count="{ident}">{len(rows)} of {len(rows)} entries</span></div>
<div class="table-wrap"><table id="{ident}"><thead><tr>{thead}</tr></thead><tbody>{body}</tbody></table></div><p class="empty" hidden>No matching entries. Try another search.</p></section>'''


def note(title, body):
    return f'<aside class="notice"><span class="notice-icon" aria-hidden="true">i</span><div><strong>{e(title)}</strong><p>{e(body)}</p></div></aside>'


def pcent(x): return f"{100*x:.1f}%"
def decimal(x, places=3): return f"{x:.{places}f}"


def study_sources():
    return refs(("NFL game file", M['game_source']), ("Brier method", SCORING_SOURCE))


def overview():
    c = D["counts"]
    blocks = f'''<div class="study-hero"><div><span class="eyebrow">SUPPLEMENTAL / EMPIRICAL STUDY</span><h2>Evidence, not<br><span>just expectations.</span></h2><p>Explore a reproducible historical replay, real matched player logs, and the limits of what these numbers can tell us.</p><a class="primary" href="lines.html">Explore historical lines <span>↗</span></a><a class="text-link" href="../research/NFL_EMPIRICAL_SUMMARY.md">Read the study brief →</a></div><div class="study-mark" aria-hidden="true"><span>THE RESEARCH CYCLE</span><div class="study-ring"><b>01</b><i>VERIFY</i><b>02</b><i>TEST</i><b>03</b><i>REVIEW</i></div><small>SOURCE → SIGNAL → SCRUTINY</small></div></div>
<div class="stats"><article><span>Official game results</span><strong>{c['game_results']}</strong><small>2017 · weeks 1–6</small></article><article><span>Paired player games</span><strong>{c['paired_player_rows']}</strong><small>2024 &amp; 2025 logs</small></article><article><span>Rolling evaluation</span><strong>{c['evaluated_games']}</strong><small>2017 · weeks 4–6</small></article><article><span>Qualified strategies</span><strong class="amber">{c['qualified_strategies']:02}</strong><small>No credits awarded</small></article></div>'''
    intro = note('Historical research only. No current betting signal.', 'Models and coefficients are project calculations, not NFL forecasts or sportsbook offers. The sample is small, old and retrospective; neither single-game candidate beats the 50/50 reference. Chance cannot be eliminated.')
    entries = []
    b = D['scores']['binary_baseline']
    entries.append(['<strong>50/50 reference</strong><small>Not eligible for rewards</small>', str(b['n']), decimal(b['brier'],4), '—', badge('Reference'), study_sources()])
    for s in D['scores']['candidates']:
        delta = b['brier'] - s['brier']
        entries.append([f'<strong>{e(s["label"])}</strong><small>Descriptive order #{s["descriptive_rank"]}</small>', str(s['n']), decimal(s['brier'],4), f'{delta:+.4f}', badge('Not eligible','warn'), study_sources()])
    leaders = table('Single-game signal check', 'Rolling 2017 Weeks 4–6. Lower Brier is better; Δ = reference Brier − model Brier.', ['Model','Games','Brier ↓','Δ vs reference','Eligibility','Official inputs'], entries, 'model-summary')
    links='''<div class="section-title"><h2>Follow the evidence</h2><span class="eyebrow">THREE WAYS IN</span></div><div class="brief-grid"><article class="panel brief"><span class="step">01 / ORIGINATION</span><h3>A line is a model output.</h3><p>Inspect all 44 historical Elo estimates, implied fair prices, and score projections alongside the official game results.</p><a href="lines.html">Open the line archive →</a></article><article class="panel brief"><span class="step">02 / DEPENDENCE</span><h3>Don't multiply blindly.</h3><p>Compare actual matched-game correlations with illustrative binary leg outcomes and their independence products.</p><a href="correlations.html">Explore correlations →</a></article><article class="panel brief"><span class="step">03 / DISCIPLINE</span><h3>Earn the right to rank.</h3><p>See the fail-closed gates, sample rules and non-cash reward policy. None of the candidates currently qualifies.</p><a href="validation.html">Review the gates →</a></article></div>'''
    return blocks + intro + leaders + links


def lines():
    intro = note('Not live quotes; not a recommendation.', 'Each estimate is replayed after the fact using information through the prior week. Prices assume a hypothetical two-outcome, tie-void contract and zero vig. Current bookmaker quotes, edge and settlement rules are unverified and intentionally blank.')
    rows=[]
    for g in D['predictions']:
        a=g['elo_fair_home']['american']
        score=f'{e(g["away"])} {g["away_score"]} – {e(g["home"])} {g["home_score"]}'
        rows.append([f'<strong>{e(g["away"])} @ {e(g["home"])}</strong><small>2017 · Week {g["week"]}</small>', e(g['cutoff']), str(g['home_prior_games'])+' / '+str(g['away_prior_games']), pcent(g['elo_home_p']), f'{a:+.0f}', decimal(g['elo_fair_home']['decimal'],2), decimal(g['projected_total'],1), f'{g["home_spread_projection"]:+.1f}', score, missing(), refs(('NFL result',g['source']),('NFL data',M['game_source']))])
    content=table('Historical model-line archive','44 retrospective forecasts · fair odds and projections are calculated estimates, not official quoted prices.',['Matchup','Prior-data cutoff','Prior games H / V','Home win p','Fair home US','Fair home decimal','Projected total','Projected home spread','Final (V – H)','Market quote · unverified','Official inputs'],rows,'historical-lines')
    return intro + content + note('How to read these numbers', 'The Elo model starts all teams at 1500 and updates once per week with K=20 and no home-field adjustment. A score blend makes a mean total and margin, not a calibrated spread/total distribution. The same-week outcome is never a feature.')


def correlations():
    intro=note('Correlation is not a price.', 'All coefficients below are project calculations from official historical results. They are unconditional, retrospective and sensitive to sample selection. Illustrative over thresholds are not verified sportsbook lines; uncertainty intervals are blank because the evidence is insufficient for a robust clustered estimate.')
    rows=[]
    for x in D['correlations']:
        pairs=[('NFL source', x['sources'][0])]
        if len(x['sources'])==3:
            pairs.append(('NFL source 2', x['sources'][1]))
        pairs.append(('NIST method',M['nist_source']))
        rows.append([f'<strong>{e(x["label"])}</strong>',e(x['measure']),str(x['n']),f'{x["value"]:+.3f}' if x['value'] is not None else missing(),missing(),badge('Descriptive only','warn'),refs(*pairs)])
    corr=table('Observed associations','Pearson r for continuous totals; binary phi is Pearson r applied to the two event indicators.',['Historical pair','Measure','Games','Coefficient','95% interval · unverified','Status','Official inputs'],rows,'associations')
    joint_rows=[]
    for x in D['correlations']:
        if 'comparison' not in x: continue
        q=x['comparison']
        pairs=[('NFL source',x['sources'][0])]
        if len(x['sources'])==3: pairs.append(('NFL source 2',x['sources'][1]))
        pairs.append(('NIST method',M['nist_source']))
        joint_rows.append([f'<strong>{e(x["label"])}</strong>',str(q['n']),f'{q["n11"]} / {q["n10"]} / {q["n01"]} / {q["n00"]}',pcent(q['joint']),pcent(q['independent_product']),refs(*pairs)])
    joint=table('Joint events vs independence','Counts ordered: both, A only, B only, neither. Percentages use the same historical sample.',['Illustrative event pair','n','Both / A / B / neither','Observed joint','Product of marginals','Official inputs'],joint_rows,'joint-events')
    return intro+corr+joint+note('Continuous and thresholded outcomes are different estimands.', 'A positive yardage correlation does not require positive correlation between particular over/under indicators. No pairwise coefficient can identify an arbitrary three-leg joint distribution. Condition on matchup, roles, availability, exact threshold and settlement before attempting a prospective model.')


def games():
    rows=[]
    for g in D['games']:
        rows.append([str(g['week']),e(g['date']),f'<strong>{e(g["away_name"])}</strong><small>{e(g["away"])}</small>',str(g['away_score']),f'<strong>{e(g["home_name"])}</strong><small>{e(g["home"])}</small>',str(g['home_score']),e(g['id']),refs(('NFL source row',g['source']))])
    return note('A pinned primary-source snapshot.', 'All 91 rows match the cited NFL Football Operations file, including historical team display names. “Home” means the source’s designated home team; some games were played outside its usual home venue.') + table('NFL 2017 game results','First six regular-season weeks · score order is visitor then designated home.',['Week','Date','Visitor','Visitor pts','Designated home','Home pts','Game ID','Official source'],rows,'game-archive')


def players():
    rows=[]
    for r in D['players']:
        qb = str(r['qb_passing_yards']) if r['qb_passing_yards'] is not None else missing()
        status=badge('Paired','ok') if r['paired'] else badge('Excluded','warn')
        rows.append([str(r['season']),str(r['week']),e(r['date']),e(r['opponent']),f'<strong>{e(r["qb"])}</strong>',qb,f'<strong>{e(r["receiver"])}</strong>',str(r['receiver_yards']),str(r['receiver_receptions']),status,refs(('QB NFL log',r['qb_source']),('Receiver NFL log',r['receiver_source']))])
    return note('34 source-checked rows; 31 matched game pairs.', 'The 2025 Kelce Weeks 16–18 rows have no Mahomes passing-yard row in the retrieved log. Their passing yards remain blank and they are excluded—not treated as zero or assigned an inferred reason.') + table('Player game-log evidence','Same season, week, date, opponent and result · official NFL.com logs transcribed on 2026-11-02.',['Season','Week','Date','Opponent','Quarterback','Passing yds','Receiver','Receiving yds','Receptions','Pair status','Official sources'],rows,'player-archive')


def validation():
    candidates=[]
    names={'provenance':'Input','chronology':'Time','sample':'Sample','calibration':'Calibration','skill':'Skill','market_and_settlement':'Market','forward_test':'Forward'}
    def status(s): return badge(s.title(), 'ok' if s=='pass' else 'warn' if s=='fail' else 'neutral')
    for c in D['scores']['candidates']:
        candidates.append([f'<strong>{e(c["label"])}</strong>',*[status(c['gates'][k]) for k in names],badge('Not eligible','warn'),study_sources()])
    audited=table('Observed gate results','The calibration pass is only a coarse bin check; a separate sample gate still fails.',['Candidate',*names.values(),'Eligibility','Official inputs'],candidates,'gate-results')
    gates=[
        ('01','Provenance','Official sources, complete records, no duplicates or missing fields; verify the pinned input revision.',M['game_source']),
        ('02','Chronology','Forecast from data available before outcomes; lock future definitions in advance.',M['game_source']),
        ('03','Sample','Project policy: ≥200 matched held-out events, ≥3 seasons, and ≥10 season/week blocks.',M['game_source']),
        ('04','Calibration','Five fixed bins; each populated bin needs ≥20 cases and forecast-frequency gap ≤0.10. Necessary, not sufficient.',SCORING_SOURCE),
        ('05','Skill & selection','Positive paired Brier improvement and a positive multiplicity-adjusted lower confidence bound using week blocks.',SCORING_SOURCE),
        ('06','Market & settlement','Verify executable timestamped prices, full settlement terms, fees and pushes/voids.',M['rules_source']),
        ('07','Forward & joint','Require locked forward forecasts. Parlays and player combos also require validated exact-event joint probabilities and leg terms.',M['nist_source']),
    ]
    gate_rows=[[f'<span class="record-id">G{num}</span><strong>{e(name)}</strong>',e(rule),refs(('Primary reference',url))] for num,name,rule,url in gates]
    rules=table('Competition gates','These thresholds are project policies, not requirements or endorsements from the linked organizations.',['Gate','Proposed pass requirement','Official reference'],gate_rows,'gate-policy')
    return note('Zero qualified strategies.', 'Descriptive ordering is not a competition ranking. The 44-game, one-season study fails the sample threshold; both candidate Brier scores are worse than the 50/50 reference. Market and prospective evidence are unverified.') + audited + rules + note('Proposed non-cash rewards', 'If every applicable gate passes, eligible strategies forecasting the same event set are ordered by Brier. First, second and third receive 100, 60 and 30 research credits respectively. Ties share rank; later places receive zero credits. This is a proposed paper policy, not a funded cash contest or payout.')


def review():
    flags=[
        ('F01','Historical coverage','Only Weeks 1–6 of 2017 are in the game source; 44 evaluations are not enough to establish a durable edge.',M['game_source']),
        ('F02','No market prices','No timestamped, executable sportsbook odds, limits, closing prices or fees were verified. Edge, ROI and CLV stay blank.',M['rules_source']),
        ('F03','Retrospective selection','Forecasts and thresholds were defined after these seasons had already occurred; this is not a preregistered prospective trial.',M['game_source']),
        ('F04','Uncertainty & dependence','A dependable multi-season, week-blocked interval and multiplicity-adjusted significance test were not available.',M['nist_source']),
        ('F05','Missing player rows','Three Kelce rows lack a matching Mahomes passing-yard row in the published log; blank is not zero and no reason is inferred.','https://www.nfl.com/players/patrick-mahomes/stats/logs/2025/'),
        ('F06','Player-prop settlement','The illustrated thresholds are project examples, not verified historical operator offers or settlement terms.',M['rules_source']),
        ('F07','Venue and team names','The official 2017 file uses designated home teams and historical names; venue and current branding must not be inferred.',M['schema_source']),
        ('F08','Reuse rights','The source-repository metadata did not expose a license. Permission to redistribute source data was not established.', 'https://github.com/nfl-football-ops/Big-Data-Bowl'),
        ('F09','No current availability feed','Injuries, depth-chart changes, active status and live lines are not part of this historical study.', 'https://www.nfl.com/injuries/'),
        ('F10','Rewards are hypothetical','Research credits are a project proposal only; no sponsor, funded prize or cash payout is asserted.',SCORING_SOURCE),
    ]
    rows=[[f'<span class="record-id">{i}</span><strong>{e(name)}</strong>',e(detail),badge('Needs review','warn'),refs(('Primary reference',url))] for i,name,detail,url in flags]
    return note('Open limitations, not hidden assumptions.', 'These items block a validated betting claim or live forecast; they do not block publication of the historical research site. Consult the source for the scope it actually supports.')+table('Flagged for Review','The official link is evidence for the relevant source or context—not proof that a missing value exists.',['ID / issue','Finding or gap','Status','Source'],rows,'review-flags')


NAV=[('index.html','Study overview'),('lines.html','Historical lines'),('correlations.html','Correlations'),('validation.html','Validation & rewards'),('games.html','Game archive'),('players.html','Player pairs'),('review.html','Flagged for Review')]
PAGES={'index.html':('Historical study','A closer look at the verified evidence.',overview),
       'lines.html':('Historical line archive','Retrospective forecasts, not live offers.',lines),
       'correlations.html':('Correlation lab','Matched outcomes. Explicit limitations.',correlations),
       'validation.html':('Validation & rewards','A gate before a ranking.',validation),
       'games.html':('Game archive','The official source behind the study.',games),
       'players.html':('Player pair archive','Same-game observations from NFL logs.',players),
       'review.html':('Flagged for Review','The gaps that remain.',review)}


def shell(filename, title, subtitle, content):
    nav=''.join(f'<a class="nav-item {"active" if path==filename else ""}" {"aria-current=page" if path==filename else ""} href="{path}"><span class="nav-number">{i:02}</span>{e(label)}</a>' for i,(path,label) in enumerate(NAV,1))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="Source-linked historical NFL forecasts, game and player data, correlations, and validation gates."><meta name="theme-color" content="#173e36"><title>{e(title)} · OWN5 NFL Research</title><link rel="icon" href="../assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="../assets/style.css"><link rel="stylesheet" href="empirical.css"><script src="../assets/app.js" defer></script></head><body><a class="skip" href="#main">Skip to content</a><div class="layout"><aside class="sidebar"><a class="brand" href="../index.html"><span class="brand-icon">O<span>5</span></span><span>OWN5<small>NFL RESEARCH DESK</small></span></a><div class="workspace"><span class="live-dot"></span> Historical evidence <span class="workspace-arrow">⌄</span></div><span class="nav-caption">EMPIRICAL STUDY</span><nav aria-label="Study navigation">{nav}</nav><div class="side-bottom"><div class="mode"><span class="live-dot"></span> Paper research only</div><p>No bets. No live odds.<br>Evidence before exposure.</p><a href="../index.html">← Main research workspace</a></div></aside><div class="main-shell"><header class="topbar"><div><span class="breadcrumb"><a href="../index.html">Workspace</a> <span>/</span> {e(title)}</span></div><div class="topbar-right"><span class="desktop-only">NFL / HISTORICAL STUDY</span><span class="avatar">O5</span></div></header><main id="main"><div class="page-heading"><div><span class="eyebrow">SOURCE-LINKED RESEARCH</span><h1>{e(title)}</h1><p>{e(subtitle)}</p></div><span class="date-label"><span class="live-dot"></span> Reviewed {e(M['as_of_utc'])}</span></div>{content}<footer><span>OWN5 <span class="footer-divider">/</span> Independent NFL research · Not affiliated with the NFL.</span><span>Blank = unverified. <a href="../research/NFL_EMPIRICAL_METHODS.md">Study methodology ↗</a> · <a href="../data/derived/report.json">Reproducible report ↗</a> · <a href="../pages/sources.html">Main source register ↗</a></span></footer></main></div></div></body></html>\n'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='check committed output without rewriting files')
    args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    different=[]
    for path,(title,subtitle,fn) in PAGES.items():
        result=shell(path,title,subtitle,fn())
        dest=OUT/path
        if args.check:
            if not dest.exists() or dest.read_text(encoding='utf-8') != result: different.append(str(dest.relative_to(ROOT)))
        else: dest.write_text(result,encoding='utf-8')
    if different:
        print('Stale generated pages: '+', '.join(different), file=sys.stderr)
        return 1
    print(('Checked' if args.check else 'Built')+f' {len(PAGES)} static empirical study pages.')
    return 0


if __name__=='__main__':
    raise SystemExit(main())

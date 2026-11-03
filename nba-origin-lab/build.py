"""Deterministic, additive NBA research microsite; no live market feed or bets."""
from pathlib import Path
from html import escape
import csv
import math
import statistics

HERE = Path(__file__).parent
SAMPLE = HERE.parent / 'nba-2026-lab/data/edwards_2025_26_recent10.csv'
GAME = 'https://www.nba.com/game/'
GLOSS = 'https://www.nba.com/stats/help/glossary'
INJ = 'https://official.nba.com/nba-injury-report-2026-27-season/'
SCHEDULE = 'https://www.nba.com/games'
LOG = 'https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26'
NAV = [('index.html','Overview'),('sources.html','Evidence'),('lines.html','Own lines'),('strategies.html','Strategies'),('correlations.html','Correlation'),('gates.html','Validation'),('leaderboard.html','Leaderboard'),('review.html','Flagged for Review')]

def h(x): return escape(str(x), quote=True)
def table(headers, rows):
    assert rows
    out = '<div class="scroll"><table><thead><tr>'+''.join('<th>'+h(c)+'</th>' for c in headers)+'</tr></thead><tbody>'
    for cells, src in rows:
        assert len(cells)==len(headers)-1 and src.startswith(('https://www.nba.com/','https://official.nba.com/'))
        out += '<tr>'+''.join('<td>'+h(c)+'</td>' for c in cells)+f'<td><a href="{h(src)}" target="_blank" rel="noopener noreferrer">Official source ↗</a></td></tr>'
    return out+'</tbody></table></div>'

def page(filename, title, eyebrow, intro, content):
    nav=''.join(f'<a href="{h(link)}"'+(' aria-current="page"' if link==filename else '')+'>'+h(label)+'</a>' for link,label in NAV)
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Source-first NBA line-origination research; no validated betting edges."><title>{h(title)} · Own5 NBA Origin Lab</title><link rel="stylesheet" href="style.css"></head><body><header class="top"><div class="brand"><span class="mark">O5</span><span>OWN5 <small>/ NBA ORIGIN LAB</small></span></div><span class="badge">RESEARCH ONLY · 03 NOV 2026</span></header><div class="shell"><aside><div class="side-label">WORKSPACE</div><nav aria-label="Sections">{nav}</nav><div class="side-note">No market feed. No certified edges. All proposals are hypotheses, not NBA-endorsed methods.</div></aside><main><div class="eyebrow">{h(eyebrow)} / NBA RESEARCH</div><h1>{h(title)}</h1><p class="lead">{h(intro)}</p>{content}<footer>Own5 · NBA Origin Lab · Source-linked research · <a href="review.html">Review limitations</a> · <a href="../nba-2026-lab/index.html">Earlier NBA evidence lab</a></footer></main></div></body></html>'''
    (HERE/filename).write_text(html, encoding='utf-8')

def section(label, body, caption=''):
    return f'<section class="panel"><div class="section-head"><h2>{h(label)}</h2>{("<span>"+h(caption)+"</span>") if caption else ""}</div>{body}</section>'

def main():
    with SAMPLE.open(newline='') as f: data=list(csv.DictReader(f))
    assert len(data)==10 and len({r['game_id'] for r in data})==10
    for r in data:
        assert r['source']==GAME+r['game_id']+'/'
        for field in ('points','assists','rebounds','threes','minutes'): r[field]=int(r[field])
    vals=[r['points'] for r in data]
    mid=statistics.median(vals)
    mae=sum(abs(v-mid) for v in vals)/len(vals)
    def corr(a,b):
        x=[r[a] for r in data];y=[r[b] for r in data];mx=statistics.mean(x);my=statistics.mean(y)
        return sum((u-mx)*(v-my) for u,v in zip(x,y))/math.sqrt(sum((u-mx)**2 for u in x)*sum((v-my)**2 for v in y))
    flag='class="warning"'
    cards='<div class="metrics"><div><strong>0</strong><span>Certified strategies</span></div><div><strong>0</strong><span>Live own lines</span></div><div><strong>10</strong><span>Historical player-games</span></div><div><strong>0</strong><span>Rewards issued</span></div></div>'
    overview=cards+section('Executive decision', '<p>Do not publish a wager or claim skill. This lab defines how to originate a probability distribution and price from official NBA evidence, but the current sample does not meet the prospective validation, injury, settlement or market-quote gates. The 2025–26 ten-game sample is descriptive, selected and far too small to establish an edge.</p><p>Singles, cross-game parlays and same-game prop combinations each need separate joint-probability and settlement checks. A higher historical hit rate alone is not proof of skill: selection, multiple testing and variance remain.</p><p><a class="button" href="gates.html">Inspect validation gates →</a> <a class="button muted" href="review.html">See unresolved items →</a></p>')+section('At a glance',table(['Question','Finding','Evidence'],[
        (['Can we quote current game or prop prices?','No — timestamped book quotes absent; cells remain blank.'],SCHEDULE),
        (['Is there a reproducible sample?','Yes — 10 historical Anthony Edwards player-games, selected by the earlier NBA lab; exploratory only.'],LOG),
        (['Is injury reporting optional?','No — the official 2026–27 reporting index is the source; game-day status must be snapshot before any forecast.'],INJ),
        (['Can derived correlation establish bet edge?','No — historical box-score association is not a joint prop-hit probability or market price.'],GLOSS)]))
    page('index.html','The evidence-first NBA desk','00 / overview','Build your own lines; publish only when the data and the validation both survive scrutiny.',overview)
    sources=section('Official evidence register',table(['ID','Official location','Use / verification boundary','Source'],[
        (['S01','NBA stats glossary','OffRtg, Pace, USG%, eFG%, TS%; definitions, not a predictive edge.'],GLOSS),
        (['S02','NBA games & scores','Schedule and results; page is dynamic, snapshot and timestamp before modeling.'],SCHEDULE),
        (['S03','NBA 2026–27 injury report','Participation status, updated throughout day; do not infer availability from absence.'],INJ),
        (['S04','NBA player box-score log','Historical selected-player sample provenance; individual game links below.'],LOG),
    ]))+section('Auditable historical rows',table(['Game ID','Date','Opponent','PTS','AST','REB','3PM','Source'],[
        ([r['game_id'],r['date'],r['opponent'],r['points'],r['assists'],r['rebounds'],r['threes']],r['source']) for r in data
    ]))+'<p class="note">All ten row values (date, opponent, result, MIN, PTS, 3PM, REB, AST and game ID) were checked against the NBA player box-score log on 2026-11-03. The official log is dynamic and no immutable official snapshot is included; see review R01.</p>'
    page('sources.html','Evidence register','01 / sources','Official links on every table row; provenance and limits are stated rather than assumed.',sources)
    lines=section('Historical illustration — not an NBA betting line',table(['Target','Statistic','Value','Scope','Source'],[
        (['Edwards PTS','Sample median',f'{mid:g}','10 selected 2025–26 games; calculated here, not a current projection'],LOG),
        (['Edwards PTS','In-sample absolute error',f'{mae:.1f} pts','Evaluated on the SAME ten observations: biased; not out-of-sample'],LOG),
        (['Current 2026–27 PTS distribution','Predicted mean / uncertainty','','Unverified — no current rolling player, opponent, lineup or minutes inputs'],INJ),
        (['Current fair line / over probability','Line / probability','','Unverified — model not fit and calibrated'],SCHEDULE),
        (['Quoted book odds / spread','Timestamped price','','Unverified — no licensed-operator quote snapshot'],SCHEDULE),
    ]))+section('Origination pipeline · proposed method',table(['Step','Required artifact','Failure policy','Source'],[
        (['1 · Snapshot','Official game schedule, player and team game logs with as-of timestamps','No data → no line'],SCHEDULE),
        (['2 · Availability','Latest official injury snapshot and confirmed starting context','Unknown status → suppress or widen uncertainty'],INJ),
        (['3 · Estimate','Expected possessions, minutes, usage, rate and uncertainty using prior-only observations','No prospective calibration → research output only'],GLOSS),
        (['4 · Convert','Predictive outcome distribution → quantile or over probability; save model version and time','No distribution → no implied price'],GLOSS),
        (['5 · Quote','Compare to timestamped operator quote after vig and settlement adjustments','No official operator quote → edge blank'],SCHEDULE),
    ]))+'<p class="note">Pipeline and stop rules are our proposed research design, not official NBA guidance. Evidence links support input definitions only.</p>'
    page('lines.html','Own lines laboratory','02 / origination','A reproducible descriptive baseline is not a tradable line. Current forecasts stay empty.',lines)
    strategies=section('Pre-registered hypothesis queue',table(['Format','Hypothesis (unvalidated)','Required test','Status','Source'],[
        (['Single · total','Possession and efficiency forecast versus posted total','Walk-forward calibration + frozen odds + vig-aware net returns','Blocked'],GLOSS),
        (['Single · player prop','Minutes × usage × rate predictive distribution','Player/game holdout + injury snapshots + settlement mapping','Blocked'],INJ),
        (['Parlay · separate games','Estimate joint hit probability including shared schedule/news factors','Dependence-adjusted payout EV + joint holdout','Blocked'],SCHEDULE),
        (['Same-game prop combo','Correlated points/assists/rebounds or 3PM legs','Conditional joint model + operator SGP terms and payout','Blocked'],LOG),
    ]))+'<p class="note">Hypotheses are our proposals. The linked NBA pages establish the relevant observations or vocabulary; they do not validate profitability or operator rules.</p>'
    page('strategies.html','Strategy queue','03 / strategies','Different bet structures, different dependence and settlement risks; none currently qualified.',strategies)
    corrows=[]
    for a,b in [('points','assists'),('points','rebounds'),('threes','points'),('assists','rebounds')]:
        corrows.append(([f'{a.upper()} × {b.upper()}',f'{corr(a,b):+.4f}','10','Pearson, selected historical sample; not bet-hit correlation'],LOG))
    correlations=section('Measured sample associations',table(['Pair','Pearson r','n','Interpretation','Source'],corrows)) + section('What is missing for a bet combo?',table(['Object','Value','Required to publish','Source'],[
        (['Threshold-specific prop-hit phi','','Actual thresholds with timestamped outcomes per leg'],LOG),
        (['Same-game joint probability','','Paired binary leg hits with same game ID and pre-specified thresholds'],LOG),
        (['Parlay EV / payout','','Actual posted SGP terms and price snapshot; cannot multiply marginal rates blindly'],SCHEDULE),
    ]))+'<p class="note">Pearson coefficients are computed by this repository from the ten prior-lab rows; source links are provenance, not independent certification of the calculation. Sample selection and small n make these estimates unstable.</p>'
    page('correlations.html','Correlation audit','04 / dependence','Correlation is measured on matched historical observations, not guessed from narrative.',correlations)
    gates=section('Hard gates · proposed contest policy',table(['Gate','Required evidence / test','Now','Source'],[
        (['G0 · Provenance','Official game-level inputs, source URL per observation, as-of timestamp','Partial'],LOG),
        (['G1 · Availability','Official injury status snapshot before tip-off','Fail'],INJ),
        (['G2 · Forecast','Frozen pregame version, distribution and confidence interval','Fail'],GLOSS),
        (['G3 · Leakage','Rolling-origin splits; no future result or same-game data in inputs','Fail'],SCHEDULE),
        (['G4 · Calibration','Prospective log loss / Brier score and reliability by bucket','Fail'],LOG),
        (['G5 · Economics','Timestamped odds, vig, SGP pricing and written settlement terms','Fail'],SCHEDULE),
        (['G6 · Selection','Frozen candidate count, multiple-testing correction, holdout','Fail'],LOG),
        (['G7 · Risk','Joint exposure, limits, max drawdown, void handling','Fail'],INJ),
    ]))+'<p class="note">G0–G7 are project-defined gates, not rules issued by the NBA. Links show input provenance or context only; operator terms are missing. A gate fails closed on missing evidence.</p>'
    page('gates.html','Validation gates','05 / controls','Selective skill means prospective, reproducible, risk-adjusted evidence; luck cannot be eliminated.',gates)
    leaderboard=section('Competition standings',table(['Entrant','Eligible bets','Net units','Calibration','Risk-adjusted score','Reward','Source'],[
        (['No qualified entries','0','','','',''],SCHEDULE),
    ])) + section('Proposed scoring protocol',table(['Rule','Definition','Current decision','Source'],[
        (['Entry lock','Record model hash, picks, threshold, timestamp and quoted settlement terms before tip','Not available'],SCHEDULE),
        (['Primary score','Prospective net units after price/void handling, with uncertainty intervals','Blank until certified bets'],SCHEDULE),
        (['Skill check','Out-of-sample calibration, multiple-testing-aware comparisons and drawdown','No qualifying sample'],LOG),
        (['Rewards','Fund and specify terms separately before promising payouts','No reward amount verified; 0 awarded'],SCHEDULE),
    ]))+'<p class="note">Leaderboard and rewards are proposed Own5 contest rules, not NBA facts. Official links are context for inputs, not source of reward policy.</p>'
    page('leaderboard.html','Leaderboard','06 / competition','No winner without a qualified, timestamped out-of-sample record. No prizes promised.',leaderboard)
    review=section('Open irregularities · nonblocking',table(['ID','Issue','Unverified field / action','Source'],[
        (['R01','Official player log is dynamic; no immutable official data snapshot retained','Ten displayed rows checked against NBA log on 2026-11-03; archive reproducible official source extract for future audits'],LOG),
        (['R02','Sample is selected, tiny and from 2025–26, not current 2026–27','Collect prior-only full-season player-game panel'],LOG),
        (['R03','No current official schedule/injury/player joins with frozen timestamps','Snapshot official inputs as-of prediction time'],INJ),
        (['R04','No official operator quote, settlement rules or jurisdiction specified','Quoted odds / vig / SGP payout left blank'],SCHEDULE),
        (['R05','No prospective picks, independent holdout or real-world execution','Win rate / profit / CLV left blank'],SCHEDULE),
        (['R06','No defined prop thresholds or paired binary observations','Hit phi and joint probabilities left blank'],LOG),
        (['R07','No contest sponsor, pool or enforceable payout policy','Reward amount blank; nothing awarded'],SCHEDULE),
        (['R08','Shared root site/navigation owned by earlier sessions','Microsite is additive at /nba-origin-lab/; root nav unchanged'],SCHEDULE),
    ]))
    page('review.html','Flagged for Review','07 / limitations','Missing evidence is visible. Blank fields are deliberate; flags do not turn into claims.',review)
    print('Generated',len(NAV),'pages; historical median',mid,'in-sample MAE',round(mae,2))

if __name__=='__main__': main()

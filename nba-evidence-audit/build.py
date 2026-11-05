#!/usr/bin/env python3
"""Build a bounded audit, not a verification of the full repository."""
from html import escape
from pathlib import Path
P=Path(__file__).resolve().parent
NBA='https://www.nba.com/stats/leaders?Season=2025-26'
INJ='https://official.nba.com/nba-injury-report-2026-27-season/'
GLOSS='https://www.nba.com/stats/help/glossary'
pages={
'index':('Executive summary','This is a bounded, independent review of selected claims in NBA Signal Lab, not a line-by-line certification of the repository. Historical model lines are not current recommendations. No audited profitable strategy, funded prize, current market price, or current slate is established here.',[
('Official input','NBA injury reports are updated throughout the day; a frozen projection must record the report time.','Official policy checked',INJ),
('Decision','Hold strategies and rewards until source data, timestamped prices, settlement rules, and prospective results are verified.','Proposed gate, not an NBA claim',GLOSS),
('Uncertainty','Statistical procedures can quantify uncertainty; they cannot remove luck or prove future profitability.','Methodological assessment',GLOSS),
('Scope','This review does not independently transcribe the 125 player-game records or verify all other repository rows.','Not verified',NBA)]),
'findings':('Findings & correlations','Numerical comparisons below are calculations from the existing repository output, not official NBA-published correlations. Official links identify relevant underlying data, not a verification of our computations.',[
('Direction of dependence','For the sample P(A and B)=0.512 and P(A)P(B)=0.467. Multiplication underestimates that observed joint rate, not overestimates it.','Calculated from existing output; input rows not reverified',NBA),
('Generalization','The sample comparison alone does not establish a future true joint probability or sportsbook mispricing. Pooling two players can also introduce player-mix effects.','Analysis; no prospective validation',NBA),
('Cross-game independence','Near-zero lag-one Pearson correlation does not establish independence of threshold bets, of different players, or of different games.','Analysis; unverified hypothesis',NBA),
('Power calculation','The existing engine uses a normal approximation for sample size, despite wording that describes an exact binomial power table. Its small-sample tail calculation is separate.','Code inspected; assumptions require review',NBA)]),
'strategies':('Strategies & validation','These are research proposals, not validated betting recommendations. Official source links provide data context and do not certify the proposed methods or thresholds.',[
('Singles','Freeze a pregame forecast and compare it with timestamped executable odds; settle consistently.','Pending: odds and prospective holdout',GLOSS),
('Cross-game parlays','Estimate joint outcomes on an untouched sample rather than assuming independence from lag-one correlation.','Pending: joint and market data',NBA),
('Same-game player combos','Estimate joint probabilities by player and threshold, with uncertainty and out-of-sample calibration.','Pending: sufficient data and rules',NBA),
('Leaderboard & rewards','Pre-register scoring, trials and eligibility; report uncertainty and keep prize amounts blank until funded.','Proposal; no funding verified',INJ)]),
'flagged':('Flagged for review','These findings concern existing materials; links to those materials are provided outside the official-source column. Do not treat unexamined rows as verified.',[
('F01 — reversed direction','Existing Signal Lab text says multiplying marginals overstates probability, but its own sample joint rate is larger than the product.','Needs correction by owner; see correlation page',NBA),
('F02 — independence','Near-zero autocorrelation does not demonstrate cross-game parlay independence.','Needs review by owner',NBA),
('F03 — luck','“Luck stripped” is misleading: variance remains even after statistical adjustment.','Needs review by owner',GLOSS),
('F04 — power','Sample-size routine uses a normal approximation; do not label it exact binomial power.','Needs review by owner',NBA),
('F05 — verification','Official leaders page is not itself a source for calculated combo correlations; individual source rows and computation need independent verification.','Unverified',NBA),
('F06 — current information','Prior slate and report snapshots are historical; no current lines or prices have been independently verified in this review.','Unverified',INJ)])}
nav=' '.join(f'<a href="{k}.html">{escape(v[0])}</a>' for k,v in pages.items())
for key,(title,intro,rows) in pages.items():
 body=''.join('<tr>'+''.join(f'<td>{escape(c)}</td>' for c in row[:3])+f'<td><a href="{escape(row[3],quote=True)}">Official NBA context</a></td></tr>' for row in rows)
 html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} | NBA evidence audit</title><link rel="stylesheet" href="style.css"></head><body><header><div><p class="eyebrow">OWN5 / RESEARCH</p><h1>NBA evidence audit</h1><p>Independent review · 5 November 2026</p><nav>{nav}</nav></div></header><main><h2>{escape(title)}</h2><p>{escape(intro)}</p><div class="table"><table><thead><tr><th>Topic</th><th>Finding</th><th>Status</th><th>Official source / context</th></tr></thead><tbody>{body}</tbody></table></div><aside><strong>Review the existing desk:</strong> <a href="../nba-signal-lab/index.html">Signal Lab</a> · <a href="../nba-signal-lab/correlations.html">Correlation claims</a> · <a href="../nba-signal-lab/flagged.html">Existing flags</a> · <a href="../research/nba-signal-lab/EXECUTIVE_SUMMARY.md">Original executive summary</a></aside><p class="foot">Official context links are not proof of analyst-derived quantities. No claim of full repository verification.</p></main></body></html>'''
 (P/f'{key}.html').write_text(html,encoding='utf-8')

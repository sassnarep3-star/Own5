"""Deterministic, dependency-free scoped dashboard. Facts and proposals stay separate."""
import json, html, csv
from pathlib import Path
ROOT=Path(__file__).resolve().parent
S={
 'injuries':('NFL injury report','https://www.nfl.com/injuries/','Checked displayed Week 10 report, first chunk only; not a complete league snapshot.'),
 'teams':('NFL official club directory','https://www.nfl.com/teams/','Checked directory and linked club identities.'),
 'was':('Commanders depth chart','https://www.commanders.com/team/depth-chart','Checked displayed offensive and defensive rows; not proof of game participation.'),
 'ne':('Patriots unofficial depth chart','https://www.patriots.com/team/depth-chart','Checked explicit unofficial disclaimer and offensive chart; not a confirmed lineup.'),
 'nist':('NIST scatter plots','https://www.itl.nist.gov/div898/handbook/eda/section3/scatterp.htm','Checked association/causation warning; does not endorse betting policy.'),
 'policy':('NFL policy URL — unavailable','https://operations.nfl.com/updates/football-ops/2017-nfl-injury-report-policy/','Returned 404 / Flag on the Play; no policy claims accepted.')}
# Rows: item, evidence/answer, missing information, disposition/action, source keys.
D={
'index':('Executive summary',[
 ('Decision now','Research and paper evaluation only.','Current calibrated prices and executable quotes','Do not place bets from this dashboard.',['injuries','nist']),
 ('Evidence scope','Selected official pages inspected on 2026-11-12 UTC.','All-team historical snapshots and independent reconciliation','This is a bounded review, not a line-by-line certification of the entire repository.',['injuries','teams']),
 ('Existing tools','NFL model and strategy lab already exist in this repository.','Current independent input verification','Keep historical model outputs separate from current evidence. See review page.',['teams']),
 ('Uncertainty','Association alone does not prove causality.','Evidence that a signal survives a genuinely future sample','Luck cannot be eliminated; quantify uncertainty and abstain when evidence is insufficient.',['nist']),
 ('Automation boundary','This release is a static reviewed snapshot.','Continuous authorized ingestion, scheduling, odds access and monitoring','No manual data entry required for this snapshot; it is not a live all-team tracker.',['injuries'])]),
'questions':('Decision questions & missing information',[
 ('What game and cutoff are priced?','','Official schedule ID, timezone, forecast timestamp and feature availability times','Discover with official game pages; reject inputs published after forecast cutoff.',['teams']),
 ('Who is available?','Report includes practice and game-status columns.','Final active/inactive list and report revisions','Archive official reports and reconcile club game-day announcements; blank status is not a medical clearance.',['injuries']),
 ('Who actually replaces a starter?','Club charts provide positional ordering; some are unofficial.','Confirmed lineup, substitutions, snap allocation and third/fourth-string roles','Join roster IDs, transactions, active lists and official gamebooks; never infer replacement from injury alone.',['was','ne']),
 ('How much does a replacement change the line?','','Historical point-in-time participation, opponents, scheme and uncertainty','Estimate only in training; compare models with/without role features on held-out weeks.',['injuries','nist']),
 ('Are prices executable?','','Operator, jurisdiction, timestamp, limits, two-sided odds, fees and settlement version','Obtain authorized operator records; no current market price asserted.',['teams']),
 ('Do correlations transfer?','','Paired official game observations, thresholds, sample window and holdout results','Measure continuous stats and binary leg outcomes separately; do not reuse team-season correlations as parlay dependence.',['nist']),
 ('Can rewards be paid?','','Budget, eligibility, jurisdiction and approved competition rules','Use paper-only provisional recognition; no cash rewards or gambling execution enabled.',['teams'])]),
'injuries':('Injuries & replacement evidence',[
 ('WAS · Lucas Patrick · C','Concussion; Did Not Participate In Practice; Out.','Replacement identity, depth and expected snaps','Verified displayed NFL row on review date only; replacement and impact unverified.',['injuries']),
 ('WAS · Colson Yankoff · TE','Knee; Did Not Participate In Practice; Out.','Confirmed replacement and impact','Chart lists John Bates then Colson Yankoff on a TE row; does not establish a promoted starter.',['injuries','was']),
 ('NE · Ben Brown','NFL report: C; Knee; Did Not Participate In Practice; Out.','Actual game-day role and replacement','Club unofficial chart places Brown first at LG and second at C. Position/role discrepancy requires review, not silent normalization.',['injuries','ne']),
 ('NE · Carlton Davis III · CB','Knee; Did Not Participate In Practice; Out.','Confirmed defensive replacement, third/fourth depth and matchup impact','No quantitative defensive deficiency claimed.',['injuries']),
 ('WAS · QB ordering','Chart displays Jayden Daniels, Marcus Mariota, Athan Kaliakmanis.','Final game-day participants and expected snaps','Chart-only ordering; do not label all as active or assert a depth-related betting edge.',['was']),
 ('League coverage','','Other players, all-team depth charts, final active lists and report revisions','UNVERIFIED / incomplete coverage. No live monitoring process deployed.',['teams','injuries'])]),
'strategies':('Signal research & validation',[
 ('S1 · singles · independent team strength','PROPOSAL: opponent-adjusted scoring/efficiency model, with shrinkage.','Official historical games, time-correct training and executable quotes','Compare with a simple scoring baseline; fit margin/total distributions; publish fair prices separately from market prices.',['teams','nist']),
 ('S2 · singles/props · replacement exposure','PROPOSAL: position-specific availability and expected participation.','Verified starters, substitutes, snaps and pregame status archives','Test incremental held-out forecast improvement; no hard-coded points per missing starter.',['injuries','was','ne']),
 ('S3 · player prop combos','PROPOSAL: shared pace, attempts and target-allocation model.','Official paired logs, active roles, thresholds and settlement rules','Fit joint outcomes; validate joint probabilities, not only each marginal.',['nist','injuries']),
 ('S4 · cross-game parlays','PROPOSAL: aggregate only independently validated legs.','Shared weather/schedule/strategy exposure and operator quote','Test dependence across games and common model errors; do not automatically multiply probabilities.',['nist']),
 ('G0 · provenance + contract','PROPOSED REQUIRED GATE','Official source, retrieval time, hash, player/game IDs, quote and settlement terms','Missing evidence blocks eligibility. Original records remain immutable.',['teams','injuries']),
 ('G1 · preregistration + leakage','PROPOSED REQUIRED GATE','Locked hypothesis, variants, cutoff and chronological folds','Record every tried variant; training precedes test and final holdout is untouched.',['nist']),
 ('G2 · predictive skill','PROPOSED REQUIRED GATE','Out-of-sample log loss, Brier score, calibration and interval coverage','Compare with locked baseline; thresholds and power plan must be preregistered, not chosen after results.',['nist']),
 ('G3 · economic skill + chance','PROPOSED REQUIRED GATE','Net returns, confidence intervals, price slippage, all attempted tests','Cluster uncertainty by game/week, correct multiple testing, and test null outcomes. CLV alone is not proof of profit.',['nist']),
 ('G4 · joint validation + robustness','PROPOSED REQUIRED GATE','Conditional dependence, role changes, season drift and drawdown','Pass joint calibration for combos; sensitivity and prospective paper test required.',['nist','injuries']),
 ('G5 · reproducibility + deployment','PROPOSED REQUIRED GATE','Locked artifacts, reproducible rerun, stale-data alarm, rollback','All gates must pass; a missing gate is blocked, never treated as passed.',['teams'])]),
'correlations':('Correlation & fair pricing',[
 ('QB passing yards vs receiver yards','','Official paired game logs and role-conditioned sample','Coefficient blank / UNVERIFIED. Report n, window, Pearson/Spearman and uncertainty when available.',['nist']),
 ('QB passing over + receiver over','','Exact thresholds, paired binary outcomes and push/void rules','Binary correlation and joint probability blank / UNVERIFIED; continuous r is not a combo price.',['nist']),
 ('RB rushing over + team win','','Official paired outcomes, role changes and game context','Joint probability blank / UNVERIFIED; a plausible football story is not a measured edge.',['nist']),
 ('Three-leg player prop combo','','Full joint distribution and operator settlement','Pairwise correlations alone do not determine a three-way joint probability. No fair price published.',['nist']),
 ('Origination workflow','PROPOSAL: train only on pre-cutoff official observations.','Held-out distribution calibration and current complete inputs','Score distribution → win/cover/total probabilities → fair odds; compare with quotes only after independent forecast is locked.',['teams','nist']),
 ('Derivation boundary','Model outputs are estimates, never official NFL lines.','Reproducible sourced input set','Because current complete inputs are missing, current lines, EV and recommended stakes remain blank.',['teams'])]),
'leaderboard':('Competition & rewards',[
 ('Singles division','','Validated out-of-sample submissions','Blocked; no ranking or reward issued.',['nist']),
 ('Parlays division','','Validated joint-outcome submissions','Blocked; do not rank by raw win count or cherry-picked returns.',['nist']),
 ('Player prop combos division','','Validated role-conditioned joint forecasts','Blocked; no ranking or reward issued.',['injuries','nist']),
 ('Proposed ranking policy','PROPOSAL: economic-skill lower confidence bound, forecast skill tie-break.','Approved scoring window, trial registry, risk cap and comparable unit stakes','Rank within division only after every gate passes; publish all failures and freeze season rules.',['nist']),
 ('Proposed reward policy','PROPOSAL: noncash recognition for eligible top performers.','Approved prize rules, budget and legal review','No cash prizes configured. Never reward a strategy solely for a lucky short run.',['nist'])]),
'suggestions':('Suggestions · review before implementation',[
 ('P0 · immutable evidence archive','PROPOSED / NOT IMPLEMENTED','Authorized access and retention policy','Preferred first step: timestamp + hash raw official responses; acceptance: every feature traces to pre-cutoff evidence.',['injuries','teams']),
 ('P0 · role reconciliation','PROPOSED / NOT IMPLEMENTED','Roster IDs, depth/active lists, transaction and gamebook feeds','Compare official chart ordering with confirmed lineup; acceptance: discrepancies block affected predictions.',['was','ne']),
 ('P0 · stale-data circuit breaker','PROPOSED / NOT IMPLEMENTED','Source-specific update expectations and alarm destination','Fail closed on missing or changed source schema; acceptance: synthetic stale/failure tests prevent publication.',['injuries']),
 ('P1 · evidence-first navigation','PROPOSED / NOT IMPLEMENTED IN ROOT','Final integration ownership of shared landing page','Recommend one NFL entry point with current-as-of date; root NBA summary and old NFL pages should have clear sport/date labels.',['teams']),
 ('P1 · reproducible experiment registry','PROPOSED / NOT IMPLEMENTED','Complete historical records and registered analysis plan','Prefer archived paper experiments before complex models; acceptance: deterministic results and untouched holdout.',['nist']),
 ('P2 · joint simulator','PROPOSED / NOT IMPLEMENTED','Validated singles and role-conditioned samples','Defer until ingestion and singles pass gates; acceptance: joint calibration survives future weeks.',['nist'])]),
'flagged':('Flagged for Review',[
 ('F01 · scope','Repository contains NFL, NBA and unrelated rental dashboards.','Full independent row-by-row source audit','Bounded review only. Root EXECUTIVE_SUMMARY.md is NBA-specific; do not present it as this NFL summary.',['teams']),
 ('F02 · historical lines','data/model_lines_2026_wk9.csv contains Week 9 dated outputs.','Current independent verification and refresh','Historical research only; not current actionable lines. Source links are not proof of present-day freshness.',['teams']),
 ('F03 · chart authority','Patriots explicitly calls chart unofficial.','Confirmed lineup and participation','Official publisher does not make chart ordering an official game-day lineup.',['ne']),
 ('F04 · position discrepancy','Ben Brown: C in NFL injury row; first LG / second C on club chart.','Game-day role reconciliation','Keep both observations; replacement and quantitative impact blank.',['injuries','ne']),
 ('F05 · policy URL failed','Attempted injury-policy URL returned 404.','Accessible current policy document','No reporting deadlines or policy definitions asserted from this URL.',['policy']),
 ('F06 · no current coefficients','','Sourced paired observations, exact thresholds and holdout','Current prop correlations, joint prices and market EV blank / UNVERIFIED.',['nist']),
 ('F07 · proposed thresholds','nfl_model/validation.py contains fixed sample and economic thresholds.','Independent justification and power analysis','Project policies, not NFL-certified standards. Existing boolean comparisons also need strict schema review before qualification.',['nist']),
 ('F08 · no continuous tracker','','Authorized ingestion, all-team coverage, persistent scheduler and monitoring','Snapshot only; no claim of automated current all-team injury/depth tracking.',['injuries','teams']),
 ('F09 · evidence currency','Dynamic pages can change after review.','Immutable full response archives and new retrieval','Selected rows reflect displayed source at review time, not permanent verified truth.',['injuries'])]),
'sources':('Source register',[(k,v[0],v[2],'Reviewed 2026-11-12 UTC; source supports only its stated scope.',[k]) for k,v in S.items()])}
nav=''.join(f'<a href="{k}.html">{html.escape(v[0])}</a>' for k,v in D.items())
for slug,(title,rows) in D.items():
    body=''
    for item,known,missing,action,keys in rows:
        cells=[item,known,missing,action]
        body+='<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in cells)+'<td>'+''.join(f'<a href="{S[k][1]}">{html.escape(S[k][0])}</a><br>' for k in keys)+'</td></tr>'
    page=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title} · NFL Decision Desk</title><link rel="stylesheet" href="style.css"></head><body><a class="skip" href="#main">Skip to content</a><header><div class="eyebrow">OWN5 / RESEARCH OPERATIONS</div><h1>NFL Decision Desk</h1><p>Evidence before action. Independent pricing before comparison.</p><span class="badge">SNAPSHOT · 12 NOV 2026 UTC</span> <span class="badge warn">PAPER RESEARCH ONLY</span></header><div class="layout"><nav aria-label="Categories">{nav}<a href="../nfl-strategy-lab/index.html">Existing NFL Strategy Lab ↗</a><a href="../index.html">Repository landing ↗</a></nav><main id="main"><h2>{title}</h2><p class="notice">Blank cells mean missing / unverified information, not zero. Proposals are project recommendations, not facts endorsed by the linked source. No current betting recommendation is issued.</p><label for="filter">Filter rows</label><input id="filter" type="search" placeholder="Search questions, evidence or flags"><p id="count" role="status">{len(rows)} rows</p><div class="table-wrap"><table><caption>{title} — row-level evidence and next actions</caption><thead><tr><th scope="col">Item</th><th scope="col">Known / answer</th><th scope="col">Missing information</th><th scope="col">Decision / next step</th><th scope="col">Official reference</th></tr></thead><tbody>{body}</tbody></table></div><p><a href="register.json">Download complete evidence register (JSON)</a></p><footer>Verification is limited to stated scope. No live feed, validated profit, reward entitlement, or risk-free outcome is claimed. <a href="README.md">Method and reproduction</a></footer></main></div><script src="app.js"></script></body></html>'''
    (ROOT/f'{slug}.html').write_text(page)
(ROOT/'register.json').write_text(json.dumps({'reviewed_on':'2026-11-12','sources':S,'pages':D},indent=2)+'\n')
print(f'Built {len(D)} pages; {sum(len(r) for _,r in D.values())} sourced rows')

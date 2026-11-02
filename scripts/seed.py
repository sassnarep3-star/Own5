"""Create the reviewed research register. Not a live odds/statistics importer."""
import json
from pathlib import Path

SOURCES = [
('REPO-AUDIT','Official project repository · GitHub API','Initial repository tree','https://api.github.com/repos/sassnarep3-star/Own5/git/trees/426b19d4981627243aa21b324903eab97cfb9d13','The official repository Git tree contains only README.md, a blob of size 6 bytes. Local inspection confirms its content is # Own5.','Repository audit only; this is not an NFL statistical source or evidence of a strategy edge.'),
('NFL-RULES','NFL Football Operations','2026 NFL rulebook','https://operations.nfl.com/rules-officiating/2026-nfl-rulebook','The page labels itself “2026 NFL RULEBOOK” and links the official PDF.','Rules and scoring context only; not sportsbook settlement rules.'),
('NFL-NGS','NFL Next Gen Stats','Metric glossary','https://nextgenstats.nfl.com/glossary','Time to Throw excludes sacks; the glossary defines CPOE, targeted air yards and YAC above expectation.','Definitions verified; no player-level historical tracking dataset acquired.'),
('NFL-INJ','NFL.com','Official injury report','https://www.nfl.com/injuries/','The retrieved page shows a 2026 week 8 injury report with practice and game status columns.','Live page, not an archived pre-kickoff injury feed; no historical availability inference.'),
('NFL-SCHED','NFL.com','NFL schedules','https://www.nfl.com/schedules/','The schedule page exposes year and week navigation and game links.','Not an immutable schedule archive; no result rows imported into a model.'),
('NFL-STATS','NFL.com','Player statistics','https://www.nfl.com/stats/player-stats/','The page provides passing, rushing and receiving categories and year navigation.','Fetched table lacks column headers in the text extraction. Numeric rows deliberately not imported.'),
('DK-GENERAL','DraftKings Sportsbook','General rules · Virginia','https://sportsbook.draftkings.com/help/general-betting-rules/general-rules','The retrieved introduction explicitly identifies DraftKings Virginia house rules and a hierarchy of rules.','Virginia-specific example, not universal rules or evidence of local eligibility. No odds feed obtained.'),
('DK-MARKET','DraftKings Sportsbook','Bet types and market rules','https://sportsbook.draftkings.com/help/general-betting-rules/market-rules','Whole-number two-way spreads and totals settle as Push when tied to the specified line.','Only the cited market definitions were checked. Exact prop/SGP void and participation rules remain unverified.'),
('SK-CV','scikit-learn maintainers','Cross-validation','https://scikit-learn.org/stable/modules/cross_validation.html','Training and testing on the same data is a methodological mistake; a test set is held out for final evaluation.','Official library documentation supports methodology, not evidence of NFL profitability.'),
('SK-TIME','scikit-learn maintainers','TimeSeriesSplit','https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html','Other CV methods can train on future data and evaluate on past data; comparable folds require equally spaced samples.','NFL records require custom chronological game/week grouping; do not blindly split irregular rows.'),
('SK-CAL','scikit-learn maintainers','Probability calibration','https://scikit-learn.org/stable/modules/calibration.html','Brier and log loss assess reliability, resolution and uncertainty; lower Brier alone does not prove better calibration.','Reliability diagrams and held-out evaluation are also needed.'),
('SC-CORR','SciPy maintainers','Pearson correlation','https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html','Pearson measures linear relationship; constant input has undefined correlation; confidence intervals are available.','Zero Pearson correlation does not establish independence; default parametric p-values need assumptions.'),
('SC-BOOT','SciPy maintainers','Bootstrap confidence intervals','https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html','Resamples with replacement; paired=True resamples common indices across paired arrays.','Game/week clustered resampling is a project adaptation, not a property of the default iid API.'),
('SM-MULTI','statsmodels maintainers','Multiple-testing corrections','https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html','Documents Holm, Benjamini/Hochberg and Benjamini/Yekutieli adjustments.','Use Holm as the project default; neither adjustment repairs leakage or invalid p-values.'),
]
sources=[dict(id=i,publisher=p,title=t,url=u,checked='2026-11-02',status='Checked',finding=f,limitation=l) for i,p,t,u,f,l in SOURCES]
facts=[]
def fact(i,name,definition,scope,src): facts.append(dict(id=i,metric=name,definition=definition,scope=scope,status='Definition checked',sources=[src]))
fact('F01','Time to Throw','Average time from snap to throw on pass attempts; sacks excluded.','Passing','NFL-NGS')
fact('F02','Intended Air Yards','Average air yards on all pass attempts; negative behind the line of scrimmage.','Passing','NFL-NGS')
fact('F03','Completion Probability','Completion probability based on tracking factors including separation and field location.','Passing','NFL-NGS')
fact('F04','Completion % Above Expectation','Actual completion percentage compared with expected completion percentage.','Passing','NFL-NGS')
fact('F05','Targeted Air Yards','Average passing air yards per target for a receiver.','Receiving','NFL-NGS')
fact('F06','Share of Team Air Yards','Receiver intended air yards divided by team intended air yards, expressed as a percentage.','Receiving','NFL-NGS')
fact('F07','YAC Above Expectation','Receiver yards after catch compared with expected yards after catch.','Receiving','NFL-NGS')
fact('F08','Rushing Efficiency','Total distance traveled as a ball carrier divided by rushing yards gained.','Rushing','NFL-NGS')
fact('F09','8+ Defenders in the Box','Frequency with which a rusher faces eight or more defenders in the box.','Rushing','NFL-NGS')
fact('F10','Whole-number two-way spread','A tie after applying the spread settles as Push under the cited rules.','Settlement · cited operator only','DK-MARKET')
fact('F11','Total points','Over/Under on a specified total; equality settles as Push under the cited rules.','Settlement · cited operator only','DK-MARKET')
strategies=[]
def strategy(i,name,market,signal,model,risk,src):
    strategies.append(dict(id=i,name=name,market=market,signal=signal,model=model,risk=risk,status='Blocked · data',gates_passed=0,sample=None,roi=None,brier=None,edge=None,rank=None,reward=None,sources=src))
strategy('S01','Opponent-adjusted team strength','Single','Lagged team scoring and opponent strength; shrink early-season estimates.','Regularized home/away score distribution; price moneyline and spread from joint score samples.','Roster drift, schedule strength and rule changes.',['NFL-RULES','NFL-SCHED','SK-TIME'])
strategy('S02','Possession & pace totals','Single','Lagged play volume and scoring efficiency, conditioned on game context.','Hierarchical possession and points model; retain discrete total and push probability.','Pace may change with score; do not use realized game pace as a pregame feature.',['NFL-SCHED','DK-MARKET','SK-CV'])
strategy('S03','Availability repricing','Single','Official injury updates available before the prediction cutoff.','Scenario-weighted lineup forecasts with explicit unknown-status uncertainty.','Questionable is not a measured probability of absence; no automatic numeric conversion.',['NFL-INJ','SK-TIME'])
strategy('S04','Receiver opportunity','Player prop','Lagged targets, intended air yards share and receiving opportunity.','Separate volume from efficiency; predict an integer reception distribution and yards distribution.','Role changes, target competition and incomplete as-of data.',['NFL-NGS','NFL-STATS','SK-CAL'])
strategy('S05','Rushing workload','Player prop','Lagged rushing volume, efficiency and box-count context.','Hierarchical workload model; scenario-based attempts and yards.','Game-script dependence; rushing efficiency is not a standalone causal signal.',['NFL-NGS','NFL-STATS','SK-CV'])
strategy('S06','Cross-game value basket','Parlay','Individually qualified legs with synchronized executable prices.','Estimate joint win probability; multiply marginals only with justified independence.','Common weather/regime exposure and offered parlay price can erase single-leg edge.',['SC-CORR','DK-GENERAL','SK-CAL'])
strategy('S07','Quarterback × receiver','Prop combo','Joint passing and receiving opportunities within the same game.','Shared game/drive simulation; count simulations where every leg wins.','No fixed positive correlation assumption; pairwise correlation alone cannot price a combo.',['NFL-NGS','SC-CORR','DK-MARKET'])
strategy('S08','Game-script combo','Prop combo','Team score scenarios jointly with rushing or receiving workload.','Joint discrete outcomes; use actual quoted combo payout and exact settlement rules.','Selection bias, unsupported correlation assumptions and operator repricing.',['NFL-RULES','SC-CORR','DK-GENERAL'])
gates=[
('G01','Provenance & settlement','Every observation has an official URL, captured timestamp, stable event/player ID and applicable settlement version. Missing values block that market.','All','NFL-STATS'),
('G02','As-of integrity','Features, injury updates and odds must be captured before prediction time; prediction before kickoff. Deduplicate records and keep each game in one fold.','All','SK-TIME'),
('G03','Preregistered walk-forward','Freeze candidate code, features, selection rule, folds and test family before the untouched holdout. Tune only inside chronological training windows.','All','SK-CV'),
('G04','Predictive quality','Held-out Brier and log loss must beat preregistered naive and available no-vig market baselines; inspect reliability diagrams and subgroup uncertainty.','All','SK-CAL'),
('G05','Dependence & payout','Estimate held-out joint outcomes, sample size and game/week-clustered confidence intervals. No independence shortcut without evidence; quote exact combo price.','Parlays / combos','SC-CORR'),
('G06','Skill evidence','Positive lower bound of a preregistered 95% game/week-block bootstrap interval for net flat-stake return; Holm-adjusted p ≤ 0.05 across all tried candidates. Power analysis determines sample size, not an arbitrary bet count.','All','SM-MULTI'),
('G07','Forward replication & risk','Freeze before prospective paper testing. Require a second nonoverlapping evaluation window, verified costs/limits, robustness checks and preregistered exposure/drawdown limits. No real-money deployment here.','All','SC-BOOT'),
]
gates=[dict(id=i,name=n,rule=r,applies=a,status='Not run',basis='Project policy · proposed',sources=[s]) for i,n,r,a,s in gates]
correlations=[]
for i,pair,unit,control in [
('C01','QB passing yards × receiver receiving yards','Paired player-game outcomes','QB/receiver identity, opportunity and opponent'),
('C02','Team points × RB rushing attempts','Paired team/player-game outcomes','Pregame strength, opponent and availability'),
('C03','Receiver A × receiver B receptions','Paired teammate-game outcomes','Shared passing volume and competition for targets'),
('C04','Game total × QB passing yards','Paired game/player outcomes','Opponent, pace and availability'),
('C05','Cross-game leg wins','Binary outcomes at frozen bet thresholds','Week-level regime and synchronized decision time'),
('C06','Strategy net returns','Game/week aggregated flat-stake returns','Overlapping legs, stakes and market exposure'),
]: correlations.append(dict(id=i,pair=pair,unit=unit,controls=control,pearson=None,ci=None,n=None,joint_win=None,status='Unverified · no matched sample',sources=['SC-CORR','SC-BOOT']))
markets=[
('M01','Moneyline','P(home win), P(tie), P(away win)','For no-push binary markets: fair decimal = 1 / p. For tie-as-push: fair decimal = (1 − p_push) / p_win.','Freeze the market’s tie and overtime treatment.',['DK-MARKET','NFL-RULES']),
('M02','Point spread','Distribution of home score − away score','For home handicap h, win if margin + h > 0; push if = 0. Fair decimal = (1 − p_push) / p_win.','Report a handicap and side price, not a mean margin alone.',['DK-MARKET','NFL-RULES']),
('M03','Game total','Distribution of home score + away score','For over line t, win if total > t; push if = t. Fair decimal = (1 − p_push) / p_win.','Keep integer score mass and overtime rules.',['DK-MARKET','NFL-RULES']),
('M04','Player prop','Player outcome distribution conditional on participation','Evaluate probability at the exact threshold; retain equality mass when push is possible.','DNP, stat corrections and void rules not yet verified.',['NFL-STATS','DK-GENERAL']),
('M05','Parlay / prop combo','Full joint settlement distribution','For all-win/no-push only: fair decimal = 1 / P(all win). General EV = Σ P(state) × net return(state).','Actual quote required; pushes/voids can alter the payout.',['SC-CORR','DK-GENERAL']),
]
markets=[dict(id=i,market=m,output=o,method=f,caution=c,probability=None,fair_odds=None,status='Method only · not fitted',sources=s) for i,m,o,f,c,s in markets]
flags=[
('R01','Historical prices missing','High','No official, timestamped executable odds archive was obtained. No EV, closing-line value or ROI can be reported.','S01–S08 / all markets',['DK-GENERAL']),
('R02','As-of outcome dataset missing','High','Official pages were inspected, but no complete game/player history with pregame feature snapshots was acquired. All candidate strategies remain untrained.','All validation gates',['NFL-STATS','NFL-SCHED']),
('R03','Correlation values unavailable','High','No matched held-out samples. All coefficients, sample sizes, joint hit rates and intervals are blank. Do not substitute intuitive signs.','C01–C06',['SC-CORR']),
('R04','Prop & combo settlement incomplete','High','Exact participation, void, overtime and stat-correction rules for each proposed prop/combo are not verified.','M04–M05',['DK-GENERAL','DK-MARKET']),
('R05','Injury policy URL unreadable','Medium','An attempted NFL Football Operations injury-policy URL returned only “Skip to main content”. No policy claims were taken from it; the official injury report was inspected instead.','Availability research',['NFL-INJ']),
('R06','No validation or skill claim','High','No empirical gates have run. An attractive backtest alone would not remove luck; uncertainty, multiple testing and prospective replication remain necessary.','Leaderboard and strategies',['SK-CV','SM-MULTI','SC-BOOT']),
('R07','Rewards are not funded','Medium','A paper competition policy is specified, but no sponsor, budget, prize amount or payment mechanism is verified. Reward amounts stay blank; no cash contest is running.','Leaderboard',['SK-CV']),
('R08','Jurisdiction not established','High','Retrieved operator general rules explicitly apply to Virginia. This is research only, not an eligibility determination or betting service for any location.','All markets',['DK-GENERAL']),
('R09','Live-source drift & incomplete headers','Medium','Source checks are dated snapshots of visible text, not a continuous feed. The extracted NFL player table omitted headers; numeric player rows were excluded rather than guessed.','Source register / NFL statistics',['NFL-STATS']),
('R10','Empty starting repository','Low','Initial repository contained only README.md (# Own5); no preexisting datasets, algorithms or applications existed to audit. All new empirical fields remain blank.','Repository audit',['REPO-AUDIT']),
]
flags=[dict(id=i,issue=t,severity=s,detail=d,scope=sc,status='Needs review',sources=src) for i,t,s,d,sc,src in flags]
competition=[
('L01','Eligibility','All seven gates must pass with independent audit artifacts. Singles, parlays and prop combos are separate divisions. No candidate is currently eligible.',['SK-CV']),
('L02','Ranking','Within a division, rank eligible candidates by the lower 95% clustered net-return bound on the same preregistered evaluation window; tie-break with lower log loss, then lower drawdown.',['SC-BOOT','SK-CAL']),
('L03','Anti-gaming','Log all trials, including abandoned candidates; one frozen submission per strategy version. Apply Holm correction across the registered family. Deduplicate overlapping bets.',['SM-MULTI']),
('L04','Rewards','Proposed non-cash research badges: Evidence Leader (rank 1), Replicated (forward gate), Transparent (complete audit). Monetary rewards disabled until terms, sponsor and eligibility are verified.',['SK-CV']),
('L05','Risk accounting','Use flat 1-unit paper stakes for comparability, record all costs, pushes, voids and rejected quotes. Aggregate correlated exposure by game and week; compare with abstain and market baselines.',['DK-GENERAL','SC-CORR']),
]
competition=[dict(id=i,topic=t,rule=r,basis='Project policy · proposed',sources=s) for i,t,r,s in competition]
data=dict(as_of='2026-11-02',sources=sources,facts=facts,strategies=strategies,gates=gates,correlations=correlations,markets=markets,flags=flags,competition=competition,predictions=[])
Path('data/research.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print('Wrote reviewed register: ', {k:len(v) for k,v in data.items() if isinstance(v,list)})

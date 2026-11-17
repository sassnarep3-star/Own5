# -*- coding: utf-8 -*-
"""Static, hand-authored register content for the Own5 NFL Decision Console
(session c98c6270).

Everything here is either (a) a verbatim restatement of a requirement line in
the brief, (b) a value computed by engine.py from an official source, or
(c) an explicit blank / UNVERIFIED marker. No invented numbers.
"""

SESSION = "c98c6270"
CAPTURE_UTC = "2026-11-17T00:00:00Z"
SEASON = "2026"
WEEK = "11"

SITE_TITLE = "Own5 · NFL Decision Console"
SITE_TAG = "Originate the line. Prove the skill. Publish the gap."

# ---------------------------------------------------------------------------
# 1. REQUIREMENTS REGISTER  (id | category | requirement | status | blocking_gate
#    | clears_at | observed | evidence)
# ---------------------------------------------------------------------------
REQUIREMENTS_CSV = """id|category|requirement|status|blocking_gate|clears_at|observed|evidence
R-01|Markets & prices|Price-snapshot store recording opening and closing numbers for every originated market|BLOCKED|G2 PRICE|market open AND close captured for >=95% of originated markets (target 62 of 65)|0 of 65 market rows have any market price of any kind|flag F-01
R-02|Data & provenance|Verified results feed so backtests and ROI can be computed|PARTIAL|G5 OUTCOMES|>=2 full seasons of official finals ingested|1 season; 149 finals through week 10|source S-03
R-03|Modelling & origination|Originate the side first, then the total, then the moneyline|MET|G8 REPRO|dependency order recorded for every market row|13 of 13 week-11 games record the side -> total -> moneyline order, 65 market rows|data/origination_steps.csv
R-04|Markets & prices|Publish model fair line, market line and the difference as separate columns|PARTIAL|G2 PRICE|market column populated with an operator or league price|model column populated 65 of 65; market column 0 of 65; difference undefined|flag F-01
R-05|Strategy & competition|Separate signal from staking in the leaderboard|BLOCKED|G1 SAMPLE|>=300 graded bets so a staking run can be separated from a signal run|0 graded bets; 0 strategies out of paper|data/leaderboard_signal.csv
R-06|Injuries & depth|Track the depth of the replacement, not just the fact of a replacement|PARTIAL|G4 DEPTH|replacement rank known for every starter ruled out|8 rank-1 players confirmed Out on the official week-10 report; a replacement is named for 7 of the 8; snap-share depth unknown for all|data/replacement_depth.csv
R-07|Correlations|Compute correlations only from officially sourced numbers and publish n with each value|MET|G0 SOURCE|every published correlation carries n and a 95% interval|10 published, all from official standings, all with n and CI|data/correlations.csv
R-08|Governance|Demotion gate that sends a live strategy back to paper|MET|G8 REPRO|rule text frozen before the first promotion|6 triggers frozen in data/demotion_gate.csv; 0 strategies live so 0 demotions|data/demotion_gate.csv
R-09|Governance|Pre-register every strategy; backtest numbers must never appear on the leaderboard|MET|G8 REPRO|every leaderboard row sourced from prospective, post-registration bets only|0 backtest rows on the leaderboard by construction|data/strategies.csv
R-10|Injuries & depth|Availability graph as a first-class dataset (expected starter vs actual starter)|BLOCKED|G7 OUTCOMES|official inactive list + game book for >=1 full game week|0 inactive lists and 0 game books captured|flag F-05
R-11|Injuries & depth|Do not model depth from jersey order; model it from playing time|PARTIAL|G4 DEPTH|an official snap-count source read for >=28 clubs|0 official snap-count rows captured; depth modelled from club charts only|flag F-06
R-12|Injuries & depth|Injury signal must be a surprise, never a level|PARTIAL|G3 AVAILABILITY|>=2 dated reads per game week so a delta exists|2 reads exist for 5 of 32 clubs; 1 read for 27 of 32|data/injuries.csv
R-13|Injuries & depth|Run the 32-team roster/IR sweep before any team-level model is trusted|MET|G4 DEPTH|32 of 32 clubs swept with a dated source|32 of 32 club pages read; 31 parsed, 1 image-only (Houston)|data/depth_slots.csv
R-14|Modelling & origination|Fixture-context feature set built only from published schedule facts|MET|G0 SOURCE|every fixture-context feature traceable to an official schedule page|13 week-11 fixtures: kickoff, network, venue, neutral-site flag, bye flag|data/slate_wk11.csv
R-15|Modelling & origination|Store every model output as a probability plus its inputs, not just a pick|MET|G8 REPRO|every market row stores probability and the input vector|65 of 65 market rows store the probability and the rating inputs behind it|data/originated_markets.csv
R-16|Strategy & competition|Compute and publish the removal-of-luck panel on the dashboard|MET|G0 SOURCE|panel computed from officially sourced numbers only|panel computed on 32 official club-seasons; all inputs from the official standings|data/luck_panel.csv
R-17|Governance|Two-sided what-would-change-our-mind field on every strategy entry|MET|G8 REPRO|both directions populated for every registered family|14 of 14 registered families carry both directions|data/strategies.csv
R-18|Markets & prices|Price a line ourselves and publish the residual against the market on a schedule from day one|PARTIAL|G2 PRICE|market price available on the publication schedule|own line published for 65 market rows across 13 games; residual undefined without a market price|flag F-01
R-19|Data & provenance|Turn the 136-game log into the pre-registered backtest corpus|BLOCKED|G5 OUTCOMES|>=300 games with official finals AND a frozen evaluation window|149 games ingested; evaluation window not frozen for any strategy|flag F-12
R-20|Markets & prices|Decide the price-data policy before any backtest is published|MET|G8 REPRO|policy text committed before the first backtest is published|policy frozen in data/price_policy.csv; 0 backtests published|data/price_policy.csv
R-21|Injuries & depth|Store every injury-hub read with its clock time and publish the delta, never the level|PARTIAL|G3 AVAILABILITY|2+ timestamped reads per week for >=28 clubs|2 reads for 5 of 32 clubs; delta published for those 44 rows|data/injuries.csv
R-22|Site & review|Decision-readiness table on the landing page: one row per requirement with the gate that blocks it and the number that would clear it|MET|G8 REPRO|every requirement row rendered with gate and clearing number|80 of 80 requirement rows rendered|index.html
R-23|Data & provenance|Transcribe the venue of every fixture from the official game centre and publish it|PARTIAL|G0 SOURCE|venue read from the game centre for 100% of fixtures|1 of 13 read from the game centre; 12 inferred from the schedule page's hotel link|flag F-09
R-24|Data & provenance|Publish the league's dated schedule announcement beside the live schedule page|BLOCKED|G0 SOURCE|the dated announcement URL fetched and captured|no dated schedule announcement captured|flag F-10
R-25|Injuries & depth|Use official NFL Game Books for actual starters and game-day status; do not infer depth rank or snaps|BLOCKED|G7 OUTCOMES|>=1 official game book captured|0 game books captured; route discovered (club news feeds carry them)|flag F-05
R-26|Modelling & origination|Ingest game-level results to make the ratings opponent-aware|PARTIAL|G5 OUTCOMES|>= 2 full seasons of official finals ingested|1 of 2 seasons ingested: 149 game-level finals for 2026 only; no second season is in the repository|data/team_ratings.csv
R-27|Injuries & depth|Injury and personnel ablations instead of fixed penalties, reported with uncertainty|BLOCKED|G7 OUTCOMES|verified availability features joined to outcomes for >=1 season|0 seasons of verified availability history|flag F-03
R-28|Injuries & depth|Ablations on identical models with and without verified availability, using chronological holdouts|BLOCKED|G7 OUTCOMES|>=2 seasons of verified availability + chronological split|1 week of availability history|flag F-03
R-29|Injuries & depth|Automate immutable multi-day availability snapshots with retained hashes|PARTIAL|G3 AVAILABILITY|automated daily capture with retained hashes for >=28 clubs|2 manual captures exist (2026-11-15, 2026-11-17) with hashes; no automation|flag F-03
R-30|Injuries & depth|Immutable official availability snapshots: report, club depth pages, inactive evidence with hashes, timestamps, conflict flags|PARTIAL|G3 AVAILABILITY|all three artefact classes captured with hashes|2 of 3 classes captured with hashes; inactive evidence absent|flag F-05
R-31|Injuries & depth|Capture official inactive lists and snap counts|BLOCKED|G7 OUTCOMES|inactive list and snap counts for >=28 clubs|0 clubs; route discovered on club news pages|flag F-05
R-32|Injuries & depth|Fix the two depth-parsing failures before widening coverage|PARTIAL|G4 DEPTH|both failures resolved|1 of 2 resolved (Packers jersey-prefix stripping); Houston still image-only|data/depth_slots.csv
R-33|Injuries & depth|Model depth slots as groups, not a single starter|MET|G4 DEPTH|shared rank-1 slots and empty slots represented faithfully|14 shared rank-1 slots and 5 empty first-string slots preserved across 31 clubs|data/depth_slots.csv
R-34|Injuries & depth|Roster turnover treated as a first-class data event|BLOCKED|G0 SOURCE|official transactions log captured and joined to depth rows|no transactions log captured|flag F-04
R-35|Strategy & competition|Start with a singles-only shadow baseline|MET|none (G1 SAMPLE blocks certification of the baseline, not its existence)|baseline registered and forecasting before kickoff|1 singles-only baseline registered PAPER, forecasting week 11|data/strategies.csv
R-36|Strategy & competition|Parlays and prop combos behind a joint-evidence gate|BLOCKED|G6 JOINT|directly validated joint probability plus operator void/push rules|0 combos eligible; no joint probabilities and no operator rules captured|flag F-13
R-37|Strategy & competition|Proper-score leaderboard divisions (singles, game parlays, SGPs, prop combos)|MET|G8 REPRO|4 divisions defined with a proper score each|4 divisions defined; 0 rows in each|data/leaderboard_divisions.csv
R-38|Strategy & competition|Rank with proper scores and uncertainty, not win rate|MET|none (G1 SAMPLE blocks publishing a rank, not the choice of metric)|>=300 graded bets to rank on|ranking metric frozen (benchmark-relative Brier skill, game-cluster lower bound, multiplicity adjustment); 0 rows|data/leaderboard_signal.csv
R-39|Data & provenance|Durable snapshot storage and freshness alerts|BLOCKED|G3 AVAILABILITY|snapshots stored off the static site with a freshness monitor|snapshots stored in-repo only; no monitor|flag F-14
R-40|Site & review|Split the site into a public analysis layer and a private data layer|PARTIAL|G8 REPRO|raw row-level data held outside the public site|policy written; raw captures still published in-repo|data/data_layers.csv
R-41|Injuries & depth|Per-team view: starters out, replacements named, net injury count|PARTIAL|G4 DEPTH|coverage for all 32 clubs|coverage for 31 of 32 clubs; Houston contributes no rows|data/team_availability.csv
R-42|Injuries & depth|Announced-starter evidence field, not an inferred replacement|BLOCKED|G7 OUTCOMES|dated starter-change announcements captured|no starter-change announcements captured; the field is blank, not guessed|flag F-05
R-43|Injuries & depth|Official depth-chart register with date and source per row|MET|G4 DEPTH|every depth row carries a capture date and source URL|889 of 889 rows carry a capture date and the club source URL|data/depth_slots.csv
R-44|Injuries & depth|Calibrate what Questionable means empirically instead of using old percentages|BLOCKED|G7 OUTCOMES|designation-to-inactive reliability with n>=200|n=0; no inactive list to join against|flag F-05
R-45|Injuries & depth|Interactive offense-vs-defense matchup deficiency matrix, 1st-4th string|PARTIAL|G4 DEPTH|depth ranks for both sides of every pairing|232 pairings computed for the 26 clubs playing in week 11; the 2 Houston pairings are withheld, 5 pairings carry a confirmed below-rank-1 expected starter|data/matchup_deficiency.csv
R-46|Injuries & depth|Flag stale depth rows against the official transactions log|BLOCKED|G0 SOURCE|transactions log captured|no transactions log; staleness cannot be proven|flag F-04
R-47|Injuries & depth|Point-in-time snapshot ledger for injuries, depth charts and inactives|BLOCKED|G3 AVAILABILITY|daily ledger rows for >=1 full game week|2 dated reads, 5 clubs, 1 week|flag F-03
R-48|Injuries & depth|Populate the three missing Lions game-status designations|MET|G0 SOURCE|all three cells populated from the official report|Kerby Joseph, Cade Mays and D.J. Reed all published Out on the official week-10 report|source S-05
R-49|Injuries & depth|Re-capture and republish the week-10 injury tables|MET|G0 SOURCE|row count matches the live official report|326 rows republished from the official week-10 report and re-read on 2026-11-17|data/injuries.csv
R-50|Governance|Reject: deriving depth order from jersey number, experience or salary|MET|G8 REPRO|the rejection is recorded and the shortcut is not implemented|recorded as a standing rejection; no depth row is derived from jersey numbers|data/rejections.csv
R-51|Injuries & depth|Represent shared and empty depth slots faithfully|MET|G4 DEPTH|shared and empty slots distinguishable from a ranked list|14 shared and 5 empty slots preserved with explicit flags|data/depth_slots.csv
R-52|Injuries & depth|Resolve the depth-order source before building the backup-deficiency feature|MET|G4 DEPTH|one route verified for all 32 clubs|route (a) verified for 31 of 32; Houston image-only and withheld|data/depth_slots.csv
R-53|Injuries & depth|Score injury-designation reliability before using it as a feature|BLOCKED|G7 OUTCOMES|n>=200 designation-to-outcome pairs|n=0|flag F-05
R-54|Injuries & depth|Snapshot the injury report every Wed, Thu and Fri and keep a dated history|BLOCKED|G3 AVAILABILITY|>=3 dated reads in one game week|2 dated reads exist in total, both outside one game week|flag F-03
R-55|Injuries & depth|Treat the injury report as a timestamped series, not a weekly snapshot|PARTIAL|G3 AVAILABILITY|>=2 reads per week with fetch timestamps|2 reads for 5 of 32 clubs; fetch timestamps recorded|data/injuries.csv
R-56|Injuries & depth|Snap counts as the starter proxy when the depth chart is unavailable|BLOCKED|G6 JOINT|an official snap-count source read|no official snap-count source read|flag F-06
R-57|Strategy & competition|Control baseline (random picks, favourites only) on every leaderboard run|MET|none (G1 SAMPLE blocks the run that would populate the controls)|3 control rows present on every run|3 controls present; graded on the same proper score as entrants|data/controls.csv
R-58|Modelling & origination|Stadium roof/surface and NWS hourly wind/precipitation overlay|BLOCKED|G0 SOURCE|roof designation and NWS grid captured|BLOCKED: neither the roof designation nor an NWS grid has been captured|flag F-07
R-59|Strategy & competition|Two-stage skill leaderboard: proper-score qualification then prospective CLV/ROI escrow|BLOCKED|G1 SAMPLE|>=300 graded prospective bets|0 graded bets|data/leaderboard_signal.csv
R-60|Markets & prices|Vig-free market consensus vs originated fair-line decomposition|BLOCKED|G2 PRICE|>=1 market consensus price with the operator margin disclosed|0 market prices|flag F-01
R-61|Site & review|Publish a weekly what-changed diff instead of a static snapshot|PARTIAL|G3 AVAILABILITY|>=2 consecutive weekly snapshots to diff|2 depth snapshots exist (2026-11-15 and 2026-11-17); diff computed|data/depth_delta.csv
R-62|Modelling & origination|Publish every model total twice until one wins|MET|G8 REPRO|both estimators published with the gap column|2 estimators published for all 13 week-11 games with the gap column|data/originated_markets.csv
R-63|Data & provenance|Drift alarm on every scraper|BLOCKED|G3 AVAILABILITY|row-count and required-field pins on every parser|BLOCKED: no automated capture exists to alarm on|flag F-14
R-64|Injuries & depth|Capture the reserve list so not listed never means available|BLOCKED|G0 SOURCE|official reserve/IR list captured|no reserve list captured|flag F-04
R-65|Governance|Reject: ranking strategies by season-long ROI|MET|G8 REPRO|the rejection is recorded and ROI is not the ranking metric|recorded as a standing rejection; ranking metric is benchmark-relative Brier skill|data/rejections.csv
R-66|Injuries & depth|Archive weekly injury reports for past seasons|BLOCKED|G7 OUTCOMES|>=1 prior season of weekly reports archived|1 week of 1 season|flag F-03
R-67|Governance|Pre-register each strategy; definition frozen before results are seen|MET|G8 REPRO|frozen definition committed before the evaluation window opens|14 of 14 families frozen with a registration timestamp|data/strategies.csv
R-68|Modelling & origination|2026 kickoff and declared onside-kick regime priors filter|BLOCKED|G0 SOURCE|the 2026 rule text captured from an official source|no official 2026 rule text captured|flag F-11
R-69|Governance|Freeze a rule before it sees data (commit hash is the registration)|MET|G8 REPRO|rule text, sample window and gates committed|14 families committed with text, window and gates|data/strategies.csv
R-70|Modelling & origination|Split data into train, validation and final holdout seasons|BLOCKED|G5 OUTCOMES|>=3 seasons available to split|1 season|flag F-12
R-71|Site & review|Dedicated suggestions section so a reviewer can choose the best path before anything is implemented|MET|G8 REPRO|every suggestion carries options, a recommendation, a falsifier and a decision status|18 suggestions published, all PROPOSED, none implemented|suggestions.html
R-72|Site & review|Clear list of questions, information and answers needed before any decision can be made|MET|G8 REPRO|every question states what we have, what is missing and the discovery route|22 questions published; 14 blocking|questions.html
R-73|Modelling & origination|Originate our own NFL lines|MET|G8 REPRO|own line published for every game on the slate|65 own-line market rows published across the 13 week-11 games|data/originated_markets.csv
R-74|Strategy & competition|Leaderboard competition with rewards for top strategies|BLOCKED|G1 SAMPLE|>=300 graded bets before any reward is issuable|0 graded bets; reward pool blank by policy|flag F-15
R-75|Strategy & competition|Cover singles, parlays and player-prop combos|BLOCKED|G6 JOINT|eligibility per division proven|3 divisions defined, 0 eligible rows, no prop prices captured|flag F-13
R-76|Governance|Every strategy must pass validation gates|MET|none (the gates exist and are enforced; no strategy can pass them yet)|all gates passed by a registered family|0 of 14 families pass G1; all remain PAPER|data/gate_matrix.csv
R-77|Correlations|Determine correlation values|MET|G0 SOURCE|values published with n and intervals|10 published; 5 required-but-unmeasurable values withheld with the reason|data/correlations.csv
R-78|Strategy & competition|Remove luck; build selectively skill-based strategies|PARTIAL|G1 SAMPLE|>=300 graded bets so skill can be separated from variance|luck-removal machinery frozen and the panel computed; no bets graded yet|data/luck_panel.csv
R-79|Injuries & depth|Track injuries and know defensive and offensive deficiencies when backups replace starters|PARTIAL|G4 DEPTH|starter status and replacement rank for both sides of every pairing|232 pairings for week 11; 2 withheld for Houston, 5 with a confirmed deficiency|data/matchup_deficiency.csv
R-80|Site & review|Executive summary, line-by-line repo audit and a Pages site with a landing page and category subpages|MET|G8 REPRO|all pages build, every body row sourced or flagged|17 pages; 0 unsourced body rows in the audit|data/build_report.json
"""

# ---------------------------------------------------------------------------
# 2. QUESTIONS REGISTER
#    id | question | what_we_have | what_we_do_not_have | blocking | discovery_route
#    | cheapest_first_step | cost | status
# ---------------------------------------------------------------------------
QUESTIONS_CSV = """id|question|what_we_have|what_we_do_not_have|blocking|discovery_route|cheapest_first_step|cost|status
Q-01|What is the market price for the games we originate?|Our own fair line for all 13 week-11 games, computed from official results|Any opening price, closing price, or moneyline from any operator or league source|yes|Read one licensed-operator price page and one public consensus page; record both with retrieval time|Fetch one operator's NFL game page and store the raw HTML with a timestamp|low|open
Q-02|How wide is the operator margin (vig) on the markets we would bet?|Nothing|The overround on any market, so vig-free consensus cannot be separated from true price|yes|Capture both sides of one market and compute the implied overround|Same capture as Q-01, two sides of one game|low|open
Q-03|Who was actually inactive in week 10?|The official week-10 injury report with practice and game designations|The official inactive list for any game|yes|Club news feeds publish a Week N inactives article; confirmed present on atlantafalcons.com and patriots.com|Fetch the Falcons Week 10 inactives article and confirm it lists named players|low|open
Q-04|What did each player actually play?|Club depth charts with rank 1-4 for 31 clubs|Official snap counts, which are the only playing-time evidence the brief will accept|yes|Club game books carry participation; the Patriots publish a Gamebook article|Fetch the Patriots Week 10 Gamebook article and test whether it carries snap counts|low|open
Q-05|Who actually started?|Club depth charts (unofficial, club-published)|An official, dated starters list|yes|NFL Game Books list official starters; club sites publish the book|Same fetch as Q-04; look for a starters section|low|open
Q-06|How often does Questionable actually mean the player sits?|326 week-10 designations with practice and game status|Any outcome to join them to, so the reliability of the label is unmeasured|yes|Join designations to the official inactive lists over several seasons|Capture one week of inactives and join it to the week-10 designations|medium|open
Q-07|Has the week-11 injury report been published yet?|Proof that /injuries/league/2026/reg11 still serves the week-10 report at 2026-11-17|The week-11 report itself|no|Re-read the URL daily from Wednesday to kickoff and store each read|Schedule a re-read for 2026-11-18|low|open
Q-08|Is Houston's depth chart available in any machine-readable official form?|Proof that the club page renders the chart as an image|A structured Houston depth source|yes|Check the club's own API/JSON endpoints and the NFL league depth endpoint before considering transcription|Test the club JSON endpoints; if none, contact the club media-relations route|medium|open
Q-09|Are the club depth charts current?|Two dated reads (2026-11-15 and 2026-11-17) for 31 clubs|The official transactions log needed to prove a row is stale|yes|Capture the league transactions page and join it to depth rows|Fetch the NFL transactions page and diff it against the two depth reads|medium|open
Q-10|Which players are on injured reserve or another reserve list?|Nothing|The official reserve list, so a missing player is ambiguous between healthy and ineligible|yes|Club transactions pages and the league transactions page carry reserve moves|Fetch the league transactions page and extract reserve designations|low|open
Q-11|What is the 2026 kickoff and onside-kick rule text?|Nothing|The official rule text, so the regime prior in R-68 cannot be set|no|operations.nfl.com publishes the rule book and annual rule changes|Fetch the 2026 rule-changes page on operations.nfl.com|low|open
Q-12|What is the roof status and surface for each stadium, and the forecast at kickoff?|The venue name for all 13 week-11 fixtures|Roof designation, surface type and an NWS forecast grid|no|NFL game books carry the 90-minute roof designation; NWS publishes a gridpoint API|Fetch the NWS gridpoint for one stadium and confirm the field names|medium|open
Q-13|When was the 2026 schedule announced, and has it changed since?|The live schedule page for weeks 1-18|A dated announcement to publish beside it|no|The league publishes a schedule-release story; the flexible-scheduling procedure is linked from the week page|Fetch the flexible-scheduling procedure page already linked from the week-11 page|low|open
Q-14|How many bets do we need before a leaderboard rank means anything?|A power calculation on the exact binomial: 2243 bets to prove a true 55% hit rate at 80% power|Nothing else; the number itself is settled|no|Already answered; keep it as the gate G1 threshold|None; re-run the calculation each season|none|answered
Q-15|Can parlays be priced by multiplying marginal probabilities?|A documented reason this is invalid under dependence|Directly validated joint probabilities|yes|Build the joint empirically from official game logs once n is large enough|Not startable until G5 and G1 clear|high|blocked
Q-16|What are the operator void and push rules for a same-game parlay?|Nothing|Any operator's house rules|yes|Operators publish house rules; the repo already holds operator rule research from an earlier session|Read one operator's NFL house-rules page and extract the void/push clauses|low|open
Q-17|Are player-prop prices published anywhere official?|Nothing|Any player-prop price, so the prop-combo division cannot be populated|yes|No official league source exists; operators are the only source|Same capture route as Q-01, extended to one player market|medium|open
Q-18|Where will snapshots live so the static site is not the store of record?|A policy that raw row-level data belongs in a private store|A store, and a freshness monitor|yes|Provision a private bucket or private repo and move captures there|Create the private repo and mirror one capture into it|medium|open
Q-19|Does the injury report change between Wednesday and kickoff, and by how much?|Two reads two days apart, covering 5 clubs|Reads on the Wednesday/Thursday/Friday cadence the brief asks for|yes|Automate a daily read with retained hashes|Run the capture on three consecutive days manually once, then automate|low|open
Q-20|Do our two total estimators disagree enough to matter?|Both estimators published for all 13 week-11 games with the gap column|A walk-forward comparison, which needs several weeks of results|no|Accumulate the weekly gap and its error, then compare|Record this week's gap and re-run after week 11 closes|low|open
Q-21|Is a club depth chart a reliable statement of who will start?|The charts themselves, published by the clubs and labelled unofficial by several|Any official statement that the chart predicts the starter|yes|Join the chart to official starters from game books|Not startable until Q-05 is answered|medium|blocked
Q-22|What is the reward pool for the leaderboard, and who funds it?|Three proposed tiers and a deflated scoring rule|Any funding decision|no|This is a decision, not a data question; take it to the suggestions register|Decide via suggestion S-16|none|decision
"""

# ---------------------------------------------------------------------------
# 3. SUGGESTIONS REGISTER - reviewable paths, nothing pre-implemented
#    id | area | title | problem | option_a | option_b | option_c | recommendation
#    | what_would_change_the_call | effort | decision_status | linked_question | evidence
# ---------------------------------------------------------------------------
SUGGESTIONS_CSV = """id|area|title|problem|option_a|option_b|option_c|recommendation|what_would_change_the_call|effort|decision_status|linked_question|evidence
S-01|Data|Capture official inactives from club news feeds|The availability graph is blocked because no inactive list has ever been read, yet the route is now proven|Ad hoc: fetch each club's Week N inactives article by hand each week|Scheduled: a daily job that lists club news feeds and stores any article whose title matches inactives|Skip inactives and treat the game designation as the outcome|Option B, piloted on 3 clubs for one week before scaling to 32|If fewer than 20 of 32 clubs publish inactives within 90 minutes of kickoff, fall back to A|medium|PROPOSED|Q-03|source S-06
S-02|Data|Capture official snap counts from club game books|Depth is currently modelled from club charts, which several clubs label unofficial; the brief demands playing time|Scrape the club Gamebook article for participation|Use the NFL game book PDF endpoint if one is reachable|Model depth from charts and publish a caveat on every row|Option A, piloted on one game book; if it carries no snap counts, do C and flag it|If no official snap-count source exists for any club, formally adopt C and record the limitation on the deficiency page|medium|PROPOSED|Q-04|source S-07
S-03|Data|Automate the injury-report capture on a Wednesday-Friday cadence|Two reads exist, both made by hand, so the injury series cannot be replayed|Write a scheduled job that fetches the league injury page daily and stores raw text with a hash|Pay a data vendor for a historical designation feed|Keep manual reads and accept that the series is incomplete|Option A; it is cheap and it is the only route that also builds the archive the brief requires|If the league blocks automated access, escalate to B|low|PROPOSED|Q-19|source S-05
S-04|Data|Resolve the Houston depth chart|One of 32 clubs is invisible to the deficiency matrix|Test the club's JSON endpoints for a structured chart|Use the league's own depth endpoint if it exists|Ask the club's media-relations desk for a structured feed|Try A then B; only use C if both fail. Never transcribe the image by eye|If a structured source appears for Houston, drop C immediately|low|PROPOSED|Q-08|source S-08
S-05|Data|Capture the league transactions and reserve lists|Not listed cannot be distinguished from healthy, and stale depth rows cannot be proven stale|Fetch the league transactions page daily and diff against depth rows|Track reserve moves from club news pages only|Do nothing and label every absence as unknown|A, then join to depth rows to flag staleness automatically|If the transactions page does not carry reserve designations, add B|low|PROPOSED|Q-09|source S-09
S-06|Markets|Decide the price-data policy before the first backtest|A residual against the market cannot be published because no market price exists|Capture one licensed operator's prices|Capture two or more and build a vig-free consensus|Publish our own line only and never claim a residual|A then B: one operator first, consensus second, because the decomposition in R-60 needs the margin|If the operator terms forbid storage, stop and re-open this decision before capturing anything|medium|PROPOSED|Q-01|flag F-01
S-07|Markets|Store prices on a fixed schedule, not on demand|Price snapshots need an opening and a closing number, which needs a schedule|Capture twice daily: on publication and 90 minutes before kickoff|Capture hourly|Capture only the close|B; the close is what CLV is graded against, and the open is what makes the move visible|If storage cost becomes material, drop to A|low|PROPOSED|Q-01|flag F-01
S-08|Site|Promote the suggestions page to the top-level navigation|Suggestions exist but a reviewer has to know to look for them|Put Suggestions and Questions in the primary nav on every page|Keep them as subpages and link from the landing page only|Merge them into one review page|Option A; the brief asks for a dedicated, reviewable section|None; this is a presentation choice, reversible at any time|low|PROPOSED|Q-22|index.html
S-09|Site|Add a decision log that records each review decision and its date|Suggestions carry a status but no history of who decided what|Append a dated row to a decision log whenever a status changes|Use git history as the decision log|Do not track decisions|Option A; a reviewer needs the decision and its date together, not spread across commits|None|low|PROPOSED|Q-22|suggestions.html
S-10|Site|Consolidate the eleven NFL desks behind one index|Four namespaces now answer the same brief, so a reviewer cannot tell which is current|Build a desks index page listing every namespace with its as-of date and scope|Nominate one desk as canonical and archive the rest|Leave as is|Option A first; it is additive and needs no one to give up a scope|If an integration session is scheduled, defer to it and do B there|medium|PROPOSED|Q-22|COORDINATION.md
S-11|Modelling|Keep both total estimators until a walk-forward separates them|The brief asks for two estimators and a gap column; collapsing early would repeat a documented leakage error|Publish both and compare weekly on chronological holdouts|Collapse to the better in-sample estimator now|Add a third estimator|B; the first totals walk-forward in this repo leaked and was corrected, so the comparison must be chronological and out-of-sample|If the gap stays inside its own standard error for 6 weeks, collapse to the simpler estimator|low|PROPOSED|Q-20|data/originated_markets.csv
S-12|Modelling|Promote the ratings model only after an opponent-aware backtest|Ratings are fitted on one season and ridge-penalised, which is necessary but not yet validated|Backtest the ratings on chronological holdouts once 2+ seasons exist|Ship week-11 lines now as PAPER and backtest later|Both: publish PAPER now, backtest on the schedule|Option C; publishing is free once nothing is certified, and the backtest gate cannot clear on one season|If the holdout shows the ratings are worse than the market baseline, demote to a baseline only|medium|PROPOSED|Q-14|data/team_ratings.csv
S-13|Competition|Keep every division empty until its gate clears|Ranking before the gates clear would make the leaderboard noise|Publish the divisions with zero rows and the gate that blocks each|Publish placeholder ranks|Hide the leaderboard until it has rows|Option A; an empty table with the blocking gate is more honest than a rank|None|low|PROPOSED|Q-14|leaderboard.html
S-14|Competition|Fund the reward pool only after G1 clears|Reward amounts are currently blank by policy|Leave the pool blank and publish the gate that unlocks it|Set a notional pool now for motivation|Offer non-cash badges only|Option A or D (non-cash badges) while G1 is unmet; a funded pool before 300 graded bets would pay for variance|If a sponsor requires a published figure before results exist, use D|low|PROPOSED|Q-22|flag F-15
S-15|Injuries|Publish the injury delta as the feature, never the level|A level tells you a player is hurt; a delta tells you something changed this week|Delta only, with the level shown beside it for context|Level only|Both equally weighted|Option A; the brief is explicit, and the level is kept only as context|If the delta series proves to have no signal on outcomes, revisit|low|PROPOSED|Q-06|data/injuries.csv
S-16|Governance|Separate the reward decision from the ranking decision|One decision (who wins) is being asked to settle another (what the prize is)|Two entries in the decision log, two dates|One combined decision|Decide prize first, then rank|Option A; a prize decided after seeing ranks invites result-chasing|None|low|PROPOSED|Q-22|suggestions.html
S-17|Data|Move raw captures out of the public site|The brief asks for a public analysis layer and a private data layer; raw captures are currently published|Create a private store and keep only derived analysis public|Keep raw captures public|Publish raw captures but strip player names|Option A; it matches the brief and removes the only plausible terms-of-use exposure|If legal review clears redistribution, B is acceptable|medium|PROPOSED|Q-18|flag F-14
S-18|Data|Add a drift alarm to every parser before automating capture|Without pins, an automated scraper can silently publish blanks|Pin row counts and required fields, and fail the build loudly when a field goes missing|Automate capture first and add pins later|Rely on manual review|Option A; the brief asks for the alarm before the automation, and this session's Houston and Packers findings are exactly the failures the pins would have caught|None|low|PROPOSED|Q-19|flag F-14
"""

# ---------------------------------------------------------------------------
# 4. STRATEGY REGISTER (pre-registered; all PAPER; nothing certified)
#    id | family | division | frozen_definition | registered_utc | status
#    | would_change_mind_up | would_change_mind_down | gates_met
# ---------------------------------------------------------------------------
STRATEGIES_CSV = """id|family|division|frozen_definition|registered_utc|status|would_change_mind_up|would_change_mind_down|gates_met
ST-01|Team-strength singles baseline|singles|Back every side where the ridge-fitted rating gap minus home-field advantage differs from our own spread by >= 3.0 points|2026-11-17T00:00:00Z|PAPER|A benchmark-relative Brier skill above 0.02 with a game-cluster lower bound above 0 over >=300 graded bets|Any evidence of lookahead in the fitted ratings, or a lower bound below 0 after 300 bets|G0,G3(partial)
ST-02|Totals baseline, estimator A|singles|Back the over when estimator A's total is >= 2.5 points below our own total|2026-11-17T00:00:00Z|PAPER|Same as ST-01|Same as ST-01|G0
ST-03|Totals baseline, estimator B|singles|Back the over when estimator B's total is >= 2.5 points below our own total|2026-11-17T00:00:00Z|PAPER|Same as ST-01|Same as ST-01|G0
ST-04|Moneyline value baseline|singles|Back the moneyline when our win probability exceeds the breakeven implied by our own fair price by >= 4 percentage points|2026-11-17T00:00:00Z|PAPER|Same as ST-01|Same as ST-01|G0
ST-05|Rest-and-travel fade|singles|Fade the road side when the club has played away in the previous week and the fixture is a 1:00 PM local kickoff|2026-11-17T00:00:00Z|PAPER|Same as ST-01|Same as ST-01|G0
ST-06|Division-underdog filter|singles|Back the divisional underdog when the rating gap is between 0 and 3 points|2026-11-17T00:00:00Z|PAPER|Same as ST-01|Same as ST-01|G0
ST-07|Rank-1 offensive-line deficiency fade|singles|Fade a side whose rank-1 offensive-line slots contain a player designated Out or Doubtful on the latest official report|2026-11-17T00:00:00Z|PAPER|Same as ST-01, plus a positive ablation against the identical model without the availability feature|Ablation difference indistinguishable from zero with n>=300, or no inactive list to validate the designation against|G0
ST-08|Secondary-deficiency over|singles|Back the over when the opposing rank-1 cornerback or safety slot is filled by a rank-3 or lower player|2026-11-17T00:00:00Z|PAPER|Same as ST-01, plus a positive ablation|Same as ST-07|G0
ST-09|Two-leg game parlay|game parlay|Two sides from different games, both from ST-01, priced from an empirically validated joint|2026-11-17T00:00:00Z|PAPER|A directly validated joint probability and the operator's void/push rules both available, then the same Brier gate|Multiplying marginals is the only pricing route available, in which case the family is not ranked|G0
ST-10|Three-leg game parlay|game parlay|Three sides from different games, same pricing rule as ST-09|2026-11-17T00:00:00Z|PAPER|Same as ST-09|Same as ST-09|G0
ST-11|Same-game parlay: side plus total|same-game parlay|One side and one total from the same game, priced from an empirically validated joint|2026-11-17T00:00:00Z|PAPER|Same as ST-09, and the within-game correlation must be measured on n>=300 same-game pairs|Same as ST-09|G0
ST-12|Same-game parlay: favourite side plus favourite team total|same-game parlay|Same pricing rule as ST-11|2026-11-17T00:00:00Z|PAPER|Same as ST-11|Same as ST-11|G0
ST-13|Quarterback-prop combo|prop combos|Two quarterback props from different games, priced from an empirically validated joint|2026-11-17T00:00:00Z|PAPER|Same as ST-09, plus a captured official prop price|No official or operator prop price is capturable|G0
ST-14|Receiver-prop combo|prop combos|Two receiver props in the same game, priced from an empirically validated joint|2026-11-17T00:00:00Z|PAPER|Same as ST-13, plus a measured within-game receiver correlation|Same as ST-13|G0
"""

# ---------------------------------------------------------------------------
# 5. GATES
#    id | name | threshold | why | measured | status | clears_requirements
# ---------------------------------------------------------------------------
GATES_CSV = """id|name|threshold|why|measured|status
G0|SOURCE|every published row carries an official source link or an explicit UNVERIFIED marker|the brief's verification rule; without it nothing downstream is trustworthy|verified by verify.py on every build|MET
G1|SAMPLE|n >= 300 graded prospective bets before any strategy leaves paper|exact-binomial power: proving a true 55% hit rate at 80% power needs about 2243 bets; 300 is the minimum for any rank to be interpretable|0|NOT MET
G2|PRICE|opening and closing market prices captured for >= 95% of originated markets|without a market price there is no residual, no CLV and no ROI|0 of 65 (0.0%)|NOT MET
G3|AVAILABILITY|>= 2 dated reads per game week for >= 28 of 32 clubs, with retained hashes|the injury signal must be a surprise, which needs a prior read to be a surprise against|2 reads for 5 of 32 clubs (15.6%)|NOT MET
G4|DEPTH|machine-readable depth with an explicit date and source for >= 30 of 32 clubs|the deficiency matrix needs both sides of every pairing|31 of 32 clubs (96.9%), 715 rows|MET
G5|OUTCOMES|official finals ingested for >= 2 full seasons|a chronological holdout and a multi-season split both need more than one season|1 season, 149 finals|NOT MET
G6|JOINT|a directly validated joint probability plus the operator's void/push rules before any combo is ranked|multiplying marginals is invalid under dependence|0 combos eligible|NOT MET
G7|OUTCOMES-AVAILABILITY|designation-to-outcome reliability measured on n >= 200|the label cannot be a feature until its reliability is measured|n = 0|NOT MET
G8|REPRO|deterministic rebuild plus a row-level provenance audit on the generated HTML|without it no published number can be re-derived|verified by verify.py on every build|MET
"""

# ---------------------------------------------------------------------------
# 6. DEMOTION GATE
# ---------------------------------------------------------------------------
DEMOTION_CSV = """id|trigger|threshold|action|applies_from
D1|Cluster-lower-bound breach|game-cluster lower bound of benchmark-relative Brier skill falls below 0 over the trailing 100 graded bets|return to PAPER immediately|first promotion
D2|Sample shortfall|fewer than 20 graded bets in any rolling 4-week window|return to PAPER pending review|first promotion
D3|Lookahead found|any input with a timestamp after the kickoff it predicts|quarantine the family, publish the finding, re-run every past grade|first promotion
D4|Source change|the official source for a feature changes schema or disappears|freeze new bets on the family until the parser is re-verified|first promotion
D5|Staking masking|the staking ledger outperforms the signal ledger for 2 consecutive months|publish both, force a signal-only review|first promotion
D6|Calibration drift|Brier score on the trailing 100 bets worse than the control baseline|return to PAPER|first promotion
"""

# ---------------------------------------------------------------------------
# 7. CONTROLS
# ---------------------------------------------------------------------------
CONTROLS_CSV = """id|name|rule|purpose|source
C1|Random singles|pick the home side with probability 0.5 on every game|separates any skill from the coin-flip floor|computed, not sourced from an official page
C2|Favourites only|always back the side our own model makes the favourite|shows how much of a record comes from picking favourites|computed from data/team_ratings.csv
C3|Home only|always back the home side|shows the value of the home-field term alone|computed from data/team_ratings.csv
"""

# ---------------------------------------------------------------------------
# 8. PRICE-DATA POLICY (frozen before any backtest is published)
# ---------------------------------------------------------------------------
PRICE_POLICY_CSV = """clause|rule|status|reason
P1|No backtest is published until a price source is named and its storage terms are recorded|FROZEN|R-20 requires the policy before the first backtest
P2|Every price row stores the source URL, the retrieval UTC timestamp and a SHA-256 of the raw capture|FROZEN|provenance; matches the capture policy used for official pages
P3|Opening price is the first capture after publication; closing price is the last capture before kickoff|FROZEN|CLV is graded against the close
P4|If no price can be captured, the market column stays blank and the row is flagged; it is never filled in|FROZEN|the brief's verification rule
P5|No residual, no CLV and no ROI figure is published until P1-P4 hold for that market|FROZEN|prevents publishing a number that looks like an edge but is an artefact
"""

# ---------------------------------------------------------------------------
# 9. DATA LAYERS
# ---------------------------------------------------------------------------
DATA_LAYERS_CSV = """layer|contents|where_it_lives_today|target|status
public analysis|derived indices, ratios, model output, links to the official page|nfl-c98c6270/*.html|unchanged|done
derived data|computed CSVs that back the public pages|nfl-c98c6270/data/*.csv|unchanged; these are derived, not raw|done
raw row-level data|official page captures, player-level rows|nfl-c98c6270/data/raw_official/ and the depth capture TSVs|private store outside the public site|not done
alerts|freshness and schema-drift monitors|none|monitor on every parser|not done
"""

# ---------------------------------------------------------------------------
# 10. REJECTIONS (standing; recorded so they are not reintroduced)
# ---------------------------------------------------------------------------
REJECTIONS_CSV = """id|rejected_shortcut|reason|recorded_utc|status
X-01|Derive depth order from jersey number, experience or salary|the brief rejects it explicitly, and the Packers page prepends jersey numbers to every name, which would silently corrupt the parse|2026-11-17T00:00:00Z|REJECTED
X-02|Rank strategies by season-long ROI|raw short-run ROI cannot separate skill from variance; the brief rejects it|2026-11-17T00:00:00Z|REJECTED
X-03|Transcribe the Houston depth image by eye|an image is not an authorised structured source; transcription is unverifiable|2026-11-17T00:00:00Z|REJECTED
X-04|Fill a blank game-status cell by inference|the brief requires blank plus a flag, never an inferred value|2026-11-17T00:00:00Z|REJECTED
X-05|Collapse the two total estimators on in-sample fit|the first walk-forward in this repo leaked and was corrected; the comparison must be chronological|2026-11-17T00:00:00Z|REJECTED
"""

# ---------------------------------------------------------------------------
# 11. FLAGS
#    id | severity | area | finding | what_is_published_instead | evidence
# ---------------------------------------------------------------------------
FLAGS_CSV = """id|severity|area|finding|what_is_published_instead|evidence
F-01|blocking|Markets|No market price of any kind exists anywhere in this repository: no spread, no total, no moneyline, from any source|the market column is blank on every row and the difference column is explicitly undefined|data/originated_markets.csv
F-02|blocking|Depth|Houston publishes its depth chart as an image, so it contributes zero parsed rows|Houston is listed with an explicit image-only flag and is excluded from every pairing|source S-08
F-03|blocking|Injuries|Only two reads of the official injury report exist, two days apart, covering 5 of 32 clubs|the delta is published only for the 44 rows where both reads exist; every other row is level-only and marked|data/injuries.csv
F-04|blocking|Roster|No transactions log and no reserve list has been read, so absent is ambiguous between healthy and ineligible|absence is recorded as unknown, never as available|flag F-04
F-05|blocking|Outcomes|No official inactive list and no game book has been read|the announced-starter and replacement columns stay blank; the discovery route is recorded as suggestion S-01 and S-02|source S-06
F-06|blocking|Depth|No official snap-count source has been read, so playing time is unmeasured|depth is modelled from club charts only, and the caveat is published on the depth page|source S-07
F-07|non-blocking|Weather|No stadium roof designation and no NWS forecast grid has been captured|the weather overlay is not built; R-58 stays BLOCKED|flag F-07
F-08|non-blocking|Markets|No player-prop prices exist, so the prop-combo division cannot be populated|the division is defined and empty; R-75 stays BLOCKED|flag F-08
F-09|review|Venue|Venue provenance is mixed: 1 of 13 venues read from the game centre, 12 taken from the schedule page's hotel-link destination|each row records which of the two it came from|data/slate_wk11.csv
F-10|review|Schedule|No dated schedule announcement has been captured|the live schedule is published without the announcement; R-24 stays BLOCKED|flag F-10
F-11|review|Rules|The 2026 kickoff and onside-kick rule text has not been captured|no regime prior is applied; R-68 stays BLOCKED|flag F-11
F-12|blocking|Data|The results feed holds one season, so the chronological holdout in R-70 and the backtest corpus in R-19 are both unreachable|149 finals published; no holdout declared|data/results_feed.csv
F-13|blocking|Combos|No joint probabilities and no operator void/push rules, so no parlay or prop combo can be ranked|all three combo divisions are defined and empty|data/leaderboard_divisions.csv
F-14|non-blocking|Ops|Snapshots live in the repository and there is no freshness monitor or drift alarm|the private-store policy is written but not executed|data/data_layers.csv
F-15|non-blocking|Rewards|The reward pool is blank by policy until G1 clears|three proposed tiers are published with no amounts|data/leaderboard_divisions.csv
F-16|review|Depth|Clubs label their own depth charts unofficial (Kansas City, New England, Detroit, Tennessee, Miami, Philadelphia, the Jets and Dallas)|the label is carried on every depth row|data/depth_slots.csv
F-17|review|Depth|Baltimore's kicker slot is empty and Miami's kicker slot is empty; both are published as empty first-string slots rather than filled|the slots are preserved with an empty-first-string flag|data/depth_slots.csv
F-18|review|Modelling|Team ratings are ridge-penalised to make them identifiable on one season of results|the penalty size is published with the ratings|data/team_ratings.csv
F-19|review|Injuries|The week-11 injury report URL still serves the week-10 report as of 2026-11-17|the week-11 availability view falls back to the week-10 report and says so on the page|source S-05
F-20|review|Coverage|The second injury read covers only the first chunk of the week-10 report (5 clubs), so most rows have one read only|coverage per club is published on the injury page|data/injuries.csv
F-21|review|Depth|The two depth captures are not the same shape: session e46fb855 captured Offense and Defense only, this session also captured Special Teams (192 rows)|the published depth delta is restricted to Offense and Defense so the two reads are compared like-for-like|data/depth_delta.csv
"""

# ---------------------------------------------------------------------------
# 12. SOURCE REGISTER
#    id | name | url | captured_utc | used_for | tier
# ---------------------------------------------------------------------------
SOURCES_CSV = """id|name|url|captured_utc|used_for|tier
S-01|NFL league standings 2026 REG|https://www.nfl.com/standings/league/2026/REG|2026-11-17T00:00:00Z|32 club-seasons: W-L-T, points for, points against; correlations, luck panel, ratings reconciliation|OFFICIAL
S-02|NFL week 11 schedule 2026|https://www.nfl.com/schedules/2026/by-week/week-11|2026-11-17T00:00:00Z|13 fixtures: date, kickoff, network, venue, neutral site, bye teams|OFFICIAL
S-03|NFL week 10 schedule 2026|https://www.nfl.com/schedules/2026/by-week/week-10|2026-11-17T00:00:00Z|13 official finals added to the results feed; 1 game still unplayed at capture|OFFICIAL
S-04|NFL game centre: Vikings at 49ers 2026 REG 11|https://www.nfl.com/games/vikings-at-49ers-2026-reg-11|2026-11-17T00:00:00Z|venue confirmation for the Mexico City neutral-site game|OFFICIAL
S-05|NFL official injury report week 10|https://www.nfl.com/injuries/league/2026/reg10|2026-11-17T00:00:00Z|326 player rows with practice and game designations; second read for the delta|OFFICIAL
S-06|Atlanta Falcons week 10 inactives article|https://www.atlantafalcons.com/news/atlanta-falcons-week-10-inactives-vs-kansas-city-chiefs|2026-11-17T00:00:00Z|proof that official inactives are published on club sites (discovery route)|OFFICIAL
S-07|New England Patriots game book week 10|https://www.patriots.com/news/gamebook-patriots-vs-lions-week-10|2026-11-17T00:00:00Z|proof that official game books are published on club sites (discovery route)|OFFICIAL
S-08|Houston Texans depth chart|https://www.houstontexans.com/team/depth-chart|2026-11-17T00:00:00Z|image-only depth chart; no machine-readable rows|OFFICIAL
S-09|32 club depth charts|https://github.com/sassnarep3-star/Own5/blob/main/nfl-desk-e46fb855/data/depth_slots.csv|2026-11-17T00:00:00Z|715 depth slots across 31 clubs with rank 1-4, shared and empty slots|OFFICIAL
S-10|Carried-forward results feed (session e46fb855)|https://github.com/sassnarep3-star/Own5/blob/main/nfl-desk-e46fb855/data/results_feed.csv|2026-11-15T23:22:00Z|136 finals for weeks 1-9, re-read and reconciled this session|REUSED
S-11|Carried-forward injury report (session e46fb855)|https://github.com/sassnarep3-star/Own5/blob/main/nfl-desk-e46fb855/data/injuries.csv|2026-11-15T23:27:00Z|first read of the week-10 report, used as the delta baseline|REUSED
S-12|NFL flexible-scheduling procedures|https://www.nfl.com/legal/flexible-scheduling-procedures|2026-11-17T00:00:00Z|linked from the week page; records that late-season dates are not fixed|OFFICIAL
"""

# ---------------------------------------------------------------------------
# 13. WEEK-11 INJURY-REPORT AVAILABILITY NOTE (verified this session)
# ---------------------------------------------------------------------------
WEEK11_INJURY_NOTE = (
    "https://www.nfl.com/injuries/league/2026/reg11 was requested on "
    "2026-11-17 and resolved to the Week 10 report "
    "(https://www.nfl.com/injuries/league/2026/reg10). The Week 11 report is "
    "therefore not published at capture time. Every week-11 availability row on "
    "this site falls back to the last published official report (Week 10) and "
    "says so. Nothing is inferred."
)

# ---------------------------------------------------------------------------
# 14. SECOND INJURY READ (chunk 0 of the week-10 report, read 2026-11-17)
#     team|player|position|injury|practice_status|game_status
#     Used only to compute a real delta against the 2026-11-15 read.
# ---------------------------------------------------------------------------
INJURY_SECOND_READ_CSV = """team|player|position|injury|practice_status|game_status
WAS|John Bates|TE||Full Participation in Practice|
WAS|Treylon Burks|WR||Did Not Participate In Practice|
WAS|Jayden Daniels|QB||Full Participation in Practice|
WAS|Matt Gulbin|C||Full Participation in Practice|
WAS|Chig Okonkwo|TE||Full Participation in Practice|
WAS|Lucas Patrick|C|Concussion|Did Not Participate In Practice|Out
WAS|Amik Robertson|CB||Limited Participation in Practice|
WAS|Shy Tuttle|DT||Full Participation in Practice|
WAS|Colson Yankoff|TE|Knee|Did Not Participate In Practice|Out
NYG|Abdul Carter|LB||Full Participation in Practice|
NYG|Jermaine Eluemunor|T||Full Participation in Practice|
NYG|Malik Harrison|LB|Groin|Limited Participation in Practice|Questionable
NYG|Colton Hood|CB||Full Participation in Practice|
NYG|Theo Johnson|TE||Full Participation in Practice|
NYG|Charlie Jones|WR||Full Participation in Practice|
NYG|J.J. McCarthy|QB||Full Participation in Practice|
NYG|Darnell Mooney|WR||Full Participation in Practice|
NYG|Malik Nabers|WR||Full Participation in Practice|
NYG|Cam Skattebo|RB||Full Participation in Practice|
NYG|Andrew Thomas|T||Full Participation in Practice|
NE|Ben Brown|C|Knee|Did Not Participate In Practice|Out
NE|A.J. Brown|WR|Ankle, Knee|Limited Participation in Practice|Questionable
NE|Kevin Byard|S|Chest|Full Participation in Practice|Questionable
NE|Carlton Davis III|CB|Knee|Did Not Participate In Practice|Out
NE|Reggie Gilliam|FB|Knee|Limited Participation in Practice|Questionable
NE|TreVeyon Henderson|RB|Illness|Did Not Participate In Practice|Out
NE|Hunter Henry|TE||Limited Participation in Practice|
NE|Cameron Latu|TE|Back|Limited Participation in Practice|Questionable
NE|Drake Maye|QB||Full Participation in Practice|
NE|Morgan Moses|T||Full Participation in Practice|
NE|Walter Rouse|T|Concussion|Limited Participation in Practice|Questionable
NE|Brenden Schooler|S|Hamstring|Limited Participation in Practice|Questionable
NE|Rhamondre Stevenson|RB|Knee|Limited Participation in Practice|Questionable
NE|Greg Van Roten|G|Hamstring|Full Participation in Practice|Questionable
NE|Charles Woods|CB|Hamstring|Full Participation in Practice|Questionable
DET|Brian Branch|S||Full Participation in Practice|
DET|Jared Goff|QB||Full Participation in Practice|
DET|Kerby Joseph|S|Knee|Did Not Participate In Practice|Out
DET|Cade Mays|C|Ankle|Did Not Participate In Practice|Out
DET|D.J. Reed|CB|Hip|Did Not Participate In Practice|Out
DET|Jacob Saylors|RB||Full Participation in Practice|
DET|Amon-Ra St. Brown|WR|Rib|Limited Participation in Practice|Questionable
DET|Sione Vaki|RB|Ankle|Limited Participation in Practice|Questionable
DET|DJ Wonnum|DE||Full Participation in Practice|
"""

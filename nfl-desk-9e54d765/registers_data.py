"""Register content for desk 9e54d765: suggestions and questions.

Every row names what is known, what is missing and the route that would find it. Nothing here
is auto-approved: `review_status` is the owner's decision field and the desk only pre-fills it
where this session actually built the thing and the build is the evidence.
"""

SUGGESTION_DRAFT = "draft — awaiting the owner's decision; nothing is implemented"
SUGGESTION_ACCEPTED = 'accepted 2026-11-19 by this session and built here; the evidence path is the check'

SUGGESTIONS = [
    ('S01', 'Rank the leaderboard by Brier skill against the closing line, never by win rate',
     '(a) win rate, (b) flat ROI, (c) benchmark-relative Brier skill with a cluster interval',
     '(c) — win rate and ROI cannot separate skill from variance at any sample this project '
     'can reach', 'HIGH — it decides what every other number means', SUGGESTION_ACCEPTED,
     'the first certified strategy shows a positive lower bound after the multiplicity '
     'correction',
     'if a strategy with a negative skill interval out-earns one with a positive interval over '
     '300 settled bets, revisit the ranking', 'data/backtest_families.csv'),
    ('S02', 'Publish signal and staking as two columns and never combine them',
     '(a) one blended score, (b) two columns, (c) staking only',
     '(b) — a lucky staking run must not be able to hide a negative signal',
     'HIGH — it is the difference between a scoreboard and a slot machine',
     SUGGESTION_ACCEPTED,
     'a strategy shows staking ROI above zero while its skill interval sits wholly below zero '
     '(this already happens on the 2026 tail)',
     'if the two columns never disagree over 300 settled bets, the split is not doing work',
     'data/leaderboard.csv'),
    ('S03', 'Estimate the availability effect as a coefficient, never apply a fixed penalty',
     '(a) subtract N points per missing starter, (b) estimate the coefficient with a ridge, '
     '(c) ignore availability', '(b) — a fixed penalty is an assumption dressed as a measurement',
     'HIGH — the brief forbids fixed penalties outright', SUGGESTION_ACCEPTED,
     'the estimated coefficient keeps its sign across three rolling origins',
     'if the coefficient flips sign between origins, drop the feature and publish that result',
     'data/availability_coefficients.csv'),
    ('S04', 'Define depth as playing-time share inside a position group',
     '(a) parse 32 club depth pages, (b) usage rank from snap share, (c) both',
     '(b) — measurable, uniform across clubs, and impossible to corrupt with jersey order',
     'MEDIUM — it changes the depth tables and the deficiency view', SUGGESTION_ACCEPTED,
     'a club publishes a structured official depth feed that disagrees with the usage rank for '
     'more than 5% of slots',
     'if such a feed appears, add it as a cross-check and publish the disagreements instead of '
     'replacing the measured rank', 'data/depth_usage_2026.csv'),
    ('S05', 'Treat any closing-line bias as a hypothesis that must be pre-registered',
     '(a) use it now, (b) pre-register a 2026-only test with a frozen threshold, (c) ignore it',
     '(b) — a bias found by looking at the holdout has spent that holdout',
     'HIGH — using a discovered effect as if it were a prediction is the classic error',
     SUGGESTION_DRAFT, 'a frozen threshold committed before the next kickoff',
     'if a prospective sample of at least 100 games shows the bias with the same sign, promote '
     'it to a candidate family', 'data/backtest_families.csv'),
    ('S06', 'Keep the combo gate closed until a joint probability exists',
     '(a) multiply marginal probabilities, (b) block combos, (c) rank them with a warning',
     '(b) — multiplying marginals under dependence is arithmetically wrong, not merely risky',
     'HIGH — it prevents publishing a number that cannot be true', SUGGESTION_ACCEPTED,
     'a fitted joint distribution beats the independent product by more than one percentage '
     'point on held-out games, with n published',
     'if the measured dependence is negligible for a specific leg set, open that set alone',
     'data/correlations.csv'),
    ('S07', 'Publish the weekly residual against the market instead of a pick',
     '(a) publish picks, (b) publish the residual series, (c) both',
     '(b) — a residual accumulates evidence whether or not anyone bets; a pick invites '
     'result-chasing', 'MEDIUM — it changes what the front page shows', SUGGESTION_ACCEPTED,
     'four consecutive weekly residual snapshots with a consistent sign',
     'if the residuals show no persistence over four weeks, stop publishing them weekly',
     'data/origination_week11.csv'),
    ('S08', 'Admit only stamped, hashed availability reads as evidence',
     '(a) trust the tables already in the repository, (b) re-read and hash, (c) both',
     '(b) — the repository already contains one capture that asked for Week 11 and received '
     'Week 10, so provenance has to be re-checked at every build', 'MEDIUM',
     SUGGESTION_ACCEPTED, 'two independent reads of the same page disagree',
     'if two reads a day apart agree on every cell, relax to one read per day',
     'data/availability_week11.csv'),
    ('S09', 'Put a control baseline in every scored table, not only the leaderboard',
     '(a) leaderboard only, (b) every scored table',
     '(b) — a control is the only way a reader can tell whether a number is any good',
     'MEDIUM', SUGGESTION_ACCEPTED, 'every scored table carries a control row',
     'if a control ever outranks the model, the model adds nothing and the table says so',
     'data/backtest_families.csv'),
    ('S10', 'Settle the price-data policy before publishing any backtest figure',
     '(a) backtest first, (b) a written price policy first, (c) no policy',
     '(b) — a backtest against an unnamed price is not reproducible', 'HIGH',
     SUGGESTION_ACCEPTED, 'the policy carries a date and a scope before the first figure',
     'if a named-operator closing series with a verifiable stamp appears, widen the policy to '
     'row-level prices', 'preregistration.json'),
    ('S11', 'Print the number that would clear each gate beside the gate',
     '(a) a status word only, (b) status plus the clearing number',
     '(b) — "blocked" without a number is not a decision aid', 'MEDIUM', SUGGESTION_ACCEPTED,
     'every blocked row carries a number',
     'if a row cannot be given a number, it is a question rather than a requirement',
     'data/requirements.csv'),
    ('S12', 'Make the questions register carry the discovery route, not just the gap',
     '(a) a list of gaps, (b) gap plus route plus blocker',
     '(b) — a gap with no route is a complaint', 'LOW', SUGGESTION_ACCEPTED,
     'every question names a route',
     'if a route proves impossible, demote the question to a rejected item with the reason',
     'data/questions.csv'),
    ('S13', 'Publish two total estimators side by side until one wins out of sample',
     '(a) pick one now, (b) keep both with a gap column',
     '(b) — the gap is the evidence, and choosing now would be choosing before the evidence',
     'MEDIUM', SUGGESTION_DRAFT, 'a frozen comparison plan, then the gap over a full season',
     'if the second estimator never beats the first out of sample, retire it and publish the '
     'result', 'data/backtest_totals.csv'),
    ('S14', 'Show replacement depth as a measured gap, never as a claim about who started',
     '(a) assert that a backup replaced a starter, (b) publish the usage gap',
     '(b) — there is no official inactive list in the repository, so a replacement can be '
     'bounded but not named', 'MEDIUM', SUGGESTION_ACCEPTED,
     'an official inactive list or Game Book is captured',
     'if the inactive list confirms a replacement, publish it as confirmed and keep the '
     'measured gap beside it', 'data/replacement_depth_2026.csv'),
]

QUESTIONS = [
    ('Q01', 'What is the closing price, from a named operator, for each of the 13 Week 11 '
            'markets?',
     'Two named operators are readable and their main lines are captured with read stamps '
     '(DraftKings, FanDuel)',
     'A capture at kickoff minus ten minutes, hashed',
     'A scheduled job at kickoff minus ten minutes, run where the bytes can be hashed',
     'every CLV number, the closing column, and the escrow stage of the leaderboard', 'SHORT',
     'https://sportsbook.draftkings.com/leagues/football/nfl'),
    ('Q02', 'Are official NFL pages usable for automated daily capture?',
     'Readable once per session through the page tool; this session did not read the terms '
     'text, so it asserts no permission either way',
     'A legal read of the terms', 'Read the nfl.com terms section on automated retrieval and '
     'record the decision with its date', 'any multi-day automated availability series',
     'LEGAL', 'https://www.nfl.com/legal/terms'),
    ('Q03', 'Is playing-time share an admissible stand-in for "started"?',
     'Snap counts cover 136 of the 2026 club-games in the repository and the join to '
     'designation rows is published per designation',
     'An official inactive list, or the Game Book, per game',
     'Read one official inactive article per week and publish the join rate against snap share',
     'any claim that a named player replaced a named starter', 'DATA',
     'https://www.nfl.com/injuries/league/2026/reg11'),
    ('Q04', 'Can a public-data model beat the closing line at all?',
     'Not in this corpus: the model scores negative Brier skill against the de-vigged close '
     'and is worse on every holdout season',
     'Either a new feature class or the honest conclusion that it cannot',
     'Test a new feature class only under a new registration, never by re-running this one',
     'the first certified leaderboard row', 'MODEL',
     'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz'),
    ('Q05', 'Why does the market-line benchmark itself sit below the closing line?',
     'The spread-to-probability benchmark scores very close to the moneyline close, with its '
     'interval covering zero, so it is a benchmark rather than a strategy',
     'A named-operator closing spread series with a stamp',
     'Capture both operators at kickoff and recompute the benchmark on the same games',
     'using the benchmark as the ceiling in every skill comparison', 'DATA',
     'https://sportsbook.draftkings.com/leagues/football/nfl'),
    ('Q06', 'What does the official "Questionable" designation actually mean?',
     'Pooled 2023-2026: 61.7% of Questionable rows have a snap record [60.3, 63.0], n=4,970',
     'An official inactive list to separate "dressed" from "played"',
     'Join designations to official inactives for one season and recompute',
     'using the designation as a numeric penalty', 'DATA',
     'https://www.nfl.com/injuries/league/2026/reg11'),
    ('Q07', 'Does the availability term help or hurt?',
     'It hurt on 950 paired chronological-holdout games: squared error is higher with the '
     'term on, and the interval excludes zero',
     'A larger point-in-time-safe designation set than two weeks',
     'Keep capturing weekly stamped reads and refit once ten weeks exist',
     'promoting the availability family to the leaderboard', 'MODEL',
     'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz'),
    ('Q08', 'Which club-week availability facts are verified for 2026?',
     'Week 10 (official read 2026-11-12T16:52:39Z) and Week 11 (official read today)',
     'Every earlier week, which exists only inside the pinned dataset',
     'Rebuild the counts from official reads as weeks accumulate',
     'backtesting the availability feature before Week 10 of 2026', 'DATA',
     'https://www.nfl.com/injuries/league/2026/reg11'),
    ('Q09', 'Is the pinned spread sign convention home-favoured positive?',
     'Yes: the stored line correlates +0.431 with the realised home margin (n=7,087), and the '
     'model fit under that convention has MAE 3.41 against 8.22 for the alternative',
     'Nothing further', 'Already answered by measurement; see data/sign_convention.csv',
     'any use of the pinned spread column', 'ANSWERED',
     'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz'),
    ('Q10', 'How many settled bets are needed before a ranking means anything?',
     'The luck panel computes the count needed to separate 55% and 54% from break-even at 95% '
     'confidence and 80% power',
     'Nothing further for the arithmetic; the sample has to be earned',
     'Report n beside every rank and refuse to rank below 300 settled bets',
     'any claim that one strategy is better than another', 'ANSWERED',
     'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5496353/'),
    ('Q11', 'Do same-game legs move together enough to break a product rule?',
     'Margin and total in the same game correlate 0.020 [-0.031, 0.071] at n=1,495: small, '
     'not zero, and the joint distribution is still unknown',
     'A fitted joint distribution per leg pair',
     'Fit a bivariate model per leg pair from the pinned box scores and publish the gap',
     'any same-game parlay or combo ranking', 'MODEL',
     'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz'),
    ('Q12', 'Which venue is printed for each Week 11 fixture?',
     'One fixture read this session (IND at HOU: HOUSTON, TX / RELIANT STADIUM); the other 12 '
     'are not read here',
     'Twelve game-centre reads', 'Read each game centre and transcribe the two printed fields',
     'a complete venue column', 'SHORT',
     'https://www.nfl.com/games/colts-at-texans-2026-reg-11'),
    ('Q13', 'What happens to a live strategy that starts to fail?',
     'Demotion triggers are frozen in the registration: a 90% lower bound below zero, an ROI '
     'at or below -10% over 50 settled bets, or a changed input hash',
     'A live sample to apply them to', 'Apply the gate mechanically when a sample exists',
     'keeping a failing strategy on the board', 'ANSWERED', 'preregistration.json'),
    ('Q14', 'Is the repository\'s published availability capture what it claims to be?',
     'No, and the file says so itself: the capture stamped 2026-11-18T03:55:13Z records '
     'requested_url .../reg11 but source_url .../reg10, with 347 rows and 28 clubs, so the '
     '"Week 11 prior read" is Week 10 content',
     'A capture that records the page it actually received, not the one it asked for',
     'Assert on the printed heading of the received page; this desk transcribes the heading '
     '"Injuries - WEEK 11" as part of its own read',
     'any delta, trend or reliability number that treats that file as Week 11', 'DATA',
     'https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-desk-6cbf25fa/'
     'injury_reads/capture_injuries_2026-11-18.csv'),
]

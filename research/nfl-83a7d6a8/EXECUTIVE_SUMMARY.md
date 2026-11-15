# Executive summary — NFL market desk (session 83a7d6a8)

**Captured 2026-11-15T23:40:00Z · NFL 2026 season · Week 11 · paper research only · no bet is placed, no stake is live, no reward is issued.**

Site: `nfl-market-desk/index.html` (13 pages). Machine-readable data: `nfl-market-desk/data/*.csv`. Every table row on the site carries a source link, and `verify.py` fails the build if one does not.

---

## 1. The four sentences that matter

1. **We can originate a line and cannot price it.** 39 fair lines on 13 Week 11 games, each published beside the market's line and the difference. The market line is aggregator tier: no book, no jurisdiction, no timestamp. Nothing on this desk can be certified against it.
2. **The model does not beat the market on validation.** Weeks 5–8: model Brier **0.2427** against the market's **0.2192** on 57 games. Weeks 9–10 (final holdout): **0.1524** vs **0.1570** on 24 games. A 24-game holdout is not evidence, and we do not present it as one.
3. **One family clears its own signal test and still cannot be certified.** S5 (Rest edge >= 3 days): hit rate **0.2917** against a price-implied null, n=24, Holm-adjusted p=0.0397. Certification needs a closing price, and this repository contains none.
4. **The best ROI on the board is the one the brief told us never to rank by.** S7 shows **63.33%** ROI on **3** graded bets. It is ranked fifth of five on staking and second of four on signal, and it is not the leader.

## 2. What was built

| Area | Delivered | Where |
|---|---|---|
| Results | 145 official finals, 32/32 clubs reconciled exactly against the league standings on W-L-T, PF and PA | `data/results_feed.csv`, `data/standings_reconciliation.csv` |
| Corpus | 145-game pre-registered corpus (136 inherited + 9 new), chronological, with rest, neutral site, roof and surface beside every row | `data/backtest_corpus.csv` |
| Origination | side → total → moneyline, in that order, each with fair line, market line and difference, and probability + inputs | `data/originated_markets.csv` |
| Price policy | 10 decisions fixed before any return was published | `data/price_policy.csv` |
| Price store | 195 snapshot rows: 78 populated, 117 empty by policy with a flag | `data/price_snapshots.csv` |
| Attendance | 28 clubs, 347 injury rows, 70 Out / 11 Doubtful / 90 Questionable | `data/injuries_wk10.csv` |
| Depth | 551 rows from 11 of 32 clubs, shared and empty slots preserved, 17 divergences against the inherited register | `data/depth_rows.csv`, `data/depth_compare.csv` |
| Replacement depth | 14 named replacements, all 2nd string, 0 compounding | `data/replacement_cascade.csv` |
| Strategies | 9 pre-registered families with published sha256 rule files | `data/strategy_registration.csv`, `data/preregistration/` |
| Gates | 12 gates: 6 MET, 1 PARTIAL, 5 NOT MET | `data/gates.csv` |
| Leaderboard | 7 ranked families, signal and staking kept apart, 3 controls on the same games | `data/leaderboard.csv`, `data/control_summary.csv` |
| Luck | observed hits vs the hits the model's own probabilities predicted | `data/luck_panel.csv` |
| Correlations | 5 official team-level values with n and p; 5 withheld with the reason | `data/correlations_official.csv` |
| Registers | 78 requirements, 34 flags, 15 questions, 19 suggestions, 11 desks catalogued | `data/requirements.csv`, `data/flags.csv`, `data/questions.csv`, `data/suggestions.csv` |

## 3. Requirements: 78 lines, honest statuses

| Status | Rows | Meaning |
|---|---|---|
| MET | 46 | built and verified against a committed file |
| PARTIAL | 21 | built for the subset where the input exists, and labelled |
| NOT MET | 9 | the input does not exist in this repository |
| REJECTED | 2 | refused on principle, with the reason recorded |

Each row's status is machine-checked: `verify.py` resolves the row's evidence path and fails if the file does not exist or has zero rows.

### The nine rows that are not met

| Requirement | Why | Cheapest route |
|---|---|---|
| R-12 Make the injury signal a surprise, never a level | - | A pre-season expectation baseline per player, plus designation reliability (OWN-12). |
| R-25 Use official Game Books for actual starters and game-day status | - | An official game-book source. ESPN's gamebook path is not the NFL's game book and returned no play-by-play from this sandbox. |
| R-29 Capture official inactive lists and snap counts | - | Official inactive lists (published 90 minutes before kickoff) and snap counts. Neither was reachable this session (OWN-11). |
| R-32 Treat roster turnover as a first-class data event | - | A transactions log join. The Eagles waived two players on 2026-11-13 while both are still printed on the chart (OWN-09 note). |
| R-42 Calibrate what Questionable means empirically | - | Several seasons of designations joined to inactive lists (Q-06). One week cannot calibrate a designation. |
| R-51 Score injury-designation reliability before using it as a feature | - | Question Q-06. Not built; the label is not used as a numeric feature anywhere. |
| R-54 Use snap counts as the starter proxy when the depth chart is unavailable | - | Official snap counts (OWN-11). |
| R-64 Archive weekly injury reports for past seasons | - | An archive source. Nothing reachable from this sandbox serves historical weekly reports. |
| R-66 2026 kickoff and declared onside-kick regime priors filter | - | The 2026 rule text from the league's own rulebook; not read this session. |

## 4. Gates: what stands between paper and live

| Gate | Name | Status | Test |
|---|---|---|---|
| G0 | Source integrity | MET | Every input row carries a URL, a tier and a capture time; the results feed reconciles 32/32 against the official standings |
| G1 | Pre-registration | MET | The family's rule file exists, its sha256 matches the ledger, and its registration predates the first graded bet |
| G2 | Verified price | NOT MET | Opening and closing prices from an official or named-operator source exist for the market |
| G3 | No lookahead | MET | Every forecast is produced from games strictly before its own week, and the forecast file records train_last_week |
| G4 | Sample adequacy | NOT MET | Prospective graded bets >= 300 per family (the power note fixes that number before results); n is published |
| G5 | Multiplicity | MET | Holm adjustment across all registered families, with the family count published |
| G6 | Calibration | NOT MET | Market-relative skill is positive with a cluster-bootstrap lower bound above zero |
| G7 | Joint probability | NOT MET | A parlay or prop combo is ranked only where a directly validated joint probability and the operator's void/push rules are both present |
| G8 | Availability evidence | PARTIAL | Personnel enters only from official, timestamped observations; ablations replace fixed penalties |
| G9 | Demotion | MET | A live strategy has a written trigger that returns it to paper |
| G10 | Control baselines | MET | Every leaderboard run carries random-pick and favourites-only controls graded the same way |
| G11 | Persistence outside the design | NOT MET | The edge is re-measured on a season not used to design the rule |

**MET:** G0, G1, G3, G5, G9, G10.

**NOT MET:** G2, G4, G6, G7, G11.

## 5. Leaderboard, with the numbers the ranking is not allowed to use

| Family | Rule | Registry | n | Signal | p (Holm) | Rank | ROI | Staking rank |
|---|---|---|---|---|---|---|---|---|
| S5 | Rest edge >= 3 days | hit rate vs price-implied null | 24 | 0.2917 | 0.0397 | 1 | no price | - |
| S7 | Fade large home favourite >= 10 points | hit rate vs price-implied null | 3 | 0.1468 | 1.0000 | 2 | 63.33% | 1 |
| S6 | Divisional home underdog | hit rate vs price-implied null | 18 | -0.2251 | 0.3273 | 3 | -28.72% | 4 |
| S4 | Home underdog >= 2.5 points | hit rate vs price-implied null | 40 | -0.3462 | 0.0001 | 4 | -46.95% | 5 |
| S3 | Moneyline value >= 5 probability points | proper score (Brier) | 69 | 0.1541 | 0.2972 | 1 | 7.71% | 3 |
| S2 | Model total edge >= 3.0 points | proper score (Brier) | 44 | -0.0072 | 1.0000 | 2 | no price | - |
| S1 | Model side edge >= 3.0 points | proper score (Brier) | 41 | -0.1608 | 1.0000 | 3 | 28.49% | 2 |

Controls, on the same games: random home side Brier 0.2500 (hit 0.4444), favourites-only 0.2500 (hit 0.2763), coin flip 0.2500.

Luck, removed: the model picked 53 of 81 games right, while its own probabilities predicted 56.27. It was **below** its own expectation, and that comparison — not the hit rate — is the one that decides whether anything here is skill.

## 6. What is blocked, and by what

| Flag | Finding | Blocks |
|---|---|---|
| INH-F-01 | nfl.com publishes no spreads, totals or moneylines | Price data |
| INH-F-04 | The Week 11 official injury report is not published yet | Injuries |
| INH-F-08 | No player-prop lines exist from any source in this repo | Player props |
| INH-F-10 | The certification universe is far smaller than gate G1 requires | Sample size |
| OWN-01 | No official or operator price exists anywhere in reach | price |
| OWN-04 | Houston publishes its depth chart as an image | depth |
| OWN-07 | The Week 11 injury report URL still serves Week 10 - reconfirmed | injury |
| OWN-11 | No inactive list and no snap counts are captured | injury |
| OWN-17 | No player-prop price exists, so prop combinations cannot be graded | model |

34 flags in total, all namespaced so the inherited register (INH-) and this desk (OWN-) can never be confused again. The inherited PR #79 register used the same identifiers for entirely different findings.

## 7. What we refused to do

- **Rank by season ROI.** The board shows why: the top-ROI family has 3 priced bets.
- **Derive depth from jersey number, experience or salary.** Jersey numbers are parsed and stored, and used for nothing.
- **Multiply marginal probabilities to price a parlay.** Gate G7 blocks both combo families until a joint probability is measured.
- **Fill a blank with an estimate.** 117 of the 195 price snapshots are empty by policy, the roof and surface of 8 games are blank because the mirror is blank, and the market-implied margin standard deviation is blank because the honest arithmetic says it cannot be recovered from one line.

## 8. Where the value actually is

Three things on this desk are worth acting on, and none of them is a bet:

1. **The results feed and its reconciliation.** 145 finals, 32/32 exact on W-L-T, PF and PA. That is the foundation every later claim stands on, and it is now reusable.
2. **The depth divergence.** 17 rows where a club's own live chart and the register inherited from PR #79 disagree — including two players the Eagles waived on 13 November who are still printed on the chart. That is a measurable data-integrity problem, and it is the cheapest improvement available (suggestion SG-03).
3. **The honest negative on the personnel coefficient.** −1.892 points per extra unavailable player, standard error 2.260, n=9. The temptation is to adopt the point estimate; the interval spans zero, so the desk publishes the ablation and refuses the penalty.

## 9. What the next session should do first

1. **Get a price.** Nothing else on this desk can be certified without it (SG-01, Q-01).
2. **Schedule a second capture** so the store has a delta rather than a point (SG-13, Q-15).
3. **Capture inactive lists and snap counts** so depth becomes playing time rather than published order (SG-05, Q-04).
4. **Widen depth coverage from 11 to 32 clubs** — 20 remain (SG-03).
5. **Consolidate the eleven desks** into one register so an outside reader can cite this repository at all (SG-02, Q-11).

## 10. Reading order

- `nfl-market-desk/index.html` — the desk on one page, blockers first
- `nfl-market-desk/readiness.html` — 78 requirements with the number that clears each
- `nfl-market-desk/leaderboard.html` — the two rankings, the controls and the luck panel
- `nfl-market-desk/availability.html` — injuries, replacements and the depth of each
- `nfl-market-desk/prices.html` — the store, its 117 policy blanks, and the results feed
- `nfl-market-desk/review.html` — every flag with its source


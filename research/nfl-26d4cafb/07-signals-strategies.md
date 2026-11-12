# Signals, Strategies and Leaderboard

**Session `26d4cafb` - snapshot 2026-11-12 UTC - NFL 2026 Week 10**

> Generated directly from `nfl-desk-26d4cafb/data/` by `engine.py`. Every row links to the official source it was read from. Values that could not be confirmed from an official source are left blank and listed on the Flagged for Review page.

## Signals

| # | Category | Signal | Definition | Source | Cadence | Verified | Limitation |
|---|---|---|---|---|---|---|---|
| SIG-01 | Injuries | Official practice-report DNP count delta | Count of players listed Did Not Participate on the official weekly injury report; net of the opponent's count. | nfl.com/injuries/league/2026/reg10 | Wed-Sat | verified | Wednesday report only; Friday/Saturday final statuses not yet issued for Sunday/Monday games (FLG-03). |
| SIG-02 | Injuries | Confirmed Out / IR starter indicator | Binary flag per position group where the 1st-string player is officially on Injured Reserve or ruled Out. | nfl.com news + official IR transactions | daily | verified | IR does not appear in the active weekly injury table (FLG-06). |
| SIG-03 | Depth | Active backup string tier (2nd/3rd/4th) | The highest healthy string available at an affected position, read from the official club depth chart. | Official club /team/depth-chart pages | weekly | verified | Club charts are unofficial, sometimes raster-only, sometimes lagging (FLG-05, FLG-09, FLG-10, FLG-11). |
| SIG-04 | Depth | Offensive-line continuity count | Number of the five offensive-line positions whose 1st-string player is Out/IR/DNP. | nfl.com/injuries/league/2026/reg10 + club depth charts | weekly | verified | Same as SIG-03. |
| SIG-05 | Depth | Defensive front-seven depletion | Model-prior points conceded from EDGE/DT/LB starters Out/IR/DNP. | nfl.com/injuries/league/2026/reg10 | weekly | verified | Magnitude is a bounded model prior, not an official stat (FLG-04). |
| SIG-06 | Depth | Secondary depletion | Model-prior points conceded from CB/S starters Out/IR/DNP. | nfl.com/injuries/league/2026/reg10 | weekly | verified | Magnitude is a bounded model prior, not an official stat (FLG-04). |
| SIG-07 | Ratings | Shrunk offensive points-per-game delta | Team points per game minus league mean, shrunk toward zero with k pseudo-games. | Official 136-game ledger | weekly | verified | Small 2026 sample requires heavy shrinkage. |
| SIG-08 | Ratings | Shrunk defensive points-allowed delta | Team points allowed per game minus league mean, shrunk toward zero with k pseudo-games. | Official 136-game ledger | weekly | verified | Opponent-strength adjustment is first-order only. |
| SIG-09 | Ratings | Point-differential (net-points) rating | (PF - PA) / games, shrunk; the single strongest official-derived team-strength measure. | Official 136-game ledger | weekly | verified | Ignores schedule strength beyond one iteration. |
| SIG-10 | Context | Empirical non-neutral home-field advantage | Mean home margin computed on official non-neutral-site games only. | Official 136-game ledger | weekly | verified | Neutral-site set depends on Q-04 confirmation. |
| SIG-11 | Context | Rest-days differential | Home rest days minus away rest days, from the official schedule. | nfl.com/schedules | weekly | verified | Bye-week and Thursday effects are confounded with team quality. |
| SIG-12 | Context | Neutral-site indicator | Binary flag zeroing HFA for confirmed international neutral-site games. | nfl.com/schedules | weekly | verified | Two 2026 games have an unconfirmed venue (Q-04). |
| SIG-13 | Props | QB passing-yards game-log central tendency | Shrunk mean and standard deviation of the QB's official 2026 game-by-game passing yards. | nfl.com/players/<slug>/stats/logs/2026/ | weekly | verified | No official prop lines exist to compare against (FLG-01). |
| SIG-14 | Props | Same-game QB-to-target correlation | Pearson r between the QB's passing yards and the primary target's receiving yards in the same game. | nfl.com/players/<slug>/stats/logs/2026/ | weekly | verified | Sample is 6 teams / 50 team-games (Q-10). |

## Strategies

| # | Strategy | Type | Market | Rule | Signals | Status | Graded | Win rate | Gates | Reward |
|---|---|---|---|---|---|---|---|---|---|---|
| STR-01 | Net-points rating + empirical HFA | single | spread | Bet the side whose walk-forward shrunk net-points rating plus the empirical HFA implies a margin differing from the originator's own fair spread by more than the gate threshold. | SIG-09, SIG-10, SIG-12 | backtested walk-forward | 35 | 0.7429 | &mdash; | &mdash; |
| STR-02 | Depth-adjusted injury fade | single | spread | Fade any team whose confirmed Out/IR model prior exceeds the opponent's by the gate threshold, using the active backup string to size the prior. | SIG-02, SIG-03, SIG-04, SIG-05, SIG-06 | prospective (Week 10 onward) | 0 | &mdash; | &mdash; | &mdash; |
| STR-03 | Offensive-line continuity fade | single | spread | Fade teams with 2+ offensive-line 1st-string players Out/IR/DNP. | SIG-04, SIG-03 | prospective (Week 10 onward) | 0 | &mdash; | &mdash; | &mdash; |
| STR-04 | Rest-differential play | single | spread | Back the team with the rest-days advantage when the differential meets the gate threshold. | SIG-11 | backtested walk-forward | 26 | 0.8077 | &mdash; | &mdash; |
| STR-05 | Divisional-underdog contrarian | single | spread | Back divisional underdogs, where favourite bias is documented and games are historically tighter. | SIG-09, SIG-10 | backtested walk-forward | 36 | 0.3333 | &mdash; | &mdash; |
| STR-06 | Totals: depth-driven scoring-environment | single | total | Play the total when the combined offensive rating delta and the defensive depletion prior move the originator's total past the gate threshold. | SIG-07, SIG-08, SIG-05, SIG-06 | prospective (Week 10 onward) | 0 | &mdash; | &mdash; | &mdash; |
| STR-07 | Two-leg low-correlation parlay | parlay | spread | Pair two single-bet signals whose measured Pearson r is below the correlation cap, else reject the parlay. | STR-01, STR-04, SIG-10 | backtested walk-forward | 16 | 0.5 | &mdash; | &mdash; |
| STR-08 | Same-game QB + target prop combo | player-prop combo | player props | Combine a QB passing-yards over with his primary target's receiving-yards over only when the measured same-game r is positive and the joint probability clears the gate. | SIG-13, SIG-14 | measured (no official lines to bet; FLG-01) | 0 | &mdash; | &mdash; | &mdash; |
| STR-09 | Negative-correlation hedge combo | player-prop combo | player props | Combine a QB passing-yards over with the lead RB's rushing-yards over when the measured r is negative, using the Frechet lower bound for the joint probability. | SIG-13, SIG-14 | measured (no official lines to bet; FLG-01) | 0 | &mdash; | &mdash; | &mdash; |
| STR-10 | Composite gated ensemble | single | spread | Take only the bets on which every individually gated single-bet strategy agrees, i.e. the intersection of STR-01, STR-02 and STR-04. | SIG-02, SIG-09, SIG-10, SIG-11 | prospective (Week 10 onward) | 8 | 1.0 | &mdash; | &mdash; |

## Leaderboard

| Rank | # | Strategy | Graded | Win rate | ROI/unit | DSR | Max DD | Gates | Reward |
|---|---|---|---|---|---|---|---|---|---|
| 2 | STR-01 | Net-points rating + empirical HFA | 35 | 0.7429 | 0.4182 | 0.9138 | 2.091 | ALL 10 PASS | TIER 1 - featured placement + largest research allocation |
| &mdash; | STR-02 | Depth-adjusted injury fade | 0 | &mdash; | &mdash; | &mdash; | &mdash; | NOT RANKED | NO REWARD (failed >=1 validation gate) |
| &mdash; | STR-03 | Offensive-line continuity fade | 0 | &mdash; | &mdash; | &mdash; | &mdash; | NOT RANKED | NO REWARD (failed >=1 validation gate) |
| 1 | STR-04 | Rest-differential play | 26 | 0.8077 | 0.542 | 0.9478 | 1.091 | ALL 10 PASS | TIER 1 - featured placement + largest research allocation |
| &mdash; | STR-05 | Divisional-underdog contrarian | 36 | 0.3333 | -0.3636 | 0.0004 | 13.091 | BLOCKED | NO REWARD (failed >=1 validation gate) |
| &mdash; | STR-06 | Totals: depth-driven scoring-environment | 0 | &mdash; | &mdash; | &mdash; | &mdash; | NOT RANKED | NO REWARD (failed >=1 validation gate) |
| &mdash; | STR-07 | Two-leg low-correlation parlay | 16 | 0.5 | 0.8223 | 0.7023 | 3.0 | BLOCKED | NO REWARD (failed >=1 validation gate) |
| &mdash; | STR-08 | Same-game QB + target prop combo | 0 | &mdash; | &mdash; | &mdash; | &mdash; | NOT RANKED | NO REWARD (failed >=1 validation gate) |
| &mdash; | STR-09 | Negative-correlation hedge combo | 0 | &mdash; | &mdash; | &mdash; | &mdash; | NOT RANKED | NO REWARD (failed >=1 validation gate) |
| &mdash; | STR-10 | Composite gated ensemble | 8 | 1.0 | 0.9091 | &mdash; | 0.0 | BLOCKED | NO REWARD (failed >=1 validation gate) |

## Validation gates

| # | G-03 sample | G-04 break-even | G-05 binomial | G-06 Holm | G-07 DSR | G-08 Brier | G-09 correlation | G-10 drawdown | Overall |
|---|---|---|---|---|---|---|---|---|---|
| STR-01 | PASS (n=35) | PASS (0.7429 > 0.5238) | PASS (p=0.0064) | PASS (holm p=0.0257) | PASS (DSR=0.9138) | PASS (Brier 0.2061 < null reference 0.2539) | N/A (single bet) | PASS (2.09 u) | PASS (all gates) |
| STR-02 | FAIL (n=0) | NOT EVALUABLE (no official price/input) | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT RANKED (insufficient official history) |
| STR-03 | FAIL (n=0) | NOT EVALUABLE (no official price/input) | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT RANKED (insufficient official history) |
| STR-04 | PASS (n=26) | PASS (0.8077 > 0.5238) | PASS (p=0.0014) | PASS (holm p=0.0069) | PASS (DSR=0.9478) | PASS (Brier 0.2074 < null reference 0.2563) | N/A (single bet) | PASS (1.09 u) | PASS (all gates) |
| STR-05 | PASS (n=36) | FAIL (0.3333 <= 0.5238) | PASS (p=0.0437) | PASS (holm p=0.0437) | PASS (DSR=0.0004) | PASS (Brier 0.2500 < null reference 0.2609) | N/A (single bet) | FAIL (13.09 u > 10.0 u budget) | BLOCKED (2 gate(s) failed) |
| STR-06 | FAIL (n=0) | NOT EVALUABLE (no official price/input) | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT RANKED (insufficient official history) |
| STR-07 | FAIL (n=16 < 20) | PASS (0.5000 > 0.2744) | &mdash; | &mdash; | PASS (DSR=0.7023) | NOT EVALUABLE | PASS (\|phi\|=0.333 < 0.60; joint within Frechet [0.500, 0.750]) | PASS (3.00 u) | BLOCKED (1 gate(s) failed) |
| STR-08 | FAIL (n=0) | NOT EVALUABLE (no official price/input) | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT RANKED (insufficient official history) |
| STR-09 | FAIL (n=0) | NOT EVALUABLE (no official price/input) | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT EVALUABLE | NOT RANKED (insufficient official history) |
| STR-10 | FAIL (n=8 < 20) | PASS (1.0000 > 0.5238) | PASS (p=0.0077) | PASS (holm p=0.0257) | FAIL (DSR=) | PASS (Brier 0.0443 < null reference 0.2506) | N/A (single bet) | PASS (0.00 u) | BLOCKED (2 gate(s) failed) |

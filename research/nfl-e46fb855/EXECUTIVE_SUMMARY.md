# Executive summary — NFL decision-readiness desk (session `e46fb855`)

Built 2026-11-15 from six official captures. Site:
<https://sassnarep3-star.github.io/Own5/nfl-desk-e46fb855/>

## 1. What this desk is

A decision-readiness desk, not a tipping service. Every requirement line in the
brief is published as a row with three things beside it: this desk's status, the
gate that blocks it, and **the number that would clear it**. Nothing is
certified, nothing is staked, and no performance claim is made.

## 2. What was verified this session

| Check | Result |
|---|---|
| Official 2026 finals in the results feed | 145 |
| Completed games in the pre-registered backtest corpus (weeks 1–9) | 136 |
| Feed rows re-read from the official week pages and matching | 59 of 59 |
| Clubs whose game-by-game record reconciles to the official standings | 32 of 32 |
| Clubs with a parsed official depth chart | 31 of 32 (Houston publishes an image) |
| Published depth slots transcribed | 700 |
| Rows in the week-10 injury report | 326 |
| Injury rows re-read and compared with the earlier read | 49, of which 4 had changed |
| Line-by-line audit checks against official sources | 154 |
| Offence-vs-defence pairings in the week-11 deficiency matrix | 563 |
| Week-11 markets originated (side, total, moneyline) | 39 |
| Price-snapshot rows this desk needs / can fill | 52 / 13 (all model output, none market) |

## 3. The three findings that matter

1. **No official or licensed market price exists anywhere in this repository, so
   nothing can be graded.** nfl.com publishes no spreads, totals or moneylines,
   and no operator price has ever been read in; a parallel desk
   (`nfl-market-desk`, session `83a7d6a8`) searched the same pages and recorded
   the same finding in its own price policy P-01. The only price-like rows
   anywhere in the repo are aggregator (nflverse) reference lines of unknown
   timestamp, which cannot serve as an opening or a closing number. ROI, closing
   line value and the residual against the market are undefined; the staking
   board is empty by design and no strategy can be certified. This is flag F-01,
   and it is a decision (S-01), not a defect to be worked around.
2. **Home-field advantage is not established in this sample.** The model fits it
   at -0.12 points per game, 95% interval
   [-2.14, 1.90] on 145 official games. The
   interval contains zero.
3. **Neither totals estimator beats the naive baseline — and the first run that
   said otherwise was wrong.** Fitted on prior weeks only, estimator A
   (shrunk team game totals) has a walk-forward mean absolute error of
   11.61 and estimator B (points-for/points-against blend)
   11.89, against a league-average baseline of
   11.18. An earlier run of this build appeared to show estimator B
   winning by about a point; that was leakage, because it was fitted on the
   full-season standings, which contain the game being predicted (flag F-18).
   Both estimators stay published side by side with the gap column, as the brief
   asks, and neither is collapsed until the pre-registered comparison fires.

## 4. Where the brief's requirements stand

72 requirement lines: **32 met, 14 partial, 26 blocked**. The blocked ones are
blocked by data that does not exist yet, not by work not done — six blocking
gaps (F-01 to F-06) plus the single-season problem (F-12) account for all of
them, and each carries the number that would clear it.

## 5. What a reviewer has to decide

The questions register states what we have, what is missing, whether it blocks a
decision, and the cheapest way to discover it
(<https://sassnarep3-star.github.io/Own5/nfl-desk-e46fb855/questions.html>).
The suggestions register sets out the paths — options, recommendation, what
would change the call, decision status
(<https://sassnarep3-star.github.io/Own5/nfl-desk-e46fb855/suggestions.html>).
Fourteen suggestions are published; **none has been implemented** and each sits
at AWAITING DECISION, IMPLEMENTED-AS-A-RULE, DEFERRED or REJECTED.

The single decision that unblocks the most: **S-01, where market prices come
from.** Until it is answered, gates G2, G3 and G4 cannot pass for any strategy.

## 6. Cross-desk notes

Three decision-readiness desks were built on this branch on the same day
(`nfl-560ed315`, `nfl-readiness-cba42531` and this one) and they count the
brief's requirement lines as 81, 85 and 72 respectively. The brief is being split
into lines three different ways; none of the three is wrong, but a reviewer
cannot reconcile them. Logged as flag F-19, with consolidation proposed as
suggestion S-12. No file belonging to another session was changed.

7. Honesty rules this desk is held to

* Every body row on every page ends in a source cell: a link to the official
  page the value was read from, or an explicit UNVERIFIED badge.
* A value that cannot be confirmed from an official source is blank and flagged;
  it is never inferred, averaged or carried over from a third party.
* Correlations are computed only from official inputs, with n and a 95%
  interval published. Aggregator-derived values (nflverse) exist elsewhere in
  this repository and are listed on a withheld table, not reused as values.
* Every measurement says whether it is in or out of sample. One family (F6) is
  published as an explicitly in-sample diagnostic and is excluded from
  promotion.
* The whole desk rebuilds deterministically from pinned captures; a silent drift
  fails the workflow.

# Refusals — what this desk will not say, and the missing input behind it

A gap in this build is a **result**: it is published with a reason and a route to an
answer, because a reader who can see what is unverified can discount it correctly, and a
reader who cannot will be confidently wrong. Each entry names the thing that would have
to exist for the claim to be made.

## 1. No closing-line-value claim

**Refused:** "our lines beat the market's closing number."

`data/price_snapshots.csv` holds 148 rows and **zero** of them are closing quotes: no
source in this repository carried a timestamped final line for a 2026 game. The
historical window's prices come from an aggregator mirror with an *undocumented line
vintage*, which is adequate for testing whether a model tracks the market and not
adequate for calling any row a close. V-08 is therefore FAIL, CLV earns nobody points,
and `data/market_gaps.csv` carries 42 closing cells as `ABSENT FROM SOURCE`.

*Would need:* the `capture_job.py` schedule to run for two weeks before a game's kickoff
and once inside ten minutes of it, archiving the payload digest — which is now wired into
CI, and turns this from a permanent refusal into a calendar problem.

## 2. No opening moneyline

**Refused:** inventing an opening moneyline from the opening spread.

The source page publishes an opening *spread* and an opening *total* only, with a split
"Open" cell (open spread on the favourite's row, `o/u` on the other) — a layout that is
easy to mis-parse and impossible to fill by arithmetic. `line_sheet.csv` leaves the
opening-moneyline column blank; MK-Q-01 asks the operator page's owner which field is
authoritative. An opening ML derived from the spread would be a modelled number wearing a
"market" column header.

## 3. No QB ↔ top-WR correlation from a third party's figure

**Refused:** publishing r = 0.76 for the quarterback-and-WR1 pair.

The only version of that number in this repository is another session's third-party
aggregate, not a value recomputed from official play-by-play. `data/correlations.csv`
prints the row with a **blank r**, `tier = NOT COMPUTED`, and the reason. The desk's own
officially sourced correlations are in the same table, each with `n` and a Fisher-z
interval, so the refusal sits beside what could be computed rather than hiding in a
footnote (MK-F-09).

*Would need:* per-game official passing and receiving statistics for the same player
weeks, joined on an exact name key. `data/decision-desk/raw/stats_player_week_*.csv.gz`
gets close but its snap columns measure participation, not targets.

## 4. No prop-combo grading, so no prop division

**Refused:** scoring the two captured prop markets as bets.

Grading "Christian McCaffrey 38+ rushing attempts" needs the official per-player game
stat, and no pinned source here publishes it. The prop rows are therefore kept as
observations in the store with **no bet attached**, the prop-combos division reads
`BLOCKED` with that sentence as its reason, and MK-Q-05 asks which feed is authoritative
for prop grading. A desk that grades a prop against the wrong stat sheet will produce a
long, confident, wrong ledger.

## 5. No individualised injury prediction from a status label

**Refused:** turning `Questionable` into "58.6% likely to play this specific player."

58.6% is a base rate over 590 player-weeks with a Wilson interval of 54.63–62.55%,
pooled across statuses, positions and contexts. Applying it to one named player is a
different claim, needing a model conditioned on position, snap history and opponent, and
this desk does not have one that it would defend in front of a bettor. It publishes the
base rate, the `Out`-played-zero-times result, and per-player **measured** snap shares
instead of a prediction.

## 6. No relaxation of a failed name join

**Refused:** loosening the name key until the join succeeds.

A surname-plus-initial join invented appearances: it produced "Out, played 7 of 588",
which is the kind of number that would have quietly justified an availability model. The
exact normalised full-name join gives 0 of 588. So the join stays strict, and every
rejected match is counted and published per status: `join_rejected_unique_candidate`
(7 for Questionable, 7 for Out, 0 for Doubtful) and `join_rejected_ambiguous` (0 in all
three — this season's report and snap records contain no surname-plus-initial collisions
inside the joined weeks). A rejected candidate is a row that *looked* joinable and was
not, which is exactly the population a fuzzy rule would silently convert into a false
appearance. Ambiguity is held in a module-level lookup, never smuggled into the join key.

## 7. No clamping of an "impossible" percentage, and no blended denominator

**Refused:** capping the removed-snap percentages at 100%.

`data/availability_impact.csv` reports offensive and defensive snaps removed against
**each side's own** base, and 10 of 25 club-week rows still exceed 100% on offence (max
**256.5%**) with 6 over on defence (max **328.0%**). That is not a bug: several full-time
players at one position can all be out at once, and a snap is not a slot — the column
measures volume removed, not a share of a budget. Clamping the display to 100 would
delete the structural fact (a genuinely thinned unit) and leave a number that merely
looks legal.

What *was* wrong, and is now fixed instead of defended: an earlier version divided a
blend of offensive and defensive snaps by the **offensive** base alone, which inflated
every defence-heavy club (Arizona printed 200.0, Dallas 421.0). Per-side bases were
introduced rather than a cap, which is the difference between fixing a denominator and
hiding a symptom. The table now publishes `offence_snap_base` and `defence_snap_base`
next to the percentages so the division can be redone by hand, and
`players_unmatched` counts everyone on the report who is absent from the snap records —
they contribute zero, never an estimate.

## 8. No silent refresh of a stale pin

**Refused:** re-downloading three upstream files mid-analysis because their digests
changed.

`games`, `injuries_2026` and `snap_counts_2026` were republished upstream after this
desk's 2026-11-12T16:52:39Z pin. Swapping them would invalidate every consistency check
that had just passed against the old bytes, so the pin holds, the divergence is
compared-and-logged, and MK-F-01 says which three files drifted and when. The reader can
see the desk is running on a stale-but-known snapshot; that is better than a
fresh-but-unverified one presented as if nothing happened.

## 9. No promoted strategy, and no demotion theatre

**Refused:** calling anything "validated", and calling the demotion gate "passed."

Six of eleven gates pass; the failures are V-05 (Holm-adjusted p = 1.0000 — nothing
survives twelve variants), V-06 (the model forecasts worse than the posted line), V-08
(no closing data) and V-11 (promotion authority, which this desk does not have). The
demotion gate reports **`STAYS ON PAPER`** for all twelve strategies, and because
`data/live_bets.csv` ships empty, its own output says `rules_unevaluable: D3` and is
labelled *armed, not passed*. A gate that "passed" against an empty ledger would be a
gate that passes on nothing, and `verify.py` fails if any process writes rows into that
file.

## 10. No tooling changes made from the desk's own suggestions

**Refused:** implementing a suggestion because the desk wrote it.

`data/suggestions.csv` carries 10 entries, every one `PROPOSED`, each with its options,
its cost, what would change, and a recommendation. Nothing in this build was implemented
from its own suggestion row — including the six that would have made the desk look better
(ticks column, twice-daily capture, per-season backtest rows). `verify.py` asserts the
state column is still all-`PROPOSED`, so the promise cannot rot silently. A reviewer
picks a path; then the code changes.

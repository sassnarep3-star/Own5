# Methodology

Every number on the desk is produced by a script in `nfl-engine-39086ec8/` and reproduced by
`build_data.py` → `build_site.py` → `verify.py`. Nothing is typed into a page by hand; the HTML
is generated from the CSVs, so a page cannot drift from its data.

## Source policy

1. **Official first.** League and club domains for schedule, standings, injuries, depth charts.
   Operator domains for prices. Nothing else is allowed to be a *source of a number*.
2. **A blank is a result.** If the source does not publish it, the cell is blank and the item
   appears on the Flagged for Review page. A missing value is never interpolated, back-filled
   from a later capture, or inferred from a related field.
3. **Provenance is a column, not a footnote.** Every price row carries `source_url`,
   `source_operator`, `source_region`, `captured_at_utc`, `raw_sha256`, `archive_path`.
   The raw block is archived verbatim so a reader can recompute the hash and re-read the page
   text the number came from.
4. **Declared ≠ sourced.** Numbers chosen to make a test run (fixed lines of −3 and 45.5, depth
   weights, staking percentage) are rendered with a `declared definition` chip carrying their
   basis, never with a source link. The verifier rejects a table row that has neither.

## Price store

Append-only, one row per (game, market, event, capture). Re-inserting the same key with a
different value raises `SnapshotConflict` instead of overwriting; the conflict is recorded, not
resolved. A row fails validation without a full UTC timestamp — `DATE_ONLY` is rejected, which is
what caught the prior desks' quote files.

`event` is `open` or `close`. Week 10 has **zero** `open` rows. The store says so in `summary.json`
and on the price page rather than labelling its single capture as both ends of a movement.

## Results and settlement

Settlement uses final scores only, from the 137-game feed. Reconciliation sums PF/PA/W/L/T per club
and compares to the league standings for all 32 clubs at each of 6 statistical slots = 192 checks.
A mismatch is a hard build failure. There is no tolerance band and no manual override list.

Spread settlement is `push` when the margin lands exactly on the line, and pushes are excluded from
both the win and the loss counts rather than counted as half-wins.

## Origination

Three stages, in the required order: **side**, **total**, **moneyline**.

- Stage 1 fits a ridge regression (λ = 5.0, standardised design, no numpy) on the 137-game feed and
  produces an expected home margin and a fair spread.
- Stage 2 fits league scoring rates to an expected total.
- Stage 3 reads stage 1's margin distribution and returns P(home), P(tie), P(away) and a fair
  moneyline.

Stage isolation is enforced in code: stage 2 may not read a market price and stage 3 may not read
stage 2's output for the side. A regression test asserts each prohibition.

Fair, market and difference are three separate columns. When the market is absent the market column
is blank and the difference column is the string `UNPRICED` — never `0`, which would silently read
as "no disagreement".

## Signal vs staking

Two scoreboards over the same bets.

- **Signal**: hit rate against the break-even required by the price, tested with a Wilson lower
  bound and a z against the break-even, never against 50%.
- **Staking**: bankroll multiple and max drawdown under a declared 1%-of-bankroll flat stake.

The two are never combined into one ranking. An entry whose bets fall inside the window used to fit
or select it is tagged `NOT_ELIGIBLE_IN_SAMPLE` and cannot receive a pass verdict regardless of its
signal z — this is applied by rule, not by judgement.

## Depth of replacement

For each published chart slot: which rung the listed starter sits on, how many rungs to the next
deeper body, whether the chain cascades, and whether the slot is exhausted (nobody behind). Slots
are weighted by position importance, and the weight set is **declared**, not derived from data.

Where a club does not publish a chart, the slot list is empty. It is not filled from a beat writer,
a depth chart aggregator, or a previous season.

## Correlations

A correlation is published only with: the source of both series, `n`, a Fisher-z 95% interval, and
a p-value. Values inherited from earlier desks are **recomputed from the inputs those desks
declared**; a value that does not reproduce is flagged (C2, C3) rather than removed, because a
silent deletion hides the problem.

Sensitivity is mandatory for any correlation involving rest: bye weeks are scheduled, not random,
so a rest coefficient is recomputed with byes excluded before it is called a signal.

## Luck removal

No strategy is ranked on raw ROI. Every ranking carries n, the break-even rate implied by the
price, a Wilson interval, and — where multiple strategies are compared — Holm correction and a
deflated Sharpe ratio against the number of variants actually tested. Where that count is unknown
(Q06), the correction cannot be applied and the result is reported as exploratory.

## Demotion

Five rules, each with a machine-readable threshold, each demonstrated firing on a scenario:

| ID | Fires when |
|---|---|
| D1 | sample below the minimum and no reason to stop |
| D2 | closing-line value turns negative over the recent window |
| D3 | drawdown exceeds the declared tolerance |
| D4 | no verifiable price exists for the strategy's market |
| D5 | a data-integrity check fails |

## Reproducibility

Python 3.11, standard library only, no numpy, no network at build time, no randomness anywhere.
`build_data.py` and `build_site.py` are deterministic: `verify.py` rebuilds both and fails if any
file changes. `verify.py` itself runs 1,215 checks — links, row-level sourcing, snapshot hashes,
reconciliation, structural rules — and returns non-zero on the first category that fails.

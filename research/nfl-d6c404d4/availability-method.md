# Availability and depth — method, and what the data actually supports

**Desk:** NFL verified line desk · session `d6c404d4` · built 2026-11-19T07:05Z

## The rule that governs this page

An injury designation is a **label printed by the club**, not a probability and not a number of points.
This desk never converts a designation into a points penalty. It measures what each label has historically
been worth, publishes the interval, and leaves the model without a personnel term until a point-in-time
join is complete enough to survive walk-forward testing.

## What "Questionable" is worth

Measured across four seasons of official designations joined to recorded playing time:

| Designation as printed | Report rows | Joined to playing time | Played share | 95% interval |
|---|---|---|---|---|
| Questionable | 4,970 | 2,982 (60.0%) | **0.2501** | 0.2383 – 0.2623 |
| Out | 4,087 | 1 | 0.0000 | — |
| Doubtful | 499 | 3 | 0.0020 | — |

"Played" means an offensive snap share above 5% in that club-week. The denominator is the number of report
rows, so a **missing join is not counted as "did not play"** — the published rate is conservative. The same
caveat explains the near-zero Out join: a player ruled out records no snaps, so there is nothing to join.

## Depth is a distribution, not a depth chart

Usage rank is assigned by **recorded offensive snap share within a position group, per club-week**. Nothing
else enters. Jersey number, salary, contract and experience are not used, and are not available to the
pipeline.

| Position | Rank | Club-weeks | Mean share | p10 | p90 | Share of weeks under 50% |
|---|---|---|---|---|---|---|
| QB | 1 | — | 0.955 | 0.857 | 1.000 | 1.6% |
| QB | 2 | — | 0.134 | 0.017 | 0.333 | 100% |
| WR | 1 | — | 0.837 | 0.679 | 0.972 | 1.8% |
| WR | 2 | — | 0.671 | 0.379 | 0.896 | 15.9% |
| WR | 3 | — | 0.446 | 0.132 | 0.692 | 55.6% |
| RB | 1 | — | 0.618 | 0.423 | 0.829 | 19.0% |
| RB | 2 | — | 0.288 | 0.105 | 0.452 | 96.1% |
| TE | 1 | — | 0.719 | 0.500 | 0.929 | 9.7% |

The p10/p90 spread is the argument: a WR3 plays under half the snaps in 56% of club-weeks, and a RB2 in
96%. Any model that treats "the starter is out" as a fixed downgrade is asserting a constant where the data
shows a distribution with a long lower tail. That is why the desk runs **ablations** rather than penalties,
and why the personnel feature is currently **not admitted**.

## The delta, not the level

Two official reads exist:

| Read | Clock | Week | Rows |
|---|---|---|---|
| Prior | 2026-11-18T03:55:13Z | Week 10 | 347 |
| This | 2026-11-19T06:53:00Z | Week 11 | 253 |

225 player-level changes, 213 players off the report. Both clocks appear on every delta row. Publishing a
level ("club X is banged up") would be an editorial claim; publishing the delta between two stamped reads
is a measurement. The two row counts are different weeks and are not comparable — a flag records that
rather than implying a drop in injuries.

## What is missing, and the cheapest route to it

- **Inactives** (90 minutes before kickoff) are the only authoritative "who is actually unavailable" list.
  Route: official inactives page, captured per game. Named as question Q03.
- **Week 10 snap counts** are absent from the pinned snapshot, so the most recent playing-time evidence for
  the Week 11 designations is Week 9. Stated on every affected row rather than silently carried forward.
- **Point-in-time depth**: to use availability in the model, the join must be as-of the pre-kickoff moment.
  The current join is 60% and is not.

## Refusals, restated

- No jersey-number depth order.
- No salary or experience as a proxy for role.
- No fixed per-player points penalty.
- No inferred replacement name: if an official source does not name the replacement, the cell stays blank.

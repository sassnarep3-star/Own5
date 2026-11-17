# Own5 NFL Decision Console — methodology (session `c98c6270`)

Live site: https://sassnarep3-star.github.io/Own5/nfl-c98c6270/
Code: `nfl-c98c6270/{content.py,engine.py,build_site.py,verify.py,run.py,tests/}`

## What this desk does

It answers one question: **what would have to be true before any number here
could justify a bet?** It originates its own NFL line from official league data
only, publishes the model column, leaves the market column blank, and publishes
the gate that blocks every conclusion.

## Pipeline (deterministic, no network at build time)

```
data/depth_capture_part1..8.tsv   (pinned official club depth charts, 2026-11-17)
data/standings_official.csv       (official 2026 standings)
data/slate_wk11.csv               (official week-11 schedule)
data/week10_finals.csv            (official week-10 finals)
nfl-desk-e46fb855/data/*          (carried forward, read-only)
            |
        engine.py  ->  data/*.csv
            |
      build_site.py ->  *.html
            |
        verify.py   ->  data/verification_report.json   (55 checks)
```

`python3 run.py` runs all three in order. Nothing fetches at build time: the
captures are the evidence. The GitHub workflow re-reads the live pages for
provenance only, and that step is deliberately non-blocking.

## Origination order (R-03)

1. **Side.** Ridge-penalised least squares on home margin, one coefficient per
   team plus one home-field term, λ = 1.0 pt². The penalty is required for
   identifiability (every team plays every other at most twice); it shrinks
   every rating toward zero and that is disclosed everywhere the ratings appear.
   Spread = rating gap. σ = 13.5 is a published convention, not a league value.
2. **Total.** Two estimators, published side by side with the gap, until a
   chronological walk-forward separates them:
   - A: league rate plus the average of each side's own scoring and concession
     deviation from it.
   - B: Pythagorean expectation from points for/against, exponent 2.37
     (published convention, labelled as such).
3. **Moneyline.** Derived from the step-1 probability only. It never feeds back
   into the side, and `origination_steps.csv` records the dependency so the
   claim can be checked rather than believed.

## Depth

Depth comes from the club's own published depth chart, read on
2026-11-17. Rules:

- A slot is a **group**: ranks 1–4 are all published, not just the starter.
- A shared first string is published as shared (`Name A+Name B`), never resolved
  into an order.
- An empty first string is published empty. It is not filled from a lower rank.
- No depth order is ever derived from jersey number, experience or salary
  (standing rejection X-01). Green Bay prefixes names with jersey numbers; the
  number is stripped and the raw string kept.
- Houston publishes its chart inside an image. One row is published, with no
  names, and the fact is flagged (rejection X-03: never transcribe by eye).
- Only four clubs date their chart. Every other `as_of_published` cell is blank.

## Availability and deficiency

- The injury report is stored with both read clock times and published as a
  **delta**, not a level. Rows without a second read say so.
- Week 11 is not published: `/injuries/league/2026/reg11` serves the week-10
  report. Week-11 availability therefore falls back to week 10 and says so.
- A "recommended starter" is the highest-ranked player in the slot who is not
  Out on the last official report. Where the rank-1 player is Out, the expected
  rank moves to 2, 3 or 4 and the pairing is marked a deficiency.
- A missing replacement is published as **unknown, not available**.

## Why the leaderboard is empty

Four divisions are defined and each names its blocking gate. Gate G1 requires
300 graded prospective bets; there are zero, because there are zero market
prices. A backtest number may never appear on the leaderboard at all (R-09),
so there is nothing to fall back on.

## Statistics

- Correlations: Pearson r from the official standings only, with n and a Fisher-z
  95% interval. Five values the brief asks for cannot be computed from anything
  officially captured; they are withheld with the reason, not guessed.
- Power: exact binomial in log space (`_binom_tail`), not a simulation. The
  original `math.comb` implementation overflowed at n ≥ ~1030; the replacement
  computes the tail from log-gamma and is tested up to n = 4000.
- Luck panel: Pythagorean expectation minus actual win rate, plus one-score-game
  record, both from official numbers.

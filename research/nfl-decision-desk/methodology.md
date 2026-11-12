# NFL Decision Desk — methodology (session arena-e413f933)

## Line origination (own lines)

Reproduces the repo-documented model exactly (see `scripts/originate_lines.py`):

```
rating(team) = (PF - PA) / G
shrunk(team) = rating * G / (G + 4)        # empirical-Bayes shrink toward 0
margin       = shrunk(home) - shrunk(away) + HFA
HFA          = 2.0 pts (2002-2024 mean home margin); 0 at neutral sites
total        = (PF_h/G_h + PA_a/G_a + PF_a/G_a + PA_h/G_h) / 2
```

- Inputs: official standings through Week 9 + official Week-10 schedule.
- Munich game (NE @ DET) treated as neutral: HFA = 0.
- Lines rounded to nearest 0.5 (Python `round` half-to-even, matching the
  prior session's `numpy.round` behaviour for continuity).
- **Market columns are blank** — no official public source publishes betting
  lines (flag F-MKT-1, question Q07). They are never filled by inference.
- **Deficiency advisory** (`advisory_spread_defadj`) is a separate heuristic,
  never merged into the model line: −1.0 pts per Out starter, −0.5 per DNP,
  capped at −3.0 per team, applied half-weight to the margin. Fixed rule,
  documented here, labelled in the CSV.

## Deficiency tracking (injuries × depth charts)

- Source A: official league injury report (practice participation + game status).
- Source B: official club depth charts (starter → 2nd → 3rd → 4th strings).
- Join: player name (normalised: case, punctuation, suffixes) must appear as a
  listed starter. No fuzzy matching that could guess.
- Severity weights: Out 1.0, Questionable 0.25, DNP 0.5, Limited 0.0
  (only ≥2 designations become deficiency rows: Limited, DNP, Questionable, Out).
- Replacement: next listed non-empty backup cell. If that player is himself
  officially Out, the chain advances to the next string (`effective_*` columns).
  Advancing only skips players with `game_status = Out` — arithmetic on two
  official lists, not a prediction of who will play.

## Luck vs skill

- Pythagorean expected wins: `PF^2.37 / (PF^2.37 + PA^2.37) * games`
  (ties counted as 0.5 wins). Exponent 2.37 is an **a-priori model parameter**,
  not an official value — labelled as such in every output row.
- `luck_index = actual_wins − expected_wins`. Positive = winning more than
  scoring differential implies.

## Correlations

- C01–C04 computed from official standings (Pearson/Spearman, n stated per row).
- C05 (parlay leg correlations) stays **pending** until ≥4 weeks of official
  final scores exist; gate G4 stays closed until then.
- C06 (model vs market CLV) stays **blocked** pending a market-line policy
  decision (Q07/S04). Never estimated.

## Validation gates (all strategies)

| Gate | Rule | State |
|---|---|---|
| G1 | ≥100 graded bets or ≥4 completed weeks | pending |
| G2 | ROI > 0 at −110 (breakeven 52.38%) | pending |
| G3 | Positive CLV over ≥20 paired observations | blocked (no market source) |
| G4 | Pairwise leg correlation computed and below pre-registered threshold | pending (C05) |
| G5 | Edge survives excluding one-score-game luck | pending |
| G6 | Every input row has an official source link; blanks flagged | automated in `verify_nfl_desk.py` |
| G7 | Official inactives confirm starter assumptions before grading | pending |
| G8 | Input source is official or user-approved | failed for props (F-PROP-1) |

## Rewards / leaderboard

Tier rules (unchanged from prior session's `data/leaderboard.csv`):

- **Tier 1** (top 3 by risk-adjusted return): featured placement + largest research allocation.
- **Tier 2** (next 4): standard research allocation.
- **Tier 3** (validated but lower ranked): honorable mention.

Tiers activate only when a strategy passes G1+G2. Until then all metric cells
stay blank — pending status, never fabricated.

## Verification policy

- Every table row published on the site carries an official source link.
- Unconfirmable values are blank and flagged; nothing is inferred.
- `nfl-decision-desk/verify_nfl_desk.py` enforces both before merge.

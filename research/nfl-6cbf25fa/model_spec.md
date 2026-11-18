# Pre-registered model specification — session 6cbf25fa (NFL Price & Ledger Desk)

Frozen 2026-11-18, before any Week 11 game has been played and before the
Week 11 lines were computed. The commit hash of this file is the registration.
The SHA256 of this file is recorded in `data/nfl-desk-6cbf25fa/model_inputs.json`.
No part of this spec may be edited after lines are published; a change requires
a new version of this file and a new origination snapshot.

## Purpose

Originate our own fair prices for the Week 11 slate (side first, then total,
then moneyline) from verified game results only, store the opening snapshot in
the price-snapshot store, and publish the residual against the market once a
verified market price source exists (currently: none — market columns stay
blank and flagged).

## Input corpus (verified game results)

1. 2026 regular-season finals, Weeks 1-9, from the pinned nflverse snapshot in
   `data/decision-desk/raw/games.csv.gz`, re-verified against the sha256 hashes
   in `data/decision-desk/raw/provenance.json` on every pipeline run.
2. 2026 Week 10 finals (14 games) from the official NFL.com scores page,
   read 2026-11-18 (read_utc 2026-11-18T03:55:13Z), stored in
   `data/nfl-desk-6cbf25fa/results_week10.csv`.
3. No other input. No injury, depth, snap-count or weather feature enters this
   model (an availability-adjusted variant is future work once the Week 11
   official report is published; the gap is published, not hidden).

Total corpus: 148 games (134 from weeks 1-9 + 14 from week 10). The corpus n is
published with every derived number.

## Ratings

For each team i, over the corpus:

- `o_i` = offensive deviation = mean points scored by i minus league mean
  points per team-game.
- `e_i` = defensive effectiveness = league mean points per team-game minus
  mean points allowed by i.
- Two opponent-adjustment iterations: `o_i ← mean over games of
  (points_i − L + e_opp)`, `e_i ← mean over games of (o_opp − (points_allowed_i − L))`,
  recentering `o` and `e` to mean zero after each iteration so that L remains
  the league mean points per team-game.
- `L` = league mean points per team-game (a single constant, published).

## Home-field advantage

- Estimated as the mean residual `(actual home margin − predicted margin)` over
  location=Home games only (n published). Predicted margin uses the converged
  ratings and no HFA.
- Neutral-site games (location=Neutral; Week 10 NE@DET Munich; Week 11 MIN@SF
  Mexico City, confirmed from the official game centre) receive HFA = 0.

## Spread (side), total, moneyline

- Expected home margin `m = (o_H − e_H) − (o_A − e_A) + HFA` (HFA term = 0 at
  neutral sites). Fair spread = m, published unrounded and rounded to the
  nearest 0.5 (halves away from zero, documented convention).
- Expected total `T = 2L + (o_H + o_A) − (e_H + e_A)`. HFA is deliberately NOT
  added to the total (documented simplification; the effect is small and the
  one-pass HFA estimate is fitted to margins, not totals).
- Win probability: `p_raw(home) = Φ(m / σ)` with σ = residual standard
  deviation of `(actual margin − expected margin)` over all corpus games (n
  published). The empirical tie rate `p_push = ties / games` is published with
  n. Published probabilities: `p_home_win = p_raw·(1−p_push)`,
  `p_away_win = (1−p_raw)·(1−p_push)`, `p_push` as estimated.
- Fair moneyline: American odds from p_win; decimal odds `(1−p_push)/p_win`.

## Publication rules (hard requirements from the brief)

- Every output row stores the model output as a probability (side/ML) plus the
  full input reference: `inputs_sha256` of `model_inputs.json`, which contains
  the ratings, HFA, σ, tie rate, corpus n and per-team games played.
- Fair line, market line, and the difference are separate columns. The market
  line and residual are blank and flagged (F-P01) until a verified operator
  price source exists; they are never inferred.
- Price-snapshot store: one immutable row per market per game with
  `opened_utc`, opening fair value, blank closing columns (status `open`;
  closings are filled only after the game completes, from official results,
  never estimated).
- Drift alarms: `verify.py` pins row counts and required fields and fails
  loudly on any change (league slate changed, missing score, probability sums
  not equal to 1, blank closing column filled without status change, etc.).

## Known limitations (published, not hidden)

- The corpus is one season (148 games); HFA and σ estimates carry wide
  uncertainty and are re-estimated weekly by rerunning this spec on the new
  corpus. No uncertainty interval is asserted on the lines themselves yet
  (future work: bootstrap over games).
- Week 11 availability (injuries/depth) is not yet a feature; the Week 11
  injury report had not been published at the read time (flag F-P02). The
  origination is therefore availability-blind and marked as such.
- Market prices are absent; no CLV, ROI or leaderboard claim is made from these
  lines. No staking: nothing here recommends a bet.

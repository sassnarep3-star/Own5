# Executive summary — NBA Line Commission (session arena-a46d621e)

Snapshot **2026-11-05 (UTC)**. Every value below is either transcribed from an official nba.com page
(with a per-row link on the site) or computed in-repo by `nba-commission/compute.py` from those rows.
Nothing is inferred. Where a value could not be verified it is blank and listed on the Flagged for
review page.

## What was built

- **11 own game lines** for the 2026-11-05 (2 games) and 2026-11-06 (9 games) slate: spread and total
  for every game, each with a seven-variant sensitivity grid (prior weight K ∈ {10, 20, 40}, home-court
  constant HFA ∈ {0.0, 2.5, 3.0}, and a no-prior/current-only variant).
- **8 own player-prop lines** (PTS, REB, AST, 3PM) for the two players with usable official game logs,
  each with the model mean, spread, empirical over-rate and push-rate at the published line.
- **Correlation values computed in-repo**: 7 team-level Pearson correlations (n = 30 teams), 7
  player-pair correlations with Fisher-z intervals (n = 137 player-games) and a genuine out-of-sample
  re-test of each (2025-26 vs 2026-27), 5 same-game prop-combo joint prices with φ and lift, and a
  lag-1 serial-independence check.
- **8 pre-registered strategies** across three families — singles, cross-game parlays (2- and 3-leg),
  same-game player-prop combos and a cross-game prop parlay — each behind **12 validation gates**.
- **A luck-vs-skill engine**: exact-binomial power curves, family-wise error bounds, worked
  coin-flip-style examples, and a deflation rule that shrinks a short hot streak toward break-even
  before it can be ranked.
- **A competition design** (deflated scoring, 50/30/20 tiers, a hard sample floor, anti-gaming rules)
  with an intentionally empty standings table.
- **A repo audit** re-verifying the six earlier NBA boards in this repository against official pages.

## What the numbers actually show

- **Net rating is the dominant team signal this season**: net points/game vs win% r = 0.9206
  (95% CI 0.8385–0.9619, n = 30). Points allowed is the stronger half of that (r = −0.7369 vs win%,
  points scored r = 0.5397).
- **Same-game prop legs are strongly dependent.** PTS × 3PM r = 0.7165 (n = 137); PTS × REB 0.3809;
  PTS × AST 0.2070. In joint terms, PTS ≥ 25 with 3PM ≥ 3 occurs in 65.7% of games versus 56.5% if the
  legs were independent — a lift of ×1.163. Pricing that combo off the product of marginals
  makes the independence-priced odds about 16.4% too generous (1.77 vs 1.52) before any vig. The pattern repeats for the other combos
  (PC5 PTS ≥ 30 & MIN ≥ 35: lift ×1.236).
- **Cross-game legs look close to independent, and that is all we can say.** Lag-1 correlation of a
  player's own points is +0.056 (Edwards, 61 games) and −0.041 (Dončić, 64 games). Near zero is
  consistent with independence across games; it cannot prove it, and the 2026-27 windows (4 and 8
  games) are too small to add anything.
- **The 2026-27 official home/road split does not measure home-court advantage**: 62–59 at home,
  two-sided binomial p = 0.856 over 121 team-games. HFA = 2.5 points is therefore published as an
  assumption (F02), not as a measurement, with 0.0 and 3.0 runs shown for every game.
- **Own lines are fragile to the model prior.** Across the seven variants a single game's spread spans
  up to 7.9 points (BOS @ CHA: −8.6 to −0.3). That range is published per game rather than hidden
  behind one number.
- **A 55% edge needs ≈2,248 graded bets** to be certified at α = 0.05 with 80% power against a −110
  break-even of 0.52381; a 60% edge needs ≈269. A bettor with exactly the break-even rate goes 55–45
  over 100 bets with probability 0.618, and reaches 55% over 200 bets 25.1% of the time. A true 55%
  bettor is detected only 17.8% of the time over those same 200 bets.

## What is not claimed

- **No edge, no ROI, no closing-line value, no reward.** No sportsbook price was verified in this
  session (F01). Every market column is blank by design.
- **No moneyline model** (F08): a win-probability model needs a margin-variance constant that is not
  verified from an official source.
- **No certification.** 0 of 8 strategies are certified; 0 graded bets exist; the leaderboard is empty.
- **No availability claim** (F04, F11): Anthony Edwards appears in 4 of Minnesota's 9 games and no
  official injury report was accessed; prop lines are unconditional on playing.
- **No legal or betting advice.** This is research on data provenance and statistical method.

## Deliverables

- Site: `nba-commission/` (14 pages, dashboard plus category subpages, every table row source-linked).
- Engine: `nba-commission/compute.py` (rebuild + 11 data checks), `nba-commission/build.py`,
  `nba-commission/verify.py` (provenance, link, render and idempotency checks).
- Data: `nba-commission/data/` — 2026-27 standings (30 rows), team stats (30 rows), slate (11 rows),
  2026-27 game logs (12 rows), inherited 2025-26 logs (125 rows), 2025-26 priors (30 rows), `outputs.json`.
- Method and record: `research/nba-commission/methodology.md`, `data-notes.md`, `repo-audit.md`, this file.

## Bottom line

The pipeline is real: official data in, own lines out, correlations measured, gates that fail closed,
and a leaderboard that cannot be gamed by a hot week. The edge is not demonstrated, and this summary
does not pretend otherwise — the honest reading of the numbers above is that a same-game combo is
mispriced by anyone who multiplies marginals, and that everything else needs a verified market price
and hundreds of graded bets before it means anything.

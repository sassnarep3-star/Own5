# Methodology and reproducibility

**Snapshot date:** 2026-11-12. All numeric fields are derived from the CSV inputs under `nfl-b34253a1/data/`; `seed.py` writes the reviewed/transcribed inputs, `engine.py` calculates model outputs, `content_seed.py` writes review registers, and `build.py` renders the static pages. No live sportsbook API, credential, or automatic wager function is used.

## Input provenance and reconciliation

- `games_2026_w1_w9.csv` holds 136 final games with NFL game-page and week-schedule URLs. It is derived from the repository's prior game log plus the independently checked Week 8/9 results; every row is linked to an NFL game page.
- `standings_2026_w10.csv` is the pre-Week-10 NFL standings snapshot. `engine.py` re-aggregates W/L/T/PF/PA from the 136 final game rows and checks every value for all 32 teams. Result: PASS; zero mismatches.
- `team_stats_2026_w10.csv` transcribes NFL team passing, rushing, defense-passing, and defense-rushing pages. Team abbreviations remain explicit; NFL `AZ`/`LA` labels were mapped to the local `ARI`/`LAR` keys only after team identity was checked, and no alternate code is silently erased from source provenance.
- `schedule_2026_w10.csv` has 14 games plus four BYE rows. `depth_chart_coverage_2026_w10.csv` gives one club chart source per NFL team.
- The source register records URLs, capture date, scope, and caveats. Dynamic pages were not preserved as raw HTML/PDF responses; a source URL and transcription do not make a dynamic page immutable.

## Baseline score-line formula

For team `t`, `G_t = W_t + L_t + T_t`, `PF/G = PF_t / G_t`, and `PA/G = PA_t / G_t`:

- Away projected points = `(away PF/G + home PA/G) / 2`.
- Home projected points = `(home PF/G + away PA/G) / 2`.
- Each team score is rounded to the nearest 0.5 point using ties-away-from-zero.
- Projected home margin = rounded home points minus rounded away points.
- Model home spread = negative projected home margin; model total = sum of the two rounded points.

There is no home-field adjustment, no fitted scoring distribution, and no numeric availability/injury adjustment. The four adjusted score fields are blank by design. Injury observation counts beside a line are selected-data counts only, not point-valued signals.

## Market comparison

For each scheduled game, one DraftKings and one FanDuel board/event quote was transcribed. The displayed two-book means are unweighted averages of the two quoted home spreads and totals. `model_home_margin_minus_market_home_line` is projected home margin plus the signed sportsbook home spread; `model_total_minus_market_total` is projected total minus the two-book mean. These are arithmetic comparisons only, not recommendations or proof of positive expected value. Different books may legitimately show different lines/prices.

The quote records are dated 2026-11-12 but do not preserve exact UTC capture time, jurisdiction, raw response/hash, account-level availability, limits, accepted price, or closing line. They cannot support executable-price, CLV, or return claims.

## Walk-forward evaluation

`build_walk_forward()` processes weeks in order. For each game in Week `w >= 2`, it calculates expected points from team PF/G and opponent PA/G accumulated only through Week `w-1`; it forecasts every game in that week before adding any same-week result. The 120 Week 2–9 forecasts are scored against official final margins. Reported error is actual minus projected.

Result: MAE `10.4048`, mean error `-0.7939`, Pearson projected-vs-actual margin `r=0.135006`, two-sided `p=0.141514`, Fisher-z 95% CI `[-0.045336, 0.306826]`. The interval is the ordinary independent-observation Fisher-z interval; it is not cluster-adjusted for shared teams/weeks. This is one season's sequential forecast evaluation, not an independent multi-season holdout, a betting ledger, or profitability evidence.

## Correlation calculations

Pearson's `r` is calculated from the paired values in the row's metric descriptions. The two-sided p-value uses the ordinary Pearson t-test (`df=n-2`); the 95% interval uses Fisher's z transform with standard error `1/sqrt(n-3)`. These calculations do not correct for multiple testing, ecological dependence, shared team inputs, or time/cluster dependence.

- CORR-01 to CORR-03 use the 32 pre-Week-10 team standings: PF/G, PA/G, and net points/G versus official win percentage.
- CORR-04 uses the 120 walk-forward projected and actual home margins.
- CORR-05 to CORR-07 are intentionally blank: the paired player-game prop outcomes, exact thresholds/odds, joint outcomes, and settlements are missing.

## Strategy/gate/leaderboard policy

Six strategy hypotheses are recorded with current evidence, missing inputs, and status. The eleven gates are project-defined governance rules, not NFL standards. Only G0 (input-source structure and result reconciliation) passes; G1–G10 remain blocked. Strategy rank, win rate, ROI, CLV, risk/luck-adjusted score, required sample size, and reward values remain blank or explicitly unavailable. No entry is eligible. No arbitrary sample threshold or prize budget was invented.

## Rebuild and verification

From repository root:

```sh
python3 nfl-b34253a1/seed.py
python3 nfl-b34253a1/engine.py
python3 nfl-b34253a1/content_seed.py
python3 nfl-b34253a1/audit_repo.py
python3 nfl-b34253a1/build.py
python3 nfl-b34253a1/verify.py
python3 -m unittest discover -s nfl-b34253a1/tests -v
```

The generated static pages use relative links and no third-party runtime dependency. `verify.py` checks data provenance, missing-field policy, HTML/CSV integrity, local links, accessibility structure, scope, and the audit artifact; it does not independently re-fetch dynamic external sources.

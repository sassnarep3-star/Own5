# NBA Line Desk 2026-27 — executive summary

Markdown copy of `nba-line-desk/executive-summary.html`. Every figure is computed by `tools/nba_line_desk/compute.py` and reproduced by `tests/test_nba_line_desk.py`.

## Bottom line

No NBA strategy is validated for 2026-27, and none should be used to place a bet.

One team-level association holds up. The 2025-26 final win% predicts the 2026-27 win% (r = 0.501, 95% CI 0.171 to 0.729, n = 30, permutation p = 0.0049, passes the Bonferroni threshold of 0.025). It is not a betting signal yet, for three reasons:

1. No official source publishes priced NBA markets, so the price and closing-line gates (G2–G5) cannot be tested (flag F07).
2. The target is measured on 5 to 8 games per team, below the 20-game sample gate (flag F08).
3. Reported 2026-27 prop-market restrictions are not confirmed on an official page (flag F06).

## Method

- Official data only: nba.com standings, team traditional stats and Anthony Edwards game logs for 2026-27; the 2025-26 final standings for the predictor. Sources S01–S08 (see `data/nba-2026-27/sources.csv`).
- 20 reconciliation checks, all passing. Standings and team stats agree for all 30 teams. The league record is 107-107. Box-score arithmetic holds for every game row.
- Pre-registered tests: same-season association (eight candidates, Bonferroni alpha 0.00625, permutation seed 20261103) and one out-of-sample predictor (alpha 0.025).

## Findings

- **Same-season (descriptive).** Three of eight candidates pass the corrected test: points per game, turnovers, and opponent points (the last is outcome-derived, flag F16). All three come from the same games as the target, so none is predictive (flag F17).
- **Out-of-sample (predictive).** Prior-season win% vs 2026-27 win% passes (r = 0.501). The margin version is r = 0.436 (95% CI 0.090 to 0.688, p = 0.0148, passes alpha 0.025). Both are team-level, one season, n = 30 (flag F18).
- **Luck.** 0 of 30 teams are beyond chance at p < 0.05 (about 1.5 expected). About 97 games per team are needed for a ±10-point win% estimate.
- **Power.** 783 priced bets are needed to detect a 55% true win rate (80% power, two-sided alpha 0.05).
- **Market.** The prior-season association may already be in the price. This cannot be checked without priced data.

## Decisions

- Market odds are not invented. Price, CLV and ROI cells are blank and flagged (F07).
- Reported prop restrictions are marked UNVERIFIED, not prohibited (F06).
- Same-season box-score signals are reported but never used as predictors.
- SIG03 was reclassified as outcome-derived after the first run. The change is disclosed, not hidden (F16).

## Repository review

See `research/nba-2026-27/review.md`. Key items: README does not link `nba-2026-lab/` (F02); an older note says there is no route to stats.nba.com (F03); older NBA notes cite betting-guide websites (F04); older NBA evidence is 2025-26 data (F01).

## Open items

13 open flags. See `nba-line-desk/flagged.html` (or `data/nba-2026-27/flags.csv`). None blocks the merge.

Analysis only. Not betting advice. Gambling problem? NCPG helpline 1-800-MY-RESET (S07).

# Methodology and reproducibility

## Evidence boundary

Snapshot `2026-11-03T23:39:30Z`. Official NBA inputs are manually transcribed into `nba-own-lines/data/*.csv`; analyst calculations are regenerated in `derived.json`. Dynamic official pages may subsequently change (F01). Official links support the input facts, not the analyst's model, gates or competition policy.

## Line origination

Definitions come from the [NBA glossary](https://www.nba.com/stats/help/glossary): OffRtg is points per 100 possessions, DefRtg is points allowed per 100 possessions, and PACE is possessions per 48 minutes.

For each rating `R`, with possession-weighted league baseline `L` and analyst-set prior `k = 10` games:

```text
weight = GP / (GP + k)
adjusted_R = L + weight × (R − L)
```

For away team A and home team H:

```text
expected_possessions = mean(adjusted_PACE_A, adjusted_PACE_H)
expected_eff_A = adjusted_OffRtg_A + adjusted_DefRtg_H − league_OffRtg
expected_eff_H = adjusted_OffRtg_H + adjusted_DefRtg_A − league_OffRtg
points_A = expected_possessions × expected_eff_A / 100
points_H = expected_possessions × expected_eff_H / 100 + HFA
margin_H = points_H − points_A
home_spread = −round_to_nearest_half(margin_H)
away_spread = −home_spread
total = round_to_nearest_half(points_A + points_H)
p_home = 1 / (1 + exp(−margin_H / 6))
p_away = 1 − p_home
```

`HFA = 0`; no home advantage is inferred. The 6-point logistic scale and 10-game prior are analyst assumptions, not NBA facts. American prices are no-vig conversions of model probabilities, rounded to whole numbers. They are not sportsbook quotes. The [official playing rules](https://ak-static.cms.nba.com/wp-content/uploads/sites/4/2026/10/2026-27-Official-NBA-Playing-Rules.pdf) supply timing/overtime context; overtime is not modeled.

## Player reference lines and combos

For each selected player, the complete current-season official log is used (Luka 7, Edwards 4, Maxey 8, Shai 7 games). Reference lines are arithmetic means rounded to the nearest 0.5 for PTS, REB, AST and 3PM. Script reconciliation requires every mean to match the corresponding official rounded per-game average.

Reference lines are not playable props. All playable fields are null. Edwards is suppressed because the [official report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-03_06_15PM.pdf) lists him Out. Other selected players are held because availability is not confirmed. Prop combinations have no directions, joint probabilities or payouts.

## Correlation and luck control

Pearson `r` is calculated for five team pairs (n = 30) and 16 selected player-game pairs (n = 4–8). Player tests use exact two-sided label-permutation p-values. Holm's step-down correction is applied across all 16 player tests. No adjusted p-value is below 0.05. These are continuous-stat associations, not threshold-specific joint-hit correlations.

For a future preregistered binary null, the module implements:

```text
P[X ≥ k] = Σ(i=k…n) C(n,i) p₀^i (1−p₀)^(n−i)
```

The null `p₀` must be declared for the actual market; 0.5 is only a function default/test example, not a universal betting assumption. Prospective proper scoring, price-aware evaluation, confidence intervals and multiplicity control are required before skill is claimed.

## Fail-closed contest

- **G00:** official provenance.
- **G01:** frozen snapshot and model specification.
- **G02:** availability resolved; unknown never passes; Out suppresses props.
- **G03:** timestamped market prices, payouts and settlement evidence.
- **G04:** prospective ledger without retroactive selection.
- **G05:** at least 100 graded out-of-sample forecasts per strategy.
- **G06:** preregistered predictive metrics beat a frozen baseline with uncertainty.
- **G07:** luck screen and multiple-comparison control.
- **G08:** combination dependence for parlays/prop combos.
- **G09:** written risk, no-leakage and no-stake-while-unqualified policy.

G00/G01/G09 pass on current documentary evidence. Other required gates fail. G08 is N/A for singles, never treated as a pass. No score or rank is manufactured from missing results.

## Reproduce and audit

```bash
python3 nba-own-lines/model.py
python3 nba-own-lines/build.py
python3 nba-own-lines/check.py
python3 -m unittest discover -s nba-own-lines -p 'test_*.py' -v
python3 -m unittest discover -s tests -q
```

Expected local result at integration: 16 new tests and 56 existing tests pass; checker reports 11 pages, 199 table rows, 454 links, 16 lines and 0 qualified strategies. `build.py` must produce byte-identical committed HTML and `derived.json` must equal a fresh calculation.

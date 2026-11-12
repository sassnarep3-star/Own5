# Strategy pre-registration

Committed before the current results were inspected. Variants are fixed; abandoned variants are
still counted in the multiplicity budget.

## Variants evaluated in this round (k = 7)

| ID | Rule | Sample |
|---|---|---|
| S1_home_underdog_ats | Back the home team whenever it is the underdog, ATS | 1980–2024 regular season |
| S2_home_dog_ge7_ats | Back the home team when it receives 7 or more points | 1980–2024 |
| S3_divisional_home_dog_ats | As S1, restricted to divisional games | 1980–2024 |
| S4_fade_10plus_favourites | Back the underdog when the favourite gives 10 or more | 1980–2024 |
| S5_over_closing_total | Back the over at the closing total | 1980–2024 |
| S6_home_off_bye_ats | Back the home team when it had 13+ days rest and the opponent did not | nflverse results 2010–2026 |
| S7_fade_more_injured | Back the side with the smaller lineup-deficiency gap | 2023–2026 |

Additional exploratory tests reported but **not** counted as certification candidates because they
were chosen after inspection: the ≥50 pp deficiency-gap subset, the starting-QB-out subset, and the
"model versus market" thresholds of 2/3/4 points.

## Pricing assumptions

- Standard −110 on every side: break-even = 110/210 = **52.38%**.
- Flat stake, pushes void and excluded.
- No stale-line assumption: every backtest uses the line recorded in the pinned dataset, whose
  timestamp is unknown (F01).

## Results (see `data/decision-desk/strategy_ledger.csv`)

All seven families land between 48.0% and 54.0%. None passes G2 after Bonferroni, none passes G3 on
a holdout, and G4/G8 cannot pass at all. The correct reading is that **none of these has
demonstrated skill** — not that they are proven losers.

## What would change the answer

A verified, timestamped price history would allow CLV to be measured. At that point the strongest
candidate is not any of the seven public rules above, but the injury-deficiency model used as a
pricing input, because it has a documented mechanism and a measurable effect on margin
(−0.039 points per percentage point, p = 6×10⁻⁵).

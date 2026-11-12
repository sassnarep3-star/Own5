# Originated Lines and Out-of-Sample Grading

**Session `26d4cafb` - snapshot 2026-11-12 UTC - NFL 2026 Week 10**

> Generated directly from `nfl-desk-26d4cafb/data/` by `engine.py`. Every row links to the official source it was read from. Values that could not be confirmed from an official source are left blank and listed on the Flagged for Review page.

## Originated Week 10 lines

| # | Date | Away | Home | Neutral | Pts away | Pts home | Margin | Spread | Total | P(home) | P(tie) | ML home | ML away | Home off toll | Away off toll | Mkt spread | Mkt total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W10-01 | 2026-11-12 | WAS | NYG | no | 22.33 | 22.7 | 0.37 | 0.5 | 45 | 0.4919 | 0.0595 | -110 | +110 | 0.0 | 0.4 | &mdash; | &mdash; |
| W10-02 | 2026-11-15 | NE | DET | YES | 24.42 | 24.02 | -0.41 | -0.5 | 48 | 0.4479 | 0.0574 | +110 | -110 | 0.275 | 1.587 | &mdash; | &mdash; |
| W10-03 | 2026-11-15 | KC | ATL | no | 22.19 | 21.59 | -0.61 | -0.5 | 44 | 0.4334 | 0.0602 | +117 | -117 | 0.0 | 0.175 | &mdash; | &mdash; |
| W10-04 | 2026-11-15 | HOU | CLE | no | 23.67 | 19.74 | -3.93 | -4.0 | 43 | 0.2502 | 0.0509 | +279 | -279 | 0.3 | 0.425 | &mdash; | &mdash; |
| W10-05 | 2026-11-15 | MIN | GB | no | 17.12 | 16.54 | -0.57 | -0.5 | 33 | 0.4264 | 0.0687 | +118 | -118 | 1.475 | 1.375 | &mdash; | &mdash; |
| W10-06 | 2026-11-15 | MIA | IND | no | 20.87 | 21.75 | 0.87 | 1.0 | 42 | 0.5227 | 0.0608 | -125 | +125 | 0.275 | 3.075 | &mdash; | &mdash; |
| W10-07 | 2026-11-15 | CAR | NO | no | 28.47 | 26.21 | -2.26 | -2.5 | 55 | 0.3544 | 0.0516 | +168 | -168 | 0.425 | 0.225 | &mdash; | &mdash; |
| W10-08 | 2026-11-15 | BUF | NYJ | no | 29.47 | 21.75 | -7.72 | -7.5 | 51 | 0.1246 | 0.0313 | +677 | -677 | 0.0 | 0.052 | &mdash; | &mdash; |
| W10-09 | 2026-11-15 | JAX | TEN | no | 28.62 | 15.57 | -13.05 | -13.0 | 44 | 0.0196 | 0.0086 | +4959 | -4959 | 0.0 | 0.0 | &mdash; | &mdash; |
| W10-10 | 2026-11-15 | LAR | ARI | no | 23.74 | 20.48 | -3.26 | -3.0 | 44 | 0.2857 | 0.0534 | +231 | -231 | 0.975 | 1.6 | &mdash; | &mdash; |
| W10-11 | 2026-11-15 | SEA | LV | no | 22.88 | 22.54 | -0.34 | -0.5 | 45 | 0.45 | 0.0593 | +109 | -109 | 0.0 | 3.225 | &mdash; | &mdash; |
| W10-12 | 2026-11-15 | SF | DAL | no | 29.23 | 24.17 | -5.06 | -5.0 | 53 | 0.2229 | 0.0431 | +329 | -329 | 0.325 | 0.95 | &mdash; | &mdash; |
| W10-13 | 2026-11-15 | PIT | CIN | no | 23.3 | 26.5 | 3.2 | 3.0 | 50 | 0.6489 | 0.0512 | -216 | +216 | 0.0 | 0.0 | &mdash; | &mdash; |
| W10-14 | 2026-11-16 | LAC | BAL | no | 19.11 | 15.84 | -3.28 | -3.5 | 35 | 0.2611 | 0.0582 | +261 | -261 | 5.5 | 0.0 | &mdash; | &mdash; |

> Market columns are deliberately blank: NFL.com publishes no spreads, totals or moneylines (FLG-01).

## Out-of-sample grading vs the repository's existing originators

| Model | n | MAE | RMSE | Bias | Total MAE | Accuracy | Brier |
|---|---|---|---|---|---|---|---|
| 26d4cafb walk-forward (this session, depth-adjusted) | 29 | 10.982 | 13.353 | -1.684 | 10.741 | 0.8276 | 0.1688 |
| line-lab market scrape (ESPN/DraftKings) -- THIRD PARTY | 15 | 9.6 | 11.895 | 5.667 | 9.567 | 0.8667 | 0.1472 |
| nfl-strategy-lab (originate_lines.py, HFA=+2.0) | 15 | 9.0 | 11.453 | 4.733 | 11.033 | 0.8 | 0.1591 |
| own5-desk (points-poisson-v0.1, HFA=0.0, k=8) | 13 | 10.193 | 12.58 | 4.148 | 9.615 | 0.7692 | 0.1252 |

### Matched sample (games every model graded)

| Model | n | MAE | Bias | Total MAE | Accuracy | Brier |
|---|---|---|---|---|---|---|
| 26d4cafb walk-forward (this session, depth-adjusted) | 13 | 11.028 | 4.896 | 9.538 | 0.8462 | 0.1648 |
| line-lab market scrape (ESPN/DraftKings) -- THIRD PARTY | 13 | 9.308 | 5.154 | 8.808 | 0.9231 | 0.1389 |
| nfl-strategy-lab (originate_lines.py, HFA=+2.0) | 13 | 9.808 | 5.346 | 9.615 | 0.7692 | 0.1664 |
| own5-desk (points-poisson-v0.1, HFA=0.0, k=8) | 13 | 10.193 | 4.148 | 9.615 | 0.7692 | 0.1252 |

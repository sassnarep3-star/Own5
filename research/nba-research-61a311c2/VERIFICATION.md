# Verification Record — Session 61a311c2

## Baseline and coordination

- Branch: `arena/61a311c2-own5`; claim commit `fdf6c15`; baseline main `54e8dee`. [Coordination](https://github.com/sassnarep3-star/Own5/blob/arena/61a311c2-own5/COORDINATION.md)
- Baseline inventory: 434 files hashed at `54e8dee596d49731c3da535a1f77b01cd0c295d5`. [Baseline tree](https://github.com/sassnarep3-star/Own5/tree/54e8dee596d49731c3da535a1f77b01cd0c295d5)
- Baseline test sweep before new work: 157 tests across 9 suites passed; nonfatal ResourceWarnings only. [Repo tests](https://github.com/sassnarep3-star/Own5/tree/54e8dee596d49731c3da535a1f77b01cd0c295d5/tests)

## Canonical row verification

| Dataset | Rows | Method | Status | Source |
|---|---:|---|---|---|
| Edwards 2025-26 log | 61 | Field-by-field comparison to official table | verified | [NBA](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) |
| Dončić 2025-26 log | 64 | Field-by-field comparison; explicit SeasonType | verified | [NBA](https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26&SeasonType=Regular%20Season) |
| Current player logs | 29 | Official table transcription/comparison | verified | [NBA](https://www.nba.com/stats/player/1629029/boxscores?Season=2026-27&SeasonType=Regular%20Season) |
| Prior team traditional | 30 | Selected fields transcribed from official table | verified | [NBA](https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season) |
| Current team advanced | 30 | Selected fields transcribed; W/L and Off-Def-Net reconciled | verified | [NBA](https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season) |
| Nov 5–6 schedule | 11 | Official schedule IDs/times/venues | verified | [NBA](https://www.nba.com/schedule?date=2026-11-06) |
| FanDuel Nov 5 quotes | 12 | Visible operator values; timestamp blank | verified value / flagged timestamp | [FanDuel](https://sportsbook.fanduel.com/navigation/nba) |
| Nov 6 availability | 4 | 4pm ET injury PDF; most teams NOT YET SUBMITTED | blank + flagged | [NBA PDF](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_04_00PM.pdf) |

## Explicitly not certified

The legacy 22-game `nba-desk` walk-forward sample was only partially re-verified (UTA@POR `0022600147` box-score chunk). The remaining rows are excluded from canonical qualification and flagged. Root executive claims citing preprints/industry conventions were not independently re-certified this session. [UTA@POR box score](https://www.nba.com/game/0022600147/box-score) · [Legacy executive summary](https://github.com/sassnarep3-star/Own5/blob/54e8dee596d49731c3da535a1f77b01cd0c295d5/EXECUTIVE_SUMMARY.md)

## Irregularities

19 flags are published on the dashboard, including legacy spread sign, invalid cross-game independence claim, mislabeled DSR shrinkage, non-ASCII header, scope mix, dynamic drift, tip-time mismatch and PACE/POSS non-identity. [Flagged page](../../nba-research-61a311c2/review.html) · [Baseline repo](https://github.com/sassnarep3-star/Own5/tree/54e8dee596d49731c3da535a1f77b01cd0c295d5)

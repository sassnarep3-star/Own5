# Flagged for review

The machine-readable [`flagged_review.csv`](../../nfl-b34253a1/data/flagged_review.csv) records 20 issues with severity, finding, impact, action, status, and source URLs. Items are open/nonblocking for this static research release; they are not resolved by having a citation link.

## High-impact open limits

- **No injury-to-points conversion:** all adjusted score/spread fields are blank. DNP/LP/OUT/IR and chart order are separate evidence, not a calibrated point penalty.
- **Selective, pregame injury snapshot:** 76 observations cover 17 teams. No final active/inactive or actual snap ledger is available for every listed player. Four bye-team chart pages are now documented but were not used as Week 10 injury signals.
- **Dynamic sportsbook snapshot:** 28 DraftKings/FanDuel quote rows retain event and board links, but no exact UTC time, jurisdiction, historical closing quote, execution check, or accepted-bet receipt. Follow-up page fetches on 2026-11-13 displayed NE@DET at +3 / 49.5 on the [official DraftKings NFL board](https://sportsbook.draftkings.com/leagues/football/nfl?category=games&subcategory=game-lines&nav_1=all-games), versus the stored Nov. 12 +2.5 / 51.5; the [official FanDuel NFL board](https://sportsbook.fanduel.com/navigation/nfl) displayed a 49.5 total versus the stored 50.5. With capture time and jurisdiction unretained, these are differing page displays, not a verified comparable price move. See FLG-05; neither row should be presented as a current quote.
- **No paired prop/parlay outcomes or settlements:** corresponding correlation values remain blank; no joint probability, fair combo price, EV, ROI, or CLV is calculated.
- **No proven skill:** 120 game-margin forecasts on one 2026 season yielded MAE 10.4048 and r 0.135006. No net-bet ledger, clustered uncertainty, multi-season holdout, or prospective registration.
- **Legacy repository material remains owned by prior sessions:** the repository audit distinguishes historic/nonofficial inputs and stale claims; this session did not overwrite those files or certify every old line.
- **Reward and eligibility governance absent:** no funded award, contest rules, jurisdiction review, or verified eligibility. Ranks/rewards remain blank.

The [Flagged page](../../nfl-b34253a1/flagged.html) provides the complete row-level table and links each flag to its source evidence. The audit page separately explains the limits of the repository-wide line index.

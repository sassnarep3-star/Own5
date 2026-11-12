# NFL 2026 Week 10 research snapshot — executive summary

**Captured:** 2026-11-12 (UTC date only; some source pages did not expose an exact capture time)
**Scope:** results through Week 9, Week 10 schedule/market/status snapshot.
**Use:** exploratory, descriptive research only. This is not betting advice, a pick sheet, fair-price model, or a claim of profitable skill.

## What was checked

- 136 completed 2026 Week 1–9 games were reconciled against the NFL's pre-Week-10 standings. All 32 teams matched wins, losses, ties, points for, and points against; zero mismatches.
- The Week 10 slate contains 14 scheduled games and four bye teams. The dataset contains 32 team-stat rows and 32 club depth-chart source checks; selected injury/depth observations are not an exhaustive league injury ledger.
- A reproducible no-home-advantage baseline generated 14 Week 10 lines. It uses current team PF/G and the opponent's PA/G, rounded team scores to half-points, and applies no numeric injury adjustment.
- The DraftKings and FanDuel quote fields are distinct dated snapshots. The retrieved pages supplied no preserved UTC quote timestamp or jurisdiction; quotes are not established as executable or closing prices.

## Validation snapshot

The simple pre-week rolling PF/G + opponent PA/G model was evaluated on 120 Week 2–9 games using only results through the previous week: **MAE 10.4048 points**, mean error (actual minus projected) **-0.7939 points**, projected-versus-actual margin **r = 0.135006**, two-sided **p = 0.141514**, naive Fisher-z 95% interval **[-0.045336, 0.306826]**. The interval and p-value do not adjust for shared teams or weeks. This is a one-season descriptive forecast evaluation, not a profitability test or validated betting skill.

Three 32-team standings correlations are descriptive and ecological: PF/G vs. win percentage `r=0.693836`; PA/G vs. win percentage `r=-0.666179`; net points/G vs. win percentage `r=0.875830`. Player-prop and parlay rows remain blank because paired game-level outcomes, exact prop prices, and settlements were not archived.

## What is not established

- No final active/inactive or actual snap ledger is attached to every injury observation; a DNP, LP, IR listing, or chart order is not proof of a Week 10 replacement.
- No validated player/string-slot-to-points coefficient exists in this snapshot. Adjusted spread/total fields are intentionally blank.
- No time-stamped historical market archive, closing-line ledger, wager ledger, settlement/void data, net ROI, CLV, or prospective multi-season holdout exists.
- Six strategies are defined, but none is validated. The source-integrity gate G0 passes; G1–G10 are blocked. No leaderboard rank, luck-adjusted score, funded reward, or eligible entry is reported.

## Navigate

- [Results and schedule](../../nfl-b34253a1/results.html)
- [Baseline lines and market snapshots](../../nfl-b34253a1/lines.html)
- [Injury/depth tracker](../../nfl-b34253a1/injuries.html)
- [Correlations](../../nfl-b34253a1/correlations.html)
- [Strategies](../../nfl-b34253a1/strategies.html)
- [Validation gates](../../nfl-b34253a1/validation.html)
- [Leaderboard and luck/skill status](../../nfl-b34253a1/leaderboard.html)
- [Source register](../../nfl-b34253a1/sources.html)
- [Decision questions](../../nfl-b34253a1/questions.html)
- [Suggestions for review](../../nfl-b34253a1/suggestions.html)
- [Flagged items](../../nfl-b34253a1/flagged.html)
- [Repository audit](../../nfl-b34253a1/audit.html)

Primary source registers and computation notes: [SOURCES.md](SOURCES.md), [METHODOLOGY.md](METHODOLOGY.md), [INJURIES_DEPTH.md](INJURIES_DEPTH.md), [FLAGGED.md](FLAGGED.md).

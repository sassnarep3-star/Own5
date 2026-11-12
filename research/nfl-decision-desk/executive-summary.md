# Executive Summary — NFL Decision Desk (Week 10, 2026)

_Prepared 2026-11-12 from official nfl.com sources and official club depth charts.
Session arena-e413f933. Every claim links a source; unconfirmable values are blank and flagged._

## What this desk does

Turns official NFL data into decision-ready output: our own game lines, a ranked
list of questions that must be answered before betting decisions, a reviewable
suggestions register, injury/depth-chart deficiency tracking, and a gated
strategy leaderboard — all with per-row official source links.

## Headline numbers (all official-derived)

| Metric | Value | Source |
|---|---|---|
| Standings captured | 32/32 teams through Week 9 | [nfl.com/standings](https://www.nfl.com/standings/) |
| Week-10 games scheduled | 14 games + 4 byes (CHI, DEN, PHI, TB) | [Week-10 schedule](https://www.nfl.com/schedules/2026/REG10) |
| Injury-report rows | 278 across all 14 games; 5 Out, 1 Questionable | [Official injury report](https://www.nfl.com/injuries/league/2026/REG10) |
| Depth charts captured | 27/28 Week-10 teams (HOU image-only → flagged) | 27 official club pages |
| Starter deficiencies found | 119 (2 Out, 68 DNP, 49 Limited starter rows) | injuries × depth charts |
| Net-points vs wins correlation | **r = 0.846** (n=32) — standings differential is a genuine skill signal | computed |
| Pythag expected vs actual wins | r = 0.864 — records largely track scoring | computed |
| Luck index extremes | DEN +2.17 (luckiest), TB −2.17 (unluckiest) | [luck_vs_skill.csv](../nfl-decision-desk-e413f933/data/luck_vs_skill.csv) |
| Deficiency load vs team quality | r = 0.254 (n=27) — injured rosters skew slightly weaker, weakly | computed |

## Week-10 lines we originate (model, not market)

Full table: [own_lines_2026_wk10.csv](../nfl-decision-desk-e413f933/data/own_lines_2026_wk10.csv).
Model = shrunken net-points + HFA 2.0 (0 at Munich). **Market columns blank —
no official source publishes betting lines (flagged F-MKT-1).**

Notable: BUF −7 @ NYJ · JAX −11.5 @ TEN · SF −4 @ DAL · PIT/CIN CIN −4.5 ·
NE@DET neutral DET −2.5 · advisory deficiency moves SEA@LV from SEA −3.5 to SEA −2
(Seattle carries the heaviest starter-deficiency load of any Week-10 team).

## Top deficiency signals for Week 10

1. **SEA** — 6 starters DNP including QB Sam Darnold and LT Charles Cross (Drew Lock effective string per report; officially ruled out news vs blank game-status → confirm via inactives, Q04).
2. **AZ** — 6 starters DNP across OL and front seven (C Froholdt, LG Seumalo, NT Lopez, OLB Sweat, S Baker, ILB Wilson) with backup-QB chart listing Beck.
3. **NE** — 2 starters officially Out (CB Carlton Davis III, LG Ben Brown) + RB chain broken: Stevenson DNP → Henderson **Out** → 3rd-string Kiner effective.
4. **SF** — CMC, Trent Williams, Mike Evans, Green, Lenoir, Greenlaw all DNP (8 deficiency rows); LCB Green has **no listed backup**.
5. **PIT** — T.J. Watt and Cameron Heyward DNP with **no listed backups** on the official chart.
6. **DAL** — 5 starters DNP (Ferguson, Hooker, Porter Jr., Ezeiruaku, Locke).

Full chains: [deficiencies_2026_wk10.csv](../nfl-decision-desk-e413f933/data/deficiencies_2026_wk10.csv),
per-team loads: [team_deficiency_index.csv](../nfl-decision-desk-e413f933/data/team_deficiency_index.csv).

## Questions that must be answered before decisions (D2)

15 registered questions with discovery methods: [questions_register.csv](../nfl-decision-desk-e413f933/data/questions_register.csv).
Blocking decisions:

- **Q07 (market lines)** — policy decision required from you: capture market lines manually from licensed screens, or keep market columns permanently blank (CLV gate G3 stays closed either way until decided).
- **Q13 (player props)** — no official prop source exists; STR-D5 stays blocked unless you approve an external source.
- **Q01/Q03/Q04/Q08/Q09** — resolve themselves at official inactives (90 min pre-kickoff); workflow proposal in S02.

## Suggestions for review (D3)

12 suggestions, each with effort/risk/benefit and the question it clears:
[suggestions_register.csv](../nfl-decision-desk-e413f933/data/suggestions_register.csv).
Highest leverage, in order: **S01** Friday injury refresh → **S02** inactives
confirmation gate → **S03** official results backfill (unlocks gates G1/G4) →
**S04** market-capture policy decision.

## Strategy competition status (D6)

- 7 strategies registered (singles, parlay, prop combo, QA): [strategies.csv](../nfl-decision-desk-e413f933/data/strategies.csv).
- 8 gates defined: [gates.csv](../nfl-decision-desk-e413f933/data/gates.csv). **No strategy has passed any staking gate yet — graded bets = 0.** This is reported, not hidden.
- Leaderboard tiers (rewards) defined; all metric cells blank pending graded data: [leaderboard.csv](../nfl-decision-desk-e413f933/data/leaderboard.csv).
- Luck-removal: Pythag residual index computed for all 32 teams (feeds STR-D6 fade rule at ±1.5 wins).

## Flagged for review (9 items)

HOU image-only depth chart · BAL chart-vs-transaction (Lamar IR) · MIA QB depth
gap · blank game-status on 272/278 injury rows · no market source · no prop
source · unconfirmed Week-10 QB starters · week-8 results CHI@SEA stale blank ·
(closed) week-8 re-verification passed 13/13. Full list with clearing actions:
[flagged_items.csv](../nfl-decision-desk-e413f933/data/flagged_items.csv).

## Bottom line

The desk is **decision-ready for model lines and deficiency analysis** on 27 of
28 teams, with every row sourced. It is **deliberately not ready** for staking:
gates G1–G5 need results history and (for G3) a market-data policy decision from
you. Nothing was inferred; everything unconfirmable is blank and flagged.

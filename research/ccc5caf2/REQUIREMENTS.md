# Decision-readiness matrix — OWN5 NFL Line Originator

**Session:** `ccc5caf2` · **Date:** 2026-11-18 · **Desk:** `nfl-desk-ccc5caf2/requirements.html`

Every brief requirement mapped to its blocking gate, the number that would clear it, and the observed status. Full table with source links: `nfl-desk-ccc5caf2/requirements.html`.

## Status summary

- ~39% of ~50 brief requirements met or defined
- 4 blocking questions (Q01, Q02, Q04, Q05) cannot be closed from public data
- 0 certified strategies (leaderboard intentionally empty)
- 18 flagged irregularities (F01–F18)

## Key rows

| Requirement | Blocking gate | Number that clears it | Observed |
|---|---|---|---|
| Price-snapshot store (open + close per market) | Price-data policy before backtests | Timestamped operator snapshot per market/week | Not met (F01, Q01) |
| Verified results feed | Verified closing price + matched outcome | 136-game pre-registered backtest corpus | Partial (F02) |
| Originate side → total → moneyline | Fair-line model + residual vs market | All 13 Week 11 games priced | Met (model) |
| Fair / market / difference columns | Market line with timestamp | fair · market · residual | Not met (F01) |
| Separate signal from staking | Proper-score ranking (Brier skill) | Brier skill + cluster lower bound + multiplicity | Not met |
| Track depth of replacement | Verified depth-slot group per player | Depth string + snap share per player/week | Partial (F05, F16) |
| Correlations from official sources, publish n | n recorded per coefficient | Pearson r / phi with n and CI | Met (F09) |
| Demotion gate | Any hard gate failure demotes | All hard gates pass before live | Defined |
| Pre-register every strategy | Commit hash = registration | Frozen rule text per variant | Defined |
| Availability graph (expected vs actual) | Depth-chart register + inactive/snap evidence | Date + source per roster row | Not met (F16) |
| Depth from playing time, not jersey order | Snap-count starter proxy | Snap share within team/position group | Met (inference, F05) |
| Injury signal = surprise, never level | Designation reliability (play rate + CI) | Delta, not level | Partial (F14) |
| 32-team roster/IR sweep | Reserve list captured | All 32 clubs checked | Not met |
| Venue per fixture from Game Centre | Official venue per fixture | Venue for all Week 11 games | Met |
| GitHub Pages live site | Site builds, no broken links | Live Pages deployment | In progress |

Blank values are unverified, never inferred. Flags link to the Flagged for review page (`nfl-desk-ccc5caf2/flagged.html`).

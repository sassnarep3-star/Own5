# Source audit and irregularities

## Scope

This session reviewed its additive `nba-strategy-lab/**` namespace and reused these previously reviewed frozen snapshots:

| Frozen input | Rows | Original reviewed repository location | Official source pattern |
|---|---:|---|---|
| Team seasons 2024-25 through 2026-27 | 90 | `nba-desk/data/team_seasons.csv` | `https://www.nba.com/stats/teams/traditional?...` |
| Team-game box scores | 44 | `nba-desk/data/games_sample_2026_27.csv` | `https://www.nba.com/game/{game_id}` |
| Archived schedule | 16 | `nba-desk/data/schedule_2026_11_04_05.csv` | `https://www.nba.com/schedule?month=11&year=2026` |
| Dončić / Edwards player games | 125 | `nba-signal-lab/data/game_logs_2025_26.csv` | `https://www.nba.com/game/{game_id}/` |

The board records prior sessions 4396568c and 6d508fee as having checked these inputs against official pages. This session preserves their raw values byte-for-byte and independently executes 547 provenance/arithmetic/relational checks. It does not claim a fresh NBA fetch; F06 keeps external reconfirmation open for manual review.

## Row-level rule

Every generated body-table row contains an official NBA link. Derived rows link to the official input/context page and are labeled model-derived or descriptive. No sportsbook source is represented as official. Blank source fields, market fields, ROI, ranks, scores and rewards remain blank.

## Open irregularities

- **F01 HIGH:** no verified sportsbook quotes or settlement ledger.
- **F02 HIGH:** 22 team games, three parlays and at most 51 pooled prop holdouts are insufficient for qualification.
- **F03 HIGH:** no current player-availability refresh; archived lines are not actionable.
- **F04 MEDIUM:** zero HFA and diagnostic residual scale are analyst conventions.
- **F05 MEDIUM:** prop evidence is a two-player convenience sample.
- **F06 MEDIUM:** external source pages were not freshly fetched in this session.
- **F07 LOW:** the 2026-11-04/05 schedule is archived.
- **F08 LOW:** no funded reward pool exists.
- **F09 LOW:** schedule venues are blank and two 2026-11-05 tip times are blank; nothing is inferred.

## Repository irregularities outside this namespace

The root repository contains multiple prior NFL and NBA dashboards with different scopes, snapshots, parameters, and conclusions. They are preserved, not merged into one supposedly consistent dataset. Their historical rows were not blanket re-certified here. The root Pages workflow is named for the evidence desk but the site is deployed from `main` at `/`; this naming mismatch is cosmetic and was not changed because workflows are outside the claimed scope.

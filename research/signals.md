# Signal Research — Generating Useful Signals (T4)

A **signal** is any measurable, officially-sourced input that can move our own line estimate away from the market line. Signals are only useful if they are (a) sourced from official data, (b) fresh, and (c) validated through the gates on the [Validation](validation.html) page. Anything that cannot be sourced officially is **excluded or flagged** — never estimated.

## Signal inventory

<!-- TABLE:signals.csv -->

## Example verified inputs (2026-11-02)

2026 passing leaders (official NFL player stats, REG through Week 8, sorted by passing yards): [nfl.com/stats/player-stats](https://www.nfl.com/stats/player-stats/)

<!-- TABLE:player-passing-2026.csv -->

## How signals become a line

1. Collect official inputs only: standings/stats [nfl.com/standings](https://www.nfl.com/standings/), [nfl.com/stats](https://www.nfl.com/stats/), injury report [nfl.com/injuries](https://www.nfl.com/injuries/), schedule/byes [nfl.com/schedules](https://www.nfl.com/schedules), NGS [operations.nfl.com](https://operations.nfl.com/gameday/technology/nfl-next-gen-stats), stat corrections [fantasy.nfl.com](https://fantasy.nfl.com/research/statcorrections).
2. Build a model price per game (our own line) from those inputs.
3. Compare with the operator-published line on official sportsbook pages ([FanDuel NFL](https://sportsbook.fanduel.com/navigation/nfl), [DraftKings NFL](https://sportsbook.draftkings.com/leagues/football/nfl)) — value exists only when model price and market price disagree by more than the gate threshold.
4. Size with quarter-Kelly (gate G07); never exceed correlation caps (G05, G09).

**Excluded by rule:** public betting percentages, "sharp money" claims, historical closing lines, weather values per game (no structured official field), sportsbook hold % — all flagged on the [Flagged for Review](flagged.html) page, all left blank in the data tables.

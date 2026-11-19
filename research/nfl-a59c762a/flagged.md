# Flagged for review — NFL Decision Console (session a59c762a)

**Published page:** [`nfl-desk-a59c762a/flagged.html`](../../nfl-desk-a59c762a/flagged.html)
**Machine-readable register:** [`nfl-desk-a59c762a/data/flagged.csv`](../../nfl-desk-a59c762a/data/flagged.csv)

Nothing here blocks the site. Every item carries the official source that produced it,
so it can be reviewed and a change requested. The two items marked *critical* and
*blocking* are the ones that would change a decision.

| ID | Severity | Item | Official source |
|---|---|---|---|
| F-A59-01 | critical | The repository's primary 2026 results feed leaves the Week-10 Chargers at Ravens row blank, and the official page shows it finished 23-20 on 16 November. A per-club reconciliation against the official standings fails for exactly Baltimore and the Chargers. A cross-session request has been raised; the owning session's file is not edited by this desk. | [Week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10) · [standings](https://www.nfl.com/standings/league/2026/REG) |
| F-A59-02 | blocking | No market price source is admitted, so no market line, residual, closing-line value or return exists. Every money cell is blank and flagged and the dependent gates are BLOCKED rather than failed. | see SG-A59-01 |
| F-A59-03 | review | Four other repository results feeds are shorter than the true 150-game corpus; one omits the Rams at Cardinals row and leaves the Chargers at Ravens row as not final. | [standings](https://www.nfl.com/standings/league/2026/REG) |
| F-A59-04 | review | The repository's earlier Week-11 availability read was a ten-row game-page sample, and its club statements that Minnesota and San Francisco had no active injuries are superseded by the full league report. | [Week 11 injury report](https://www.nfl.com/injuries/league/2026/reg11) |
| F-A59-05 | blocking | The depth-order source is verified for 31 of 32 clubs: Houston publishes depth as an image and the Patriots capture is partial. The backup-deficiency feature, the matchup matrix and the starters-out count are therefore left unbuilt. | see SG-A59-02 |
| F-A59-06 | review | The availability graph covers one game. The official Game Book route is proven, but there is no league-wide capture job. | [Game Books index](https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books) |
| F-A59-07 | review | No official snap-count source was verified. The Game Book carries no snap counts and the Next Gen Stats glossary documents no public per-player play series. | [Next Gen Stats glossary](https://nextgenstats.nfl.com/glossary) |
| F-A59-08 | resolved | The three blank Lions game-status cells are the publisher's timing, not a parsing failure: the Sunday columns are not yet published on a Thursday read. | [Week 11 report](https://www.nfl.com/injuries/league/2026/reg11) · [Week 10 report](https://www.nfl.com/injuries/league/2026/reg10) |
| F-A59-09 | review | No durable snapshot store, scheduler, freshness monitor or drift alarm exists. The multi-day availability series cannot yet be replayed as it was known. | — |
| F-A59-10 | review | Two official venue strings differ for the same fixture: the game centre prints RELIANT STADIUM and the schedule page hotel link says NRG Stadium. | [game centre](https://www.nfl.com/games/colts-at-texans-2026-reg-11) |
| F-A59-11 | review | The official schedule-release landing page carries no publication date, so the dated-announcement requirement cannot be satisfied from it. | [Schedule Release](https://www.nfl.com/nfl-schedule-release/) |

# Requirements trace

| ID | Requirement | Delivered evidence | Status | Official / project review |
|---|---|---|---|---|
| R01 | Originate own NBA lines | 16 calculated November 4–5 spreads/totals/scores/no-vig model prices | Done as research baselines; not market claims | [NBA team stats](https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season) |
| R02 | Research signal-generating strategies | Seven registered hypotheses with explicit evidence boundaries | Done; zero released signals | [NBA games](https://www.nba.com/games) |
| R03 | Leaderboard with rewards | Unranked seven-entrant board; future 100/60/40 non-cash policy | Done; zero current rewards | [NBA team stats](https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season) |
| R04 | Singles, parlays, player prop combos | Three singles, two parlays, two prop-combo strategies; four concrete held/suppressed prop references | Covered; none qualified | [NBA player stats](https://www.nba.com/stats/players/traditional?Season=2026-27&SeasonType=Regular%20Season&PerMode=PerGame) |
| R05 | Validation gates | G00–G09, strategy matrix, unknown-never-passes logic | Done; 0/7 qualify | [Official injury report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-03_06_15PM.pdf) |
| R06 | Correlation values | Five team + 16 player-game Pearson coefficients; exact player permutation p and Holm adjustment | Done; exploratory only | [NBA player stats](https://www.nba.com/stats/players/traditional?Season=2026-27&SeasonType=Regular%20Season&PerMode=PerGame) |
| R07 | Remove luck / selectively skill-based | Frozen protocol, exact null tests, Holm correction, binomial function, prospective minimum | Done as controls; no skill claimed without evidence | [NBA glossary](https://www.nba.com/stats/help/glossary) |
| R08 | Executive summary | Dashboard overview plus `research/nba-own-lines/executive-summary.md` | Done | [NBA team stats](https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season) |
| R09 | Repo review / irregularities | CI and ownership review; existing tests; F01–F11 | Done for claimed scope; older rows not re-certified (F10) | [Project repository](https://github.com/sassnarep3-star/Own5) |
| R10 | Clean landing page and category subpages | 11 responsive static pages, dashboard tables, consistent navigation | Done | [Project repository](https://github.com/sassnarep3-star/Own5) |
| R11 | Every table row has an official source link | Automated audit of 199 body rows and 454 links | Pass | [NBA Games](https://www.nba.com/games) |
| R12 | Blank unconfirmed values; Flagged for Review | Null derived fields, blank HTML cells, blank register and F01–F11 | Pass | [Official injury report](https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-03_06_15PM.pdf) |
| R13 | Parallel-session coordination | Claim pushed first; additive scopes; concurrent board conflict preserved both records | Done | [Project coordination board](https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md) |
| R14 | Combined build and broken-link check | 16 new + 56 existing tests; deterministic 11-page checker | Pass locally; PR checks pending | [Project repository](https://github.com/sassnarep3-star/Own5) |
| R15 | PR, merge and Pages deploy | Fixed session branch is integration branch | Pending at this document's initial commit | [Project pull requests](https://github.com/sassnarep3-star/Own5/pulls) |
| R16 | No manual user input | Data collection, calculations, site, tests, integration and publication performed autonomously | In progress through R15 | [Project repository](https://github.com/sassnarep3-star/Own5) |

**Acceptance rule:** research-line origination can be complete while strategy qualification remains zero. Missing odds, availability, outcomes or dependence evidence must never be filled with guesses. Flagged items do not block static publication, but they do block signals and rewards.

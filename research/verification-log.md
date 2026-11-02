# Verification Log — Line-by-Line (T8)

**Rule applied throughout:** every factual value in every table row carries a link to an official source (nfl.com / media.nfl.com / operations.nfl.com / official club sites / official sportsbook operator pages / regulator-approved house rules / NCPG). Anything not confirmable from an official source is left **blank** and logged in `data/flagged.csv` / [Flagged for Review](flagged.html). No values were inferred.

**Verification date for all rows:** 2026-11-02 (UTC).

## What was checked, and how

| Check | Method | Result |
| --- | --- | --- |
| 2026 schedule format (18 weeks / 272 games / 17+3 / byes W5–14 / kickoff / Week 18 / 9 international) | Read official NFL Media announcement [link](https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced) | verified → LF05–LF13 |
| Per-team 2026 bye weeks | Read official NFL bye release [link](https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week); cross-checked 32 teams across weeks 5–14 (2+4+4+4+2+4+6+0+4+2 = 32) | verified → bye-weeks-2026.csv |
| Playoff format (14 teams, No.1-seed bye, 2v7/3v6/4v5) | Read official NFL.com news [link](https://www.nfl.com/news/owners-approve-expanding-postseason-to-14-teams-0ap3000001107961) | verified → LF15–LF17 |
| Tie = half win/half loss; tiebreaker ladder | Read [nfl.com tiebreaking procedures](https://www.nfl.com/standings/tie-breaking-procedures) | verified → LF18 |
| 2026 salary cap $301.2M (2025 $279.2M; 2024 $255.4M; 2022 $208.2M) | Read [NFL.com cap announcement](https://www.nfl.com/news/nfl-announces-2026-salary-cap-set-at-301-2-million-per-team) | verified → LF19–LF20 |
| Game length 60 min / four 15-min periods; Rule 16 OT | Read [2026 Official Playing Rules](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook) | verified → LF21–LF22 |
| NGS: 10 Hz tracking, 200+ data points/play, AWS | Read [operations.nfl.com NGS page](https://operations.nfl.com/gameday/technology/nfl-next-gen-stats) | verified → LF23 |
| Elias Sports Bureau = official statistician | Read [NFL stat corrections page](https://fantasy.nfl.com/research/statcorrections) | verified → LF24 |
| Official sportsbook partners + official data feed | Read [NFL.com partners announcement](https://www.nfl.com/news/nfl-announces-tri-exclusive-sports-betting-partners) | verified → LF25 |
| 32 teams, conferences/divisions, official club sites | Read [nfl.com/teams](https://www.nfl.com/teams/) (both page chunks) | verified → teams.csv |
| Standings snapshot (W-L-T-PCT-PF-PA-NET-STRK, 32 teams) | Read [nfl.com/standings](https://www.nfl.com/standings/); internal consistency asserted in code (NET=PF−PA, PCT formula, ΣW=ΣL) | verified → standings-2026-wk8.csv |
| Week 8 schedule/results/networks/byes/MNF weather note | Read [nfl.com/schedules](https://www.nfl.com/schedules) | verified → week8-2026-results.csv (4 network cells blank, F12) |
| Injury report exists & is official, Week 8 | Read [nfl.com/injuries](https://www.nfl.com/injuries/) | verified (SIG01/SIG02 source) |
| 2026 passing leaders top 10 | Read [nfl.com/stats/player-stats](https://www.nfl.com/stats/player-stats/) | verified → player-passing-2026.csv |
| Team stats pages live | Read [nfl.com/stats/team-stats](https://www.nfl.com/stats/team-stats/) | verified (SIG05 source) |
| Bet definitions (spread/ML/total/parlay/SGP/teaser/prop/live/round robin) | Read [DraftKings NFL](https://sportsbook.draftkings.com/leagues/football/nfl), [FanDuel NFL guide](https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl), [FanDuel parlay guide](https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet) | verified → bet-types.csv |
| Grading rules (OT counts; tie→ML void; push on whole number; postponed→void; relocated same-day→action; void-leg reprice; correlated legs rule; 55-min rule; prop void if inactive) | Read [FanDuel grading FAQ](https://sportsbook.fanduel.com/navigation/nfl), [FanDuel house rules](https://www.fanduel.com/fanduel-sportsbook-house-rules-on), [BetMGM MA house rules PDF](https://massgaming.com/wp-content/uploads/BetMGM-House-Rules-8.14.25.pdf) | verified → bet-types.csv BT10–BT12, bet-combos.csv |
| Key numbers 3 and 7 (teasers) | Read [FanDuel NFL guide](https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl) | verified |
| Helpline 1-800-GAMBLER (1-800-426-2537), text 800GAM, chat, 24/7 | Read [NCPG helpline page](https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/) | verified → LF26 |
| Correlation values | Computed by `tools/compute_correlations.py` from the verified standings snapshot; assertions on the official data all passed | computed in-repo → correlations.csv |
| Historical closing lines / CLV / line movement | Searched official sources — none publish these | **not verifiable → blank + flagged F01** |
| Live line values at a point in time | Dynamic operator pages; no official static snapshot | **not verifiable as a value → blank + flagged F02** |
| Same-game leg correlation coefficients; hold %; public betting %; per-game weather values | No official source | **blank + flagged F03–F06** |
| Strategy performance metrics | No graded-bet history exists in-repo | **blank + flagged F07 — never fabricated** |

## Irregularities noticed during verification (all on [Flagged for Review](flagged.html))

- F09: `nfl.com/standings/league/2026/reg8` and `/REG9` rendered "No Standings Available" to the automated fetch; the default `/standings/` URL rendered the full table — snapshot taken from the default URL.
- F10: injury-report URLs (e.g., `/injuries/league/2026/reg7-1`) do not match the displayed "Week 8" label.
- F12: TV network text missing for 4 of 13 played Week-8 games in the fetched markup → those cells left blank.
- F08: BetMGM house-rules PDF cited is the Massachusetts (regulator-approved) version; other states file their own.

## Reproduce

```
python3 tools/seed_data.py              # writes all data/*.csv (with per-row source_url)
python3 tools/compute_correlations.py   # asserts official-data consistency, writes data/correlations.csv
python3 tools/build_site.py             # renders the static site + data/*.json from CSVs + research/*.md
python3 tools/check_site.py             # re-verifies every CSV row has a source link; checks HTML links
```

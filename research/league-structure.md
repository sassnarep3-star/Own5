# League Structure & Rules — Verified Research (T2)

All facts below were verified on 2026-11-02 against official NFL sources. Machine-readable version: `data/league-facts.csv`, `data/teams.csv`, `data/bye-weeks-2026.csv`, `data/standings-2026-wk8.csv`, `data/week8-2026-results.csv`.

## Structure

- **32 teams**, two conferences (AFC, NFC), four divisions each (East, North, South, West), four teams per division. [NFL.com teams](https://www.nfl.com/teams/) · [NFL.com standings](https://www.nfl.com/standings/)
- Each club's official website is linked from the NFL teams directory (see `data/teams.csv` for all 32). [NFL.com teams](https://www.nfl.com/teams/)

## 2026 season format

- **18-week, 272-game regular season**; each team plays **17 regular-season games + 3 preseason games** (sixth consecutive year at 17+3). [NFL Media schedule announcement](https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced)
- **One bye week per team**, byes Weeks 5–14, none in Week 12 (Thanksgiving week). [NFL bye-week release](https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week)
- Kickoff: **Wednesday, Sept 9, 2026, Seattle**. Week 18: Sat Jan 9 – Sun Jan 10, 2027, all 16 games intra-division (17th straight year). [NFL Media](https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced)
- **Nine international regular-season games in 2026** (most ever), incl. first games in Melbourne, Paris, Rio de Janeiro; three in London, plus Madrid, Mexico City, Munich. [NFL Media](https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced)
- Scheduling formula: 17 games built so every team plays every division in the other conference once every four years; home/away alternates (9 home one year, 8 the next). [operations.nfl.com — Making the Schedule](https://operations.nfl.com/calendar-events/nfl-schedule/making-the-schedule)

## Playoffs

- **14 playoff teams (7 per conference) since the 2020 season**; only the **No. 1 seed in each conference** receives a first-round bye; Wild Card: **2 hosts 7, 3 hosts 6, 4 hosts 5**. [NFL.com — owners approve 14-team postseason](https://www.nfl.com/news/owners-approve-expanding-postseason-to-14-teams-0ap3000001107961)
- Tie games count as **one-half win and one-half loss**; the full tiebreaking ladder (head-to-head → division → common games → conference → strength of victory/schedule → points scored/allowed rankings → net points → net TDs → coin toss) is published officially. [NFL.com tiebreaking procedures](https://www.nfl.com/standings/tie-breaking-procedures)

## Rules & timing

- Game length: **60 minutes, four 15-minute periods** (Rule 4, Game Timing); overtime per **Rule 16**. [2026 Official Playing Rules — operations.nfl.com](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook) (PDF: [media.nfl.com](https://media.nfl.com/content/dam/communications/Official%20Playing%20Rules/2026%20Official%20Playing%20Rules.pdf))
- 2026 rules changes include kickoff alignment items (6-1-3, 6-1-5), onside kick declaration at any time (6-1-6), and league consultation on disqualifications (19-2). [2026 rulebook](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook)

## Finance

- **2026 salary cap: $301.2 million per club** — first time above $300M; up $22M from 2025 ($279.2M); 2024 was $255.4M; 2022 was $208.2M. [NFL.com](https://www.nfl.com/news/nfl-announces-2026-salary-cap-set-at-301-2-million-per-team)

## Official data infrastructure

- **Next Gen Stats**: tracking in every venue (Zebra Technologies, Wilson) on AWS; location/speed/acceleration at **10 Hz**; **200+ data points per play**; metrics include completion probability, expected rushing yards, win probability. [NFL Football Operations](https://operations.nfl.com/gameday/technology/nfl-next-gen-stats)
- **Elias Sports Bureau** is the official statistician of the NFL; official stat corrections are released by the NFL League Office and Elias. [NFL stat corrections](https://fantasy.nfl.com/research/statcorrections)
- Player/team stats and standings are published at [nfl.com/stats](https://www.nfl.com/stats/) and [nfl.com/standings](https://www.nfl.com/standings/); schedules at [nfl.com/schedules](https://www.nfl.com/schedules); the weekly injury report at [nfl.com/injuries](https://www.nfl.com/injuries/).
- The NFL's Official Sports Betting Partners — **Caesars, DraftKings, FanDuel** — all use the **NFL's official league data feed**. [NFL.com](https://www.nfl.com/news/nfl-announces-tri-exclusive-sports-betting-partners)

## Snapshot tables (2026-11-02)

<!-- TABLE:standings-2026-wk8.csv -->

<!-- TABLE:week8-2026-results.csv -->

<!-- TABLE:bye-weeks-2026.csv -->

<!-- TABLE:teams.csv -->

# Executive Summary — Own5: NFL Line Origination & Skill-Based Strategy Lab

**Prepared:** 2026-11-02 (UTC) · **Season context:** 2026 NFL regular season, Week 8 complete (Monday Night Football Nov 2) · **Repo:** sassnarep3-star/Own5 · **Live site:** https://sassnarep3-star.github.io/Own5/

## What this project is

Own5 is an automated research lab for **originating our own NFL betting lines** instead of passively accepting market prices. The goal is to collect, organize, and analyze NFL data from official sources only, generate **useful signals**, run every candidate strategy through **validation gates**, measure and cap **correlations**, and rank surviving strategies on a **leaderboard with reward tiers**. Single bets, parlays, and player-prop combos are all in scope.

## Key verified facts (all sourced — see [Sources](detail-sources.html))

- The 2026 NFL regular season is **18 weeks, 272 games**; each of the **32 teams** plays **17 games** and **3 preseason games**, with **one bye week** (byes run Weeks 5–14; none in Week 12). Kickoff was Wednesday, Sept 9, 2026 in Seattle; Week 18 is Jan 9–10, 2027 with all 16 games intra-division. Nine international games are played in 2026 — the most ever. [NFL Media, May 14, 2026](https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced) · [bye weeks per team](https://amp.nfl.com/news/2026-nfl-schedule-release-every-team-bye-week)
- Playoffs: **14 teams (7 per conference) since 2020**; only the **No. 1 seed per conference** gets a bye; Wild Card is 2v7, 3v6, 4v5. [NFL.com](https://www.nfl.com/news/owners-approve-expanding-postseason-to-14-teams-0ap3000001107961)
- A tie counts as **half a win and half a loss**; full official tiebreaking ladder published by the league. [NFL.com tiebreaking procedures](https://www.nfl.com/standings/tie-breaking-procedures)
- **2026 salary cap: $301.2M per club** — first time above $300M (2025: $279.2M). [NFL.com](https://www.nfl.com/news/nfl-announces-2026-salary-cap-set-at-301-2-million-per-team)
- An NFL game is **60 minutes (four 15-minute periods)**; overtime per Rule 16 of the 2026 Official Playing Rules. [operations.nfl.com rulebook](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook)
- **Next Gen Stats** (Zebra/Wilson sensors on AWS) capture player location, speed and acceleration **10×/second, 200+ data points per play** in every venue. [NFL Football Operations](https://operations.nfl.com/gameday/technology/nfl-next-gen-stats)
- **Elias Sports Bureau** is the official statistician of the NFL; official stat corrections are released by the NFL League Office. [NFL stat corrections](https://fantasy.nfl.com/research/statcorrections)
- The NFL's **Official Sports Betting Partners** are **Caesars, DraftKings and FanDuel**, and all three use the **NFL's official league data feed**. [NFL.com](https://www.nfl.com/news/nfl-announces-tri-exclusive-sports-betting-partners)

## Current verified snapshot (2026-11-02, through Week 8)

- Full 32-team standings captured from [nfl.com/standings](https://www.nfl.com/standings/) → `data/standings-2026-wk8.csv`. Leaders: BUF 6-1, SF 6-1, MIN 6-1, PIT 6-2, DEN 6-2; bottom: LAC 0-7, TEN 1-7, MIA 1-6.
- Week 8 schedule/results captured from [nfl.com/schedules](https://www.nfl.com/schedules) → `data/week8-2026-results.csv` (14 games; byes HOU, NO, NYG, SF; MNF Nov 2 CHI@SEA 8:15 PM ESPN, game card weather note "Clear, night").
- Official Week 8 injury report: [nfl.com/injuries](https://www.nfl.com/injuries/).
- 2026 passing leaders captured from [nfl.com/stats/player-stats](https://www.nfl.com/stats/player-stats/) → `data/player-passing-2026.csv` (1. Jordan Love 2,246 yds … 10. Aaron Rodgers 1,871 yds).

## Strategy framework (10 strategies, all pending validation)

Singles (STR01 rest-edge, STR02 net-points mismatch, STR04 injury-adjusted, STR10 division dogs), player props (STR03 QB prop value), parlays (STR05 two-leg cross-game), same-game combos (STR06 SGP selective, STR07 cross-player prop combos inside SGP only), teasers (STR08 key-number 3/7), and live (STR09). **No performance numbers are shown anywhere: no graded-bet history exists yet, so every leaderboard metric cell is intentionally blank** (flag F07) — fabricating results would violate the project's no-hallucination rule.

## Validation gates (the anti-luck machinery)

12 gates (G01–G12): minimum sample (n≥30), backtest ROI>0 with 95% CI above break-even, walk-forward holdout, CLV (defined but **flagged — no official source publishes closing lines**, F01), correlation cap |r|<0.50 between strategies, max drawdown <20%, quarter-Kelly sizing, 100% officially-sourced inputs, parlay correlation rule (house rules void unpermitted correlated legs), grading integrity (OT included; pushes refund; postponed → void; inactive player → prop void), liquidity/limits, and a standing responsible-gambling gate (1-800-GAMBLER, 24/7 confidential — [NCPG](https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/)).

## Correlation findings (computed in-repo from official standings)

Pearson r across all 32 teams (2026 through Week 8, [nfl.com/standings](https://www.nfl.com/standings/), computed by `tools/compute_correlations.py` → `data/correlations.csv`):

- **Net points per game vs. winning %: r = 0.839** (strongest single-team signal)
- Points scored per game vs. win%: r = 0.614; points allowed per game vs. win%: r = −0.580
- Offense vs. defense per game (PF/G vs. PA/G): r = −0.012 (essentially independent — supports building separate offensive and defensive signals)
- Same-game betting-leg correlation coefficients: **not available from any official source → left blank, flagged (F03)**

## Bet-type rules that shape the combos

From official operator sources ([DraftKings NFL page](https://sportsbook.draftkings.com/leagues/football/nfl), [FanDuel guides & grading FAQ](https://sportsbook.fanduel.com/navigation/nfl), [FanDuel house rules](https://www.fanduel.com/fanduel-sportsbook-house-rules-on), [BetMGM regulator-approved house rules](https://massgaming.com/wp-content/uploads/BetMGM-House-Rules-8.14.25.pdf)): parlays need ≥2 legs and every leg must win; **correlated selections are not permitted unless explicitly offered (e.g., SGP)**; void legs re-price the parlay; OT counts for full-game spread/ML/totals; whole-number spread/total landing on the number is a push (refund); postponed before kickoff → void; relocated same-day → action; football results official after 55 minutes; player prop void if player not active; most common NFL margins are **3 and 7** (teaser key numbers).

## Irregularities flagged for review

12 items on the [Flagged for Review](flagged.html) page — including the standings deep-link rendering "No Standings Available" to automated fetches (F09), injury-URL week-label mismatch (F10), dynamic line values not snapshotted (F02), and all unverifiable market-history items (F01, F03, F04, F06). **None block publication; all unverifiable values are blank, never inferred.**

## Responsible gambling

This project is analytics research only. Sports betting is restricted to adults of legal age in their jurisdiction and carries real risk of loss. If gambling stops being fun: **1-800-GAMBLER (1-800-426-2537)**, text 800GAM, or chat — 24/7, confidential, all 50 states. [National Council on Problem Gambling](https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/)

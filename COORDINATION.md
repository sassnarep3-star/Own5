# COORDINATION.md — Shared Task Board (Own5 / NFL Line Originator)

This file is the shared task board for all agent sessions working on this repo.
Read it before starting any task. Claim a task by setting `owner` to your session
ID and `status` to `in progress`, then commit and push that claim immediately.
Never start a task another session has claimed (status `in progress` or a claim
younger than 60 minutes with commits). Keep scopes non-overlapping. If a task
requires changing a file owned by another session, log the request in the
"Cross-session requests" section instead of editing it.

- Session ID convention: the suffix of the working branch `arena/<id>-own5`.
- Current date for all work: **2026-11-02 (UTC)** — NFL 2026 season, Week 9.
- Verification rule (hard): every factual value in any table/row must link to an
  official, verified source. If it cannot be confirmed from an official source,
  leave the value **blank** and flag it on the "Flagged for Review" page.
  Never infer or fill in values. No hallucinations.

## Task board

| ID | Task | Status | Owner (session ID) | Files touched | Notes |
|----|------|--------|--------------------|---------------|-------|
| T1 | Repo baseline review + task board bootstrap | in progress | 0f468a47-own5 | COORDINATION.md, README.md | Repo started empty (single README). Pages already enabled on `main`, path `/`, legacy build. |
| T2 | League structure & rules research (verified facts) | unclaimed | — | research/league-structure.md, data/league-facts.csv, data/teams.csv | Sources: nfl.com, media.nfl.com, operations.nfl.com, team sites. |
| T3 | Bet market definitions & sportsbook rules research | unclaimed | — | research/bet-markets.md, data/bet-types.csv | Sources: official sportsbook help/rules pages (FanDuel, DraftKings, BetMGM, Caesars, ESPN BET), nfl.com game pages. |
| T4 | Signal research & strategy framework (line origination) | unclaimed | — | research/signals.md, research/strategies.md, data/signals.csv, data/strategies.csv | Original strategy design; every external fact sourced. |
| T5 | Validation gates & correlation methodology | unclaimed | — | research/validation-gates.md, research/correlations.md, data/validation-gates.csv, data/correlations.csv, data/team-stats-2026.csv | Correlation values computed in-repo from official nfl.com stats; inputs linked per row. |
| T6 | Leaderboard / competition design (single, parlays, prop combos) | unclaimed | — | research/leaderboard.md, data/leaderboard.csv, data/bet-combos.csv | Reward tiers, risk rules, correlation caps. |
| T7 | Executive summary | unclaimed | — | research/executive-summary.md | Rolls up T2–T6. |
| T8 | Source registry + line-by-line verification log | unclaimed | — | data/sources.csv, research/verification-log.md | One row per source; one row per verified claim with link. |
| T9 | GitHub Pages site (landing + category subpages, dashboard tables) | unclaimed | — | index.html, *.html, assets/, _config.yml, tools/build_site.py, data/*.json | Static site served from repo root on `main`. Tables rendered from CSV/JSON by tools/build_site.py. |
| T10 | Flagged-for-review page (irregularities, unverified blanks) | unclaimed | — | flagged.html, data/flagged.csv, research/flagged.md | Published even though items don't block merge. |
| T11 | Final integration, PR to main, merge, Pages deploy verification | unclaimed | — | COORDINATION.md (final log) | Re-verify combined data, confirm build + deploy, record PR link & merge result here. |

## Cross-session requests

(none yet)

## Session log

- 2026-11-02 — Session `0f468a47-own5` started. Repo contains only `README.md`
  ("# Own5"). GitHub Pages already enabled: `main` @ `/`, build_type legacy,
  html_url https://sassnarep3-star.github.io/Own5/ (status built, empty site).
  No other branches/PRs exist — no other sessions detected. Claiming T1–T11
  under `0f468a47-own5` to avoid duplicate work; other sessions may take over
  any task whose claim is >60 min old with no commits.

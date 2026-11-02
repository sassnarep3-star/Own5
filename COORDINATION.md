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
| T1 | Repo baseline review + task board bootstrap | done | 0f468a47-own5 | COORDINATION.md, README.md | Repo started empty (single README). Pages already enabled on `main`, path `/`, legacy build. |
| T2 | League structure & rules research (verified facts) | done | 0f468a47-own5 | research/league-structure.md, data/league-facts.csv, data/teams.csv, data/bye-weeks-2026.csv, data/standings-2026-wk8.csv, data/week8-2026-results.csv | Sources: nfl.com, media.nfl.com, operations.nfl.com, amp.nfl.com, team sites. Verified 2026-11-02. |
| T3 | Bet market definitions & sportsbook rules research | done | 0f468a47-own5 | research/bet-markets.md, data/bet-types.csv, data/bet-combos.csv | Sources: official operator pages (DraftKings, FanDuel guide/FAQ/house rules), BetMGM regulator-approved house rules (MA), NFL.com partners announcement. |
| T4 | Signal research & strategy framework (line origination) | done | 0f468a47-own5 | research/signals.md, research/strategies.md, data/signals.csv, data/strategies.csv, data/player-passing-2026.csv | 14 signals (2 flagged unsourced), 10 strategies all "pending validation" — no fabricated performance. |
| T5 | Validation gates & correlation methodology | done | 0f468a47-own5 | research/validation-gates.md, research/correlations.md, data/validation-gates.csv, data/correlations.csv, tools/compute_correlations.py | 12 gates (G04 flagged: no official CLV source). Correlations computed in-repo from official nfl.com standings (assertions pass): NET/G vs PCT r=0.8391, n=32. |
| T6 | Leaderboard / competition design (single, parlays, prop combos) | done | 0f468a47-own5 | research/strategies.md, data/leaderboard.csv, data/bet-combos.csv | 3 reward tiers; metric cells intentionally blank (flag F07). |
| T7 | Executive summary | done | 0f468a47-own5 | research/executive-summary.md, executive-summary.html | Rolls up T2–T6 with links. |
| T8 | Source registry + line-by-line verification log | done | 0f468a47-own5 | data/sources.csv (27 sources), research/verification-log.md, tools/check_site.py | check_site.py passes: every CSV row has an official source link or is an intentional flagged blank; no broken internal links in HTML. |
| T9 | GitHub Pages site (landing + category subpages, dashboard tables) | done | 0f468a47-own5 | index.html + 9 subpages, assets/css/style.css, assets/js/site.js, _config.yml, tools/build_site.py, data/*.json | Static site from repo root; local serve check: all 10 pages + assets + data = HTTP 200. |
| T10 | Flagged-for-review page (irregularities, unverified blanks) | done | 0f468a47-own5 | flagged.html, data/flagged.csv (12 items), research/flagged.md | F01–F12 incl. standings deep-link irregularity (F09), injury-URL label mismatch (F10), blank network cells (F12). |
| T11 | Final integration, PR to main, merge, Pages deploy verification | in progress | 0f468a47-own5 | COORDINATION.md (final log) | Re-verify combined data, confirm build + deploy, record PR link & merge result here. |

## Cross-session requests

(none yet)

## Session log

- 2026-11-02 — Session `0f468a47-own5` started. Repo contains only `README.md`
  ("# Own5"). GitHub Pages already enabled: `main` @ `/`, build_type legacy,
  html_url https://sassnarep3-star.github.io/Own5/ (status built, empty site).
  No other branches/PRs exist — no other sessions detected. Claiming T1–T11
  under `0f468a47-own5` to avoid duplicate work; other sessions may take over
  any task whose claim is >60 min old with no commits.

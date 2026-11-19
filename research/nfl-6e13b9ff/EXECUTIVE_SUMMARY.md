# Executive Summary — NFL Brief Traceability & Decision Desk (session 6e13b9ff)

**As of:** 2026-11-19 (UTC) · **Branch:** `arena/6e13b9ff-own5` · **Read stamps:** 2026-11-19T06:51:41Z (standings, Week-11 slate) and 2026-11-19T06:57:28Z (Week-11 injury report, Week-12 slate, IND@HOU game centre).

## What this session did

1. **Claimed first** in `COORDINATION.md` (protocol followed; scope strictly additive), then built a new desk at `nfl-desk-6e13b9ff/` with data under `data/nfl-desk-6e13b9ff/`.
2. **Re-read the official sources first-hand today**, line by line: all 32 standings rows, the complete 13-game Week-11 slate plus 6 byes, the newly published Week-11 injury report (26 designation rows for tonight's IND@HOU game), six Week-12 spot fixtures, and the IND@HOU game centre. Every row carries its official URL and read stamp — see `verification.csv` (61 rows) and the capture CSVs.
3. **Mapped every line of this session's brief** (84 requirement rows, `requirements_coverage.csv`) to a status with the blocking gate, the number that would clear it, the observed value, and in-repo evidence that must exist (the verifier fails otherwise).
4. **Published the registers the brief asks for:** 18 questions (`questions.csv`), 14 reviewable suggestions (`suggestions.csv`), 20 flagged items (`flagged.csv`), 6 official sources (`sources.csv`), plus this summary. Nothing in the suggestions register is implemented — each waits for an owner decision.
5. **Fail-closed verification:** `verify_desk.py` enforces per-row evidence-or-flag, official-host allowlist for `source_url`, PCT/NET arithmetic on all 32 standings rows, fresh-vs-prior capture diffs, pinned row counts, and internal link integrity. Unit tests include negative controls.

## Headline numbers (all sourced; blanks stay blank)

| Fact | Value | Source |
|---|---|---|
| Requirements of this brief in the coverage matrix | 84 | `data/nfl-desk-6e13b9ff/requirements_coverage.csv` |
| First-hand verification rows today | 61 | `data/nfl-desk-6e13b9ff/verification.csv` |
| 2026 standings rows re-read and diffed vs 2026-11-18 capture | 32/32 agree | nfl.com standings (official) |
| Week-11 slate | 13 games + 6 byes (ATL, CLE, GB, LAR, NE, SEA — bye section prints "LAR"; standings page uses "LA") | nfl.com schedule (official) |
| Week-11 injury report status | Published at `reg11` (served Week 10 on 2026-11-18 → flag F6-11 resolved) | nfl.com injuries (official) |
| TNF IND@HOU designations (first-hand) | IND: Out 5 / Questionable 5 / blank 2; HOU: Out 4 / Questionable 4 / blank 7 | nfl.com injuries (official) |
| Forecast freeze | All 39 Week-11 markets opened 2026-11-18T03:55:13Z, before tonight's 8:15 PM ET kickoff | price snapshot store + official schedule |
| Venue (IND@HOU), game centre vs schedule page | "RELIANT STADIUM" vs "NRG Stadium" — both official; recorded, not resolved (F6-04) | nfl.com game centre (official) |

## The gates that block the most (number that would clear each)

1. **G-10 price-data policy + source** — blocks fair/market/difference columns, residuals, vig-free decomposition, ROI/CLV. Clears with 1 signed policy + 1 source returning open+close for all markets. Observed: 39 schema rows, 0 priced (F6-15).
2. **G-DEPTH depth-order route** — blocks the backup-deficiency and matchup-deficiency features. Clears with one route verified for all 32 clubs. Observed: club-page verification incomplete; snap route runs only on an aggregator mirror (F6-16, F6-18).
3. **G-CORPUS count reconciliation** — blocks backtest publication. Clears with one pinned count (brief says 136, spec says 148, coordination record says 150) (F6-01).
4. **G-CAPTURE-HEALTH** — blocks every replay/backtest claim. Clears with 7 consecutive green daily capture runs. Observed: latest scheduled run failed at the rebuild step (F6-02); a second scheduled check is red (F6-03).
5. **G-FUND rewards** — clears with an approved pool amount; pool still blank (F6-20). **G-JOINT** — combos stay held at the gate (0 combo rows scored). **G-TERMS / G-POLICY** — public/private split and capture compliance need owner decisions.

## What is in good shape

Origination runs two consecutive slates (W10, W11) under a frozen spec with probabilities + inputs stored; signal/staking split, controls (random + favorites), four proper-score divisions, pre-registration, what-would-change-our-mind fields and the demotion gate are all in place; the luck-removal panel is published; results feed verifies Week-10 finals 14/14 with official Game Book links; the point-in-time injury ledger keeps stamps and deltas; designation archives exist 2023-2026 (aggregator-labelled); official-standings correlations publish n=32.

## Recommendations (nothing implemented without a decision)

See `suggestions.html` — 14 options, each with recommendation and what-would-change-our-mind. Top three: **S6-01** pick the price source this week; **S6-03** make the daily capture green again; **S6-04** triage the 14 open PRs (oldest since 2026-11-02).

## Irregularities (20, published on the Flagged page; none blocks this merge)

Highlights: three circulating corpus counts (F6-01); two red scheduled checks on `main` (F6-02, F6-03); venue string conflict across two official pages (F6-04); Week-12 heading/date mismatches (F6-05); a prior base-rate claim that failed its own claim-check (F6-10); stale coordination rows after merged PRs (F6-13); the availability-graph build sitting in unmerged PR #136 (F6-12); root banner still stamped 2026-11-02 (F6-08).

## Verification performed

`build_desk.py` (deterministic, stdlib) → `verify_desk.py` (fail-closed; runs after build) → `python -m unittest` (negative controls: a dropped row, a filled price cell, a broken link or a missing evidence file must fail). CI workflow `.github/workflows/nfl-desk-6e13b9ff.yml` runs build + verify + tests on every change to this scope.

## Sources

All external reads this session were first-hand from official nfl.com pages (register: `data/nfl-desk-6e13b9ff/sources.csv`). In-repo evidence links point to committed files; where a value could not be confirmed from an official source it is left blank and flagged — nothing is inferred.

# Shared task board — Own5

## Operating rules

- Official-source verification only for factual table values. Unsupported values stay blank and appear under Flagged for Review. Independent model calculations are identified as derived research, not official statistics or verified sportsbook lines.
- Claim a scope before work; record evidence, checks, and irregularities when finished. `needs review` items are published, not blocking.
- Shared table data, navigation, and final integration are reserved until research and implementation tasks are complete.
- Pull with rebase before pushing. Preserve concurrent work. A claim without a commit for over 60 minutes can be handed over with a log entry.
- Platform constraint: this session must use its assigned branch `arena/e0e66278-own5`; it cannot create or switch to `session-*` branches. Session ID: `e0e66278`. This exception is recorded rather than silently violating the platform branch policy.
- The starting repository and `origin/main` contain only `README.md`; no existing coordination claims or other implementation files were found at 2026-11-02 UTC.

## Claims

| Task | Status | Owner session | Files / non-overlapping scope |
|---|---|---|---|
| T01 — Source register and research methodology | done | e0e66278 | `research/`, `docs/METHODOLOGY.md`, `docs/SOURCE_AUDIT.md`, `docs/REQUIREMENTS.md`, `data/source_register.json`, `data/verified_facts.json`, `data/review_items.json` |
| T02 — Modeling, correlation, validation gates, leaderboard engine | in progress | e0e66278 | `nfl_model/`, `tests/`, `requirements.txt`, `scripts/` |
| T03 — Static dashboard and publication configuration | unclaimed | — | `site/`, `.github/workflows/`, `package.json`, `package-lock.json`, `.gitignore` |
| T04 — Final integration, line-by-line checks, PR, merge, Pages | unclaimed | — | `README.md`, `docs/EXECUTIVE_SUMMARY.md`, `docs/VERIFICATION_REPORT.md`, shared generated data, `artifacts/`, final publication metadata; append-only updates to this board |

This session will claim each subsequent task only after its predecessor is done. Another session may claim an unclaimed task using a different file scope. Cross-scope requests belong in the log below, not in an edit to another owner's files.

## Activity log

- 2026-11-02 UTC — e0e66278: reviewed the entire starting repository (`README.md`, 1 line), fetched `origin/main`, and confirmed no board existed. Claimed T01. Initial source audit will distinguish official NFL rules/results from unavailable sportsbook/prop inputs and from derived model outputs. No factual findings are yet marked verified.
- 2026-11-02 UTC — e0e66278: initial remote branch did not yet exist, so the first `git pull --rebase origin arena/e0e66278-own5` reported a missing remote ref. No merge/conflict occurred; the claim was then pushed successfully and tracking established.
- 2026-11-02 UTC — e0e66278: T01 done. Inspected 17 official/primary sources; froze 32 standings rows, 15 Week 9 matchups, 17 paired 2024 player-game rows, and 14 quoted rule/product facts (78 fact rows). Verified 5,528 league PF = 5,528 PA; Burrow 4,918 passing yards; Chase 1,708 receiving yards / 127 receptions against official career controls; all player week/date/opponent/result tuples match. Sources and exact evidence are linked in `data/source_register.json` and `docs/SOURCE_AUDIT.md`. Thirteen irregularities/missing-input items are recorded for review, including no verified market quotes, a mislabeled NFL Support article, a rejected player slug, and GSIS access limits. Claimed T02; no other session claim was present.

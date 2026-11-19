# Repo review (bounded) — session 8ad92a0e, 2026-11-19 UTC

Read-only review. No other session's files were modified; findings are published as
flags F8-07…F8-09 and in the cross-session section of `COORDINATION.md`.

## Inventory (observed this session)

| Metric | Value |
|---|---|
| Desk-like top-level directories (nfl/nba/sf/rental/own5/repo/site…) | 69 |
| HTML pages in repo | 706 |
| GitHub workflows | 44 |
| Open pull requests | 17 |
| COORDINATION.md size | ~525 KB / 4,301 lines |
| Root dashboard stamp | `AS OF 2026-11-02` (17 days stale — F8-07) |

## Verifier sweep (selected, read-only)

| Check | Result |
|---|---|
| `python3 tools/check_site.py` (root research desk) | **PASS**, 0 failures |
| `python3 nfl-desk-7e228db8/verify_desk.py` | **PASS**, 1,645 checks, 0 failures |
| `python3 -m unittest discover -s tests` (root suite) | **OK** |
| This desk: `nfl-desk-8ad92a0e/verify.py` | **PASS**, 3,009 checks, 0 failures |
| This desk: `python3 -m unittest discover -s nfl-desk-8ad92a0e/tests` | **13 tests OK** (7 negative controls) |

## CI state (main, observed ~11:19 UTC)

Mostly green: `pages build and deployment`, `Verify research dashboard`, `Verify Own5 evidence desk`,
`NFL desk 35fc3437 — verify`, `NFL cross-desk evidence review (74306746)`, `Verify NFL Origin Desk`
all success. `Verify nfl-desk-067f2314` showed an empty conclusion at read time — recorded as F8-09
(pre-existing, owned by that desk; sessions 51cf3786/7e228db8 documented related long-standing
red workflows owned by other desks). Not touched here.

## Irregularities for review (see `flagged.html`)

- **F8-07** root index stamped 2026-11-02; generator-locked (`scripts/build.py`, session cd43258e).
- **F8-08** sprawl: 69 desks / 706 pages / 44 workflows / 17 open PRs — navigation and CI costs;
  consolidation question Q8-16 open for the owner.
- **F8-09** pre-existing CI noise from other desks' workflows.
- **F8-12/F8-13** conflicting corpus counts across desks (136/148/150) — suggestion S8-01 proposes
  one canonical feed; this desk's adoption gate is documented on `results.html`.
- Brief claims checked this session: Lions Out designations (**not confirmed** — F8-05); "136-game
  log" = weeks 1–9 of the current 150-game feed (F8-13); Week-10 injury counts not re-counted here
  (F8-12, Q8-12).

## Cross-session status

No file owned by another session was edited. Requests that belong to other owners (root stamp
refresh, workflow sprawl, canonical corpus) are logged as suggestions S8-01/S8-10/S8-11 and
questions Q8-16, not actioned.

# Verification record — integration session 3ddb3f07 (2026-11-19)

Every check below was run in this session against the working tree, and the command is
given so it can be repeated. Nothing is asserted that was not executed.

## 1. Baseline captured before any repair

| Check | Command | Result |
|-------|---------|--------|
| Every desk's own verifier | `python3 repo-review/run_verifiers.py` | 30 verifiers, 27 PASS, 3 FAIL (`nba-commission`, `nfl-b34253a1`, `nfl-command-desk`) |
| Broken internal links (repo-wide) | `href`/`src` scan of every published HTML file, resolved as GitHub Pages resolves it | **127 broken** in 12 files |
| Red checks on `main` | `gh run list --branch main` | `Verify NFL read-and-decide desk (35a1feb2)` and `Own5 hub - daily official capture` failing |

The three failing verifiers were diagnosed individually:

* `nba-commission` — its repo-wide link scan reported the 127 broken links above as its own
  failures. The links were real; the desk was right to fail.
* `nfl-b34253a1` — the repository-wide line-hash audit pins the content of every file in its
  scope, so any change to an audited file fails the check until the audit is regenerated.
  This is a merge-time tripwire, not a data defect.
* `nfl-command-desk` — gate V11 checked that the published pre-registration hash exists and
  is an ancestor of HEAD. The hash `e7282e35…` (and the original `4078a9ad`) had been
  orphaned by a rebase on 2026-11-18, so the check could never pass again.

## 2. Repairs, each verified by the owning desk's own verifier

| Desk | Repair | Verification |
|------|--------|--------------|
| `nfl-desk-864d5668` | `build_site.py` now links a source cell only when it really is a URL; prose gets an explicit no-source marker. `verify.py` gained a guard that fails on any `href` that is not a path or URL. | `python3 run.py && python3 verify.py` → **37 checks, 0 failures**; the desk's own page text is unchanged |
| `nfl-desk-e1d60f5d` | links are written relative to the page that renders them; the nav pointed at `pages/executive-summary.html`, which does not exist (the file is `pages/exec.html`) | `python3 build.py && python3 verify.py` → **241 checks, 0 failures**; repo-wide scan of the desk → 0 broken |
| `nfl-desk-ccc5caf2` | `summary.html` linked `research/ccc5caf2/…` from inside the desk directory; now `../research/ccc5caf2/…` | repo-wide scan → 0 broken |
| `nfl-command-desk` | V11 rewritten: it proves the rule text at the published freeze commit is byte-identical to the committed file, that the freeze commit is in the current history, that the site quotes that hash, and that the site discloses the orphaned original registration. `FLAG-V11` added to the flagged register. | `python3 generate.py && python3 build.py && python3 verify.py` → **53 checks, 0 failures**; unit tests → **53 passed** |
| `own5-hub` | the published capture summary is derived from the ledger; a capture that does not parse is recorded with `parse_status`; gate G8 fails the build if the page and the ledger disagree | `python3 build.py && python3 verify.py` → **38 checks, 0 failures**; unit tests → **4 passed** |
| `own5-hub-capture.yml` | the immutable capture is committed before the pages are rebuilt, so a rebuild failure can no longer discard the evidence | workflow file rewritten; the failure path now writes diagnostics and fails loudly |
| `nfl-desk-35a1feb2` | the committed pages were rebuilt from the desk's own generator (the sibling-desk inventory had moved on) | `python3 engine.py && python3 build_site.py && python3 verify.py` → **PASS (15 pages, 844 rows)**; two consecutive rebuilds change no bytes |

## 3. The front door

| Check | Command | Result |
|-------|---------|--------|
| Build | `python3 nfl-integration-3ddb3f07/build_hub.py` | 15 pages from 33 source files; 0 broken internal links |
| Gates | `python3 nfl-integration-3ddb3f07/verify_hub.py` | **13 passed, 0 failed** |
| Unit tests | `python3 -m unittest discover -s nfl-integration-3ddb3f07/tests` | **9 passed** (3 negative controls included) |
| Determinism | two consecutive builds | no byte changes |
| Provenance | every table row on every page | 751 rows: each has an official source link or an explicit unverified marker |
| Readiness table | `decision_readiness.csv` (78 rows) vs the landing page | exact match, no missing and no extra requirement |
| Lineage | sha256 of every source file vs the disk | identical |
| Claims | regex over every page + the leaderboard CSV | no certification claim; 0 of 7 families certified |

## 4. Repository-wide checks after the repairs

* Broken internal links: **0** across every published HTML file (the front door's own pages
  are checked by its own gate; the repository scan covers the other 500+ pages).
* Every desk's own verifier re-run: **31 verifiers, 30 PASS, 1 FAIL** — the failure is the
  `nfl-b34253a1` line-hash audit, which is regenerated as the last step of this session
  because this session changed files in its scope (`.github/workflows/`,
  `scripts/build.py`, `research/nfl-3ddb3f07/**`, `data/**`).
* `nba-commission`, which had been failing on the 127 broken links, now passes: **ALL
  CHECKS PASSED (6 groups, 0 failures)**.

## 5. Root site

* `python3 scripts/seed.py && python3 scripts/build.py` → 8 pages regenerated; the landing
  page now points at the front door and carries the review date 2026-11-19.
* `python3 -m unittest discover -s tests` → **95 tests OK**; `node --check assets/app.js`
  → OK.

## 6. What was deliberately not done

* No value was filled in where an official source is silent; the blanks stay blank and are
  flagged.
* No strategy was certified, no ROI or closing-line value was computed from an aggregator
  reference, and no historical leaderboard figure was promoted to a skill claim.
* The pre-registration chain was not "fixed" by recreating a commit with the old message:
  the broken chain is disclosed on the site instead (FLAG-V11).
* The three requirement registers were not merged into one count; the crosswalk has not
  been verified row by row.

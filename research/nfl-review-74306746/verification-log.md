# Verification log

**Run date:** 2026-11-19 UTC
**Evidence snapshot:** `2f02e1e7975ee61780b39e1ef9bc83591ccb55e2` plus the pushed scope-claim commit `239cebb0864d52791ddf8517dfd2db0093b58805`. The branch is `arena/74306746-own5`; `origin/main` advanced after this snapshot, and all later commits are explicitly outside the review scope.
**External access:** no official, club, operator, nflverse or other external webpage was fetched in this review. All results below are local code/data checks; source URLs remain historical references.

## Review-package build and checks

Final local run:

- `python3 nfl-review-74306746/build_site.py` — built 6 static pages.
- `python3 nfl-review-74306746/verify.py` — **passed**: 6 pages, 20 cited table rows, 10 source groups, 10 readiness rows, 8 questions, 7 suggestions and 8 flags.
- `python3 -m unittest discover -s nfl-review-74306746/tests -v` — **9 tests passed**.
- `git diff --check` — **passed** (no whitespace errors).

The review verifier reproduced, from local committed files only: 78 FanDuel-labelled engine rows and 13 hash-matching text summaries; 39 empty market-desk open and 39 empty close rows; 1/32 populated roster-sweep rows; 12 command origination rows against 13 Week 11 fixtures; 14 Week 10 Game Book URL fields; 44 starter and 12 inactive rows tied to JAX–TEN only; and an nflverse aggregator snap-count snapshot with 12,693 rows for 136 games / 32 clubs, REG Weeks 1–9 only. The latter's local provenance timestamp is 2026-11-12. It has no Week 10/11 rows and is not a direct per-game NFL Game Book transcription in this review. Archive and aggregator hashes were checked against the repository's local manifests, not against external servers.

The 14 Game Book URLs, JAX–TEN-only extractions, nflverse aggregate, and market desk's zero inactive/snap rows are kept as distinct source and namespace scopes. A passing local check does not confirm external source accuracy or current page content.

## Selected existing desk verifiers and tests

Reran the same read-only verifier/test pairs listed in `.github/workflows/nfl-review-74306746.yml` on 2026-11-19:

- `python3 nfl-command-desk/verify.py` — **50 passed, 0 failed**. `python3 -m unittest discover -s nfl-command-desk/tests -v` — **26 tests passed**.
- `python3 nfl-market-desk/verify.py` — **10 checks passed** (including its 13-page deterministic rebuild). `python3 -m unittest discover -s nfl-market-desk/tests -v` — **27 tests passed**.
- `python3 nfl-engine-39086ec8/verify.py` — **1,215 checks, 0 failed**. `python3 -m unittest discover -s nfl-engine-39086ec8/tests -v` — **68 tests passed**.
- `python3 nfl-desk-35fc3437/verify_desk.py` — **all checks passed**. `python3 -m unittest discover -s nfl-desk-35fc3437/tests -v` — **9 tests passed**.
- `python3 nfl-venue-390e13fd/verify.py` — **passed**. `python3 -m unittest discover -s nfl-venue-390e13fd/tests -v` — **12 tests passed**.
- `python3 nfl-desk-38430fe3/verify.py` — **passed**. `python3 -m unittest discover -s nfl-desk-38430fe3/tests -v` — **7 tests passed**.
- `python3 nfl-desk-6cbf25fa/verify.py` — **543 checks, 0 failures**. `python3 -m unittest discover -s nfl-desk-6cbf25fa/tests -v` — **11 tests passed**.

The market-desk, venue-desk, Week 10 injury-desk and Week 11 market/injury-desk test output included `ResourceWarning`s for unclosed file handles; all those tests passed. These are existing test warnings, and no files in those owner scopes were changed by this review.

## Other repository checks performed

- Compared the command and market requirements registers without merging their separate schemas.
- Recomputed all 13 engine archive SHA-256 values and checked them against the price CSV; these files are transcribed text summaries, not saved webpage/response bytes.
- Compared market-desk R-13 with the 32-team roster sweep and counted populated roster URL/count fields.
- Compared Week 11 fixture and origination sets across command, 35fc3437, market and venue registers; identified the Arizona-at-Kansas-City omission in the command desk's origination file.
- Compared local standings/correlation capture dates and kept date-skewed values separate rather than claiming a same-snapshot error.
- Earlier in this session, ran `python3 tools/decision_desk/build_all.py`. It reused committed parsed tables because `.work/official` HTML was absent; it did not fetch official pages. Its generated tracked audit files were restored.
- Earlier exploratory verifiers/tests were also rerun; tracked owner files were clean before this review package was written.

## Reproduction

From the repository root, use the build, verifier and unit-test commands above. The new package uses only the Python standard library. The scoped GitHub Actions workflow additionally reruns all seven owner-desk verifier/test pairs with full Git history available for the command desk's preregistration check. It does not write to the other desk namespaces and makes no external webpage requests.

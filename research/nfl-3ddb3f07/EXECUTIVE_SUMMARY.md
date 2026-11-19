# Executive summary — Own5 NFL front door (integration session 3ddb3f07, 2026-11-19)

This is the summary of the repository as it stands after the final integration pass. It
states only what the repository itself computes or what an official publisher published;
nothing here is inferred. Where a value could not be confirmed, it is blank and flagged.

## 1. What was delivered by this session

* **A front door for the site** (`nfl-integration-3ddb3f07/`), fifteen pages, built
  deterministically from the tables the other desks own. Nothing is copied: each table is
  read at build time and the file that was read is recorded with its sha256 on the
  verification page. Every table row carries an official source link or an explicit
  unverified marker — 751 rows, checked by a gate that fails the build otherwise.
* **The decision-readiness table on the landing page**: one row per requirement (78), each
  with the gate that blocks it, the number that would clear it, the current number and a
  link to the evidence file.
* **Repairs to the site that were broken and undocumented**: 127 broken links across three
  desks (including anchors whose `href` was a sentence), a stale root landing page, a
  scheduled check that had been red on `main`, and a daily capture job that destroyed the
  evidence it was supposed to keep.

## 2. What the repository knows today

| Area | State |
|------|-------|
| Requirements | 78 in the canonical register; the register's own status words are published as they stand |
| Markets originated | 39, in the order side → total → moneyline, with fair line, market line and difference in three separate columns |
| Verified prices | 0 — no operator price is admitted, so residual, closing-line value and real-price ROI are blank by policy |
| Results corpus | 145 games read from the official schedule pages, reconciled club by club against the official standings |
| Depth | 12 club depth charts parsed from the clubs' own published pages, with raw text and hash retained; the clubs that publish an image stay blank |
| Correlations | 5 published from official inputs, each with its n; 5 pairs withheld because they would need a non-official input |
| Strategies | 7 families, 0 certified; signal score and staking score are separate, and controls (random picks, favourites only) are graded on the same games |
| Gates | 12 gates plus 7 demotion rules; a strategy needs every gate, and a live strategy that loses its edge returns to paper on a stated trigger |
| Flagged | 34 items in the market desk's register plus 13 in the integration audit; nothing is silently corrected |

## 3. The three things that block a decision

1. **No admitted price source.** Until a permitted, timestamped operator price exists,
   market residual, closing-line value and ROI are undefined, and no strategy can be
   certified on a price-relative score. This is a decision, not a research gap: see
   suggestion SG-01 and question Q-01.
2. **Availability is a snapshot, not a series.** The injury report is captured with a clock
   time and a hash, and the delta between captures is what gets published — never the
   level. But a full Wednesday-to-kickoff series for every club is not retained yet, so a
   designation's *surprise* cannot be reconstructed for backtesting.
3. **One season.** Holdout and ablation studies need more history than the 2026 season
   alone can give.

## 4. What this session found and fixed (all reproducible)

| Defect | Where | Status |
|--------|-------|--------|
| 61 anchors whose `href` was prose (`href="n/a - deliberately omitted"`) | `nfl-desk-864d5668` | fixed in the desk's generator; a regression guard now fails on any non-path href |
| 8 pages linking with desk-root-relative paths; the nav pointed at a file that does not exist | `nfl-desk-e1d60f5d` | fixed in the desk's generator; the desk's own 241 checks pass |
| 1 repo-relative link that 404ed from its served location | `nfl-desk-ccc5caf2` | fixed |
| The published pre-registration hash was orphaned by a rebase and no longer exists | `nfl-command-desk` | the gate now proves what is still provable (the rule text is byte-identical to the freeze commit) and requires the broken chain to be disclosed (FLAG-V11) |
| The published capture summary was a hand-written string that could disagree with the ledger | `own5-hub` | the summary is derived from the ledger, and gate G8 fails the build if they disagree |
| A capture whose page no longer parses crashed the whole build | `own5-hub` | it is now recorded in the ledger as a failed capture — evidence, not a lost run |
| The daily capture job discarded the capture when the rebuild failed | `.github/workflows/own5-hub-capture.yml` | the immutable capture is committed first; the pages are rebuilt from it after |
| The desk's committed pages no longer matched its own deterministic build | `nfl-desk-35a1feb2` | rebuilt from its generator; its scheduled check was red on `main` and is now reproducible |
| The root landing page was stamped "Reviewed 2026-11-02" and linked no desk newer than 2026-11-17 | `scripts/build.py` → `index.html` | the generator now points at the front door and stamps the review date |

## 5. Verification performed

* The front door's own gates: 13 checks, 0 failures (pages, provenance on every row, the
  readiness table's row count against the source CSV, lineage hashes, determinism, no
  certification claim, and the repository-wide link check).
* 9 unit tests, including negative controls: a row stripped of its source, a link pointed
  at a missing file and a planted certification claim are each caught.
* Every desk's own verifier re-run from the merged tree: **32 verifiers, 32 pass**. The
  repository-wide line-hash audit is regenerated after every merge that touches an audited
  file (a known fragility, recorded below), and it passes against the merged tree.
* Repository-wide link check: 0 broken internal links across every published HTML file.

## 6. Flagged, not blocking

* **The pre-registration chain is broken** (FLAG-V11). The original registration commit and
  its republish were both orphaned by a rebase. The rule text has not changed, and that is
  provable; but "the rules were frozen before the results were seen" can no longer be
  demonstrated from the repository. No strategy may be certified on the basis of a
  pre-registration hash, and the site says so.
* **The repository-wide line-hash audit is a merge-time tripwire.** Every merge that
  changes a file in the audit's scope requires the audit to be regenerated, or the B34
  desk's check fails. This has been worked around repeatedly by other sessions; it is
  recorded here as a structural cost of the current design.
* **Two other requirement registers exist** (80 rows in the Own5 hub, 73 in the command
  desk). They are published separately. A combined completion count is deliberately not
  published: the crosswalk has not been verified row by row.

## 7. Where to look

* Front door: `nfl-integration-3ddb3f07/index.html`
* Verification record: `research/nfl-3ddb3f07/VERIFICATION.md`
* This summary: `research/nfl-3ddb3f07/EXECUTIVE_SUMMARY.md`

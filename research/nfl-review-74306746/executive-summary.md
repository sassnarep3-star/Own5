# Executive summary

## Decision posture

**Continue paper-only.** No strategy is certified in the reviewed leaderboards. This review does not establish an executable price feed, a current-week injury state, a complete starter/inactive/snap record, or a legal basis for collection and display. Leave unsupported price, lineup and joint-outcome values blank and visibly flagged; do not infer them from other fields.

## What is in the repository

- Several separate NFL workstreams contain line-origination, official-source-linked schedule/result and injury captures, pre-registration, control baselines, scoring, gates, questions, suggestions and flagged registers. The desks are not one unified data layer: the command desk has a 73-row requirements register, while the market desk has 78 rows with a different schema and scope. Preserve each register as its owner's record; do not combine completion percentages without a row-level crosswalk.
- Side, total and moneyline originations are represented in the reviewed market desk and 35fc3437 desk. Fair values, market values and differences have distinct fields; some market columns are intentionally blank. Coverage is not identical across desk views: the command desk's Week 11 origination file has 12 game rows while its fixture file lists 13 games, and the other inspected Week 11 origination registers have 13.
- The repository contains official-linked historical results and game-book references. The command desk's 150-row corpus and the market desk's 145-row capture cover different read windows; their counts should not be compared as if they were the same snapshot. The local verifiers validate their declared arithmetic/reconciliation rules, not the current contents of the external pages.
- A Week 10 NFL injury capture contains 347 rows in separate namespaces. A requested Week 11 injury URL was recorded by prior desks as serving a page headed Week 10 on 2026-11-18. This review did not re-fetch it, so it makes no claim about what the URL serves on 2026-11-19.
- A Week 10 manifest links an official Game Book for each of 14 games, but the inspected starter/inactive extraction covers JAX–TEN only (44 starter rows and 12 inactive rows). Separately, an nflverse (third-party aggregator) 2026 snap-count file contains 12,693 rows for 136 games / 32 clubs, regular-season weeks 1–9 only, with a recorded 2026-11-12 provenance timestamp; it has no Week 10/11 rows and is not a direct per-game NFL Game Book transcription in this review. The market desk separately reports zero inactive and snap-count rows within its own scope. None of these facts establishes full-slate Week 10/11 availability or snap coverage.
- A FanDuel register contains 78 rows labelled `VERIFIED` (13 Week 10 games × three markets × two outcomes), all labelled `close`, with the same recorded capture time. Thirteen committed text summaries match their recorded SHA-256 values. That proves the committed text is hash-stable; it does not prove the text is a raw operator response or independently confirm the source, timestamp, jurisdiction, terms or close-time semantics. A separate market-desk store has blank operator open/close entries and states no operator quote was available. The disagreement is unresolved.
- The market desk's roster readiness row says 32/32 rosters were captured, but its cited 32-team roster sweep has only one populated roster count and URL; 31 are blank. This is a repository consistency discrepancy, not a newly checked NFL roster fact.
- Official-standings-derived correlations appear in multiple snapshots. The input dates and values differ; this may reflect different capture windows. Do not compare or combine them until the same 32-team snapshot and exact field definitions are reconciled.

## Checks run

The command, market, engine, 35fc3437, venue, 38430fe3 and 6cbf25fa desk verifiers/tests passed in the current session. Their pass results are **repository checks only**: they establish internal consistency against committed data and code, not that cited pages were fetched again or that every capture is complete. `nfl-market-desk` tests emitted `ResourceWarning`s for unclosed files despite passing.

## Highest-priority actions

1. Reconcile the operator-price records, timestamps and source evidence between the engine and market desk; until then, keep price-dependent calculations blocked.
2. Correct or substantiate the roster-sweep readiness statement in its owning scope.
3. Reconcile the missing Arizona-at-Kansas-City origination row in the command desk with its 13-game fixture list.
4. Keep current-week injury and actual starter / inactive / snap claims blank until the official page identity and game-level evidence are captured for the exact target games.
5. Normalize result and correlation comparisons to one dated official input snapshot before presenting a cross-desk aggregate.
6. Retain paper-only status until preregistration, proper-score/uncertainty/multiplicity gates, price provenance, joint-evidence and operator-rule gates, and the required owner/legal decisions are all clear.

## Limitations

No official webpage was fetched in this review. The external URLs below are historical source references from repository registers. Evidence is pinned to commit `2f02e1e7975ee61780b39e1ef9bc83591ccb55e2`; later commits are outside this report and can change the broader repository state. No source contents were independently checked, no new NFL fact was transcribed, and no existing desk file or status was changed. The repository's NFL Terms interpretation is an existing desk's note, not a legal opinion. This review does not recommend a wager.

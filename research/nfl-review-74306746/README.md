# NFL cross-desk evidence review — session 74306746

**Review snapshot:** 2026-11-19 UTC
**Input snapshot:** the read-only repository state at base commit `2f02e1e7975ee61780b39e1ef9bc83591ccb55e2`, plus the session's pushed claim commit `239cebb0864d52791ddf8517dfd2db0093b58805`.
**Scope:** an additive review of the NFL line-originator desks in the pinned evidence snapshot. Existing desk data, dashboards, scripts and workflows remain read-only and canonical within their claimed scopes. Commits after `2f02e1e7975ee61780b39e1ef9bc83591ccb55e2` are outside this review.

## Decision

Keep every strategy in PAPER / shadow status. Do not treat the repository's FanDuel snapshot labels as independently verified, do not compute or publish a price residual / CLV / realized ROI from the conflicting price registers, and do not treat the captured Week 10 injury report as current Week 11 availability. Resolve the owner-scoped findings in `flagged.json` before any price-dependent, personnel-dependent or joint-outcome feature is promoted.

The review found reproducible repository checks and source-linked historical captures, but **did not fetch or re-verify any official webpage**. Official links in the review are audit references to the source URLs recorded by prior desks; they are not represented as current confirmations. This report is an internal repository review, not legal advice or betting advice.

## Availability scope boundary

The Week 10 results register has **14 Game Book PDF links**, but the separate starter/inactive tables contain **44 starter rows and 12 inactive rows for JAX–TEN only**. A different namespace holds an nflverse third-party snap-count file with 12,693 rows for 136 games / 32 clubs through regular-season Week 9 (provenance dated 2026-11-12); it is not a direct official per-game transcription and contains no Week 10/11 rows. The market desk's own `R-25` count of zero inactive/snap rows remains scoped to that desk. Do not conflate these three records or infer complete Week 10/11 coverage.

## Deliverables

- `executive-summary.md` — short decision summary and boundaries.
- `verification-log.md` — exact local commands and results.
- `source-coverage.json` — source categories, recorded capture scope, repository evidence and explicit freshness limits.
- `readiness.json` — compact blocking-gate / clearing-number summary; the command desk's full register remains linked as canonical.
- `questions.json`, `suggestions.json`, `flagged.json` — answered/unanswered questions, review-only options, and owner-scoped issues.
- `../nfl-review-74306746/` — deterministic static Pages dashboard generated from these review registers.

## Rebuild and checks

From the repository root:

```sh
python3 nfl-review-74306746/build_site.py
python3 nfl-review-74306746/verify.py
python3 -m unittest discover -s nfl-review-74306746/tests -v
```

The verifier checks only this review's generated site and the cross-desk claims it reproduces from the read-only registers. It validates external-link schemes/hostnames but never contacts external websites. CI also reruns the selected existing desk verifiers and tests; it does not modify their files.

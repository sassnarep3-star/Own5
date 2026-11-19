# Flagged register — session 067f2314

Mirror of `nfl-desk-067f2314/data/flagged.csv` (33 flags), published on the desk's
Flagged for Review page. Flags do not block the site; they block the decisions they attach
to until resolved from an official source.

## High severity

- **F06-02** Joint-evidence gate blocks parlay/prop ranking — no validated joint probabilities.
- **F06-03** No market prices anywhere in this desk — market/difference/residual columns blank
  by policy pending the price-data decision.
- **F06-04** Replacement depth blank — no verified official depth-chart source read this session.
- **F06-08** Removal-of-luck panel blocked — needs settled bets and a control baseline (n = 0).
- **F06-10** Price-data policy undecided — user-owned decision blocks gate G02 and all
  ROI/CLV/backtest publication.
- **F06-16** Inactive lists and snap counts not captured.
- **F06-17** Depth-chart register not built (known parsing failures: Texans image, Packers
  jersey prefixes remain unresolved).
- **F06-22** Deficiency matrix not built (requires a verified depth source).

## Medium severity

- **F06-01** Leaderboard performance cells blank (no prices, no settled bets).
- **F06-05** Availability graph and snap-based depth not built.
- **F06-06** Injury series has a single capture — the "surprise, never a level" delta
  requirement is structurally blocked until a series exists.
- **F06-07** 32-team roster/IR sweep not run (only 26 playing teams on the report).
- **F06-09** 136-game backtest corpus not assembled.
- **F06-13** Opponent-adjusted ratings not built.
- **F06-14** Injury/depth ablations not run.
- **F06-15** Availability snapshot automation not scheduled.
- **F06-18** Roster turnover not versioned.
- **F06-19** Public/private data split not implemented.
- **F06-20** Announced-starter evidence not captured.
- **F06-21** "Questionable" not yet calibrated empirically.
- **F06-26** Reserve list not captured.
- **F06-27** Historical injury archive not built.
- **F06-29** Season split (train/validation/holdout) not applied.
- **F06-30** Pre-existing CI failure on main ("NFL Decision Desk — fetch & verify") owned by
  other sessions — logged for owner review, not edited here.
- **F06-31** False-negative smoke checks in 10 workflows (`curl | grep -q` under pipefail) —
  logged as cross-session request X51-14, not edited here.

## Low severity

- **F06-11** Venues transcribed from the schedule page; game-centre cross-check pending.
- **F06-12** Dated schedule announcement not fetched.
- **F06-23** Lions designations (Joseph, Mays, Reed) blank in the early-week report —
  consistent with the pre-Week-10 finding; designations typically arrive later in the week.
- **F06-24** Weather overlay not built.
- **F06-25** Single model estimator published (the "publish every total twice" requirement
  needs a second pre-registered estimator).
- **F06-28** Onside-kick regime priors not applied.
- **F06-33** Small-sample model constants (HFA −5.64, sigma 15.29, n = 14) — frozen at spec
  v1, supersedable only by a pre-registered change on a larger official sample.

## Resolved

- **F06-32** Stale claim rows of session 35fc3437 closed as done with the merge record
  completed by this session (PR #127 was already merged; only the log rows were stale).

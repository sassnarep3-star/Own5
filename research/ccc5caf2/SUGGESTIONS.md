# Suggestions register — OWN5 NFL Line Originator

**Session:** `ccc5caf2` · **Date:** 2026-11-18 · **Desk:** `nfl-desk-ccc5caf2/suggestions.html`

Recommendations for improving the site and the decision process. Each suggestion carries a decision state and a review test so someone can review and choose the best path before anything is implemented. Nothing is implemented unless explicitly accepted and logged.

## Review workflow

1. Read each suggestion's problem, impact, effort and confidence.
2. Check the decision state (Recommended now / Pilot / Defer).
3. Apply the review test to decide whether to accept, reject or defer.
4. Record the decision in a decision log (one line per accepted suggestion: date, evidence, owner, revisit date).
5. Only implement accepted suggestions; rejected ones are archived here with rationale.

## Top suggestions (Recommended now)

| ID | Suggestion | Impact | Effort | Confidence | Decision state | Review test |
|---|---|---|---|---|---|---|
| S01 | Archive a timestamped operator price snapshot every week | High | Medium | High | Recommended now | Fall back to manual capture of 5 games/week if blocked |
| S02 | Ship a sign-convention regression test with every backtest | High | Low | High | Recommended now | Update fixture and record change if convention differs |
| S03 | Pre-register the variant count before looking at results | High | Low | High | Recommended now | New variant starts a new pre-registration round |
| S04 | Publish a market-efficiency scorecard per signal | High | Medium | High | Recommended now | Promote to full gate evaluation if residual edge with verified closing price |
| S05 | Use lineup deficiency as a pricing input, not a bet trigger | Medium | Low | High | Recommended now | Revisit if future season shows residual edge with verified prices |
| S08 | Score the leaderboard on CLV and calibration, never win rate | High | Medium | High | Recommended now | If CLV cannot be captured (S01 fails), board stays provisional |
| S09 | Dual-source data layer with automatic disagreement alerts | High | Low | High | Recommended now | Fail closed (blank + flag) if official page parsing fails |
| S11 | Price correlated legs with an empirical copula; refuse independent pricing | High | Medium | High | Recommended now | Document if operator's SGP price already reflects correlation |
| S13 | Separate OFFICIAL and AGGREGATOR tiers in every table, mechanically | High | Low | High | Recommended now | Label AGGREGATOR where no official publisher exists |
| S16 | Publish the reward structure only after the jurisdiction question is closed | Medium | Low | High | Recommended now | Close Q04/Q05 first; then publish reward terms |

## Pilot / Defer

- S06 offensive-line continuity (Pilot), S07 practice-status probabilities (Pilot), S14 cap/retire strategies (Pilot)
- S10 EPA opponent-adjusted efficiency (Defer), S15 weather/venue adjustment (Defer)

Full table: `nfl-desk-ccc5caf2/suggestions.html`.

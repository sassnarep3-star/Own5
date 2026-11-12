# Questions that must be answered before a decision

Four questions are **blocking**: they cannot be resolved by more analysis of public data.

## Blocking

1. **Q01 — Which price is the benchmark?** Our line at post, the operator's current price, or the
   close? Every CLV and edge statement depends on it. *Close it by:* capturing a timestamped
   operator snapshot twice weekly (S01).
2. **Q02 — Are the aggregator lines closing lines, and from which operator?** *Close it by:*
   publisher provenance or replacement with an archived operator feed.
3. **Q03 — What bankroll, staking rule and maximum drawdown apply?** *Owner decision.*
4. **Q04 — Are rewards cash, points, or nothing?** *Owner decision plus jurisdiction review (Q05).*
5. **Q05 — Which jurisdiction and operator rules govern the bets?** *Owner states the jurisdiction;
   then the applicable house rules are re-read.*
6. **Q06 — Can historical prop lines be obtained?** Without them no prop strategy has a break-even
   price. *Only a commercial archive or forward collection can answer this.*
7. **Q18 — Is there budget for a paid odds feed?** One feed closes Q01, Q02 and Q06 together.

## Partially answered

- **Q07** What defines a starter? Snap share is used (measurable), depth charts are not published.
- **Q08** How many points is a missing player worth? −0.039 points per percentage point of relative
  deficiency on margin; per-position values are not yet estimated.
- **Q09 / Q10** Should practice status and Questionable players carry probability weights? Judgment
  weights are used and disclosed; fitted activation rates are the next step (S07).
- **Q14** Is home-field advantage really zero at a neutral site? Currently assumed zero.

## Answered

- **Q11** Sample size: 300 bets to list, full power analysis (≈2,241 bets) to certify.
- **Q12** Error budget: Bonferroni 0.05/k with k published; exploratory labels allowed at 0.10 with
  disclosure.
- **Q13** Model update cadence: weekly refit on prior weeks only; freeze after the Wednesday report.
- **Q15** Postseason: excluded from ratings; treated as a separate sample.
- **Q16** Source disagreement: fail closed and flag (S09), never choose silently.
- **Q17** Versioning: every fetch pinned with SHA-256 and UTC timestamp in the repository.

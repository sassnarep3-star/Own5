# Executive summary — NFL decision brief

**Review date:** 2026-11-19 UTC. Official web pages were re-read in this session; the fetch interface did not expose a reliable clock time or raw response bytes/hashes.

## Decision

Keep the NFL project in **paper / shadow mode**, beginning with singles. Do not publish market residuals from an uncleared data source, use unverified availability as a model feature, rank parlays/player-prop combinations, stake live capital, or issue cash rewards until the relevant source, validation, and governance gates are cleared. This is a decision-readiness recommendation, not a finding that a particular strategy is profitable or unprofitable.

## Important verified changes and limits

- The official NFL [Week 11 injury report](https://www.nfl.com/injuries/league/2026/reg11) now identifies itself as the 2026 Week 11 report. The previous repository source log says the same URL served Week 10 on 2026-11-18. The old read is a historical capture, not today's report. The current report is not a retained, hashed, multi-day pre-kickoff archive and does not by itself establish actual starters or playing time.
- The official NFL [Week 11 schedule](https://www.nfl.com/schedules/2026/by-week/week-11) and Colts–Texans [Game Center](https://www.nfl.com/games/colts-at-texans-2026-reg-11) publish the fixture facts. The [Houston Texans stadium page](https://www.houstontexans.com/stadium/) says Reliant Stadium returned as the name in August 2026 after the NRG Stadium naming period. This verifies that fixture/context point only; it does not verify all venues or prior seasons.
- A public [DraftKings NFL markets page](https://sportsbook.draftkings.com/leagues/football/nfl) is visible, but display is not evidence of rights to retain, use in backtests, or republish. No operator prices were copied into this review. Keep the line, difference, CLV, and ROI fields blank until a permitted, timestamped opening/closing data source and policy are established.
- Official injury labels are not a substitute for the expected-starter, announced-starter, inactive, actual-starter and snap-participation evidence chain. Keep unknown values blank; do not infer depth from jersey number, salary, experience, or roster order.
- Combinations need direct joint-outcome evidence and current operator/jurisdiction-specific settlement rules. Marginal probabilities alone are not a valid joint estimate.

## Repository irregularity found

`python3 nfl-command-desk/verify.py` returned **47 PASS / 3 FAIL** on this checkout. All three failures are V11 checks for the claimed registration SHA `e7282e35dbf9afb0c1b364a152b9431dc71b64af`: the object is absent from this checkout's Git object database, so it cannot be verified as the strategy-registration ancestor. This is a repository issue, not an NFL-source fact. The pre-registration claim should not be relied on until that hash reference is repaired and verification passes.

## Best next path

1. Repair and independently verify the registration hash and strategy definitions.
2. Decide and document market-data permissions, jurisdiction, retention and open/close semantics before price-based backtests.
3. Begin scheduled immutable pre-kickoff capture of official injury/roster/inactive information, then join official starters and snap counts; publish coverage and conflicts.
4. Freeze a singles shadow baseline with stored probabilities and inputs, chronological train/validation/holdout, random/favorite controls, proper scores, uncertainty and a prospective demotion rule.
5. Add parlays/SGPs/prop combos only after direct joint-probability validation and the relevant operator settlement rules are versioned.
6. Enable rewards only after prospective qualification and funding, eligibility, dispute and governance rules are established.

The [decision brief](index.html) contains the prioritized question/gate register, source links, proposed options and two-sided conditions that would change each recommendation. The existing [NFL Command Desk](../nfl-command-desk/index.html) remains the broader requirements ledger; this addition does not alter it.

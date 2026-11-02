# Removing Luck: Skill-vs-Variance Separation (T5)

Betting outcomes are dominated by variance over any horizon a human cares about. A 52% coin weighted in your favor still loses frequently over hundreds of flips. "Removing luck from the equation" means grading strategies on metrics whose expectation is driven by skill and whose noise shrinks fast.

## 1. Grade on de-vigged CLV, not results

- The closing line at a sharp, high-limit book is the market's best estimate of true probability; beating it systematically is the accepted definition of betting skill. (INDUSTRY convention: https://www.pinnacleoddsdropper.com/blog/closing-line-value ; https://pikkit.com/blog/how-to-track-closing-line-value-clv-in-sports-betting)
- CLV identifies skill in roughly **200–500 bets**; ROI needs **2,000–5,000** and win rate **1,000–3,000** because they are heavily luck-contaminated. (INDUSTRY: https://www.sportsbettingoddscalculator.com/guides/closing-line-value — thresholds flagged as convention, not law.)
- Always **de-vig** the close first (normalize both sides' implied probabilities to 100%) so the book's margin isn't mistaken for your edge. (https://www.pinnacleoddsdropper.com/blog/closing-line-value)

**Leaderboard consequence:** the primary score is mean de-vigged CLV in basis points, not profit.

## 2. Statistical tests applied to every track record

| Test | What it kills | Rule |
|---|---|---|
| Bootstrap CI on mean CLV | Small-sample flukes | 95% CI must exclude 0 (Gate G3) |
| Binomial test of beat-close rate | "Hot streak" narratives | Share of bets beating the de-vigged close tested vs. 50% |
| Monte Carlo permutation null | Pattern-mining luck | Metric must beat 95th percentile of shuffled-outcome null (Gate G5) |
| Deflated Sharpe Ratio / PBO (CSCV) | Selection bias across many tried variants | PBO < 10%; selection-aware t ≳ 3 (Gate G4). PRIMARY: Bailey & López de Prado, https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf |

## 3. Shrinkage: never take a raw average at face value

Leaderboard scores use empirical-Bayes shrinkage: a bettor's displayed skill = sample mean CLV pulled toward 0 in proportion to noise (few bets ⇒ heavy pull). This makes it mathematically unattractive to climb the board with a short lucky run — the anti-luck mechanism is in the scoring rule itself, not in moderator judgment.

## 4. Standardize stakes before comparing anyone

Flat-stake (1-unit) performance is computed alongside actual staking so that one lucky max-bet cannot dominate a record. Staking itself is constrained to fractional Kelly (Gate G8): f* = (bp − q)/b, with half- or quarter-Kelly mandated because edge estimates are uncertain and correlated positions share risk. (PRIMARY: Kelly 1956, *Bell System Technical Journal*; https://oddscipher.com/the-codex/kelly/ ; https://marketmath.io/blog/kelly-criterion-guide)

## 5. Separate "the effect is real" from "the market misses it"

A real basketball effect (e.g., B2B fatigue — 44% win rate vs 50% null, arXiv:2606.27957) is **not** an edge if the closing line already prices it. Every strategy is therefore evaluated on *residual* predictive power **versus the closing line**, never versus raw outcomes. This single design choice removes the largest class of false "systems."

## 6. What would falsify a strategy

Each pre-registered spec must state its own kill criteria (e.g., "mean CLV < 0 over any rolling 300-bet window ⇒ retire"). Strategies without falsification criteria are not eligible — unfalsifiable systems are astrology.

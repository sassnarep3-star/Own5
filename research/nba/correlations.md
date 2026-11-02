# Correlation Framework for Parlays & Player-Prop Combos (T4)

## Why correlation decides parlay value

A parlay priced as independent legs pays `∏(1/pᵢ)`-style odds. If legs are **positively correlated**, the true joint probability is higher than the independence product — the parlay is underpriced unless the book applies a sufficient "correlation tax." If legs are **negatively correlated**, the joint probability is *lower* than the product — the parlay is structurally bad even at full odds. Books adjust SGP payouts for correlation, but imperfectly; the edge, if any, lives in the gap between the true joint distribution and the book's adjustment. (INDUSTRY concept: https://nba-prop-bets.com/articles/nba-same/)

Reference arithmetic (exact, verifiable): five independent legs at 50% each ⇒ joint probability 0.5⁵ = **3.125%**.

## Direction taxonomy (qualitative — directions sourced, numeric values deliberately blank)

**Verification policy:** No official or primary source publishes numeric NBA prop-correlation coefficients. Per the project rule — *never infer or fill in values* — the `r` column is left **blank** and the whole table is mirrored on the Flagged for Review page until the coefficients are computed from official box-score data with `analysis/prop_correlations.py`.

| # | Leg A | Leg B | Direction | Strength (qualitative, per source) | Mechanism | r (Pearson) | Source (direction/strength) |
|---|---|---|---|---|---|---|---|
| C1 | Star player points OVER | Same team moneyline | Positive | Strong | Big scoring night → good offensive night → win | *(blank — unverified)* | https://nba-prop-bets.com/articles/nba-same/ |
| C2 | Star points OVER | Star assists OVER (same player, high-usage ball-handler) | Positive | High | Offense runs through him: scores and creates | *(blank — unverified)* | https://oddsindex.com/guides/nba-same-game-parlay-tips |
| C3 | Star points OVER | Star rebounds OVER (bigs / rebounding wings) | Positive | Moderate | Paint scorers are positioned for boards | *(blank — unverified)* | https://oddsindex.com/guides/nba-same-game-parlay-tips |
| C4 | Assists OVER | Rebounds OVER (same player) | Positive | Low–moderate | Weakest of the three pairings | *(blank — unverified)* | https://oddsindex.com/guides/nba-same-game-parlay-tips |
| C5 | Player threes made OVER | Same player points OVER | Positive | High (volume 3pt shooters) | Threes are points | *(blank — unverified)* | https://oddsindex.com/guides/nba-same-game-parlay-tips |
| C6 | PG assists OVER | Teammate shooter points OVER | Positive | Moderate | Assists convert to teammate buckets | *(blank — unverified)* | https://nba-prop-bets.com/articles/nba-same/ |
| C7 | Game total OVER | Team threes made OVER | Positive | Moderate | High-scoring games carry 3pt volume | *(blank — unverified)* | https://oddsindex.com/guides/nba-same-game-parlay-tips |
| C8 | Projected pace UP | Multiple counting-stat OVERs | Positive | Moderate | More possessions → more of everything | *(blank — unverified)* | https://oddsindex.com/guides/nba-same-game-parlay-tips |
| C9 | Game total UNDER | Any player points OVER | **Negative** | — (prohibited pairing, Gate G7) | Low-scoring games starve everyone | *(blank — unverified)* | https://nba-prop-bets.com/articles/nba-same/ |
| C10 | Center post-touches points OVER | Perimeter teammate points OVER | **Negative** (context-dependent) | — | Usage competition for possessions | *(blank — unverified)* | https://nba-prop-bets.com/articles/nba-same/ ; https://www.edgebetting.ai/betting-education/player-props |

## Combo-stat caution (PRA / PR / PA / RA)

A combined line (e.g., PRA 41.5) is **not** three independent overs: component stats share drivers (minutes, pace, role, game script), so you cannot sum component over-probabilities or assume independence. (INDUSTRY: https://www.edgebetting.ai/betting-education/player-props)

## How the numeric values get filled in (and verified)

1. Pull per-game player box scores from the **official NBA statistics feed** (stats.nba.com endpoints via the open-source `nba_api` client) for ≥ 2 full seasons.
2. Run `analysis/prop_correlations.py` — computes, per player (min. 40 games) and league-wide: Pearson and Spearman r for PTS↔AST, PTS↔REB, AST↔REB, 3PM↔PTS, player PTS↔team PTS, player PTS↔win.
3. Values enter this table **only** with: sample size, season range, and the official data source link. Anything else stays blank.
4. Parlay pricing then uses the empirical joint distribution (resampling actual game lines of a player's stat vector preserves the full dependence structure, not just pairwise r).

**Status: UNVERIFIED / PENDING DATA — this entire table's numeric column is intentionally empty.** The sandbox used to build this repo has no network route to stats.nba.com; filling values from memory or from unofficial aggregators would violate the project's verification rules.

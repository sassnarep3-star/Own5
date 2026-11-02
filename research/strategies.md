# Signal-Generation Strategy Catalog (T2)

**Status convention:** Every strategy below is a **candidate**. No strategy may be represented as profitable, "verified," or leaderboard-eligible until it passes **all** validation gates in [`validation-gates.md`](validation-gates.md). No performance numbers are claimed anywhere in this repo because no live betting record exists yet.

**Source tiers used throughout this repo:**
- **OFFICIAL** — NBA league sources (NBA.com / official.nba.com).
- **PRIMARY** — peer-reviewed or preprint research (PubMed/DOI, arXiv, author-hosted papers).
- **INDUSTRY** — betting-industry educational material. Used only for concepts/conventions, never as proof of an edge. Rows resting solely on INDUSTRY sources are listed on the Flagged for Review page.

---

## S1 — Rest & schedule-spot signal (single bets: spread / ML / totals)

**Hypothesis:** Teams on the second night of a back-to-back (B2B) underperform expectation; rest differential between opponents is predictive of outcome and efficiency beyond what the market fully prices.

**Evidence:**
- Esteves et al. (2021), *Eur J Sport Sci* 21(1):26–35 — likelihood of winning increases significantly from B2B to one day of rest; shooting-efficiency stats discriminate congestion states. PRIMARY. https://pubmed.ncbi.nlm.nih.gov/32172667/ (DOI: 10.1080/17461391.2020.1736179)
- arXiv:2606.27957 (2026), six seasons of play-by-play (2019/20–2024/25) — B2B games show a **44% win rate vs. ~50% null expectation**; road-trip fatigue only appears past the 5th consecutive away game. PRIMARY. https://arxiv.org/html/2606.27957v1

**Build:** Features = rest days each side, B2B flag, 3-games-in-4-nights flag, consecutive-road-game count, travel/time zones. Target = margin vs. closing spread (not raw W/L), so the test is "does the market underprice rest?" rather than "does rest matter?"

**Known risk:** Rest is the most publicized situational factor; modern closing lines likely price most of it. Gate G3 (CLV) is the decisive test.

## S2 — Injury-report latency signal (singles + props)

**Hypothesis:** Edges exist in the minutes after official injury-report changes (upgrades/downgrades/late scratches), before props and sides fully reprice — especially derivative markets (player props) that reprice slower than sides.

**Evidence (timing windows that define the scan schedule):**
- NBA Official Injury Report, 2025-26 season — teams must designate participation status **by 5 p.m. local time the day before a game**; for the **second game of a back-to-back, by 1 p.m. local time on game day**; plus a **game-day report between 11 a.m.–1 p.m. local** (8–10 a.m. for tip-offs 5 p.m. or earlier); reports update continually. OFFICIAL. https://official.nba.com/nba-injury-report-2025-26-season/
- December 2025 league memo reportedly moves public report updates to every 15 minutes (media-reported; not yet confirmed on an official league page → **flagged as unverified**). INDUSTRY/MEDIA. https://sports.yahoo.com/articles/nba-takes-stand-injury-reporting-231429192.html

**Build:** Poll the official report at its known update windows; map each listed player to a usage-redistribution model (see S6); bet only markets that have not yet moved. Log timestamp of report change vs. timestamp of bet vs. line at bet vs. closing line.

## S3 — Home/away, travel & altitude context signal (singles)

**Hypothesis:** Home-court advantage (HCA) is real but shrinking and heterogeneous (altitude venues, specific travel patterns); markets using stale league-average HCA misprice specific games.

**Evidence:**
- arXiv:2606.27957 — home advantage, travel and rest effects quantified vs. randomized nulls across 2019/20–2024/25. PRIMARY. https://arxiv.org/html/2606.27957v1
- Pollard & Gómez (2021, as cited in IJRSS study of NBA Finals 2006–2026): home advantage across major North American sports declined from ~64% (1980s) to ~57% (2010s); NBA Finals home win% 61.4% overall, 56.7% in the last 10 seasons. PRIMARY (via published study). https://www.ijrss.org/index.php/ijrss/article/download/958/572/1494
- Third-party dataset (swishdunk.com): home win% 57.5% in 1996-97 → 55.4% in 2025-26; decade blocks 60.4% → 59.4% → 56.2%; seasonal min 54.3% (2023-24). **INDUSTRY — not an official NBA publication; numbers flagged as unverified against official sources.** https://swishdunk.com/nba-evolution-30-years-stats

**Build:** Estimate per-season HCA with shrinkage; venue fixed effects (e.g., altitude); interact with travel features from S1.

## S4 — Streak/persistence signal (singles)

**Hypothesis:** Short-horizon team persistence exists — P(win | won previous game) = **54.5%** vs. 50% memoryless null (PRIMARY: arXiv:2606.27957). The open question is whether the market *under- or over-prices* streaks (public money chases streaks, which can make streak-fading profitable even though streaks are real).

**Build:** Condition on previous-game outcome, location sequence, and margin; evaluate strictly against the closing line (G3), since raw persistence that the market already prices is worthless.

## S5 — Pace-interaction prop signal (totals + prop overs)

**Hypothesis:** Projected game pace (possessions) is the single biggest shared driver of counting-stat props; when a pace mismatch is underweighted by prop lines, correlated overs/unders across the same game are mispriced.

**Evidence:** Pace as a shared driver of points/rebounds/assists/threes overs is standard in industry SGP analysis. INDUSTRY (concept only). https://oddsindex.com/guides/nba-same-game-parlay-tips ; https://www.edgebetting.ai/betting-education/player-props

**Build:** Possession model per matchup; propagate pace delta into per-player counting-stat distributions; compare to posted lines.

## S6 — Usage-vacuum prop signal (player props)

**Hypothesis:** When a high-usage player is OUT (per the official injury report, S2), teammates' usage, minutes, and counting stats rise in predictable, player-specific patterns that prop lines only partially price — especially for second-order beneficiaries.

**Evidence:** Concept documented in industry prop-education material. INDUSTRY (concept only). https://www.edgebetting.ai/betting-education/player-props

**Build:** "With/without" splits from official box scores (minimum-sample gates apply); redistribute vacated usage/minutes; bet only when model-vs-line gap exceeds threshold after vig.

## S7 — Line-origination / CLV-chasing signal (meta-strategy, all bet types)

**Hypothesis:** The core craft of "originating your own lines": price every market independently *before* seeing the market; bet only where your de-vigged price differs from the available price by more than the vig, and grade yourself on de-vigged closing line value (CLV), not W/L.

**Evidence (CLV as the skill metric):**
- CLV definition and formula CLV% = (Closing odds / Bet odds) − 1, de-vigging required, Pinnacle close as benchmark. INDUSTRY (convention). https://www.pinnacleoddsdropper.com/blog/closing-line-value
- CLV detects skill in ~200–500 bets vs. thousands for ROI; +1–2% sustained CLV considered strong. INDUSTRY (convention; exact thresholds flagged). https://www.sportsbettingoddscalculator.com/guides/closing-line-value ; https://pikkit.com/blog/how-to-track-closing-line-value-clv-in-sports-betting
- Market inefficiencies in NBA betting demonstrated with a non-parametric win-probability model. PRIMARY. arXiv:1910.08858 — https://arxiv.org/abs/1910.08858

## S8 — Correlated same-game-parlay (SGP) construction (parlays / prop combos)

**Hypothesis:** Books price SGP legs with an imperfect correlation adjustment ("correlation tax"). When true correlation between legs exceeds the book's adjustment, the parlay price is too generous; when legs are negatively correlated, the parlay is structurally −EV. Edge = modeling the joint distribution better than the book.

**Evidence (correlation taxonomy — directions, industry concept):**
- Positive: star points over + team ML / team total over; PG assists over + shooter points over; threes made + points; pace up + multiple overs. Negative: game total under + player points over. INDUSTRY (directions only; **no numeric correlation values are published by an official or primary source — see `correlations.md`**). https://nba-prop-bets.com/articles/nba-same/ ; https://oddsindex.com/guides/nba-same-game-parlay-tips
- Leg-count discipline: five independent 50% legs ≈ 3.125% joint probability before correlation adjustments. Arithmetic (verifiable: 0.5^5). https://nba-prop-bets.com/articles/nba-same/

**Build:** Estimate the player-level joint distribution (copula or empirical resampling from official box scores — see `analysis/prop_correlations.py`), price the parlay, compare to offered price, and only bet positive-gap combos. Never combine negatively correlated legs.

---

## What is deliberately NOT in this catalog

- No "system" based on W/L streak ROI tables from untraceable screenshots.
- No claimed win rates or ROI — none exist yet; all strategies must earn eligibility through the gates.
- No tout content. All INDUSTRY sources are used for definitions/conventions only.

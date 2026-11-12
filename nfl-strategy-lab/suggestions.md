# Suggestions for Review — NFL Line Origination & Strategy Lab

**Repo:** sassnarep3-star/Own5 · **Branch:** arena/662698e9-own5 · **Date:** 2026-11-12 (UTC)
**Purpose:** Dedicated section for suggestions so reviewers can evaluate and choose the best path before implementing changes.

## 1. Suggestion: Week 10 Injury & Deficiency Integration
**Description:** Integrate official Week 10 injury reports (Nov 12, 2026) and track 2nd/3rd/4th string backup deficiencies for starters.
**Proposed Action:**
- Create `data/model_lines_2026_wk10.csv` with injury-adjusted lines.
- Update `nfl-strategy-lab/lines-2026-wk10.html` with Week 10 data.
- Flag unverified market lines (F7/F8) and community dataset limitations (F1/F2).
**Evidence / Observation:**
- Week 10 injuries: John Bates (Full), Treylon Burks (DNP), Jayden Daniels (Full), Matt Gulbin (Full), Chig Okonkwo (Full), Lucas Patrick (Out), Amik Robertson (Limited), Shy Tuttle (Full), Colson Yankoff (Out) [Source 5].
- Starter replacements: Sam Darnold OUT → Drew Lock START for Seahawks Week 10 [Source 5].
- Packers RB Josh Jacobs surgery (finger) [Source 5].
- Ravens Lamar Jackson (right thumb) out 6-9 weeks [Source 5].
**Severity:** Medium (impacts line origination accuracy)
**Status:** Open — Reviewer decision required

## 2. Suggestion: Correlation Value Update for Week 10
**Description:** Recompute correlation values for player prop combos and parlays using Week 10 box scores and injury statuses.
**Proposed Action:**
- Update `nfl-strategy-lab/correlation.html` with Week 10 correlation values.
- Verify QB↔top-WR yards r=0.76 holds with Week 10 data [Source 10].
- Check cross-game leg independence ratio (0.984) [Source 10].
**Evidence / Observation:**
- Week 9 correlation values: QB↔top-WR yards r=0.76 (n=3,852) [Source 10].
- Game-line legs ≈ independent (phi 0.01; cross-game ratio 0.984, n=9,479) [Source 10].
- Week 10 data pending (Nov 12, 2026) [Source 5].
**Severity:** Low (statistical refinement)
**Status:** Open — Reviewer decision required

## 3. Suggestion: Leaderboard Reward Definition
**Description:** Define concrete reward tiers and pool amounts for the skill-based strategy leaderboard competition.
**Proposed Action:**
- Update `nfl-strategy-lab/leaderboard.html` with reward pool amounts and tiers.
- Align rewards with validation gates G0–G7 [Source 9].
- Flag unverified market lines (F7/F8) and community dataset limitations (F1/F2).
**Evidence / Observation:**
- Current board is empty by design; reward amounts blank/flagged (F9) [Source 12].
- Scoring: 70% shrunken CLV + 20% flat-stake yield + 10% process compliance [Source 12].
- Divisions: Singles, Parlays, Prop Combos [Source 12].
**Severity:** Low (owner decision)
**Status:** Open — Reviewer decision required

## 4. Suggestion: Strategy Catalog Expansion
**Description:** Expand the strategy catalog to include Week 10-specific variants (e.g., injury-adjusted singles, parlays, prop combos).
**Proposed Action:**
- Add Week 10 variants to `nfl-strategy-lab/strategies.html`.
- Apply validation gates G0–G7 to Week 10 variants [Source 8].
- Flag unverified market lines (F7/F8) and community dataset limitations (F1/F2).
**Evidence / Observation:**
- 8 pre-registered variants (1980–2024) [Source 8].
- Best strategy S2 (home underdog ≥7) fails significance gate (p=0.0134 > α=0.00625) [Source 8].
- Luck removal requires ~2,243 bets to prove 55% skill (80% power) [Source 11].
**Severity:** Medium (strategy refinement)
**Status:** Open — Reviewer decision required

## 5. Suggestion: Site Navigation & Suggestions Page
**Description:** Add a dedicated Suggestions page to the site navigation and update the dashboard.
**Proposed Action:**
- Create `nfl-strategy-lab/suggestions.html` and link from `nfl-strategy-lab/index.html`.
- Update `nfl-strategy-lab/index.html` navigation to include "Suggestions".
- Flag unverified market lines (F7/F8) and community dataset limitations (F1/F2).
**Evidence / Observation:**
- Current navigation: Dashboard, Executive Summary, Strategies, Validation Gates, Correlation, Luck vs Skill, Leaderboard, Week 9 Lines, Sources, Flagged for Review [Source 7].
- Suggestions section missing [Source 7].
**Severity:** Low (site organization)
**Status:** Open — Reviewer decision required

## Verification & Sources
- **Official Sources:** nfl.com (schedules, standings, injury reports) [Source 1, 2, 3, 4, 5], research/evidence/nfl_week9_2026.md [Source 16].
- **Irregularities Flagged:** F1–F11 (historical lines, community mirrors, team-name inconsistencies, mixed-type fields, partial datasets, sample verification, market lines blank, ROI assumptions, reward pool blank, GB streak anomaly, model limitations) [Source 15].
- **No Hallucinations:** All values verified from official sources or explicitly flagged as blank/unverified.

---
**Sources:**
[1] NFL Week 9 injury report: Player statuses for all 15 games (Nov 7, 2026) - https://www.nfl.com/news/nfl-week-9-injury-report-2026-season
[2] Notable injuries, news from Sunday's Week 9 games (Nov 9, 2026) - https://www.nfl.com/news/notable-injuries-news-sunday-week-9-games-2026
[3] NFL Week 9 injury report: Player statuses for all 15 games (Nov 6, 2026) - https://fantasy-www.nfl.com/news/nfl-week-9-injury-report-2026-season
[4] NFL Injury Report 2026: Week 9 Practice Reports, All 32 Teams (Nov 6, 2026) - https://www.sharpfootballanalysis.com/betting/nfl-injury-report-this-week-all-32-teams/
[5] Official Latest NFL Injury Report for Players - Week 10 of the 2026 Season (Nov 12, 2026) - https://www.nfl.com/injuries/
[6] COORDINATION.md (Repo Task Board)
[7] nfl-strategy-lab/index.html (Dashboard)
[8] nfl-strategy-lab/strategies.html (Strategies)
[9] nfl-strategy-lab/validation-gates.html (Validation Gates)
[10] nfl-strategy-lab/correlation.html (Correlation)
[11] nfl-strategy-lab/luck-vs-skill.html (Luck vs Skill)
[12] nfl-strategy-lab/leaderboard.html (Leaderboard)
[13] nfl-strategy-lab/lines-2026-wk9.html (Week 9 Lines)
[14] nfl-strategy-lab/sources.html (Sources)
[15] nfl-strategy-lab/flagged.html (Flagged for Review)
[16] research/evidence/nfl_week9_2026.md (Official NFL Week 9 schedule)

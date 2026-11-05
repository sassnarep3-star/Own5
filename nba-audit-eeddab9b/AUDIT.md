# Independent NBA deliverable audit

**Session:** `eeddab9b` · **Reviewed:** 2026-11-05 UTC · **Scope:** additive audit only. No existing NBA data, strategies, site pages, or shared root navigation were changed.

## Executive conclusion

The repository already contains an NBA Signal Lab with an executive summary, source-linked data tables, model-derived lines, correlation analysis, singles/parlays/player-prop-combo strategies, validation gates, a leaderboard design, and a Flagged for Review page. Its strategy states remain pending, with zero certified entries; market prices and prize pool are blank rather than invented. Local build and test suites passed.

This audit identifies material caveats that should travel with any use of the research: the latest slate is historical as of this review date; a small two-player lag-1 sample does not establish cross-game independence; pooled estimates and intervals do not account for player clustering; source identifiers conflict between the evidence log and verification page; and derived model-line rows do not consistently link directly to all season-specific statistical inputs.

**Primary-source limitation:** NBA URLs are supplied below and throughout the project for manual review. In this session, NBA pages could not be freshly retrieved from the shell environment, so this audit does not represent a new line-by-line re-fetch against those pages. The prior session records a page-fetcher transcription performed on 2026-11-03. Local checksum tests are not substitutes for current-source verification.

## Findings

| ID | Status | Evidence | Action |
|---|---|---|---|
| A01 — stale slate | Needs review | Published line slate is 2026-11-04 with inputs labeled 2026-11-03; review date is 2026-11-05. See the [NBA official Nov. 4 game calendar](https://www.nba.com/games?date=2026-11-04) and [published model lines](../nba-signal-lab/model-lines.html). | Label as historical and refresh from dated official inputs before any current-slate use. |
| A02 — independence claim too strong | Needs review | The [correlations page](../nba-signal-lab/correlations.html) reports lag-1 points r = −0.041 (63 pairs, CI [−0.285, 0.209]) for Luka Dončić and 0.056 (60 pairs, CI [−0.200, 0.306]) for Anthony Edwards. These broad intervals include nontrivial dependencies. The page and README also say the evidence supports / holds independence, stronger than these data warrant. See official [Dončić](https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26) and [Edwards](https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26) logs. | Treat G05 as unverified. A two-player lag-1 probe cannot establish independence among team-game parlay legs or returns. Measure joint outcomes on a broader, pre-registered sample. |
| A03 — pooled correlation uncertainty | Needs review | 125 rows are pooled from only two players. The page gives per-player point estimates but pooled Fisher-z intervals do not account for within-player clustering, serial dependence, or player heterogeneity. The sample size and source cohort are described in [verification](../nba-signal-lab/verification.html) and [Flagged for Review](../nba-signal-lab/flagged.html). Official source: [NBA 2025-26 leaders](https://www.nba.com/stats/leaders?Season=2025-26). | Retain as exploratory; do not use pooled intervals/hit rates as reliable pricing inputs. Expand players and use cluster-/time-aware uncertainty plus out-of-sample validation. |
| A04 — source identifier collision | Needs review | `E7` in `nba-signal-lab/data/raw/evidence_log.md` means SGA box scores; `E7` on `nba-signal-lab/verification.html` means 2025-26 team traditional statistics. Subsequent E8–E10 entries also differ. See official [SGA box scores](https://www.nba.com/stats/player/1628983/boxscores?Season=2025-26) and [2025-26 team stats](https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season). | Create one canonical stable source-ID map; until then, cite direct URLs, not the conflicting IDs. |
| A05 — incomplete provenance on derived lines | Needs review | Model-line row links point to generic team schedule pages; team CSV URLs do not consistently include season parameters. The derivation uses season-specific team statistics, so current links may not preserve the exact input context. See [2026-27 team stats](https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season), [2025-26 team stats](https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season), and [model lines](../nba-signal-lab/model-lines.html). | Link each derived output to its actual season-qualified inputs and dated schedule/game row; retain dated retrieval evidence. |

These are nonblocking publication/review findings. Existing user-facing NBA flags remain on the [NBA Signal Lab Flagged for Review page](../nba-signal-lab/flagged.html). This audit's separate [Flagged for Review page](flagged.html) publishes A01–A05. The audit overview is [here](index.html).

### Repository presentation note (not a league-statistic finding)

Top-level Jekyll metadata still describes Own5 as an NFL line originator, and the README's opening inventory is stale even though later sections document the NBA Signal Lab. See the repository's [`_config.yml`](https://github.com/sassnarep3-star/Own5/blob/main/_config.yml), [README](https://github.com/sassnarep3-star/Own5/blob/main/README.md), and [NBA dashboard](../nba-signal-lab/index.html). If the repo is intended to be NBA-first, update the top-level description and discovery/navigation without removing the NFL pages.

## Checks run

| Check | Result |
|---|---|
| `python3 nba-signal-lab/build.py` | Pass; generated 11 pages. |
| `python3 nba-signal-lab/compute.py` | Pass; 16 checks, 0 failures; 6 slate model lines and 7 correlation pairs / 5 prop-threshold rows. |
| `python3 -m unittest discover -s nba-signal-lab -p 'test*.py' -v` | Pass, 13/13. Three tests emitted nonfatal unclosed-file `ResourceWarning`s. |
| `python3 -m unittest discover -s tests -v` | Pass, 91/91. |
| `python3 nba-own-lines/check.py` | Pass, 20 checks. |
| `python3 nba-desk/check.py` | Pass, 14 pages, 506 rows, 15 flags. |
| `python3 nba-2026-lab/check.py`; `nba-origin-lab/test_site.py`; `nba-audit-e9f83ff4/test_audit.py` | Pass. |
| `python3 scripts/check_site.py` | Not run to completion: this checker requires `dist/`, which was absent (`dist/ does not exist; run scripts/build_site.py first`). This is a command-order/precondition issue, not a failed test assertion. |

The source links documented in the [NBA Signal Lab verification page](../nba-signal-lab/verification.html) and [evidence log](../nba-signal-lab/data/raw/evidence_log.md) provide manual review starting points. Values remain subject to the freshness and lineage findings above.

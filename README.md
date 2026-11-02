# Own5 — NFL research desk

Evidence-first NFL line research: independent fair lines, single-bet/parlay/player-prop strategy families, correlation diagnostics, fail-closed validation gates and an eligibility-first leaderboard.

**Dashboard:** https://sassnarep3-star.github.io/Own5/

**Status:** frozen 2026-11-02 research snapshot. No strategy is currently validated for wagering. Publication verification is recorded in [COORDINATION.md](COORDINATION.md).

## What is inside

- **15 independent Week 9 research lines** derived from official standings and schedule inputs.
- **6 registered strategies** covering singles, cross-game parlays, same-game QB–WR combos and player props.
- **11 validation gates**; unknown evidence blocks qualification.
- **17 paired 2024 Burrow–Chase games** with Pearson/Spearman/phi, empirical joint frequency and bootstrap intervals.
- **78 verified fact rows** linked to official sources, plus a 17-source register and frozen evidence excerpts.
- **13 review flags** for missing markets, current props, settlement variability, source irregularities and model limitations.
- **0 qualified strategies / 0 rewards**: no invented performance ranking.

## Evidence policy

Official facts, operator statements and derived estimates are separate. Every published table row links to an official source. Unsupported values remain blank (`null`) and appear on **Flagged for Review**. A source beside a derived estimate identifies its inputs; it does not mean the NFL endorses the estimate.

The current line originator is a transparent, unvalidated shrunken-PF/PA + independent-Poisson baseline. It disables home advantage and leaves injury/weather/starter adjustments blank. No sportsbook prices, current prop quotes or out-of-sample wager ledger were verified.

## Run locally

Requires Python 3.11+ and Node 20+. No third-party Python packages or npm dependencies are needed.

```bash
npm ci
npm test          # 29 unit tests
npm run build     # evidence snapshot -> derived data -> static site -> link/provenance audit
npm start         # serves dist/ on 0.0.0.0:8000
```

## Repository map

| Path | Purpose |
|---|---|
| `research/evidence/` | Frozen official rows and quotations |
| `research/build_snapshot.py` | Typed snapshot extraction and reconciliation |
| `nfl_model/` | Ratings, score distribution, correlation, settlement, contracts, gates, audit |
| `scripts/` | Data build, static-site integrity check, preview server |
| `site/` | Static dashboard generator and assets |
| `data/` | Source register, verified facts, derived outputs, review flags |
| `docs/` | Executive summary, methodology, source audit, requirements, verification |
| `tests/` | Standard-library unit tests |
| `.github/workflows/pages.yml` | Test/build/determinism/Pages publication pipeline |
| `COORDINATION.md` | Shared claims, scopes, verification log and publication record |

## Key documents

- [Executive summary](docs/EXECUTIVE_SUMMARY.md)
- [Methodology and validation protocol](docs/METHODOLOGY.md)
- [Source audit](docs/SOURCE_AUDIT.md)
- [Requirements traceability](docs/REQUIREMENTS.md)
- [Integration verification](docs/VERIFICATION_REPORT.md)

## Responsible scope

Research software only. No wagers are placed. Luck cannot be eliminated from finite samples; the protocol controls leakage, settlement errors, multiple testing and dependence while preserving uncertainty. Do not use nonpublic information. Restricted persons must follow applicable NFL/organizational policies.

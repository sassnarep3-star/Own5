# Session 26d4cafb — NFL Decision Desk research dossier

**Snapshot: 2026-11-12 UTC · NFL 2026 regular season · Week 10**

Every document in this folder is generated directly from
`nfl-desk-26d4cafb/data/` by `nfl-desk-26d4cafb/export_research.py`. No value is
retyped by hand, so the markdown cannot drift from the underlying data.

Reproduce with:

```
cd nfl-desk-26d4cafb
python3 engine.py            # rebuild every CSV/JSON from the official inputs
python3 build.py             # render the dashboard site
python3 export_research.py   # regenerate this dossier
python3 verify.py            # 25 line-by-line checks
python3 -m unittest discover -s nfl-desk-26d4cafb/tests
```

## Documents

| File | Contents |
|---|---|
| [executive-summary.md](executive-summary.md) | Headline numbers, the six findings that should change decisions, requirements coverage, and what is still missing. |
| [01-repo-audit.md](01-repo-audit.md) | Line-by-line repository audit (`RA-01..RA-12`) with the official source used to verify each finding. |
| [02-suggestions.md](02-suggestions.md) | Improvement proposals (`SUG-01..SUG-12`) and the four selectable implementation paths (`PATH-A..PATH-D`). **Nothing here is implemented.** |
| [03-pre-decision.md](03-pre-decision.md) | Pre-decision questions with known information, answers reached and gaps (`Q-01..Q-14`), plus discovery actions (`DISC-01..DISC-10`). |
| [04-methodology.md](04-methodology.md) | The declared model, hyper-parameters, home-field advantage estimate, shrinkage sensitivity and the zero-look-ahead protocol. |
| [05-injuries-depth.md](05-injuries-depth.md) | The 46-row Offense/Defense starter-to-backup register (`INJ-01..INJ-46`) with active-string tiers. |
| [06-lines.md](06-lines.md) | The 14 originated Week 10 lines, plus out-of-sample grading of the repository's existing originators (raw and matched sample). |
| [07-signals-strategies.md](07-signals-strategies.md) | Signals (`SIG-01..SIG-14`), strategies (`STR-01..STR-10`), the gated leaderboard and per-strategy gate results. |
| [08-correlations.md](08-correlations.md) | Team-level and player-prop Pearson correlations, prop-combo joint probabilities, lift and Frechet-Hoeffding bounds, QB checksums. |
| [09-luck-vs-skill.md](09-luck-vs-skill.md) | Per-pick nulls, exact Poisson-binomial tests, Holm-Bonferroni, Deflated Sharpe Ratio, the selectivity trend test and parlays. |
| [10-flagged.md](10-flagged.md) | Everything that could not be confirmed from an official source (`FLG-01..FLG-16`), with links. None of it blocks publication. |
| [11-sources.md](11-sources.md) | The official-source register (`SRC-01..SRC-51`) behind every number on this site. |

## Zero-hallucination policy

1. Every factual value is read from an official NFL page (`nfl.com`,
   `operations.nfl.com`) or an official NFL club page, fetched on 2026-11-12.
2. A value that cannot be confirmed from an official source is stored as an empty
   string and is cross-referenced to a `FLG-` id. It renders as a blank cell, never
   as an inferred number.
3. Fields prefixed `model_` are explicit model priors computed by `engine.py`. They
   are never presented as official NFL statistics.

## Headline results

- **136** completed official games; **16** of them were missing from the repository's
  2026-11-02-frozen boards and were re-fetched from NFL.com.
- **32/32** teams reconcile exactly (W, L, T, PF, PA) to
  [nfl.com/standings](https://www.nfl.com/standings/) — **0 mismatches**.
- 2026 home-field advantage on 130 non-neutral games is **-0.054 points**
  (95% CI [-2.34, +2.23], p = 0.96) — statistically indistinguishable from zero,
  against the **+2.0** the repository's existing boards assume.
- **2 of 10** strategies clear all ten fail-closed validation gates.
- **16** items remain open on the Flagged for Review page, none blocking.

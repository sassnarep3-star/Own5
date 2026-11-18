# Verification record — OWN5 NFL Line Originator

**Session:** `ccc5caf2` · **Date:** 2026-11-18 · **Desk:** `nfl-desk-ccc5caf2/verification.html`

Hard rule: if a value cannot be confirmed from an official/primary source, it is left blank and flagged. Never inferred. No hallucinations.

## Verification checks performed this session

| Check | Source fetched | Result | Verdict |
|---|---|---|---|
| 2026 REG standings (32 clubs) | https://www.nfl.com/standings/league/2026/REG | All 32 clubs; W-L-T, PF, PA reproduced | Verified |
| Week 11 schedule (13 games) | https://www.nfl.com/schedules/2026/by-week/week-11 | 13 games, Nov 19–23, times, networks, venues | Verified |
| Week 10 injury report (sampled) | https://www.nfl.com/injuries/ | Lions Joseph/Mays/Reed Out; St. Brown Questionable — match nfl.com | Verified (sample) |
| Fair lines Week 11 | Computed from S-03 standings (PF/PA model) | Model output, not an odds source | Model only (market blank, F01/F02) |
| QB↔WR correlation | nflverse stats_player (AGGREGATOR) | r = 0.50, n = 1,255 (recomputed) | AGGREGATOR tier |
| Operator closing-line history | No official/operator page publishes it | Not available | Blocked (F01/F02) |
| Machine-readable official depth chart | Not published by the league | Not available | Blocked (F16) |

## Reproductions (prior-session claims re-checked)

| Claim | Prior value | Recomputed | Verdict |
|---|---|---|---|
| Home underdogs cover 52.6% | 0.526 | 0.497 | Does not reproduce (F08) |
| Home dogs +7 cover 56.4% (n=793) | 0.564 / n=793 | 0.540 / n=730 | Does not reproduce (F08) |
| QB↔WR correlation r = 0.76 (n=3,852) | 0.76 / n=3,852 | 0.50 / n=1,255 | Does not reproduce (F09) |
| Break-even bettor 110+ wins in 200 = 20.8% | 0.208 | 0.251 (exact binomial) | Does not reproduce (F10) |
| Favourites cover 48.1% (n=10,424) | 0.481 | 0.485 | Agrees |
| Overs 49.1% (n=10,729) | 0.491 | 0.491 | Agrees |

Non-reproducing prior figures are flagged (F08, F09, F10) and left for human review; recomputed values are used on this desk.

## Site integrity

- All internal links across pages resolve (no broken links).
- Every table row carries a source link or is an intentional flagged blank.
- No value is inferred from unofficial sources.

Sources fetched 2026-11-18 from nfl.com (OFFICIAL). Aggregator sources pinned by SHA-256 (nflverse, spreadspoke).

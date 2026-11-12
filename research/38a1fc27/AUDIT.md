# Repository audit — 2026-11-12

Scope: every previously published numeric claim in this repository that a reader might rely on,
plus link integrity and per-row provenance. The full machine-readable output is
`data/decision-desk/claim_checks.csv`, `standings_crosscheck.csv`, `provenance_audit.csv` and
`cross_scope_lines.csv`.

## 1. Cross-source agreement (new)

- **Standings:** 32 clubs' W-L-T and PF/PA parsed from nfl.com reproduce **exactly** from the
  nflverse game log. This is the strongest available check that both sources are sound.
- **Injury report:** 276 official rows match the mirror on team, player, position, practice status
  and game status. Zero disagreements.

## 2. Claims that do not reproduce

| Claim | Prior | Recomputed | Likely cause |
|---|---|---|---|
| Home underdogs cover ATS | 52.6% | 49.72% (n = 3,626) | different underdog identification or push handling; not documented |
| Home dogs +7 or more | 56.37% (n = 793) | 53.97% (n = 730) | same; the sample difference (63 bets) points at favourite mapping |
| QB↔WR1 correlation | 0.76 (n = 3,852) | 0.50 (n = 1,255) | different dataset (play-by-play through 2020) and WR1 definition |
| 110+ wins in 200 bets at break-even | 20.8% | 25.13% | prior derivation undocumented; exact binomial used here |

These are **published, not silently corrected**. The earlier pages remain live; the new numbers are
shown next to them so a human can adjudicate.

## 3. Claims that reproduce

Favourite ATS 48.1% → 48.49%; overs 49.1% → 49.08%; favourite SU 65.63% → 66.14% (minor);
2,243 bets → 2,241; parlay break-even 27.47% → 27.44%; independence of ATS/total legs phi ≈ 0.01 →
0.006.

## 4. Internal links

246 HTML pages and 4,182 internal links scanned: **0 broken**.

## 5. Provenance

19 published CSV tables scanned for per-row source links: all sourced. Derived tables link to the
script that produced them and to the pinned inputs.

## 6. Cross-scope consistency

`nfl-strategy-lab` and `line-lab` both cover Week 9. Their boards agree on the schedule; they publish
different objects (one a model line, the other a market snapshot). No contradictory claim was found
between them that is not already covered by F01 (market provenance).

## 7. Audit conclusion

The repository's *infrastructure* claims (tests, links, build determinism) hold. Several
*statistical* claims do not reproduce, and the two most consequential ones — home-dog cover rates and
the QB/WR correlation — are used elsewhere in the project. They are flagged for a human decision
rather than overwritten.

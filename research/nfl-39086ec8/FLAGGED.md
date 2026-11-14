# Flagged for review — unresolved evidence and decisions

All unresolved items are intentionally visible. “Blank” means no confirmed source value was
available; it never means zero. The page version is `nfl-engine-39086ec8/flagged.html`; the
machine-readable detailed records are `data/repo_audit.csv`, `data/questions.csv`, and
`data/price_coverage.csv`.

## Data gaps

| Item | Current published state | Evidence / next step |
|---|---|---|
| Opening prices | Blank; 0 Week 10 opening snapshots | Capture at market open going forward; no backfill. See [FanDuel event market](https://sportsbook.fanduel.com/football/nfl/new-england-patriots-@-detroit-lions-35605986). |
| WAS@NYG price | `UNPRICED` | The official [Week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10) shows it kicked off before capture. |
| Player prop prices | Blank / `UNPRICED` | FanDuel page renders prop names but no lines or prices in readable text. |
| Source jurisdiction | `US-UNSPECIFIED` | FanDuel public page does not state the governing state. Confirm jurisdiction and applicable operator rules before settling historical prices. |
| Full injury feed | 4 clubs transcribed; chunks 3–7 unread | Parse all official [NFL injury report](https://www.nfl.com/injuries/league/2026/reg10) rows. |
| Depth chart coverage | Four clubs read; NE defense and 28 clubs missing | Obtain direct official club charts. Existing sources include [Detroit](https://www.detroitlions.com/team/depth-chart), [New England](https://www.patriots.com/team/depth-chart), [New York Giants](https://www.giants.com/team/depth-chart), [Washington](https://www.commanders.com/team/depth-chart). Patriots explicitly labels its chart unofficial. |
| Closing-line value | Not computed | Requires captures at both a defined open and close, plus valid operator jurisdiction/settlement semantics. |
| Strategy rewards | Not implemented | Q04: decide whether rewards are points, cash, or none; any cash/incentive path needs eligibility, legal, tax, and responsible-gambling review. No incentive was invented. |

## Repository audit flags

| ID | Finding | Status | Source / detail |
|---|---|---|---|
| A8 | Root stat hard-codes validated strategies `00/08` | REVIEW | See root dashboard and `repo_audit.csv`; number is not generated from the current validation register. |
| B2 | Alias join can drop ARI/LAR without canonicalisation | IRREGULAR | Official [NFL standings](https://www.nfl.com/standings/) labels Arizona and Los Angeles; repo uses AZ/LA in one feed. Fixed in this desk's `canon()`; legacy rows remain flagged. |
| B6 | Rest vs margin correlation is driven by bye games | IRREGULAR | Official [NFL schedules](https://www.nfl.com/schedules/2026/by-week/week-10) identify bye weeks; excluding those records changes r from −0.4257 to +0.0387, p=0.72, n=89. |
| B7 | C-03 cited standings for a quantity derived from schedule + results | IRREGULAR | See source and calculation notes in `repo_audit.csv`. |
| B10 | Prior Week 10 own-line table omitted WAS@NYG | IRREGULAR | Official [Week 10 schedule](https://www.nfl.com/schedules/2026/by-week/week-10); this desk now has 14 rows and marks one unpriced. |
| B11 | Prior desks said no official game price was available | IRREGULAR | 13 public FanDuel event pages exposed readable Game Lines; [example](https://sportsbook.fanduel.com/football/nfl/new-england-patriots-@-detroit-lions-35605986). |
| C2 | Prior correlation C-02 does not reproduce from stated inputs | REVIEW | See `repo_audit.csv`; do not use as a verified result. |
| C3 | Prior correlation C-01 does not reproduce from stated inputs | REVIEW | See `repo_audit.csv`; do not use as a verified result. |
| C5 | Prior quote capture was date-only; CAR@NO moved −2.5 to −1.5 between desks | IRREGULAR | Date-only timestamps cannot establish capture order or closing price. |
| C6 | Alleged spread sign error | NOT CHECKED | Withdrawn by C7: same-row moneyline and spread signs agree. |
| D2 | Inherited deficiency metric is 0 on 698/705 slots | IRREGULAR | It measures occurrence, not chart depth. See this desk's `depth_replacement_slots.csv`. |

None of these flags blocks merge; they do block any claim of a proven wagering edge.

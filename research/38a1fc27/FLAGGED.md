# Flagged for review

Nothing here blocks publication. Everything here blocks a **claim**.

| ID | Item | Severity | What was found | What was done |
|---|---|---|---|---|
| F01 | Market line provenance and timestamp | blocks | All market values come from nflverse `games.csv`; operator and snapshot time unknown | Published as AGGREGATOR; G4/G8 marked failed; S01 proposed |
| F02 | No official closing-line history | blocks | No official source publishes timestamped closes | CLV not computed; no strategy certified |
| F03 | No official player-prop line history | blocks | Prop legs evaluated at median splits and by correlation | Economic evaluation withheld |
| F04 | Incomplete game statuses | review | 276 rows but only 6 game statuses on the Thursday snapshot | Practice weights applied, labelled provisional |
| F05 | Depth strings inferred | review | No machine-readable official depth chart | Snap-share method published |
| F06 | Six clubs report no injuries | note | Page lists 26 clubs; others show "no injuries reported" | Shown as zero, not missing |
| F07 | LA vs LAR club code | note | nflverse uses LA, teams.csv uses LAR | Alias applied in the audit |
| F08 | Prior home-underdog claims | review | 52.6% vs 49.7%; 56.4%/793 vs 54.0%/730 | Prior figures flagged |
| F09 | Prior QB↔WR correlation | review | 0.76 vs 0.50 on 2024–2026 data | Both published |
| F10 | Prior 20.8% luck figure | review | Exact binomial gives 25.1% | Exact value published |
| F11 | Sign-convention error (this session) | note | Wrong spread sign produced a false 57.4% edge | Corrected to 51.4%; test proposed (S02) |
| F12 | Single aggregator dependency | review | One mirror supplies snap counts, stats, injuries, lines | Dual-source assertions proposed (S09) |
| F13 | Week 10 market lines unverified | review | No operator page snapshot captured | Labelled AGGREGATOR |
| F14 | Availability weights are judgement | review | 1.0/0.75/0.5 and 0.5/0.25/0.0 are assumptions | Listed in methodology; S07 proposed |
| F15 | Small 2026 calibration sample | review | 136 of 950 games; per-season slopes −0.035 to −0.131 | Per-season results published |
| F16 | No official depth-chart feed | review | Club pages are inconsistent | Inference documented |
| F17 | Neutral-site assumption | note | Munich game treated as zero HFA | Published in the line table |
| F18 | Mirror freshness | note | 276/276 match today, but the mirror can lag | Timestamp published; weekly re-run |

# Questions, information, answers, unknowns and discovery steps

These are the questions that must be answered before the desk can make a decision it is willing to
publish. Each entry states what is known, what is missing, what the answer is today, and the
concrete step that would close the gap.

| ID | Question | Why it blocks a decision | Information we have | Information we do not have | Answer today | Unknown | Discovery step |
|---|---|---|---|---|---|---|---|
| Q-01 | What are the real market spreads, totals and moneylines for these games? | Without a price there is no edge, no ROI, no CLV, no break-even test | NFL.com publishes no prices; `nfl.com/betting/` returns 404; operator pages (DraftKings, FanDuel, BetMGM) are geolocation-gated from this environment | Any primary operator or exchange price feed | No price source is reachable | Whether a licensed feed can be obtained and stored with timestamps | D-01 |
| Q-02 | Which price would a strategy actually be bet into, and at what juice and limit? | Break-even hit rate depends on the offered price, not on the model | The repo's older desks assume a flat -110 (`nfl-desk-864d5668/data/leaderboard.csv`) or use a third-party ESPN/DraftKings scrape (`nfl-desk-26d4cafb/data/oos_week9.csv`) | The actual offered price of a named book for these games | Flat -110 is an assumption, not a fact | Real juice and limits per market | D-01 |
| Q-03 | Is the model's probability calibration good enough to bet? | Calibration is the skill measure that survives without a price | Walk-forward n = 73: Brier 0.2291 vs 0.2443 base rate, log loss 0.6480 vs 0.6818, slope 0.869, winner hit rate 60.3% | A larger out-of-sample sample; a calibration that holds on later weeks | Marginally better than base rate on a small sample | Whether the edge survives with n > 200 | D-02 |
| Q-04 | Does replacement depth move the line? | Determines whether S5 is worth running at all | 347 official injury rows, 32 official depth charts, per-player replacement tier | Official historical injury reports for Weeks 1-9 (nfl.com publishes only the current week) | Not answerable yet | Whether a depth adjustment has any measurable value | D-04 |
| Q-05 | How do the 61 injury rows with no depth-chart entry resolve? | Missing depth tiers weaken the depth tracker and the deficiency counts | Club depth charts for 31 clubs, 16 Houston rows blocked by the image-only chart | Official confirmation of those players' chart position | Flagged, left blank | Which of the 61 are true chart absences versus chart omissions | D-05 |
| Q-06 | Are the Chiefs' and Titans' official injury blocks complete? | Two clubs' absence counts may be under-reported | Both blocks captured from the official page, with the truncation and the two-segment assembly recorded | A clean second capture | Flagged as irregular | Exact size of the gaps | D-06 |
| Q-07 | Can player-level official data be extracted for props? | S6 is entirely blocked on this | NFL Game Center exposes an official Game Book PDF per game | A parsed player table for the 2026 season | Not answerable yet | Whether the PDFs parse cleanly at scale | D-03 |
| Q-08 | What is the true home-field effect in 2026? | HFA = 2.0 is the only non-official number in the engine | 137 official final scores; the repo's older desk estimates HFA empirically (`nfl-desk-864d5668/data/hfa.csv`) | A defensible 2026 estimate with a confidence interval | 2.0 points, flagged as an assumption | The value that maximises out-of-sample accuracy | D-07 |
| Q-09 | Which advanced team statistics matter? | Advanced stats would materially improve the model | NFL.com team-stat pages expose first downs, third-down rate, yards, sacks and turnover ratio | Values that can be paired unambiguously with their labels | Not answerable from the team-stat tiles | Whether the Game Book PDF or the club stats pages give a clean per-game table | D-03, D-08 |
| Q-10 | How should this desk be merged with the existing NFL desks? | Six overlapping NFL desks exist with duplicated and drifting inputs | The audit in `research/08-repo-audit.md` | A decision on the canonical desk and the shared navigation | Not decided here | Whether the repo keeps one NFL desk or a family with one shared data layer | D-09 |

## Discovery steps

| ID | Step | Unblocks | Effort |
|---|---|---|---|
| D-01 | Establish a licensed primary price feed (for example a regulated state lottery or an operator API) that stores the raw price with a capture timestamp per market, and re-run the append-only snapshot store | Q-01, Q-02, S4, criteria 9 and 10 of the gate | Commercial |
| D-02 | Re-run the pipeline weekly and keep the walk-forward ledger so the calibration sample grows past n = 200 | Q-03 | Low, automated |
| D-03 | Parse the official NFL Game Book PDFs into a per-game player table and publish the parser plus a verification script | Q-07, Q-09, S6 | Medium |
| D-04 | Freeze each future week's official injury report into a dated archive inside this desk so a depth backtest becomes possible | Q-04, S5 | Low, automated |
| D-05 | Manually review the Houston Texans depth-chart image and transcribe it by hand into `depth_raw.py` | Q-05, 16 blank Texans rows | Low |
| D-06 | Re-capture the official Chiefs and Titans injury blocks and diff them against the current transcription | Q-06 | Low |
| D-07 | Estimate the 2026 home-field effect from the official results with a bootstrap interval and compare it against the 2.0 constant | Q-08 | Low |
| D-08 | Decide whether to use club statistics pages for advanced team stats, and document the exact pairing rule if so | Q-09 | Low |
| D-09 | Hold a final integration session that re-verifies the combined tree and publishes one canonical NFL landing page | Q-10, site navigation | Medium |

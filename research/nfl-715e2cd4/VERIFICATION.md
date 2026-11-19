# Verification log — desk 715e2cd4

**Session:** 715e2cd4. **Date of all reads:** 2026-11-19, clock recorded per capture in
`data/captures.csv` and `data/capture_log.csv`.

## 1. Method

1. Read the official page with the page-read tool; save the processed text as a raw extract in `raw/`.
2. Hash the extract (SHA-256) and record the URL, the read clock and the row count.
3. Parse with a **fail-closed** parser: `pipeline.py` aborts if a page's row count or field count
   drifts from the pin (32 clubs, 136 finals, 14 finals, 13 fixtures, 253 injury rows).
4. Reconcile derived numbers against an independent official total wherever one exists.
5. Leave anything unconfirmed blank, and give it a flag id.
6. `verify.py` re-asserts steps 2-5 and fails the build on any violation, including nine negative
   controls.

What the hash does and does not prove: it proves the extract did not change after capture. It does
**not** prove the transcription is faithful. Faithfulness is evidenced by reconciliation, not by
hashing. This distinction is stated on the site as well.

## 2. Line-by-line checks performed

| # | Check | Method | Result |
|---|---|---|---|
| 1 | Standings have 32 clubs | row count pin | PASS (32) |
| 2 | Wins equal losses league-wide | arithmetic | PASS (149 = 149) |
| 3 | Points for equals points against league-wide | arithmetic | PASS (6,923 = 6,923) |
| 4 | Games played sum is even | arithmetic | PASS (150 games) |
| 5 | Corpus covers weeks 1-9 only | week set | PASS ({1..9}) |
| 6 | Corpus has no duplicate fixture | matchup+week key | PASS (0 duplicates) |
| 7 | Every club: corpus + official Week 10 line = official season total | club-by-club reconciliation | **PASS 32/32 MATCH** |
| 8 | The four Week 10 bye clubs reconcile without a Week 10 line | reconciliation | PASS (CHI, DEN, PHI, TB) |
| 9 | Week 10 extract has 14 finals | row count pin | PASS (14) |
| 10 | Week 11 extract has 13 fixtures | row count pin | PASS (13) |
| 11 | Week 11 fixtures plus 6 byes cover 32 clubs | set arithmetic | PASS (26 + 6) |
| 12 | Injury report rows | row count pin | PASS (253 rows, 24 clubs) |
| 13 | Clubs marked "no injuries reported" are counted as zero rows, not missing | explicit handling | PASS (CIN, WAS) |
| 14 | Designated Out total matches the per-club summary | cross-table check | PASS (9) |
| 15 | Designated Questionable total matches the per-club summary | cross-table check | PASS (7) |
| 16 | Practice status totals match the report | cross-table check | PASS (83 DNP / 87 LP / 83 FP) |
| 17 | Estimator A MAE reproduces from the per-game table | independent recompute | PASS |
| 18 | Constant-mean total baseline MAE reproduces from the corpus | independent recompute | PASS |
| 19 | Home-win interval brackets the point estimate | arithmetic | PASS |
| 20 | Every data row carries a resolvable URL (where applicable) | verifier rule V1 | PASS |
| 21 | Every blank has an adjacent explanation | verifier rule V2 | PASS |
| 22 | No internal link is broken across 15 pages | verifier rule V3 | PASS |
| 23 | No market price is asserted anywhere | verifier rule V7 | PASS |
| 24 | No depth, snap or inactive value is invented | verifier rule V9 | PASS |
| 25 | Leaderboard carries no performance figure | verifier rule V6 | PASS |

## 3. Source-by-source record

| # | Source | Rows / facts taken | Verified how |
|---|---|---|---|
| S01 | `nfl.com/standings/league/2026/REG` | 32 clubs × (W,L,T,PF,PA) | league-wide W=L and PF=PA; drives 32/32 reconciliation |
| S02 | `nfl.com/schedules/2026/by-week/week-11` | 13 fixtures, kickoffs, networks, byes | fixture set + 6 byes = 32 clubs |
| S03 | `nfl.com/schedules/2026/by-week/week-10` | 14 finals with scores | reconciliation closes the season exactly |
| S04 | `nfl.com/injuries/league/2026/reg11` | 253 player rows, 24 clubs | cross-table counts |
| S05 | `nfl.com/injuries/league/2026/reg10` | pointer only | not used for any value |
| S06 | `nfl.com/transactions/` | pointer only | not used for any value |
| S07 | Dolphins/Willis/McCord article | IR move + first start | quote stored verbatim |
| S08 | News roundup 2026-11-13 | Lamar Jackson 6-10 weeks | quote stored verbatim |
| S09 | News roundup 2026-11-11 | Watson and Beck starters | headline-level only, flagged F-14 |
| S10 | "Drew Lock ... will start" | announced starter | headline verbatim |
| S11 | Game centre Bengals@Commanders | NORTHWEST STADIUM, Landover MD | conflicts with the schedule link → F-03 |
| S12 | Game centre Colts@Texans | RELIANT STADIUM, Houston TX | matches the schedule page |

## 4. Irregularities found (and what was done)

1. **Venue conflict (F-03).** The Week 11 schedule page's ticket link points to `AT+T Stadium` /
   `FedEx Field` style venue URLs, while the game centre Game Info block for Bengals@Commanders prints
   **NORTHWEST STADIUM, LANDOVER, MD**. The game centre is treated as authoritative for the venue
   column; both strings are quoted and the row is flagged.
2. **Negative home-field term (F-06).** −0.50 points over 136 games. Published as the model's HFA and
   raised as Q04, not replaced with a textbook 2-3 points.
3. **Lions designations do not match the brief (F-12).** The brief says Joseph, Mays and Reed are Out.
   The page read at 2026-11-19 shows Joseph and Reed with practice status and a blank game status,
   and Mays DNP with a blank status. Both claims are quoted; neither is asserted.
4. **Club-code mismatch (F-05).** The carried 136-game file uses LAR/ARI/WSH where the league table
   uses LA/AZ/WAS. Mapped explicitly in `pipeline.py`, never silently.
5. **Partial standings capture (F-04).** Only W-L-T-PCT-PF-PA were taken. Home/road/division/conference
   columns are omitted from every table rather than reconstructed.
6. **No publication timestamp on the injury report (F-11).** Only our read clock exists, so a "delta"
   can be labelled with our clock but not the publisher's.

## 5. What could not be verified at all

* Any market price (0 of 39 markets).
* Any depth rank, starter flag or replacement name (253 of 253 rows blank).
* Any snap share or inactive status (253 of 253 rows blank).
* Whether Lamar Jackson is on IR (evidenced only by a league article, not by a captured transaction).
* What "Questionable" means (n = 0 archived seasons).
* Any prior-season comparison (no prior-season page captured).

Each of these has a flag id on `flagged.html` and a question id on `questions.html`.

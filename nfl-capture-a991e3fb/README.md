# Week 10 official injury report: live capture (session a991e3fb, 2026-11-15)

Page: `/Own5/nfl-capture-a991e3fb/` (GitHub Pages, repo root source).

## What was done

1. Read the official NFL.com Week 10 injury report (`https://www.nfl.com/injuries/league/2026/reg10`) in full, 8 chunks.
2. Transcribed all 347 rows (28 clubs, 14 games) into `raw/reg10_official_transcription.txt`.
3. `build.py` parses the transcription, runs hard checks, writes the CSV, the diff against the previously published table, and the page.
4. Compared with the previously published table at `data/decision-desk/official/official_injuries_wk10.csv` (276 rows, captured 2026-11-12T16:52:39Z from the generic `/injuries/` URL).

## Results

| Measure | Previously published | Live official page (this capture) |
|---|---|---|
| Rows | 276 | 347 |
| Clubs with rows | 26 (no Ravens, no Chargers) | 28 (CHI, DEN, PHI, TB absent = Week 10 byes) |
| Lions Joseph / Mays / Reed game status | blank | Out |
| Rows that differ | — | 268 (71 added to the report; 130 blank game status now Out, Questionable or Doubtful; 67 other practice or game status changes) |

## Checks (see `data/checks.csv`)

- Per-club row counts equal the reader tallies (28/28 sections).
- The four clubs without a section are exactly the Week 10 bye clubs in `data/bye-weeks-2026.csv`.
- All status values fall within the published vocabulary; every row has a `nfl.com` source link.
- Lions designations match the official page.

## Limits (flagged on the page)

- Bash cannot reach nfl.com from this sandbox. The raw file is a transcription of the fetch tool's output, not a byte-for-byte download. It has no SHA-256 hash of the page, because the bytes were not stored. A reviewer should spot-check rows against the page.
- The official page shows no publication timestamp. The capture time is the time the page was read, not the time NFL published it.
- `/injuries/league/2026/reg11` redirected to the Week 10 page when read, so no Week 11 report was available.
- Malik Willis (injured reserve) and Lamar Jackson (injured reserve) do not appear as rows. Their absence is recorded from the official news headlines on the same page, not inferred as healthy.

## Not done in this session (blocked, with the source that would unblock it)

The brief asks for multi-day snapshots, a scheduled capture, depth charts for 32 clubs, snap counts, inactive lists, archives of past injury reports, a venue for every fixture, and an authorized source for the Texans depth image. Each needs either a scheduled job that can reach nfl.com (not available in this sandbox) or a source the repo does not yet hold. The existing requirements register, which tracks these items and their blockers, is at `nfl-desk-3fb93d11/requirements.html`. The open questions and suggestions are at `nfl-desk-3fb93d11/questions.html` and `nfl-desk-3fb93d11/suggestions.html`.

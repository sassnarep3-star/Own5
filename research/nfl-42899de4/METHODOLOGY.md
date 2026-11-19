# Methodology — Week-11 per-team injury desk (session 42899de4)

Date of work: 2026-11-19 (UTC). Branch: `arena/42899de4-own5`.

## Scope

Own lines from the brief:

- Per-team view: **starters out**, **replacements named**, **net injury count** — one row per club.
- Injury-hub reads stored with **clock time**, and the **delta** published (never the level alone).
- Point-in-time snapshots; **no jersey-order inference**; "not listed" is never read as "available".
- Fixtures and byes for Weeks 11 and 10 from the official schedule only.
- Site: clean dashboard landing + category subpages, tables.
- Verification rule: every row has an official source link or is blank **and flagged**.

Out of scope (owned elsewhere): root landing/nav (integration session, CI-locked),
availability graph (PR #136), price/line data (G-10 blocked), depth extraction
(K-035 route B), designation-reliability modelling (nfl-line-audit).

## Reads (first-hand, `fetch_page`)

| ID | URL | Read window (UTC) |
|----|-----|-------------------|
| S-01 | `https://www.nfl.com/injuries/league/2026/reg11` | 2026-11-19 11:46–11:52 |
| S-02 | `https://www.nfl.com/injuries/league/2026/reg10` | 2026-11-19 11:55–12:03 |
| S-03 | `https://www.nfl.com/schedules/2026/REG11` | 2026-11-19 11:53 |
| S-04 | `https://www.nfl.com/schedules/2026/by-week/week-10` | 2026-11-19 12:06 |

No other session's files were used as data. Four repo captures were read **only**
as cross-checks (X-01…X-04 in `sources.csv`).

## Transcription

- `injury_report_w11.csv`: 255 rows = 253 player rows (24 clubs) + 2 explicit
  `no_injuries_reported` rows (CIN, WAS). Columns copied verbatim from the page
  (club, player, position, injury, practice status, game status).
- `injury_report_w10.csv`: 347 player rows, 28 clubs (the 4 Week-10 byes are
  absent from the report, as expected).
- Fixtures/byes transcribed from the schedule pages exactly as printed
  (kickoff has no zone suffix on the schedule page; the injury-report headers
  print the same clocks with EST — Q-TV-08).

## Definitions

**Report state** (per club, per week)

| State | Meaning |
|-------|---------|
| `listed` | Club has player rows on the official report. |
| `no_injuries_reported` | Page explicitly prints "No Injuries Reported" → counts are 0 because the page says so (F-TV-06). |
| `absent` | Club not on the report because it is on bye → **every** report column blank (F-TV-06). |

**Net injury count** = number of players on the club's report with a printed
game-status designation (Out + Questionable + Doubtful) as of the read clock.
Rules:

1. If any designation is printed for the club → counts published.
2. If the club is on the report but **no** designation is printed (all Game
   Status cells empty, as for Sunday/Monday clubs on the Wednesday read) →
   counts are **blank**, `designations_printed = NO_NOT_PRINTED`, flag F-TV-03.
   Blank ≠ zero: zero would assert "nobody is out", which the page does not say.
3. Explicit "No Injuries Reported" → 0 (printed statement, not inference).
4. Bye → blank (the club is not on the report at all).

Practice-status counts (DNP/LP/FP) are always published for clubs with rows —
the practice column is populated on both reads.

**Starters out / replacements named** — always blank in this snapshot
(F-TV-01, F-TV-02). No official announced-starter article and no official
depth/playing-time source were read in this session; the brief forbids
inference, so the columns exist, are blank, and are flagged. Gates: K-027,
K-035.

**Delta (W10 → W11)** — club-level difference of the same printed metric:

- `delta_listed`, `delta_dnp`: computable for the 22 clubs that played both
  weeks; blank for bye clubs.
- `delta_out`, `delta_net`: computable only where **both** sides are printed —
  IND, HOU (Thursday game designations), CIN, WAS (explicit zero). Blank for
  the other 22 playing clubs (W11 side unpublished, F-TV-03) and for bye clubs.
- Publication-state asymmetry (F-TV-11): W10 designations are final (completed
  week); W11 designations are mid-week. Both sides are labelled in the table.

The **signal** is the delta; levels are published only alongside their read
clocks (Q-TV-07).

## Pipeline

```
fetch_page (first-hand) ──► row-level CSVs (data/nfl-teamview-42899de4/)
                                    │
                                    ▼
              compute_views.py  (deterministic roll-up: 32-club views + delta)
                                    │
                                    ▼
              build_site.py     (12 HTML pages + style.css, no wall-clock)
                                    │
                                    ▼
              verify.py         (fail-closed: pins, allowlist, blank rules,
                                 independent recomputation, byte-identical
                                 rebuild, site link integrity)
                                    │
                                    ▼
              tests/test_verify.py (11 negative controls — corruption must fail)
```

CI (`.github/workflows/nfl-teamview-42899de4.yml`) runs all three stages on
every PR touching this desk's paths and diffs the rebuild against the committed
files.

## What was deliberately not done

- No starter/depth/reserve data of any kind was invented or imported.
- No news-rail headlines were modelled (F-TV-08).
- No edits to other sessions' files, the root landing, or shared nav.
- No rows copied from other desks' captures — cross-checks only.

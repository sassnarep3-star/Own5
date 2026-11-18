# NFL Command Desk — executive summary

Session `4078a9ad`, branch `arena/4078a9ad-own5`. Work date **2026-11-18 (UTC)**.
Every figure below was read from an official publisher in this session or is a computation
over rows that reconcile to one. Where nothing official exists, the line says so.

## 1. What was built

A single decision layer over the repository's 32 NFL desk folders, in one additive namespace
(`nfl-command-desk/`), with eleven pages and eighteen data tables. Every table row carries the
official page it came from, or an `UNVERIFIED` marker. The generator and the verifier are
deterministic: no network, no clock, no git in the build.

## 2. The one result that matters

**The results corpus now reconciles to the league's own standings, for every club.**

| Check | Result |
|---|---|
| Completed 2026 games in the corpus | **150** (weeks 1-10) |
| Clubs whose W-L-T, PF and PA match the corpus exactly | **32 / 32** |
| Mismatched clubs | **0** |

Points-for and points-against are additive, so a single wrong score breaks at least two clubs.
A perfect 32-club match is a much stronger check than spot-reading a scoreline, and it is why
the 136-game log can now be called a backtest corpus rather than a list. The reconciliation is
recomputed by the verifier on every build (`V03`, `V04`), and a unit test plants a one-point
error to prove the check catches it.

## 3. What the pre-registered tests found

Registration commit **`e7282e35dbf9afb0c1b364a152b9431dc71b64af`**, written before any number
was published. Windows: train weeks 1-4, validation weeks 5-8, holdout weeks 9-10.

| Registered strategy | Window | n | Brier skill vs flat 0.5 | 95% CI | Holm p | Certified |
|---|---|---|---|---|---|---|
| REG-M1 moneyline baseline | validation | 56 | −0.353 | −0.662 .. −0.045 | 0.370 | NO |
| REG-M1 moneyline baseline | holdout | 29 | +0.222 | −0.147 .. +0.564 | 0.246 | NO |
| REG-M1 moneyline baseline | weeks 5-10 | 85 | −0.157 | −0.405 .. +0.089 | 0.177 | NO |
| REG-S1 side vs model line (control) | weeks 5-10 | 85 | 0.000 | 0.000 .. 0.000 | 0.117 | NO |
| REG-S2 home at a frozen −2.0 line | weeks 5-10 | 86 | — | 0.233 .. 0.442 (hit rate) | 0.030 | NO |

**No strategy is certified.** Three things stop it:

1. The Brier-skill interval for the only forecast we have crosses zero on the full
   out-of-sample window.
2. The side rows are controls, not selections: at the model's own line the cover rate *is* the
   home-cover rate, and at a frozen −2.0 line the result is one directional exposure across 86
   games, not a per-game pick.
3. The repository holds **no official market price**, so ROI and closing-line value cannot be
   computed at all (FLAG-P1). The staking columns are blank by design.

The luck arithmetic is published so a good week cannot be mistaken for skill: at n=57 a bettor
needs 31 wins (54.4%) before 55% is even reached, and **617 settled bets** are needed to detect
a true 55% edge with 80% power.

## 4. Availability: what the official page actually says today

The Week 11 injury report **was not published** at read time. The request for
`nfl.com/injuries/league/2026/reg11` resolved to the Week 10 page and its title string read
"Week 10 of the 2026 Season" at **2026-11-18T03:45Z**. No Week 11 availability value is
published on the site.

Week 10 was re-read for the four clubs fully visible in chunk 0 of 8 (**44 rows**), and compared
cell by cell with the repository's capture of 2026-11-12T16:52Z:

| Result | Rows |
|---|---|
| Identical | 27 |
| **Stale in the repository copy** | **17** |

The brief named three Lions cells published blank. All three are confirmed, and the official
page now prints more than a status for them:

| Player | Repo 2026-11-12 | Official 2026-11-18 |
|---|---|---|
| Kerby Joseph | injury blank, practice "Limited", game status blank | Knee, Did Not Participate, **Out** |
| Cade Mays | injury blank, practice DNP, game status blank | Ankle, Did Not Participate, **Out** |
| D.J. Reed | injury blank, practice DNP, game status blank | Hip, Did Not Participate, **Out** |

Four further Lions rows moved (Branch, Goff, St. Brown, Vaki). What still cannot be said: no
official source names a replacement, so the replacement and depth columns stay blank on every
club (FLAG-A2, FLAG-D1).

## 5. Fixtures and schedule provenance

- **13 games + 6 byes** in Week 11, each club exactly once, 32/32 accounted for.
- Every fixture carries date, kickoff (ET) and network from the official week page.
- Every venue is transcribed, with the method stated per row: the page prints no venue column,
  so the destination of the page's own hotel link is used, and the one fixture named in prose
  (Minnesota at San Francisco, Estadio Banorte) carries both that page and the announcement.
- The league's **dated** schedule announcement (**2026-05-14**, media.nfl.com) is published
  beside the live page; the six comparable facts agree: 18 weeks, 272 games, 17 + 3, nine
  international games, Week 11 in Mexico City, season 107.

## 6. Requirements ledger

73 requirement lines from the brief, each with the gate that blocks it and the number that
would clear it.

| Status | Count |
|---|---|
| MET | 27 |
| PARTIAL | 10 |
| BLOCKED | 33 |
| REJECTED (shortcut refused) | 2 |
| NOT STARTED | 1 |

The 33 blocked rows cluster into six missing datasets, not thirty-three separate failures:

| Missing dataset | Blocks | Flag |
|---|---|---|
| Official market prices (opening and closing) | 5 rows | FLAG-P1 |
| Snap counts, playing time, inactives | 8 rows | FLAG-A2 |
| Roster / reserve-list sweep, Game Books | 4 rows | FLAG-A3 |
| Multi-day hashed availability snapshots | 5 rows | FLAG-A4 |
| Club depth charts (any of 32) | 9 rows | FLAG-D1 |
| Joint outcome table for correlations | 2 rows | FLAG-C1 |

## 7. What a reviewer should do next

The suggestions page carries twelve proposals with empty decision cells. In order of value:

1. **S12** — stop adding NFL desks. Thirty-two desks and zero certified strategies is the
   finding, and another desk will not change it.
2. **S05** — capture the injury report three times a week into a hashed store. Everything about
   availability, the injury ablation and the replacement signal depends on this one dataset.
3. **S01/S02** — make one desk the landing page and retire the rest. A reader currently has to
   choose between 32 pages that answer the same question differently.

## 8. Honest limitations

- One read per source, on one day. The injury page was returned as processed text, not server
  bytes, and only 1 of 8 chunks was read.
- The 136-game log was transcribed by an earlier session on 2026-11-12. It is adopted here
  because it reconciles exactly, which is evidence about the scores, not about the venue or
  kickoff fields.
- The home-field value 2.0 is a published **assumption**; the observed 2026 home margin is
  −0.98 over 150 games with a 95% CI of −3.07 to +1.13.
- No market price, no correlation, no injury ablation and no snap count exists in the
  repository. Nothing has been filled in by hand to hide that.

Sources: <https://www.nfl.com/standings/league/2026/REG>,
<https://www.nfl.com/schedules/2026/by-week/week-10>,
<https://www.nfl.com/schedules/2026/by-week/week-11>,
<https://www.nfl.com/injuries/league/2026/reg10>,
<https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1>,
<https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced>.

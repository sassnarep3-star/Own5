# NFL cross-desk reconciliation - executive summary (session 28431d9c)

Date: 2026-11-13 (UTC). Branch `arena/28431d9c-own5`. Published hub: `nfl-hub-28431d9c/` (served under the GitHub Pages site at `/Own5/nfl-hub-28431d9c/`). Every number below is computed by `build.py` and re-checked by `verify.py`.

## Key results

- **Standings:** 32 official teams. 30 match exactly in all three desks. The only differences are NYG and WAS, because the desks still show the Thursday game as pending.
- **Thursday result:** Adding the official Thursday result to each desk's pre-game NYG and WAS record and points: e413f933 reproduces NYG (pre 5-2-1 182-172); b34253a1 reproduces NYG (pre 5-2-1 182-172); 26d4cafb reproduces NYG (pre 5-2-1 182-172); 38a1fc27 root snapshot reproduces NYG (pre 5-2-1 182-172); e413f933 reproduces WAS (pre 2-5-1 172-202); b34253a1 reproduces WAS (pre 2-5-1 172-202); 26d4cafb reproduces WAS (pre 2-5-1 172-202); 38a1fc27 root snapshot reproduces WAS (pre 2-5-1 172-202).
- **Week 10 slate:** 14 games checked against the official schedule. Mismatches across desks: 0. b34253a1 still shows the Thursday game as SCHEDULED. The e413f933 and 26d4cafb schedule files have no status field, so their Thursday status cannot be checked.
- **Byes:** CHI, DEN, PHI and TB. e413f933 and b34253a1 match. 26d4cafb has no machine-readable bye list.
- **Injuries (4 games, 44 official rows):** e413f933 matches 29 exactly and differs on 15. b34253a1 lists 11 of the rows, differs on 3 and is practice-level only on 2.
- **Own-line favorites:** the three desks disagree on the favorite in 4 of 14 games. The desks' home-field inputs differ.
- **Flags:** 16 open (3 high, 9 medium, 4 low). Flags are nonblocking and are published on the Flagged for Review page.

## Method

1. Official values were transcribed from `fetch_page` results of nfl.com: the standings page (re-fetched 2026-11-13, post-Thursday), the Week 10 schedule page (3 chunks), and the Week 10 injury report (chunks 0 to 6; chunk 7 returned no data). Each official row carries its page URL.
2. Each desk file was read read-only and compared row by row. A value that could not be confirmed is shown blank and flagged. Nothing was inferred or filled.
3. `verify.py` checks the official arithmetic (PF = PA, net, win %), the 44-row injury count, row links, internal links, the Thursday reversal (re-derived from the desk files), and that a rebuild is byte-identical.

## Limits

- Only the official sources listed above were used. Article bodies of news items were not opened. Chunk 7 of the injury report returned no data.
- No own-line origination, signal strategy, correlation, parlay or leaderboard work was done in this session. Those outputs in each desk are unverified here (Flagged H-16).
- Market quotes were not re-verified against the sportsbooks. Their timestamps are date-only (H-02).

## Suggestions for human review (not implemented)

1. Desk owners refresh standings and the Thursday status to the post-game official values (H-01).
2. b34253a1 records a retrieval time for every market quote (H-02).
3. Fix the Ben Brown position (LG vs C) and the "VERIFIED" label in b34253a1 (H-03).
4. Correct the 26d4cafb availability labels ("Confirmed Out / IR" for players not on IR) and the Nacua entry (H-06, H-08).
5. Replace the root 38a1fc27 injury snapshot with a dated official pull, or mark it superseded (H-14).
6. Use one abbreviation for Washington (desks use WAS, WSH) and for Arizona (desks use AZ, ARI). The abbreviation match is currently handled in code only.
7. Add a machine-readable bye list to 26d4cafb (H-12).
8. Capture official news article bodies, not only headlines, before using any news as a status source (H-13).
9. Confirm the Seattle QB designation on the official injury page before using it in any QB-dependent output (H-15).

## Questions

**Known (confirmed this session):** official standings and slate; the Thursday final; the 44 official injury rows for the four sampled games; TreVeyon Henderson's Out status (illness) and hospitalization headline; Sam Darnold ruled out and Drew Lock expected to start (headline); Lamar Jackson placed on IR (headline) and out 6-9 weeks; Tyler Huntley out for the season (headline); Puka Nacua knee testing (Week 9 headline).

**Missing or unconfirmed:**
- Whether Carson Beck starts for Arizona and Deshaun Watson for Cleveland (headlines not reproduced on re-fetch).
- Whether Malik Willis is on IR and Kyle McCord starts for Miami (not reproduced).
- Kenneth Walker's status (absent from the official Seattle table).
- Game status for Sam Darnold and Puka Nacua (blank on the official page while the news implies out).
- Venue names for the Thursday game and the Munich game.
- Timestamps for the sportsbook quotes.

**How to find the missing information:** re-fetch the nfl.com injury report and its news links on each game day; check the nfl.com transactions page for IR moves (not fetched in this session); read the article bodies of the news items linked from the injury page; take sportsbook quotes with a retrieval time; and re-run `build.py` and `verify.py` after any update.

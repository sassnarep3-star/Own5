# FLAGGED FOR REVIEW — session 7e228db8 (mirror of the desk register)

The authoritative register is `data/nfl-desk-7e228db8/flagged.csv`, rendered at
`nfl-desk-7e228db8/flagged.html` with evidence links. Summary:

| ID | Item | Severity |
|---|---|---|
| F7-01 | IND@HOU venue named "RELIANT STADIUM" (game centre) vs "NRG Stadium" (schedule page) | medium |
| F7-02 | LAC still lists Daiyan Henley despite the 2026-11-10 trade report to DEN (stale roster evidence) | high |
| F7-03 | DET's Aidan Hutchinson absent from the Week 11 report amid a significant knee-injury report — reserve list not captured | high |
| F7-04 | BUF label "Dee Alford" links to /players/deaundre-ford/ (label/slug mismatch) | low |
| F7-05 | Many blank game-status cells on the Wednesday read (official mid-week state) | medium |
| F7-06 | Shared corpus data/games_2026.json missing Week 8 MNF CHI 34 @ SEA 17 — patched here; owner adoption requested | high |
| F7-07 | No verified operator price source → market/residual/CLV/ROI blank by policy (F7-P01) | high |
| F7-08 | Injury series has a single (Wednesday) read this week | medium |
| F7-09 | 62 of 120 W1–8 corpus rows carry 'recon' verification (PFR reconciled) — inherited | medium |
| F7-10 | Fitted HFA is negative (−0.93 pts, n=150) — published as computed, tested prospectively | medium |
| F7-11 | KC lists RB Kenneth Walker III; roster status unverifiable without transactions capture | medium |
| F7-12 | PIT lists WR Michael Pittman; roster status unverifiable without transactions capture | medium |
| F7-13 | Game-centre injury strip shows undefined letter "A" — not used as a designation | low |
| F7-14 | Model is in-sample on 150 finals — no out-of-sample claim is made | high |
| F7-15 | Page-fetch returns processed text; hashes cover stored excerpts, not server bytes | medium |
| F7-16 | nfl-b34253a1 audit hash-pins workflows changed by PR #139 (X51-14 fix) — audit stale until regenerated | low |
| F7-17 | nba-commission verifier fails on a broken internal link (standing X51-05) | low |
| F7-18 | nfl-command-desk registration commit not on main lineage | low |
| F7-19 | nfl-desk-35a1feb2 committed-artefact drift on main — takeover fix V7-14 applied, owner review requested | medium |

Nothing here blocks publication; these are published precisely so the owner can review them.

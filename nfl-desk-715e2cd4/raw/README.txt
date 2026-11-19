RAW CAPTURE EXTRACTS — nfl-desk-715e2cd4
========================================
These files are text EXTRACTS of official nfl.com pages, captured with a page-read
tool that returns processed text, not server bytes. They are therefore labelled
"processed extract", never "verbatim HTML". Each file's sha256 is recorded in
../data/captures.csv together with the source URL and the UTC retrieval time, so
tampering or silent drift is detectable; the hash does NOT prove transcription
accuracy. Row-level accuracy is evidenced separately by reconciliation checks
(see ../research/nfl-715e2cd4/VERIFICATION.md).

File conventions
  standings_2026_reg.txt        "TEAM W L T PF PA" per club, one row each
  schedule_2026_wk11.txt        one fixture per row: away|home|date|time_et|network|venue|status
  results_2026_wk10.txt         one final per row: away|home|away_pts|home_pts|date
  injuries_2026_reg11.txt       verbatim markdown table rows pasted from the page, grouped by team

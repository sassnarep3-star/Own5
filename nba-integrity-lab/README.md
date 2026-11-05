# NBA Integrity Desk

A static, additive GitHub Pages research dashboard. Open `index.html` or serve the repository root and browse `/nba-integrity-lab/`. The nine November 6 model lines are frozen research estimates, **not** official NBA or bookmaker lines, calibrated betting predictions, or recommendations. The display is not a live injury or odds feed.

## Scope and evidence

- `data/team_snapshot.csv`: 18 selected 2026–27 NBA advanced-team rows.
- `data/schedule_snapshot.csv`: nine matchups and the 4:00 p.m. ET November 5 injury-report snapshot. A later update can differ; 17 of 18 team reports were unsubmitted in this snapshot. The Utah–Dallas source labels differ and are not converted or reconciled.
- `data/edwards_sample.csv`: 25 selected 2025–26 Anthony Edwards appearances and the displayed columns; chosen after the season and conditional on participation.
- `model.py`: transparent researcher-chosen baselines, selected-sample descriptive correlations, exact independent-binomial examples and a fail-closed gate checker. See its docstrings and [verification boundary](../research/nba-integrity-lab/VERIFICATION.md). Inputs, formulas, and thresholds are not verified forecasts or trading signals.
- `data/legacy-audit.json`: link-presence scan of static HTML data rows in immutable session-start commit `54e8dee596d49731c3da535a1f77b01cd0c295d5`. It lists all 369 missing-allowlist-link locations. Presence is not proof of factual entailment; unlisted domains and non-HTML/dynamic data can be missed. It is not a full repository fact-check.
- `review.html`: transparent, nonblocking flags, including cross-session correction requests; missing quotes, performance and rewards remain truly blank.

Official data sources and the limited manual comparisons are recorded in [VERIFICATION.md](../research/nba-integrity-lab/VERIFICATION.md); source links on strategy and policy rows are contextual references, not endorsements. The local checker does not exhaustively check remote URL availability.

## Rebuild and test

Requires Python 3.11+ and Git with the baseline commit available. All analysis uses the standard library; there is no API key, build-time download, or server backend.

```sh
python3 nba-integrity-lab/legacy_audit.py   # regenerate baseline row-link audit
python3 nba-integrity-lab/build.py          # regenerate derived JSON and 10 HTML pages
python3 nba-integrity-lab/check.py          # local links, table row contexts, blank cells
python3 -m unittest discover -s nba-integrity-lab -p 'test_*.py' -v
node --check nba-integrity-lab/app.js
git diff --exit-code -- nba-integrity-lab   # after committing reproducible outputs
```

For a local preview, run `python3 -m http.server 3000 --bind 0.0.0.0` from the repository root. The JavaScript enhances table filtering; tables and links remain usable with JavaScript disabled. For the Chromium smoke test, install the existing root dependencies via `npm ci --ignore-scripts`, start the server and run `TEST_BASE_URL=http://127.0.0.1:3000 node nba-integrity-lab/browser.cjs`. The address is used by the test process only; the published site itself uses relative URLs. Tests check both desktop and mobile, as well as no-JavaScript rendering.

## Future competition prototype

`competition.py` demonstrates a proposed offline ranking after ten policy gates, per-row timestamps and source-link shape checks, a positive externally reviewed clustered lower bound, and at least 200 verified graded records. Its inputs are **attestations**, not authenticated records: the code does not verify sources, calculate the clustered bound, establish the completeness of an omitted trial family, conduct an actual competition or settle payouts. Divisions rank separately by supplied lower bound; exact ties are ordered by strategy ID. Proposed gold/silver/bronze research badges are noncash, and the cash field remains null. Synthetic fixtures in `test_competition.py` are not real results. The live page deliberately contains zero qualified strategies and no prizes.

A real evaluation would require verifiable immutable pre-event records, executable prices and rules, held-out outcomes, appropriate uncertainty/multiplicity treatment, an independent replication, and external review. Luck cannot be literally removed; a sample floor alone cannot establish skill.

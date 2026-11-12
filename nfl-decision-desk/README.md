# NFL Decision Desk — 2026-11-12 UTC

## Executive summary

The safe present decision is **research / paper evaluation only**. Existing NFL code provides model, correlation and gate machinery, but does not establish a current executable advantage. This additive nine-page dashboard supplies explicit questions, answers, missing information, research candidates, proposed qualification gates, an unranked competition framework, suggestions awaiting review and nonblocking irregularities. It does not replace other sessions' files.

## Verification boundary

60 rows link to official publisher references. A link on a proposal establishes relevant background or a discovery destination, **not endorsement or proof of the proposed strategy**. Selected displayed source excerpts were checked using the page retrieval tool on November 12, 2026 UTC. Only the first injury-report chunk was reviewed; selected injury rows are not a complete league snapshot. No independent roster cross-check was completed. Do not silently treat an official publisher's unofficial chart as confirmed participation.

Checked source scopes are documented in `register.json` and `sources.html`. The injury-policy URL returned a 404; no policy facts were extracted. NFL injuries, Washington chart, New England chart/disclaimer, NFL club directory and NIST scatter-plot association warning were checked. Two unrelated NIST pages fetched during discovery (skewness and DOE standard deviations) do not support this release's strategy claims and were excluded.

Current prop correlation coefficients, joint probabilities, fair current lines, market prices, expected values, stakes and competition results are **not verified** and are blank. None of the strategy proposals has passed validation. Statistical modeling cannot remove luck; use prospective holdouts, clustered uncertainty, registered trials, multiplicity controls and abstention instead. Gate thresholds require a locked power analysis; arbitrary constants are not official scientific standards.

## Repository review findings

Reviewed the shared board (1,048 lines at initial read), package configuration, Pages/verification workflows, existing NFL folder structure, `nfl_model/{validation,correlation,ratings}.py`, `data/correlations.csv`, the opening rows of `data/model_lines_2026_wk9.csv`, and root `EXECUTIVE_SUMMARY.md`. This is **not** a claim that the entire multi-project repository or every historical input was re-verified. Existing player-correlation machinery distinguishes descriptive continuous correlation from binary-leg outcomes. Existing fixed gate thresholds are project policies. Existing gate equality comparisons need strict type-schema review before operational qualification. All these limitations are published on Flagged for Review.

## Reproduce

From the repository root:

```sh
python3 nfl-decision-desk/build.py
python3 nfl-decision-desk/verify.py
node --check nfl-decision-desk/app.js
python3 -m unittest discover -s tests -v
```

Build is dependency-free. Tests check determinism, every table row's registered official references, local links/assets, blank unavailable coefficients and ranks, and absence of network execution in client code. Structural tests do **not** validate external claims or guarantee external link availability. HTML tables and navigation work without JavaScript; JavaScript adds filtering only. Source pages are dynamic and their complete raw responses are not archived here.

## Automation and review

No manual input was needed to build this release. It is nevertheless a **static snapshot**, not continuous injury/lineup surveillance. Proposed ingestion, lineup reconciliation, source-hash archives, stale-feed alarms and joint simulation are deliberately not represented as implemented services. No funds, prizes, betting accounts, credentials or paid API access are configured. Shared root navigation was not edited because its ownership is elsewhere; the new site is directly accessible at `/Own5/nfl-decision-desk/` and links back to the existing NFL lab and repository landing page.

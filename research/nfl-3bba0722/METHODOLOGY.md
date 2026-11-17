# Methodology — NFL decision review hub

## Scope

This is a bounded, additive source review on 2026-11-17. It is not a rebuild or reconciliation of every NFL desk in the repository. Existing namespaces are read-only; the hub publishes a separate decision docket and explicit findings. The exact retrieval time was not exposed by the page retriever, so only the date is recorded.

## Source verification

1. Prefer direct primary pages from NFL.com, NFL Football Operations, the relevant NFL club, the applicable operator, or the responsible government agency.
2. Record the exact requested URL and the page's rendered title/scope. A live page that resolves to the wrong week is a **mismatch**, not a usable current observation.
3. Record the check date, what the page actually contains, source tier and use limitations. Do not invent a fetch time or raw hash when the retriever did not provide one.
4. Distinguish “official publisher” from “complete,” “current,” “machine-readable,” “approved for modeling,” and “permission to reuse.” These are separate conditions.
5. Preserve direct official links in every published register row. Where no source confirms a value, the value remains blank and the row is explicitly flagged. Links to repository files are labeled as repository evidence and do not substitute for an official source.

## Evidence model

- **Official source:** primary NFL league, official club, operator, or government page. Operator and government sources are separately labeled from NFL sources.
- **Repository evidence:** an existing file/page that records what an earlier session published. It is an audit trail, not an independent primary source.
- **Proposal:** an option or gate designed for future testing. A proposal is never displayed as a verified league fact or a performance result.
- **Unknown:** no direct value is published. A missing row is not zero, healthy, inactive, a starter, or a negative result.
- **Mismatch:** a source route was reached but the page identity/scope did not match the requested season/week. It cannot clear the requested gate.
- **Restricted:** the source is public but carries an explicit use limitation; rights review is separate from source authenticity.

## Readiness and strategy gates (proposed, not NFL rules)

- Price-dependent outputs require a permitted operator/licensed source with a stable market key and opening/closing timestamps. Until then fair line, market line and difference remain separate fields, with market-dependent cells blank.
- Availability snapshots should run daily from Wednesday through kickoff, with the expected source/week identity checked each time. If a report is not published or the route is stale, record that state instead of carrying forward an old page. A change/delta requires at least two distinct timestamped reads of the same identified official report; a wrong-week response fails closed.
- Expected starters and actual game-day starters/inactives are separate nodes. Join a dated club chart to a game-specific official source; do not infer starter or replacement order from jersey number, experience or salary.
- Depth coverage requires an explicit source/parser result for all 32 clubs before any full-league team feature is trusted. Source-defined groups, shared names and empty slots must be preserved.
- Snap counts are a distinct feature from depth-chart order. Do not publish snap share until an official playing-time source and its use terms are verified.
- Personnel value is tested with identical models with and without verified availability features on chronological holdouts. Report effect, sample size and uncertainty; no fixed point penalty or uncalibrated designation percentage is assumed.
- Pre-register every strategy's definition, inputs, market, sample window, controls, gate thresholds and multiplicity handling before opening the evaluation window. Keep train, validation and final holdout chronological and disjoint.
- A proposed skill qualification is a positive lower 95% game-cluster confidence bound for benchmark-relative Brier skill on an untouched final holdout after pre-registered multiplicity adjustment. Freeze the sample-size/power plan before the holdout. This is a research proposal, not an official NFL standard.
- Keep signal evaluation separate from staking. Backtest values do not belong on the prospective leaderboard. Random and favorites-only controls are required for comparisons.
- Do not rank parlays or player-prop combos by multiplying marginal probabilities. Require a directly validated joint probability and the applicable operator/jurisdiction price, void, push and settlement rules.
- Every model output should store a probability/distribution, fair line, market line, residual, exact input snapshots, model/version hash and forecast timestamp. Keep two total estimators visible until a preregistered walk-forward comparison selects one.
- The luck-removal panel should show benchmark-relative skill with uncertainty and controls; it should not present an adjusted number without its sample, benchmark and method.

## Site build and checks

`nfl-review-3bba0722/build_site.py` deterministically renders six static pages from the local JSON registers. It uses only Python's standard library. `verify.py` checks official-domain URLs, row-level source links or explicit unverified status, required fields, unique IDs, relative internal links, selected repository-evidence links, blank unconfirmed observed values and a deterministic rebuild. Unit tests run with:

```sh
python3 nfl-review-3bba0722/verify.py
python3 -m unittest discover -s nfl-review-3bba0722/tests -v
```

The verifier does not claim that a URL will remain live. Future scheduled ingestion should capture response bytes and hashes under a documented retention policy and alert on freshness/schema changes.

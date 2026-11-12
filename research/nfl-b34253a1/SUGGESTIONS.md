# Suggestions for review — no shared-site change authorized by this page

The machine-readable [`site_suggestions.csv`](../../nfl-b34253a1/data/site_suggestions.csv) contains 12 options with decision area, choices, basis, implementation status, tradeoffs, and source links. Every row is `AWAITING_REVIEW`. This session kept all public files isolated under `nfl-b34253a1/` and did not edit the root navigation, existing NFL desks, or sibling project files.

## Highest-priority decisions

1. **Shared navigation:** keep this project isolated, add a root README/dashboard card, or consolidate into an existing NFL desk. The isolated option is currently implemented only inside this namespace; B/C need reviewer approval and an owning maintainer.
2. **Market snapshots:** require source/operator, jurisdiction, exact UTC capture time, event/market key, line/price, capture hash, and closing quote before CLV or ROI evaluation. Exact time and jurisdiction remain blank in this snapshot.
3. **Availability:** display report status, club chart order, final actives/inactives, and actual snaps separately. Do not turn a string number into a point deduction.
4. **Evidence gates:** show every gate beside every strategy; do not rank or reward an entry until all mandatory prospective-evidence requirements pass.
5. **Paired prop/parlay data:** require the exact legs, odds, outcomes, and settlement rules before estimating joint probability or fair value.
6. **Responsible-use review:** retain non-advice language and accessibility features; resolve jurisdiction, eligibility, local requirements, and any support links before public expansion.

Other options cover stale-data badges, method-level correlation limits, archived legacy claim labels, a pre-event prediction ledger, and reward governance. These are proposals, not services or data feeds delivered by this session. Review the full CSV/page before choosing; a suggestion's presence is not approval.

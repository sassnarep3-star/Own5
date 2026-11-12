# Repository audit scope and interpretation

The generated [`repo_audit_summary.json`](../../nfl-b34253a1/data/repo_audit_summary.json) and [`repo_audit.csv`](../../nfl-b34253a1/data/repo_audit.csv) are a dated physical-line inventory of selected prior NFL/data/research/shared-site artifacts in the repository. `audit_repo.py` restricts its file set to NFL/research/data/shared-context paths and excludes this session's own `nfl-b34253a1/`, `research/nfl-b34253a1/`, and workflow so the inventory does not certify itself.

## Per-line fields

Each CSV row contains an audit ID, repository-relative path, physical line number, SHA-256 of the line, excerpt (truncated to 240 characters), classification, audit note, an HTTPS official source URL or official counterpart, `source_basis`, any nonofficial legacy reference found in a CSV row, scope label, and date.

`source_basis` distinguishes `ROW_SOURCE_FIELD`, `ROW_SOURCE_URLS_FIELD`, `OFFICIAL_GAME_LINK_FROM_RECORD_CONTEXT`, `HTTPS_OFFICIAL_LINK_IN_LINE`, `OFFICIAL_SCOPE_REFERENCE_FALLBACK_NOT_ROW_PROVENANCE`, and `OFFICIAL_COUNTERPART_FOR_FLAGGED_INPUT_NOT_INPUT_PROVENANCE`. In particular, a fallback NFL URL or an official comparator for a flagged secondary-market dataset is not represented as the original source of a historical value.

## What the audit establishes—and does not

- It makes the in-scope repository files, physical lines, source hints, legacy URLs, and review classifications searchable/downloadable.
- It flags legacy ESPN market/futures values and secondary historical datasets such as Spreadspoke/nflverse/Kaggle as not used for the current model.
- It distinguishes source-backed current facts from dated snapshots, derived outputs, implementation, rendered copy, and prior research claims.
- **It is not a fresh independent fetch of every legacy external URL, not proof that every historic numerical claim is correct, and not a certification of every source line.** The `audit_note`, `classification`, and `source_basis` matter; do not treat a generic official scope reference as row-level provenance.
- The canonical 2026 Week 1–9 result log is rechecked separately through the 32-team NFL standings reconciliation. That reconciliation does not validate old dashboards or old backtests.

The exact file/line counts and category/source-basis counts are generated in the JSON summary and shown on the [Repository Audit page](../../nfl-b34253a1/audit.html). The audit's input selection is fixed in `nfl-b34253a1/audit_repo.py` and is intentionally limited to this NFL scope; unrelated NBA/rental scopes are not certified or modified.

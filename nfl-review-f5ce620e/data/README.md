# Review data guide

This namespace is an independent, audit-only dossier. It does not edit or regenerate other desks, select a user policy, alter a model, or claim an approved odds feed.

- `sources.json` is the source register. Each source has a read window, publisher/source class, observation, scope limit, local note reference and status. `SRC-VEN-01`–`SRC-VEN-13` are one-to-one with the 13 Week 11 venue rows.
- `audit_findings.json` contains the line-level review findings. A finding marked `flagged: true` is unresolved, partial, blocked, or an important correction. `source_ids` resolve to the source register; `repo_evidence` paths are review pointers, not substitutes for official source URLs.
- `questions.json` and `suggestions.json` are review queues. Every suggestion is explicitly proposal-only and contains options, a recommendation, reasons on both sides, and evidence that could change the recommendation.
- `venues_week11.csv` preserves the official Game Center's location and stadium labels; it makes no roof/surface/weather inference.
- `results_increment_week10.csv` is a single game result delta, not a complete results feed.
- `manifest.json` hashes only `raw/official_reads_2026-11-18.md` and the two local CSV transcriptions. It does not hash live source pages or authenticate source-server bytes.

Empty, unknown, unverified or policy-blocked values are not imputed. External links are for manual review; CI does not fetch or scrape live sources.

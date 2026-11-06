# San Francisco Rent Increase Review (2026)

Static, GitHub Pages-compatible research site for the anonymized two-unit scenario. Public pages contain no real tenant names/initials or street address. User-supplied dates and rent amounts are preserved but explicitly labeled owner-reported and unverified; no unit-specific increase amount is calculated from them.

## Pages

- `index.html` — overview/dashboard
- `summary.html` — executive summary and answers
- `case-data.html` — anonymized reported facts
- `rules.html` — local/state/federal framework and calculations left blank when unsupported
- `practice.html` — owner process, fairness, expenses and legal-service scope
- `notice.html` — notice preflight checklist
- `flagged.html` — items requiring document/legal review
- `sources.html` — official source register

## Verification

Run from repository root:

```sh
python3 sf-rent-increase-2026/tests/verify_site.py
```

The validator checks local navigation/file targets, official-domain links in every factual table row, known-personal-information exclusion, required privacy and case markers, and all source links against the project's official-host allowlist. It does not substitute for legal review or verify private lease facts.

Research checked November 6, 2026. See the live source links on every page and `sources.html`. No case facts are represented as verified by a public agency.

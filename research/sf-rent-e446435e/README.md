# SF Rent Increase Compliance & Evidence Dashboard — Research (Session e446435e)

Scope: `research/sf-rent-e446435e/**` + `sf-rent-e446435e/**` (exclusive to session `e446435e`;
branch `arena/e446435e-own5`). All other repo paths are read-only for this session.

As-of date: **2026-11-06**. Property: **1940 two-unit residential building, Outer Sunset,
San Francisco, CA 94122** (ZIP 94122).

## Privacy / anonymization (binding)

Personal tenant identifiers supplied with the request are **internal only** and appear in
**zero** tracked files, commits, PRs, or public pages. This package uses placeholders:

| Placeholder | Meaning (dates/amounts preserved exactly) |
|---|---|
| Tenant Alpha | Continuing original co-tenant, Unit 1 |
| Tenant Beta, Tenant Gamma | Departed original co-tenants, Unit 1 |
| Tenant Delta | Replacement co-tenant, Unit 1 (continuing tenancy Apr 1, 2026) |
| Tenant Epsilon, Tenant Zeta | Original co-tenants, Unit 2 |
| Unit 1 | Reported: initial lease Feb 1, 2025 @ **$3,995.00/mo**; continuing tenancy Apr 1, 2026 @ **$3,995.00/mo** |
| Unit 2 | Reported: last lease start Jun 1, 2019 @ **$3,150.00/mo** |

Reported lease facts are **user-supplied inputs**, not independently verified facts. They are
labeled "reported" everywhere and gated by flags (see `FLAGGED.md`).

## Documents

| File | Contents |
|---|---|
| `EXECUTIVE_SUMMARY.md` | Anonymized executive brief answering every question asked |
| `ANALYSIS.md` | Full Q&A analysis: lawful ceilings, scenarios, notice procedure, corporate vs. individual practice, one-vs-both, scrutiny checklist |
| `SOURCES.md` | Primary-source register (official publishers only) with retrieval notes |
| `FLAGGED.md` | Nonblocking review register `R44-F01…F19` with source links |
| `REPO_AUDIT.md` | Bounded line-by-line repo audit record |
| `VERIFICATION.md` | Checks run and their results |

## How to read the site

Public dashboard: `sf-rent-e446435e/` → `https://sassnarep3-star.github.io/Own5/sf-rent-e446435e/`.
Every table row links to an official source; blank cells are **unverified, never zero**; every
blank carries a flag link to `flagged.html`. Dollar figures labeled **derived** are arithmetic
illustrations (`base × official %`, no compounding) gated by open flags — not lawful-rent
determinations. General educational information only, not legal advice; no notice should be
served until the blocking flags close and counsel reviews.

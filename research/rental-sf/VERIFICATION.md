# Verification Log — Rental Increase SF

**2026-11-06 (UTC), session 6ee577e4-own5.**

| Check | Result |
|---|---|
| Every external source fetched this session and content actually read | PASS — see SOURCES.md retrieval log |
| DOJ RealPage 2024-08-23 press release | FAILS (404 after site reorg) → replaced with archived 2025-01-07 release; logged as F-08-adjacent substitution |
| sf.gov banked vs worked-example banking tests | CONTRADICTION CONFIRMED on the official pages → flag F-02; no value beyond current-year 1.6% is asserted as settled |
| Arithmetic (all $ values) | Recomputed independently (3995×.016=63.92, …); additive-not-compound rule applied per S-05 |
| Table rows without official source | None — every legal/factual row links to S-01…S-22; unverifiable cells left BLANK |
| HTML parse + internal links for new `rental-sf/` pages | PASS (see tools run in COORDINATION.md log) |
| PII scan of new files | PASS — placeholders only; brief's names never written anywhere |
| Root `check_site.py` | Ran; 0 failures, 9 pre-existing intentional warnings — unchanged by this session |
| AB 1482 dollar cap | Derived (8.8%) and labeled derived — flag F-05 |
| 2027-28 rate | BLANK (not published) — flag F-04 |

**Not verified (and cannot be from this sandbox):** official construction records for the building; the
Rent Board's files for the two tenancies; whether a notice was served in 2026-04; current docket status
of DOJ v. RealPage; any current property-specific facts beyond the brief.

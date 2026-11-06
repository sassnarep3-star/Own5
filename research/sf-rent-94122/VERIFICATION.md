# Verification log — sf-rent-94122 (session e028ae77)

Date: 2026-11-06 (UTC). Method: official pages fetched and read via the web fetch tool; statute texts via leginfo/uscode; values transcribed verbatim.

| Check | Result | Source(s) |
|-------|--------|-----------|
| SF allowable increase 3/1/2026–2/28/2027 = 1.6% | PASS (news 2026-01-14, rent-increase page, current-rates table) | S01, S02, S04 |
| 3/1/2025–2/28/2026 = 1.4% (60% of 2.4% CPI-U, BLS Nov 2024) | PASS | S03, S04 |
| 3/1/2024–2/28/2025 = 1.7% | PASS | S04 |
| Formula = 60% of Bay Area CPI-U | PASS | S01–S03, S20 |
| Once per 12 months; anniversary date rules | PASS | S01, S16 |
| Base-rent-only calculation; no rounding up | PASS | S01 |
| Banking: ≥24 months to bank; additive not compounded; no expiry in tenancy; not carried to new tenant; since 4/1/1982 | PASS | S16 |
| Notice 30/90 days (+5 mailed); required contents; rate on effective date | PASS | S01, S16, S09 |
| Rent increase license / Housing Inventory prerequisite | PASS | S05, S01 |
| Coverage: units built on/before 6/13/1979 rent controlled | PASS (rule); unit-level status unverified → F03 | S06, S18 |
| No charge for additional occupants | PASS | S01 |
| Beyond-annual increases only via petition/passthrough | PASS | S17 |
| AB 1482 cap 5%+CPI≤10%, ≤2 increases/12mo, local-ordinance exemption | PASS | S10 |
| AB 1482 SF-region 8/1/2026–7/31/2027 = 8.8% (CPI 3.8%) | PASS vs county housing authority; not operative for these units → F12 | S19, S10 |
| Costa-Hawkins vacancy decontrol / exemptions | PASS | S12 |
| Civ. Code §827 30/90-day notice | PASS | S09 |
| Fixed-term lease: no mid-term increase unless lease allows | PASS | S15 |
| Federal: FHA §3604(b) protected classes; HUD enforcement; no federal rent cap | PASS (cap absence stated as blank-by-design, F11) | S13, S14 |
| Free SF tenant legal help: EDC 415-659-9184; Rent Board 415-252-4600; discrimination → SF HRC | PASS | S07, S08 |
| Site integrity | `verify.py` PASS: 8 pages, 20 sources, 54 rows, 12 flags, 0 broken links, 0 PII leaks; local serve 10/10 HTTP 200 | sf-rent-94122/verify.py |

Irregularities found during research: third-party sites showing 1.7% for 2026–27 conflict with official 1.6% (F10 — official value used). Unit 2's 2019 lease with unchanged reported rent implies possible skipped/banked increases — ledger unknown, not computed (F05).

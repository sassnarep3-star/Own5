# Flagged for Review — Session e446435e (nonblocking for merge; blocking for any notice)

Status **needs review** on every item. Each flag links to the official source governing it.
Site mirror: `sf-rent-e446435e/flagged.html`.

| ID | Severity | Issue | Finding / limitation | Scope | Sources |
|---|---|---|---|---|---|
| R44-F01 | High | Unit-by-unit rent-control coverage & exemptions unverified | 1940 build year + 2 units suggest coverage (Prop I/§37.12), but exemptions, condo conversion, substantial rehab, or owner-move-in history could change either unit. Confirm with Rent Board + license records. | Both units | S-11, S-12 |
| R44-F02 | High | Lawful base rents & rent histories unverified | $3,995.00 (Feb 2025 / Apr 2026) and $3,150.00 (Jun 2019) are user-supplied. Lawful base rent, interim increases, concessions, and fees need leases + receipts + Board records. All derived math assumes them arguendo. | Both units | S-04 |
| R44-F03 | High | Unit 1 Apr 1, 2026 agreement type unknown | Fixed-term vs. month-to-month, and any rent-increase clause, decides whether $0.00 is due until Apr 1, 2027 or an annual/banked increase is available. Lease review required. | Unit 1 | S-04 |
| R44-F04 | High | Banked balances unverified | Unit 2's 11.5% bank assumes zero increases since Jun 2019; Unit 1's 1.4% bank assumes none since Feb 2025/2026. Needs full payment history + anniversary accounting. | Both units | S-03, S-05, S-06 |
| R44-F05 | High | Housing Inventory license status unverified | Annual/banked increases without an active §37.15 license are void. Confirm at portal.sfrb.org before any notice. | Building | S-07, S-08 |
| R44-F06 | Medium | 2027–28 annual rate unannounced | Any scenario touching Mar 2027+ leaves the rate blank until the Board publishes it. | Both units | S-01, S-02 |
| R44-F07 | Medium | Bedroom counts unknown; 0BR SAFMR cell unconfirmed | Market-benchmark applicability per unit is blank. HUD 94122 SAFMRs verified for 1–4BR only. | Benchmarks | S-23, S-24 |
| R44-F08 | Low | HUD worksheet display quirks | Step 4 computes ZCTA SAFMR while Step 6 prints HMFA FMR; `br_size=2` 404s; `br_size=0` header-only. Benchmarks taken from successful worksheets only. | Benchmarks | S-23, S-24 |
| R44-F09 | Low | sf.gov explainer typos | "June 1, 2025 is 1.6%" and "August 1, 2024 (1.4%)" contradict Form 571 (1.4% for 2025–26; 1.7% for 2024–25). Form 571 governs here. | Rates | S-01, S-04, S-06 |
| R44-F10 | Low | Computed AB 1482 SF cap blank | Formula (5% + CPI, max 10%) verified; current-year CPI computation not verified this session. Moot: stricter local control governs. | State law | S-15, S-32 |
| R44-F11 | Medium | "Typical" corporate/individual increase behavior unverified | Private pricing norms have no official source. Institutional 10-K venues + algorithmic-pricing enforcement are verified context only. | Practice | S-25, S-26, S-27 |
| R44-F12 | High | Selectivity / discrimination / retaliation / harassment fact review | Any one-unit-only action needs objective timing locks + uniform written policy + 180-day retaliation clearance + counsel review before service. | Both units | S-17, S-18, S-20 |
| R44-F13 | High | Notice execution must be perfect | Personal delivery or mailed +5 days; 30/35 vs 90/95-day thresholds; full §37.3(b) itemization; proof of service. Site checklists are illustrative, not a served notice. | Process | S-03, S-14 |
| R44-F14 | Medium | Subsidy / voucher / federally-backed status unknown | §37.3(a)(10) voucher interplay and CARES §4024(c) covered-dwelling rules depend on unknown facts. | Both units | S-03, S-22 |
| R44-F15 | High | No lawyer review obtained | This is general educational information, not legal advice. No proposed increase has been reviewed by counsel for either side. | All | S-28, S-29 |
| R44-F16 | Low | Repo audit bounds; sibling single-line HTML | Audit is bounded (inventory + locks + scans + source re-verification), not a re-read of all 205 pages. Sibling `wc -l` zeroes are single-line files with verified bytes — not defects. Pre-existing unclosed-`<section`> notes belong to other sessions. | Repo | — (audit record: REPO_AUDIT.md) |
| R44-F17 | Medium | Anniversary-change & §6.14 edge cases need counseling | Non-anniversary effective dates change the anniversary and can forfeit banks; roommate/subtenancy edge cases need lease-specific review. Confirm with Rent Board counseling before serving. | Both units | S-06, S-09 |
| R44-F18 | Low | Remote-link availability not continuously monitored | Two PDFs failed direct fetch (petition form 516C; FY2024–25 statistical report) and are linked via verified index pages. Remote content may change; register records check date. | Sources | S-09, S-30 |
| R44-F19 | Medium | Petition-based adjustments are case-specific | Capital-improvement / substantial-rehab / operating-cost passthroughs require individual Board decisions; no amounts verified or projected here. | Both units | S-04, S-10 |

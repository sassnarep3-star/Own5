# Verification Record — Session e446435e (2026-11-06)

## Source verification (primary sources only)

- 32 official sources read on 2026-11-06 via direct page/PDF fetch and targeted official-site
  search (`sf.gov`, `leginfo.legislature.ca.gov`, `huduser.gov`, `hud.gov`, `justice.gov`,
  `sec.gov`, `calcivilrights.ca.gov`, `congress.gov`). Register + findings + limitations:
  `SOURCES.md` (S-01…S-32). No third-party publisher supplies any value on the site.
- Verbatim text confirmed for: Form 571 rate schedule; §37.3(a)/(b)/(d) operative clauses;
  Civ. Code §827(b)(1)–(3) service/timing rules; HUD FY2027 94122 SAFMR worksheet values
  (1BR $2,770; 2BR $3,410; 3BR $4,460; 4BR $5,020).

## Arithmetic verification (no compounding; percents sum; dollars = base × %)

- Unit 1 ($3,995.00): 1.4% = $55.93; 1.6% = $63.92; 3.0% = $119.85 → $4,114.85. All exact.
- Unit 2 ($3,150.00): 1.8% = $56.70; 0.7% = $22.05; 2.3% = $72.45; 3.6% = $113.40;
  1.7% = $53.55; 1.4% = $44.10; bank 11.5% = $362.25; +1.6% ($50.40) = 13.1% = $412.65 →
  $3,562.65. Annual-only: $3,200.40. All exact to the cent.
- Notice-date illustrations: mailed Nov 6, 2026 +35 days → Dec 11, 2026 (≤10%); +95 days →
  Feb 9, 2027 (>10%). Day-count illustrations only; service facts + anniversary effects gated
  by R44-F04/F13/F17.
- `sf-rent-e446435e/verify.py` recomputes every derived figure from `data/canonical.json`
  (Decimal, ROUND_HALF_UP) and fails on any mismatch.

## Automated checks (this scope)

- `python3 sf-rent-e446435e/build.py` — deterministic build of 11 pages + 4 CSV exports from
  `data/canonical.json`; fails on unknown source/flag IDs.
- `python3 sf-rent-e446435e/verify.py` — page/link/row/PII/math/CSV-consistency suite; requires
  FAIL=0 (see its output header for counts).
- PII scanner: spaced-initials patterns, e-mail/phone/SSN patterns with public-agency-number
  allowlist — must report zero hits across `sf-rent-e446435e/**` and
  `research/sf-rent-e446435e/**`.

## Repo-level checks (read-only; nothing outside scope modified)

- `python3 -m unittest discover -s tests` → 91/91 OK (pre-existing suite).
- `python3 tools/check_site.py` → 20 checks, 0 failures, 9 pre-existing intentional
  blank-source warnings (unchanged).
- Sibling scopes untouched; row/link/PII scans recorded in `REPO_AUDIT.md`.

## Bounds

Automated checks verify structure, link integrity, math, and PII absence — not remote-link
uptime, not legal correctness of any future notice, and not a substitute for counsel review
(R44-F15, R44-F18).

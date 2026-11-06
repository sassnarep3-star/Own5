#!/usr/bin/env python3
"""Deterministic build for the SF 94122 rental-increase review subsite.

Generates sf-rent-94122/data/*.csv and sf-rent-94122/*.html from the verified
data structures below. No external assets, no network, no manual input.
Every factual row carries an official source id that resolves in sources.csv.
Unverifiable values are left BLANK and cross-referenced on the Flagged page.
"""
import csv
import html
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

CHECKED = "2026-11-06"

SOURCES = [
    # id, publisher, title, url, what it verifies
    ("S01", "City & County of San Francisco — Rent Board (sf.gov)", "Learn about rent increases in San Francisco",
     "https://www.sf.gov/learn-about-rent-increases-san-francisco",
     "1.6% allowable increase 3/1/2026–2/28/2027; 60% of Bay Area CPI-U; once per 12 months; anniversary date; base-rent-only calculation, no rounding up; 30/90-day notice (+5 days mailed) and required notice contents; rate in effect on effective date; rent increase license; no rent charge for additional occupants; vacancy decontrol; worked examples."),
    ("S02", "City & County of San Francisco (sf.gov News, 2026-01-14)", "Annual Rent Increase for 3/1/26 - 2/28/27 Announced",
     "https://www.sf.gov/news--annual-rent-increase-3126-22827-announced",
     "1.6% for rent-controlled units effective 3/1/2026–2/28/2027; $2,000 × .016 = $32.00 worked example; prior period (3/1/2025–2/28/2026) 1.4%."),
    ("S03", "City & County of San Francisco (sf.gov News, 2024-11-19)", "Annual Rent Increase for 3/1/25 - 2/28/26 Announced",
     "https://www.sf.gov/news--annual-rent-increase-3125-22826-announced",
     "1.4% effective 3/1/2025–2/28/2026, based on 60% of the 2.4% Bay Area CPI-U increase posted Nov 2024 by BLS; prior period 1.7%."),
    ("S04", "City & County of San Francisco — Rent Board (sf.gov)", "Current Rates, including Rent Increase, Relocation, Sec. Deposit",
     "https://www.sf.gov/reports--current-rates-including-rent-increase-relocation-sec-deposit",
     "Rate table: 1.6% (3/1/2026–2/28/2027), 1.4% (3/1/2025–2/28/2026), 1.7% (3/1/2024–2/28/2025); security deposit interest 4.2% for 3/1/2026–2/28/2027; historical '571 Allowable Annual Increases' schedule."),
    ("S05", "City & County of San Francisco (sf.gov)", "The Rent Board Housing Inventory",
     "https://www.sf.gov/rent-board-housing-inventory",
     "Owners must report into the Housing Inventory and hold a current rent increase license before any annual or banked increase goes into effect; notice not enforceable without a license on the effective date."),
    ("S06", "City & County of San Francisco (sf.gov)", "Learn about San Francisco rental laws",
     "https://www.sf.gov/learn-about-san-francisco-rental-laws/",
     "Many residential units built on or before June 13, 1979 have rent control AND just-cause eviction protection; post-6/13/1979 units, most single-family homes/condos exempt from rent limits; check building year via the Property Information Map."),
    ("S07", "City & County of San Francisco (sf.gov)", "Evictions in San Francisco",
     "https://www.sf.gov/evictions-san-francisco",
     "Rent Board at 415-252-4600; tenants served an Unlawful Detainer should contact the Eviction Defense Collaborative at 415-659-9184 for free legal help."),
    ("S08", "City & County of San Francisco — Rent Board (sf.gov)", "About Rent Board",
     "https://www.sf.gov/departments--rent-board--about",
     "Free phone/drop-in counseling 415-252-4600; Rent Board cannot arbitrate discrimination or retaliation — those go to the SF Human Rights Commission."),
    ("S09", "California Legislative Information (leginfo)", "Civil Code § 827 — notice of rent increase",
     "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=827.",
     "Statewide written-notice statute: at least 30 days for increases of 10% or less of the lowest rent in the prior 12 months; at least 90 days above 10%."),
    ("S10", "California Legislative Information (leginfo)", "Civil Code § 1947.12 — Tenant Protection Act (AB 1482) rent cap",
     "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=1947.12.",
     "Statewide cap: no more than 5% + regional CPI change, max 10%, in any 12-month period; max two increases per 12 months; exempts housing subject to a more restrictive local rent ordinance (SF Rent Ordinance qualifies); no limit on initial rent for a vacant unit."),
    ("S11", "California Legislative Information (leginfo)", "Civil Code § 1946.2 — Tenant Protection Act just-cause eviction",
     "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=1946.2.",
     "AB 1482 just-cause eviction protections for covered tenancies."),
    ("S12", "California Legislative Information (leginfo)", "Civil Code § 1954.50 et seq. — Costa-Hawkins Rental Housing Act",
     "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=CIV&sectionNum=1954.50.",
     "Statewide vacancy decontrol (owner may set initial rent for a new tenancy); exempts post-2/1/1995 construction and separately alienable single-family homes/condos from local rent caps; local ordinances otherwise remain in force."),
    ("S13", "Office of the Law Revision Counsel, U.S. House (uscode.house.gov)", "42 U.S.C. § 3604 — Fair Housing Act prohibited practices",
     "https://uscode.house.gov/view.xhtml?req=(title:42%20section:3604%20edition:prelim)",
     "Federal law makes it unlawful to discriminate in the terms, conditions, or privileges of rental of a dwelling because of race, color, religion, sex, familial status, national origin, or disability (§ 3604(b))."),
    ("S14", "U.S. Department of Housing and Urban Development (hud.gov)", "Fair Housing — HUD FHEO",
     "https://www.hud.gov/program_offices/fair_housing_equal_opp",
     "HUD enforces the federal Fair Housing Act (42 U.S.C. §§ 3601–3619); seven federally protected classes."),
    ("S15", "Judicial Council of California (courts.ca.gov)", "California Tenants — official guide (PDF)",
     "https://www4.courts.ca.gov/documents/California-Tenants-Guide.pdf",
     "For a fixed-term lease the landlord cannot raise rent during the term unless the rental agreement expressly allows it; AB 1482 cap 5% + CPI or 10% whichever lower; notice rules."),
    ("S16", "City & County of San Francisco — Rent Board (sf.gov)", "Banked rent increases",
     "https://www.sf.gov/information--banked-rent-increases",
     "A skipped annual increase is banked only if at least 24 full months pass without any increase; no limit on banked amount; banked increases do not expire, are added (not compounded/prorated), carry to new owners, and do NOT carry to a new tenant; banking allowed only since 4/1/1982; license + 30/90-day notice required."),
    ("S17", "City & County of San Francisco — Rent Board (sf.gov)", "Landlord Petitions and Passthroughs",
     "https://sf.gov/landlord-petitions-and-passthroughs",
     "Increases beyond the annual allowable amount require a Rent Board petition/passthrough (capital improvement, operating & maintenance, comparable-rent special circumstances, Prop I history, utility passthrough, bond passthrough worksheets); tenant need not pay until approved."),
    ("S18", "SF Planning Department (sf.gov PIM)", "Property Information Map",
     "https://sfplanninggis.org/PIM/",
     "Official tool to look up a building's year built / certificate of occupancy to confirm rent-control coverage."),
    ("S19", "Contra Costa County Housing Authority (government housing authority)", "AB 1482: The California Tenant Protection Act of 2019",
     "https://contracostaha.org/ab-1482-the-california-tenant-protection-act-of-2019/",
     "For increases effective 8/1/2026–7/31/2027 the applicable CPI is 3.8%, so the AB 1482 maximum is 8.8% (5% + 3.8%) for the SF-Oakland-Hayward region; restates § 1947.12 rules. NOTE: not the operative cap for SF rent-controlled units (S10 exemption)."),
    ("S20", "U.S. Bureau of Labor Statistics (bls.gov)", "Consumer Price Index (CPI-U)",
     "https://www.bls.gov/cpi/",
     "Publisher of the CPI-U data the SF Rent Board and AB 1482 use in their formulas."),
]

# layer, id, topic, finding/value, status, source ids
LAWS = [
    ("Local — SF Rent Ordinance (Admin. Code ch. 37)", "L01", "Rent-control coverage",
     "Many residential units built on or before June 13, 1979 have rent control AND just-cause eviction protection. A building built in 1940 falls inside this window; unit-level exemptions (e.g., single-family use, substantial rehabilitation) must still be checked.",
     "Verified (rule); unit-level coverage unverified — see F03", "S06,S18"),
    ("Local — SF Rent Ordinance", "L02", "Allowable annual increase 3/1/2026–2/28/2027", "1.6% of base rent",
     "Verified", "S01,S02,S04"),
    ("Local — SF Rent Ordinance", "L03", "Allowable annual increase 3/1/2025–2/28/2026", "1.4% of base rent",
     "Verified", "S03,S04"),
    ("Local — SF Rent Ordinance", "L04", "Allowable annual increase 3/1/2024–2/28/2025", "1.7% of base rent",
     "Verified", "S04"),
    ("Local — SF Rent Ordinance", "L05", "Rate formula", "60% of the increase in the CPI-U for All Urban Consumers, Bay Area (published by BLS)",
     "Verified", "S01,S02,S03,S20"),
    ("Local — SF Rent Ordinance", "L06", "Frequency / anniversary date",
     "Rent may be increased only once every 12 months; the effective date of an increase becomes the new anniversary date.",
     "Verified", "S01,S16"),
    ("Local — SF Rent Ordinance", "L07", "Calculation base",
     "Increase is calculated on base rent only (incl. housing services such as parking/storage; excl. temporary passthroughs); increases cannot be rounded up to the nearest dollar.",
     "Verified", "S01"),
    ("Local — SF Rent Ordinance", "L08", "Banked (skipped) increases",
     "A skipped increase is banked only after at least 24 full months without any increase; no cap on banked total; banked percentages are added, never compounded or prorated; they do not expire during a tenancy, transfer to new owners, but do not carry to a new tenant; banking exists only since 4/1/1982.",
     "Verified (rule); per-unit banked ledger unverified — see F05", "S16"),
    ("Local — SF Rent Ordinance", "L09", "Notice of increase",
     "30-day written notice; 90-day written notice if the increase, alone or combined with another increase in the same year, exceeds 10%; +5 days if mailed. Notice should state dollar amount, percentage, effective date, and which part is banked.",
     "Verified", "S01,S16,S09"),
    ("Local — SF Rent Ordinance", "L10", "Rate to apply",
     "Use the percentage in effect on the effective date of the increase, not the percentage in effect when the notice is served.",
     "Verified", "S01,S16"),
    ("Local — SF Rent Ordinance", "L11", "Rent increase license",
     "Landlord must have reported into the Rent Board Housing Inventory and hold a current rent increase license before any annual or banked increase can go into effect.",
     "Verified (rule); owner's license status unverified — see F06", "S05,S01,S16"),
    ("Local — SF Rent Ordinance", "L12", "Vacancy decontrol",
     "There is no limit on the rent a landlord may first charge when renting an empty rent-controlled unit; the cap attaches to the new tenancy.",
     "Verified", "S01,S12"),
    ("Local — SF Rent Ordinance", "L13", "Additional occupants",
     "A landlord cannot charge additional rent merely because a new/additional roommate moves in with an existing tenant — an unlawful rent increase even if the lease says otherwise.",
     "Verified", "S01"),
    ("Local — SF Rent Ordinance", "L14", "Increases beyond the annual amount",
     "Only via Rent Board petition / passthrough (capital improvements, operating & maintenance, comparable-unit special circumstances, Prop I history, utility passthroughs, bond passthrough worksheets). Tenants need not pay until the Rent Board approves.",
     "Verified", "S17"),
    ("Local — SF Rent Ordinance", "L15", "Eviction protection",
     "Just-cause eviction protection applies to covered units; no-fault evictions have additional rules and relocation assistance.",
     "Verified", "S06,S07"),
    ("Local — SF Rent Ordinance", "L16", "Security deposit interest 3/1/2026–2/28/2027", "4.2%",
     "Verified", "S04"),
    ("State — AB 1482 (Civ. Code § 1947.12)", "T01", "Statewide rent cap",
     "Max increase in any 12-month period = 5% + regional CPI change, capped at 10%; max two increases per 12 months. Units subject to a MORE restrictive local ordinance (SF's is) are exempt — the SF Rent Ordinance cap controls these units.",
     "Verified", "S10"),
    ("State — AB 1482", "T02", "SF-region AB 1482 ceiling 8/1/2026–7/31/2027", "8.8% (5% + 3.8% CPI)",
     "Verified vs government housing authority page; NOT applicable to these rent-controlled units — see F12", "S19,S10"),
    ("State — AB 1482 (Civ. Code § 1946.2)", "T03", "Just-cause eviction (statewide)", "Just cause required to terminate covered tenancies after 12/24 months of occupancy.",
     "Verified", "S11"),
    ("State — Costa-Hawkins (Civ. Code §§ 1954.50–1954.535)", "T04", "Limits on local rent control",
     "Guarantees vacancy decontrol; prohibits local caps on post-2/1/1995 construction and on single-family homes/condos (with exceptions, incl. corporate owners under AB 1482); SF's pre-1979 coverage remains valid.",
     "Verified", "S12"),
    ("State — Civ. Code § 827", "T05", "Notice statute", "Written notice: ≥30 days if increase ≤10% of lowest rent in prior 12 months; ≥90 days if >10%.",
     "Verified", "S09"),
    ("State — lease terms", "T06", "Fixed-term lease", "Rent cannot be raised during a fixed-term lease unless the rental agreement expressly allows it.",
     "Verified", "S15"),
    ("Federal — Fair Housing Act (42 U.S.C. §§ 3601–3619)", "F01", "Anti-discrimination",
     "Unlawful to discriminate in the terms, conditions, or privileges of rental because of race, color, religion, sex, familial status, national origin, or disability. Consistent, uniformly applied rent policies are the defensible practice.",
     "Verified", "S13,S14"),
    ("Federal", "F02", "Federal rent cap", "BLANK — no federal statute imposes a cap on rent increases; federal housing law (FHA) regulates discrimination, not amounts.",
     "Blank by design (no official source sets a federal cap); flagged F11", "S13,S14"),
    ("Federal — HUD", "F03", "Enforcement", "HUD's Office of Fair Housing and Equal Opportunity enforces the FHA.",
     "Verified", "S14"),
]

# unit, field, value, status/derivation, sources
UNITS = [
    ("Unit 1", "Location", "Outer Sunset, San Francisco, CA 94122 (user-provided)", "User-provided, unverified. The SF annual allowance is citywide; no official ZIP-specific rate exists.", "S01"),
    ("Unit 1", "Building year built", "1940 (user-provided)", "User-provided, unverified; inside the on/before 6/13/1979 rent-control window — see F03 for unit-level confirmation.", "S06,S18"),
    ("Unit 1", "Initial lease start", "February 1, 2025 @ $3,995/month (user-provided)", "User-provided, unverified input; dates and amounts retained per instructions.", "S01"),
    ("Unit 1", "Initial lease tenants", "Tenant A, Tenant B, Tenant C (placeholder names — real identities withheld)", "Anonymized per privacy requirement; internal only.", ""),
    ("Unit 1", "Continuing tenancy", "April 1, 2026 @ $3,995/month — Tenant A and Tenant D (placeholders)", "User-provided, unverified. Household change from 3 to 2 occupants: charging more for the change is an unlawful increase (L13); succession effect unverified — see F04.", "S01"),
    ("Unit 1", "Illustrative annual increase at current 1.6% (derived arithmetic on unverified base)", "$3,995 × 0.016 = $63.92 → $4,058.92/month", "DERIVED from user-provided base; NOT a verified lawful amount. If April 1, 2026 was the last rent event, the next increase cannot take effect before April 1, 2027 and the 3/1/2027–2/28/2028 rate is unpublished — see F07.", "S01,S02"),
    ("Unit 2", "Location", "Outer Sunset, San Francisco, CA 94122 (user-provided)", "User-provided, unverified.", "S01"),
    ("Unit 2", "Building year built", "1940 (user-provided)", "User-provided, unverified; inside rent-control window — see F03.", "S06,S18"),
    ("Unit 2", "Last lease start", "June 1, 2019 @ $3,150/month (user-provided)", "User-provided, unverified input.", "S01"),
    ("Unit 2", "Tenants", "Tenant E and Tenant F (placeholder names — real identities withheld)", "Anonymized per privacy requirement; internal only.", ""),
    ("Unit 2", "Illustrative annual increase on June 1, 2026 anniversary at current 1.6% (derived arithmetic on unverified base)", "$3,150 × 0.016 = $50.40 → $3,200.40/month", "DERIVED from user-provided base; NOT a verified lawful amount. June 1, 2026 falls in the 3/1/2026–2/28/2027 window (1.6%). Any banked increases from skipped years are NOT computed — rent ledger unknown — see F05.", "S01,S02,S16"),
]

QA = [
    ("Q1", "What is a reasonable and normal rental increase in SF 94122 under local, state, and federal law?",
     "For these rent-controlled (1940 building) units the LOCAL cap controls: the annual allowable increase set by the SF Rent Board — 1.6% for effective dates 3/1/2026–2/28/2027, 1.4% for 3/1/2025–2/28/2026 — applied once per 12 months on the anniversary date. 'Normal' practice is exactly this published CPI-linked annual adjustment. The STATE AB 1482 ceiling (8.8% for the SF region, 8/1/2026–7/31/2027) does not apply because SF's local ordinance is more restrictive. FEDERAL law sets no rent cap; it prohibits discrimination. Market-rent comparables for 94122 are BLANK — no official source verified — see F08.",
     "S01,S02,S04,S10,S19,S13"),
    ("Q2", "How do big real estate corporations vs individual owners handle increases in SF?",
     "The Rent Ordinance applies the SAME caps, notice, anniversary, banking, and license rules to every owner — the official sources reviewed draw no distinction between corporate and individual landlords for rent-controlled units. (AB 1482 does distinguish corporate ownership only for single-family/condo exemptions, irrelevant here.) Any claim about typical corporate vs individual practice percentages is BLANK — no official source verified — see F09.",
     "S01,S05,S10,S12"),
    ("Q3", "What is the correct way to inform tenants of a rent increase?",
     "Written notice at least 30 days before the effective date (90 days if the increase, alone or combined with another in the same year, exceeds 10%; +5 days if mailed). Notice should state the dollar amount, the percentage, the effective date, and any banked portion; use the rate in effect on the effective date. The owner must hold a current rent increase license (Housing Inventory reporting) before the increase can take effect. No increase during a fixed-term lease unless the lease allows it.",
     "S01,S16,S05,S09,S15"),
    ("Q4", "What are reasonable reasons for a rent increase?",
     "The annual allowable increase itself requires no additional justification — it is the lawful standard adjustment. Anything beyond it requires a Rent Board petition/passthrough (capital improvements, operating & maintenance, utility/bond passthroughs, comparable-rent special circumstances). Charging more because a roommate moved in is expressly unlawful; increases cannot be rounded up.",
     "S01,S17"),
    ("Q5", "Can the increase pass review by an SF tenant lawyer / free tenant legal services?",
     "Yes if it stays within the verified rules above: correct rate for the effective date, 12-month spacing, valid license, proper written notice, base-rent-only math, correct handling of any banked amounts. Free help exists in SF: Eviction Defense Collaborative 415-659-9184 (free legal help for tenants), Rent Board counseling 415-252-4600, and the SF Human Rights Commission for discrimination/retaliation. This site is not legal advice and cannot substitute for attorney review — see F11.",
     "S07,S08,S01"),
    ("Q6", "Raise one unit's rent or both — discrimination risk?",
     "No law requires raising both units, and raising both is not a 'safe harbor'. The defensible approach is a uniform, documented policy: apply the same lawful annual allowable increase to every covered unit on its own anniversary date, with identical notice procedures. Selectively targeting one household because of a protected class (race, color, religion, sex, familial status, national origin, disability) or in retaliation is unlawful under the federal Fair Housing Act; discrimination complaints in SF go to the Human Rights Commission. Evaluate each tenancy's lawful rent history independently.",
     "S13,S14,S08,S01"),
]

FLAGGED = [
    ("F01", "High", "Tenant personal information", "Real tenant names/initials are withheld from all published pages; placeholder names (Tenant A–F) are used. Dates and dollar amounts are retained as provided. Personal information stays internal only.", "Privacy requirement (user instruction)"),
    ("F02", "High", "User-provided unit facts unverified", "Rents ($3,995; $3,150), lease dates (2/1/2025, 4/1/2026, 6/1/2019), building year (1940), and ZIP 94122 come from the user and could not be confirmed against an official source; they are labeled user-provided wherever shown.", "S01 (rules applied), no official record source"),
    ("F03", "High", "Unit-level rent-control coverage", "1940 construction is consistent with coverage (units built on/before 6/13/1979), but exemptions (single-family use, substantial rehabilitation, subsidized) are unit-specific. Confirm each unit via the Property Information Map / Rent Board counselor.", "S06,S18"),
    ("F04", "Medium", "Unit 1 tenant succession", "Initial lease had 3 occupants; continuing tenancy has 2. The legal effect of the household change on the anniversary date / base rent needs lease records and counsel review. Charging extra for the roommate change is unlawful.", "S01"),
    ("F05", "High", "Rent ledger and banked increases unknown", "Whether annual increases were imposed each year (esp. Unit 2 since 6/1/2019) is unknown. Banked increases require ≥24 months without any increase, are added not compounded, and do not carry to new tenants. No banked amount is calculated here.", "S16"),
    ("F06", "High", "Rent increase license / Housing Inventory status", "Unknown whether the owner has reported to the Housing Inventory and holds a current rent increase license; without it on the effective date the increase notice is unenforceable.", "S05"),
    ("F07", "Medium", "3/1/2027–2/28/2028 rate unpublished", "The rate for increases effective on/after March 1, 2027 has not been announced; any Unit 1 increase effective April 1, 2027 would use that future rate. Cell left blank.", "S02,S04"),
    ("F08", "Medium", "94122 market-rent comparables", "BLANK — no official government source for Outer Sunset market rents was verified; no market-based 'normal' percentage is claimed.", "none (left blank)"),
    ("F09", "Medium", "Corporate vs individual owner practice norms", "BLANK — no official source verifies typical practice differences between corporate and individual landlords in SF; only the equal legal treatment could be verified.", "S01,S10"),
    ("F10", "Low", "Conflicting third-party figures", "Some non-official sites show 1.7% for 2026–27; the official SF Rent Board pages state 1.6% for 3/1/2026–2/28/2027. The official value is used.", "S02,S04"),
    ("F11", "High", "Not legal advice", "This is a research brief, not legal advice or a tenant-lawyer approval. Have any actual notice reviewed by a tenant-rights attorney before serving; free SF services listed on the Questions page.", "S07,S08"),
    ("F12", "Low", "AB 1482 regional figure source", "The 8.8% SF-region figure for 8/1/2026–7/31/2027 comes from a county housing authority page (formula from § 1947.12); it does not apply to these rent-controlled units because the stricter local ordinance controls.", "S10,S19"),
]

NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("units.html", "Units"),
    ("law.html", "Law & caps"),
    ("process.html", "Process & notice"),
    ("questions.html", "Questions"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
]

S = {s[0]: s for s in SOURCES}

def e(v):
    return html.escape("" if v is None else str(v), quote=True)

def refs(ids):
    ids = [i.strip() for i in ids.split(",") if i.strip()]
    if not ids:
        return '<span class="refs none">internal / anonymization note</span>'
    return '<span class="refs">' + " ".join(
        f'<a href="{e(S[i][3])}" target="_blank" rel="noopener noreferrer" title="{e(S[i][1])} — {e(S[i][0])}">{e(i)} ↗</a>'
        for i in ids) + "</span>"

def write_csv(name, header, rows):
    with open(DATA / name, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def table(headers, rows, tid):
    head = "".join(f'<th scope="col">{e(h)}</th>' for h in headers)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    return (f'<section class="panel"><div class="table-wrap"><table id="{e(tid)}">'
            f'<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div></section>')

def page(title, active, main):
    parts = []
    for h, t in NAV:
        if h == active:
            parts.append(f'<a href="{e(h)}" class="active" aria-current="page">{e(t)}</a>')
        else:
            parts.append(f'<a href="{e(h)}">{e(t)}</a>')
    nav = "".join(parts)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Anonymized, source-linked review of reasonable rental increases for two rent-controlled units in San Francisco's Outer Sunset (94122).">
<title>{e(title)} · SF 94122 Rental Increase Review</title>
<link rel="stylesheet" href="style.css"></head>
<body>
<header><div class="wrap"><div class="eyebrow">RENTAL INCREASE REVIEW · SAN FRANCISCO, CA 94122 · AS OF 2026-11-06</div>
<h1>{e(title)}</h1>
<nav aria-label="Main navigation">{nav}</nav></div></header>
<main class="wrap">{main}
<footer><div class="wrap">Personal information anonymized (placeholder tenants only); dates and amounts retained as user-provided and marked unverified. Blank cells = unverified, never inferred. Not legal advice.
Companion brief: <a href="../rental-increase-sf/index.html">rental-increase-sf/</a> (session 7659538a) ·
<a href="https://github.com/sassnarep3-star/Own5" target="_blank" rel="noopener noreferrer">Repository ↗</a></div></footer>
</main></body></html>'''

def build():
    write_csv("sources.csv", ["id", "publisher", "title", "url", "verified_finding", "checked"],
              [(s[0], s[1], s[2], s[3], s[4], CHECKED) for s in SOURCES])
    write_csv("laws.csv", ["layer", "id", "topic", "finding", "status", "sources"], LAWS)
    write_csv("units.csv", ["unit", "field", "value", "status_derivation", "sources"], UNITS)
    write_csv("qa.csv", ["id", "question", "answer", "sources"], QA)
    write_csv("flagged.csv", ["id", "severity", "item", "detail", "source"], FLAGGED)

    # ---- index ----
    idx_main = f'''
<section class="callout"><b>Bottom line.</b> Both units sit in a 1940 building, inside San Francisco's rent-control window (units built on or before June 13, 1979). For covered units the lawful annual increase is the Rent Board's published allowance — <strong>1.6% for effective dates March 1, 2026 – February 28, 2027</strong> — once every 12 months, on the tenant's anniversary date, with proper written notice and a current rent increase license. {refs("S01,S02,S04,S05")}</section>
<div class="cards">
<article><span>Current annual allowance (SF)</span><b>1.6%</b><small>effective 3/1/2026–2/28/2027 · 60% of Bay Area CPI-U</small>{refs("S01,S02")}</article>
<article><span>Prior allowances</span><b>1.4% / 1.7%</b><small>3/1/2025–2/28/2026 / 3/1/2024–2/28/2025</small>{refs("S03,S04")}</article>
<article><span>Unit 1 reported base rent</span><b>$3,995</b><small>user-provided, unverified · continuing tenancy reported 4/1/2026</small></article>
<article><span>Unit 2 reported base rent</span><b>$3,150</b><small>user-provided, unverified · lease start reported 6/1/2019</small></article>
<article><span>State cap (not operative here)</span><b>8.8%</b><small>AB 1482, SF region, 8/1/2026–7/31/2027 — local ordinance is stricter and controls</small>{refs("S10,S19")}</article>
<article><span>Open review items</span><b>{len(FLAGGED)}</b><small><a href="flagged.html">Flagged for review ↗</a></small></article>
</div>
<section class="panel"><h2>How to use this site</h2>
<p>Start with the <a href="executive-summary.html">Executive summary</a>, then <a href="units.html">Units</a> (anonymized facts and derived arithmetic), <a href="law.html">Law &amp; caps</a> (local/state/federal layers, every row source-linked), <a href="process.html">Process &amp; notice</a>, the <a href="questions.html">Answers</a> to your six questions, the <a href="sources.html">Sources</a> register, and the <a href="flagged.html">Flagged for review</a> page listing everything that could not be verified from an official source.</p></section>'''
    (ROOT / "index.html").write_text(page("Rental increase review — Outer Sunset 94122", "index.html", idx_main), encoding="utf-8")

    # ---- executive summary ----
    es_main = f'''
<section class="panel"><h2>Executive summary</h2>
<p><b>Scope.</b> Two units in one 1940 building in San Francisco's Outer Sunset (ZIP 94122), both reported as rent controlled. Unit 1: initial lease February 1, 2025 at $3,995/month (three occupants, anonymized); continuing tenancy April 1, 2026 at $3,995/month (two occupants). Unit 2: lease started June 1, 2019 at $3,150/month (two occupants). All tenant identities are anonymized on this site; dates and amounts are retained exactly as provided and flagged as user-provided/unverified.</p>
<p><b>Law.</b> Because the building predates June 13, 1979, the SF Rent Ordinance applies (unit-level confirmation still required). The only ordinary in-tenancy increase is the annual allowable increase: <b>1.6%</b> for effective dates 3/1/2026–2/28/2027 (60% of Bay Area CPI-U), once per 12 months on the anniversary date, calculated on base rent only, no rounding up. {refs("S01,S02,S06")} Skipped increases may be "banked" only after 24 full months without any increase, are added not compounded, and never carry to a new tenant. {refs("S16")} Anything beyond the annual amount requires a Rent Board petition/passthrough. {refs("S17")} State AB 1482 (5% + CPI, max 10%; 8.8% in the SF region for 8/1/2026–7/31/2027) does not apply because the local ordinance is stricter; Costa-Hawkins guarantees vacancy decontrol only. {refs("S10,S19,S12")} Federal law sets no rent cap and prohibits discrimination in rental terms based on protected classes. {refs("S13,S14")}</p>
<p><b>Notice.</b> Written notice ≥30 days before the effective date (90 days if the increase exceeds 10% alone or combined in the same year; +5 days if mailed), stating dollar amount, percentage, effective date, and any banked portion, using the rate in effect on the effective date; a current rent increase license (Housing Inventory) must be on file. No increase during a fixed-term lease unless the lease allows it. {refs("S01,S16,S05,S09,S15")}</p>
<p><b>Reasonableness.</b> The defensible, "normal" increase for both units is the published annual allowance applied uniformly on each unit's own anniversary date — not a market-based figure (market comps for 94122 could not be verified from an official source and are left blank). Raising one unit is lawful; raising both is not required and is not a safe harbor. Uniform, documented treatment avoids disparate-treatment risk under the federal Fair Housing Act. {refs("S01,S13,S14")} Charging extra for Unit 1's roommate change is expressly unlawful. {refs("S01")}</p>
<p><b>Review.</b> Any notice should be scrubbed by a tenant-rights lawyer before service; SF offers free help (Eviction Defense Collaborative 415-659-9184; Rent Board counseling 415-252-4600; discrimination → SF Human Rights Commission). See <a href="flagged.html">Flagged for review</a> for all unverified items (coverage, ledger/banking, license, future rate, market data). {refs("S07,S08")}</p></section>'''
    (ROOT / "executive-summary.html").write_text(page("Executive summary", "executive-summary.html", es_main), encoding="utf-8")

    # ---- units ----
    u_rows = [[f"<b>{e(r[0])}</b>", e(r[1]), e(r[2]), e(r[3]), refs(r[4])] for r in UNITS]
    units_main = f'''<section class="panel"><p>Placeholder tenant names only — personal information is anonymized. "User-provided" values are kept exactly as supplied and are not confirmed by any official source. "Derived" arithmetic is shown for illustration on the unverified base and is <b>not</b> a verified lawful amount.</p></section>
{table(["Unit", "Field", "Value", "Status / derivation", "Sources"], u_rows, "units")}'''
    (ROOT / "units.html").write_text(page("Units — anonymized facts", "units.html", units_main), encoding="utf-8")

    # ---- law ----
    l_rows = [[e(r[0]), f'<span class="rid">{e(r[1])}</span><b>{e(r[2])}</b>', e(r[3]), e(r[4]), refs(r[5])] for r in LAWS]
    law_main = f'''<section class="panel"><p>Three layers govern: <b>local</b> (SF Rent Ordinance — controls here), <b>state</b> (AB 1482 / Costa-Hawkins / Civ. Code § 827 / lease terms), <b>federal</b> (Fair Housing Act — no rent cap, anti-discrimination). Every row links to the official source(s) checked on {CHECKED}.</p></section>
{table(["Layer", "ID / topic", "Finding / value", "Status", "Sources"], l_rows, "laws")}'''
    (ROOT / "law.html").write_text(page("Law & caps — local / state / federal", "law.html", law_main), encoding="utf-8")

    # ---- process ----
    proc_main = f'''
<section class="panel"><h2>Compliant rent-increase checklist (rent-controlled units)</h2>
<ol>
<li><b>Confirm coverage</b> of each unit (Property Information Map / Rent Board counselor). {refs("S06,S18")}</li>
<li><b>Confirm the lawful base rent and rent ledger</b>, including every prior increase and any banked amounts (banked only after ≥24 months without an increase; added, not compounded; not carried to new tenants). {refs("S16")}</li>
<li><b>Confirm the anniversary date</b> and that at least 12 months have passed since the last increase. {refs("S01")}</li>
<li><b>Hold a current rent increase license</b> (Housing Inventory reporting) before the increase takes effect. {refs("S05")}</li>
<li><b>Use the rate in effect on the effective date</b> — 1.6% for 3/1/2026–2/28/2027. {refs("S01,S02")}</li>
<li><b>Calculate on base rent only</b>; do not round up. {refs("S01")}</li>
<li><b>Serve written notice</b> ≥30 days ahead (90 days if &gt;10% alone or combined in the same year; +5 days if mailed), stating dollar amount, percentage, effective date, and banked portion. {refs("S01,S16,S09")}</li>
<li><b>Never raise rent mid-term</b> on a fixed-term lease unless the lease allows it. {refs("S15")}</li>
<li><b>Never charge for additional occupants.</b> {refs("S01")}</li>
<li><b>For anything beyond the annual amount</b>, file the Rent Board petition/passthrough first. {refs("S17")}</li>
<li><b>Keep records</b> (ledger, lease, license, calculation, notice, delivery proof) and <b>apply the same policy uniformly</b> to all units; have a tenant-rights attorney review before serving. {refs("S13,S07,S08")}</li>
</ol></section>'''
    (ROOT / "process.html").write_text(page("Process & notice — correct procedure", "process.html", proc_main), encoding="utf-8")

    # ---- questions ----
    q_rows = [[f'<span class="rid">{e(r[0])}</span><b>{e(r[1])}</b>', e(r[2]), refs(r[3])] for r in QA]
    qa_main = f'<section class="panel"><p>Answers to the six questions, each linked to official sources. Items that could not be verified from an official source are stated as BLANK and cross-listed on <a href="flagged.html">Flagged for review</a>.</p></section>{table(["Question", "Answer", "Sources"], q_rows, "qa")}'
    (ROOT / "questions.html").write_text(page("Questions & answers", "questions.html", qa_main), encoding="utf-8")

    # ---- sources ----
    s_rows = [[f'<span class="rid">{e(r[0])}</span>', e(r[1]), f'<b>{e(r[2])}</b>', e(r[4]), e(CHECKED),
               f'<a href="{e(r[3])}" target="_blank" rel="noopener noreferrer">Official link ↗</a>'] for r in SOURCES]
    src_main = f'<section class="panel"><p>Primary-source register, checked {CHECKED} by reading the official pages/statutes. Only government and official legal publishers are used for legal values; no market-data site was used to set any amount.</p></section>{table(["ID", "Publisher", "Document", "Verified finding", "Checked", "Link"], s_rows, "sources")}'
    (ROOT / "sources.html").write_text(page("Official sources", "sources.html", src_main), encoding="utf-8")

    # ---- flagged ----
    f_rows = [[f'<span class="rid">{e(r[0])}</span><span class="badge {e(r[1].lower())}">{e(r[1])}</span>', f"<b>{e(r[2])}</b>", e(r[3]), e(r[4])] for r in FLAGGED]
    flag_main = f'<section class="panel"><p>Everything that could not be confirmed from an official source, plus privacy and legal-advice caveats. These are published openly and are nonblocking. Blank cells elsewhere on this site correspond to these items.</p></section>{table(["ID / severity", "Item", "Detail", "Reference"], f_rows, "flagged")}'
    (ROOT / "flagged.html").write_text(page("Flagged for review", "flagged.html", flag_main), encoding="utf-8")

    print(f"Built {len(NAV)} pages + 5 CSVs in sf-rent-94122/")

if __name__ == "__main__":
    build()

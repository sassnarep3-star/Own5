from pathlib import Path
from html import escape

P = Path(__file__).parent
rate = 'https://www.sf.gov/news--annual-rent-increase-3126-22827-announced'
rules = 'https://www.sf.gov/learn-about-rent-increases-san-francisco'
bank = 'https://www.sf.gov/information--banked-rent-increases'
notice = 'https://sf.gov/information/allowable-rent-increases'
license = 'https://www.sf.gov/notice-of-rent-board-fee-and-housing-inventory-requirement'
state = 'https://www.sf.gov/reports--california-tenant-protection-act-2019-ab-1482'
fair = 'https://www.hud.gov/reporthousingdiscrimination'
crd = 'https://calcivilrights.ca.gov/wp-content/uploads/sites/32/2019/09/FinalText-FairHousingRegulations.pdf'
ordinance = 'https://www.sf.gov/information--sec-373-rent-limitations'
petition = 'https://media.api.sf.gov/documents/516C_Tenant_Petition_Form_C_EN_5.25_Fillable_Updated.pdf'
repair = 'https://www.sf.gov/file/530-om-petition-fillable-324pdf'
counsel = 'https://media.api.sf.gov/documents/120882_-_Housing_Trust_Fund_Five-Year_Report_-_2018-2023.pdf'
capital = 'https://www.sf.gov/departments--rent-board'
algorithm = 'https://sfbos.archive.sf.gov/sites/default/files/o0224-24.pdf'

pages = {
'index': ('Executive summary', '''<p class="lead">A cautious, tenant-respecting approach for two reported rent-controlled homes in the Outer Sunset. Research reviewed November 6, 2026.</p><div class="callout"><strong>Do not serve a notice yet.</strong> Coverage, lawful base rent, rent histories, tenancy continuity, lease restrictions and license status have not been independently verified. No lawyer has reviewed or approved a proposed increase.</div><p>For an eligible annual increase effective March 1, 2026 through February 28, 2027, San Francisco’s published rate is <strong>1.6%</strong> of lawful base rent. This is a ceiling for the annual component, not proof that either home is eligible. A smaller increase or no increase is an option. Banked increases require separate review.</p><p>The conservative business choice is to consider the same neutral policy for both units, while checking each tenancy independently. Different timing or amounts are not automatically discriminatory; equal treatment does not guarantee legal compliance. Seek independent San Francisco landlord–tenant counsel before service.</p><p>Private assertions and derived unit-specific amounts are intentionally not published as verified facts: no official property or tenancy records were provided. See <a href="review.html">Flagged for Review</a>.</p>''', [
('Local annual rate','1.6% for effective dates March 1, 2026–February 28, 2027; apply to lawful base rent only.',rate),
('Unit 1: lawful base rent / proposed amount','',rules),
('Unit 2: lawful base rent / proposed amount','',rules),
('Status','Illustrative policy only; no individualized legal determination or assurance of tenant-lawyer approval.',petition),
]),
'law': ('Law & limits','<p>Different laws can apply simultaneously. This is a research summary, not legal advice. Verify current rules and the property’s actual classification before acting.</p>',[
('San Francisco annual increase','The Rent Board sets the rate; eligible increases generally occur no more than once every 12 months. Use the rate effective when the increase takes effect.',rules),
('2026–27 rate','1.6%, March 1, 2026 through February 28, 2027. A later effective date requires checking the newly published rate.',rate),
('Coverage','A pre-1979 building is a relevant indicator, not conclusive proof of coverage; exemptions and property history require review.', 'https://sf.gov/sites/default/files/2023-10/516B%20Tenant%20Petition%2010.30.23%20Fillable.pdf'),
('California AB 1482','The Rent Board states its 8.8% San Francisco rate for August 1, 2026–July 31, 2027 does not apply to units under SF rent-increase limitations. Do not substitute it for the local annual rate.',state),
('Federal fair housing','HUD identifies protected classes and prohibits retaliation for fair housing activity. Federal program-specific restrictions may also apply; no federal general rent cap is established by this source.',fair),
('State fair housing','California rules address protected classes and retaliation, including protected activity; neutral-looking decisions can still warrant legal scrutiny.',crd),
('Roommate changes','A landlord cannot raise rent simply because an additional roommate joins an existing tenancy. Last-original-occupant and successor issues are fact-specific; do not assume a reset.',rules),
('Banking','Unused annual increases may be banked, subject to timing and notice requirements; do not compound or prorate them. The precise balance needs a complete history.',bank),
]),
'units': ('Unit analysis','<p>Unit labels are placeholders. Private lease information is not independently verified against official records; blank cells are intentional, not zeros. The source links provide the applicable methodology, not proof of these individual facts.</p>',[
('Unit 1 — coverage, lawful base rent, anniversary, banked balance, proposed amount','',rules),
('Unit 1 — continuing tenancy / occupant status','',petition),
('Unit 2 — coverage, lawful base rent, anniversary, banked balance, proposed amount','',rules),
('Unit 2 — prior increases and banked balance','',bank),
('Illustrative calculation for either eligible unit','Lawful base rent × 0.016 = annual increase; base rent + increase = new base rent. Do not round up. This is not a final notice amount.',rate),
('Low-risk policy recommendation','Consider an annual-only increase of up to the published rate, or less, subject to each unit’s verified eligibility. Do not include a banked amount without a verified ledger.',bank),
('Timing','At least 12 months must have elapsed since the last annual increase or commencement, as applicable; delayed increases can change the anniversary date.',rules),
]),
'process': ('Notice & safeguards','<p>Use this checklist with counsel and the actual lease. This is not a completed notice or a substitute for legal service.</p>',[
('1. Confirm eligibility','Check coverage, lawful base rent, full rent history, anniversary, existing lease terms, subsidies and prior notices. Obtain the current rent increase license before imposing an annual or banked increase.',license),
('2. Calculate','Use the rate effective on the increase date and base rent only; distinguish annual and banked components. Avoid rounding up.',rules),
('3. Serve written notice','At least 30 days for increases of 10% or less, or 90 days if the increase alone or combined with other increases in the prior year exceeds 10%; add five days if mailed. Confirm method and service rules with counsel.',notice),
('4. Explain the increase','Include dollar amount, percentage, effective date and annual versus banked portions; identify dates underlying any banked increase. Preserve proof of service.',bank),
('5. State a truthful basis','The annual allowance is intended to cover ordinary operating and maintenance expense increases; do not claim a particular cost as a separate authorized charge without required procedure.',repair),
('6. Separate special charges','Capital improvement and other passthroughs have distinct procedures and possible hardship protections; do not add them as ordinary annual increases.',capital),
('7. Review fairly','Use consistent objective criteria, check for discriminatory effects and retaliation, document the actual rationale and allow questions. Same increases do not immunize a decision.',crd),
('8. Tenant review','Tenants can challenge unlawful increases at the Rent Board. City-funded right-to-counsel assistance concerns eviction and eligibility; it is not a guarantee of free representation for every rent-increase dispute.',counsel),
]),
'practice': ('Owner practices & fairness','<p>Local rules apply regardless of landlord size. The available official sources do not establish a representative, ZIP-specific “normal” increase by owner type. No market averages are invented.</p>',[
('Corporate versus individual practice','',algorithm),
('Published city finding','A 2024 ordinance describes use of algorithmic pricing tools by some large landlords; its legislative findings are not a verified measure of what typical owners charge today.',algorithm),
('One unit or both?','One unit may be treated differently for a documented, legitimate reason such as different eligibility or timing; analyze each unit and the overall pattern. Neither raising both nor raising one guarantees freedom from a discrimination claim.',crd),
('Practical neutral policy','Use a documented annual review and the same criteria for both units; verify each lease and timing separately. Consider less than the maximum to reduce tenant burden. This is a recommendation, not a statutory requirement.',bank),
('Tenant advocate scrutiny','An advocate could question missing rent history, licensing, service, occupant continuity, protected activity, and inconsistent treatment. Obtain an independent legal review; no particular outcome can be promised.',petition),
]),
'review': ('Flagged for Review','<p>These are unresolved issues, not a finding of a violation. Blank unit-specific fields remain blank until substantiated by official records or an appropriate independent review.</p>',[
('F01 — property and exemptions','', 'https://sf.gov/sites/default/files/2023-10/516B%20Tenant%20Petition%2010.30.23%20Fillable.pdf'),
('F02 — both units: current lawful base rent, dates, lease terms and rent histories','',rules),
('F03 — Unit 1: continuing tenancy, original occupant and new occupant legal status','',petition),
('F04 — valid rent increase license and inventory reporting','',license),
('F05 — both units: last increase, anniversary, effective date, banked balance and service','',bank),
('F06 — prior complaints, protected activity, accommodation and any fair housing risks','',crd),
('F07 — subsidies, additional program restrictions and lease limitations','',state),
('F08 — official market evidence of customary increases by landlord type or 94122','',algorithm),
('F09 — no independent counsel or tenant advocate has reviewed these facts or approved an increase','',petition),
('F10 — inconsistent banking example year','The Rent Board banking page contains an apparent inconsistent year in one worked example; use its rate schedule and independently check calculations rather than copying the example date.',bank),
]),
}
nav = [('index','Overview'),('law','Law & limits'),('units','Unit analysis'),('process','Notice & safeguards'),('practice','Practices & fairness'),('review','Flagged for Review')]
for slug,(title,intro,rows) in pages.items():
    links = ''.join('<a href="{}.html"{}>{}</a>'.format(x, ' aria-current="page"' if x == slug else '', escape(t)) for x,t in nav)
    trs = ''.join(f'<tr><th scope="row">{escape(a)}</th><td>{escape(b)}</td><td><a href="{escape(c, quote=True)}">Official source ↗</a></td></tr>' for a,b,c in rows)
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} | SF Rent Review</title><link rel="stylesheet" href="style.css"></head><body><header><div class="wrap"><a class="brand" href="index.html">SF RENT REVIEW <span> /  RESEARCH DESK</span></a><nav aria-label="Main navigation">{links}</nav></div></header><main class="wrap"><div class="eyebrow">SAN FRANCISCO · 94122</div><h1>{escape(title)}</h1>{intro}<div class="tablewrap"><table><thead><tr><th scope="col">Topic</th><th scope="col">Finding / status</th><th scope="col">Evidence</th></tr></thead><tbody>{trs}</tbody></table></div><p class="footnote">Official links support general rules, not private facts. Blank = unverified. Sources and rules can change; confirm before acting.</p></main><footer><div class="wrap">Independent research · No personal identifiers · Not legal advice</div></footer></body></html>'''
    (P / f'{slug}.html').write_text(html)

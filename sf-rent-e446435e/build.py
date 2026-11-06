"""Deterministic static build for the SF rent e446435e dashboard.

Reads data/canonical.json (single source of truth), renders money tokens
({calc:unit:pct} / {delta:unit:pct} / {total:unit:pct}) with Decimal math
(no compounding), writes 11 static HTML pages + 4 CSV exports.
Fails closed on unknown source/flag IDs or rows without any reference.
No external assets, keys, or backend. Run: python3 sf-rent-e446435e/build.py
"""
import csv
import html
import io
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
D = json.loads((ROOT / "data" / "canonical.json").read_text())
BASES = {k: Decimal(str(v)) for k, v in D["bases"].items()}
SOURCES = {s["id"]: s for s in D["sources"]}
FLAGS = {f["id"]: f for f in D["flags"]}
SRC_IDS = set(SOURCES)
FLAG_IDS = set(FLAGS)

TOKEN = re.compile(r"\{(calc|delta|total):(unit1|unit2):(\d+(?:\.\d+)?)\}")


def money(base_key, pct_s):
    base = BASES[base_key]
    pct = Decimal(pct_s)
    delta = (base * pct / Decimal(100)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    total = base + delta
    return delta, total


def fmt(amount):
    return f"${amount:,.2f}"


def render_token(m):
    kind, base_key, pct_s = m.group(1), m.group(2), m.group(3)
    delta, total = money(base_key, pct_s)
    if kind == "delta":
        return f"+{fmt(delta)}"
    if kind == "total":
        return fmt(total)
    return f"+{fmt(delta)} \u2192 {fmt(total)}"


def render(text):
    return TOKEN.sub(render_token, text)


def e(value):
    return html.escape(render(str(value)), quote=True)


def refs(ids):
    out = ['<span class="refs">']
    for i in ids:
        s = SOURCES[i]
        out.append(
            f'<a href="{e(s["url"])}" target="_blank" rel="noopener noreferrer"'
            f' title="{e(s["publisher"])} — {e(s["title"])}">{e(i)} \u2197</a>'
        )
    return "".join(out) + "</span>"


def flagrefs(ids):
    out = ['<span class="flagrefs">']
    for i in ids:
        out.append(f'<a href="flagged.html#{e(i)}" title="{e(FLAGS[i]["issue"])}">{e(i)} \u2691</a>')
    return "".join(out) + "</span>"


class Raw(str):
    """Pre-escaped HTML cell content: inserted verbatim, never re-escaped."""


def cell(value):
    if value is None:
        return '<td class="missing" aria-label="Unverified: value unavailable"></td>'
    if isinstance(value, Raw):
        return "<td>" + value + "</td>"
    return "<td>" + e(value) + "</td>"


def table(title, desc, headers, rows, tid, filters=None):
    controls = (
        f'<label class="search"><span aria-hidden="true">\u2315</span>'
        f'<input type="search" data-search="{tid}" aria-label="Search {e(title)}"'
        f' placeholder="Search this table\u2026"></label>'
    )
    if filters:
        controls += (
            f'<label class="filter">Severity <select data-filter="{tid}">'
            f"<option value=\"\">All</option>"
            + "".join(f"<option>{e(f)}</option>" for f in filters)
            + "</select></label>"
        )
    body = "".join("<tr>" + "".join(cell(c) for c in row) + "</tr>" for row in rows)
    return f"""<section class="panel table-panel"><div class="panel-head"><div><h2>{title}</h2><p>{desc}</p></div><button class="export" data-export="{tid}">Export CSV <span aria-hidden="true">\u2193</span></button></div><div class="table-tools">{controls}<span class="row-count" data-count="{tid}">{len(rows)} entries</span></div><div class="table-wrap"><table id="{tid}"><caption class="sr-only">{title}. Blank cells are unverified, not zero.</caption><thead><tr>{''.join('<th scope="col">' + h + "</th>" for h in headers)}</tr></thead><tbody>{body}</tbody></table></div><p class="empty" hidden>No matching entries. Try another search.</p></section>"""


def finding_rows(page, id_prefix=None):
    rows = []
    for r in D["rows"]:
        if r["page"] != page:
            continue
        if id_prefix and not r["id"].startswith(id_prefix):
            continue
        if not r["sources"] and not r["flags"]:
            raise SystemExit(f"Row {r['id']} has no source or flag reference")
        for s in r["sources"]:
            if s not in SRC_IDS:
                raise SystemExit(f"Row {r['id']} unknown source {s}")
        for f in r["flags"]:
            if f not in FLAG_IDS:
                raise SystemExit(f"Row {r['id']} unknown flag {f}")
        name = Raw(f'<span class="record-id">{e(r["id"])}</span><strong>{e(r["topic"])}</strong>')
        rows.append([name, r["value"], r["finding"], Raw(refs(r["sources"]) + flagrefs(r["flags"]))])
    return rows


def note(title, text, cls=""):
    return f'<aside class="notice {cls}"><span class="notice-icon" aria-hidden="true">i</span><div><strong>{title}</strong><p>{text}</p></div></aside>'


NAV = [
    ("index", "Dashboard", "01"),
    ("summary", "Executive summary", "02"),
    ("local-law", "SF local law", "03"),
    ("state-law", "CA state law", "04"),
    ("federal-law", "Federal law & benchmarks", "05"),
    ("practice", "Owner practices", "06"),
    ("process", "Notice & reasons", "07"),
    ("units", "Unit scenarios", "08"),
    ("fair-housing", "Fairness: one vs both", "09"),
    ("flagged", "Flagged for Review", "10"),
    ("sources", "Sources", "11"),
]
SUBTITLES = {
    "index": "Lawful ceilings, reported inputs, and open gates — at a glance.",
    "summary": "Bottom line, unit paths, and answers to each question.",
    "local-law": "SF Rent Board ceilings, banking, licenses, and turnover rules.",
    "state-law": "Notice service, AB 1482, retaliation, and FEHA.",
    "federal-law": "No federal cap, fair-housing bars, and HUD benchmarks.",
    "practice": "Institutional vs. individual owners — verified context only.",
    "process": "How to serve notice, and which reasons are lawful.",
    "units": "Anonymized scenario math with every gate flagged.",
    "fair-housing": "One unit or both: the review-passing pattern.",
    "flagged": "Open review items — nonblocking for publication.",
    "sources": "Every official source, with findings and limits.",
}


def hero():
    return f"""<section class="hero"><div><span class="eyebrow" style="color:#ffe6ad">OUTER SUNSET · SAN FRANCISCO 94122 · RENT-CONTROL COMPLIANCE</span><h2>Reasonable increases, proven line by line.</h2><p>Evidence dashboard for a 1940 two-unit building: the 1.6% annual ceiling, banked-increase math for both units, notice procedure, corporate vs. individual practice, and the fairness analysis for raising one unit or both. Every row links to an official source; blanks are unverified.</p><a class="primary" href="summary.html">Read the executive summary</a><a class="text-link" href="flagged.html">Open review items ({len(D['flags'])}) \u2192</a></div></section>"""


def stats():
    n_rows = len(D["rows"]) + len(D["rates"])
    n_blank = sum(1 for r in D["rows"] if r["value"] is None) + sum(
        1 for x in D["rates"] if x["rate_pct"] is None
    )
    n_high = sum(1 for f in D["flags"] if f["severity"] == "High")
    return f"""<div class="stats"><article><span>Annual ceiling (2026–27)</span><strong>1.6%</strong><small>Of lawful base rent · Mar 1, 2026 – Feb 28, 2027</small></article><article><span>Evidence rows</span><strong>{n_rows:02}</strong><small>Every row carries an official source or flag</small></article><article><span>Blank (unverified)</span><strong class="amber">{n_blank:02}</strong><small>Blank means unverified — never zero</small></article><article><span>High-severity flags</span><strong class="amber">{n_high:02}</strong><small><a href="flagged.html">Must close before any notice \u2197</a></small></article></div>"""


def cards():
    items = [
        ("summary.html", "02", "Executive summary", "Bottom line and per-unit lawful paths."),
        ("local-law.html", "03", "SF local law", "Ceilings, banking, licenses, turnover."),
        ("state-law.html", "04", "CA state law", "Service, timing, AB 1482, FEHA."),
        ("federal-law.html", "05", "Federal & benchmarks", "FHA bars + HUD 94122 SAFMRs."),
        ("practice.html", "06", "Owner practices", "REITs vs. individuals, verified only."),
        ("process.html", "07", "Notice & reasons", "Service checklist + lawful reasons."),
        ("units.html", "08", "Unit scenarios", "Derived math with open gates."),
        ("fair-housing.html", "09", "One vs both", "Selective-increase fairness review."),
    ]
    return '<div class="cards">' + "".join(
        f'<a class="card" href="{h}"><span class="num">{n}</span><h3>{t}</h3><p>{p}</p></a>'
        for h, n, t, p in items
    ) + "</div>"


def rates_table():
    rows = []
    for x in D["rates"]:
        val = None if x["rate_pct"] is None else f"{x['rate_pct']}%"
        rows.append(
            [
                Raw(f'<span class="record-id">{e(x["id"])}</span><strong>{e(x["window"])}</strong>'),
                val,
                Raw(refs(x["sources"]) + flagrefs(x["flags"])),
            ]
        )
    return table(
        "Allowable annual increases (Form 571)",
        "Official Rent Board schedule. Apply the rate for the window containing the increase's effective date.",
        ["Effectiveness window", "Annual %", "Official source"],
        rows,
        "rates",
    )


def flags_table():
    sev = {"High": "high", "Medium": "warn", "Low": "neutral"}
    rows = []
    for f in D["flags"]:
        if not f["sources"] and "ref_url" not in f:
            raise SystemExit(f"Flag {f['id']} has no reference")
        ref = refs(f["sources"])
        if "ref_url" in f:
            ref += (
                f'<a href="{e(f["ref_url"])}" target="_blank" rel="noopener noreferrer">'
                f'{e(f["ref_label"])} \u2197</a>'
            )
        ref += flagrefs([f["id"]]).replace("flagged.html#", "#")
        rows.append(
            [
                Raw(f'<span class="record-id" id="{e(f["id"])}">{e(f["id"])}</span><span class="badge {sev[f["severity"]]}">{e(f["severity"])}</span>'),
                Raw(f"<strong>{e(f['issue'])}</strong>"),
                f["detail"],
                f["scope"],
                Raw(f'<span class="badge warn">{e(f["status"])}</span>'),
                Raw(ref),
            ]
        )
    # add data-sev attributes for the severity filter
    out = table(
        "Flagged for Review",
        "Open items. Nonblocking for publication; high-severity items block any rent-increase notice.",
        ["ID / severity", "Issue", "Finding / limitation", "Scope", "Status", "Reference"],
        rows,
        "flags",
        filters=["High", "Medium", "Low"],
    )
    for f in D["flags"]:
        out = out.replace(f'<tr><td><span class="record-id" id="{f["id"]}"',
                          f'<tr data-sev="{f["severity"]}"><td><span class="record-id" id="{f["id"]}"', 1)
    return out


def sources_table():
    rows = []
    for s in D["sources"]:
        rows.append(
            [
                Raw(f"<strong>{e(s['id'])}</strong><br><small>{e(s['publisher'])}</small>"),
                Raw(f"<strong>{e(s['title'])}</strong><br><small>Checked {e(s['checked'])}</small>"),
                s["finding"],
                s["limitation"],
                Raw(refs([s["id"]])),
            ]
        )
    return table(
        "Primary-source register",
        f"Official publishers only · checked {e(D['as_of'])} · no third-party values used.",
        ["ID / publisher", "Document", "Finding used", "Limitation", "Official source"],
        rows,
        "sources",
    )


HEADERS = ["Item", "Value", "Finding / application", "Official source"]
DESC = "Blank cells are unverified, not zero. Derived $ figures are arithmetic illustrations gated by flags."

CONTENT = {
    "index": lambda: hero()
    + stats()
    + note("Do not serve any notice yet.", "Coverage, lawful base rents, histories, the Unit 1 agreement type, license status, and banked balances are unverified. High-severity flags must close and counsel must review first.", "danger")
    + cards()
    + table("At a glance", DESC, HEADERS, finding_rows("index"), "glance"),
    "summary": lambda: note("Bottom line.", "The 2026–27 annual ceiling is 1.6% of lawful base rent. Unit 1 paths range from $0.00 (fixed-term) to $4,114.85 (Feb 2027 anniversary); Unit 2 from $3,200.40 (annual-only) to $3,562.65 (max banked) — every figure conditional on open flags. AB 1482 is moot; federal law bars discrimination, not percentages.", "warn")
    + table("Executive brief", DESC, HEADERS, finding_rows("summary"), "brief"),
    "local-law": lambda: note("The local ordinance controls.", "Where SF rent control is stricter than state law, the Rent Ordinance governs. Defective or unlicensed increases are null and void — not merely late.")
    + rates_table()
    + table("SF rules", DESC, HEADERS, finding_rows("local-law"), "local"),
    "state-law": lambda: note("State law sets the procedure and the protections.", "Section 827 controls how notice is served and how long it runs; AB 1482 yields to stricter local control; retaliation and FEHA rules constrain why and how rents move.")
    + table("California rules", DESC, HEADERS, finding_rows("state-law"), "state"),
    "federal-law": lambda: note("Federal law: no cap, no discrimination.", "No general federal private-market rent cap exists. The Fair Housing Act bars discriminatory rates and terms; HUD market rents are benchmarks, never authority for above-ceiling increases.")
    + table("Federal rules & HUD benchmarks", DESC, HEADERS, finding_rows("federal-law"), "federal"),
    "practice": lambda: note("Verified context only.", "Institutional disclosure venues and algorithmic-pricing enforcement are verified. Private-market 'normal percentages' have no official source and stay blank.")
    + table("Corporations vs. individual owners", DESC, HEADERS, finding_rows("practice"), "practice"),
    "process": lambda: note("Perfect execution or void.", "Personal delivery or mailed +5 days in CA; 30/35 vs 90/95-day thresholds; full dollar-and-percent itemization; license first. Checklists here are illustrative — not a served notice.")
    + table("Notice procedure & reasons", DESC, HEADERS, finding_rows("process"), "process"),
    "units": lambda: note("Scenario math, every gate flagged.", "Derived figures assume reported bases, zero interim increases, month-to-month tenancies, and active licenses — all unverified. Percents sum without compounding; dollars equal base × %.")
    + table("Unit 1 — $3,995.00/mo", DESC, HEADERS, finding_rows("units", "U1"), "unit1")
    + table("Unit 2 — $3,150.00/mo", DESC, HEADERS, [r for r in finding_rows("units") if r[0].find("U2-") != -1 or r[0].find("UB-") != -1], "unit2")
    + table("Market-benchmark gates", DESC, HEADERS, finding_rows("units", "UM"), "benchmarks"),
    "fair-housing": lambda: note("Selective action needs a paper trail.", "Raising one unit while holding the other is lawful-in-principle where objective timing locks differ — but only under a written uniform policy, with retaliation clearance and counsel review.")
    + table("One unit or both", DESC, HEADERS, finding_rows("fair-housing"), "fairness"),
    "flagged": lambda: note("Published openly. Nonblocking for the site.", "High-severity items block any rent-increase notice — not publication. No missing value has been filled in.", "warn") + flags_table(),
    "sources": lambda: note("Official publishers only.", "Checked means the stated finding was read in the linked official material on 2026-11-06. Lease facts from the request appear nowhere here — no official record confirms them.") + sources_table(),
}

for key, title, num in NAV:
    def link(k):
        return "index.html" if k == "index" else f"{k}.html"

    content = CONTENT[key]()
    body = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="SF rent-control increase compliance dashboard: {e(title)}. Verified ceilings, scenario math, notice rules, and open review items."><meta name="theme-color" content="#0f5c4d"><title>{e(title)} · SF Rent Review e446435e</title><link rel="stylesheet" href="style.css"><script src="app.js" defer></script></head><body><a class="skip" href="#main">Skip to content</a><div class="layout"><aside class="sidebar"><a class="brand" href="index.html"><span class="brand-icon">SF</span><span>RENT REVIEW<small>SESSION e446435e</small></span></a><span class="nav-caption">DASHBOARD</span><nav aria-label="Main navigation">{''.join(f'<a href="{link(k)}" class="nav-item {"active" if k == key else ""}" ' + ('aria-current="page"' if k == key else "") + f'><span class="nav-number">{n}</span>{t}' + ('<span class="nav-tag">19</span>' if k == "flagged" else "") + "</a>" for k, t, n in NAV)}</nav><div class="side-bottom"><p>General information only — not legal advice. Anonymized: no tenant PII.</p><a href="https://github.com/sassnarep3-star/Own5/tree/main/research/sf-rent-e446435e" target="_blank" rel="noopener noreferrer">Research package \u2197</a></div></aside><div class="main-shell"><header class="topbar"><div><span class="breadcrumb">SF Rent Review <span>/</span> {e(title)}</span></div><div class="topbar-right"><span>94122 · RENT CONTROL</span><span class="avatar">SF</span></div></header><main id="main"><div class="page-heading"><div><span class="eyebrow">SAN FRANCISCO · OUTER SUNSET</span><h1>{e(title)}</h1><p>{SUBTITLES[key]}</p></div><span class="date-label"><span class="live-dot"></span> Verified {e(D["as_of"])}</span></div>{content}<footer><span>SF Rent Review e446435e <span class="footer-divider">/</span> General information, not legal advice.</span><span>Blank cells = unverified. <a href="flagged.html">Flagged for Review \u2197</a> · <a href="sources.html">Sources \u2197</a> · <a href="data/findings.csv">Open data (CSV) \u2197</a></span></footer></main></div></div></body></html>"""
    (ROOT / ("index.html" if key == "index" else f"{key}.html")).write_text(body + "\n")

# CSV exports (tokens rendered)
with (ROOT / "data" / "rates.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "window", "rate_pct", "sources", "flags"])
    for x in D["rates"]:
        w.writerow([x["id"], x["window"], "" if x["rate_pct"] is None else x["rate_pct"],
                    ";".join(x["sources"]), ";".join(x["flags"])])
with (ROOT / "data" / "sources.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "publisher", "title", "finding", "limitation", "checked", "url"])
    for s in D["sources"]:
        w.writerow([s["id"], s["publisher"], s["title"], s["finding"], s["limitation"],
                    s["checked"], s["url"]])
with (ROOT / "data" / "flags.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "severity", "issue", "detail", "scope", "status", "sources"])
    for x in D["flags"]:
        w.writerow([x["id"], x["severity"], x["issue"], x["detail"], x["scope"],
                    x["status"], ";".join(x["sources"])])
with (ROOT / "data" / "findings.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "page", "topic", "value", "finding", "sources", "flags"])
    for r in D["rows"]:
        w.writerow([r["id"], r["page"], r["topic"],
                    "" if r["value"] is None else render(r["value"]), r["finding"],
                    ";".join(r["sources"]), ";".join(r["flags"])])

print(f"Built 11 pages + 4 CSVs: {len(D['rows'])} findings, {len(D['rates'])} rates, "
      f"{len(D['sources'])} sources, {len(D['flags'])} flags.")

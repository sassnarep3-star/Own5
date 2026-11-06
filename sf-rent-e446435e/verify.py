"""Deterministic verification for the SF rent e446435e dashboard.

Checks (FAIL exits non-zero):
 1. All 11 pages + assets + data files exist.
 2. Every <tbody> row in every page has >=1 link (official https or flagged.html).
 3. Every relative href/src resolves; every external link is https on an allowlisted
    official host; every flagged.html#anchor exists; _blank links carry rel=noopener.
 4. Zero PII: spaced-initial patterns, e-mail, SSN, and non-allowlisted phone patterns
    across sf-rent-e446435e/** and research/sf-rent-e446435e/**.
 5. Money-token math: every {calc|delta|total:unit:pct} in canonical.json recomputed
    (Decimal, ROUND_HALF_UP, no compounding) and present in the built page.
 6. CSV/JSON consistency (row counts + rate values).
Run: python3 sf-rent-e446435e/verify.py
"""
import csv
import html as htmlmod
import json
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
RESEARCH = REPO / "research" / "sf-rent-e446435e"

PAGES = ["index", "summary", "local-law", "state-law", "federal-law", "practice",
         "process", "units", "fair-housing", "flagged", "sources"]
ALLOWED_HOSTS = {"sf.gov", "www.sf.gov", "media.api.sf.gov", "leginfo.legislature.ca.gov",
                 "hud.gov", "www.hud.gov", "huduser.gov", "www.huduser.gov",
                 "justice.gov", "www.justice.gov", "sec.gov", "www.sec.gov",
                 "calcivilrights.ca.gov", "congress.gov", "www.congress.gov",
                 "github.com"}
ALLOWLIST_PHONES = {"415-659-9184", "415-252-4600", "415-782-8940"}

fails, warns = [], []


def fail(msg):
    fails.append(msg)


def warn(msg):
    warns.append(msg)


D = json.loads((ROOT / "data" / "canonical.json").read_text())
BASES = {k: Decimal(str(v)) for k, v in D["bases"].items()}

# 1. files exist
expected = [ROOT / ("index.html" if p == "index" else p + ".html") for p in PAGES]
expected += [ROOT / "style.css", ROOT / "app.js", ROOT / "data" / "canonical.json",
             ROOT / "data" / "rates.csv", ROOT / "data" / "sources.csv",
             ROOT / "data" / "flags.csv", ROOT / "data" / "findings.csv"]
for p in expected:
    if not p.is_file():
        fail(f"missing file: {p.relative_to(REPO)}")

html_text = {}
for p in PAGES:
    fp = ROOT / ("index.html" if p == "index" else p + ".html")
    html_text[p] = fp.read_text() if fp.is_file() else ""

flag_ids = {f["id"] for f in D["flags"]}
src_ids = {s["id"] for s in D["sources"]}

# 2/3. rows + links
total_rows = 0
for p in PAGES:
    t = html_text[p]
    for m in re.finditer(r"<tbody>(.*?)</tbody>", t, re.S):
        for rm in re.finditer(r"<tr.*?>(.*?)</tr>", m.group(1), re.S):
            total_rows += 1
            links = re.findall(r'<a\s+[^>]*href="([^"]+)"', rm.group(1))
            if not links:
                fail(f"{p}.html: tbody row without any link: {rm.group(1)[:90]!r}")
    for am in re.finditer(r"<a\s+[^>]*href=\"([^\"]+)\"[^>]*>", t):
        href = htmlmod.unescape(am.group(1))
        tag = am.group(0)
        if href.startswith(("https://", "http://")):
            if href.startswith("http://"):
                fail(f"{p}.html: non-https link: {href}")
            host = urlparse(href).hostname or ""
            if host not in ALLOWED_HOSTS:
                fail(f"{p}.html: non-allowlisted host: {href}")
            if 'target="_blank"' in tag and "noopener" not in tag:
                fail(f"{p}.html: _blank without noopener: {href}")
        elif href.startswith("#"):
            page_ids = set(re.findall(r'id="([^"]+)"', t))
            if href[1:] not in flag_ids and href[1:] not in page_ids:
                fail(f"{p}.html: unknown anchor: {href}")
        else:
            target = (ROOT / href.split("#")[0]).resolve()
            if not target.is_file():
                fail(f"{p}.html: broken relative link: {href}")
            if "#R44-" in href:
                anchor = href.split("#")[1]
                dest = html_text.get(target.stem, target.read_text())
                if f'id="{anchor}"' not in dest:
                    fail(f"{p}.html: missing anchor target: {href}")
    for sm in re.finditer(r'<(?:link|script)[^>]*(?:href|src)="([^"]+)"', t):
        src = sm.group(1)
        if src.startswith("http"):
            fail(f"{p}.html: external asset: {src}")
        elif not (ROOT / src).is_file():
            fail(f"{p}.html: missing asset: {src}")

# JSON reference integrity
for r in D["rows"]:
    if not r["sources"] and not r["flags"]:
        fail(f"row {r['id']}: no source or flag")
    for s in r["sources"]:
        if s not in src_ids:
            fail(f"row {r['id']}: unknown source {s}")
    for f in r["flags"]:
        if f not in flag_ids:
            fail(f"row {r['id']}: unknown flag {f}")
for x in D["rates"]:
    for s in x["sources"]:
        if s not in src_ids:
            fail(f"rate {x['id']}: unknown source {s}")
    for f in x["flags"]:
        if f not in flag_ids:
            fail(f"rate {x['id']}: unknown flag {f}")

# 4. PII scan (patterns assembled so this file holds no literal)
sp = chr(32)
initials = ["L" + sp + "O", "V" + sp + "N", "J" + "P",
            "M" + sp + "T", "E" + sp + "R", "I" + sp + "S"]
pii_res = [re.compile(r"\b" + re.escape(x) + r"\b") for x in initials]
pii_res.append(re.compile(r"[A-Za-z0-9._%+-]+" + "@" + r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}"))
pii_res.append(re.compile(r"\b\d{3}-\d{2}-\d{4}\b"))
phone_re = re.compile(r"\b(\d{3}-\d{3}-\d{4})\b")
scan_files = [p for p in list(ROOT.rglob("*")) + list(RESEARCH.rglob("*"))
              if p.is_file() and p.suffix in {".html", ".json", ".csv", ".md", ".py", ".css", ".js"}]
pii_hits = 0
for p in scan_files:
    text = p.read_text()
    rel = p.relative_to(REPO)
    for rx in pii_res:
        for m in rx.finditer(text):
            # allow this file's own pattern-assembly lines
            if p.name == "verify.py" and ('"' in text[max(0, m.start() - 12):m.start()]):
                continue
            fail(f"PII pattern {m.group(0)!r} in {rel}")
            pii_hits += 1
    for m in phone_re.finditer(text):
        if m.group(1) not in ALLOWLIST_PHONES:
            fail(f"non-allowlisted phone {m.group(1)} in {rel}")
            pii_hits += 1

# 5. money-token math
TOKEN = re.compile(r"\{(calc|delta|total):(unit1|unit2):(\d+(?:\.\d+)?)\}")


def expected_str(kind, base_key, pct_s):
    base = BASES[base_key]
    delta = (base * Decimal(pct_s) / Decimal(100)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    total = base + delta
    if kind == "delta":
        return f"+${delta:,.2f}"
    if kind == "total":
        return f"${total:,.2f}"
    return f"+${delta:,.2f} \u2192 ${total:,.2f}"


tokens_checked = 0
raw_json = (ROOT / "data" / "canonical.json").read_text()
page_of_row = {r["id"]: r["page"] for r in D["rows"]}
for r in D["rows"]:
    for field in (r.get("value") or "", r.get("finding") or ""):
        for m in TOKEN.finditer(field):
            tokens_checked += 1
            want = expected_str(m.group(1), m.group(2), m.group(3))
            page = page_of_row[r["id"]]
            if want not in html_text[page]:
                fail(f"row {r['id']}: expected {want!r} missing from {page}.html")

# 6. CSV consistency
def csv_rows(name):
    with (ROOT / "data" / name).open() as f:
        return list(csv.DictReader(f))

if (ROOT / "data" / "findings.csv").is_file():
    if len(csv_rows("findings.csv")) != len(D["rows"]):
        fail("findings.csv count != canonical rows")
if (ROOT / "data" / "rates.csv").is_file():
    rr = csv_rows("rates.csv")
    if len(rr) != len(D["rates"]):
        fail("rates.csv count != canonical rates")
    for got, want in zip(rr, D["rates"]):
        w = "" if want["rate_pct"] is None else str(want["rate_pct"])
        if got["rate_pct"] != w or got["id"] != want["id"]:
            fail(f"rates.csv mismatch on {want['id']}")
if (ROOT / "data" / "sources.csv").is_file():
    if len(csv_rows("sources.csv")) != len(D["sources"]):
        fail("sources.csv count != canonical sources")
if (ROOT / "data" / "flags.csv").is_file():
    if len(csv_rows("flags.csv")) != len(D["flags"]):
        fail("flags.csv count != canonical flags")

print(f"pages={len(PAGES)} tbody_rows={total_rows} tokens={tokens_checked} "
      f"scanned={len(scan_files)} FAIL={len(fails)} WARN={len(warns)}")
for w in warns:
    print("WARN:", w)
for f in fails:
    print("FAIL:", f)
sys.exit(1 if fails else 0)

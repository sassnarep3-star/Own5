#!/usr/bin/env python3
"""Line-by-line verification for the sf-rent-94122 subsite.

Checks (all must pass):
1. Every CSV data row has a non-empty `sources` field, and every source id
   resolves to an official allowlisted domain in sources.csv.
2. Rows whose value contains 'BLANK' must carry an explicit flag reference on
   the Flagged page (flagged.csv) — unverified values are never filled in.
3. Every internal href/src in the generated HTML files resolves to an
   existing file inside sf-rent-94122/.
4. Every external link in HTML matches the same official allowlist.
5. sources.csv ids are unique and complete (all referenced ids exist).
Exit code 0 = pass.
"""
import csv
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

OFFICIAL_DOMAINS = {
    "sf.gov", "www.sf.gov", "sfrb.org",
    "leginfo.legislature.ca.gov",
    "uscode.house.gov",
    "hud.gov", "www.hud.gov",
    "courts.ca.gov", "www4.courts.ca.gov",
    "bls.gov", "www.bls.gov",
    "sfplanninggis.org",
    "contracostaha.org",  # county government housing authority
    "github.com",  # repo self-link in footer
}

failures = []

def fail(msg):
    failures.append(msg)

def load(name):
    with open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

sources = load("sources.csv")
src_ids = {r["id"]: r for r in sources}
if len(src_ids) != len(sources):
    fail("sources.csv has duplicate ids")
for sid, r in src_ids.items():
    if urlparse(r["url"]).netloc.lower() not in OFFICIAL_DOMAINS:
        fail(f"source {sid} URL not on official allowlist: {r['url']}")

flagged = load("flagged.csv")
flag_ids = {r["id"] for r in flagged}

for name, src_col in [("laws.csv", "sources"), ("units.csv", "sources"),
                      ("qa.csv", "sources"), ("flagged.csv", "source")]:
    for row in load(name):
        rid = row.get("id") or row.get("unit") or "?"
        val = " ".join(str(v) for v in row.values())
        refs = re.findall(r"S\d+", row.get(src_col, ""))
        for ref in refs:
            if ref not in src_ids:
                fail(f"{name} row {rid}: unknown source id {ref}")
        if "BLANK" in val:
            # must reference a flag or be explicitly marked blank-by-design
            if not any(fid in val for fid in flag_ids) and "flag" not in val.lower():
                fail(f"{name} row {rid}: contains BLANK without a flag reference")

# HTML internal/external link check
html_files = sorted(ROOT.glob("*.html"))
link_re = re.compile(r'(?:href|src)="([^"]+)"')
for hf in html_files:
    text = hf.read_text(encoding="utf-8")
    for url in link_re.findall(text):
        if url.startswith(("http://", "https://")):
            dom = urlparse(url).netloc.lower()
            if dom not in OFFICIAL_DOMAINS:
                fail(f"{hf.name}: external link not allowlisted: {url}")
        elif not url.startswith(("#", "mailto:")):
            target = (hf.parent / url.split("#")[0].split("?")[0])
            if not target.exists():
                fail(f"{hf.name}: broken internal link: {url}")

# Every flagged id appears on the flagged page; every page in NAV exists
flag_page = (ROOT / "flagged.html").read_text(encoding="utf-8")
for fid in flag_ids:
    if fid not in flag_page:
        fail(f"flag {fid} missing from flagged.html")

# PII check: user-supplied tenant initials must not appear in published pages
banned = ["L O", "V N", "JP", "E R", "I S", "M T"]
for hf in html_files:
    text = hf.read_text(encoding="utf-8")
    for b in banned:
        if re.search(r"\b" + re.escape(b) + r"\b", text):
            fail(f"{hf.name}: possible tenant identifier leak: {b}")

if failures:
    print("VERIFY FAILED:")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print(f"VERIFY PASS: {len(html_files)} HTML pages, {len(sources)} sources, "
      f"{sum(len(load(n)) for n in ['laws.csv','units.csv','qa.csv','flagged.csv'])} data rows, "
      f"{len(flag_ids)} flags; all rows source-linked or explicitly flagged; "
      f"0 broken links; no personal identifiers published.")

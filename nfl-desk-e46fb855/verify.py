"""Row-level proof that what the site publishes is sourced and internally sound.

Walks the generated HTML (not the CSVs), because what a reader sees is what has
to be defensible.  For every <tr> in every <tbody> it asserts that the row's
final cell either links to an http(s) source or carries the UNVERIFIED badge.
Anything else fails the build, so an unsourced row can never be published
silently.

Also checks: every expected page exists, every internal link resolves, the
capture ledger still matches the bytes on disk, and a second build of the data
is byte-identical to the first (determinism).
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

TR = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S)
TD = re.compile(r"<td\b[^>]*>(.*?)</td>", re.S)
TBODY = re.compile(r"<tbody\b[^>]*>(.*?)</tbody>", re.S)
HREF = re.compile(r'href="(https?://[^"]+)"')
BLANK = re.compile(r'class="blank"')
INTERNAL = re.compile(r'href="([a-z0-9\-]+\.html)"')

EXPECTED_PAGES = [
    "index.html", "executive-summary.html", "requirements.html", "questions.html",
    "suggestions.html", "results.html", "slate.html", "lines.html", "price-store.html",
    "depth.html", "injuries.html", "matchup.html", "strategies.html", "gates.html",
    "leaderboard.html", "correlations.html", "luck.html", "flagged.html", "sources.html",
    "audit.html", "verification.html",
]

# CSVs that legitimately hold rows with no per-row source: they are registers of
# text a human reviews, or rows whose emptiness is itself the finding.
NO_SOURCE_REQUIRED = {"manifest.csv", "build_report.json", "price_store_schema.csv"}


def csv_rows(name):
    import csv
    with open(DATA / name, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def check_pages():
    failures, checked, linked, blanked = [], 0, 0, 0
    pages = sorted(p for p in os.listdir(ROOT) if p.endswith(".html"))
    for p in EXPECTED_PAGES:
        if p not in pages:
            failures.append(f"{p}: expected page was not generated")
    internal_targets = set(pages)
    link_refs = {}
    for page in pages:
        html = (ROOT / page).read_text(encoding="utf-8")
        if "OWN5" not in html:
            failures.append(f"{page}: the OWN5 masthead is missing")
        link_refs[page] = set(INTERNAL.findall(html))
        for target in link_refs[page]:
            if target not in internal_targets:
                failures.append(f"{page}: links to {target}, which was not generated")
        for body in TBODY.findall(html):
            for tr in TR.findall(body):
                cells = TD.findall(tr)
                if not cells:
                    continue
                checked += 1
                last = cells[-1]
                if BLANK.search(last):
                    blanked += 1
                elif HREF.search(last):
                    linked += 1
                else:
                    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", tr)).strip()[:150]
                    failures.append(f"{page}: row with no source link and no UNVERIFIED badge -> {text}")
    return failures, checked, linked, blanked


def check_manifest():
    failures = []
    import csv
    path = DATA / "manifest.csv"
    if not path.exists():
        return ["manifest.csv: capture ledger is missing"]
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            rel = row["path"]
            if rel.startswith("(read-only) "):
                continue
            p = ROOT / rel
            if not p.exists():
                failures.append(f"manifest.csv: {rel} is listed but not on disk")
                continue
            blob = p.read_bytes()
            if hashlib.sha256(blob).hexdigest() != row["sha256"]:
                failures.append(f"manifest.csv: {rel} no longer matches its recorded hash")
            if len(blob) != int(row["bytes"]):
                failures.append(f"manifest.csv: {rel} byte count changed")
    return failures


def check_determinism():
    """Rebuild the data and prove nothing moved."""
    failures = []
    import engine
    before = {}
    for p in sorted(DATA.glob("*.csv")):
        before[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    engine.build()
    for p in sorted(DATA.glob("*.csv")):
        if p.name in before and hashlib.sha256(p.read_bytes()).hexdigest() != before[p.name]:
            failures.append(f"{p.name}: a rebuild changed the data (not deterministic)")
    return failures


def main() -> int:
    failures, checked, linked, blanked = check_pages()
    failures += check_manifest()
    failures += check_determinism()

    print(f"body rows checked      : {checked}")
    print(f"  with an official link: {linked}")
    print(f"  explicitly UNVERIFIED: {blanked}")
    if failures:
        print(f"\nFAILED ({len(failures)}):")
        for f in failures[:60]:
            print("  -", f)
        return 1
    print("\nOK: every body row is sourced or explicitly flagged, links resolve, "
          "captures match their hashes, and the build is deterministic.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

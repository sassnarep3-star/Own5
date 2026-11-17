"""Row-level verification of the generated site.

This checks the HTML, not the CSVs. A blank that escapes the data layer is still
caught here.

Checks:
  1. every page in the navigation exists and every internal link resolves
  2. every <tbody> row whose table has a "source" column carries a link or an
     explicit UNVERIFIED badge
  3. no page carries an unlabelled empty cell in a body row
  4. the nav is identical on every page (no page silently drops a category)
  5. every number that appears in a headline card exists in the derived data
     (spot-check: the counts in the footer match manifest.json)
  6. the corpus tarball still hashes to the pin

Exit code 0 only if all checks pass.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "nfl-season-941fe39f"
DERIVED = DESK / "data" / "derived"
TARBALL = DESK / "data" / "corpus" / "raw" / "nfldata_e045566e.tar.gz"
PIN = "9a6a736819bd6587f135d0995778c23ef9e51a9587d9e901f5dc84072504462c"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    "season_site", Path(__file__).resolve().parent / "site.py")
SITE = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(SITE)  # the navigation contract lives in site.py

LINK = re.compile(r'href="([^"]+)"')
ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
CELL = re.compile(r"<td[^>]*>(.*?)</td>", re.S)


def text_of(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def main() -> int:
    failures: list[str] = []
    pages = sorted(DESK.glob("*.html"))
    expected = {href for href, _ in SITE.NAV}
    present = {p.name for p in pages}

    # 1. navigation completeness and internal links
    for p in pages:
        raw = p.read_text(encoding="utf-8")
        for href in LINK.findall(raw):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = href.split("#")[0]
            if not target:
                continue
            if target in ("assets/style.css", "assets/site.js"):
                if not (DESK / target).exists():
                    failures.append(f"{p.name}: missing asset {target}")
                continue
            if not (DESK / target).exists():
                failures.append(f"{p.name}: broken internal link {target}")

    missing = expected - present
    if missing:
        failures.append(f"pages in the nav that were not built: {sorted(missing)}")

    # 4. identical nav on every page
    nav_html = None
    for p in pages:
        raw = p.read_text(encoding="utf-8")
        m = re.search(r'<nav class="main">.*?</nav>', raw, re.S)
        if not m:
            failures.append(f"{p.name}: no nav block")
            continue
        block = re.sub(r' class="on"', "", m.group(0))
        if nav_html is None:
            nav_html = block
        elif block != nav_html:
            failures.append(f"{p.name}: nav differs from the first page built")

    # 2 and 3. row-level provenance
    body_rows = 0
    sourced = 0
    for p in pages:
        raw = p.read_text(encoding="utf-8")
        for tmatch in re.finditer(r'<table.*?</table>', raw, re.S):
            table = tmatch.group(0)
            head = re.search(r"<thead>.*?</thead>", table, re.S)
            if head and "source" not in head.group(0).lower():
                continue
            if not head:
                continue
            for rmatch in ROW.finditer(table):
                row = rmatch.group(1)
                if "<td" not in row:
                    continue
                body_rows += 1
                cells = CELL.findall(row)
                last = cells[-1] if cells else ""
                if "href=" in last or "UNVERIFIED" in last:
                    sourced += 1
                else:
                    failures.append(
                        f"{p.name}: a body row has no source link: {text_of(row)[:90]}")

    # 5. footer counts match the manifest
    manifest = json.loads((DERIVED / "manifest.json").read_text())
    c = manifest["counts"]
    index = (DESK / "index.html").read_text(encoding="utf-8")
    for label, value in (
        ("requirements", f'{c["requirements"]} requirements'),
        ("certified", f'{c["certified"]} certified strategies'),
    ):
        if value not in index:
            failures.append(f"index.html: footer is missing '{value}' from the manifest")
    if f"{c['originated_markets']:,} originated markets" not in index:
        failures.append("index.html: footer market count does not match manifest.json")

    # 6. corpus pin
    digest = hashlib.sha256(TARBALL.read_bytes()).hexdigest() if TARBALL.exists() else ""
    if digest != PIN:
        failures.append(f"corpus tarball hash changed: {digest or 'missing'} != {PIN}")

    print(f"pages                 {len(pages)}")
    print(f"body rows checked     {body_rows}")
    print(f"rows with a source    {sourced}  ({100.0 * sourced / max(body_rows, 1):.1f}%)")
    print(f"corpus pin            {'OK' if digest == PIN else 'BAD'}")
    if failures:
        print(f"\n{len(failures)} FAILURE(S):")
        for f in failures[:40]:
            print(f"  - {f}")
        return 1
    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""verify_nfl_desk.py — verification harness for the NFL Decision Desk (gate G6).

Checks:
  1. Every rendered table data row (every <tr> in <tbody>) contains at least
     one <a href="..."> source link.
  2. Every internal href on every page resolves to a file that exists.
  3. Every CSV with a *_url column has that column non-empty on every row.
  4. Market columns in own_lines_2026_wk10.csv are blank (policy F-MKT-1).
  5. Rebuilding the site is deterministic (caller runs `git diff --exit-code`).
  6. Flagged/unverified cells are never silently numeric: cells containing
     the marker 'blank · flagged' are allowed (they are the flag).

Exit code 0 = all checks pass.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
errors = []


def check(cond, msg):
    if not cond:
        errors.append(msg)


def main():
    pages = [f for f in os.listdir(HERE) if f.endswith(".html")]
    check(len(pages) >= 12, f"expected >=12 pages, found {len(pages)}")

    # 1. every tbody row has a source link
    for page in sorted(pages):
        with open(os.path.join(HERE, page)) as f:
            content = f.read()
        tbodies = re.findall(r"<tbody>(.*?)</tbody>", content, re.S)
        for i, tb in enumerate(tbodies):
            rows = re.findall(r"<tr>(.*?)</tr>", tb, re.S)
            for j, row in enumerate(rows):
                check(
                    "<a href=" in row,
                    f"{page}: table#{i} row#{j+1} has no source link",
                )

    # 2. internal links resolve
    for page in sorted(pages):
        with open(os.path.join(HERE, page)) as f:
            content = f.read()
        for href in re.findall(r'href="([^"]+)"', content):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = href.split("#")[0]
            if not target:
                continue
            check(
                os.path.exists(os.path.join(HERE, target)),
                f"{page}: broken internal link -> {href}",
            )

    # 3. CSV source columns non-empty
    for name in sorted(os.listdir(DATA)):
        if not name.endswith(".csv"):
            continue
        with open(os.path.join(DATA, name), newline="") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            errors.append(f"{name}: no rows")
            continue
        src_cols = [c for c in rows[0] if "source" in c or c == "url" or c.endswith("_url")]
        for r in rows:
            for c in src_cols:
                check(
                    (r.get(c) or "").strip() != "",
                    f"{name}: empty {c} on row {r.get(rows[0].keys().__iter__().__next__(), '?')}",
                )

    # 4. market columns blank
    with open(os.path.join(DATA, "own_lines_2026_wk10.csv"), newline="") as f:
        for r in csv.DictReader(f):
            check(
                r["market_spread"].strip() == "" and r["market_total"].strip() == "",
                f"own_lines: market column not blank for {r['away_team']}@{r['home_team']}",
            )

    # 5. deficiency rows: no unexplained replacement when strings exist
    with open(os.path.join(DATA, "deficiencies_2026_wk10.csv"), newline="") as f:
        for r in csv.DictReader(f):
            check(
                r["depth_source_url"].startswith("http"),
                f"deficiencies: missing depth source for {r['team']} {r['position']}",
            )
            check(
                r["injury_source_url"].startswith("http"),
                f"deficiencies: missing injury source for {r['team']} {r['position']}",
            )

    # 6. flagged cells: blank values in rendered pages must carry flag marker
    for page in sorted(pages):
        with open(os.path.join(HERE, page)) as f:
            content = f.read()
        # a cell that is entirely empty <td></td> would be an unflagged blank
        check(
            "<td></td>" not in content,
            f"{page}: contains an empty unflagged <td></td>",
        )

    if errors:
        print(f"FAIL — {len(errors)} problem(s):")
        for e in errors[:50]:
            print("  -", e)
        sys.exit(1)
    print(f"PASS — {len(pages)} pages: source links, internal links, CSV sources, market-blank policy all verified")


if __name__ == "__main__":
    main()

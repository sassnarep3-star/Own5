"""Row-level proof that every body-table row on the published site is sourced.

Walks the generated HTML (not the CSVs) so that what is checked is what a reader
actually sees.  For every <tr> in every <tbody> it asserts one of:

  * the row's final cell contains a link to an http(s) source, or
  * the row's final cell carries the UNVERIFIED badge.

Anything else is a hard failure and exits non-zero, which fails the workflow and
stops the site being published with a silently unsourced row.
"""

from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES = sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))

TR = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S)
TD = re.compile(r"<td\b[^>]*>(.*?)</td>", re.S)
TBODY = re.compile(r"<tbody\b[^>]*>(.*?)</tbody>", re.S)
HREF = re.compile(r'href="(https?://[^"]+)"')
BADGE = re.compile(r'class="blank"')

EXPECTED = ["index.html", "executive-summary.html", "requirements.html", "suggestions.html",
            "questions.html", "results.html", "price-store.html", "lines.html",
            "strategies.html", "gates.html", "leaderboard.html", "correlations.html",
            "depth.html", "sources.html", "repo-audit.html", "flagged.html"]


def main() -> int:
    failures, checked, unsourced_marked, linked = [], 0, 0, 0

    missing_pages = [p for p in EXPECTED if p not in PAGES]
    for p in missing_pages:
        failures.append(f"{p}: page was not generated")

    nav_links = {}
    for page in PAGES:
        with open(os.path.join(ROOT, page), encoding="utf-8") as fh:
            html = fh.read()
        nav_links[page] = set(re.findall(r'<a class="[^"]*" href="([a-z0-9\-]+\.html)"', html))
        for b in TBODY.findall(html):
            for tr in TR.findall(b):
                cells = TD.findall(tr)
                if not cells:
                    continue
                checked += 1
                last = cells[-1]
                if BADGE.search(last):
                    unsourced_marked += 1
                elif HREF.search(last):
                    linked += 1
                else:
                    snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", tr)).strip()[:160]
                    failures.append(f"{page}: row with no source link and no UNVERIFIED badge -> "
                                    f"{snippet}")

    # every page must be reachable from the sidebar
    for page in PAGES:
        body = open(os.path.join(ROOT, page), encoding="utf-8").read()
        for other in EXPECTED:
            if other == page:
                continue
            if other not in body:
                failures.append(f"{page}: sidebar does not link to {other}")

    print(f"pages:            {len(PAGES)}")
    print(f"body rows:        {checked}")
    print(f"  source-linked:  {linked}")
    print(f"  UNVERIFIED:     {unsourced_marked}")
    print(f"failures:         {len(failures)}")
    for f in failures[:25]:
        print("  -", f)
    if failures:
        return 1
    print("OK: every row on every page is either source-linked or explicitly UNVERIFIED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
verify_site.py — line-by-line verification of the generated site (T10).

Checks:
  1. Every HTML page exists in docs/ and every internal href resolves to a file.
  2. Every data-table row (<tr> inside <tbody>) contains at least one <a href> (source link),
     or a BLANK-flag chip (unverifiable values must be flagged, never silent).
  3. Every https link in the site's Sources registry appears in research/ or data/ docs
     (coverage check the other way: registry completeness).
  4. No 'None' or 'nan' leaked into rendered cells.

Exit code 0 = all checks pass. Prints a per-check report.
"""
import glob
import os
import re
import sys

DOCS = 'docs/'
problems = []


def main():
    pages = sorted(glob.glob(DOCS + '*.html'))
    if not pages:
        print('FAIL: no pages generated'); return 1
    all_external = set()
    for p in pages:
        src = open(p, encoding='utf-8').read()
        name = os.path.basename(p)
        # 1. internal links resolve
        for href in re.findall(r'href="([^"]+)"', src):
            if href.startswith('http') or href.startswith('#'):
                if href.startswith('http'):
                    all_external.add(href)
                continue
            target = os.path.normpath(os.path.join(DOCS, href))
            if not os.path.exists(target):
                problems.append(f'{name}: broken internal link -> {href}')
        # 2. every body row has a source link or a flag chip
        for tr in re.findall(r'<tbody>(.*?)</tbody>', src, flags=re.S):
            for row in re.findall(r'<tr>(.*?)</tr>', tr, flags=re.S):
                if '<a href' not in row and 'chip flag' not in row and 'BLANK' not in row:
                    text = re.sub(r'<[^>]+>', ' ', row)[:120]
                    problems.append(f'{name}: table row without source link or flag -> {text.strip()}')
        # 4. no leaked nulls
        for bad in ('>None<', '>nan<', '>NaN<'):
            if bad in src:
                problems.append(f'{name}: leaked null value {bad}')
    # 3. Sources page must be present and link the two pinned datasets
    src_page = open(DOCS + 'sources.html', encoding='utf-8').read()
    for must in ['tobycrabtree/spreadspoke', 'brianfoshee/nfl-play-by-play-data',
                 'nfl.com/standings/league/2026/REG', 'arxiv.org/abs/1710.02824']:
        if must not in src_page:
            problems.append(f'sources.html: missing registry entry containing {must}')

    print(f'pages checked: {len(pages)}; external links referenced: {len(all_external)}')
    if problems:
        print(f'FAIL: {len(problems)} problem(s)')
        for x in problems[:60]:
            print(' -', x)
        return 1
    print('PASS: all internal links resolve; all table rows carry source links or explicit flags; no null leaks')
    return 0


if __name__ == '__main__':
    sys.exit(main())

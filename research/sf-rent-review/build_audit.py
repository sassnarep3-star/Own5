#!/usr/bin/env python3
"""Produce the auditable row-to-primary-source register from site data."""
from pathlib import Path
import argparse
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
pages = json.loads((ROOT / 'sf-rent-review/data/pages.json').read_text(encoding='utf-8'))
sources = json.loads((ROOT / 'sf-rent-review/data/sources.json').read_text(encoding='utf-8'))


def clean(value):
    return value.replace('|', '\\|').replace('\n', ' ') if value else '*[blank; unverified]*'


def render():
    out = ['# Row-by-row evidence register', '',
           'Snapshot: 2026-11-06. These records mirror the public dashboard, with stable row IDs and the exact official source links used. Each statement was reviewed within the scope recorded in `VERIFICATION.md` and `sf-rent-review/data/sources.json`. Recommendations are assessments, not official findings. A source link to a legal rule does not confirm a private fact. This is not legal review.', '',
           '| Row | Page · section | Finding / values in display order | Official sources |',
           '|---|---|---|---|']
    for slug, page in pages.items():
        for section in page['sections']:
            for row in section['rows']:
                fields = ' · '.join(clean(value) for value in row['cells'])
                citations = ' · '.join(f'[{sid}]({sources[sid]["url"]})' for sid in row['sources'])
                out.append(f'| `{row["id"]}` | {clean(page["nav"])} · {clean(section["title"])} | {fields} | {citations} |')
    out.append('')
    return '\n'.join(out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    output = HERE / 'ROW_AUDIT.md'
    content = render()
    if args.check:
        if not output.exists() or output.read_text(encoding='utf-8') != content:
            raise SystemExit('Row evidence register is out of date')
        print('Row evidence register matches current data.')
    else:
        output.write_text(content, encoding='utf-8')
        print('Wrote row evidence register.')

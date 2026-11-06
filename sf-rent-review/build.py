#!/usr/bin/env python3
"""Deterministically render the static, source-linked SF rent review site."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
SOURCES = json.loads((HERE / 'data' / 'sources.json').read_text(encoding='utf-8'))
PAGES = json.loads((HERE / 'data' / 'pages.json').read_text(encoding='utf-8'))
ALLOWED_HOSTS = {'www.sf.gov', 'leginfo.legislature.ca.gov', 'www.dre.ca.gov',
                 'calcivilrights.ca.gov', 'www.gao.gov', 'www.justice.gov',
                 'www.hud.gov', 'www.congress.gov'}
NAV = [('index', 'Overview'), ('units', 'Unit review'), ('rules', 'Rules & rates'),
       ('notice', 'Notice & process'), ('fairness', 'Fairness & rights'),
       ('practice', 'Owner practices'), ('review', 'Flagged for review'),
       ('sources', 'Source library')]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def validate() -> None:
    assert list(PAGES) == [name for name, _ in NAV if name != 'sources']
    seen = set()
    for sid, source in SOURCES.items():
        assert sid.startswith('S') and len(sid) == 3
        url = urlsplit(source['url'])
        assert url.scheme == 'https' and url.hostname in ALLOWED_HOSTS, (sid, source['url'])
        assert source['checked'] == '2026-11-06' and source['verified_scope']
    for page in PAGES.values():
        assert page['title'] and page['description'] and page['sections']
        for section in page['sections']:
            assert section['id'] and section['rows'] and section['columns']
            for row in section['rows']:
                assert row['id'] not in seen, row['id']
                seen.add(row['id'])
                assert len(row['cells']) == len(section['columns']), row['id']
                assert row['sources'] and set(row['sources']) <= SOURCES.keys(), row['id']
                assert all(isinstance(cell, str) for cell in row['cells'])


def source_links(ids: list[str]) -> str:
    links = []
    for sid in ids:
        src = SOURCES[sid]
        links.append(f'<a class="source-link" href="{esc(src["url"])}" '
                     f'target="_blank" rel="noopener noreferrer" '
                     f'aria-label="{esc(sid + ": " + src["title"])} (opens in a new tab)" '
                     f'title="{esc(src["title"])}">{esc(sid)} <span aria-hidden="true">↗</span></a>')
    return '<div class="source-links">' + ''.join(links) + '</div>'


def render_cell(value: str, first: bool = False) -> str:
    if not value:
        return '<span class="empty-value" aria-label="Unverified; intentionally blank">—</span>'
    if first:
        return f'<strong>{esc(value)}</strong>'
    return esc(value)


def render_section(section: dict) -> str:
    headers = ''.join(f'<th scope="col">{esc(h)}</th>' for h in section['columns'])
    headers += '<th scope="col" class="source-heading">Official source</th>'
    rows = []
    for row in section['rows']:
        cells = ''.join(f'<td>{render_cell(value, i == 0)}</td>' for i, value in enumerate(row['cells']))
        rows.append(f'<tr data-record-id="{esc(row["id"])}" data-sources="{esc(" ".join(row["sources"]))}">'
                    f'{cells}<td>{source_links(row["sources"])}</td></tr>')
    return f'''<section class="content-section" id="{esc(section['id'])}">
<div class="section-heading"><div><span class="eyebrow">SOURCE-LINKED RECORDS</span><h2>{esc(section['title'])}</h2><p>{esc(section['intro'])}</p></div><span class="section-count">{len(rows):02d} records</span></div>
<p class="scroll-hint">Scroll sideways to see every column and source <span aria-hidden="true">→</span></p><div class="table-shell"><div class="table-scroll" role="region" tabindex="0" aria-label="{esc(section['title'])}: scroll horizontally to see all columns"><table><caption class="sr-only">{esc(section['title'])}. An em dash is an intentionally blank, unverified value.</caption><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table></div></div>
</section>'''


def render_source_library() -> str:
    rows = []
    for sid, source in SOURCES.items():
        rows.append(f'''<tr data-record-id="{esc(sid)}" data-sources="{esc(sid)}">
<td><strong>{esc(sid)}</strong></td><td><strong>{esc(source['title'])}</strong><span class="cell-sub">{esc(source['verified_scope'])}</span></td>
<td>{esc(source['checked'])}</td><td>{source_links([sid])}</td></tr>''')
    return f'''<section class="content-section" id="source-register"><div class="section-heading"><div>
<span class="eyebrow">PRIMARY SOURCES ONLY</span><h2>Source register</h2><p>Each document was opened for the stated scope. A government link cannot establish an unverified private lease fact.</p></div><span class="section-count">{len(rows):02d} sources</span></div>
<p class="scroll-hint">Scroll sideways to see every column and source <span aria-hidden="true">→</span></p><div class="table-shell"><div class="table-scroll" role="region" tabindex="0" aria-label="Source register: scroll horizontally to see all columns"><table><caption class="sr-only">Official source register and the scope checked.</caption>
<thead><tr><th scope="col">Ref</th><th scope="col">Source and checked scope</th><th scope="col">Reviewed</th><th scope="col">Official source</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></div></section>'''


def navigation(current: str) -> str:
    links = []
    for i, (name, label) in enumerate(NAV):
        active = ' class="nav-link active" aria-current="page"' if name == current else ' class="nav-link"'
        links.append(f'<a{active} href="{name}.html"><span class="nav-number">{i+1:02d}</span>'
                     f'<span>{esc(label)}</span><span class="nav-arrow" aria-hidden="true">↗</span></a>')
    return ''.join(links)


def illustration() -> str:
    # A generic illustration; deliberately not an image of the property.
    return '''<div class="hero-art" aria-hidden="true"><div class="sun-disc"></div>
<svg viewBox="0 0 330 230" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M7 197H324" stroke="#759384" stroke-width="1.5"/><path d="M25 195V87L82 63L140 87V195M140 195V57L200 33L260 57V195M260 195V91L304 76V195" fill="#E3ECE4" stroke="#406C5B" stroke-width="2" stroke-linejoin="round"/>
<path d="M25 87H140M140 57H260M260 91H304M16 195H314M52 195V154H80V195M179 195V148H207V195M274 195V156H292V195" stroke="#406C5B" stroke-width="2"/>
<path d="M44 106H68V132H44zM96 106H120V132H96zM160 80H184V111H160zM216 80H240V111H216zM160 123H184V139H160zM216 123H240V139H216zM271 107H292V130H271z" fill="#C8DCCF" stroke="#406C5B" stroke-width="1.5"/>
<path d="M56 106V132M108 106V132M172 80V111M228 80V111M281 107V130" stroke="#406C5B" stroke-width="1.2"/>
<path d="M20 79L82 52L146 79M132 48L200 21L268 48" stroke="#406C5B" stroke-width="2" stroke-linecap="round"/>
<circle cx="312" cy="55" r="2" fill="#799687"/><circle cx="15" cy="49" r="2" fill="#799687"/>
</svg><span class="art-label">ILLUSTRATIVE ONLY · NOT THE PROPERTY</span></div>'''


def home_content() -> str:
    return '''<div class="metric-grid" aria-label="Key facts">
<a class="metric-card" href="rules.html#rates"><span class="metric-label">CURRENT ANNUAL ALLOWANCE <span aria-hidden="true">↗</span></span><strong>1.6<span>%</span></strong><small>For covered units · through Feb 28, 2027</small></a>
<a class="metric-card" href="rules.html#how-it-works"><span class="metric-label">STANDARD INTERVAL <span aria-hidden="true">↗</span></span><strong>12 <span>months</span></strong><small>Between ordinary annual increases</small></a>
<a class="metric-card" href="notice.html#timing"><span class="metric-label">WRITTEN NOTICE <span aria-hidden="true">↗</span></span><strong>30 <span>days</span></strong><small>Minimum in the ordinary ≤10% case</small></a>
<a class="metric-card status-metric" href="review.html"><span class="metric-label">UNIT-SPECIFIC STATUS <span aria-hidden="true">↗</span></span><strong>Not cleared</strong><small>Private facts remain unverified</small></a>
</div>
<section class="decision-panel"><div><span class="eyebrow light">A CONSIDERED STARTING POINT</span><h2>Keep it simple, and keep it fair.</h2><p>Consider no increase, or an ordinary-only adjustment within the applicable annual allowance after independent verification. A lower amount is permitted; the maximum is not a measure of what owners normally charge.</p><a href="units.html">Review the two units <span aria-hidden="true">→</span></a></div><div class="decision-side"><span>BEFORE YOU DECIDE</span><p>Coverage, lawful base rent, lease terms, notice history, and a current license all matter.</p><a href="https://www.sf.gov/information--banked-rent-increases" target="_blank" rel="noopener noreferrer">Read the Rent Board guidance ↗</a></div></section>
<div class="quick-links"><div><span class="eyebrow">EXPLORE THE BRIEF</span><h2>Start with what matters.</h2></div><a href="notice.html"><span>01</span><strong>How to give notice</strong><b aria-hidden="true">↗</b></a><a href="fairness.html"><span>02</span><strong>Fairness &amp; rights</strong><b aria-hidden="true">↗</b></a><a href="review.html"><span>03</span><strong>Open review items</strong><b aria-hidden="true">↗</b></a></div>'''


def draft_notice() -> str:
    return '''<section class="example-notice" aria-labelledby="example-title"><div class="example-heading"><div><span class="eyebrow">COMMUNICATION OUTLINE</span><h2 id="example-title">A starting point, not a notice to serve.</h2><p>Facts and service have not been verified. This illustrative outline cannot itself change rent.</p></div><span class="review-pill">NOT READY TO SERVE</span></div>
<div class="letter"><p>Dear tenant,</p><p>I am writing about a proposed ordinary annual rent adjustment under San Francisco’s Rent Ordinance. The proposed details would be:</p><dl class="letter-fields"><div><dt>Verified current base rent</dt><dd>—</dd></div><div><dt>Annual increase · amount and percentage</dt><dd>—</dd></div><div><dt>Any banked portion, separately identified</dt><dd>—</dd></div><div><dt>Proposed new base rent</dt><dd>—</dd></div><div><dt>Effective date</dt><dd>—</dd></div></dl><p>Please contact the housing provider with questions. You may also contact the San Francisco Rent Board for information about rent increases.</p><p class="letter-note">The content, all fields, recipient, timing, service method, and any required forms must be independently reviewed before use. <a href="https://www.sf.gov/learn-about-rent-increases-san-francisco" target="_blank" rel="noopener noreferrer">Rent Board guidance ↗</a> · <a href="https://www.sf.gov/information--sec-373-rent-limitations" target="_blank" rel="noopener noreferrer">SF § 37.3 ↗</a></p></div></section>'''


def template(name: str, page: dict) -> str:
    is_home = name == 'index'
    title = page['title']
    breadcrumb = dict(NAV)[name]
    art = illustration() if is_home else ''
    hero_class = 'hero hero-home' if is_home else 'hero hero-subpage'
    home = home_content() if is_home else ''
    sections = ''.join(render_section(section) for section in page.get('sections', []))
    if name == 'sources':
        sections = render_source_library()
    if name == 'notice':
        sections += draft_notice()
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(page['description'])}"><meta name="color-scheme" content="light">
<title>{esc(breadcrumb)} · SF Rent Review</title><link rel="stylesheet" href="assets/style.css"><link rel="icon" href="assets/favicon.svg" type="image/svg+xml"></head>
<body><a class="skip-link" href="#main-content">Skip to content</a><div class="app-shell">
<aside class="sidebar"><a class="brand" href="index.html" aria-label="SF Rent Review home"><span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></span><span>SF RENT<span class="brand-second">REVIEW</span></span></a><div class="sidebar-context"><span class="context-dot"></span> OUTER SUNSET · 94122</div>
<p class="nav-label">RESEARCH DESK</p><nav aria-label="Site navigation">{navigation(name)}</nav>
<div class="sidebar-bottom"><span class="side-sparkle" aria-hidden="true">✳</span><p>Clear information.<br><strong>Thoughtful decisions.</strong></p><a href="sources.html">About this research <span aria-hidden="true">→</span></a></div></aside>
<main class="main" id="main-content"><div class="topbar"><div><span class="topbar-parent">SF RENT REVIEW</span><span class="topbar-sep">/</span><span>{esc(breadcrumb)}</span></div><div class="topbar-right"><span class="topbar-dot"></span><span>Snapshot · Nov 6, 2026</span></div></div>
<div class="main-inner"><section class="{hero_class}"><div class="hero-copy"><span class="eyebrow"><span class="eyebrow-dot"></span> {esc(page['kicker'])}</span><h1>{esc(title)}</h1><p>{esc(page['description'])}</p><div class="hero-actions"><a class="button button-primary" href="{'units.html' if is_home else 'review.html'}">{'Review both units' if is_home else 'View review items'} <span aria-hidden="true">→</span></a><a class="button button-text" href="sources.html">Browse official sources <span aria-hidden="true">↗</span></a></div></div>{art}</section>
{home}<aside class="information-bar"><span class="info-symbol" aria-hidden="true">i</span><p><strong>Research, not legal clearance.</strong> Property-specific facts and legal review are unverified. Rules are a dated snapshot and may change. <a href="review.html">See what remains open →</a></p></aside>
{sections}<footer class="footer"><div><strong>SF RENT REVIEW</strong><span>Independent, privacy-first research</span></div><div>Snapshot: 06 Nov 2026 · Not legal advice <span> / </span><a href="sources.html">Source library</a> <span> / </span><a href="../index.html">Repository home ↗</a></div></footer></div></main></div></body></html>'''


def outputs() -> dict[str, str]:
    validate()
    result = {name + '.html': template(name, page) for name, page in PAGES.items()}
    source_page = {'title': 'Every conclusion starts with a source.', 'kicker': 'THE EVIDENCE LIBRARY',
                   'description': 'Government sources, checked for a clearly described scope. Follow each link to review the underlying rules and their limits.'}
    result['sources.html'] = template('sources', source_page)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='fail if generated HTML differs from the committed output')
    args = parser.parse_args()
    bad = []
    for path, content in outputs().items():
        file = HERE / path
        content += '\n'
        if args.check:
            if not file.exists() or file.read_text(encoding='utf-8') != content:
                bad.append(path)
        else:
            file.write_text(content, encoding='utf-8')
    if bad:
        print('Generated pages out of date:', ', '.join(bad))
        return 1
    print(f'{"Checked" if args.check else "Built"} {len(outputs())} pages and {len(SOURCES)} official sources.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

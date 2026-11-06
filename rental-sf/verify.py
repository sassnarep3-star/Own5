#!/usr/bin/env python3
"""Deterministic checks for the rental-sf static site. No third-party deps.
Usage: python3 rental-sf/verify.py [repo-root]
  1. HTML parses (tag balance)
  2. every local href/src resolves to an existing file
  3. every <tr> in <tbody> of tables marked data-verify (all content tables)
     contains at least one <a> (source link or flag link) — or text "n/a"/"BLANK"
  4. no obvious PII tokens from the source brief
  5. no external links to non-https URLs
"""
import os, re, sys
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'rental-sf')
VOID = {'br','img','hr','meta','link','input','source','area','base','col','embed','track','wbr'}

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[]; self.errs=[]; self.links=[]; self.tables=[]; self.cur_table=None; self.cur_row=None
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        for a in ('href','src','action'):
            if d.get(a): self.links.append(d[a])
        if tag=='table': self.cur_table={'rows':[], 'in_tbody':False}
        if tag=='tbody' and self.cur_table is not None: self.cur_table['in_tbody']=True
        if tag=='tr' and self.cur_table is not None and self.cur_table['in_tbody']:
            self.cur_row={'has_link':False,'text':'','has_note':False}
        if tag=='a' and self.cur_row is not None: self.cur_row['has_link']=True
        if tag not in VOID: self.stack.append(tag)
    def handle_data(self, data):
        if self.cur_row is not None:
            self.cur_row['text'] += data
            if 'BLANK' in data or 'n/a' in data.lower(): self.cur_row['has_note']=True
    def handle_endtag(self, tag):
        if tag=='tr' and self.cur_row is not None:
            self.cur_table['rows'].append(self.cur_row); self.cur_row=None
        if tag=='tbody' and self.cur_table is not None: self.cur_table['in_tbody']=False
        if tag=='table' and self.cur_table is not None:
            self.tables.append(self.cur_table); self.cur_table=None
        if tag in VOID: return
        if self.stack and self.stack[-1]==tag: self.stack.pop()
        else:
            if tag in self.stack:
                idx=len(self.stack)-1-self.stack[::-1].index(tag)
                self.errs.append(f"unclosed {self.stack[idx+1:]} before </{tag}>")
                del self.stack[idx:]
            else: self.errs.append(f"stray </{tag}>")

def main():
    files=[f for f in sorted(os.listdir(SITE)) if f.endswith('.html')]
    fail=0; warn=0
    total_rows=0
    for f in files:
        p=P(); src=open(os.path.join(SITE,f),encoding='utf-8').read(); p.feed(src)
        leftover=[t for t in p.stack]
        for e in p.errs: print(f"FAIL {f}: parse: {e}"); fail+=1
        if leftover: print(f"FAIL {f}: unclosed tags at EOF: {leftover}"); fail+=1
        for l in p.links:
            if l.startswith(('https://','http://','mailto:','tel:','#','data:','javascript:')): continue
            lp=urlparse(l).path; base=SITE
            if not lp: continue
            t=os.path.normpath(os.path.join(base,lp))
            if not os.path.exists(t): print(f"FAIL {f}: broken local ref -> {l}"); fail+=1
        for t in p.tables:
            for row in t['rows']:
                total_rows+=1
                if not row['has_link'] and not row['has_note']:
                    snippet=' '.join(row['text'].split())[:80]
                    print(f"WARN {f}: table row without source/flag link: \"{snippet}\""); warn+=1
        ext=[l for l in p.links if l.startswith('http://')]
        for l in ext: print(f"FAIL {f}: non-https external link: {l}"); fail+=1
    # PII scan (tokens that must never appear)
    pii=[r'L O', r'V N', r'J P', r'\bJP\b', r'E R', r'I S', r'outer sunset.*owner name']
    joined=' '.join(open(os.path.join(SITE,f),encoding='utf-8').read() for f in files)
    for pat in pii:
        if re.search(pat, joined): print(f"WARN manual PII review: pattern {pat!r} present (context may be benign)"); warn+=1
    print(f"\n{len(files)} pages, {total_rows} table rows checked; FAIL={fail}, WARN={warn}")
    return 1 if fail else 0

if __name__=='__main__': sys.exit(main())

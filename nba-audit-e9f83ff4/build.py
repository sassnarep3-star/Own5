"""Independent audit of the published ten-game sample, not a trading model."""
from pathlib import Path
import csv, html, importlib.util

root = Path(__file__).resolve().parent.parent
out = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('calc', root/'nba-2026-lab/compute.py')
calc = importlib.util.module_from_spec(spec); spec.loader.exec_module(calc)
rows = calc.load()
log = 'https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26'
injuries = 'https://official.nba.com/nba-injury-report-2026-27-season/'
def esc(x): return html.escape(str(x), quote=True)
def link(url, text='Official source'): return f'<a href="{esc(url)}">{esc(text)}</a>'
def table(headers, body):
    return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(cell)+'</td>' for cell in row)+'</tr>' for row in body)+'</tbody></table></div>'
nav = '<nav><a href="index.html">Overview</a><a href="sample.html">Verified sample</a><a href="review.html">Flagged for review</a><a href="../nba-2026-lab/">NBA lab</a></nav>'
def page(title, content):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} | NBA audit</title><link rel="stylesheet" href="style.css"></head><body><header><div class="wrap"><span class="eyebrow">OWN5 · INDEPENDENT AUDIT · 03 NOV 2026</span><h1>{esc(title)}</h1>{nav}</div></header><main class="wrap">{content}</main><footer class="wrap">Exploratory research, not betting advice. Values and inputs can change.</footer></body></html>'''
metrics = table(['Sample variables','Pearson r','Source and provenance'], [[esc(x+' × '+y),f'{r:+.4f}',link(log,'NBA player game log')+' · calculated locally'] for x,y,r in calc.correlations(rows)])
overview = '''<section class="hero"><p class="eyebrow">EXECUTIVE SUMMARY</p><h2>Evidence before edges.</h2><p>The existing NBA lab has an independently checked, ten-game historical sample. Its correlations describe this sample only. They do not establish a profitable signal, a current market edge, or a validated strategy.</p><div class="cards"><div><strong>10</strong><span>game rows checked</span></div><div><strong>0</strong><span>validated strategies reported by the lab</span></div><div><strong>—</strong><span>verified current prices</span></div></div></section><h2>Exploratory correlations</h2><p>Computed from the ten rows below, not published correlation values from the NBA. Points and threes overlap mechanically; these are not prop-hit or parlay correlations.</p>'''+metrics+'''<h2>What is missing</h2><p>Timestamped odds, rules and settlement, a prospective holdout, an automated feed, and funded reward terms. Luck cannot be eliminated; validation can only quantify uncertainty. Do not interpret rankings as proof of skill.</p><p><a href="sample.html">Inspect the checked rows →</a> &nbsp; <a href="review.html">Review limitations →</a></p>'''
sample = '<p>Each CSV field was compared with the first ten 2025–26 regular-season rows of the official player log on 2026-11-03. Minutes are the rounded integer displayed by that log. This is a convenience sample, not a representative dataset.</p>'+table(['Date','Opponent','Result','MIN','PTS','3PM','REB','AST','Sources'],[[esc(r[c]) for c in ('date','opponent','result','minutes','points','threes','rebounds','assists')]+[link(r['source'],'Game')+' · '+link(log,'Player log')] for r in rows])
flags = [
('F1','Sample is one player and ten games; no basis for generalizing to all players or markets.',log),
('F2','Pearson on raw statistics is not a correlation of settled leg outcomes; no thresholds or joint payouts are supplied.',log),
('F3','The existing lab has no timestamped market prices or settlement ledger; current lines, CLV, profit and rewards are unverified.',log),
('F4','The injury report is updated throughout the day. An as-of timestamp and historical snapshot are required to prevent look-ahead bias; this audit did not join injury statuses.',injuries),
('F5','Structural checks count official-domain links, not whether each linked source supports each claim. Full repository-wide line-by-line verification remains incomplete.',log),
('F6','No prospective out-of-sample validation or funded competition was independently established in this audit.',log),
('F7','Links to NBA game pages may default to a different pane; use the player log for the exact transcribed player statistics.',log),
]
review = '<p>These are audit observations, not claims that the linked NBA pages endorse a betting strategy. Blank or unverified values must not be used as inputs.</p>'+table(['ID','Finding','Relevant official source'],[[esc(a),esc(b),link(c)] for a,b,c in flags])
for name,title,content in [('index.html','NBA evidence audit',overview),('sample.html','Verified game sample',sample),('review.html','Flagged for review',review)]:
    (out/name).write_text(page(title,content),encoding='utf8')
print('Built 3 audit pages')

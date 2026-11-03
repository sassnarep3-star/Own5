"""Leave-one-game-out sensitivity for the existing, explicitly selected NBA sample."""
import csv
import html
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / 'nba-2026-lab/data/edwards_2025_26_recent10.csv'
OUTPUT = Path(__file__).with_name('index.html')
PAIRS = [('points', 'assists'), ('points', 'rebounds'), ('threes', 'points'), ('points', 'win'), ('assists', 'rebounds')]
LOG = 'https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26'

def corr(rows, x, y):
    a = [int(r[x]) if x != 'win' else int(r['result'] == 'W') for r in rows]
    b = [int(r[y]) if y != 'win' else int(r['result'] == 'W') for r in rows]
    am, bm = sum(a)/len(a), sum(b)/len(b)
    num = sum((v-am)*(w-bm) for v,w in zip(a,b))
    den = math.sqrt(sum((v-am)**2 for v in a)*sum((w-bm)**2 for w in b))
    return num/den if den else None

def analyze(rows):
    assert len(rows) == 10 and len({r['game_id'] for r in rows}) == 10
    assert all(r['source'] == 'https://www.nba.com/game/' + r['game_id'] + '/' for r in rows)
    result = []
    for x,y in PAIRS:
        full = corr(rows,x,y)
        loo = [(r, corr(rows[:i]+rows[i+1:],x,y)) for i,r in enumerate(rows)]
        assert full is not None and all(v is not None for _,v in loo)
        flips = sum((v > 0) != (full > 0) for _,v in loo)
        result.append((x,y,full,loo,flips))
    return result

def build():
    with INPUT.open(newline='') as f:
        rows = list(csv.DictReader(f))
    results = analyze(rows)
    e = html.escape
    cards = []
    for x,y,full,loo,flips in results:
        detail = ''.join(f'<tr><td><a href="{e(r["source"])}">{e(r["date"])} · {e(r["opponent"])} · {e(r["game_id"])}</a></td><td>{v:+.4f}</td></tr>' for r,v in loo)
        cards.append(f'<section><h2>{e(x)} × {e(y)}</h2><p>Full-sample r = <strong>{full:+.4f}</strong> (n=10); leave-one-out range <strong>{min(v for _,v in loo):+.4f} to {max(v for _,v in loo):+.4f}</strong> (n=9 each); sign reversals: <strong>{flips}/10</strong>. <a href="{LOG}">Official player log</a>.</p><details><summary>See all ten exclusions and official game links</summary><table><thead><tr><th>Excluded game (official source)</th><th>Remaining-nine r</th></tr></thead><tbody>{detail}</tbody></table></details></section>')
    page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NBA correlation sensitivity | Own5</title><style>body{{font:16px/1.5 system-ui,sans-serif;color:#e8eef9;background:#101827;max-width:950px;margin:0 auto;padding:24px}}a{{color:#88c8ff}}section{{background:#1b2940;border:1px solid #344560;border-radius:12px;margin:16px 0;padding:18px}}table{{border-collapse:collapse;width:100%}}td,th{{padding:8px;border-bottom:1px solid #344560;text-align:left}}summary{{cursor:pointer}}.warning{{border-left:4px solid #f5b942;padding:12px;background:#302a20}}nav a{{margin-right:16px}}</style></head><body><nav><a href="../nba-2026-lab/index.html">NBA lab</a><a href="../nba-2026-lab/review.html">Flagged for Review</a><a href="{LOG}">Official NBA player log</a></nav><h1>NBA correlation sensitivity audit</h1><p class="warning"><strong>Exploratory, not a betting signal.</strong> This is a convenience-selected ten-game historical sample, not a random sample or prospective holdout. Leave-one-out measures sensitivity, not confidence, predictive power, independence, or profit. No market odds or bet outcomes were verified. Zero strategies validated and zero rewards earned. The original lab's review flags remain open.</p><p>Computed directly from <a href="../nba-2026-lab/data/edwards_2025_26_recent10.csv">the ten recorded rows</a> (each row links to an official NBA game); compare with the <a href="{LOG}">official NBA player log</a>. Pearson r uses centered sums; each exclusion recomputes r from the other nine games. Values below are derived calculations, <strong>not figures published by the NBA</strong>. Source links support input review only.</p>{''.join(cards)}<p><a href="../nba-2026-lab/correlations.html">Original correlations</a> · <a href="https://github.com/sassnarep3-star/Own5/blob/main/nba-sensitivity/build.py">Calculation code</a></p></body></html>'''
    OUTPUT.write_text(page)
    return results

if __name__ == '__main__':
    build()
    print('Built', OUTPUT)

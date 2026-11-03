"""Reproducible descriptive statistics; never a model edge or bet recommendation."""
import csv
import math
from pathlib import Path

CSV = Path(__file__).parent / 'data' / 'edwards_2025_26_recent10.csv'
PAIRS = [('points', 'assists'), ('points', 'rebounds'), ('threes', 'points'), ('points', 'win'), ('assists', 'rebounds')]

def pearson(xs, ys):
    if len(xs) != len(ys) or len(xs) < 3:
        raise ValueError('Need at least three paired observations')
    mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
    a = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    dx = sum((x-mx)**2 for x in xs)
    dy = sum((y-my)**2 for y in ys)
    if not dx or not dy:
        raise ValueError('Zero variance; correlation undefined')
    return a / math.sqrt(dx*dy)

def load():
    with CSV.open(newline='') as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 10 or len({r['game_id'] for r in rows}) != len(rows):
        raise ValueError('Expected ten unique games')
    for r in rows:
        if not r['source'] == f"https://www.nba.com/game/{r['game_id']}/":
            raise ValueError('Missing official game source')
        for col in ('minutes','points','threes','rebounds','assists'):
            r[col] = int(r[col])
        if r['result'] not in ('W','L') or not (r['threes']*3 <= r['points']):
            raise ValueError('Invalid row')
        r['win'] = int(r['result']=='W')
    return rows

def correlations(rows):
    return [(x,y,pearson([r[x] for r in rows], [r[y] for r in rows])) for x,y in PAIRS]

if __name__ == '__main__':
    for x,y,r in correlations(load()):
        print(f'{x} × {y}: {r:+.4f} (n=10)')

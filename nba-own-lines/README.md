# NBA Own Lines — source-first research dashboard

Additive GitHub Pages namespace for session `636a7712`. It does not edit the root/NFL dashboard or any other NBA lab.

- **Snapshot:** 2026-11-03T23:39:30Z; NBA season 2026–27.
- **Evidence:** 30 official team rows, 16 official upcoming games, 4 selected players, 26 official player-game rows.
- **Output:** 16 analyst-calculated research game lines; 7 fail-closed strategy entries; 21 correlations; 4 held/suppressed player prop combos.
- **Decision:** 0 qualified strategies and 0 rewards. No sportsbook price, ROI, CLV, joint-hit probability or payout is invented.

## Reproduce

```bash
python3 nba-own-lines/model.py       # validate CSVs and regenerate derived.json
python3 nba-own-lines/build.py       # regenerate all HTML from the CSV evidence
python3 nba-own-lines/check.py       # links, row sources, deterministic derived data
python3 -m unittest discover -s nba-own-lines -p 'test_*.py' -v
```

All code uses the Python standard library. `model.py` owns formulas and gate logic; `build.py` only renders. `data/derived.json` and every HTML file are deterministic outputs. Official links support the NBA input values, not NBA endorsement of analyst assumptions or strategies.

## Publication

After merge to `main`, the expected URL is `https://sassnarep3-star.github.io/Own5/nba-own-lines/`. See `research/nba-own-lines/` for the source audit, methodology, requirements trace and executive summary. Publication/PR results are recorded in root `COORDINATION.md`.

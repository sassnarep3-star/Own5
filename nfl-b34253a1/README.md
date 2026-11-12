# NFL 2026 Week 10 research snapshot

An isolated, standard-library-only static research desk. The snapshot is dated **2026-11-12** and is descriptive—not betting advice, an executable odds service, or evidence of proven betting skill.

## Rebuild locally

Run from the repository root:

```sh
python3 nfl-b34253a1/seed.py
python3 nfl-b34253a1/engine.py
python3 nfl-b34253a1/content_seed.py
python3 nfl-b34253a1/audit_repo.py
python3 nfl-b34253a1/build.py
python3 nfl-b34253a1/verify.py
python3 -m unittest discover -s nfl-b34253a1/tests -v
```

The 13 static pages are `index.html` (overview) plus 12 categories. To preview from repository root, start `python3 -m http.server 3000 --bind 0.0.0.0` and open `/nfl-b34253a1/`.

`verify.py` checks the source URL fields, row counts, blank/unvalidated fields, 32-team/136-game reconciliation status, local HTML links, accessibility structure, and every physical-line audit SHA-256 against the indexed repository file. It is a structural/provenance check; it does not re-fetch dynamic sources or validate betting performance. A separate isolated workflow runs the project tests, existing repository unit suite, deterministic rebuild, and real Chromium desktop/mobile smoke checks.

## Key files

- `data/games_2026_w1_w9.csv`, `standings_2026_w10.csv`, `team_stats_2026_w10.csv`, `schedule_2026_w10.csv`: official-source-linked inputs.
- `data/market_quotes_2026_w10.csv`: 28 separate DraftKings/FanDuel quote rows; date-only capture, no preserved UTC timestamp/jurisdiction.
- `data/injuries_depth_w10.csv`, `depth_chart_coverage_2026_w10.csv`: 76 selected observations across 17 teams and 32 club-chart source checks (including four Week 10 bye teams).
- `data/model_lines_2026_w10.csv`, `walk_forward_2026_w2_w9.csv`, `correlations_2026.csv`: deterministic exploratory outputs; injury-adjusted lines and unsupported player-prop correlations remain blank.
- `data/strategies_2026.csv`, `validation_gates_2026.csv`, `leaderboard_2026.csv`, `luck_skill_2026.csv`: six unvalidated strategies; G0 passes and G1–G10 are blocked; no rankings or rewards.
- `data/repo_audit.csv`, `repo_audit_summary.json`: line-indexed audit of selected prior/shared NFL artifacts, with direct source versus fallback/comparator provenance distinguished.
- `../research/nfl-b34253a1/`: methodology, source notes, summary, injury notes, decision Q&A, suggestions, and flagged findings.

For full scope and caveats, read [`../research/nfl-b34253a1/EXECUTIVE_SUMMARY.md`](../research/nfl-b34253a1/EXECUTIVE_SUMMARY.md) and [`../research/nfl-b34253a1/METHODOLOGY.md`](../research/nfl-b34253a1/METHODOLOGY.md).
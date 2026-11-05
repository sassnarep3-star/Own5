# OWN5 NBA Research Desk — session 61a311c2

Evidence-first, static GitHub Pages dashboard and deterministic research engine.

## Run

```bash
python3 nba-research-61a311c2/engine.py
python3 nba-research-61a311c2/audit_repo.py
python3 nba-research-61a311c2/build.py
python3 -m unittest discover -s nba-research-61a311c2 -p 'test_*.py' -v
```

## Rules

- Every empirical table row has an official NBA source link; operator/method/project rows use their official publisher links.
- Unconfirmed values are blank/null and flagged. No ROI, probabilities, ranks or monetary rewards are fabricated.
- Legacy namespaces are read-only archives. Canonical inputs live in `data/`.
- Gates G01–G12 fail closed; current action is `PAPER_RESEARCH_ONLY`.

See `research/nba-research-61a311c2/EXECUTIVE_SUMMARY.md` and the dashboard `index.html`.

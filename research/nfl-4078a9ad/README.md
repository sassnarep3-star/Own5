# NFL Command Desk — session index

| Document | What it is |
|---|---|
| [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) | The one-page result: 150/150 games reconciled, 0 strategies certified, 6 missing datasets |
| [METHODOLOGY.md](METHODOLOGY.md) | Provenance rule, corpus merge rule, windows, model, metrics, demotion gate |
| [VERIFICATION.md](VERIFICATION.md) | Every page read with its stamp, every check performed, what was not verified |
| [REPO_REVIEW.md](REPO_REVIEW.md) | Review of the existing 32-desk repository, and the irregularities found |

Live pages: <https://sassnarep3-star.github.io/Own5/nfl-command-desk/>

Data: `nfl-command-desk/data/*.csv` (18 tables, every row source-linked or flagged).

Reproduce:

```
python3 nfl-command-desk/generate.py
python3 nfl-command-desk/build.py
python3 nfl-command-desk/verify.py
python3 -m unittest discover -s nfl-command-desk/tests -v
```

Registration commit (frozen before any published number):
`f85bb0b43ad00aa35ab27536ee42da052d8c3af0`.

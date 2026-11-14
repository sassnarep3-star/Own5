# Session `ce1f16ff` — dossier index

The site itself is published flat at
[`nfl-desk-ce1f16ff/`](../../nfl-desk-ce1f16ff/) (live at
<https://sassnarep3-star.github.io/Own5/nfl-desk-ce1f16ff/>) so that every table link
resolves relative to the CSVs it was built from. This directory is the markdown record:
what was measured, what was refused, and what would change the answer.

| Document | What it holds |
|---|---|
| [methodology.md](methodology.md) | The build order, the statistics used, and why each gate is written the way it is |
| [findings.md](findings.md) | Every headline number, with its `n`, interval and source |
| [refusals.md](refusals.md) | The claims this desk will not make, and the specific missing input behind each |

## Reproduce

```sh
cd nfl-desk-ce1f16ff
python3 run.py            # 43 tables + 13 pages from the committed inputs
python3 run.py --check    # prove the committed build equals a clean rebuild
python3 verify.py         # 32 checks
python3 -m unittest discover -s tests   # 82 tests
```

Standard library only. No network access is required or attempted at build time.

# NFL brief traceability — session 1911d7cd

**Page:** https://sassnarep3-star.github.io/Own5/nfl-brief-traceability/ (live after the Pages build on `main`)

Maps every item of the NFL brief to the register row that covers it, and records what this session re-checked.

| File | What it is |
|---|---|
| `build.py` | Generates `brief_traceability.csv` and `index.html`. Register statuses are read from `nfl-line-audit/data/requirements.csv`, not typed. |
| `verify.py` | Fail-closed checks (23). Exit 1 on any failure. Includes negative controls that prove each flag is real. |
| `flags.csv` | Nine irregularities (F-B01 to F-B09), each with a source link. |
| `official_wk11_IND_HOU.csv` | The official Week 11 rows for IND and HOU, transcribed from nfl.com/injuries (read 2026-11-19). |
| `spotcheck_wk11.csv` | Row-by-row comparison of those 26 official rows with the repo capture (25 PASS, 1 FAIL). |
| `reproduce.log` | Result of rebuilding nfl-line-audit from pinned inputs: zero tracked-file diffs. |
| `ci_investigation.md` | The red `pages-smoke` job on main, and what could and could not be confirmed. |

## Scope and limits

- Only the rows marked PASS or FAIL in the `this_session_check` column were re-checked in this session. Everything else shows the register's own claim, labelled NOT CHECKED. Nothing is marked verified without an official link.
- The official-source check covers IND and HOU only, 26 of the 255 Week 11 rows. Other clubs were not re-read.
- Rows whose source is a repository file are not official evidence. That is flag F-B05.

## Rebuild

```
python3 nfl-brief-traceability/build.py
python3 nfl-brief-traceability/verify.py
```

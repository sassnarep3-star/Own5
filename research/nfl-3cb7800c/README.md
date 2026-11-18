# Research note — session 3cb7800c (NFL Week 11 official-source desk)

Method, scope and sources for the desk in `nfl-desk-3cb7800c/`. The published site is the
`nfl-desk-3cb7800c/` directory; this note only records method.

* **Read stamp.** Every official page was read by the sandbox fetch tool on 2026-11-18 between
  03:13 and 03:14 UTC. The fetch tool returns processed page text, not server bytes (flag F-09).
* **What was not read.** Game pages linked from the schedule were not fetched. Injury report
  rows, inactives, snap counts, depth charts, game books and venues were not read.
* **Counting rule for desks.** See `nfl-desk-3cb7800c/data/desks_index.csv` and `tools/index_desks.py`.
* **Checks.** `nfl-desk-3cb7800c/verify.py` and `nfl-desk-3cb7800c/tests/test_desk.py`
  (negative controls included). CI: `.github/workflows/nfl-desk-3cb7800c.yml`.
* **Not done.** No model, price, backtest or leaderboard work. Those live in the sibling desks
  listed on the Desks index.

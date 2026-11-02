# Own5 — NFL Line Origination & Skill-Based Strategy Lab

Automated, fully-sourced research project for **originating our own NFL betting lines**: collect and organize official NFL data, generate signals, validate every strategy through gates, measure correlations, and rank surviving strategies on a leaderboard with reward tiers. Singles, parlays, and player-prop combos are covered.

- **Live site (GitHub Pages):** https://sassnarep3-star.github.io/Own5/
- **Task board / coordination:** [COORDINATION.md](COORDINATION.md)
- **Executive summary:** [research/executive-summary.md](research/executive-summary.md) · on the site: [Executive Summary](executive-summary.html)

## Verification policy (no hallucinations)

Every factual value in every table row links to an **official source** (nfl.com, media.nfl.com, operations.nfl.com, official club sites, official sportsbook operator pages, regulator-approved house rules, NCPG). Values that cannot be confirmed officially are left **blank** and published on the **Flagged for Review** page ([flagged.html](flagged.html) / `data/flagged.csv`). Nothing is ever inferred.

## Repo layout

| Path | Contents |
| --- | --- |
| `index.html` … `flagged.html`, `assets/` | GitHub Pages site (static, generated) |
| `data/*.csv` / `data/*.json` | All tables — one `source_url` per row |
| `research/*.md` | Research docs (prose source for the site pages) |
| `tools/seed_data.py` | Writes all `data/*.csv` deterministically (verified values + source links) |
| `tools/compute_correlations.py` | Computes `data/correlations.csv` from the official standings snapshot (asserts data consistency) |
| `tools/build_site.py` | Renders the static site from CSVs + research docs |
| `tools/check_site.py` | Verification: every CSV row has a source link; HTML pages contain no broken internal links |

## Reproduce

```bash
python3 tools/seed_data.py
python3 tools/compute_correlations.py
python3 tools/build_site.py
python3 tools/check_site.py
```

## Responsible gambling

Analytics research only. Sports betting is for adults of legal age in your jurisdiction and carries risk of loss. Help is available 24/7 and confidential: **1-800-GAMBLER (1-800-426-2537)**, text 800GAM, or chat — [National Council on Problem Gambling](https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/).

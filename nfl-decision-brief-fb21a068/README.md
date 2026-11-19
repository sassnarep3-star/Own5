# NFL Decision Brief

A dated, evidence-first review of the most consequential open decisions in Own5's NFL line-originating project. This is an additive companion to the existing NFL Command Desk; it does not rewrite another session's registers or claim that blocked requirements are complete.

## Build and verify

```sh
python3 build.py
python3 verify.py
```

The brief uses only published source references. It does not store or reproduce market prices, infer availability from blank cells, infer depth from jersey/roster order, or present unverified model performance as skill. `data/decision_register.csv` keeps each question and suggestion auditable; every row has a source URL, a status, and (where relevant) an internal evidence link.

## Current scope

- Official-source re-read: 2026-11-19 UTC (page-fetch timestamp resolution unavailable).
- Primary NFL sources: Week 11 schedule, Week 11 injury report, Week 11 game centre, 2026 schedule announcement, standings; official Houston Texans stadium page.
- Operator material: FanDuel Ontario house rules/parlay explainer and DraftKings NFL markets page, each scoped to what that page actually shows.
- Findings about existing site state link to the corresponding repository CSV as well as the official source page. They are repository audit findings, not claims that the official publisher endorsed a model or strategy.
- A direct run of the existing NFL Command Desk verifier produced 47 PASS / 3 FAIL. All three failures are the V11 registration checks: the cited registration SHA is absent from this checkout's Git object database. The brief flags this separately; do not rely on the affected pre-registration claim until the hash is repaired and verified.

## Deployment note

This directory is a static GitHub Pages-compatible subpage. Existing root navigation is intentionally untouched because it is owned by the shared integration work. From the published project site, use `nfl-decision-brief-fb21a068/`.

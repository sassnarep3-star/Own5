#!/usr/bin/env python3
"""One entry point for the whole desk: inputs -> results -> store -> model -> board -> site.

    python3 run.py            rebuild every derived table, then render the pages
    python3 run.py --check    rebuild into a scratch copy and report any difference
                              (this is what CI runs; it is how "committed = reproducible"
                              is enforced rather than asserted)

Order is a dependency chain, not a preference:
  inputs      verify digests, write the input register
  results     build the verified results feed and its 13 self-checks
  originate   walk-forward ratings -> fair side, fair total, fair moneyline
  grade       settled legs for the historical window
  ledger      signal and staking scoreboards, gates, calibration, naive comparison
  depth       replacement depth, graded by measured snaps
  availability injury ladder base rates, official counts, absence impact
  markets     price snapshot store, line sheet, gap register
  leaderboard division scores and rewards (consumes the gate table)
  gate        demotion gate (consumes everything above, fails closed)
  registers   suggestions, questions, flags, source register
  correlate   correlations from officially sourced numbers only, plus refusals
  build_site  render the pages from the committed CSVs
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
sys.path.insert(0, HERE)

STEPS = ["inputs", "results_feed", "originate", "grade", "ledger", "depth", "availability",
         "markets", "leaderboard", "gate", "registers", "correlate", "build_site"]
GENERATED = ["input_register.csv", "results_feed.csv", "results_checks.csv", "results_disagreements.csv",
             "fair_lines.csv", "model_ratings.csv", "backtest_predictions.csv", "derivation.csv",
             "settled_legs.csv", "leaderboard_signal.csv", "leaderboard_staking.csv", "validation.csv",
             "calibration.csv", "naive_comparison.csv", "naive_comparison_detail.csv", "multiplicity.csv",
             "exposure.csv", "staking_scenarios.csv", "replacement_depth.csv", "depth_by_team.csv",
             "depth_rules.csv", "absence_vs_depth.csv", "availability_base_rates.csv",
             "availability_wk10_official.csv", "availability_source_diff.csv", "availability_impact.csv",
             "price_snapshots.csv", "store_meta.csv", "line_sheet.csv", "market_gaps.csv",
             "market_summary.csv", "leaderboard.csv", "rewards.csv", "scoring_rules.csv",
             "demotion_gate.csv", "gate_rules.csv", "gate_integrity.csv", "suggestions.csv",
             "questions.csv", "flags.csv", "sources.csv", "correlations.csv", "game_conditions.csv"]


def run_all():
    out = {}
    import inputs
    out["inputs"] = len(inputs.register())
    import results_feed
    rows, dis = results_feed.build()
    results_feed.checks(rows)
    out["results"] = dict(rows=len(rows), disagreements=len(dis))
    import originate
    _, bt, meta = originate.write()
    out["originate"] = dict(backtest_rows=len(bt), tie_rate=round(meta["tie_rate"], 4))
    import grade
    bs, legs = grade.grade()
    out["grade"] = dict(strategies=len(bs), legs=len(legs))
    import ledger
    closing = 0
    p = os.path.join(DATA, "store_meta.csv")
    if os.path.exists(p):
        for r in csv_rows(p):
            if r and r[0] == "rows_stage_closing":
                closing = int(r[1])
    _, sig, stk, gt, passes = ledger.write(dict(closing_rows=closing, live_graded_bets=0))
    out["ledger"] = dict(strategies=len(sig), gates=len(gt), promoted=len(passes))
    import depth
    out["depth"] = depth.write()
    import availability
    out["availability"] = availability.write()
    import markets
    mk = markets.write()
    out["markets"] = dict(store=mk["store"]["rows"], sheet=mk["sheet"], gaps=mk["gaps"],
                          chain_ok=mk["chain_ok"])
    import leaderboard
    sc, rw = leaderboard.write()
    out["leaderboard"] = dict(entries=len(sc), awarded=sum(1 for r in rw if r["award"].startswith(("headline",)) ),
                              divisions=len(rw))
    import gate
    gr, gm = gate.write()
    out["gate"] = dict(strategies=len(gr), integrity_ok=gm["integrity_ok"], live_bets=gm["live"])
    import registers
    out["registers"] = registers.write()
    import correlate
    out["correlate"] = dict(rows=len(correlate.compute()))
    import build_site
    out["pages"] = build_site.build()
    return out


def csv_rows(path):
    import csv
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


PAGES_BUILT = ["index.html", "markets.html", "store.html", "results.html", "injuries.html",
               "depth.html", "leaderboard.html", "gates.html", "correlations.html",
               "suggestions.html", "questions.html", "flagged.html", "sources.html"]


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else "MISSING"


def digest_dir(d):
    out = {}
    for name in sorted(GENERATED):
        p = os.path.join(d, name)
        out[name] = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else "MISSING"
    return out


def check():
    """Rebuild in place over the committed inputs and report byte-level drift.

    Deliberately not a copy-into-scratch dance: the modules read pinned inputs by
    path relative to the repository and write ``data/`` by the same rule, so the only
    faithful test of "committed = reproducible" is to rebuild here and compare
    digests. A scratch copy would test a different directory layout, which is how a
    check passes locally and fails in CI.
    """
    committed = digest_dir(DATA)
    pages = {p: _sha(os.path.join(HERE, p)) for p in PAGES_BUILT}
    print("check mode: re-running the pipeline over the committed inputs")
    run_all()
    after = digest_dir(DATA)
    after_pages = {p: _sha(os.path.join(HERE, p)) for p in PAGES_BUILT}
    changed = sorted([k for k in after if after[k] != committed.get(k)]
                     + [f"page:{p}" for p in after_pages if after_pages[p] != pages.get(p)])
    absent = sorted(k for k, v in committed.items() if v == "MISSING" and after.get(k) == "MISSING")
    print(json.dumps(dict(deterministic=not changed, changed=changed,
                          never_produced=absent,
                          tables=len(after) - len(absent)), indent=1))
    if changed:
        print("::error::committed tables differ from a clean rebuild - run `python3 run.py` "
              "and commit the result", file=sys.stderr)
    return 0 if not changed else 1


def main():
    if "--check" in sys.argv:
        return check()
    summary = run_all()
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

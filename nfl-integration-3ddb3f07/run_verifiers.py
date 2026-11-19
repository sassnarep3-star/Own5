#!/usr/bin/env python3
"""Re-run every desk's own verifier and record the result.

This is the repository's line-by-line evidence: each desk proves its own tables, and the
outcome of every proof is written to data/verifier_runs.csv, which the front door
publishes. No timestamps are recorded, so re-running this file on an unchanged tree
produces the same bytes and the build's drift check stays meaningful.

Run:  python3 nfl-integration-3ddb3f07/run_verifiers.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from build_hub import verifier_sweep  # noqa: E402

OUT = HERE / "data" / "verifier_runs.csv"
FIELDS = ["desk", "command", "exit_code", "result", "summary"]


def main() -> int:
    rows = verifier_sweep()
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in FIELDS})
    failed = [r for r in rows if r["result"] != "PASS"]
    print(f"verifiers: {len(rows)} run, {len(rows) - len(failed)} PASS, {len(failed)} FAIL")
    for r in failed:
        print(f"  FAIL {r['desk']}: {r['summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run the whole Decision Desk pipeline in dependency order."""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ["parse_official.py", "compute_injuries.py", "compute_lines.py",
         "compute_strategies.py", "compute_correlations.py", "audit_repo.py"]


def main() -> int:
    html = os.path.join(HERE, "..", "..", ".work", "official", "injury_report_wk10.html")
    steps = list(STEPS)
    if not os.path.exists(html):
        # CI rebuilds from the committed snapshot; the official HTML is not
        # committed (multi-megabyte), so the parse step is skipped rather than
        # allowed to overwrite the committed parsed tables with an empty file.
        steps.remove("parse_official.py")
        print("note: .work/official HTML absent - reusing committed parsed tables")
    steps.insert(steps.index("audit_repo.py"), "export_registers.py")
    for step in steps:
        print(f"== {step}")
        rc = subprocess.call([sys.executable, os.path.join(HERE, step)])
        if rc != 0:
            print(f"FAILED {step}", file=sys.stderr)
            return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())

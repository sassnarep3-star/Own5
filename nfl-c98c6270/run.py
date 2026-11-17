#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One command to rebuild the whole desk: data, pages, then the proof.

    python3 run.py

Order matters and is fixed:
  1. engine.py   - deterministic: pinned official captures -> CSVs
  2. build_site.py - deterministic: CSVs -> HTML
  3. verify.py   - read-only: proves every published row is sourced or flagged

Nothing here fetches from the network. The captures in data/ are the pinned
evidence; re-reading the live pages is a separate, deliberately non-blocking
step in the workflow so that a league page changing cannot silently rewrite
what this desk publishes.
"""

from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

STEPS = [
    ("engine.py", "rebuild every table from the pinned official captures"),
    ("build_site.py", "render every page from those tables"),
    ("verify.py", "prove every published row is sourced or flagged"),
]


def run(script):
    proc = subprocess.run([sys.executable, script], cwd=HERE,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace")
    if proc.returncode != 0:
        print(out)
        print("FAILED: %s (exit %d)" % (script, proc.returncode))
        sys.exit(proc.returncode)
    return out


def main():
    for script, what in STEPS:
        print("== %s - %s" % (script, what))
        out = run(script)
        tail = out.strip().splitlines()[-6:]
        print("\n".join("   " + l for l in tail))
    print("\nOK: desk rebuilt and verified.")


if __name__ == "__main__":
    main()

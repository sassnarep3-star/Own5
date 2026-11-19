#!/usr/bin/env python3
"""Run every desk verifier (<dir>/verify*.py) from the repository root and record the result.

Each verifier runs inside a scratch copy of the working tree so a verifier that writes
files cannot mutate the repository under review (pattern proven by repo-review desk).
Output: ../data/nfl-desk-7e228db8/verifier_sweep.csv
"""
from __future__ import annotations

import csv
import io
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = REPO / "data" / "nfl-desk-7e228db8" / "verifier_sweep.csv"

# Skip build-only dirs that ship no verifier of their own, plus VCS internals.
SKIP_DIRS = {".git", ".github", "node_modules", "__pycache__"}

def find_verifiers(root: Path):
    out = []
    for d in sorted(p for p in root.iterdir() if p.is_dir() and p.name not in SKIP_DIRS):
        scripts = sorted(d.glob("verify*.py")) + sorted(d.glob("run_verifiers.py"))
        for s in scripts:
            out.append((d.name, s.relative_to(root)))
    return out

def main() -> int:
    rows = []
    with tempfile.TemporaryDirectory(prefix="own5-sweep-") as tmp:
        scratch = Path(tmp) / "tree"
        shutil.copytree(REPO, scratch, ignore=shutil.ignore_patterns(".git"))
        for desk, script in find_verifiers(REPO):
            t0 = time.time()
            try:
                proc = subprocess.run([sys.executable, str(script)], cwd=scratch,
                                      capture_output=True, text=True, timeout=180)
                rc, tail = proc.returncode, (proc.stdout + proc.stderr).strip().splitlines()[-1:]
                tail = tail[0][:180] if tail else ""
            except subprocess.TimeoutExpired:
                rc, tail = "timeout", "killed at 180s"
            except Exception as e:  # noqa: BLE001
                rc, tail = "error", str(e)[:180]
            rows.append([desk, str(script), rc, f"{time.time()-t0:.1f}s",
                         "PASS" if rc == 0 else "FAIL", tail])
    rows.sort(key=lambda r: (r[4] != "FAIL", r[0]))
    with io.open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["desk_directory", "script", "exit_code", "duration", "verdict", "last_output_line"])
        w.writerows(rows)
    n_pass = sum(1 for r in rows if r[4] == "PASS")
    print(f"verifier sweep: {len(rows)} scripts, {n_pass} PASS, {len(rows)-n_pass} FAIL -> {OUT}")
    for r in rows:
        if r[4] == "FAIL":
            print("  FAIL", r[0], r[1], "rc=", r[2], "|", r[5])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

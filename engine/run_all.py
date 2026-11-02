"""Reproduce every empirical output from the vendored raw data.

    python engine/run_all.py

Order matters: verification -> origination -> strategies -> correlations ->
skill/luck -> pricing -> gates. Each stage writes to data/empirical/.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = ["verify_official", "originate", "strategies", "correlations",
          "skill_luck", "pricing", "gates"]

for s in STAGES:
    print(f"\n{'='*70}\n{s}\n{'='*70}", flush=True)
    r = subprocess.run([sys.executable, str(HERE / f"{s}.py")], cwd=HERE)
    if r.returncode != 0:
        sys.exit(f"stage {s} failed")
print("\nAll stages complete.")

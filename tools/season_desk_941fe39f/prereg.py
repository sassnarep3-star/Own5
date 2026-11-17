"""Freeze the pre-registration for the 2026/27 NFL desk.

A pre-registration is only worth something if it can be shown to predate the
data it judges. This script writes `nfl-season-941fe39f/data/strategy/prereg.json`
containing every strategy's rule text, window, and gates, plus the git commit
that introduced the pre-registration module and a SHA-256 of each strategy's
rule text. Anyone can then check that no rule changed after the results were
seen.

Run AFTER committing `strategies.py`. If the working tree is dirty for the files
listed below, the script refuses to write, because a pre-registration made
against uncommitted code proves nothing.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "nfl-season-941fe39f" / "data" / "strategy" / "prereg.json"
WATCH = ["tools/season_desk_941fe39f/strategies.py",
         "tools/season_desk_941fe39f/model.py",
         "tools/season_desk_941fe39f/stats.py"]

sys.path.insert(0, str(Path(__file__).resolve().parent))
import strategies as S  # noqa: E402


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, check=False).stdout.strip()


def main() -> int:
    dirty = [f for f in WATCH if git("status", "--porcelain", "--", f)]
    if dirty and "--force" not in sys.argv:
        print("REFUSING TO WRITE: these files are uncommitted, so a pre-registration")
        print("made now cannot be shown to predate the data:")
        for f in dirty:
            print(f"  dirty  {f}")
        print("\nCommit them, then re-run. Use --force only if you intend to re-register.")
        return 1

    commit = git("rev-parse", "HEAD")
    subject = git("log", "-1", "--format=%s", commit)
    out = {
        "desk": "941fe39f",
        "written_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "registration_commit": commit,
        "registration_subject": subject,
        "registration_committed_utc": git("log", "-1", "--format=%cI", commit),
        "file_hashes": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
                        for f in WATCH},
        "windows": {
            "train": list(S.TRAIN),
            "validation": list(S.VALIDATION),
            "holdout": list(S.HOLDOUT),
            "prospective": list(S.PROSPECTIVE),
        },
        "staking_assumption": {
            "flat_stake_units_per_bet": S.RISK,
            "prereg_version": S.PREREG_VERSION,
            "vig": "one cent each way; a -110/-110 market is used for every ROI",
            "clv_definition": "close minus our devigged fair price, in probability points, "
                              "signed in favour of the side we took",
        },
        "strategies": [
            {
                "id": p["id"],
                "name": p["name"],
                "family": p["family"],
                "hypothesis": p.get("hypothesis", ""),
                "rule": p["rule"],
                "rule_sha256": hashlib.sha256(p["rule"].encode()).hexdigest(),
                "window": p.get("window", ""),
                "gates": S.GATES,
                "units": p.get("units", ""),
                "status_at_registration": p.get("status", "paper"),
            }
            for p in S.PREREG
        ],
        "amendment_policy": (
            "A rule may not be edited after registration. A change is a new strategy with "
            "a new id and a fresh window, and the superseded id stays on the leaderboard "
            "marked retired. The site reads this file and publishes the commit it was "
            "registered against."),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  registered against {commit[:12]} {subject[:60]}")
    print(f"  {len(out['strategies'])} strategies frozen, {len(S.GATES)} gates frozen")
    return 0


if __name__ == "__main__":
    sys.exit(main())

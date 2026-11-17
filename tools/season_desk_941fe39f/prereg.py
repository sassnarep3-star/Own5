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


def check(path: Path) -> int:
    """Verify a committed registration without rewriting it.

    A pre-registration is evidence, and evidence is read, not refreshed. This
    check answers three questions:

      1. does each strategy's rule text still hash to what was registered?
      2. does each watched file still hash to what was registered?
      3. is the registration commit an ancestor of every commit that has touched
         the watched files since?

    Question 3 is the one that matters. If the rules were edited after the
    evaluator moved, the registration proves nothing, and this exits non-zero.
    """
    if not path.exists():
        print(f"MISSING {path.relative_to(ROOT)}: run prereg.py and commit it")
        return 1
    reg = json.loads(path.read_text())
    failures: list[str] = []

    by_id = {x["id"]: x for x in reg["strategies"]}
    import strategies as S
    if len(S.PREREG) != len(by_id):
        failures.append(f"{len(S.PREREG)} strategies in code vs {len(by_id)} registered")
    for p_ in S.PREREG:
        got = hashlib.sha256(p_["rule"].encode()).hexdigest()
        want = by_id.get(p_["id"], {}).get("rule_sha256")
        if got != want:
            failures.append(f"{p_['id']} rule text changed after registration")
        # JSON turns a tuple threshold into a list, so compare canonical forms
        # rather than raw Python objects.
        registered_gates = by_id.get(p_["id"], {}).get("gates") or {}
        canon = lambda o: json.loads(json.dumps(o, sort_keys=True, default=list))
        if canon(registered_gates) != canon(S.GATES):
            failures.append(f"{p_['id']}: the gate register changed after registration")

    for f, want in reg["file_hashes"].items():
        full = ROOT / f
        if not full.exists():
            failures.append(f"{f} is registered but missing")
        elif hashlib.sha256(full.read_bytes()).hexdigest() != want:
            failures.append(f"{f} changed after registration")

    commit = reg["registration_commit"]
    if not git("cat-file", "-e", commit + "^{commit}") == "" and \
            subprocess.run(["git", "cat-file", "-e", commit + "^{commit}"],
                           cwd=ROOT, capture_output=True).returncode != 0:
        failures.append(f"registration commit {commit[:12]} is not in this clone")
    else:
        for f in reg["file_hashes"]:
            last = git("log", "-1", "--format=%H", "--", f)
            if not last:
                continue
            rc = subprocess.run(["git", "merge-base", "--is-ancestor", commit, last],
                                cwd=ROOT, capture_output=True).returncode
            if rc != 0:
                failures.append(f"{f} was touched by {last[:12]} AFTER registration "
                                f"{commit[:12]}")
            elif last != commit:
                print(f"  note: {f} last touched by {last[:12]}, after registration "
                      f"{commit[:12]} (ancestry holds)")

    print(f"registration {commit[:12]} {reg['registration_subject'][:56]}")
    print(f"  {len(by_id)} strategies, {len(reg['file_hashes'])} watched files")
    if failures:
        print(f"\n{len(failures)} PROBLEM(S):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("\nPRE-REGISTRATION INTACT")
    return 0


def main() -> int:
    if "--check" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--check") + 1]) if \
            len(sys.argv) > sys.argv.index("--check") + 1 else OUT
        return check(out)

    dirty = [f for f in WATCH if git("status", "--porcelain", "--", f)]
    if dirty and "--force" not in sys.argv:
        print("REFUSING TO WRITE: these files are uncommitted, so a pre-registration")
        print("made now cannot be shown to predate the data:")
        for f in dirty:
            print(f"  dirty  {f}")
        print("\nCommit them, then re-run. Use --force only if you intend to re-register.")
        return 1

    # The registration is the commit that INTRODUCED the rules, not whatever
    # HEAD happens to be. Using HEAD would make the file change on every later
    # commit, which is indistinguishable from drift.
    # `git log -- path` returns the TIP when history is shallow, because git has
    # no older commit to attribute the file to. Silently registering the tip is
    # the exact failure this file exists to prevent, so check for it.
    shallow = git("rev-parse", "--is-shallow-repository")
    if shallow == "true":
        print("REFUSING TO WRITE: this is a shallow clone, so git cannot tell which")
        print("commit introduced strategies.py. Run 'git fetch --unshallow' first.")
        return 1
    commit = git("log", "-1", "--format=%H", "--",
                 "tools/season_desk_941fe39f/strategies.py")
    if not commit:
        print("REFUSING TO WRITE: strategies.py has no commit, so there is nothing")
        print("to register against. Commit it first.")
        return 1
    subject = git("log", "-1", "--format=%s", commit)
    out = {
        "desk": "941fe39f",
        # derived from the registration commit, so the file is byte-stable
        "written_utc": git("log", "-1", "--format=%cI", commit),
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

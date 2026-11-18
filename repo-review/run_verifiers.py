"""Run every desk verifier (<dir>/verify.py) from the repository root and record the result.

Each verifier runs in a scratch copy of the working tree so that a verifier which writes
files cannot change the repository under review. Output: data/verifier_runs.csv.
Usage: python3 repo-review/run_verifiers.py
"""
from __future__ import annotations

import csv
import datetime as dt
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
GH_BLOB = "https://github.com/sassnarep3-star/Own5/blob/main/"
OUT = HERE / "data" / "verifier_runs.csv"
FIELDS = ["directory", "command", "exit_code", "result", "summary_line", "run_utc", "source_url", "workflow_files"]


def tree_snapshot(dest: Path) -> None:
    def ignore(_dir: str, names: list[str]) -> set[str]:
        return {n for n in names if n in {".git", "__pycache__", "node_modules"}}
    shutil.copytree(REPO, dest, ignore=ignore, dirs_exist_ok=True)


def workflows_for(directory: str) -> str:
    hits = []
    for wf in sorted((REPO / ".github" / "workflows").glob("*.yml")):
        text = wf.read_text(encoding="utf-8", errors="replace")
        if f"{directory}/" in text or f"{directory}\n" in text or f"{directory}'" in text:
            hits.append(wf.name)
    return ";".join(hits)


def pick_summary(output: str, failed: bool) -> str:
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    if not lines:
        return "(no output)"
    keys = ("FAIL", "Error", "error", "AssertionError", "failure")
    ok_keys = ("PASS", "OK", "passed", "verify:", "checks", "verified")
    if failed:
        for ln in reversed(lines):
            if any(k in ln for k in keys):
                return ln[:220]
        return lines[-1][:220]
    for ln in reversed(lines):
        if any(k in ln for k in ok_keys):
            return ln[:220]
    return lines[-1][:220]


def main() -> int:
    # repo-review/verify.py reads this table, so it is run separately (CI and the review README), not inside the sweep.
    verifiers = sorted(p.parent.name for p in REPO.glob("*/verify.py") if p.parent.name != "repo-review")
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "repo"
        tree_snapshot(scratch)
        for directory in verifiers:
            cmd = [sys.executable, f"{directory}/verify.py"]
            try:
                proc = subprocess.run(cmd, cwd=scratch, capture_output=True, text=True, timeout=600)
                code, output = proc.returncode, proc.stdout + "\n" + proc.stderr
            except subprocess.TimeoutExpired as exc:
                code, output = 124, f"timeout after {exc.timeout}s"
            failed = code != 0
            rows.append({
                "directory": directory,
                "command": " ".join(cmd),
                "exit_code": str(code),
                "result": "FAIL" if failed else "PASS",
                "summary_line": pick_summary(output, failed),
                "run_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source_url": GH_BLOB + f"{directory}/verify.py",
                "workflow_files": workflows_for(directory),
            })
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    passed = sum(r["result"] == "PASS" for r in rows)
    print(f"verifier_runs.csv: {len(rows)} verifiers, {passed} PASS, {len(rows) - passed} FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

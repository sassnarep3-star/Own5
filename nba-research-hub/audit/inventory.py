"""Hash every physical line of every tracked file at a pinned baseline commit.

This is content inventory, not independent factual verification. Code lines are
not NBA facts; selected NBA fields are compared separately in field_audit.csv.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
AUDIT = ROOT / "audit"
REPO_URL = "https://github.com/sassnarep3-star/Own5/blob/"
OFFICIAL_RE = re.compile(r"https://(?:www\.nba\.com|official\.nba\.com|ak-static\.cms\.nba\.com|www\.fanduel\.com|pubmed\.ncbi\.nlm\.nih\.gov|www\.itl\.nist\.gov|www\.davidhbailey\.com)/[^\s\"'<>,)\]]*")


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO)


def kind(path: str) -> str:
    p = path.lower()
    if p.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".ico", ".woff", ".woff2", ".ttf", ".br", ".gz", ".zip")):
        return "binary"
    if p.endswith(".csv"):
        return "csv-data"
    if p.endswith((".py", ".js", ".cjs", ".mjs", ".ts")):
        return "code"
    if p.endswith((".html", ".css")):
        return "markup-style"
    if p.endswith((".json", ".yml", ".yaml", ".toml")):
        return "config-data"
    if p.endswith(".md"):
        return "documentation"
    if "package-lock" in p:
        return "dependency-lock"
    return "other"


def main() -> dict:
    baseline = json.loads((AUDIT / "baseline.json").read_text(encoding="utf-8"))
    commit = baseline["commit"]
    paths = git("ls-tree", "-r", "--name-only", commit).decode("utf-8").splitlines()
    file_rows: list[dict] = []
    line_rows: list[dict] = []
    for path in sorted(paths):
        raw = git("show", f"{commit}:{path}")
        sha = hashlib.sha256(raw).hexdigest()
        k = kind(path)
        binary = k == "binary" or b"\x00" in raw
        review_url = f"{REPO_URL}{commit}/{path}"
        if binary:
            file_rows.append({
                "path": path, "sha256": sha, "bytes": len(raw), "line_count": 0,
                "binary": True, "kind": k, "review_url": review_url,
                "official_link_count": 0, "status": "INV", "note": "Binary content hashed; line audit not applicable.",
            })
            continue
        text = raw.decode("utf-8", errors="replace")
        lines = text.splitlines()
        official_count = 0
        for i, line in enumerate(lines, 1):
            urls = OFFICIAL_RE.findall(line)
            official_count += len(urls)
            evidence = urls[0] if urls else ""
            if k == "code":
                status = "INV"
                flag = "Code behavior is tested separately; not an NBA factual claim."
            elif k == "csv-data" and evidence:
                status = "LINK"
                flag = "Official/source link present; link presence is not source entailment."
            elif k == "csv-data":
                status = "INV"
                flag = "No official source link on this line; manual review."
            else:
                status = "INV"
                flag = "Inventory only; external factual review not applicable or pending."
            line_rows.append({
                "path": path, "line": i, "kind": k,
                "line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
                "status": status, "review_url": f"{review_url}#L{i}",
                "evidence_url": evidence, "flag": flag,
            })
        file_rows.append({
            "path": path, "sha256": sha, "bytes": len(raw), "line_count": len(lines),
            "binary": False, "kind": k, "review_url": review_url,
            "official_link_count": official_count,
            "status": "LINK" if official_count else "INV",
            "note": "Content inventory only; see field_audit.csv for selected direct NBA comparisons.",
        })
    with (AUDIT / "file_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(file_rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(file_rows)
    with (AUDIT / "line_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(line_rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(line_rows)
    summary = {
        "baseline_commit": commit, "files": len(file_rows), "physical_lines": len(line_rows),
        "binary_files": sum(1 for r in file_rows if r["binary"]),
        "lines_with_source_link": sum(1 for r in line_rows if r["evidence_url"]),
        "status_legend": {"INV": "inventory only / manual review", "LINK": "source link present, not independently verified"},
        "file_inventory_sha256": hashlib.sha256((AUDIT / "file_inventory.csv").read_bytes()).hexdigest(),
        "line_inventory_sha256": hashlib.sha256((AUDIT / "line_inventory.csv").read_bytes()).hexdigest(),
    }
    (AUDIT / "inventory_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


if __name__ == "__main__":
    main()

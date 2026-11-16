"""Builds the whole desk: data -> manifest -> HTML pages.

Deterministic by construction: the build timestamp is a pinned constant, not
the wall clock, so running this twice produces byte-identical output and the
workflow can prove the committed artefacts match a clean rebuild.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

import engine
import build_site as site_mod

ROOT = Path(__file__).resolve().parent
OFFICIAL = ROOT / "data" / "official"
DATA = ROOT / "data"

BUILD_UTC = engine.BUILD_UTC
SESSION = engine.SESSION


def git_head() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT),
                             capture_output=True, text=True, timeout=30)
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return ""


def write_manifest() -> list:
    rows = []
    for path in sorted(OFFICIAL.glob("*.json")):
        data = path.read_text(encoding="utf-8")
        captured = ""
        try:
            captured = json.loads(data).get("fetched_utc", "")
        except Exception:
            captured = ""
        rows.append({
            "path": f"data/official/{path.name}",
            "bytes": len(data.encode("utf-8")),
            "sha256": hashlib.sha256(data.encode("utf-8")).hexdigest(),
            "captured": captured,
        })
    # carried-forward inputs this desk reads but does not own
    for rel in ("../nfl-desk-3fb93d11/data/results_feed.csv",
                "../nfl-desk-3fb93d11/data/standings_official.csv",
                "../nfl-desk-864d5668/data/injuries.csv"):
        p = (DATA / rel).resolve()
        if not p.exists():
            continue
        blob = p.read_bytes()
        rows.append({
            "path": rel.replace("../", "(read-only) "),
            "bytes": len(blob),
            "sha256": hashlib.sha256(blob).hexdigest(),
            "captured": "carried forward from an earlier session",
        })
    with open(DATA / "manifest.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "bytes", "sha256", "captured"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return rows


def main() -> int:
    report = engine.build()
    manifest_rows = write_manifest()
    pages = site_mod.render({"build_utc": BUILD_UTC, "session": SESSION})
    report["pages"] = len(pages)
    report["manifest_entries"] = len(manifest_rows)
    # note: the git HEAD is deliberately NOT written into any artefact. Writing
    # it would make the committed output differ from a clean rebuild in CI,
    # which would break the deterministic-build check.
    head = git_head()
    with open(DATA / "build_report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
    print(f"session {SESSION} built at {BUILD_UTC}")
    print(f"  official finals      : {report['official_finals']}")
    print(f"  originated markets   : {report['originated_markets']}")
    print(f"  depth slots          : {report['depth_slots']}")
    print(f"  audit checks         : {report['audit_checks']}")
    print(f"  pages                : {len(pages)}")
    print(f"  manifest entries     : {len(manifest_rows)}")
    if head:
        print(f"  git HEAD             : {head[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

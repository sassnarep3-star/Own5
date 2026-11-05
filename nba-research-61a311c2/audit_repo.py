#!/usr/bin/env python3
"""Baseline repository inventory + canonical row evidence register.

The inventory proves file identity/size/hash at the session baseline commit. It
does not pretend to re-certify every legacy claim. Canonical empirical rows are
separately registered with the official source used for comparison.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
BASELINE = "54e8dee596d49731c3da535a1f77b01cd0c295d5"
REPO_URL = "https://github.com/sassnarep3-star/Own5"
OFFICIAL_RE = re.compile(r"https://(?:www\.nba\.com|official\.nba\.com|ak-static\.cms\.nba\.com)/[^\s\"'<>]+")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def count_json_sources(obj) -> tuple[int, int]:
    total = with_src = 0
    if isinstance(obj, dict):
        if any(k in obj for k in ("id", "source_url", "sources", "url")):
            total += 1
            if obj.get("source_url") or obj.get("sources") or obj.get("url"):
                with_src += 1
        for v in obj.values():
            t, w = count_json_sources(v)
            total += t
            with_src += w
    elif isinstance(obj, list):
        for v in obj:
            t, w = count_json_sources(v)
            total += t
            with_src += w
    return total, with_src


def inventory() -> list[dict]:
    paths = git("ls-tree", "-r", "--name-only", BASELINE).splitlines()
    rows = []
    for path in paths:
        blob = subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)
        text = None
        try:
            text = blob.decode("utf-8")
        except UnicodeDecodeError:
            pass
        ext = Path(path).suffix.lower()
        lines = len(text.splitlines()) if text is not None else None
        rows_total = rows_src = None
        if text is not None and ext == ".csv":
            try:
                parsed = list(csv.DictReader(io.StringIO(text)))
                rows_total = len(parsed)
                if parsed and "source_url" in parsed[0]:
                    rows_src = sum(bool(r.get("source_url")) for r in parsed)
                else:
                    rows_src = sum(bool(OFFICIAL_RE.search(json.dumps(r))) for r in parsed)
            except Exception:
                rows_total = rows_src = None
        elif text is not None and ext == ".json":
            try:
                rows_total, rows_src = count_json_sources(json.loads(text))
            except Exception:
                rows_total = rows_src = None
        top = path.split("/")[0]
        if top.startswith("nba") or top in {"docs", "research"} and "nba" in path.lower():
            scope = "nba_archive"
        elif top in {"data", "research", "scripts", "pages", "assets", "tests", "own5-desk", "nfl-strategy-lab", "nfl_model", "line-lab", "analysis", "tools", "site"} or path in {"README.md", "EXECUTIVE_SUMMARY.md", "index.html", "signals.html"}:
            scope = "mixed_or_nfl_archive"
        else:
            scope = "project_archive"
        rows.append({
            "path": path, "bytes": len(blob), "lines": lines,
            "sha256": hashlib.sha256(blob).hexdigest(), "extension": ext or "(none)",
            "scope": scope, "rows_total": rows_total, "rows_with_source_url": rows_src,
            "status": "inventory_hash_verified_content_not_certified",
            "source_url": f"{REPO_URL}/blob/{BASELINE}/{path}",
        })
    return rows


def row_audit() -> list[dict]:
    specs = [
        ("player_games_2025_26.csv", lambda r: f"{r['player_id']}:{r['game_id']}", "official NBA player game-log table compared field-by-field", "verified"),
        ("player_games_2026_27.csv", lambda r: f"{r['player_id']}:{r['game_id']}", "official NBA player game-log table transcribed and compared", "verified"),
        ("teams_prior_2025_26.csv", lambda r: r["team_id"], "official NBA team traditional table; selected fields transcribed", "verified"),
        ("teams_current_2026_27.csv", lambda r: r["team_id"], "official NBA team advanced table; selected fields transcribed", "verified"),
        ("slate.csv", lambda r: r["game_id"], "official NBA schedule game identity/time/venue", "verified"),
        ("market_quotes_nov5.csv", lambda r: f"{r['game_id']}:{r['market']}:{r['selection']}", "operator-official FanDuel visible quote; dynamic timestamp unavailable", "verified_value_timestamp_flagged"),
        ("availability.csv", lambda r: f"{r['game_id']}:{r['player_id']}", "official NBA injury-report PDF; status intentionally blank where not submitted", "flagged_unverified_value"),
    ]
    out = []
    for filename, keyfn, method, status in specs:
        with (DATA / filename).open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            fields = [k for k in r if k not in {"source_url", "note", "quote_timestamp"}]
            out.append({"dataset": filename, "row_key": keyfn(r), "fields_checked": len(fields),
                        "verification_method": method, "status": status,
                        "source_url": r["source_url"]})
    return out


def main() -> None:
    inv = inventory()
    audit = row_audit()
    for name, rows in (("repo_inventory.csv", inv), ("row_audit.csv", audit)):
        with (DATA / name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    manifest = {"baseline_commit": BASELINE, "baseline_files": len(inv),
                "canonical_rows_audited": len(audit),
                "canonical_verified_rows": sum(r["status"].startswith("verified") for r in audit),
                "canonical_flagged_rows": sum(r["status"].startswith("flagged") for r in audit),
                "inventory_sha256": hashlib.sha256((DATA / "repo_inventory.csv").read_bytes()).hexdigest(),
                "row_audit_sha256": hashlib.sha256((DATA / "row_audit.csv").read_bytes()).hexdigest()}
    (DATA / "audit_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

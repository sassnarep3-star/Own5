"""Verification harness for the NBA Line Commission site (session arena-a46d621e).

Fails loudly on any of:
  1. a CSV row without an official (nba.com) source link;
  2. an outputs.json row without a source/reference link;
  3. a broken internal link in any page of this site (and, optionally, the whole repo);
  4. a page that leaks Python junk (None/NaN/objects) into the HTML;
  5. a table row with no link at all (every table must be source-linked);
  6. non-determinism: rerunning compute.py must reproduce outputs.json byte for byte;
  7. the research documents disappearing.

Run: python3 nba-commission/verify.py
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DATA = ROOT / "data"

OFFICIAL = ("https://www.nba.com/", "https://nba.com/")
METHOD = ("https://www.ams.org/", "https://www.davidhbailey.com/", "https://arxiv.org/",
          "https://www.statsmodels.org/")
ALLOWED = OFFICIAL + METHOD

failures: list[str] = []
notes: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def ok(msg: str) -> None:
    notes.append(msg)


def is_allowed(url: str) -> bool:
    return any(url.startswith(p) for p in ALLOWED)


def check_csvs() -> None:
    total = 0
    for path in sorted(DATA.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            fail(f"{path.name}: empty file")
            continue
        if "source_url" not in rows[0]:
            fail(f"{path.name}: no source_url column")
            continue
        for i, row in enumerate(rows, start=2):
            total += 1
            url = (row.get("source_url") or "").strip()
            if not url:
                fail(f"{path.name}:{i}: missing source_url")
            elif not is_allowed(url):
                fail(f"{path.name}:{i}: non-official source {url}")
    ok(f"CSV provenance: {total} data rows, every row carries an allowed official/method URL")


def walk_rows(obj, path="$"):
    """Yield (path, dict) for every dict inside outputs.json."""
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from walk_rows(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_rows(v, f"{path}[{i}]")


def check_outputs() -> None:
    out = json.loads((DATA / "outputs.json").read_text(encoding="utf-8"))
    required_sections = ["meta", "checks", "team_ratings", "lines", "team_correlations",
                         "player_pairs", "prop_combos", "props", "luck", "gates",
                         "strategies", "leaderboard", "flags", "sources"]
    for s in required_sections:
        if s not in out:
            fail(f"outputs.json missing section {s}")
    keyed = [("lines", "source_url"), ("props", "source_url"), ("team_correlations", "source_url"),
             ("player_pairs", "source_url"), ("prop_combos", "source_url"), ("gates", "source_url"),
             ("flags", "source_url"), ("sources", "url")]
    for section, field in keyed:
        for i, row in enumerate(out.get(section, [])):
            url = (row.get(field) or "").strip()
            if not url or not is_allowed(url):
                fail(f"outputs.json {section}[{i}] bad {field}: {url!r}")
    # team ratings and strategies must carry provenance too
    for i, row in enumerate(out["team_ratings"]):
        if not is_allowed(row.get("source_url_current", "")):
            fail(f"outputs.json team_ratings[{i}] missing official source")
    for i, row in enumerate(out["strategies"]):
        if "rule" not in row or not row["rule"]:
            fail(f"outputs.json strategies[{i}] has no pre-registered rule")
        if row.get("certified"):
            fail(f"outputs.json strategies[{i}] is certified without a graded bet")
    # no blank/None confusion in numeric headline fields
    for l in out["lines"]:
        if l.get("market_spread") or l.get("market_total"):
            fail("market columns must stay blank (no odds source)")
        if not isinstance(l["own_spread_home"], (int, float)):
            fail(f"line {l['game_id']} has no numeric own spread")
    for p in out["props"]:
        if p.get("market_line"):
            fail(f"prop {p['player']} {p['stat']} must not carry an unverified market line")
    if out["meta"]["strategies_certified"] != sum(1 for s in out["strategies"] if s.get("certified")):
        fail("meta.strategies_certified disagrees with the strategy table")
    ok(f"outputs.json provenance: {sum(len(out.get(s, [])) for s, _ in keyed)} keyed rows linked")


def check_pages() -> None:
    pages = sorted(ROOT.glob("*.html"))
    if len(pages) < 14:
        fail(f"expected 14 pages, found {len(pages)}")
    # structural leak patterns only: prose may legitimately contain the words
    junk = re.compile(r"(>\s*None\s*<|>\s*nan\s*<|>\s*NaN\s*<|>\s*inf\s*<|&lt;object at 0x|"
                      r"Traceback \(most recent call last\)|\[\{|\{\')")
    for p in pages:
        text = p.read_text(encoding="utf-8")
        for m in junk.finditer(text):
            # "None" appears legitimately inside prose words? keep the check strict but targeted
            snippet = text[max(0, m.start() - 40):m.start() + 40].replace("\n", " ")
            fail(f"{p.name}: suspicious token {m.group(0)!r} near: {snippet}")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            target = (p.parent / href.split("#")[0].split("?")[0])
            if not target.exists():
                fail(f"{p.name}: broken internal link {href}")
        # every page except the pure-prose ones must contain at least one table
        if p.name not in {"executive-summary.html", "audit.html"} and "<table" not in text:
            fail(f"{p.name}: no table found")
        # every table row must contain a link or an explicit BLANK marker
        for tbl in re.findall(r"<table.*?</table>", text, re.S):
            rows = re.findall(r"<tr>(.*?)</tr>", tbl, re.S)
            for row in rows[1:]:
                if "<td" not in row:
                    continue
                if "<a " not in row and "blank" not in row and "—" not in row:
                    fail(f"{p.name}: table row without a source link or BLANK marker: "
                         f"{html.unescape(re.sub('<[^>]+>', ' ', row))[:90]!r}")
    ok(f"pages: {len(pages)} HTML files, internal links resolve, tables source-linked")


def check_repo_links() -> None:
    broken = []
    for path in REPO.rglob("*.html"):
        if ".git" in path.parts or "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http://", "https://", "mailto:", "#", "data:", "javascript:", "tel:")):
                continue
            target = (path.parent / href.split("#")[0].split("?")[0]).resolve()
            if not target.exists():
                broken.append((str(path.relative_to(REPO)), href))
    for b in broken:
        fail(f"repo link broken: {b[0]} -> {b[1]}")
    ok(f"repo-wide link scan: {len(list(REPO.rglob('*.html')))} pages, {len(broken)} broken")


def check_determinism() -> None:
    before = hashlib.sha256((DATA / "outputs.json").read_bytes()).hexdigest()
    res = subprocess.run([sys.executable, str(ROOT / "compute.py")],
                         capture_output=True, text=True, cwd=str(REPO))
    if res.returncode != 0:
        fail(f"compute.py failed: {res.stderr[-400:]}")
        return
    after = hashlib.sha256((DATA / "outputs.json").read_bytes()).hexdigest()
    if before != after:
        fail("compute.py is not deterministic: outputs.json changed on re-run")
    else:
        ok("determinism: compute.py reproduces outputs.json byte for byte")
    if "0 failed" not in res.stdout:
        fail(f"compute.py reported failing checks: {res.stdout.strip()[-300:]}")


def check_research() -> None:
    for name in ("EXECUTIVE_SUMMARY.md", "methodology.md", "data-notes.md", "repo-audit.md"):
        p = REPO / "research" / "nba-commission" / name
        if not p.exists() or p.stat().st_size < 500:
            fail(f"research document missing or too short: {name}")
    ok("research documents present (executive summary, methodology, data notes, repo audit)")


def main() -> int:
    check_csvs()
    check_outputs()
    check_pages()
    check_repo_links()
    check_research()
    check_determinism()
    for n in notes:
        print("  ok:", n)
    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for f in failures:
            print("  -", f)
        return 1
    print(f"\nALL CHECKS PASSED ({len(notes)} groups, 0 failures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

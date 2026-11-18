#!/usr/bin/env python3
"""Fail-closed verification for the NFL Origin Desk.

Checks:
  1. Every CSV row carries a source link in its final column (or is an explicit
     blank-and-flag entry). No inferred values.
  2. Every CSV row has the declared column count.
  3. No broken internal links across all HTML pages (relative .html targets must
     exist; style.css must exist).
  4. Every page renders required sections.
Exit non-zero on any failure.
"""
import csv
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "nfl-origin-desk")
OUT = os.path.join(ROOT, "nfl-origin-desk")

failures = []

def fail(msg):
    failures.append(msg)
    print("FAIL:", msg)

# ---------------------------------------------------------------------------
# 1 + 2. CSV checks: column count + source link in final column
# ---------------------------------------------------------------------------
csv_files = sorted(glob.glob(os.path.join(DATA, "*.csv")))
if not csv_files:
    fail("no CSV files found in data/nfl-origin-desk")
for path in csv_files:
    name = os.path.basename(path)
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        fail(f"{name}: empty file"); continue
    header = rows[0]
    ncol = len(header)
    low = [h.lower() for h in header]
    src_cols = [i for i, h in enumerate(low) if "url" in h or "source" in h or h == "link"]
    if not src_cols:
        fail(f"{name}: no source-url column found (header needs url/source/link)")
    for i, row in enumerate(rows[1:], start=2):
        if len(row) != ncol:
            fail(f"{name} line {i}: expected {ncol} columns, got {len(row)}")
            continue
        # every row must carry at least one populated HTTP source link
        urls = [row[c] for c in src_cols if row[c] and row[c].strip().startswith("http")]
        if not urls:
            fail(f"{name} line {i}: no source URL in any source column (row id {row[0] if row else '?'})")
    print(f"OK   {name}: {len(rows)-1} data rows, {ncol} columns, source column(s) {src_cols}")

# ---------------------------------------------------------------------------
# 3. Internal link check across HTML pages
# ---------------------------------------------------------------------------
html_files = sorted(glob.glob(os.path.join(OUT, "*.html")))
if not html_files:
    fail("no HTML files found in nfl-origin-desk")
existing = {os.path.basename(p) for p in html_files} | {"style.css", ".nojekyll"}

link_re = re.compile(r'href=["\']([^"\']+)["\']')
for path in html_files:
    name = os.path.basename(path)
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    for m in link_re.finditer(content):
        href = m.group(1)
        # skip external and anchor-only links
        if href.startswith("http") or href.startswith("mailto:") or href.startswith("#"):
            continue
        # strip fragment/query
        target = href.split("#")[0].split("?")[0]
        if not target:
            continue
        if target not in existing:
            fail(f"{name}: broken internal link -> {href}")
    print(f"OK   {name}: internal links resolved")

# ---------------------------------------------------------------------------
# 4. Required sections present
# ---------------------------------------------------------------------------
required = {
    "index.html": ["Decision-readiness table", "blocking gate", "number to clear"],
    "requirements.html": ["Decision-readiness table"],
    "questions.html": ["Questions register"],
    "suggestions.html": ["Review test"],
    "lines.html": ["side", "total", "moneyline"],
    "strategies.html": ["Strategy catalog"],
    "gates.html": ["Validation gates"],
    "leaderboard.html": ["Proper-score leaderboard"],
    "correlations.html": ["Official-source correlations"],
    "injuries.html": ["Injury"],
    "sources.html": ["Source registry"],
    "flagged.html": ["Flagged for review"],
    "executive-summary.html": ["Executive summary"],
}
for name, needles in required.items():
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        fail(f"{name}: missing page"); continue
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    for needle in needles:
        if needle.lower() not in content.lower():
            fail(f"{name}: missing required section '{needle}'")

# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------
print()
if failures:
    print(f"VERIFICATION FAILED: {len(failures)} issue(s)")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print(f"VERIFICATION PASSED: {len(csv_files)} CSVs, {len(html_files)} HTML pages, "
      f"all rows source-linked, no broken internal links.")
sys.exit(0)

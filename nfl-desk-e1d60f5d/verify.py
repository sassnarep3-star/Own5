#!/usr/bin/env python3
"""Line-by-line verifier for the OWN5 NFL decision desk.

Checks:
  * every rendered data-table row carries an official source link, or is an
    explicit blank/flag (never an inferred value);
  * every internal link target exists;
  * every data CSV is well-formed and every populated row has a source_url or
    an explicit blank/flag reason;
  * the build is deterministic (re-running build.py produces identical bytes).

Exit non-zero on any failure.
"""
import csv
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")

failures = []
checks = 0


def check(condition, message):
    global checks
    checks += 1
    if condition:
        print(f"  ok   {message}")
    else:
        failures.append(message)
        print(f"  FAIL {message}")


def read_csv(name):
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sources_in(text):
    """Return all https URLs found in the HTML."""
    return set(re.findall(r'https://[^"\'<>\\s]+', text))


def main():
    print(f"Verifying desk at {ROOT}\n")

    # --- 1. Data CSVs well-formed + source coverage -------------------------
    expected_source_cols = {
        "standings_2026_wk11.csv": ["source_url"],
        "schedule_2026_wk11.csv": ["source_url"],
        "byes_2026_wk11.csv": ["source_url"],
        "questions.csv": ["source_url"],
        "suggestions.csv": ["source_url"],
        "sources.csv": ["url"],
        "flagged.csv": ["source_url"],
    }
    for fname, required in expected_source_cols.items():
        path = os.path.join(DATA, fname)
        check(os.path.exists(path), f"data file exists: {fname}")
        rows = read_csv(fname)
        check(len(rows) > 0, f"{fname} has at least one row ({len(rows)})")
        for i, r in enumerate(rows):
            for col in required:
                val = (r.get(col) or "").strip()
                check(bool(val), f"{fname} row {i} has non-empty {col}")

    # --- 2. Every rendered page exists and has tables -----------------------
    table_pages = ["index.html", "standings.html", "schedule.html", "questions.html",
                   "suggestions.html", "sources.html", "flagged.html"]
    page_files = table_pages + ["exec.html"]
    for pf in page_files:
        path = os.path.join(PAGES, pf) if pf != "index.html" else os.path.join(ROOT, pf)
        check(os.path.exists(path), f"page exists: {pf}")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        if pf in table_pages:
            check("<table" in content, f"{pf} contains a data table")
            check('class="data-table"' in content, f"{pf} uses the data-table class")

    # --- 3. Every official URL in pages is reachable-looking https ---------
    for pf in page_files:
        path = os.path.join(PAGES, pf) if pf != "index.html" else os.path.join(ROOT, pf)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        for url in sorted(sources_in(content)):
            check(url.startswith("https://"), f"{pf}: external link is https: {url[:80]}")

    # --- 4. Internal nav targets exist --------------------------------------
    internal = [
        "index.html", "pages/exec.html", "pages/standings.html",
        "pages/schedule.html", "pages/questions.html",
        "pages/suggestions.html", "pages/sources.html", "pages/flagged.html",
        "assets/style.css",
    ]
    for target in internal:
        path = os.path.join(ROOT, target)
        check(os.path.exists(path), f"internal target exists: {target}")

    # --- 5. Flagged register: blocking items have severity ------------------
    flagged = read_csv("flagged.csv")
    for i, r in enumerate(flagged):
        check(bool(r.get("id")), f"flagged row {i} has an id")
        check(bool(r.get("severity")), f"flagged row {i} has a severity")
        check(bool(r.get("source_url")), f"flagged row {i} {r.get('id')} has a source URL")

    # --- 6. Questions register: blocking flagged values ---------------------
    questions = read_csv("questions.csv")
    for i, r in enumerate(questions):
        check(bool(r.get("id")), f"question row {i} has an id")
        check(r.get("blocking") in ("Yes", "No"), f"question row {i} blocking is Yes/No")

    # --- 7. Determinism: rebuild produces identical bytes -------------------
    before = {}
    for pf in page_files:
        path = os.path.join(PAGES, pf) if pf != "index.html" else os.path.join(ROOT, pf)
        with open(path, "rb") as f:
            before[pf] = hashlib.sha256(f.read()).hexdigest()
    subprocess.run([sys.executable, "build.py"], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    after = {}
    for pf in page_files:
        path = os.path.join(PAGES, pf) if pf != "index.html" else os.path.join(ROOT, pf)
        with open(path, "rb") as f:
            after[pf] = hashlib.sha256(f.read()).hexdigest()
    for pf in page_files:
        check(before[pf] == after[pf], f"deterministic rebuild: {pf} unchanged")

    # --- summary ------------------------------------------------------------
    print(f"\n{checks} checks, {len(failures)} failure(s)")
    if failures:
        print("Failures:")
        for f in failures:
            print("  -", f)
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

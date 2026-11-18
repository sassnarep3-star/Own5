#!/usr/bin/env python3
"""Snapshot the NFL desk directories in this checkout into data/desks_index.csv.

Counting rule (stated on the published page):
  a top-level directory whose name starts with "nfl-" or "nfl_", or whose name is "own5-desk".

The output is a PINNED SNAPSHOT. Other sessions add desks over time, so the build never re-scans the
tree. Run this script only when a new snapshot is deliberately taken, then commit the CSV with a new
SNAPSHOT_UTC value. verify.py checks that every pinned directory still exists and reports (does not fail
on) directories added since the snapshot.
"""
import csv
import html
import os
import re
import sys

SNAPSHOT_UTC = "2026-11-18T03:14:00Z"
LIVE_BASE = "https://sassnarep3-star.github.io/Own5/"
DESK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO_ROOT = os.path.abspath(os.path.join(DESK_DIR, ".."))
OUT = os.path.join(DESK_DIR, "data", "desks_index.csv")
COLUMNS = [
    "desk_dir", "has_index_html", "html_pages", "data_files", "title",
    "scoped_workflow", "live_url", "source_class", "snapshot_read_utc",
]


SELF_DIR = "nfl-desk-3cb7800c"


def is_desk_name(name: str) -> bool:
    if name == SELF_DIR:
        return False  # this desk is not a sibling of itself
    return name.startswith("nfl-") or name.startswith("nfl_") or name == "own5-desk"


def page_title(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read(20000)
    except OSError:
        return ""
    m = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
    if not m:
        return ""
    title = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    return title[:120]


def snapshot_rows():
    rows = []
    for name in sorted(os.listdir(REPO_ROOT)):
        full = os.path.join(REPO_ROOT, name)
        if not os.path.isdir(full) or not is_desk_name(name):
            continue
        html_pages = 0
        data_files = 0
        for dirpath, dirnames, filenames in os.walk(full):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            for fn in filenames:
                if fn.endswith(".html"):
                    html_pages += 1
                if "/data/" in os.path.join(dirpath, fn).replace(os.sep, "/") or dirpath.endswith("/data"):
                    data_files += 1
        index_path = os.path.join(full, "index.html")
        has_index = os.path.isfile(index_path)
        title = page_title(index_path) if has_index else ""
        workflow = os.path.isfile(os.path.join(REPO_ROOT, ".github", "workflows", name + ".yml"))
        rows.append({
            "desk_dir": name,
            "has_index_html": "yes" if has_index else "no",
            "html_pages": str(html_pages),
            "data_files": str(data_files),
            "title": title,
            "scoped_workflow": "yes" if workflow else "no",
            "live_url": LIVE_BASE + name + "/" if has_index else "",
            "source_class": "INTERNAL (repo directory listing; not a league source)",
            "snapshot_read_utc": SNAPSHOT_UTC,
        })
    return rows


def main(argv):
    rows = snapshot_rows()
    if "--write" not in argv:
        for r in rows:
            print(r["desk_dir"], r["has_index_html"], r["html_pages"], r["data_files"])
        print("directories:", len(rows), "(dry run; pass --write to update the pinned snapshot)")
        return 0
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print("wrote", OUT, len(rows), "rows")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

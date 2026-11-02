#!/usr/bin/env python3
"""Line-by-line verification of the Own5 site data + generated HTML.

Checks:
1. Every CSV row in data/*.csv has a non-empty official source link
   (http/https) in a source-ish column (source_url / url / official_site),
   OR the row is explicitly a flagged/blank row (flagged.csv, leaderboard
   metric blanks) — blanks must be intentional, never filled by inference.
2. All URLs in CSVs are http(s) and well-formed.
3. Generated HTML pages exist, and every internal href/src resolves to a
   file in the repo; every external link is http(s).
4. No HTML page contains the literal placeholder {{TABLE:...}}.
5. Standings CSV internal consistency (NET = PF-PA etc.) — re-asserted.

Exit code 0 = all checks pass (flagged items are reported, not failures).
"""
import csv, os, re, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
fails, warns = [], []

SOURCE_COLS = {"source_url", "url", "official_site", "nfl_profile", "input_source_url"}
ALLOW_NO_SOURCE = {"flagged.csv", "leaderboard.csv"}  # rows here are claims-about-absence or pending blanks

def is_url(s):
    return bool(re.fullmatch(r"https?://[^\s\"'<>]+", s.strip()))

for fn in sorted(os.listdir(DATA)):
    if not fn.endswith(".csv"):
        continue
    rows = list(csv.DictReader(open(os.path.join(DATA, fn), encoding="utf-8")))
    for i, r in enumerate(rows, 2):  # +1 header
        srcs = [v for c, v in r.items() if c and c.lower() in SOURCE_COLS and v and v.strip()]
        urls = [s for s in srcs if ";" not in s]
        for s in srcs:
            for part in re.split(r"\s*;\s*", s):
                part = part.strip()
                if part and not is_url(part):
                    fails.append(f"{fn}:{i} bad URL {part!r}")
        status = " ".join(str(v) for c, v in r.items() if c and c.lower() in ("status","verification_status","row_status","allowed")).lower()
        if fn in ALLOW_NO_SOURCE or "flagged" in status or "excluded" in status:
            if not urls:
                warns.append(f"{fn}:{i} row has no source link — intentional blank/flag (status: {status[:60]!r}); published on flagged.html")
        else:
            if not urls:
                fails.append(f"{fn}:{i} MISSING source link — row must have an official source_url or be flagged")

# standings consistency
rows = list(csv.DictReader(open(os.path.join(DATA, "standings-2026-wk8.csv"), encoding="utf-8")))
for r in rows:
    if int(r["NET"]) != int(r["PF"]) - int(r["PA"]):
        fails.append(f"standings: NET != PF-PA for {r['team']}")
    if abs(float(r["PCT"]) - (int(r["W"]) + 0.5 * int(r["T"])) / int(r["GP"])) > 0.001:
        fails.append(f"standings: PCT mismatch for {r['team']}")
if sum(int(r["W"]) for r in rows) != sum(int(r["L"]) for r in rows):
    fails.append("standings: total W != total L")

# HTML checks
pages = [f for f in os.listdir(ROOT) if f.endswith(".html")]
for p in sorted(pages):
    content = open(os.path.join(ROOT, p), encoding="utf-8").read()
    if "{{TABLE:" in content or "<!-- TABLE:" in content:
        fails.append(f"{p}: unresolved TABLE placeholder")
    for m in re.finditer(r'(?:href|src)="([^"]+)"', content):
        u = m.group(1)
        if u.startswith(("http://", "https://", "data:", "mailto:")) or u.startswith("#"):
            continue
        target = os.path.normpath(os.path.join(ROOT, u.split("#")[0]))
        if not os.path.exists(target):
            fails.append(f"{p}: broken internal link {u}")

# external URL sanity in html
for p in sorted(pages):
    content = open(os.path.join(ROOT, p), encoding="utf-8").read()
    for m in re.finditer(r'href="(https?://[^"]+)"', content):
        if not is_url(m.group(1)):
            fails.append(f"{p}: bad external URL {m.group(1)}")

print(f"pages checked: {len(pages)}")
print(f"WARNINGS ({len(warns)}):")
for w in warns:
    print("  -", w)
print(f"FAILURES ({len(fails)}):")
for f_ in fails:
    print("  -", f_)
if fails:
    sys.exit(1)
print("ALL CHECKS PASSED (flagged/blank rows are intentional and listed in data/flagged.csv)")

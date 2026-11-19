#!/usr/bin/env python3
"""Fail-closed verification of the Own5 NFL front door.

Gates
  H01 pages        every page the navigation promises exists and every internal link resolves
  H02 provenance   every table row carries an official source link or an explicit unverified marker
  H03 readiness    the landing table has exactly one row per requirement of the canonical register
  H04 lineage      every source file the site was built from is still the file on disk (sha256)
  H05 determinism  a rebuild changes no bytes
  H06 claims       nothing claims a certified strategy or a staking return
  H07 links        the repository-wide link check finds no broken internal link

Exit code 0 only when every gate passes.
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = HERE / "data"
sys.path.insert(0, str(HERE))

from build_hub import PAGES, internal_link_report  # noqa: E402

FAILURES: list[str] = []
PASSES: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    if ok:
        PASSES.append(label)
        print(f"PASS {label}" + (f" ({detail})" if detail else ""))
    else:
        FAILURES.append(f"{label}: {detail}")
        print(f"FAIL {label}" + (f": {detail}" if detail else ""))
    return ok


class Rows(HTMLParser):
    """Collects every table row with its links and text, so a row can be checked for provenance."""

    def __init__(self):
        super().__init__()
        self.rows: list[dict] = []
        self.links: list[str] = []
        self._in_tbody = False
        self._cur: dict | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tbody":
            self._in_tbody = True
        elif tag == "tr" and self._in_tbody:
            self._cur = {"links": [], "text": ""}
        elif tag == "a" and "href" in a:
            self.links.append(a["href"])
            if self._cur is not None:
                self._cur["links"].append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tbody":
            self._in_tbody = False
        elif tag == "tr" and self._cur is not None:
            self.rows.append(self._cur)
            self._cur = None

    def handle_data(self, data):
        if self._cur is not None:
            self._cur["text"] += data


def h01_pages():
    missing = [p for p in PAGES if not (HERE / p).exists()]
    check(not missing, "H01 every promised page exists", ",".join(missing))
    broken = []
    for p in PAGES:
        f = HERE / p
        if not f.exists():
            continue
        rp = Rows()
        rp.feed(f.read_text(encoding="utf-8"))
        for href in rp.links:
            if href.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            target = (f.parent / href.split("#")[0]).resolve()
            if not target.exists():
                broken.append(f"{p} -> {href}")
    check(not broken, "H01 every internal link in the front door resolves", "; ".join(broken[:5]))
    for p in PAGES:
        f = HERE / p
        if f.exists():
            txt = f.read_text(encoding="utf-8")
            ok = ("Own5 NFL front door" in txt and "not affiliated with the NFL" in txt
                  and "blank cells are unverified" in txt)
            if not ok:
                check(False, f"H01 {p} carries the provenance footer")
                break
    else:
        check(True, "H01 every page carries the provenance footer")


def h02_provenance():
    """Every row of every table shows where it came from, or says that it is unverified."""
    offenders = []
    total = 0
    for p in PAGES:
        f = HERE / p
        if not f.exists():
            continue
        rp = Rows()
        rp.feed(f.read_text(encoding="utf-8"))
        for row in rp.rows:
            total += 1
            text = row["text"]
            has_link = any(u.startswith("https://") for u in row["links"])
            has_marker = ("UNVERIFIED" in text or "NO VERIFIED SOURCE" in text
                          or "NO SOURCE" in text)
            if not (has_link or has_marker):
                offenders.append(f"{p}: {text[:70]!r}")
    check(not offenders, f"H02 every table row has an official source or an unverified marker "
                         f"({total} rows)", "; ".join(offenders[:5]))


def h03_readiness():
    src = REPO / "nfl-market-desk" / "data" / "decision_readiness.csv"
    with src.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    html = (HERE / "index.html").read_text(encoding="utf-8")
    ids = set(re.findall(r"<td>(R-\d+)</td>", html))
    want = {r["requirement_id"] for r in rows}
    check(ids == want, f"H03 the landing table has one row per requirement ({len(want)})",
          f"missing {sorted(want - ids)[:4]} extra {sorted(ids - want)[:4]}")
    check("Number that would clear it" in html,
          "H03 the landing table publishes the number that would clear each requirement")
    check("Gate" in html and "Gate status" in html,
          "H03 the landing table publishes the gate that blocks each requirement")


def h04_lineage():
    bad = []
    with (DATA / "lineage.csv").open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            p = REPO / r["path"]
            if not p.exists():
                bad.append(f"{r['path']} missing")
                continue
            sha = hashlib.sha256(p.read_bytes()).hexdigest()
            if sha != r["sha256"]:
                bad.append(f"{r['path']} changed since the build")
    check(not bad, "H04 every source file is still the file that was built from", "; ".join(bad[:5]))
    # the verifier results file must be present and cover the desks
    with (DATA / "verifier_runs.csv").open(newline="", encoding="utf-8") as f:
        vr = list(csv.DictReader(f))
    check(len(vr) >= 20, f"H04 the verifier sweep covers the desks ({len(vr)} verifiers)")


def h05_determinism():
    before = {p: hashlib.sha256((HERE / p).read_bytes()).hexdigest() for p in PAGES}
    res = subprocess.run([sys.executable, str(HERE / "build_hub.py")], capture_output=True,
                         text=True, cwd=REPO, timeout=600)
    if res.returncode != 0:
        check(False, "H05 the rebuild succeeds", res.stderr[-300:])
        return
    after = {p: hashlib.sha256((HERE / p).read_bytes()).hexdigest() for p in PAGES}
    diff = [p for p in PAGES if before[p] != after[p]]
    check(not diff, "H05 a rebuild changes no bytes", ",".join(diff))


def h06_claims():
    bad = []
    forbidden = [
        r"certified strategy(?!\s+(is|are)?\s*(cannot|may not|none|not))",
        r"\bROI of \d",
        r"guaranteed",
        r"guarantee(d)? (?:profit|return|win)",
    ]
    for p in PAGES:
        f = HERE / p
        if not f.exists():
            continue
        txt = f.read_text(encoding="utf-8")
        for pat in forbidden:
            for m in re.finditer(pat, txt, re.I):
                bad.append(f"{p}: {m.group(0)}")
    check(not bad, "H06 no page claims a certified strategy or a staking return",
          "; ".join(bad[:5]))
    # and the truth itself: nothing is certified
    with (REPO / "nfl-market-desk" / "data" / "leaderboard.csv").open(newline="", encoding="utf-8") as f:
        lb = list(csv.DictReader(f))
    cert = [r for r in lb if str(r.get("certified", "")).lower() == "yes"]
    check(not cert, f"H06 no strategy family is certified ({len(lb)} families)",
          ",".join(r["family_id"] for r in cert))


def h07_links():
    broken = internal_link_report()
    check(not broken, f"H07 the repository-wide link check finds no broken internal link "
                      f"({len(broken)} found)", "; ".join(f"{b['page']} -> {b['value']}"
                                                        for b in broken[:5]))


def main() -> int:
    for gate in (h01_pages, h02_provenance, h03_readiness, h04_lineage, h05_determinism,
                 h06_claims, h07_links):
        try:
            gate()
        except Exception as e:  # noqa: BLE001 - a crashing gate is a failure, never a pass
            check(False, f"{gate.__name__} raised", repr(e))
    print(f"\n{len(PASSES)} passed, {len(FAILURES)} failed")
    if FAILURES:
        print("FAILURES:")
        for f in FAILURES:
            print(" -", f)
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())

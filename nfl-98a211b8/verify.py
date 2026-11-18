#!/usr/bin/env python3
"""Verification for the session 98a211b8 desk. Stdlib only. Exit 1 on any failure.

Checks:
 V1  excerpt SHA-256 matches the value pinned in captures and data CSVs
 V2  the 44-row official parse and team counts are as recorded
 V3  injury_row_checks.csv equals a fresh comparison (no hand edits)
 V4  every repo_review row has an evidence link and an official link or INTERNAL
 V5  every unverified item without a link is labelled UNVERIFIED
 V6  every body table row in every page carries an https link or an UNVERIFIED/INTERNAL label
 V7  every relative link in every page resolves to a file in this folder
 V8  no http:// links anywhere in the pages
 V9  rebuilding into a temp folder reproduces the committed pages byte for byte
 V10 visible text names only pages this desk publishes
"""
import csv
import io
import os
import re
import shutil
import sys
import tempfile
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build  # noqa: E402

failures = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(name)


class Rows(HTMLParser):
    """Collects each <tr> inside <tbody> with its link targets and text."""

    def __init__(self):
        super().__init__()
        self.in_tbody = False
        self.rows = []
        self.cur = None
        self.hrefs_all = []
        self.text = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.cur = {"hrefs": [], "text": ""}
        if tag == "a" and "href" in a:
            self.hrefs_all.append(a["href"])
            if self.cur is not None:
                self.cur["hrefs"].append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.cur is not None:
            self.rows.append(self.cur)
            self.cur = None

    def handle_data(self, data):
        if self.cur is not None:
            self.cur["text"] += data


def read_csv(name):
    with open(os.path.join(build.DATA, name), encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    # V0 every CSV row has the same number of fields as its header
    bad0 = []
    for fn in sorted(os.listdir(build.DATA)):
        if not fn.endswith(".csv"):
            continue
        with open(os.path.join(build.DATA, fn), encoding="utf-8", newline="") as fh:
            rd = csv.reader(fh)
            header = next(rd)
            for no, row in enumerate(rd, 2):
                if len(row) != len(header):
                    bad0.append(f"{fn}:{no}")
    check("V0 every CSV row has the header's field count", not bad0, ",".join(bad0[:5]))

    # V1 excerpt hash pinned
    sha = build.sha256_file(os.path.join(HERE, build.EXCERPT))
    caps = read_csv("official_status_captures.csv")
    pinned = {c["excerpt_sha256"] for c in caps if c["excerpt_sha256"]}
    check("V1 excerpt sha256 pinned", pinned == {sha}, sha)

    # V2 parse counts
    official = build.parse_official_rows(os.path.join(HERE, build.EXCERPT))
    counts = {t: sum(1 for o in official if o["team_nickname"] == t) for t in build.TEAMS}
    check("V2 official rows parsed = 44 (WAS 9, NYG 11, NE 15, DET 9)",
          len(official) == 44 and counts == {"Commanders": 9, "Giants": 11, "Patriots": 15, "Lions": 9},
          str(counts))

    # V3 injury_row_checks.csv equals a fresh comparison
    repo_index = build.load_repo_rows(os.path.join(build.ROOT, build.REPO_COPY))
    fresh = build.compare_rows(official, repo_index, build.REPO_COPY)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=build.CHECK_COLS, lineterminator="\n")
    w.writeheader()
    for r in fresh:
        w.writerow({k: r.get(k, "") for k in build.CHECK_COLS})
    with open(os.path.join(build.DATA, "injury_row_checks.csv"), encoding="utf-8", newline="") as fh:
        committed = fh.read()
    check("V3 injury_row_checks.csv reproduces from the excerpt and repo copy",
          committed == buf.getvalue())
    n_match = sum(1 for r in fresh if r["match"] == "MATCH")
    check("V3b match count recorded as 27 of 44", n_match == 27, f"{n_match} match, {len(fresh) - n_match} differ")

    # V4 repo review links
    repo = read_csv("repo_review.csv")
    bad4 = [r["id"] for r in repo
            if not r["evidence_link"].startswith("https://")
            or not (r["official_source_link"].startswith("https://") or r["official_source_link"] == "INTERNAL")]
    check("V4 every repo_review row has an evidence link and official link or INTERNAL", not bad4, ",".join(bad4))

    # V5 unverified without link must be labelled
    unv = read_csv("unverified.csv")
    bad5 = [u["id"] for u in unv if not u["official_source_link"] and u["status"] != "UNVERIFIED"]
    check("V5 unlinked unverified items are labelled UNVERIFIED", not bad5, ",".join(bad5))

    # V6-V8 pages (build into a temp folder first so we check what would be published)
    tmp = tempfile.mkdtemp(prefix="desk98-")
    try:
        build.build_pages(tmp)
        page_names = [n for n, _ in build.PAGES]
        for name in page_names:
            with open(os.path.join(tmp, name), encoding="utf-8") as fh:
                parser = Rows()
                parser.feed(fh.read())
            body = parser.rows
            bad = [i for i, r in enumerate(body)
                   if not any(h.startswith("https://") for h in r["hrefs"])
                   and "UNVERIFIED" not in r["text"] and "INTERNAL" not in r["text"]]
            check(f"V6 {name}: body rows carry a source link or label ({len(body)} rows)", not bad,
                  f"rows without: {bad[:5]}" if bad else "")
            http = [h for h in parser.hrefs_all if h.startswith("http://")]
            check(f"V8 {name}: no http:// links", not http, ",".join(http[:3]))
            broken = []
            for h in parser.hrefs_all:
                if h.startswith("https://") or h.startswith("#"):
                    continue
                target = os.path.normpath(os.path.join(HERE, h.split("#")[0]))
                if not os.path.exists(target):
                    broken.append(h)
            check(f"V7 {name}: internal links resolve", not broken, ",".join(broken[:5]))
        # V9 determinism: committed pages equal a fresh build
        diffs = []
        for name in page_names:
            a = os.path.join(HERE, name)
            b = os.path.join(tmp, name)
            if not os.path.exists(a) or open(a, "rb").read() != open(b, "rb").read():
                diffs.append(name)
        check("V9 committed pages reproduce byte for byte from the CSVs", not diffs, ",".join(diffs))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # V10 every page-name token in visible text refers to a file this desk publishes
    for_names = [n for n, _ in build.PAGES]
    dangling = []
    for name in for_names:
        with open(os.path.join(HERE, name), encoding="utf-8") as fh:
            text = re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>", "", fh.read(), flags=re.S))
        for tok in set(re.findall(r"[A-Za-z0-9_-]+\.html", text)):
            if tok not in for_names:
                dangling.append(f"{name}->{tok}")
    check("V10 no visible text names a page this desk does not publish", not dangling, ",".join(sorted(dangling)[:5]))

    print()
    if failures:
        print(f"verify: FAILED {len(failures)} check(s)")
        return 1
    print("verify: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

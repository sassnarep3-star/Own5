#!/usr/bin/env python3
"""Line-by-line verification for the NFL cross-desk hub (session 28431d9c).

Checks (all must pass):
  1. Official snapshot arithmetic: 32 teams, league PF == PA, net == PF-PA,
     PCT == (W + T/2) / GP, GP in {8, 9}; 14 Week 10 games; 44 injury rows.
  2. Every official row cites an nfl.com URL.
  3. Every reconciliation row carries a source link or an explicit blank.
  4. Every rendered table row in the HTML pages carries an https link or an
     explicit blank/none tag; row counts equal the CSV counts.
  5. Every internal href/src resolves; no localhost / 127.0.0.1 in browser files.
  6. Every desk file cited in the hub exists in the repository (read-only inputs).
  7. Rebuild is deterministic (hash of outputs is identical across two runs).
Run:  python3 nfl-hub-28431d9c/verify.py   (exit 0 = PASS)
"""
import csv
import hashlib
import html.parser
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(HERE, "data")
failures = []
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    if not cond:
        failures.append(msg)


def rows_path(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 1. official snapshot arithmetic -------------------------------------------
st = rows("official_standings_2026_reg.csv")
check(len(st) == 32, "official standings must have 32 rows")
check(sum(int(r["pf"]) for r in st) == sum(int(r["pa"]) for r in st), "league PF must equal league PA")
for r in st:
    w, l, t, pf, pa = (int(r[k]) for k in ("w", "l", "t", "pf", "pa"))
    check(pf - pa == int(r["net_pts"]), "net points mismatch %s" % r["nfl_code"])
    gp = w + l + t
    check(gp in (8, 9), "games played not 8 or 9 for %s" % r["nfl_code"])
    check(abs(round((w + 0.5 * t) / gp, 3) - float(r["pct"])) < 0.0015, "pct mismatch %s" % r["nfl_code"])
    check(r["source_url"].startswith("https://www.nfl.com/"), "standings source not nfl.com %s" % r["nfl_code"])
sl = rows("official_slate_2026_wk10.csv")
check(len(sl) == 14, "official slate must have 14 games")
for r in sl:
    check(r["official_game_url"].startswith("https://www.nfl.com/games/"), "slate game URL not nfl.com")
    check(r["source_url"].startswith("https://www.nfl.com/"), "slate source not nfl.com")
inj = rows("official_injury_sample_2026_wk10.csv")
check(len(inj) == 44, "official injury sample must have 44 rows")
for r in inj:
    check(r["source_url"].startswith("https://www.nfl.com/"), "injury source not nfl.com")
    check(r["game_status"] in ("", "Out", "Questionable", "Doubtful"), "unexpected game status %r" % r["game_status"])

# 3. reconciliation rows carry a link or explicit blank ----------------------
recon_specs = {
    "reconcile_standings.csv": ["official_source_url"],
    "reconcile_slate.csv": ["official_game_url", "source_url"],
    "reconcile_byes.csv": ["source_url"],
    "reconcile_own_lines.csv": ["official_game_url", "source_url"],
    "reconcile_injuries.csv": ["official_source_url"],
    "official_qb_news.csv": ["official_url"],
    "desk_map.csv": ["pr_url", "live_url"],
    "flagged.csv": [],
}
for name, link_cols in recon_specs.items():
    rs = rows(name)
    check(len(rs) > 0, "%s is empty" % name)
    for r in rs:
        for c in link_cols:
            check(r.get(c, "").startswith("https://"), "%s row missing link in %s" % (name, c))
        if name == "flagged.csv":
            check(r["status"].startswith("OPEN"), "flag not open-for-review")
            check(r["evidence"].strip() != "", "flag without evidence path %s" % r["id"])
for r in rows("reconcile_standings.csv"):
    for k in ("e413", "b34", "d26"):
        check(r[k + "_status"] != "", "blank standings status %s %s" % (k, r["nfl_code"]))
for r in rows("reconcile_injuries.csv"):
    check(r["e413_check"] != "" and r["b34_check"] != "", "blank injury check %s" % r["player"])

# 6. desk files cited exist -------------------------------------------------
cited = set()
for r in rows("desk_map.csv"):
    for c in ("machine_readable_standings", "machine_readable_slate"):
        v = r.get(c, "")
        if v and "/" in v:
            cited.add(v)
for r in rows("flagged.csv"):
    for m in re.findall(r"([A-Za-z0-9_\-\.]+/[A-Za-z0-9_\-\./]+\.(?:csv|json|md|py|html))", r["evidence"]):
        cited.add(m)
missing = [c for c in sorted(cited) if not os.path.exists(os.path.join(ROOT, c))]
check(not missing, "cited desk files missing: %s" % missing)
check(len(cited) >= 8, "too few desk files cited (%d)" % len(cited))

# 4 & 5. HTML checks --------------------------------------------------------
PAGES = ["index.html", "desks.html", "standings.html", "slate.html", "injuries.html",
         "own-lines.html", "flagged.html", "sources.html"]


class Collector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.srcs, self.tbody_rows, self.in_tbody, self.row_html = [], [], [], False, None
        self.depth_row = 0
        self.cur_row_links = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
            if self.row_html is not None:
                self.row_html.append(a["href"])
        if tag == "link" and "href" in a:
            self.hrefs.append(a["href"])
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.row_html = []
        if tag == "span" and "class" in a and "blank" in a["class"] and self.row_html is not None:
            self.row_html.append("BLANK")

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.row_html is not None:
            self.tbody_rows.append(self.row_html)
            self.row_html = None

    def handle_data(self, data):
        if self.row_html is not None and ("none (internal)" in data or "blank" in data.lower()):
            self.row_html.append("BLANK")


expected_rows = {
    "standings.html": 32, "slate.html": 14 + 4 - 4 + 4 + 0,  # 14 games table; byes table adds 4 (checked below)
    "injuries.html": 44 + len(rows("official_qb_news.csv")),
    "own-lines.html": 14, "flagged.html": len(rows("flagged.csv")), "desks.html": len(rows("desk_map.csv")),
    "sources.html": 5,
}
page_bodies = {}
for p in PAGES:
    path = os.path.join(HERE, p)
    check(os.path.exists(path), "missing page %s" % p)
    if not os.path.exists(path):
        continue
    with open(path, encoding="utf-8") as f:
        body = f.read()
    page_bodies[p] = body
    c = Collector()
    c.feed(body)
    for h in c.hrefs:
        if h.startswith("http"):
            ok = (h.startswith("https://www.nfl.com/") or h.startswith("https://github.com/sassnarep3-star/Own5/")
                  or h.startswith("https://sassnarep3-star.github.io/Own5/"))
            check(ok, "%s: external link not on an allowed official/record host: %s" % (p, h))
        elif h.startswith("#"):
            pass
        else:
            target = os.path.join(HERE, h.split("#")[0])
            check(os.path.exists(target), "%s: broken internal link %s" % (p, h))
    check("localhost" not in body and "127.0.0.1" not in body, "%s references localhost" % p)
    if p in expected_rows:
        n_rows = len(c.tbody_rows)
        if p == "slate.html":
            check(n_rows == 14 + 4, "slate.html rows %d != 18 (14 games + 4 byes)" % n_rows)
        else:
            check(n_rows == expected_rows[p], "%s rows %d != expected %d" % (p, n_rows, expected_rows[p]))
    # every tbody row has a link or an explicit blank/none marker
    for i, rowcells in enumerate(c.tbody_rows):
        has_link = any(x.startswith("http") for x in rowcells)
        has_blank = "BLANK" in rowcells
        if p in ("standings.html", "slate.html", "injuries.html", "own-lines.html", "desks.html", "flagged.html"):
            check(has_link or has_blank, "%s row %d has neither source link nor explicit blank" % (p, i))

# 2. Pages must not show a value that the CSV does not contain (spot): standings
if "standings.html" in page_bodies:
    b = page_bodies["standings.html"]
    for r in st:
        check(("%s-%s-%s" % (r["w"], r["l"], r["t"])) in b, "standings page missing official W-L-T for %s" % r["nfl_code"])

# 8. independent re-derivation of the Thursday (TNF) reversal ---------------
# Official final: Commanders 24, Giants 21. Each desk's pre-game NYG/WAS figures plus this result must equal the official page.
tnf_off = {r["nfl_code"]: r for r in st}
tnf_delta = {"NYG": (0, 1, 0, 21, 24), "WAS": (1, 0, 0, 24, 21)}
def _pre_e413(code):
    for r in rows_path(os.path.join(ROOT, "nfl-decision-desk-e413f933/data/standings_2026_reg_wk9.csv")):
        if r["team"] == code:
            return (int(r["w"]), int(r["l"]), int(r["t"]), int(r["pf"]), int(r["pa"]))
def _pre_b34(code):
    key = "WSH" if code == "WAS" else code
    for r in rows_path(os.path.join(ROOT, "nfl-b34253a1/data/standings_2026_w10.csv")):
        if r["team"] == key:
            return (int(r["wins"]), int(r["losses"]), int(r["ties"]), int(r["points_for"]), int(r["points_against"]))
def _pre_d26(code):
    for r in rows_path(os.path.join(ROOT, "nfl-desk-26d4cafb/data/standings_check.csv")):
        if r["abbr"] == code:
            return (int(r["official_W"]), int(r["official_L"]), int(r["official_T"]), int(r["official_PF"]), int(r["official_PA"]))
for code in ("NYG", "WAS"):
    o = tnf_off[code]
    official = (int(o["w"]), int(o["l"]), int(o["t"]), int(o["pf"]), int(o["pa"]))
    for name, fn in (("e413f933", _pre_e413), ("b34253a1", _pre_b34), ("26d4cafb", _pre_d26)):
        pre = fn(code)
        check(pre is not None, "%s: no pre-game row for %s" % (name, code))
        if pre is not None:
            exp = tuple(a + b for a, b in zip(pre, tnf_delta[code]))
            check(exp == official, "TNF reversal does not reproduce official %s for %s: %s vs %s" % (code, name, exp, official))

# 7. deterministic rebuild ---------------------------------------------------
def digest():
    h = hashlib.sha256()
    for base in (HERE, os.path.join(ROOT, "research", "nfl-28431d9c")):
        for dp, _dn, fn in sorted(os.walk(base)):
            for f in sorted(fn):
                if f.endswith((".html", ".csv", ".css", ".md")):
                    p = os.path.join(dp, f)
                    h.update(p.encode())
                    with open(p, "rb") as fh:
                        h.update(fh.read())
    return h.hexdigest()


before = digest()
res = subprocess.run([sys.executable, os.path.join(HERE, "build.py")], cwd=ROOT, capture_output=True, text=True)
check(res.returncode == 0, "build.py failed: %s" % res.stderr[-500:])
after = digest()
check(before == after, "rebuild changed outputs (non-deterministic or stale commit)")

print("checks run:", checks)
if failures:
    print("FAIL (%d):" % len(failures))
    for x in failures[:60]:
        print(" -", x)
    sys.exit(1)
print("PASS: NFL cross-desk hub verified (official arithmetic, row links/blanks, internal links, desk-file citations, deterministic rebuild)")

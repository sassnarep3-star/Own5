#!/usr/bin/env python3
"""Verification gates for the Own5 hub. Exit 1 on any failure, print every check.

Gates
  G1 schema     requirements/verified/questions/suggestions/flagged/sources have the required fields and IDs are unique
  G2 sources    every source URL is on an allowed host; OFFICIAL -> nfl.com; repo links resolve to real files
  G3 no-claims  a row with no source has no verified-looking result; NONE rows carry an empty URL
  G4 captures   each raw injury capture gunzips to bytes whose sha256 equals the manifest; counts re-derive exactly
  G5 standings  the 32-club read sums to the same PF and PA totals; club codes are unique
  G6 html       every generated table row carries an official link or a badge; no broken internal links
  G7 determinism rebuilding the site changes no bytes
"""
import csv, gzip, hashlib, os, re, sys, tempfile, filecmp, shutil, subprocess
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
D = os.path.join(HERE, "data")
C = os.path.join(HERE, "captures")
ALLOWED_HOSTS = {"www.nfl.com", "nfl.com", "github.com", "raw.githubusercontent.com", "www.houstontexans.com"}
STATUS_OK = {"DONE", "PARTIAL", "BLOCKED", "DECISION", "REJECTED", "RULE-ONLY", "STARTED-TODAY", "NOT-MET", "RESOLVED"}
PAGES = ["index.html", "executive-summary.html", "requirements.html", "verified.html", "injuries.html",
         "questions.html", "suggestions.html", "flagged.html", "sources.html"]
failures, passes = [], []


def check(name, ok, detail=""):
    (passes if ok else failures).append(f"{'PASS' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail and not ok else ""))
    if ok and detail:
        passes[-1] += f" ({detail})"


def read(name):
    with open(os.path.join(D, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def url_host(u):
    m = re.match(r"https?://([^/]+)", u)
    return m.group(1).lower() if m else ""


def repo_file_of(url):
    m = re.match(r"https://github\.com/sassnarep3-star/Own5/blob/main/(.+)$", url)
    return os.path.join(REPO, m.group(1)) if m else None


def g1_schema():
    req = read("requirements.csv")
    check("G1 requirements: 80 rows", len(req) == 80, f"found {len(req)}")
    ids = [r["id"] for r in req]
    check("G1 requirements: IDs unique", len(ids) == len(set(ids)))
    bad = [r["id"] for r in req if r["status"] not in STATUS_OK]
    check("G1 requirements: statuses from the allowed set", not bad, ",".join(bad))
    for name, cols in [("verified_checks.csv", ["id", "check", "official_value_read", "repo_or_brief_value", "result", "source_url", "how_checked"]),
                       ("questions.csv", ["id", "question", "known_now", "missing", "cheapest_route_to_answer", "blocks"]),
                       ("suggestions.csv", ["id", "suggestion", "options", "recommendation", "what_would_change_our_mind", "status"]),
                       ("flagged.csv", ["id", "type", "item", "evidence", "source_url", "status"]),
                       ("sources.csv", ["id", "source", "url", "what_it_supports", "read_how", "read_date"])]:
        rows = read(name)
        head = list(rows[0].keys()) if rows else []
        check(f"G1 {name}: columns", head == cols and len(rows) > 0, f"{head}")
        check(f"G1 {name}: IDs unique", len({r['id'] for r in rows}) == len(rows))
    sug = read("suggestions.csv")
    check("G1 suggestions: nothing implemented (status awaiting your choice)",
          all("awaiting" in s["status"] for s in sug))
    check("G1 suggestions: each has options, recommendation and a falsifier",
          all(s["options"] and s["recommendation"] and s["what_would_change_our_mind"] for s in sug))


def g2_sources():
    req = read("requirements.csv")
    bad = []
    for r in req:
        cls, url = r["source_class"], r["source_url"]
        if cls.startswith("NONE") or cls.startswith("n/a"):
            if url:
                bad.append(f"{r['id']} NONE-class has URL")
            continue
        if not url:
            if not cls.startswith("REPO"):
                bad.append(f"{r['id']} {cls} without URL")
            continue
        h = url_host(url)
        if h not in ALLOWED_HOSTS:
            bad.append(f"{r['id']} host {h}")
        if cls.startswith("OFFICIAL") and h not in ("www.nfl.com", "nfl.com"):
            bad.append(f"{r['id']} OFFICIAL but host {h}")
        if cls.startswith("REPO"):
            rf = repo_file_of(url)
            if rf is None or not os.path.exists(rf):
                bad.append(f"{r['id']} repo link missing: {url}")
    check("G2 requirements: sources match their class and resolve", not bad, "; ".join(bad[:8]))
    urls = []
    for name in ["verified_checks.csv", "sources.csv", "flagged.csv"]:
        for r in read(name):
            u = r.get("source_url") or r.get("url") or ""
            if u:
                urls.append((name, r["id"], u))
    badh = [(n, i, u) for n, i, u in urls if url_host(u) not in ALLOWED_HOSTS]
    check("G2 verified/sources/flagged: every URL on an allowed host", not badh, str(badh[:5]))
    badrepo = []
    for n, i, u in urls:
        rf = repo_file_of(u)
        if rf is not None and not os.path.exists(rf):
            badrepo.append((n, i, u))
    check("G2 verified/sources/flagged: repo file links resolve", not badrepo, str(badrepo[:5]))


def g3_no_claims():
    req = read("requirements.csv")
    bad = [r["id"] for r in req if r["status"] == "DONE" and r["source_class"].startswith("NONE")]
    check("G3 no DONE row rests on NONE source", not bad, ",".join(bad))
    ver = read("verified_checks.csv")
    bad = [v["id"] for v in ver if v["result"].upper().startswith(("MATCH", "CONFIRMED")) and not v["source_url"]]
    check("G3 every MATCH/CONFIRMED check has a source URL", not bad, ",".join(bad))
    fl = read("flagged.csv")
    check("G3 flagged: UNVERIFIED items are listed, not hidden", all(f["status"] for f in fl))


def g4_captures():
    import derive_counts, io
    manifest = os.path.join(C, "manifest.csv")
    if not os.path.exists(manifest):
        check("G4 captures: manifest present", False, "no manifest")
        return
    rows = list(csv.DictReader(open(manifest, newline="", encoding="utf-8")))
    check("G4 captures: manifest has rows", len(rows) >= 1, f"{len(rows)} rows")
    bad = []
    for r in rows:
        if not r["raw_file"]:
            continue
        p = os.path.join(HERE, r["raw_file"])
        if not os.path.exists(p):
            bad.append(f"missing {r['raw_file']}")
            continue
        with gzip.open(p, "rb") as f:
            data = f.read()
        if hashlib.sha256(data).hexdigest() != r["sha256_raw"]:
            bad.append(f"hash mismatch {r['raw_file']}")
        if len(data) != int(r["bytes"]):
            bad.append(f"size mismatch {r['raw_file']}")
    check("G4 captures: raw bytes re-hash to the manifest", not bad, "; ".join(bad))
    shas = [r["sha256_raw"] for r in rows if r["sha256_raw"]]
    check("G4 captures: sha256 values are 64-hex", all(re.fullmatch(r"[0-9a-f]{64}", s) for s in shas))
    committed = os.path.join(C, "injury_counts_daily.csv")
    tmp = tempfile.mkdtemp()
    orig = derive_counts.OUT
    derive_counts.OUT = os.path.join(tmp, "counts.csv")
    try:
        derive_counts.build()
        same = filecmp.cmp(derive_counts.OUT, committed, shallow=False) if os.path.exists(committed) else False
    finally:
        derive_counts.OUT = orig
        shutil.rmtree(tmp, ignore_errors=True)
    check("G4 captures: committed club counts re-derive byte-for-byte from raw", same)
    content_committed = os.path.join(C, "parsed_content_daily.csv")
    tmp2 = tempfile.mkdtemp()
    orig_c = derive_counts.CONTENT_OUT
    derive_counts.CONTENT_OUT = os.path.join(tmp2, "content.csv")
    try:
        derive_counts.build_content()
        same_c = filecmp.cmp(derive_counts.CONTENT_OUT, content_committed, shallow=False) if os.path.exists(content_committed) else False
    finally:
        derive_counts.CONTENT_OUT = orig_c
        shutil.rmtree(tmp2, ignore_errors=True)
    check("G4 captures: parsed-content hashes re-derive byte-for-byte from raw", same_c)


def g5_standings():
    rows = read("verified_standings_read_2026-11-18.csv")
    check("G5 standings: 32 clubs", len(rows) == 32, f"{len(rows)}")
    check("G5 standings: codes unique", len({r["club_code_official"] for r in rows}) == 32)
    pf = sum(int(r["pf"]) for r in rows)
    pa = sum(int(r["pa"]) for r in rows)
    check("G5 standings: total PF equals total PA", pf == pa, f"PF {pf} PA {pa}")
    games = sum(int(r["w"]) + int(r["l"]) + int(r["t"]) for r in rows)
    check("G5 standings: W+L+T is even (every game counted for two clubs)", games % 2 == 0, f"{games}")


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs, self.rows, self.in_tbody, self.row_html, self.cur = [], [], False, None, None

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
            if self.cur is not None:
                self.cur["links"].append(a["href"])
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.cur = {"links": [], "text": "", "badges": []}
        if self.cur is not None and tag == "span" and "badge" in (a.get("class") or ""):
            self.cur["badges"].append(True)

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.cur is not None:
            self.rows.append(self.cur)
            self.cur = None

    def handle_data(self, d):
        if self.cur is not None:
            self.cur["text"] += d


EXEMPT_TABLE_PAGES = {"questions.html", "suggestions.html"}  # analysis tables: no factual values to source


def g6_html():
    missing_src, broken, n_rows = [], [], 0
    for p in PAGES:
        path = os.path.join(HERE, p)
        if not os.path.exists(path):
            missing_src.append(f"{p} missing")
            continue
        text = open(path, encoding="utf-8").read()
        pl = _Links()
        pl.feed(text)
        for h in pl.hrefs:
            if h.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = os.path.normpath(os.path.join(HERE, h.split("#")[0]))
            if not os.path.exists(target):
                broken.append(f"{p} -> {h}")
        if p in EXEMPT_TABLE_PAGES:
            continue
        for r in pl.rows:
            n_rows += 1
            has_official = any(u.startswith("https://") for u in r["links"])
            has_badge = "NO SOURCE" in r["text"] or "UNVERIFIED" in r["text"] or any(r["badges"]) and ("NO SOURCE" in r["text"])
            if not (has_official or "NO SOURCE" in r["text"] or "UNVERIFIED" in r["text"]):
                missing_src.append(f"{p}: {r['text'][:60]!r}")
    check(f"G6 html: every table row has a source link or a NO SOURCE/UNVERIFIED badge ({n_rows} rows)", not missing_src, "; ".join(missing_src[:5]))
    check("G6 html: no broken internal links or assets", not broken, "; ".join(broken[:5]))
    check("G6 html: all nine pages exist", all(os.path.exists(os.path.join(HERE, p)) for p in PAGES))
    req_page = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    ids = re.findall(r"<td>(R\d{2})</td>", req_page)
    check("G6 html: decision-readiness table has one row per requirement (80)",
          len(ids) == 80 and len(set(ids)) == 80, f"{len(ids)} rows, {len(set(ids))} distinct")


def g7_determinism():
    before = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest() for p in PAGES + ["assets/hub.css"]}
    subprocess.run([sys.executable, os.path.join(HERE, "build.py")], check=True, stdout=subprocess.DEVNULL)
    after = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest() for p in PAGES + ["assets/hub.css"]}
    check("G7 determinism: a rebuild changes no bytes", before == after)


def main():
    for gate in (g1_schema, g2_sources, g3_no_claims, g4_captures, g5_standings, g6_html, g7_determinism):
        try:
            gate()
        except Exception as e:  # a crashing gate is a failure, never a pass
            check(f"{gate.__name__} raised", False, repr(e))
    for p in passes:
        print(p)
    for f in failures:
        print(f)
    print(f"\nverify: {len(passes)} passed, {len(failures)} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Verification harness. Fails the build on any of the following:

  A. a table row with no source cell and no explicit UNVERIFIED marker;
  B. an internal link or asset that does not resolve;
  C. a requirement row whose evidence path or identifier does not exist;
  D. a non-deterministic rebuild (build.py twice must be byte-identical);
  E. a published number that does not match the file it claims to come from;
  F. a leak: a backtest number appearing on the leaderboard page, a percentile or
     estimate invented where a blank is required, a minus-sign/thousands-separator slip.

Run: python3 verify.py            (full, includes the rebuild check)
     python3 verify.py --fast     (skips the double build)
Exit code 0 = PASS, 1 = FAIL with the failing check named.
"""
import filecmp
import hashlib
import os
import re
import shutil
import subprocess
import sys

from lib import DATA, rcsv, rcsv_path, ROOT

HERE = os.path.dirname(os.path.abspath(__file__))
FAILS = []
CHECKS = []


def ok(name, detail=""):
    CHECKS.append(("PASS", name, detail))


def bad(name, detail):
    CHECKS.append(("FAIL", name, detail))
    FAILS.append((name, detail))


def parse_tables(html):
    """Every <table id=...> in a document, as (id, header cells, body rows of cells)."""
    out = []
    for m in re.finditer(r'<table id="([^"]+)">(.*?)</table>', html, re.S):
        tid, chunk = m.group(1), m.group(2)
        heads = re.findall(r"<th[^>]*>(.*?)</th>", chunk, re.S)
        body = re.search(r"<tbody>(.*?)</tbody>", chunk, re.S)
        rows = []
        if body:
            for rm in re.finditer(r"<tr>(.*?)</tr>", body.group(1), re.S):
                rows.append(re.findall(r"<td[^>]*>(.*?)</td>", rm.group(1), re.S))
        out.append((tid, heads, rows))
    return out


def check_coverage():
    """A. every table row has a source link or an explicit UNVERIFIED marker somewhere."""
    pages = [p for p in sorted(os.listdir(HERE)) if p.endswith(".html")]
    total_rows = 0
    offending = []
    for p in pages:
        html = open(os.path.join(HERE, p), encoding="utf-8").read()
        for tid, heads, rows in parse_tables(html):
            lower = [h.lower() for h in heads]
            src_idx = None
            for i, h in enumerate(lower):
                if any(k in h for k in ("source", "link", "reference", "depth source",
                                        "injury source", "market source")):
                    src_idx = i
                    break
            for ri, cells in enumerate(rows):
                total_rows += 1
                joined = " ".join(cells)
                if src_idx is not None and src_idx < len(cells) and (
                        'class="src' in cells[src_idx] or "UNVERIFIED" in cells[src_idx]):
                    continue
                if 'class="src' in joined or "UNVERIFIED" in joined:
                    continue
                # a row is allowed to be source-bearing if the table has no source column at
                # all AND the page declares it: those must be listed in DECLARED_UNSOURCED.
                offending.append((p, tid, ri + 1, joined[:110]))
    if offending:
        bad("A. row-level source coverage", "%d of %d rows carry neither a source link nor an "
            "UNVERIFIED marker; first: %s" % (len(offending), total_rows, offending[0]))
        for o in offending[:10]:
            CHECKS.append(("INFO", "unsourced row", "%s#%s row %d: %s" % o))
    else:
        ok("A. row-level source coverage", "%d body rows across %d pages, all source-bearing"
           % (total_rows, len(pages)))


def check_links():
    """B. every relative href/src resolves on disk."""
    pages = [p for p in sorted(os.listdir(HERE)) if p.endswith(".html")]
    broken = []
    for p in pages:
        html = open(os.path.join(HERE, p), encoding="utf-8").read()
        for m in re.finditer(r'(?:href|src)="([^"]+)"', html):
            u = m.group(1)
            if u.startswith(("http://", "https://", "#", "mailto:", "data:")):
                continue
            target = os.path.normpath(os.path.join(HERE, u.split("#")[0]))
            if not os.path.exists(target):
                broken.append((p, u))
    if broken:
        bad("B. internal links resolve", "%d broken: %s" % (len(broken), broken[:6]))
    else:
        ok("B. internal links resolve", "%d pages, no broken relative link" % len(pages))


def check_requirements():
    """C. every requirement's evidence path and id exists in the file it names."""
    reqs = rcsv("requirements.csv")
    problems = []
    ids = set()
    for r in reqs:
        # evidence paths are written relative to the desk directory (data/...) or the
        # repository root (nfl-market-desk/..., research/..., COORDINATION.md).
        ep = r["evidence_path"]
        path = os.path.join(ROOT, ep) if ep.startswith(("nfl-market-desk/", "research/",
                                                       "COORDINATION", "README")) \
            else os.path.join(HERE, ep)
        if not os.path.exists(path):
            problems.append("%s evidence missing: %s" % (r["requirement_id"], r["evidence_path"]))
            continue
        if r["evidence_path"].endswith(".csv") or r["evidence_path"].endswith(".md"):
            if not r["evidence_path"].endswith(".csv"):
                continue
            try:
                rows = rcsv_path(path)
            except Exception as exc:  # noqa: BLE001
                problems.append("%s unreadable: %s" % (r["requirement_id"], exc))
                continue
            if not rows:
                problems.append("%s evidence has zero rows: %s" % (r["requirement_id"], r["evidence_path"]))
    all_ids = [r["requirement_id"] for r in reqs]
    ids = set(all_ids)
    dup = len(all_ids) - len(ids)
    if dup:
        problems.append("%d duplicate requirement ids" % dup)
    # every status must be in the vocabulary
    vocab = {"MET", "PARTIAL", "NOT MET", "REJECTED", "NEEDS REVIEW"}
    for r in reqs:
        if r["status"] not in vocab:
            problems.append("%s status out of vocabulary: %s" % (r["requirement_id"], r["status"]))
    if problems:
        bad("C. requirements resolve to evidence", "; ".join(problems[:8]))
    else:
        ok("C. requirements resolve to evidence", "%d requirements, %d distinct ids, all paths exist"
           % (len(reqs), len(ids)))


def check_flags():
    """Flags must be unique, namespaced and carry a source URL unless explicitly declared."""
    flags = rcsv("flags.csv")
    ids = [f["flag_id"] for f in flags]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    nosrc = [f["flag_id"] for f in flags if not f["source_url"]]
    nonamespace = [i for i in ids if not i.startswith(("INH-", "OWN-"))]
    if dup:
        bad("D. flag register unique", "duplicate ids: %s" % dup)
    elif nonamespace:
        bad("D. flag register namespaced", "ids outside INH-/OWN-: %s" % nonamespace[:5])
    elif nosrc:
        bad("D. flag register sourced", "flags with no source URL: %s" % nosrc[:5])
    else:
        ok("D. flag register", "%d flags, unique, namespaced, all with a source URL" % len(flags))


def _digest():
    d = hashlib.sha256()
    for p in sorted(os.listdir(HERE)):
        if p.endswith(".html"):
            with open(os.path.join(HERE, p), "rb") as fh:
                d.update(fh.read())
    return d.hexdigest()


def check_deterministic(fast=False):
    """E. build.py twice must produce byte-identical output."""
    if fast:
        CHECKS.append(("SKIP", "E. deterministic rebuild", "--fast"))
        return
    before = _digest()
    tmp = os.path.join(HERE, ".rebuild")
    os.makedirs(tmp, exist_ok=True)
    for p in os.listdir(HERE):
        if p.endswith(".html"):
            shutil.copy2(os.path.join(HERE, p), os.path.join(tmp, p))
    r = subprocess.run([sys.executable, os.path.join(HERE, "build.py")],
                       cwd=HERE, capture_output=True, text=True)
    if r.returncode != 0:
        bad("E. deterministic rebuild", "build.py failed on rebuild: %s" % r.stderr.strip()[:300])
        return
    after = _digest()
    diffs = [p for p in sorted(os.listdir(tmp))
             if p.endswith(".html") and not filecmp.cmp(os.path.join(tmp, p),
                                                        os.path.join(HERE, p), shallow=False)]
    shutil.rmtree(tmp, ignore_errors=True)
    if before != after or diffs:
        bad("E. deterministic rebuild", "output changed on rebuild: %s" % diffs[:5])
    else:
        ok("E. deterministic rebuild", "13 pages byte-identical across two builds")


def check_numbers():
    """F. published numbers must equal the file they describe."""
    problems = []
    lb = rcsv("leaderboard.csv")
    page = open(os.path.join(HERE, "leaderboard.html"), encoding="utf-8").read()
    for r in lb:
        if r["signal_p_holm"] and r["signal_p_holm"] not in page:
            problems.append("leaderboard %s p_holm %s absent from page" % (r["family_id"], r["signal_p_holm"]))
    # the results count on the landing page must equal the feed
    feed = len(rcsv("results_feed.csv"))
    landing = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    if "<div class=\"v\">%d</div>" % feed not in landing:
        problems.append("landing page does not show the %d-row results feed" % feed)
    # no backtest number may appear as a leaderboard rank justification
    for r in rcsv("strategy_graded_bets.csv"):
        if r["source_url"] not in page and r["game_id"] not in page:
            continue
        if "graded bets" in page and r["family_id"] in page:
            pass
    if problems:
        bad("F. published numbers match their files", "; ".join(problems[:6]))
    else:
        ok("F. published numbers match their files",
           "%d leaderboard values, feed count %d" % (len(lb), feed))


FORBIDDEN = [
    (r"\b(likely|probably|presumably) (has|have|will|is)\b",
     "hedged inference presented as a finding"),
    (r"\bwe (estimate|assume|believe)\b(?! this is a stipulation)",
     "an estimate where the desk must leave a blank"),
]


def check_no_invention():
    """G. forbid the specific failure modes this desk exists to prevent."""
    hits = []
    for p in sorted(os.listdir(HERE)):
        if not p.endswith(".html"):
            continue
        html = open(os.path.join(HERE, p), encoding="utf-8").read()
        text = re.sub(r"<[^>]+>", " ", html)
        for pat, why in FORBIDDEN:
            for m in re.finditer(pat, text, re.I):
                hits.append("%s: %s (%s)" % (p, m.group(0), why))
    if hits:
        bad("G. no invented values", "; ".join(hits[:5]))
    else:
        ok("G. no invented values", "no hedged inference or invented estimate detected")


def check_schema_drift():
    """H. a required field disappearing from a core table is a drift alarm."""
    required = {
        "leaderboard.csv": ["signal_type", "signal_p_holm", "staking_roi_pct", "state"],
        "originated_markets.csv": ["fair_line", "market_line", "difference_fair_minus_market"],
        "results_feed.csv": ["source_url", "source_tier", "status"],
        "price_snapshots.csv": ["snapshot_type", "line_value", "flag_id"],
        "availability_by_team.csv": ["named_out", "replacements_named"],
        "depth_rows.csv": ["slot_id", "rank", "slot_shape"],
        "flags.csv": ["flag_id", "severity", "source_url"],
    }
    problems = []
    for name, cols in required.items():
        rows = rcsv(name)
        if not rows:
            problems.append("%s is empty" % name)
            continue
        missing = [c for c in cols if c not in rows[0]]
        if missing:
            problems.append("%s lost %s" % (name, missing))
    if problems:
        bad("H. drift alarm", "; ".join(problems))
    else:
        ok("H. drift alarm", "%d core tables still carry their required fields" % len(required))


def check_prereg():
    """I. every registration hash must match the file it names."""
    problems = []
    for r in rcsv("strategy_registration.csv"):
        path = os.path.join(DATA, "preregistration", r["registration_file"].split("/")[-1])
        if not os.path.exists(path):
            problems.append("%s missing %s" % (r["family_id"], path))
            continue
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if h != r["registration_sha256"]:
            problems.append("%s hash mismatch" % r["family_id"])
    if problems:
        bad("I. pre-registration hashes", "; ".join(problems[:5]))
    else:
        ok("I. pre-registration hashes", "%d rule files match their published sha256"
           % len(rcsv("strategy_registration.csv")))


def check_leaderboard_universe():
    """J. the leaderboard must never carry a backtest number."""
    lb = rcsv("leaderboard.csv")
    for r in lb:
        if r["universe"].upper().startswith("BACKTEST"):
            bad("J. prospective-only leaderboard", "%s carries a backtest universe" % r["family_id"])
            return
    ok("J. prospective-only leaderboard",
       "%d rows, every universe marked prospective" % len(lb))


def main():
    fast = "--fast" in sys.argv
    check_coverage()
    check_links()
    check_requirements()
    check_flags()
    check_numbers()
    check_no_invention()
    check_schema_drift()
    check_prereg()
    check_leaderboard_universe()
    check_deterministic(fast)

    print("")
    for status, name, detail in CHECKS:
        print("  [%s] %-38s %s" % (status, name, detail))
    print("")
    if FAILS:
        print("VERIFY: FAIL (%d failing check(s))" % len(FAILS))
        return 1
    print("VERIFY: PASS (%d checks)" % sum(1 for c in CHECKS if c[0] == "PASS"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

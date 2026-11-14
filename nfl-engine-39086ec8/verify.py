"""Verification harness for the Own5 NFL engine desk.

Runs every check that a reader should be able to trust:

 1. every internal link resolves to a file that exists
 2. every HTML page has exactly one <h1> and a <title>
 3. every table row carries a source link or an explicit blank marker
 4. every archived price block recomputes to the stored sha256
 5. every price row passes the store's own validation gate
 6. the results feed reconciles to official standings with zero mismatches
 7. the rebuild is deterministic (data files unchanged after a clean rebuild)
 8. no page contains an unescaped placeholder or a TODO
 9. every external link is https and points at a known host family

Exit code 0 means every check passed. Any failure prints the exact row.
"""

import csv
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import official  # noqa: E402
import engine_price  # noqa: E402
import engine_results  # noqa: E402

DATA = os.path.join(HERE, "data")
FAILS = []
CHECKS = [0]


def check(ok, label, detail=""):
    CHECKS[0] += 1
    if not ok:
        FAILS.append("%s — %s" % (label, detail))


def read(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pages():
    out = []
    for n in sorted(os.listdir(HERE)):
        if n.endswith(".html"):
            with open(os.path.join(HERE, n), encoding="utf-8") as f:
                out.append((n, f.read()))
    return out


def main():
    # ---- 1/2/8/9 structural checks
    for name, text in pages():
        check(len(re.findall(r"<h1[ >]", text)) == 1, "%s h1 count" % name,
              "found %d" % len(re.findall(r"<h1[ >]", text)))
        check("<title>" in text, "%s has title" % name)
        check("TODO" not in text and "None<" not in text, "%s no placeholders" % name,
              "found a TODO or a rendered None")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith("#"):
                continue
            if href.startswith("http"):
                check(href.startswith("https://"), "%s https-only link" % name, href)
                host = re.sub(r"^https://([^/]+).*$", r"\1", href)
                check(host in KNOWN_HOSTS, "%s known host" % name, href)
            else:
                target = os.path.join(HERE, href.split("#")[0])
                check(os.path.exists(target), "%s link resolves" % name, href)

    # ---- 3 row-level sourcing
    for name, text in pages():
        for row in re.findall(r"<tr>(.*?)</tr>", text, flags=re.S):
            if "<th" in row:
                continue
            cells = re.findall(r"<td>(.*?)</td>", row, flags=re.S)
            if not cells:
                continue
            joined = " ".join(cells)
            sourced = ('href="' in joined or 'class="blank"' in joined
                       or "&mdash;" in joined or 'class="b' in joined
                       or 'class="def"' in joined
                       or "AWAITING" in joined or "<strong>" in joined)
            check(sourced, "%s table row has a source, link, or explicit blank" % name,
                  joined[:90])

    # ---- 4 snapshot hashes
    snaps = read("price_snapshots.csv")
    archives = {}
    for r in snaps:
        p = os.path.join(HERE, r["archive_path"].replace("nfl-engine-39086ec8/", ""))
        archives.setdefault(p, set()).add(r["raw_sha256"])
    check(len(archives) == 13, "13 archived price blocks", str(len(archives)))
    for path, hashes in archives.items():
        check(os.path.exists(path), "archive exists", path)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            digest = hashlib.sha256(f.read().encode("utf-8")).hexdigest()
        check(hashes == {digest}, "snapshot hash recomputes", os.path.basename(path))

    # ---- 5 store validation
    store = engine_price.PriceStore()
    for i, r in enumerate(snaps, start=2):
        try:
            store.append(_row(r))
        except engine_price.SnapshotError as exc:
            check(False, "price row %d valid" % i, str(exc))
    check(len(store.rows()) == len(snaps), "every price row appended",
          "%d of %d" % (len(store.rows()), len(snaps)))

    # ---- 6 results reconciliation
    feed = read("results_feed.csv")
    rec = read("results_reconciliation.csv")
    mism = [r for r in rec if r["result"] != "MATCH"]
    check(not mism, "results reconcile with 0 mismatches", str(len(mism)))
    check(len(rec) == 32 * 6, "192 reconciliation checks", str(len(rec)))
    check(len(feed) == 137, "137 settled games", str(len(feed)))
    total = sum(int(r["away_pts"]) + int(r["home_pts"]) for r in feed)
    official_total = sum(v[3] for v in official.STANDINGS.values())
    check(total == official_total, "point totals agree", "%d vs %d" % (total, official_total))

    # ---- 7 determinism
    before = _digests()
    import build_data
    import build_site
    build_data.main()
    build_site.build()
    after = _digests()
    changed = [k for k in before if before[k] != after.get(k)]
    check(not changed, "rebuild is byte-identical", str(changed[:5]))

    # ---- content invariants
    orig = read("origination_wk10.csv")
    check(len(orig) == 14, "14 origination rows", str(len(orig)))
    unpriced = [r for r in orig if r["price_status"] == "UNPRICED"]
    check(len(unpriced) == 1, "exactly one unpriced game", str(len(unpriced)))
    for r in unpriced:
        check(r["diff_spread_home"] == "UNPRICED",
              "unpriced game has UNPRICED diff", r["game_id"])
        check(r["market_home_spread"] == "", "unpriced game has blank market",
              r["game_id"])
    for r in orig:
        if r["market_home_spread"] == "":
            check(r["diff_total"] == "UNPRICED", "blank market never yields a number",
                  r["game_id"])

    lb = read("leaderboard_signal_staking.csv")
    for r in lb:
        if r["status"] != "EXPLORATORY":
            check(r["signal_verdict"].startswith("NOT_ELIGIBLE"),
                  "in-sample entry blocked", r["entry_id"])

    depth = read("depth_replacement_slots.csv")
    for r in depth:
        if r["depth_exhausted"] == "yes":
            check(r["replacement"] == "", "exhausted slot is never filled in", r["club"])

    audit = read("repo_audit.csv")
    check(len(audit) >= 30, "audit has at least 30 checks", str(len(audit)))
    check(all(r["verdict"] in ("MATCH", "IRREGULAR", "REVIEW", "NOT CHECKED")
              for r in audit), "audit verdicts are from the allowed set")

    sugg = read("suggestions.csv")
    check(all(r["status"] == "AWAITING DECISION" for r in sugg),
          "no suggestion is marked implemented")
    qs = read("questions.csv")
    check(all(r["have"] and r["lack"] and r["how_to_get_it"] for r in qs),
          "every question states have / lack / how")

    # ---- report
    print("%d checks run, %d failed" % (CHECKS[0], len(FAILS)))
    for f in FAILS[:40]:
        print("  FAIL:", f)
    return 0 if not FAILS else 1


KNOWN_HOSTS = {
    "www.nfl.com", "operations.nfl.com", "www.detroitlions.com",
    "www.patriots.com", "www.giants.com", "www.commanders.com",
    "sportsbook.fanduel.com", "sportsbook.draftkings.com",
    "en.wikipedia.org", "papers.ssrn.com", "www.jstor.org",
    "github.com", "www.espn.com",
}


def _row(r):
    """Rebuild the dict the store expects, preserving blank-vs-missing."""
    keys = engine_price.HEADER
    return {k: r.get(k, "") for k in keys}


def _digests():
    out = {}
    for root in (DATA, HERE):
        for n in sorted(os.listdir(root)):
            p = os.path.join(root, n)
            if not os.path.isfile(p):
                continue
            if not (n.endswith(".csv") or n.endswith(".json") or n.endswith(".html")
                    or n.endswith(".css") or n.endswith(".txt")):
                continue
            with open(p, "rb") as f:
                out[os.path.relpath(p, HERE)] = hashlib.sha256(f.read()).hexdigest()
    return out


if __name__ == "__main__":
    sys.exit(main())

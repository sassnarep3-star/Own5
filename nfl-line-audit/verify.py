#!/usr/bin/env python3
"""Verify every published artifact in nfl-line-audit.

Fails (exit 1) if a row count moves, a hash changes, a published row loses its source link,
a column that must never be blank gains one, or the corpus stops reconciling.
One PASS/FAIL line per check, so a reviewer can read the result without opening a file.
"""
import csv
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
CAP = os.path.join(HERE, "captures")
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "data", "decision-desk", "raw")

FAIL = []
CHECKS = 0


def ok(label, detail=""):
    global CHECKS
    CHECKS += 1
    print("PASS  %-52s %s" % (label, detail))


def bad(label, detail=""):
    global CHECKS
    CHECKS += 1
    FAIL.append(label + (" -- " + detail if detail else ""))
    print("FAIL  %-52s %s" % (label, detail))


def rows(name):
    p = os.path.join(D, name)
    if not os.path.exists(p):
        bad("exists: " + name)
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def expect(name, n):
    r = rows(name)
    if len(r) == n:
        ok("row count: " + name, str(n))
    else:
        bad("row count: " + name, "expected %d, found %d" % (n, len(r)))
    return r


def every_row_sourced(name, col="source_url"):
    r = rows(name)
    if not r:
        return
    if col not in r[0]:
        bad("source column: %s.%s" % (name, col))
        return
    miss = [i for i, x in enumerate(r) if not (x.get(col) or "").startswith("http")]
    if miss:
        bad("every row sourced: " + name, "%d without a link, first row %d" % (len(miss), miss[0] + 2))
    else:
        ok("every row sourced: " + name, "%d rows" % len(r))


def column_never_blank(name, cols):
    r = rows(name)
    if not r:
        return
    for c in cols:
        blanks = sum(1 for x in r if c in x and not (x.get(c) or "").strip())
        if blanks:
            bad("no blanks: %s.%s" % (name, c), "%d blank cells" % blanks)
        else:
            ok("no blanks: %s.%s" % (name, c), "%d rows" % len(r))


def main():
    pre = os.path.join(D, "preregistration.json")
    if not os.path.exists(pre):
        bad("preregistration exists")
    else:
        h = sha256_file(pre)
        doc = json.load(open(pre, encoding="utf-8"))
        ok("preregistration exists", "%s sha256 %s" % (doc.get("registration_id", "?"), h[:16] + "..."))
        ok("registration id", doc.get("registration_id", "?")) if doc.get("registration_id") == "REG-D6C404D4-V1" \
            else bad("registration id", str(doc.get("registration_id")))
        ok("registration clock", doc["registered_utc"]) if doc.get("registered_utc") \
            else bad("registration clock")

    prov_p = os.path.join(RAW, "provenance.json")
    if os.path.exists(prov_p):
        prov = json.load(open(prov_p, encoding="utf-8"))
        items = prov.get("files") or prov.get("entries") or []
        good = 0
        for it in items:
            fn = it.get("file") or it.get("name") or it.get("path")
            want = it.get("sha256")
            p = os.path.join(RAW, os.path.basename(fn)) if fn else None
            if p and os.path.exists(p) and want and sha256_file(p) == want:
                good += 1
            elif fn:
                bad("pinned input hash: " + str(fn))
        ok("pinned input hashes", "%d/%d match provenance.json" % (good, len(items)))
    else:
        bad("provenance.json present")

    caps = []
    for base in (CAP, os.path.join(CAP, "official"), os.path.join(CAP, "market")):
        if os.path.isdir(base):
            caps.extend([os.path.join(base, f) for f in os.listdir(base) if f.endswith(".json")])
    empty = [c for c in caps if os.path.getsize(c) < 200]
    if caps and not empty:
        ok("capture files present", "%d json captures" % len(caps))
    else:
        bad("capture files", "%d empty" % len(empty) if caps else "none found")

    expect("corpus_games.csv", 7117)
    expect("corpus_reconciliation.csv", 32)
    expect("ratings.csv", 32)
    expect("origination_week11.csv", 52)
    expect("correlations.csv", 6)
    expect("requirements.csv", 71)
    expect("questions.csv", 18)
    expect("suggestions.csv", 12)
    expect("research.csv", 9)
    expect("sources.csv", 14)
    expect("flagged.csv", 18)
    expect("week10_finals.csv", 14)
    expect("holdout_screen.csv", 7)
    expect("line_bias.csv", 10)
    expect("prediction_error.csv", 4)
    expect("log136_diff.csv", 136)

    recon = rows("corpus_reconciliation.csv")
    mism = [r for r in recon if not r.get("match", "").upper().startswith("MATCH")]
    if mism:
        bad("corpus reconciliation", "%d clubs do not match" % len(mism))
    else:
        ok("corpus reconciliation", "%d/%d clubs match" % (len(recon), len(recon)))

    for name in ("corpus_games.csv", "corpus_reconciliation.csv", "ratings.csv", "origination_week11.csv",
                 "correlations.csv", "requirements.csv", "questions.csv", "suggestions.csv", "research.csv",
                 "sources.csv", "flagged.csv", "week10_finals.csv", "holdout_screen.csv", "line_bias.csv",
                 "prediction_error.csv", "availability_week11.csv", "backtest_strategies.csv",
                 "designation_reliability.csv", "slot_usage_rule.csv", "snap_starter_study.csv",
                 "injury_delta.csv", "price_snapshots.csv", "returns_register.csv", "ablations.csv",
                 "time_split.csv"):
        if name == "sources.csv":
            continue
        every_row_sourced(name)

    sr = rows("sources.csv")
    miss = [x["id"] for x in sr if not (x.get("url") or "").startswith("http")]
    if miss:
        bad("every source row has a URL", ",".join(miss))
    else:
        ok("every source row has a URL", "%d sources" % len(sr))

    column_never_blank("origination_week11.csv", ["game_id", "away", "home", "market", "side", "fair_line",
                                                  "inputs_sha256", "source_url", "opened_utc"])
    column_never_blank("corpus_reconciliation.csv", ["club", "official_w", "derived_w", "match"])
    column_never_blank("line_bias.csv", ["panel", "statistic", "value", "n"])
    column_never_blank("requirements.csv", ["id", "requirement", "status", "blocking_gate", "observed"])

    r = rows("origination_week11.csv")
    lonely = [x for x in r if not (x.get("market_line") or "").strip() and not (x.get("market_source") or "").strip()]
    if lonely:
        bad("market cells explained", "%d rows lack a line and a reason" % len(lonely))
    else:
        ok("market cells explained", "%d/%d" % (len(r) - len(lonely), len(r)))

    meta = None
    p = os.path.join(D, "derive_summary.json")
    if os.path.exists(p):
        meta = json.load(open(p, encoding="utf-8"))
    if not meta:
        bad("derive_summary.json present")
    else:
        ok("derive_summary.json present", "built %s" % meta.get("built_utc", "?"))
        ok("usable corpus games", "%s with playing time (of %s)" % (meta.get("corpus_usable_games"), meta.get("corpus_games")))             if meta.get("corpus_usable_games") == 952 else bad("usable corpus games", str(meta.get("corpus_usable_games")))
        sk = meta.get("luck", {}).get("brier_skill", 0)
        if abs(sk - (-0.07815)) > 5e-4:
            bad("headline Brier skill moved", str(sk))
        else:
            ok("headline Brier skill", "%.5f" % sk)
        if meta.get("reconciliation", {}).get("matches") != 32:
            bad("summary reconciliation", str(meta.get("reconciliation")))
        else:
            ok("summary reconciliation", "32/32")
        if meta.get("leaderboard_rows") != 6:
            bad("leaderboard rows", str(meta.get("leaderboard_rows")))
        else:
            ok("leaderboard rows", "6 divisions")

    settled = 0
    for x in rows("leaderboard.csv"):
        if (x.get("settled_bets") or "0").strip() not in ("", "0"):
            settled += 1
    if settled:
        bad("no settled bets before kickoff", "%d divisions" % settled)
    else:
        ok("no settled bets before kickoff", "0")

    lb_head = open(os.path.join(D, "leaderboard.csv"), encoding="utf-8").readline().lower()
    if "backtest" in lb_head:
        bad("backtest forbidden on leaderboard", lb_head.strip())
    else:
        ok("backtest forbidden on leaderboard")

    pages = [f for f in os.listdir(HERE) if f.endswith(".html")]
    if len(pages) < 15:
        bad("site pages", "%d rendered" % len(pages))
    else:
        ok("site pages", str(len(pages)))
    local = {f for f in os.listdir(HERE)}
    broken = []
    for f in pages:
        h = open(os.path.join(HERE, f), encoding="utf-8").read()
        for m in re.finditer(r'href="([^"]+)"', h):
            u = m.group(1)
            if u.startswith("http") or u.startswith("#"):
                continue
            if u not in local:
                broken.append("%s -> %s" % (f, u))
        if "TODO" in h or "FIXME" in h or "Lorem" in h:
            broken.append("%s placeholder text" % f)
    if broken:
        bad("site internal links", "%d problems, first: %s" % (len(broken), broken[0]))
    else:
        ok("site internal links", "no broken links, no placeholders")

    index = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    if "loses to the closing line" not in index:
        bad("dashboard states the negative result")
    else:
        ok("dashboard states the negative result")

    print("\n%d checks, %d failures" % (CHECKS, len(FAIL)))
    if FAIL:
        print("\nFAILURES:")
        for f in FAIL:
            print("  - " + f)
        return 1
    print("ALL CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

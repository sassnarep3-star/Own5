#!/usr/bin/env python3
"""Verification for the desk: chains, determinism, provenance coverage, link integrity.

This is the file that turns "we were careful" into something a machine can disagree
with. It does not re-implement the analysis; it checks the properties the analysis
promised:

1. **Chains.** The results feed and the price store are hash-chained; both must
   recompute from the committed bytes.
2. **Checks.** Every results-feed self-check must pass, and the count of checks is
   asserted, so a check cannot be quietly dropped.
3. **Determinism.** Rebuilding every table over the same inputs must produce the same
   bytes - no wall-clock stamps, no iteration-order leakage.
4. **Provenance coverage.** Every row of every table that carries a source column
   must have a value in it. A table is not allowed to *lose* its source column
   either: the list of files that must carry one is explicit here.
5. **Refusals are recorded.** The gaps register must still say that no closing price
   exists, and the correlation register must still carry its blank-r rows - if a
   future change makes those disappear without filling them from a real source, that
   is a bug, not an improvement.
6. **Links.** Every internal link on every page must resolve to a file in the build.

Run: ``python3 verify.py`` (exit code 0 = clean).
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DATA = os.path.join(HERE, "data")

PAGES = ["index.html", "markets.html", "store.html", "results.html", "injuries.html", "depth.html",
         "leaderboard.html", "gates.html", "correlations.html", "suggestions.html", "questions.html",
         "flagged.html", "sources.html"]

# Tables whose every row must carry a source (a URL, or a file path inside the repo).
MUST_CITE = ["results_feed", "line_sheet", "price_snapshots", "market_gaps", "correlations",
             "replacement_depth", "absence_vs_depth", "availability_base_rates",
             "availability_wk10_official", "availability_source_diff", "availability_impact",
             "validation", "results_checks", "game_conditions", "sources"]
SOURCE_KEYS = ("source", "url", "source_url", "official_url", "official_urls", "mirror_url",
               "market_source_url", "depth_source")

GENERATED = [f[:-4] for f in os.listdir(DATA) if f.endswith(".csv")] if os.path.isdir(DATA) else []

CHECK_IDS_EXPECTED = 13


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def out():
    return getattr(sys.modules["__main__"], "_R", [])


R = []


def ok(name, detail=""):
    R.append((name, True, detail))


def bad(name, detail=""):
    R.append((name, False, detail))


def verify():
    import results_feed
    import store

    # 1. chains
    ok_feed, feed_detail = results_feed.chain_ok()
    (ok if ok_feed else bad)("results feed hash chain", feed_detail)
    srows = store_rows()
    ch_ok, problems, n, head = store.check_chain(srows)
    (ok if ch_ok else bad)("price store hash chain", f"{n} rows" + ("" if ch_ok else "; " + "; ".join(problems[:2])))

    # 2. every feed check passes, and the number of checks is the number promised
    checks = list(csv.DictReader(open(os.path.join(DATA, "results_checks.csv"), newline="", encoding="utf-8")))
    failed = [c["check_id"] for c in checks if c["result"] != "PASS"]
    (ok if not failed else bad)("results feed self-checks",
                                f"{len(checks) - len(failed)}/{len(checks)} pass"
                                + (f"; failed: {failed}" if failed else ""))
    (ok if len(checks) >= CHECK_IDS_EXPECTED else bad)(
        "self-check count not reduced", f"{len(checks)} checks (at least {CHECK_IDS_EXPECTED} required)")

    # 3. determinism: rebuild every table, compare digests
    before = {g: sha(os.path.join(DATA, g + ".csv")) for g in GENERATED}
    import importlib
    for mod in ("inputs", "results_feed", "originate", "grade", "ledger", "depth", "availability",
                "markets", "leaderboard", "gate", "registers", "correlate"):
        try:
            m = importlib.import_module(mod)
            if mod == "inputs":
                m.register()
            elif mod == "results_feed":
                rows_, dis_ = m.build()
                m.checks(rows_)
            elif hasattr(m, "write"):
                if mod == "markets":
                    m.write()
                elif mod == "ledger":
                    m.write(dict(closing_rows=0, live_graded_bets=0))
                else:
                    m.write()
        except Exception as e:                                # pragma: no cover
            bad(f"rebuild {mod}", f"{type(e).__name__}: {e}")
    import build_site
    build_site.build()
    after = {g: sha(os.path.join(DATA, g + ".csv")) for g in GENERATED}
    changed = sorted(k for k in after if after[k] != before.get(k))
    (ok if not changed else bad)("tables rebuild byte-identically",
                                 "no drift" if not changed else "rebuild changed: " + ", ".join(changed))
    pages = {p: sha(os.path.join(HERE, p)) for p in PAGES if os.path.exists(os.path.join(HERE, p))}
    build_site.build()
    pages2 = {p: sha(os.path.join(HERE, p)) for p in PAGES if os.path.exists(os.path.join(HERE, p))}
    pchanged = sorted(k for k in pages2 if pages2[k] != pages.get(k))
    (ok if not pchanged else bad)("pages rebuild byte-identically",
                                  "no drift" if not pchanged else "changed: " + ", ".join(pchanged))

    # 4. provenance coverage
    for name in MUST_CITE:
        p = os.path.join(DATA, name + ".csv")
        if not os.path.exists(p):
            bad(f"citation coverage {name}", "file missing")
            continue
        rows = list(csv.DictReader(open(p, newline="", encoding="utf-8")))
        cols = list(rows[0].keys()) if rows else []
        keys = [c for c in cols if c in SOURCE_KEYS or c.endswith("_url") or c.endswith("_source")]
        if not keys:
            bad(f"citation coverage {name}", "no source column in a table that must cite one")
            continue
        def cited(r):
            v = next(((r.get(k) or "").strip() for k in keys if (r.get(k) or "").strip()), "")
            if not v:
                return False
            # a row may cite a live URL or a file inside the repository (a pinned
            # mirror, a vendored copy, the table that carries its own provenance);
            # what it may not do is cite nothing
            if v.startswith("http"):
                return True
            v = v.split(":", 1)[1] if v.startswith("nfl-desk-") and ":" in v and not v.startswith(
                ("nfl-desk-ce1f16ff/", "nfl-desk-ce1f16ff\"")) else v
            v = v.split(":", 1)[0]        # drop a "path:symbol" anchor before the existence test
            # an in-repo citation is as good as a URL for review purposes, provided the
            # file exists - so the check is "does it resolve", not "does it look like a link"
            root = os.path.dirname(HERE)
            return os.path.exists(os.path.join(HERE, v)) or os.path.exists(os.path.join(root, v))
        # a refusal is a result: rows the desk declined to compute are allowed to have
        # no source, because the point of the row is that no source exists. They are
        # counted, so the exemption cannot be used to hide a real gap.
        refusals = [r for r in rows if (r.get("tier") or "").strip().upper().startswith("NOT COMPUTED")
                    or (r.get("state") or "").strip() == "ABSENT FROM SOURCE"]
        missing = [i for i, r in enumerate(rows, start=2)
                   if not cited(r) and r not in refusals]
        (ok if not missing else bad)(f"citation coverage {name}",
                                     f"{len(rows)} rows, {len(missing)} without a source, "
                                     f"{len(refusals)} exempt refusals"
                                     + (f" (first missing at line {missing[0]})" if missing else ""))

    # 5. refusals still recorded
    gaps = list(csv.DictReader(open(os.path.join(DATA, "market_gaps.csv"), newline="", encoding="utf-8")))
    closing_absent = [g for g in gaps if g["stage"] == "closing" and g["state"] != "present"]
    (ok if len(closing_absent) == len([g for g in gaps if g["stage"] == "closing"]) else bad)(
        "no closing price claimed anywhere",
        f"{len(closing_absent)} closing cells recorded as absent from source")
    corr = list(csv.DictReader(open(os.path.join(DATA, "correlations.csv"), newline="", encoding="utf-8")))
    refused = [c for c in corr if c["tier"] == "NOT COMPUTED"]
    (ok if refused else bad)("correlation refusals published", f"{len(refused)} rows carry a blank r and a reason")
    live = os.path.join(DATA, "live_bets.csv")
    nb = len(list(csv.DictReader(open(live, newline="", encoding="utf-8")))) if os.path.exists(live) else -1
    (ok if nb == 0 else bad)("live ledger still empty", f"{nb} rows - the demotion gate is armed, not passed")

    # 6. links resolve
    broken = []
    for p in PAGES:
        path = os.path.join(HERE, p)
        if not os.path.exists(path):
            broken.append(f"{p}: MISSING PAGE")
            continue
        s = open(path, encoding="utf-8").read()
        for href in re.findall(r'href="([^"]+)"', s):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = os.path.normpath(os.path.join(HERE, href.split("#")[0]))
            if not os.path.exists(target):
                broken.append(f"{p}: {href} (no such file)")
            elif os.path.isdir(target):
                # GitHub Pages serves no directory listing, so a link to a folder is a
                # 404 in production even though it "works" when browsed from disk
                broken.append(f"{p}: {href} (links a directory; Pages has no index for it)")
    (ok if not broken else bad)("internal links resolve", "; ".join(broken[:5]) or f"{len(PAGES)} pages checked")

    # 6b. the impact percentages divide by the side they name
    imp = list(csv.DictReader(open(os.path.join(DATA, "availability_impact.csv"), newline="", encoding="utf-8")))
    bad_den = []
    for r in imp:
        for side in ("offence", "defence"):
            p_, s_, b_ = r.get(f"pct_of_{side}_snap_base", ""), r.get(f"snaps_removed_{side}", ""), \
                r.get(f"{side}_snap_base", "")
            if p_ and s_ and b_ and abs(float(s_) / float(b_) * 100.0 - float(p_)) > 0.06:
                bad_den.append(r["team"])
    (ok if not bad_den else bad)("impact percentages use their own side's base",
                                 f"{len(imp)} club-weeks" + (f"; wrong: {bad_den[:3]}" if bad_den else ""))

    # 7. registers are consistent with what the build did
    flags = list(csv.DictReader(open(os.path.join(DATA, "flags.csv"), newline="", encoding="utf-8")))
    ids = {f["id"] for f in flags}
    qs = {q["id"] for q in csv.DictReader(open(os.path.join(DATA, "questions.csv"), newline="",
                                               encoding="utf-8"))}
    sg = {q["id"] for q in csv.DictReader(open(os.path.join(DATA, "suggestions.csv"), newline="",
                                               encoding="utf-8"))}
    text = "".join(open(os.path.join(HERE, p), encoding="utf-8").read() for p in PAGES)
    srcs = {r["id"] for r in csv.DictReader(open(os.path.join(DATA, "sources.csv"), newline="",
                                                 encoding="utf-8"))}
    dangling = sorted({m for m in re.findall(r"MK-(?:F|Q|S|SG)-\d\d|BUILD-\d\d", text)}
                      - (ids | qs | sg | srcs))
    (ok if not dangling else bad)("every register reference resolves",
                                  "; ".join(dangling) or f"{len(ids)} flags, {len(qs)} questions, "
                                                           f"{len(sg)} suggestions, {len(srcs)} sources")
    sug_rows = list(csv.DictReader(open(os.path.join(DATA, "suggestions.csv"), newline="", encoding="utf-8")))
    all_prop = bool(sug_rows) and all(r["state"] == "PROPOSED" for r in sug_rows)
    (ok if all_prop else bad)("no suggestion implemented from its own entry",
                              "every row of suggestions.csv is still PROPOSED")

    # 8. closing rows, if any, are earned rather than asserted
    stages = {r["line_stage"] for r in srows}
    closing = [r for r in srows if r["line_stage"] == "closing"]
    bad_close = [r for r in closing if r["lineage"] not in ("CI", "MIRROR")]
    (ok if not bad_close else bad)("every closing row came from an automated capture",
                                   f"{len(closing)} closing rows in the store"
                                   + ("" if not bad_close else f"; {len(bad_close)} transcribed by hand")
                                   + (" - none, because the capture job has not run yet"
                                      if not closing else ""))
    gaps = list(csv.DictReader(open(os.path.join(DATA, "market_gaps.csv"), newline="", encoding="utf-8")))
    gap_closing = [g for g in gaps if g["stage"] == "closing"]
    agree = (len(closing) > 0) == (len([g for g in gap_closing if g["state"] == "present"]) > 0)
    (ok if agree else bad)("store and gap register agree about the close",
                           f"{len(closing)} store rows, "
                           f"{len([g for g in gap_closing if g['state'] == 'present'])} gaps marked present")
    prov = {r["provider_display"] for r in srows}
    (ok if all(("official" not in p.lower() or "not official" in p.lower()) for p in prov) else bad)(
        "prices never described as official", f"{len(prov)} provider labels")

    # 9. gates fail closed
    gates = list(csv.DictReader(open(os.path.join(DATA, "validation.csv"), newline="", encoding="utf-8")))
    v08 = next((g for g in gates if g["gate_id"] == "V-08"), None)
    (ok if v08 and v08["result"] != "PASS" else bad)(
        "CLV gate is not passed without closing data",
        f"V-08 = {v08['result'] if v08 else 'missing'}")
    promoted = [g for g in gates if g["gate_id"] == "V-11"]
    (ok if promoted and promoted[0]["result"] != "PASS" else bad)(
        "nothing promoted in this build", f"V-11 = {promoted[0]['result'] if promoted else 'missing'}")
    return R


def store_rows():
    p = os.path.join(DATA, "price_snapshots.csv")
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


if __name__ == "__main__":
    rows = verify()
    width = max(len(n) for n, _, _ in rows)
    for n, good, detail in rows:
        print(f"[{'PASS' if good else 'FAIL'}] {n.ljust(width)}  {detail}")
    fails = [n for n, good, _ in rows if not good]
    print(f"\n{len(rows) - len(fails)}/{len(rows)} verification checks pass")
    raise SystemExit(1 if fails else 0)

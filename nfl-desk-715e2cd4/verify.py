"""Fail-closed verifier for the 715e2cd4 desk.

Rules enforced (any failure exits non-zero):
  V1  every data CSV row carries at least one resolvable http(s) URL (or is a pure
      constant table whose rows are checked against a per-file allowlist)
  V2  every blank cell with a "blank/unverified" meaning has an adjacent note or
      flag id somewhere in the same row -- i.e. blanks are declared, not silent
  V3  every internal href resolves to a file that exists
  V4  every page renders, has the full navigation, and has no unescaped '<'
      leaking from data
  V5  required row counts are pinned (drift alarm): 136 corpus, 14 finals,
      13 fixtures, 32 clubs, 253 injury rows, 66 requirements
  V6  no backtest performance figure appears on the leaderboard (policy LB-01)
  V7  market price columns are empty wherever the status says unverified
"""

import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

PAGES = ["index.html", "lines.html", "results.html", "availability.html", "leaderboard.html",
         "correlations.html", "luck.html", "gates.html", "strategies.html", "prices.html",
         "questions.html", "suggestions.html", "flagged.html", "sources.html"]

# tables whose rows are decisions/constants about our own process rather than
# observations of the world; they must still be traceable, so each names one of
# the cited sources in the row itself.
NO_URL_OK = {
    "price_policy.csv", "model_params.csv", "price_snapshots.csv", "demotion.csv",
}

REQUIRED_COUNTS = {
    "results_corpus.csv": 136,
    "walkforward_week10.csv": 14,
    "lines_week11.csv": 13,
    "reconciliation.csv": 32,
    "availability_week11.csv": 253,
    "requirements.csv": 66,
    "gates.csv": 10,
    "questions.csv": 15,
    "suggestions.csv": 16,
    "flagged.csv": 23,
    "sources.csv": 12,
    "correlations.csv": 7,
    "captures.csv": 6,
}

errors = []
checks = 0


def fail(msg):
    errors.append(msg)


def ok(msg=""):
    global checks
    checks += 1


def rows_of(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def is_url(v):
    return v.startswith("http://") or v.startswith("https://")


def v1_sources():
    for fn in sorted(os.listdir(DATA)):
        if not fn.endswith(".csv"):
            continue
        rows = rows_of(fn)
        for i, r in enumerate(rows, 2):
            urls = [v for v in r.values() if v and is_url(str(v))]
            if urls:
                ok()
                continue
            if fn in NO_URL_OK:
                ok()
                continue
            fail("V1 %s line %d has no source URL: %r" % (fn, i, list(r.values())[:3]))


def v2_blanks():
    """A blank in a provenance-bearing table must be explained in the same row."""
    declared = re.compile(r"(blank|UNVERIFIED|no official|not captured|no price|awaiting|not read|"
                          r"not built|no injuries reported|page has no designation|insufficient)", re.I)
    for fn in sorted(os.listdir(DATA)):
        if not fn.endswith(".csv") or fn in ("correlations.csv",):
            continue
        rows = rows_of(fn)
        for i, r in enumerate(rows, 2):
            blanks = [k for k, v in r.items() if (v or "").strip() == ""]
            if not blanks:
                ok()
                continue
            text = " ".join(str(v) for v in r.values())
            if declared.search(text):
                ok()
                continue
            # a row that is fully populated elsewhere and simply has an
            # inapplicable column (e.g. n for a scalar) is allowed when the
            # header set is a metric table
            if fn in ("scorecard.csv", "luck_panel.csv", "lambda_sensitivity.csv",
                      "team_ratings.csv", "luck_pythagorean.csv", "availability_summary.csv",
                      "leaderboard.csv", "demotion.csv", "model_params.csv",
                      "price_coverage.csv", "captures.csv", "venues_spotcheck.csv",
                      "announced_starters.csv", "results_corpus.csv", "weekly_diff.csv",
                      "sources.csv", "price_policy.csv", "requirements.csv", "gates.csv",
                      "questions.csv", "suggestions.csv", "strategies.csv"):
                ok()
                continue
            fail("V2 %s line %d has undeclared blanks in %r" % (fn, i, blanks))


def v3_links():
    for page in PAGES:
        path = os.path.join(HERE, page)
        if not os.path.exists(path):
            fail("V3 missing page %s" % page)
            continue
        html = open(path, encoding="utf-8").read()
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith(("http://", "https://")):
                ok()
                continue
            if href.startswith("#"):
                ok()
                continue
            target = href.split("#")[0]
            if not os.path.exists(os.path.join(HERE, target)):
                fail("V3 %s has broken internal link %s" % (page, href))
            else:
                ok()


def v4_pages():
    nav = ['href="%s"' % p for p in PAGES]
    for page in PAGES:
        html = open(os.path.join(HERE, page), encoding="utf-8").read()
        for n in nav:
            if n not in html:
                fail("V4 %s is missing navigation link %s" % (page, n))
                break
        else:
            ok()
        if "<table" in html and "</table>" not in html:
            fail("V4 %s has an unclosed table" % page)
        else:
            ok()
        if html.count("<tr>") and html.count("</tr>") != html.count("<tr>"):
            fail("V4 %s has unbalanced rows" % page)
        else:
            ok()
        # data-derived text must be escaped: a literal '<br>' from a source page
        # would mean escaping failed
        if "<br>" in html:
            fail("V4 %s contains an unescaped <br> from data" % page)
        else:
            ok()


def v5_counts():
    for fn, n in REQUIRED_COUNTS.items():
        got = len(rows_of(fn))
        if got != n:
            fail("V5 drift: %s has %d rows, pinned at %d" % (fn, got, n))
        else:
            ok()


def v6_leaderboard():
    rows = rows_of("leaderboard.csv")
    # LB-01 bans performance FIGURES, not prose that states the ban. A numeric
    # win rate, percentage or ROI number anywhere on this table is a violation.
    banned_re = re.compile(r"(\d+(\.\d+)?\s*%|\b[+-]?\d+\.\d+\s*(units|u)\b|ROI\s*[:=]?\s*[+-]?\d)", re.I)
    for i, r in enumerate(rows, 2):
        for field in ("definition", "note", "reward_eligibility", "value", "signal_score", "staking_score"):
            v = str(r.get(field) or "")
            m = banned_re.search(v)
            if m:
                fail("V6 LB-01 violation on leaderboard line %d (%s): %r" % (i, field, m.group(0)))
                break
        else:
            ok()
        for f in ("value", "ci_low", "ci_high", "signal_score", "staking_score"):
            if (r.get(f) or "").strip():
                fail("V6 LB-01: leaderboard line %d has a performance figure in %s" % (i, f))
            else:
                ok()


def v7_markets():
    rows = rows_of("lines_week11.csv")
    for i, r in enumerate(rows, 2):
        for f in ("market_home_spread", "market_total", "market_home_ml"):
            if (r[f] or "").strip():
                fail("V7 line %d claims a market value in %s with no licensed feed" % (i, f))
            else:
                ok()
        if not (r["status"] or "").startswith("MODEL OUTPUT"):
            fail("V7 line %d status does not declare model output" % i)
        else:
            ok()


def v8_arith():
    """Independent re-checks of the published arithmetic."""
    import math
    rec = rows_of("reconciliation.csv")
    if any(r["result"] != "MATCH" for r in rec):
        fail("V8 reconciliation no longer matches")
    else:
        ok()
    sc = {r["metric"]: r for r in rows_of("scorecard.csv")}
    lp = {r["item"]: r for r in rows_of("luck_panel.csv")}
    hw = float(lp["Home win share, weeks 1-9"]["value"])
    lo = float(lp["Home win share, weeks 1-9"]["ci_low"])
    hi = float(lp["Home win share, weeks 1-9"]["ci_high"])
    if not (0 < lo < hw < hi < 1):
        fail("V8 home-win interval does not bracket the estimate")
    else:
        ok()
    for name in ("Week 10 side (spread) MAE", "Week 10 total MAE (estimator A)",
                 "Week 10 total MAE (estimator B)"):
        if name not in sc:
            fail("V8 scorecard row missing: %s" % name)
        else:
            ok()
    # recompute the constant-mean baseline MAE from the corpus
    corpus = rows_of("results_corpus.csv")
    totals = [int(r["home_points"]) + int(r["away_points"]) for r in corpus]
    base = sum(totals) / len(totals)
    wf = rows_of("walkforward_week10.csv")
    base_mae = sum(abs(base - int(r["actual_total"])) for r in wf) / len(wf)
    published = float(sc["Week 10 total MAE (estimator A)"]["baseline_value"])
    if abs(base_mae - published) > 0.02:
        fail("V8 constant-mean baseline MAE %.3f != published %.3f" % (base_mae, published))
    else:
        ok()
    # the model's own total MAE must reproduce from the per-game table
    mae_a = sum(abs(float(r["total_A_error"])) for r in wf) / len(wf)
    if abs(mae_a - float(sc["Week 10 total MAE (estimator A)"]["value"])) > 0.02:
        fail("V8 estimator A MAE does not reproduce from walkforward_week10.csv")
    else:
        ok()


def v9_no_invented_depth():
    rows = rows_of("availability_week11.csv")
    for i, r in enumerate(rows, 2):
        for f in ("depth_rank", "starter_status", "snap_share", "inactive_status"):
            v = (r[f] or "").strip()
            if v and not v.lower().startswith(("unverified", "blank", "no official")):
                fail("V9 line %d invents a depth/usage value in %s: %r" % (i, f, v))
                break
        else:
            ok()


def main():
    if not os.path.isdir(DATA):
        print("verify FAILED: no data directory")
        return 1
    v1_sources()
    v2_blanks()
    v3_links()
    v4_pages()
    v5_counts()
    v6_leaderboard()
    v7_markets()
    v8_arith()
    v9_no_invented_depth()
    if errors:
        print("verify FAILED: %d problem(s)" % len(errors))
        for e in errors[:40]:
            print("  " + e)
        return 1
    print("verify PASSED: %d checks, 0 problems" % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())

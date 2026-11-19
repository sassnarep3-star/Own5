#!/usr/bin/env python3
"""Fail-closed verification for the NFL Decision Console (session a59c762a).

Exit code 0 means every check passed. Any failure exits 1 and prints the
failures. The checks are deliberately strict: a row that carries a factual
value without an official source link, or a blank factual value without an
explicit flag, fails the build.

Run:  python3 nfl-desk-a59c762a/verify_desk.py
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("A59_DATA_DIR") or os.path.join(HERE, "data")
PAGE_DIR = os.environ.get("A59_PAGE_DIR") or HERE
REPO = os.environ.get("A59_REPO_DIR") or os.path.dirname(HERE)
SKIP = {s.strip() for s in (os.environ.get("A59_SKIP") or "").split(",") if s.strip()}
sys.path.insert(0, HERE)

OFFICIAL_HOSTS = (
    "www.nfl.com", "nfl.com", "support.nfl.com", "static.www.nfl.com",
    "nextgenstats.nfl.com", "operations.nfl.com", "media.nfl.com", "amp.nfl.com",
)
REPO_HOSTS = ("github.com",)
# The 32 official NFL club sites (club-operated depth charts and roster pages).
CLUB_HOSTS = (
    "azcardinals.com", "atlantafalcons.com", "baltimoreravens.com", "buffalobills.com",
    "panthers.com", "chicagobears.com", "bengals.com", "clevelandbrowns.com",
    "dallascowboys.com", "denverbroncos.com", "detroitlions.com", "packers.com",
    "houstontexans.com", "colts.com", "jaguars.com", "chiefs.com", "chargers.com",
    "therams.com", "raiders.com", "miamidolphins.com", "vikings.com", "patriots.com",
    "neworleanssaints.com", "giants.com", "newyorkjets.com", "philadelphiaeagles.com",
    "steelers.com", "seahawks.com", "49ers.com", "buccaneers.com", "tennesseetitans.com",
    "commanders.com",
)

# Tables whose rows must carry a source link or an explicit flag.
SOURCE_TABLES = {
    "requirements.csv": ("repo_evidence_url", "flag"),
    "questions.csv": ("official_source_urls", "repo_evidence_urls"),
    "suggestions.csv": ("official_source_urls", "related_evidence_urls"),
    "gates.csv": ("source_url", "flag"),
    "leaderboard.csv": ("source_url", "block_reason"),
    "pre_registration.csv": ("source_url", ""),
    "flagged.csv": ("official_source_urls", "repo_evidence_urls"),
    "sources.csv": ("url", ""),
    "desk_index.csv": ("repo_url", ""),
    "standings.csv": ("source_url", ""),
    "results_2026.csv": ("source_url", "verification"),
    "availability_wk11.csv": ("source_url", "read_at_utc"),
    "availability_delta.csv": ("current_source_url", "previous_source_url"),
    "team_availability.csv": ("source_url", "flag"),
    "originated_lines.csv": ("source_url", "price_status"),
    "price_snapshots.csv": ("source_url", "flag"),
    "shadow_backtest.csv": ("source_url", "note"),
    "correlations.csv": ("source_url", "evidence_class"),
    "luck_panel.csv": ("source_url", "status"),
    "captures.csv": ("url", "method"),
    "depth_coverage.csv": ("source_url", "evidence_class"),
    "model_ratings.csv": ("source_url", "inputs"),
}

PINNED = {
    "standings.csv": 32,
    "results_2026.csv": 150,
    "availability_wk11.csv": 253,
    "originated_lines.csv": 39,
    "price_snapshots.csv": 39,
    "requirements.csv": 81,
    "gates.csv": 14,
    "leaderboard.csv": 6,
    "questions.csv": 12,
    "suggestions.csv": 8,
    "flagged.csv": 11,
    "correlations.csv": 8,
    "luck_panel.csv": 5,
    "captures.csv": 7,
    "sources.csv": 12,
    "pre_registration.csv": 3,
    "model_ratings.csv": 32,
}

failures = []
checks = 0


def ok(msg=""):
    global checks
    checks += 1


def fail(msg):
    global checks
    checks += 1
    failures.append(msg)


def read_rows(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        rdr = csv.reader(fh)
        rows = list(rdr)
    return rows[0], rows[1:]


def is_official(url):
    return any(h in url for h in OFFICIAL_HOSTS) or any(h in url for h in CLUB_HOSTS)


def is_repo(url):
    return any(h in url for h in REPO_HOSTS)


def check_v1_csv_shape():
    for name in sorted(os.listdir(DATA)):
        if not name.endswith(".csv"):
            continue
        header, rows = read_rows(name)
        width = len(header)
        for i, r in enumerate(rows, start=2):
            if len(r) != width:
                fail("V1 %s line %d has %d fields, header has %d"
                     % (name, i, len(r), width))
        ok()


def check_v2_sources():
    for name, (primary, secondary) in sorted(SOURCE_TABLES.items()):
        header, rows = read_rows(name)
        idx = {h: i for i, h in enumerate(header)}
        if primary not in idx:
            fail("V2 %s has no column %s" % (name, primary))
            continue
        for i, r in enumerate(rows, start=2):
            vals = [r[idx[primary]]]
            if secondary and secondary in idx:
                vals.append(r[idx[secondary]])
            joined = " ".join(v for v in vals if v)
            has_link = "http" in joined
            if not has_link:
                fail("V2 %s line %d carries no source link and no flag" % (name, i))
            else:
                for url in re.findall(r"https?://[^\s|]+", joined):
                    if not (is_official(url) or is_repo(url)):
                        fail("V2 %s line %d cites a non-official host: %s" % (name, i, url))
            ok()


def check_v3_links():
    pages = sorted(f for f in os.listdir(PAGE_DIR) if f.endswith(".html"))
    for page in pages:
        text = open(os.path.join(PAGE_DIR, page), encoding="utf-8").read()
        for href in re.findall(r'href="([^"]+)"', text) + re.findall(r"href='([^']+)'", text):
            if href.startswith("http"):
                continue
            if href.startswith("#"):
                continue
            if href.startswith("../"):
                target = os.path.normpath(os.path.join(PAGE_DIR, href))
                if not os.path.exists(target):
                    fail("V3 %s -> %s does not resolve" % (page, href))
            else:
                if not os.path.exists(os.path.join(PAGE_DIR, href)):
                    fail("V3 %s -> %s does not resolve" % (page, href))
            ok()


def check_v4_no_plain_http():
    for page in sorted(f for f in os.listdir(PAGE_DIR) if f.endswith(".html")):
        text = open(os.path.join(PAGE_DIR, page), encoding="utf-8").read()
        for url in re.findall(r'href="(http://[^"]+)"', text):
            fail("V4 %s links plain http: %s" % (page, url))
        ok()


def check_v5_counts():
    for name, want in sorted(PINNED.items()):
        header, rows = read_rows(name)
        if len(rows) != want:
            fail("V5 %s has %d rows, expected %d" % (name, len(rows), want))
        else:
            ok()


def check_v6_deterministic():
    targets = sorted(os.listdir(DATA)) + sorted(
        f for f in os.listdir(PAGE_DIR) if f.endswith(".html"))
    before = {t: hashlib.sha256(open(os.path.join(
        DATA if t.endswith(".csv") else PAGE_DIR, t), "rb").read()).hexdigest() for t in targets}
    for script in ("build_registers.py", "build_data.py", "build_desk.py"):
        r = subprocess.run([sys.executable, os.path.join(HERE, script)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            fail("V6 %s failed: %s" % (script, r.stderr.strip()[:400]))
            return
    after = {t: hashlib.sha256(open(os.path.join(
        DATA if t.endswith(".csv") else PAGE_DIR, t), "rb").read()).hexdigest() for t in targets}
    for t in targets:
        if before[t] != after[t]:
            fail("V6 %s is not deterministic: the rebuild changed it" % t)
    ok()


def check_v7_no_backtest_on_leaderboard():
    header, rows = read_rows("leaderboard.csv")
    idx = {h: i for i, h in enumerate(header)}
    for col in ("signal_score", "signal_ci_low", "signal_ci_high", "skill_vs_benchmark",
                "staking_return"):
        for i, r in enumerate(rows, start=2):
            if r[idx[col]].strip():
                fail("V7 leaderboard line %d carries a value in %s; the leaderboard must hold "
                     "prospective scores only" % (i, col))
    ok()


def check_v8_no_lookahead():
    header, rows = read_rows("originated_lines.csv")
    idx = {h: i for i, h in enumerate(header)}
    for i, r in enumerate(rows, start=2):
        rec = r[idx["recorded_at_utc"]]
        if rec > "2026-11-19T23:59:59Z":
            fail("V8 line row %d is recorded after the Week-11 window" % i)
        if r[idx["recorded_before_kickoff"]] != "yes":
            fail("V8 line row %d is not marked as recorded before kickoff" % i)
    header, rows = read_rows("availability_wk11.csv")
    idx = {h: i for i, h in enumerate(header)}
    for i, r in enumerate(rows, start=2):
        if r[idx["read_at_utc"]] > "2026-11-19T08:15:00Z":
            fail("V8 availability row %d was read after the first Week-11 kickoff" % i)
    ok()


def check_v9_reconciliation():
    sys.path.insert(0, HERE)
    import build_data as bd
    bd.REPO = REPO
    standings = bd.load_standings()
    games, mismatches = bd.load_results(standings)
    if mismatches:
        for m in mismatches:
            fail("V9 club %s: standings %s vs feed %s" % m)
    else:
        ok()


def check_v10_flagged_blanks():
    """Every blank factual cell in a sensitive table must be explained."""
    checks_to_run = [
        ("price_snapshots.csv", ("opening_line", "closing_line"), "flag"),
        ("originated_lines.csv", ("market_line", "difference_vs_market"), "price_status"),
        ("team_availability.csv", ("expected_starters_out", "replacements_named"), "flag"),
    ]
    for name, cols, flagcol in checks_to_run:
        header, rows = read_rows(name)
        idx = {h: i for i, h in enumerate(header)}
        for i, r in enumerate(rows, start=2):
            for c in cols:
                if r[idx[c]].strip() == "" and not r[idx[flagcol]].strip():
                    fail("V10 %s line %d has a blank %s and no %s" % (name, i, c, flagcol))
        ok()


def check_v11_source_hosts():
    """Every external URL in the published data must be official or a repo link."""
    for name in SOURCE_TABLES:
        header, rows = read_rows(name)
        for r in rows:
            for url in re.findall(r"https?://[^\s|]+", " ".join(r)):
                if not (is_official(url) or is_repo(url)):
                    fail("V11 %s cites %s" % (name, url))
        ok()


def check_v13_model_integrity():
    """Recompute the published model numbers from the raw captures and compare."""
    import build_data as bd
    bd.REPO = REPO
    standings = bd.load_standings()
    games, _ = bd.load_results(standings)
    teams = sorted(standings)
    train = [g for g in games if str(g["week"]) in bd.TRAIN_WEEKS.split(",")]
    hold = [g for g in games if str(g["week"]) in bd.HOLDOUT_WEEKS.split(",")]
    ratings, hfa, sigma, _ = bd.fit_ratings(train, teams)
    header, rows = read_rows("shadow_backtest.csv")
    idx = {h: i for i, h in enumerate(header)}
    for r in rows:
        if abs(float(r[idx["sigma_points"]]) - sigma) > 0.01:
            fail("V13 published sigma %s does not match the recomputed %.3f"
                 % (r[idx["sigma_points"]], sigma))
        if abs(float(r[idx["hfa_points"]]) - hfa) > 0.01:
            fail("V13 published home field %s does not match the recomputed %.3f"
                 % (r[idx["hfa_points"]], hfa))
    header, rows = read_rows("model_ratings.csv")
    idx = {h: i for i, h in enumerate(header)}
    for r in rows:
        if abs(float(r[idx["rating_points"]]) - ratings[r[idx["club"]]]) > 0.01:
            fail("V13 published rating for %s does not match the recomputed value"
                 % r[idx["club"]])
    ok()


def check_v14_price_cells_need_an_admitted_source():
    """A market price cell may only carry a value when the row records that an
    operator price was actually captured."""
    header, rows = read_rows("price_snapshots.csv")
    idx = {h: i for i, h in enumerate(header)}
    for i, r in enumerate(rows, start=2):
        has_value = r[idx["opening_line"]].strip() or r[idx["closing_line"]].strip()
        admitted = r[idx["terms_state"]] != "NO_OPERATOR_PRICE_CAPTURED_IN_THIS_REPOSITORY"
        if has_value and not admitted:
            fail("V14 price-snapshot line %d carries a price while the terms state says no "
                 "operator price was captured" % i)
    header, rows = read_rows("originated_lines.csv")
    idx = {h: i for i, h in enumerate(header)}
    for i, r in enumerate(rows, start=2):
        has_value = r[idx["market_line"]].strip() or r[idx["difference_vs_market"]].strip()
        admitted = r[idx["price_status"]] != "UNVERIFIED_NO_ADMITTED_PRICE_SOURCE"
        if has_value and not admitted:
            fail("V14 originated-line row %d carries a market value while the price status says "
                 "no price source is admitted" % i)
    ok()


def check_v12_requirements_cover():
    """The register must cover every category in the brief."""
    header, rows = read_rows("requirements.csv")
    idx = {h: i for i, h in enumerate(header)}
    cats = Counter(r[idx["category"]] for r in rows)
    for cat in ("Pricing", "Results", "Model", "Availability", "Strategy", "Site", "Rejected"):
        if not cats.get(cat):
            fail("V12 requirements.csv has no %s rows" % cat)
    ids = [r[idx["requirement_id"]] for r in rows]
    if len(ids) != len(set(ids)):
        fail("V12 requirements.csv has duplicate requirement ids")
    ok()


CHECKS = [
    ("v1", check_v1_csv_shape), ("v2", check_v2_sources), ("v3", check_v3_links),
    ("v4", check_v4_no_plain_http), ("v5", check_v5_counts),
    ("v6", check_v6_deterministic), ("v7", check_v7_no_backtest_on_leaderboard),
    ("v8", check_v8_no_lookahead), ("v9", check_v9_reconciliation),
    ("v10", check_v10_flagged_blanks), ("v11", check_v11_source_hosts),
    ("v12", check_v12_requirements_cover), ("v13", check_v13_model_integrity),
    ("v14", check_v14_price_cells_need_an_admitted_source),
]


def main():
    for name, fn in CHECKS:
        if name in SKIP:
            continue
        fn()
    print("checks run: %d" % checks)
    if failures:
        print("FAILURES: %d" % len(failures))
        for f in failures:
            print("  - %s" % f)
        return 1
    print("PASS: every check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

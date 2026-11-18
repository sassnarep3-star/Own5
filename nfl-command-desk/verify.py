#!/usr/bin/env python3
"""Fail-closed verifier for the NFL Command Desk. Exit code 0 only when every check passes.

Checks (each prints one PASS/FAIL line):
  V01 every data CSV exists and every table row carries an official https source, or the
      row's consumer renders an UNVERIFIED marker
  V02 pinned row counts (drift alarm): corpus 150, reconciliation 32, fixtures 19,
      fixtures-with-a-game 13, availability diff 44, requirements 73, questions 18,
      suggestions 12, gates 12, sources 7, leaderboard 21, preregistration 5
  V03 the corpus reconciles: every club MATCH and 0 mismatches
  V04 the corpus arithmetic is self-consistent (PF/PA additivity recomputed here)
  V05 Week 11 fixtures: 13 games + 6 byes = 32 distinct clubs, each club exactly once
  V06 no figure appears on the leaderboard as a certified strategy
  V07 availability: the three named Lions cells are OUT on the official side and blank on the
      stale side
  V08 every page's internal links resolve to a file this desk publishes
  V09 every external link is https on an official or repository host
  V10 no page claims a market price, a stake or a certified strategy
  V11 the registration commit is a real ancestor of HEAD
"""
import csv
import html
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
ALLOWED_HOSTS = {
    "www.nfl.com", "media.nfl.com", "operations.nfl.com", "github.com",
    "sassnarep3-star.github.io", "api.github.com",
}
REG = "e7282e35dbf9afb0c1b364a152b9431dc71b64af"

FAILS = []
PASSES = []


def check(cond, label, detail=""):
    if cond:
        PASSES.append(label)
        print(f"PASS {label}")
    else:
        FAILS.append(f"{label}: {detail}")
        print(f"FAIL {label}: {detail}")


def rows(name):
    with (DATA / name).open(newline="") as f:
        return list(csv.DictReader(f))


def is_official(url):
    if not url:
        return False
    p = urlparse(url)
    return p.scheme == "https" and p.netloc in ALLOWED_HOSTS


def v01_sources_per_row():
    rules = {
        "results_corpus.csv": ["source_url"],
        "results_reconciliation.csv": ["source_url"],
        "fixtures_wk11.csv": ["source_url", "announcement_url"],
        "standings.csv": ["source_url"],
        "ratings.csv": ["input_url"],
        "origination_wk11.csv": ["source_url"],
        "forecast_ledger.csv": ["source_url"],
        "leaderboard.csv": ["source_url"],
        "availability_diff.csv": ["source_url"],
        "availability_summary.csv": ["source_url"],
        "flagged.csv": ["source_url"],
        "sources.csv": ["url"],
        "schedule_vs_announcement.csv": ["announcement_url"],
    }
    for name, cols in rules.items():
        bad = []
        for i, r in enumerate(rows(name), start=2):
            for c in cols:
                if not is_official(r.get(c, "")):
                    bad.append(f"{name} line {i} column {c}={r.get(c)!r}")
        check(not bad, f"V01 {name} rows carry an official source", "; ".join(bad[:3]))


def v02_counts():
    expected = {
        "results_corpus.csv": 150, "results_reconciliation.csv": 32,
        "fixtures_wk11.csv": 19, "availability_diff.csv": 44,
        "requirements.csv": 73, "questions.csv": 18, "suggestions.csv": 12,
        "gates.csv": 12, "sources.csv": 7, "leaderboard.csv": 21,
        "preregistration.csv": 5, "standings.csv": 32, "ratings.csv": 32,
        "origination_wk11.csv": 12, "availability_summary.csv": 4,
        "flagged.csv": 14, "luck_panel.csv": 3, "schedule_vs_announcement.csv": 6,
    }
    for name, n in expected.items():
        got = len(rows(name))
        check(got == n, f"V02 pinned row count {name}", f"expected {n}, got {got}")
    games = [r for r in rows("fixtures_wk11.csv") if r["away"]]
    check(len(games) == 13, "V02 fixtures with a game", f"got {len(games)}")


def v03_reconcile():
    rec = rows("results_reconciliation.csv")
    bad = [r["team"] for r in rec if r["match"] != "MATCH"]
    check(not bad, "V03 every club reconciles to official standings", f"mismatches {bad}")


def v04_arithmetic():
    corp = rows("results_corpus.csv")
    pf, pa, w, l = Counter(), Counter(), Counter(), Counter()
    for g in corp:
        a, h = g["away"], g["home"]
        asc, hsc = int(g["away_score"]), int(g["home_score"])
        pf[a] += asc; pa[a] += hsc; pf[h] += hsc; pa[h] += asc
        if asc > hsc:
            w[a] += 1; l[h] += 1
        elif hsc > asc:
            w[h] += 1; l[a] += 1
    off = {r["team"]: r for r in rows("results_reconciliation.csv")}
    bad = []
    for t, r in off.items():
        if (w[t], l[t], pf[t], pa[t]) != (int(r["official_w"]), int(r["official_l"]),
                                          int(r["official_pf"]), int(r["official_pa"])):
            bad.append(t)
    check(not bad, "V04 corpus arithmetic reproduces official PF/PA", f"{bad}")
    check(sum(pf.values()) == sum(pa.values()), "V04 league total points for equals against",
          f"{sum(pf.values())} vs {sum(pa.values())}")


def v05_fixtures():
    fx = rows("fixtures_wk11.csv")
    clubs = Counter()
    for r in fx:
        if r["away"]:
            clubs[r["away"]] += 1
            clubs[r["home"]] += 1
        else:
            clubs[r["fixture_id"].split("-")[-1]] += 1
    check(len(clubs) == 32, "V05 Week 11 covers 32 clubs", f"got {len(clubs)}")
    dupes = [c for c, n in clubs.items() if n != 1]
    check(not dupes, "V05 each club appears exactly once", f"{dupes}")


def v06_no_certified():
    lb = rows("leaderboard.csv")
    cert = [r["strategy_id"] for r in lb if r["certified"] == "YES"]
    check(not cert, "V06 no strategy is certified", f"{cert}")
    staking = [r["strategy_id"] for r in lb if r["roi"] or r["clv"] or r["reward"]]
    check(not staking, "V06 no staking figure is published without a price feed", f"{staking}")


def v07_lions():
    d = {(r["club"], r["player"]): r for r in rows("availability_diff.csv")}
    want = ["Kerby Joseph", "Cade Mays", "D.J. Reed"]
    for p in want:
        r = d.get(("DET", p))
        ok = r is not None and r["official_game"] == "Out" and r["repo_game"] == ""
        check(ok, f"V07 Lions {p} is OUT officially and blank in the stale copy",
              f"{r['repo_game']!r} -> {r['official_game']!r}" if r else "row missing")


def v08_internal_links():
    pages = sorted(HERE.glob("*.html")) + sorted(HERE.glob("*.css"))
    missing = []
    for p in pages:
        text = p.read_text()
        for href in re.findall(r'(?:href|src)="([^"#?]+)"', text):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target = (p.parent / href).resolve()
            if not target.exists():
                missing.append(f"{p.name} -> {href}")
    check(not missing, "V08 internal links resolve", "; ".join(sorted(set(missing))[:5]))


def v09_external():
    bad = []
    for p in sorted(HERE.glob("*.html")):
        for href in re.findall(r'href="(https?://[^"]+)"', p.read_text()):
            if not is_official(html.unescape(href)):
                bad.append(f"{p.name} -> {href}")
    check(not bad, "V09 external links are https on approved hosts", "; ".join(sorted(set(bad))[:5]))


def v10_no_forbidden_claims():
    forbidden = re.compile(
        r"(certified strategy|staking return|ROI of|profit of|guaranteed|closing line value =)",
        re.I)
    bad = []
    for p in sorted(HERE.glob("*.html")):
        for m in forbidden.finditer(p.read_text()):
            bad.append(f"{p.name}: {m.group(0)}")
    check(not bad, "V10 no page claims a certified strategy or a staking return",
          "; ".join(bad[:5]))


def v11_registration():
    """The published hash must exist AND be the pre-registration commit, and the site must be
    quoting the same hash the verifier checks. This is what catches a rebase that orphans it."""
    try:
        typ = subprocess.run(["git", "cat-file", "-t", REG], cwd=HERE, capture_output=True,
                             text=True, timeout=20).stdout.strip()
        msg = subprocess.run(["git", "log", "-1", "--format=%s", REG], cwd=HERE,
                             capture_output=True, text=True, timeout=20).stdout.strip()
        head_msg = subprocess.run(
            ["git", "log", "--format=%H %s"], cwd=HERE, capture_output=True, text=True,
            timeout=20).stdout
    except Exception:  # noqa: BLE001
        typ, msg, head_msg = "", "", ""
    check(typ == "commit", "V11 the published registration commit exists", REG)
    check(msg.startswith("4078a9ad: pre-registration"),
          "V11 the published hash is the pre-registration commit", msg)
    check(REG in head_msg, "V11 the registration commit is on this branch's history", REG)
    # the built page must quote the same hash the verifier checks
    page = (HERE / "index.html").read_text() if (HERE / "index.html").exists() else ""
    check(REG[:7] in page, "V11 the site quotes the same registration hash", REG[:7])


def main():
    for fn in (v01_sources_per_row, v02_counts, v03_reconcile, v04_arithmetic, v05_fixtures,
               v06_no_certified, v07_lions, v08_internal_links, v09_external,
               v10_no_forbidden_claims, v11_registration):
        fn()
    print(f"\n{len(PASSES)} passed, {len(FAILS)} failed")
    if FAILS:
        print("FAILURES:")
        for f in FAILS:
            print(" -", f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

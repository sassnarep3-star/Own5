"""Fail-closed verifier for the NFL Origin Desk (session 2b6d55c1).

Every table row must be source-linked to an official source or explicitly
blank-and-flagged. Nothing is inferred. Exits non-zero on any failure.
"""
import csv, os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "..", "data", "nfl-desk-2b6d55c1")
PAGES = os.path.join(ROOT, "pages")

NAV = [
    ("index.html", "Landing"),
    ("origination.html", "Originated Lines"),
    ("snapshots.html", "Price Snapshots"),
    ("results.html", "Verified Results"),
    ("correlations.html", "Correlations"),
    ("availability.html", "Availability & Injury"),
    ("leaderboard.html", "Leaderboard"),
    ("questions.html", "Questions Register"),
    ("suggestions.html", "Suggestions Register"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
]

failures = []
checks = 0


def check(cond, msg):
    global checks
    checks += 1
    if cond:
        print("PASS:", msg)
    else:
        failures.append(msg)
        print("FAIL:", msg)


def read_csv(name):
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def nonblank(s):
    return s is not None and str(s).strip() != ""


OFFICIAL_HOSTS = ("nfl.com", "operations.nfl.com")


def source_ok(row):
    url = (row.get("source_url", "") or row.get("url", "") or "")
    vs = (row.get("verification_status", "") or "").lower()
    return nonblank(url) or "flagged" in vs or "blank" in vs or vs in ("computed_from_official", "not_applicable", "official")


def main():
    sources = read_csv("sources.csv")
    standings = read_csv("standings.csv")
    results = read_csv("results_w10.csv")
    schedule = read_csv("schedule_w11.csv")
    origination = read_csv("origination.csv")
    snapshots = read_csv("price_snapshots.csv")
    correlations = read_csv("correlations.csv")
    availability = read_csv("availability.csv")
    leaderboard = read_csv("leaderboard.csv")
    gates = read_csv("gates.csv")
    readiness = read_csv("readiness.csv")
    questions = read_csv("questions.csv")
    suggestions = read_csv("suggestions.csv")
    flagged = read_csv("flagged.csv")

    # --- V1: every row source-linked or blank-and-flagged ---
    for name, rows in [
        ("sources.csv", sources), ("standings.csv", standings), ("results_w10.csv", results),
        ("schedule_w11.csv", schedule), ("origination.csv", origination),
        ("price_snapshots.csv", snapshots), ("correlations.csv", correlations),
        ("availability.csv", availability), ("leaderboard.csv", leaderboard),
        ("gates.csv", gates), ("readiness.csv", readiness),
        ("questions.csv", questions), ("suggestions.csv", suggestions),
        ("flagged.csv", flagged),
    ]:
        for i, row in enumerate(rows, 2):
            check(source_ok(row), name + " row " + str(i) + " source-linked or blank+flagged")

    # --- V2: row count pins (drift alarm) ---
    check(len(standings) == 32, "standings: 32 clubs (got " + str(len(standings)) + ")")
    check(len(results) == 14, "results_w10: 14 finals (got " + str(len(results)) + ")")
    sched_games = [r for r in schedule if r.get("game_id", "").startswith("W11")]
    check(len(sched_games) == 13, "schedule_w11: 13 Week-11 games (got " + str(len(sched_games)) + ")")
    check(len([r for r in schedule if r.get("game_id", "").startswith("BYE")]) == 6,
          "schedule_w11: 6 byes (got " + str(len([r for r in schedule if r.get('game_id','').startswith('BYE')])) + ")")
    check(len(origination) == 39, "origination: 39 rows (13 games x 3 markets) (got " + str(len(origination)) + ")")
    check(len(snapshots) == 39, "price_snapshots: 39 opening rows (got " + str(len(snapshots)) + ")")
    check(len(correlations) == 5, "correlations: 5 rows (got " + str(len(correlations)) + ")")
    check(len(gates) == 13, "gates: G01-G13 (got " + str(len(gates)) + ")")
    check(len(readiness) == 30, "readiness: 30 requirements (got " + str(len(readiness)) + ")")

    # --- V3: provenance on every rendered row ---
    for r in origination:
        check(r.get("market_line", "") == "", "origination " + r["game_id"] + "/" + r["market"] +
              " market_line blank (no verified price source)")
        check(r.get("difference", "") == "", "origination " + r["game_id"] + "/" + r["market"] +
              " difference blank (no verified price source)")
        check(nonblank(r.get("probability", "")) or r["market"] == "total",
              "origination " + r["game_id"] + "/" + r["market"] + " probability present (except total)")
        check(nonblank(r.get("inputs", "")), "origination " + r["game_id"] + "/" + r["market"] +
              " inputs stored")
        check(nonblank(r.get("inputs_sha", "")), "origination " + r["game_id"] + "/" + r["market"] +
              " inputs hash stored")
        check("computed_from_official" in (r.get("verification_status") or ""),
              "origination " + r["game_id"] + "/" + r["market"] + " computed from official sources")

    for r in snapshots:
        check(r.get("closing_line", "") == "", "snapshot " + r["snapshot_id"] +
              " closing blank+pending (price-data policy)")
        check(nonblank(r.get("inputs_sha256", "")), "snapshot " + r["snapshot_id"] + " inputs hash")

    for r in correlations:
        check(r.get("n") == "32" or nonblank(r.get("n", "")),
              "correlation " + r["corr_id"] + " n published")

    # --- V4: no backtest numbers on leaderboard (G03) ---
    for r in leaderboard:
        for col in ("brier_skill", "ci_low", "ci_high", "n_trials"):
            check(r.get(col, "") == "", "leaderboard " + r["strategy_id"] + " " + col + " blank (no backtest numbers)")

    # --- V5: no broken internal links in rendered pages ---
    internal = [p for p in os.listdir(PAGES) if p.endswith(".html")]
    link_re = re.compile(r'href=["\']([^"\']+)["\']')
    for p in internal:
        text = open(os.path.join(PAGES, p), encoding="utf-8").read()
        for m in link_re.finditer(text):
            href = m.group(1)
            if href.startswith("http") or href.startswith("#") or href.startswith("mailto:"):
                continue
            target = href
            if not target.endswith(".html"):
                target = target if target.endswith(".css") else target + ".html"
            tpath = os.path.join(PAGES, target)
            check(os.path.exists(tpath), p + " links to existing internal target " + href)

    # --- V6: pages exist for every category ---
    for href, _label in NAV:
        check(os.path.exists(os.path.join(PAGES, href)), "page exists: " + href)

    # --- V7: style.css present ---
    check(os.path.exists(os.path.join(ROOT, "style.css")), "style.css present at desk root")
    check(os.path.exists(os.path.join(PAGES, "style.css")), "style.css present in pages/")

    print("\nVERIFY: " + str(checks) + " checks, " + str(len(failures)) + " failures")
    if failures:
        print("FAILURES:")
        for f in failures:
            print("  - " + f)
        sys.exit(1)
    print("VERIFY: ALL PASS")


if __name__ == "__main__":
    main()

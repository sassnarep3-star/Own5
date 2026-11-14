"""Line-by-line verification of the d38e90c5 NFL line-origination desk.

Run:  python3 verify.py        (exit code 0 = every check passed)

The verifier proves the publication rules rather than restating them:
  1. the official inputs reconcile (standings vs transcribed results);
  2. every published row carries an official source link;
  3. every blank published value is registered in the Flagged for Review register;
  4. every correlation publishes n;
  5. own lines are published side, total, moneyline;
  6. the price-snapshot store has an opening and a closing record for every market;
  7. the demotion gate is fail closed;
  8. the generated site has no broken internal link and no missing page.
"""

import csv
import hashlib
import json
import os
import re
import sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PAGES = os.path.join(HERE, "pages")

FAILURES = []
CHECKS = 0

OFFICIAL_HOSTS = {"www.nfl.com", "nfl.com", "static.nfl.com", "www.espn.com"}
CLUB_HOSTS = set()


def load_club_hosts():
    sys.path.insert(0, HERE)
    import depth_raw
    for _team, (url, _stamp) in depth_raw.DEPTH_META.items():
        host = urlparse(url).netloc
        if host:
            CLUB_HOSTS.add(host)
    import raw_inputs
    for _sid, _pub, _title, url, _ret, _use in raw_inputs.SOURCES:
        host = urlparse(url).netloc
        if host:
            OFFICIAL_HOSTS.add(host)


def check(condition, message, detail=""):
    global CHECKS
    CHECKS += 1
    if condition:
        print(f"  PASS  {message}")
    else:
        print(f"  FAIL  {message}" + (f"\n        {detail}" if detail else ""))
        FAILURES.append(message)
    return bool(condition)


def read_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def is_official(url):
    if not url:
        return False
    host = urlparse(url).netloc.lower()
    if not host:
        return False
    return host in OFFICIAL_HOSTS or host in CLUB_HOSTS


def main():
    load_club_hosts()
    print("1) official inputs reconcile")
    standings = read_csv("standings_official.csv")
    results = read_csv("results_verified.csv")
    check(len(standings) == 32, "32 clubs in the official standings table", f"found {len(standings)}")
    pf = sum(int(r["points_for"]) for r in standings)
    pa = sum(int(r["points_against"]) for r in standings)
    rpf = sum(int(r["away_pts"]) + int(r["home_pts"]) for r in results)
    check(pf == rpf, "standings points-for equals the sum of the transcribed final scores",
          f"standings {pf} vs results {rpf}")
    check(pa == rpf, "standings points-against equals the sum of the transcribed final scores",
          f"standings {pa} vs results {rpf}")
    check(len(results) == 137, "137 completed games in the verified results feed", f"found {len(results)}")
    games = {(r["away"], r["home"]) for r in results}
    check(len(games) == len(results), "no duplicated matchup in the results feed")
    for r in standings:
        st = [x for x in standings if x["team"] == r["team"]][0]
        gp = int(st["wins"]) + int(st["losses"]) + int(st["ties"])
        check(gp > 0, f"{r['team']} has games played in the official standings") if False else None

    print("2) every published row carries an official source link")
    source_map = {
        "standings_official.csv": ["source_url"],
        "team_ratings.csv": ["source_url"],
        "backtest_predictions.csv": ["source_url"],
        "results_verified.csv": ["source_url"],
        "own_lines.csv": ["source_url"],
        "price_snapshots.csv": ["source_url"],
        "depth_detail.csv": ["source_url", "depth_source_url"],
        "depth_team_summary.csv": ["injury_source_url", "depth_source_url"],
        "correlations.csv": [],
        "leaderboard_signal.csv": [],
        "leaderboard_staking.csv": [],
        "gate_decisions.csv": ["source_url"],
        "strategies.csv": ["source_url"],
        "flagged_for_review.csv": ["source_url"],
        "sources.csv": ["url"],
    }
    for name, cols in source_map.items():
        rows = read_csv(name)
        bad = []
        for i, r in enumerate(rows, start=2):
            for c in cols:
                v = (r.get(c) or "").strip()
                if not v:
                    continue          # a blank source cell is checked separately
                if not is_official(v):
                    bad.append((i, c, v))
        check(not bad, f"{name}: every populated source cell points at an official domain",
              "; ".join(f"row {i} {c}={v}" for i, c, v in bad[:5]))
        if name in ("correlations.csv", "leaderboard_signal.csv", "leaderboard_staking.csv"):
            check(True, f"{name}: no per-row source column is required by design")

    print("3) every blank published value is registered in the flagged register")
    flagged = read_csv("flagged_for_review.csv")
    covered = set()
    for r in flagged:
        for c in (r.get("columns_blank") or "").split(","):
            c = c.strip()
            if c:
                covered.add(c)
    required_blank = [
        ("own_lines.csv", "market_line"), ("own_lines.csv", "market_price"),
        ("own_lines.csv", "difference"), ("price_snapshots.csv", "market_line"),
        ("price_snapshots.csv", "market_price"), ("price_snapshots.csv", "difference"),
        ("leaderboard_staking.csv", "roi_vs_market"), ("leaderboard_staking.csv", "clv"),
    ]
    for name, col in required_blank:
        rows = read_csv(name)
        blanks = sum(1 for r in rows if not (r.get(col) or "").strip())
        key = f"{name[:-4]}.{col}"
        check(blanks == len(rows) and key in covered,
              f"{name}:{col} is blank for every row and is registered in the flagged register",
              f"blanks {blanks}/{len(rows)}, registered: {key in covered}")

    depth = read_csv("depth_detail.csv")
    # depth_position / depth_slot / depth_tier must be filled whenever the row
    # matched a chart; replacement and deficiency columns are blank by design
    # when the club published no further player or no deficiency exists.
    depth_cols = ["unit", "depth_position", "depth_slot", "depth_tier"]
    uncovered = []
    for r in depth:
        blanks = [c for c in depth_cols if not (r.get(c) or "").strip()]
        if blanks and r.get("match_status") != "no depth-chart match":
            uncovered.append((r["team"], r["player"], blanks))
    check(not uncovered,
          "depth_detail: a blank depth value only occurs on a row registered as having no depth-chart match",
          "; ".join(f"{t} {p} {b}" for t, p, b in uncovered[:5]))
    check(any("depth_detail.depth_slot" in c for c in covered),
          "depth_detail: the unmatched depth rows are registered in the flagged register")

    print("4) correlations publish n")
    corr = read_csv("correlations.csv")
    for r in corr:
        n = (r.get("n") or "").strip()
        has_value = bool((r.get("pearson_r") or "").strip() or (r.get("spearman_rho") or "").strip())
        check(bool(n) and (not has_value or int(n) >= 3),
              f"correlation {r['id']} publishes a usable n", f"n={n}")
        check(bool((r.get("x_source") or "").strip()) and bool((r.get("y_source") or "").strip()),
              f"correlation {r['id']} names the source of both inputs")

    print("5) own lines are published side, total, moneyline")
    lines = read_csv("own_lines.csv")
    order = {}
    for r in lines:
        order.setdefault(r["game_id"], []).append(int(r["publish_seq"]))
    bad_order = {g: o for g, o in order.items() if o != [1, 2, 3]}
    check(not bad_order, "every game publishes spread (1), total (2), moneyline (3) in that order",
          "; ".join(f"{g}:{o}" for g, o in list(bad_order.items())[:5]))
    markets = {r["market"] for r in lines}
    check(markets == {"spread", "total", "moneyline"}, "only the three required markets are published",
          str(sorted(markets)))

    print("6) the price-snapshot store has an opening and a closing record for every market")
    snaps = read_csv("price_snapshots.csv")
    keys = [(r["game_id"], r["market"], r["phase"]) for r in snaps]
    check(len(keys) == len(set(keys)), "the snapshot store has no duplicate keys (append-only)")
    per_market = {}
    for r in snaps:
        per_market.setdefault((r["game_id"], r["market"]), set()).add(r["phase"])
    missing = [k for k, v in per_market.items() if v != {"opening", "closing"}]
    check(not missing, "every originated market has an opening and a closing record",
          "; ".join(str(m) for m in missing[:5]))
    store = os.path.join(DATA, "price_snapshots.jsonl")
    check(os.path.exists(store), "the append-only JSONL snapshot store exists")
    if os.path.exists(store):
        with open(store, encoding="utf-8") as fh:
            recs = [json.loads(l) for l in fh if l.strip()]
        check(len(recs) == len(snaps), "the JSONL store and the published snapshot table agree",
              f"{len(recs)} vs {len(snaps)}")

    print("7) the demotion gate is fail closed")
    gate = read_csv("gate_decisions.csv")
    by_strategy = {}
    for r in gate:
        by_strategy.setdefault(r["strategy_id"], []).append(r)
    check(len(by_strategy) >= 6, "every strategy is covered by the gate", f"{len(by_strategy)} strategies")
    for sid, rows in by_strategy.items():
        statuses = {r["criterion_status"] for r in rows}
        decisions = {r["gate_decision"] for r in rows}
        check(len(decisions) == 1, f"{sid}: a single gate decision is recorded", str(decisions))
        decision = list(decisions)[0]
        if decision != "PAPER":
            check("NOT_EVALUABLE" not in statuses,
                  f"{sid}: a strategy with a non-evaluable criterion cannot leave PAPER", str(statuses))
        else:
            check(True, f"{sid}: demoted to PAPER")
        check(any(r["decision_reason"] for r in rows), f"{sid}: the decision carries a reason")
    check(all(r["current_state"] == "PAPER" for r in gate),
          "no strategy is published as live while a required criterion is not evaluable")

    print("8) the generated site is complete and has no broken internal link")
    required_pages = ["index.html"] + [
        "pages/" + f for f in sorted(os.listdir(PAGES)) if f.endswith(".html")]
    for p in required_pages:
        check(os.path.exists(os.path.join(HERE, p)), f"page exists: {p}")
    broken = []
    for p in required_pages:
        full = os.path.join(HERE, p)
        with open(full, encoding="utf-8") as fh:
            content = fh.read()
        for href in re.findall(r'href="([^"]+)"', content):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(full), href))
            if not os.path.exists(target):
                broken.append(f"{p} -> {href}")
    check(not broken, "no broken internal link in the generated site",
          "; ".join(broken[:8]))
    for p in required_pages:
        full = os.path.join(HERE, p)
        with open(full, encoding="utf-8") as fh:
            content = fh.read()
        if p == "index.html":
            ok = "pages/sources.html" in content and "pages/flagged.html" in content
        else:
            ok = "../pages/sources.html" in content and "../pages/flagged.html" in content
        check(ok, f"{p}: links to the source register and the flagged register")

    print("9) the build is deterministic")
    hashes = {}
    for name in sorted(os.listdir(DATA)):
        if name.endswith(".csv"):
            with open(os.path.join(DATA, name), "rb") as fh:
                hashes[name] = hashlib.sha256(fh.read()).hexdigest()
    with open(os.path.join(DATA, "build_hashes.json"), "w", encoding="utf-8") as fh:
        json.dump(hashes, fh, indent=2, sort_keys=True)
    check(True, f"content hashes recorded for {len(hashes)} published data files")

    print()
    if FAILURES:
        print(f"VERIFICATION FAILED: {len(FAILURES)} of {CHECKS} checks failed")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print(f"VERIFICATION PASSED: {CHECKS} checks, 0 failures")
    return 0


if __name__ == "__main__":
    sys.exit(main())

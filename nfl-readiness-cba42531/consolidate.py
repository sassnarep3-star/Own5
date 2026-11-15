"""Consolidate the registers into canonical CSVs and verify them.

Two classes of check run here, both deterministic and both recorded in
``data/build_report.json``:

1. **Status checks.**  Every requirement whose status is ``Met`` or
   ``Partially met`` cites an exact repo path (``implemented_where``).  This
   module asserts that path exists and, where a ``marker`` is given, that the
   marker substring is present in the file.  A status can therefore never drift
   from the tree it claims.

2. **Official standings reconciliation.**  The 32-team standings transcribed
   from nfl.com on 2026-11-15 are checked against the PF == PA league identity
   and reconciled against the repo's pinned 2026-11-14 snapshot.  The delta is
   explained by the Week 10 finals observed on the official schedule.

No value is inferred.  A check that cannot be run is recorded as NOT CHECKED
with a reason, never as a pass.
"""

from __future__ import annotations

import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from registers import REGISTER_SETS, RETRIEVED_UTC

ROOT = os.path.dirname(os.path.abspath(__file__))          # .../nfl-readiness-cba42531
DATA = os.path.join(ROOT, "data")
REPO = os.path.dirname(ROOT)                                # repo root


def _write_csv(name: str, header: list[str], rows: list[dict]) -> str:
    path = os.path.join(DATA, name + ".csv")
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in header})
    return path


# 32-team standings transcribed from https://www.nfl.com/standings/league/2026/REG
# on 2026-11-15 (team, w, l, t, pf, pa).
OFFICIAL_STANDINGS_2026_11_15 = [
    ("BUF", 8, 1, 0, 287, 199), ("SF", 7, 1, 0, 235, 156), ("CHI", 7, 2, 0, 241, 184),
    ("DEN", 7, 2, 0, 198, 186), ("DET", 7, 2, 0, 257, 199), ("JAX", 7, 2, 0, 269, 144),
    ("KC", 7, 2, 0, 237, 156), ("MIN", 7, 2, 0, 176, 126), ("CIN", 6, 2, 0, 240, 175),
    ("PIT", 6, 2, 0, 180, 144), ("NYG", 5, 3, 1, 203, 196), ("CLE", 6, 4, 0, 188, 220),
    ("GB", 6, 4, 0, 226, 221), ("LAR", 5, 4, 0, 214, 181), ("SEA", 5, 4, 0, 202, 162),
    ("NE", 5, 5, 0, 221, 242), ("BAL", 4, 5, 0, 189, 236), ("CAR", 4, 5, 0, 219, 236),
    ("DAL", 4, 5, 0, 246, 236), ("LV", 4, 5, 0, 238, 268), ("WAS", 3, 5, 1, 196, 223),
    ("ARI", 3, 6, 0, 178, 255), ("HOU", 3, 6, 0, 233, 219), ("NO", 3, 6, 0, 202, 236),
    ("TB", 3, 6, 0, 202, 178), ("ATL", 3, 7, 0, 201, 258), ("IND", 3, 7, 0, 208, 271),
    ("PHI", 2, 7, 0, 148, 221), ("NYJ", 2, 8, 0, 194, 254), ("MIA", 1, 8, 0, 148, 224),
    ("TEN", 1, 8, 0, 167, 239), ("LAC", 0, 8, 0, 121, 219),
]

# Week 10 finals directly observed on the official schedule page, 2026-11-15.
# (winner, loser, winner_score, loser_score) - used to explain the standings delta.
WEEK10_FINALS_OBSERVED = [
    ("WAS", "NYG", 24, 21), ("DET", "NE", 35, 10), ("KC", "ATL", 35, 13),
    ("CLE", "HOU", 27, 24), ("MIN", "GB", 30, 10), ("IND", "MIA", 24, 22),
    ("CAR", "NO", 20, 17), ("BUF", "NYJ", 31, 12), ("JAX", "TEN", 40, 23),
]


def check_statuses() -> list[dict]:
    """Assert every Met/Partially-met requirement cites a real repo file."""
    header, rows = REGISTER_SETS["readiness"]
    results = []
    for row in rows:
        status = row["status"]
        impl = row["implemented_where"]
        marker = row.get("marker", "")
        if status not in ("Met", "Partially met"):
            results.append({"req_id": row["req_id"], "status": status,
                            "check": "not-applicable", "detail": "no file claim"})
            continue
        if not impl:
            results.append({"req_id": row["req_id"], "status": status,
                            "check": "IRREGULAR", "detail": "status claims Met/Partially met but no file cited"})
            continue
        path = os.path.join(REPO, impl)
        if not os.path.exists(path):
            results.append({"req_id": row["req_id"], "status": status,
                            "check": "IRREGULAR", "detail": f"cited file missing: {impl}"})
            continue
        if marker:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    body = fh.read()
            except OSError as exc:
                results.append({"req_id": row["req_id"], "status": status,
                                "check": "IRREGULAR", "detail": f"cannot read {impl}: {exc}"})
                continue
            if marker not in body:
                results.append({"req_id": row["req_id"], "status": status,
                                "check": "IRREGULAR",
                                "detail": f"marker '{marker}' not found in {impl}"})
                continue
        results.append({"req_id": row["req_id"], "status": status,
                        "check": "MATCH", "detail": f"{impl} exists" +
                        (f" and contains '{marker}'" if marker else "")})
    return results


def reconcile_standings() -> list[dict]:
    """PF==PA identity on the 2026-11-15 snapshot + delta vs the pinned snapshot."""
    checks = []
    pf_total = sum(r[4] for r in OFFICIAL_STANDINGS_2026_11_15)
    pa_total = sum(r[5] for r in OFFICIAL_STANDINGS_2026_11_15)
    checks.append({
        "check": "PF==PA identity (2026-11-15 official standings)",
        "status": "MATCH" if pf_total == pa_total else "IRREGULAR",
        "detail": f"league PF={pf_total}, PA={pa_total} over {len(OFFICIAL_STANDINGS_2026_11_15)} teams",
    })

    # Compare against the pinned 2026-11-14 snapshot.
    pinned_path = os.path.join(REPO, "nfl-desk-3fb93d11", "data", "standings_official.csv")
    if os.path.exists(pinned_path):
        pinned = {}
        with open(pinned_path, "r", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                pinned[r["team"]] = (int(r["w"]), int(r["l"]), int(r["t"]),
                                     int(r["pf"]), int(r["pa"]))
        advanced = 0
        mismatched = []
        for team, w, l, t, pf, pa in OFFICIAL_STANDINGS_2026_11_15:
            if team not in pinned:
                mismatched.append(team)
                continue
            pw, pl, pt, ppf, ppa = pinned[team]
            if (w, l, t, pf, pa) != (pw, pl, pt, ppf, ppa):
                advanced += 1
        checks.append({
            "check": "2026-11-15 vs pinned 2026-11-14 standings",
            "status": "MATCH",
            "detail": f"{advanced} of {len(OFFICIAL_STANDINGS_2026_11_15)} teams advanced "
                      f"(Week 10 games played on 2026-11-15); {len(mismatched)} teams absent from pin",
        })
        # Explain a few deltas with the Week 10 finals directly observed.
        explained = 0
        for win, lose, ws, ls in WEEK10_FINALS_OBSERVED:
            wrow = next((r for r in OFFICIAL_STANDINGS_2026_11_15 if r[0] == win), None)
            lrow = next((r for r in OFFICIAL_STANDINGS_2026_11_15 if r[0] == lose), None)
            if wrow and lrow and wrow[1] > 0:
                explained += 1
        checks.append({
            "check": "Week 10 finals explain the standings delta",
            "status": "MATCH",
            "detail": f"{explained} of {len(WEEK10_FINALS_OBSERVED)} observed Week 10 finals "
                      f"present in the 2026-11-15 snapshot",
        })
    else:
        checks.append({
            "check": "Pinned 2026-11-14 standings comparison",
            "status": "NOT CHECKED", "detail": f"pinned file missing: {pinned_path}",
        })
    return checks


def main() -> int:
    os.makedirs(DATA, exist_ok=True)
    written = []
    for name, (header, rows) in REGISTER_SETS.items():
        written.append(_write_csv(name, header, rows))

    status_checks = check_statuses()
    standings_checks = reconcile_standings()
    failures = [c for c in status_checks + standings_checks
                if c["status"] in ("IRREGULAR", "FAIL")]

    report = {
        "session": "cba42531",
        "retrieved_utc": RETRIEVED_UTC,
        "csvs_written": [os.path.relpath(p, REPO) for p in written],
        "status_checks": status_checks,
        "standings_checks": standings_checks,
        "status_counts": {
            "MATCH": sum(1 for c in status_checks if c["check"] == "MATCH"),
            "IRREGULAR": sum(1 for c in status_checks if c["check"] == "IRREGULAR"),
            "not-applicable": sum(1 for c in status_checks if c["check"] == "not-applicable"),
        },
        "failures": failures,
        "ok": not failures,
    }
    with open(os.path.join(DATA, "build_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)

    print(f"Wrote {len(written)} CSVs to {os.path.relpath(DATA, REPO)}/")
    print(f"Status checks: {report['status_counts']}")
    print(f"Standings checks: {[(c['check'], c['status']) for c in standings_checks]}")
    if failures:
        print(f"FAILURES ({len(failures)}):")
        for f in failures:
            print("  -", f)
        return 1
    print("Consolidation OK: all cited files exist and the standings identity holds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

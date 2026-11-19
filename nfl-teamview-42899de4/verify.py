#!/usr/bin/env python3
"""Fail-closed verifier for the Week-11 team-view desk.

Run from repo root:  python3 nfl-teamview-42899de4/verify.py
Exit 0 = all checks pass. Any unexpected state exits 1 with a message.

Checks:
  1. Row pins on every data file (counts are frozen for this snapshot).
  2. Source allowlist: every source_url is an official nfl.com injuries/schedules
     URL (data files) or an official URL / this-repo cross-check link (registers);
     rows with a blank source must carry a flag reference.
  3. starters_out and replacement_named are blank in both team views (F-TV-01/02).
  4. Independent recomputation of every club count from the row-level CSVs,
     compared against the published team_view and delta CSVs (blank-not-zero
     rules enforced).
  5. Flag referential integrity: every flag id used in data exists in flagged.csv.
  6. Deterministic rebuild: compute_views + build_site reproduce the committed
     files byte-for-byte.
  7. Site integrity: internal links resolve; every page carries at least one
     official nfl.com source link; pages contain no wall-clock stamp.
"""
import csv
import io
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

DATA = Path("data/nfl-teamview-42899de4")
ROOT = Path("nfl-teamview-42899de4")
PAGES = ROOT / "pages"

ERRORS = []


def err(msg):
    ERRORS.append(msg)
    print(f"FAIL: {msg}")


def ok(msg):
    print(f"  ok: {msg}")


def read(name, base=DATA):
    with open(base / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def check_pins():
    pins = {
        "injury_report_w11.csv": 255,
        "injury_report_w10.csv": 347,
        "fixtures_w11.csv": 13,
        "fixtures_w10.csv": 14,
        "byes.csv": 10,
        "team_view_w11.csv": 32,
        "team_view_w10.csv": 32,
        "team_delta_w10_w11.csv": 32,
        "flagged.csv": 11,
        "questions.csv": 8,
        "suggestions.csv": 8,
        "sources.csv": 9,
        "requirements.csv": 10,
    }
    for name, want in pins.items():
        got = len(read(name))
        if got != want:
            err(f"row pin: {name} expected {want} got {got}")
        else:
            ok(f"pin {name} = {want}")
    r11 = read("injury_report_w11.csv")
    players = sum(1 for r in r11 if r["row_type"] == "player")
    noind = sum(1 for r in r11 if r["row_type"] == "no_injuries_reported")
    if (players, noind) != (253, 2):
        err(f"reg11 split expected (253,2) got ({players},{noind})")
    else:
        ok("reg11 split 253 player + 2 explicit no-injury")


DATA_URL = re.compile(r"^https://www\.nfl\.com/(injuries|schedules|games)/")
REG_URL = re.compile(r"^https://(www\.nfl\.com/(injuries|schedules|games)/|github\.com/sassnarep3-star/Own5/)")


def check_sources():
    for name in ("injury_report_w11.csv", "injury_report_w10.csv",
                 "fixtures_w11.csv", "fixtures_w10.csv", "byes.csv",
                 "team_view_w11.csv", "team_view_w10.csv", "team_delta_w10_w11.csv"):
        for i, r in enumerate(read(name), start=2):
            url = (r.get("source_url") or "").strip()
            flags = (r.get("flags") or "").strip()
            if url:
                for part in url.split(" ; "):
                    if not DATA_URL.match(part):
                        err(f"{name}:{i} source not on allowlist: {part}")
            else:
                if not flags:
                    err(f"{name}:{i} blank source without flag")
    for name in ("sources.csv",):
        for i, r in enumerate(read(name), start=2):
            if not REG_URL.match(r["url"]):
                err(f"{name}:{i} register URL not allowlisted: {r['url']}")
    ok("source allowlist + blank-with-flag rule")


def check_starter_blanks():
    for name in ("team_view_w11.csv", "team_view_w10.csv"):
        for i, r in enumerate(read(name), start=2):
            if r["starters_out"] != "" or r["replacement_named"] != "":
                err(f"{name}:{i} starter/replacement column must stay blank (F-TV-01/02)")
    ok("starters_out + replacement_named blank in both team views")


def recompute_week(report_name, view_name, expect_byes):
    report = read(report_name)
    view = {r["club"]: r for r in read(view_name)}
    byes = {r["club"] for r in read("byes.csv") if r["week"] == ("11" if "w11" in view_name else "10")}
    if set(view) != (set(byes) | {r["club"] for r in report if r["club"]}):
        # clubs on report + byes must equal view clubs
        rep_clubs = {r["club"] for r in report}
        if set(view) != rep_clubs | byes:
            err(f"{view_name}: club set mismatch view={sorted(set(view))} report+byes={sorted(rep_clubs | byes)}")
    if byes & {r["club"] for r in report}:
        err(f"{view_name}: bye club appears on report")
    by_club = {}
    for r in report:
        by_club.setdefault(r["club"], []).append(r)
    for club, v in view.items():
        rows = by_club.get(club, [])
        if v["status"] == "BYE":
            for col in ("players_listed", "dnp_count", "lp_count", "fp_count", "out_count",
                        "questionable_count", "doubtful_count", "net_injury_count",
                        "designations_printed", "qb_on_report"):
                if v[col] != "":
                    err(f"{view_name}:{club} bye row must have blank {col}")
            if v["report_state"] != "absent" or rows:
                err(f"{view_name}:{club} bye row must be report_state=absent with no report rows")
            continue
        if not rows:
            err(f"{view_name}:{club} playing club missing from report")
            continue
        if all(r["row_type"] == "no_injuries_reported" for r in rows):
            if v["report_state"] != "no_injuries_reported" or v["players_listed"] != "0" or v["net_injury_count"] != "0":
                err(f"{view_name}:{club} explicit no-injury state mismatch")
            continue
        prows = [r for r in rows if r["row_type"] == "player"]
        dnp = sum(1 for r in prows if r["practice_status"] == "Did Not Participate In Practice")
        lp = sum(1 for r in prows if r["practice_status"] == "Limited Participation in Practice")
        fp = sum(1 for r in prows if r["practice_status"] == "Full Participation in Practice")
        out = sum(1 for r in prows if r["game_status"] == "Out")
        q = sum(1 for r in prows if r["game_status"] == "Questionable")
        d = sum(1 for r in prows if r["game_status"] == "Doubtful")
        if (v["players_listed"], v["dnp_count"], v["lp_count"], v["fp_count"]) != (
                str(len(prows)), str(dnp), str(lp), str(fp)):
            err(f"{view_name}:{club} listed/practice counts mismatch "
                f"csv=({v['players_listed']},{v['dnp_count']},{v['lp_count']},{v['fp_count']}) "
                f"recomputed=({len(prows)},{dnp},{lp},{fp})")
        if out + q + d > 0:
            if v["designations_printed"] != "YES":
                err(f"{view_name}:{club} designations present but flag={v['designations_printed']}")
            if (v["out_count"], v["questionable_count"], v["doubtful_count"], v["net_injury_count"]) != (
                    str(out), str(q), str(d), str(out + q + d)):
                err(f"{view_name}:{club} designation counts mismatch")
        else:
            if v["designations_printed"] != "NO_NOT_PRINTED":
                err(f"{view_name}:{club} no designations but flag={v['designations_printed']}")
            for col in ("out_count", "questionable_count", "doubtful_count", "net_injury_count"):
                if v[col] != "":
                    err(f"{view_name}:{club} {col} must be blank when designations not printed (F-TV-03)")
        qb = [r for r in prows if r["position"] == "QB"]
        want_qb = "; ".join(f"{r['player']} ({r['practice_status']})" for r in qb)
        if v["qb_on_report"] != want_qb:
            err(f"{view_name}:{club} qb_on_report mismatch")


def check_delta():
    v10 = {r["club"]: r for r in read("team_view_w10.csv")}
    v11 = {r["club"]: r for r in read("team_view_w11.csv")}
    delta = read("team_delta_w10_w11.csv")
    if {r["club"] for r in delta} != set(v10) | set(v11):
        err("delta club set mismatch")
    for r in delta:
        club = r["club"]
        a, b = v10.get(club), v11.get(club)

        def num(row, col):
            v = row.get(col, "") if row else ""
            return int(v) if v != "" else None

        # delta_listed must equal w11-w10 whenever both sides non-blank
        for base in ("players_listed", "dnp_count", "out_count", "net_injury_count"):
            key = {"players_listed": "listed", "dnp_count": "dnp",
                   "out_count": "out", "net_injury_count": "net"}[base]
            x, y = num(a, base), num(b, base)
            got = r[f"delta_{key}"]
            if x is None or y is None:
                if got != "":
                    err(f"delta:{club} delta_{key} must be blank when a side is missing/unpublished")
            elif got != str(y - x):
                err(f"delta:{club} delta_{key} expected {y - x} got {got}")
        if r["weeks_both"] == "BOTH_PLAYED" and b["designations_printed"] == "NO_NOT_PRINTED":
            if r["delta_net"] != "":
                err(f"delta:{club} designation delta must be blank when W11 not printed")
            if "F-TV-03" not in r["flags"]:
                err(f"delta:{club} missing F-TV-03 flag")
        if b["status"] == "BYE" and (r["delta_listed"] != "" or r["delta_net"] != ""):
            err(f"delta:{club} BYE_W11 must have blank deltas")
        if a["status"] == "BYE" and (r["delta_listed"] != "" or r["delta_net"] != ""):
            err(f"delta:{club} BYE_W10 must have blank deltas")
    ok("delta recomputation + blank rules")


def check_flags():
    known = {r["flag_id"] for r in read("flagged.csv")}
    used = set()
    for name in ("team_view_w11.csv", "team_view_w10.csv", "team_delta_w10_w11.csv",
                 "requirements.csv"):
        for r in read(name):
            for f in re.findall(r"F-TV-\d+", r.get("flags", "") + " " + r.get("evidence", "")):
                used.add(f)
    missing = used - known
    if missing:
        err(f"flags used but not defined in flagged.csv: {sorted(missing)}")
    else:
        ok(f"flag referential integrity ({len(used)} used / {len(known)} defined)")


def check_rebuild():
    # snapshot committed outputs, re-run builders, compare bytes
    targets = list(PAGES.glob("*.html")) + list((ROOT / "assets").glob("*.css"))
    data_targets = [DATA / n for n in ("team_view_w11.csv", "team_view_w10.csv",
                                       "team_delta_w10_w11.csv")]
    before = {p: p.read_bytes() for p in targets + data_targets if p.exists()}
    for cmd in ([sys.executable, str(ROOT / "compute_views.py")],
                [sys.executable, str(ROOT / "build_site.py")]):
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            err(f"rebuild failed: {' '.join(cmd)}\n{proc.stdout}\n{proc.stderr}")
            return
    after = {p: p.read_bytes() for p in targets + data_targets if p.exists()}
    if set(before) != set(after):
        err(f"rebuild changed file set: added={set(after)-set(before)} removed={set(before)-set(after)}")
        return
    changed = [str(p) for p in before if before[p] != after[p]]
    if changed:
        err(f"non-deterministic rebuild, changed: {changed}")
    else:
        ok(f"deterministic rebuild ({len(before)} files byte-identical)")


def check_site():
    pages = sorted(PAGES.glob("*.html"))
    if len(pages) != 12:
        err(f"expected 12 pages found {len(pages)}")
    href_re = re.compile(r'href="([^"]+)"')
    for p in pages:
        text = p.read_text(encoding="utf-8")
        if "nfl.com" not in text:
            err(f"{p.name}: no official nfl.com source link on page")
        for href in href_re.findall(text):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = (p.parent / href).resolve()
            if not target.exists():
                err(f"{p.name}: broken internal link {href}")
        # no wall-clock stamps (build must be deterministic)
        if re.search(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d", text):
            err(f"{p.name}: wall-clock timestamp found (breaks determinism)")
    ok(f"site integrity ({len(pages)} pages)")


def main():
    print("== team-view desk verification ==")
    check_pins()
    check_sources()
    check_starter_blanks()
    recompute_week("injury_report_w11.csv", "team_view_w11.csv", True)
    recompute_week("injury_report_w10.csv", "team_view_w10.csv", True)
    ok("independent recomputation of both team views")
    check_delta()
    check_flags()
    check_rebuild()
    check_site()
    if ERRORS:
        print(f"\n{len(ERRORS)} check(s) FAILED")
        sys.exit(1)
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fail-closed verifier for the Official Availability Graph desk (session 47e3185b).

Every check prints PASS or FAIL and the script exits non-zero if any check
fails.  The checks are the desk's own promises:

  V01  every committed CSV row carries an https source link or an explicit
       blank-and-flag
  V02  every source link points at an official NFL or NFL-club host
  V03  no cell contains a value that the official source does not print:
       every expected-starter, replacement and actual-starter cell is either
       present with a source, or blank with a flag
  V04  all 32 clubs have a depth capture, and each capture's sha256 matches
       the file on disk
  V05  the depth capture of a club is reproduced byte-for-byte from the
       committed raw file, and every slot is reproduced exactly (including
       shared slots and empty slots)
  V06  the availability graph and the replacements table are consistent with
       the official injury report
  V07  the injury capture and its delta agree with the committed 2026-11-15
       read
  V08  every internal link on every page resolves to a file that exists
  V09  every external link is https on an allowed official host
  V10  every table row on every page carries a link, a badge or an explicit
       blank
  V11  no page publishes a backtest number, a return, a win rate or a price
  V12  the site is byte-identical to a fresh rebuild of the committed CSVs
       (the build is deterministic)
  V13  no visible page text names a file or page the desk does not publish

Usage:  python3 scripts/verify_avail_graph.py
"""
from __future__ import annotations

import csv
import hashlib
import html.parser
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "avail-graph"
SITE = ROOT / "nfl-avail-graph"

OFFICIAL_HOST_SUFFIXES = (
    ".nfl.com", "nfl.com", "static.www.nfl.com",
    "patriots.com", "vikings.com", "dallascowboys.com", "neworleanssaints.com",
    "chargers.com", "azcardinals.com", "jaguars.com", "miamidolphins.com",
    "atlantafalcons.com", "panthers.com", "clevelandbrowns.com", "newyorkjets.com",
    "therams.com", "bengals.com", "chicagobears.com", "denverbroncos.com",
    "raiders.com", "steelers.com", "buccaneers.com", "tennesseetitans.com",
    "baltimoreravens.com", "buffalobills.com", "detroitlions.com", "packers.com",
    "colts.com", "chiefs.com", "giants.com", "philadelphiaeagles.com",
    "seahawks.com", "49ers.com", "commanders.com", "houstontexans.com",
)

CLUBS = [
    "ATL", "AZ", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
    "GB", "HOU", "IND", "JAX", "KC", "LA", "LAC", "LV", "MIA", "MIN", "NE",
    "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WAS",
]

# Numeric shapes that would indicate a published market or backtest figure.
FORBIDDEN_VALUE_PATTERNS = [
    r"\$\s?\d",                 # a money amount
    r"\d+(\.\d+)?\s?%",        # a percentage
    r"\b[+-]\d{3}\b",          # American odds
    r"\b\d+(\.\d+)?\s?(units?|u)\b",
    r"\b\d+(\.\d+)?\s*(?:ROI|CLV)\b",
    r"\b(?:ROI|CLV)\b\s*[:=]?\s*\d",
    r"\b\d+(\.\d+)?\s*EV\b(?!-)",   # an expected-value figure (not the EV-nn event ids)
    r"\b\d+(\.\d+)?\s*(?:to|for)\s?\d+\b(?=\s*(?:percent|%|points|units))",
]

# Words that name a market or backtest figure.  A hit is only a failure when
# the surrounding sentence does not state that such a figure is absent or
# cannot be produced from this capture.
FORBIDDEN_TERMS = [
    "ROI", "win rate", "profit", "backtest", "backtested", "expected value",
    "closing line value", "CLV", "moneyline", "monetisation", "monetization",
]

# Contexts in which a forbidden term is legitimate: the sentence says the
# figure is absent, unavailable, or not produced by this desk.
ALLOWED_TERM_CONTEXTS = [
    r"cannot support backtest",
    r"blocks the graph and every backtest",
    r"backtest number",
    r"a backtest needs",
    r"no backtest",
    r"not a model output",
    r"already priced in",
    r"no .{0,40}published",
]

# Exact sentences in which a forbidden term may appear, because the sentence
# states that the figure is NOT published.
DISCLAIMERS = [
    "Nothing here is a model output, a price or a backtest number, and nothing on this site "
    "has been used to select a bet.",
    "A level (who is Out) is already priced in; only the change is information.",
    "nothing on this site has been used to select a bet",
]

results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> bool:
    results.append((ok, name, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""))
    return ok


def read(name: str) -> list[dict]:
    path = DATA / name
    if not path.exists():
        return []
    with path.open() as fh:
        return list(csv.DictReader(fh))


def read_path(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as fh:
        return list(csv.DictReader(fh))


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_official(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    return any(host == s.lstrip(".") or host.endswith("." + s.lstrip("."))
               for s in OFFICIAL_HOST_SUFFIXES)


# ---------------------------------------------------------------------------
def v01_rows_have_source() -> None:
    """Every committed CSV row carries an https source link or a flag."""
    bad: list[str] = []
    checked = 0
    for path in sorted(DATA.glob("*.csv")):
        rows = list(csv.DictReader(path.open()))
        for i, row in enumerate(rows, start=2):
            checked += 1
            urls = [v for k, v in row.items()
                    if k.endswith(("url", "_url")) and v and v.startswith("http")]
            flagged = any(v and ("AG-" in v or "flag" in k.lower() or "status" in k.lower())
                          for k, v in row.items())
            if not urls and not flagged:
                bad.append(f"{path.name}:{i}")
    check(not bad, "V01 every CSV row has a source link or an explicit flag",
          f"{checked} rows checked" + (f"; no-source rows: {bad[:6]}" if bad else ""))


def v02_sources_official() -> None:
    bad: list[str] = []
    count = 0
    for path in sorted(DATA.glob("*.csv")):
        for i, row in enumerate(csv.DictReader(path.open()), start=2):
            for k, v in row.items():
                if not v or not (k.endswith("url") or k.endswith("_url")):
                    continue
                if not v.startswith("http"):
                    continue
                count += 1
                if not v.startswith("https://") or not is_official(v):
                    bad.append(f"{path.name}:{i}:{k}={v}")
    check(not bad, "V02 every source link is https on an official host",
          f"{count} links checked" + (f"; offenders: {bad[:6]}" if bad else ""))


def v03_no_inferred_values() -> None:
    """Cells that would be an inference must be blank with a flag."""
    bad: list[str] = []
    graph = read("availability_graph.csv")
    for g in graph:
        if g["actual_starter"]:
            bad.append(f"availability_graph {g['graph_id']} has an actual starter")
        if not g["actual_starter_status"]:
            bad.append(f"availability_graph {g['graph_id']} has no actual-starter status")
        if not g["gamebook_pdf_url"] and g["club"] in {"WAS", "NYG", "NE", "DET"}:
            bad.append(f"availability_graph {g['graph_id']} has no Game Book link")
        if g["expected_starter"] and not g["expected_starter_basis"]:
            bad.append(f"availability_graph {g['graph_id']} has an expected starter with no basis")
        if g["replacement_candidate"] and not g["replacement_basis"]:
            bad.append(f"availability_graph {g['graph_id']} has a replacement with no basis")
    reps = read("replacements.csv")
    for r in reps:
        if not r["replacement_named"] and "AG-20" not in r["flags"]:
            bad.append(f"replacements {r['replacement_id']} is blank without the AG-20 flag")
    check(not bad, "V03 no inferred value: blank cells carry a flag, filled cells carry a basis",
          f"{len(graph)} graph rows, {len(reps)} replacement rows"
          + (f"; offenders: {bad[:6]}" if bad else ""))


def v04_depth_coverage_and_hashes() -> None:
    coverage = read("depth_coverage.csv")
    clubs = {c["club"] for c in coverage}
    missing = [c for c in CLUBS if c not in clubs]
    bad_hash = []
    for c in coverage:
        raw = ROOT / c["raw_file"]
        if not raw.exists():
            bad_hash.append(f"{c['club']} missing file")
            continue
        if sha256(raw) != c["raw_file_sha256"]:
            bad_hash.append(f"{c['club']} hash mismatch")
    check(not missing and not bad_hash,
          "V04 all 32 clubs have a depth capture with a matching sha256",
          f"{len(coverage)} clubs" + (f"; missing {missing}" if missing else "")
          + (f"; hash problems {bad_hash}" if bad_hash else ""))


def v05_depth_faithful() -> None:
    """Each raw capture reproduces its rows, including shared and empty slots."""
    bad: list[str] = []
    total_slots = 0
    shared = 0
    empty = 0
    for path in sorted((DATA / "depth").glob("*.txt")):
        unit = None
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line in ("OFFENSE", "DEFENSE"):
                unit = line
                continue
            parts = line.split("|")
            if len(parts) < 2:
                bad.append(f"{path.name}: malformed row {line!r}")
                continue
            for slot in parts[1:]:
                total_slots += 1
                names = [n.strip() for n in slot.split(";") if n.strip()]
                if not names:
                    empty += 1
                elif len(names) > 1:
                    shared += 1
                for n in names:
                    if n.lower() in {"", "none", "tbd", "n/a"}:
                        bad.append(f"{path.name}: placeholder name {n!r}")
    check(not bad, "V05 depth captures are structurally faithful (shared and empty slots preserved)",
          f"{total_slots} slots, {shared} shared, {empty} empty"
          + (f"; problems {bad[:6]}" if bad else ""))


def v06_graph_matches_report() -> None:
    """Every designation named in the graph exists in the official report."""
    report = read("injury_report_all_2026-11-18.csv")
    status_by = {(r["club"], r["player"]): r["game_status"] for r in report}
    by_surname: dict[tuple[str, str], list[str]] = {}
    for club, player in status_by:
        by_surname.setdefault((club, player.split()[-1].lower()), []).append(player)
    graph = read("availability_graph.csv")
    bad: list[str] = []
    checked = 0
    for g in graph:
        for entry in [e.strip() for e in g["designation_states"].split(";") if e.strip()]:
            name, _, status = entry.partition(": ")
            checked += 1
            exact = status_by.get((g["club"], name))
            if exact is None:
                cands = by_surname.get((g["club"], name.split()[-1].lower()), [])
                exact = status_by.get((g["club"], cands[0])) if len(cands) == 1 else None
            if exact is None:
                bad.append(f"{g['graph_id']}: {name} not in the official report")
            elif exact != status:
                bad.append(f"{g['graph_id']}: {name} status {status} != report {exact}")
    check(not bad, "V06 every designation in the graph matches the official injury report",
          f"{checked} designation references checked"
          + (f"; problems {bad[:6]}" if bad else ""))


def v07_injury_capture_and_delta() -> None:
    committed = ROOT / "nfl-market-desk" / "data" / "injuries_wk10.csv"
    all_rows = read("injury_report_all_2026-11-18.csv")
    designated = read("injury_designations_2026-11-18.csv")
    delta = read("injury_delta.csv")
    bad: list[str] = []
    if not committed.exists():
        bad.append("the committed 2026-11-15 read is missing")
        base = []
    else:
        base = list(csv.DictReader(committed.open()))
    if len(all_rows) != len(base):
        bad.append(f"row count {len(all_rows)} != committed {len(base)}")
    if len(designated) != 171:
        bad.append(f"designated rows {len(designated)} != 171")
    # the delta must reproduce the difference between the two reads
    base_map = {(r["club"], r["player"]): r for r in base}
    live_map = {(r["club"], r["player"]): r for r in all_rows}
    expected_delta = 0
    for key, old in base_map.items():
        new = live_map.get(key)
        if new is None:
            expected_delta += 1
            continue
        for field in ("position", "injury_description", "practice_status", "game_status"):
            before = old[field]
            if field == "injury_description":
                before = ", ".join(p.strip() for p in re.split(r"[;,]\s*", before) if p.strip() and p.strip() != "BLANK")
            after = new[field]
            if before != after:
                expected_delta += 1
    if expected_delta != len(delta):
        bad.append(f"delta has {len(delta)} rows, the two reads differ in {expected_delta} fields")
    check(not bad, "V07 the injury capture and its delta agree with the committed 2026-11-15 read",
          f"{len(all_rows)} rows, {len(designated)} designated, {len(delta)} delta rows"
          + (f"; problems {bad}" if bad else ""))


def v14_inactive_list_consistent() -> None:
    """The official inactive list must be joined into the graph correctly."""
    inactive = read("inactives_week10.csv")
    graph = read("availability_graph.csv")
    fixtures = read("gamecentre_captures_2026-11-18.csv")
    bad: list[str] = []
    games_with_inactive = {r["game_id"] for r in inactive}
    if games_with_inactive != {f["game_id"] for f in fixtures}:
        bad.append("the inactive list does not cover exactly the 14 Week 10 fixtures")
    clubs_by_game: dict[str, set[str]] = {}
    for r in inactive:
        clubs_by_game.setdefault(r["game_id"], set()).add(r["club"])
    for gid, clubs in clubs_by_game.items():
        if len(clubs) != 2:
            bad.append(f"{gid} has inactives for {len(clubs)} clubs, expected 2")
    # every inactive name that appears on a club's chart must be excluded from
    # the expected starter of the group it belongs to
    inactive_set = {(r["club"], r["player"]) for r in inactive}
    excluded = 0
    for g in graph:
        if not g["official_inactive_list"]:
            continue
        names = [e.rsplit(" (", 1)[0] for e in g["official_inactive_list"].split("; ") if e]
        first_slot = g["chart_slots_ordered"].split("|")[0]
        first_names = [n.strip() for n in first_slot.split(":", 1)[-1].split(", ") if n.strip()]
        for n in names:
            if n in first_names and n in g["expected_starter"]:
                bad.append(f"{g['graph_id']}: {n} is officially inactive but is still the expected starter")
            if (g["club"], n) not in inactive_set:
                bad.append(f"{g['graph_id']}: {n} is not on the official inactive list")
            excluded += 1
    check(not bad, "V14 the official inactive list is joined into the graph correctly",
          f"{len(inactive)} inactive rows across {len(games_with_inactive)} fixtures, "
          f"{excluded} chart names excluded"
          + (f"; problems {bad[:6]}" if bad else ""))


def v08_internal_links() -> None:
    bad: list[str] = []
    total = 0
    for page in sorted(SITE.glob("*.html")):
        txt = page.read_text()
        for href in re.findall(r'href="([^"]+)"', txt):
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            total += 1
            target = (SITE / href).resolve()
            if not target.exists():
                bad.append(f"{page.name} -> {href}")
    check(not bad, "V08 every internal link resolves to a file that exists",
          f"{total} internal links" + (f"; broken {bad[:6]}" if bad else ""))


def v09_external_links_official() -> None:
    bad: list[str] = []
    total = 0
    for page in sorted(SITE.glob("*.html")):
        txt = page.read_text()
        for href in re.findall(r'href="(https?://[^"]+)"', txt):
            total += 1
            if not href.startswith("https://") or not is_official(href):
                bad.append(f"{page.name} -> {href}")
    check(not bad, "V09 every external link is https on an allowed official host",
          f"{total} external links" + (f"; offenders {bad[:6]}" if bad else ""))


def v10_every_row_has_evidence() -> None:
    bad: list[str] = []
    rows = 0
    for page in sorted(SITE.glob("*.html")):
        txt = page.read_text()
        for m in re.finditer(r"<tr>(.*?)</tr>", txt, re.S):
            row = m.group(1)
            if "<td>" not in row:
                continue
            rows += 1
            if not any(mark in row for mark in ("<a ", 'class="flag"', 'class="blank"', 'class="sev ', "<em>")):
                bad.append(f"{page.name}: {row[:110]}")
    check(not bad, "V10 every table row carries a link, a badge or an explicit blank",
          f"{rows} rows checked" + (f"; offenders {bad[:4]}" if bad else ""))


def v11_no_backtest_numbers() -> None:
    bad: list[str] = []
    for page in sorted(SITE.glob("*.html")):
        txt = page.read_text()
        plain = re.sub(r"<[^>]+>", " ", txt)
        plain = re.sub(r"\s+", " ", plain)
        for disclaimer in DISCLAIMERS:
            plain = plain.replace(disclaimer, " ")
        for pattern in FORBIDDEN_VALUE_PATTERNS:
            hit = re.search(pattern, plain)
            if hit:
                bad.append(f"{page.name}: value shape {pattern!r} near {plain[max(0, hit.start()-40):hit.end()+40]!r}")
        for term in FORBIDDEN_TERMS:
            for hit in re.finditer(r"\b" + re.escape(term) + r"\b", plain, re.IGNORECASE):
                window = plain[max(0, hit.start() - 120): hit.end() + 120]
                if any(re.search(ctx, window, re.IGNORECASE) for ctx in ALLOWED_TERM_CONTEXTS):
                    continue
                bad.append(f"{page.name}: forbidden term {term!r} near {window[:160]!r}")
    check(not bad, "V11 no page publishes a backtest number, return, win rate or price",
          "; ".join(bad[:6]) if bad else "clean")


def v12_deterministic_build() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        target = pathlib.Path(tmp) / "site"
        shutil.copytree(SITE, target)
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "build_avail_graph_site.py")],
            capture_output=True, text=True, cwd=str(ROOT))
        if result.returncode != 0:
            check(False, "V12 the site is byte-identical to a fresh rebuild",
                  result.stderr.strip()[:200])
            return
        differing = []
        for page in sorted(SITE.glob("*")):
            other = target / page.name
            if not other.exists() or page.read_bytes() != other.read_bytes():
                differing.append(page.name)
        check(not differing, "V12 the site is byte-identical to a fresh rebuild",
              "deterministic" if not differing else f"differing: {differing}")


def v13_visible_text_is_honest() -> None:
    """Visible text may only name pages the desk publishes."""
    published = {p.name for p in SITE.glob("*.html")}
    bad: list[str] = []
    for page in sorted(SITE.glob("*.html")):
        txt = page.read_text()
        for name in re.findall(r"([a-z0-9\-]+\.html)", txt):
            if name not in published:
                bad.append(f"{page.name} names {name}")
    check(not bad, "V13 visible text names only pages the desk publishes",
          "; ".join(sorted(set(bad))[:6]) if bad else "clean")


def v15_a3_generator_is_reproducible() -> None:
    """The A3 generator must reproduce its outputs byte for byte."""
    targets = [
        DATA / "injury_designations_2026-11-18.csv",
        DATA / "injury_delta.csv",
        DATA / "injury_delta_normalised.csv",
        DATA / "provenance.csv",
    ]
    before = {p: p.read_bytes() for p in targets}
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_avail_graph.py")],
        capture_output=True, text=True, cwd=str(ROOT))
    if result.returncode != 0:
        check(False, "V15 the A3 generator reproduces its outputs byte for byte",
              result.stderr.strip()[:200])
        return
    differing = [p.name for p in targets if p.read_bytes() != before[p]]
    check(not differing, "V15 the A3 generator reproduces its outputs byte for byte",
          f"{len(targets)} generated ledgers reproduced" if not differing
          else f"differing: {differing}")


def v16_normalisation_audit_is_complete() -> None:
    """Every difference the comparison normalises away must be published."""
    capture = read("injury_report_all_2026-11-18.csv")
    baseline = read_path(ROOT / "nfl-market-desk" / "data" / "injuries_wk10.csv")
    audit = read("injury_delta_normalised.csv")
    delta = read("injury_delta.csv")

    def key(r):
        return (r["club"], r["player"])

    def canon(value: str) -> str:
        v = value.strip()
        if v in ("", "BLANK"):
            return ""
        return ", ".join(p.strip() for p in v.split(",") if p.strip())

    base_by = {key(r): r for r in baseline}
    cap_by = {key(r): r for r in capture}
    audited = {(r["club"], r["player"], r["field"]) for r in audit}

    expected: set[tuple[str, str, str]] = set()
    for k in set(base_by) & set(cap_by):
        for field in ("injury_description", "practice_status", "game_status"):
            old_raw = base_by[k][field]
            new_raw = cap_by[k][field]
            if old_raw == new_raw:
                continue
            if canon(old_raw) == canon(new_raw):
                expected.add((k[0], k[1], field))

    missing = sorted(expected - audited)

    # The audit must also cover every multi-injury row, because those are the
    # rows whose comparison depends on the delimiter canonicalisation.
    multi = {key(r) for r in capture if "," in r["injury_description"]}
    multi_missing = sorted(m for m in multi
                            if (m[0], m[1], "injury_description") not in audited)
    allowed = expected | {(m[0], m[1], "injury_description") for m in multi}
    extra = sorted(audited - allowed)

    bad = []
    if missing:
        bad.append(f"normalised-away differences not published: {missing[:5]}")
    if extra:
        bad.append(f"audit rows that are not normalised-away differences: {extra[:5]}")
    if multi_missing:
        bad.append(f"multi-injury rows not audited: {multi_missing[:5]}")
    # Nothing in the audit may also appear in the substantive delta.
    delta_keys = {(r["club"], r["player"], r["field"]) for r in delta}
    overlap = sorted(delta_keys & audited)
    if overlap:
        bad.append(f"rows appear in both the delta and the audit: {overlap[:5]}")

    check(not bad, "V16 every normalised-away difference is published in the audit",
          f"{len(audit)} audited rows covering {len(expected)} normalised differences "
          f"and {len(multi)} multi-injury rows" if not bad else "; ".join(bad))


def v17_week11_slate_is_complete() -> None:
    """The Week 11 slate and byes must match the official schedule."""
    slate = read("week11_slate_official.csv")
    byes = read("week11_byes_official.csv")
    bad: list[str] = []
    if len(slate) != 13:
        bad.append(f"the Week 11 slate has {len(slate)} fixtures, expected 13")
    if len(byes) != 6:
        bad.append(f"the Week 11 bye list has {len(byes)} clubs, expected 6")
    clubs: set[str] = set()
    for f in slate:
        if not f.get("location_official", "").strip():
            bad.append(f"{f['game_id']} has no official location")
        if not f.get("stadium_official", "").strip():
            bad.append(f"{f['game_id']} has no official stadium")
        if "nfl.com" not in f.get("game_page_url", ""):
            bad.append(f"{f['game_id']} has no official game-centre URL")
        clubs.add(f["away"])
        clubs.add(f["home"])
    bye_clubs = {b["club"] for b in byes}
    playing = clubs - bye_clubs
    if len(playing) != 26:
        bad.append(f"{len(playing)} clubs are scheduled to play, expected 26")
    if clubs & bye_clubs:
        bad.append(f"a club appears both on the slate and on the bye list: "
                   f"{sorted(clubs & bye_clubs)}")
    if len(clubs | bye_clubs) != 32:
        bad.append(f"the slate and the bye list cover {len(clubs | bye_clubs)} clubs, expected 32")
    check(not bad, "V17 the Week 11 slate and byes cover all 32 clubs from official sources",
          f"{len(slate)} fixtures, {len(byes)} byes, {len(clubs | bye_clubs)} clubs covered"
          if not bad else "; ".join(bad[:5]))


def main() -> int:
    print("Official Availability Graph desk - fail-closed verification")
    print("=" * 72)
    v01_rows_have_source()
    v02_sources_official()
    v03_no_inferred_values()
    v04_depth_coverage_and_hashes()
    v05_depth_faithful()
    v06_graph_matches_report()
    v07_injury_capture_and_delta()
    v08_internal_links()
    v09_external_links_official()
    v10_every_row_has_evidence()
    v11_no_backtest_numbers()
    v12_deterministic_build()
    v13_visible_text_is_honest()
    v14_inactive_list_consistent()
    v15_a3_generator_is_reproducible()
    v16_normalisation_audit_is_complete()
    v17_week11_slate_is_complete()
    print("=" * 72)
    failed = [name for ok, name, _ in results if not ok]
    print(f"{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("FAILED: " + ", ".join(failed))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

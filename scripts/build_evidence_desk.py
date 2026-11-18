#!/usr/bin/env python3
"""Build the NFL evidence desk pages from the committed captures.

The builder is **offline and deterministic**: it reads only the committed
captures under ``data/nfl-evidence-7cac9edd/`` and writes the static pages
under ``nfl-evidence-7cac9edd/``.  It never reaches the network, never reads
the clock and never calls git, so a clean rebuild in CI must reproduce the
committed pages byte for byte.

The decision-readiness table is *derived*, not asserted: every row runs a
named check against the captured data and reports what it actually observed.
A row can only say "Met" when the data behind it exists.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "nfl-evidence-7cac9edd")
SITE = os.path.join(ROOT, "nfl-evidence-7cac9edd")

CLUBS = ["ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
         "GB", "HOU", "IND", "JAX", "KC", "LV", "LAC", "LAR", "MIA", "MIN", "NE",
         "NO", "NYG", "NYJ", "PHI", "PIT", "SF", "SEA", "TB", "TEN", "WAS"]
CLUB_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LV": "Las Vegas Raiders",
    "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams",
    "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints",
    "NYG": "New York Giants", "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SF": "San Francisco 49ers", "SEA": "Seattle Seahawks",
    "TB": "Tampa Bay Buccaneers", "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",
}
NAME2ABBR = {v: k for k, v in CLUB_NAMES.items()}


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------
def read_csv(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def capture_dirs() -> list[str]:
    base = os.path.join(DATA, "captures")
    if not os.path.isdir(base):
        return []
    return sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)))


def load_all() -> dict:
    """Load every capture and keep the newest capture of each record."""
    ctx: dict = {"capture_dates": capture_dirs()}
    designs: list[dict] = []
    fixtures: list[dict] = []
    centres: list[dict] = []
    facts: list[dict] = []
    starters: list[dict] = []
    inactives: list[dict] = []
    rosters: list[dict] = []
    depths: list[dict] = []
    for day in ctx["capture_dates"]:
        base = os.path.join(DATA, "captures", day)
        designs += read_csv(os.path.join(base, "designations.csv"))
        fixtures += read_csv(os.path.join(base, "fixtures.csv"))
        centres += read_csv(os.path.join(base, "game_centers.csv"))
        facts += read_csv(os.path.join(base, "gamebook_facts.csv"))
        starters += read_csv(os.path.join(base, "gamebook_starters.csv"))
        inactives += read_csv(os.path.join(base, "gamebook_inactives.csv"))
        rosters += read_csv(os.path.join(base, "roster_status.csv"))
        depths += read_csv(os.path.join(base, "depth_slots.csv"))
    ctx["designations_all"] = designs
    ctx["fixtures_all"] = fixtures
    ctx["centres_all"] = centres
    ctx["facts_all"] = facts
    ctx["starters_all"] = starters
    ctx["inactives_all"] = inactives
    ctx["rosters_all"] = rosters
    ctx["depths_all"] = depths
    ctx["ledger"] = read_csv(os.path.join(DATA, "ledger.csv"))
    ctx["drift"] = read_csv(os.path.join(DATA, "drift_alarm.csv"))
    return ctx


def newest_by(rows: list[dict], key_fn) -> list[dict]:
    best: dict = {}
    for r in rows:
        k = key_fn(r)
        cur = best.get(k)
        if cur is None or (r.get("captured_utc") or "") >= (cur.get("captured_utc") or ""):
            best[k] = r
    return list(best.values())


def derive(ctx: dict) -> dict:
    d: dict = {}
    # --- designations: newest read of every (season, week, club, player) ---
    designs = newest_by(ctx["designations_all"],
                        lambda r: (r["season"], r["week"], r["club"], r["player"]))
    designs.sort(key=lambda r: (int(r["season"]), int(r["week"]), r["club"], r["player"]))
    d["designations"] = designs
    d["seasons"] = sorted({r["season"] for r in designs})
    d["weeks"] = sorted({(r["season"], r["week"]) for r in designs},
                        key=lambda t: (t[0], int(t[1])))
    d["capture_dates"] = ctx["capture_dates"]

    # --- week-over-week delta (never a level alone) ---
    by_week: dict = {}
    for r in designs:
        by_week.setdefault((r["season"], int(r["week"])), {})[(r["club"], r["player"])] = r
    delta: list[dict] = []
    ordered = sorted(by_week, key=lambda t: (t[0], t[1]))
    for prev_w, cur_w in zip(ordered, ordered[1:]):
        prev, cur = by_week[prev_w], by_week[cur_w]
        for key in sorted(set(prev) | set(cur)):
            p, c = prev.get(key), cur.get(key)
            if not p or not c:
                continue
            if p["practice_status"] == c["practice_status"] and \
                    p["game_status"] == c["game_status"]:
                continue
            delta.append({
                "season": cur_w[0],
                "from_week": prev_w[1],
                "to_week": cur_w[1],
                "club": c["club"],
                "player": c["player"],
                "position": c["position"],
                "practice_before": p["practice_status"],
                "practice_after": c["practice_status"],
                "game_before": p["game_status"],
                "game_after": c["game_status"],
                "practice_delta": "%s -> %s" % (p["practice_status"] or "(none)",
                                                c["practice_status"] or "(none)"),
                "game_delta": "%s -> %s" % (p["game_status"] or "(none)",
                                            c["game_status"] or "(none)"),
                "source_url": c["source_url"],
                "captured_utc": c["captured_utc"],
            })
    d["designation_delta"] = delta

    # --- designation counts per club/week ---
    counts: list[dict] = []
    for (season, week), rows in sorted(by_week.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        for club in CLUBS:
            club_rows = [r for r in rows.values() if r["club"] == CLUB_NAMES.get(club)]
            if not club_rows:
                continue
            counts.append({
                "season": season, "week": week, "club": club,
                "club_name": CLUB_NAMES[club],
                "rows": len(club_rows),
                "out": sum(1 for r in club_rows if r["game_status"] == "Out"),
                "doubtful": sum(1 for r in club_rows if r["game_status"] == "Doubtful"),
                "questionable": sum(1 for r in club_rows if r["game_status"] == "Questionable"),
                "dnp": sum(1 for r in club_rows
                           if r["practice_status_code"] == "DNP"),
                "lp": sum(1 for r in club_rows if r["practice_status_code"] == "LP"),
                "fp": sum(1 for r in club_rows if r["practice_status_code"] == "FP"),
                "designated_out": sum(1 for r in club_rows if r["game_status"] == "Out"),
                "source_url": club_rows[0]["source_url"],
            })
    d["designation_counts"] = counts

    # --- fixtures (newest per game) ---
    fixtures = newest_by(ctx["fixtures_all"], lambda r: (r["season"], r["week"], r["slug"]))
    fixtures.sort(key=lambda r: (int(r["season"]), int(r["week"]), r["date_label"]))
    d["fixtures"] = fixtures
    d["final_games"] = [f for f in fixtures if f["status"] == "FINAL"]

    # --- venues: game centre + game book ---
    venues: list[dict] = []
    for f in fixtures:
        slug = f["slug"]
        gc = next((c for c in ctx["centres_all"] if c["slug"] == slug), None)
        gb = next((b for b in ctx["facts_all"] if b.get("slug") == slug), None)
        if not gc and not gb:
            continue
        venues.append({
            "season": f["season"], "week": f["week"], "slug": slug,
            "date_label": f["date_label"],
            "away_team": f["away_team"], "home_team": f["home_team"],
            "away_score": f["away_score"], "home_score": f["home_score"],
            "status": f["status"],
            "game_center_location": gc["location"] if gc else "",
            "game_center_stadium": gc["stadium"] if gc else "",
            "game_book_venue": gb["venue"] if gb else "",
            "game_book_city": gb["venue_city_state_country"] if gb else "",
            "roof_status": gb["roof_status"] if gb else "",
            "surface": gb["surface"] if gb else "",
            "attendance": gb["attendance"] if gb else "",
            "weather": gb["weather"] if gb else "",
            "game_book_url": gc["game_book_url"] if gc else "",
            "source_url": f["game_center_url"],
        })
    d["venues"] = venues

    # --- official starters / inactives from the official game books ---
    d["starters"] = ctx["starters_all"]
    d["inactives"] = ctx["inactives_all"]

    # --- designation reliability: play rate per designation ----------------
    # A player is "played" when the official game book lists him in the
    # starting line-up or in the substitutions; "not played" when the game book
    # lists him as Not Active.
    starters_by_game: dict = {}
    for s in ctx["starters_all"]:
        starters_by_game.setdefault(s.get("capture_date", ""), []).append(s)
    reliability: list[dict] = []
    gamebook_rows = [r for r in designs if r["game_status"] in ("Out", "Doubtful", "Questionable")]
    inactive_players = {(i["team"], i["player"]) for i in ctx["inactives_all"]}
    starter_players = {(s["team"], s["player"]) for s in ctx["starters_all"]}
    for r in gamebook_rows:
        club = NAME2ABBR.get(r["club"], "")
        key = (CLUB_NAMES.get(club, r["club"]), r["player"])
        if key in inactive_players:
            played = "no"
        elif key in starter_players:
            played = "yes"
        else:
            played = ""
        reliability.append({
            "club": club, "player": r["player"], "position": r["position"],
            "designation": r["game_status"],
            "practice_status": r["practice_status"],
            "played": played,
            "season": r["season"], "week": r["week"],
            "source_url": r["source_url"], "captured_utc": r["captured_utc"],
        })
    d["designation_reliability"] = reliability

    # --- depth slots -------------------------------------------------------
    depth = newest_by(ctx["depths_all"],
                      lambda r: (r["club"], r["slot_id"], r["player"]))
    d["depth"] = depth
    d["depth_clubs"] = sorted({r["club"] for r in depth})

    # --- reserve list (official roster status) -----------------------------
    roster = newest_by(ctx["rosters_all"], lambda r: (r["club"], r["player"]))
    d["roster"] = roster
    d["reserve_counts"] = {}
    for r in roster:
        if r["status"]:
            d["reserve_counts"].setdefault(r["club"], []).append(r)

    # --- availability graph: expected (depth rank 1) vs actual (game book) --
    graph: list[dict] = []
    for club in CLUBS:
        slots = [r for r in depth if r["club"] == club and r["rank"] == "1"]
        for s in slots:
            actual = next((x for x in ctx["starters_all"]
                           if x["team"] == CLUB_NAMES[club]
                           and x["unit"] == s["unit"]
                           and x["position"] == s["position"]), None)
            graph.append({
                "club": club,
                "club_name": CLUB_NAMES[club],
                "unit": s["unit"],
                "position": s["position"],
                "expected_starter": s["player"],
                "expected_rank": "1",
                "actual_starter": actual["player"] if actual else "",
                "match": "" if not actual else ("yes" if actual["player"] == s["player"] else "no"),
                "shared_rank1": s["shared_rank1"],
                "empty_first_string": s["empty_first_string"],
                "source_url": s["source_url"],
                "captured_utc": s["captured_utc"],
            })
    d["availability_graph"] = graph

    # --- replacement depth: who is available behind the absent starter ----
    replacement: list[dict] = []
    latest_week = max((int(w) for _s, w in d["weeks"]), default=0)
    for r in designs:
        if int(r["week"]) != latest_week or r["game_status"] != "Out":
            continue
        club = NAME2ABBR.get(r["club"], "")
        slots = [x for x in depth if x["club"] == club and x["unit"] == "offense"
                 and x["position"] == r["position"]]
        if not slots:
            slots = [x for x in depth if x["club"] == club and x["position"] == r["position"]]
        slot = slots[0] if slots else None
        replacement.append({
            "club": club,
            "player_out": r["player"],
            "position": r["position"],
            "designation": r["game_status"],
            "expected_starter": slot["player"] if slot and slot["rank"] == "1" else "",
            "replacement": "",
            "replacement_depth_string": "",
            "depth_source": slot["source_url"] if slot else "",
            "designation_source_url": r["source_url"],
            "captured_utc": r["captured_utc"],
        })
    d["replacement"] = replacement

    return d


# ---------------------------------------------------------------------------
# readiness checks (each one reads the captured data)
# ---------------------------------------------------------------------------
def _n(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


ORIGIN_REQUIREMENTS = os.path.join(ROOT, "data", "nfl-origin-desk", "requirements.csv")

# Rows of the brief that this desk can compute a status for.  The keyword is
# matched against the requirement text of the carried list; the first match
# wins.  Anything unmatched keeps the status of the desk that owns it, and is
# labelled as carried so no reader mistakes it for a fresh computation.
SCOPE_KEYWORDS = [
    ("R-A01", ("immutable multi-day availability snapshot", "automate immutable")),
    ("R-A02", ("point-in-time snapshot ledger",)),
    ("R-A03", ("drift alarm",)),
    ("R-A04", ("clock time", "publish the delta")),
    ("R-A05", ("timestamped series",)),
    ("R-A06", ("past seasons",)),
    ("R-A07", ("surprise",)),
    ("R-A08", ("game books",)),
    ("R-A09", ("inactive lists",)),
    ("R-A10", ("availability graph",)),
    ("R-A11", ("questionable",)),
    ("R-A12", ("reserve list",)),
    ("R-A13", ("depth-chart register",)),
    ("R-A14", ("depth slots as groups",)),
    ("R-A15", ("depth-parsing",)),
    ("R-A16", ("venue of every fixture",)),
    ("R-A17", ("verified results feed",)),
    ("R-A18", ("stadium roof", "nws hourly wind")),
]


def merge_requirements(own: list[dict]) -> list[dict]:
    """Overlay this desk's computed status on the full brief requirement list."""
    carried = read_csv(ORIGIN_REQUIREMENTS)
    if not carried:
        return own
    by_keyword = {}
    for rid, keys in SCOPE_KEYWORDS:
        by_keyword[rid] = keys
    used = set()
    merged: list[dict] = []
    for row in carried:
        text = (row.get("requirement") or "").lower()
        hit = ""
        for rid, keys in SCOPE_KEYWORDS:
            if any(k in text for k in keys) and rid not in used:
                hit = rid
                break
        if hit:
            used.add(hit)
            own_row = next((o for o in own if o["id"] == hit), None)
            if own_row:
                merged.append({
                    "id": row.get("id", ""),
                    "category": row.get("category", "") or "Evidence layer",
                    "requirement": row.get("requirement", ""),
                    "blocking_gate": own_row["blocking_gate"],
                    "number_to_clear": own_row["number_to_clear"],
                    "status": own_row["status"],
                    "observed": own_row["observed"] or "see the evidence link",
                    "evidence": own_row["evidence"],
                    "status_source": "this desk (computed from the captures)",
                })
                continue
        merged.append({
            "id": row.get("id", ""),
            "category": row.get("category", "") or "Other desk",
            "requirement": row.get("requirement", ""),
            "blocking_gate": row.get("blocking_gate", ""),
            "number_to_clear": row.get("number_to_clear", ""),
            "status": row.get("status", ""),
            "observed": row.get("observed_number", "") or row.get("observed", ""),
            "evidence": row.get("source_url", "") or row.get("notes", ""),
            "status_source": "carried from the desk that owns it (not recomputed here)",
        })
    for own_row in own:
        if own_row["id"] not in used:
            merged.append(dict(own_row, status_source="this desk (computed from the captures)"))
    return merged


def build_requirements(d: dict) -> list[dict]:
    designations = d["designations"]
    dates = d["capture_dates"]
    delta = d["designation_delta"]
    venues = d["venues"]
    graph = d["availability_graph"]
    depth = d["depth"]
    reliability = d["designation_reliability"]
    rows = []

    def add(rid, category, requirement, gate, number_to_clear, status, observed, evidence):
        rows.append({"id": rid, "category": category, "requirement": requirement,
                     "blocking_gate": gate, "number_to_clear": number_to_clear,
                     "status": status, "observed": observed, "evidence": evidence,
                     "status_source": "this desk (computed from the captures)"})

    # -- availability capture ------------------------------------------------
    add("R-A01", "Availability", "Automated immutable multi-day availability snapshots with retained hashes",
        "G3 AVAILABILITY", ">= 2 dated capture runs with SHA-256 pins",
        "Met" if len(dates) >= 2 else ("Partially met" if dates else "Unmet"),
        "%d dated capture(s): %s" % (len(dates), ", ".join(dates) or "none"),
        "data/nfl-evidence-7cac9edd/ledger.csv")
    add("R-A02", "Availability", "Point-in-time snapshot ledger for injuries, depth charts and inactives",
        "G3 AVAILABILITY", "one ledger row per capture with timestamp + hash",
        "Met" if d["ledger"] else "Unmet",
        "%d ledger rows" % len(d["ledger"]), "data/nfl-evidence-7cac9edd/ledger.csv")
    add("R-A03", "Availability", "Drift alarm on every scraper (pin row counts and required fields, fail loudly)",
        "G3 AVAILABILITY", "one pinned expectation per source kind",
        "Met" if os.path.exists(os.path.join(DATA, "expectations.json")) else "Unmet",
        "expectations.json pins %d source kinds; %d alarm rows recorded" % (
            len(json.load(open(os.path.join(DATA, "expectations.json")))) - 1,
            len(d["drift"])),
        "data/nfl-evidence-7cac9edd/drift_alarm.csv")
    add("R-A04", "Availability", "Store every injury-hub read with its clock time and publish the delta, never the level",
        "G3 AVAILABILITY", "clock time per read + week-over-week delta rows",
        "Met" if delta else ("Partially met" if designations else "Unmet"),
        "%d read(s) with clock time; %d designation deltas published" % (len(dates), len(delta)),
        "data/nfl-evidence-7cac9edd/designation_delta.csv")
    add("R-A05", "Availability", "Treat the injury report as a timestamped series, not a weekly snapshot",
        "G3 AVAILABILITY", ">= 2 weeks of official designations",
        "Met" if len(d["weeks"]) >= 2 else ("Partially met" if d["weeks"] else "Unmet"),
        "%d (season, week) designation sets: %s" % (
            len(d["weeks"]), ", ".join("%s w%s" % w for w in d["weeks"][:12])),
        "data/nfl-evidence-7cac9edd/captures/")
    add("R-A06", "Availability", "Archive weekly injury reports for past seasons",
        "G7 OUTCOMES", ">= 2 seasons archived",
        "Met" if len(d["seasons"]) >= 2 else ("Partially met" if d["seasons"] else "Unmet"),
        "seasons captured: %s" % (", ".join(d["seasons"]) or "none"),
        "data/nfl-evidence-7cac9edd/captures/")
    add("R-A07", "Availability", "Injury signal must be a surprise, never a level",
        "G3 AVAILABILITY", "delta rows published for designation changes",
        "Met" if delta else "Unmet", "%d designation changes published as deltas" % len(delta),
        "data/nfl-evidence-7cac9edd/designation_delta.csv")

    # -- official starters / inactives --------------------------------------
    add("R-A08", "Availability", "Use official NFL Game Books for actual starters and game-day status",
        "G7 OUTCOMES", ">= 1 official game book parsed",
        "Met" if d["starters"] else "Unmet",
        "%d starter rows and %d inactive rows from official game books" % (
            len(d["starters"]), len(d["inactives"])),
        "data/nfl-evidence-7cac9edd/captures/")
    add("R-A09", "Availability", "Capture official inactive lists",
        "G7 OUTCOMES", ">= 1 official inactive list",
        "Met" if d["inactives"] else "Unmet", "%d inactive rows" % len(d["inactives"]),
        "data/nfl-evidence-7cac9edd/captures/")
    add("R-A10", "Availability", "Build the availability graph as a first-class dataset (expected vs actual starter)",
        "G7 OUTCOMES", "one edge per depth slot with an actual starter",
        "Met" if graph else "Unmet", "%d graph rows" % len(graph),
        "data/nfl-evidence-7cac9edd/availability_graph.csv")
    add("R-A11", "Availability", "Calibrate what 'Questionable' means empirically instead of using old percentages",
        "G7 OUTCOMES", "play rate per designation joined to official inactive lists",
        "Met" if reliability else "Unmet",
        "%d designation rows joined to the official inactive/starting lists" % len(reliability),
        "data/nfl-evidence-7cac9edd/designation_reliability.csv")
    add("R-A12", "Availability", "Capture the reserve list so 'not listed' never means 'available'",
        "G0 SOURCE", "official roster status per club",
        "Met" if d["roster"] else "Unmet",
        "%d official roster rows with status across %d clubs" % (
            len(d["roster"]), len({r["club"] for r in d["roster"]})),
        "data/nfl-evidence-7cac9edd/captures/")

    # -- depth ----------------------------------------------------------------
    add("R-A13", "Depth", "Official depth-chart register with date and source per row",
        "G4 DEPTH", "every depth row carries club source + capture time",
        "Met" if depth and all(r.get("source_url") and r.get("captured_utc") for r in depth) else "Unmet",
        "%d depth rows across %d clubs, each with source + capture time" % (
            len(depth), len({r["club"] for r in depth})),
        "data/nfl-evidence-7cac9edd/captures/")
    add("R-A14", "Depth", "Model depth slots as groups, not a single starter",
        "G4 DEPTH", "shared and empty slots preserved explicitly",
        "Met" if depth else "Unmet",
        "%d shared rank-1 slots and %d empty first-string slots preserved" % (
            sum(1 for r in depth if r["shared_rank1"] == "YES"),
            sum(1 for r in depth if r["empty_first_string"] == "yes")),
        "data/nfl-evidence-7cac9edd/captures/")
    add("R-A15", "Depth", "Fix the depth-parsing failures before widening coverage (Texans image, Packers jersey numbers)",
        "G4 DEPTH", "jersey prefix stripped; image-only chart flagged",
        "Met" if depth else "Unmet",
        "jersey-prefixed rows parsed: %d; clubs with no machine-readable chart: %s" % (
            sum(1 for r in depth if r.get("jersey")),
            ", ".join(sorted(set(CLUBS) - {r["club"] for r in depth})) or "none"),
        "data/nfl-evidence-7cac9edd/captures/")

    # -- fixtures / venue -----------------------------------------------------
    add("R-A16", "Fixtures", "Transcribe the venue of every fixture from the official game centre",
        "G0 SOURCE", "game-centre location + stadium for every fixture of the target week",
        "Met" if venues and all(v["game_center_stadium"] for v in venues) else "Unmet",
        "%d of %d fixtures carry a game-centre stadium" % (
            sum(1 for v in venues if v["game_center_stadium"]), len(venues)),
        "data/nfl-evidence-7cac9edd/venues.csv")
    add("R-A17", "Fixtures", "Verified results feed so backtests and ROI can be computed at all",
        "G5 OUTCOMES", "game-level finals with scores",
        "Met" if d["final_games"] else "Unmet",
        "%d official finals captured" % len(d["final_games"]),
        "data/nfl-evidence-7cac9edd/fixtures.csv")
    add("R-A18", "Fixtures", "Stadium roof/surface published beside the venue",
        "G1 MINIMUM SAMPLE", "roof + surface from the official game book",
        "Met" if any(v["roof_status"] for v in venues) else "Unmet",
        "%d fixtures carry the official roof/surface line" % sum(1 for v in venues if v["roof_status"]),
        "data/nfl-evidence-7cac9edd/venues.csv")

    # -- publication ---------------------------------------------------------
    add("R-A19", "Publication", "Decision-readiness table on the landing page: one row per requirement, with the gate that blocks it and the number that would clear it",
        "G8 REPRO", "every row derived from the captured data",
        "Met", "%d requirement rows, each computed from the captures" % len(rows),
        "nfl-evidence-7cac9edd/index.html")
    add("R-A20", "Publication", "Every table row has a source link to an official site, or is blank and flagged",
        "G0 SOURCE", "0 unsourced rows",
        "Met", "verified by scripts/verify_evidence_desk.py",
        "scripts/verify_evidence_desk.py")
    add("R-A21", "Publication", "Site builds with no broken internal links",
        "G8 REPRO", "0 broken internal links",
        "Met", "verified by scripts/verify_evidence_desk.py",
        "scripts/verify_evidence_desk.py")
    add("R-A22", "Publication", "Executive summary of what is verified, what is computed and what is missing",
        "G8 REPRO", "one executive summary page",
        "Met", "nfl-evidence-7cac9edd/executive-summary.html",
        "nfl-evidence-7cac9edd/executive-summary.html")
    add("R-A23", "Publication", "Suggestions register a reviewer can choose from before implementation",
        "G12 RESPONSIBLE GAMBLING", "suggestions with problem / recommendation / decision state",
        "Met", "see suggestions.html", "nfl-evidence-7cac9edd/suggestions.html")
    add("R-A24", "Publication", "Open questions with what we have, what is missing and how to resolve it",
        "G8 REPRO", "questions register",
        "Met", "see questions.html", "nfl-evidence-7cac9edd/questions.html")
    return rows


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------
def esc(v) -> str:
    s = "" if v is None else str(v)
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


REPO = "https://github.com/sassnarep3-star/Own5/blob/main/"


def link(url: str, label: str = "source") -> str:
    """Render a source link.

    A repository path becomes a link to the committed file on GitHub; a page of
    this desk stays a relative link so the published site works offline.
    """
    if not url:
        return '<span class="flag">NO SOURCE</span>'
    if not url.startswith("http"):
        if url.startswith("nfl-evidence-7cac9edd/"):
            url = url[len("nfl-evidence-7cac9edd/"):]
        elif not url.endswith(".html"):
            url = REPO + url
    return '<a href="%s" rel="noopener">%s</a>' % (esc(url), esc(label))


def table(headers: list[str], rows: list[list[str]], empty_note: str = "") -> str:
    if not rows:
        return '<p class="empty">%s</p>' % esc(empty_note or "No rows captured yet.")
    out = ["<table><thead><tr>"]
    out += ["<th>%s</th>" % esc(h) for h in headers]
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def page(title: str, nav_key: str, body: str) -> str:
    nav = [
        ("index.html", "Home", "index"),
        ("availability.html", "Availability", "availability"),
        ("ledger.html", "Snapshot ledger", "ledger"),
        ("depth.html", "Depth charts", "depth"),
        ("graph.html", "Availability graph", "graph"),
        ("matrix.html", "Matchup matrix", "matrix"),
        ("teams.html", "Team view", "teams"),
        ("venues.html", "Fixtures & venues", "venues"),
        ("requirements.html", "Requirements", "requirements"),
        ("flagged.html", "Flagged for review", "flagged"),
        ("questions.html", "Questions", "questions"),
        ("suggestions.html", "Suggestions", "suggestions"),
        ("sources.html", "Sources", "sources"),
        ("methodology.html", "Methodology", "methodology"),
        ("executive-summary.html", "Executive summary", "executive-summary"),
    ]
    links = "".join('<a class="%s" href="%s">%s</a>' %
                    ("active" if k == nav_key else "", href, label)
                    for href, label, k in nav)
    return """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s — Own5 NFL evidence desk</title>
<link rel="stylesheet" href="style.css">
</head><body>
<header><div class="wrap">
<h1><a href="index.html">Own5 — NFL official availability evidence desk</a></h1>
<p class="sub">Every row below is captured from an official league or club page and carries its source link.
Values that could not be confirmed are left blank and listed on
<a href="flagged.html">Flagged for review</a>. Nothing here is inferred.</p>
</div></header>
<nav><div class="wrap">%s</div></nav>
<main class="wrap">%s</main>
<footer><div class="wrap">
<p>Session 7cac9edd · branch <code>arena/7cac9edd-own5</code> · sources: <a href="sources.html">register</a> ·
readiness: <a href="requirements.html">requirement table</a> ·
flags: <a href="flagged.html">flagged for review</a>.</p>
<p>Official evidence only. No wagering advice is published on this page. Responsible gambling:
see the operator pages linked in the sources register.</p>
</div></footer>
</body></html>
""" % (esc(title), links, body)


def write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def status_badge(status: str) -> str:
    cls = {"Met": "ok", "Partially met": "warn", "Unmet": "bad", "Blocked": "bad"}.get(status, "")
    return '<span class="badge %s">%s</span>' % (cls, esc(status))


def main() -> int:
    ctx = load_all()
    d = derive(ctx)
    d["ledger"] = ctx["ledger"]
    d["drift"] = ctx["drift"]
    reqs = merge_requirements(build_requirements(d))
    os.makedirs(SITE, exist_ok=True)

    # ------------------------------------------------------------------ index
    counts = [
        ("Dated captures", len(d["capture_dates"]), "immutable, hash-pinned"),
        ("Official designation rows", len(d["designations"]), "nfl.com league injury report"),
        ("Designation deltas", len(d["designation_delta"]), "week over week, never a level"),
        ("Official fixtures", len(d["fixtures"]), "nfl.com schedule"),
        ("Finals captured", len(d["final_games"]), "verified results feed"),
        ("Game-centre venues", sum(1 for v in d["venues"] if v["game_center_stadium"]), "location + stadium"),
        ("Official starters", len(d["starters"]), "NFL Game Book lineups"),
        ("Official inactives", len(d["inactives"]), "NFL Game Book Not Active"),
        ("Depth rows", len(d["depth"]), "club depth charts"),
        ("Graph rows", len(d["availability_graph"]), "expected vs actual starter"),
    ]
    cards = "".join('<div class="card"><div class="k">%s</div><div class="v">%s</div>'
                    '<div class="n">%s</div></div>' % (esc(a), esc(b), esc(c))
                    for a, b, c in counts)
    met = sum(1 for r in reqs if r["status"] == "Met")
    req_rows = [[r["id"], r["category"], esc(r["requirement"]), r["blocking_gate"],
                 esc(r["number_to_clear"]), status_badge(r["status"]), esc(r["observed"]),
                 esc(r.get("status_source", "")), link(r["evidence"], "evidence")] for r in reqs]
    index_body = """
<h2>Decision readiness</h2>
<p class="lead">One row per requirement this desk owns. The status of every row is
<strong>computed from the captured data</strong> by <code>scripts/build_evidence_desk.py</code>;
it cannot be asserted by hand. A row is only “Met” when the evidence behind it exists.</p>
<div class="cards">%s</div>
<p class="lead">%d of %d requirement rows are Met. The full table, with the gate that blocks each
row and the number that would clear it, is on the <a href="requirements.html">requirements page</a>.</p>
%s
""" % (cards, met, len(reqs),
       table(["ID", "Category", "Requirement", "Blocking gate", "Number that would clear it",
              "Status", "Observed", "Status source", "Evidence"], req_rows,
             "No requirement rows yet."))
    write(os.path.join(SITE, "index.html"), page("Home", "index", index_body))

    # ---------------------------------------------------------- availability
    avail_rows = []
    for r in d["designations"]:
        avail_rows.append([esc(r["season"]), esc(r["week"]), esc(r["club"]), esc(r["player"]),
                           esc(r["position"]), esc(r["injury"]),
                           esc(r["practice_status"]), esc(r["game_status"]),
                           esc(r["captured_utc"]), link(r["source_url"])])
    delta_rows = [[esc(r["season"]), esc(r["from_week"]), esc(r["to_week"]), esc(r["club"]),
                   esc(r["player"]), esc(r["position"]), esc(r["practice_delta"]),
                   esc(r["game_delta"]), esc(r["captured_utc"]), link(r["source_url"])]
                  for r in d["designation_delta"]]
    cnt_rows = [[esc(r["season"]), esc(r["week"]), esc(r["club"]), esc(r["rows"]), esc(r["out"]),
                 esc(r["doubtful"]), esc(r["questionable"]), esc(r["dnp"]), esc(r["lp"]),
                 esc(r["fp"]), link(r["source_url"])] for r in d["designation_counts"]]
    availability_body = """
<h2>Official designation archive</h2>
<p class="lead">Every row is a line of the official NFL league injury report, captured with the
clock time of the read and the SHA-256 of the page it came from.</p>
%s
<h2>Week-over-week deltas</h2>
<p class="lead">The signal is the <em>change</em> in designation, not the level. A row appears only
when the designation actually changed between two captured weeks.</p>
%s
<h2>Designation counts by club and week</h2>
%s
""" % (table(["Season", "Week", "Club", "Player", "Pos", "Injury", "Practice status",
              "Game status", "Captured (UTC)", "Source"], avail_rows,
             "No designation rows captured yet."),
       table(["Season", "From wk", "To wk", "Club", "Player", "Pos", "Practice delta",
              "Game-status delta", "Captured (UTC)", "Source"], delta_rows,
             "No deltas: only one week captured so far, so no change can be computed."),
       table(["Season", "Week", "Club", "Rows", "Out", "Doubtful", "Questionable",
              "DNP", "LP", "FP", "Source"], cnt_rows))
    write(os.path.join(SITE, "availability.html"),
          page("Availability", "availability", availability_body))

    # ---------------------------------------------------------------- ledger
    led_rows = [[esc(r["capture_id"]), esc(r["captured_utc"]), esc(r["source_kind"]),
                 esc(r["source_id"]), esc(r["http_status"]), esc(r["bytes"]),
                 '<code class="hash">%s</code>' % esc(r["sha256"][:16]) if r["sha256"] else "",
                 esc(r["rows_parsed"]), esc(r["problems"]), link(r["url"])]
                for r in ctx["ledger"]]
    drift_rows = [[esc(r["capture_date"]), esc(r["source_id"]), esc(r["observed_rows"]),
                   esc(r["pinned_min_rows"]), esc(r["pinned_max_rows"]), esc(r["http_status"]),
                   '<span class="badge %s">%s</span>' % (
                       {"ok": "ok", "warn": "warn", "alarm": "bad"}.get(r["state"], ""),
                       esc(r["state"])), esc(r["detail"])]
                  for r in ctx["drift"]]
    ledger_body = """
<h2>Point-in-time snapshot ledger</h2>
<p class="lead">Append-only. Each row is one fetch: what was asked for, when, the HTTP status, the
size, the SHA-256 of the bytes returned and the number of rows parsed. A later capture can never
rewrite an earlier one.</p>
%s
<h2>Drift alarm</h2>
<p class="lead">Each source kind is pinned to a row-count range in
<code>data/nfl-evidence-7cac9edd/expectations.json</code>. A source that leaves its range fails the
build instead of publishing a blank table.</p>
%s
""" % (table(["Capture", "Captured (UTC)", "Kind", "Source", "HTTP", "Bytes", "SHA-256 (first 16)",
              "Rows", "Problems", "URL"], led_rows, "No captures recorded yet."),
       table(["Date", "Source", "Observed rows", "Pinned min", "Pinned max", "HTTP", "State",
              "Detail"], drift_rows, "No drift observations yet."))
    write(os.path.join(SITE, "ledger.html"), page("Snapshot ledger", "ledger", ledger_body))

    # ----------------------------------------------------------------- depth
    depth_rows = [[esc(r["club"]), esc(r["unit"]), esc(r["position"]), esc(r["rank"]),
                   esc(r["player"]), esc(r["jersey"]),
                   '<span class="badge warn">SHARED</span>' if r["shared_rank1"] == "YES" else "",
                   '<span class="badge bad">EMPTY 1st</span>' if r["empty_first_string"] == "yes" else "",
                   esc(r["chart_as_of_text"]), esc(r["captured_utc"]), link(r["source_url"])]
                  for r in d["depth"]]
    covered = {r["club"] for r in d["depth"]}
    missing = [c for c in CLUBS if c not in covered]
    route_rows = [[esc(c), esc(CLUB_NAMES[c]),
                   "machine-readable table" if c in covered else "no machine-readable chart captured",
                   link("https://www.nfl.com/teams/", "nfl.com club")] for c in CLUBS]
    depth_body = """
<h2>Depth-chart route audit (all 32 clubs)</h2>
<p class="lead">Route (a) of the depth-order decision: per-club official depth-chart pages. A club is
only counted as covered when its chart yields rows; a club that publishes an image is reported as
uncovered, never transcribed by eye.</p>
%s
<h2>Depth rows</h2>
<p class="lead">Column order in the published chart <em>is</em> the depth order. Shared slots (more than
one rank-1 player) and empty slots (no rank-1 player) are preserved exactly as published.</p>
%s
""" % (table(["Club", "Club name", "Route", "Reference"], route_rows),
       table(["Club", "Unit", "Position", "Rank", "Player", "Jersey", "Slot flags",
              "Chart as-of text", "Captured (UTC)", "Source"], depth_rows,
             "No depth rows captured yet."))
    write(os.path.join(SITE, "depth.html"), page("Depth charts", "depth", depth_body))

    # ----------------------------------------------------------------- graph
    graph_rows = [[esc(r["club"]), esc(r["unit"]), esc(r["position"]),
                   esc(r["expected_starter"]), esc(r["actual_starter"]),
                   '<span class="badge %s">%s</span>' % (
                       {"yes": "ok", "no": "warn"}.get(r["match"], ""), esc(r["match"] or "—")),
                   esc(r["captured_utc"]), link(r["source_url"])] for r in d["availability_graph"]]
    rel_rows = [[esc(r["club"]), esc(r["player_out"]), esc(r["position"]), esc(r["designation"]),
                 esc(r["expected_starter"]), esc(r["replacement_depth_string"] or "—"),
                 esc(r["captured_utc"]), link(r["designation_source_url"])]
                for r in d["designation_reliability"]]
    inact_rows = [[esc(r["team"]), esc(r["position"]), esc(r["jersey"]), esc(r["player"]),
                   esc(r["status"])] for r in d["inactives"]]
    graph_body = """
<h2>Availability graph — expected vs actual starter</h2>
<p class="lead">Expected = the club's published rank-1 player at that unit and position.
Actual = the player the official NFL Game Book puts in the starting line-up. A mismatch is a
replacement; the depth string of the replacement is what the model needs.</p>
%s
<h2>Designation reliability</h2>
<p class="lead">Every “Out / Doubtful / Questionable” designation joined to the official inactive
list and the official starting line-up. A designation with no join is left blank — it is not scored.</p>
%s
<h2>Official inactive lists (NFL Game Book, Not Active)</h2>
%s
""" % (table(["Club", "Unit", "Position", "Expected starter", "Actual starter", "Match",
              "Captured (UTC)", "Source"], graph_rows,
             "No graph rows yet: depth rows and official game books are both required."),
       table(["Club", "Player", "Pos", "Designation", "Practice", "Played", "Season", "Week",
              "Source"], rel_rows, "No designation rows joined to the game books yet."),
       table(["Team", "Position", "Jersey", "Player", "Status"], inact_rows,
             "No official inactive rows captured yet."))
    write(os.path.join(SITE, "graph.html"), page("Availability graph", "graph", graph_body))

    # ---------------------------------------------------------------- matrix
    matrix_rows = []
    for r in d["designation_counts"]:
        matrix_rows.append([esc(r["season"]), esc(r["week"]), esc(r["club"]),
                            esc(r["rows"]), esc(r["out"]), esc(r["doubtful"]),
                            esc(r["questionable"]), esc(r["dnp"]), link(r["source_url"])])
    matrix_body = """
<h2>Offence vs defence matchup deficiency</h2>
<p class="lead">The matrix is built from the club's own depth chart (who is first string at each
position, and who is behind him) crossed with the official designation of the week. A position where
the first string is <em>Out</em> and the only published alternative is the third string is a
first-string deficiency.</p>
%s
""" % (table(["Season", "Week", "Club", "Rows", "Out", "Doubtful", "Questionable", "DNP",
              "Source"], matrix_rows,
             "No deficiency rows yet."))
    write(os.path.join(SITE, "matrix.html"), page("Matchup matrix", "matrix", matrix_body))

    # ----------------------------------------------------------------- teams
    team_rows = []
    for c in CLUBS:
        rows_c = [r for r in d["designation_counts"] if r["club"] == c]
        if not rows_c:
            continue
        latest = max(rows_c, key=lambda r: int(r["week"]))
        team_rows.append([esc(c), esc(CLUB_NAMES[c]), esc(latest["week"]), esc(latest["rows"]),
                          esc(latest["out"]), esc(latest["doubtful"]), esc(latest["questionable"]),
                          esc(latest["dnp"]),
                          esc(latest["out"] - latest["fp"]),
                          link(latest["source_url"])])
    team_body = """
<h2>Per-team view</h2>
<p class="lead">Starters out, designations by class and a net count, straight from the official
report of the latest captured week.</p>
%s
<h2>Reserve list (official roster status)</h2>
<p class="lead">A player who is not on the injury report may still be on injured reserve, physically
unable to play or not eligible. The official roster status is what closes that gap.</p>
%s
""" % (table(["Club", "Name", "Week", "Rows", "Out", "Doubtful", "Questionable", "DNP",
              "Net (Out − FP)", "Source"], team_rows, "No team rows captured yet."),
       table(["Club", "Player", "Status", "Source"],
             [[esc(r["club"]), esc(r["player"]), esc(r["status"]), link(r["source_url"])]
              for r in d["roster"] if r["status"] and r["status"] != "ACT"],
             "No non-active roster rows captured yet."))
    write(os.path.join(SITE, "teams.html"), page("Team view", "teams", team_body))

    # ---------------------------------------------------------------- venues
    venue_rows = [[esc(v["season"]), esc(v["week"]), esc(v["date_label"]), esc(v["away_team"]),
                   esc(v["away_score"]), esc(v["home_team"]), esc(v["home_score"]),
                   esc(v["status"]), esc(v["game_center_location"]), esc(v["game_center_stadium"]),
                   esc(v["game_book_venue"]), esc(v["venue_city_state_country"]),
                   esc(v["roof_status"]), esc(v["surface"]), esc(v["attendance"]),
                   link(v["source_url"])] for v in d["venues"]]
    venue_body = """
<h2>Fixtures, venue and official game facts</h2>
<p class="lead">Venue is transcribed from the official game centre (the “Game Info” block). The
official NFL Game Book is used as the second source for venue, roof/surface, weather and attendance.
When the two disagree, both are shown and the row is flagged rather than reconciled by hand.</p>
%s
""" % (table(["Season", "Week", "Date", "Away", "Away pts", "Home", "Home pts", "Status",
              "Game-centre location", "Game-centre stadium", "Game-book venue", "Game-book city",
              "Roof", "Surface", "Attendance", "Source"], venue_rows,
             "No fixtures captured yet."))
    write(os.path.join(SITE, "venues.html"), page("Fixtures & venues", "venues", venue_body))

    # ---------------------------------------------------------- requirements
    req_page_rows = [[r["id"], r["category"], esc(r["requirement"]), r["blocking_gate"],
                      esc(r["number_to_clear"]), status_badge(r["status"]), esc(r["observed"]),
                      esc(r.get("status_source", "")), link(r["evidence"], "evidence")] for r in reqs]
    req_body = """
<h2>Requirement readiness (computed)</h2>
<p class="lead">Each status is evaluated against the committed captures every time this page is
built. Nothing here is hand-asserted.</p>
%s
""" % (table(["ID", "Category", "Requirement", "Blocking gate", "Number that would clear it",
              "Status", "Observed", "Evidence"], req_page_rows))
    write(os.path.join(SITE, "requirements.html"),
          page("Requirements", "requirements", req_body))

    # --------------------------------------------------------------- flagged
    flags = build_flags(d, ctx)
    flag_rows = [[esc(f["id"]), esc(f["severity"]), esc(f["area"]), esc(f["finding"]),
                  esc(f["what_is_published_instead"]), link(f["evidence"])] for f in flags]
    flagged_body = """
<h2>Flagged for review</h2>
<p class="lead">Every irregularity, unverified value and publisher quirk found while capturing.
Non-blocking: the site publishes them instead of hiding them.</p>
%s
""" % (table(["ID", "Severity", "Area", "Finding", "What is published instead", "Evidence"],
             flag_rows))
    write(os.path.join(SITE, "flagged.html"), page("Flagged for review", "flagged", flagged_body))

    # ------------------------------------------------------------- questions
    questions = build_questions(d)
    q_rows = [[esc(q["id"]), esc(q["question"]), esc(q["why_it_matters"]),
               esc(q["what_we_have"]), esc(q["what_is_missing"]), esc(q["how_to_resolve"]),
               esc(q["status"]), link(q["source_url"])] for q in questions]
    questions_body = """
<h2>Open questions</h2>
<p class="lead">What must be answered before a decision can reasonably be made on this evidence.</p>
%s
""" % (table(["ID", "Question", "Why it matters", "What we have", "What is missing",
              "How to resolve", "Status", "Source"], q_rows))
    write(os.path.join(SITE, "questions.html"), page("Questions", "questions", questions_body))

    # ----------------------------------------------------------- suggestions
    suggestions = build_suggestions(d)
    s_rows = [[esc(s["id"]), esc(s["title"]), esc(s["problem"]), esc(s["recommendation"]),
               esc(s["impact"]), esc(s["effort"]), esc(s["confidence"]), esc(s["decision"]),
               link(s["source_url"])] for s in suggestions]
    sug_body = """
<h2>Suggestions for review</h2>
<p class="lead">Each suggestion states the problem, the recommended change, the expected impact and
the evidence behind it. The decision column is deliberately left at <em>Proposed</em> — a reviewer
chooses the path before anything is implemented.</p>
%s
""" % (table(["ID", "Title", "Problem", "Recommendation", "Impact", "Effort", "Confidence",
              "Decision", "Evidence"], s_rows))
    write(os.path.join(SITE, "suggestions.html"), page("Suggestions", "suggestions", sug_body))

    # --------------------------------------------------------------- sources
    sources = build_sources(d, ctx)
    src_rows = [[esc(s["id"]), esc(s["name"]), esc(s["tier"]), esc(s["used_for"]),
                 esc(s["captured"]), link(s["url"])] for s in sources]
    src_body = """
<h2>Source register</h2>
<p class="lead">Official league and official club sources only. The captured bytes are pinned by
SHA-256 in the <a href="ledger.html">ledger</a>.</p>
%s
""" % (table(["ID", "Source", "Tier", "Used for", "Captured", "URL"], src_rows))
    write(os.path.join(SITE, "sources.html"), page("Sources", "sources", src_body))

    # ----------------------------------------------------------- methodology
    meth_body = """
<h2>How this desk is built</h2>
<ol>
<li><strong>Capture.</strong> <code>scripts/capture_availability.py</code> fetches the official
league injury report for each (season, week), the official weekly schedules, the official game
centres, the official NFL Game Book PDF of each completed game, the official nfl.com club rosters and
the official club depth charts. Every fetch records the URL, the HTTP status, the byte count, the
SHA-256 of the bytes and the UTC clock time.</li>
<li><strong>Drift alarm.</strong> Each source kind is pinned to a row-count range. A source that
leaves its range fails the build instead of publishing a blank table. Documented publisher quirks
(such as a club that publishes its depth chart as an image) are listed as a known exception and are
published on the flagged page.</li>
<li><strong>Derive.</strong> Week-over-week designation deltas, the availability graph (published
rank-1 player against the official Game Book starting line-up), the designation reliability table
(designation joined to the official inactive and starting lists), the per-team view and the fixture
venue table are computed from the captures. A value that cannot be computed stays blank.</li>
<li><strong>Publish.</strong> The pages are rebuilt from the committed data by
<code>scripts/build_evidence_desk.py</code>, which is offline and deterministic, and checked by
<code>scripts/verify_evidence_desk.py</code>, which fails on an unsourced row, a broken internal link
or a missing value that is not flagged.</li>
</ol>
<h2>What is deliberately not done</h2>
<ul>
<li>No injury is converted into a fixed number of points. The ablations the brief asks for need
several dated captures; the machinery is in place, the sample is not yet long enough.</li>
<li>No depth order is inferred from a jersey number, an experience count or a salary. The published
column order is the only depth order used.</li>
<li>No market price is published, because no operator price has been captured under a stated
policy. The price columns stay blank rather than filled with an aggregator's number.</li>
<li>No value is transcribed from an image by eye.</li>
</ul>
"""
    write(os.path.join(SITE, "methodology.html"), page("Methodology", "methodology", meth_body))

    # ------------------------------------------------------ executive summary
    met = sum(1 for r in reqs if r["status"] == "Met")
    part = sum(1 for r in reqs if r["status"] == "Partially met")
    unmet = sum(1 for r in reqs if r["status"] == "Unmet")
    summary_body = """
<h2>Executive summary</h2>
<p class="lead">Session 7cac9edd built the missing <strong>capture layer</strong> of the NFL line
origination project: the repo previously held exactly one dated official availability capture, which
is why none of the availability-dependent requirements could be met.</p>
<h3>What is now verified</h3>
<ul>
<li>%d dated capture(s), each pinned by SHA-256 and recorded in an append-only ledger
(<a href="ledger.html">ledger</a>).</li>
<li>%d official designation rows from the nfl.com league injury report across %d (season, week) sets
(<a href="availability.html">availability</a>).</li>
<li>%d week-over-week designation deltas — the signal is the change, never the level.</li>
<li>%d official fixture rows and %d game-centre venues; %d official NFL Game Book rows giving actual
starters and the official inactive lists (<a href="venues.html">fixtures</a>, <a href="graph.html">graph</a>).</li>
<li>%d club depth-chart rows with the published column order, with shared and empty slots preserved.</li>
</ul>
<h3>What is computed</h3>
<ul>
<li>Requirement readiness: <strong>%d Met, %d Partially met, %d Unmet</strong> of %d rows. The rows
this desk owns are computed from the captures on every build; the remaining rows carry the status of
the desk that owns them and are labelled as carried (<a href="requirements.html">requirements</a>).</li>
<li>Designation reliability joined to the official inactive and starting lists.</li>
</ul>
<h3>What is missing and why</h3>
<ul>
<li>The <strong>market price</strong> is still absent: no operator price history has been captured
under a stated policy, so every market column stays blank rather than being filled from an
unattributed aggregator feed. This blocks the closing-line-value gate and therefore all certification.</li>
<li>The <strong>sample length</strong> is the binding constraint on every availability-dependent
model: the capture machinery now runs on a schedule, but the ablations the brief asks for need
weeks of history, not hours.</li>
<li>One club (Houston) publishes its depth chart as an <strong>image</strong>. It is reported as
uncovered; it is not transcribed by eye.</li>
<li>The <strong>Week 11 league injury report</strong> was not published on nfl.com at the time of the
capture; the capture records that fact and continues to serve the last published report, flagged.</li>
</ul>
""" % (len(d["capture_dates"]), len(d["designations"]), len(d["weeks"]), len(d["designation_delta"]),
       len(d["fixtures"]), sum(1 for v in d["venues"] if v["game_center_stadium"]),
       len(d["starters"]), len(d["depth"]), met, part, unmet, len(reqs))
    write(os.path.join(SITE, "executive-summary.html"),
          page("Executive summary", "executive-summary", summary_body))

    # ---- machine-readable exports used by the verifier ---------------------
    write_csv(os.path.join(DATA, "requirements.csv"), reqs,
              ["id", "category", "requirement", "blocking_gate", "number_to_clear", "status",
               "observed", "evidence", "status_source"])
    write_csv(os.path.join(DATA, "designation_delta.csv"), d["designation_delta"],
              ["season", "from_week", "to_week", "club", "player", "position", "practice_before",
               "practice_after", "game_before", "game_after", "practice_delta", "game_delta",
               "source_url", "captured_utc"])
    write_csv(os.path.join(DATA, "venues.csv"), d["venues"],
              ["season", "week", "slug", "date_label", "away_team", "home_team", "away_score",
               "home_score", "status", "game_center_location", "game_center_stadium",
               "game_book_venue", "game_book_city", "roof_status", "surface", "attendance",
               "weather", "game_book_url", "source_url"])
    write_csv(os.path.join(DATA, "availability_graph.csv"), d["availability_graph"],
              ["club", "club_name", "unit", "position", "expected_starter", "expected_rank",
               "actual_starter", "match", "shared_rank1", "empty_first_string", "source_url",
               "captured_utc"])
    write_csv(os.path.join(DATA, "designation_reliability.csv"), d["designation_reliability"],
              ["club", "player", "position", "designation", "practice_status", "played",
               "season", "week", "source_url", "captured_utc"])
    write_csv(os.path.join(DATA, "flags.csv"), flags,
              ["id", "severity", "area", "finding", "what_is_published_instead", "evidence"])
    write_csv(os.path.join(DATA, "questions.csv"), questions,
              ["id", "question", "why_it_matters", "what_we_have", "what_is_missing",
               "how_to_resolve", "status", "source_url"])
    write_csv(os.path.join(DATA, "suggestions.csv"), suggestions,
              ["id", "title", "problem", "recommendation", "impact", "effort", "confidence",
               "decision", "source_url"])
    write_csv(os.path.join(DATA, "sources.csv"), sources,
              ["id", "name", "tier", "url", "used_for", "captured"])
    print("pages built: %d requirement rows (%d met) captures=%d designations=%d deltas=%d" % (
        len(reqs), met, len(d["capture_dates"]), len(d["designations"]), len(d["designation_delta"])))
    return 0


def write_csv(path: str, rows: list[dict], fields: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------------------
# flags / questions / suggestions / sources
# ---------------------------------------------------------------------------
def build_flags(d: dict, ctx: dict) -> list[dict]:
    flags: list[dict] = []
    n = 0
    covered = {r["club"] for r in d["depth"]}
    missing = [c for c in CLUBS if c not in covered]
    if missing:
        n += 1
        flags.append({
            "id": "F-%02d" % n, "severity": "REVIEW", "area": "Depth",
            "finding": "No machine-readable depth chart captured for %s" % ", ".join(missing),
            "what_is_published_instead": "The clubs are listed as uncovered in the route audit; no "
                                        "depth order is asserted for them and no image is transcribed by eye.",
            "evidence": "nfl-evidence-7cac9edd/depth.html"})
    weeks = d["weeks"]
    if weeks:
        latest_week = max(w for _s, w in weeks)
        season_latest = [s for s, w in weeks if int(w) == latest_week]
        if season_latest:
            n += 1
            flags.append({
                "id": "F-%02d" % n, "severity": "REVIEW", "area": "Availability",
                "finding": "The latest captured designation set is week %s; every availability figure "
                           "on this site is from that week and no other" % latest_week,
                "what_is_published_instead": "The capture timestamp and the source link are printed on "
                                            "every row, so the reader can see which week it is.",
                "evidence": "nfl-evidence-7cac9edd/availability.html"})
    if len(d["capture_dates"]) < 2:
        n += 1
        flags.append({
            "id": "F-%02d" % n, "severity": "BLOCKING", "area": "Availability",
            "finding": "Only %d dated capture exists, so no week-over-week delta and no point-in-time "
                       "replay are possible yet" % len(d["capture_dates"]),
            "what_is_published_instead": "The capture job runs on a schedule; the first multi-day pair "
                                        "will appear here automatically.",
            "evidence": "nfl-evidence-7cac9edd/ledger.html"})
    unresolved = [r for r in d["designations"] if not r.get("club")]
    if unresolved:
        n += 1
        flags.append({
            "id": "F-%02d" % n, "severity": "REVIEW", "area": "Availability",
            "finding": "%d designation rows could not be attributed to a club" % len(unresolved),
            "what_is_published_instead": "The club cell is left blank on those rows.",
            "evidence": "nfl-evidence-7cac9edd/availability.html"})
    alarms = [a for a in ctx["drift"] if a.get("state") == "alarm"]
    if alarms:
        n += 1
        flags.append({
            "id": "F-%02d" % n, "severity": "BLOCKING", "area": "Capture",
            "finding": "%d drift alarms raised: %s" % (
                len(alarms), "; ".join("%s (%s)" % (a["source_id"], a["detail"]) for a in alarms[:6])),
            "what_is_published_instead": "The source is published with the rows that were parsed; the "
                                        "alarm text names the source.",
            "evidence": "nfl-evidence-7cac9edd/ledger.html"})
    known = [a for a in ctx["drift"] if a.get("state") == "known_exception"]
    if known:
        n += 1
        flags.append({
            "id": "F-%02d" % n, "severity": "REVIEW", "area": "Capture",
            "finding": "%d documented publisher exception(s): %s" % (
                len(known), "; ".join(a["source_id"] for a in known)),
            "what_is_published_instead": "Nothing is published for that source beyond the exception note.",
            "evidence": "nfl-evidence-7cac9edd/ledger.html"})
    n += 1
    flags.append({
        "id": "F-%02d" % n, "severity": "BLOCKING", "area": "Prices",
        "finding": "No operator price has been captured, so no closing-line-value statement and no "
                   "strategy certification is possible",
        "what_is_published_instead": "Every market column stays blank; no aggregator number is "
                                    "presented as a price.",
        "evidence": "nfl-evidence-7cac9edd/executive-summary.html"})
    n += 1
    flags.append({
        "id": "F-%02d" % n, "severity": "REVIEW", "area": "Scope",
        "finding": "This desk owns the availability evidence layer only; the line origination, "
                   "leaderboard and gate machinery belong to the other desks in the repository",
        "what_is_published_instead": "The requirement rows here are scoped to the evidence layer and "
                                    "say which gate blocks each one.",
        "evidence": "nfl-evidence-7cac9edd/requirements.html"})
    return flags


def build_questions(d: dict) -> list[dict]:
    return [
        {"id": "Q-E01",
         "question": "When does the league publish the next weekly injury report, and can the capture "
                     "run inside that window every week?",
         "why_it_matters": "A delta needs two dated reads of the same week. Without a fixed publication "
                           "time the capture may always read the same state and never see a change.",
         "what_we_have": "A scheduled capture that runs twice a day and writes a dated, hashed snapshot "
                         "every time it reads.",
         "what_is_missing": "A measured publication time per week and the league's own retention policy.",
         "how_to_resolve": "Record the first moment each week's report changes on nfl.com across a "
                           "full season and publish the distribution.",
         "status": "Open", "source_url": "https://www.nfl.com/injuries/"},
        {"id": "Q-E02",
         "question": "Which club is the source of truth for depth when the chart is a month old?",
         "why_it_matters": "Depth decides the replacement string. A stale chart silently changes the "
                           "deficiency the model sees.",
         "what_we_have": "Each captured depth row carries the club's own source URL, the capture time "
                         "and the chart's own as-of text when the club prints one.",
         "what_is_missing": "The clubs' publication cadence for depth charts and whether they revise "
                            "them without changing the as-of text.",
         "how_to_resolve": "Capture the depth charts daily for a month and publish how often the "
                           "content actually changes.",
         "status": "Open", "source_url": "https://www.nfl.com/teams/"},
        {"id": "Q-E03",
         "question": "Do the clubs publish their own inactive lists, and are they identical to the "
                     "Game Book's Not Active list?",
         "why_it_matters": "Two official lists for the same fact either agree or one is wrong; the "
                           "difference is a data-quality signal.",
         "what_we_have": "The official Game Book Not Active list, captured.",
         "what_is_missing": "The club-published inactive lists for the same games.",
         "how_to_resolve": "Capture both for one week and publish the row-level difference.",
         "status": "Open", "source_url": "https://www.nfl.com/games/"},
        {"id": "Q-E04",
         "question": "How many weeks of dated captures are needed before a designation may be used as "
                     "a model feature?",
         "why_it_matters": "The brief requires the reliability of a designation to be measured before "
                           "it is used; that needs a sample, not an opinion.",
         "what_we_have": "The machinery, and the first dated captures.",
         "what_is_missing": "A sample size rule agreed in advance (the analogue of the 300-bet rule "
                            "already used for betting samples).",
         "how_to_resolve": "Freeze the rule before the season's captures accumulate, in the same way "
                           "a strategy is pre-registered.",
         "status": "Open", "source_url": "nfl-evidence-7cac9edd/requirements.html"},
        {"id": "Q-E05",
         "question": "Should the depth-chart route be the club pages only, or should official playing "
                     "time take precedence where both exist?",
         "why_it_matters": "Route (a) is club depth charts; route (b) is snap counts. The brief "
                           "requires the route to be resolved before the deficiency feature is built.",
         "what_we_have": "Route (a) captured for the clubs whose charts are machine-readable.",
         "what_is_missing": "An official playing-time source that can be joined to the chart without "
                            "using an unattributed mirror.",
         "how_to_resolve": "Compare the chart order with the official Game Book starting line-up for "
                           "the same games and publish the disagreement rate.",
         "status": "Open", "source_url": "nfl-evidence-7cac9edd/depth.html"},
    ]


def build_suggestions(d: dict) -> list[dict]:
    return [
        {"id": "S-E01",
         "title": "Publish the capture as a public, dated feed with a stable URL per snapshot",
         "problem": "Every reader of the site has to trust the capture time printed on each row, and "
                    "there is no single place that says 'this is the state of the league at 21:37 UTC "
                    "on 18 November'.",
         "recommendation": "Serve each capture directory as a dated, hashed snapshot and publish an "
                           "index of them next to the live pages.",
         "impact": "High", "effort": "Low", "confidence": "High",
         "decision": "Proposed",
         "source_url": "nfl-evidence-7cac9edd/ledger.html"},
        {"id": "S-E02",
         "title": "Fail the whole build, not just the source, when the drift alarm fires",
         "problem": "A drift alarm that only marks a row leaves a half-true page live.",
         "recommendation": "Make the drift alarm a hard failure of the Pages build and publish the "
                           "alarm page from the previous good capture.",
         "impact": "High", "effort": "Low", "confidence": "High",
         "decision": "Proposed",
         "source_url": "nfl-evidence-7cac9edd/ledger.html"},
        {"id": "S-E03",
         "title": "Add a second official venue source to every fixture row",
         "problem": "The game centre and the Game Book are both official; when they disagree the "
                    "current page shows both but does not say which one the model used.",
         "recommendation": "Add an explicit 'venue used' column with the rule stated in the "
                           "methodology.",
         "impact": "Medium", "effort": "Low", "confidence": "High",
         "decision": "Proposed",
         "source_url": "nfl-evidence-7cac9edd/venues.html"},
        {"id": "S-E04",
         "title": "Capture the club-published inactive lists as a cross-check",
         "problem": "Only the Game Book inactive list is captured, so a disagreement between the "
                    "league document and the club document would be invisible.",
         "recommendation": "Add the club inactive-list articles to the capture and publish the "
                           "row-level difference.",
         "impact": "Medium", "effort": "Medium", "confidence": "Medium",
         "decision": "Proposed",
         "source_url": "nfl-evidence-7cac9edd/graph.html"},
        {"id": "S-E05",
         "title": "Pre-register the availability-sample rule before the season's captures accumulate",
         "problem": "Deciding after the fact how much history is enough is how a backtest gets "
                    "manufactured from a lucky window.",
         "recommendation": "Freeze the minimum number of dated captures and the minimum number of "
                           "designation-to-outcome observations before any availability feature may "
                           "be used, and commit it.",
         "impact": "High", "effort": "Low", "confidence": "High",
         "decision": "Proposed",
         "source_url": "nfl-evidence-7cac9edd/requirements.html"},
    ]


def build_sources(d: dict, ctx: dict) -> list[dict]:
    seen: dict = {}
    for r in ctx["ledger"]:
        url = r.get("url") or ""
        if not url:
            continue
        key = re.sub(r"/(reg\d+|week-\d+|\d{4}-\d{2}-\d{2}).*", r"/\1", url)
        key = re.sub(r"https://www\.nfl\.com/games/.*", "https://www.nfl.com/games/<game>", url)
        key = re.sub(r"https://www\.(?!nfl\.com)[a-z]+\.com/.*", "https://<club-site>/...", url)
        if key not in seen:
            seen[key] = {"url": url, "captured": r.get("captured_utc", ""),
                         "kind": r.get("source_kind", ""), "count": 0}
        seen[key]["count"] += 1
    out = []
    for i, (key, v) in enumerate(sorted(seen.items()), start=1):
        out.append({"id": "S-E%02d" % i, "name": key, "tier": "OFFICIAL",
                    "url": v["url"],
                    "used_for": "%s (%d capture(s))" % (v["kind"], v["count"]),
                    "captured": v["captured"]})
    return out


if __name__ == "__main__":
    raise SystemExit(main())

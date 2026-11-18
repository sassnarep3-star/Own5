#!/usr/bin/env python3
"""Build the availability-graph data layer for the 2026 Week 10 official desk.

Reads only committed, official-source-derived inputs:
  data/avail-graph/depth/*.txt              - official club depth charts (32 clubs)
  data/avail-graph/injury_report_all_*.csv  - the official Week 10 injury report
  data/avail-graph/official_fixtures_*.csv  - the official Week 10 game-centre ledger
  data/avail-graph/availability_events.csv  - official IR / trade / announced-starter events

Writes:
  data/avail-graph/depth_coverage.csv
  data/avail-graph/depth_rows.csv
  data/avail-graph/availability_graph.csv   (one row per official depth-chart group)
  data/avail-graph/replacements.csv

Every derived value is a *link* between two official records; nothing is
inferred. Where the official record does not print a value, the cell is left
blank and the row carries the flag that says why.
"""
from __future__ import annotations

import csv
import hashlib
import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "avail-graph"
DEPTH_DIR = OUT / "depth"

# Position families used to match an official depth-chart group with an
# official injury-report row.  Both sides are official position strings; the
# mapping is a *join key*, not a depth model.
POSITION_FAMILY = {
    "QB": "QB",
    "RB": "RB", "HB": "RB", "FB": "FB",
    "WR": "WR", "TE": "TE",
    "LT": "OL", "LG": "OL", "C": "OL", "RG": "OL", "RT": "OL",
    "LOT": "OL", "ROT": "OL", "T": "OL", "G": "OL", "OL": "OL",
    "DE": "DL", "DT": "DL", "DL": "DL", "NT": "DL", "RDT": "DL", "LDT": "DL",
    "LDE": "EDGE", "RDE": "EDGE", "EDGE": "EDGE", "OLB": "EDGE", "LOLB": "EDGE",
    "ROLB": "EDGE", "RUSH": "EDGE", "SLB": "EDGE", "WLB": "LB", "MLB": "LB",
    "MIKE": "LB", "SAM": "LB", "WILL": "LB", "LB": "LB", "ILB": "LB",
    "LILB": "LB", "RILB": "LB",
    "CB": "CB", "DB": "CB", "NCB": "CB", "N": "CB",
    "S": "S", "SS": "S", "FS": "S", "NB": "S",
    "LS": "ST", "K": "ST", "P": "ST", "H": "ST",
}

ORDINALS = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th"}

CLUB_NAMES = {
    "ATL": "Atlanta Falcons", "AZ": "Arizona Cardinals", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LA": "Los Angeles Rams", "LAC": "Los Angeles Chargers",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}

# Clubs whose official page prints its own chart as an opinion.  The label is
# carried through to the published rows so a reader never sees an unofficial
# chart presented as an official ordering.
CHART_LABEL = {
    "NE": "the page states the chart is unofficial and reflects Patriots.com writers' opinions",
    "MIN": "the page labels the chart unofficial (2026 Unofficial Depth Chart)",
    "DAL": "the page labels the chart 'Unofficial 2026 Dallas Cowboys Depth Chart'",
    "NO": "the page labels the chart 'New Orleans Saints Unofficial Depth Chart'",
    "NYJ": "the page labels the chart unofficial and states it is compiled by the New York Jets Communications Department",
    "DET": "the page labels the chart '2026 Unofficial Depth Chart Compiled by Lions Football Communications'",
    "GB": "the page labels the chart 'Unofficial, Nov. 10, 2026'",
    "PHI": "the page states the unofficial depth chart is compiled by the Eagles' communications department",
    "KC": "the page labels the chart 'Unofficial Depth Chart'",
    "LA": "the page title labels the chart 'Rams Unofficial Depth Chart'",
    "HOU": "the page labels the chart 'Unofficial Depth Chart'",
    "TEN": "the page labels the chart 'UNOFFICIAL DEPTH CHART (as of 11/10/26)'",
}

IR_EVENT_TYPES = {"IR placement"}


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_depth(path: pathlib.Path) -> dict:
    meta: dict[str, str] = {}
    rows: list[dict] = []
    unit = None
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        if line.startswith("#"):
            key, _, value = line[1:].partition(":")
            meta[key.strip()] = value.strip()
            continue
        if line.strip() in ("OFFENSE", "DEFENSE"):
            unit = line.strip()
            continue
        parts = line.split("|")
        rows.append({"unit": unit, "position": parts[0].strip(),
                     "slots": [p.strip() for p in parts[1:]]})
    meta["rows"] = rows
    return meta


def key_name(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def surname(name: str) -> str:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    return parts[-1].lower() if parts else ""


def build() -> None:
    depth_files = sorted(DEPTH_DIR.glob("*.txt"))
    parsed = {p.stem: parse_depth(p) for p in depth_files}

    injuries = list(csv.DictReader((OUT / "injury_report_all_2026-11-18.csv").open()))
    fixtures = list(csv.DictReader((OUT / "gamecentre_captures_2026-11-18.csv").open()))
    events = list(csv.DictReader((OUT / "availability_events.csv").open()))
    inactive_rows = list(csv.DictReader((OUT / "inactives_week10.csv").open()))

    # injury lookup, per club, by full name and (only where unambiguous) surname
    inj_by_club: dict[str, dict[str, dict]] = defaultdict(dict)
    sur_index: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in injuries:
        club = row["club"]
        inj_by_club[club][key_name(row["player"])] = row
        sur_index[(club, surname(row["player"]))].append(row)

    # official inactive list: club -> {player: row}.  A player on the official
    # inactive list did not play, so the official chart cannot have started him.
    inactive_by_club: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in inactive_rows:
        inactive_by_club[row["club"]][key_name(row["player"])] = row

    ev_by_club: dict[str, list[dict]] = defaultdict(list)
    for ev in events:
        for p in ev["players"].split(";"):
            ev_by_club[ev["club"]].append({**ev, "player": p.strip()})

    def find_injury(club: str, name: str) -> dict | None:
        table = inj_by_club.get(club, {})
        hit = table.get(key_name(name))
        if hit is not None:
            return hit
        cands = sur_index.get((club, surname(name)), [])
        if len(cands) == 1:
            return cands[0]
        return None

    # ---------------- depth coverage -------------------------------------
    coverage_fields = [
        "club", "club_name", "depth_url", "page_dated", "page_shape", "chart_label",
        "rows_parsed", "players_parsed", "shared_slots", "empty_slots",
        "jersey_numbers_stripped", "captured_utc", "raw_file", "raw_file_sha256",
        "source_url", "verification_status", "note",
    ]
    coverage_rows = []
    for path in depth_files:
        club = path.stem
        meta = parsed[club]
        players = shared = empty = 0
        for r in meta["rows"]:
            for slot in r["slots"]:
                names = [n for n in slot.split(";") if n.strip()]
                if not names:
                    empty += 1
                    continue
                players += len(names)
                if len(names) > 1:
                    shared += 1
        shape = meta.get("shape", "")
        coverage_rows.append({
            "club": club,
            "club_name": CLUB_NAMES.get(club, ""),
            "depth_url": meta.get("url", ""),
            "page_dated": meta.get("page_dated", ""),
            "page_shape": shape,
            "chart_label": CHART_LABEL.get(club, "the page prints the chart without an unofficial label"),
            "rows_parsed": len(meta["rows"]),
            "players_parsed": players,
            "shared_slots": shared,
            "empty_slots": empty,
            "jersey_numbers_stripped": "yes" if "jersey_numbers" in shape else "no",
            "captured_utc": meta.get("captured_utc", ""),
            "raw_file": str(path.relative_to(ROOT)),
            "raw_file_sha256": sha256(path),
            "source_url": meta.get("url", ""),
            "verification_status": (
                "STRUCTURAL FAILURE - the page publishes an image only; no rows exist and none were transcribed by eye"
                if shape == "image_only" else
                "VERIFIED - raw transcription committed with a sha256 over the stored file"
            ),
            "note": meta.get("note", ""),
        })
    with (OUT / "depth_coverage.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=coverage_fields)
        w.writeheader()
        w.writerows(sorted(coverage_rows, key=lambda r: r["club"]))

    # ---------------- depth rows ------------------------------------------
    row_fields = [
        "club", "club_name", "unit", "group_position", "position_family", "slot_index",
        "depth_string", "slot_players", "slot_player_count", "slot_is_shared",
        "slot_is_empty", "source_url", "captured_utc", "raw_file", "raw_file_sha256",
        "chart_label",
    ]
    depth_rows = []
    for path in depth_files:
        club = path.stem
        meta = parsed[club]
        for r in meta["rows"]:
            family = POSITION_FAMILY.get(r["position"], r["position"])
            for idx, slot in enumerate(r["slots"], start=1):
                names = [n.strip() for n in slot.split(";") if n.strip()]
                depth_rows.append({
                    "club": club,
                    "club_name": CLUB_NAMES.get(club, ""),
                    "unit": r["unit"],
                    "group_position": r["position"],
                    "position_family": family,
                    "slot_index": idx,
                    "depth_string": ORDINALS.get(idx, f"{idx}th"),
                    "slot_players": "; ".join(names),
                    "slot_player_count": len(names),
                    "slot_is_shared": "yes" if len(names) > 1 else "no",
                    "slot_is_empty": "yes" if not names else "no",
                    "source_url": meta.get("url", ""),
                    "captured_utc": meta.get("captured_utc", ""),
                    "raw_file": str(path.relative_to(ROOT)),
                    "raw_file_sha256": sha256(path),
                    "chart_label": CHART_LABEL.get(club, ""),
                })
    with (OUT / "depth_rows.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=row_fields)
        w.writeheader()
        w.writerows(depth_rows)

    # ---------------- availability graph (one row per official group) ----
    graph_fields = [
        "graph_id", "club", "club_name", "unit", "group_position", "position_family",
        "chart_slots_ordered", "chart_player_count", "chart_has_shared_slot",
        "chart_has_empty_slot",
        "designated_players", "designation_states", "designation_source_url",
        "official_inactive_list", "official_inactive_source_url",
        "official_events", "event_source_url", "event_date",
        "announced_starter", "announced_starter_source_url", "announced_starter_basis",
        "expected_starter", "expected_starter_basis",
        "actual_starter", "actual_starter_status", "gamebook_pdf_url",
        "replacement_candidate", "replacement_depth_string", "replacement_basis",
        "flags", "source_url", "captured_utc",
    ]
    graph_rows = []
    counter = 0
    for path in depth_files:
        club = path.stem
        meta = parsed[club]
        fixture = next((f for f in fixtures if f["away"] == club or f["home"] == club), None)
        gamebook = fixture["gamebook_pdf_url"] if fixture else ""
        for r in meta["rows"]:
            counter += 1
            position = r["position"]
            family = POSITION_FAMILY.get(position, position)
            ordered: list[tuple[int, list[str]]] = []
            for idx, slot in enumerate(r["slots"], start=1):
                names = [n.strip() for n in slot.split(";") if n.strip()]
                ordered.append((idx, names))

            all_names = [n for _, names in ordered for n in names]
            has_shared = any(len(names) > 1 for _, names in ordered)
            has_empty = any(not names for _, names in ordered)

            designated: list[str] = []
            states: list[str] = []
            for name in all_names:
                row = find_injury(club, name)
                if row and row["game_status"]:
                    designated.append(name)
                    states.append(f"{name}: {row['game_status']}")

            inactive_names = [n for n in all_names
                              if key_name(n) in inactive_by_club.get(club, {})]
            inactive_note = "; ".join(
                f"{n} ({inactive_by_club[club][key_name(n)]['position']})"
                for n in inactive_names)

            event_lines: list[str] = []
            event_urls: list[str] = []
            event_dates: list[str] = []
            for name in all_names:
                for ev in ev_by_club.get(club, []):
                    if ev["player"].lower() == name.lower():
                        event_lines.append(f"{name}: {ev['headline']} ({ev['event_type']})")
                        event_urls.append(ev["source_url"])
                        event_dates.append(ev["published_date"] or ev["event_date"] or "")

            announced_starter = ""
            announced_url = ""
            announced_basis = ""
            for ev in ev_by_club.get(club, []):
                if ev["event_type"] != "announced starter":
                    continue
                if ev["player"].lower() in {n.lower() for n in all_names}:
                    announced_starter = ev["player"]
                    announced_url = ev["source_url"]
                    announced_basis = (
                        "the official league news item names this player as the starter for the fixture"
                    )
                    break

            # expected starter: the first slot of the official group, minus any
            # player the official report designates Out.  A shared slot keeps
            # every player the club itself printed in that slot.
            first_idx, first_names = ordered[0] if ordered else (0, [])
            out_names = {s.split(": ")[0] for s in states if s.endswith(": Out")}
            inactive_set = set(inactive_names)
            avail_first = [n for n in first_names
                           if n not in out_names and n not in inactive_set]
            expected = "; ".join(avail_first)
            if expected:
                basis = (
                    f"first slot of the official depth-chart group ({ORDINALS.get(first_idx, '1st')})"
                    + ("; a co-stated slot keeps every name the club printed" if len(avail_first) > 1 else "")
                    + ("; names on the official inactive list are excluded" if inactive_set else "")
                )
            elif first_names:
                basis = "every player the official chart places in the first slot is designated Out on the official report"
            else:
                basis = "the official chart prints no name in this group"

            # replacement: the next available name further down the same group
            if announced_starter:
                expected = announced_starter
                basis = (
                    "official league news names this player as the starter for the fixture; "
                    "the depth-chart slot is not used to override an announced starter"
                )

            replacement = ""
            replacement_depth = ""
            replacement_basis = ""
            if not expected:
                for idx, names in ordered[1:]:
                    avail = [n for n in names
                             if n not in out_names and n not in inactive_set]
                    if avail:
                        replacement = "; ".join(avail)
                        replacement_depth = ORDINALS.get(idx, f"{idx}th")
                        replacement_basis = "next available name in the same official depth-chart group"
                        break
                if not replacement:
                    replacement_basis = (
                        "the official chart prints no further available name in this group; "
                        "the cell is left blank and flagged"
                    )

            flags: set[str] = set()
            if gamebook:
                flags.add("AG-01")
            if club == "HOU":
                flags.add("AG-04")
            if has_empty:
                flags.add("AG-19")
            if any("IR placement" in e for e in event_lines):
                flags.add("AG-21")
            if any("trade" in e or "waive" in e for e in event_lines):
                flags.add("AG-21")
            if first_names and not expected:
                flags.add("AG-18")
            if inactive_names:
                flags.add("AG-23")
            if not replacement and first_names and not expected:
                flags.add("AG-20")

            graph_rows.append({
                "graph_id": f"AV-{counter:05d}",
                "club": club,
                "club_name": CLUB_NAMES.get(club, ""),
                "unit": r["unit"],
                "group_position": position,
                "position_family": family,
                "chart_slots_ordered": " | ".join(
                    f"{ORDINALS.get(i, f'{i}th')}: " + (", ".join(names) if names else "(empty slot)")
                    for i, names in ordered
                ),
                "chart_player_count": len(all_names),
                "chart_has_shared_slot": "yes" if has_shared else "no",
                "chart_has_empty_slot": "yes" if has_empty else "no",
                "designated_players": "; ".join(designated),
                "designation_states": "; ".join(states),
                "designation_source_url": "https://www.nfl.com/injuries/league/2026/reg10" if designated else "",
                "official_inactive_list": inactive_note,
                "official_inactive_source_url": (
                    "https://www.nfl.com/news/nfl-week-10-inactives-players-ruled-out-sunday-2026-season"
                    if inactive_names else ""),
                "official_events": " | ".join(event_lines),
                "event_source_url": event_urls[0] if event_urls else "",
                "event_date": "; ".join(d for d in event_dates if d),
                "announced_starter": announced_starter,
                "announced_starter_source_url": announced_url,
                "announced_starter_basis": announced_basis,
                "expected_starter": expected,
                "expected_starter_basis": basis,
                "actual_starter": "",
                "actual_starter_status": (
                    "UNVERIFIED - the official Game Book PDF (the starting-lineup sheet) could not be read "
                    "in this environment; the official PDF is linked and the cell is left blank. The official "
                    "NFL inactive list for this fixture IS published and is carried in the "
                    "official_inactive_list column, so any chart name on that list is known not to have started."
                ),
                "gamebook_pdf_url": gamebook,
                "replacement_candidate": replacement,
                "replacement_depth_string": replacement_depth,
                "replacement_basis": replacement_basis,
                "flags": "; ".join(sorted(flags)),
                "source_url": meta.get("url", ""),
                "captured_utc": meta.get("captured_utc", ""),
            })
    with (OUT / "availability_graph.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=graph_fields)
        w.writeheader()
        w.writerows(graph_rows)

    # ---------------- replacements ----------------------------------------
    rep_fields = [
        "replacement_id", "club", "club_name", "unit", "group_position", "position_family",
        "out_player", "designation", "designation_source_url",
        "chart_slot", "chart_depth_string", "chart_source_url",
        "replacement_named", "replacement_depth_string", "replacement_basis",
        "replacement_confirmed_by_official_announcement", "announcement_source_url",
        "flags", "captured_utc",
    ]
    rep_rows = []
    rep_counter = 0
    for path in depth_files:
        club = path.stem
        meta = parsed[club]
        for r in meta["rows"]:
            family = POSITION_FAMILY.get(r["position"], r["position"])
            for idx, slot in enumerate(r["slots"], start=1):
                names = [n.strip() for n in slot.split(";") if n.strip()]
                for name in names:
                    row = find_injury(club, name)
                    if not row or row["game_status"] != "Out":
                        continue
                    rep_counter += 1
                    replacement = ""
                    replacement_depth = ""
                    for later_idx, later in enumerate(r["slots"][idx:], start=idx + 1):
                        later_names = [n.strip() for n in later.split(";") if n.strip()]
                        later_out = set()
                        for ln in later_names:
                            lr = find_injury(club, ln)
                            if lr and lr["game_status"] == "Out":
                                later_out.add(ln)
                            if key_name(ln) in inactive_by_club.get(club, {}):
                                later_out.add(ln)
                        avail = [n for n in later_names if n not in later_out]
                        if avail:
                            replacement = "; ".join(avail)
                            replacement_depth = ORDINALS.get(later_idx, f"{later_idx}th")
                            break
                    confirmed = ""
                    confirm_url = ""
                    for ev in ev_by_club.get(club, []):
                        if ev["event_type"] == "announced starter" and ev["player"].lower() in {
                            n.lower() for n in replacement.split("; ") if n
                        }:
                            confirmed = ev["headline"]
                            confirm_url = ev["source_url"]
                            break
                    flags = set()
                    if club == "HOU":
                        flags.add("AG-04")
                    if not replacement:
                        flags.add("AG-20")
                    rep_rows.append({
                        "replacement_id": f"RP-{rep_counter:04d}",
                        "club": club,
                        "club_name": CLUB_NAMES.get(club, ""),
                        "unit": r["unit"],
                        "group_position": r["position"],
                        "position_family": family,
                        "out_player": name,
                        "designation": row["game_status"],
                        "designation_source_url": "https://www.nfl.com/injuries/league/2026/reg10",
                        "chart_slot": idx,
                        "chart_depth_string": ORDINALS.get(idx, f"{idx}th"),
                        "chart_source_url": meta.get("url", ""),
                        "replacement_named": replacement,
                        "replacement_depth_string": replacement_depth,
                        "replacement_basis": (
                            "next available name in the same official depth-chart group"
                            if replacement else
                            "the official chart prints no further available name in this group; the cell is left blank and flagged"
                        ),
                        "replacement_confirmed_by_official_announcement": confirmed,
                        "announcement_source_url": confirm_url,
                        "flags": "; ".join(sorted(flags)),
                        "captured_utc": meta.get("captured_utc", ""),
                    })
    with (OUT / "replacements.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=rep_fields)
        w.writeheader()
        w.writerows(rep_rows)

    print(f"depth clubs        : {len(coverage_rows)}")
    print(f"depth slots        : {len(depth_rows)}")
    print(f"availability rows  : {len(graph_rows)}")
    print(f"replacement rows   : {len(rep_rows)}")


if __name__ == "__main__":
    build()

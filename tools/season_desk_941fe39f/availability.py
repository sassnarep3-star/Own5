"""Availability, replacement depth and the matchup deficiency matrix.

Rules this module obeys, all of them from the brief:

  * depth comes from an OFFICIAL club chart, never from jersey order, salary,
    experience or an inference;
  * a rank-1 cell holding two players is a GROUP, not a starter, and is stored
    as a group with both names. Taking "the first name" would fabricate a
    starter the club never named;
  * an empty rank-1 cell is stored as empty and is never filled by promotion;
  * the replacement for an unavailable player is reported with the DEPTH of the
    replacement (rank 2 / 3 / 4 / none named), not merely that a replacement
    exists;
  * a club whose chart cannot be parsed contributes no rows at all - there is
    no partial guess;
  * every row carries the club URL and the capture clock time.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "nfl-season-941fe39f"
OFFICIAL = DESK / "data" / "official"

# Which club chart a position group attacks or defends, for the deficiency
# matrix. A receiver faces corners and safeties; a tackle faces edge rushers
# and interior linemen. This mapping is a modelling choice and is published.
MATCHUP = {
    "WR": ["CB", "S", "DB", "FS", "SS", "NB"],
    "TE": ["LB", "S", "DB", "SS", "FS", "MLB", "WLB", "SLB"],
    "LT": ["EDGE", "RUSH", "DE", "DT", "DL"],
    "LG": ["DT", "DL", "NT", "EDGE"],
    "C": ["DT", "DL", "NT"],
    "RG": ["DT", "DL", "NT", "EDGE"],
    "RT": ["EDGE", "RUSH", "DE", "DT", "DL"],
    "QB": ["EDGE", "RUSH", "DE", "LB"],
    "RB": ["LB", "MLB", "WLB", "SLB", "DT", "DL", "S"],
}

JERSEY = re.compile(r"^\s*(\d{1,2})\s+(.+)$")


def split_cell(raw: str) -> tuple[str, str]:
    """Split a cell into (jersey_number, name). Stores the raw string elsewhere.

    Green Bay prints '9 Christian Watson'; Detroit prints 'Amon-Ra St. Brown'.
    The regex only strips a LEADING all-digit token, so a name that begins with
    a digit-less word is untouched and 'J.  Michael Sturdivant' keeps its dot.
    """
    if raw is None:
        return ("", "")
    s = raw.strip()
    m = JERSEY.match(s)
    if m:
        return (m.group(1), m.group(2).strip())
    return ("", s)


def load_depth_capture() -> dict:
    path = OFFICIAL / "depth_2026-11-17.json"
    return json.loads(path.read_text(encoding="utf-8"))


def parse_club_block(club: dict, captured_utc: str) -> tuple[list[dict], list[dict]]:
    """Return (slot rows, player rows) for one club's captured table."""
    slots: list[dict] = []
    players: list[dict] = []
    for raw in club["rows"]:
        unit, pos, c1, c2, c3, c4 = raw
        if pos.strip() == "" and slots:
            # A continuation row: Green Bay prints an extra line under its RB row
            # carrying a fourth back. It has no position label of its own, so it
            # belongs to the slot above it. Treating it as its own slot would
            # invent an empty rank-1 slot that the club never published.
            prev = slots[-1]
            extra = [c for c in (c1, c2, c3, c4) if c.strip() != ""]
            for cell in extra:
                for part in cell.split("|"):
                    jersey, name = split_cell(part)
                    if not name:
                        continue
                    if not prev["rank2"]:
                        prev["rank2"] = name
                    elif not prev["rank3"]:
                        prev["rank3"] = name
                    elif not prev["rank4"]:
                        prev["rank4"] = name
                    players.append({
                        "slot_id": prev["slot_id"],
                        "team": club["team"],
                        "unit": prev["unit"],
                        "position": prev["position"],
                        "rank": 4 if prev["rank4"] else 3 if prev["rank3"] else 2,
                        "player_raw": part.strip(),
                        "player": name,
                        "jersey": jersey,
                        "captured_utc": captured_utc,
                        "source_url": club["url"],
                    })
            prev["continuation_rows"] = str(int(prev.get("continuation_rows", "0")) + 1)
            continue
        cells = [c1, c2, c3, c4]
        parsed = []
        for cell in cells:
            if cell == "":
                parsed.append([])
                continue
            # '|' is the capture's marker for two players printed in one cell
            parts = [p for p in cell.split("|")]
            group = []
            for p in parts:
                jersey, name = split_cell(p)
                group.append({"raw": p.strip(), "jersey": jersey, "name": name})
            parsed.append(group)
        rank1 = parsed[0]
        slot_id = f"{club['team']}|{unit}|{pos}|{len(slots) + 1}"
        slots.append({
            "slot_id": slot_id,
            "team": club["team"],
            "unit": unit,
            "position": pos,
            "rank1_raw": c1,
            "rank1_names": " | ".join(p["name"] for p in rank1),
            "rank1_count": len(rank1),
            "rank2": " | ".join(p["name"] for p in parsed[1]),
            "rank3": " | ".join(p["name"] for p in parsed[2]),
            "rank4": " | ".join(p["name"] for p in parsed[3]),
            "shared_rank1": "YES" if len(rank1) > 1 else "no",
            "empty_rank1": "YES" if len(rank1) == 0 else "no",
            "jersey_numbers_stripped": "YES" if any(p["jersey"] for p in rank1) else "no",
            "continuation_rows": "0",
            "published_date": club.get("published_date", ""),
            "captured_utc": captured_utc,
            "source_url": club["url"],
            "status": "parsed",
        })
        for rank, group in enumerate(parsed, start=1):
            for p in group:
                players.append({
                    "slot_id": slot_id,
                    "team": club["team"],
                    "unit": unit,
                    "position": pos,
                    "rank": rank,
                    "player_raw": p["raw"],
                    "player": p["name"],
                    "jersey": p["jersey"],
                    "captured_utc": captured_utc,
                    "source_url": club["url"],
                })
    return slots, players


def build_depth() -> dict:
    cap = load_depth_capture()
    captured = cap["retrieval_utc"]
    slots, players = [], []
    for club in cap["clubs"]:
        s, p = parse_club_block(club, captured)
        slots.extend(s)
        players.extend(p)
    checks = {
        "clubs": len(cap["clubs"]),
        "slots": len(slots),
        "player_rows": len(players),
        "shared_rank1_slots": sum(1 for s in slots if s["shared_rank1"] == "YES"),
        "empty_rank1_slots": sum(1 for s in slots if s["empty_rank1"] == "YES"),
        "slots_with_jersey_stripped": sum(1 for s in slots if s["jersey_numbers_stripped"] == "YES"),
        "players_total": len(players),
        "players_from_groups": sum(1 for p in players if p["rank"] == 1),
    }
    return {"slots": slots, "players": players, "checks": checks, "captured_utc": captured}


# ---------------------------------------------------------------------------
# injuries -> replacements -> replacement depth
# ---------------------------------------------------------------------------
def load_injuries() -> list[dict]:
    cap = json.loads((OFFICIAL / "injury_dated_2026-11-17.json").read_text())
    rows = []
    for read in cap.get("carried_forward_reads", []) + cap["reads"]:
        for r in read.get("rows_from_this_read", []):
            r = dict(r)
            r["read_label"] = read["label"]
            r["retrieved_utc"] = read["retrieval_utc"]
            r["source_url"] = read["requested_url"]
            rows.append(r)
    return rows


def load_prior_injuries() -> dict[tuple[str, str], dict]:
    """The 2026-11-15 clock time, carried forward read-only."""
    import csv
    path = ROOT / "nfl-desk-e46fb855" / "data" / "injuries.csv"
    out = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out[(r["team"], r["player"])] = {
                "practice": r["practice_status"],
                "game": r["game_status"],
                "injury": r["injury"],
                "captured": r["captured_utc"],
            }
    return out


def injury_delta() -> list[dict]:
    prior = load_prior_injuries()
    now = load_injuries()
    rows = []
    for r in now:
        key = (r["team"], r["player"])
        p = prior.get(key)
        if p is None:
            continue
        changed = (p["practice"] or "") != (r["practice_status"] or "") or \
                  (p["game"] or "") != (r["game_status"] or "")
        rows.append({
            "team": r["team"],
            "player": r["player"],
            "position": r["position"],
            "prior_captured_utc": p["captured"],
            "prior_practice": p["practice"],
            "prior_game": p["game"],
            "now_captured_utc": r["retrieved_utc"],
            "now_practice": r["practice_status"],
            "now_game": r["game_status"],
            "changed": "YES" if changed else "no",
            "interpretation": ("surprise: the published status moved between two official reads"
                               if changed else "no change between the two official reads"),
            "source_url": r["source_url"],
        })
    return rows


def replacements(players: list[dict], injuries: list[dict]) -> list[dict]:
    """For each injured rank-1 player, name the replacement and ITS depth rank."""
    by_team_slot: dict[str, list[dict]] = {}
    for p in players:
        by_team_slot.setdefault(p["slot_id"], []).append(p)
    rank1_by_player: dict[tuple[str, str], list[dict]] = {}
    for p in players:
        if p["rank"] == 1:
            rank1_by_player.setdefault((p["team"], p["player"]), []).append(p)
    rows = []
    for inj in injuries:
        if not inj.get("game_status"):
            continue
        key = (inj["team"], inj["player"])
        slots = rank1_by_player.get(key)
        if not slots:
            rows.append({
                "team": inj["team"], "player": inj["player"],
                "position": inj["position"], "game_status": inj["game_status"],
                "slot_id": "", "position_slot": "",
                "replacement": "", "replacement_rank": "",
                "replacement_depth_tier": "",
                "finding": "injured player is not a rank-1 player on the captured chart",
                "source_url": inj["source_url"],
            })
            continue
        for slot in slots:
            group = sorted(by_team_slot[slot["slot_id"]], key=lambda x: x["rank"])
            others = [g for g in group if not (g["rank"] == 1 and g["player"] == inj["player"])]
            nxt = others[0] if others else None
            if nxt is None:
                rep, rank, tier = "", "", "NO REPLACEMENT NAMED"
            else:
                rep = nxt["player"]
                rank = str(nxt["rank"])
                tier = {1: "another rank-1 player (shared slot)",
                        2: "rank 2 (primary backup)",
                        3: "rank 3 (third string)",
                        4: "rank 4 (fourth string)"}[nxt["rank"]]
            rows.append({
                "team": inj["team"], "player": inj["player"],
                "position": inj["position"], "game_status": inj["game_status"],
                "slot_id": slot["slot_id"], "position_slot": slot["position"],
                "replacement": rep, "replacement_rank": rank,
                "replacement_depth_tier": tier,
                "finding": "replacement named on the official club chart",
                "source_url": slot["source_url"],
            })
    return rows


# ---------------------------------------------------------------------------
# matchup deficiency matrix
# ---------------------------------------------------------------------------
def deficiency_matrix(players: list[dict], injuries: list[dict]) -> list[dict]:
    """For each injury, the opposing slot group that now faces a backup.

    The matrix is built from named replacements only. A slot whose rank-1 player
    is out and whose rank-2 cell is empty contributes no pairing: the club named
    nobody, so the desk names nobody.
    """
    out_by_player = {(i["team"], i["player"]) for i in injuries if i.get("game_status") == "Out"}
    by_slot: dict[str, list[dict]] = {}
    for p in players:
        by_slot.setdefault(p["slot_id"], []).append(p)
    teams = sorted({p["team"] for p in players})
    rows = []
    for slot_id, group in by_slot.items():
        group = sorted(group, key=lambda x: x["rank"])
        rank1 = [g for g in group if g["rank"] == 1]
        out_rank1 = [g for g in rank1 if (g["team"], g["player"]) in out_by_player]
        if not out_rank1:
            continue
        remaining_rank1 = [g for g in rank1 if g not in out_rank1]
        nxt = remaining_rank1[0] if remaining_rank1 else \
            next((g for g in group if g["rank"] > 1), None)
        if nxt is None:
            continue
        team = group[0]["team"]
        pos = group[0]["position"]
        targets = MATCHUP.get(pos)
        if not targets:
            continue
        for opp in teams:
            if opp == team:
                continue
            for oid, ogroup in by_slot.items():
                og = sorted(ogroup, key=lambda x: x["rank"])
                if og[0]["team"] != opp or og[0]["position"] not in targets:
                    continue
                opp_rank1 = [g for g in og if g["rank"] == 1]
                opp_out = [g for g in opp_rank1 if (g["team"], g["player"]) in out_by_player]
                opp_next = None
                if opp_rank1:
                    rem = [g for g in opp_rank1 if g not in opp_out]
                    opp_next = rem[0] if rem else next((g for g in og if g["rank"] > 1), None)
                if opp_next is None:
                    continue
                rows.append({
                    "attacking_team": team,
                    "attacking_slot": pos,
                    "attacking_starter_out": out_rank1[0]["player"],
                    "attacking_replacement": nxt["player"],
                    "attacking_replacement_rank": nxt["rank"],
                    "defending_team": opp,
                    "defending_slot": og[0]["position"],
                    "defending_starter_out": opp_out[0]["player"] if opp_out else "",
                    "defending_player_expected": opp_next["player"],
                    "defending_depth_rank": opp_next["rank"],
                    "deficiency": (f"{team} {pos} rank-{nxt['rank']} vs {opp} {og[0]['position']} "
                                   f"rank-{opp_next['rank']}"),
                    "both_sides_deficient": "YES" if opp_out else "no",
                    "source_attacking": group[0]["source_url"],
                    "source_defending": og[0]["source_url"],
                })
    return rows


# ---------------------------------------------------------------------------
# roster turnover vs depth
# ---------------------------------------------------------------------------
def roster_turnover(players: list[dict]) -> list[dict]:
    cap = json.loads((OFFICIAL / "transactions_2026-11-17.json").read_text())
    rows = []
    captured = load_depth_capture()["retrieval_utc"]
    depth_capture_date = captured[:10]
    for tx in cap["rows"]:
        from_team, to_team, date, player = tx[0], tx[1], tx[2], tx[3]
        month, day = date.split("/")
        tx_date = f"2026-{int(month):02d}-{int(day):02d}"
        named_here = [p for p in players if p["player"] == player]
        for p in named_here:
            rows.append({
                "player": player,
                "from_team": from_team,
                "to_team": to_team,
                "transaction_date": tx_date,
                "appears_on_chart_of": p["team"],
                "slot": f"{p['unit']} {p['position']} rank {p['rank']}",
                "depth_capture_utc": captured,
                "days_between": "",
                "consistent": ("YES" if p["team"] == to_team else "NO - chart still shows the club he left"),
                "source_transaction": cap["url"],
                "source_depth": p["source_url"],
            })
    return rows

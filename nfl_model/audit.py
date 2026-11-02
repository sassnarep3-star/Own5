"""Recheck frozen evidence, official links, reconciliations and derived-row provenance."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from .contracts import official_url


def load(root: Path, name: str) -> object:
    return json.loads((root / "data" / name).read_text())


def audit_data(root: Path) -> dict:
    failures: list[str] = []
    checks: list[str] = []
    sources = load(root, "source_register.json")
    facts = load(root, "verified_facts.json")
    snapshot = json.loads((root / "research/official_snapshot.json").read_text())
    reviews = load(root, "review_items.json")
    source_by_id = {s["id"]: s for s in sources}
    if len(source_by_id) != len(sources):
        failures.append("duplicate source IDs")
    for s in sources:
        if not official_url(s["url"]):
            failures.append(f"non-official source URL: {s['id']}")
        if s["evidence_file"]:
            path = root / s["evidence_file"]
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != s["evidence_sha256"]:
                failures.append(f"evidence hash mismatch: {s['id']}")
    checks.append(f"{len(sources)} official source URLs and excerpt hashes checked")
    fact_ids = set()
    for fact in facts:
        fid = fact["id"]
        if fid in fact_ids:
            failures.append(f"duplicate fact: {fid}")
        fact_ids.add(fid)
        if not fact["verified"] or not fact["source_urls"]:
            failures.append(f"unverified fact without flag: {fid}")
        for sid, url in zip(fact["source_ids"], fact["source_urls"]):
            # Schedule facts cite the exact official game link inside the S11 excerpt.
            per_game_link = fact["category"] == "Official schedule" and sid == "S11" and url in fact["evidence_line"]
            if sid not in source_by_id or (source_by_id[sid]["url"] != url and not per_game_link) or not official_url(url):
                failures.append(f"bad source linkage: {fid}")
        evidence = (root / fact["evidence_file"]).read_text()
        if fact["evidence_line"] not in evidence:
            failures.append(f"missing evidence line: {fid}")
        if fact.get("additional_evidence_line"):
            if fact["additional_evidence_line"] not in (root / fact["additional_evidence_file"]).read_text():
                failures.append(f"missing second evidence line: {fid}")
        values = fact["values"]
        if fid.startswith("team-"):
            c = [v.strip() for v in fact["evidence_line"].strip("|").split("|")][1:]
            expected = dict(wins=int(c[0]), losses=int(c[1]), ties=int(c[2]), points_for=int(c[4]), points_against=int(c[5]))
            if values != expected:
                failures.append(f"standings row mismatch: {fid}")
        elif fid.startswith("schedule-"):
            if values["local_time"] not in fact["evidence_line"] or values["broadcast"] not in fact["evidence_line"]:
                failures.append(f"schedule row mismatch: {fid}")
        elif fid.startswith("paired-"):
            b = [v.strip() for v in fact["evidence_line"].strip("|").split("|")]
            c = [v.strip() for v in fact["additional_evidence_line"].strip("|").split("|")]
            expected = dict(burrow_passing_yards=int(b[6]), chase_receptions=int(c[4]), chase_receiving_yards=int(c[5]))
            if values != expected:
                failures.append(f"player row mismatch: {fid}")
    checks.append(f"{len(facts)} fact rows checked against exact saved evidence")
    teams = snapshot["teams"]
    if len(teams) != 32 or len({t['team_code'] for t in teams}) != 32:
        failures.append("standings coverage mismatch")
    pf, pa = sum(t["points_for"] for t in teams), sum(t["points_against"] for t in teams)
    if pf != pa or pf != snapshot["reconciliation"]["team_points_for"]:
        failures.append("league points reconciliation failed")
    checks.append(f"league PF = PA = {pf}")
    if len(snapshot["schedule"]) != 15:
        failures.append("Week 9 coverage mismatch")
    participants = {t for g in snapshot["schedule"] for t in (g["home"], g["away"])}
    if len(participants) != 30 or participants | {"PIT", "TEN"} != {t["team_code"] for t in teams}:
        failures.append("schedule/bye coverage mismatch")
    checks.append("15 matchups + 2 bye teams cover all 32 teams")
    paired = snapshot["paired_player_games"]
    if len(paired) != 17:
        failures.append("paired game coverage mismatch")
    for g in paired:
        if g["evidence_lines"][0] not in (root / g["evidence_files"][0]).read_text():
            failures.append(f"missing Burrow evidence week {g['week']}")
        if g["evidence_lines"][1] not in (root / g["evidence_files"][1]).read_text():
            failures.append(f"missing Chase evidence week {g['week']}")
    if sum(g["burrow_passing_yards"] for g in paired) != 4918:
        failures.append("Burrow career reconciliation failed")
    if sum(g["chase_receiving_yards"] for g in paired) != 1708 or sum(g["chase_receptions"] for g in paired) != 127:
        failures.append("Chase career reconciliation failed")
    checks.append("17 paired games reconcile to official career controls")
    if snapshot["market_quotes"] or snapshot["settlement_events"]:
        failures.append("unexpected market/settlement records require separate verification")
    for item in reviews:
        if item["status"] != "needs review" or not item["source_urls"] or not all(official_url(u) for u in item["source_urls"]):
            failures.append(f"bad review linkage: {item['id']}")
    checks.append(f"{len(reviews)} review items carry official source links")
    lines_path = root / "data/derived_lines.json"
    if lines_path.exists():
        lines = json.loads(lines_path.read_text())
        if len(lines) != len(snapshot["schedule"]):
            failures.append("derived line coverage mismatch")
        for line in lines:
            if not line.get("derived") or not all(official_url(u) for u in line["source_urls"]):
                failures.append(f"derived line provenance missing: {line['game_id']}")
            if any(line[k] is not None for k in ("market_spread", "market_total", "market_american", "market_edge", "clv")):
                failures.append(f"unsupported market value: {line['game_id']}")
            if not 0 <= line["truncation_tail_mass"] < 1e-12:
                failures.append(f"excessive Poisson truncation: {line['game_id']}")
            total = line["home_win_probability"] + line["tie_probability"] + line["away_win_probability"]
            if abs(total - 1) > 1e-10:
                failures.append(f"probability mass mismatch: {line['game_id']}")
        checks.append(f"{len(lines)} derived lines: provenance, blank market fields and probability mass checked")
    return {"status": "pass" if not failures else "fail", "checks": checks, "failures": failures,
            "source_count": len(sources), "fact_rows": len(facts), "review_items": len(reviews),
            "snapshot_date": snapshot["retrieved_utc"]}

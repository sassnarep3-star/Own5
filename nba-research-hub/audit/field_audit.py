"""Compare selected inherited NBA fields with the hub's official-reviewed snapshot.

The hub snapshot was manually compared with re-opened NBA pages on 2026-11-05.
This script does not re-fetch the network; it records deterministic comparisons
against that frozen evidence. Unreviewed official values remain blank.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DATA = ROOT / "data"
AUDIT = ROOT / "audit"


def read(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num_eq(a: str, b: str) -> bool:
    try:
        return abs(float(a) - float(b)) <= 1e-6
    except ValueError:
        return a == b


def main() -> dict:
    teams = read(DATA / "team_snapshot.csv")
    team_key = {(t["season"], t["team_id"]): t for t in teams}
    abbr_id = {t["abbr"]: t["team_id"] for t in teams if t["season"] == "2026-27"}
    players = read(DATA / "player_games.csv")
    player_key = {(p["player_id"], p["game_id"]): p for p in players}
    edwards_key = {p["game_id"]: p for p in players if p["player_id"] == "1630162"}
    rows: list[dict] = []

    def add(path: str, line: int, field: str, claim: str, official: str, status: str, source: str, note: str) -> None:
        rows.append({
            "audit_id": f"A{len(rows)+1:05d}", "path": path, "line": line, "field": field,
            "repository_claim": claim, "official_value": official, "status": status,
            "source_url": source, "note": note,
        })

    # Prior NBA Signal Lab team tables: selected fields only.
    team_fields = [("gp", "gp"), ("w", "w"), ("l", "l"), ("win_pct", "win_pct"), ("pts_pg", "pts_pg"), ("plus_minus_pg", "plus_minus_pg")]
    for season_file, season in [("teams_2025_26.csv", "2025-26"), ("teams_2026_27.csv", "2026-27")]:
        path = f"nba-signal-lab/data/{season_file}"
        for line, row in enumerate(read(REPO / path), 2):
            official = team_key[(season, row["team_id"])]
            for old, new in team_fields:
                match = num_eq(row[old], official[new])
                status = "MATCH" if match else ("STALE" if season == "2026-27" else "MISMATCH")
                note = "Selected field matches official-reviewed snapshot." if match else ("Older Nov 3 snapshot differs from Nov 5 refresh; not a transcription error." if season == "2026-27" else "Unexpected mismatch; manual review.")
                add(path, line, old, row[old], official[new], status, official["source_url"], note)

    # NBA Desk team seasons: 2025-26/2026-27 selected fields; 2024-25 not re-verified.
    path = "nba-desk/data/team_seasons.csv"
    desk_fields = [("gp", "gp"), ("w", "w"), ("l", "l"), ("pts_pg", "pts_pg"), ("plus_minus_pg", "plus_minus_pg")]
    for line, row in enumerate(read(REPO / path), 2):
        tid = abbr_id.get(row["team"])
        official = team_key.get((row["season"], tid)) if tid else None
        for old, new in desk_fields:
            if official is None:
                add(path, line, old, row[old], "", "UNVERIFIED", row.get("source_url", ""), "Season/team not in official-reviewed hub snapshot; official value blank.")
            else:
                match = num_eq(row[old], official[new])
                status = "MATCH" if match else ("STALE" if row["season"] == "2026-27" else "MISMATCH")
                note = "Selected field matches official-reviewed snapshot." if match else ("Older snapshot differs from Nov 5 refresh." if row["season"] == "2026-27" else "Unexpected mismatch; manual review.")
                add(path, line, old, row[old], official[new], status, official["source_url"], note)

    # NBA Signal Lab player logs: all stored fields except display-name accent normalization.
    path = "nba-signal-lab/data/game_logs_2025_26.csv"
    compare_fields = ["player_id", "team", "game_date", "matchup", "game_id", "result", "min", "pts", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "oreb", "dreb", "reb", "ast", "stl", "blk", "tov", "pf", "plus_minus", "source_url"]
    for line, row in enumerate(read(REPO / path), 2):
        official = player_key.get((row["player_id"], row["game_id"]))
        for field in compare_fields:
            if official is None:
                add(path, line, field, row[field], "", "UNVERIFIED", row.get("source_url", ""), "Player-game not in official-reviewed hub sample.")
            else:
                match = num_eq(row[field], official[field]) if field not in {"team", "game_date", "matchup", "game_id", "result", "source_url", "player_id"} else row[field] == official[field]
                add(path, line, field, row[field], official[field], "MATCH" if match else "MISMATCH", official["official_page"], "Compared with re-opened official player table via hub snapshot.")

    # NBA 2026 lab Edwards sample: selected fields where game is in official-reviewed hub log.
    path = "data/nba-2026-27/player_logs_edwards.csv"
    mapping = [("game_id", "game_id"), ("game_date", "game_date"), ("result", "result"), ("min", "min"), ("pts", "pts"), ("fg3m", "tpm"), ("reb", "reb"), ("ast", "ast")]
    for line, row in enumerate(read(REPO / path), 2):
        official = edwards_key.get(row["game_id"])
        for old, new in mapping:
            if official is None:
                add(path, line, old, row[old], "", "UNVERIFIED", row.get("source_url", "https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26"), "Game not in official-reviewed hub sample.")
            else:
                match = num_eq(row[old], official[new]) if old not in {"game_id", "game_date", "result"} else row[old] == official[new]
                add(path, line, old, row[old], official[new], "MATCH" if match else "MISMATCH", official["official_page"], "Selected field compared with official-reviewed Edwards log.")

    # NBA Own Lines player sample: only Luka/Edwards rows are in the hub official-reviewed sample.
    path = "nba-own-lines/data/player_games.csv"
    mapping = [("player_id", "player_id"), ("game_id", "game_id"), ("date", "game_date"), ("matchup", "matchup"), ("result", "result"), ("minutes", "min"), ("pts", "pts"), ("reb", "reb"), ("ast", "ast"), ("threepm", "tpm")]
    for line, row in enumerate(read(REPO / path), 2):
        official = player_key.get((row["player_id"], row["game_id"]))
        for old, new in mapping:
            if official is None:
                add(path, line, old, row[old], "", "UNVERIFIED", row.get("source_url", "https://www.nba.com/stats/leaders?Season=2025-26"), "Player not in official-reviewed two-player hub sample; official value blank.")
            else:
                match = num_eq(row[old], official[new]) if old not in {"player_id", "game_id", "date", "matchup", "result"} else row[old] == official[new]
                add(path, line, old, row[old], official[new], "MATCH" if match else "MISMATCH", official["official_page"], "Selected field compared with official-reviewed hub log.")

    with (AUDIT / "field_audit.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    summary = {
        "field_comparisons": len(rows), "status_counts": counts,
        "files_compared": sorted({r["path"] for r in rows}),
        "field_audit_sha256": hashlib.sha256((AUDIT / "field_audit.csv").read_bytes()).hexdigest(),
        "note": "MATCH/STALE/MISMATCH use the hub snapshot manually checked against official NBA pages on 2026-11-05. UNVERIFIED official values are blank. This is not a network re-fetch.",
    }
    (AUDIT / "field_audit_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


if __name__ == "__main__":
    main()

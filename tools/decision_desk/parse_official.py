#!/usr/bin/env python3
"""Parse the official NFL.com pages saved by ``fetch_sources.py`` into CSVs.

Design rules:
* Only values that literally appear in the official HTML are emitted.
* A cell that cannot be located is left empty and flagged downstream; nothing
  is inferred, imputed or carried over from another dataset.
* Team attribution for an injury table uses the nearest preceding club name in
  the document ("closest preceding nickname"), which is how the page groups
  its tables.  Rows whose club cannot be resolved are emitted with an empty
  team and counted in the parse report.
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, ".work", "official")
OUT = os.path.join(ROOT, "data", "decision-desk", "official")

NICKNAMES = [
    "Cardinals", "Falcons", "Ravens", "Bills", "Panthers", "Bears", "Bengals",
    "Browns", "Cowboys", "Broncos", "Lions", "Packers", "Texans", "Colts",
    "Jaguars", "Chiefs", "Raiders", "Chargers", "Rams", "Dolphins", "Vikings",
    "Patriots", "Saints", "Giants", "Jets", "Eagles", "Steelers", "49ers",
    "Seahawks", "Buccaneers", "Titans", "Commanders",
]
PRACTICE = ["Did Not Participate In Practice", "Limited Participation in Practice",
            "Full Participation in Practice"]
GAME = ["Out", "Doubtful", "Questionable"]


def clean(s: str) -> str:
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?is)<br\s*/?>", " ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def table_rows(chunk: str) -> list[list[str]]:
    rows = []
    for tr in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", chunk):
        cells = re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr)
        rows.append([clean(c) for c in cells])
    return rows


def team_before(doc: str, pos: int) -> str:
    window = doc[max(0, pos - 20000):pos]
    best, best_at = "", -1
    for nick in NICKNAMES:
        # closest preceding mention wins; word-boundary, case-sensitive
        for m in re.finditer(r"\b" + re.escape(nick) + r"\b", window):
            if m.start() > best_at:
                best_at, best = m.start(), nick
    return best


def parse_injuries(doc: str) -> tuple[list[dict], list[str]]:
    rows, problems = [], []
    for m in re.finditer(r"(?is)<table[^>]*>(.*?)</table>", doc):
        chunk = m.group(0)
        trs = table_rows(chunk)
        if not trs or not any("Player" in c for c in trs[0]):
            continue
        team = team_before(doc, m.start())
        if not team:
            problems.append("injury table with unresolved team")
        for cells in trs[1:]:
            if len(cells) < 3 or not cells[0]:
                continue
            # cell order on nfl.com: Player | Position | Injuries | Practice Status | Game Status
            padded = cells + [""] * (5 - len(cells))
            rows.append({
                "team_nickname": team,
                "player": padded[0],
                "position": padded[1],
                "injury": padded[2],
                "practice_status": padded[3],
                "game_status": padded[4],
            })
    return rows, problems


def parse_standings(doc: str) -> tuple[list[dict], list[str]]:
    rows, problems = [], []
    for m in re.finditer(r"(?is)<table[^>]*>(.*?)</table>", doc):
        trs = table_rows(m.group(0))
        if not trs:
            continue
        header = " ".join(trs[0])
        if "Team" not in header or "PCT" not in header:
            continue
        for cells in trs[1:]:
            if len(cells) < 8 or not cells[0]:
                continue
            # Team | W | L | T | PCT | PF | PA | Net Pts | ...
            if not re.fullmatch(r"\d+", cells[1].replace(",", "")):
                continue
            rows.append({
                "team": cells[0],
                "w": cells[1], "l": cells[2], "t": cells[3], "pct": cells[4],
                "pf": cells[5], "pa": cells[6],
                "net_pts": cells[7] if len(cells) > 7 else "",
            })
    if not rows:
        problems.append("standings table not found")
    return rows, problems


def write_csv(path: str, rows: list[dict], fields: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    prov = json.load(open(os.path.join(ROOT, "data", "decision-desk", "raw", "provenance.json")))
    retrieved = prov["retrieved_utc"]
    urls = {p["name"]: p["url"] for p in prov["pages"]}
    report = {"retrieved_utc": retrieved, "pages": {}}

    inj_path = os.path.join(WORK, "injury_report_wk10.html")
    if os.path.exists(inj_path):
        doc = open(inj_path, encoding="utf-8", errors="replace").read()
        rows, problems = parse_injuries(doc)
        for r in rows:
            r["source_url"] = urls.get("injury_report_wk10", "https://www.nfl.com/injuries/")
            r["retrieved_utc"] = retrieved
        write_csv(os.path.join(OUT, "official_injuries_wk10.csv"), rows,
                  ["team_nickname", "player", "position", "injury",
                   "practice_status", "game_status", "source_url", "retrieved_utc"])
        report["pages"]["injury_report_wk10"] = {
            "rows": len(rows), "problems": problems,
            "teams": sorted({r["team_nickname"] for r in rows if r["team_nickname"]}),
            "with_game_status": sum(1 for r in rows if r["game_status"]),
            "sample": rows[:6],
        }
    else:
        report["pages"]["injury_report_wk10"] = {"rows": 0, "problems": ["missing html"]}

    st_path = os.path.join(WORK, "standings_reg_2026.html")
    if os.path.exists(st_path):
        doc = open(st_path, encoding="utf-8", errors="replace").read()
        rows, problems = parse_standings(doc)
        for r in rows:
            r["source_url"] = urls.get("standings_reg_2026", "https://www.nfl.com/standings/league/2026/REG")
            r["retrieved_utc"] = retrieved
        write_csv(os.path.join(OUT, "official_standings_2026.csv"), rows,
                  ["team", "w", "l", "t", "pct", "pf", "pa", "net_pts",
                   "source_url", "retrieved_utc"])
        report["pages"]["standings_reg_2026"] = {
            "rows": len(rows), "problems": problems, "sample": rows[:3]}
    else:
        report["pages"]["standings_reg_2026"] = {"rows": 0, "problems": ["missing html"]}

    with open(os.path.join(OUT, "parse_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print(json.dumps(report, indent=2)[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())

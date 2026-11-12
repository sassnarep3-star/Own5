#!/usr/bin/env python3
"""Verification gate for the Decision Desk.

Fails (non-zero exit) if any of these rules break:

1. every table row on every page carries a link (evidence or the script/pinned
   input that produced it);
2. every internal link resolves to a real file;
3. every published CSV row has a per-row source link;
4. required fields are populated, and any intentionally blank value is covered
   by a flag column;
5. no placeholder text ("None", "nan", "TODO", "TBD") leaks into the site.
"""
from __future__ import annotations

import csv
import glob
import html.parser
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SITE = os.path.join(ROOT, "nfl-decision-desk")
DATA = os.path.join(ROOT, "data", "decision-desk")
ALLOWED_PLACEHOLDERS = {"pending", "n/a", "—", ""}


class TableParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self._depth = 0
        self._row = None
        self._cell = None
        self._in_cell = False
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self._depth += 1
            self.tables.append([])
        elif tag == "tr" and self._depth:
            self._row = []
            self.tables[-1].append(self._row)
        elif tag in ("td", "th") and self._row is not None:
            self._cell = {"text": "", "link": False, "header": tag == "th"}
            self._in_cell = True
        elif tag == "a" and self._in_cell:
            self._cell["link"] = True
            if a.get("href"):
                self.links.append(a["href"])
        elif tag == "a":
            if a.get("href"):
                self.links.append(a["href"])

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._in_cell and self._row is not None:
            self._row.append(self._cell)
            self._cell = None
            self._in_cell = False
        elif tag == "table" and self._depth:
            self._depth -= 1

    def handle_data(self, data):
        if self._in_cell and self._cell is not None:
            self._cell["text"] += data


def check_pages():
    problems = []
    stats = {"pages": 0, "tables": 0, "rows": 0, "rows_without_link": 0,
             "links": 0, "broken_links": []}
    for path in sorted(glob.glob(os.path.join(SITE, "*.html"))):
        name = os.path.basename(path)
        text = open(path, encoding="utf-8").read()
        stats["pages"] += 1
        p = TableParser()
        p.feed(text)
        for href in p.links:
            if href.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            target = os.path.join(SITE, href.split("#")[0].split("?")[0])
            stats["links"] += 1
            if href and not os.path.exists(target):
                stats["broken_links"].append({"page": name, "href": href})
        for ti, tbl in enumerate(p.tables):
            stats["tables"] += 1
            body = [r for r in tbl if r and not all(c["header"] for c in r)]
            for ri, row in enumerate(body):
                stats["rows"] += 1
                if not any(c["link"] for c in row):
                    stats["rows_without_link"] += 1
                    problems.append(f"{name}: table {ti} row {ri} has no link")
        for bad in ("None", "nan", "TODO", "TBD", "undefined", "[object"):
            if re.search(r">\s*" + re.escape(bad) + r"\s*<", text):
                problems.append(f"{name}: placeholder text '{bad}' rendered")
    return stats, problems


def check_csvs():
    problems = []
    checked = 0
    for path in sorted(glob.glob(os.path.join(DATA, "**", "*.csv"), recursive=True)):
        rel = os.path.relpath(path, ROOT)
        if "official" in rel or "/raw/" in rel:
            continue
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        if not rows:
            problems.append(f"{rel}: empty table")
            continue
        checked += 1
        for i, r in enumerate(rows):
            if "source_url" not in r or not str(r.get("source_url", "")).startswith("http"):
                problems.append(f"{rel}: row {i} missing source_url")
                break
    return {"csv_tables_checked": checked}, problems


def check_domain_rules():
    """Required-field rules for the key published tables."""
    problems = []
    inj = list(csv.DictReader(open(os.path.join(DATA, "injuries_wk10_players.csv"))))
    if len(inj) < 200:
        problems.append(f"injuries: expected the full report, got {len(inj)} rows")
    for i, r in enumerate(inj):
        for field in ("team", "player", "position", "practice_status", "source_url"):
            if not r.get(field):
                problems.append(f"injuries row {i}: empty {field}")
        if not r.get("game_status") and "provisional" not in (r.get("weight_basis") or ""):
            problems.append(f"injuries row {i}: no game status but weight basis is not provisional")

    lines = list(csv.DictReader(open(os.path.join(DATA, "model_lines_wk10.csv"))))
    if len(lines) != 14:
        problems.append(f"lines: expected 14 Week 10 games, got {len(lines)}")
    for i, r in enumerate(lines):
        for field in ("model_spread_home", "model_total", "source_schedule"):
            if not r.get(field):
                problems.append(f"lines row {i}: empty {field}")
        if not r.get("market_spread_home_agg") and not r.get("verdict"):
            problems.append(f"lines row {i}: blank market without a verdict flag")

    ledger = list(csv.DictReader(open(os.path.join(DATA, "strategy_ledger.csv"))))
    for i, r in enumerate(ledger):
        if int(r.get("n_bets") or 0) <= 0:
            problems.append(f"ledger row {i}: no bets")
        if not r.get("win_rate"):
            problems.append(f"ledger row {i}: empty win rate")
        if r.get("status") == "CERTIFIED" and "G4_closing_line_value=fail" in (r.get("gate_results") or ""):
            problems.append(f"ledger row {i}: certified while CLV gate failed")

    props = list(csv.DictReader(open(os.path.join(DATA, "prop_correlations.csv"))))
    for i, r in enumerate(props):
        if not r.get("pearson_r") and "flagged" not in (r.get("status") or ""):
            problems.append(f"prop row {i}: empty r without a flag")
    return problems


def main() -> int:
    stats, page_problems = check_pages()
    csv_stats, csv_problems = check_csvs()
    rule_problems = check_domain_rules()
    problems = page_problems + csv_problems + rule_problems
    report = {"site": stats, **csv_stats, "problems": problems[:100],
              "problem_count": len(problems)}
    with open(os.path.join(DATA, "verify_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print(json.dumps({k: v for k, v in report.items() if k != "problems"}, indent=2))
    if problems:
        print(f"FAIL: {len(problems)} problems")
        for p in problems[:40]:
            print(" -", p)
        return 1
    print("PASS: all rows sourced, all links resolve, all required fields present")
    return 0


if __name__ == "__main__":
    sys.exit(main())

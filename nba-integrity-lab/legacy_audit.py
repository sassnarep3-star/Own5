#!/usr/bin/env python3
"""Inventory static HTML table rows in the immutable session-start tree.

This is a link-presence scan, not a factual/semantic audit. A matched domain
only identifies a plausible official context link; it does not prove that the
linked source contains or supports the row. Dynamic client-rendered rows and
non-HTML files are outside this scan.
"""
from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlparse

BASE = "54e8dee596d49731c3da535a1f77b01cd0c295d5"
ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data" / "legacy-audit.json"
# Conservative allowlist, not an exhaustive list of official publishers.
CONTEXT_DOMAINS = (
    "nba.com", "nfl.com", "nist.gov", "nih.gov", "mass.gov", "massgaming.com",
    "betmgm.com", "draftkings.com", "fanduel.com", "ncpgambling.org", "ncaa.org",
    "github.com", "cdc.gov", "gov.uk",
)


class TableScanner(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.table_depth = 0
        self.row = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.table_depth += 1
        elif tag == "tr" and self.table_depth and self.row is None:
            self.row = {"has_td": False, "links": []}
        elif tag == "td" and self.row is not None:
            self.row["has_td"] = True
        elif tag == "a" and self.row is not None:
            self.row["links"].append(dict(attrs).get("href", ""))

    def handle_endtag(self, tag):
        if tag == "tr" and self.row is not None:
            if self.row["has_td"]:
                self.rows.append(self.row)
            self.row = None
        elif tag == "table":
            self.table_depth = max(0, self.table_depth - 1)


def allowed_context(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return False
    return (parsed.scheme == "https" and
            any(host == d or host.endswith("." + d) for d in CONTEXT_DOMAINS))


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8")
    return result.stdout


def scan_base() -> dict:
    paths = [line for line in git("ls-tree", "-r", "--name-only", BASE).splitlines() if line.endswith(".html")]
    groups = defaultdict(lambda: {"pages": 0, "rows": 0, "missing_context_links": 0})
    files, findings = [], []
    for path in sorted(paths):
        parser = TableScanner()
        parser.feed(git("show", f"{BASE}:{path}"))
        group = path.split("/", 1)[0] if "/" in path else "(root)"
        groups[group]["pages"] += 1
        groups[group]["rows"] += len(parser.rows)
        missing = [i for i, row in enumerate(parser.rows, start=1)
                   if not any(allowed_context(href) for href in row["links"])]
        groups[group]["missing_context_links"] += len(missing)
        file_url = f"https://github.com/sassnarep3-star/Own5/blob/{BASE}/{quote(path, safe='/')}"
        files.append({"path": path, "group": group, "rows": len(parser.rows),
                      "missing_context_links": len(missing), "repo_url": file_url})
        for ordinal in missing:
            findings.append({"path": path, "row_ordinal": ordinal, "repo_url": file_url})
    return {"base_commit": BASE, "scope": "tracked static HTML in session-start commit",
            "allowlisted_domains": list(CONTEXT_DOMAINS),
            "groups": [{"group": name, **stats} for name, stats in sorted(groups.items())],
            "files": files, "findings": findings,
            "totals": {"pages": len(paths), "rows": sum(v["rows"] for v in groups.values()),
                       "missing_context_links": len(findings)}}


def write_audit() -> dict:
    result = scan_base()
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    result = write_audit()
    print(json.dumps(result["totals"], sort_keys=True))

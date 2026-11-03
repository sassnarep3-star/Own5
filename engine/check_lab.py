"""Integrity checks for the generated lab/ dashboard.

Fails loudly if:
  * an internal link or fragment does not resolve
  * a data table row that should carry a source link has none
  * a page is missing, empty, or contains an unrendered template artefact
  * a claimed "validated" status contradicts the gate results
  * an external source link is not https
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "lab"
OUT = ROOT / "data" / "empirical"

EXPECTED = [
    "index.html", "board.html", "leaderboard.html", "strategies.html",
    "correlations.html", "combos.html", "skill-luck.html", "gates.html",
    "verification.html", "executive-summary.html", "flagged.html", "sources.html",
]


class Doc(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
        self.rows = 0
        self.text: list[str] = []
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if tag == "tr":
            self.rows += 1
        if tag not in ("meta", "link", "br", "img", "input", "hr"):
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()

    def handle_data(self, data):
        self.text.append(data)


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []
    docs: dict[str, Doc] = {}

    for name in EXPECTED:
        p = LAB / name
        if not p.exists():
            failures.append(f"missing page: lab/{name}")
            continue
        raw = p.read_text(encoding="utf-8")
        if len(raw) < 1500:
            failures.append(f"suspiciously small page: lab/{name} ({len(raw)} bytes)")
        for artefact in ("{esc(", "{card(", "nan</td>", "None</td>", "TODO", "FIXME"):
            if artefact in raw:
                failures.append(f"unrendered artefact {artefact!r} in lab/{name}")
        d = Doc()
        d.feed(raw)
        docs[name] = d
        if d.stack:
            warnings.append(f"unclosed tags in lab/{name}: {d.stack[:5]}")

    # Internal links and fragments.
    n_internal = n_external = 0
    for name, d in docs.items():
        for href in d.links:
            u = urlparse(href)
            if u.scheme in ("http", "https"):
                n_external += 1
                if u.scheme != "https":
                    failures.append(f"insecure external link in {name}: {href}")
                continue
            if u.scheme in ("mailto", "tel", "data"):
                continue
            n_internal += 1
            path = unquote(u.path)
            target = (LAB / path).resolve() if path else (LAB / name)
            if not target.exists():
                failures.append(f"broken internal link in {name}: {href}")
                continue
            if u.fragment and target.suffix == ".html":
                td = docs.get(target.name)
                if td is None and target.parent == LAB:
                    td = Doc()
                    td.feed(target.read_text(encoding="utf-8"))
                if td is not None and u.fragment not in td.ids:
                    failures.append(f"broken fragment in {name}: {href}")

    # Every empirical table that promises a source must actually link one.
    for fn, col in [("correlations_empirical.csv", "source_url"),
                    ("prop_continuous_correlations.csv", "source_url"),
                    ("combo_fair_prices.csv", "source_url"),
                    ("combo_walk_forward.csv", "source_url"),
                    ("official_verification.csv", "source_url"),
                    ("current_power_ratings.csv", "source_url")]:
        p = OUT / fn
        if not p.exists():
            failures.append(f"missing empirical output: {fn}")
            continue
        df = pd.read_csv(p, keep_default_na=False)
        if col not in df.columns:
            failures.append(f"{fn}: no {col} column")
            continue
        bad = df[~df[col].astype(str).str.startswith("https://")]
        if len(bad):
            failures.append(f"{fn}: {len(bad)} rows without an https source link")

    # Gate/status consistency.
    gr = pd.read_csv(OUT / "gate_results.csv", keep_default_na=False)
    gate_cols = [f"G{i}" for i in range(1, 11)]
    for r in gr.itertuples():
        passed = all(str(getattr(r, c)) == "True" for c in gate_cols)
        if (r.status == "VALIDATED") != passed:
            failures.append(f"{r.strategy}: status contradicts gates")
    summary = json.loads((OUT / "gates_summary.json").read_text())
    if summary["validated"] != int((gr.status == "VALIDATED").sum()):
        failures.append("gates_summary.json disagrees with gate_results.csv")

    # The dashboard must not claim a profitable edge when nothing validated.
    if summary["validated"] == 0:
        idx = (LAB / "index.html").read_text(encoding="utf-8").lower()
        if "0 of" not in idx and "no strategy cleared" not in idx:
            failures.append("index.html does not state the zero-validated result")

    total_rows = sum(d.rows for d in docs.values())
    print("=== LAB SITE CHECK ===")
    print(f"  pages            : {len(docs)}/{len(EXPECTED)}")
    print(f"  table rows       : {total_rows}")
    print(f"  internal links   : {n_internal}")
    print(f"  external links   : {n_external}")
    print(f"  warnings         : {len(warnings)}")
    for w in warnings:
        print(f"    WARN {w}")
    print(f"  failures         : {len(failures)}")
    for f in failures:
        print(f"    FAIL {f}")
    print("ALL CHECKS PASSED" if not failures else "CHECKS FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

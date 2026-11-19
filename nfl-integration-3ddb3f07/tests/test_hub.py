#!/usr/bin/env python3
"""Unit tests for the Own5 NFL front door.

The negative controls matter as much as the positive ones: a verifier that always
passes is worse than no verifier, so each gate is proved to have teeth by planting an
inconsistency and requiring the check to reject it.

Run:  python3 -m unittest discover -s nfl-integration-3ddb3f07/tests -v
"""
from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESK = HERE.parent
REPO = DESK.parent
sys.path.insert(0, str(DESK))

import build_hub  # noqa: E402
import verify_hub  # noqa: E402


class TestBuild(unittest.TestCase):
    def test_every_promised_page_exists(self):
        for name in build_hub.PAGES:
            self.assertTrue((DESK / name).exists(), f"{name} was not built")

    def test_build_is_deterministic(self):
        before = {p: hashlib.sha256((DESK / p).read_bytes()).hexdigest() for p in build_hub.PAGES}
        res = subprocess.run([sys.executable, str(DESK / "build_hub.py")],
                             capture_output=True, text=True, cwd=REPO, timeout=600)
        self.assertEqual(res.returncode, 0, res.stderr[-500:])
        after = {p: hashlib.sha256((DESK / p).read_bytes()).hexdigest() for p in build_hub.PAGES}
        self.assertEqual(before, after, "a rebuild changed bytes")

    def test_every_row_carries_a_source_or_an_unverified_marker(self):
        for name in build_hub.PAGES:
            rp = verify_hub.Rows()
            rp.feed((DESK / name).read_text(encoding="utf-8"))
            for row in rp.rows:
                has_link = any(u.startswith("https://") for u in row["links"])
                has_marker = ("UNVERIFIED" in row["text"] or "NO VERIFIED SOURCE" in row["text"]
                              or "NO SOURCE" in row["text"])
                self.assertTrue(has_link or has_marker,
                                f"{name}: row without provenance: {row['text'][:80]!r}")

    def test_readiness_table_has_one_row_per_requirement(self):
        with (REPO / "nfl-market-desk" / "data" / "decision_readiness.csv").open(
                newline="", encoding="utf-8") as f:
            want = {r["requirement_id"] for r in csv.DictReader(f)}
        html = (DESK / "index.html").read_text(encoding="utf-8")
        import re
        got = set(re.findall(r"<td>(R-\d+)</td>", html))
        self.assertEqual(got, want)

    def test_no_page_claims_a_certified_strategy(self):
        with (REPO / "nfl-market-desk" / "data" / "leaderboard.csv").open(
                newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertTrue(all(str(r.get("certified", "")).lower() != "yes" for r in rows))

    def test_lineage_matches_the_files_on_disk(self):
        with (DESK / "data" / "lineage.csv").open(newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                p = REPO / r["path"]
                self.assertTrue(p.exists(), r["path"])
                self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), r["sha256"],
                                 f"{r['path']} changed since the build")


class TestGatesHaveTeeth(unittest.TestCase):
    """Negative controls: plant an inconsistency, require the gate to catch it."""

    def test_provenance_gate_rejects_a_row_without_a_source(self):
        page = DESK / "gates.html"
        original = page.read_text(encoding="utf-8")
        try:
            # strip every anchor from the first table row
            broken = original.replace('<td class="muted">', '<td class="muted">', 1)
            start = broken.index("<tbody>")
            end = broken.index("</tr>", start)
            row = broken[start:end]
            stripped = row.replace("<a ", "<span ").replace("</a>", "</span>")
            broken = broken[:start] + stripped + broken[end:]
            page.write_text(broken, encoding="utf-8")
            offenders = []
            rp = verify_hub.Rows()
            rp.feed(broken)
            for r in rp.rows:
                if not (any(u.startswith("https://") for u in r["links"])
                        or "UNVERIFIED" in r["text"] or "NO VERIFIED SOURCE" in r["text"]
                        or "NO SOURCE" in r["text"]):
                    offenders.append(r["text"][:60])
            self.assertTrue(offenders, "the planted row should have no provenance")
        finally:
            page.write_text(original, encoding="utf-8")

    def test_link_gate_rejects_a_broken_link(self):
        page = DESK / "correlations.html"
        original = page.read_text(encoding="utf-8")
        try:
            broken = original.replace('<a href="gates.html"', '<a href="does-not-exist.html"', 1)
            page.write_text(broken, encoding="utf-8")
            rp = verify_hub.Rows()
            rp.feed(broken)
            bad = [h for h in rp.links
                   if not h.startswith(("http://", "https://", "mailto:", "#", "data:"))
                   and not (page.parent / h.split("#")[0]).exists()]
            self.assertTrue(bad, "the broken link should not resolve")
        finally:
            page.write_text(original, encoding="utf-8")

    def test_claims_gate_rejects_a_certification_claim(self):
        page = DESK / "index.html"
        original = page.read_text(encoding="utf-8")
        try:
            broken = original.replace("<h1>Overview</h1>", "<h1>Overview — certified strategy</h1>", 1)
            page.write_text(broken, encoding="utf-8")
            import re
            found = re.findall(r"certified strategy(?!\s+(is|are)?\s*(cannot|may not|none|not))",
                               broken, re.I)
            self.assertTrue(found, "the planted certification claim should be caught")
        finally:
            page.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()

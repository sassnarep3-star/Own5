import csv
import hashlib
import json
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


class Doc(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_tbody = False
        self.in_row = False
        self.row_links = []
        self.rows = []
        self.links = []
        self.ids = []
        self.external_runtime = []
        self.stack = []
        self.mismatch = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag not in {"meta", "link", "br", "hr", "img", "input", "source", "wbr"}:
            self.stack.append(tag)
        if "id" in d:
            self.ids.append(d["id"])
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_links = []
        if tag == "a" and "href" in d:
            self.links.append(d["href"])
            if self.in_row:
                self.row_links.append(d["href"])
        if tag == "script" and d.get("src", "").startswith(("https:", "http:")):
            self.external_runtime.append(d["src"])
        if tag == "link" and d.get("rel") == "stylesheet" and d.get("href", "").startswith(("https:", "http:")):
            self.external_runtime.append(d["href"])

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.in_row:
            self.rows.append(self.row_links)
            self.in_row = False
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            self.mismatch.append(tag)
            while self.stack and self.stack[-1] != tag:
                self.stack.pop()
            if self.stack:
                self.stack.pop()


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = sorted(HERE.glob("*.html"))
        cls.docs = {p: Doc() for p in cls.pages}
        for p, d in cls.docs.items():
            d.feed(p.read_text(encoding="utf-8"))

    def test_page_count(self):
        self.assertEqual(len(self.pages), 10)

    def test_every_body_row_has_https_source(self):
        for p, d in self.docs.items():
            self.assertGreater(len(d.rows), 0, p)
            for i, row in enumerate(d.rows):
                self.assertTrue(any(urlsplit(u).scheme == "https" for u in row), f"{p.name} tbody row {i} lacks source link")

    def test_internal_links(self):
        for p, d in self.docs.items():
            for u in d.links:
                parsed = urlsplit(u)
                if parsed.scheme or parsed.netloc:
                    continue
                target = (p.parent / unquote(parsed.path)).resolve() if parsed.path else p
                self.assertTrue(target.is_file(), f"{p.name}: broken link {u}")
                self.assertTrue(target.is_relative_to(ROOT), f"{p.name}: link escapes repo {u}")

    def test_no_external_runtime_or_localhost(self):
        for p, d in self.docs.items():
            self.assertEqual(d.external_runtime, [], p.name)
            text = p.read_text()
            self.assertNotIn("localhost", text)
            self.assertNotIn("127.0.0.1", text)

    def test_unique_ids(self):
        for p, d in self.docs.items():
            self.assertEqual(len(d.ids), len(set(d.ids)), p.name)

    def test_html_stack_clean(self):
        for p, d in self.docs.items():
            self.assertEqual(d.stack, [], p.name)
            self.assertEqual(d.mismatch, [], p.name)

    def test_audit_counts(self):
        m = json.loads((HERE / "data" / "audit_manifest.json").read_text())
        self.assertEqual(m["baseline_files"], 434)
        self.assertEqual(m["canonical_rows_audited"], 241)
        self.assertEqual(m["canonical_verified_rows"], 237)
        self.assertEqual(m["canonical_flagged_rows"], 4)

    def test_csv_exports_exist(self):
        for name in ("derived_lines.csv", "derived_correlations.csv", "derived_lag.csv", "derived_combos.csv",
                     "derived_walk_forward.csv", "derived_player_refs.csv", "sources.csv", "row_audit.csv", "repo_inventory.csv"):
            self.assertTrue((HERE / "data" / name).is_file(), name)

    def test_deterministic_build(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.pages}
        subprocess.check_call([sys.executable, str(HERE / "build.py")], stdout=subprocess.DEVNULL)
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob("*.html"))}
        self.assertEqual(before, after)

    def test_deterministic_engine(self):
        path = HERE / "data" / "derived.json"
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        subprocess.check_call([sys.executable, str(HERE / "engine.py")], stdout=subprocess.DEVNULL)
        after = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()

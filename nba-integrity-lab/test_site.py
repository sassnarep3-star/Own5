import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

import build
import check
import legacy_audit

HERE = Path(__file__).resolve().parent


class SiteTests(unittest.TestCase):
    def test_all_pages_rows_and_local_links(self):
        result = check.check_site()
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["pages"], 10)
        self.assertGreaterEqual(result["data_rows"], 600)
        self.assertGreater(result["local_links"], 100)

    def test_every_generated_table_row_requires_official_context(self):
        with self.assertRaises(ValueError):
            build.table("test", "Test", "", ["Value"], [(["x"], [])])
        with self.assertRaises(ValueError):
            build.table("test", "Test", "", ["Value"], [(["x"], [("fake", "https://nba.com.evil.example")])])
        self.assertTrue(build.official_url("https://www.nba.com/stats/help/glossary"))
        self.assertFalse(build.official_url("http://www.nba.com/"))
        self.assertFalse(build.official_url("https://github.com.evil.example/"))

    def test_blank_values_remain_visibly_empty(self):
        markup = build.table("empty", "Empty", "", ["Unverified"], [([None], [("NBA", build.model.NBA_LOG)])])
        self.assertIn('<td class="missing" aria-label="Unverified: value unavailable"></td>', markup)
        parser = check.PageParser()
        parser.feed(markup)
        self.assertEqual(parser.empty_cells, [])

    def test_review_lists_every_missing_legacy_location(self):
        audit = json.loads((HERE / "data/legacy-audit.json").read_text(encoding="utf8"))
        self.assertEqual(audit["base_commit"], legacy_audit.BASE)
        self.assertEqual(audit["totals"], {"pages": 139, "rows": 2852, "missing_context_links": 369})
        self.assertEqual(len(audit["findings"]), audit["totals"]["missing_context_links"])
        self.assertEqual(sum(x["missing_context_links"] for x in audit["files"]), len(audit["findings"]))
        page = (HERE / "review.html").read_text(encoding="utf8")
        self.assertIn("not a semantic fact-check", page)
        self.assertIn("369", page)

    def test_legacy_audit_reproducible_from_pinned_git_tree(self):
        expected = json.loads((HERE / "data/legacy-audit.json").read_text(encoding="utf8"))
        self.assertEqual(legacy_audit.scan_base(), expected)

    def test_build_is_byte_reproducible(self):
        generated = [HERE / filename for filename, _, _ in build.NAV] + [HERE / "data/derived.json"]
        def digest():
            return {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in generated}
        before = digest()
        subprocess.run([sys.executable, str(HERE / "build.py")], cwd=HERE.parent, check=True, capture_output=True)
        self.assertEqual(before, digest())

    def test_zero_real_leaderboard_results_and_no_cash(self):
        text = (HERE / "leaderboard.html").read_text(encoding="utf8")
        self.assertIn("No active cash competition", text)
        self.assertIn("No automated entry or payout service exists", text)
        self.assertNotIn("$1,000", text)

    def test_context_link_scan_does_not_accept_spoofed_domains(self):
        self.assertTrue(legacy_audit.allowed_context("https://www.nba.com/stats"))
        self.assertFalse(legacy_audit.allowed_context("https://nba.com.example.org/"))
        self.assertFalse(legacy_audit.allowed_context("javascript:alert(1)"))


if __name__ == "__main__":
    unittest.main()

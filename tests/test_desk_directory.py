"""The NFL desk directory counts only what is on disk, and its links resolve (session 5c5f4aaf)."""
import csv
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bdd", ROOT / "tools" / "build_desk_directory.py")
bdd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bdd)


class DeskDirectoryTests(unittest.TestCase):
    def test_build_is_deterministic(self):
        a = bdd.build()
        b = bdd.build()
        self.assertEqual(a, b)

    def test_every_relative_link_resolves_from_the_directory_folder(self):
        page, _ = bdd.build()
        for href in re.findall(r'href="([^"#?]+)"', page):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            self.assertTrue((bdd.OUT_DIR / href).resolve().exists(), href)

    def test_flagged_counts_match_the_csv_on_disk(self):
        rows = bdd.collect()
        for r in rows:
            if not r["flagged_rows"]:
                continue
            path = ROOT / r["flagged_file"]
            with path.open(encoding="utf-8", newline="") as fh:
                data = [x for x in list(csv.reader(fh))[1:] if any(c.strip() for c in x)]
            self.assertEqual(int(r["flagged_rows"]), len(data), r["desk"])

    def test_non_nfl_folders_are_excluded(self):
        names = {r["desk"] for r in bdd.collect()}
        self.assertNotIn("sf-rent", names)
        self.assertNotIn("nba-desk", names)
        self.assertIn("nfl-desk-35a1feb2", names)


if __name__ == "__main__":
    unittest.main()

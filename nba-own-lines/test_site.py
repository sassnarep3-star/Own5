import unittest

from check import audit


class SiteTests(unittest.TestCase):
    def test_deterministic_site_links_and_row_sources(self):
        report = audit()
        self.assertEqual(report["pages"], 11)
        self.assertEqual(report["table_rows"], 199)
        self.assertEqual(report["lines"], 16)
        self.assertEqual(report["qualified"], 0)


if __name__ == "__main__":
    unittest.main()

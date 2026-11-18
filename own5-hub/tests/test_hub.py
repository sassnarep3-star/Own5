"""Unit tests for the Own5 hub parser and the committed official capture (stdlib unittest)."""
import glob, os, sys, unittest
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from parse_injuries import parse_file, parse_injury_html  # noqa: E402

RAW = sorted(glob.glob(os.path.join(HERE, "captures", "raw", "injuries", "*.html.gz")))


class ParserTests(unittest.TestCase):
    def test_committed_capture_structure(self):
        self.assertTrue(RAW, "no raw injury capture committed")
        rows, n_tables = parse_file(RAW[-1])
        self.assertEqual(n_tables, 28)
        self.assertEqual(len(rows), 347)

    def test_lions_designations_are_out(self):
        rows, _ = parse_file(RAW[-1])
        lions = {r["player"]: r for r in rows if r["team"] == "Lions"}
        for name in ["Kerby Joseph", "Cade Mays", "D.J. Reed"]:
            self.assertEqual(lions[name]["game_status"], "Out", name)

    def test_drift_alarm_on_wrong_structure(self):
        with self.assertRaises(ValueError):
            parse_injury_html("<html><body><p>no tables here</p></body></html>")

    def test_wrong_cell_count_raises(self):
        html = ('<div class="d3-o-section-sub-title"><span>Test</span></div><table><thead><tr>'
                '<th>Player</th><th>Position</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th>'
                '</tr></thead><tbody><tr><td>A</td><td>B</td></tr></tbody></table>')
        with self.assertRaises(ValueError):
            parse_injury_html(html)


if __name__ == "__main__":
    unittest.main()

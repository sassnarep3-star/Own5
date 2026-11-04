#!/usr/bin/env python3
"""Tests for the NBA Signal Lab pipeline (session 6d508fee).

Run standalone:  python3 nba-signal-lab/test_lab.py
(or)             cd nba-signal-lab && python3 -m unittest test_lab -v
"""
import hashlib, json, os, re, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(DATA, "outputs.json")) as f:
            cls.out = json.load(f)

    # ---------- determinism ----------
    def test_compute_is_deterministic(self):
        before = sha(os.path.join(DATA, "outputs.json"))
        subprocess.run([sys.executable, os.path.join(HERE, "compute.py")],
                       check=True, capture_output=True)
        after = sha(os.path.join(DATA, "outputs.json"))
        self.assertEqual(before, after)

    def test_build_is_deterministic(self):
        htmls = [f for f in os.listdir(HERE) if f.endswith(".html")]
        before = {f: sha(os.path.join(HERE, f)) for f in htmls}
        subprocess.run([sys.executable, os.path.join(HERE, "build.py")],
                       check=True, capture_output=True)
        after = {f: sha(os.path.join(HERE, f)) for f in htmls}
        self.assertEqual(before, after)

    # ---------- verification layer ----------
    def test_all_verification_checks_pass(self):
        fails = [c for c in self.out["verification"]["checks"] if not c["ok"]]
        self.assertEqual(fails, [], f"verification failures: {fails}")

    def test_game_log_checksums_match_official(self):
        self.assertTrue(self.out["checksum_rows"])
        for c in self.out["checksum_rows"]:
            self.assertTrue(c["ok"], f"checksum failed for {c['player']}")

    def test_game_log_identities(self):
        import csv
        with open(os.path.join(DATA, "game_logs_2025_26.csv"), newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 125)
        for r in rows:
            pts = 2*(int(r["fgm"])-int(r["tpm"])) + 3*int(r["tpm"]) + int(r["ftm"])
            self.assertEqual(pts, int(r["pts"]), r)
            self.assertEqual(int(r["oreb"])+int(r["dreb"]), int(r["reb"]), r)

    # ---------- source-link coverage ----------
    def test_every_data_row_has_official_source(self):
        import csv
        for name, needle in [("teams_2026_27.csv", "nba.com"),
                             ("teams_2025_26.csv", "nba.com"),
                             ("standings_2026_27.csv", "nba.com"),
                             ("standings_2025_26.csv", "nba.com"),
                             ("game_logs_2025_26.csv", "nba.com/game/"),
                             ("schedule_2026_11_04.csv", "nba.com"),
                             ("players_registry.csv", "nba.com")]:
            with open(os.path.join(DATA, name), newline="") as f:
                rows = list(csv.DictReader(f))
            self.assertTrue(rows, name)
            for r in rows:
                self.assertIn(needle, r["source_url"], f"{name}: {r}")

    def test_every_html_table_row_links_a_source(self):
        """Row-level rule: each rendered table row ends in a source link or the
        explicit BLANK — UNVERIFIED marker."""
        for fname in ("data-verified.html", "model-lines.html", "analysis.html"):
            with open(os.path.join(HERE, fname)) as f:
                doc = f.read()
            rows = re.findall(r"<tr>.*?</tr>", doc, re.S)
            data_rows = [r for r in rows if "<td>" in r]
            self.assertTrue(data_rows, fname)
            for r in data_rows:
                ok = ('href="https://www.nba.com' in r or 'href="http' in r
                      or "BLANK — UNVERIFIED" in r)
                self.assertTrue(ok, f"{fname}: row without source link: {r[:160]}")

    # ---------- blank + flag discipline ----------
    def test_market_columns_are_blank(self):
        for g in self.out["model_lines"]:
            self.assertIsNone(g["market_spread"])
            self.assertIsNone(g["market_total"])
        self.assertIn("BLANK — UNVERIFIED", open(os.path.join(HERE, "model-lines.html")).read())

    def test_prize_pool_is_blank_and_flagged(self):
        self.assertIsNone(self.out["leaderboard"]["prize_pool"])
        flagged = open(os.path.join(HERE, "flagged.html")).read()
        self.assertIn("prize pool", flagged.lower())

    def test_no_strategy_certified(self):
        for s in self.out["strategies"]:
            self.assertFalse(s["certified"])
            self.assertEqual(s["status"], "PENDING")
        self.assertEqual(self.out["leaderboard"]["certified_count"], 0)

    def test_flagged_page_lists_every_flag(self):
        flagged = open(os.path.join(HERE, "flagged.html")).read()
        for f in self.out["flags"]:
            self.assertIn(f["id"], flagged, f"flag {f['id']} missing from flagged.html")

    # ---------- structure ----------
    def test_all_pages_exist(self):
        for fname in ("index.html", "executive-summary.html", "model-lines.html",
                      "correlations.html", "strategies.html", "luck-vs-skill.html",
                      "leaderboard.html", "data-verified.html", "analysis.html",
                      "verification.html", "flagged.html", "style.css"):
            self.assertTrue(os.path.exists(os.path.join(HERE, fname)), fname)

    def test_correlation_blocks_present(self):
        c = self.out["correlations"]
        self.assertEqual(len(c["stat_pairs"]), 7)
        self.assertEqual(len(c["prop_thresholds"]), 5)
        self.assertEqual(len(c["lag1_pts"]), 2)
        for lag in c["lag1_pts"]:
            self.assertLessEqual(lag["ci95"][0], 0)
            self.assertGreaterEqual(lag["ci95"][1], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

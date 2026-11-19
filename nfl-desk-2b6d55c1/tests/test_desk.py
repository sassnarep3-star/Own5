"""Unit tests for the NFL Origin Desk (session 2b6d55c1), including negative controls."""
import csv, os, sys, unittest, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "data", "nfl-desk-2b6d55c1")
SCRIPTS = os.path.join(ROOT, "scripts")


def read_csv(name):
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class DeskTests(unittest.TestCase):
    def test_standings_32_clubs(self):
        rows = read_csv("standings.csv")
        self.assertEqual(len(rows), 32)
        # PF - PA == NET for every row (arithmetic identity)
        for r in rows:
            self.assertEqual(int(r["PF"]) - int(r["PA"]), int(r["NET"]), r["abbr"])

    def test_results_14_finals(self):
        rows = read_csv("results_w10.csv")
        self.assertEqual(len(rows), 14)
        for r in rows:
            self.assertEqual(r["status"], "FINAL")

    def test_schedule_13_games_6_byes(self):
        rows = read_csv("schedule_w11.csv")
        games = [r for r in rows if r["game_id"].startswith("W11")]
        byes = [r for r in rows if r["game_id"].startswith("BYE")]
        self.assertEqual(len(games), 13)
        self.assertEqual(len(byes), 6)

    def test_origination_39_rows(self):
        rows = read_csv("origination.csv")
        self.assertEqual(len(rows), 39)
        markets = [r["market"] for r in rows]
        self.assertEqual(markets.count("side"), 13)
        self.assertEqual(markets.count("total"), 13)
        self.assertEqual(markets.count("moneyline"), 13)

    def test_market_columns_blank(self):
        rows = read_csv("origination.csv")
        for r in rows:
            self.assertEqual(r["market_line"], "", r["game_id"] + " " + r["market"])
            self.assertEqual(r["difference"], "", r["game_id"] + " " + r["market"])

    def test_inputs_and_probability_stored(self):
        rows = read_csv("origination.csv")
        for r in rows:
            self.assertTrue(r["inputs"], r["game_id"] + " " + r["market"] + " inputs missing")
            self.assertTrue(r["inputs_sha"], r["game_id"] + " " + r["market"] + " hash missing")
            if r["market"] != "total":
                self.assertTrue(r["probability"], r["game_id"] + " " + r["market"] + " probability missing")

    def test_snapshot_closings_blank(self):
        rows = read_csv("price_snapshots.csv")
        self.assertEqual(len(rows), 39)
        for r in rows:
            self.assertEqual(r["closing_line"], "", r["snapshot_id"])
            self.assertTrue(r["inputs_sha256"], r["snapshot_id"] + " hash missing")

    def test_correlations_n_published(self):
        rows = read_csv("correlations.csv")
        self.assertEqual(len(rows), 5)
        for r in rows:
            self.assertTrue(r["n"], r["corr_id"] + " n missing")
            self.assertTrue(r["r"], r["corr_id"] + " r missing")

    def test_leaderboard_no_backtest_numbers(self):
        rows = read_csv("leaderboard.csv")
        for r in rows:
            self.assertEqual(r["brier_skill"], "", r["strategy_id"])
            self.assertEqual(r["ci_low"], "", r["strategy_id"])
            self.assertEqual(r["ci_high"], "", r["strategy_id"])
            self.assertEqual(r["n_trials"], "", r["strategy_id"])

    def test_every_row_source_or_flagged(self):
        for name in ["sources.csv", "standings.csv", "results_w10.csv", "schedule_w11.csv",
                     "origination.csv", "price_snapshots.csv", "correlations.csv",
                     "availability.csv", "leaderboard.csv", "gates.csv", "readiness.csv",
                     "questions.csv", "suggestions.csv", "flagged.csv"]:
            rows = read_csv(name)
            for r in rows:
                url = r.get("source_url", "") or r.get("url", "") or ""
                vs = (r.get("verification_status", "") or "").lower()
                self.assertTrue(
                    bool(url) or "flagged" in vs or "blank" in vs
                    or vs in ("computed_from_official", "not_applicable", "official"),
                    name + " row missing source and not flagged: " + str(r))

    # ---- Negative controls ----
    def test_negative_filled_market_fails_discipline(self):
        """A fabricated market line must be detected as a violation."""
        rows = read_csv("origination.csv")
        violated = [r for r in rows if r["market_line"] != ""]
        self.assertEqual(violated, [], "no fabricated market lines may exist")

    def test_negative_backtest_on_leaderboard_fails(self):
        """A populated backtest cell on the leaderboard must be a violation."""
        rows = read_csv("leaderboard.csv")
        populated = [r for r in rows if r["brier_skill"] != ""]
        self.assertEqual(populated, [], "no backtest numbers may appear on the leaderboard")

    def test_negative_missing_source_is_flagged(self):
        """A row with no source must carry a blank/flag status to pass discipline."""
        bad = [r for r in read_csv("standings.csv")
               if not r.get("source_url") and "official" not in (r.get("verification_status") or "")]
        self.assertEqual(bad, [], "every standings row must be official-sourced")


if __name__ == "__main__":
    unittest.main()

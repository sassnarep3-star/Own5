import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("price_store",ROOT/"store.py")
store=importlib.util.module_from_spec(spec);spec.loader.exec_module(store)

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old_data=store.DATA
        store.DATA=Path(self.tmp.name)
        store.initialize()
    def tearDown(self):
        store.DATA=self.old_data;self.tmp.cleanup()
    def price(self,phase="opening",capture="2026-11-14T15:00:00Z"):
        return {"origin_id":"OR-01","event_id":"EV-01","market_type":"side","market_id":"spread-home","selection_id":"HOME","phase":phase,"line":"-2.5","odds_american":"-110","book":"EXAMPLE","jurisdiction":"XX","captured_at_utc":capture,"source_updated_at_utc":"","source_url":"https://sportsbook.fanduel.com/navigation/nfl","source_hash_sha256":"","verified_status":"verified","flag_id":""}
    def settlement(self, result="won"):
        return {"origin_id":"OR-01","event_id":"EV-01","market_type":"side","market_id":"spread-home","selection_id":"HOME","settlement":result,"settled_at_utc":"2026-11-14T23:00:00Z","book":"EXAMPLE","jurisdiction":"XX","rules_url":"https://www.fanduel.com/fanduel-sportsbook-house-rules-in","source_url":"https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1","source_hash_sha256":"","verified_status":"verified","flag_id":""}
    def bet(self):
        return {"bet_id":"BET-1","origin_id":"OR-01","event_id":"EV-01","market_id":"spread-home","selection_id":"HOME","book":"EXAMPLE","jurisdiction":"XX","stake_units":"2","accepted_odds_american":"150","accepted_price_source_url":"https://sportsbook.fanduel.com/navigation/nfl"}
    def test_append_open_close_and_prevent_duplicate(self):
        store.append_price(self.price())
        store.append_price(self.price("closing","2026-11-14T20:00:00Z"))
        with self.assertRaisesRegex(store.StoreError,"duplicate"):
            store.append_price(self.price())
        with (store.DATA/"price_snapshots.csv").open(newline="") as f:rows=list(csv.DictReader(f))
        self.assertEqual([r["phase"] for r in rows],["opening","closing"])
        self.assertEqual(store.audit_snapshot_pairs(rows),[])
        self.assertEqual(store.audit_snapshot_pairs(rows[:1])[0]["missing_phases"],"closing")
    def test_rejects_naive_datetime(self):
        with self.assertRaisesRegex(store.StoreError,"explicitly UTC"):
            store.append_price(self.price(capture="2026-11-14T15:00:00"))
    def test_rejects_unlinked_quote(self):
        row=self.price();row["source_url"]=""
        with self.assertRaisesRegex(store.StoreError,"required price fields"):
            store.append_price(row)
    def test_rejects_unknown_market_and_zero_odds(self):
        row=self.price();row["market_type"]="guess"
        with self.assertRaisesRegex(store.StoreError,"unsupported market_type"):
            store.append_price(row)
        row=self.price();row["odds_american"]="0"
        with self.assertRaisesRegex(store.StoreError,"non-zero"):
            store.append_price(row)
    def test_roi_reconciles_results_and_prices(self):
        rows=[{"verified_status":"verified","settlement_source_url":"https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1","accepted_price_source_url":"https://sportsbook.fanduel.com/navigation/nfl","rules_url":"https://www.fanduel.com/fanduel-sportsbook-house-rules-in","settlement":"won","stake_units":"2","accepted_odds_american":"150","net_return_units":"3"},
              {"verified_status":"verified","settlement_source_url":"https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1","accepted_price_source_url":"https://sportsbook.fanduel.com/navigation/nfl","rules_url":"https://www.fanduel.com/fanduel-sportsbook-house-rules-in","settlement":"lost","stake_units":"1","accepted_odds_american":"-110","net_return_units":"-1"}]
        out=store.evaluate(rows)
        self.assertEqual(out["bets"],2);self.assertEqual(out["net_units"],2);self.assertAlmostEqual(out["roi_pct"],200/3)
    def test_rejects_unverified_roi_and_mismatched_return(self):
        row={"verified_status":"unverified","settlement_source_url":"https://www.nfl.com/games/x","accepted_price_source_url":"https://sportsbook.fanduel.com/navigation/nfl","rules_url":"https://www.fanduel.com/fanduel-sportsbook-house-rules-in","settlement":"won","stake_units":"1","accepted_odds_american":"100"}
        with self.assertRaisesRegex(store.StoreError,"refusing to calculate ROI"):
            store.evaluate([row])
        row["verified_status"]="verified";row["net_return_units"]="0"
        with self.assertRaisesRegex(store.StoreError,"does not reconcile"):
            store.evaluate([row])
    def test_settlement_requires_rules_and_verified_grade_joins_exact_market(self):
        with self.assertRaisesRegex(store.StoreError,"required settlement fields"):
            store.append_settlement({"origin_id":"x"})
        store.append_settlement(self.settlement())
        store.append_graded_bet(self.bet())
        with (store.DATA/"graded_bets.csv").open(newline="") as f: rows=list(csv.DictReader(f))
        self.assertEqual(rows[0]["net_return_units"],"3")
        self.assertEqual(store.evaluate(rows)["roi_pct"],150)
        with self.assertRaisesRegex(store.StoreError,"duplicate bet_id"):
            store.append_graded_bet(self.bet())
    def test_grade_refuses_when_settlement_is_missing(self):
        with self.assertRaisesRegex(store.StoreError,"exactly one verified market settlement"):
            store.append_graded_bet(self.bet())
    def test_legacy_quote_prices_are_left_blank_and_flagged(self):
        import subprocess,sys
        subprocess.run([sys.executable,str(ROOT/"seed_quotes.py")],check=True)
        with (ROOT/"data/unclassified_market_quotes.csv").open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),28)
        price_cols=("away_spread","away_spread_american_odds","home_spread","home_spread_american_odds","total_points","over_american_odds","under_american_odds","away_moneyline_american","home_moneyline_american")
        self.assertTrue(all(not any(r[c] for c in price_cols) and not r["retrieved_time_utc"] and r["flag_id"] in {"F01","F07"} for r in rows))
    def test_seeded_feed_source_checks(self):
        import subprocess,sys
        subprocess.run([sys.executable,str(ROOT/"seed_results.py")],check=True)
        with (ROOT/"data/official_results.csv").open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),136)
        self.assertTrue(all(r["official_source_url"].startswith("https://www.nfl.com/games/") for r in rows))

if __name__=="__main__":unittest.main()

import unittest

from nfl_model.contracts import official_url, validate_forecast, validate_market_quote, validate_settlement


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.ids = {"S10"}
        self.quote = dict(game_id="test", market="spread", selection="home", line=-3.5,
                          decimal_price=1.91, quote_timestamp="2026-11-08T16:00:00Z",
                          kickoff_timestamp="2026-11-08T18:00:00Z", bookmaker="example-official-operator",
                          jurisdiction="test", rule_version="test-v1", source_id="S10",
                          source_url="https://www.nfl.com/standings/league/2026/REG")
        self.forecast = dict(game_id="test", market="spread", selection="home", probability=0.55,
                             forecast_timestamp="2026-11-08T16:01:00Z",
                             feature_cutoff_timestamp="2026-11-08T15:59:00Z",
                             kickoff_timestamp="2026-11-08T18:00:00Z", model_version="test",
                             config_sha256="abc", source_ids=["S10"])

    def test_official_url_allowlist(self):
        self.assertTrue(official_url("https://www.nfl.com/standings"))
        self.assertTrue(official_url("https://support.fanduel.com/s/article/test"))
        self.assertFalse(official_url("https://nfl.com.evil.example/test"))
        self.assertFalse(official_url("http://www.nfl.com/test"))
        self.assertFalse(official_url("https://random-blog.example/test"))

    def test_valid_quote_and_forecast(self):
        self.assertEqual(validate_market_quote(self.quote, self.ids), [])
        self.assertEqual(validate_forecast(self.forecast, self.ids), [])

    def test_missing_price_never_imputed(self):
        self.quote["decimal_price"] = None
        self.assertIn("missing decimal_price", validate_market_quote(self.quote, self.ids))

    def test_leakage_rejected(self):
        self.forecast["feature_cutoff_timestamp"] = "2026-11-08T19:00:00Z"
        self.assertIn("require feature_cutoff <= forecast < kickoff", validate_forecast(self.forecast, self.ids))
        self.quote["quote_timestamp"] = self.quote["kickoff_timestamp"]
        self.assertIn("quote must precede kickoff", validate_market_quote(self.quote, self.ids))

    def test_timezone_required(self):
        self.forecast["forecast_timestamp"] = "2026-11-08T16:01:00"
        self.assertTrue(validate_forecast(self.forecast, self.ids))

    def test_unknown_source_rejected(self):
        self.quote["source_id"] = "S999"
        self.assertIn("unknown source_id", validate_market_quote(self.quote, self.ids))

    def test_settlement_requires_official_source(self):
        settlement = dict(ticket_id="test", operator="test", rule_version="v1", outcome="win",
                          stake=1, profit=0.91, source_id="S10", source_url="https://www.nfl.com/games/test")
        self.assertEqual(validate_settlement(settlement, self.ids), [])
        settlement["source_url"] = "https://example.com/not-official"
        self.assertTrue(validate_settlement(settlement, self.ids))


if __name__ == "__main__":
    unittest.main()

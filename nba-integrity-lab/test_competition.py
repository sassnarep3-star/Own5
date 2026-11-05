import unittest

import competition
import test_model


class CompetitionTests(unittest.TestCase):
    def sample(self, name="S01", division="single"):
        # Synthetic fixtures test software mechanics only. They are not NBA
        # results, bookmaker quotes, a real confidence bound, or a real prize.
        evidence = test_model.GateTests().valid_attestation()
        evidence.update({"clustered_score_lower_bound": .01, "clustered_bound_reviewed": True})
        forecasts = []
        for i in range(200):
            forecasts.append({"forecast_id": f"f{i}", "event_id": f"e{i}",
                              "feature_cutoff": "2026-11-05T18:00:00Z", "quote_time": "2026-11-05T19:00:00Z",
                              "decision_time": "2026-11-05T19:01:00Z", "event_time": "2026-11-06T00:00:00Z",
                              "quote_url": "https://sportsbook.draftkings.com/same-game-parlay",
                              "outcome_url": "https://www.nba.com/games", "source_attestations_reviewed": True,
                              "decimal_odds": 1.91, "outcome": 1 if i % 5 < 3 else 0,
                              "model_p": .6, "benchmark_p": .5})
        return {"strategy_id": name, "division": division, "evidence": evidence, "forecasts": forecasts}

    def test_empty_competition_has_no_winners(self):
        self.assertEqual(competition.rank_entries([]), {"ranked": [], "blocked": []})

    def test_synthetic_eligible_entry_only_gets_proposed_non_cash_badge(self):
        result = competition.rank_entries([self.sample()])
        self.assertEqual(result["blocked"], [])
        self.assertEqual(result["ranked"][0]["rank"], 1)
        self.assertEqual(result["ranked"][0]["proposed_badge"], "Gold research badge")
        self.assertIsNone(result["ranked"][0]["cash_amount"])

    def test_duplicate_forecast_and_missing_bound_block(self):
        entry = self.sample()
        entry["forecasts"][1]["forecast_id"] = entry["forecasts"][0]["forecast_id"]
        self.assertEqual(len(competition.rank_entries([entry])["ranked"]), 0)
        entry = self.sample()
        entry["evidence"]["clustered_bound_reviewed"] = False
        self.assertEqual(len(competition.rank_entries([entry])["ranked"]), 0)

    def test_one_missing_gate_blocks(self):
        entry = self.sample()
        entry["evidence"]["independent_replication"] = False
        self.assertEqual(len(competition.rank_entries([entry])["ranked"]), 0)

    def test_future_quote_or_wrong_source_blocks(self):
        entry = self.sample()
        entry["forecasts"][0]["quote_time"] = "2026-11-06T01:00:00Z"
        self.assertEqual(len(competition.rank_entries([entry])["ranked"]), 0)
        entry = self.sample()
        entry["forecasts"][0]["quote_url"] = "https://draftkings.com.evil.example/"
        self.assertEqual(len(competition.rank_entries([entry])["ranked"]), 0)

    def test_forecast_before_holdout_blocks(self):
        entry = self.sample()
        entry["forecasts"][0].update({"feature_cutoff": "2026-10-30T18:00:00Z", "quote_time": "2026-10-30T19:00:00Z",
                                      "decision_time": "2026-10-30T19:01:00Z", "event_time": "2026-10-31T00:00:00Z"})
        self.assertEqual(len(competition.rank_entries([entry])["ranked"]), 0)

    def test_ties_are_deterministic_and_cash_is_never_assigned(self):
        result = competition.rank_entries([self.sample("B"), self.sample("A")])
        self.assertEqual([x["strategy_id"] for x in result["ranked"]], ["A", "B"])
        self.assertTrue(all(x["cash_amount"] is None for x in result["ranked"]))
        self.assertEqual(result["ranked"][1]["proposed_badge"], "Silver research badge")

    def test_trial_count_includes_submitted_candidates(self):
        first, second = self.sample("A"), self.sample("B")
        first["evidence"]["registered_trials"] = 1
        result = competition.rank_entries([first, second])
        self.assertEqual([r["strategy_id"] for r in result["ranked"]], ["B"])
        self.assertEqual([r["strategy_id"] for r in result["blocked"]], ["A"])

    def test_different_divisions_are_ranked_separately(self):
        result = competition.rank_entries([self.sample("A"), self.sample("B", "player prop")])
        self.assertEqual([r["rank"] for r in result["ranked"]], [1, 1])


if __name__ == "__main__":
    unittest.main()

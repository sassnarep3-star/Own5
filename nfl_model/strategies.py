"""Frozen strategy registry. No post-holdout parameter search."""
from __future__ import annotations

from .validation import evaluate_gates

REGISTRY = [
    {"id": "ST01", "name": "Points-rating singles", "category": "Single bet",
     "signal": "Shrunken PF/PA ratings versus a verified market; require ≥3 pp probability edge and ≥2.5 points spread disagreement.",
     "parameters": {"shrinkage_pseudogames": 8, "min_probability_edge": 0.03, "min_spread_disagreement": 2.5},
     "source_ids": ["S10", "S16"], "blockers": ["R01", "R03", "R05"]},
    {"id": "ST02", "name": "Total-distribution singles", "category": "Single bet",
     "signal": "Full score distribution versus both operator total prices; require ≥4 pp edge with explicit push mass.",
     "parameters": {"min_probability_edge": 0.04, "max_score_truncated": 100},
     "source_ids": ["S06", "S10", "S17"], "blockers": ["R01", "R03", "R05"]},
    {"id": "ST03", "name": "Cross-game two-leg parlay", "category": "Parlay",
     "signal": "Two distinct games with no shared team; model residual dependence and require ≥5 pp joint edge.",
     "parameters": {"legs": 2, "min_joint_edge": 0.05, "shared_team_allowed": False},
     "source_ids": ["S10", "S11", "S16"], "blockers": ["R01", "R03", "R11"]},
    {"id": "ST04", "name": "QB–WR same-game combo", "category": "Player-prop combo",
     "signal": "Historical Burrow passing ≥250 and Chase receiving ≥75; direct joint frequency, never an independence assumption.",
     "parameters": {"passing_yards_threshold": 250, "receiving_yards_threshold": 75, "historical_season": 2024},
     "source_ids": ["S09", "S12", "S13"], "blockers": ["R02", "R03", "R04", "R10", "R11"]},
    {"id": "ST05", "name": "Role-stability player props", "category": "Player prop",
     "signal": "Verified targets, routes, snap share, opponent allowance and participation; training-only shrinkage.",
     "parameters": {"min_verified_role_games": 8, "tracking_required": True},
     "source_ids": ["S08", "S09"], "blockers": ["R02", "R03", "R05"]},
    {"id": "ST06", "name": "Market-disagreement filter", "category": "Single bet",
     "signal": "Independent model versus de-vigged market disagreement ≥4 pp; reject stale quotes and unexplained moves.",
     "parameters": {"min_disagreement": 0.04, "max_quote_age_seconds": 900},
     "source_ids": ["S05", "S16"], "blockers": ["R01", "R03", "R11"]},
]


def registered_strategies() -> list[dict]:
    strategies = []
    source_urls = {
        "S05": "https://support.nfl.com/hc/en-us/articles/35869738523412-Who-is-making-the-odds",
        "S06": "https://support.nfl.com/hc/en-us/articles/35869727578900-What-is-a-total",
        "S08": "https://www.nfl.com/news/next-gen-stats-introduction-to-completion-probability-0ap3000000964655",
        "S09": "https://support.fanduel.com/s/article/Betting-football-with-FanDuel",
        "S10": "https://www.nfl.com/standings/league/2026/REG",
        "S11": "https://www.nfl.com/schedules/2026/by-week/week-9",
        "S12": "https://www.nfl.com/players/joe-burrow/stats/logs/2024/",
        "S13": "https://www.nfl.com/players/ja-marr-chase/stats/logs/2024/",
        "S16": "https://academic.oup.com/rfs/issue/29/1",
        "S17": "https://journals.ametsoc.org/view/journals/mwre/148/9/mwrD190076.xml?tab_body=fulltext-display",
    }
    for item in REGISTRY:
        strategy = dict(item)
        strategy["metrics"] = {}
        strategy["gates"] = evaluate_gates({})
        strategy["eligible"] = False
        strategy["status"] = "Blocked — evidence incomplete"
        strategy["net_roi"] = None
        strategy["net_roi_lb"] = None
        strategy["clv"] = None
        strategy["settled_bets"] = None
        strategy["reward_points"] = 0
        strategy["source_urls"] = [source_urls[i] for i in item["source_ids"]]
        strategy["derived"] = True
        strategies.append(strategy)
    return strategies

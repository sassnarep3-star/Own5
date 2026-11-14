"""Deterministic rebuild of every table this desk publishes.

Run:  python3 nfl-desk-3fb93d11/run.py

Outputs land in nfl-desk-3fb93d11/data/.  The build is pure: the same inputs
produce byte-identical CSVs, which the CI workflow enforces with git diff.
"""

from __future__ import annotations

import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import engine
from engine import (RETRIEVED_UTC, STANDINGS_URL, TEAMS, fmt, INJURY_URL,
                    INJURY_WK11_URL, MIRROR_GAMES_URL, official_standings,
                    load_official_games, reconcile_feed, reconcile_mirror,
                    build_sources, official_correlations, withheld_correlations,
                    walk_forward_2026, model_accuracy, build_price_store,
                    originate, build_replacement_depth, load_mirror, mirror_index,
                    read_csv, write_csv, fnum)
import gates
import registers
import audit_repo
import build_site
from gates import (FAMILIES, GATES, DEMOTION_GATE, run_universe, summarise,
                   holm_adjust, evaluate_gates, build_leaderboard,
                   BREAKEVEN, PARLAY_BREAKEVEN, FLAT_PRICE, HOLM_ALPHA)

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")


def main() -> dict:
    report = {}

    # ---------------------------------------------------------------- 1. feed
    games, parse_problems = load_official_games()
    standings = official_standings()
    feed_rec, feed_mismatches = reconcile_feed(games, standings)
    mirror_rec, mirror_stats = reconcile_mirror(games)
    report["official_games"] = len(games)
    report["parse_problems"] = parse_problems
    report["standings_mismatches"] = feed_mismatches
    report["mirror_agreement"] = mirror_stats

    write_csv("results_feed.csv", [{
        **g,
        "away_club": TEAMS[g["away"]], "home_club": TEAMS[g["home"]],
        "result": ("home win" if g["home_margin"] > 0 else
                   "away win" if g["home_margin"] < 0 else "tie"),
        "source_tier": "OFFICIAL", "fetched_utc": RETRIEVED_UTC,
    } for g in games],
        ["game_id", "season", "week", "kickoff_date", "weekday_as_published",
         "weekday_checked", "away", "away_club", "home", "home_club",
         "away_score", "home_score", "home_margin", "total_points", "result",
         "neutral_site", "source_tier", "source_url", "fetched_utc"])

    write_csv("results_reconciliation.csv", feed_rec,
              ["team", "club", "official_w", "official_l", "official_t", "official_pf",
               "official_pa", "feed_w", "feed_l", "feed_t", "feed_pf", "feed_pa",
               "w_delta", "l_delta", "t_delta", "pf_delta", "pa_delta", "agrees",
               "official_source_url", "feed_source_url"])

    write_csv("results_mirror_check.csv", mirror_rec,
              ["game_id", "week", "matchup", "official_away_score", "official_home_score",
               "mirror_away_score", "mirror_home_score", "agrees", "state",
               "official_source_url", "mirror_source_url"])

    write_csv("standings_official.csv", standings,
              ["team", "club", "w", "l", "t", "games_played", "win_pct", "pf", "pa",
               "net_pts", "pf_per_game", "pa_per_game", "net_per_game",
               "source_url", "fetched_utc"])

    # --------------------------------------------------------- 2. model + origination
    wf = walk_forward_2026(games, first_eval_week=5)
    acc = model_accuracy(wf["predictions"])
    report["accuracy"] = {k: (fmt(v, 4) if isinstance(v, float) else v) for k, v in acc.items()}

    mirror = load_mirror()
    slates = read_csv(os.path.join(DATA, "_raw_slate_wk10_wk11.csv"))
    slates = [s for s in slates if s["status"] == "SCHEDULED"]
    originated, steps, meta = originate(games, slates, mirror, acc.get("sigma_margin"))
    report["origination"] = {"sigma": fmt(meta["sigma"], 3), "hfa_pts": fmt(meta["hfa_pts"], 3),
                             "markets": len(originated), "games": len(slates)}

    write_csv("originated_markets.csv", originated,
              ["game_id", "season", "week", "away", "home", "matchup", "kickoff_label",
               "neutral_site", "status", "market_id", "market_type", "origination_order",
               "derived_from", "model_line", "market_line",
               "difference_model_minus_market", "model_price_american",
               "market_price_american", "units", "model_source_url",
               "market_source_url", "market_source_tier", "snapshot_utc"])

    write_csv("origination_steps.csv", steps,
              ["game_id", "origination_step", "model_value", "market_value",
               "difference", "derived_from", "source_url"])

    # ------------------------------------------------------------- 3. price store
    price_rows = build_price_store(originated, slates)
    write_csv("price_snapshots.csv", price_rows,
              ["season", "week", "game_id", "matchup", "market_id", "market_type",
               "snapshot_type", "line_value", "price_american", "snapshot_utc",
               "source_url", "source_tier", "verified", "flag_id"])
    store_counts = {}
    store_filled = {}
    for r in price_rows:
        store_counts[r["snapshot_type"]] = store_counts.get(r["snapshot_type"], 0) + 1
        if r["line_value"] != "":
            store_filled[r["snapshot_type"]] = store_filled.get(r["snapshot_type"], 0) + 1
    filled = sum(store_filled.values())
    report["price_store"] = {"rows": len(price_rows), "populated": filled,
                             "by_snapshot_type": store_counts}

    write_csv("price_store_schema.csv", [
        {"snapshot_type": st, "meaning": desc,
         "source_url": (engine.SCHEDULE_URL if st.startswith("MODEL") else MIRROR_GAMES_URL),
         "rows_total": store_counts.get(st, 0),
         "populated_rows": store_filled.get(st, 0),
         "empty_rows": store_counts.get(st, 0) - store_filled.get(st, 0),
         "source_tier": {"MODEL_ORIGIN": "DERIVED", "MODEL_CLOSE": "",
                         "MARKET_OPEN": "", "MARKET_CLOSE": "",
                         "MARKET_REFERENCE": "AGGREGATOR"}[st],
         "blocking_flag": {"MODEL_ORIGIN": "", "MODEL_CLOSE": "F-03",
                           "MARKET_OPEN": "F-01", "MARKET_CLOSE": "F-01",
                           "MARKET_REFERENCE": "F-01"}[st]}
        for st, desc in engine.SNAPSHOT_TYPES],
        ["snapshot_type", "meaning", "rows_total", "populated_rows", "empty_rows",
         "source_tier", "blocking_flag"])

    # ------------------------------------------------------------- 4. correlations
    corr = official_correlations(standings, games)
    write_csv("correlations_official.csv", corr,
              ["corr_id", "unit_of_analysis", "metric_a", "metric_b", "r", "p_value",
               "ci95_low", "ci95_high", "n", "n_definition", "source_tier",
               "source_url", "fetched_utc"])
    write_csv("correlations_withheld.csv", withheld_correlations(),
              ["withheld_id", "quantity", "previously_published_value",
               "previously_published_n", "published_by_session", "input_basis",
               "admissible_under_official_only_rule", "reason", "source_url"])
    report["correlations_official"] = len(corr)

    # ------------------------------------------------------------------ 5. depth
    depth_rows, depth_checks = build_replacement_depth()
    withheld = [r for r in depth_rows if r["replacement_depth_string"]]
    write_csv("replacement_depth.csv", depth_rows,
              ["team", "club", "unit", "position", "first_string", "second_string",
               "third_string", "starter_unavailable", "expected_starter_next_game",
               "replacement_player", "replacement_depth_string",
               "depth_of_replacement_label", "replacement_on_official_report",
               "replacement_game_status", "replacement_practice_status",
               "compounding_replacement_out", "cascade_to_player", "cascade_depth_string",
               "rungs_down", "no_backup_published", "depth_chart_source_url",
               "injury_source_url", "as_of"])
    write_csv("depth_injury_crosscheck.csv", depth_checks,
              ["team", "player", "position", "game_status", "practice_status",
               "injured_player_is_published_starter", "depth_slot_moved", "check_state",
               "injury_source_url", "depth_source_url"])
    irregular = sum(1 for c in depth_checks if c["check_state"].startswith("IRREGULAR"))
    report["depth"] = {"slots": len(depth_rows),
                       "slots_using_a_backup": len(withheld),
                       "clubs_published": len({r["team"] for r in depth_rows}),
                       "out_players_checked": len(depth_checks),
                       "out_players_irregular": irregular}

    # ------------------------------------------------------------ 6. backtests
    midx = mirror_index(mirror)
    off_games = []
    for g in games:
        m = midx.get(("2026", str(g["week"]), g["away"], g["home"]), {})
        home_ml, away_ml = fnum(m.get("home_moneyline")), fnum(m.get("away_moneyline"))
        mp = float("nan")
        if home_ml and away_ml:
            from statslib import devig_two_way
            _, mp = devig_two_way(away_ml, home_ml)
        off_games.append({**g, "period": g["week"], "neutral": bool(g["neutral_site"]),
                          "market_side": fnum(m.get("spread_line")),
                          "market_total": fnum(m.get("total_line")),
                          "market_prob_home": mp,
                          "home_rest": fnum(m.get("home_rest")),
                          "away_rest": fnum(m.get("away_rest")),
                          "div_game": m.get("div_game", "")})

    mir_games = []
    for r in mirror:
        if r["game_type"] != "REG" or not r["home_score"] or not r["away_score"]:
            continue
        if int(r["season"]) > 2025:
            continue
        if r["home_team"] not in engine.TEAM_INDEX or r["away_team"] not in engine.TEAM_INDEX:
            continue
        home_ml, away_ml = fnum(r.get("home_moneyline")), fnum(r.get("away_moneyline"))
        mp = float("nan")
        if home_ml and away_ml:
            from statslib import devig_two_way
            _, mp = devig_two_way(away_ml, home_ml)
        mir_games.append({
            "game_id": r["game_id"], "season": int(r["season"]),
            "period": int(r["season"]), "week": int(r["week"]),
            "home": r["home_team"], "away": r["away_team"],
            "neutral": r["location"] == "Neutral",
            "home_margin": int(r["home_score"]) - int(r["away_score"]),
            "total_points": int(r["home_score"]) + int(r["away_score"]),
            "market_side": fnum(r.get("spread_line")),
            "market_total": fnum(r.get("total_line")),
            "market_prob_home": mp,
            "home_rest": fnum(r.get("home_rest")), "away_rest": fnum(r.get("away_rest")),
            "div_game": r.get("div_game", ""),
        })

    uni_off = run_universe(off_games, "OFFICIAL-2026", 4, "OFFICIAL",
                           "https://www.nfl.com/schedules/2026/by-week/")
    uni_mir = run_universe(mir_games, "MIRROR-1999-2025", 3, "AGGREGATOR", MIRROR_GAMES_URL)

    ledger, gate_rows, board_rows = [], [], []
    for universe, uni, tier in (("OFFICIAL-2026", uni_off, "OFFICIAL"),
                                ("MIRROR-1999-2025", uni_mir, "AGGREGATOR")):
        rows = []
        for fam in FAMILIES:
            s = summarise(uni["bets"].get(fam["id"], []))
            rows.append({**s, "family_id": fam["id"], "family": fam["name"],
                         "bet_class": fam["bet_class"], "market": fam["market"],
                         "universe": universe, "universe_tier": tier,
                         "rule": fam["rule"], "parameters": fam["parameters"],
                         "row_id": f"{fam['id']}@{universe}"})
        rows = holm_adjust(rows)
        for r, fam in zip(rows, FAMILIES):
            g = evaluate_gates(r, fam, tier)
            gate_rows.extend(g)
            r["gates_passed"] = sum(1 for x in g if x["result"] == "pass")
            r["gates_hard"] = sum(1 for x in g if x["result"] != "not evaluated")
            r["gates_total"] = len(g)
            board_rows.append(r)

    board_rows = build_leaderboard(board_rows)

    for r in board_rows:
        ledger.append({
            "row_id": r["row_id"], "family_id": r["family_id"], "family": r["family"],
            "bet_class": r["bet_class"], "market": r["market"], "universe": r["universe"],
            "universe_tier": r["universe_tier"], "n_bets": r.get("n_bets", 0),
            "n_decided": r.get("n_decided", 0), "n_pushes": r.get("n_pushes", 0),
            "wins": r.get("wins", 0), "hit_rate": fmt(r.get("hit_rate"), 4),
            "breakeven": fmt(r.get("breakeven"), 4),
            "ci95_low": fmt(r.get("ci95_low"), 4), "ci95_high": fmt(r.get("ci95_high"), 4),
            "p_vs_breakeven": fmt(r.get("p_vs_breakeven"), 6),
            "p_vs_coinflip": fmt(r.get("p_vs_coinflip"), 6),
            "holm_p": fmt(r.get("holm_p"), 6),
            "holm_significant": r.get("holm_significant", ""),
            "mean_clv": fmt(r.get("mean_clv"), 3),
            "roi_pct": fmt(r.get("roi_pct"), 3),
            "sharpe": fmt(r.get("sharpe"), 4),
            "deflated_sharpe": fmt(r.get("deflated_sharpe"), 4),
            "gates_passed": r.get("gates_passed", 0),
            "gates_hard": r.get("gates_hard", 0),
            "rule": r["rule"], "parameters": r["parameters"],
            "source_tier": r.get("source_tier", ""),
            "source_url": r.get("source_url", ""),
        })
    write_csv("strategy_ledger.csv", ledger,
              ["row_id", "family_id", "family", "bet_class", "market", "universe",
               "universe_tier", "n_bets", "n_decided", "n_pushes", "wins", "hit_rate",
               "breakeven", "ci95_low", "ci95_high", "p_vs_breakeven", "p_vs_coinflip",
               "holm_p", "holm_significant", "mean_clv", "roi_pct", "sharpe",
               "deflated_sharpe", "gates_passed", "gates_hard", "rule", "parameters",
               "source_tier", "source_url"])

    write_csv("gate_matrix.csv", gate_rows,
              ["strategy_id", "strategy", "gate_id", "result", "note", "universe_tier",
               "source_url"])

    # ------------------------------------------------- 7. leaderboard + demotion
    lb = []
    for r in board_rows:
        lb.append({
            "row_id": r["row_id"], "family_id": r["family_id"], "family": r["family"],
            "bet_class": r["bet_class"], "universe": r["universe"],
            "board": r.get("board", ""), "board_size": r.get("board_size", ""),
            "universe_tier": r["universe_tier"], "n_decided": r.get("n_decided", 0),
            "signal_score": fmt(r.get("signal_score"), 2),
            "staking_score": fmt(r.get("staking_score"), 2),
            "signal_rank": r.get("signal_rank", ""), "staking_rank": r.get("staking_rank", ""),
            "rank_gap": r.get("rank_gap", ""),
            "roi_pct": fmt(r.get("roi_pct"), 3),
            "hit_rate": fmt(r.get("hit_rate"), 4),
            "gates_passed": r.get("gates_passed", 0), "gates_hard": r.get("gates_hard", 0),
            "certified": r.get("certified", "no"), "state": r.get("state", "PAPER"),
            "note": r.get("note", ""),
            "source_tier": r.get("source_tier", ""),
            "source_url": r.get("source_url", ""),
        })
    write_csv("leaderboard.csv", lb,
              ["row_id", "family_id", "family", "bet_class", "universe", "board", "board_size",
               "universe_tier", "n_decided", "signal_score", "staking_score", "signal_rank",
               "staking_rank",
               "rank_gap", "roi_pct", "hit_rate", "gates_passed", "gates_hard",
               "certified", "state", "note", "source_tier", "source_url"])

    dem_rows = []
    for r in board_rows:
        for tid, trig, why in DEMOTION_GATE["triggers"]:
            if tid == "D1c" and r.get("n_decided", 0) and r.get("hit_rate") == r.get("hit_rate"):
                fired = "would fire" if r["hit_rate"] < r.get("breakeven", 1) else "clear"
            elif tid in ("D1a", "D1b", "D1f"):
                fired = "not observable - no verified price or bankroll data (F-01, Q-03)"
            elif tid == "D1d":
                fired = "clear - parameters unchanged since pre-registration"
            elif tid == "D1e":
                fired = "would fire for every graded bet - no verified snapshot exists (F-01)"
            else:
                fired = "not evaluated"
            dem_rows.append({
                "row_id": r["row_id"], "family_id": r["family_id"],
                "current_state": r.get("state", "PAPER"),
                "demotion_trigger": tid, "trigger_text": trig, "why_it_matters": why,
                "evaluation": fired,
                "source_url": "https://www.nfl.com/schedules/2026/by-week/",
            })
    write_csv("demotion_gate.csv", dem_rows,
              ["row_id", "family_id", "current_state", "demotion_trigger", "trigger_text",
               "why_it_matters", "evaluation", "source_url"])

    write_csv("gates.csv", GATES,
              ["gate_id", "name", "test", "hard", "provenance", "source_url"])

    # ---------------------------------------------------------------- 8. sources
    write_csv("sources.csv", build_sources(games),
              ["source_id", "publisher", "title", "url", "tier", "fetched_utc",
               "used_for", "rows_contributed", "verification_status"])

    report["backtests"] = {
        "official_universe_rows": len(off_games),
        "mirror_universe_rows": len(mir_games),
        "graded_periods_official": uni_off["graded_periods"],
        "families": len(FAMILIES),
        "certified": sum(1 for r in board_rows if r.get("certified") == "yes"),
    }
    report["sigma_used"] = fmt(uni_off["sigma"], 3)

    # ------------------------------------------------------- 9. review registers
    registers.write_registers(report["accuracy"], report["depth"], mirror_stats,
                              meta["hfa_pts"], len(games))
    audit_rows = audit_repo.main()
    report["repo_audit"] = {"checks": len(audit_rows),
                            "irregular": sum(1 for r in audit_rows if r["verdict"] == "IRREGULAR"),
                            "match": sum(1 for r in audit_rows if r["verdict"] == "MATCH"),
                            "not_checked": sum(1 for r in audit_rows if r["verdict"] == "NOT CHECKED")}
    report["flags"] = len(read_csv(os.path.join(DATA, "flagged.csv")))

    with open(os.path.join(DATA, "build_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True, default=str)

    # ---------------------------------------------------------------- 10. site
    build_site.build(report)
    return report


if __name__ == "__main__":
    rep = main()
    print(json.dumps(rep, indent=2, sort_keys=True, default=str))

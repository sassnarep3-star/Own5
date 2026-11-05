"""Frozen NBA research model. All functions are deterministic and offline."""
from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path
from typing import Any

from . import stats

STATS = ("pts", "reb", "ast", "tpm")
STAT_LABELS = {"pts": "Points", "reb": "Rebounds", "ast": "Assists", "tpm": "Threes made"}
PAIRS = list(itertools.combinations(STATS, 2))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def r3(x: float | None) -> float | None:
    return None if x is None else round(x, 3)


def r6(x: float | None) -> float | None:
    return None if x is None else round(x, 6)


def team_lines(teams: list[dict], schedule: list[dict], protocol: dict) -> tuple[list[dict], list[dict]]:
    cfg = protocol["team_model"]
    by_season: dict[str, dict[str, dict]] = {}
    for row in teams:
        by_season.setdefault(row["season"], {})[row["team_id"]] = row
    abbr_to_id = {row["abbr"]: row["team_id"] for row in teams if row["season"] == cfg["current_season"]}
    current = by_season[cfg["current_season"]]
    prior = by_season[cfg["prior_season"]]

    def blend(team_id: str, key: str, k: float) -> float:
        c, p = current[team_id], prior[team_id]
        gp = float(c["gp"])
        w = gp / (gp + k)
        return w * float(c[key]) + (1 - w) * float(p[key])

    lines: list[dict] = []
    sensitivity: list[dict] = []
    k0 = float(cfg["prior_strength_games"])
    hfa0 = float(cfg["primary_home_points_adjustment"])
    scale = float(cfg["logistic_scale_points"])
    for game in schedule:
        away_id, home_id = abbr_to_id[game["away"]], abbr_to_id[game["home"]]
        away_off = blend(away_id, "pts_pg", k0)
        home_off = blend(home_id, "pts_pg", k0)
        away_def = away_off - blend(away_id, "plus_minus_pg", k0)
        home_def = home_off - blend(home_id, "plus_minus_pg", k0)
        home_pts = (home_off + away_def) / 2 + hfa0 / 2
        away_pts = (away_off + home_def) / 2 - hfa0 / 2
        margin = home_pts - away_pts
        total = home_pts + away_pts
        lines.append({
            "game_id": game["game_id"], "date": game["date"], "tip_et": game["tip_et"],
            "away": game["away"], "home": game["home"], "venue": game["venue"],
            "away_gp": int(current[away_id]["gp"]), "home_gp": int(current[home_id]["gp"]),
            "away_off_blend": r3(away_off), "away_def_blend": r3(away_def),
            "home_off_blend": r3(home_off), "home_def_blend": r3(home_def),
            "expected_home_pts": r3(home_pts), "expected_away_pts": r3(away_pts),
            "expected_margin": r3(margin), "expected_total": r3(total),
            "research_home_spread": stats.half_point_line(-margin),
            "research_total": stats.half_point_line(total),
            "home_win_prob_heuristic": r6(stats.logistic(margin, scale)),
            "market_spread": "", "market_total": "", "market_odds": "", "edge": "",
            "availability": "Held — final availability unverified",
            "kind": "Derived calculation", "flag": "F01/F02",
            "source_url": game["source_url"],
            "input_current": "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season",
            "input_prior": "https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season",
        })
        for k in cfg["sensitivity_prior_strengths"]:
            for hfa in cfg["sensitivity_home_points_adjustments"]:
                ao = blend(away_id, "pts_pg", k); ho = blend(home_id, "pts_pg", k)
                ad = ao - blend(away_id, "plus_minus_pg", k); hd = ho - blend(home_id, "plus_minus_pg", k)
                hp = (ho + ad) / 2 + hfa / 2; ap = (ao + hd) / 2 - hfa / 2
                m = hp - ap; t = hp + ap
                sensitivity.append({
                    "game_id": game["game_id"], "away": game["away"], "home": game["home"],
                    "prior_strength": k, "home_points_adjustment": hfa,
                    "expected_margin": r3(m), "expected_total": r3(t),
                    "research_home_spread": stats.half_point_line(-m), "research_total": stats.half_point_line(t),
                    "kind": "Derived sensitivity", "source_url": game["source_url"],
                })
    return lines, sensitivity


def player_forecasts(games: list[dict], protocol: dict) -> tuple[list[dict], list[dict]]:
    cfg = protocol["player_model"]
    infer = protocol["inference"]
    min_prior = int(cfg["minimum_prior_games"])
    window = int(cfg["rolling_window_games"])
    rows: list[dict] = []
    by_player: dict[str, list[dict]] = {}
    for g in games:
        by_player.setdefault(g["player_id"], []).append(g)
    for pid in sorted(by_player):
        logs = sorted(by_player[pid], key=lambda r: r["game_date"])
        thresholds = cfg["research_thresholds"][pid]
        source = logs[0]["official_page"]
        for i in range(min_prior, len(logs)):
            prior = logs[:i]
            recent = prior[-window:]
            actual_row = logs[i]
            for stat in STATS:
                vals = [float(r[stat]) for r in prior]
                recent_vals = [float(r[stat]) for r in recent]
                threshold = float(thresholds[stat])
                actual = float(actual_row[stat])
                hit = int(actual > threshold)
                mu = stats.mean(recent_vals)
                sigma = stats.sd(recent_vals) if len(recent_vals) > 1 else 0.0
                p_candidate = stats.normal_sf(threshold, mu, sigma)
                hits_prior = sum(1 for v in vals if v > threshold)
                p_baseline = (hits_prior + 1) / (len(vals) + 2)
                expanding = stats.mean(vals)
                last = vals[-1]
                rows.append({
                    "player_id": pid, "player": actual_row["player"], "game_date": actual_row["game_date"],
                    "game_id": actual_row["game_id"], "stat": stat, "stat_label": STAT_LABELS[stat],
                    "threshold": threshold, "n_prior": len(prior), "rolling_mean": r3(mu),
                    "rolling_sd": r3(sigma), "last_value": last, "expanding_mean": r3(expanding),
                    "actual": actual, "hit": hit, "p_candidate": r6(p_candidate), "p_baseline": r6(p_baseline),
                    "brier_candidate": r6(stats.brier(p_candidate, hit)),
                    "brier_baseline": r6(stats.brier(p_baseline, hit)),
                    "logloss_candidate": r6(stats.log_loss(p_candidate, hit)),
                    "logloss_baseline": r6(stats.log_loss(p_baseline, hit)),
                    "kind": "Derived walk-forward forecast", "source_url": source,
                })
    # Eight player×stat skill series, date-clustered paired bootstrap and Holm.
    summaries: list[dict] = []
    raw_p: list[float | None] = []
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        grouped.setdefault((row["player_id"], row["stat"]), []).append(row)
    for (pid, stat), group in sorted(grouped.items()):
        dates = [r["game_date"] for r in group]
        diffs = [r["brier_candidate"] - r["brier_baseline"] for r in group]
        boot = stats.cluster_bootstrap_mean_diff(dates, diffs, int(infer["bootstrap_replicates"]), int(infer["random_seed"]))
        raw_p.append(boot["p_bootstrap"])
        pred = [r["rolling_mean"] for r in group]
        actual = [r["actual"] for r in group]
        last = [r["last_value"] for r in group]
        exp = [r["expanding_mean"] for r in group]
        summaries.append({
            "player_id": pid, "player": group[0]["player"], "stat": stat, "stat_label": STAT_LABELS[stat],
            "n": len(group), "clusters": boot["clusters"],
            "brier_candidate": r6(stats.mean([r["brier_candidate"] for r in group])),
            "brier_baseline": r6(stats.mean([r["brier_baseline"] for r in group])),
            "logloss_candidate": r6(stats.mean([r["logloss_candidate"] for r in group])),
            "logloss_baseline": r6(stats.mean([r["logloss_baseline"] for r in group])),
            "brier_diff": r6(boot["mean_diff"]), "brier_diff_ci_lo": r6(boot["ci_lo"]),
            "brier_diff_ci_hi": r6(boot["ci_hi"]), "p_raw": r6(boot["p_bootstrap"]),
            "mae_rolling": r3(stats.mae(pred, actual)), "rmse_rolling": r3(stats.rmse(pred, actual)),
            "mae_last": r3(stats.mae(last, actual)), "mae_expanding": r3(stats.mae(exp, actual)),
            "kind": "Derived skill diagnostic", "source_url": group[0]["source_url"],
        })
    adjusted = stats.holm(raw_p)
    min_n = int(protocol["validation_gates"]["minimum_predictive_observations_per_series"])
    for s, p_adj in zip(summaries, adjusted):
        s["p_holm"] = r6(p_adj)
        s["passes_predictive_gate"] = bool(s["n"] >= min_n and p_adj is not None and p_adj < float(infer["alpha"]) and s["brier_diff_ci_hi"] < 0)
        s["gate_reason"] = "PASS" if s["passes_predictive_gate"] else f"FAIL — n={s['n']} < {min_n} and/or no Holm-significant negative Brier difference"
    return rows, summaries


def correlations(games: list[dict], protocol: dict) -> list[dict]:
    infer = protocol["inference"]
    reps = int(infer["permutation_replicates"])
    seed = int(infer["random_seed"])
    by_player: dict[str, list[dict]] = {}
    for g in games:
        by_player.setdefault(g["player_id"], []).append(g)
    rows: list[dict] = []
    raw_p: list[float | None] = []
    for pid in sorted(by_player):
        logs = sorted(by_player[pid], key=lambda r: r["game_date"])
        source = logs[0]["official_page"]
        for x, y in PAIRS:
            xs = [float(r[x]) for r in logs]; ys = [float(r[y]) for r in logs]
            r = stats.pearson(xs, ys)
            p = stats.permutation_p_pearson(xs, ys, reps, seed)
            raw_p.append(p)
            rows.append({
                "player_id": pid, "player": logs[0]["player"], "family": "same-game", "stat_x": x, "stat_y": y,
                "n": len(logs), "pearson_r": r6(r), "p_raw": r6(p),
                "interpretation": "Descriptive within-player association; exchangeability assumed for permutation null.",
                "kind": "Derived correlation", "source_url": source,
            })
        for stat in STATS:
            xs = [float(r[stat]) for r in logs[:-1]]; ys = [float(r[stat]) for r in logs[1:]]
            r = stats.pearson(xs, ys)
            p = stats.permutation_p_pearson(xs, ys, reps, seed + 1)
            raw_p.append(p)
            rows.append({
                "player_id": pid, "player": logs[0]["player"], "family": "lag-1", "stat_x": stat, "stat_y": stat,
                "n": len(xs), "pearson_r": r6(r), "p_raw": r6(p),
                "interpretation": "Non-significance is not proof of independence or cross-game parlay safety.",
                "kind": "Derived correlation", "source_url": source,
            })
    for row, p_adj in zip(rows, stats.holm(raw_p)):
        row["p_holm"] = r6(p_adj)
    return rows


def prop_combos(games: list[dict], protocol: dict) -> list[dict]:
    thresholds = protocol["player_model"]["research_thresholds"]
    by_player: dict[str, list[dict]] = {}
    for g in games:
        by_player.setdefault(g["player_id"], []).append(g)
    rows: list[dict] = []
    two_raw_p: list[float | None] = []
    for pid in sorted(by_player):
        logs = sorted(by_player[pid], key=lambda r: r["game_date"])
        source = logs[0]["official_page"]
        th = thresholds[pid]
        hits = {s: [int(float(r[s]) > float(th[s])) for r in logs] for s in STATS}
        n = len(logs)
        for pair in PAIRS:
            x, y = pair
            a = sum(1 for i in range(n) if hits[x][i] and hits[y][i])
            b = sum(1 for i in range(n) if hits[x][i] and not hits[y][i])
            c = sum(1 for i in range(n) if not hits[x][i] and hits[y][i])
            d = n - a - b - c
            pa, pb = (a + b) / n, (a + c) / n
            p_ind = pa * pb
            p_joint = a / n
            p = stats.fisher_exact_two_sided(a, b, c, d)
            two_raw_p.append(p)
            rows.append({
                "player_id": pid, "player": logs[0]["player"], "legs": 2,
                "combo": f"{STAT_LABELS[x]} > {th[x]} + {STAT_LABELS[y]} > {th[y]}",
                "n": n, "joint_hits": a, "p_x": r6(pa), "p_y": r6(pb),
                "p_independent": r6(p_ind), "p_joint": r6(p_joint),
                "lift": r6(p_joint / p_ind) if p_ind else None,
                "phi": r6(stats.phi_coefficient(a, b, c, d)), "p_raw": r6(p),
                "table_2x2": f"{a},{b},{c},{d}",
                "interpretation": "Historical research thresholds, not sportsbook props. Lift > 1 means multiplying marginals understates joint hits.",
                "kind": "Derived joint dependence", "source_url": source,
            })
        for triple in itertools.combinations(STATS, 3):
            a = sum(1 for i in range(n) if all(hits[s][i] for s in triple))
            p_ind = math.prod(sum(hits[s]) / n for s in triple)
            p_joint = a / n
            rows.append({
                "player_id": pid, "player": logs[0]["player"], "legs": 3,
                "combo": " + ".join(f"{STAT_LABELS[s]} > {th[s]}" for s in triple),
                "n": n, "joint_hits": a, "p_x": "", "p_y": "",
                "p_independent": r6(p_ind), "p_joint": r6(p_joint),
                "lift": r6(p_joint / p_ind) if p_ind else None,
                "phi": "", "p_raw": "", "table_2x2": "",
                "interpretation": "Descriptive three-way joint rate only; no exact three-way test or payout claim.",
                "kind": "Derived joint dependence", "source_url": source,
            })
    adjusted = stats.holm(two_raw_p)
    j = 0
    for row in rows:
        if row["legs"] == 2:
            row["p_holm"] = r6(adjusted[j]); j += 1
        else:
            row["p_holm"] = ""
    return rows


def luck_planning(protocol: dict) -> dict:
    cfg = protocol["power_planning"]
    p0 = float(cfg["null_win_probability"]); p1 = float(cfg["alternative_win_probability"])
    alpha = float(cfg["one_sided_alpha"]); power = float(cfg["target_power"])
    n = stats.power_normal(p0, p1, alpha, power)
    crit = stats.binom_critical(n, p0, alpha)
    exact_power = stats.binom_sf(crit, n, p1)
    family = int(cfg["multiplicity_family_for_planning"])
    alpha_b = alpha / family
    n_b = stats.power_normal(p0, p1, alpha_b, power)
    crit_b = stats.binom_critical(n_b, p0, alpha_b)
    exact_power_b = stats.binom_sf(crit_b, n_b, p1)
    return {
        "american_odds_example": int(cfg["american_odds_example"]),
        "break_even_win_probability": r6(p0), "alternative_win_probability": p1,
        "normal_approx_n_single": n, "critical_wins_single": crit,
        "exact_power_at_normal_n": r6(exact_power),
        "planning_family_size": family, "bonferroni_alpha": r6(alpha_b),
        "normal_approx_n_bonferroni": n_b, "critical_wins_bonferroni": crit_b,
        "exact_power_at_bonferroni_n": r6(exact_power_b),
        "example_30_bets_20_wins_p_vs_breakeven": r6(stats.binom_sf(20, 30, p0)),
        "real_graded_bets": 0, "roi": None, "clv": None, "max_drawdown": None,
        "kind": "Derived planning arithmetic; odds example is not a market quote",
        "source_url": "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf",
        "note": "Luck cannot be literally removed. Normal approximation is planning only; exact binomial power is reported at that n. No real-return performance exists.",
    }


GATES = [
    ("G01", "Provenance", "Every required input has a directly checked official source and row link.", "Official source register and field audit."),
    ("G02", "Prospective registration", "Rules were frozen before unseen outcomes.", "Timestamped protocol commit before outcomes; current protocol is retrospective."),
    ("G03", "No leakage", "Forecasts use only information available before the event.", "Chronological walk-forward code and tests."),
    ("G04", "Availability", "Final lineup/availability is verified at decision time.", "Final injury report and lineup snapshot."),
    ("G05", "Market quotes", "Timestamped side, line, odds, limit and book are verified.", "Operator quote archive."),
    ("G06", "Settlement rules", "Applicable jurisdiction/operator void, push, OT and neutral-site rules are verified.", "Jurisdiction-specific house rules."),
    ("G07", "Dependence", "Joint dependence is validated out-of-sample, or explicitly N/A for a single.", "Prospective joint-hit ledger and payout rules."),
    ("G08", "Sample / power", "At least 200 genuine graded priced bets and disclosed power planning.", "Real graded ledger; no synthetic rows."),
    ("G09", "Predictive skill", "Beats a baseline with multiplicity-adjusted evidence and adequate n.", "Out-of-sample proper-score comparison."),
    ("G10", "Economic edge", "Lower uncertainty bound of net ROI after costs is positive.", "Real prices, payouts and clustered ROI interval."),
    ("G11", "Luck / multiplicity", "Real-return null diagnostics and selection-bias controls are reported.", "Returns ledger, declared trial family, bootstrap/permutation."),
    ("G12", "Reproducibility / risk", "Deterministic build, tests, no-stake-until-eligible rule and audit hashes.", "CI, checker and risk policy."),
]

STRATEGIES = [
    ("ST1", "Single", "Team-strength side single", 1, "Blend current/prior efficiency and compare a research margin with a verified market side once quotes exist.", "N/A"),
    ("ST2", "Single", "Efficiency total single", 1, "Blend offense/allowed points to originate a total and compare with a verified market total once quotes exist.", "N/A"),
    ("ST3", "Prop", "Rolling player-prop single", 1, "Use strictly prior rolling role/production to forecast a frozen research threshold; suppress until availability and a real prop quote exist.", "N/A"),
    ("ST4", "Parlay", "Cross-game two-leg parlay", 2, "Combine only independent, validated single edges; cross-game dependence and operator payout are currently unmeasured.", "FAIL"),
    ("ST5", "Prop combo", "Same-game two-prop combo", 2, "Test whether positive joint dependence is mispriced by a operator; historical lift is descriptive, not a payout edge.", "FAIL"),
    ("ST6", "Prop combo", "Same-game three-prop combo", 3, "Extend joint-dependence research to three legs; no exact three-way validation or real payout exists.", "FAIL"),
]


def strategies_and_gates(protocol: dict, skill: list[dict], lines: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    min_bets = int(protocol["validation_gates"]["minimum_graded_priced_bets"])
    predictive_pass = any(s["passes_predictive_gate"] for s in skill)
    strategies: list[dict] = []
    gate_rows: list[dict] = []
    leaderboard: list[dict] = []
    for sid, category, name, legs, hypothesis, dependence_status in STRATEGIES:
        statuses = {
            "G01": "PASS", "G02": "FAIL", "G03": "PASS", "G04": "FAIL", "G05": "FAIL",
            "G06": "FAIL", "G07": dependence_status, "G08": "FAIL",
            "G09": "PASS" if predictive_pass and category in {"Prop", "Prop combo"} else "FAIL",
            "G10": "FAIL", "G11": "FAIL", "G12": "PASS",
        }
        reasons = {
            "G01": "Selected official inputs directly checked; row links present.",
            "G02": "Protocol written after historical outcomes were visible; not prospective preregistration.",
            "G03": "Walk-forward code uses strictly earlier games; team lines are pregame snapshots.",
            "G04": "Final Nov 6 availability/lineups unverified at the Nov 5 4 PM snapshot.",
            "G05": "No verified sportsbook quote archive.",
            "G06": "Operator guide is context, not verified jurisdiction-specific house rules.",
            "G07": "Single has no joint-leg dependence." if dependence_status == "N/A" else "No prospective joint-hit/payout validation; historical dependence is descriptive.",
            "G08": f"0 genuine graded priced bets < {min_bets}.",
            "G09": "No series passes the frozen predictive gate." if not predictive_pass else "Predictive gate passed for at least one prop series; economic gates still required.",
            "G10": "No prices/payouts; net ROI and lower bound are blank.",
            "G11": "No real returns for null/multiplicity diagnostics.",
            "G12": "Deterministic offline build, tests, fail-closed eligibility and no-stake policy.",
        }
        eligible = all(v in {"PASS", "N/A"} for v in statuses.values())
        blockers = [g for g, v in statuses.items() if v not in {"PASS", "N/A"}]
        source = "https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nba"
        strategies.append({
            "strategy_id": sid, "category": category, "name": name, "legs": legs,
            "hypothesis": hypothesis, "eligible": eligible, "status": "Eligible" if eligible else "Blocked",
            "gates_passed": sum(1 for v in statuses.values() if v in {"PASS", "N/A"}),
            "gate_count": len(GATES), "blockers": ",".join(blockers),
            "graded_bets": 0, "reward": "", "kind": "Analyst strategy hypothesis", "source_url": source,
        })
        for gid, gname, criterion, evidence in GATES:
            gate_rows.append({
                "strategy_id": sid, "gate_id": gid, "gate": gname, "status": statuses[gid],
                "criterion": criterion, "evidence_needed": evidence, "reason": reasons[gid],
                "kind": "Validation gate", "source_url": source,
            })
        leaderboard.append({
            "strategy_id": sid, "name": name, "category": category, "rank": "", "eligible": eligible,
            "graded_bets": 0, "roi": "", "clv": "", "score_lower_bound": "", "max_drawdown": "",
            "reward": "", "status": "Unranked — ineligible" if not eligible else "Eligible",
            "blockers": ",".join(blockers), "kind": "Competition rule; no graded entry", "source_url": source,
        })
    return strategies, gate_rows, leaderboard

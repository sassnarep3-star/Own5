"""Run the whole 941fe39f desk: compute every table, then build the site.

    python3 tools/season_desk_941fe39f/build.py

Deterministic. Reads only the pinned corpus tarball, the official captures and
the carried-forward files this repo already holds. Writes only under
nfl-season-941fe39f/. No network access.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import availability as AV
import corpus as CORPUS
import crosscheck as CC
import model as MODEL
import registers as REG
import snapshots as SNAP
import stats
import strategies as STRAT

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "nfl-season-941fe39f"
DATA = DESK / "data"
DERIVED = DATA / "derived"

BUILD_UTC = "2026-11-17T01:30:00Z"
SESSION = "941fe39f"


# --------------------------------------------------------------------- io
def q(x):
    """Quantise a float to 10 decimal places before it is published.

    Two machines using different libm builds can differ in the last bit of a
    probability (1e-16), and that is enough for a committed file to fail a
    `git diff --exit-code` check on the other machine, as it did here. Rounding
    at 10 dp is far below anything this data can support (the smallest published
    quantity is a p-value, and none is quoted past 4 dp) and makes every output
    bit-identical across platforms.
    """
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return ""
        return round(x, 10)
    return x


def write_csv(name: str, header: list[str], rows: list[list]) -> dict:
    path = DERIVED / f"{name}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows([q(c) for c in row] for row in rows)
    data = buf.getvalue().encode("utf-8")
    path.write_bytes(data)
    return {"table": name, "rows": len(rows), "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data)}


def f(x, nd=4):
    if x is None:
        return ""
    if isinstance(x, float):
        if math.isnan(x):
            return ""
        return f"{x:.{nd}f}"
    return x


def write_json(name: str, obj) -> dict:
    path = DERIVED / f"{name}.json"
    data = json.dumps(obj, indent=1, ensure_ascii=False).encode("utf-8")
    path.write_bytes(data)
    return {"table": name, "rows": len(obj) if isinstance(obj, list) else 1,
            "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


# --------------------------------------------------------------------- main
def main() -> int:
    manifest = {"build_utc": BUILD_UTC, "session": SESSION, "tables": [], "checks": []}

    # 1. corpus
    cm = CORPUS.build()
    manifest["corpus"] = cm
    games = MODEL.load_games()
    manifest["checks"].append({"check": "corpus games loaded", "detail": f"{len(games)} rows",
                               "pass": len(games) > 7000})

    # 2. cross-checks against independent official reads
    checks = CC.run()
    manifest["crosschecks"] = [
        {"name": c["name"], "verdict": c["verdict"], "compared": c["compared"],
         "matched": c["matched"],
         **({"favourite_flips": c["favourite_flips"],
             "median_abs_diff": c["median_abs_diff"],
             "p90_abs_diff": c["p90_abs_diff"]} if "favourite_flips" in c else {}),
         **({"explained": c["explained"]} if "explained" in c else {}),
         **({"pending": c["pending"]} if "pending" in c else {})}
        for c in checks]

    # 3. originate
    orig = MODEL.originate(games)["rows"]
    manifest["checks"].append({"check": "originated markets", "detail": f"{len(orig)} rows",
                               "pass": len(orig) > 5000})
    orows = []
    for r in orig:
        resid = (r["model_margin_home"] - r["market_spread_home"]
                 if r["market_spread_home"] is not None else None)
        tresid = (r["model_total"] - r["market_total"]
                  if r["market_total"] is not None else None)
        orows.append([
            r["game_id"], r["season"], r["week"], r["gameday"], r["away"], r["home"],
            f(r["model_margin_home"], 3), f(r["market_spread_home"], 2), f(resid, 3),
            f(r["model_total"], 3), f(r["market_total"], 2), f(tresid, 3),
            f(r["model_home_win_prob"], 5),
            f(r["market_home_ml"], 0), f(r["market_away_ml"], 0),
            r["n_fit_games"], r["fit_cutoff"], f(r["sigma"], 3),
            f(r["result"], 0), f(r["total_actual"], 0),
            r["roof"], r["surface"], f(r["wind"], 1), f(r["temp"], 1),
            r["div_game"], r["rest_home"], r["rest_away"], r["location"],
            "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
            "model-own-price",
        ])
    manifest["tables"].append(write_csv("origination", [
        "game_id", "season", "week", "gameday", "away", "home",
        "model_margin_home", "market_spread_home", "residual_side",
        "model_total", "market_total", "residual_total",
        "model_home_win_prob", "market_home_ml", "market_away_ml",
        "n_fit_games", "fit_cutoff", "sigma",
        "result", "total_actual", "roof", "surface", "wind_mph", "temp_f",
        "div_game", "rest_home", "rest_away", "location",
        "source_url", "price_provenance"], orows))

    # 4. price store: one row per originated market with the price snapshot
    prow = []
    for r in orig:
        for market, key in (("side", "market_spread_home"), ("total", "market_total"),
                            ("moneyline", "market_home_ml")):
            if r[key] is None:
                continue
            prow.append([
                r["game_id"], r["season"], r["week"], market,
                "CLOSE", f(r[key], 2),
                f(r["home_spread_odds"] if market == "side" else
                  (r["over_odds"] if market == "total" else r["market_home_ml"]), 0),
                "",  # open price: absent from the corpus, flagged F-01
                "close only - no open exists in the corpus (F-01)",
                "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
            ])
    manifest["tables"].append(write_csv("price_snapshots", [
        "game_id", "season", "week", "market", "snapshot_type", "line",
        "price_american_home_or_over", "open_line", "open_status", "source_url"], prow))

    # 5. results feed (2026) from the corpus
    rf = []
    for g in games:
        if g["season"] != 2026:
            continue
        rf.append([g["game_id"], g["week"], g["gameday"], g["away"], g["home"],
                   f(g["away_score"], 0), f(g["home_score"], 0), g["status"],
                   "https://www.nfl.com/schedules/2026/by-week/week-%d" % g["week"]])
    manifest["tables"].append(write_csv("results_2026", [
        "game_id", "week", "gameday", "away", "home", "away_score", "home_score",
        "status", "source_url"], rf))

    # 6. model diagnostics + residual alpha by season
    diag = []
    for season in range(1999, 2027):
        al = MODEL.residual_alpha(orig, season, season)
        lv = MODEL.residual_level(orig, season, season)
        diag.append([season, al["n"], f(al["r"], 4), f(al["ci"][0], 4), f(al["ci"][1], 4),
                     f(lv["mae_model_side"], 3), f(lv["mae_market_side"], 3),
                     f(lv["mean_residual"], 3), f(lv["sd_residual"], 3),
                     f(lv["mae_model_total"], 3), f(lv["mae_market_total"], 3),
                     "https://github.com/nflverse/nfldata/blob/master/data/games.csv"])
    manifest["tables"].append(write_csv("model_by_season", [
        "season", "n_games", "alpha_r", "alpha_ci_lo", "alpha_ci_hi",
        "mae_model_side", "mae_market_side", "mean_residual_side", "sd_residual_side",
        "mae_model_total", "mae_market_total", "source_url"], diag))
    lvl = MODEL.residual_level(orig, 1999, 2025)
    lvl_hold = MODEL.residual_level(orig, STRAT.HOLDOUT[0], STRAT.HOLDOUT[1])
    al_all = MODEL.residual_alpha(orig, 1999, 2025)
    al_hold = MODEL.residual_alpha(orig, STRAT.HOLDOUT[0], STRAT.HOLDOUT[1])
    manifest["alpha"] = {"full": al_all, "holdout": al_hold, "level": lvl,
                         "level_holdout": lvl_hold}

    # 7. strategies, gates, leaderboards
    res = STRAT.run_all(orig)
    cert = STRAT.certify(res)
    srow = []
    for p in STRAT.PREREG:
        c = next((x for x in cert if x["id"] == p["id"]), {})
        srow.append([p["id"], p["name"], p["family"], p["units"], p["status"],
                     p["rule"], p["window"],
                     c.get("verdict", ""), c.get("failed_gates", ""),
                     c.get("n_holdout", ""), f(c.get("bss_holdout"), 4),
                     f(c.get("roi_holdout"), 4), f(c.get("clv_mean"), 3),
                     f(c.get("p_holm"), 4), f(c.get("calib_slope"), 3),
                     f(c.get("calib_intercept"), 4),
                     "A certified strategy must show positive Brier skill vs the close on the "
                     "holdout AND a positive residual alpha whose interval excludes zero. Seeing "
                     "either fail in the opposite direction (negative skill with an interval "
                     "above zero) is what would change the verdict to 'worse than the market'",
                     "backtested - never on the leaderboard"])
    manifest["tables"].append(write_csv("strategies", [
        "id", "name", "family", "units", "registration_status", "frozen_rule", "window",
        "verdict", "failed_gates", "n_holdout", "bss_holdout", "roi_holdout",
        "residual_alpha_pts", "p_holm", "calib_slope", "calib_intercept",
        "what_would_change_our_mind", "leaderboard_eligible"], srow))

    grow = []
    for gid, g in STRAT.GATES.items():
        grow.append([gid, g["rule"], g["why"], str(g["threshold"]),
                     "YES" if g.get("measurable_in_this_corpus", True) else "NO",
                     "https://github.com/nflverse/nfldata/blob/master/data/games.csv"])
    manifest["tables"].append(write_csv("gates", ["gate", "rule", "why", "threshold",
                                                 "measurable_in_corpus", "source_url"], grow))

    # winner / loser tables per window
    lrow = []
    for p in STRAT.PREREG:
        if p["id"] not in res["bets"]:
            continue
        for label, (lo, hi) in (("train", STRAT.TRAIN), ("validation", STRAT.VALIDATION),
                                ("holdout", STRAT.HOLDOUT)):
            s = res["summary"][(p["id"], label)]
            if s["n"] == 0:
                continue
            lrow.append([p["id"], p["family"], label, f"{lo}-{hi}", s["n"], s["wins"],
                         f(s["hit_rate"], 4), f(s["break_even_rate"], 4),
                         f(s["profit"], 3), f(s["roi"], 4),
                         f(s["brier"], 5), f(s["brier_market"], 5), f(s["bss"], 4),
                         f(s["p_value"], 4), f(s["max_season_share"], 3),
                         "https://github.com/nflverse/nfldata/blob/master/data/games.csv"])
    manifest["tables"].append(write_csv("leaderboard_graded", [
        "strategy", "family", "window", "seasons", "n", "wins", "hit_rate",
        "break_even_rate", "profit_units", "roi", "brier", "brier_market",
        "brier_skill", "p_value", "max_season_share", "source_url"], lrow))

    # 8. luck panel: 2026 teams from the corpus
    luck = []
    agg: dict[str, dict] = {}
    for g in games:
        if g["season"] != 2026 or g["status"] != "FINAL":
            continue
        for side in ("home", "away"):
            t = g[side]
            agg.setdefault(t, {"w": 0, "l": 0, "t": 0, "pf": 0, "pa": 0,
                               "one_score_w": 0, "one_score_g": 0})
        hs, as_ = g["home_score"], g["away_score"]
        h, a = agg[g["home"]], agg[g["away"]]
        h["pf"] += hs
        h["pa"] += as_
        a["pf"] += as_
        a["pa"] += hs
        if hs > as_:
            h["w"] += 1
            a["l"] += 1
        elif hs < as_:
            h["l"] += 1
            a["w"] += 1
        else:
            h["t"] += 1
            a["t"] += 1
        if abs(hs - as_) <= 8:
            if hs > as_:
                h["one_score_w"] += 1
            elif as_ > hs:
                a["one_score_w"] += 1
            h["one_score_g"] += 1
            a["one_score_g"] += 1
    EXP = 2.37   # Pythagorean exponent, a convention (flag F-11), applied to all teams alike
    for t in sorted(agg):
        d = agg[t]
        gp = d["w"] + d["l"] + d["t"]
        pf, pa = d["pf"], d["pa"]
        py = (pf ** EXP) / (pf ** EXP + pa ** EXP) * gp if pf or pa else 0.0
        actual = (d["w"] + 0.5 * d["t"]) / gp if gp else float("nan")
        luck_wins = actual * gp - py
        luck.append([t, gp, d["w"], d["l"], d["t"], pf, pa, f(pf / gp, 2), f(pa / gp, 2),
                     f(actual, 4), f(py / gp, 4), f(luck_wins, 2),
                     d["one_score_w"], d["one_score_g"],
                     f(d["one_score_w"] / d["one_score_g"], 4) if d["one_score_g"] else "",
                     f(EXP, 2),
                     "https://www.nfl.com/standings/league/2026/REG"])
    manifest["tables"].append(write_csv("luck_panel", [
        "team", "games", "w", "l", "t", "pf", "pa", "pf_per_game", "pa_per_game",
        "actual_win_pct", "pythagorean_win_pct", "luck_wins", "one_score_wins",
        "one_score_games", "one_score_win_pct", "pythagorean_exponent", "source_url"], luck))

    # 9. correlations from the corpus, n published with each
    def _n(v):
        """Corpus numerics are strings; a blank stays None, never zero."""
        if v is None or v == "" or v == "NA":
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def closes(g):
        return g["spread_line_home"] if g["spread_line_home"] is not None else None
    corr_rows = []
    pairs = [
        ("C-01", "closing spread vs actual margin", lambda g: closes(g), lambda g: g["result"]),
        ("C-02", "closing total vs actual total", lambda g: g["total_line"], lambda g: g["total"]),
        ("C-03", "closing spread vs closing total", lambda g: closes(g), lambda g: g["total_line"]),
        ("C-04", "home rest vs actual margin", lambda g: g["home_rest"], lambda g: g["result"]),
        ("C-05", "rest difference vs actual margin",
         lambda g: (g["home_rest"] - g["away_rest"])
         if g["home_rest"] is not None and g["away_rest"] is not None else None,
         lambda g: g["result"]),
        ("C-06", "wind vs actual total", lambda g: g["wind_mph"], lambda g: g["total"]),
        ("C-07", "temperature vs actual total", lambda g: g["temp_f"], lambda g: g["total"]),
    ]
    for cid, label, fx, fy in pairs:
        xs = [_n(fx(g)) for g in games if g["result"] is not None]
        ys = [_n(fy(g)) for g in games if g["result"] is not None]
        r, n = stats.pearson(xs, ys)
        lo, hi = stats.fisher_ci(r, n)
        corr_rows.append([cid, label, f(r, 4), str(n), f(lo, 4), f(hi, 4),
                          "pooled 1999-2026, all games with both values",
                          "https://github.com/nflverse/nfldata/blob/master/data/games.csv"])
    manifest["tables"].append(write_csv("correlations", [
        "id", "pair", "r", "n", "ci_lo", "ci_hi", "window", "source_url"], corr_rows))

    # 10. availability: depth, injuries, replacements, matrix, turnover
    depth = AV.build_depth()
    drow = []
    for s in depth["slots"]:
        drow.append([s["slot_id"], s["team"], s["unit"], s["position"],
                     s["rank1_raw"], s["rank1_names"], s["rank1_count"],
                     s["rank2"], s["rank3"], s["rank4"],
                     s["shared_rank1"], s["empty_rank1"], s["jersey_numbers_stripped"],
                     s["published_date"], s["captured_utc"], s["source_url"]])
    manifest["tables"].append(write_csv("depth_slots", [
        "slot_id", "team", "unit", "position", "rank1_raw", "rank1_names", "rank1_count",
        "rank2", "rank3", "rank4", "shared_rank1", "empty_rank1",
        "jersey_numbers_stripped", "published_date", "captured_utc", "source_url"], drow))

    inj = AV.load_injuries()
    irow = []
    for r in inj:
        irow.append([r["team"], r["player"], r["position"], r["injury"],
                     r["practice_status"], r["game_status"], r["retrieved_utc"],
                     r["source_url"]])
    manifest["tables"].append(write_csv("injuries", [
        "team", "player", "position", "injury", "practice_status", "game_status",
        "read_utc", "source_url"], irow))

    dlt = AV.injury_delta()
    manifest["tables"].append(write_csv("injury_delta", [
        "team", "player", "position", "prior_read_utc", "prior_practice", "prior_game",
        "now_read_utc", "now_practice", "now_game", "changed", "interpretation",
        "source_url"],
        [[d["team"], d["player"], d["position"], d["prior_captured_utc"],
          d["prior_practice"], d["prior_game"], d["now_captured_utc"],
          d["now_practice"], d["now_game"], d["changed"], d["interpretation"],
          d["source_url"]] for d in dlt]))

    rep = AV.replacements(depth["players"], inj)
    manifest["tables"].append(write_csv("replacements", [
        "team", "player", "position", "game_status", "slot", "position_slot",
        "replacement", "replacement_rank", "replacement_depth_tier", "finding", "source_url"],
        [[r["team"], r["player"], r["position"], r["game_status"], r["slot_id"],
          r["position_slot"], r["replacement"], r["replacement_rank"],
          r["replacement_depth_tier"], r["finding"], r["source_url"]] for r in rep]))

    mat = AV.deficiency_matrix(depth["players"], inj)
    manifest["tables"].append(write_csv("deficiency_matrix", [
        "attacking_team", "attacking_slot", "attacking_starter_out", "attacking_replacement",
        "attacking_replacement_rank", "defending_team", "defending_slot",
        "defending_starter_out", "defending_player_expected", "defending_depth_rank",
        "matchup_deficiency", "both_sides_deficient", "source_attacking", "source_defending"],
        [[m["attacking_team"], m["attacking_slot"], m["attacking_starter_out"],
          m["attacking_replacement"], m["attacking_replacement_rank"], m["defending_team"],
          m["defending_slot"], m["defending_starter_out"], m["defending_player_expected"],
          m["defending_depth_rank"], m["deficiency"], m["both_sides_deficient"],
          m["source_attacking"], m["source_defending"]] for m in mat]))

    to = AV.roster_turnover(depth["players"])
    manifest["tables"].append(write_csv("roster_turnover", [
        "player", "from_team", "to_team", "transaction_date", "appears_on_chart_of",
        "slot", "depth_capture_utc", "consistent", "source_transaction", "source_depth"],
        [[t["player"], t["from_team"], t["to_team"], t["transaction_date"],
          t["appears_on_chart_of"], t["slot"], t["depth_capture_utc"], t["consistent"],
          t["source_transaction"], t["source_depth"]] for t in to]))

    # 11. snapshots: ledger, freshness, capture log
    led = SNAP.build_ledger()
    lrows = SNAP.freshness(led["rows"], BUILD_UTC)
    manifest["tables"].append(write_csv("snapshot_ledger", [
        "source_id", "unit", "captured_utc", "age_hours", "max_age_hours", "state",
        "sha256", "bytes", "schema_fingerprint", "required_fields_present",
        "missing_fields", "publisher", "url", "file"],
        [[r["source_id"], r["unit"], r["captured_utc"], r["age_hours"],
          r["max_age_hours"], r["state"], r["sha256"], r["bytes"],
          r["schema_fingerprint"], r["required_fields_present"], r["missing_fields"],
          r["publisher"], r["url"], r["file"]] for r in lrows]))
    clog = SNAP.capture_log(led["rows"])
    manifest["tables"].append(write_csv("capture_log", [
        "unit", "distinct_clock_times", "first_capture", "last_capture", "can_replay", "captures"],
        [[c["unit"], c["distinct_clock_times"], c["first"], c["last"], c["can_replay"],
          c["captures"]] for c in clog]))
    manifest["snapshot_failures"] = led["failures"]
    manifest["checks"].append({"check": "capture schema contracts", "detail":
                               f"{len(led['failures'])} failures",
                               "pass": not led["failures"]})

    # 12. crosschecks, registers, audit
    cfl = []
    for c in checks:
        for r in c["rows"]:
            src = r.get("source_url", "")
            cfl.append([c["name"][:2], r.get("game_id") or r.get("team") or r.get("claim") or r.get("season", ""),
                        r.get("official", ""), r.get("corpus", ""), r.get("match", ""),
                        r.get("explanation", "") or r.get("note", ""), src])
    manifest["tables"].append(write_csv("crosschecks", [
        "check_group", "subject", "official", "corpus", "match", "note", "source_url"], cfl))

    manifest["tables"].append(write_csv("requirements", [
        "id", "requirement", "status", "blocking_gate", "number_that_would_clear_it", "page"],
        [[r["id"], r["requirement"], r["status"], r["gate"], r["clears"], r["page"]]
         for r in REG.REQUIREMENTS]))
    manifest["tables"].append(write_csv("questions", [
        "id", "question", "what_we_have", "what_we_do_not_have", "cheapest_route",
        "blocks", "severity"],
        [[q["id"], q["question"], q["have"], q["missing"], q["route"], q["blocks"],
          q["severity"]] for q in REG.QUESTIONS]))
    manifest["tables"].append(write_csv("suggestions", [
        "id", "title", "problem", "options", "recommendation", "what_would_change_the_call",
        "status", "page"],
        [[s["id"], s["title"], s["problem"], " | ".join(s["options"]), s["recommendation"],
          s["falsifier"], s["status"], s["page"]] for s in REG.SUGGESTIONS]))
    manifest["tables"].append(write_csv("flags", [
        "id", "severity", "title", "detail", "source_url", "status"],
        [[x["id"], x["severity"], x["title"], x["detail"], x["source"], x["status"]]
         for x in REG.FLAGS]))
    manifest["tables"].append(write_csv("audit", [
        "id", "claim", "verification_performed", "result", "source_url"],
        [[a[0], a[1], a[2], a[3], a[4]] for a in REG.AUDIT]))

    # 13. schedule page: week 11 fixtures + the dated announcement claims
    ann = json.loads((DATA / "official" / "schedule_announcement_2026.json").read_text())
    sched = next(c for c in checks if c["name"].startswith("C."))
    manifest["tables"].append(write_csv("schedule_announcement", [
        "claim_id", "official_claim", "checked_against", "result", "match", "source_url"],
        [[r["claim"], r["official"], r["corpus"], "", r["match"], ann["url"]]
         for r in sched["rows"]]))

    slate = []
    for g in games:
        if g["season"] == 2026 and g["week"] == 11:
            slate.append([g["game_id"], g["gameday"], g["gametime"], g["weekday"],
                          g["away"], g["home"], g["stadium"], g["location"],
                          f(g["spread_line_home"], 2), f(g["total_line"], 2),
                          f(g["home_moneyline"], 0), f(g["away_moneyline"], 0),
                          "https://www.nfl.com/schedules/2026/by-week/week-11"])
    manifest["tables"].append(write_csv("slate_week11", [
        "game_id", "gameday", "gametime_et", "weekday", "away", "home", "stadium",
        "location", "market_spread_home", "market_total", "market_home_ml",
        "market_away_ml", "source_url"], slate))

    manifest["counts"] = {
        "originated_markets": len(orig),
        "priced_markets": len(prow),
        "graded_games": sum(1 for g in games if g["result"] is not None),
        "seasons": len({g["season"] for g in games}),
        "strategies": len(STRAT.PREREG),
        "certified": sum(1 for c in cert if c["certified"] == "yes"),
        "requirements": len(REG.REQUIREMENTS),
        "met": sum(1 for r in REG.REQUIREMENTS if r["status"] == "met"),
        "partial": sum(1 for r in REG.REQUIREMENTS if r["status"] == "partial"),
        "blocked": sum(1 for r in REG.REQUIREMENTS if r["status"] == "blocked"),
        "questions": len(REG.QUESTIONS),
        "suggestions": len(REG.SUGGESTIONS),
        "flags": len(REG.FLAGS),
        "depth_slots_parsed": len(depth["slots"]),
        "depth_clubs_parsed": depth["checks"]["clubs"],
        "injury_rows": len(inj),
        "matrix_rows": len(mat),
        "correlations": len(corr_rows),
        "ledger_rows": len(led["rows"]),
    }
    manifest["depth_checks"] = depth["checks"]
    # `certifications` used to hold EVERY graded row, which made
    # len(certifications) read as "14 certified" on a page whose whole
    # point is that zero are certified. The key now names what it holds.
    manifest["strategy_verdicts"] = cert
    manifest["certified_strategies"] = [x["id"] for x in cert
                                        if x.get("certified") == "yes"]

    # write manifest + all derived rows for the site builder
    manifest["index_badge"] = {
        "href": "nfl-season-941fe39f/index.html",
        "html": ("<!-- own5-index-badge:941fe39f -->"
                 '<p id="desk-941fe39f-link" style="margin:10px 0 0">'
                 '<a href="nfl-season-941fe39f/index.html">NFL Season Desk (941fe39f) &#8599;</a>'
                 " &middot; 2026 season, 7,058 originated markets, 0 certified</p>"
                 "<!-- /own5-index-badge:941fe39f -->"),
    }
    def quantise(o):
        if isinstance(o, float):
            return q(o)
        if isinstance(o, dict):
            return {k: quantise(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [quantise(v) for v in o]
        return o

    (DERIVED / "manifest.json").write_text(
        json.dumps(quantise(manifest), indent=1) + "\n")
    (DERIVED / "crosschecks.json").write_text(json.dumps(checks, indent=1) + "\n")
    print(json.dumps(manifest["counts"], indent=1))
    for c in checks:
        print(f"  {c['verdict']:<28} {c['name'][:70]}")
    for c in manifest["checks"]:
        print(f"  [{'PASS' if c['pass'] else 'FAIL'}] {c['check']} -> {c['detail']}")
    return 0 if all(c["pass"] for c in manifest["checks"]) else 1


if __name__ == "__main__":
    sys.exit(main())

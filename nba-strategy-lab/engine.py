#!/usr/bin/env python3
"""Deterministic, standard-library NBA research engine.

Raw values are frozen transcriptions with official NBA URLs. All model values are
analyst-derived. No sportsbook quote, current availability, profit, or skill claim
is inferred. The engine fails closed: candidates cannot rank or receive rewards.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import NormalDist, mean
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data"
NORMAL = NormalDist()
SEASON_URL = "https://www.nba.com/stats/teams/traditional?Season={season}&SeasonType=Regular%20Season"
PLAYER_URLS = {
    "Luka Doncic": "https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26",
    "Anthony Edwards": "https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26",
}
TEAM_URL = SEASON_URL.format(season="2026-27")
GAME_URL = "https://www.nba.com/stats/teams/boxscores?Season=2026-27&SeasonType=Regular%20Season"
SCHEDULE_URL = "https://www.nba.com/schedule?month=11&year=2026"
GLOSSARY_URL = "https://www.nba.com/stats/help/glossary"
INJURY_URL = "https://official.nba.com/nba-injury-report-2026-27-season/"
MIN_TEST = 200
PRIOR_GAMES = 20.0  # disclosed analyst regularization choice, not an NBA estimate
OFFICIAL_HOSTS = {"www.nba.com", "official.nba.com"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: list[dict]) -> None:
    path = OUT / name
    if not rows:
        raise ValueError(f"refusing empty output: {name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def f(value: float | None, digits: int = 4) -> float | None:
    return None if value is None else round(value, digits)


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("Pearson requires paired n >= 2")
    mx, my = mean(xs), mean(ys)
    xx = sum((x - mx) ** 2 for x in xs)
    yy = sum((y - my) ** 2 for y in ys)
    if xx == 0 or yy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(xx * yy)


def fisher_ci(r: float | None, n: int) -> tuple[float | None, float | None]:
    if r is None or n <= 3 or abs(r) >= 1:
        return None, None
    z = math.atanh(r)
    se = 1 / math.sqrt(n - 3)
    return math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)


def phi(a: list[int], b: list[int]) -> float | None:
    return pearson(a, b)


def binomial_tail(k: int, n: int, p: float) -> float:
    if not 0 <= k <= n or not 0 <= p <= 1:
        raise ValueError("invalid binomial inputs")
    return min(1.0, sum(math.comb(n, x) * p**x * (1 - p) ** (n - x) for x in range(k, n + 1)))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    radius = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return center - radius, center + radius


def holm(rows: list[dict], key: str = "p_one_sided") -> None:
    ordered = sorted(rows, key=lambda row: row[key])
    running = 0.0
    for i, row in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - i) * row[key]))
        row["p_holm"] = f(running, 6)


def american(p: float) -> int:
    if not 0 < p < 1:
        raise ValueError("probability must be in (0,1)")
    value = 100 * (1 - p) / p if p <= 0.5 else -100 * p / (1 - p)
    return int(round(value))


def total_of(row: dict[str, str]) -> float:
    return 2 * float(row["pts_pg"]) - float(row["plus_minus_pg"])


def validate(teams: list[dict], games: list[dict], players: list[dict], schedule: list[dict]) -> list[dict]:
    checks: list[dict] = []

    def check(group: str, name: str, ok: bool, detail: str, source: str) -> None:
        checks.append({"group": group, "check": name, "status": "PASS" if ok else "FAIL", "detail": detail, "source_url": source})
        if not ok:
            raise AssertionError(f"{group}: {name}: {detail}")

    for filename, rows in (("team_seasons.csv", teams), ("games_sample_2026_27.csv", games), ("player_games.csv", players), ("schedule.csv", schedule)):
        ok = all(urlparse(r["source_url"]).scheme == "https" and urlparse(r["source_url"]).hostname in OFFICIAL_HOSTS and r["source_url"] for r in rows)
        check("provenance", filename, ok, f"{len(rows)} rows; HTTPS official NBA host on every row", rows[0]["source_url"])
    by_season = defaultdict(list)
    for row in teams:
        by_season[row["season"]].append(row)
        check("team identity", f'{row["season"]} {row["team"]} GP=W+L', int(row["gp"]) == int(row["w"]) + int(row["l"]), f'{row["gp"]}={row["w"]}+{row["l"]}', row["source_url"])
    for season, rows in sorted(by_season.items()):
        check("team aggregate", f"{season} 30 unique teams", len(rows) == 30 and len({r["team"] for r in rows}) == 30, f"{len(rows)} rows", rows[0]["source_url"])
        check("team aggregate", f"{season} wins=losses", sum(int(r["w"]) for r in rows) == sum(int(r["l"]) for r in rows), f'W={sum(int(r["w"]) for r in rows)} L={sum(int(r["l"]) for r in rows)}', rows[0]["source_url"])
        if season != "2026-27":
            check("team aggregate", f"{season} full season", all(int(r["gp"]) == 82 for r in rows), "30 teams × 82 games", rows[0]["source_url"])
    grouped_games = defaultdict(list)
    for row in games:
        grouped_games[row["game_id"]].append(row)
        check("game identity", f'{row["game_id"]} {row["team"]} points', int(row["pts"]) == 2 * int(row["fgm"]) + int(row["fg3m"]) + int(row["ftm"]), "PTS=2×FGM+3PM+FTM", row["source_url"])
    check("game aggregate", "22 games / 44 rows", len(games) == 44 and len(grouped_games) == 22, f"{len(grouped_games)} games", GAME_URL)
    for game_id, rows in grouped_games.items():
        a, b = rows
        ok = len(rows) == 2 and a["opp"] == b["team"] and b["opp"] == a["team"] and int(a["home"]) + int(b["home"]) == 1 and int(a["plus_minus"]) == int(a["pts"]) - int(b["pts"]) and int(b["plus_minus"]) == int(b["pts"]) - int(a["pts"])
        check("game identity", f"{game_id} paired box score", ok, "two opponents; one home; +/- mirrors score", a["source_url"])
    seen = set()
    counts = Counter()
    for row in players:
        key = (row["player_id"], row["game_id"])
        check("player identity", f'{row["player"]} {row["game_id"]} points', int(row["pts"]) == 2 * int(row["fgm"]) + int(row["tpm"]) + int(row["ftm"]), "PTS=2×FGM+3PM+FTM", row["source_url"])
        check("player identity", f'{row["player"]} {row["game_id"]} rebounds', int(row["reb"]) == int(row["oreb"]) + int(row["dreb"]), "REB=OREB+DREB", row["source_url"])
        check("player identity", f'{row["player"]} {row["game_id"]} unique', key not in seen, "unique player-game", row["source_url"])
        seen.add(key)
        counts[row["player"]] += 1
    check("player aggregate", "expected frozen coverage", counts == {"Luka Doncic": 64, "Anthony Edwards": 61}, str(dict(counts)), PLAYER_URLS["Luka Doncic"])
    ids = [r["game_id"] for r in schedule]
    team_codes = {r["team"] for r in teams}
    check("schedule", "16 unique games", len(schedule) == 16 and len(set(ids)) == 16, "14 on 2026-11-04; 2 on 2026-11-05", SCHEDULE_URL)
    check("schedule", "known team codes", all(r["home"] in team_codes and r["away"] in team_codes and r["home"] != r["away"] for r in schedule), "all 30 teams appear", SCHEDULE_URL)
    return checks


def prior_game_rows(games: list[dict], s25: dict[str, dict]) -> list[dict]:
    grouped = defaultdict(dict)
    for row in games:
        grouped[row["game_id"]]["home" if row["home"] == "1" else "away"] = row
    output = []
    for game_id, pair in sorted(grouped.items(), key=lambda item: (item[1]["home"]["date"], item[0])):
        h, a = pair["home"], pair["away"]
        margin = float(s25[h["team"]]["plus_minus_pg"]) - float(s25[a["team"]]["plus_minus_pg"])
        total = (total_of(s25[h["team"]]) + total_of(s25[a["team"]])) / 2
        output.append({"game_id": game_id, "date": h["date"], "home": h["team"], "away": a["team"], "pred_margin": margin, "actual_margin": int(h["pts"]) - int(a["pts"]), "pred_total": total, "actual_total": int(h["pts"]) + int(a["pts"]), "source_url": h["source_url"]})
    return output


def line_rows(schedule: list[dict], seasons: dict[str, dict[str, dict]], sigma: float) -> list[dict]:
    s25, s26 = seasons["2025-26"], seasons["2026-27"]
    league25 = mean(float(r["plus_minus_pg"]) for r in s25.values())
    league26 = mean(float(r["plus_minus_pg"]) for r in s26.values())
    league_total26 = mean(total_of(r) for r in s26.values())
    rows = []
    for game in schedule:
        home, away = game["home"], game["away"]
        ratings, total_devs = {}, {}
        for team in (home, away):
            cur, prior = s26[team], s25[team]
            gp = int(cur["gp"])
            ratings[team] = (gp * float(cur["plus_minus_pg"]) + PRIOR_GAMES * float(prior["plus_minus_pg"])) / (gp + PRIOR_GAMES)
            current_dev = total_of(cur) - league_total26
            prior_dev = total_of(prior) - mean(total_of(r) for r in s25.values())
            total_devs[team] = (gp * current_dev + PRIOR_GAMES * prior_dev) / (gp + PRIOR_GAMES)
        margin = ratings[home] - ratings[away]  # zero-HFA disclosed convention
        total = league_total26 + total_devs[home] + total_devs[away]
        hp = NORMAL.cdf(margin / sigma)
        rows.append({"game_id": game["game_id"], "date": game["date"], "tip_et_24h": game["tip_et_24h"], "matchup": f"{away} @ {home}", "model_home_margin": f(margin, 2), "model_home_spread": f(-margin, 2), "model_total": f(total, 2), "model_home_win_probability": f(hp, 4), "model_home_fair_american": american(hp), "model_away_fair_american": american(1 - hp), "market_spread": "", "market_total": "", "market_price": "", "market_edge": "", "status": "ARCHIVED RESEARCH — NOT ACTIONABLE", "source_url": game["source_url"], "ratings_source_url": TEAM_URL})
    return rows


def build_strategies(games: list[dict], players: list[dict]) -> tuple[list[dict], list[dict]]:
    candidates = []
    # Team tests use only 2025-26 ratings to predict the later frozen games.
    team_defs = [
        ("S01", "Single · prior winner", "single", "Select model favorite on every game.", lambda r: True, lambda r: (r["pred_margin"] > 0) == (r["actual_margin"] > 0)),
        ("S02", "Single · 3-point conviction", "single", "Select only when absolute prior margin difference is at least 3.", lambda r: abs(r["pred_margin"]) >= 3, lambda r: (r["pred_margin"] > 0) == (r["actual_margin"] > 0)),
        ("S03", "Single · totals direction", "single", "Prior total above 231.22 (2025-26 unweighted league mean) predicts realized total above that fixed benchmark; no market total used.", lambda r: True, lambda r: (r["pred_total"] > 231.22) == (r["actual_total"] > 231.22)),
    ]
    for sid, name, track, rule, selected, hit in team_defs:
        chosen = [r for r in games if selected(r)]
        for row in chosen:
            candidates.append({"strategy_id": sid, "strategy": name, "track": track, "rule": rule, "event": f'{row["date"]} {row["away"]}@{row["home"]}', "split": "holdout", "hit": int(hit(row)), "source_url": row["source_url"]})
    # Top two absolute-margin favorites per date form a fixed two-leg research parlay.
    dates = defaultdict(list)
    for row in games:
        dates[row["date"]].append(row)
    for date, rows in sorted(dates.items()):
        legs = sorted(rows, key=lambda r: abs(r["pred_margin"]), reverse=True)[:2]
        won = all((r["pred_margin"] > 0) == (r["actual_margin"] > 0) for r in legs)
        candidates.append({"strategy_id": "S04", "strategy": "Parlay · daily top two favorites", "track": "parlay", "rule": "Two largest absolute prior-margin favorites each date; joint success required.", "event": date + " " + "/".join(r["game_id"] for r in legs), "split": "holdout", "hit": int(won), "source_url": legs[0]["source_url"]})
    # Chronological per-player 60/40 split. Thresholds are fixed, not optimized.
    test_rows = []
    for player in sorted({r["player"] for r in players}):
        rows = sorted((r for r in players if r["player"] == player), key=lambda r: (r["game_date"], r["game_id"]))
        cut = int(len(rows) * 0.6)
        for r in rows[:cut]:
            test_rows.append({**r, "split": "development"})
        for r in rows[cut:]:
            test_rows.append({**r, "split": "holdout"})
    prop_defs = [
        ("S05", "Prop single · Dončić 25+ points", "prop_single", lambda r: r["player"] == "Luka Doncic", lambda r: int(r["pts"]) >= 25),
        ("S06", "Prop single · Edwards 25+ points", "prop_single", lambda r: r["player"] == "Anthony Edwards", lambda r: int(r["pts"]) >= 25),
        ("S07", "Prop combo · 25+ points & 5+ rebounds", "prop_combo", lambda r: True, lambda r: int(r["pts"]) >= 25 and int(r["reb"]) >= 5),
        ("S08", "Prop combo · 25+ points & 3+ threes", "prop_combo", lambda r: True, lambda r: int(r["pts"]) >= 25 and int(r["tpm"]) >= 3),
        ("S09", "Prop combo · 25+ points & 5+ assists", "prop_combo", lambda r: True, lambda r: int(r["pts"]) >= 25 and int(r["ast"]) >= 5),
    ]
    for sid, name, track, selected, hit in prop_defs:
        for row in test_rows:
            if selected(row):
                candidates.append({"strategy_id": sid, "strategy": name, "track": track, "rule": name.split("·", 1)[1].strip() + "; chronological 60/40 split; threshold fixed before holdout summary.", "event": f'{row["player"]} {row["game_date"]} {row["game_id"]}', "split": row["split"], "hit": int(hit(row)), "source_url": row["source_url"]})
    strategies = []
    for sid in sorted({r["strategy_id"] for r in candidates}):
        all_rows = [r for r in candidates if r["strategy_id"] == sid]
        dev = [r for r in all_rows if r["split"] == "development"]
        test = [r for r in all_rows if r["split"] == "holdout"]
        k, n = sum(r["hit"] for r in test), len(test)
        if dev:
            null = sum(r["hit"] for r in dev) / len(dev)
            null = min(max(null, 1e-6), 1 - 1e-6)
            dev_note = f"{sum(r['hit'] for r in dev)}/{len(dev)} development hit rate"
        else:
            null = 0.5
            dev_note = "No development sample; directional null p=0.5"
        low, high = wilson(k, n)
        strategies.append({"strategy_id": sid, "strategy": all_rows[0]["strategy"], "track": all_rows[0]["track"], "rule": all_rows[0]["rule"], "development": dev_note, "holdout_n": n, "holdout_hits": k, "holdout_hit_rate": f(k / n, 4), "ci95_low": f(low, 4), "ci95_high": f(high, 4), "null_probability": f(null, 6), "p_one_sided": binomial_tail(k, n, null), "roi": "", "market_price": "", "qualification": "NOT QUALIFIED", "rank": "", "score": "", "reward": "", "source_url": test[0]["source_url"]})
    holm(strategies)
    return candidates, strategies


def correlations(players: list[dict], team_games: list[dict]) -> list[dict]:
    rows = []
    groups = [("Pooled two players", players)] + [(p, [r for r in players if r["player"] == p]) for p in sorted(PLAYER_URLS)]
    pairs = [("pts", "reb", "Points × rebounds"), ("pts", "ast", "Points × assists"), ("pts", "tpm", "Points × made threes"), ("pts", "win", "Points × team win")]
    for group, data in groups:
        for x, y, label in pairs:
            xs = [float(r[x]) if x != "win" else int(r["result"] == "W") for r in data]
            ys = [float(r[y]) if y != "win" else int(r["result"] == "W") for r in data]
            r = pearson(xs, ys)
            lo, hi = fisher_ci(r, len(data))
            rows.append({"analysis": label, "group": group, "kind": "Pearson" if y != "win" else "point-biserial", "n": len(data), "estimate": f(r), "ci95_low": f(lo), "ci95_high": f(hi), "joint_hit_rate": "", "independence_product": "", "lift": "", "interpretation": "Descriptive; not proof of profitable combo pricing", "source_url": data[0]["source_url"]})
        thresholds = [("25+ PTS & 5+ REB", lambda r: int(r["pts"]) >= 25, lambda r: int(r["reb"]) >= 5), ("25+ PTS & 3+ 3PM", lambda r: int(r["pts"]) >= 25, lambda r: int(r["tpm"]) >= 3), ("25+ PTS & 5+ AST", lambda r: int(r["pts"]) >= 25, lambda r: int(r["ast"]) >= 5)]
        for label, af, bf in thresholds:
            a, b = [int(af(r)) for r in data], [int(bf(r)) for r in data]
            pa, pb = mean(a), mean(b)
            joint = mean(x and y for x, y in zip(a, b))
            product = pa * pb
            est = phi(a, b)
            lo, hi = fisher_ci(est, len(data))
            rows.append({"analysis": label, "group": group, "kind": "phi / joint rate", "n": len(data), "estimate": f(est), "ci95_low": f(lo), "ci95_high": f(hi), "joint_hit_rate": f(joint, 4), "independence_product": f(product, 4), "lift": f(joint / product, 4) if product else "", "interpretation": "Empirical joint rate; pool does not establish causal or future dependence", "source_url": data[0]["source_url"]})
    # Same-date two-leg parlay diagnostic, kept separate from player correlations.
    dates = defaultdict(list)
    for r in team_games:
        dates[r["date"]].append(r)
    parlay_hits, leg_hits = [], []
    for date, games in sorted(dates.items()):
        legs = sorted(games, key=lambda r: abs(r["pred_margin"]), reverse=True)[:2]
        hits = [int((r["pred_margin"] > 0) == (r["actual_margin"] > 0)) for r in legs]
        parlay_hits.append(int(all(hits)))
        leg_hits.extend(hits)
    joint, product = mean(parlay_hits), mean(leg_hits) ** 2
    rows.append({"analysis": "Daily top-two favorite parlay", "group": "22 games / 3 dates", "kind": "joint vs independence", "n": len(parlay_hits), "estimate": "", "ci95_low": "", "ci95_high": "", "joint_hit_rate": f(joint, 4), "independence_product": f(product, 4), "lift": f(joint / product, 4) if product else "", "interpretation": "Only three parlays; phi blank and no inference", "source_url": team_games[0]["source_url"]})
    return rows


def gates_and_board(strategies: list[dict]) -> tuple[list[dict], list[dict]]:
    gates = []
    for s in strategies:
        checks = {
            "G01 official input provenance": True,
            "G02 frozen rule and chronological holdout": True,
            "G03 at least 200 holdout events": s["holdout_n"] >= MIN_TEST,
            "G04 Holm-adjusted p < 0.05": s["p_holm"] < 0.05,
            "G05 CI lower bound beats null": s["ci95_low"] > s["null_probability"],
            "G06 timestamped market and settlement": False,
            "G07 independent prospective replication": False,
            "G08 combo dependence robustness": s["track"] not in {"parlay", "prop_combo"},
        }
        failed = [name for name, ok in checks.items() if not ok]
        for name, ok in checks.items():
            gates.append({"strategy_id": s["strategy_id"], "gate": name, "status": "PASS" if ok else "FAIL", "evidence": "Computed from frozen holdout" if name.startswith(("G03", "G04", "G05")) else ("Policy satisfied" if ok else "Required evidence absent; fail closed"), "source_url": s["source_url"]})
        s["failed_gates"] = len(failed)
        s["qualification"] = "QUALIFIED" if not failed else "NOT QUALIFIED"
        if not failed:
            raise AssertionError("qualification requires a scoring/reward policy not present in this snapshot")
    board = [{"rank": "", "strategy_id": s["strategy_id"], "strategy": s["strategy"], "track": s["track"], "eligible": "NO", "deflated_score": "", "roi": "", "reward": "", "reason": f'{s["failed_gates"]} gate(s) open; ranking disabled', "source_url": s["source_url"]} for s in strategies]
    return gates, board


def main() -> None:
    teams = read_csv(RAW / "team_seasons.csv")
    games = read_csv(RAW / "games_sample_2026_27.csv")
    players = read_csv(RAW / "player_games.csv")
    schedule = read_csv(RAW / "schedule.csv")
    checks = validate(teams, games, players, schedule)
    seasons = {s: {r["team"]: r for r in teams if r["season"] == s} for s in sorted({r["season"] for r in teams})}
    prior = prior_game_rows(games, seasons["2025-26"])
    rmse = math.sqrt(mean((r["actual_margin"] - r["pred_margin"]) ** 2 for r in prior))
    lines = line_rows(schedule, seasons, rmse)
    ledger, strategies = build_strategies(prior, players)
    corr = correlations(players, prior)
    gates, board = gates_and_board(strategies)
    flags = [
        {"flag_id": "F01", "severity": "HIGH", "item": "No verified sportsbook quotes or settlement ledger", "disposition": "Market prices, ROI, edges, ranks and rewards blank; all strategies fail closed.", "source_url": SCHEDULE_URL},
        {"flag_id": "F02", "severity": "HIGH", "item": "Small, non-prospective samples", "disposition": "22 team games, 3 parlays and at most 50 pooled prop holdouts; no skill claim.", "source_url": GAME_URL},
        {"flag_id": "F03", "severity": "HIGH", "item": "Current player availability not refreshed", "disposition": "Archived lines are not actionable; no injury adjustment inferred.", "source_url": INJURY_URL},
        {"flag_id": "F04", "severity": "MEDIUM", "item": "Zero home-court advantage is an analyst convention", "disposition": "Model margin omits HFA; residual scale comes from the same 22-game diagnostic and is not validated.", "source_url": TEAM_URL},
        {"flag_id": "F05", "severity": "MEDIUM", "item": "Two-player convenience sample", "disposition": "Correlations and prop thresholds do not generalize to the league.", "source_url": PLAYER_URLS["Luka Doncic"]},
        {"flag_id": "F06", "severity": "MEDIUM", "item": "External source pages were not freshly fetched in this session", "disposition": "Frozen official-source transcriptions inherited from reviewed repo snapshots; identities recomputed. Manual source review links supplied.", "source_url": GLOSSARY_URL},
        {"flag_id": "F07", "severity": "LOW", "item": "Archived schedule", "disposition": "2026-11-04/05 lines are reproducible historical research, not a current slate.", "source_url": SCHEDULE_URL},
        {"flag_id": "F08", "severity": "LOW", "item": "Rewards are unfunded", "disposition": "Reward cells blank; proposed 50/30/20 allocation activates only for eligible entries and a separately funded pool.", "source_url": SCHEDULE_URL},
        {"flag_id": "F09", "severity": "LOW", "item": "Blank source fields retained", "disposition": "Archived schedule venues are blank; two 2026-11-05 tip times are blank. No values inferred.", "source_url": SCHEDULE_URL},
    ]
    sources = [
        {"source_id": "S01", "publisher": "NBA", "dataset": "2026-11 schedule", "url": SCHEDULE_URL, "scope": "16 archived schedule rows"},
        {"source_id": "S02", "publisher": "NBA", "dataset": "2026-27 traditional team stats", "url": TEAM_URL, "scope": "30 team rows"},
        {"source_id": "S03", "publisher": "NBA", "dataset": "2025-26 traditional team stats", "url": SEASON_URL.format(season="2025-26"), "scope": "30 team rows / priors"},
        {"source_id": "S04", "publisher": "NBA", "dataset": "2024-25 traditional team stats", "url": SEASON_URL.format(season="2024-25"), "scope": "30 team rows / evidence audit"},
        {"source_id": "S05", "publisher": "NBA", "dataset": "2026-27 team box scores", "url": GAME_URL, "scope": "22 paired games / 44 rows"},
        {"source_id": "S06", "publisher": "NBA", "dataset": "Luka Dončić 2025-26 box scores", "url": PLAYER_URLS["Luka Doncic"], "scope": "64 player-game rows"},
        {"source_id": "S07", "publisher": "NBA", "dataset": "Anthony Edwards 2025-26 box scores", "url": PLAYER_URLS["Anthony Edwards"], "scope": "61 player-game rows"},
        {"source_id": "S08", "publisher": "NBA", "dataset": "Statistics glossary", "url": GLOSSARY_URL, "scope": "Definitions/context"},
        {"source_id": "S09", "publisher": "NBA Official", "dataset": "2026-27 injury reporting", "url": INJURY_URL, "scope": "Availability limitation context"},
    ]
    write_csv("lines.csv", lines)
    write_csv("strategies.csv", strategies)
    write_csv("strategy_ledger.csv", ledger)
    write_csv("correlations.csv", corr)
    write_csv("gates.csv", gates)
    write_csv("leaderboard.csv", board)
    write_csv("flags.csv", flags)
    write_csv("sources.csv", sources)
    write_csv("audit_checks.csv", checks)
    summary = {"as_of": "2026-11-05", "official_source_rows": len(teams) + len(games) + len(players) + len(schedule), "audit_checks": len(checks), "audit_failures": 0, "lines": len(lines), "candidates": len(strategies), "qualified": sum(s["qualification"] == "QUALIFIED" for s in strategies), "rewards": 0, "correlation_rows": len(corr), "flags": len(flags), "holdout_games": len(prior), "player_games": len(players), "margin_diagnostic_rmse": f(rmse, 4), "min_holdout_required": MIN_TEST, "prior_games": PRIOR_GAMES}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

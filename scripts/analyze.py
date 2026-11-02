#!/usr/bin/env python3
"""Rebuild the reproducible, historical NFL research report using the stdlib.

The NFL inputs are official game results and manually checked NFL.com player-log
transcriptions. Model outputs are estimates, not official or offered prices.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME_PATH = ROOT / "data/raw/nfl_2017_games.csv"
PLAYER_PATH = ROOT / "data/raw/player_pair_games.csv"
OUTPUT = ROOT / "data/derived/report.json"
GAME_SHA256 = "f5bbd13d9c711c07e3d4a5b674eb25c1f5f9ced099729337bfd366b5229199ed"
REVISION = "9ad0b4b2ea36697e29e44e2399512cc1ce70358c"
GAME_SOURCE = f"https://github.com/nfl-football-ops/Big-Data-Bowl/blob/{REVISION}/Data/games.csv"
SCHEMA_SOURCE = f"https://github.com/nfl-football-ops/Big-Data-Bowl/blob/{REVISION}/schema.md"
NOAA_SOURCE = "https://vlab.ncep.noaa.gov/web/mdl/ndfd-verification-score-definitions"
NIST_SOURCE = "https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/correlat.htm"
RULES_SOURCE = "https://www.gamblingcommission.gov.uk/licensees-and-businesses/lccp/condition/4-2-6-display-of-rules-betting"
FTC_SOURCE = "https://www.ftc.gov/news-events/news/press-releases/2002/06/ftc-warns-consumers-about-online-gambling-children"


def mean(values):
    return statistics.fmean(values)


def correlation(xs, ys):
    """Pearson r; return None if the statistic is undefined."""
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    if len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    return statistics.correlation(xs, ys)


def binary_comparison(xs, ys):
    """Paired 0/1 outcomes, observed joint vs product of sample marginals."""
    if len(xs) != len(ys) or not xs or any(x not in (0, 1) for x in xs + ys):
        raise ValueError("binary event vectors must be equally sized, nonempty, and 0/1")
    n = len(xs)
    n11 = sum(a == 1 and b == 1 for a, b in zip(xs, ys))
    n10 = sum(a == 1 and b == 0 for a, b in zip(xs, ys))
    n01 = sum(a == 0 and b == 1 for a, b in zip(xs, ys))
    n00 = sum(a == 0 and b == 0 for a, b in zip(xs, ys))
    return {
        "n": n,
        "phi": correlation(xs, ys),
        "p_a": sum(xs) / n,
        "p_b": sum(ys) / n,
        "joint": n11 / n,
        "independent_product": (sum(xs) / n) * (sum(ys) / n),
        "n11": n11,
        "n10": n10,
        "n01": n01,
        "n00": n00,
    }


def fair_odds(p):
    """Hypothetical no-vig two-outcome odds; assumes a tie/void returns stake."""
    if not 0 < p < 1:
        raise ValueError("probability must be strictly between 0 and 1")
    # Retain unrounded numerical values; formatting is a presentation concern.
    american = -100 * p / (1 - p) if p >= .5 else 100 * (1 - p) / p
    return {"decimal": 1 / p, "american": american}


def parse_games(path=GAME_PATH, require_official_hash=True):
    raw = path.read_bytes()
    if require_official_hash and hashlib.sha256(raw).hexdigest() != GAME_SHA256:
        raise ValueError("Game file differs from the pinned NFL source. Do not publish it as verified.")
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    games, ids, teams_by_week = [], set(), defaultdict(set)
    for line, r in enumerate(rows, start=2):
        game_id = r["gameId"]
        week = int(r["week"])
        season = int(r["season"])
        home, away = r["homeTeamAbbr"], r["visitorTeamAbbr"]
        if game_id in ids or home == away or home in teams_by_week[week] or away in teams_by_week[week]:
            raise ValueError(f"Duplicate game/team in week at source line {line}")
        if season != 2017 or week not in range(1, 7):
            raise ValueError(f"Unexpected season/week at source line {line}")
        h, a = int(r["HomeScore"]), int(r["VisitorScore"])
        if h < 0 or a < 0:
            raise ValueError(f"Negative score at source line {line}")
        ids.add(game_id)
        teams_by_week[week].update((home, away))
        games.append({
            "id": game_id,
            "season": season,
            "week": week,
            "date": r["gameDate"],
            "home": home,
            "away": away,
            "home_name": r["homeDisplayName"],
            "away_name": r["visitorDisplayName"],
            "home_score": h,
            "away_score": a,
            "source": f"{GAME_SOURCE}#L{line}",
        })
    if require_official_hash and (len(games) != 91 or Counter(g["week"] for g in games) != {1: 15, 2: 16, 3: 16, 4: 16, 5: 14, 6: 14}):
        raise ValueError("Unexpected official sample dimensions")
    return sorted(games, key=lambda g: (g["week"], g["date"][-4:], g["date"][:2], g["date"][3:5], g["id"]))


def parse_players(path=PLAYER_PATH):
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    seen = set()
    for r in rows:
        r["season"], r["week"] = int(r["season"]), int(r["week"])
        key = (r["season"], r["week"], r["date"], r["opponent"], r["result"], r["qb"], r["receiver"])
        if key in seen:
            raise ValueError(f"Duplicate player-game row: {key}")
        seen.add(key)
        for field in ("qb_passing_yards", "receiver_yards", "receiver_receptions"):
            r[field] = int(r[field]) if r[field] else None
        for field in ("qb_source", "receiver_source"):
            if not r[field].startswith("https://www.nfl.com/players/"):
                raise ValueError(f"Non-official player source in {key}")
        r["paired"] = r["qb_passing_yards"] is not None and r["receiver_yards"] is not None
    return rows


def logistic(value):
    return 1 / (1 + math.exp(-value))


def walk_forward(games):
    """Compute each whole week's forecasts before processing that week's scores.

    Equal 1500 Elo ratings, K=20 and no home/neutral adjustment. The second
    candidate is logistic((home prior mean margin - away prior mean margin)/14).
    Only weeks 4–6 are scored. No ties occur in the official six-week sample;
    if a tie appears, it is excluded from binary evaluation, and used as .5 in Elo.
    """
    ratings = defaultdict(lambda: 1500.0)
    # per-team [games, points scored, points conceded]
    form = defaultdict(lambda: [0, 0, 0])
    all_prior_scores = []
    predictions = []
    for week in sorted({g["week"] for g in games}):
        week_games = [g for g in games if g["week"] == week]
        week_predictions = []
        for game in week_games:
            h, a = game["home"], game["away"]
            elo_p = 1 / (1 + 10 ** ((ratings[a] - ratings[h]) / 400))
            hg, hpf, hpa = form[h]
            ag, apf, apa = form[a]
            form_p = None
            total_projection = None
            home_projection = None
            away_projection = None
            if hg and ag:
                form_p = logistic(((hpf - hpa) / hg - (apf - apa) / ag) / 14)
                home_projection = (hpf / hg + apa / ag) / 2
                away_projection = (apf / ag + hpa / hg) / 2
                total_projection = home_projection + away_projection
            baseline_total = mean(all_prior_scores) if all_prior_scores else None
            if week >= 4:
                if form_p is None or total_projection is None or baseline_total is None:
                    raise ValueError(f"Missing prior observations for game {game['id']}")
                outcome = None if game["home_score"] == game["away_score"] else int(game["home_score"] > game["away_score"])
                predictions.append({
                    **game,
                    "cutoff": f"end of week {week - 1}",
                    "home_prior_games": hg,
                    "away_prior_games": ag,
                    "outcome_home_win": outcome,
                    "elo_home_p": elo_p,
                    "form_home_p": form_p,
                    "elo_fair_home": fair_odds(elo_p),
                    "elo_fair_away": fair_odds(1 - elo_p),
                    "home_projected_points": home_projection,
                    "away_projected_points": away_projection,
                    "projected_total": total_projection,
                    # This is a mean margin, not a full predictive distribution.
                    "home_spread_projection": away_projection - home_projection,
                    "baseline_total": baseline_total,
                })
            week_predictions.append((game, elo_p))
        # Apply results only after every game in this week has been forecast.
        for game, p in week_predictions:
            h, a = game["home"], game["away"]
            hs, vs = game["home_score"], game["away_score"]
            actual = .5 if hs == vs else int(hs > vs)
            change = 20 * (actual - p)
            ratings[h] += change
            ratings[a] -= change
            for team, scored, conceded in ((h, hs, vs), (a, vs, hs)):
                form[team][0] += 1
                form[team][1] += scored
                form[team][2] += conceded
            all_prior_scores.append(hs + vs)
    return predictions


def calibration_diagnostics(probs, outcomes):
    """Five fixed bins. Project policy: every populated bin >=20 and gap <=.10.

    This coarse check is necessary but not sufficient for reliable calibration.
    """
    if not probs or len(probs) != len(outcomes):
        raise ValueError("probabilities and outcomes must have equal, nonzero length")
    bins = [[] for _ in range(5)]
    for p, y in zip(probs, outcomes):
        if not 0 <= p <= 1 or y not in (0, 1):
            raise ValueError("Invalid probability or binary outcome")
        bins[min(int(p * 5), 4)].append((p, y))
    result = []
    for i, members in enumerate(bins):
        if not members:
            continue
        forecast = mean([p for p, _ in members])
        observed = mean([y for _, y in members])
        result.append({"lower": i / 5, "upper": (i + 1) / 5, "n": len(members),
                       "mean_probability": forecast, "frequency": observed,
                       "absolute_gap": abs(forecast - observed)})
    return {"bins": result, "passes": all(b["n"] >= 20 and b["absolute_gap"] <= .10 for b in result)}


def evaluate_gates(evidence):
    """Fail closed when evidence needed by the research competition is missing.

    Thresholds are project policy, not claims of statistical sufficiency. The
    caller must substantiate every True flag and confidence bound independently.
    """
    def tri(value):
        return "pass" if value is True else "fail" if value is False else "unverified"
    enough = evidence["n"] >= 200 and evidence["seasons"] >= 3 and evidence["week_blocks"] >= 10
    delta = evidence.get("brier_improvement")
    lower = evidence.get("adjusted_ci_lower")
    if delta is None:
        skill = "unverified"
    elif delta <= 0:
        skill = "fail"
    elif lower is None or evidence.get("multiplicity_adjusted") is not True or evidence.get("week_blocked") is not True:
        skill = "unverified"
    else:
        skill = "pass" if lower > 0 else "fail"
    kind = evidence.get("market_type")
    if kind not in ("single", "parlay", "player_combo"):
        raise ValueError("Specify single, parlay, or player_combo for gate evaluation")
    gates = {
        "provenance": tri(evidence.get("source_and_quality_verified")),
        "chronology": tri(evidence.get("chronology_verified")),
        "sample": "pass" if enough else "fail",
        "calibration": tri(evidence.get("calibration_pass")),
        "skill": skill,
        "market_and_settlement": tri(evidence.get("market_and_settlement_verified")),
        "forward_test": tri(evidence.get("locked_forward_test_pass")),
    }
    if kind in ("parlay", "player_combo"):
        gates["joint_and_leg_terms"] = tri(evidence.get("joint_and_leg_terms_verified"))
    return gates


def reward_eligible(candidates):
    """Award proposed, non-cash credits only after every gate passes.

    Candidates must share the same event set and benchmark before being passed
    to this function. Ties at identical full-precision Brier get the same rank.
    """
    for candidate in candidates:
        # Re-evaluation must never preserve a stale award after evidence changes.
        candidate["eligible"] = False
        candidate["competition_rank"] = None
        candidate["reward_credits"] = None
    base = {"provenance", "chronology", "sample", "calibration", "skill", "market_and_settlement", "forward_test"}
    def has_passed_all(candidate):
        kind = candidate.get("market_type")
        if kind not in ("single", "parlay", "player_combo"):
            return False
        required = base | ({"joint_and_leg_terms"} if kind != "single" else set())
        return set(candidate.get("gates", {})) == required and all(v == "pass" for v in candidate["gates"].values())
    qualified = sorted((c for c in candidates if has_passed_all(c)), key=lambda c: c["brier"])
    credits = {1: 100, 2: 60, 3: 30}
    previous_score, rank = None, 0
    for index, row in enumerate(qualified, 1):
        if previous_score is None or row["brier"] != previous_score:
            rank = index
        row["eligible"] = True
        row["competition_rank"] = rank
        row["reward_credits"] = credits.get(rank, 0)
        previous_score = row["brier"]
    return qualified


def score_predictions(predictions, *, source_verified=None, chronology_verified=None):
    decisive = [p for p in predictions if p["outcome_home_win"] is not None]
    if not decisive:
        raise ValueError("No decisive games for binary evaluation")
    def metrics(field):
        probs = [.5 if field == "baseline" else p[field] for p in decisive]
        obs = [p["outcome_home_win"] for p in decisive]
        brier = mean([(pr - y) ** 2 for pr, y in zip(probs, obs)])
        logloss = -mean([y * math.log(pr) + (1 - y) * math.log1p(-pr) for pr, y in zip(probs, obs)])
        return {"n": len(obs), "brier": brier, "log_loss": logloss, "brier_skill_vs_50_50": 1 - brier / .25}
    baseline = metrics("baseline")
    candidates = []
    for ident, label, field in (
        ("elo", "Weekly Elo", "elo_home_p"),
        ("margin", "Prior margin", "form_home_p"),
    ):
        vals = metrics(field)
        calibration = calibration_diagnostics([p[field] for p in decisive], [p["outcome_home_win"] for p in decisive])
        gates = evaluate_gates({
            # This snapshot was compared field-by-field with the pinned NFL source
            # on 2026-11-02; chronology is covered by the tests for this revision.
            "source_and_quality_verified": source_verified,
            "chronology_verified": chronology_verified,
            "market_type": "single",
            "n": vals["n"],
            "seasons": len({p["season"] for p in decisive}),
            "week_blocks": len({(p["season"], p["week"]) for p in decisive}),
            "calibration_pass": calibration["passes"],
            "brier_improvement": baseline["brier"] - vals["brier"],
            "adjusted_ci_lower": None,
            "multiplicity_adjusted": None,
            "week_blocked": None,
            "market_and_settlement_verified": None,
            "locked_forward_test_pass": None,
        })
        candidates.append({
            "id": ident, "label": label, "market_type": "single", **vals,
            "calibration": calibration, "gates": gates,
            "eligible": False, "competition_rank": None, "reward_credits": None,
            "sources": [GAME_SOURCE, NOAA_SOURCE],
        })
    reward_eligible(candidates)
    candidates.sort(key=lambda r: r["brier"])
    for rank, row in enumerate(candidates, start=1):
        row["descriptive_rank"] = rank
    total_errors = [abs(p["projected_total"] - p["home_score"] - p["away_score"]) for p in predictions]
    baseline_errors = [abs(p["baseline_total"] - p["home_score"] - p["away_score"]) for p in predictions]
    return {
        "binary_baseline": baseline,
        "candidates": candidates,
        "total_projection": {"n": len(predictions), "mae": mean(total_errors), "baseline_mae": mean(baseline_errors)},
    }


def make_correlations(games, players):
    home_scores = [g["home_score"] for g in games]
    away_scores = [g["away_score"] for g in games]
    event_a = [int(g["home_score"] > g["away_score"]) for g in games]
    event_b = [int(g["home_score"] + g["away_score"] > 44.5) for g in games]
    rows = [{
        "id": "team_scores", "category": "Game scores", "label": "Designated home points / visitor points",
        "measure": "Pearson r", "n": len(games), "value": correlation(home_scores, away_scores),
        "sources": [GAME_SOURCE, NIST_SOURCE],
    }, {
        "id": "team_parlay", "category": "Same-game events", "label": "Home win / combined score over 44.5",
        "measure": "Binary phi", "value": correlation(event_a, event_b),
        "comparison": binary_comparison(event_a, event_b), "n": len(games), "sources": [GAME_SOURCE, NIST_SOURCE],
    }]
    for season, qb, receiver in ((2024, "Joe Burrow", "Ja'Marr Chase"), (2025, "Patrick Mahomes", "Travis Kelce")):
        paired = [p for p in players if p["season"] == season and p["qb"] == qb and p["receiver"] == receiver and p["paired"]]
        xs = [p["qb_passing_yards"] for p in paired]
        ys = [p["receiver_yards"] for p in paired]
        sources = [paired[0]["qb_source"], paired[0]["receiver_source"], NIST_SOURCE]
        rows.append({
            "id": f"player_yards_{season}", "category": "Player totals",
            "label": f"{qb} passing yards / {receiver} receiving yards ({season})",
            "measure": "Pearson r", "n": len(paired), "value": correlation(xs, ys), "sources": sources,
        })
        over_qb = [int(x > 249.5) for x in xs]
        over_rec = [int(y > 49.5) for y in ys]
        rows.append({
            "id": f"player_overs_{season}", "category": "Illustrative player events",
            "label": f"{qb} over 249.5 pass yds / {receiver} over 49.5 rec yds ({season})",
            "measure": "Binary phi", "n": len(paired), "value": correlation(over_qb, over_rec),
            "comparison": binary_comparison(over_qb, over_rec), "sources": sources,
        })
    return rows


def build_report(games=None, players=None):
    pinned_games = games is None
    games = parse_games() if pinned_games else games
    players = parse_players() if players is None else players
    predictions = walk_forward(games)
    # These flags apply only to the pinned file and tested implementation used
    # for this report, not arbitrary caller-supplied games.
    scores = score_predictions(predictions, source_verified=True if pinned_games else None,
                               chronology_verified=True if pinned_games else None)
    correlations = make_correlations(games, players)
    return {
        "metadata": {
            "as_of_utc": "2026-11-02", "game_source_revision": REVISION,
            "game_source_sha256": GAME_SHA256,
            "game_source": GAME_SOURCE, "schema_source": SCHEMA_SOURCE,
            "noaa_source": NOAA_SOURCE, "nist_source": NIST_SOURCE,
            "rules_source": RULES_SOURCE, "ftc_source": FTC_SOURCE,
            "status": "Historical research only; not live odds or a betting recommendation.",
        },
        "counts": {
            "game_results": len(games), "game_weeks": len({g['week'] for g in games}),
            "evaluated_games": len(predictions), "evaluated_seasons": len({p['season'] for p in predictions}),
            "evaluated_weeks": len({(p['season'], p['week']) for p in predictions}),
            "player_rows": len(players), "paired_player_rows": sum(p['paired'] for p in players),
            "unpaired_player_rows": sum(not p['paired'] for p in players),
            "qualified_strategies": sum(row['eligible'] for row in scores['candidates']),
        },
        "scores": scores,
        "correlations": correlations,
        "games": games,
        "players": players,
        "predictions": predictions,
    }


def main():
    report = build_report()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print(json.dumps({"counts": report["counts"], "scores": report["scores"], "correlations": report["correlations"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

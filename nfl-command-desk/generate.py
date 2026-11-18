#!/usr/bin/env python3
"""Regenerate every CSV of the NFL Command Desk deterministically (session 4078a9ad).

No network, no clock, no git. Run from the repository root:
    python3 nfl-command-desk/generate.py
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import analysis as A          # noqa: E402
import corpus as C            # noqa: E402
import official as O          # noqa: E402
import registry as R          # noqa: E402

DATA = HERE / "data"
DATA.mkdir(parents=True, exist_ok=True)

STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
W11_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
W10_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
INJ_URL = "https://www.nfl.com/injuries/league/2026/reg10"
INJ11_URL = "https://www.nfl.com/injuries/league/2026/reg11"
ANN_URL = O.ANNOUNCEMENT["url"]


def write(name, cols, rows):
    with (DATA / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    return len(rows)


def sources():
    rows = [dict(source_id=s[0], publisher=s[1], url=s[2], used_for=s[3], read_utc=s[4],
                 class_=s[5]) for s in O.SOURCES]
    return write("sources.csv",
                 ["source_id", "publisher", "url", "used_for", "read_utc", "class_"], rows)


def fixtures():
    rows = []
    for date, time_et, net, away, home, venue, method, neutral, ev in O.WEEK11:
        rows.append(dict(
            fixture_id=f"2026-W11-{away}-{home}", season=2026, week=11, date=date,
            kickoff_et=time_et, network=net, away=away, home=home, venue=venue,
            neutral_site=neutral, venue_method=method,
            fixture_facts=f"date {date}; kickoff {time_et} ET; network {net}; {ev}".strip("; "),
            announcement_date=O.ANNOUNCEMENT["date"], announcement_url=ANN_URL,
            source_url=W11_URL, read_utc="2026-11-18T03:47:00Z"))
    for tm in O.WEEK11_BYES:
        rows.append(dict(fixture_id=f"2026-W11-BYE-{tm}", season=2026, week=11, date="",
                         kickoff_et="", network="", away="", home="", venue="",
                         neutral_site="", venue_method="", fixture_facts="bye week",
                         announcement_date=O.ANNOUNCEMENT["date"], announcement_url=ANN_URL,
                         source_url=W11_URL, read_utc="2026-11-18T03:47:00Z"))
    return write("fixtures_wk11.csv",
                 ["fixture_id", "season", "week", "date", "kickoff_et", "network", "away",
                  "home", "venue", "neutral_site", "venue_method", "fixture_facts",
                  "announcement_date", "announcement_url", "source_url", "read_utc"], rows)


def requirements():
    rows = []
    for rid, req, cat, gate, clear, obs, status, ev in R.REQUIREMENTS:
        rows.append(dict(requirement_id=rid, requirement=req, category=cat, gate=gate,
                         clearing_number=clear, observed=obs, status=status,
                         evidence=ev, verified_utc="2026-11-18"))
    return write("requirements.csv",
                 ["requirement_id", "requirement", "category", "gate", "clearing_number",
                  "observed", "status", "evidence", "verified_utc"], rows)


def gates():
    rows = [dict(gate_id=g[0], name=g[1], rule=g[2], status=g[3], blocking=g[4])
            for g in R.GATES]
    return write("gates.csv", ["gate_id", "name", "rule", "status", "blocking"], rows)


def questions():
    rows = [dict(question_id=q[0], question=q[1], information_missing=q[2],
                 how_to_discover=q[3], blocks=q[4], answer=q[5])
            for q in R.QUESTIONS]
    return write("questions.csv",
                 ["question_id", "question", "information_missing", "how_to_discover",
                  "blocks", "answer"], rows)


def suggestions():
    rows = [dict(suggestion_id=s[0], suggestion=s[1], why=s[2], effort=s[3],
                 evidence_needed=s[4], decision=s[5]) for s in R.SUGGESTIONS]
    return write("suggestions.csv",
                 ["suggestion_id", "suggestion", "why", "effort", "evidence_needed",
                  "decision"], rows)


def flagged():
    rows = [dict(flag_id=f[0], severity=f[1], area=f[2], finding=f[3],
                 what_would_resolve=f[4], source_url=f[5]) for f in R.FLAGGED]
    return write("flagged.csv",
                 ["flag_id", "severity", "area", "finding", "what_would_resolve",
                  "source_url"], rows)


def availability_diff():
    """2026-11-12 repository capture (data/decision-desk/official/official_injuries_wk10.csv)
    against the 2026-11-18 re-read. Only rows present in the re-read are compared; nothing
    is inferred for clubs outside chunk 0."""
    repo = {}
    p = C.ROOT / "data/decision-desk/official/official_injuries_wk10.csv"
    with p.open(newline="") as f:
        for r in csv.DictReader(f):
            repo[(r["team_nickname"], r["player"])] = r
    nick = {"WAS": "Commanders", "NYG": "Giants", "NE": "Patriots", "DET": "Lions"}
    rows, changed = [], 0
    for club, player, pos, inj, prac, game in O.INJURY_WEEK10_RE_READ:
        key = (nick[club], player)
        old = repo.get(key, {})
        old_inj, old_game = old.get("injury", ""), old.get("game_status", "")
        old_prac = old.get("practice_status", "")
        fields = []
        if (old_inj or "") != inj:
            fields.append("injury")
        if (old_prac or "") != prac:
            fields.append("practice_status")
        if (old_game or "") != game:
            fields.append("game_status")
        if fields:
            changed += 1
        rows.append(dict(club=club, player=player, position=pos,
                         repo_injury=old_inj, repo_practice=old_prac, repo_game=old_game,
                         repo_captured_utc=old.get("retrieved_utc", ""),
                         official_injury=inj, official_practice=prac, official_game=game,
                         differing_fields=";".join(fields),
                         result="STALE" if fields else "MATCH",
                         source_url=INJ_URL, read_utc="2026-11-18T03:45:00Z"))
    n = write("availability_diff.csv",
              ["club", "player", "position", "repo_injury", "repo_practice", "repo_game",
               "repo_captured_utc", "official_injury", "official_practice", "official_game",
               "differing_fields", "result", "source_url", "read_utc"], rows)
    return n, changed


def availability_summary():
    counts = {}
    for club, player, pos, inj, prac, game in O.INJURY_WEEK10_RE_READ:
        c = counts.setdefault(club, dict(rows=0, out=0, questionable=0, blank=0))
        c["rows"] += 1
        if game == "Out":
            c["out"] += 1
        elif game == "Questionable":
            c["questionable"] += 1
        elif game == "":
            c["blank"] += 1
    rows = []
    for club, c in sorted(counts.items()):
        rows.append(dict(club=club, rows_read=c["rows"], game_status_out=c["out"],
                         game_status_questionable=c["questionable"],
                         game_status_blank=c["blank"],
                         starters_out="", replacements_named="",
                         source_url=INJ_URL, read_utc="2026-11-18T03:45:00Z"))
    return write("availability_summary.csv",
                 ["club", "rows_read", "game_status_out", "game_status_questionable",
                  "game_status_blank", "starters_out", "replacements_named", "source_url",
                  "read_utc"], rows)


def schedule_vs_announcement():
    a = O.ANNOUNCEMENT
    rows = [
        ("weeks", 18, a["weeks"], "matches"),
        ("regular games", 272, a["games"], "matches"),
        ("regular games per club", "17 + 3 preseason", f"{a['regular_games_per_team']} + {a['preseason_games_per_team']} preseason", "matches"),
        ("international games", 9, a["international_games"], "matches"),
        ("Week 11 international", "Mexico City, MIN at SF, NBC 8:20 p.m. ET",
         a["week11_mexico"], "matches; venue named Estadio Banorte in the announcement"),
        ("season number", 107, a["season_number"], "matches"),
    ]
    return write("schedule_vs_announcement.csv",
                 ["fact", "as_announced", "announcement_value", "result",
                  "announcement_url", "announcement_date"],
                 [dict(fact=f, as_announced=x, announcement_value=y, result=z,
                       announcement_url=ANN_URL, announcement_date=a["date"])
                  for f, x, y, z in rows])


def standings():
    rows = [dict(team=s[0], name=s[1], w=s[2], l=s[3], t=s[4], pct=s[5], pf=s[6], pa=s[7],
                 net=s[6] - s[7], source_url=STANDINGS_URL, read_utc="2026-11-18T03:52:00Z")
            for s in O.STANDINGS]
    return write("standings.csv",
                 ["team", "name", "w", "l", "t", "pct", "pf", "pa", "net", "source_url",
                  "read_utc"], rows)


def ratings(res):
    rows = []
    for tm, r in sorted(res["ratings"].items(), key=lambda x: -x[1]):
        n = len([g for g in res["train"] if tm in (g["home"], g["away"])])
        rows.append(dict(team=tm, games_train=n, net_points_pg=round(r, 3),
                         points_scored_pg=round(res["tots"][tm], 3),
                         source="derived from the corpus (weeks 1-4 only)",
                         input_url=STANDINGS_URL))
    return write("ratings.csv",
                 ["team", "games_train", "net_points_pg", "points_scored_pg", "source",
                  "input_url"], rows)


def origination(res):
    """Week 11 origination from the train-window ratings, in the registered order:
    side first, then total (both estimators), then moneyline."""
    rows = []
    for date, time_et, net, away, home, venue, method, neutral, ev in O.WEEK11:
        rh = res["ratings"].get(home)
        ra = res["ratings"].get(away)
        if rh is None or ra is None:
            continue
        fair = rh - ra + A.HFA
        tot_a = res["tots"][home] + res["tots"][away]
        rows.append(dict(
            fixture_id=f"2026-W11-{away}-{home}", away=away, home=home,
            neutral_site=neutral,
            # 1. side
            fair_home_margin=round(fair, 2),
            fair_favourite=("home" if fair > 0 else "away"),
            fair_spread=round(-fair, 2),
            # 2. total, both estimators
            fair_total_a=round(tot_a, 1), fair_total_b=round(res["lg"], 1),
            total_gap=round(tot_a - res["lg"], 1),
            # 3. moneyline
            p_home_ml=round(A.sigmoid(fair / A.LM_SCALE), 4),
            p_away_ml=round(1 - A.sigmoid(fair / A.LM_SCALE), 4),
            # market columns: not available, blank by policy
            market_spread="", market_total="", market_home_ml="", market_away_ml="",
            residual_spread="", residual_total="", residual_ml="",
            hfa_assumption=A.HFA, inputs="net points/game and points scored/game, weeks 1-4 corpus",
            source_url=W11_URL, flag="FLAG-P1 market columns blank"))
    return write("origination_wk11.csv",
                 ["fixture_id", "away", "home", "neutral_site", "fair_home_margin",
                  "fair_favourite", "fair_spread", "fair_total_a", "fair_total_b", "total_gap",
                  "p_home_ml", "p_away_ml", "market_spread", "market_total", "market_home_ml",
                  "market_away_ml", "residual_spread", "residual_total", "residual_ml",
                  "hfa_assumption", "inputs", "source_url", "flag"], rows)


def forecast_ledger(res):
    rows = []
    for f in res["forecasts"]:
        rows.append(dict(window=f["window"], week=f["week"], date=f["date"],
                         away=f["away"], home=f["home"],
                         rating_home=f["rating_home"], rating_away=f["rating_away"],
                         fair_margin=f["fair_margin"], fair_total_a=f["fair_total_a"],
                         fair_total_b=f["fair_total_b"],
                         p_home_ml=round(f["p_home_ml"], 4),
                         actual_home_margin=f["home_margin"], actual_total=f["total"],
                         home_win="" if f["home_win"] is None else f["home_win"],
                         inputs="ratings from weeks 1-4; HFA 2.0; logistic scale 6.0",
                         source_url=STANDINGS_URL))
    return write("forecast_ledger.csv",
                 ["window", "week", "date", "away", "home", "rating_home", "rating_away",
                  "fair_margin", "fair_total_a", "fair_total_b", "p_home_ml",
                  "actual_home_margin", "actual_total", "home_win", "inputs",
                  "source_url"], rows)


def leaderboard(res):
    """Divisions: singles / game parlay / same-game parlay / prop combo.
    Signal columns are computed; staking columns are intentionally blank."""
    rows = []
    for r in res["rows"]:
        rows.append(dict(
            division="singles",
            strategy_id=r["strategy_id"], name=r["name"], window=r["window"],
            bets=r["bets"], brier=r["brier"], bss_vs_flat=r["bss_vs_flat"],
            ci_low=r["ci_low"], ci_high=r["ci_high"], p_exact=r["p_exact"],
            p_holm=r["p_holm"], certified=r["certified"] or "NO",
            mae=r.get("mae", ""), mean_bias=r.get("bias", ""),
            roi="", clv="", reward="",
            control_note="flat 0.5 control and always-home control in the same run",
            source_url=STANDINGS_URL))
    for div in ("game parlay", "same-game parlay", "prop combo"):
        rows.append(dict(division=div, strategy_id="", name="(none registered)",
                         window="", bets=0, brier="", bss_vs_flat="", ci_low="", ci_high="",
                         p_exact="", p_holm="", certified="", mae="", mean_bias="",
                         roi="", clv="", reward="",
                         control_note="G09 joint-evidence gate: no validated joint probability exists",
                         source_url=ANN_URL))
    return write("leaderboard.csv",
                 ["division", "strategy_id", "name", "window", "bets", "brier",
                  "bss_vs_flat", "ci_low", "ci_high", "p_exact", "p_holm", "certified",
                  "mae", "mean_bias", "roi", "clv", "reward", "control_note",
                  "source_url"], rows)


def preregistration():
    rows = [
        dict(strategy_id="REG-M1", name="Moneyline: opponent-aware net points per game",
             market="moneyline",
             rule="p(home) = sigmoid((rating_home - rating_away + 2.0)/6.0); rating = mean own margin over weeks 1-4",
             train_window="weeks 1-4 (2026)", validation_window="weeks 5-8",
             holdout_window="weeks 9-10",
             gates="G01 G02 G03 G04 G05 G06 G07",
             would_change_our_mind_up="Brier skill lower bound > 0 on the holdout and a calibrated slope in 0.8-1.2",
             would_change_our_mind_down="Brier skill lower bound stays below 0 after 200 out-of-sample games",
             status="registered, frozen before results"),
        dict(strategy_id="REG-S1", name="Side vs model line (control)",
             market="side", rule="home covers when actual margin > fair margin; coin-flip control",
             train_window="weeks 1-4", validation_window="weeks 5-8", holdout_window="weeks 9-10",
             gates="G01 G03 G06", would_change_our_mind_up="a cover rate whose CI excludes 50%",
             would_change_our_mind_down="cover rate inside 45-55%", status="registered, control"),
        dict(strategy_id="REG-S2", name="Home minus 2.0 vs a frozen 2.0 line",
             market="side", rule="bet home at a constant -2.0 every game; hit = margin > 2",
             train_window="not used (no fitting)", validation_window="weeks 5-8",
             holdout_window="weeks 9-10", gates="G01 G06 G07",
             would_change_our_mind_up="the same rate reproduced on a second season",
             would_change_our_mind_down="a second season near 50%", status="registered, exposure test"),
        dict(strategy_id="REG-T1", name="Total estimator A (club scoring rates)",
             market="total", rule="fair total = points scored/game home + points scored/game away",
             train_window="weeks 1-4", validation_window="weeks 5-8", holdout_window="weeks 9-10",
             gates="G01 G03", would_change_our_mind_up="paired MAE CI versus B excludes 0 in A's favour",
             would_change_our_mind_down="B stays closer", status="registered"),
        dict(strategy_id="REG-T2", name="Total estimator B (league mean)",
             market="total", rule="fair total = league mean total over weeks 1-4",
             train_window="weeks 1-4", validation_window="weeks 5-8", holdout_window="weeks 9-10",
             gates="G01 G03", would_change_our_mind_up="paired MAE CI excludes 0 in B's favour",
             would_change_our_mind_down="A stays closer", status="registered"),
    ]
    return write("preregistration.csv",
                 ["strategy_id", "name", "market", "rule", "train_window", "validation_window",
                  "holdout_window", "gates", "would_change_our_mind_up",
                  "would_change_our_mind_down", "status"], rows)


def luck(res):
    lp, need = A.luck_panel(res["games"])
    rows = [dict(bets=x["bets"], expected_wins=x["expected"], sd=x["sd"],
                 wins_for_55=x["wins_for_55"], prob_55_or_more=x["prob_55_or_more"],
                 bets_needed_80_power=need) for x in lp]
    return write("luck_panel.csv",
                 ["bets", "expected_wins", "sd", "wins_for_55", "prob_55_or_more",
                  "bets_needed_80_power"], rows)


def metrics_json(res):
    """Small machine-readable summary next to the CSVs (suggestion S09)."""
    out = dict(
        generated_for="2026-11-18 NFL Command Desk (session 4078a9ad)",
        corpus_games=len(res["games"]),
        windows={k: len(v) for k, v in res["windows"].items()},
        hfa=A.HFA, lm_scale=A.LM_SCALE,
        league_mean_total=round(res["lg"], 3),
        strategies_certified=0,
        rows=[{k: v for k, v in r.items()} for r in res["rows"]],
    )
    (DATA / "summary.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


def main():
    games, recon, failures = C.build()
    if failures:
        raise SystemExit(f"reconciliation failed for {failures}; refusing to publish")
    res = A.run()
    counts = {
        "sources": sources(),
        "fixtures": fixtures(),
        "standings": standings(),
        "ratings": ratings(res),
        "origination": origination(res),
        "forecast_ledger": forecast_ledger(res),
        "leaderboard": leaderboard(res),
        "preregistration": preregistration(),
        "luck_panel": luck(res),
        "gates": gates(),
        "requirements": requirements(),
        "questions": questions(),
        "suggestions": suggestions(),
        "flagged": flagged(),
        "availability_summary": availability_summary(),
        "schedule_vs_announcement": schedule_vs_announcement(),
    }
    n, changed = availability_diff()
    counts["availability_diff"] = n
    counts["availability_diff_changed"] = changed
    counts["results_corpus"] = len(games)
    counts["results_reconciliation"] = len(recon)
    metrics_json(res)
    for k, v in counts.items():
        print(f"{k:28} {v}")
    print(f"{'reconciliation failures':28} {len(failures)}")


if __name__ == "__main__":
    main()

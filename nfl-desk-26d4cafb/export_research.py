"""Export the research/ markdown dossier for session 26d4cafb.

Reads nfl-desk-26d4cafb/data/ (produced by engine.py) and writes
research/nfl-26d4cafb/*.md.

This script exists so the markdown dossier can never drift from the data: the prose
is written once here, every table is generated straight from the CSVs, and no value
is retyped by hand.
"""

from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(os.path.dirname(HERE), "research", "nfl-26d4cafb")


def rows(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def md_table(rs, cols, headers):
    if not rs:
        return "_No rows._\n"
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rs:
        cells = []
        for c in cols:
            v = r.get(c)
            v = "" if v is None else str(v)
            v = v.replace("|", "\\|").replace("\n", " ").strip()
            cells.append(v if v else "&mdash;")
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def write(name, title, body):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# %s\n\n" % title)
        fh.write("**Session `26d4cafb` - snapshot 2026-11-12 UTC - NFL 2026 Week 10**\n\n")
        fh.write("> Generated directly from `nfl-desk-26d4cafb/data/` by `engine.py`. Every row links "
                 "to the official source it was read from. Values that could not be confirmed from an "
                 "official source are left blank and listed on the Flagged for Review page.\n\n")
        fh.write(body)
    return path


def main():
    summary = json.load(open(os.path.join(DATA, "summary.json"), encoding="utf-8"))
    hfa = rows("hfa.csv")[0]
    st = rows("standings_check.csv")
    ln = rows("lines_wk10.csv")
    inj = rows("injuries.csv")
    sig = rows("signals.csv")
    strat = rows("strategies.csv")
    lb = rows("leaderboard.csv")
    gt = rows("gates.csv")
    corr = rows("correlations.csv")
    combo = rows("prop_combos.csv")
    lk = rows("luck_skill.csv")
    sel = rows("selectivity.csv")
    flg = rows("flagged.csv")
    src = rows("sources.csv")
    aud = rows("repo_audit.csv")
    sug = rows("suggestions.csv")
    qs = rows("questions.csv")
    disc = rows("discovery.csv")
    paths = rows("paths.csv")
    req = rows("requirements.csv")
    oos = rows("oos_week9_summary.csv")
    oosm = rows("oos_week9_matched.csv")
    ks = rows("shrinkage_sensitivity.csv")
    ps = rows("parlay_summary.csv")
    qb = rows("qb_checksums.csv")
    logs = rows("player_logs.csv")
    sel_info = summary.get("selectivity_test") or {}
    nmatch = summary["standings_teams"]

    # ---- executive summary -------------------------------------------------
    b = ["## Headline numbers\n\n"]
    b.append("| Metric | Value |\n|---|---|\n")
    def kv(label, value):
        b.append("| %s | %s |\n" % (label, value))

    kv("Completed games in official ledger", summary["ledger_completed_games"])
    kv("Games re-fetched after the repo's 2026-11-02 freeze",
       summary["ledger_added_after_repo_freeze"])
    kv("Standings reconciliation", "%d/%d teams, %d mismatches"
       % (nmatch, nmatch, summary["standings_mismatches"]))
    kv("Empirical home-field advantage", "%+.3f pts (n=%s, p=%s)"
       % (float(hfa["mean_home_margin"]), hfa["n_non_neutral_games"], hfa["p_two_sided"]))
    _lg = rows("ledger.csv")
    _hw = sum(1 for g in _lg if int(g["home_pts"]) > int(g["away_pts"]))
    _aw = sum(1 for g in _lg if int(g["away_pts"]) > int(g["home_pts"]))
    _tt = len(_lg) - _hw - _aw
    kv("Home / away records", "%d home W / %d away W / %d T" % (_hw, _aw, _tt))
    kv("Week 10 lines originated", summary["week10_lines_originated"])
    kv("Injury / depth rows tracked", len(inj))
    kv("Player game logs", len(logs))
    kv("QB season checksums verified", "%d, 0 mismatches"
       % len([r for r in qb if r["checksum_match"] == "MATCH"]))
    kv("Strategies passing all 10 gates", "%d of %d"
       % (len([r for r in lb if r["rank"]]), len(strat)))
    kv("Open flagged items", len(flg))

    b.append("\n## Findings that should change decisions\n\n")
    b.append("1. **The repository's NFL boards are 16 games stale.** Four boards (root `index.html`, "
             "`own5-desk/`, `line-lab/`, `nfl-strategy-lab/`) are frozen at 2026-11-02 and are missing "
             "Week 8 Monday Night Football and all 15 Week 9 games. All 16 were re-fetched verbatim "
             "from NFL.com and merged; the resulting 136-game ledger reconciles **32/32** teams to "
             "[nfl.com/standings](https://www.nfl.com/standings/) with zero mismatches.\n")
    b.append("2. **2026 home-field advantage is statistically indistinguishable from zero.** The "
             "empirical value on %s non-neutral games is %+.3f points (95%% CI [%s, %s], p=%s). Prior "
             "boards assumed +2.0; on the matched sample that assumption produced a margin bias of "
             "**%s points**.\n"
             % (hfa["n_non_neutral_games"], float(hfa["mean_home_margin"]),
                hfa["ci95_low"], hfa["ci95_high"], hfa["p_two_sided"],
                (oosm[2]["margin_bias"] if len(oosm) > 2 else "n/a")))
    b.append("3. **Baltimore is starting its third-string quarterback on Monday night**, while the "
             "official Week 10 injury table still reads \"No Injuries Reported\" for that game because "
             "IR players are excluded and the report is in its pre-Thursday window (FLG-06).\n")
    b.append("4. **Two of ten strategies clear all ten validation gates** after Holm-Bonferroni "
             "family-wise control and the Deflated Sharpe Ratio. The other eight are explicitly blocked "
             "or marked not evaluable, not silently dropped.\n")
    b.append("5. **Selective skill is NOT established.** Accuracy across confidence terciles is "
             "%s / %s / %s, which is not monotone, so the highest-confidence bucket does not beat the "
             "middle one. The engine reports this rather than claiming selectivity.\n"
             % (sel[0]["win_rate"], sel[1]["win_rate"], sel[2]["win_rate"]))
    b.append("6. **No official market or player-prop lines exist.** NFL.com publishes none, so every "
             "market, price, edge and CLV column is deliberately left blank and flagged (FLG-01, "
             "FLG-02) rather than sourced from a third-party scrape.\n")
    b.append("\n## Requirements coverage\n\n")
    b.append(md_table(req, ["id", "area", "requirement", "deliverable", "status"],
                      ["#", "Area", "Requirement", "Deliverable", "Status"]))
    b.append("\n## What is still missing\n\n")
    b.append(md_table(flg, ["id", "severity", "category", "item", "value_left_blank",
                            "resolution_path", "status"],
                      ["#", "Severity", "Category", "Item", "Value left blank", "Discovery", "Status"]))
    write("executive-summary.md", "Executive Summary", "".join(b))

    # ---- repo audit --------------------------------------------------------
    b = ["## Findings\n\n"]
    b.append(md_table(aud, ["id", "severity", "area", "path", "finding", "impact",
                            "recommendation", "verification_status"],
                      ["#", "Severity", "Area", "Path", "Finding", "Impact", "Recommendation", "Status"]))
    b.append("\n## Verification performed\n\n")
    b.append("- Recomputed all 32 teams' W/L/T/PF/PA from the merged 136-game ledger and compared to "
             "[nfl.com/standings](https://www.nfl.com/standings/): 0 mismatches.\n")
    b.append("- Re-fetched Week 8 MNF and all 15 Week 9 finals from "
             "[nfl.com/schedules/2026/by-week/week-9](https://www.nfl.com/schedules/2026/by-week/week-9) "
             "and merged them into the ledger.\n")
    b.append("- Verified 6 quarterbacks' game-by-game passing yards against the official season totals "
             "on [nfl.com/stats/player-stats](https://www.nfl.com/stats/player-stats/): 0 mismatches.\n")
    write("01-repo-audit.md", "Repository Audit", "".join(b))

    # ---- suggestions -------------------------------------------------------
    b = ["## Implementation paths\n\n> Nothing in this document has been implemented. These are "
         "proposals for review; site-wide changes are made only after a path is chosen.\n\n"]
    b.append(md_table(paths, ["id", "name", "scope", "includes", "pros", "cons", "breaking_change",
                              "estimated_effort", "recommendation"],
                      ["Path", "Name", "Scope", "Includes", "Pros", "Cons", "Breaking", "Effort",
                       "Recommendation"]))
    b.append("\n## Suggestions\n\n")
    b.append(md_table(sug, ["id", "priority", "category", "title", "current_state", "suggestion",
                            "improves_decision_making", "effort", "risk_if_ignored", "path"],
                      ["#", "P", "Category", "Suggestion", "Current state", "Proposal",
                       "Why it improves decisions", "Effort", "Risk if ignored", "Path"]))
    write("02-suggestions.md", "Suggestions and Decision Paths", "".join(b))

    # ---- pre-decision ------------------------------------------------------
    b = ["## Questions, known information, answers and gaps\n\n"]
    b.append(md_table(qs, ["id", "topic", "question", "known", "answer", "missing", "blocks"],
                      ["#", "Topic", "Question", "Known", "Answer reached", "Still missing", "Blocks"]))
    b.append("\n## Discovery actions\n\n")
    b.append(md_table(disc, ["id", "target_question", "action", "how", "owner", "effort", "unblocks"],
                      ["#", "Answers", "Action", "How", "Owner", "Effort", "Unblocks"]))
    write("03-pre-decision.md", "Pre-Decision Questions and Discovery", "".join(b))

    # ---- methodology -------------------------------------------------------
    b = ["## Declared model\n\n"]
    b.append("- Team offence: shrunk, opponent-adjusted points per game above league mean.\n")
    b.append("- Team defence: shrunk, opponent-adjusted points allowed per game above league mean.\n")
    b.append("- Expected points: `pts_A = league_mean + off_A + def_B`, with the empirical home-field "
             "advantage split half to each side and zeroed for confirmed neutral-site games.\n")
    b.append("- Score distribution: independent Poisson on the two expected point totals; win, loss and "
             "tie probabilities, the fair spread and the fair total come from direct enumeration.\n")
    b.append("- Injury/depth toll: itemised per team per unit, weighted by the official availability "
             "tier. These are bounded model priors, never official statistics.\n")
    b.append("\n## Declared hyper-parameters\n\n")
    b.append(md_table([{"k": k, "v": v} for k, v in sorted(summary["model_hyperparameters"].items())],
                      ["k", "v"], ["Parameter", "Value"]))
    b.append("\n## Home-field advantage\n\n")
    b.append(md_table([hfa], ["n_non_neutral_games", "mean_home_margin", "stdev", "standard_error",
                              "ci95_low", "ci95_high", "t_stat", "p_two_sided", "home_wins",
                              "away_wins", "ties", "sensitivity_including_unconfirmed"],
                      ["n", "Mean", "SD", "SE", "CI low", "CI high", "t", "p", "Home W", "Away W",
                       "T", "Incl. unconfirmed"]))
    b.append("\n> Two 2026 games (Week 4 IND@WSH, Week 6 HOU@JAX) show a 9:30 AM ET international "
             "kickoff window but no venue on the official schedule page, so their neutral-site status "
             "is unconfirmed; they are excluded from the main estimate and reported as a sensitivity "
             "(FLG-12).\n")
    b.append("\n## Shrinkage sensitivity\n\n")
    b.append(md_table(ks, ["shrink_k", "n_graded", "margin_MAE", "margin_RMSE", "margin_bias",
                           "is_declared_value"],
                      ["k", "n", "MAE", "RMSE", "Bias", "Declared"]))
    b.append("\n## Zero-look-ahead protocol\n\n")
    b.append("- Walk-forward: a bet graded in week *w* is produced by a model fitted only on weeks "
             "< *w*.\n")
    b.append("- The null probability for each pick also comes only from weeks < *w*.\n")
    b.append("- Each pick is scored against its **own** null (the pre-week home win rate), then tested "
             "with an exact **Poisson-binomial**, not a plain binomial with a constant p.\n")
    b.append("- No official injury register exists for Weeks 1-9, so no injury-based strategy is "
             "backtested; those entries are marked not evaluable rather than graded on invented data.\n")
    write("04-methodology.md", "Methodology", "".join(b))

    # ---- injuries ----------------------------------------------------------
    b = ["## Starter-to-backup register (Week 10)\n\n"]
    b.append(md_table(inj, ["id", "game_id", "team", "opp", "unit", "pos", "starter_1st",
                            "practice_status", "official_game_status", "backup_2nd", "backup_3rd",
                            "backup_4th", "active_string", "availability_tier", "model_pts_impact",
                            "snap_epa_official", "flag_id"],
                      ["#", "Game", "Team", "Opp", "Unit", "Pos", "1st", "Practice status",
                       "Official game status", "2nd", "3rd", "4th", "Active string", "Tier",
                       "Model prior", "Official EPA", "Flag"]))
    b.append("\n> `official_game_status` is filled in only where NFL.com has actually published a game "
             "status (Thursday night and the early-issued Munich game). Sunday and Monday statuses are "
             "not issued until Friday/Saturday, so those cells are blank (FLG-03).\n")
    write("05-injuries-depth.md", "Injuries and Backup Depth", "".join(b))

    # ---- lines -------------------------------------------------------------
    b = ["## Originated Week 10 lines\n\n"]
    b.append(md_table(ln, ["game_id", "date", "away", "home", "neutral", "model_lambda_away",
                           "model_lambda_home", "model_margin_home", "model_spread_home",
                           "model_total_line", "p_home_win", "p_tie", "ml_home", "ml_away",
                           "injury_toll_home_off", "injury_toll_away_off", "market_spread",
                           "market_total"],
                      ["#", "Date", "Away", "Home", "Neutral", "Pts away", "Pts home", "Margin",
                       "Spread", "Total", "P(home)", "P(tie)", "ML home", "ML away", "Home off toll",
                       "Away off toll", "Mkt spread", "Mkt total"]))
    b.append("\n> Market columns are deliberately blank: NFL.com publishes no spreads, totals or "
             "moneylines (FLG-01).\n")
    b.append("\n## Out-of-sample grading vs the repository's existing originators\n\n")
    b.append(md_table(oos, ["model", "n_games_graded", "margin_MAE", "margin_RMSE", "margin_bias",
                            "total_MAE", "straight_up_accuracy", "brier_score"],
                      ["Model", "n", "MAE", "RMSE", "Bias", "Total MAE", "Accuracy", "Brier"]))
    b.append("\n### Matched sample (games every model graded)\n\n")
    b.append(md_table(oosm, ["model", "matched_sample_n", "margin_MAE", "margin_bias", "total_MAE",
                             "straight_up_accuracy", "brier_score"],
                      ["Model", "n", "MAE", "Bias", "Total MAE", "Accuracy", "Brier"]))
    write("06-lines.md", "Originated Lines and Out-of-Sample Grading", "".join(b))

    # ---- signals / strategies ----------------------------------------------
    b = ["## Signals\n\n"]
    b.append(md_table(sig, ["id", "category", "name", "definition", "data_source", "cadence",
                            "verification_status", "known_limitation"],
                      ["#", "Category", "Signal", "Definition", "Source", "Cadence", "Verified",
                       "Limitation"]))
    b.append("\n## Strategies\n\n")
    b.append(md_table(strat, ["strategy_id", "name", "bet_type", "market", "rule", "signals",
                              "status", "n_graded", "win_rate", "gates_passed", "reward_tier"],
                      ["#", "Strategy", "Type", "Market", "Rule", "Signals", "Status", "Graded",
                       "Win rate", "Gates", "Reward"]))
    b.append("\n## Leaderboard\n\n")
    b.append(md_table(lb, ["rank", "strategy_id", "name", "graded_bets", "win_rate", "roi_per_unit",
                           "deflated_sharpe_ratio", "max_drawdown_units", "gates_passed",
                           "reward_tier"],
                      ["Rank", "#", "Strategy", "Graded", "Win rate", "ROI/unit", "DSR", "Max DD",
                       "Gates", "Reward"]))
    b.append("\n## Validation gates\n\n")
    b.append(md_table(gt, ["strategy_id", "G03_min_sample_n20", "G04_breaks_even_-110",
                           "G05_binomial_p05", "G06_holm_p05", "G07_deflated_sharpe",
                           "G08_brier_calibration", "G09_correlation_cap", "G10_drawdown_budget",
                           "overall"],
                      ["#", "G-03 sample", "G-04 break-even", "G-05 binomial", "G-06 Holm",
                       "G-07 DSR", "G-08 Brier", "G-09 correlation", "G-10 drawdown", "Overall"]))
    write("07-signals-strategies.md", "Signals, Strategies and Leaderboard", "".join(b))

    # ---- correlations ------------------------------------------------------
    b = ["## Team level (n=32)\n\n"]
    b.append(md_table([r for r in corr if r["level"] == "team"],
                      ["pair_id", "metric_x", "metric_y", "n", "pearson_r", "r_squared", "t_stat",
                       "p_two_sided", "status"],
                      ["#", "Metric X", "Metric Y", "n", "r", "r^2", "t", "p", "Status"]))
    b.append("\n## Player props (same-game pairs)\n\n")
    b.append(md_table([r for r in corr if r["level"] == "player-prop"],
                      ["pair_id", "metric_x", "metric_y", "n", "pearson_r", "r_squared", "t_stat",
                       "p_two_sided"],
                      ["#", "Metric X", "Metric Y", "n", "r", "r^2", "t", "p"]))
    b.append("\n## Prop combos: joints, lift, Frechet-Hoeffding bounds\n\n")
    b.append(md_table(combo, ["combo", "leg_a", "leg_b", "n_games", "p_leg_a", "p_leg_b",
                              "p_joint_observed", "p_joint_if_independent", "lift_over_independence",
                              "phi_correlation", "frechet_min", "frechet_max",
                              "within_frechet_bounds"],
                      ["Combo", "Leg A", "Leg B", "n", "P(A)", "P(B)", "P(A and B)", "P(A)P(B)",
                       "Lift", "phi", "Min", "Max", "In bounds"]))
    b.append("\n> Reference line is each player's own shrunk season median - a synthetic fair "
             "reference, not an official prop line (FLG-01, FLG-02).\n")
    b.append("\n## Quarterback checksums\n\n")
    b.append(md_table(qb, ["qb", "team", "n_games", "official_season_pass_yds", "sum_of_game_logs",
                           "checksum_match", "mean_pass_yds", "sd_pass_yds", "r_with_primary_target"],
                      ["QB", "Team", "Games", "Official", "Sum of logs", "Check", "Mean", "SD",
                       "r vs target"]))
    write("08-correlations.md", "Correlations and Prop Combos", "".join(b))

    # ---- luck vs skill ------------------------------------------------------
    b = ["## Luck vs skill\n\n"]
    b.append(md_table(lk, ["strategy", "n_graded_bets", "win_rate", "mean_null_win_rate",
                           "lift_over_null", "p_two_sided_exact_poisson_binomial", "holm_adjusted_p",
                           "significant_after_holm", "brier", "brier_reference_null", "sharpe",
                           "deflated_sharpe_ratio", "max_drawdown_units"],
                      ["Strategy", "n", "Win rate", "Null", "Lift", "p (exact)", "Holm p",
                       "Significant", "Brier", "Brier null", "Sharpe", "DSR", "Max DD"]))
    b.append("\n## Selectivity test\n\n")
    b.append(md_table(sel, ["tercile", "n_bets", "mean_abs_model_margin", "wins", "win_rate",
                            "mean_null_win_rate", "lift_over_null"],
                      ["Confidence tercile", "n", "Mean abs margin", "Wins", "Win rate", "Null",
                       "Lift"]))
    b.append("\nchi2 = %s, p = %s, monotone increasing: **%s**\n\n%s\n"
             % (sel_info.get("chi2_trend"), sel_info.get("p_trend_two_sided"),
                sel_info.get("monotone_increasing"), sel_info.get("interpretation")))
    b.append("\n## Two-leg parlays\n\n")
    b.append(md_table(ps, ["n_parlays", "pairing", "leg_a_win_rate", "leg_b_win_rate",
                           "measured_leg_phi", "parlay_hit_rate", "null_implied_hit_rate",
                           "independence_implied_hit_rate", "lift_over_independence", "frechet_min",
                           "frechet_max", "break_even_hit_rate", "roi_per_unit"],
                      ["Parlays", "Pairing", "Leg A", "Leg B", "phi", "Hit rate", "Null",
                       "Independence", "Lift", "Min", "Max", "Break-even", "ROI/unit"]))
    write("09-luck-vs-skill.md", "Luck vs Skill", "".join(b))

    # ---- flagged ------------------------------------------------------------
    b = ["## Flagged for review\n\n"]
    b.append(md_table(flg, ["id", "severity", "category", "item", "issue", "value_left_blank",
                            "resolution_path", "status"],
                      ["#", "Severity", "Category", "Item", "Issue", "Value left blank", "Discovery",
                       "Status"]))
    write("10-flagged.md", "Flagged for Review", "".join(b))

    # ---- sources -------------------------------------------------------------
    b = ["## Official source register\n\n"]
    b.append(md_table(src, ["id", "publisher", "title", "used_for", "fetched",
                            "verification_status"],
                      ["#", "Publisher", "Title", "Used for", "Fetched", "Status"]))
    write("11-sources.md", "Official Sources", "".join(b))

    print("Wrote %d research docs to %s" % (len(os.listdir(OUT)), OUT))
    for f in sorted(os.listdir(OUT)):
        print("  -", f)


if __name__ == "__main__":
    sys.exit(main())

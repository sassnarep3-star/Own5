#!/usr/bin/env python3
"""Build the additive static dashboard exclusively from reviewed CSV inputs."""
from __future__ import annotations

import html
import json
from pathlib import Path

from model import AS_OF, ROOT, load_data, write_derived

NAV = [
    ("index.html", "Overview"), ("lines.html", "Own lines"), ("players.html", "Players & props"),
    ("teams.html", "Team data"), ("strategies.html", "Strategies"), ("correlations.html", "Correlations"),
    ("gates.html", "Validation gates"), ("leaderboard.html", "Leaderboard"), ("methodology.html", "Methodology"),
    ("sources.html", "Sources"), ("review.html", "Flagged for Review"),
]


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def num(value: float | None, digits: int = 1) -> str:
    return "" if value is None else f"{value:.{digits}f}"


def spread(value: float | None) -> str:
    return "" if value is None else f"{value:+.1f}"


def american(value: int | None) -> str:
    return "" if value is None else f"{value:+d}"


def percent(value: float | None) -> str:
    return "" if value is None else f"{100 * value:.1f}%"


def link(label: str, url: str) -> str:
    return f'<a href="{esc(url)}" rel="noopener">{esc(label)}</a>'


def source_links(data: dict, *source_ids: str, extra: list[tuple[str, str]] | None = None) -> str:
    items = list(extra or [])
    for source_id in source_ids:
        source = data["source_map"][source_id]
        items.append((source_id, source["url"]))
    return " ".join(link(label, url) for label, url in items)


def table(headers: list[str], rows: list[list[object]], sources: list[str], caption: str, wide: bool = False) -> str:
    assert len(rows) == len(sources)
    output = ['<div class="tablewrap"><table>', f"<caption>{esc(caption)}</caption>", "<thead><tr>"]
    for index, header in enumerate(headers):
        css = ' class="wrapcell"' if wide and index in {1, 2, 3} else ""
        output.append(f"<th{css}>{esc(header)}</th>")
    output.append("</tr></thead><tbody>")
    for row, source_html in zip(rows, sources):
        assert len(row) == len(headers) - 1
        output.append("<tr>")
        for index, cell in enumerate(row):
            css = ' class="wrapcell"' if wide and index in {1, 2, 3} else ""
            output.append(f"<td{css}>{esc(cell)}</td>")
        output.append(f'<td class="sources">{source_html}</td></tr>')
    output.append("</tbody></table></div>")
    return "".join(output)


def page(filename: str, title: str, description: str, body: str) -> str:
    navigation = "".join(
        f'<a href="{href}"' + (' aria-current="page"' if href == filename else "") + f">{esc(label)}</a>"
        for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{esc(description)}"><title>{esc(title)} · NBA Own Lines</title>
<link rel="stylesheet" href="style.css"></head><body><a class="skip" href="#main">Skip to content</a>
<header class="masthead"><div class="wrap"><div class="topline"><div><div class="brand"><div class="mark">NBA</div><div><p class="eyebrow">Own5 · independent research</p><h1>NBA Own Lines</h1></div></div><p>Official-source evidence → transparent calculations → fail-closed validation</p></div><div class="asof"><b>Snapshot</b><br>{esc(AS_OF)}<br>2026–27 regular season</div></div>
<nav class="nav" aria-label="Dashboard sections">{navigation}</nav></div></header>
<main id="main" class="wrap">{body}</main>
<footer class="footer"><div class="wrap"><p><b>Research, not betting advice.</b> Calculated lines, probabilities and fair American prices are analyst-derived, not sportsbook quotes or NBA endorsements. No qualified strategy or stake is recommended. Luck cannot be removed; only tested against.</p><p>Official NBA links are supplied for manual review. If you choose to bet, follow local law and use responsible-gambling limits. US support: 1-800-GAMBLER.</p><p>Additive Own5 namespace · source snapshot {esc(AS_OF)} · <a href="review.html">Review limitations and blanks</a></p></div></footer></body></html>"""


def section(title: str, subtitle: str, content: str) -> str:
    return f'<section class="section"><div class="sectionhead"><h3>{esc(title)}</h3><p>{esc(subtitle)}</p></div>{content}</section>'


def pagehead(kicker: str, title: str, description: str) -> str:
    return f'<div class="pagehead"><p class="eyebrow">{esc(kicker)}</p><h2>{esc(title)}</h2><p>{esc(description)}</p></div>'


def build_pages(data: dict, derived: dict) -> dict[str, str]:
    sources = data["source_map"]
    lines = derived["lines"]
    correlations = derived["correlations"]
    leaderboard = derived["leaderboard"]
    player_correlations = [row for row in correlations if row["scope"] == "Player-game"]
    strongest_team = next(row for row in correlations if row["pair"] == "NetRtg × Win%")
    pages = {}

    summary_rows = [
        ["Own lines", f"{len(lines)} November 4–5 games calculated from shrunk OffRtg/DefRtg/PACE", "Research baselines only; market and edge cells are blank", "lines.html"],
        ["Validation", "0 of 7 strategies qualified; 0 prospective graded forecasts", "No active single, parlay or prop-combo signal", "gates.html"],
        ["Team association", f"NetRtg × Win% r = {strongest_team['r']:.4f} (n = 30)", "Strong contemporaneous association, not out-of-sample skill", "correlations.html"],
        ["Player luck screen", f"0 of {len(player_correlations)} exploratory tests has Holm-adjusted p < 0.05", "Raw correlations do not survive multiplicity control", "correlations.html"],
        ["Availability", "Anthony Edwards is Out; several team reports were not yet submitted", "Edwards props suppressed; other unknowns held", "players.html"],
        ["Competition", "No score, ROI, CLV, rank or monetary prize is claimed", "Current reward: 0 research points for every entrant", "leaderboard.html"],
    ]
    body = pagehead("Executive summary", "Originate lines. Withhold unjustified bets.", "A current NBA research desk with reproducible calculations and explicit evidence boundaries.")
    body += f"""<div class="hero"><div class="panel decision"><p class="eyebrow">Executive decision</p><h2>16 calculated game lines.<br><strong>0 qualified betting strategies.</strong></h2><p>The model publishes transparent ratings-only baselines for the confirmed November 4–5 slate. It does not convert those baselines into picks: availability is incomplete, no official sportsbook quote was captured, and no prospective holdout has established skill. This is the intended fail-closed result, not missing work.</p><div class="toc"><a href="lines.html">Review the lines</a><a href="methodology.html">Inspect formulas</a><a href="review.html">See all 11 flags</a></div></div><div class="panel card"><h3>What “remove luck” means here</h3><p>Random variation cannot be deleted from sport. This desk freezes rules before outcomes, requires prospective samples, compares against baselines, applies exact null tests and corrects for multiple comparisons. Until those gates pass, skill, profit and rewards remain unclaimed.</p></div></div>"""
    body += f"""<div class="metrics"><div class="card metric"><b>30</b><span>official team rows</span></div><div class="card metric"><b>16</b><span>confirmed upcoming games</span></div><div class="card metric"><b>26</b><span>player-game evidence rows</span></div><div class="card metric zero"><b>0 / 7</b><span>qualified strategies</span></div><div class="card metric zero"><b>0 / 16</b><span>Holm-significant player tests</span></div></div>"""
    body += '<div class="grid3">' + "".join(
        f'<div class="card"><h3>{esc(label)}</h3><p>{esc(text)}</p><a href="{href}">Open section →</a></div>'
        for label, text, href in (
            ("01 · Evidence", "Team, schedule, player and injury rows with direct NBA review links.", "sources.html"),
            ("02 · Origination", "Spreads, totals, projected scores and no-vig model prices from disclosed formulas.", "lines.html"),
            ("03 · Competition", "Singles, parlays and prop combos held to the same prospective gates.", "leaderboard.html"),
        )
    ) + "</div>"
    body += section("Executive findings", "Every row links to the official evidence domain", table(
        ["Area", "Finding", "Decision / analysis", "Dashboard", "Official source / context"],
        [row[:3] + [""] for row in summary_rows],
        [link("Open " + row[0], row[3]) + " " + source_links(data, "S10" if row[0] == "Availability" else "S04" if row[0] == "Player luck screen" else "S02") for row in summary_rows],
        "Internal dashboard links and official NBA context are both provided. Internal links do not replace official evidence.", True,
    ))
    # Add the internal destination as visible text in the dashboard column without faking a raw HTML cell.
    body += '<div class="callout info"><b>Reading rule:</b> negative spreads favor that team; fair American prices come from the analyst logistic model and contain no sportsbook margin. Empty cells are deliberate. No over/under, side, parlay or prop is recommended.</div>'
    pages["index.html"] = page("index.html", "Executive overview", "Verified NBA research-line snapshot and executive summary", body)

    line_rows, line_sources = [], []
    for row in lines:
        game_url = f"https://www.nba.com/game/{row['slug']}/"
        line_rows.append([
            f"{row['date']} · {row['time_et']} ET", f"{row['away']} @ {row['home']}", num(row["away_points"]), num(row["home_points"]),
            spread(row["away_spread"]), spread(row["home_spread"]), num(row["total"]), percent(row["home_probability"]),
            american(row["away_fair_american"]), american(row["home_fair_american"]), "", "", "Research only",
        ])
        line_sources.append(source_links(data, "S02", extra=[("Game", game_url)]))
    body = pagehead("Own lines", "16 ratings-only game baselines", "Pregame matchups and records come from official NBA schedule cards; ratings come from the official 2026–27 advanced team table.")
    body += '<div class="callout danger"><b>Not market odds or betting picks.</b> The model has zero home-court adjustment, no injury adjustment and no overtime adjustment. Market spread/total and edge columns are intentionally blank. Projections use information frozen before these games.</div>'
    body += section("Projected scores, spreads, totals and fair prices", "Fair American = analyst probability converted to no-vig odds", table(
        ["Date · tip", "Matchup", "Away pts", "Home pts", "Away spread", "Home spread", "Total", "Home win", "Away fair ML", "Home fair ML", "Market spread", "Edge", "Release", "Official review"],
        line_rows, line_sources, "Analyst-derived values; official sources support inputs and matchups, not the model output.", False,
    ))
    league = derived["league"]
    param_rows = [
        ["League OffRtg baseline", num(league["off_rtg"], 3), "Possession-weighted from 30 rounded official team rows", "Analyst calculation"],
        ["League PACE baseline", num(league["pace"], 3), "Possession-weighted from official PACE and POSS", "Analyst calculation"],
        ["Prior strength", "10.0 games", "Shrinks each team rating toward the league baseline", "Analyst-set assumption"],
        ["Home-court advantage", "0.0 points", "No unmeasured home adjustment", "Analyst-set assumption"],
        ["Logistic scale", "6.0 points", "Maps projected home margin to a win probability", "Analyst-set assumption"],
        ["Overtime", "Not modeled", "Ratings baseline uses PACE per 48 minutes", "Official rules context"],
    ]
    body += section("Model parameters", "Disclosed, reproducible and not NBA-issued", table(
        ["Parameter", "Value", "Role", "Classification", "Official context"], param_rows,
        [source_links(data, "S11" if i < 5 else "S12") for i in range(len(param_rows))],
        "Empty or assumed values are never presented as official NBA facts.", True,
    ))
    pages["lines.html"] = page("lines.html", "Own game lines", "Calculated NBA spreads, totals and fair prices", body)

    schedule_map = {row["game_id"]: row for row in data["schedule"]}
    prop_rows, prop_sources = [], []
    for row in derived["player_props"]:
        game = schedule_map[row["upcoming_game_id"]]
        means, refs = row["means"], row["reference_lines"]
        prop_rows.append([
            row["player"], f"{game['away']} @ {game['home']} · {game['date']}", row["gp"],
            f"{means['pts']:.2f} → {refs['pts']:.1f}", f"{means['reb']:.2f} → {refs['reb']:.1f}",
            f"{means['ast']:.2f} → {refs['ast']:.1f}", f"{means['threepm']:.2f} → {refs['threepm']:.1f}",
            row["availability"] or "Unconfirmed", row["availability_note"], row["release_status"], "",
        ])
        prop_sources.append(source_links(data, row["source_id"], "S10", extra=[("Game", f"https://www.nba.com/game/{game['slug']}/")]))
    body = pagehead("Players & prop combos", "Reference lines are not playable props", "Mean → nearest-half reference line, calculated from each complete selected 2026–27 game log. No direction or over/under is recommended.")
    body += '<div class="callout danger"><b>Availability gate:</b> Edwards is officially Out and suppressed. All other selected players remain held because this snapshot does not confirm availability. Playable-line cells are blank for every player.</div>'
    body += section("Player reference lines", "PTS / REB / AST / 3PM; official averages reconciled by script", table(
        ["Player", "Upcoming game", "GP", "PTS mean → ref", "REB mean → ref", "AST mean → ref", "3PM mean → ref", "Official status", "Report note", "Release", "Playable lines", "Official review"],
        prop_rows, prop_sources, "Reference lines are analyst arithmetic. Official status is blank unless explicitly listed; not being listed is not treated as Available.", True,
    ))
    combo_rows, combo_sources = [], []
    for row in derived["prop_combos"]:
        game = schedule_map[row["game_id"]]
        combo_rows.append([
            row["combo_id"], row["player"], f"{game['away']} @ {game['home']}",
            " + ".join(f"{leg['market'].upper()} {leg['reference_line']:.1f}" for leg in row["legs"]),
            "", "", "", row["release_status"],
        ])
        combo_sources.append(source_links(data, row["source_id"], "S10", extra=[("Game", f"https://www.nba.com/game/{game['slug']}/")]))
    body += section("Player prop combinations", "No direction, joint probability or payout without dependence and market evidence", table(
        ["Combo", "Player", "Game", "Reference legs only", "Directions", "Joint probability", "Payout", "Release", "Official review"],
        combo_rows, combo_sources, "Continuous-stat Pearson r on the correlations page is not a joint-hit probability.", True,
    ))
    game_rows, game_sources = [], []
    for row in data["player_games"]:
        player = data["player_map"][row["player_id"]]
        game_rows.append([player["player"], row["date"], row["matchup"], row["result"], row["minutes"], row["pts"], row["reb"], row["ast"], row["threepm"]])
        game_sources.append(source_links(data, player["source_id"], extra=[("NBA game", row["source_url"])]))
    body += section("Complete selected player-game evidence", "26 rows; no omitted games within each selected player's current-season log", table(
        ["Player", "Date", "Matchup", "W/L", "MIN", "PTS", "REB", "AST", "3PM", "Official review"],
        game_rows, game_sources, "Fields transcribed from the official player logs; each row also links its official NBA game page.", False,
    ))
    pages["players.html"] = page("players.html", "Players and prop combos", "Official player-game evidence and held prop references", body)

    team_rows, team_sources = [], []
    for row in data["teams"]:
        team_rows.append([row["team"], row["abbr"], row["gp"], row["wins"], row["losses"], f"{int(row['wins']) / int(row['gp']):.3f}", row["off_rtg"], row["def_rtg"], row["net_rtg"], row["pace"], row["poss"]])
        team_sources.append(source_links(data, "S02", "S03"))
    body = pagehead("Team data", "All 30 official team-rating rows", "NBA advanced statistics, 2026–27 regular season, frozen at the snapshot. Win% is the only derived column on this table.")
    body += section("Ratings used by the model", "OffRtg/DefRtg per 100 possessions; PACE per 48 minutes", table(
        ["Team", "Abbr", "GP", "W", "L", "Win%", "OffRtg", "DefRtg", "NetRtg", "PACE", "POSS", "Official review"],
        team_rows, team_sources, "Both NBA advanced-table chunks were transcribed. GP = W + L and schedule records are automatically reconciled.", False,
    ))
    pages["teams.html"] = page("teams.html", "Official team data", "All 30 NBA advanced team-stat rows", body)

    strategy_rows, strategy_sources = [], []
    for row in leaderboard:
        strategy_rows.append([row["strategy_id"], row["strategy"], row["category"], row["hypothesis"], f"{row['passed_gates']} / {row['required_gates']}", ", ".join(row["failed_gate_ids"]), row["status"]])
        strategy_sources.append(source_links(data, row["source_id"]))
    body = pagehead("Strategy registry", "Singles, parlays and player prop combos", "Each hypothesis is registered before evaluation. A strategy cannot become a signal until every required gate passes.")
    body += section("Seven candidate strategies", "No entrant is qualified; no strategy is cherry-picked after results", table(
        ["ID", "Strategy", "Category", "Hypothesis", "Gates passed", "Open gates", "Decision", "Official context"],
        strategy_rows, strategy_sources, "Official links support the evidence domain; the hypotheses and policies are analyst-defined.", True,
    ))
    policy_rows = [
        ["Single side / total", "One calibrated marginal forecast plus a timestamped price", "Availability, market, holdout, baseline and luck gates", "No current release"],
        ["Cross-game parlay", "Joint distribution; independence must be tested, not assumed", "Leg correlation, payout, settlement and joint calibration", "Joint values blank"],
        ["Same-game side + total", "Explicit joint score distribution", "Shared-game dependence and same-game settlement rules", "Joint values blank"],
        ["Player prop combo", "Threshold-specific joint-hit model with current availability", "Within-player dependence, directions, prices and Out suppression", "All combos held/suppressed"],
    ]
    body += section("Combination construction policy", "Multiplying unverified marginal hit rates is prohibited", table(
        ["Bet type", "Required model", "Additional evidence", "Current decision", "Official context"], policy_rows,
        [source_links(data, "S02"), source_links(data, "S01"), source_links(data, "S01"), source_links(data, "S04")],
        "The desk analyzes combination requirements without inventing a same-game parlay payout.", True,
    ))
    pages["strategies.html"] = page("strategies.html", "Strategy registry", "NBA single, parlay and prop-combo strategy hypotheses", body)

    def correlation_table(rows: list[dict], player: bool) -> str:
        output_rows, output_sources = [], []
        for row in rows:
            output_rows.append([row["subject"], row["pair"], row["n"], num(row["r"], 4), num(row["p_permutation"], 5) if player else "", num(row["p_holm"], 5) if player else "", row["note"]])
            output_sources.append(source_links(data, row["source_id"]))
        return table(["Subject", "Pair", "n", "Pearson r", "Exact perm. p", "Holm p", "Interpretation", "Official inputs"], output_rows, output_sources,
                     "Player p-values are exact two-sided label-permutation tests; Holm correction covers all 16 player tests. Team p-cells are intentionally not applicable/blank.", True)

    body = pagehead("Correlation analysis", "Measure association. Do not confuse it with an edge.", "Pearson r ranges from −1 to +1. These contemporaneous descriptive statistics do not establish prediction, causation, profitability or threshold-specific joint-hit rates.")
    body += f'<div class="finding"><b>Multiplicity result:</b> 0 of {len(player_correlations)} player tests has Holm-adjusted p &lt; 0.05. Two strong raw associations (Luka PTS×3PM and Shai PTS×AST) do not survive the family-wise correction at that threshold. This is why raw correlation alone cannot qualify a strategy.</div>'
    body += section("Team-level correlations", "30 teams; current-season snapshot", correlation_table([row for row in correlations if row["scope"] == "Team"], False))
    body += section("Player-game correlations", "Four selected players; 4–8 observations each; exploratory only", correlation_table(player_correlations, True))
    pages["correlations.html"] = page("correlations.html", "Correlations", "Team and player NBA Pearson correlations with luck screening", body)

    gate_def_rows = [[gate["id"], gate["name"], gate["requirement"], "Unknown never passes"] for gate in derived["gates"]]
    body = pagehead("Validation gates", "Fail closed. No unknown is treated as a pass.", "G00–G09 are analyst-defined research controls. Official links identify the evidence domain; they do not imply NBA approval of the gate.")
    body += section("Gate definitions", "G08 applies to combinations only; every other gate applies to every entrant", table(
        ["Gate", "Name", "Pass requirement", "Default", "Official evidence domain"], gate_def_rows,
        [source_links(data, gate["source_id"]) for gate in derived["gates"]], "A missing input, unresolved availability or absent result fails the relevant gate.", True,
    ))
    gate_lookup = {(row["strategy_id"], row["gate_id"]): row["status"] for row in derived["gate_rows"]}
    matrix_rows, matrix_sources = [], []
    gate_ids = [gate["id"] for gate in derived["gates"]]
    for strategy in leaderboard:
        matrix_rows.append([strategy["strategy"]] + [gate_lookup.get((strategy["strategy_id"], gid), "N/A") for gid in gate_ids] + [strategy["status"]])
        matrix_sources.append(source_links(data, strategy["source_id"]))
    body += section("Strategy × gate matrix", "N/A is not a pass; it means combo-dependence gate G08 is not applicable to singles", table(
        ["Strategy"] + gate_ids + ["Result", "Official context"], matrix_rows, matrix_sources,
        "G00/G01/G09 pass on documented provenance/specification/risk policy. Open evidence gates prevent qualification.", False,
    ))
    pages["gates.html"] = page("gates.html", "Validation gates", "Fail-closed NBA strategy validation matrix", body)

    board_rows, board_sources = [], []
    for row in leaderboard:
        board_rows.append(["", row["strategy"], row["category"], row["observed_n"], "", "", "", f"{row['passed_gates']} / {row['required_gates']}", row["status"], row["reward_points"]])
        board_sources.append(source_links(data, row["source_id"]))
    body = pagehead("Leaderboard competition", "No performance ranking without prospective evidence", "Research points are non-cash recognition only. A rank requires every gate, at least 100 prospective graded forecasts, and a declared scoring window.")
    body += section("Current leaderboard", "All entrants unranked; score, Brier skill, ROI and CLV deliberately blank", table(
        ["Rank", "Strategy", "Category", "Graded N", "Score", "Brier skill", "ROI / CLV", "Gates", "Status", "Research points", "Official context"],
        board_rows, board_sources, "Zero points reflects ineligibility, not a measured loss. No monetary reward is funded or promised.", True,
    ))
    reward_rows = [
        ["1st eligible strategy", "100", "Highest preregistered score after all gates; tie rules declared before scoring"],
        ["2nd eligible strategy", "60", "Next highest eligible score; no prize if fewer than two qualify"],
        ["3rd eligible strategy", "40", "Next highest eligible score; no prize if fewer than three qualify"],
    ]
    body += section("Future non-cash reward policy", "Not active while zero strategies qualify", table(
        ["Eligible position", "Research points", "Condition", "Official input context"], reward_rows,
        [source_links(data, "S02") for _ in reward_rows], "Analyst-defined competition policy; NBA.com is input context only and is not a sponsor.", True,
    ))
    pages["leaderboard.html"] = page("leaderboard.html", "Leaderboard", "Fail-closed NBA strategy competition and reward policy", body)

    method_rows = [
        ["1 · Freeze", "Save reviewed official rows, timestamp, formulas and exclusions before tip-off", "Prevents retroactive input selection"],
        ["2 · Shrink", "adjusted = league + GP/(GP+10) × (official − league)", "Reduces small-sample extremes; prior is analyst-set"],
        ["3 · Match up", "expected away efficiency = adjusted away OffRtg + adjusted home DefRtg − league OffRtg; symmetric for home", "Uses official definitions and possession units"],
        ["4 · Pace and score", "expected possessions = mean(adjusted PACE); points = possessions × efficiency / 100", "48-minute baseline; no overtime or injury adjustment"],
        ["5 · Price", "p(home) = logistic(home margin / 6); convert p and 1−p to no-vig American prices", "Analyst probability model, not a market quote"],
        ["6 · Validate", "Prospective scoring, baseline comparison, confidence intervals and exact/simulated luck tests", "No current performance claim"],
    ]
    body = pagehead("Methodology", "From official rows to reproducible research lines", "The calculations are deliberately simple enough to audit line by line. Assumptions are disclosed rather than filled in as facts.")
    body += section("Line-origination pipeline", "All arithmetic is implemented in model.py", table(
        ["Step", "Rule", "Purpose / boundary", "Official definitions / inputs"], method_rows,
        [source_links(data, "S02"), source_links(data, "S11"), source_links(data, "S11"), source_links(data, "S11"), source_links(data, "S02"), source_links(data, "S01")],
        "Spread = −rounded projected margin for the home team; total = rounded sum of projected scores; nearest-half rounding is independent.", True,
    ))
    skill_rows = [
        ["Prospective window", "At least 100 graded forecasts per strategy", "Current N = 0; no skill claim"],
        ["Proper scoring", "Brier score and log loss against a frozen baseline", "Current values blank"],
        ["Price-aware evaluation", "ROI and closing-line value only with timestamped prices and settlement", "Current values blank"],
        ["Binary luck test", "P[X ≥ k] = Σ C(n,i)p₀ⁱ(1−p₀)ⁿ⁻ⁱ under a preregistered null", "No hit-rate test is run without outcomes"],
        ["Multiplicity", "Holm correction across the 16 exploratory player correlation tests", "0 remain below 0.05"],
        ["Dependence", "Joint-hit and threshold-specific analysis for combos", "Pearson continuous-stat r is not substituted"],
    ]
    body += section("Skill versus luck protocol", "Randomness is quantified, not claimed away", table(
        ["Control", "Rule", "Current result", "Official evidence domain"], skill_rows,
        [source_links(data, "S02"), source_links(data, "S11"), source_links(data, "S01"), source_links(data, "S04"), source_links(data, "S04"), source_links(data, "S04")],
        "The binomial function is implemented and unit-tested for future preregistered binary markets; p₀ must match the market, not automatically be 0.5.", True,
    ))
    body += '<div class="callout info"><b>Reproducibility:</b> <code>python3 nba-own-lines/model.py</code> validates all source rows and regenerates <code>derived.json</code>; <code>build.py</code> renders these pages; <code>check.py</code> audits row links, internal links and derived determinism.</div>'
    pages["methodology.html"] = page("methodology.html", "Methodology", "Transparent NBA line-origination and skill-versus-luck methods", body)

    source_rows = [[row["source_id"], row["publisher"], row["title"], row["retrieved_at"], row["scope"], row["verification"]] for row in data["sources"]]
    body = pagehead("Source register & audit", "Official NBA evidence, row by row", "Every factual NBA value in the CSV snapshot is covered by these sources. Calculated values are labeled analyst-derived throughout.")
    body += section("Official source register", "12 sources; retrieved at the frozen snapshot", table(
        ["ID", "Publisher", "Official page", "Retrieved UTC", "Scope", "Verification performed", "Direct link"], source_rows,
        [link("Open official source", row["url"]) for row in data["sources"]], "Dynamic pages can change after retrieval; this limitation is flagged F01.", True,
    ))
    audit_rows = [
        ["Team cardinality", "30 rows / 30 unique IDs / 30 unique abbreviations", "PASS"],
        ["Team arithmetic", "GP = W + L for every team; NetRtg reconciles within rounding tolerance", "PASS"],
        ["Schedule reconciliation", "16 unique game IDs; 32 team-game records match the advanced table; all 30 teams covered", "PASS"],
        ["Player completeness", "26 rows match selected official GP totals: 7 + 4 + 8 + 7", "PASS"],
        ["Player average reconciliation", "16 mean checks (4 players × PTS/REB/AST/3PM) match official rounded averages", "PASS"],
        ["Source audit", "Every source is HTTPS on an official NBA host; every player-game row links its official game", "PASS"],
        ["Model output", "16 lines; probabilities sum to one; no market/edge values; 0 qualified strategies", "PASS"],
        ["Publication scope", "Only nba-own-lines/, research/nba-own-lines/ and this session's coordination record", "PASS"],
    ]
    body += section("Automated evidence checks", "Run by model.py, check.py and unit tests", table(
        ["Check", "Coverage", "Result", "Official source / context"], audit_rows,
        [source_links(data, "S02"), source_links(data, "S02"), source_links(data, "S01", "S02"), source_links(data, "S04"), source_links(data, "S04"), source_links(data, "S01"), source_links(data, "S02"), source_links(data, "S03")],
        "PASS describes structural/reconciliation checks, not predictive validation. External URLs still require manual review of the live official page.", True,
    ))
    pages["sources.html"] = page("sources.html", "Official sources", "NBA source register and evidence reconciliation", body)

    flag_rows = [[row["flag_id"], row["severity"], row["area"], row["finding"], row["consequence"], row["status"]] for row in data["flags"]]
    body = pagehead("Flagged for Review", "Irregularities, unknowns and intentional blanks", "These items do not block publication. They block betting qualification and are kept visible for post-publication review.")
    body += '<div class="callout danger"><b>Review before relying on this snapshot.</b> Eleven nonblocking publication flags are listed below. High-severity evidence gaps are the reason no strategy is qualified.</div>'
    body += section("Review register", "F01–F11; each row links to its official evidence or review context", table(
        ["ID", "Severity", "Area", "Finding", "Consequence", "Status", "Official source / context"], flag_rows,
        [source_links(data, row["source_id"]) for row in data["flags"]], "A source link in a missing-input row provides review context; it does not prove that the missing value exists.", True,
    ))
    blank_rows = [
        ["Market spread / total / price / edge", "All 16 game rows", "No timestamped official sportsbook quote", "F04"],
        ["Playable player lines and directions", "All selected players and combos", "Availability unresolved or player Out", "F02 / F03"],
        ["Combo joint probability / payout", "All 4 prop combos and parlay strategies", "Dependence, thresholds, prices and settlement unresolved", "F09"],
        ["Score / Brier skill / ROI / CLV", "All 7 strategies", "No prospective settled ledger or price history", "F07"],
        ["Leaderboard rank", "All 7 strategies", "No eligible entrant; zero is ineligibility, not a loss", "F07 / F11"],
    ]
    body += section("Intentional blank register", "Blank means not verified or not applicable—never an inferred zero", table(
        ["Blank field", "Where", "Reason", "Flag", "Official review context"], blank_rows,
        [source_links(data, "S01"), source_links(data, "S10"), source_links(data, "S04"), source_links(data, "S02"), source_links(data, "S02")],
        "Derived JSON uses null for these fields; HTML leaves the cells empty.", True,
    ))
    pages["review.html"] = page("review.html", "Flagged for Review", "NBA evidence irregularities, unknowns and intentional blanks", body)

    assert set(pages) == {filename for filename, _ in NAV}
    return pages


def main() -> None:
    data = load_data()
    derived = write_derived()
    pages = build_pages(data, derived)
    for filename, content in pages.items():
        (ROOT / filename).write_text(content, encoding="utf-8")
    print(f"Built {len(pages)} pages; {derived['metadata']['schedule_rows']} lines; {derived['metadata']['qualified_strategies']} qualified strategies.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render the desk's static pages from the committed CSVs (stdlib only, deterministic).

Python 3.11-compatible: no nested same-type quotes inside f-strings; row builders take
keyword arguments matching the CSV columns. Every table row carries its official source
link, or an explicit blank+flag marker.
"""
from __future__ import annotations

import csv
import html
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data" / "nfl-desk-7e228db8"
GH = "https://github.com/sassnarep3-star/Own5"

NAV = [
    ("index.html", "Overview"),
    ("lines.html", "Week 11 lines"),
    ("price-store.html", "Price snapshots"),
    ("results.html", "Verified results"),
    ("ratings.html", "Ratings"),
    ("correlations.html", "Correlations"),
    ("injuries.html", "Injury report"),
    ("schedule.html", "Schedule & venues"),
    ("leaderboard.html", "Leaderboard & gates"),
    ("readiness.html", "Decision readiness"),
    ("suggestions.html", "Suggestions"),
    ("questions.html", "Questions"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
    ("executive-summary.html", "Executive summary"),
]


def esc(v) -> str:
    return html.escape(str(v if v is not None else ""), quote=True)


def rd(name: str) -> list[dict]:
    with io.open(DATA / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def link(url: str, label: str | None = None) -> str:
    if not url:
        return '<span class="blank">blank</span>'
    return '<a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + esc(label or url) + "</a>"


def blank_flag(flag: str = "flagged") -> str:
    return '<span class="blank">blank</span> <span class="badge warn">' + esc(flag) + "</span>"


def badge(value: str) -> str:
    v = (value or "").lower()
    if any(k in v for k in ("pass", "met", "match", "true", "final", "fixed")) and "not met" not in v:
        cls = "ok"
    elif any(k in v for k in ("fail", "unmet", "high")):
        cls = "bad"
    elif any(k in v for k in ("partial", "open", "pending", "medium", "low", "proposed", "in progress", "blank", "control", "pre_registered", "not_certified")):
        cls = "warn"
    else:
        cls = "neutral"
    return '<span class="badge ' + cls + '">' + esc(value) + "</span>"


def note(text: str) -> str:
    return '<p class="note">' + text + "</p>"


def table(headers: list[str], rows: list[list[str]], cls: str = "") -> str:
    h = "".join("<th>" + c + "</th>" for c in headers)
    body = ""
    for r in rows:
        body += "<tr>" + "".join("<td>" + c + "</td>" for c in r) + "</tr>\n"
    return '<div class="tscroll"><table class="' + cls + '"><thead><tr>' + h + "</tr></thead>\n<tbody>\n" + body + "</tbody></table></div>"


def page(title: str, body: str, active: str) -> str:
    nav = "".join('<a href="' + h + '"' + (' class="active"' if h == active else "") + ">" + esc(t) + "</a>" for h, t in NAV)
    return (
        '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "<title>" + esc(title) + " — Own5 NFL Verification &amp; Decision Desk (7e228db8)</title>\n"
        '<link rel="stylesheet" href="style.css"></head>\n<body>\n<header><div class="wrap">\n'
        '<p class="crumb"><a href="index.html">Own5 NFL Verification &amp; Decision Desk</a> · '
        "session <code>7e228db8</code> · official reads 2026-11-19 UTC</p>\n"
        "<h1>" + esc(title) + "</h1>\n<nav>" + nav + "</nav>\n</div></header>\n"
        '<main class="wrap">\n' + body + "\n</main>\n"
        '<footer class="wrap"><p>Every value links to an official source or is an explicit blank+flag. '
        'Raw excerpts with SHA-256: <a href="https://github.com/sassnarep3-star/Own5/tree/main/data/nfl-desk-7e228db8/raw" '
        'target="_blank" rel="noopener noreferrer">data/nfl-desk-7e228db8/raw/</a>. '
        "Unverified values are never filled in.</p></footer>\n</body></html>\n"
    )


def main() -> None:
    ctx = json.loads((DATA / "build_context.json").read_text(encoding="utf-8"))
    flags = rd("flagged.csv")
    readiness = rd("readiness.csv")
    met = sum(1 for r in readiness if r["status"] == "Met")
    part = sum(1 for r in readiness if "artial" in r["status"])
    unmet = sum(1 for r in readiness if r["status"] == "Unmet")
    open_flags = sum(1 for r in flags if r["status"] == "open")
    high = sum(1 for r in flags if r["severity"] == "high")
    sweep = rd("verifier_sweep.csv")
    fails = [r for r in sweep if r["verdict"] == "FAIL"]
    pages = {}

    # ------------------------------------------------------------------ index
    kpi = ctx["n_finals"]
    inj_rows = ctx["n_inj_rows"]
    body = f"""
<section class="hero">
<p class="kicker">NFL 2026 · Week 11 · {kpi} verified finals through Week 10 · 32/32 clubs reconciled to the official standings</p>
<h2>One screen before any decision</h2>
<p>This desk originates its own NFL lines from officially sourced numbers only, keeps a price-snapshot store and a
pre-registered leaderboard, and publishes every gap instead of hiding it. No manual owner input is required to
rebuild: <code>python3 nfl-desk-7e228db8/build_desk.py &amp;&amp; python3 nfl-desk-7e228db8/build_site.py</code>.</p>
<ul class="kpis">
<li><strong>{kpi}</strong><span>verified finals<br>(W1–8 corpus 120 + patch 1 + W9 15 + W10 14)</span></li>
<li><strong>32/32</strong><span>clubs reconciled to official standings<br>(W-L-T, PF, PA exact)</span></li>
<li><strong>{inj_rows}</strong><span>official injury-report rows<br>(read 2026-11-19T07:03Z)</span></li>
<li><strong>39</strong><span>price snapshots opened<br>(side → total → moneyline)</span></li>
<li><strong>{met}/{len(readiness)}</strong><span>requirements fully met<br>({part} partial, {unmet} unmet)</span></li>
<li><strong>{open_flags}</strong><span>open flags<br>({high} high severity)</span></li>
</ul>
</section>
<section>
<h2>Decision-readiness (summary)</h2>
{table(["Status", "Requirements", "What clears the rest"], [
    [badge("Met"), str(met), "Requirement delivered in a desk namespace with sources"],
    [badge("Partially met"), str(part), "Named blockers on the <a href='readiness.html'>readiness table</a> (gate + number to clear per row)"],
    [badge("Unmet"), str(unmet), "Blocked on owner decisions Q7-01 (price source), Q7-03 (capture automation), Q7-04–Q7-06 (official sources)"],
])}
{note('Blocking owner decisions are collected on the <a href="questions.html">Questions page</a>. '
      'Suggestions are reviewable on the <a href="suggestions.html">Suggestions page</a> — nothing is implemented '
      'without a recorded decision. Irregularities found by the line-by-line review are on the '
      '<a href="flagged.html">Flagged for Review page</a> (open + high counts above). The repo-wide verifier '
      "sweep (37 scripts, 2026-11-19) is published on the <a href='flagged.html'>Flagged page</a>.")}
</section>
<section>
<h2>What would change our mind</h2>
{table(["Claim", "Would be revised if"], [
    ["Model lines are usable signal", "Prospective shadow results from Week 11 onward show Brier skill ≤ 0 against the random/favourite baselines (G0/G6 gates)"],
    ["Negative home advantage (−0.93 pts, n=150) is a season effect", "The venue/roof split (S7-09) shows it is a venue-mix artefact, or prospective weeks revert HFA positive"],
    ["Corpus is complete for backtests", "A further reconciliation mismatch appears when Week 11 finals are ingested (the Week 8 MNF patch proved such gaps exist)"],
])}
</section>"""
    pages["index.html"] = page("Overview", body, "index.html")

    # ------------------------------------------------------------------ lines
    lines = rd("lines_week11.csv")

    def line_row(game_id, date_et, time_et, away, home, fair_spread_home, fair_total,
                 p_home_win_novig, fair_odds_home_decimal, fair_odds_away_decimal, source_url, **_):
        return [
            "<code>" + esc(game_id) + "</code>",
            esc(away) + " @ " + esc(home),
            esc(date_et) + " " + esc(time_et) + " ET",
            "<strong>" + esc(fair_spread_home) + "</strong> (home)",
            blank_flag("F7-P01"), blank_flag("diff"),
            "<strong>" + esc(fair_total) + "</strong>",
            blank_flag("F7-P01"), blank_flag("diff"),
            "<strong>" + esc(p_home_win_novig) + "</strong>",
            esc(fair_odds_home_decimal) + " / " + esc(fair_odds_away_decimal),
            link(source_url, "official schedule"),
        ]

    lrows = [line_row(**g) for g in lines]
    byes = ", ".join(ctx["byes"])
    spec = ctx["spec"]
    lines_note = note(
        "Model spec <code>" + esc(spec["model_spec_version"]) + "</code> (frozen before the window; the commit hash is the "
        "registration): opponent-aware SRS margin ratings + fitted home advantage <strong>" + esc(str(ctx["hfa"])) + " pts</strong> "
        "+ margin σ <strong>" + esc(str(ctx["sigma_m"])) + "</strong>; totals from per-club points-involved pace, σ "
        "<strong>" + esc(str(ctx["sigma_t"])) + "</strong>; fitted in-sample on <strong>" + esc(str(ctx["n_finals"])) + "</strong> "
        "verified finals (F7-14). Market columns are blank by policy — no verified operator price exists (F7-P01), so the "
        "difference columns are blank too (R023). Probabilities and full inputs (SHA-256) are stored on every row (R035). "
        "Kickoff of the first originated game: <code>" + esc(spec["week11_kickoff_utc"]) + "</code> — this desk's lines were "
        "committed before it."
    )
    body = f"""
<section>
<h2>Origination order: side → total → moneyline (R022)</h2>
{lines_note}
{table(["Game", "Matchup", "Kickoff (ET)", "Fair spread (home)", "Market spread", "Spread diff",
        "Fair total", "Market total", "Total diff", "P(home win) no-vig", "Fair decimal odds (home/away)", "Source"], lrows)}
{note("Week 11 byes (official): <strong>" + esc(byes) + "</strong>. MIN@SF is the Mexico City international game "
      "(Estadio Banorte per official game centre). See <a href='price-store.html'>price snapshots</a> for the per-market "
      "store and <a href='flagged.html'>flags</a> for the market-data policy.")}
</section>"""
    pages["lines.html"] = page("Week 11 originated lines", body, "lines.html")

    # ------------------------------------------------------------ price store
    snaps = rd("price_snapshots.csv")

    def snap_row(snapshot_id, game_id, market, our_open_fair_value, opened_at_utc, inputs_sha256, **_):
        return [
            "<code>" + esc(snapshot_id) + "</code>", esc(game_id), esc(market),
            "<strong>" + esc(our_open_fair_value) + "</strong>",
            blank_flag("F7-P01"), blank_flag("F7-P01"), blank_flag("close"),
            blank_flag("residual"), blank_flag("CLV"),
            esc(opened_at_utc), "<code>" + esc(inputs_sha256[:16]) + "…</code>",
        ]

    srows = [snap_row(**s) for s in snaps]
    body = f"""
<section>
<h2>Price-snapshot store (R020) and price-data policy (R039)</h2>
{note(str(len(snaps)) + " immutable open snapshots (13 games × 3 markets) record <em>our</em> originated fair value at "
      "open, with the model inputs hash. Policy (frozen): no operator price is captured or estimated; market open/close, "
      "residual-vs-market and CLV stay blank+flagged until a licensed source exists (Q7-01). Closing values are written "
      "only from verified sources after each game.")}
{table(["Snapshot", "Game", "Market", "Our open fair value", "Market open", "Market close",
        "Close source", "Residual", "CLV", "Opened (UTC)", "Inputs hash"], srows)}
</section>"""
    pages["price-store.html"] = page("Price snapshot store", body, "price-store.html")

    # ----------------------------------------------------------------- results
    feed = rd("results_feed_2026_through_wk10.csv")

    def feed_row(week, date_et, away, home, away_pts, home_pts, status, international, source_url, **_):
        gp = "https://www.nfl.com/games/" + away.lower() + "-at-" + home.lower() + "-2026-reg-" + week
        intl = badge(international) if international else "—"
        return [esc(week), esc(date_et),
                "<strong>" + esc(away) + " " + esc(away_pts) + "</strong> @ " + esc(home) + " " + esc(home_pts),
                badge(status), intl, link(gp, "game page"), link(source_url, "schedule page")]

    w910 = [r for r in feed if r["week"] in ("9", "10")]
    rrows = [feed_row(**r) for r in w910]
    feed_url = GH + "/blob/main/data/nfl-desk-7e228db8/results_feed_2026_through_wk10.csv"
    body = f"""
<section>
<h2>Verified results feed (R021): {len(feed)} finals</h2>
{note("Weeks 1–8 come from the shared corpus (data/games_2026.json: 58 rows verified game-by-game on nfl.com, 62 from "
      "Pro-Football-Reference reconciled to official standings — inherited limitation F7-09). Weeks 9–10 were read from the "
      "official schedule pages on 2026-11-19 (rows below). The corpus was missing Week 8 MNF (CHI 34 @ SEA 17): proved by "
      "reconciliation and patched here (F7-06). After the patch, derived W-L-T/PF/PA match the official standings for "
      "<strong>all 32 clubs exactly</strong> — that reconciliation is the desk's hard gate.")}
{table(["Wk", "Date", "Final", "Status", "Intl", "Game page", "Source"], rrows)}
{note("The full 150-row feed: <a href='" + esc(feed_url) + "' target='_blank' rel='noopener noreferrer'>results_feed_2026_through_wk10.csv</a>.")}
</section>"""
    pages["results.html"] = page("Verified results feed", body, "results.html")

    # ---------------------------------------------------------------- ratings
    rt = rd("ratings_2026_wk11.csv")

    def rating_row(league_rank, team, srs_rating_pts, pace_pts_per_game, games_counted,
                   pf_per_game, pa_per_game, net_per_game, source_url, **_):
        return [esc(league_rank), "<strong>" + esc(team) + "</strong>", esc(srs_rating_pts),
                esc(pace_pts_per_game), esc(games_counted), esc(pf_per_game), esc(pa_per_game),
                esc(net_per_game), link(source_url, "official standings")]

    rrows = [rating_row(**r) for r in rt]
    body = f"""
<section>
<h2>Opponent-aware ratings (game-level results ingested)</h2>
{note("SRS-style least-squares margin ratings (pure stdlib, deterministic): margin = r_home − r_away + HFA. Opponent "
      "strength is baked in through the schedule actually played. HFA came out <strong>negative</strong> (−0.93 pts; home "
      "teams won 45.3% of 150 verified finals) — published as computed, not assumed (F7-10). Pace = per-club points "
      "involved per game (official PF+PA).")}
{table(["Rank", "Club", "SRS rating (pts)", "Pace (pts/gm)", "Games", "PF/gm", "PA/gm", "NET/gm", "Source"], rrows)}
</section>"""
    pages["ratings.html"] = page("Opponent-aware ratings", body, "ratings.html")

    # ----------------------------------------------------------- correlations
    cs = rd("correlations.csv")

    def corr_row(pair, pearson_r, n, ci95_low, ci95_high, source_url, method, **_):
        return ["<strong>" + esc(pair) + "</strong>", esc(pearson_r), esc(n),
                "[" + esc(ci95_low) + ", " + esc(ci95_high) + "]",
                link(source_url, "official standings"), esc(method)]

    crows = [corr_row(**c) for c in cs]
    body = f"""
<section>
<h2>Correlations — official sources only, n published (R009/R026)</h2>
{note("Pearson r computed in-repo from the 2026-11-19 official standings capture; Fisher-z 95% interval beside every "
      "value. No third-party rows.")}
{table(["Pair", "r", "n", "95% CI", "Source", "Method"], crows)}
</section>"""
    pages["correlations.html"] = page("Correlations", body, "correlations.html")

    # --------------------------------------------------------------- injuries
    inj = rd("injuries_2026_week11.csv")
    teams = []
    for t in sorted({r["team"] for r in inj}):
        trs = [r for r in inj if r["team"] == t]
        if len(trs) == 1 and trs[0]["practice_status"] == "No Injuries Reported":
            teams.append("<h3>" + esc(t) + "</h3><p>No Injuries Reported (official page, verbatim)</p>")
            continue
        rows = []
        for r in trs:
            gs = r["game_status"] or blank_flag("blank in official report")
            rows.append([esc(r["player"]), esc(r["position"]), r["injuries"] or "—",
                         esc(r["practice_status"]), gs])
        teams.append("<h3>" + esc(t) + " (" + str(len(trs)) + " rows)</h3>" +
                     table(["Player", "Pos", "Injury", "Practice status", "Game status"], rows, cls="compact"))
    raw_url = GH + "/blob/main/data/nfl-desk-7e228db8/raw/injuries_2026_week11.excerpt.txt"
    body = f"""
<section>
<h2>Official Week 11 injury report — 2026-11-19T07:03Z read (R031)</h2>
{note(str(inj_rows) + " rows across 26 clubs (two clubs officially report 'No Injuries Reported'). Blank game-status "
      "cells are <em>official blanks on the Wednesday read</em> — they are marked, never filled (S7-10). Practice "
      "designations will move by Friday/Saturday; deltas, not levels, are the signal (R031/R040). Reserve-list caveat: "
      "a player absent from this report is not automatically available (F7-03 DET/Aidan Hutchinson; F7-02 LAC/Daiyan "
      "Henley stale row; F7-11/F7-12 unconfirmed roster moves). Raw capture: "
      "<a href='" + esc(raw_url) + "' target='_blank' rel='noopener noreferrer'>verbatim excerpt + SHA-256</a>.")}
{''.join(teams)}
</section>"""
    pages["injuries.html"] = page("Injury report (Week 11)", body, "injuries.html")

    # --------------------------------------------------------------- schedule
    sch = rd("schedule_2026_week11.csv")

    def sched_row(game_id, away, home, date_et, time_et, network, venue_from_schedule_page,
                  neutral_site, venue_source, source_url, **_):
        intl_badge = " " + badge("intl") if neutral_site.startswith("yes") else ""
        return ["<code>" + esc(game_id) + "</code>", esc(away) + " @ " + esc(home),
                esc(date_et) + " " + esc(time_et) + " ET", esc(network),
                esc(venue_from_schedule_page) + intl_badge,
                link(venue_source, "venue source"), link(source_url, "official schedule")]

    srows = [sched_row(**g) for g in sch]
    body = f"""
<section>
<h2>Week 11 schedule, venues, and the league's dated announcement</h2>
{note("Venues are published schedule facts taken from the schedule page's own venue links; the two game-centre-verified "
      "venues are cross-checked (IND@HOU shows a naming conflict, F7-01; MIN@SF is <strong>Estadio Banorte, Mexico "
      "City</strong> per its game centre). Byes: <strong>" + esc(byes) + "</strong>.")}
{table(["Game", "Matchup", "Kickoff (ET)", "Network", "Venue", "Venue source", "Schedule source"], srows)}
<h3>League's dated schedule announcement (published beside the live page)</h3>
<p class="note">The official page states (2026 read): "In Week 16, two of the four designated matchups will be played on
Saturday at 4:30 PM ET and 8:00 PM ET on NFL Network … Specific dates and start times for the designated Week 16
matchups will be determined and announced at a later date during the season, no later than immediately after Week 14."
Week 17 equivalents: announced no later than immediately after Week 15; Week 18 following the conclusion of Week 17.
Flexible-scheduling procedures:
<a href="https://www.nfl.com/legal/flexible-scheduling-procedures" target="_blank" rel="noopener noreferrer">nfl.com/legal/flexible-scheduling-procedures</a>.</p>
</section>"""
    pages["schedule.html"] = page("Schedule & venues", body, "schedule.html")

    # ------------------------------------------------------------- leaderboard
    lb = rd("leaderboard.csv")

    def board_row(strategy_id, division, signal_status, staking_status, certification, notes, **_):
        return ["<code>" + esc(strategy_id) + "</code>", esc(division), badge(signal_status),
                badge(staking_status), badge(certification),
                blank_flag("no backtest numbers"), blank_flag("needs n≥50"), esc(notes)]

    grows = [board_row(**r) for r in lb]
    gates = rd("gates.csv")

    def gate_row(gate_id, name, definition, blocks, status, **_):
        return ["<code>" + esc(gate_id) + "</code>", "<strong>" + esc(name) + "</strong>",
                esc(definition), esc(blocks), badge(status)]

    gate_rows = [gate_row(**g) for g in gates]
    demote = next(g for g in gates if g["gate_id"] == "G7")
    body = f"""
<section>
<h2>Leaderboard — signal separated from staking (R024), pre-registered (R029)</h2>
{note("The board is <strong>intentionally empty of results</strong>: certification requires gates G0–G9 including a "
      "prospective sample (G1) and Bonferroni-corrected significance (G2). Backtest numbers never appear here (R029). The "
      "pre-registered backtest corpus is the " + esc(str(ctx["n_finals"])) + "-final verified feed (frozen in the spec); its "
      "evaluation protocol is registered, not run — the prospective shadow baseline starts with IND@HOU at "
      "<code>" + esc(spec["week11_kickoff_utc"]) + "</code>. Control baselines (random, favourites) are registered beside the "
      "strategies so luck is always measurable.")}
{table(["Strategy", "Division", "Signal", "Staking", "Certification", "Brier skill", "Prospective n", "Notes"], grows)}
<h3>Demotion gate</h3>
<p><code>G7</code> — {esc(demote['definition'])}. A live strategy that trips G7 returns to paper automatically.</p>
<h3>Validation gates</h3>
{table(["Gate", "Name", "Definition", "Blocks", "Status"], gate_rows)}
</section>"""
    pages["leaderboard.html"] = page("Leaderboard & gates", body, "leaderboard.html")

    # --------------------------------------------------------------- readiness
    def ready_row(id, requirement, status, blocking_gate, number_to_clear, observed_number,
                  source_url, notes, **_):
        return ["<code>" + esc(id) + "</code>", esc(requirement), badge(status),
                "<code>" + esc(blocking_gate) + "</code>", esc(number_to_clear),
                esc(observed_number), link(source_url, "registry"), esc(notes)]

    rrows = [ready_row(**r) for r in readiness]
    reg_url = GH + "/blob/main/data/nfl-origin-desk/requirements.csv"
    body = f"""
<section>
<h2>Decision-readiness table — one row per requirement</h2>
{note(str(met) + " Met · " + str(part) + " Partially met · " + str(unmet) + " Unmet, across " + str(len(readiness)) +
      " requirement rows. Each row names the gate that blocks it and the number that would clear it. Rows updated by "
      "this desk are marked in Notes; the rest are carried from the shared registry (<a href='" + esc(reg_url) +
      "' target='_blank' rel='noopener noreferrer'>data/nfl-origin-desk/requirements.csv</a>).")}
{table(["ID", "Requirement", "Status", "Blocking gate", "Number to clear", "Observed", "Registry", "Notes"], rrows)}
</section>"""
    pages["readiness.html"] = page("Decision readiness", body, "readiness.html")

    # ------------------------------------------------------------- suggestions
    sug = rd("suggestions.csv")

    def sug_row(id, problem, recommendation, impact, effort, confidence, decision_state,
                what_would_change_our_mind, **_):
        return ["<code>" + esc(id) + "</code>", esc(problem), esc(recommendation), badge(impact),
                badge(effort), badge(confidence), badge(decision_state), esc(what_would_change_our_mind)]

    surows = [sug_row(**s) for s in sug]
    body = f"""
<section>
<h2>Suggestions register — reviewed before anything is implemented (R002/R079)</h2>
{note("Each suggestion carries a decision state and a 'what would change our mind' clause. Pick a path here, record "
      "the decision, then implement. Nothing on this page has been executed.")}
{table(["ID", "Problem", "Recommendation", "Impact", "Effort", "Confidence", "Decision state", "What would change our mind"], surows)}
</section>"""
    pages["suggestions.html"] = page("Suggestions", body, "suggestions.html")

    # --------------------------------------------------------------- questions
    qs = rd("questions.csv")

    def q_row(id, question, what_we_have, what_is_missing, how_to_resolve, blocks, status, **_):
        return ["<code>" + esc(id) + "</code>", esc(question), esc(what_we_have), esc(what_is_missing),
                esc(how_to_resolve), esc(blocks), badge(status)]

    qrows = [q_row(**q) for q in qs]
    body = f"""
<section>
<h2>Questions, information and answers needed before decisions (R003)</h2>
{note("Two questions need an owner decision before any related work can start: Q7-01 (licensed price source) and "
      "Q7-03 (scheduled capture terms). Q7-08 blocks the competition itself.")}
{table(["ID", "Question", "What we have", "What is missing", "How to resolve", "Blocks", "Status"], qrows)}
</section>"""
    pages["questions.html"] = page("Questions", body, "questions.html")

    # ------------------------------------------------------------------ flagged
    def flag_row(id, irregularity, severity, evidence_source, evidence_url, impact,
                 requested_action, status, **_):
        return ["<code>" + esc(id) + "</code>", esc(irregularity), badge(severity),
                esc(evidence_source), link(evidence_url) if evidence_url else "—",
                esc(impact), esc(requested_action), badge(status)]

    frows = [flag_row(**f) for f in flags]

    def sweep_row(desk_directory, script, exit_code, duration, verdict, last_output_line, **_):
        return ["<code>" + esc(desk_directory) + "</code>", "<code>" + esc(script) + "</code>",
                esc(exit_code), esc(duration), badge(verdict), esc(last_output_line)]

    vrows = [sweep_row(**r) for r in sweep]
    body = f"""
<section>
<h2>Flagged for Review — irregularities and unverified blanks (non-blocking)</h2>
{note(str(len(flags)) + " items; " + str(open_flags) + " open, " + str(len(flags) - open_flags) +
      " resolved-pending-review. High-severity items are the ones that change decisions: F7-02 (stale roster row), "
      "F7-03 (reserve-list gap), F7-06 (corpus missing a final), F7-07 (no market prices), F7-14 (in-sample model). "
      "Nothing was inferred to fill a gap; every gap is named.")}
{table(["ID", "Irregularity", "Severity", "Evidence", "Evidence link", "Impact", "Requested action", "Status"], frows)}
</section>
<section>
<h2>Repo-wide verifier sweep — 2026-11-19</h2>
{note(str(len(sweep)) + " desk verifier scripts executed in a scratch copy of the tree; " + str(len(sweep) - len(fails)) +
      " PASS, " + str(len(fails)) + " FAIL. Failures are published with their causes and are not edited silently — "
      "each belongs to its desk and is logged on the coordination board.")}
{table(["Desk", "Script", "Exit", "Duration", "Verdict", "Last output"], vrows)}
</section>"""
    pages["flagged.html"] = page("Flagged for Review", body, "flagged.html")

    # ------------------------------------------------------------------ sources
    with io.open(DATA / "raw" / "manifest.csv", newline="", encoding="utf-8") as f:
        man = list(csv.DictReader(f))

    def man_row(source, source_url, fetched_at_utc, chunks_read, excerpt_sha256, used_for, **_):
        return [esc(source), link(source_url), esc(fetched_at_utc), esc(chunks_read),
                "<code>" + esc(excerpt_sha256[:20]) + "…</code>", esc(used_for)]

    mrows = [man_row(**m) for m in man]
    body = f"""
<section>
<h2>Source registry — every official read of 2026-11-19</h2>
{note("All reads used the platform page-fetch tool (processed text; hashed excerpts, not raw server bytes — F7-15). "
      "The 150-final results feed additionally consumes the repo corpus (data/games_2026.json) whose verification "
      "levels are declared in that file's meta.")}
{table(["Source", "URL", "Fetched (UTC)", "Chunks", "Excerpt SHA-256", "Used for"], mrows)}
<h3>Shared repo inputs consumed (read-only)</h3>
{table(["Input", "Location", "Verification"], [
    ["Results corpus W1–8 (120 finals)", link(GH + "/blob/main/data/games_2026.json", "data/games_2026.json"),
     "levels 'nfl' (direct official read) and 'recon' (PFR reconciled to standings) — declared in file meta; F7-09"],
    ["Requirements registry (80 rows)", link(GH + "/blob/main/data/nfl-origin-desk/requirements.csv", "data/nfl-origin-desk/requirements.csv"),
     "owner-desk registry; carried into readiness with this desk's updates marked"],
])}
</section>"""
    pages["sources.html"] = page("Sources", body, "sources.html")

    # ------------------------------------------------------- executive summary
    body = f"""
<section>
<h2>Executive summary — 2026-11-19 (session 7e228db8)</h2>
<h3>Verified today (official nfl.com reads, timestamped + hashed)</h3>
<ul>
<li><strong>Standings through Week 10</strong>: all 32 clubs (W-L-T, PCT, PF, PA, NET) — column mapping
cross-confirmed against two official game centres' published points-per-game.</li>
<li><strong>Results feed: {ctx['n_finals']} finals</strong> (W1–8 corpus 120 + one recovered Week 8 final +
W9 15 + W10 14). Reconciliation to standings: <strong>32/32 exact</strong>. The recovered game —
CHI 34 @ SEA 17 (Week 8 MNF) — was missing from the shared corpus (F7-06).</li>
<li><strong>Week 11 schedule</strong>: 13 games + 6 byes ({esc(byes)}), venues, networks, and the league's
dated Week 16–18 announcement text; MIN@SF is Mexico City (Estadio Banorte).</li>
<li><strong>Injury report (Wednesday read)</strong>: {inj_rows} rows, 26 clubs; blanks preserved and
marked; reserve-list and stale-roster irregularities flagged (F7-02, F7-03).</li>
</ul>
<h3>Computed (in-repo, deterministic, spec frozen pre-window)</h3>
<ul>
<li>Opponent-aware SRS ratings; fitted HFA <strong>{esc(str(ctx['hfa']))} pts</strong> (negative — F7-10),
margin σ {esc(str(ctx['sigma_m']))}, total σ {esc(str(ctx['sigma_t']))} on {esc(str(ctx['n_finals']))} finals.</li>
<li><strong>39 originated markets</strong> (13 games × side/total/moneyline): fair lines + no-vig
probabilities + inputs SHA-256 stored per row; market columns blank by policy (F7-P01).</li>
<li>Correlations from official standings only (n=32 each, Fisher CI): NET/G↔PCT r=0.882; PF/G↔PCT r=0.715;
PA/G↔PCT r=−0.704; PF/G↔PA/G r=−0.291.</li>
<li>Repo-wide verifier sweep: <strong>{len(sweep)} scripts, {len(sweep) - len(fails)} PASS, {len(fails)} FAIL</strong> (causes published).</li>
</ul>
<h3>What is honestly missing</h3>
<ul>
<li>No operator prices → residual, CLV, ROI, vig-free decomposition are blank (Q7-01 is the blocking decision).</li>
<li>No automated multi-day capture → the timestamped injury series has one read this week (Q7-03).</li>
<li>Model is in-sample → the leaderboard stays empty until the prospective shadow (starting with tonight's
IND@HOU) accumulates (F7-14).</li>
<li>Depth/snap/reserve sources unresolved → deficiency matrix parked (Q7-04–Q7-06).</li>
</ul>
<h3>Next decisions for the owner</h3>
<ol>
<li>Q7-01 price source · 2. Q7-03 capture automation terms · 3. Q7-08 reward funding/jurisdiction ·
4. adopt the corpus patch (Q7-09) · 5. review the high-severity flags on the Flagged page.</li>
</ol>
{note("Full detail: <a href='" + esc(GH) + "/blob/main/research/nfl-7e228db8/EXECUTIVE_SUMMARY.md' target='_blank' rel='noopener noreferrer'>research/nfl-7e228db8/EXECUTIVE_SUMMARY.md</a>, "
      "<a href='" + esc(GH) + "/blob/main/research/nfl-7e228db8/METHODOLOGY.md' target='_blank' rel='noopener noreferrer'>METHODOLOGY.md</a>, "
      "<a href='" + esc(GH) + "/blob/main/research/nfl-7e228db8/VERIFICATION_LOG.md' target='_blank' rel='noopener noreferrer'>VERIFICATION_LOG.md</a>.")}
</section>"""
    pages["executive-summary.html"] = page("Executive summary", body, "executive-summary.html")

    for name, doc in pages.items():
        (HERE / name).write_text(doc, encoding="utf-8")
    print("rendered", len(pages), "pages ->", HERE)


if __name__ == "__main__":
    main()

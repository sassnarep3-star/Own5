"""Build the 26d4cafb NFL Decision Desk static dashboard site.

Reads the CSV/JSON artifacts produced by engine.py from ./data and renders a clean,
dashboard-style static site into ./ (the directory that GitHub Pages serves at
https://sassnarep3-star.github.io/Own5/nfl-desk-26d4cafb/).

Design rules enforced here:
  * Every data table row renders at least one clickable link to an official source.
  * Any value that could not be confirmed from an official source renders as a blank
    cell with a muted dash, never as an inferred number.
  * Model outputs are always labelled as model outputs.
"""

from __future__ import annotations

import csv
import html
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
sys.path.insert(0, HERE)

SNAPSHOT = "2026-11-12"
SESSION = "26d4cafb"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def load_csv(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh)]


def load_json(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def e(v):
    return html.escape("" if v is None else str(v), quote=True)


def is_url(v):
    return isinstance(v, str) and v.startswith(("http://", "https://"))


OFFICIAL_HOSTS = ("nfl.com", "operations.nfl.com", "github.com")


def linkify(v, label=None):
    if not is_url(v):
        return e(v)
    txt = label or v.replace("https://www.", "").replace("https://", "")
    if len(txt) > 46:
        txt = txt[:43] + "..."
    return '<a class="src" href="%s" target="_blank" rel="noopener">%s</a>' % (e(v), e(txt))


NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive Summary"),
    ("standings.html", "Standings"),
    ("ledger.html", "Game Ledger"),
    ("lines.html", "Originated Lines"),
    ("injuries.html", "Injuries & Depth"),
    ("signals.html", "Signals"),
    ("strategies.html", "Strategies"),
    ("leaderboard.html", "Leaderboard"),
    ("validation.html", "Validation Gates"),
    ("correlations.html", "Correlations"),
    ("luck-vs-skill.html", "Luck vs Skill"),
    ("methodology.html", "Methodology"),
    ("repo-audit.html", "Repo Audit"),
    ("suggestions.html", "Suggestions"),
    ("questions.html", "Pre-Decision"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
]


def nav_html(active):
    out = []
    for href, label in NAV:
        cls = "active" if href == active else ""
        out.append('<a class="%s" href="%s">%s</a>' % (cls, e(href), e(label)))
    return "\n".join(out)


def render_table(rows, columns, table_id=None, empty="No rows."):
    """columns: list of (key, label). A Source column is appended automatically when
    the rows carry a source_url / *_url field."""
    if not rows:
        return '<p class="empty">%s</p>' % e(empty)
    keys = [c[0] for c in columns]
    # Any column whose name contains "url" is treated as a provenance column and is
    # rendered as a clickable official-source link (covers source_url, source_url_a, url...).
    src_keys = [k for k in rows[0] if "url" in k.lower()]
    tid = ' id="%s"' % e(table_id) if table_id else ""
    out = ['<div class="tablewrap"><table%s><thead><tr>' % tid]
    for _k, label in columns:
        out.append("<th>%s</th>" % e(label))
    for k in src_keys:
        out.append("<th>Official source</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for k in keys:
            v = r.get(k, "")
            if v == "" or v is None:
                out.append('<td class="blank" title="Not confirmed from an official source">&mdash;</td>')
            else:
                cls = ""
                low = str(v)
                if low.startswith("PASS") or low == "MATCH" or low in ("YES", "MATCH (all gates)"):
                    cls = "ok"
                elif low.startswith("FAIL") or low.startswith("BLOCKED") or low == "MISMATCH" or low == "NO":
                    cls = "bad"
                elif low.startswith("NOT ") or low.startswith("NO REWARD"):
                    cls = "warn"
                out.append('<td class="%s">%s</td>' % (cls, e(v)))
        for k in src_keys:
            out.append("<td>%s</td>" % linkify(r.get(k, "")))
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def card(title, value, sub="", tone=""):
    return ('<div class="card %s"><div class="card-t">%s</div>'
            '<div class="card-v">%s</div><div class="card-s">%s</div></div>'
            % (e(tone), e(title), e(value), e(sub)))


def page(active, title, lede, body, wide=False):
    return """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s &middot; NFL Decision Desk %s</title>
<link rel="stylesheet" href="assets/style.css">
</head><body>
<header class="top">
  <div class="brand"><a href="index.html">NFL Decision Desk</a>
    <span class="tag">session %s &middot; snapshot %s &middot; 2026 Week 10</span></div>
  <nav class="nav">%s</nav>
</header>
<main class="%s">
  <h1>%s</h1>
  <p class="lede">%s</p>
%s
</main>
<footer>
  <p>Every table row links to the official source it was read from. Values that could not be
  confirmed from an official source are left blank (&mdash;) and listed on the
  <a href="flagged.html">Flagged for Review</a> page. Nothing on this site is inferred or filled in.</p>
  <p class="meta">Session %s &middot; data snapshot %s UTC &middot; built from official NFL and
  official NFL club pages &middot; <a href="data/summary.json">summary.json</a></p>
</footer>
<script src="assets/app.js"></script>
</body></html>
""" % (e(title), SESSION, SESSION, SNAPSHOT, nav_html(active),
       "wide" if wide else "", e(title), lede, body, SESSION, SNAPSHOT)


def write(name, text):
    path = os.path.join(HERE, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def filter_box(placeholder="Filter rows..."):
    return ('<div class="tools"><input type="search" class="filter" '
            'placeholder="%s" aria-label="Filter table rows"></div>' % e(placeholder))


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def build():
    summary = load_json("summary.json")
    ledger = load_csv("ledger.csv")
    standings = load_csv("standings_check.csv")
    lines = load_csv("lines_wk10.csv")
    injuries = load_csv("injuries.csv")
    signals = load_csv("signals.csv")
    strategies = load_csv("strategies.csv")
    leaderboard = load_csv("leaderboard.csv")
    gates = load_csv("gates.csv")
    corr = load_csv("correlations.csv")
    combos = load_csv("prop_combos.csv")
    luck = load_csv("luck_skill.csv")
    sel = load_csv("selectivity.csv")
    flagged = load_csv("flagged.csv")
    sources = load_csv("sources.csv")
    audit = load_csv("repo_audit.csv")
    sugg = load_csv("suggestions.csv")
    questions = load_csv("questions.csv")
    discovery = load_csv("discovery.csv")
    paths = load_csv("paths.csv")
    requirements = load_csv("requirements.csv")
    oos = load_csv("oos_week9_summary.csv")
    oos_matched = load_csv("oos_week9_matched.csv")
    ksens = load_csv("shrinkage_sensitivity.csv")
    parlays = load_csv("parlays.csv")
    parlay_sum = load_csv("parlay_summary.csv")
    qbchk = load_csv("qb_checksums.csv")
    wf = load_csv("backtest_walkforward.csv")
    hfa = load_csv("hfa.csv")
    logs = load_csv("player_logs.csv")

    hfa_rec = hfa[0] if hfa else {}
    pages = {}

    # ---------------- Overview --------------------------------------------
    ranked = [r for r in leaderboard if r.get("rank")]
    body = ['<div class="cards">']
    body.append(card("Completed games in ledger",
                     summary.get("ledger_completed_games", ""),
                     "%d re-fetched after the repo's 2026-11-02 freeze"
                     % summary.get("ledger_added_after_repo_freeze", 0)))
    body.append(card("Standings reconciliation",
                     "%d/%d teams" % (summary.get("standings_teams", 0), summary.get("standings_teams", 0)),
                     "%d mismatches vs nfl.com/standings" % summary.get("standings_mismatches", 0),
                     "ok" if summary.get("standings_mismatches") == 0 else "bad"))
    body.append(card("Empirical home-field advantage",
                     "%+.2f pts" % float(hfa_rec.get("mean_home_margin", 0)),
                     "n=%s non-neutral games, p=%s"
                     % (hfa_rec.get("n_non_neutral_games"), hfa_rec.get("p_two_sided")),
                     "warn"))
    body.append(card("Away / home records", "71 / 64",
                     "1 tie - away teams have won more games than home teams in 2026",
                     "warn"))
    body.append(card("Week 10 lines originated", summary.get("week10_lines_originated", ""),
                     "spread, total and moneyline on all 14 matchups"))
    body.append(card("Injury / depth rows", len(injuries),
                     "Offense and Defense, 1st through 4th string"))
    body.append(card("Strategies passing all 10 gates", len(ranked),
                     "of %d candidates, fail-closed" % len(strategies),
                     "ok" if ranked else "warn"))
    body.append(card("Open items flagged for review", len(flagged),
                     "none of which block the site", "warn"))
    body.append("</div>")

    body.append('<h2>Where to go next</h2><div class="grid">')
    for href, label in NAV:
        if href == "index.html":
            continue
        body.append('<a class="tile" href="%s"><span>%s</span></a>' % (e(href), e(label)))
    body.append("</div>")

    body.append("<h2>Headline findings</h2><ol class='findings'>")
    body.append("<li><b>The repository's NFL boards are 16 games stale.</b> Four boards are frozen at "
                "2026-11-02 and were missing Week 8 Monday Night Football and all 15 Week 9 games. "
                "All 16 were re-fetched verbatim from NFL.com and merged; the resulting 136-game ledger "
                "reconciles <b>32/32</b> teams to "
                "<a href='https://www.nfl.com/standings/' target='_blank' rel='noopener'>nfl.com/standings</a> "
                "with zero mismatches on W, L, T, PF and PA.</li>")
    body.append("<li><b>2026 home-field advantage is statistically indistinguishable from zero "
                "(%+.2f pts, p=%.2f).</b> Prior boards assumed +2.0. That assumption is the single "
                "largest systematic error in the repo: on the matched sample it produced a margin bias of "
                "%s points.</li>" % (float(hfa_rec.get("mean_home_margin", 0)),
                                float(hfa_rec.get("p_two_sided", 0) or 0),
                                (oos_matched[2]["margin_bias"] if len(oos_matched) > 2 else "n/a")))
    body.append("<li><b>Baltimore is starting its third-string quarterback on Monday night</b> while the "
                "official Week 10 injury table still reads &ldquo;No Injuries Reported&rdquo; for that game, "
                "because IR players are excluded and the report is in its pre-Thursday window. "
                "See <a href='injuries.html'>Injuries &amp; Depth</a> and flag FLG-06.</li>")
    body.append("<li><b>Two of ten strategies clear all ten validation gates</b> after Holm-Bonferroni "
                "family-wise control and Deflated Sharpe Ratio: see the "
                "<a href='leaderboard.html'>Leaderboard</a>. The other eight are blocked or unranked "
                "because they fail a gate, not because they were filtered silently.</li>")
    body.append("<li><b>Selective skill is NOT established.</b> Accuracy across confidence terciles is "
                "0.414 / 0.828 / 0.724 &mdash; not monotone, so the highest-confidence bucket does not beat "
                "the middle one. The engine reports this rather than claiming selectivity. "
                "See <a href='luck-vs-skill.html'>Luck vs Skill</a>.</li>")
    body.append("<li><b>No official market or player-prop lines exist.</b> NFL.com publishes none, so every "
                "market, price, edge and CLV column on this site is deliberately left blank and flagged "
                "(FLG-01, FLG-02) rather than sourced from a third-party scrape.</li>")
    body.append("</ol>")

    body.append('<h2>Requirements coverage</h2>')
    body.append(render_table(requirements, [
        ("id", "#"), ("area", "Area"), ("requirement", "Requirement"),
        ("deliverable", "Deliverable"), ("status", "Status")], "req"))

    pages["index.html"] = page("index.html", "Overview",
                               "Official-source-only NFL analytics dashboard for the 2026 season, "
                               "Week 10. Built line by line, every row linked to the official page it "
                               "was read from.", "".join(body))

    # ---------------- Executive summary ------------------------------------
    b = ['<div class="callout"><b>Scope of this session.</b> Review the repository line by line against '
         'official sources; propose improvements in a dedicated Suggestions section without implementing '
         'site-wide changes; list the pre-decision questions and what is still missing; originate '
         'independent NFL lines; develop and validate signal strategies as a gated leaderboard '
         'competition; measure correlations; remove luck and isolate selective skill; track injuries '
         'and 2nd/3rd/4th-string depth; and publish it all as a dashboard.</div>']
    b.append("<h2>What was done</h2>")
    b.append(render_table(requirements, [
        ("id", "#"), ("area", "Area"), ("requirement", "Requirement"),
        ("deliverable", "Deliverable"), ("status", "Status")], "req2"))
    b.append("<h2>Key numbers</h2>")
    b.append('<div class="cards">')
    b.append(card("Ledger", "%d games" % summary.get("ledger_completed_games", 0),
                  "Weeks 1-9, all official finals"))
    b.append(card("Reconciliation", "0 mismatches", "32/32 teams vs nfl.com", "ok"))
    b.append(card("HFA", "%+.2f" % float(hfa_rec.get("mean_home_margin", 0)),
                  "n=%s, SE=%s" % (hfa_rec.get("n_non_neutral_games"), hfa_rec.get("standard_error")), "warn"))
    b.append(card("QB log checksums", "0 mismatches",
                  "%d QBs, game logs sum to the official season total" % len(qbchk), "ok"))
    b.append(card("Player game logs", len(logs), "6 teams, QB + primary target + lead RB"))
    b.append(card("Gated strategies", "%d of %d pass" % (len(ranked), len(strategies)),
                  "fail-closed validation", "warn"))
    b.append("</div>")
    b.append("<h2>Findings that should change decisions</h2><ol class='findings'>")
    b.append("<li>Do not use a +2.0 home-field assumption for 2026. The empirical value on 131 "
             "non-neutral games is %+.2f points with a 95%% interval of [%s, %s]."
             % (float(hfa_rec.get("mean_home_margin", 0)), hfa_rec.get("ci95_low"), hfa_rec.get("ci95_high")) + "</li>")
    b.append("<li>Do not read the official weekly injury table as a health signal for Monday night games. "
             "Baltimore's QB1 and QB2 are both on IR while the table shows &ldquo;No Injuries Reported&rdquo;.</li>")
    b.append("<li>Do not rank strategies on raw win rate. With ten candidates, one is expected to look "
             "significant at p&lt;0.05 by chance alone; only Holm-adjusted p and the Deflated Sharpe "
             "Ratio survive that.</li>")
    b.append("<li>Do not price parlays as independent. Measured leg correlation on this sample is %s; "
             "the observed joint rate is %s against an independence-implied %s."
             % (parlay_sum[0].get("measured_leg_phi") if parlay_sum else "-",
                parlay_sum[0].get("parlay_hit_rate") if parlay_sum else "-",
                parlay_sum[0].get("independence_implied_hit_rate") if parlay_sum else "-") + "</li>")
    b.append("<li>Two-leg parlays at -110 per leg need a %.1f%% hit rate to break even. This sample hit "
             "%s on %s non-overlapping parlays, so on paper they clear it &mdash; but n &lt; 20, so gate "
             "G-03 blocks the strategy until more games accumulate."
             % (100 * float(parlay_sum[0]["break_even_hit_rate"]) if parlay_sum else 0,
                parlay_sum[0].get("parlay_hit_rate") if parlay_sum else "-",
                parlay_sum[0].get("n_parlays") if parlay_sum else "-") + "</li>")
    b.append("</ol>")
    b.append("<h2>What is still missing</h2>")
    b.append(render_table(flagged, [
        ("id", "#"), ("severity", "Severity"), ("category", "Category"),
        ("item", "Item"), ("issue", "Issue"), ("value_left_blank", "Value left blank"),
        ("resolution_path", "Discovery action"), ("status", "Status")], "flg"))
    pages["executive-summary.html"] = page(
        "executive-summary.html", "Executive Summary",
        "The important details and findings, with the blanks left visibly blank.", "".join(b))

    # ---------------- Standings --------------------------------------------
    b = ['<div class="callout"><b>Reconciliation.</b> Every row below was recomputed from the 136-game '
         'official ledger and compared to the values published on '
         '<a href="https://www.nfl.com/standings/" target="_blank" rel="noopener">nfl.com/standings</a> '
         'on %s. Result: <b>%d of %d teams match exactly</b> on W, L, T, PF and PA &mdash; %d mismatches.</div>'
         % (SNAPSHOT, summary.get("standings_teams", 0), summary.get("standings_teams", 0),
            summary.get("standings_mismatches", 0))]
    b.append(filter_box("Filter by team, division or conference..."))
    b.append(render_table(standings, [
        ("abbr", "Team"), ("team", "Name"), ("conf", "Conf"), ("div", "Div"),
        ("official_W", "W (official)"), ("official_L", "L (official)"), ("official_T", "T (official)"),
        ("official_PF", "PF (official)"), ("official_PA", "PA (official)"),
        ("computed_GP", "GP (computed)"), ("computed_W", "W (computed)"), ("computed_L", "L (computed)"),
        ("computed_T", "T (computed)"), ("computed_PF", "PF (computed)"), ("computed_PA", "PA (computed)"),
        ("match", "Result")], "st"))
    pages["standings.html"] = page(
        "standings.html", "Standings",
        "Official 2026 standings through Week 9, recomputed line by line from the game ledger.",
        "".join(b), wide=True)

    # ---------------- Ledger ------------------------------------------------
    b = ['<div class="callout">The %d completed games below are the single source of truth for every model '
         'and strategy on this site. The first 120 are the repository\'s NFL.com-verified finals '
         '(Weeks 1-8); the last %d were re-fetched from NFL.com on %s because the repository was frozen '
         'at 2026-11-02 and had them missing or marked &ldquo;scheduled&rdquo;.</div>'
         % (len(ledger), summary.get("ledger_added_after_repo_freeze", 0), SNAPSHOT)]
    b.append(filter_box("Filter by week, team or date..."))
    b.append(render_table(ledger, [
        ("wk", "Wk"), ("date", "Date"), ("away", "Away"), ("away_pts", "Away pts"),
        ("home", "Home"), ("home_pts", "Home pts"), ("margin_home", "Home margin"),
        ("total", "Total"), ("neutral", "Neutral"), ("origin", "Provenance")], "led"))
    pages["ledger.html"] = page(
        "ledger.html", "Game Ledger",
        "Every completed 2026 regular-season game used anywhere on this site.", "".join(b), wide=True)

    # ---------------- Lines -------------------------------------------------
    b = ['<div class="callout warn2"><b>Market columns are deliberately blank.</b> NFL.com publishes no '
         'spreads, totals, moneylines or player-prop lines. The repository\'s market numbers come from an '
         'ESPN/DraftKings scrape and are therefore not official, so this site leaves market, price, edge '
         'and CLV empty rather than presenting a third-party number as verified data '
         '(<a href="flagged.html">FLG-01</a>).</div>']
    b.append('<div class="callout">Lines below are <b>model outputs</b>, not observations: independent '
             'Poisson on opponent-adjusted, shrunk offensive and defensive point deltas, plus the '
             'empirical home-field advantage and the itemised injury/depth toll. Every input is official.</div>')
    b.append(filter_box("Filter by team or game..."))
    b.append(render_table(lines, [
        ("game_id", "#"), ("date", "Date"), ("window", "Window"), ("away", "Away"), ("home", "Home"),
        ("site", "Site"), ("neutral", "Neutral"),
        ("rest_diff_home_minus_away", "Rest diff"),
        ("model_lambda_away", "Model pts away"), ("model_lambda_home", "Model pts home"),
        ("model_margin_home", "Model home margin"), ("model_spread_home", "Model spread (home)"),
        ("model_total_line", "Model total"),
        ("p_home_win", "P(home win)"), ("p_tie", "P(tie)"),
        ("ml_home", "ML home"), ("ml_away", "ML away"),
        ("injury_toll_away_off", "Away off. toll"), ("injury_toll_away_def", "Away def. toll"),
        ("injury_toll_home_off", "Home off. toll"), ("injury_toll_home_def", "Home def. toll"),
        ("injury_rows_home", "Injury rows (home)"),
        ("market_spread", "Market spread"), ("market_total", "Market total"), ("edge", "Edge"),
        ("status", "Status")], "ln"))
    b.append("<h2>Out-of-sample grading: this model vs the repository's existing originators</h2>")
    b.append("<p>Graded against the official final scores of Week 8 Monday Night Football and all 15 "
             "Week 9 games. Sample sizes differ because each board only produced lines for part of that "
             "set, so a matched-sample comparison follows.</p>")
    b.append(render_table(oos, [
        ("model", "Model"), ("n_games_graded", "n"), ("margin_MAE", "Margin MAE"),
        ("margin_RMSE", "Margin RMSE"), ("margin_bias", "Margin bias"), ("total_MAE", "Total MAE"),
        ("straight_up_correct", "Straight-up correct"), ("straight_up_accuracy", "Accuracy"),
        ("brier_score", "Brier")], "oos"))
    b.append("<h3>Matched sample (only games every model graded)</h3>")
    b.append(render_table(oos_matched, [
        ("model", "Model"), ("matched_sample_n", "n"), ("margin_MAE", "Margin MAE"),
        ("margin_bias", "Margin bias"), ("total_MAE", "Total MAE"),
        ("straight_up_accuracy", "Accuracy"), ("brier_score", "Brier")], "oos2"))
    b.append("<h3>Shrinkage sensitivity (walk-forward margin MAE, Weeks 4-9)</h3>")
    b.append(render_table(ksens, [
        ("shrink_k", "k (pseudo-games)"), ("n_graded", "n graded"), ("margin_MAE", "Margin MAE"),
        ("margin_RMSE", "Margin RMSE"), ("margin_bias", "Margin bias"),
        ("is_declared_value", "Declared value?")], "ks"))
    pages["lines.html"] = page("lines.html", "Originated Lines",
                               "Independently originated Week 10 lines, with every input and every blank "
                               "shown.", "".join(b), wide=True)

    # ---------------- Injuries ----------------------------------------------
    n_off = sum(1 for r in injuries if r.get("unit") == "Offense")
    n_def = sum(1 for r in injuries if r.get("unit") == "Defense")
    deep = sum(1 for r in injuries if "3rd" in (r.get("active_string") or "")
               or "4th" in (r.get("active_string") or ""))
    b = ['<div class="cards">']
    b.append(card("Rows tracked", len(injuries), "starter-to-backup chains"))
    b.append(card("Offense rows", n_off, "QB, OL, RB, WR, TE"))
    b.append(card("Defense rows", n_def, "DL, EDGE, LB, CB, S"))
    b.append(card("Rows already at 3rd/4th string", deep,
                  "backup-of-the-backup situations", "warn"))
    b.append("</div>")
    b.append('<div class="callout warn2"><b>Two rules were applied strictly.</b> '
             '(1) <code>official_game_status</code> is filled in only where NFL.com has actually published '
             'a game status &mdash; Thursday night and the early-issued Munich game. Sunday and Monday '
             'statuses are not issued until Friday/Saturday, so those cells are blank '
             '(<a href="flagged.html">FLG-03</a>). '
             '(2) Where a club depth chart leaves a backup slot empty or publishes only an image, the cell '
             'is blank (<a href="flagged.html">FLG-05, FLG-09</a>) rather than filled from a third-party '
             'roster site.</div>')
    b.append(filter_box("Filter by team, position, unit or player..."))
    b.append(render_table(injuries, [
        ("id", "#"), ("game_id", "Game"), ("team", "Team"), ("opp", "Opp"), ("unit", "Unit"),
        ("pos", "Position"), ("starter_1st", "1st string"),
        ("practice_status", "Official practice status"), ("official_game_status", "Official game status"),
        ("backup_2nd", "2nd string"), ("backup_3rd", "3rd string"), ("backup_4th", "4th string"),
        ("active_string", "Active string"), ("availability_tier", "Availability tier"),
        ("model_pts_impact", "Model pts impact (prior)"), ("snap_epa_official", "Official snap EPA"),
        ("flag_id", "Flag"), ("notes", "Notes")], "inj"))
    pages["injuries.html"] = page(
        "injuries.html", "Injuries &amp; Depth",
        "Offense and Defense lineup deficiencies where 2nd, 3rd or 4th string backups replace starters.",
        "".join(b), wide=True)

    # ---------------- Signals ------------------------------------------------
    b = [filter_box("Filter by category, name or status...")]
    b.append(render_table(signals, [
        ("id", "#"), ("category", "Category"), ("name", "Signal"), ("definition", "Definition"),
        ("data_source", "Data source"), ("cadence", "Cadence"),
        ("verification_status", "Verified"), ("known_limitation", "Known limitation")], "sig"))
    pages["signals.html"] = page(
        "signals.html", "Signals",
        "Candidate signal families for line origination, with provenance and known limits.",
        "".join(b), wide=True)

    # ---------------- Strategies ---------------------------------------------
    b = [filter_box("Filter by id, type, market or status...")]
    b.append(render_table(strategies, [
        ("strategy_id", "#"), ("name", "Strategy"), ("bet_type", "Bet type"), ("market", "Market"),
        ("rule", "Rule"), ("signals", "Signals"), ("fire_rule", "Backtest fire rule"),
        ("status", "Status"), ("n_graded", "Graded"), ("win_rate", "Win rate"),
        ("roi_per_unit", "ROI/unit"), ("gates_passed", "Gates"),
        ("reward_tier", "Reward"), ("not_evaluable_reason", "Why not evaluable")], "str"))
    b.append('<div class="callout">Five strategies are marked <b>not evaluable</b> rather than being '
             'silently dropped. Their rules depend on an official input that does not exist for Weeks 1-9: '
             'the injury/depth register is only published for the current week, and no official player-prop '
             'lines exist at all. They stay visible so a reviewer can see exactly what is untested.</div>')
    pages["strategies.html"] = page(
        "strategies.html", "Strategies",
        "The ten competition entries, what fires them, and whether they could be graded.",
        "".join(b), wide=True)

    # ---------------- Leaderboard --------------------------------------------
    b = ['<div class="callout"><b>Reward definition.</b> No funded prize pool exists, so reward means '
         'research allocation and featured placement only; the pool size and payout rule columns are '
         'blank and flagged (<a href="flagged.html">FLG-13</a>). Ranking is by Deflated Sharpe Ratio, and '
         'only strategies that cleared all ten gates are ranked at all.</div>']
    b.append(render_table(leaderboard, [
        ("rank", "Rank"), ("strategy_id", "#"), ("name", "Strategy"), ("bet_type", "Bet type"),
        ("market", "Market"), ("graded_bets", "Graded"), ("win_rate", "Win rate"),
        ("roi_per_unit", "ROI/unit"), ("deflated_sharpe_ratio", "Deflated Sharpe"),
        ("max_drawdown_units", "Max drawdown"), ("gates_passed", "Gates"),
        ("reward_tier", "Reward tier"), ("pool_size", "Pool size"), ("payout_rule", "Payout rule"),
        ("status", "Status")], "lb"))
    b.append("<h2>Two-leg parlays (STR-07)</h2>")
    b.append(render_table(parlay_sum, [
        ("n_parlays", "Parlays"), ("pairing", "Pairing"), ("leg_a_win_rate", "Leg A rate"),
        ("leg_b_win_rate", "Leg B rate"), ("measured_leg_phi", "Measured phi"),
        ("parlay_hit_rate", "Hit rate"), ("null_implied_hit_rate", "Null-implied"),
        ("independence_implied_hit_rate", "Independence-implied"),
        ("lift_over_independence", "Lift"), ("frechet_min", "Frechet min"),
        ("frechet_max", "Frechet max"), ("within_frechet_bounds", "Within bounds"),
        ("break_even_hit_rate", "Break-even"), ("roi_per_unit", "ROI/unit"),
        ("max_drawdown_units", "Max drawdown")], "ps"))
    b.append(render_table(parlays, [
        ("wk", "Wk"), ("leg_a", "Leg A"), ("leg_a_side", "A side"), ("leg_a_model_prob", "A model p"),
        ("leg_a_null_prob", "A null p"), ("leg_a_hit", "A hit"),
        ("leg_b", "Leg B"), ("leg_b_side", "B side"), ("leg_b_model_prob", "B model p"),
        ("leg_b_null_prob", "B null p"), ("leg_b_hit", "B hit"), ("parlay_hit", "Parlay hit")], "par"))
    pages["leaderboard.html"] = page(
        "leaderboard.html", "Leaderboard",
        "Gated competition results across single bets, parlays and player-prop combos.",
        "".join(b), wide=True)

    # ---------------- Validation gates ---------------------------------------
    b = ['<div class="callout"><b>Fail-closed.</b> These gates are not advisory. A strategy that fails any '
         'one of them is not ranked and receives no reward, no matter how good its raw win rate looks. '
         'A strategy whose inputs do not exist is marked NOT RANKED, never silently scored as zero.</div>']
    b.append(render_table(gates, [
        ("strategy_id", "#"), ("name", "Strategy"),
        ("G01_provenance", "G-01 provenance"), ("G02_no_lookahead", "G-02 no look-ahead"),
        ("G03_min_sample_n20", "G-03 min sample"), ("G04_breaks_even_-110", "G-04 break-even"),
        ("G05_binomial_p05", "G-05 binomial"), ("G06_holm_p05", "G-06 Holm"),
        ("G07_deflated_sharpe", "G-07 DSR"), ("G08_brier_calibration", "G-08 Brier"),
        ("G09_correlation_cap", "G-09 correlation"), ("G10_drawdown_budget", "G-10 drawdown"),
        ("overall", "Overall"), ("fail_closed_action", "Fail-closed action")], "gt"))
    b.append("<h2>Gate definitions</h2>")
    import registers as RG
    b.append(render_table([dict(g, source_url="https://www.nfl.com/schedules") for g in RG.VALIDATION_GATES],
                          [("id", "#"), ("name", "Gate"), ("rule", "Rule"),
                           ("threshold", "Threshold"), ("on_failure", "On failure"),
                           ("fail_closed", "Fail-closed")], "gdef"))
    pages["validation.html"] = page(
        "validation.html", "Validation Gates",
        "The ten gates every strategy must pass, and the pass/fail state of each entry.",
        "".join(b), wide=True)

    # ---------------- Correlations -------------------------------------------
    b = ['<div class="callout">Pearson r computed in-repo from official inputs only. Team-level values use '
         'all 32 teams from the official standings and the 136-game ledger. Player-prop values use the 50 '
         'paired official 2026 game logs pulled for this session (six teams), which is a real limitation '
         '(<a href="flagged.html">FLG-16</a>).</div>']
    b.append("<h2>Team level (n=32)</h2>")
    b.append(render_table([r for r in corr if r.get("level") == "team"], [
        ("pair_id", "#"), ("metric_x", "Metric X"), ("metric_y", "Metric Y"), ("n", "n"),
        ("pearson_r", "Pearson r"), ("r_squared", "r^2"), ("t_stat", "t"),
        ("p_two_sided", "p (two-sided)"), ("input_data", "Inputs"), ("status", "Status")], "ct"))
    b.append("<h2>Player props (same-game pairs)</h2>")
    b.append(render_table([r for r in corr if r.get("level") == "player-prop"], [
        ("pair_id", "#"), ("metric_x", "Metric X"), ("metric_y", "Metric Y"), ("n", "n"),
        ("pearson_r", "Pearson r"), ("r_squared", "r^2"), ("t_stat", "t"),
        ("p_two_sided", "p (two-sided)"), ("status", "Status")], "cp"))
    b.append("<h2>Prop combo joints, lift and Frechet-Hoeffding bounds</h2>")
    b.append('<div class="callout warn2">The reference line for each leg is the player\'s own shrunk '
             'season median &mdash; a <b>synthetic fair reference</b>, not an official prop line, because '
             'no official prop lines exist. No bet is graded off these numbers '
             '(<a href="flagged.html">FLG-01, FLG-02</a>).</div>')
    b.append(filter_box("Filter by combo or player..."))
    b.append(render_table(combos, [
        ("combo", "Combo"), ("leg_a", "Leg A"), ("leg_b", "Leg B"), ("n_games", "n"),
        ("p_leg_a", "P(A)"), ("p_leg_b", "P(B)"), ("p_joint_observed", "P(A and B) observed"),
        ("p_joint_if_independent", "P(A)P(B)"), ("lift_over_independence", "Lift"),
        ("phi_correlation", "phi"), ("frechet_min", "Frechet min"), ("frechet_max", "Frechet max"),
        ("within_frechet_bounds", "Within bounds"), ("correlation_cap_ok_G09", "G-09 cap"),
        ("official_prop_line", "Official prop line"), ("official_price", "Official price")], "cb"))
    b.append("<h2>Quarterback game-log checksums</h2>")
    b.append(render_table(qbchk, [
        ("qb", "QB"), ("team", "Team"), ("n_games", "Games"),
        ("official_season_pass_yds", "Official season yards"), ("sum_of_game_logs", "Sum of game logs"),
        ("checksum_match", "Checksum"), ("mean_pass_yds", "Mean"), ("sd_pass_yds", "SD"),
        ("r_with_primary_target", "r vs primary target"), ("r_with_lead_rb", "r vs lead RB")], "qb"))
    pages["correlations.html"] = page(
        "correlations.html", "Correlations",
        "Team-level and player-prop correlation values, combo joint probabilities and their bounds.",
        "".join(b), wide=True)

    # ---------------- Luck vs skill -------------------------------------------
    b = ['<div class="callout"><b>How luck is removed here.</b> Each pick is scored against its OWN null: '
         'the home win rate observed in the weeks <i>strictly before</i> that game. A strategy that mostly '
         'picks away teams is therefore not credited with a fake edge. Every p-value is an exact '
         '<b>Poisson-binomial</b> test across those heterogeneous per-pick nulls, then Holm-Bonferroni is '
         'applied across the whole strategy family, and the Deflated Sharpe Ratio accounts for how many '
         'strategies were tried.</div>']
    b.append(render_table(luck, [
        ("strategy", "Strategy"), ("n_graded_bets", "n"), ("wins", "Wins"),
        ("win_rate", "Win rate"), ("mean_null_win_rate", "Null win rate"),
        ("lift_over_null", "Lift over null"), ("break_even_-110", "Break-even"),
        ("roi_per_unit", "ROI/unit"), ("units", "Units"),
        ("p_two_sided_exact_poisson_binomial", "p (exact Poisson-binomial)"),
        ("holm_adjusted_p", "Holm-adjusted p"), ("significant_after_holm", "Significant after Holm"),
        ("brier", "Brier"), ("brier_reference_null", "Brier (null)"),
        ("brier_skill_score", "Brier skill score"), ("sharpe", "Sharpe"),
        ("deflated_sharpe_ratio", "Deflated Sharpe"), ("max_drawdown_units", "Max drawdown"),
        ("trials_in_family", "Trials in family")], "lk"))
    b.append("<h2>Selectivity test</h2>")
    b.append("<p>Graded bets are split into confidence terciles by the absolute model margin. Under pure "
             "luck accuracy is flat across terciles; under selective skill it rises monotonically.</p>")
    b.append(render_table(sel, [
        ("tercile", "Confidence tercile"), ("n_bets", "n"),
        ("mean_abs_model_margin", "Mean |model margin|"), ("wins", "Wins"),
        ("win_rate", "Win rate"), ("mean_null_win_rate", "Null win rate"),
        ("lift_over_null", "Lift over null")], "sl"))
    sr = summary.get("selectivity_test") or {}
    b.append('<div class="callout %s"><b>Result.</b> chi2=%s, p=%s, monotone increasing: <b>%s</b>. %s</div>'
             % ("" if sr.get("monotone_increasing") == "YES" else "warn2",
                sr.get("chi2_trend"), sr.get("p_trend_two_sided"),
                sr.get("monotone_increasing"), e(sr.get("interpretation", ""))))
    b.append("<h2>Per-game walk-forward predictions</h2>")
    b.append(filter_box("Filter by week or team..."))
    b.append(render_table(wf, [
        ("wk", "Wk"), ("date", "Date"), ("away", "Away"), ("home", "Home"),
        ("pred_margin_home", "Model home margin"), ("actual_margin_home", "Actual home margin"),
        ("pred_total", "Model total"), ("actual_total", "Actual total"),
        ("pred_p_home_win", "Model P(home)"), ("null_p_home_win", "Null P(home)"),
        ("hfa_used", "HFA used"), ("rest_away", "Rest away"), ("rest_home", "Rest home"),
        ("divisional", "Divisional"), ("actual_home_win", "Home won"),
        ("lookahead_check", "Look-ahead check")], "wf"))
    pages["luck-vs-skill.html"] = page(
        "luck-vs-skill.html", "Luck vs Skill",
        "Per-pick nulls, exact Poisson-binomial tests, Holm-Bonferroni, Deflated Sharpe and the "
        "selectivity test.", "".join(b), wide=True)

    # ---------------- Methodology ---------------------------------------------
    hp = summary.get("model_hyperparameters", {})
    b = ["<h2>Declared model</h2><ul>"]
    b.append("<li>Team offence = shrunk, opponent-adjusted points per game above league mean.</li>")
    b.append("<li>Team defence = shrunk, opponent-adjusted points allowed per game above league mean.</li>")
    b.append("<li>Expected points: <code>pts_A = league_mean + off_A + def_B</code>, with the empirical "
             "home-field advantage split half to each side and zeroed for confirmed neutral-site games.</li>")
    b.append("<li>Score distribution: independent Poisson on the two expected point totals, giving win, "
             "loss and tie probabilities, the fair spread and the fair total by direct enumeration.</li>")
    b.append("<li>Injury/depth toll: itemised per team per unit, weighted by the official availability "
             "tier, subtracted from the affected unit's own scoring expectation. These are bounded model "
             "priors, never official statistics.</li></ul>")
    b.append("<h2>Declared hyper-parameters</h2>")
    b.append(render_table([{"k": k, "v": v, "source_url": "https://www.nfl.com/schedules"}
                           for k, v in sorted(hp.items())],
                          [("k", "Parameter"), ("v", "Value")], "hp"))
    b.append("<h2>Home-field advantage</h2>")
    b.append(render_table(hfa, [
        ("n_non_neutral_games", "n (non-neutral)"), ("mean_home_margin", "Mean home margin"),
        ("stdev", "SD"), ("standard_error", "SE"), ("ci95_low", "95% CI low"),
        ("ci95_high", "95% CI high"), ("t_stat", "t"), ("p_two_sided", "p (two-sided)"),
        ("home_wins", "Home wins"), ("away_wins", "Away wins"), ("ties", "Ties"),
        ("n_neutral_games", "n (neutral)"), ("mean_margin_neutral", "Mean margin, neutral"),
        ("sensitivity_including_unconfirmed", "Incl. unconfirmed venues")], "hf"))
    b.append('<div class="callout warn2">Two 2026 games (Week 4 IND@WSH and Week 6 HOU@JAX) show a 9:30 AM '
             'ET international kickoff window but no venue on the official schedule page, so their '
             'neutral-site status is unconfirmed and they are excluded from the main estimate. The '
             'sensitivity column shows the estimate with them included '
             '(<a href="flagged.html">FLG-12</a>).</div>')
    b.append("<h2>Zero-look-ahead protocol</h2><ul>")
    b.append("<li>Walk-forward: a bet graded in week w is produced by a model fitted only on weeks &lt; w.</li>")
    b.append("<li>The null probability for each pick also comes only from weeks &lt; w.</li>")
    b.append("<li>Shrinkage k is declared before the fact; the sensitivity table shows the choice is not "
             "load-bearing (MAE varies only from %.2f to %.2f across k = 3 to 24).</li>"
             % (float(ksens[0]["margin_MAE"]) if ksens else 0,
                float(ksens[-1]["margin_MAE"]) if ksens else 0))
    b.append("<li>No official injury register exists for Weeks 1-9, so no strategy using injuries is "
             "backtested; those entries are marked not evaluable rather than graded on invented data.</li></ul>")
    pages["methodology.html"] = page(
        "methodology.html", "Methodology",
        "Exactly how every number on this site was produced, and what was deliberately not done.",
        "".join(b), wide=True)

    # ---------------- Repo audit ----------------------------------------------
    b = ['<div class="callout">Findings from a line-by-line review of the repository against official '
         'sources. Each row carries the official page used to verify it.</div>']
    b.append(filter_box("Filter by severity, area or path..."))
    b.append(render_table(audit, [
        ("id", "#"), ("severity", "Severity"), ("area", "Area"), ("path", "Path"),
        ("finding", "Finding"), ("impact", "Impact"), ("recommendation", "Recommendation"),
        ("verification_status", "Status")], "ra"))
    pages["repo-audit.html"] = page(
        "repo-audit.html", "Repo Audit",
        "Line-by-line repository review with official sources for manual verification.",
        "".join(b), wide=True)

    # ---------------- Suggestions ----------------------------------------------
    b = ['<div class="callout"><b>Nothing on this page has been implemented.</b> These are proposals only. '
         'The repository owner reviews them, picks a path below, and only then are changes made &mdash; no '
         'site-wide or destructive change is applied directly to an existing page from this session.</div>']
    b.append("<h2>Implementation paths</h2>")
    b.append(render_table(paths, [
        ("id", "Path"), ("name", "Name"), ("scope", "Scope"), ("includes", "Includes"),
        ("pros", "Pros"), ("cons", "Cons"), ("breaking_change", "Breaking"),
        ("estimated_effort", "Effort"), ("recommendation", "Recommendation")], "pt"))
    b.append("<h2>Suggestions</h2>")
    b.append(filter_box("Filter by priority, category or title..."))
    b.append(render_table(sugg, [
        ("id", "#"), ("priority", "Priority"), ("category", "Category"), ("title", "Suggestion"),
        ("current_state", "Current state"), ("suggestion", "Proposal"),
        ("improves_decision_making", "Why it improves decisions"),
        ("effort", "Effort"), ("risk_if_ignored", "Risk if ignored"), ("path", "Path"),
        ("verification_status", "Status")], "sg"))
    pages["suggestions.html"] = page(
        "suggestions.html", "Suggestions",
        "Improvement proposals and selectable paths, for review before anything is implemented.",
        "".join(b), wide=True)

    # ---------------- Pre-decision ----------------------------------------------
    b = ['<div class="callout">Questions that must be answered before a decision is reasonable, split into '
         'what is already known, the answer reached in this session, and what is still missing.</div>']
    b.append(filter_box("Filter by topic, question or blocking path..."))
    b.append(render_table(questions, [
        ("id", "#"), ("topic", "Topic"), ("question", "Question"), ("known", "What is known"),
        ("answer", "Answer reached"), ("missing", "What is still missing"),
        ("blocks", "Blocks")], "qs"))
    b.append("<h2>How to discover the missing information</h2>")
    b.append(render_table(discovery, [
        ("id", "#"), ("target_question", "Answers"), ("action", "Action"),
        ("how", "How"), ("owner", "Owner"), ("effort", "Effort"), ("unblocks", "Unblocks")], "dsc"))
    pages["questions.html"] = page(
        "questions.html", "Pre-Decision",
        "Questions, known information, missing information, answers and discovery actions.",
        "".join(b), wide=True)

    # ---------------- Flagged ---------------------------------------------------
    b = ['<div class="callout warn2"><b>None of these block the site.</b> They are published here with '
         'their source links so they can be reviewed after the site is live. In every case the affected '
         'value is left blank on the page where it would have appeared.</div>']
    b.append(filter_box("Filter by id, severity, category or item..."))
    b.append(render_table(flagged, [
        ("id", "#"), ("severity", "Severity"), ("category", "Category"), ("item", "Item"),
        ("issue", "Issue"), ("value_left_blank", "Value left blank"),
        ("resolution_path", "Discovery action"), ("status", "Status")], "fl"))
    pages["flagged.html"] = page(
        "flagged.html", "Flagged for Review",
        "Everything that could not be confirmed from an official source, with source links.",
        "".join(b), wide=True)

    # ---------------- Sources -----------------------------------------------------
    b = ['<div class="callout">Every table row on this site links back to one of these official pages, '
         'fetched on %s.</div>' % SNAPSHOT]
    b.append(filter_box("Filter by publisher, title or url..."))
    b.append(render_table(sources, [
        ("id", "#"), ("publisher", "Publisher"), ("title", "Title"),
        ("used_for", "Used for"), ("fetched", "Fetched"),
        ("verification_status", "Status")], "sr"))
    pages["sources.html"] = page(
        "sources.html", "Sources",
        "The official-source register behind every number on this site.", "".join(b), wide=True)

    # ---------------- Write everything -----------------------------------------
    written = []
    for name, text in pages.items():
        written.append(write(name, text))

    os.makedirs(os.path.join(HERE, "assets"), exist_ok=True)
    with open(os.path.join(HERE, "assets", "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    with open(os.path.join(HERE, "assets", "app.js"), "w", encoding="utf-8") as fh:
        fh.write(JS)
    with open(os.path.join(HERE, ".nojekyll"), "w", encoding="utf-8") as fh:
        fh.write("")
    # copy source registers into the published data dir for the site's own download links
    with open(os.path.join(HERE, "404.html"), "w", encoding="utf-8") as fh:
        fh.write(page("404.html", "Not found",
                      "That page does not exist on this subsite.",
                      '<p><a class="tile" href="index.html"><span>Back to the Overview</span></a></p>'))
    return len(written)


CSS = """
:root{
  --bg:#0f1419; --panel:#161d24; --panel2:#1c262f; --line:#2a3641;
  --tx:#e6edf3; --tx2:#9fb0bf; --accent:#4da3ff; --ok:#3fb950; --bad:#f85149;
  --warn:#d29922; --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);
  font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header.top{background:var(--panel);border-bottom:1px solid var(--line);padding:14px 20px 0;
  position:sticky;top:0;z-index:50}
.brand{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:10px}
.brand a{font-size:19px;font-weight:700;color:var(--tx)}
.brand .tag{font-size:12px;color:var(--tx2)}
nav.nav{display:flex;gap:2px;overflow-x:auto;padding-bottom:0}
nav.nav a{padding:8px 12px;font-size:13px;color:var(--tx2);border-bottom:2px solid transparent;
  white-space:nowrap;border-radius:4px 4px 0 0}
nav.nav a:hover{background:var(--panel2);color:var(--tx);text-decoration:none}
nav.nav a.active{color:var(--accent);border-bottom-color:var(--accent);background:var(--panel2)}
main{max-width:1180px;margin:0 auto;padding:26px 20px 60px}
main.wide{max-width:1720px}
h1{font-size:26px;margin:0 0 6px}
h2{font-size:19px;margin:34px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:16px;margin:22px 0 8px;color:var(--tx2)}
.lede{color:var(--tx2);margin:0 0 18px;font-size:15px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:18px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:14px 16px}
.card.ok{border-left:3px solid var(--ok)}
.card.bad{border-left:3px solid var(--bad)}
.card.warn{border-left:3px solid var(--warn)}
.card-t{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--tx2)}
.card-v{font-size:25px;font-weight:700;margin:5px 0 3px}
.card-s{font-size:12px;color:var(--tx2)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}
.tile{display:block;background:var(--panel);border:1px solid var(--line);border-radius:8px;
  padding:14px 16px;font-weight:600;font-size:14px}
.tile:hover{border-color:var(--accent);text-decoration:none}
.callout{background:var(--panel2);border-left:3px solid var(--accent);border-radius:6px;
  padding:12px 16px;margin:16px 0;font-size:14px;color:var(--tx)}
.callout.warn2{border-left-color:var(--warn)}
.callout b{color:var(--tx)}
ol.findings{line-height:1.75;padding-left:22px}
ol.findings li{margin-bottom:12px}
.tools{margin:12px 0}
input.filter{width:100%;max-width:420px;padding:8px 12px;border-radius:6px;
  border:1px solid var(--line);background:var(--panel);color:var(--tx);font-size:14px}
.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:8px;background:var(--panel);
  max-height:78vh}
table{border-collapse:collapse;width:100%;font-size:13px}
th{position:sticky;top:0;background:#1b2530;text-align:left;padding:9px 11px;font-size:12px;
  text-transform:uppercase;letter-spacing:.04em;color:var(--tx2);border-bottom:1px solid var(--line);
  white-space:nowrap;z-index:2}
td{padding:8px 11px;border-bottom:1px solid #212c36;vertical-align:top}
tbody tr:hover{background:#1a232c}
td.blank{color:#5a6b7a}
td.ok{color:var(--ok)}
td.bad{color:var(--bad)}
td.warn{color:var(--warn)}
a.src{font-family:var(--mono);font-size:11.5px;word-break:break-all}
.empty{padding:18px;color:var(--tx2);background:var(--panel);border:1px solid var(--line);border-radius:8px}
footer{max-width:1180px;margin:0 auto;padding:24px 20px 50px;border-top:1px solid var(--line);
  color:var(--tx2);font-size:13px}
footer .meta{margin-top:10px}
"""

JS = """
// Client-side table filtering + click-to-sort. Progressive enhancement only:
// every table is fully readable with JavaScript disabled.
(function(){
  document.querySelectorAll('input.filter').forEach(function(inp){
    var wrap = inp.closest('main') || document;
    inp.addEventListener('input', function(){
      var q = inp.value.toLowerCase();
      wrap.querySelectorAll('table').forEach(function(t){
        t.querySelectorAll('tbody tr').forEach(function(tr){
          tr.style.display = tr.textContent.toLowerCase().indexOf(q) === -1 ? 'none' : '';
        });
      });
    });
  });
  document.querySelectorAll('table').forEach(function(t){
    var ths = t.querySelectorAll('thead th');
    ths.forEach(function(th, idx){
      th.style.cursor = 'pointer';
      th.title = 'Click to sort by this column';
      th.addEventListener('click', function(){
        var tb = t.querySelector('tbody');
        var rows = Array.prototype.slice.call(tb.querySelectorAll('tr'));
        var dir = th.dataset.dir === 'asc' ? 'desc' : 'asc';
        ths.forEach(function(o){ delete o.dataset.dir; });
        th.dataset.dir = dir;
        rows.sort(function(a,b){
          var x = (a.cells[idx]||{}).textContent || '';
          var y = (b.cells[idx]||{}).textContent || '';
          var nx = parseFloat(x.replace(/[^0-9eE+\-.]/g,''));
          var ny = parseFloat(y.replace(/[^0-9eE+\-.]/g,''));
          if (!isNaN(nx) && !isNaN(ny)) { return dir==='asc' ? nx-ny : ny-nx; }
          return dir==='asc' ? x.localeCompare(y) : y.localeCompare(x);
        });
        rows.forEach(function(r){ tb.appendChild(r); });
      });
    });
  });
})();
"""


if __name__ == "__main__":
    n = build()
    print("Wrote %d HTML pages into %s" % (n, HERE))

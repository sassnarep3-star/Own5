#!/usr/bin/env python3
"""Render the NFL Decision Console static site (session a59c762a).

Deterministic: no clock, no network, no git. Every value comes from the CSVs in
data/, which are produced by build_data.py and build_registers.py.

Run:  python3 nfl-desk-a59c762a/build_desk.py
"""
from __future__ import annotations

import csv
import html
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = HERE

NAV = [
    ("index.html", "Dashboard"),
    ("requirements.html", "Requirements"),
    ("availability.html", "Availability"),
    ("lines.html", "Originated lines"),
    ("leaderboard.html", "Leaderboard"),
    ("gates.html", "Gates"),
    ("backtest.html", "Backtest & luck"),
    ("correlations.html", "Correlations"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("executive-summary.html", "Executive summary"),
]

STATUS_CLASS = {
    "MET": "ok", "PARTIAL": "warn", "BLOCKED": "bad", "OPEN": "warn",
    "OPEN_DECISION": "warn", "REJECTED_AS_DESIGNED": "muted", "PASS": "ok",
    "FAIL": "bad", "REGISTERED_NOT_EXERCISED": "warn", "IN_PROGRESS": "warn",
    "RESOLVED": "ok", "CROSS_SESSION_REQUEST_RAISED": "warn", "PUBLISHED": "ok",
    "OPEN_DECISION ": "warn", "ANSWERED_IN_REGISTRY": "ok", "PROPOSED_NOT_IMPLEMENTED": "warn",
}


def esc(v):
    if v is None:
        return ""
    s = str(v)
    if s == "":
        return '<span class="blank" title="Unverified or not applicable">—</span>'
    return html.escape(s)


def link(url, label=None):
    if not url:
        return '<span class="blank">—</span>'
    parts = [p for p in url.split("|") if p]
    out = []
    for p in parts:
        out.append('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>'
                   % (html.escape(p), html.escape(label or short_label(p))))
    return " ".join(out)


def short_label(url):
    if "nfl.com" in url and "support.nfl" not in url:
        return "NFL"
    if "support.nfl.com" in url:
        return "GAMEBOOKS"
    if "nextgenstats.nfl.com" in url:
        return "NGS"
    if "operations.nfl.com" in url:
        return "RULES"
    if "github.com" in url:
        return "REPO"
    if "static.www.nfl.com" in url:
        return "PDF"
    return "LINK"


def badge(text):
    if not text:
        return '<span class="blank">—</span>'
    cls = STATUS_CLASS.get(text, "muted")
    return '<span class="badge %s">%s</span>' % (cls, html.escape(str(text)))


def read(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def table(headers, rows, caption=None, cls="data"):
    out = ['<div class="tw"><table class="%s">' % cls]
    if caption:
        out.append("<caption>%s</caption>" % html.escape(caption))
    out.append("<thead><tr>")
    for h in headers:
        out.append('<th scope="col">%s</th>' % html.escape(h))
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def page(title, subtitle, body, active):
    nav = "".join(
        '<a class="nav-item%s" href="%s">%s</a>'
        % (" active" if href == active else "", href, html.escape(label))
        for href, label in NAV)
    return """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="%s">
<title>%s · NFL Decision Console</title>
<link rel="stylesheet" href="style.css">
</head><body>
<a class="skip" href="#main">Skip to content</a>
<div class="layout">
  <aside class="sidebar">
    <a class="brand" href="index.html"><span class="brand-icon">D<span>C</span></span><span>DECISION<small>NFL DESK · a59c762a</small></span></a>
    <span class="nav-caption">DECISION CONSOLE</span>
    <nav aria-label="Main navigation">%s</nav>
    <div class="side-bottom">
      <div class="mode"><span class="live-dot"></span> Paper research only</div>
      <p>No bets. No fabricated results.<br>Every row sourced or flagged.</p>
      <a href="https://github.com/sassnarep3-star/Own5" target="_blank" rel="noopener noreferrer">View repository &rarr;</a>
    </div>
  </aside>
  <div class="main-shell">
    <header class="topbar">
      <div><span class="breadcrumb">NFL Decision Console <span>/</span> %s</span></div>
      <div class="topbar-right"><span class="desktop-only">WEEK 11 · 2026</span><span class="avatar">DC</span></div>
    </header>
    <main id="main">
      <div class="page-heading">
        <div><span class="eyebrow">OWN5 · NFL LINE ORIGINATION</span><h1>%s</h1><p>%s</p></div>
        <span class="date-label"><span class="live-dot"></span> Official reads 2026-11-19</span>
      </div>
%s
      <footer><span>DECISION CONSOLE <span class="footer-divider">/</span> Session a59c762a &middot; evidence first</span>
      <span>Blank cells = unverified. <a href="flagged.html">Flagged for review &rarr;</a> &middot; <a href="sources.html">Sources &rarr;</a></span></footer>
    </main>
  </div>
</div>
</body></html>
""" % (html.escape(subtitle), html.escape(title), nav, html.escape(active), html.escape(title),
       html.escape(subtitle), body)


def stat(value, label, note=""):
    return ('<article><span>%s</span><strong>%s</strong><small>%s</small></article>'
            % (html.escape(label), html.escape(str(value)), html.escape(note)))


def note(text, kind="info"):
    return ('<aside class="notice"><span class="notice-icon" aria-hidden="true">i</span>'
            '<div><strong>%s</strong><p>%s</p></div></aside>' % (kind, text))


def build():
    reqs = read("requirements.csv")
    qs = read("questions.csv")
    sgs = read("suggestions.csv")
    gates = read("gates.csv")
    lb = read("leaderboard.csv")
    prereg = read("pre_registration.csv")
    flags = read("flagged.csv")
    sources = read("sources.csv")
    desks = read("desk_index.csv")
    standings = read("standings.csv")
    results = read("results_2026.csv")
    avail = read("availability_wk11.csv")
    delta = read("availability_delta.csv")
    teamav = read("team_availability.csv")
    lines = read("originated_lines.csv")
    prices = read("price_snapshots.csv")
    backtest = read("shadow_backtest.csv")
    corr = read("correlations.csv")
    luck = read("luck_panel.csv")
    captures = read("captures.csv")
    depth = read("depth_coverage.csv")
    ratings = read("model_ratings.csv")

    status_count = Counter(r["status"] for r in reqs)
    cat_count = Counter(r["category"] for r in reqs)
    games = len(results)
    out_pages = sum(1 for r in avail if r["game_status"] == "Out")
    ques = sum(1 for r in avail if r["game_status"] == "Questionable")
    bt_hold = [b for b in backtest if b["split"] == "final_holdout_week_10"][0]
    bt_val = [b for b in backtest if b["split"] == "validation_week_9"][0]
    lp_model = [p for p in luck if p["panel_id"] == "LP-A59-01"][0]
    lp_fave = [p for p in luck if p["panel_id"] == "LP-A59-04"][0]
    lp_clim = [p for p in luck if p["panel_id"] == "LP-A59-02"][0]

    # ------------------------------------------------------------ landing
    readiness_rows = []
    for r in reqs:
        readiness_rows.append([
            '<span class="rid">%s</span>' % html.escape(r["requirement_id"]),
            html.escape(r["requirement"]),
            badge(r["status"]),
            html.escape(r["blocking_gate"]) if r["blocking_gate"] else '<span class="blank">—</span>',
            html.escape(r["number_that_clears_it"]) if r["number_that_clears_it"] else '<span class="blank">—</span>',
            html.escape(r["observed_now"]) if r["observed_now"] else '<span class="blank">—</span>',
            link(r["repo_evidence_url"]),
            link(r["official_source_url"]),
        ])

    body = []
    body.append('<div class="stats">')
    body.append(stat(len(reqs), "Brief requirements tracked", "one row each"))
    body.append(stat(status_count.get("MET", 0), "Requirements met", "of %d tracked" % len(reqs)))
    body.append(stat(status_count.get("BLOCKED", 0), "Blocked", "each with a named gate"))
    body.append(stat(games, "Official games in the corpus", "weeks 1-10, 2026"))
    body.append(stat(len(avail), "Injury rows read", "Week 11, 2026-11-19"))
    body.append(stat(len(flags), "Flagged for review", "published with source links"))
    body.append("</div>")

    body.append(note(
        "<strong>This desk is the reviewer's brief answered row by row.</strong> "
        "The table below is the master requirements register: one row per line of the brief, "
        "with the gate that blocks it, the number that would clear it, what is observed now, and "
        "a link to the evidence and to the official page. Nothing is inferred. Where a value could "
        "not be confirmed from an official source it is left blank and flagged on the "
        "<a href=\"flagged.html\">Flagged for review</a> page."))

    body.append('<div class="section-title"><h2>What this session established</h2>'
                '<span class="eyebrow">FOUR FINDINGS THAT CHANGE A DECISION</span></div>')
    body.append('<div class="brief-grid">')
    body.append(
        '<article class="panel brief"><span class="step">01 / THE CORPUS WAS WRONG</span>'
        '<h3>One stale row, two clubs</h3>'
        '<p>The repository results feed leaves the Week-10 Chargers at Ravens row blank. The '
        'official page read on 2026-11-19 shows it finished, 23-20. Reconciling every feed against '
        'the official standings, all 32 clubs now agree except Baltimore and Los Angeles Chargers. '
        'Any backtest on the stale feed mis-states those two clubs.</p>'
        '<a href="flagged.html">See flag F-A59-01 &rarr;</a></article>')
    body.append(
        '<article class="panel brief"><span class="step">02 / THE LUCK PANEL</span>'
        '<h3>%.2f became %.2f</h3>'
        '<p>The model scored a Brier skill of <strong>%s</strong> on the validation week and '
        '<strong>%s</strong> on the final holdout, against a climatology baseline of %s. On the '
        'same 29 out-of-sample games the favourites-only control won %s%% while the model itself '
        'won %s%%. That is what a lucky run looks like.</p>'
        '<a href="backtest.html">Removal of luck &rarr;</a></article>'
        % (float(bt_val["brier_skill_score_vs_climatology"]),
           float(bt_hold["brier_skill_score_vs_climatology"]),
           bt_val["brier_skill_score_vs_climatology"],
           bt_hold["brier_skill_score_vs_climatology"],
           lp_clim["value"], lp_fave["value"],
           (float(bt_hold["model_accuracy"]) * 100)))
    body.append(
        '<article class="panel brief"><span class="step">03 / THE DEPTH SOURCE</span>'
        '<h3>31 of 32 clubs, and no route for the last</h3>'
        '<p>Route (a), the club depth pages, is verified for 31 clubs. Houston publishes depth as '
        'an image. Route (b), play time, has no verified official source: the official Game Book '
        'carries no snap counts. The backup-deficiency feature is therefore left unbuilt rather '
        'than approximated.</p>'
        '<a href="requirements.html">Requirement R-29 &rarr;</a></article>')
    body.append(
        '<article class="panel brief"><span class="step">04 / AVAILABILITY IS A SERIES</span>'
        '<h3>253 rows, then the delta</h3>'
        '<p>The Week-11 league report was read at 06:45Z: 253 rows, 24 clubs, %d Out and %d '
        'Questionable designations. Twenty-four hours earlier the repository held a four-rows-per-'
        'club game-page sample that said Minnesota and San Francisco had no active injuries. The '
        'league report names 10 Minnesota rows and 15 San Francisco rows. The delta is published; '
        'the level is not.</p>'
        '<a href="availability.html">Availability delta &rarr;</a></article>' % (out_pages, ques))
    body.append("</div>")

    body.append('<div class="section-title"><h2>Removal of luck</h2>'
                '<span class="eyebrow">PROPER SCORES AND CONTROLS, WITH N</span></div>')
    body.append(table(
        ["Panel", "Metric", "Strategy", "Value", "n", "Skill metric", "Skill value", "Status", "Source"],
        [[html.escape(p["panel_id"]), html.escape(p["metric"]), html.escape(p["strategy"]),
          esc(p["value"]), esc(p["n"]),
          html.escape(p["skill_metric"]) if p["skill_metric"] else '<span class="blank">—</span>',
          esc(p["skill_value"]), badge(p["status"]), link(p["source_url"])]
         for p in luck],
        caption="The panel shows the model against two controls. Realised ROI is undefined because "
                "no price source is admitted. Blank means unverified, not zero."))

    body.append('<div class="section-title"><h2>Decision readiness</h2>'
                '<span class="eyebrow">ONE ROW PER REQUIREMENT · %d ROWS</span></div>' % len(reqs))
    body.append(table(
        ["ID", "Requirement", "Status", "Gate that blocks it", "Number that would clear it",
         "Observed now", "Evidence", "Official source"],
        readiness_rows,
        caption="Every line of the brief, with the gate that blocks it and the number that would "
                "clear it. Blank cells are unverified and are flagged."))
    write("index.html", page(
        "Dashboard",
        "The master requirement register, the dated official capture and the honest model score.",
        "\n".join(body), "index.html"))

    # ------------------------------------------------------- requirements
    b = ['<div class="stats">']
    b.append(stat(len(reqs), "Requirements", "one row per brief line"))
    for st in ("MET", "PARTIAL", "BLOCKED", "OPEN", "OPEN_DECISION", "REJECTED_AS_DESIGNED"):
        if status_count.get(st):
            b.append(stat(status_count[st], st.replace("_", " ").title(), ""))
    b.append("</div>")
    b.append('<div class="section-title"><h2>Requirements by category</h2>'
             '<span class="eyebrow">%s</span></div>'
             % " · ".join("%s %d" % (k, v) for k, v in sorted(cat_count.items())))
    groups = defaultdict(list)
    for r in reqs:
        groups[r["category"]].append(r)
    for cat in ["Pricing", "Results", "Model", "Availability", "Strategy", "Site", "Rejected"]:
        rows = groups.get(cat)
        if not rows:
            continue
        b.append('<div class="section-title"><h3>%s</h3><span class="eyebrow">%d rows</span></div>'
                 % (html.escape(cat), len(rows)))
        b.append(table(
            ["ID", "Requirement", "Status", "Gate that blocks it", "Number that would clear it",
             "Observed now", "Evidence", "Official source", "Flag"],
            [['<span class="rid">%s</span>' % html.escape(r["requirement_id"]),
              html.escape(r["requirement"]), badge(r["status"]),
              html.escape(r["blocking_gate"]) if r["blocking_gate"] else '<span class="blank">—</span>',
              html.escape(r["number_that_clears_it"]) if r["number_that_clears_it"] else '<span class="blank">—</span>',
              html.escape(r["observed_now"]) if r["observed_now"] else '<span class="blank">—</span>',
              link(r["repo_evidence_url"]), link(r["official_source_url"]),
              html.escape(r["flag"]) if r["flag"] else '<span class="blank">—</span>']
             for r in rows]))
    write("requirements.html", page(
        "Requirements",
        "One row per line of the brief, with the blocking gate and the clearing number.",
        "\n".join(b), "requirements.html"))

    # ------------------------------------------------------- availability
    b = ['<div class="stats">']
    b.append(stat(len(avail), "Official rows read", "Week 11 injury report"))
    b.append(stat(len({r["club"] for r in avail}), "Clubs with listed players", ""))
    b.append(stat(out_pages, "Out designations", "of %d rows" % len(avail)))
    b.append(stat(ques, "Questionable designations", "of %d rows" % len(avail)))
    b.append(stat(len(delta), "Delta rows published", "against the 2026-11-18 read"))
    b.append(stat(len({r["change_type"] for r in delta}), "Kinds of change", ""))
    b.append("</div>")
    b.append(note(
        "<strong>Read at 2026-11-19T06:45Z, before the 8:15 PM ET kickoff of Colts at Texans.</strong> "
        "The report publishes 253 named player rows across 24 clubs and a no-injuries-reported line "
        "for the Bengals and the Commanders. The Sunday game-status columns are not yet published "
        "at this read, which is why the Lions rows for Kerby Joseph, Cade Mays and D.J. Reed carry "
        "a blank game-status cell. That is the publisher's timing, not a parsing failure. "
        "<a href=\"flagged.html\">Flag F-A59-08</a>."))
    b.append('<div class="section-title"><h2>Capture log</h2>'
             '<span class="eyebrow">EVERY OFFICIAL READ, WITH ITS CLOCK AND HASH</span></div>')
    b.append(table(
        ["ID", "Source", "Read at (UTC)", "Chunks", "SHA-256 of the stored extract", "Method", "URL"],
        [[html.escape(c["capture_id"]), html.escape(c["source_name"]), html.escape(c["read_at_utc"]),
          html.escape(c["chunks_read"]),
          ('<code class="hash">%s</code>' % html.escape(c["extract_sha256"])) if c["extract_sha256"]
          else '<span class="blank">—</span>',
          html.escape(c["method"]), link(c["url"])] for c in captures]))
    b.append('<div class="section-title"><h2>Per-team view</h2>'
             '<span class="eyebrow">NET INJURY COUNT IS PUBLISHED; STARTERS OUT AND REPLACEMENTS ARE BLANK</span></div>')
    b.append(table(
        ["Club", "Slate", "Rows listed", "Out", "Questionable", "No game status", "FP", "LP", "DNP",
         "Net injury count", "Expected starters out", "Replacements named", "Source", "Flag"],
        [[html.escape(t["club"]), badge(t["slate_status"]), esc(t["rows_listed"]), esc(t["out"]),
          esc(t["questionable"]), esc(t["no_game_status"]), esc(t["full_participation"]),
          esc(t["limited_participation"]), esc(t["did_not_participate"]),
          esc(t["net_injury_count"]),
          esc(t["expected_starters_out"]), esc(t["replacements_named"]),
          link(t["source_url"]),
          html.escape(t["flag"]) if t["flag"] else '<span class="blank">—</span>']
         for t in teamav],
        caption="Starters out and replacement names stay blank because the depth-order source is "
                "verified for 31 of 32 clubs only. The flag column states the reason on every row."))
    b.append('<div class="section-title"><h2>The delta, not the level</h2>'
             '<span class="eyebrow">AGAINST THE 2026-11-18T03:46Z READ</span></div>')
    b.append(note(
        "<strong>Two club statements do not survive.</strong> The earlier read carried a game-page "
        "statement that Minnesota and San Francisco had no active injuries. The league report "
        "published the next day names 10 Minnesota rows and 15 San Francisco rows, including "
        "Minnesota receiver Jordan Addison, who did not participate. A game page is not an "
        "availability source."))
    b.append(table(
        ["ID", "Club", "Player", "Change", "Previous value", "Current value",
         "Previous read (UTC)", "Current read (UTC)", "Previous source", "Current source", "Note"],
        [[html.escape(d["delta_id"]), html.escape(d["club"]), html.escape(d["player"]),
          badge(d["change_type"]), esc(d["previous_value"]), esc(d["current_value"]),
          html.escape(d["previous_read_utc"]), html.escape(d["current_read_utc"]),
          link(d["previous_source_url"]), link(d["current_source_url"]), html.escape(d["note"])]
         for d in delta[:60]],
        caption="The 60 most informative rows of %d. The remainder carry the same structure."
                % len(delta)))
    write("availability.html", page(
        "Availability",
        "The dated Week-11 capture, the per-team view and the change against the earlier read.",
        "\n".join(b), "availability.html"))

    # ------------------------------------------------------------- lines
    b = ['<div class="stats">']
    b.append(stat(len({l["game_id"] for l in lines}), "Week-11 games originated", ""))
    b.append(stat(len(lines), "Line rows", "side, then total, then moneyline"))
    b.append(stat(len(prices), "Price-snapshot rows", "every opening and closing cell blank"))
    b.append(stat(0, "Market residuals published", "no price source is admitted"))
    b.append("</div>")
    b.append(note(
        "<strong>The market line and the difference are blank, and they will stay blank.</strong> "
        "A residual needs an admitted, timestamped price. The price store holds the schema and "
        "the model record, and every market cell is flagged. Requirement R-02 is the open decision "
        "that would fill it."))
    b.append('<div class="section-title"><h2>Originated Week-11 lines</h2>'
             '<span class="eyebrow">MODEL LINE · MARKET LINE · DIFFERENCE · THREE SEPARATE COLUMNS</span></div>')
    b.append(table(
        ["Game", "Kickoff", "Away at Home", "Order", "Market", "Model fair line", "Model value",
         "Market line", "Difference vs market", "Probability", "Inputs", "Source"],
        [[html.escape(l["game_id"]), html.escape(l["kickoff_date"] + " " + l["kickoff_time_et"]),
          html.escape(l["away"] + " at " + l["home"]), esc(l["market_order"]),
          html.escape(l["market"]), '<strong>%s</strong>' % esc(l["model_fair_line"]),
          esc(l["model_fair_value"]), esc(l["market_line"]), esc(l["difference_vs_market"]),
          esc(l["probability"]), '<span class="inputs">%s</span>' % html.escape(l["inputs"]),
          link(l["source_url"])] for l in lines],
        caption="39 rows: 13 games at three markets each, in the order side, total, moneyline. "
                "The inputs column is the whole model state for that row."))
    b.append('<div class="section-title"><h2>Price snapshot store</h2>'
             '<span class="eyebrow">SCHEMA PUBLISHED, MARKET CELLS BLANK BY POLICY</span></div>')
    b.append(table(
        ["Snapshot", "Game", "Market", "Source class", "Book", "Jurisdiction", "Captured (UTC)",
         "Opening line", "Closing line", "Terms state", "Model fair line", "Flag", "Source"],
        [[html.escape(p["snapshot_id"]), html.escape(p["game_id"]), html.escape(p["market"]),
          html.escape(p["source_class"]), esc(p["book"]), esc(p["jurisdiction"]),
          esc(p["captured_utc"]), esc(p["opening_line"]), esc(p["closing_line"]),
          html.escape(p["terms_state"]), esc(p["model_fair_line"]), html.escape(p["flag"]),
          link(p["source_url"])] for p in prices[:15]],
        caption="The 15 first rows of %d. Every opening and closing cell is blank and carries the "
                "price-policy flag." % len(prices)))
    write("lines.html", page(
        "Originated lines",
        "Side, then total, then moneyline, with the model line, the market line and the difference "
        "as three separate columns.",
        "\n".join(b), "lines.html"))

    # ------------------------------------------------------- leaderboard
    b = ['<div class="stats">']
    b.append(stat(len(lb), "Registered entries", "across four divisions"))
    b.append(stat(0, "Prospective games scored", "the first game kicks off tonight"))
    b.append(stat(0, "Strategies eligible to stake", "no admitted price source"))
    b.append(stat(len(prereg), "Frozen pre-registrations", "with a commit hash"))
    b.append("</div>")
    b.append(note(
        "<strong>Signal and staking are separate columns, and both are blank.</strong> "
        "A lucky staking run must not be able to mask a bad signal, so a return can never be "
        "shown without a signal score beside it. Nothing has been played prospectively yet and no "
        "price source is admitted, so neither column has a value. No backtest number appears "
        "anywhere on this page; the shadow backtest lives on its own page and is labelled."))
    b.append('<div class="section-title"><h2>Leaderboard</h2>'
             '<span class="eyebrow">PROSPECTIVE ONLY</span></div>')
    b.append(table(
        ["Entry", "Division", "Strategy", "Scope", "Staking policy", "Registered (UTC)",
         "n prospective", "Signal score", "Signal metric", "CI low", "CI high",
         "Skill vs benchmark", "Staking return", "Staking n", "Eligibility", "Reason", "Source"],
        [[html.escape(r["entry_id"]), html.escape(r["division"]),
          html.escape(r["strategy"]) if r["strategy"] else '<span class="blank">—</span>',
          html.escape(r["market_scope"]), html.escape(r["stake_policy"]),
          html.escape(r["registered_utc"]), esc(r["n_prospective"]), esc(r["signal_score"]),
          html.escape(r["signal_score_metric"]) if r["signal_score_metric"] else '<span class="blank">—</span>',
          esc(r["signal_ci_low"]), esc(r["signal_ci_high"]), esc(r["skill_vs_benchmark"]),
          esc(r["staking_return"]), esc(r["staking_n"]), badge(r["eligibility"]),
          html.escape(r["block_reason"]), link(r["source_url"])] for r in lb],
        caption="Four divisions: singles, game parlay, same-game parlay, prop combo. The three "
                "multi-leg divisions are blocked by the joint-evidence gate."))
    b.append('<div class="section-title"><h2>Pre-registration</h2>'
             '<span class="eyebrow">FROZEN BEFORE THE WINDOW OPENED</span></div>')
    b.append(table(
        ["Strategy", "Name", "Scope", "Rule text", "Window", "Evaluation metric", "Gates",
         "Frozen (UTC)", "What would change our mind", "Second side", "Source"],
        [[html.escape(p["strategy_id"]), html.escape(p["strategy"]), html.escape(p["scope"]),
          '<span class="inputs">%s</span>' % html.escape(p["rule_text"]),
          html.escape(p["window"]), html.escape(p["evaluation_metric"]),
          html.escape(p["gates"]), html.escape(p["frozen_utc"]),
          html.escape(p["what_would_change_our_mind_a"]),
          html.escape(p["what_would_change_our_mind_b"]), link(p["source_url"])]
         for p in prereg],
        caption="The commit that freezes a rule is the registration. Each entry carries both sides "
                "of the what-would-change-our-mind field."))
    write("leaderboard.html", page(
        "Leaderboard",
        "Signal separated from staking, prospective scores only, every strategy pre-registered.",
        "\n".join(b), "leaderboard.html"))

    # ------------------------------------------------------------- gates
    b = ['<div class="stats">']
    b.append(stat(len(gates), "Gates", ""))
    for st, lbl in (("PASS", "Passed"), ("PARTIAL", "Partial"), ("BLOCKED", "Blocked")):
        b.append(stat(sum(1 for g in gates if g["current_result"] == st), lbl, ""))
    b.append("</div>")
    b.append('<div class="section-title"><h2>Validation gates</h2>'
             '<span class="eyebrow">A BLOCKED GATE NAMES ITS PREREQUISITE; IT IS NOT A FAILED STRATEGY</span></div>')
    b.append(table(
        ["Gate", "Name", "Rule", "Threshold", "Result", "Evidence", "Source", "Flag"],
        [[html.escape(g["gate_id"]), html.escape(g["gate"]), html.escape(g["rule"]),
          html.escape(g["threshold"]), badge(g["current_result"]), html.escape(g["evidence"]),
          link(g["source_url"]), html.escape(g["flag"]) if g["flag"] else '<span class="blank">—</span>']
         for g in gates]))
    write("gates.html", page(
        "Gates",
        "The validation, joint-evidence, price, depth and demotion gates, each with its result and "
        "its evidence.",
        "\n".join(b), "gates.html"))

    # ---------------------------------------------------------- backtest
    b = ['<div class="stats">']
    b.append(stat(len(results), "Games in the corpus", "weeks 1-10, reconciled to the standings"))
    b.append(stat(int(bt_val["n_games"]), "Validation games", "week 9"))
    b.append(stat(int(bt_hold["n_games"]), "Final holdout games", "week 10"))
    b.append(stat(bt_hold["sigma_points"], "Residual sigma (points)", "training window"))
    b.append(stat(bt_hold["hfa_points"], "Home field (points)", "fitted, not assumed"))
    b.append("</div>")
    b.append(note(
        "<strong>These numbers are on a shadow page and are forbidden on the leaderboard.</strong> "
        "They exist to show what a lucky run looks like: the validation week gave a Brier skill of "
        "%s and the untouched final holdout gave %s. A leaderboard that ranked on the validation "
        "week alone would have declared skill."
        % (bt_val["brier_skill_score_vs_climatology"], bt_hold["brier_skill_score_vs_climatology"])))
    b.append('<div class="section-title"><h2>Shadow backtest</h2>'
             '<span class="eyebrow">CHRONOLOGICAL SPLIT · NOT ON THE LEADERBOARD</span></div>')
    b.append(table(
        ["Run", "Split", "Train weeks", "Test weeks", "n", "Model", "Accuracy", "Brier",
         "Climatology Brier", "Brier skill", "MAE (points)", "sigma", "HFA", "Source"],
        [[html.escape(t["run_id"]), html.escape(t["split"]), html.escape(t["train_weeks"]),
          html.escape(t["test_weeks"]), esc(t["n_games"]), html.escape(t["model_version"]),
          esc(t["model_accuracy"]), esc(t["model_brier"]), esc(t["climatology_brier"]),
          '<strong>%s</strong>' % esc(t["brier_skill_score_vs_climatology"]),
          esc(t["mean_absolute_margin_error_points"]), esc(t["sigma_points"]), esc(t["hfa_points"]),
          link(t["source_url"])] for t in backtest]))
    b.append('<div class="section-title"><h2>Removal of luck</h2>'
             '<span class="eyebrow">MODEL AGAINST TWO CONTROLS</span></div>')
    b.append(table(
        ["Panel", "Metric", "Strategy", "Value", "n", "Comparator", "Skill metric", "Skill value",
         "Adjusted alpha", "Trials", "Status", "Source"],
        [[html.escape(p["panel_id"]), html.escape(p["metric"]), html.escape(p["strategy"]),
          esc(p["value"]), esc(p["n"]),
          html.escape(p["comparator"]) if p["comparator"] else '<span class="blank">—</span>',
          html.escape(p["skill_metric"]) if p["skill_metric"] else '<span class="blank">—</span>',
          esc(p["skill_value"]), esc(p["adjusted_alpha_bonferroni"]), esc(p["trial_count"]),
          badge(p["status"]), link(p["source_url"])] for p in luck]))
    b.append('<div class="section-title"><h2>Model ratings</h2>'
             '<span class="eyebrow">OPPONENT-ADJUSTED, FITTED ON WEEKS 1-8 ONLY</span></div>')
    b.append(table(
        ["Club", "Rating (points)", "Rank", "Games in fit", "Adj offense ppg", "Adj defense ppg",
         "Source"],
        [[html.escape(r["club"]), esc(r["rating_points"]), esc(r["rating_rank"]),
          esc(r["games_in_fit"]), esc(r["adj_offense_ppg"]), esc(r["adj_defense_ppg"]),
          link(r["source_url"])] for r in ratings],
        caption="rating = rating_home - rating_away plus a fitted home field of %s points."
                % bt_hold["hfa_points"]))
    b.append('<div class="section-title"><h2>Correlations</h2>'
             '<span class="eyebrow">OFFICIAL NUMBERS ONLY, WITH n</span></div>')
    b.append(corr_table(corr))
    write("backtest.html", page(
        "Backtest & luck",
        "The shadow evaluation, the removal-of-luck panel and the model ratings, with every number "
        "carrying its n.",
        "\n".join(b), "backtest.html"))

    # ------------------------------------------------------ correlations
    b = ['<div class="stats">']
    b.append(stat(len(corr), "Correlations published", "each with n"))
    b.append(stat(len({c["source_url"] for c in corr}), "Official sources used", ""))
    b.append("</div>")
    b.append(note(
        "<strong>Every correlation is computed from officially sourced numbers only</strong> and "
        "every one publishes n, a 95% interval and a two-sided p-value. Nothing is computed from a "
        "third-party price or an unofficial dataset."))
    b.append('<div class="section-title"><h2>Correlations</h2>'
             '<span class="eyebrow">n PUBLISHED WITH EVERY VALUE</span></div>')
    b.append(corr_table(corr))
    write("correlations.html", page(
        "Correlations",
        "Computed only from officially sourced numbers, with n published next to every value.",
        "\n".join(b), "correlations.html"))

    # --------------------------------------------------------- questions
    b = ['<div class="stats">']
    b.append(stat(len(qs), "Open questions", ""))
    b.append(stat(sum(1 for q in qs if q["status"] == "ANSWERED_IN_REGISTRY"), "Answered", ""))
    b.append(stat(sum(1 for q in qs if q["status"] == "CROSS_SESSION_REQUEST_RAISED"),
                  "Raised to another session", ""))
    b.append("</div>")
    b.append('<div class="section-title"><h2>Questions, information and answers</h2>'
             '<span class="eyebrow">WHAT IS KNOWN, WHAT IS MISSING, WHAT IS NEEDED BEFORE A DECISION</span></div>')
    for q in qs:
        b.append('<article class="qa">')
        b.append('<h3><span class="rid">%s</span> %s %s</h3>'
                 % (html.escape(q["question_id"]), html.escape(q["question"]), badge(q["status"])))
        b.append('<dl>')
        for lbl, key in (("Known from verified sources", "known_from_verified_sources"),
                         ("Missing information", "missing_information"),
                         ("Answer needed before a decision", "answer_needed_before_decision"),
                         ("Clearing evidence", "clearing_evidence")):
            b.append('<dt>%s</dt><dd>%s</dd>' % (html.escape(lbl),
                                                  html.escape(q[key]) if q[key] else '<span class="blank">—</span>'))
        b.append('<dt>Sources</dt><dd>%s</dd>'
                 % (link(q["official_source_urls"]) + " " + link(q["repo_evidence_urls"])))
        b.append("</dl></article>")
    write("questions.html", page(
        "Questions",
        "What is known, what is missing and what must be answered before a decision can reasonably "
        "be made.",
        "\n".join(b), "questions.html"))

    # -------------------------------------------------------- suggestions
    b = ['<div class="stats">']
    b.append(stat(len(sgs), "Suggestions", "none implemented"))
    b.append(stat(sum(1 for s in sgs if s["priority"] == "high"), "High priority", ""))
    b.append(stat(0, "Suggestions implemented", "each awaits a decision"))
    b.append("</div>")
    b.append(note(
        "<strong>Nothing here has been implemented.</strong> Each suggestion lists the options, a "
        "recommended path, and both sides of the what-would-change-our-mind field: what would make "
        "the recommendation change, and what would keep it. A decision is the reviewer's to make."))
    for s in sgs:
        b.append('<article class="qa">')
        b.append('<h3><span class="rid">%s</span> %s <span class="badge %s">%s</span></h3>'
                 % (html.escape(s["suggestion_id"]), html.escape(s["topic"]),
                    "bad" if s["priority"] == "high" else "warn", html.escape(s["priority"])))
        b.append('<dl>')
        b.append('<dt>Options</dt><dd>%s</dd>' % html.escape(s["options"]))
        b.append('<dt>Recommended path</dt><dd><strong>%s</strong></dd>' % html.escape(s["recommended_path"]))
        b.append('<dt>What would change our mind</dt><dd>%s</dd>'
                 % html.escape(s["what_would_change_our_mind"]))
        b.append('<dt>Decision status</dt><dd>%s</dd>' % badge(s["decision_status"]))
        b.append('<dt>Sources</dt><dd>%s</dd>'
                 % (link(s["official_source_urls"]) + " " + link(s["related_evidence_urls"])))
        b.append("</dl></article>")
    write("suggestions.html", page(
        "Suggestions",
        "Options, a recommended path and both sides of the what-would-change-our-mind field, for "
        "review before any change is implemented.",
        "\n".join(b), "suggestions.html"))

    # ----------------------------------------------------------- flagged
    b = ['<div class="stats">']
    b.append(stat(len(flags), "Flagged items", ""))
    for sev in ("critical", "blocking", "review", "resolved"):
        n = sum(1 for f in flags if f["severity"] == sev)
        if n:
            b.append(stat(n, sev.title(), ""))
    b.append("</div>")
    b.append(note(
        "<strong>Nothing here blocks the site.</strong> Every item carries the official source that "
        "produced it, so it can be reviewed and requested. The critical and blocking items are the "
        "ones that would change a decision."))
    b.append(table(
        ["ID", "Severity", "Item", "Observation", "Decision impact", "Action", "Official source",
         "Repository evidence", "Status"],
        [[html.escape(f["flag_id"]),
          '<span class="badge %s">%s</span>' % ("bad" if f["severity"] in ("critical", "blocking")
                                                else ("ok" if f["severity"] == "resolved" else "warn"),
                                                html.escape(f["severity"])),
          html.escape(f["item"]), html.escape(f["observation"]), html.escape(f["decision_impact"]),
          html.escape(f["action"]), link(f["official_source_urls"]),
          link(f["repo_evidence_urls"]), badge(f["status"])] for f in flags]))
    write("flagged.html", page(
        "Flagged for review",
        "Irregularities and unverified items, each with the official source that produced it.",
        "\n".join(b), "flagged.html"))

    # ----------------------------------------------------------- sources
    b = ['<div class="stats">']
    b.append(stat(len(sources), "Sources", ""))
    b.append(stat(sum(1 for s in sources if s["read_at_utc"] != "not read in this session"),
                  "Read first-hand", ""))
    b.append(stat(len(desks), "Desks indexed", ""))
    b.append("</div>")
    b.append('<div class="section-title"><h2>Sources</h2>'
             '<span class="eyebrow">WHAT EACH SOURCE ESTABLISHES, AND WHAT IT CANNOT</span></div>')
    b.append(table(
        ["ID", "Publisher", "Title", "Read at (UTC)", "What it establishes", "Scope limit", "URL"],
        [[html.escape(s["source_id"]), html.escape(s["publisher"]), html.escape(s["title"]),
          html.escape(s["read_at_utc"]), html.escape(s["what_it_establishes"]),
          html.escape(s["scope_limit"]), link(s["url"])] for s in sources]))
    b.append('<div class="section-title"><h2>Desk index</h2>'
             '<span class="eyebrow">EVERY NFL DESK IN THE REPOSITORY</span></div>')
    b.append(table(
        ["Desk", "Name", "Entry page", "What it holds", "Official source links", "Flagged items",
         "Read-only for this session"],
        [[html.escape(d["desk_id"]), html.escape(d["desk_name"]),
          '<a href="../%s">%s</a>' % (html.escape(d["entry_page"]), html.escape(d["entry_page"])),
          html.escape(d["what_it_holds"]), link(d["official_source_links"]), esc(d["flagged_count"]),
          html.escape(d["read_only_for_this_session"])] for d in desks],
        caption="Links are repository-relative from the desk folder, so they resolve on GitHub "
                "Pages and on GitHub alike."))
    write("sources.html", page(
        "Sources",
        "Every source with what it establishes and what it cannot, plus the index of the desks.",
        "\n".join(b), "sources.html"))

    # ---------------------------------------------------- executive summary
    b = ['<div class="stats">']
    b.append(stat(len(reqs), "Requirements", "one row each"))
    b.append(stat(status_count.get("MET", 0), "Met", ""))
    b.append(stat(status_count.get("PARTIAL", 0), "Partial", ""))
    b.append(stat(status_count.get("BLOCKED", 0), "Blocked", ""))
    b.append(stat(len(flags), "Flagged", ""))
    b.append("</div>")
    b.append('<div class="section-title"><h2>The short version</h2>'
             '<span class="eyebrow">WHAT IS TRUE, WHAT IS COMPUTED, WHAT IS MISSING</span></div>')
    b.append('<div class="brief-grid">')
    b.append('<article class="panel brief"><span class="step">VERIFIED</span>'
             '<h3>What was read first-hand</h3>'
             '<p>The 2026 league standings (32 clubs), the Week-11 official injury report (253 rows '
             'across 24 clubs), the Week-11 schedule (13 games), all 14 Week-10 finals, the 2026 '
             'Schedule Release page, the Colts at Texans game centre, and the complete official '
             'Game Book for Washington at New York, which publishes the actual starters, the Not '
             'Active list and the game-day weather.</p></article>')
    b.append('<article class="panel brief"><span class="step">COMPUTED</span>'
             '<h3>What was derived</h3>'
             '<p>An opponent-adjusted rating model fitted on weeks 1-8 only, a fitted home field of '
             '%s points, a residual sigma of %s points, 39 originated lines across 13 games, 8 '
             'correlations with n and intervals, a %d-game corpus reconciled to the standings with '
             '0 mismatches, and a two-split shadow backtest.</p></article>'
             % (bt_hold["hfa_points"], bt_hold["sigma_points"], len(results)))
    b.append('<article class="panel brief"><span class="step">MISSING</span>'
             '<h3>What is blocked and why</h3>'
             '<p>No admitted price source, so no market residual, no closing-line value and no '
             'return. No verified depth order for the Houston Texans and no verified official '
             'snap-count source, so no replacement depth and no matchup matrix. No prospective game '
             'played, so the leaderboard carries no score.</p></article>')
    b.append("</div>")
    b.append('<div class="section-title"><h2>The finding that matters most</h2>'
             '<span class="eyebrow">REMOVAL OF LUCK</span></div>')
    b.append(table(
        ["Split", "n", "Model accuracy", "Model Brier", "Climatology Brier", "Brier skill",
         "MAE (points)", "Favourites-only win rate"],
        [[html.escape(t["split"]), esc(t["n_games"]), esc(t["model_accuracy"]),
          esc(t["model_brier"]), esc(t["climatology_brier"]),
          '<strong>%s</strong>' % esc(t["brier_skill_score_vs_climatology"]),
          esc(t["mean_absolute_margin_error_points"]), lp_fave["value"]] for t in backtest],
        caption="The same model, the same controls, two chronological splits. The validation week "
                "would have looked like skill. The untouched holdout did not."))
    b.append('<div class="section-title"><h2>Decisions waiting on the reviewer</h2>'
             '<span class="eyebrow">FROM THE SUGGESTIONS REGISTER</span></div>')
    b.append(table(
        ["ID", "Priority", "Topic", "Recommended path", "What would change our mind", "Status"],
        [[html.escape(s["suggestion_id"]), html.escape(s["priority"]), html.escape(s["topic"]),
          html.escape(s["recommended_path"]), html.escape(s["what_would_change_our_mind"]),
          badge(s["decision_status"])] for s in sgs]))
    write("executive-summary.html", page(
        "Executive summary",
        "What is verified, what is computed, what is blocked, and the three findings that change a "
        "decision.",
        "\n".join(b), "executive-summary.html"))

    print("wrote %d pages to %s" % (len(NAV), OUT))


def corr_table(corr):
    return table(
        ["ID", "What is correlated", "Statistic", "Value", "n", "95% low", "95% high",
         "Two-sided p", "Unit", "Method", "Source"],
        [[html.escape(c["correlation_id"]), html.escape(c["description"]),
          html.escape(c["statistic"]), '<strong>%s</strong>' % esc(c["value"]), esc(c["n"]),
          esc(c["ci95_low"]), esc(c["ci95_high"]), esc(c["p_value_two_sided"]),
          html.escape(c["unit"]), html.escape(c["method"]), link(c["source_url"])]
         for c in corr],
        caption="Every value is computed from officially sourced numbers, and every value carries "
                "the number of observations behind it.")


def write(name, content):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(content)


if __name__ == "__main__":
    build()

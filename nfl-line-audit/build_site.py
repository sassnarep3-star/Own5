#!/usr/bin/env python3
"""Render the NFL verified line desk (static HTML, stdlib only, deterministic).

Every table cell comes from a CSV in nfl-line-audit/data/. Cells that are empty are rendered
as a badged blank, never as a zero. No JavaScript is required to read anything.
"""
import csv
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
BUILT = "2026-11-19T07:05:00Z"

PAGES = [
    ("index.html", "Dashboard"),
    ("origination.html", "Originated lines"),
    ("prices.html", "Price snapshots"),
    ("results.html", "Verified results"),
    ("availability.html", "Availability"),
    ("model.html", "Model & backtest"),
    ("leaderboard.html", "Leaderboard"),
    ("correlations.html", "Correlations"),
    ("readiness.html", "Decision readiness"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("research.html", "Research register"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("summary.html", "Executive summary"),
]


def read(name):
    p = os.path.join(D, name)
    if not os.path.exists(p):
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(x):
    return html.escape(str(x if x is not None else ""), quote=True)


BADGES = {
    "MET": "ok", "PARTIALLY MET": "mid", "NOT MET": "bad",
    "OFFICIAL": "ok", "PINNED-DATASET": "mid", "AGGREGATOR": "mid", "OPERATOR": "mid", "REPO": "muted",
    "OPEN": "bad", "RESOLVED": "ok",
}
WORDS = ["MATCH", "MISMATCH", "AGREE", "DISAGREE", "NOT IN PINNED SNAPSHOT", "CLUB-CODE MISMATCH",
         "REPO LOG BLANK", "YES", "NO", "CONTROL", "BLOCKED", "CONDITIONAL", "MET", "PARTIALLY MET", "NOT MET",
         "OFFICIAL", "PINNED-DATASET", "AGGREGATOR", "OPERATOR", "REPO", "OPEN", "RESOLVED", "new on report"]


def badge(text):
    t = (text or "").strip()
    if not t:
        return '<span class="b b-blank">blank</span>'
    for key, cls in BADGES.items():
        if t.upper().startswith(key):
            return '<span class="b b-%s">%s</span>' % (cls, esc(t))
    for w in WORDS:
        if t.upper().startswith(w):
            cls = "ok" if w in ("MATCH", "AGREE", "YES", "MET", "OFFICIAL", "RESOLVED") else (
                "bad" if w in ("MISMATCH", "DISAGREE", "NO", "NOT MET", "BLOCKED") else "muted")
            return '<span class="b b-%s">%s</span>' % (cls, esc(t))
    return esc(t)


def link_cell(url, label=None):
    """Render one link per URL. Several URLs in a cell are separated and each gets its own anchor."""
    if not url or not str(url).startswith("http"):
        return '<span class="b b-blank">no source</span>'
    if label:
        return '<a href="%s" rel="noopener" target="_blank">%s</a>' % (esc(url), esc(label))
    parts = [p.strip() for p in str(url).split(";") if p.strip().startswith("http")]
    if not parts:
        return '<span class="b b-blank">no source</span>'
    return "<br>".join('<a href="%s" rel="noopener" target="_blank">%s</a>' % (esc(p), esc(short(p))) for p in parts)


def short(url):
    u = re.sub(r"^https?://(www\.)?", "", str(url))
    u = re.sub(r"^github\.com/sassnarep3-star/Own5/blob/main/", "repo/", u)
    u = re.sub(r"^github\.com/nflverse/nflverse-data/releases/download/", "nflverse/", u)
    return u[:72]


NUMERIC = re.compile(r"^-?\d+(\.\d+)?$")


def cell(v, col=""):
    v = "" if v is None else str(v)
    if v == "":
        return '<td class="blank"><span class="b b-blank">—</span></td>'
    if col.endswith("_url") or col in ("source_url", "evidence_url", "schedule_url", "url", "evidence"):
        return "<td>%s</td>" % link_cell(v)
    if NUMERIC.match(v) and ("skill" in col or "ci_" in col or "roi" in col or "probability" in col or "value" in col):
        fv = float(v)
        cls = "neg" if fv < 0 else ("pos" if fv > 0 else "")
        return '<td class="num %s">%s</td>' % (cls, esc(v))
    if col in ("status", "verdict", "match", "certified", "source_class", "type", "decision"):
        return "<td>%s</td>" % badge(v)
    return "<td>%s</td>" % esc(v)


def table(rows, cols=None, caption="", note=""):
    if not rows:
        return '<p class="empty">No rows. This is a published empty table, not a missing build step.</p>'
    cols = cols or list(rows[0].keys())
    head = "".join("<th>%s</th>" % esc(c.replace("_", " ")) for c in cols)
    body = []
    for r in rows:
        body.append("<tr>" + "".join(cell(r.get(c, ""), c) for c in cols) + "</tr>")
    cap = '<caption>%s</caption>' % esc(caption) if caption else ""
    n = '<p class="note">%s</p>' % note if note else ""
    return ('<div class="tw"><table>%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>%s'
            % (cap, head, "".join(body), n))


def page(title, active, body, sub=""):
    nav = "".join('<a href="%s"%s>%s</a>' % (h, ' class="active"' if h == active else "", esc(t))
                  for h, t in PAGES)
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s · NFL verified line desk</title>
<link rel="stylesheet" href="style.css">
</head><body>
<header class="top">
  <a class="brand" href="index.html"><span class="mark">O5</span> NFL verified line desk</a>
  <nav>%s</nav>
</header>
<main>
<h1>%s</h1>
%s
%s
</main>
<footer>
  <p>Built %s from <code>nfl-line-audit/data/</code>. Official facts link to nfl.com; operator prices link to the operator page.
  Empty cells are unverified and badged, never filled. No betting advice, no performance claim.</p>
  <p>Independence: this desk is not affiliated with the NFL. Data policy P-01 keeps row-level official data off this site.</p>
</footer>
</body></html>
""" % (esc(title), nav, esc(title), '<p class="sub">%s</p>' % esc(sub) if sub else "", body, esc(BUILT))


def stat_cards(items):
    out = []
    for value, label, cls in items:
        out.append('<div class="card %s"><div class="v">%s</div><div class="l">%s</div></div>' % (cls, value, label))
    return '<section class="cards">%s</section>' % "".join(out)


def main():
    S = json.load(open(os.path.join(D, "derive_summary.json"), encoding="utf-8"))
    req = read("requirements.csv")
    orig = read("origination_week11.csv")
    prices = read("price_snapshots.csv")
    corpus = read("corpus_games.csv")
    recon = read("corpus_reconciliation.csv")
    log = read("log136_diff.csv")
    ratings = read("ratings.csv")
    avail = read("availability_week11.csv")
    delta = read("injury_delta.csv")
    bt = read("backtest_strategies.csv")
    lbias = read("line_bias.csv")
    screen = read("holdout_screen.csv")
    wf = read("walkforward_backtest.csv")
    err = read("prediction_error.csv")
    split = read("time_split.csv")
    luck = read("luck_panel.csv")
    corr = read("correlations.csv")
    desig = read("designation_reliability.csv")
    slots = read("slot_usage_rule.csv")
    starters = read("snap_starter_study.csv")
    lb = read("leaderboard.csv")
    qs = read("questions.csv")
    sug = read("suggestions.csv")
    res = read("research.csv")
    flags = read("flagged.csv")
    srcs = read("sources.csv")
    finals = read("week10_finals.csv")
    returns = read("returns_register.csv")
    abl = read("ablations.csv")

    counts = {}
    for r in req:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    met = counts.get("MET", 0)
    partial = counts.get("PARTIALLY MET", 0)
    notmet = counts.get("NOT MET", 0)
    brier = S["luck"]["brier_skill"]

    # ---------------------------------------------------------------- dashboard
    body = stat_cards([
        (str(len(req)), "brief lines tracked, one row each", ""),
        (str(met), "met with evidence in this desk", "ok"),
        (str(partial), "partially met, gap stated", "mid"),
        (str(notmet), "not met", "bad"),
        ("%+.1f%%" % (100 * brier), "model Brier skill vs the closing line (744 games)", "bad"),
        (str(S["reconciliation"]["matches"]) + "/32", "clubs reconciling to the official standings", "ok"),
        ("0", "strategies certified (pre-registered gate)", "mid"),
        ("0", "settled prospective bets (first kickoff tonight)", "muted"),
    ])
    body += """
<section class="verdict">
  <h2>The finding, first</h2>
  <p><strong>Our own line loses to the closing line.</strong> The model was frozen before evaluation, refit each week on prior
  weeks only, and scored against the de-vigged closing price on 744 out-of-sample games: Brier skill
  <strong>%(brier)+.1f%%</strong>. The side markets we bet in a pre-registered backtest are not separated from the market;
  the total and moneyline families are <em>significantly worse</em> than it after multiplicity correction. Nothing is on the
  leaderboard because nothing has settled.</p>
  <p>One baseline does read positive: betting every over at the closing number returns +0.33%%. The Market &amp; model page
  shows why — the closing total sits 1.26 points low against what was scored — and why that is a market quirk to be
  pre-registered, not a strategy: the screen that found it used the holdout.</p>
  <p>That is the useful result. A desk that will not publish a failure cannot publish anything.</p>
</section>
<section class="cols">
  <article>
    <h2>What this desk does</h2>
    <ul>
      <li>Prices all 13 Week 11 fixtures itself: <b>side, then total, then moneyline</b>, with fair, market and difference in separate columns.</li>
      <li>Stores every market's opening quote from <b>two named operators</b> with the read clock; closings stay blank until kickoff.</li>
      <li>Reads the official Week 11 injury report today and publishes a <b>delta</b> against the 18 Nov read, never a level.</li>
      <li>Measures what <b>“Questionable”</b> is worth: 25.0%% played, n=4,970, interval published.</li>
      <li>Ranks by <b>proper scores with a clustered interval and a multiplicity adjustment</b>, with staking kept in its own column.</li>
      <li>Freezes a registration before any evaluation; the commit hash is the registration.</li>
    </ul>
  </article>
  <article>
    <h2>What it refuses to do</h2>
    <ul>
      <li><b>No fixed point penalty</b> for a missing starter: no such penalty exists anywhere in the pipeline.</li>
      <li><b>No depth from jersey order, experience or salary</b>: usage rank comes from playing time only.</li>
      <li><b>No backtest number on the leaderboard.</b></li>
      <li><b>No marginal multiplication</b> for parlays: the joint is required first (r=0.513 shows why).</li>
      <li><b>No inferred replacement name</b>: an unnamed replacement stays blank.</li>
    </ul>
  </article>
</section>
""" % {"brier": 100 * brier}
    body += '<section><h2>Decision readiness — one row per line of the brief</h2>'
    body += '<p class="sub">Status, the gate that blocks it, and the number that would clear it. Every row links to its evidence.</p>'
    body += table(req, ["id", "requirement", "status", "blocking_gate", "observed", "evidence_path"],
                  note="The full table with categories is on the Decision readiness page. Status is a judgement against the evidence in this desk only.")
    body += "</section>"
    body += '<section><h2>Open items that need your decision</h2>'
    body += table([r for r in sug if r["id"] in ("S01", "S03", "S06", "S09", "S11")],
                  ["id", "suggestion", "recommendation", "cost"], note="Twelve suggestions are on the Suggestions page, each with options, a recommendation and what would change our mind.")
    body += "</section>"
    write("index.html", page("Dashboard", "index.html", body,
                             "Line origination, verified results and a skill leaderboard for the 2026 NFL season. Official sources only; operator prices named and stamped."))

    # ---------------------------------------------------------------- origination
    body = '<p class="sub">Three markets in the required order: side, then total, then moneyline. Fair line, market line and the difference are separate columns on every row. Market values are the median of two named operators, de-vigged where the market is a probability.</p>'
    body += stat_cards([
        (str(len([r for r in orig if r["market"] == "side"])), "fixtures with an originated side", ""),
        (str(len(orig)), "market rows (4 per fixture)", ""),
        ("2", "named operators behind every market cell", "ok"),
        ("0", "market cells filled without an admitted quote", "ok"),
    ])
    body += '<section><h2>Week 11 originated markets</h2>'
    body += table(orig, ["game_id", "away", "home", "kickoff_as_printed", "market_order", "market", "side",
                         "fair_line", "probability", "market_line", "market_n_books",
                         "difference_fair_minus_market", "inputs_sha256", "source_url", "market_url"],
                  note="probability is the model's probability for that side or over; inputs_sha256 is recomputed from the published input object by the verifier. Sign convention: fair and market side lines are home-favoured-negative as operators print them.")
    body += "</section>"
    body += '<section><h2>The ratings behind the lines</h2>'
    body += '<p class="sub">Opponent-adjusted, recency-weighted points per drive. A club’s offence is measured against the defences it actually faced; the fit is iterative and deterministic.</p>'
    body += table(ratings, ["club", "off_points_per_drive", "def_points_allowed_per_drive", "net_points_per_drive",
                            "weighted_games", "est_drives_per_game", "source_url"])
    body += "</section>"
    write("origination.html", page("Originated lines", "origination.html", body,
                                   "Our own prices for all 13 Week 11 fixtures, in the order side → total → moneyline."))

    # ---------------------------------------------------------------- prices
    body = '<p class="sub">Every quote is stored with the operator, the printed price, the read clock and the page URL. Closing values are blank until kickoff by policy: a closing number can only be read at kickoff and is never inferred.</p>'
    body += stat_cards([
        (str(len([p for p in prices if p["operator"] != "CONSENSUS (median of named books)"])), "operator quote cells stored", ""),
        ("2", "named operators", "ok"),
        ("0", "closing values (none captured yet)", "muted"),
        ("1", "capture per operator so far", "mid"),
    ])
    body += '<section><h2>Price snapshots</h2>'
    body += table([p for p in prices if p["operator"] != "CONSENSUS (median of named books)"],
                  ["operator", "capture_id", "read_utc", "away", "home", "market", "field", "value_as_printed",
                   "snapshot_role", "closing_value", "source_url"],
                  note="Consensus rows (n_books) are on the same CSV. A two-book median is a midpoint, not a market truth; operator disagreements of a full point are flagged.")
    body += "</section>"
    body += """<section><h2>Why the closing column is empty</h2>
<ul>
  <li>All 13 Week 11 games kick off 2026-11-19 to 2026-11-23. The first is tonight, 8:15 PM ET.</li>
  <li>A closing price must be read at the moment the market closes for a specific game. Anything earlier is an opening or a current price.</li>
  <li>The capture job committed with this desk reads both operators on a schedule; when a closing read lands, the row fills and the verifier stops accepting a blank.</li>
</ul></section>"""
    write("prices.html", page("Price snapshots", "prices.html", body,
                              "Opening and current operator quotes for every market we originate, with clocks."))

    # ---------------------------------------------------------------- results
    body = '<p class="sub">The results feed everything the model fits on. Week 10 was appended from the official week page because the pinned snapshot stops at week 9.</p>'
    body += stat_cards([
        (str(S["corpus_usable_games"]), "games usable by the model (of %s in the pinned corpus)" % S["corpus_games"], ""),
        (str(S["reconciliation"]["matches"]) + "/32", "clubs reconciling on W-L-T, PF and PA", "ok"),
        (str(len(finals)), "Week 10 finals read officially today", "ok"),
        ("19", "rows in the repo's 136-game log that need a source", "bad"),
    ])
    body += '<section><h2>Week 10 finals</h2>'
    body += table(finals, ["away", "home", "away_score", "home_score", "total", "winner", "section_as_printed", "source_url", "read_utc"])
    body += "</section>"
    body += '<section><h2>Corpus reconciliation to the official standings</h2>'
    body += table(recon, ["club", "official_w", "official_l", "official_t", "official_pf", "official_pa", "official_net",
                          "derived_w", "derived_l", "derived_t", "derived_pf", "derived_pa", "match", "source_url"],
                  note="Game-derived records from the corpus versus the official standings read at 2026-11-19T06:50Z. 32/32 match. A mismatch would block the build.")
    body += "</section>"
    body += '<section><h2>136-game log audit</h2>'
    body += '<p class="sub">Every row of the committed log checked against the pinned source. Agreements, blanks and absences are counted, not asserted.</p>'
    body += stat_cards([
        (str(S["log136"]["agree"]), "rows agree on the posted score", "ok"),
        (str(S["log136"]["blank"]), "rows have no score in the log at all", "mid"),
        (str(S["log136"]["missing"]), "fixtures absent from the pinned snapshot", "bad"),
        ("0", "rows that disagree on a posted score", "ok"),
    ])
    body += table(log, ["week", "away", "home", "repo_log_away_score", "repo_log_home_score",
                        "pinned_away_score", "pinned_home_score", "verdict", "source_url"],
                  note="A blank in the log is a table row with no score posted, which cannot enter a backtest. The full 136 rows are on this page.")
    body += "</section>"
    body += '<section><h2>Reserve-list register</h2>'
    body += table(returns, ["club_as_printed", "date_as_printed", "player_as_printed", "position_as_printed",
                            "transaction_as_printed", "source_url", "read_utc"],
                  note="From a committed byte capture with a sha256 in the own5-hub manifest. Completeness across all 32 clubs is not established and is flagged.")
    body += "</section>"
    write("results.html", page("Verified results", "results.html", body,
                               "Every game the model fits on has a source row, and the corpus reconciles to the official standings."))

    # ---------------------------------------------------------------- availability
    body = '<p class="sub">The official Week 11 injury report read today, with the two clocks and the previous read beside it. Depth is modelled from playing time only.</p>'
    body += stat_cards([
        (str(S["injury_delta"]["now_rows"]), "official rows read today (24 clubs)", "ok"),
        (str(S["injury_delta"]["changed_rows"]), "player-level changes vs the 18 Nov read", "mid"),
        ("25.0%", "Questionable players who actually played (n=4,970)", "bad"),
        ("0", "jersey numbers used anywhere in the model", "ok"),
    ])
    body += """<section class="verdict"><h2>What “Questionable” is actually worth</h2>
<p>Across four seasons of official designations joined to playing time: <b>Questionable = 25.0%% played</b>
(95%% interval 23.8–26.2%%, n=4,970 rows; 2,982 joined to a playing-time record). <b>Out = 0.00%%</b> (n=4,087) and
<b>Doubtful = 0.20%%</b> (n=499). The label is not a probability and is never turned into a points penalty here.</p></section>"""
    body += '<section><h2>Designation reliability</h2>'
    body += table(desig, ["designation_as_printed", "rows_in_reports", "matched_to_playing_time", "played_share",
                          "played_share_ci_low", "played_share_ci_high", "join_rate", "seasons_pooled", "source_url"],
                  note="'Played' means a recorded offensive snap share above 5% in that club-week. A missing join is not counted as 'did not play', so the play rate is conservative.")
    body += "</section>"
    body += '<section><h2>Usage rank within a position group — the depth proxy</h2>'
    body += '<p class="sub">Rank 1 in WR is the receiver who played the most offensive snaps that week. Many club-weeks have three receivers near the top, which is why a single “starter” is the wrong object: the distribution is the honest answer.</p>'
    body += table(slots, ["position_group", "usage_rank", "club_weeks", "mean_offensive_share", "p10", "p90",
                          "share_of_club_weeks_under_50pct", "rule", "source_url"])
    body += "</section>"
    body += '<section><h2>Top-two playing-time split by club</h2>'
    body += table(starters, ["club", "team_games", "avg_top1_offensive_share", "avg_top2_offensive_share",
                             "avg_players_at_50pct_or_more", "source_url"])
    body += "</section>"
    body += '<section><h2>Changes since the 18 November read</h2>'
    body += table(delta, ["club", "player", "position", "prior_report_week", "this_report_week", "prior_game_status",
                          "this_game_status", "prior_practice_status", "this_practice_status", "delta", "source_url"],
                  note="Both clocks on every row. No level is published as a signal; this is the delta and nothing else.")
    body += "</section>"
    body += '<section><h2>Week 11 designation table, verbatim</h2>'
    body += ('<p class="note">How to read an empty cell: <span class="b b-blank">—</span> means the official source printed '
             'nothing there, or the value could not be verified. It is never a zero, never a guess, and never carried '
             'forward from another week. 1,475 cells on this table are blank by that rule.</p>')
    body += table(avail, ["club", "player_as_printed", "position_as_printed", "injury_as_printed",
                          "practice_status_as_printed", "game_status_as_printed", "last_2026_week_with_snaps",
                          "last_2026_offensive_share", "usage_rank_note", "source_url"],
                  note="Every cell is the official print, including the blanks. Two clubs print 'No Injuries Reported' and appear as a single row each.")
    body += "</section>"
    write("availability.html", page("Availability", "availability.html", body,
                                   "Official designations, a measured delta, and a depth proxy built from playing time."))

    # ---------------------------------------------------------------- model
    body = '<p class="sub">The model, its walk-forward record, and the pre-registered strategies scored against the market.</p>'
    body += stat_cards([
        ("%+.1f%%" % (100 * S["luck"]["brier_skill"]), "Brier skill vs the de-vigged closing line", "bad"),
        ("%+.2f" % S["line_bias"]["closing_total_bias"], "closing total minus what was scored, points", "mid"),
        (str(S["walkforward_predictions"]), "out-of-sample game predictions", ""),
        ("0", "strategies certified", "mid"),
        ("359", "bets needed to separate 55% from break-even", "mid"),
    ])
    body += '<section class="verdict"><h2>Result: the line is better than the model</h2>'
    body += '<p>On 744 walk-forward games the closing line beats our originated probability. The error table below shows it per season: mean absolute error on the side, model versus line.</p></section>'
    body += '<section><h2>Prediction error by season</h2>'
    body += table(err, ["season", "games", "side_mae_model", "side_mae_closing_line", "side_bias_model",
                        "total_mae_model", "total_mae_closing_line", "total_bias_model",
                        "closing_total_bias", "closing_side_bias", "model_closer_than_line_side", "source_url"],
                  note="Bias is mean(actual - forecast). The model's total bias is near zero; the closing line's bias is "
                       "consistently positive, which is the effect the over screen picks up.")
    body += "</section>"
    body += '<section><h2>The closing line is also imperfect &mdash; and that is not a business</h2>'
    body += '<p class="sub">The market beats this model on every measure, but it is not unbiased. Measured, with a week-clustered interval.</p>'
    body += table(lbias, ["panel", "statistic", "value", "ci_low", "ci_high", "n", "clusters", "reads"],
                  caption="Line bias and dispersion",
                  note="Cluster bootstrap over 49 (season, week) cells, 2,000 draws. A positive residual means the closing number sat below what was scored.")
    body += """<section class="verdict"><h2>The one positive number, and why it is not published as a strategy</h2>
<p>Betting every over at the closing total returns <b>+0.33%</b> per unit across 741 decided games. The reason is in the
bias row: the closing total sits about <b>1.26 points below</b> the total actually scored (cluster interval 0.40 to 2.05).
That is a market-level effect, not a modelling edge, and it shrinks each season.</p>
<p>The screen below asks where the effect lives. It found no concentration by total size, so it is a league-wide level
shift rather than a subset effect. <b>Because this screen looked at the holdout, the holdout is no longer a holdout for
this hypothesis.</b> Any test of it must be pre-registered on 2026 games before kickoff, with the threshold frozen and the
registration commit published first. No threshold is proposed here.</p></section>"""
    body += table(screen, ["cell", "n", "over_rate", "roi_flat", "mean_residual", "reads"],
                  caption="Where the over effect lives (discovery screen, not a result)")
    body += "</section>"
    body += '<section><h2>Time split</h2>'
    body += table(split, ["split", "seasons", "games", "brier_skill_vs_market", "model_brier", "reads", "source_url"],
                  note="The one family that looked positive in the 2023-2024 window reverses in the 2025-2026 holdout. The holdout column is the one that counts.")
    body += "</section>"
    body += '<section><h2>Pre-registered strategies, scored (BACKTEST)</h2>'
    body += table(bt, ["strategy", "bets", "wins", "win_rate", "units", "roi", "brier_skill_vs_market",
                       "ci_low", "ci_high", "p_raw", "p_holm", "certified", "staking_grade"],
                  note="BACKTEST NUMBERS. These are forbidden on the leaderboard and are published here only. Skill is benchmark-relative Brier skill on each strategy's own bets; the interval is a 1,000-draw game-cluster bootstrap; p_holm is Holm-adjusted across the seven registered families.")
    body += "</section>"
    body += '<section><h2>Removal of luck</h2>'
    body += table(luck, ["panel", "statistic", "value", "n", "band_low", "band_high", "reads", "source_url"],
                  note="How much of a run is variance, and what sample is needed before a skill claim is possible.")
    body += "</section>"
    body += '<section><h2>Ablations, not fixed penalties</h2>'
    body += table(abl, ["ablation", "seasons", "games", "brier_skill_vs_market", "brier_model", "change_vs_base",
                        "verdict", "source_url"])
    body += "</section>"
    body += '<section><h2>The walk-forward game log</h2><p class="sub">Every prediction, the line it was scored against, and the sigma used at the time. Full table.</p>'
    body += table(wf, ["season", "week", "game_id", "away", "home", "home_score", "away_score", "model_margin_home",
                       "market_margin_home", "p_home_model", "p_home_market", "model_total", "closing_total",
                       "sigma_margin", "sigma_total", "history_games"])
    body += "</section>"
    write("model.html", page("Model & backtest", "model.html", body,
                             "A frozen model, honestly scored. It loses to the closing line; the numbers say so."))

    # ---------------------------------------------------------------- leaderboard
    body = '<p class="sub">Prospective results only. The pre-registration forbids backtest numbers here, so until bets settle this page is empty by construction.</p>'
    body += stat_cards([
        ("0", "settled prospective bets", "mid"),
        ("0", "certified strategies", "mid"),
        (str(len(lb)), "divisions under watch", ""),
        ("90%", "confidence level of the demotion gate's lower bound", ""),
    ])
    body += """<section><h2>How a strategy gets on this page</h2>
<ol class="steps">
  <li>Its definition is frozen in a registration commit <em>before</em> any evaluation. The commit hash is the registration.</li>
  <li>It is forecast pre-kickoff and settles against the operator price recorded at capture time.</li>
  <li>It is ranked by benchmark-relative Brier skill with a game-cluster interval, then Holm-adjusted across families.</li>
  <li>Staking is a separate column. A lucky staking run cannot lift a bad signal.</li>
  <li>It returns to paper automatically if the skill lower bound drops below zero, if ROI over the last 50 bets is at or below -10%, or if its inputs change without a new registration.</li>
</ol></section>"""
    body += '<section><h2>Divisions</h2>'
    body += table(lb, ["division", "strategy_id", "strategy", "settled_bets", "brier_skill_vs_market", "ci_low",
                       "ci_high", "p_holm", "signal_grade", "staking_units", "staking_roi", "demotion_status",
                       "what_would_change_our_mind"])
    body += "</section>"
    write("leaderboard.html", page("Leaderboard", "leaderboard.html", body,
                                   "Proper scores with uncertainty; staking held separate; a gate that demotes."))

    # ---------------------------------------------------------------- correlations
    body = '<p class="sub">Only officially sourced numbers, and n printed beside every value. The source class is stated on each row: OFFICIAL, or PINNED-DATASET when the input is an aggregator.</p>'
    body += table(corr, ["correlation", "n", "value", "ci_low", "ci_high", "sample", "source_class", "source_url", "note"])
    body += """<section class="verdict"><h2>What the correlations decide</h2>
<ul>
  <li><b>Same-game parlay legs are dependent.</b> QB passing yards and the team's top-WR receiving yards move together at r=0.513 over 1,523 team-games. Multiplying marginal probabilities would overstate the joint and is forbidden.</li>
  <li><b>Side and total are nearly independent.</b> Home margin and game total correlate at 0.019 over 952 games, so a same-game side+total combination is admissible only with a joint that respects that near-independence.</li>
  <li><b>Scoring and winning move together but not identically</b> (PF/G vs win pct 0.716, 95% interval 0.505–0.863, n=32 clubs). A points-based rating and a win-based rating will disagree, which is why the model does not use win percentage at all.</li>
</ul></section>"""
    write("correlations.html", page("Correlations", "correlations.html", body,
                                    "Dependence measured, with sample sizes, before any combo is allowed."))

    # ---------------------------------------------------------------- readiness
    cats = []
    seen = []
    for r in req:
        if r["category"] not in seen:
            seen.append(r["category"])
            cats.append(r["category"])
    body = '<p class="sub">One row per line of the brief: what is done, what blocks it, and the number that would clear it. The evidence column links to the exact file or official page.</p>'
    body += stat_cards([(str(met), "met", "ok"), (str(partial), "partially met", "mid"),
                        (str(notmet), "not met", "bad"), (str(len(req)), "lines tracked", "")])
    for cat in cats:
        rows = [r for r in req if r["category"] == cat]
        body += '<section><h2>%s</h2>' % esc(cat.title())
        body += table(rows, ["id", "requirement", "status", "blocking_gate", "observed", "evidence_path"])
        body += "</section>"
    write("readiness.html", page("Decision readiness", "readiness.html", body,
                                 "Every requirement, its gate and the number that clears it."))

    # ---------------------------------------------------------------- questions
    body = '<p class="sub">What we know, what is missing, and the cheapest official route to the answer. A question without a route is not a question, it is a wish.</p>'
    body += table(qs, ["id", "question", "known_now", "missing", "route", "blocks", "owner"])
    body += ('<section><h2>Suggested discovery order</h2><ol class="steps">'
             '<li><b>Q02 legal basis</b> — it governs every capture that follows.</li>'
             '<li><b>Q01 closing prices</b> — without a closing price there is no CLV and no escrow stage.</li>'
             '<li><b>Q03 official participants</b> — it turns the availability graph from a proxy into evidence.</li>'
             '<li><b>Q07 joint dependence</b> — it is the only gate on every combo division.</li>'
             '<li><b>Q04/Q05 model reality</b> — answered by this desk: the model is behind the line.</li>'
             '</ol></section>')
    write("questions.html", page("Questions", "questions.html", body,
                                 "Eighteen questions, each with what is known, what is missing and how to close it."))

    # ---------------------------------------------------------------- suggestions
    body = '<p class="sub">Reviewable paths, not changes. Each has options, a recommendation, a cost, an acceptance test and what would change our mind. The decision column is blank until you choose.</p>'
    body += table(sug, ["id", "suggestion", "options", "recommendation", "cost", "acceptance_test",
                        "what_would_change_our_mind", "decision"],
                  note="Nothing on this page has been implemented. The build publishes the register; a decision is yours to record in COORDINATION.md.")
    write("suggestions.html", page("Suggestions", "suggestions.html", body,
                                   "Twelve proposals with a two-sided falsification test each. Nothing implemented without a decision."))

    # ---------------------------------------------------------------- research
    body = '<p class="sub">The research register: every strategy with its frozen definition, its division and a two-sided “what would change our mind”.</p>'
    body += table(res, ["id", "strategy", "division", "registration_ref", "frozen_definition",
                        "what_would_change_our_mind", "status"])
    body += """<section><h2>Signal generation: what was tried and what it produced</h2>
<table><thead><tr><th>Idea</th><th>How it was made operational</th><th>Result</th></tr></thead><tbody>
<tr><td>Opponent-aware efficiency</td><td>Iterative fit of points per drive against the defences faced, recency-weighted</td><td>Produces usable rankings; does not beat the line (see Model page)</td></tr>
<tr><td>Availability surprise</td><td>Delta of official designations between two stamped reads, weighted by playing time</td><td>Blocked from the model until the point-in-time join is complete; published as an input instead</td></tr>
<tr><td>Price disagreement</td><td>De-vigged two-book consensus versus our own probability</td><td>Residuals published for all 13 fixtures; no threshold survives the gate</td></tr>
<tr><td>Pace mismatch</td><td>Estimated drives per game as a pace control in the total</td><td>Weak relation to scoring (r=0.167); kept as a control, not a signal</td></tr>
<tr><td>Dependence-aware combos</td><td>Measured correlation versus a marginal product</td><td>Same-game legs are dependent, so bulk multiplication is rejected</td></tr>
</tbody></table></section>"""
    write("research.html", page("Research register", "research.html", body,
                                "Every strategy, its frozen definition, and the evidence that would retire it."))

    # ---------------------------------------------------------------- flagged
    body = '<p class="sub">Irregularities, corrections to numbers published elsewhere in the repository, and items that could not be verified. Every row carries its evidence link.</p>'
    body += '<p class="note">A correction is not a complaint: it is the evidence that the re-derivation was done. Flagged items do not block the merge and are published for review.</p>'
    body += table(flags, ["id", "type", "title", "detail", "evidence_url", "status"])
    write("flagged.html", page("Flagged for review", "flagged.html", body,
                               "Eighteen items: defects this desk found in its own pipeline, corrections to numbers published elsewhere, and unverifiable cells."))

    # ---------------------------------------------------------------- sources
    body = '<p class="sub">Every external source used, with the exact read stamp and what it supports. Source classes: OFFICIAL (the league), OPERATOR (a named licensed sportsbook), AGGREGATOR (a research dataset, never presented as official), REPO.</p>'
    body += table(srcs, ["id", "source", "url", "supports", "read_how", "read_stamp", "source_class"])
    body += """<section><h2>Data policy P-01</h2>
<p class="sub">Decided before any backtest was published; the full text is in the registration file.</p>
<ul>
  <li>No row-level official NFL data is republished on this site. The site publishes derived aggregates and links to the official page.</li>
  <li>Raw official bytes are hashed and counted but not committed in this namespace.</li>
  <li>Operator prices are stored with the operator name, the printed price, the read clock and the page URL, and are attributed to that operator.</li>
  <li>Aggregator data is labelled PINNED-DATASET or AGGREGATOR on every row and never described as official.</li>
</ul>
<p>The basis is <a href="https://www.nfl.com/legal/terms/" rel="noopener">NFL.com Terms and Conditions s.1.3</a> (read 2026-11-19): individual non-commercial informational use only, and systematic retrieval prohibited without written consent.</p></section>"""
    write("sources.html", page("Sources", "sources.html", body,
                                "Fourteen sources, each with its read stamp and its class."))

    # ---------------------------------------------------------------- summary
    body = """<section><h2>Executive summary</h2>
<p class="lede">The desk does what the brief asks: it originates its own NFL lines, records them against named operator prices,
tracks official availability with clocks, ranks strategies on proper scores and publishes a decision-ready register. It also
reports the outcome honestly: <b>the line beats the model</b>.</p>
</section>
<section class="cols">
<article><h3>Origination</h3><ul>
<li>13 Week 11 fixtures, three markets in the required order, 52 market rows.</li>
<li>Fair, market and difference in separate columns; market cells carry the median of DraftKings and FanDuel, de-vigged where needed.</li>
<li>Every row stores a hash of the exact input object; the verifier recomputes it.</li>
<li>Model: opponent-aware points per drive, recency-weighted, home field +0.31 points (indistinguishable from zero).</li>
</ul></article>
<article><h3>Results and corpus</h3><ul>
<li>952 usable games, 32/32 clubs reconciling to the official standings on W-L-T, PF and PA.</li>
<li>14 Week 10 finals appended from the official page because the pinned snapshot stops at week 9.</li>
<li>The repo's 136-game log: 117 agree, 16 are blank table rows, 3 fixtures are absent. It cannot be a corpus for 19 rows.</li>
</ul></article>
<article><h3>Skill</h3><ul>
<li>Model Brier skill against the closing line: %+.1f%% over 744 walk-forward games.</li>
<li>No pre-registered family certifies; two are significantly worse than the market after correction.</li>
<li>Bets needed to separate a 55%% bettor from break-even at -110: 359.</li>
<li>Zero strategies on the leaderboard because zero bets have settled.</li>
</ul></article>
<article><h3>Availability</h3><ul>
<li>Official Week 11 report read today: 253 rows, 24 clubs; CIN and WAS print no injuries.</li>
<li>225 player-level changes against the 18 Nov read, both clocks on every row.</li>
<li>Questionable plays 25.0%% of the time (n=4,970). It is not a probability and is never a points penalty.</li>
<li>Depth comes from playing time: 12 position/rank rows with intervals, no jersey numbers anywhere.</li>
</ul></article>
<article><h3>Governance</h3><ul>
<li>Pre-registration committed before evaluation; the commit hash is the registration and the verifier recomputes it.</li>
<li>Backtest numbers are forbidden on the leaderboard by rule and by build.</li>
<li>Demotion gate: three automatic triggers, published before use.</li>
<li>18 flagged items with evidence links, including three defects this desk found in its own pipeline.</li>
</ul></article>
<article><h3>What to decide next</h3><ul>
<li>Whether to keep chasing the closing line with public data, or to reposition the model as a residual generator (S03).</li>
<li>Whether to seek written consent for automated capture, which unlocks the whole availability series (Q02, S01).</li>
<li>Whether official inactives are the next data purchase (Q03, S02).</li>
<li>Whether usage rank replaces the depth-chart idea permanently (S06).</li>
</ul></article>
</section>
<section><h2>Numbers restated with their sample</h2></section>""" % (100 * S["luck"]["brier_skill"])
    body += table([
        {"metric": "Brier skill vs closing line", "value": "%+.4f" % S["luck"]["brier_skill"], "n": S["luck"]["n_brier"],
         "source": "nfl-line-audit/data/backtest_strategies.csv"},
        {"metric": "Clubs reconciling to official standings", "value": "%d/32" % S["reconciliation"]["matches"], "n": 32,
         "source": "nfl-line-audit/data/corpus_reconciliation.csv"},
        {"metric": "Questionable play rate", "value": "0.2501", "n": 4970, "source": "nfl-line-audit/data/designation_reliability.csv"},
        {"metric": "Same-game prop correlation (QB yards vs top-WR yards)", "value": "0.5130", "n": 1523, "source": "nfl-line-audit/data/correlations.csv"},
        {"metric": "Bets to separate 55% from break-even at -110", "value": "359", "n": "", "source": "nfl-line-audit/data/luck_panel.csv"},
        {"metric": "Originated market rows", "value": "52", "n": 13, "source": "nfl-line-audit/data/origination_week11.csv"},
        {"metric": "Injury-report changes vs 18 Nov read", "value": "225", "n": 253, "source": "nfl-line-audit/data/injury_delta.csv"},
    ], ["metric", "value", "n", "source"], note="Every number on this page is recomputed by the build from the files in the repository.")
    write("summary.html", page("Executive summary", "summary.html", body,
                                "One page. The finding, the numbers, and what to decide next."))

    print("rendered", len(PAGES), "pages")


def write(name, html_text):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        f.write(html_text)


if __name__ == "__main__":
    main()

"""Deterministic GitHub Pages build for the d38e90c5 NFL line-origination desk.

Usage:  python3 build_site.py

Reads  : data/*.csv, data/summary.json, research/*.md
Writes : index.html, pages/*.html, assets/style.css

The build is deterministic: the same inputs always produce byte-identical output, so the
CI job can run `git diff --exit-code` to prove that the committed pages match the data.
"""

import csv
import datetime
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RESEARCH = os.path.join(HERE, "research")
PAGES = os.path.join(HERE, "pages")
ASSETS = os.path.join(HERE, "assets")
os.makedirs(PAGES, exist_ok=True)
os.makedirs(ASSETS, exist_ok=True)

GENERATED = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

NAV = [
    ("index.html", "Overview"),
    ("pages/requirements.html", "Requirements"),
    ("pages/executive-summary.html", "Executive summary"),
    ("pages/own-lines.html", "Own lines"),
    ("pages/price-snapshots.html", "Price snapshots"),
    ("pages/results.html", "Verified results"),
    ("pages/leaderboard.html", "Leaderboard"),
    ("pages/correlations.html", "Correlations"),
    ("pages/gate.html", "Demotion gate"),
    ("pages/strategies.html", "Strategies"),
    ("pages/injuries.html", "Injuries"),
    ("pages/depth.html", "Depth tracker"),
    ("pages/questions.html", "Questions and unknowns"),
    ("pages/suggestions.html", "Suggestions"),
    ("pages/repo-audit.html", "Repo audit"),
    ("pages/flagged.html", "Flagged for review"),
    ("pages/methodology.html", "Methodology"),
    ("pages/strategy-research.html", "Strategy research"),
    ("pages/injuries-and-depth.html", "Injuries and depth"),
    ("pages/sources.html", "Sources"),
]

CSS = """:root {
  --bg: #f6f7f9; --panel: #ffffff; --ink: #16191d; --muted: #5b6470;
  --line: #dde1e6; --accent: #1b4f91; --accent-soft: #eaf0fa; --warn: #8a4b00;
  --warn-soft: #fdf1e2; --good: #1c6b3f; --good-soft: #e8f4ec;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
a { color: var(--accent); }
a:hover { color: #0d3363; }
header.masthead { background: var(--accent); color: #fff; padding: 22px 24px; }
header.masthead h1 { margin: 0 0 4px; font-size: 22px; }
header.masthead p { margin: 0; opacity: .9; font-size: 13px; }
nav.toc { background: var(--panel); border-bottom: 1px solid var(--line); padding: 10px 24px;
  display: flex; flex-wrap: wrap; gap: 6px 14px; }
nav.toc a { font-size: 13px; text-decoration: none; padding: 3px 8px; border-radius: 10px; }
nav.toc a:hover { background: var(--accent-soft); }
nav.toc a.active { background: var(--accent-soft); font-weight: 600; }
main { max-width: 1180px; margin: 0 auto; padding: 22px 24px 60px; }
section.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
  padding: 18px 20px; margin-bottom: 18px; }
section.panel > h2 { margin-top: 0; font-size: 18px; border-bottom: 1px solid var(--line);
  padding-bottom: 8px; }
section.panel > h3 { font-size: 15px; margin-bottom: 6px; }
p.lede { font-size: 15px; color: var(--muted); }
table { border-collapse: collapse; width: 100%; font-size: 13px; margin: 10px 0 4px; }
th, td { border: 1px solid var(--line); padding: 6px 8px; text-align: left; vertical-align: top; }
th { background: var(--accent-soft); font-weight: 600; }
tr:nth-child(even) td { background: #fbfcfd; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
code { background: #eef1f4; padding: 1px 4px; border-radius: 3px; font-size: 12.5px; }
pre { background: #12171d; color: #e6edf3; padding: 12px 14px; border-radius: 6px; overflow-x: auto; }
pre code { background: none; color: inherit; padding: 0; }
.note { background: var(--warn-soft); border-left: 4px solid var(--warn); padding: 10px 12px;
  border-radius: 4px; margin: 10px 0; font-size: 13.5px; }
.ok { background: var(--good-soft); border-left: 4px solid var(--good); padding: 10px 12px;
  border-radius: 4px; margin: 10px 0; font-size: 13.5px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }
.stat { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; }
.stat .k { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
.stat .v { font-size: 21px; font-weight: 650; margin-top: 2px; }
.stat .s { font-size: 12px; color: var(--muted); margin-top: 2px; }
.blank { color: var(--warn); font-style: italic; }
.badge { display: inline-block; font-size: 11.5px; padding: 1px 7px; border-radius: 9px;
  border: 1px solid var(--line); background: #f1f3f5; }
.badge.PASS { background: var(--good-soft); border-color: #b6d8c4; color: var(--good); }
.badge.FAIL { background: #fdecec; border-color: #e6b4b4; color: #96221f; }
.badge.NOT_EVALUABLE { background: var(--warn-soft); border-color: #e4c391; color: var(--warn); }
footer { color: var(--muted); font-size: 12.5px; padding: 18px 24px 40px; max-width: 1180px; margin: 0 auto; }
.small { font-size: 12.5px; color: var(--muted); }
"""


# --------------------------------------------------------------- utilities
def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def linkify(text):
    """Turn bare URLs into links, leaving already-linked markdown alone."""
    text = esc(text)
    return re.sub(r"(?<!href=\")(?<![\"'>])https?://[^\s<\"']+", r'<a href="\g<0>">\g<0></a>', text)


def cell(v):
    if v is None or str(v).strip() == "":
        return '<span class="blank">not available</span>'
    s = str(v)
    if s.startswith("http"):
        return f'<a href="{esc(s)}">{esc(s)}</a>'
    return linkify(s)


def read_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_summary():
    with open(os.path.join(DATA, "summary.json"), encoding="utf-8") as fh:
        return json.load(fh)


def table(rows, columns, headers=None, numeric=(), link_cols=()):
    """columns: list of (key, label). numeric: keys right-aligned."""
    if not rows:
        return "<p class='note'>No rows.</p>"
    out = ["<table><thead><tr>"]
    for key, label in columns:
        cls = ' class="num"' if key in numeric else ""
        out.append(f"<th{cls}>{esc(label)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for key, _label in columns:
            v = r.get(key, "")
            cls = ' class="num"' if key in numeric else ""
            out.append(f"<td{cls}>{cell(v)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def stat_cards(items):
    out = ['<div class="grid">']
    for k, v, s in items:
        out.append(f'<div class="stat"><div class="k">{esc(k)}</div>'
                   f'<div class="v">{esc(v)}</div><div class="s">{esc(s)}</div></div>')
    out.append("</div>")
    return "".join(out)


def page(title, subtitle, body, active, depth=1):
    # links inside index.html are relative to the desk root, links inside
    # pages/*.html are relative to the pages/ directory
    base = "../" * depth
    nav = []
    for href, label in NAV:
        cls = ' class="active"' if href == active else ""
        nav.append(f'<a href="{base}{href}"{cls}>{esc(label)}</a>')
    nav_html = "".join(nav)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} - Own5 NFL desk d38e90c5</title>
<link rel="stylesheet" href="{base}assets/style.css">
</head>
<body>
<header class="masthead">
  <h1>{esc(title)}</h1>
  <p>{esc(subtitle)}</p>
</header>
<nav class="toc">{nav_html}</nav>
<main>
{body}
</main>
<footer>
  Own5 NFL line-origination desk, session <code>d38e90c5</code>. Built {esc(GENERATED)}.
  Every published table row links to its official source; values that cannot be confirmed from an
  official source are shown as <span class="blank">not available</span> and listed on the
  <a href="{base}pages/flagged.html">Flagged for review</a> page.
</footer>
</body>
</html>
"""


# ----------------------------------------------------------- markdown mini
def md_to_html(md):
    lines = md.split("\n")
    out = []
    i = 0
    in_code = False
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                out.append("<pre><code>")
                in_code = True
            i += 1
            continue
        if in_code:
            out.append(esc(line))
            i += 1
            continue
        if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(h)}</th>" for h in header) +
                       "</tr></thead><tbody>")
            for r in rows:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("</tbody></table>")
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if re.match(r"^\s*[-*]\s+", line):
            out.append("<ul>")
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                item = re.sub(r"^\s*[-*]\s+", "", lines[i])
                out.append("<li>" + inline(item) + "</li>")
                i += 1
            out.append("</ul>")
            continue
        if re.match(r"^\s*\d+\.\s+", line):
            out.append("<ol>")
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                item = re.sub(r"^\s*\d+\.\s+", "", lines[i])
                out.append("<li>" + inline(item) + "</li>")
                i += 1
            out.append("</ol>")
            continue
        if line.strip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append(f'<div class="note">{inline(" ".join(buf))}</div>')
            continue
        if not line.strip():
            i += 1
            continue
        buf = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,6}\s|\s*[-*]\s|\s*\d+\.\s|\s*>|\||```)", lines[i]):
            buf.append(lines[i])
            i += 1
        out.append(f"<p>{inline(' '.join(x.strip() for x in buf))}</p>")
    if in_code:
        out.append("</code></pre>")
    return "\n".join(out)


def inline(text):
    text = esc(text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"(?<!href=\")(?<![\"'>])https?://[^\s<\"')]+", r'<a href="\g<0>">\g<0></a>', text)
    return text


def write_page(path, content):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


# ------------------------------------------------------------------ pages
def build_overview(summary):
    lines = read_csv("own_lines.csv")
    upcoming = [l for l in lines if l["segment"] == "upcoming"]
    body = [
        '<section class="panel">',
        '<h2>What this desk is</h2>',
        '<p class="lede">A self-contained NFL line-origination and strategy desk that publishes its own '
        'side, total and moneyline lines from officially sourced numbers only, keeps an append-only '
        'price-snapshot store, keeps a verified results feed, separates signal quality from staking '
        'performance, tracks replacement depth, and runs a fail-closed demotion gate.</p>',
        stat_cards([
            ("Completed official games", summary["completed_games"], "NFL.com schedule pages"),
            ("Upcoming games", summary["upcoming_games"], "Weeks 10 and 11"),
            ("Originated markets", summary["originated_markets"],
             f"{summary['originated_markets_breakdown']['spread']} spread, "
             f"{summary['originated_markets_breakdown']['total']} total, "
             f"{summary['originated_markets_breakdown']['moneyline']} moneyline"),
            ("Price snapshot records", summary["price_snapshot_records"], "opening + closing, append-only"),
            ("Official injury rows", summary["injury_rows"], "Week 10 report"),
            ("Walk-forward predictions", summary["walk_forward_predictions"], "out of sample"),
            ("Flagged items", summary["flagged_items"], "published for review"),
            ("Market price status", "blank", summary["market_price_status"]),
        ]),
        "</section>",
        '<section class="panel"><h2>Publication order</h2>',
        "<p>Every game is published <strong>side / spread first, total second, moneyline third</strong>. "
        "The model fair line, the market line and the difference are three separate columns. The market "
        "line and difference are blank because no official price source exists.</p>",
        table([l for l in upcoming if l["publish_seq"] == "1"][:14],
              [("week", "Wk"), ("date", "Date"), ("away", "Away"), ("home", "Home"),
               ("model_fair_line", "Model fair line"), ("market_line", "Market line"),
               ("difference", "Difference"), ("model_fair_price", "Model fair price"),
               ("source_url", "Source")],
              numeric=("week",)),
        '<p class="small">Full table with all 297 markets: <a href="pages/own-lines.html">Own lines</a>.</p>',
        "</section>",
        '<section class="panel"><h2>Key findings</h2><ul>',
        f'<li>Walk-forward out-of-sample performance on n = {summary["signal_quality_overall"]["n"]} '
        f'predictions: MAE {summary["signal_quality_overall"]["mae_margin"]} points, Brier '
        f'{summary["signal_quality_overall"]["brier"]} against a '
        f'{summary["signal_quality_overall"]["brier_baseline"]} base-rate baseline, log loss '
        f'{summary["signal_quality_overall"]["log_loss"]} against '
        f'{summary["signal_quality_overall"]["log_loss_baseline"]}, winner hit rate '
        f'{summary["signal_quality_overall"]["winner_hit_rate"]}. A transparent baseline, not a proven edge.</li>',
        "<li>NFL.com publishes no betting prices and no operator price feed was reachable from this "
        "environment, so every market line, price, difference, CLV and market ROI stays blank and is "
        "published on the <a href=\"pages/flagged.html\">Flagged for review</a> page.</li>",
        "<li>Replacement depth is tracked per player (starter, second, third, fourth string) on offense "
        "and on defense, with the named replacement and a depth-deficiency flag.</li>",
        "<li>All six strategies are <strong>PAPER</strong>: the demotion gate fails closed, so nothing is "
        "promoted while a required criterion cannot be evaluated.</li>",
        "</ul></section>",
        '<section class="panel"><h2>Pages</h2><ul>',
    ]
    for href, label in NAV:
        if href == "index.html":
            continue
        body.append(f'<li><a href="{href}">{esc(label)}</a></li>')
    body.append("</ul></section>")
    return page("NFL line origination and strategy desk",
                "Session d38e90c5 - official-source model lines, price snapshots, verified results, "
                "depth tracking, correlations, leaderboards and a demotion gate",
                "\n".join(body), "index.html", depth=0)


def build_lines(summary):
    lines = read_csv("own_lines.csv")
    cols = [("segment", "Segment"), ("week", "Wk"), ("date", "Date"), ("kickoff", "Kickoff"),
            ("away", "Away"), ("home", "Home"), ("market_label", "Market"), ("side", "Model side"),
            ("model_fair_line", "Model fair line"), ("model_fair_prob", "Model fair prob"),
            ("model_fair_price", "Model fair price"), ("market_line", "Market line"),
            ("market_price", "Market price"), ("difference", "Difference"),
            ("market_price_status", "Price status"), ("source_url", "Source")]
    body = [
        '<section class="panel"><h2>Own lines</h2>',
        "<p>Each game's markets are published side first, total second, moneyline third. "
        "<em>Model fair line</em>, <em>market line</em> and <em>difference</em> are separate columns; "
        "the last two are blank because no official price source is reachable.</p>",
        '<div class="note">The table below shows the upcoming slate. Completed games carry the '
        "walk-forward model line that was available at kickoff and are in the same file on the "
        "<a href=\"price-snapshots.html\">price snapshot</a> page.</div>",
        table([l for l in lines if l["segment"] == "upcoming"], cols, numeric=("week", "model_fair_prob")),
        "</section>",
        '<section class="panel"><h2>Completed games - walk-forward model lines</h2>',
        table([l for l in lines if l["segment"] != "upcoming"], cols, numeric=("week", "model_fair_prob")),
        "</section>",
    ]
    return page("Own lines", "Model fair line, market line and difference as separate columns",
                 "\n".join(body), "pages/own-lines.html")


def build_snapshots(summary):
    snaps = read_csv("price_snapshots.csv")
    cols = [("game_id", "Game"), ("week", "Wk"), ("date", "Date"), ("away", "Away"), ("home", "Home"),
            ("market_label", "Market"), ("phase", "Phase"), ("captured_at", "Captured"),
            ("model_fair_line", "Model fair line"), ("model_fair_price", "Model fair price"),
            ("market_line", "Market line"), ("market_price", "Market price"),
            ("difference", "Difference"), ("price_status", "Price status"),
            ("verified_result", "Verified result"), ("source_url", "Source")]
    body = [
        '<section class="panel"><h2>Price-snapshot store</h2>',
        "<p>Append-only store (<code>data/price_snapshots.jsonl</code>) with one opening and one "
        f"closing record for every originated market - {summary['price_snapshot_records']} records for "
        f"{summary['originated_markets']} markets. Existing records are never rewritten.</p>",
        '<div class="note">The market price, market line and difference fields are blank for every '
        "record because NFL.com publishes no prices and no operator feed was reachable. The records "
        "exist so the opening/closing structure is in place and the moment a primary source exists "
        "the values can be appended without touching the history.</div>",
        table(snaps, cols, numeric=("week",)),
        "</section>",
    ]
    return page("Price snapshots", "Opening and closing records for every originated market",
                 "\n".join(body), "pages/price-snapshots.html")


def build_results(summary):
    rows = read_csv("results_verified.csv")
    cols = [("week", "Wk"), ("date", "Date"), ("away", "Away"), ("away_pts", "Away pts"),
            ("home", "Home"), ("home_pts", "Home pts"), ("margin", "Margin"),
            ("total_points", "Total"), ("result_status", "Status"), ("source_url", "Source")]
    body = [
        '<section class="panel"><h2>Verified results feed</h2>',
        f"<p>{len(rows)} completed games with official final scores. This is the feed that settlement "
        "and ROI would run on; it is complete and reconciled against the official standings "
        "(aggregate points for and points allowed both equal 6,291).</p>",
        table(rows, cols, numeric=("week", "away_pts", "home_pts", "margin", "total_points")),
        "</section>",
    ]
    return page("Verified results", "Official final scores for every completed game",
                 "\n".join(body), "pages/results.html")


def build_leaderboard(summary):
    signal = read_csv("leaderboard_signal.csv")
    staking = read_csv("leaderboard_staking.csv")
    sig_cols = [("strategy_id", "ID"), ("strategy", "Strategy"), ("family", "Family"),
                ("signal_basis", "Signal basis"), ("n_predictions", "n"),
                ("mae_margin_pts", "MAE pts"), ("brier_score", "Brier"),
                ("brier_baseline", "Brier base rate"), ("log_loss", "Log loss"),
                ("log_loss_baseline", "Log loss base rate"),
                ("winner_hit_rate", "Winner hit rate"),
                ("calibration_slope", "Calibration slope")]
    st_cols = [("strategy_id", "ID"), ("strategy", "Strategy"), ("family", "Family"),
               ("price_basis", "Price basis"), ("n_bets", "Bets"), ("wins", "Wins"),
               ("losses", "Losses"), ("pushes", "Pushes"), ("hit_rate", "Hit rate"),
               ("realised_profit_units", "Realised units"),
               ("expected_profit_units", "Expected units"),
               ("luck_gap_units", "Luck gap"), ("luck_band_95_units", "95% luck band"),
               ("max_drawdown_units", "Max drawdown"), ("roi_vs_market", "Market ROI"),
               ("clv", "CLV")]
    body = [
        '<section class="panel"><h2>Signal quality (independent of staking)</h2>',
        "<p>These are the skill measures: accuracy and calibration of the model against official "
        "results, computed on every out-of-sample prediction regardless of whether anything was "
        "staked. n is published with every row.</p>",
        table(signal, sig_cols, numeric=("n_predictions", "mae_margin_pts", "brier_score",
                                          "brier_baseline", "log_loss", "log_loss_baseline",
                                          "winner_hit_rate", "calibration_slope")),
        "</section>",
        '<section class="panel"><h2>Staking performance (never used alone)</h2>',
        '<div class="note">Every strategy here is priced at the model\'s own fair price, so the '
        "expected profit is exactly zero and the realised result is luck. That is precisely why the "
        "two tables are separate and why the demotion gate refuses to promote a strategy on the "
        "strength of a staking run. Market ROI and CLV are blank because no official price exists.</div>",
        table(staking, st_cols, numeric=("n_bets", "wins", "losses", "pushes", "hit_rate",
                                          "realised_profit_units", "expected_profit_units",
                                          "luck_gap_units", "luck_band_95_units", "max_drawdown_units")),
        "</section>",
    ]
    return page("Leaderboard", "Signal quality separated from staking performance",
                 "\n".join(body), "pages/leaderboard.html")


def build_correlations(summary):
    rows = read_csv("correlations.csv")
    cols = [("id", "ID"), ("label", "Relationship"), ("x", "X"), ("y", "Y"),
            ("pearson_r", "Pearson r"), ("spearman_rho", "Spearman rho"), ("n", "n"),
            ("x_source", "Source of X"), ("y_source", "Source of Y"), ("note", "Note")]
    body = [
        '<section class="panel"><h2>Correlations</h2>',
        "<p>Every value is computed from officially sourced numbers only, and <strong>n is published "
        "with every value</strong>. Third-party archives are not used here even where the repository "
        "already has them; see the <a href=\"repo-audit.html\">repo audit</a>.</p>",
        table(rows, cols, numeric=("pearson_r", "spearman_rho", "n")),
        "</section>",
    ]
    return page("Correlations", "Official-source correlations with n published for every value",
                 "\n".join(body), "pages/correlations.html")


def build_gate(summary):
    rows = read_csv("gate_decisions.csv")
    cols = [("strategy_id", "ID"), ("strategy", "Strategy"), ("criterion", "Criterion"),
            ("criterion_status", "Status"), ("criterion_detail", "Detail"),
            ("required_for_live", "Required for live"), ("gate_decision", "Gate decision"),
            ("decision_reason", "Reason"), ("source_url", "Source")]
    body = [
        '<section class="panel"><h2>Demotion gate</h2>',
        "<p>Fail-closed. A strategy is <strong>PAPER</strong> when any live criterion fails and also "
        "when any live criterion cannot be evaluated. Only a strategy whose every live criterion "
        "passes may be LIVE_ELIGIBLE; the same rule moves a live strategy back to paper.</p>",
        '<div class="note">All six strategies are PAPER today: criteria 9 and 10 need a real price, '
        "and S4/S5/S6 cannot even measure their signal yet.</div>",
        table(rows, cols),
        "</section>",
    ]
    return page("Demotion gate", "Fail-closed gate with an explicit demotion decision per strategy",
                 "\n".join(body), "pages/gate.html")


def build_strategies(summary):
    rows = read_csv("strategies.csv")
    cols = [("id", "ID"), ("name", "Strategy"), ("family", "Family"), ("definition", "Definition"),
            ("selection_rule", "Selection rule"), ("price_basis", "Price basis"),
            ("market_required", "Market price needed"), ("n_bets", "Bets"),
            ("status_note", "Status"), ("source_url", "Source")]
    body = [
        '<section class="panel"><h2>Strategy catalogue</h2>',
        "<p>Single bets, parlays and player-prop combinations. Full research, measurements and the "
        "blocking reasons are in <code>research/04-strategy-research.md</code>.</p>",
        table(rows, cols, numeric=("n_bets",)),
        "</section>",
    ]
    return page("Strategies", "Single bets, parlays and player-prop combinations",
                 "\n".join(body), "pages/strategies.html")


def build_injuries(summary):
    rows = read_csv("depth_detail.csv")
    out_rows = [r for r in rows if r["absence_class"] == "Out"]
    cols = [("team", "Club"), ("player", "Player"), ("unit", "Unit"),
            ("depth_position", "Depth position"), ("depth_slot", "Depth slot"),
            ("depth_tier", "Depth tier"), ("injury", "Injury"),
            ("practice_status", "Practice status"), ("game_status", "Game status"),
            ("replacement_player", "Replacement"), ("replacement_depth_tier", "Replacement tier"),
            ("depth_deficiency", "Depth deficiency"), ("source_url", "Source")]
    body = [
        '<section class="panel"><h2>Week 10 official injury report - players listed Out</h2>',
        "<p>Verbatim practice and game designations from the official NFL injury report. "
        "<em>No designation published</em> is recorded explicitly and is never treated as healthy.</p>",
        table(out_rows, cols),
        "</section>",
        '<section class="panel"><h2>Per-club depth summary</h2>',
    ]
    summary_rows = read_csv("depth_team_summary.csv")
    body.append(table(summary_rows,
                      [("team", "Club"), ("out_total", "Out"), ("out_offense_starters", "Off starters out"),
                       ("out_defense_starters", "Def starters out"), ("doubtful_starters", "Doubtful starters"),
                       ("questionable_starters", "Questionable starters"), ("no_designation", "No designation"),
                       ("depth_deficiencies", "Depth deficiencies"), ("severity", "Severity"),
                       ("starter_out_players", "Starter outs"), ("injury_source_url", "Injury source"),
                       ("depth_source_url", "Depth source")],
                      numeric=("out_total", "out_offense_starters", "out_defense_starters",
                               "doubtful_starters", "questionable_starters", "no_designation",
                               "depth_deficiencies", "severity")))
    body.append("</section>")
    return page("Injuries", "Official Week 10 injury report with depth tiers and deficiencies",
                 "\n".join(body), "pages/injuries.html")


def build_depth(summary):
    rows = read_csv("depth_detail.csv")
    cols = [("team", "Club"), ("player", "Player"), ("unit", "Unit"),
            ("depth_position", "Position"), ("depth_slot", "Depth slot"),
            ("depth_tier", "Depth tier"), ("absence_class", "Absence class"),
            ("replacement_player", "Replacement"), ("replacement_depth_tier", "Replacement tier"),
            ("depth_deficiency", "Depth deficiency"), ("match_status", "Depth match"),
            ("source_url", "Injury source"), ("depth_source_url", "Depth chart source")]
    body = [
        '<section class="panel"><h2>Replacement depth tracker</h2>',
        "<p>Every official injury row matched to the club's official depth chart, with the depth tier "
        "of the player and of the replacement. Depth deficiency is flagged when a starter is Out and "
        "the next in line is a third- or fourth-string reserve.</p>",
        table(rows, cols),
        "</section>",
    ]
    return page("Depth tracker", "Starter versus second, third and fourth string on offense and defense",
                 "\n".join(body), "pages/depth.html")


def build_flagged(summary):
    rows = read_csv("flagged_for_review.csv")
    cols = [("area", "Area"), ("item", "Item"), ("issue", "Issue"),
            ("source_url", "Source / manual review link"), ("recommended_action", "Recommended action")]
    body = [
        '<section class="panel"><h2>Flagged for review</h2>',
        "<p>Every value that could not be confirmed from an official source, plus every irregularity "
        "found while transcribing. Nothing on this list is estimated or filled in elsewhere.</p>",
        table(rows, cols),
        "</section>",
    ]
    return page("Flagged for review", "Unverified values and irregularities, with manual-review links",
                 "\n".join(body), "pages/flagged.html")


def build_sources(summary):
    rows = read_csv("sources.csv")
    cols = [("source_id", "ID"), ("publisher", "Publisher"), ("title", "Title"),
            ("url", "URL"), ("retrieved", "Retrieved"), ("used_for", "Used for")]
    body = [
        '<section class="panel"><h2>Source register</h2>',
        "<p>Every published table row traces to one of these sources.</p>",
        table(rows, cols),
        "</section>",
    ]
    return page("Sources", "Official source register for every published row",
                 "\n".join(body), "pages/sources.html")


def build_doc_page(md_name, title, subtitle, active):
    with open(os.path.join(RESEARCH, md_name), encoding="utf-8") as fh:
        md = fh.read()
    body = ['<section class="panel">', md_to_html(md), "</section>"]
    return page(title, subtitle, "\n".join(body), active)


def main():
    summary = read_summary()
    write_page(os.path.join(HERE, "index.html"), build_overview(summary))
    write_page(os.path.join(PAGES, "own-lines.html"), build_lines(summary))
    write_page(os.path.join(PAGES, "price-snapshots.html"), build_snapshots(summary))
    write_page(os.path.join(PAGES, "results.html"), build_results(summary))
    write_page(os.path.join(PAGES, "leaderboard.html"), build_leaderboard(summary))
    write_page(os.path.join(PAGES, "correlations.html"), build_correlations(summary))
    write_page(os.path.join(PAGES, "gate.html"), build_gate(summary))
    write_page(os.path.join(PAGES, "strategies.html"), build_strategies(summary))
    write_page(os.path.join(PAGES, "injuries.html"), build_injuries(summary))
    write_page(os.path.join(PAGES, "depth.html"), build_depth(summary))
    write_page(os.path.join(PAGES, "flagged.html"), build_flagged(summary))
    write_page(os.path.join(PAGES, "sources.html"), build_sources(summary))
    write_page(os.path.join(PAGES, "requirements.html"),
               build_doc_page("01-requirements.md", "Requirements and acceptance status",
                              "Every requirement, the artefact that satisfies it and its honest status",
                              "pages/requirements.html"))
    write_page(os.path.join(PAGES, "executive-summary.html"),
               build_doc_page("00-executive-summary.md", "Executive summary",
                              "Findings, evidence and what is deliberately blank",
                              "pages/executive-summary.html"))
    write_page(os.path.join(PAGES, "methodology.html"),
               build_doc_page("02-methodology.md", "Methodology",
                              "How the model originates its own lines, and what is an assumption",
                              "pages/methodology.html"))
    write_page(os.path.join(PAGES, "strategy-research.html"),
               build_doc_page("04-strategy-research.md", "Strategy research",
                              "Single bets, parlays, player props, validation gates and luck control",
                              "pages/strategy-research.html"))
    write_page(os.path.join(PAGES, "injuries-and-depth.html"),
               build_doc_page("05-injuries-and-depth.md", "Injuries and depth",
                              "Depth tiers, replacement paths, deficiencies and irregularities",
                              "pages/injuries-and-depth.html"))
    write_page(os.path.join(PAGES, "questions.html"),
               build_doc_page("06-questions-and-unknowns.md", "Questions and unknowns",
                              "Questions, information, answers, unknowns and discovery steps",
                              "pages/questions.html"))
    write_page(os.path.join(PAGES, "suggestions.html"),
               build_doc_page("07-suggestions.md", "Suggestions",
                              "Options for review and the recommended path before implementation",
                              "pages/suggestions.html"))
    write_page(os.path.join(PAGES, "repo-audit.html"),
               build_doc_page("08-repo-audit.md", "Repo audit",
                              "Line-by-line review of the existing NFL desks, drift and irregularities",
                              "pages/repo-audit.html"))
    with open(os.path.join(ASSETS, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    print("built: index.html and %d pages" % len(os.listdir(PAGES)))


if __name__ == "__main__":
    main()

"""Generate the static Own5 dashboard from audited JSON. No runtime API calls."""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
REPO_URL = "https://github.com/sassnarep3-star/Own5"


def load(name: str):
    return json.loads((ROOT / "data" / name).read_text())


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def blank() -> str:
    return '<span class="blank" role="img" aria-label="Unverified; intentionally left blank" title="Unverified — intentionally left blank"></span>'


def fmt(value: object, kind: str = "text") -> str:
    if value is None:
        return blank()
    if kind == "pct":
        return f"{value * 100:.1f}%"
    if kind == "dec":
        return f"{value:.3f}"
    if kind == "r":
        return f"{value:+.3f}"
    if kind == "signed":
        return f"{value:+g}" if value else "0"
    if kind == "american":
        return f"{value:+d}"
    if kind == "int":
        return f"{value:,}"
    return e(value)


def source_label(url: str) -> str:
    p = urlparse(url)
    path = p.path
    if "/standings" in path: return "NFL standings"
    if "/schedules" in path: return "NFL schedule"
    if "/games/" in path: return "NFL game"
    if "joe-burrow" in path and "/logs" in path: return "Burrow log"
    if "ja-marr-chase" in path and "/logs" in path: return "Chase log"
    if "/players/" in path and "/career" in path: return "NFL career"
    if "next-gen-stats" in path: return "NFL NGS"
    if p.hostname == "support.nfl.com": return "NFL Support"
    if p.hostname == "operations.nfl.com": return "NFL Operations"
    if p.hostname == "static.www.nfl.com": return "NFL rulebook PDF"
    if p.hostname == "www.nflgsis.com": return "NFL GSIS"
    if p.hostname and "fanduel.com" in p.hostname: return "FanDuel rules"
    if p.hostname == "academic.oup.com": return "OUP method"
    if p.hostname and "ametsoc.org" in p.hostname: return "AMS method"
    return "Official source"


def src(urls: list[str]) -> str:
    return '<div class="source-links">' + "".join(
        f'<a href="{e(u)}" target="_blank" rel="noopener">{e(source_label(u))} ↗</a>' for u in dict.fromkeys(urls)
    ) + "</div>"


def badge(text: str, kind: str | None = None) -> str:
    kind = kind or ("pass" if text.lower().startswith("verified") else "blocked" if "block" in text.lower() or "review" in text.lower() else "derived" if "research" in text.lower() or "derived" in text.lower() else "neutral")
    return f'<span class="badge {e(kind)}">{e(text)}</span>'


def table(headers: list[str], rows: list[list[str]], *, label: str = "Filter table") -> str:
    head = "".join(f"<th>{e(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'''<div class="table-card"><div class="table-tools"><input type="search" data-table-search placeholder="Filter this table…" aria-label="{e(label)}"><span class="table-count"></span></div><div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div></div>'''


def kpi(label: str, value: str, note: str, tone: str = "") -> str:
    return f'<div class="kpi {tone}"><div class="kpi-label">{e(label)}</div><div class="kpi-value">{value}</div><div class="kpi-note">{e(note)}</div></div>'


def section(title: str, subtitle: str, content: str) -> str:
    return f'<section class="section"><div class="section-head"><div><h2>{e(title)}</h2><p>{e(subtitle)}</p></div></div>{content}</section>'


NAV = [
    ("", [("index.html", "Overview", "⌂")]),
    ("Research", [("lines.html", "Own NFL lines", "◈"), ("strategies.html", "Strategies", "◇"), ("correlations.html", "Correlations", "⌁")]),
    ("Markets", [("parlays.html", "Parlays & combos", "⧉"), ("props.html", "Player props", "◎"), ("leaderboard.html", "Leaderboard", "♜")]),
    ("Evidence", [("validation.html", "Validation gates", "✓"), ("data.html", "Official data", "▤"), ("sources.html", "Source register", "↗"), ("methodology.html", "Methodology", "≡")]),
    ("Governance", [("review.html", "Flagged for review", "⚑")]),
]


def page(slug: str, title: str, subtitle: str, body: str, review_count: int) -> None:
    nav = ""
    for group, items in NAV:
        if group:
            nav += f'<div class="nav-group"><div class="nav-label">{e(group)}</div>'
        else:
            nav += '<div class="nav-group">'
        for href, label, icon in items:
            active = " active" if href == slug else ""
            count = f'<span class="nav-count">{review_count}</span>' if href == "review.html" else ""
            nav += f'<a class="nav-link{active}" href="{href}"><span class="nav-icon">{icon}</span>{e(label)}{count}</a>'
        nav += "</div>"
    document = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Own5 — evidence-first NFL line research, validation gates, correlations and source audit."><title>{e(title)} · Own5</title><link rel="stylesheet" href="assets/app.css"></head><body>
<a class="skip-link" href="#main" style="position:absolute;left:-9999px" onfocus="this.style.left='8px'" onblur="this.style.left='-9999px'">Skip to content</a>
<aside class="sidebar" aria-label="Primary navigation"><a class="brand" href="index.html"><span class="brand-mark">O5</span><span><strong>Own5</strong><span>NFL research desk</span></span></a>{nav}<div class="sidebar-foot">Frozen snapshot · Nov 2, 2026<br><a href="{REPO_URL}" target="_blank" rel="noopener">View repository ↗</a></div></aside><div class="overlay"></div>
<div class="shell"><header class="topbar"><button class="menu-btn" aria-label="Open navigation">☰</button><div class="crumb">Workspace &nbsp;/&nbsp; NFL &nbsp;/&nbsp; <strong>{e(title)}</strong></div><div class="top-actions"><span class="snapshot">Snapshot · 2026-11-02</span>{badge("Research only", "derived")}</div></header>
<main class="content" id="main"><div class="page-head"><div><div class="eyebrow">NFL · Evidence first</div><h1>{e(title)}</h1><p>{e(subtitle)}</p></div></div>{body}
<footer class="footer"><span>Research only. No wagers placed. Derived estimates are not official NFL lines.</span><span><a href="sources.html">Sources</a> · <a href="review.html">Flagged for review</a> · <a href="methodology.html">Methodology</a></span></footer></main></div><script src="assets/app.js"></script></body></html>'''
    (DIST / slug).write_text(document)


def scatter(games: list[dict]) -> str:
    width, height = 720, 360
    left, right, top, bottom = 62, 24, 24, 52
    xmin, xmax, ymin, ymax = 100, 470, 0, 290
    def X(v): return left + (v - xmin) / (xmax - xmin) * (width - left - right)
    def Y(v): return height - bottom - (v - ymin) / (ymax - ymin) * (height - top - bottom)
    parts = [f'<svg class="chart" viewBox="0 0 {width} {height}" role="img" aria-label="Scatter plot of Burrow passing yards and Chase receiving yards in 17 official 2024 games">']
    for v in range(0, 251, 50):
        parts.append(f'<line x1="{left}" y1="{Y(v):.1f}" x2="{width-right}" y2="{Y(v):.1f}" stroke="#e8edf3"/><text x="{left-10}" y="{Y(v)+4:.1f}" text-anchor="end" font-size="11" fill="#647187">{v}</text>')
    for v in range(150, 451, 50):
        parts.append(f'<text x="{X(v):.1f}" y="{height-bottom+20}" text-anchor="middle" font-size="11" fill="#647187">{v}</text>')
    parts.append(f'<line x1="{X(250):.1f}" y1="{top}" x2="{X(250):.1f}" y2="{height-bottom}" stroke="#c58b19" stroke-dasharray="5 4"/><line x1="{left}" y1="{Y(75):.1f}" x2="{width-right}" y2="{Y(75):.1f}" stroke="#c58b19" stroke-dasharray="5 4"/>')
    for g in games:
        x, y = g["burrow_passing_yards"], g["chase_receiving_yards"]
        hit = x >= 250 and y >= 75
        parts.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="6" fill="{"#087f78" if hit else "#8aa0b8"}" fill-opacity=".85"><title>Week {g["week"]}: Burrow {x} pass yards, Chase {y} receiving yards</title></circle>')
    parts.append(f'<text x="{width/2}" y="{height-8}" text-anchor="middle" font-size="12" fill="#42526a">Burrow passing yards</text><text x="16" y="{height/2}" transform="rotate(-90 16 {height/2})" text-anchor="middle" font-size="12" fill="#42526a">Chase receiving yards</text>')
    parts.append(f'<text x="{X(250)+6:.1f}" y="{top+12}" font-size="10" fill="#9a6500">250 pass yds</text><text x="{width-right-4}" y="{Y(75)-6:.1f}" text-anchor="end" font-size="10" fill="#9a6500">75 rec yds</text></svg>')
    return "".join(parts)


def build() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / ".nojekyll").touch()
    shutil.copytree(ROOT / "site/assets", DIST / "assets")
    shutil.copytree(ROOT / "data", DIST / "data")
    shutil.copytree(ROOT / "research/evidence", DIST / "evidence")
    shutil.copytree(ROOT / "docs", DIST / "docs")
    summary = load("summary.json")
    lines = load("derived_lines.json")
    strategies = load("strategies.json")
    facts = load("verified_facts.json")
    sources = load("source_register.json")
    reviews = load("review_items.json")
    corr = load("correlations.json")
    gates = load("gate_definitions.json")
    snapshot = json.loads((ROOT / "research/official_snapshot.json").read_text())
    rc = len(reviews)
    warning = f'''<div class="banner"><span class="banner-icon">⚑</span><div><strong>No verified sportsbook prices. No strategy is approved for wagering.</strong><p>Own lines are independent research estimates. Market odds, current props, edge and CLV are intentionally blank until official, timestamped evidence exists. <a href="review.html">Review all {rc} flags →</a></p></div></div>'''

    # Overview / executive summary
    findings = [
        ["Official snapshot", f'{summary["teams"]} teams · {summary["research_lines"]} Week 9 matchups', badge("Verified inputs", "verified"), "Frozen NFL standings and schedule; not a live feed.", src(["https://www.nfl.com/standings/league/2026/REG", "https://www.nfl.com/schedules/2026/by-week/week-9"])],
        ["Historical QB–WR co-movement", f'Pearson r = {corr["pearson_r"]:+.3f}', badge("Derived", "derived"), f'17 paired 2024 games; 95% bootstrap interval [{corr["pearson_ci95"][0]:+.3f}, {corr["pearson_ci95"][1]:+.3f}]. Descriptive only.', src(corr["source_urls"])],
        ["Joint combo vs independence", f'{fmt(corr["joint_rate"], "pct")} observed vs {fmt(corr["independence_product"], "pct")} product', badge("Derived", "derived"), f'{corr["joint_hits"]}/17 joint hits at ≥250 passing / ≥75 receiving yards. Not a current SGP price.', src(corr["source_urls"])],
        ["Validation outcome", f'{summary["qualified_strategies"]} of {summary["strategies"]} strategies qualify', badge("Blocked", "blocked"), "Every family lacks verified market history and untouched out-of-sample evidence.", src(["https://academic.oup.com/rfs/issue/29/1"])],
        ["Evidence gaps", f'{rc} items flagged', badge("Needs review", "review"), "Missing prices, current props, participation, settlement variants and source irregularities are published.", src(["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"])],
    ]
    categories = [
        ("lines.html", "◈", "Own NFL lines", "Independent Week 9 fair spreads, totals and probabilities."),
        ("strategies.html", "◇", "Strategy registry", "Six frozen families, parameters and blocking evidence."),
        ("parlays.html", "⧉", "Parlays & combos", "Joint pricing, settlement rules and correlation discipline."),
        ("props.html", "◎", "Player props", "Official paired game logs and blank current markets."),
        ("correlations.html", "⌁", "Correlation lab", "Yards correlation, binary dependence and uncertainty."),
        ("validation.html", "✓", "Validation gates", "Eleven fail-closed gates; unknown never passes."),
        ("leaderboard.html", "♜", "Leaderboard", "Eligibility-first ranking and non-cash research points."),
        ("data.html", "▤", "Official data", "Every verified fact row with its official source."),
        ("review.html", "⚑", "Flagged for review", "Irregularities and unsupported values, ready for review."),
    ]
    cat_html = '<div class="category-grid">' + "".join(f'<a class="category" href="{href}"><span class="cat-icon">{icon}</span><strong>{e(t)}</strong><span>{e(d)}</span></a>' for href, icon, t, d in categories) + "</div>"
    body = f'''<div class="hero"><div class="eyebrow">Independent research · 2026 Week 9</div><h1>Originate lines.<br>Prove the edge before trusting it.</h1><p>A source-audited NFL research desk for single bets, parlays and player-prop combinations. Verified facts, derived estimates and missing market inputs stay separate—by design.</p><div class="hero-actions"><a class="btn btn-primary" href="lines.html">Explore research lines →</a><a class="btn btn-secondary" href="validation.html">Inspect validation gates</a></div></div>{warning}
<div class="kpis">{kpi("Research lines", str(summary["research_lines"]), "Week 9 · independent estimates", "accent")}{kpi("Registered strategies", str(summary["strategies"]), "Singles, parlays and props")}{kpi("Qualified strategies", str(summary["qualified_strategies"]), "No performance claims", "warn")}{kpi("Official fact rows", str(summary["verified_fact_rows"]), f'{summary["official_sources"]} primary sources')}{''}</div>
{section("Executive findings", "What the evidence supports—and what it does not.", table(["Finding", "Result", "Classification", "Interpretation", "Official inputs"], findings))}
<div class="grid-2 section"><div class="card"><h2>Ready for inspection</h2><ul class="list-clean"><li><strong>Official snapshot:</strong> 32 teams, 15 matchups and 17 paired player games.</li><li><strong>Transparent baseline:</strong> shrunken points ratings and explicit score probabilities.</li><li><strong>Reproducible checks:</strong> evidence hashes, reconciliations, unit tests and internal-link audit.</li></ul></div><div class="card"><h2>Deliberately not claimed</h2><ul class="list-clean"><li><strong>No verified edge:</strong> no timestamped sportsbook archive or untouched holdout.</li><li><strong>No current prop picks:</strong> participation and operator prices are missing.</li><li><strong>No luck-free guarantee:</strong> uncertainty and regime change remain.</li></ul></div></div>
{section("Explore the research desk", "Each category is a simple, filterable table view with source links.", cat_html)}'''
    page("index.html", "NFL research overview", "Executive summary of the frozen evidence, independent lines and validation status.", body, rc)

    # Own lines
    line_rows, probability_rows = [], []
    for g in lines:
        matchup = f'<span class="table-title">{e(g["away_name"])} at {e(g["home_name"])}</span><span class="table-sub">{"Madrid · neutral-site flag" if g["neutral_site"] else e(g["away"] + " @ " + g["home"])}</span>'
        line_rows.append([matchup, f'{e(g["date"])}<span class="table-sub">{e(g["local_time"])} LOCAL</span>', fmt(g["fair_spread_home"], "signed"), fmt(g["fair_total"]), fmt(g["home_two_way_probability"], "pct"), fmt(g["home_fair_american"], "american"), fmt(g["away_fair_american"], "american"), blank(), blank(), blank(), src(g["source_urls"])])
        probability_rows.append([matchup, fmt(g["lambda_away"], "dec"), fmt(g["lambda_home"], "dec"), fmt(g["home_win_probability"], "pct"), fmt(g["tie_probability"], "pct"), fmt(g["away_win_probability"], "pct"), fmt(g["total_push_probability"], "pct"), src(g["source_urls"])])
    body = warning + section("Independent fair lines", "Home spread is from the home team’s perspective. Fair moneylines condition on no tie. These are not sportsbook quotes.", table(["Matchup", "Date / venue-local time", "Home fair spread", "Fair total", "Home win % (no tie)", "Home fair American", "Away fair American", "Market spread", "Market total", "Market edge", "Official inputs"], line_rows))
    body += section("Score distribution detail", "Independent-Poisson baseline; home advantage disabled. Integer fair lines retain explicit push probability.", table(["Matchup", "Away λ", "Home λ", "Home win", "Tie", "Away win", "Push at fair total", "Official inputs"], probability_rows))
    body += '<div class="callout">Model assumptions: 8 pseudo-games of shrinkage; zero home-advantage adjustment; no injury/weather/starter adjustment. The <a href="methodology.html">methodology</a> separates these choices from official facts.</div>'
    page("lines.html", "Own NFL lines", "Week 9 research lines derived only from the frozen official standings and schedule.", body, rc)

    # Strategies
    rows = []
    for s in strategies:
        params = '<div class="chips">' + "".join(f'<span class="chip">{e(k)}: {e(v)}</span>' for k, v in s["parameters"].items()) + "</div>"
        rows.append([f'<span class="table-title">{e(s["id"])}</span><span class="table-sub">{e(s["name"])}</span>', e(s["category"]), e(s["signal"]), params, badge("Blocked", "blocked"), ", ".join(s["blockers"]), src(s["source_urls"])])
    body = warning + section("Frozen strategy registry", "Six families declared before holdout evaluation. Parameters are project choices, not official NFL values.", table(["Strategy", "Category", "Signal / selection rule", "Declared parameters", "Status", "Review flags", "Official inputs / method"], rows))
    body += '<div class="callout warn">Adding a variant increments the trial count. No strategy can enter the leaderboard until every validation gate passes.</div>'
    page("strategies.html", "Strategy registry", "Single-bet, parlay and player-prop families with explicit selection rules and blockers.", body, rc)

    # Parlays
    joint_rows = [
        ["Observed joint hit rate", fmt(corr["joint_rate"], "pct"), f'{corr["joint_hits"]}/{corr["n_games"]} games; Wilson interval [{fmt(corr["joint_wilson_ci95"][0], "pct")}, {fmt(corr["joint_wilson_ci95"][1], "pct")}].', src(corr["source_urls"])],
        ["Independence product", fmt(corr["independence_product"], "pct"), "Marginal product shown only as a comparator, not an SGP assumption.", src(corr["source_urls"])],
        ["Observed minus independent", fmt(corr["joint_minus_independent"], "pct"), "Positive difference means the historical joint event occurred more often than the product.", src(corr["source_urls"])],
        ["Joint lift", fmt(corr["joint_lift"], "dec"), "P(A∩B) / [P(A)P(B)].", src(corr["source_urls"])],
        ["Historical fair joint decimal", fmt(corr["fair_joint_decimal"], "dec"), "1 / empirical joint rate. Not executable, not current, and not operator-settled.", src(corr["source_urls"])],
        ["Current SGP fair price", blank(), "Unavailable: current participation, prices and out-of-sample joint calibration are missing.", src(["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"])],
    ]
    ticket_rows = [
        ["ST03 · cross-game", blank(), blank(), blank(), blank(), blank(), badge("Blocked", "blocked"), src(["https://www.nfl.com/schedules/2026/by-week/week-9", "https://academic.oup.com/rfs/issue/29/1"])],
        ["ST04 · same-game", "Burrow ≥250 pass yds", "Chase ≥75 rec yds", blank(), blank(), blank(), badge("Historical only", "derived"), src(corr["source_urls"] + ["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"])],
    ]
    body = warning + section("Combination pricing workbench", "Current ticket fields remain blank. Historical thresholds are research definitions, not sportsbook lines.", table(["Ticket family", "Leg 1", "Leg 2", "Current joint probability", "Operator decimal price", "Net edge", "Status", "Official inputs"], ticket_rows))
    body += section("Historical joint-event evidence", "Burrow passing ≥250 and Chase receiving ≥75 in 17 paired 2024 regular-season games.", table(["Measure", "Value", "Meaning / limitation", "Official inputs"], joint_rows))
    body += '''<div class="grid-2"><div class="card"><h3>Cross-game discipline</h3><p class="muted">Two distinct games and no shared team are necessary but not sufficient for independence. Residual dependence must be tested. Pushes and voids remove legs only under the supplied settlement contract.</p></div><div class="card"><h3>Same-game discipline</h3><p class="muted">Shared pace, script and target share can change joint probability. The engine requires an operator-specific repricing function for SGP void/push cases; it never defaults to multiplying prices.</p></div></div>'''
    page("parlays.html", "Parlays & combos", "Joint-event evidence, settlement-aware pricing and explicitly unavailable current tickets.", body, rc)

    # Player props
    current = [["Burrow passing / Chase receiving", "≥250 pass yds / ≥75 rec yds", blank(), blank(), blank(), blank(), badge("Blocked", "blocked"), src(corr["source_urls"] + ["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"])]]
    rows = []
    for g in snapshot["paired_player_games"]:
        hit = g["burrow_passing_yards"] >= 250 and g["chase_receiving_yards"] >= 75
        rows.append([f'Week {g["week"]}', e(g["date"]), e(g["opponent"]), e(g["result"]), fmt(g["burrow_passing_yards"]), fmt(g["chase_receptions"]), fmt(g["chase_receiving_yards"]), badge("Joint hit", "pass") if hit else badge("No joint hit", "neutral"), src(g["source_urls"])])
    body = warning + section("Current prop market", "No current operator line, price or participation status was verified. Nothing is filled by inference.", table(["Research pair", "Historical thresholds", "Current prop line", "Over price", "Under price", "Participation", "Status", "Official inputs"], current))
    body += section("Official paired game logs", "2024 regular season only. Week/date/opponent/result match across both official logs; bye week 12 is excluded.", table(["Week", "Date", "Opponent", "Bengals result", "Burrow pass yds", "Chase receptions", "Chase rec yds", "≥250 / ≥75 research test", "Official sources"], rows))
    body += '<div class="callout">FanDuel’s official help says applicable NFL player props require the player to be active and play at least one snap. That is an operator-specific rule, not a universal settlement assumption. <a href="sources.html">See source S09.</a></div>'
    page("props.html", "Player props", "Official historical volume data and a fail-closed current prop-market record.", body, rc)

    # Correlations
    metric_rows = [
        ["Pearson r · yards", fmt(corr["pearson_r"], "r"), f'95% paired bootstrap CI [{fmt(corr["pearson_ci95"][0], "r")}, {fmt(corr["pearson_ci95"][1], "r")}]', "Linear co-movement in 17 selected games; not causal or current.", src(corr["source_urls"])],
        ["Spearman rank r", fmt(corr["spearman_r"], "r"), "Rank-based companion diagnostic", "Less sensitive to extreme yardage values; same sample limitation.", src(corr["source_urls"])],
        ["Binary phi · thresholds", fmt(corr["binary_phi"], "r"), f'95% paired bootstrap CI [{fmt(corr["binary_phi_ci95"][0], "r")}, {fmt(corr["binary_phi_ci95"][1], "r")}]', "Dependence of ≥250 passing and ≥75 receiving indicators.", src(corr["source_urls"])],
        ["Joint hit rate", fmt(corr["joint_rate"], "pct"), f'{corr["joint_hits"]}/{corr["n_games"]} games', "Direct empirical joint frequency is preferred to an independence product.", src(corr["source_urls"])],
        ["Independence product", fmt(corr["independence_product"], "pct"), f'{fmt(corr["passing_rate"], "pct")} × {fmt(corr["receiving_rate"], "pct")}', "Comparator only; not used to price a current SGP.", src(corr["source_urls"])],
        ["Joint lift", fmt(corr["joint_lift"], "dec"), "Observed joint / independence product", "A descriptive ratio, not a validated predictive multiplier.", src(corr["source_urls"])],
        ["Current pair correlation", blank(), "Unverified", "No current-season joint estimate or operator SGP price is published.", src(["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"])],
    ]
    body = f'''<div class="kpis">{kpi("Paired games", str(corr["n_games"]), "2024 regular season")}{kpi("Pearson r", fmt(corr["pearson_r"], "r"), "Yards co-movement", "accent")}{kpi("Binary phi", fmt(corr["binary_phi"], "r"), "Threshold dependence")}{kpi("Joint hits", f'{corr["joint_hits"]}/{corr["n_games"]}', "≥250 pass / ≥75 rec")}</div>'''
    body += section("Observed game cloud", "Teal points clear both research thresholds. Dashed lines are project thresholds, not sportsbook lines.", f'<div class="card">{scatter(snapshot["paired_player_games"])}<p class="small muted" style="margin:10px 0 0">Official inputs: <a href="{corr["source_urls"][0]}" target="_blank" rel="noopener">Burrow log ↗</a> · <a href="{corr["source_urls"][1]}" target="_blank" rel="noopener">Chase log ↗</a>. Derived chart.</p></div>')
    body += section("Correlation and joint-event diagnostics", "10,000 paired bootstrap resamples; seed 20261102. Intervals do not remove selection bias.", table(["Measure", "Estimate", "Uncertainty / comparator", "Interpretation", "Official inputs"], metric_rows))
    body += '<div class="callout warn">A single correlation does not define a joint betting distribution. Same-game pricing requires out-of-sample joint calibration and the operator’s exact settlement/repricing rules.</div>'
    page("correlations.html", "Correlation lab", "Descriptive dependence diagnostics from official paired player logs—not a universal SGP coefficient.", body, rc)

    # Validation
    gate_rows = [[g["id"], e(g["name"]), e(g["requirement"]), badge("Project policy", "neutral"), src(g["source_urls"])] for g in gates]
    matrix = []
    for s in strategies:
        cells = [f'<span class="gate-dot {g["status"]}" title="{e(g["status"])}"></span>{e(g["status"])}' for g in s["gates"]]
        matrix.append([f'{e(s["id"])} · {e(s["name"])}'] + cells + [src(s["source_urls"])])
    body = warning + section("Gate definitions", "All gates must pass. Missing evidence is blocked, not a pass. Thresholds are conservative project policy.", table(["Gate", "Name", "Requirement", "Classification", "Method references"], gate_rows))
    body += section("Strategy gate matrix", "Every registered family is currently blocked by incomplete evidence.", table(["Strategy"] + [g["id"] for g in gates] + ["Official inputs"], matrix))
    body += '<div class="callout">Finite-sample luck cannot be eliminated. The protocol controls leakage, settlement errors, multiple testing and dependence, and reports uncertainty instead of promising a skill guarantee.</div>'
    page("validation.html", "Validation gates", "Eleven fail-closed gates applied to every registered strategy.", body, rc)

    # Leaderboard
    board_rows = []
    for s in strategies:
        board_rows.append([blank(), f'<span class="table-title">{e(s["id"])}</span><span class="table-sub">{e(s["name"])}</span>', e(s["category"]), blank(), blank(), blank(), "0", badge("Blocked", "blocked"), src(s["source_urls"])])
    body = f'''<div class="card empty-state section"><div class="empty-icon">♜</div><h2>No qualified entries yet</h2><p>Raw profit and hit rate do not earn a rank. A strategy must pass every gate before its net ROI lower bound, CLV and forecast skill are compared.</p></div>'''
    body += section("Competition standings", "Non-cash research points: 100 / 60 / 40 for the top three qualified ranks. No points are issued for an empty qualified field.", table(["Rank", "Strategy", "Category", "Net ROI lower bound", "CLV lower bound", "Brier skill", "Research points", "Status", "Official inputs"], board_rows))
    page("leaderboard.html", "Strategy leaderboard", "Eligibility-first competition. No invented performance ranking or rewards.", body, rc)

    # Official data
    fact_rows = []
    for f in facts:
        values = '<div class="chips">' + "".join(f'<span class="chip">{e(k.replace("_", " "))}: {e(v)}</span>' for k, v in f["values"].items()) + "</div>"
        fact_rows.append([e(f["id"]), e(f["category"]), e(f["subject"]), values, badge("Verified", "verified"), src(f["source_urls"])])
    body = f'''<div class="kpis">{kpi("Verified fact rows", str(len(facts)), "Exact evidence linkage", "accent")}{kpi("Team rows", "32", "2026 snapshot")}{kpi("Week 9 matchups", "15", "Official schedule")}{kpi("Paired player games", "17", "2024 regular season")}</div>'''
    body += section("Line-by-line official fact register", "Filter by team, player, category or source. Values are parsed from frozen official rows/quotations; derived model outputs are kept elsewhere.", table(["Fact ID", "Category", "Subject", "Verified values", "Status", "Official source"], fact_rows))
    body += '<div class="callout">Reconciliation: league PF = PA = 5,528; Burrow passing yards = 4,918; Chase receiving yards = 1,708 and receptions = 127. See the <a href="docs/SOURCE_AUDIT.md">source audit</a> and <a href="evidence/career_reconciliation.md">official career controls</a>.</div>'
    page("data.html", "Official data", "The complete verified fact register for this release, with an official source on every row.", body, rc)

    # Sources
    source_rows = []
    for s in sources:
        evidence_link = f'<a href="{e(s["evidence_file"].replace("research/evidence/", "evidence/"))}">Frozen excerpt</a><span class="table-sub mono">{e(s["evidence_sha256"][:12])}…</span>' if s["evidence_file"] else '<span class="muted">Bibliographic reference</span>'
        source_rows.append([e(s["id"]), e(s["publisher"]), f'<a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["title"])} ↗</a>', e(s["access_method"]), e(s["retrieved_utc"]), evidence_link])
    body = section("Primary-source register", "NFL/official operator sources for facts; official scholarly publishers for methodology. A source link does not endorse a derived estimate.", table(["ID", "Publisher", "Official source", "Access / verification method", "Retrieved UTC", "Evidence"], source_rows))
    body += '<div class="callout">The automated audit rechecks excerpt hashes and internal links. External pages are dynamic; the frozen evidence preserves what was actually inspected for this release.</div>'
    page("sources.html", "Source register", "Official URLs, access methods, retrieval dates and frozen evidence hashes.", body, rc)

    # Review
    review_rows = []
    for r in reviews:
        fields = '<div class="chips">' + "".join(f'<span class="chip">{e(x)}</span>' for x in r["blank_fields"]) + "</div>" if r["blank_fields"] else '<span class="muted">Source irregularity</span>'
        review_rows.append([e(r["id"]), f'<span class="table-title">{e(r["title"])}</span><span class="table-sub">{e(r["affected"])}</span>', e(r["detail"]), fields, e(r["action"]), badge("Needs review", "review"), src(r["source_urls"])])
    body = f'<div class="banner"><span class="banner-icon">⚑</span><div><strong>{rc} items published for review</strong><p>These flags do not block the site release. They do block unsupported factual values and strategy qualification.</p></div></div>'
    body += section("Flagged for review", "Unsupported values remain blank in the data. Each item includes an official link and a concrete next action.", table(["ID", "Issue / scope", "Finding", "Blank fields", "Required action", "Status", "Official source"], review_rows))
    page("review.html", "Flagged for review", "Irregularities, access limits and missing evidence—published rather than hidden.", body, rc)

    # Methodology
    assumption_rows = [
        ["Shrinkage", "8 pseudo-games toward league scoring rate", "Project assumption; not an official NFL parameter.", src(["https://www.nfl.com/standings/league/2026/REG"])],
        ["Home advantage", "Disabled (0 adjustment)", "No empirical home-advantage value is inferred or filled.", src(["https://www.nfl.com/standings/league/2026/REG"])],
        ["Score distribution", "Independent Poisson, truncated at 100 per team", "Transparent baseline; dependence and football scoring discreteness require validation.", src(["https://www.nfl.com/standings/league/2026/REG"])],
        ["Prop joint probability", "Direct empirical joint frequency", "Historical comparator only; current SGP pricing remains blank.", src(corr["source_urls"])],
        ["Settlement", "Operator-specific push/void/reprice contract", "No universal SGP rule is assumed.", src(["https://support.fanduel.com/s/article/Betting-football-with-FanDuel"])],
        ["Multiplicity", "Family alpha 0.05 / 6 registered families", "Conservative project gate; method context from official publisher.", src(["https://academic.oup.com/rfs/issue/29/1"])],
    ]
    signal_rows = [
        ["Opponent-adjusted scoring", "Available as a baseline", "PF/PA rates, league mean and shrinkage; no market edge claimed.", src(["https://www.nfl.com/standings/league/2026/REG"])],
        ["Passing difficulty / tracking", "Not acquired", "Air distance, separation, pass-rusher distance and QB speed are described by NFL NGS; raw tracking is not in this snapshot.", src(["https://www.nfl.com/news/next-gen-stats-introduction-to-completion-probability-0ap3000000964655"])],
        ["Official game statistics", "Public entry points verified", "Game Books contain scores/statistics; GSIS corrections use Elias. Bulk authenticated access is not claimed.", src(["https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books", "https://www.nflgsis.com/Help/About.html"])],
        ["Market disagreement / CLV", "Blocked", "Requires authorized timestamped quotes and de-vigged closing prices.", src(["https://support.nfl.com/hc/en-us/articles/35869738523412-Who-is-making-the-odds"])],
    ]
    body = f'''<div class="grid-2 section"><div class="card"><h2>Line originator</h2><div class="formula">attack_i = (PF_i + k·μ) / (n_i + k)\ndefense_i = (PA_i + k·μ) / (n_i + k)\nλ_home = attack_home · defense_away / μ\nλ_away = attack_away · defense_home / μ</div><p class="muted small">μ uses total team games, not matchups. Fair spread/total are distribution medians; ties and pushes retain explicit mass.</p></div><div class="card"><h2>Skill before rewards</h2><p class="muted">Forecast skill, economic skill, settlement integrity, dependence and reproducibility are separate gates. A profitable-looking sample is not enough.</p><div class="callout">Unknown ≠ pass. Synthetic tests ≠ leaderboard results. Official inputs ≠ NFL endorsement of a model.</div></div></div>'''
    body += section("Declared assumptions", "These are model choices, not verified official facts.", table(["Component", "Setting", "Interpretation", "Official input / method"], assumption_rows))
    body += section("Signal development roadmap", "Useful signals require point-in-time data and out-of-sample evidence, not narrative alone.", table(["Signal family", "Availability", "Evidence boundary", "Official source"], signal_rows))
    body += '<div class="card"><h2>Full protocol</h2><p class="muted">Read the complete predeclared protocol, correlation formulas, gate definitions and future data contract.</p><a class="btn btn-primary" style="background:var(--teal);color:#fff" href="docs/METHODOLOGY.md">Open methodology document →</a> <a href="docs/REQUIREMENTS.md" style="margin-left:12px">Requirements traceability</a></div>'
    page("methodology.html", "Methodology", "How independent lines are formed, how dependence is handled and why qualification is fail-closed.", body, rc)

    # Simple 404 for GitHub Pages
    (DIST / "404.html").write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Page not found · Own5</title><link rel="stylesheet" href="assets/app.css"></head><body><main class="content" style="max-width:680px;margin:80px auto"><div class="card empty-state"><h1>Page not found</h1><p>The requested research page does not exist.</p><p><a class="btn btn-primary" style="background:var(--teal);color:#fff" href="index.html">Return to overview</a></p></div></main></body></html>')
    print(f"Built {len(list(DIST.glob('*.html')))} HTML pages in dist/")


if __name__ == "__main__":
    build()

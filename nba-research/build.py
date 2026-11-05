#!/usr/bin/env python3
"""Deterministic static dashboard builder. No JavaScript, network or secrets."""
from __future__ import annotations

import csv
import hashlib
import html
import json
import posixpath
from pathlib import Path
from urllib.parse import urlparse

import engine

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
AUDIT = ROOT / "audit"
AS_OF = engine.AS_OF


def e(x: object) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def read(name: str, folder: Path = DATA) -> list[dict[str, str]]:
    with (folder / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def jread(name: str, folder: Path = DATA) -> dict:
    with (folder / name).open(encoding="utf-8") as f:
        return json.load(f)


def link(page_path: str, target: str) -> str:
    return posixpath.relpath(target, posixpath.dirname(page_path) or ".")


def source_label(url: str) -> str:
    host = urlparse(url).netloc.replace("www.", "")
    return host or "source"


def table(rows: list[dict], caption: str, columns: list[str] | None = None,
          source_field: str = "source_url", review_field: str | None = "review_url",
          csv_name: str | None = None, csv_folder: str = "../data") -> str:
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
    # Put provenance last, but keep every requested data column.
    special = [c for c in (source_field, review_field) if c and c in columns]
    cols = [c for c in columns if c not in special] + special
    if not cols and rows:
        cols = list(rows[0].keys())
    head = "".join(f'<th scope="col">{e(c.replace("_", " "))}</th>' for c in cols)
    body = []
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c, "")
            if c in special and v:
                label = "Review" if c == review_field and review_field else source_label(v)
                cells.append(f'<td class="source"><a href="{e(v)}" target="_blank" rel="noopener noreferrer">{e(label)} ↗</a></td>')
            elif v == "" or v is None:
                cells.append('<td><span class="blank" title="Intentionally blank; see review flags">blank — unverified</span></td>')
            else:
                cls = ' class="num"' if isinstance(v, (int, float)) or (isinstance(v, str) and v.replace(".", "", 1).replace("-", "", 1).isdigit()) else ""
                cells.append(f"<td{cls}>{e(v)}</td>")
        if not any(r.get(c) for c in special):
            raise ValueError(f"Table row lacks a provenance link: {caption} {r}")
        body.append("<tr>" + "".join(cells) + "</tr>")
    download = ""
    if csv_name:
        download = f' <a class="download" href="{e(csv_folder + "/" + csv_name)}" download>Download CSV ↓</a>'
    empty = '<p class="empty-state">No eligible rows. Missing evidence is not filled with placeholder performance.</p>' if not rows else ""
    return f'<section class="table-panel"><div class="table-head"><h2>{e(caption)}</h2>{download}</div><div class="table-wrap"><table><caption>{e(caption)}. Every row carries a source or review link; blank cells are intentional and flagged.{download}</caption><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>{empty}</section>'


NAV = [
    ("index.html", "Overview"),
    ("pages/lines.html", "Own lines"),
    ("pages/correlations.html", "Correlations"),
    ("pages/strategies.html", "Strategies"),
    ("pages/leaderboard.html", "Leaderboard"),
    ("pages/teams.html", "Teams"),
    ("pages/players.html", "Players"),
    ("pages/evidence.html", "Evidence"),
    ("pages/audit.html", "Repo audit"),
    ("pages/review.html", "Flagged for review"),
    ("pages/methodology.html", "Methodology"),
]


def page(page_path: str, title: str, subtitle: str, body: str) -> str:
    nav = []
    for target, label in NAV:
        active = target == page_path
        attrs = ' aria-current="page" class="active"' if active else ''
        nav.append(f'<a href="{e(link(page_path, target))}"{attrs}>{e(label)}</a>')
    hub = link(page_path, "../index.html")
    css = link(page_path, "assets/style.css")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · NBA Line Research</title><meta name="description" content="{e(subtitle)}">
<link rel="stylesheet" href="{e(css)}"></head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap header-inner"><div><p class="eyebrow">Own5 · evidence-first research</p><h1>{e(title)}</h1><p class="subtitle">{e(subtitle)}</p></div><div class="stamp"><span>Frozen snapshot</span><strong>{AS_OF}</strong><span>No bets placed</span></div></div>
<nav class="wrap nav" aria-label="Dashboard sections">{"".join(nav)}</nav></header>
<main id="main" class="wrap">{body}</main>
<footer class="site-footer"><div class="wrap"><p>Independent research. Not affiliated with the NBA or any sportsbook. Experimental lines are not betting advice. Blank means unverified, never zero.</p><p><a href="{e(hub)}">Own5 hub</a> · <a href="https://github.com/sassnarep3-star/Own5" target="_blank" rel="noopener noreferrer">Repository</a> · <a href="{e(link(page_path, "pages/review.html"))}">Flagged for review</a></p></div></footer>
</body></html>'''


def cards(items: list[tuple[str, str, str]]) -> str:
    return '<div class="cards">' + "".join(f'<article class="card"><span>{e(label)}</span><strong>{e(value)}</strong><small>{e(note)}</small></article>' for label, value, note in items) + '</div>'


def note(text: str, kind: str = "note") -> str:
    return f'<aside class="{e(kind)}">{text}</aside>'


def bullets(items: list[str]) -> str:
    return '<ul class="findings">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def build() -> dict:
    summary = engine.build()
    d = {p.name: read(p.name) for p in DATA.glob("*.csv")}
    audit_summary = jread("scan_summary.json", AUDIT)
    findings = read("findings.csv", AUDIT)
    inventory = read("file_inventory.csv", AUDIT)
    broken = jread("broken_link_examples.json", AUDIT)
    lines = d["lines.csv"]; comp = d["market_comparison.csv"]; corr = d["correlations.csv"]; props = d["prop_combinations.csv"]
    strategies = d["strategies.csv"]; gates = d["gates.csv"]; flags = d["flags.csv"]; power = d["power.csv"]
    requirements = read("requirements.csv")
    pages: dict[str, str] = {}

    def add(path: str, title: str, subtitle: str, body: str) -> None:
        pages[path] = page(path, title, subtitle, body)

    # Overview / executive summary
    orl = next(r for r in lines if r["game_id"] == "0022600187")
    mia = next(r for r in lines if r["game_id"] == "0022600188")
    pooled_3pt = next(r for r in corr if r["scope"] == "Pooled (descriptive)" and r["x"] == "pts" and r["y"] == "tpm")
    centered_ast = next(r for r in corr if r["scope"] == "Player-centered pooled" and r["x"] == "pts" and r["y"] == "ast")
    pooled_ast = next(r for r in corr if r["scope"] == "Pooled (descriptive)" and r["x"] == "pts" and r["y"] == "ast")
    ed_combo = next(r for r in props if r["player"] == "Anthony Edwards" and r["combination"] == "PTS>=25 + 3PM>=3")
    body = cards([
        ("Official teams", str(summary["teams"]), "Current + prior season tables"),
        ("Player-games", str(summary["player_games"]), "Two selected high-usage players"),
        ("Archived prices", str(summary["market_prices"]), "Two games; not executable"),
        ("Integrity checks", f'{summary["integrity_passed"]}/{summary["integrity_checks"]}', "All passed"),
        ("Strategies", str(summary["strategies"]), "Predeclared; all blocked"),
        ("Certified / rewarded", str(summary["certified_strategies"]), "Leaderboard intentionally empty"),
        ("Review flags", str(summary["flags"]), "Open limitations are visible"),
        ("Repo findings", str(audit_summary["findings"]), f'{audit_summary["files"]} files scanned'),
    ])
    body += '<section class="panel"><h2>Executive summary</h2>' + bullets([
        f'<strong>The evidence is reconciled, but no edge is certified.</strong> Fifteen official-source integrity checks pass across 30 teams, 125 selected player-games, two scheduled games and 12 archived FanDuel prices. The settled-bet ledger is empty, so ROI, CLV, Deflated Sharpe, PBO, ranks and rewards remain blank.',
        f'<strong>Own lines are experimental.</strong> The neutral-baseline model projects Orlando {orl["projected_away_points"]} at Phoenix {orl["projected_home_points"]} (fair PHX {orl["fair_home_spread"]}, total {orl["fair_total"]}) and Miami {mia["projected_away_points"]} at Golden State {mia["projected_home_points"]} (fair GSW {mia["fair_home_spread"]}, total {mia["fair_total"]}). These are point estimates, not calibrated probabilities or recommendations. Missing availability, roster drift and the uncalibrated margin distribution are flagged.',
        f'<strong>Dependence matters and aggregation can mislead.</strong> Pooled points–threes correlation is {pooled_3pt["pearson_r"]}. Points–assists falls from {pooled_ast["pearson_r"]} pooled to {centered_ast["pearson_r"]} after player centering. Edwards PTS≥25 + 3PM≥3 hits {ed_combo["joint_probability"]} jointly versus an independence product of {ed_combo["independence_product"]} (lift {ed_combo["joint_lift"]}). Positive dependence means multiplying marginals <em>understates</em> the joint hit probability; it does not validate a parlay price.',
        f'<strong>Luck cannot be eliminated by a hot streak.</strong> At a hypothetical -110 break-even, detecting a true 55% hit rate with 80% exact power requires {next(r["minimum_independent_bets"] for r in power if r["alternative_hit_probability"]=="0.55" and r["alpha"]=="0.050000")} independent bets unadjusted, or {next(r["minimum_independent_bets"] for r in power if r["alternative_hit_probability"]=="0.55" and r["alpha"]=="0.006250")} under a 5%/8 Bonferroni screening scenario. Eight candidates are registered; every strategy fails the outcome, dependence, calibration and replication gates.',
        f'<strong>The repository audit is broad but scoped.</strong> Every baseline file and line was structurally scanned: {audit_summary["lines"]:,} lines, {audit_summary["python_files"]} Python files, {audit_summary["csv_files"]} CSVs and {audit_summary["html_files"]} HTML files. Syntax/JSON/JS checks pass. The audit found {audit_summary["broken_internal_links"]} inherited directory links without an index page and {audit_summary["findings"]} findings; shared broken links are repaired only in final integration and reverified.',
    ]) + '</section>'
    body += note('<strong>Decision:</strong> publish the research and blocked leaderboard; do not place bets or award rewards. The next evidence required is a point-in-time historical game/market ledger, complete availability, exact-leg dependence validation and a frozen prospective replication window.', 'decision')
    body += table(lines, "Experimental own lines", csv_name="lines.csv", csv_folder="data")
    body += table([r for r in gates if r["status"] == "BLOCKED"], "Blocking validation gates", csv_name="gates.csv", csv_folder="data")
    body += table([r for r in flags if r["severity"] == "High"], "Highest-priority review flags", csv_name="flags.csv", csv_folder="data")
    add("index.html", "NBA line-origination research", "Verified evidence, experimental lines, dependence-aware analysis and fail-closed validation.", body)

    # Own lines
    body = note('Model: shrink current offense/defense/pace toward a possession-weighted prior with K=20; expected pace is the matchup average; each team’s points per 100 is the average of its offense and the opponent’s defense. Home advantage is a disclosed zero baseline with ±2-point sensitivity. Win probability and EV are intentionally blank because no calibrated scoring distribution is verified.')
    body += table(lines, "Originated spread and total", csv_name="lines.csv")
    body += table(comp, "Archived market comparison", csv_name="market_comparison.csv")
    body += table(d["sensitivity.csv"], "Home-advantage sensitivity scenarios", csv_name="sensitivity.csv")
    body += table(d["ratings.csv"], "Shrunk team ratings", csv_name="ratings.csv")
    add("pages/lines.html", "Own lines and market comparison", "Point estimates only; archived prices are not executable quotes.", body)

    # Correlations
    body = note('Intervals are conditional player-stratified moving-block bootstraps (1,000 replicates, block length 5, seed 20261105), not population-generalizable NBA estimates. Centered pooled intervals are omitted rather than bootstrap centered values as if they were raw observations. Exact binomial combo intervals assume independent games within a player and are descriptive only.')
    body += table(corr, "Continuous stat correlations", csv_name="correlations.csv")
    body += table(props, "Player-prop combination hit rates", csv_name="prop_combinations.csv")
    body += table(d["dependence_diagnostics.csv"], "Serial diagnostic — not parlay independence evidence", csv_name="dependence_diagnostics.csv")
    add("pages/correlations.html", "Correlations and prop combinations", "Per-player, player-centered and joint-event evidence with explicit dependence limits.", body)

    # Strategies
    body = note(f'Pre-registration SHA-256: <code>{summary["preregistration_sha256"]}</code>. Rules were declared before any settled-bet evaluation. Any later parameter search must be registered before outcomes and increases the trial family.')
    body += table(strategies, "Registered strategy catalog", csv_name="strategies.csv")
    body += table(gates, "Ten fail-closed validation gates", csv_name="gates.csv")
    body += table(power, "Exact binomial power and illustrative streaks", csv_name="power.csv")
    add("pages/strategies.html", "Strategies and validation gates", "Singles, cross-game parlays and player-prop combinations; zero certified entries.", body)

    # Leaderboard
    reward_rows = [
        {"tier":"Gold badge","eligibility":"Rank 1 among certified strategies; at least 1 certified entry","reward":"Non-cash digital badge","cash_amount":"","status":"Policy only; no winner","source_url":engine.DSR_URL,"flag_id":"R09"},
        {"tier":"Silver badge","eligibility":"Rank 2 among certified strategies; at least 2 certified entries","reward":"Non-cash digital badge","cash_amount":"","status":"Policy only; no winner","source_url":engine.DSR_URL,"flag_id":"R09"},
        {"tier":"Bronze badge","eligibility":"Rank 3 among certified strategies; at least 3 certified entries","reward":"Non-cash digital badge","cash_amount":"","status":"Policy only; no winner","source_url":engine.DSR_URL,"flag_id":"R09"},
        {"tier":"Cash prize pool","eligibility":"Requires verified funding and payout mechanism","reward":"","cash_amount":"","status":"Unverified; not offered","source_url":engine.DSR_URL,"flag_id":"R09"},
    ]
    scoring_rows = [
        {"rule":"Primary score","definition":"Deflated Sharpe Ratio using the full effective comparable trial family; require >=0.95","label":"Analyst competition policy","source_url":engine.DSR_URL},
        {"rule":"Tie-breaks","definition":"Net ROI lower uncertainty bound, then CLV; unresolved ties share rank","label":"Analyst competition policy","source_url":engine.DSR_URL},
        {"rule":"Entry","definition":"All ten gates PASS; missing metrics block entry rather than score zero","label":"Analyst competition policy","source_url":engine.PBO_URL},
        {"rule":"Divisions","definition":"Singles; cross-game parlays; player-prop combinations","label":"Analyst competition policy","source_url":"https://sportsbook.draftkings.com/page/nba-player-props"},
        {"rule":"Anti-gaming","definition":"No retroactive rule changes, selective deletion, undisclosed trials or fabricated settlement; audit hash required","label":"Analyst competition policy","source_url":engine.PBO_URL},
    ]
    body = cards([("Eligible entries","0","All strategies blocked"),("Certified strategies","0","No performance invented"),("Cash pool","blank — unverified","No funded prize verified"),("Rewards earned","0","Badges only after gates")])
    body += '<section class="panel"><h2>Leaderboard</h2><p class="empty-state">No strategy has passed all validation gates. Ranks, scores and rewards are intentionally empty.</p>'
    body += '<div class="table-wrap"><table><caption>Certified leaderboard. Zero eligible entries; no placeholder rows.</caption><thead><tr><th>rank</th><th>strategy</th><th>division</th><th>deflated Sharpe</th><th>net ROI lower bound</th><th>CLV</th><th>reward</th><th>source</th></tr></thead><tbody></tbody></table></div></section>'
    body += table(reward_rows, "Reward policy", csv_name=None)
    body += table(scoring_rows, "Scoring and entry policy", csv_name=None)
    body += table(gates, "Required gates", csv_name="gates.csv")
    add("pages/leaderboard.html", "Reward leaderboard", "Only validated strategies can rank; no funded cash prize or winner is verified.", body)

    # Teams
    body = note('Current-season samples are only 6–9 games. Prior-season ratings are an 82-game baseline, not a roster-adjusted forecast. Official ratings are used directly rather than deriving defense from rounded net points.')
    body += table(d["team_advanced_2026_27.csv"], "2026–27 official advanced table", csv_name="team_advanced_2026_27.csv")
    body += table(d["team_traditional_2026_27.csv"], "2026–27 official traditional table", csv_name="team_traditional_2026_27.csv")
    body += table(d["standings_2026_27.csv"], "2026–27 official standings", csv_name="standings_2026_27.csv")
    body += table(d["team_advanced_2025_26.csv"], "2025–26 official advanced prior", csv_name="team_advanced_2025_26.csv")
    body += table(d["signals.csv"], "Descriptive persistence signal", csv_name="signals.csv")
    add("pages/teams.html", "Team evidence and ratings", "Complete official team tables, standings and disclosed shrinkage inputs.", body)

    # Players
    body = note('<strong>Sample correction:</strong> Dončić ranked first and Edwards third in the official 2025–26 scoring list; Gilgeous-Alexander was second. This is a selected two-player high-usage sample, not the top two scorers and not a league-wide prop dataset.')
    body += table(d["players.csv"], "Selected-player official checksums", csv_name="players.csv")
    body += table(d["player_games.csv"], "Complete 125-row selected player-game sample", csv_name="player_games.csv")
    add("pages/players.html", "Player game logs", "Every retained row links to the official NBA game and log source.", body)

    # Evidence
    body = table(d["sources.csv"], "Source register and verification scope", source_field="url", review_field=None, csv_name="sources.csv")
    body += table(d["schedule.csv"], "Official November 5 schedule", csv_name="schedule.csv")
    body += table(d["injuries.csv"], "Official noon injury report — current games only", csv_name="injuries.csv")
    body += table(d["market_snapshot.csv"], "Archived official operator prices", csv_name="market_snapshot.csv")
    body += table(d["checks.csv"], "Input integrity checks", csv_name="checks.csv")
    add("pages/evidence.html", "Evidence and verification", "Row-level official links, frozen market observations and explicit retrieval limits.", body)

    # Audit
    body = cards([("Baseline files",str(audit_summary["files"]),audit_summary["baseline"][:12]),("Lines scanned",f'{audit_summary["lines"]:,}',"Every baseline line counted/scanned"),("Syntax errors",str(audit_summary["python_syntax_errors"]+audit_summary["json_errors"]+audit_summary["js_syntax_errors"]),"Python/JSON/JS"),("Broken inherited links",str(audit_summary["broken_internal_links"]),"Repair in final integration"),("CSV rows without official row link",str(audit_summary["csv_no_link_rows"]),"Provenance coverage, not factual-error count"),("Findings",str(audit_summary["findings"]),"Manual + automated")])
    body += note('Scope: structural/provenance audit of every inherited file at the pinned baseline, plus independent official re-review of the new snapshot and reused player sample. This is not a claim that every historical fact in all 434 inherited files was independently re-fetched.')
    body += table(findings, "Audit findings", csv_name="findings.csv", csv_folder="../audit")
    inv_cols=["path","extension","bytes","lines","structural_status","issues","csv_rows","csv_official_link_rows","csv_other_link_rows","csv_no_link_rows","internal_links","broken_internal_links","review_url"]
    body += table(inventory, "Complete baseline file inventory", columns=inv_cols, source_field="review_url", review_field=None, csv_name="file_inventory.csv", csv_folder="../audit")
    body += table(broken, "Broken inherited link examples", source_field="review_url", review_field=None, csv_name="broken_link_examples.json", csv_folder="../audit")
    add("pages/audit.html", "Repository audit", "Pinned-baseline line inventory, structural checks, provenance coverage and review links.", body)

    # Review
    blank_rows = [
        {"item":"Model win probability and expected value","value":"","reason":"No calibrated scoring distribution or executable price","flag_id":"R03;R05","source_url":engine.NBA_GLOSSARY},
        {"item":"Strategy ROI, CLV, DSR, PBO, rank and reward","value":"","reason":"No settled/prospective ledger or trial-return matrix","flag_id":"R01;R08","source_url":engine.DSR_URL},
        {"item":"Leaderboard entries","value":"","reason":"Zero strategies pass all gates","flag_id":"R01","source_url":engine.DSR_URL},
        {"item":"Exact market retrieval timestamp, jurisdiction and ticket terms","value":"","reason":"Dynamic render did not expose a frozen executable quote","flag_id":"R05","source_url":engine.FD_BOARD},
        {"item":"Current prop market probability and edge","value":"","reason":"No verified timestamped prop/combo prices","flag_id":"R01;R07","source_url":"https://sportsbook.draftkings.com/page/nba-player-props"},
        {"item":"Cash prize pool and payouts","value":"","reason":"Funding and payout mechanism unverified","flag_id":"R09","source_url":engine.DSR_URL},
        {"item":"Unsubmitted injury-report player/reason cells","value":"","reason":"Official report says NOT YET SUBMITTED; no availability inference","flag_id":"R04","source_url":"https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-05_12_00PM.pdf"},
    ]
    body = note('Open flags are nonblocking for publishing research, but they block betting certification and rewards. Every blank is intentional. Review links point to official context or the exact repository location.')
    body += table(flags, "Flagged for review register", csv_name="flags.csv")
    body += table(blank_rows, "Unverified blank register", csv_name=None)
    body += table(findings, "Repository findings with exact review links", csv_name="findings.csv", csv_folder="../audit")
    add("pages/review.html", "Flagged for review", "Irregularities, unverified blanks and scoped limitations with official or exact review links.", body)

    # Methodology
    assumptions = [
        {"parameter":"Shrinkage K","value":"20 games","label":"Analyst policy, not an NBA estimate","source_url":engine.NBA_ADV,"flag_id":"R02"},
        {"parameter":"Home advantage baseline","value":"0 points","label":"Neutral baseline; not an estimated effect","source_url":engine.NBA_GLOSSARY,"flag_id":"R03"},
        {"parameter":"Home sensitivity","value":"-2 / 0 / +2 points","label":"Analyst scenarios","source_url":engine.NBA_GLOSSARY,"flag_id":"R03"},
        {"parameter":"Bootstrap","value":"1000 reps; block 5; seed 20261105","label":"Conditional dependence diagnostic","source_url":engine.NIST_URL,"flag_id":"R06"},
        {"parameter":"Trial family","value":"8 predeclared candidates","label":"Analyst governance; future searches increase m","source_url":engine.DSR_URL,"flag_id":"R08"},
        {"parameter":"Primary alpha / power","value":"0.05 one-sided / 0.80","label":"Policy; Bonferroni 0.05/8 also shown","source_url":engine.NIST_URL,"flag_id":"R08"},
        {"parameter":"DSR / PBO thresholds","value":"DSR >=0.95; PBO <=0.50","label":"Analyst gate policy informed by primary methods","source_url":engine.PBO_URL,"flag_id":"R08"},
    ]
    body = '<section class="panel"><h2>Method in plain language</h2><ol class="method"><li><strong>Freeze evidence.</strong> Transcribe official tables with row links; keep unknowns blank; record retrieval limits.</li><li><strong>Originate a transparent baseline.</strong> Shrink small-sample team ratings, match pace and opponent defense, and compare point estimates with archived prices. Do not invent probabilities.</li><li><strong>Measure dependence honestly.</strong> Report per-player and centered correlations, exact joint hit rates and conditional intervals. Never treat lag-1 scoring as parlay independence.</li><li><strong>Separate skill from luck as far as evidence allows.</strong> Use exact binomial power, Holm adjustment, Deflated Sharpe with the full trial family, CSCV/PBO, market calibration and prospective replication. No ledger means no skill claim.</li><li><strong>Fail closed.</strong> A strategy ranks only after all ten gates pass. Rewards are non-cash badges until funding is verified.</li></ol></section>'
    body += table(assumptions, "Disclosed model and policy assumptions", csv_name=None)
    body += table(requirements, "Requirement coverage matrix", csv_name="requirements.csv")
    body += f'<section class="panel"><h2>Research documents</h2><ul><li><a href="{e(link("pages/methodology.html", "research/METHODOLOGY.md"))}">Methodology</a></li><li><a href="{e(link("pages/methodology.html", "research/DATA_NOTES.md"))}">Data notes</a></li><li><a href="{e(link("pages/methodology.html", "research/EXECUTIVE_SUMMARY.md"))}">Executive summary</a></li><li><a href="{e(link("pages/methodology.html", "research/LEADERBOARD.md"))}">Leaderboard design</a></li><li><a href="{e(link("pages/methodology.html", "research/FLAGS.md"))}">Flag register</a></li></ul></section>'
    add("pages/methodology.html", "Methodology and requirements", "Disclosed assumptions, reproducible calculations and requirement-by-requirement coverage.", body)

    # Write pages and CSS.
    for path, content in pages.items():
        out = ROOT / path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
    css = '''/* Deterministic, dependency-free dashboard styles. */
:root{--bg:#f6f7f9;--panel:#fff;--ink:#17202a;--muted:#5b6573;--line:#d8dee7;--accent:#174e7c;--warn:#8a4b00;--bad:#9b1c1c;--ok:#166534}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}a{color:var(--accent)}.wrap{max-width:1240px;margin:0 auto;padding:0 20px}.skip{position:absolute;left:-9999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:10}.site-header{background:#fff;border-bottom:1px solid var(--line)}.header-inner{display:flex;justify-content:space-between;gap:24px;padding-top:28px;padding-bottom:18px}.eyebrow{margin:0 0 4px;color:var(--muted);font-size:.78rem;text-transform:uppercase;letter-spacing:.08em}h1{margin:0;font-size:clamp(1.6rem,3vw,2.3rem);line-height:1.15}.subtitle{margin:8px 0 0;color:var(--muted);max-width:70ch}.stamp{display:flex;flex-direction:column;align-items:flex-end;gap:2px;color:var(--muted);font-size:.85rem;white-space:nowrap}.stamp strong{color:var(--ink);font-size:1.05rem}.nav{display:flex;flex-wrap:wrap;gap:6px;padding-top:10px;padding-bottom:12px}.nav a{padding:7px 10px;border-radius:6px;text-decoration:none;color:var(--muted);font-size:.9rem}.nav a:hover,.nav a.active{background:#e8f0f8;color:var(--accent)}.nav a.active{font-weight:650}main{padding-top:24px;padding-bottom:40px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:0 0 20px}.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:14px}.card span,.card small{display:block;color:var(--muted);font-size:.8rem}.card strong{display:block;font-size:1.5rem;margin:4px 0}.panel,.table-panel,.note,.decision{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:18px;margin:0 0 20px}.decision{border-left:5px solid var(--accent)}.note{border-left:5px solid var(--warn)}h2{margin:0 0 12px;font-size:1.2rem}.findings{margin:0;padding-left:20px}.findings li{margin:0 0 12px}.method li{margin:0 0 10px}.table-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}.download{font-size:.85rem;white-space:nowrap}.table-wrap{overflow:auto;max-width:100%;border:1px solid var(--line);border-radius:6px}table{border-collapse:collapse;width:100%;font-size:.82rem;background:#fff}caption{text-align:left;padding:8px;color:var(--muted);font-size:.78rem;caption-side:top}th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left;vertical-align:top}th{background:#eef2f6;position:sticky;top:0;font-weight:650;white-space:nowrap}tbody tr:nth-child(even){background:#fafbfc}td.num{text-align:right;font-variant-numeric:tabular-nums}.source{white-space:nowrap}.blank{color:var(--bad);font-size:.75rem;font-style:italic}.empty-state{padding:16px;color:var(--muted);background:#fff;border:1px dashed var(--line);border-radius:6px}code{font-size:.85em;word-break:break-all}.site-footer{border-top:1px solid var(--line);background:#fff;color:var(--muted);font-size:.85rem;padding:18px 0}.site-footer p{margin:4px 0}@media(max-width:700px){.header-inner{flex-direction:column}.stamp{align-items:flex-start}.wrap{padding:0 12px}th,td{padding:6px}.card strong{font-size:1.25rem}}@media print{.nav,.skip,.download{display:none}body{background:#fff}.panel,.table-panel,.card{break-inside:avoid}.table-wrap{overflow:visible}table{font-size:7pt}}
'''
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets/style.css").write_text(css, encoding="utf-8")
    manifest = {}
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(("tests/", "__pycache__/")) or rel in ("data/site_manifest.json", "audit/verification.json"):
            continue
        if p.suffix in (".html", ".css", ".csv", ".json", ".md", ".jsonl", ".py"):
            manifest[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    with (DATA / "site_manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True); f.write("\n")
    return {"pages": len(pages), "manifest_files": len(manifest), **summary}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))

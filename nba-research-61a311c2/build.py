#!/usr/bin/env python3
"""Build a clean, static, source-linked NBA research dashboard."""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
D = json.loads((DATA / "derived.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((DATA / "audit_manifest.json").read_text(encoding="utf-8"))
with (DATA / "row_audit.csv").open(newline="", encoding="utf-8") as f:
    ROW_AUDIT = list(csv.DictReader(f))
with (DATA / "repo_inventory.csv").open(newline="", encoding="utf-8") as f:
    INVENTORY = list(csv.DictReader(f))

NAV = [
    ("index", "Overview"), ("lines", "Own lines"), ("players", "Players & props"),
    ("correlations", "Correlations"), ("strategies", "Strategies"),
    ("validation", "Validation gates"), ("leaderboard", "Leaderboard"),
    ("sources", "Sources"), ("review", "Flagged for Review"), ("audit", "Repo audit"),
]


def e(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def src(url: str, label: str = "Source") -> str:
    if not url:
        return '<span class="blank" aria-label="Unverified source"></span>'
    return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} ↗</a>'


def badge(text: str) -> str:
    t = str(text)
    cls = "ok" if t.startswith(("pass", "verified", "delivered")) else "warn" if t.startswith(("blocked", "flagged", "partial", "pending", "unmeasured")) else "neutral"
    return f'<span class="badge {cls}">{e(t.replace("_", " "))}</span>'


def cell(v) -> str:
    if v is None or v == "":
        return '<td class="blank" aria-label="Unverified or not applicable"></td>'
    return f"<td>{v}</td>"


def table(title: str, desc: str, headers: list[str], rows: list[list], tid: str, export: str | None = None) -> str:
    export_link = f'<a class="export" href="data/{e(export)}">CSV ↓</a>' if export else ""
    head = "".join(f'<th scope="col">{e(h)}</th>' for h in headers)
    body = "".join("<tr>" + "".join(cell(c) for c in row) + "</tr>" for row in rows)
    return f'''<section class="panel"><div class="panel-head"><div><h2>{e(title)}</h2><p>{e(desc)}</p></div>{export_link}</div>
<div class="table-tools"><label class="search">Search <input type="search" data-search="{e(tid)}" aria-label="Search {e(title)}" placeholder="Filter rows…"></label><span class="row-count" data-count="{e(tid)}">{len(rows)} rows</span></div>
<div class="table-wrap"><table id="{e(tid)}"><caption class="sr-only">{e(title)}. Blank cells are unverified, not zero. Every row has a source link.</caption>
<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div></section>'''


def note(title: str, text: str) -> str:
    return f'<aside class="notice"><strong>{e(title)}</strong><p>{e(text)}</p></aside>'


def cards(items: list[tuple[str, str, str]]) -> str:
    return '<div class="cards">' + "".join(f'<article class="card"><span>{e(label)}</span><strong>{e(value)}</strong><small>{e(sub)}</small></article>' for label, value, sub in items) + "</div>"


def page(key: str, title: str, subtitle: str, content: str) -> None:
    nav_parts = []
    for k, t in NAV:
        active = "active" if k == key else ""
        aria = 'aria-current="page"' if k == key else ""
        nav_parts.append(f'<a href="{k}.html" class="{active}" {aria}>{e(t)}</a>')
    nav = "".join(nav_parts)
    body = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Evidence-first NBA line-origination research dashboard. Official source links on every table row; unverified values stay blank.">
<title>{e(title)} · OWN5 NBA Research</title><link rel="stylesheet" href="assets/style.css"><script src="assets/app.js" defer></script>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230f172a'/%3E%3Ctext x='16' y='22' font-size='16' text-anchor='middle' fill='white' font-family='Arial'%3EO5%3C/text%3E%3C/svg%3E"></head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="brand"><a href="index.html">OWN5 <span>NBA research desk</span></a></div>
<div class="as-of">Snapshot {e(D['summary']['as_of'])} · paper research only</div></header>
<nav class="site-nav" aria-label="Main navigation">{nav}</nav>
<main id="main"><div class="page-heading"><h1>{e(title)}</h1><p>{e(subtitle)}</p></div>{content}
<footer><p>Independent research. Not affiliated with the NBA or any sportsbook. Blank cells are unverified, not zero. No bets, ROI or funded rewards are claimed.</p>
<p><a href="https://github.com/sassnarep3-star/Own5" target="_blank" rel="noopener noreferrer">Repository ↗</a> · <a href="../research/nba-research-61a311c2/EXECUTIVE_SUMMARY.md">Executive summary ↗</a> · <a href="../index.html">Legacy NFL desk ↗</a></p></footer></main></body></html>'''
    (HERE / f"{key}.html").write_text(body + "\n", encoding="utf-8")


def overview() -> str:
    s = D["summary"]
    out = cards([
        ("Canonical audited rows", s["canonical_rows"], "official/operator source links"),
        ("Model-only slate lines", s["slate_games"], "Nov 5–6; not qualified bets"),
        ("Qualified strategies", f"0 / {s['strategies']}", "fail-closed gates"),
        ("Open review flags", s["flags"], "published, nonblocking"),
    ])
    out += note("Bottom line", "The desk can originate transparent model lines and measure selected-player dependence, but it cannot yet claim betting skill: closing quotes, availability, calibrated probabilities and cross-game dependence are missing. All reward/ROI fields remain blank or zero.")
    out += table("Research categories", "Each category has a dedicated subpage and source-linked tables.", ["Category", "Finding", "Status", "Source"], [
        ["<a href='lines.html'>Own lines</a>", "11 pace/efficiency model lines; 2 Nov 5 market comparisons", badge("model_only"), src("https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season", "NBA")],
        ["<a href='players.html'>Players & props</a>", "29 current player-game rows; 47 exploratory chronological forecasts", badge("partial"), src("https://www.nba.com/stats/player/1629029/boxscores?Season=2026-27&SeasonType=Regular%20Season", "NBA")],
        ["<a href='correlations.html'>Correlations</a>", "12 within-player correlations; 10 threshold-combo frequencies", badge("partial"), src("https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html", "Method")],
        ["<a href='validation.html'>Validation gates</a>", "G01–G12; eligibility false", badge("blocked"), src("https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf", "Method")],
        ["<a href='leaderboard.html'>Leaderboard</a>", "6 registered strategies; no ranked or funded entries", badge("blocked"), src("https://github.com/sassnarep3-star/Own5", "Project")],
        ["<a href='audit.html'>Repo audit</a>", f"{MANIFEST['baseline_files']} baseline files inventoried; {MANIFEST['canonical_rows_audited']} canonical rows registered", badge("verified_inventory"), src("https://github.com/sassnarep3-star/Own5/tree/54e8dee596d49731c3da535a1f77b01cd0c295d5", "Baseline")],
    ], "categories")
    out += table("Requirements trace", "Acceptance criteria and honest completion state.", ["ID", "Requirement", "Status", "Evidence", "Source"], [
        [r["id"], e(r["requirement"]), badge(r["status"]), e(r["evidence"]), src(r["source_url"])] for r in D["requirements"]
    ], "requirements")
    return out


def lines_page() -> str:
    out = note("Model lines, not betting recommendations", "Home spread uses betting convention: negative means the home team is favored. K=10 shrinkage and HFA=0 are declared model choices. No availability adjustment or calibrated win probability is applied.")
    rows = []
    for l in D["lines"]:
        links = src(l["source_url"], "NBA") + (" · " + src(l["market_source_url"], "Market") if l["market_source_url"] else "")
        rows.append([e(l["date"]), f'<strong>{e(l["away"])} @ {e(l["home"])}</strong><small>{e(l["tip_et"])} ET · {e(l["arena"])}</small>',
                     e(l["model_home_spread"]), e(l["model_total"]), l["market_home_spread"], l["market_total"],
                     l["spread_diff_model_minus_market"], l["total_diff_model_minus_market"], badge(l["status"]), links])
    out += table("Slate line board", "Nov 5 has a dynamic FanDuel snapshot; Nov 6 market cells are blank because no quote was retrieved.", ["Date", "Game", "Model home spread", "Model total", "Market home spread", "Market total", "Spread diff", "Total diff", "Status", "Sources"], rows, "lines", "derived_lines.csv")
    out += table("Model parameters", "Derived from the verified current team snapshot; not fitted to outcomes.", ["Parameter", "Value", "Source"], [
        ["Shrinkage K", D["model"]["k_shrink"], src("https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season", "NBA")],
        ["Home advantage", D["model"]["hfa"], src("https://www.nba.com/stats/help/glossary", "NBA")],
        ["League OffRtg", D["model"]["league_off_rtg"], src("https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season", "NBA")],
        ["League DefRtg", D["model"]["league_def_rtg"], src("https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season", "NBA")],
        ["League PACE", D["model"]["league_pace"], src("https://www.nba.com/stats/teams/advanced?Season=2026-27&SeasonType=Regular%20Season", "NBA")],
    ], "params")
    quotes = []
    with (DATA / "market_quotes_nov5.csv").open(newline="", encoding="utf-8") as f:
        for q in csv.DictReader(f):
            quotes.append([e(q["game_id"]), e(q["book"]), e(q["market"]), e(q["selection"]), q["line"] or None, q["american"], q["quote_timestamp"] or None, src(q["source_url"], "FanDuel")])
    out += table("Nov 5 operator quote snapshot", "Values were visible on the operator page at retrieval. Timestamp and closing-line status are unverified/blank.", ["Game", "Book", "Market", "Selection", "Line", "American", "Quote timestamp", "Source"], quotes, "quotes", "market_quotes_nov5.csv")
    return out


def players_page() -> str:
    out = note("Reference thresholds are not market props", "Current-season medians produce half-step research thresholds only. Availability and market prop prices are blank; no prop is qualified.")
    rows = []
    for p in D["player_refs"]:
        rows.append([f'<strong>{e(p["player"])}</strong><small>{e(p["team"])}</small>', p["n_current"], p["reference_pts"], p["reference_reb"], p["reference_ast"], p["reference_tpm"], p["availability_status"], p["market_prop_line"], badge(p["status"]), src(p["source_url"], "NBA") + (" · " + src(p["availability_source_url"], "Injury") if p["availability_source_url"] else "")])
    out += table("Current player reference lines", "Through Nov 4, 2026. Edwards has only 4 current rows; absence from later games is not inferred.", ["Player", "n", "PTS ref", "REB ref", "AST ref", "3PM ref", "Availability", "Market prop", "Status", "Sources"], rows, "playerrefs", "derived_player_refs.csv")
    wf = D["walk_forward"]
    out += table("Exploratory points replay", "Chronological expanding-median reversion on the 125 historical player-games. This is forecast accuracy, not betting ROI.", ["Metric", "Value", "Source"], [
        ["Forecast rows", wf["n_forecasts"], src("https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26", "NBA")],
        ["Wins / losses", f'{wf["wins"]} / {wf["losses"]}', src("https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26&SeasonType=Regular%20Season", "NBA")],
        ["Hit rate", wf["hit_rate"], src("https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26", "NBA")],
        ["Wilson 95% CI", f'{wf["wilson_low"]} – {wf["wilson_high"]}', src("https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html", "Method")],
        ["Exact p vs 50%", wf["exact_p_vs_50pct"], src("https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf", "Method")],
        ["Bonferroni p (family=6)", wf["bonferroni_p_family6"], src("https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf", "Method")],
        ["Graded bets / ROI", "0 / blank", src("https://sportsbook.fanduel.com/navigation/nba", "Operator")],
    ], "wfsummary")
    preds = [[e(p["date"]), e(p["player"]), e(p["game_id"]), p["prior_n"], p["reference_line"], e(p["pick"]), p["actual_pts"], "hit" if p["hit"] else "miss", src(p["source_url"], "NBA")] for p in D["predictions"]]
    out += table("Chronological forecast ledger", "Every row uses only prior games for the reference line and signal.", ["Date", "Player", "Game", "Prior n", "Line", "Pick", "Actual PTS", "Result", "Source"], preds, "predictions", "derived_walk_forward.csv")
    return out


def correlations_page() -> str:
    out = note("Dependence is measured only where the sample supports it", "Within-player Pearson correlations use moving-block 95% percentile CIs (block=5, 2000 resamples, fixed seed). They are exploratory, selected-player estimates. Cross-game parlay dependence is unmeasured and blank.")
    rows = [[e(c["player"]), e(c["pair"]), c["n"], c["r"], f'{c["ci_low"]} – {c["ci_high"]}' if c["ci_low"] is not None else None, badge(c["status"]), src(c["source_url"], "NBA")] for c in D["correlations"]]
    out += table("Within-player stat correlations", "2025-26 official game logs; no pooled cross-player coefficient is used for pricing.", ["Player", "Pair", "n", "Pearson r", "95% block CI", "Status", "Source"], rows, "corr", "derived_correlations.csv")
    lag = [[e(c["player"]), e(c["metric"]), c["n_pairs"], c["r"], f'{c["ci_low"]} – {c["ci_high"]}' if c["ci_low"] is not None else None, badge(c["status"]), src(c["source_url"], "NBA")] for c in D["lag"]]
    out += table("Serial dependence probe", "Lag-1 points within a player is not evidence that different games are independent.", ["Player", "Metric", "Pairs", "r", "95% block CI", "Status", "Source"], lag, "lag", "derived_lag.csv")
    combos = [[e(c["player"]), e(c["combo"]), c["n"], c["joint_hit"], f'{c["joint_ci_low"]} – {c["joint_ci_high"]}' if c["joint_ci_low"] is not None else None, c["independence_product"], c["lift"], c["phi"], badge(c["status"]), src(c["source_url"], "NBA")] for c in D["combos"]]
    out += table("Same-game threshold combinations", "Historical threshold frequencies, not official sportsbook prop lines. Three-leg phi is blank because pairwise phi is insufficient.", ["Player", "Combo", "n", "Joint hit", "95% block CI", "Independence product", "Lift", "Phi", "Status", "Source"], combos, "combos", "derived_combos.csv")
    cg = D["cross_game_correlation"]
    out += table("Cross-game parlay dependence", "Required for S06; no matched cross-game leg sample was obtained.", ["Estimand", "r", "n", "95% CI", "Status", "Source"], [["Cross-game leg dependence", cg["r"], cg["n"], cg["ci"], badge(cg["status"]), src(cg["source_url"], "Method")]], "crossgame")
    return out


def strategies_page() -> str:
    rows = [[f'<span class="id">{e(s["id"])}</span> <strong>{e(s["name"])}</strong>', e(s["class"]), e(s["hypothesis"]), e(s["evidence"]), badge(s["status"]), s["graded_bets"], s["roi"], src(s["source_url"])] for s in D["strategies"]]
    return note("Research queue, not picks", "All six strategies are registered before qualification. None has graded bets, ROI, rank or monetary reward.") + table("Candidate strategies", "Singles, player props, same-game combos and cross-game parlays are separate divisions.", ["ID / strategy", "Class", "Hypothesis", "Current evidence", "Status", "Graded bets", "ROI", "Source"], rows, "strategies")


def validation_page() -> str:
    rows = [[f'<span class="id">{e(g["id"])}</span> <strong>{e(g["name"])}</strong>', e(g["rule"]), badge(g["status"]), src(g["source_url"])] for g in D["gates"]]
    out = note("Fail-closed eligibility", "A strategy is eligible only when every gate is explicitly true. Missing evidence is not a pass. Current decision: PAPER_RESEARCH_ONLY.")
    out += table("Mandatory gates", "G01–G12 apply before leaderboard qualification.", ["Gate", "Requirement", "Status", "Source"], rows, "gates")
    out += table("Skill-vs-luck controls", "Implemented controls and remaining blanks.", ["Control", "State", "Source"], [
        ["Exact binomial tail", "Implemented for replay; p=0.614567 vs 50% before family correction", src("https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf", "Method")],
        ["Moving-block bootstrap", "Implemented for selected-player CIs; assumptions flagged", src("https://www.itl.nist.gov/div898/handbook/eda/section3/eda334.htm", "NIST")],
        ["Holm / Bonferroni", "Implemented; family size 6 registered", src("https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf", "Method")],
        ["Deflated Sharpe Ratio", None, src("https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf", "Method")],
        ["Closing-line value", None, src("https://sportsbook.fanduel.com/navigation/nba", "Operator")],
        ["Prospective paper ledger", "0 graded bets", src("https://github.com/sassnarep3-star/Own5", "Project")],
    ], "luck")
    return out


def leaderboard_page() -> str:
    rows = [[l["rank"], f'<span class="id">{e(l["entry_id"])}</span> <strong>{e(l["name"])}</strong>', e(l["class"]), l["graded_bets"], l["net_units"], l["score"], l["reward_points"], l["monetary_reward"], badge("not_eligible"), src(l["source_url"])] for l in D["leaderboard"]]
    out = note("No qualified entries. No funded prizes.", "Rows are registry order, not rankings. Rank, net units, score and monetary reward are blank. Research reward points are zero until all gates pass.")
    out += table("Reward leaderboard", "Reward-based competition is enabled only after qualification and funding verification.", ["Rank", "Entry", "Division", "Graded bets", "Net units", "Score", "Reward points", "Monetary reward", "Eligibility", "Source"], rows, "leaderboard")
    out += table("Competition charter", "Proposed project policy; methodological sources do not imply contest approval.", ["Rule", "Policy", "Source"], [
        ["Eligibility", "All G01–G12 true; independent audit artifact required.", src("https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf", "Method")],
        ["Ranking", "Eligible entries ranked by lower 95% block-bootstrap net-return bound; tie-break lower log loss, then lower drawdown.", src("https://www.itl.nist.gov/div898/handbook/eda/section3/eda334.htm", "NIST")],
        ["Anti-gaming", "Log every trial including abandoned variants; freeze versions; deduplicate overlapping exposure.", src("https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf", "Method")],
        ["Rewards", "Non-cash research badges only until sponsor, budget, eligibility and payout terms are verified; monetary amounts blank.", src("https://github.com/sassnarep3-star/Own5", "Project")],
        ["Risk accounting", "Flat 1-unit paper stakes; record pushes, voids, costs and correlated game/week exposure.", src("https://sportsbook.draftkings.com/help/general-betting-rules/market-rules", "Operator")],
    ], "charter")
    return out


def sources_page() -> str:
    rows = [[f'<strong>{e(s["id"])}</strong><small>{e(s["publisher"])}</small>', e(s["tier"]), e(s["scope"]), e(s["retrieved_date"]), badge(s["status"]), e(s["notes"]), src(s["url"], "Open")] for s in D["sources"]]
    return note("Source scope matters", "OFFICIAL = NBA property; OPERATOR_OFFICIAL = sportsbook's own rules/quotes; PRIMARY_METHOD = official scientific documentation or author paper; PROJECT_OFFICIAL = this repository. A source link verifies the scoped statement, not profitability.") + table("Source register", "21 scoped sources retrieved or inventoried on 2026-11-05.", ["ID / publisher", "Tier", "Scope", "Retrieved", "Status", "Notes", "Link"], rows, "sources", "sources.csv")


def review_page() -> str:
    rows = [[f'<span class="id">{e(f["id"])}</span> ' + badge(f["severity"]), f'<strong>{e(f["issue"])}</strong>', e(f["detail"]), badge("needs_review"), src(f["source_url"])] for f in D["flags"]]
    return note("Published openly; nonblocking for the site", "These items block empirical qualification or live betting claims, not publication. No missing value has been inferred.") + table("Flagged for Review", "19 evidence gaps and irregularities retained for manual review.", ["ID / severity", "Issue", "Finding / limitation", "Status", "Source"], rows, "flags")


def audit_page() -> str:
    out = cards([
        ("Baseline files", MANIFEST["baseline_files"], "hash/size/line inventory"),
        ("Canonical rows", MANIFEST["canonical_rows_audited"], "row-level evidence register"),
        ("Verified-value rows", MANIFEST["canonical_verified_rows"], "official/operator values"),
        ("Flagged blank rows", MANIFEST["canonical_flagged_rows"], "availability unconfirmed"),
    ])
    out += note("What the audit does and does not claim", "Every baseline file was inventoried and hashed at commit 54e8dee. Canonical empirical rows were compared/transcribed from official sources. Legacy NFL/NBA claims were not all re-certified; they remain archived and flagged where irregular.")
    ra = [[e(r["dataset"]), e(r["row_key"]), r["fields_checked"], e(r["verification_method"]), badge(r["status"]), src(r["source_url"])] for r in ROW_AUDIT]
    out += table("Canonical row evidence register", "241 rows; blank availability values are explicitly flagged.", ["Dataset", "Row key", "Fields checked", "Method", "Status", "Source"], ra, "rowaudit", "row_audit.csv")
    inv = [[e(r["path"]), r["bytes"], r["lines"] or None, e(r["scope"]), r["rows_total"] if r["rows_total"] else None, r["rows_with_source_url"] if r["rows_with_source_url"] else None, badge(r["status"]), src(r["source_url"], "Blob")] for r in INVENTORY]
    out += table("Baseline repository inventory", "434 files at the session baseline. Content certification is limited to the canonical subsets described above.", ["Path", "Bytes", "Lines", "Scope", "Rows", "Rows w/ source", "Status", "Source"], inv, "inventory", "repo_inventory.csv")
    return out


def main() -> None:
    (HERE / "assets").mkdir(exist_ok=True)
    page("index", "NBA line-origination research", "Evidence first. Independent lines, measured dependence, fail-closed validation.", overview())
    page("lines", "Own lines", "Transparent model spreads and totals; market comparisons only where a quote was retrieved.", lines_page())
    page("players", "Players & props", "Official game logs, reference thresholds and chronological replay.", players_page())
    page("correlations", "Correlations", "Within-player dependence and threshold combinations; cross-game dependence remains blank.", correlations_page())
    page("strategies", "Strategy queue", "Six registered hypotheses across singles, props, combos and parlays.", strategies_page())
    page("validation", "Validation gates", "Mandatory evidence before any strategy can qualify.", validation_page())
    page("leaderboard", "Reward leaderboard", "Reward reproducibility, not a lucky run. No funded prizes.", leaderboard_page())
    page("sources", "Sources & findings", "Scoped official, operator, methodological and project sources.", sources_page())
    page("review", "Flagged for Review", "Unknowns and irregularities in the open.", review_page())
    page("audit", "Repository audit", "Baseline inventory and canonical row evidence register.", audit_page())
    print("Built 10 static NBA research pages.")


if __name__ == "__main__":
    main()

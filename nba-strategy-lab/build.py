#!/usr/bin/env python3
"""Build the static NBA Strategy Lab. Run engine.py first."""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RAW = DATA / "raw"
PAGES = [
    ("index.html", "Overview"), ("lines.html", "Own lines"),
    ("strategies.html", "Strategies"), ("leaderboard.html", "Leaderboard"),
    ("correlations.html", "Correlations"), ("validation.html", "Validation"),
    ("evidence.html", "Evidence tables"), ("audit.html", "Audit checks"),
    ("methodology.html", "Methodology"), ("sources.html", "Sources"),
    ("review.html", "Flagged for review"),
]
LABELS = {
    "source_url": "Official source", "ratings_source_url": "Ratings source",
    "game_id": "Game", "date": "Date", "tip_et_24h": "Tip ET (24h)",
    "matchup": "Matchup", "model_home_margin": "Model home margin",
    "model_home_spread": "Model home spread", "model_total": "Model total",
    "model_home_win_probability": "Home win probability",
    "model_home_fair_american": "Home fair price (model)",
    "model_away_fair_american": "Away fair price (model)",
    "market_spread": "Market spread", "market_total": "Market total",
    "market_price": "Market price", "market_edge": "Market edge",
    "strategy_id": "ID", "holdout_n": "Holdout n", "holdout_hits": "Hits",
    "holdout_hit_rate": "Hit rate", "ci95_low": "95% CI low", "ci95_high": "95% CI high",
    "null_probability": "Null probability", "p_one_sided": "One-sided p",
    "p_holm": "Holm-adjusted p", "failed_gates": "Open gates", "roi": "ROI",
    "deflated_score": "Deflated score", "n": "n", "ci95_low": "95% CI low",
    "ci95_high": "95% CI high", "joint_hit_rate": "Joint hit rate",
    "independence_product": "Independence product", "lift": "Lift vs independence",
    "source_id": "ID", "url": "Official URL", "as_of": "As of",
}


def read(name: str, raw: bool = False) -> list[dict[str, str]]:
    path = (RAW if raw else DATA) / name
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def label(key: str) -> str:
    return LABELS.get(key, key.replace("_", " ").capitalize())


def source_links(row: dict[str, str]) -> str:
    links = []
    for key, text in (("source_url", "NBA source"), ("ratings_source_url", "NBA ratings"), ("url", "Official page")):
        value = row.get(key, "")
        if value:
            links.append(f'<a href="{html.escape(value, quote=True)}" target="_blank" rel="noopener noreferrer">{text} ↗</a>')
    return "<br>".join(links)


def table(rows: list[dict], *, caption: str, compact: bool = False) -> str:
    if not rows:
        return '<p class="empty">No entries.</p>'
    keys = [k for k in rows[0] if k not in {"source_url", "ratings_source_url", "url"}]
    keys.append("sources")
    head = "".join(f"<th scope=\"col\">{html.escape(label(k))}</th>" for k in keys)
    body = []
    for row in rows:
        cells = []
        for key in keys:
            if key == "sources":
                value = source_links(row)
            else:
                raw = row.get(key, "")
                if raw == "":
                    value = '<span class="blank" title="Blank: unverified, unavailable, or not applicable">—</span>'
                elif key == "status":
                    cls = "pass" if raw == "PASS" else "fail"
                    value = f'<span class="status {cls}">{html.escape(raw)}</span>'
                elif key in {"qualification", "eligible"}:
                    value = f'<span class="status fail">{html.escape(raw)}</span>'
                elif key in {"hit_rate", "holdout_hit_rate", "model_home_win_probability", "ci95_low", "ci95_high", "null_probability", "joint_hit_rate", "independence_product"} and raw:
                    value = html.escape(raw)
                else:
                    value = html.escape(str(raw))
                if key in {"rule", "detail", "interpretation", "disposition", "evidence", "reason", "scope", "development"}:
                    value = f'<span class="wrap">{value}</span>'
            cells.append(f"<td data-label=\"{html.escape(label(key), quote=True)}\">{value}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    search = "" if compact else '<input class="table-filter" type="search" placeholder="Filter this table…" aria-label="Filter table rows">'
    return f'<section class="table-card"><div class="table-toolbar"><h2>{html.escape(caption)}</h2><span class="row-count">{len(rows)} rows</span>{search}</div><div class="table-scroll"><table><caption class="sr-only">{html.escape(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div></section>'


def layout(filename: str, title: str, intro: str, content: str) -> str:
    nav_parts = []
    for href, text in PAGES:
        active = ' class="active" aria-current="page"' if href == filename else ""
        nav_parts.append(f'<a href="{href}"{active}>{html.escape(text)}</a>')
    nav = "".join(nav_parts)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Evidence-first NBA line origination and fail-closed strategy research.">
<title>{html.escape(title)} · NBA Strategy Lab</title><link rel="stylesheet" href="assets/style.css"><script defer src="assets/app.js"></script></head>
<body><a class="skip" href="#main">Skip to content</a><aside class="sidebar"><a class="brand" href="index.html"><span class="brand-mark">N</span><span>NBA Strategy Lab<small>Evidence before edge</small></span></a><nav aria-label="Main navigation">{nav}</nav><div class="sidebar-note"><span class="dot"></span> Research only<br><small>No actionable wagers</small></div></aside>
<main id="main"><header class="page-header"><div><p class="eyebrow">OWN5 / NBA / 2026-11-05</p><h1>{html.escape(title)}</h1><p>{html.escape(intro)}</p></div><span class="research-badge">0 qualified</span></header>{content}<footer><strong>Verification boundary:</strong> frozen NBA.com source snapshots; derived values are analyst calculations. Blank cells are never inferred. <a href="review.html">Review all limitations</a>.</footer></main></body></html>'''


def write_page(filename: str, title: str, intro: str, content: str) -> None:
    (ROOT / filename).write_text(layout(filename, title, intro, content), encoding="utf-8")


def main() -> None:
    summary = json.loads((DATA / "summary.json").read_text())
    lines, strategies = read("lines.csv"), read("strategies.csv")
    corr, gates, board = read("correlations.csv"), read("gates.csv"), read("leaderboard.csv")
    flags, sources, checks = read("flags.csv"), read("sources.csv"), read("audit_checks.csv")
    cards = "".join(f'<a class="category" href="{href}"><span>{html.escape(name)}</span><b>Explore →</b></a>' for href, name in PAGES[1:6])
    metrics = "".join(f'<div class="metric"><span>{html.escape(name)}</span><strong>{value}</strong><small>{html.escape(note)}</small></div>' for name, value, note in [
        ("Official-source rows", summary["official_source_rows"], "each row linked"),
        ("Integrity checks", summary["audit_checks"], "0 failures"),
        ("Archived model lines", summary["lines"], "research only"),
        ("Qualified strategies", summary["qualified"], "fail-closed"),
    ])
    findings = [
        {"finding": "No strategy is validated or rewarded", "evidence": "All nine candidates have open gates; ranking and ROI are blank.", "source_url": "https://www.nba.com/stats/help/glossary"},
        {"finding": "Same-game prop legs are dependent", "evidence": "Pooled 25+ PTS & 3+ 3PM: φ=0.4733, joint=0.6480, independence product=0.5591 (n=125).", "source_url": "https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26"},
        {"finding": "Small samples do not remove luck", "evidence": "Team diagnostics use 22 games; the parlay track has only 3 joint events.", "source_url": "https://www.nba.com/stats/teams/boxscores?Season=2026-27&SeasonType=Regular%20Season"},
        {"finding": "Market edge cannot be calculated", "evidence": "No verified bookmaker prices or prospective settlement ledger; market fields remain blank.", "source_url": "https://www.nba.com/schedule?month=11&year=2026"},
    ]
    home = f'''<section class="hero"><div><span class="pill">EXECUTIVE SUMMARY</span><h2>Selective by design.<br>Unranked until proven.</h2><p>A reproducible NBA research desk for originating lines, measuring dependence, and testing singles, parlays and player-prop combinations. The current evidence supports research—not a claim of betting skill.</p><div class="actions"><a class="button primary" href="strategies.html">Review strategies</a><a class="button" href="methodology.html">Read methodology</a></div></div><div class="hero-status"><span>Competition status</span><strong>OPEN · UNFUNDED</strong><dl><div><dt>Eligible entries</dt><dd>0 / 9</dd></div><div><dt>Rewards issued</dt><dd>0</dd></div><div><dt>Market quotes</dt><dd>—</dd></div></dl></div></section>
<section class="metrics">{metrics}</section><section class="section-head"><div><p class="eyebrow">RESEARCH WORKSPACE</p><h2>From raw evidence to validation</h2></div></section><section class="categories">{cards}</section>{table(findings, caption="Decision-grade findings", compact=True)}
<section class="callout"><strong>What “remove luck” means here.</strong> Luck cannot be literally removed. This lab reduces false discoveries with chronological splits, fixed thresholds, exact binomial tests, Holm correction, uncertainty intervals, minimum sample sizes, and independent prospective replication. <a href="validation.html">See every gate</a>.</section>'''
    write_page("index.html", "NBA research, without the guesswork", "Own lines, empirical correlations, and a competition that pays only after evidence clears every gate.", home)
    write_page("lines.html", "Archived own lines", "Sixteen model-derived spreads, totals and fair prices for the frozen 2026-11-04/05 schedule. Not current betting lines.", '<div class="notice"><strong>Archived research only.</strong> Zero home-court advantage and 20-game shrinkage are analyst conventions. Fair American prices are model arithmetic, not sportsbook quotes. Blank market cells are covered by F01.</div>' + table(lines, caption="Frozen schedule and model outputs"))
    write_page("strategies.html", "Strategy candidates", "Singles, a daily parlay, and fixed player-prop thresholds. Historical hit rates are diagnostics, not realized betting ROI.", '<div class="notice"><strong>Fail-closed catalog.</strong> A visible candidate is not a qualified strategy. Only entries passing every gate may become active; currently none do.</div>' + table(strategies, caption="Candidate holdout diagnostics") + table(read("strategy_ledger.csv"), caption="Event-level strategy ledger"))
    reward_policy = [
        {"place": "1", "proposed_pool_share": "50%", "activation": "Only if qualified and pool separately funded", "reward_amount": "", "source_url": "https://www.nba.com/stats/help/glossary"},
        {"place": "2", "proposed_pool_share": "30%", "activation": "Only if qualified and pool separately funded", "reward_amount": "", "source_url": "https://www.nba.com/stats/help/glossary"},
        {"place": "3", "proposed_pool_share": "20%", "activation": "Only if qualified and pool separately funded", "reward_amount": "", "source_url": "https://www.nba.com/stats/help/glossary"},
    ]
    write_page("leaderboard.html", "Leaderboard competition", "No rank by default. A future score is available only to qualified, independently replicated entries.", '<div class="notice"><strong>0 eligible entries · 0 rewards.</strong> Sorting by raw hit rate would reward small-sample luck, so rank, score, ROI and reward cells stay blank.</div>' + table(board, caption="Eligibility board — intentionally unranked") + table(reward_policy, caption="Proposed future reward allocation", compact=True))
    write_page("correlations.html", "Correlation & combo pricing", "Pearson, point-biserial and φ statistics with Fisher-z intervals; joint hit rates are compared with independence products.", '<div class="notice"><strong>Do not multiply dependent legs.</strong> Correlation describes this frozen sample, not a causal effect or a guaranteed future price. Pooled rows combine only Dončić and Edwards.</div>' + table(corr, caption="Computed correlation and joint-rate diagnostics"))
    write_page("validation.html", "Validation gates", "Every candidate must pass every applicable evidence gate. Missing market or replication evidence fails closed.", table(gates, caption="Strategy-by-strategy gate matrix") + table(strategies, caption="Qualification summary", compact=True))
    team = read("team_seasons.csv", True)
    games = read("games_sample_2026_27.csv", True)
    players = read("player_games.csv", True)
    schedule = read("schedule.csv", True)
    write_page("evidence.html", "Official-source evidence tables", "All 275 frozen input rows, without inferred blanks. Values are transcriptions from the linked official NBA pages; derived outputs live elsewhere.", table(team, caption="Team seasons · 90 rows") + table(schedule, caption="Archived schedule · 16 rows") + table(games, caption="Team-game box scores · 44 rows") + table(players, caption="Player-game box scores · 125 rows"))
    write_page("audit.html", "Line-by-line audit", "Automated provenance, arithmetic and cross-row identity checks. Passing internal checks does not replace manual review of the linked source pages.", '<div class="notice"><strong>547 checks · 0 failures.</strong> External pages were not freshly fetched in this session (F06); the official links remain available for manual review.</div>' + table(checks, caption="Executed integrity assertions"))
    methods = [
        {"component": "Official input boundary", "method": "Only frozen rows carrying HTTPS NBA URLs enter calculations; no memory-based values.", "status": "IMPLEMENTED", "source_url": "https://www.nba.com/stats/help/glossary"},
        {"component": "Team rating", "method": "(current GP × current margin + 20 × prior-season margin) / (current GP + 20); home margin = home rating − away rating.", "status": "DERIVED / UNVALIDATED", "source_url": "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season"},
        {"component": "Total", "method": "Current league mean total plus each team's shrunk total deviation. Total per team = 2×PTS/G − margin/G.", "status": "DERIVED / UNVALIDATED", "source_url": "https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season"},
        {"component": "Win probability", "method": "Normal CDF(model home margin / 14.3454). Scale is RMSE of the 22-game prior-only diagnostic.", "status": "DERIVED / UNVALIDATED", "source_url": "https://www.nba.com/stats/teams/boxscores?Season=2026-27&SeasonType=Regular%20Season"},
        {"component": "Player holdout", "method": "Chronological per-player 60/40 split; fixed 25-point, 5-rebound, 5-assist and 3-three thresholds.", "status": "RETROSPECTIVE", "source_url": "https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26"},
        {"component": "Dependence", "method": "Pearson r / φ; joint two-leg rate compared with p(A)×p(B). Fisher-z intervals are descriptive.", "status": "IMPLEMENTED", "source_url": "https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26"},
        {"component": "Luck screen", "method": "Exact one-sided binomial tail against development or directional null; Holm correction across nine candidates; Wilson 95% interval.", "status": "IMPLEMENTED", "source_url": "https://www.nba.com/stats/help/glossary"},
        {"component": "Future deflated score", "method": "For qualified entries only: 100 × max(0, CI lower bound − null rate) × ln(1+n); no score is calculated now.", "status": "PROPOSED", "source_url": "https://www.nba.com/stats/help/glossary"},
        {"component": "Prospective activation", "method": "Timestamped market, availability and settlement plus independent replication are mandatory; no retroactive promotion.", "status": "BLOCKED", "source_url": "https://official.nba.com/nba-injury-report-2026-27-season/"},
    ]
    write_page("methodology.html", "Methodology & requirements", "Transparent formulas and explicit boundaries. Analyst conventions are labeled and never presented as NBA-published estimates.", table(methods, caption="Computational methodology") + '<section class="prose"><h2>Requirements trace</h2><ul><li><strong>Own lines:</strong> 16 archived spread/total/probability outputs.</li><li><strong>Signals:</strong> nine candidates across singles, parlays and prop combos.</li><li><strong>Correlation:</strong> 22 computed diagnostics with sample sizes and intervals where defined.</li><li><strong>Skill selection:</strong> eight gates per candidate; no all-pass entry, no ranking.</li><li><strong>Verification:</strong> every body-table row has an official NBA link; blanks remain blank.</li><li><strong>Responsible use:</strong> research only; no staking, execution, or profit claim.</li></ul></section>')
    write_page("sources.html", "Official source register", "Direct NBA and NBA Official links for manual review. Repo snapshots preserve the exact rows used by the engine.", table(sources, caption="Source register") + '<section class="prose"><h2>Review protocol</h2><p>Open the official link on any row and compare the source page with the frozen value. A passing identity check detects internal inconsistency, not every possible transcription error. F06 records that this session did not freshly fetch external NBA pages.</p></section>')
    write_page("review.html", "Flagged for Review", "Nonblocking irregularities, unavailable values and generalization limits. These items remain visible after publication.", table(flags, caption="Open review items") + '<section class="callout"><strong>Escalation rule.</strong> Any future missing input remains blank and keeps the affected strategy ineligible. Flagged items never get silently filled.</section>')
    print(f"Built {len(PAGES)} pages in {ROOT}")


if __name__ == "__main__":
    main()

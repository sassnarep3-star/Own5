#!/usr/bin/env python3
"""Deterministically build the isolated, dependency-free Week 10 research site."""
from __future__ import annotations
import csv
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
AS_OF = "2026-11-12"
NAV = [
    ("results", "Results & schedule", "results.html"),
    ("lines", "Own lines & market", "lines.html"),
    ("injuries", "Injury & depth", "injuries.html"),
    ("sources", "Sources", "sources.html"),
    ("correlations", "Correlations", "correlations.html"),
    ("strategies", "Strategies", "strategies.html"),
    ("validation", "Validation gates", "validation.html"),
    ("leaderboard", "Leaderboard", "leaderboard.html"),
    ("questions", "Decision Q&A", "questions.html"),
    ("suggestions", "Suggestions", "suggestions.html"),
    ("flagged", "Flagged review", "flagged.html"),
    ("audit", "Repository audit", "audit.html"),
]


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def ext_link(url: str, label: str) -> str:
    url = (url or "").strip()
    if not url.startswith("https://"):
        return '<span class="blank">Not supplied</span>'
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>'


def link_cell(value: str, label: str, multi: bool = False) -> str:
    urls = [u.strip() for u in (value or "").split(";") if u.strip()] if multi else ([value.strip()] if (value or "").strip() else [])
    if not urls:
        return '<span class="blank">Not recorded</span>'
    labels = [label]
    if multi and len(urls) > 1:
        labels = [f"{label} {i}" for i in range(1, len(urls) + 1)]
    return " ".join(ext_link(url, labels[min(i, len(labels)-1)]) for i, url in enumerate(urls))


def badge(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return '<span class="blank">Not recorded</span>'
    low = value.lower()
    cls = "neutral"
    if value == "PASS" or low in {"done", "verified"}:
        cls = "pass"
    elif any(k in low for k in ("blocked", "not_computable", "unfunded", "not_validated", "no_qualified", "research_only")):
        cls = "blocked"
    elif any(k in low for k in ("high", "critical")):
        cls = "high"
    elif any(k in low for k in ("open", "awaiting", "review", "partial", "missing", "flagged")):
        cls = "review"
    return f'<span class="badge {cls}">{esc(value.replace("_", " "))}</span>'


def text_cell(value: str, key: str = "") -> str:
    value = "" if value is None else str(value)
    if value.strip() == "":
        return '<span class="blank">Not recorded</span>'
    if key in {"status", "line_status", "verification_status", "severity", "decision", "decision_area"}:
        return badge(value)
    return esc(value).replace("\n", "<br>")


def table(rows: list[dict[str, str]], columns: list[tuple], caption: str, table_id: str) -> str:
    if not rows:
        return f'<div class="note"><p>{esc(caption)}: no rows in this snapshot.</p></div>'
    header = "".join(f'<th scope="col">{esc(label)}</th>' for _, label, _ in columns)
    body = []
    for row in rows:
        cells = []
        for key, label, kind in columns:
            value = row.get(key, "")
            if kind == "url":
                content = link_cell(value, label)
            elif kind == "multi_url":
                content = link_cell(value, label, multi=True)
            elif kind == "badge":
                content = badge(value)
            else:
                content = text_cell(value, key)
            cells.append(f"<td>{content}</td>")
        row_id = row.get("id") or row.get("team") or row.get("game_id") or ""
        body.append(f'<tr data-row-key="{esc(row_id)}">{"".join(cells)}</tr>')
    return (
        f'<div class="table-wrap"><table id="{esc(table_id)}">'
        f'<caption>{esc(caption)} ({len(rows)} rows)</caption>'
        f'<thead><tr>{header}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
    )


def download_links(files: list[tuple[str, str]]) -> str:
    links = "".join(f'<a class="download-link" href="data/{esc(name)}" download>{esc(label)}</a>' for name, label in files)
    return f'<div class="downloads">{links}</div>'


def source_links(row: dict[str, str], fields: list[tuple[str, str]]) -> str:
    items = []
    for field, label in fields:
        value = row.get(field, "")
        for i, url in enumerate([x.strip() for x in value.split(";") if x.strip()]):
            link_label = f"{label} {i+1}" if ";" in value else label
            if url.startswith("https://"):
                items.append(ext_link(url, link_label))
    return f'<div class="source-links">{"".join(items)}</div>' if items else '<p class="blank">No source URL recorded.</p>'


def page(title: str, eyebrow: str, description: str, active: str, content: str) -> str:
    nav = ['<a href="index.html"' + (' aria-current="page"' if active == "home" else '') + '>Overview</a>']
    for key, label, href in NAV:
        current = ' aria-current="page"' if active == key else ''
        nav.append(f'<a href="{href}"{current}>{esc(label)}</a>')
    heading = "" if active == "home" else f'<div class="section-heading page-title"><div><p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(title)}</h1><p>{esc(description)}</p></div></div>'
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#071019">
<meta name="description" content="NFL 2026 Week 10 dated, evidence-first research snapshot. Descriptive only; not betting advice.">
<title>{esc(title)} · Week 10 NFL research</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to main content</a>
<header class="site-header">
  <div class="header-inner">
    <div class="brand-row">
      <a class="brand" href="index.html" aria-label="NFL Week 10 research overview">
        <span class="brand-mark" aria-hidden="true">W10</span>
        <span class="brand-text"><strong>OWN5 · NFL Research</strong><span>Evidence first. Qualification fail-closed.</span></span>
      </a>
      <span class="snapshot-badge">Static snapshot · {AS_OF}</span>
    </div>
    <div class="nav-wrap"><nav class="site-nav" aria-label="Primary navigation">{"".join(nav)}</nav></div>
  </div>
</header>
<main id="main" class="page-shell">
  {heading}{content}
</main>
<footer class="site-footer"><div class="site-footer-inner">
  <p>Research snapshot as of {AS_OF}; dynamic external sources may have changed.</p>
  <p>Not a recommendation, fair-odds model, or claim of proven betting skill.</p>
</div></footer>
</body>
</html>
'''


def section(title: str, detail: str = "", right: str = "") -> str:
    detail_html = f'<p>{esc(detail)}</p>' if detail else ""
    return f'<div class="section-heading"><div><h2>{esc(title)}</h2>{detail_html}</div>{right}</div>'


def metric(label: str, value: str, note: str = "") -> str:
    note_html = f'<span class="metric-note">{esc(note)}</span>' if note else ""
    return f'<div class="metric-card"><span class="metric-label">{esc(label)}</span><strong class="metric-value">{esc(value)}</strong>{note_html}</div>'


def callout(title: str, body: str, cls: str = "") -> str:
    return f'<aside class="callout {esc(cls)}"><strong>{esc(title)}</strong><p>{esc(body)}</p></aside>'


def content_cards(rows: list[dict[str, str]], title_key: str, meta_fields: list[tuple[str, str]], body_fields: list[tuple[str, str]], link_fields: list[tuple[str, str]], id_key: str, badge_field: str = "") -> str:
    out = []
    for row in rows:
        rid = row.get(id_key, "")
        title = row.get(title_key, "(untitled record)")
        meta = []
        if rid:
            meta.append(f'<span class="badge neutral">{esc(rid)}</span>')
        for key, label in meta_fields:
            if key == badge_field:
                continue
            value = row.get(key, "")
            if value:
                meta.append(f'<span>{esc(label)}: {esc(value)}</span>')
        if badge_field and row.get(badge_field):
            meta.append(badge(row[badge_field]))
        details = []
        for key, label in body_fields:
            value = row.get(key, "")
            if value:
                details.append(f'<dt>{esc(label)}</dt><dd>{esc(value)}</dd>')
        out.append(f'''<article class="content-card" id="{esc(rid)}">
<div class="card-meta">{"".join(meta)}</div><h3>{esc(title)}</h3>
<dl>{"".join(details)}</dl>{source_links(row, link_fields)}</article>''')
    return f'<div class="cards-list">{"".join(out)}</div>'


def build_index() -> str:
    recon = read_json("game_reconciliation.json")
    wf = read_json("walk_forward_summary.json")
    audit = read_json("repo_audit_summary.json")
    schedule = read_csv("schedule_2026_w10.csv")
    games = read_csv("games_2026_w1_w9.csv")
    injuries = read_csv("injuries_depth_w10.csv")
    lines = read_csv("model_lines_2026_w10.csv")
    gates = read_csv("validation_gates_2026.csv")
    passing_gates = sum(r["status"] == "PASS" for r in gates)
    playing = sum(r["status"] == "SCHEDULED" for r in schedule)
    body = f'''<section class="hero hero-grid" aria-labelledby="hero-title">
<div><p class="eyebrow">NFL 2026 · Week 10 · evidence snapshot</p>
<h1 id="hero-title">Research before claims.</h1>
<p class="lede">A source-linked snapshot of verified results, baseline lines, selected lineup evidence, and validation gaps. Every output is dated; missing evidence stays visible.</p>
<div class="meta"><span class="meta-chip">Captured {AS_OF}</span><span class="meta-chip">NFL standings reconciliation: {esc(recon['status'])}</span><span class="meta-chip">{len(lines)} exploratory score lines</span></div></div>
<aside class="hero-side"><strong>Not betting advice</strong><p>These are descriptive calculations, not picks or fair prices. No strategy is validated, no wager is graded, and no monetary reward is funded.</p></aside>
</section>
<div class="metric-grid">
{metric('Completed games reconciled', str(len(games)), 'Weeks 1–9; zero W/L/T/PF/PA mismatches')}
{metric('Teams checked', str(recon['teams']), '32 NFL teams; 32/32 standings reconciled')}
{metric('Week 10 scheduled', str(playing), '14 games plus 4 bye teams')}
{metric('Walk-forward forecasts', str(wf['n_games']), 'Weeks 2–9, prior-week inputs only')}
{metric('Forecast MAE', wf['mae_points'], 'Points; one-season descriptive')}
{metric('Selected injury/depth rows', str(len(injuries)), '17 teams; not an exhaustive injury ledger')}
{metric('Depth chart source coverage', '32 / 32', 'Four bye-team charts checked; not line adjustments')}
{metric('Repository line audit', f"{audit['physical_lines']:,}", f"{audit['files']} in-scope files indexed")}
</div>
{callout('Validation remains blocked', f'{passing_gates} of {len(gates)} project gates pass (G0 only). No strategy rank, ROI, closing-line value, luck-adjusted score, or reward eligibility is established.', 'warning')}
{section('Explore the evidence', 'Twelve isolated category pages; no shared dashboards or prior-owner files were changed.')}
<div class="cards-grid">'''
    for i, (key, label, href) in enumerate(NAV, 1):
        blurbs = {
            "results": "136 reconciled finals, the Week 10 slate, and four bye rows.",
            "lines": "Symmetric PF/G + opponent PA/G baselines and dated two-book quotes.",
            "injuries": "76 selected report/depth observations plus 32 team chart sources.",
            "sources": "58 source records, capture dates, coverage and caveats.",
            "correlations": "Four computed descriptive correlations; three paired-prop rows left blank.",
            "strategies": "Six hypotheses with current evidence and explicit missing inputs.",
            "validation": "Eleven fail-closed gates; G0 passes, G1–G10 blocked.",
            "leaderboard": "Six unranked strategies and three unavailable luck/reward metrics.",
            "questions": "Sixteen known-versus-missing decision questions.",
            "suggestions": "Twelve review options with tradeoffs; all await a decision.",
            "flagged": "Twenty open findings on scope, prices, injury evidence, and validation.",
            "audit": "Line-indexed repository inventory with source-basis labels and downloads.",
        }
        body += f'<a class="page-card" href="{href}"><span class="card-number">{i:02d} / 12</span><h3>{esc(label)}</h3><p>{esc(blurbs[key])}</p><span class="arrow">Open section →</span></a>'
    body += f'''</div>
{section('What the backtest does not say', 'Week 2–9 results are one season of forecast evaluation, not a betting-skill test.')}
<div class="split-grid"><div class="panel"><h3>Measured</h3><p>MAE {esc(wf['mae_points'])}; mean error {esc(wf['mean_error_actual_minus_projected'])}; projected/actual margin r {esc(wf['pearson_projected_vs_actual']['r'])}, p {esc(wf['pearson_projected_vs_actual']['p'])}.</p></div><div class="panel"><h3>Missing by design</h3><p>Timestamped closing prices, accepted bets, settlement rules, net returns, clustered uncertainty, prospective pre-registration, and independent later-season validation.</p></div></div>
{section('Download the core snapshot', 'The row-level CSVs retain source URLs and explicit blanks.')}
<div class="data-links">{''.join(f'<a href="data/{name}" download>{esc(label)}</a>' for name,label in [('games_2026_w1_w9.csv','136-game log'),('standings_2026_w10.csv','Standings'),('schedule_2026_w10.csv','Week 10 schedule'),('model_lines_2026_w10.csv','Baseline lines'),('market_quotes_2026_w10.csv','28 quote rows'),('injuries_depth_w10.csv','Selected availability rows'),('correlations_2026.csv','Correlation results'),('validation_gates_2026.csv','Validation gates')])}</div>
'''
    return page("Overview", "Research desk", "Dated and source-linked; descriptive only.", "home", body)


def build_results() -> str:
    recon = read_json("game_reconciliation.json")
    games = read_csv("games_2026_w1_w9.csv")
    schedule = read_csv("schedule_2026_w10.csv")
    weeks = ", ".join(f"W{k}: {v}" for k, v in recon["week_counts"].items())
    body = f'''{callout('Reconciliation: PASS', f"{recon['games']} completed games; {recon['teams_reconciled']}/32 teams; every W-L-T/PF/PA field matches NFL standings; {len(recon['mismatches'])} mismatches.", 'pass')}
<div class="stats-row" style="margin:16px 0"><div class="stat-pill"><strong>{len(games)}</strong><span>finals</span></div><div class="stat-pill"><strong>{len(schedule)}</strong><span>Week 10 games + byes</span></div><div class="stat-pill"><strong>{sum(r['status']=='SCHEDULED' for r in schedule)}</strong><span>scheduled games</span></div><div class="stat-pill"><strong>{sum(r['status']=='BYE' for r in schedule)}</strong><span>bye teams</span></div></div>
<p class="muted">Game counts by week: {esc(weeks)}. A bye row carries the official schedule URL; it does not imply an injury status.</p>
{section('Week 10 schedule', 'Times are displayed as transcribed from the NFL schedule/injury source; four BYE teams have no game link.')}
{table(schedule,[('date','Date','text'),('kickoff_et','Kickoff ET','text'),('away_team','Away / bye team','text'),('home_team','Home','text'),('venue','Venue','text'),('status','Status','badge'),('game_url','NFL game page','url'),('source_schedule_url','NFL schedule','url')],'Week 10 schedule and bye coverage','schedule-table')}
{section('Completed results through Week 9', 'Every game row links to an NFL game page; the standings check is a separate aggregate reconciliation.')}
<div class="table-toolbar"><p>All final results in the canonical input log.</p>{download_links([('games_2026_w1_w9.csv','Download game log'),('game_reconciliation.json','Reconciliation JSON')])}</div>
{table(games,[('week','Week','text'),('date','Date','text'),('away_team','Away','text'),('away_points','Away points','text'),('home_team','Home','text'),('home_points','Home points','text'),('status','Status','badge'),('source_url','NFL game source','url'),('schedule_url','NFL schedule source','url')],'Officially linked completed-game rows','games-table')}
'''
    return page("Results & schedule", "Result reconciliation", "Official results through Week 9 and the Week 10 slate.", "results", body)


def build_lines() -> str:
    lines = read_csv("model_lines_2026_w10.csv")
    quotes = read_csv("market_quotes_2026_w10.csv")
    body = f'''{callout('Exploratory baseline only', 'These score lines are not picks, fair odds, or a recommendation. No home-field term or numerical injury adjustment is applied. Market comparisons are dated two-book arithmetic, not expected value.', 'warning')}
{section('Week 10 model lines', 'Team PF/G and opponent PA/G are averaged symmetrically; each score is rounded to a half-point.')}
<div class="table-toolbar"><p>All 14 scheduled games; injury-adjusted fields intentionally blank.</p>{download_links([('model_lines_2026_w10.csv','Download model lines'),('market_quotes_2026_w10.csv','Download quote rows')])}</div>
{table(lines,[('date','Date','text'),('kickoff_et','Kickoff ET','text'),('away_team','Away','text'),('home_team','Home','text'),('base_away_points','Away score','text'),('base_home_points','Home score','text'),('model_home_spread','Model home spread','text'),('model_total','Model total','text'),('injury_adjustment_away_points','Away injury points','text'),('injury_adjustment_home_points','Home injury points','text'),('market_home_spread_mean_two_books','Two-book home spread','text'),('market_total_mean_two_books','Two-book total','text'),('model_home_margin_minus_market_home_line','Margin comparison','text'),('model_total_minus_market_total','Total comparison','text'),('source_url','NFL game','url'),('source_market_urls','Book event pages','multi_url')],'Baseline and market comparison (not recommendations)','model-lines')}
{section('Source quote rows', 'DraftKings and FanDuel remain separate; differing sportsbook quotes are not an error.')}
{table(quotes,[('date','Game date','text'),('away_team','Away','text'),('home_team','Home','text'),('book','Book','text'),('away_spread','Away spread','text'),('away_spread_american_odds','Away price','text'),('home_spread','Home spread','text'),('home_spread_american_odds','Home price','text'),('total_points','Total','text'),('over_american_odds','Over price','text'),('under_american_odds','Under price','text'),('away_moneyline_american','Away ML','text'),('home_moneyline_american','Home ML','text'),('retrieved_date','Captured date','text'),('retrieved_time_utc','UTC time','text'),('timestamp_status','Time status','text'),('source_url','Operator event','url'),('board_url','Operator board','url')],'Book-level Week 10 quote snapshot','quote-rows')}
{callout('Quote caveat', 'The dynamic public pages did not expose a preserved UTC capture time or jurisdiction in this snapshot. Quotes are not known to be executable, current, or closing prices; no bet ledger or CLV is computed.', 'warning')}
'''
    return page("Own lines & market", "Baseline and quotes", "Symmetric score baselines beside distinct dated sportsbook snapshots.", "lines", body)


def build_injuries() -> str:
    injuries = read_csv("injuries_depth_w10.csv")
    coverage = read_csv("depth_chart_coverage_2026_w10.csv")
    teams = len({r["team"] for r in injuries})
    body = f'''{callout('Selective status tracker — not an all-team inactive list', f'{len(injuries)} selected report/depth observations across {teams} teams. A blank row or team is not a health clearance; midweek practice status is not final game participation.', 'warning')}
<div class="stats-row" style="margin:16px 0"><div class="stat-pill"><strong>{len(injuries)}</strong><span>selected observations</span></div><div class="stat-pill"><strong>{teams} / 32</strong><span>teams with selected injury rows</span></div><div class="stat-pill"><strong>{len(coverage)} / 32</strong><span>club chart sources recorded</span></div><div class="stat-pill"><strong>0</strong><span>numeric injury point adjustments</span></div></div>
{section('Club chart source coverage', 'CHI, DEN, PHI, and TB were Week 10 byes; their pages are documented but do not create Week 10 injury signals.')}
{table(coverage,[('team','Team','text'),('team_name','Club','text'),('week10_status','Week 10 status','badge'),('chart_retrieved_on','Retrieved','text'),('chart_displayed_as_of','Page as-of','text'),('authority_note','Authority / timing note','text'),('scope_use','Use in this snapshot','text'),('chart_source_url','Club chart','url')],'32-team club-site chart coverage','chart-coverage')}
{section('Selected report and depth-chain observations', 'DNP/LP/OUT/IR/status announcements and club chart ordering are retained as separate evidence.')}
<div class="table-toolbar"><p>Participation and confirmed replacement fields are intentionally unfilled.</p>{download_links([('injuries_depth_w10.csv','Download 76-row tracker'),('depth_chart_coverage_2026_w10.csv','Download chart coverage')])}</div>
{table(injuries,[('team','Team','text'),('side','Side','text'),('position','Pos.','text'),('affected_player','Player','text'),('reported_status','Reported status','badge'),('reported_body_part_or_reason','Reason / body part','text'),('published_depth_chain','Published chain','text'),('deepest_listed_string_slot','Deepest listed slot','text'),('actual_week10_participation','Actual participation','text'),('expected_starter_after_report','Expected replacement','text'),('verification_status','Verification','badge'),('note','Evidence note','text'),('source_url','NFL report/index','url'),('official_depth_chart_url','Club chart','url'),('news_source_url','NFL news','url')],'Selected Week 10 injury/depth observations','injury-table')}
{callout('No slot-to-points conversion', 'No validated player-specific or position-specific replacement coefficient was found. The model’s injury adjustment columns remain blank; chart rank is not a score penalty.', 'danger')}
'''
    return page("Injury & depth", "Availability evidence", "Selected status/depth observations with explicit participation gaps.", "injuries", body)


def build_sources() -> str:
    sources = read_csv("sources_registry.csv")
    body = f'''{callout('Source list is not a live feed', 'Each record includes an official publisher URL and a retrieval date/scope. NFL pages and sportsbook boards are dynamic and were not archived as raw source responses with a content hash.', 'warning')}
<div class="table-toolbar"><p>{len(sources)} registered sources, including NFL, NFL Operations, two sportsbook boards, and 32 club chart pages.</p>{download_links([('sources_registry.csv','Download source register'),('depth_chart_coverage_2026_w10.csv','Download 32-chart coverage')])}</div>
{table(sources,[('source_id','ID','text'),('category','Category','text'),('title','Source title','text'),('checked_on','Checked','text'),('scope_checked','Scope inspected','text'),('caveat','Caveat','text'),('official_url','Publisher page','url')],'Source register','source-register')}
{section('Provenance rules', 'What a source link does and does not prove.')}
<div class="split-grid"><div class="panel"><h3>Primary evidence</h3><p>NFL schedules, game pages, standings, team stats and injury reports anchor the current NFL facts. Club pages are the publisher for their listed depth order; their labels and freshness vary.</p></div><div class="panel"><h3>Separate operator evidence</h3><p>DraftKings and FanDuel are sportsbook publishers, not the NFL. Each book quote is retained separately, with date-only timing and no claim of user-specific availability.</p></div><div class="panel"><h3>Derived outputs</h3><p>Line formulas and correlations are generated by the isolated engine. Their output provenance includes inputs and formula, not an external claim that the result is accurate or useful for betting.</p></div><div class="panel"><h3>Legacy material</h3><p>Earlier secondary market/history datasets stay flagged in the audit. This session did not rewrite or certify other sessions’ files.</p></div></div>
'''
    return page("Sources", "Evidence register", "Source links, inspection scope, and the limits of dynamic snapshots.", "sources", body)


def build_correlations() -> str:
    rows = read_csv("correlations_2026.csv")
    body = f'''{callout('Descriptive statistics, not independent skill evidence', 'The 32-team standings metrics are ecological and share the same season inputs. The 120-game forecast correlation has team/week dependence that the ordinary p-value and Fisher interval do not adjust for.', 'warning')}
{section('Correlation register', 'Pearson r, ordinary two-sided p-value, Fisher-z 95% interval, and sample size where computable.')}
{table(rows,[('correlation_id','ID','text'),('metric_x','Metric X','text'),('metric_y','Metric Y','text'),('pearson_r','Pearson r','text'),('p_value_two_sided','Two-sided p','text'),('ci95_low_fisher_z','95% CI low','text'),('ci95_high_fisher_z','95% CI high','text'),('n','n','text'),('status','Status','badge'),('caveat','Caveat','text'),('source_url','Source','url'),('source_game_results_url','Results source','url')],'Computed and not-computable correlations','correlation-table')}
<div class="panel" style="margin-top:16px"><h3>Current values</h3><p>PF/G vs win percentage: <strong>r = 0.693836</strong>; PA/G vs win percentage: <strong>r = -0.666179</strong>; net points/G vs win percentage: <strong>r = 0.875830</strong> (n=32 each). Walk-forward projected vs actual margin: <strong>r = 0.135006</strong> (n=120).</p><p>Player-prop and joint-leg rows are blank because paired game-level outcomes, exact prop lines/prices and settlements were not archived. No zero correlation or independence is implied.</p></div>
{download_links([('correlations_2026.csv','Download correlation table'),('walk_forward_2026_w2_w9.csv','Download walk-forward games'),('walk_forward_summary.json','Download walk-forward summary')])}
'''
    return page("Correlations", "Association analysis", "Computed team/game correlations and intentionally blank player-prop rows.", "correlations", body)


def build_strategies() -> str:
    rows = read_csv("strategies_2026.csv")
    body = f'''{callout('A hypothesis is not a strategy proven to work', 'The statuses below say what current evidence supports. None has an evaluated net return or passed the validation matrix.', 'warning')}
{content_cards(rows,'name',[('strategy_id','ID'),('category','Category'),('status','Status')],[('hypothesis','Hypothesis'),('signal_fields','Potential signal fields'),('current_evidence','Current evidence'),('required_missing','Required missing evidence')],[('source_url','Primary source'),('secondary_source_url','Supporting source')],'strategy_id','status')}
{section('Shared restrictions', 'Every new test should be time-stamped, registered before outcomes, and compared against a declared benchmark.')}
<div class="split-grid"><div class="panel"><h3>Single-game spread / total</h3><p>Currently research-only. No executable quote time, closing price, calibration, settlement ledger, holdout return, or clustered uncertainty.</p></div><div class="panel"><h3>Parlays and player props</h3><p>Blocked until the exact offered combo prices, paired player/game outcomes, dependence, rules, and settlement history are available.</p></div><div class="panel"><h3>Availability-adjusted lines</h3><p>Blocked until final actives and replacement participation are linked to a validated player/position-specific value coefficient.</p></div><div class="panel"><h3>Selection / ranking</h3><p>No strategy is currently qualified. A missing field is not a zero, a pass, or a positive edge.</p></div></div>
{download_links([('strategies_2026.csv','Download six strategy records'),('validation_gates_2026.csv','Download validation gates')])}
'''
    return page("Strategies", "Strategy hypotheses", "Six single-game, parlay, prop, and availability strategy families—none validated.", "strategies", body)


def build_validation() -> str:
    rows = read_csv("validation_gates_2026.csv")
    passed = sum(row["status"] == "PASS" for row in rows)
    body = f'''{callout(f'Fail-closed status: {passed} of {len(rows)} gates pass', 'G0 source integrity/reconciliation passes as a project-level input check. G1–G10 are blocked. These are project governance rules, not NFL certification standards.', 'warning')}
{table(rows,[('gate_id','Gate','text'),('gate_name','Name','text'),('mandatory_rule','Requirement','text'),('current_evidence','Current evidence','text'),('status','Status','badge'),('policy_note','Policy note','text'),('source_url','Source reference','url')],'Eleven validation gates','gate-table')}
{section('Interpretation', 'Passing one integrity gate does not establish model calibration, ROI, legal eligibility, or skill.')}
<div class="panel"><p>G0 records schema/source structure and the completed-games reconciliation. G1 (quote timestamp), G2 (pre-registration), G3 (chronology), G4 (power/holdout), G5 (multiplicity), G6 (calibration/joint dependence), G7 (net returns/CLV), G8 (final lineup verification), G9 (luck-adjusted ranking), and G10 (reward governance) remain blocked because the required evidence is absent.</p></div>
{download_links([('validation_gates_2026.csv','Download gate matrix'),('flagged_review.csv','Download review flags')])}
'''
    return page("Validation gates", "Qualification", "Eleven project-defined fail-closed tests; only source integrity currently passes.", "validation", body)


def build_leaderboard() -> str:
    rows = read_csv("leaderboard_2026.csv")
    luck = read_csv("luck_skill_2026.csv")
    body = f'''{callout('No qualified entries — no rankings or rewards', 'All six rows have zero graded bets, blank rank/ROI/skill fields, and a NO_QUALIFIED_ENTRY status. No reward is funded, offered, or awarded.', 'danger')}
{section('Leaderboard status', 'The empty metrics are intentional. No placeholder ranks or model scores are fabricated.')}
{table(rows,[('strategy_id','ID','text'),('strategy_name','Strategy','text'),('category','Category','text'),('rank','Rank','text'),('graded_bets','Graded bets','text'),('win_rate','Win rate','text'),('net_roi','Net ROI','text'),('risk_adjusted_skill_score','Skill score','text'),('luck_adjusted_ci','Luck-adjusted CI','text'),('gates_passed','Gates','text'),('status','Status','badge'),('proposed_reward','Reward status','text'),('source_url','Source','url'),('strategy_source_url','Strategy source','url')],'Unranked strategy records','leaderboard-table')}
{section('Luck, sample size, and reward status', 'No numerical output is estimable without a registered, settled, and auditable result stream.')}
{table(luck,[('item_id','ID','text'),('metric','Metric','text'),('estimate','Estimate','text'),('n','n','text'),('method','Method proposed','text'),('status','Status','badge'),('note','Reason blank','text'),('source_url','Reference','url')],'Unavailable luck/skill and reward metrics','luck-table')}
{callout('Reward governance is unresolved', 'No competition charter, funded award amount, eligibility review, independent audit process, or dispute policy was verified.', 'warning')}
{download_links([('leaderboard_2026.csv','Download leaderboard'),('luck_skill_2026.csv','Download luck/skill status')])}
'''
    return page("Leaderboard", "Qualification status", "No graded bets, no rank, no validated skill score, and no funded reward.", "leaderboard", body)


def build_questions() -> str:
    rows = read_csv("decision_questions.csv")
    body = f'''{callout('Decision aid, not an approval or legal opinion', 'The row-level matrix separates known evidence, missing information, the answer needed before a decision, and concrete discovery steps.', 'warning')}
{content_cards(rows,'question',[('question_id','Question'),('status','Status')],[('known_information','Known information'),('missing_information','Missing information'),('answer_needed_before_decision','Answer needed before decision'),('discovery_steps','Discovery pathway')],[('source_url','Source'),('supporting_source_url','Supporting source')],'question_id','status')}
{download_links([('decision_questions.csv','Download 16-question matrix')])}
'''
    return page("Decision Q&A", "Known and missing evidence", "Sixteen questions that must be resolved before stronger decisions or claims.", "questions", body)


def build_suggestions() -> str:
    rows = read_csv("site_suggestions.csv")
    body = f'''{callout('All suggestions await human review', 'No root navigation, shared site, prior-owner NFL desk, or sister project was changed. The work remains isolated in this session namespace.', 'warning')}
{content_cards(rows,'title',[('suggestion_id','ID'),('decision_area','Area'),('decision','Decision')],[('option','Option(s)'),('decision_basis','Basis'),('implementation_status','Current status'),('tradeoffs','Tradeoffs')],[('source_url','Primary source'),('supporting_source_url','Supporting source')],'suggestion_id','decision')}
{download_links([('site_suggestions.csv','Download all 12 review suggestions')])}
'''
    return page("Suggestions for review", "Review before integration", "Options, tradeoffs, and scope decisions—not silently implemented changes.", "suggestions", body)


def build_flagged() -> str:
    rows = read_csv("flagged_review.csv")
    high = sum(row["severity"] == "HIGH" for row in rows)
    body = f'''{callout(f'{len(rows)} open review items · {high} high severity', 'Open/nonblocking means the static research snapshot can be published with the limitation visible; it does not mean the claim is verified or the risk resolved.', 'warning')}
{content_cards(rows,'topic',[('flag_id','Flag'),('severity','Severity'),('status','Status')],[('finding','Finding'),('impact','Impact'),('action','Action')],[('source_url','Primary source'),('secondary_source_url','Supporting source')],'flag_id','severity')}
<div class="panel" style="margin-top:16px"><h3>Audit files are separate evidence</h3><p>The repository line audit is an index of in-scope legacy files; it is not a fresh external re-fetch of every historical value. See the <a href="audit.html">Repository Audit page</a> and download the line-indexed CSV there.</p></div>
{download_links([('flagged_review.csv','Download 20 review flags')])}
'''
    return page("Flagged for review", "Open limitations", "Specific source, scope, timing, model, and governance gaps with next actions.", "flagged", body)


def build_audit() -> str:
    summary = read_json("repo_audit_summary.json")
    status_counts = summary.get("status_counts", {})
    basis_counts = summary.get("source_basis_counts", {})
    findings = summary.get("critical_findings", [])
    files = summary.get("files_inventory", [])
    status_rows = [{"classification": k, "rows": f"{v:,}"} for k, v in sorted(status_counts.items(), key=lambda item: (-item[1], item[0]))]
    basis_rows = [{"source_basis": k, "rows": f"{v:,}"} for k, v in sorted(basis_counts.items(), key=lambda item: (-item[1], item[0]))]
    body = f'''{callout('Line inventory, not blanket certification', summary.get('scope',''), 'warning')}
<div class="metric-grid">{metric('In-scope files', f"{summary['files']:,}", 'Selected NFL/research/shared context')}{metric('Physical lines', f"{summary['physical_lines']:,}", 'Each row has a path, line, hash, classification')}{metric('Audit date', summary['as_of'], 'Date of current repository snapshot')}{metric('Legacy inputs flagged', f"{status_counts.get('FLAGGED_NONOFFICIAL_HISTORICAL_INPUT',0)+status_counts.get('FLAGGED_LEGACY_MARKET_VALUE',0):,}", 'Secondary history / legacy market rows')}</div>
{callout('Read the provenance basis', 'A ROW_SOURCE_FIELD is direct row provenance. OFFICIAL_SCOPE_REFERENCE_FALLBACK_NOT_ROW_PROVENANCE is only a scope-level official reference. OFFICIAL_COUNTERPART_FOR_FLAGGED_INPUT_NOT_INPUT_PROVENANCE points to an official comparison, not the original historic value.', 'warning')}
{section('Classification counts', 'Physical-line classification from the current run of audit_repo.py.')}
{table(status_rows,[('classification','Classification','text'),('rows','Rows','text')],'Audit classification counts','audit-status-counts')}
{section('Source-basis counts', 'Every row carries a basis label so generic references are not mistaken for direct provenance.')}
{table(basis_rows,[('source_basis','Source basis','text'),('rows','Rows','text')],'Audit source-basis counts','audit-source-counts')}
{section('Critical findings', 'These are the audit’s concise repository-level findings; see each per-line note for context.')}
{content_cards(findings,'finding',[('id','Finding ID')],[],[],'id')}
{section('In-scope file inventory', 'The complete physical-line ledger is available as CSV; the file inventory shows the selected file scope.')}
{table(files,[('path','Repository path','text'),('physical_lines','Physical lines','text'),('bytes','Bytes','text')],'Audited file inventory','audit-files')}
{section('Download the full audit', 'The CSV is intentionally large because it provides one row for each indexed physical line.')}
{download_links([('repo_audit.csv','Download line-by-line audit CSV'),('repo_audit_summary.json','Download audit summary JSON')])}
<p class="muted" style="margin-top:14px">The audit does not refetch every external URL, does not certify all legacy values, and does not modify prior-owner files. Current Week 1–9 result reconciliation is separately reported as PASS.</p>
'''
    return page("Repository audit", "Legacy-scope inventory", "A searchable line index with explicit direct-source, fallback, and comparator labels.", "audit", body)


def build() -> list[Path]:
    pages = {
        "index.html": build_index(),
        "results.html": build_results(),
        "lines.html": build_lines(),
        "injuries.html": build_injuries(),
        "sources.html": build_sources(),
        "correlations.html": build_correlations(),
        "strategies.html": build_strategies(),
        "validation.html": build_validation(),
        "leaderboard.html": build_leaderboard(),
        "questions.html": build_questions(),
        "suggestions.html": build_suggestions(),
        "flagged.html": build_flagged(),
        "audit.html": build_audit(),
    }
    out = []
    for name, content in pages.items():
        path = ROOT / name
        path.write_text(content, encoding="utf-8", newline="\n")
        out.append(path)
    print(f"Built {len(out)} static pages in {ROOT}.")
    return out


if __name__ == "__main__":
    build()

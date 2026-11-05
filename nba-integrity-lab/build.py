#!/usr/bin/env python3
"""Build the static, source-linked NBA Integrity Desk from reviewed snapshots."""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import urlparse

import model

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
BASE = "54e8dee596d49731c3da535a1f77b01cd0c295d5"
REPO_BASE = f"https://github.com/sassnarep3-star/Own5/tree/{BASE}"
OLD_SUMMARY = f"https://github.com/sassnarep3-star/Own5/blob/{BASE}/research/nba-signal-lab/EXECUTIVE_SUMMARY.md#L50-L70"
OLD_COMPUTE = f"https://github.com/sassnarep3-star/Own5/blob/{BASE}/nba-signal-lab/compute.py#L350-L395"
OLD_CORRELATIONS = f"https://github.com/sassnarep3-star/Own5/blob/{BASE}/docs/correlations.html"
MODEL_REPO = "https://github.com/sassnarep3-star/Own5/blob/main/nba-integrity-lab/model.py"
NBA_GLOSSARY = "https://www.nba.com/stats/help/glossary"
NBA_LEADERS = "https://www.nba.com/stats/leaders?Season=2025-26"
NBA_SPREADS = "https://sportsbook.draftkings.com/page/nba-finals-odds"
OLD_SPREAD = f"https://github.com/sassnarep3-star/Own5/blob/{BASE}/nba-signal-lab/compute.py#L239-L251"
NBA_GAMES = "https://www.nba.com/games?date=2026-11-06"
JAZZ_SCHEDULE = "https://www.nba.com/jazz/schedule"
MAVS_SCHEDULE = "https://www.nba.com/mavs/schedule"
NIST_INTERVAL = "https://www.itl.nist.gov/div898/handbook/prc/section2/old.prc271.htm"

NAV = [
    ("index.html", "Overview", "01"),
    ("summary.html", "Executive summary", "02"),
    ("lines.html", "Own model lines", "03"),
    ("strategies.html", "Strategies", "04"),
    ("correlations.html", "Correlations", "05"),
    ("validation.html", "Validation gates", "06"),
    ("leaderboard.html", "Leaderboard", "07"),
    ("data.html", "Verified inputs", "08"),
    ("sources.html", "Sources", "09"),
    ("review.html", "Flagged for Review", "10"),
]

STRATEGIES = [
    ("S01", "Efficiency spread", "Single", "Compare a frozen model handicap with a separately verified pregame spread and price.", "No executable quote, preregistered holdout, or settled ledger.", model.NBA_ADVANCED),
    ("S02", "Pace and efficiency total", "Single", "Test a pace-based total against a timestamped market total, including overtime and push rules.", "No verified market line, settlement rules, or calibration.", model.NBA_ADVANCED),
    ("S03", "Player volume", "Player prop", "Evaluate minutes, availability and role as pregame predictors of a player counting statistic.", "No point-in-time minutes or availability model, quote, or holdout.", model.NBA_LOG),
    ("S04", "Two-game combination", "Cross-game parlay", "Model the joint outcome of separately specified legs from different games; compare with the actual combined price.", "No paired, timestamped parlay ledger; dependence is unknown.", model.SPORTSBOOK_SGP),
    ("S05", "Points + made threes", "Same-game prop combo", "Test a joint model for points and made threes, rather than multiply marginal hit rates by default.", "Exploratory selected sample only; no verified combo price or test set.", model.NBA_LOG),
    ("S06", "Points + rebounds + assists", "Same-game prop combo", "Estimate the full three-leg joint event from an appropriate conditional model and matched settlement rules.", "No prospective three-leg observations, quoted payout, or validated joint model.", model.NBA_LOG),
    ("S07", "Teammate assists + points", "Same-game prop combo", "Test paired teammate assists and points with availability and shared game state accounted for.", "Matched teammate-game observations and market prices are not verified.", model.NBA_LOG),
]

GATES = [
    ("G01", "Source and coverage", "Review each input against an official source; disclose missing fields and sample selection.", model.NBA_ADVANCED),
    ("G02", "Point-in-time record", "Verify feature and quote timestamps precede the decision, and the decision precedes the event.", model.NBA_INJURY),
    ("G03", "Registration", "Freeze the hypothesis, model, trial family, test and holdout before the holdout starts.", model.NBA_LOG),
    ("G04", "Executable market and rules", "Record the actual price, market, operator, stake, and rules for pushes, voids, overtime and combo settlement.", model.SPORTSBOOK_SGP),
    ("G05", "Out-of-sample outcomes", "Use an untouched chronological holdout with verified settlements and no feature leakage.", NBA_GAMES),
    ("G06", "Sample floor", "At least 200 graded bets is a proposed minimum, not evidence of adequate power or skill by itself.", model.NIST_BINOMIAL),
    ("G07", "Dependence", "Use paired outcome data and an appropriate clustered method; do not infer independence from lag-1 correlation.", model.NBA_LOG),
    ("G08", "Multiplicity and test", "A valid preregistered one-sided test must satisfy p ≤ 0.05 / number of registered trials; adapt the test to actual outcomes.", model.NIST_BINOMIAL),
    ("G09", "Independent replication", "Require a later, untouched replication; one successful split is not enough.", NBA_GAMES),
    ("G10", "Reproducibility and controls", "Reproduce inputs and decisions and document stake limits, conflicts, eligibility and reward controls.", model.NBA_INJURY),
]


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


class Markup(str):
    pass


def badge(text: str, kind: str = "neutral") -> Markup:
    return Markup(f'<span class="badge {e(kind)}">{e(text)}</span>')


def official_url(url: str) -> bool:
    try:
        p = urlparse(url)
        host = (p.hostname or "").lower()
    except ValueError:
        return False
    domains = ("nba.com", "nist.gov", "draftkings.com", "github.com")
    return p.scheme == "https" and any(host == d or host.endswith("." + d) for d in domains)


def source_links(sources: list[tuple[str, str]]) -> str:
    if not sources or not all(official_url(url) for _, url in sources):
        raise ValueError(f"every data row must have a permitted official source link: {sources!r}")
    return '<span class="sources">' + ' '.join(
        f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} <span aria-hidden="true">↗</span></a>'
        for label, url in sources) + '</span>'


def table(table_id: str, title: str, description: str, headers: list[str],
          rows: list[tuple[list[object], list[tuple[str, str]]]], search: bool = False) -> str:
    heading = f'<div class="table-heading"><div><h2 id="{e(table_id)}-title">{e(title)}</h2><p>{e(description)}</p></div>'
    if search:
        heading += (f'<label class="search"><span class="sr-only">Search {e(title)}</span>'
                    f'<input type="search" placeholder="Search rows…" data-search="{e(table_id)}" '
                    f'aria-controls="{e(table_id)}"></label>')
    heading += '</div>'
    content = []
    for cells, sources in rows:
        if len(cells) != len(headers):
            raise ValueError(f"{table_id}: expected {len(headers)} cells, got {len(cells)}")
        rendered = []
        for value in cells:
            if value is None:
                rendered.append('<td class="missing" aria-label="Unverified: value unavailable"></td>')
            elif isinstance(value, Markup):
                rendered.append(f'<td>{value}</td>')
            else:
                rendered.append(f'<td>{e(value)}</td>')
        content.append('<tr>' + ''.join(rendered) + '<td>' + source_links(sources) + '</td></tr>')
    return (f'<section class="panel table-panel" aria-labelledby="{e(table_id)}-title">{heading}'
            f'<div class="table-wrap"><table id="{e(table_id)}"><thead><tr>'
            + ''.join(f'<th scope="col">{e(h)}</th>' for h in headers + ["Official source / context"])
            + '</tr></thead><tbody>' + ''.join(content) + '</tbody></table></div>'
            + (f'<p class="empty-state" data-empty="{e(table_id)}" hidden>No matching rows.</p>' if search else '')
            + '</section>')


def card(label: str, value: str, detail: str, href: str, kind: str = "") -> str:
    return (f'<a class="stat-card {e(kind)}" href="{e(href)}"><span class="stat-label">{e(label)}</span>'
            f'<strong>{e(value)}</strong><span class="stat-detail">{e(detail)}</span>'
            f'<span class="stat-arrow" aria-hidden="true">↗</span></a>')


def line_rows(lines: list[dict]) -> list:
    rows = []
    for line in lines:
        sources = [("NBA report", line["source_url"]), ("NBA stats", line["team_source_home"])]
        if line["time_source_url"] != line["source_url"]:
            sources.append(("Tip source", line["time_source_url"]))
        spread = line["model_home_spread"]
        spread_text = "0.0" if abs(spread) < 0.05 else f"{spread:+.1f}"
        rows.append(([f"{line['away']} @ {line['home']}", line["time_as_published"],
                      spread_text, f"{line['model_total']:.1f}", None, None,
                      badge("Unverified market", "warning")], sources))
    return rows


def snapshot_table(lines: list[dict], table_id: str = "line-table") -> str:
    return table(table_id, "November 6 model snapshot",
                 "Research estimates, not bookmaker quotes. The home spread is the negative of the model home margin.",
                 ["Matchup", "Tip as published", "Model home spread", "Model total", "Market spread", "Market total", "Status"],
                 line_rows(lines))


def overview(r: dict, audit: dict) -> str:
    b = r["analysis"]["binary"][0]
    cards = ''.join([
        card("MODEL SNAPSHOT", str(len(r["lines"])), "Nov 6 matchups", "lines.html", "blue"),
        card("AUDITED SAMPLE", str(len(r["logs"])), "selected player-games", "data.html"),
        card("QUALIFIED", "0", "strategies · no rewards", "leaderboard.html"),
        card("LEGACY REVIEW", str(audit["totals"]["missing_context_links"]), "rows need a source-link check", "review.html", "amber"),
    ])
    return f'''<div class="hero"><div><div class="eyebrow"><span class="dot"></span> NBA / EVIDENCE-FIRST RESEARCH</div>
<h1>Own the line.<br><span>Know the evidence.</span></h1><p>A clear workspace for originating NBA research lines, testing strategy ideas and separating measured signals from assumptions.</p>
<div class="hero-actions"><a class="button primary" href="lines.html">Explore model lines <span aria-hidden="true">↗</span></a><a class="button secondary" href="summary.html">Read executive summary</a></div></div>
<div class="hero-note"><span class="mini-label">CURRENT POSITION</span><strong>Research, not a bet.</strong><p>No strategy has passed the gates. Market prices, actual returns and prize funding remain unverified.</p><a href="review.html">See all review items ↗</a></div></div>
<div class="stats-grid">{cards}</div>
<div class="callout"><div class="callout-icon">!</div><div><strong>This is a frozen snapshot, not a live odds feed.</strong><p>Inputs were reviewed on November 5, 2026. Availability was incomplete in the 4:00 p.m. ET NBA injury report; team statistics and schedules can change.</p></div><a href="review.html">View limitations →</a></div>
{snapshot_table(r['lines'], 'overview-lines')}
<div class="split-grid"><section class="panel insight"><span class="eyebrow">WHAT THE DATA ACTUALLY SAYS</span><h2>Dependence matters.</h2><p>In the selected Edwards sample, points ≥25 and threes ≥3 occurred together <strong>{b['n11']} of {b['n']} times</strong>. The observed joint rate was {b['joint']:.1%}; multiplying the two sample marginals gives {b['product']:.1%}.</p><p class="muted">Exploratory only: one player, 25 appearances, chosen after the season. This does not establish a tradeable edge.</p><a class="text-link" href="correlations.html">Inspect the calculations →</a></section>
<section class="panel insight"><span class="eyebrow">THE COMPETITION</span><h2>Evidence before ranking.</h2><p>Singles, cross-game parlays and player-prop combinations use the same fail-closed gates. No verified results means no rank, no ROI and no cash reward.</p><p class="muted">Luck cannot be eliminated. Replication and uncertainty controls can reduce false confidence.</p><a class="text-link" href="leaderboard.html">See the leaderboard →</a></section></div>'''


def summary(r: dict, audit: dict) -> str:
    a = r["analysis"]
    rows = [
        (["Objective", "Originate research lines and evaluate singles, parlays and prop combinations.", "Proposed research", None], [("NBA glossary", NBA_GLOSSARY)]),
        (["Model snapshot", f"{len(r['lines'])} Nov 6 matchups from 18 team rows; estimates are model calculations, not NBA-published lines.", "Unvalidated", None], [("NBA teams", model.NBA_ADVANCED), ("NBA report", model.NBA_INJURY_SNAPSHOT)]),
        (["Player correlations", f"One selected player; {len(r['logs'])} reviewed appearances. Points × made threes r = {a['continuous'][0]['r']:.3f}.", "Exploratory", None], [("NBA player log", model.NBA_LOG)]),
        (["Joint hit example", f"Points ≥25 and threes ≥3: {a['binary'][0]['n11']}/{a['binary'][0]['n']} observed; joint {a['binary'][0]['joint']:.1%} vs {a['binary'][0]['product']:.1%} product.", "Not a price", None], [("NBA player log", model.NBA_LOG)]),
        (["Luck and skill", f"Hypothetical 30 wins in 50 at −110: exact one-sided null tail {a['tail_30_of_50']:.3f}, under independent fixed-probability assumptions.", "Illustration only", None], [("NIST binomial", model.NIST_BINOMIAL)]),
        (["Competition", "No settled bets, qualified strategies, ranks or funded cash awards in this desk.", "Blocked", None], [("Operator example", model.SPORTSBOOK_SGP), ("NIST", model.NIST_BINOMIAL)]),
        (["Repository audit", f"Static baseline scan: {audit['totals']['pages']} HTML pages, {audit['totals']['rows']} data rows, {audit['totals']['missing_context_links']} without an allowlisted context link.", "Presence check, not fact verification", None], [("GitHub baseline", REPO_BASE)]),
        (["Prior report corrections", "Prior home-margin/spread sign, scorer ranking, joint-rate direction and independence claims require correction; owner requests are logged.", "Flagged for Review", None], [("NBA leaders", NBA_LEADERS), ("Older calculation", OLD_SPREAD), ("Spread definition", NBA_SPREADS)]),
    ]
    return '''<div class="section-intro"><span class="eyebrow">DECISION BRIEF</span><h1>Executive summary</h1><p>The project is a research workspace, not an active sportsbook or a proof of profitability. Its most important outcome is an honest separation between source facts, model outputs and unresolved evidence.</p></div>''' + table(
        "summary", "What matters", "Blank performance cells mean no value was verified.",
        ["Area", "Finding", "Assessment", "Verified ROI"], rows) + '''<div class="callout"><div class="callout-icon">!</div><div><strong>Bottom line</strong><p>No manual entry is needed to browse this static report. Automatic future refresh, real bookmaker data, prospective validation and funded rewards are not in place.</p></div></div>'''


def lines_page(r: dict) -> str:
    params = [
        (["Net-rating shrinkage", "20 games", "Analyst choice made after viewing the data; not optimized or preregistered."], [("Model code", MODEL_REPO), ("NBA stats", model.NBA_ADVANCED)]),
        (["Home-court adjustment", "0 points", "Analyst assumption, not a verified estimate of home advantage."], [("Model code", MODEL_REPO), ("NBA stats", model.NBA_ADVANCED)]),
        (["Total", "Average pace × averaged offense/opposing defense", "Uses rounded team ratings; no separate overtime or injury adjustment."], [("Model code", MODEL_REPO), ("NBA glossary", NBA_GLOSSARY)]),
        (["Market price, edge and calibrated win probability", None, "No verified quote or distribution; cells remain blank."], [("NBA report", model.NBA_INJURY_SNAPSHOT)]),
    ]
    return '''<div class="section-intro"><span class="eyebrow">LINE ORIGINATION</span><h1>Own model lines</h1><p>A transparent baseline for the November 6 slate. A model line is a calculation from NBA inputs; it is not an NBA statistic, a sportsbook price, a recommendation or a validated edge.</p></div>
<div class="callout"><div class="callout-icon">!</div><div><strong>All nine are blocked for use.</strong><p>Every game had at least one team marked NOT YET SUBMITTED in the 4:00 p.m. ET injury snapshot. No market data or outcome distribution is verified. The report is not automatically refreshed.</p></div><a href="review.html">Why? →</a></div>''' + snapshot_table(r["lines"]) + table(
        "model-choices", "How the baseline works", "These are analyst choices, not official NBA values or a fitted model.",
        ["Input or assumption", "Value / formula", "Limitation"], params) + '''<section class="panel prose"><h2>Calculation, in plain language</h2><p>For the total, average the teams’ published pace and blend each offense with the opposing defense. For the home margin, shrink each team’s published net rating toward zero using <code>games / (games + 20)</code>, take their difference, and scale by half the average pace per 100 possessions. Home spread is the negative of that margin. Spread and total are separate crude baselines, not calibrated forecasts.</p><p>These ratings use a short early-season sample. Displayed NBA ratings are individually rounded; the exact underlying unrounded values are unavailable. No bookmaker comparison, uncertainty interval or player availability adjustment is supplied.</p><p><a href="data.html">Inspect all team and injury inputs →</a> · <a href="../nba-signal-lab/index.html">Earlier Signal Lab ↗</a></p></section>'''


def strategies_page() -> str:
    rows = [([sid, name, category, hypothesis, badge("Blocked", "warning"), missing],
             [("Official context", source), ("NBA injuries", model.NBA_INJURY)])
            for sid, name, category, hypothesis, missing, source in STRATEGIES]
    return '''<div class="section-intro"><span class="eyebrow">HYPOTHESIS LIBRARY</span><h1>Strategies</h1><p>Seven distinct candidate approaches across singles, parlays and player-prop combinations. All are research hypotheses, not picks; none has a verified betting edge.</p></div>''' + table(
        "strategies", "Candidate strategies", "The source link provides context; it does not certify a profitable strategy.",
        ["ID", "Strategy", "Division", "Hypothesis to test", "Status", "What is missing"], rows, True) + '''<section class="panel prose"><h2>Signal design</h2><p>Promising inputs to investigate include pace, offensive and defensive efficiency, expected minutes, injuries, rest and market movement. Each candidate must be frozen before a future test, use only information available before the event, and be compared against a transparent baseline.</p><p>A parlay needs the probability and settlement of the whole ticket, not just promising-looking legs. Shared game conditions and correlated outcomes must be modeled or empirically tested.</p><a class="text-link" href="validation.html">Review all gates →</a></section>'''


def correlations_page(r: dict) -> str:
    a = r["analysis"]
    cont = []
    for c in a["continuous"]:
        note = "Overlapping consecutive appearances; not a cross-game wager test." if "lag 1" in c["pair"] else "One player, selected appearances; descriptive only."
        cont.append(([c["pair"], str(c["n"]), f"{c['r']:+.3f}" if c["r"] is not None else None,
                      badge("Exploratory", "neutral"), note], [("NBA player log", model.NBA_LOG)]))
    cont.append((["Different-game wager hit indicators", None, None, badge("Unverified", "warning"), "No paired priced bet outcomes were verified."],
                 [("NBA games", NBA_GAMES), ("Operator context", model.SPORTSBOOK_SGP)]))
    joint = []
    for b in a["binary"]:
        joint.append(([b["pair"], str(b["n"]), f"{b['n11']}/{b['n']}", f"{b['joint']:.1%}", f"{b['product']:.1%}",
                       f"{b['lift']:.2f}×" if b["lift"] is not None else None,
                       f"{b['phi']:+.3f}" if b["phi"] is not None else None], [("NBA player log", model.NBA_LOG)]))
    t = a["triple"]
    joint.append(([t["name"], str(t["n"]), f"{t['joint_count']}/{t['n']}", f"{t['joint']:.1%}", f"{t['product']:.1%}",
                   f"{t['lift']:.2f}×" if t["lift"] is not None else None, None], [("NBA player log", model.NBA_LOG)]))
    return '''<div class="section-intro"><span class="eyebrow">DEPENDENCE ANALYSIS</span><h1>Correlations</h1><p>Calculated from 25 selected 2025–26 Anthony Edwards appearances whose displayed fields were checked against the NBA player log. These are not NBA-published coefficients or prospective betting results.</p></div>
<div class="callout"><div class="callout-icon">!</div><div><strong>Do not generalize this sample to all players or games.</strong><p>Only games in which this player appeared are included. Thresholds were chosen after the data was seen. Points contain points from made threes, and correlation does not imply a causal edge or independence.</p></div><a href="data.html">View the rows →</a></div>''' + table(
        "continuous", "Continuous correlations", "Pearson r; the lag-1 example uses 24 overlapping adjacent-appearance pairs.",
        ["Variables", "Pairs", "r", "Assessment", "Interpretation"], cont) + table(
        "joint", "Exploratory joint outcomes", "Empirical joint = all specified conditions / 25; independence product = product of sample marginals. Phi is only defined here for two legs.",
        ["Thresholds (illustrative)", "n", "Joint count", "Observed joint", "Marginal product", "Lift", "Phi"], joint) + '''<section class="panel prose"><h2>Reading the comparison</h2><p>In this sample, a lift greater than one means the observed joint rate is above the product of its sample marginals. Multiplying those marginals therefore <strong>understates</strong> the observed joint rate for that particular comparison; it does not establish the direction in other samples. A sportsbook’s actual combined quote is still needed.</p><p>The previously published claim that near-zero lag-1 player autocorrelation establishes cross-game parlay independence is not supported. The actual wager-leg correlation remains blank until matched wager outcomes are available.</p><a class="text-link" href="review.html">See the earlier-report correction →</a></section>'''


def validation_page(r: dict) -> str:
    gates = [([gid, name, rule, badge("Blocked", "warning")], [("Official context", source), ("Project code", MODEL_REPO)])
             for gid, name, rule, source in GATES]
    examples = []
    for row in r["analysis"]["binomial_examples"]:
        examples.append(([str(row["n"]), str(row["trials"]), f"{row['alpha']:.4f}", str(row["critical_wins"]),
                          f"{row['power_at_55']:.1%}", f"{row['null_tail']:.4f}"], [("NIST binomial", model.NIST_BINOMIAL)]))
    p = r["analysis"]["tail_30_of_50"]
    illustration = [(["30 wins / 50 bets", "−110 on every no-push bet", "110/210", f"{p:.4f}", "Hypothetical; not a strategy result."], [("NIST binomial", model.NIST_BINOMIAL)])]
    return '''<div class="section-intro"><span class="eyebrow">FAIL-CLOSED REVIEW</span><h1>Validation gates</h1><p>All ten gates are project policy proposals, not official NBA requirements. Each strategy starts blocked; a green data check alone cannot certify a strategy.</p></div>''' + table(
        "gates", "Mandatory gates", "Statuses reflect the absence of an audited prospective strategy ledger, not a score assigned to the source data.",
        ["ID", "Gate", "Requirement", "Current status"], gates) + table(
        "luck-example", "Luck can look like skill", "Illustrative exact tail under an independent, fixed-probability, no-push binomial model.",
        ["Hypothetical record", "Assumed price", "Null win rate", "P(X ≥ wins)", "Meaning"], illustration) + table(
        "power", "Exact binomial power examples", "Hypothetical true win rate 55% vs −110 break-even; one-sided, with Bonferroni α / trials. Values are calculated, not betting outcomes.",
        ["Graded n", "Trials", "Per-test α", "Critical wins", "Power at 55%", "Actual null tail"], examples) + '''<section class="panel prose"><h2>Assumptions and limits</h2><p>The exact binomial example assumes independent bets, the same fixed success probability, a constant −110 price, no pushes, no commission and no selection after the fact. Actual prices and dependence usually vary; use a valid predeclared method and clustered uncertainty for the real ledger instead.</p><p>At n=2,243, the exact power in this specific one-candidate example is about 79.2%, not a guarantee of 80%. The older desk’s approximately 2,243 figure is a normal approximation. Statistical significance is not a guarantee of future profitability, and luck cannot be removed from outcomes.</p><p>The gate checker validates supplied evidence fields; it cannot independently authenticate a sportsbook quote or create missing data.</p></section>'''


def leaderboard_page() -> str:
    rows = [([None, sid, name, category, "0", None, None, badge("Blocked", "warning")],
             [("Official context", source), ("NIST", model.NIST_BINOMIAL)])
            for sid, name, category, _, _, source in STRATEGIES]
    tiers = [
        (["1", "Gold research badge", None, "Proposed; only after every gate and a verified ranking."], [("NIST", model.NIST_BINOMIAL), ("Project code", MODEL_REPO)]),
        (["2", "Silver research badge", None, "Proposed; not awarded."], [("NIST", model.NIST_BINOMIAL), ("Project code", MODEL_REPO)]),
        (["3", "Bronze research badge", None, "Proposed; not awarded."], [("NIST", model.NIST_BINOMIAL), ("Project code", MODEL_REPO)]),
    ]
    return '''<div class="section-intro"><span class="eyebrow">COMPETITION DESIGN</span><h1>Leaderboard</h1><p>A fail-closed competition proposal with separate divisions for singles, cross-game parlays and prop combinations. No strategies qualify and no results or awards have been fabricated.</p></div>
<div class="callout"><div class="callout-icon">!</div><div><strong>No active cash competition.</strong><p>There is no verified prize pool, payout service, entrant ledger or funded reward. Badge tiers are design proposals, not awarded prizes.</p></div><a href="review.html">Review funding →</a></div>''' + table(
        "leaderboard", "Candidate standings", "Rank, p-value and ROI remain blank until verified settled outcomes and all gates exist.",
        ["Rank", "ID", "Strategy", "Division", "Graded bets", "p-value", "ROI", "Eligibility"], rows) + table(
        "rewards", "Proposed reward tiers", "Non-cash recognition only; cash amounts have not been verified or funded.",
        ["Place", "Proposed recognition", "Cash amount", "Status"], tiers) + '''<section class="panel prose"><h2>Proposed scoring and controls</h2><p>Within each division, compare pre-event probabilistic forecasts with a synchronized, documented benchmark using a proper log score. Use an independently audited lower confidence bound with game-level clustering; require all gates and a separate replication before ranking. This is a proposal: no baseline quotes, confidence bounds or rankings are currently available.</p><p>Fix the strategy family and stake rules in advance, prevent duplicate entries and shared-data leakage, log voids and exclusions, and declare ties and reward eligibility before any competition begins. The <a href="competition.py">offline prototype</a> can check supplied attestations and rank eligible examples, but it cannot authenticate sources or produce a clustered confidence bound. No automated entry or payout service exists.</p></section>'''


def data_page(r: dict) -> str:
    teams = [([t["abbr"], t["team"], t["gp"], t["off_rtg"], t["def_rtg"], t["net_rtg"], t["pace"]],
              [("NBA advanced", t["source_url"])]) for t in r["teams"]]
    logs = [([x["game_date"], x["matchup"], x["result"], x["minutes"], x["points"], x["three_made"], x["rebounds"], x["assists"]],
             [("Player log", x["source_url"]), ("Game", x["game_url"])]) for x in r["logs"]]
    games = [([g["game_date"], f"{g['away']} @ {g['home']}", g["time_as_published"], g["away_report"], g["home_report"]],
              [("4pm NBA report", g["source_url"])] + ([("Tip source", g["time_source_url"])] if g["time_source_url"] != g["source_url"] else []))
             for g in r["games"]]
    return '''<div class="section-intro"><span class="eyebrow">SOURCE SNAPSHOT</span><h1>Verified inputs</h1><p>Only the displayed fields below were individually compared with the official sources on November 5, 2026. A team or player link is not an endorsement of any model calculation.</p></div>
<div class="callout"><div class="callout-icon">!</div><div><strong>Dynamic sources may now differ.</strong><p>The official NBA pages change over time; this is a frozen transcription, not an archived official extract or a live feed. The injury report is the 4:00 p.m. ET snapshot.</p></div><a href="sources.html">Sources →</a></div>''' + table(
        "team-inputs", "Team inputs", "2026–27 NBA advanced-team table as read; displayed ratings can differ from their rounded subtraction by 0.1.",
        ["Team", "Name", "GP", "OffRtg", "DefRtg", "NetRtg", "Pace"], teams, True) + table(
        "player-inputs", "Player-game sample", "Anthony Edwards, 25 selected appearances in 2025–26; only the columns shown were independently reviewed.",
        ["Date", "Matchup", "Result", "Minutes", "Points", "3PM", "Rebounds", "Assists"], logs, True) + table(
        "schedule-inputs", "Schedule and report status", "Status is exactly the selected report snapshot, not a current or complete injury determination.",
        ["Date", "Matchup", "Tip as published", "Away report", "Home report"], games) + '''<section class="panel prose"><h2>Download the frozen inputs</h2><p><a href="data/team_snapshot.csv">Team snapshot CSV</a> · <a href="data/edwards_sample.csv">Player-game CSV</a> · <a href="data/schedule_snapshot.csv">Schedule / report CSV</a> · <a href="data/derived.json">Derived calculations JSON</a></p><p>These files contain only this desk’s scoped review, not a certification of the rest of the repository.</p></section>'''


def sources_page() -> str:
    sources = [
        (["S01", "NBA", "Advanced team statistics", "18 team rows: games, offensive/defensive/net ratings and pace."], [("NBA advanced", model.NBA_ADVANCED)]),
        (["S02", "NBA", "Dallas advanced team statistics", "Used to recover the Dallas row where the aggregate extraction was split."], [("Dallas advanced", "https://www.nba.com/stats/team/1610612742/advanced?Season=2026-27")]),
        (["S03", "NBA Official", "November 5 injury report, 4:00 p.m. ET", "Nine matchups and snapshot report statuses; the extracted Utah/Dallas time needs a second source."], [("NBA PDF", model.NBA_INJURY_SNAPSHOT)]),
        (["S04", "NBA / Utah Jazz", "Utah schedule", "Confirms Utah at Dallas and displays 6:00 p.m. MST on November 6."], [("Jazz schedule", JAZZ_SCHEDULE)]),
        (["S05", "NBA", "Anthony Edwards game log", "25 selected 2025–26 appearances and the specific displayed columns in the input table."], [("NBA player log", model.NBA_LOG)]),
        (["S06", "NBA", "Statistics glossary", "Official definitions of the statistics; it does not validate the project’s formulas."], [("NBA glossary", NBA_GLOSSARY)]),
        (["S07", "NIST", "Binomial distribution", "Fixed-probability binomial formula used in the hypothetical null and power examples."], [("NIST", model.NIST_BINOMIAL)]),
        (["S08", "DraftKings", "Same-game parlay explanation", "Example operator describes combinations and dynamic odds; not a current quote or universal house rule."], [("Operator page", model.SPORTSBOOK_SGP)]),
        (["S09", "NBA Official", "Current injury report index", "Reports update throughout the day; use the current index rather than assuming the snapshot is current."], [("NBA injury index", model.NBA_INJURY)]),
        (["S10", "NBA", "Games calendar", "The November calendar lists nine games on November 6; matchups came from the report."], [("NBA games", NBA_GAMES)]),
        (["S11", "GitHub", "Session-start repository tree", "Official GitHub record of the exact baseline used for the static HTML link scan."], [("Baseline tree", REPO_BASE)]),
        (["S12", "NBA", "2025–26 scoring leaders", "Ranks Dončić first, Gilgeous-Alexander second and Edwards third by points per game."], [("NBA leaders", NBA_LEADERS)]),
        (["S13", "DraftKings", "NBA point-spread explanation", "Defines negative spread for the favorite and positive spread for the underdog; not an executable quote."], [("Operator explanation", NBA_SPREADS)]),
        (["S14", "NBA / Dallas Mavericks", "Mavericks schedule", "Lists November 6 versus Utah and labels its displayed time PDT, differing from the Jazz label."], [("Mavericks schedule", MAVS_SCHEDULE)]),
    ]
    return '''<div class="section-intro"><span class="eyebrow">AUDIT TRAIL</span><h1>Sources</h1><p>Official league, government, operator and repository sources were reviewed for the narrowly stated purpose below. A source link is context; it does not automatically verify every claim on a page.</p></div>''' + table(
        "sources", "Primary source register", "External sources were read on November 5, 2026; dynamic pages can change.",
        ["ID", "Publisher", "Source", "What was checked"], sources, True) + '''<section class="panel prose"><h2>Verification boundary</h2><p>The player sample covers only the displayed 25 rows and selected fields. The team snapshot covers 18 teams playing November 6, not all 30 teams. The repository-wide scan checks static HTML link presence only; it does not review every historical claim, CSV cell, document or dynamic row.</p><p><a href="review.html">Open the full Flagged for Review register →</a></p></section>'''


def flags(audit: dict) -> list:
    count = audit["totals"]["missing_context_links"]
    return [
        ("R01", "High", "No verified sportsbook prices", "Executable pregame quotes, matched closing quotes, prop thresholds, combo payouts and settlement history are absent. Market and ROI cells are blank.", [("Operator context", model.SPORTSBOOK_SGP)]),
        ("R02", "High", "Availability incomplete", "The 4:00 p.m. ET report marks 17 of 18 team entries NOT YET SUBMITTED; all nine matchups have at least one such entry. The status can change.", [("NBA report", model.NBA_INJURY_SNAPSHOT), ("Current index", model.NBA_INJURY)]),
        ("R03", "High", "Model not calibrated", "The 20-game prior and zero home adjustment are analyst choices, not verified NBA values; there is no injury adjustment, market comparison or prospective validation.", [("NBA teams", model.NBA_ADVANCED), ("Project code", MODEL_REPO)]),
        ("R04", "High", "Selected player sample", "The 25 rows cover one player’s selected appearances only. They cannot establish population-wide relationships or future prop performance.", [("NBA log", model.NBA_LOG)]),
        ("R05", "High", "Cross-game wager correlation missing", "Near-zero lag-1 player scoring correlation does not prove independence of different-game wager legs. Matched bet outcomes were not verified.", [("NBA log", model.NBA_LOG), ("Operator context", model.SPORTSBOOK_SGP)]),
        ("R06", "High", "Earlier joint-probability direction reversed", "The older summary says multiplying marginals overstates a joint rate even while describing lift above one. For such a sample, the product is below the observed joint rate.", [("Older summary", OLD_SUMMARY), ("NBA log", model.NBA_LOG)]),
        ("R07", "Medium", "Normal approximation labeled exact", "The earlier module summary calls its power table exact, but its function uses a normal approximation. This desk computes illustrative exact tails under stated assumptions.", [("Older code", OLD_COMPUTE), ("NIST", model.NIST_BINOMIAL)]),
        ("R08", "Medium", "Shrinkage is not proof of skill", "An earlier 25-bet prior is a shrinkage illustration; it is not by itself a validated deflated Sharpe ratio test, a replication, or removal of luck.", [("Older code", OLD_COMPUTE), ("NIST", model.NIST_BINOMIAL)]),
        ("R09", "High", "Legacy correlation directions", "An older NBA page displays unsourced positive and negative directional labels. They are not verified empirical values in this desk.", [("Older page", OLD_CORRELATIONS), ("NBA log", model.NBA_LOG)]),
        ("R10", "Medium", "No automatic refresh", "This site publishes a reviewed static snapshot, not a continuously updated schedule, injury feed or market feed. Old lines become stale.", [("NBA report index", model.NBA_INJURY), ("Project code", MODEL_REPO)]),
        ("R11", "High", "No funded rewards or ranking", "Prize pool, cash amounts and actual performance are unverified; the leaderboard and badge tiers are proposals only.", [("Operator context", model.SPORTSBOOK_SGP), ("Project code", MODEL_REPO)]),
        ("R12", "Medium", "Utah–Dallas time labels", "The report extraction omits the Utah–Dallas time; the Jazz schedule says 6:00 PM MST and the Mavericks table labels 7:00 PM as PDT. We preserve the Jazz label without converting it and flag the differing labels.", [("Jazz schedule", JAZZ_SCHEDULE), ("Mavericks schedule", MAVS_SCHEDULE), ("NBA report", model.NBA_INJURY_SNAPSHOT)]),
        ("R13", "Medium", "Legacy row source links", f"{count} static data rows in the session-start tree lack a link to the conservative allowlist. Each file and row ordinal is listed below; some legitimate official domains may be outside the allowlist.", [("GitHub baseline", REPO_BASE)]),
        ("R14", "Medium", "Verification scope", "Other legacy rows, Markdown, CSV/JSON and dynamically rendered tables were not fully checked claim by claim. A present link does not prove source entailment.", [("GitHub baseline", REPO_BASE), ("NBA log", model.NBA_LOG)]),
        ("R15", "Medium", "Point-in-time source archive", "The team table is dynamic and only the reviewed transcription is stored; an immutable official raw extract and pre-event registration were not obtained.", [("NBA teams", model.NBA_ADVANCED), ("NBA report", model.NBA_INJURY_SNAPSHOT)]),
        ("R16", "High", "Earlier home-spread sign", "The older code labels home-strength minus away-strength plus home advantage as a home spread, but that expression is an expected home margin. Standard home spread uses the opposite sign. Owner correction requested; old files remain unchanged.", [("Older code", OLD_SPREAD), ("Operator spread definition", NBA_SPREADS)]),
        ("R17", "Medium", "Earlier scorer ranking", "The earlier report calls Dončić and Edwards the top two 2025–26 scorers. NBA's leaders table places Gilgeous-Alexander second and Edwards third. The sampled player choice is not a top-two selection.", [("NBA leaders", NBA_LEADERS), ("Older summary", OLD_SUMMARY)]),
    ]


def review_page(audit: dict) -> str:
    flag_rows = [([id_, severity, title, finding, badge("Needs review", "warning")], sources)
                 for id_, severity, title, finding, sources in flags(audit)]
    groups = [([g["group"], str(g["pages"]), str(g["rows"]), str(g["missing_context_links"])],
               [("Baseline tree", REPO_BASE)]) for g in audit["groups"]]
    files = [([f["path"], str(f["rows"]), str(f["missing_context_links"])], [("GitHub file", f["repo_url"])])
             for f in audit["files"]]
    findings = [([f["path"], str(f["row_ordinal"]), badge("No allowlisted link", "warning")], [("GitHub file", f["repo_url"])])
                for f in audit["findings"]]
    return '''<div class="section-intro"><span class="eyebrow">OPEN ITEMS</span><h1>Flagged for Review</h1><p>Unverified values remain blank. Findings are visible and nonblocking for publication; they do not become verified merely because a source link is present.</p></div>''' + table(
        "flags", "Review register", "High and medium are project triage labels, not claims about financial risk.",
        ["ID", "Priority", "Issue", "Finding / action", "Status"], flag_rows, True) + table(
        "audit-groups", "Legacy static HTML audit", f"Session-start commit {BASE[:7]}; a conservative domain-link presence scan only, not a semantic fact-check.",
        ["Site / folder", "HTML pages", "Data rows", "Rows without allowed link"], groups) + '''<section class="panel prose"><h2>About the row audit</h2><p>We examined tracked static HTML table data rows in the session-start commit. The allowlist is conservative; other legitimate sources can be missed. Header-only rows are excluded. Link presence does not establish that the source supports a claim. GitHub links below are official evidence of the repository file, not a source confirming its sports statistics. The row ordinal counts data rows in document order within that file.</p><p><a href="data/legacy-audit.json">Download the full machine-readable audit</a> · <a href="sources.html">Source register</a></p></section>''' + '''<details class="details"><summary>Show every audited file</summary>''' + table(
        "audit-files", "All baseline HTML files", "Every scanned file, including files with no flagged row.",
        ["File", "Data rows", "Rows without allowed link"], files, True) + '</details>' + '''<details class="details"><summary>Show exact row locations requiring review</summary>''' + table(
        "audit-rows", "Rows without an allowlisted context link", "The source field is the GitHub file evidence; the unsupported sports source remains unverified.",
        ["File", "Data-row ordinal", "Finding"], findings, True) + '</details>'


def layout(filename: str, title: str, body: str, review_count: int) -> str:
    nav = []
    for href, label, number in NAV:
        current = href == filename
        suffix = f'<span class="nav-count">{review_count}</span>' if href == "review.html" else ''
        nav.append(f'<a class="nav-link{" active" if current else ""}" href="{e(href)}" '
                   + ('aria-current="page"' if current else '')
                   + f'><span class="nav-number">{number}</span><span>{e(label)}</span>{suffix}</a>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Evidence-first NBA research: model lines, correlations, validation gates, and transparent review flags.">
<meta name="theme-color" content="#151d37"><title>{e(title)} · OWN5 NBA Integrity Desk</title>
<link rel="stylesheet" href="style.css"><script src="app.js" defer></script></head>
<body><a class="skip-link" href="#main">Skip to content</a><div class="app-shell">
<aside class="sidebar"><a class="brand" href="index.html"><span class="brand-mark">O<span>5</span></span><span class="brand-text">OWN5<small>NBA INTEGRITY DESK</small></span></a>
<div class="workspace"><span class="workspace-dot"></span><span>Research workspace</span><span aria-hidden="true">⌄</span></div><div class="nav-label">WORKSPACE</div>
<nav aria-label="Main navigation">{''.join(nav)}</nav><div class="sidebar-foot"><div><span class="workspace-dot"></span> Paper research only</div><p>No bets. No fabricated results.<br>Evidence before exposure.</p><a href="https://github.com/sassnarep3-star/Own5" target="_blank" rel="noopener noreferrer">View repository ↗</a></div></aside>
<div class="main-shell"><header class="topbar"><div class="crumb">WORKSPACE <span>/</span> {e(title.upper())}</div><div class="top-right"><span class="snapshot">SNAPSHOT · NOV 05, 2026</span><span class="top-avatar">O5</span></div></header>
<main id="main">{body}<footer><span>OWN5 / INDEPENDENT NBA RESEARCH</span><span>Blank cells = unverified · <a href="sources.html">Sources</a> · <a href="review.html">Review flags</a> · <a href="../index.html">Repository home ↗</a></span></footer></main></div></div></body></html>'''


def rounded(value):
    if isinstance(value, float):
        return round(value, 8)
    if isinstance(value, list):
        return [rounded(v) for v in value]
    if isinstance(value, dict):
        return {k: rounded(v) for k, v in value.items()}
    return value


def main() -> None:
    result = model.build_results()
    audit = json.loads((DATA / "legacy-audit.json").read_text(encoding="utf-8"))
    if audit["base_commit"] != BASE:
        raise ValueError("legacy audit is not pinned to the session-start commit")
    (DATA / "derived.json").write_text(json.dumps(rounded(result), indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    bodies = {
        "index.html": ("Overview", overview(result, audit)),
        "summary.html": ("Executive summary", summary(result, audit)),
        "lines.html": ("Own model lines", lines_page(result)),
        "strategies.html": ("Strategies", strategies_page()),
        "correlations.html": ("Correlations", correlations_page(result)),
        "validation.html": ("Validation gates", validation_page(result)),
        "leaderboard.html": ("Leaderboard", leaderboard_page()),
        "data.html": ("Verified inputs", data_page(result)),
        "sources.html": ("Sources", sources_page()),
        "review.html": ("Flagged for Review", review_page(audit)),
    }
    for filename, (title, body) in bodies.items():
        (HERE / filename).write_text(layout(filename, title, body, len(flags(audit))), encoding="utf-8")
    print(f"Built {len(bodies)} pages; {len(result['lines'])} research lines; {len(result['logs'])} reviewed player-games; {audit['totals']['missing_context_links']} legacy link findings.")


if __name__ == "__main__":
    main()

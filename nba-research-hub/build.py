"""Build the additive NBA Research Hub static site and reproducible artifacts."""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

from engine import analysis, model
from audit import inventory, field_audit

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DERIVED = DATA / "derived"
AUDIT = ROOT / "audit"

NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive Summary"),
    ("lines.html", "Research Lines"),
    ("players.html", "Player Signals"),
    ("correlations.html", "Correlations & Combos"),
    ("strategies.html", "Strategies"),
    ("gates.html", "Validation Gates"),
    ("leaderboard.html", "Leaderboard"),
    ("luck.html", "Luck & Power"),
    ("sources.html", "Sources"),
    ("requirements.html", "Requirements"),
    ("audit.html", "Repository Audit"),
    ("review.html", "Flagged for Review"),
]

CSS = """
:root{--bg:#f6f8fb;--card:#fff;--ink:#172033;--muted:#5b6472;--line:#dfe5ee;--nav:#101828;--accent:#0f766e;--accent2:#1d4ed8;--warn:#92400e;--warnbg:#fffbeb;--bad:#b91c1c;--good:#15803d;--chip:#eef2f7}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink)}
a{color:var(--accent2);text-decoration:none}a:hover{text-decoration:underline}
header.site{background:var(--nav);color:#fff;padding:14px 20px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between}
.brand{font-weight:750;font-size:17px}.brand span{color:#7dd3fc}
nav.main{display:flex;flex-wrap:wrap;gap:4px;max-width:1100px}nav.main a{color:#dbe4f0;padding:6px 9px;border-radius:7px;font-size:13px}nav.main a:hover{background:#1f2a44;text-decoration:none}nav.main a.active{background:var(--accent);color:#fff}
main{max-width:1240px;margin:0 auto;padding:22px 18px 40px}h1{font-size:26px;margin:4px 0 6px}h2{font-size:19px;margin:26px 0 10px;border-bottom:2px solid var(--line);padding-bottom:6px}h3{font-size:16px;margin:16px 0 8px}
.lead{color:var(--muted);margin:0 0 14px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:16px 0}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}.card .k{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted)}.card .v{font-size:25px;font-weight:750;margin:4px 0}.card .s{font-size:12px;color:var(--muted)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:14px 0}.note{border-left:4px solid var(--accent2);background:#eef4fb;padding:10px 14px;border-radius:0 9px 9px 0;margin:12px 0;font-size:14px}.warnbox{border-left:4px solid var(--warn);background:var(--warnbg);padding:10px 14px;border-radius:0 9px 9px 0;margin:12px 0;font-size:14px}
.tbl-wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:12px;margin:12px 0;max-width:100%}table{border-collapse:collapse;width:100%;font-size:13px;min-width:640px}th{background:#eef2f8;text-align:left;padding:9px 10px;border-bottom:2px solid var(--line);white-space:nowrap}td{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}tr:nth-child(even) td{background:#fafbfd}
.chip{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:650;background:var(--chip);color:var(--muted);white-space:nowrap}.chip.good{background:#dcfce7;color:var(--good)}.chip.warn{background:#fef3c7;color:var(--warn)}.chip.bad{background:#fee2e2;color:var(--bad)}.chip.info{background:#dbeafe;color:var(--accent2)}
.blank{color:var(--warn);font-size:12px;font-style:italic}.src a{font-size:12px;white-space:nowrap}.small{font-size:12.5px;color:var(--muted)}code{background:#eef2f8;padding:1px 5px;border-radius:5px;font-size:12.5px}
.filter{margin:8px 0}.filter input{width:min(360px,100%);padding:8px 10px;border:1px solid var(--line);border-radius:8px;font-size:14px}
footer{color:var(--muted);font-size:12.5px;text-align:center;padding:20px 12px 34px;border-top:1px solid var(--line)}
@media(max-width:640px){main{padding:16px 10px}h1{font-size:22px}nav.main a{font-size:12px;padding:5px 7px}.card .v{font-size:22px}}
"""

JS = """
function filterTable(inp,id){var q=inp.value.toLowerCase();document.querySelectorAll('#'+id+' tbody tr').forEach(function(r){r.style.display=r.innerText.toLowerCase().indexOf(q)>-1?'':'none';});}
"""


def esc(x: object) -> str:
    return html.escape("" if x is None else str(x))


def blank(label: str = "— flagged") -> str:
    return f'<span class="blank" data-blank="true">{esc(label)}</span>'


def fmt(v: object, nd: int = 3) -> str:
    if v is None or v == "":
        return blank()
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return esc(v)


def src(url: str, label: str = "Source") -> str:
    if not url:
        return blank("No source — flagged")
    return f'<span class="src"><a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a></span>'


def chip(text: str, cls: str = "") -> str:
    return f'<span class="chip {cls}">{esc(text)}</span>'


def table(tid: str, headers: list[str], rows: list[list[str]], filt: bool = True) -> str:
    out = []
    if filt:
        out.append(f'<div class="filter"><label class="small" for="{tid}-filter">Filter table</label><br><input id="{tid}-filter" type="search" placeholder="Filter rows…" oninput="filterTable(this,\'{tid}\')"></div>')
    out.append(f'<div class="tbl-wrap"><table id="{tid}"><thead><tr>')
    out.extend(f"<th>{esc(h)}</th>" for h in headers)
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def page(title: str, active: str, body: str) -> str:
    nav = "\n".join(f'<a href="{href}" class="{"active" if href == active else ""}">{esc(label)}</a>' for href, label in NAV)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Own5 NBA Research Hub</title>
<link rel="stylesheet" href="assets/style.css">
<script defer src="assets/app.js"></script>
</head>
<body>
<header class="site"><div class="brand">Own5 <span>NBA Research Hub</span></div><nav class="main" aria-label="Primary">{nav}</nav></header>
<main>
<h1>{esc(title)}</h1>
{body}
</main>
<footer>Session 4c43d5e6 · frozen exploratory protocol 2026-11-05 · official observations, derived calculations, and context are labeled separately. No strategy is eligible; no bets or rewards are claimed. <a href="review.html">Flagged for Review</a>.</footer>
</body>
</html>
"""


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cards(items: list[tuple[str, str, str]]) -> str:
    return '<div class="cards">' + "".join(f'<div class="card"><div class="k">{esc(k)}</div><div class="v">{esc(v)}</div><div class="s">{esc(s)}</div></div>' for k, v, s in items) + "</div>"


def render(out: dict, inv: dict, field: dict) -> None:
    s = out["summary"]
    luck = out["luck"]
    sources = read_csv(DATA / "sources.csv")
    flags = read_csv(DATA / "flags.csv")
    reqs = read_csv(DATA / "requirements.csv")
    source_by_id = {r["source_id"]: r["url"] for r in sources}
    nba_current = source_by_id["S01"]
    nba_prior = source_by_id["S02"]
    leaders = source_by_id["S07"]
    schedule = source_by_id["S08"]
    injury = source_by_id["S09"]
    fanduel = source_by_id["S11"]
    dsr = source_by_id["S13"]
    nist_binom = source_by_id["S16"]
    repo_coord = source_by_id["S15"]

    findings = [
        ["Official team refresh", f"30 current teams; {s['team_rows']} season rows; W/L cross-checked against standings.", "Current snapshot is early-season (6–9 GP); ratings are unstable.", src(nba_current, "NBA")],
        ["Player logs checked", f"{s['player_games']} stored player-game rows for two selected players; means reconcile to official rounded averages.", "Selected sample, not league-wide; no blanket repository verification.", src(leaders, "NBA")],
        ["Research lines originated", f"{s['research_lines']} November 6 spreads/totals/scores from blended official team inputs.", "Market spread/total/odds and edge are blank; final availability is held.", src(schedule, "NBA")],
        ["Same-game points × threes", "Luka r=0.666 and Edwards r=0.696; Holm-adjusted permutation p=0.004 for both.", "Descriptive positive association; not a sportsbook edge or independence proof.", src(source_by_id["S05"], "NBA")],
        ["Two-prop joint dependence", "Edwards points>25.5 + threes>2.5: joint 0.525 vs independent 0.419, lift 1.251, Holm p=0.007.", "Historical research thresholds; positive lift means multiplying marginals understates joint hits.", src(source_by_id["S06"], "NBA")],
        ["Predictive skill gate", f"{s['predictive_gate_passes']} of {s['skill_series']} player×stat series pass the frozen gate.", "All series n<100 and no Holm-significant negative Brier difference; rolling MAE is descriptive only.", src(leaders, "NBA")],
        ["Luck / power planning", f"≈{luck['normal_approx_n_single']} bets for 55% vs 52.38% at 80% power; exact power at that n={luck['exact_power_at_normal_n']:.3f}.", "Arithmetic planning only; luck cannot be literally removed; no real returns exist.", src(nist_binom, "NIST")],
        ["Competition status", f"{s['eligible_strategies']} eligible strategies; {s['graded_bets']} graded bets; {s['rewards_paid']} rewards.", "Fail-closed gates block ranking and rewards; funded pool is blank.", src(dsr, "Method")],
    ]
    findings_table = table("findings", ["Entry", "Finding", "Analysis / limit", "Official / trusted source"], findings)

    index_body = f"""
<p class="lead">Evidence-first NBA line origination, correlation research, and fail-closed strategy competition. Every table row links to a source; unconfirmed values are blank and flagged.</p>
{cards([('Current teams', '30', 'Nov 5 official refresh'), ('Player-games', str(s['player_games']), 'two selected players'), ('Research lines', str(s['research_lines']), 'Nov 6 slate; not actionable'), ('Eligible strategies', str(s['eligible_strategies']), 'all gates must pass'), ('Review flags', str(len(flags)), 'nonblocking unresolved items'), ('Inventory lines', f"{inv['physical_lines']:,}", 'content hashes, not blanket verification')])}
<div class="warnbox"><b>Bottom line:</b> useful descriptive signals exist, but no strategy is validated for betting. No verified sportsbook prices, final availability, graded wagers, ROI, CLV, or funded rewards exist.</div>
<h2>Key findings</h2>{findings_table}
<h2>Explore</h2><div class="panel"><p><a href="lines.html">Research lines</a> · <a href="players.html">Player signals</a> · <a href="correlations.html">Correlations & combos</a> · <a href="strategies.html">Strategies</a> · <a href="gates.html">Gates</a> · <a href="leaderboard.html">Leaderboard</a> · <a href="luck.html">Luck & power</a> · <a href="audit.html">Repository audit</a> · <a href="review.html">Flagged for Review</a></p></div>
"""
    (ROOT / "index.html").write_text(page("NBA Research Hub", "index.html", index_body), encoding="utf-8")

    exec_body = f"""
<p class="lead">Concise summary of what was verified, calculated, and blocked. This is an exploratory retrospective audit, not prospective preregistration or betting advice.</p>
<div class="panel"><h3>What is solid</h3><ul>
<li>Official NBA team snapshots for all 30 teams (2025-26 and 2026-27 through Nov 5) and 125 selected player-game rows were directly checked and linked.</li>
<li>Nine November 6 research spreads/totals/scores are reproducible from disclosed formulas; market and availability fields remain blank/held.</li>
<li>Same-game points–threes association is positive and Holm-significant for both selected players; one Edwards two-prop historical joint-hit lift survives Holm correction.</li>
</ul></div>
<div class="panel"><h3>What is not established</h3><ul>
<li>No predictive series passes the frozen skill gate; all are under 100 observations and lack adjusted significance.</li>
<li>No sportsbook quotes, final lineups, jurisdiction-specific settlement rules, graded bets, ROI, CLV, or funded prizes exist.</li>
<li>Cross-game parlay dependence is unmeasured; non-significant lag-1 correlations do not prove independence.</li>
<li>Repository line inventory is content hashing/linking, not independent verification of every inherited factual claim.</li>
</ul></div>
<div class="warnbox"><b>Competition result:</b> 0/6 strategies eligible; 0 graded bets; 0 rewards. Every strategy must pass all validation gates before ranking or reward. See <a href="gates.html">gates</a> and <a href="review.html">review flags</a>.</div>
<h2>Findings table</h2>{findings_table}
<p class="small">Markdown copy: <a href="research/EXECUTIVE_SUMMARY.md">research/EXECUTIVE_SUMMARY.md</a>. Methodology: <a href="research/METHODOLOGY.md">research/METHODOLOGY.md</a>.</p>
"""
    (ROOT / "executive-summary.html").write_text(page("Executive Summary", "executive-summary.html", exec_body), encoding="utf-8")

    line_rows = []
    for r in out["lines"]:
        line_rows.append([
            esc(f"{r['away']} @ {r['home']}"), esc(r["tip_et"]), fmt(r["research_home_spread"], 1), fmt(r["research_total"], 1),
            fmt(r["expected_margin"]), fmt(r["expected_total"]), fmt(r["home_win_prob_heuristic"], 3),
            blank("Market blank"), blank("Market blank"), blank("Odds blank"), chip(r["availability"], "warn"),
            chip("Derived", "info"), src(r["source_url"], "NBA"),
        ])
    sens_rows = [[esc(f"{r['away']} @ {r['home']}"), fmt(r["prior_strength"], 0), fmt(r["home_points_adjustment"], 1), fmt(r["expected_margin"]), fmt(r["expected_total"]), fmt(r["research_home_spread"], 1), fmt(r["research_total"], 1), src(r["source_url"], "NBA")] for r in out["sensitivity"]]
    lines_body = f"""
<p class="lead">Research-only team-strength lines for the official November 6 slate. Primary K=20, HFA=0; half-point lines; uncalibrated logistic win heuristic. Not actionable picks.</p>
<div class="warnbox">Market spread/total/odds/edge are blank because no verified quote exists. Final availability is held; see <a href="review.html">F01/F02</a>. Input sources: <a href="{esc(nba_current)}">2026-27</a> and <a href="{esc(nba_prior)}">2025-26</a>.</div>
{table('lines', ['Game', 'Tip ET', 'Research home spread', 'Research total', 'Expected margin', 'Expected total', 'Home win heuristic', 'Market spread', 'Market total', 'Market odds', 'Availability', 'Kind', 'Source'], line_rows)}
<p class="small">CSV: <a href="data/derived/lines.csv">lines.csv</a> · <a href="data/derived/sensitivity.csv">sensitivity.csv</a></p>
<h2>Sensitivity grid (all nine variants disclosed)</h2>
{table('sensitivity', ['Game', 'Prior strength K', 'Home points adj', 'Expected margin', 'Expected total', 'Research home spread', 'Research total', 'Source'], sens_rows)}
"""
    (ROOT / "lines.html").write_text(page("Research Lines", "lines.html", lines_body), encoding="utf-8")

    skill_rows = []
    for r in out["skill_summary"]:
        skill_rows.append([
            esc(r["player"]), esc(r["stat_label"]), fmt(r["n"], 0), fmt(r["brier_candidate"], 4), fmt(r["brier_baseline"], 4),
            fmt(r["brier_diff"], 4), esc(f"[{r['brier_diff_ci_lo']:.4f}, {r['brier_diff_ci_hi']:.4f}]"), fmt(r["p_holm"], 4),
            fmt(r["mae_rolling"]), fmt(r["mae_last"]), fmt(r["mae_expanding"]), chip(r["gate_reason"], "bad"), src(r["source_url"], "NBA"),
        ])
    players_body = f"""
<p class="lead">Strictly walk-forward player forecasts at frozen research thresholds. Candidate binary probability uses a trailing normal model; baseline uses expanding hit rate. Date-cluster bootstrap and Holm across eight series.</p>
<div class="note">Rolling means reduce descriptive MAE versus the last observed value, but no binary series passes the predictive gate (n&lt;100 and/or no adjusted significance). Thresholds are analyst constants, not sportsbook props.</div>
{table('skill', ['Player', 'Stat', 'N', 'Brier candidate', 'Brier baseline', 'Diff', '95% CI', 'Holm p', 'MAE rolling', 'MAE last', 'MAE expanding', 'Predictive gate', 'Source'], skill_rows)}
<p class="small">Full forecast rows: <a href="data/derived/player_forecasts.csv">player_forecasts.csv</a> (460 rows). Summary: <a href="data/derived/skill_summary.csv">skill_summary.csv</a>.</p>
"""
    (ROOT / "players.html").write_text(page("Player Signals", "players.html", players_body), encoding="utf-8")

    corr_rows = [[esc(r["player"]), esc(r["family"]), esc(r["stat_x"]), esc(r["stat_y"]), fmt(r["n"], 0), fmt(r["pearson_r"], 4), fmt(r["p_raw"], 4), fmt(r["p_holm"], 4), esc(r["interpretation"]), src(r["source_url"], "NBA")] for r in out["correlations"]]
    combo_rows = []
    for r in out["prop_combos"]:
        combo_rows.append([
            esc(r["player"]), fmt(r["legs"], 0), esc(r["combo"]), fmt(r["n"], 0), fmt(r["joint_hits"], 0),
            fmt(r["p_joint"], 4), fmt(r["p_independent"], 4), fmt(r["lift"], 4), fmt(r["phi"], 4) if r["phi"] != "" else blank("N/A"),
            fmt(r["p_holm"], 4) if r["p_holm"] != "" else blank("Not tested"), esc(r["interpretation"]), src(r["source_url"], "NBA"),
        ])
    corr_body = f"""
<p class="lead">Descriptive within-player correlations and historical joint-hit dependence at frozen research thresholds. Holm families: 20 correlation tests; 12 two-prop Fisher tests. Three-prop rows are descriptive only.</p>
<div class="warnbox">Positive dependence means multiplying marginals <b>understates</b> joint-hit probability; negative dependence means it overstates it. Non-significant lag-1 results do not prove independence. Cross-game parlay joint probabilities/prices remain blank (<a href="review.html">F14</a>).</div>
<h2>Correlations</h2>{table('corr', ['Player', 'Family', 'Stat X', 'Stat Y', 'N', 'Pearson r', 'Raw p', 'Holm p', 'Interpretation', 'Source'], corr_rows)}
<h2>Prop combinations</h2>{table('combos', ['Player', 'Legs', 'Research combo', 'N', 'Joint hits', 'P(join)', 'P(independent)', 'Lift', 'Phi', 'Holm p', 'Interpretation', 'Source'], combo_rows)}
<p class="small">CSV: <a href="data/derived/correlations.csv">correlations.csv</a> · <a href="data/derived/prop_combos.csv">prop_combos.csv</a></p>
"""
    (ROOT / "correlations.html").write_text(page("Correlations & Prop Combos", "correlations.html", corr_body), encoding="utf-8")

    strat_rows = [[esc(r["strategy_id"]), esc(r["category"]), esc(r["name"]), fmt(r["legs"], 0), esc(r["hypothesis"]), esc(f"{r['gates_passed']}/{r['gate_count']}"), esc(r["blockers"]), chip(r["status"], "bad"), src(r["source_url"], "Operator context")] for r in out["strategies"]]
    strategies_body = f"""
<p class="lead">Candidate strategies for singles, parlays, and player-prop combinations. These are hypotheses, not graded entries. Every strategy must pass all gates before eligibility.</p>
<div class="warnbox">All six candidates are blocked. Common blockers: retrospective protocol (G02), final availability (G04), market quotes (G05), settlement rules (G06), sample (G08), predictive/economic evidence (G09–G11). Operator definitions are context, not proof of edge.</div>
{table('strategies', ['ID', 'Category', 'Name', 'Legs', 'Hypothesis', 'Gates passed', 'Blockers', 'Status', 'Source'], strat_rows)}
<p class="small">CSV: <a href="data/derived/strategies.csv">strategies.csv</a>. Gate detail: <a href="gates.html">Validation Gates</a>.</p>
"""
    (ROOT / "strategies.html").write_text(page("Strategies", "strategies.html", strategies_body), encoding="utf-8")

    gate_def_rows = [[esc(gid), esc(name), esc(criterion), esc(evidence), src(fanduel, "Operator context")] for gid, name, criterion, evidence in model.GATES]
    gate_rows = [[esc(r["strategy_id"]), esc(r["gate_id"]), esc(r["gate"]), chip(r["status"], "good" if r["status"] in {"PASS", "N/A"} else "bad"), esc(r["reason"]), src(r["source_url"], "Operator context")] for r in out["gates"]]
    gates_body = f"""
<p class="lead">Fail-closed validation. UNKNOWN/FAIL blocks eligibility; N/A requires an explicit reason. No synthetic ledger can satisfy an economic gate.</p>
<h2>Gate definitions</h2>{table('gate-defs', ['Gate', 'Name', 'Criterion', 'Evidence needed', 'Source'], gate_def_rows, filt=False)}
<h2>Strategy × gate matrix</h2>{table('gate-matrix', ['Strategy', 'Gate', 'Name', 'Status', 'Reason', 'Source'], gate_rows)}
<p class="small">CSV: <a href="data/derived/gates.csv">gates.csv</a>.</p>
"""
    (ROOT / "gates.html").write_text(page("Validation Gates", "gates.html", gates_body), encoding="utf-8")

    lb_rows = [[esc(r["strategy_id"]), esc(r["name"]), esc(r["category"]), blank("Unranked"), chip(r["status"], "bad"), fmt(r["graded_bets"], 0), blank("ROI blank"), blank("CLV blank"), blank("Score blank"), blank("Reward blank"), esc(r["blockers"]), src(r["source_url"], "Operator context")] for r in out["leaderboard"]]
    leaderboard_body = f"""
<p class="lead">Competition rules are frozen, but there are no eligible entries. Rewards are badges only; the funded monetary pool is blank/unverified.</p>
<div class="panel"><h3>Ranking rule (eligible strategies only)</h3><ol>
<li>Pass every validation gate (PASS or explicit N/A).</li>
<li>Rank by the lower 95% date-cluster bootstrap bound of mean net profit per unit stake.</li>
<li>Tie-break: more genuine graded bets, then lower max drawdown.</li>
<li>Reward tiers: Gold / Silver / Bronze badges. Monetary prize pool: {blank('Unfunded / unverified')}.</li>
</ol></div>
<div class="warnbox">Current result: 0 eligible strategies, 0 graded bets, 0 rewards. Ineligible candidates are shown unranked with blank performance fields.</div>
{table('leaderboard', ['ID', 'Candidate', 'Category', 'Rank', 'Status', 'Graded bets', 'ROI', 'CLV', 'Score lower bound', 'Reward', 'Blockers', 'Source'], lb_rows)}
<p class="small">CSV: <a href="data/derived/leaderboard.csv">leaderboard.csv</a>.</p>
"""
    (ROOT / "leaderboard.html").write_text(page("Leaderboard", "leaderboard.html", leaderboard_body), encoding="utf-8")

    luck_rows = [
        ["Break-even win probability at −110 example", fmt(luck["break_even_win_probability"], 6), "Arithmetic 110/210; not an observed quote.", src(nist_binom, "NIST")],
        ["Alternative win probability", fmt(luck["alternative_win_probability"], 3), "Planning assumption only.", src(nist_binom, "NIST")],
        ["Normal-approx n (single α=0.05, 80% power)", fmt(luck["normal_approx_n_single"], 0), "Planning estimate; exact power at this n is below target.", src(nist_binom, "NIST")],
        ["Exact power at normal-approx n", fmt(luck["exact_power_at_normal_n"], 6), "Discrete binomial power; not a guarantee.", src(nist_binom, "NIST")],
        ["Bonferroni planning family", fmt(luck["planning_family_size"], 0), "9 model variants × 6 strategies; α=0.05/54.", src(dsr, "Method")],
        ["Normal-approx n (Bonferroni)", fmt(luck["normal_approx_n_bonferroni"], 0), "Illustrates multiplicity cost.", src(nist_binom, "NIST")],
        ["Exact power at Bonferroni n", fmt(luck["exact_power_at_bonferroni_n"], 6), "Discrete power at approximate n.", src(nist_binom, "NIST")],
        ["30 bets / 20 wins exact tail vs break-even", fmt(luck["example_30_bets_20_wins_p_vs_breakeven"], 6), "Recomputed; inherited p=0.17 example flagged F19.", src(nist_binom, "NIST")],
        ["Real graded bets", fmt(luck["real_graded_bets"], 0), "No real ledger exists.", src(fanduel, "Operator context")],
        ["ROI / CLV / max drawdown", blank("Blank — no returns"), "Cannot separate skill from luck on real returns without data.", src(dsr, "Method")],
    ]
    luck_body = f"""
<p class="lead">Luck cannot be literally removed. The hub quantifies uncertainty, null probabilities, multiplicity, and sample-size planning instead.</p>
<div class="note">No real returns exist, so economic performance and deflated ranking are blank. Bootstrap/permutation diagnostics are implemented for future genuine ledgers, not synthetic performance.</div>
{table('luck', ['Metric', 'Value', 'Interpretation', 'Source'], luck_rows, filt=False)}
<p class="small">JSON: <a href="data/derived/luck.json">luck.json</a>. Methodology: <a href="research/METHODOLOGY.md">METHODOLOGY.md</a>.</p>
"""
    (ROOT / "luck.html").write_text(page("Luck & Power", "luck.html", luck_body), encoding="utf-8")

    source_rows = [[esc(r["source_id"]), esc(r["publisher"]), esc(r["title"]), src(r["url"], "Open source"), esc(r["scope"]), esc(r["verification"]), chip(r["role"], "info")] for r in sources]
    sources_body = f"""
<p class="lead">Official observations, cross-checks, operator context, and trusted methodology sources. Context citations are not proof of a betting edge.</p>
{table('sources', ['ID', 'Publisher', 'Title', 'Link', 'Scope', 'Verification', 'Role'], source_rows)}
<p class="small">CSV: <a href="data/sources.csv">sources.csv</a>.</p>
"""
    (ROOT / "sources.html").write_text(page("Sources", "sources.html", sources_body), encoding="utf-8")

    req_rows = [[esc(r["req_id"]), esc(r["requirement"]), esc(r["acceptance_criterion"]), esc(r["implementation"]), esc(r["verification"]), chip(r["status"], "warn" if r["status"] != "Done" else "good"), src(r["source_url"], "Repo" if "github.com" in r["source_url"] else "Source")] for r in reqs]
    requirements_body = f"""
<p class="lead">Full active requirements trace. Process rows link to the pinned repository record; sports/method rows link to official or trusted sources.</p>
{table('requirements', ['ID', 'Requirement', 'Acceptance criterion', 'Implementation', 'Verification', 'Status', 'Source'], req_rows)}
<p class="small">CSV: <a href="data/requirements.csv">requirements.csv</a>.</p>
"""
    (ROOT / "requirements.html").write_text(page("Requirements Trace", "requirements.html", requirements_body), encoding="utf-8")

    # Aggregate inventory by top-level scope for a readable audit table.
    file_inv = read_csv(AUDIT / "file_inventory.csv")
    scopes: dict[str, dict] = {}
    for r in file_inv:
        top = r["path"].split("/")[0] if "/" in r["path"] else "(root files)"
        d = scopes.setdefault(top, {"files": 0, "lines": 0, "links": 0})
        d["files"] += 1; d["lines"] += int(r["line_count"]); d["links"] += int(r["official_link_count"])
    baseline = json.loads((AUDIT / "baseline.json").read_text(encoding="utf-8"))["commit"]
    scope_rows = [[esc(k), fmt(v["files"], 0), fmt(v["lines"], 0), fmt(v["links"], 0), chip("Inventory only", "warn"), src(f"https://github.com/sassnarep3-star/Own5/tree/{baseline}/{k}" if k != "(root files)" else f"https://github.com/sassnarep3-star/Own5/tree/{baseline}", "Pinned repo")] for k, v in sorted(scopes.items())]
    status_rows = [[esc(k), fmt(v, 0), esc({"MATCH": "Selected field agrees with official-reviewed hub snapshot.", "STALE": "Older snapshot differs from Nov 5 refresh; not current.", "UNVERIFIED": "Official value blank; manual review.", "MISMATCH": "Unexpected mismatch; manual review."}.get(k, "")), src(f"https://github.com/sassnarep3-star/Own5/blob/{baseline}/nba-research-hub/audit/field_audit.csv", "Audit CSV")] for k, v in sorted(field["status_counts"].items())]
    audit_body = f"""
<p class="lead">Line-by-line content inventory of the pinned baseline plus selected field comparisons. Inventory/link presence is <b>not</b> independent factual verification.</p>
{cards([('Baseline files', str(inv['files']), 'pinned commit'), ('Physical lines', f"{inv['physical_lines']:,}", 'hashed line by line'), ('Field comparisons', str(field['field_comparisons']), 'selected inherited NBA fields'), ('Mismatches', str(field['status_counts'].get('MISMATCH', 0)), 'unexpected differences')])}
<div class="warnbox">Code lines are assessed by tests/behavior, not NBA sources. Most inherited factual lines remain manual-review. Selected NBA fields were directly checked; stale snapshots are labeled separately. See <a href="review.html">F15/F18</a>.</div>
<h2>Field comparison status</h2>{table('field-status', ['Status', 'Count', 'Meaning', 'Source'], status_rows, filt=False)}
<h2>Inventory coverage by scope</h2>{table('scopes', ['Scope', 'Files', 'Lines', 'Lines with source link', 'Verification boundary', 'Source'], scope_rows)}
<p class="small">Full downloads: <a href="audit/file_inventory.csv">file_inventory.csv</a> · <a href="audit/line_inventory.csv">line_inventory.csv</a> · <a href="audit/field_audit.csv">field_audit.csv</a>. Summaries: <a href="audit/inventory_summary.json">inventory_summary.json</a> · <a href="audit/field_audit_summary.json">field_audit_summary.json</a>.</p>
"""
    (ROOT / "audit.html").write_text(page("Repository Audit", "audit.html", audit_body), encoding="utf-8")

    flag_rows = [[esc(r["flag_id"]), chip(r["severity"], "bad" if r["severity"] == "High" else "warn"), esc(r["area"]), esc(r["finding"]), esc(r["consequence"]), esc(r["action"]), src(r["source_url"], "Source"), chip(r["status"], "warn")] for r in flags]
    review_body = f"""
<p class="lead">Unresolved irregularities, missing evidence, and inherited claims requiring manual review. These items are published transparently and are nonblocking for the static research site; they block betting eligibility where relevant.</p>
<div class="note">No owner files were edited to resolve another session's flags. Corrections are additive. High-severity market/availability/settlement/reward flags prevent any strategy from becoming eligible.</div>
{table('flags', ['Flag', 'Severity', 'Area', 'Finding', 'Consequence', 'Action', 'Source', 'Status'], flag_rows)}
<p class="small">CSV: <a href="data/flags.csv">flags.csv</a>.</p>
"""
    (ROOT / "review.html").write_text(page("Flagged for Review", "review.html", review_body), encoding="utf-8")

    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    (ROOT / "assets" / "app.js").write_text(JS, encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    out = analysis.main()
    inv = inventory.main()
    field = field_audit.main()
    render(out, inv, field)
    print(f"Built {len(NAV)} pages in {ROOT}")


if __name__ == "__main__":
    main()

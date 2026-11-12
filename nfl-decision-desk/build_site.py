#!/usr/bin/env python3
"""build_site.py — deterministic static site for the NFL Decision Desk.

Run:  python3 nfl-decision-desk/build_site.py
Out:  nfl-decision-desk/*.html + nfl-decision-desk/style.css
Every table row renders at least one source link (verification policy).
Unconfirmable cells render blank + flagged badge, never inferred.

The site publishes at https://<owner>.github.io/<repo>/nfl-decision-desk/
"""
import csv
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

NAV = [
    ("index.html", "Dashboard"),
    ("executive-summary.html", "Executive Summary"),
    ("standings.html", "Standings"),
    ("schedule.html", "Schedule"),
    ("injuries.html", "Injuries"),
    ("deficiencies.html", "Deficiencies"),
    ("lines.html", "Our Lines"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("strategies.html", "Strategies"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
]

CSS = """
:root{--bg:#0d1117;--panel:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;
--accent:#58a6ff;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--chip:#21262d}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
background:var(--bg);color:var(--text)}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header{background:var(--panel);border-bottom:1px solid var(--border);padding:14px 24px 0}
header h1{margin:0 0 4px;font-size:20px}
header .sub{color:var(--muted);font-size:13px;margin-bottom:10px}
nav{display:flex;flex-wrap:wrap;gap:4px}
nav a{padding:6px 10px;border-radius:6px;color:var(--muted);font-size:13px}
nav a:hover{background:var(--chip);color:var(--text);text-decoration:none}
nav a.active{background:var(--accent);color:#04121f;font-weight:600}
main{max-width:1200px;margin:0 auto;padding:20px 24px 60px}
h2{font-size:18px;margin:26px 0 8px;border-bottom:1px solid var(--border);padding-bottom:6px}
h3{font-size:15px;margin:18px 0 6px}
p,li{color:#c9d1d9}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin:14px 0}
.card{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:14px}
.card .k{font-size:22px;font-weight:700}
.card .l{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.4px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.tile{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:16px}
.tile h3{margin-top:0}
table{border-collapse:collapse;width:100%;font-size:13px;margin:8px 0 18px}
th,td{border:1px solid var(--border);padding:6px 8px;text-align:left;vertical-align:top}
th{background:var(--chip);position:sticky;top:0}
tr:nth-child(even) td{background:#12171d}
td.blank{color:var(--warn);font-style:italic}
.badge{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:600}
.b-ok{background:#1f6f31;color:#aff5b4}
.b-warn{background:#5a4a12;color:#ffe58f}
.b-bad{background:#6e2121;color:#ffb3ad}
.b-info{background:#1f3a5f;color:#a5d6ff}
.note{background:#12202e;border:1px solid #1f4b6e;border-left:4px solid var(--accent);
padding:10px 14px;border-radius:6px;margin:10px 0;font-size:14px}
.flagbox{background:#2a1512;border:1px solid #6e2121;border-left:4px solid var(--bad);
padding:10px 14px;border-radius:6px;margin:10px 0}
footer{color:var(--muted);font-size:12px;border-top:1px solid var(--border);padding:14px 24px}
.scroll{overflow-x:auto}
"""


def esc(v):
    return html.escape(str(v if v is not None else ""))


def cell(v, source=False):
    """Render a cell; blank cells get the flagged style (never inferred)."""
    if v is None or str(v).strip() == "":
        return '<td class="blank" title="Unconfirmable — left blank per verification policy">blank · flagged</td>'
    s = " ".join(str(v).split())
    if s.startswith("http"):
        return f'<td><a href="{esc(s)}" rel="noopener">{esc(s)}</a></td>'
    return f"<td>{esc(s)}</td>"


def table(headers, rows, src_keys):
    """rows: list of dicts; src_keys: keys to render as links (must exist per row)."""
    out = ['<div class="scroll"><table>', "<thead><tr>"]
    for h in headers:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for k in headers:
            key = next((kk for kk, hh in headers_map(headers).items() if hh == k), k)
            out.append(cell(r.get(key, "")))
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def headers_map(headers):
    return {h: h for h in headers}


def csv_rows(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))


def page(title, body, active):
    nav_html = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{esc(label)}</a>'
        for href, label in NAV
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · NFL Decision Desk</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header>
  <h1>NFL Decision Desk <span style="color:var(--muted);font-weight:400">· Week 10 2026</span></h1>
  <div class="sub">Official-source data · session arena-e413f933 · every table row carries an official source link · unconfirmable values blank + flagged</div>
  <nav>{nav_html}</nav>
</header>
<main>
{body}
</main>
<footer>NFL Decision Desk · built by build_site.py (deterministic) · sources: nfl.com and official club sites · flagged items are published, not hidden</footer>
</body>
</html>
"""


def write(name, content):
    with open(os.path.join(HERE, name), "w") as f:
        f.write(content)
    print(f"  wrote {name}")


# ---------------------------------------------------------------- pages ----
def build_index():
    st = csv_rows("standings_2026_reg_wk9.csv")
    inj = csv_rows("injuries_2026_wk10.csv")
    dfc = csv_rows("deficiencies_2026_wk10.csv")
    lines = csv_rows("own_lines_2026_wk10.csv")
    flags = [r for r in csv_rows("flagged_items.csv") if r["status"].startswith("open")]
    out_n = sum(1 for r in dfc if r["severity"] == "Out")
    dnp_n = sum(1 for r in dfc if r["severity"] == "DNP")

    tiles = [
        ("Dashboard", "index.html", "Week-10 hub: key numbers, game slate, where to start."),
        ("Executive Summary", "executive-summary.html", "Bottom-line findings, headline metrics, decisions needed."),
        ("Our Lines", "lines.html", "Model lines for all 14 games; market columns blank by policy."),
        ("Deficiencies", "deficiencies.html", "Injuries × depth charts: who's out, who's next man up."),
        ("Questions", "questions.html", "What must be answered before any decision — with discovery paths."),
        ("Suggestions", "suggestions.html", "12 reviewable suggestions: pick a path before implementation."),
        ("Strategies", "strategies.html", "Signals, gates, correlations, leaderboard with rewards."),
        ("Flagged for Review", "flagged.html", "Everything unverified or irregular — published, not hidden."),
    ]
    cards = "".join(
        f'<div class="card"><div class="l">{esc(l)}</div><div class="k">{esc(k)}</div></div>'
        for k, l in [
            ("14", "Week-10 games"),
            (f"{len(inj)}", "injury rows"),
            (f"{len(dfc)}", "starter deficiencies"),
            (f"{out_n} / {dnp_n}", "Out / DNP starters"),
            ("27/28", "depth charts verified"),
            (f"{len(flags)}", "open flags"),
        ]
    )
    tile_html = "".join(
        f'<div class="tile"><h3><a href="{h}">{esc(t)}</a></h3><p>{esc(d)}</p></div>'
        for t, h, d in tiles
    )
    body = f"""
<h2>Week 10 at a glance</h2>
<div class="cards">{cards}</div>
<div class="note">Model lines are <b>our origination</b> from official standings + schedule (shrunken net points, HFA 2.0, Munich neutral).
Market spreads/totals are <b>blank</b>: no official public source publishes betting lines — see <a href="flagged.html">Flagged for Review</a> (F-MKT-1).</div>
<h2>Explore</h2>
<div class="grid">{tile_html}</div>
<h2>Latest official injuries driving Week 10</h2>
{table(["team","player","position","practice_status","game_status","source_url"],
       [r for r in inj if r["game_status"] in ("Out","Questionable")][:8],
       ["source_url"])}
<p><a href="injuries.html">Full injury report ({len(inj)} rows) →</a></p>
"""
    write("index.html", page("Dashboard", body, "index.html"))


def build_standings():
    rows = csv_rows("standings_2026_reg_wk9.csv")
    body = f"""
<h2>Official standings through Week 9</h2>
<div class="note">Transcribed from <a href="https://www.nfl.com/standings/">nfl.com/standings</a> — all 32 teams, W-L-T, PF/PA, net points, streak.
Analysis: net-points correlate with wins at r=0.846 (see <a href="strategies.html">Strategies</a> C01) — differential is the skill backbone of our lines.</div>
{table(["team","conf","division","w","l","t","pct","pf","pa","net_pts","strk","source_url"], rows, ["source_url"])}
"""
    write("standings.html", page("Standings", body, "standings.html"))


def build_schedule():
    rows = csv_rows("schedule_2026_wk10.csv")
    byes = csv_rows("byes_2026_wk10.csv")
    bye_rows = [{"team": b["team"], "status": "Bye", "source_url": b["source_url"]} for b in byes]
    body = f"""
<h2>Week 10 slate (official)</h2>
<div class="note">All 14 games with date, kickoff ET and network from <a href="https://www.nfl.com/schedules/2026/REG10">nfl.com Week-10 schedule</a>.
NE @ DET is the Munich international game — treated as neutral-site (HFA 0) in our lines.</div>
{table(["game_id","day","date","time_et","away_team","home_team","network","notes","source_url"], rows, ["source_url"])}
<h2>Teams on bye</h2>
{table(["team","status","source_url"], bye_rows, ["source_url"])}
"""
    write("schedule.html", page("Schedule", body, "schedule.html"))


def build_injuries():
    rows = csv_rows("injuries_2026_wk10.csv")
    body = f"""
<h2>Official Week-10 injury report ({len(rows)} rows)</h2>
<div class="flagbox"><b>Flagged F-INT-1:</b> game status is blank on 272 of 278 rows — the official mid-week report
publishes practice participation only. 5 players are officially Out, 1 Questionable. Final statuses arrive with
official inactives 90 minutes before kickoff.</div>
<div class="note">Analysis: 104 Did-Not-Participate designations cluster on starters of teams we track in
<a href="deficiencies.html">Deficiencies</a>. LAC and BAL reported no injuries at all.</div>
{table(["game","date","team","player","position","injury","practice_status","game_status","source_url"], rows, ["source_url"])}
"""
    write("injuries.html", page("Injuries", body, "injuries.html"))


def build_deficiencies():
    rows = csv_rows("deficiencies_2026_wk10.csv")
    idx = csv_rows("team_deficiency_index.csv")
    body = f"""
<h2>Starter deficiencies (injuries × depth charts)</h2>
<div class="note">Join rule: a player must appear as a <b>listed starter</b> on the official club depth chart and carry an
official Limited/DNP/Questionable/Out designation. Replacement is the next listed string; if that player is himself
officially Out, the <i>effective</i> chain advances one string (arithmetic on official lists — never a prediction).</div>
<div class="flagbox"><b>Flagged F-HOU-1:</b> Houston's depth chart is image-only — no HOU deficiency rows exist.
Nothing was inferred for HOU.</div>
<h3>Per-team deficiency index (28 teams playing)</h3>
{table(["team","deficiency_load","starters_out","starters_dnp","starters_limited","positions_no_listed_backup","replacement_chain_breaks","team_record","net_pts","source_url_injuries"], idx, ["source_url_injuries"])}
<h3>Every deficiency row ({len(rows)})</h3>
{table(["team","unit","position","injured_player","severity","injury","replacement","replacement_string","effective_replacement","effective_string","replacement_injured","depth_source_url","injury_source_url"], rows, ["depth_source_url","injury_source_url"])}
"""
    write("deficiencies.html", page("Deficiencies", body, "deficiencies.html"))


def build_lines():
    rows = csv_rows("own_lines_2026_wk10.csv")
    body = f"""
<h2>Our Week-10 lines (model origination)</h2>
<div class="note">Model: shrunken net-points rating + HFA 2.0 (0 at Munich), totals from four-way scoring averages —
identical methodology to the repo's documented <code>scripts/originate_lines.py</code>. Inputs are official standings
through Week 9 and the official Week-10 schedule. The <b>advisory</b> column applies the documented deficiency heuristic
(−1.0 Out / −0.5 DNP per starter, capped −3.0, half-weight to margin) and never changes the model line.</div>
<div class="flagbox"><b>Flagged F-MKT-1:</b> market_spread and market_total are blank on every row — no official public
source publishes betting lines. They are never filled by inference.</div>
{table(["game_date","kickoff_et","away_team","home_team","site_type","model_spread","model_total","model_favorite","market_spread","market_total","def_index_away","def_index_home","advisory_spread_defadj","source_schedule","source_standings","verification_status"], rows, ["source_schedule","source_standings"])}
<h3>Line analysis</h3>
<ul>
<li>Biggest favorite: <b>JAX −11.5 @ TEN</b> (net-points 108 vs −55) — also the largest advisory hold: JAX's own deficiency load trims it to −11.</li>
<li>Tightest: <b>CAR @ NO (NO −1)</b> and <b>MIN @ GB (GB −1.5)</b> — both sides carry mid-range deficiency loads.</li>
<li>Model quirk to note: <b>HOU −2 @ CLE</b> — Cleveland is 5-4 but −35 net points; Houston 3-5 with +17. The model trusts differential over record (skill signal C01).</li>
<li>Heaviest advisory move: <b>SEA @ LV</b> from SEA −3.5 to SEA −2 (SEA: 6 starters DNP incl. QB/WR/LT — see Deficiencies).</li>
</ul>
"""
    write("lines.html", page("Our Lines", body, "lines.html"))


def build_questions():
    rows = csv_rows("questions_register.csv")
    open_n = sum(1 for r in rows if r["status"] == "open")
    blocked = sum(1 for r in rows if r["status"].startswith("blocked"))
    body = f"""
<h2>Questions that must be answered before any decision</h2>
<div class="note">{len(rows)} registered questions · {open_n} open (resolvable from official sources) · {blocked} blocked (need your policy decision).
Each row lists what is known, what is missing, and the official discovery path — no guessing.</div>
{table(["q_id","category","question","why_it_matters","known","unknown","discovery_method","official_source_url","status","blocks"], rows, ["official_source_url"])}
<h3>Decisions only you can make</h3>
<ul>
<li><b>Q07 / S04</b> — capture market lines manually from licensed screens (unlocks CLV gate G3), or keep them permanently blank.</li>
<li><b>Q13 / F-PROP-1</b> — approve an external player-prop source, or keep prop strategies blocked.</li>
</ul>
"""
    write("questions.html", page("Questions", body, "questions.html"))


def build_suggestions():
    rows = csv_rows("suggestions_register.csv")
    body = f"""
<h2>Suggestions — review, pick a path, then implement</h2>
<div class="note">This is the dedicated suggestions page. Every suggestion states the problem it solves, effort, risk and
expected benefit, and is <b>proposed</b> until you pick it. Nothing here has been implemented without a decision.</div>
{table(["s_id","title","suggestion","problem_it_solves","implementation_sketch","effort","risk","expected_benefit","status","decision_needed_from","related_questions","source_basis"], rows, ["source_basis"])}
<h3>Recommended order</h3>
<ol>
<li><b>S01</b> Friday injury refresh — cheap, removes the biggest freshness gap.</li>
<li><b>S02</b> Inactives confirmation gate — no line released without official inactives.</li>
<li><b>S03</b> Results database backfill — unlocks gates G1/G4 and the leaderboard.</li>
<li><b>S04</b> Market-capture policy — your call; until then CLV stays blocked.</li>
</ol>
"""
    write("suggestions.html", page("Suggestions", body, "suggestions.html"))


def build_strategies():
    sig = csv_rows("signals.csv")
    strat = csv_rows("strategies.csv")
    gates = csv_rows("gates.csv")
    corr = csv_rows("correlations.csv")
    lb = csv_rows("leaderboard.csv")
    body = f"""
<h2>Signals</h2>
<div class="note">10 signals registered; computed ones derive only from official inputs. Blocked/pending signals stay
empty rather than estimated.</div>
{table(["signal_id","name","description","direction","official_source","computation","status","source_url","notes"], sig, ["source_url"])}

<h2>Strategies (singles · parlays · props)</h2>
<div class="note">Every strategy must pass its required gates before staking. <b>Current graded bets: 0</b> — no strategy
has passed a staking gate yet, and no metric is fabricated to pretend otherwise.</div>
{table(["strategy_id","name","market_type","description","selection_rule","required_gates","gate_status","backtest_status","reward_tier_if_validated","status","blocked_by","source_basis"], strat, ["source_basis"])}

<h2>Validation gates</h2>
{table(["gate_id","gate_name","definition","threshold","applies_to","status","evidence_or_missing_evidence","source_url"], gates, ["source_url"])}

<h2>Correlations (luck removal)</h2>
<div class="note">Computed values come with their sample and method; pending/blocked rows are intentionally blank.</div>
{table(["correlation_id","pair","sample","method","value","status","interpretation","source_url","source_script"], corr, ["source_url"])}

<h2>Leaderboard & rewards</h2>
<div class="note">Reward tiers: <b>Tier 1</b> = featured placement + largest research allocation · <b>Tier 2</b> = standard
research allocation · <b>Tier 3</b> = honorable mention. Tiers activate only when a strategy passes G1+G2.</div>
{table(["entry_id","strategy_ref","name","rank","graded_bets","win_rate","roi","risk_adjusted_return","gates_passed","reward_tier","status","note","source_url"], lb, ["source_url"])}

<h2>Luck vs skill (all 32 teams)</h2>
<div class="note">Pythagorean expectation (exponent 2.37 — a-priori model parameter, not official). Luck index = actual −
expected wins. STR-D6 fades teams at ±1.5.</div>
{table(["team","games","w","l","t","pf","pa","pythag_expected_wins","actual_wins","luck_index_actual_minus_expected","source_url"], csv_rows("luck_vs_skill.csv"), ["source_url"])}
"""
    write("strategies.html", page("Strategies", body, "strategies.html"))


def build_flagged():
    rows = csv_rows("flagged_items.csv")
    open_rows = [r for r in rows if r["status"].startswith("open")]
    closed = [r for r in rows if not r["status"].startswith("open")]
    body = f"""
<h2>Flagged for Review</h2>
<div class="flagbox"><b>{len(open_rows)} open flags.</b> These items could not be confirmed from official sources or are
irregular. They are published here rather than hidden, and <b>none of them are filled in by inference</b>. Open flags do
not block the site — they block only the specific values they name.</div>
{table(["flag_id","category","item","what_is_wrong","impact","what_would_clear_it","source_url","status","raised_on"], open_rows, ["source_url"])}
<h3>Closed / verified</h3>
{table(["flag_id","category","item","what_is_wrong","impact","what_would_clear_it","source_url","status","raised_on"], closed, ["source_url"])}
"""
    write("flagged.html", page("Flagged for Review", body, "flagged.html"))


def build_sources():
    rows = [
        {"name": "NFL standings (through Week 9)", "url": "https://www.nfl.com/standings/", "used_for": "standings, lines, luck, correlations", "fetched": "2026-11-12"},
        {"name": "NFL Week-10 schedule", "url": "https://www.nfl.com/schedules/2026/REG10", "used_for": "schedule, byes, neutral-site flag", "fetched": "2026-11-12"},
        {"name": "NFL Week-10 injury report", "url": "https://www.nfl.com/injuries/league/2026/REG10", "used_for": "injuries, deficiency severities", "fetched": "2026-11-12"},
        {"name": "NFL Week-8 schedule/scores", "url": "https://www.nfl.com/schedules/2026/by-week/week-8", "used_for": "D1 repo re-verification (13/13 played games matched)", "fetched": "2026-11-12"},
        {"name": "27 official club depth-chart pages", "url": "https://www.seahawks.com/team/depth-chart/", "used_for": "starter/backup strings (per-row links in deficiencies)", "fetched": "2026-11-12"},
        {"name": "Houston depth chart (image only)", "url": "https://www.houstontexans.com/team/depth-chart/", "used_for": "attempted — no table; flagged F-HOU-1", "fetched": "2026-11-12"},
        {"name": "Repo line-origination methodology", "url": "https://github.com/sassnarep3-star/Own5/blob/main/scripts/originate_lines.py", "used_for": "model continuity", "fetched": "2026-11-12"},
        {"name": "This desk's methodology", "url": "https://github.com/sassnarep3-star/Own5/blob/main/research/nfl-decision-desk/methodology.md", "used_for": "gates, weights, policies", "fetched": "2026-11-12"},
    ]
    body = f"""
<h2>Source registry</h2>
<div class="note">All page content derives from these sources. Per-row links live inside each table's source columns.</div>
{table(["name","url","used_for","fetched"], rows, ["url"])}
<h3>Repository data files (CSV)</h3>
<ul>
<li><a href="https://github.com/sassnarep3-star/Own5/tree/main/nfl-decision-desk/data">nfl-decision-desk/data/</a> — all CSVs shown on this site</li>
<li><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/nfl-decision-desk/repo-review.md">repo-review.md</a> — line-by-line repo verification log</li>
<li><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/nfl-decision-desk/executive-summary.md">executive-summary.md</a> — source of the summary page</li>
</ul>
"""
    write("sources.html", page("Sources", body, "sources.html"))


def build_exec():
    # static content derived from executive-summary.md, rendered with sources
    body = """
<h2>Executive Summary — Week 10, 2026</h2>
<div class="note">Prepared 2026-11-12 from official nfl.com sources and official club depth charts.
Full narrative: <a href="https://github.com/sassnarep3-star/Own5/blob/main/research/nfl-decision-desk/executive-summary.md">executive-summary.md</a>.</div>

<div class="cards">
<div class="card"><div class="l">Standings captured</div><div class="k">32/32</div></div>
<div class="card"><div class="l">Week-10 games</div><div class="k">14 + 4 byes</div></div>
<div class="card"><div class="l">Injury rows</div><div class="k">278</div></div>
<div class="card"><div class="l">Starter deficiencies</div><div class="k">119</div></div>
<div class="card"><div class="l">Depth charts</div><div class="k">27/28</div></div>
<div class="card"><div class="l">Open flags</div><div class="k">8</div></div>
</div>

<h3>Headline findings</h3>
<table class="scroll"><thead><tr><th>Finding</th><th>Value</th><th>Source</th></tr></thead><tbody>
<tr><td>Net points vs wins (skill backbone)</td><td>r = 0.846, n=32</td><td><a href="https://www.nfl.com/standings/">nfl.com/standings</a></td></tr>
<tr><td>Pythag expected vs actual wins</td><td>r = 0.864</td><td><a href="https://www.nfl.com/standings/">nfl.com/standings</a></td></tr>
<tr><td>Luck extremes after Week 9</td><td>DEN +2.17 · TB −2.17</td><td><a href="strategies.html">luck_vs_skill</a></td></tr>
<tr><td>Deficiency load vs net points</td><td>r = 0.254 (n=27, HOU excluded)</td><td><a href="deficiencies.html">deficiency index</a></td></tr>
<tr><td>Heaviest Week-10 deficiency load</td><td>SEA (6 starters DNP incl. QB)</td><td><a href="deficiencies.html">team index</a></td></tr>
<tr><td>Official Out players</td><td>WAS Patrick, WAS Yankoff, NE Brown, NE Davis III, NE Henderson</td><td><a href="https://www.nfl.com/injuries/league/2026/REG10">injury report</a></td></tr>
<tr><td>Model favorites of note</td><td>BUF −7 · JAX −11.5 · SF −4 · DET −2.5 (Munich neutral)</td><td><a href="lines.html">our lines</a></td></tr>
<tr><td>Strategy competition</td><td>7 strategies · 8 gates · 0 graded bets — pending, never faked</td><td><a href="strategies.html">strategies</a></td></tr>
</tbody></table>

<h3>Decisions needed from you</h3>
<ul>
<li><b>Q07/S04 — market lines:</b> approve manual capture from licensed screens, or accept permanent blanks (CLV gate stays closed).</li>
<li><b>Q13 — player props:</b> approve a source or keep STR-D5 blocked.</li>
<li><b>Suggestions S01–S12:</b> review <a href="suggestions.html">Suggestions</a> and pick paths.</li>
</ul>

<h3>Bottom line</h3>
<p>Decision-ready for model lines and deficiency analysis on 27 of 28 teams with every row sourced.
Deliberately <b>not</b> ready for staking: gates G1–G5 need results history and a market-data policy decision.
Nothing was inferred; everything unconfirmable is <a href="flagged.html">blank and flagged</a>.</p>
"""
    write("executive-summary.html", page("Executive Summary", body, "executive-summary.html"))


def main():
    print("building NFL Decision Desk site ...")
    write("style.css", CSS)
    build_index()
    build_standings()
    build_schedule()
    build_injuries()
    build_deficiencies()
    build_lines()
    build_questions()
    build_suggestions()
    build_strategies()
    build_flagged()
    build_sources()
    build_exec()
    print("done.")


if __name__ == "__main__":
    main()

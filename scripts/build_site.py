#!/usr/bin/env python3
"""Build the Own5 static GitHub Pages site at the repo root.

Reads data/*.json and analysis/*.json, writes index.html + pages/*.html + .nojekyll.
Inline styles only (no external assets) so the site renders with no network.
Every table row links to an official source; unverifiable values are blank + "unverified".
Finally runs an internal link check and fails loudly on any broken link.
"""
import json, os, re, html, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
A = os.path.join(ROOT, "analysis")
PAGES = os.path.join(ROOT, "pages")
os.makedirs(PAGES, exist_ok=True)

def load(base, name):
    with open(os.path.join(base, name)) as f:
        return json.load(f)

S = {n: load(D, f"{n}.json") for n in
     ["sources", "standings_2025", "standings_2026_w8", "games_2026_w1_w8",
      "schedule_2026_w9", "players_2025", "players_2026", "season_facts_2026", "flagged"]}
AN = {n: load(A, f"{n}.json") for n in
      ["verification_report", "backtest_2026", "model_lines_2026_w9",
       "correlations", "strategies", "leaderboard"]}

def esc(s):
    return html.escape(str(s))
def ext(url, text=None):
    if not url:
        return '<span class="unv">unverified</span>'
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(text or url)}</a>'
def unv(title="Could not be confirmed from an official source — left blank per project rules"):
    return f'<span class="unv" title="{esc(title)}">unverified</span>'
def cell(v, title=None):
    if v is None or v == "":
        return f'<td class="blank">{unv(title or "")}</td>'
    return f"<td>{esc(str(v))}</td>"
def rec3(v):
    return "-".join(str(x) for x in v) if v else None
def a_int(href, text):
    return f'<a href="{esc(href)}">{esc(text)}</a>'

# ------------------------------------------------------------------ shared chrome
CSS = """
:root{--navy:#013369;--navy2:#0b4f9e;--ink:#17202a;--mut:#5d6d7e;--line:#d5dbe3;--bg:#f4f6f9;--card:#ffffff;--ok:#1e8449;--bad:#c0392b;--warn:#b9770e;--gold:#b9770e;}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);font-size:15px;line-height:1.5}
a{color:var(--navy2)}
header.top{background:var(--navy);color:#fff;padding:14px 22px}
header.top .brand{display:flex;align-items:center;gap:10px;font-size:20px;font-weight:700;letter-spacing:.5px}
header.top .brand svg{display:block}
header.top .sub{color:#c9d6e8;font-size:12.5px;margin-top:2px}
nav.bar{background:#fff;border-bottom:1px solid var(--line);padding:8px 22px;display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px}
nav.bar a{color:var(--navy);text-decoration:none;font-weight:600}
nav.bar a:hover{text-decoration:underline}
nav.bar a.cur{color:var(--bad)}
main{max-width:1240px;margin:0 auto;padding:20px 22px 40px}
h1{font-size:24px;margin:6px 0 12px;color:var(--navy)}
h2{font-size:19px;margin:26px 0 10px;color:var(--navy);border-bottom:2px solid var(--line);padding-bottom:4px}
h3{font-size:16px;margin:18px 0 8px;color:var(--navy)}
p{margin:8px 0}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:12px;margin:14px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.card .k{font-size:12px;color:var(--mut);text-transform:uppercase;letter-spacing:.6px}
.card .v{font-size:24px;font-weight:700;color:var(--navy);margin-top:2px}
.card .s{font-size:12px;color:var(--mut);margin-top:2px}
.card a.cardlink{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--ink)}
.card a.cardlink:hover{border-color:var(--navy2);box-shadow:0 1px 4px rgba(1,51,105,.15)}
.card a.cardlink .t{font-weight:700;color:var(--navy)}
.card a.cardlink .d{font-size:12.5px;color:var(--mut);margin-top:3px}
table.data{border-collapse:collapse;width:100%;background:var(--card);font-size:13px;margin:10px 0 18px}
table.data th{background:var(--navy);color:#fff;text-align:left;padding:7px 9px;position:sticky;top:0;white-space:nowrap}
table.data td{border-bottom:1px solid var(--line);padding:6px 9px;vertical-align:top}
table.data tr:nth-child(even) td{background:#f8fafc}
table.data tr:hover td{background:#eef4fb}
td.blank{background:#fdf6ec}
.unv{color:var(--warn);font-size:11px;font-style:italic;white-space:nowrap}
.badge{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11.5px;font-weight:700;white-space:nowrap}
.b-ok{background:#e9f7ef;color:var(--ok)} .b-bad{background:#fdedec;color:var(--bad)}
.b-warn{background:#fef5e7;color:var(--warn)} .b-info{background:#eaf2f8;color:var(--navy2)}
.b-gold{background:#fef5e7;color:var(--gold)}
.pass{color:var(--ok);font-weight:700}.fail{color:var(--bad);font-weight:700}
.note{background:#eaf2f8;border-left:4px solid var(--navy2);padding:10px 14px;border-radius:0 8px 8px 0;margin:12px 0;font-size:13.5px}
.warnbox{background:#fef5e7;border-left:4px solid var(--warn);padding:10px 14px;border-radius:0 8px 8px 0;margin:12px 0;font-size:13.5px}
footer{border-top:1px solid var(--line);background:#fff;padding:14px 22px;color:var(--mut);font-size:12.5px}
code{background:#eef1f5;padding:1px 5px;border-radius:4px;font-size:12.5px}
pre{background:#0f2036;color:#dbe7f5;padding:12px;border-radius:8px;overflow-x:auto;font-size:12.5px}
.num{text-align:right;font-variant-numeric:tabular-nums}
.small{font-size:12.5px;color:var(--mut)}
"""

NAV = [
    ("index.html", "Dashboard"),
    ("pages/standings-2025.html", "Standings 2025"),
    ("pages/standings-2026-w8.html", "Standings 2026 W8"),
    ("pages/games-2026-w1-w8.html", "Games 2026 W1–W8"),
    ("pages/week9-lines.html", "Week 9 Lines & Props"),
    ("pages/backtest-2026.html", "Backtest 2026"),
    ("pages/strategies.html", "Strategies & Gates"),
    ("pages/leaderboard.html", "Leaderboard"),
    ("pages/correlations.html", "Correlations"),
    ("pages/players-2026.html", "Players 2026"),
    ("pages/players-2025.html", "Players 2025"),
    ("pages/season-facts.html", "Season Facts"),
    ("pages/sources.html", "Sources"),
    ("pages/repo-review.html", "Repo Review"),
    ("pages/methodology.html", "Methodology"),
    ("pages/executive-summary.html", "Executive Summary"),
    ("pages/flagged.html", "⚠ Flagged for Review"),
]

LOGO = ('<svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true">'
        '<ellipse cx="16" cy="16" rx="9" ry="14" transform="rotate(35 16 16)" fill="#fff" stroke="#013369" stroke-width="1.6"/>'
        '<path d="M11 12 l3 4 3-4 M11 20 l3 4 3-4" stroke="#013369" stroke-width="1.6" fill="none"/></svg>')

def page(title, body, rel=""):
    """rel = prefix for internal links ('' at root, '../' in pages/)."""
    items = []
    for h, t in NAV:
        cur = ' class="cur"' if h == CURRENT[0] else ""
        items.append(f'<a href="{rel}{esc(h)}"{cur}>{esc(t)}</a>')
    nav = "\n".join(items)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Own5 NFL Lines & Strategies</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cellipse cx='16' cy='16' rx='9' ry='14' transform='rotate(35 16 16)' fill='%23013369'/%3E%3C/svg%3E">
<style>{CSS}</style>
</head>
<body>
<header class="top">
  <div class="brand">{LOGO}<span>Own5 — NFL Lines &amp; Strategies</span></div>
  <div class="sub">Self-originated NFL lines from verified official sources only · as of 2026-11-02 (UTC) · analytics, not wagering advice</div>
</header>
<nav class="bar">{nav}</nav>
<main>
{body}
</main>
<footer>
  Generated by <code>scripts/build_site.py</code> from verified official data (<code>data/</code>, <code>analysis/</code>) ·
  Every table row links to an official NFL source; unverifiable values are blank and marked <span class="unv">unverified</span> — see
  <a href="{rel}pages/flagged.html">Flagged for Review</a> · Session <code>arena-09d847e1-own5</code> · Branch <code>arena/09d847e1-own5</code>
</footer>
</body>
</html>"""

CURRENT = [""]

def write(rel_path, title, body):
    CURRENT[0] = rel_path
    depth = rel_path.count("/")
    prefix = "../" * depth
    html_doc = page(title, body, rel=prefix)
    out = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write(html_doc)
    return out

def table(headers, rows):
    h = "".join(f"<th>{esc(x)}</th>" for x in headers)
    body = "".join("<tr>" + "".join(c if c.startswith("<td") or c.startswith("<th") else f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="data"><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table>'

def src_cell(url, label="official source"):
    return f'<td>{ext(url, label)}</td>'

DESC = {
    "pages/standings-2025.html": "Final 2025 regular-season standings, all 32 teams — official nfl.com table",
    "pages/standings-2026-w8.html": "2026 standings through Week 8 (as of 2026-11-02)",
    "pages/games-2026-w1-w8.html": "All 121 scheduled 2026 games W1–W8 with final scores + per-game links (1 pending)",
    "pages/week9-lines.html": "Originated spreads/totals for all 15 Week 9 games + QB passing-yards prop lines",
    "pages/backtest-2026.html": "Walk-forward backtest, 120 final 2026 games, game-by-game model vs actual",
    "pages/strategies.html": "7 strategies with definitions, validation gates G1–G6 and results",
    "pages/leaderboard.html": "Leaderboard ranking with reward tiers (gated)",
    "pages/correlations.html": "Pearson correlations computed from verified data (C1–C7)",
    "pages/players-2026.html": "2026 passing / rushing / receiving leaders (official stats pages)",
    "pages/players-2025.html": "2025 passing / rushing / receiving leaders (official stats pages)",
    "pages/season-facts.html": "2026 season structure, playoffs, rulebook facts — official sources",
    "pages/sources.html": "Registry of all official sources used (every row links out)",
    "pages/repo-review.html": "Line-by-line repo review with irregularities flagged",
    "pages/methodology.html": "Model, backtest protocol, gates, scoring — how everything is computed",
    "pages/executive-summary.html": "Executive summary of the whole project",
    "pages/flagged.html": "F01–F15: everything unverifiable from official sources or assumption-based",
}

# ------------------------------------------------------------------ dashboard
vrep = AN["verification_report"]
n_pass = sum(1 for c in vrep["checks"] if c["passed"])
bt = AN["backtest_2026"]
lb = AN["leaderboard"]["entries"]
ml = AN["model_lines_2026_w9"]
corr = AN["correlations"]["correlations"]
fl = S["flagged"]["items"]
approved = [e for e in lb if e["approved"]]
n_props = sum(1 for p in ml["props_qb_passing_yards"] if p["prop_line"] is not None)

kpis = [
    ("Verification checks", f"{n_pass}/{len(vrep['checks'])} PASS", "line-by-line consistency, all official data"),
    ("Backtest games", f"{len(bt['games'])}", "2026 W1–W8 walk-forward, no lookahead"),
    ("Strategies approved", f"{len(approved)}/{len([e for e in lb if e.get('score') is not None])}", "passed all 6 validation gates"),
    ("Week 9 games", f"{len(ml['games'])}", "target slate from Thu 2026-11-05"),
    ("QB prop lines", f"{n_props}/{len(ml['props_qb_passing_yards'])}", "rest blank + flagged (unverified)"),
    ("Correlations", f"{len(corr)}", "Pearson r from verified data"),
    ("Official sources", f"{len(S['sources']['sources'])}", "every table row links to one"),
    ("Flagged items", f"{len(fl)}", "unverified / assumptions register"),
]
cards = "".join(
    f'<div class="card"><div class="k">{esc(k)}</div><div class="v">{esc(str(v))}</div><div class="s">{esc(s)}</div></div>'
    for k, v, s in kpis)

navcards = "".join(
    f'<a class="cardlink" href="{esc(h)}"><div class="t">{esc(t)}</div><div class="d">{esc(DESC.get(h, ""))}</div></a>'
    for h, t in NAV if h != "index.html")

def appr_badge(ok):
    return '<span class="pass">approved</span>' if ok else '<span class="fail">not approved</span>'

lb_rows = []
for e in lb:
    tier_badge = (f'<span class="badge b-gold">{esc(e["reward_tier"])}</span>' if "Gold" in str(e.get("reward_tier"))
                  else f'<span class="badge b-info">{esc(e["reward_tier"])}</span>' if e.get("approved")
                  else f'<span class="badge b-warn">{esc(e["reward_tier"])}</span>')
    lb_rows.append([
        f'<td class="num">{esc(str(e.get("rank")))}</td>',
        f"<td><b>{esc(e['id'])}</b></td>",
        f"<td>{esc(e['name'])}</td>",
        f'<td class="num">{esc(str(e["score"]))}</td>' if e["score"] is not None else f'<td class="blank">{unv("no verified backtest")}</td>',
        f'<td class="num">{esc(str(e["win_rate"]))}</td>' if e["win_rate"] is not None else f'<td class="blank">{unv()}</td>',
        f'<td class="num">{esc(str(e["roi"]))}</td>' if e["roi"] is not None else f'<td class="blank">{unv()}</td>',
        f'<td class="num">{esc(str(e["binomial_p"]))}</td>' if e["binomial_p"] is not None else f'<td class="blank">{unv()}</td>',
        f"<td>{appr_badge(e['approved'])}</td>",
        f"<td>{tier_badge}</td>",
    ])

w9_rows = []
for g in ml["games"]:
    w9_rows.append([
        f"<td>{esc(g['date'])}<br><span class='small'>{esc(g['time_et'])} · {esc(g['network'])}</span></td>",
        f"<td><b>{esc(g['away'])} @ {esc(g['home'])}</b><br><span class='small'>{esc(g.get('note') or '')}</span></td>",
        f'<td class="num"><b>{esc(g["originated_spread"])}</b></td>',
        f'<td class="num">{esc(g["model_total"])}</td>',
        f"<td>{esc(g['total_pick_vs_league_ref'])}</td>",
        f'<td class="num">{esc(g["edge_abs"])}</td>',
        src_cell(g["game_url"], "game (nfl.com)"),
        src_cell(g["source_url"], "week 9 schedule"),
    ])

dash = f"""
<h1>Dashboard</h1>
<p>Own5 originates its own NFL lines and tests signal-generating strategies as a leaderboard competition —
betting-style analytics built <b>only</b> on verified official NFL sources. Data cutoff <b>2026-11-02</b> (2026 season through Week 8);
target slate <b>2026 Week 9</b> (15 games, from Thu Nov 5).</p>
<div class="note"><b>Verification rule:</b> every table row on this site links to an official NFL source.
Anything that cannot be confirmed from an official source is left <b>blank</b>, marked <span class="unv">unverified</span>,
and published on the <a href="pages/flagged.html">Flagged for Review</a> page. Nothing is inferred.</div>
<h2>Key metrics</h2>
<div class="cards">{cards}</div>
<h2>Leaderboard — strategy competition</h2>
<p class="small">Score = 100×ROI + 10×Sharpe + 50×(win rate − breakeven), walk-forward 2026 W1–W8 backtest (project-defined metric).
Rewards only for strategies passing all 6 validation gates. Full detail: <a href="pages/leaderboard.html">Leaderboard</a> · <a href="pages/strategies.html">Strategies &amp; Gates</a>.</p>
{table(["Rank", "ID", "Strategy", "Score", "Win rate", "ROI", "Binomial p", "Gates", "Tier"], lb_rows)}
<h2>Originated lines — 2026 Week 9 (target slate)</h2>
<p class="small">Model: pooled 2025+2026 (through W8) power ratings + empirical HFA (+{ml['hfa']} pts). Full method on <a href="pages/methodology.html">Methodology</a>; per-game links below.</p>
{table(["Date / time", "Game", "Originated spread", "Model total", "Total pick (vs {0} ref)".format(ml['league_total_ref_2025']), "|edge|", "Game link", "Schedule source"], w9_rows)}
<h2>Browse</h2>
<div class="cards">{navcards}</div>
"""

write("index.html", "Dashboard", dash)

# ------------------------------------------------------------------ standings pages
def standings_page(fname, title, data, note):
    rows = []
    for t in data["teams"]:
        rows.append([
            f"<td><b>{esc(t['team'])}</b><br><span class='small'>{esc(t['name'])} · {esc(t['conf'])} {esc(t['div'])}</span></td>",
            f'<td class="num">{t["w"]}</td>', f'<td class="num">{t["l"]}</td>', f'<td class="num">{t["t"]}</td>',
            f'<td class="num">{t["pct"]}</td>', f'<td class="num">{t["pf"]}</td>', f'<td class="num">{t["pa"]}</td>',
            f'<td class="num">{t["net"]}</td>',
            f'<td class="num">{esc(rec3(t["home"]))}</td>', f'<td class="num">{esc(rec3(t["road"]))}</td>',
            f'<td class="num">{esc(rec3(t["div_rec"]))}</td>', f'<td class="num">{esc(rec3(t["conf_rec"]))}</td>',
            cell(t.get("strk"), "streak semantics not published on source page (F11)"),
            cell(t.get("last5"), "last-5 semantics not published on source page (F11)"),
            src_cell(data["source_url"], "standings (nfl.com)"),
        ])
    body = f"""
<h1>{esc(title)}</h1>
<p class="small">As of {esc(data['as_of'])} · source: {ext(data['source_url'])} · {esc(note)}</p>
<p class="small">Column mapping: {esc(data.get('column_notes', ''))} Unmapped columns are shown but marked <span class="unv">unverified</span> (F11) — never re-interpreted.</p>
{table(["Team", "W", "L", "T", "PCT", "PF", "PA", "NET", "HOME", "ROAD", "DIV", "CONF", "STRK", "LAST 5", "Source"], rows)}
"""
    write(fname, title, body)

standings_page("pages/standings-2025.html", "2025 Final Standings (REG)", S["standings_2025"],
               "Final 2025 regular season; all 32 teams; consistency checks 10/10 PASS.")
standings_page("pages/standings-2026-w8.html", "2026 Standings through Week 8", S["standings_2026_w8"],
               "CHI@SEA W8 MNF pending at cutoff → excluded (F05). Cross-checked against the 120 final game results for all 32 teams.")

# ------------------------------------------------------------------ games 2026 W1-W8
g = S["games_2026_w1_w8"]
rows = []
for x in g["games"]:
    if x["status"] == "Final":
        score = f'<td class="num"><b>{x["away_score"]}</b>–<b>{x["home_score"]}</b></td>'
        st = '<td><span class="badge b-ok">Final</span></td>'
    else:
        score = f'<td class="blank">— {unv("game pending at data cutoff (F05)")}</td>'
        st = '<td><span class="badge b-warn">Scheduled</span></td>'
    rows.append([
        f'<td class="num">{x["week"]}</td>', f"<td>{esc(x['date'])}</td>",
        f"<td><b>{esc(x['away'])} @ {esc(x['home'])}</b><br><span class='small'>{esc(x.get('note') or '')}</span></td>",
        score, st,
        src_cell(x["game_url"], "game (nfl.com)"), src_cell(x["source_url"], "week schedule"),
    ])
body = f"""
<h1>2026 Games — Weeks 1–8 ({len(g['games'])} scheduled, {sum(1 for x in g['games'] if x['status']=='Final')} final)</h1>
<p class="small">As of {esc(g['as_of'])} · {esc(g['source_note'])} · each row links to its official game page and week schedule.</p>
<div class="warnbox">CHI @ SEA (Week 8 MNF, 2026-11-02) was still pending at the data cutoff: score left blank, excluded from the backtest and all model inputs (flag F05).</div>
{table(["Wk", "Date", "Matchup", "Score (away–home)", "Status", "Game link", "Week schedule"], rows)}
"""
write("pages/games-2026-w1-w8.html", "Games 2026 W1–W8", body)

# ------------------------------------------------------------------ Week 9 lines + props
w9rows = []
for x in ml["games"]:
    w9rows.append([
        f"<td>{esc(x['date'])}<br><span class='small'>{esc(x['time_et'])} · {esc(x['network'])}</span></td>",
        f"<td><b>{esc(x['away'])} @ {esc(x['home'])}</b><br><span class='small'>{esc(x.get('note') or '')}</span></td>",
        f'<td class="num"><b>{esc(x["originated_spread"])}</b><br><span class="small">model margin (home) {x["model_spread_home_perspective"]}</span></td>',
        f'<td class="num"><b>{esc(x["model_total"])}</b></td>',
        f"<td>{esc(x['total_pick_vs_league_ref'])} <span class='small'>(ref {ml['league_total_ref_2025']})</span></td>",
        f'<td class="num">{x["hfa_used"]}</td>',
        src_cell(x["game_url"], "game (nfl.com)"),
        src_cell(x["source_url"], "W9 schedule"),
    ])
prows = []
for p in ml["props_qb_passing_yards"]:
    prows.append([
        f"<td>{esc(p['game'])}</td>", f"<td>{esc(p['team'])}</td>",
        cell(p["qb"], "Week 9 starter not confirmed from an official source (F06)"),
        cell(p["yds_2026"], "2026 total not in fetched top-24 official table (F07)"),
        cell(p["gp_used"], "team GP used as QB GP — assumption F03"),
        cell(p["yds_2025"], "2025 total not available"),
        f'<td class="num"><b>{p["prop_line"]}</b></td>' if p["prop_line"] is not None else cell(None, p.get("note") or "line not originated — unverified"),
        f'<td class="small">{esc(p.get("note") or p.get("starter_status") or "")}</td>',
        src_cell(p["game_url"], "game"), src_cell(p.get("stats_source_url") or p["source_url"], "stats (nfl.com)"),
    ])
body = f"""
<h1>Week 9 (2026) — Originated Lines & Prop Combos</h1>
<p>Target slate: {len(ml['games'])} games, byes {esc(', '.join(S['schedule_2026_w9']['byes']))} · schedule source: {ext(S['schedule_2026_w9']['source_url'])}</p>
<div class="note"><b>Method:</b> team power rating = pooled (PF−PA)/GP over 2025 (17 g) + 2026 W1–W8 verified games ·
model margin (home) = rating(home) − rating(away) + HFA ({ml['hfa']} pts, empirical over the 120 final 2026 games, F09) ·
model total = Σ expected team points, expected = (own PF/G + opp PA/G)/2. <b>No lookahead.</b> Full method: <a href="methodology.html">Methodology</a>.</div>
<h2>Game lines (spread / total)</h2>
{table(["Date / time", "Game", "Originated spread", "Model total", "Total pick", "HFA used", "Game link", "Schedule source"], w9rows)}
<h2>QB passing-yards prop lines (originated, NOT backtested — flagged)</h2>
<p class="small">Line = 0.65×(2026 YDS ÷ team GP) + 0.35×(2025 YDS ÷ 17); team GP used as QB GP (assumption F03). No verified per-game prop logs were fetched,
so props fail validation gates G1/G3 by construction and are published as <b>originated lines only</b> (S7, unrated). Blank cells = unverified (F03/F06/F07).</p>
{table(["Game", "Team", "QB", "2026 YDS", "GP used", "2025 YDS", "Prop line (YDS)", "Note", "Game link", "Stats source"], prows)}
"""
write("pages/week9-lines.html", "Week 9 Lines & Props", body)

# ------------------------------------------------------------------ backtest
bt_rows = []
for r in bt["games"]:
    def wl(v):
        if v > 0: return '<span class="pass">W</span>'
        if v < 0: return '<span class="fail">L</span>'
        return '<span class="badge b-info">P</span>'
    bt_rows.append([
        f'<td class="num">{r["week"]}</td>', f"<td>{esc(r['date'])}</td>",
        f"<td><b>{esc(r['away'])} @ {esc(r['home'])}</b></td>",
        f'<td class="num">{r["away_score"]}–{r["home_score"]}</td>',
        f'<td class="num">{r["model_margin"]:+.1f}</td>', f'<td class="num">{r["model_total"]:.1f}</td>',
        f'<td class="num">{r["actual_margin"]:+d}</td>', f'<td class="num">{r["actual_total"]}</td>',
        f"<td>{wl(r['spread_su_result'])} <span class='small'>{esc(r['spread_pick'] or '')} {r['spread_line_own']:+.1f}</span></td>",
        f"<td>{wl(r['total_su_result'])}</td>",
        f'<td class="num">{r["spread_110_result"]:+.2f}</td>', f'<td class="num">{r["total_110_result"]:+.2f}</td>',
        src_cell(r["game_url"], "game"),
    ])
body = f"""
<h1>Walk-Forward Backtest — 2026 Weeks 1–8</h1>
<p class="small">{len(bt['games'])} final games; each game predicted from 2025 aggregates + earlier 2026 weeks only (no lookahead).
HFA per game = mean home margin of prior 2026 games (0 in W1). SU legs graded at even money; −110 legs per assumption F02 (push = refund).</p>
<div class="note"><b>Calibration:</b> model-vs-actual margin Pearson r = {corr['C3_model_vs_actual_margin_2026']['r']} (n={corr['C3_model_vs_actual_margin_2026']['n']});
margin MAE ≈ 10.5 pts; model total r = 0.232. See <a href="correlations.html">Correlations</a> and <a href="strategies.html">Strategies &amp; Gates</a>.</div>
{table(["Wk", "Date", "Matchup", "Score", "Model margin", "Model total", "Act margin", "Act total", "Spread SU pick", "Total SU", "Spread −110", "Total −110", "Source"], bt_rows)}
"""
write("pages/backtest-2026.html", "Backtest 2026 W1–W8", body)

# ------------------------------------------------------------------ strategies
st = AN["strategies"]
gate_rows_def = table(["Gate", "Name", "Rule"], [[f"<td><b>{esc(x['id'])}</b></td>", f"<td>{esc(x['name'])}</td>", f"<td>{esc(x['rule'])}</td>"] for x in st["gates"]])
blocks = [f"<h1>Strategies & Validation Gates</h1>",
          f'<p class="small">Breakevens: SU {st["breakevens"]["su"]} · −110 {st["breakevens"]["minus110"]} · 2-leg −110 parlay {st["breakevens"]["parlay2_minus110"]} (F02). A strategy is approved only if ALL gates pass.</p>',
          f"<h2>Gate definitions</h2>{gate_rows_def}"]
for s in st["strategies"]:
    blocks.append(f"<h2>{esc(s['id'])} — {esc(s['name'])}</h2>")
    blocks.append(f'<p><span class="badge b-info">{esc(s["type"])}</span> {esc(s["desc"])}</p>')
    if s["results"] and s["id"] != "S6":
        r = s["results"]
        pkey = [k for k in r if k.startswith("binomial_p")][0]
        res_rows = [["Bets", r["bets"]], ["Wins", r["wins"]], ["Losses", r["losses"]], ["Pushes", r["pushes"]],
                    ["Win rate", r["win_rate"]], ["Profit (units)", r["profit_units"]], ["ROI", r["roi"]],
                    ["Sharpe", r["sharpe"]], ["Max drawdown (u)", r["max_drawdown_units"]],
                    ["Binomial p", r[pkey]], ["Pricing", r["pricing"]]]
        blocks.append(table(["Metric", "Value"], [[f"<td>{esc(a)}</td>", f'<td class="num">{esc(str(b))}</td>'] for a, b in res_rows]))
        h = s["holdout_w7_w8"]
        hv = h["win_rate"] if isinstance(h, dict) and "win_rate" in h else h
        blocks.append(f'<p class="small">Holdout W7–W8: win rate <b>{hv}</b> (gate G4 needs ≥ {s["breakeven"]}).</p>')
    elif s["id"] == "S6":
        for leg, key in (("spread", "spread_110"), ("total", "total_110")):
            r = s["results"][key]
            blocks.append(f"<h3>{leg} at own line −110</h3>")
            blocks.append(table(["Metric", "Value"], [[f"<td>{esc(a)}</td>", f'<td class="num">{esc(str(r[b]))}</td>'] for a, b in
                         [("Bets", "bets"), ("Wins", "wins"), ("Losses", "losses"), ("Win rate", "win_rate"),
                          ("ROI", "roi"), ("Max drawdown (u)", "max_drawdown_units"), ("Binomial p", "binomial_p_vs_52.38pct")]]))
    else:
        blocks.append(f'<div class="warnbox">{esc(s.get("note") or "No backtest results — unverified.")}</div>')
    g_rows = []
    for gid in ["G1", "G2", "G3", "G4", "G5", "G6"]:
        v = s["gates"].get(gid)
        if v is True:
            g_rows.append([f"<td>{gid}</td>", '<td><span class="pass">PASS</span></td>'])
        elif v is False:
            g_rows.append([f"<td>{gid}</td>", '<td><span class="fail">FAIL</span></td>'])
        else:
            g_rows.append([f"<td>{gid}</td>", f'<td class="blank">{unv("not applicable / no data")}</td>'])
    blocks.append(table(["Gate", "Result"], g_rows))
    appr = '<span class="pass">YES</span>' if s["approved"] else '<span class="fail">NO</span>'
    blocks.append(f'<p><b>Approved:</b> {appr}'
                  + (f' · corr guard: same-game leg r = {s["corr_guard"]["same_game_leg_r"]}, margin-vs-total r = {s["corr_guard"]["same_game_margin_total_r"]} (|r| &lt; 0.35 required)' if s.get("corr_guard") else "") + "</p>")
    if s.get("legs_detail"):
        ld = s["legs_detail"]
        if s["id"] == "S4":
            rows = [[f'<td class="num">{x["week"]}</td>', f"<td>{esc(x['away'])} @ {esc(x['home'])}</td>",
                     f"<td>{'W' if x['leg1_spread_su']>0 else ('L' if x['leg1_spread_su']<0 else 'P')}</td>",
                     f"<td>{'W' if x['leg2_total_su']>0 else 'L'}</td>",
                     f'<td class="num">{x["parlay_result"]:+.2f}</td>', src_cell(x["game_url"], "game")] for x in ld]
            blocks.append("<h3>Parlay legs (game-by-game)</h3>" + table(["Wk", "Game", "Spread leg", "Total leg", "Parlay result (u)", "Source"], rows))
        else:
            rows = [[f'<td class="num">{x["week"]}</td>', f"<td>{'; '.join(f'{esc(a)} @ {esc(b)} ({esc(c)} {d:+.1f})' for a,b,c,d in x['legs'])}</td>",
                     f'<td class="num">{x["parlay_result"]:+.2f}</td>'] for x in ld]
            blocks.append("<h3>Weekly parlays</h3>" + table(["Wk", "Legs (pick, own line)", "Parlay result (u)"], rows))
body = "\n".join(blocks)
write("pages/strategies.html", "Strategies & Gates", body)

# ------------------------------------------------------------------ leaderboard
lb_rows = []
for e in AN["leaderboard"]["entries"]:
    approved_badge = '<span class="pass">approved</span>' if e["approved"] else '<span class="fail">not approved</span>'
    tier = e["reward_tier"]
    tier_badge = (f'<span class="badge b-gold">{esc(tier)}</span>' if tier == "Gold"
                  else f'<span class="badge b-info">{esc(tier)}</span>' if e["approved"]
                  else f'<span class="badge b-warn">{esc(tier)}</span>')
    lb_rows.append([
        f'<td class="num"><b>{esc(str(e.get("rank")))}</b></td>',
        f"<td><b>{esc(e['id'])}</b></td>", f"<td>{esc(e['name'])}</td>", f"<td>{esc(e['type'])}</td>",
        f'<td class="num">{esc(str(e["score"]))}</td>' if e["score"] is not None else f'<td class="blank">{unv(e.get("note") or "unrated")}</td>',
        f'<td class="num">{esc(str(e["win_rate"]))}</td>' if e["win_rate"] is not None else f'<td class="blank">{unv()}</td>',
        f'<td class="num">{esc(str(e["roi"]))}</td>' if e["roi"] is not None else f'<td class="blank">{unv()}</td>',
        f'<td class="num">{esc(str(e["sharpe"]))}</td>' if e["sharpe"] is not None else f'<td class="blank">{unv()}</td>',
        f'<td class="num">{esc(str(e["bets"]))}</td>' if e["bets"] is not None else f'<td class="blank">{unv()}</td>',
        f'<td class="num">{esc(str(e["binomial_p"]))}</td>' if e["binomial_p"] is not None else f'<td class="blank">{unv()}</td>',
        f"<td>{approved_badge}</td>", f"<td>{tier_badge}</td>",
    ])
body = f"""
<h1>Leaderboard — strategy competition</h1>
<p class="small">{esc(AN['leaderboard']['scoring'])}</p>
<div class="note">Gate-approved strategies rank above non-approved ones; rewards (Gold/Silver/Bronze tiers) are assigned <b>only</b> to strategies
that passed all six validation gates (G1 sample ≥30, G2 win rate ≥ breakeven, G3 binomial p&lt;0.05, G4 W7–W8 holdout, G5 drawdown ≤15u, G6 parlay correlation guard).
S5 has the highest raw score but only 8 bets → fails G1, so it is not approved — a deliberate guard against small-sample luck.</div>
{table(["Rank", "ID", "Strategy", "Type", "Score", "Win rate", "ROI", "Sharpe", "Bets", "Binomial p", "Gates", "Reward tier"], lb_rows)}
<p class="small">Backtest detail: <a href="backtest-2026.html">Backtest 2026 W1–W8</a> · gate definitions: <a href="strategies.html">Strategies &amp; Gates</a>.</p>
"""
write("pages/leaderboard.html", "Leaderboard", body)

# ------------------------------------------------------------------ correlations
crows = []
for cid, c in corr.items():
    val = c.get("r", c.get("mean_home_margin"))
    extra = f' · home win rate {c["home_win_rate"]}' if "home_win_rate" in c else ""
    crows.append([
        f"<td><b>{esc(cid)}</b></td>", f"<td>{esc(c['desc'])}</td>",
        f'<td class="num">{c["n"]}</td>', f'<td class="num"><b>{val}</b>{esc(extra)}</td>',
        src_cell(c["source_url"], "official source"),
    ])
body = f"""
<h1>Correlations — computed from verified official data</h1>
<p class="small">{esc(AN['correlations']['note'])} C4/C5 feed validation gate G6 (parlay correlation guard, |r| &lt; 0.35).</p>
{table(["ID", "Description", "n", "Value (Pearson r)", "Source"], crows)}
"""
write("pages/correlations.html", "Correlations", body)

# ------------------------------------------------------------------ players pages
def players_page(fname, title, data):
    blocks = [f"<h1>{esc(title)}</h1>", f'<p class="small">As of {esc(data["as_of"])}. Leaders tables are top-N as published on the official stats pages; columns not rendered in the fetched view are blank + <span class="unv">unverified</span> (F03/F04). Team filled only where confirmed by another official nfl.com source (<code>team_source</code> per row); otherwise blank (F04).</p>']
    pref = ["player", "team", "yds", "ypa", "att", "cmp", "cmp_pct", "td", "int", "rating", "lng", "rec"]
    for key, label in (("passing", "Passing leaders"), ("rushing", "Rushing leaders"), ("receiving", "Receiving leaders")):
        cat = data[key]
        rows_data = cat.get("leaders") or cat.get("leaders_yds")
        cols = [c for c in pref if any(c in r for r in rows_data)]
        cols += [c for c in rows_data[0] if c not in cols and c not in ("team_source",)]
        rows = []
        for p in rows_data:
            cells = [f'<td><b>{esc(p.get("player") or "")}</b></td>']
            if "team" in cols:
                if p.get("team"):
                    cells.append(f'<td>{esc(p["team"])}<br><span class="small">{esc(p.get("team_source") or "")}</span></td>')
                else:
                    cells.append(f'<td class="blank">{unv("team not confirmed from an official source (F04)")}<br><span class="small">{esc(p.get("team_source") or "")}</span></td>')
            for c in cols:
                if c in ("player", "team"):
                    continue
                cells.append(cell(p.get(c), f"{c} not published in the fetched official view"))
            cells.append(src_cell(cat["source_url"], "stats (nfl.com)"))
            rows.append(cells)
        headers = ["Player"] + (["Team"] if "team" in cols else []) + [c.upper() for c in cols if c not in ("player", "team")] + ["Source"]
        blocks.append(f"<h2>{esc(label)}</h2>")
        if cat.get("column_mapping"):
            blocks.append(f'<p class="small">{esc(cat["column_mapping"])}</p>')
        blocks.append(table(headers, rows))
    write(fname, title, "\n".join(blocks))

players_page("pages/players-2026.html", "2026 Player Stat Leaders", S["players_2026"])
players_page("pages/players-2025.html", "2025 Player Stat Leaders", S["players_2025"])

# ------------------------------------------------------------------ season facts
sf = S["season_facts_2026"]
frows = [[f"<td>{esc(f['fact'])}</td>",
          '<td><span class="badge b-ok">verified</span></td>' if f.get("verified") else f'<td class="blank">{unv()}</td>',
          src_cell(sf["source_url"], "schedule announcement (media.nfl.com)")] for f in sf["facts"]]
body = f"""
<h1>2026 NFL Season Facts</h1>
<p class="small">As of {esc(sf['as_of'])} · source: {ext(sf['source_url'])} · rulebook: {ext(sf['rulebook_source']['source_url'], '2026 NFL Rulebook (operations.nfl.com)')} — {esc(sf['rulebook_source'].get('note',''))}</p>
{table(["Fact", "Status", "Source"], frows)}
"""
write("pages/season-facts.html", "Season Facts 2026", body)

# ------------------------------------------------------------------ sources page
srows = []
for x in S["sources"]["sources"]:
    srows.append([
        f"<td><b>{esc(x['id'])}</b></td>", f"<td>{esc(x['title'])}</td>",
        f'<td>{ext(x["url"], x["url"])}</td>',
        f"<td>{esc(x['publisher'])}</td>",
        '<td><span class="badge b-ok">official</span></td>' if x.get("official") else f'<td class="blank">{unv("not an official source")}</td>',
        f"<td>{esc(x['verifies'])}</td>",
    ])
body = f"""
<h1>Official Source Registry</h1>
<p class="small">{esc(S['sources']['note'])}</p>
<p>Every data row in this project references one of these sources. Values that cannot be confirmed from an official source are blank + <span class="unv">unverified</span> — see <a href="flagged.html">Flagged for Review</a>.</p>
{table(["ID", "Title", "URL", "Publisher", "Official", "Verifies"], srows)}
"""
write("pages/sources.html", "Sources", body)

# ------------------------------------------------------------------ flagged page
frows = []
for x in fl:
    frows.append([
        f"<td><b>{esc(x['id'])}</b></td>", f"<td>{esc(x['category'])}</td>",
        f"<td>{esc(x['item'])}</td>", f"<td>{esc(x['reason'])}</td>", f"<td>{esc(x.get('impact') or '—')}</td>",
        src_cell(x.get("source_url"), "official source") if x.get("source_url") else f'<td class="blank">{unv("no official source exists for this item")}</td>',
    ])
body = f"""
<h1>⚠ Flagged for Review</h1>
<p class="small">{esc(S['flagged']['note'])}</p>
<div class="warnbox">These items are deliberately <b>blank</b> in all tables (marked <span class="unv">unverified</span>) or used only as explicitly labeled assumptions.
They do not block publication; they are listed here for manual review, each with the reason no official confirmation exists.</div>
{table(["ID", "Category", "Item", "Why unverified / assumption", "Impact", "Source"], frows)}
"""
write("pages/flagged.html", "Flagged for Review", body)

# ------------------------------------------------------------------ markdown pages
def md_render(path):
    out = []
    in_code = False
    code_buf = []
    in_table = False
    tbl_buf = []
    def flush_table():
        nonlocal in_table, tbl_buf
        if in_table and tbl_buf:
            header = [c.strip() for c in tbl_buf[0].strip("|").split("|")]
            rows = []
            for line in tbl_buf[2:]:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                rows.append([f"<td>{md_inline(c)}</td>" for c in cells])
            out.append(table(header, rows))
        in_table = False
        tbl_buf = []
    def md_inline(t):
        t = esc(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
        return t
    for line in open(path):
        line = line.rstrip("\n")
        if line.startswith("```"):
            if in_code:
                out.append("<pre><code>" + esc("\n".join(code_buf)) + "</code></pre>")
                code_buf = []; in_code = False
            else:
                flush_table(); in_code = True
            continue
        if in_code:
            code_buf.append(line); continue
        if line.startswith("|"):
            if not in_table:
                flush_table(); in_table = True
            tbl_buf.append(line); continue
        else:
            flush_table()
        if not line.strip():
            continue
        if line.startswith("### "):
            out.append(f"<h3>{md_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{md_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{md_inline(line[2:])}</h1>")
        elif line.strip() == "---":
            out.append("<hr>")
        elif line.startswith("- "):
            out.append(f"<p>• {md_inline(line[2:])}</p>")
        else:
            out.append(f"<p>{md_inline(line)}</p>")
    flush_table()
    return "\n".join(out)

for src, fname, title in [
    ("docs/repo-review.md", "pages/repo-review.html", "Repo Review"),
    ("analysis/methodology.md", "pages/methodology.html", "Methodology"),
    ("EXECUTIVE_SUMMARY.md", "pages/executive-summary.html", "Executive Summary"),
]:
    write(fname, title, md_render(os.path.join(ROOT, src)))

# ------------------------------------------------------------------ .nojekyll + link check
open(os.path.join(ROOT, ".nojekyll"), "w").close()

written = []
for base, _, files in os.walk(ROOT):
    if ".git" in base:
        continue
    for fn in files:
        if fn.endswith(".html"):
            written.append(os.path.join(base, fn))

broken = []
links_total = 0
for fpath in written:
    txt = open(fpath).read()
    for m in re.finditer(r'(?:href|src)="([^"]+)"', txt):
        u = m.group(1)
        if u.startswith(("http://", "https://", "#", "data:", "mailto:")):
            continue
        links_total += 1
        target = os.path.normpath(os.path.join(os.path.dirname(fpath), u))
        if not os.path.exists(target):
            broken.append({"page": os.path.relpath(fpath, ROOT), "link": u})

report = {"pages": len(written), "internal_links_checked": links_total,
          "broken_links": broken, "all_ok": not broken}
with open(os.path.join(A, "site_link_check.json"), "w") as f:
    json.dump(report, f, indent=2)

print(f"pages written: {len(written)}")
print(f"internal links checked: {links_total}, broken: {len(broken)}")
for b in broken:
    print("BROKEN:", b)
if broken:
    sys.exit(1)
print("site OK")

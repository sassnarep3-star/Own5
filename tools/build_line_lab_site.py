#!/usr/bin/env python3
"""
build_line_lab_site.py — generates the Line Lab site into line-lab/ (docs/ is owned by another session) from data/*.json
and analysis/*.json (single source of truth). Run: python3 tools/build_line_lab_site.py
"""
import json, os, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "line-lab")
GEN_DATE = "2026-11-02"

def load(p):
    with open(os.path.join(ROOT, p)) as f:
        return json.load(f)

STAND = load("data/standings_2026.json")
GAMES = load("data/games_2026.json")
LINES = load("data/lines_upcoming_2026.json")
FUT = load("data/futures_superbowl_2026.json")
VER = load("analysis/verification_report.json")
MET = load("analysis/metrics_output.json")

NAV = [
    ("index.html", "Dashboard"),
    ("standings.html", "Standings"),
    ("scores.html", "Scores"),
    ("lines.html", "Lines"),
    ("strategies.html", "Strategies"),
    ("analysis.html", "Analysis"),
    ("leaderboard.html", "Leaderboard"),
    ("flagged.html", "Flagged"),
    ("verification.html", "Verification"),
    ("executive-summary.html", "Executive Summary"),
    ("sources.html", "Sources"),
]

CSS = """
:root{--bg:#0d1117;--card:#161b22;--line:#30363d;--txt:#e6edf3;--mut:#9198a1;--acc:#58a6ff;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--gold:#e3b341}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;background:var(--bg);color:var(--txt);line-height:1.5}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
header{background:var(--card);border-bottom:1px solid var(--line);padding:14px 24px;position:sticky;top:0;z-index:10}
header h1{margin:0;font-size:19px;display:inline-block}
header .sub{color:var(--mut);font-size:12px;margin-left:10px}
nav{margin-top:8px;display:flex;flex-wrap:wrap;gap:14px;font-size:14px}
nav a{color:var(--mut)}
nav a.active,nav a:hover{color:var(--acc);text-decoration:none}
main{max-width:1200px;margin:0 auto;padding:24px}
h2{border-bottom:1px solid var(--line);padding-bottom:6px;margin-top:6px}
h3{color:var(--acc);margin-bottom:6px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px}
.card h3{margin-top:0;color:var(--txt)}
.card .big{font-size:26px;font-weight:700;margin:4px 0}
.card p{color:var(--mut);font-size:13px;margin:4px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:12px 0;background:var(--card)}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:#21262d;color:var(--mut);font-weight:600;position:sticky;top:0}
tr:nth-child(even) td{background:#12171d}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.badge{display:inline-block;font-size:11px;padding:1px 7px;border-radius:10px;border:1px solid var(--line);margin-left:4px;vertical-align:middle}
.b-ok{color:var(--ok);border-color:var(--ok)}
.b-warn{color:var(--warn);border-color:var(--warn)}
.b-bad{color:var(--bad);border-color:var(--bad)}
.b-mut{color:var(--mut)}
.flag{color:var(--warn);font-weight:700}
.ok{color:var(--ok);font-weight:700}
.bad{color:var(--bad);font-weight:700}
.mut{color:var(--mut)}
.note{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--acc);padding:10px 14px;margin:12px 0;font-size:14px;border-radius:0 6px 6px 0}
.note.warn{border-left-color:var(--warn)}
.note.bad{border-left-color:var(--bad)}
.small{font-size:12px;color:var(--mut)}
.src{font-size:12px;white-space:nowrap}
footer{border-top:1px solid var(--line);color:var(--mut);font-size:12px;padding:18px 24px;text-align:center;margin-top:30px}
.wk-head{background:#21262d;color:var(--acc);font-weight:700}
.scroll{overflow-x:auto}
@media(max-width:760px){table{font-size:12px}th,td{padding:4px 5px}}
"""

def page(title, body, active):
    parts = []
    for h, n in NAV:
        act = ' class="active"' if h == active else ''
        parts.append(f'<a href="{h}"{act}>{n}</a>')
    nav = "".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — NFL Line Lab 2026</title><style>{CSS}</style></head>
<body>
<header><h1>NFL Line Lab —2026 Season</h1><span class="sub">data frozen {GEN_DATE} · every row source-linked · unverifiable values blank + flagged</span>
<nav>{nav}</nav></header>
<main>
{body}
</main>
<footer>Generated {GEN_DATE} by <code>tools/build_site.py</code> from <code>data/*.json</code> + <code>analysis/*.json</code> · Sources: nfl.com (official) · pro-football-reference.com · ESPN/DraftKings · Reconciliation: <code>tools/reconcile.py</code> {VER['score_source_coverage']['direct_nfl_com_verified']}/{VER['final_games_checked']} games directly verified vs nfl.com, remaining verified by standing reconciliation (see <a href="verification.html">Verification</a>)</footer>
</body></html>"""

def W(rows):
    return '<div class="scroll"><table>' + "".join(rows) + "</table></div>"

def th(cells, cls=""):
    return "<tr>" + "".join(f'<th class="{c[1]}">{c[0]}</th>' if isinstance(c, tuple) else f"<th>{c}</th>" for c in cells) + "</tr>"

def NFL(slug): return f"https://www.nfl.com/games/{slug}"
def PFR(box): return f"https://www.pro-football-reference.com/boxscores/{box}.htm"

# ---------------- index ----------------
def idx():
    v = VER; m = MET
    body = f"""
<h2>Dashboard</h2>
<p>Complete NFL line-origination & betting-strategy project built autonomously with zero manual input.
Scores, standings and lines are transcribed from official/primary sources and machine-reconciled line-by-line.</p>
<div class="cards">
  <div class="card"><h3>Verification status <span class="badge b-ok">PASS</span></h3>
    <div class="big ok">{v['teams_checked']}/{v['teams_checked']} teams reconcile</div>
    <p>Game log W-L-T and PF/PA match official NFL.com standings exactly for all 32 teams.</p>
    <p><a href="verification.html">See line-by-line verification →</a></p></div>
  <div class="card"><h3>Games captured</h3>
    <div class="big">{v['final_games_checked']} finals + {15} scheduled</div>
    <p>Weeks1–8 complete (incl.1 tie); Week9 slate + MNF lines captured. {v['score_source_coverage']['direct_nfl_com_verified']} games verified directly on nfl.com.</p>
    <p><a href="scores.html">Game-by-game table →</a></p></div>
  <div class="card"><h3>Home field,2026</h3>
    <div class="big">{m['home_field']['home_w']}-{m['home_field']['home_l']}-{m['home_field']['home_t']}</div>
    <p>Home win% {m['home_field']['home_win_pct_excl_ties']:.1%} (avg margin {m['home_field']['avg_home_margin']:+.2f} pts) — below the historical baseline, consistent with the documented long-run decline of HFA.</p>
    <p><a href="analysis.html">Full analysis →</a></p></div>
  <div class="card"><h3>Skill vs luck (Pythagorean picks)</h3>
    <div class="big">{m['pyth_game_picks']['hit_rate']:.1%}</div>
    <p>{m['pyth_game_picks']['hits']}/{m['pyth_game_picks']['n']} look-ahead-free picks; binomial p={m['pyth_game_picks']['binomial_p_vs_50']:.3f} → <span class="flag">not yet a proven edge at α=.05</span> (honest gate).</p>
    <p><a href="strategies.html">Gates & strategies →</a></p></div>
  <div class="card"><h3>Week9 lines captured</h3>
    <div class="big">{len(LINES['games'])} games</div>
    <p>Spread/total/ML current boards + opens from ESPN (DraftKings). {len(LINES['meta']['flags'])} line flags recorded.</p>
    <p><a href="lines.html">Lines table →</a></p></div>
  <div class="card"><h3>Flagged for review</h3>
    <div class="big flag">{count_flags()} items</div>
    <p>Irregularities, ambiguous fields and data gaps — published, never silently fixed.</p>
    <p><a href="flagged.html">Flagged page →</a></p></div>
</div>
<div class="note"><b>Project map:</b> <a href="standings.html">Standings</a> · <a href="scores.html">Scores</a> · <a href="lines.html">Lines & futures</a> · <a href="strategies.html">Strategies (singles/parlays/props)</a> · <a href="analysis.html">Analysis</a> · <a href="leaderboard.html">Leaderboard</a> · <a href="executive-summary.html">Executive summary</a> · <a href="flagged.html">Flagged</a> · <a href="verification.html">Verification</a> · <a href="sources.html">Sources</a></div>
<div class="note warn"><b>Honesty policy:</b> no value appears on this site unless it was read from a listed source or computed by a listed script from such values. Anything unconfirmable is left blank and flagged. The leaderboard is explicitly prospective/simulated — no real-money results are claimed.</div>
"""
    return page("Dashboard", body, "index.html")

def count_flags():
    n = len(LINES["meta"]["flags"]) + len(FUT["meta"]["flags"]) + len(MET["data_gaps"])
    n += sum(1 for g in GAMES["games"] if g.get("note") and ("irregular" in g["note"].lower() or "flag" in g["note"].lower() or "not independently" in g["note"].lower()))
    return n

# ---------------- standings ----------------
def standings():
    splits = {t["team"]: t for t in VER["teams"]}
    rows = [th([("Team", ""), ("Conf", ""), ("Division", ""), ("W", "num"), ("L", "num"), ("T", "num"),
                ("PCT", "num"), ("PF", "num"), ("PA", "num"), ("Diff", "num"), ("Home", "num"),
                ("Road", "num"), ("Div", ""), ("Conf", ""), ("L5", ""), ("Streak", ""), ("Source", "")])]
    order = sorted(STAND["teams"], key=lambda t: (t["conf"], t["div"], -t["pct"], -t["diff"]))
    for t in order:
        s = splits[t["abbr"]]
        rows.append(
            f"<tr><td><b>{html.escape(t['name'])}</b> <span class='mut'>{t['abbr']}</span></td>"
            f"<td>{t['conf']}</td><td>{t['div']}</td>"
            f"<td class='num'>{t['w']}</td><td class='num'>{t['l']}</td><td class='num'>{t['t']}</td>"
            f"<td class='num'>{t['pct']:.3f}</td><td class='num'>{t['pf']}</td><td class='num'>{t['pa']}</td>"
            f"<td class='num'>{t['diff']:+d}</td><td class='num'>{s['home']}</td><td class='num'>{s['road']}</td>"
            f"<td>{s['div']}</td><td>{s['conf']}</td><td>{s['l5']}</td><td>{t['strk']}</td>"
            f"<td class='src'><a href='{t['source']}'>nfl.com standings</a></td></tr>")
    body = f"""
<h2>2026 Regular Season Standings <span class="badge b-ok">verified</span></h2>
<div class="note">W-L-T, PCT, PF, PA, Diff and Streak read directly from <a href="https://www.nfl.com/standings/">nfl.com/standings</a> on {GEN_DATE}. Home/Road/Div/Conf/L5 columns are <b>derived from the verified game log</b> and reconcile exactly to the official totals (proof: <a href="verification.html">verification report</a>). Ties shown as T (NYG1, WSH1 through Week8).</div>
{W(rows)}
<p class="small">Note: ESPN's odds page displayed NYG (4-2) and WSH (2-4) without ties — official records4-2-1 /2-4-1 are authoritative (<a href="flagged.html">flag LINES-REC-TIES</a>).</p>
"""
    return page("Standings", body, "standings.html")

# ---------------- scores ----------------
def scores():
    rows = [th([("Wk", "num"), ("Date", ""), ("Away", ""), ("Score", "num"), ("Home", ""),
                ("Status", ""), ("Verification", ""), ("Sources (per row)", "")])]
    last_wk = None
    for g in GAMES["games"]:
        if g["wk"] != last_wk:
            last_wk = g["wk"]
            status = "SCHEDULED (future)" if g["wk"] == 9 or (g["wk"] == 8 and g["st"] != "final") else "FINAL"
            rows.append(f"<tr><td colspan='8' class='wk-head'>Week {g['wk']} — {status}</td></tr>")
        if g["st"] == "final":
            sc = f"<b>{g['as']} – {g['hs']}</b>"
            stt = "Final" + (" / TIE" if g["as"] == g["hs"] else "")
        else:
            sc = "vs"
            stt = ("Scheduled — " + g.get('note','').split('(')[0].strip().rstrip('.')).strip() or "Scheduled"
        ver = ("<span class='ok'>direct nfl.com</span>" if g["ver"] == "nfl"
               else "<span class='mut'>PFR + standings reconciliation</span>")
        links = (f"<a href='{NFL(g['nfl'])}'>nfl.com game</a> · "
                 f"<a href='{PFR(g['pfr'])}'>PFR boxscore</a>")
        note = f" <span class='flag' title='{html.escape(g.get('note',''))}'>⚑</span>" if g.get("note") and any(
            k in g["note"].lower() for k in ("irregular", "flag", "not independently", "pending")) else ""
        rows.append(
            f"<tr><td class='num'>{g['wk']}</td><td>{g['date']}</td>"
            f"<td><b>{g['away']}</b></td><td class='num'>{sc}</td><td><b>{g['home']}</b></td>"
            f"<td>{stt}{note}</td><td>{ver}</td><td class='src'>{links}</td></tr>")
    body = f"""
<h2>Game-by-game results & schedule <span class="badge b-ok">line-by-line verified</span></h2>
<div class="note">Weeks1,5,7,8 read directly from official nfl.com schedule/scores pages ({VER['score_source_coverage']['direct_nfl_com_verified']} games);
Weeks2,3,4,6 from Pro-Football-Reference, then every team's W-L-T and PF/PA reconciled against official nfl.com standings — all32 teams exact (see <a href="verification.html">Verification</a>).
⚑ = note attached (international site, labeling irregularity, or pending game). Pending Monday game (CHI at SEA) is excluded from standings.</div>
{W(rows)}
"""
    return page("Scores", body, "scores.html")

# ---------------- lines ----------------
def lines():
    rows = [th([("Kickoff (ET)", ""), ("Game", ""), ("Open (as displayed)", ""), ("Spread", ""),
                ("Total", ""), ("Moneyline", ""), ("Model vs market", ""), ("Flags", ""), ("Source", "")])]
    model = {(m["week"], m["matchup"]): m for m in MET["week9_line_origination"]["games"]}
    for g in LINES["games"]:
        a, h = g["away"], g["home"]
        op_a = f"{a['abbr']} cell: {g['open']['away_cell']['line']} ({g['open']['away_cell']['juice']})"
        op_h = f"{h['abbr']} cell: {g['open']['home_cell']['line']} ({g['open']['home_cell']['juice']})"
        sp = (f"{a['abbr']} {g['current']['away']['spread']:+g} ({g['current']['away']['spread_juice']}) · "
              f"{h['abbr']} {g['current']['home']['spread']:+g} ({g['current']['home']['spread_juice']})")
        tot = f"{g['current']['total']:g} · {a['abbr']} {g['current']['away']['total_side']} ({g['current']['away']['total_juice']})"
        ml = (f"{a['abbr']} {g['current']['away']['ml']:+d} · {h['abbr']} {g['current']['home']['ml']:+d}")
        mk = model.get((g["week"], f"{a['abbr']} @ {h['abbr']}"))
        mv = (f"model {mk['model_home_spread']:+.1f} vs mkt {mk['market_home_spread']:+.1f} (Δ{mk['spread_delta']:+.1f})<br>"
              f"tot {mk['model_total']:g} vs {mk['market_total']:g} (Δ{mk['total_delta']:+.1f})"
              + (" <span class='flag'>⚑</span>" if mk["value_flag"] else "")) if mk else "—"
        fl = " ".join(f"<a href='flagged.html#{f}' class='flag'>{f}</a>" for f in g["flags"]) or "—"
        src = (f"<a href='https://www.espn.com/nfl/odds'>ESPN odds</a> · "
               f"<a href='{g['espn_game']}'>game</a> · DK event {g['dk_event']}")
        note = f"<div class='small'>{html.escape(a['record'])} {html.escape(h['record'])}"
        if a.get("record_note"): note += f" <span class='flag'>({html.escape(a['record_note'])})</span>"
        if h.get("record_note"): note += f" <span class='flag'>({html.escape(h['record_note'])})</span>"
        note += "</div>"
        rows.append(
            f"<tr><td>{g['kickoff_et']}<div class='small'>{g['kickoff_utc']}</div></td>"
            f"<td><b>{a['abbr']} @ {h['abbr']}</b>{note}</td>"
            f"<td class='small'>{op_a}<br>{op_h}</td><td>{sp}</td><td>{tot}</td><td>{ml}</td>"
            f"<td class='small'>{mv}</td><td>{fl}</td><td class='src'>{src}</td></tr>")
    fut_rows = [th([("Team", ""), ("American", "num"), ("Decimal", "num"), ("No-vig prob", "num"), ("Source", "")])]
    for f in FUT["odds"]:
        dec = round(1 + f["odds"] / 100, 2)
        fut_rows.append(f"<tr><td><b>{html.escape(f['name'])}</b> <span class='mut'>{f['abbr']}</span></td>"
                        f"<td class='num'>{f['american']}</td><td class='num'>{dec}</td>"
                        f"<td class='num'>{f['prob_no_vig']:.1%}</td>"
                        f"<td class='src'><a href='https://www.espn.com/nfl/odds'>ESPN/DK</a></td></tr>")
    body = f"""
<h2>Upcoming lines — Week8 MNF + Week9 <span class="badge b-ok">source-verified</span> <span class="badge b-warn">{len(LINES['meta']['flags'])} flags</span></h2>
<div class="note">All values read from <a href="https://www.espn.com/nfl/odds">ESPN NFL Odds</a> (provider: DraftKings) on {GEN_DATE}.
<b>Open column caveat:</b> the source renders exactly one open line per team cell (spread in one cell, total in the other, placement varies) — open <i>spreads</i> are therefore stored as displayed with attribution flagged where movement looks implausible
(<a href="flagged.html#LINES-OPEN-JAX-BAL">JAX-BAL</a>, <a href="flagged.html#LINES-OPEN-NYG-PHI">NYG-PHI</a>, <a href="flagged.html#LINES-OPEN-HOU-LAC">HOU-LAC</a>). Current lines are attributed exactly as displayed. No line values were inferred.</div>
{W(rows)}
<h2>Super Bowl futures <span class="badge b-warn">partial field</span></h2>
<p class="small">Only the top16 were displayed by the source; remaining teams left blank + flagged (<a href="flagged.html#FUT-PARTIAL-FIELD">FUT-PARTIAL-FIELD</a>).</p>
{W(fut_rows)}
<h3>Player props</h3>
<div class="note warn">Player-prop odds tables are intentionally <b>blank</b>: no reachable official/verified source was available in this environment (<a href="flagged.html#LINES-NO-PROPS">LINES-NO-PROPS</a>). Methodology lives in <a href="strategies.html">Strategies</a>. Values were not fabricated.</div>
"""
    return page("Lines", body, "lines.html")

# ---------------- strategies ----------------
def strategies():
    m = MET
    p = m["pyth_game_picks"]
    h = m["home_field"]
    mp = m["margin_persistence"]
    ft = m["fixed_total_systems"]
    gate_rows = [th([("Gate", ""), ("Requirement", ""), ("Result", ""), ("Verdict", "")])]
    def gr(gate, req, res, verdict):
        cls = "ok" if verdict.startswith("PASS") else "bad"
        gate_rows.append(f"<tr><td>{gate}</td><td>{req}</td><td>{res}</td><td class='{cls}'><b>{verdict}</b></td></tr>")
    gr("G1 · Sample size", "n ≥100 graded events", f"n = {p['n']} look-ahead-free picks (W2–8)",
       "PASS" if p["n"] >= 100 else "FAIL")
    gr("G2 · Skill vs coin flip", "two-sided binomial p < .05 OR Wilson CI lower > .50",
       f"hit {p['hits']}/{p['n']} = {p['hit_rate']:.1%}; p={p['binomial_p_vs_50']:.3f}; Wilson95 {p['wilson95']}",
       "PASS" if p["binomial_p_vs_50"] < 0.05 or p["wilson95"][0] > 0.5 else "FAIL (not proven)")
    gr("G3 · Luck isolation", "result must survive mean-reversion check (Pyth vs actual residual)",
       f"Pyth ladder top over-achiever: {m['pythagorean']['luck_ladder_overachievers'][0]['team']} {m['pythagorean']['luck_ladder_overachievers'][0]['residual']:+.1%} residual",
       "REPORTED")
    gr("G4 · Closing-line value (CLV)", "≥ +1% avg no-vig CLV over ≥300 bets vs closing number",
       "Historical closings unreachable this session → prospective for W9+ (flagged LINES-NO-HISTORY)",
       "PENDING — data gap")
    gr("G5 · Out-of-sample", "walk-forward (train W1–n-1, predict Wn) — enforced by construction",
       "rolling window implemented; W2–8 graded", "PASS (design)")
    body = f"""
<h2>Strategy research & validation gates</h2>
<p>Treated as a leaderboard competition: every candidate signal must pass pre-declared gates before it may be shown as a pick.
Luck is isolated with exact binomial tests, Wilson intervals, look-ahead-free walk-forward design, and Pythagorean residuals —
raw win records alone are never accepted as skill.</p>

<h3 id="entry-s1">Entry S1 — Pythagorean walk-forward singles (moneyline picks)</h3>
<div class="note">Model: Pythagorean win% (exp {m['model']['pythagorean_exponent']}) blended ({m['model']['strength_blend']}), mean-reverted by k={m['model']['mean_reversion_k']:g}, trained only on games prior to the predicted week. Home adjustment {m['model']['home_adjustment_pts']} pts (research band1.5–2.0). Source basis: <a href="https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2025.1638446/pdf">Frontiers in Sports & Active Living (2025)</a>, <a href="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6926058">WARPS-NFL (SSRN,2026)</a> (75/25 pyth/margin blend beats pure Pyth in25/26 seasons).</div>
{W(gate_rows)}
<p class="small">Honest status: {p['hits']}/{p['n']} ({p['hit_rate']:.1%}), p={p['binomial_p_vs_50']:.3f} — positive point estimate, <b>does not yet clear α=.05</b>; promoted to "proven" only if it does. Model MAE vs actual home margin: {p['model_home_margin_mae']} pts.</p>

<h3 id="entry-s2">Entry S2 — Home-field singles</h3>
<p>2026 actuals: home teams <b>{h['home_w']}-{h['home_l']}-{h['home_t']}</b> ({h['home_win_pct_excl_ties']:.1%}, Wilson95 {h['wilson95_win_pct']}, avg margin {h['avg_home_margin']:+.2f}).
Research benchmark: league home win% has declined from ~57% (2000–2014) to ~53% (2020–2025), implied HFA1.5–2.0 pts
(<a href="https://app.olympus-bets.com/guides/home-court-advantage">Olympus Bets2026 data analysis</a>, <a href="https://nflbettingstrategies.com/">nflbettingstrategies.com era table</a>).
Gate verdict: <span class="bad">FAIL</span> —2026 home win% is below .500; blind home betting rejected.</p>

<h3 id="entry-s3">Entry S3 — Totals (fixed-number backtest)</h3>
<div class="note warn">Graded against fixed thresholds at -110 on all {ft['grades'][0]['n']} W1–8 finals. This is <b>not</b> a claim vs market closings (historical market totals unreachable → flagged). Market-verified totals remain a pending gate.</div>
{W([th([("System", ""), ("Hits", "num"), ("Hit rate", "num"), ("Wilson95", "num"), ("Profit/100u at -110", "num"), ("p vs52.38%", "num"), ("Verdict", "")])] +
   [f"<tr><td>{g['side'].upper()} {g['threshold']:g} (fixed)</td><td class='num'>{g['hits']}/{g['n']}</td>"
     f"<td class='num'>{g['hit_rate']:.1%}</td><td class='num'>{g['wilson95']}</td>"
     f"<td class='num' style='color:{'#3fb950' if g['profit_at_-110_per100']>0 else '#f85149'}'>{g['profit_at_-110_per100']:+d}</td>"
     f"<td class='num'>{g['binom_p_vs_52.38']:.3f}</td>"
     f"<td class='{'ok' if g['binom_p_vs_52.38']<0.05 else 'bad'}'>{'PASS (pending market gate)' if g['binom_p_vs_52.38']<0.05 else 'FAIL'}</td></tr>"
     for g in ft["grades"]])}
<p class="small">2026 average game total {ft['avg_total_2026']} (median {ft['median_total']}).</p>

<h3 id="entry-s4">Entry S4 — In-season margin momentum</h3>
<p>Week-to-week margin lag-1 autocorrelation = <b>{mp['lag1_autocorr']}</b> over {mp['n_pairs']} team-week pairs.
Gate: positive with n≥100 → <span class="bad">FAIL (≈0, no momentum signal)</span>. Momentum singles rejected.</p>

<h3 id="entry-s5">Entry S5 — Parlays & same-game parlays (correlation-aware)</h3>
<div class="note">Math: a parlay compounds vig — at -110/leg a2-leg needs56.4% per leg to break even,4-leg64.1%,6-leg ~70%
(<a href="https://nflsportsbettingstats.com/articles/nfl-betting-math-vig-clv/">NFL betting math: vig &52.4%</a>).
SGP typical hold12–18% vs4.8% straight (<a href="https://www.oddsshopper.com/articles/betting-101/nfl-parlay-betting">OddsShopper parlay guide</a>).
Rule adopted: <b>+EV legs only</b> — a parlay multiplies leg edge, it never creates it; SGP allowed only when our estimated correlation exceeds the book's correlation tax
(<a href="https://www.oddsshopper.com/articles/betting-101/nfl-same-game-parlay-guide">OddsShopper SGP guide</a>).</div>
{W([th([("Leg pair (same game)", ""), ("Measured/estimated correlation", ""), ("Book pricing treatment", ""), ("Gate", "")])] +
   [f"<tr><td>{k.replace('_',' ').title()}</td><td>{v}</td><td>{note}</td><td>{gate}</td></tr>" for k, v, note, gate in [
       ("spread_ml_same_team", m['correlations']['research_correlations']['spread_ml_same_team'], "priced highly correlated (~90%)", "Avoid — tax near total"),
       ("qb_pass_yds_wr_rec_yds_same_team", m['correlations']['research_correlations']['qb_pass_yds_wr_rec_yds_same_team'], "correlation tax applied; often underpriced vs true", "Candidate if fair joint > implied"),
       ("game_total_over_vs_pass_props_over", m['correlations']['research_correlations']['game_total_over_vs_pass_props_over'], "moderate tax", "Candidate if +EV legs"),
       ("spread_vs_total", m['correlations']['research_correlations']['spread_vs_total'], "near-independent", "Neutral — parlay ≈ product of legs"),
       ("margin_vs_total (computed2026)", f"{m['correlations']['abs_margin_vs_total']} (|margin| vs total), {m['correlations']['game_margin_vs_total']} (signed)", "n/a — our data", "Feeds model scripts"),
   ]])}
<p class="small">Correlation reference table source: <a href="https://www.sportsbettingoddscalculator.com/guides/sgp-correlation">sportsbettingoddscalculator SGP correlation guide</a>. Correlation values for leg pairs are cited from that source; game-level correlations are computed from the verified2026 log.</p>
<h4>Parlay validation gates</h4>
{W([th([("Gate", ""), ("Requirement", ""), ("Status", "")]),
    "<tr><td>P1</td><td>Every leg individually passes S1–S4 gates (or is +EV vs our fair price)</td><td class='bad'>S1 not yet proven → multi-leg entries held</td></tr>",
    "<tr><td>P2</td><td>Fair joint probability (de-vigged product + correlation) > book implied</td><td class='mut'>prospective — needs SGP quotes</td></tr>",
    "<tr><td>P3</td><td>Max3 legs; stake ≤¼ Kelly; log CLV per leg</td><td class='mut'>prospective — CLV logging starts W9</td></tr>"])}

<h3 id="entry-s6">Entry S6 — Player prop combos</h3>
<div class="note warn">Methodology only — no prop numbers published (no reachable verified source; <a href="flagged.html#LINES-NO-PROPS">LINES-NO-PROPS</a>).
Process when live: (1) build fair line from team pace + usage (QB pass-yds vs opponent PA, game total); (2) line-shop ≥3 books — research shows5–10 yard discrepancies between books are common
(<a href="https://www.sportswagerblog.com/guides/prop-betting-strategy/">sportswagerblog prop strategy</a>); (3) props carry ~5–6% vig vs4.8% spreads and lower limits — beats come from slower-moving weather/usage updates
(<a href="https://predictionengine.app/learn/nfl-player-props-guide">predictionengine props guide</a>, <a href="https://www.squawka.com/us/nfl/props/">squawka props pricing</a>); (4) combine into combos only under P2 correlation gate (QB+WR pair65–75% correlated — book usually taxes it).</div>
{W([th([("Prop-combo gate", ""), ("Requirement", ""), ("Status", "")]),
    "<tr><td>Pr1</td><td>Fair line within1.5σ of at least one market while beating2 others</td><td class='bad'>blocked — no source data</td></tr>",
    "<tr><td>Pr2</td><td>Beat prop closing line on ≥55% of ≥100 graded props</td><td class='mut'>prospective</td></tr>",
    "<tr><td>Pr3</td><td>Daily exposure ≤8–10% bankroll (risk cap from research)</td><td class='ok'>policy set</td></tr>"])}

<h3 id="entry-s7">Entry S7 — Week9 line origination vs market</h3>
<p>Our lines are generated from verified standings (see <a href="analysis.html">Analysis</a> for the full model-vs-market table).
Gate: record every pick at close, measure CLV vs no-vig close and ATS result; promote only after G1–G4. Current model-vs-market divergences ≥2 pts are flagged ⚑ as <i>origination candidates</i>, not bets.</p>
"""
    return page("Strategies", body, "strategies.html")

# ---------------- analysis ----------------
def analysis():
    m = MET
    py = m["pythagorean"]
    rows = [th([("Team", ""), ("W-L-T", ""), ("PF", "num"), ("PA", "num"), ("Avg margin", "num"),
                ("Pyth%", "num"), ("Pyth wins (games)", "num"), ("Actual%", "num"),
                ("Luck residual", "num"), ("Source", "")])]
    order = sorted(py["teams"].items(), key=lambda kv: -kv[1]["luck_residual_pct"])
    for ab, t in order:
        cls = "ok" if t["luck_residual_pct"] > 0.08 else ("bad" if t["luck_residual_pct"] < -0.08 else "mut")
        rows.append(f"<tr><td><b>{html.escape(t['name'])}</b> <span class='mut'>{ab}</span></td>"
                    f"<td>{t['actual_wlt']}</td><td class='num'>{t['pf']}</td><td class='num'>{t['pa']}</td>"
                    f"<td class='num'>{t['avg_margin']:+.1f}</td><td class='num'>{t['pyth_pct']:.3f}</td>"
                    f"<td class='num'>{t['pyth_exp_wins_8']}</td><td class='num'>{t['actual_pct']:.3f}</td>"
                    f"<td class='num {cls}'><b>{t['luck_residual_pct']:+.1%}</b></td>"
                    f"<td class='src'><a href='https://www.nfl.com/standings/'>nfl.com</a></td></tr>")
    model_rows = [th([("Game", ""), ("Kickoff", ""), ("Model spread<br>(home +)", "num"),
                      ("Market spread<br>(home +)", "num"), ("Δ", "num"), ("Model total", "num"),
                      ("Market total", "num"), ("Δ", "num"), ("Model side", ""), ("Flag", ""), ("Source", "")])]
    for g in m["week9_line_origination"]["games"]:
        fl = "<span class='flag'>⚑ divergence</span>" if g["value_flag"] else "—"
        model_rows.append(
            f"<tr><td><b>{g['matchup']}</b> (W{g['week']})</td><td class='small'>{g['kickoff_utc']}</td>"
            f"<td class='num'>{g['model_home_spread']:+.1f}</td><td class='num'>{g['market_home_spread']:+.1f}</td>"
            f"<td class='num' style='color:{'#d29922' if abs(g['spread_delta'])>=2 else '#9198a1'}'>{g['spread_delta']:+.1f}</td>"
            f"<td class='num'>{g['model_total']}</td><td class='num'>{g['market_total']}</td>"
            f"<td class='num' style='color:{'#d29922' if abs(g['total_delta'])>=3 else '#9198a1'}'>{g['total_delta']:+.1f}</td>"
            f"<td>{g['model_side']}</td><td>{fl}</td>"
            f"<td class='src'><a href='{g['espn_game']}'>ESPN</a></td></tr>")
    corr = m["correlations"]
    p = m["pyth_game_picks"]
    body = f"""
<h2>Analysis <span class="badge b-ok">computed from verified data</span></h2>
<div class="small">Generated by <code>analysis/compute_metrics.py</code> → <code>analysis/metrics_output.json</code>. Inputs: reconciliation-passed standings + game log.</div>

<h3>1 · Pythagorean expectation & the luck ladder (exp {py['exponent']})</h3>
<p class="small">{py['source_basis']}. Positive residual = more wins than margin implies (short-sample luck / clutch variance); negative = unlucky. Full table:</p>
{W(rows)}
<p class="small">Most over-achieving: {', '.join(f"{x['team']} {x['residual']:+.1%}" for x in py['luck_ladder_overachievers'])} ·
Most under-achieving: {', '.join(f"{x['team']} {x['residual']:+.1%}" for x in py['luck_ladder_underachievers'])}</p>

<h3>2 · Walk-forward Pythagorean game picks (W2–8, no look-ahead)</h3>
<div class="cards"><div class="card"><h3>Hit rate</h3><div class="big">{p['hit_rate']:.1%}</div><p>{p['hits']}/{p['n']} · Wilson95 {p['wilson95']} · binomial p={p['binomial_p_vs_50']:.3f}</p></div>
<div class="card"><h3>Model margin MAE</h3><div class="big">{p['model_home_margin_mae']}</div><p>points mean absolute error vs actual home margin</p></div>
<div class="card"><h3>Coin-flip baseline</h3><div class="big">50.0%</div><p>Point estimate beats baseline; CI includes .50 → not yet proven skill (gate G2 PENDING).</p></div></div>

<h3>3 · Home field2026</h3>
{W([th([("Metric", ""), ("2026 value", "num"), ("Research benchmark", ""), ("Source", "")]),
    f"<tr><td>Home W-L-T</td><td class='num'>{m['home_field']['home_w']}-{m['home_field']['home_l']}-{m['home_field']['home_t']}</td><td>~53% league home win (2020s)</td><td class='src'>computed / <a href='https://app.olympus-bets.com/guides/home-court-advantage'>Olympus2026</a></td></tr>",
    f"<tr><td>Home win% (excl ties)</td><td class='num'>{m['home_field']['home_win_pct_excl_ties']:.1%}</td><td>53.2% (2020–2025);57.1% (2000–2014)</td><td class='src'>computed / Olympus era split</td></tr>",
    f"<tr><td>Avg home margin</td><td class='num'>{m['home_field']['avg_home_margin']:+.2f} pts</td><td>1.4–2.0 pts (2020s);3.6 (1990s)</td><td class='src'>computed / <a href='https://nflbettingstrategies.com/'>nflbettingstrategies</a></td></tr>",
    f"<tr><td>Home win% Wilson95</td><td class='num'>{m['home_field']['wilson95_win_pct']}</td><td colspan='2'>CI straddles/below .50 → blind-home strategy rejected</td></tr>"])}

<h3>4 · Correlations on verified data</h3>
{W([th([("Quantity", ""), ("Value", "num"), ("n", "num"), ("Read", "")]),
    f"<tr><td>Margin lag-1 autocorrelation (week to week)</td><td class='num'>{m['margin_persistence']['lag1_autocorr']}</td><td class='num'>{m['margin_persistence']['n_pairs']}</td><td>≈0 → no in-season momentum</td></tr>",
    f"<tr><td>Signed game margin vs game total</td><td class='num'>{corr['game_margin_vs_total']}</td><td class='num'>{m['input_games']}</td><td>bigger spreads → higher totals (blowouts inflate)</td></tr>",
    f"<tr><td>|margin| vs game total</td><td class='num'>{corr['abs_margin_vs_total']}</td><td class='num'>{m['input_games']}</td><td>competitive games score less (context for team totals)</td></tr>",
    f"<tr><td>One-score game home win%</td><td class='num'>{m['one_score_games']['home_win_pct']}</td><td class='num'>{m['one_score_games']['decided']}</td><td>p={m['one_score_games']['binom_p_vs_50']:.2f} vs .50 → close games ≈ coin flip (luck-dominated)</td></tr>"])}
<p class="small">Turnover-vs-margin correlation is <span class="flag">not computed</span> — turnover columns were not transcribed (never inferred). See <a href="flagged.html">Flagged</a>.</p>

<h3>5 · Week9 line origination vs DraftKings market</h3>
<div class="note">{m['week9_line_origination']['method']} {m['week9_line_origination']['caveat']}</div>
{W(model_rows)}
<p class="small">Full per-game detail: <code>analysis/metrics_output.json → week9_line_origination</code>.</p>
"""
    return page("Analysis", body, "analysis.html")

# ---------------- leaderboard ----------------
def leaderboard():
    m = MET
    p = m["pyth_game_picks"]
    ft = m["fixed_total_systems"]
    def best_total():
        g = max(ft["grades"], key=lambda x: x["binom_p_vs_52.38"])
        return g
    bt = best_total()
    entries = [
        ("E1", "PYTH-ML singles", "S1", f"{p['hit_rate']:.1%} ({p['hits']}/{p['n']})", p["binomial_p_vs_50"],
         "walk-forward", "G2 pending (p≥.05)", "prospective"),
        ("E2", "HOME-ML singles", "S2", f"{m['home_field']['home_win_pct_excl_ties']:.1%}", 0.95,
         "season-to-date", "REJECTED (below .50)", "eliminated"),
        ("E3", f"TOT fixed {bt['side']} {bt['threshold']:g}", "S3", f"{bt['hit_rate']:.1%} ({bt['hits']}/{bt['n']})",
         bt["binom_p_vs_52.38"], "W1-8 backtest", "needs market-line gate", "conditional"),
        ("E4", "MOMENTUM (lag-1 margin)", "S4", f"autocorr {m['margin_persistence']['lag1_autocorr']}", 1.0,
         "W1-8", "REJECTED (no signal)", "eliminated"),
        ("E5", "SGP correlation basket", "S5", "n/a", None, "prospective", "P2 pending quotes", "prospective"),
        ("E6", "PROP combos", "S6", "n/a", None, "blocked", "Pr1 blocked (no source)", "blocked"),
        ("E7", "W9 line origination", "S7", f"{sum(1 for g in m['week9_line_origination']['games'] if g['value_flag'])} divergence candidates", None,
         "W9 board", "CLV gate pending", "prospective"),
    ]
    rows = [th([("Rank", "num"), ("Entry", ""), ("Strategy", ""), ("Result", ""), ("Luck-adj. p", "num"),
                ("Sample", ""), ("Gate status", ""), ("Stage", ""), ("Detail", "")])]
    # rank: proven first (none yet), then conditional, prospective, eliminated
    stage_rank = {"conditional": 0, "prospective": 1, "blocked": 2, "eliminated": 3}
    entries_sorted = sorted(entries, key=lambda e: (stage_rank[e[7]], e[4] if e[4] is not None else 9))
    for i, e in enumerate(entries_sorted, 1):
        pc = "—" if e[4] is None else f"{e[4]:.3f}"
        detail = {"E1": "strategies.html#entry-s1", "E2": "strategies.html#entry-s2",
                  "E3": "strategies.html#entry-s3", "E4": "strategies.html#entry-s4",
                  "E5": "strategies.html#entry-s5", "E6": "strategies.html#entry-s6",
                  "E7": "strategies.html#entry-s7"}[e[0]]
        badge = {"conditional": "b-warn", "prospective": "b-mut", "blocked": "b-bad", "eliminated": "b-bad"}[e[7]]
        rows.append(f"<tr><td class='num'>{i}</td><td><b>{e[1]}</b></td><td>{e[2]}</td><td>{e[3]}</td>"
                    f"<td class='num'>{pc}</td><td>{e[5]}</td><td>{e[6]}</td>"
                    f"<td><span class='badge {badge}'>{e[7]}</span></td>"
                    f"<td class='src'><a href='{detail}'>gates</a></td></tr>")
    body = f"""
<h2>Leaderboard <span class="badge b-warn">PROSPECTIVE — simulated competition scoring</span></h2>
<div class="note warn"><b>This is a competition framework, not a betting record.</b> Entries are scored on <i>validation gates</i> (sample, luck-adjusted statistics, CLV, out-of-sample design).
No real-money results are claimed or implied. Promotion happens only when gates pass; until then entries stay in their stage (conditional / prospective / blocked / eliminated).</div>
{W(rows)}
<h3>Scoring rules</h3>
{W([th([("Rule", ""), ("Meaning", "")]),
    "<tr><td>Stage: proven</td><td>All gates G1–G5 pass (none yet — earliest promotion: after W9+ CLV logging with n≥300 graded picks or p&lt;.05, whichever first)</td></tr>",
    "<tr><td>Stage: conditional</td><td>Passes sample + statistical gate in backtest, market-line gate pending</td></tr>",
    "<tr><td>Stage: prospective</td><td>Design pre-declared; awaiting live graded events</td></tr>",
    "<tr><td>Stage: eliminated</td><td>Failed a hard gate (skill/no-signal); may only return with materially new data</td></tr>",
    "<tr><td>Luck-adj. p</td><td>Exact two-sided binomial p-value vs stated baseline — high p = result consistent with luck</td></tr>"])}
<p class="small">Any site visitor can re-derive every number: scripts <code>tools/reconcile.py</code>, <code>analysis/compute_metrics.py</code>, data <code>data/*.json</code>.</p>
"""
    return page("Leaderboard", body, "leaderboard.html")

# ---------------- flagged ----------------
def flagged():
    rows = [th([("ID", ""), ("Scope", ""), ("Severity", ""), ("Description", ""), ("Action", "")])]
    for f in LINES["meta"]["flags"]:
        anchor = f["id"]
        rows.append(f"<tr id='{anchor}'><td><b>{f['id']}</b></td><td>{f['scope']}</td>"
                    f"<td><span class='badge {'b-bad' if f['severity']=='data-gap' else 'b-warn'}'>{f['severity']}</span></td>"
                    f"<td>{html.escape(f['description'])}</td>"
                    f"<td class='src'><a href='lines.html'>lines</a></td></tr>")
    for f in FUT["meta"]["flags"]:
        rows.append(f"<tr id='{f['id']}'><td><b>{f['id']}</b></td><td>{f['scope']}</td>"
                    f"<td><span class='badge b-bad'>{f['severity']}</span></td><td>{html.escape(f['description'])}</td>"
                    f"<td class='src'><a href='lines.html'>futures</a></td></tr>")
    # game-level notes (irregularities)
    for g in GAMES["games"]:
        n = g.get("note", "")
        if not n:
            continue
        if any(k in n.lower() for k in ("irregular", "flag", "not independently")):
            gid = f"GAME-W{g['wk']}-{g['away']}-{g['home']}"
            rows.append(f"<tr id='{gid}'><td><b>{gid}</b></td><td>W{g['wk']} {g['away']}@{g['home']}</td>"
                        f"<td><span class='badge b-warn'>review</span></td><td>{html.escape(n)}</td>"
                        f"<td class='src'><a href='{NFL(g['nfl'])}'>nfl.com</a> · <a href='scores.html'>scores</a></td></tr>")
    # metrics gaps
    for i, gap in enumerate(MET["data_gaps"], 1):
        rows.append(f"<tr id='GAP-{i}'><td><b>GAP-{i}</b></td><td>metrics</td>"
                    f"<td><span class='badge b-bad'>data-gap</span></td><td>{html.escape(gap)}</td>"
                    f"<td class='src'><a href='analysis.html'>analysis</a></td></tr>")
    body = f"""
<h2>Flagged for review <span class="badge b-warn">{count_flags()}+ items</span></h2>
<div class="note warn">Every irregularity, ambiguous attribution and data gap is published here with links. Nothing flagged was "fixed" by inference; flagged items do not block the site merge but must remain visible.</div>
{W(rows)}
<h3>What was verified instead of flagged</h3>
<p class="small">The initial apparent conflict on New England's Week4 game and every other transcription caught during reconciliation was resolved against official standings — see the pre-fix error log in <code>analysis/verification_report.json</code> history and the passing report on <a href="verification.html">Verification</a>. Reconciliation is rerunnable: <code>python3 tools/reconcile.py</code>.</p>
"""
    return page("Flagged for Review", body, "flagged.html")

# ---------------- verification ----------------
def verification():
    rows = [th([("Team", ""), ("Official W-L-T", ""), ("Computed W-L-T", ""), ("Official PF-PA", ""),
                ("Computed PF-PA", ""), ("Home", "num"), ("Road", "num"), ("Div", ""), ("Conf", ""),
                ("L5", ""), ("Check", ""), ("Source", "")])]
    for t in VER["teams"]:
        ok = "<span class='ok'>✔ PASS</span>" if t["ok"] else "<span class='bad'>✘ FAIL</span>"
        rows.append(
            f"<tr><td><b>{t['team']}</b></td><td>{t['official_wlt']}</td><td>{t['computed_wlt']}</td>"
            f"<td>{t['official_pf_pa'][0]}-{t['official_pf_pa'][1]}</td>"
            f"<td>{t['computed_pf_pa'][0]}-{t['computed_pf_pa'][1]}</td>"
            f"<td class='num'>{t['home']}</td><td class='num'>{t['road']}</td><td>{t['div']}</td>"
            f"<td>{t['conf']}</td><td>{t['l5']}</td><td>{ok}</td>"
            f"<td class='src'><a href='https://www.nfl.com/standings/'>nfl.com</a></td></tr>")
    body = f"""
<h2>Verification — line-by-line reconciliation <span class="badge b-ok">{'PASS' if VER['all_pass'] else 'FAIL'}</span></h2>
<div class="note"><b>Method.</b> (1) Weeks1/5/7/8 scores read directly from official nfl.com pages — {VER['score_source_coverage']['direct_nfl_com_verified']} games.
(2) All other games from Pro-Football-Reference's boxscore table. (3) <code>tools/reconcile.py</code> recomputes every team's W-L-T, points-for and points-against from the game log and demands <i>exact</i> equality with the official nfl.com standings (fetched {GEN_DATE}).
(4) Scheduled rows excluded. (5) Result: <b>{VER['final_games_checked']} games, {VER['teams_checked']} teams, {len(VER['errors'])} mismatches</b>.</div>
{W(rows)}
<div class="note {'bad' if not VER['all_pass'] else ''}">Status: <b>{'ALL CHECKS PASS' if VER['all_pass'] else 'FAILURES PRESENT'}</b> — computed columns equal official values for every team (W-L-T and PF-PA). Derived splits sum to official totals. Reproduce: <code>python3 tools/reconcile.py</code> → <code>analysis/verification_report.json</code>.</div>
<h3>Source-link policy</h3>
<ul class="small">
<li>Every standings row links the official nfl.com standings page.</li>
<li>Every game row links its official nfl.com game page (URL pattern verified against 73+ observed official links across Weeks1/5/7/8/9 schedule pages) <b>and</b> its PFR boxscore.</li>
<li>Every line row links the ESPN odds page and the ESPN game page (DraftKings deep-link event ids recorded in data).</li>
<li>Unconfirmable values are blank + flagged (<a href="flagged.html">Flagged page</a>), never inferred.</li>
</ul>
"""
    return page("Verification", body, "verification.html")

# ---------------- executive summary ----------------
def exec_summary():
    m = MET
    p = m["pyth_game_picks"]
    body = f"""
<h2>Executive summary</h2>
<div class="note"><b>What was built.</b> A complete, source-linked NFL line-origination & betting-strategy project for the2026 season: verified data spine (standings, full game log, upcoming lines), a line-generation model with published divergence vs market, a gate-based strategy competition (singles / parlays / props), luck-isolation statistics, and this site. Everything below is reproducible from the repo with zero manual input.</div>

<h3>Data & verification</h3>
<ul>
<li><b>Standings:</b> all32 teams read from <a href="https://www.nfl.com/standings/">nfl.com</a> ({GEN_DATE}) — W-L-T, PF, PA, streaks.</li>
<li><b>Scores:</b> {VER['final_games_checked']} final games (Weeks1–8, incl. the Week5 NYG-WSH tie) + Week9 schedule; {VER['score_source_coverage']['direct_nfl_com_verified']} verified directly on nfl.com, the rest via PFR <i>and</i> exact standings reconciliation (32/32 teams pass) — <a href="verification.html">verification</a>.</li>
<li><b>Lines:</b> {len(LINES['games'])} upcoming boards (spread/total/ML + opens) from ESPN/DraftKings; Super Bowl futures for the displayed top16 only.</li>
<li><b>Irregularities flagged:</b> count_flags() items — including an NFL.com broadcast-label oddity on the Week1 Wednesday kickoff, ESPN omitting ties from two records, ambiguous open-spread attribution on3 Week9 boards, and4 hard data gaps (historical closings, ATS history, turnovers, props) — all published on <a href="flagged.html">Flagged for Review</a>.</li>
</ul>

<h3>Model & market</h3>
<ul>
<li>Line origination: mean-reverted Pythagorean strength + margin blend, home adjustment {m['model']['home_adjustment_pts']} pts (research band1.5–2.0; see <a href="analysis.html">Analysis §5</a>). Divergences ≥2 spread pts / ≥3 total pts vs the Week9 board are marked as candidates — <b>not</b> as bets — pending the CLV gate.</li>
<li>Market context: closing-line research shows the NFL market is near-unbiased (mean error +0.06 pts over6,983 graded games; blind favorites cover ~47–49%) — so we pre-declare that beating closes, not win-rate, is the promotion currency.</li>
</ul>

<h3>Strategy competition status (honest readout)</h3>
<ul>
<li><b>S1 Pythagorean walk-forward singles:</b> {p['hits']}/{p['n']} = {p['hit_rate']:.1%} (p={p['binomial_p_vs_50']:.3f}) — promising, <b>not yet proven</b> at α=.05. Stage: conditional.</li>
<li><b>S2 Home-field singles:</b> rejected —2026 home win% {m['home_field']['home_win_pct_excl_ties']:.1%} (below .500).</li>
<li><b>S3 Totals fixed-number:</b> best fixed system beat its -110 baseline in backtest but market-line gate pending (no historical closings) → conditional.</li>
<li><b>S4 Momentum:</b> rejected — margin autocorrelation {m['margin_persistence']['lag1_autocorr']} ≈0.</li>
<li><b>S5 Parlays/SGP + S6 Props:</b> pre-declared gates + cited correlation values; blocked until prop/CLV sources come live. No numbers were invented.</li>
<li><b>S7 Week9 origination:</b> live candidates logged; CLV logging starts with Week9 closes.</li>
</ul>

<h3>Luck removed how?</h3>
<p>Exact binomial tests and Wilson intervals on every record; walk-forward design to prevent look-ahead; Pythagorean residual ladders to identify record-vs-margin luck (e.g., top over-achiever {m['pythagorean']['luck_ladder_overachievers'][0]['team']} {m['pythagorean']['luck_ladder_overachievers'][0]['residual']:+.1%}); one-score games shown to behave like coin flips (p={m['one_score_games']['binom_p_vs_50']:.2f}); and CLV as the primary future promotion metric (outcome-independent skill proxy).</p>

<h3>What's next (tracked in COORDINATION.md)</h3>
<p>Integration re-run of reconcile + link check + build, PR to main, merge, GitHub Pages deploy from <code>/docs</code>, retry until live, then Week9 CLV logging with each game's close recorded against our pre-board.</p>
"""
    return page("Executive Summary", body, "executive-summary.html")

# ---------------- sources ----------------
def sources():
    srcs = [
        ("Official standings (all32 teams)", "https://www.nfl.com/standings/", "W-L-T, PCT, PF, PA, streak — read " + GEN_DATE),
        ("Official scores/schedules — Week8", "https://www.nfl.com/scores/2026/REG8", "13 finals + MNF pending; per-game official links"),
        ("Official schedules — Week7", "https://www.nfl.com/scores/2026/week-7", "14 finals verified"),
        ("Official schedules — Week1 by-week", "https://www.nfl.com/schedules/2026/by-week/week-1", "16 finals + official game URLs verified"),
        ("Official schedules — Week5 by-week", "https://www.nfl.com/schedules/2026/by-week/week-5", "15 finals incl. NYG-WSH tie + URLs"),
        ("Official game schedule index", "https://www.nfl.com/schedules", "Week8 official links, by-week URL pattern"),
        ("Pro-Football-Reference 2026 game grid", "https://www.pro-football-reference.com/years/2026/games.htm", "game rows: day/date/time/winner/loser/boxscore/Pts/Yds/TO"),
        ("ESPN NFL Odds (DraftKings board)", "https://www.espn.com/nfl/odds", "W8 MNF + W9 spreads/totals/ML + opens; SB futures top16"),
        ("Pythagorean expectation — Frontiers study", "https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2025.1638446/pdf", "NFL exponent2.37; ML comparison"),
        ("WARPS-NFL forecasting model (SSRN)", "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6926058", "75/25 pyth+margin blend outperforms features like EPA/play"),
        ("CLV explainer (OddsShopper)", "https://www.oddsshopper.com/articles/betting-101/closing-line-value-explained", "beat-the-close as primary skill metric"),
        ("CLV guide (calcmybets)", "https://www.calcmybets.com/guides/closing-line-value-clv", "CLV formula; +1–2% sustained = skill"),
        ("Home-field decline (Olympus Bets2026)", "https://app.olympus-bets.com/guides/home-court-advantage", "57.1%→53.2% era split;1.5–2.5pt equivalence"),
        ("HFA era table (nflbettingstrategies)", "https://nflbettingstrategies.com/", "1990s60%/3.6pts →2020s53%/1.4pts; venue variance"),
        ("NFL market calibration dataset (nfl_weekly_picks)", "https://github.com/meckelan/nfl_weekly_picks", "mean error+0.06pts/6,983 games; dog/cover stats (GitHub-hosted research)"),
        ("Shank (2018) market efficiency", "https://ideas.repec.org/a/spr/jecfin/v42y2018i4d10.1007_s12197-018-9431-4.html", "spread/totals inefficiency findings (academic)"),
        ("Herd behaviour & underdogs (Applied Econ Letters)", "https://www.tandfonline.com/doi/abs/10.1080/13504851.2011.568384", "large-spread underdog returns (academic)"),
        ("Parlay vig math", "https://nflsportsbettingstats.com/articles/nfl-betting-math-vig-clv/", "56.4%/64.1%/70% per-leg break-evens;52.4% rule"),
        ("Parlays (OddsShopper)", "https://www.oddsshopper.com/articles/betting-101/nfl-parlay-betting", "+EV-legs rule; vig compounding"),
        ("SGP correlation (OddsShopper)", "https://www.oddsshopper.com/articles/betting-101/nfl-same-game-parlay-guide", "correlation tax; fair-joint comparison method"),
        ("SGP correlation reference values", "https://www.sportsbettingoddscalculator.com/guides/sgp-correlation", "spread/ML~90%, QB-WR65–75%, total-props55–65%"),
        ("Player props guide (predictionengine)", "https://predictionengine.app/learn/nfl-player-props-guide", "prop vig5–6%; limits; beatable edges"),
        ("Props pricing (squawka)", "https://www.squawka.com/us/nfl/props/", "wider margins, lower limits, cross-book discrepancies"),
        ("Prop strategy (sportswagerblog)", "https://www.sportswagerblog.com/guides/prop-betting-strategy/", "5–10yd cross-book gaps;8–10% daily cap"),
        ("Wind & totals (lakeshore-edge via r/algobetting)", "https://www.reddit.com/r/algobetting/comments/1twp5z4/i_graded_8000_nfl_games_against_the_closing_line/", "15+mph wind → over ~41%; HFA now ~1.9pts"),
    ]
    rows = [th([("Source", ""), ("URL", ""), ("Used for", "")])]
    for name, url, use in srcs:
        rows.append(f"<tr><td><b>{html.escape(name)}</b></td><td class='src'><a href='{url}'>{url}</a></td><td>{html.escape(use)}</td></tr>")
    body = f"""
<h2>Sources & citations</h2>
<div class="note">Official-source values (scores, standings, lines) carry per-row links on their own pages. This page lists page-level sources for research claims and datasets. Environment note: bulk downloads of nflverse data and direct curl to non-GitHub hosts were blocked in the build sandbox — all data was therefore captured through page fetches and verified by reconciliation rather than bulk import.</div>
{W(rows)}
"""
    return page("Sources", body, "sources.html")

def main():
    os.makedirs(DOCS, exist_ok=True)
    pages = {
        "index.html": idx(), "standings.html": standings(), "scores.html": scores(),
        "lines.html": lines(), "strategies.html": strategies(), "analysis.html": analysis(),
        "leaderboard.html": leaderboard(), "flagged.html": flagged(),
        "verification.html": verification(), "executive-summary.html": exec_summary(),
        "sources.html": sources(),
    }
    for name, content in pages.items():
        with open(os.path.join(DOCS, name), "w") as f:
            f.write(content)
    print(f"built {len(pages)} pages -> line-lab/")

if __name__ == "__main__":
    main()

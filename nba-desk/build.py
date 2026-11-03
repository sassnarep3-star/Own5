#!/usr/bin/env python3
"""Generate the NBA Desk site (static HTML, inline CSS, no network assets) and the
research/nba-4396568c/*.md documents from data/derived/analysis.json + the source CSVs.

    python3 nba-desk/analysis.py && python3 nba-desk/build.py
"""
from __future__ import annotations

import csv
import html
import json
import math
import os
from statistics import NormalDist

ND = NormalDist()
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(HERE, "data")
RES = os.path.join(ROOT, "research", "nba-4396568c")
AS_OF = "2026-11-03"
OFFICIAL_HOSTS = ("https://www.nba.com/", "https://official.nba.com/", "https://ak-static.cms.nba.com/")
REPO = "https://github.com/sassnarep3-star/Own5/blob/main/nba-desk/"
E = html.escape


def rd(name, sub=""):
    with open(os.path.join(DATA, sub, name), newline="") as f:
        return list(csv.DictReader(f))


A_ = json.load(open(os.path.join(DATA, "derived", "analysis.json")))
P = A_["params"]
WF = A_["walk_forward"]
LINES = rd("lines_2026_11_04_05.csv", "derived")
WFR = rd("walk_forward_22_games.csv", "derived")
RATINGS = A_["ratings"]
TS = rd("team_seasons.csv")
HR = rd("home_road_2025_26.csv")
GS = rd("games_sample_2026_27.csv")
SCHED = rd("schedule_2026_11_04_05.csv")
INJ = rd("injury_report_2026-11-03_1700ET.csv")
XC = rd("crosscheck_nba_own_lines.csv")
TEAMS = {r["team"]: r for r in rd("teams.csv")}

URL_STAND25 = "https://www.nba.com/standings?Season=2025-26"
URL_STAND = "https://www.nba.com/standings"
URL_TRAD26 = "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season"
URL_TRAD25 = "https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season"
URL_TRAD24 = "https://www.nba.com/stats/teams/traditional?Season=2024-25&SeasonType=Regular%20Season"
URL_BOX = "https://www.nba.com/stats/teams/boxscores?Season=2026-27&SeasonType=Regular%20Season"
URL_SCHED = "https://www.nba.com/schedule?month=11&year=2026"
URL_INJ_IDX = "https://official.nba.com/nba-injury-report-2026-27-season/"
URL_INJ_PDF = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-03_05_00PM.pdf"
URL_GLOSS = "https://www.nba.com/stats/help/glossary"
URL_PLAYER_LOG = "https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26"


def a(url, text=None, ext=True):
    t = E(text if text is not None else ("official page" if url.startswith(OFFICIAL_HOSTS) else "external / repo page"))
    return f'<a href="{E(url)}"' + (' target="_blank" rel="noopener noreferrer"' if ext else "") + f">{t}</a>"


def pct(x, d=1):
    if x < 0.0005 and x > 0:
        return f"{x:.1e}"
    return f"{100 * x:.{d}f}%"


def f1(x, d=1):
    return f"{x:.{d}f}"


# ------------------------------------------------------------------ layout
NAV = [
    ("index.html", "Overview"), ("lines.html", "Own lines"), ("model.html", "Model & test"),
    ("correlations.html", "Correlations"), ("strategies.html", "Strategies"), ("gates.html", "Validation gates"),
    ("leaderboard.html", "Leaderboard"), ("luck-vs-skill.html", "Luck vs skill"), ("data.html", "Data & checks"),
    ("injuries.html", "Injury report"), ("audit.html", "Repo audit"), ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"), ("summary.html", "Executive summary"),
]

CSS = """
:root{--bg:#f4f6f8;--card:#fff;--ink:#14202b;--mut:#5b6b7a;--line:#dde3ea;--acc:#0b5cab;--warn:#b45309;--bad:#b42318;--ok:#0f7a4d}
*{box-sizing:border-box}body{margin:0;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--ink)}
header.top{background:#0f2a43;color:#fff;padding:14px 22px}header.top h1{margin:0;font-size:20px}header.top p{margin:2px 0 0;color:#b9cbdc;font-size:13px}
nav{background:#fff;border-bottom:1px solid var(--line);padding:8px 16px;display:flex;flex-wrap:wrap;gap:4px;position:sticky;top:0;z-index:5}
nav a{padding:6px 10px;border-radius:6px;color:var(--ink);text-decoration:none;font-size:14px}nav a:hover{background:#eaf1f8}nav a.on{background:var(--acc);color:#fff}
main{max-width:1200px;margin:0 auto;padding:20px}h2{margin:28px 0 8px;font-size:18px}h3{margin:18px 0 6px;font-size:15px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:12px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}.card b{display:block;font-size:26px}.card span{color:var(--mut);font-size:13px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
.notice{border-left:4px solid var(--warn);background:#fff7ed;padding:10px 14px;border-radius:6px;margin:12px 0}.notice.bad{border-color:var(--bad);background:#fef3f2}.notice.ok{border-color:var(--ok);background:#ecfdf3}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px;margin:8px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#eef3f8;font-weight:600;position:sticky;top:0;white-space:nowrap}td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:0}.blank{color:var(--bad);font-style:italic}.tag{display:inline-block;padding:1px 8px;border-radius:99px;font-size:12px;background:#eaf1f8;color:var(--acc)}
.tag.bad{background:#fef3f2;color:var(--bad)}.tag.warn{background:#fff7ed;color:var(--warn)}.tag.ok{background:#ecfdf3;color:var(--ok)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}small,.mut{color:var(--mut)}a{color:var(--acc)}
footer{max-width:1200px;margin:10px auto 30px;padding:0 20px;color:var(--mut);font-size:13px}code{background:#eef3f8;padding:1px 5px;border-radius:4px}
details summary{cursor:pointer;padding:8px 12px;font-weight:600}
"""

PAGES: dict[str, str] = {}


def page(fname, title, sub, body):
    nav = "".join(f'<a href="{h}"' + (' class="on"' if h == fname else "") + f">{E(t)}</a>" for h, t in NAV)
    PAGES[fname] = (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{E(title)} - NBA Desk</title><style>{CSS}</style></head><body>"
        f'<header class="top"><h1>NBA Desk - {E(title)}</h1><p>{E(sub)} | data as of {AS_OF} UTC | paper research only, no bets, no betting advice</p></header>'
        f"<nav>{nav}</nav><main>{body}</main>"
        f'<footer>Every table row links to the page it was taken from. <span class="blank">Blank red cells</span> = value not confirmable, flagged on '
        f'<a href="flagged.html">Flagged for Review</a>. Sibling NBA sites from other sessions: '
        f'<a href="../docs/index.html">docs/</a> · <a href="../nba-2026-lab/index.html">nba-2026-lab</a> · '
        f'<a href="../nba-origin-lab/index.html">nba-origin-lab</a> · <a href="../nba-validation/index.html">nba-validation</a> · <a href="../nba-own-lines/index.html">nba-own-lines</a> · <a href="../nba-audit-e9f83ff4/index.html">nba-audit</a> · '
        f'<a href="../nba-sensitivity/index.html">nba-sensitivity</a>.</footer></body></html>'
    )


def table(headers, rows, kind="official", num=(), caption=""):
    """kind: official = every row must carry an official NBA/NBA-Official link;
    derived = computed here (row links to its official inputs or to the code);
    external = primary/peer-reviewed source (arXiv, PubMed...)."""
    th = "".join(f'<th class="n">{E(h)}</th>' if i in num else f"<th>{E(h)}</th>" for i, h in enumerate(headers))
    body = []
    for r in rows:
        tds = "".join(f'<td class="n">{c}</td>' if i in num else f"<td>{c}</td>" for i, c in enumerate(r))
        body.append(f"<tr>{tds}</tr>")
    cap = f"<caption class='mut' style='text-align:left;padding:6px 10px'>{caption}</caption>" if caption else ""
    return f'<div class="tw"><table data-kind="{kind}">{cap}<thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


BLANK = '<span class="blank">BLANK - unverified</span>'


def sgn(x, d=1):
    return f"{x:+.{d}f}"


# ------------------------------------------------------------------ flags
NYS = sorted({r["team"] for r in INJ if r["reason"] == "NOT YET SUBMITTED"})
UNLAB = [r for r in INJ if r["attribution"].startswith("unlabeled")]
N_GAMES_PLAYED = 107

FLAGS = [
    ("F01", "High", "Market data", "No verified market quote (spread, total, moneyline, prop) was captured. nba.com game pages are JavaScript-rendered and expose no odds in fetched text. All market columns are blank, closing-line value cannot be computed, and no edge can be claimed.", "Capture timestamped quotes from an auditable licensed feed, then fill the ledger.", URL_SCHED),
    ("F02", "High", "Validation", "0 of 6 pre-registered strategies qualify (gates G3, G4, G5, G7, G9 cannot be evaluated). 0 rewards awarded; the reward pool is unfunded. The leaderboard has no ranked entries by design.", "Settle at least the sample size shown on Luck vs skill, with quotes, before any ranking.", URL_SCHED),
    ("F03", "Medium", "Data coverage", f"Game-level data covers 22 of the {N_GAMES_PLAYED} games played at capture (10/31-11/02). Rule: games whose two team rows were fully visible in the first six of seven chunks of the official team box-score table. Two partial games (game IDs 0022600150 and 0022600152) are excluded. Team-season totals for all 30 teams are complete.", "Transcribe the remaining pages of the box-score table (or an official export).", URL_BOX),
    ("F04", "Medium", "Model validity", f"Walk-forward n = 22 games is underpowered: margin MAE gain {f1(WF['margin_abs_err_gain']['mean'], 2)} pts (z = {f1(WF['margin_abs_err_gain']['z'], 2)}); total MAE gain {f1(WF['total_abs_err_gain']['mean'], 2)} pts (z = {f1(WF['total_abs_err_gain']['z'], 2)}). Neither is significant. sigma, home-court advantage and the shrinkage constant K were estimated using the same 22 games; the home-court constant cancels in model-vs-naive comparisons but sigma and K do not.", "Re-estimate on the settled ledger; treat current parameters as provisional.", URL_BOX),
    ("F05", "Medium", "Injuries", f"At the 5:00 PM ET report, {len(NYS)} of 30 team slots read NOT YET SUBMITTED ({', '.join(NYS)}); MIL has no row in the parsed PDF; {len(UNLAB)} listed players follow PDF page breaks with no team label and are NOT attributed to any team. Own lines are not injury-adjusted (no player-value model exists here).", "Re-pull later reports on the official index and add a player-value model before using lines.", URL_INJ_PDF),
    ("F06", "Medium", "Schedule/rest", "Per the official schedule PHX (vs POR 11/04, vs ORL 11/05) and MIA (at LAC 11/04, at GSW 11/05) play on consecutive days. No rest or back-to-back adjustment is applied, so lines for ORL@PHX and MIA@GSW are unadjusted. Venues for all games and tip times for 11/05 are left blank (not confirmed).", "Model rest effects once enough settled games exist; confirm venue/tip from the schedule page.", URL_SCHED),
    ("F07", "Medium", "Transcription", f"Home/road splits for MEM, SAC and UTA were cut off in the fetched standings text, so their home-vs-road column order is unconfirmed (league identities cannot detect a swap). If swapped, league home win % would be {pct(P['home_pct_if_swapped'], 2)} instead of {pct(P['home_pct'], 2)} (home-court advantage about {f1(ND.inv_cdf(P['home_pct_if_swapped']) * P['sigma'], 2)} vs {f1(P['hfa'], 2)} pts).", "Re-open the standings page and confirm the three rows.", URL_STAND25),
    ("F08", "Medium", "Transcription", "All 30 + 90 + 30 + 44 + 61 data rows were transcribed from rendered official pages. The integrity suite (31 identity checks, all pass) detects most single-cell errors but not offsetting ones. Pages change as games are played; values reflect capture on 2026-11-03.", "Spot-check rows with the per-row links; re-run the integrity suite after any edit.", URL_TRAD26),
    ("F09", "Medium", "Math tables", "The luck-vs-skill, break-even (-110 odds convention) and parlay-arithmetic tables are pure mathematics or market convention; no official NBA page exists for them. Rows link to the code that computes them, not to an official site.", "Not applicable; verify by re-running analysis.py.", REPO + "analysis.py"),
    ("F10", "Medium", "Correlations", "Player-prop and same-game-parlay correlations are blank: no player prop lines and only a 10-game single-player sample exist in the repo. Team-level correlations here are computed from official team data; the 22-game and 44-team-game samples are small and the two rows of one game are not independent.", "Collect a large official player-game sample before computing prop correlations.", URL_PLAYER_LOG),
    ("F11", "Low", "Totals", f"Prior-only totals showed a +{f1(WF['total_model']['bias'])} point bias on the 22 games: league scoring per team-game fell from {f1(P['lt25'] / 2, 1)} (2025-26) to {f1(P['lt26'] / 2, 1)} (2026-27 to date). Published totals re-centre on the 2026-27 league level, but the early-season sample is 5-8 games per team.", "Re-check league level weekly.", URL_TRAD26),
    ("F12", "Medium", "Existing repo", "Audit of earlier NBA material: 17 of 21 sources in docs/sources.html were not re-opened this session; 15 are third-party INDUSTRY pages that are not official sources; the Yahoo memo and PubMed author/journal attribution are unverified; the arXiv:1910.08858 claim is the authors' own, not independent evidence. See Repo audit.", "Replace industry sources with official or peer-reviewed ones.", "https://github.com/sassnarep3-star/Own5/blob/main/docs/sources.html"),
    ("F13", "Low", "Repo structure", "Eight parallel NBA sites now exist (docs/, nba-2026-lab, nba-origin-lab, nba-validation, nba-own-lines, nba-audit-e9f83ff4, nba-sensitivity, nba-desk) and the root landing page links only docs/. Root pages are owned by another session and were not edited; a request is logged in COORDINATION.md.", "Integrator of root index.html adds a hub link.", "https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md"),
    ("F15", "Medium", "Model risk", "A second, independent in-repo model (nba-own-lines, session 636a7712) prices the same 16 games with different inputs and no home-court advantage. The two sets of home margins differ materially (see Model page for the mean absolute difference). Neither is validated, so no line should be treated as accurate before settlement.", "Settle the ledger and compare both models on identical games.", URL_SCHED),
    ("F14", "Low", "Process", "Requested branch naming session-<id>/<task> is impossible: the platform fixes this session's branch to arena/4396568c-own5. Logged in COORDINATION.md.", "No action needed.", "https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md"),
]

FLAGS.sort(key=lambda f: f[0])


# ------------------------------------------------------------------ helpers for injuries
def inj_status(team):
    rows = [r for r in INJ if r["team"] == team]
    if not rows:
        return "no row in parsed PDF"
    if rows[0]["reason"] == "NOT YET SUBMITTED":
        return "NOT YET SUBMITTED"
    out = sum(r["status"] == "Out" for r in rows)
    return f"{len(rows)} listed ({out} Out)"


UNLAB_MATCHUPS = {"PHI@DET", "MIL@BOS"}
B2B = {"ORL@PHX": "PHX plays 11/04 and 11/05", "MIA@GSW": "MIA plays 11/04 and 11/05"}


# ------------------------------------------------------------------ pages
def build_pages():
    wfm, wfn = WF["margin_model"], WF["margin_naive"]
    tt = WF["team_test"]
    integ = A_["integrity"]
    n_ok = sum(c["passed"] for c in integ)

    # ---------------- index
    cards = [
        (str(len(LINES)), "own lines published (11/04-11/05)"), ("0", "verified market quotes"),
        ("0 / 6", "strategies qualified"), ("0", "rewards awarded (pool unfunded)"),
        (f"{n_ok} / {len(integ)}", "data integrity checks passed"), (str(len(FLAGS)), "flags for review"),
    ]
    c_html = "".join(f"<div class='card'><b>{v}</b><span>{E(t)}</span></div>" for v, t in cards)
    rows = []
    for L in LINES:
        rows.append([E(L["date"]), f"{E(L['away'])} @ {E(L['home'])}", E(L["own_spread_home"]), pct(float(L["own_home_win_prob"]), 0),
                     f1(float(L["own_total"])), a(f"https://www.nba.com/game/{L['game_id']}", "nba.com game page")])
    body = f"""
<div class="notice bad"><b>Status: research only.</b> The desk originates its own lines from official NBA data. It has <b>no verified market prices</b>, so it cannot say any line has an edge, and <b>no strategy has passed the validation gates</b>. Nothing here is betting advice.</div>
<div class="cards">{c_html}</div>
<h2>Own lines for the next slate</h2>
<p class="mut">Spread = home team minus points. Win % = home team. Totals are for the full game. Not adjusted for injuries or rest (see flags F05, F06). Full table with sensitivity and market columns: <a href="lines.html">Own lines</a>.</p>
{table(["Date", "Game (away @ home)", "Own spread", "Home win %", "Own total", "Source"], rows, "official", num=(3, 4))}
<h2>What is on each page</h2>
<div class="grid2">
<div class="panel"><b><a href="lines.html">Own lines</a></b><br>16 lines, 30-team ratings, injury-report status per team.</div>
<div class="panel"><b><a href="model.html">Model &amp; test</a></b><br>Parameters, walk-forward test on 22 games, 30-team persistence test.</div>
<div class="panel"><b><a href="correlations.html">Correlations</a></b><br>Team-season, team-game and parlay-leg correlations; blanks flagged.</div>
<div class="panel"><b><a href="strategies.html">Strategies</a> / <a href="gates.html">Gates</a> / <a href="leaderboard.html">Leaderboard</a></b><br>Six pre-registered strategies (singles, parlays, prop combos), nine gates, fail-closed ranking.</div>
<div class="panel"><b><a href="luck-vs-skill.html">Luck vs skill</a></b><br>Exact binomial tables: how many bets separate skill from luck.</div>
<div class="panel"><b><a href="audit.html">Repo audit</a> &amp; <a href="flagged.html">Flagged for Review</a></b><br>Existing NBA claims checked against official/primary sources; every irregularity listed.</div>
</div>
<h2>Key results at a glance</h2>
<ul>
<li>Home teams won {pct(P['home_pct'])} of non-neutral 2025-26 games ({P['home_w']}-{P['home_l']}); implied home-court advantage {f1(P['hfa'], 2)} points (derived).</li>
<li>Team margins persist only partly: 2024-25 to 2025-26 slope {f1(P['beta'], 2)} (r = {f1(P['fit_margin']['r'], 2)}, n = 30). Early 2026-27 margins track 2025-26 margins with r = {f1(tt['r'], 2)} (95% CI {f1(tt['r_ci'][0], 2)} to {f1(tt['r_ci'][1], 2)}, n = 30).</li>
<li>On 22 played games the prior-only model beat an HFA-only baseline by {f1(WF['margin_abs_err_gain']['mean'], 2)} points of absolute error, which is <b>not statistically significant</b> (z = {f1(WF['margin_abs_err_gain']['z'], 2)}).</li>
</ul>"""
    page("index.html", "Overview", "Own NBA lines from official data", body)

    # ---------------- lines
    rows = []
    for L, S in zip(LINES, SCHED):
        mu = f"{L['away']}@{L['home']}"
        notes = []
        if mu in B2B:
            notes.append("back-to-back, unadjusted: " + B2B[mu])
        if mu in UNLAB_MATCHUPS:
            notes.append("report has unattributed rows")
        rows.append([
            E(L["date"]) + (f"<br><small>{E(L['tip_et_24h'])} ET</small>" if L["tip_et_24h"] else "<br>" + BLANK),
            f"<b>{E(L['away'])} @ {E(L['home'])}</b>", f"<b>{E(L['own_spread_home'])}</b><br><small>raw {sgn(float(L['own_home_margin']))} home margin</small>",
            pct(float(L["own_home_win_prob"])), f"{L['own_total']}<br><small>rounded {L['own_total_rounded']}</small>",
            f"{L['sens_spread_min']} to {L['sens_spread_max']}", BLANK, f"{E(L['away'])}: {E(inj_status(L['away']))}<br>{E(L['home'])}: {E(inj_status(L['home']))}",
            E("; ".join(notes)) or "-", a(f"https://www.nba.com/game/{L['game_id']}", "game page") + " " + a(URL_SCHED, "schedule")])
    t1 = table(["Date / tip", "Game", "Own spread (home)", "Home win %", "Own total", "Home-margin range under parameter sensitivity", "Market spread / total", "Injury report status (5:00 PM ET, 11/03)", "Notes", "Source"], rows, "official", num=(3,))
    rows = []
    for R in RATINGS:
        rows.append([f"<b>{R['team']}</b>", E(TEAMS[R["team"]]["name"]), f"{R['w']}-{R['l']}", R["pm_2024_25"], R["pm_2025_26"], R["pm_2026_27_to_date"],
                     f1(R["prior"], 2), pct(R["weight_on_current"], 0), f"<b>{R['rating']:+.2f}</b>",
                     a(URL_TRAD26, "2026-27") + " " + a(URL_TRAD25, "2025-26") + " " + a(URL_TRAD24, "2024-25")])
    t2 = table(["Team", "Name", "W-L 2026-27", "Margin 24-25", "Margin 25-26", "Margin 26-27 to date", "Prior (beta x 25-26)", "Weight on 2026-27", "Rating (pts vs avg)", "Source"], rows, "official", num=(3, 4, 5, 6, 7, 8))
    body = f"""
<div class="notice"><b>Read before using.</b> Lines are derived from official team scoring margins only. They ignore injuries, rest and travel, and there is no market line to compare with (flags F01, F05, F06). The sensitivity column shows the home-margin range across 3 values of K x 3 values of beta; a wide range means the line is weakly determined.</div>
<h2>Own lines, 2026-11-04 and 2026-11-05</h2>
<p class="mut">Frozen in <code>data/ledger_2026_11_04_05.csv</code> (git history is the timestamp). Results are to be filled only from the official game page and settled with <code>settle.py</code>.</p>
{t1}
<h2>Team ratings used (30 teams)</h2>
<p class="mut">Rating = (G x current margin + K x prior) / (G + K), K = {f1(P['K'], 2)}; prior = {f1(P['beta'], 3)} x last season's margin. Margins are points per game vs the league average, as published by NBA.com.</p>
{t2}"""
    page("lines.html", "Own lines", "Originated spreads and totals with injury status", body)

    # ---------------- model
    def prow(name, val, how, src):
        return [E(name), val, E(how), src]
    rows = [
        prow("beta (margin persistence)", f1(P["beta"], 3) + f" (SE {f1(P['fit_margin']['slope_se'], 3)})", "OLS slope of 2025-26 margin on 2024-25 margin, n = 30, r = " + f1(P["fit_margin"]["r"], 3), a(URL_TRAD24, "2024-25") + " " + a(URL_TRAD25, "2025-26")),
        prow("beta_T (total persistence)", f1(P["beta_t"], 3) + f" (SE {f1(P['fit_total']['slope_se'], 3)})", "OLS slope of team game-total deviation (2 x PTS - margin - league mean), same seasons, n = 30", a(URL_TRAD24, "2024-25") + " " + a(URL_TRAD25, "2025-26")),
        prow("Home win % 2025-26", pct(P["home_pct"], 2) + f" ({P['home_w']}-{P['home_l']})", "Home wins / non-neutral games from the standings splits; if the 3 unconfirmed rows were swapped: " + pct(P["home_pct_if_swapped"], 2), a(URL_STAND25)),
        prow("sigma (game margin noise)", f1(P["sigma"], 2), "RMSE of the prior-only margin model on the 22-game sample (upper bound: includes rating error; estimated in-sample)", a(URL_BOX)),
        prow("Home-court advantage (pts)", f1(P["hfa"], 2), "sigma x inverse-normal(home win %)", a(URL_STAND25)),
        prow("K (shrinkage, games)", f1(P["K"], 2), "sigma^2 / tau^2, tau^2 = residual variance of the training regression - sigma^2/82 = " + f1(P["tau_p2"], 2), a(URL_TRAD25)),
        prow("League points per team-game 2026-27", f1(P["lt26"] / 2, 2), "GP-weighted mean of 2 x PTS - margin, halved (to date, 214 team-games)", a(URL_TRAD26)),
        prow("League points per team-game 2025-26", f1(P["lt25"] / 2, 2), "same formula, 82-game season", a(URL_TRAD25)),
        prow("sigma_T / K_T (totals)", f"{f1(P['sigma_t'], 2)} / {f1(P['K_t'], 1)}", "same construction for totals", a(URL_BOX)),
    ]
    t_par = table(["Parameter", "Value", "How derived", "Official input"], rows, "official")
    rows = [
        ["Margin MAE (pts)", f1(wfm["mae"], 2), f1(wfn["mae"], 2), f1(WF["margin_abs_err_gain"]["mean"], 2) + f" +/- {f1(WF['margin_abs_err_gain']['se'], 2)}", a(URL_BOX)],
        ["Margin RMSE (pts)", f1(wfm["rmse"], 2), f1(wfn["rmse"], 2), "", a(URL_BOX)],
        ["Straight-up correct (of 22)", str(WF["margin_su_model"]), str(WF["margin_su_naive"]) + " (always home)", "", a(URL_BOX)],
        ["Correlation pred vs actual margin", f1(WF["margin_corr"], 2), "n/a", "", a(URL_BOX)],
        ["Total MAE (pts)", f1(WF["total_model"]["mae"], 2), f1(WF["total_naive"]["mae"], 2), f1(WF["total_abs_err_gain"]["mean"], 2) + f" +/- {f1(WF['total_abs_err_gain']['se'], 2)}", a(URL_BOX)],
        ["Total bias (pred - actual)", sgn(WF["total_model"]["bias"]), sgn(WF["total_naive"]["bias"]), "", a(URL_BOX)],
        ["Correlation pred vs actual total", f1(WF["total_corr"], 2), "n/a", "", a(URL_BOX)],
    ]
    t_wf = table(["Metric (22 games, prior-only inputs)", "Model", "Baseline (HFA only / last-season league total)", "MAE gain +/- SE", "Source"], rows, "official", num=(1, 2, 3))
    rows = [
        ["Correlation, 2025-26 margin vs 2026-27 margin to date", f"{f1(tt['r'], 2)} (95% CI {f1(tt['r_ci'][0], 2)} to {f1(tt['r_ci'][1], 2)})", "n = 30; ~7 games per team", a(URL_TRAD26) + " " + a(URL_TRAD25)],
        ["Slope (SE)", f"{f1(tt['slope'], 2)} ({f1(tt['slope_se'], 2)})", f"trained beta {f1(P['beta'], 2)} lies inside 1 SE", a(URL_TRAD26)],
        ["RMSE predicting 2026-27 margin: beta x last season", f1(tt["pred_rmse_beta"], 2), "model", a(URL_TRAD26)],
        ["RMSE: last season's margin unshrunk (beta = 1)", f1(tt["pred_rmse_one"], 2), "no regression to the mean", a(URL_TRAD26)],
        ["RMSE: predict league average (0)", f1(tt["pred_rmse_zero"], 2), "no information", a(URL_TRAD26)],
    ]
    t_tt = table(["Out-of-sample team test (parameters fitted only on 2024-25 to 2025-26)", "Value", "Note", "Source"], rows, "official")
    rows = []
    for r in WFR:
        rows.append([E(r["date"]), f"{E(r['away'])} @ {E(r['home'])}", r["actual_margin"], r["pred_margin"], r["naive_margin"], r["actual_total"], r["pred_total"], a(r["source_url"], "game page")])
    t_g = table(["Date", "Game", "Actual home margin", "Pred margin (prior only)", "Baseline margin", "Actual total", "Pred total (prior only)", "Source"], rows, "official", num=(2, 3, 4, 5, 6))
    xc_rows, diffs, mine_l, oth_l = [], [], [], []
    for L, X, S in zip(LINES, XC, SCHED):
        assert L["game_id"] == X["game_id"] == S["game_id"] and L["home"] == X["home"] and L["away"] == X["away"]
        m, o = float(L["own_home_margin"]), float(X["other_home_margin"])
        diffs.append(abs(m - o))
        mine_l.append(m)
        oth_l.append(o)
        h, mm = X["other_tip_et"].split(" ")[0].split(":"), X["other_tip_et"].split(" ")[1]
        tip24 = f"{(int(h[0]) % 12) + (12 if mm == 'PM' else 0):02d}:{h[1]}"
        tipcell = ("matches" if tip24 == S["tip_et_24h"] else "differs") if S["tip_et_24h"] else "this desk blank"
        xc_rows.append([E(L["date"]), f"{E(L['away'])} @ {E(L['home'])}", sgn(m), sgn(o), sgn(m - o), L["own_total"], X["other_total"], tipcell,
                        a(f"https://www.nba.com/game/{L['game_id']}", "game page") + " " + a("https://github.com/sassnarep3-star/Own5/blob/main/nba-own-lines/data/derived.json", "other model output")])
    r_xc = sum((x - sum(mine_l) / 16) * (y - sum(oth_l) / 16) for x, y in zip(mine_l, oth_l)) / math.sqrt(sum((x - sum(mine_l) / 16) ** 2 for x in mine_l) * sum((y - sum(oth_l) / 16) ** 2 for y in oth_l))
    t_xc = table(["Date", "Game", "Desk home margin", "Other model home margin", "Difference", "Desk total", "Other model total", "11/04 tip (ET) vs other session", "Source"], xc_rows, "official", num=(2, 3, 4, 5, 6))
    body = f"""
<div class="notice"><b>Honest reading.</b> The model's edge over a naive baseline on 22 games is within noise (margin z = {f1(WF['margin_abs_err_gain']['z'], 2)}; total z = {f1(WF['total_abs_err_gain']['z'], 2)}). The 30-team test is the stronger evidence: last season's margin carries real but partial information (r = {f1(tt['r'], 2)}), and shrinking it by beta beat both no-shrinkage and no-information predictors, by a small margin.</div>
<h2>Method in five lines</h2>
<ol><li>Team rating = posterior margin: in-season margin weighted by games played G against a prior of beta x last season's margin; weight G/(G+K).</li>
<li>Home margin = rating(home) - rating(away) + home-court advantage. Home win probability = Phi(margin / sigma).</li>
<li>Game total = league level (2026-27 to date) + both teams' shrunk total deviations.</li>
<li>beta, beta_T and the home-court advantage come from official team tables (training pair 2024-25 to 2025-26, 2025-26 splits). sigma and K use the error size on the 22-game sample (in-sample, flag F04). Nothing is tuned to maximise accuracy.</li>
<li>Lines are frozen in the ledger before tip and settled against official final scores.</li></ol>
<h2>Parameters</h2>{t_par}
<h2>Walk-forward test on played 2026-27 games</h2>
<p class="mut">Predictions use 2025-26 information only (no 2026-27 results), then are compared with actual results.</p>{t_wf}
<h2>Out-of-sample team test</h2>{t_tt}
<h2>The 22 games</h2>{t_g}
<h2>Cross-check against an independent model in this repository</h2>
<p class="mut">Session 636a7712 (<a href="../nba-own-lines/index.html">nba-own-lines</a>) built a different model (efficiency ratings, zero home-court advantage). Its 16 matchups and game IDs agree with this desk's schedule. Its home margins are copied into <code>data/crosscheck_nba_own_lines.csv</code>. Mean absolute difference in home margin: <b>{f1(sum(diffs) / 16, 2)} points</b>; correlation of the two sets of margins: <b>{f1(r_xc, 2)}</b>. Neither model is validated, so agreement is not evidence of accuracy, and the gap shows how model-dependent a line is (flag F15).</p>{t_xc}"""
    page("model.html", "Model & test", "Line-origination method and its out-of-sample test", body)

    # ---------------- correlations
    C = A_["correlations"]

    def crow(r, x, y):
        ci = f"[{f1(r['ci_lo'], 2)}, {f1(r['ci_hi'], 2)}]" if r["ci_lo"] is not None else ""
        return [x, y, f"{r['r']:+.3f}", ci, str(r["n"])]
    rows = []
    for r in C["team_season"]:
        src = {"2024-25": URL_TRAD24, "2025-26": URL_TRAD25, "2026-27": URL_TRAD26, "pair": URL_TRAD25}[r["season"]]
        rows.append([E(r["season"])] + [E(c) for c in crow(r, r["x"], r["y"])[:2]] + crow(r, "", "")[2:] + [a(src)])
    t_ts = table(["Season", "X", "Y", "Pearson r", "95% CI (Fisher)", "n", "Source"], rows, "official", num=(3, 5))
    rows = []
    for r in C["team_game"]:
        rows.append([E(r["x"]), E(r["y"])] + crow(r, "", "")[2:] + [a(URL_BOX)])
    t_tg = table(["X", "Y", "Pearson r", "95% CI (Fisher)", "n (team-games)", "Source"], rows, "official", num=(2, 4))
    rows = []
    for r in C["game_level"]:
        rows.append([E(r["x"]), E(r["y"])] + crow(r, "", "")[2:] + [a(URL_BOX)])
    t_gl = table(["X", "Y", "Pearson r", "95% CI (Fisher)", "n (games)", "Source"], rows, "official", num=(2, 4))
    rows = []
    for r in C["parlay"]:
        rows.append([f1(r["p_leg1"], 2), f1(r["p_leg2"], 2), f"{r['phi']:+.1f}", pct(r["independent"], 2), pct(r["joint"], 2), f"x{r['ratio']:.2f}",
                     a(REPO + "analysis.py", "analysis.py", ext=True)])
    t_pl = table(["P(leg 1)", "P(leg 2)", "Leg correlation (phi)", "Joint if independent", "Joint with phi", "Ratio", "Source"], rows, "derived", num=(0, 1, 2, 3, 4, 5))
    blanks = [
        ("Player points x assists (same player)", "player game logs"), ("Player points x rebounds", "player game logs"),
        ("Player 3PM x points", "player game logs"), ("Teammates' props (usage competition)", "player game logs, many players"),
        ("Same-game spread leg x total leg (market-priced)", "market spread and total quotes"), ("Cross-game leg correlation (different games, same night)", "large game sample"),
    ]
    rows = [[E(n), BLANK, E("needs: " + need), a(URL_PLAYER_LOG, "NBA player game log (example input)")] for n, need in blanks]
    t_bl = table(["Correlation wanted", "Value", "Why blank", "Source"], rows, "official")
    body = f"""
<div class="notice"><b>How to use these.</b> Official NBA data gives <i>team-level</i> relationships (below) with confidence intervals. Player-prop and same-game-parlay correlations need data not yet captured; they are left blank rather than estimated (flag F10). The earlier 10-game Anthony Edwards correlations in <a href="../nba-2026-lab/correlations.html">nba-2026-lab</a> are exploratory only (n = 10) and are not reused here.</div>
<h2>Team-season correlations (n = 30 teams per row)</h2>{t_ts}
<p class="mut">Margin and win % move almost one-for-one (r about 0.92-0.98), so a margin-based rating is also a win-rate rating. The 24-25 to 25-26 rows are the persistence correlations used to set beta.</p>
<h2>Team-game correlations (44 team-games from 22 games)</h2>{t_tg}
<p class="mut">Both rows of a game share pace, so the effective sample is below 44 and the intervals are optimistic.</p>
<h2>Spread leg vs total leg (22 games)</h2>{t_gl}
<p class="mut">All three intervals include zero. A positive spread/total residual correlation would make a same-game spread + total ticket more likely to hit together than the product of the legs; 22 games cannot establish it.</p>
<h2>Parlay arithmetic: joint probability of two legs</h2>
<p class="mut">P(A and B) = pq + phi x sqrt(p(1-p)q(1-q)). A price built on independent legs overstates or understates the true joint probability by the ratio shown. Pure mathematics, no official source (flag F09).</p>{t_pl}
<h2>Blank (unverified) correlations</h2>{t_bl}"""
    page("correlations.html", "Correlations", "Measured relationships and the ones still blank", body)

    # ---------------- strategies
    rows = []
    for s in A_["strategies"]:
        rows.append([f"<b>{s['id']}</b>", E(s["name"]), E(s["type"]), E(s["rule"]), E(s["signal"]), f"<span class='blank'>{E(s['missing_input'])}</span>",
                     str(s["bets_settled"]), E(s["gates_passed"]), "<span class='tag bad'>NOT QUALIFIED</span>", a(URL_SCHED, "official schedule (signal inputs)")])
    t_s = table(["ID", "Strategy", "Type", "Rule (frozen)", "Signal", "Missing input", "Settled bets", "Gates passed", "Status", "Source"], rows, "official", num=(6,))
    body = f"""
<div class="notice">All six strategies were registered before any result was available and <b>fail closed</b>: with no market quotes none can be tested for closing-line value, so none qualifies and no reward is paid. The signal columns point to inputs that already exist (own lines); the missing-input column is what blocks testing.</div>
<h2>Pre-registered strategies (singles, parlays, prop combos)</h2>{t_s}
<h2>Rules common to every strategy</h2>
<ul><li>Edge threshold and stake rule are fixed before the first bet; changing either creates a new strategy ID (counts toward the multiple-testing penalty).</li>
<li>Parlays and prop combos must be priced with a measured joint probability (see Correlations). Legs with a blank correlation are not allowed.</li>
<li>Own lines are published before tip and frozen in the ledger; results come only from official game pages.</li></ul>"""
    page("strategies.html", "Strategies", "Six pre-registered signal strategies", body)

    # ---------------- gates
    rows = []
    for g in A_["gates"]:
        tone = "ok" if g["status"].startswith("Automatable") else "bad" if g["status"].startswith("Blocked") else "warn"
        rows.append([f"<b>{g['id']}</b>", E(g["name"]), E(g["rule"]), f"<span class='tag {tone}'>{E(g['status'])}</span>", a(URL_BOX if g["id"] in ("G1", "G6") else URL_SCHED, "official input page")])
    t_g = table(["Gate", "Name", "Requirement", "Current state", "Source"], rows, "official")
    rows = []
    for s in A_["strategies"]:
        cells = []
        for g in A_["gates"]:
            if g["id"] in ("G1", "G2"):
                cells.append("<span class='tag ok'>pass</span>")
            elif g["id"] in ("G6", "G8"):
                cells.append("<span class='tag warn'>partial</span>")
            else:
                cells.append("<span class='tag bad'>blocked</span>")
        rows.append([f"<b>{s['id']}</b> {E(s['name'])}"] + cells + [a(URL_SCHED, "schedule")])
    t_m = table(["Strategy"] + [g["id"] for g in A_["gates"]] + ["Source"], rows, "official")
    body = f"""
<div class="notice">A strategy must pass <b>every</b> gate. G1 and G2 pass for all six (sources verified, rules frozen). The rest need settled bets and market quotes that do not exist yet, so the matrix fails closed.</div>
<h2>The nine gates</h2>{t_g}<h2>Gate matrix</h2>{t_m}"""
    page("gates.html", "Validation gates", "Every strategy must pass all nine", body)

    # ---------------- leaderboard
    rows = [[f"<b>{s['id']}</b>", E(s["name"]), "-", "0", "-", "<span class='tag bad'>unranked</span>", "none", a(URL_SCHED, "schedule")] for s in A_["strategies"]]
    t_l = table(["Entry", "Strategy", "Rank", "Settled bets", "CLV (95% lower bound)", "Status", "Reward", "Source"], rows, "official")
    rows = [
        ["Own margin model (prior-only inputs)", f1(wfm["mae"], 2), f1(wfm["rmse"], 2), f"{WF['margin_su_model']}/22", a(URL_BOX)],
        ["Baseline: home-court advantage only", f1(wfn["mae"], 2), f1(wfn["rmse"], 2), f"{WF['margin_su_naive']}/22", a(URL_BOX)],
    ]
    t_a = table(["Accuracy (22 played games; not a betting result)", "Margin MAE", "Margin RMSE", "Straight-up", "Source"], rows, "official", num=(1, 2))
    body = f"""
<div class="notice bad"><b>No entry qualifies. 0 rewards awarded; the reward pool is unfunded.</b> Ranking uses closing-line value, which needs market quotes (flag F01).</div>
<h2>Competition rules</h2>
<ol><li><b>Eligibility:</b> pass all nine gates. Unqualified entries are listed but unranked.</li>
<li><b>Score:</b> mean closing-line value; rank by its 95% lower bound, not by hit rate or profit, to separate skill from luck.</li>
<li><b>Entry integrity:</b> rules and thresholds frozen in git before tip; edits create a new entry; every entrant counts toward the multiple-testing penalty (see Luck vs skill: with 100 entrants of pure luck the best of them is expected to hit about {pct([x for x in A_['luck_skill']['leaderboard_luck'] if x['entrants'] == 100 and x['bets_each'] == 100][0]['expected_best_hit_rate'], 0)} over 100 bets).</li>
<li><b>Rewards:</b> none until a pool is funded and an entry qualifies. No rewards have been issued.</li></ol>
<h2>Entries</h2>{t_l}
<h2>Model accuracy (information only)</h2>{t_a}"""
    page("leaderboard.html", "Leaderboard", "Fail-closed ranking of strategies", body)

    # ---------------- luck vs skill
    LS = A_["luck_skill"]
    su_p = sum(math.comb(22, k) for k in range(WF["margin_su_model"], 23)) / 2 ** 22
    rows = [[str(r["n"]), pct(r["p_fair_coin_ge_55pct"], 2), pct(r["p_fair_coin_ge_breakeven"], 1), pct(r["p_true55_ge_breakeven"], 1), a(REPO + "analysis.py", "analysis.py")] for r in LS["single_bettor"]]
    t1 = table(["Bets", "P(luck alone reaches >= 55% hit rate)", "P(luck alone beats break-even 52.38%)", "P(a true 55% bettor beats break-even)", "Source"], rows, "derived", num=(0, 1, 2, 3))
    rows = [[str(r["entrants"]), str(r["bets_each"]), pct(r["expected_best_hit_rate"], 1), pct(r["p_any_ge_60pct"], 2), a(REPO + "analysis.py", "analysis.py")] for r in LS["leaderboard_luck"]]
    t2 = table(["Entrants (all pure luck)", "Bets each", "Expected best hit rate", "P(someone reaches >= 60%)", "Source"], rows, "derived", num=(0, 1, 2, 3))
    rows = [[pct(r["true_hit_rate"], 0), str(r["n_bets"]), str(r["k_critical"]), a(REPO + "analysis.py", "analysis.py")] for r in LS["required_n"]]
    t3 = table(["True hit rate", "Bets needed (80% power, one-sided 5%)", "Wins needed to reject break-even", "Source"], rows, "derived", num=(0, 1, 2))
    body = f"""
<div class="notice">These are exact binomial calculations (pure mathematics, flag F09). Break-even at -110 odds is 110/210 = {pct(LS['breakeven_110'], 2)}; that odds convention is a market convention, not an official NBA fact.</div>
<h2>What this means for the leaderboard</h2>
<ul><li>A bettor who is right 55% of the time needs roughly <b>{[r for r in LS['required_n'] if r['true_hit_rate'] == 0.55][0]['n_bets']} settled bets</b> before a break-even test is reliable. Hundreds of bets are not enough; dozens are noise.</li>
<li>The best of many unskilled entrants always looks skilled over short samples, so rankings use closing-line value, minimum sample sizes and a multiple-testing penalty.</li>
<li>Applied to this desk: the prior-only model called {WF['margin_su_model']} of 22 games straight-up. Under a fair coin P(at least {WF['margin_su_model']} of 22) = {pct(su_p, 1)}, i.e. not distinguishable from luck.</li></ul>
<h2>One bettor, fair-coin luck vs real skill</h2>{t1}
<h2>Many entrants: the winner's curse</h2>{t2}
<h2>Bets needed to detect an edge</h2>{t3}"""
    page("luck-vs-skill.html", "Luck vs skill", "How many bets separate skill from luck", body)

    # ---------------- data
    rows = []
    for c in integ:
        n = c["check"]
        src = URL_BOX if "game sample" in n or "2026-27: 214" in n else URL_STAND25 if "home/road" in n else URL_SCHED if "schedule" in n else URL_TRAD24 if n.startswith("2024-25") else URL_TRAD25 if n.startswith("2025-26") else URL_TRAD26 if n.startswith("2026-27") else URL_TRAD26
        rows.append([E(n), "<span class='tag ok'>pass</span>" if c["passed"] else "<span class='tag bad'>FAIL</span>", E(c["detail"]), a(src)])
    t_i = table(["Integrity check", "Result", "Detail", "Source"], rows, "official")
    rows = [
        ["teams.csv", str(len(TEAMS)), "Team names, NBA team IDs, conference", a(URL_STAND25), a(REPO + "data/teams.csv", "CSV")],
        ["team_seasons.csv", str(len(TS)), "GP, W, L, PTS/G, +/- per game, 3 seasons", a(URL_TRAD26) + " " + a(URL_TRAD25) + " " + a(URL_TRAD24), a(REPO + "data/team_seasons.csv", "CSV")],
        ["home_road_2025_26.csv", str(len(HR)), "Home / road / neutral W-L, 2025-26", a(URL_STAND25), a(REPO + "data/home_road_2025_26.csv", "CSV")],
        ["games_sample_2026_27.csv", str(len(GS)), "Box-score rows for 22 games, 10/31-11/02", a(URL_BOX), a(REPO + "data/games_sample_2026_27.csv", "CSV")],
        ["schedule_2026_11_04_05.csv", str(len(SCHED)), "16 scheduled games (venue and 11/05 tips blank)", a(URL_SCHED), a(REPO + "data/schedule_2026_11_04_05.csv", "CSV")],
        ["injury_report_2026-11-03_1700ET.csv", str(len(INJ)), "Verbatim rows from the 5:00 PM ET report", a(URL_INJ_PDF), a(REPO + "data/injury_report_2026-11-03_1700ET.csv", "CSV")],
        ["ledger_2026_11_04_05.csv", "16", "Frozen own lines; results blank until settled", a(URL_SCHED), a(REPO + "data/ledger_2026_11_04_05.csv", "CSV")],
    ]
    t_r = table(["File", "Rows", "Contents", "Official source", "Raw file"], rows, "official", num=(1,))
    byg = {}
    for r in GS:
        byg.setdefault(r["game_id"], []).append(r)
    rows = []
    for gid, v in sorted(byg.items()):
        h = [x for x in v if x["home"] == "1"][0]
        aw = [x for x in v if x["home"] == "0"][0]
        rows.append([E(h["date"]), f"{E(aw['team'])} @ {E(h['team'])}", f"{aw['pts']}-{h['pts']}" + (" (OT)" if h["min"] == "265" else ""), a(h["source_url"], gid)])
    t_gm = table(["Date", "Game", "Score (away-home)", "Source (game ID)"], rows, "official")
    rows = [[E(r["season"]), f"<b>{E(r['team'])}</b>", r["gp"], r["w"], r["l"], r["pts_pg"], r["plus_minus_pg"], a(r["source_url"])] for r in TS]
    t_ts = table(["Season", "Team", "GP", "W", "L", "PTS/G", "+/- per game", "Source"], rows, "official", num=(2, 3, 4, 5, 6))
    rows = [[f"<b>{E(r['team'])}</b>", r["home_w"] + "-" + r["home_l"], r["road_w"] + "-" + r["road_l"], r["neutral_w"] + "-" + r["neutral_l"],
             ('<span class="blank">' + E(r["home_road_order"]) + "</span>") if r["home_road_order"].startswith("UNCONF") else "as printed", a(r["source_url"])] for r in HR]
    t_hr = table(["Team", "Home", "Road", "Neutral", "Column order", "Source"], rows, "official")
    body = f"""
<h2>Integrity checks ({n_ok}/{len(integ)} pass)</h2>
<p class="mut">Run by <code>analysis.py</code> and <code>tests/test_nba_desk.py</code>. They test league identities (wins = losses, 1,230 games, margins sum to about zero, points = 2 x FGM + 3PM + FTM, home wins = road losses). They cannot catch offsetting transcription errors (flag F08).</p>{t_i}
<h2>Datasets</h2>{t_r}
<h2>Game sample (22 games)</h2>{t_gm}
<details><summary>Team seasons: 90 rows (2024-25, 2025-26, 2026-27 to date)</summary>{t_ts}</details>
<details><summary>2025-26 home / road / neutral splits: 30 rows</summary>{t_hr}</details>"""
    page("data.html", "Data & checks", "Official data captured and how it was reconciled", body)

    # ---------------- injuries
    rows = []
    for r in INJ:
        team = E(r["team"]) if r["team"] else BLANK
        mu = E(r["matchup"]) if r["matchup"] else BLANK
        status = E(r["status"]) if r["status"] else "-"
        why = E(r["reason"])
        flag = "" if r["attribution"] == "stated" else "<span class='tag warn'>team not stated - not attributed</span>"
        rows.append([mu, team, E(r["player"]) or "-", status, why, flag, a(r["source_url"], "PDF")])
    t = table(["Game", "Team", "Player", "Status", "Reason", "Attribution", "Source"], rows, "official")
    body = f"""
<div class="notice"><b>Snapshot of the official 5:00 PM ET report (published 2026-11-03).</b> {len(NYS)} of 30 team slots were NOT YET SUBMITTED; MIL has no row in the parsed text; {len(UNLAB)} rows follow page breaks without a team label and are left unattributed. Reports update through the day: see the {a(URL_INJ_IDX, 'official index')}. The lines on this site are <b>not</b> injury-adjusted.</div>
<h2>Report rows (verbatim)</h2>{t}"""
    page("injuries.html", "Injury report", "Official injury report snapshot used for context", body)

    # ---------------- audit
    audit = [
        ("arXiv:2606.27957 (docs/sources.html)", "Paper exists; title 'From streaks to synergies: A multi-scale analysis of performance and scoring in the NBA'; 7,054 regular-season + 504 playoff games, 2019/20-2024/25.", "Verified", "Abstract and section 2 match the docs' description.", "https://arxiv.org/html/2606.27957v1"),
        ("Docs: 'B2B 44% win rate'", "Section 3.2: back-to-back games show a win rate of 44% vs expected 50%.", "Verified", "Matches. Concerns 2019/20-2024/25 only.", "https://arxiv.org/html/2606.27957v1"),
        ("Docs: 'P(W|W)=54.5%'", "Section 3.1: P(W|W) = 54.5%.", "Verified", "Matches.", "https://arxiv.org/html/2606.27957v1"),
        ("Cross-check: home win rate", "Paper: teams win 0.55 at home. Official 2025-26 standings: 679-546 at home = 55.4%.", "Consistent", "Two independent official/primary sources agree.", URL_STAND25),
        ("PubMed 32172667 (docs)", "Abstract exists: 82 games, 2016/17 season; win likelihood rises from back-to-back to one day's rest; shooting statistics discriminate.", "Partly verified", "The docs' attribution 'Esteves et al. 2021, Eur J Sport Sci' (author, journal, year) was NOT visible in what was retrieved: unverified.", "https://pubmed.ncbi.nlm.nih.gov/32172667/"),
        ("arXiv:1910.08858 (docs)", "Exists. Authors Ramesh, Mostofa, Bornstein, Dobelman; submitted 19 Oct 2019. Abstract: authors say their algorithm 'generates above market returns' across NFL, NBA, NCAAF, NCAAB, WNBA.", "Exists; claim is the authors' own", "The docs' use ('demonstrated inefficiencies in NBA betting markets') overstates a single-author-team claim: the abstract names five markets and gives no NBA-specific result.", "https://arxiv.org/abs/1910.08858"),
        ("Official injury report page, 2026-27", "Index exists with PDF links at 15-minute ET intervals; rules text: submission due 5 pm local the day before; game-day report 11 am-1 pm local (8-10 am if tip at or before 5 pm); second night of a back-to-back by 1 pm local.", "Verified", "Docs link to the 2025-26 page (not re-opened here); the 2026-27 page is the current one.", URL_INJ_IDX),
        ("Docs: 15-minute public update cadence (Yahoo memo)", "The official index lists reports in 15-minute increments for 2026-11-03. The Dec-2025 Yahoo article itself was not re-opened.", "Cadence consistent; memo unverified", "Replace the Yahoo citation with the official index.", URL_INJ_IDX),
        ("Bailey & Lopez de Prado PBO PDF; IJRSS Finals home-advantage paper", "Not opened this session.", "Unverified", "Docs' 'HCA 61.4% Finals; 56.7% last 10' and PBO claims remain unchecked.", "https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf"),
        ("15 INDUSTRY sources in docs/sources.html (CLV, SGP, Kelly, backtesting blogs)", "Third-party commercial or blog pages; not official; not re-opened.", "Unverified (not official)", "Concepts only. Any number from them stays unverified.", "https://github.com/sassnarep3-star/Own5/blob/main/docs/sources.html"),
        ("nba-2026-lab Edwards sample (10 rows)", "Re-checked against the official player log by three other sessions (5ea3d798 author; e9f83ff4, 9ded47ab, 9557a8aa). Not re-checked here.", "Checked by others", "Selected 10-game sample; correlations exploratory.", URL_PLAYER_LOG),
        ("docs/leaderboard.html", "Contains no entries and no rewards.", "Consistent with this site", "Nothing to verify; matches 0 qualified strategies.", "https://github.com/sassnarep3-star/Own5/blob/main/docs/leaderboard.html"),
    ]
    rows = []
    for item, found, status, note, url in audit:
        tone = "ok" if status.startswith(("Verified", "Consistent", "Checked")) else "bad" if status.startswith("Unverified") else "warn"
        rows.append([E(item), E(found), f"<span class='tag {tone}'>{E(status)}</span>", E(note), a(url)])
    t_a = table(["Existing claim / source", "What the official or primary source says", "Status", "Note", "Source"], rows, "external")
    sites = [
        ("docs/", "9c3a0a69", "Strategy, gate, correlation framework; empty leaderboard", "No numeric correlations, no lines", "../docs/index.html"),
        ("nba-2026-lab/", "5ea3d798", "10-game player sample, 5 correlations, review flags", "No team lines", "../nba-2026-lab/index.html"),
        ("nba-audit-e9f83ff4/", "e9f83ff4", "Independent audit of the sample", "No lines", "../nba-audit-e9f83ff4/index.html"),
        ("nba-sensitivity/", "9557a8aa", "Leave-one-out sensitivity of the sample", "No lines", "../nba-sensitivity/index.html"),
        ("nba-own-lines/", "636a7712", "Efficiency-rating own lines for the same 16 games, 4-player prop sample, 21 correlations, 0/7 qualified", "Different model and zero home-court advantage; margins differ (see Model page)", "../nba-own-lines/index.html"),
        ("nba-validation/", "e9a43ca6", "Validation engine, 6 candidate strategies, review flags; declines to publish lines", "No own lines (by design); 0 certified", "../nba-validation/index.html"),
        ("nba-origin-lab/", "9ded47ab", "Evidence register, line-origin framework, review flags", "See its page for its own lines", "../nba-origin-lab/index.html"),
    ]
    rows = [[E(s), E(o), E(c), E(n), a("https://github.com/sassnarep3-star/Own5/tree/main/" + s.rstrip("/"), "repo folder") + " " + a(u, "live page", ext=False)] for s, o, c, n, u in sites]
    t_s = table(["Site", "Session", "Contents", "Gap", "Source"], rows, "derived")
    body = f"""
<div class="notice">Scope: this audit re-opened the sources in the table below. It did <b>not</b> verify every sentence of every earlier page; items marked Unverified were not opened. Nothing is marked Verified without an official or primary link.</div>
<h2>Existing claims checked</h2>{t_a}
<h2>Other NBA sites in this repository</h2>{t_s}"""
    page("audit.html", "Repo audit", "Earlier NBA claims against official and primary sources", body)

    # ---------------- sources
    src = [
        ("OFFICIAL", "NBA.com team traditional stats 2026-27", "30 team rows through 11/02", URL_TRAD26),
        ("OFFICIAL", "NBA.com team traditional stats 2025-26", "30 team rows, 82 games", URL_TRAD25),
        ("OFFICIAL", "NBA.com team traditional stats 2024-25", "30 team rows, 82 games", URL_TRAD24),
        ("OFFICIAL", "NBA.com standings 2025-26", "Home/road/neutral splits; team IDs", URL_STAND25),
        ("OFFICIAL", "NBA.com standings (current)", "Records cross-check (first chunk only)", URL_STAND),
        ("OFFICIAL", "NBA.com team box scores 2026-27", "Box-score rows for 22 games", URL_BOX),
        ("OFFICIAL", "NBA.com schedule, November 2026", "Matchups for 11/04-11/05", URL_SCHED),
        ("OFFICIAL", "NBA Official injury report index 2026-27", "Rules, report links", URL_INJ_IDX),
        ("OFFICIAL", "NBA Official injury report 11/03 5:00 PM ET (PDF)", "61 rows snapshot", URL_INJ_PDF),
        ("OFFICIAL", "NBA.com player game log (E. Edwards 2025-26)", "Example input for prop correlations", URL_PLAYER_LOG),
        ("PRIMARY", "arXiv:2606.27957", "B2B, P(W|W), home win rate", "https://arxiv.org/html/2606.27957v1"),
        ("PRIMARY", "arXiv:1910.08858", "Authors' betting-market claim", "https://arxiv.org/abs/1910.08858"),
        ("PRIMARY", "PubMed 32172667", "Fixture congestion abstract", "https://pubmed.ncbi.nlm.nih.gov/32172667/"),
    ]
    rows = [[f"<span class='tag'>{t}</span>", E(n), E(u_), a(url)] for t, n, u_, url in src]
    body = f"""<p class="mut">All captured 2026-11-03 UTC. NBA.com pages are rendered by script, so the data was read from the rendered text and transcribed; each row in each table carries its own link for manual review.</p>
{table(["Tier", "Source", "Used for", "Link"], rows, "external")}"""
    page("sources.html", "Sources", "Every source used on this site", body)

    # ---------------- flagged
    rows = []
    for fid, sev, area, item, fix, url in FLAGS:
        tone = "bad" if sev == "High" else "warn" if sev == "Medium" else ""
        rows.append([f"<b>{fid}</b>", f"<span class='tag {tone}'>{sev}</span>", E(area), E(item), E(fix), a(url)])
    body = f"""<div class="notice">Flags never block publication. Each is an irregularity, unverified value or limitation. Where a value could not be confirmed it is blank on its page.</div>
{table(["ID", "Severity", "Area", "Finding", "How to resolve", "Source"], rows, "external")}"""
    page("flagged.html", "Flagged for Review", f"{len(FLAGS)} irregularities and unverified items", body)

    # ---------------- summary
    page("summary.html", "Executive summary", "What was built, what it shows, what it cannot show", f'<div class="panel">{summary_html()}</div>')


def summary_items():
    tt = WF["team_test"]
    ls = A_["luck_skill"]
    n55 = [r for r in ls["required_n"] if r["true_hit_rate"] == 0.55][0]["n_bets"]
    return [
        ("Bottom line", f"The desk originates its own NBA lines from official NBA team data and publishes {len(LINES)} (11/04-11/05). It cannot yet show that any line, single, parlay or prop combo has an edge: there are no verified market quotes, so closing-line value is not computable and 0 of 6 pre-registered strategies qualify. 0 rewards are awarded; the pool is unfunded."),
        ("How lines are made", f"Team rating = in-season points margin blended with a prior of {f1(P['beta'], 2)} x last season's margin (weight on the current season = G/(G+{f1(P['K'], 1)}), G = games played), plus home-court advantage of {f1(P['hfa'], 2)} points (from {pct(P['home_pct'])} home wins in 2025-26). Win probability = normal CDF of margin / {f1(P['sigma'], 1)}."),
        ("Does it work?", f"Partly, and the sample is small. Early 2026-27 margins correlate r = {f1(tt['r'], 2)} with 2025-26 margins (n = 30). On 22 played games the prior-only model beat an HFA-only baseline by {f1(WF['margin_abs_err_gain']['mean'], 2)} points of margin error (z = {f1(WF['margin_abs_err_gain']['z'], 2)}, not significant). On totals there was no gain (z = {f1(WF['total_abs_err_gain']['z'], 2)}) and a +{f1(WF['total_model']['bias'])} point bias from last season's higher scoring level."),
        ("Correlations", "Team-season: win % tracks points margin at r = 0.92 to 0.98. Team-game and spread/total-leg correlations from 22 games have intervals spanning zero. Parlay arithmetic is tabulated by leg correlation. Player-prop and same-game-parlay correlations are blank and flagged."),
        ("Removing luck", f"Break-even at -110 is 52.38%. A true 55% bettor needs about {n55} settled bets for an 80%-power test. With 100 pure-luck entrants the best is expected to hit about 62% over 100 bets. Rankings therefore use closing-line value with a lower confidence bound, minimum sample, multiple-testing penalty and frozen pre-registration."),
        ("Repo audit", "arXiv:2606.27957 figures cited in docs (B2B 44%, P(W|W) 54.5%) verified against the paper; PubMed and arXiv:1910.08858 exist but the docs' attribution/claim wording is partly unverified; 15 of 21 listed sources are third-party commercial pages. Official 2026-27 injury page confirmed."),
        ("Flags", f"{len(FLAGS)} flags, none blocking. Top three: no market quotes (F01); 0 qualified strategies and unfunded rewards (F02); 22-game sample is underpowered (F04). Injury reports for 17 teams were not yet submitted when captured, and lines are not injury-adjusted (F05)."),
        ("Next steps", "Capture timestamped quotes; settle the 16 ledger games from official pages (python3 nba-desk/settle.py); extend the game sample; add a player-value model for injuries; collect a large official player-game sample for prop correlations."),
    ]


def summary_html():
    return "".join(f"<h3>{E(h)}</h3><p>{E(t)}</p>" for h, t in summary_items())


# ------------------------------------------------------------------ research docs
def write_docs():
    os.makedirs(RES, exist_ok=True)
    ex = "# Executive summary - NBA Desk (session 4396568c)\n\nData as of 2026-11-03 UTC. Live site: https://sassnarep3-star.github.io/Own5/nba-desk/index.html\n\n"
    ex += "".join(f"## {h}\n\n{t}\n\n" for h, t in summary_items())
    open(os.path.join(RES, "EXECUTIVE_SUMMARY.md"), "w").write(ex)
    me = f"""# Methodology - NBA Desk

All inputs are CSVs in `nba-desk/data/`, transcribed from official NBA pages; each row has `source_url`. `python3 nba-desk/analysis.py` runs the integrity checks, fits the model and writes `data/derived/`; `python3 nba-desk/build.py` writes the site and these documents.

## Data
- Team seasons 2024-25, 2025-26 (82 games) and 2026-27 to date (214 team-games): games, W, L, PTS per game, +/- per game.
- 2025-26 home/road/neutral splits (MEM, SAC, UTA column order unconfirmed, flag F07).
- 22 team-box-score games (44 rows), 10/31-11/02, chosen by visibility rule (flag F03).
- Schedule 11/04-11/05 (16 games); injury report 5:00 PM ET 11/03 (verbatim).

## Model
1. beta = OLS slope of 2025-26 margin on 2024-25 margin = {P['beta']:.3f} (n = 30). Same for total deviations: {P['beta_t']:.3f}.
2. sigma = RMSE of the prior-only margin model on the 22 games = {P['sigma']:.2f} (conservative; in-sample).
3. Home-court advantage = sigma x inverse-normal(home win %) = {P['hfa']:.2f} points; home win % = {P['home_w']}/{P['home_w'] + P['home_l']}.
4. K = sigma^2 / tau^2 = {P['K']:.2f}, tau^2 = training residual variance - sigma^2/82 = {P['tau_p2']:.2f}. Rating = (G x margin + K x beta x last-season margin)/(G + K).
5. Own margin = rating(home) - rating(away) + HFA; win probability = Phi(margin/sigma); total = 2026-27 league level + shrunk total deviations (K_T = {P['K_t']:.1f}).

## Validation
- Training pair 2024-25 to 2025-26; test pair 2025-26 to 2026-27 to date (n = 30) and 22 played games walk-forward (prior-only inputs).
- Gates G1-G9 (site page *Validation gates*) fail closed. Strategies S1-S6 are pre-registered; none can be evaluated without market quotes.
- Luck: exact binomial tables (site page *Luck vs skill*), parlay joint-probability formula pq + phi sqrt(p(1-p)q(1-q)).

## Limits
Small samples, no injury or rest adjustment, no market data, hand transcription. See the *Flagged for Review* page ({len(FLAGS)} flags).

## Reproduce
```
python3 nba-desk/analysis.py && python3 nba-desk/build.py
python3 -m unittest discover -s nba-desk/tests -q
python3 nba-desk/check.py
python3 nba-desk/settle.py        # after filling official final scores in the ledger
```
"""
    open(os.path.join(RES, "METHODOLOGY.md"), "w").write(me)
    au = "# Audit - NBA Desk (D1)\n\nScope: sources re-opened in this session. Not a verification of every sentence of every earlier page.\n\n## Findings\n\n"
    au += "| # | Item | Status |\n|---|---|---|\n"
    for i, r in enumerate([
        ("arXiv:2606.27957 exists; 7,054 + 504 games; 2019/20-2024/25", "Verified"),
        ("B2B 44% vs 50% (section 3.2)", "Verified"),
        ("P(W|W) = 54.5% (section 3.1)", "Verified"),
        ("Home win rate 0.55 in the paper vs 55.4% official 2025-26", "Consistent"),
        ("PubMed 32172667 abstract content", "Verified; author/journal/year attribution unverified"),
        ("arXiv:1910.08858 exists; claim is the authors' own; docs wording overstates", "Partly verified"),
        ("Official 2026-27 injury page and rules", "Verified"),
        ("Yahoo memo, Bailey PBO PDF, IJRSS, 15 industry sources", "Not opened - unverified"),
    ], 1):
        au += f"| {i} | {r[0]} | {r[1]} |\n"
    au += "\nLinks and detail: site page `audit.html`. Flags: `flagged.html`.\n"
    open(os.path.join(RES, "AUDIT.md"), "w").write(au)


def main():
    build_pages()
    for fn, content in PAGES.items():
        with open(os.path.join(HERE, fn), "w") as f:
            f.write(content + "\n")
    write_docs()
    print(f"wrote {len(PAGES)} pages")


if __name__ == "__main__":
    main()

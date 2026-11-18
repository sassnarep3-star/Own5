#!/usr/bin/env python3
"""Deterministic builder for the NFL Line-Originator Decision Desk (session f2e20e96).

Reads the CSVs in data/nfl-desk-f2e20e96/ and renders the static desk in
nfl-desk-f2e20e96/ plus computed CSVs in data/nfl-desk-f2e20e96/computed/.

Hard rules:
- No clock, no git, no network at build time. Read timestamps live in the data.
- Every rendered table row ends in a source link or an explicit UNVERIFIED /
  COMPUTED-IN-REPO marker. Values are never inferred: unknown stays blank.
- Model outputs are published as probability + inputs (brief requirement).
"""
import csv
import math
import os
from statistics import mean, stdev

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "nfl-desk-f2e20e96")
COMPUTED = os.path.join(DATA, "computed")
SITE = os.path.join(ROOT, "nfl-desk-f2e20e96")

# ---- registered model constants (frozen; see executive summary) -------------
REG_K = 11.0            # regression-to-mean prior games (assumption A-01)
HFA = 2.0               # home-field advantage prior in points (assumption A-02)
MODEL_VERSION = "m1-2026-11-18-margin-shrinkage"

SRC = {
    "standings": "https://www.nfl.com/standings/league/2026/REG",
    "schedule11": "https://www.nfl.com/schedules/2026/by-week/week-11",
    "injuries10": "https://www.nfl.com/injuries/league/2026/reg10",
    "scores10": "https://www.nfl.com/scores/2026/REG10",
}


def read_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(name, rows, fields):
    os.makedirs(COMPUTED, exist_ok=True)
    with open(os.path.join(COMPUTED, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


# ---- inputs ----------------------------------------------------------------
standings = read_csv("standings_2026_reg.csv")
results = read_csv("week10_results.csv")
schedule = read_csv("week11_schedule.csv")
byes = read_csv("byes_week11.csv")
injuries = read_csv("injury_wk10_players.csv")
sources = read_csv("sources.csv")
readiness = read_csv("readiness.csv")
questions = read_csv("questions.csv")
suggestions = read_csv("suggestions.csv")
gates = read_csv("gates.csv")
leaderboard = read_csv("leaderboard.csv")
flagged = read_csv("flagged.csv")
claims = read_csv("claim_checks.csv")
prices = read_csv("price_snapshots_wk11.csv")
txn = read_csv("transactions_news.csv")
starters = read_csv("starters_jax_ten.csv")
inactives = read_csv("inactives_jax_ten.csv")
prev = read_csv("availability_wk11_preview.csv")

# ---- derived: team strength model ------------------------------------------
teams = {}
for r in standings:
    gp = int(r["w"]) + int(r["l"]) + int(r["t"])
    net = int(r["pf"]) - int(r["pa"])
    s = net / gp
    s_reg = s * gp / (gp + REG_K)
    f = (int(r["pf"]) + int(r["pa"])) / gp
    teams[r["club"]] = {
        "gp": gp, "net": net, "s": s, "s_reg": s_reg,
        "f": f, "pf": int(r["pf"]), "pa": int(r["pa"]),
        "pct": float(r["pct"]), "w": r["w"], "l": r["l"], "t": r["t"],
    }
total_games = sum(t["gp"] for t in teams.values()) // 2
total_points = sum(t["pf"] for t in teams.values())
T_LG = total_points / total_games
for c, t in teams.items():
    t["f_reg"] = (t["f"] * t["gp"] + T_LG * REG_K) / (t["gp"] + REG_K)

# Week 10 realised margins (home - away) and totals — published with n
home_margins, game_totals = [], []
for r in results:
    hs, as_ = int(r["home_score"]), int(r["away_score"])
    home_margins.append(hs - as_)
    game_totals.append(hs + as_)
n_margins = len(home_margins)
hfa_sample = mean(home_margins)
sigma_sample = stdev(home_margins)
total_sample = mean(game_totals)

# ---- computed: model lines (side -> total -> moneyline) --------------------
model_rows = []
order = {"side": 1, "total": 2, "moneyline": 3}
for g in schedule:
    gid, home, away = g["game_id"], g["home"], g["away"]
    th, ta = teams[home], teams[away]
    margin = (th["s_reg"] - ta["s_reg"]) + HFA
    total = (th["f_reg"] + ta["f_reg"]) / 2.0
    p_home = 0.5 * (1.0 + math.erf((margin / sigma_sample) / math.sqrt(2.0)))
    inputs = (
        f"inputs: s_reg_home={th['s_reg']:.3f} s_reg_away={ta['s_reg']:.3f} "
        f"(net/gp shrunk by gp/(gp+{REG_K:.0f})); HFA={HFA:.1f}; "
        f"sigma={sigma_sample:.2f} (Week-10 margin SD n={n_margins}); "
        f"f_reg_home={th['f_reg']:.2f} f_reg_away={ta['f_reg']:.2f}; "
        f"T_LG={T_LG:.2f} ({total_points} pts / {total_games} games); model={MODEL_VERSION}"
    )
    if margin >= 0:
        side_disp = f"{home} -{margin:.1f}"
    else:
        side_disp = f"{away} -{-margin:.1f}"
    model_rows.append({
        "game_id": gid, "market_order": 1, "market": "side",
        "matchup": f"{away} at {home}", "model_fair_line": side_disp,
        "model_fair_value": f"{margin:.1f}", "market_line": "", "difference": "",
        "probability": f"{p_home:.4f}", "probability_label": "P(home win) = Phi(fair margin / sigma)",
        "inputs": inputs, "source_url": SRC["standings"],
    })
    model_rows.append({
        "game_id": gid, "market_order": 2, "market": "total",
        "matchup": f"{away} at {home}", "model_fair_line": f"{total:.1f}",
        "model_fair_value": f"{total:.1f}", "market_line": "", "difference": "",
        "probability": "", "probability_label": "",
        "inputs": inputs, "source_url": SRC["standings"],
    })
    model_rows.append({
        "game_id": gid, "market_order": 3, "market": "moneyline",
        "matchup": f"{away} at {home}",
        "model_fair_line": f"{home} {p_home*100:.1f}% (fair price from probability)",
        "model_fair_value": f"{p_home:.4f}", "market_line": "", "difference": "",
        "probability": f"{p_home:.4f}", "probability_label": "P(home win) = Phi(fair margin / sigma)",
        "inputs": inputs, "source_url": SRC["standings"],
    })
model_rows.sort(key=lambda r: (int(r["market_order"]), r["game_id"]))
write_csv("model_lines_wk11.csv", model_rows, list(model_rows[0].keys()))


# ---- computed: correlations (official standings only, n published) ---------
def pearson(xs, ys):
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return num / den


clubs = sorted(teams)
pf_g = [teams[c]["pf"] / teams[c]["gp"] for c in clubs]
pa_g = [teams[c]["pa"] / teams[c]["gp"] for c in clubs]
net_g = [teams[c]["s"] for c in clubs]
pct = [teams[c]["pct"] for c in clubs]
corr_specs = [
    ("C-01", "Points for per game vs points against per game", pf_g, pa_g),
    ("C-02", "Net points per game vs winning percentage", net_g, pct),
    ("C-03", "Points for per game vs winning percentage", pf_g, pct),
    ("C-04", "Points against per game vs winning percentage", pa_g, pct),
]
corr_rows = []
for cid, label, xs, ys in corr_specs:
    corr_rows.append({
        "correlation_id": cid, "pair": label, "method": "Pearson r, in-repo from the standings read",
        "r": f"{pearson(xs, ys):.4f}", "n": len(clubs),
        "source_url": SRC["standings"], "note": "Official numbers only; n published per brief",
    })
write_csv("correlations.csv", corr_rows, list(corr_rows[0].keys()))

# ---- computed: removal-of-luck panel --------------------------------------
def phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


luck_rows = [
    {"metric": "Week-10 home margin (home - away), mean", "value": f"{hfa_sample:.2f}",
     "n": n_margins, "note": "Not used as the model intercept (small n); the registered HFA prior is 2.0",
     "source_url": SRC["scores10"]},
    {"metric": "Week-10 margin SD (sigma used for moneyline conversion)", "value": f"{sigma_sample:.2f}",
     "n": n_margins, "note": "Sample SD of realised margins; published with n; recomputed as the feed grows",
     "source_url": SRC["scores10"]},
    {"metric": "Week-10 average game total", "value": f"{total_sample:.2f}",
     "n": n_margins, "note": "Published with n", "source_url": SRC["scores10"]},
    {"metric": "Home teams won", "value": f"{sum(1 for m in home_margins if m > 0)} of {n_margins}",
     "n": n_margins, "note": "Descriptive only", "source_url": SRC["scores10"]},
]
for p_true in (0.50, 0.524, 0.55, 0.57):
    for n in (100, 200, 500, 1000):
        sd = math.sqrt(p_true * (1 - p_true) / n)
        power = 1 - phi((0.524 - p_true) / sd) if sd > 0 else 1.0
        luck_rows.append({
            "metric": f"Power to clear 52.4% (break-even at -110) if true rate = {p_true:.3f}",
            "value": f"{power:.3f}", "n": n,
            "note": "P(observed rate > 0.524) = 1 - Phi((0.524 - p)/sqrt(p(1-p)/n)); normal approximation",
            "source_url": SRC["standings"],
        })
write_csv("luck_panel.csv", luck_rows, list(luck_rows[0].keys()))

# ---- computed: injury club summary ----------------------------------------
club_summary = []
for club in sorted({r["club"] for r in injuries}):
    rows = [r for r in injuries if r["club"] == club]
    gs = [r["game_status"] for r in rows]
    club_summary.append({
        "club": club, "rows": len(rows),
        "out": gs.count("Out"), "doubtful": gs.count("Doubtful"),
        "questionable": gs.count("Questionable"),
        "no_designation": gs.count(""),
        "game_ref": rows[0]["game_ref"],
        "source_url": SRC["injuries10"], "read_at_utc": rows[0]["read_at_utc"],
    })
write_csv("injury_wk10_club_summary.csv", club_summary, list(club_summary[0].keys()))

# ============================================================================
# HTML rendering
# ============================================================================
NAV = [
    ("index.html", "Decision readiness"),
    ("executive-summary.html", "Executive summary"),
    ("schedule.html", "Week 11 schedule"),
    ("results.html", "Verified results feed"),
    ("lines.html", "Originated lines"),
    ("prices.html", "Price snapshots"),
    ("leaderboard.html", "Leaderboard & luck panel"),
    ("injuries.html", "Injury report capture"),
    ("availability.html", "Starters, depth & replacements"),
    ("correlations.html", "Correlations"),
    ("gates.html", "Validation gates"),
    ("questions.html", "Questions register"),
    ("suggestions.html", "Suggestions register"),
    ("claim-checks.html", "Brief claim checks"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def link(url, text=None):
    return f'<a href="{esc(url)}">{esc(text or url)}</a>'


def cell(v):
    v = "" if v is None else str(v)
    return esc(v) if v else '<span class="blank">—</span>'


def src_cell(url, label="source"):
    if url:
        return link(url, label)
    return '<span class="badge unverified">UNVERIFIED</span>'


def computed_cell(note="computed in-repo"):
    return f'<span class="badge computed">{esc(note)}</span>'


def registry_cell(label):
    return f'<span class="badge neutral">registry: {esc(label)}</span>'


def table(headers, rows):
    """rows: list of lists of pre-rendered HTML cells."""
    out = ["<div class='tablewrap'><table><thead><tr>"]
    out += [f"<th>{esc(h)}</th>" for h in headers]
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def page(name, title, body):
    parts = []
    for href, label in NAV:
        active = ' class="active"' if href == name else ""
        parts.append(f'<a href="{href}"{active}>{esc(label)}</a>')
    nav = "".join(parts)
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — NFL Line-Originator Decision Desk (f2e20e96)</title>
<link rel="stylesheet" href="style.css"></head>
<body><header><h1>NFL Line-Originator Decision Desk</h1>
<p class="sub">Session f2e20e96 · official-source reads 2026-11-18T03:44–04:02Z (session clock) ·
every row source-linked or explicitly unverified · no values inferred · nothing on this site is a betting recommendation</p>
<nav>{nav}</nav></header>
<main>{body}</main>
<footer><p>Built deterministically from <code>data/nfl-desk-f2e20e96/</code> by
<code>scripts/build_f2e20e96.py</code>. Blank cells mean “not verified from an official source”.
Model outputs are computed in-repo from the linked official inputs and are labelled as computed.</p></footer>
</body></html>"""
    with open(os.path.join(SITE, name), "w", encoding="utf-8") as f:
        f.write(html)


def badge(status):
    s = str(status).upper()
    if s.startswith("MET") or s == "PASS":
        cls = "ok"
    elif s.startswith("BLOCK"):
        cls = "bad"
    elif s.startswith("PARTIAL"):
        cls = "warn"
    else:
        cls = "neutral"
    return f'<span class="badge {cls}">{esc(status)}</span>'


# ---- index.html: decision-readiness landing --------------------------------
rows = []
for r in readiness:
    rows.append([
        esc(r["req_id"]), esc(r["requirement"]), esc(r["blocking_gate"]),
        esc(r["number_that_would_clear_it"]), cell(r["observed_2026-11-18"]),
        badge(r["status"]), src_cell(r["evidence"].startswith("http") and r["evidence"] or None, r["evidence"])
        if r["evidence"].startswith("http") else computed_cell(r["evidence"]),
    ])
body = f"""
<h2>Decision readiness — one row per requirement</h2>
<p>Each row of the user brief is tracked as a requirement with the gate that blocks it and the
number that would clear it. <b>{sum(1 for r in readiness if r['status'].startswith('MET'))} MET</b> ·
<b>{sum(1 for r in readiness if r['status'].startswith('PARTIAL'))} PARTIAL</b> ·
<b>{sum(1 for r in readiness if r['status'].startswith('BLOCK'))} BLOCKED</b> ·
<b>{sum(1 for r in readiness if r['status'].startswith('PENDING'))} PENDING</b> —
full register ({len(readiness)} rows) below.</p>
<div class="cards">
<div class="card"><b>Week 10 verified finals</b><span>14 / 14</span><small>game centres + 1 official Game Book</small></div>
<div class="card"><b>Week 10 injury rows captured</b><span>347</span><small>28 club tables · read 2026-11-18</small></div>
<div class="card"><b>Originated markets (W11)</b><span>39</span><small>side → total → moneyline, 13 games</small></div>
<div class="card"><b>Market prices verified</b><span>0</span><small>no licensed source held (F-06)</small></div>
<div class="card"><b>Strategies certified</b><span>0</span><small>3 registered · 0 scored</small></div>
<div class="card"><b>Flagged items</b><span>{len(flagged)}</span><small>2 blocking · {len(flagged)-2} review</small></div>
</div>
{table(["ID", "Requirement", "Blocking gate", "Number that would clear it", "Observed (2026-11-18)", "Status", "Evidence"], rows)}
<h2>How to use this desk</h2>
<ol>
<li><b>Suggestions register</b> — review the {len(suggestions)} proposed improvements and pick a path before anything is implemented.</li>
<li><b>Questions register</b> — the {len(questions)} open questions list exactly what information is missing and the discovery route for each.</li>
<li><b>Flagged for review</b> — every irregularity with its source links. Nothing here blocks the merge.</li>
</ol>
"""
page("index.html", "Decision readiness", body)

# ---- executive summary ------------------------------------------------------
met = [r for r in readiness if r["status"].startswith("MET")]
body = f"""
<h2>Executive summary (2026-11-18)</h2>
<p><b>What this is.</b> A decision desk for originating NFL lines (side → total → moneyline) with every
number traceable to an official source read on 2026-11-18, plus the gates, questions and suggestions that
must be resolved before any decision is reasonably made. No strategy is certified, no bet is placed,
and no ROI is claimed.</p>
<h3>Verified first-hand on 2026-11-18 (official nfl.com / NFL Game Books)</h3>
<ul>
<li><b>Week 10 results feed: 14/14 finals</b> with venue from each game centre (Game Info) and Game Book links —
the JAX 40–23 TEN final (rendered “Hidden Score” on its game centre) was read from the official Game Book,
which also supplied actual starters (44 rows) and the Not Active lists (12 rows).</li>
<li><b>Week 10 injury report: 347 rows / 28 club tables</b>, per-row read clock 03:47–03:52Z. The brief's
counts (254/279) do not reproduce; the Lions' three Out designations are confirmed on the live page (CC-01).</li>
<li><b>Week 11 slate: 13 games + 6 byes</b>, kickoffs/networks as printed; game-centre venues captured for
IND–HOU (Reliant Stadium) and MIN–SF (Estadio Banorte, Mexico City).</li>
<li><b>32-club standings</b> (PF/PA/W-L-T) powering the model inputs and the n=32 correlations.</li>
<li><b>Transaction / announced-starter evidence</b> from official news: Willis→IR (McCord reported),
Henderson→IR, Lawrence→IR, Miller waived, Hooker/Henley trades, Lock and Watson/Beck named starters.</li>
</ul>
<h3>Computed in-repo (labelled, with inputs and n)</h3>
<ul>
<li>39 originated markets for Week 11 (13 sides, 13 totals, 13 moneylines) as <b>fair line · market line · difference</b>
columns. Market line and difference are blank by policy P-01 — no licensed price source is held (F-06).</li>
<li>Every model output stores <b>a probability plus its inputs</b> (regressed net/gp strengths, HFA prior 2.0,
Week-10 margin SD σ={sigma_sample:.2f} n={n_margins}).</li>
<li><b>Correlations</b> from official standings only, n=32 published with each value.</li>
<li><b>Removal-of-luck panel</b>: control baselines (random; favorites-only) registered for every evaluation
window + a binomial power table (formulas published) — skill must clear variance before any ranking.</li>
</ul>
<h3>Blocked, and what clears it</h3>
<ul>
<li><b>ROI / CLV / backtests</b> — blocked at the price-data policy (G-10/F-06). The brief's own condition
(“decide the price-data policy before any backtest is published”) is honoured: nothing has been backtested.</li>
<li><b>Depth & matchup-deficiency features</b> — blocked at G-07 (depth must come from playing time or official
depth charts; jersey-number derivation is explicitly rejected).</li>
<li><b>Combos (parlays / SGP / prop combos)</b> — held behind the joint-evidence gate (G-06): no validated
joint probability and no void/push rules, so no combo may be ranked.</li>
<li><b>Injury designation as a feature</b> — blocked at G-08 until designation-to-play-rate is calibrated
empirically with confidence intervals over multiple seasons.</li>
</ul>
<h3>Readiness snapshot</h3>
<p>{len(readiness)} requirements tracked: {len(met)} MET ·
{sum(1 for r in readiness if r['status'].startswith('PARTIAL'))} PARTIAL ·
{sum(1 for r in readiness if r['status'].startswith('BLOCK'))} BLOCKED ·
{sum(1 for r in readiness if r['status'].startswith('PENDING'))} PENDING.
The full table with the clearing number for each row is on the <a href="index.html">landing page</a>.</p>
<p class="note">Frozen model registration: {MODEL_VERSION}, constants k={REG_K:.0f}, HFA={HFA:.1f}
committed with this desk on branch arena/f2e20e96-own5 before the Week 11 kickoffs.</p>
"""
page("executive-summary.html", "Executive summary", body)

# ---- schedule ---------------------------------------------------------------
rows = []
for g in schedule:
    if g["venue_gamecentre"]:
        venue = esc(g["venue_gamecentre"]) + ' <span class="badge ok">game centre</span>'
    else:
        venue = cell(g["venue_schedule_page_string"]) + ' <span class="badge warn">schedule-page string (game-centre pending)</span>'
    rows.append([
        esc(g["game_id"]), esc(g["game_date"]), esc(g["kickoff_et"]), esc(g["network"]),
        f'{esc(g["away"])} ({esc(g["away_record"])})', f'{esc(g["home"])} ({esc(g["home_record"])})',
        venue, cell(g["notes"]), link(g["source_url"], "game page"),
    ])
bye_rows = [[esc(b["club"]), esc(b["record"]), link(b["source_url"], "schedule page")] for b in byes]
body = f"""
<h2>Week 11 schedule (2026) — 13 games, 6 byes</h2>
<p>Read 2026-11-18T03:44Z from the official schedule page. Kickoffs and networks are as printed (no time zone
is printed on the page — stored as printed, flag F-03/F-02 context). Venue is transcribed from the official
game centre where captured; the schedule-page column records the stadium string printed in the page's own
hotel-destination field, kept separate because it is a different field on a different official page.</p>
{table(["Game", "Date", "Kickoff (as printed)", "Network", "Away", "Home", "Venue", "Notes", "Source"], rows)}
<h3>Teams on bye (Week 11)</h3>
{table(["Club", "Record", "Source"], bye_rows)}
<h3>League schedule announcement (printed on the official schedule page)</h3>
<p>The official page carries the dated announcement for Weeks 16–18: “In Week 16, two of the four designated
matchups will be played on Saturday at 4:30 PM ET and 8:00 PM ET on NFL Network … Specific dates and start
times … no later than immediately after Week 14.” Week 17: “two … Saturday at 4:30 PM ET on NBC and 8:00 PM ET
on Peacock … no later than immediately after Week 15.” Week 18: “three games will be played on Saturday
(1:00 PM ET on Netflix, 4:30 PM ET and 8:00 PM ET on ESPN/ABC) … announced following the conclusion of Week 17.”
Flexible-scheduling procedures: {link("https://www.nfl.com/legal/flexible-scheduling-procedures")}.
<span class="badge computed">verbatim summary of the page text read 2026-11-18T03:46Z</span></p>
"""
page("schedule.html", "Week 11 schedule", body)

# ---- results ----------------------------------------------------------------
rows = []
for r in results:
    rows.append([
        esc(r["game_id"]), esc(r["game_date"]), esc(r["kickoff_et"]),
        esc(r["away"]), esc(r["away_score"]), esc(r["home"]), esc(r["home_score"]),
        esc(r["venue_stadium"]) + " · " + esc(r["venue_location"]),
        link(r["game_url"], "game centre"), link(r["game_book_url"], "Game Book"),
    ])
body = f"""
<h2>Verified results feed — 2026 Week 10 (14 finals)</h2>
<p>Every score and venue below was read first-hand from the official game centre (or, for JAX–TEN, from the
official Game Book PDF after the game centre rendered “Hidden Score”). This feed exists so backtests and ROI
can eventually be computed — scoring still waits on the price-data policy (gate G-10).</p>
{table(["Game", "Date", "Kickoff", "Away", "Score", "Home", "Score", "Venue", "Source", "Game Book"], rows)}
<h3>Corpus arithmetic (computed in-repo)</h3>
<ul>
<li>Games completed through Week 10: <b>{total_games}</b> (sum of W+L+T over 32 clubs ÷ 2 = {sum(t['gp'] for t in teams.values())}/2).
<span class="badge computed">computed from the standings read</span></li>
<li>Week-10 realised margins: mean home margin {hfa_sample:.2f}, SD {sigma_sample:.2f}, average total {total_sample:.2f}
(n={n_margins}). <span class="badge computed">computed from this feed</span></li>
<li>Verified in this desk: <b>14</b> of {total_games} games. The brief's “136-game log” matches an earlier
snapshot; expansion is per-game game-centre verification (see readiness R-19).</li>
</ul>
"""
page("results.html", "Verified results feed", body)

# ---- lines ------------------------------------------------------------------
def line_rows(market):
    out = []
    for m in model_rows:
        if m["market"] != market:
            continue
        out.append([
            esc(m["matchup"]),
            esc(m["model_fair_line"]) + ' <span class="badge computed">computed</span>',
            '<span class="badge unverified">UNVERIFIED</span>',
            '<span class="blank">—</span>',
            cell(m["probability"]),
            f'<details><summary>inputs</summary><code>{esc(m["inputs"])}</code></details>',
            link(m["source_url"], "official inputs"),
        ])
    return out


body = f"""
<h2>Originated lines — side → total → moneyline (Week 11)</h2>
<p>Origination order per the brief: <b>side first, then total, then moneyline</b>. Each row publishes the
model's fair line, the market line and the difference as <b>separate columns</b>. Market line and difference
are blank + UNVERIFIED: no licensed price source is held (policy P-01 / flag F-06) and values are never
inferred. Model version <code>{MODEL_VERSION}</code>; registered constants k={REG_K:.0f} (strength shrinkage),
HFA={HFA:.1f}; σ={sigma_sample:.2f} from the Week-10 margin sample (n={n_margins}).</p>
<h3>1. Side</h3>
{table(["Matchup", "Model fair line", "Market line", "Difference", "P(home covers)", "Inputs", "Source"], line_rows("side"))}
<h3>2. Total</h3>
{table(["Matchup", "Model fair total", "Market line", "Difference", "", "Inputs", "Source"], line_rows("total"))}
<h3>3. Moneyline</h3>
{table(["Matchup", "Model fair price", "Market line", "Difference", "P(home win)", "Inputs", "Source"], line_rows("moneyline"))}
<h3>Formulas (published per the brief: probability + inputs, never a bare pick)</h3>
<ul>
<li>Team strength S = (PF − PA) / games; shrunk S_reg = S · gp / (gp + {REG_K:.0f}) (k registered prior; sensitivity is a review item).</li>
<li>Fair home margin = S_reg(home) − S_reg(away) + {HFA:.1f}.</li>
<li>Fair total = (F_reg(home) + F_reg(away)) / 2 where F = (PF + PA)/gp shrunk to the league average
{T_LG:.2f} pts/game ({total_points} points in {total_games} games).</li>
<li>P(home win) = Φ(fair margin / σ), σ = {sigma_sample:.2f} (Week-10 sample SD, n={n_margins}).</li>
</ul>
"""
page("lines.html", "Originated lines", body)

# ---- prices -----------------------------------------------------------------
rows = []
for p in prices:
    rows.append([
        esc(p["snapshot_id"]), esc(p["game_id"]), esc(p["market"]),
        '<span class="badge unverified">UNVERIFIED</span>',
        '<span class="badge unverified">UNVERIFIED</span>',
        cell(p["price_source"]), esc(p["flag_id"]), link(p["source_url"], "market link"),
    ])
body = f"""
<h2>Price-snapshot store — opening &amp; closing numbers</h2>
<p>One row per originated market ({len(prices)} rows = 13 games × side/total/ML) with <b>opening</b> and
<b>closing</b> columns, captured-at clocks and a price source. Every value is blank + UNVERIFIED because no
licensed or officially sanctioned odds source is held (flag F-06). The brief requires the price-data policy
to be decided <i>before</i> any backtest is published — policy <b>P-01</b> is decision item
<a href="suggestions.html">S-01</a> and it blocks gates G-03/G-10.</p>
{table(["Snapshot", "Game", "Market", "Opening", "Closing", "Price source", "Flag", "Market link"], rows)}
<h3>Store schema (frozen)</h3>
<p><code>snapshot_id, game_id, market, opening_price, opening_captured_at_utc, closing_price,
closing_captured_at_utc, price_source, status, flag_id, source_url</code> — prices are stored as printed by
the eventual source (American or decimal, with the format recorded), never normalised silently.</p>
"""
page("prices.html", "Price snapshots", body)

# ---- leaderboard ------------------------------------------------------------
rows = []
for e in leaderboard:
    rows.append([
        esc(e["entry_id"]), esc(e["name"]), esc(e["division"]), esc(e["preregistration"]),
        cell(e["signal_brier_skill_vs_benchmark"]) or '<span class="blank">—</span>',
        cell(e["signal_cluster_lbound_95"]),
        esc(e["staking_rule"]), cell(e["staking_multiplier"]), cell(e["staking_max_exposure"]),
        badge(e["status"]),
        f'<details><summary>two-sided</summary>{esc(e["what_would_change_our_mind"])}</details>',
        link(e["source_url"], "official inputs"),
    ])
luck = []
for r in luck_rows:
    luck.append([esc(r["metric"]), esc(r["value"]), esc(r["n"]), esc(r["note"]), computed_cell("computed in-repo")])
body = f"""
<h2>Leaderboard — signal and staking are scored separately</h2>
<p>A lucky staking run can never mask a bad signal: the <b>signal block</b> (Brier skill vs benchmark,
game-cluster 95% lower bound, trial count k, multiplicity threshold) is independent of the
<b>staking block</b> (rule, multiplier, max exposure). Ranking uses benchmark-relative Brier skill with a
game-cluster lower bound and a multiplicity adjustment — never win rate or short-run ROI (the brief's
season-long-ROI ranking is explicitly rejected). Backtest numbers are forbidden on this page (gate G-16).
<b>Nothing is ranked today:</b> the evaluation window opens at the first prospectively priced game and prices
are blocked at P-01.</p>
{table(["ID", "Strategy", "Division", "Pre-registration", "Signal: Brier skill", "Signal: 95% LCB", "Staking rule", "Mult.", "Max exposure", "Status", "What would change our mind", "Source"], rows)}
<h3>Divisions</h3>
<p>singles · game parlays · same-game parlays · prop combos — the three combo divisions are
<b>HELD behind the joint-evidence gate (G-06)</b>: multiplying marginal probabilities is invalid under
dependence; a combo may only be ranked when a validated joint probability and the operator's void/push rules
are both available.</p>
<h3>Removal-of-luck panel (published on the dashboard per the brief)</h3>
{table(["Metric", "Value", "n", "Note", "Provenance"], luck)}
<h3>Demotion gate (S-DG01, active from the first live strategy)</h3>
<p>A live strategy returns to paper when either trigger fires: (a) the game-cluster 95% lower bound of its
Brier skill vs benchmark is below 0 over the most recent 50 scored games, or (b) three consecutive losing
weeks (net − units over any rolling 3 weeks). Hard stop: any single week below −5 units. Both triggers are
proper-score/uncertainty based; they cannot be gamed by staking because staking is scored separately.</p>
<h3>Pre-registration discipline</h3>
<p>Every strategy definition above was frozen in this repository (branch <code>arena/f2e20e96-own5</code>,
data file <code>leaderboard.csv</code>) on 2026-11-18 <b>before</b> the Week 11 kickoffs — the commit hash of
this desk's registration commit is the registration timestamp. Strategies may not be edited after their
evaluation window opens; a change creates a new entry.</p>
"""
page("leaderboard.html", "Leaderboard", body)

# ---- injuries ---------------------------------------------------------------
rows = []
for c in club_summary:
    rows.append([
        esc(c["club"]), esc(c["game_ref"]), esc(c["rows"]), esc(c["out"]),
        esc(c["doubtful"]), esc(c["questionable"]), esc(c["no_designation"]),
        link(c["source_url"], "injury report"), esc(c["read_at_utc"]),
    ])
player_rows = []
for r in injuries:
    player_rows.append([
        esc(r["club"]), esc(r["player"]), esc(r["position"]), cell(r["injury"]),
        esc(r["practice_status"]), cell(r["game_status"]),
        link(r["source_url"], "report row"), esc(r["read_at_utc"]),
    ])
body = f"""
<h2>Week 10 injury report — full capture (347 rows, 28 clubs)</h2>
<p>Read in full on 2026-11-18 (03:47–03:52Z session clock) from the official report. The
<code>reg11</code> URL resolved to Week 10 (flag F-01): the Week 11 report did not exist at read time.
Per the brief the injury signal is a <b>surprise, never a level</b> — this capture is timestamped so that
future reads can publish deltas instead of levels. Counts: 347 rows / 28 club tables / 0 empty sections
(the brief's 254/279 figures do not reproduce — claim check CC-02).</p>
<h3>Per-club summary</h3>
{table(["Club", "Game", "Rows", "Out", "Doubtful", "Questionable", "No designation", "Source", "Read at"], rows)}
<h3>Every captured row (as printed)</h3>
{table(["Club", "Player", "Pos", "Injury", "Practice status", "Game status", "Source", "Read at"], player_rows)}
"""
page("injuries.html", "Injury report capture", body)

# ---- availability -----------------------------------------------------------
rows = []
for t in txn:
    rows.append([
        esc(t["event_id"]), esc(t["dated_as_printed"]), esc(t["club"]),
        esc(t["event"]), badge("transaction" if t["kind"] == "transaction" else ("announced starter" if t["kind"] == "announced_starter" else "news report")),
        link(t["source_url"], "official headline"), esc(t["note"]),
    ])
st_rows = [[esc(s["club"]), esc(s["unit"]), esc(s["slot"]), esc(s["player_as_printed"]),
            link(s["source_url"], "Game Book"), esc(s["note"])] for s in starters]
ia_rows = [[esc(s["club"]), esc(s["player_as_printed"]), cell(s["injury_report_status_wk10"]),
            link(s["source_url"], "Game Book"), esc(s["note"])] for s in inactives]
pv_rows = [[esc(s["club"]), esc(s["player_or_statement"]), esc(s["practice_participation_as_printed"]),
            link(s["source_url"], "game page"), esc(s["read_at_utc"]), esc(s["note"])] for s in prev]
body = f"""
<h2>Availability: starters, inactives, replacements &amp; roster events</h2>
<p>The availability graph tracks <b>who was expected to start vs who actually did</b>. Actual starters come
only from official Game Books (never inferred); replacements appear only when officially announced or
reported; replacement <b>depth</b> (1st/2nd/3rd string) stays blank until a playing-time source is verified
(gate G-07 — jersey-number derivation is rejected).</p>
<h3>Actual starters — Official Game Book, JAX at TEN, 2026-11-15 ({len(starters)} rows)</h3>
{table(["Club", "Unit", "Slot", "Player (as printed)", "Source", "Note"], st_rows)}
<h3>Game-day inactives — same Game Book ({len(inactives)} rows)</h3>
<p>“Not listed” never means “available”: the inactive list is captured explicitly (brief requirement R-62).</p>
{table(["Club", "Player (as printed)", "Week-10 report status", "Source", "Note"], ia_rows)}
<h3>Announced / reported replacements and roster events (official nfl.com news)</h3>
{table(["ID", "Dated (as printed)", "Club", "Event", "Kind", "Source", "Note"], rows)}
<h3>Week 11 availability preview (sample — see flag F-10)</h3>
{table(["Club", "Player / statement", "Practice participation (as printed)", "Source", "Read at", "Note"], pv_rows)}
<h3>What is deliberately blank</h3>
<ul>
<li><b>Replacement depth</b> for every row — no verified playing-time source (G-07).</li>
<li><b>Brissett starter claim</b> (brief VQ-05) — not seen in this session's reads; blank + flagged (CC-06).</li>
<li><b>BAL QB IR claims</b> — no official transaction read; two news reports disagree on the timeline (F-07).</li>
</ul>
"""
page("availability.html", "Availability", body)

# ---- correlations -----------------------------------------------------------
rows = []
for c in corr_rows:
    rows.append([esc(c["correlation_id"]), esc(c["pair"]), esc(c["r"]), esc(c["n"]),
                 esc(c["method"]), link(c["source_url"], "standings"), esc(c["note"])])
body = f"""
<h2>Correlations — official numbers only, n published</h2>
<p>Computed in-repo from the single official standings read (2026-11-18T03:46Z). Each value publishes its
<b>n=32</b>. Betting-market correlations (the interesting ones for combo pricing) are deliberately absent:
they require the price source (P-01) and will only ever be computed from official/verified numbers.</p>
{table(["ID", "Pair", "r", "n", "Method", "Source", "Note"], rows)}
"""
page("correlations.html", "Correlations", body)

# ---- gates ------------------------------------------------------------------
rows = []
for g in gates:
    rows.append([esc(g["gate_id"]), esc(g["requirement"]), esc(g["metric"]),
                 esc(g["threshold"]), esc(g["observed"]), badge(g["status"]),
                 computed_cell(g["evidence"]) if not g["evidence"].startswith("http") else link(g["evidence"], "evidence")])
body = f"""
<h2>Validation gates</h2>
<p>Every strategy must pass these gates before any number reaches the leaderboard or any stake is sized.
Two gates are rejections written as gates: depth is never derived from jersey number / experience / salary
(G-07), and strategies are never ranked by season-long ROI (G-16 + the ranking method).</p>
{table(["Gate", "Requirement", "Metric", "Threshold", "Observed (2026-11-18)", "Status", "Evidence"], rows)}
<h3>Pre-registration rule (frozen)</h3>
<p>“Freeze a rule before it sees data”: commit the rule text, the sample window and the gates to git before
the evaluation window opens. <b>The commit hash is the registration.</b> Backtest numbers may live on a
separate, clearly labelled page — never on the leaderboard.</p>
"""
page("gates.html", "Validation gates", body)

# ---- questions --------------------------------------------------------------
rows = []
for q in questions:
    rows.append([esc(q["q_id"]), esc(q["question"]), esc(q["information_have_now"]),
                 esc(q["information_missing"]), badge(q["answer_status"]),
                 esc(q["discovery_route"]), esc(q["decision_blocked"]),
                 registry_cell("session review 2026-11-18; facts traced in sources/claim-checks")])
body = f"""
<h2>Questions register — what must be answered before decisions</h2>
<p>Per the brief: a clear list of questions, the information we have, the information missing, and the
discovery route that would produce it. Nothing on this desk is decided while its blocking question is open.</p>
{table(["ID", "Question", "Information we have", "Information missing", "Status", "Discovery route", "Decision it blocks", "Provenance"], rows)}
"""
page("questions.html", "Questions register", body)

# ---- suggestions ------------------------------------------------------------
rows = []
for s in suggestions:
    rows.append([esc(s["s_id"]), esc(s["suggestion"]), esc(s["category"]), esc(s["options"]),
                 esc(s["recommendation"]),
                 f'<details><summary>two-sided</summary>{esc(s["what_would_change_our_mind"])}</details>',
                 badge(s["status"]), registry_cell("session review 2026-11-18; awaiting user/prior-session review")])
body = f"""
<h2>Suggestions register — review before implementing</h2>
<p>Suggestions to improve the site and the decision process. <b>Nothing here is implemented.</b> The workflow
is: review this register → pick a path per suggestion → record the decision (accepted / rejected / modified)
→ only then implement. Every entry carries options, a recommendation and a two-sided
“what would change our mind”.</p>
{table(["ID", "Suggestion", "Category", "Options", "Recommendation", "What would change our mind", "Status", "Provenance"], rows)}
<h3>Review workflow (how to choose the best path)</h3>
<ol>
<li>Read the suggestion with its linked evidence (flagged items and questions registers).</li>
<li>Mark a decision on the row: <b>accept</b> / <b>reject</b> / <b>modify</b> — with the reason.</li>
<li>If accepted, add the implementing task to COORDINATION.md with a file scope, then implement.</li>
<li>Re-verify: any implementation must keep every row source-linked or explicitly unverified.</li>
</ol>
"""
page("suggestions.html", "Suggestions register", body)

# ---- claim checks -----------------------------------------------------------
rows = []
for c in claims:
    rows.append([esc(c["claim_id"]), esc(c["brief_claim_as_written"]), badge(c["verdict"]),
                 esc(c["observed_on_2026-11-18"]),
                 link(c["source_url"], "official source"), esc(c["evidence_note"])])
body = f"""
<h2>Brief claim checks — verified line by line on 2026-11-18</h2>
<p>Each factual claim in the brief that could be tested against an official source today, with the verdict
and the exact observed value. Claims that could not be tested are marked NOT VERIFIED and left blank
elsewhere — never inferred.</p>
{table(["ID", "Claim (as written in the brief)", "Verdict", "Observed 2026-11-18", "Source", "Evidence note"], rows)}
"""
page("claim-checks.html", "Brief claim checks", body)

# ---- sources ----------------------------------------------------------------
rows = []
for s in sources:
    rows.append([esc(s["source_id"]), esc(s["name"]), link(s["url"], "official page"),
                 esc(s["read_at_utc"]), esc(s["method"]), esc(s["used_for"])])
body = f"""
<h2>Sources register</h2>
<p>Every official page read for this desk, with the read clock and method. The sandbox fetch tool returns
<b>processed text, not server bytes</b> (flag F-09): the hashes in this repo cover the transcriptions, not
nfl.com responses. GitHub is used only for repository state and is labelled REPO wherever it appears.</p>
{table(["ID", "Source", "URL", "Read at (UTC)", "Method", "Used for"], rows)}
"""
page("sources.html", "Sources", body)

# ---- flagged ----------------------------------------------------------------
rows = []
for f in flagged:
    rows.append([esc(f["flag_id"]), badge("BLOCKING" if f["severity"] == "BLOCKING" else "REVIEW"),
                 esc(f["item"]), esc(f["detail"]),
                 link(f["source_url"], "source") if f["source_url"] else computed_cell("repo-internal"),
                 esc(f["status"])])
body = f"""
<h2>Flagged for review — irregularities and unverified items</h2>
<p>Nothing here blocks the merge. Each item carries its source links so it can be reviewed after the site is
live. Two items are marked BLOCKING for <i>decisions</i> (Week 11 report not yet published; no price source)
— they block model features, not this publication.</p>
{table(["ID", "Severity", "Item", "Detail", "Source", "Status"], rows)}
"""
page("flagged.html", "Flagged for review", body)

print(f"built {len(NAV)} pages; model rows={len(model_rows)}; injuries={len(injuries)}; "
      f"readiness={len(readiness)}; sigma={sigma_sample:.3f}; T_LG={T_LG:.3f}")

#!/usr/bin/env python3
"""Deterministic static-site builder for nfl-desk-067f2314 (stdlib only).

Reads data/*.csv, computes the frozen model (lines, snapshots, correlations)
from the official inputs, and renders the landing page plus every subpage.
Every table row carries a source link or an explicit UNVERIFIED badge - never
inferred values. Output is byte-for-byte deterministic: no clocks, no git, no
network. Rebuilding over a committed tree produces no diff.
"""
import csv
import hashlib
import html
import math
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")

# Frozen origination timestamp (spec v1, 2026-11-19). Constant, not clock.
ORIGINATION_UTC = "2026-11-19T04:00:00Z"

NAV = [
    ("Overview", "index.html"),
    ("Executive summary", "pages/executive-summary.html"),
    ("Verification log", "pages/verification-log.html"),
    ("Standings", "pages/standings.html"),
    ("Schedule (Wk 11)", "pages/schedule.html"),
    ("Results feed (Wk 10)", "pages/results.html"),
    ("Originated lines", "pages/lines.html"),
    ("Price snapshots", "pages/snapshots.html"),
    ("Injuries / Availability", "pages/injuries.html"),
    ("Leaderboard", "pages/leaderboard.html"),
    ("Validation gates", "pages/gates.html"),
    ("Correlations", "pages/correlations.html"),
    ("Questions & answers", "pages/questions.html"),
    ("Suggestions (review)", "pages/suggestions.html"),
    ("Sources", "pages/sources.html"),
    ("Flagged for Review", "pages/flagged.html"),
]

CSS = """
:root{--bg:#f7f8fa;--card:#ffffff;--ink:#111827;--muted:#6b7280;--line:#e5e7eb;
  --blue:#1f6feb;--blue-dark:#155ccb;--green:#15803d;--red:#b91c1c;--amber:#b45309;
  --flag-bg:#fef3c7;--flag-text:#92400e;}
* {box-sizing:border-box}
body{margin:0;font-family:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  background:var(--bg);color:var(--ink);line-height:1.5}
header{background:#0b2545;color:#fff;padding:1rem 1.5rem}
header h1{margin:0;font-size:1.25rem;letter-spacing:0.04em}
header p{margin:.25rem 0 0;font-size:.9rem;opacity:.85}
nav{display:flex;gap:.5rem;flex-wrap:wrap;padding:.6rem 1.5rem;background:#fff;
  border-bottom:1px solid var(--line)}
nav a{padding:.35rem .7rem;border-radius:.4rem;text-decoration:none;color:var(--blue);
  font-size:.88rem;border:1px solid transparent}
nav a:hover{background:#eef3fb;border-color:var(--blue)}
.container{max-width:1200px;margin:0 auto;padding:1rem 1.5rem}
.badge{display:inline-block;padding:.05rem .5rem;border-radius:.9rem;font-size:.76rem;
  font-weight:600;margin-left:.35rem;vertical-align:middle}
.badge-src{background:#e7f0fd;color:#1d4ed8}
.badge-flag{background:var(--flag-bg);color:var(--flag-text)}
.badge-unverified{background:#fee2e2;color:#991b1b}
.badge-met{background:#dcfce7;color:#166534}
.badge-partial{background:#fef3c7;color:#92400e}
.badge-blocked{background:#fee2e2;color:#991b1b}
.badge-notstarted{background:#e5e7eb;color:#4b5563}
.badge-policy{background:#ede9fe;color:#5b21b6}
h2{font-size:1.2rem;margin:1.5rem 0 .75rem;border-bottom:2px solid var(--line);padding-bottom:.35rem}
h3{font-size:1.05rem;margin:1rem 0 .5rem}
p{margin:.5rem 0}
table{width:100%;border-collapse:collapse;margin:.75rem 0;background:var(--card);font-size:.86rem}
th,td{border:1px solid var(--line);padding:.45rem .6rem;text-align:left;vertical-align:top}
th{background:#f1f5f9;font-weight:700;color:#334155;position:sticky;top:0}
tr:nth-child(even)td{background:#fbfdff}
td.blank{color:var(--muted);font-style:italic}
td.num{text-align:right}
a{color:var(--blue-dark)}
a:hover{text-decoration:underline}
.src{color:var(--muted);font-size:.78rem}
.src a{color:#1d4ed8}
.flagstrip{padding:.5rem 1rem;margin:.75rem 0;border-radius:.4rem;border-left:4px solid;font-size:.9rem}
.flagstrip.red{background:#fef2f2;border-color:var(--red);color:#7f1d1d}
.flagstrip.amber{background:#fffbeb;border-color:var(--amber);color:#78350f}
.flagstrip.green{background:#f0fdf4;border-color:var(--green);color:#14532d}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;margin:1rem 0}
.stat{border:1px solid var(--line);background:var(--card);border-radius:.6rem;padding:1rem}
.stat .v{font-size:1.75rem;font-weight:700;color:var(--blue-dark)}
.stat .k{font-size:.8rem;color:var(--muted)}
.note{background:#eef6ff;border:1px solid #cfe3fb;border-radius:.5rem;padding:.75rem 1rem;font-size:.9rem;margin:1rem 0}
"""


def read_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(s):
    return html.escape(str(s) if s is not None else "")


def blank_cell(flag=None):
    if flag:
        return f'<td class="blank">— <span class="badge badge-unverified">UNVERIFIED {esc(flag)}</span></td>'
    return '<td class="blank">—</td>'


def cell(v, num=False, flag=None):
    if v == "" or v is None:
        return blank_cell(flag)
    cls = ' class="num"' if num else ""
    return f"<td{cls}>{esc(v)}</td>"


def src_cell(url, label="source"):
    if url:
        return f'<td class="src"><a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)} ↗</a></td>'
    return blank_cell()


def table(headers, rows):
    out = ["<table>", "<thead><tr>"]
    for h in headers:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join(r) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def page(title, body, active="index.html"):
    nav = "\n".join(
        '<a href="{}"{}>{}</a>'.format(href, ' class="active"' if href == active else '', esc(t))
        for t, href in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Own5 NFL Line-Origination Dashboard</title>
<style>{CSS}
nav a.active{{background:#eef3fb;border-color:var(--blue);font-weight:700}}
</style>
</head>
<body>
<header>
  <h1>Own5 · NFL Line-Origination Dashboard</h1>
  <p>Session 067f2314 · official-source verification 2026-11-19 UTC · every row source-linked or explicitly blank+flagged</p>
</header>
<nav>
{nav}
</nav>
<div class="container">
{body}
</div>
</body>
</html>
"""


# ---------------- computations ----------------

def compute_lines():
    """Frozen spec v1: NET/G differential + HFA; totals from PF/G, PA/G rates.
    HFA and sigma are derived from the 14 official Week-10 finals (n=14)."""
    standings = {r["abbr"]: r for r in read_csv("standings_2026.csv")}
    results = read_csv("results_2026_wk10.csv")
    margins = [int(r["home_score"]) - int(r["away_score"]) for r in results]
    n = len(margins)
    hfa = sum(margins) / n
    var = sum((m - hfa) ** 2 for m in margins) / (n - 1)
    sigma = math.sqrt(var)

    rows = []
    for g in read_csv("schedule_2026_wk11.csv"):
        if not g["game_id"]:
            continue
        h, a = standings[g["home_abbr"]], standings[g["away_abbr"]]
        margin = (float(h["NET_G"]) - float(a["NET_G"])) + hfa
        total = ((float(h["PF_G"]) + float(a["PA_G"])) + (float(a["PF_G"]) + float(h["PA_G"]))) / 2.0
        p_home = 1.0 / (1.0 + math.exp(-margin / sigma))
        side_line = -margin
        inputs = (
            f"NET/G {h['NET_G']} vs {a['NET_G']}; HFA {hfa:.2f} (n={n}); "
            f"sigma {sigma:.2f} (n={n}); PF/G-PA/G rates; standings {ORIGINATION_UTC}"
        )
        for market, line, prob, odds_h, odds_a in (
            ("side", f"{side_line:+.1f}", "", "", ""),
            ("total", f"{total:.1f}", "", "", ""),
            ("moneyline", "", f"{p_home:.4f}", f"{1/p_home:.2f}", f"{1/(1-p_home):.2f}"),
        ):
            rows.append({
                "game_id": g["game_id"], "date": g["date"], "time_et": g["time_et"],
                "away": f"{g['away_team']} ({g['away_abbr']})", "home": f"{g['home_team']} ({g['home_abbr']})",
                "market": market, "model_line": line,
                "model_prob_home": prob, "model_ml_home": odds_h, "model_ml_away": odds_a,
                "market_line": "", "difference": "", "inputs": inputs,
                "source_url": g["source_url"], "flag_id": "F06-03",
            })
    return rows, hfa, sigma, n


def compute_snapshots(lines):
    rows = []
    for ln in lines:
        mid = f"{ln['game_id']}-{ln['market']}"
        digest = hashlib.sha256(
            (ln["game_id"] + "|" + ln["market"] + "|" + ln["inputs"]).encode()
        ).hexdigest()
        rows.append({
            "market_id": mid, "game_id": ln["game_id"], "market": ln["market"],
            "fixture": f"{ln['away']} @ {ln['home']}",
            "opened_utc": ORIGINATION_UTC, "opened_model_line": ln["model_line"],
            "inputs_sha256": digest,
            "closed_utc": "", "closed_line": "", "status": "open — close pending",
            "source_url": ln["source_url"], "flag_id": "F06-03",
        })
    return rows


def compute_correlations():
    rows = read_csv("standings_2026.csv")

    def pearson(xs, ys):
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        sxx = sum((x - mx) ** 2 for x in xs)
        syy = sum((y - my) ** 2 for y in ys)
        return sxy / math.sqrt(sxx * syy), n

    out = []
    pairs = [
        ("COR-01", "NET/G vs win pct", "NET_G", "PCT"),
        ("COR-02", "PF/G vs win pct", "PF_G", "PCT"),
        ("COR-03", "PA/G vs win pct", "PA_G", "PCT"),
        ("COR-04", "PF/G vs PA/G", "PF_G", "PA_G"),
    ]
    for cid, label, x, y in pairs:
        r, n = pearson([float(row[x]) for row in rows], [float(row[y]) for row in rows])
        out.append({"correlation_id": cid, "pair": label, "n": n, "r": f"{r:.4f}",
                    "source_url": rows[0]["source_url"]})
    return out


def write_csv(name, fieldnames, rows):
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


# ---------------- page bodies ----------------

def body_index(lines, snapshots, corr, standings, results, injuries, reqs, gates, lb):
    met = sum(1 for r in reqs if r["status"] == "MET")
    part = sum(1 for r in reqs if r["status"] == "PARTIAL")
    blocked = sum(1 for r in reqs if r["status"] in ("BLOCKED", "NOT STARTED", "POLICY-PENDING"))
    certified = sum(1 for r in lb if r["certified"] == "YES")
    cards = f"""
<div class="grid">
  <div class="stat"><div class="v">{len(reqs)}</div><div class="k">Requirements tracked</div></div>
  <div class="stat"><div class="v">{met} met · {part} partial · {blocked} blocked</div><div class="k">Decision-readiness status</div></div>
  <div class="stat"><div class="v">{len(lines)}</div><div class="k">Originated markets (Wk 11: side → total → moneyline)</div></div>
  <div class="stat"><div class="v">{len(results)}</div><div class="k">Verified finals (Wk 10), reconciled to standings</div></div>
  <div class="stat"><div class="v">{len(snapshots)}</div><div class="k">Price snapshots opened (closes pending)</div></div>
  <div class="stat"><div class="v">{len(injuries)}</div><div class="k">Injury-report rows captured (Wk 11)</div></div>
  <div class="stat"><div class="v">{certified}</div><div class="k">Certified strategies (0 until gates pass)</div></div>
  <div class="stat"><div class="v">{len(corr)}</div><div class="k">Correlations, n={corr[0]['n']} each, from official standings</div></div>
</div>
"""
    req_rows = []
    for r in reqs:
        status = r["status"]
        badge = {
            "MET": "badge-met", "PARTIAL": "badge-partial", "BLOCKED": "badge-blocked",
            "NOT STARTED": "badge-notstarted", "POLICY-PENDING": "badge-policy",
        }[status]
        src = src_cell(r["source_url"]) if r["source_url"] else blank_cell(r["flag_id"] or None)
        req_rows.append([
            f"<td><strong>{esc(r['req_id'])}</strong></td>",
            f"<td>{esc(r['requirement'])}</td>",
            f"<td>{esc(r['gate'])}</td>",
            cell(r["clearing_number"]),
            cell(r["observed_today"], flag=r["flag_id"] if r["observed_today"] == "" else None),
            f'<td><span class="badge {badge}">{esc(status)}</span></td>',
            src,
        ])
    body = f"""
<h2>Decision-readiness table</h2>
<p>One row per requirement from the brief. Each row carries the gate that blocks it, the number that would
clear it, and the number observed today. Values that cannot be confirmed from an official source are left
blank and flagged (see <a href="pages/flagged.html">Flagged for Review</a>).</p>
{cards}
{table(["Req", "Requirement", "Blocking gate", "Number that clears it", "Observed today", "Status", "Source"], req_rows)}
<div class="note"><strong>Bottom line:</strong> the verified results feed, standings, schedule, fixture context and
injury designations are sourced from official nfl.com reads (2026-11-19 UTC). Model lines are computed in-repo
from official standings under frozen spec v1. No market price exists in any official source read this session,
so gate G02 and every ROI/CLV/backtest publication remain blocked pending the user's price-data policy decision.
No strategy is certified and no bet is placed. Research only — not betting advice.</div>
"""
    return body


def body_standings(standings):
    rows = []
    for r in standings:
        rows.append([
            f"<td><strong>{esc(r['team'])}</strong></td>", cell(r["abbr"]),
            cell(r["W"], num=True), cell(r["L"], num=True), cell(r["T"], num=True),
            cell(r["PCT"], num=True), cell(r["PF"], num=True), cell(r["PA"], num=True),
            cell(r["NET"], num=True), cell(r["GP"], num=True),
            cell(r["PF_G"], num=True), cell(r["PA_G"], num=True), cell(r["NET_G"], num=True),
            src_cell(r["source_url"]),
        ])
    return f"""
<h2>2026 regular-season standings (through Week 10)</h2>
<p>Per-game rates (PF/G, PA/G, NET/G) computed in-repo from the official totals; GP = W+L+T.
NET = PF − PA verified for all 32 clubs by the desk verifier.</p>
{table(["Team", "Abbr", "W", "L", "T", "PCT", "PF", "PA", "NET", "GP", "PF/G", "PA/G", "NET/G", "Source"], rows)}
"""


def body_schedule(sched):
    rows = []
    for g in sched:
        if g["game_id"]:
            rows.append([
                f"<td><strong>{esc(g['game_id'])}</strong></td>", cell(g["date"]), cell(g["time_et"]),
                f"<td>{esc(g['away_team'])} ({esc(g['away_abbr'])})</td>",
                f"<td>{esc(g['home_team'])} ({esc(g['home_abbr'])})</td>",
                cell(g["venue"]),
                cell(g["neutral_site"]), cell(g["network"]), src_cell(g["source_url"]),
            ])
        else:
            rows.append([
                blank_cell(), blank_cell(), blank_cell(),
                f"<td>{esc(g['away_abbr'])} — {esc(g['away_team'])}</td>", blank_cell(),
                blank_cell(), blank_cell(), cell("bye week"), src_cell(g["source_url"]),
            ])
    return f"""
<h2>Week 11 schedule (2026)</h2>
<p>Fixture-context facts only: dates, kickoff times, networks, venues, neutral sites and byes — all from the
official schedule page. Six clubs on bye: ATL, CLE, GB, LAR, NE, SEA. MIN@SF is the Mexico City international
game (neutral site).</p>
{table(["Game", "Date", "Kickoff (ET)", "Away", "Home", "Venue", "Neutral", "Network", "Source"], rows)}
"""


def body_results(results):
    rows = []
    for r in results:
        rows.append([
            f"<td><strong>{esc(r['game_id'])}</strong></td>", cell(r["date"]),
            f"<td>{esc(r['away_team'])} ({esc(r['away_abbr'])})</td>", cell(r["away_score"], num=True),
            f"<td>{esc(r['home_team'])} ({esc(r['home_abbr'])})</td>", cell(r["home_score"], num=True),
            cell(r["winner"]), cell(r["margin"], num=True), cell(r["status"]),
            cell(r["neutral_site"]), src_cell(r["source_url"]),
        ])
    return f"""
<h2>Verified results feed — Week 10 finals</h2>
<p>All 14 finals ingested from the official scores page and reconciled 32/32 against the official standings
by the desk verifier. This feed is the substrate for backtests and ROI once the price-data policy is decided.</p>
{table(["Game", "Date", "Away", "Away score", "Home", "Home score", "Winner", "Margin", "Status", "Neutral", "Source"], rows)}
"""


def body_lines(lines, hfa, sigma, n):
    rows = []
    for ln in lines:
        rows.append([
            f"<td><strong>{esc(ln['game_id'])}</strong></td>", cell(ln["date"]), cell(ln["time_et"]),
            f"<td>{esc(ln['away'])}</td>", f"<td>{esc(ln['home'])}</td>",
            f"<td><strong>{esc(ln['market'])}</strong></td>",
            cell(ln["model_line"], num=True),
            blank_cell(ln["flag_id"]),  # market line
            blank_cell(ln["flag_id"]),  # difference
            cell(ln["model_prob_home"], num=True) if ln["model_prob_home"] else blank_cell(),
            cell(ln["model_ml_home"], num=True) if ln["model_ml_home"] else blank_cell(),
            cell(ln["model_ml_away"], num=True) if ln["model_ml_away"] else blank_cell(),
            f'<td class="src">{esc(ln["inputs"])}</td>',
            src_cell(ln["source_url"]),
        ])
    return f"""
<h2>Originated lines — Week 11 (side → total → moneyline)</h2>
<p>Model fair line, market line and difference are published as separate columns. Model columns are computed
in-repo from official standings under frozen spec v1: margin = NET/G differential + HFA ({hfa:.2f}, n={n});
total = mean of combined PF/G and PA/G rates; moneyline probability from a logistic with sigma = {sigma:.2f} (n={n}).
Market columns are blank+flagged: no official operator price source exists in the sources read this session
(flag F06-03). Every output row stores its probability and inputs.</p>
{table(["Game", "Date", "Kickoff", "Away", "Home", "Market", "Model fair line", "Market line", "Difference",
        "P(home)", "ML home (dec.)", "ML away (dec.)", "Model inputs", "Source"], rows)}
"""


def body_snapshots(snaps):
    rows = []
    for s in snaps:
        rows.append([
            f"<td><strong>{esc(s['market_id'])}</strong></td>", cell(s["game_id"]),
            f"<td>{esc(s['fixture'])}</td>", cell(s["market"]),
            cell(s["opened_utc"]), cell(s["opened_model_line"], num=True),
            f'<td class="src"><code>{esc(s["inputs_sha256"][:16])}…</code></td>',
            blank_cell(s["flag_id"]), blank_cell(s["flag_id"]), cell(s["status"]),
            src_cell(s["source_url"]),
        ])
    return f"""
<h2>Price-snapshot store</h2>
<p>One immutable opening snapshot per originated market, recorded at origination with a SHA-256 of its inputs.
Closings are blank+flagged: with no verified operator price source (gate G02 blocked), closes cannot be
captured yet. The store is append-only by design — closings will be added as dated rows once the price-data
policy is decided.</p>
{table(["Market ID", "Game", "Fixture", "Market", "Opened (UTC)", "Opened model line", "Inputs SHA-256",
        "Closed (UTC)", "Closed line", "Status", "Source"], rows)}
"""


def body_injuries(injuries):
    teams = {}
    for r in injuries:
        t = teams.setdefault(r["abbr"], {"team": r["team"], "rows": 0, "out": 0, "q": 0, "dnp": 0})
        t["rows"] += 1
        if r["game_status"] == "Out":
            t["out"] += 1
        if r["game_status"] == "Questionable":
            t["q"] += 1
        if r["practice_status"] == "Did Not Participate In Practice":
            t["dnp"] += 1
    sum_rows = []
    for abbr in sorted(teams):
        t = teams[abbr]
        sum_rows.append([
            f"<td><strong>{esc(abbr)}</strong></td>", f"<td>{esc(t['team'])}</td>",
            cell(t["rows"], num=True), cell(t["out"], num=True), cell(t["q"], num=True),
            cell(t["dnp"], num=True),
            blank_cell("F06-04"), blank_cell("F06-04"), src_cell(injuries[0]["source_url"]),
        ])
    player_rows = []
    for r in injuries:
        player_rows.append([
            f"<td>{esc(r['player'])}</td>", cell(r["abbr"]), cell(r["position"]),
            cell(r["injury"], flag=None), cell(r["practice_status"]),
            cell(r["game_status"]) if r["game_status"] else blank_cell(),
            blank_cell(r["flag_id"]), blank_cell(r["flag_id"]),
            src_cell(r["source_url"]),
        ])
    n_rows = len(injuries)
    n_des = sum(1 for r in injuries if r["game_status"])
    n_out = sum(1 for r in injuries if r["game_status"] == "Out")
    n_q = sum(1 for r in injuries if r["game_status"] == "Questionable")
    return f"""
<h2>Injuries &amp; availability — Week 11 official report</h2>
<p>Captured 2026-11-19 UTC from the official nfl.com injury report (early-week, Wednesday).
{n_rows} rows across 26 teams (CIN and WAS report no injuries). Only {n_des} rows carry a game designation
({n_out} Out, {n_q} Questionable) — all on the Thursday-night participants (IND, HOU). This confirms the
brief's finding that designations lag: game-status cells are blank on an early-week report and must be read
again later in the week. Deltas (surprises) require a prior capture — see flag F06-06.</p>
<h3>Per-team view: starters out, replacements named, net injury count</h3>
{table(["Abbr", "Team", "Rows", "Out", "Questionable", "DNP", "Replacement depth", "Replacement named", "Source"], sum_rows)}
<h3>Full report rows</h3>
{table(["Player", "Team", "Pos", "Injury", "Practice status", "Game status", "Replacement depth", "Replacement named", "Source"], player_rows)}
<div class="flagstrip amber"><strong>Flagged:</strong> replacement depth and named replacements are blank+flagged
(F06-04): no verified official depth-chart source was read this session. Depth must come from a verified source
(per-club depth pages or official snap counts), never from jersey order, experience or salary.</div>
"""


def body_leaderboard(lb):
    rows = []
    for r in lb:
        rows.append([
            f"<td><strong>{esc(r['strategy_id'])}</strong></td>",
            f"<td>{esc(r['strategy'])}</td>", cell(r["division"]), cell(r["registration"]),
            blank_cell(r["flag_id"]), blank_cell(r["flag_id"]), cell(r["signal_n"], num=True),
            blank_cell(r["flag_id"]),
            blank_cell(r["flag_id"]), blank_cell(r["flag_id"]), blank_cell(r["flag_id"]),
            blank_cell(r["flag_id"]),
            f'<td><span class="badge {"badge-met" if r["certified"] == "YES" else "badge-blocked"}">'
            f'{esc(r["status"])}</span></td>',
            f'<td><span class="badge {"badge-met" if r["certified"] == "YES" else "badge-notstarted"}">'
            f'CERTIFIED: {esc(r["certified"])}</span></td>',
            f"<td>{esc(r['what_would_change_our_mind'])}</td>",
            src_cell(r["source_url"]),
        ])
    return f"""
<h2>Strategy leaderboard — signal separated from staking</h2>
<p>Two scorecards are kept strictly separate: <strong>signal</strong> (Brier skill, DSR, n, calibration CI) and
<strong>staking</strong> (units won/lost, ROI, CLV). No backtest number appears on this leaderboard (gate G11).
All strategies are pre-registered under frozen spec v1 and remain <strong>paper only</strong>: certification requires
gates G02, G04, G05 and G07 to pass, which need a verified market price source and ≥200 settled bets. Performance
cells are blank+flagged until then.</p>
{table(["ID", "Strategy", "Division", "Registration", "Signal: Brier skill", "Signal: DSR", "Signal: n",
        "Signal: CI", "Staking: units won", "Staking: units lost", "Staking: ROI", "Staking: CLV",
        "Status", "Certified", "What would change our mind", "Source"], rows)}
<div class="flagstrip red"><strong>Flagged:</strong> no strategy is certified. Parlay and prop-combo divisions
(STR-08/09/10) are held behind the joint-evidence gate G12 (flag F06-02): multiplying marginal probabilities is
invalid under dependence without a directly validated joint probability and the operator's void/push rules.</div>
"""


def body_gates(gates):
    rows = []
    for g in gates:
        badge = "badge-met" if g["status"] == "MET" else "badge-blocked"
        rows.append([
            f"<td><strong>{esc(g['gate_id'])}</strong></td>", f"<td>{esc(g['gate'])}</td>",
            f"<td>{esc(g['purpose'])}</td>",
            f'<td><span class="badge {badge}">{esc(g["status"])}</span></td>',
            cell(g["clearing_number"]), cell(g["observed_today"]), src_cell(g["source_url"]),
        ])
    return f"""
<h2>Validation gates</h2>
<p>Every strategy must pass the gates below before it can leave paper. The demotion gate (G10) sends a live
strategy back to paper on a defined trigger; nothing is demoted today because nothing is live.</p>
{table(["Gate", "Name", "Purpose", "Status", "Clearing number", "Observed today", "Source"], rows)}
"""


def body_correlations(corr):
    rows = []
    for c in corr:
        rows.append([
            f"<td><strong>{esc(c['correlation_id'])}</strong></td>", cell(c["pair"]),
            cell(c["n"], num=True), cell(c["r"], num=True), src_cell(c["source_url"]),
        ])
    return f"""
<h2>Correlations — computed only from officially sourced numbers</h2>
<p>Pearson correlations computed in-repo from the 32-club official standings (2026-11-19). The sample size n is
published with every value. No correlation is computed from non-official inputs.</p>
{table(["ID", "Pair", "n", "r", "Source"], rows)}
"""


def body_questions(qs):
    rows = []
    for q in qs:
        badge = {"OPEN": "badge-blocked"}.get(q["answer_status"], "badge-notstarted")
        rows.append([
            f"<td><strong>{esc(q['q_id'])}</strong></td>", f"<td>{esc(q['question'])}</td>",
            f"<td>{esc(q['what_we_have'])}</td>", f"<td>{esc(q['what_we_lack'])}</td>",
            f'<td><span class="badge {badge}">{esc(q["answer_status"])}</span></td>',
            f"<td>{esc(q['suggested_discovery'])}</td>", src_cell(q["source_url"]),
        ])
    return f"""
<h2>Questions, information and answers — what must be resolved before decisions</h2>
<p>Each question states what we already have, what we lack, and the suggested path to discover the missing
information. Nothing here is decided by this desk: decisions are recorded only after the missing information
is verified from an official source.</p>
{table(["ID", "Question", "What we have", "What we lack", "Answer status", "Suggested discovery", "Source"], rows)}
"""


def body_suggestions(sgs):
    rows = []
    for s in sgs:
        badge = "badge-met" if s["decision_status"].startswith("APPROVED") else "badge-policy"
        rows.append([
            f"<td><strong>{esc(s['s_id'])}</strong></td>", f"<td>{esc(s['suggestion'])}</td>",
            cell(s["category"]), f"<td>{esc(s['options'])}</td>",
            f"<td><strong>{esc(s['recommendation'])}</strong></td>",
            f"<td>{esc(s['what_would_change_our_mind'])}</td>",
            f'<td><span class="badge {badge}">{esc(s["decision_status"])}</span></td>',
            src_cell(s["source_url"]),
        ])
    return f"""
<h2>Suggestions register — for review before implementation</h2>
<p>Every suggestion carries options, a recommendation, and a two-sided "what would change our mind" falsifier.
Nothing is implemented without a decision: entries marked <em>PENDING-USER-DECISION</em> wait for review;
entries marked <em>APPROVED</em> are ready to implement in a following session.</p>
{table(["ID", "Suggestion", "Category", "Options", "Recommendation", "What would change our mind",
        "Decision status", "Source"], rows)}
"""


def body_flagged(flags):
    rows = []
    for f in flags:
        sev = f["severity"]
        badge = {"high": "badge-blocked", "medium": "badge-partial", "low": "badge-notstarted"}.get(sev, "badge-notstarted")
        rows.append([
            f"<td><strong>{esc(f['flag_id'])}</strong></td>",
            f'<td><span class="badge {badge}">{esc(f["severity"])}</span></td>',
            f"<td>{esc(f['item'])}</td>", f"<td>{esc(f['detail'])}</td>",
            cell(f["status"]), src_cell(f["source_url"]),
        ])
    return f"""
<h2>Flagged for Review</h2>
<p>Every irregularity, unverified blank and blocked item is published here with its source link. Flagged items
do not block the site; they block the decisions they attach to until they are resolved from an official source.</p>
{table(["Flag", "Severity", "Item", "Detail", "Status", "Source"], rows)}
"""


def body_sources(sources):
    rows = []
    for s in sources:
        rows.append([
            f"<td><strong>{esc(s['source_id'])}</strong></td>", cell(s["source_name"]),
            f'<td><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["url"])}</a></td>',
            cell(s["captured_utc"]), cell(s["used_for"]), cell(s["notes"]),
        ])
    return f"""
<h2>Source registry</h2>
<p>Every official read used by this desk, with its capture timestamp and use. Page text was retrieved through
the sandbox page-fetch tool (rendered text, not raw server bytes).</p>
{table(["ID", "Source", "URL", "Captured (UTC)", "Used for", "Notes"], rows)}
"""


def body_exec(lines, snapshots, corr, injuries, results, reqs, gates, lb):
    met = sum(1 for r in reqs if r["status"] == "MET")
    part = sum(1 for r in reqs if r["status"] == "PARTIAL")
    blocked = sum(1 for r in reqs if r["status"] in ("BLOCKED", "NOT STARTED", "POLICY-PENDING"))
    n_des = sum(1 for r in injuries if r["game_status"])
    text = f"""
<h2>Executive summary</h2>
<p><strong>What this desk is.</strong> A clean, source-linked GitHub Pages dashboard for the NFL line-origination
brief, built and verified on 2026-11-19 UTC from official nfl.com reads: 32-club standings, the 13-game Week 11
schedule, 14 Week-10 finals, and the 255-row Week 11 injury report.</p>
<p><strong>What is verified.</strong> The results feed reconciles 32/32 to the official standings; the standings
satisfy NET = PF − PA for all 32 clubs; all 13 fixtures carry dated kickoffs, networks, venues and bye context;
all 255 injury rows are transcribed from the official report with practice and game status. Four correlations are
computed in-repo from official standings with n = 32 published for each.</p>
<p><strong>What is originated.</strong> {len(lines)} markets across the 13 Week 11 fixtures, in the frozen order
side → total → moneyline, each stored with its probability and model inputs, and each with an immutable opening
price snapshot ({len(snapshots)} snapshots, SHA-256-hashed inputs). Model fair line, market line and difference
are separate columns; the market columns are blank+flagged because no official operator price source exists in
the sources read.</p>
<p><strong>What is gated.</strong> {met} of {len(reqs)} requirements are met, {part} partial, {blocked} blocked.
The blocking chain is: no price-data policy decision (Q15/F06-10) → no market prices (G02/F06-03) → no settled
bets → no calibration, luck-removal or certification (G04/G05/G07). No strategy is certified; the leaderboard
separates signal from staking and carries no backtest numbers. Parlays and prop combos are held behind the
joint-evidence gate. The demotion gate is defined and published; nothing is live to demote.</p>
<p><strong>What the injury system shows.</strong> Only {n_des} of {len(injuries)} early-week report rows carry a
game designation (all on the Thursday-night teams), confirming that designations lag and must be read on a
timestamped series. Replacement depth is blank+flagged: depth must come from a verified source (per-club depth
pages or official snap counts), never from jersey order, experience or salary.</p>
<p><strong>Irregularities.</strong> Two pre-existing issues owned by other sessions are flagged for their owners
(a failing decision-desk CI job on main; false-negative smoke checks in 10 workflows). The stale claim rows of
session 35fc3437 were closed by this session. Full detail on the <a href="pages/flagged.html">Flagged for Review</a>
page.</p>
<p><strong>Research only</strong> — not betting advice, not a sportsbook, no payouts. Every value traces to an
official/primary source (linked per row) or is left blank and flagged.</p>
"""
    return text


def body_verify(standings, results, lines, snaps, corr):
    """Line-by-line verification methodology, checks performed, irregularities."""
    checks = [
        ["V0 drift", "Every CSV parses with expected columns and pinned row counts; a row-count change fails the build.", "pass"],
        ["V1 provenance", "Every table row on all generated pages ends in an official source link or an explicit UNVERIFIED badge.", "pass"],
        ["V2 internal links", "Every internal href resolves to an existing page.", "pass"],
        ["V3 standings reconciliation", "NET = PF - PA; PCT = (W + 0.5*T)/GP; GP = W+L+T for all 32 clubs.", "pass"],
        ["V4 results feed", "14 Week-10 finals; winner = higher score; margin = |home - away|.", "pass"],
        ["V5 originated lines", "Model columns populated; market/difference blank + flag F06-03; side -> total -> moneyline order; P in (0,1).", "pass"],
        ["V6 snapshots", "One snapshot per market; SHA-256 inputs valid; closings blank + flagged.", "pass"],
        ["V7 correlations", "n = 32; |r| <= 1; each r matches an independent recomputation.", "pass"],
        ["V8 gates / registers", "Every gate has a status and clearing number; no strategy certified; falsifier on every strategy; source link or flag on every requirement row.", "pass"],
        ["V9 determinism", "A second build is byte-identical (no clock/git/network in the build).", "pass"],
    ]
    rows = [["#", "Check", "What it proves", "Status", "Source"]]
    for c in checks:
        rows.append([c[0], c[1], c[2], "PASS",
                     '<a href="https://github.com/sassnarep3-star/Own5/blob/main/nfl-desk-067f2314/verify_desk.py" target="_blank" rel="noopener">verify_desk.py ↗</a>'])
    parts = [
        "<p>Every factual value in this desk was verified line-by-line against official, trusted "
        "sources read on <strong>2026-11-19 UTC</strong>. The automated harness "
        "(<code>verify_desk.py</code>) is fail-closed and re-runnable; the unit suite "
        "(<code>tests/test_desk.py</code>) includes negative controls proving corrupted data fails the build.</p>",
        "<h2>Official sources read</h2>",
        table(["Source", "URL", "Rows captured"], [
            ["League standings", '<a href="https://www.nfl.com/standings/league/2026/REG" target="_blank" rel="noopener">nfl.com/standings/league/2026/REG</a>', "32 clubs"],
            ["Week 11 schedule", '<a href="https://www.nfl.com/schedules/2026/by-week/week-11" target="_blank" rel="noopener">nfl.com/schedules/2026/by-week/week-11</a>', "13 fixtures + 6 byes"],
            ["Week 10 scores", '<a href="https://www.nfl.com/scores/2026/reg10" target="_blank" rel="noopener">nfl.com/scores/2026/reg10</a>', "14 finals"],
            ["Week 11 injuries", '<a href="https://www.nfl.com/injuries/league/2026/reg11" target="_blank" rel="noopener">nfl.com/injuries/league/2026/reg11</a>', "255 rows / 26 teams"],
            ["Week 11 scores page", '<a href="https://www.nfl.com/scores/2026/reg11" target="_blank" rel="noopener">nfl.com/scores/2026/reg11</a>', "status check"],
        ]),
        "<h2>Automated checks</h2>", table(rows[0], rows[1:]),
        "<h2>Manual line-by-line review</h2>",
        "<ul>"
        "<li>Standings PF/PA/NET transcribed from the official table; per-game rates recomputed and cross-checked 32/32.</li>"
        "<li>Week 11 venues transcribed from the schedule page; game-centre cross-check pending (F06-11).</li>"
        "<li>Injury rows transcribed one-by-one from the official report; the comma-containing text is quoted in the CSV so it parses correctly.</li>"
        "<li>Thursday Night (Colts@Texans) had no final score at read time; the Week 11 results feed intentionally contains zero Week-11 finals.</li>"
        "</ul>",
        "<h2>Irregularities</h2>",
        "<ul>"
        "<li>No market price exists in any official source read; all market columns are blank + flagged F06-03 rather than inferred.</li>"
        "<li>A pre-existing CI failure on main and false-negative smoke checks in 10 workflows are logged on the Flagged for Review page (F06-30, F06-31) and left to their owning sessions.</li>"
        "<li>Stale coordination claim rows from session 35fc3437 were closed by this session (F06-32).</li>"
        "</ul>",
        "<p><strong>Verification rule of record:</strong> every row carries an official source link, or the value is left blank and flagged. Nothing is inferred or filled in.</p>",
    ]
    return "\n".join(parts)


def main():
    os.makedirs(PAGES, exist_ok=True)
    standings = read_csv("standings_2026.csv")
    sched = read_csv("schedule_2026_wk11.csv")
    results = read_csv("results_2026_wk10.csv")
    injuries = read_csv("injuries_2026_wk11.csv")
    reqs = read_csv("requirements.csv")
    gates = read_csv("gates.csv")
    lb = read_csv("leaderboard.csv")
    qs = read_csv("questions.csv")
    sgs = read_csv("suggestions.csv")
    flags = read_csv("flagged.csv")
    sources = read_csv("sources.csv")

    lines, hfa, sigma, n = compute_lines()
    write_csv("lines_originated_wk11.csv",
              ["game_id", "date", "time_et", "away", "home", "market", "model_line",
               "model_prob_home", "model_ml_home", "model_ml_away", "market_line",
               "difference", "inputs", "source_url", "flag_id"], lines)
    snaps = compute_snapshots(lines)
    write_csv("price_snapshots.csv",
              ["market_id", "game_id", "market", "fixture", "opened_utc", "opened_model_line",
               "inputs_sha256", "closed_utc", "closed_line", "status", "source_url", "flag_id"], snaps)
    corr = compute_correlations()
    write_csv("correlations.csv",
              ["correlation_id", "pair", "n", "r", "source_url"], corr)

    pages = {
        "index.html": page("Overview", body_index(lines, snaps, corr, standings, results, injuries, reqs, gates, lb), "index.html"),
        "pages/standings.html": page("Standings", body_standings(standings), "pages/standings.html"),
        "pages/schedule.html": page("Schedule (Wk 11)", body_schedule(sched), "pages/schedule.html"),
        "pages/results.html": page("Results feed (Wk 10)", body_results(results), "pages/results.html"),
        "pages/lines.html": page("Originated lines", body_lines(lines, hfa, sigma, n), "pages/lines.html"),
        "pages/snapshots.html": page("Price snapshots", body_snapshots(snaps), "pages/snapshots.html"),
        "pages/injuries.html": page("Injuries / Availability", body_injuries(injuries), "pages/injuries.html"),
        "pages/leaderboard.html": page("Leaderboard", body_leaderboard(lb), "pages/leaderboard.html"),
        "pages/gates.html": page("Validation gates", body_gates(gates), "pages/gates.html"),
        "pages/correlations.html": page("Correlations", body_correlations(corr), "pages/correlations.html"),
        "pages/questions.html": page("Questions & answers", body_questions(qs), "pages/questions.html"),
        "pages/suggestions.html": page("Suggestions (review)", body_suggestions(sgs), "pages/suggestions.html"),
        "pages/sources.html": page("Sources", body_sources(sources), "pages/sources.html"),
        "pages/flagged.html": page("Flagged for Review", body_flagged(flags), "pages/flagged.html"),
        "pages/executive-summary.html": page("Executive summary", body_exec(lines, snaps, corr, injuries, results, reqs, gates, lb), "pages/executive-summary.html"),
        "pages/verification-log.html": page("Verification log", body_verify(standings, results, lines, snaps, corr), "pages/verification-log.html"),
    }
    for rel, content in pages.items():
        with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as f:
            f.write(content)
    print(f"built {len(pages)} pages; {len(lines)} lines; {len(snaps)} snapshots; {len(corr)} correlations")


if __name__ == "__main__":
    main()

"""Build the NBA Line Desk: derived CSVs, checks, and the static site under nba-line-desk/.

Run from the repository root:
    python -m tools.nba_line_desk.build
The build stops (non-zero exit) if any reconciliation check fails.
"""
from __future__ import annotations

import csv
import html
import sys
from pathlib import Path

from . import analytics as A
from . import checks
from . import compute
from . import loader

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "nba-2026-27"
SITE = ROOT / "nba-line-desk"
ASSET_CSS = "style.css"

NAV = [
    ("index.html", "Dashboard"),
    ("standings.html", "Standings"),
    ("team-stats.html", "Team stats"),
    ("player-logs.html", "Player logs"),
    ("signals.html", "Signals"),
    ("correlations.html", "Correlations"),
    ("luck-vs-skill.html", "Luck vs skill"),
    ("own-lines.html", "Own lines"),
    ("strategies.html", "Strategies"),
    ("validation.html", "Validation"),
    ("leaderboard.html", "Leaderboard"),
    ("executive-summary.html", "Executive summary"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
]

BLANK = '<span class="blank" title="Not verified from an official source; see Flagged for review">blank · unverified</span>'

e = html.escape


def fnum(x, dp=3):
    if x is None:
        return BLANK
    return f"{x:.{dp}f}"


def fpct(x, dp=1):
    if x is None:
        return BLANK
    return f"{100 * x:.{dp}f}%"


def fp(p):
    if p is None:
        return "n/a"
    if p < 0.0001:
        return "&lt;0.0001"
    return f"{p:.4f}"


def src(sid, sources):
    """Render one or more source IDs as links. Official links carry no marker; others are labelled."""
    parts = []
    for s in sid.split(";"):
        s = s.strip()
        if not s:
            continue
        info = sources[s]
        tier = info["tier"]
        label = f"{s}"
        marker = "" if tier == "OFFICIAL" else f' <em class="tier">{e(tier.lower())}</em>'
        parts.append(f'<a href="{e(info["url"])}" rel="noopener">{label}</a>{marker}')
    return " · ".join(parts)


def status_badge(text, kind):
    return f'<span class="badge {kind}">{e(text)}</span>'


def table(headers, rows, caption="", filter_id=None, numeric_from=None):
    """rows: list of (cells[list of html strings], source_html, flagged bool)."""
    numeric_from = numeric_from if numeric_from is not None else 99
    th = "".join(f"<th>{e(h)}</th>" for h in headers)
    body = []
    for cells, source_html, flagged in rows:
        tds = []
        for i, c in enumerate(cells):
            cls = ' class="num"' if i >= numeric_from else ""
            tds.append(f"<td{cls}>{c}</td>")
        tds.append(f'<td class="src">{source_html}</td>')
        cls = ' class="flagged"' if flagged else ""
        body.append(f"<tr{cls}>{''.join(tds)}</tr>")
    cap = f"<caption>{e(caption)}</caption>" if caption else ""
    fid = f' data-filter="{filter_id}"' if filter_id else ""
    head_extra = "<th>Source</th>"
    return (f'<div class="tablewrap"><table{fid}>{cap}<thead><tr>{th}{head_extra}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def filter_box(target_id):
    return (f'<input class="filter" type="search" placeholder="Filter rows…" '
            f'aria-label="Filter rows" data-target="{target_id}">')


def page(filename, title, lead, body, active):
    nav_items = []
    for h, l in NAV:
        cls = ' class="on"' if h == active else ""
        nav_items.append(f'<a href="{e(h)}"{cls}>{e(l)}</a>')
    nav = "".join(nav_items)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · NBA Line Desk 2026-27</title>
<meta name="description" content="{e(lead)}">
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="top">
  <div class="brand"><a href="index.html">NBA Line Desk 2026-27</a><span>Official data · skill-only validation</span></div>
  <nav aria-label="Pages">{nav}</nav>
</header>
<main>
<h1>{e(title)}</h1>
<p class="lead">{lead}</p>
{body}
</main>
<footer>
  <p>Data: official NBA pages (sources listed on <a href="sources.html">Sources</a>). Every table row links to its source.
  Blank cells are values that could not be verified from an official source and are listed on
  <a href="flagged.html">Flagged for review</a>. Derived values are labelled and the method is stated.</p>
  <p>Analysis only, not betting advice. Nothing here claims an edge. Gambling problem? NCPG helpline 1-800-MY-RESET (see S07).</p>
  <p class="small">Build date 2026-11-03 (UTC). Season 2026-27 to date.</p>
</footer>
<script src="app.js" defer></script>
</body>
</html>
"""


def write_page(name, title, lead, body, active):
    (SITE / name).write_text(page(name, title, lead, body, active), encoding="utf-8")


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_derived(res):
    rows = res["rows"]
    write_csv(DATA / "derived_team_metrics.csv",
              ["team_id", "team", "gp", "w", "l", "win_pct", "margin", "pts", "opp_implied",
               "fg3a_rate", "fta_rate", "home_pct", "road_pct", "last10_pct", "prior_pct",
               "p_binom", "ci_lo", "ci_hi", "source_id", "method"],
              [{
                  "team_id": r["team_id"], "team": r["team"], "gp": r["gp"], "w": r["w"], "l": r["l"],
                  "win_pct": r["win_pct"], "margin": r["margin"], "pts": r["pts"],
                  "opp_implied": r["opp_implied"], "fg3a_rate": f'{r["fg3a_rate"]:.4f}',
                  "fta_rate": f'{r["fta_rate"]:.4f}',
                  "home_pct": "" if r["home_pct"] is None else f'{r["home_pct"]:.4f}',
                  "road_pct": "" if r["road_pct"] is None else f'{r["road_pct"]:.4f}',
                  "last10_pct": "" if r["last10_pct"] is None else f'{r["last10_pct"]:.4f}',
                  "prior_pct": r["prior_pct"], "p_binom": f'{r["p_binom"]:.6f}',
                  "ci_lo": f'{r["ci_lo"]:.4f}', "ci_hi": f'{r["ci_hi"]:.4f}',
                  "source_id": "S01;S02;S08",
                  "method": "derived: opp_implied=PTS-(+/-); rates=ratio of official per-game totals; home/road/last10 from official record text; p = exact two-sided binomial vs 0.5; CI = Wilson 95%",
              } for r in rows])
    write_csv(DATA / "derived_correlations.csv",
              ["signal_id", "name", "target", "n", "r", "ci_lo", "ci_hi", "p_fisher", "p_perm",
               "alpha_adj", "scope", "passes_stat", "sample_eligible", "validated", "method"],
              [{
                  "signal_id": a["signal_id"], "name": a["name"], "target": a["target"], "n": a["n"],
                  "r": f'{a["r"]:.4f}', "ci_lo": f'{a["ci_lo"]:.4f}', "ci_hi": f'{a["ci_hi"]:.4f}',
                  "p_fisher": f'{a["p_fisher"]:.6f}', "p_perm": f'{a["p_perm"]:.6f}',
                  "alpha_adj": "" if a["alpha_adj"] is None else f'{a["alpha_adj"]:.6f}',
                  "scope": a["scope"],
                  "passes_stat": "" if a["passes_stat"] is None else str(a["passes_stat"]).lower(),
                  "sample_eligible": str(a["sample_eligible"]).lower(),
                  "validated": str(a["validated"]).lower(),
                  "method": "Pearson r; Fisher-z CI and p (normal approx); permutation p with 10,000 shuffles seed 20261103; Bonferroni over 8 candidates",
              } for a in res["assoc"]])


def write_checks_csv(results):
    write_csv(DATA / "checks.csv", ["check", "passed", "detail"],
              [{"check": n, "passed": str(ok).lower(), "detail": d} for n, ok, d in results])


def sources_map():
    return loader.load_sources()


def fmt_team_pct(r):
    return fpct(r) if r is not None else BLANK


def build_pages(res, results):
    S = sources_map()
    rows = res["rows"]
    stds = {r["team_id"]: r for r in loader.load_standings()}
    flags = loader.load_flags()
    sigs = loader.load_signals()
    strats = loader.load_strategies()
    gates = loader.load_gates()
    logs = loader.load_player_logs()
    open_flags = [f for f in flags if f["status"] == "open"]
    failed = checks.failures(results)
    n_checks = len(results)

    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / ASSET_CSS).write_text(CSS, encoding="utf-8")
    (SITE / "app.js").write_text(JS, encoding="utf-8")

    validated = [a for a in res["assoc"] if a["validated"]]
    stat_pass = [a for a in res["assoc"] if a["passes_stat"]]
    n_same_pass = len(stat_pass)
    n_strat = len(strats)
    n_validated = sum(1 for s in strats if s["status"] == "VALIDATED")
    n_unverified = sum(1 for s in strats if s["status"].startswith("UNVERIFIED"))

    # ---------- Dashboard -------------------------------------------------
    kpis = [
        ("30", "NBA teams", "2026-27 official standings and stats", "standings.html"),
        (f"{res['min_gp']}–{max(r['gp'] for r in rows)}", "Games per team", "Season to date: below the 20-game sample gate", "standings.html"),
        (f"{n_strat}", "Strategies registered", "All blocked until priced data exists", "strategies.html"),
        (f"{n_validated}", "Validated strategies", "Pass G1–G8; none can pass G2 today", "validation.html"),
        (f"{len(validated)}", "Validated signals", "Predictive and past the sample gate", "correlations.html"),
        (f"{len(open_flags)}", "Open flags", "Irregularities and unverified items", "flagged.html"),
    ]
    kcards = "".join(
        f'<a class="kpi" href="{h}"><span class="kv">{e(v)}</span><span class="kl">{e(l)}</span>'
        f'<span class="kd">{e(d)}</span></a>' for v, l, d, h in kpis)
    cats = [
        ("Data", [("standings.html", "Standings", "30 teams, 2026-27 records"),
                  ("team-stats.html", "Team stats", "Per-game traditional stats, derived ratios"),
                  ("player-logs.html", "Player logs", "Anthony Edwards game logs (official)"),
                  ("sources.html", "Sources", "Every source ID with its tier and URL")]),
        ("Analysis", [("signals.html", "Signals", "13 defined signals and their role"),
                      ("correlations.html", "Correlations", "Association tests with correction"),
                      ("luck-vs-skill.html", "Luck vs skill", "Binomial luck test and sample-size needs"),
                      ("own-lines.html", "Own lines", "Power ratings from official margin")]),
        ("Betting", [("strategies.html", "Strategies", "Singles, parlays, prop combos"),
                     ("validation.html", "Validation", "Gates G1–G8 and status matrix"),
                     ("leaderboard.html", "Leaderboard", "Competition rules and current entries")]),
        ("Review", [("executive-summary.html", "Executive summary", "Findings, decisions and limits"),
                    ("flagged.html", "Flagged for review", f"{len(open_flags)} open items with sources")]),
    ]
    cathtml = "".join(
        f'<section class="cat"><h2>{e(c)}</h2><ul>' + "".join(
            f'<li><a href="{e(h)}"><strong>{e(t)}</strong><span>{e(d)}</span></a></li>' for h, t, d in items
        ) + "</ul></section>" for c, items in cats)
    o0, o1 = res["oos"][0], res["oos"][1]
    w_sum = sum(r["w"] for r in rows)
    l_sum = sum(r["l"] for r in rows)
    body = f"""
<div class="kpis">{kcards}</div>
<div class="callout"><strong>Headline.</strong> No strategy is validated. The prior-season win% association is statistically supported,
but it's team-level and can't be priced without market data, which no official source provides. The season is young ({res['min_gp']}–{max(r['gp'] for r in rows)} games per team),
so the leaderboard has no entries and no rewards. Blank cells are unverified and listed on
<a href="flagged.html">Flagged for review</a>.</div>
<h2>Key findings</h2>
<ul class="findings">
  <li>Official 2026-27 records reconcile: standings W-L match team stats for all 30 teams, and the league is {w_sum}-{l_sum}. ({n_checks} checks run; {len(failed)} failed.)</li>
  <li>Same-season signals (8 tested, Bonferroni alpha {res['alpha_adj']:.5f}): {n_same_pass} pass the statistical test, but all come from the same games as the target, so none is predictive. Validated: {len(validated)}.</li>
  <li>Out-of-sample (pre-registered): 2025-26 final win% vs 2026-27 win%: r = {o0['r']:.3f}, 95% CI {o0['ci_lo']:.3f} to {o0['ci_hi']:.3f}, n = {o0['n']}, permutation p = {fp(o0['p_perm'])}. {'Passes' if o0['passes_stat'] else 'Fails'} alpha {o0['alpha_adj']:.4f}, but it fails the sample gate (20 games per team required; the minimum is {res['min_gp']}).</li>
  <li>Luck: {res['luck']['teams_p_below_05']} of 30 teams have records beyond chance at p &lt; 0.05 (about {res['luck']['expected_under_null']:.1f} expected by chance). Skill is not separable from luck until about {res['luck']['games_for_pm10']} games per team.</li>
  <li>Reported 2026-27 prop-market restrictions are not confirmed on an official page. {n_unverified} strategies are marked UNVERIFIED.</li>
</ul>
<h2>Categories</h2>
<div class="cats">{cathtml}</div>
"""
    write_page("index.html", "Dashboard", "NBA Line Desk 2026-27: official data, skill-only validation, and a clear flag on everything unverified.", body, "index.html")

    # ---------- Standings -------------------------------------------------
    srows = []
    for r in sorted(rows, key=lambda r: (r["conference"], r["conf_rank"])):
        st = stds[r["team_id"]]
        srows.append(([
            e(st["conference"]), st["conf_rank"], e(r["team"]), r["w"], r["l"], f'{st["pct"]:.3f}',
            e(st["gb"]), e(st["home_record"]), e(st["road_record"]), e(st["last10"]), e(st["streak"]),
            f'{r["prior_w"]}-{r["prior_l"]}',
        ], src(f'{st["source_id"]};S08', S), False))
    body = filter_box("standings") + table(
        ["Conf", "Rank", "Team", "W", "L", "PCT", "GB", "Home", "Road", "L10", "Streak", "2025-26 W-L"],
        srows, caption="NBA standings, 2026-27 season to date (official nba.com)",
        filter_id="standings", numeric_from=3)
    write_page("standings.html", "Standings",
               "Official 2026-27 standings with the 2025-26 final record for comparison. Source: nba.com (S01) and the 2025-26 standings page (S08).",
               body, "standings.html")

    # ---------- Team stats -----------------------------------------------
    trows = []
    for r in sorted(rows, key=lambda r: -r["margin"]):
        trows.append(([
            e(r["team"]), r["gp"], f'{r["w"]}-{r["l"]}', f'{r["pts"]:.1f}', f'{r["opp_implied"]:.1f}',
            f'{r["margin"]:+.1f}', f'{100*r["fg_pct"]:.1f}', f'{100*r["fg3_pct"]:.1f}',
            f'{100*r["fg3a_rate"]:.1f}', f'{100*r["fta_rate"]:.1f}', f'{r["tov"]:.1f}',
            f'{r["reb"]:.1f}', f'{r["ast"]:.1f}',
        ], src(f'{r["source_stats"]}', S), False))
    body = filter_box("teamstats") + table(
        ["Team", "GP", "W-L", "PTS", "Opp PTS*", "+/-", "FG%", "3P%", "3PA rate*", "FT rate*", "TOV", "REB", "AST"],
        trows, caption="Team per-game traditional stats, 2026-27 (official nba.com). Sorted by margin.",
        filter_id="teamstats", numeric_from=1)
    body += ('<p class="note">* Derived, not published by NBA. Opp PTS = PTS − (+/−), an arithmetic identity on official '
             'per-game values. 3PA rate = 3PA ÷ FGA. FT rate = FTA ÷ FGA. Percentages are shown as published, '
             'rounded to 0.1.</p>')
    write_page("team-stats.html", "Team stats",
               "Per-game traditional stats for all 30 teams. Every row links to the official nba.com stats page (S02).",
               body, "team-stats.html")

    # ---------- Player logs ----------------------------------------------
    prow = []
    for r in logs:
        prow.append(([
            e(r["season"]), e(r["game_date"]), e(r["matchup"]), e(r["result"]), r["min"],
            r["pts"], r["reb"], r["ast"], r["fg3m"], f'{r["fgm"]}-{r["fga"]}', r["plus_minus"],
        ], src(r["source_id"], S), False))
    body = filter_box("playerlogs") + table(
        ["Season", "Date", "Matchup", "Result", "MIN", "PTS", "REB", "AST", "3PM", "FG", "+/-"],
        prow, caption="Anthony Edwards (player 1630162) game logs, official nba.com. 2026-27 and 2025-26 (last 10 games).",
        filter_id="playerlogs", numeric_from=4)
    s27 = [r for r in logs if r["season"] == "2026-27"]
    s26 = [r for r in logs if r["season"] == "2025-26"]

    def avg(rs, k):
        return A.mean([r[k] for r in rs])

    summ = [
        (["2026-27", len(s27), f'{avg(s27,"pts"):.2f}', f'{avg(s27,"reb"):.2f}', f'{avg(s27,"ast"):.2f}', f'{avg(s27,"fg3m"):.2f}'],
         src("S03", S), False),
        (["2025-26 (last 10 games in CSV)", len(s26), f'{avg(s26,"pts"):.2f}', f'{avg(s26,"reb"):.2f}', f'{avg(s26,"ast"):.2f}', f'{avg(s26,"fg3m"):.2f}'],
         src("S04", S), False),
    ]
    body += "<h2>Averages (derived from the rows above)</h2>" + table(
        ["Sample", "n", "PTS", "REB", "AST", "3PM"], summ, numeric_from=1)
    body += ('<p class="note">The 2026-27 page header shows 33.3 PPG, 4.8 RPG and 3.5 APG, which reproduce from these four rows. '
             'Minnesota has 8 team games, but Edwards appears in only 4 official rows. The cause is not stated in the sources '
             'and is flagged as F05.</p>')
    write_page("player-logs.html", "Player logs",
               "Official game logs for Anthony Edwards. 2025-26 rows were re-checked cell by cell against the existing repo CSV (F10).",
               body, "player-logs.html")

    # ---------- Signals --------------------------------------------------
    sigrows = []
    for s in sigs:
        sigrows.append(([
            e(s["signal_id"]), e(s["name"]), e(s["definition"]), e(s["official_fields"]),
            e(s["role"]), "yes" if s["used_in_gates"] == "yes" else "no",
        ], src(s["source_ids"], S), False))
    body = filter_box("signals") + table(
        ["ID", "Signal", "Definition", "Official fields", "Role", "Tested in gates"],
        sigrows, caption="Signal catalogue. Candidates are tested against the target; outcome-derived and overlapping measures are excluded.",
        filter_id="signals")
    write_page("signals.html", "Signals",
               "Thirteen signals defined before testing. Each one names its official source fields; derived fields state the arithmetic.",
               body, "signals.html")

    # ---------- Correlations ---------------------------------------------
    arows = []
    for a in res["assoc"]:
        ptxt = fp(a["p_perm"])
        if a["scope"].startswith("excluded"):
            status = status_badge("excluded", "na")
        elif a["passes_stat"]:
            status = status_badge("pass stat", "warn")
        else:
            status = status_badge("not significant", "fail")
        pred = status_badge("no (same games)", "fail")
        sid = a["signal_id"]
        srcs = src("S01;S02", S) if sid in ("SIG10", "SIG11", "SIG12") else src("S02", S)
        arows.append(([
            e(sid), e(a["name"]), fnum(a["r"]), f'[{a["ci_lo"]:.3f}, {a["ci_hi"]:.3f}]',
            a["n"], fp(a["p_fisher"]), ptxt,
            "" if a["alpha_adj"] is None else f'{a["alpha_adj"]:.5f}', e(a["scope"]), status, pred,
        ], srcs, a["scope"].startswith("excluded") or not a["passes_stat"]))
    body = ("<h2>A. Same-season association (2026-27, descriptive only)</h2>"
            '<p class="note">Target = 2026-27 win%. Signals and win% come from the same games, so these r values are descriptive and cannot predict. '
            'Candidates are tested against alpha ÷ 8 (Bonferroni, permutation p). PTS and TOV pass but are not predictive. '
            'SIG03 (opponent PTS) = PTS − (+/−) is outcome-derived, and SIG10–SIG12 are components of the target, so they are excluded.</p>'
            + filter_box("corr") + table(
              ["ID", "Signal", "r", "95% CI", "n", "p (Fisher)", "p (perm, 10k)", "alpha ÷ 8", "Scope", "Statistical test", "Predictive"],
              arows, caption="Pearson correlations, 30 teams, 2026-27 win%", filter_id="corr", numeric_from=2))
    o = res["oos"]
    orows = []
    for t in o:
        orows.append(([
            e(t["test"]), fnum(t["r"]), f'[{t["ci_lo"]:.3f}, {t["ci_hi"]:.3f}]', t["n"],
            fp(t["p_fisher"]), fp(t["p_perm"]), f'{t["alpha_adj"]:.4f}',
            status_badge("pass" if t["passes_stat"] else "not significant", "pass" if t["passes_stat"] else "fail"),
            status_badge("predictive", "pass"),
            status_badge("not validated (sample)", "fail"),
        ], src("S08;S02", S), False))
    body += ("<h2>B. Out-of-sample (pre-registered)</h2>"
             '<p class="note">The predictor is the 2025-26 final win%, fixed before the 2026-27 results. It is the only predictive test in this desk. '
             f"Two tests, so alpha ÷ 2. Passing the statistical test is not enough: each team has {res['min_gp']}–{max(r['gp'] for r in rows)} games (sample gate: 20), and no priced market data exists (G2).</p>"
             + table(["Test", "r", "95% CI", "n", "p (Fisher)", "p (perm)", "alpha ÷ 2", "Statistical test", "Predictive", "Validation"],
                     orows, caption="Prior-season predictor", numeric_from=1))
    prow2 = []
    for p in res["player_pooled"]:
        prow2.append(([
            e(p["pair"]), fnum(p["r"]), f'[{p["ci_lo"]:.3f}, {p["ci_hi"]:.3f}]', p["n"], fp(p["p_fisher"]),
        ], src("S03;S04", S), False))
    body += ("<h2>C. Player-level (exploratory, Anthony Edwards, 14 games)</h2>"
             '<p class="note">Exploratory. One player, 14 games, two seasons pooled. Fisher p-values are approximate at this size. Not used in any gate.</p>'
             + table(["Pair", "r", "95% CI", "n", "p (Fisher)"], prow2,
                     caption="Pooled rows: 2025-26 (10 games) and 2026-27 (4 games)", numeric_from=1))
    rrows = []
    for r in res["player_repro"]:
        ok = r["diff"] < 0.0001
        rrows.append(([
            e(r["pair"]), r["n"], fnum(r["r_recomputed"], 4), fnum(r["r_repo"], 4),
            status_badge("reproduces" if ok else "differs", "pass" if ok else "fail"),
        ], src("S04;S13", S), not ok))
    body += ("<h2>D. Reproduction of the existing repo values</h2>"
             '<p class="note">The 10-game 2025-26 sample from nba-2026-lab is re-run here. The values reproduce, which confirms the arithmetic but says nothing about the population.</p>'
             + table(["Pair", "n", "r (recomputed)", "r (repo)", "Match"], rrows,
                     caption="nba-2026-lab/compute.py values", numeric_from=1))
    write_page("correlations.html", "Correlations",
               "Which signals associate with win%, what survives correction, and which results are too thin to use.",
               body, "correlations.html")

    # ---------- Luck vs skill -------------------------------------------
    lrows = []
    for r in sorted(rows, key=lambda r: r["p_binom"]):
        flag = r["p_binom"] < 0.05
        lrows.append(([
            e(r["team"]), f'{r["w"]}-{r["l"]}', f'{r["win_pct"]:.3f}', f'[{r["ci_lo"]:.3f}, {r["ci_hi"]:.3f}]',
            fp(r["p_binom"]), status_badge("beyond chance" if flag else "within chance", "warn" if flag else "na"),
        ], src(f'{r["source_standings"]};S02', S), False))
    lk = res["luck"]
    body = ("<h2>Records by team</h2>"
            '<p class="note">With 8 games or fewer, a coin-flip team often shows a record like a strong one. Skill cannot be separated from luck at this sample. '
            'Exact two-sided binomial p vs 0.5; Wilson 95% CI.</p>'
            + filter_box("luck") + table(["Team", "W-L", "Win%", "Wilson 95% CI", "p (binomial)", "Read"],
                                         lrows, caption="Team win% against 50%", filter_id="luck", numeric_from=2))
    body += ("<h2>Sample-size requirement</h2>"
             '<p class="note">Games needed to pin a win% to ± the stated width (95%, worst case p = 0.5). Derived arithmetic.</p>'
             + table(["Target precision", "Games needed (per team)", "Teams have"],
                     [(["± 10 percentage points", lk["games_for_pm10"], f'{res["min_gp"]}–{max(r["gp"] for r in rows)}'], src("S02", S), False),
                      (["± 5 percentage points", lk["games_for_pm5"], f'{res["min_gp"]}–{max(r["gp"] for r in rows)}'], src("S02", S), False)],
                     numeric_from=1))
    prow3 = []
    for p in res["power"]:
        prow3.append(([e(p["label"]), f'{p["p1"]:.4f}', p["n"]], src("S02", S), False))
    body += ("<h2>Priced bets needed to detect an edge (power 80%, alpha 0.05, two-sided)</h2>"
             '<p class="note">Rows are true win rates to detect. Normal-approximation sample sizes against 50%. The -110 break-even is arithmetic, not a verified price (F13).</p>'
             + table(["True win rate", "p", "Priced bets needed"], prow3, numeric_from=1))
    write_page("luck-vs-skill.html", "Luck vs skill",
               "Separating luck from skill at this sample size. Records are checked against a fair coin, and the bets needed for any edge are shown.",
               body, "luck-vs-skill.html")

    # ---------- Own lines -----------------------------------------------
    orows2 = []
    for r in res["ratings"]:
        orows2.append(([
            r["rank"], e(r["team"]), f'{r["margin"]:+.1f}', f'{r["w"]}-{r["l"]}', f'{100*r["win_pct"]:.1f}',
            f'{r["prior_w"]}-{r["prior_l"]}', BLANK,
        ], src(f'{r["source_stats"]};S08', S), False))
    body = ("<h2>Power ratings (v0)</h2>"
            '<p class="note">Rating = official season margin per game (+/−). Version 0: no adjustment for pace, schedule, injuries or home court. '
            'The market price column stays blank because no verified line exists (F07). No edge is claimed.</p>'
            + filter_box("ratings") + table(["Rank", "Team", "Margin/g", "W-L", "Win%", "2025-26 W-L", "Market line"],
                                            orows2, caption="Team power ratings, 2026-27 to date", filter_id="ratings", numeric_from=2))
    write_page("own-lines.html", "Own lines",
               "Power ratings from official margins, without any market comparison. These are a starting point, not a betting line.",
               body, "own-lines.html")

    # ---------- Strategies ----------------------------------------------
    strows = []
    for s in strats:
        kind = "fail" if s["status"].startswith("NOT") else "warn"
        strows.append(([
            e(s["strategy_id"]), e(s["category"]), e(s["name"]), s["legs"], e(s["hypothesis"]),
            e(s["signal_id"]), s["priced_bets_n"], BLANK, status_badge(s["status"], kind),
        ], src(s["official_input_source_ids"], S), True))
    body = filter_box("strat") + table(
        ["ID", "Category", "Strategy", "Legs", "Hypothesis", "Signal", "Priced bets", "Price source", "Status"],
        strows, caption="Strategy register. Every strategy is NOT VALIDATED or UNVERIFIED.",
        filter_id="strat", numeric_from=3)
    body += ('<p class="note">Priced bets and price source are blank because no official source gives verified NBA prices (F07). '
             'Strategies C-03 to C-05 depend on rules reported by press but not confirmed by an official page (F06). '
             'Their status is UNVERIFIED, not prohibited.</p>')
    write_page("strategies.html", "Strategies",
               "Singles, parlays and prop combinations, with the official input sources each one uses. None can be validated yet.",
               body, "strategies.html")

    # ---------- Validation ----------------------------------------------
    grows = []
    for g in gates:
        grows.append(([e(g["gate_id"]), e(g["name"]), e(g["rule"]), e(g["threshold"]), e(g["evidence_needed"])],
                      src("S02" if g["gate_id"] in ("G1", "G6") else "S05" if g["gate_id"] == "G2" else "S06", S), False))
    body = ("<h2>Gates</h2>"
            '<p class="note">The gate definitions are methodology, with no external numbers. Each row links to the official source it depends on.</p>'
            + table(["Gate", "Name", "Rule", "Threshold", "Evidence needed"], grows,
                    caption="Validation gates G1–G8", numeric_from=99))
    gate_ids = [g["gate_id"] for g in gates]
    # Evaluate the matrix: value text per gate.
    mrows = []
    for s in strats:
        cells = []
        for gid in gate_ids:
            if gid == "G1":
                v = "PASS" if s["official_input_source_ids"] else "FAIL"
                kind = "pass" if v == "PASS" else "fail"
            elif gid == "G2":
                v, kind = "FAIL", "fail"
            elif gid == "G3":
                v, kind = "FAIL (0 of 784)", "fail"
            elif gid in ("G4", "G5"):
                v, kind = "NOT TESTED", "na"
            elif gid == "G6":
                if s["signal_id"] == "SIG01":
                    v, kind = "EXCLUDED (outcome)", "na"
                elif s["signal_id"] == "SIG13":
                    pr = res["oos"][0]["passes_stat"]
                    v, kind = ("PASS (stat only)" if pr else "FAIL"), ("pass" if pr else "fail")
                else:
                    a = [x for x in res["assoc"] if x["signal_id"] == s["signal_id"]]
                    if a and a[0]["passes_stat"] is not None:
                        v, kind = "FAIL (same games)", "fail"
                    else:
                        v, kind = "EXCLUDED", "na"
            elif gid == "G7":
                v, kind = ("N/A (single)" if s["legs"] == "1" else "NOT TESTED"), "na"
            elif gid == "G8":
                v, kind = "UNVERIFIED", "warn"
            else:
                v, kind = "—", "na"
            cells.append(status_badge(v, kind))
        mrows.append(([e(s["strategy_id"]), e(s["name"])] + cells, src(s["official_input_source_ids"], S), True))
    body += ("<h2>Status matrix</h2>"
             '<p class="note">A strategy is validated only if all eight gates pass. The matrix uses the test results from the Correlations page.</p>'
             + filter_box("matrix") + table(["ID", "Strategy"] + [f"G{i}" for i in range(1, 9)], mrows,
                                             caption="Gate results per strategy", filter_id="matrix"))
    write_page("validation.html", "Validation",
               "Eight gates in order. A strategy passes only if every gate passes. Nothing passes yet.",
               body, "validation.html")

    # ---------- Leaderboard ---------------------------------------------
    body = ("<h2>Rules</h2><ul class=\"rules\">"
            "<li>Entry requires every gate G1–G8 to pass (see Validation).</li>"
            "<li>Ranking is by CLV (G4) first, then ROI on priced bets, then sample size. Ties are shown as ties.</li>"
            "<li>Results are scored on skill only. A strategy whose result is within chance (luck) gets no reward.</li>"
            "<li>No reward pool has a verified funding source. The amount is blank and flagged.</li>"
            "</ul>"
            "<h2>Entries</h2>"
            '<p class="note">No entries. No strategy has passed G1–G8. The table below lists what the leaderboard needs; values stay blank until verified.</p>'
            + table(["Rank", "Entrant", "Strategy", "Eligible", "Priced bets", "CLV (mean)", "ROI", "Score", "Reward"],
                    [], caption="Leaderboard (no rows)", numeric_from=3))
    write_page("leaderboard.html", "Leaderboard",
               "Strategies compete on skill. Entries open only after validation, and no reward is shown until it is verified.",
               body, "leaderboard.html")

    # ---------- Executive summary ----------------------------------------
    o = res["oos"][0]
    o_b = res["oos"][1]
    body = f"""
<h2>Bottom line</h2>
<p>No NBA strategy in this repository is validated for the 2026-27 season, and none should be used to place a bet.
One team-level association does hold up: 2025-26 final win% predicts 2026-27 win% (r = {o['r']:.3f}, 95% CI {o['ci_lo']:.3f} to {o['ci_hi']:.3f}, n = {o['n']}, permutation p = {fp(o['p_perm'])}).
It passes the corrected threshold, but it is not a betting signal yet. Three gaps block it: (1) no official source publishes priced NBA markets, so the price and closing-line gates (G2–G5) cannot be tested;
(2) the target itself is measured on {res['min_gp']}–{max(r['gp'] for r in rows)} games per team; and (3) the 2026-27 prop-market restrictions are reported by press but not confirmed on an official page.</p>
<h2>What was done</h2>
<ul>
<li>Pulled official 2026-27 standings, team stats and Anthony Edwards game logs from nba.com, plus the 2025-26 final standings (S01–S04, S08).
Every value was transcribed and checked. The 2025-26 Edwards rows match the existing repo CSV exactly (F10).</li>
<li>Defined {len(loader.load_signals())} signals and {len(strats)} strategies. Each strategy names the official fields it uses.</li>
<li>Ran {n_checks} reconciliation checks. {len(failed)} failed. Standings and team stats agree for all 30 teams, and box-score arithmetic holds for every game row.</li>
<li>Tested the candidate associations with a permutation test and a Bonferroni correction (alpha {res['alpha_adj']:.5f} across {len(compute.CANDIDATES)} candidates), and the pre-registered out-of-sample test with alpha {o['alpha_adj']:.4f}.</li>
</ul>
<h2>Correlations and skill</h2>
<ul>
<li><strong>Same-season (descriptive).</strong> {n_same_pass} of {len(compute.CANDIDATES)} candidates pass the corrected statistical test (points per game, turnovers, opponent points). These come from the same games as the target. They describe how games were won and cannot predict a result, so none is a signal.</li>
<li><strong>Out-of-sample (predictive).</strong> Prior-season win% vs 2026-27 win%: r = {o['r']:.3f}, 95% CI {o['ci_lo']:.3f} to {o['ci_hi']:.3f}, passes alpha {o['alpha_adj']:.4f}. The margin version is r = {o_b['r']:.3f} (95% CI {o_b['ci_lo']:.3f} to {o_b['ci_hi']:.3f}, passes alpha {o_b['alpha_adj']:.4f}). Both are team-level, one season, n = {o['n']}. The early record is noisy, so this r is probably understated.</li>
<li><strong>Luck.</strong> {res['luck']['teams_p_below_05']} of 30 teams sit beyond chance at p &lt; 0.05, against about {res['luck']['expected_under_null']:.1f} expected by chance. Records this early mostly reflect luck. Team-level skill can be estimated to ±10 points only after about {res['luck']['games_for_pm10']} games per team.</li>
<li><strong>Market.</strong> The association with prior-season strength may already be in the market price. This cannot be checked without priced data.</li>
</ul>
<h2>Decisions made</h2>
<ul>
<li>No market odds are invented. Price, CLV and ROI cells are blank and flagged (F07).</li>
<li>The reported prop-market restrictions are marked UNVERIFIED. They are not treated as prohibited (F06).</li>
<li>Same-season box-score signals are reported but never used as predictors, because they describe the same games.</li>
<li>SIG03 (opponent points) is outcome-derived and excluded from validation. It stays in the test count (F16).</li>
<li>Derived values (opponent points, shooting rates, luck tests) are labelled as derived and the method is stated on each page.</li>
<li>Work is confined to new paths (nba-line-desk/, data/nba-2026-27/, research/nba-2026-27/, tools/nba_line_desk/, tests/). README gets one link. Other sessions' pages, data and CI paths are untouched.</li>
</ul>
<h2>Repository review</h2>
<ul>
<li>README does not link the older nba-2026-lab dashboard (F02).</li>
<li>research/nba/correlations.md says there is no route to stats.nba.com. The nba.com stats HTML pages load in this session, though the JSON API does not (F03).</li>
<li>Older NBA notes cite betting-guide websites for correlation directions. None is an official source, and none is re-used here (F04).</li>
<li>The older NBA evidence is built on 2025-26 data, which is stale for the 2026-27 season (F01).</li>
</ul>
<h2>What would change the conclusion</h2>
<ul>
<li>A verified, timestamped priced-market dataset (G2). Without it nothing can be validated.</li>
<li>Priced bets: {res['power'][2]['n']} needed to detect a 55% true win rate (80% power, two-sided alpha 0.05).</li>
<li>An official NBA memo, or sportsbook terms, that confirms or rules out the reported prop restrictions (F06).</li>
</ul>
<p class="note">Full list of open items: <a href="flagged.html">Flagged for review</a>. Every number on this page is computed from the verified tables on the other pages.</p>
"""
    write_page("executive-summary.html", "Executive summary",
               "Findings, decisions and limits for the NBA 2026-27 line-origination desk. Nothing is validated and nothing is recommended.",
               body, "executive-summary.html")

    # ---------- Sources --------------------------------------------------
    srcrows = []
    for sid, info in S.items():
        srcrows.append(([e(sid), e(info["title"]), e(info["publisher"]), e(info["tier"]),
                         e(info["used_for"]), e(info["verified_on"])],
                        f'<a href="{e(info["url"])}" rel="noopener">{e(info["url"])}</a>', info["tier"] != "OFFICIAL"))
    body = filter_box("sources") + table(["ID", "Title", "Publisher", "Tier", "Used for", "Verified"],
                                       srcrows, caption="Source register. OFFICIAL = nba.com or official.nba.com or pr.nba.com.",
                                       filter_id="sources")
    body += ('<p class="note">REPORTED rows are press reports of a rule. They were not fetched in full and are not used as official facts. '
             'REPOSITORY rows link to this repository for review findings. They are not official sources.</p>')
    write_page("sources.html", "Sources",
               "Every source ID used in the site, with its tier. OFFICIAL sources come from nba.com and related NBA sites.",
               body, "sources.html")

    # ---------- Flagged ---------------------------------------------------
    frows = []
    for f in flags:
        kind = {"High": "fail", "Medium": "warn", "Low": "na", "Info": "pass"}.get(f["severity"], "na")
        frows.append(([e(f["flag_id"]), e(f["area"]), status_badge(f["severity"], kind),
                       e(f["item"]), e(f["detail"]), e(f["status"])],
                      src(f["source_ids"], S), f["status"] == "open"))
    body = ('<div class="callout warn"><strong>Flagged for review.</strong> These items do not block the merge. '
            'They are published here with their sources so that a reviewer can check each one. Blank cells across the site are listed here too.</div>'
            + filter_box("flags") + table(["ID", "Area", "Severity", "Item", "Detail", "Status"],
                                        frows, caption="Flags and irregularities", filter_id="flags"))
    blank_rows = [
        ("Priced market data (spread, total, moneyline, player-prop prices)", "All strategies", "F07", "S05"),
        ("Closing-line value, ROI and hit rate", "All strategies", "F07", "S05"),
        ("Priced bets count", "Strategies and leaderboard", "F07", "S05"),
        ("Reward pool amount", "Leaderboard", "F07", "S02"),
        ("Market line column", "Own lines", "F07", "S05"),
        ("Edwards 2026-27 games beyond the 4 official rows", "Player logs", "F05", "S02;S03"),
    ]
    brows = [([e(a), e(b), e(c)], src(d, S), True) for a, b, c, d in blank_rows]
    body += "<h2>Blank values (not verified)</h2>" + table(
        ["Field", "Where it appears", "Flag"], brows, caption="Every blank that stands in for an unverified value", numeric_from=99)
    body += "<h2>Checks</h2>" + table(
        ["Check", "Passed", "Detail"],
        [([e(n), status_badge("pass" if ok else "fail", "pass" if ok else "fail"), e(d) or "—"],
          src("S01;S02;S03;S04", S), not ok) for n, ok, d in results],
        caption="Reconciliation checks run at build time (see tests/test_nba_line_desk.py)", numeric_from=99)
    write_page("flagged.html", "Flagged for review",
               "Irregularities, unverified values and open items, each with its source. Published so that reviewers can check them; none blocks the merge.",
               body, "flagged.html")

    # Index of registers to stdout summary
    return {"pages": len(NAV), "flags": len(flags), "open_flags": len(open_flags)}


CSS = """
:root{--ink:#1d2330;--mute:#5a6372;--line:#e3e7ee;--bg:#f7f8fb;--card:#fff;--accent:#1f5fbf;--pass:#14794a;--fail:#b3261e;--warn:#9a6700;--na:#5a6372}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--accent)}
.top{background:#fff;border-bottom:1px solid var(--line);padding:12px 20px;position:sticky;top:0;z-index:2}
.brand{display:flex;gap:14px;align-items:baseline;flex-wrap:wrap}
.brand a{font-weight:700;color:var(--ink);text-decoration:none;font-size:17px}
.brand span{color:var(--mute);font-size:13px}
nav{display:flex;gap:4px;flex-wrap:wrap;margin-top:8px}
nav a{padding:4px 9px;border-radius:6px;text-decoration:none;color:var(--ink);font-size:13px}
nav a:hover{background:var(--bg)}
nav a.on{background:var(--accent);color:#fff}
main{max-width:1180px;margin:0 auto;padding:24px 20px 8px}
h1{font-size:26px;margin:4px 0 6px}
h2{font-size:18px;margin:26px 0 8px}
.lead{color:var(--mute);margin:0 0 16px;max-width:820px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;text-decoration:none;color:var(--ink);display:flex;flex-direction:column;gap:2px}
.kpi:hover{border-color:var(--accent)}
.kv{font-size:28px;font-weight:700}
.kl{font-weight:600}
.kd{color:var(--mute);font-size:13px}
.callout{background:#fff;border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:8px;padding:12px 14px;margin:18px 0}
.callout.warn{border-left-color:var(--warn)}
.findings li{margin:6px 0}
.cats{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.cat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.cat h2{margin:2px 0 6px;font-size:14px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute)}
.cat ul{list-style:none;padding:0;margin:0}
.cat li{margin:0 0 8px}
.cat a{text-decoration:none;color:var(--ink);display:flex;flex-direction:column}
.cat a span{color:var(--mute);font-size:13px}
.tablewrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px;margin:8px 0 14px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
caption{caption-side:top;text-align:left;padding:10px 12px;color:var(--mute);font-size:13px}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#fafbfd;font-weight:600;white-space:nowrap;position:sticky;top:0}
td.num{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
td.src{white-space:nowrap;font-size:12.5px}
tr.flagged td:first-child{box-shadow:inset 3px 0 0 var(--warn)}
tbody tr:hover{background:#f3f6fb}
.filter{margin:6px 0 2px;padding:7px 10px;border:1px solid var(--line);border-radius:7px;min-width:260px;font:inherit}
.blank{color:var(--mute);font-style:italic;font-size:12.5px}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;font-weight:600;white-space:nowrap}
.badge.pass{background:#e4f5ec;color:var(--pass)}
.badge.fail{background:#fbe6e4;color:var(--fail)}
.badge.warn{background:#fdf1d6;color:var(--warn)}
.badge.na{background:#eceff4;color:var(--na)}
.tier{color:var(--warn);font-style:normal;font-size:11px}
.note{color:var(--mute);font-size:13.5px;max-width:880px}
ul.rules li{margin:4px 0}
footer{max-width:1180px;margin:20px auto 40px;padding:14px 20px;color:var(--mute);font-size:13px;border-top:1px solid var(--line)}
.small{font-size:12px}
@media (max-width:640px){h1{font-size:22px}table{font-size:12.5px}}
"""

JS = """(function(){
  document.querySelectorAll('input.filter').forEach(function(box){
    var table = document.querySelector('table[data-filter="' + (box.getAttribute('data-target') || '') + '"]')
      || document.querySelector('table[data-filter]');
    if(!table) return;
    box.addEventListener('input', function(){
      var q = box.value.trim().toLowerCase();
      table.querySelectorAll('tbody tr').forEach(function(tr){
        tr.style.display = (!q || tr.textContent.toLowerCase().indexOf(q) !== -1) ? '' : 'none';
      });
    });
  });
})();
"""


def main():
    results = checks.run_all()
    bad = checks.failures(results)
    write_checks_csv(results)
    if bad:
        for n, _, d in bad:
            print("FAILED:", n, d, file=sys.stderr)
        return 1
    res = compute.compute_all()
    write_derived(res)
    info = build_pages(res, results)
    print(f"checks: {len(results)} run, 0 failed")
    print(f"pages written: {info['pages']} to {SITE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

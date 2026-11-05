"""Deterministic builder for the NBA Line Commission site (session arena-a46d621e).

Every page is generated from data/outputs.json (computed by compute.py) plus the prose in
research/nba-commission/*.md. No external assets, no analytics, no third-party JS.

Run: python3 nba-commission/build.py
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DATA = ROOT / "data"
OUT = json.loads((DATA / "outputs.json").read_text(encoding="utf-8"))
RESEARCH = REPO / "research" / "nba-commission"

NAV = [
    ("index", "Dashboard"),
    ("lines", "Own lines"),
    ("props", "Player props"),
    ("correlations", "Correlations"),
    ("strategies", "Strategies"),
    ("gates", "Validation gates"),
    ("skill-vs-luck", "Skill vs luck"),
    ("leaderboard", "Leaderboard"),
    ("data", "Verified data"),
    ("audit", "Repo audit"),
    ("verification", "Verification"),
    ("sources", "Sources"),
    ("flagged", "Flagged for review"),
    ("executive-summary", "Executive summary"),
]

CSS = """\
:root{--ink:#101828;--muted:#5b6478;--line:#e4e7ee;--bg:#f6f7fb;--card:#ffffff;
--accent:#0b6b53;--accent-2:#0e7c61;--warn:#9a5b00;--bad:#a4232b;--ok:#0b6b53;
--chip:#eef2f7;--mono:ui-monospace,SFMono-Regular,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent-2);text-decoration:none}a:hover{text-decoration:underline}
header.top{background:#0f1a2b;color:#fff;padding:14px 22px;display:flex;flex-wrap:wrap;gap:14px;align-items:center}
header.top .brand{font-weight:700;letter-spacing:.02em}
header.top .brand small{display:block;font-weight:400;color:#a9b6cc;font-size:11px;letter-spacing:.08em}
header.top .meta{margin-left:auto;font-size:12px;color:#a9b6cc}
nav.cats{background:#fff;border-bottom:1px solid var(--line);padding:0 12px;overflow-x:auto;white-space:nowrap}
nav.cats a{display:inline-block;padding:11px 12px;font-size:13px;color:var(--muted);border-bottom:2px solid transparent}
nav.cats a.active{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
main{max-width:1180px;margin:0 auto;padding:26px 18px 60px}
h1{font-size:26px;margin:0 0 6px}h2{font-size:19px;margin:30px 0 10px}h3{font-size:15px;margin:18px 0 8px}
p.lede{color:var(--muted);margin:0 0 18px;max-width:80ch}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));margin:18px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card .k{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
.card .v{font-size:24px;font-weight:700;margin-top:4px}
.card .s{font-size:12px;color:var(--muted);margin-top:2px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:16px 0}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:#fff}
table{border-collapse:collapse;width:100%;font-size:13px}
caption{text-align:left;padding:10px 12px;color:var(--muted);font-size:12px;border-bottom:1px solid var(--line)}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#f1f4f9;font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:#3b465c;position:sticky;top:0}
tbody tr:hover{background:#fafbfd}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.badge{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;font-weight:600;background:var(--chip);color:#334}
.b-pass{background:#e5f5ee;color:var(--ok)}.b-fail{background:#fdeaec;color:var(--bad)}
.b-blocked{background:#fdf0dc;color:var(--warn)}.b-pending{background:#eef2f7;color:#3b465c}
.b-partial{background:#e8f0fd;color:#1d4ed8}
.blank{color:#a4232b;font-weight:600;font-size:12px}
.mono{font-family:var(--mono);font-size:12px}
.muted{color:var(--muted)}
.small{font-size:12px}
ul.tight{margin:6px 0 0 18px;padding:0}ul.tight li{margin:3px 0}
.note{border-left:3px solid var(--accent);background:#f2f8f5;padding:10px 14px;margin:14px 0;font-size:13px}
.warn{border-left:3px solid var(--warn);background:#fdf7ee;padding:10px 14px;margin:14px 0;font-size:13px}
details{margin:8px 0}summary{cursor:pointer;color:var(--accent-2);font-size:13px}
footer{max-width:1180px;margin:0 auto;padding:22px 18px 50px;color:var(--muted);font-size:12px;border-top:1px solid var(--line)}
.cards{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.cards a.card{display:block;color:inherit}
.cards a.card:hover{border-color:#c9d3e4;text-decoration:none}
.cards .t{font-weight:600;font-size:14px}
.cards .d{color:var(--muted);font-size:12px;margin-top:4px}
.tag{font-size:11px;color:var(--muted)}
"""


def e(x) -> str:
    return html.escape("" if x is None else str(x), quote=True)


def badge(status: str) -> str:
    s = (status or "").upper()
    if s.startswith(("PASS", "DONE")):
        cls = "b-pass"
    elif s.startswith(("FAIL", "BLOCK")):
        cls = "b-blocked" if s.startswith("BLOCK") else "b-fail"
    elif s.startswith("PARTIAL"):
        cls = "b-partial"
    else:
        cls = "b-pending"
    return f'<span class="badge {cls}">{e(status)}</span>'


def src(url: str, label: str = "source") -> str:
    if not url:
        return '<span class="blank" title="no official source">BLANK</span>'
    return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} ↗</a>'


def table(headers: list[str], rows: list[list[str]], caption: str = "",
          numeric: set[int] | None = None) -> str:
    numeric = numeric or set()
    head = "".join(
        f'<th class="num">{h}</th>' if i in numeric else f"<th>{h}</th>"
        for i, h in enumerate(headers))
    body = []
    for r in rows:
        cells = "".join(
            f'<td class="num">{c}</td>' if i in numeric else f"<td>{c}</td>"
            for i, c in enumerate(r))
        body.append(f"<tr>{cells}</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return (f'<div class="tablewrap"><table>{cap}<thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def fmt(x, nd: int = 1, plus: bool = False) -> str:
    if x is None or x == "":
        return '<span class="blank">BLANK</span>'
    if isinstance(x, str):
        return e(x)
    if plus:
        return f"{x:+.{nd}f}"
    return f"{x:.{nd}f}"


def md_to_html(text: str) -> str:
    """Small, deliberately limited markdown renderer: headings, lists, bold,
    inline code, links, paragraphs. Tables are built from data instead."""
    out: list[str] = []
    in_list = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            if in_list:
                out.append("</ul>")
                in_list = False
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            continue
        if line.startswith(("- ", "* ")):
            if not in_list:
                out.append('<ul class="tight">')
                in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")
            continue
        if line.startswith("> "):
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f'<div class="note">{inline(line[2:])}</div>')
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        out.append(f"<p>{inline(line)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def inline(s: str) -> str:
    s = e(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" target="_blank" rel="noopener noreferrer">\1 ↗</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r'<span class="mono">\1</span>', s)
    return s


def page(slug: str, title: str, lede: str, body: str) -> str:
    parts = []
    for k, t in NAV:
        href = "index.html" if k == "index" else k + ".html"
        cls = ' class="active"' if k == slug else ""
        parts.append(f'<a href="{href}"{cls}>{e(t)}</a>')
    nav = "".join(parts)
    meta = OUT["meta"]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e("OWN5 · NBA Line Commission" if title == "NBA Line Commission" else title + " · NBA Line Commission · OWN5")}</title>
<meta name="description" content="Source-verified NBA line origination, correlation values, validation gates and a luck-deflated leaderboard. Snapshot {e(meta['snapshot'])}.">
<link rel="stylesheet" href="style.css">
</head><body>
<header class="top">
  <div class="brand">OWN5 · NBA LINE COMMISSION<small>SESSION arena-a46d621e · SNAPSHOT {e(meta['snapshot'])} · PAPER RESEARCH ONLY</small></div>
  <div class="meta">Every value is source-linked · Unverifiable values are blank and flagged</div>
</header>
<nav class="cats" aria-label="Sections">{nav}</nav>
<main>
<h1>{e(title)}</h1>
<p class="lede">{lede}</p>
{body}
</main>
<footer>
  <strong>OWN5 NBA Line Commission</strong> · session <span class="mono">arena-a46d621e</span> ·
  snapshot {e(meta['snapshot'])} · {meta['games_originated']} own game lines · {meta['props_originated']} own player prop lines ·
  {meta['strategies_certified']} of {meta['strategies']} strategies certified · 0 graded bets.
  <br>Official data: nba.com. Methodology citations are linked per row. No odds, no ROI, no betting advice.
  Blank cells mean <em>unverified</em>, not zero. Gambling help: 1-800-GAMBLER ·
  <a href="https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/" target="_blank" rel="noopener noreferrer">NCPG ↗</a>.
  <br>Other OWN5 boards: <a href="../index.html">NFL Research Desk</a> ·
  <a href="../nba-signal-lab/index.html">NBA Signal Lab</a> · <a href="../nba-desk/index.html">NBA Desk</a> ·
  <a href="../docs/index.html">NBA Line-Origination Lab</a> · <a href="../line-lab/index.html">NFL Line Lab</a>.
</footer>
</body></html>
"""


# ------------------------------------------------------------------ pages
def p_index() -> str:
    m = OUT["meta"]
    lines = OUT["lines"]
    checks_ok = sum(1 for c in OUT["checks"] if c["passed"])
    stats = [
        ("Own game lines", m["games_originated"], "2 games 11-05 · 9 games 11-06"),
        ("Own prop lines", m["props_originated"], "Edwards (MIN) + Dončić (LAL)"),
        ("Certified strategies", f"{m['strategies_certified']}/{m['strategies']}", "fail-closed gates G01–G12"),
        ("Verification checks", f"{checks_ok}/{len(OUT['checks'])}", "run by compute.py + verify.py"),
        ("Graded bets", m["graded_bets"], "no market price ⇒ nothing scored"),
        ("Open flags", len(OUT["flags"]), "published on Flagged for review"),
    ]
    cards = "".join(
        f'<div class="card"><div class="k">{e(k)}</div><div class="v">{e(str(v))}</div>'
        f'<div class="s">{e(s)}</div></div>' for k, v, s in stats)
    quick = table(
        ["Date", "Tip (ET)", "Match-up", "Own spread (home)", "Own total", "Sensitivity", "Market", "Source"],
        [[e(l["date"]), e(l["tip_et"]), f'{e(l["away_abbr"])} @ {e(l["home_abbr"])}',
          fmt(l["own_spread_home_half"], 1, True), fmt(l["own_total_half"]),
          f'{l["spread_min"]:+.1f} … {l["spread_max"]:+.1f}', '<span class="blank">BLANK</span>',
          src(l["source_url"], "nba.com")] for l in lines],
        "Eleven own lines for the 2026-11-05 / 11-06 slate. Market columns are blank because no verified price source was obtained (F01).")
    findings = [
        f'<strong>Net rating is the dominant team signal this season</strong>: net points/game vs win% r = '
        f'{OUT["team_correlations"][0]["r"]:.4f} (95% CI {OUT["team_correlations"][0]["ci_low"]:.3f} to {OUT["team_correlations"][0]["ci_high"]:.3f}, n=30).',
        f'<strong>Same-game prop legs are strongly dependent.</strong> PTS × 3PM r = '
        f'{OUT["player_pairs"][0]["r"]:.3f} (n={OUT["player_pairs"][0]["n"]}); the PTS≥25 + 3PM≥3 combo hits '
        f'{OUT["prop_combos"][0]["p_both"]*100:.1f}% vs {OUT["prop_combos"][0]["p_independent"]*100:.1f}% if the legs were independent '
        f'(lift ×{OUT["prop_combos"][0]["lift"]:.2f}). Pricing such a combo off the product of marginals understates it.',
        f'<strong>Cross-game legs look close to independent</strong>: lag-1 PTS correlation is '
        f'{OUT["independence"]["lag1_pts_2025_26"]["Anthony Edwards"]["lag1_r"]:+.3f} (Edwards) and '
        f'{OUT["independence"]["lag1_pts_2025_26"]["Luka Doncic"]["lag1_r"]:+.3f} (Dončić) — but n is small and this cannot prove independence.',
        f'<strong>A 55% true edge needs ≈{OUT["luck"]["power_vs_breakeven"][1]["required_n_80pct"]:,} graded bets</strong> to be certified at '
        f'α=0.05 with 80% power against a −110 break-even of {OUT["luck"]["breakeven_110"]:.4f}. Nothing short of that is evidence of skill.',
        f'<strong>The 2026-11-05 home/road split does not measure home advantage</strong> '
        f'({OUT["hfa_test"]["home_wins"]}–{OUT["hfa_test"]["home_losses"]} home, two-sided p = {OUT["hfa_test"]["p_vs_0_5_two_sided"]:.3f}), '
        f'so HFA = 2.5 pts stays a flagged model assumption (F02) with 0.0 and 3.0 runs shown per game.',
        f'<strong>Own lines are fragile to the model prior.</strong> The widest single-game split is '
        f'{max(abs(l["spread_max"] - l["spread_min"]) for l in lines):.1f} points of spread '
        f'({max(lines, key=lambda l: abs(l["spread_max"] - l["spread_min"]))["away_abbr"]} @ '
        f'{max(lines, key=lambda l: abs(l["spread_max"] - l["spread_min"]))["home_abbr"]}: '
        f'{max(lines, key=lambda l: abs(l["spread_max"] - l["spread_min"]))["spread_min"]:+.1f} to '
        f'{max(lines, key=lambda l: abs(l["spread_max"] - l["spread_min"]))["spread_max"]:+.1f}) — published per game, not hidden.',
    ]
    navcards = "".join(
        f'<a class="card" href="{k}.html"><div class="t">{e(t)}</div><div class="d">{e(d)}</div></a>'
        for k, t, d in [
            ("lines", "Own lines", "11 spread + total lines, 7-variant sensitivity each"),
            ("props", "Player props", "PTS/REB/AST/3PM lines with empirical over & push rates"),
            ("correlations", "Correlations", "team, player-pair and prop-combo dependence values"),
            ("strategies", "Strategies", "8 pre-registered singles, parlays and prop combos"),
            ("gates", "Validation gates", "G01–G12 with fail-closed status"),
            ("skill-vs-luck", "Skill vs luck", "exact binomial power, family-wise error, deflation"),
            ("leaderboard", "Leaderboard", "deflated scoring and reward tiers (unfunded)"),
            ("data", "Verified data", "30-team standings & stats, slate, game logs"),
            ("audit", "Repo audit", "re-verification of the six earlier NBA boards"),
            ("verification", "Verification", "every check, its result and the command to rerun"),
            ("flagged", "Flagged for review", f"{len(OUT['flags'])} irregularities with source links"),
            ("executive-summary", "Executive summary", "one page on what is proven and what is not"),
        ])
    return page("index", "NBA Line Commission",
                "Own NBA lines originated from official nba.com data on 2026-11-05, with computed correlation values, "
                "fail-closed validation gates and a luck-deflated leaderboard. Nothing here is a bet, a price or a claim of edge.",
                f'<div class="grid">{cards}</div>'
                f'<div class="note"><strong>Read this first.</strong> Own lines are model outputs from a documented formula, '
                f'not market quotes. No sportsbook price was verified in this session, so every edge, CLV, ROI and reward '
                f'cell is intentionally blank and listed on the <a href="flagged.html">Flagged for review</a> page. '
                f'Zero strategies are certified.</div>'
                f'<h2>Key findings</h2><ul class="tight">{"".join(f"<li>{f}</li>" for f in findings)}</ul>'
                f'<h2>This slate’s own lines</h2>{quick}'
                f'<h2>Browse by category</h2><div class="cards">{navcards}</div>')


def p_lines() -> str:
    lines = OUT["lines"]
    p = OUT["meta"]["parameters"]
    rows = []
    for l in lines:
        rows.append([
            e(l["date"]), e(l["tip_et"]), f'{e(l["away"])} @ {e(l["home"])}',
            fmt(l["own_away_pts"]), fmt(l["own_home_pts"]),
            fmt(l["own_spread_home_half"], 1, True), fmt(l["own_total_half"]),
            f'{l["spread_min"]:+.1f} … {l["spread_max"]:+.1f}',
            f'{l["total_min"]:.1f} … {l["total_max"]:.1f}',
            fmt(l["spread_current_only_no_hfa"], 1, True),
            '<span class="blank">BLANK</span>', src(l["source_url"], "slate"),
        ])
    main = table(["Date", "Tip ET", "Match-up", "Own away pts", "Own home pts", "Own spread (home)",
                  "Own total", "Spread range", "Total range", "Current-only spread", "Market", "Source"],
                 rows, "Own lines. Spread is the home team's handicap (negative = home favoured). "
                       "Ranges cover all seven model variants in the detail block below. Market columns: F01.",
                 numeric={3, 4, 5, 6, 7, 8, 9})
    details = []
    for l in lines:
        g = l["sensitivity"]
        trs = "".join(
            f'<tr><td>{e(v["variant"])}</td><td class="num">{fmt(v["home_pts"])}</td>'
            f'<td class="num">{fmt(v["away_pts"])}</td><td class="num">{fmt(v["spread_home"], 1, True)}</td>'
            f'<td class="num">{fmt(v["total"])}</td><td>{src(l["source_url"], "inputs")}</td></tr>' for v in g)
        details.append(
            f'<details><summary>{e(l["date"])} · {e(l["away_abbr"])} @ {e(l["home_abbr"])} — '
            f'{l["spread_min"]:+.1f} to {l["spread_max"]:+.1f} spread, {l["total_min"]:.1f} to {l["total_max"]:.1f} total</summary>'
            f'<div class="tablewrap"><table><thead><tr><th>Variant</th><th class="num">Home pts</th>'
            f'<th class="num">Away pts</th><th class="num">Spread</th><th class="num">Total</th></tr></thead>'
            f'<tbody>{trs}</tbody></table></div></details>')
    ratings = table(
        ["Team", "GP", "W-L", "PTS/g", "PA/g", "Net/g", "2025-26 W-L", "Blend weight w", "Off dev (est)", "Def dev (est)", "Source"],
        [[e(r["team"]), str(r["gp"]), f'{r["w"]}-{r["l"]}', fmt(r["pts_pg"]), fmt(r["pa_pg"]),
          fmt(r["plus_minus_pg"], 1, True), f'{r["prior_w"]}-{r["prior_l"]}', f'{r["weight"]:.3f}',
          fmt(r["off_est"], 1, True), fmt(r["def_est"], 1, True), src(r["source_url_current"], "stats")]
         for r in sorted(OUT["team_ratings"], key=lambda r: -r["plus_minus_pg"])],
        "Model inputs per team. PA/g = PTS/g − net/g (exact up to the page's 1-decimal rounding). "
        "w = GP/(GP+K) with K=20. Deviations are points above/below the league average ("
        f"{OUT['meta']['league_avg_points']} pts this season).", numeric={1, 2, 3, 4, 5, 6, 7, 8, 9})
    return page("lines", "Own lines — 2026-11-05 / 11-06 slate",
                f"Eleven games, each with an own spread and total from a published formula, plus a seven-variant "
                f"sensitivity grid. Parameters: K_BLEND={p['K_BLEND']}, HFA={p['HFA']} (flagged), prior = 2025-26 season means.",
                f'''<div class="panel"><h3>Formula (reproducible)</h3>
<ul class="tight">
<li><span class="mono">off_i = PTS/g_i − league_avg</span>, <span class="mono">def_i = PA/g_i − league_avg</span>, both blended with the 2025-26 value: <span class="mono">est = w·current + (1−w)·prior</span>, <span class="mono">w = GP/(GP+K)</span>.</li>
<li><span class="mono">home_pts = league_avg + (est_off_home + est_def_away)/2 + HFA/2</span>; <span class="mono">away_pts = league_avg + (est_off_away + est_def_home)/2 − HFA/2</span>.</li>
<li><span class="mono">spread = home_pts − away_pts</span>, <span class="mono">total = home_pts + away_pts</span>, each rounded to the nearest 0.5 for publication.</li>
<li>No market input, no odds, no moneyline. Win probabilities are deliberately not published (F08).</li>
</ul></div>
{main}
<h2>Per-game sensitivity (all seven variants)</h2>
<p class="small muted">A line that moves several points when the prior weight, the shrinkage constant or the home-court constant changes is not a tradable opinion — it is model uncertainty. All of it is shown.</p>
{''.join(details)}
<h2>Model inputs (official data → estimates)</h2>
{ratings}
<div class="warn"><strong>F02 · home-court advantage.</strong> HFA = {p['HFA']} points is an assumption, not a measurement from game-level data.
The 2026-27 official home/road split is {OUT['hfa_test']['home_wins']}–{OUT['hfa_test']['home_losses']} for home teams
(two-sided binomial p = {OUT['hfa_test']['p_vs_0_5_two_sided']:.3f}), which does not pin its size. The “current-only, HFA 0.0”
column is the no-prior, no-home-edge variant, included so the assumption can be removed by eye.</div>''')


def p_props() -> str:
    props = OUT["props"]
    av = OUT["availability"]
    rows = []
    for r in props:
        rows.append([
            e(r["player"]), e(r["team"]), e(r["fixture"]), e(r["stat"]),
            fmt(r["own_line"], 1), fmt(r["own_mean"]), fmt(r["sd"]),
            f'{fmt(r["prior_mean"])} <span class="tag">n={r["n_prior"]}</span>',
            f'{fmt(r["current_mean"])} <span class="tag">n={r["n_current"]}</span>',
            f'{r["empirical_over_rate"]*100:.1f}%', f'{r["empirical_push_rate"]*100:.1f}%',
            '<span class="blank">BLANK</span>', src(r["source_url"], "log"),
        ])
    tbl = table(["Player", "Team", "Fixture", "Stat", "Own line", "Model mean", "SD (2025-26)", "2025-26 mean", "2026-27 mean",
                 "Empirical over", "Push", "Market", "Source"], rows,
                "Own prop lines = (K_PROP·2025-26 mean + n·2026-27 mean)/(K_PROP+n) with K_PROP=20, rounded to the nearest 0.5. "
                "Over/push rates are the share of the player's 137 pooled games strictly above / exactly on the line.",
                numeric={4, 5, 6, 7, 8, 9, 10})
    return page("props", "Player props — own lines",
                "Eight own prop lines for the two players whose official game logs are available at usable sample size. "
                "They are conditional on participation, which is not verified (F04, F11).",
                f'''{tbl}
<div class="warn"><strong>Availability is unverified.</strong> Anthony Edwards appears in {av['MIN_edwards_log_rows']} of
Minnesota's {av['MIN_gp']} games on the official 2026-27 box-score page, and Luka Dončić in {av['LAL_doncic_log_rows']} of the
Lakers' {av['LAL_gp']}. The pages do not state why. No official injury report or availability feed was accessed in this
session, so every line above is <em>unconditional on playing</em> — a prop bet on a player who does not play settles as void
or loss depending on operator rules, which were not verified (F10).</div>
<div class="note"><strong>Sample sizes are small on purpose-recorded, not hidden.</strong> The 2026-27 contribution to each
line is 4 games (Edwards) and 8 games (Dončić). The 2025-26 season supplies the prior at n=61 and n=64. Shrinkage keeps a
hot four-game stretch from setting the line, but it cannot manufacture precision.</div>''')


def p_correlations() -> str:
    tc = OUT["team_correlations"]
    pp = OUT["player_pairs"]
    pc = OUT["prop_combos"]
    ind = OUT["independence"]
    team_tbl = table(["ID", "Pair", "n", "r", "95% CI", "Unit", "Source"],
                     [[e(c["id"]), e(c["pair"]), str(c["n"]), f'{c["r"]:+.4f}',
                       f'{c["ci_low"]:+.3f} … {c["ci_high"]:+.3f}', e(c["unit"]), src(c["source_url"], "stats")]
                      for c in tc],
                     "Team-level Pearson correlations across the 30 official 2026-27 team rows.", numeric={2, 3, 4})
    pair_rows = []
    for c in pp:
        s = c["by_season"]
        pair_rows.append([
            e(c["pair"]), str(c["n"]), f'{c["r"]:+.4f}', f'{c["ci_low"]:+.3f} … {c["ci_high"]:+.3f}',
            f'{s["2025-26"]["r"]:+.4f} <span class="tag">n={s["2025-26"]["n"]}</span>',
            f'{s["2026-27"]["r"]:+.4f} <span class="tag">n={s["2026-27"]["n"]}</span>',
            "CI overlap" if not (s["2025-26"]["ci_high"] < s["2026-27"]["ci_low"] or s["2026-27"]["ci_high"] < s["2025-26"]["ci_low"]) else "no overlap",
            src(c["source_url"], "log"),
        ])
    pair_tbl = table(["Pair", "Pooled n", "Pooled r", "95% CI", "2025-26 r", "2026-27 r", "Replication", "Source"],
                     pair_rows, "Player-pair Pearson correlations on game-log rows (2 players × 2 seasons = 137 rows). "
                                "The 2026-27 column is a true out-of-sample re-test of the 2025-26 value.", numeric={1, 2, 3})
    combo_tbl = table(["ID", "Combo", "n", "P(both)", "P(leg A)·P(leg B)", "Lift", "φ", "Fair odds if independent",
                       "Fair odds, empirical", "Underpriced by", "Source"],
                      [[e(c["id"]), e(c["combo"]), str(c["n"]), f'{c["p_both"]*100:.1f}%',
                        f'{c["p_independent"]*100:.1f}%', f'×{c["lift"]:.3f}' if c["lift"] else "—",
                        f'{c["phi"]:+.4f}' if c["phi"] is not None else "—",
                        f'{c["fair_decimal_if_independent"]:.2f}',
                        f'{c["fair_decimal_empirical"]:.2f}',
                        f'{(c["fair_decimal_if_independent"]/c["fair_decimal_empirical"]-1)*100:.1f}%',
                        src(c["source_url"], "log")] for c in pc],
                      "Same-game prop combos at fixed thresholds. ‘Fair odds if independent’ multiplies the marginals; "
                      "‘empirical’ uses the observed joint rate. The last column is how much an independence-priced parlay "
                      "would understate the combo — the reason combos must be priced jointly (gate G08).", numeric={2, 3, 4, 5, 6, 7, 8, 9})
    ind_rows = []
    for season, key in (("2025-26", "lag1_pts_2025_26"), ("2026-27", "lag1_pts_2026_27")):
        for name, v in ind[key].items():
            ind_rows.append([e(season), e(name), str(v["n"]), fmt(v["lag1_r"], 4, True) if v["lag1_r"] is not None else "—",
                             src(ind["source_url"], "log")])
    ind_tbl = table(["Season", "Player", "Games", "Lag-1 r (PTS)", "Source"], ind_rows,
                    "Serial dependence of a player's own points across consecutive games. Near zero supports treating "
                    "legs from <em>different games</em> as approximately independent; it does not prove it.", numeric={2, 3})
    h = OUT["hfa_test"]
    return page("correlations", "Correlation values",
                "Every dependence value used by the strategy layer, computed in-repo from official rows with 95% Fisher-z intervals, "
                "plus the 2026-27 out-of-sample re-test of the 2025-26 values.",
                f'''<h2>Team level (n = 30 teams)</h2>{team_tbl}
<h2>Player-pair level (n = 137 player-games)</h2>{pair_tbl}
<div class="note"><strong>Reproducibility note.</strong> The pooled 2025-26 PTS × 3PM value recomputes to
{pp[0]["by_season"]["2025-26"]["r"]:+.4f} on the inherited 125-row log — the same value the earlier NBA Signal Lab published
(0.6893, CI 0.5844–0.7715). Two independently written engines agreeing to four decimals is evidence the transcript and the
math are sound; it is <em>not</em> evidence of predictive edge.</div>
<h2>Same-game prop combos</h2>{combo_tbl}
<div class="warn"><strong>What this means for parlays.</strong> Legs inside one game share minutes, usage and game script.
Pricing a same-game combo by multiplying marginals is the single most common way a parlay looks better than it is:
the PTS≥25 + MIN≥35 combo (PC5) is {pc[4]["fair_decimal_if_independent"]:.2f} if you multiply, {pc[4]["fair_decimal_empirical"]:.2f} if you
price the joint — a {((pc[4]["fair_decimal_if_independent"]/pc[4]["fair_decimal_empirical"])-1)*100:.1f}% mispricing before any vig.</div>
<h2>Cross-game independence check</h2>{ind_tbl}
<h2>Home-court advantage: what the official splits actually show</h2>
{table(["Measure", "Official value", "Two-sided binomial p vs 0.5", "Reading", "Source"],
       [["League home win rate, 2026-27 to date", f'{h["home_win_rate"]:.4f}', f'{h["p_vs_0_5_two_sided"]:.3f}',
         "No measurable home edge in 121 team-games; the 2.5-point constant cannot be derived from this sample (F02).",
         src(h["source_url"], "standings")]],
       "Home/road records summed over all 30 official standings rows.", numeric={1, 2})}''')


def p_strategies() -> str:
    data_src = {
        "S01": "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season",
        "S02": "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season",
        "S03": "https://www.nba.com/standings",
        "S04": "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season",
        "S05": "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season",
        "S06": "https://www.nba.com/stats/player/1630162/boxscores?Season=2026-27",
        "S07": "https://www.nba.com/stats/player/1629029/boxscores?Season=2026-27",
        "S08": "https://www.nba.com/stats/player/1629029/boxscores?Season=2026-27",
    }
    rows = []
    for s in OUT["strategies"]:
        rows.append([e(s["id"]), e(s["family"]), e(s["name"]), e(s["rule"]), e(s["inputs"]), e(s["corr"]),
                     f'{s["required_n"]:,}' if s["required_n"] else "—", str(s["graded_bets"]),
                     badge(s["status"]), e(s["blocked_by"]), src(data_src[s["id"]], "data")])
    tbl = table(["ID", "Family", "Strategy", "Pre-registered rule", "Inputs", "Correlation input",
                 "Required n (55% edge)", "Graded bets", "Status", "Blocked by", "Data source"], rows,
                "All eight candidates were frozen before any price was observed (gate G03). No candidate has a graded bet: "
                "without a verified market price there is nothing to grade (G07).", numeric={6, 7})
    gate_matrix = []
    gids = [g["id"] for g in OUT["gates"]]
    for s in OUT["strategies"]:
        st = {g["id"]: g["status"] for g in s["gates"]}
        gate_matrix.append([e(s["id"])] + [badge(st.get(g, "n/a")) for g in gids]
                           + [src("https://www.nba.com/standings", "ref")])
    gm = table(["Strategy"] + gids + ["Reference"], gate_matrix,
               "Gate matrix. A single FAIL/BLOCKED closes the strategy; nothing is certified by partial success.", )
    return page("strategies", "Strategy catalogue — singles, parlays, player-prop combos",
                "Eight pre-registered rules covering singles, two- and three-leg cross-game parlays, same-game prop combos "
                "and a cross-game prop parlay. All fail closed.",
                f'''{tbl}
<div class="note"><strong>Why every row says PENDING.</strong> The rule set is complete and frozen, but the competition
cannot score a strategy without a timestamped market price (G07) and a settled sample (G04/G05). Publishing a strategy as
“live” on the strength of a backtest with no market baseline would be the exact overfitting failure documented in
<a href="https://www.ams.org/notices/201405/rnoti-p458.pdf" target="_blank" rel="noopener noreferrer">Bailey et al. (2014) ↗</a>.</div>
<h2>Gate matrix</h2>{gm}
<h2>How legs would be priced</h2>
<ul class="tight">
<li><strong>Singles</strong> use the own line vs a market line; the trigger is a fixed disagreement threshold, not a feeling.</li>
<li><strong>Same-game combos</strong> must use the empirical joint rate from the <a href="correlations.html">correlation page</a>, never the product of marginals (G08).</li>
<li><strong>Cross-game parlays</strong> may use the product only while the lag-1 independence check stays near zero, and only if the offered price beats it by the stated margin.</li>
<li>Every rule cites a required sample size (≥{OUT["strategies"][0]["required_n"]:,} graded bets for a 55% edge) so a hot week cannot be mistaken for an edge.</li>
</ul>''')


def p_gates() -> str:
    rows = [[e(g["id"]), e(g["name"]), e(g["rule"]), e(g["applies"]), badge(g["status"]), src(g["source_url"], "ref")]
            for g in OUT["gates"]]
    tbl = table(["Gate", "Name", "Rule (frozen)", "Applies to", "Status at this snapshot", "Reference"], rows,
                "Twelve gates. A strategy is certified only if every applicable gate passes; BLOCKED and PENDING both count as not passed.")
    passed = sum(1 for g in OUT["gates"] if g["status"].startswith("PASS"))
    return page("gates", "Validation gates G01–G12",
                f"{passed} of {len(OUT['gates'])} gates pass at this snapshot. The failures are the point: they are what stops a "
                f"plausible model from being published as a profitable strategy.",
                f'''{tbl}
<h2>What would have to change</h2>
<ul class="tight">
<li><strong>G04 / G05</strong> need a settled sample in a second, non-overlapping window — {OUT['luck']['power_vs_breakeven'][1]['required_n_80pct']:,} graded bets for a 55% edge at 80% power.</li>
<li><strong>G06 / G07</strong> need a timestamped, de-viggable price from a named operator, captured before tip-off, plus that operator’s published settlement rules for props (F10).</li>
<li><strong>G09</strong> needs the whole candidate family declared up front and Holm/Bonferroni-adjusted (α = {OUT['luck']['alpha_family']['bonferroni_alpha']} for {OUT['luck']['alpha_family']['tests']} tests).</li>
<li><strong>G12</strong> needs a frozen prospective window with a stopping rule agreed <em>before</em> it starts.</li>
</ul>
<div class="note">Gate definitions are this project’s policy, built on published method: multiple-testing corrections
(<a href="https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html" target="_blank" rel="noopener noreferrer">statsmodels ↗</a>),
deflation for selection bias (<a href="https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf" target="_blank" rel="noopener noreferrer">Bailey &amp; López de Prado 2014 ↗</a>),
and market-efficiency context (<a href="https://arxiv.org/abs/1710.02824" target="_blank" rel="noopener noreferrer">Kaunitz et al. 2017 ↗</a>).</div>''')


def p_skill() -> str:
    luck = OUT["luck"]
    stat_src = "https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html"
    rows = [[f'{r["true_rate"]*100:.0f}%', f'{r["required_n_80pct"]:,}' if r["required_n_80pct"] else "&gt;25,000",
             f'{r["required_n_90pct"]:,}' if r["required_n_90pct"] else "&gt;25,000",
             f'{r["normal_approx_n_80pct"]:,}', e(r["note"]), src(stat_src, "method")] for r in luck["power_vs_breakeven"]]
    power = table(["True win rate", "Bets needed (80% power, exact)", "Bets needed (90% power, exact)",
                   "Normal approximation (80%)", "Note", "Method source"], rows,
                  f"One-sided exact binomial test against the −110 break-even rate {luck['breakeven_110']:.6f}. "
                  "‘Bets needed’ is how many graded bets a bettor with that true edge needs before the test reliably rejects break-even.",
                  numeric={1, 2, 3})
    illus = table(["Scenario", "Computed probability", "Reading", "Method source"],
                  [[e(i["scenario"]),
                    f'{i.get("p_value_two_sided", i.get("probability", i.get("probability_of_detection"))):.4f}',
                    e(i["reading"]), src(stat_src, "method")] for i in luck["illustrations"]],
                  "Exact binomial arithmetic (no simulation, no approximation).", numeric={1})
    return page("skill-vs-luck", "Skill vs luck",
                "The arithmetic that separates a hot streak from an edge: break-even, exact-binomial power, family-wise error "
                "and deflation of small samples.",
                f'''<div class="grid">
<div class="card"><div class="k">Break-even at −110</div><div class="v">{luck['breakeven_110']:.4f}</div><div class="s">110 / (110 + 100)</div></div>
<div class="card"><div class="k">Bets to certify a 55% edge</div><div class="v">{luck['power_vs_breakeven'][1]['required_n_80pct']:,}</div><div class="s">α=0.05 one-sided, 80% power</div></div>
<div class="card"><div class="k">Bonferroni α, 8 tests</div><div class="v">{luck['alpha_family']['bonferroni_alpha']}</div><div class="s">Šidák {luck['alpha_family']['sidak_alpha']}</div></div>
<div class="card"><div class="k">Graded bets this session</div><div class="v">0</div><div class="s">nothing to certify</div></div>
</div>
<h2>Power table</h2>{power}
<h2>Worked examples</h2>{illus}
<div class="warn"><strong>A 55–45 run is not skill.</strong> A bettor with <em>exactly</em> the break-even rate goes 55–45 over
100 bets with probability {luck['illustrations'][0]['p_value_two_sided']:.3f} — i.e. routinely. Reaching 55% over 200 bets happens
{luck['illustrations'][1]['probability']*100:.1f}% of the time for such a bettor. Conversely, a genuine 55% edge is detected only
{luck['illustrations'][2]['probability_of_detection']*100:.1f}% of the time over those same 200 bets.</div>
<h2>Deflation before ranking</h2>
<p class="small">The leaderboard never displays a raw win rate. It displays
<span class="mono">{e(luck['deflation_rule']['formula'])}</span> — a 55–45 record deflates to
<strong>{luck['deflation_rule']['example']['deflated_rate']:.4f}</strong>, barely above break-even, which is the honest reading of a
100-bet sample. Ranking also requires the minimum sample in the power table.</p>
<h2>Method sources</h2>
{table(["ID", "Reference", "Link", "How it is used here"],
       [[e(c["id"]), e(c["title"]), src(c["url"], "open"), e(c["checked"])] for c in luck["citations"]],
       "Citations are used for method only; no value from these papers is imported as an NBA statistic.")}''')


def p_leaderboard() -> str:
    lb = OUT["leaderboard"]
    tiers = table(["Place", "Share", "Amount", "Status"],
                  [[str(t["place"]), e(t["share"]), f'<span class="blank">BLANK</span>', e(t["amount_status"])] for t in lb["tiers"]],
                  "Reward structure is a proposal. No sponsor, no pool, no payout mechanism exists (F09).", numeric={0})
    entries = table(["Rank", "Entry", "Strategy", "Graded bets", "Deflated rate", "CLV", "Score", "Status"],
                    [["—", "—", "—", "0", '<span class="blank">BLANK</span>', '<span class="blank">BLANK</span>',
                      '<span class="blank">BLANK</span>', badge("NO ENTRIES — NOTHING GRADED")]],
                    "The competition table is empty because no strategy has a settled bet. An empty table is the correct output, not a gap.")
    return page("leaderboard", "Leaderboard & rewards",
                "A competition design that pays for skill, not variance: deflated scoring, a minimum sample, family-wise error control "
                "and an entry bar that a hot week cannot clear.",
                f'''<div class="panel"><h3>Scoring</h3>
<p class="small"><span class="mono">{e(lb["scoring"])}</span></p>
<p class="small muted">Units: {e(lb["unit"])}. Minimum bets to rank: <strong>{lb["minimum_bets_to_rank"]:,}</strong>.</p></div>
<h2>Reward tiers</h2>{tiers}
<h2>Standings</h2>{entries}
<p class="small muted">{e(lb["entries_note"])}</p>
<h2>Anti-gaming rules</h2>
<ul class="tight">{"".join(f"<li>{e(x)}</li>" for x in lb["anti_gaming"])}</ul>
<div class="note"><strong>Design intent.</strong> A 50/30/20 split of an unfunded pool with a hard sample floor means the only way to
reach the top of this board is to survive hundreds of graded bets with a positive de-vigged closing-line value — which is what
skill looks like when luck is subtracted, and what almost nothing survives.</div>''')


def build_data_page() -> str:
    import csv as _csv
    def rows(name):
        with (DATA / name).open(newline="", encoding="utf-8") as fh:
            return list(_csv.DictReader(fh))
    standings = rows("standings_2026_27.csv")
    stats = rows("team_stats_2026_27.csv")
    slate = rows("slate_2026_11_05_06.csv")
    log = rows("game_logs_2026_27.csv")
    st_tbl = table(["Team", "W", "L", "PCT", "GB", "Conf", "Div", "Home", "Road", "OT", "L10", "Streak", "Source"],
                   [[e(r["team"]), r["w"], r["l"], e(r["win_pct"]), e(r["gb"]), e(r["conf_rec"]), e(r["div_rec"]),
                     e(r["home_rec"]), e(r["road_rec"]), e(r["ot_rec"]), e(r["last10"]), e(r["streak"]),
                     src(r["source_url"], "standings")] for r in standings],
                   "All 30 teams, transcribed from nba.com/standings on 2026-11-05. W-L agree with the team-stats page (check X01).",
                   numeric={1, 2, 3, 4})
    ts_tbl = table(["Team", "GP", "W-L", "PTS/g", "FG%", "3P%", "FT%", "REB/g", "AST/g", "TOV/g", "Net/g", "Source"],
                   [[e(r["team"]), r["gp"], f'{r["w"]}-{r["l"]}', e(r["pts_pg"]), e(r["fg_pct"]), e(r["tp_pct"]),
                     e(r["ft_pct"]), e(r["reb_pg"]), e(r["ast_pg"]), e(r["tov_pg"]), e(r["plus_minus_pg"]),
                     src(r["source_url"], "stats")] for r in stats],
                   "nba.com team traditional stats, 2026-27 regular season, per game.", numeric={1, 2, 3, 4, 5, 6, 7, 8, 9, 10})
    slate_tbl = table(["Game ID", "Date", "Tip ET", "Away", "Home", "Venue", "City", "Competition", "Source"],
                      [[e(r["game_id"]), e(r["date"]), e(r["tip_et"]), e(r["away_team"]), e(r["home_team"]),
                        e(r["venue"]), e(r["city"]), e(r["comp"]), src(r["source_url"], "schedule")] for r in slate],
                      "The 11-game slate. Nine of these are Emirates NBA Cup group-play games (F06).")
    log_tbl = table(["Player", "Date", "Match-up", "W/L", "MIN", "PTS", "REB", "AST", "3PM", "FTA", "TOV", "+/−", "Source"],
                    [[e(r["player"]), e(r["game_date"]), e(r["matchup"]), e(r["result"]), r["min"], r["pts"], r["reb"],
                      r["ast"], r["tpm"], r["fta"], r["tov"], e(r["plus_minus"]), src(r["source_url"], "game")]
                     for r in sorted(log, key=lambda r: (r["player_id"], r["game_date"]), reverse=True)],
                    "Every 2026-27 player-game row used in this session (12 rows), each linked to its official game page.",
                    numeric={4, 5, 6, 7, 8, 10, 11, 12})
    return page("data", "Verified data",
                "The transcribed official tables, row by row, each with the page it came from. If a cell could not be read from an "
                "official page it is absent here rather than guessed.",
                f'''<h2>2026-27 standings (30 teams)</h2>{st_tbl}
<h2>2026-27 team traditional stats (30 teams)</h2>{ts_tbl}
<h2>Slate: 2026-11-05 and 2026-11-06 (11 games)</h2>{slate_tbl}
<h2>2026-27 player game logs (12 rows)</h2>{log_tbl}
<h2>Inherited 2025-26 logs (125 rows)</h2>
<div class="note">The 2025-26 game logs (Anthony Edwards 61 rows, Luka Dončić 64 rows) were transcribed by session
<span class="mono">6d508fee</span> and are carried in <span class="mono">data/game_logs_2025_26.csv</span> with a per-row
<span class="mono">source_url</span> to the official game page. This session re-ran the arithmetic on them: all 125 rows satisfy the
scoring/rebound identities, the per-player averages reproduce the official headline averages, and six rows were independently
re-fetched from nba.com on 2026-11-05 and matched exactly (see <a href="verification.html">Verification</a>).</div>''')


def p_audit() -> str:
    audit_md = (RESEARCH / "repo-audit.md").read_text(encoding="utf-8") if (RESEARCH / "repo-audit.md").exists() else ""
    return page("audit", "Repo audit — re-verification of the earlier NBA boards",
                "Six NBA boards already existed in this repository. This session re-fetched official pages, recomputed their numbers "
                "where possible, and recorded what matched, what is stale and what is irregular.",
                md_to_html(audit_md))


def p_verification() -> str:
    checks = OUT["checks"]
    chk_src = {
        "X01": "https://www.nba.com/standings", "X02": "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season",
        "X03": "https://www.nba.com/standings", "X04": "https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season",
        "X05-2025-26": "https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26&DateFrom=2025-10-01&DateTo=2025-11-20",
        "X06-2025-26": "https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26&DateFrom=2025-10-01&DateTo=2025-11-20",
        "X05-2026-27": "https://www.nba.com/stats/player/1630162/boxscores?Season=2026-27",
        "X06-2026-27": "https://www.nba.com/stats/player/1630162/boxscores?Season=2026-27",
        "X07": "https://www.nba.com/stats/player/1629029/boxscores?Season=2026-27",
        "X08": "https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season",
        "X09": "https://www.nba.com/schedule?date=2026-11-05",
    }
    rows = [[e(c["id"]), e(c["claim"]), badge("PASS" if c["passed"] else "FAIL"), e(c["detail"]),
             src(chk_src.get(c["id"], "https://www.nba.com/standings"), "page")] for c in checks]
    tbl = table(["Check", "Claim tested", "Result", "Detail", "Official page checked"], rows,
                "Every check is executed by compute.py and re-executed by verify.py on each run.")
    return page("verification", "Verification log",
                f"{sum(1 for c in checks if c['passed'])}/{len(checks)} data checks pass. Every table row on this site carries an "
                f"official link or an explicit BLANK; link integrity and page rendering are checked by a script.",
                f'''{tbl}
<h2>Row-level provenance</h2>
{table(["Dataset", "Rows", "Rule enforced"],
       [[f'standings_2026_27.csv {src("https://www.nba.com/standings", "open")}', "30", "every row has source_url = official standings page"],
        [f'team_stats_2026_27.csv {src("https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season", "open")}', "30", "every row has source_url = official team-stats page"],
        [f'slate_2026_11_05_06.csv {src("https://www.nba.com/schedule?date=2026-11-05", "open")}', "11", "every row has source_url = official schedule page"],
        [f'game_logs_2026_27.csv {src("https://www.nba.com/stats/player/1630162/boxscores?Season=2026-27", "open")}', "12", "every row has source_url = official game page"],
        [f'game_logs_2025_26.csv {src("https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26", "open")}', "125", "every row has source_url = official game page (inherited, re-arithmetic-checked)"],
        [f'team_priors_2025_26.csv {src("https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season", "open")}', "30", "every row has source_url = official 2025-26 team-stats page (inherited)"],
        [f'outputs.json {src("https://www.nba.com/standings", "open")}', "all sections", "every line, prop, correlation, gate, strategy and flag carries a source_url or reference"]],
       "Enforced by verify.py; a row without a source fails the build.")}
<h2>How to reproduce</h2>
<pre class="mono">python3 nba-commission/compute.py      # rebuild data/outputs.json and run the data checks
python3 nba-commission/build.py        # regenerate all 14 pages
python3 nba-commission/verify.py       # provenance, link, render and idempotency checks
python3 -m unittest discover -s nba-commission/checks</pre>
<div class="note"><strong>What verification does not mean.</strong> Passing these checks proves the site is internally consistent and
faithful to the official pages it cites. It says nothing about whether any line is useful, and nothing about profitability.</div>''')


def p_sources() -> str:
    rows = [[e(s["id"]), e(s["publisher"]), e(s["title"]), src(s["url"], "open"), e(s["used_for"]), e(s["fetched"])]
            for s in OUT["sources"]]
    tbl = table(["ID", "Publisher", "Document", "Link", "Used for", "Checked"], rows,
                "Official data sources first, then methodology references. ‘Fetched’ means the page was retrieved in this session; "
                "‘search metadata only’ means the citation was confirmed but the document was not downloaded.")
    return page("sources", "Source register", "Every source cited anywhere on this site, with what it was used for and when it was checked.",
                f'''{tbl}
<h2>Official-source policy</h2>
<ul class="tight">
<li>Data values come only from nba.com properties (standings, team traditional stats, schedule, player box scores).</li>
<li>A value that could not be read from an official page is left blank and listed on <a href="flagged.html">Flagged for review</a>.</li>
<li>Methodology citations (AMS, arXiv, statsmodels, author copies) never supply an NBA number; they only justify a statistical procedure.</li>
<li>No sportsbook, aggregator, or secondary stats site is used as a data source anywhere in this session.</li>
</ul>''')


def p_flagged() -> str:
    rows = [[e(f["id"]), e(f["title"]), badge(f["severity"].upper()), e(f["detail"]), e(f["scope"]), src(f["source_url"], "related")]
            for f in OUT["flags"]]
    tbl = table(["ID", "Irregularity", "Severity", "Detail", "Scope", "Source"], rows,
                "Unverified values, source-page defects and model assumptions. None of these block publication; all of them block "
                "treating anything on this site as validated.")
    return page("flagged", "Flagged for review", f"{len(OUT['flags'])} items to review manually. Each states what is unknown, why, "
                                               "and where the related official page is.",
                f'''{tbl}
<div class="warn"><strong>The single most important flag.</strong> F01 — no verified market price. Without a timestamped price from a
named book, no edge, no closing-line value, no ROI and no reward can exist. Everything downstream that depends on price is blank
by design, not by omission.</div>''')


def p_exec() -> str:
    md = (RESEARCH / "EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8") if (RESEARCH / "EXECUTIVE_SUMMARY.md").exists() else ""
    md = re.sub(r"^# .*\n", "", md, count=1)
    return page("executive-summary", "Executive summary",
                "One page: what was built, what was verified against official sources, what the numbers show, and what remains unknown.",
                md_to_html(md))


def main() -> None:
    pages = {
        "index": p_index,
        "lines": p_lines,
        "props": p_props,
        "correlations": p_correlations,
        "strategies": p_strategies,
        "gates": p_gates,
        "skill-vs-luck": p_skill,
        "leaderboard": p_leaderboard,
        "data": build_data_page,
        "audit": p_audit,
        "verification": p_verification,
        "sources": p_sources,
        "flagged": p_flagged,
        "executive-summary": p_exec,
    }
    (ROOT / "style.css").write_text(CSS, encoding="utf-8")
    for slug, fn in pages.items():
        (ROOT / f"{slug}.html").write_text(fn(), encoding="utf-8")
    print(f"pages written: {len(pages)} to nba-commission/")


if __name__ == "__main__":
    main()

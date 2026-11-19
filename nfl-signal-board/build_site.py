"""NFL Signal Board — deterministic static site build (session 1fab8a48).

Every page is generated from data/nfl-signal-board/*.csv. No JS is needed to read content.
Every table row prints a source link. Values that could not be confirmed are blank and carry
an explicit blank reason, so a blank is never mistaken for a zero.
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "nfl-signal-board"
OUT = HERE

CSS = """
:root{--bg:#0b0f14;--panel:#121922;--ink:#e8eef6;--dim:#93a4b8;--line:#243040;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--accent:#58a6ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header{background:linear-gradient(180deg,#101823,#0b0f14);border-bottom:1px solid var(--line);padding:18px 20px}
header .wrap{max-width:1180px;margin:0 auto}
h1{font-size:21px;margin:0 0 4px;letter-spacing:-.2px}
.sub{color:var(--dim);font-size:13px}
nav{max-width:1180px;margin:0 auto;padding:10px 20px;display:flex;flex-wrap:wrap;gap:6px;border-bottom:1px solid var(--line)}
nav a{padding:5px 10px;border:1px solid var(--line);border-radius:999px;font-size:13px;color:var(--dim);background:#0f151d}
nav a.on{color:#0b0f14;background:var(--accent);border-color:var(--accent);font-weight:600}
main{max-width:1180px;margin:0 auto;padding:22px 20px 60px}
h2{font-size:17px;margin:30px 0 6px;padding-top:8px;border-top:1px solid var(--line)}
h2:first-child{border-top:0;margin-top:6px}
h3{font-size:14px;margin:18px 0 6px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}
p{color:#c9d6e5;max-width:76ch}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:10px;margin:12px 0 6px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.card .v{font-size:22px;font-weight:700;letter-spacing:-.4px}
.card .k{font-size:11.5px;color:var(--dim);text-transform:uppercase;letter-spacing:.05em;margin-top:2px}
.card.ok .v{color:var(--ok)}.card.warn .v{color:var(--warn)}.card.bad .v{color:var(--bad)}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin:10px 0 4px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13.2px}
th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#16202b;color:var(--dim);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;position:sticky;top:0}
tbody tr:hover{background:#161f2a}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
tr.blank td{color:#6d7e91;font-style:italic}
.tag{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;font-weight:600;white-space:nowrap}
.t-met{background:#0d2f16;color:var(--ok);border:1px solid #1d5c2b}
.t-part{background:#332508;color:var(--warn);border:1px solid #6b4e12}
.t-block{background:#3a1114;color:var(--bad);border:1px solid #7d1f24}
.t-info{background:#0d2137;color:var(--accent);border:1px solid #1d4a7d}
.t-gray{background:#1a2330;color:var(--dim);border:1px solid var(--line)}
.hero{background:linear-gradient(135deg,#12202f,#0e1621);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:10px 0 4px}
.hero .big{font-size:30px;font-weight:800;letter-spacing:-.8px}
.hero .neg{color:var(--bad)}
.note{font-size:12.5px;color:var(--dim);margin:6px 0 0}
.callout{border-left:3px solid var(--warn);background:#191307;padding:10px 14px;border-radius:0 8px 8px 0;margin:12px 0}
.callout.bad{border-color:var(--bad);background:#1b0d0e}
.callout.ok{border-color:var(--ok);background:#0c1a10}
footer{max-width:1180px;margin:0 auto;padding:24px 20px;color:var(--dim);font-size:12px;border-top:1px solid var(--line)}
.skip{position:absolute;left:-9999px}
@media(max-width:700px){.cards{grid-template-columns:repeat(2,1fr)}th,td{padding:6px 7px;font-size:12.4px}main{padding:16px 12px 50px}nav{padding:8px 12px}header{padding:14px 12px}}
"""

NAV = [
    ("index.html", "Overview"),
    ("readiness.html", "Decision readiness"),
    ("origination.html", "Origination &amp; prices"),
    ("model.html", "Model &amp; luck panel"),
    ("leaderboard.html", "Leaderboard &amp; pre-registration"),
    ("availability.html", "Availability &amp; depth"),
    ("correlations.html", "Correlations"),
    ("results.html", "Results &amp; corpus"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("research.html", "Research register"),
    ("flagged.html", "Flagged for review"),
    ("method.html", "Method &amp; sources"),
]


def load(name: str) -> list[dict]:
    p = DATA / f"{name}.csv"
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def site_url(path: str) -> str:
    return "https://github.com/sassnarep3-star/Own5/blob/main/" + path


def page(slug: str, title: str, body: str, sub: str = "") -> None:
    nav = "".join(
        f'<a href="{h}"{" class=on" if h == slug else ""}>{n}</a>' for h, n in NAV
    )
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — Own5 NFL Signal Board</title>
<meta name="description" content="Official-source NFL line origination, decision readiness, luck-removal panel and pre-registered strategy register. Every row is source-linked or blank-and-flagged.">
<style>{CSS}</style></head>
<body>
<header><div class="wrap">
<h1>Own5 · NFL Signal Board</h1>
<div class="sub">Session <code>1fab8a48</code> · official-source verification 2026-11-19 UTC · every table row is source-linked, and any value that could not be confirmed is
<strong>left blank and flagged</strong>, never inferred. {sub}</div>
</div></header>
<nav>{nav}</nav>
<main>
<h2>{esc(title)}</h2>
{body}
</main>
<footer>
<p>Policy P-01: the public site carries derived aggregates, our own model outputs and operator-attributed prices only; row-level official data stays private.
No bets are placed, no performance is claimed, and no strategy on this site is certified. This is research, not betting advice.
Own5 is a multi-session repository: this board is one additive desk and links to the others from the <a href="method.html">Method &amp; sources</a> page.</p>
</footer>
</body></html>
"""
    (OUT / slug).write_text(doc, encoding="utf-8")


def table(headers: list[tuple[str, str]], rows: list[list[str]], cls: str = "", blank_rows: set[int] | None = None) -> str:
    """headers: (label, css-class). rows: already-escaped cell html."""
    blank_rows = blank_rows or set()
    th = "".join(f'<th class="{c}">{h}</th>' for h, c in headers)
    body = []
    for i, r in enumerate(rows):
        klass = ' class="blank"' if i in blank_rows else ""
        body.append(f"<tr{klass}>" + "".join(f'<td class="{headers[j][1]}">{c}</td>' for j, c in enumerate(r)) + "</tr>")
    return f'<div class="tw"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def src(url: str, label: str = "source ↗") -> str:
    if not url:
        return '<span class="tag t-gray">no source</span>'
    return f'<a href="{esc(url)}" rel="noopener">{label}</a>'


def chip(status: str) -> str:
    s = status.upper()
    if s.startswith("MET"):
        return f'<span class="tag t-met">{esc(status)}</span>'
    if s.startswith("PARTIAL"):
        return f'<span class="tag t-part">{esc(status)}</span>'
    if s.startswith("BLOCKED"):
        return f'<span class="tag t-block">{esc(status)}</span>'
    return f'<span class="tag t-gray">{esc(status)}</span>'


# --------------------------------------------------------------------------- pages
def build_index():
    reqs = load("requirements")
    metrics = load("model_metrics")
    summary = json.loads((DATA / "derive_summary.json").read_text())
    h = summary["headline"]
    m = summary["model"]
    counts = summary["counts"]
    met = sum(1 for r in reqs if r["status"] == "MET")
    part = sum(1 for r in reqs if r["status"] == "PARTIAL")
    blocked = sum(1 for r in reqs if r["status"] == "BLOCKED")
    flags = load("flagged")
    side_all = next(r for r in metrics if r["model_id"] == "M1 all 2015-2026")
    ml_all = next(r for r in metrics if r["model_id"] == "M3 all 2015-2026")
    calib = m["calibration"]

    body = f"""
<div class="hero">
  <div class="sub">The headline, unsoftened</div>
  <div class="big neg">The model does not beat the market.</div>
  <p>On {int(side_all['n']):,} priced games from 2015 to 2026, our side probability scores a
  <strong>Brier skill of {esc(side_all['brier_skill'])}</strong> against a coin flip at the closing line
  (95% cluster interval {esc(side_all['ci_low'])} to {esc(side_all['ci_high'])}). The moneyline scores
  <strong>{esc(ml_all['brier_skill'])}</strong> against the de-vigged close. The calibration slope on train is
  <strong>{calib['slope']:.3f}</strong>: the raw probabilities are badly over-confident, so the raw edges on the
  origination page (up to +0.76 EV per unit) are an artefact and <strong>no stake is taken from any of them</strong>.</p>
  <p class="note">That is the useful result. It is published first because a site that hides it is worse than no site.
  All {counts['origination_rows']} market rows, {counts['fixtures']} fixtures and {counts['operator_prices']} operator prices are below with clocks and links.</p>
</div>

<div class="cards">
  <div class="card"><div class="v">{counts['fixtures']}</div><div class="k">Week 11 fixtures originated</div></div>
  <div class="card"><div class="v">{counts['origination_rows']}</div><div class="k">market rows (side → total → ML)</div></div>
  <div class="card"><div class="v">{counts['operator_prices']}</div><div class="k">operator prices read today</div></div>
  <div class="card ok"><div class="v">{summary['reconciliation']['clubs_reconciled']}/32</div><div class="k">clubs reconcile to standings</div></div>
  <div class="card"><div class="v">{counts['injury_rows']}</div><div class="k">injury-report rows captured</div></div>
  <div class="card bad"><div class="v">0</div><div class="k">certified strategies</div></div>
</div>
<div class="cards">
  <div class="card"><div class="v">{met}</div><div class="k">requirements met</div></div>
  <div class="card warn"><div class="v">{part}</div><div class="k">partial</div></div>
  <div class="card bad"><div class="v">{blocked}</div><div class="k">blocked</div></div>
  <div class="card"><div class="v">{len(flags)}</div><div class="k">flagged for review</div></div>
  <div class="card"><div class="v">{counts['questions']}</div><div class="k">questions needing answers</div></div>
  <div class="card"><div class="v">{counts['suggestions']}</div><div class="k">reviewable suggestions</div></div>
</div>

<h2>What you can decide today, and what blocks the rest</h2>
<p>One row per requirement in the brief. Each row carries the gate that blocks it and the number that would clear it.
The full table, with the observed value on every row, is on the <a href="readiness.html">Decision readiness</a> page.</p>
"""
    focus = ["R02", "R03", "R04", "R09", "R15", "R16", "R19", "R36"]
    rows = []
    for r in reqs:
        if r["id"] not in focus:
            continue
        rows.append([esc(r["id"]), esc(r["requirement"]), chip(r["status"]),
                     esc(r["blocking_gate"]), esc(r["number_that_would_clear_it"]), esc(r["observed"]),
                     src(r["source_url"])])
    body += table([("ID", ""), ("Requirement", ""), ("Status", ""), ("Gate that blocks it", ""),
                   ("Number that would clear it", ""), ("Observed today", ""), ("Source", "")], rows)

    body += f"""
<h2>How to read this board</h2>
<div class="cards">
  <div class="card"><div class="v">1</div><div class="k"><a href="origination.html">Origination &amp; prices</a> — fair, market and the difference as separate columns, with the read clock</div></div>
  <div class="card"><div class="v">2</div><div class="k"><a href="model.html">Model &amp; luck panel</a> — the walk-forward scores, calibration, controls and the removal-of-luck panel</div></div>
  <div class="card"><div class="v">3</div><div class="k"><a href="leaderboard.html">Leaderboard</a> — signal and staking kept apart; every strategy starts at 0 settled bets</div></div>
  <div class="card"><div class="v">4</div><div class="k"><a href="availability.html">Availability &amp; depth</a> — what the official report says, and what it cannot tell us</div></div>
  <div class="card"><div class="v">5</div><div class="k"><a href="questions.html">Questions</a> — the information we do not have, with a discovery route for each</div></div>
  <div class="card"><div class="v">6</div><div class="k"><a href="flagged.html">Flagged for review</a> — every irregularity and every unverified blank, with links</div></div>
</div>

<div class="callout bad">
<strong>Three things this board refuses to do.</strong>
It does not put a backtest figure on the leaderboard. It does not name a replacement starter without an official inactive list or game book.
It does not publish a percentage for what "Questionable" means, because the join that would measure it has not been run.
</div>

<h2>The honest state of each pillar</h2>
"""
    pillars = [
        ("Line origination", "side → total → moneyline for 13 fixtures, fair / market / difference in separate columns, a sha256 of the exact inputs on every row",
         f"{counts['origination_rows']} rows", "PARTIAL — the market column is one operator, and no price is stakeable while the calibration slope is 0.11"),
        ("Results corpus", "the pinned 1999–2026 game corpus reconciled to today's official standings, plus an audit of the 136-row log the brief names",
         f"{summary['reconciliation']['clubs_reconciled']}/32 clubs, {counts['log_rows']} log rows audited", "MET for the 2026 season to date"),
        ("Luck removal", "proper scores with a week-cluster bootstrap, two control baselines, and a published count of how many bets a win rate needs",
         f"n={int(side_all['n']):,}", "MET — and it says the model loses"),
        ("Strategy competition", "8 pre-registered strategies, 4 divisions, signal and staking separated, a two-sided change-our-mind field",
         "0 settled bets", "BLOCKED until 300+ bets settle per division"),
        ("Availability &amp; depth", "253 official report rows across 24 clubs, counted and stamped; no replacement is named",
         f"{counts['designated']} game-status cells", "BLOCKED — the inactive list and game book are not held"),
        ("Correlations", "computed from today's official standings only, n printed on every coefficient",
         "4 coefficients, n=32", "PARTIAL — these are team-level, not parlay-leg, correlations"),
    ]
    body += table([("Pillar", ""), ("What is actually built", ""), ("Scale", "num"), ("Verdict", "")],
                  [[esc(a), esc(b), esc(c), esc(d)] for a, b, c, d in pillars])

    body += """
<div class="callout">
<strong>Scope note.</strong> This repository already contains 50+ prior desks built by parallel sessions. This board is additive and does not
edit their files. Where an earlier desk's claim and an official page disagree, the official page wins and the disagreement is listed on
<a href="flagged.html">Flagged for review</a>. Where two desks disagree with each other, both are recorded and neither is adopted here.
</div>
"""
    page("index.html", "Overview", body, "Start here.")


def build_readiness():
    reqs = load("requirements")
    counts = {}
    for r in reqs:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    body = f"""
<p>One row per line of the brief. The three decision columns are the point of the table: <strong>what blocks it</strong>,
<strong>the number that would clear it</strong>, and <strong>the value observed today</strong>. A row is
<span class="tag t-met">MET</span> only when the observed value already clears its own number.</p>
<div class="cards">
"""
    for k in ("MET", "PARTIAL", "BLOCKED"):
        body += f'<div class="card"><div class="v">{counts.get(k,0)}</div><div class="k">{k.lower()}</div></div>'
    body += f'<div class="card"><div class="v">{len(reqs)}</div><div class="k">total rows</div></div></div>'

    cats = []
    for r in reqs:
        if r["category"] not in cats:
            cats.append(r["category"])
    for c in cats:
        sub = [r for r in reqs if r["category"] == c]
        rows = [[esc(r["id"]), esc(r["requirement"]), chip(r["status"]), esc(r["blocking_gate"]),
                 esc(r["number_that_would_clear_it"]), esc(r["observed"]), src(r["source_url"])] for r in sub]
        body += f"<h3>{esc(c)} · {len(sub)} rows</h3>"
        body += table([("ID", ""), ("Requirement", ""), ("Status", ""), ("Blocking gate", ""),
                       ("Number that would clear it", ""), ("Observed today", ""), ("Source", "")], rows)
    body += """
<div class="callout">
<strong>Reading the status.</strong> <span class="tag t-met">MET</span> means the observed value clears the stated number.
<span class="tag t-part">PARTIAL</span> means something real exists but a named piece is missing.
<span class="tag t-block">BLOCKED</span> means an input or a decision is missing and no substitute value was invented to fill the gap.
</div>
"""
    page("readiness.html", "Decision readiness", body, "Requirement → gate → clearing number → observed value.")


def build_origination():
    orig = load("origination")
    snaps = load("price_snapshots")
    summary = json.loads((DATA / "derive_summary.json").read_text())
    h = summary["headline"]
    fixtures = []
    for o in orig:
        if o["fixture_id"] not in [f[0] for f in fixtures]:
            fixtures.append((o["fixture_id"], o["away"], o["home"], o["kickoff_et"]))

    body = f"""
<p>Thirteen Week 11 fixtures, originated in the brief's dependency order: <strong>side</strong> first, then <strong>total</strong>,
then <strong>moneyline</strong>. The model's own line, the operator's printed line and the difference between them sit in
three separate columns, and every row carries a sha256 over the exact inputs that produced its probability.</p>
<div class="callout bad">
<strong>No stake is taken from these rows.</strong> The calibration slope fitted on the training window is
<strong>{summary['model']['calibration']['slope']:.3f}</strong> (n={summary['model']['calibration']['n']}). A slope far below 1 means the raw
probabilities are over-confident, so a raw edge of +0.7 EV is not a real edge. The <em>calibrated</em> probability is printed beside the raw one so
the shrinkage is visible rather than hidden.
</div>
<div class="cards">
  <div class="card"><div class="v">{len(fixtures)}</div><div class="k">fixtures</div></div>
  <div class="card"><div class="v">{len(orig)}</div><div class="k">market rows</div></div>
  <div class="card"><div class="v">{sum(1 for o in orig if o['market_line'])}</div><div class="k">rows with an operator price</div></div>
  <div class="card bad"><div class="v">0</div><div class="k">rows cleared for staking</div></div>
</div>
"""
    for fid, away, home, ko in fixtures:
        sub = [o for o in orig if o["fixture_id"] == fid]
        rows = []
        for o in sub:
            rows.append([esc(o["market_order"]), esc(o["market"]), esc(o["selection"]),
                         esc(o["fair_line"]), esc(o["market_line"]), esc(o["difference_fair_minus_market"]),
                         esc(o["fair_prob"]), esc(o["fair_prob_calibrated"]), esc(o["market_prob_devig"]),
                         esc(o["ev_per_unit"]), esc(o["stake_signal"].split(" | ")[0]),
                         esc(o["price_read_utc"]), src(o["price_source_url"], "operator ↗")])
        body += f"<h3>{esc(away)} at {esc(home)} · {esc(fid)} · kickoff {esc(ko)}</h3>"
        body += table([("Order", ""), ("Market", ""), ("Selection", ""), ("Fair line (ours)", "num"),
                       ("Market line (operator)", "num"), ("Diff fair−market", "num"),
                       ("Fair prob", "num"), ("Fair prob calibrated", "num"), ("Market prob (de-vigged)", "num"),
                       ("EV per unit (uncalibrated)", "num"), ("Stake signal", ""), ("Price read (UTC)", "mono"), ("Source", "")], rows)

    body += """
<h2>Price-snapshot store</h2>
<p>Every originated market has a stored opening snapshot with the operator, the printed price and its read clock.
The closing column is deliberately empty: a close can only be read at kickoff, and a close is never inferred from an earlier read.</p>
"""
    rows = [[esc(s["snapshot_id"]), esc(s["operator"]), esc(s["market"]), esc(s["selection"]),
             esc(s["open_value"]), esc(s["open_read_utc"]) or '<span class="tag t-gray">not read</span>',
             esc(s["close_value"]) or '<span class="tag t-part">PENDING at kickoff</span>',
             esc(s["close_status"]), src(s["source_url"], "operator ↗")] for s in snaps]
    body += table([("Snapshot", "mono"), ("Operator", ""), ("Market", ""), ("Selection", ""), ("Open (as printed)", ""),
                   ("Open read (UTC)", "mono"), ("Close", ""), ("Close status", ""), ("Source", "")], rows)

    body += f"""
<h2>Inputs behind every number</h2>
<p>Each row's <code>model_inputs</code> field holds the full input dictionary (Elo difference, the fitted intercept and slope,
the offence and defence rates for both clubs, the dispersion parameters and the sigma variant) and <code>inputs_sha256</code> is the
sha256 of that exact string. The row data is at
<a href="{site_url('data/nfl-signal-board/origination.csv')}">origination.csv</a>; the model constants are frozen in
<a href="{site_url('data/nfl-signal-board/preregistration.json')}">preregistration.json</a>.</p>
<div class="callout">
<strong>What the market column is.</strong> One operator's live board, attributed by name, read at {esc(h['operator_prices'])} prices at 11:10 UTC.
It is not a consensus: a one-book "consensus" would be a fiction, so the consensus columns are blank and the gap is flagged (SBF-12).
</div>
"""
    page("origination.html", "Origination &amp; prices", body, "Side → total → moneyline; the market column carries the operator and the clock.")


def build_model():
    metrics = load("model_metrics")
    calib_rows = load("calibration")
    luck = load("luck")
    summary = json.loads((DATA / "derive_summary.json").read_text())
    m = summary["model"]
    body = f"""
<p>The evaluation is walk-forward: a rating and a scoring model are updated game by game, and each forecast is made before the result is seen.
Tuning reads only the training window (2015–2024). The holdout (2025–2026) is scored once and never used to choose anything.</p>

<h2>1. Proper scores</h2>
<p><strong>Side benchmark.</strong> A spread bet is a coin flip at the closing line by construction: the operator sets the line at its own
median, so P(cover) is 0.5 before the vig. That makes 0.5 the assumption-free benchmark, and it is what the model is scored against.
<strong>Moneyline benchmark.</strong> The de-vigged closing moneyline. <strong>Totals.</strong> The pinned corpus carries closing totals but no
over/under prices, so no market probability can be formed; the total is therefore scored on point error and is explicitly not comparable to the
probability scores.</p>
"""
    rows = []
    for r in metrics:
        cls = "t-block" if r["certified"].startswith("NO") else ("t-gray" if r["certified"].startswith("CONTROL") else "t-part")
        rows.append([esc(r["model_id"]), esc(r["description"]), esc(r["n"]), esc(r["brier_model"]), esc(r["brier_market"]),
                     esc(r["brier_skill"]), esc(r["ci_low"]), esc(r["ci_high"]), esc(r["p_holm"]),
                     f'<span class="tag {cls}">{esc(r["certified"])}</span>', src(r["source_url"])])
    body += table([("Model", ""), ("What it scores", ""), ("n", "num"), ("Model score", "num"), ("Benchmark", "num"),
                   ("Skill / error gap", "num"), ("CI low", "num"), ("CI high", "num"), ("Holm p", "num"),
                   ("Certified?", ""), ("Source", "")], rows)
    body += f"""
<div class="callout bad">
<strong>{esc(m['calibration_note'])}</strong>
The practical consequence: a raw model probability of 0.92 is, on the evidence, closer to 0.55. Any staking that used the raw number
would be systematically too large — the exact failure mode the brief's "removal of luck" requirement exists to catch.
</div>

<h2>2. Calibration of the side model</h2>
<p>Predicted probability against the observed cover rate, all priced games. Perfect calibration is a gap of 0.000 in every bin.</p>
"""
    rows = [[esc(r["bin_low"]) + "–" + esc(r["bin_high"]), esc(r["n"]), esc(r["mean_predicted"]), esc(r["observed_rate"]),
             esc(r["gap"]), src(r["source_url"])] for r in calib_rows]
    body += table([("Predicted bin", ""), ("n", "num"), ("Mean predicted", "num"), ("Observed", "num"),
                   ("Gap", "num"), ("Source", "")], rows)

    body += """
<h2>3. The removal-of-luck panel</h2>
<p>Three separate questions, each answered with a number and its sample size rather than an opinion.</p>
"""
    last = None
    for r in luck:
        if r["panel"] != last:
            body += f"<h3>{esc(r['panel'])}</h3>"
            last = r["panel"]
        n = esc(r["n"]) or '<span class="tag t-gray">n/a</span>'
        body += (f'<div class="card" style="margin:8px 0"><div class="v" style="font-size:16px">{esc(r["statistic"])} — '
                 f'<strong>{esc(r["value"])}</strong></div>'
                 f'<div class="k">n={n} · clusters={esc(r["clusters"]) or "—"} · interval '
                 f'{esc(r["ci_low"]) or "—"} to {esc(r["ci_high"]) or "—"}</div>'
                 f'<p class="note">{esc(r["reads"])} · {src(r["source_url"])}</p></div>')

    body += f"""
<h2>4. What would have to change</h2>
<div class="tw"><table><thead><tr><th>Finding</th><th>What would overturn it</th></tr></thead><tbody>
<tr><td>Side skill of {esc(next(r['brier_skill'] for r in metrics if r['model_id']=='M1 all 2015-2026'))}</td>
<td>A model whose cluster lower bound on skill is above 0 out of sample. On this data the bound is
{esc(next(r['ci_low'] for r in metrics if r['model_id']=='M1 all 2015-2026'))}, so the answer is not "close".</td></tr>
<tr><td>Calibration slope {m['calibration']['slope']:.3f}</td>
<td>A refit with a richer feature set that moves the slope toward 1 on data the fit has not seen.</td></tr>
<tr><td>The {m['tot_bias']:.2f}-point total bias</td>
<td>A pre-registered 2026-only test whose interval spans zero. The hypothesis has already seen the holdout, so it needs a fresh registration.</td></tr>
</tbody></table></div>
"""
    page("model.html", "Model &amp; luck panel", body, "Proper scores, calibration and the controls that make a lucky run identifiable.")


def build_leaderboard():
    lb = load("leaderboard")
    prereg = load("prereg")
    body = """
<p>The leaderboard is a competition with gates, not a display of past performance. Two rules make it defensible:
<strong>signal and staking live in separate columns</strong>, so a lucky staking run cannot lift a bad signal; and
<strong>no backtest number ever appears here</strong> — a strategy earns a figure only by settling bets after its registration.</p>
<div class="callout">
<strong>Everyone starts at zero.</strong> There are no settled bets since registration, so every strategy is
<span class="tag t-block">UNCERTIFIED</span>. The ranking key, when numbers exist, is the <em>lower bound</em> of the skill interval,
not the point estimate, and never win rate or season-long ROI.
</div>
"""
    rows = []
    for r in lb:
        rows.append([esc(r["division"]), esc(r["strategy_id"]), esc(r["strategy"]),
                     esc(r["signal_stat"]), esc(r["signal_value"]) or "—",
                     f"{esc(r['signal_ci_low']) or '—'} to {esc(r['signal_ci_high']) or '—'}",
                     esc(r["staking_roi"]) or "—", esc(r["settled_bets"]) or "—",
                     esc(r["grade"]), esc(r["what_would_change_our_mind"]), esc(r["demotion_rule"]),
                     src(r["source_url"])])
    body += table([("Division", ""), ("ID", ""), ("Strategy", ""), ("Signal statistic", ""), ("Signal", "num"),
                   ("Signal CI", ""), ("Staking ROI", "num"), ("Settled", "num"), ("Grade", ""),
                   ("What would change our mind", ""), ("Demotion rule", ""), ("Source", "")], rows)

    body += """
<h2>Pre-registration register</h2>
<p>A strategy is registered by freezing its rule text, its sample window and its gates, hashing the frozen artifact, and committing that
hash before the evaluation window opens. The commit is the registration. Changing a rule requires a new registration id.</p>
"""
    rows = [[esc(p["registration_id"]), esc(p["strategy_id"]), esc(p["division"]), esc(p["rule_text"]),
             esc(p["sample_window"]), esc(p["gates"]), esc(p["frozen_utc"]),
             f'<code title="{esc(p["artifact_sha256"])}">{esc(p["artifact_sha256"][:16])}…</code>',
             src(p["source_url"])] for p in prereg]
    body += table([("Registration", "mono"), ("Strategy", ""), ("Division", ""), ("Rule text (frozen)", ""),
                   ("Sample window", ""), ("Gates", ""), ("Frozen (UTC)", "mono"), ("Artifact sha256", "mono"),
                   ("Source", "")], rows)

    body += """
<h2>Divisions and rewards</h2>
<div class="tw"><table><thead><tr><th>Division</th><th>Ranked by</th><th>Gate before any ranking</th><th>Status</th></tr></thead><tbody>
<tr><td>Single — side</td><td>lower bound of Brier skill vs a coin flip at the close</td><td>300+ settled bets, Holm across registered families</td><td><span class="tag t-block">0 settled</span></td></tr>
<tr><td>Single — total</td><td>lower bound of point-error skill, plus agreement of the two total estimators within 10%</td><td>300+ settled bets</td><td><span class="tag t-block">0 settled</span></td></tr>
<tr><td>Single — moneyline</td><td>lower bound of Brier skill vs the de-vigged close</td><td>300+ settled bets</td><td><span class="tag t-block">0 settled</span></td></tr>
<tr><td>Same-game parlay</td><td>joint-probability gap to the product of marginals</td><td>a directly validated joint probability + the operator's void rules</td><td><span class="tag t-block">blocked by design</span></td></tr>
<tr><td>Cross-game parlay</td><td>joint-probability gap</td><td>a measured cross-game correlation interval containing 0</td><td><span class="tag t-block">not started</span></td></tr>
<tr><td>Prop combo</td><td>fitted bivariate joint</td><td>a joint with published n</td><td><span class="tag t-block">blocked by design</span></td></tr>
<tr><td>Controls</td><td>not ranked</td><td>none — a control can never be certified</td><td><span class="tag t-gray">benchmark only</span></td></tr>
</tbody></table></div>
<p class="note">Reward amounts are not stated because the owner has not decided them. Stating a number would be an invention, so the
tier structure is described and the amount is a question (Q10).</p>
"""
    page("leaderboard.html", "Leaderboard &amp; pre-registration", body, "Signal and staking kept apart; nothing is ranked before it settles.")


def build_availability():
    depth = load("depth")
    summary = json.loads((DATA / "derive_summary.json").read_text())
    counts = summary["counts"]
    body = f"""
<p>The brief asks for a live picture of who is out, who replaces them, and how deep the replacement is. The official Week 11 report gives us
designations. It does <strong>not</strong> give us the inactive list, a named replacement, a depth order or a snap count. So the table below publishes
exactly what the official page prints, and leaves the replacement columns blank with the gate that would fill them.</p>
<div class="cards">
  <div class="card"><div class="v">{counts['injury_rows']}</div><div class="k">report rows captured</div></div>
  <div class="card"><div class="v">{counts['injury_clubs']}</div><div class="k">clubs with a table</div></div>
  <div class="card warn"><div class="v">{counts['designated']}</div><div class="k">rows with a game-status cell</div></div>
  <div class="card bad"><div class="v">0</div><div class="k">replacements named from an official source</div></div>
</div>
<div class="callout bad">
<strong>Why the replacement column is empty.</strong> A designation tells us a player is doubtful or out. It does not tell us who takes the snaps.
Naming a backup from a depth chart would be an inference the brief forbids, and the club depth pages are not a verified structured source for all
32 clubs. The gate is therefore explicit: an official inactive list plus announced-starter evidence (or a game book).
</div>
"""
    rows = []
    for d in depth:
        cls = "t-met" if d["gate_status"].startswith("GATE OPEN") else "t-block"
        rows.append([esc(d["club"]), esc(d["out_designated"]) or "—", esc(d["questionable_designated"]) or "—",
                     '<span class="tag t-gray">blank — no official source names one</span>',
                     esc(d["blocking_gate"]), esc(d["number_that_would_clear_it"]),
                     f'<span class="tag {cls}">{esc(d["gate_status"])}</span>', esc(d["note"]), src(d["source_url"])])
    body += table([("Club", ""), ("Out", "num"), ("Questionable", "num"), ("Replacement named", ""),
                   ("Blocking gate", ""), ("Number that would clear it", ""), ("Gate status", ""), ("Note", ""), ("Source", "")], rows)

    body += """
<h2>What the official print does and does not contain</h2>
<div class="tw"><table><thead><tr><th>Field the brief needs</th><th>On the official Week 11 report?</th><th>What this board does about it</th></tr></thead><tbody>
<tr><td>Injury and practice status</td><td>Yes — printed per player</td><td>Captured, counted and stamped with a read clock</td></tr>
<tr><td>Game designation (Out / Doubtful / Questionable)</td><td>Only on a minority of rows — the rest are blank on the official print</td><td>Blanks kept as blanks; the count of designated cells is published (16 of 253)</td></tr>
<tr><td>Who actually started</td><td>No — that is the game book</td><td>Not claimed. Flagged SBF-07</td></tr>
<tr><td>Official inactive list</td><td>No — published separately about 90 minutes before kickoff</td><td>Not captured. The capture job is added; nothing is backfilled</td></tr>
<tr><td>Depth order / slot rank</td><td>No — that is a club depth page</td><td>No depth order is published. Deriving it from jersey number, experience or salary is rejected</td></tr>
<tr><td>Snap counts</td><td>No</td><td>Not read. The playing-time route to depth is stated as the preferred one and blocked</td></tr>
<tr><td>Reserve / injured-reserve status</td><td>No</td><td>Not claimed. "Not listed" is never reported here as "available"</td></tr>
</tbody></table></div>
<div class="callout">
<strong>Two clubs read "No Injuries Reported".</strong> Cincinnati and Washington print that line for Week 11. It is reproduced as printed and is
<strong>not</strong> treated as evidence of health — the flag SBF-03 records it, and no model feature uses it.
</div>
"""
    page("availability.html", "Availability &amp; depth", body, "What the official report says, and the exact gate on everything it does not.")


def build_correlations():
    summary = json.loads((DATA / "derive_summary.json").read_text())
    stands = load("corpus_reconciliation")
    # compute the four official-source coefficients in-page from the standings already published
    rows = []
    import statistics
    pct = []; pf = []; pa = []
    for s in stands:
        g = s["w"] and (int(s["w"]) + int(s["l"]) + int(s["t"]))
        if not g:
            continue
        pct.append((int(s["w"]) + 0.5 * int(s["t"])) / g)
        pf.append(int(s["pf"]) / g)
        pa.append(int(s["pa"]) / g)

    def corr(a, b):
        ma, mb = statistics.mean(a), statistics.mean(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
        return num / den if den else None

    pairs = [
        ("Net points per game vs winning percentage", "NET/G", "PCT", corr([p - q for p, q in zip(pf, pa)], pct)),
        ("Points for per game vs winning percentage", "PF/G", "PCT", corr(pf, pct)),
        ("Points against per game vs winning percentage", "PA/G", "PCT", corr(pa, pct)),
        ("Points for per game vs points against per game", "PF/G", "PA/G", corr(pf, pa)),
    ]
    body = f"""
<p>Correlations are computed only from numbers on an official page, and <strong>n is printed with every value</strong>. The inputs here are today's
official league standings: 32 clubs, each with a record and points for/against. Nothing is imported from a third-party dataset.</p>
<div class="callout">
<strong>What these are not.</strong> They are team-level, season-to-date relationships. They are <em>not</em> parlay-leg correlations, and using them as
if they were is exactly the error the brief warns about: multiplying marginal probabilities is invalid when the legs are dependent. The leg-level
coefficient needs play-by-play, which is not held here (Q09).
</div>
"""
    rows = [[esc(a), esc(b), esc(c), f"{v:.4f}" if v is not None else "", "32", "the 2026 regular season to date, today's official standings",
             src("https://www.nfl.com/standings/league/2026/REG")] for a, b, c, v in pairs]
    body += table([("Relationship", ""), ("x", ""), ("y", ""), ("Pearson r", "num"), ("n", "num"), ("Window", ""), ("Source", "")], rows)

    body += """
<h2>Correlation rules used by this board</h2>
<div class="tw"><table><thead><tr><th>Rule</th><th>Why</th><th>Enforced where</th></tr></thead><tbody>
<tr><td>No value without n</td><td>A coefficient without a sample cannot be judged</td><td>This table; the verifier fails a row with a value and no n</td></tr>
<tr><td>No third-party inputs</td><td>The brief allows official numbers only</td><td>The four rows above read only the standings page</td></tr>
<tr><td>No leg correlation claimed without play-by-play</td><td>Marginal probabilities do not multiply under dependence</td><td>Same-game and cross-game parlays stay blocked</td></tr>
<tr><td>n is not rows of a table</td><td>The unit here is a club, not a table row</td><td>n counts clubs, and says so</td></tr>
</tbody></table></div>
"""
    page("correlations.html", "Correlations", body, "Only officially sourced numbers, with n on every coefficient.")


def build_results():
    recon = load("corpus_reconciliation")
    log = load("log136")
    summary = json.loads((DATA / "derive_summary.json").read_text())
    ls = summary["log136"]
    body = f"""
<p>A backtest is only as good as its results feed. This page shows the two checks that make the feed usable: every club's game-derived record
reconciled to the official standings, and the 136-row log named in the brief audited row by row.</p>

<h2>1. Corpus reconciliation: {summary['reconciliation']['clubs_reconciled']}/32 clubs exact</h2>
<p>The pinned corpus is replayed for 2026 and each club's wins, losses, ties, points for and points against are compared to today's official
standings. The build <strong>fails</strong> if any club disagrees, so this table cannot silently drift.</p>
"""
    rows = [[esc(r["club"]), f'{esc(r["w"])}-{esc(r["l"])}-{esc(r["t"])}', f'{esc(r["src_w"])}-{esc(r["src_l"])}-{esc(r["src_t"])}',
             esc(r["pf"]), esc(r["src_pf"]), esc(r["pa"]), esc(r["src_pa"]),
             '<span class="tag t-met">exact</span>' if r["reconciles"] == "YES" else '<span class="tag t-block">MISMATCH</span>',
             src(r["source_url"])] for r in recon]
    body += table([("Club", ""), ("Record (games)", "num"), ("Record (official)", "num"), ("PF (games)", "num"),
                   ("PF (official)", "num"), ("PA (games)", "num"), ("PA (official)", "num"), ("Reconciles", ""), ("Source", "")], rows)

    body += f"""
<h2>2. The 136-row log, audited</h2>
<p>The brief names a 136-game log. Audited row by row against the reconciled corpus: <strong>{ls['agree']} agree</strong>,
<strong>{ls['blank']} carry no score</strong>, <strong>{ls['absent']} have no matching game</strong> and
<strong>{ls['disagree']} disagree</strong>. The log's own status field says "final" on every row, including the blank ones.</p>
<div class="cards">
  <div class="card ok"><div class="v">{ls['agree']}</div><div class="k">agree</div></div>
  <div class="card warn"><div class="v">{ls['blank']}</div><div class="k">blank</div></div>
  <div class="card bad"><div class="v">{ls['absent']}</div><div class="k">absent from the snapshot</div></div>
  <div class="card"><div class="v">{ls['disagree']}</div><div class="k">disagree on a posted score</div></div>
</div>
"""
    rows = [[esc(r["wk"]), esc(r["date"]), esc(r["away"]), esc(r["home"]), esc(r["away_score_log"]) or "—",
             esc(r["home_score_log"]) or "—", esc(r["away_score_official"]) or "—", esc(r["home_score_official"]) or "—",
             esc(r["audit_verdict"]), esc(r["status_log"]), src(r["source_url"])] for r in log]
    body += table([("Wk", "num"), ("Date", "mono"), ("Away", ""), ("Home", ""), ("Away (log)", "num"), ("Home (log)", "num"),
                   ("Away (official)", "num"), ("Home (official)", "num"), ("Verdict", ""), ("Log status", ""), ("Source", "")], rows)
    body += """
<div class="callout">
<strong>Verdict on the log.</strong> It is not wrong on a single posted score, so it is usable as a partial corpus — but 19 of 136 rows cannot
be used as-is (16 blank, 3 absent). The reconciled corpus is the input to every backtest on this site instead.
</div>
"""
    page("results.html", "Results &amp; corpus", body, "Reconciled to the official standings; the named log audited line by line.")


def build_questions():
    qs = load("questions")
    summary = json.loads((DATA / "derive_summary.json").read_text())
    body = f"""
<p>The brief asks for a clear list of the questions, information and answers that must be settled before a decision can reasonably be made.
Each row states what we already have, what we do not have, and <strong>the specific route that would close the gap</strong>. Nothing here is a
rhetorical question: every row names the artifact that would answer it.</p>
<div class="cards">
  <div class="card"><div class="v">{len(qs)}</div><div class="k">questions</div></div>
  <div class="card ok"><div class="v">{sum(1 for q in qs if q['can_decide_today'].startswith('YES'))}</div><div class="k">decidable today</div></div>
  <div class="card warn"><div class="v">{sum(1 for q in qs if q['can_decide_today'].startswith('PARTLY'))}</div><div class="k">partly</div></div>
  <div class="card bad"><div class="v">{sum(1 for q in qs if q['can_decide_today'].startswith('NO'))}</div><div class="k">cannot decide yet</div></div>
</div>
"""
    rows = []
    for q in qs:
        cls = "t-met" if q["can_decide_today"].startswith("YES") else ("t-part" if q["can_decide_today"].startswith("PARTLY") else "t-block")
        rows.append([esc(q["id"]), esc(q["question"]), esc(q["why_it_matters"]), esc(q["what_we_have"]),
                     '<span class="tag t-gray">' + esc(q["what_we_do_not_have"]) + "</span>", esc(q["discovery_route"]),
                     f'<span class="tag {cls}">{esc(q["can_decide_today"])}</span>', src(q["source_url"])])
    body += table([("ID", ""), ("Question", ""), ("Why it matters", ""), ("What we have", ""),
                   ("What we do not have", ""), ("Discovery route", ""), ("Decidable today", ""), ("Source", "")], rows)
    body += """
<h2>The missing information, as a single list</h2>
<div class="tw"><table><thead><tr><th>Information we do not have</th><th>What it would unlock</th><th>Route</th><th>Question</th></tr></thead><tbody>
<tr><td>Official inactive lists (90 min before kickoff)</td><td>confirmed starters out and replacements in</td><td>official inactive feed / game book</td><td>Q05</td></tr>
<tr><td>Official game books</td><td>actual starters and game-day status</td><td>NFL game book publication</td><td>Q05</td></tr>
<tr><td>Snap counts</td><td>playing-time depth, the only depth the brief accepts</td><td>official snap-count source</td><td>Q05, Q07</td></tr>
<tr><td>A verified depth order for 32 clubs</td><td>the backup-deficiency matrix</td><td>club depth pages, verified club by club</td><td>Q07</td></tr>
<tr><td>Over/under prices on the closing totals</td><td>a market probability for the total</td><td>an operator archive or a price feed</td><td>Q02</td></tr>
<tr><td>A second and third operator price</td><td>a real consensus and a de-vigged fair market</td><td>additional operator reads under policy P-01</td><td>Q01</td></tr>
<tr><td>Play-by-play</td><td>parlay-leg correlations</td><td>a licensed play-by-play source</td><td>Q09</td></tr>
<tr><td>The reserve / IR list</td><td>distinguishing "healthy" from "not listed"</td><td>club roster reserve sections</td><td>Q17</td></tr>
<tr><td>The play rate of each designation</td><td>turning "Questionable" into a feature</td><td>join archived reports to inactive lists</td><td>Q06</td></tr>
<tr><td>The owner's decisions on rewards and data licensing</td><td>a competition with stakes and a publishable price feed</td><td>owner</td><td>Q01, Q10</td></tr>
</tbody></table></div>
"""
    page("questions.html", "Questions", body, "The information we do not have, and the exact route that would supply it.")


def build_suggestions():
    sug = load("suggestions")
    body = """
<p>A reviewable list, not a changelog. Every suggestion has an empty <strong>owner decision</strong> column: nothing here is approved,
and nothing is implemented by this session beyond what is already on the site. The owner can mark any row accept, defer or reject.</p>
"""
    rows = [[esc(s["id"]), esc(s["suggestion"]), esc(s["problem_it_solves"]), esc(s["effort"]), esc(s["risk"]),
             esc(s["how_we_would_know_it_worked"]),
             '<span class="tag t-gray">undecided</span>', src(s["source_url"])] for s in sug]
    body += table([("ID", ""), ("Suggestion", ""), ("Problem it solves", ""), ("Effort", ""), ("Risk", ""),
                   ("How we would know it worked", ""), ("Owner decision", ""), ("Source", "")], rows)
    body += """
<h2>What I would do first, if the choice were mine</h2>
<div class="callout ok">
<strong>1.</strong> Capture the official inactive list for one week before building anything else (SUG04). It is the single input that converts
"a player is out" into "this backup is playing", which is the whole depth feature.
<strong>2.</strong> Use the game book as the starter record instead of a depth chart (SUG05): it is published, dated and does not need a per-club parser.
<strong>3.</strong> Do not touch the model until those two inputs exist — with a calibration slope of 0.11 the binding constraint is the model, not the data volume.
</div>
"""
    page("suggestions.html", "Suggestions", body, "Review before implementing; every row has an empty owner-decision column.")


def build_research():
    rs = load("research")
    body = """
<p>The claims this board actually tested, each with the evidence, the sample and a two-sided statement of what would overturn it.
Rows marked <span class="tag t-block">REJECTED</span> are shortcuts that were considered and refused, with the reason.</p>
"""
    rows = []
    for r in rs:
        cls = "t-met" if r["status"].startswith("VERIFIED") else ("t-block" if r["status"].startswith("REJECTED") else "t-part")
        rows.append([esc(r["id"]), esc(r["title"]), esc(r["question"]), esc(r["evidence"]), esc(r["n"]),
                     esc(r["result"]), esc(r["what_would_change_our_mind"]),
                     f'<span class="tag {cls}">{esc(r["status"])}</span>', src(r["source_url"])])
    body += table([("ID", ""), ("Title", ""), ("Question", ""), ("Evidence and method", ""), ("n", "num"),
                   ("Result", ""), ("What would change our mind", ""), ("Status", ""), ("Source", "")], rows)

    body += """
<h2>Two corrections this build made to itself</h2>
<div class="callout bad">
<strong>The spread sign.</strong> A first pass treated the pinned corpus's <code>closing_spread_home</code> as home-favoured-negative and produced a
side skill of +0.038 with an interval excluding zero. The data says the opposite: scored as home-favoured-positive the mean absolute error is 10.25
points against 14.62 the other way. With the sign fixed, the skill is negative. The first number was a sign error, and it is recorded here rather than quietly replaced.
</div>
<div class="callout bad">
<strong>The benchmark.</strong> A second pass scored the side against the de-vigged <em>moneyline</em> probability. A constant 0.5 predictor beat that
benchmark by 0.139, which is impossible if the benchmark were a cover probability — the control exposed the error. The side is now scored against a
coin flip at the closing line, and the same control returns exactly 0.0000, which is what a correct benchmark must do.
</div>
"""
    page("research.html", "Research register", body, "Every claim with its evidence, its n, and what would overturn it.")


def build_flagged():
    fl = load("flagged")
    body = """
<p>Every irregularity, contradiction and unverified blank found while building this board, with a link and a severity. Nothing on this page blocks
the rest of the site: the boards above publish blanks where these items apply, and this page is where the gap is recorded so it can be reviewed.</p>
<div class="cards">
"""
    for sev, cls in (("high", "bad"), ("medium", "warn"), ("low", "")):
        body += f'<div class="card {cls}"><div class="v">{sum(1 for f in fl if f["severity"]==sev)}</div><div class="k">{sev} severity</div></div>'
    body += "</div>"
    rows = []
    for f in fl:
        cls = {"high": "t-block", "medium": "t-part", "low": "t-gray"}.get(f["severity"], "t-gray")
        rows.append([esc(f["id"]), f'<span class="tag {cls}">{esc(f["severity"])}</span>', esc(f["type"]), esc(f["title"]),
                     esc(f["detail"]), src(f["evidence_url"], "evidence ↗"), esc(f["status"])])
    body += table([("ID", ""), ("Severity", ""), ("Type", ""), ("Item", ""), ("Detail", ""), ("Evidence", ""), ("Status", "")], rows)
    page("flagged.html", "Flagged for review", body, "Irregularities and unverified blanks, each with a link.")


def build_method():
    sources = load("sources")
    summary = json.loads((DATA / "derive_summary.json").read_text())
    hashes = summary["frozen_inputs"]
    body = f"""
<p>This page is the audit trail: what was read, when, from where, and the hash of every artifact the build depends on.
Read timestamps are UTC. Where a source was not re-read in this session, the row says so instead of borrowing an earlier read.</p>

<h2>1. Sources</h2>
"""
    rows = [[esc(s["source_id"]), esc(s["title"]), f'<a href="{esc(s["url"])}" rel="noopener">{esc(s["url"])}</a>',
             f'<span class="tag {"t-met" if s["tier"]=="OFFICIAL" else "t-info" if s["tier"]=="OPERATOR" else "t-gray"}">{esc(s["tier"])}</span>',
             esc(s["read_utc"]), f'<code>{esc(s["sha256"][:16])}…</code>' if s["sha256"] else "—", esc(s["used_for"])] for s in sources]
    body += table([("ID", ""), ("Source", ""), ("URL", ""), ("Tier", ""), ("Read (UTC)", ""), ("sha256", "mono"), ("Used for", "")], rows)

    body += f"""
<h2>2. Frozen inputs</h2>
<p>These hashes are the fingerprint of the build. Any change to an input changes them, and the verifier fails if a pinned row count moves.</p>
<div class="tw"><table><thead><tr><th>Artifact</th><th>sha256</th></tr></thead><tbody>
"""
    for k, v in sorted(hashes.items()):
        body += f'<tr><td>{esc(k)}</td><td class="mono">{esc(v)}</td></tr>'
    body += """</tbody></table></div>

<h2>3. How every number was produced</h2>
<div class="tw"><table><thead><tr><th>Number</th><th>Method</th><th>Failure mode it is guarded against</th></tr></thead><tbody>
<tr><td>The ratings</td><td>a walk-forward Elo updated game by game with a season regression and a home-field term</td><td>lookahead: a game can only move a rating after it is played</td></tr>
<tr><td>The projected margin</td><td>a linear map from the rating difference, fitted on 2015–2024 only</td><td>tuning on the holdout</td></tr>
<tr><td>The projected total</td><td>rolling offence and defence scoring rates with shrinkage toward the league mean</td><td>small-sample rates driving fake edges</td></tr>
<tr><td>The cover probability</td><td>a normal dispersion model around the projected margin, with sigma chosen on train</td><td>choosing sigma on the evaluation window</td></tr>
<tr><td>The skill</td><td>1 − (model Brier ÷ benchmark Brier), with a week-cluster bootstrap</td><td>treating correlated games as independent</td></tr>
<tr><td>The multiplicity control</td><td>Holm adjustment across the registered families</td><td>finding a winner by trying many variants</td></tr>
<tr><td>The calibration slope</td><td>a logistic fit of outcome on the log-odds of the model probability, train only</td><td>staking inflated probabilities</td></tr>
<tr><td>The reconciliation</td><td>32 club records recomputed from games and compared to the official page; the build fails on any mismatch</td><td>a corpus that silently drifts from the official record</td></tr>
</tbody></table></div>

<h2>4. Determinism</h2>
<p>The data build uses a fixed seed ({summary['model'].get('seed', 20261119)}) and no wall-clock value, so two consecutive runs produce byte-identical CSVs.
The bootstrap uses a linear congruential generator implemented in the build rather than a library, so the intervals reproduce on any machine with
Python 3.11 and no third-party packages. <code>verify.py</code> re-runs the build and fails if the committed files differ.</p>

<h2>5. Related desks in this repository</h2>
<p>Own5 is a multi-session repository. This board is additive. The nearest neighbours, all read-only from here:</p>
<div class="tw"><table><thead><tr><th>Desk</th><th>What it covers</th><th>Link</th></tr></thead><tbody>
<tr><td>NFL Verified Line Desk</td><td>a 7,117-game corpus, a 136-row log audit and a 744-game walk-forward model</td><td><a href="https://sassnarep3-star.github.io/Own5/nfl-line-audit/">nfl-line-audit</a></td></tr>
<tr><td>NFL Decision-Readiness Desk</td><td>a 79-requirement ledger with gates and clearing numbers</td><td><a href="https://sassnarep3-star.github.io/Own5/nfl-desk-067f2314/">nfl-desk-067f2314</a></td></tr>
<tr><td>NFL Venue &amp; Schedule-Announcement Desk</td><td>venue transcription from official game centres</td><td><a href="https://sassnarep3-star.github.io/Own5/nfl-venue-390e13fd/">nfl-venue-390e13fd</a></td></tr>
<tr><td>NFL integration hub</td><td>the cross-desk index</td><td><a href="https://sassnarep3-star.github.io/Own5/nfl-integration-a620f5a5/">nfl-integration-a620f5a5</a></td></tr>
</tbody></table></div>
"""
    page("method.html", "Method &amp; sources", body, "What was read, when, and how every number was produced.")


def main() -> int:
    build_index(); build_readiness(); build_origination(); build_model(); build_leaderboard()
    build_availability(); build_correlations(); build_results(); build_questions(); build_suggestions()
    build_research(); build_flagged(); build_method()
    (OUT / ".nojekyll").write_text("")
    (OUT / "style.css").write_text(CSS.strip() + "\n")
    n = len(list(OUT.glob("*.html")))
    print(f"built {n} pages in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

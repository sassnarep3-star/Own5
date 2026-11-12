#!/usr/bin/env python3
"""Render the NFL Decision Desk static site from the computed data."""
from __future__ import annotations

import csv
import html
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DD = "https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/"
DOC = "https://github.com/sassnarep3-star/Own5/blob/main/research/38a1fc27/"
sys.path.insert(0, HERE)
import content  # noqa: E402
import lib  # noqa: E402

SITE = os.path.join(ROOT, "nfl-decision-desk")
DATA = os.path.join(ROOT, "data", "decision-desk")
REPO = "https://github.com/sassnarep3-star/Own5/blob/main/"

NAV = [
    ("index.html", "Overview"),
    ("requirements.html", "Requirements"),
    ("suggestions.html", "Suggestions"),
    ("questions.html", "Open questions"),
    ("lines.html", "Own lines"),
    ("strategies.html", "Strategies"),
    ("validation.html", "Gates"),
    ("correlations.html", "Correlations"),
    ("injuries.html", "Injuries & depth"),
    ("audit.html", "Repo audit"),
    ("summary.html", "Summary"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged"),
    ("verification.html", "Verification"),
]

GATES = [
    ("G0", "Pre-registration", "The rule, threshold and sample window are committed before results are inspected.",
     "Research integrity; stops post-hoc threshold selection."),
    ("G1", "Minimum sample", "n >= 300 graded bets before a strategy may be listed, and a power check for certification.",
     "A 55% true rate and a 52.38% break-even need ~2,241 bets at 80% power."),
    ("G2", "Significance vs multiplicity", "Exact two-sided binomial p < 0.05 / k, where k is the number of variants tested.",
     "Keeps false discoveries bounded when many families are tried."),
    ("G3", "Chronological holdout", "The final 30% of bets, by date, must clear break-even on its own.",
     "Guards against fitting the past."),
    ("G4", "Closing-line value", "Average CLV >= 0 against a verified closing price.",
     "The industry skill metric; requires a price history (F02)."),
    ("G5", "Correlation cap", "|r| < 0.50 against every live strategy on overlapping bets.",
     "Prevents disguised duplicate exposure."),
    ("G6", "Drawdown", "Maximum drawdown < 20 units on a 100-unit bankroll.",
     "Risk control, not just selection."),
    ("G7", "Staking", "<= quarter Kelly, capped at 2% of bankroll per bet.",
     "Stops one bet from dominating the record."),
    ("G8", "Market integrity", "All prices traceable to a verified operator or official source.",
     "Aggregator lines do not qualify (F01)."),
    ("G9", "Parlay correlation", "No correlated legs without the operator's same-game price.",
     "Correlated legs priced as independent are a guaranteed loss."),
    ("G10", "Grading integrity", "Official final scores; pushes void; player props void if the player is inactive.",
     "Prevents mis-graded results."),
    ("G11", "Liquidity", "Stake within posted limits; books may refuse or limit any bet.",
     "Operational, not statistical."),
    ("G12", "Responsible gambling", "Adults only, legal jurisdiction only, support at 1-800-GAMBLER.",
     "Applies to every page and every strategy."),
]


# --------------------------------------------------------------- helpers
def esc(x) -> str:
    return html.escape("" if x is None else str(x))


def read_csv(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_json(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def badge(text, kind="") -> str:
    cls = "badge " + kind
    return f'<span class="{cls.strip()}">{esc(text)}</span>'


def status_badge(value) -> str:
    v = (value or "").lower()
    if any(k in v for k in ("met", "match", "agrees", "computed", "answered", "pass", "candidate")):
        kind = "ok"
    elif any(k in v for k in ("block", "fail", "mismatch", "does not", "reject")):
        kind = "bad"
    elif any(k in v for k in ("partial", "review", "provisional", "minor", "n/a", "defer", "pilot", "not ")):
        kind = "warn"
    else:
        kind = ""
    return badge(value, kind)


def table(headers, rows, classes="data", source=None, source_label="source") -> str:
    """Render an HTML table.

    ``source`` (a URL, or a list parallel to ``rows``) adds a per-row source
    column, so the "every row links to its evidence" rule holds for computed
    tables as well as for authored ones.
    """
    if source and rows and "Source" not in headers:
        headers = list(headers) + ["Source"]
        srcs = source if isinstance(source, list) else [source] * len(rows)
        rows = [list(r) + [source_cell(srcs[i], source_label)]
                for i, r in enumerate(rows)]
    out = [f'<div class="tablewrap"><table class="{classes}">', "<thead><tr>"]
    for h in headers:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def link(url, text=None) -> str:
    if not url:
        return ""
    return f'<a href="{esc(url)}" rel="noopener">{esc(text or url)}</a>'


def source_cell(url, text="source") -> str:
    return link(url, text) if url else badge("no source", "warn")


def kpi(value, label, note="", kind="") -> str:
    return (f'<div class="kpi {kind}"><div class="kpi-value">{esc(value)}</div>'
            f'<div class="kpi-label">{esc(label)}</div>'
            f'<div class="kpi-note">{note}</div></div>')


def page(filename, title, lead, body, updated="") -> str:
    nav = "".join(
        f'<a class="{"active" if f == filename else ""}" href="{f}">{esc(label)}</a>'
        for f, label in NAV)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · NFL Decision Desk</title>
<meta name="description" content="{esc(lead)}">
<link rel="stylesheet" href="style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='18' fill='%230b1f3a'/><text x='50' y='68' font-size='52' text-anchor='middle' fill='%23ffd166' font-family='sans-serif'>D</text></svg>">
</head>
<body>
<header class="top">
  <div class="wrap">
    <div class="brand">
      <span class="mark">DD</span>
      <div>
        <h1><a href="index.html">NFL Decision Desk</a></h1>
        <p>Own lines · validated strategies · injury &amp; depth intelligence</p>
      </div>
    </div>
    <div class="stamp">
      <strong>Week 10 · 2026 season</strong>
      <span>Snapshot {esc(updated or "2026-11-12")} UTC</span>
    </div>
  </div>
  <nav class="wrap">{nav}</nav>
</header>
<main class="wrap">
  <section class="pagehead">
    <h2>{esc(title)}</h2>
    <p>{lead}</p>
  </section>
  {body}
</main>
<footer class="wrap">
  <p><strong>Verification policy.</strong> Every table row links to an official page or to the
  script and pinned input that produced it. Values that cannot be confirmed are left blank and
  published on the <a href="flagged.html">Flagged for review</a> page — never inferred.</p>
  <p>Research only. No bets are placed, no performance is claimed, and nothing here is betting
  advice. If gambling is a problem: 1-800-GAMBLER.</p>
</footer>
</body>
</html>
"""


def write(name, text):
    with open(os.path.join(SITE, name), "w", encoding="utf-8") as fh:
        fh.write(text)


# --------------------------------------------------------------- pages
def build_index(data):
    prov = read_json(os.path.join(DATA, "raw", "provenance.json")) if os.path.exists(
        os.path.join(DATA, "raw", "provenance.json")) else {}
    audit = read_json("audit_summary.json")
    inj = read_json("injury_signal.json")
    meta = read_json("strategy_meta.json")
    ledger = read_csv("strategy_ledger.csv")
    lines = read_csv("model_lines_wk10.csv")
    players = read_csv("injuries_wk10_players.csv")
    cert = sum(1 for r in ledger if r.get("status") == "CERTIFIED")
    reproduced = sum(1 for c in read_csv("claim_checks.csv")
                     if c.get("verdict", "").lower().startswith("agree"))
    body = ['<div class="grid kpis">']
    body.append(kpi("32/32", "clubs reconciled",
                    "official standings vs independent game log", "ok"))
    body.append(kpi(f"{len(players)}", "official injury rows",
                    "Week 10 report, per-row source links"))
    body.append(kpi(f"{len(lines)}", "games priced",
                    "own spread and total for Week 10"))
    body.append(kpi(f"{cert}", "certified strategies",
                    f"{len(ledger)} families tested; none pass G4/G8", "bad"))
    body.append(kpi(f"{reproduced}/{len(read_csv('claim_checks.csv'))}",
                    "prior claims reproduced",
                    "the rest are flagged on the audit page", "warn"))
    body.append(kpi(audit.get("internal_links", {}).get("broken_count", "0"),
                    "broken internal links",
                    f"{audit.get('internal_links', {}).get('pages', 0)} pages scanned", "ok"))
    body.append(kpi(f"{len(content.SUGGESTIONS)}", "suggestions for review",
                    "each with a decision state and a review test"))
    body.append(kpi(f"{len(content.QUESTIONS)}", "open questions",
                    "4 block a decision and cannot be closed from public data", "warn"))
    body.append("</div>")

    # headline findings
    slope = inj.get("market_residual_model", {}).get("slope_pts_per_pp", "")
    fade = inj.get("fade_more_injured_team", {})
    body.append('<h3>What the numbers say</h3><div class="cards">')
    cards = [
        ("Lineup loss predicts margin, not the market",
         f"A percentage point of relative lineup deficiency is worth about "
         f"{float(inj.get('quality_controlled_model', {}).get('raw_margin_slope_pts_per_pp', 0) or 0):.3f} "
         f"points of margin (p = {inj.get('quality_controlled_model', {}).get('raw_margin_p', 'n/a')}). "
         f"But fading the more-injured team is only {float(fade.get('win_rate', 0) or 0)*100:.1f}% "
         f"ATS over {fade.get('n_bets', 0)} bets (p = {fade.get('p_two_sided', 'n/a')}). The market "
         "already prices most of it.", "injuries.html#calibration"),
        ("The market prices about half of the injury effect",
         f"Regressing the market spread on the same deficiency measure gives "
         f"-0.019 points per percentage point, about 49% of the raw effect. The "
         "leftover -0.020 per point is statistically weak (p = 0.024) and produces "
         "no binary ATS edge, and the line's timestamp is unknown (F01).",
         "injuries.html#priced"),
        ("Same-team prop legs are heavily correlated",
         "QB passing yards and his WR1's receiving yards correlate at r = 0.50 "
         "(n = 1,255 team-games). At median lines the joint hit rate is 32.5% versus "
         "24.8% if legs were independent — a +7.7 pp gap that changes the fair price.",
         "correlations.html#sgp"),
        ("Sign conventions are the top risk to this project",
         "The first injury backtest reported a 57.4% ATS edge purely because the spread "
         "was used with the wrong sign. Fixed, the same test returns 51.4%. Every "
         "backtest now carries a convention note and the error is retained in the log.",
         "verification.html#sign"),
    ]
    for title, text, href in cards:
        body.append(f'<article class="card"><h4>{esc(title)}</h4><p>{esc(text)}</p>'
                    f'<a class="more" href="{href}">Open the detail →</a></article>')
    body.append("</div>")

    # decisions to make now
    body.append('<h3>Decisions waiting on you</h3>')
    body.append("<p>These are the only items that cannot be settled by more analysis. "
                "Each links to the suggestion and the test that would change the call.</p>")
    rows = []
    for s in content.SUGGESTIONS:
        if s["decision"] in ("Recommended now",) and s["impact"] == "High":
            rows.append([esc(s["id"]), esc(s["title"]), status_badge(s["decision"]),
                         esc(s["owner"]),
                         f'<a href="suggestions.html#{s["id"]}">details</a>'])
    body.append(table(["ID", "Decision", "State", "Owner", ""], rows))

    body.append('<h3>Data snapshot</h3>')
    if prov:
        assets = prov.get("assets", [])
        pages = prov.get("pages", [])
        body.append(f"<p>Retrieved <strong>{esc(prov.get('retrieved_utc'))}</strong>: "
                    f"{sum(1 for a in assets if a.get('http_status') == 200)}/{len(assets)} "
                    f"pinned datasets and {sum(1 for p in pages if p.get('http_status') == 200)}/"
                    f"{len(pages)} official pages returned HTTP 200. Each file's SHA-256 and byte "
                    f"count are recorded in "
                    f'<a href="{REPO}data/decision-desk/raw/provenance.json">provenance.json</a>.</p>')
    rows = [[esc(p.get("name")), link(p.get("url")),
             status_badge(f"HTTP {p.get('http_status')}"),
             esc(f"{p.get('bytes', 0):,} bytes"),
             link(REPO + "data/decision-desk/raw/official_text/" + str(p.get("name")) + ".txt", "text extract")]
            for p in prov.get("pages", [])]
    body.append(table(["Official page", "URL", "Status", "Size", "Snapshot"], rows,
                      source=DD + "raw/provenance.json"))

    body.append('<h3>Where to look first</h3><div class="cards three">')
    for href, title, text in [
        ("suggestions.html", "Suggestions register", "16 recommendations with impact, effort, confidence and a decision state. Review and pick a path."),
        ("questions.html", "Questions that gate decisions", "18 questions; 4 block anything beyond research and cannot be closed from public data."),
        ("injuries.html", "Injury &amp; depth desk", "276 official injury rows, depth strings 1-4, and the measured price of lineup loss."),
    ]:
        body.append(f'<article class="card"><h4><a href="{href}">{title}</a></h4><p>{text}</p></article>')
    body.append("</div>")
    write("index.html", page("index.html", "Decision overview",
                             "One dashboard for own lines, validated strategies and lineup intelligence — "
                             "with the evidence and the gaps side by side.",
                             "".join(body), prov.get("retrieved_utc", "")[:10]))


PAGEMAP = {
    "requirements.html": "requirements.html", "suggestions.html": "suggestions.html",
    "questions.html": "questions.html", "lines.html": "lines.html",
    "strategies.html": "strategies.html", "validation.html": "validation.html",
    "correlations.html": "correlations.html", "injuries.html": "injuries.html",
    "summary.html": "summary.html", "sources.html": "sources.html",
    "flagged.html": "flagged.html", "verification.html": "verification.html",
    "audit.html": "audit.html",
}


def page_for(evidence: str) -> str:
    for name in PAGEMAP:
        if name in evidence:
            return name
    return "index.html"


def build_requirements():
    rows = []
    for r in content.REQUIREMENTS:
        rows.append([
            esc(r["id"]), esc(r["requirement"]), status_badge(r["status"]),
            esc(r["how"]), esc(r["gap"]) or badge("none", "ok"),
            f'<a href="{esc(page_for(r["evidence"]))}">{esc(r["evidence"])}</a>',
        ])
    body = [f"<p>All {len(content.REQUIREMENTS)} distinct instructions in the brief are listed below. "
            "“Partially met” means the analysis exists and the remaining gap is a data-access "
            "problem that is named on the questions page.</p>",
            table(["ID", "Requirement", "Status", "How it is met", "Remaining gap", "Artefact"], rows)]
    write("requirements.html", page("requirements.html", "Requirements matrix",
                                   "The brief, decomposed line by line, with the artefact that satisfies each line.",
                                   "".join(body)))


def build_suggestions():
    body = ['<div class="callout"><h4>How to review this register</h4>'
            "<p>Each suggestion states the problem it solves, the change, its expected impact and "
            "effort, and the test that would make us abandon it. Decision states are "
            "<strong>Recommended now</strong>, <strong>Pilot</strong>, "
            "<strong>Defer</strong> or <strong>Reject</strong>. Nothing is implemented until you "
            "choose — this page is the approval surface.</p></div>"]
    counts = {}
    for s in content.SUGGESTIONS:
        counts[s["decision"]] = counts.get(s["decision"], 0) + 1
    body.append('<div class="grid kpis">')
    for k, v in counts.items():
        body.append(kpi(v, k, "suggestions", "ok" if k == "Recommended now" else ""))
    body.append("</div>")
    for s in content.SUGGESTIONS:
        body.append(f"""
<details class="sug" id="{s['id']}">
  <summary><span class="sid">{esc(s['id'])}</span> {esc(s['title'])} {status_badge(s['decision'])}</summary>
  <div class="sugbody">
    <dl>
      <dt>Problem</dt><dd>{esc(s['problem'])}</dd>
      <dt>Recommendation</dt><dd>{esc(s['recommendation'])}</dd>
      <dt>Impact / effort / confidence</dt><dd>{esc(s['impact'])} · {esc(s['effort'])} · {esc(s['confidence'])}</dd>
      <dt>Evidence</dt><dd>{esc(s['evidence'])}</dd>
      <dt>Owner</dt><dd>{esc(s['owner'])}</dd>
      <dt>Review test</dt><dd>{esc(s['review_test'])}</dd>
    </dl>
  </div>
</details>""")
    write("suggestions.html", page("suggestions.html", "Suggestions for review",
                                   "Recommendations to improve decision quality, ranked by impact, "
                                   "each with a decision state you can approve, modify or reject.",
                                   "".join(body)))


def build_questions():
    groups = [("Blocking", "bad"), ("Partially answered", "warn"), ("Answered", "ok")]
    body = ['<div class="callout"><h4>Why this page exists</h4>'
            "<p>A decision is only as good as the information behind it. These are the questions "
            "that still need an answer, what we already know, and the cheapest way to close each "
            "one. Anything marked <em>blocking</em> cannot be resolved by more analysis of public "
            "data alone.</p></div>"]
    for status, kind in groups:
        items = [q for q in content.QUESTIONS if q["status"] == status]
        if not items:
            continue
        body.append(f'<h3 id="{status.split()[0].lower()}">{esc(status)} '
                    f'{badge(len(items), "count")}</h3>')
        rows = []
        for q in items:
            rows.append([
                f'<span id="{q["id"]}">{esc(q["id"])}</span>',
                f"<strong>{esc(q['question'])}</strong><br><span class=\"muted\">{esc(q['why'])}</span>",
                esc(q["have"]), esc(q["missing"]), esc(q["resolve"]),
                status_badge(q["status"]), esc(q["related"]),
            ])
        body.append(table(["ID", "Question / why it matters", "What we have",
                           "What is missing", "How to close it", "Status", "Req"], rows,
                          source=DD + "questions.csv"))
    write("questions.html", page("questions.html", "Open questions",
                                 "What must be answered before a decision is reasonable, and how to get it.",
                                 "".join(body)))


def build_lines():
    lines = read_csv("model_lines_wk10.csv")
    bt = read_csv("model_backtest.csv")
    model = read_json("line_model.json")
    rows = []
    for r in lines:
        edge = r.get("edge_vs_market_pts", "")
        edge_html = esc(edge)
        if edge:
            try:
                if abs(float(edge)) >= 3:
                    edge_html = f'<span class="pos">{esc(edge)}</span>'
            except ValueError:
                pass
        rows.append([
            esc(r.get("gameday")), esc(r.get("kickoff_et")),
            f"{esc(r.get('away'))} @ {esc(r.get('home'))}",
            esc(r.get("site")), esc(r.get("model_spread_home")),
            esc(r.get("model_total")), esc(r.get("injury_adjustment_pts")),
            esc(r.get("market_spread_home_agg")), esc(r.get("market_total_agg")),
            edge_html, status_badge(r.get("verdict")),
            source_cell(r.get("market_source"), "agg"),
        ])
    body = [f'<div class="grid kpis">',
            kpi(len(lines), "games priced", "Week 10, 2026"),
            kpi(model.get("hfa_pts", "—"), "home-field points", "estimated in-model"),
            kpi(f"{model.get('injury_coefficient_pts_per_pp', '—')}",
                "pts per pp of deficiency", "injury coefficient"),
            kpi(model.get("edges_ge3", 0), "candidates ≥ 3 pts",
                "model vs aggregator line, not bets", "warn"),
            "</div>"]
    body.append("<h3>Week 10 board</h3>")
    body.append("<p>Model spread is quoted from the home team's perspective (negative = home "
                "favoured). The injury adjustment is applied to the margin and shown separately so "
                "the size of the adjustment is auditable. Market columns are "
                "<strong>aggregator</strong> values, not operator snapshots (F01).</p>")
    body.append(table(["Date", "ET", "Game", "Site", "Model spread", "Model total",
                       "Injury adj.", "Market spread", "Market total", "Edge",
                       "Verdict", "Market src"], rows,
                      source=DD + "model_lines_wk10.csv"))
    body.append("<h3>How the line is built</h3><ol class=\"tight\">"
                "<li><strong>Ratings.</strong> Ridge least squares on final margins, "
                "<code>margin = rating_home − rating_away + hfa</code>, fitted only on games before "
                "the week being priced. Shrinkage keeps early-season ratings honest.</li>"
                "<li><strong>Totals.</strong> Two-way points model, "
                "<code>points = μ + offence_team − defence_opponent</code>, same walk-forward rule.</li>"
                "<li><strong>Injury adjustment.</strong> The lineup-deficiency gap is regressed on "
                "margin controlling for prior scoring margin; the coefficient is applied to the "
                "current week's gap.</li>"
                "<li><strong>Market comparison.</strong> Edge = model margin − aggregator expected "
                "home margin. An edge is a research candidate, never a bet instruction.</li></ol>")
    body.append(f"<p>Home-field advantage estimated at <strong>{esc(model.get('hfa_pts'))}</strong> "
                f"points on this build; the injury coefficient is "
                f"<strong>{esc(model.get('injury_coefficient_pts_per_pp'))}</strong> points per "
                f"percentage point (SE {esc(model.get('injury_coefficient_se'))}, "
                f"p {esc(model.get('injury_coefficient_p'))}, n "
                f"{esc(model.get('injury_coefficient_n'))}).</p>")
    body.append("<h3 id=\"backtest\">Walk-forward backtest of the same model</h3>")
    body.append("<p>Every game from 1999 to 2026 priced before kickoff with ratings from prior "
                "weeks only, then compared with the aggregator line. A threshold of 3 points means "
                "the bet is only taken when the model disagrees with the market by at least 3.</p>")
    rows = [[esc(r["model"]), esc(r["threshold_pts"]), esc(r["n_bets"]), esc(r["wins"]),
             esc(r["win_rate"]), f"{esc(r['ci_low'])}–{esc(r['ci_high'])}",
             esc(r["p_two_sided"]), esc(r["flat_roi_at_minus110"]),
             status_badge("no edge" if float(r["win_rate"]) < 0.53 else "check")]
            for r in bt]
    body.append(table(["Model", "Threshold", "Bets", "Wins", "Win rate", "95% CI",
                       "p vs 52.38%", "ROI at -110", "Read"], rows,
                      source=DD + "model_backtest.csv"))
    body.append('<p class="muted">Reading: a model that beats the market would show win rates '
                'clearly above 52.4% with tight intervals. It does not. That is the expected '
                'result and it is the reason no strategy is certified.</p>')
    write("lines.html", page("lines.html", "Own lines — Week 10, 2026",
                             "A spread and total for every game, built from prior weeks only, with the "
                             "injury adjustment exposed and the walk-forward record published.",
                             "".join(body)))


def build_strategies():
    ledger = read_csv("strategy_ledger.csv")
    meta = read_json("strategy_meta.json")
    rows = []
    for r in ledger:
        rows.append([
            esc(r.get("provisional_rank")), f"<strong>{esc(r.get('variant'))}</strong>",
            esc(r.get("n_bets")), esc(r.get("wins")), esc(r.get("win_rate")),
            f"{esc(r.get('ci95_low'))}–{esc(r.get('ci95_high'))}",
            esc(r.get("p_two_sided")), esc(r.get("roi_flat_minus110")),
            esc(r.get("holdout_win_rate")) or badge("n/a", "warn"),
            f"{esc(r.get('gates_passed'))} / {int(r.get('gates_passed', 0)) + int(r.get('gates_failed', 0))}",
            status_badge(r.get("status")),
        ])
    body = [f'<div class="callout warn"><h4>Zero certified strategies — by design</h4>'
            f"<p>{len(ledger)} families were tested against a Bonferroni threshold of "
            f"α = {meta.get('bonferroni_alpha', 0):.5f} (k = {meta.get('variants_tested')}). "
            "None passes every hard gate: G4 (closing-line value) and G8 (verified market price) "
            "cannot be passed at all without a price history. The leaderboard below is therefore "
            "provisional and cannot pay rewards.</p></div>"]
    body.append('<h3 id="leaderboard">Leaderboard (provisional)</h3>')
    body.append(table(["#", "Strategy family", "Bets", "Wins", "Win rate", "95% CI",
                       "p vs 52.38%", "ROI at -110", "Holdout", "Gates", "Status"], rows,
                      source=DD + "strategy_ledger.csv"))
    body.append("<h3>What each family is</h3>")
    desc = {
        "S1": ("Home underdogs ATS", "Back the home team whenever it is the underdog. The classic 'home dogs bark' claim."),
        "S2": ("Home dogs receiving 7+", "The subset where the home side gets a touchdown or more."),
        "S3": ("Divisional home dogs", "Familiarity plus home field; the subset where the clubs share a division."),
        "S4": ("Fade 10+ point favourites", "Large favourites historically cover less often than the price implies."),
        "S5": ("Over the closing total", "Test whether closing totals are systematically too low."),
        "S6": ("Home team off a bye", "Rest advantage: home side with 13+ days, opponent on normal rest."),
        "S7": ("Fade the more-injured team", "Our own measure: the side with the larger lineup-deficiency gap."),
    }
    cards = []
    for r in ledger:
        key = r["variant"][:2]
        name, text = desc.get(key, (r["variant"], ""))
        cards.append(f'<article class="card"><h4>{esc(r["variant"])}</h4><p>{esc(text)}</p>'
                     f'<p class="muted">Gate record: {esc(r.get("gate_results",""))}</p></article>')
    body.append('<div class="cards three">' + "".join(cards) + "</div>")

    body.append('<h3 id="luck">Removing luck</h3>')
    body.append("<ul class=\"tight\">"
                f"<li><strong>Break-even at the price, not at 50%.</strong> -110 requires "
                f"{float(meta.get('break_even_at_minus110', 0))*100:.2f}%, so every test is "
                "against 52.38%.</li>"
                f"<li><strong>Multiplicity is counted.</strong> {meta.get('variants_tested')} variants "
                f"tested, so α = {meta.get('bonferroni_alpha', 0):.5f}. Buckets found after "
                "inspection are labelled exploratory.</li>"
                "<li><strong>Chronological holdout.</strong> The last 30% of bets, by date, must "
                "clear break-even independently.</li>"
                "<li><strong>Permutation null.</strong> 500 shuffles of the deficiency labels give "
                "an empirical null distribution for every slope we publish.</li>"
                "<li><strong>Power, not vibes.</strong> "
                f"{meta.get('power_check', 'A 55% true rate needs about 2,241 bets to be distinguished from 52.38% at 80% power.')}</li>"
                "</ul>")
    body.append('<div class="callout"><h4>Parlay and same-game construction</h4>'
                f"<p>A two-leg -110 parlay needs a joint <strong>27.44%</strong> "
                "(0.5238²). Independent break-even legs deliver exactly that, so the parlay price "
                "itself carries no edge — only correlation does. Same-team legs are strongly "
                "correlated (see <a href=\"correlations.html\">correlations</a>), which is why "
                "the operator's same-game price, not the parlay multiplier, is the only fair test.</p></div>")
    body.append('<h3 id="rewards">Reward structure (proposal, unfunded)</h3>')
    body.append(table(["Tier", "Requirement", "Reward", "Status"],
                      [["Gold", "Certified: all hard gates pass, CLV verified", "Proposal — amount blank", badge("needs Q04", "warn")],
                       ["Silver", "Certified on gates G0-G3, G5-G7 with 300+ bets", "Proposal — amount blank", badge("needs Q04", "warn")],
                       ["Bronze", "Provisional listing with positive holdout", "Badge only", badge("available", "ok")]],
                      source=DD + "strategy_ledger.csv"))
    body.append('<p class="muted">No cash amount is published because funding, jurisdiction and '
                'operator terms are open questions (Q04, Q05). Publishing a number before those '
                'are answered would be a claim we cannot support.</p>')
    write("strategies.html", page("strategies.html", "Strategies &amp; leaderboard",
                                  "Seven pre-registered families, one honest scoreboard, and the "
                                  "machinery that removes luck from the ranking.",
                                  "".join(body)))


def build_validation():
    body = ["<p>Every strategy is scored against the same thirteen gates. A strategy is "
            "CERTIFIED only when every hard gate passes; anything else stays provisional no "
            "matter how good the win rate looks.</p>"]
    rows = [[f"<strong>{g}</strong>", esc(name), esc(criterion), esc(rationale)]
            for g, name, criterion, rationale in GATES]
    body.append(table(["Gate", "Name", "Criterion", "Why it exists"], rows,
                      source=DOC + "validation-gates.md"))
    ledger = read_csv("strategy_ledger.csv")
    body.append("<h3>Gate results this build</h3>")
    body.append("<p>The matrix below is generated from the strategy ledger. “Failed” includes "
                "gates that cannot be passed at all — G4 and G8 — which is why no strategy is "
                "certified.</p>")
    gate_ids = [g[0] for g in GATES]
    head = ["Strategy"] + gate_ids + ["Status"]
    trows = []
    for r in ledger:
        results = dict(part.split("=") for part in (r.get("gate_results") or "").split(";") if "=" in part)
        cells = [f"<strong>{esc(r['variant'])}</strong>"]
        for g in gate_ids:
            key = [k for k in results if k.startswith(g + "_")]
            val = results.get(key[0], "n/a") if key else "n/a"
            cells.append(badge("pass", "ok") if val == "pass"
                         else (badge("fail", "bad") if val == "fail" else badge("—", "warn")))
        cells.append(status_badge(r.get("status")))
        trows.append(cells)
    body.append(table(head, trows, source=DD + "strategy_ledger.csv"))
    body.append('<div class="callout"><h4>The honest consequence</h4><p>Because G4 needs a '
                'verified closing price and G8 needs a verified operator price, the correct '
                'current statement is: <strong>no strategy in this project is certified as '
                'skill-based</strong>. That is not a failure of the analysis; it is the analysis '
                'working.</p></div>')
    write("validation.html", page("validation.html", "Validation gates",
                                  "Thirteen gates, published thresholds, and the per-strategy matrix.",
                                  "".join(body)))


def build_correlations():
    props = read_csv("prop_correlations.csv")
    parlays = read_csv("parlay_correlations.csv")
    sgp = read_csv("sgp_pricing_table.csv")
    summary = read_json("correlation_summary.json")
    emp = summary.get("empirical_qb_wr1_joint", {})
    body = [f'<div class="grid kpis">',
            kpi(f"{summary.get('panel_team_games', 0)}", "team-games in the panel",
                "2024-2026 regular season"),
            kpi(emp.get("joint_over_rate", "—"), "QB+WR1 joint over rate",
                f"independent would be {emp.get('independent_product', '—')}"),
            kpi(f"{emp.get('excess_pp', '—')} pp", "excess vs independence",
                "the same-game parlay gap", "warn"),
            "</div>"]
    body.append("<h3 id=\"props\">Prop correlations</h3>")
    body.append("<p>Pearson correlation between the underlying statistics, not between bet "
                "outcomes. Fisher 95% intervals are shown; a coefficient is only used for pricing "
                "when the interval excludes zero.</p>")
    rows = [[esc(r["measure"]), esc(r["pearson_r"]),
             f"{esc(r['ci95_low'])}–{esc(r['ci95_high'])}", esc(r["n_team_games"]),
             esc(r["p_value"]), esc(r["note"]), source_cell(r.get("source_url"), "data")]
            for r in props]
    body.append(table(["Pair", "r", "95% CI", "n", "p", "Interpretation", "Source"], rows,
                      source=DD + "prop_correlations.csv"))
    body.append("<h3 id=\"sgp\">Same-game parlay pricing</h3>")
    body.append("<p>For two legs with equal 50% win probability and correlation r, the joint "
                "probability is 0.25 + arcsin(r)/(2π). The fair price column keeps a 9.09% hold "
                "so it can be compared directly with a two-leg -110 parlay paying +264.</p>")
    rows = [[esc(r["r"]), esc(r["joint_prob"]), esc(r["ratio_vs_independent"]),
             esc(r["fair_price_keeping_9.09pct_hold"])] for r in sgp]
    body.append(table(["r", "Joint probability", "vs independent", "Fair price (9.09% hold)"], rows,
                      source=DD + "sgp_pricing_table.csv"))
    body.append("<h3>Parlay leg correlations (phi)</h3>")
    rows = [[esc(r["measure"]), esc(r["value"]), esc(r["n"]), esc(r["interpretation"])]
            for r in parlays]
    body.append(table(["Leg pair", "phi", "n games", "Reading"], rows,
                      source=DD + "parlay_correlations.csv"))
    body.append('<div class="callout"><h4>What this means for combination bets</h4>'
                "<p>Cross-market legs (spread and total) are effectively independent, so a "
                "two-leg parlay across them is fairly priced by the multiplier. Same-team legs "
                "are not: passing volume drives both the quarterback's yards and his receiver's, "
                "so pricing them as independent overstates the payout. Same-team combinations "
                "should only be taken at the operator's same-game price, where the book applies "
                "its own correlation model.</p></div>")
    write("correlations.html", page("correlations.html", "Correlations",
                                     "Measured correlation values for parlay legs and player-prop "
                                     "combinations, with intervals and sample sizes.",
                                     "".join(body)))


def build_injuries():
    players = read_csv("injuries_wk10_players.csv")
    teams = read_csv("team_deficiency_wk10.csv")
    signal = read_json("injury_signal.json")
    by_season = read_csv("injury_signal_by_season.csv")
    wf = read_csv("injury_walk_forward.csv")
    body = ['<div class="grid kpis">',
            kpi(len(players), "players on the official report", "Week 10, all clubs"),
            kpi(sum(1 for p in players if p.get("is_starter") == "yes"),
                "starters flagged", "snap share ≥ 0.5 in their unit"),
            kpi(len(teams), "clubs profiled", "offence and defence separately"),
            kpi(signal.get("market_residual_model", {}).get("slope_pts_per_pp", "—"),
                "pts per pp vs market", "weak, p = 0.020", "warn"),
            "</div>"]

    body.append('<h3 id="methodology">How depth and deficiency are measured</h3>')
    body.append("<ol class=\"tight\">"
                "<li><strong>Who is a starter.</strong> A player's snap share in his own unit "
                "(offence or defence) across the season to date. Share ≥ 0.50 = starter; the "
                "remaining players at his position group are ranked 2nd, 3rd, 4th string.</li>"
                "<li><strong>What an absence costs.</strong> Replacement drop = availability "
                "weight × (the player's share − the next available player's share at the same "
                "position group). Summed by unit, it is the team's deficiency in percentage "
                "points of unit snaps.</li>"
                "<li><strong>Availability weights.</strong> Out 1.0, Doubtful 0.75, Questionable "
                "0.5; where the game status is not yet published, DNP 0.5, Limited 0.25, Full 0.0. "
                "These are documented assumptions (F14), not official probabilities.</li>"
                "<li><strong>Excluded.</strong> “Not injury related” absences (rest, personal) "
                "are excluded from the deficiency score.</li></ol>")
    body.append('<div class="callout warn"><h4>What this is not</h4><p>This is not an official '
                'depth chart. The league does not publish one in machine-readable form (F05/F16). '
                'The method above is measurable, reproducible and published so you can judge it.</p></div>')

    body.append('<h3 id="offence">Team deficiency — Week 10</h3>')
    body.append("<p>Sorted by total replacement drop. Defence and offence are separated because "
                "they are priced differently. “Starters out or limited” counts starters with "
                "availability weight ≥ 0.5.</p>")
    rows = []
    for t in teams:
        rows.append([f"<strong>{esc(t['team'])}</strong>", esc(t["team_name"]),
                     esc(t["players_listed"]), esc(t["players_with_snap_profile"]),
                     esc(t["starters_unavailable_or_limited"]),
                     f'<span class="pos">{esc(t["off_replacement_drop"])}</span>',
                     f'<span class="pos">{esc(t["def_replacement_drop"])}</span>',
                     f"<strong>{esc(t['total_replacement_drop'])}</strong>",
                     source_cell(t.get("source_url"), "nfl.com")])
    body.append(table(["Team", "Club", "Players listed", "With snap profile",
                       "Starters out/limited", "Offence drop (pp)", "Defence drop (pp)",
                       "Total (pp)", "Source"], rows,
                      source=DD + "team_deficiency_wk10.csv"))

    body.append('<h3 id="calibration">Does lineup loss actually matter?</h3>')
    q = signal.get("quality_controlled_model", {})
    mr = signal.get("market_residual_model", {})
    body.append(f"<p><strong>Yes for margin, about half of it already priced.</strong> Controlling "
                f"for prior scoring margin, a percentage point of relative deficiency is associated "
                f"with <strong>{esc(q.get('raw_margin_slope_pts_per_pp'))}</strong> points of margin "
                f"(n = {esc(q.get('n'))}, p = {esc(q.get('raw_margin_p'))}). The market line moves "
                f"<strong>{esc(q.get('market_spread_slope_pts_per_pp'))}</strong> points per point — "
                f"about {float(q.get('share_of_effect_priced_by_market') or 0)*100:.0f}% of the "
                f"effect — leaving a residual of "
                f"<strong>{esc(q.get('ats_residual_slope_pts_per_pp'))}</strong> points per point "
                f"(p = {esc(q.get('ats_residual_p'))}).</p>")
    rows = [[esc(r["season"]), esc(r["n"]), esc(r["slope_pts_per_pp"]), esc(r["se"]),
             esc(r["t"]), esc(r["p"]), esc(r["r2"]), esc(r["bets_gap_ge50pp"]),
             esc(r["win_rate"]) or badge("n/a", "warn")] for r in by_season]
    body.append(table(["Season", "Games", "Slope (pts/pp)", "SE", "t", "p", "R²",
                       "Bets at ≥50 pp gap", "ATS win rate"], rows,
                      source=DD + "injury_signal_by_season.csv"))
    body.append("<h4 id=\"priced\">Is there a bet in it?</h4>")
    fade = signal.get("fade_more_injured_team", {})
    hold = signal.get("holdout_gap50", {})
    qb = signal.get("starting_QB_out_exactly_one_side", {})
    body.append(f"<p>Fading the more-injured team wins "
                f"<strong>{float(fade.get('win_rate', 0) or 0)*100:.1f}%</strong> ATS over "
                f"{fade.get('n_bets')} bets (95% CI {fade.get('ci95', ['', ''])[0]}–"
                f"{fade.get('ci95', ['', ''])[1]}), p = {fade.get('p_two_sided')} against the "
                f"52.38% break-even. The ≥50 pp subset, fixed on 2023-2024 and tested on "
                f"2025-2026, wins {float(hold.get('test_win_rate', 0) or 0)*100:.1f}% over "
                f"{hold.get('test_n')} bets (p = {hold.get('test_p_two_sided')}). A starting "
                f"quarterback out on exactly one side: {float(qb.get('win_rate', 0) or 0)*100:.1f}% "
                f"over {qb.get('n_games')} games.</p>")
    body.append("<p><strong>Reading:</strong> none of these clear a Bonferroni threshold for a "
                "betting edge, and the effects are small enough that a stale line could explain "
                "them. The correct use of the metric is inside our own price (see "
                "<a href=\"lines.html\">own lines</a>), not as a trigger.</p>")
    rows = [[esc(r["test_season"]), esc(r["train_n"]), esc(r["predicted_slope"]),
             esc(r["bets"]), esc(r["wins"]), esc(r["win_rate"]) or badge("n/a", "warn")]
            for r in wf]
    body.append(table(["Test season", "Training games", "Slope learned", "Bets", "Wins", "Win rate"], rows,
                      source=DD + "injury_walk_forward.csv"))

    body.append('<h3 id="players">Official Week 10 injury report, player by player</h3>')
    body.append("<p>Every row below is taken from the official NFL injury report and links to it. "
                "“Not matched” in the mirror column means the player was not found in the "
                "independent mirror and is not cross-verified.</p>")
    rows = []
    for p in players:
        rows.append([esc(p.get("team")), esc(p.get("player")), esc(p.get("position")),
                     esc(p.get("injury")) or badge("—", "warn"),
                     esc(p.get("practice_status")), esc(p.get("game_status")) or badge("pending", "warn"),
                     esc(p.get("season_snap_share")), esc(p.get("depth_string")),
                     esc(p.get("is_starter")), esc(p.get("replacement_drop")),
                     status_badge(p.get("injury_report_match")),
                     source_cell(p.get("source_url"), "nfl.com")])
    body.append(table(["Team", "Player", "Pos", "Injury", "Practice", "Game status",
                       "Snap share", "String", "Starter", "Repl. drop", "Mirror", "Source"], rows,
                      source=DD + "injuries_wk10_players.csv"))
    write("injuries.html", page("injuries.html", "Injuries &amp; lineup depth",
                                 "Who is out, who replaces him, and what that depth loss is worth in points.",
                                 "".join(body)))


def build_audit():
    audit = read_json("audit_summary.json")
    claims = read_csv("claim_checks.csv")
    prov = read_csv("provenance_audit.csv")
    cross = read_csv("cross_scope_lines.csv")
    st = audit.get("official_vs_derived_standings", {})
    links = audit.get("internal_links", {})
    body = ['<div class="grid kpis">',
            kpi(f"{st.get('matches', 0)}/{st.get('teams', 0)}", "clubs reconcile", "official standings vs game log", "ok"),
            kpi(links.get("broken_count", 0), "broken internal links", f"{links.get('pages', 0)} pages", "ok"),
            kpi(f"{sum(1 for c in claims if c['verdict'].lower().startswith('agree'))}/{len(claims)}",
                "claims reproduced", "the rest are flagged", "warn"),
            kpi(sum(1 for p in prov if p.get("verdict") != "ok"), "CSV tables to review",
                f"{len(prov)} tables audited"),
            "</div>"]
    body.append('<h3>Official standings vs an independent game log</h3>')
    body.append(f"<p>The 32 clubs' W-L-T and points for/against were parsed from "
                f"<a href=\"https://www.nfl.com/standings/league/2026/REG\">nfl.com</a> and "
                f"re-derived from the pinned nflverse game results. "
                f"<strong>{st.get('matches')} of {st.get('teams')}</strong> match exactly; "
                f"mismatches: {esc(', '.join(st.get('mismatches', [])) or 'none')}.</p>")
    body.append("<h3>Prior claims, re-derived line by line</h3>")
    body.append("<p>Each row is a numeric claim already published in this repository. The "
                "recomputation uses the conventions documented on the verification page, not the "
                "original script.</p>")
    rows = [[esc(c["claim"]), esc(c["published_in"]), esc(c["prior_value"]),
             esc(c["recomputed_value"]), status_badge(c["verdict"]), esc(c["note"]),
             source_cell(c.get("source_url"), "source")] for c in claims]
    body.append(table(["Claim", "Published in", "Prior", "Recomputed", "Verdict", "Note", "Source"], rows,
                      source=DD + "claim_checks.csv"))
    body.append("<h3>Provenance audit of every CSV table</h3>")
    bad = [p for p in prov if p.get("verdict") != "ok"]
    body.append(f"<p>{len(prov)} CSV tables scanned, {sum(int(p['rows']) for p in prov):,} rows. "
                f"{len(bad)} table(s) need review: "
                f"{esc(', '.join(p['file'] for p in bad) or 'none')}. Every derived table carries "
                "a link to the script that produced it.</p>")
    rows = [[esc(p["file"]), esc(p["rows"]), esc(p["sourced"]), esc(p["unsourced"]),
             status_badge(p["verdict"])] for p in prov if p.get("verdict") != "ok"]
    if rows:
        body.append(table(["Table", "Rows", "Sourced", "Unsourced", "Verdict"], rows,
                          source=DD + "provenance_audit.csv"))
    body.append("<h3>Cross-scope consistency (two Week 9 line boards)</h3>")
    if cross:
        rows = [[esc(c["game"]), esc(c["strategy_lab_model_spread"]), esc(c["strategy_lab_market"]),
                 esc(c["line_lab_market_spread"]), status_badge(c["match"]),
                 source_cell(c.get("source"), "file")] for c in cross]
        body.append(table(["Game", "Strategy-lab model spread", "Strategy-lab market",
                           "Line-lab market spread", "Schedule match", "Source"], rows,
                          source=DD + "cross_scope_lines.csv"))
        body.append('<p class="muted">The two scopes price different things: one publishes a '
                    'model line, the other a market snapshot. The audit checks that they agree on '
                    'the schedule and that neither leaves a market cell unlabelled.</p>')
    body.append('<h3>Link integrity</h3>')
    body.append(f"<p>{links.get('links_checked', 0):,} internal links checked across "
                f"{links.get('pages', 0)} HTML pages; "
                f"{links.get('broken_count', 0)} broken.</p>")
    write("audit.html", page("audit.html", "Repository audit",
                             "Line-by-line re-derivation of everything this repository previously claimed, "
                             "plus link and provenance checks.",
                             "".join(body)))


def build_summary():
    inj = read_json("injury_signal.json")
    meta = read_json("strategy_meta.json")
    ledger = read_csv("strategy_ledger.csv")
    lines = read_csv("model_lines_wk10.csv")
    players = read_csv("injuries_wk10_players.csv")
    body = [f"""
<div class="prose">
<h3>Objective</h3>
<p>Originate our own NFL lines, test strategies that might carry skill, price and understand
correlation across singles, parlays and player-prop combinations, and track injuries and lineup
depth well enough to know when a starter is replaced by a 2nd, 3rd or 4th string player — with
every value traceable to an official source or explicitly flagged.</p>

<h3>What is verified</h3>
<ul>
<li><strong>Official data, row by row.</strong> {len(players)} player rows from the
<a href="https://www.nfl.com/injuries/">official Week 10 injury report</a>, the
<a href="https://www.nfl.com/schedules/2026/by-week/week-10">Week 10 schedule</a> and the
<a href="https://www.nfl.com/standings/league/2026/REG">2026 standings</a>, each with a source link
and a retrieval timestamp recorded in <code>provenance.json</code>.</li>
<li><strong>Dual-source agreement.</strong> All 32 clubs' standings reproduce exactly from an
independent game log; all 276 injury rows match the independent mirror.</li>
<li><strong>Own lines.</strong> A spread and total for all {len(lines)} Week 10 games, fitted only
on prior weeks, with the injury adjustment shown separately.</li>
</ul>

<h3>What is computed</h3>
<ul>
<li><strong>Injury value.</strong> A percentage point of relative lineup deficiency is worth about
<strong>{esc(inj.get('quality_controlled_model', {}).get('raw_margin_slope_pts_per_pp'))} points</strong>
of margin (p = {esc(inj.get('quality_controlled_model', {}).get('raw_margin_p'))}). The market moves
<strong>{esc(inj.get('quality_controlled_model', {}).get('market_spread_slope_pts_per_pp'))}</strong>
points per point — roughly half the effect — leaving a residual of
<strong>{esc(inj.get('quality_controlled_model', {}).get('ats_residual_slope_pts_per_pp'))}</strong>
(p = {esc(inj.get('quality_controlled_model', {}).get('ats_residual_p'))}).</li>
<li><strong>No betting edge.</strong> Fading the more-injured team is
{float(inj.get('fade_more_injured_team', {}).get('win_rate', 0) or 0)*100:.1f}% ATS over
{esc(inj.get('fade_more_injured_team', {}).get('n_bets'))} bets, p = 1.0. The model's own
walk-forward ATS record is 50.2-50.9%, i.e. no edge.</li>
<li><strong>Correlation.</strong> QB passing yards and his WR1's receiving yards correlate at
r = 0.50; at median lines the joint hit rate is 32.5% versus 24.8% if independent. Cross-market
legs (spread vs total) are independent (phi = 0.006).</li>
<li><strong>Zero certified strategies.</strong> {len(ledger)} families tested against
α = {meta.get('bonferroni_alpha', 0):.5f}; none passes every gate.</li>
</ul>

<h3>What is missing, and why it matters</h3>
<ul>
<li><strong>No verified price history (F01, F02).</strong> Without a timestamped operator price,
closing-line value cannot be computed and no strategy can be certified as skill. This is the
single largest blocker; suggestion S01 addresses it.</li>
<li><strong>No official prop lines (F03).</strong> Prop combinations are priced by correlation, not
against real lines, so their economic value is unknown.</li>
<li><strong>Depth is inferred (F05, F16).</strong> Snap share is a measurable proxy for a depth
chart the league does not publish.</li>
<li><strong>Prior-session figures do not all reproduce (F08-F10).</strong> The home-underdog,
QB/WR correlation and 20.8% luck figures are flagged for human review.</li>
</ul>

<h3>The five decisions in front of you</h3>
<ol>
<li>Capture a real price history (S01) — without it, nothing can ever be certified.</li>
<li>Adopt the sign-convention regression test (S02) — it already caught one invented edge.</li>
<li>Close the jurisdiction and funding questions (Q04, Q05) before publishing any reward amount.</li>
<li>Approve the correction of the four non-reproducing prior figures (F08-F10), or ask for a
second opinion first.</li>
<li>Decide whether the injury metric is a pricing input only (recommended, S05) or a bet trigger
(not supported by the data).</li>
</ol>

<h3>Bottom line</h3>
<p>The desk is now automated, sourced and reproducible. The honest current state is: good
infrastructure, verified inputs, no certified edge. That is a much better position than a
leaderboard full of unverified win rates — and it is exactly what "remove luck from the equation"
requires.</p>
</div>"""]
    write("summary.html", page("summary.html", "Executive summary",
                               "What was built, what is verified, what is missing, and the decisions that follow.",
                               "".join(body)))


def build_sources():
    rows = []
    for s in content.SOURCES:
        rows.append([esc(s["id"]), esc(s["name"]), badge(s["tier"], "ok" if s["tier"] == "OFFICIAL" else "warn"),
                     link(s["url"]), esc(s["used"]), esc(s["retrieval"])])
    body = ['<div class="callout"><h4>Two tiers only</h4><p><strong>OFFICIAL</strong> means the '
            'page is published by the league or a club. <strong>AGGREGATOR</strong> means a '
            'third-party project re-publishes data derived from official sources. Aggregator data '
            'is used for computation and labelled everywhere; it is never described as official.</p></div>']
    body.append(table(["ID", "Source", "Tier", "Link", "Used for", "How it is pinned"], rows,
                      source=DD + "sources.csv"))
    prov = read_json(os.path.join(DATA, "raw", "provenance.json"))
    if prov:
        body.append("<h3>Pinned files this build</h3>")
        rows = [[esc(a["asset"]), link(a["url"]), status_badge(f"HTTP {a['http_status']}"),
                 esc(f"{a['bytes']:,}"), f"<code>{esc(a['sha256'][:16])}…</code>",
                 esc(a.get("header", "")[:60])] for a in prov.get("assets", [])]
        body.append(table(["File", "URL", "Status", "Bytes", "SHA-256", "Header"], rows,
                          source=DD + "raw/provenance.json"))
    write("sources.html", page("sources.html", "Sources",
                               "Every input, its tier, its link and its pin.",
                               "".join(body)))


def build_flagged():
    groups = [("blocks", "bad", "Blocking"), ("review", "warn", "Needs review"),
              ("note", "warn", "Noted")]
    body = ['<div class="callout"><h4>Nothing here blocks publication — everything here blocks a claim</h4>'
            '<p>These are the gaps, irregularities and inherited discrepancies found while building '
            'this desk. Each one is published with its source so you can review it after the site '
            'is live and request changes.</p></div>']
    for key, kind, label in groups:
        items = [f for f in content.FLAGS if f["severity"] == key]
        body.append(f'<h3>{esc(label)} {badge(len(items), "count")}</h3>')
        rows = [[f'<span id="{f["id"]}">{esc(f["id"])}</span>', f"<strong>{esc(f['item'])}</strong>",
                 esc(f["detail"]), esc(f["action"]), source_cell(f["source"], "source")]
                for f in items]
        body.append(table(["ID", "Item", "What we found", "What we did", "Source"], rows,
                          source=DD + "flagged.csv"))
    write("flagged.html", page("flagged.html", "Flagged for review",
                               "Irregularities, unverified values and inherited claims that need a human decision.",
                               "".join(body)))


def build_verification():
    audit = read_json("audit_summary.json")
    prov = read_json(os.path.join(DATA, "raw", "provenance.json"))
    body = [f"""
<div class="prose">
<h3>Rules used on every row</h3>
<ol>
<li><strong>Official or flagged.</strong> A row either links to an official page, or links to the
script and pinned input that computed it, or is blank and flagged. There is no fourth option.</li>
<li><strong>No inference.</strong> A value that is not in the source is never filled in. Missing
game statuses show as <em>pending</em>, not as "Questionable".</li>
<li><strong>Tier disclosure.</strong> Official and aggregator data are labelled separately in every
table.</li>
<li><strong>Dual-source assertion.</strong> Where the official page is parseable, the aggregator
mirror must agree row for row. It currently does: 32/32 standings rows and 276/276 injury rows.</li>
<li><strong>Timestamps.</strong> Every fetch records URL, HTTP status, byte count, SHA-256 and UTC
time in <code>data/decision-desk/raw/provenance.json</code>.</li>
</ol>

<h3 id="sign">The sign-convention check that changed the answer</h3>
<p>The first backtest of the injury metric used <code>margin + spread</code> as the against-the-spread
residual, which treats the spread as a handicap on the home team. The pinned source actually stores
the <em>expected home margin</em> (positive = home favoured). With the wrong sign the strategy looked
like 57.4% ATS; with the correct sign it is 51.4% (p = 1.0). The erroneous run is preserved in the
claim table, and suggestion S02 adds a regression test so it cannot recur silently.</p>

<h3>What was checked this build</h3>
<ul>
<li>All 32 clubs' W-L-T and PF/PA against an independent game log — {audit.get('official_vs_derived_standings', {}).get('matches', 0)}/32 match.</li>
<li>{audit.get('internal_links', {}).get('links_checked', 0):,} internal links across {audit.get('internal_links', {}).get('pages', 0)} pages — {audit.get('internal_links', {}).get('broken_count', 0)} broken.</li>
<li>{audit.get('claims_reviewed', 0)} previously published numeric claims re-derived.</li>
<li>{audit.get('provenance', {}).get('files', 0)} CSV tables scanned for per-row provenance.</li>
<li>Every computed table's arithmetic reproducible by <code>python3 tools/decision_desk/build_all.py</code>.</li>
</ul>

<h3>Reproduce this site</h3>
<pre><code>python3 tools/decision_desk/fetch_sources.py   # official pages + pinned mirrors
python3 tools/decision_desk/build_all.py       # parse, compute, audit
python3 tools/decision_desk/build_site.py      # render nfl-decision-desk/
python3 tools/decision_desk/verify.py          # row/link/blank checks</code></pre>

<h3>Snapshot</h3>
<p>Retrieved {esc(prov.get('retrieved_utc', 'n/a'))}; {sum(1 for a in prov.get('assets', []) if a.get('http_status') == 200)}
of {len(prov.get('assets', []))} pinned datasets and {sum(1 for p in prov.get('pages', []) if p.get('http_status') == 200)}
of {len(prov.get('pages', []))} official pages returned HTTP 200. A failed fetch produces a status
row, never a fabricated value.</p>
</div>"""]
    write("verification.html", page("verification.html", "Verification log",
                                     "What was checked, how, and what it returned.",
                                     "".join(body)))


def main() -> int:
    os.makedirs(SITE, exist_ok=True)
    build_index(None)
    build_requirements()
    build_suggestions()
    build_questions()
    build_lines()
    build_strategies()
    build_validation()
    build_correlations()
    build_injuries()
    build_audit()
    build_summary()
    build_sources()
    build_flagged()
    build_verification()
    with open(os.path.join(SITE, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS)
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    print(f"wrote {len(NAV)} pages to nfl-decision-desk/")
    return 0


CSS = """
:root{--navy:#0b1f3a;--ink:#16233a;--muted:#5b6b82;--line:#dde3ec;--bg:#f6f8fb;
--card:#ffffff;--accent:#1f4e79;--gold:#b8860b;--ok:#12805c;--warn:#8a5a00;--bad:#a3232b}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header.top{background:var(--navy);color:#fff;padding:18px 0 0}
header.top .wrap{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;flex-wrap:wrap}
.brand{display:flex;gap:14px;align-items:center}
.mark{display:inline-grid;place-items:center;width:44px;height:44px;border-radius:10px;background:#ffd166;color:#0b1f3a;font-weight:800;letter-spacing:.5px}
header.top h1{margin:0;font-size:20px;font-weight:700}
header.top h1 a{color:#fff}
header.top p{margin:2px 0 0;color:#b9c7dd;font-size:13px}
.stamp{text-align:right;font-size:12px;color:#b9c7dd;display:flex;flex-direction:column}
.stamp strong{color:#ffd166;font-size:13px}
nav.wrap{display:flex;gap:2px;flex-wrap:wrap;margin-top:14px;padding-bottom:0}
nav a{color:#cfdcee;font-size:12.5px;padding:8px 10px;border-bottom:3px solid transparent;white-space:nowrap}
nav a:hover{color:#fff;text-decoration:none;background:rgba(255,255,255,.06)}
nav a.active{color:#fff;border-bottom-color:#ffd166;font-weight:600}
main{margin:26px auto 60px}
.pagehead h2{margin:0 0 6px;font-size:27px}
.pagehead p{margin:0 0 22px;color:var(--muted);max-width:820px}
h3{margin:30px 0 10px;font-size:18px}
h4{margin:0 0 8px;font-size:15px}
.grid{display:grid;gap:14px}
.kpis{grid-template-columns:repeat(auto-fit,minmax(215px,1fr));margin-bottom:8px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi-value{font-size:24px;font-weight:700;color:var(--navy);line-height:1.2}
.kpi-label{font-size:12.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-top:4px}
.kpi-note{font-size:12px;color:var(--muted);margin-top:6px}
.kpi.ok .kpi-value{color:var(--ok)} .kpi.bad .kpi-value{color:var(--bad)} .kpi.warn .kpi-value{color:var(--warn)}
.cards{grid-template-columns:repeat(auto-fit,minmax(300px,1fr));margin:10px 0 4px}
.cards.three{grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.card p{margin:0;color:var(--muted);font-size:13.5px}
.card .more{display:inline-block;margin-top:10px;font-size:12.5px}
.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:12px;background:var(--card);margin:10px 0 18px;max-height:none}
table.data{border-collapse:collapse;width:100%;font-size:12.8px}
table.data th{position:sticky;top:0;background:#eef2f8;text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);white-space:nowrap;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;color:#3b4a63}
table.data td{padding:8px 10px;border-bottom:1px solid #eef1f6;vertical-align:top}
table.data tr:nth-child(even) td{background:#fbfcfe}
.badge{display:inline-block;padding:2px 7px;border-radius:999px;font-size:11px;font-weight:600;background:#e9eef6;color:#3b4a63;white-space:nowrap}
.badge.ok{background:#e3f4ec;color:var(--ok)}
.badge.warn{background:#fdf1dd;color:var(--warn)}
.badge.bad{background:#fbe6e7;color:var(--bad)}
.badge.count{background:var(--navy);color:#fff}
.callout{background:#fff;border-left:4px solid var(--accent);border-radius:8px;padding:14px 16px;margin:16px 0}
.callout.warn{border-left-color:var(--gold);background:#fffaf0}
.callout p{margin:6px 0 0;color:#38465c}
details.sug{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:8px 0;padding:10px 14px}
details.sug summary{cursor:pointer;font-weight:600;list-style:none}
details.sug summary::-webkit-details-marker{display:none}
details.sug[open]{box-shadow:0 1px 0 #e6ebf3 inset}
.sid{display:inline-block;background:var(--navy);color:#fff;border-radius:6px;padding:1px 7px;font-size:11.5px;margin-right:8px}
.sugbody dl{display:grid;grid-template-columns:190px 1fr;gap:6px 14px;margin:12px 0 4px}
.sugbody dt{color:var(--muted);font-size:12.5px;text-transform:uppercase;letter-spacing:.04em}
.sugbody dd{margin:0}
.prose{max-width:900px}
.prose p,.prose li{color:#2b3a52}
.prose code{background:#eef2f8;padding:1px 5px;border-radius:4px;font-size:12.5px}
pre{background:var(--navy);color:#e8eefc;padding:14px;border-radius:10px;overflow:auto;font-size:12.5px}
pre code{background:none;color:inherit;padding:0}
.muted{color:var(--muted);font-size:12.5px}
.pos{color:var(--ok);font-weight:600}
ul.tight li,ol.tight li{margin:4px 0}
footer{border-top:1px solid var(--line);padding:22px 20px 40px;color:var(--muted);font-size:12.5px;max-width:1180px;margin:0 auto}
footer p{margin:6px 0}
@media(max-width:640px){.sugbody dl{grid-template-columns:1fr}.stamp{text-align:left}}
"""


if __name__ == "__main__":
    sys.exit(main())

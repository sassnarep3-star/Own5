"""Deterministic static builder for the 715e2cd4 NFL line-origination desk.

Reads only data/*.csv, writes index.html, 13 category pages and style.css.
No clock, no network, no git, no randomness: byte-identical on every run.
"""

import csv
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = HERE

PAGES = [
    ("index.html", "Overview", "Decision readiness: every requirement, the gate blocking it, and the number that would clear it."),
    ("lines.html", "Originated lines", "Week 11 fair lines in the required order (side, then total, then moneyline), with market and residual columns."),
    ("results.html", "Verified results", "The 136-game corpus, the Week 10 holdout scorecard and the reconciliation to official standings."),
    ("availability.html", "Injuries &amp; depth", "Official Week 11 designations, per-club counts, and exactly which depth fields are missing."),
    ("leaderboard.html", "Leaderboard", "Signal and staking scored separately, with control baselines and no certified strategy."),
    ("correlations.html", "Correlations", "Every correlation computed from official numbers, with n and a confidence interval."),
    ("luck.html", "Removal of luck", "Why a short-run win rate cannot be told apart from noise, and how few certified strategies exist."),
    ("gates.html", "Validation gates", "G0-G9, each with its pass criterion, status and the observation that sets it."),
    ("strategies.html", "Strategies", "Pre-registered definitions, the two-sided what-would-change-our-mind field, and the demotion rules."),
    ("prices.html", "Price data", "The price policy, the snapshot schema, and the honest zero coverage figure."),
    ("questions.html", "Questions &amp; information", "What must be answered before any decision is reasonable, and how to discover the missing facts."),
    ("suggestions.html", "Suggestions", "Proposed improvements with cost, recommendation and decision state. Nothing is implemented without a decision."),
    ("flagged.html", "Flagged for review", "Unverified values, irregularities and the source links for each."),
    ("diff.html", "What changed", "The weekly diff: what moved since the previous dated snapshot, and what could not be diffed."),
    ("sources.html", "Sources", "Every official source read, with the clock time of the read."),
]

NAV_ORDER = [p[0] for p in PAGES]


def esc(x):
    return html.escape(str(x), quote=True)


def read(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def linkify(v):
    """Render a cell. Blank cells are visually marked UNVERIFIED, never '-'."""
    v = "" if v is None else str(v)
    if v.startswith("http://") or v.startswith("https://"):
        host = v.split("/")[2] if "//" in v else v
        label = "nfl.com" if "nfl.com" in host else ("github" if "github" in host else host)
        return '<a class="src" href="%s" rel="noopener" target="_blank">%s</a>' % (esc(v), esc(label))
    if v.strip() == "":
        return '<span class="blank">blank</span>'
    low = v.lower()
    if low.startswith("unverified") or low.startswith("not certified") or low.startswith("blocked"):
        return '<span class="badge warn">%s</span>' % esc(v)
    if v in ("MATCH", "MET", "PASSED", "MET "):
        return '<span class="badge ok">%s</span>' % esc(v)
    if v in ("MISMATCH", "NOT MET", "FAILED", "REJECTED"):
        return '<span class="badge bad">%s</span>' % esc(v)
    if v in ("PARTIAL", "BLOCKED", "NOT TRIGGERED", "Needs review"):
        return '<span class="badge mid">%s</span>' % esc(v)
    return esc(v)


def table(headers, rows, cls="", caption=None, link_cols=(), status_cols=(), num_cols=()):
    out = ['<div class="tw"><table class="%s">' % cls]
    if caption:
        out.append("<caption>%s</caption>" % caption)
    out.append("<thead><tr>" + "".join("<th>%s</th>" % esc(h) for h in headers) + "</tr></thead><tbody>")
    for r in rows:
        cells = []
        for i, v in enumerate(r):
            if i in link_cols:
                cells.append("<td>%s</td>" % linkify(v))
            elif i in status_cols:
                cells.append("<td>%s</td>" % linkify(v))
            elif i in num_cols:
                cells.append('<td class="num">%s</td>' % linkify(v))
            else:
                cells.append("<td>%s</td>" % linkify(v))
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def kv(rows, headers=("item", "value", "note")):
    return table(list(headers), rows, cls="kv")


CSS = """
:root{--bg:#0b1016;--panel:#111923;--panel2:#0e151e;--line:#1f2c3a;--ink:#e6edf5;--dim:#8fa3b8;
--ok:#22c07a;--warn:#f0b429;--bad:#e5534b;--accent:#4aa8ff;--mono:ui-monospace,SFMono-Regular,Menlo,monospace}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header.top{position:sticky;top:0;z-index:20;background:rgba(11,16,22,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.wrap{max-width:1240px;margin:0 auto;padding:0 20px}
.brand{display:flex;align-items:center;gap:12px;padding:14px 0 10px}
.brand b{font-size:16px;letter-spacing:.2px}
.brand span{color:var(--dim);font-size:12.5px}
nav.tabs{display:flex;flex-wrap:wrap;gap:2px;padding-bottom:10px}
nav.tabs a{font-size:13px;padding:6px 10px;border-radius:7px;color:var(--dim)}
nav.tabs a:hover{background:var(--panel);color:var(--ink);text-decoration:none}
nav.tabs a.on{background:#16263a;color:#bfe0ff;box-shadow:inset 0 0 0 1px #21405f}
main{padding:26px 0 60px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.2px}
h2{font-size:17px;margin:34px 0 10px;padding-bottom:7px;border-bottom:1px solid var(--line)}
h3{font-size:14.5px;margin:22px 0 8px;color:#cfe0f2}
p.lede{color:var(--dim);margin:0 0 18px;max-width:70ch}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));margin:18px 0 6px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:14px 15px}
.card .k{color:var(--dim);font-size:11.5px;text-transform:uppercase;letter-spacing:.07em}
.card .v{font-size:23px;font-weight:600;margin-top:4px;font-variant-numeric:tabular-nums}
.card .s{color:var(--dim);font-size:12px;margin-top:3px}
.card.ok{border-left:3px solid var(--ok)}.card.bad{border-left:3px solid var(--bad)}
.card.warn{border-left:3px solid var(--warn)}.card.info{border-left:3px solid var(--accent)}
.tw{overflow:auto;border:1px solid var(--line);border-radius:11px;background:var(--panel2);margin:10px 0 4px}
table{border-collapse:collapse;width:100%;font-size:13px}
caption{caption-side:top;text-align:left;padding:11px 13px 0;color:var(--dim);font-size:12px}
th{position:sticky;top:0;background:#101b26;text-align:left;padding:9px 11px;font-weight:600;
color:#a9bed3;font-size:11.5px;text-transform:uppercase;letter-spacing:.045em;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:8px 11px;border-bottom:1px solid #16212d;vertical-align:top}
tbody tr:hover{background:#131e2a}
td.num{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--mono);font-size:12.5px}
.blank{color:#5c6e82;font-style:italic;font-size:12px}
.badge{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;font-weight:600;white-space:nowrap}
.badge.ok{background:rgba(34,192,122,.14);color:#5fe0a4}
.badge.bad{background:rgba(229,83,75,.15);color:#ff8f88}
.badge.mid{background:rgba(240,180,41,.14);color:#f5c95e}
.badge.warn{background:rgba(143,163,184,.12);color:#a9bed3}
a.src{font-family:var(--mono);font-size:11.5px}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent);
border-radius:9px;padding:12px 15px;margin:16px 0;color:#c3d4e5;font-size:13.5px}
.note.bad{border-left-color:var(--bad)}.note.warn{border-left-color:var(--warn)}
.note b{color:#fff}
ul.tight{margin:8px 0 0;padding-left:20px;color:#c3d4e5}ul.tight li{margin:4px 0}
footer{border-top:1px solid var(--line);color:var(--dim);font-size:12px;padding:18px 0 40px}
code{font-family:var(--mono);font-size:12.5px;background:#16212d;padding:1px 5px;border-radius:5px}
.two{display:grid;gap:16px;grid-template-columns:1fr 1fr}
@media(max-width:820px){.two{grid-template-columns:1fr}}
"""


def shell(active, title, body, subtitle=""):
    tabs = []
    for slug, label, _ in PAGES:
        cls = ' class="on"' if slug == active else ""
        tabs.append('<a href="%s"%s>%s</a>' % (slug, cls, label))
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s · Own5 NFL line desk</title>
<link rel="stylesheet" href="style.css">
</head><body>
<header class="top"><div class="wrap">
<div class="brand"><b>Own5 · NFL line origination desk</b>
<span>session 715e2cd4 · data read 2026-11-19 · no certified strategy</span></div>
<nav class="tabs">%s</nav>
</div></header>
<main><div class="wrap">
<h1>%s</h1>
%s
%s
</div></main>
<footer><div class="wrap">
Every numeric value on this site is either computed in-repo from an official nfl.com page or left blank and
flagged. Market prices are blank by policy P-01. No backtest figure appears on the leaderboard.
&nbsp;·&nbsp; <a href="https://github.com/sassnarep3-star/Own5/tree/main/nfl-desk-715e2cd4">source</a>
</div></footer></body></html>
""" % (esc(title), "".join(tabs), title,
       ('<p class="lede">%s</p>' % subtitle) if subtitle else "", body)


# ------------------------------------------------------------------- pages
def page_index():
    req = read("requirements.csv")
    gates = read("gates.csv")
    sc = read("scorecard.csv")
    lp = read("luck_panel.csv")
    flags = read("flagged.csv")

    met = sum(1 for r in req if r["status"] == "MET")
    part = sum(1 for r in req if r["status"] == "PARTIAL")
    notmet = sum(1 for r in req if r["status"] in ("NOT MET", "BLOCKED"))
    rej = sum(1 for r in req if r["status"] == "REJECTED")
    passed = sum(1 for g in gates if g["status"] == "PASSED")
    failed = sum(1 for g in gates if g["status"] in ("FAILED", "BLOCKED"))
    side = [r for r in sc if "side" in r["metric"]][0]
    tot_a = [r for r in sc if "estimator A" in r["metric"]][0]
    tot_b = [r for r in sc if "estimator B" in r["metric"]][0]
    bss = [r for r in sc if "Brier" in r["metric"]][0]
    homeci = [r for r in lp if "Home win share" in r["item"]][0]
    need = [r for r in lp if "Bets needed" in r["item"]][0]

    cards = """<div class="grid">
<div class="card bad"><div class="k">Certified strategies</div><div class="v">0</div>
<div class="s">none has cleared G1-G4</div></div>
<div class="card info"><div class="k">Requirements tracked</div><div class="v">%d</div>
<div class="s">%d met · %d partial · %d not met/blocked · %d rejected</div></div>
<div class="card warn"><div class="k">Validation gates passed</div><div class="v">%d / %d</div>
<div class="s">G0 passed; G1-G4, G8, G9 fail or are blocked</div></div>
<div class="card bad"><div class="k">Markets with a market price</div><div class="v">0 / 39</div>
<div class="s">no licensed feed (F-01)</div></div>
<div class="card info"><div class="k">Bets needed to prove 55%% skill</div><div class="v">%s</div>
<div class="s">80%% power, two-sided 5%%</div></div>
<div class="card bad"><div class="k">Flagged items for review</div><div class="v">%d</div>
<div class="s">every blank traces to one</div></div>
</div>""" % (len(req), met, part, notmet, rej, passed, len(gates), "{:,}".format(int(need["value"])), len(flags))

    headline = """<div class="note bad"><b>The single most decision-relevant fact on this site:</b>
on the only chronological holdout that exists (Week 10, 14 official finals), both pre-registered total
estimators <b>lost to a constant league-mean total</b> (skill %s and %s against the constant-mean baseline),
while the side estimator beat a constant home-margin baseline (skill %s) on a sample far too small to mean
anything. A total model that cannot beat the league average is not a total model yet.</div>""" % (
        esc(tot_a["skill_vs_baseline"]), esc(tot_b["skill_vs_baseline"]), esc(side["skill_vs_baseline"]))

    rows = [[r["req_id"], r["requirement"], r["category"], r["status"], r["blocking_gate"],
             r["number_that_would_clear_it"], r["observed"], r["flag_id"], r["evidence_url"]] for r in req]
    req_tbl = table(["#", "Requirement", "Category", "Status", "Gate that blocks it",
                     "The number that would clear it", "Observed here", "Flag", "Evidence"],
                    rows, status_cols=(3,), link_cols=(8,),
                    caption="Decision-readiness table: one row per requirement. Status is a judgement about "
                            "evidence held in this namespace, not a claim about the world.")

    scores = table(["Metric", "Value", "n", "95% interval", "Baseline", "Skill vs baseline", "Verdict"],
                   [[r["metric"], r["value"], r["n"],
                     ("%s – %s" % (r["ci_low"], r["ci_high"])) if r["ci_low"] else "",
                     r["baseline"], r["skill_vs_baseline"], r["verdict"]] for r in sc],
                   num_cols=(1, 2, 5), status_cols=(6,),
                   caption="Week 10 holdout. Informational only: 14 observations cannot certify anything.")

    what = """<div class="two">
<div class="card"><div class="k">What this desk does</div>
<ul class="tight">
<li>Originates its own line for all 13 Week 11 fixtures, side first, then total, then moneyline.</li>
<li>Scores the frozen model out of sample on a chronological holdout and publishes the failures.</li>
<li>Computes every correlation from official numbers only and prints n next to each one.</li>
<li>Tracks 66 requirements against the brief, each with its blocking gate and its clearing number.</li>
<li>Publishes 16 reviewable suggestions and 15 questions that must be answered before decisions.</li>
</ul></div>
<div class="card"><div class="k">What this desk refuses to do</div>
<ul class="tight">
<li>Invent a market price, a depth rank, a starter, a snap share or a win rate.</li>
<li>Put a backtest figure on the leaderboard (policy LB-01).</li>
<li>Multiply marginal probabilities to price a parlay (gate G8).</li>
<li>Infer depth from jersey number, experience or salary (rejected in writing).</li>
<li>Say "not listed" when the truth is "on injured reserve" (F-13).</li>
</ul></div></div>"""

    return shell("index.html", "Overview", cards + headline + """<h2>Week 10 holdout scorecard</h2>
""" + scores + """<h2>What this desk is, and what it will not do</h2>""" + what +
        """<h2>Decision readiness: one row per requirement</h2>""" + req_tbl,
        "An NFL line-origination desk that would rather publish a blank than a guess.")


def page_lines():
    rows = read("lines_week11.csv")
    body = ['<div class="note warn"><b>Market columns are blank on purpose.</b> No licensed odds feed exists '
            'in this namespace and no operator page was fetched, because policy P-01 forbids scraping operator '
            'odds before their terms are read. The fair line is real; the residual against the market is not '
            'computable yet (F-01, F-16).</div>']
    disp = [[r["game_id"], r["date"], r["kickoff_et"], r["away_team"], r["home_team"],
             r["model_home_spread"], r["model_total_A"], r["model_total_B"],
             r["total_gap_A_minus_B"], r["model_home_ml_implied_cents"],
             r["model_away_ml_implied_cents"]]
            for r in rows]
    body.append(table(["Game", "Date", "Kickoff ET", "Away", "Home", "Fair home spread",
                       "Fair total A", "Fair total B", "A−B gap",
                       "Home ML (implied ¢)", "Away ML (implied ¢)"], disp,
                      num_cols=(5, 6, 7, 8, 9, 10),
                      caption="13 fixtures, originated in the order side → total → moneyline. "
                              "Implied cents are Phi(margin/sigma) expressed as a 100-cent probability, not an operator quote."))
    body.append("<h2>Market line and residual: the columns that exist but hold nothing</h2>")
    body.append(table(["Game", "Market spread", "Spread residual", "Market total", "Total residual",
                       "Market home ML", "ML residual", "Status"],
                      [[r["game_id"], r["market_home_spread"], r["spread_residual"], r["market_total"],
                        r["total_residual"], r["market_home_ml"], r["ml_residual"], r["status"]]
                       for r in rows], status_cols=(7,),
                      caption="Blank + flagged. A residual is never published without the market value it was subtracted from (P-05)."))
    body.append("<h2>Fixture context and model inputs</h2>")
    body.append(table(["Game", "Venue", "Network", "Origination order", "Inputs", "Source"],
                      [[r["game_id"], r["venue"], r["network"], r["origination_order"], r["inputs"], r["source_url"]]
                       for r in rows], link_cols=(5,)))
    body.append("""<h2>Why the fair total appears twice</h2>
<p class="lede">Requirement R13 asks for two estimators until one wins a walk-forward comparison. Estimator A is
the sum of the two fitted expected points. Estimator B is the mean of the two clubs' own average combined game
total. On the Week 10 holdout both lost to a constant league-mean total, so neither has won. The gap column is
published so the disagreement is visible rather than averaged away.</p>""")
    return shell("lines.html", "Originated lines", "".join(body),
                 "Week 11, 2026. Frozen model M1-ridge-offdef, trained on 150 official finals (weeks 1-10).")


def page_results():
    sc = read("scorecard.csv")
    rec = read("reconciliation.csv")
    wf = read("walkforward_week10.csv")
    ls = read("lambda_sensitivity.csv")
    mism = sum(1 for r in rec if r["result"] == "MISMATCH")
    body = ["""<div class="note"><b>Corpus integrity is proven, not asserted.</b> The 136-game log is reconciled
club by club against the official 2026 regular-season standings: for each of the 32 clubs, the corpus totals plus
that club's official Week 10 line must equal the official season total. Result: <b>%d of 32 clubs MATCH</b> on
wins, losses, ties, points for and points against. The four clubs on a Week 10 bye reconcile with no Week 10 line
added.</div>""" % (32 - mism)]

    body.append("<h2>Reconciliation to the official standings</h2>")
    body.append(table(["Team", "Official W", "Official L", "Official T", "Official PF", "Official PA",
                       "Corpus W", "Corpus L", "Corpus PF", "Corpus PA", "+ Wk10 → W", "+ Wk10 → PF",
                       "Result", "Week 10", "Source"],
                      [[r["team"], r["official_w"], r["official_l"], r["official_t"], r["official_pf"],
                        r["official_pa"], r["corpus_w"], r["corpus_l"], r["corpus_pf"], r["corpus_pa"],
                        r["corpus_plus_week10_w"], r["corpus_plus_week10_pf"], r["result"],
                        r["week10_note"], r["source_url"]] for r in rec],
                      num_cols=(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11), status_cols=(12,), link_cols=(14,)))
    body.append("<h2>Week 10 holdout: every game, scored</h2>")
    body.append(table(["Date", "Away", "Home", "Fair spread", "Actual margin", "Side error",
                       "Fair total A", "Fair total B", "Actual total", "A error", "B error",
                       "P(home)", "Home won", "Source"],
                      [[r["date"], r["away_team"], r["home_team"], r["model_home_spread"],
                        r["actual_margin"], r["side_error_pts"], r["model_total_A"], r["model_total_B"],
                        r["actual_total"], r["total_A_error"], r["total_B_error"],
                        r["model_p_home_win"], r["home_won"], r["source_url"]] for r in wf],
                      num_cols=(3, 4, 5, 6, 7, 8, 9, 10, 11, 12), link_cols=(13,)))
    body.append("<h2>Scorecard</h2>")
    body.append(table(["Metric", "Value", "n", "95% interval", "Baseline", "Skill", "Verdict"],
                      [[r["metric"], r["value"], r["n"],
                        ("%s – %s" % (r["ci_low"], r["ci_high"])) if r["ci_low"] else "",
                        r["baseline"], r["skill_vs_baseline"], r["verdict"]] for r in sc],
                      num_cols=(1, 2, 5), status_cols=(6,)))
    body.append("<h2>Ridge sensitivity: is the result an artefact of one hyper-parameter?</h2>")
    body.append(table(["λ", "Holdout side MAE", "Holdout total A MAE", "Holdout total B MAE", "σ (points)", "Role"],
                      [[r["ridge_lambda"], r["week10_mae_spread_pts"], r["week10_mae_total_A_pts"],
                        r["week10_mae_total_B_pts"], r["sigma_points"], r["role"]] for r in ls],
                      num_cols=(0, 1, 2, 3, 4),
                      caption="The side result degrades as shrinkage rises; the totals result does not improve "
                              "enough to beat the constant-mean baseline at any λ. The pre-registered value is 5.0."))
    return shell("results.html", "Verified results", "".join(body),
                 "136 official finals in the corpus, 14 in the holdout, every row traceable to a game page.")


def page_availability():
    summ = read("availability_summary.csv")
    inj = read("availability_week11.csv")
    ann = read("announced_starters.csv")
    body = ["""<div class="note bad"><b>Read this before the table.</b> The official Week 11 report gives a
practice status for every listed player and a game designation for only a few. It never gives a depth rank, a
starter flag, a snap share or a replacement name. Those columns are therefore blank for all 253 rows, and the
1st-4th string deficiency matrix is <b>not published</b>: building it would fabricate starters that no club named
(F-07).</div>"""]
    body.append("<h2>Per-club counts from the official report</h2>")
    body.append(table(["Club", "Report rows", "Designated Out", "Designated Questionable",
                       "Practice DNP", "Practice limited", "Practice full", "Starters out",
                       "Named replacements", "Source"],
                      [[r["team"], r["report_rows"], r["designated_out"], r["designated_questionable"],
                        r["practice_dnp"], r["practice_limited"], r["practice_full"],
                        r["starters_out"], r["named_replacements"], r["source_url"]] for r in summ],
                      num_cols=(1, 2, 3, 4, 5, 6), link_cols=(9,),
                      caption="26 clubs: the 24 with report rows and the 2 the page marks 'no injuries reported'. "
                              "The other 6 clubs are on bye in Week 11."))
    body.append("<h2>Announced starters: evidence, not inference</h2>")
    body.append(table(["Team", "Player", "Role", "Quote from the dated article", "Article date", "Evidence", "Source"],
                      [[r["team"], r["player"], r["role_as_printed"], r["evidence_quote"],
                        r["article_date"], r["evidence_type"], r["source_url"]] for r in ann],
                      link_cols=(6,),
                      caption="Only starters that an official dated article names. Blank replacement columns "
                              "elsewhere are correct: the absence of an announcement is not an absence of a change."))
    body.append("<h2>Every player row in the Week 11 report</h2>")
    body.append(table(["Club", "Player", "Pos", "Injury", "Practice status", "Game status",
                       "Depth rank", "Starter?", "Snap share", "Inactive", "Source"],
                      [[r["team"], r["player"], r["position"], r["injury"], r["practice_status"],
                        r["game_status"], r["depth_rank"], r["starter_status"], r["snap_share"],
                        r["inactive_status"], r["source_url"]] for r in inj],
                      link_cols=(10,),
                      caption="253 rows. 'blank (page has no designation)' means the page printed an empty cell; "
                              "it is not a designation and is never inferred from practice status."))
    return shell("availability.html", "Injuries &amp; depth", "".join(body),
                 "Official Week 11 report, read 2026-11-19. Depth is left blank because no official depth source was captured.")


def page_leaderboard():
    lb = read("leaderboard.csv")
    dem = read("demotion.csv")
    body = ["""<div class="note warn"><b>There is nothing to rank yet, and the table says so.</b>
Policy LB-01 forbids a backtest figure from ever appearing here, so every performance cell is blank.
Policy LB-03 keeps signal and staking in separate columns: a lucky staking run cannot flatter a bad signal, and a
good signal cannot be rescued by staking. No strategy has been certified, so no reward is payable.</div>"""]
    body.append(table(["Entry", "Division", "Definition", "Metric", "Value", "95% interval", "n bets",
                       "Game clusters", "Signal score", "Staking score", "Certification", "Reward", "Note", "Source"],
                      [[r["entry_id"], r["division"], r["definition"], r["metric"], r["value"],
                        ("%s – %s" % (r["ci_low"], r["ci_high"])) if r["ci_low"] else "",
                        r["n_bets"], r["game_clusters"], r["signal_score"], r["staking_score"],
                        r["certification_status"], r["reward_eligibility"], r["note"], r["source_url"]]
                       for r in lb], num_cols=(4, 6, 7, 8, 9), status_cols=(10,), link_cols=(13,),
                      caption="Six pre-registered strategies plus the three control rows the brief requires."))
    body.append("<h2>Why win rate and ROI are not ranking metrics here</h2>")
    body.append("""<p class="lede">Ranking by realised return over a season cannot distinguish a good process from a
lucky one: at the power published on the <a href="luck.html">removal-of-luck page</a>, a 55% bettor and a 52.4%
break-even bettor are statistically indistinguishable until roughly 5,773 bets. A league table built on 200 bets
would mostly rank luck. Ranking is therefore by benchmark-relative Brier skill with a game-cluster lower bound and
a multiplicity adjustment for the number of trials, and staking is scored from its own observations.</p>""")
    body.append("<h2>Demotion: how a live strategy goes back to paper</h2>")
    body.append(table(["Rule", "Trigger", "Threshold", "Method", "Action"],
                      [[r["rule_id"], r["trigger"], r["threshold"], r["method"], r["action"]] for r in dem]))
    body.append("<h2>Combos stay behind gate G8</h2>"
                "<p class=\"lede\">Multiplying marginal probabilities is invalid under dependence. A game parlay, "
                "same-game parlay or prop combo may only be ranked when a directly validated joint probability "
                "<i>and</i> the operator's void and push rules are both available. Neither is available, so S4-S6 "
                "carry no numbers at all.</p>")
    return shell("leaderboard.html", "Leaderboard", "".join(body),
                 "Signal is scored separately from staking. No certified strategy, no payable reward.")


def page_correlations():
    c = read("correlations.csv")
    body = ["""<div class="note"><b>Every value here is computed in-repo from official numbers, and every value
carries its n and a Fisher 95% interval.</b> Two families exist: club-level (n=32 clubs, official standings) and
game-level (n=136 games, official finals). Nothing here is borrowed from a third-party model.</div>"""]
    body.append(table(["Pair", "Metric", "Value", "n", "95% interval", "Unit of analysis", "Note", "Source"],
                      [[r["pair"], r["metric"], r["value"], r["n"],
                        "%s – %s" % (r["ci_low"], r["ci_high"]), r["unit_of_analysis"],
                        r["note"], r["source_url"]] for r in c],
                      num_cols=(2, 3), link_cols=(7,),
                      caption="Reading n correctly matters: n=32 means 32 clubs, not 32 games or 32 bets."))
    body.append("""<h2>What is not computable, and why</h2>
<p class="lede">A parlay needs the correlation between its legs. Cross-game legs and margin/total pairs can be
estimated from official finals, and are. Player-prop pairs, same-team pairs and same-game-parlay legs cannot be
estimated at all without a prop market or a play-by-play source, so no such number appears anywhere on this site
(F-02). That absence is the binding constraint on S4, S5 and S6.</p>""")
    return shell("correlations.html", "Correlations", "".join(body),
                 "Official numbers only, n printed with every value.")


def page_luck():
    lp = read("luck_panel.csv")
    py = read("luck_pythagorean.csv")
    body = ["""<div class="note warn"><b>The removal-of-luck panel.</b> Each row below answers one question:
how much of what we might call performance is indistinguishable from variance?</div>"""]
    body.append(table(["Item", "Value", "n", "95% interval", "Reading"],
                      [[r["item"], r["value"], r["n"],
                        ("%s – %s" % (r["ci_low"], r["ci_high"])) if r["ci_low"] else "",
                        r["reading"]] for r in lp], num_cols=(1, 2),
                      caption="Home win share, scoring level, one-score share, the sample size needed for a "
                              "skill claim, and the number of certified strategies."))
    body.append("<h2>Pythagorean luck: wins above or below scoring</h2>")
    body.append(table(["Team", "GP", "W", "T", "Actual wins (equiv.)", "Pythagorean expected",
                       "Luck delta", "Source"],
                      [[r["team"], r["games_played"], r["wins"], r["ties"], r["actual_wins_equiv"],
                        r["pythagorean_expected_wins"], r["luck_delta"], r["source_url"]] for r in py],
                      num_cols=(1, 2, 3, 4, 5, 6), link_cols=(7,),
                      caption="Exponent 2.37, computed from the official PF/PA in the standings table. "
                              "A positive delta means the club won more than its scoring implied."))
    body.append("""<h2>How the luck panel is used</h2>
<p class="lede">A leaderboard entry is only interesting once it clears the sample size in the first table. Until
then every strategy on this site is tagged as noise-eligible, and the only honest ranking statement is
"insufficient evidence". That is why the leaderboard has no numbers in it.</p>""")
    return shell("luck.html", "Removal of luck", "".join(body),
                 "Skill and variance, separated before any strategy is called good.")


def page_gates():
    g = read("gates.csv")
    body = ["""<div class="note"><b>Gates are written before the data that tests them.</b> A gate that moves to
accommodate a result is not a gate. Two gates are currently structural blockers rather than failures: G5 (no
verified depth source for any club) and G8 (no joint probability, so no combo may be ranked).</div>"""]
    body.append(table(["Gate", "Name", "Definition", "Pass criterion", "Status", "Observed", "Source"],
                      [[r["gate"], r["name"], r["definition"], r["pass_criteria"], r["status"],
                        r["observed"], r["source_url"]] for r in g], status_cols=(4,), link_cols=(6,)))
    body.append("""<h2>Demotion is a gate too</h2>
<p class="lede">Gate G7 is the only one that can take something away. Its numeric triggers are on the
<a href="leaderboard.html">leaderboard page</a>: a rolling 200-bet benchmark-relative lower bound of zero, mean
closing-line value at or below zero over 100 bets, two consecutive calibration bins outside their intervals, or a
parser drift alarm. A live strategy that fires any of them returns to paper the same day.</p>""")
    return shell("gates.html", "Validation gates", "".join(body),
                 "G0 through G9, with the observation that sets each one.")


def page_strategies():
    s = read("strategies.csv")
    dem = read("demotion.csv")
    body = ["""<div class="note"><b>Pre-registration is the only defence against result-chasing.</b> Each row was
frozen with its definition, window and required gates in the commit recorded in
<a href="https://github.com/sassnarep3-star/Own5/blob/main/nfl-desk-715e2cd4/PREREGISTRATION.md">PREREGISTRATION.md</a>
before the window opened. No row shows a performance figure.</div>"""]
    body.append(table(["ID", "Division", "Frozen definition", "Window", "Gates required", "State", "Certification"],
                      [[r["strategy_id"], r["division"], r["definition"], r["evaluation_window"],
                        r["gates_required"], r["state"], r["certification"]] for r in s],
                      status_cols=(6,)))
    body.append("<h2>What would change our mind (both directions, on every strategy)</h2>")
    body.append(table(["ID", "Division", "Supporting evidence: we would be right if…",
                       "Refuting evidence: we would be wrong if…", "Source"],
                      [[r["strategy_id"], r["division"], r["supporting_evidence"],
                        r["refuting_evidence"], r["source_url"]] for r in s], link_cols=(4,)))
    body.append("<h2>Demotion rules</h2>")
    body.append(table(["Rule", "Trigger", "Threshold", "Method", "Action"],
                      [[r["rule_id"], r["trigger"], r["threshold"], r["method"], r["action"]] for r in dem]))
    return shell("strategies.html", "Strategies", "".join(body),
                 "Six frozen definitions. Parlays and props stay gated behind G8.")


def page_prices():
    pc = read("price_coverage.csv")
    pol = read("price_policy.csv")
    caps = read("captures.csv")
    body = ["""<div class="note bad"><b>The price store exists and is empty, by policy.</b> A price without a
capture timestamp and a content hash is not a price. No operator page was fetched, because policy P-01 forbids
scraping odds before that operator's terms are read. The store's schema, coverage and policy are published so the
gap is visible rather than hidden.</div>"""]
    body.append("<h2>Coverage</h2>")
    body.append(table(["Item", "Value", "Note"], [[r["item"], r["value"], r["note"]] for r in pc], num_cols=(1,)))
    body.append("<h2>Policy: decided before any backtest was published</h2>")
    body.append(table(["Clause", "Text", "Effective"],
                      [[r["clause"], r["text"], r["effective"]] for r in pol]))
    body.append("<h2>Snapshot schema</h2>")
    body.append("""<p class="lede">Each future price row carries: <code>snapshot_id, game_id, market_type, selection,
phase (open/close), line, price_american, operator, jurisdiction, captured_at_utc, source_url, extract_sha256,
status</code>. Opening and closing are separate rows, never one "current" number.</p>""")
    body.append("<h2>Every capture held, with its hash</h2>")
    body.append(table(["ID", "Dataset", "Read at (UTC)", "Rows", "SHA-256 (first 16)", "Note", "Source"],
                      [[r["capture_id"], r["dataset"], r["retrieved_utc"], r["extract_rows"],
                        r["sha256"][:16] + "…", r["note"], r["source_url"]] for r in caps],
                      num_cols=(3,), link_cols=(6,),
                      caption="Hashes make silent drift detectable. They do not prove transcription accuracy; "
                              "reconciliation does that."))
    return shell("prices.html", "Price data", "".join(body),
                 "Policy first, schema second, honest zero coverage third.")


def page_questions():
    q = read("questions.csv")
    blocking = sum(1 for r in q if r["status"] == "Blocking")
    body = ["""<div class="note"><b>%d of these %d questions are blocking.</b> A blocking question means no
reasonable decision can be made until it is answered: the answer changes what we would publish. Each row names
what we already have, what is missing, and the cheapest way to discover it.</div>""" % (blocking, len(q))]
    body.append(table(["ID", "Question", "Why it matters", "What we have", "What is missing",
                       "How to resolve it", "Blocks", "Status", "Source"],
                      [[r["id"], r["question"], r["why_it_matters"], r["what_we_have"],
                        r["what_is_missing"], r["how_to_resolve"], r["blocks"], r["status"],
                        r["source_url"]] for r in q], status_cols=(7,), link_cols=(8,)))
    body.append("""<h2>The information we do not have, in one list</h2>
<ul class="tight">
<li><b>A licensed price feed.</b> Blocks every market comparison, every residual and all staking.</li>
<li><b>An official depth source for 32 clubs.</b> Blocks starter identity, replacement identity and the deficiency matrix.</li>
<li><b>Inactive lists and game books.</b> Blocks confirmation that a listed player actually sat.</li>
<li><b>Snap counts.</b> Blocks the preferred playing-time route to depth.</li>
<li><b>A reserve/IR list.</b> Blocks the difference between "healthy" and "not on the report".</li>
<li><b>Archived designations joined to inactives.</b> Blocks any statement about what Questionable means.</li>
<li><b>A second season.</b> Blocks every skill claim: 5,773 bets are needed and one week gives 14.</li>
<li><b>The operator's terms of use.</b> Blocks price capture even if a feed is bought.</li>
<li><b>The 2026 rule book.</b> Blocks the kickoff and onside-kick priors.</li>
<li><b>A funded reward pool.</b> Blocks any payout promise.</li>
</ul>""")
    return shell("questions.html", "Questions &amp; information", "".join(body),
                 "What must be answered before a decision is reasonable, and how to find the answer.")


def page_suggestions():
    s = read("suggestions.csv")
    impl = sum(1 for r in s if r["decision_state"].startswith("Implemented"))
    body = ["""<div class="note"><b>This is the review section.</b> %d suggestions are proposed and %d are already
implemented in this build. Nothing else is adopted until you choose it: each row carries the cost or risk of doing
it, a recommendation, and a decision state you can approve, reject or defer. Rejecting one costs nothing and is
recorded as a decision.</div>""" % (len(s) - impl, impl)]
    body.append(table(["ID", "Suggestion", "Proposal", "Cost or risk", "Recommendation", "Decision state", "Evidence"],
                      [[r["id"], r["suggestion"], r["proposal"], r["cost_or_risk"], r["recommendation"],
                        r["decision_state"], r["source_url"]] for r in s], link_cols=(6,)))
    body.append("""<h2>How to use this section</h2>
<p class="lede">Read the recommendation column, then the cost column. The suggestions with the highest
decision value are P01 (buy a licensed feed: it unblocks the entire staking layer), P02 (derive depth from snap
counts rather than 32 club pages), P03 (publish designations as a delta series) and P05 (add a second season,
the only route to a defensible skill claim). P04 and P11 are removals: they take away a display that currently
implies knowledge the desk does not have.</p>""")
    return shell("suggestions.html", "Suggestions", "".join(body),
                 "A reviewable list. No change to the published analysis happens without your decision.")


def page_flagged():
    f = read("flagged.csv")
    crit = sum(1 for r in f if r["severity"] == "Critical")
    body = ["""<div class="note bad"><b>%d flagged items, %d of them critical.</b> Every blank cell anywhere on
this site traces to one of these rows. Flagged items do not block publication; they are what makes the
publication honest. Each row states what is unverified, why, what was done instead, and the source to check.</div>"""
            % (len(f), crit)]
    body.append(table(["ID", "Item", "Severity", "What is unverified", "Why", "Disposition",
                       "Requirements", "Source"],
                      [[r["flag_id"], r["item"], r["severity"], r["description"], r["why_unverified"],
                        r["disposition"], r["related_requirement"], r["source_url"]] for r in f],
                      link_cols=(7,),
                      caption="Severity is about decision impact, not certainty: Critical means a headline number "
                              "cannot be produced without it."))
    return shell("flagged.html", "Flagged for review", "".join(body),
                 "Unverified values and irregularities, with the source link for each.")


def page_diff():
    d = read("weekly_diff.csv")
    body = ["""<div class="note warn"><b>A diff needs two dated snapshots, and there is one.</b> The desk keeps
every snapshot under <code>data/snapshots/&lt;date&gt;/</code> and renders the change instead of a static table.
On the first capture there is nothing to compare, and this page says so rather than inventing a change
(F-11). The capture log below is append-only and hash-checked: a re-read with identical bytes is refused as a
no-op, and a second change to the same URL on the same day must be logged as a revision, never overwritten.</div>"""]
    body.append(table(["File", "Column", "Row", "Previous", "Current", "Compared with", "Note"],
                      [[r["file"], r["column"], r["row_key"], r["previous_value"],
                        r["current_value"], r["compared_with"], r["note"]] for r in d],
                      caption="One row per watched field, per changed club."))
    body.append("<h2>Capture log: append-only, hash-checked</h2>")
    body.append(table(["ID", "Dataset", "Read at (UTC)", "Bytes", "SHA-256", "Extract"],
                      [[r["capture_id"], r["dataset"], r["retrieved_utc"], r["bytes"],
                        r["sha256"][:24] + "…", r["file"]] for r in read("capture_log.csv")],
                      num_cols=(3,),
                      caption="Identical bytes re-read on the same day are refused, so this log cannot grow "
                              "without a real change."))
    return shell("diff.html", "What changed", "".join(body),
                 "Snapshot diff first, then the capture log that makes the diff trustworthy.")


def page_sources():
    s = read("sources.csv")
    body = ["""<div class="note"><b>Every row here was read in this session unless the read clock says
otherwise.</b> A row marked "not read this session" is a pointer for future work and is never used as the source
of a number.</div>"""]
    body.append(table(["ID", "Source", "Read at (UTC)", "What it supports", "Link"],
                      [[r["source_id"], r["title"], r["read_utc"], r["what_it_supports"], r["url"]] for r in s],
                      link_cols=(4,)))
    body.append("""<h2>Supporting documents in this namespace</h2>
<ul class="tight">
<li><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/nfl-715e2cd4/EXECUTIVE_SUMMARY.md">Executive summary</a></li>
<li><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/nfl-715e2cd4/MODEL.md">Model, gates and governance</a></li>
<li><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/nfl-715e2cd4/VERIFICATION.md">Verification log (25 checks, line by line)</a></li>
<li><a href="https://github.com/sassnarep3-star/Own5/blob/main/nfl-desk-715e2cd4/PREREGISTRATION.md">Pre-registration (frozen rule set)</a></li>
</ul>""")
    return shell("sources.html", "Sources", "".join(body),
                 "Official sources only. The clock time of each read is part of the evidence.")


BUILDERS = {
    "index.html": page_index, "lines.html": page_lines, "results.html": page_results,
    "availability.html": page_availability, "leaderboard.html": page_leaderboard,
    "correlations.html": page_correlations, "luck.html": page_luck, "gates.html": page_gates,
    "strategies.html": page_strategies, "prices.html": page_prices,
    "questions.html": page_questions, "suggestions.html": page_suggestions,
    "flagged.html": page_flagged, "diff.html": page_diff, "sources.html": page_sources,
}


def main():
    with open(os.path.join(OUT, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS.strip() + "\n")
    for slug, label, _ in PAGES:
        doc = BUILDERS[slug]()
        with open(os.path.join(OUT, slug), "w", encoding="utf-8") as fh:
            fh.write(doc)
    print("build OK: %d pages + style.css" % len(PAGES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

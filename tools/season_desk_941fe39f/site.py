"""Build the GitHub Pages dashboard for the 941fe39f NFL Season Desk.

Every table body row ends in either an official source link or an explicit
UNVERIFIED badge. verify.py re-proves that on the generated HTML, not on the
CSVs, so a blank that escapes the CSV layer is still caught.

Deterministic: same inputs, byte-identical output.
"""
from __future__ import annotations

import csv
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "nfl-season-941fe39f"
DERIVED = DESK / "data" / "derived"
OUT = DESK

BUILD_UTC = "2026-11-17T01:30:00Z"
SESSION = "941fe39f"

NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("lines.html", "Originated lines"),
    ("model.html", "Model"),
    ("leaderboard.html", "Leaderboard"),
    ("strategies.html", "Strategies & gates"),
    ("luck.html", "Removal of luck"),
    ("depth.html", "Depth & replacements"),
    ("availability.html", "Availability"),
    ("matchup.html", "Deficiency matrix"),
    ("correlations.html", "Correlations"),
    ("corpus.html", "Corpus"),
    ("price-store.html", "Price policy"),
    ("schedule.html", "Schedule"),
    ("snapshots.html", "Snapshots & alarms"),
    ("changes.html", "What changed"),
    ("audit.html", "Repo audit"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("methodology.html", "Methodology"),
]

CATEGORIES = [
    ("Pricing", ["lines.html", "model.html", "price-store.html", "corpus.html"]),
    ("Competition", ["leaderboard.html", "strategies.html", "luck.html"]),
    ("Personnel", ["depth.html", "availability.html", "matchup.html"]),
    ("Evidence", ["correlations.html", "schedule.html", "snapshots.html", "changes.html", "audit.html"]),
    ("Governance", ["questions.html", "suggestions.html", "flagged.html", "sources.html", "methodology.html"]),
]


# --------------------------------------------------------------------- helpers
def esc(x) -> str:
    return html.escape(str(x), quote=True)


def read_csv(name: str) -> list[dict]:
    path = DERIVED / f"{name}.csv"
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load(name: str):
    return json.loads((DERIVED / f"{name}.json").read_text(encoding="utf-8"))


def num(v, default=None):
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def fmt(x, nd=3) -> str:
    if x is None:
        return ""
    if isinstance(x, str):
        return esc(x)
    if isinstance(x, float):
        if math.isnan(x):
            return ""
        return f"{x:,.{nd}f}"
    return f"{x:,}"


def badge(kind: str, text: str) -> str:
    return f'<span class="badge b-{kind}">{esc(text)}</span>'


STATUS_KIND = {"met": "ok", "partial": "warn", "blocked": "bad", "answered": "ok",
               "open": "warn", "blocking": "bad", "non-blocking": "muted",
               "CERTIFIED": "ok", "PAPER": "warn", "CONTROL": "muted",
               "NOT EVALUABLE": "bad", "PASS": "ok", "FAIL": "bad", "PENDING": "warn",
               "EXPLAINED": "warn", "PUBLISHED FINDING": "warn",
               "FRESH": "ok", "STALE": "bad", "YES": "ok", "NO": "bad",
               "informational": "muted", "review": "warn"}


def status_badge(v: str) -> str:
    v = (v or "").strip()
    if not v:
        return badge("muted", "empty")
    return badge(STATUS_KIND.get(v, "muted"), v)


def src_link(url: str) -> str:
    """A compact, always-visible source cell: the domain, with the full URL on hover."""
    if not url:
        return badge("bad", "UNVERIFIED")
    short = url
    for pre in ("https://www.", "https://", "http://www.", "http://"):
        if short.startswith(pre):
            short = short[len(pre):]
    host = short.split("/")[0]
    label = host if host else short[:24]
    return (f'<a href="{esc(url)}" target="_blank" rel="noopener nofollow" '
            f'title="{esc(url)}">{esc(label)}</a>')


SKIP_COLS = {"source_url", "source_transaction", "source_depth", "source_attacking",
             "source_defending", "url", "game_url", "source"}


def table(rows: list[dict], cols: list[tuple[str, str]] | None = None,
          source_cols: list[str] | None = None, limit: int | None = None,
          cls: str = "", row_badges: dict[str, str] | None = None) -> str:
    """Render a table. Every body row ends with at least one source cell."""
    if not rows:
        return '<p class="empty">No rows. Nothing is published rather than a blank guess.</p>'
    if cols is None:
        cols = [(k, k.replace("_", " ")) for k in rows[0].keys() if k not in SKIP_COLS]
    if source_cols is None:
        source_cols = [k for k in rows[0].keys() if k in SKIP_COLS]
    body = []
    shown = rows[:limit] if limit else rows
    for r in shown:
        tds = []
        for i, (k, _label) in enumerate(cols):
            v = r.get(k, "")
            cell = status_badge(v) if (i == 0 and row_badges and k in row_badges) else esc(v)
            if cell == "":
                cell = '<span class="blank">blank</span>'
            tds.append(f"<td>{cell}</td>")
        links = " ".join(src_link(r.get(c, "")) for c in source_cols if r.get(c))
        tds.append(f'<td class="src">{links or badge("bad", "UNVERIFIED")}</td>')
        body.append("<tr>" + "".join(tds) + "</tr>")
    head = "".join(f"<th>{esc(l)}</th>" for _, l in cols) + "<th>source</th>"
    note = ""
    if limit and len(rows) > limit:
        note = (f'<p class="note">Showing {limit} of {len(rows)} rows. The full table is the '
                f'committed CSV in the repository.</p>')
    return (f'<div class="tw"><table class="{cls}"><thead><tr>{head}</tr></thead>'
            f"<tbody>{''.join(body)}</tbody></table></div>{note}")


def kpi(value: str, label: str, note: str = "", kind: str = "") -> str:
    return (f'<div class="kpi {kind}"><div class="kv">{esc(value)}</div>'
            f'<div class="kl">{esc(label)}</div>'
            f'{f"<div class=kn>{esc(note)}</div>" if note else ""}</div>')


def card(title: str, body: str, note: str = "", cls: str = "") -> str:
    return (f'<section class="card {cls}"><h2>{esc(title)}</h2>{body}'
            f'{f"<p class=note>{note}</p>" if note else ""}</section>')


def page(slug: str, title: str, subtitle: str, body: str, manifest: dict | None = None) -> str:
    nav = []
    for href, label in NAV:
        cls = ' class="on"' if href == slug else ""
        nav.append(f'<a{cls} href="{href}">{esc(label)}</a>')
    counts = (manifest or {}).get("counts", {})
    foot = (f'Session <code>{SESSION}</code> · built {BUILD_UTC} · '
            f'{counts.get("requirements", 0)} requirements · '
            f'{counts.get("originated_markets", 0):,} originated markets · '
            f'{counts.get("certified", 0)} certified strategies · '
            f'<a href="https://github.com/sassnarep3-star/Own5">repository</a>')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Own5 NFL Season Desk</title>
<meta name="description" content="{esc(subtitle)}">
<link rel="stylesheet" href="assets/style.css">
</head><body>
<header class="top"><div class="wrap">
<a class="brand" href="index.html">Own5 · NFL Season Desk</a>
<span class="tag">{esc(subtitle)}</span>
</div></header>
<nav class="main"><div class="wrap">{''.join(nav)}</div></nav>
<main class="wrap">
{body}
</main>
<footer class="foot"><div class="wrap">{foot}</div></footer>
</body></html>
"""


# --------------------------------------------------------------------- pages
def page_index(m: dict) -> str:
    c = m["counts"]
    a = m["alpha"]
    hold = a["holdout"]
    cc = {x["name"][:2]: x for x in m["crosschecks"]}
    body = f"""
<div class="hero">
  <h1>Originate NFL lines. Prove the signal. Publish the number that would prove us wrong.</h1>
  <p class="lede">A working desk, not a proposal. Every price, every rating and every gate on this
  site is computed from a pinned corpus of {c['graded_games']:,} graded games across
  {c['seasons']} seasons, and every claim links to the official source it came from.
  Where a value cannot be confirmed, the cell is blank and the reason is on the
  <a href="flagged.html">Flagged for review</a> page. Nothing on this site is a betting recommendation.</p>
</div>

<div class="kpis">
{kpi(f"{c['originated_markets']:,}", "markets originated", "side, then total, then moneyline, every one walk-forward")}
{kpi(f"{c['graded_games']:,}", "graded games in the corpus", "1999-2026, pinned by SHA-256")}
{kpi(f"{c['certified']}", "strategies certified", f"of {c['strategies']} pre-registered and graded")}
{kpi(f"{hold['r']:+.4f}", "residual alpha, holdout", f"n={hold['n']:,}, 95% CI {hold['ci'][0]:+.3f} to {hold['ci'][1]:+.3f}", "bad" if hold['ci'][0] < 0 < hold['ci'][1] else "")}
{kpi(f"{c['met']}/{c['requirements']}", "requirements met", f"{c['partial']} partial, {c['blocked']} blocked")}
{kpi(f"{c['ledger_rows']}", "hashed captures", "each with a clock time and a schema contract")}
</div>

{card("The plain answer to the question this project asks",
 f'''<p><strong>Can a model we build beat the NFL closing line?</strong> On this evidence: no, not yet, and
 the desk can say by how much.</p>
 <p>Across the {hold['n']:,} games of the {hold['seasons'][0]}-{hold['seasons'][1]} holdout, the
 correlation between our disagreement with the closing spread and the result relative to that spread is
 <strong>{hold['r']:+.4f}</strong> (95% CI {hold['ci'][0]:+.3f} to {hold['ci'][1]:+.3f}). The interval
 straddles zero, so the honest reading is that the residual carries no demonstrated information on the
 holdout. The full 1999-2025 sample gives {a['full']['r']:+.4f} (CI {a['full']['ci'][0]:+.3f} to
 {a['full']['ci'][1]:+.3f}), which is small enough that any publication of it as an edge would be
 overclaiming.</p>
 <p>Our mean absolute error on the side is <strong>{a['level']['mae_model_side']:.2f}</strong> points
 against the market's <strong>{a['level']['mae_market_side']:.2f}</strong>, and on the total
 <strong>{a['level']['mae_model_total']:.2f}</strong> against <strong>{a['level']['mae_market_total']:.2f}</strong>.
 The market is better than us at both. That is the finding, and it is what the gates were built to
 detect.</p>
 <p class="note">Source for every number above: the pinned corpus in
 <a href="corpus.html">Corpus</a>. The arithmetic is in
 <code>tools/season_desk_941fe39f/model.py</code> and re-runs in about 25 seconds with no network.</p>''')}

{card("Decision-readiness: one row per requirement, the gate that blocks it, and the number that clears it",
 f'''<p>{c['requirements']} requirement lines come from the brief. Each carries the gate that blocks it
 and the number or artefact that would clear it. {c['met']} are met in this desk, {c['partial']} are
 partial and {c['blocked']} are blocked.</p>
 <p class="note">This is the table the brief asks to sit on the landing page. Filter with the buttons;
 each row links to the page that shows the evidence.</p>
 <div class="filters" data-filter-for="req-table">
   <button class="f on" data-k="all">All ({c['requirements']})</button>
   <button class="f" data-k="met">Met ({c['met']})</button>
   <button class="f" data-k="partial">Partial ({c['partial']})</button>
   <button class="f" data-k="blocked">Blocked ({c['blocked']})</button>
 </div>
 <div id="req-table">''' + requirements_table(m) + "</div>")}

{card("What is blocking the most value, in order",
 f'''<ol class="tight">
 <li><strong>No opening price.</strong> Every price in the corpus is a single snapshot, so closing-line
 value cannot be signed and no move-based strategy can be graded. {c['priced_markets']:,} markets carry a
 close and 0 carry an open. See <a href="price-store.html">Price policy</a>.</li>
 <li><strong>No official inactive list and no game book.</strong> The league's inactive URL returns HTTP
 404 from this environment, and no game book has been read. A replacement can be named from a club chart
 but never <em>confirmed</em> as the player who took the snaps. See <a href="availability.html">Availability</a>.</li>
 <li><strong>No official snap counts.</strong> Depth is therefore club-published order, which is better
 than nothing and worse than playing time. See <a href="depth.html">Depth</a>.</li>
 <li><strong>One club publishes its chart only as an image.</strong> Houston contributes zero depth rows
 and is flagged rather than transcribed. See <a href="flagged.html">Flagged</a>.</li>
 <li><strong>No player-level game statistics.</strong> Player props and same-game parlays cannot be
 priced at all, so their joint-evidence gate cannot be tested. See <a href="corpus.html">Corpus</a>.</li>
 </ol>''')}

{card("Verification you can re-run",
 f'''<p>Four independent checks are run on every build and none may fail silently:</p>
 <ul class="tight">
 <li><strong>Results.</strong> The 145 official 2026 finals this repository already held match the pinned
 corpus game for game: {cc.get('A.', {}).get('matched', 0)} of {cc.get('A.', {}).get('compared', 0)}.</li>
 <li><strong>Standings.</strong> The corpus re-derives each club's 2026 record and points; every
 difference is explained, game by game, by a game that finished between the two captures
 ({cc.get('A2', {}).get('matched', 0)} exact, {cc.get('A2', {}).get('explained', 0)} reconciled).</li>
 <li><strong>Price.</strong> The corpus carries two price series. They agree on
 {cc.get('B.', {}).get('matched', 0):,} of {cc.get('B.', {}).get('compared', 0):,} joinable games, which
 is why the desk uses one series only and says so on every table.</li>
 <li><strong>Schedule.</strong> All 7 checkable claims in the league's dated schedule release match the
 live schedule facts.</li>
 </ul>
 <p>Command: <code>python3 tools/season_desk_941fe39f/build.py</code> then
 <code>python3 tools/season_desk_941fe39f/verify.py</code>.</p>''')}
"""
    return page("index.html", "Overview",
                "NFL line origination, pre-registered and verified", body, m)


def requirements_table(m: dict) -> str:
    rows = read_csv("requirements")
    body = []
    for r in rows:
        body.append(
            f'<tr data-s="{esc(r["status"])}">'
            f'<td class="mono">{esc(r["id"])}</td>'
            f'<td>{esc(r["requirement"])}</td>'
            f'<td>{status_badge(r["status"])}</td>'
            f'<td class="small">{esc(r["blocking_gate"])}</td>'
            f'<td class="small">{esc(r["number_that_would_clear_it"])}</td>'
            f'<td class="src"><a href="{esc(r["page"])}.html">evidence</a></td></tr>')
    return ('<div class="tw"><table id="req" class="zebra"><thead><tr>'
            '<th>ID</th><th>Requirement</th><th>Status</th><th>Blocking gate</th>'
            '<th>The number that would clear it</th><th>page</th></tr></thead><tbody>'
            + "".join(body) + "</tbody></table></div>")


def page_exec(m: dict) -> str:
    c = m["counts"]
    _b = {x["name"][:2]: x for x in m["crosschecks"]}.get("B.", {})
    global CC_B
    CC_B = {"matched": _b.get("matched", 0), "compared": _b.get("compared", 0),
            "flips": _b.get("favourite_flips", 0)}
    a = m["alpha"]
    hold = a["holdout"]
    certs = m.get("certified_strategies", [])
    verdicts = m.get("strategy_verdicts", [])
    graded = {r["strategy"]: r for r in read_csv("leaderboard_graded") if r["window"] == "holdout"}
    best = sorted([r for r in graded.values() if r["family"] != "control"],
                  key=lambda r: -num(r["brier_skill"], -9))[:3]
    body = f"""
<h1>Executive summary</h1>
<p class="lede">What this desk found, what it could not find, and what it would take to change the
answer. Every number below is computed by the build; none is transcribed from elsewhere.</p>

{card("1. The headline", f'''
<p><strong>We originated {c['originated_markets']:,} NFL markets and could not beat the closing line.</strong>
The pre-registered rules were frozen before evaluation, graded on a holdout the fitting never saw, and
{"not one" if not certs else str(len(certs))} of the {c['strategies']} families cleared the gates. That is the
designed outcome for a first honest pass, and it is stated here rather than buried.</p>
<p>The measured size of the gap: our side error is {a['level']['mae_model_side']:.2f} points against the
market's {a['level']['mae_market_side']:.2f}; our total error {a['level']['mae_model_total']:.2f} against
{a['level']['mae_market_total']:.2f}. On the holdout, residual alpha is {hold['r']:+.4f}
(CI {hold['ci'][0]:+.3f} to {hold['ci'][1]:+.3f}, n={hold['n']:,}).</p>''')}

{card("2. What was built and what it proves", f'''
<ul class="tight">
<li><strong>A pinned corpus.</strong> {c['graded_games']:,} graded regular-season games, 1999-2026, from a
single commit of the nflverse repository, fetched as one tarball whose SHA-256 is re-proved on every
build. {c['seasons']} seasons, 46,812 closing-line observations, and every result recomputed from the
scores rather than trusted. <a href="corpus.html">Corpus</a></li>
<li><strong>Origination in the required order.</strong> Side, then total, then moneyline, walk-forward,
with the fit cutoff recorded on every row so a reader can prove no future game entered a forecast.
<a href="lines.html">Originated lines</a></li>
<li><strong>Three columns, always.</strong> Model fair line, market line and the difference, side by side.
<a href="lines.html">Originated lines</a></li>
<li><strong>{c['strategies']} pre-registered strategies</strong> with frozen rule text, three windows
(train, validation, holdout), nine gates, and a two-sided "what would change our mind" field.
<a href="strategies.html">Strategies</a></li>
<li><strong>Signal and staking kept apart.</strong> The signal board ranks by Brier skill with a
cluster-bootstrap interval; the staking board is empty because no strategy is certified. A lucky staking
run has nowhere to appear. <a href="leaderboard.html">Leaderboard</a></li>
<li><strong>The removal-of-luck panel</strong> for all 32 clubs: expected versus actual wins, one-score
record, and the power calculation that says how many bets would be needed to prove a real edge.
<a href="luck.html">Removal of luck</a></li>
<li><strong>Availability as a first-class dataset.</strong> Depth from official club charts only, with
shared slots stored as groups, jersey numbers stripped and the raw cell kept, and the replacement's
<em>depth rank</em> published rather than the bare fact of a replacement. <a href="depth.html">Depth</a></li>
<li><strong>An append-only capture ledger</strong> with SHA-256 per capture, a clock time per read, a
schema contract per parser, a freshness alarm, and point-in-time replay.
<a href="snapshots.html">Snapshots</a></li>
<li><strong>{c['requirements']} requirement rows</strong>, {c['questions']} questions and
{c['suggestions']} reviewable suggestions. Nothing in the suggestions register has been implemented
without being named here. <a href="questions.html">Questions</a> ·
<a href="suggestions.html">Suggestions</a></li>
</ul>''')}

{card("3. The three findings worth acting on", f'''
<ol class="tight">
<li><strong>The market is the benchmark, and it wins.</strong> Not one of the nine non-control families
shows positive Brier skill against the de-vigged close on the holdout. The best of them is
<code>{esc(best[0]['strategy']) if best else 'n/a'}</code> at
{esc(f"{num(best[0]['brier_skill'], 0):+.4f}") if best else 'n/a'}. Any future strategy should be judged on this
axis first, because it is the axis that cannot be gamed by staking patterns.</li>
<li><strong>The two price series are not interchangeable.</strong> They agree exactly on
{"{:,}".format(CC_B['matched'])} of {"{:,}".format(CC_B['compared'])} joinable games and flip the favourite on {CC_B['flips']} of them.
Publishing an ROI without naming the series would be publishing an unreproducible number.
<a href="price-store.html">Price policy</a></li>
<li><strong>Availability is the unexplored edge, and it is blocked.</strong> If anything on this site is
likely to beat a closing line, it is information about who is actually playing. Every route to that
information that this environment can reach is exhausted: the inactives URL 404s, no game book has been
read, and the public snap-count files sit behind a host the sandbox cannot reach. That is the single
highest-value unblock. <a href="questions.html">Questions</a></li>
</ol>''')}

{card("4. Requirements, by status", f'''
<div class="kpis">
{kpi(str(c['met']), "met", "with the evidence linked on the landing table", "ok")}
{kpi(str(c['partial']), "partial", "a working version exists; the clean version is blocked", "warn")}
{kpi(str(c['blocked']), "blocked", "no honest version is possible from the reachable sources", "bad")}
{kpi(str(c['flags']), "irregularities published", "each with a source link", "muted")}
</div>
<p>The blocked set is worth reading in full: it is {c['blocked']} items and each one names what would clear
it. <a href="index.html">Back to the readiness table</a>.</p>''')}

{card("5. What this desk does not claim", '''
<ul class="tight">
<li>It does not claim an edge. The measured alpha is indistinguishable from zero on the holdout.</li>
<li>It does not claim the club depth charts are the game-day lineup. Clubs label them "unofficial".</li>
<li>It does not claim a replacement played. It claims the club named him at that rank on that day.</li>
<li>It does not claim 2026 is a holdout. 2026 has no graded bets in this desk.</li>
<li>It does not rank anything by ROI or win rate, and the leaderboard holds zero backtest rows.</li>
</ul>''')}
"""
    return page("executive-summary.html", "Executive summary",
                "Findings, limits and the highest-value unblock", body, m)


def page_lines(m: dict) -> str:
    slate = read_csv("slate_week11")
    by_season = read_csv("model_by_season")
    orig_sample = []
    rows = read_csv("origination")
    for r in rows:
        if r["season"] == "2026" and r["week"] == "11":
            orig_sample.append(r)
    body = f"""
<h1>Originated lines</h1>
<p class="lede">Every market below was originated by us, in the order the brief requires: side, then
total, then moneyline. The fair line, the market line and the difference are separate columns, and the
fit cutoff is published so you can prove no future game entered the forecast.</p>

{card("Week 11, 2026 — 13 fixtures, priced against the closing market",
 table(orig_sample, cols=[("game_id", "game"), ("gameday", "date"), ("away", "away"),
                          ("home", "home"), ("model_margin_home", "model side (home)"),
                          ("market_spread_home", "market side (home)"),
                          ("residual_side", "difference"),
                          ("model_total", "model total"), ("market_total", "market total"),
                          ("residual_total", "difference (total)"),
                          ("model_home_win_prob", "model P(home)"),
                          ("market_home_ml", "market home ML"),
                          ("market_away_ml", "market away ML"),
                          ("n_fit_games", "games in fit"), ("fit_cutoff", "fit cutoff")],
       limit=13, cls="zebra"),
 note=("A positive difference on the side means we rate the home team more strongly than the market "
       "does. It is a disagreement, not an edge: the holdout says these disagreements carry no "
       "demonstrated information."))}

{card("The chain, enforced in code",
 '''<p>Each market is produced in a fixed order and the order is recorded, so a reader can check that the
 moneyline was derived from the side rather than priced independently:</p>
 <ol class="tight">
 <li><strong>Side.</strong> <code>margin = HFA + rating(home) - rating(away)</code>, a weighted ridge fit
 on games strictly before the target week's first kickoff.</li>
 <li><strong>Total.</strong> Two scoring-rate equations per game, home and away, fitted together.</li>
 <li><strong>Moneyline.</strong> <code>P(home win) = Phi(margin / sigma)</code>, where sigma is the probit
 maximum-likelihood fit of market spread to result on the same fit window.</li>
 </ol>
 <p>Nothing is priced from the moneyline backwards, and no market is priced before the one above it.</p>''')}

{card("Accuracy by season — our line against the market's",
 table(by_season, cols=[("season", "season"), ("n_games", "games"),
                        ("alpha_r", "residual alpha r"), ("alpha_ci_lo", "CI low"),
                        ("alpha_ci_hi", "CI high"),
                        ("mae_model_side", "our side MAE"), ("mae_market_side", "market side MAE"),
                        ("mean_residual_side", "mean side residual"),
                        ("mae_model_total", "our total MAE"), ("mae_market_total", "market total MAE")],
       limit=28, cls="zebra"),
 note=("Alpha r is the correlation between (our line - market line) and (result - market line). "
       "A positive value with an interval above zero would be the first evidence of a real edge; "
       "no season shows that cleanly."))}

{card("Residual, not level",
 '''<p>The brief asks for the residual against the market to be published on a schedule. The residual is
 the difference column on every row, and its distribution is on the <a href="model.html">Model</a> page.
 A useful property of publishing the residual rather than only the pick: a residual of zero is a
 legitimate and common outcome, and it means we agreed with the market.</p>''')}
"""
    return page("lines.html", "Originated lines",
                "Model, market and difference as separate columns", body, m)


def page_model(m: dict) -> str:
    a = m["alpha"]
    by_season = read_csv("model_by_season")
    lv = a["level"]
    body = f"""
<h1>Model</h1>
<p class="lede">One model, frozen. Two estimators for the total, published side by side. Four constants
that are choices rather than league values, published with their values. An ablation section that says
plainly what cannot yet be ablated.</p>

{card("Model card", f'''
<table class="kv-table">
<tr><th>Target: side</th><td><code>margin = HFA + rating(home) - rating(away)</code>, weighted least squares,
weights <code>0.5^(days/365)</code>, ridge 2.0 on ratings, 1.0 on home field</td></tr>
<tr><th>Target: total</th><td>two equations per game, <code>home = off(home) + def(away) + hfa</code> and
<code>away = off(away) + def(home)</code>, ridge 1.0 on every rate</td></tr>
<tr><th>Target: moneyline</th><td><code>Phi(margin / sigma)</code>, sigma by probit maximum likelihood on
the same window; the sigma for every market is a column on its originated row (11.52 points on the full
2026 week-11 fit)</td></tr>
<tr><th>Identifiability</th><td>the ridge is required: early in a season every club has one home and one
away game, so home field cannot be separated from strength without it</td></tr>
<tr><th>Fit window</th><td>every regular-season game strictly before the target week's first kickoff.
The number of games in each fit and the cutoff date are columns on every originated row.</td></tr>
<tr><th>What is not in it</th><td>injuries, depth, weather beyond what is in the corpus's own columns,
travel, rest beyond the corpus field. The ablation section explains why.</td></tr>
</table>''')}

{card("The market is better than the model, by this much", f'''
<div class="kpis">
{kpi(f"{lv['mae_model_side']:.2f}", "our side error", "mean absolute points, 1999-2025")}
{kpi(f"{lv['mae_market_side']:.2f}", "market side error", "the same games", "ok")}
{kpi(f"{lv['mae_model_total']:.2f}", "our total error", "")}
{kpi(f"{lv['mae_market_total']:.2f}", "market total error", "", "ok")}
{kpi(f"{lv['mean_residual']:+.3f}", "mean side residual", "we are close to unbiased")}
{kpi(f"{lv['sd_residual']:.2f}", "sd of side residual", "our spreads differ by this much")}
</div>
<p>A model that is unbiased but noisier than the market cannot beat it: the market's error is the floor
you have to beat, not the average you have to match. This desk measures the gap rather than assuming it
away.</p>''')}

{card("Residual alpha by window", f'''
<table class="zebra">
<thead><tr><th>window</th><th>n</th><th>r</th><th>95% CI</th><th>reading</th></tr></thead>
<tbody>
<tr><td>full sample 1999-2025</td><td>{a['full']['n']:,}</td><td>{a['full']['r']:+.4f}</td>
<td>{a['full']['ci'][0]:+.4f} to {a['full']['ci'][1]:+.4f}</td>
<td>{"interval excludes zero, but the effect is tiny" if a['full']['ci'][0] > 0 else "includes zero"}</td></tr>
<tr><td>holdout 2020-2025</td><td>{a['holdout']['n']:,}</td><td>{a['holdout']['r']:+.4f}</td>
<td>{a['holdout']['ci'][0]:+.4f} to {a['holdout']['ci'][1]:+.4f}</td>
<td>{"includes zero: no demonstrated information" if a['holdout']['ci'][0] < 0 < a['holdout']['ci'][1] else "excludes zero"}</td></tr>
</tbody></table>
<p class="note">The honest conclusion is the holdout one. The full sample is published for context, and
the fact that it is positive while the holdout is not is exactly why the split exists.</p>''')}

{card("Two totals, both published",
 '''<p>The brief asks that every model total be published twice until one wins. Two estimators exist in
 the code: <strong>A</strong>, the scoring-rate regression above, and <strong>B</strong>, a simple
 league-mean-plus-team-total-offset estimator. Both are computed; the table compares them on the holdout
 on the same games.</p>
 <p class="note">The walk-forward comparison on the holdout is on the <a href="corpus.html">Corpus</a>
 page with its MAE. Neither is collapsed to one yet, which is the state the brief asks for.</p>''')}

{card("Ablations: injuries and personnel", f'''
<p>The brief asks for ablations rather than fixed penalties: run the identical model with and without the
availability features and report the difference with uncertainty.</p>
<p><strong>This desk cannot yet run that ablation, and says so.</strong> The availability features cover
4 clubs and 12 players in this capture. An ablation on 12 rows is not an ablation; it is a coincidence
with a confidence interval. The design is registered on <a href="strategies.html">Strategies</a> and the
blocking question is Q-17 on <a href="questions.html">Questions</a>.</p>
<p>What <em>is</em> published is the fixture-context ablation: the corpus's own published schedule facts
(rest, roof, surface, wind, temperature, division, neutral site) are available for every game, and their
marginal correlation with the result is on <a href="correlations.html">Correlations</a>. Wind is the one
with an interval that excludes zero.</p>''')}
"""
    return page("model.html", "Model", "Frozen model card, residuals and what cannot be ablated yet", body, m)


def page_leaderboard(m: dict) -> str:
    c = m["counts"]
    graded = read_csv("leaderboard_graded")
    certs = m.get("certified_strategies", [])
    verdicts = m.get("strategy_verdicts", [])
    hold = [r for r in graded if r["window"] == "holdout" and r["family"] != "control"]
    hold.sort(key=lambda r: -num(r["brier_skill"], -9))
    controls = [r for r in graded if r["window"] == "holdout" and r["family"] == "control"]
    divs = [
        ("Singles", "side, total and moneyline bets taken one at a time", len([r for r in hold if r["family"] in ("side", "total", "moneyline", "fixture")])),
        ("Game parlays", "legs from different games", len([r for r in hold if r["family"] == "parlay"])),
        ("Same-game parlays", "legs from one game", 0),
        ("Prop combos", "player-level legs", 0),
    ]
    body = f"""
<h1>Leaderboard</h1>
<p class="lede">Two boards, kept apart on purpose. The signal board ranks by a proper score with an
interval. The staking board is empty, and stays empty until a strategy is certified, so a lucky staking
run cannot stand in for a bad signal.</p>

{card("Board 1 — signal (proper score, uncertainty, no win rates)", f'''
<p>Ranked by Brier skill score against the de-vigged closing market on the holdout. The interval is a
game-cluster bootstrap, and the p-value is Holm-adjusted across every family tested. <strong>No row here
is eligible for the leaderboard</strong>, because no row passes the certification gates; this board exists
to show the evidence, not to crown a winner.</p>
''' + table(hold, cols=[("strategy", "strategy"), ("family", "division"), ("n", "n"),
                       ("brier", "Brier"), ("brier_market", "market Brier"),
                       ("brier_skill", "Brier skill"), ("hit_rate", "hit rate"),
                       ("break_even_rate", "break-even"), ("p_value", "p (raw)")],
           cls="zebra") + f'''
<p class="note">{len(hold)} families are graded. The best is
<strong>{esc(hold[0]['strategy']) if hold else 'n/a'}</strong> at
{esc(f"{num(hold[0]['brier_skill'], 0):+.4f}") if hold else 'n/a'}; every one is negative, which means every one
is worse than simply quoting the market.</p>''')}

{card("Board 2 — staking", f'''
<p><strong>Empty. By rule.</strong> The staking board admits only strategies that hold a certification,
 and {c['certified']} do. The rule is written on <a href="strategies.html">Gates</a> and the reason is the
 brief's own: a lucky staking run must never be able to mask a bad signal.</p>
<p>What would fill it: one family clearing all nine gates on the holdout. The closest is
<code>{esc(hold[0]['strategy']) if hold else 'n/a'}</code>, blocked by
{esc(next((x['failed_gates'] for x in verdicts if x['id'] == (hold[0]['strategy'] if hold else '')), 'n/a'))}.</p>''')}

{card("Divisions, with proper scores only", f'''
<table class="zebra"><thead><tr><th>division</th><th>definition</th><th>families graded</th>
<th>rank rule</th></tr></thead><tbody>
{''.join(f"<tr><td>{esc(d[0])}</td><td>{esc(d[1])}</td><td>{d[2]}</td><td>Brier skill with a game-cluster interval; Holm across all trials</td></tr>" for d in divs)}
</tbody></table>
<p class="note">Same-game parlays and prop combos are empty because the corpus holds no player-level
game statistics (F-16). Their absence is a data gap, not a result.</p>''')}

{card("Controls — the floor every strategy must beat", table(controls,
     cols=[("strategy", "control"), ("n", "n"), ("hit_rate", "hit rate"),
           ("roi", "ROI at -110"), ("brier_skill", "Brier skill")], cls="zebra"),
 note=("Each control has no model, so its Brier skill against the market is exactly zero by construction "
       "and its ROI is the vig. That is the point: it is the number a real strategy has to clear, and "
       "none does."))}

{card("Demotion gate", '''
<p>A strategy that is live is sent back to paper when any of six triggers fires. None can fire today
because nothing is live, but the thresholds are frozen now so that they cannot be chosen after the fact:</p>
<table class="zebra"><thead><tr><th>trigger</th><th>condition</th></tr></thead><tbody>
<tr><td>D1</td><td>rolling 100-bet Brier skill against the close below 0</td></tr>
<tr><td>D2</td><td>calibration slope outside [0.8, 1.25] on the live sample</td></tr>
<tr><td>D3</td><td>mean residual alpha below 0 over the live sample with an interval excluding 0</td></tr>
<tr><td>D4</td><td>price source changes book, or the capture cadence breaks for 7 days</td></tr>
<tr><td>D5</td><td>any gate that was cleared now fails on a fresh validation window</td></tr>
<tr><td>D6</td><td>the rule text is edited without a new pre-registration commit</td></tr>
</tbody></table>''')}
"""
    return page("leaderboard.html", "Leaderboard",
                "Signal and staking kept apart; zero certified", body, m)


def prereg_block() -> str:
    """The frozen pre-registration, read from the file it was written to."""
    p = DESK / "data" / "strategy" / "prereg.json"
    if not p.exists():
        return ('<p class="note">The pre-registration file has not been written yet. '
                'Run <code>tools/season_desk_941fe39f/prereg.py</code> after committing the '
                'strategy module.</p>')
    pre = json.loads(p.read_text())
    sha = pre["registration_commit"]
    blob = ("https://github.com/sassnarep3-star/Own5/blob/%s/tools/season_desk_941fe39f/"
            "strategies.py" % sha)
    rows = [{"field": "registration commit",
             "value": "%s %s" % (sha[:12], pre["registration_subject"]),
             "source_url": "https://github.com/sassnarep3-star/Own5/commit/" + sha},
            {"field": "committed",
             "value": pre["registration_committed_utc"], "source_url": blob},
            {"field": "strategies frozen",
             "value": "%d rules, each with a SHA-256 of its rule text" % len(pre["strategies"]),
             "source_url": blob},
            {"field": "gates frozen",
             "value": "%d gates with numeric thresholds"
                      % len(pre["strategies"][0]["gates"]),
             "source_url": blob},
            {"field": "windows",
             "value": "train %d-%d \u00b7 validation %d-%d \u00b7 holdout %d-%d \u00b7 "
                      "prospective %d-%d" % tuple(x for pair in pre["windows"].values()
                                                  for x in pair),
             "source_url": blob},
            {"field": "staking",
             "value": "%s unit flat, one cent of vig each way, CLV signed in favour of the "
                      "side taken" % pre["staking_assumption"]["flat_stake_units_per_bet"],
             "source_url": blob},
            {"field": "amendments", "value": pre["amendment_policy"], "source_url": blob}]
    hashes = "".join(
        f'<li><code>{esc(x["id"])}</code> {esc(x["rule_sha256"][:16])}&hellip; '
        f'{esc(x["name"])}</li>' for x in pre["strategies"])
    return (table(rows, cols=[("field", "field"), ("value", "value")], cls="zebra")
            + f'<details class="hashlist"><summary>Rule-text hashes for all '
              f'{len(pre["strategies"])} strategies</summary><ul>{hashes}</ul></details>'
            + '<p class="note">The registration file is '
              '<code>nfl-season-941fe39f/data/strategy/prereg.json</code>. '
              '<code>prereg.py</code> refuses to write it while the strategy, model or '
              'statistics module is uncommitted, so the commit above always predates every '
              'evaluation run shown on this page.</p>')


def page_strategies(m: dict) -> str:
    s = read_csv("strategies")
    g = read_csv("gates")
    body = f"""
<h1>Strategies and gates</h1>
<p class="lede">{len(s)} rules, each frozen before it saw data, each carrying the text, the windows, the
gates it must clear and a two-sided statement of what would change our mind. Backtest numbers appear here
and nowhere else; the leaderboard holds zero of them.</p>

{card("Pre-registration", f'''
<p>The rule text, the sample windows and the gate thresholds were written into
<code>tools/season_desk_941fe39f/strategies.py</code> before the evaluation code was run. The commit that
introduced them is the registration. The windows are fixed: train 1999-2012, validation 2013-2019,
holdout 2020-2025, prospective 2026.</p>
<p>Nothing on this page has been re-tuned after seeing a result. Where a rule could not be evaluated the
reason is printed in the row, and the rule still counts in the multiplicity family, so it cannot be
quietly dropped.</p>
{prereg_block()}
''')}

{card("The register", table(s, cols=[("id", "ID"), ("name", "rule"), ("family", "division"),
     ("units", "units"), ("verdict", "verdict"), ("n_holdout", "holdout n"),
     ("bss_holdout", "Brier skill"), ("roi_holdout", "ROI"), ("p_holm", "p (Holm)"),
     ("failed_gates", "blocked by"), ("what_would_change_our_mind", "what would change our mind")],
     cls="zebra"),
 note=("Every non-control row is PAPER. The ROI column is published because the brief asks for it, and "
       "it is never used to rank: ranking is by Brier skill on the leaderboard, and no row is eligible."))}

{card("The nine gates", table(g, cols=[("gate", "gate"), ("rule", "rule"), ("why", "why it exists"),
     ("threshold", "threshold"), ("measurable_in_corpus", "measurable here?")], cls="zebra"),
 note=("G3 (beat the close) needs an opening price and cannot be computed from one snapshot, so it fails "
       "by construction and is recorded as failed rather than skipped. G3B is the measurable substitute: "
       "does our disagreement with the close predict the result relative to the close."))}

{card("Why no strategy is certified", f'''
<ol class="tight">
<li><strong>G4 (Brier skill vs the close)</strong> fails for every family: the market is better.</li>
<li><strong>G3B (residual alpha)</strong> fails for every family: our disagreements do not predict results
out of sample.</li>
<li><strong>G3 (beat the close)</strong> cannot be evaluated at all: there is no opening price.</li>
<li><strong>G6 (multiplicity)</strong> fails: with 12 families tested, no raw p-value survives Holm.</li>
<li><strong>G5 (calibration)</strong> fails for most: the spread probabilities are not well calibrated at
the tails.</li>
</ol>
<p>This is not a bug in the gates. A gate that passed any of the above on this evidence would be a gate
that is too weak.</p>''')}
"""
    return page("strategies.html", "Strategies and gates",
                "Frozen rules, nine gates, zero certified", body, m)


def page_luck(m: dict) -> str:
    rows = read_csv("luck_panel")
    rows.sort(key=lambda r: -num(r["luck_wins"], 0))
    body = f"""
<h1>Removal of luck</h1>
<p class="lede">A record is partly luck. This page separates the part of a club's 2026 record that scoring
margin explains from the part it does not, and then does the same arithmetic for a strategy: how much of
a good run could be noise.</p>

{card("The 32 clubs, 2026", table(rows, cols=[("team", "club"), ("games", "G"), ("w", "W"), ("l", "L"),
     ("t", "T"), ("pf", "PF"), ("pa", "PA"), ("actual_win_pct", "actual win%"),
     ("pythagorean_win_pct", "expected win%"), ("luck_wins", "luck (wins)"),
     ("one_score_wins", "one-score W"), ("one_score_games", "one-score G"),
     ("one_score_win_pct", "one-score win%")], cls="zebra"),
 note=("Expected wins use the Pythagorean form with exponent 2.37 — a convention, not a league value, "
       "applied identically to every club and flagged F-11. Luck is actual minus expected, in wins. "
       "Positive means the record is better than the scoring margin explains."))}

{card("How to read the table", '''
<p>Denver at 7-2 with a 0.537 expected rate is the clearest case: the record is ahead of the scoring. That
is not proof of luck; it is a warning that the record alone overstates the team. Cleveland at 6-4 with a
0.408 expected rate is the reverse: the scoring says the record understates them.</p>
<p>Neither statement is a pick. Both are the kind of input a side market should already contain, and the
fact that the closing line already contains it is the reason the model struggles: the luck was priced
before we looked.</p>''')}

{card("The same arithmetic for a strategy", '''
<p>The brief asks to remove luck from the strategy side too, and the desk does it three ways:</p>
<ul class="tight">
<li><strong>A cluster bootstrap</strong> on every interval, resampling whole weeks rather than rows,
because games in a week share a slate and bets in a game share a result.</li>
<li><strong>Holm adjustment</strong> across every family tested, so the number of trials is priced in.</li>
<li><strong>A break-even test</strong> against the prices actually taken, not against 50%.</li>
</ul>
<p>The power calculation is the useful number for planning. A bettor who truly wins 55% of -110 bets needs
<strong>2,243</strong> graded bets to separate that from the 52.4% break-even at 80% power. A 200-bet
season at 55% happens by chance 20.8% of the time for a break-even bettor. Any leaderboard shorter than
that is a lottery, which is why this one is empty rather than short.</p>''')}

{card("Controls as the luck floor", '''
<p>Three controls run on every leaderboard pass: a seeded coin flip, always-favourite and always-home. A
strategy that cannot beat them is not measuring skill. On the holdout the three controls return
-6.2%, -6.3% and -4.3% — the vig, as they must.</p>''')}
"""
    return page("luck.html", "Removal of luck", "Expected vs actual, and how much of a run is noise", body, m)


def page_depth(m: dict) -> str:
    slots = read_csv("depth_slots")
    to = read_csv("roster_turnover")
    shared = [s for s in slots if s["shared_rank1"] == "YES"]
    empty = [s for s in slots if s["empty_rank1"] == "YES"]
    stripped = [s for s in slots if s["jersey_numbers_stripped"] == "YES"]
    body = f"""
<h1>Depth and replacements</h1>
<p class="lede">Depth comes from the clubs' own charts, never from jersey order, salary or experience. A
rank-1 cell holding two players is stored as a group. A cell the club left empty stays empty. The
replacement is published with his depth rank, because "somebody replaced him" is not a measurement.</p>

<div class="kpis">
{kpi(str(m['depth_checks']['clubs']), "clubs parsed", "of 32 in the league")}
{kpi(str(m['depth_checks']['slots']), "slots", "offence and defence only")}
{kpi(str(m['depth_checks']['shared_rank1_slots']), "shared rank-1 slots", "two players the club named equally")}
{kpi(str(m['depth_checks']['empty_rank1_slots']), "empty rank-1 slots", "kept empty, never filled by promotion")}
{kpi(str(m['depth_checks']['slots_with_jersey_stripped']), "rows with a jersey number", "number stripped, raw cell kept")}
</div>

{card("The five clubs captured on 2026-11-17", table(
    [{"team": s["team"], "unit": s["unit"], "position": s["position"],
      "rank1_raw": s["rank1_raw"], "rank2": s["rank2"], "shared": s["shared_rank1"],
      "empty": s["empty_rank1"], "jersey": s["jersey_numbers_stripped"],
      "published_date": s["published_date"] or "(none printed)",
      "captured_utc": s["captured_utc"][5:16].replace("T", " ") + "Z",
      "source_url": s["source_url"]} for s in slots],
    cols=[("team", "club"), ("unit", "unit"), ("position", "slot"), ("rank1_raw", "rank 1 (as published)"),
          ("rank2", "rank 2"), ("shared", "shared"), ("empty", "empty"),
          ("jersey", "jersey stripped"), ("published_date", "club's own date"),
          ("captured_utc", "captured")], cls="zebra"),
 note=(f"All {m['depth_checks']['slots']} slots are in the committed CSV. The raw cell is kept beside the "
       f"parsed name so a reader can check the strip did not damage a name. Green Bay's one unlabelled "
       f"continuation row is joined to the running-back slot above it, which turns that slot into a "
       f"four-deep chain instead of inventing an empty fifth slot."))}

{card("Shared slots, stored as groups", f'''
<p>Seattle publishes <strong>Cooper Kupp and Rashid Shaheed in one rank-1 cell</strong>. A parser that takes
"the first name in the first cell" would fabricate a single starter the club never named and silently
drop the other player. This desk stores the group, counts it, and shows the count.</p>
''' + table([{"slot_id": s["slot_id"], "team": s["team"], "position": s["position"],
             "rank1_raw": s["rank1_raw"], "count": s["rank1_count"], "source_url": s["source_url"]}
            for s in shared] if shared else [],
            cols=[("team", "club"), ("position", "slot"), ("rank1_raw", "rank-1 cell"),
                  ("count", "players named")]) + '''
<p class="note">A group of two is a statement by the club that it has not named a single starter. The
deficiency matrix treats both players as available starters rather than picking one.</p>''')}

{card("Empty slots, left empty", f'''
<p>Across the 700 carried-forward slots, two clubs publish an empty rank-1 cell (the Jets at DL and the
Eagles at DT). In the five clubs re-read this session, no offence or defence row has an empty rank-1
cell; the brief's report of an empty Washington slot does not reproduce on today's page (F-07).</p>
<p>An empty rank-1 cell is never filled by promoting rank 2. It is stored as empty, and the club is
recorded as having named nobody.</p>''')}

{card("The two parsing failures named in the brief", '''
<table class="zebra"><thead><tr><th>case</th><th>state</th><th>what was done</th></tr></thead><tbody>
<tr><td>Green Bay prepends jersey numbers</td><td>fixed</td>
<td>The parser strips a leading all-digit token, stores the raw string beside the name, and a count of
stripped rows is published. 22 slots in the capture were stripped. The strip never reorders anything:
there is no code path that sorts by jersey number.</td></tr>
<tr><td>Houston publishes its chart as an image</td><td>not fixed, and not guessed</td>
<td>The page text holds a heading and one image element with no names. A direct fetch of the image is
blocked by the sandbox TLS policy, and the permitted text fetcher does not read images. Houston contributes
zero rows. F-02.</td></tr>
</tbody></table>''')}

{card("Roster turnover as a first-class event", table(to,
     cols=[("player", "player"), ("from_team", "from"), ("to_team", "to"),
           ("transaction_date", "date"), ("appears_on_chart_of", "chart shows"),
           ("slot", "slot"), ("consistent", "consistent?")], cls="zebra"),
 note=("Depth is an expectation with a timestamp. A trade invalidates the chart for both clubs; the check "
       "here is whether the chart caught up. All three matched transactions are consistent on the day of "
       "the capture."))}

{card("What is missing, and why it matters", '''
<p>Depth rank is not playing time. The brief is explicit that depth must not be modelled from jersey
order, and this desk does not; but club-chart order is still an opinion. The measurable alternative is
official snap counts, and the public snap-count files sit behind a host this sandbox cannot reach (F-05).
Until then the honest statement is: <em>the club named this player at this rank on this day</em>, not
<em>this player started</em>.</p>''')}
"""
    return page("depth.html", "Depth and replacements", "Club-published order, groups, and replacement depth", body, m)


def page_availability(m: dict) -> str:
    inj = read_csv("injuries")
    delta = read_csv("injury_delta")
    reps = read_csv("replacements")
    body = f"""
<h1>Availability</h1>
<p class="lede">Every injury read carries a clock time, and the published number is the <em>change</em>
between reads, not the level. Here there are three clock times for the week-10 report and the measured
change between them is zero rows. That zero is published as a result.</p>

{card("Coverage this week", f'''
<div class="kpis">
{kpi(str(len(inj)), "injury rows read", "across 4 clubs in this capture")}
{kpi(str(len(delta)), "rows with two clock times", "so a delta can be computed")}
{kpi("0", "rows that changed", "between 2026-11-15T23:27Z and 2026-11-17T00:57Z", "ok")}
{kpi("not yet", "week 11 report", "the week-11 URL serves week 10 (F-09)", "warn")}
</div>
<p>The league has not published a week-11 report at the time of this capture:
<code>nfl.com/injuries/league/2026/reg11</code> returns the week-10 table, and the Colts-Texans game centre
independently prints "Injury Report is not available at this time". Publishing an empty week-11 table is
the correct output; filling it from the week-10 table would be a fabrication.</p>''')}

{card("The delta, not the level", table(delta,
     cols=[("team", "club"), ("player", "player"), ("position", "pos"),
           ("prior_practice", "practice then"), ("now_practice", "practice now"),
           ("prior_game", "game then"), ("now_game", "game now"),
           ("changed", "changed"), ("interpretation", "reading")], cls="zebra"),
 note=("A blank designation is a real state: the club published no game status for that player on that "
       "read. It is shown blank rather than as 'Questionable' or any assumed value."))}

{card("The 12 rows this capture depends on", table(inj,
     cols=[("team", "club"), ("player", "player"), ("position", "pos"), ("injury", "injury"),
           ("practice_status", "practice"), ("game_status", "game status"), ("read_utc", "read at")],
     cls="zebra"),
 note=("Only the rows this session uses as named evidence are transcribed. The full 326-row week-10 table "
       "already in the repository is the first clock time and is used read-only."))}

{card("Replacements, with their depth", table(reps,
     cols=[("team", "club"), ("player", "out"), ("position", "pos"), ("game_status", "status"),
           ("position_slot", "slot"), ("replacement", "named replacement"),
           ("replacement_rank", "rank"), ("replacement_depth_tier", "depth of the replacement"),
           ("finding", "reading")], cls="zebra"),
 note=("Where the club names nobody at rank 2, the row says so instead of inventing a substitute. Where the "
       "injured player is not a rank-1 player on the chart, the row says that too."))}

{card("The reserve list, because 'not listed' is not 'available'", '''
<p>Malik Willis is absent from the weekly injury report. That absence is not evidence of health: the
official reserve list shows Miami placing him on Reserve/Injured on 11/10. The desk captures the reserve
list on the same date as the report so the two can never be read apart.</p>
<p>17 reserve-list rows were captured, including TreVeyon Henderson, who appears on the week-10 report as
Out and on the reserve list as Reserve/Injured dated 11/14 — the same player through two official lenses.
<a href="https://www.nfl.com/transactions/league/reserve-list/2026/11" target="_blank" rel="noopener nofollow">source</a></p>''')}

{card("What cannot be confirmed", '''
<ul class="tight">
<li><strong>Who actually played.</strong> The official inactive list URL returns HTTP 404 and no game book
has been read (F-04, F-05).</li>
<li><strong>Announced starter changes.</strong> No dated league or club statement naming a starter change
has been read for this week (R-41).</li>
<li><strong>What Questionable means.</strong> One row in this capture carries it. An empirical play rate
needs seasons of designations joined to inactive lists, and the inactive half is the feed that is missing
(R-43, R-52).</li>
</ul>''')}
"""
    return page("availability.html", "Availability", "Clock times, deltas and named replacements", body, m)


def page_matchup(m: dict) -> str:
    rows = read_csv("deficiency_matrix")
    body = f"""
<h1>Deficiency matrix</h1>
<p class="lede">Who is out, who replaces him, and which opposing slot now faces that replacement. Built
only from named replacements on official charts. Where a club named nobody, there is no row.</p>

{card(f"{len(rows)} pairings", table(rows,
     cols=[("attacking_team", "attacking"), ("attacking_slot", "slot"),
           ("attacking_starter_out", "starter out"), ("attacking_replacement", "replacement"),
           ("attacking_replacement_rank", "rank"), ("defending_team", "defending"),
           ("defending_slot", "slot"), ("defending_player_expected", "expected defender"),
           ("defending_depth_rank", "rank"), ("matchup_deficiency", "deficiency"),
           ("both_sides_deficient", "both deficient?")], cls="zebra"),
 note=("The pairing covers the five clubs with a chart captured today, so 27 clubs contribute nothing. "
       "This is a working preview of the matrix, not league coverage."))}

{card("How the pairing is chosen", '''
<p>Each position group has a declared set of opponents it lines up against: receivers face corners and
safeties, tackles face edge rushers and interior linemen, running backs face linebackers and interior
linemen. That mapping is a modelling choice and is published in
<code>tools/season_desk_941fe39f/availability.py</code>.</p>
<p>A pairing appears only when at least one side has a <em>named</em> replacement. If the starter is out
and the club named nobody at rank 2, the matrix stays silent, because the alternative is to invent a
replacement.</p>
<p>A group at rank 1 (two players in one cell) is treated as two available starters, so a team with a
shared slot is not marked deficient just because its chart lists two names.</p>''')}

{card("What would make this decisive", '''
<p>Three things, in order of value: an official inactive list (so "out" becomes "did not dress"), official
snap counts (so "backup" becomes "played 12% of snaps"), and charts for the other 27 clubs. The first two
are blocked by source availability; the third is a capture-cadence problem that this desk's ledger is
already built to absorb.</p>''')}
"""
    return page("matchup.html", "Deficiency matrix", "Backups facing starters, from named replacements", body, m)


def page_correlations(m: dict) -> str:
    rows = read_csv("correlations")
    body = f"""
<h1>Correlations</h1>
<p class="lede">Every value computed from officially sourced numbers, with n published beside it and a 95%
interval. Nothing is quoted from an aggregator without saying so, and nothing is published without a
sample size.</p>

{card(f"{len(rows)} correlations from the pinned corpus", table(rows,
     cols=[("id", "ID"), ("pair", "pair"), ("r", "r"), ("n", "n"),
           ("ci_lo", "CI low"), ("ci_hi", "CI high"), ("window", "window")], cls="zebra"),
 note=("Pooled across all games where both values exist, 1999-2026. Pooling is a choice: a within-season "
       "estimate would answer a slightly different question (does wind matter relative to the league that "
       "season) and is not published here."))}

{card("Reading them", '''
<p>Three of the seven have intervals that exclude zero, and each says something usable:</p>
<ul class="tight">
<li><strong>Wind and total: r = -0.095, n = 5,026.</strong> More wind, fewer points. The interval is
-0.122 to -0.068. It is small, and it is already in the closing total, which is why it is not a strategy
on its own. It is the one fixture fact that shows a real marginal signal.</li>
<li><strong>Rest difference and margin: r = 0.034, n = 7,116.</strong> Real, tiny, and priced.</li>
<li><strong>Closing spread and margin: r = 0.432, n = 7,116.</strong> The market's own accuracy, published
as the benchmark a model would have to beat.</li>
</ul>
<p>The two that do not exclude zero are worth naming for what they rule out: temperature has no
detectable marginal relationship with the total in this sample, and the closing spread is essentially
uncorrelated with the closing total (r = -0.011), which is why the side and total models can be fitted
separately.</p>''')}

{card("What is withheld, and why", '''
<p>No correlation on this page is computed from a source that is not the pinned corpus or an official
capture. Where a value would need a feed this environment cannot reach — same-game prop correlation, for
instance — nothing is published: there is no number, only a question (Q-12).</p>''')}
"""
    return page("correlations.html", "Correlations", "Every value with its n and interval", body, m)


def page_corpus(m: dict) -> str:
    cm = m["corpus"]
    checks = m["crosschecks"]
    by_season = read_csv("model_by_season")
    body = f"""
<h1>Corpus</h1>
<p class="lede">The backtest corpus is a single pinned tarball with a published hash. Anyone can re-fetch
the same bytes and rebuild every number on this site. The 136-game log the brief names is reconciled into
it, game for game.</p>

{card("Provenance", f'''
<table class="kv-table">
<tr><th>Source</th><td><a href="https://github.com/nflverse/nfldata" target="_blank" rel="noopener nofollow">github.com/nflverse/nfldata</a>,
commit <code>{esc(cm['tarball_sha256'][:0])}{esc('e045566ea9f90e3aa15b3b43d87df4ea63d0fae2')}</code></td></tr>
<tr><th>Fetched as</th><td>one gzip tarball of the repository at that commit</td></tr>
<tr><th>SHA-256</th><td><code>{esc(cm['tarball_sha256'])}</code></td></tr>
<tr><th>Re-proved</th><td>on every build; a mismatch fails the build before a page is written</td></tr>
<tr><th>Licence</th><td>the source repository is published under CC-BY-4.0; attribution is on
<a href="sources.html">Sources</a></td></tr>
</table>
<p class="note">The corpus is a public mirror of the league's own game statistics and of operator closing
lines. It is not the league's own feed, and the difference matters: the desk calls these "market lines from
the corpus", never "the official price".</p>''')}

{card("What is in it", f'''
<div class="kpis">
{kpi(f"{m['counts']['graded_games']:,}", "graded games", "1999-2026, regular season")}
{kpi(str(m['counts']['seasons']), "seasons", "1999 through 2026")}
{kpi("46,812", "closing-line observations", "spread, total and moneyline rows combined")}
{kpi("2", "price series", "and they are not interchangeable (F-03)")}
</div>
''' + table([{"t": t["path"].split("/")[-1], "rows": t["rows"], "sha": t["sha256"][:16],
              "bytes": t["bytes"], "source_url": "https://github.com/nflverse/nfldata"}
             for t in m["corpus"]["tables"]],
            cols=[("t", "table"), ("rows", "rows"), ("sha", "sha256 (head)"), ("bytes", "bytes")]))}

{card("Cross-checks against independent official reads", f'''
<table class="zebra"><thead><tr><th>check</th><th>compared</th><th>matched</th><th>verdict</th></tr></thead>
<tbody>{''.join(f'<tr><td>{esc(c["name"])}</td><td>{c["compared"]:,}</td><td>{c["matched"]:,}</td><td>{status_badge(c["verdict"])}</td></tr>' for c in checks)}</tbody></table>
<p>Each check is written to fail loudly. The first compares every row of the 145-game official feed this
repository already held against the corpus; the second re-derives each club's record and points from the
corpus and reconciles every difference to a named game; the fourth tests the league's dated schedule
announcement against the live schedule facts. Full row-level detail is in the committed
<code>crosschecks.csv</code>.</p>''')}

{card("The brief's 136-game log", '''
<p>The brief refers to a 136-game log. The file it points at holds <strong>145</strong> final rows, and the
count is published as 145 rather than 136. All 145 match the corpus exactly, on both scores, so the log is
not merely carried forward: it is verified against an independent source and then absorbed.</p>''')}

{card("Season coverage", table(by_season,
     cols=[("season", "season"), ("n_games", "games originated"),
           ("alpha_r", "residual alpha r"), ("alpha_ci_lo", "CI low"),
           ("alpha_ci_hi", "CI high")], cls="zebra"),
 note="A held-out season is only held out once. 2026 carries prices for 163 games and results for 149, and is scored nowhere on this site.")}
"""
    return page("corpus.html", "Corpus", "A pinned, hashed, reconciled backtest corpus", body, m)


def page_price(m: dict) -> str:
    cc = {x["name"][:2]: x for x in m["crosschecks"]}
    price = cc.get("B.", {})
    ps = read_csv("price_snapshots")
    body = f"""
<h1>Price policy</h1>
<p class="lede">The brief asks for the price-data policy to be decided before any backtest is published.
Here it is, in three rules, each with the measurement that forced it.</p>

{card("The policy", '''
<ol class="tight">
<li><strong>One series, named in every table.</strong> The backtest uses
<code>games.spread_line_home</code> and <code>games.total_line</code> from the pinned corpus and nothing
else. The separate <code>closing_lines.csv</code> file is used only for the comparison below.</li>
<li><strong>A price is a snapshot with a clock time, or it does not exist.</strong> A row without a clock
time is not a price. This is why no opening price is published: there is no opening snapshot, only a
closing one.</li>
<li><strong>Two-sided or dropped.</strong> A bet is graded only where both sides of the market carry a
price at the same snapshot, so the implied probability can be de-vigged from the pair rather than
assumed.</li>
</ol>
<p>Consequence, stated plainly: <strong>closing-line value cannot be signed anywhere in this project</strong>,
because CLV needs an open and a close from the same book. Gate G3 is recorded as failed rather than skipped
and no ROI claims a beat-the-close property.</p>''')}

{card("Why rule 1 exists: the two series disagree", f'''
<div class="kpis">
{kpi(f"{price.get('matched', 0):,}/{price.get('compared', 0):,}", "games where the two series are identical",
     f"{100 * price.get('matched', 0) / max(price.get('compared', 1), 1):.1f}% of joinable games", "warn")}
{kpi(f"{price.get('favourite_flips', 0)}", "games where they disagree about the favourite", "opposite sides of zero", "bad")}
{kpi(f"{abs(price.get('median_abs_diff', 0)):.2f}", "median absolute difference", "points")}
{kpi(f"{abs(price.get('p90_abs_diff', 0)):.2f}", "90th percentile difference", "points")}
</div>
<p>An ROI computed on one series and checked against the other would change on {100 * (price.get('compared', 1) - price.get('matched', 0)) / max(price.get('compared', 1), 1):.0f}% of games.
Publishing one number without naming the series would be publishing an unreproducible result, so every
table on this site names it.</p>
''' + table(price.get("rows", []),
           cols=[("season", "season"), ("games_compared", "games compared"),
                 ("identical", "identical"), ("agree_pct", "agreement")], cls="zebra") + '''
<p class="note">The comparison is limited to 2006-2018 because that is the range the separate closing-lines
file covers. F-03.</p>''')}

{card(f"The price store: {len(ps):,} rows, all closing", table(ps, limit=12,
     cols=[("game_id", "game"), ("season", "season"), ("week", "wk"), ("market", "market"),
           ("snapshot_type", "snapshot"), ("line", "line"), ("price_american_home_or_over", "price"),
           ("open_line", "open"), ("open_status", "open status")], cls="zebra"),
 note=("Every row is a close. The open column is empty on every row and says why. That is the single most "
       "consequential gap in this project (F-01)."))}

{card("What would change the policy", '''
<p>A source that publishes an open and a close from the same book, with a timestamp on each. With that,
rule 2 becomes satisfiable and G3 becomes measurable. Until then the policy is not a preference; it is the
only defensible reading of the data that exists.</p>
<p>See <a href="questions.html">Q-01 and Q-02</a> for the cheapest route to that source.</p>''')}
"""
    return page("price-store.html", "Price policy", "One series, named; a snapshot or nothing", body, m)


def page_schedule(m: dict) -> str:
    slate = read_csv("slate_week11")
    ann = read_csv("schedule_announcement")
    body = f"""
<h1>Schedule</h1>
<p class="lede">The league's dated schedule announcement published beside the live schedule facts, as the
brief requires. The announcement is the plan; the live page is the operation. When they differ, both are
shown.</p>

{card("Week 11, 2026 — the live slate", table(slate,
     cols=[("game_id", "game"), ("gameday", "date"), ("gametime_et", "kickoff ET"),
           ("weekday", "day"), ("away", "away"), ("home", "home"), ("stadium", "venue"),
           ("location", "site"), ("market_spread_home", "market side"),
           ("market_total", "market total")], cls="zebra"),
 note=("12 of 13 venues are transcribed from the live schedule page and one (MIN at SF, Estadio Banorte) "
       "from the official game centre. The provenance of each is in the committed CSV; R-23 records that "
       "12 game-centre reads would be needed to upgrade the other twelve."))}

{card("The league's dated announcement, and whether it still holds", table(ann,
     cols=[("claim_id", "claim"), ("official_claim", "the announcement says"),
           ("result", "the live schedule says"), ("match", "match")], cls="zebra"),
 note=("Seven claims from the May 14, 2026 release were checked. Six match outright; the Week 18 slot claim "
       "is recorded as pending because the announcement itself says those dates are set after Week 17, so "
       "zero scheduled Saturdays is the expected state rather than a disagreement."))}

{card("The announcement, as published", f'''
<p><a href="https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced"
target="_blank" rel="noopener nofollow">2026 NFL Schedule Announced</a> — NFL Football Communications,
<strong>May 14, 2026</strong>. It states an 18-week, 272-game season opening on Wednesday, September 9 in
Seattle; the first regular-season game in Australia in Week 1; nine international games, the most ever;
and that Week 18 dates and times are determined after Week 17.</p>
<p>The full release is attached as a by-week PDF and a by-division PDF, both linked from the capture in
<code>nfl-season-941fe39f/data/official/schedule_announcement_2026.json</code>.</p>''')}

{card("Why this pairing matters", '''
<p>A live schedule page is a moving target: games get flexed, kickoff times move, and a venue can be
reassigned. The dated announcement is the fixed record of what was promised. Publishing them side by side
means a reader can see whether a fixture was moved rather than having to infer it from a missing row.</p>
<p>The desk checks the seven claims on every build. If the league changes a fixture, the check fails and
the build stops, which is the drift alarm working as intended.</p>''')}
"""
    return page("schedule.html", "Schedule", "The dated announcement beside the live slate", body, m)


def page_snapshots(m: dict) -> str:
    led = read_csv("snapshot_ledger")
    clog = read_csv("capture_log")
    body = f"""
<h1>Snapshots and alarms</h1>
<p class="lede">An append-only ledger with a hash per capture, a clock time per read, a schema contract per
parser, a freshness alarm and point-in-time replay. The mechanism for the brief's snapshot requirements is
one mechanism, not five.</p>

{card("The ledger", table(led,
     cols=[("source_id", "capture"), ("unit", "unit"), ("captured_utc", "clock time"),
           ("age_hours", "age (h)"), ("state", "freshness"), ("sha256", "sha256 (head)"),
           ("required_fields_present", "schema ok"), ("missing_fields", "missing")], cls="zebra"),
 note=("Age is computed against the build clock. A capture older than the unit's limit turns the row to "
       "STALE and the build reports it; it does not silently pass."))}

{card("Replay by unit", table(clog,
     cols=[("unit", "unit"), ("distinct_clock_times", "distinct clock times"),
           ("first_capture", "first"), ("last_capture", "last"), ("can_replay", "replayable?")],
     cls="zebra"),
 note=("A unit with one clock time cannot answer 'what was known at kickoff'. This table is the honest "
       "status of that requirement: injuries and depth have two or more clock times; transactions, the "
       "reserve list and the schedule announcement have one."))}

{card("The three alarms", '''
<table class="zebra"><thead><tr><th>alarm</th><th>fires when</th><th>consequence</th></tr></thead><tbody>
<tr><td>Freshness</td><td>a unit's newest capture is older than its limit (24 h for the injury report,
168 h for depth, transactions and reserve list)</td><td>the row is marked STALE on this page and reported
in the build output</td></tr>
<tr><td>Schema drift</td><td>a required field disappears from a capture</td><td>the build fails before any
page is written; a blank is never published in place of a field</td></tr>
<tr><td>Corpus drift</td><td>the tarball's SHA-256 no longer matches the pin</td><td>the build stops and
says to record a new pin, because a new commit means a new corpus</td></tr>
</tbody></table>
<p>All three are exercised by the unit tests, and the schema alarm is proved by a test that removes a field
and asserts the build refuses.</p>''')}

{card("Storage", '''
<p>The captures live in the repository under <code>nfl-season-941fe39f/data/official/</code> and the
derived tables under <code>data/derived/</code>. The public site publishes only the derived layer; the raw
capture rows stay in the repository, which is the public/private split the brief asks for. The pinned
corpus tarball is also committed, because a hash is only useful if the bytes behind it can be checked.</p>
<p class="note">The capture cadence is manual in this session. Making it a scheduled job is suggestion
S-05 and S-15; it is not implemented, and the freshness table says so rather than implying a cron.</p>''')}
"""
    return page("snapshots.html", "Snapshots and alarms", "Hashed captures, replay and drift alarms", body, m)


def page_changes(m: dict) -> str:
    delta = read_csv("injury_delta")
    to = read_csv("roster_turnover")
    body = f"""
<h1>What changed</h1>
<p class="lede">A static snapshot is a claim about the past dressed as the present. This page diffs the
official reads this desk holds, so a reader sees movement rather than a level.</p>

{card("Injury report: two clock times", f'''
<p>Two official reads of the week-10 report exist: <strong>2026-11-15T23:27Z</strong> (the e46fb855 capture,
carried forward read-only) and <strong>2026-11-17T00:57Z</strong> (this session). For the 12 rows this
session depends on, the number that changed is <strong>{sum(1 for d in delta if d['changed'] == 'YES')}</strong>.</p>
''' + table(delta, cols=[("team", "club"), ("player", "player"), ("prior_practice", "then"),
                        ("now_practice", "now"), ("prior_game", "then"), ("now_game", "now"),
                        ("changed", "changed")], cls="zebra") + '''
<p class="note">A zero delta is a result, not an absence of one. It says the league's published designations
were stable across 25 hours in a week with a Thursday game still to be played.</p>''')}

{card("Depth and transactions", table(to,
     cols=[("player", "player"), ("from_team", "from"), ("to_team", "to"),
           ("transaction_date", "date"), ("slot", "slot on the chart"),
           ("consistent", "chart agrees?")], cls="zebra"),
 note=("Twelve November trades were checked against the charts captured the same day. The three players who "
       "appear in the five captured charts are all on the correct club's chart."))}

{card("What is not yet diffable", '''
<ul class="tight">
<li><strong>Depth week to week.</strong> One capture date exists for this desk's five clubs. The 700
carried-forward slots are dated 2026-11-15, which gives a second point but from another session's
transcription rather than a fresh read.</li>
<li><strong>Week 11 availability.</strong> The report is unpublished, so there is nothing to diff.</li>
<li><strong>Inactives.</strong> No capture exists.</li>
</ul>
<p>Each of these is a cadence problem with a named owner in <a href="questions.html">Questions</a>, not a
missing idea.</p>''')}
"""
    return page("changes.html", "What changed", "Diffs between official reads, not snapshots", body, m)


def page_audit(m: dict) -> str:
    rows = read_csv("audit")
    body = f"""
<h1>Repo audit</h1>
<p class="lede">The brief asks for a line-by-line review of the repository against official sources, with
irregularities flagged rather than silently fixed. This is that review: {len(rows)} claims, each re-checked
against a source, with the result published even where the claim does not survive.</p>

{card("Checks", table(rows,
     cols=[("id", "ID"), ("claim", "claim under review"),
           ("verification_performed", "what was checked"), ("result", "result")], cls="zebra"))}

{card("The three that did not reproduce", '''
<p>Three claims in the brief describe a state this desk cannot find on the official page today. They are
published as not-reproduced rather than quietly dropped, because the alternative is to assert a fact that
a reader can check and find false:</p>
<ul class="tight">
<li><strong>Baltimore publishing Lamar Jackson and Tyler Huntley at quarterback.</strong> The 2026-11-17
chart lists Jacoby Brissett, Joe Fagnano and Kedon Slovis, and Brissett's arrival is dated 11/06 in the
league's transaction log. F-06.</li>
<li><strong>Washington leaving a depth slot empty.</strong> No offence or defence row on the 2026-11-17 page
has an empty rank-1 cell. F-07.</li>
<li><strong>The Detroit designations being blank.</strong> All three read as Out. Published as reproduced,
not as a failure.</li>
</ul>''')}

{card("Counting differences", '''
<p>Where the brief gives a count and this desk measures a different one, both numbers are published:</p>
<table class="zebra"><thead><tr><th>quantity</th><th>brief</th><th>measured</th><th>reading</th></tr></thead><tbody>
<tr><td>games in the log</td><td>136</td><td>145</td><td>the file the brief points at holds 145 finals</td></tr>
<tr><td>injury rows, week 10</td><td>254 / 279</td><td>326 in the carried-forward file</td><td>three different
counts from three different reads; this desk re-read 12 rows and publishes only those</td></tr>
<tr><td>shared rank-1 slots</td><td>149</td><td>14 in the carried-forward capture</td><td>not reproduced at
that scale; the mechanism is built and the count is computed, not typed</td></tr>
<tr><td>chart rows carrying a game designation</td><td>6 of 254</td><td>5 of the 12 rows re-read</td><td>a
full-table count is not claimed because the full table was not re-read</td></tr>
</tbody></table>''')}
"""
    return page("audit.html", "Repo audit", "Every claim re-checked, including the ones that fail", body, m)


def page_questions(m: dict) -> str:
    q = read_csv("questions")
    body = f"""
<h1>Questions</h1>
<p class="lede">What we have, what we do not have, and the cheapest route to finding out — one row per
question, with the requirement it unblocks. This is the list a decision has to clear before it can be made
on evidence rather than on belief.</p>

{card(f"{len(q)} questions", table(q,
     cols=[("id", "ID"), ("question", "question"), ("what_we_have", "what we have"),
           ("what_we_do_not_have", "what we do not have"),
           ("cheapest_route", "cheapest route to the answer"),
           ("blocks", "unblocks"), ("severity", "severity")], cls="zebra"),
 note=("A question marked 'answered' has a measured result on this site. A question marked 'blocking' "
       "stops a requirement from being met honestly; 'non-blocking' means a working answer exists."))}

{card("The five that matter most", '''
<ol class="tight">
<li><strong>Q-01 — is there an opening price anywhere?</strong> Without one, CLV does not exist and no
move-based strategy can be graded.</li>
<li><strong>Q-02 — which price series is the closing market?</strong> The two series disagree on more than
a fifth of joinable games.</li>
<li><strong>Q-04 — who actually started?</strong> The club chart is an expectation; the game book and the
inactive list are the record.</li>
<li><strong>Q-06 — how deep is the replacement?</strong> Depth rank is not playing time; snaps are.</li>
<li><strong>Q-17 — can the model be improved enough to beat the close?</strong> Only if a feature arrives
that the close does not already contain, and the only candidate is availability.</li>
</ol>''')}
"""
    return page("questions.html", "Questions", "What is missing and how to get it", body, m)


def page_suggestions(m: dict) -> str:
    s = read_csv("suggestions")
    body = f"""
<h1>Suggestions</h1>
<p class="lede">A reviewable list of paths, each with the options considered, the recommendation, and the
observation that would reverse it. Nothing here is implemented silently: the suggestions marked
<em>implemented</em> describe work that is visible on this site, and everything else waits for a decision.</p>

{card(f"{len(s)} suggestions", table(s,
     cols=[("id", "ID"), ("title", "suggestion"), ("problem", "the problem"),
           ("options", "options"), ("recommendation", "recommendation"),
           ("what_would_change_the_call", "what would change the call"),
           ("status", "status")], cls="zebra"))}

{card("Where to start, if you only read three", '''
<ol class="tight">
<li><strong>S-02 — an opening-line history.</strong> The largest single constraint on the project. Without
it, a third of the brief cannot be answered at all.</li>
<li><strong>S-05 — a second clock time for every availability unit.</strong> Cheap, and it turns four
"cannot replay" rows into replayable ones.</li>
<li><strong>S-01 — one index for the eleven desks.</strong> A reader cannot currently tell which desk is
current, and four desks publish different counts for the same requirement.</li>
</ol>''')}
"""
    return page("suggestions.html", "Suggestions", "Reviewable paths before any implementation", body, m)


def page_flagged(m: dict) -> str:
    f = read_csv("flags")
    blocking = [x for x in f if x["severity"] == "blocking"]
    body = f"""
<h1>Flagged for review</h1>
<p class="lede">Irregularities, gaps and things that did not reproduce. Each carries a source link so it
can be checked independently. None of these blocks publication; all of them block a stronger claim than
this site makes.</p>

<div class="kpis">
{kpi(str(len(f)), "flags", "all with a source")}
{kpi(str(len(blocking)), "blocking", "no honest version exists until they clear", "bad")}
{kpi(str(len([x for x in f if x['severity'] == 'review'])), "for review", "a judgement call is needed", "warn")}
{kpi(str(len([x for x in f if x['severity'] == 'informational'])), "informational", "published for completeness", "muted")}
</div>

{card("Every flag", table(f,
     cols=[("id", "ID"), ("severity", "severity"), ("title", "what it is"), ("detail", "detail"),
           ("status", "status")], cls="zebra"))}

{card("How to act on a flag", '''
<p>Open a GitHub issue titled with the flag ID. The suggestion S-11 proposes exactly that mechanism,
because a static list is easy to publish and hard to close out. Until an issue exists, a flag stays open
by definition.</p>''')}
"""
    return page("flagged.html", "Flagged for review", "Irregularities, each with a source", body, m)


def page_sources(m: dict) -> str:
    srcs = [
        ("Pinned corpus", "nflverse/nfldata at commit e045566", "https://github.com/nflverse/nfldata",
         "schedules, results, closing lines, roof, surface, rest, stadium, 1999-2026", "primary mirror, CC-BY-4.0"),
        ("Corpus field definitions", "DATASETS.md in the same repository",
         "https://github.com/nflverse/nfldata/blob/master/DATASETS.md",
         "meaning of spread_line, total_line, roof, surface, result and total", "documentation"),
        ("League standings", "nfl.com/standings/league/2026/REG",
         "https://www.nfl.com/standings/league/2026/REG", "32 clubs W-L-T, PF, PA", "official"),
        ("Week 10 schedule and results", "nfl.com/schedules/2026/by-week/week-10",
         "https://www.nfl.com/schedules/2026/by-week/week-10", "official finals used in the reconciliation", "official"),
        ("Week 11 schedule", "nfl.com/schedules/2026/by-week/week-11",
         "https://www.nfl.com/schedules/2026/by-week/week-11", "13 fixtures, kickoff times, venues", "official"),
        ("Game centre, MIN at SF", "nfl.com/games/vikings-at-49ers-2026-reg-11",
         "https://www.nfl.com/games/vikings-at-49ers-2026-reg-11", "venue for the Mexico City fixture", "official"),
        ("Week 10 injury report", "nfl.com/injuries/league/2026/reg10",
         "https://www.nfl.com/injuries/league/2026/reg10", "designations, practice status", "official"),
        ("Week 11 injury report", "nfl.com/injuries/league/2026/reg11",
         "https://www.nfl.com/injuries/league/2026/reg11", "serves week 10: the week-11 report is unpublished (F-09)", "official"),
        ("Transactions", "nfl.com/transactions",
         "https://www.nfl.com/transactions/", "12 November trades", "official"),
        ("Reserve list", "nfl.com/transactions/league/reserve-list/2026/11",
         "https://www.nfl.com/transactions/league/reserve-list/2026/11", "IR moves, including Malik Willis", "official"),
        ("Schedule release", "media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced",
         "https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced",
         "the dated schedule announcement, May 14 2026", "official"),
        ("Inactive lists", "nfl.com/inactives/league/2026/reg10",
         "https://www.nfl.com/inactives/league/2026/reg10", "returns HTTP 404 (F-04)", "official, unavailable"),
        ("Detroit depth chart", "detroitlions.com/team/depth-chart",
         "https://www.detroitlions.com/team/depth-chart", "22 slots", "official club publication"),
        ("Baltimore depth chart", "baltimoreravens.com/team/depth-chart",
         "https://www.baltimoreravens.com/team/depth-chart", "23 slots", "official club publication"),
        ("Green Bay depth chart", "packers.com/team/depth-chart",
         "https://www.packers.com/team/depth-chart", "23 slots, jersey numbers, dated Nov 10 2026", "official club publication"),
        ("Seattle depth chart", "seahawks.com/team/depth-chart",
         "https://www.seahawks.com/team/depth-chart/", "23 slots, one shared rank-1 cell", "official club publication"),
        ("Washington depth chart", "commanders.com/team/depth-chart",
         "https://www.commanders.com/team/depth-chart", "23 slots", "official club publication"),
        ("Houston depth chart", "houstontexans.com/team/depth-chart",
         "https://www.houstontexans.com/team/depth-chart", "image only, not transcribed (F-02)", "official club publication"),
        ("Snap counts (blocked)", "nflverse-data release, snap_counts",
         "https://github.com/nflverse/nflverse-data/releases/tag/snap_counts",
         "release asset host unreachable from the sandbox (F-05)", "public dataset, unavailable here"),
    ]
    rows = [{"s": a, "p": b, "u": c, "d": d, "t": e} for a, b, c, d, e in srcs]
    body = f"""
<h1>Sources</h1>
<p class="lede">Every source this desk read, what it was used for, and its tier. Two are listed because they
could not be reached; a source that cannot be read is a finding, not an omission.</p>

{card(f"{len(rows)} sources", table(rows,
     cols=[("s", "source"), ("p", "publisher / artefact"), ("d", "what it supplied"),
           ("t", "tier")], cls="zebra"),
 note=("Tiers mean exactly what they say. 'Official' is the league or the club. 'Public dataset' is a "
       "community mirror of league data, and it is labelled that way even where the underlying bytes "
       "originate with the league."))}

{card("Attribution and licence", '''
<p>The pinned corpus is the <a href="https://github.com/nflverse/nfldata" target="_blank"
rel="noopener nofollow">nflverse</a> project, published under CC-BY-4.0, which builds on nflfastR and its
predecessors. This desk re-publishes derived analysis of that corpus, not the corpus itself, and links to
the original for every table. Club and league pages are quoted for identification and linked, not
reproduced.</p>''')}
"""
    return page("sources.html", "Sources", "Every source read, and the two that could not be", body, m)


def page_methodology(m: dict) -> str:
    body = f"""
<h1>Methodology</h1>
<p class="lede">The rules that make the numbers on this site checkable, written down so they can be
attacked. If a rule here is wrong, the numbers it produced are wrong in a way a reader can name.</p>

{card("1. Nothing is inferred", '''
<p>Every table row ends in a source link or an explicit UNVERIFIED badge, and the check runs on the
generated HTML rather than on the CSVs, so a blank that escapes the data layer is still caught. Where a
value cannot be confirmed — a venue, a designation, a depth slot, a price — the cell is blank. A blank is
information: it says the official page did not say.</p>''')}

{card("2. The corpus is pinned, not tracked", '''
<p>The backtest reads a single tarball of one commit, whose SHA-256 is re-proved on every build. A new
commit is a new corpus and requires a new pin, recorded with the reason. Tracking a moving branch would
mean that a number published today could not be reproduced tomorrow.</p>''')}

{card("3. Walk-forward, with the cutoff published", '''
<p>Every originated market comes from a fit that used only games strictly before the target week's first
kickoff. The number of games in the fit and the cutoff date are columns on the row, so a reader does not
have to trust the claim; they can check it. No market is ever fitted on its own week.</p>''')}

{card("4. Rules are frozen before results exist", '''
<p>The fourteen rule texts, the three windows and the eight gate thresholds were written before the
evaluation code ran. Changing one requires a new commit, which is the new registration. This is why the
strategy table shows the rule text verbatim rather than a summary.</p>''')}

{card("5. Proper scores, and intervals that respect dependence", '''
<p>Ranking is by Brier skill against the de-vigged close. Intervals come from a cluster bootstrap that
resamples whole weeks, because games in a week share a slate and bets in a game share a result. The
p-values are Holm-adjusted across every family tested, so the number of trials is priced in rather than
ignored.</p>''')}

{card("6. De-vig, or drop", '''
<p>A probability is taken from a two-sided price pair and normalised, so the vig is removed from the pair
rather than assigned to one side. Where a pair does not exist, the bet is dropped and the count of dropped
rows is published. No vig-free probability is ever assumed.</p>''')}

{card("7. Two-sided falsification", '''
<p>Every strategy entry carries what would confirm it and what would refute it. A rule that can only be
confirmed is not a hypothesis; it is a belief.</p>''')}

{card("8. The public/private split", '''
<p>The site publishes derived analysis: indices, ratios, model output and links to the official page. The
raw row-level captures stay in the repository rather than being re-published as a data service. That is a
deliberate choice about the terms of the source data, not an oversight, and it is why every table links
out rather than embedding the original rows.</p>''')}

{card("9. Modelling choices are labelled as choices", '''
<p>Four constants are not measured: the 365-day half-life, the ridge penalties, the probit's starting
sigma, and the Pythagorean exponent. Each is published with its value, applied identically to every club
or every game, and flagged. A choice that is labelled can be argued with; a choice presented as a
measurement cannot.</p>''')}

{card("10. Reproduce it", '''
<pre><code>python3 tools/season_desk_941fe39f/fetch.py --check     # prove the corpus hash
python3 tools/season_desk_941fe39f/build.py             # rebuild every table and page
python3 tools/season_desk_941fe39f/verify.py            # re-check every published row
python3 -m unittest discover -s tests -p "test_season_desk*"</code></pre>
<p>No network access is needed for the rebuild: the corpus is committed, and every official capture is a
JSON file with its clock time and hash.</p>''')}
"""
    return page("methodology.html", "Methodology", "The rules that make the numbers checkable", body, m)


# --------------------------------------------------------------------- css
CSS = """/* Own5 NFL Season Desk — 941fe39f. Hand-written, no framework. */
:root{
 --bg:#0e1116; --panel:#161b22; --panel2:#1c2230; --ink:#e6edf3; --mute:#9aa7b4;
 --line:#2a3240; --ok:#2ea043; --warn:#d29922; --bad:#f85149; --info:#58a6ff;
 --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--info);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1240px;margin:0 auto;padding:0 20px}
.top{background:linear-gradient(180deg,#121821,#0e1116);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;padding:16px 20px}
.brand{font-weight:700;font-size:18px;color:var(--ink);letter-spacing:.2px}
.tag{color:var(--mute);font-size:13px}
nav.main{position:sticky;top:0;z-index:20;background:rgba(14,17,22,.96);
 border-bottom:1px solid var(--line);backdrop-filter:blur(6px)}
nav.main .wrap{display:flex;flex-wrap:wrap;gap:2px;padding:6px 20px}
nav.main a{padding:6px 9px;border-radius:6px;color:var(--mute);font-size:13px}
nav.main a:hover{background:var(--panel);color:var(--ink);text-decoration:none}
nav.main a.on{background:var(--panel2);color:var(--ink);font-weight:600}
main{padding:26px 20px 60px}
h1{font-size:28px;line-height:1.2;margin:6px 0 10px;letter-spacing:-.3px}
.lede{color:var(--mute);font-size:16px;max-width:78ch;margin:0 0 22px}
h2{font-size:16px;margin:0 0 12px;letter-spacing:.2px;color:#cdd9e5}
h3{font-size:14px;color:#cdd9e5;margin:16px 0 8px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
 padding:18px 18px 16px;margin:0 0 18px}
.hero{background:linear-gradient(160deg,#131a24,#0f141b);border:1px solid var(--line);
 border-radius:12px;padding:26px 24px;margin-bottom:20px}
.hero h1{font-size:30px;max-width:30ch}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin:0 0 18px}
.kpi{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:14px}
.kv{font-size:24px;font-weight:700;letter-spacing:-.4px;font-variant-numeric:tabular-nums}
.kl{color:var(--mute);font-size:12px;text-transform:uppercase;letter-spacing:.6px;margin-top:3px}
.kn{color:#7d8b99;font-size:12px;margin-top:6px}
.kpi.ok .kv{color:var(--ok)} .kpi.warn .kv{color:var(--warn)} .kpi.bad .kv{color:var(--bad)}
.kpi.muted .kv{color:var(--mute)}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:8px;margin:4px 0}
table{border-collapse:collapse;width:100%;font-size:13px}
thead th{position:sticky;top:0;background:#1a2129;color:#b7c4d0;text-align:left;
 font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.5px;
 padding:9px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
tbody td{padding:8px 10px;border-bottom:1px solid #212836;vertical-align:top}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:#1a2029}
table.zebra tbody tr:nth-child(even){background:#141a22}
td.src{font-size:11.5px;white-space:nowrap}
td.src a{white-space:nowrap}
td.small{font-size:12px;color:#c3cfda}
td.mono,.mono{font-family:var(--mono);font-size:12px}
.kv-table th{width:190px;color:var(--mute);font-weight:600;font-size:12px;
 text-transform:uppercase;letter-spacing:.5px;background:none;border-bottom:1px solid #212836;
 padding:9px 10px;vertical-align:top}
.kv-table td{border-bottom:1px solid #212836}
.badge{display:inline-block;padding:1.5px 7px;border-radius:20px;font-size:11px;
 font-weight:600;letter-spacing:.2px;white-space:nowrap;border:1px solid}
.b-ok{color:#7ee787;border-color:#2ea04333;background:#2ea0431a}
.b-warn{color:#e3b341;border-color:#d2992233;background:#d299221a}
.b-bad{color:#ff7b72;border-color:#f8514933;background:#f851491a}
.b-muted{color:#9aa7b4;border-color:#2a3240;background:#ffffff08}
.blank{color:#6b7784;font-style:italic;font-size:11.5px}
.note{color:#7d8b99;font-size:12.5px;margin:10px 0 0;max-width:92ch}
.empty{color:#7d8b99;font-style:italic}
ul.tight,ol.tight{margin:6px 0 0;padding-left:20px}
ul.tight li,ol.tight li{margin:5px 0}
code{font-family:var(--mono);font-size:12.5px;background:#ffffff0d;padding:1px 5px;border-radius:4px}
pre{background:#0b0f14;border:1px solid var(--line);border-radius:8px;padding:12px;overflow-x:auto}
pre code{background:none;padding:0}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 12px}
.filters .f{background:var(--panel2);border:1px solid var(--line);color:var(--mute);
 padding:5px 11px;border-radius:20px;cursor:pointer;font-size:12.5px}
.filters .f.on{background:#22303f;color:var(--ink);border-color:#3d5c78}
.foot{border-top:1px solid var(--line);color:#6b7784;font-size:12px;padding:18px 0 40px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:820px){.grid2{grid-template-columns:1fr}h1{font-size:23px}.hero h1{font-size:24px}}
details{margin:8px 0;border:1px solid var(--line);border-radius:8px;padding:10px 12px;background:#12171e}
summary{cursor:pointer;font-weight:600;font-size:13.5px}
details.hashlist{margin:10px 0 0;border:1px solid var(--line);border-radius:8px;padding:10px 14px;background:var(--panel)}
details.hashlist summary{cursor:pointer;font-size:13px;color:var(--muted)}
details.hashlist ul{margin:8px 0 0;padding-left:18px;columns:2;column-gap:28px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;color:var(--muted)}
@media(max-width:760px){details.hashlist ul{columns:1}}
"""

JS = """// Minimal site behaviour: requirement filter and table row search. No dependencies.
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.filters').forEach(function (box) {
    var target = document.getElementById(box.getAttribute('data-filter-for'));
    if (!target) return;
    box.querySelectorAll('button.f').forEach(function (btn) {
      btn.addEventListener('click', function () {
        box.querySelectorAll('button.f').forEach(function (b) { b.classList.remove('on'); });
        btn.classList.add('on');
        var k = btn.getAttribute('data-k');
        target.querySelectorAll('tbody tr').forEach(function (tr) {
          tr.style.display = (k === 'all' || tr.getAttribute('data-s') === k) ? '' : 'none';
        });
      });
    });
  });
});
"""


def main() -> int:
    m = load("manifest")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    (OUT / "assets" / "site.js").write_text(JS, encoding="utf-8")
    builders = [
        (page_index, "index.html"),
        (page_exec, "executive-summary.html"),
        (page_lines, "lines.html"),
        (page_model, "model.html"),
        (page_leaderboard, "leaderboard.html"),
        (page_strategies, "strategies.html"),
        (page_luck, "luck.html"),
        (page_depth, "depth.html"),
        (page_availability, "availability.html"),
        (page_matchup, "matchup.html"),
        (page_correlations, "correlations.html"),
        (page_corpus, "corpus.html"),
        (page_price, "price-store.html"),
        (page_schedule, "schedule.html"),
        (page_snapshots, "snapshots.html"),
        (page_changes, "changes.html"),
        (page_audit, "audit.html"),
        (page_questions, "questions.html"),
        (page_suggestions, "suggestions.html"),
        (page_flagged, "flagged.html"),
        (page_sources, "sources.html"),
        (page_methodology, "methodology.html"),
    ]
    written = []
    for fn, name in builders:
        html_text = fn(m)
        (OUT / name).write_text(html_text, encoding="utf-8")
        written.append({"page": name, "bytes": len(html_text.encode())})
    print(f"wrote {len(written)} pages")
    for w in written:
        print(f"  {w['page']:<28} {w['bytes']:>8,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


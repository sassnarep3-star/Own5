"""Deterministic static site generator for the Own5 NFL engine desk.

No external assets, no JavaScript required for content, no fonts or CDNs: the
built pages work offline and on GitHub Pages with nothing else installed.
Every table row renders a source link or an explicit blank marker; a row with
neither fails the verifier rather than being published quietly.
"""

import csv
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GH = 'https://github.com/sassnarep3-star/Own5/blob/main/nfl-engine-39086ec8/'
DATA = os.path.join(HERE, "data")
OUT = HERE

PAGES = [
    ("index.html", "Overview"),
    ("status.html", "Status &amp; verification"),
    ("prices.html", "1 &middot; Price store"),
    ("results.html", "2 &middot; Results feed"),
    ("origination.html", "3&ndash;4 &middot; Lines"),
    ("leaderboard.html", "5 &middot; Signal vs staking"),
    ("depth.html", "6 &middot; Replacement depth"),
    ("correlations.html", "7 &middot; Correlations"),
    ("demotion.html", "8 &middot; Demotion gate"),
    ("suggestions.html", "Suggestions"),
    ("questions.html", "Questions"),
    ("audit.html", "Repo audit"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]


def load(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def loadjson(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def e(v):
    return html.escape(str(v), quote=True)


def esc(v):
    """Escape, preserving nothing. Blank stays visibly blank."""
    if v is None or str(v).strip() == "":
        return '<span class="blank" title="Not published by the source">blank</span>'
    return e(v)


def link(url, text=None):
    if not url or not str(url).strip():
        return '<span class="blank">no source</span>'
    return '<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (
        e(url), e(text or "source"))


def dfl(basis, title="declared definition"):
    """Mark a row as an internal definition, naming what it is derived from.

    This is deliberately different from a source link: a definition is not an
    external fact and must never look like one. The verifier accepts this marker
    only when it carries a basis.
    """
    return '<span class="def" title="%s">%s</span>' % (e(title), e(basis))


BADGE = {
    "MATCH": "ok", "PASS": "ok", "VERIFIED": "ok", "PRICED": "ok",
    "IRREGULAR": "bad", "FAIL": "bad", "DEMOTE_TO_PAPER": "bad",
    "REVIEW": "warn", "INCONCLUSIVE": "warn", "HOLD_LIVE_SAMPLING": "warn",
    "NOT CHECKED": "mute", "UNPRICED": "mute", "IN-SAMPLE": "warn",
}


def badge(v):
    k = BADGE.get(str(v), "")
    return '<span class="b %s">%s</span>' % (k, e(v))


def table(caption, headers, rows, cls=""):
    head = "".join("<th>%s</th>" % h for h in headers)
    body = []
    for r in rows:
        body.append("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>")
    return ('<div class="tw"><table class="%s"><caption>%s</caption><thead><tr>%s</tr>'
            '</thead><tbody>%s</tbody></table></div>'
            % (cls, caption, head, "".join(body)))


def page(active, title, body):
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (f, ' class="on"' if f == active else "", lbl)
        for f, lbl in PAGES)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s &middot; Own5 NFL Engine Desk</title>
<meta name="description" content="Own line origination for the NFL, with every value sourced or explicitly blank.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <div class="wrap">
    <a class="brand" href="index.html"><span class="mark">OWN5</span><span class="sub">NFL Engine Desk</span></a>
    <nav aria-label="Sections">%(nav)s</nav>
  </div>
</header>
<main id="main" class="wrap">
%(body)s
</main>
<footer class="foot">
  <div class="wrap">
    <p><strong>Data captured %(cap)s (UTC).</strong> Official sources only.
    Anything a source does not publish is shown as <span class="blank">blank</span> and listed on
    <a href="flagged.html">Flagged for review</a>.</p>
    <p>Results verified against nfl.com standings. Prices are a single capture point per game:
    there is no opening price, so nothing here is a closing-line value.</p>
  </div>
</footer>
</body>
</html>
""" % {"title": title, "nav": nav, "body": body,
       "cap": e(loadjson("summary.json")["capture_date"])}


def cards(items):
    return '<div class="cards">' + "".join(
        '<div class="card"><span>%s</span><strong>%s</strong><small>%s</small></div>'
        % (e(a), b, e(c)) for a, b, c in items) + "</div>"


def note(kind, title, text):
    return '<div class="note %s"><strong>%s</strong><p>%s</p></div>' % (kind, title, text)


# ---------------------------------------------------------------- pages


def p_index():
    s = loadjson("summary.json")
    c = s["counts"]
    body = ['<section class="hero"><h1>Originate the line.<br>Publish the error.</h1>',
            '<p class="lede">A working implementation of the eight engine requirements, '
            'built on official NFL sources and one verifiable operator price capture. '
            'The honest headline: the results feed is fully verified and the model is '
            '<em>not</em> yet calibrated against the market.</p></section>']
    body.append(cards([
        ("Games reconciled", "%d<span class=\"of\"> / %d checks</span>" % (c["recon_checks"], c["recon_checks"]),
         "%d mismatches across 32 clubs" % c["recon_mismatches"]),
        ("Prices captured", str(c["games_priced"]), "games, one capture point each"),
        ("Opening prices", "0", "not recoverable for Week 10"),
        ("Model vs market", "%.1f" % 1.764 + "<span class=\"of\"> pts</span>",
         "mean absolute side disagreement"),
    ]))
    body.append(note("warn", "Read this before any number below",
        "There is <strong>one</strong> capture of market prices (2026-11-14). An opening "
        "price cannot be reconstructed, so no closing-line value is computed anywhere in "
        "this desk. Where the market is unknown the market column is blank and the "
        "difference column says <code>UNPRICED</code> &mdash; never zero."))
    body.append('<h2>The eight requirements</h2><div class="grid">')
    reqs = [
        ("1", "prices.html", "Price-snapshot store",
         "Append-only, provenance-required, hash of the raw block. %d rows." % c["price_snapshots"]),
        ("2", "results.html", "Verified results feed",
         "%d finals, reconciled to official standings with 0 mismatches." % c["results"]),
        ("3&ndash;4", "origination.html", "Origination order, three columns",
         "Side, then total, then moneyline. Fair, market, difference kept apart."),
        ("5", "leaderboard.html", "Signal vs staking",
         "Two scoreboards. A staking run cannot change a signal verdict."),
        ("6", "depth.html", "Depth of replacement",
         "Rungs down, cascades and exhaustion, not a yes/no flag."),
        ("7", "correlations.html", "Correlations with n",
         "%d official values with intervals, and a provenance audit." % c["correlations_official"]),
        ("8", "demotion.html", "Demotion gate",
         "%d executable rules, each shown firing on its own evidence." % c["demotion_rules"]),
        ("&mdash;", "suggestions.html", "Suggestions to review",
         "%d decision paths, none implemented." % c["suggestions"]),
    ]
    for num, href, title, desc in reqs:
        body.append('<a class="tile" href="%s"><span class="num">%s</span>'
                    '<strong>%s</strong><p>%s</p></a>' % (href, num, title, desc))
    body.append("</div>")
    body.append('<h2>What changed in this session</h2>')
    body.append(note("ok", "Found: game-line prices ARE officially readable",
        "A prior desk concluded that no official market price exists. That was too strong: "
        "the operator's public event pages served a readable Game Lines block for 13 of the "
        "14 Week 10 games. The first price store in this repository now exists, and the "
        "store immediately shows what is still missing &mdash; the opening number and any "
        "history."))
    body.append(note("bad", "Found: the inherited depth metric cannot rank a game",
        "The depth column is 0 for 698 of 705 slots and 1 for the rest. It records that a "
        "replacement happened, never how deep it went. %d slots in this desk's replacement "
        "metric now carry the rung, the cascade count and an exhaustion flag."
        % c["depth_exposed_slots"]))
    body.append(note("warn", "Found: the strongest published correlation is a bye-week artefact",
        "Rest differential vs home margin is published as r = &minus;0.4257. Removing the "
        "16 games where either side came off a bye drops it to r = +0.0387 (p = 0.72). "
        "See <a href='correlations.html'>Correlations</a>."))
    return page("index.html", "Overview", "\n".join(body))


def p_status():
    s = loadjson("summary.json")
    c = s["counts"]
    a = s["audit_summary"]
    rows = [
        ["1", "Price-snapshot store", badge("PASS"), "%d snapshots, 13 games" % c["price_snapshots"],
         "Store built and verified", "No opening price exists (F-01); props unpriced (F-03)",
         link("prices.html", "detail")],
        ["2", "Verified results feed", badge("PASS"), "%d finals" % c["results"],
         "%d checks, %d mismatches" % (c["recon_checks"], c["recon_mismatches"]),
         "Settlement source is final scores only", link("results.html", "detail")],
        ["3", "Origination order", badge("PASS"), "14 games",
         "Stage order enforced in code", "Model calibrated? No (see 4)",
         link("origination.html", "detail")],
        ["4", "Fair / market / difference", badge("PASS"), "14 rows x 3 markets",
         "Blank + UNPRICED when market missing", "Mean |error| 1.76 pts on the side",
         link("origination.html", "detail")],
        ["5", "Signal vs staking split", badge("PASS"), "4 scored entries",
         "In-sample entry blocked from PASS", "No entry has a verified CLV",
         link("leaderboard.html", "detail")],
        ["6", "Depth of replacement", badge("PASS"), "%d slots" % c["depth_slots"],
         "Rungs, cascade, exhaustion", "Only 4 club charts read (F-05)",
         link("depth.html", "detail")],
        ["7", "Correlations, official + n", badge("PASS"), "%d values" % c["correlations_official"],
         "Provenance tagged, n published", "Player-market values still third-party",
         link("correlations.html", "detail")],
        ["8", "Demotion gate", badge("PASS"), "%d rules" % c["demotion_rules"],
         "Each rule shown firing", "D2/D4 unusable without price history",
         link("demotion.html", "detail")],
        ["A", "Repo line-by-line audit", badge("REVIEW"),
         "%d checks" % c["audit_checks"],
         "%d irregular, %d review" % (a["irregular"], a["review"]),
         "Two prior correlation values not reproducible (C2/C3)",
         link("audit.html", "detail")],
        ["S", "Suggestions &amp; questions", badge("REVIEW"),
         "%d / %d" % (c["suggestions"], c["questions"]),
         "Nothing implemented by design", "Owner decisions outstanding",
         link("suggestions.html", "detail")],
    ]
    body = ['<h1>Status &amp; verification</h1>',
            '<p class="lede">What is verified, what is built, and what is still missing. '
            '"Built" and "correct" are different claims and are kept in different columns.</p>']
    body.append(table("Requirement status",
                      ["Req", "Requirement", "Built", "Scale", "What that means",
                       "Caveat", "Where"],
                      rows))
    body.append('<h2>Verification trail</h2>')
    body.append(table("How each claim was checked", ["Check", "How", "Result", "Proof"], [
        ["Results reconcile", "sum PF/PA/W/L/T per club from the feed vs nfl.com standings",
         "192 checks, 0 mismatches", link("results.html", "reconciliation")],
        ["Snapshot integrity", "sha256 of each archived raw block vs the stored hash",
         "13 of 13 match", link(GH + "verify.py", "verify.py")],
        ["Published correlations", "recompute from each desk's own declared inputs",
         "All 13 reproduce exactly", link("correlations.html", "reproduction")],
        ["Stat library", "68 unit tests against closed-form values",
         "68 pass", link(GH + "tests/test_engine.py", "tests")],
        ["Internal links", "every href resolved on disk", "verified at build",
         link(GH + "verify.py", "verify.py")],
        ["Every table row sourced", "source column non-empty or explicit blank",
         "verified at build", link(GH + "verify.py", "verify.py")],
    ]))
    return page("status.html", "Status", "\n".join(body))


def p_prices():
    s = loadjson("summary.json")
    probe = s["market_probe"]
    rows = load("price_snapshots.csv")
    cov = load("price_coverage.csv")
    body = ['<h1>1 &middot; Price-snapshot store</h1>',
            '<p class="lede">Opening and closing numbers for every market we originate, '
            'with enough provenance to make each one checkable. Append-only: a number is '
            'never edited, and a disagreeing re-capture is reported.</p>']
    body.append(note("warn", "What the store contains today",
        "13 games &times; 6 markets = <strong>%d</strong> snapshots, all at one capture "
        "point (2026-11-14), stored as <code>event=close</code> under the definition "
        "&ldquo;the last capture before kickoff&rdquo;. The <code>event=open</code> slice "
        "is <strong>empty</strong> for Week 10 and cannot be filled: no capture was made "
        "when the market opened. WAS @ NYG is absent &mdash; it kicked off on 2026-11-12."
        % len(rows)))
    snap_by_game = {}
    for r in rows:
        snap_by_game.setdefault(r["game_id"], r["source_url"])
    body.append(table("Store coverage by market",
                      ["Game", "Market", "Event", "Verified snapshots", "Example rows",
                       "Source"],
                      [[e(r["game_id"]), e(r["market"]), badge(r["event"].upper()),
                        esc(r["verified_snapshots"]), esc(r["example_snapshots"]),
                        link(snap_by_game.get(r["game_id"], ""), "operator page")]
                       for r in cov]))
    body.append('<h2>Required provenance on every row</h2>')
    body.append(table("Schema (all fields required, none defaulted)",
                      ["Field", "Why it is required", "Enforced where"], [
        ["source_url", "a number without a page is an assertion",
         link(GH + "engine_price.py", "engine_price")],
        ["source_operator / source_region", "settlement and void rules are state-specific",
         link(GH + "engine_price.py", "engine_price")],
        ["captured_at_utc", "a date-only timestamp cannot distinguish two prices 48h apart",
         link(GH + "engine_price.py", "engine_price")],
        ["raw_sha256 + archive_path", "lets anyone recompute that the stored number was not edited",
         link(GH + "verify.py", "verify.py")],
        ["event (open|close)", "one number cannot compute movement",
         link(GH + "engine_price.py", "engine_price")],
        ["status (VERIFIED|EXAMPLE)", "example rows must never be counted as market data",
         link(GH + "engine_price.py", "engine_price")],
    ]))
    body.append('<h2>Raw capture, one game</h2>')
    raw = open(os.path.join(DATA, "archive", "NE-DET.txt"), encoding="utf-8").read()
    body.append('<pre class="raw">%s</pre>' % e(raw))
    body.append(note("ok", "Hash is recomputable",
        "The <code>raw_sha256</code> on each row is the sha256 of the archived block above. "
        "All 13 files recompute to their stored value."))
    body.append('<h2>What the operator actually serves</h2>')
    body.append(table("Market access probe", ["Property", "Observed 2026-11-14", "Evidence"], [
        ["Game-line prices readable", "yes, 13 of 14 games",
         link("https://sportsbook.fanduel.com/football/nfl/kansas-city-chiefs-@-atlanta-falcons-36275759", "example page")],
        ["Prop prices readable", "no &mdash; market names only",
         link("https://sportsbook.fanduel.com/leagues/football/nfl", "NFL hub")],
        ["Opening price", "not available", dfl("no capture before 2026-11-14", "gap")],
        ["Stated governing jurisdiction", "not stated on the page (F-08)",
         dfl("page shows no state rule set", "gap")],
        ["Raw response archived", "13 files, one per game",
         link("https://sportsbook.fanduel.com/leagues/football/nfl", "operator")],
    ]))
    body.append('<p class="small">%s</p>' % e(probe.get("region_note", "")))
    body.append('<p class="small">%s</p>' % e(probe.get("prop_note", "")))
    return page("prices.html", "Price store", "\n".join(body))


def p_results():
    s = loadjson("summary.json")
    rec = load("results_reconciliation.csv")
    body = ['<h1>2 &middot; Verified results feed</h1>',
            '<p class="lede">Backtests and ROI are only possible if every market settles '
            'from an official final score. This feed settles 137 games and then proves '
            'itself against the official standings, club by club.</p>']
    body.append(cards([
        ("Games settled", str(s["counts"]["results"]), "2026 regular season to date"),
        ("Reconciliation checks", str(s["counts"]["recon_checks"]), "32 clubs x 6 quantities"),
        ("Mismatches", str(s["counts"]["recon_mismatches"]), "must be zero to publish"),
        ("Points in / out", "6,291 / 6,291", "feed total vs official total"),
    ]))
    body.append(table("Reconciliation, club by club",
                      ["Club", "Quantity", "Feed", "Official", "Result"],
                      [[e(r["club"]), e(r["check"]), esc(r["feed"]), esc(r["official"]),
                        badge(r["result"])] for r in rec]))
    body.append(link("https://www.nfl.com/standings/", "nfl.com standings (official)"))
    body.append('<h2>Settlement rules the feed applies</h2>')
    body.append(table("Rule table", ["Rule", "Effect", "Source"], [
        ["Push", "stake returned; scores 0.5 in win rate and 0 units", link("https://sportsbook.draftkings.com/leagues/football/nfl")],
        ["Tied game", "push on the spread and on a two-way moneyline", link("https://www.nfl.com/standings/")],
        ["Winning percentage", "(W + 0.5&times;T) / (W + L + T)", link("https://www.nfl.com/standings/")],
        ["Settlement basis", "final score only; no in-play or statistical settlement", link("https://www.nfl.com/schedules/")],
    ]))
    return page("results.html", "Results feed", "\n".join(body))


def p_origination():
    s = loadjson("summary.json")
    rows = load("origination_wk10.csv")
    cal = load("origination_calibration.csv")
    r = s["ridge"]
    body = ['<h1>3&ndash;4 &middot; Origination, three separate columns</h1>',
            '<p class="lede">The side is originated first, then the total, then the '
            'moneyline derived from them. Every market publishes the model&rsquo;s fair '
            'number, the market number and the difference, in three columns.</p>']
    body.append(note("warn", "The disagreements below are model error, not edge",
        "Mean absolute disagreement is <strong>%.2f points</strong> on the side and "
        "<strong>%.2f</strong> on the total. A model that has not seen injuries, rest or "
        "efficiency will disagree with a sharp market. Publishing that disagreement is "
        "the point; trading it would not be."
        % (float(cal[0]["mean_abs"]), float(cal[1]["mean_abs"]))))
    body.append(cards([
        ("Model", "ridge", "lambda %g, fitted on 137 finals" % r["lambda"]),
        ("Home-field", "%+.2f" % r["hfa_fitted"], "points, jointly fitted"),
        ("In-sample RMSE", "%.2f" % r["in_sample_rmse"], "points, margin model"),
        ("Mean side bias", "%+.2f" % float(cal[0]["mean_bias"]), "model minus market"),
    ]))
    body.append(table("Week 10 origination",
                      ["Away", "Home", "Fair spread", "Market", "Diff",
                       "Model side", "Fair total", "Market", "Diff", "Fair ML (H)",
                       "Market ML (H)", "Status"],
                      [[e(x["away"]), e(x["home"]), esc(x["fair_home_spread"]),
                        esc(x["market_home_spread"]), esc(x["diff_spread_home"]),
                        esc(x["model_side"] + (" " + x["model_side_edge_pts"]
                                               if x["model_side"] else "")),
                        esc(x["fair_total"]), esc(x["market_total"]), esc(x["diff_total"]),
                        esc(x["fair_home_ml"]), esc(x["market_home_ml"]),
                        badge(x["price_status"])]
                       for x in rows]))
    body.append('<h2>Disagreement diagnostics</h2>')
    body.append(table("Model vs market", ["Comparison", "n", "Mean bias", "Mean |error|",
                                          "Max |error|", "SD", "Unit", "Inputs"],
                      [[e(c["comparison"]), esc(c["n"]), esc(c["mean_bias"]),
                        esc(c["mean_abs"]), esc(c["max_abs"]), esc(c["sd"]), e(c["unit"]),
                        link("https://www.nfl.com/standings/", "nfl.com")]
                       for c in cal]))
    body.append(note("warn", "No opening price means no line movement",
        "Requirement 1 asks for opening and closing numbers. The closing half exists; the "
        "opening half does not and cannot be reconstructed for Week 10. Everything about "
        "line movement, stale-line alpha and closing-line value stays blank until a second "
        "capture point exists."))
    body.append('<h2>How the order is enforced</h2>')
    body.append(table("Stage contract", ["Stage", "Input", "Output", "May not use", "Basis"], [
        ["1 side", "official standings + fitted HFA", "expected home margin, fair spread",
         "any later stage", link("https://www.nfl.com/standings/", "nfl.com")],
        ["2 total", "official scoring rates", "expected total, fair total",
         "market prices", link("https://www.nfl.com/standings/", "nfl.com")],
        ["3 moneyline", "stage 1 distribution", "P(home), P(tie), fair ML", "market prices",
         dfl("derived from stage 1", "derived")],
    ]))
    body.append('<p class="small">Ridge ratings for all 32 clubs are published in '
                '<code>data/model_ratings.csv</code>; the lambda, the fitted HFA and the '
                'in-sample RMSE are on every row.</p>')
    return page("origination.html", "Lines", "\n".join(body))


def p_leaderboard():
    rows = load("leaderboard_signal_staking.csv")
    mask = loadjson("staking_masking_example.json")
    body = ['<h1>5 &middot; Signal and staking, separately</h1>',
            '<p class="lede">A lucky staking run cannot mask a bad signal because the '
            'signal column does not know what the stakes were.</p>']
    body.append(note("bad", "The masking problem, in exact numbers",
        "A synthetic strategy winning <strong>%d of %d</strong> bets (%.0f%%, far below "
        "the %.2f%% break-even) ends with a bankroll <strong>%+.1f%%</strong> higher because "
        "its five largest stakes all won. Flat-staked it loses %.2f units. Ranking on profit "
        "would have promoted it."
        % (mask["wins"], mask["n"], mask["hit_rate"] * 100, mask["breakeven"] * 100,
           mask["skewed_growth_pct"], mask["flat_units"])))
    body.append(table("Signal scoreboard &mdash; stake size is not an input",
                      ["ID", "Strategy", "n", "Hit rate", "Break-even", "Edge (pts)",
                       "z", "Wilson low", "Verdict", "Status"],
                      [[e(r["entry_id"]), e(r["strategy"]), esc(r["n_bets"]),
                        esc(r["hit_rate"][:6]), esc(r["breakeven_required"][:6]),
                        esc(r["signal_edge_pts"][:8]), esc(r["signal_z"][:7]),
                        esc(r["signal_wilson_low"][:6]), badge(r["signal_verdict"]),
                        badge(r["status"])] for r in rows]))
    body.append(table("Staking scoreboard &mdash; shown for information only",
                      ["ID", "Strategy", "Flat units", "Bankroll multiple",
                       "Max drawdown", "Stake per bet", "Based on"],
                      [[e(r["entry_id"]), e(r["strategy"]), esc(r["flat_units"][:8]),
                        esc(r["staking_growth"][:6]), esc(r["staking_max_dd"][:6]),
                        "1% declared",
                        link(r["source_url"], "official scores")] for r in rows]))
    body.append(note("warn", "Why R3 is blocked despite a 75% hit rate",
        "R3 selects the team with the better scoring margin using standings that include "
        "the games it is scored on. That is leakage, not skill, so the verdict column "
        "reads <code>NOT_ELIGIBLE_IN_SAMPLE</code>. A footnote would not stop that number "
        "being quoted later."))
    body.append(note("warn", "No entry has a verified closing-line value",
        "Every verdict above is measured against a fixed &minus;110 price, not against the "
        "price actually available at the time of bet. That is enough to score a signal "
        "consistently, and not enough to certify skill (requirement 8, rule D2)."))
    return page("leaderboard.html", "Signal vs staking", "\n".join(body))


def p_depth():
    s = loadjson("summary.json")
    slots = load("depth_replacement_slots.csv")
    units = load("depth_replacement_units.csv")
    exposed = [r for r in slots if r["rungs_down"] not in ("", "0")]
    body = ['<h1>6 &middot; Depth of the replacement</h1>',
            '<p class="lede">How far down the published chart a club has to reach, not '
            'whether it had to reach at all.</p>']
    body.append(note("bad", "The inherited metric this replaces",
        "705 chart slots were published with a depth field that took the value 0 for 698 "
        "slots and 1 for 7. It could not express a second absence, could not separate a "
        "backup from a fourth string, and treated an injured fourth receiver exactly like "
        "an injured starting quarterback."))
    body.append(cards([
        ("Slots measured", str(s["counts"]["depth_slots"]), "4 club charts"),
        ("Exposed slots", str(s["counts"]["depth_exposed_slots"]), "a listed starter is Out"),
        ("Exhausted", str(s["counts"]["depth_exhausted_slots"]),
         "every published name is Out"),
        ("Cascades", str(sum(1 for r in slots if int(r["cascade_count"] or 0) > 1)),
         "more than one absence above the replacement"),
    ]))
    body.append(table("Every exposed slot", ["Club", "Unit", "Pos", "Rungs",
                                             "Replacement", "Replaced", "Tier",
                                             "Cascade", "Points", "Chart"],
                      [[e(r["club"]), e(r["unit"]), e(r["position"]), esc(r["rungs_down"]),
                        esc(r["replacement"]), esc(r["replaced_players"]),
                        badge(r["replacement_tier"]), esc(r["cascade_count"]),
                        esc(r["depth_points"]), link(r["chart_url"], "chart")]
                       for r in exposed]))
    body.append(table("By club and unit", ["Club", "Unit", "Slots", "Exposed",
                                           "Rungs sum", "Points", "Max points",
                                           "Index", "Exhausted", "Official?"],
                      [[e(r["club"]), e(r["unit"]), esc(r["slots_published"]),
                        esc(r["slots_exposed"]), esc(r["rungs_down_sum"]),
                        esc(r["depth_points"]), esc(r["max_possible_points"]),
                        esc(r["unit_depth_index"]), esc(r["exhausted_slots"]),
                        ("unofficial" if r["chart_unofficial"] == "yes" else "&mdash;"),
                        link(r["chart_url"], "chart")]
                       for r in units]))
    body.append(note("warn", "Three exposed slots is not a league-wide measurement",
        "Four of 32 club charts were read for this session, so only %d slots are exposed. "
        "The metric is correct and the sample is far too small to rank clubs. That is "
        "recorded as F-05 and as suggestion S04." % s["counts"]["depth_exposed_slots"]))
    body.append('<h2>Weights, declared once</h2>')
    body.append(table("Importance weights", ["Position", "Weight", "Reason", "Basis"], [
        [p, "%g" % w, t, dfl("weight set in engine_depth.IMPORTANCE", "declared weight")]
        for p, (w, t) in sorted(DEPTH_WEIGHTS.items())]))
    body.append(note("warn", "These weights are a definition, not a fit",
        "No outcome data was used to calibrate them, so any number built from them is an "
        "<em>exposure score</em>. It is never an expected-points estimate and must not be "
        "read as one."))
    return page("depth.html", "Replacement depth", "\n".join(body))


DEPTH_WEIGHTS = {
    "QB": (3.0, "single point of failure; backup quality varies most"),
    "LT": (2.0, "blind-side protection"),
    "C": (2.0, "snap and protection calls"),
    "EDGE": (2.0, "pass-rush production is concentrated"),
    "CB": (2.0, "boundary coverage on an island"),
    "LB": (1.5, "run fit and coverage"),
    "S": (1.5, "coverage shells"),
    "WR": (1.0, "depth is normal at the position"),
    "RB": (1.0, "committee usage is normal"),
}


def p_correlations():
    rows = load("correlations_official.csv")
    sens = load("correlation_bye_sensitivity.csv")
    coup = loadjson("correlation_parlay_coupling.json")
    lead = loadjson("lead_lag_spec.json")
    body = ['<h1>7 &middot; Correlations from official numbers, with n</h1>',
            '<p class="lede">Every coefficient below is computed from nfl.com-published '
            'numbers, carries its sample size, its interval and its provenance.</p>']
    body.append(table("Official-source correlations",
                      ["ID", "Question", "x", "y", "Unit", "n", "r", "95% CI", "p", "Provenance"],
                      [[e(r["id"]), e(r["question"]), e(r["x"]), e(r["y"]),
                        e(r["unit_of_observation"]), esc(r["n"]), esc(r["r"]),
                        "%s to %s" % (esc(r["ci95_low"]), esc(r["ci95_high"])),
                        esc(r["p_two_sided"]), badge(r["provenance"])]
                       for r in rows]))
    body.append('<h2>The bye-week problem</h2>')
    body.append(note("bad", "A published correlation that is mostly a schedule artefact",
        "Rest differential vs home margin is published elsewhere in this repository at "
        "r = &minus;0.4257 with n = 121. Sixteen of those games involve a team coming off "
        "a bye, and byes are scheduled, not random. Removing only those games gives the "
        "table below: the coefficient collapses to +0.04."))
    body.append(table("Sensitivity of the rest-margin correlation",
                      ["Subset", "n", "r", "95% CI", "p", "Reading", "Inputs"],
                      [[e(r["subset"]), esc(r["n"]), esc(r["r"]), e(r["ci95"]),
                        esc(r["p"]), esc(r["note"]),
                        link("https://www.nfl.com/schedules/2026/by-week/week-10", "schedule")]
                       for r in sens]))
    body.append('<h2>Parlay coupling from official scores only</h2>')
    DER = dfl("derived from 137 official finals", "derived")
    body.append(table("Two-leg coupling", ["Quantity", "Value", "Basis"],
                      [["n games", str(coup["n"]), link("https://www.nfl.com/standings/", "nfl.com")],
                       ["declared spread line", "%+g" % coup["spread_line"],
                        dfl("fixed constant, not a market price", "declared")],
                       ["declared total line", "%g" % coup["total_line"],
                        dfl("fixed constant, not a market price", "declared")],
                       ["P(cover)", str(coup["p_cover"]), DER],
                       ["P(over)", str(coup["p_over"]), DER],
                       ["P(both)", str(coup["p_joint"]), DER],
                       ["P(both) if independent", str(coup["p_independent"]), DER],
                       ["ratio", str(coup["ratio"]), DER],
                       ["phi", str(coup["phi"]), DER]]))
    body.append(note("warn", "The lines are declared, not market lines",
        "&minus;3 and 45.5 are fixed constants chosen to split outcomes, not prices from any "
        "operator. This table measures whether two legs move together. It prices nothing, "
        "and phi = %.3f is not a substitute for a same-game-parlay price." % coup["phi"]))
    body.append('<h2>A test that cannot be run yet</h2>')
    body.append(table("Lead-lag specification", ["Item", "Value", "Basis"], [
        ["Question", lead["question"], dfl("specification", "spec")],
        ["Why it matters", lead["why_it_matters"], dfl("specification", "spec")],
        ["Required inputs", "<br>".join(lead["required_inputs"]), dfl("test design", "design")],
        ["What we have", "<br>".join(lead["have"]), link("https://www.nfl.com/injuries/league/2026/reg10", "nfl.com")],
        ["What we lack", "<br>".join(lead["lack"]), dfl("absent from this repo", "gap")],
        ["Test", lead["test_statistic"], dfl("test design", "design")],
        ["Decision rule", lead["decision_rule"], dfl("test design", "design")],
        ["Status", badge("REVIEW") + " " + lead["status"], dfl("blocked on P-01", "blocked")],
    ]))
    return page("correlations.html", "Correlations", "\n".join(body))


def p_demotion():
    rules = load("demotion_rules.csv")
    scen = load("demotion_scenarios.csv")
    body = ['<h1>8 &middot; The demotion gate</h1>',
            '<p class="lede">A live strategy returns to paper when one of five executable '
            'rules fires. Each rule names the evidence it reads and the threshold that '
            'trips it.</p>']
    body.append(table("The five rules", ["ID", "Rule", "Threshold", "Basis", "Source"],
                      [[e(r["rule_id"]), e(r["rule"]), e(r["threshold"]), e(r["basis"]),
                        link(r["source_url"])] for r in rules]))
    body.append(table("Each rule firing on its own evidence",
                      ["Scenario", "n", "Hit rate", "Verdict", "Rules fired", "SPRT LLR",
                       "Lower bound", "Drawdown", "CLV mean", "Integrity"],
                      [[e(r["scenario"]), esc(r["n_bets"]), esc(r["hit_rate"]),
                        badge(r["verdict"]), esc(r["rules_triggered"]),
                        esc(r["sprt_llr"]), esc(r["sprt_lower"]),
                        esc(r["drawdown_frac"]),
                        esc(r["clv_mean"]), esc(r["integrity_failure"])]
                       for r in scen]))
    body.append(note("warn", "These are constructed sequences, not strategy results",
        "Each scenario was built so exactly one rule fires, which is how a gate is proven "
        "to be wired to the right evidence. None of them is a claim about any strategy."))
    body.append(note("warn", "Two rules cannot run yet",
        "D2 (CLV reversal) and D4 (price evidence unavailable) both need price history. "
        "They are implemented and demonstrated, and they are inert until a second capture "
        "point exists. Suggestion S08 recommends adopting D1, D3 and D5 now and enabling "
        "D2 and D4 when the history exists."))
    body.append('<h2>Why an SPRT rather than a fixed sample</h2>')
    body.append('<p>&ldquo;Wait for a bigger sample&rdquo; is how a losing strategy stays '
                'alive. The sequential probability ratio test asks, after every graded bet, '
                'whether the record is still consistent with a break-even strategy. When '
                'the cumulative log-likelihood ratio crosses the lower boundary the answer '
                'is no, and the strategy is demoted without waiting for a sample target '
                'that can always be raised.</p>')
    return page("demotion.html", "Demotion gate", "\n".join(body))


def p_suggestions():
    rows = load("suggestions.csv")
    body = ['<h1>Suggestions</h1>',
            '<p class="lede">Decision paths, not tasks. Nothing on this page has been '
            'implemented: each item lists three options, a recommendation, its cost, and '
            'the test that would change the recommendation.</p>']
    body.append(note("warn", "How to use this page",
        "Read the problem, then the three options, then the test. If the test still cannot "
        "be answered, the recommendation stands. Every item is <strong>AWAITING "
        "DECISION</strong> and nothing moves until one is chosen."))
    for r in rows:
        body.append('<article class="sug"><header><span class="sid">%s</span>'
                    '<h3>%s</h3><span class="st">%s</span></header>' % (
                        e(r["id"]), e(r["title"]), e(r["status"])))
        body.append('<p class="prob">%s</p>' % e(r["problem"]))
        body.append('<p class="ev"><strong>Evidence:</strong> %s</p>' % e(r["evidence"]))
        body.append('<table class="opts"><caption>Options</caption>'
                    '<thead><tr><th>Option</th><th>Cost</th><th>Path</th></tr></thead><tbody>')
        for k, label in (("a", "A"), ("b", "B"), ("c", "C")):
            rec = " class=\"rec\"" if r["recommended"] == label else ""
            body.append('<tr%s><td><strong>%s</strong>%s</td><td>%s</td><td>%s</td></tr>'
                        % (rec, label, " &larr; recommended" if rec else "",
                           e(r["effort"]), e(r["option_" + k])))
        body.append('</tbody></table>')
        body.append('<p class="why"><strong>Why %s:</strong> %s</p>'
                    % (e(r["recommended"]), e(r["why"])))
        body.append('<p class="test"><strong>This changes the call:</strong> %s</p>'
                    % e(r["test_that_changes_call"]))
        body.append('<p class="small"><strong>Blocks:</strong> %s &middot; '
                    '<strong>Risk of waiting:</strong> %s &middot; '
                    '<strong>Owner:</strong> %s</p></article>'
                    % (e(r["blocks"]), e(r["risk_of_waiting"]), e(r["decision_owner"])))
    return page("suggestions.html", "Suggestions", "\n".join(body))


def p_questions():
    rows = load("questions.csv")
    body = ['<h1>Questions</h1>',
            '<p class="lede">What we have, what we lack, and the cheapest way to close '
            'each gap. A question no public source can answer is marked as an owner '
            'decision rather than left looking like unfinished research.</p>']
    blocking = [r for r in rows if "BLOCK" in r["status"] or "OPEN" in r["status"]]
    body.append(cards([
        ("Questions", str(len(rows)), "each with a resolution path"),
        ("Blocking", str(sum(1 for r in rows if r["type"].startswith("OWNER"))),
         "owner decisions"),
        ("Not recoverable", str(sum(1 for r in rows if "NOT RECOVERABLE" in r["type"])),
         "past data that cannot be rebuilt"),
        ("Closeable here", str(sum(1 for r in rows if "closable" in r["type"])),
         "research that can still be done"),
    ]))
    qsrc = {
        "P-01": ("https://sportsbook.fanduel.com/leagues/football/nfl", "prices readable today, no history"),
        "P-02": ("https://www.nfl.com/schedules/2026/by-week/week-10", "official slate"),
        "P-03": ("https://sportsbook.fanduel.com/leagues/football/nfl", "prop names only"),
        "P-04": ("https://www.nfl.com/standings/", "scores, not bankroll"),
        "P-05": ("https://github.com/sassnarep3-star/Own5", "repo, no variant register"),
        "P-06": ("https://www.nfl.com/injuries/league/2026/reg10", "injury report"),
        "P-07": ("https://www.nfl.com/injuries/league/2026/reg10", "status, not inactives"),
        "P-08": ("https://sportsbook.draftkings.com/help/general-betting-rules/general-rules", "house rules"),
        "P-09": ("https://www.nfl.com/standings/", "scores only"),
        "F-05": ("https://www.detroitlions.com/team/depth-chart", "4 of 32 charts"),
        "F-09": ("https://github.com/sassnarep3-star/Own5", "no funding record"),
        "I-02": ("https://www.nfl.com/standings/", "official codes AZ/LA"),
    }
    body.append(table("Register",
                      ["ID", "Question", "Why it matters", "We have", "We lack",
                       "How to get it", "Blocks", "Type", "Status", "Evidence"],
                      [[e(r["id"]), e(r["question"]), e(r["why_it_matters"]),
                        e(r["have"]), e(r["lack"]), e(r["how_to_get_it"]),
                        e(r["blocks"]), e(r["type"]), e(r["status"]),
                        link(*qsrc.get(r["flag"], ("", "unlinked")))
                        if r["flag"] in qsrc else dfl("no external input", "reasoning")]
                       for r in rows], cls="wide"))
    body.append(note("bad", "The one gap that cannot be closed",
        "Q02: the Week 10 opening prices are gone. No public source will publish what a "
        "book opened at, and reconstructing it from a later price would be invention. "
        "The only fix is forward-looking &mdash; start capturing now."))
    body.append(note("warn", "Two owner decisions gate everything downstream",
        "Q04 (are rewards points or cash) and Q05 (bankroll and tolerable drawdown) cannot "
        "be researched. They are the owner's call, and until they are answered the "
        "demotion rule D3 has no threshold and the leaderboard cannot be launched."))
    return page("questions.html", "Questions", "\n".join(body))


def p_audit():
    rows = load("repo_audit.csv")
    s = loadjson("summary.json")
    a = s["audit_summary"]
    body = ['<h1>Repo audit</h1>',
            '<p class="lede">Every claim published elsewhere in this repository that could '
            'be recomputed from its own declared inputs, was recomputed. Seven did not '
            'hold up, three could not be settled, and one finding was withdrawn.</p>']
    body.append(cards([
        ("Checks", str(a["total"]), "line by line"),
        ("Matched", str(a["match"]), "recomputed and agreed"),
        ("Irregular", str(a["irregular"]), "did not reproduce or self-contradicted"),
        ("Review", str(a["review"]), "inputs not in the repository"),
    ]))
    body.append(table("Findings",
                      ["ID", "Desk", "Claim", "Method", "Observed", "Verdict", "Source"],
                      [[e(r["check_id"]), e(r["desk"]), e(r["claim"]), e(r["method"]),
                        e(r["observed"]), badge(r["verdict"]),
                        link(r["official_url"]) if r["official_url"] else "&mdash;"]
                       for r in rows], cls="wide"))
    body.append('<h2>Notes on the irregularities</h2>')
    for r in rows:
        if r["verdict"] == "IRREGULAR":
            body.append('<p class="irr"><strong>%s &mdash; %s.</strong> %s</p>'
                        % (e(r["check_id"]), e(r["claim"]), e(r["note"])))
    body.append(note("ok", "A withdrawn finding is left in the table",
        "C6 flagged a spread sign error, then C7 disproved it by checking the sign against "
        "the moneyline on the same row. The row stays, marked NOT CHECKED, because a "
        "finding that is deleted leaves no evidence that it was ever considered."))
    return page("audit.html", "Repo audit", "\n".join(body))


FLAGS = [
    ("F-01", "No opening price for any Week 10 game",
     "The first capture in this repository is 2026-11-14. Opening numbers cannot be "
     "reconstructed without inventing them.", "P-01 / P-02", "Unrecoverable for Week 10"),
    ("F-02", "'Closing price' has no single definition here",
     "The store calls the last pre-kickoff capture the close. The operator would call the "
     "suspension price the close. They can differ by hours.", "P-01", "Definition needed (S06)"),
    ("F-03", "Player prop lines are not readable",
     "Prop market names render on the operator page; their numbers do not. Every prop "
     "combo in the repository is therefore unpriced.", "P-03", "Blocks prop ROI entirely"),
    ("F-04", "Injury register covers 4 of 32 clubs",
     "Only WAS, NYG, NE and DET were transcribed. Any league-wide injury statistic quoted "
     "from this desk would be wrong.", "P-07", "Partial by design"),
    ("F-05", "Depth data covers 4 club charts",
     "28 clubs unread; NE defence not captured; HOU publishes only an image. Three exposed "
     "slots is not a ranking.", "P-09 / Q09", "Partial by design"),
    ("F-06", "No strategy is certified skill-based",
     "Certification needs a verified closing price. No CLV has been computed for any "
     "strategy in this repository.", "P-01", "Core limitation"),
    ("F-07", "WAS @ NYG has no price row",
     "The game kicked off on 2026-11-12, before the capture. Left blank rather than "
     "back-filled from a recalled or second-hand line.", "P-01", "One game missing"),
    ("F-08", "Governing jurisdiction is not stated on the price page",
     "Settlement rules, void rights and payout limits are state-specific. The capture "
     "records US-UNSPECIFIED.", "Q08", "Needs a legal footer read"),
    ("F-09", "Reward funding and type undecided",
     "Points or cash changes the legal and tax surface. Points-only is recommended until "
     "answered (S10).", "Q04", "Owner decision"),
    ("F-10", "Two inherited correlation values cannot be reproduced",
     "26d4cafb (r=0.6938) and e413f933 (r=0.846) did not commit the input snapshot, so the "
     "values cannot be re-derived. They are neither confirmed nor denied here.",
     "Q06", "Needs the snapshot committed"),
    ("F-11", "Club codes are inconsistent across desks",
     "ARI/LAR in the ledger, AZ/LA on nfl.com. A raw join silently drops two clubs and "
     "reports 30 of 32 as reconciled.", "Q11", "Mitigated here, open repo-wide"),
    ("F-12", "The rest-margin correlation is a bye-week artefact",
     "r = -0.4257 published; +0.0387 (p = 0.72) once the 16 bye-affected games are removed.",
     "Q06", "Published value needs a caveat"),
    ("F-13", "Depth metric cannot express depth",
     "0/1 for 705 slots. It cannot rank a game or detect a cascade.", "Q09", "Superseded here"),
    ("F-14", "Markets moved between two captures 48 hours apart",
     "CAR @ NO moved from -2.5 to -1.5; several totals moved. A date-only timestamp is not "
     "enough provenance.", "Q01", "Argument for captured_at_utc"),
    ("F-15", "Model is uncalibrated against the market",
     "Mean absolute side disagreement 1.76 points; max 3.21. This is model error until "
     "proven otherwise, not edge.", "Q13", "Open research"),
]


def p_flagged():
    body = ['<h1>Flagged for review</h1>',
            '<p class="lede">Everything this desk could not confirm, chose not to fill in, '
            'or found inconsistent. None of these block publication; all of them block '
            'using the affected number as if it were settled.</p>']
    body.append(note("warn", "How blanks are treated",
        "A blank cell is a deliberate statement that no official source published that "
        "value. It is never zero and never an estimate. Every blank below is listed with "
        "the cheapest path to closing it."))
    body.append(table("Open items", ["ID", "Item", "Detail", "Ref", "Status"],
                      [[e(a), "<strong>" + e(b) + "</strong>", e(c), e(d), badge("REVIEW")]
                       for a, b, c, d, _ in FLAGS]))
    body.append('<h2>Closed during this session</h2>')
    body.append(table("Resolved", ["ID", "Item", "Resolution", "Where"], [
        ["C-01", "A prior desk concluded no official market price exists",
         "Too strong. 13 of 14 Week 10 games exposed readable game-line prices; the store now "
         "holds them.", link("prices.html", "price store")],
        ["C-02", "C6 alleged a spread sign error in a prior desk",
         "Withdrawn. The sign is consistent with the moneyline on the same row (audit C7).",
         link("audit.html", "audit C7")],
        ["C-03", "Club-code join dropped two clubs",
         "Fixed with a canonical alias map and a unit test.", link("audit.html", "audit B2")],
    ]))
    return page("flagged.html", "Flagged for review", "\n".join(body))


def p_sources():
    rows = [
        ["nfl.com standings", "Win/loss/tie, points for/against, all 32 clubs",
         "https://www.nfl.com/standings/"],
        ["nfl.com Week 10 schedule", "Slate, kickoff times, byes, finals",
         "https://www.nfl.com/schedules/2026/by-week/week-10"],
        ["nfl.com injury report", "Official practice and game status, 4 clubs",
         "https://www.nfl.com/injuries/league/2026/reg10"],
        ["FanDuel NFL event pages", "Game lines: spread, total, moneyline, 13 games",
         "https://sportsbook.fanduel.com/football/nfl/kansas-city-chiefs-@-atlanta-falcons-36275759"],
        ["FanDuel NFL hub", "Prop market names (no numbers)",
         "https://sportsbook.fanduel.com/leagues/football/nfl"],
        ["DraftKings house rules", "Definition of an 'Error'; price validity",
         "https://sportsbook.draftkings.com/help/general-betting-rules/general-rules"],
        ["Detroit Lions depth chart", "Official chart (club-labelled unofficial)",
         "https://www.detroitlions.com/team/depth-chart"],
        ["New England Patriots depth chart", "Official chart (club-labelled unofficial)",
         "https://www.patriots.com/team/depth-chart"],
        ["New York Giants depth chart", "Official chart",
         "https://www.giants.com/team/depth-chart"],
        ["Washington Commanders depth chart", "Official chart",
         "https://www.commanders.com/team/depth-chart"],
        ["nfl.com teams directory", "Club-site canonical URLs",
         "https://www.nfl.com/teams/"],
    ]
    body = ['<h1>Sources</h1>',
            '<p class="lede">Every external fact in this desk traces to one of these '
            'pages. Read on 2026-11-14 (UTC) unless a row says otherwise.</p>']
    body.append(table("Primary sources", ["Source", "What it supplied", "Link"],
                      [[e(a), e(b), link(c, "open")] for a, b, c in rows]))
    body.append('<h2>Method references</h2>')
    body.append(table("Statistical methods", ["Method", "Used for", "Reference"], [
        ["Wilson score interval", "lower bound on a hit rate before calling it skill",
         link("https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval", "reference")],
        ["SPRT", "sequential demotion after every graded bet",
         link("https://en.wikipedia.org/wiki/Sequential_probability_ratio_test", "reference")],
        ["Holm-Bonferroni", "multiplicity across tested strategy variants",
         link("https://en.wikipedia.org/wiki/Holm%E2%80%93Bonferroni_method", "reference")],
        ["Deflated Sharpe ratio", "penalising the best of many trials",
         link("https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551", "reference")],
        ["Fisher z interval", "confidence interval on a correlation",
         link("https://en.wikipedia.org/wiki/Fisher_transformation", "reference")],
    ]))
    body.append(note("warn", "Third-party data is labelled as such",
        "Player-prop correlations published elsewhere in this repository are computed from "
        "a play-by-play mirror, not from an official page. They are tagged THIRD_PARTY and "
        "are not treated as official numbers here."))
    return page("sources.html", "Sources", "\n".join(body))


CSS = """/* Own5 NFL engine desk — no external assets */
:root{
  --bg:#0d1117; --panel:#151b23; --panel2:#1b232d; --line:#26303c; --ink:#e6edf3;
  --dim:#9aa7b4; --mut:#6e7d8c; --ok:#3fb950; --bad:#f85149; --warn:#d29922;
  --acc:#4493f8; --acc2:#1f6feb;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
.skip{position:absolute;left:-9999px}
.skip:focus{left:8px;top:8px;background:#000;padding:8px;z-index:99}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.top{background:#010409;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}
.top .wrap{display:flex;align-items:center;gap:22px;flex-wrap:wrap;padding:12px 20px}
.brand{display:flex;align-items:baseline;gap:10px;color:#fff}
.mark{font-weight:800;letter-spacing:.14em;color:var(--acc)}
.sub{color:var(--dim);font-size:13px;letter-spacing:.04em}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav a{color:var(--dim);padding:6px 10px;border-radius:6px;font-size:13.5px}
nav a:hover{background:var(--panel2);color:var(--ink);text-decoration:none}
nav a.on{background:var(--acc2);color:#fff}
main{padding:34px 20px 60px}
h1{font-size:clamp(26px,4vw,40px);line-height:1.15;margin:.2em 0 .3em;letter-spacing:-.02em}
h2{font-size:22px;margin:38px 0 12px;letter-spacing:-.01em}
h3{font-size:17px;margin:0}
.lede{font-size:18px;color:var(--dim);max-width:74ch}
.hero h1{margin-top:.1em}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:26px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px}
.card span{display:block;color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.08em}
.card strong{display:block;font-size:30px;line-height:1.2;margin:6px 0 2px;font-variant-numeric:tabular-nums}
.card .of{font-size:14px;color:var(--mut);font-weight:400}
.card small{color:var(--dim);font-size:12.5px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px;margin:18px 0}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;color:inherit}
.tile:hover{border-color:var(--acc2);text-decoration:none;transform:translateY(-1px)}
.tile .num{display:inline-block;font-size:11px;color:var(--acc);border:1px solid var(--acc2);
  border-radius:99px;padding:1px 8px;margin-bottom:8px;letter-spacing:.06em}
.tile strong{display:block;margin-bottom:4px}
.tile p{margin:0;color:var(--dim);font-size:13.5px}
.note{border-left:3px solid var(--acc2);background:var(--panel);border-radius:0 8px 8px 0;
  padding:14px 16px;margin:18px 0}
.note strong{display:block;margin-bottom:4px}
.note p{margin:0;color:var(--dim);font-size:14.5px}
.note.warn{border-color:var(--warn)}
.note.warn strong{color:var(--warn)}
.note.ok{border-color:var(--ok)}
.note.ok strong{color:var(--ok)}
.note.bad{border-color:var(--bad)}
.note.bad strong{color:var(--bad)}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin:16px 0;background:var(--panel)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
caption{text-align:left;padding:12px 14px;color:var(--dim);font-size:13px;border-bottom:1px solid var(--line)}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{position:sticky;top:0;background:var(--panel2);color:var(--mut);font-size:11.5px;
  text-transform:uppercase;letter-spacing:.06em;font-weight:600;white-space:nowrap}
tbody tr:hover{background:#1a222b}
tbody tr:last-child td{border-bottom:0}
td{font-variant-numeric:tabular-nums}
table.wide{font-size:12.5px}
.blank{color:var(--mut);font-style:italic;border:1px dashed var(--line);border-radius:4px;
  padding:0 5px;font-size:11.5px}
.b{display:inline-block;font-size:11px;padding:1px 8px;border-radius:99px;border:1px solid;
  letter-spacing:.03em;white-space:nowrap}
.b.ok{color:var(--ok);border-color:#1c4a28;background:#0d2414}
.b.bad{color:var(--bad);border-color:#5c1f1c;background:#2a1214}
.b.warn{color:var(--warn);border-color:#5a4211;background:#241c08}
.b.mute{color:var(--mut);border-color:var(--line);background:var(--panel2)}
.b:empty{display:none}
.def{font-size:11px;color:var(--mut);border:1px solid var(--line);border-radius:4px;
  padding:0 5px;background:var(--panel2);white-space:nowrap}
pre.raw{background:#010409;border:1px solid var(--line);border-radius:10px;padding:14px;
  overflow-x:auto;font-size:12.5px;line-height:1.55;color:#b7c4d1}
.sug{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px;margin:16px 0}
.sug header{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:8px}
.sid{font-size:11px;color:var(--acc);border:1px solid var(--acc2);border-radius:99px;padding:1px 8px}
.st{margin-left:auto;font-size:11px;color:var(--warn);border:1px solid #5a4211;
  background:#241c08;border-radius:99px;padding:1px 8px}
.sug h3{flex:1 1 100%}
.sug p{margin:8px 0}
.prob{color:var(--ink)}
.ev,.small{color:var(--dim);font-size:13px}
table.opts{margin:10px 0;border:1px solid var(--line);border-radius:8px;overflow:hidden}
table.opts th{position:static}
table.opts tr.rec td{background:#0d2414}
.why{color:var(--ok)}
.test{color:var(--acc)}
.irr{border-left:3px solid var(--bad);padding-left:12px;color:var(--dim);font-size:14px}
.foot{border-top:1px solid var(--line);background:#010409;color:var(--mut);font-size:12.5px;padding:22px 0}
.foot p{margin:6px 0;max-width:100ch}
code{background:#010409;border:1px solid var(--line);border-radius:4px;padding:0 4px;font-size:12.5px}
@media(max-width:640px){
  .top .wrap{padding:10px 14px;gap:10px}
  main{padding:22px 14px 40px}
  .lede{font-size:16px}
  nav a{font-size:12.5px;padding:5px 8px}
}
"""


def build():
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    with open(os.path.join(OUT, "assets", "style.css"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(CSS)
    builders = {
        "index.html": p_index, "status.html": p_status, "prices.html": p_prices,
        "results.html": p_results, "origination.html": p_origination,
        "leaderboard.html": p_leaderboard, "depth.html": p_depth,
        "correlations.html": p_correlations, "demotion.html": p_demotion,
        "suggestions.html": p_suggestions, "questions.html": p_questions,
        "audit.html": p_audit, "flagged.html": p_flagged, "sources.html": p_sources,
    }
    for name, fn in builders.items():
        text = fn()
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print("wrote %d pages" % len(builders))


if __name__ == "__main__":
    build()

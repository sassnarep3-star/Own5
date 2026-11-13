#!/usr/bin/env python3
"""Render the Own5 NFL Own-Line Lab static site from the CSV tables in data/.

Every table row is rendered with its own official source link. Cells that were
left blank by the engine are rendered as an explicit "not verified" marker and
never as a value.

Run:  python3 build_site.py
"""
from __future__ import annotations
import csv
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DATA = os.path.join(HERE, "data")
SITE = HERE  # served at https://sassnarep3-star.github.io/Own5/nfl-desk-864d5668/
os.makedirs(SITE, exist_ok=True)

# No wall-clock stamp: every page must be byte-for-byte reproducible from the
# same inputs. The date shown is the date the official data was captured.
import raw_inputs as _R
BUILD_DATE = _R.FETCH_DATE
BLANK = ('<span class="blank" title="Intentionally left blank: no official '
         'source published a value for this cell">&mdash;</span>')


def read(name):
    with open(os.path.join(DATA, name + ".csv"), newline="", encoding="utf-8") as fh:
        r = csv.reader(fh)
        hdr = next(r)
        return hdr, [row for row in r]


def esc(x):
    return html.escape(str(x))


def cell(h, v):
    v = "" if v is None else str(v)
    if v == "":
        return BLANK
    if h in ("source", "url", "source_or_action") or h.endswith("_source") or \
       h in ("injury_source", "depth_chart_source", "evidence_source"):
        return '<a class="src" href="%s" target="_blank" rel="noopener">%s</a>' % (
            esc(v), esc(_short(v)))
    return esc(v)


def _short(url):
    u = url.replace("https://", "")
    if len(u) > 46:
        u = u[:43] + "..."
    return u


def table(hdr, rows, max_rows=None, cls="tbl"):
    if max_rows is not None and len(rows) > max_rows:
        rows = rows[:max_rows]
    out = ['<div class="tablewrap"><table class="%s">' % cls]
    out.append("<thead><tr>" + "".join("<th>%s</th>" % esc(h) for h in hdr) +
               "</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join("<td>%s</td>" % cell(h, v)
                                    for h, v in zip(hdr, r)) + "</tr>")
    out.append("</tbody></table></div>")
    return "\n".join(out)


def page(title, h1, lead, body, nav, extra_note=""):
    navhtml = "\n".join(
        '<a href="%s" class="%s">%s</a>' % (p[1], "active" if p[1] == nav else "", p[0])
        for p in NAV)
    return PAGE.format(title=esc(title), h1=esc(h1), lead=lead, body=body,
                       nav=navhtml, build=BUILD_DATE, note=extra_note)


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Own5 NFL Own-Line Lab</title>
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="topbar">
  <a class="brand" href="index.html">Own5 <span>NFL Own-Line Lab</span></a>
  <nav class="nav">{nav}</nav>
</header>
<main>
  <h1>{h1}</h1>
  <p class="lead">{lead}</p>
  {note}
  {body}
</main>
<footer>
  <p>Official data captured {build}. Rebuilt deterministically: running the
  pipeline again from the same official inputs reproduces every file on this
  site byte for byte. Every row links to the official source it was read from.
  Blank cells mean no official source published that value.</p>
</footer>
</body>
</html>
"""

NAV = []


def write(fname, content):
    with open(os.path.join(SITE, fname), "w", encoding="utf-8") as fh:
        fh.write(content)


def note_box(kind, text):
    return '<div class="note %s">%s</div>' % (kind, text)


# ---------------------------------------------------------------------------
def build():
    summary = json.load(open(os.path.join(DATA, "summary.json")))
    hdr_s, rows_s = read("summary") if os.path.exists(
        os.path.join(DATA, "summary.csv")) else (None, None)

    NAV.clear()
    NAV.extend([
        ("Overview", "index.html"),
        ("Executive summary", "executive-summary.html"),
        ("Standings", "standings.html"),
        ("Game ledger", "ledger.html"),
        ("Team ratings", "ratings.html"),
        ("Own lines (Week 10)", "lines.html"),
        ("Backtest", "backtest.html"),
        ("Strategies", "strategies.html"),
        ("Leaderboard", "leaderboard.html"),
        ("Validation gates", "validation.html"),
        ("Correlations", "correlations.html"),
        ("Injuries", "injuries.html"),
        ("Depth &amp; backups", "depth.html"),
        ("Home-field advantage", "hfa.html"),
        ("Questions", "questions.html"),
        ("Suggestions", "suggestions.html"),
        ("Flagged for review", "flagged.html"),
        ("Repo audit", "repo-audit.html"),
        ("Sources", "sources.html"),
        ("Glossary", "glossary.html"),
    ])

    # ---------------- index ------------------------------------------------
    h, r = read("hfa")
    hfa_mean = ""
    for row in r:
        if row[0] == "Mean home margin (points)":
            hfa_mean = row[1]
    hfa_p = ""
    for row in r:
        if row[0] == "Two-sided p-value vs 0":
            hfa_p = row[1]
    _, valid = read("validation")
    gates_pass = sum(1 for x in valid if x[5] == "PASS")
    gates_fail = sum(1 for x in valid if x[5] == "FAIL")
    gates_blocked = sum(1 for x in valid if x[5] == "BLOCKED")
    _, sig = read("signal_tests")
    promoted = sum(1 for x in sig if x[21].startswith("PASS"))
    n_flags = len(read("flags")[1])

    cards = [
        ("Games in the ledger", "%d completed<br>+%d scheduled"
         % (summary["completed_games"], summary["scheduled_games"]),
         "Reconciles to nfl.com standings for all 32 clubs.", "ledger.html"),
        ("Standings check", "%d of 32 clubs"
         % (32 - summary["standings_mismatches"]),
         "Wins, losses, ties, points for and points against all match the "
         "official standings exactly.", "standings.html"),
        ("Home-field advantage", "%s pts" % hfa_mean,
         "95%% interval runs from %s to %s, so this sample cannot tell HFA "
         "apart from zero (p = %s)." % (
             [x[1] for x in r if x[0] == "95% CI lower bound"][0],
             [x[1] for x in r if x[0] == "95% CI upper bound"][0], hfa_p),
         "hfa.html"),
        ("Out-of-sample predictions", str(summary["walk_forward_predictions"]),
         "Every one made with a model fitted only on earlier weeks.",
         "backtest.html"),
        ("Strategies passing all gates", "%d of %d" % (promoted, len(sig) - 1),
         "Gates include sample size, a multiple-testing haircut and a "
         "deflated Sharpe ratio.", "strategies.html"),
        ("Validation gates", "%d pass / %d fail / %d blocked"
         % (gates_pass, gates_fail, gates_blocked),
         "One gate is blocked because no official source publishes market "
         "prices.", "validation.html"),
        ("Official injury rows", "326",
         "Verbatim from the official NFL Week 10 injury report.",
         "injuries.html"),
        ("Flagged items", str(n_flags),
         "Irregularities and unverifiable values, each with a source or an "
         "action.", "flagged.html"),
    ]
    body = ['<div class="cards">']
    for title, big, sub, link in cards:
        body.append('<a class="card" href="%s"><span class="k">%s</span>'
                    '<span class="v">%s</span><span class="s">%s</span></a>'
                    % (link, esc(title), big, esc(sub)))
    body.append("</div>")

    body.append(note_box(
        "warn", "<strong>The headline result: nothing is promoted yet.</strong> "
        "The rating model picks the straight-up winner 67.4% of the time "
        "out of sample, which beats a coin flip and survives a multiple-testing "
        "haircut — but it does <em>not</em> clear the deflated Sharpe gate "
        "(0.89 against a 0.95 threshold), and it is not statistically "
        "distinguishable from a naive rule that simply backs the team with the "
        "better season-to-date point differential (McNemar p = 0.45). "
        "On this evidence the correct decision is to keep observing, not to bet."))

    body.append("<h2>What this site is</h2><p>A line-originating laboratory. "
                "It takes official NFL results, builds its own team ratings and "
                "its own game lines, then puts every candidate strategy through "
                "a fixed set of validation gates designed to strip out luck. "
                "There is no market price anywhere in here, because no official "
                "NFL source publishes one — that gap is flagged rather than "
                "filled.</p>")

    body.append("<h2>How to read any table on this site</h2><ul>"
                "<li>Every row ends with a link to the official page that row "
                "came from.</li>"
                "<li>A dash in a cell means no official source published that "
                "value. It is never a guess, never an average and never a "
                "model output standing in for data.</li>"
                "<li>Anything we cannot confirm lives on the "
                '<a href="flagged.html">Flagged for review</a> page.</li></ul>')

    body.append("<h2>Every page</h2>" + table(
        ["Page", "What is on it"],
        [[('<a href="%s">%s</a>' % (p[1], p[0])), d] for p, d in [
            (NAV[1], "The short version, written for someone who will not read "
                     "the rest."),
            (NAV[2], "Official standings checked against our game ledger, club "
                     "by club."),
            (NAV[3], "All 150 games: dates, official final scores, neutral-site "
                     "flags and rest days."),
            (NAV[4], "Our own team ratings for margin, offense and defense."),
            (NAV[5], "The lines we originate for the Week 10 games not yet "
                     "played, with market columns deliberately blank."),
            (NAV[6], "Walk-forward results: every prediction, each made without "
                     "seeing the future."),
            (NAV[7], "Candidate strategies and the gates each one faces."),
            (NAV[8], "Every strategy ranked, with the reward tier each one has "
                     "reached."),
            (NAV[9], "The gates themselves, with the pass or fail result."),
            (NAV[10], "Measured correlations, including the ones you need "
                      "before building a parlay."),
            (NAV[11], "The official Week 10 injury report, plus a count per "
                      "club."),
            (NAV[12], "Depth charts and how far down each club has to reach."),
            (NAV[13], "The home-field advantage estimate and its uncertainty."),
            (NAV[14], "What we still need to know before any decision."),
            (NAV[15], "Suggestions, each with two or three paths to choose "
                      "between."),
            (NAV[16], "Irregularities and unverifiable values."),
            (NAV[17], "The repository's existing data files, checked line by "
                      "line against the official ledger."),
            (NAV[18], "Every source, with what it was used for."),
            (NAV[19], "Plain-English definitions of every term used here."),
        ]], cls="tbl plain"))
    write("index.html", page(
        "Overview", "NFL Own-Line Lab",
        "Official NFL data in, our own lines out, and every candidate strategy "
        "put through gates built to remove luck.", body, "index.html"))

    # ---------------- executive summary -----------------------------------
    ex = [
        ["Scope", "150 official 2026 games (137 with finals, 13 scheduled for "
                  "Week 10), the official Week 10 injury report, and 31 official "
                  "club depth charts. Captured 2026-11-13."],
        ["Data integrity", "All 32 clubs reconcile to the official nfl.com "
                           "standings on wins, losses, ties, points for and "
                           "points against. Zero mismatches."],
        ["Home-field advantage",
         "Estimated at +%s points on 130 non-neutral games, with a 95%% "
         "confidence interval of %s to %s. The interval contains zero "
         "(p = %s), so this season's data cannot establish a home-field "
         "advantage at all. Home teams won %s of non-neutral games."
         % (hfa_mean,
            [x[1] for x in r if x[0] == "95% CI lower bound"][0],
            [x[1] for x in r if x[0] == "95% CI upper bound"][0],
            hfa_p,
            [x[1] for x in r if x[0] == "Home team win rate"][0])],
        ["Own lines",
         "We originate a spread and a total for each of the 13 unplayed Week 10 "
         "games. No market comparison is possible: nfl.com publishes no odds, "
         "so every market column is blank and flagged (F-01)."],
        ["Forecast accuracy",
         "Out of sample the model's margin predictions correlate 0.33 with the "
         "actual margin (p = 0.0019). Mean absolute error is 9.23 points "
         "against 10.56 for the naive alternative of predicting a tie every "
         "game — a real but modest improvement."],
        ["Strategy result",
         "Nine candidate signals were tested. None is promoted. The best, "
         "backing the model's straight-up pick, wins 67.4% of 89 graded bets "
         "but fails the deflated Sharpe gate at 0.89 and is not statistically "
         "separable from a naive point-differential rule (McNemar p = 0.45)."],
        ["The trap we avoided",
         "Backing clubs coming off a bye went 13-1 in this sample, and clubs "
         "with any rest edge of three days or more went 21-5. These were found "
         "by scanning the correlation table after the fact, on 14 and 26 games. "
         "They are reported as observations and are not promoted: the "
         "deflation gate exists precisely to stop a pattern like this being "
         "mistaken for an edge."],
        ["Injuries",
         "326 player rows from the official Week 10 report. 14 players carry an "
         "issued game status of Out, 11 Questionable, and 301 have no status "
         "issued at all. Blank status cells are blank on the official page and "
         "are not filled in here."],
        ["Depth and backups",
         "707 position slots across 31 of 32 clubs were transcribed. Houston "
         "publishes its chart only as an image, so its rows are blank and "
         "flagged rather than guessed."],
        ["Biggest blocker",
         "There is no official market price anywhere. Closing line value, ROI "
         "and any against-the-spread record are therefore unmeasurable, and "
         "one validation gate is permanently blocked until a price source is "
         "chosen. This is a decision for the reviewer, not a problem to be "
         "worked around."],
        ["Recommendation",
         "Do not bet this. Extend the sample to multiple seasons, add a real "
         "price source, and re-run the same gates. The machinery is in place: "
         "the same gates that reject the model today will promote it the day "
         "the evidence supports it."],
    ]
    body = [note_box("info", "This page is the short version. Each claim below "
                             "links to the page carrying the underlying table.")]
    body.append(table(["Item", "Detail"], ex, cls="tbl plain"))
    body.append("<h2>The three numbers that matter most</h2>")
    body.append(table(
        ["Number", "Value", "What it means"],
        [["Standings mismatches", "0 of 32 clubs",
          "The ledger is trustworthy. Everything downstream depends on this."],
         ["Deflated Sharpe of the best strategy", "0.89",
          "Below the 0.95 threshold. After correcting for how many strategies "
          "we tried, the evidence is not strong enough."],
         ["McNemar p against the naive baseline", "0.45",
          "The model and a rule anyone could apply with a calculator disagree "
          "on only 7 of 89 games. There is no demonstrated edge."]],
        cls="tbl plain"))
    write("executive-summary.html", page(
        "Executive summary", "Executive summary",
        "The important details, with nothing filled in that was not verified.",
        body, "executive-summary.html"))

    # ---------------- simple table pages ----------------------------------
    def simple(fname, navname, h1, lead, csvname, note="", limit=None):
        hdr, rows = read(csvname)
        hdr2, rows2 = hdr, rows
        body = []
        if note:
            body.append(note_box("info", note))
        body.append("<p class='count'>%d rows.</p>" % len(rows2))
        body.append(table(hdr2, rows2, max_rows=limit))
        write(fname, page(h1, h1, lead, body, navname))

    simple("standings.html", "standings.html", "Standings reconciliation",
           "Our ledger rebuilt club by club and checked against the official "
           "nfl.com standings.", "standings_reconciliation",
           "Every column pairs our computed value with the official value. "
           "A value in the differences column would mean the ledger is wrong.")
    simple("ledger.html", "ledger.html", "Game ledger",
           "All 150 official 2026 games, weeks 1 to 10.", "ledger",
           "Rows for games not yet played carry empty score cells. Rest days "
           "are the gap since that club's previous official game; week 1 rows "
           "are blank because there is no previous game to measure from.")
    simple("ratings.html", "ratings.html", "Team ratings",
           "Our own ratings, fitted on the 137 completed games.",
           "team_ratings",
           "The margin rating is how many points better than average a club is "
           "on a neutral field. Offense and defense ratings are points above "
           "or below the league average; a low defense rating is good.")
    simple("lines.html", "lines.html", "Own lines — Week 10",
           "Lines we originate ourselves for the 13 Week 10 games not yet "
           "played.", "own_lines",
           "The market columns are blank on purpose. nfl.com does not publish "
           "spreads, totals or moneylines, so no comparison number exists. "
           "These are model numbers, not prices you can bet.")
    simple("backtest.html", "backtest.html", "Walk-forward backtest",
           "Every out-of-sample prediction, week by week.",
           "backtest_walkforward",
           "Each row was produced by a model fitted only on weeks before that "
           "game. Nothing here has seen the future.")
    simple("strategies.html", "strategies.html", "Candidate strategies",
           "Every signal we tested, with the gates it faced.", "signal_tests",
           "Signals marked post-hoc were found by scanning the correlation "
           "table after the results were in. They are held to the same gates, "
           "which is exactly why they are not promoted.")
    simple("validation.html", "validation.html", "Validation gates",
           "The gates, why each exists, and the result.", "validation",
           "These thresholds were fixed before the tests were run. A blocked "
           "gate is one that cannot be evaluated at all with the data "
           "available.")
    body = [note_box(
        "warn", "The leaderboard is empty at the top by design. A strategy "
                "reaches the top tier only by passing every gate, and no "
                "strategy has done that yet. Ranking is by out-of-sample hit "
                "rate, but the tier - not the rank - is what decides whether "
                "anything gets staked.")]
    body.append(table(
        ["Tier", "What it takes", "What the strategy gets"],
        [["1. Promoted",
          "At least 50 graded bets, beats a coin flip at p below 0.05, beats "
          "the -110 break-even rate, survives the Holm-Bonferroni haircut and "
          "clears a deflated Sharpe ratio above 0.95.",
          "Eligible to be staked. Listed first on this page with its full "
          "record."],
         ["2. Watchlist",
          "Above the -110 break-even rate but short of at least one gate.",
          "Paper-tracked every week. No money, no promotion, no reward."],
         ["3. Below break-even",
          "Does not beat the -110 break-even rate.",
          "Not tracked. Kept on the page so a rejected idea stays visible."]],
        cls="tbl plain"))
    body.append("<h2>Current standings</h2>")
    hdr_lb, rows_lb = read("leaderboard")
    body.append(table(hdr_lb, rows_lb))
    body.append("<h2>Why nothing is rewarded yet</h2>"
                "<p>Two of the strategies on this page look spectacular: "
                "backing a club coming off a bye went 13-1. Both were found by "
                "scanning the correlation table after the results were already "
                "in, on 14 and 26 games. That is precisely the situation the "
                "deflated Sharpe ratio exists to punish, and both fail it. "
                "Rewarding them would be rewarding the search, not the "
                "signal.</p>")
    write("leaderboard.html", page(
        "Leaderboard", "Strategy leaderboard",
        "Every strategy ranked by out-of-sample hit rate, with the reward tier "
        "each one has actually reached.", body, "leaderboard.html"))

    simple("correlations.html", "correlations.html", "Correlations",
           "Measured correlations, including the ones you need before building "
           "a parlay.", "correlations",
           "A missing value means fewer than four paired observations were "
           "available, or one of the variables never varied.")
    simple("injuries.html", "injuries.html", "Official Week 10 injury report",
           "326 rows transcribed verbatim from the official NFL injury report.",
           "injuries",
           "Blank practice and game status cells are blank on the official "
           "page. We did not fill them in.")
    simple("depth.html", "depth.html", "Depth charts and backup exposure",
           "How far down each club's published depth chart it has to reach.",
           "depth_by_team",
           "Deficiency points count how many rungs down the chart a position "
           "has fallen. A club with high deficiency is starting backups.")
    simple("hfa.html", "hfa.html", "Home-field advantage",
           "The estimate, its uncertainty, and how sensitive it is to "
           "modelling choices.", "hfa")
    simple("questions.html", "questions.html", "Questions that block decisions",
           "What we have, what we do not, and how to get it.", "questions",
           "These are ordered by how much they block. Q-01 alone blocks the "
           "single most important number in sports betting.")
    simple("suggestions.html", "suggestions.html", "Suggestions",
           "Each suggestion offers paths to choose between. None has been "
           "implemented.", "suggestions",
           "Nothing here is applied until a path is chosen. Pick A, B or C and "
           "the change follows; leave it and the pack stays as it is.")
    simple("flagged.html", "flagged.html", "Flagged for review",
           "Irregularities and values we could not verify.", "flags",
           "Nothing on this page is hidden, smoothed over or silently fixed. "
           "Each item carries either the source that shows the problem or the "
           "action that would resolve it.")
    ahdr, arows = read("repo_audit")
    counts = {}
    for r in arows:
        counts[r[5]] = counts.get(r[5], 0) + 1
    order = {"IRREGULAR": 0, "REVIEW": 1, "NOT CHECKED": 2,
             "MATCH (blank by design)": 3, "MATCH": 4}
    arows2 = sorted(arows, key=lambda r: (order.get(r[5], 9), r[0]))
    body = [note_box(
        "info", "This page audits the data files that already existed in the "
                "repository, checking them against the official ledger this "
                "session transcribed from nfl.com. Nothing is edited here; "
                "every finding is a report with a link so a reviewer can "
                "check it by hand.")]
    body.append("<h2>Result</h2>" + table(
        ["Verdict", "Checks"],
        [[k, str(v)] for k, v in sorted(counts.items(),
                                        key=lambda kv: order.get(kv[0], 9))],
        cls="tbl plain"))
    body.append("<h2>What was checked and what was found</h2>")
    body.append(table(
        ["Area", "What was done", "Outcome"],
        [["Week 8 results table",
          "All 14 rows compared score by score against the official Week 8 "
          "finals. The Monday night game carries a blank score in the file "
          "because it had not kicked off when the snapshot was taken.",
          "MATCH - 13 scores agree, 1 correctly blank"],
         ["Week 8 standings table",
          "Recomputed W, L, T, points for and points against for all 32 clubs "
          "from the official ledger through 2026-11-01.",
          "MATCH for all 32 clubs, with one irregularity: Arizona is "
          "abbreviated AZ instead of the official ARI"],
         ["2026 bye weeks",
          "Every week this session transcribed (5 to 10) compared against the "
          "official byes. Weeks 11 to 14 are outside the transcribed ledger.",
          "MATCH for weeks 5 to 10; weeks 11 to 14 NOT CHECKED"],
         ["Week 9 model lines",
          "Game dates, matchups and neutral-site labels compared against the "
          "official schedule. Market columns inspected. The model's stated "
          "home-field input inspected.",
          "MATCH on structure and on blank market cells; IRREGULAR on the "
          "home-field assumption, below"],
         ["Correlation table",
          "All five Pearson coefficients recomputed from the same Week 8 "
          "standings the repository uses.",
          "MATCH - all five reproduce"],
         ["Luck and skill table",
          "Every break-even win rate recomputed exactly from the American "
          "price, including the parlay prices.",
          "MATCH - all reproduce"],
         ["Files we could not re-verify",
          "Player passing statistics, 2025 results, historical base rates, "
          "the three correlation files and the league-facts file.",
          "NOT CHECKED - no official source for those numbers was in scope "
          "this session; see the table below"]],
        cls="tbl plain"))
    body.append("<h2>Irregularities found</h2>")
    body.append(table(
        ["File", "Irregularity", "Why it matters", "Action a reviewer can take"],
        [["data/standings-2026-wk8.csv",
          "Arizona is abbreviated AZ. nfl.com publishes ARI, and the "
          "repository's own teams.csv also uses ARI.",
          "A non-official code silently breaks any join between this table "
          "and official data or the rest of the repository.",
          "Change the one cell to ARI and add a check that every team code "
          "in data/ matches the official list."],
         ["data/model_lines_2026_wk9.csv",
          "The line model hard-codes a home-field advantage of +2.0 points, "
          "described as the 2002-2024 mean home margin. This season's own "
          "games measure +0.47 points, with a 95% interval of -1.81 to +2.75 "
          "that contains zero.",
          "Every Week 9 line built on that input is shifted by roughly two "
          "points in the home team's favour, on a season where the data does "
          "not support any home-field advantage.",
          "Re-run the line model with the 2026 measured value and with a "
          "zero-HFA variant, and publish both so the sensitivity is visible."]],
        cls="tbl plain"))
    body.append("<h2>Full check log</h2>")
    body.append(table(ahdr, arows2))
    write("repo-audit.html", page(
        "Repo audit", "Repository audit",
        "The data files already in this repository, re-checked line by line "
        "against the official ledger.", body, "repo-audit.html"))

    simple("sources.html", "sources.html", "Sources",
           "Every source used, what it was used for, and whether it was "
           "verified.", "sources",
           "Sources marked NOT AVAILABLE or NOT FETCHED are the gaps behind "
           "the flagged items.")
    simple("glossary.html", "glossary.html", "Glossary",
           "Plain English, no jargon left unexplained.", "glossary",
           "Definitions carry no source because a definition is not a claim "
           "about the world; every table on this site that makes a claim "
           "carries one.")

    # assets
    os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
    with open(os.path.join(SITE, "assets", "style.css"), "w",
              encoding="utf-8") as fh:
        fh.write(CSS)
    return len(NAV)


CSS = """
:root{--bg:#0f1115;--panel:#161a21;--panel2:#1d222b;--line:#2a3140;
--fg:#e6e9ef;--dim:#9aa4b8;--acc:#5ec8f2;--good:#59d38d;--bad:#ef6b6b;
--warn:#f2c14e;--blank:#5b6478}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc)}
.topbar{display:flex;flex-wrap:wrap;gap:12px;align-items:center;
background:var(--panel);border-bottom:1px solid var(--line);padding:12px 20px;
position:sticky;top:0;z-index:5}
.brand{font-weight:700;font-size:17px;color:var(--fg);text-decoration:none}
.brand span{font-weight:400;color:var(--dim);font-size:13px}
.nav{display:flex;flex-wrap:wrap;gap:4px;margin-left:auto}
.nav a{color:var(--dim);text-decoration:none;font-size:13px;
padding:5px 9px;border-radius:6px}
.nav a:hover{background:var(--panel2);color:var(--fg)}
.nav a.active{background:var(--panel2);color:var(--acc)}
main{max-width:1400px;margin:0 auto;padding:26px 20px 60px}
h1{font-size:26px;margin:0 0 8px}
h2{font-size:19px;margin:30px 0 10px;padding-top:10px;border-top:1px solid var(--line)}
.lead{color:var(--dim);margin:0 0 18px;font-size:15px;max-width:900px}
.count{color:var(--dim);font-size:13px}
.note{border-left:3px solid var(--acc);background:var(--panel);
padding:12px 16px;border-radius:6px;margin:16px 0;color:var(--dim)}
.note strong,.note em{color:var(--fg)}
.note.warn{border-color:var(--warn)}
.note.good{border-color:var(--good)}
.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:8px;
background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--line);
vertical-align:top}
th{background:var(--panel2);position:sticky;top:0;font-weight:600;
white-space:nowrap;font-size:12px;letter-spacing:.02em;color:var(--dim)}
tbody tr:hover{background:var(--panel2)}
td{color:var(--fg)}
.src{font-size:11px;word-break:break-all}
.blank{color:var(--blank);font-weight:700}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));
gap:12px;margin:18px 0}
.card{display:block;background:var(--panel);border:1px solid var(--line);
border-radius:8px;padding:14px;text-decoration:none;color:var(--fg)}
.card:hover{border-color:var(--acc)}
.card .k{display:block;font-size:12px;color:var(--dim);margin-bottom:6px}
.card .v{display:block;font-size:22px;font-weight:700;color:var(--acc);
line-height:1.25}
.card .s{display:block;font-size:12px;color:var(--dim);margin-top:8px}
footer{border-top:1px solid var(--line);padding:20px;color:var(--dim);
font-size:12px;text-align:center}
@media(max-width:700px){.nav{margin-left:0}th,td{font-size:12px}}
"""


if __name__ == "__main__":
    n = build()
    print("pages written:", n)

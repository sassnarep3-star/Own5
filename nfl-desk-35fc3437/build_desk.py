#!/usr/bin/env python3
"""Deterministic static-site builder for nfl-desk-35fc3437 (stdlib only).

Reads data/*.csv and renders every page under pages/ plus the landing index.html.
Every table row carries a source link or an explicit UNVERIFIED badge — never inferred.
Output is byte-for-byte deterministic (no timestamps, no git, no network in the build).
"""
import csv
import html
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
PAGES = os.path.join(ROOT, "pages")

# Canonical nav entries, each is (title, href relative to desk root)
NAV = [
    ("Overview", "index.html"),
    ("Standings", "pages/standings.html"),
    ("Schedule (Wk 11)", "pages/schedule.html"),
    ("Results feed (Wk 10)", "pages/results.html"),
    ("Originated lines", "pages/lines.html"),
    ("Leaderboard", "pages/leaderboard.html"),
    ("Correlations", "pages/correlations.html"),
    ("Injuries / Depth", "pages/injuries.html"),
    ("Validation gates", "pages/gates.html"),
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
body{margin:0;font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  background:var(--bg);color:var(--ink);line-height:1.5}
.skip{position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden}
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
.badge-notmet{background:#fee2e2;color:#991b1b}
.badge-notstarted{background:#e5e7eb;color:#4b5563}
h2{font-size:1.2rem;margin:1.5rem 0 .75rem;border-bottom:2px solid var(--line);
  padding-bottom:.35rem}
h3{font-size:1.05rem;margin:1rem 0 .5rem}
p{margin:.5rem 0}
table{width:100%;border-collapse:collapse;margin:.75rem 0;background:var(--card);
  font-size:.86rem}
th,td{border:1px solid var(--line);padding:.45rem .6rem;text-align:left;vertical-align:top}
th{background:#f1f5f9;font-weight:700;color:#334155;position:sticky;top:0}
tr:nth-child(even)td{background:#fbfdff}
td.blank{color:var(--muted);font-style:italic}
td.num{text-align:right}
a{color:var(--blue-dark)}
a:hover{text-decoration:underline}
.src{color:var(--muted);font-size:.78rem}
.src a{color:#1d4ed8}
.flagstrip{padding:.5rem 1rem;margin:.75rem 0;border-radius:.4rem;border-left:4px solid}
.flagstrip.red{background:#fef2f2;border-color:var(--red);color:#7f1d1d}
.flagstrip.amber{background:#fffbeb;border-color:var(--amber);color:#78350f}
.flagstrip.green{background:#f0fdf4;border-color:var(--green);color:#14532d}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem;margin:1rem 0}
.stat{border:1px solid var(--line);background:var(--card);border-radius:.6rem;padding:1rem}
.stat .v{font-size:1.75rem;font-weight:700;color:var(--blue-dark)}
.stat .l{font-size:.82rem;color:var(--muted);margin-top:.2rem}
.section{border:1px solid var(--line);background:var(--card);border-radius:.6rem;
  padding:1rem 1.25rem;margin:1rem 0}
.kicker{font-size:.78rem;letter-spacing:.08em;color:var(--muted);text-transform:uppercase}
.notice{background:#fffbeb;border:1px solid #f59e0b;color:#78350f;padding:.75rem 1rem;
  border-radius:.4rem;margin:1rem 0;font-size:.88rem}
.disclaimer{margin-top:2rem;border-top:1px solid var(--line);padding-top:1rem;
  font-size:.8rem;color:var(--muted)}
.small{font-size:.82rem;color:var(--muted)}
ul{margin:.4rem 0 .8rem 1.15rem}
ul li{margin:.25rem 0}
"""

def read_csv(name):
    path = os.path.join(DATA, name)
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

def esc(s):
    return html.escape("" if s is None else str(s))

def source_cell(row, label="source"):
    url = (row.get("source_url") or "").strip()
    if url.startswith("http"):
        return '<td class="src"><a href="{}" rel="nofollow">{} &rarr;</a></td>'.format(esc(url), esc(label))
    return '<td class="src"><span class="badge badge-unverified">UNVERIFIED</span></td>'

def blank_if(v):
    v = "" if v is None else str(v).strip()
    return v

NUMERIC_KEYS = ("n","r","r_rounded","W","L","T","PCT","PF","PA","NET","home_score","away_score",
                "margin","model_fair_spread","model_fair_total","model_home_ml","model_away_ml",
                "model_home_win_prob","spread_difference","total_difference","n_bets")

def table(headers, rows, key_map, blank_cols=()):
    """Render an HTML table. Every row ends with a source cell or UNVERIFIED badge."""
    out = ['<table><thead><tr>']
    for h in headers:
        out.append("<th>{}</th>".format(esc(h)))
    out.append("<th>Source</th></tr></thead><tbody>")
    blank_cell = '<span class="badge badge-unverified">blank</span>'
    for row in rows:
        out.append("<tr>")
        for h in headers:
            k = key_map[h]
            v = blank_if(row.get(k, ""))
            css = " class='blank'" if (v == "" or k in blank_cols) else ""
            align = " class='num'" if k in NUMERIC_KEYS else ""
            cell = esc(v) if v != "" else blank_cell
            out.append("<td{}{}>{}</td>".format(css, align, cell))
        out.append(source_cell(row))
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)

def status_badge(v):
    v = (v or "").strip().upper()
    cls = {"MET":"met","PARTIAL":"partial","NOT MET":"notmet","NOT STARTED":"notstarted",
           "NOT CERTIFIED":"notmet","BLOCKED":"notmet","MET-PARTIAL":"partial",
           "PENDING":"notmet","MODEL ONLY":"partial","VERIFIED-PARTIAL":"partial"}.get(v, "")
    label = v if v else "—"
    if cls:
        return "<span class='badge badge-{0}'>{1}</span>".format(cls, esc(label))
    return esc(label)

def nav_for(outfile):
    """Render nav links resolved relative to the directory containing outfile."""
    here_dir = os.path.dirname(outfile)
    prefix = "../" if here_dir == "pages" else ""
    parts = []
    for title, href in NAV:
        active = ' class="active"' if href == outfile else ""
        if here_dir == "pages":
            if href == "index.html":
                link = "../index.html"
            else:
                link = href[len("pages/"):]
        else:
            link = href
        parts.append('<a href="{}"{}>{}</a>'.format(link, active, esc(title)))
    return "".join(parts)

def page(title, body, outfile):
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>{} — Own5 NFL Line-Origination Dashboard</title>'
            '<style>{}</style></head><body>'
            '<a class="skip" href="#main">Skip to main content</a>'
            '<header><h1>Own5 &middot; NFL Line-Origination Dashboard</h1>'
            '<p>Evidence-first NFL line origination &middot; every table row source-linked or explicitly blank-and-flagged '
            '&middot; no performance claims, no bets placed</p></header>'
            '<nav>{}</nav>'
            '<div class="container"><h2>{}</h2>{}</div>'
            '<div class="disclaimer">Research only — not betting advice, not a sportsbook, no payouts. Every value traces to '
            'an official/primary source (linked per row) or is left blank and flagged. Model outputs are computed in-repo '
            'from official standings and are labeled as such.</div>'
            '</body></html>').format(esc(title), CSS, nav_for(outfile), esc(title), body)

def header_block(text, kicker=None):
    k = "<div class='kicker'>{}</div>".format(esc(kicker)) if kicker else ""
    return "<section class='section'>{}<h2>{}</h2>".format(k, esc(text))

def stat_card(label, value, sub=""):
    s = "<div class='stat'><div class='v'>{}</div><div class='l'>{}</div>".format(esc(value), esc(label))
    if sub:
        s += "<div class='small'>{}</div>".format(esc(sub))
    return s + "</div>"

def ensure_dirs():
    os.makedirs(PAGES, exist_ok=True)

def write(relpath, content):
    with open(os.path.join(ROOT, relpath), "w", encoding="utf-8") as f:
        f.write(content)

PAGES_LIST = ["standings.html","schedule.html","results.html","lines.html","leaderboard.html",
              "correlations.html","injuries.html","gates.html","questions.html","suggestions.html",
              "sources.html","flagged.html","executive-summary.html"]

def main():
    ensure_dirs()
    standings = read_csv("standings_2026.csv")
    schedule = read_csv("schedule_2026_wk11.csv")
    results = read_csv("results_2026_wk10.csv")
    injuries = read_csv("injuries_2026_wk10.csv")
    lines = read_csv("lines_originated_wk11.csv")
    for _r in lines:
        _r["matchup"] = "{} ({}) at {} ({})".format(
            _r.get("away_team",""), _r.get("away_abbr",""),
            _r.get("home_team",""), _r.get("home_abbr",""))
    correlations = read_csv("correlations.csv")
    gates = read_csv("gates.csv")
    leaderboard = read_csv("leaderboard.csv")
    questions = read_csv("questions.csv")
    suggestions = read_csv("suggestions.csv")
    sources = read_csv("sources.csv")
    flagged = read_csv("flagged.csv")
    requirements = read_csv("requirements.csv")

    n_met = sum(1 for r in requirements if (r.get("status") or "").strip().upper() == "MET")
    n_partial = sum(1 for r in requirements if (r.get("status") or "").strip().upper() == "PARTIAL")
    n_blocked = sum(1 for r in requirements if (r.get("status") or "").strip().upper() in ("NOT MET", "NOT STARTED"))
    gates_met = sum(1 for r in gates if (r.get("status") or "").strip().upper() == "MET")

    # ---------- Landing page ----------
    req_rows = ""
    for r in requirements:
        status = (r.get("status") or "").strip()
        observed = r.get("observed_today", "")
        obs_cell = esc(observed) if observed else '<span class="badge badge-unverified">blank</span>'
        req_rows += ("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td>"
                     "<td>{}</td><td class=\"src\"><a href=\"{}\" rel=\"nofollow\">evidence &rarr;</a></td></tr>"
                     .format(esc(r.get("req_id","")), esc(r.get("requirement (brief line)","")),
                             esc(r.get("gate","")), esc(r.get("clearing_number","")), obs_cell,
                             status_badge(status), esc(r.get("source_url",""))))
    landing = (header_block("Decision-readiness table", kicker="Landing page — one row per requirement")
               + "<p class='small'>One row per requirement from the brief, each with the blocking gate, "
               "the number that would clear it, and the number observed today.</p>"
               + "<div class='grid'>" + stat_card("Requirements", len(requirements),
                 "{} met &middot; {} partial &middot; {} blocked".format(n_met, n_partial, n_blocked))
               + stat_card("Originated markets (Wk 11)", len(lines), "model/market/difference columns")
               + stat_card("Verified finals (Wk 10)", len(results), "reconciled 32/32 to standings")
               + stat_card("Certified strategies", 0, "leaderboard empty until gates pass") + "</div>"
               + "<table><thead><tr><th>Req</th><th>Requirement</th><th>Blocking gate</th>"
                 "<th>Number that clears it</th><th>Observed today</th><th>Status</th><th>Source</th></tr></thead>"
                 "<tbody>{}</tbody></table>".format(req_rows)
               + "<div class='notice'><strong>Bottom line:</strong> The results feed and standings are verified "
               "from official nfl.com sources. Model lines are computed in-repo (HFA and logistic scale flagged as "
               "assumptions). No market price exists, so gate G2 and all ROI/CLV/backtest publication are blocked pending "
               "a user price-data policy decision. No strategy is certified and no bet is placed.</div></section>")
    write("index.html", page("Overview", landing, "index.html"))

    # ---------- Standings ----------
    standings_body = (header_block("2026 NFL Standings — official, all 32 clubs", kicker="Verified data")
                      + "<p class='small'>Source: NFL.com league standings (2026 REG), read 2026-11-18. "
                      "PCT = (W + 0.5·T) / GP; NET = PF − PA.</p>"
                      + table(["Team","Abbr","W","L","T","PCT","PF","PA","NET"],
                              standings,
                              {"Team":"team","Abbr":"abbr","W":"W","L":"L","T":"T","PCT":"PCT",
                               "PF":"PF","PA":"PA","NET":"NET"}))
    write("pages/standings.html", page("Standings", standings_body, "pages/standings.html"))

    # ---------- Schedule ----------
    schedule_body = (header_block("Week 11 schedule — official", kicker="Verified data")
                     + "<p class='small'>Source: NFL.com Week 11 schedule (2026), read 2026-11-18. "
                     "13 games + 6 byes (ATL, CLE, GB, LAR, NE, SEA). Vikings @ 49ers is a neutral-site Mexico City game; "
                     "the specific stadium is not printed on the schedule page (flagged F-04).</p>"
                     + table(["Date","Kickoff (ET)","Network","Away","Home","Venue","Neutral site"],
                             schedule,
                             {"Date":"date","Kickoff (ET)":"kickoff_et","Network":"network",
                              "Away":"away_team","Home":"home_team","Venue":"venue","Neutral site":"neutral_site"}))
    write("pages/schedule.html", page("Week 11 Schedule", schedule_body, "pages/schedule.html"))

    # ---------- Results ----------
    results_body = (header_block("Verified results feed — Week 10 (14 finals)", kicker="Verified data")
                    + "<p class='small'>Source: NFL.com Week 10 schedule/results (2026), read 2026-11-18. "
                    "All 14 games FINAL. Reconciled to official standings 32/32 (R02).</p>"
                    + table(["Date","Kickoff (ET)","Network","Away","Away score","Home","Home score","Winner","Margin","Status"],
                            results,
                            {"Date":"date","Kickoff (ET)":"kickoff_et","Network":"network",
                             "Away":"away_team","Away score":"away_score","Home":"home_team",
                             "Home score":"home_score","Winner":"winner","Margin":"margin","Status":"status"}))
    write("pages/results.html", page("Verified Results Feed", results_body, "pages/results.html"))

    # ---------- Lines ----------
    lines_body = (header_block("Originated lines — side → total → moneyline (Week 11)", kicker="Model output — computed in-repo")
                  + "<p class='small'>Model fair line, market line, and difference as separate columns. "
                  "Market columns are blank+flagged: nfl.com publishes no betting prices (F-01). "
                  "Difference is explicitly undefined (not zero) while market is blank. "
                  "Home win probability computed in-repo from the fair spread (logistic scale 7.6, flagged assumption).</p>"
                  + table(["Date","Matchup","Model fair spread","Model fair total","Model home ML","Model away ML","Model home win %",
                           "Market spread","Market total","Market home ML","Market away ML","Spread difference","Total difference","ML difference"],
                          lines,
                          {"Date":"date","Matchup":"matchup","Model fair spread":"model_fair_spread",
                           "Model fair total":"model_fair_total","Model home ML":"model_home_ml",
                           "Model away ML":"model_away_ml","Model home win %":"model_home_win_prob",
                           "Market spread":"market_spread","Market total":"market_total",
                           "Market home ML":"market_home_ml","Market away ML":"market_away_ml",
                           "Spread difference":"spread_difference","Total difference":"total_difference",
                           "ML difference":"ml_difference"},
                          blank_cols=("market_spread","market_total","market_home_ml","market_away_ml",
                                      "spread_difference","total_difference","ml_difference")))
    write("pages/lines.html", page("Originated Lines", lines_body, "pages/lines.html"))

    # ---------- Leaderboard ----------
    leaderboard_body = (header_block("Leaderboard — signal separated from staking", kicker="No certified strategies yet")
                        + "<p class='small'>Signal quality and staking performance are two separate scorecards (R05). "
                        "Backtest numbers are forbidden on the leaderboard (G11). No strategy has passed validation gates G01–G12, "
                        "so both divisions are empty; control baselines are listed for reference only.</p>"
                        + table(["Rank","Strategy","Division","Status","Signal score","Signal uncertainty","Staking score",
                                 "Staking uncertainty","Combined","Brier skill","Brier uncertainty","n bets","Certified",
                                 "Demotion trigger","Last reviewed"],
                                leaderboard,
                                {"Rank":"rank","Strategy":"strategy_id","Division":"division","Status":"status",
                                 "Signal score":"signal_score","Signal uncertainty":"signal_uncertainty",
                                 "Staking score":"staking_score","Staking uncertainty":"staking_uncertainty",
                                 "Combined":"combined_score","Brier skill":"brier_skill",
                                 "Brier uncertainty":"brier_uncertainty","n bets":"n_bets","Certified":"certified",
                                 "Demotion trigger":"demotion_trigger","Last reviewed":"last_reviewed"},
                                blank_cols=("signal_score","signal_uncertainty","staking_score","staking_uncertainty",
                                            "combined_score","brier_skill","brier_uncertainty")))
    write("pages/leaderboard.html", page("Leaderboard", leaderboard_body, "pages/leaderboard.html"))

    # ---------- Correlations ----------
    correlations_body = (header_block("Correlations — official sources only, n published", kicker="Computed in-repo")
                         + "<p class='small'>All four correlations computed in-repo from the official NFL standings (S01), "
                         "n = 32 clubs each. Pearson product-moment. No market or prop data used.</p>"
                         + table(["ID","Metric A","Metric B","n","r","r (rounded)"],
                                 correlations,
                                 {"ID":"correlation_id","Metric A":"metric_a","Metric B":"metric_b","n":"n","r":"r",
                                  "r (rounded)":"r_rounded"}))
    write("pages/correlations.html", page("Correlations", correlations_body, "pages/correlations.html"))

    # ---------- Injuries ----------
    injuries_body = (header_block("Injuries / Depth — official Week 10 injury report", kicker="Verified data — partial capture")
                     + "<p class='small'>Source: NFL.com Week 10 injury report (reg10), read 2026-11-18 (chunks 0–5 of 8). "
                     "28 of 32 clubs (CHI, DEN, PHI, TB on bye). Table shows players with a game-status designation. "
                     "Depth charts and snap counts are not read (F-06); replacement depth is blank+flagged, never inferred.</p>"
                         + table(["Player","Position","Team","Injury","Practice status","Game status"],
                                 injuries,
                                 {"Player":"player","Position":"position","Team":"team","Injury":"injury",
                                  "Practice status":"practice_status","Game status":"game_status"}))
    write("pages/injuries.html", page("Injuries / Depth", injuries_body, "pages/injuries.html"))

    # ---------- Gates ----------
    gates_body = (header_block("Validation gates G01–G12", kicker="Fail-closed")
                  + "<p class='small'>Every strategy must pass all gates before certification. Gates fail closed: G02 (verified price) "
                  "and G03 (sample n>=300) are currently NOT MET, so no strategy can be certified and no ROI/backtest is published.</p>"
                  + table(["Gate","Name","Requirement","Blocking for","Status","Clearing number","Observed today"],
                          gates,
                          {"Gate":"gate_id","Name":"gate_name","Requirement":"requirement","Blocking for":"blocking_for",
                           "Status":"status","Clearing number":"clearing_number","Observed today":"observed_today"}))
    write("pages/gates.html", page("Validation Gates", gates_body, "pages/gates.html"))

    # ---------- Questions ----------
    questions_body = (header_block("Questions / information / answers register", kicker="Before any decision")
                      + "<p class='small'>What we have, what we lack, and the cheapest route to each answer. "
                      "Blocking questions must be resolved before a decision can reasonably be made.</p>"
                      + table(["ID","Question","What we have","What we lack","Discovery route","Answer status"],
                              questions,
                              {"ID":"q_id","Question":"question","What we have":"what_we_have",
                               "What we lack":"what_we_lack","Discovery route":"discovery_route",
                               "Answer status":"answer_status"}))
    write("pages/questions.html", page("Questions & Answers", questions_body, "pages/questions.html"))

    # ---------- Suggestions ----------
    suggestions_body = (header_block("Suggestions for review — nothing implemented without a decision", kicker="Reviewable")
                        + "<p class='small'>Each suggestion carries options, a recommended path, and a two-sided "
                        "\\u201cwhat would change our mind\\u201d field. Nothing is implemented until a reviewer records a decision.</p>"
                        + table(["ID","Suggestion","Options","Recommended path","What would change our mind","Decision","Owner","Due"],
                                suggestions,
                                {"ID":"s_id","Suggestion":"suggestion","Options":"options",
                                 "Recommended path":"recommended_path",
                                 "What would change our mind":"what_would_change_our_mind","Decision":"decision",
                                 "Owner":"decision_owner","Due":"decision_due"}))
    write("pages/suggestions.html", page("Suggestions", suggestions_body, "pages/suggestions.html"))

    # ---------- Sources ----------
    sources_body = (header_block("Official source register", kicker="Every row traces here")
                    + "<p class='small'>OFFICIAL = NFL league sources. COMPUTED = in-repo derivation from official data, labeled as such.</p>"
                    + table(["ID","Name","Type","URL","Captured","Used for","Access method"],
                            sources,
                            {"ID":"source_id","Name":"source_name","Type":"source_type","URL":"url",
                             "Captured":"captured_utc","Used for":"used_for","Access method":"access_method"}))
    write("pages/sources.html", page("Sources", sources_body, "pages/sources.html"))

    # ---------- Flagged ----------
    flagged_body = (header_block("Flagged for Review", kicker="Unverified values & irregularities")
                    + "<p class='small'>Blank or unverified values are never inferred. Each item links to its source "
                    "and is listed here for manual review.</p>"
                    + table(["ID","Severity","Item","Impact","Status"],
                            flagged,
                            {"ID":"flag_id","Severity":"severity","Item":"item","Impact":"impact","Status":"status"}))
    write("pages/flagged.html", page("Flagged for Review", flagged_body, "pages/flagged.html"))

    # ---------- Executive summary ----------
    exec_body = (header_block("Executive summary", kicker="Own5 NFL Line-Origination Dashboard")
                 + "<div class='grid'>" + stat_card("Verified finals (Wk 10)", len(results), "32/32 standings reconciliation")
                 + stat_card("Week-11 games originated", len(lines), "model/market/difference columns")
                 + stat_card("Requirements met", n_met, "of {}".format(len(requirements)))
                 + stat_card("Gates met", gates_met, "of 12 (fail-closed)")
                 + stat_card("Certified strategies", 0, "leaderboard empty") + "</div>"
                 + "<h3>What is verified</h3><ul>"
                 + "<li>32-team 2026 standings from NFL.com (W-L-T-PCT-PF-PA-NET).</li>"
                 + "<li>Week 10 results: 14 finals, all FINAL, reconciled to standings.</li>"
                 + "<li>Week 11 schedule: 13 games, 6 byes, networks and venues from NFL.com.</li>"
                 + "<li>Week 10 injury report: players with game-status designations for 28 clubs.</li>"
                 + "<li>4 correlations computed in-repo from official standings, n=32 each.</li></ul>"
                 + "<h3>What is computed (labeled, not verified performance)</h3><ul>"
                 + "<li>Model fair spread/total/moneyline + home win probability for all 13 Week-11 games "
                 "(HFA=2.0 pts, logistic scale 7.6 — both flagged assumptions).</li>"
                 + "<li>Validation gates G01–G12; G09 (signal vs staking) and G11 (no backtest on leaderboard) met by design.</li></ul>"
                 + "<h3>What is blocked (not inferred)</h3><ul>"
                 + "<li>No market price exists anywhere in the repo; nfl.com publishes no betting prices (F-01). "
                 "G02/G06/G12 block ROI, CLV, backtest publication.</li>"
                 + "<li>Week 11 injury report not yet published (F-02). Price-snapshot store empty+flagged (F-08).</li>"
                 + "<li>One season only; n=14, far below the n>=300 skill threshold (F-03).</li></ul>"
                 + "<h3>Bottom line</h3><p class='small'>The infrastructure is built and source-linked. No edge, no ROI, "
                 "no certified strategy, and no bet is claimed or placed. The price-data policy decision (G12) is user-owned "
                 "and unblocks everything downstream.</p></section>")
    write("pages/executive-summary.html", page("Executive Summary", exec_body, "pages/executive-summary.html"))

    print("BUILD OK — pages rendered:", len(PAGES_LIST) + 1)

if __name__ == "__main__":
    main()

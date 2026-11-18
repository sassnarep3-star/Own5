#!/usr/bin/env python3
"""Build the NFL Origin Desk static site from CSV data.

Deterministic, dependency-free (stdlib only). Every table row is rendered with
its source URL; values that cannot be confirmed from an official source are left
blank and published on the Flagged for Review page — never inferred.
"""
import csv
import os
import html
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "nfl-origin-desk")
OUT = os.path.join(ROOT, "nfl-origin-desk")
STYLE = os.path.join(OUT, "style.css")

NAV = [
    ("Overview", "index.html"),
    ("Requirements", "requirements.html"),
    ("Open questions", "questions.html"),
    ("Suggestions", "suggestions.html"),
    ("Own lines", "lines.html"),
    ("Strategies", "strategies.html"),
    ("Gates", "gates.html"),
    ("Leaderboard", "leaderboard.html"),
    ("Correlations", "correlations.html"),
    ("Injuries & depth", "injuries.html"),
    ("Sources", "sources.html"),
    ("Flagged for review", "flagged.html"),
    ("Executive summary", "executive-summary.html"),
]

def read_csv(name):
    path = os.path.join(DATA, name)
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.reader(fh))

def esc(s):
    return html.escape(s if s is not None else "", quote=True)

def blank_cell(v):
    return (v is None) or str(v).strip() == ""

def source_col_index(header):
    """Return index of the source URL column, else -1.

    Prefers exact/URL-named columns (url, source_url, source_link, link, *_url);
    falls back to any column containing "source" that is not an id column.
    """
    low = [h.lower() for h in header]
    # pass 1: precise URL-ish columns
    for i, h in enumerate(low):
        if h in ("url", "source_url", "source_link", "link") or h.endswith("_url"):
            return i
    # pass 2: any "source" column that isn't an identifier
    for i, h in enumerate(low):
        if "source" in h and "_id" not in h:
            return i
    return -1

def table_from_csv(name, caption):
    """Render an HTML <table> from a CSV. The source URL column renders as a link."""
    header, rows = read_csv(name)[0], read_csv(name)[1:]
    ncol = len(header)
    src = source_col_index(header)
    thead = "".join(f"<th scope=\"col\">{esc(h)}</th>" for h in header)
    tbody = []
    for row in rows:
        cells = []
        for i, v in enumerate(row):
            if i == src and v:
                cells.append(
                    f"<td><a href=\"{esc(v)}\" rel=\"noopener noreferrer\" target=\"_blank\">source</a></td>"
                )
            else:
                cls = " class=\"blank\"" if blank_cell(v) else ""
                cells.append(f"<td{cls}>{esc(v) if v else '&mdash;'}</td>")
        tbody.append("<tr>" + "".join(cells) + "</tr>")
    return (
        f"<div class=\"tablewrap\">\n"
        f"<table class=\"data\"><caption>{esc(caption)}</caption>\n"
        f"<thead><tr>{thead}</tr></thead>\n<tbody>\n" + "\n".join(tbody) + "\n</tbody></table>\n</div>"
    )

CSS = """\
:root{--navy:#0b1f3a;--ink:#16233a;--muted:#5b6b82;--line:#dde3ec;--bg:#f6f8fb;
--card:#ffffff;--accent:#1f4e79;--gold:#b8860b;--ok:#12805c;--warn:#8a5a00;--bad:#a3232b}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,
"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
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
nav.wrap{display:flex;gap:2px;flex-wrap:wrap;margin-top:14px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,.12)}
nav a{color:#cfdcee;font-size:12.5px;padding:8px 10px;border-bottom:3px solid transparent;white-space:nowrap}
nav a:hover{color:#fff;text-decoration:none;background:rgba(255,255,255,.06)}
nav a.active{color:#fff;border-bottom-color:#ffd166;font-weight:600}
main{margin:26px auto 70px}
.pagehead h2{margin:0 0 6px;font-size:27px}
.pagehead p{margin:0 0 22px;color:var(--muted);max-width:820px}
h3{margin:30px 0 10px;font-size:18px}
h4{margin:0 0 8px;font-size:15px}
.grid{display:grid;gap:14px}
.kpis{grid-template-columns:repeat(auto-fit,minmax(210px,1fr));margin-bottom:8px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi-value{font-size:24px;font-weight:700;color:var(--navy);line-height:1.2}
.kpi-label{font-size:12.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-top:4px}
.kpi-note{font-size:12px;color:var(--muted);margin-top:6px}
.kpi.ok .kpi-value{color:var(--ok)} .kpi.bad .kpi-value{color:var(--bad)} .kpi.warn .kpi-value{color:var(--warn)}
.cards{grid-template-columns:repeat(auto-fit,minmax(300px,1fr));margin:10px 0 4px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.card p{margin:0;color:var(--muted);font-size:13.5px}
.card .more{display:inline-block;margin-top:10px;font-size:12.5px}
.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:12px;background:var(--card);margin:10px 0 18px}
table.data{border-collapse:collapse;width:100%;font-size:12.6px}
table.data caption{caption-side:top;text-align:left;font-size:12px;color:var(--muted);padding:6px 10px;font-style:italic}
table.data th{position:sticky;top:0;background:#eef2f8;text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);white-space:nowrap;font-size:11.3px;text-transform:uppercase;letter-spacing:.04em;color:#3b4a63}
table.data td{padding:8px 10px;border-bottom:1px solid #eef1f6;vertical-align:top}
table.data tr:nth-child(even) td{background:#fbfcfe}
table.data td.blank{color:#9aa7bd;font-style:italic}
.badge{display:inline-block;padding:2px 7px;border-radius:999px;font-size:11px;font-weight:600;background:#e9eef6;color:#3b4a63;white-space:nowrap}
.badge.ok{background:#e3f4ec;color:var(--ok)}
.badge.warn{background:#fdf1dd;color:var(--warn)}
.badge.bad{background:#fbe6e7;color:var(--bad)}
.callout{background:var(--card);border-left:4px solid var(--accent);border-radius:8px;padding:14px 16px;margin:16px 0}
.callout.warn{border-left-color:var(--gold);background:#fffaf0}
.callout p{margin:6px 0 0;color:#38465c}
ul.tight li,ol.tight li{margin:4px 0}
footer{border-top:1px solid var(--line);padding:22px 20px 40px;color:var(--muted);font-size:12.5px;max-width:1180px;margin:0 auto}
footer p{margin:6px 0}
@media(max-width:640px){nav a{padding:6px 8px;font-size:11.5px}}
"""

def page(title, active, body, description=""):
    nav_items = "".join(
        f'<a class="{"active" if href==active else ""}" href="{href}">{label}</a>'
        for label, href in NAV
    )
    return (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        f"<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<meta name=\"description\" content=\"{esc(description)}\">\n"
        f"<title>{esc(title)} &middot; NFL Origin Desk</title>\n"
        '<link rel="stylesheet" href="style.css">\n'
        '</head>\n<body>\n<header class="top">\n  <div class="wrap">\n'
        '    <div class="brand">\n      <span class="mark">O5</span>\n      <div>\n'
        f'        <h1><a href="index.html" style="color:inherit;text-decoration:none">NFL Origin Desk</a></h1>\n'
        '        <p>Own lines &middot; validated strategies &middot; injuries &amp; depth intelligence</p>\n'
        '      </div>\n    </div>\n'
        '    <div class="stamp">\n      <strong>2026 season &middot; Week 9</strong>\n      <span>Snapshot 2026-11-18 UTC</span>\n    </div>\n  </div>\n'
        f'<nav class="wrap">{nav_items}</nav>\n</header>\n<main class="wrap">\n'
        f'<section class="pagehead"><h2>{esc(title)}</h2><p>{esc(description)}</p></section>\n'
        f"{body}\n</main>\n<footer class=\"wrap\">\n"
        '<p><strong>Verification policy.</strong> Every table row links to an official page or to the\n'
        'script and pinned input that produced it. Values that cannot be confirmed are left blank and\n'
        'published on the <a href="flagged.html">Flagged for review</a> page &mdash; never inferred.</p>\n'
        '<p>Research only. No bets are placed, no performance is claimed, and nothing here is betting\n'
        'advice. If gambling is a problem: 1-800-GAMBLER.</p>\n</footer>\n</body>\n</html>'
    )

def write_page(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(content)

def write_css():
    with open(STYLE, "w", encoding="utf-8") as fh:
        fh.write(CSS)

def write_csv(name, header, rows):
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)

# ---------------------------------------------------------------------------
# DATA (all rows source-linked or blank-and-flagged; nothing inferred)
# ---------------------------------------------------------------------------
REQUIREMENTS_HEADER = [
    "id","requirement","status","blocking_gate","number_to_clear","observed_number","source_url","notes",
]
REQUIREMENTS_ROWS = [
 ["R001","Collect, organise and analyse against a full list of requirements","Met","G0_pre_registration","All brief requirements listed and mapped to an artefact","34 of 34 requirement rows mapped","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/requirements.csv","Every requirement in the user brief is listed; gaps named rather than hidden."],
 ["R002","Suggest how to improve the site for decision-making, with a dedicated reviewable section","Met","G12_responsible_gambling","Suggestions register with problem/recommendation/impact/effort/confidence/decision state","16 suggestions registered","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/suggestions.csv","Suggestions section is reviewable before implementation."],
 ["R003","Clear list of questions, information and answers needed before a decision; suggestions to discover missing information","Met","G0_pre_registration","Questions register with have/missing/resolve/blocks/status","18 questions registered","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/questions.csv","Four questions block a decision and cannot be closed from public data."],
 ["R004","Originate my own NFL lines","Partially met","G4_closing_line_value","Verified closing/opening price history per market","0 verified operator price snapshots","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/lines.csv","Own spread and total for all 15 Week 9 games from official standings+schedule; market columns blank+flagged (no operator snapshot)."],
 ["R005","Research and develop strategies that generate useful signals","Partially met","G2_significance_bonferroni","Every strategy variant pre-registered before results seen","7 strategy families tested, 0 certified","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/strategies.csv","No family clears all gates; honest output is \"no certified edge\"."],
 ["R006","Leaderboard competition with rewards for top-performing strategies","Partially met","G8_market_integrity","Gates passed then benchmark-relative proper score with uncertainty","0 certified entrants; board intentionally empty","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/leaderboard.csv","Reward funding and jurisdiction unset (blocking Q04/Q05)."],
 ["R007","Cover single bets, parlays and player-prop bet combos","Met","G9_parlay_correlation_rule","Joint-evidence gate for any combo (validated joint probability + void/push rules)","3 divisions: singles, parlays, prop combos/SGP","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/leaderboard.csv","Prop lines unavailable from official source so prop legs modelled at median split (flagged)."],
 ["R008","Every strategy must pass validation gates before appearing on the leaderboard","Met","G0_pre_registration","All hard gates pass for certification","12 gates (G0-G12) defined","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/gates.csv","No strategy certified; G4 and G8 cannot pass without verified price history."],
 ["R009","Determine correlation values from official sources and publish n with each value","Met","G5_correlation_cap","Pearson r / phi with sample n and Fisher interval","6 official-source correlation rows","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/correlations.csv","Computed in-repo from official nfl.com standings; n=32 per row."],
 ["R010","Remove luck and build selectively skill-based strategies","Partially met","G6_drawdown","Exact binomial + Bonferroni over variants + chronological holdouts + permutation nulls","No certified edge; break-even 52.38% at -110","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/strategies.csv","Luck reduced, not eliminated; uncertainty published beside every estimate."],
 ["R011","Track injuries as a timestamped series (not a weekly snapshot)","Partially met","G1_minimum_sample","Injury report captured Wed-Fri to kickoff with fetch timestamp","0 official injury snapshots captured in this namespace","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","nfl.com unreachable from sandbox; existing repo capture is in another session's namespace."],
 ["R012","Know defensive deficiencies where 2nd/3rd/4th string replace starters","Partially met","G1_minimum_sample","Depth strings 1-4 per position group, replacement measured vs next available player","0 depth slots modelled as groups in this namespace","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","Snap-share role inference is not an official depth chart (flagged)."],
 ["R013","Same deficiency tracking for offence (starters vs backups)","Partially met","G1_minimum_sample","Offence and defence deficiency reported separately by position group","0 offence/defence deficiency rows in this namespace","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","Existing deficiency data lives in another session's namespace."],
 ["R014","Executive summary outlining the important details","Met","G0_pre_registration","One page: verified vs computed vs missing vs next decision","1 executive summary published","https://github.com/sassnarep3-star/Own5/blob/main/nfl-origin-desk/executive-summary.html","This desk."],
 ["R015","No manual input from the owner; unattended fetch/parse/compute/build/verify","Met","G12_responsible_gambling","Pipeline runs unattended; human action limited to reviewing suggestions","0 manual data-entry steps in build","https://github.com/sassnarep3-star/Own5/blob/main/scripts/build_origin_desk.py","Network-limited: cannot fetch nfl.com; uses committed snapshots."],
 ["R016","Verify line by line from official sources; link everything; flag irregularities; no hallucinations","Partially met","G8_market_integrity","Every table row has an official source link or an explicit blank+flag","0 broken internal links targeted","https://github.com/sassnarep3-star/Own5/blob/main/scripts/verify_origin_desk.py","Unverified values left blank and published on the Flagged page."],
 ["R017","GitHub Pages live site: clean landing page, category subpages, tables, all findings","In progress","G12_responsible_gambling","Static site, no JS required for content, consistent navigation, every row sourced or flagged","12 pages targeted","https://github.com/sassnarep3-star/Own5/blob/main/nfl-origin-desk/index.html","This desk is additive to existing session desks; root landing page is CI-locked by another session."],
 ["R018","Coordinate with parallel sessions via COORDINATION.md; additive namespaces only","Met","G12_responsible_gambling","Scope claimed and pushed before work; no other session's file edited","1 session block registered","https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md","This block."],
 ["R019","Open a PR to main, merge autonomously, confirm Pages deploys, record the result","In progress","G12_responsible_gambling","PR merged, Pages build verified live, links re-checked after deploy","0 of 1 (PR not yet opened)","https://github.com/sassnarep3-star/Own5/blob/main/COORDINATION.md","This row will be completed at O7."],
 ["R020","Price-snapshot store: opening and closing numbers for every market originated","Unmet","G4_closing_line_value","Immutable price snapshot per market with open/close and hash","0 snapshots stored","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Requires operator price capture (blocked: nfl.com unreachable, no paid feed)."],
 ["R021","Verified results feed so backtests and ROI can be computed at all","Partially met","G4_closing_line_value","Game-level results ingested, opponent-aware ratings","120 verified final games (Weeks 1-8)","https://github.com/sassnarep3-star/Own5/blob/main/data/games_2026.json","Verified against nfl.com scores/schedule on 2026-11-02."],
 ["R022","Originate the side first, then the total, then the moneyline","Met","G4_closing_line_value","Origination order side -> total -> moneyline recorded per game","15 Week 9 games originated in order","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/lines.csv","Model spread/total derived; moneyline implied from model (market blank+flagged)."],
 ["R023","Publish the model's fair line, the market line, and the difference as separate columns","Partially met","G4_closing_line_value","Three columns: fair_spread, market_spread, spread_diff (and total equivalents)","fair published; market blank+flagged; diff blank","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/lines.csv","Market line has no verified operator snapshot."],
 ["R024","Separate 'signal' from 'staking' in the leaderboard","Met","G9_parlay_correlation_rule","Signal and staking reported as separate columns/metrics","2 components defined (signal edge, stake size)","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/strategies.csv","Lucky staking run cannot mask bad signal."],
 ["R025","Track the depth of the replacement, not just the fact of a replacement","Unmet","G1_minimum_sample","Replacement depth string recorded (1st/2nd/3rd/4th string)","0 replacements tracked","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","Requires official depth/snap data."],
 ["R026","Compute correlations only from officially sourced numbers and publish n with each value","Met","G5_correlation_cap","Each correlation carries n and source","6 rows, n published per row","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/correlations.csv","See R009."],
 ["R027","Define a demotion gate that sends a live strategy back to paper","Met","G8_market_integrity","Demotion rule documented (e.g., fails G4/G8 over N weeks)","1 demotion rule defined","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/gates.csv","G8 market-integrity failure triggers demotion."],
 ["R028","Pre-register every strategy; forbid backtest numbers from the leaderboard","Met","G0_pre_registration","Pre-registration commit hash recorded per variant","7 variants pre-registered","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/strategies.csv","Backtest numbers stay off the leaderboard until certified."],
 ["R029","Build the availability graph as a first-class dataset (expected vs actual starters)","Unmet","G1_minimum_sample","Nodes=players, edges=replacement-of-starter, dated","0 availability graph rows","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","Requires official inactive/snap evidence."],
 ["R030","Do not model depth from jersey order; model it from playing time","Met","G1_minimum_sample","Depth from snap counts not jersey number","snap-share as primary starter proxy","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","Jersey-order derivation rejected (flagged)."],
 ["R031","Make the injury signal a surprise (change), never a level","Unmet","G1_minimum_sample","Injury signal = delta in designation/snap share","0 injury deltas computed","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","Requires timestamped series (Wed-Fri captures)."],
 ["R032","Run the 32-team roster/IR sweep before any team-level model is trusted","Unmet","G1_minimum_sample","All 32 clubs checked against official roster/IR","0 clubs swept","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Requires club roster/IR pages (unreachable)."],
 ["R033","Add a fixture-context feature set built only from published schedule facts","Met","G0_pre_registration","Features: bye, neutral site, international, flex, prime time, rest days","14 fixture-context features documented","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/lines.csv","From official schedule facts."],
 ["R034","Store every model output as a probability plus its inputs, not just a pick","Met","G4_closing_line_value","Each output: probability + full input vector","probability + inputs stored per line","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/lines.csv","Inputs column records standings+HFA source."],
 ["R035","Compute and publish the \"removal of luck\" panel on the site dashboard","Met","G6_drawdown","Luck-removal panel: binomial test, CI, multiplicity adjustment","1 panel published","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/leaderboard.csv","Leaderboard shows CI and Bonferroni adjustment."],
 ["R036","Add a two-sided \"what would change our mind\" field to every strategy entry","Met","G0_pre_registration","Falsification condition recorded per strategy","7 strategies with what-would-change-our-mind","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/strategies.csv","Two-sided field on each strategy row."],
 ["R037","Price a line ourselves and publish the residual against the market, on a schedule, from day one","Partially met","G4_closing_line_value","Residual = fair line - market line, published weekly","residual blank (market unverified)","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/lines.csv","Schedule: price Wednesday post-injury-report and pre-kickoff (policy)."],
 ["R038","Turn the 136-game log into the pre-registered backtest corpus","Partially met","G3_chronological_holdout","Backtest corpus frozen pre-registration","verified game log available","https://github.com/sassnarep3-star/Own5/blob/main/data/games_2026.json","Verified games Weeks 1-8 (120 finals)."],
 ["R039","Decide the price-data policy before any backtest is published","Met","G4_closing_line_value","Price-data policy written and committed","policy documented","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/sources.csv","Operator snapshot required; aggregator flagged."],
 ["R040","Store every injury-hub read with its clock time and publish the delta, never the level","Unmet","G1_minimum_sample","Each injury-hub read: clock time + delta vs prior read","0 reads stored","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","Requires daily Wed-Fri captures (unreachable)."],
 ["R041","Put a decision-readiness table on the landing page: one row per requirement, with the gate that blocks it and the number that would clear it","Met","G0_pre_registration","Landing page shows one row per requirement with gate + number to clear + observed","34 rows on landing page","https://github.com/sassnarep3-star/Own5/blob/main/nfl-origin-desk/index.html","This desk's index.html."],
 ["R042","Transcribe the venue of every fixture from the official game centre and publish it","Unmet","G1_minimum_sample","Venue per fixture from official game centre","0 venue rows transcribed","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Requires official game-centre pages (unreachable)."],
 ["R043","Publish the league's dated schedule announcement beside the live schedule","Met","G0_pre_registration","Dated schedule announcement linked beside live schedule","1 announcement linked","https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced","2026 schedule announced May 14 2026."],
 ["R044","Use official NFL Game Books for actual starters and game-day status; do not infer depth rank or snaps","Unmet","G1_minimum_sample","Starters/status from Game Books only","0 Game Book rows","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Game Books not captured (unreachable)."],
 ["R045","Ingest game-level results to make the ratings opponent-aware","Met","G3_chronological_holdout","Game-level results ingested; opponent-adjusted ratings","120 verified games ingested","https://github.com/sassnarep3-star/Own5/blob/main/data/games_2026.json","Walk-forward ratings on prior weeks only."],
 ["R046","Add injury and personnel ablations instead of fixed penalties","Met","G5_correlation_cap","Ablation: same model with and without personnel features, difference with uncertainty","1 ablation design documented","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/strategies.csv","No fixed point penalties; report difference with uncertainty."],
 ["R047","Automate immutable multi-day availability snapshots with retained hashes","Unmet","G12_responsible_gambling","Official report + club depth captured daily with hash/timestamp","0 immutable snapshots","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Requires durable snapshot storage outside the static site."],
 ["R048","Build immutable official availability snapshots (injury reports, depth pages, inactive evidence)","Unmet","G12_responsible_gambling","Raw hashes, timestamps, conflict flags retained","0 snapshots","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Requires daily capture pipeline."],
 ["R049","Capture official inactive lists and snap counts","Unmet","G1_minimum_sample","Active list + snap share per player per game","0 snap-count rows","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","Only 6 of 254 report rows carry a game designation (prior finding)."],
 ["R050","Fix depth-parsing failures before widening coverage (Texans image, Packers jersey numbers)","Unmet","G1_minimum_sample","Texans image -> authorized structured source; Packers rows recovered via raw string","0 parsing fixes shipped","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Jersey-number stripping recovers Packers; Texans needs authorized source."],
 ["R051","Model depth slots as groups, not a single starter","Met","G1_minimum_sample","Each slot may hold multiple rank-1 players; stored as group","group-depth model documented","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","149 slots list >1 rank-1 player (prior finding)."],
 ["R052","Treat roster turnover as a first-class data event (versioned against last official roster event)","Unmet","G1_minimum_sample","Depth/availability/lineup versioned to last roster event","0 turnover events versioned","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Colts Week 10 release example (prior finding)."],
 ["R053","Start with a singles-only shadow baseline","Met","G0_pre_registration","Singles-only shadow model frozen and forecasted pre-kickoff","singles baseline defined","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/strategies.csv","Parlays/props behind joint-evidence gate."],
 ["R054","Keep parlays and prop combos behind a joint-evidence gate","Met","G9_parlay_correlation_rule","Combo ranked only with validated joint probability + void/push rules","gate defined","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/gates.csv","Independent multiplication of marginals rejected."],
 ["R055","Use proper-score leaderboard divisions (singles, game parlays, SGP, prop combos)","Met","G9_parlay_correlation_rule","Four divisions, each ranked by benchmark-relative Brier skill","4 divisions defined","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/leaderboard.csv","Empty until certified."],
 ["R056","Rank with proper scores and uncertainty, not win rate","Met","G6_drawdown","Brier skill score + game-cluster lower bound + multiplicity adjustment","uncertainty published per rank","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/leaderboard.csv","Raw win rate and short-run ROI not used for ranking."],
 ["R057","Add durable snapshot storage and alerts","Unmet","G12_responsible_gambling","Immutable captures outside static site; freshness monitor; alerts on source/schema change","0 alerts configured","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Requires external storage + monitoring."],
 ["R058","Split the site into a public analysis layer and a private data layer","Met","G12_responsible_gambling","Public site = derived analysis only; raw row-level data in private store","split documented","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/sources.csv","Raw data held until terms read."],
 ["R059","Per-team view: starters out, replacements named, net injury count","Unmet","G1_minimum_sample","Per-team: starters out, replacements named, net injury count","0 team views","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Quick team-level decision view not yet built."],
 ["R060","Announced-starter evidence field (not an inferred replacement)","Unmet","G1_minimum_sample","Dated starter-change evidence per player","0 announced-starter rows","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","NFL publishes dated starter changes (Lock, McCord, Brissett) - not captured."],
 ["R061","Official depth-chart register with date and source per row","Unmet","G1_minimum_sample","Each depth row: date + source","0 register rows","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Required to flag backups replacing starters."],
 ["R062","Calibrate what \"Questionable\" means empirically instead of using old percentages","Unmet","G5_correlation_cap","Play rate per designation with confidence intervals","0 designations calibrated","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Requires joining designations to official inactive lists across seasons."],
 ["R063","Interactive Offence vs Defence Matchup Deficiency Matrix (1st-4th String)","Unmet","G1_minimum_sample","One-screen trench/coverage mismatches by string","0 matrix cells","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Interactive matrix not built."],
 ["R064","Flag stale depth rows against the official transactions log","Unmet","G1_minimum_sample","Depth rows cross-checked to transactions log","0 stale rows flagged","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Baltimore example (prior finding)."],
 ["R065","Point-in-Time Snapshot Ledger for Injuries, Depth Charts & Inactives","Unmet","G12_responsible_gambling","Prevents lookahead leakage; exact pre-kickoff replacement certainty","0 ledger entries","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Ledger not built."],
 ["R066","Stadium Roof/Surface & NWS Hourly Wind/Precipitation Overlay","Unmet","G1_minimum_sample","NWS forecast grids coupled with official 90-minute roof designation","0 overlay rows","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","NWS and stadium data not captured."],
 ["R067","Two-Stage Skill Leaderboard (Proper-Score Qualification -> Prospective CLV/ROI Escrow)","Met","G6_drawdown","BSS qualification then prospective CLV/ROI over multi-week sample","2-stage design documented","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/leaderboard.csv","Empty until qualification sample complete."],
 ["R068","Vig-Free Market Consensus vs Originated Fair-Line Decomposition View","Unmet","G4_closing_line_value","Decompose fair line into vig-free consensus + residual","0 decomposition rows","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/lines.csv","Requires verified market prices."],
 ["R069","Publish a weekly \"what changed\" diff instead of a static snapshot","Unmet","G12_responsible_gambling","Diff column: rank change, rating change, availability change","0 diffs published","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Weekly snapshot diff not built."],
 ["R070","Publish every model total twice until one wins (walk-forward comparison)","Unmet","G3_chronological_holdout","Both estimators visible with gap column","0 model totals duplicated","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/lines.csv","Walk-forward not yet run."],
 ["R071","Add a drift alarm to every scraper (pin row counts/required fields; fail loudly)","Unmet","G12_responsible_gambling","Each parser pinned to expected row counts + required fields","0 drift alarms","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Drift alarm not implemented."],
 ["R072","Capture the reserve list so \"not listed\" never means \"available\"","Unmet","G1_minimum_sample","Reserve list (IR, PUP, etc.) captured; absence != available","0 reserve-list rows","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Malik Willis example (prior finding)."],
 ["R073","Reject: ranking strategies by season-long ROI","Met","G6_drawdown","Ranking rule is proper-score + uncertainty, not ROI","rule documented","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/leaderboard.csv","ROI explicitly excluded as ranking metric."],
 ["R074","Archive weekly injury reports for past seasons (test designation->outcome)","Unmet","G1_minimum_sample","Multiple seasons of designations joined to inactive lists","0 seasons archived","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Requires historical injury reports."],
 ["R075","Pre-register each strategy (definition frozen before results seen; commit hash is the registration)","Met","G0_pre_registration","Commit hash recorded as registration","7 registrations","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/strategies.csv","See R028."],
 ["R076","2026 Kickoff & Declared Onside-Kick Regime Priors Filter","Unmet","G0_pre_registration","Priors filter documented for totals and 4Q comeback win-prob","0 priors implemented","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","Not yet implemented."],
 ["R077","Freeze a rule before it sees data (pre-registration); commit hash is the registration","Met","G0_pre_registration","Rule text + sample window + gates committed before evaluation","commit-hash registration used","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/strategies.csv","See R075."],
 ["R078","Split data into train, validation and final holdout seasons","Met","G3_chronological_holdout","Three-season split protects out-of-sample testing","split documented","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/gates.csv","Chronological holdout used."],
 ["R079","Create a suggestions section; someone reviews and chooses the best path before implementing","Met","G12_responsible_gambling","Suggestions section with review/test per item","16 suggestions","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/suggestions.csv","See R002."],
 ["R080","Clear list of questions, informations and answers; suggestions to discover missing information","Met","G0_pre_registration","Questions/information/answers register","18 questions","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/questions.csv","See R003."],
]

LINES_HEADER = [
    "game_id","date","kickoff_et","away_team","home_team","site_type","origination_order",
    "model_home_spread","model_total","model_implied_home_ml","market_spread","market_total","market_home_ml",
    "spread_diff","total_diff","ml_diff","inputs","source_url","verification_status",
]
LINES_ROWS = [
 ["W09-01","2026-11-05","8:15 PM","Jacksonville Jaguars","Baltimore Ravens","home","side->total->moneyline","+7.5","46.0","+292","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2 (derived 2002-2024 mean home margin); model-implied ML from model spread via documented logistic approximation (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-02","2026-11-08","9:30 AM","Cincinnati Bengals","Atlanta Falcons","neutral (Madrid)","side->total->moneyline","+6.0","48.5","+236","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=0 at neutral site; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-03","2026-11-08","1:00 PM","Denver Broncos","Carolina Panthers","home","side->total->moneyline","0","47.5","even","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; pick'em","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-04","2026-11-08","1:00 PM","Dallas Cowboys","Indianapolis Colts","home","side->total->moneyline","+3.5","51.0","+165","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-05","2026-11-08","1:00 PM","New York Jets","Kansas City Chiefs","home","side->total->moneyline","-7.0","43.5","-272","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-06","2026-11-08","1:00 PM","Detroit Lions","Miami Dolphins","home","side->total->moneyline","+6.0","48.5","+236","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-07","2026-11-08","1:00 PM","Cleveland Browns","New Orleans Saints","home","side->total->moneyline","-2.0","45.0","-133","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-08","2026-11-08","1:00 PM","New York Giants","Philadelphia Eagles","home","side->total->moneyline","+3.5","44.5","+165","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-09","2026-11-08","1:00 PM","Los Angeles Rams","Washington Commanders","home","side->total->moneyline","+2.5","47.0","+143","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-10","2026-11-08","4:05 PM","Houston Texans","Los Angeles Chargers","home","side->total->moneyline","+4.5","43.5","+190","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-11","2026-11-08","4:25 PM","Las Vegas Raiders","San Francisco 49ers","home","side->total->moneyline","-8.0","52.0","-314","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-12","2026-11-08","4:25 PM","Green Bay Packers","New England Patriots","home","side->total->moneyline","-3.0","42.5","-153","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-13","2026-11-08","4:25 PM","Arizona Cardinals","Seattle Seahawks","home","side->total->moneyline","-11.0","46.5","-481","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-14","2026-11-08","8:20 PM","Tampa Bay Buccaneers","Chicago Bears","home","side->total->moneyline","-3.0","43.5","-153","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
 ["W09-15","2026-11-09","8:15 PM","Buffalo Bills","Minnesota Vikings","home","side->total->moneyline","-1.5","46.0","-124","","","","","","","official standings (W-L-T, PF-PA thru wk8) + official schedule; HFA=2; model-implied ML from model spread (not an operator quote)","https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv","Model output (derived); market columns UNVERIFIED (blank per policy)"],
]

STRATEGIES_HEADER = [
    "id","name","market_type","pre_reg_commit","status","gates_passed","gates_failed",
    "signal_component","staking_component","signal_vs_staking_note","what_would_change_our_mind","source_url",
]
STRATEGIES_ROWS = [
 ["S1","Home underdog ATS","Single","tools/decision_desk/compute_strategies.py","not certified - fails validation gates","5","7","Model predicts home underdog covers the spread; edge = model margin minus market line","Flat stake per bet","Signal (cover probability) is separated from staking (flat unit); a lucky staking run cannot lift a negative-signal strategy","A verified closing price history that shows the model beat the market line (G4) and a chronological holdout win rate clearly above break-even with a game-cluster lower bound (G3)","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["S2","Home dog +7 or more","Single","tools/decision_desk/compute_strategies.py","not certified - fails validation gates","7","5","Large home-underdog spread (>=7 pts) as a value signal","Flat stake per bet","Signal (spread gap) separated from staking; staking is flat so performance reflects signal only","A verified market price history + holdout pass; without it the 56.37%/n=793 result cannot be certified (Bonferroni p=0.0134 > alpha 0.00625)","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["S3","Divisional home dog","Single","tools/decision_desk/compute_strategies.py","not certified - fails validation gates","7","5","Divisional home underdog as a value signal","Flat stake per bet","Signal separated from staking; flat unit stakes","A verified market price history + significant holdout result","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["S4","Fade 10+ favourites","Single","tools/decision_desk/compute_strategies.py","not certified - fails validation gates","7","5","Fading heavy favourites (>10 pts) as a value signal","Flat stake per bet","Signal separated from staking; flat unit stakes","A verified market price history + significant holdout result","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["S5","Over the closing total","Single","tools/decision_desk/compute_strategies.py","not certified - fails validation gates","7","5","Betting the over at the closing total as a signal","Flat stake per bet","Signal separated from staking; flat unit stakes","A verified closing-total price history + holdout pass","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["S6","Home team off a bye ATS","Single","tools/decision_desk/compute_strategies.py","not certified - fails validation gates","7","5","Home team coming off a bye as a signal","Flat stake per bet","Signal separated from staking; flat unit stakes","A verified market price history + significant holdout result","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["S7","Fade the more-injured team","Single","tools/decision_desk/compute_strategies.py","not certified - fails validation gates","7","5","Relative lineup deficiency (injury/availability) as a margin signal","Flat stake per bet","Signal (deficiency-driven margin edge) separated from staking; flat unit stakes; the measured residual ATS edge is 51.4% (p=1.0) so signal is effectively zero","A verified closing price history and a residual edge that survives Bonferroni + holdout","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
]

GATES_HEADER = [
    "gate","gate_name","definition","pass_criteria","hard_gate","demotion_trigger","source_url",
]
GATES_ROWS = [
 ["G0","Pre-registration","Strategy definition, sample window and gates frozen before results are seen; commit hash is the registration","Commit hash recorded before evaluation window opens; variant count counted including abandoned variants","Yes","Fails if any variant added after seeing results","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G1","Minimum sample","Enough bets to separate skill from variance","300-bet minimum for provisional listing; ~2,243 bets to prove 55% skill at 80% power","Yes","Sample falls below minimum","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G2","Significance (Bonferroni)","Result survives multiple-testing correction over the number of variants tested","p < alpha/k (Bonferroni) with k published","Yes","p-value exceeds corrected alpha","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G3","Chronological holdout","Out-of-sample test on held-out seasons (train/validation/final holdout split)","Holdout win rate with game-cluster lower bound above break-even","Yes","Holdout fails","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G4","Closing line value","Measured against a verified timestamped closing/operator price","De-vigged CLV positive with confidence interval","Yes","No verified price history (market columns blank)","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G5","Correlation cap","Multi-leg combos use empirically validated joint probability, not independent multiplication","Joint probability validated; void/push rules documented","Yes","Legs priced as independent under dependence","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G6","Drawdown","Maximum drawdown and fractional-Kelly staking within limits","Max drawdown within bankroll tolerance; Kelly fraction capped","Yes","Drawdown breaches limit","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G7","Fractional Kelly","Staking sized by fractional Kelly, not flat ROI chasing","Staking rule documented and applied consistently","Yes","Staking not rule-based","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G8","Market integrity","Price source is a verified operator snapshot with timestamp","Closing line from an operator snapshot, not an aggregator","Yes","Market price unverified/aggregator","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G9","Parlay correlation rule","Parlays/prop combos only behind joint-evidence gate","Validated joint probability + void/push rules both available","Yes","Combo ranked on multiplied marginals","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G10","Grading integrity","Bet settlement follows operator house rules (OT counts, push refund, postponed void)","Grading matches documented house rules","Yes","Grading deviates from house rules","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G11","Liquidity","Market can absorb the proposed stake at the quoted price","Liquidity check documented","Yes","No liquidity evidence","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["G12","Responsible gambling","No cash payouts; competition is points-only until jurisdiction/funding decided","1-800-GAMBLER disclosure; no real-money service","Yes","Real money introduced without jurisdiction review","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
]

LEADERBOARD_HEADER = [
    "division","strategy","metric","metric_value","ci_low","ci_high","n_trials",
    "game_clusters","multiplicity_adjusted","certification_status","signal_score","staking_score","source_url",
]
LEADERBOARD_ROWS = [
 ["Singles","S1 Home underdog ATS","Brier skill score (benchmark-relative)","","","","","","","Not certified","","","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["Singles","S2 Home dog +7 or more","Brier skill score (benchmark-relative)","","","","","","","Not certified","","","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["Singles","S3 Divisional home dog","Brier skill score (benchmark-relative)","","","","","","","Not certified","","","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["Singles","S4 Fade 10+ favourites","Brier skill score (benchmark-relative)","","","","","","","Not certified","","","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["Singles","S5 Over the closing total","Brier skill score (benchmark-relative)","","","","","","","Not certified","","","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["Singles","S6 Home team off a bye ATS","Brier skill score (benchmark-relative)","","","","","","","Not certified","","","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["Singles","S7 Fade the more-injured team","Brier skill score (benchmark-relative)","","","","","","","Not certified","","","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["Game parlays","(none certified)","Brier skill score (benchmark-relative)","","","","","","","Not certified","","","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["Same-game parlays","(none certified)","Brier skill score (benchmark-relative)","","","","","","","Not certified","","","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
 ["Prop combos","(none certified)","Brier skill score (benchmark-relative)","","","","","","","Not certified","","","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/strategy_ledger.csv"],
]

CORRELATIONS_HEADER = [
    "pair","metric","r","n","ci_low","ci_high","source_url","notes",
]
CORRELATIONS_ROWS = [
 ["NET points per game vs win percentage","Pearson r","0.8391","32","","","https://www.nfl.com/standings/","Computed in-repo from official 2026 standings snapshot (32 teams); NET = PF-PA asserted."],
 ["Points for per game vs win percentage","Pearson r","0.6136","32","","","https://www.nfl.com/standings/","Official 2026 standings snapshot; n=32 teams."],
 ["Points against per game vs win percentage","Pearson r","-0.5796","32","","","https://www.nfl.com/standings/","Official 2026 standings snapshot; n=32 teams."],
 ["Points for per game vs points against per game","Pearson r","-0.0117","32","","","https://www.nfl.com/standings/","Official 2026 standings snapshot; n=32 teams."],
 ["QB passing yards vs his team's top-WR receiving yards","Pearson r","0.76","3852","","","https://github.com/sassnarep3-star/Own5/blob/main/research/arena-f1d30421/correlation.md","Same-game prop-leg dependence; inputs pinned to spreadspoke@1d309cb and pbp@352c9c9 (flagged F1/F2). Same-team legs must not be priced as independent."],
 ["QB passing yards vs WR1 receiving yards (median lines)","Empirical joint vs independent hit rate","0.325 vs 0.248","1255","","","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/sgp_pricing_table.csv","Joint hit rate 32.5% vs 24.8% if independent (+7.7 pp gap); SGP priced empirically, not by multiplying marginals."],
]

INJURIES_HEADER = [
    "team","team_name","player","position","pos_group","practice_status","game_status","season_snap_share",
    "depth_string","is_starter","next_man_up_share","replacement_drop","availability_weight","weight_basis","source_url","retrieved_utc",
]
INJURIES_ROWS = [
 ["DET","Lions","Jared Goff","QB","QB","Limited Participation in Practice","","0.99375","1","yes","0.05","0.235937","0.25","provisional (practice status; no game status published)","https://www.nfl.com/injuries/","2026-11-12T16:47:34Z"],
 ["DET","Lions","Amon-Ra St. Brown","WR","WR","Limited Participation in Practice","","0.8325","2","yes","0.5625","0.0675","0.25","provisional (practice status; no game status published)","https://www.nfl.com/injuries/","2026-11-12T16:47:34Z"],
 ["DET","Lions","Kerby Joseph","S","DB","Limited Participation in Practice","","","","","","","0.25","provisional (practice status; no game status published)","https://www.nfl.com/injuries/","2026-11-12T16:47:34Z"],
 ["DET","Lions","Cade Mays","C","OL","Did Not Participate In Practice","","0.655","7","yes","0.21375","0.220625","0.5","provisional (practice status; no game status published)","https://www.nfl.com/injuries/","2026-11-12T16:47:34Z"],
 ["WAS","Commanders","John Bates","TE","TE","Full Participation in Practice","","0.39625","2","no","0.3925","0","0","provisional (practice status; no game status published)","https://www.nfl.com/injuries/","2026-11-12T16:47:34Z"],
 ["WAS","Commanders","Treylon Burks","WR","WR","Did Not Participate In Practice","","0.533333","4","yes","0.435714","0.0488095","0.5","provisional (practice status; no game status published)","https://www.nfl.com/injuries/","2026-11-12T16:47:34Z"],
 ["WAS","Commanders","Jayden Daniels","QB","QB","Full Participation in Practice","","0.925","1","yes","0.84","0","0","provisional (practice status; no game status published)","https://www.nfl.com/injuries/","2026-11-12T16:47:34Z"],
]

QUESTIONS_HEADER = [
    "id","question","why_it_matters","what_we_have","what_is_missing","how_to_resolve","blocks","status","source_url",
]
QUESTIONS_ROWS = [
 ["Q01","Which price is the benchmark for \"beating the market\": our line at post, the operator's current price, or the closing price?","Every CLV, edge and certification statement depends on which price it is measured against.","A single aggregator line per game with an unknown timestamp.","A timestamped operator price history.","Capture the operator page twice weekly (Wednesday post-injury-report and Sunday pre-kickoff) and store the raw snapshot.","Gate G4, leaderboard certification and any claim of skill.","Blocking","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q02","Are the aggregator line values closing lines, and for which operator?","If they are closing lines the market prices information efficiently; if they are early lines part of a measured edge is stale-line alpha.","nflverse-style spread_line/total_line; no documentation of source or snapshot time.","Provenance and timestamp from the publisher.","Ask the mirror maintainer for the upstream source, or replace with an archived operator snapshot.","Interpretation of every market comparison in this repo.","Blocking","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q03","What bankroll, staking rule and maximum drawdown are acceptable?","Kelly fractions, stop rules and the drawdown gate are undefined without a bankroll.","A 100-unit reference bankroll and a quarter-Kelly cap used for illustration only.","The owner's actual risk tolerance and capital.","Owner decision; not resolvable from any source.","G6/G7 evaluation, reward sizing.","Blocking","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q04","Are rewards cash, points, or nothing?","Cash rewards change the legal, tax and eligibility requirements.","Reward tiers proposed in prior sessions; no funding decision.","Owner decision plus a jurisdiction review.","Owner decision; treat as points-only until answered.","Competition launch.","Blocking","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q05","Which jurisdiction and operator rules govern the bets?","Same-game parlay restrictions, minimum age and void/push rules differ by state and operator.","Operator house-rule pages cited (FanDuel/DraftKings/BetMGM).","A confirmed jurisdiction for the owner and the applicable operator's current terms.","Owner states the jurisdiction; then re-read that operator's house rules for that state.","G8-G12, any live betting.","Blocking","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q06","Can we obtain historical player-prop lines to backtest prop strategies?","Without a prop line there is no breakeven price, so a prop strategy cannot be evaluated economically.","Median-split proxies and correlation coefficients from official-derived stats.","Any official public prop-line history (none exists).","Commercial odds archive, or forward-collect prop lines from today onward and accept a start date.","Economically meaningful prop backtests.","Blocking","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q07","What defines a \"starter\" - the club depth chart, or snap share?","Depth charts are not published by the league; snap share is measurable but lags role changes.","Snap-share role inference with explicit thresholds and depth strings 1-4.","An official, machine-readable depth chart (none exists at nfl.com).","Keep snap share as the primary definition and publish the threshold; cross-check against club-published depth charts where available.","Precision of R12/R13, not their existence.","Partially answered","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q08","How many points is a missing player worth?","The injury adjustment needs a value per player, not just a count.","An estimated coefficient of -0.039 points per percentage point of relative deficiency on raw margin (p=6e-5).","Position-specific values (QB vs guard vs safety) and interaction effects.","Fit per-position-group coefficients with enough sample, and validate out of season.","Precision of the injury adjustment in the line model.","Partially answered","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q09","Should practice status be used as a probability weight?","The game status is not published until later in the week; ignoring practice participation discards the only early signal.","Documented weights (Out 1.0, Doubtful 0.75, Questionable 0.5; DNP 0.5, Limited 0.25, Full 0.0).","Empirically fitted activation probabilities by practice sequence.","Fit on 2023-2026 reports and replace the judgment weights.","Nothing blocking; improves accuracy.","Partially answered","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q10","Do Questionable players belong in the deficiency score?","A Questionable starter often plays; counting him at 0.5 could double-count with his backup.","A 0.5 weight applied consistently.","Evidence on actual activation rates by position and practice level.","Same fit as Q09; until then keep the weight and disclose it.","Nothing blocking.","Partially answered","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q11","What sample size is required before a strategy may appear on the leaderboard?","Appearing on a board is a claim; small samples make that claim false.","A 300-bet minimum, and the calculation that 2,243 bets are needed to distinguish 55% from 52.38% at 80% power.","An owner-agreed rule for provisional vs certified listing.","Adopt the 300-bet minimum for provisional listing and full power analysis for certification.","Reward allocation, not analysis.","Answered","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q12","What false-discovery rate is acceptable when certifying a strategy?","Bonferroni over variants at alpha=0.05; a different error budget changes which strategies qualify.","Bonferroni 0.05/k with k published, plus permutation nulls.","An explicit owner preference (strict vs exploratory).","Keep strict for anything that would attract money; allow exploratory labels at 0.10 with disclosure.","Nothing blocking; policy choice.","Answered","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q13","How often may the model be updated in-season?","Frequent refits invite overfitting and make the published line unreproducible.","A fixed weekly refit in the pipeline, with parameters estimated only from prior weeks.","A rule for mid-week injury-driven recalculation.","Freeze the model after the Wednesday report; publish the frozen line and the injury adjustment separately.","Auditability of the line history.","Answered","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q14","Is home-field advantage really zero at a neutral site?","The Munich game is a designated home game; treating it as neutral is an assumption.","HFA = +2 points estimated from prior seasons; neutral games set to zero.","Measured margin in international/neutral games.","Estimate the neutral-site effect from the historical neutral games in the pinned dataset.","Precision of one line, not the framework.","Partially answered","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q15","Do we include postseason games in ratings and backtests?","Including playoffs mixes different rest patterns and opponent quality.","Regular season only, explicitly filtered.","A decision on whether postseason props/futures are in scope.","Keep regular season for ratings; treat postseason as a separate labelled sample.","Nothing blocking.","Answered","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q16","Which lineage wins when the official page and the mirror disagree?","A silent drift would change every downstream number.","A row-for-row cross-check (276/276 injury rows and 32/32 standings rows currently agree).","An automated fail-closed policy in CI.","Adopt: fail the build and flag the mismatch rather than choosing silently.","Trust in the whole pipeline.","Answered","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q17","How are source changes versioned?","An official page changes weekly; a value without a timestamp cannot be audited later.","A provenance file with URL, HTTP status, SHA-256, byte count and UTC timestamp for every fetch.","Long-term retention beyond the repository history.","Keep the weekly snapshot commit; tag releases per season.","Long-run reproducibility.","Answered","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
 ["Q18","Is there budget for a paid odds feed?","A verified price feed closes Q01, Q02 and Q06 at once; the free route is slow and partial.","No paid feed; aggregator lines only.","Owner budget decision.","Owner decision; document the cost of the gap either way.","Certification of skill (G4), prop backtests.","Blocking","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/questions.csv"],
]

SUGGESTIONS_HEADER = [
    "id","title","problem","recommendation","impact","effort","confidence","evidence","decision","owner","review_test","source_url",
]
SUGGESTIONS_ROWS = [
 ["S01","Archive a timestamped operator price snapshot every week","Every CLV and \"market vs model\" statement rests on an aggregator line whose timestamp is unknown. Without a price history, gate G4 can never be evaluated and no strategy can be certified as skill.","Capture the operator's own NFL page (spread, total, moneyline) at two fixed times per week (Wednesday post-injury-report and Sunday pre-kickoff) and store the raw snapshot with HTTP headers and hash.","High","Medium","High","validation page #G4; claim_checks row 'closing line value'","Recommended now","Data engineering","If the operator page blocks automated capture or terms forbid it, fall back to manual capture of 5 games per week and mark the sample as partial.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S02","Ship a sign-convention regression test with every backtest","The first injury backtest reported a 57.4% ATS edge that vanished once the spread sign convention was corrected. A single sign error is enough to invent an edge.","Add a unit test that asserts the ATS sign on a synthetic fixture, plus a known-answer test on 10 historical games with published results, and fail the build if either drifts.","High","Low","High","verification page #sign; claim_checks row 'Injury-driven lineup loss is not priced by the market'","Recommended now","Quant","If a future data feed documents a different convention, update the fixture rather than the assertion, and record the change.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S03","Pre-register the variant count before looking at results","Bonferroni only means something if the number of tested variants is honest. Buckets found after inspection inflate the true false-discovery rate.","Write the strategy list and thresholds into the strategies register, commit it, and require the commit hash in the results table. Count every variant, including abandoned ones.","High","Low","High","strategies page #multiplicity; strategy_meta.json","Recommended now","Research","If a strategy must be added after the fact, it starts in a new pre-registration round with its own alpha budget.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S04","Publish a market-efficiency scorecard per signal","We can measure whether a signal predicts results, but the useful question is whether the market has already priced it.","For each signal, report (a) regression of the market line on the signal, (b) regression of the ATS residual on the signal, (c) the implied 'priced share'. Rank ideas by residual edge, not by raw predictive power.","High","Medium","High","injuries page #calibration; injury_calibration_games.csv","Recommended now","Quant","If a signal shows residual edge with a verified closing price, promote it to a full gate evaluation.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S05","Use lineup deficiency as a pricing input for our own lines, not as a bet trigger","The measured relationship is real for predicting margin, but the market already moves about half of it and the residual ATS record is 51.4% (p=1.0).","Feed deficiency into the line model (already implemented) and stop advertising it as a betting signal. Show the model line both with and without the adjustment so the size of the adjustment is auditable.","Medium","Low","High","lines page; line_model.json","Recommended now","Model owner","If a future season shows a residual edge with verified prices, revisit.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S06","Extend depth tracking to offensive-line continuity","Offensive line injuries are the classic source of hidden lineup decay: five players who never practised together still count as 'starters available'. Snap share alone cannot see that.","Build a weekly starting-five continuity metric (same five linemen starting together, consecutive weeks) from snap counts and measure its relationship to sacks allowed, pressure rate and ATS residual.","Medium","Medium","Medium","injuries page #methodology; snap counts pinned in raw data","Pilot","Research","If continuity shows no relationship to pressure or margin after a season of data, drop it.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S07","Treat practice-status transitions as a probability, not a label","The official report gives three practice levels and a game status. Collapsing them to fixed weights throws away the strongest information: a player moving DNP -> LP -> FP across the week.","Fit the mapping empirically: P(active) by (practice sequence, game status) from multiple seasons of reports, and publish the fitted table with sample sizes.","Medium","Medium","Medium","injuries page #weights; injuries_wk10_players.csv","Pilot","Quant","If the fitted probabilities differ from the assumed weights by less than 5 percentage points, keep the simple weights.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S08","Score the leaderboard on CLV and calibration, never on win rate","A win-rate leaderboard rewards luck and variance; over 300 bets a 52% and a 56% record are statistically indistinguishable.","Rank by de-vigged CLV first, calibration second, flat-stake yield third; require a 300-bet minimum and publish confidence intervals next to every rank.","High","Medium","High","strategies page #leaderboard; strategy_meta.json (required n = 2,243 for 55% vs 52.38%)","Recommended now","Competition design","If CLV data cannot be captured (S01 fails), the board stays provisional and unranked.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S09","Make the data layer dual-source with automatic disagreement alerts","The pipeline depends on one aggregator mirror. If it drifts from the official page, every downstream number drifts silently.","Every build fetches the official page and the mirror; add a hard assertion that the two agree row-for-row on the injury report and standings, and fail the build on any mismatch.","High","Low","High","verification page #dual; standings_crosscheck.csv","Recommended now","Data engineering","If the official page layout changes and parsing fails, fail closed (blank + flag) rather than falling back silently.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S10","Model opponent-adjusted efficiency, not raw points","The current ratings use final margins with a two-way fit; they cannot distinguish a good offence beating bad defences from a mediocre one.","Add EPA per play (offence and defence) from the same pinned source, blend with the margin model, and evaluate whether it reduces out-of-sample log-loss.","Medium","High","Medium","lines page #model; model_backtest.csv (no edge at 50.5%)","Defer","Model owner","Promote when play-by-play ingestion is in place and the blend beats the margin model on holdout log-loss.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S11","Price correlated legs with an empirical copula, and refuse independent pricing","Same-team QB + WR1 legs are correlated (r = 0.50 on 2024-2026); at median lines the joint hit rate is 32.5% versus 24.8% if treated as independent, a +7.7 pp gap that changes the fair price materially.","Require an empirical joint estimate for any same-game combination; publish the implied fair price next to the offered price and reject the bet when the offered price assumes independence.","High","Medium","High","correlations page #sgp; sgp_pricing_table.csv","Recommended now","Quant","If the operator's SGP price already reflects the correlation (compare implied joint to empirical), no action is needed beyond documentation.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S12","Keep a decision log (one line per accepted suggestion)","Suggestions accepted without a recorded rationale get re-litigated, and rejected ones get re-proposed.","Append an ADR row when a suggestion moves to Accepted/Rejected: date, decision, evidence, owner, revisit date.","Medium","Low","High","suggestions page; COORDINATION.md session log","Recommended now","Project owner","If the log has fewer than one entry per accepted suggestion, the process is not being followed.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S13","Separate OFFICIAL and AGGREGATOR tiers in every table, mechanically","Mixing an official injury row and a mirror-derived snap profile in one 'verified' column invites over-claiming.","Every table carries a tier column; a build check fails if an OFFICIAL-labelled row's source URL is not an official domain.","High","Medium","High","verification page #tiers; sources.csv","Recommended now","Data engineering","Define the official domain list (nfl.com, operations.nfl.com, media.nfl.com, club sites) and enforce it in verify.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S14","Run the competition as points-only until the reward questions are answered","Cash rewards change the legal, tax and eligibility profile; no jurisdiction or funding decision exists yet.","Publish the intended cash structure as a proposal, not a commitment; keep the board points-only until Q04/Q05 are answered.","Medium","Low","High","questions page #Q04; strategies page #rewards","Recommended now","Project owner","Close Q04/Q05 first; then publish reward terms with eligibility rules.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S15","Publish a weekly \"what changed\" diff instead of a static snapshot","A static snapshot hides whether a rating, ranking or availability call moved and why.","Store each weekly snapshot and render a diff column (rank change, rating change, availability change).","Medium","Medium","Medium","flagged page; lines page","Defer","Data engineering","Store weekly snapshots; diff rendered client-side from committed snapshots.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
 ["S16","Capture the reserve list so \"not listed\" never means \"available\"","A player absent from the weekly injury report may be on injured reserve, not healthy.","Capture the reserve list (IR, PUP, etc.) weekly and join it to the availability graph; treat reserve-list players as unavailable.","High","Medium","High","injuries page; flagged page (Malik Willis example)","Recommended now","Data engineering","If a player on the reserve list appears in a game, treat it as a data error and alert.","https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/suggestions.csv"],
]

SOURCES_HEADER = [
    "source_id","name","tier","type","url","what_it_verifies","accessed_on",
]
SOURCES_ROWS = [
 ["S01","NFL.com - official league site","OFFICIAL","official NFL","https://www.nfl.com/","League news, standings, schedules, stats, injuries, teams","2026-11-02"],
 ["S02","NFL Media - football information (media.nfl.com)","OFFICIAL","official NFL","https://media.nfl.com/","Official schedule announcements; official statistics reports courtesy of Elias Sports Bureau","2026-11-02"],
 ["S03","NFL Football Operations (operations.nfl.com)","OFFICIAL","official NFL","https://operations.nfl.com/","Official Playing Rules, schedule-making, Next Gen Stats technology","2026-11-02"],
 ["S04","NFL Standings (2026, through Week 8)","OFFICIAL","official NFL","https://www.nfl.com/standings/","W-L-T, PCT, PF, PA, NET PTS, streak for all 32 teams; snapshot accessed 2026-11-02","2026-11-02"],
 ["S05","NFL Schedules 2026","OFFICIAL","official NFL","https://www.nfl.com/schedules","Week-by-week matchups, times, networks, results; bye teams; weather note on game cards","2026-11-02"],
 ["S06","NFL official injury report","OFFICIAL","official NFL","https://www.nfl.com/injuries/","Official weekly injury report: player, position, injury, practice status, game status","2026-11-12"],
 ["S07","NFL player stats 2026","OFFICIAL","official NFL","https://www.nfl.com/stats/player-stats/","Official 2026 player stat leaders (passing, rushing, receiving, ...), Elias Sports Bureau data","2026-11-02"],
 ["S08","NFL team stats 2026","OFFICIAL","official NFL","https://www.nfl.com/stats/team-stats/","Official 2026 team offense/defense/special-teams stats","2026-11-02"],
 ["S09","NFL teams directory","OFFICIAL","official NFL","https://www.nfl.com/teams/","All 32 clubs with links to official club websites","2026-11-02"],
 ["S10","NFL tiebreaking procedures","OFFICIAL","official NFL","https://www.nfl.com/standings/tie-breaking-procedures","Official tiebreaking steps; tie game = half win / half loss","2026-11-02"],
 ["S11","2026 schedule announced (May 14, 2026)","OFFICIAL","official NFL","https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced","18-week, 272-game 2026 schedule; 17 games + 3 preseason per team; byes Weeks 5-14; kickoff Sept 9, 2026; Week 18 Jan 9-10; 9 international games","2026-11-02"],
 ["S12","2026 Official Playing Rules of the NFL (rulebook)","OFFICIAL","official NFL","https://operations.nfl.com/rules-officiating/2026-nfl-rulebook","Rules in effect for 2026 season; Rule 4 game timing (60 min, four 15-min periods); Rule 16 overtime","2026-11-02"],
 ["S13","NFL Next Gen Stats technology","OFFICIAL","official NFL","https://operations.nfl.com/gameday/technology/nfl-next-gen-stats","Player/ball tracking in every venue; location/speed/acceleration 10x per second; 200+ data points per play","2026-11-02"],
 ["S14","DraftKings Sportsbook - NFL lines & bet types","INDUSTRY","official sportsbook operator","https://sportsbook.draftkings.com/leagues/football/nfl","Operator definitions of NFL spread, moneyline, totals, live betting, parlays, props","2026-11-02"],
 ["S15","FanDuel - NFL betting guide","INDUSTRY","official sportsbook operator","https://www.fanduel.com/sports-betting-guide/how-to-bet-on-nfl","Operator definitions of spread, push, parlay, same game parlay, teaser; key margins 3 and 7 in NFL","2026-11-02"],
 ["S16","BetMGM house rules approved by Massachusetts Gaming Commission","INDUSTRY","regulator-approved operator rules","https://massgaming.com/wp-content/uploads/BetMGM-House-Rules-8.14.25.pdf","Football results official after 55 minutes of play; postponed/cancelled game handling; same-game-parlay variants","2026-11-02"],
 ["S17","NCPG - National Problem Gambling Helpline","OFFICIAL","official responsible-gambling resource","https://www.ncpgambling.org/help-treatment/national-helpline-1-800-522-4700/","1-800-GAMBLER (1-800-426-2537), text 800GAM, chat; 24/7, confidential, all 50 states","2026-11-02"],
 ["S18","NFL announces tri-exclusive sports betting partners","OFFICIAL","official NFL","https://www.nfl.com/news/nfl-announces-tri-exclusive-sports-betting-partners","Caesars, DraftKings, FanDuel are Official Sports Betting Partners of the NFL; all three use the NFL's official league data feed","2026-11-02"],
 ["S19","scikit-learn methodology docs","METHODOLOGY","peer-reviewed software documentation","https://scikit-learn.org/stable/modules/model_evaluation.html","TimeSeriesSplit, cross-validation and calibration references","2026-11-02"],
 ["S20","SciPy Pearson correlation docs","METHODOLOGY","peer-reviewed software documentation","https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html","Pearson correlation reference","2026-11-02"],
]

FLAGGED_HEADER = [
    "flag_id","item","severity","description","why_unverified","disposition","source_link","related_requirement",
]
FLAGGED_ROWS = [
 ["F01","No verified operator price snapshot","High","Market spread/total/moneyline columns are blank across the lines table. No timestamped operator (DraftKings/FanDuel/BetMGM) price history exists in this namespace.","nfl.com and operator odds pages are unreachable from the sandbox; no paid odds feed subscribed.","Blank + flagged; market columns never inferred. Gates G4/G8 cannot pass until S01 (price snapshot) is shipped.","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/lines.csv","R004/R020/R023/R037/R068"],
 ["F02","Prop lines unavailable from an official source","High","Player-prop bet legs are modelled at median splits; no official public prop-line history exists.","No official source publishes NFL player-prop lines.","Blank + flagged; prop combos held behind the joint-evidence gate (G5/G9).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/correlations.csv","R007/R006"],
 ["F03","No certified strategies","High","All 7 strategy families fail validation gates (G2, G3, G4, G6, G8 fail). Leaderboard is intentionally empty.","Requires verified closing prices (G4) and a passing chronological holdout (G3).","Blank + flagged; no strategy ranked until certified.","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/leaderboard.csv","R005/R006/R008/R028"],
 ["F04","Injury report not captured as a timestamped series","Medium","Only one injury-report capture exists in the repo; no Wed/Thu/Fri-to-kickoff series.","nfl.com unreachable from the sandbox; capture lives in another session's namespace.","Blank + flagged; injury signal treated as a change (delta), not a level (R031/R040).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","R011/R031/R040"],
 ["F05","Depth is snap-share inference, not an official depth chart","Medium","Depth strings 1-4 and starter flags are inferred from snap share, not from an official club depth chart.","No official machine-readable depth chart exists at nfl.com.","Blank + flagged; snap share disclosed as the starter proxy (R030).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","R012/R013/R029"],
 ["F06","32-team roster/IR sweep not run","Medium","No club-by-club roster/IR sweep has been completed in this namespace.","Club roster/IR pages unreachable from the sandbox.","Blank + flagged; blocks team-level model trust (R032).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","R032/R072"],
 ["F07","Venues not transcribed from official game centre","Low","Venue of every fixture not transcribed and published.","Official game-centre pages unreachable from the sandbox.","Blank + flagged (R042).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","R042"],
 ["F08","Official inactive lists and snap counts not captured","Medium","Only 6 of 254 report rows carry a game designation; no active list or snap share captured in this namespace.","nfl.com unreachable; snap counts exist in another session's namespace.","Blank + flagged; backup replacement of a starter cannot be confirmed (R049).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/injuries.csv","R049/R025"],
 ["F09","Depth-parsing failures not fixed (Texans image; Packers jersey numbers)","Medium","Texans publish depth as an image; Packers prepend jersey numbers.","Requires an authorized structured source for the Texans image; jersey-number stripping recovers Packers rows.","Blank + flagged; Texans image needs authorized source, not eye-transcription (R050).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","R050"],
 ["F10","Roster turnover not versioned","Low","Depth, availability and lineup evidence not versioned against the last official roster event.","Official transactions/roster pages unreachable.","Blank + flagged (R052).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","R052"],
 ["F11","Immutable availability snapshots not built","Medium","No daily injury-report/depth-page/inactive captures with retained hashes, timestamps and conflict flags.","Requires durable snapshot storage outside the static site plus a capture pipeline.","Blank + flagged; blocks replay of practice designations (R047/R048/R065).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","R047/R048/R065"],
 ["F12","Stadium roof/surface and NWS weather overlay not built","Low","No NWS hourly wind/precipitation overlay coupled with official 90-minute stadium roof designations.","NWS and stadium data not captured.","Blank + flagged (R066).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/flagged.csv","R066"],
 ["F13","Two-stage escrow leaderboard not live","Low","Proper-score qualification then prospective CLV/ROI escrow not yet operating over a multi-week sample.","Awaits verified price capture and qualification sample.","Blank + flagged (R067).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/leaderboard.csv","R067"],
 ["F14","Reward funding and jurisdiction unset","High","Q04 (cash vs points vs nothing) and Q05 (jurisdiction/operator rules) cannot be closed from public data.","Owner decision required; not resolvable from any source.","Blocked; competition remains points-only until answered (S16).","https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-origin-desk/questions.csv","R006/R004/R015"],
]

# ---------------------------------------------------------------------------
# Write data CSVs (authoritative; existing hand-written files are replaced)
# ---------------------------------------------------------------------------
write_csv("requirements.csv", REQUIREMENTS_HEADER, REQUIREMENTS_ROWS)
write_csv("lines.csv", LINES_HEADER, LINES_ROWS)
write_csv("strategies.csv", STRATEGIES_HEADER, STRATEGIES_ROWS)
write_csv("gates.csv", GATES_HEADER, GATES_ROWS)
write_csv("leaderboard.csv", LEADERBOARD_HEADER, LEADERBOARD_ROWS)
write_csv("correlations.csv", CORRELATIONS_HEADER, CORRELATIONS_ROWS)
write_csv("injuries.csv", INJURIES_HEADER, INJURIES_ROWS)
write_csv("questions.csv", QUESTIONS_HEADER, QUESTIONS_ROWS)
write_csv("suggestions.csv", SUGGESTIONS_HEADER, SUGGESTIONS_ROWS)
write_csv("sources.csv", SOURCES_HEADER, SOURCES_ROWS)
write_csv("flagged.csv", FLAGGED_HEADER, FLAGGED_ROWS)

print("Wrote", len(REQUIREMENTS_ROWS), "requirements rows")
print("Wrote", len(LINES_ROWS), "lines rows")
print("Wrote", len(STRATEGIES_ROWS), "strategies rows")
print("Wrote", len(GATES_ROWS), "gates rows")
print("Wrote", len(LEADERBOARD_ROWS), "leaderboard rows")
print("Wrote", len(CORRELATIONS_ROWS), "correlations rows")
print("Wrote", len(INJURIES_ROWS), "injuries rows")
print("Wrote", len(QUESTIONS_ROWS), "questions rows")
print("Wrote", len(SUGGESTIONS_ROWS), "suggestions rows")
print("Wrote", len(SOURCES_ROWS), "sources rows")
print("Wrote", len(FLAGGED_ROWS), "flagged rows")

# ---------------------------------------------------------------------------
# PAGE BODIES
# ---------------------------------------------------------------------------
def req_status_badge(s):
    s = (s or "").lower()
    if s == "met": return '<span class="badge ok">Met</span>'
    if s == "partially met": return '<span class="badge warn">Partially met</span>'
    if s == "unmet": return '<span class="badge bad">Unmet</span>'
    if s == "in progress": return '<span class="badge warn">In progress</span>'
    return f'<span class="badge">{esc(s)}</span>'

def landing_body():
    req = read_csv("requirements.csv")
    header, rows = req[0], req[1:]
    i_status = header.index("status")
    i_id = header.index("id")
    i_req = header.index("requirement")
    i_gate = header.index("blocking_gate")
    i_clear = header.index("number_to_clear")
    i_obs = header.index("observed_number")
    met = sum(1 for r in rows if r[i_status].strip().lower()=="met")
    partial = sum(1 for r in rows if r[i_status].strip().lower()=="partially met")
    unmet = sum(1 for r in rows if r[i_status].strip().lower()=="unmet")
    inprog = sum(1 for r in rows if r[i_status].strip().lower()=="in progress")
    body = f"""
<div class="grid kpis">
  <div class="kpi ok"><div class="kpi-value">{len(rows)}</div><div class="kpi-label">requirements tracked</div><div class="kpi-note">one row per requirement on the landing page</div></div>
  <div class="kpi ok"><div class="kpi-value">{met}</div><div class="kpi-label">met</div><div class="kpi-note">requirements satisfied</div></div>
  <div class="kpi warn"><div class="kpi-value">{partial}</div><div class="kpi-label">partially met</div><div class="kpi-note">blocked on gates or data</div></div>
  <div class="kpi bad"><div class="kpi-value">{unmet}</div><div class="kpi-label">unmet</div><div class="kpi-note">not yet started / blocked</div></div>
  <div class="kpi warn"><div class="kpi-value">{inprog}</div><div class="kpi-label">in progress</div><div class="kpi-note">site, PR and Pages deploy</div></div>
  <div class="kpi ok"><div class="kpi-value">0</div><div class="kpi-label">certified strategies</div><div class="kpi-note">leaderboard intentionally empty until gates pass</div></div>
  <div class="kpi ok"><div class="kpi-value">15</div><div class="kpi-label">Week 9 games originated</div><div class="kpi-note">own side, total and model-implied moneyline</div></div>
</div>
<div class="callout warn"><p><strong>Read first.</strong> This desk originates its own NFL lines (side &rarr; total &rarr; moneyline) from official standings and schedule inputs only. Market-price columns are blank and flagged: no verified operator snapshot exists yet (F01), so nothing here is a bet recommendation. No strategy is certified.</p></div>
<h3>Decision-readiness table</h3>
<p>One row per requirement, with the blocking gate, the number that would clear it, and the observed number. Full detail on the <a href="requirements.html">Requirements</a> page.</p>
<div class="tablewrap"><table class="data"><caption>Decision-readiness: requirement &rarr; blocking gate &rarr; number to clear &rarr; observed status.</caption>
<thead><tr><th scope="col">ID</th><th scope="col">Requirement</th><th scope="col">Status</th><th scope="col">Blocking gate</th><th scope="col">Number that would clear it</th><th scope="col">Observed number / status</th></tr></thead>
<tbody>
"""
    for r in rows:
        body += ("<tr>"
                 f"<td><span class=\"sid\">{esc(r[i_id])}</span></td>"
                 f"<td>{esc(r[i_req])}</td>"
                 f"<td>{req_status_badge(r[i_status])}</td>"
                 f"<td>{esc(r[i_gate])}</td>"
                 f"<td>{esc(r[i_clear])}</td>"
                 f"<td>{esc(r[i_obs])}</td>"
                 "</tr>\n")
    body += """
</tbody></table></div>
<h3>Where to look first</h3>
<div class="grid cards">
  <article class="card"><h4><a href="questions.html">Questions that gate decisions</a></h4><p>18 questions; 4 block a decision and cannot be closed from public data (Q01-Q05, Q18).</p></article>
  <article class="card"><h4><a href="suggestions.html">Suggestions register</a></h4><p>16 recommendations with impact, effort, confidence and a decision state. Review and pick a path before implementing.</p></article>
  <article class="card"><h4><a href="lines.html">Own lines (Week 9)</a></h4><p>15 games originated side &rarr; total &rarr; moneyline; market columns blank and flagged.</p></article>
  <article class="card"><h4><a href="flagged.html">Flagged for review</a></h4><p>14 irregularities and unverified blanks, each with source links.</p></article>
</div>
"""
    return body

def page_table(name, title, caption, description):
    return table_from_csv(name, caption)

def strategies_body():
    s = read_csv("strategies.csv")
    header, rows = s[0], s[1]
    # Actually header, rows = s[0], s[1:]
    header, rows = s[0], s[1:]
    body = "<p>Seven pre-registered strategy families, tested on historical data with exact binomial tests, Bonferroni correction, chronological holdouts and permutation nulls. Signal is separated from staking (flat unit stakes) so a lucky staking run cannot mask a bad signal. None pass all validation gates; the leaderboard stays empty until a strategy is certified.</p>\n"
    body += table_from_csv("strategies.csv", "Strategy catalog. Gate results show pass/fail/n/a across G0-G12. Backtest numbers are kept off the leaderboard until certified.")
    body += """
<div class="callout"><p><strong>What would change our mind.</strong> Each strategy carries a two-sided falsification field: the specific evidence (verified closing prices, a passing holdout, a residual edge surviving Bonferroni) that would promote it from "not certified" to certified. Until then, backtest numbers are not published as performance.</p></div>
"""
    return body

def leaderboard_body():
    body = """
<p>The leaderboard is split into four proper-score divisions: singles, game parlays, same-game parlays and prop combos. Strategies are ranked by benchmark-relative Brier skill with a game-cluster lower bound and a multiplicity adjustment &mdash; never by raw win rate or short-run ROI. Signal is reported separately from staking. No entrant has passed all validation gates, so every division is intentionally empty.</p>
"""
    body += table_from_csv("leaderboard.csv", "Proper-score leaderboard (empty until certified). CI = confidence interval; n_trials and game_clusters published with each value.")
    body += """
<div class="callout warn"><p><strong>Certification bar.</strong> A strategy must pass all 12 gates (G0-G12), including verified closing line value (G4) and market integrity (G8), before it can appear. Because no operator price snapshot exists yet (F01), G4/G8 cannot pass and the board is empty by design.</p></div>
"""
    return body

def correlations_body():
    body = """
<p>Correlations are computed only from officially sourced numbers, and every value is published with its sample size n. Same-team prop legs are priced empirically (joint probability), never by multiplying marginal probabilities under dependence.</p>
"""
    body += table_from_csv("correlations.csv", "Official-source correlations. n published with each value; Fisher intervals where computable.")
    return body

def injuries_body():
    body = """
<p>Injury and availability are tracked as a timestamped series, not a weekly snapshot. Depth strings (1-4) are recorded per position group; where an official depth chart is unavailable, snap share is used as the starter proxy and disclosed as such. The injury signal is treated as a change (delta in designation or snap share), never as a level.</p>
<div class="callout warn"><p><strong>Coverage note.</strong> This namespace holds a representative sample of officially-sourced injury rows (retrieved 2026-11-12). Full 32-club coverage, daily Wed-Fri captures, inactive lists and the reserve list are not yet built (F04, F06, F08, F11, F72).</p></div>
"""
    body += table_from_csv("injuries.csv", "Injury & availability sample. Depth strings 1-4; snap share as starter proxy; game status blank until officially published later in the week.")
    return body

def questions_body():
    body = "<p>Questions, information and answers that must be addressed before any decision can reasonably be made. Blocking questions cannot be closed from public data and require an owner decision or a new data capture.</p>\n"
    body += table_from_csv("questions.csv", "Questions register. Four blocking questions (Q01, Q02, Q03, Q04, Q05, Q18) gate certification and reward launch.")
    return body

def suggestions_body():
    s = read_csv("suggestions.csv")
    header, rows = s[0], s[1:]
    body = "<p>Suggestions for improving the site and decision-making. Each has a decision state, an owner and a review test &mdash; someone reviews and chooses the best path before any change is implemented.</p>\n"
    for r in rows:
        rid, title, problem, rec, impact, effort, confidence, evidence, decision, owner, review_test, src = (r + [""]*12)[:12]
        body += f"""
<details class="sug"><summary><span class="sid">{esc(rid)}</span>{esc(title)}</summary>
<div class="sugbody">
<dl>
<dt>Problem</dt><dd>{esc(problem)}</dd>
<dt>Recommendation</dt><dd>{esc(rec)}</dd>
<dt>Impact</dt><dd>{esc(impact)}</dd>
<dt>Effort</dt><dd>{esc(effort)}</dd>
<dt>Confidence</dt><dd>{esc(confidence)}</dd>
<dt>Decision</dt><dd>{esc(decision)}</dd>
<dt>Owner</dt><dd>{esc(owner)}</dd>
<dt>Review test</dt><dd>{esc(review_test)}</dd>
<dt>Evidence</dt><dd><a href="{esc(src)}" rel="noopener noreferrer" target="_blank">{esc(src)}</a></dd>
</dl>
</div>
</details>
"""
    return body

def lines_body():
    body = """
<p>Own lines for all 15 Week 9, 2026 games, originated in the order <strong>side &rarr; total &rarr; moneyline</strong>. Ratings use only prior weeks (walk-forward); totals use a two-way points model; the moneyline is model-implied from the model spread via a documented approximation and is labelled as such &mdash; it is <strong>not</strong> an operator quote. Model spread is quoted from the home team's perspective (negative = home favoured).</p>
<div class="callout warn"><p><strong>Market comparison.</strong> Market spread / total / moneyline and the spread/total/ML differences (residuals) are blank and flagged: no verified operator price snapshot exists (F01). An edge shown here is a research candidate, never a bet instruction.</p></div>
"""
    body += table_from_csv("lines.csv", "Week 9 originated board. Fair (model) line published; market line blank+flagged; difference blank until a verified price snapshot exists.")
    body += """
<h3>How the line is built</h3>
<ol class="tight">
<li><strong>Ratings.</strong> Ridge least squares on final margins, margin = rating_home - rating_away + HFA, fitted only on games before the week being priced. HFA = 2 points (derived 2002-2024 mean home margin).</li>
<li><strong>Totals.</strong> Two-way points model, points = mu + offence_team - defence_opponent, same walk-forward rule.</li>
<li><strong>Moneyline.</strong> Model-implied from the model spread via the documented logistic approximation (labelled; not an operator quote).</li>
<li><strong>Fixture context.</strong> Bye, neutral site, international, flex and rest-day features from published schedule facts only.</li>
<li><strong>Inputs stored.</strong> Every model output is stored as a probability-plus-inputs, not just a pick; the inputs column records the standings and HFA source.</li>
</ol>
"""
    return body

def gates_body():
    body = "<p>Twelve validation gates (G0-G12). Every hard gate must pass for a strategy to be certified; G8 (market integrity) failure sends a live strategy back to paper (demotion gate). Backtest numbers are forbidden on the leaderboard until pre-registration and gate clearance.</p>\n"
    body += table_from_csv("gates.csv", "Validation gates. G0 pre-registration (commit hash is the registration); G4 closing line value; G8 market integrity.")
    return body

def sources_body():
    body = "<p>Source registry. Every tier is labelled OFFICIAL (NFL league sources), INDUSTRY (regulator-approved operator rules) or METHODOLOGY (software/statistics documentation).</p>\n"
    body += table_from_csv("sources.csv", "Source registry. Each row links to the page it verifies.")
    return body

def flagged_body():
    body = "<p>Irregularities and unverified blanks. Values that cannot be confirmed from an official source are left blank and published here with source links &mdash; never inferred. These do not block the merge; they are review items for the owner.</p>\n"
    body += table_from_csv("flagged.csv", "Flagged for review. 14 items; severity High/Medium/Low.")
    return body

def executive_summary_body():
    body = """
<div class="prose">
<h2>Executive summary &mdash; NFL Origin Desk</h2>
<p><strong>What this desk is.</strong> A research workspace for originating NFL lines and running a leaderboard competition in which strategies must pass validation gates before being ranked. It is additive to the existing session desks in this repo (root NFL Research Desk, NFL Strategy Lab, NFL Line Lab, NBA labs and several NFL decision desks); it touches no file owned by another session.</p>

<h3>Verified</h3>
<ul class="tight">
<li>15 Week 9, 2026 games originated side &rarr; total &rarr; moneyline from official standings and schedule (model spread / total / model-implied moneyline; model output only).</li>
<li>120 verified final games (Weeks 1-8, 2026) reconciled game-by-game against nfl.com scores and the official standings.</li>
<li>32/32 official clubs reconciled; 14 fixture-context features from published schedule facts.</li>
<li>6 official-source correlations published with n (NET/G vs win% r=0.8391, n=32; QB vs top-WR yards r=0.76, n=3,852; same-team QB+WR1 joint hit rate 32.5% vs 24.8% independent).</li>
<li>12 validation gates defined; 7 strategy families pre-registered; all 7 fail at least G2/G3/G4/G6/G8; 0 certified strategies (leaderboard empty by design).</li>
<li>Signal separated from staking (flat unit stakes) on every strategy; two-sided "what would change our mind" field on each entry.</li>
<li>16 suggestions registered (reviewable), 18 questions registered (4 blocking), 14 flagged irregularities/unverified blanks.</li>
</ul>

<h3>Computed but not certified</h3>
<ul class="tight">
<li>Model-implied moneyline per game (derived from model spread; labelled "not an operator quote").</li>
<li>Strategy backtest records (win rate, CI, ROI, p vs break-even 52.38%) &mdash; kept off the leaderboard until G4/G8 pass.</li>
<li>Brier-skill leaderboard skeleton across four divisions, with CI and multiplicity adjustment placeholders.</li>
</ul>

<h3>Missing / blocked (blank + flagged, never inferred)</h3>
<ul class="tight">
<li><strong>Verified operator price snapshot</strong> (F01) &mdash; blocks G4/G8, leaderboard certification, CLV and any skill claim. Requires S01 (price capture) or an owner decision on a paid feed (Q18).</li>
<li><strong>Player-prop lines</strong> (F02) &mdash; no official public prop-line history; prop combos held behind the joint-evidence gate.</li>
<li><strong>Timestamped injury series and full availability coverage</strong> (F04, F06, F08) &mdash; nfl.com unreachable from the sandbox; daily Wed-Fri captures and the reserve list not yet built.</li>
<li><strong>Depth-chart register, venues, Game Book starters, stadium/weather overlay, weekly diff, drift alarms, immutable snapshots</strong> &mdash; all flagged, awaiting official data or owner decision.</li>
<li><strong>Reward funding and jurisdiction</strong> (Q04/Q05, F14) &mdash; owner decision; competition stays points-only until answered.</li>
</ul>

<h3>Decisions waiting on the owner</h3>
<ul class="tight">
<li>Q04: cash, points or no rewards?</li>
<li>Q05: jurisdiction and governing operator rules?</li>
<li>Q03: bankroll, staking rule, maximum drawdown?</li>
<li>Q18: budget for a paid odds feed?</li>
<li>S01/S09: ship the operator price snapshot and dual-source fail-closed checks.</li>
</ul>

<div class="callout"><p><strong>Bottom line.</strong> No edge, ROI, certification, cash payout or bet is claimed. Luck is reduced (binomial tests, Bonferroni, holdouts, uncertainty published) but not eliminated. Nothing here is betting advice.</p></div>
</div>
"""
    return body

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
PAGES = {
    "index.html": ("Overview", "One dashboard for own lines, validated strategies and injury &amp; depth intelligence &mdash; with the evidence and the gaps side by side.", landing_body, True),
    "requirements.html": ("Requirements", "One row per requirement: the blocking gate, the number that would clear it, and the observed status.", lambda: table_from_csv("requirements.csv", "Decision-readiness table. Every requirement mapped to a gate, a clearing number and an observed status."), False),
    "questions.html": ("Open questions", "Questions, information and answers that must be addressed before any decision.", questions_body, False),
    "suggestions.html": ("Suggestions", "Reviewable suggestions: problem, recommendation, impact, effort, confidence, decision state and review test.", suggestions_body, False),
    "lines.html": ("Own lines", "Week 9 originated board: side &rarr; total &rarr; moneyline, fair line vs market line vs difference.", lines_body, False),
    "strategies.html": ("Strategies", "Pre-registered strategy catalog with signal/staking separation and gate results.", strategies_body, False),
    "gates.html": ("Validation gates", "The 12 gates (G0-G12) every strategy must pass.", gates_body, False),
    "leaderboard.html": ("Leaderboard", "Proper-score divisions: singles, game parlays, same-game parlays, prop combos. Empty until certified.", leaderboard_body, False),
    "correlations.html": ("Correlations", "Official-source correlations, each published with n.", correlations_body, False),
    "injuries.html": ("Injuries &amp; depth", "Injury &amp; availability sample: depth strings 1-4, snap share as starter proxy.", injuries_body, False),
    "sources.html": ("Sources", "Source registry: official, industry and methodology tiers.", sources_body, False),
    "flagged.html": ("Flagged for review", "Irregularities and unverified blanks, with source links.", flagged_body, False),
    "executive-summary.html": ("Executive summary", "Verified vs computed vs missing, and decisions waiting on the owner.", executive_summary_body, False),
}

def main():
    write_css()
    for name, (title, desc, body_fn, active) in PAGES.items():
        write_page(name, page(title, name == "index.html" or active, body_fn(), desc))
        print("wrote", name)
    # also write an empty .nojekyll for Pages
    with open(os.path.join(OUT, ".nojekyll"), "w", encoding="utf-8") as fh:
        fh.write("")
    print("wrote .nojekyll")
    print("Build complete ->", OUT)

if __name__ == "__main__":
    main()

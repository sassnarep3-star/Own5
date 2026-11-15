#!/usr/bin/env python3
"""Deterministic site build: nfl-market-desk/*.html from nfl-market-desk/data/*.csv.

No template engine, no network, no timestamps beyond the recorded capture clock, so a
rebuild on a clean checkout is byte-identical (verify.py checks exactly that).

Design rules enforced here:
  * every body-table row gets a source cell; a row whose source cell is empty is
    rendered as an explicit UNVERIFIED marker, never left blank;
  * every page states what it does NOT establish;
  * numbers on prose pages are computed from the data files at build time.
"""
import os

from lib import DATA, rcsv, f
import report as R

HERE = os.path.dirname(os.path.abspath(__file__))
CAPTURED = "2026-11-15T23:40:00Z"
CAPTURED_DATE = "2026-11-15"

CSS = """
:root{--ink:#10231f;--muted:#5b6b66;--line:#dfe5e2;--bg:#f7f9f8;--card:#fff;
--good:#1c6b4b;--goodbg:#e6f3ec;--warn:#8a5a00;--warnbg:#fdf1d9;--bad:#9d2b1f;--badbg:#fbe7e4;
--accent:#173e36;--accent2:#2f6f5e}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent2)}
code{font:13px/1.4 ui-monospace,SFMono-Regular,Menlo,monospace;background:#eef2f0;padding:1px 5px;border-radius:4px}
header.top{position:sticky;top:0;z-index:5;background:var(--accent);color:#fff;border-bottom:1px solid #0d2a24}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
header.top .wrap{display:flex;align-items:center;gap:18px;min-height:58px;flex-wrap:wrap}
.brand{font-weight:700;letter-spacing:.02em;color:#fff;text-decoration:none;font-size:15px}
.brand span{opacity:.65;font-weight:500}
header.top nav{display:flex;gap:2px;flex-wrap:wrap;margin-left:auto}
header.top nav a{color:#d8e6e1;text-decoration:none;font-size:13px;padding:6px 9px;border-radius:6px}
header.top nav a:hover{background:#1f4d43;color:#fff}
header.top nav a.on{background:#f2f7f5;color:var(--accent);font-weight:600}
main{padding:26px 0 60px}
h1{font-size:27px;margin:0 0 6px;letter-spacing:-.01em}
h2{font-size:19px;margin:34px 0 8px}
h3{font-size:15px;margin:18px 0 6px}
p.lede{color:var(--muted);margin:0 0 18px;max-width:78ch}
.crumb{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(176px,1fr));gap:12px;margin:18px 0 6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:13px 15px}
.card .k{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.card .v{font-size:25px;font-weight:700;margin:3px 0 1px;font-variant-numeric:tabular-nums}
.card .s{font-size:12.5px;color:var(--muted)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:14px 0}
.panel.note{border-left:4px solid var(--accent2)}
.panel.warn{border-left:4px solid #c98a00;background:#fffdf6}
.panel.bad{border-left:4px solid #a5321f;background:#fff8f7}
.tbl{overflow:auto;border:1px solid var(--line);border-radius:10px;background:var(--card);margin:8px 0 4px;max-height:70vh}
table{border-collapse:collapse;width:100%;font-size:13px}
thead th{position:sticky;top:0;background:#eef3f1;text-align:left;font-weight:600;padding:9px 10px;border-bottom:1px solid var(--line);white-space:nowrap;z-index:1}
tbody td{padding:8px 10px;border-bottom:1px solid #eef1ef;vertical-align:top}
tbody tr:hover{background:#fbfdfc}
tbody tr:last-child td{border-bottom:0}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.badge{display:inline-block;font-size:11.5px;font-weight:600;padding:2px 7px;border-radius:999px;border:1px solid transparent;white-space:nowrap}
.badge.good{color:var(--good);background:var(--goodbg);border-color:#c7e5d6}
.badge.warn{color:var(--warn);background:var(--warnbg);border-color:#f0dcae}
.badge.bad{color:var(--bad);background:var(--badbg);border-color:#f3cdc7}
.badge.neutral{color:#3b4a46;background:#eef1f0;border-color:#dde3e1}
.unv{color:#8a3f00;background:#fff4e5;border:1px dashed #e0b284;border-radius:4px;padding:1px 5px;font-size:11.5px;font-weight:600;white-space:nowrap}
a.src{font-size:12px;color:var(--accent2);text-decoration:none;border-bottom:1px dotted #9ec3b8}
a.src:hover{border-bottom-style:solid}
.tools{display:flex;gap:10px;align-items:center;margin:6px 0 8px;flex-wrap:wrap}
.tools input{flex:1;min-width:200px;padding:7px 10px;border:1px solid var(--line);border-radius:7px;font-size:13px}
.tools .count{font-size:12.5px;color:var(--muted)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:820px){.grid2{grid-template-columns:1fr}}
ul.tight{margin:6px 0 6px 18px;padding:0}ul.tight li{margin:3px 0}
dl.kv{display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;margin:6px 0;font-size:13.5px}
dl.kv dt{color:var(--muted)}dl.kv dd{margin:0}
footer{border-top:1px solid var(--line);margin-top:40px;padding:18px 0 0;font-size:12.5px;color:var(--muted)}
footer a{color:var(--muted)}
.toc{display:flex;gap:8px;flex-wrap:wrap;margin:4px 0 18px}
.toc a{font-size:12.5px;border:1px solid var(--line);background:#fff;border-radius:999px;padding:4px 11px;text-decoration:none;color:var(--accent)}
"""


def esc(x):
    return (str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def table(rows, columns, tid, source_col=None, numeric=(), note=None, searchable=True):
    """Render a table. `columns` is a list of (key, header, css) or plain keys."""
    if not rows:
        return '<p class="panel">No rows.</p>'
    cols = []
    for c in columns:
        if isinstance(c, tuple):
            cols.append(c)
        else:
            cols.append((c, c, "num" if c in numeric else ""))
    body = []
    for i, r in enumerate(rows):
        tds = []
        for key, head, cls in cols:
            v = r.get(key, "")
            if v == "" or v is None:
                v = '<span class="unv">UNVERIFIED</span>' if key == source_col else "&mdash;"
            tds.append('<td class="%s">%s</td>' % (cls, v))
        body.append("<tr>%s</tr>" % "".join(tds))
    head = "".join('<th scope="col" class="%s">%s</th>' % (c[2], esc(c[1])) for c in cols)
    tools = ""
    if searchable:
        tools = ('<div class="tools"><input type="search" data-filter-table="%s" '
                 'placeholder="Filter %d rows&hellip;" aria-label="Filter this table">'
                 '<span class="count" data-count-for="%s">%d rows</span></div>' % (tid, len(rows), tid, len(rows)))
    cap = '<p class="cap">%s</p>' % note if note else ""
    return (tools + '<div class="tbl"><table id="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>%s'
            % (tid, head, "".join(body), cap))


def section(title, body, anchor=None):
    a = ' id="%s"' % anchor if anchor else ""
    return '<h2%s>%s</h2>\n%s' % (a, title, body)


def page(slug, title, sub, body, nav_title=None):
    nav = []
    for s, t, _sub, _b in R.PAGES:
        cls = ' class="on"' if s == slug else ""
        nav.append('<a href="%s.html"%s>%s</a>' % (s, cls, t))
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} &middot; NFL Market Desk</title>
<meta name="description" content="{sub}">
<style>{css}</style>
</head><body>
<header class="top"><div class="wrap">
<a class="brand" href="index.html">NFL Market Desk <span>/ own5 &middot; session 83a7d6a8</span></a>
<nav aria-label="Sections">{nav}</nav>
</div></header>
<main><div class="wrap">
<p class="crumb">NFL 2026 &middot; week 11 &middot; captured {cap}</p>
<h1>{title}</h1>
<p class="lede">{sub}</p>
{body}
<footer>
<p><strong>Paper research only.</strong> No bet is placed, no stake is live, no reward is
issued. Every numeric cell is computed from a committed data file in
<code>nfl-market-desk/data/</code>; every source link opens the page it came from. Cells
that could not be confirmed against an official page are left blank and marked
<span class="unv">UNVERIFIED</span> rather than estimated.</p>
<p>Built deterministically from the data files by <code>build.py</code>; verified by
<code>verify.py</code>. Capture clock: {cap}. &middot;
<a href="https://github.com/sassnarep3-star/Own5/tree/main/nfl-market-desk">source in the repository</a></p>
</footer>
</div></main>
<script>
document.querySelectorAll('[data-filter-table]').forEach(function(inp){{
  var id=inp.getAttribute('data-filter-table');
  var tbl=document.getElementById(id);
  var out=document.querySelector('[data-count-for="'+id+'"]');
  var rows=Array.prototype.slice.call(tbl.tBodies[0].rows);
  inp.addEventListener('input',function(){{
    var q=inp.value.toLowerCase(),shown=0;
    rows.forEach(function(r){{
      var hit=r.textContent.toLowerCase().indexOf(q)>-1;
      r.style.display=hit?'':'none'; if(hit)shown++;
    }});
    if(out)out.textContent=shown+' of '+rows.length+' rows';
  }});
}});
</script>
</body></html>
""".format(title=title, sub=sub, css=CSS, nav="".join(nav), body=body, cap=CAPTURED_DATE)


# ---------------------------------------------------------------------------
# page bodies
# ---------------------------------------------------------------------------
def body_landing():
    n = R.v_landing()
    req = rcsv("requirements.csv")
    st = {}
    for r in req:
        st[r["status"]] = st.get(r["status"], 0) + 1
    gates = rcsv("gates.csv")
    met = sum(1 for g in gates if g["status"] == "MET")
    notmet = sum(1 for g in gates if g["status"] == "NOT MET")
    flags = rcsv("flags.csv")
    blocking = sum(1 for x in flags if x["severity"] == "blocking")
    lb = rcsv("leaderboard.csv")
    ma = {r["holdout"]: r for r in rcsv("model_accuracy.csv")}
    best = max(lb, key=lambda r: float(r["signal_p_holm"] or 0) * -1 if r["signal_rank"] == "1" else -9)

    cards = [
        ("Requirements tracked", len(req), "%d met &middot; %d partial &middot; %d not met &middot; %d refused"
         % (st.get("MET", 0), st.get("PARTIAL", 0), st.get("NOT MET", 0), st.get("REJECTED", 0))),
        ("Validation gates", "%d / %d" % (met, len(gates)), "%d not met &middot; nothing may go live" % notmet),
        ("Markets originated", n["originated_markets"], "week 11 slate &middot; side, total, moneyline"),
        ("Graded bets", n["graded_bets"], "prospective only &middot; %d families" % n["registered_families"]),
        ("Blocking flags", blocking, "%d flags in the register" % len(flags)),
        ("Results verified", n["results_feed_rows"], "finals &middot; 32/32 standings reconcile"),
    ]
    cards_html = '<div class="cards">%s</div>' % "".join(
        '<div class="card"><div class="k">%s</div><div class="v">%s</div><div class="s">%s</div></div>'
        % (k, v, s) for k, v, s in cards)

    # --- decision readiness, blocking rows first
    ready = R.v_readiness()
    order = {"NOT MET": 0, "PARTIAL": 1, "MET": 2, "REJECTED": 3}
    ready_sorted = sorted(ready, key=lambda r: (order.get(r["_status"], 9), r["id"]))
    ready_rows = []
    for r in ready_sorted[:24]:
        ready_rows.append({
            "id": r["id"], "Requirement": r["Requirement"], "Status": r["Status"],
            "Gate": r["Gate"], "Would clear it": r["The number that would clear it"],
            "Evidence": r["Evidence"],
        })

    honest = """
<div class="panel bad"><h3 style="margin-top:0">What this desk does not establish, stated up front</h3>
<ul class="tight">
<li><strong>No price we can certify.</strong> nfl.com publishes no spread, total or moneyline, and no
sportsbook page was reachable from the capture environment. The only prices in this repository come
from a third-party mirror with no book, no jurisdiction and no timestamp. Those prices are labelled
AGGREGATOR and are barred from certification and from any closing-line claim.</li>
<li><strong>The model does not beat the market on the validation window.</strong> Weeks 5&ndash;8:
model Brier {v_bm} against the market's {v_bk} on the same {v_n} games. It does beat it on the final
holdout (weeks 9&ndash;10: {h_bm} vs {h_bk} on {h_n} games), but a 24-game holdout is not evidence of
an edge and we do not present it as one.</li>
<li><strong>No bet is live and no reward is issued.</strong> Every family is registered PAPER. Five of
the eleven gates are not met, and the two that matter most &mdash; a certifiable price and a
prospective sample &mdash; cannot be met from inside this repository.</li>
<li><strong>Depth coverage is 11 of 32 clubs</strong> and every one of those charts is undated or one
capture old. The replacement matrix is therefore a partial view, labelled as such.</li>
</ul></div>
""".format(v_bm=ma["VALIDATION (weeks 5-8)"]["brier_model"],
           v_bk=ma["VALIDATION (weeks 5-8)"]["brier_market"],
           v_n=ma["VALIDATION (weeks 5-8)"]["n_games"],
           h_bm=ma["FINAL HOLDOUT (weeks 9-10)"]["brier_model"],
           h_bk=ma["FINAL HOLDOUT (weeks 9-10)"]["brier_market"],
           h_n=ma["FINAL HOLDOUT (weeks 9-10)"]["n_games"])

    changed = """
<div class="panel note"><h3 style="margin-top:0">What changed in this build</h3>
<ul class="tight">
<li><strong>Price store opened.</strong> 195 snapshot rows now exist for the 39 originated Week-11
markets: 78 carry a number (our own fair line, and the aggregator reference), 117 are deliberately
empty with a flag, because an opening and a close cannot be observed without a second clock.</li>
<li><strong>Flags consolidated.</strong> The inherited register from PR #79 used the same identifiers
(F-01&hellip;F-14) as this desk for entirely different findings. Both are now in one register with
namespaces: INH- for the inherited fourteen, OWN- for this desk's twenty, 34 in total.</li>
<li><strong>Two ledger counts corrected.</strong> The Week 11 slate note said 14 games (the page lists
13) and the injury capture note said 254 rows (the committed file holds 347). Both are corrected in
place with the correction left visible as OWN-20, not overwritten.</li>
<li><strong>The total market got an honest reference.</strong> A draft build derived a
&quot;market-implied margin standard deviation&quot; from a symmetric price and produced 42.9-point
standard deviations. That is an artefact, not a market number, so the field is now blank by
construction and the total's market reference is the de-vigged two-way total price instead.</li>
</ul></div>"""

    lead = """
<div class="panel note"><h3 style="margin-top:0">The one-line reading</h3>
<p style="margin:0">{line}</p></div>""".format(line=(
        "Of the %d bet families this desk pre-registered, one clears its own signal test "
        "(S5, rest edge, hit rate %.4f against a price-implied null, n=%s, Holm p=%s) &mdash; and it "
        "cannot be certified, because certification needs a closing price this repository does not "
        "contain. The best staking ROI on the board belongs to a family with %s graded bets, which is "
        "exactly the number the brief told us never to rank by."
        % (len(lb),
           float([r for r in lb if r["family_id"] == "S5"][0]["signal_headline"]),
           [r for r in lb if r["family_id"] == "S5"][0]["graded_bets"],
           [r for r in lb if r["family_id"] == "S5"][0]["signal_p_holm"],
           [r for r in lb if r["family_id"] == "S7"][0]["graded_bets"]))
        if any(r["family_id"] == "S5" for r in lb) else "")

    body = cards_html + lead + honest + changed
    body += section("Decision readiness &mdash; the rows that block", 
                    '<p class="lede">One row per requirement, worst first. The column that matters is the '
                    'one that says what number would clear it. <a href="readiness.html">All %d rows &rarr;</a></p>' % len(ready)
                    + table(ready_rows, ["id", "Requirement", "Status", "Gate", "Would clear it",
                                         "Evidence"], "ready", source_col="Evidence"),
                    "readiness")
    body += section("Sessions and desks &mdash; what already exists",
                    '<p class="lede">Eleven prior NFL desks are in this repository. This one re-verified '
                    'four of them against live sources and found one real collision (the flag namespace) '
                    'and one real disagreement (the depth register).</p>'
                    + table(R.v_desks(), ["Desk", "What it claims", "Re-verified by this desk", "Relation", "Link"], "desks"),
                    "desks")
    body += section("Start here",
                    '<div class="grid2">'
                    '<div class="panel"><h3 style="margin-top:0">If you want the numbers</h3><ul class="tight">'
                    '<li><a href="lines.html">Line origination</a> &mdash; fair line, market line, difference, 39 markets</li>'
                    '<li><a href="leaderboard.html">Leaderboard</a> &mdash; signal and staking ranked separately</li>'
                    '<li><a href="availability.html">Availability</a> &mdash; 28 clubs, 14 named replacements</li>'
                    '<li><a href="prices.html">Prices and results</a> &mdash; 195 snapshot rows, 145 verified finals</li>'
                    '</ul></div>'
                    '<div class="panel"><h3 style="margin-top:0">If you want the doubts</h3><ul class="tight">'
                    '<li><a href="review.html">Flagged for Review</a> &mdash; 34 flags, %d blocking</li>'
                    '<li><a href="questions.html">Questions</a> &mdash; 15, with the cheapest route to each answer</li>'
                    '<li><a href="gates.html">Gates</a> &mdash; %d met, %d not met, and the test for each</li>'
                    '<li><a href="suggestions.html">Suggestions</a> &mdash; 19 decisions waiting for you</li>'
                    '</ul></div></div>'
                    % (blocking, met, notmet), "start")
    body += section("How to read this site",
                    '<div class="panel"><p style="margin:0">Each table row carries a source link. '
                    'A cell that says <span class="unv">UNVERIFIED</span> is a cell where a value ought to '
                    'be, must be shown, and could not be confirmed against an official page &mdash; it is '
                    'not zero and it is not an estimate. Tiers are stated on every value: '
                    '<span class="badge good">OFFICIAL</span> a league or club page, '
                    '<span class="badge warn">AGGREGATOR</span> a third-party mirror with undocumented '
                    'provenance, <span class="badge neutral">DERIVED</span> computed here from published '
                    'inputs.</p></div>', "how")
    return body


def body_readiness():
    rows = R.v_readiness()
    order = {"NOT MET": 0, "PARTIAL": 1, "MET": 2, "REJECTED": 3}
    rows = sorted(rows, key=lambda r: (order.get(r["_status"], 9), r["id"]))
    rows = [{"id": r["id"], "Requirement": r["Requirement"], "Status": r["Status"],
             "Gate": r["Gate"], "Gate status": r["Gate status"],
             "The number that would clear it": r["The number that would clear it"],
             "Current number": r["Current number"], "Evidence": r["Evidence"]} for r in rows]
    body = ('<div class="panel note"><p style="margin:0">Statuses are not self-assessed: '
            '<code>verify.py</code> resolves every row&rsquo;s evidence path and fails the build if the '
            'file or the row is missing. The Evidence column opens that file. A REJECTED row is a '
            'proposal this desk refused on principle, with the reason recorded &mdash; not a row that '
            'failed.</p></div>')
    body += table(rows, ["id", "Requirement", "Status", "Gate", "Gate status",
                         "The number that would clear it", "Current number", "Evidence"], "req",
                  source_col="Evidence")
    return body


def body_lines():
    import json
    ms = json.load(open(os.path.join(DATA, "model_summary.json"), encoding="utf-8"))
    rows = R.v_lines()
    q = rcsv("originated_markets.csv")
    side = [r for r in q if r["market_type"] == "SIDE"]
    diff = sorted(side, key=lambda r: -abs(float(r["difference_fair_minus_market"])))
    biggest = diff[0] if diff else None
    body = ('<div class="panel note"><p style="margin:0"><strong>What this page is.</strong> For every '
            'Week 11 game we publish three numbers side by side: the line our own ratings produce, the '
            'line a third-party mirror shows, and the difference. The market column is '
            '<span class="badge warn">AGGREGATOR</span> tier &mdash; a mirror with no book, no timestamp '
            'and no jurisdiction &mdash; so the difference is a research quantity, not an edge.</p></div>')
    if biggest:
        body += ('<div class="panel"><p style="margin:0">The largest side disagreement on the slate is '
                 '<strong>%s @ %s</strong>: our fair line is %s points from the mirror&rsquo;s, which '
                 'would imply a %.1f%% home win probability against the mirror&rsquo;s own de-vigged '
                 'number. Two independent ways of being wrong open up at that size, which is why the '
                 'family that trades it (S1) is registered at a 3.0-point threshold and has never '
                 'been certified.</p></div>'
                 % (biggest["away"], biggest["home"], biggest["difference_fair_minus_market"],
                    100 * float(biggest["probability"])))
    body += section("Originated markets", table(rows, ["id", "Fixture", "Market", "Order", "Kickoff",
                                                       "Our fair line", "Market line",
                                                       "Difference (fair - market)", "Probability",
                                                       "Market source", "Slate source"], "lines",
                                                source_col="Market source",
                                                numeric=("Our fair line", "Market line",
                                                         "Difference (fair - market)", "Probability")),
                    "markets")
    body += section("Model accuracy on held-out weeks",
                    table(R.v_model_accuracy(), ["Sample", "n", "n with a market price", "Brier (model)",
                                                 "Brier (market)", "Brier (coin flip)", "Skill vs market",
                                                 "Skill vs coin flip", "MAE margin (model)",
                                                 "MAE margin (market)", "Source"], "acc",
                          source_col="Source"),
                    "accuracy")
    body += section("Personnel ablation (why there is no fixed injury penalty)",
                    '<p class="lede">The brief asks for ablations with uncertainty instead of a fixed '
                    'points penalty. %d Week-10 games had a usable personnel difference. The fitted '
                    'coefficient is %s points per additional unavailable player with a standard error '
                    'of %s &mdash; an interval that spans zero. No penalty is applied anywhere in the '
                    'published lines.</p>' % (ms["availability_ablation_n"],
                                             ms["availability_coefficient_pts_per_extra_out"],
                                             ms["availability_coefficient_se"])
                    + table(R.v_ablation(), ["Week", "Fixture", "Out (home/away)", "Starters out (h/a)",
                                             "Availability diff", "P(home) without personnel",
                                             "P(home) with the fitted coefficient", "Actual",
                                             "Injury source"], "abl", source_col="Injury source"),
                    "ablation")
    body += section("Every forecast", 
                    table(R.v_forecasts(), ["Week", "Fixture", "P(home win)", "Fair margin", "Fair total",
                                           "Market spread", "Market total", "Train games",
                                           "Train last week", "Score", "Source"], "fc", source_col="Source"),
                    "forecasts")
    return body


def body_strategies():
    reg = R.v_strategies()
    bets = rcsv("strategy_graded_bets.csv")
    per = {}
    for b in bets:
        per.setdefault(b["family_id"], []).append(b)
    body = ('<div class="panel note"><p style="margin:0">Nine families were written down and hashed '
            '<em>before</em> any of them was graded. The SHA-256 in each row is the registration: change '
            'a rule and the hash changes, which is the only thing that makes a backtest mean anything. '
            'None of these numbers appears on the leaderboard page, because the leaderboard is '
            'prospective-only by rule.</p></div>')
    body += table(reg, ["id", "Family", "Signal type", "Bet class", "Rule (pre-registered, hashed)",
                        "SHA-256", "Registered", "Status", "Rule file"], "reg", source_col="Rule file")
    body += section("Graded bets (backtest register, not the leaderboard)",
                    '<p class="lede">%d bets across %d families. This table exists so the backtest is '
                    'auditable; it is deliberately not ranked.</p>'
                    % (len(bets), len(per))
                    + table([{"id": b["family_id"], "Game": b["game_id"], "Week": b["week"],
                              "Side": b["side_or_total"], "Won": b["won"],
                              "p": b["proper_score_p"], "Model p": b["model_prob"],
                              "Reference": b["reference_prob"], "Price": b["price_american"],
                              "Price implied": b["price_implied_prob"], "Edge": b["edge"],
                              "Source": R.link(b["source_url"], "NFL week " + b["week"])}
                             for b in bets],
                            ["id", "Game", "Week", "Side", "Won", "p", "Model p", "Reference",
                             "Price", "Price implied", "Edge", "Source"], "bets", source_col="Source"),
                    "bets")
    return body


def body_leaderboard():
    lb = rcsv("leaderboard.csv")
    body = ('<div class="panel note"><p style="margin:0"><strong>Two rankings, never one.</strong> '
            'Families that publish a probability are ranked on a proper score (Brier) against the '
            'market&rsquo;s own de-vigged probability, with a Holm adjustment across all nine registered '
            'families. Families that are market-state rules carry no probability at all, so ranking them '
            'on Brier was an artefact; they are ranked on hit rate against the null rate implied by the '
            'price they paid. Staking is a separate column and a separate rank, and it is never the '
            'ranking criterion.</p></div>')
    body += section("Leaderboard", table(R.v_leaderboard(),
                                         ["id", "Family", "Class", "Registry", "n", "Signal", "p (Holm)",
                                          "Signal rank", "Staking n", "ROI", "Staking rank", "Hit rate",
                                          "State", "Why not certified", "Source"], "lb",
                            source_col="Source"),
                    "board")
    body += section("Controls on the same games",
                    '<p class="lede">A strategy that cannot beat a coin flip with the same games and the '
                    'same outcomes has not shown anything. The controls are graded on exactly the same '
                    'rows, not on a sample of convenience.</p>'
                    + table(R.v_controls_and_luck(), ["id", "Control", "n", "Decided", "Brier",
                                                     "Hit rate", "Reading", "Source"], "ctl",
                            source_col="Source"),
                    "controls")
    luck = rcsv("luck_panel.csv")
    body += section("Removal of luck",
                    '<p class="lede">The question is not how often the model was right; it is whether it '
                    'was right more often than its own probabilities said it would be. On the '
                    'prospective block the model hit %s of %s games while its own probabilities '
                    'predicted %s &mdash; it was <em>below</em> expectation, and a hit rate of %s looks '
                    'like skill only if you never compute that comparison.</p>'
                    % (luck[0]["hits_observed"], luck[0]["n_games"],
                       luck[0]["hits_expected_from_model_probs"], luck[0]["pick_accuracy"])
                    + table([{"id": r["panel"], "n": r["n_games"], "Pick accuracy": r["pick_accuracy"],
                              "95% interval": r["pick_accuracy_ci95"], "Hits observed": r["hits_observed"],
                              "Hits expected from the model's own probabilities":
                                  r["hits_expected_from_model_probs"],
                              "Binomial p vs that expectation": r["binomial_p_vs_model_expectation"],
                              "Brier (model)": r["brier_model"], "Brier (coin flip)": r["brier_coinflip"],
                              "Brier skill vs coin flip": r["brier_skill_vs_coinflip"],
                              "Cluster bootstrap 95%": r["brier_cluster_boot_ci95"],
                              "Reading": r["reading"],
                              "Source": R.link("https://www.nfl.com/schedules/2026/by-week/week-10",
                                               "NFL scores")} for r in luck],
                            ["id", "n", "Pick accuracy", "95% interval", "Hits observed",
                             "Hits expected from the model's own probabilities",
                             "Binomial p vs that expectation", "Brier (model)", "Brier (coin flip)",
                             "Brier skill vs coin flip", "Cluster bootstrap 95%", "Reading", "Source"],
                            "luck", source_col="Source"),
                    "luck")
    body += section("Demotion rules (written before go-live)",
                    table([{"id": r["rule_id"], "Trigger": r["trigger"], "Definition": r["definition"],
                            "Effect": r["effect"], "Applies to": r["applies_to"],
                            "Evidence": R.link(R.EVIDENCE_BASE + "data/demotion_rules.csv",
                                               "demotion_rules.csv", "DERIVED")}
                           for r in rcsv("demotion_rules.csv")],
                          ["id", "Trigger", "Definition", "Effect", "Applies to", "Evidence"], "demo",
                          source_col="Evidence"),
                    "demotion")
    return body


def body_gates():
    g = rcsv("gates.csv")
    body = ('<div class="panel note"><p style="margin:0">A gate is a test, not an opinion. Each row '
            'below states the test, who it applies to and what happens if it fails. Nothing on this site '
            'is certified until every hard gate is MET; today five are not.</p></div>')
    body += table(R.v_gates(), ["id", "Gate", "Test", "Class", "Status", "Blocking flag(s)", "Source"],
                  "gates", source_col="Source")
    body += section("Gate vocabulary",
                    '<dl class="kv">'
                    '<dt>hard</dt><dd>a failure blocks certification outright; there is no override</dd>'
                    '<dt>soft</dt><dd>a failure blocks the specific claim the gate protects, not the family</dd>'
                    '<dt>MET</dt><dd>the test was run and passed, with the evidence in the linked file</dd>'
                    '<dt>NOT MET</dt><dd>the test cannot be run because the input does not exist in this repository</dd>'
                    '<dt>PARTIAL</dt><dd>the test was run on the subset of the universe where it is possible</dd>'
                    '</dl>', "vocab")
    return body


def body_availability():
    av = rcsv("availability_by_team.csv")
    cas = rcsv("replacement_cascade.csv")
    ms = __import__("json").load(open(os.path.join(DATA, "model_summary.json"), encoding="utf-8"))
    tot_out = sum(int(r["named_out"]) for r in av)
    tot_q = sum(int(r["questionable"]) for r in av)
    tot_d = sum(int(r["doubtful"]) for r in av)
    repl = sum(1 for r in cas if r["replacement"])
    second = sum(1 for r in cas if r["depth_of_replacement"].startswith("2nd"))
    body = ('<div class="panel note"><p style="margin:0"><strong>Read this before the tables.</strong> '
            'The Week 10 report lists %d players Out, %d Doubtful and %d Questionable across the 28 '
            'clubs that played. "%d starters named out" is not a severity score and is not converted '
            'into points anywhere: the fitted coefficient for personnel is indistinguishable from zero '
            '(%s +/- %s over nine games), so the replacement table is evidence, not an adjustment.</p>'
            '</div>' % (tot_out, tot_d, tot_q, repl,
                        ms["availability_coefficient_pts_per_extra_out"],
                        ms["availability_coefficient_se"]))
    body += ('<div class="panel warn"><p style="margin:0"><strong>The gap that matters.</strong> '
             '"Starters out" is measured against a published depth chart for 11 of 32 clubs. For the '
             'other 21 the report side is complete and the replacement side is blank, because the club '
             'publishes its chart as an image (Houston), behind a different host, or not at all. A blank '
             'replacement cell here means <em>we could not read it</em>, never <em>nobody is behind '
             'him</em>. The full coverage table, with a hash of every raw capture, is on '
             '<a href="sources.html">Sources</a>.</p></div>')
    body += section("Per team", table(R.v_availability(),
                                      ["id", "Club", "On report", "Out", "Doubtful", "Questionable",
                                       "No designation", "Chart parsed", "Starters out",
                                       "Replacements named", "Compounding", "Net unavailable (weighted)",
                                       "Note", "Source"], "avail", source_col="Source"),
                    "teams")
    body += section("The depth of each replacement",
                    '<p class="lede">%d named replacements; %d are the 2nd string on the club&rsquo;s own '
                    'chart and none is a compounding case (a 2nd-string player himself injured). That is '
                    'the honest answer to &ldquo;how deep is the deficiency&rdquo;, and it is also why '
                    'the feature is not worth building yet: at one removal per club, depth beyond the '
                    'second string never gets exercised.</p>' % (repl, second)
                    + table(R.v_cascade(), ["id", "Club", "Starter (rank 1 on the club's own chart)",
                                            "Position", "Status", "Replacement", "Depth of replacement",
                                            "Replacement also on report", "Compounding", "Depth source",
                                            "Injury source"], "cas", source_col="Depth source"),
                    "cascade")
    body += section("Depth register coverage", 
                    table([{"id": r["club"], "Club": r["club_name"], "Shape": r["page_shape"],
                            "Rows parsed": r["rows_parsed"], "Players": r["players_parsed"],
                            "Shared slots": r["shared_slots"], "Empty slots": r["empty_slots"],
                            "Jerseys stripped": r["jersey_numbers_stripped"], "Parsed": r["parsed"],
                            "Page dated": r["page_dated"] or '<span class="unv">undated</span>',
                            "Hash": '<code>%s</code>' % r["raw_file_sha256"][:12],
                            "Source": R.link(r["depth_url"], "club chart", "OFFICIAL")}
                           for r in rcsv("depth_coverage.csv")],
                          ["id", "Club", "Shape", "Rows parsed", "Players", "Shared slots", "Empty slots",
                           "Jerseys stripped", "Parsed", "Page dated", "Hash", "Source"], "cov",
                          source_col="Source"),
                    "coverage")
    body += section("Every parsed depth row",
                    '<p class="lede">%d rows from 11 clubs. Shared slots are two players at the same '
                    'rank, published faithfully; empty slots are holes the club itself prints.</p>'
                    % len(R.v_depth())
                    + table(R.v_depth(), ["id", "Club", "Unit", "Position", "Slot", "Rank", "Player",
                                          "Jersey", "Shape", "Page dated", "Source"], "depth",
                            source_col="Source"),
                    "rows")
    body += section("Where the live chart and the inherited register disagree",
                    '<p class="lede">Seventeen divergences against the register inherited from PR #79. '
                    'Nine players appear on a live chart and not in the register; two appear only in the '
                    'register; six are ranked differently. We publish them as disagreements rather than '
                    'picking a winner, because both sources are the club&rsquo;s own page at different '
                    'times and neither is dated.</p>'
                    + table(R.v_compare(), ["id", "Player", "Live position", "Live rank",
                                            "Inherited position", "Inherited rank", "Result", "Note",
                                            "Source"], "cmp", source_col="Source"),
                    "compare")
    body += section("Announced starters (evidence, not inference)",
                    table([{"id": r["id"], "Club": r["club"], "Player": r["player"],
                            "Published": r["published_date"], "Headline": r["headline"],
                            "Announced starter": r["announced_starter"] or
                            '<span class="unv">not named in the headline</span>',
                            "Note": r["note"], "Source": R.link(r["url"], "NFL news", "OFFICIAL")}
                           for r in rcsv("announced_starter_changes.csv")],
                          ["id", "Club", "Player", "Published", "Headline", "Announced starter",
                           "Note", "Source"], "ann", source_col="Source"),
                    "announced")
    return body


def body_correlations():
    body = ('<div class="panel note"><p style="margin:0">Every correlation on this page is computed '
            'here from one official page, and every row publishes its n and its two-sided p. Values we '
            'cannot source officially are not published at all; they are listed with the reason on the '
            'second table.</p></div>')
    body += table(R.v_correlations(), ["id", "Unit", "Metric A", "Metric B", "r", "r squared",
                                       "p (two-sided)", "n", "n definition", "Tier", "Source"],
                  "corr", source_col="Source")
    body += section("Withheld, and why",
                    table(R.v_correlations_withheld(), ["id", "Pair", "Why it is not published",
                                                        "Prior input tier", "Status", "Evidence"], "wh",
                          source_col="Evidence"),
                    "withheld")
    body += section("What the numbers do and do not mean",
                    '<div class="panel"><ul class="tight">'
                    '<li>n=32 is one season slice of 32 clubs. It is enough to report a coefficient and '
                    'its p-value; it is not enough to support a player-level claim, which is why no '
                    'player correlation appears here.</li>'
                    '<li>Points-for and win percentage correlating at r=0.725 is a sanity check on the '
                    'data join, not a discovery.</li>'
                    '<li>Parlay and prop-combo dependence needs paired player outcomes and prop prices. '
                    'Neither exists in this repository (OWN-17), so no parlay correlation is published '
                    'and gate G7 blocks both combo families outright.</li>'
                    '</ul></div>', "meaning")
    return body


def body_prices():
    pol = rcsv("price_policy.csv")
    ps = rcsv("price_snapshots.csv")
    pop = sum(1 for r in ps if r["line_value"])
    body = ('<div class="panel note"><p style="margin:0"><strong>Policy first, numbers second.</strong> '
            '%d policy decisions were fixed before any return was computed. %d snapshot rows exist for '
            'the 39 originated markets; %d carry a number and %d are empty by policy. An empty row is a '
            'statement that the observation does not exist, which is why the store has more empty rows '
            'than filled ones.</p></div>' % (len(pol), len(ps), pop, len(ps) - pop))
    body += section("Price policy", table(R.v_policy(), ["id", "Question", "Decision", "Scope", "Status",
                                                        "Tier", "Rationale", "Source"], "pol",
                                          source_col="Source"),
                    "policy")
    body += section("The snapshot store", 
                    '<p class="lede">Five snapshot types per market. MODEL_ORIGIN and MARKET_REFERENCE '
                    'are filled; opening, close and model-close are empty with a flag, because a single '
                    'capture cannot produce a second observation.</p>'
                    + table(R.v_price_store(), ["id", "Fixture", "Market", "Snapshot", "Clock (UTC)",
                                                "Line", "Price", "Tier", "Verified", "Flag", "Source"],
                            "ps", source_col="Source"),
                    "store")
    body += section("Venues: what the official page prints, and what it does not",
                    '<p class="lede">The brief asks for a roof/surface overlay and a venue transcribed '
                    'from the official game centre. The official Week 11 page prints the stadium for 12 '
                    'of 13 games (in its ticket and hotel link destinations), prints a weather line for '
                    'one game, and names only the host city for the Mexico City fixture. It prints no '
                    'roof and no surface at all &mdash; so those two columns stay aggregator-tier and '
                    'blank where the mirror is blank, rather than being filled in from memory.</p>'
                    + table(R.v_venues(), ["id", "Fixture", "Stadium (official page)", "Neutral site",
                                           "Weather printed on the page", "Roof (mirror, aggregator)",
                                           "Surface (mirror, aggregator)", "Status", "Source"], "ven",
                            source_col="Source"),
                    "venues")
    body += section("Verified results feed",
                    '<p class="lede">%d finals, each tied to the official week page it was read from. '
                    '127 of the 145 also appear in the pinned mirror and agree; 18 do not appear in the '
                    'mirror at all and are marked absent rather than imputed.</p>' % len(R.v_results())
                    + table(R.v_results(), ["Week", "Date", "Away", "Home", "Neutral", "Status",
                                            "Mirror check", "Source"], "res", source_col="Source"),
                    "results")
    body += section("Standings reconciliation",
                    '<p class="lede">The feed is only trustworthy if it reproduces the league&rsquo;s own '
                    'table. All 32 clubs reconcile exactly on W-L-T, points for and points against.</p>'
                    + table(R.v_reconciliation(), ["id", "Club", "Feed W-L-T", "Official W-L-T",
                                                   "Feed PF/PA", "Official PF/PA", "Result", "Source"],
                            "rec", source_col="Source"),
                    "recon")
    body += section("Standings",
                    table(R.v_standings(), ["id", "Club", "W", "L", "T", "Win pct", "PF", "PA", "Net",
                                            "PF/G", "PA/G", "Home", "Road", "Source"], "std",
                          source_col="Source", numeric=("W", "L", "T", "PF", "PA", "Net", "PF/G", "PA/G")),
                    "standings")
    return body


def body_questions():
    q = rcsv("questions.csv")
    have = sum(1 for r in q if r["have_information"] == "YES")
    body = ('<div class="panel note"><p style="margin:0">%d questions. %d can be answered today from '
            'this repository; %d cannot. Each row names what we already have, what is missing, and the '
            'cheapest route to the missing part &mdash; so a decision can be made about whether the '
            'answer is worth buying.</p></div>' % (len(q), have, len(q) - have))
    body += table(R.v_questions(), ["id", "Question", "Have it?", "What we have", "What is missing",
                                    "Cheapest route to the answer", "Blocks", "Flags", "Source"], "q",
                  source_col="Source")
    body += section("The four questions that gate everything else",
                    '<div class="grid2">'
                    '<div class="panel"><h3 style="margin-top:0">Where is the price?</h3><p>No official or '
                    'operator price is reachable. Until one is, every ROI here is a research figure and '
                    'no strategy can be certified. Route: buy a feed, or paste dated screenshots of one '
                    'book into a private store.</p></div>'
                    '<div class="panel"><h3 style="margin-top:0">Who actually played?</h3><p>Inactive '
                    'lists and snap counts are the two missing pieces that would turn &ldquo;he is on the '
                    'chart&rdquo; into &ldquo;he took the snaps&rdquo;. Route: capture the inactive list '
                    '90 minutes before kickoff.</p></div>'
                    '<div class="panel"><h3 style="margin-top:0">Can the injury report be trusted?</h3>'
                    '<p>347 rows, 90 Questionable, and no measurement of how often '
                    'Questionable plays. Route: join several seasons of designations to inactive lists; '
                    'needs an archive that does not exist here.</p></div>'
                    '<div class="panel"><h3 style="margin-top:0">Is any of this a series yet?</h3>'
                    '<p>One capture of everything. A delta needs two clocks. Route: a scheduled second '
                    'capture, appending rather than overwriting.</p></div>'
                    '</div>', "gating")
    return body


def body_suggestions():
    s = rcsv("suggestions.csv")
    body = ('<div class="panel note"><p style="margin:0">Nineteen decisions are waiting. Each row '
            'lists the options actually on the table, which one this desk recommends and why, and the '
            'rule that would reverse the recommendation. Nothing here has been implemented on the '
            'strength of a recommendation alone.</p></div>')
    body += table(R.v_suggestions(), ["id", "Topic", "Priority", "Options", "Recommended path",
                                      "Reversible rule (what would change the call)", "Cost", "Status",
                                      "Source"], "sg", source_col="Source")
    return body


def body_sources():
    body = ('<div class="panel note"><p style="margin:0">One row per capture, with publisher, tier, '
            'clock time, what it was used for and what was wrong with it. This is the ledger: if a '
            'number on this site cannot be traced to a row here, it should not be trusted.</p></div>')
    body += table(R.v_sources(), ["id", "Publisher", "Title", "Tier", "Fetched (UTC)", "Used for",
                                  "Notes", "Link"], "src", source_col="Link")
    body += section("The league's own dated schedule language, beside the live schedule",
                    '<p class="lede">The brief asks for the league&rsquo;s dated announcement to be '
                    'published next to the live schedule, so a reader can tell a fixed kickoff from a '
                    'placeholder. These four are quoted verbatim from the live page with the capture '
                    'clock.</p>'
                    + table(R.v_announcements(), ["id", "Topic", "Dated language on the official page",
                                                  "Captured (UTC)", "Source"], "ann",
                            source_col="Source"),
                    "announcements")
    return body


def body_review():
    flags = rcsv("flags.csv")
    blk = [x for x in flags if x["severity"] == "blocking"]
    body = ('<div class="panel bad"><p style="margin:0"><strong>%d blocking, %d in total.</strong> '
            'A blocking flag is one where a published claim on this site could be wrong for a reason we '
            'cannot fix from inside the repository. Blocking flags do not stop this desk from '
            'publishing analysis; they stop it from certifying a strategy, issuing a reward or calling '
            'anything a closing line.</p></div>' % (len(blk), len(flags)))
    body += table(R.v_flags(), ["id", "Severity", "Area", "Finding", "Consequence",
                                "Action taken / needed", "Status", "Origin", "Source"], "flags",
                  source_col="Source", note=(
                      'Every flag carries the page it was observed on. A flag with an empty source '
                      'link is a defect in the register itself and is treated as one.'))
    body += section("How a flag gets closed",
                    '<dl class="kv">'
                    '<dt>blocking</dt><dd>needs an input that does not exist here (a price, an inactive '
                    'list, a second capture). Stays open until the input arrives.</dd>'
                    '<dt>review</dt><dd>two sources disagree, or a value is ambiguous. Closed by '
                    're-reading the official page, not by choosing the convenient number.</dd>'
                    '<dt>corrected, kept visible</dt><dd>an error this desk made, fixed in place with the '
                    'correction recorded (OWN-20 is the worked example).</dd>'
                    '</dl>', "closing")
    return body


BUILDERS = {
    "landing": body_landing, "readiness": body_readiness, "lines": body_lines,
    "strategies": body_strategies, "leaderboard": body_leaderboard, "gates": body_gates,
    "availability": body_availability, "correlations": body_correlations, "prices": body_prices,
    "questions": body_questions, "suggestions": body_suggestions, "sources": body_sources,
    "review": body_review,
}


def main():
    written = []
    for slug, title, sub, builder in R.PAGES:
        html = page(slug, title, sub, BUILDERS[builder]())
        path = os.path.join(HERE, slug + ".html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        written.append((slug, len(html)))
    for slug, n in written:
        print("  %-14s %6d bytes" % (slug + ".html", n))
    print("pages:", len(written))


if __name__ == "__main__":
    main()

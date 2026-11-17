#!/usr/bin/env python3
"""build_site.py — renders the desk's CSV tables into the static Pages site.

Deterministic: no clock reads, no randomness, sorted input. Every body row ends in either an official link
or an explicit UNVERIFIED badge, which is a structural property of the renderer (it appends the cell), and
verify.py re-proves it from the generated HTML rather than from the CSVs.
"""
from __future__ import annotations
import csv, html, io, math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
REPO = HERE.parent
AS_OF = "2026-11-17T01:05Z"
CAPTURE = "2026-11-17T00:38Z – 00:52Z"

CSS = """
:root{--bg:#0e1116;--panel:#161b23;--panel2:#1b2230;--line:#27303e;--ink:#e7edf6;--dim:#94a3b8;--teal:#4fd1c5;
--amber:#f6c453;--red:#f2748c;--green:#7bd88f;--blue:#7aa2f7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Inter,sans-serif}
a{color:var(--teal);text-decoration:none}a:hover{text-decoration:underline}
.shell{display:grid;grid-template-columns:250px 1fr;min-height:100vh}
nav.side{border-right:1px solid var(--line);padding:20px 16px;position:sticky;top:0;height:100vh;overflow:auto}
.brand{font-weight:700;letter-spacing:.04em;font-size:15px}
.brand small{display:block;color:var(--dim);font-weight:500;letter-spacing:.12em;font-size:10px;margin-top:4px}
.grp{margin:18px 0 6px;font-size:10px;letter-spacing:.14em;color:var(--dim)}
nav.side a{display:block;color:var(--ink);padding:5px 8px;border-radius:7px;font-size:13.5px}
nav.side a.on{background:var(--panel2);color:var(--teal);font-weight:600}
main{padding:26px 30px 60px;max-width:1500px}
h1{font-size:25px;margin:0 0 6px}h2{font-size:17px;margin:30px 0 10px}h3{font-size:14px;margin:22px 0 8px;color:var(--dim)}
.sub{color:var(--dim);font-size:13.5px;margin:0 0 18px;max-width:1000px}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;border:1px solid var(--line);color:var(--dim)}
.pill.ok{color:var(--green);border-color:#204b34}.pill.no{color:var(--red);border-color:#4d2632}
.pill.warn{color:var(--amber);border-color:#4d4022}.pill.info{color:var(--blue);border-color:#28374f}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:12px;margin:16px 0 6px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 14px}
.card b{display:block;font-size:22px;margin:2px 0 3px;font-weight:650}.card span{color:var(--dim);font-size:12px}
.card a{font-size:12.5px}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--teal);border-radius:10px;
padding:12px 14px;margin:14px 0;font-size:13.5px;max-width:1100px}
.note.amber{border-left-color:var(--amber)}.note.red{border-left-color:var(--red)}.note.green{border-left-color:var(--green)}
.tblwrap{overflow:auto;border:1px solid var(--line);border-radius:11px;background:var(--panel);margin:8px 0 4px}
table{border-collapse:collapse;width:100%;font-size:12.8px}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{position:sticky;top:0;background:var(--panel2);color:var(--dim);font-weight:600;font-size:11px;
letter-spacing:.06em;text-transform:uppercase;white-space:nowrap}
tbody tr:last-child td{border-bottom:0}tbody tr:hover td{background:#1a212c}
td.num{font-variant-numeric:tabular-nums;white-space:nowrap}
td a{white-space:nowrap}.blank{color:#5b6b82}
.badge{display:inline-block;padding:1px 7px;border-radius:6px;font-size:11px;border:1px solid var(--line);white-space:nowrap}
.b-yes{color:var(--green);border-color:#204b34}.b-no{color:var(--red);border-color:#4d2632}
.b-part{color:var(--amber);border-color:#4d4022}.b-un{color:var(--dim)}
.b-off{color:var(--blue);border-color:#28374f}.b-3p{color:#c99df5;border-color:#3b2a52}
ul.tight{margin:6px 0 0;padding-left:20px;font-size:13.5px}ul.tight li{margin:4px 0}
footer{margin-top:34px;padding-top:14px;border-top:1px solid var(--line);color:var(--dim);font-size:12px}
@media(max-width:960px){.shell{grid-template-columns:1fr}nav.side{position:static;height:auto;border-right:0;
border-bottom:1px solid var(--line)}}
"""

NAV = [
    ("Workspace", [("index.html", "Landing / status"), ("executive-summary.html", "Executive summary"),
                   ("requirements.html", "Decision readiness"), ("questions.html", "Questions register"),
                   ("suggestions.html", "Suggestions (review first)")]),
    ("Verified record", [("results.html", "Results & standings"), ("roster-events.html", "Roster & reserve events"),
                        ("availability.html", "Availability snapshots"), ("sources.html", "Sources & manifest")]),
    ("Origination", [("origination.html", "Week 11 lines & model"), ("price-store.html", "Price-snapshot store"),
                     ("analytics.html", "Correlations & luck")]),
    ("Competition", [("competition.html", "Strategies, gates, leaderboard"),
                     ("verification.html", "Verification log"), ("flagged.html", "Flagged for review")]),
]



def sibling_inventory():
    """An index of every sibling desk present in the tree, with the newest capture timestamp its own data
    files advertise. Built by reading their files at render time so it cannot rot into a hand-kept list.
    Nothing here is read from git history on purpose: a commit date would depend on how deep the checkout is
    (CI builds run against a one-commit clone), and a published table must not change when a reviewer's clone
    differs from the runner's. The inventory covers only the tree this build sees, and it says so."""
    import re
    ts = re.compile(r"20\d{2}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?Z?)?")
    mine = HERE.name
    out = []
    for d in sorted(REPO.iterdir()):
        if not d.is_dir() or not (d.name.startswith("nfl") or d.name in ("line-lab", "own5-desk")):
            continue
        if d.name == mine:
            continue
        has = (d / "index.html").exists()
        newest, ndata = "", 0
        for f in sorted((d / "data").glob("*")) if (d / "data").is_dir() else []:
            ndata += 1
            try:
                blob = f.read_text(encoding="utf-8", errors="ignore")[:400000]
            except OSError:
                continue
            for m in ts.findall(blob):
                if m > newest:
                    newest = m
        out.append(dict(desk=d.name, entry=("index.html" if has else "(no index page at that path)"),
                        newest_date_string_in_their_own_files=newest or "not found in data/",
                        data_files=str(ndata),
                        note=("This desk's own capture is 2026-11-17T00:38-00:55Z; nothing here was re-read "
                              "for this row."),
                        source_url=f"https://github.com/sassnarep3-star/Own5/tree/main/{d.name}"))
    out = sorted([r for r in out if r["newest_date_string_in_their_own_files"].startswith("20")],
                 key=lambda r: r["newest_date_string_in_their_own_files"], reverse=True) + \
        [r for r in out if not r["newest_date_string_in_their_own_files"].startswith("20")]
    with io.open(DATA / "sibling_desks.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["desk"], lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    return out


def rd(name):
    with io.open(DATA / name, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows, (list(rows[0].keys()) if rows else [])


URLKEYS = ("source_url", "url", "source")
NUMISH = {"w", "l", "t", "pf", "pa", "games_played", "n", "listed", "played", "rows", "bytes", "depth_rows_still_listing_player",
          "forecasts_recorded", "settled", "stakes_recorded"}


def badge_for(text):
    t = (text or "").strip().lower()
    if not t:
        return '<span class="blank">—</span>'
    if t in ("yes", "pass", "met", "pass-by-abstention", "final", "fixed here", "resolved upstream"):
        cls = "b-yes"
    elif t in ("no", "fail", "fail-as-expected", "blocked", "rejected", "correction", "data defect, fixed here"):
        cls = "b-no"
    elif t.startswith(("part", "open", "armed", "registered", "shadow", "blocked", "awaiting", "not ", "model", "policy")):
        cls = "b-part"
    else:
        cls = "b-un"
    return f'<span class="badge {cls}">{html.escape(text)}</span>'


def render_rows(rows, fields, forced_status=None):
    out = []
    for r in rows:
        cells = []
        for k in fields:
            v = (r.get(k) or "").strip()
            cls = ' class="num"' if k in NUMISH and v.replace(".", "").replace("-", "").replace("%", "").isdigit() else ""
            if k in ("status", "result", "changed", "matches_game_log", "pct_agrees", "net_agrees", "answer_status",
                     "decision_status", "gate_status", "registration_state", "verification_status"):
                cells.append(f"<td>{badge_for(v)}</td>")
            elif v == "":
                cells.append(f'<td{cls}><span class="blank">—</span></td>')
            elif len(v) > 150:
                cells.append(f"<td{cls}>{html.escape(v)}</td>")
            else:
                cells.append(f"<td{cls}>{html.escape(v)}</td>")
        link = next((r.get(k) for k in URLKEYS if (r.get(k) or "").strip()), "")
        if link.startswith("http"):
            kind = "3P" if "third" in (r.get("source_class", "") + r.get("kind", "")).lower() else "official"
            cells.append(f'<td><a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer">{kind} ↗</a></td>')
        elif link:
            cells.append(f'<td><a href="{html.escape(link)}">repo artefact ↗</a></td>')
        else:
            cells.append('<td><span class="badge b-un">UNVERIFIED · blank by policy (no official value exists)</span></td>')
        out.append("<tr>" + "".join(cells) + "</tr>")
    head = "".join(f"<th>{html.escape(k.replace('_', ' '))}</th>" for k in fields) + "<th>provenance</th>"
    return f'<div class="tblwrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(out)}</tbody></table></div>'


def page(name, title, intro, blocks, active=None, extra_head=""):
    nav = []
    for grp, items in NAV:
        nav.append(f'<div class="grp">{grp}</div>')
        for fn, label in items:
            nav.append(f'<a href="{fn}" class="{"on" if fn == name else ""}">{label}</a>')
    body = []
    for b in blocks:
        kind = b[0]
        if kind == "h":
            body.append(f"<h2>{b[1]}</h2>")
            if len(b) > 2 and b[2]:
                body.append(f'<p class="sub">{b[2]}</p>')
        elif kind == "p":
            body.append(f"<p class='sub'>{b[1]}</p>")
        elif kind == "note":
            body.append(f'<div class="note {b[1]}">{b[2]}</div>')
        elif kind == "cards":
            items = "".join(f'<div class="card"><span>{c[0]}</span><b>{c[1]}</b><small style="color:var(--dim);font-size:12px">{c[2]}</small></div>' for c in b[1])
            body.append(f'<div class="cards">{items}</div>')
        elif kind == "table":
            rows, fields = rd(b[1])
            keep = b[2] if len(b) > 2 and b[2] else fields
            fields = [k for k in keep if k in fields] or fields
            body.append(render_rows(rows, fields))
            if len(b) > 3 and b[3]:
                body.append(f'<p class="sub">{b[3]}</p>')
        elif kind == "list":
            body.append("<ul class='tight'>" + "".join(f"<li>{x}</li>" for x in b[1]) + "</ul>")
            if len(b) > 2 and b[2]:
                body.append(f'<p class="sub">{b[2]}</p>')
    cur = name
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · Own5 currency desk</title>
<meta name="description" content="NFL line-origination currency and corrections desk: verified record, availability snapshots, roster events, originated Week 11 lines and a decision-readiness register.">
<link rel="stylesheet" href="assets/desk.css"></head><body><div class="shell">
<nav class="side"><div class="brand">OWN5 · CURRENCY &amp; CORRECTIONS<small>session 35a1feb2 · {AS_OF}</small></div>
{''.join(nav)}
<div class="grp">Other NFL desks</div>
<a href="../nfl-desk-e46fb855/index.html">e46fb855 (2026-11-15)</a>
<a href="../nfl-readiness-cba42531/index.html">cba42531 (2026-11-15)</a>
<a href="../nfl-desk-864d5668/index.html">864d5668 (2026-11-13)</a>
<a href="../nfl-desk-d38e90c5/index.html">d38e90c5 (2026-11-14)</a>
<a href="../nfl-decision-desk/index.html">decision-desk</a>
<div class="grp">Repository</div>
<a href="https://github.com/sassnarep3-star/Own5" target="_blank" rel="noopener noreferrer">GitHub ↗</a>
<a href="https://www.nfl.com/standings/league/2026/REG" target="_blank" rel="noopener noreferrer">League standings ↗</a>
</nav><main><h1>{html.escape(title)}</h1><p class="sub">{intro}</p>{''.join(body)}
<footer>Own5 currency &amp; corrections desk · captures {CAPTURE} · independent research, paper only, no bets placed ·
not affiliated with the NFL. Blank cells are unverified by design, never zero.</footer></main></div>
<script src="assets/desk.js" defer></script></body></html>
"""


def index_cards():
    req, _ = rd("requirements_master.csv")
    c = Counter(r["status"].split(" ")[0] for r in req)
    gates, _ = rd("gates.csv")
    passed = sum(1 for g in gates if g["status"].startswith("PASS"))
    flagged, _ = rd("flagged.csv")
    st, _ = rd("standings_verified.csv")
    corr, _ = rd("correlations.csv")
    stale, _ = rd("roster_event_staleness_audit.csv")
    n_stale = sum(1 for r in stale if r["depth_rows_still_listing_player"] not in ("", "0"))
    return c, passed, len(flagged), len(st), len(corr), n_stale


def build():
    dist = HERE
    (dist / "assets").mkdir(exist_ok=True)
    (dist / "assets/desk.css").write_text(CSS, encoding="utf-8")
    (dist / "assets/desk.js").write_text(
        "document.querySelectorAll('table').forEach(function(t){t.setAttribute('tabindex','0');});\n",
        encoding="utf-8")
    (dist / ".nojekyll").write_text("", encoding="utf-8")

    c, passed, nflag, nst, ncorr, nstale = index_cards()
    tot = sum(c.values())
    intro_index = (
        f"Everything on this desk was read from the league's own pages between {CAPTURE} on 2026-11-17 and "
        f"re-derived from those captures on every build. It is the freshest layer of the site: the previous "
        f"desk's captures stop at 2026-11-15T23:35Z. {tot} requirement lines are tracked here, one per row, "
        f"each with the gate that blocks it and the number that clears it.")
    blocks = [
        ("cards", [
            ("Requirement lines tracked", f"{tot}", f"{c['MET']} met · {c['PARTIAL']} partial · {c['BLOCKED']} blocked"),
            ("Validation gates passing", f"{passed} / 9", "sample size and market price are the two that hold everything up"),
            ("Verified games in the record", "149", "plus 1 published blank: not kicked off at read time"),
            ("Roster events read from the register", "62", "first time any session has read trades + reserve list"),
            ("Depth rows contradicted by the register", f"{nstale}", "1 in 5 roster events contradicts a published depth row"),
            ("Corrections to prior claims on this site", f"{nflag}", "includes two claims that do not survive the official record"),
        ]),
        ("h", "What changed since the last desk's capture",
         "Four Week 10 games finished and are now in the record; the standings were re-read and reconcile "
         "32 of 32 clubs against the game-by-game log; two artefacts nobody had ever read (the trades "
         "register and the reserve list) are now read; and Week 11 was registered before kickoff."),
        ("list", [
            "<b>Week 10 settled.</b> Four games that the 2026-11-15 desk published as blank are final "
            "(Rams 34 Cardinals 6, Seahawks 21 Raiders 13, 49ers 46 Cowboys 40, Steelers 18 Bengals 38). "
            "<b>Chargers at Ravens is still blank</b> — it had not kicked off when this was read. "
            "<a href='https://www.nfl.com/schedules/2026/by-week/week-10' target='_blank' rel='noopener noreferrer'>week-10 page ↗</a>",
            "<b>Standings reconciled.</b> 32 rows read; games played implied by them (298) equals exactly "
            "twice the 149 verified games, and points for across the league equals points against (6880 = 6880). "
            "That balance is what catches a duplicated or dropped fixture.",
            "<b>A data defect found and fixed.</b> The carried-forward results feed keys two clubs as LAR and "
            "ARI while the standings page uses LA and AZ. Joining by code silently drops nine games per club; "
            "the league-wide totals still balanced, so only the per-club reconciliation caught it.",
            "<b>The reserve list and trades register are read for the first time.</b> 12 trades, 50 "
            "reserve-list rows, and the join against depth: 13 depth rows still list a player the league "
            "register says left or went on injured reserve.",
            "<b>Two prior claims do not survive the record.</b> &ldquo;No market price of any kind exists in "
            "this repo&rdquo; is wrong (a 7,548-game log carries spreads on 7,439 rows). &ldquo;Baltimore put "
            "both quarterbacks on IR&rdquo; is not in the register as read; what exists is a league report of "
            "&ldquo;out 6–9 weeks&rdquo;, which is a medical status, not a roster event.",
            "<b>Week 11 registered before kickoff.</b> 13 fixtures × 3 stages (side, then total, then "
            "moneyline), 39 snapshots recorded at 00:55Z on 2026-11-17 against a first kickoff of "
            "2026-11-19T20:15Z. The market column is empty and the difference column reads undefined.",
            "<b>The Week 11 availability report does not exist yet.</b> The reg11 URL serves the Week 10 "
            "report and both clubs' game centres say so explicitly. That is recorded as an empty capture, "
            "not as an all-clear.",
        ], "Each item links to the table that holds it."),
        ("h", "The five decisions that unlock the rest", "Everything below is a one-line decision, not a project."),
        ("table", "suggestions_register.csv", ["id", "suggestion", "recommended_path", "cost_to_try", "what_it_unlocks", "decision_status"]),
        ("note", "amber",
         "<b>How to read a blank cell.</b> A blank means no official value exists for that field, and the "
         "row says so. It is never zero, never &ldquo;close to&rdquo;, and never filled from a guess. "
         "A value labelled <i>third-party</i> comes from a hashed in-repo mirror that is not the league's own "
         "publication; the brief's policy gate decides whether those numbers may ever be used, so they are "
         "kept in separate tables and off the leaderboard."),
        ("h", "Every desk on this brief, in one table", "built from the sibling directories in this checkout — "
                "the date column is the newest 2026 date string a desk's own files contain, which may be a "
                "capture stamp or a scheduled kickoff, so read it with that in mind; "
                "the root index is owned by the integration session, so this is the desk's own view of the field"),
        ("table", "sibling_desks.csv", ["desk", "entry", "newest_date_string_in_their_own_files",
                                        "data_files", "note"],
         "Two things this row cannot tell you: whether a desk's numbers are still true, and whether two desks "
         "disagree. The timestamp is the newest one that desk's own <code>data/</code> files advertise "
         "(bottom rows publish none), so it says when a file was written, nothing more. The corrections this desk published against "
         "several of them are on the <a href='flagged.html'>flagged page</a>."),
        ("h", "Where things stand, by category", "",),
        ("list", [
            f"<b>Decision readiness</b> — {tot} rows, one per requirement in the brief: <a href='requirements.html'>the table</a>.",
            "<b>Questions</b> — 18, six answered by today's reads, twelve open with the cheapest route: <a href='questions.html'>register</a>.",
            "<b>Suggestions</b> — 12 paths with a recommendation and a falsifier, none implemented: <a href='suggestions.html'>review page</a>.",
            "<b>Origination</b> — the model, the 13 registered fixtures and the walk-forward scoreboard: <a href='origination.html'>lines</a>.",
            "<b>Competition</b> — strategies, nine gates, the demotion trigger set and the split leaderboard: <a href='competition.html'>gates &amp; leaderboard</a>.",
            "<b>Corrections</b> — 15 published irregularities with their official sources: <a href='flagged.html'>flagged for review</a>.",
        ]),
    ]
    n_siblings = len(sibling_inventory())
    (dist / "index.html").write_text(page("index.html", "NFL line origination — currency & corrections desk",
                                          intro_index, blocks), encoding="utf-8")
    print("siblings indexed:", n_siblings)

    (dist / "executive-summary.html").write_text(page("executive-summary.html", "Executive summary",
        "Written only from the tables on this desk; every number here appears in a table with a source.", [
        ("h", "1. The state of the project in one paragraph", ""),
        ("p", "The machinery to originate NFL lines exists, is deterministic, is sourced, and ran today: "
              "149 verified games feed a frozen ridge model that published 39 pre-kickoff forecasts for the "
              "13 Week 11 fixtures across side, total and moneyline in that order. What does not exist is the "
              "other half of the loop. There is no admitted market price, so no residual; one season of "
              "official results, so no certified sample; no verified depth for 32 of 32 clubs, so no "
              "replacement-quality feature; and no scheduled capture writing history, so no replayable "
              "availability series. Nine validation gates: two pass. Eight registered strategy families: zero "
              "certified. That is not caution, it is the count."),
        ("h", "2. What today's read changed", ""),
        ("list", [
            "The verified record grew from 145 to 149 games and now reconciles with the standings page for "
            "all 32 clubs — after fixing a club-code defect (LAR/ARI against LA/AZ) that had been silently "
            "dropping two clubs' games in any join.",
            "Home-field advantage is not what the conventions assume: over 149 verified finals the mean home "
            "margin is <b>−0.51</b> points (−0.26 excluding eight neutral-site games), home teams won "
            "<b>47.65%</b>. A +2.5 anchor would misprice every side this season.",
            "Designation levels carry almost no information on their own, but designation <i>changes</i> are "
            "rare too: two reads of the same weekly report 1 hour 13 minutes apart differ by nothing across 147 field "
            "values. The informative artefacts are the report's publication days, the roster register, and the "
            "inactive list nobody is capturing.",
            "The reserve list settles why a player is missing from a report (e.g. a quarterback on the injured "
            "reserve list since 11/10 for Miami) and unsettles a claim repeated across desks about Baltimore's "
            "quarterbacks, for which the register carries no move at all.",
            "Roster turnover is not decoration: 13 of 62 dated roster events contradict a published depth row, "
            "including a receiver placed on reserve on 10/28 still listed first-string by his club.",
        ]),
        ("h", "3. The one finding that changes the plan's shape", ""),
        ("note", "", "The brief says a price-data policy must be decided <i>before</i> any backtest is "
                     "published, and an earlier flag on this site says no market price of any kind exists in the "
                     "repo. Both are load-bearing and the second is wrong: a hashed multi-season log in this "
                     "repo carries a spread and total on 7,439 of 7,548 games and moneylines on 5,458 (163 of 272 "
                     "games in 2026). So the blocker is a <b>decision about source class</b>, not a data hunt — "
                     "one paragraph of policy, written into the repo, converts several &ldquo;impossible this "
                     "season&rdquo; gates into &ldquo;computable tomorrow&rdquo;. It also decides whether the "
                     "136-game snap corpus (identified: 12,693 rows across exactly 136 games, weeks 1–9) can "
                     "support the playing-time depth model the brief asks for. Nothing on this desk is labelled "
                     "a backtest, and no backtest number appears on any leaderboard, until that decision exists."),
        ("h", "4. What the model is and is not", ""),
        ("p", "Ridge team-strength on game margins, λ=1.0 on team ratings, home term estimated, trained only on "
              "games finished before the recorded forecast time, residual sd 10.4 points, fitted home term "
              "−0.46. Two total estimators are published side by side with their gap because neither retires: "
              "A wins weeks 5, 7, 9; B wins 6, 8, 10 — and the naive league-average total beat both in weeks 7 "
              "and 9 (MAE 9.38 and 10.99 against 10.39/11.23 and 11.03/11.11). That is the honest scoreboard, "
              "including the part where the model loses to a constant."),
        ("h", "5. What the leaderboard currently says", ""),
        ("p", "Nothing, by construction. Eight families are registered with frozen rule text, a two-sided "
              "falsifier each, and 39 recorded forecasts. Every score cell is blank because Week 11 has not "
              "been played, and the promotion rule says a signal must beat a coin flip, a best-differential "
              "pick and a league-average total before it is reported as anything. Signal and staking are "
              "separate tables so a lucky stake run cannot lift a bad signal."),
        ("h", "6. Recommended next moves, in order", ""),
        ("list", [
            "1 — Decide S-01 (admit the third-party price/snap class for backtesting only). One paragraph. "
            "Everything else on the list gets cheaper after it.",
            "2 — Add the inactive-list capture (S-03a). It is the only artefact that turns &ldquo;suspected "
            "replacement&rdquo; into &ldquo;confirmed starter&rdquo;, and its existence and format were "
            "confirmed today.",
            "3 — Paginate the roster register and re-run the staleness join (S-05). Today's 13 contradictions "
            "are a lower bound, not a total.",
            "4 — Put the seven-day capture series on the schedule already added here (S-06), then re-run the "
            "designation reliability score on official data only (S-08).",
            "5 — Consolidate the eight desks under one index (S-07) and stop answering the same brief in "
            "parallel namespaces (S-12).",
        ]),
        ("h", "7. Standing rejections (kept, because they are the reason the numbers are trustworthy)", ""),
        ("list", [
            "Deriving depth order from jersey number, experience or salary — rejected by the brief and by this desk.",
            "Ranking strategies on season-long ROI — rejected; 149 games cannot separate 53% from 50%.",
            "Parlays and prop combos without a validated joint probability and the operator's void rules — withheld.",
            "Fixed point penalties for missing starters — not applied; there is no availability feature in the model at all.",
            "Filling a blank cell because a plausible number exists — refused at build time by verify.py.",
        ]),
    ]))

    (dist / "requirements.html").write_text(page("requirements.html", "Decision-readiness register",
        "One row per requirement line in the brief. Status, the gate that blocks it, the number that clears "
        f"it, and what this session actually did. {tot} rows: {c['MET']} met, {c['PARTIAL']} partial, "
        f"{c['BLOCKED']} blocked, {c['REJECTED']} rejected by the brief, {c['OPEN']} open decision.", [
        ("table", "requirements_master.csv", None, "Blank status is not used: every row carries a status, and every blocked row names a gate and a clearing number."),
    ]))

    (dist / "questions.html").write_text(page("questions.html", "Questions register",
        "What must be answered before a decision is reasonable — with what we already have, what is missing, "
        "and the cheapest route to the answer. Six were answerable from today's reads.", [
        ("table", "questions_register.csv", None, "Answer status is one of: ANSWERED, ANSWERED-PARTIAL, ANSWERED-PROVISIONALLY, ANSWERED-BY-DESIGN, ANSWERED-AS-NO, ANSWERED-AS-BOUNDED, CORRECTED, NOT ANSWERED, NOT ANSWERABLE HERE, DECISION-NEEDED, ANSWERED-FROM-REPO."),
    ]))

    (dist / "suggestions.html").write_text(page("suggestions.html", "Suggestions — review before anything is implemented",
        "Each suggestion states the options considered, the recommended path, what it costs, what it unlocks, "
        "and what evidence would reverse the call. Nothing on this page is implemented; the status column is a "
        "review queue, not a changelog.", [
        ("note", "", "Review order: S-01 gates S-02, S-08 and the two gates that block certification. "
                     "S-03 and S-04 are independent of it and are the only rows that need data work rather than "
                     "a decision."),
        ("table", "suggestions_register.csv", None, ""),
    ]))

    (dist / "results.html").write_text(page("results.html", "Verified results and standings",
        "The results feed as re-read today, the four games that moved from blank to final, and the six "
        "integrity checks that let this record be trusted at all.", [
        ("h", "Integrity checks on this read", ""),
        ("table", "standings_integrity_checks.csv", None, "Re-run on every build from the raw transcript; a FAIL stops the site build."),
        ("h", "Week 10 — the increment", "Four games finished; one had not kicked off and is published blank.", ""),
        ("table", "results_wk10_increment.csv", None, ""),
        ("h", "What changed between the two dated reads of week 10", ""),
        ("table", "results_feed_changes_wk10.csv", None, "This is the weekly diff the brief asks for: same fixture, two clock times, one line per change."),
        ("h", "Standings, verified club by club against the game-by-game log", ""),
        ("table", "standings_verified.csv", None, "pct and net are recomputed from W/L/T/PF/PA; a mismatch is a defect in the feed, not a rounding difference."),
        ("h", "The combined verified record", "149 finals and one unplayed fixture, weeks 1–10 of 2026.", ""),
        ("table", "results_feed_2026.csv", ["week", "kickoff_date", "away", "home", "away_score", "home_score",
                                            "home_margin", "total_points", "result", "neutral_site", "status", "verification"],
         "Every row here is an official read by a named session. Rows with an empty score are published that way "
         "because the league had not published a final."),
    ]))

    (dist / "availability.html").write_text(page("availability.html", "Availability snapshots",
        "Two dated reads of the same weekly report, the delta between them, the designation census, and the "
        "announcement evidence the report itself does not carry.", [
        ("note", "green", "<b>The delta is the finding.</b> 49 rows and 147 field values compared between "
                          "2026-11-15T23:27Z and 2026-11-17T00:40Z: <b>zero changes</b>. After the report's own "
                          "deadline the file is static, so &ldquo;capture daily until kickoff&rdquo; mostly "
                          "duplicates rows. The clocks that matter are the publication days, the roster "
                          "register, and the inactive list nobody is capturing yet."),
        ("h", "Read delta (what we publish)", ""),
        ("table", "injury_read_delta.csv", None, "A null table is shown as such rather than omitted."),
        ("h", "Read 2, as captured", "Rows the fetcher returned in full. The replacement column is blank by policy: the report names no replacement.", ""),
        ("table", "availability_snapshot_wk10_read2.csv",
         ["team", "player", "position", "injury", "practice_status", "game_status", "read_utc", "coverage", "replacement_named"], ""),
        ("h", "Designation census for the clubs re-read", ""),
        ("table", "availability_census_read2.csv", None, "(blank) is a real value: the club listed the player without a game designation."),
        ("h", "Coverage of this read, stated plainly", ""),
        ("table", "availability_read2_coverage.csv", None, ""),
        ("h", "Announced-starter evidence (dated league reporting, not a designation)", ""),
        ("table", "announced_starter_evidence.csv", None, "Recorded because the brief asks for an announced-starter field that is not an inferred replacement — and this is the only defensible form of it."),
    ]))

    (dist / "roster-events.html").write_text(page("roster-events.html", "Roster and reserve events",
        "The first read of the league's transactions register by any session on this repo, and the join that "
        "turns it into a staleness check on depth.", [
        ("h", "Summary", ""),
        ("table", "roster_event_summary.csv", None, ""),
        ("h", "Depth rows contradicted by the register", "13 of 62 events. Each row is a dated league move against a carried-forward club depth slot.", ""),
        ("table", "roster_event_staleness_audit.csv", ["date_official", "club", "player", "transaction",
         "depth_rows_still_listing_player", "depth_rows_detail", "status"],
         "Where the depth table's own page carried no publication date, that is written into the row rather than assumed."),
        ("h", "Trades, November 2026", "Position is blank because the page publishes it blank.", ""),
        ("table", "trades_register_2026_11.csv", ["date_official", "from_club", "to_club", "player", "transaction", "note"], ""),
        ("h", "Reserve list, November and late October 2026", "Both month pages stopped after ~25 rows: this is a bounded read, not a complete register.", ""),
        ("table", "reserve_register_2026_10_11.csv", ["date_official", "month_read", "club", "player", "transaction"], ""),
    ]))

    (dist / "origination.html").write_text(page("origination.html", "Week 11 origination and the model",
        "Side first, then total, then moneyline. Fair line, market line and difference are three separate "
        "columns; the middle one is empty because no admitted market read exists, and the third says so.", [
        ("cards", [
            ("Fixtures registered", "13", "weeks 11, Nov 19–23"),
            ("Snapshots recorded", "39", "3 stages per fixture"),
            ("Recorded before kickoff by", "43h 20m", "00:55Z Nov 17 vs 20:15Z Nov 19"),
            ("Certified strategies", "0", "see the gates"),
        ]),
        ("h", "The slate as published", ""),
        ("table", "slate_wk11.csv", ["kickoff_date", "away", "home", "kickoff_time_et", "network",
         "fixture_record_away", "fixture_record_home", "venue_from_game_centre", "venue_read"],
         "Venue is filled only where it was read from that fixture's own game centre — 1 of 13. The other 12 say NOT READ."),
        ("h", "Originated markets", "Every row carries the probability and the six inputs that produced it.", ""),
        ("table", "originated_wk11.csv", ["game_id", "away", "home", "stage_1_fair_spread_home",
         "stage_1_home_win_probability", "stage_2_total_estimator_A", "stage_2_total_estimator_B", "stage_2_gap",
         "stage_3_fair_moneyline_home", "market_line", "difference_vs_market", "model_version",
         "recorded_before_kickoff_utc"], "Fair spread is the raw margin rounded to the nearest half point; the unrounded margin is in its own column in the CSV."),
        ("h", "Model card", ""),
        ("table", "model_card.csv", None, ""),
        ("h", "Total estimators, walk-forward (both published until one retires)", ""),
        ("table", "walkforward_totals.csv", None, "Neither estimator is retired. The naive league-average "
         "total beats both in two of six weeks, which is why the control row exists."),
        ("h", "Fixture context, from published schedule facts only", ""),
        ("table", "fixture_context_wk11.csv", None, ""),
    ]))

    (dist / "price-store.html").write_text(page("price-store.html", "Price-snapshot store",
        "The store is a schema plus the model side of every snapshot. The market side is deliberately empty "
        "and the reason is a decision, not a task.", [
        ("h", "Schema", ""),
        ("table", "price_store_schema.csv", None, "terms_state exists because the brief separates the public "
         "analysis layer from the raw row-level store until the terms are read."),
        ("h", "Snapshots recorded this session", "39 rows: 13 fixtures × 3 stages, all MODEL_RECORD.", ""),
        ("table", "price_snapshots.csv", ["snapshot_id", "captured_utc", "stage", "market", "line",
         "model_line", "market_open", "market_close", "difference", "source_class", "note"], ""),
        ("h", "The policy decision that fills the two empty columns", ""),
        ("p", "Two admissible readings. <b>Official-only</b>: no operator or aggregator price may enter, and "
              "then the store stays half-empty, no residual or CLV is publishable, and no strategy can be "
              "certified this season. <b>Labelled second class</b>: the in-repo multi-season log is admitted for "
              "backtesting and residual reporting only, never as a model input and never on the leaderboard; "
              "then G4 becomes computable tomorrow and the escrow stage can open. The second is recommended "
              "with a hard restriction, because the first makes the brief's own validation plan unreachable and "
              "the log's closing-only granularity is stated, not hidden."),
    ]))

    (dist / "analytics.html").write_text(page("analytics.html", "Correlations, luck and the third-party audit",
        "Published correlations use only officially sourced numbers and each carries its n and a 95% interval. "
        "Everything else sits in a withheld or third-party table with the reason.", [
        ("h", "Correlations from the standings read only", ""),
        ("table", "correlations.csv", ["measure", "variables", "r", "n", "ci95_lo", "ci95_hi", "source_class", "read_utc"], ""),
        ("h", "Withheld — and why", ""),
        ("table", "correlations_withheld.csv", None, "Withholding is the default whenever the inputs are not official or the join is one-sided."),
        ("h", "Removal-of-luck panel", "Actual wins minus Pythagorean expected wins; the exponent is a convention and is labelled on every row.", ""),
        ("table", "luck_panel.csv", ["team", "games", "actual_wins", "expected_wins_pythagorean", "luck_wins",
         "luck_z", "one_possession_games", "record_in_one_possession", "blowout_games", "record_in_blowouts"], ""),
        ("h", "Third-party corpus inventory (not used by the model)", ""),
        ("table", "third_party_inventory.csv", None, ""),
        ("h", "Designation play rates — descriptive only", "Computed on the third-party mirror; it answers the calibration question without being admitted as a feature.", ""),
        ("table", "designation_play_rate.csv", ["designation", "played", "active_no_snaps", "not_in_game", "listed",
         "play_rate", "ci95_lo", "ci95_hi", "seasons", "source_class"],
         "Universe is limited to games whose participation sheet exists, because a missing row outside that "
         "universe proves nothing. Out-designated players essentially never appear, which is the point: the "
         "designation is an instruction, not a prediction."),
        ("h", "Hashed third-party assets", ""),
        ("table", "third_party_asset_register.csv", None, ""),
    ]))

    (dist / "competition.html").write_text(page("competition.html", "Strategies, gates, leaderboard",
        "Pre-registered families, the nine gates with today's measured value, the demotion triggers, the "
        "controls, and the two leaderboards — signal and staking, never merged.", [
        ("h", "Registered strategy families", ""),
        ("table", "strategies_register.csv", ["id", "family", "division", "market_stage", "inputs_allowed",
         "signal_hypothesis", "falsifier_if_the_signal_is_wrong", "falsifier_if_it_is_never_published",
         "gates_failed_now", "registration_state"], "Full frozen rule text is in the CSV download at the bottom of this desk's data directory."),
        ("h", "Validation gates", ""),
        ("table", "gates.csv", None, ""),
        ("h", "Demotion gate — a live strategy goes back to paper when any trigger fires", ""),
        ("table", "demotion_gate.csv", None, ""),
        ("h", "Controls every run must beat", ""),
        ("table", "controls.csv", None, ""),
        ("h", "Divisions and how each is scored", ""),
        ("table", "leaderboard_divisions.csv", None, ""),
        ("h", "Leaderboard — signal only (probability quality)", "No backtest number appears here, ever.", ""),
        ("table", "leaderboard_signal.csv", None, ""),
        ("h", "Leaderboard — staking (same probabilities, different stake rule)", ""),
        ("table", "leaderboard_staking.csv", None, ""),
    ]))

    (dist / "verification.html").write_text(page("verification.html", "Verification log",
        "Twenty-two checks run against this desk's own outputs and against claims carried forward from earlier "
        "sessions. The build fails if any of them breaks. Twelve inputs are hash-pinned; every derived table is "
        "pinned by rebuilding it and comparing bytes instead.", [
        ("h", "Checks run", ""),
        ("table", "repo_audit.csv", None, ""),
        ("h", "Method", ""),
        ("list", [
            "<b>Read then re-derive.</b> Raw transcript → CSV → page. The site is never hand-edited; "
            "<code>engine.py</code> regenerates every derived table and <code>verify.py</code> rebuilds it and "
            "compares bytes.",
            "<b>Row-level provenance.</b> <code>verify.py</code> walks the generated HTML: every body row must "
            "end in an official link, a labelled third-party link, or an UNVERIFIED badge.",
            "<b>Transcript containment.</b> Every number published in the standings and results tables must "
            "appear in the raw transcript, so a table cannot quietly gain a value the read did not contain.",
            "<b>Capture integrity.</b> SHA-256 of every raw file and of each carried-forward input is recorded "
            "in the manifest and re-checked on every build.",
            "<b>Cross-source reconciliation.</b> Standings against the game-by-game log, club by club — the "
            "check that found the club-code defect.",
            "<b>Unit tests.</b> The scorer, the correlation interval, the play-rate universe rule, the alias "
            "map, and the no-invention rules are tested directly.",
        ]),
        ("h", "Pinned inputs", "the hash proves the file on disk is the file that was read or written; "
                               "nothing below is edited by hand after the fact"),
        ("table", "manifest.csv", None, "A prior desk's capture appears here as a read-only input with its own "
                                        "hash. That is how a carried-forward number can be shown to be unchanged "
                                        "since this session read it &mdash; and it is what would expose an edit "
                                        "made after the fact."),
        ("h", "Limits of this verification", ""),
        ("note", "amber", "The hash proves the transcript was not edited after the read, not that the league "
                           "served those bytes. The fetcher, not curl, is the only channel that reaches the "
                           "league's site from this sandbox. Third-party figures come from in-repo mirrors of "
                           "aggregator releases; they are labelled, kept out of the model, and out of the "
                           "leaderboard. Nothing here is a claim that any strategy has an edge."),
    ]))

    (dist / "flagged.html").write_text(page("flagged.html", "Flagged for review",
        "Irregularities, corrections to prior claims on this site, and things that are blocked by the world "
        "rather than by the code. None of these block the merge; all of them are published with a source.", [
        ("cards", [
            ("Items published", str(nflag), "each with what the official record says"),
            ("Corrections to prior claims", "4", "two of them change what a model may assume"),
            ("Blocking on external state", "3", "report publication, game completion, policy decision"),
        ]),
        ("table", "flagged.csv", ["id", "kind", "title", "what_the_official_record_says", "what_we_do_about_it"], ""),
    ]))

    (dist / "sources.html").write_text(page("sources.html", "Sources and capture manifest",
        "Every page read, when it was read, what it contained and what it is used for — plus the hash of every "
        "artefact this desk's numbers were derived from.", [
        ("table", "sources.csv", None, ""),
        ("h", "Manifest (raw reads and pinned inputs)", ""),
        ("table", "manifest.csv", ["path", "bytes", "sha256", "retrieved", "read_channel"], ""),
    ]))

    counts = dict(files=len(list(dist.glob("*.html"))), requirements=tot)
    print("built", counts)


if __name__ == "__main__":
    build()

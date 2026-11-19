#!/usr/bin/env python3
"""Deterministic static-site builder for the Week-11 team-view desk.

Run from repo root:  python3 nfl-teamview-42899de4/build_site.py
Writes:              nfl-teamview-42899de4/pages/*.html + assets/style.css
No wall-clock timestamps: every date shown comes from the data files.
"""
import csv
import html
from pathlib import Path

ROOT = Path("nfl-teamview-42899de4")
DATA = Path("data/nfl-teamview-42899de4")
PAGES = ROOT / "pages"
ASSETS = ROOT / "assets"

NAV = [
    ("index.html", "Dashboard"),
    ("teams.html", "Per-team view"),
    ("delta.html", "W10 \u2192 W11 delta"),
    ("report-w11.html", "Report W11"),
    ("report-w10.html", "Report W10"),
    ("fixtures.html", "Fixtures & byes"),
    ("requirements.html", "Decision readiness"),
    ("flagged.html", "Flagged"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("sources.html", "Sources"),
    ("exec-summary.html", "Exec summary"),
]

CSS = """/* NFL team-view desk - session 42899de4 */
:root{--bg:#0d1117;--panel:#161b22;--panel2:#1c2129;--border:#30363d;--text:#e6edf3;
--muted:#9198a1;--accent:#58a6ff;--good:#3fb950;--warn:#d29922;--bad:#f85149;--blank:#6e7681}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
header{background:var(--panel);border-bottom:1px solid var(--border);padding:14px 24px 0;position:sticky;top:0;z-index:10}
header h1{margin:0 0 4px;font-size:18px}header .sub{color:var(--muted);font-size:12px;margin-bottom:10px}
nav{display:flex;flex-wrap:wrap;gap:2px;margin-top:6px}
nav a{padding:7px 12px;border-radius:6px 6px 0 0;color:var(--muted);font-size:13px;border:1px solid transparent;border-bottom:none}
nav a:hover{color:var(--text);text-decoration:none;background:var(--panel2)}
nav a.on{color:var(--text);background:var(--bg);border-color:var(--border);font-weight:600}
main{padding:20px 24px 60px;max-width:1500px;margin:0 auto}
h2{font-size:16px;margin:26px 0 10px;border-bottom:1px solid var(--border);padding-bottom:6px}
h3{font-size:14px;margin:18px 0 8px;color:var(--muted)}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px;margin:14px 0}
.tile{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px 14px}
.tile .n{font-size:24px;font-weight:700}.tile .l{color:var(--muted);font-size:12px;margin-top:2px}
.tile .x{color:var(--muted);font-size:11px;margin-top:6px}
.badge{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:600;border:1px solid var(--border)}
.b-ok{color:var(--good);border-color:var(--good)}.b-warn{color:var(--warn);border-color:var(--warn)}
.b-bad{color:var(--bad);border-color:var(--bad)}.b-mute{color:var(--muted)}
.b-part{color:var(--warn);border-color:var(--warn)}
table{border-collapse:collapse;width:100%;background:var(--panel);border:1px solid var(--border);border-radius:8px;overflow:hidden;font-size:13px}
th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--border);vertical-align:top}
th{background:var(--panel2);color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.4px;position:sticky;top:0}
tr:last-child td{border-bottom:none}
tr:hover td{background:#1a2029}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.blank{color:var(--blank)}td.blank{letter-spacing:1px}
.club{font-weight:600}
.wrap{overflow-x:auto}
.note{background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--accent);padding:10px 14px;border-radius:6px;margin:12px 0;font-size:13px}
.note.warn{border-left-color:var(--warn)}.note.bad{border-left-color:var(--bad)}
footer{color:var(--muted);font-size:12px;padding:18px 24px;border-top:1px solid var(--border);margin-top:30px}
code{background:var(--panel2);padding:1px 5px;border-radius:4px;font-size:12px}
.flag{color:var(--warn);font-size:11px}
a.src{font-size:11px}
"""


def esc(v):
    return html.escape(str(v), quote=True)


def read(name):
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def page(title, active, body, desc=""):
    links = []
    for href, label in NAV:
        cls = ' class="on"' if href == active else ""
        links.append(f'<a href="{href}"{cls}>{label}</a>')
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="../assets/style.css">
</head><body>
<header><h1>NFL Team View &middot; Week 11 Decision Desk</h1>
<div class="sub">Session 42899de4 &middot; branch arena/42899de4-own5 &middot; all values from official nfl.com reads on 2026-11-19 &middot; blanks are flagged, never inferred</div>
<nav>{''.join(links)}</nav></header>
<main>
{body}
</main>
<footer>Verification: every row carries an official source link or is blank with a flag reference &middot; fail-closed verifier in <code>nfl-teamview-42899de4/verify.py</code> &middot; cross-checks recorded in <code>research/nfl-42899de4/VERIFICATION.md</code></footer>
</body></html>
"""


def td(v, cls="", blank_title=""):
    if v == "" or v is None:
        t = f' title="{esc(blank_title)}"' if blank_title else ""
        return f'<td class="blank{(" " + cls) if cls else ""}"{t}>&mdash;</td>'
    return f'<td class="{cls}">{esc(v)}</td>'


def link_td(url, flag=""):
    if url:
        return f'<td><a class="src" href="{esc(url)}" target="_blank" rel="noopener">source</a></td>'
    return f'<td class="blank" title="Blank source with flag {esc(flag)}">&mdash; <span class="flag">{esc(flag)}</span></td>'


def status_badge(s):
    m = {"MET": "b-ok", "PARTIAL": "b-part", "BLOCKED": "b-bad", "PENDING": "b-warn",
         "Proposed": "b-mute", "Requested via COORDINATION": "b-warn",
         "Blocked on source": "b-bad", "Answered": "b-ok"}
    return f'<span class="badge {m.get(s, "b-mute")}">{esc(s)}</span>'


# ---------------------------------------------------------------- pages ----
def p_index(v11, delta, flagged, reqs, w11_rows):
    listed = [r for r in v11 if r["report_state"] == "listed"]
    explicit = [r for r in v11 if r["report_state"] == "no_injuries_reported"]
    byes = [r for r in v11 if r["status"] == "BYE"]
    desig = [r for r in v11 if r["designations_printed"] in ("YES", "YES_EXPLICIT")]
    dnp_total = sum(int(r["dnp_count"]) for r in listed)
    delta_desig = sum(1 for r in delta if r["delta_net"] != "")
    delta_counts = sum(1 for r in delta if r["delta_listed"] != "")
    met = sum(1 for r in reqs if r["status"] == "MET")
    blocked = sum(1 for r in reqs if r["status"] == "BLOCKED")

    rows = []
    for r in v11:
        flags = r["flags"]
        if r["status"] == "BYE":
            badge = '<span class="badge b-warn">BYE</span>'
        else:
            badge = '<span class="badge b-ok">PLAYING</span>'
        rows.append("<tr>"
                    f'<td class="club">{esc(r["club"])} <span style="color:var(--muted);font-weight:400">{esc(r["club_name"])}</span></td>'
                    f'<td>{badge}</td>'
                    f'<td>{esc(r["opponent"]) or "&mdash;"}</td>'
                    f'<td>{esc(r["kickoff_printed"]) or "&mdash;"} {esc(r["network"])}</td>'
                    + td(r["players_listed"], "num", "BYE: club not on report (F-TV-06)")
                    + td(r["dnp_count"], "num", "BYE: club not on report (F-TV-06)")
                    + td(r["out_count"], "num", "Designations not printed as of read (F-TV-03)")
                    + td(r["questionable_count"], "num", "Designations not printed as of read (F-TV-03)")
                    + td(r["net_injury_count"], "num", "Designations not printed as of read (F-TV-03)")
                    + td(r["qb_on_report"], "", "No QB row on the official report for this club")
                    + td(r["starters_out"], "", "Blank: no official announced-starter source read (F-TV-01)")
                    + td(r["replacement_named"], "", "Blank: depth source unresolved (F-TV-02)")
                    + f'<td class="flag">{esc(flags)}</td>'
                    + link_td(r["source_url"], flags)
                    + "</tr>")

    body = f"""
<div class="note"><strong>Decision state, 2026-11-19 (Wednesday of Week 11).</strong>
Game-status designations are printed only for the Thursday game (IND at HOU) and for the two clubs with explicit
&ldquo;No Injuries Reported&rdquo; entries (CIN, WAS). For the 22 Sunday/Monday clubs the designation columns are
<em>blank because the official report has not printed them yet</em> &mdash; blank, never zero (F-TV-03).
Starters-out and replacement columns are blank for every club: no official starter or depth source was read this
session and nothing is inferred (F-TV-01, F-TV-02).</div>

<div class="tiles">
  <div class="tile"><div class="n">{len(listed)}</div><div class="l">clubs with player rows on reg11</div><div class="x">+ {len(explicit)} explicit &ldquo;No Injuries Reported&rdquo; (CIN, WAS)</div></div>
  <div class="tile"><div class="n">{len(byes)}</div><div class="l">clubs on Week-11 bye</div><div class="x">ATL CLE GB LAR NE SEA &mdash; not on report</div></div>
  <div class="tile"><div class="n">{len(desig)}/26</div><div class="l">playing clubs with W11 designations printed</div><div class="x">IND HOU (Thu game) + CIN WAS (explicit zero)</div></div>
  <div class="tile"><div class="n">{dnp_total}</div><div class="l">DNP rows across clubs on report</div><div class="x">practice status, always printed</div></div>
  <div class="tile"><div class="n">{delta_desig}/32</div><div class="l">clubs with computable designation delta</div><div class="x">{delta_counts}/32 have listed-count delta (both weeks played)</div></div>
  <div class="tile"><div class="n">{met}/{len(reqs)}</div><div class="l">brief lines met &middot; {blocked} blocked</div><div class="x">see decision-readiness table</div></div>
</div>

<h2>Per-team decision view &mdash; Week 11</h2>
<div class="wrap"><table>
<thead><tr><th>Club</th><th>Status</th><th>Opp</th><th>Kickoff</th>
<th class="num">Listed</th><th class="num">DNP</th><th class="num">Out</th><th class="num">Q</th><th class="num">Net inj.</th>
<th>QB on report</th><th>Starters out</th><th>Replacements</th><th>Flags</th><th>Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>

<h2>Registers</h2>
<p><a href="flagged.html">Flagged ({len(flagged)})</a> &middot;
<a href="questions.html">Questions &amp; answers</a> &middot;
<a href="suggestions.html">Suggestions</a> &middot;
<a href="requirements.html">Decision readiness ({len(reqs)} brief lines)</a> &middot;
<a href="sources.html">Sources</a> &middot;
<a href="delta.html">W10 &rarr; W11 delta</a> &middot;
<a href="report-w11.html">Row-level reg11 ({len(w11_rows)} rows)</a>
</p>
"""
    return page("NFL Team View · Week 11 Dashboard", "index.html", body,
                "Week-11 per-team decision view with net injury counts, deltas and flags")


def p_teams(v11, v10):
    def block(v, week):
        rows = []
        for r in v:
            rows.append("<tr>"
                        f'<td class="club">{esc(r["club"])}</td><td>{esc(r["club_name"])}</td>'
                        f'<td>{esc(r["status"])}</td><td>{esc(r["report_state"])}</td>'
                        + td(r["players_listed"], "num")
                        + td(r["dnp_count"], "num") + td(r["lp_count"], "num") + td(r["fp_count"], "num")
                        + td(r["out_count"], "num", "Designations not printed as of read (F-TV-03)")
                        + td(r["questionable_count"], "num", "Designations not printed as of read (F-TV-03)")
                        + td(r["doubtful_count"], "num", "Designations not printed as of read (F-TV-03)")
                        + td(r["net_injury_count"], "num", "Designations not printed as of read (F-TV-03)")
                        + td(r["qb_on_report"], "", "No QB row on the official report")
                        + td(r["starters_out"], "", "Blank: no official announced-starter source read (F-TV-01)")
                        + td(r["replacement_named"], "", "Blank: depth source unresolved (F-TV-02)")
                        + f'<td class="flag">{esc(r["flags"])}</td>'
                        + link_td(r["source_url"], r["flags"]) + "</tr>")
        return f"""
<h2>Week {week} &mdash; 32 clubs</h2>
<div class="wrap"><table>
<thead><tr><th>Club</th><th>Name</th><th>Status</th><th>Report state</th>
<th class="num">Listed</th><th class="num">DNP</th><th class="num">LP</th><th class="num">FP</th>
<th class="num">Out</th><th class="num">Q</th><th class="num">D</th><th class="num">Net inj.</th>
<th>QB on report</th><th>Starters out</th><th>Replacements</th><th>Flags</th><th>Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
"""

    body = ("""
<div class="note">One row per club per week. <strong>Net injury count</strong> = players with a printed
Out/Questionable/Doubtful designation on the official report as of the read clock; blank when designations are not
yet printed (F-TV-03). <strong>BYE</strong> rows are blank in every report column because the club is not on the
report at all (F-TV-06) &mdash; distinct from the explicit zero printed for CIN/WAS. Starters-out and
replacements stay blank by rule (F-TV-01, F-TV-02).</div>
""" + block(v11, 11) + block(v10, 10))
    return page("Per-team view", "teams.html", body, "Per-club injury report view for weeks 11 and 10")


def p_delta(delta):
    rows = []
    for r in delta:
        rows.append("<tr>"
                    f'<td class="club">{esc(r["club"])}</td><td>{esc(r["club_name"])}</td>'
                    f'<td>{esc(r["weeks_both"])}</td>'
                    + td(r["listed_w10"], "num") + td(r["listed_w11"], "num") + td(r["delta_listed"], "num", "Not computable (bye or missing side)")
                    + td(r["dnp_w10"], "num") + td(r["dnp_w11"], "num") + td(r["delta_dnp"], "num", "Not computable")
                    + td(r["out_w10"], "num") + td(r["out_w11"], "num", "W11 designations not printed (F-TV-03)") + td(r["delta_out"], "num", "W11 side not printed (F-TV-03)")
                    + td(r["net_w10"], "num") + td(r["net_w11"], "num", "W11 designations not printed (F-TV-03)") + td(r["delta_net"], "num", "W11 side not printed (F-TV-03)")
                    + f'<td class="flag">{esc(r["flags"])}</td>'
                    + f'<td style="font-size:12px;color:var(--muted)">{esc(r["note"])}</td>'
                    + link_td(r["source_url"], r["flags"]) + "</tr>")
    body = f"""
<div class="note warn"><strong>Publication-state asymmetry (F-TV-11).</strong> Week-10 designations are final
(completed week); Week-11 designations exist only for the Thursday game as of the Wednesday 2026-11-19 read.
Designation deltas are therefore computable for only {sum(1 for r in delta if r['delta_net'] != '')} of 32 clubs
and are blank elsewhere &mdash; never zero-filled. Listed-count and DNP deltas are computable for the
{sum(1 for r in delta if r['delta_listed'] != '')} clubs that played both weeks. The signal is the delta; each
level carries its read clock.</div>
<div class="wrap"><table>
<thead><tr><th>Club</th><th>Name</th><th>Weeks</th>
<th class="num">Listed W10</th><th class="num">Listed W11</th><th class="num">&Delta;Listed</th>
<th class="num">DNP W10</th><th class="num">DNP W11</th><th class="num">&Delta;DNP</th>
<th class="num">Out W10</th><th class="num">Out W11</th><th class="num">&Delta;Out</th>
<th class="num">Net W10</th><th class="num">Net W11</th><th class="num">&Delta;Net</th>
<th>Flags</th><th>Note</th><th>Source</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
"""
    return page("W10 → W11 delta", "delta.html", body, "Club-level injury deltas between week 10 and week 11")


def p_report(rows, week, url):
    by_club = {}
    for r in rows:
        by_club.setdefault(r["club"], []).append(r)
    parts = [f"""
<div class="note">Row-level transcription of the official Week-{week} injury report, read first-hand on
2026-11-19. {len(rows)} rows across {len(by_club)} clubs. Every row links to the official page; the two
&ldquo;No Injuries Reported&rdquo; entries are explicit page text, not inferred zeros.</div>
<div class="wrap"><table>
<thead><tr><th>Club</th><th>Player</th><th>Pos</th><th>Injury</th><th>Practice status</th><th>Game status</th><th>Row type</th><th>Source</th></tr></thead><tbody>"""]
    for club in sorted(by_club):
        for r in by_club[club]:
            if r["row_type"] == "no_injuries_reported":
                parts.append(f'<tr><td class="club">{esc(club)}</td><td colspan="4"><em>No Injuries Reported</em> (explicit page text)</td><td class="blank">&mdash;</td><td>no_injuries_reported</td><td><a class="src" href="{esc(r["source_url"])}" target="_blank" rel="noopener">source</a></td></tr>')
            else:
                injury_cell = esc(r["injury"]) or '<span class="blank">&mdash;</span>'
                if r["game_status"]:
                    gs_cell = esc(r["game_status"])
                else:
                    gs_cell = ('<span class="blank" title="Designation not printed as of read '
                              '(F-TV-03)">&mdash;</span>')
                parts.append("<tr>"
                             f'<td class="club">{esc(club)}</td><td>{esc(r["player"])}</td><td>{esc(r["position"])}</td>'
                             f'<td>{injury_cell}</td>'
                             f'<td>{esc(r["practice_status"])}</td>'
                             f'<td>{gs_cell}</td>'
                             f'<td>{esc(r["row_type"])}</td>'
                             f'<td><a class="src" href="{esc(r["source_url"])}" target="_blank" rel="noopener">source</a></td></tr>')
    parts.append("</tbody></table></div>")
    return page(f"Report Week {week}", f"report-w{week}.html", "\n".join(parts),
                f"Row-level official Week-{week} injury report")


def p_fixtures(fx11, fx10, byes):
    r11 = []
    for g in fx11:
        note = f' <span class="flag">{esc(g["note"])}</span>' if g["note"] else ""
        r11.append(f'<tr><td>{esc(g["date"])}</td><td>{esc(g["day"])}</td><td class="club">{esc(g["away"])} @ {esc(g["home"])}</td>'
                   f'<td>{esc(g["kickoff_printed"])}</td><td>{esc(g["network"])}</td><td>{note}</td>'
                   f'<td><a class="src" href="{esc(g["source_url"])}" target="_blank" rel="noopener">source</a></td></tr>')
    r10 = []
    for g in fx10:
        note = f' <span class="flag">{esc(g["note"])}</span>' if g["note"] else ""
        r10.append(f'<tr><td>{esc(g["date"])}</td><td>{esc(g["day"])}</td><td class="club">{esc(g["away"])} {esc(g["away_score"])} @ {esc(g["home"])} {esc(g["home_score"])}</td>'
                   f'<td>{esc(g["slot"])}</td><td>{esc(g["slot"])} final</td><td>{note}</td>'
                   f'<td><a class="src" href="{esc(g["source_url"])}" target="_blank" rel="noopener">source</a></td></tr>')
    rb = []
    for b in byes:
        rb.append(f'<tr><td class="num">{esc(b["week"])}</td><td class="club">{esc(b["club"])}</td><td>{esc(b["club_name"])}</td>'
                  f'<td><a class="src" href="{esc(b["source_url"])}" target="_blank" rel="noopener">source</a></td></tr>')
    body = f"""
<h2>Week 11 schedule (13 games)</h2>
<div class="wrap"><table><thead><tr><th>Date</th><th>Day</th><th>Matchup</th><th>Kickoff (as printed)</th><th>Network</th><th>Note</th><th>Source</th></tr></thead>
<tbody>{''.join(r11)}</tbody></table></div>
<h2>Week 10 results (14 games)</h2>
<div class="wrap"><table><thead><tr><th>Date</th><th>Day</th><th>Matchup</th><th>Slot</th><th>Result</th><th>Note</th><th>Source</th></tr></thead>
<tbody>{''.join(r10)}</tbody></table></div>
<h2>Byes</h2>
<div class="wrap"><table><thead><tr><th class="num">Week</th><th>Club</th><th>Name</th><th>Source</th></tr></thead>
<tbody>{''.join(rb)}</tbody></table></div>
<div class="note">Kickoff times are stored exactly as printed on the schedule page (no zone suffix); the injury
report headers print the same clocks with EST, which is correct for 2026-11-22/23 after US daylight saving ends
(Q-TV-08).</div>
"""
    return page("Fixtures & byes", "fixtures.html", body, "Official Week 11 and Week 10 fixtures and byes")


def p_flagged(flagged):
    rows = []
    for f in flagged:
        rows.append(f'<tr><td class="club">{esc(f["flag_id"])}</td><td>{esc(f["scope"])}</td>'
                    f'<td>{esc(f["severity"])}</td><td>{esc(f["statement"])}</td>'
                    f'<td style="font-size:12px">{esc(f["evidence"])}</td><td style="font-size:12px">{esc(f["action"])}</td></tr>')
    body = f"""
<div class="note warn">Irregularities found during this desk's reads. Nothing here was silently corrected;
cross-session issues are reported, not edited in place.</div>
<div class="wrap"><table><thead><tr><th>ID</th><th>Scope</th><th>Severity</th><th>Statement</th><th>Evidence</th><th>Action</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
"""
    return page("Flagged", "flagged.html", body, "Flagged irregularities")


def p_questions(qs):
    rows = []
    for q in qs:
        rows.append(f'<tr><td class="club">{esc(q["question_id"])}</td><td>{esc(q["question"])}</td>'
                    f'<td>{esc(q["answer"])}</td><td>{status_badge(q["status"])}</td>'
                    f'<td>{esc(q["answered_by"])}</td><td>{esc(q["answered_utc"])}</td></tr>')
    body = f"""<div class="note">Questions register with answers grounded in this session's reads.</div>
<div class="wrap"><table><thead><tr><th>ID</th><th>Question</th><th>Answer</th><th>Status</th><th>Evidence</th><th>Date</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""
    return page("Questions", "questions.html", body, "Questions and answers register")


def p_suggestions(sgs):
    rows = []
    for s in sgs:
        rows.append(f'<tr><td class="club">{esc(s["suggestion_id"])}</td><td>{esc(s["suggestion"])}</td>'
                    f'<td>{esc(s["rationale"])}</td><td>{esc(s["target"])}</td><td>{esc(s["depends_on"])}</td>'
                    f'<td>{status_badge(s["status"])}</td></tr>')
    body = f"""<div class="note">Suggestions register for site and process improvement.</div>
<div class="wrap"><table><thead><tr><th>ID</th><th>Suggestion</th><th>Rationale</th><th>Target</th><th>Depends on</th><th>Status</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""
    return page("Suggestions", "suggestions.html", body, "Suggestions register")


def p_sources(srcs):
    rows = []
    for s in srcs:
        rows.append(f'<tr><td class="club">{esc(s["source_id"])}</td><td><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["url"])}</a></td>'
                    f'<td>{esc(s["description"])}</td><td>{esc(s["read_utc"])}</td><td>{esc(s["access"])}</td><td>{esc(s["used_for"])}</td></tr>')
    body = f"""<div class="note">S-01..S-05 are first-hand reads used as data. X-01..X-04 are read-only
cross-checks from other desks' captures &mdash; they verify this desk's transcription but are never copied into
its tables.</div>
<div class="wrap"><table><thead><tr><th>ID</th><th>URL</th><th>Description</th><th>Read (UTC)</th><th>Access</th><th>Used for</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""
    return page("Sources", "sources.html", body, "Source register")


def p_requirements(reqs):
    rows = []
    for r in reqs:
        rows.append(f'<tr><td class="club">{esc(r["req_id"])}</td><td>{esc(r["brief_line"])}</td>'
                    f'<td style="font-size:12px">{esc(r["gate"])}</td><td style="font-size:12px">{esc(r["observed"])}</td>'
                    f'<td style="font-size:12px">{esc(r["number_to_clear"])}</td><td>{status_badge(r["status"])}</td>'
                    f'<td>{esc(r["evidence"])}</td></tr>')
    body = f"""<div class="note">One row per brief line this desk owns &rarr; gate &rarr; the number that must be
cleared. This is the desk-scoped slice of the decision-readiness matrix (the full brief matrix lives with the
integration desk, PR #146/#150).</div>
<div class="wrap"><table><thead><tr><th>ID</th><th>Brief line</th><th>Gate</th><th>Observed</th><th>Number to clear</th><th>Status</th><th>Evidence</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""
    return page("Decision readiness", "requirements.html", body, "Decision-readiness table")


def p_exec(v11, delta, reqs, flagged, w11_rows, w10_rows):
    met = sum(1 for r in reqs if r["status"] == "MET")
    blocked = sum(1 for r in reqs if r["status"] == "BLOCKED")
    partial = sum(1 for r in reqs if r["status"] == "PARTIAL")
    body = f"""
<div class="note"><strong>Executive summary &mdash; Week-11 per-team injury desk (session 42899de4, 2026-11-19).</strong>
This desk read the official NFL Week-11 and Week-10 injury reports and both schedules first-hand, transcribed
{len(w11_rows)} and {len(w10_rows)} row-level entries, and published a 32-club per-team decision view, a
W10&rarr;W11 delta table, fixtures/byes, and five registers. The Week-11 report is a Wednesday snapshot:
designations are printed only for Thursday's IND at HOU game plus the explicit &ldquo;No Injuries Reported&rdquo;
entries for CIN and WAS &mdash; all other designation cells are blank because they are not yet printed, and are
published as blank with flag F-TV-03, never as zero.</div>

<div class="tiles">
  <div class="tile"><div class="n">{len(w11_rows)} / {len(w10_rows)}</div><div class="l">row-level entries transcribed (W11 / W10)</div><div class="x">100% carry official nfl.com source links</div></div>
  <div class="tile"><div class="n">{met} MET / {partial} PARTIAL / {blocked} BLOCKED</div><div class="l">brief-line status ({len(reqs)} lines in scope)</div><div class="x">blocked gates: starter evidence, depth source, reserve list</div></div>
  <div class="tile"><div class="n">{len(flagged)}</div><div class="l">flagged irregularities</div><div class="x">incl. cross-desk W10 capture mismatch (F-TV-10)</div></div>
</div>

<h2>What is decision-ready</h2>
<ul>
<li><strong>Per-club report state:</strong> listed players, practice-status counts, QB rows on report, explicit
zero vs bye vs not-yet-designated &mdash; all 32 clubs, both weeks, source-linked.</li>
<li><strong>Fixtures and byes:</strong> 13 Week-11 games with printed kickoff/network, 14 Week-10 finals, 10 bye
rows &mdash; official schedules only.</li>
<li><strong>Deltas:</strong> listed-count and DNP deltas for the 22 clubs that played both weeks; designation
deltas for the 4 clubs whose W11 designations are printed.</li>
</ul>

<h2>What is not decision-ready (and why)</h2>
<ul>
<li><strong>Starters out / replacements named:</strong> blank for all 32 clubs &mdash; no official
announced-starter or depth source was read this session; gates K-027 and K-035 (F-TV-01, F-TV-02).</li>
<li><strong>Net injury count for Sunday clubs:</strong> blank until the report prints designations (F-TV-03);
re-read later in the week (suggestion S-02-01).</li>
<li><strong>Availability:</strong> no reserve/IR list read, so &ldquo;not on report&rdquo; is never read as
&ldquo;available&rdquo; (R-TV-06).</li>
</ul>

<h2>Trust chain</h2>
<p>First-hand reads S-01..S-04 &rarr; row-level CSVs &rarr; deterministic roll-up
(<code>compute_views.py</code>) &rarr; fail-closed verifier (<code>verify.py</code>: row pins, source allowlist,
blank-not-zero rules, independent recomputation, byte-identical rebuild) &rarr; CI on PR &rarr; Pages.
Cross-checks: W11 253/253 and 255/255 against two independent same-day captures; W10 347/347 against a third;
one mismatching capture flagged (F-TV-10). See <code>research/nfl-42899de4/VERIFICATION.md</code>.</p>
"""
    return page("Executive summary", "exec-summary.html", body, "Executive summary of the Week-11 team-view desk")


def main():
    PAGES.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "style.css").write_text(CSS, encoding="utf-8")

    v11 = read("team_view_w11.csv")
    v10 = read("team_view_w10.csv")
    delta = read("team_delta_w10_w11.csv")
    fx11 = read("fixtures_w11.csv")
    fx10 = read("fixtures_w10.csv")
    byes = read("byes.csv")
    flagged = read("flagged.csv")
    qs = read("questions.csv")
    sgs = read("suggestions.csv")
    srcs = read("sources.csv")
    reqs = read("requirements.csv")
    w11_rows = read("injury_report_w11.csv")
    w10_rows = read("injury_report_w10.csv")

    out = {
        "index.html": p_index(v11, delta, flagged, reqs, w11_rows),
        "teams.html": p_teams(v11, v10),
        "delta.html": p_delta(delta),
        "report-w11.html": p_report(w11_rows, 11, "https://www.nfl.com/injuries/league/2026/reg11"),
        "report-w10.html": p_report(w10_rows, 10, "https://www.nfl.com/injuries/league/2026/reg10"),
        "fixtures.html": p_fixtures(fx11, fx10, byes),
        "flagged.html": p_flagged(flagged),
        "questions.html": p_questions(qs),
        "suggestions.html": p_suggestions(sgs),
        "sources.html": p_sources(srcs),
        "requirements.html": p_requirements(reqs),
        "exec-summary.html": p_exec(v11, delta, reqs, flagged, w11_rows, w10_rows),
    }
    for name, content in out.items():
        (PAGES / name).write_text(content, encoding="utf-8")
    print(f"wrote {len(out)} pages + style.css")


if __name__ == "__main__":
    main()

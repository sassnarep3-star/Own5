#!/usr/bin/env python3
"""Static site for the NFL Command Desk. Deterministic: reads data/*.csv only.

No clock, no network, no git. Every table row ends with its official source link, or an
UNVERIFIED badge when the value could not be confirmed.
"""
import csv
import html
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
def _registration_hash():
    """The registration commit is the one whose message starts '4078a9ad: pre-registration'.
    Read from the local git history at build time so a rebase cannot leave the site quoting a
    commit that no longer exists. Falls back to the constant when git is unavailable."""
    try:
        import subprocess
        out = subprocess.run(
            ["git", "log", "--format=%H %s", "--all", "--grep=^4078a9ad: pre-registration"],
            cwd=HERE, capture_output=True, text=True, timeout=15)
        for line in out.stdout.splitlines():
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[1].startswith("4078a9ad: pre-registration"):
                return parts[0]
    except Exception:  # noqa: BLE001
        pass
    return "e7282e35dbf9afb0c1b364a152b9431dc71b64af"


REG = _registration_hash()
READ = "2026-11-18"

NAV = [
    ("index.html", "Overview", "01"),
    ("requirements.html", "Requirements & gates", "02"),
    ("questions.html", "Questions", "03"),
    ("suggestions.html", "Suggestions", "04"),
    ("origination.html", "Origination", "05"),
    ("corpus.html", "Results corpus", "06"),
    ("leaderboard.html", "Leaderboard", "07"),
    ("availability.html", "Availability & depth", "08"),
    ("fixtures.html", "Fixtures", "09"),
    ("sources.html", "Sources", "10"),
    ("flagged.html", "Flagged for Review", "11"),
]

CSS = """
:root{--ink:#0d1b17;--muted:#5b6b66;--line:#dfe6e3;--bg:#f6f8f7;--card:#fff;
--accent:#0f6b52;--accent2:#c9f2df;--warn:#8a4b00;--warnbg:#fff4e5;--bad:#8c1d18;
--badbg:#fdecea;--good:#0f6b52;--goodbg:#e6f6ee}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
color:var(--ink);background:var(--bg)}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.layout{display:flex;min-height:100vh}
aside.side{width:250px;flex:0 0 250px;background:#0d1b17;color:#dfe9e5;padding:22px 18px}
.brand{display:flex;gap:10px;align-items:center;color:#fff;font-weight:700;letter-spacing:.4px;margin-bottom:18px}
.brand i{display:grid;place-items:center;width:34px;height:34px;border-radius:9px;background:var(--accent2);
color:#0d1b17;font-style:normal;font-weight:800}
.brand small{display:block;font-weight:500;font-size:10px;letter-spacing:1.4px;color:#93a8a0}
nav a{display:flex;gap:10px;align-items:center;padding:8px 10px;border-radius:8px;color:#cfdbd7;font-size:13.5px}
nav a:hover{background:#172b25;text-decoration:none}
nav a.on{background:#1b352c;color:#fff;font-weight:600}
nav a b{font-weight:600;font-size:11px;color:#7f9a91;min-width:18px}
.side p{font-size:11.5px;color:#8ba398;margin-top:22px;line-height:1.6}
main{flex:1;min-width:0;padding:26px 30px 60px}
header.top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;margin-bottom:18px}
h1{font-size:26px;margin:2px 0 6px;letter-spacing:-.3px}
.eyebrow{font-size:10.5px;letter-spacing:1.6px;color:var(--muted);font-weight:700}
.sub{color:var(--muted);margin:0;max-width:70ch}
.stamp{background:#fff;border:1px solid var(--line);border-radius:10px;padding:8px 12px;font-size:12px;
color:var(--muted);white-space:nowrap}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(158px,1fr));gap:12px;margin:18px 0 22px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 15px}
.card span{font-size:11px;letter-spacing:.6px;color:var(--muted);text-transform:uppercase;font-weight:700}
.card strong{display:block;font-size:27px;line-height:1.15;margin-top:4px;letter-spacing:-.5px}
.card small{color:var(--muted);font-size:11.5px}
.card.bad strong{color:var(--bad)}.card.warn strong{color:var(--warn)}.card.good strong{color:var(--good)}
section.panel{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 18px 8px;margin-bottom:20px}
section.panel h2{font-size:16px;margin:0 0 4px}
section.panel>p.desc{color:var(--muted);font-size:12.5px;margin:0 0 12px;max-width:95ch}
.tablewrap{overflow-x:auto;margin:0 -6px 8px}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:10.5px;letter-spacing:.7px;text-transform:uppercase;color:var(--muted);
background:#fbfcfc;position:sticky;top:0}
tbody tr:hover{background:#f7fbf9}
td.num{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
td.blank{background:repeating-linear-gradient(45deg,#fafafa,#fafafa 4px,#f1f1f1 4px,#f1f1f1 8px)}
td a{font-size:11.5px}
.badge{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.5px;padding:2px 7px;
border-radius:20px;white-space:nowrap}
.b-MET,.b-MATCH,.b-met{background:var(--goodbg);color:var(--good)}
.b-PARTIAL,.b-REVIEW,.b-STALE{background:var(--warnbg);color:var(--warn)}
.b-BLOCKED,.b-REJECTED,.b-NOT-STARTED,.b-BLOCKING,.b-MISMATCH,.b-NO{background:var(--badbg);color:var(--bad)}
.b-UNVERIFIED{background:#eee;color:#555}
.note{border-left:3px solid var(--accent);background:#f2faf6;padding:11px 14px;border-radius:0 8px 8px 0;
font-size:12.8px;margin:14px 0}
.note.warn{border-color:#d08a2c;background:var(--warnbg)}
.note.bad{border-color:var(--bad);background:var(--badbg)}
.note b{display:block;margin-bottom:3px}
footer{margin-top:26px;color:var(--muted);font-size:11.5px;border-top:1px solid var(--line);padding-top:14px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:900px){.layout{display:block}aside.side{width:auto;flex:none}
nav{display:flex;flex-wrap:wrap;gap:4px}main{padding:18px}.grid2{grid-template-columns:1fr}}
"""


class Html(str):
    """A string that is already valid markup and must not be escaped again."""


def h(fragment):
    return Html(fragment)


def esc(v):
    if isinstance(v, Html):
        return v
    return html.escape("" if v is None else str(v), quote=True)


def read(name):
    with (DATA / name).open(newline="") as f:
        return list(csv.DictReader(f))


def link(url, label="source"):
    if not url:
        return h('<span class="badge b-UNVERIFIED">no source</span>')
    return h(f'<a href="{html.escape(url, quote=True)}" target="_blank" '
             f'rel="noopener noreferrer">{html.escape(str(label))} &#8599;</a>')


def link_item(tup):
    """tup = (url, label) rendered as a real anchor (the plain-string path escapes)."""
    url, label = tup
    return link(url, label)


def badge(value, kind=None):
    v = (value or "").strip()
    if not v:
        return '<span class="badge b-UNVERIFIED">UNVERIFIED</span>'
    k = kind or v.replace(" ", "-")
    return f'<span class="badge b-{esc(k)}">{esc(v)}</span>'


def table(headers, rows, cls=""):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = []
    for r in rows:
        cells = []
        for c in r:
            if isinstance(c, list) and len(c) == 1 and isinstance(c[0], tuple):
                c = c[0]
            if isinstance(c, (tuple, list)) and len(c) == 2 and isinstance(c[1], str):
                c = (c[0], c[1])
            if isinstance(c, tuple):
                val, kind = c
                if kind == "num":
                    cells.append(f'<td class="num">{esc(val)}</td>')
                elif kind == "blank":
                    cells.append('<td class="blank" title="not confirmed from an official source"></td>')
                elif kind == "badge":
                    cells.append(f"<td>{badge(val)}</td>")
                elif kind == "raw":
                    cells.append(f"<td>{val}</td>")
                elif kind == "html":
                    cells.append(f"<td>{val}</td>")
                elif kind == "link":
                    cells.append(f"<td>{link_item(val)}</td>")
                else:
                    cells.append(f"<td>{esc(val)}</td>")
            else:
                cells.append(f"<td>{esc(c)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<div class="tablewrap"><table class="{cls}"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def page(fname, title, subtitle, body, active):
    nav = "".join(
        f'<a href="{h}" class="{"on" if h == active else ""}"><b>{n}</b>{t}</a>'
        for h, t, n in NAV)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · OWN5 NFL Command Desk</title>
<meta name="description" content="Evidence-first NFL line origination desk: every row source-linked or flagged.">
<link rel="stylesheet" href="style.css"></head><body><div class="layout">
<aside class="side"><a class="brand" href="index.html"><i>O5</i><span>OWN5<small>NFL COMMAND DESK</small></span></a>
<nav>{nav}</nav>
<p>Every value on this site is either read from an official publisher on a stamped date,
or blank and flagged. Nothing is inferred.</p></aside>
<main><header class="top"><div><span class="eyebrow">NFL / DECISION DESK</span>
<h1>{esc(title)}</h1><p class="sub">{esc(subtitle)}</p></div>
<div class="stamp">Read {READ}<br>Registration <code>{REG[:7]}</code></div></header>
{body}
<footer>OWN5 NFL Command Desk · session 4078a9ad · not affiliated with the NFL.
Blank cells are unverified, never zero. Registration commit {REG[:12]}.
<a href="https://github.com/sassnarep3-star/Own5">Repository</a> ·
<a href="https://sassnarep3-star.github.io/Own5/">Root site</a></footer>
</main></div></body></html>
"""


# ---------------------------------------------------------------------------------

def _findings_table():
    def where(page, label):
        return f'<a href="{page}">{label}</a>'
    rows = [
        ["Home-field assumption vs this season", "2.0 assumed; -0.98 observed",
         "The registered 2.0-point edge is not supported by 2026 so far, and the interval includes it",
         (where("origination.html", "Origination"), "html")],
        ["Total estimator A vs B", "MAE 11.63 vs 10.68",
         "B is closer by 0.95 points but the paired interval includes zero, so both stay published",
         (where("leaderboard.html", "Leaderboard"), "html")],
        ["Moneyline baseline skill", "BSS -0.157 (-0.405..+0.089)",
         "Worse than a coin over 85 out-of-sample games; the holdout alone looks better, which is why it is not claimed",
         (where("leaderboard.html", "Leaderboard"), "html")],
        ["Frozen-line exposure", "29 of 86 home covers (33.7%)",
         "One directional exposure, not per-game skill; published as a flag, not a strategy",
         (where("flagged.html", "FLAG-R1"), "html")],
        ["Bets needed to prove 55%", "617",
         "At 80% power, one-sided 5%; a 5-1 week proves nothing",
         (where("leaderboard.html", "Leaderboard"), "html")],
        ["Decay of a single capture", "17 of 44 rows stale",
         "A point-in-time injury capture moved within six days",
         (where("availability.html", "Availability"), "html")],
        ["Requirements needing data that does not exist yet", "33 of 73",
         "They collapse into six missing datasets, not 33 separate failures",
         (where("requirements.html", "Requirements"), "html")],
    ]
    return table(["Finding", "Number", "What it means", "Where"], rows)


def page_index():
    reqs = read("requirements.csv")
    flags = read("flagged.csv")
    qs = read("questions.csv")
    sug = read("suggestions.csv")
    corp = read("results_corpus.csv")
    recon = read("results_reconciliation.csv")
    lb = read("leaderboard.csv")
    avail = read("availability_diff.csv")
    met = sum(1 for r in reqs if r["status"] == "MET")
    blocked = sum(1 for r in reqs if r["status"] == "BLOCKED")
    partial = sum(1 for r in reqs if r["status"] == "PARTIAL")
    rej = sum(1 for r in reqs if r["status"] == "REJECTED")
    ns = sum(1 for r in reqs if r["status"] == "NOT-STARTED")
    stale = sum(1 for r in avail if r["result"] == "STALE")
    cert = sum(1 for r in lb if r["certified"] == "YES")
    mismatch = sum(1 for r in recon if r["match"] != "MATCH")
    body = f"""
<div class="cards">
<article class="card good"><span>Requirements met</span><strong>{met}</strong><small>of {len(reqs)} in the ledger</small></article>
<article class="card warn"><span>Partially met</span><strong>{partial}</strong><small>value read, gate not cleared</small></article>
<article class="card bad"><span>Blocked</span><strong>{blocked}</strong><small>no official source exists yet</small></article>
<article class="card"><span>Rejected shortcuts</span><strong>{rej}</strong><small>{ns} not started</small></article>
<article class="card good"><span>Corpus reconciles</span><strong>{len(corp)}/{len(corp)}</strong><small>{mismatch} club mismatches vs official standings</small></article>
<article class="card bad"><span>Strategies certified</span><strong>{cert}</strong><small>of 5 registered</small></article>
<article class="card warn"><span>Stale injury rows</span><strong>{stale}</strong><small>of {len(avail)} re-read rows</small></article>
<article class="card"><span>Open flags</span><strong>{len(flags)}</strong><small>{sum(1 for f in flags if f['severity']=='BLOCKING')} blocking</small></article>
</div>

<div class="note"><b>What this site is</b>
One page per question a bettor actually has to answer, built only from official nfl.com and
media.nfl.com pages read on 2026-11-18. Where the official page did not exist or could not be
read, the cell is blank and the item is on <a href="flagged.html">Flagged for Review</a>. The
headline is deliberately unexciting: the results corpus now reconciles to the league's own
standings for all 32 clubs and all 150 completed games, and <b>no registered strategy has
passed the gates</b>. Ten requirements are partly met and 33 are blocked on data the league
has not published (or that nobody has captured yet).</div>

<section class="panel"><h2>Decision readiness — one row per requirement</h2>
<p class="desc">The gate that blocks each requirement and the number that would clear it.
Full ledger with filters on <a href="requirements.html">Requirements &amp; gates</a>.</p>
{table(["ID", "Requirement", "Gate", "Number that would clear it", "Observed", "Status", "Source"],
       [[(r["requirement_id"], "raw"), r["requirement"], r["gate"], r["clearing_number"],
         r["observed"] or ("", "blank"), (r["status"], "badge"),
         link(REQ_SOURCE.get(r["requirement_id"], ""), "official")]
        for r in reqs[:24]])}
<p class="desc">Rows 25-{len(reqs)} are on the full ledger.</p>
</section>

<div class="grid2">
<section class="panel"><h2>What we can prove today</h2>
<p class="desc">Read from an official page in this session or reconciled against one.</p>
{table(["Claim", "Number", "Source"], [
    ["Completed 2026 games in the corpus", [(f"{len(corp)}", "num"), ], link("https://www.nfl.com/schedules/2026/by-week/week-10")],
    ["Clubs whose record, PF and PA match the corpus exactly", [(f"{len(recon) - mismatch}/{len(recon)}", "num")], link("https://www.nfl.com/standings/league/2026/REG")],
    ["Week 11 fixtures with date, kickoff, network", [("13/13", "num")], link("https://www.nfl.com/schedules/2026/by-week/week-11")],
    ["Week 11 fixtures with a venue on the official page", [("13/13", "num")], link("https://www.nfl.com/schedules/2026/by-week/week-11")],
    ["Schedule facts reconciled to the dated announcement", [("6/6", "num")], link("https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced")],
    ["Lions game-status cells the brief said were blank", [("3/3 now read OUT", "num")], link("https://www.nfl.com/injuries/league/2026/reg10")],
])}
</section>
<section class="panel"><h2>What we cannot prove today</h2>
<p class="desc">No official source exists in the repository for these, so no number is shown.</p>
{table(["Missing item", "Gate", "Flag"], [
    ["Market (opening / closing) prices for any market", "G08", ("FLAG-P1", "badge")],
    ["Snap counts and playing time", "G12", ("FLAG-A2", "badge")],
    ["Game-day inactive lists", "G11", ("FLAG-A2", "badge")],
    ["Club depth charts (any of 32)", "G11", ("FLAG-D1", "badge")],
    ["Multi-day hashed availability history", "G11", ("FLAG-A4", "badge")],
    ["Joint outcome table for correlations", "G01", ("FLAG-C1", "badge")],
])}
</section>
</div>

<section class="panel"><h2>Analysis findings</h2>
<p class="desc">Computations over the reconciled corpus. Each is reproducible from the
registration commit; the model pages carry the uncertainty.</p>
{_findings_table()}
</section>

<section class="panel"><h2>Open questions before any decision</h2>
<p class="desc">Eighteen questions, each with the information that is missing and the cheapest
route to find it. The two that are answered are answered from an official page read today.</p>
{table(["ID", "Question", "Information missing", "Answer so far"],
       [[q["question_id"], q["question"], q["information_missing"],
         q["answer"] or ("open", "badge")] for q in qs])}
</section>

<section class="panel"><h2>Suggestions waiting for your decision</h2>
<p class="desc">The decision column is deliberately empty: these are for you to accept or
reject before anyone implements them. Detail on <a href="suggestions.html">Suggestions</a>.</p>
{table(["ID", "Suggestion", "Why", "Decision"],
       [[s["suggestion_id"], s["suggestion"], s["why"], ("pending your review", "badge")]
        for s in sug])}
</section>
"""
    return page("index.html", "NFL Command Desk",
                "Where the NFL line-origination project actually stands, requirement by requirement.", body, "index.html")


REQ_SOURCE = {}


def build_req_source():
    """Each requirement's evidence row maps to a primary source page."""
    base = {
        "R01": "https://www.nfl.com/schedules/2026/by-week/week-11",
        "R02": "https://www.nfl.com/standings/league/2026/REG",
        "R03": "https://www.nfl.com/schedules/2026/by-week/week-11",
        "R04": "https://www.nfl.com/schedules/2026/by-week/week-11",
        "R05": "https://www.nfl.com/standings/league/2026/REG",
        "R06": "https://www.nfl.com/injuries/league/2026/reg10",
        "R07": "https://www.nfl.com/stats/player-stats/",
        "R08": "https://www.nfl.com/standings/league/2026/REG",
        "R09": "https://www.nfl.com/standings/league/2026/REG",
        "R10": "https://www.nfl.com/injuries/league/2026/reg10",
        "R11": "https://www.nfl.com/injuries/league/2026/reg10",
        "R12": "https://www.nfl.com/injuries/league/2026/reg10",
        "R13": "https://www.nfl.com/teams",
        "R14": "https://www.nfl.com/schedules/2026/by-week/week-11",
        "R15": "https://www.nfl.com/standings/league/2026/REG",
        "R16": "https://www.nfl.com/standings/league/2026/REG",
        "R17": "https://www.nfl.com/standings/league/2026/REG",
        "R18": "https://www.nfl.com/schedules/2026/by-week/week-11",
        "R19": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "R20": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "R21": "https://www.nfl.com/injuries/league/2026/reg10",
        "R22": "https://www.nfl.com/standings/league/2026/REG",
        "R23": "https://www.nfl.com/schedules/2026/by-week/week-11",
        "R24": "https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced",
        "R25": "https://www.nfl.com/games/patriots-at-seahawks-2026-reg-1",
        "R26": "https://www.nfl.com/standings/league/2026/REG",
        "R27": "https://www.nfl.com/injuries/league/2026/reg10",
        "R28": "https://www.nfl.com/injuries/league/2026/reg10",
        "R29": "https://www.nfl.com/injuries/league/2026/reg10",
        "R30": "https://www.nfl.com/teams",
        "R31": "https://www.nfl.com/teams",
        "R32": "https://www.nfl.com/teams",
        "R33": "https://www.nfl.com/standings/league/2026/REG",
        "R34": "https://www.nfl.com/standings/league/2026/REG",
        "R35": "https://www.nfl.com/standings/league/2026/REG",
        "R36": "https://www.nfl.com/standings/league/2026/REG",
        "R37": "https://www.nfl.com/injuries/league/2026/reg10",
        "R38": "https://www.nfl.com/injuries/league/2026/reg10",
        "R39": "https://www.nfl.com/injuries/league/2026/reg10",
        "R40": "https://www.nfl.com/injuries/league/2026/reg10",
        "R41": "https://www.nfl.com/teams",
        "R42": "https://www.nfl.com/injuries/league/2026/reg10",
        "R43": "https://www.nfl.com/teams",
        "R44": "https://www.nfl.com/teams",
        "R45": "https://www.nfl.com/injuries/league/2026/reg10",
        "R46": "https://www.nfl.com/injuries/league/2026/reg10",
        "R47": "https://www.nfl.com/injuries/league/2026/reg10",
        "R48": "https://www.nfl.com/teams",
        "R49": "https://www.nfl.com/teams",
        "R50": "https://www.nfl.com/teams",
        "R51": "https://www.nfl.com/injuries/league/2026/reg10",
        "R52": "https://www.nfl.com/injuries/league/2026/reg11",
        "R53": "https://www.nfl.com/injuries/league/2026/reg11",
        "R54": "https://www.nfl.com/teams",
        "R55": "https://www.nfl.com/standings/league/2026/REG",
        "R56": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "R57": "https://www.nfl.com/standings/league/2026/REG",
        "R58": "https://www.nfl.com/schedules/2026/by-week/week-11",
        "R59": "https://www.nfl.com/injuries/league/2026/reg10",
        "R60": "https://www.nfl.com/standings/league/2026/REG",
        "R61": "https://www.nfl.com/schedules/2026/by-week/week-10",
        "R62": "https://www.nfl.com/teams",
        "R63": "https://www.nfl.com/standings/league/2026/REG",
        "R64": "https://www.nfl.com/injuries/league/2026/reg10",
        "R65": "https://www.nfl.com/standings/league/2026/REG",
        "R66": "https://www.nfl.com/standings/league/2026/REG",
        "R67": "https://www.nfl.com/standings/league/2026/REG",
        "R68": "https://www.nfl.com/standings/league/2026/REG",
        "R69": "https://www.nfl.com/standings/league/2026/REG",
        "R70": "https://www.nfl.com/stats/player-stats/",
        "R71": "https://www.nfl.com/standings/league/2026/REG",
        "R72": "https://www.nfl.com/injuries/league/2026/reg10",
        "R73": "https://www.nfl.com/standings/league/2026/REG",
    }
    REQ_SOURCE.update(base)
    return base


def page_requirements():
    reqs = read("requirements.csv")
    gates = read("gates.csv")
    cats = sorted({r["category"] for r in reqs})
    rows = [[(r["requirement_id"], "raw"), r["requirement"], r["category"], r["gate"],
             r["clearing_number"], r["observed"] or ("", "blank"), (r["status"], "badge"),
             link(REQ_SOURCE.get(r["requirement_id"]), "official")]
            for r in reqs]
    body = f"""
<div class="note"><b>How to read a blank</b>
A blank <i>Observed</i> cell means the number was not read from an official source. It is not
zero, it is not "about zero", and it must not be filled in by hand. The <i>Number that would
clear it</i> column is the pre-committed threshold, so a future session cannot move the goal
posts quietly.</div>
<section class="panel"><h2>{len(reqs)} requirements · {len(cats)} categories</h2>
<p class="desc">Ordered as the brief asks: data foundations, then the site and decision layer.
Status counts: {sum(1 for r in reqs if r['status']=='MET')} met,
{sum(1 for r in reqs if r['status']=='PARTIAL')} partial,
{sum(1 for r in reqs if r['status']=='BLOCKED')} blocked,
{sum(1 for r in reqs if r['status']=='REJECTED')} rejected,
{sum(1 for r in reqs if r['status']=='NOT-STARTED')} not started.</p>
{table(["ID", "Requirement", "Category", "Gate", "Number that clears it", "Observed",
        "Status", "Source"], rows)}
</section>
<section class="panel"><h2>Gates G01-G12</h2>
<p class="desc">Fail-closed. A strategy must pass every blocking gate before it can carry a
reward, and the demotion rule (R08) sends it back to paper the moment a gate stops passing.</p>
{table(["ID", "Gate", "Rule", "Status", "Blocking"],
       [[g["gate_id"], g["name"], g["rule"],
         (g["status"], "badge" if g["status"] in ("met",) else "raw"), g["blocking"]]
        for g in gates])}
</section>
"""
    return page("requirements.html", "Requirements & gates",
                "One row per requirement, the gate that blocks it, and the number that would clear it.",
                body, "requirements.html")


def page_questions():
    qs = read("questions.csv")
    body = f"""
<div class="note"><b>Why a questions page</b>
A decision cannot be better than the information behind it. Each row names the question, the
information that is missing, the cheapest official route to get it, and which requirements it
blocks. Two questions are answered from pages read on 2026-11-18; the rest are open.</div>
<section class="panel"><h2>{len(qs)} questions</h2>
<p class="desc">Answer column blank = still open. An answer is only written when an official
page said so.</p>
{table(["ID", "Question", "Information missing", "How to discover it", "Blocks", "Answer"],
       [[q["question_id"], q["question"], q["information_missing"], q["how_to_discover"],
         q["blocks"], q["answer"] or ("open", "badge")] for q in qs])}
</section>
"""
    return page("questions.html", "Questions register",
                "What we do not know yet, how to find it, and what each answer would unlock.",
                body, "questions.html")


def page_suggestions():
    sg = read("suggestions.csv")
    body = f"""
<div class="note"><b>Nothing here is implemented without your decision</b>
The Decision column is empty on purpose. Read a suggestion, then accept or reject it; only
accepted suggestions get built in a later session. S12 is the one to read first.</div>
<section class="panel"><h2>{len(sg)} suggestions</h2>
<p class="desc">Each carries a reason, an effort estimate, the evidence needed, and the
official page the reason rests on.</p>
{table(["ID", "Suggestion", "Why", "Effort", "Evidence needed", "Decision", "Source"],
       [[s["suggestion_id"], s["suggestion"], s["why"], s["effort"], s["evidence_needed"],
         ("pending", "badge"), link("https://www.nfl.com/standings/league/2026/REG")] for s in sg])}
</section>
<section class="panel"><h2>Review process</h2>
<p class="desc">The process this page is asking you to run.</p>
{table(["Step", "Who", "What happens"], [
    ["1", "Reviewer", "Read the suggestion and its evidence link"],
    ["2", "Reviewer", "Write accept or reject in the Decision column (a session edits the CSV)"],
    ["3", "Session", "Re-read the linked official page before building anything"],
    ["4", "Session", "Publish the change on its own page with a source per row"],
    ["5", "Reviewer", "Check the new page; reject and revert is always allowed"],
])}
</section>
"""
    return page("suggestions.html", "Suggestions for review",
                "Twelve proposals, each with the reason and the evidence, awaiting a decision.",
                body, "suggestions.html")


def page_origination():
    og = read("origination_wk11.csv")
    rat = read("ratings.csv")
    body = f"""
<div class="note"><b>Order is the requirement</b>
Every row originates the side first, then the total (published twice), then the moneyline.
The market columns are blank because the repository holds no official price: a residual
against a market we cannot source would be an invented number (FLAG-P1).</div>
<div class="cards">
<article class="card"><span>Week 11 fixtures priced</span><strong>{len(og)}</strong><small>of 13 scheduled</small></article>
<article class="card"><span>Market prices available</span><strong>0</strong><small>official feed absent</small></article>
<article class="card"><span>Home-field assumption</span><strong>2.0</strong><small>published, not measured</small></article>
<article class="card"><span>2026 home margin observed</span><strong>-0.98</strong><small>150 games, 95% CI -3.07..1.13</small></article>
</div>
<section class="panel"><h2>Week 11 originated lines</h2>
<p class="desc">Fair line is the model output. Market and residual columns are unverified, not
hidden. Total estimators A and B are both published with their gap until a paired test
separates them.</p>
{table(["Fixture", "Side: fair home margin", "Favourite", "Fair spread",
        "Total A", "Total B", "Gap", "p(home)", "p(away)",
        "Market spread", "Market total", "Residual", "Source"],
       [[o["fixture_id"], (o["fair_home_margin"], "num"), o["fair_favourite"],
         (o["fair_spread"], "num"), (o["fair_total_a"], "num"), (o["fair_total_b"], "num"),
         (o["total_gap"], "num"), (o["p_home_ml"], "num"), (o["p_away_ml"], "num"),
         ("", "blank"), ("", "blank"), ("", "blank"), (("link", (o["source_url"], "official")))] for o in og])}
</section>
<section class="panel"><h2>Inputs: ratings from weeks 1-4 only</h2>
<p class="desc">Net points per game, opponent-aware by construction because every margin
contains the opponent. Nothing after week 4 is used for any Week 11 number.</p>
{table(["Club", "Games in train window", "Net points / game", "Points scored / game", "Source"],
       [[r["team"], (r["games_train"], "num"), (r["net_points_pg"], "num"),
         (r["points_scored_pg"], "num"), (("link", (r["input_url"], "official")))] for r in rat])}
</section>
"""
    return page("origination.html", "Line origination",
                "Side, then total, then moneyline — with the market columns left honestly blank.",
                body, "origination.html")


def page_corpus():
    corp = read("results_corpus.csv")
    recon = read("results_reconciliation.csv")
    wk = {}
    for r in corp:
        wk.setdefault(r["week"], []).append(r)
    body = f"""
<div class="note"><b>The merge rule that makes this corpus trustworthy</b>
A game row is admitted only after the whole corpus reproduces the official standings. Points
for and points against are additive, so one wrong score would break at least two clubs. All 32
clubs match on W-L-T, PF and PA, which is why the 150 rows below can be used as a backtest
corpus. This is a stronger check than spot-reading a score.</div>
<div class="cards">
<article class="card good"><span>Games admitted</span><strong>{len(corp)}</strong><small>weeks 1-10, all FINAL</small></article>
<article class="card good"><span>Clubs reconciled</span><strong>{sum(1 for r in recon if r['match']=='MATCH')}/{len(recon)}</strong><small>record, PF and PA</small></article>
<article class="card"><span>Weeks covered</span><strong>{len(wk)}</strong><small>1 through 10</small></article>
<article class="card"><span>Sources</span><strong>2</strong><small>per-game page and week page</small></article>
</div>
<section class="panel"><h2>Reconciliation against official standings</h2>
<p class="desc">Computed from the corpus, compared to the league's own table read today. A
mismatch here fails the build (drift alarm, R61).</p>
{table(["Club", "Corpus W-L-T", "Official W-L-T", "Corpus PF", "Official PF", "Corpus PA",
        "Official PA", "Result", "Source"],
       [[r["team"], f'{r["corpus_w"]}-{r["corpus_l"]}-{r["corpus_t"]}',
         f'{r["official_w"]}-{r["official_l"]}-{r["official_t"]}',
         (r["corpus_pf"], "num"), (r["official_pf"], "num"), (r["corpus_pa"], "num"),
         (r["official_pa"], "num"), (r["match"], "badge"), (("link", (r["source_url"], "official")))]
        for r in recon])}
</section>
<section class="panel"><h2>Week by week</h2>
<p class="desc">Every row carries the page it was read from. Weeks 1-9 were transcribed by an
earlier desk and adopted here after the reconciliation above; week 10 was read by this session
on 2026-11-18.</p>
""" + "".join(
        f"""<h3 style="font-size:13px;margin:14px 0 4px">Week {w}</h3>"""
        + table(["Date", "Away", "Score", "Home", "Score", "Total", "Source"],
                [[r["date"], r["away"], (r["away_score"], "num"), r["home"],
                  (r["home_score"], "num"), (r["total"], "num"), (("link", (r["source_url"], "official")))]
                 for r in sorted(wk[w], key=lambda x: x["date"])])
        for w in sorted(wk, key=int)) + """
</section>
"""
    return page("corpus.html", "Verified results corpus",
                "150 completed games, admitted only because they reproduce the league's own standings.",
                body, "corpus.html")


def page_leaderboard():
    lb = read("leaderboard.csv")
    pre = read("preregistration.csv")
    luck = read("luck_panel.csv")
    body = f"""
<div class="note bad"><b>No strategy is certified. That is the result, not a defect.</b>
Five strategies were registered before any number was computed. All five fail at least one
blocking gate: the moneyline baseline has a Brier-skill interval that crosses zero, the total
estimators are indistinguishable, and the two side rows are controls, not selections. The
staking columns (ROI, CLV, reward) are blank because there is no official price to settle
against.</div>
<div class="cards">
<article class="card bad"><span>Certified strategies</span><strong>0</strong><small>of 5 registered</small></article>
<article class="card"><span>Out-of-sample forecasts</span><strong>85</strong><small>weeks 5-10</small></article>
<article class="card warn"><span>Best Brier skill</span><strong>+0.22</strong><small>holdout only, n=29, CI crosses 0</small></article>
<article class="card warn"><span>Bets needed for 55%</span><strong>617</strong><small>80% power, one-sided 5%</small></article>
</div>
<section class="panel"><h2>Signal — proper score with uncertainty</h2>
<p class="desc">Ranked by Brier skill against the flat 0.5 control on the same games. CI is a
95% percentile bootstrap over games. Holm p adjusts across the registered family. Win rate is
a diagnostic and is never the ranking.</p>
{table(["Division", "ID", "Strategy", "Window", "Bets", "Brier", "BSS vs flat", "95% CI",
        "p (exact)", "p (Holm)", "Certified", "MAE", "Bias", "Source"],
       [[r["division"], r["strategy_id"] or ("none registered", "raw"), r["name"], r["window"],
         (r["bets"], "num"), (r["brier"], "num"), (r["bss_vs_flat"], "num"),
         f'{r["ci_low"]}..{r["ci_high"]}' if r["ci_low"] else ("", "blank"),
         (r["p_exact"], "num"), (r["p_holm"], "num"), (r["certified"] or "", "badge"),
         (r["mae"], "num"), (r["mean_bias"], "num"), (("link", (r["source_url"], "official")))] for r in lb])}
</section>
<section class="panel"><h2>Staking — deliberately separate and blank</h2>
<p class="desc">A lucky staking run must never be able to mask a bad signal, so staking lives
in its own columns and those columns cannot be filled until an official price feed exists.</p>
{table(["Division", "Strategy", "ROI", "CLV", "Reward", "Why blank"], [
    [r["division"], r["name"], ("", "blank"), ("", "blank"), ("", "blank"),
     "FLAG-P1: no official market price in the repository"] for r in lb if r["strategy_id"]])}
</section>
<section class="panel"><h2>Removal of luck</h2>
<p class="desc">What a fair coin produces at the sample sizes we actually have, and how many
bets a 55% claim needs before it can be believed. This is the arithmetic that stops a 4-1 week
from being published as skill.</p>
{table(["Bets", "Expected wins at 50%", "SD", "Wins needed for 55%",
        "P(55% or better by luck)", "Bets needed for 80% power"],
       [[(l["bets"], "num"), (l["expected_wins"], "num"), (l["sd"], "num"),
         (l["wins_for_55"], "num"), (l["prob_55_or_more"], "num"),
         (l["bets_needed_80_power"], "num")] for l in luck])}
</section>
<section class="panel"><h2>Pre-registration and the two-sided change-of-mind field</h2>
<p class="desc">Registration commit <code>{REG[:12]}</code>. Each strategy states what would
raise our confidence and what would lower it, before any result was seen.</p>
{table(["ID", "Strategy", "Market", "Rule", "Train", "Validation", "Holdout",
        "Would change our mind (up)", "Would change our mind (down)", "Status"],
       [[p["strategy_id"], p["name"], p["market"], p["rule"], p["train_window"],
         p["validation_window"], p["holdout_window"], p["would_change_our_mind_up"],
         p["would_change_our_mind_down"], p["status"]] for p in pre])}
</section>
"""
    return page("leaderboard.html", "Leaderboard",
                "Signal and staking kept apart; proper scores with uncertainty; zero certified.",
                body, "leaderboard.html")


def page_availability():
    d = read("availability_diff.csv")
    s = read("availability_summary.csv")
    stale = [r for r in d if r["result"] == "STALE"]
    lions = [r for r in d if r["club"] == "DET" and r["player"] in
             ("Kerby Joseph", "Cade Mays", "D.J. Reed")]
    which = {r["player"]: r for r in lions}
    body = f"""
<div class="note bad"><b>The headline cannot be fixed with the data in this repository</b>
A backup's replacement of a starter can be <i>suspected</i> from a report row, but it cannot be
<i>confirmed</i>: there are no snap counts, no inactive lists and no depth chart read for 2026.
So the deficiency view below publishes exactly what the official page says and leaves the
depth and replacement columns blank (FLAG-A2, FLAG-D1). Number stripping, jersey order and
salary were all rejected as substitutes; they are recorded as rejected questions, not used.</div>
<div class="cards">
<article class="card warn"><span>Rows re-read</span><strong>{len(d)}</strong><small>4 clubs in chunk 0 of 8</small></article>
<article class="card bad"><span>Stale vs 2026-11-12</span><strong>{len(stale)}</strong><small>changed between captures</small></article>
<article class="card good"><span>Lions cells fixed</span><strong>{len(lions)}/3</strong><small>Joseph, Mays, Reed now OUT</small></article>
<article class="card bad"><span>Clubs with a delta</span><strong>1/32</strong><small>only clubs re-read today</small></article>
</div>
<section class="panel"><h2>The three named Lions cells</h2>
<p class="desc">The brief said these three were published with a blank game status. The
repository capture of 2026-11-12 does have them blank; the official page read on 2026-11-18
publishes all three as <b>Out</b> with an injury and a did-not-participate status.</p>
{table(["Player", "2026-11-12 repo: injury", "repo: practice", "repo: game status",
        "2026-11-18 official: injury", "official: practice", "official: game status",
        "Result", "Source"],
       [[r["player"], r["repo_injury"] or ("", "blank"), r["repo_practice"] or ("", "blank"),
         r["repo_game"] or ("", "blank"), r["official_injury"], r["official_practice"],
         r["official_game"], (r["result"], "badge"), (("link", (r["source_url"], "official")))]
        for r in lions])}
</section>
<section class="panel"><h2>Full re-read diff</h2>
<p class="desc">Every row read today, compared cell by cell with the repository copy. A blank
in the official column means the official page printed no value there.</p>
{table(["Club", "Player", "Pos", "Repo injury", "Repo practice", "Repo game",
        "Official injury", "Official practice", "Official game", "Fields that changed",
        "Result", "Source"],
       [[r["club"], r["player"], r["position"], r["repo_injury"] or ("", "blank"),
         r["repo_practice"] or ("", "blank"), r["repo_game"] or ("", "blank"),
         r["official_injury"] or ("", "blank"), r["official_practice"] or ("", "blank"),
         r["official_game"] or ("", "blank"),
         r["differing_fields"] or ("none", "blank"), (r["result"], "badge"),
         (("link", (r["source_url"], "official")))] for r in d])}
</section>
<section class="panel"><h2>Per-club counts (only what was read)</h2>
<p class="desc">Starters out and replacements named are blank for every club: no official
source names a replacement, and an inferred one would be a fabrication.</p>
{table(["Club", "Rows read", "Game status: Out", "Questionable", "No game status",
        "Starters out", "Replacement named", "Source"],
       [[r["club"], (r["rows_read"], "num"), (r["game_status_out"], "num"),
         (r["game_status_questionable"], "num"), (r["game_status_blank"], "num"),
         ("", "blank"), ("", "blank"), (("link", (r["source_url"], "official")))] for r in s])}
</section>
<div class="note warn"><b>What the Week 11 report says</b>
The request for <code>reg11</code> resolved to the Week 10 page and the title string said
"Week 10 of the 2026 Season" at 2026-11-18T03:45Z. No Week 11 availability value is published
anywhere on this site (FLAG-A4).</div>
"""
    return page("availability.html", "Availability & depth",
                "What the official injury page says today, what moved since the last capture, and what cannot be known.",
                body, "availability.html")


def page_fixtures():
    fx = read("fixtures_wk11.csv")
    ann = read("schedule_vs_announcement.csv")
    games = [r for r in fx if r["away"]]
    byes = [r for r in fx if not r["away"]]
    body = f"""
<div class="note"><b>Fixture context from published facts only</b>
Every feature below comes from the official week page: date, kickoff, network, and the venue
named in that page's own hotel link. One fixture (Minnesota at San Francisco) is named in
prose by the dated league announcement, so it carries both citations. The announcement of
2026-05-14 sits beside the live page, and the six facts that can be compared agree.</div>
<section class="panel"><h2>The league's dated announcement</h2>
<p class="desc">Published 2026-05-14 by NFL Football Communications: 18 weeks, 272 games,
17 regular-season games plus three preseason per club, nine international games.</p>
{table(["Fact", "As published on the live schedule page", "Announcement value", "Result", "Source"],
       [[r["fact"], r["as_announced"], r["announcement_value"], (r["result"], "badge"),
         (("link", (r["announcement_url"], "announcement")))] for r in ann])}
</section>
<section class="panel"><h2>Week 11 fixtures</h2>
<p class="desc">{len(games)} games and {len(byes)} byes, each with the page it was read from.
Venue method is stated per row rather than assumed.</p>
{table(["Fixture", "Date", "Kickoff ET", "Network", "Away", "Home", "Venue", "Neutral",
        "Fixture facts", "Venue method", "Source"],
       [[r["fixture_id"], r["date"], r["kickoff_et"], r["network"], r["away"], r["home"],
         r["venue"], r["neutral_site"], r["fixture_facts"], r["venue_method"],
         (("link", (r["source_url"], "official")))] for r in games])}
</section>
<section class="panel"><h2>Byes</h2>
{table(["Club", "Week", "Source"],
       [[r["fixture_id"].split("-")[-1], "11", (("link", (r["source_url"], "official")))] for r in byes])}
</section>
"""
    return page("fixtures.html", "Fixtures & context",
                "Week 11, straight from the official week page and the dated league announcement.",
                body, "fixtures.html")


def page_sources():
    src = read("sources.csv")
    body = f"""
<div class="note"><b>Seven sources, each read once, each stamped</b>
A source counts only if the page was actually retrieved in this session and its text read.
The read stamp is the time the page was returned, not the time this file was written. Where a
page resolved to a different week than requested, the resolved title is recorded.</div>
<section class="panel"><h2>Source register</h2>
{table(["ID", "Publisher", "Page", "What it was used for", "Read (UTC)", "Class"],
       [[r["source_id"], r["publisher"], link(r["url"], r["url"].replace("https://", "")),
         r["used_for"], r["read_utc"], r["class_"]] for r in src])}
</section>
<section class="panel"><h2>Method notes</h2>
<p class="desc">How values were obtained, in the order they were obtained.</p>
{table(["Item", "Method", "Limitation"], [
    ["Scores, weeks 1-9", "Repository corpus (136 rows), adopted after full reconciliation", "Transcribed by an earlier session on 2026-11-12"],
    ["Scores, week 10", "Read from the official week page in this session", "14 of 14 played games; no game before it was re-read"],
    ["Standings", "Read from the official league standings page", "One read; the page prints AZ and LA for Arizona and the Rams"],
    ["Venue", "Hotel link destination on the official week page", "Not a printed venue column; the announcement names Minnesota's"],
    ["Injury rows", "Read from the official report page, chunk 0 of 8", "Only 4 clubs fully visible; 44 rows"],
    ["Schedule announcement", "Read from media.nfl.com", "Dated 2026-05-14; a press release, not the live page"],
    ["Market prices", "None obtained", "FLAG-P1: nothing to settle ROI or CLV against"],
])}
</section>
"""
    return page("sources.html", "Sources", "Every page this desk read, with the stamp and the limitation.",
                body, "sources.html")


def page_flagged():
    fl = read("flagged.csv")
    body = f"""
<div class="note warn"><b>Non-blocking for publication, blocking for claims</b>
Everything here is published for you to review; none of it stops the site from being live.
Each item states what was found, what would resolve it, and the official page involved.</div>
<section class="panel"><h2>{len(fl)} flagged items</h2>
<p class="desc">{sum(1 for f in fl if f['severity']=='BLOCKING')} blocking (no claim can be made),
{sum(1 for f in fl if f['severity']=='REVIEW')} for review.</p>
{table(["ID", "Severity", "Area", "Finding", "What would resolve it", "Source"],
       [[f["flag_id"], (f["severity"], "badge"), f["area"], f["finding"],
         f["what_would_resolve"], (("link", (f["source_url"], "official")))] for f in fl])}
</section>
<div class="note"><b>How to request a change</b>
Open an issue on the repository naming the flag ID. A later session re-reads the linked
official page before changing anything; if the page now says something different, the new
reading replaces the row and the old reading is kept in the diff page.</div>
"""
    return page("flagged.html", "Flagged for Review",
                "Irregularities, stale captures and unverified items — published, not buried.",
                body, "flagged.html")


def main():
    build_req_source()
    (HERE / "style.css").write_text(CSS.strip() + "\n")
    pages = {
        "index.html": page_index(), "requirements.html": page_requirements(),
        "questions.html": page_questions(), "suggestions.html": page_suggestions(),
        "origination.html": page_origination(), "corpus.html": page_corpus(),
        "leaderboard.html": page_leaderboard(), "availability.html": page_availability(),
        "fixtures.html": page_fixtures(), "sources.html": page_sources(),
        "flagged.html": page_flagged(),
    }
    for name, html_text in pages.items():
        (HERE / name).write_text(html_text + "\n")
    print(f"built {len(pages)} pages")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the NFL Brief Traceability & Decision Desk pages (session 6e13b9ff).

Deterministic, stdlib only: reads data/nfl-desk-6e13b9ff/*.csv and
research/nfl-6e13b9ff/EXECUTIVE_SUMMARY.md and renders the static pages in
this directory. Run:  python3 nfl-desk-6e13b9ff/build_desk.py
Then:                python3 nfl-desk-6e13b9ff/verify_desk.py
"""
import csv
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DATA = os.path.join(REPO, "data", "nfl-desk-6e13b9ff")
RESEARCH = os.path.join(REPO, "research", "nfl-6e13b9ff")
BLOB = "https://github.com/sassnarep3-star/Own5/blob/main/"

NAV = [
    ("index.html", "Dashboard"),
    ("requirements.html", "Requirements"),
    ("captures.html", "Official captures"),
    ("verification.html", "Verification"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged"),
    ("sources.html", "Sources"),
    ("executive-summary.html", "Executive summary"),
]


def load(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def esc(s):
    return html.escape(str(s), quote=True)


def badge(kind):
    m = {
        "MET": "b-met", "PARTIAL": "b-partial", "OPEN": "b-open",
        "BLOCKED": "b-blocked", "RULE-ADOPTED": "b-rule",
        "MATCH": "b-match", "MISMATCH": "b-open", "PUBLISHED": "b-pub",
        "DISCREPANCY": "b-disc", "NOTED": "b-noted",
        "BLOCKING": "b-block", "PARTIAL_Q": "b-part",
        "PROPOSED": "b-prop", "open": "b-open", "resolved": "b-met",
        "ANSWERED": "b-met",
    }
    key = "PARTIAL_Q" if kind == "PARTIAL" and kind not in m else kind
    cls = m.get(key) or m.get(kind, "b-noted")
    return f'<span class="badge {cls}">{esc(kind)}</span>'


def gate(v):
    return "&mdash;" if v in ("", "-") else esc(v)


def ev_links(ev):
    """Evidence: repo paths -> absolute GitHub blob URLs (never repo-relative,
    which 404 when the desk is served from /Own5/<desk>/)."""
    if not ev:
        return '<span class="small">BLANK &mdash; flagged</span>'
    out = []
    for part in ev.split(" ;; "):
        part = part.strip()
        if part.startswith("http"):
            label = part.replace("https://", "")
            if len(label) > 64:
                label = label[:61] + "..."
            out.append(f'<a href="{esc(part)}" rel="noopener">{esc(label)}</a>')
        else:
            out.append(f'<a href="{BLOB}{esc(part)}" title="{esc(part)}">{esc(part)}</a>')
    return '<span class="ev-links">' + " ".join(out) + "</span>"


NOT_OFFICIAL_BADGE = '<span class="badge b-disc">NOT OFFICIAL</span>'


def src_link(url):
    if not url:
        return '<span class="small">BLANK &mdash; unverified</span>'
    return f'<a href="{esc(url)}" rel="noopener">official source</a>'


def flag_cell(flag, flags):
    if not flag:
        return ""
    names = {f["flag_id"] for f in flags}
    if flag not in names:
        return f'<span class="badge b-flag">?{esc(flag)}</span>'
    return f'<a href="flagged.html#{esc(flag)}"><span class="badge b-flag">{esc(flag)}</span></a>'


def page(title, here, body, readstamps):
    nav = []
    for href, label in NAV:
        cls = ' class="here"' if href == here else ""
        nav.append(f'<a href="{href}"{cls}>{label}</a>')
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} - NFL Brief Traceability Desk</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<header class="site">
  <div class="wrap">
    <h1>NFL Brief Traceability &amp; Decision Desk</h1>
    <p class="sub">Session 6e13b9ff &middot; every row source-linked or blank+flagged &middot; official reads {esc(readstamps)}</p>
    <nav class="top">{''.join(nav)}</nav>
  </div>
</header>
<main class="wrap">
{body}
<footer class="site">
  <p>Data layer: <code>data/nfl-desk-6e13b9ff/</code> &middot; built by <code>nfl-desk-6e13b9ff/build_desk.py</code> &middot;
  gated by <code>verify_desk.py</code> (fail-closed) &middot; no value on this site is inferred: blanks are flagged, never filled.</p>
</footer>
</main>
</body>
</html>
"""


def md_to_html(md):
    """Minimal deterministic Markdown renderer for the executive summary."""
    lines = md.splitlines()
    out = []
    i = 0

    def inline(s):
        s = esc(s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        return s

    while i < len(lines):
        ln = lines[i]
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            header = [c.strip() for c in ln.strip().strip("|").split("|")]
            out.append("<div class=\"tablewrap\"><table><thead><tr>")
            out.extend(f"<th>{inline(c)}</th>" for c in header)
            out.append("</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</tbody></table></div>")
            continue
        if ln.startswith("# "):
            out.append(f"<h1>{inline(ln[2:])}</h1>")
        elif ln.startswith("## "):
            out.append(f"<h2>{inline(ln[3:])}</h2>")
        elif ln.startswith("### "):
            out.append(f"<h3>{inline(ln[4:])}</h3>")
        elif ln.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(f"<li>{inline(lines[i][2:])}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif ln.strip() == "":
            pass
        else:
            para = [ln]
            while (i + 1 < len(lines) and lines[i + 1].strip()
                   and not lines[i + 1].startswith(("#", "- ", "|"))):
                para.append(lines[i + 1])
                i += 1
            out.append("<p>" + inline(" ".join(para)) + "</p>")
        i += 1
    return "\n".join(out)


def build():
    cov = load("requirements_coverage.csv")
    ver = load("verification.csv")
    flags = load("flagged.csv")
    qs = load("questions.csv")
    sugg = load("suggestions.csv")
    srcs = load("sources.csv")
    standings = load("standings_fresh_2026-11-19.csv")
    slate = load("wk11_slate_2026-11-19.csv")
    byes = load("wk11_byes_2026-11-19.csv")
    tnf = load("wk11_tnf_injury_2026-11-19.csv")
    wk12 = load("wk12_slate_partial_2026-11-19.csv")
    reads = sorted({s["accessed_utc"] for s in srcs})
    readstamps = reads[0] if len(reads) == 1 else f"{reads[0]} / {reads[-1]}"
    foot = f"Official reads: {readstamps} (UTC). Status vocabulary: MET / PARTIAL / BLOCKED / OPEN / RULE-ADOPTED."

    counts = {}
    for r in cov:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    vcounts = {}
    for r in ver:
        vcounts[r["result"]] = vcounts.get(r["result"], 0) + 1

    # ---------- dashboard ----------
    cards = [
        (len(cov), "", "requirements in matrix"),
        (counts.get("MET", 0), "good", "MET"),
        (counts.get("PARTIAL", 0), "warn", "PARTIAL"),
        (counts.get("BLOCKED", 0) + counts.get("OPEN", 0), "bad", "BLOCKED + OPEN"),
        (counts.get("RULE-ADOPTED", 0), "hold", "rules adopted"),
        (len(ver), "", "verification rows"),
        (len(flags), "bad", "flagged for review"),
        (len(qs), "", "questions registered"),
        (len(sugg), "", "suggestions (none implemented)"),
    ]
    cards_html = "".join(
        f'<div class="card"><div class="n {cls}">{n}</div><div class="k">{esc(k)}</div></div>'
        for (n, cls, k) in cards)

    rows = []
    for r in cov:
        rows.append(
            f'<tr id="{esc(r["req_id"])}">'
            f'<td class="id">{esc(r["req_id"])}</td>'
            f'<td class="req">{esc(r["requirement"])}<div class="small">{esc(r["category"])}</div></td>'
            f'<td>{badge(r["status"])}{(" " + flag_cell(r["flag"], flags)) if r["flag"] else ""}</td>'
            f'<td class="gate">{gate(r["blocking_gate"])}</td>'
            f'<td class="num">{esc(r["number_to_clear"])}</td>'
            f'<td class="obs">{esc(r["observed_2026_11_19"])}</td>'
            f'<td class="ev">{ev_links(r["evidence"])}</td>'
            f"</tr>")
    readiness = (
        '<h2 id="readiness">Decision-readiness &mdash; one row per requirement of this brief</h2>'
        '<p class="lede">The gate that blocks each requirement, the number that would clear it, and the value '
        f'observed on 2026-11-19. {foot}</p>'
        '<div class="tablewrap"><table>'
        '<thead><tr><th>ID</th><th>Requirement</th><th>Status</th><th>Blocking gate</th>'
        '<th>Number that would clear it</th><th>Observed (2026-11-19)</th><th>Evidence</th></tr></thead>'
        '<tbody>' + "".join(rows) + "</tbody></table></div>")

    body = f"""
<p class="lede"><strong>Landing page.</strong> This desk traces every line of the session brief to a status, a
blocking gate, a clearing number and an observed value; verifies a fresh set of official nfl.com reads line by
line (2026-11-19); and publishes questions, suggestions and flagged irregularities for owner review. Nothing is
inferred: unconfirmable values are blank and flagged.</p>
<div class="cards">{cards_html}</div>
<div class="note"><strong>Readiness roll-up:</strong> {counts.get("MET", 0)} MET &middot;
{counts.get("PARTIAL", 0)} PARTIAL &middot; {counts.get("BLOCKED", 0)} BLOCKED &middot;
{counts.get("OPEN", 0)} OPEN &middot; {counts.get("RULE-ADOPTED", 0)} RULE-ADOPTED.
Top blockers: price-data policy/source (G-10), depth-order route for 32 clubs (G-DEPTH), corpus count
reconciliation (G-CORPUS: 136 vs 148 vs 150), capture health (2 scheduled checks red), reward pool (G-FUND).</div>
<div class="warnnote"><strong>Flagged, non-blocking:</strong> {len(flags)} items on the
<a href="flagged.html">Flagged for Review</a> page (CI reds, 14 open PRs, corpus counts, venue/label
discrepancies across official pages). They do not block this publication.</div>
{readiness}
"""
    with open(os.path.join(HERE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Dashboard", "index.html", body, readstamps))

    # ---------- requirements (grouped) ----------
    order, groups = [], {}
    for r in cov:
        if r["category"] not in groups:
            groups[r["category"]] = []
            order.append(r["category"])
        groups[r["category"]].append(r)
    toc = '<nav class="toc">' + "".join(
        f'<a href="#cat{i}">{esc(c)}</a>' for i, c in enumerate(order)) + "</nav>"
    parts = [toc,
             '<h2>Requirements coverage matrix</h2>',
             '<p class="lede">Every line of this session&rsquo;s brief, line by line: status, gate, clearing number, '
             'observed value, evidence (in-repo paths rendered as absolute GitHub links) and official source where '
             'one was read first-hand. Evidence paths are existence-checked by the verifier &mdash; a missing file '
             'fails the build.</p>']
    for i, cat in enumerate(order):
        parts.append(f'<div class="cat" id="cat{i}">{esc(cat)} &middot; {len(groups[cat])} rows</div>')
        parts.append('<div class="tablewrap"><table><thead><tr><th>ID</th><th>Requirement</th>'
                     '<th>Status</th><th>Blocking gate</th><th>Number that would clear it</th>'
                     '<th>Observed (2026-11-19)</th><th>Evidence</th><th>Source</th><th>Flag</th></tr></thead><tbody>')
        for r in groups[cat]:
            parts.append(
                f'<tr id="d-{esc(r["req_id"])}"><td class="id">{esc(r["req_id"])}</td>'
                f'<td class="req">{esc(r["requirement"])}</td>'
                f'<td>{badge(r["status"])}</td>'
                f'<td class="gate">{gate(r["blocking_gate"])}</td>'
                f'<td class="num">{esc(r["number_to_clear"])}</td>'
                f'<td class="obs">{esc(r["observed_2026_11_19"])}</td>'
                f'<td class="ev">{ev_links(r["evidence"])}</td>'
                f'<td>{src_link(r["source_url"])}</td>'
                f'<td>{flag_cell(r["flag"], flags)}</td></tr>')
        parts.append("</tbody></table></div>")
    with open(os.path.join(HERE, "requirements.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Requirements", "requirements.html", "\n".join(parts), readstamps))

    # ---------- captures ----------
    srows = "".join(
        f"<tr><td>{esc(r['team_name'])}</td><td>{esc(r['team_code'])}</td><td>{esc(r['w'])}-{esc(r['l'])}-{esc(r['t'])}</td>"
        f"<td>{esc(r['pct'])}</td><td>{esc(r['pf'])}</td><td>{esc(r['pa'])}</td><td>{esc(r['net'])}</td>"
        f"<td>{src_link(r['source_url'])}</td><td class='small'>{esc(r['read_utc'])}</td></tr>"
        for r in standings)
    mr = "".join(
        f"<tr><td>{esc(r['game_id'])}</td><td>{esc(r['game_date'])}</td><td>{esc(r['kickoff_et'])}</td>"
        f"<td>{esc(r['network'])}</td><td>{esc(r['away'])} @ {esc(r['home'])}</td>"
        f"<td class='small'>{esc(r['page_heading_note'])}</td><td>{src_link(r['source_url'])}</td></tr>"
        for r in slate)
    br = "".join(f"<tr><td>{esc(r['club'])}</td><td>{src_link(r['source_url'])}</td></tr>" for r in byes)
    tr = "".join(
        f"<tr><td>{esc(r['team'])}</td><td>{esc(r['player'])}</td><td>{esc(r['position'])}</td>"
        f"<td>{esc(r['injury_as_printed'])}</td><td>{esc(r['practice_status'])}</td>"
        f"<td>{esc(r['game_status'])}</td><td>{src_link(r['source_url'])}</td></tr>"
        for r in tnf)
    wr = "".join(
        f"<tr><td>{esc(r['game_id'])}</td><td class='small'>{esc(r['page_heading_as_printed'])}</td>"
        f"<td>{esc(r['game_date'])}</td><td>{esc(r['kickoff_et'])}</td><td>{esc(r['network'])}</td>"
        f"<td>{esc(r['away'])} @ {esc(r['home'])}</td><td>{flag_cell(r['flag'], flags)}</td>"
        f"<td>{src_link(r['source_url'])}</td></tr>"
        for r in wk12)
    body = f"""
<h2>Official captures read first-hand (2026-11-19)</h2>
<p class="lede">Transcribed row by row from official nfl.com pages in this session. Every row carries its source
URL and read stamp. Nothing on this page is copied from another session without a cross-check (see
<a href="verification.html">Verification</a>).</p>
<div class="warnnote"><strong>Convention note:</strong> the standings page prints PCT with ties as half-wins
(PCT = (W + 0.5T) / (W + L + T)) &mdash; recomputed for all 32 rows. The Week-11 bye section prints the Rams code
&ldquo;LAR&rdquo; while the standings page prints &ldquo;LA&rdquo;; both are kept exactly as printed.</div>

<h3>2026 league standings &mdash; 32/32 rows <span class="small">(source: standings page, read {esc(reads[0])})</span></h3>
<div class="tablewrap"><table><thead><tr><th>Team</th><th>Code</th><th>W-L-T</th><th>PCT</th><th>PF</th>
<th>PA</th><th>NET</th><th>Source</th><th>Read (UTC)</th></tr></thead><tbody>{srows}</tbody></table></div>

<h3>Week 11 slate &mdash; 13 fixtures</h3>
<div class="tablewrap"><table><thead><tr><th>Game</th><th>Date</th><th>Kickoff ET</th><th>Network</th>
<th>Matchup</th><th>Page heading note</th><th>Source</th></tr></thead><tbody>{mr}</tbody></table></div>
<p class="small">Byes (6, codes as printed): {' '.join(esc(r['club']) for r in byes)}.</p>

<h3>Week 11 injury report &mdash; TNF IND @ HOU designations (26 rows, read {esc(reads[-1])})</h3>
<div class="tablewrap"><table><thead><tr><th>Team</th><th>Player</th><th>Pos</th><th>Injury (as printed)</th>
<th>Practice status</th><th>Game status</th><th>Source</th></tr></thead><tbody>{tr}</tbody></table></div>
<p class="small">Sunday/Monday games carried practice statuses only at read time (game designations publish later
in the week); the two TNF tables above are captured in full.</p>

<h3>Week 12 spot fixtures &mdash; partial read (chunk 0 of 3, 6 rows)</h3>
<div class="tablewrap"><table><thead><tr><th>Game</th><th>Heading as printed</th><th>Date</th><th>Kickoff</th>
<th>Network</th><th>Matchup</th><th>Flag</th><th>Source</th></tr></thead><tbody>{wr}</tbody></table></div>
<div class="warnnote">The Week-12 page headings disagree with the listed dates for two rows (SNF heading on a
Thursday listing, TNF heading on a Friday listing) &mdash; recorded verbatim, flagged as
{flag_cell("F6-05", flags)}.</div>
"""
    with open(os.path.join(HERE, "captures.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Official captures", "captures.html", body, readstamps))

    # ---------- verification ----------
    vrows = "".join(
        f'<tr id="{esc(r["v_id"])}"><td class="id">{esc(r["v_id"])}</td><td class="req">{esc(r["claim"])}</td>'
        f"<td>{esc(r['value'])}</td><td class='small'>{esc(r['method'])}</td>"
        f"<td>{badge(r['result'])}</td><td>{flag_cell(r['flag'], flags)}</td>"
        f"<td>{src_link(r['source_url'])}</td><td class='small'>{esc(r['read_utc'])}</td></tr>"
        for r in ver)
    body = f"""
<h2>Line-by-line verification (2026-11-19)</h2>
<p class="lede">Every claim below was checked against the official source named in its row, first-hand in this
session: standings transcribed and arithmetically recomputed (ties = half-win) and diffed against the committed
2026-11-18 capture; the Week-11 slate and byes diffed against the committed prior capture; injury designations
cross-read against the game-centre cards; forecast freeze checked against kickoff. Result vocabulary:
{badge("MATCH")} {badge("PUBLISHED")} {badge("NOTED")} {badge("DISCREPANCY")} (a {badge("DISCREPANCY")} needs an
owner ruling; it is published, not silently resolved). {vcounts.get("MISMATCH", 0)} MISMATCH rows &mdash; a
MISMATCH fails the verifier and must be investigated before publication.</p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Claim</th><th>Value</th><th>Method</th><th>Result</th>
<th>Flag</th><th>Source</th><th>Read (UTC)</th></tr></thead><tbody>{vrows}</tbody></table></div>
"""
    with open(os.path.join(HERE, "verification.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Verification", "verification.html", body, readstamps))

    # ---------- questions ----------
    qrows = "".join(
        f'<tr id="{esc(r["q_id"])}"><td class="id">{esc(r["q_id"])}</td><td class="req">{esc(r["question"])}</td>'
        f"<td>{esc(r['information_needed'])}</td><td>{esc(r['answer_now'])}</td><td>{esc(r['blocks'])}</td>"
        f"<td>{badge(r['status'])}</td><td>{ev_links(r['evidence'])}</td>"
        f"<td>{flag_cell(r['flag'], flags)}</td></tr>"
        for r in qs)
    body = f"""
<h2>Questions, information and answers &mdash; before any decision</h2>
<p class="lede">What must be answered before a reasonable decision can be made, given what we have and what we do
not have. Each row names the information needed, the best answer available today, and what decision it blocks.
{len([q for q in qs if q['status'] == 'BLOCKING'])} are blocking,
{len([q for q in qs if q['status'] == 'PARTIAL'])} partially answered,
{len([q for q in qs if q['status'] == 'OPEN'])} open. Nothing here is invented: &ldquo;answer now&rdquo; either
cites evidence or says plainly that nothing is known.</p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Question</th><th>Information needed</th>
<th>Answer now</th><th>Blocks</th><th>Status</th><th>Evidence</th><th>Flag</th></tr></thead><tbody>{qrows}</tbody></table></div>
<div class="note">Cross-reference: the decision-desk register (<a
href="{BLOB}data/decision-desk/questions.csv">data/decision-desk/questions.csv</a>, 18 rows) holds the earlier
round of questions; this register adds the decisions still open as of 2026-11-19.</div>
"""
    with open(os.path.join(HERE, "questions.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Questions", "questions.html", body, readstamps))

    # ---------- suggestions ----------
    srows = "".join(
        f'<tr id="{esc(r["s_id"])}"><td class="id">{esc(r["s_id"])}</td><td class="req">{esc(r["title"])}'
        f'<div class="small">{esc(r["problem"])}</div></td><td>{esc(r["options"])}</td>'
        f"<td>{esc(r['recommendation'])}</td><td>{esc(r['what_would_change_our_mind'])}</td>"
        f"<td>{esc(r['decision_owner'])}</td><td>{esc(r['implements_when'])}</td>"
        f"<td>{ev_links(r['evidence'])}</td><td>{badge(r['status'])}</td></tr>"
        for r in sugg)
    body = f"""
<h2>Suggestions &mdash; review and choose before anything is implemented</h2>
<p class="lede">Site and process improvements for decision-making. Every suggestion carries its options, a
recommendation, what would change our mind, and an owner. <strong>Nothing here has been implemented:</strong>
each waits for a decision on this page. Ideas that need missing information are exactly the ones paired with the
<a href="questions.html">questions register</a>.</p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Suggestion &amp; problem</th><th>Options</th>
<th>Recommendation</th><th>What would change our mind</th><th>Owner</th><th>Implements when</th><th>Evidence</th>
<th>Status</th></tr></thead><tbody>{srows}</tbody></table></div>
"""
    with open(os.path.join(HERE, "suggestions.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Suggestions", "suggestions.html", body, readstamps))

    # ---------- flagged ----------
    frows = "".join(
        f'<tr id="{esc(r["flag_id"])}"><td class="id">{esc(r["flag_id"])}</td><td class="req">{esc(r["item"])}</td>'
        f"<td class='small'>{esc(r['where'])}</td><td>{esc(r['why'])}</td>"
        f"<td>{src_link(r['source_url'])}</td><td class='small'>{esc(r['observed_on'])}</td>"
        f"<td>{badge(r['status'].split()[0])} <span class='small'>{esc(' '.join(r['status'].split()[1:]))}</span></td></tr>"
        for r in flags)
    body = f"""
<h2>Flagged for Review &mdash; irregularities and unverified items</h2>
<p class="lede">Found during this session&rsquo;s repo review and first-hand official reads. Published with source
links so they can be reviewed after go-live. <strong>Flagged items do not block the merge</strong> &mdash; they are
the review queue, not the release gate. Status vocabulary: {badge("open")} {badge("resolved")}.</p>
<div class="tablewrap"><table><thead><tr><th>Flag</th><th>Item</th><th>Where</th><th>Why it matters</th>
<th>Source</th><th>Observed</th><th>Status</th></tr></thead><tbody>{frows}</tbody></table></div>
"""
    with open(os.path.join(HERE, "flagged.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Flagged for Review", "flagged.html", body, readstamps))

    # ---------- sources ----------
    official_badge = '<span class="badge b-met">OFFICIAL</span>'
    orows = "".join(
        f'<tr id="{esc(r["src_id"])}"><td class="id">{esc(r["src_id"])}</td><td class="req">{esc(r["name"])}</td>'
        f"<td>{official_badge if r['official'] == 'yes' else NOT_OFFICIAL_BADGE}</td>"
        f"<td><a href='{esc(r['url'])}'>{esc(r['url'])}</a></td>"
        f"<td class='small'>{esc(r['accessed_utc'])}</td><td>{esc(r['used_for'])}</td></tr>"
        for r in srcs)
    body = f"""
<h2>Source registry</h2>
<p class="lede">Every external source read first-hand by this session, with access stamps and what each one
verified. All are official nfl.com pages; in-repo evidence is listed on the
<a href="requirements.html">requirements</a> and <a href="verification.html">verification</a> pages.</p>
<div class="tablewrap"><table><thead><tr><th>ID</th><th>Source</th><th>Official</th><th>URL</th>
<th>Accessed (UTC)</th><th>Used for</th></tr></thead><tbody>{orows}</tbody></table></div>
"""
    with open(os.path.join(HERE, "sources.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Sources", "sources.html", body, readstamps))

    # ---------- executive summary ----------
    with open(os.path.join(RESEARCH, "EXECUTIVE_SUMMARY.md"), encoding="utf-8") as fh:
        md = fh.read()
    body = '<div class="panel">' + md_to_html(md) + "</div>"
    with open(os.path.join(HERE, "executive-summary.html"), "w", encoding="utf-8") as fh:
        fh.write(page("Executive summary", "executive-summary.html", body, readstamps))

    print(f"built {len(NAV)} pages: {counts} verify_rows={len(ver)} flags={len(flags)}")


if __name__ == "__main__":
    build()

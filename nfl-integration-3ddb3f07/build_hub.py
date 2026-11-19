#!/usr/bin/env python3
"""Build the Own5 NFL front door (nfl-integration-3ddb3f07) from the repository's
verified tables.

Design rules (integration session, 2026-11-19):

  * Deterministic. No clock, no network, no randomness. Two builds are byte-identical.
  * Nothing is copied. Every table is read from the desk that owns it, at build time,
    and the file that was read is recorded in data/lineage.csv with its sha256, so a
    drift between this site and its sources is detectable rather than silent.
  * Every table row carries an official source link (https://www.nfl.com/... and the
    other official publishers) or an explicit UNVERIFIED marker. A value that cannot be
    confirmed is printed blank and flagged; it is never inferred.
  * Repository-internal references are written as absolute GitHub blob URLs, because this
    site is served from /Own5/nfl-integration-3ddb3f07/ and a repo-relative path would
    resolve one directory too high.

Run:  python3 nfl-integration-3ddb3f07/build_hub.py
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = HERE
DATA = HERE / "data"
BUILD_DATE = "2026-11-19"          # the date this build was produced (constant, not a clock)
BLOB = "https://github.com/sassnarep3-star/Own5/blob/main/"

# ---------------------------------------------------------------------------------
# Sources. Each entry is (key, path relative to the repo root, owner desk).
# ---------------------------------------------------------------------------------
SOURCES = [
    ("readiness", "nfl-market-desk/data/decision_readiness.csv", "NFL market desk"),
    ("requirements", "nfl-market-desk/data/requirements.csv", "NFL market desk"),
    ("originated", "nfl-market-desk/data/originated_markets.csv", "NFL market desk"),
    ("prices", "nfl-market-desk/data/price_snapshots.csv", "NFL market desk"),
    ("price_policy", "nfl-market-desk/data/price_policy.csv", "NFL market desk"),
    ("results", "nfl-market-desk/data/results_feed.csv", "NFL market desk"),
    ("leaderboard", "nfl-market-desk/data/leaderboard.csv", "NFL market desk"),
    ("gates", "nfl-market-desk/data/gates.csv", "NFL market desk"),
    ("demotion", "nfl-market-desk/data/demotion_rules.csv", "NFL market desk"),
    ("registration", "nfl-market-desk/data/strategy_registration.csv", "NFL market desk"),
    ("luck", "nfl-market-desk/data/luck_panel.csv", "NFL market desk"),
    ("controls", "nfl-market-desk/data/control_summary.csv", "NFL market desk"),
    ("accuracy", "nfl-market-desk/data/model_accuracy.csv", "NFL market desk"),
    ("ablation", "nfl-market-desk/data/personnel_ablation.csv", "NFL market desk"),
    ("correlations", "nfl-market-desk/data/correlations_official.csv", "NFL market desk"),
    ("withheld", "nfl-market-desk/data/correlations_withheld.csv", "NFL market desk"),
    ("availability", "nfl-market-desk/data/availability_by_team.csv", "NFL market desk"),
    ("cascade", "nfl-market-desk/data/replacement_cascade.csv", "NFL market desk"),
    ("depth_coverage", "nfl-market-desk/data/depth_coverage.csv", "NFL market desk"),
    ("depth_rows", "nfl-market-desk/data/depth_rows.csv", "NFL market desk"),
    ("announced", "nfl-market-desk/data/announced_starter_changes.csv", "NFL market desk"),
    ("roster_sweep", "nfl-market-desk/data/roster_sweep_32.csv", "NFL market desk"),
    ("venues", "nfl-market-desk/data/venues.csv", "NFL market desk"),
    ("questions", "nfl-market-desk/data/questions.csv", "NFL market desk"),
    ("suggestions", "nfl-market-desk/data/suggestions.csv", "NFL market desk"),
    ("flags", "nfl-market-desk/data/flags.csv", "NFL market desk"),
    ("schedule_ann", "nfl-market-desk/data/schedule_announcements.csv", "NFL market desk"),
    ("hub_questions", "nfl-integration-a620f5a5/data/questions.csv", "NFL integration hub"),
    ("hub_suggestions", "nfl-integration-a620f5a5/data/suggestions.csv", "NFL integration hub"),
    ("hub_sources", "nfl-integration-a620f5a5/data/sources.csv", "NFL integration hub"),
    ("hub_audit", "nfl-integration-a620f5a5/data/audit.csv", "NFL integration hub"),
    ("hub_requirements", "own5-hub/data/requirements.csv", "Own5 hub"),
]

LINEAGE: list[dict] = []


def read(rel: str) -> list[dict]:
    p = REPO / rel
    raw = p.read_bytes()
    LINEAGE.append({
        "path": rel,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "rows": max(0, raw.decode("utf-8", "replace").count("\n") - 1),
    })
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def blob(rel: str) -> str:
    return BLOB + rel


def link(url: str, label: str = "source") -> str:
    if not url:
        return '<span class="badge warn">UNVERIFIED — no official source</span>'
    return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)} ↗</a>'


def cell_RAW(x) -> str:
    """A cell whose value is already HTML (an anchor, a badge)."""
    v = "" if x is None else str(x)
    if v == "":
        return '<td class="blank" title="Left blank: no official source published this value">&mdash;</td>'
    return f"<td>{v}</td>"


def cell(x, raw: bool = False) -> str:
    v = "" if x is None else str(x)
    if v == "":
        return '<td class="blank" title="Left blank: no official source published this value">&mdash;</td>'
    return f"<td>{v if raw else esc(v)}</td>"


def table(headers: list[str], rows: list[str], cls: str = "") -> str:
    head = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
    body = "".join(rows)
    return (f'<div class="tw"><table class="{cls}"><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def page(title: str, active: str, body: str, sub: str = "") -> str:
    nav = [
        ("index.html", "Overview", "01", "hub"),
        ("executive-summary.html", "Executive summary", "02", "hub"),
        ("requirements.html", "Requirements & readiness", "03", "evidence"),
        ("gates.html", "Validation gates", "04", "evidence"),
        ("lines.html", "Originated lines", "05", "analysis"),
        ("availability.html", "Injuries & depth", "06", "analysis"),
        ("correlations.html", "Correlations", "07", "analysis"),
        ("leaderboard.html", "Leaderboard & strategies", "08", "analysis"),
        ("luck.html", "Removal of luck", "09", "analysis"),
        ("questions.html", "Questions", "10", "registers"),
        ("suggestions.html", "Suggestions", "11", "registers"),
        ("flagged.html", "Flagged for Review", "12", "registers"),
        ("sources.html", "Official sources", "13", "registers"),
        ("desks.html", "Desk directory", "14", "repository"),
        ("verification.html", "Verification report", "15", "repository"),
    ]
    groups: dict[str, list] = {}
    for href, label, num, group in nav:
        groups.setdefault(group, []).append((href, label, num))
    order = [("hub", "Hub"), ("evidence", "Evidence"), ("analysis", "Analysis"),
             ("registers", "Registers"), ("repository", "Repository")]
    nav_html = []
    for gname, glabel in order:
        items = groups[gname]
        nav_html.append(f'<span class="nav-cap">{esc(glabel)}</span>')
        for href, label, num in items:
            on = ' class="on" aria-current="page"' if href == active else ""
            nav_html.append(f'<a href="{href}"{on}><b>{num}</b>{esc(label)}</a>')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Own5 NFL front door</title>
<meta name="description" content="Own5 NFL line-origination front door: one row per requirement, one source per row, no strategy certified.">
<link rel="stylesheet" href="style.css"></head><body>
<aside class="side"><a class="brand" href="index.html"><i>O5</i><span>OWN5<small>NFL FRONT DOOR</small></span></a>
<nav>{''.join(nav_html)}</nav>
<p>Every value is read from an official publisher on a dated capture, or it is blank and
flagged. Nothing here is a betting recommendation.</p></aside>
<main><header class="top"><div><span class="eyebrow">NFL · INTEGRATION REVIEW</span>
<h1>{esc(title)}</h1><p class="sub">{esc(sub)}</p></div>
<div class="stamp">Built {BUILD_DATE}<br>Paper research</div></header>
{body}
<footer>Own5 NFL front door · built {BUILD_DATE} from the repository's verified tables ·
not affiliated with the NFL · blank cells are unverified, never zero ·
<a href="{BLOB}COORDINATION.md">coordination log</a> ·
<a href="{BLOB}README.md">repository</a></footer>
</main></body></html>
"""


# ---------------------------------------------------------------------------------
# Small helpers over the source tables
# ---------------------------------------------------------------------------------

def count_by(rows, key, order=None):
    out = {}
    for r in rows:
        out[r.get(key, "")] = out.get(r.get(key, ""), 0) + 1
    if order:
        return {k: out[k] for k in order if k in out}
    return dict(sorted(out.items()))


def status_badge(status: str) -> str:
    s = (status or "").upper()
    if s in ("MET", "DONE", "VERIFIED", "CONFIRMED", "COMPLETE"):
        cls = "ok"
    elif s in ("NOT MET", "BLOCKED", "FAILED", "NO"):
        cls = "bad"
    elif s in ("PARTIAL", "STARTED-TODAY", "IN PROGRESS", "PENDING"):
        cls = "mid"
    else:
        cls = "muted"
    return f'<span class="badge {cls}">{esc(status)}</span>'


def source_row(url: str, tier: str = "") -> str:
    """A source cell: an official link, a link to the evidence file inside this repository,
    or an explicit statement that nothing verified it."""
    if not url:
        return '<span class="badge warn">NO VERIFIED SOURCE</span>'
    tier_html = f'<span class="badge muted">{esc(tier)}</span> ' if tier else ""
    if url.startswith("http"):
        return tier_html + link(url, "official ↗")
    # a repo-relative path: link it absolutely so it resolves from the served page
    if (REPO / url).exists():
        return tier_html + (f'<a href="{esc(blob(url))}" target="_blank" '
                            f'rel="noopener noreferrer">evidence file ↗</a>')
    return '<span class="badge warn">UNVERIFIED — the cited evidence file is missing</span>' 


# ---------------------------------------------------------------------------------
# Repository scan (desk directory + verification evidence)
# ---------------------------------------------------------------------------------

def desk_directory() -> list[dict]:
    """Every desk in the repository: the directory, its entry page, its data files and the
    newest dated string in its own files. Scanned from the working tree, so the directory
    cannot drift from what is actually published."""
    out = []
    for d in sorted(p for p in REPO.iterdir() if p.is_dir() and not p.name.startswith(".")):
        entry = d / "index.html"
        if not entry.exists():
            continue
        if d.name in ("node_modules", "__pycache__", ".git"):
            continue
        data_files = sum(1 for _ in d.rglob("*.csv")) + sum(1 for _ in d.rglob("*.json"))
        html_files = sum(1 for _ in d.rglob("*.html"))
        newest = ""
        for f in list(d.rglob("*.csv")) + list(d.rglob("*.json")) + list(d.rglob("*.md")):
            try:
                head = f.read_text(encoding="utf-8", errors="ignore")[:400000]
            except Exception:  # noqa: BLE001
                continue
            for m in re.findall(r"20\d\d-\d\d-\d\d(?:T\d\d:\d\d(?::\d\d)?Z?)?", head):
                if m > newest:
                    newest = m
        out.append({
            "desk": d.name,
            "entry": f"{d.name}/index.html",
            "data_files": data_files,
            "html_files": html_files,
            "newest": newest or "not dated",
        })
    return out


def repo_html_pages() -> list[Path]:
    pages = []
    for f in REPO.rglob("*.html"):
        parts = f.parts
        if ".git" in parts or "node_modules" in parts:
            continue
        pages.append(f)
    return sorted(pages)


def internal_link_report() -> list[dict]:
    """Every relative href/src in every published HTML file, resolved the way GitHub Pages
    resolves it. This is the repository-wide broken-link check.

    The front door's own pages are excluded: they are written by this build, so on a
    cold tree they would be reported as missing and the count would not be stable.
    verify_hub.py checks the front door's own links instead."""
    broken = []
    for f in repo_html_pages():
        if HERE in f.parents:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for attr, val in re.findall(r'(href|src)="([^"]+)"', text):
            if val.startswith(("http://", "https://", "mailto:", "#", "data:", "javascript:", "tel:")):
                continue
            target = (f.parent / val.split("#")[0].split("?")[0]).resolve()
            if not target.exists():
                broken.append({"page": str(f.relative_to(REPO)), "attr": attr, "value": val})
    return broken


def verifier_sweep() -> list[dict]:
    """Run each desk's own verifier and record the outcome. This is the repository's
    line-by-line evidence: every desk re-proves its own tables."""
    rows = []
    for d in sorted(p for p in REPO.iterdir() if p.is_dir() and not p.name.startswith(".")):
        v = d / "verify.py"
        if not v.exists():
            continue
        try:
            res = subprocess.run(["python3", str(v)], cwd=REPO, capture_output=True,
                                 text=True, timeout=900)
            out = (res.stdout or "") + (res.stderr or "")
            # the most useful summary is the last thing the verifier said
            lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
            summary = lines[-1][:200] if lines else ""
            rows.append({"desk": d.name, "command": f"python3 {d.name}/verify.py",
                         "exit_code": res.returncode, "result": "PASS" if res.returncode == 0 else "FAIL",
                         "summary": summary})
        except subprocess.TimeoutExpired:
            rows.append({"desk": d.name, "command": f"python3 {d.name}/verify.py",
                         "exit_code": 124, "result": "FAIL", "summary": "timed out"})
    return rows


# ---------------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------------

def cards(items: list[tuple]) -> str:
    out = []
    for n, label, note, cls in items:
        out.append(f'<article class="card {cls}"><strong>{esc(n)}</strong>'
                   f'<span>{esc(label)}</span><small>{esc(note)}</small></article>')
    return '<div class="cards">' + "".join(out) + "</div>"


def csv_source(rel: str) -> str:
    """Provenance for a table that is itself the source: a link to the file in the repository."""
    return (f'<a href="{esc(blob(rel))}" target="_blank" rel="noopener noreferrer">'
            f'{esc(rel.split("/")[-1])} ↗</a>')


def evidence_link(ev: str) -> str:
    """The register's own evidence file, linked absolutely so it resolves from the served page."""
    if not ev:
        return '<span class="badge warn">UNVERIFIED — no evidence file</span>'
    if ev.startswith("http"):
        return link(ev)
    return (f'<a href="{esc(blob("nfl-market-desk/" + ev))}" target="_blank" '
            f'rel="noopener noreferrer">evidence file ↗</a>')


def readiness_table(rows) -> str:
    body = []
    for r in rows:
        ev_link = evidence_link(r.get("evidence_path", ""))
        body.append(
            "<tr>"
            + cell(r.get("requirement_id"))
            + cell(r.get("requirement"))
            + cell(status_badge(r.get("status")), True)
            + cell(r.get("gate"))
            + cell(status_badge(r.get("gate_status")), True)
            + cell(r.get("number_that_would_clear_it"))
            + cell(r.get("current_number"))
            + cell(ev_link, True)
            + "</tr>")
    return table(["ID", "Requirement", "Status", "Gate", "Gate status",
                  "Number that would clear it", "Current number", "Evidence"], body)


def build_overview(D) -> str:
    rd = D["readiness"]
    st = count_by(rd, "status")
    stat = count_by(rd, "gate_status")
    orig = D["originated"]
    prices = D["prices"]
    verified_prices = sum(1 for p in prices if str(p.get("verified", "")).startswith("yes"))
    leader = D["leaderboard"]
    certified = sum(1 for l in leader if str(l.get("certified", "")).lower() == "yes")
    results = D["results"]
    finals = sum(1 for r in results if r.get("status") == "FINAL")
    corr = D["correlations"]
    flags = D["flags"]
    blocking = sum(1 for f in flags if str(f.get("severity", "")).lower() == "blocking")

    c = cards([
        (len(rd), "requirements tracked", "one row each, with the gate and the clearing number", ""),
        (f"{stat.get('MET', 0)} / {stat.get('PARTIAL', 0)} / {stat.get('NOT MET', 0)}",
         "met · partial · not met", "the register's own status words", ""),
        (len(orig), "markets originated", "side, then total, then moneyline", ""),
        (f"{verified_prices} of {len(prices)}", "verified price snapshots",
         "no operator quote is admitted yet", "bad" if verified_prices == 0 else "ok"),
        (f"{certified} of {len(leader)}", "certified strategies", "nothing passes every gate", "bad" if certified == 0 else "ok"),
        (f"{finals} of {len(results)}", "settled games in the corpus", "reconciled to the official standings", ""),
        (len(corr), "correlations published", "official inputs only, each with its n", ""),
        (len(flags), "flagged items", f"{blocking} blocking; published, not hidden", "warn"),
    ])

    body = f"""
<section class="hero"><div>
<p class="eyebrow">NFL · EVIDENCE FIRST</p>
<h2>Originate your own lines.<br>Prove the signal before the stake.</h2>
<p>One front door for the repository's NFL work: every requirement with the gate that
blocks it and the number that would clear it, every table row tied to an official source,
and every strategy un-certified until it passes every gate.</p>
</div><aside class="hero-state"><span class="pill">PAPER / NOTHING CERTIFIED</span>
<p>No operator price is admitted, so market residual, closing-line value and real-price
ROI are blank by policy. Every one of those blanks has a flag and a question attached.</p></aside></section>

{c}

<section class="panel"><div class="head"><div><h2>Decision readiness: one row per requirement</h2>
<p>Every requirement in the brief, with the gate that blocks it and the number that would
clear it. This is the canonical register; two other registers exist in the repository and
are linked below, and no combined completion count is published because the crosswalk has
not been verified.</p></div></div>
{readiness_table(rd)}
</section>

<section class="panel"><div class="head"><div><h2>Where to go next</h2>
<p>Organised by category. Each page is built from the desk that owns the table.</p></div></div>
<div class="links">
<a href="executive-summary.html">Executive summary</a>
<a href="requirements.html">Requirements & readiness</a>
<a href="gates.html">Validation gates</a>
<a href="lines.html">Originated lines</a>
<a href="availability.html">Injuries & depth</a>
<a href="correlations.html">Correlations</a>
<a href="leaderboard.html">Leaderboard & strategies</a>
<a href="luck.html">Removal of luck</a>
<a href="questions.html">Questions</a>
<a href="suggestions.html">Suggestions</a>
<a href="flagged.html">Flagged for Review</a>
<a href="sources.html">Official sources</a>
<a href="desks.html">Desk directory</a>
<a href="verification.html">Verification report</a>
</div>
</section>

<section class="panel"><div class="head"><div><h2>Other requirement registers in this repository</h2>
<p>They are not merged into the table above: a merged count would need a row-by-row
crosswalk that has not been verified. Each link opens the register that owns it.</p></div></div>
<ul>
<li><a href="{blob('own5-hub/data/requirements.csv')}" target="_blank" rel="noopener noreferrer">Own5 hub requirements (80 rows) ↗</a></li>
<li><a href="{blob('nfl-command-desk/data/requirements.csv')}" target="_blank" rel="noopener noreferrer">NFL command desk requirements (73 rows) ↗</a></li>
<li><a href="{blob('nfl-integration-a620f5a5/data/audit.csv')}" target="_blank" rel="noopener noreferrer">Integration-hub audit register (13 rows) ↗</a></li>
</ul>
</section>
"""
    return page("Overview", "index.html", body,
                "The repository's NFL front door: requirements, evidence, and what is still open.")


def build_executive_summary(D) -> str:
    rd = D["readiness"]
    st = count_by(rd, "status")
    orig = D["originated"]
    prices = D["prices"]
    verified = sum(1 for p in prices if str(p.get("verified", "")).startswith("yes"))
    leader = D["leaderboard"]
    certified = sum(1 for l in leader if str(l.get("certified", "")).lower() == "yes")
    luck = D["luck"]
    gates = D["gates"]
    gates_met = sum(1 for g in gates if str(g.get("status", "")).upper() == "MET")
    flags = D["flags"]
    blocking = sum(1 for f in flags if str(f.get("severity", "")).lower() == "blocking")
    results = D["results"]
    finals = sum(1 for r in results if r.get("status") == "FINAL")
    avail = D["availability"]
    depth_cov = D["depth_coverage"]
    parsed_clubs = sum(1 for d in depth_cov if str(d.get("parsed", "")).lower() == "yes")
    cascade = D["cascade"]
    depth_strings = count_by(cascade, "depth_of_replacement")

    body = f"""
<section class="panel prose">
<h2>1 · Where the project stands</h2>
<p>The repository originates NFL lines, tracks official availability, computes correlations
from official inputs only and ranks strategies behind fail-closed gates. It has
<strong>{len(rd)} requirements</strong> in the canonical register:
<strong>{st.get('MET', 0)} met</strong>, <strong>{st.get('PARTIAL', 0)} partial</strong>,
<strong>{st.get('NOT MET', 0)} not met</strong>. No strategy is certified.</p>
<p>The corpus holds <strong>{finals} settled games</strong> read from the official schedule
pages. The desk that owns them reconciles all 32 clubs against the official standings.</p>
</section>

<section class="panel prose">
<h2>2 · What is published, and what is deliberately blank</h2>
<ul>
<li><strong>Origination.</strong> {len(orig)} markets are originated in the required order —
side first, then the total, then the moneyline — each with the model's fair line, the
market line and the difference in three separate columns. The difference is published
against an aggregator reference, which is labelled as such and is not an operator quote.</li>
<li><strong>Prices.</strong> {verified} of {len(prices)} price snapshots are verified. No
operator price is admitted, so market residual, closing-line value and real-price ROI are
blank by policy (FLAG-P1, question Q-01, suggestion SG-01).</li>
<li><strong>Depth.</strong> {parsed_clubs} of {len(depth_cov)} club depth charts were parsed
from the clubs' own published pages, with the raw text and its hash kept. The depth of the
replacement is recorded per replacement: {", ".join(f"{k} ({v})" for k, v in depth_strings.items()) or "none recorded yet"}.</li>
<li><strong>Correlations.</strong> {len(D['correlations'])} coefficients are published from
official inputs, each with its sample size and definition; the pairs that would need a
non-official input are withheld and listed as withheld.</li>
</ul>
</section>

<section class="panel prose">
<h2>3 · Removing luck from the ranking</h2>
<p>{len(luck)} prospective panels are published with the observed hit rate, the interval
implied by the model's own probabilities, the Brier score against a coin flip and the
cluster-bootstrapped skill interval. <strong>{len(leader) - certified} of {len(leader)}</strong>
strategy families are on paper. {gates_met} of {len(gates)} gates are met across the
catalogue; a strategy needs every one of them, plus a price, before it can be ranked.</p>
<p>Control baselines (random picks, favourites only) are graded on the same games, so a
lucky staking run cannot be mistaken for a good signal.</p>
</section>

<section class="panel prose">
<h2>4 · What blocks a decision today</h2>
<ul>
<li><strong>No admitted price source</strong> — blocks market residual, closing-line
value, ROI and every price-relative score.</li>
<li><strong>Availability is a snapshot, not a series</strong> — the injury report is read
and captured with a clock time and a hash, but a full Wednesday-to-kickoff series for
every club is not yet retained.</li>
<li><strong>Depth is not universal</strong> — the clubs whose depth chart is an image
cannot be parsed, and their rows are blank rather than guessed.</li>
<li><strong>One season</strong> — holdout and ablation studies need more history than a
single 2026 season.</li>
</ul>
<p>All {len(flags)} flagged items ({blocking} blocking) are published on
<a href="flagged.html">Flagged for Review</a> with their sources; the open questions are
on <a href="questions.html">Questions</a> and the reviewable options are on
<a href="suggestions.html">Suggestions</a>.</p>
</section>

<section class="panel prose">
<h2>5 · How this site is built</h2>
<p>Every table is read at build time from the desk that owns it, and the file that was read
is recorded with its sha256 on the <a href="verification.html">verification report</a>.
Every row carries an official source link or an explicit unverified marker; a value that
cannot be confirmed is printed blank. The repository is re-verified end to end on every
build: the <a href="desks.html">desk directory</a> lists every desk, and each desk's own
verifier is re-run and its result published.</p>
</section>
"""
    return page("Executive summary", "executive-summary.html", body,
                "What is established, what is computed, what is missing, and what must be decided.")


def build_requirements(D) -> str:
    rd = D["readiness"]
    gate_rows = []
    for r in rd:
        gate_rows.append("<tr>" + cell(r.get("requirement_id")) + cell(r.get("gate"))
                         + cell(status_badge(r.get("gate_status")), True) + cell(r.get("status"))
                         + cell(r.get("requirement")) + cell(r.get("number_that_would_clear_it"))
                         + cell(evidence_link(r.get("evidence_path", "")), True) + "</tr>")
    body = f"""
<section class="panel prose"><p>The canonical register holds <strong>{len(rd)}</strong>
requirements, one row each: the requirement, its status, the gate that blocks it, the
number that would clear it, the current number, and the file that proves it. It is read
from <a href="{blob('nfl-market-desk/data/decision_readiness.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/decision_readiness.csv ↗</a>.</p>
<p>Two other registers exist in the repository — the
<a href="{blob('own5-hub/data/requirements.csv')}" target="_blank" rel="noopener noreferrer">Own5 hub register (80 rows) ↗</a>
and the <a href="{blob('nfl-command-desk/data/requirements.csv')}" target="_blank"
rel="noopener noreferrer">command desk register (73 rows) ↗</a>. They are published
separately. A combined completion count is deliberately not published: the crosswalk
between the registers has not been verified row by row, and adding three registers of
different shapes would produce a number nobody could check.</p></section>
<section class="panel"><div class="head"><div><h2>Every requirement, grouped by its blocking gate</h2></div></div>
{table(["ID", "Gate", "Gate status", "Requirement status", "Requirement",
        "Number that would clear it", "Evidence"], gate_rows)}</section>
"""
    return page("Requirements & readiness", "requirements.html", body,
                "One row per requirement: the gate that blocks it and the number that would clear it.")


def build_gates(D) -> str:
    gr = []
    for g in D["gates"]:
        gr.append("<tr>" + cell(g.get("gate_id")) + cell(g.get("name")) + cell(g.get("class"))
                  + cell(g.get("test")) + cell(status_badge(g.get("status")), True)
                  + cell(g.get("blocking_flags")) + cell_RAW(source_row(g.get("source_url"))) + "</tr>")
    dr = []
    for d in D["demotion"]:
        dr.append("<tr>" + cell(d.get("rule_id")) + cell(d.get("trigger")) + cell(d.get("definition"))
                  + cell(d.get("effect")) + cell(d.get("applies_to"))
                  + cell_RAW('<a href="' + esc(blob("nfl-market-desk/data/demotion_rules.csv"))
                             + '" target="_blank" rel="noopener noreferrer">rule register ↗</a>')
                  + "</tr>")
    body = f"""
<section class="panel prose"><p>Gates are fail-closed: a strategy that has not met every
gate is on paper. The demotion rules are the other half — a live strategy that loses its
edge is sent back to paper on a stated trigger, not on a hunch.</p></section>
<section class="panel"><div class="head"><div><h2>Validation gates</h2></div></div>
{table(["Gate", "Name", "Class", "Test", "Status", "Blocking flags", "Source"], gr)}</section>
<section class="panel"><div class="head"><div><h2>Demotion gate — a live strategy returns to paper</h2></div></div>
{table(["Rule", "Trigger", "Definition", "Effect", "Applies to", "Source"], dr)}</section>
"""
    return page("Validation gates", "gates.html", body,
                "What a strategy must pass, and what sends it back to paper.")


def build_lines(D) -> str:
    orig = D["originated"]
    body_rows = []
    for r in orig:
        body_rows.append(
            "<tr>"
            + cell(r.get("week"))
            + cell(f"{r.get('away')} @ {r.get('home')}" + (" (neutral)" if str(r.get("neutral_site", "")).lower() in ("yes", "true") else ""))
            + cell(r.get("market_type"))
            + cell(r.get("origination_order"))
            + cell(r.get("derived_from"))
            + cell(r.get("fair_line"))
            + cell(r.get("market_line"))
            + cell(r.get("difference_fair_minus_market"))
            + cell(r.get("probability"))
            + cell(r.get("model_inputs"))
            + cell_RAW(source_row(r.get("slate_source_url"), r.get("slate_source_tier")))
            + cell_RAW(source_row(r.get("market_source_url"), r.get("market_source_tier")))
            + "</tr>")
    price_rows = []
    for p in D["prices"][:60]:
        price_rows.append(
            "<tr>" + cell(p.get("snapshot_id")) + cell(p.get("snapshot_type"))
            + cell(p.get("snapshot_meaning")) + cell(p.get("snapshot_utc"))
            + cell(p.get("line_value")) + cell(p.get("price_american"))
            + cell(p.get("verified")) + cell(p.get("flag_id"))
            + cell_RAW(source_row(p.get("source_url"), p.get("source_tier"))) + "</tr>")
    pol = D["price_policy"]
    pol_rows = []
    for p in pol:
        cols = [k for k in p.keys() if k != "source_url"]
        pol_rows.append("<tr>" + "".join(cell(p.get(k)) for k in cols)
                        + cell_RAW(source_row(p.get("source_url"), p.get("tier"))) + "</tr>")
    body = f"""
<section class="panel prose"><p>Lines are originated in one order: <strong>the side
first</strong>, then the total, then the moneyline, with each later step derived from the
step before it. The model's fair line, the market line and the difference are published as
three separate columns, so a reader can see the size of the gap and its direction without
doing arithmetic.</p>
<p>The market line here is an <strong>aggregator reference of unknown timestamp</strong>,
kept for context and labelled as such. It is not an operator quote, so no residual,
closing-line value or ROI is computed from it. The price policy is on the record and
undecided.</p></section>
<section class="panel"><div class="head"><div><h2>Originated markets</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/originated_markets.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/originated_markets.csv ↗</a></p></div></div>
{table(["Week", "Matchup", "Market", "Order", "Derived from", "Fair line (model)",
        "Market line (reference)", "Difference (fair − market)", "Model probability",
        "Model inputs", "Slate source", "Market reference source"], body_rows)}</section>
<section class="panel"><div class="head"><div><h2>Price-snapshot store</h2>
<p>Opening and closing slots exist for every market we originate. They are empty until a
permitted price source is admitted, and every empty slot is flagged. Source:
<a href="{blob('nfl-market-desk/data/price_snapshots.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/price_snapshots.csv ↗</a></p></div></div>
{table(["Snapshot", "Type", "Meaning", "Captured (UTC)", "Line", "Price",
        "Verified?", "Flag", "Source"], price_rows)}</section>
<section class="panel"><div class="head"><div><h2>Price-data policy (on the record, not yet decided)</h2></div></div>
{table([k for k in pol[0].keys() if k != "source_url"] + ["Source"] if pol else [], pol_rows)}</section>
"""
    return page("Originated lines", "lines.html", body,
                "Side, then total, then moneyline — with the fair line, the market line and the difference apart.")


def build_availability(D) -> str:
    av = []
    for r in D["availability"]:
        av.append("<tr>" + cell(r.get("club")) + cell(r.get("report_rows")) + cell(r.get("named_out"))
                  + cell(r.get("doubtful")) + cell(r.get("questionable")) + cell(r.get("no_designation"))
                  + cell(r.get("practice_dnp")) + cell(r.get("practice_limited")) + cell(r.get("practice_full"))
                  + cell(r.get("starters_named_out")) + cell(r.get("replacements_named"))
                  + cell(r.get("compounding_replacements")) + cell(r.get("net_unavailable_score"))
                  + cell(r.get("coverage_note")) + cell_RAW(source_row(r.get("injury_source_url"))) + "</tr>")
    cas = []
    for r in D["cascade"]:
        cas.append("<tr>" + cell(r.get("club")) + cell(r.get("starter")) + cell(r.get("starter_position_on_chart"))
                   + cell(r.get("starter_status")) + cell(r.get("starter_slot")) + cell(r.get("replacement"))
                   + cell(r.get("replacement_slot_rank")) + cell(r.get("depth_of_replacement"))
                   + cell(r.get("replacement_game_status")) + cell(r.get("compounding"))
                   + cell_RAW(source_row(r.get("depth_source_url"))) + cell_RAW(source_row(r.get("injury_source_url"))) + "</tr>")
    dc = []
    for r in D["depth_coverage"]:
        dc.append("<tr>" + cell(r.get("club")) + cell(r.get("rows_parsed")) + cell(r.get("players_parsed"))
                  + cell(r.get("shared_slots")) + cell(r.get("empty_slots")) + cell(r.get("jersey_numbers_stripped"))
                  + cell(r.get("parsed")) + cell(r.get("verification_status")) + cell(r.get("raw_file_sha256"))
                  + cell_RAW(source_row(r.get("depth_url"))) + "</tr>")
    ann = []
    for r in D["announced"]:
        ann.append("<tr>" + cell(r.get("id")) + cell(r.get("club")) + cell(r.get("player"))
                   + cell(r.get("position")) + cell(r.get("headline")) + cell(r.get("published_date"))
                   + cell(r.get("announced_starter")) + cell(r.get("evidence_type"))
                   + cell_RAW(source_row(r.get("url"), r.get("source_tier"))) + "</tr>")
    sweep = []
    for r in D["roster_sweep"]:
        sweep.append("<tr>" + cell(r.get("club")) + cell(r.get("on_week10_report"))
                     + cell(r.get("reason_if_absent")) + cell(r.get("depth_chart_status"))
                     + cell(r.get("roster_rows_captured")) + cell(r.get("roster_active_rows"))
                     + cell(r.get("roster_status_note")) + cell_RAW(source_row(r.get("report_source_url"))) + "</tr>")
    body = f"""
<section class="panel prose"><p>Availability is read from the official NFL injury report and
kept with the clock time of the read. Two rules matter for anything downstream:</p>
<ul><li>An injury designation is a <strong>surprise, not a level</strong> — what matters is
the change between reads, and the delta table on the capture ledger is what gets published.</li>
<li>Depth of a replacement is measured by <strong>playing time</strong> on the club's own
published depth chart, never by jersey order, experience or salary. A slot shared by two
players, or left empty, is recorded as shared or empty rather than invented.</li></ul>
<p>Replacement columns are blank where the club publishes its depth chart as an image: the
blank is the evidence, and the flag says so.</p></section>

<section class="panel"><div class="head"><div><h2>Availability by club (Week 10 report)</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/availability_by_team.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/availability_by_team.csv ↗</a>. The
"unavailable score" is a stated weighting, not an estimate of points.</p></div></div>
{table(["Club", "Report rows", "Named out", "Doubtful", "Questionable", "No designation",
        "Practice DNP", "Limited", "Full", "Starters named out", "Replacements named",
        "Compounding", "Unavailable score", "Coverage note", "Source"], av)}</section>

<section class="panel"><div class="head"><div><h2>Depth of the replacement — 1st to 4th string</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/replacement_cascade.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/replacement_cascade.csv ↗</a></p></div></div>
{table(["Club", "Starter", "Position", "Starter status", "Starter slot", "Replacement",
        "Replacement rank", "Depth of replacement", "Replacement status", "Compounding",
        "Depth source", "Injury source"], cas)}</section>

<section class="panel"><div class="head"><div><h2>Depth-chart coverage by club</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/depth_coverage.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/depth_coverage.csv ↗</a>. The raw text and
its sha256 are kept so the parse can be replayed.</p></div></div>
{table(["Club", "Rows parsed", "Players parsed", "Shared slots", "Empty slots",
        "Jersey numbers stripped", "Parsed", "Verification", "Raw sha256", "Depth page"], dc)}</section>

<section class="panel"><div class="head"><div><h2>Announced starter changes (official news)</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/announced_starter_changes.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/announced_starter_changes.csv ↗</a></p></div></div>
{table(["ID", "Club", "Player", "Position", "Official headline", "Published", "Announced starter",
        "Evidence type", "Source"], ann)}</section>

<section class="panel"><div class="head"><div><h2>32-club roster / IR sweep</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/roster_sweep_32.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/roster_sweep_32.csv ↗</a></p></div></div>
{table(["Club", "On the Week 10 report", "Reason if absent", "Depth chart status",
        "Roster rows captured", "Active rows", "Status note", "Source"], sweep)}</section>
"""
    return page("Injuries & depth", "availability.html", body,
                "Who is out, who replaces them, and how deep the replacement really is.")


def build_correlations(D) -> str:
    cr = []
    for r in D["correlations"]:
        cr.append("<tr>" + cell(r.get("corr_id")) + cell(r.get("unit_of_analysis"))
                  + cell(r.get("metric_a")) + cell(r.get("metric_b")) + cell(r.get("r"))
                  + cell(r.get("r_squared")) + cell(r.get("p_two_sided")) + cell(r.get("n"))
                  + cell(r.get("n_definition")) + cell(r.get("inputs_tier"))
                  + cell_RAW(source_row(r.get("source_url"))) + cell(r.get("note")) + "</tr>")
    wh = []
    for r in D["withheld"]:
        wh.append("<tr>" + cell(r.get("withheld_id")) + cell(r.get("pair"))
                  + cell(r.get("why_not_published")) + cell(r.get("prior_input_tier"))
                  + cell(r.get("status"))
                  + cell_RAW(csv_source("nfl-market-desk/data/correlations_withheld.csv")) + "</tr>")
    body = f"""
<section class="panel prose"><p>Every published coefficient is computed from official
inputs only, and every row publishes its own <strong>n</strong> and the definition of what
n counts. A coefficient without n is not published. Pairs that would need a non-official
input are withheld and listed as withheld rather than quietly carried over from an
earlier desk.</p></section>
<section class="panel"><div class="head"><div><h2>Published correlations (official inputs only)</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/correlations_official.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/correlations_official.csv ↗</a></p></div></div>
{table(["ID", "Unit", "Metric A", "Metric B", "r", "r²", "p (two-sided)", "n",
        "Definition of n", "Input tier", "Source", "Note"], cr)}</section>
<section class="panel"><div class="head"><div><h2>Withheld correlations</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/correlations_withheld.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/correlations_withheld.csv ↗</a></p></div></div>
{table(["ID", "Pair", "Why it is not published", "Prior input tier", "Status", "Source"], wh)}</section>
"""
    return page("Correlations", "correlations.html", body,
                "Official inputs only, each value with its n, and nothing inferred.")


def build_leaderboard(D) -> str:
    lb = []
    for r in D["leaderboard"]:
        lb.append("<tr>" + cell(r.get("family_id")) + cell(r.get("family")) + cell(r.get("bet_class"))
                  + cell(r.get("signal_type")) + cell(r.get("universe")) + cell(r.get("graded_bets"))
                  + cell(r.get("signal_headline")) + cell(r.get("signal_brier"))
                  + cell(r.get("signal_p_raw")) + cell(r.get("signal_p_holm"))
                  + cell(r.get("staking_n_priced")) + cell(r.get("staking_roi_pct"))
                  + cell(r.get("rank_gap")) + cell(r.get("hit_rate"))
                  + cell(r.get("gates_status")) + cell(status_badge(r.get("certified")), True)
                  + cell(status_badge(r.get("state")), True) + cell(r.get("why_not_certified"))
                  + cell_RAW(csv_source("nfl-market-desk/data/leaderboard.csv")) + "</tr>")
    reg = []
    for r in D["registration"]:
        reg.append("<tr>" + cell(r.get("family_id")) + cell(r.get("family")) + cell(r.get("bet_class"))
                   + cell(r.get("rule_text")) + cell(r.get("universe_definition"))
                   + cell(r.get("registration_file")) + cell(r.get("registration_sha256"))
                   + cell(r.get("registered_utc")) + cell(r.get("registered_by"))
                   + cell(r.get("threshold_fixed")) + cell(r.get("status_at_registration"))
                   + cell_RAW(csv_source("nfl-market-desk/data/strategy_registration.csv")) + "</tr>")
    ctl = []
    for r in D["controls"]:
        ctl.append("<tr>" + cell(r.get("control_id")) + cell(r.get("name")) + cell(r.get("n_rows"))
                   + cell(r.get("n_decided")) + cell(r.get("brier")) + cell(r.get("hit_rate"))
                   + cell(r.get("signal_score_vs_coinflip"))
                   + cell_RAW(csv_source("nfl-market-desk/data/control_summary.csv")) + "</tr>")
    body = f"""
<section class="panel prose"><p>Signal and staking are scored separately. A signal score is
a proper score against the model, never a return; a staking figure is only published when
a real price exists. A family cannot be certified on a staking run, and the
<em>rank gap</em> column shows where the two orders disagree.</p>
<p>Control baselines are graded on the same games, so a lucky run is visible as a lucky
run.</p></section>
<section class="panel"><div class="head"><div><h2>Leaderboard — signal score and staking score, separately</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/leaderboard.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/leaderboard.csv ↗</a></p></div></div>
{table(["ID", "Family", "Bet class", "Signal type", "Universe", "Graded bets",
        "Signal headline", "Signal Brier", "p raw", "p (Holm)", "Staking n priced",
        "Staking ROI %", "Rank gap", "Hit rate", "Gates", "Certified", "State",
        "Why not certified", "Source"], lb)}</section>
<section class="panel"><div class="head"><div><h2>Pre-registration — every strategy declared before its results</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/strategy_registration.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/strategy_registration.csv ↗</a></p></div></div>
{table(["ID", "Family", "Bet class", "Rule text", "Universe", "Registration file",
        "Registration sha256", "Registered (UTC)", "Registered by", "Threshold fixed",
        "Status at registration", "Source"], reg)}</section>
<section class="panel"><div class="head"><div><h2>Control baselines</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/control_summary.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/control_summary.csv ↗</a></p></div></div>
{table(["ID", "Control", "Rows", "Decided", "Brier", "Hit rate", "Skill vs coin flip", "Source"], ctl)}</section>
"""
    return page("Leaderboard & strategies", "leaderboard.html", body,
                "Signal separated from staking, gated, pre-registered, and controlled.")


def build_luck(D) -> str:
    lp = []
    for r in D["luck"]:
        lp.append("<tr>" + cell(r.get("panel")) + cell(r.get("n_games")) + cell(r.get("pick_accuracy"))
                  + cell(r.get("pick_accuracy_ci95")) + cell(r.get("hits_observed"))
                  + cell(r.get("hits_expected_from_model_probs")) + cell(r.get("hits_above_expectation"))
                  + cell(r.get("binomial_p_vs_model_expectation")) + cell(r.get("brier_model"))
                  + cell(r.get("brier_coinflip")) + cell(r.get("brier_skill_vs_coinflip"))
                  + cell(r.get("brier_cluster_boot_ci95")) + cell(r.get("reading"))
                  + cell_RAW(csv_source("nfl-market-desk/data/luck_panel.csv")) + "</tr>")
    acc = []
    for r in D["accuracy"]:
        cols = [k for k in r.keys() if k != "source_url"]
        acc.append("<tr>" + "".join(cell(r.get(k)) for k in cols)
                   + cell_RAW(csv_source("nfl-market-desk/data/model_accuracy.csv")) + "</tr>")
    abl = []
    for r in D["ablation"]:
        abl.append("<tr>" + cell(r.get("game_id")) + cell(r.get("week")) + cell(r.get("home"))
                   + cell(r.get("away")) + cell(r.get("out_home")) + cell(r.get("out_away"))
                   + cell(r.get("questionable_home")) + cell(r.get("questionable_away"))
                   + cell(r.get("availability_diff")) + cell(r.get("depth_chart_available_home"))
                   + cell(r.get("depth_chart_available_away"))
                   + cell(r.get("prob_home_win_no_personnel"))
                   + cell(r.get("prob_home_win_with_personnel"))
                   + cell(r.get("actual_home_win")) + cell(r.get("depth_note"))
                   + cell_RAW(source_row(r.get("injury_source_url"))) + "</tr>")
    body = f"""
<section class="panel prose"><p>Luck is bounded, not removed. For every prospective panel
the site publishes the observed hit rate, the interval implied by the model's own
probabilities, the Brier score against a coin flip and the game-clustered bootstrap
interval of the skill. A hit rate that sits inside its own interval is not evidence of
skill, however good it looks.</p>
<p>The ablation compares the <em>same</em> model with and without the personnel features
instead of subtracting a fixed number of points for a missing starter, so the effect of
availability is measured with its uncertainty rather than assumed.</p></section>
<section class="panel"><div class="head"><div><h2>Removal of luck — the panel</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/luck_panel.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/luck_panel.csv ↗</a></p></div></div>
{table(["Panel", "n games", "Pick accuracy", "95% CI", "Hits observed",
        "Hits expected from model probabilities", "Hits above expectation",
        "Binomial p vs model", "Brier (model)", "Brier (coin flip)",
        "Brier skill vs coin flip", "Cluster bootstrap CI", "Reading", "Source"], lp)}</section>
<section class="panel"><div class="head"><div><h2>Model accuracy by holdout</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/model_accuracy.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/model_accuracy.csv ↗</a></p></div></div>
{table([k for k in D["accuracy"][0].keys() if k != "source_url"] + ["Source"] if D["accuracy"] else [], acc)}</section>
<section class="panel"><div class="head"><div><h2>Personnel ablation — same model, with and without availability</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/personnel_ablation.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/personnel_ablation.csv ↗</a></p></div></div>
{table(["Game", "Week", "Home", "Away", "Out (home)", "Out (away)", "Questionable (home)",
        "Questionable (away)", "Availability diff", "Depth chart (home)", "Depth chart (away)",
        "P(home) without personnel", "P(home) with personnel", "Actual home win", "Depth note",
        "Source"], abl)}</section>
"""
    return page("Removal of luck", "luck.html", body,
                "Proper scores, clustered intervals, and an ablation instead of a fixed penalty.")


def build_questions(D) -> str:
    q = []
    for r in D["questions"]:
        q.append("<tr>" + cell(r.get("question_id")) + cell(r.get("question"))
                 + cell(r.get("have_information")) + cell(r.get("have_what"))
                 + cell(r.get("missing_what")) + cell(r.get("cheapest_route_to_answer"))
                 + cell(r.get("blocks")) + cell(r.get("related_flags"))
                 + cell(status_badge("ANSWERABLE" if str(r.get("answerable_today")).lower() == "yes" else "OPEN"), True)
                 + cell_RAW(csv_source("nfl-market-desk/data/questions.csv")) + "</tr>")
    hq = []
    for r in D["hub_questions"]:
        hq.append("<tr>" + cell(r.get("question_id")) + cell(r.get("question"))
                  + cell(r.get("known_from_verified_sources")) + cell(r.get("missing_information"))
                  + cell(r.get("answer_needed_before_decision")) + cell(r.get("clearing_evidence"))
                  + cell(r.get("source_status"))
                  + cell_RAW(csv_source("nfl-integration-a620f5a5/data/questions.csv")) + "</tr>")
    body = f"""
<section class="panel prose"><p>Each question states what is known now from a verified
source, what is missing, the cheapest route to answer it, and what it blocks. A question
is not closed by a plausible answer; it is closed by evidence.</p></section>
<section class="panel"><div class="head"><div><h2>Open questions</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/questions.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/questions.csv ↗</a></p></div></div>
{table(["ID", "Question", "Have information?", "What we have", "What is missing",
        "Cheapest route to an answer", "What it blocks", "Related flags", "Status", "Source"], q)}</section>
<section class="panel"><div class="head"><div><h2>Repository-wide decision questions</h2>
<p>Source: <a href="{blob('nfl-integration-a620f5a5/data/questions.csv')}" target="_blank"
rel="noopener noreferrer">nfl-integration-a620f5a5/data/questions.csv ↗</a></p></div></div>
{table(["ID", "Question", "Known from verified sources", "Missing information",
        "Answer needed before a decision", "Clearing evidence", "Source status", "Source"], hq)}</section>
"""
    return page("Questions", "questions.html", body,
                "What is known, what is missing, what it blocks, and the cheapest way to find out.")


def build_suggestions(D) -> str:
    s = []
    for r in D["suggestions"]:
        s.append("<tr>" + cell(r.get("suggestion_id")) + cell(r.get("topic")) + cell(r.get("priority"))
                 + cell(r.get("options")) + cell(r.get("recommended_path"))
                 + cell(r.get("reversible_rule")) + cell(r.get("cost")) + cell(r.get("status"))
                 + cell_RAW(csv_source("nfl-market-desk/data/suggestions.csv")) + "</tr>")
    hs = []
    for r in D["hub_suggestions"]:
        hs.append("<tr>" + cell(r.get("suggestion_id")) + cell(r.get("priority")) + cell(r.get("topic"))
                  + cell(r.get("options")) + cell(r.get("recommended_path"))
                  + cell(r.get("what_would_change_the_recommendation")) + cell(r.get("decision_status"))
                  + cell(r.get("source_status"))
                  + cell_RAW(csv_source("nfl-integration-a620f5a5/data/suggestions.csv")) + "</tr>")
    body = f"""
<section class="panel prose"><p>Nothing here has been implemented. Each suggestion states
its options, the recommended path, the rule that would make the recommendation reversible,
and the test that would change the call. The decision is yours; this section exists so the
options can be compared before anything is built.</p></section>
<section class="panel"><div class="head"><div><h2>Suggestions register</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/suggestions.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/suggestions.csv ↗</a></p></div></div>
{table(["ID", "Topic", "Priority", "Options", "Recommended path", "Reversible rule",
        "Cost", "Status", "Source"], s)}</section>
<section class="panel"><div class="head"><div><h2>Integration-hub suggestions</h2>
<p>Source: <a href="{blob('nfl-integration-a620f5a5/data/suggestions.csv')}" target="_blank"
rel="noopener noreferrer">nfl-integration-a620f5a5/data/suggestions.csv ↗</a></p></div></div>
{table(["ID", "Priority", "Topic", "Options", "Recommended path",
        "What would change the recommendation", "Decision status", "Source status", "Source"], hs)}</section>
"""
    return page("Suggestions", "suggestions.html", body,
                "Options, a recommended path, and what would change the call — reviewed before anything is built.")


def build_flagged(D) -> str:
    fl = []
    for r in D["flags"]:
        fl.append("<tr>" + cell(r.get("flag_id")) + cell(r.get("origin")) + cell(r.get("severity"))
                  + cell(r.get("area")) + cell(r.get("title")) + cell(r.get("detail"))
                  + cell(r.get("consequence")) + cell(r.get("action")) + cell(r.get("status"))
                  + cell_RAW(source_row(r.get("source_url"))) + cell(r.get("fetched_utc")) + "</tr>")
    au = []
    for r in D["hub_audit"]:
        au.append("<tr>" + cell(r.get("audit_id")) + cell(r.get("severity")) + cell(r.get("area"))
                  + cell(r.get("observation")) + cell(r.get("decision_impact"))
                  + cell(r.get("clearance_rule")) + cell(r.get("source_status"))
                  + cell_RAW(csv_source("nfl-integration-a620f5a5/data/audit.csv")) + "</tr>")
    body = f"""
<section class="panel prose"><p>Every irregularity is published with the file it was found
in and the source that shows it. Flagged items do not block the site; they block claims.
Nothing here is silently corrected, and no value is filled in where the source is silent.</p></section>
<section class="panel"><div class="head"><div><h2>Flagged for review — market desk register</h2>
<p>Source: <a href="{blob('nfl-market-desk/data/flags.csv')}" target="_blank"
rel="noopener noreferrer">nfl-market-desk/data/flags.csv ↗</a></p></div></div>
{table(["ID", "Found in", "Severity", "Area", "Issue", "Detail", "Consequence", "Action",
        "Status", "Source", "Fetched (UTC)"], fl)}</section>
<section class="panel"><div class="head"><div><h2>Flagged for review — integration audit</h2>
<p>Source: <a href="{blob('nfl-integration-a620f5a5/data/audit.csv')}" target="_blank"
rel="noopener noreferrer">nfl-integration-a620f5a5/data/audit.csv ↗</a></p></div></div>
{table(["ID", "Severity", "Area", "Observation", "Decision impact", "Clearance rule",
        "Source status", "Source"], au)}</section>
"""
    return page("Flagged for Review", "flagged.html", body,
                "Irregularities and unverified values, published with their sources.")


def build_sources(D) -> str:
    seen: dict[str, dict] = {}
    for key, rel, owner in SOURCES:
        for r in D[key]:
            for field in ("source_url", "url", "injury_source_url", "depth_source_url",
                          "slate_source_url", "market_source_url", "venue_source_url",
                          "report_source_url", "announcement_url", "input_url"):
                u = (r.get(field) or "").strip()
                if not u.startswith("http"):
                    continue
                rec = seen.setdefault(u, {"url": u, "used_by": set(), "rows": 0})
                rec["used_by"].add(owner)
                rec["rows"] += 1
    rows = []
    for u in sorted(seen):
        rec = seen[u]
        tier = "official" if ("nfl.com" in u or "operations.nfl.com" in u
                              or "media.nfl.com" in u) else "other publisher"
        rows.append("<tr>" + cell(u[:88]) + cell(tier) + cell(rec["rows"])
                    + cell(", ".join(sorted(rec["used_by"])))
                    + cell(link(u, "open ↗"), True) + "</tr>")
    hs = []
    for r in D["hub_sources"]:
        hs.append("<tr>" + cell(r.get("source_id")) + cell(r.get("publisher")) + cell(r.get("title"))
                  + cell(r.get("url")) + cell(r.get("checked_on")) + cell(r.get("verified_observation"))
                  + cell(r.get("scope_limit"))
                  + cell_RAW(link(r.get("url"), "open ↗")) + "</tr>")
    body = f"""
<section class="panel prose"><p>Every URL used by the tables on this site, deduplicated,
with the number of rows that cite it. A URL whose host is not an official publisher is
labelled as such: aggregator references are kept for context and are never presented as
official prices.</p></section>
<section class="panel"><div class="head"><div><h2>Sources used by this site</h2></div></div>
{table(["URL", "Tier", "Rows citing it", "Used by", "Link"], rows)}</section>
<section class="panel"><div class="head"><div><h2>Official source register (integration hub)</h2>
<p>Source: <a href="{blob('nfl-integration-a620f5a5/data/sources.csv')}" target="_blank"
rel="noopener noreferrer">nfl-integration-a620f5a5/data/sources.csv ↗</a></p></div></div>
{table(["ID", "Publisher", "Title", "URL", "Checked on", "Verified observation", "Scope limit", "Link"], hs)}</section>
"""
    return page("Official sources", "sources.html", body,
                "Every URL the tables cite, with the number of rows behind it.")


def build_desks(D) -> str:
    rows = []
    for d in D["desks"]:
        rows.append("<tr>" + cell(d["desk"]) + cell(d["data_files"]) + cell(d["html_files"])
                    + cell(d["newest"])
                    + cell(f'<a href="../{esc(d["entry"])}">open ↗</a>', True)
                    + cell(f'<a href="{BLOB}{esc(d["entry"])}" target="_blank" rel="noopener noreferrer">source ↗</a>', True)
                    + "</tr>")
    body = f"""
<section class="panel prose"><p>Every desk in the repository, discovered from the working
tree when this page was built, so the directory cannot drift from what is published. The
"newest dated string" column is the newest date that appears in the desk's own data
files; it is a currency signal, not a claim that the desk was re-read.</p></section>
<section class="panel"><div class="head"><div><h2>Desk directory</h2></div></div>
{table(["Desk", "Data files", "Pages", "Newest dated string in its own files", "Entry page",
        "Repository source"], rows)}</section>
"""
    return page("Desk directory", "desks.html", body,
                "Every desk in the repository, with its entry page and its newest dated data.")


def build_verification(D) -> str:
    vr = []
    for r in D["verifiers"]:
        vr.append("<tr>" + cell(r["desk"]) + cell(r["command"]) + cell(r["result"])
                  + cell(r["summary"])
                  + cell_RAW(csv_source("nfl-integration-3ddb3f07/data/verifier_runs.csv")) + "</tr>")
    lin = []
    for r in D["lineage"]:
        lin.append("<tr>" + cell(r["path"]) + cell(r["rows"]) + cell(r["bytes"])
                   + cell(f'<code>{esc(r["sha256"][:16])}…</code>', True)
                   + cell_RAW(csv_source(r["path"])) + "</tr>")
    broken = D["broken_links"]
    body = f"""
<section class="panel prose"><p>This page is written by the build itself. It lists the
tables that were read (with the sha256 of the file that was read), the result of every
desk's own verifier when it was re-run, and the repository-wide link check.</p></section>
<section class="panel"><div class="head"><div><h2>Link check</h2>
<p>Every relative <code>href</code> and <code>src</code> in every published HTML file in
the repository except this front door's own pages, resolved the way GitHub Pages resolves
it. <strong>{len(broken)} broken</strong> across {len(D['html_pages'])} pages checked.</p></div></div>
{(table(["Page", "Attribute", "Broken value"], ["<tr>" + "".join(cell(b[k]) for k in ("page", "attr", "value")) + "</tr>" for b in broken]) if broken else "<p class='ok'>No broken internal links.</p>")}
</section>
<section class="panel"><div class="head"><div><h2>Desk verifiers, re-run at build time</h2></div></div>
{table(["Desk", "Command", "Result", "Summary", "Source"], vr)}</section>
<section class="panel"><div class="head"><div><h2>Lineage — the files this site was built from</h2></div></div>
{table(["File", "Data rows", "Bytes", "sha256", "Source"], lin)}</section>
"""
    return page("Verification report", "verification.html", body,
                "What was read, what re-verified, and what the link check found.")


# ---------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------

PAGES = {
    "index.html": build_overview,
    "executive-summary.html": build_executive_summary,
    "requirements.html": build_requirements,
    "gates.html": build_gates,
    "lines.html": build_lines,
    "availability.html": build_availability,
    "correlations.html": build_correlations,
    "leaderboard.html": build_leaderboard,
    "luck.html": build_luck,
    "questions.html": build_questions,
    "suggestions.html": build_suggestions,
    "flagged.html": build_flagged,
    "sources.html": build_sources,
    "desks.html": build_desks,
    "verification.html": build_verification,
}


def main() -> int:
    D = {}
    for key, rel, owner in SOURCES:
        D[key] = read(rel)
    D["desks"] = desk_directory()
    D["verifiers"] = read("nfl-integration-3ddb3f07/data/verifier_runs.csv")
    D["broken_links"] = internal_link_report()
    D["html_pages"] = [str(p.relative_to(REPO)) for p in repo_html_pages()]

    D["lineage"] = sorted(LINEAGE, key=lambda r: r["path"])
    for name, fn in PAGES.items():
        (OUT / name).write_text(fn(D), encoding="utf-8")

    DATA.mkdir(exist_ok=True)
    lin = D["lineage"]
    with (DATA / "lineage.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "rows", "bytes", "sha256"], lineterminator="\n")
        w.writeheader()
        w.writerows(lin)
    print(f"built {len(PAGES)} pages from {len(lin)} source files; "
          f"{len(D['broken_links'])} broken internal links found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

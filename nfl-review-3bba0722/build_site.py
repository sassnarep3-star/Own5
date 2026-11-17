#!/usr/bin/env python3
"""Build the isolated, evidence-first NFL decision review hub (stdlib only)."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"


def load_json(name: str) -> Any:
    with (DATA / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


SOURCES = load_json("sources.json")
SOURCE_BY_ID = {source["id"]: source for source in SOURCES}
QUESTIONS = load_json("questions.json")
SUGGESTIONS = load_json("suggestions.json")
FLAGS = load_json("flagged.json")
READINESS = load_json("readiness.json")
SUMMARY = load_json("summary.json")

NAV_ITEMS = [
    ("index.html", "Overview", "index"),
    ("questions.html", "Questions & answers", "questions"),
    ("suggestions.html", "Suggestions for review", "suggestions"),
    ("flagged.html", "Flagged for review", "flagged"),
    ("sources.html", "Sources", "sources"),
    ("summary.html", "Executive summary", "summary"),
]


def badge(text: str, tone: str = "neutral") -> str:
    return f'<span class="badge {esc(tone)}">{esc(text)}</span>'


def status_tone(status: str) -> str:
    upper = status.upper()
    if "UNVERIFIED" in upper or "MISMATCH" in upper or "BLOCKED" in upper or "OPEN" in upper:
        return "danger"
    if "PARTIAL" in upper or "REVIEW" in upper or "AWAITING" in upper or "RESTRICTION" in upper or "IMAGE-ONLY" in upper:
        return "warn"
    if "VERIFIED" in upper or "RECHECKED" in upper or "RESOLUTION" in upper:
        return "good"
    return "neutral"


def source_links(source_ids: list[str] | None) -> str:
    if not source_ids:
        return badge("UNVERIFIED — no official source confirmed", "danger")
    rendered: list[str] = []
    for source_id in source_ids:
        source = SOURCE_BY_ID[source_id]
        status = source["verification_status"]
        tone = status_tone(status)
        rendered.append(
            '<div class="source-item">'
            f'<a class="source-link" href="{esc(source["url"])}" target="_blank" '
            f'rel="noopener noreferrer">{esc(source["publisher"])} · {esc(source["title"])} ↗</a>'
            f'<span class="source-status {tone}">{esc(status)}</span>'
            "</div>"
        )
    return "".join(rendered)


def evidence_links(items: list[dict[str, str]] | None) -> str:
    if not items:
        return ""
    links = "".join(
        f'<a class="repo-link" href="{esc(item["url"])}">{esc(item["label"])} ↗</a>'
        for item in items
    )
    return f'<div class="repo-evidence"><span>Repository evidence</span>{links}</div>'


def status_cell(status: str) -> str:
    return badge(status, status_tone(status))


def page(title: str, description: str, active: str, body: str) -> str:
    nav_parts = []
    for href, label, key in NAV_ITEMS:
        active_class = "active" if key == active else ""
        current_attr = ' aria-current="page"' if key == active else ""
        nav_parts.append(
            f'<a href="{esc(href)}" class="nav-link {active_class}"{current_attr}>{esc(label)}</a>'
        )
    nav = "".join(nav_parts)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="#102720">
  <title>{esc(title)} · Own5 NFL Decision Review</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="site-shell">
    <header class="site-header">
      <a class="brand" href="index.html" aria-label="Own5 NFL Decision Review home">
        <span class="brand-mark">O<span>5</span></span>
        <span class="brand-name">OWN5 <small>NFL DECISION REVIEW</small></span>
      </a>
      <div class="header-meta"><span class="review-dot"></span> Source re-check · 17 Nov 2026</div>
    </header>
    <nav class="main-nav" aria-label="Review hub navigation">{nav}</nav>
    <main id="main">
      <div class="page-title">
        <p class="eyebrow">NFL · EVIDENCE FIRST · REVIEW ONLY</p>
        <h1>{esc(title)}</h1>
        <p class="page-description">{esc(description)}</p>
      </div>
      {body.strip()}
      </main>
    <footer class="site-footer">
      <span>Own5 · Independent research · Not affiliated with the NFL.</span>
      <span>Blank means unverified, not zero. No picks, prices or wager recommendations are published here.</span>
      <span><a href="../index.html">Root research dashboard</a> · <a href="https://github.com/sassnarep3-star/Own5" target="_blank" rel="noopener noreferrer">Repository ↗</a></span>
    </footer>
  </div>
</body>
</html>
'''


def readiness_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        observed = row["observed_value"]
        observed_value = esc(observed) if observed else '<span class="blank-value">—</span>'
        body.append(
            f'<tr id="{esc(row["id"])}">'
            f'<td><strong>{esc(row["id"])}</strong><br>{esc(row["requirement"])}</td>'
            f'<td>{status_cell(row["status"])}</td>'
            f'<td><strong>{esc(row["blocking_gate"])}</strong><p>{esc(row["observed_note"])}</p>'
            f'<span class="observed-value">Observed value: {observed_value}</span></td>'
            f'<td>{esc(row["clear_when"])}</td>'
            f'<td>{source_links(row["source_ids"])}{evidence_links(row.get("repo_evidence"))}</td>'
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table><caption>Decision-readiness blockers. '
        'Clearance rules are proposed project gates, not NFL rules. Unconfirmed values remain blank.</caption>'
        '<thead><tr><th>ID / requirement</th><th>Status</th><th>Blocking gate / observed state</th>'
        '<th>What would clear it</th><th>Official sources / repository evidence</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def questions_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            f'<tr id="{esc(row["id"])}">'
            f'<td><strong>{esc(row["id"])}</strong><br>{esc(row["question"])}</td>'
            f'<td>{esc(row["verified_answer"])}</td>'
            f'<td>{esc(row["missing_information"])}</td>'
            f'<td><strong>{esc(row["blocking_gate"])}</strong><br>{esc(row["clearance_number"])}</td>'
            f'<td>{status_cell(row["status"])}</td>'
            f'<td>{source_links(row["source_ids"])}{evidence_links(row.get("repo_evidence"))}'
            f'<p class="source-note">{esc(row["source_note"])}</p></td>'
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table><caption>Known, missing and decision-clearing information. '
        '“Verified answer” is limited to the linked page and dated scope.</caption>'
        '<thead><tr><th>Question</th><th>Verified answer</th><th>Still missing</th>'
        '<th>Gate / clearance number</th><th>Status</th><th>Sources and evidence</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def suggestions_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        options = "".join(
            f'<li><strong>{esc(option["label"])}</strong> — {esc(option["text"])}</li>'
            for option in row["options"]
        )
        body.append(
            f'<tr id="{esc(row["id"])}">'
            f'<td><strong>{esc(row["id"])}</strong><br><span class="priority">{esc(row["priority"])}</span></td>'
            f'<td><strong>{esc(row["title"])}</strong><p>{esc(row["problem"])}</p></td>'
            f'<td><details><summary>Compare options</summary><ul class="option-list">{options}</ul>'
            f'<div class="recommendation"><strong>Recommended path</strong><p>{esc(row["recommendation"])}</p></div>'
            f'<div class="recommendation"><strong>Decision gate</strong><p>{esc(row["decision_gate"])}</p></div></details></td>'
            f'<td>{esc(row["review_test"])}</td>'
            f'<td>{esc(row["what_would_change_our_mind"])}</td>'
            f'<td>{status_cell(row["decision_status"])}{source_links(row["source_ids"])}'
            f'<p class="source-note">{esc(row["source_note"])}</p></td>'
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table><caption>Each row is a proposal, not an approval. '
        'Options are reviewable; no data or shared model is changed by this register.</caption>'
        '<thead><tr><th>ID / priority</th><th>Suggestion / problem</th><th>Options and recommendation</th>'
        '<th>Review test</th><th>What would change our mind?</th><th>Decision state / official sources</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def flags_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for row in rows:
        body.append(
            f'<tr id="{esc(row["flag_id"])}">'
            f'<td><strong>{esc(row["flag_id"])}</strong><br>{status_cell(row["severity"])}</td>'
            f'<td><strong>{esc(row["area"])}</strong><p>{esc(row["finding"])}</p></td>'
            f'<td>{esc(row["impact"])}</td>'
            f'<td>{esc(row["action"])}</td>'
            f'<td>{status_cell(row["status"])}</td>'
            f'<td>{source_links(row["source_ids"])}{evidence_links(row.get("repo_evidence"))}</td>'
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table><caption>Unresolved and rechecked irregularities. '
        'A source link can establish a limitation or mismatch; it does not establish an unobserved value.</caption>'
        '<thead><tr><th>Flag</th><th>Finding</th><th>Decision impact</th><th>Next action</th>'
        '<th>Status</th><th>Source links / repository evidence</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def sources_table(rows: list[dict[str, Any]]) -> str:
    body = []
    for source in rows:
        body.append(
            f'<tr id="{esc(source["id"])}">'
            f'<td><strong>{esc(source["id"])}</strong><br>{esc(source["publisher_type"])}</td>'
            f'<td>{esc(source["publisher"])}<br><strong>{esc(source["title"])}</strong></td>'
            f'<td>{esc(source["observation"])}</td>'
            f'<td>{esc(source["use_limit"])}</td>'
            f'<td>{status_cell(source["verification_status"])}<br>Checked {esc(source["checked_on"])}</td>'
            f'<td>{source_links([source["id"]])}</td>'
            "</tr>"
        )
    return (
        '<div class="table-wrap"><table><caption>Official sources checked on 2026-11-17. '
        'The exact retrieval time was not exposed by the page retriever. “Official” describes the publisher, '
        'not permission to reuse its content.</caption>'
        '<thead><tr><th>Source ID / type</th><th>Publisher / page</th><th>What was observed</th>'
        '<th>Limit / permitted interpretation</th><th>Check status</th><th>Official link</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def verified_findings() -> str:
    rows = []
    for item in SUMMARY["verified_findings"]:
        rows.append(
            f'<tr><td><strong>{esc(item["title"])}</strong><p>{esc(item["detail"])}</p></td>'
            f'<td>{source_links(item["source_ids"])}</td></tr>'
        )
    return (
        '<div class="table-wrap"><table><caption>Observed facts are scoped to the linked page and check date.</caption>'
        '<thead><tr><th>Finding</th><th>Official source</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></div>'
    )


def build_index() -> str:
    body = f'''
<section class="hero-card">
  <div class="hero-copy">
    <p class="eyebrow">DECISION SUPPORT · NOT A BETTING BOARD</p>
    <h2>Separate verified facts<br><span>from model assumptions.</span></h2>
    <p>{esc(SUMMARY["lead"])}</p>
    <div class="hero-actions"><a class="button primary" href="suggestions.html">Review proposed paths <span aria-hidden="true">→</span></a>
    <a class="button secondary" href="questions.html">See what is still unknown</a></div>
  </div>
  <div class="hero-status"><span class="status-label">CURRENT DECISION</span>{badge("RESEARCH ONLY · KEY GATES BLOCKED", "danger")}
    <p>{esc(SUMMARY["decision"])}</p>
    <small>Source check date: 17 Nov 2026 · exact fetch time unavailable</small>
  </div>
</section>
<section class="notice warning"><strong>Do not treat this as live pricing or injury advice.</strong>
The official Week 12 injury URL checked here returned a Week 10 report. No operator odds, injury level, replacement depth or betting edge is inferred from a blank field.
<a href="flagged.html#F-01">Open the relevant flags →</a></section>
<section class="section-head"><div><p class="eyebrow">DECISION READINESS</p><h2>What blocks a defensible decision?</h2>
<p>Priority gates only. The prior desks' full line-by-line registers remain available below.</p></div>
<a class="inline-link" href="questions.html">Questions & answers →</a></section>
{readiness_table(READINESS)}
<section class="section-head"><div><p class="eyebrow">VERIFIED THIS REVIEW</p><h2>Fresh source checks</h2>
<p>Each statement is limited to what its linked official page actually showed.</p></div><a class="inline-link" href="sources.html">All sources →</a></section>
{verified_findings()}
<section class="link-grid">
  <a class="link-card" href="suggestions.html"><span>01 · REVIEW BEFORE BUILD</span><strong>Suggestions for review</strong><p>Options, tradeoffs, recommended path, tests and a two-sided “what would change our mind” field.</p></a>
  <a class="link-card" href="questions.html"><span>02 · KNOWN / MISSING</span><strong>Questions & answers</strong><p>Verified answers, unknowns, blocking gates and the official route to discover missing information.</p></a>
  <a class="link-card" href="flagged.html"><span>03 · AUDIT TRAIL</span><strong>Flagged for review</strong><p>Stale, inaccessible, restricted, source-mismatched or rechecked items are labeled rather than silently repaired.</p></a>
</section>
<section class="existing-registers">
  <p class="eyebrow">EXISTING REPOSITORY REGISTERS</p><h2>Full requirement tables from prior desks</h2>
  <p>This hub is additive and does not replace or reconcile other sessions' data. Review the dated source context before relying on a prior snapshot.</p>
  <ul>
    <li><a href="../nfl-desk-e46fb855/requirements.html">NFL desk e46fb855 — requirements register ↗</a> · <a href="../nfl-desk-e46fb855/index.html">overview ↗</a></li>
    <li><a href="../nfl-market-desk/readiness.html">NFL market desk — readiness register ↗</a> · <a href="../nfl-market-desk/index.html">overview ↗</a></li>
    <li><a href="../nfl-560ed315/readiness.html">NFL decision-readiness desk — gate / clearing-number table ↗</a></li>
  </ul>
</section>
<section class="existing-registers">
  <p class="eyebrow">EXISTING NFL ANALYSIS PAGES</p><h2>Model, results and availability</h2>
  <p>These are prior session outputs, not re-certified by this hub. Check the source date and flags on each page before using a value.</p>
  <div class="related-links">
    <p><strong>Pricing and outcomes:</strong> <a href="../nfl-desk-e46fb855/lines.html">own lines</a> · <a href="../nfl-desk-e46fb855/price-store.html">price store</a> · <a href="../nfl-desk-e46fb855/results.html">results</a></p>
    <p><strong>Signal and skill:</strong> <a href="../nfl-desk-e46fb855/strategies.html">strategies</a> · <a href="../nfl-desk-e46fb855/correlations.html">correlations</a> · <a href="../nfl-desk-e46fb855/leaderboard.html">leaderboard</a> · <a href="../nfl-desk-e46fb855/luck.html">removal-of-luck panel</a></p>
    <p><strong>Availability:</strong> <a href="../nfl-desk-e46fb855/injuries.html">injury report</a> · <a href="../nfl-desk-e46fb855/depth.html">depth</a> · <a href="../nfl-desk-e46fb855/matchup.html">matchup deficiency</a></p>
  </div>
</section>
<section class="method-callout"><h2>Scope and evidence rule</h2>
<p>Every unknown stays blank and flagged. Every displayed fact links to an official league, club, operator or agency source; repository links are labeled separately. Recommendations are proposals, not official NFL rules, approved bets or implemented changes.</p>
<p>Only one gamebook and two club depth pages were rechecked in this session; this is not a full 32-team or full-season audit.</p>
</section>
'''
    return page("NFL decision review", "Evidence-first decision-readiness, source audit, questions, reviewable suggestions and flags.", "index", body)


def build_questions() -> str:
    body = f'''
<section class="notice"><strong>Decision rule:</strong> An absent row is not “available”; a blank value is not zero. The table separates what was directly verified from what still requires a source.</section>
<section class="section-head"><div><p class="eyebrow">INFORMATION BEFORE ACTION</p><h2>Questions, known facts and missing evidence</h2>
<p>Use the clearance column as a proposed gate. It is not an NFL rule or a claimed result.</p></div>
<a class="download-link" href="data/questions.json">Download question data ↗</a></section>
{questions_table(QUESTIONS)}
<section class="method-callout"><h2>What this review did not do</h2>
<p>It did not create prices, estimate current injuries, infer snaps or depth ranks, calculate an ROI, assign probabilities to designations, or certify a strategy. Those fields remain blank until the listed gates are met.</p></section>
'''
    return page("Questions & answers", "A clear list of what is known, what is missing, what blocks a decision and how to discover the missing information.", "questions", body)


def build_suggestions() -> str:
    body = f'''
<section class="notice warning"><strong>Review docket only.</strong> Every item is awaiting review; no suggestion in this page changes existing data, models or shared navigation. The recommended path is a proposal, and its “what would change our mind” test is required before implementation.</section>
<section class="section-head"><div><p class="eyebrow">OPTIONS BEFORE IMPLEMENTATION</p><h2>Suggestions for review</h2>
<p>Open “Compare options” in each row. Automated capture is preferred; if a source or permission is missing, the system should fail closed rather than request manual data entry.</p></div>
<a class="download-link" href="data/suggestions.json">Download suggestion data ↗</a></section>
{suggestions_table(SUGGESTIONS)}
<section class="method-callout"><h2>Decision record expected</h2>
<p>Before implementation, record the selected option, the rejected alternatives, the owner, source/terms status, the acceptance test and the condition that would reverse the decision. Until then, the item remains “awaiting review.”</p></section>
'''
    return page("Suggestions for review", "Review alternatives and decision tests before implementing changes to the shared NFL site or model.", "suggestions", body)


def build_flags() -> str:
    body = f'''
<section class="notice warning"><strong>Flagged findings do not block publication.</strong> They block only the unsupported value or feature. The page keeps such values blank and explains what would resolve each flag.</section>
<section class="section-head"><div><p class="eyebrow">IRREGULARITIES / UNVERIFIED</p><h2>Flagged for review</h2>
<p>Includes source mismatches and items rechecked against the official page, with scope and date limits.</p></div>
<a class="download-link" href="data/flagged.json">Download flag data ↗</a></section>
{flags_table(FLAGS)}
'''
    return page("Flagged for review", "Stale sources, parsing problems, rights questions and citation gaps, each with an official link and next action.", "flagged", body)


def build_sources() -> str:
    body = f'''
<section class="notice"><strong>Source tier matters.</strong> NFL league, official club, sportsbook-operator and government sources are labeled separately. A source can be official yet stale, incomplete, restricted or irrelevant to a particular metric.</section>
<section class="section-head"><div><p class="eyebrow">PRIMARY SOURCE REGISTER</p><h2>Official pages checked</h2>
<p>Verification means the page was retrieved and its stated scope was checked on 17 Nov 2026. It does not imply a complete season capture or reuse permission.</p></div>
<a class="download-link" href="data/sources.json">Download source registry ↗</a></section>
{sources_table(SOURCES)}
<section class="method-callout"><h2>Exact timestamp limitation</h2><p>The page retriever exposed the date but not an exact UTC fetch time. This site therefore records the date only and does not fabricate a retrieval timestamp. Future scheduled captures should save the exact UTC time and raw content hash at ingestion.</p></section>
'''
    return page("Official sources", "Publisher, page, checked status, observed scope and limits for every source referenced by this review.", "sources", body)


def build_summary() -> str:
    blockers = "".join(f'<li>{esc(item)}</li>' for item in SUMMARY["blocking_gaps"])
    order = "".join(f'<li>{esc(item)}</li>' for item in SUMMARY["recommended_order"])
    body = f'''
<section class="summary-lead"><p class="eyebrow">EXECUTIVE SUMMARY · AS OF {esc(SUMMARY["as_of"])}</p>
<h2>{esc(SUMMARY["decision"])}</h2><p>{esc(SUMMARY["lead"])}</p></section>
<section class="section-head"><div><p class="eyebrow">WHAT WAS VERIFIED</p><h2>Fresh official-source findings</h2></div></section>
{verified_findings()}
<section class="two-column">
  <article class="panel"><p class="eyebrow">BLOCKERS</p><h2>Do not infer these values</h2><ul>{blockers}</ul></article>
  <article class="panel"><p class="eyebrow">RECOMMENDED ORDER</p><h2>Build the evidence chain first</h2><ol>{order}</ol></article>
</section>
<section class="method-callout"><h2>Scope note</h2><p>{esc(SUMMARY["scope_note"])}</p></section>
'''
    return page("Executive summary", "Important verified findings, blockers and recommended order for making NFL line-origin decisions defensible.", "summary", body)


def main() -> None:
    outputs = {
        "index.html": build_index(),
        "questions.html": build_questions(),
        "suggestions.html": build_suggestions(),
        "flagged.html": build_flags(),
        "sources.html": build_sources(),
        "summary.html": build_summary(),
    }
    for name, content in outputs.items():
        (ROOT / name).write_text(content, encoding="utf-8")
    print(f"Built {len(outputs)} review pages from {len(SOURCES)} source records, "
          f"{len(READINESS)} readiness rows, {len(QUESTIONS)} questions, "
          f"{len(SUGGESTIONS)} suggestions and {len(FLAGS)} flags.")


if __name__ == "__main__":
    main()

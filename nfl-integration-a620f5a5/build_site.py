"""Build the final NFL portfolio hub from this scope's small evidence registers."""
from __future__ import annotations

import csv
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("audit.html", "Audit"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("leaderboard.html", "Safe leaderboard"),
    ("sources.html", "Official sources"),
    ("flagged.html", "Flagged for Review"),
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / "data" / name).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


SOURCES = read_csv("sources.csv")
SOURCE_BY_URL = {row["url"]: row for row in SOURCES}
AUDIT = read_csv("audit.csv")
QUESTIONS = read_csv("questions.csv")
SUGGESTIONS = read_csv("suggestions.csv")


def source_links(raw: str, status: str = "") -> str:
    urls = [url.strip() for url in (raw or "").split("|") if url.strip()]
    if not urls:
        note = "UNVERIFIED — no qualifying official source identified"
        if "REPOSITORY_STATE_ONLY" in status or "REPOSITORY_STATE_ONLY" == status:
            note = "UNVERIFIED — repository-only finding; no NFL fact asserted"
        if "PROJECT_POLICY" in status:
            note = "Project-policy recommendation; no NFL fact asserted"
        return f'<span class="source-missing">{note}</span>'
    links = []
    for index, url in enumerate(urls, start=1):
        record = SOURCE_BY_URL.get(url)
        label = record["title"] if record else f"Official source {index}"
        links.append(
            f'<a class="source-link" href="{esc(url)}" target="_blank" '
            f'rel="noopener noreferrer">{esc(label)} ↗</a>'
        )
    return '<span class="source-list">' + "".join(links) + "</span>"


def evidence_links(raw: str) -> str:
    urls = [url.strip() for url in (raw or "").split("|") if url.strip()]
    if not urls:
        return '<span class="source-missing">No repository evidence path recorded</span>'
    links = []
    for index, url in enumerate(urls, start=1):
        label = url.rstrip("/").split("/")[-1] or f"Evidence {index}"
        links.append(f'<a class="evidence-link" href="{esc(url)}">{esc(label)} ↗</a>')
    return '<span class="source-list">' + "".join(links) + '</span>'


def status_badge(value: str) -> str:
    key = value.lower()
    css = "critical" if "critical" in key or "blocking" in key else "review" if "high" in key or "medium" in key else "neutral"
    return f'<span class="badge {css}">{esc(value)}</span>'


def page(title: str, current: str, content: str, description: str) -> str:
    nav = []
    for href, label in NAV:
        active = " active" if href == current else ""
        current_attr = ' aria-current="page"' if href == current else ""
        nav.append(f'<a class="nav-link{active}" href="{href}"{current_attr}>{esc(label)}</a>')
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="#10251f">
  <title>{esc(title)} · Own5 NFL Evidence Hub</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <a class="brand" href="index.html" aria-label="Own5 NFL evidence hub home"><span class="brand-mark">O5</span><span>OWN5 <small>NFL EVIDENCE HUB</small></span></a>
    <nav aria-label="Portfolio navigation">{''.join(nav)}</nav>
    <span class="review-date">INTEGRATION REVIEW · 17 NOV 2026</span>
  </header>
  <main id="main">
    <div class="page-title"><p class="eyebrow">NFL · FINAL INTEGRATION</p><h1>{esc(title)}</h1><p>{esc(description)}</p></div>
    {content}
  </main>
  <footer class="site-footer">
    <span>OWN5 · Independent research · Not affiliated with the NFL.</span>
    <span>Static analysis only. No live feed, wager placement or reward system.</span>
    <a href="../index.html">Original proposal workspace ↗</a>
  </footer>
</body>
</html>
'''


def table(headers: list[str], rows: list[list[str]], caption: str) -> str:
    head = "".join(f"<th scope=\"col\">{esc(item)}</th>" for item in headers)
    body = "".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    return f'''<div class="table-wrap"><table><caption>{esc(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'''


def audit_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    result = []
    for row in rows:
        result.append([
            status_badge(row["severity"]),
            f'<strong>{esc(row["area"])}</strong><p>{esc(row["observation"])}</p>',
            f'<p>{esc(row["decision_impact"])}</p><p class="muted"><strong>Clear when:</strong> {esc(row["clearance_rule"])}</p>',
            source_links(row["official_source_urls"], row["source_status"]),
            evidence_links(row["repository_evidence_urls"]),
        ])
    return result


def overview() -> str:
    cards = [
        ("Requirements & readiness", "Open the full row-by-row decision table and gate/clearance criteria.", "../nfl-market-desk/readiness.html", "Open 78-row readiness table"),
        ("Own lines & prices", "Side → total → moneyline, model outputs, price policy and blank market snapshots.", "../nfl-market-desk/lines.html", "Review origination"),
        ("Prices, results & model checks", "Opening and closing price policy, official results, standings reconciliation and held-out model accuracy.", "../nfl-market-desk/prices.html", "Review prices & results"),
        ("Availability & depth", "Official reports, roster/IR, shared and empty depth slots, replacement cascade and offense/defense matchup deficiencies.", "../nfl-market-desk/availability.html", "Review availability & depth"),
        ("Week 10 row-by-row audit", "Independent re-read, row-level injury comparison, transactions and claim checks.", "../nfl-audit-a699fc53/index.html", "Open official re-read"),
        ("Verified standings & slate", "Official 32-team standings, the Week 11 schedule, byes and linked source pages.", "../nfl-desk-e1d60f5d/index.html", "Open standings & schedule"),
        ("Strategies & gates", "Pre-registration files, validation policy, demotion rules and both sides of each strategy's falsifier.", "../nfl-market-desk/strategies.html", "Review strategies"),
        ("Correlations", "Official input tier, n and withheld pairs; prop-combo joint evidence remains a separate gate.", "../nfl-market-desk/correlations.html", "Review correlations"),
        ("Questions & missing information", "Known evidence, missing inputs, discovery routes and decision blockers.", "questions.html", "Open questions"),
        ("Suggestions for review", "Options, recommendation, reversal test and implementation status before data changes.", "suggestions.html", "Open suggestions"),
    ]
    card_html = "".join(
        f'<article class="desk-card"><span class="card-kicker">DECISION AREA</span><h3>{esc(title)}</h3><p>{esc(text)}</p><a href="{esc(href)}">{esc(action)} ↗</a></article>'
        for title, text, href, action in cards
    )
    top_rows = audit_rows(AUDIT[:6])
    content = f'''<section class="hero">
  <div class="hero-copy"><p class="eyebrow">OFFICIAL SOURCES · FAIL-CLOSED · SNAPSHOTS ARE DATED</p>
    <h2>Originate your own NFL lines.<br><span>Prove the signal before the stake.</span></h2>
    <p>One entry point to the existing requirements, results, price store, injury and depth evidence, strategy gates, questions, suggestions and review flags.</p>
    <div class="actions"><a class="button primary" href="../nfl-market-desk/readiness.html">Decision readiness ↗</a><a class="button secondary" href="https://www.nfl.com/schedules/2026/by-week/week-11" target="_blank" rel="noopener noreferrer">Official live schedule ↗</a></div>
  </div>
  <aside class="hero-state"><span class="state-pill">PAPER / NOT QUALIFIED</span><h3>No live betting decision is supported.</h3><p>Verified operator open/close prices are missing; historical leaderboard figures are quarantined; official availability is not yet replayable across all clubs.</p><a href="flagged.html">See the blocking evidence ↗</a></aside>
</section>
<section class="notice warning"><strong>Currency, not a live feed.</strong><p>This integration read official pages on 2026-11-17. The market desk's model/price/availability snapshots are dated through 2026-11-15; the separate standings/schedule desk was read on 2026-11-17. Links can change; this hub does not preserve a fresh byte-for-byte copy of the pages it checked.</p></section>
<section class="section-heading"><div><p class="eyebrow">START HERE</p><h2>Choose the decision area</h2></div><a href="executive-summary.html">Read executive summary ↗</a></section>
<section class="desk-grid">{card_html}</section>
<section class="schedule-panel">
  <div><p class="eyebrow">SCHEDULE CONTEXT</p><h2>Dated announcement beside the live schedule</h2><p>The league media release is dated May 8, 2026 and announces a May 14 schedule release. Use the linked weekly page for the live fixture list; use the individual Game Center for the venue of each fixture.</p></div>
  <div class="schedule-links"><a href="https://media.nfl.com/news-and-releases/2026-nfl-schedule-powered-by-aws-to-be-released-thursday--may-14" target="_blank" rel="noopener noreferrer">Dated NFL announcement ↗</a><a href="https://www.nfl.com/schedules/2026/by-week/week-11" target="_blank" rel="noopener noreferrer">Live Week 11 schedule ↗</a><a href="https://www.nfl.com/games/colts-at-texans-2026-reg-11" target="_blank" rel="noopener noreferrer">Example: fixture Game Center ↗</a></div>
</section>
<section class="section-heading"><div><p class="eyebrow">INTEGRATION AUDIT</p><h2>What blocks a decision today</h2><p class="section-subtitle">The rows below are repository findings with official context where available. Missing sources remain blank and flagged.</p></div><a href="audit.html">Open full audit ↗</a></section>
{table(["Severity", "Finding", "Decision impact & clearance", "Official source", "Repository evidence"], top_rows, "Selected current integration findings")}
<section class="callout"><div><p class="eyebrow">LEADERBOARD POLICY</p><h2>Signal and staking stay separate.</h2><p>This hub publishes no historical score or ranking. Qualification must be prospective and pre-registered; staking results are a separate escrow after a permitted price source exists.</p></div><a class="button primary" href="leaderboard.html">Open safe leaderboard ↗</a></section>
<section class="latest-links"><a href="../nfl-desk-e46fb855/index.html">Dated official-capture desk ↗</a><a href="../nfl-market-desk/index.html">Requirements and origination desk ↗</a><a href="../nfl-capture-a991e3fb/index.html">Week 10 injury recapture ↗</a><a href="../nfl-audit-a699fc53/index.html">Week 10 official re-read ↗</a><a href="../nfl-desk-e1d60f5d/index.html">Verified standings and schedule ↗</a><a href="flagged.html">Flagged for Review ↗</a></section>'''
    return page("NFL Line Origination & Decision Hub", "index.html", content, "Repository-wide entry point for NFL line research, dated official sources and decision blockers. No predictions or wagers are represented as qualified.")


def audit_page(flagged_only: bool = False) -> str:
    selected = AUDIT
    rows = audit_rows(selected)
    intro = (
        "All unresolved items and severity levels are shown here. Missing official evidence is explicitly marked; no unsupported value is filled in."
        if flagged_only else
        "Cross-desk discrepancies and blocking evidence found during the integration review. This is a repository audit, not a new NFL fact feed."
    )
    content = f'''<section class="notice warning"><strong>Scope note.</strong><p>{esc(intro)} Link to the official source is provided where one supports the observation; repository-only discrepancies are labeled as such.</p></section>
{table(["Severity", "Finding", "Impact & clearance rule", "Official source", "Repository evidence"], rows, "Integration audit and flagged findings")}
<section class="section-footer-links"><a href="../nfl-market-desk/review.html">Underlying market-desk flags ↗</a><a href="../nfl-desk-e46fb855/flagged.html">Dated-desk flags ↗</a><a href="../nfl-capture-a991e3fb/index.html">Week 10 capture and diff ↗</a></section>'''
    title = "Flagged for Review" if flagged_only else "Cross-desk audit"
    current = "flagged.html" if flagged_only else "audit.html"
    return page(title, current, content, "Source-linked irregularities and blockers found in the final integration review.")


def questions_page() -> str:
    rows = []
    for item in QUESTIONS:
        rows.append([
            f'<strong>{esc(item["question"])}</strong>',
            f'<p><strong>Have:</strong> {esc(item["known_from_verified_sources"])}</p><p><strong>Missing:</strong> {esc(item["missing_information"])}</p>',
            f'<p>{esc(item["answer_needed_before_decision"])}</p><p class="muted"><strong>Clear with:</strong> {esc(item["clearing_evidence"])}</p>',
            source_links(item["official_source_urls"], item["source_status"]),
            evidence_links(item["repository_evidence_urls"]),
        ])
    content = f'''<section class="notice"><strong>Decision questions, not assumptions.</strong><p>Answers are limited to what the linked official sources and repository captures establish. A blank source cell means no qualifying official source was identified.</p></section>
{table(["Question", "Known / missing", "What must be answered before deciding", "Official source", "Repository evidence"], rows, "Questions and information gaps before any decision")}
<section class="section-footer-links"><a href="../nfl-market-desk/questions.html">Full market-desk question register ↗</a><a href="../nfl-desk-e46fb855/questions.html">Dated-desk question register ↗</a></section>'''
    return page("Questions & Missing Information", "questions.html", content, "Questions, available evidence, missing information, official discovery routes and clearance criteria.")


def suggestions_page() -> str:
    cards = []
    for item in SUGGESTIONS:
        cards.append(f'''<article class="suggestion-card">
  <div class="suggestion-head"><span class="card-kicker">{esc(item["suggestion_id"])}</span>{status_badge(item["priority"])}</div>
  <h2>{esc(item["topic"])}</h2>
  <p><strong>Options:</strong> {esc(item["options"])}</p>
  <p><strong>Recommended path:</strong> {esc(item["recommended_path"])}</p>
  <p><strong>What would change the recommendation:</strong> {esc(item["what_would_change_the_recommendation"])}</p>
  <div class="links-row"><span><strong>Official references:</strong> {source_links(item["official_source_urls"], item["source_status"])}</span><span><strong>Repository evidence:</strong> {evidence_links(item["related_evidence_urls"])}</span></div>
  <p class="status-line">{status_badge(item["decision_status"])}</p>
</article>''')
    content = f'''<section class="notice"><strong>Review before data or model changes.</strong><p>These are reversible paths, not new NFL facts. The recommended path is explicit; each proposal states what evidence would change it. Requirements already requested by the owner (including this hub and the dated schedule links) are implemented; blocked data ingestion remains blocked by evidence or terms.</p></section>
<section class="suggestion-grid">{"".join(cards)}</section>
<section class="section-footer-links"><a href="../nfl-market-desk/suggestions.html">Full 19-item suggestions register ↗</a></section>'''
    return page("Suggestions & Review Paths", "suggestions.html", content, "Decision-review suggestions with options, recommendations, reversal tests, official references and implementation status.")


def sources_page() -> str:
    rows = []
    for item in SOURCES:
        rows.append([
            f'<strong>{esc(item["title"])}</strong><small>{esc(item["publisher"])}</small>',
            f'<p>{esc(item["verified_observation"])}</p><p class="muted"><strong>Limit:</strong> {esc(item["scope_limit"])}</p>',
            esc(item["checked_on"]),
            source_links(item["url"], "VERIFIED_OFFICIAL_CONTEXT"),
        ])
    content = f'''<section class="notice warning"><strong>Read date is not an archive.</strong><p>These official pages were read on the date shown, but this hub did not store raw page bytes or hashes for this read. The older desk manifests contain their own captured-file hashes. Do not assume a live page still shows the same content.</p></section>
{table(["Official source", "What was checked / limit", "Read on", "Link"], rows, "Official NFL and club sources checked for the integration")}
<section class="section-footer-links"><a href="../nfl-desk-e46fb855/sources.html">Dated desk source register and capture manifest ↗</a><a href="../nfl-market-desk/sources.html">Market desk source register ↗</a></section>'''
    return page("Official Sources & Source Limits", "sources.html", content, "Official NFL, NFL Media, NFL Support and club sources checked for this integration.")


def leaderboard_page() -> str:
    divisions = [
        ("Singles", "Prospective pre-registration; benchmark-relative proper-score skill, game-cluster uncertainty and multiplicity adjustment before ranking.", "PAPER · NO RANK", "https://www.nfl.com/standings/league/2026/REG", "Outcomes source only; no performance values published here."),
        ("Game parlays", "Directly validated joint probability and the selected operator's settlement/void rules; never multiply marginal probabilities as a substitute.", "LOCKED · JOINT EVIDENCE MISSING", "", "No qualifying joint-price source is recorded."),
        ("Same-game parlays", "Direct joint model with calibration, uncertainty and market-specific settlement rules.", "LOCKED · JOINT EVIDENCE MISSING", "", "No qualifying joint-price source is recorded."),
        ("Player-prop combos", "Authorized official participation data plus a directly validated joint probability and the selected operator's settlement rules.", "LOCKED · SOURCE TERMS / JOINT MODEL", "https://support.nfl.com/hc/en-us/articles/35869678028180-Game-Books", "Game Book reuse needs permission; no player-level rows are copied here."),
    ]
    rows = []
    for division, qualification, status, url, note_text in divisions:
        rows.append([
            f'<strong>{esc(division)}</strong>',
            f'<p>{esc(qualification)}</p><p class="muted">{esc(note_text)}</p>',
            status_badge(status),
            source_links(url, "VERIFIED_OFFICIAL_CONTEXT" if url else "UNVERIFIED_NO_OFFICIAL_PRICE_SOURCE"),
        ])
    content = f'''<section class="hero slim"><div class="hero-copy"><p class="eyebrow">TWO-STAGE COMPETITION · PROSPECTIVE ONLY</p><h2>No strategy is ranked here.</h2><p>This leaderboard intentionally contains no historical hit rate, Brier score, ROI, CLV, reward, or performance number. Existing legacy numerical boards are quarantined on the Flagged for Review page.</p></div><aside class="hero-state"><span class="state-pill">RANKING LOCKED</span><h3>Signal first. Staking second.</h3><p>Qualification is based on prospective, benchmark-relative signal skill. Staking and CLV are separate and stay blank until a permitted price source exists.</p></aside></section>
{table(["Division", "Qualification gate", "Current status", "Official source"], rows, "Score-free qualification board by bet class")}
<section class="callout"><div><p class="eyebrow">REGISTERED HYPOTHESES</p><h2>Freeze rules before the evaluation window.</h2><p>Review the rule text, registration hashes, thresholds, two-sided falsifiers and demotion gates. Do not treat pre-registration as proof of skill.</p></div><a class="button primary" href="../nfl-market-desk/strategies.html">Open strategy register ↗</a></section>
<section class="section-footer-links"><a href="../nfl-market-desk/gates.html">Validation gates ↗</a><a href="flagged.html">Review quarantined legacy board paths ↗</a></section>'''
    return page("Safe Leaderboard", "leaderboard.html", content, "Prospective-only, score-free status board. Backtests are not ranked or shown as performance evidence.")


def markdown_inline(text: str) -> str:
    escaped = html.escape(text, quote=False)

    def link(match: re.Match[str]) -> str:
        label, target = match.groups()
        return f'<a href="{html.escape(target, quote=True)}">{label}</a>'

    escaped = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped


def markdown_body(source: str) -> str:
    output: list[str] = []
    paragraph: list[str] = []
    list_tag: str | None = None
    in_code = False
    skipped_title = False

    def flush_paragraph() -> None:
        if paragraph:
            output.append("<p>" + markdown_inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_tag
        if list_tag:
            output.append(f"</{list_tag}>")
            list_tag = None

    for line in source.splitlines():
        if line.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                output.append("</code></pre>")
            else:
                output.append("<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            output.append(html.escape(line))
            continue
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            close_list()
            continue
        if stripped.startswith("# ") and not skipped_title:
            skipped_title = True
            flush_paragraph()
            close_list()
            continue
        heading = re.match(r"^(#{2,4})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = min(len(heading.group(1)), 3)
            output.append(f"<h{level}>{markdown_inline(heading.group(2))}</h{level}>")
            continue
        if stripped == "---":
            flush_paragraph()
            close_list()
            output.append("<hr>")
            continue
        unordered = re.match(r"^-\s+(.+)$", stripped)
        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if unordered or ordered:
            flush_paragraph()
            tag = "ul" if unordered else "ol"
            if list_tag != tag:
                close_list()
                output.append(f"<{tag} class=\"tight\">")
                list_tag = tag
            item = unordered.group(1) if unordered else ordered.group(1)
            output.append("<li>" + markdown_inline(item) + "</li>")
            continue
        close_list()
        paragraph.append(stripped)
    flush_paragraph()
    close_list()
    return "\n".join(output)


def executive_summary_page() -> str:
    markdown = (ROOT / "EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
    content = '<article class="summary-copy">' + markdown_body(markdown) + "</article>"
    return page("Executive Summary", "executive-summary.html", content, "Evidence-first summary of the NFL line-origination portfolio, decision blockers and official-source limits.")


def main() -> None:
    pages = {
        "index.html": overview(),
        "executive-summary.html": executive_summary_page(),
        "audit.html": audit_page(),
        "questions.html": questions_page(),
        "suggestions.html": suggestions_page(),
        "leaderboard.html": leaderboard_page(),
        "sources.html": sources_page(),
        "flagged.html": audit_page(flagged_only=True),
    }
    for name, content in pages.items():
        (ROOT / name).write_text(content, encoding="utf-8")
    print(f"Built {len(pages)} static integration pages from {len(SOURCES)} official source records, {len(AUDIT)} audit rows, {len(QUESTIONS)} questions and {len(SUGGESTIONS)} suggestions.")


if __name__ == "__main__":
    main()

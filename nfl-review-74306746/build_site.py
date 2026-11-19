#!/usr/bin/env python3
"""Build the isolated NFL cross-desk review site (Python standard library only)."""
from __future__ import annotations

import html
import json
from pathlib import Path
from urllib.parse import quote

SITE = Path(__file__).resolve().parent
REPO = SITE.parent
DATA = REPO / "research" / "nfl-review-74306746"
OUT = SITE

PAGES = {
    "index.html": ("Overview", "index"),
    "readiness.html": ("Decision readiness", "readiness"),
    "sources.html": ("Official-source coverage", "sources"),
    "questions.html": ("Questions & answers", "questions"),
    "suggestions.html": ("Suggestions", "suggestions"),
    "flagged.html": ("Flagged for review", "flagged"),
}


def load_json(name: str):
    with (DATA / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def evidence_href(path: str) -> str:
    """Stable GitHub permalink to the reviewed base snapshot."""
    commit = load_json("summary.json")["evidence_snapshot"]
    suffix = quote(path.strip("/"), safe="/")
    kind = "tree" if path.endswith("/") else "blob"
    return f"https://github.com/sassnarep3-star/Own5/{kind}/{commit}/{suffix}"


def official_link(url: str, label: str, extra_class: str = "") -> str:
    classes = "official-source" + (f" {extra_class}" if extra_class else "")
    return (
        f'<a class="{esc(classes)}" href="{esc(url)}" target="_blank" '
        f'rel="noopener noreferrer">{esc(label or url)}</a>'
    )


def primary_link(url: str, label: str) -> str:
    return (
        f'<a class="primary-source" href="{esc(url)}" target="_blank" '
        f'rel="noopener noreferrer">{esc(label or url)}</a>'
    )


def evidence_links(items: list[dict]) -> str:
    if not items:
        return '<span class="source-gap" data-flag="missing-repository-evidence">Repository evidence not located — flagged</span>'
    links = []
    for item in items:
        href = evidence_href(item["path"])
        links.append(
            f'<a class="repo-source" href="{esc(href)}" target="_blank" '
            f'rel="noopener noreferrer">{esc(item.get("label", item["path"]))}</a>'
        )
    return '<span class="evidence-links">' + " · ".join(links) + "</span>"


def official_sources(item: dict) -> str:
    links = item.get("official_sources") or []
    if not links:
        return '<span class="source-gap" data-flag="no-official-source">No official source for this claim — flagged</span>'
    rendered = []
    for source in links:
        kind = source.get("kind", "")
        if "Operator" in kind or "Aggregator" in kind:
            rendered.append(primary_link(source["url"], source["label"]))
        else:
            rendered.append(official_link(source["url"], source["label"], kind))
    return '<span class="source-links">' + " · ".join(rendered) + "</span>"


def badge(value: str) -> str:
    v = value.upper()
    if any(x in v for x in ("BLOCKED", "CONFLICT", "NOT CURRENT", "NOT VERIFIED")):
        style = "red"
    elif any(x in v for x in ("PARTIAL", "OPEN", "UNKNOWN", "REVIEW", "UNRESOLVED")):
        style = "amber"
    elif any(x in v for x in ("PASS", "MET", "VERIFIED")):
        style = "green"
    else:
        style = "slate"
    return f'<span class="badge {style}">{esc(value)}</span>'


def page_shell(active: str, title: str, description: str, body: str) -> str:
    nav = "".join(
        f'<a href="{esc(href)}" class="{"on" if key == active else ""}">{esc(label)}</a>'
        for href, (label, key) in PAGES.items()
    )
    summary = load_json("summary.json")
    review_date = esc(summary["review_as_of"])
    freshness_notice = esc(summary["freshness_notice"])
    evidence_snapshot = esc(summary["evidence_snapshot"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#102238">
  <meta name="description" content="{esc(description)}">
  <title>{esc(title)} · Own5 NFL Cross-Desk Review</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <div class="shell">
    <header class="topbar">
      <a class="brand" href="index.html" aria-label="Own5 NFL cross-desk review home">
        <span class="mark">O<span>5</span></span>
        <span><b>OWN5</b><small>NFL CROSS-DESK REVIEW</small></span>
      </a>
      <div class="asof"><span class="dot"></span> Repository review · {review_date}</div>
    </header>
    <nav class="nav" aria-label="Review navigation">{nav}</nav>
    <div class="freshness" role="note"><b>Snapshot &amp; source limits.</b> {freshness_notice}</div>
    <main id="main">
      <div class="pagehead"><p class="eyebrow">Independent · additive · read-only</p><h1>{esc(title)}</h1><p class="lede">{esc(description)}</p></div>
      {body.strip()}
    </main>
    <footer class="footer">
      <span>Evidence snapshot <code>{evidence_snapshot}</code></span>
      <span><a href="../research/nfl-review-74306746/README.md">Review method &amp; registers</a> · <a href="../research/nfl-review-74306746/verification-log.md">Verification log</a></span>
    </footer>
  </div>
</body>
</html>
"""


def render_index() -> str:
    summary = load_json("summary.json")
    cards = []
    for item in summary["categories"]:
        refs = " · ".join(
            f'<a class="repo-source" href="{esc(evidence_href(path))}" target="_blank" rel="noopener noreferrer">{esc(Path(path).name)}</a>'
            for path in item.get("evidence", [])[:2]
        )
        cards.append(
            f'<article class="category-card"><div class="card-top"><span class="eyebrow">{esc(item["title"])}</span>{badge(item["status"])}</div>'
            f'<p>{esc(item["description"])}</p><div class="card-foot">{official_link(item["official_url"], item["official_label"])}'
            f'<span class="dotsep">·</span>{refs}</div></article>'
        )
    registers = "".join(
        f'<a class="register-link" href="{esc(item["url"])}"><b>{esc(item["name"])}</b><span>{esc(item["note"])}</span></a>'
        for item in summary["canonical_registers"]
    )
    body = f"""
<section class="hero">
  <div class="hero-copy"><p class="eyebrow">Decision posture · PAPER ONLY</p><h2>{esc(summary["decision"])}</h2><p>{esc(summary["lead"])}</p></div>
  <div class="hero-aside"><span class="eyebrow">Review status</span><strong>No fresh external verification</strong><p>This report audits what is in the repository and reruns selected local checks. It does not establish that historical source pages are still current or that captured values are externally authentic.</p><a class="arrow" href="../research/nfl-review-74306746/verification-log.md">Read the verification log <span aria-hidden="true">→</span></a></div>
</section>
<section class="section"><div class="section-head"><div><p class="eyebrow">Decision dashboard</p><h2>Evidence by category</h2></div><p>Each card links to an official source reference and to the reviewed repository evidence. The source page itself was not re-read here.</p></div>
  <div class="category-grid">{''.join(cards)}</div>
</section>
<section class="section"><div class="section-head"><div><p class="eyebrow">Blocking view</p><h2>Start with readiness</h2></div><a class="text-link" href="readiness.html">Open the full review table <span aria-hidden="true">→</span></a></div>
  <div class="callout danger"><b>Highest-priority conflict</b><p>The engine's close-labelled FanDuel rows and the market desk's blank operator open/close store cannot both support a single “verified price” story without a scope and source reconciliation. Keep price-dependent conclusions blocked.</p><div class="chips">{official_link('https://www.nfl.com/schedules/2026/by-week/week-10', 'NFL Week 10 schedule (fixture context only)')} · {evidence_links([{"path":"nfl-engine-39086ec8/data/price_snapshots.csv","label":"Engine price register"},{"path":"nfl-market-desk/data/price_snapshots.csv","label":"Market price register"}])}</div></div>
</section>
<section class="section"><div class="section-head"><div><p class="eyebrow">Canonical owner registers</p><h2>Keep the ledgers separate</h2></div><p>These registers differ in count, schema and scope. No combined completion percentage is asserted by this review.</p></div><div class="register-grid">{registers}</div></section>
<section class="section compact"><div class="section-head"><div><p class="eyebrow">Next actions</p><h2>Review before changing anything</h2></div><p>Cross-desk findings are handed to their owners. This review changes no other desk's data, status or navigation.</p></div><div class="link-row"><a class="button" href="suggestions.html">Review suggestions</a><a class="button secondary" href="questions.html">Questions &amp; answers</a><a class="button secondary" href="flagged.html">Flagged items</a><a class="button secondary" href="sources.html">Source coverage</a></div></section>
<section class="section footnote"><h2>Scope boundary</h2><p>All counts and statuses on this site describe repository files at the pinned evidence snapshot. They are not new NFL facts. The existing desks remain canonical for their own registers; this independent review does not substitute for a source-owner correction, a legal review, or the final integrated-data check.</p><p><a href="../research/nfl-review-74306746/executive-summary.md">Download the executive summary</a> · <a href="../research/nfl-review-74306746/source-coverage.json">Source coverage register (JSON)</a> · <a href="../research/nfl-review-74306746/readiness.json">Readiness register (JSON)</a></p></section>
"""
    return page_shell("index", summary["title"], "A read-only evidence review of existing NFL line-originator desks, their sources, blockers and decision readiness.", body)


def render_sources() -> str:
    sources = load_json("source-coverage.json")
    rows = []
    for item in sources:
        primary = ""
        if item.get("primary_url"):
            primary = "<br>" + primary_link(item["primary_url"], item["primary_label"])
        rows.append(
            "<tr>"
            f'<td><b>{esc(item["area"])}</b><br><small>{esc(item["publisher"])} · {esc(item["source_class"])}</small></td>'
            f'<td>{esc(item["recorded_capture"])}<br><small>{esc(item["repository_coverage"])}</small></td>'
            f'<td>{esc(item["review_limit"])}</td>'
            f'<td>{official_link(item["official_url"], item["official_label"])}{primary}<br><small>{evidence_links(item["evidence"])}</small></td>'
            "</tr>"
        )
    body = f"""
<div class="callout neutral"><b>What “official source” means here</b><p>The NFL or club URL is linked as a source reference. `Historical reference`, `not re-fetched`, and `not read` are intentional: this review did not make an external request. For prices, a direct sportsbook page is an operator source, not an NFL source; it is shown separately and remains unverified.</p></div>
<div class="table-wrap"><table><thead><tr><th>Source area</th><th>What the repository records</th><th>Limit in this review</th><th>Official reference &amp; repository evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<section class="section compact"><h2>Coverage rules</h2><ul class="checks"><li>Every NFL fact used in the readiness summary is linked to its recorded official source.</li><li>Repository-derived counts are labeled as such; the source link is context, not independent confirmation.</li><li>Unsupported values remain blank/unknown and are listed on <a href="flagged.html">Flagged for Review</a>.</li><li>Market references from aggregators are not treated as operator opens/closes.</li><li>Third-party snap aggregates are separately tiered and cannot substitute for the missing target-week Game Book extraction.</li></ul></section>
<p class="download"><a href="../research/nfl-review-74306746/source-coverage.json">Download the source-coverage register</a></p>
"""
    return page_shell("sources", "Official-source coverage", "Source links, recorded capture scope and the limits of what this review independently verified.", body)


def render_readiness() -> str:
    items = load_json("readiness.json")
    rows = []
    for item in items:
        rows.append(
            "<tr>"
            f'<td><b>{esc(item["area"])}</b><br>{badge(item["status"])}</td>'
            f'<td>{esc(item["requirement"])}</td>'
            f'<td>{esc(item["observed"])}</td>'
            f'<td><b>{esc(item["blocking_gate"])}</b><br><small>Clear when: {esc(item["clearing_number"])}</small></td>'
            f'<td>{official_link(item["official_url"], item["official_label"])}<br><small>{evidence_links(item["evidence"])}</small><br><small class="source-note">{esc(item["source_note"])}</small></td>'
            "</tr>"
        )
    body = f"""
<div class="callout amber"><b>Review-level summary, not a merged requirements register.</b><p>The full 73-row command-desk register and separate 78-row market-desk register remain authoritative for their own scopes. The table below summarizes blockers found in this cross-desk audit; links go to the official source references and the repository evidence.</p></div>
<div class="table-wrap"><table class="readiness"><thead><tr><th>Brief area / review status</th><th>Requirement</th><th>Observed repository state</th><th>Blocking gate &amp; clearing number</th><th>Sources &amp; evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="download"><a href="../nfl-command-desk/requirements.html">Full command-desk requirements register ↗</a> · <a href="../nfl-market-desk/readiness.html">Separate market-desk readiness register ↗</a> · <a href="../research/nfl-review-74306746/readiness.json">Download this review table (JSON)</a></p>
"""
    return page_shell("readiness", "Decision readiness", "Compact gate-by-gate view of the line-origination brief, with current repository evidence, clearing conditions and source limits.", body)


def render_questions() -> str:
    items = load_json("questions.json")
    cards = []
    for item in items:
        cards.append(
            f'<article class="record-card"><div class="card-top"><span class="record-id">{esc(item["id"])}</span>{badge(item["answer_status"])}</div>'
            f'<h2>{esc(item["question"])}</h2><p>{esc(item["answer"])}</p>'
            f'<div class="detail-grid"><div><h3>Missing</h3><p>{esc(item["missing_information"])}</p></div><div><h3>Route to answer</h3><p>{esc(item["route"])}</p></div><div><h3>What it blocks</h3><p>{esc(item["blocks"])}</p></div></div>'
            f'<div class="card-foot">{official_link(item["official_url"], item["official_label"])}<span class="dotsep">·</span>{evidence_links(item["evidence"])}</div>'
            f'<p class="source-note">{esc(item["source_note"])}</p></article>'
        )
    body = '<div class="record-list">' + "".join(cards) + '</div><p class="download"><a href="../research/nfl-review-74306746/questions.json">Download questions &amp; answers (JSON)</a></p>'
    return page_shell("questions", "Questions & answers", "What repository evidence can answer, what remains unknown, and how to resolve each blocker without inferring a value.", body)


def render_suggestions() -> str:
    items = load_json("suggestions.json")
    cards = []
    for item in items:
        options = "".join(
            f'<li><b>{esc(option["label"])}</b><p>{esc(option["text"])}</p></li>'
            for option in item["options"]
        )
        cards.append(
            f'<article class="record-card"><div class="card-top"><span class="record-id">{esc(item["id"])} · {esc(item["priority"])}</span>{badge(item["status"])}</div>'
            f'<h2>{esc(item["title"])}</h2><p>{esc(item["problem"])}</p>'
            f'<h3>Options for the owner</h3><ul class="options">{options}</ul>'
            f'<div class="recommendation"><b>Review recommendation</b><p>{esc(item["recommendation"])}</p><small>{esc(item["decision"])}</small></div>'
            f'<div class="detail-grid two"><div><h3>What would change the call in favor</h3><p>{esc(item["would_change_our_mind_up"])}</p></div><div><h3>What would change the call against</h3><p>{esc(item["would_change_our_mind_down"])}</p></div></div>'
            f'<div class="card-foot">{official_link(item["official_url"], item["official_label"])}<span class="dotsep">·</span>{evidence_links(item["evidence"])}</div>'
        )
    body = '<div class="record-list">' + "".join(cards) + '</div><p class="download"><a href="../research/nfl-review-74306746/suggestions.json">Download reviewable suggestions (JSON)</a></p>'
    return page_shell("suggestions", "Suggestions for review", "Owner-scoped options, recommendations and falsification conditions. Nothing here has been implemented in another desk.", body)


def render_flagged() -> str:
    items = load_json("flagged.json")
    cards = []
    for item in items:
        cards.append(
            f'<article class="record-card flag-card"><div class="card-top"><span class="record-id">{esc(item["id"])} · {esc(item["severity"])}</span>{badge(item["status"])}</div>'
            f'<h2>{esc(item["title"])}</h2><p>{esc(item["finding"])}</p>'
            f'<div class="detail-grid two"><div><h3>Decision impact</h3><p>{esc(item["impact"])}</p></div><div><h3>Requested next action</h3><p>{esc(item["next_action"])}</p></div></div>'
            f'<div class="card-foot"><span><b>Source references (official links plus any labeled operator claim):</b> {official_sources(item)}</span><span><b>Repository evidence:</b> {evidence_links(item["evidence"])}</span></div>'
            f'<p class="source-note">Repository observation only; this review did not independently verify the external source.</p></article>'
        )
    body = f"""
<div class="callout danger"><b>Open flags are not silently resolved.</b><p>Findings below are evidence discrepancies, stale-source risks or scope limits. The recommended actions are routed to the owning desks; this review edits none of those files.</p></div>
<div class="record-list">{''.join(cards)}</div>
<p class="download"><a href="../research/nfl-review-74306746/flagged.json">Download flagged register (JSON)</a> · <a href="../research/nfl-review-74306746/verification-log.md">See the limits of the checks</a></p>
"""
    return page_shell("flagged", "Flagged for review", "Open discrepancies and unknowns. An internal check passing does not clear an external-source or ownership question.", body)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(parents=True, exist_ok=True)
    renderers = {
        "index.html": render_index,
        "readiness.html": render_readiness,
        "sources.html": render_sources,
        "questions.html": render_questions,
        "suggestions.html": render_suggestions,
        "flagged.html": render_flagged,
    }
    for filename, renderer in renderers.items():
        (OUT / filename).write_text(renderer(), encoding="utf-8", newline="\n")
    print(f"built {len(renderers)} pages in {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()

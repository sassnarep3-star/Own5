#!/usr/bin/env python3
"""Deterministically render the f5ce620e audit-only NFL review pages."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUTPUT_FILES = ("index.html", "audit.html", "questions.html", "suggestions.html", "flagged.html", "sources.html", "data/manifest.json")
MANIFEST_ITEMS = (
    ("raw/official_reads_2026-11-18.md", "source-response summary; not an HTTP archive"),
    ("data/venues_week11.csv", "local transcription of 13 official Game Center venue labels"),
    ("data/results_increment_week10.csv", "one-game official result delta; not a complete feed"),
)


def read_json(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def read_csv(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def anchor_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")


def local_evidence_links(items: list[dict[str, str]]) -> str:
    if not items:
        return "<span class=\"muted\">No local artifact link supplied.</span>"
    links = []
    for item in items:
        path = item["path"]
        links.append(
            f'<a href="{esc(path)}"><span>{esc(item["label"])}</span>'
            f' <span class="code-path">({esc(path)})</span></a>'
        )
    return "".join(links)


def load_context() -> dict[str, Any]:
    meta = read_json("data/review_meta.json")
    sources = read_json("data/sources.json")
    findings = read_json("data/audit_findings.json")
    questions = read_json("data/questions.json")
    suggestions = read_json("data/suggestions.json")
    source_by_id = {item["id"]: item for item in sources}
    finding_by_id = {item["id"]: item for item in findings}
    return {
        "meta": meta,
        "sources": sources,
        "source_by_id": source_by_id,
        "findings": findings,
        "finding_by_id": finding_by_id,
        "questions": questions,
        "suggestions": suggestions,
    }


def source_chips(source_ids: list[str], context: dict[str, Any]) -> str:
    if not source_ids:
        return '<span class="status blocking">UNVERIFIED · no source record supplied</span>'
    links = []
    source_by_id = context["source_by_id"]
    for source_id in source_ids:
        item = source_by_id.get(source_id)
        if not item:
            links.append(f'<span class="status blocking">UNVERIFIED · missing {esc(source_id)}</span>')
            continue
        klass = item["source_class"]
        links.append(
            f'<a href="{esc(item["url"])}" target="_blank" rel="noopener noreferrer">'
            f'<strong>{esc(source_id)}</strong> · {esc(item["publisher"])}'
            f'<span class="muted"> — {esc(klass)}</span> ↗</a>'
        )
    return "".join(links)


def related_findings(ids: list[str], context: dict[str, Any]) -> str:
    if not ids:
        return '<span class="muted">No related finding supplied.</span>'
    links = []
    finding_by_id = context["finding_by_id"]
    for finding_id in ids:
        item = finding_by_id.get(finding_id)
        label = f'{finding_id} · {item["area"]}' if item else f'{finding_id} · missing finding'
        links.append(f'<a href="audit.html#finding-{anchor_slug(finding_id)}">{esc(label)}</a>')
    return "".join(links)


def nav_for(meta: dict[str, Any], active: str) -> str:
    links = []
    for item in meta["page_nav"]:
        current = ' aria-current="page"' if item["path"] == active else ""
        links.append(f'<a href="{esc(item["path"])}"{current}>{esc(item["label"])}</a>')
    return "".join(links)


def page(title: str, active: str, body: str, context: dict[str, Any]) -> str:
    meta = context["meta"]
    rendered = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Independent, source-linked NFL decision-readiness audit; unresolved claims remain visibly flagged.">
  <title>{esc(title)} · Own5</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="site-header">
  <div class="header-inner">
    <div class="brandline"><span class="brand-mark" aria-hidden="true">O5</span><span>{esc(meta['short_title'])}</span><span class="tag">AUDIT ONLY</span></div>
    <h1>{esc(title)}</h1>
    <p>{esc(meta['as_of'])} · {esc(meta['primary_capture_window'])}</p>
    <nav class="site-nav" aria-label="Review pages">{nav_for(meta, active)}</nav>
  </div>
</header>
<div class="page-shell">
  <p class="breadcrumb">Own5 / independent review / <span class="mono">f5ce620e</span></p>
  <main>
{body}
  </main>
  <footer class="site-footer">
    <strong>Scope:</strong> {esc(meta['site_notice'])}
    <br>Local hashes cover the listed local review files only; they do not authenticate the live source server. Suggestions are proposals and are not implemented.
  </footer>
</div>
</body>
</html>
'''
    return "\n".join(line.rstrip() for line in rendered.splitlines()) + "\n"


def severity_class(severity: str) -> str:
    value = severity.lower()
    if value == "blocking":
        return "severity-blocking"
    if value == "high":
        return "severity-high"
    if value == "medium":
        return "severity-medium"
    return "severity-low"


def status_class(status: str, flagged: bool) -> str:
    if not flagged:
        return "resolved"
    if "blocking" in status.lower() or "blocked" in status.lower():
        return "blocking"
    return ""


def finding_card(item: dict[str, Any], context: dict[str, Any], compact: bool = False) -> str:
    resolved = not item["flagged"]
    body_class = " resolved" if resolved else ""
    details = "" if compact else f'''
      <details>
        <summary>Limits, decision effect and clearance gate</summary>
        <p><strong>Not verified:</strong> {esc(item['not_verified'])}</p>
        <p><strong>Decision effect:</strong> {esc(item['decision_effect'])}</p>
        <p><strong>Gate:</strong> {esc(item['gate'])}</p>
        <p><strong>Clearance criterion:</strong> {esc(item['clearance_number'])}</p>
      </details>'''
    evidence = local_evidence_links(item.get("repo_evidence", []))
    sources = source_chips(item.get("source_ids", []), context)
    return f'''
<article class="finding-card{body_class}" id="finding-{anchor_slug(item['id'])}">
  <h3><span>{esc(item['id'])}</span> {esc(item['area'])}</h3>
  <div class="finding-meta"><span class="pill {severity_class(item['severity'])}">{esc(item['severity'])}</span><span class="status {status_class(item['status'], item['flagged'])}">{esc(item['status'])}</span></div>
  <p><strong>Claim checked:</strong> {esc(item['claim_checked'])}</p>
  <p><strong>Observed:</strong> {esc(item['observed'])}</p>
  {details}
  <p class="small"><strong>Repository evidence:</strong></p>
  <div class="evidence-links">{evidence}</div>
  <p class="small"><strong>Source links (source classes shown):</strong></p>
  <div class="source-links">{sources}</div>
</article>'''


def make_manifest() -> dict[str, Any]:
    entries = []
    for relative, role in MANIFEST_ITEMS:
        path = ROOT / relative
        payload = path.read_bytes()
        entries.append({
            "path": relative,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "role": role,
        })
    return {
        "scope": "Local review artifacts only. These hashes do not authenticate source-server responses.",
        "entries": entries,
    }


def render_index(context: dict[str, Any]) -> str:
    meta = context["meta"]
    findings = context["findings"]
    sources = context["sources"]
    flagged = [item for item in findings if item["flagged"]]
    venues = read_csv("data/venues_week11.csv")
    results = read_csv("data/results_increment_week10.csv")
    high_impact = ["A01", "A02", "A03", "A04", "A06", "A07", "A11", "A13", "A14", "A16", "A20"]
    by_id = context["finding_by_id"]
    cards = []
    for finding_id in high_impact:
        item = by_id[finding_id]
        cards.append(f'''
<article class="card">
  <div class="kicker">{esc(item['id'])} · {esc(item['severity'])}</div>
  <h3><a href="audit.html#finding-{anchor_slug(item['id'])}">{esc(item['area'])}</a></h3>
  <p>{esc(item['observed'])}</p>
  <div class="source-links">{source_chips(item['source_ids'], context)}</div>
</article>''')
    body = f'''
<p class="disclaimer"><strong>Decision status: NOT CLEARED.</strong> This is an independent evidence audit, not a betting recommendation or model certification. No model, data policy, capture workflow, shared navigation or prior-desk file was changed.</p>
<p class="lede">This dossier checks whether high-impact NFL claims are current, source-backed and decision-ready. It separates what an official page says from what an old capture, a model output, or a third-party dataset can establish.</p>
<div class="cards" aria-label="Review counts">
  <div class="card"><div class="value">{len(findings)}</div><div class="label">line-level audit findings</div></div>
  <div class="card"><div class="value">{len(flagged)}</div><div class="label">items still flagged or blocked</div></div>
  <div class="card"><div class="value">{len(sources)}</div><div class="label">registered source reads / routes</div></div>
  <div class="card"><div class="value">{len(venues)} + {len(results)}</div><div class="label">Week 11 venue rows + Week 10 result delta</div></div>
</div>
<div class="two-column">
  <section>
    <span class="kicker">Executive readout</span>
    <h2>What changed the decision-readiness picture</h2>
    <ul class="callout-list">
      <li><strong>Availability:</strong> the league Week 11 injury URL still returned Week 10 at capture time, but a Texans club article had Week 11 practice tables for two clubs. The earlier blanket “not published” claim is stale for those clubs; full-league coverage is not verified.</li>
      <li><strong>Clock conflict:</strong> saved injury reads span 25 hours 13 minutes, while prior prose says 49 hours and 1 hour 13 minutes. The source pair and text need reconciliation.</li>
      <li><strong>Prices:</strong> “no price data exists in the repo” is too broad. Third-party historical line fields exist, and a first-party operator page is a current source route; neither is an approved timestamped open/close series for this project.</li>
      <li><strong>Results:</strong> NFL.com shows Chargers 23, Ravens 20, Final. This dossier records a one-game delta only; it does not rebuild the full results feed or post-update standings.</li>
      <li><strong>Readiness metadata:</strong> the prior model coefficient appears as both -0.52 and -0.46; REQ-04 is marked MET while market fields are blank and the residual is undefined.</li>
      <li><strong>Competition:</strong> reviewed P-01/P-02/P-03 registrations each have 13 forecasts and zero settlements; no skill claim or leaderboard reward is justified.</li>
    </ul>
    <p><a href="flagged.html">Open the Flagged for Review queue →</a> · <a href="questions.html">Decision questions →</a></p>
  </section>
  <aside>
    <div class="note alert">
      <h3>Do not use as a cleared model</h3>
      <p>Market terms/location, full injury coverage, reserve pagination, Game Book reuse rights, a full result reconciliation, and consistent model metadata remain unresolved.</p>
      <p><a href="audit.html">Read all findings →</a></p>
    </div>
    <div class="note" style="margin-top:12px">
      <h3>Review scope boundary</h3>
      <p>{esc(meta['scope'])}</p>
      <p>The root index/README and prior desks are read-only in this session; a portfolio navigation link is deferred to integration.</p>
    </div>
  </aside>
</div>
<h2>High-impact findings with evidence links</h2>
<div class="grid-2">{''.join(cards)}</div>
<h2>What this review did not establish</h2>
<div class="grid-2">
  <div class="note"><h3>Source and policy limits</h3><p>No 32-club Week 11 injury census, legally approved odds feed, Georgia-specific quote, rights approval for Game Book rows, or permission-compatible full live-page archive was established.</p><p><a href="sources.html">Source register and local artifact hashes →</a></p></div>
  <div class="note"><h3>Model and performance limits</h3><p>No historical feed rebuild, coefficient refit, settled forecast score, backtest promotion, ROI claim, or validated joint probability was produced. Strategy and combo decisions remain separate, reviewable proposals.</p><p><a href="suggestions.html">Read suggestions before implementation →</a></p></div>
</div>
'''
    return page("Independent NFL decision-readiness review", "index.html", body, context)


def render_audit(context: dict[str, Any]) -> str:
    findings = context["findings"]
    body = f'''
<p class="lede">Each finding states the claim checked, what the recorded evidence supports, what remains unverified, the decision effect and a numeric/explicit clearance condition. Source classes are shown on every linked source.</p>
<p class="note">There are <strong>{len(findings)} findings</strong>; <strong>{sum(1 for item in findings if item['flagged'])}</strong> remain flagged. A “verified” venue/result transcription is limited to what its cited page states and does not imply a full-feed or feature validation.</p>
{''.join(finding_card(item, context) for item in findings)}
'''
    return page("Audit findings", "audit.html", body, context)


def render_questions(context: dict[str, Any]) -> str:
    cards = []
    for item in context["questions"]:
        cards.append(f'''
<article class="finding-card" id="question-{anchor_slug(item['id'])}">
  <h3><span>{esc(item['id'])}</span> {esc(item['question'])}</h3>
  <div class="finding-meta"><span class="pill {severity_class('High' if item['priority'] == 'P0' else 'Medium')}">{esc(item['priority'])}</span><span class="status">{esc(item['answer_status'])}</span></div>
  <p><strong>Decision owner:</strong> {esc(item['owner_decision'])}</p>
  <p><strong>Known evidence:</strong> {esc(item['known_evidence'])}</p>
  <p><strong>Missing:</strong> {esc(item['missing_evidence'])}</p>
  <p><strong>Cheapest route:</strong> {esc(item['cheapest_route'])}</p>
  <p><strong>Why it matters:</strong> {esc(item['why_it_matters'])}</p>
  <p class="small"><strong>Related findings:</strong></p><div class="evidence-links">{related_findings(item['related_findings'], context)}</div>
  <p class="small"><strong>Source links:</strong></p><div class="source-links">{source_chips(item['source_ids'], context)}</div>
</article>''')
    body = f'''
<p class="disclaimer"><strong>Questions are not policy decisions.</strong> Where ownership or source policy is required, it is stated explicitly. No answer is invented to close a gate.</p>
<p class="lede">The queue prioritizes decisions that block trustworthy line origination and transparent strategy evaluation. Links lead to the findings and sources for manual review.</p>
{''.join(cards)}
'''
    return page("Decision questions", "questions.html", body, context)


def render_suggestions(context: dict[str, Any]) -> str:
    proposals = []
    for item in context["suggestions"]:
        options = []
        for option in item["options"]:
            options.append(f'''
<div class="option"><strong>{esc(option['label'])}</strong>
  <p><strong>Upside:</strong> {esc(option['upside'])}</p>
  <p><strong>Trade-off:</strong> {esc(option['downside'])}</p>
</div>''')
        mind = item["what_would_change_our_mind_if"]
        criteria = list(mind.items())
        criterion_cards = []
        for index, (direction, evidence) in enumerate(criteria):
            side_class = "support" if index == 0 else "reconsider"
            direction_label = direction.replace("_", " ").replace("toward ", "Toward ").capitalize()
            criterion_cards.append(
                f'<div class="side-box {side_class}"><strong>{esc(direction_label)}</strong>'
                f'<p>{esc(evidence)}</p></div>'
            )
        proposals.append(f'''
<article class="proposal" id="suggestion-{anchor_slug(item['id'])}">
  <div class="proposal-head">
    <div class="finding-meta"><span class="pill {severity_class('High' if item['priority'] == 'P0' else 'Medium')}">{esc(item['priority'])}</span><span class="status info">{esc(item['implementation_state'])}</span></div>
    <h2>{esc(item['id'])} · {esc(item['title'])}</h2>
  </div>
  <div class="proposal-body">
    <h3>Options considered</h3>
    <div class="option-grid">{''.join(options)}</div>
    <div class="decision"><strong>Recommendation:</strong> {esc(item['recommendation'])}</div>
    <p><strong>Why this is the current recommendation:</strong> {esc(item['what_supports_recommendation'])}</p>
    <div class="side-by-side">{''.join(criterion_cards)}</div>
    <p class="small"><strong>Related findings:</strong></p><div class="evidence-links">{related_findings(item['related_findings'], context)}</div>
    <p class="small"><strong>Source links:</strong></p><div class="source-links">{source_chips(item['source_ids'], context)}</div>
  </div>
</article>''')
    body = f'''
<p class="disclaimer"><strong>Review first — none of these suggestions is implemented.</strong> Each entry includes at least two options, its trade-offs, a recommendation, and evidence that would move the decision in either direction. User policy/model choices remain open.</p>
<p class="lede">Suggestions are scoped to evidence, validation and review gates. They do not change the shared root navigation, prior model, league data or price policy.</p>
{''.join(proposals)}
'''
    return page("Suggestions · review first", "suggestions.html", body, context)


def render_flagged(context: dict[str, Any]) -> str:
    findings = [item for item in context["findings"] if item["flagged"]]
    body = f'''
<p class="disclaimer"><strong>Flagged for Review.</strong> These items are unresolved, partial, stale, blocked, or a correction with a still-open source/policy gate. They are not silently converted into facts.</p>
<p class="lede">{len(findings)} items require a source refresh, reconciliation, rights decision, or explicit policy choice before the related claim or feature is considered ready.</p>
{''.join(finding_card(item, context, compact=True) for item in findings)}
'''
    return page("Flagged for Review", "flagged.html", body, context)


def render_source_row(item: dict[str, Any]) -> str:
    source_id = item["id"]
    return f'''
<tr id="source-{anchor_slug(source_id)}">
  <td><strong>{esc(source_id)}</strong></td>
  <td>{esc(item['publisher'])}<br><span class="muted">{esc(item['source_class'])}</span></td>
  <td><a href="{esc(item['url'])}" target="_blank" rel="noopener noreferrer">{esc(item['observed_label'])} ↗</a></td>
  <td>{esc(item['read_window_utc'])}</td>
  <td>{esc(item['observation'])}<br><strong>Limit:</strong> {esc(item['scope_limit'])}</td>
  <td><a href="{esc(item['raw_ref'])}">{esc(item['raw_ref'])}</a><br><span class="status info">{esc(item['status'])}</span></td>
</tr>'''


def render_venues_table(rows: list[dict[str, str]]) -> str:
    body_rows = []
    for row in rows:
        body_rows.append(f'''
<tr>
  <td class="mono">{esc(row['game_id'])}</td>
  <td>{esc(row['kickoff_date'])} · {esc(row['away'])} at {esc(row['home'])}</td>
  <td>{esc(row['location'])}</td>
  <td>{esc(row['stadium'])}</td>
  <td><a href="{esc(row['venue_source_url'])}" target="_blank" rel="noopener noreferrer">Official Game Center ↗</a><br><span class="muted">{esc(row['captured_window_utc'])}</span></td>
</tr>''')
    return f'''<div class="table-wrap"><table class="table-narrow"><thead><tr><th>Game</th><th>Fixture</th><th>Location as published</th><th>Stadium as published</th><th>Official source / read window</th></tr></thead><tbody>{''.join(body_rows)}</tbody></table></div>'''


def render_results_table(rows: list[dict[str, str]]) -> str:
    body_rows = []
    for row in rows:
        body_rows.append(f'''
<tr>
  <td class="mono">{esc(row['game_id'])}</td>
  <td>Week {esc(row['week'])} · {esc(row['kickoff_date'])}</td>
  <td>{esc(row['away'])} {esc(row['away_score'])} — {esc(row['home'])} {esc(row['home_score'])}<br><span class="status resolved">{esc(row['status'])}</span></td>
  <td><a href="{esc(row['result_source_url'])}" target="_blank" rel="noopener noreferrer">Official Game Center ↗</a><br><a href="{esc(row['independent_schedule_source_url'])}" target="_blank" rel="noopener noreferrer">Official Week 10 schedule ↗</a></td>
  <td>{esc(row['captured_window_utc'])}<br>{esc(row['verification_note'])}</td>
</tr>''')
    return f'''<div class="table-wrap"><table class="table-narrow"><thead><tr><th>Game</th><th>Week/date</th><th>Result</th><th>Independent official sources</th><th>Read window / scope</th></tr></thead><tbody>{''.join(body_rows)}</tbody></table></div>'''


def render_manifest_table(entries: list[dict[str, Any]]) -> str:
    rows = []
    for item in entries:
        rows.append(f'''
<tr>
  <td><a href="{esc(item['path'])}">{esc(item['path'])}</a></td>
  <td class="mono">{item['bytes']}</td>
  <td class="mono">{esc(item['sha256'])}</td>
  <td>{esc(item['role'])}<br><span class="status info">Local content only · not source-server authentication</span></td>
</tr>''')
    return f'''<div class="table-wrap"><table class="table-narrow"><thead><tr><th>Local artifact</th><th>Bytes</th><th>SHA-256</th><th>Hash scope</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>'''


def render_sources(context: dict[str, Any], manifest: dict[str, Any]) -> str:
    sources = context["sources"]
    venues = read_csv("data/venues_week11.csv")
    results = read_csv("data/results_increment_week10.csv")
    src_rows = "".join(render_source_row(item) for item in sources)
    body = f'''
<p class="lede">This register distinguishes official league/club pages, official operator pages and third-party datasets. Every source row links to the read route and its local note/reference; a source's presence does not imply that it is complete, licensed for reuse, or a current market quote.</p>
<div class="note alert"><strong>Capture limitation:</strong> the notes are not full HTTP response archives. The hashes below authenticate only the local note/CSV bytes at the time of manifest generation, not the live pages or source-server responses.</div>
<h2>Source register ({len(sources)} records)</h2>
<div class="table-wrap"><table class="table-wide"><thead><tr><th>ID</th><th>Publisher / source class</th><th>Read route / observed label</th><th>Read window</th><th>Observation and scope limit</th><th>Local reference / status</th></tr></thead><tbody>{src_rows}</tbody></table></div>
<h2>Week 11 venue labels ({len(venues)} rows)</h2>
<p>Exact location and stadium labels from each official NFL Game Center. No roof, surface, weather or venue-specific model adjustment is inferred. The official Texans stadium page independently corroborates the `RELIANT STADIUM` Game Center label as of its 2026-11-18 read.</p>
{render_venues_table(venues)}
<p class="small"><a href="data/venues_week11.csv">Download the CSV transcription</a> · <a href="{esc(context['source_by_id']['SRC-15']['url'])}" target="_blank" rel="noopener noreferrer">Houston Texans stadium-name confirmation ↗</a></p>
<h2>Week 10 result delta ({len(results)} row)</h2>
<p>This is a single source-linked result update. It does not rebuild the historical feed or certify a 32-club standings reconciliation.</p>
{render_results_table(results)}
<p class="small"><a href="data/results_increment_week10.csv">Download the result-delta CSV</a></p>
<h2>Local artifact manifest</h2>
<p>The manifest is deterministic and generated from the three listed local artifacts. It intentionally does not include itself, source JSON, HTML pages or original live responses; it makes no claim that external pages were captured byte-for-byte.</p>
{render_manifest_table(manifest['entries'])}
<p class="small"><a href="data/manifest.json">View manifest.json</a> · <a href="raw/official_reads_2026-11-18.md">Read the source notes</a> · <a href="data/README.md">Data guide</a></p>
'''
    return page("Sources & tables", "sources.html", body, context)


def render_outputs() -> dict[str, str]:
    context = load_context()
    manifest = make_manifest()
    return {
        "index.html": render_index(context),
        "audit.html": render_audit(context),
        "questions.html": render_questions(context),
        "suggestions.html": render_suggestions(context),
        "flagged.html": render_flagged(context),
        "sources.html": render_sources(context, manifest),
        "data/manifest.json": json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated files differ; do not write")
    args = parser.parse_args(argv)
    try:
        outputs = render_outputs()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"build: input error: {exc}", file=sys.stderr)
        return 2
    mismatches = []
    for relative, content in outputs.items():
        path = ROOT / relative
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                mismatches.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    if args.check:
        if mismatches:
            print("build: generated artifacts differ or are missing: " + ", ".join(mismatches), file=sys.stderr)
            return 1
        print(f"build: PASS — {len(outputs)} deterministic outputs match")
    else:
        print(f"build: wrote {len(outputs)} deterministic outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

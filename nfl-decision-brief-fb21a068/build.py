#!/usr/bin/env python3
"""Render the evidence-first decision brief from its reviewed CSV register."""
from __future__ import annotations

import csv
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV = ROOT / "data" / "decision_register.csv"
OUTPUT = ROOT / "index.html"


def e(value: str) -> str:
    return html.escape(value, quote=True)


def table(rows: list[dict[str, str]], kind: str) -> str:
    if kind == "Question":
        headers = ["ID / status", "Verified finding", "Question / missing information", "Minimum evidence to clear", "Recommendation", "What would change our mind", "Sources"]
        fields = ["id", "verified_finding", "unresolved_question", "minimum_evidence_to_clear", "recommendation", "what_would_change_our_mind"]
    else:
        headers = ["ID / priority", "Area / verified context", "Proposed improvement", "Evidence needed", "Recommendation", "What would change our mind", "Sources"]
        fields = ["id", "area", "verified_finding", "unresolved_question", "minimum_evidence_to_clear", "recommendation", "what_would_change_our_mind"]
    out = ['<div class="table-scroll"><table><thead><tr>']
    out.extend(f"<th scope=\"col\">{e(x)}</th>" for x in headers)
    out.append("</tr></thead><tbody>")
    for row in rows:
        label = row["status"] if kind == "Question" else row["priority"]
        out.append('<tr>')
        out.append(f'<th scope="row"><span class="id">{e(row["id"])}</span><span class="pill">{e(label)}</span></th>')
        if kind == "Question":
            out.append(f'<td>{e(row[fields[1]])}<p class="area">{e(row["area"])}</p></td>')
            out.append(f'<td>{e(row[fields[2]])}</td>')
            out.append(f'<td>{e(row[fields[3]])}</td>')
            out.append(f'<td>{e(row[fields[4]])}</td>')
            out.append(f'<td>{e(row[fields[5]])}</td>')
        else:
            out.append(f'<td><strong>{e(row[fields[1]])}</strong><p>{e(row[fields[2]])}</p></td>')
            out.append(f'<td>{e(row[fields[3]])}</td>')
            out.append(f'<td>{e(row[fields[4]])}</td>')
            out.append(f'<td>{e(row[fields[5]])}</td>')
            out.append(f'<td>{e(row[fields[6]])}</td>')
        out.append('<td class="sources">')
        out.append(f'<a href="{e(row["official_source_url"])}" target="_blank" rel="noopener">Official source ↗</a>')
        out.append(f'<a href="{e(row["repo_evidence_url"])}">Repo evidence ↗</a>')
        out.append('</td></tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)


def main() -> None:
    with CSV.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    questions = [r for r in rows if r["kind"] == "Question"]
    suggestions = [r for r in rows if r["kind"] == "Suggestion"]
    html_doc = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NFL Decision Brief | Own5</title>
<meta name="description" content="Prioritized NFL line-origination decisions: verified facts, unknowns, gates, and reviewable suggestions.">
<link rel="stylesheet" href="style.css"></head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="masthead"><div class="brand"><span class="mark">O5</span><div><b>OWN5 / NFL</b><small>DECISION BRIEF · REVIEW COPY</small></div></div>
<nav aria-label="Page navigation"><a href="#summary">Executive brief</a><a href="#questions">Questions & gates</a><a href="#path">Suggested path</a><a href="#sources">Sources</a></nav></header>
<main id="main">
<section class="hero" id="summary"><div class="eyebrow">Evidence review · 19 November 2026 UTC</div><h1>What must be known before a line is trusted?</h1>
<p class="lede">A concise decision layer over the existing NFL desks. It separates what official pages currently say from what the model still cannot establish, and puts the next evidence-gathering steps in dependency order.</p>
<div class="callout"><span class="callout-label">Recommended decision now</span><strong>Keep the project in paper / shadow mode. Start with singles. Do not rank parlays, use unverified availability as a feature, publish market residuals from an uncleared source, or award cash until the corresponding gates pass.</strong><p>This is a conservative project-governance recommendation, not a claim that any strategy has or has not made money. Luck cannot be removed from outcomes; only measured uncertainty and prospective replication can limit false confidence.</p></div>
<div class="snapshot-grid">
<article><span class="tag good">UPDATED SOURCE</span><h2>Week 11 injury page is now live</h2><p>The official NFL page is titled “Week 11 of the 2026 Season.” The previous repo read on Nov 18 reported that the Week 11 URL served Week 10. That earlier read remains valid as a historical observation; it is not today's state.</p><a href="https://www.nfl.com/injuries/league/2026/reg11">Open official Week 11 injury report ↗</a></article>
<article><span class="tag good">FIXTURE CONTEXT</span><h2>Houston venue naming is date-sensitive</h2><p>The NFL Game Center names Reliant Stadium. The Texans' official stadium page says that name returned in August 2026 after the NRG Stadium period. For this fixture, keep the exact published text and cite the game centre; do not apply that name to earlier seasons.</p><a href="https://www.houstontexans.com/stadium/">Open official Texans stadium page ↗</a></article>
<article><span class="tag warn">NOT CLEARED</span><h2>Visible odds are not a price-data policy</h2><p>An operator market page is publicly viewable, but this review did not establish rights to retain, use in backtests, or republish those quotes, nor an immutable opening/closing feed. The market and residual fields remain blank until policy is cleared.</p><a href="https://sportsbook.draftkings.com/leagues/football/nfl">Open official operator market page ↗</a></article>
</div>
<aside class="integrity-alert" aria-label="Flagged repository integrity issue"><div class="eyebrow">Flagged for review · repository verification</div><h2>Registration-hash check is currently failing</h2><p>The existing NFL Command Desk verifier returned <b>47 PASS / 3 FAIL</b> on this checkout. All three failures are its V11 pre-registration checks: the published registration SHA <code>e7282e35dbf9afb0c1b364a152b9431dc71b64af</code> is not present in the local Git object database, so the referenced commit cannot be independently confirmed as an ancestor here. Until repaired, do not rely on this desk's claim that those strategies are commit-hash pre-registered.</p><a href="../nfl-command-desk/verify.py">Inspect verifier ↗</a><a href="../nfl-command-desk/data/preregistration.csv">Inspect registration rows ↗</a></aside>
<div class="meta-line"><span><b>Scope:</b> questions and suggestions in this companion, not an integration-wide verification.</span><span><b>Source read:</b> official page fetches on 2026-11-19 UTC; exact fetch clock time and raw response hashes are unavailable here.</span></div>
</section>
<section class="section" id="questions"><div class="section-head"><div><div class="eyebrow">Decision-readiness</div><h2>Questions and information gaps</h2><p>Answers are deliberately bounded to what the linked official page establishes. “Updated” does not mean a requirement is cleared.</p></div><span class="counter">{len(questions)} priority questions</span></div>
{table(questions, "Question")}
</section>
<section class="section path" id="path"><div class="section-head"><div><div class="eyebrow">Suggestion review</div><h2>Proposed implementation order</h2><p>Each proposal is pending, source-linked, and includes a condition that would change the recommendation. The order minimizes leakage and prevents variance from masquerading as skill.</p></div><span class="counter">{len(suggestions)} proposals</span></div>
{table(suggestions, "Suggestion")}
</section>
<section class="section" id="decision"><div class="section-head"><div><div class="eyebrow">Go / no-go sequence</div><h2>Gates that must be passed before scale-up</h2></div></div>
<ol class="sequence"><li><b>Define data rights and retention.</b> Identify allowed sources, markets, jurisdiction, historical coverage, open/close definition and timestamp policy. Until then: no market residual / CLV claim.</li><li><b>Capture immutable information before kickoff.</b> Preserve dated official reports and source hashes, roster / IR changes, actual inactive and starter evidence. Unknown remains unknown; no jersey-order or salary shortcut.</li><li><b>Freeze a singles-only model and evaluation protocol.</b> Save each probability with its inputs and registration hash before the event. Use chronological train/validation/holdout windows and explicit random/favorite controls.</li><li><b>Qualify signal with proper scores and uncertainty.</b> Keep the signal score distinct from staking and realized ROI; account for game clustering and the number of tested strategies. Backtests never qualify a public leaderboard.</li><li><b>Escrow prospective evidence, then consider products separately.</b> Require prospective replication and an available permitted close-price benchmark before live consideration. Parlays / same-game / prop combinations remain behind direct joint-probability and operator settlement-rule gates.</li></ol>
<p class="caution"><b>Safety / scope:</b> This page is analysis and project governance, not betting advice, legal advice, a sportsbook, or a declaration that an operator feed is licensed. No live wagers, financial transactions, or cash rewards are enabled here.</p>
</section>
<section class="section sources" id="sources"><div class="section-head"><div><div class="eyebrow">Manual verification</div><h2>Official sources read</h2><p>Click through to inspect the official material. Source links support only the stated scope; operator material is not an NFL endorsement.</p></div></div>
<ul><li><a href="https://www.nfl.com/injuries/league/2026/reg11">NFL — Week 11 2026 injury report</a> <span>Current page title and report surface.</span></li>
<li><a href="https://www.nfl.com/schedules/2026/by-week/week-11">NFL — Week 11 schedule</a> <span>Fixture slate and dates.</span></li>
<li><a href="https://www.nfl.com/games/colts-at-texans-2026-reg-11">NFL — Colts at Texans Game Center</a> <span>Fixture date, location and published stadium name.</span></li>
<li><a href="https://www.houstontexans.com/stadium/">Houston Texans — official stadium information</a> <span>Reliant / NRG naming history and current venue text.</span></li>
<li><a href="https://media.nfl.com/football-information/2026/news/2026-nfl-schedule-announced">NFL Football Communications — dated 2026 schedule announcement</a> <span>League-announced schedule context.</span></li>
<li><a href="https://www.nfl.com/standings/league/2026/REG">NFL — 2026 regular-season standings</a> <span>Official standings/results reference.</span></li>
<li><a href="https://sportsbook.draftkings.com/leagues/football/nfl">DraftKings — NFL markets</a> <span>Operator page; not permission to archive or redistribute.</span></li>
<li><a href="https://www.fanduel.com/fanduel-sportsbook-house-rules-on">FanDuel — Ontario sportsbook house rules</a> <span>Jurisdiction-specific rule text; does not settle other operators or jurisdictions.</span></li>
<li><a href="https://www.fanduel.com/sports-betting-guide/what-is-a-parlay-bet">FanDuel — parlay explainer</a> <span>Operator's product description; not evidence of joint model skill.</span></li>
<li><a href="https://www.igamingontario.ca/en/player/player-support">iGaming Ontario — player support</a> <span>Ontario regulator service context only; not a legal conclusion for this project.</span></li></ul>
<p class="footnote">Repository references in the tables are links to the existing desk's CSV evidence. Their snapshots are dated and may be stale; this companion does not refresh or overwrite them. Source content can change after the read date.</p>
</section>
<footer><a href="../index.html">Own5 root</a> · <a href="../nfl-command-desk/index.html">NFL Command Desk</a> · <a href="../nfl-command-desk/flagged.html">Flagged for Review</a> · <a href="EXECUTIVE_SUMMARY.md">Executive summary</a><span>Built from <code>data/decision_register.csv</code></span></footer>
</main></body></html>'''
    OUTPUT.write_text(html_doc, encoding="utf-8")


if __name__ == "__main__":
    main()

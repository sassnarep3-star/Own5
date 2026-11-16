"""Renders the e46fb855 desk site from the CSVs engine.py writes.

Design rules that the verifier depends on:
  * the LAST cell of every body row is a source cell: either a link to an
    official page or an explicit UNVERIFIED badge (class="blank");
  * nothing is rendered that is not in a CSV or in content.py.
"""
from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SESSION = "e46fb855"

SOURCE_KEYS = (
    "source_url", "model_source_url", "market_source_url", "depth_source_url",
    "injury_source_url", "offence_source_url", "defence_source_url",
    "venue_source_url", "game_url", "url", "source",
)

NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("requirements.html", "Requirements"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("results.html", "Results feed"),
    ("slate.html", "Week 11 slate"),
    ("lines.html", "Originated lines"),
    ("price-store.html", "Price store"),
    ("depth.html", "Depth &amp; replacements"),
    ("injuries.html", "Injuries"),
    ("matchup.html", "Matchup matrix"),
    ("strategies.html", "Strategies"),
    ("gates.html", "Gates"),
    ("leaderboard.html", "Leaderboard"),
    ("correlations.html", "Correlations"),
    ("luck.html", "Luck panel"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("audit.html", "Repo audit"),
    ("verification.html", "Verification"),
]

LABELS = {
    "game_id": "Game", "season": "Season", "week": "Week", "date": "Date",
    "kickoff_date": "Kickoff date", "kickoff_et": "Kickoff (ET)", "away": "Away",
    "home": "Home", "away_score": "Away pts", "home_score": "Home pts",
    "home_margin": "Home margin", "total_points": "Total pts", "result": "Result",
    "neutral_site": "Neutral", "status": "Status", "verification": "Verified by",
    "verification_note": "Verification note", "team": "Team", "club": "Club",
    "w": "W", "l": "L", "t": "T", "pct": "PCT", "pf": "PF", "pa": "PA", "net": "NET",
    "gp": "GP", "pf_per_game": "PF/G", "pa_per_game": "PA/G", "net_per_game": "NET/G",
    "win_pct": "Win%", "official_w": "Official W", "official_l": "Official L",
    "official_t": "Official T", "official_pf": "Official PF", "official_pa": "Official PA",
    "feed_w": "Feed W", "feed_l": "Feed L", "feed_t": "Feed T", "feed_pf": "Feed PF",
    "feed_pa": "Feed PA", "delta_w": "ΔW", "delta_l": "ΔL", "delta_t": "ΔT",
    "delta_pf": "ΔPF", "delta_pa": "ΔPA", "verdict": "Verdict",
    "rating_points": "Rating (pts)", "games_played": "GP",
    "team_game_total_avg": "Team game total", "shrunk_total_tendency": "Shrunk tendency",
    "matchup": "Matchup", "venue": "Venue", "network": "Network",
    "market_id": "Market", "market_type": "Market type",
    "origination_order": "Step", "derived_from": "Derived from",
    "model_line": "Model line", "market_line": "Market line",
    "market_line_status": "Market line status",
    "difference_model_minus_market": "Model − market",
    "difference_status": "Difference status", "units": "Units",
    "model_price_american": "Model price (US)", "model_inputs": "Model inputs",
    "model_total_estimator_b": "Estimator B", "total_estimator_gap_b_minus_a": "Gap B−A",
    "snapshot_utc": "Snapshot (UTC)", "snapshot_type": "Snapshot", "value": "Value",
    "captured_utc": "Captured (UTC)", "price_american": "Price (US)",
    "source_tier": "Source tier", "slot": "Slot", "what_it_holds": "What it holds",
    "required": "Required", "populated_this_build": "Populated this build",
    "teams_on_bye": "Teams on bye", "count": "Count", "unit": "Unit", "position": "Pos",
    "rank1": "1st string", "rank2": "2nd string", "rank3": "3rd string",
    "rank4": "4th string", "shared_rank1": "Shared 1st", "empty_first_string": "Empty 1st",
    "as_of_published": "Club's as-of date", "player": "Player", "injury": "Injury",
    "practice_status": "Practice status", "game_status": "Game status",
    "read_by": "Read by", "crosscheck_vs_carried_forward": "Cross-check",
    "delta_vs_previous_read": "Delta", "delta_status": "Delta status",
    "field": "Field", "value_read_2026_11_13": "Read 2026-11-13",
    "value_read_2026_11_15": "Read 2026-11-15",
    "starter_named_by_club": "Starter (club chart)",
    "starter_game_status": "Starter status",
    "replacement_named_by_club": "Replacement (club chart)",
    "replacement_depth_string": "Replacement string",
    "depth_of_replacement_label": "Depth of replacement", "rungs_down": "Rungs down",
    "compounding_replacement_also_out": "Compounding", "cascade_skipped": "Skipped (also out)",
    "replacement_on_injury_report": "Replacement on report",
    "no_backup_published": "No backup published", "as_of": "As of",
    "depth_slots_parsed": "Depth slots parsed", "depth_status": "Depth status",
    "players_listed_on_report": "Players on report",
    "game_status_published": "Game status published", "starters_out": "Starters out",
    "replacements_named": "Replacements named",
    "slots_with_no_replacement_published": "Slots with no replacement",
    "players_out": "Players out", "players_questionable": "Players questionable",
    "net_injury_count": "Net injury count", "status_note": "Note",
    "offence_team": "Offence", "defence_team": "Defence", "pairing": "Pairing",
    "offence_position": "Off. pos", "offence_player": "Off. player",
    "offence_depth_string": "Off. string", "defence_position": "Def. pos",
    "defence_player": "Def. player", "defence_depth_string": "Def. string",
    "depth_gap_defence_minus_offence": "Gap (def − off)", "flag": "Flag",
    "family_id": "Family", "division": "Division", "rule_text": "Rule (frozen)",
    "rule": "Test", "sample_window": "Sample window", "n": "n", "hits": "Hits",
    "hit_rate": "Hit rate", "wilson_lo": "95% low", "wilson_hi": "95% high",
    "binomial_p": "Binomial p", "holm_p": "Holm p", "roi": "ROI",
    "roi_status": "ROI status", "gates_failed": "Gates failed", "certified": "Certified",
    "what_would_change_our_mind_down": "What would change our mind (down)",
    "what_would_change_our_mind_up": "What would change our mind (up)",
    "registration": "Pre-registration", "control_id": "Control", "control": "Control",
    "expected_hit_rate": "Expected", "observed_hit_rate": "Observed", "note": "Note",
    "gate_id": "Gate", "name": "Name", "requirement": "Requirement", "metric": "Metric",
    "threshold": "Threshold", "status_this_desk": "Status this desk",
    "trigger_id": "Trigger", "window": "Window", "observed": "Observed",
    "gate_name": "Gate", "rank": "Rank", "proper_score_status": "Proper score status",
    "stake": "Stake", "clv": "CLV", "drawdown": "Drawdown", "definition": "Definition",
    "families_entered": "Families entered", "correlation_id": "ID",
    "variable_a": "Variable A", "variable_b": "Variable B", "r": "r",
    "ci95_lo": "95% low", "ci95_hi": "95% high", "input_tier": "Input tier",
    "inputs": "Inputs", "id": "ID", "quantity": "Quantity",
    "value_published_elsewhere": "Value published elsewhere",
    "n_published_elsewhere": "n published elsewhere", "published_by": "Published by",
    "why_withheld": "Why withheld", "games": "Games", "actual_wins": "Actual wins",
    "actual_win_pct": "Actual win%", "pythagorean_expected_wins": "Pythagorean exp. wins",
    "luck_wins_actual_minus_expected": "Luck (actual − expected)",
    "close_game_share": "Close-game share", "binomial_sd_wins": "Binomial SD (wins)",
    "binomial_95_low": "Binomial 95% low", "binomial_95_high": "Binomial 95% high",
    "inside_the_noise_band": "Inside the noise band",
    "true_hit_rate": "True hit rate",
    "bets_to_demonstrate_skill_80pct_power": "Bets needed (80% power)",
    "chance_a_coin_flip_shows_55pct_over_200_bets": "Coin flip showing ≥55% over 200 bets",
    "requirement_id": "ID", "blocking_gate": "Blocking gate",
    "number_that_would_clear_it": "The number that would clear it", "page": "Page",
    "question_id": "ID", "question": "Question", "what_we_have": "What we have",
    "what_is_missing": "What is missing", "blocking": "Blocking?",
    "cheapest_discovery_route": "Cheapest discovery route", "suggestion_id": "ID",
    "suggestion": "Suggestion", "options": "Options",
    "recommended_path": "Recommended path",
    "what_would_change_the_call": "What would change the call",
    "decision_status": "Decision status", "flag_id": "ID", "severity": "Severity",
    "area": "Area", "title": "Title", "detail": "Detail", "consequence": "Consequence",
    "action": "Action", "source_id": "Source", "publisher": "Publisher",
    "url": "URL", "tier": "Tier", "fetched_utc": "Fetched (UTC)", "used_for": "Used for",
    "rows_contributed": "Rows", "verification_status": "Verification status",
    "check_id": "Check", "claim": "Claim", "official_value_today": "Official value today",
    "carried_forward_value": "Carried-forward value", "interpretation": "Interpretation",
    "item": "Item", "games_evaluated": "Games", "side_picks_correct": "Winners called",
    "side_hit_rate": "Side hit rate", "margin_mae": "Margin MAE",
    "total_mae_estimator_a": "Totals MAE (A)",
    "total_mae_estimator_b": "Totals MAE (B)",
    "total_mae_league_average_baseline": "Totals MAE (baseline)",
    "bytes": "Bytes", "sha256": "SHA-256", "path": "Path", "captured": "Captured (UTC)",
}


def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def rows_of(name: str):
    with open(DATA / name, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def label(key: str) -> str:
    return LABELS.get(key, key.replace("_", " ").capitalize())


def short_url(u: str) -> str:
    try:
        p = urlparse(u)
    except Exception:
        return u[:40]
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    parts = [x for x in p.path.split("/") if x]
    tail = "/".join(parts[-2:]) if parts else ""
    out = f"{host}/{tail}" if tail else host
    return out[:46]


def source_cell(row, extra=()):
    """The last cell of every body row: an official link, or UNVERIFIED."""
    urls = []
    for key in list(SOURCE_KEYS) + list(extra):
        v = (row.get(key) or "").strip()
        if v.startswith("http") and v not in urls:
            urls.append(v)
    if not urls:
        return '<span class="blank">UNVERIFIED</span>'
    seen_hosts = []
    parts = []
    for u in urls:
        host = urlparse(u).netloc.lower().lstrip("www.")
        if host in seen_hosts:
            continue
        seen_hosts.append(host)
        parts.append(f'<a href="{esc(u)}" target="_blank" rel="noopener nofollow">{esc(short_url(u))}</a>')
    return " ".join(parts[:3])


def badges(value: str, mapping=None) -> str:
    mapping = mapping or {}
    cls = mapping.get(value)
    if cls:
        return f'<span class="pill {cls}">{esc(value)}</span>'
    return esc(value)


STATUS_PILL = {
    "met": "ok", "partial": "warn", "blocked": "bad",
    "PASS": "ok", "FAIL": "bad", "NOT APPLICABLE": "mute",
    "MATCH": "ok", "CONFIRMED": "ok", "YES": "ok", "no": "mute",
    "NO": "mute", "UNVERIFIED": "blank2", "AWAITING DECISION": "warn",
    "DEFERRED": "mute", "OPEN": "warn", "IMPLEMENTED": "ok",
}

_PILL_COLUMNS = {
    "status", "result", "certified", "blocking", "decision_status", "severity",
    "verdict", "game_status", "flag", "input_tier", "tier", "verification",
    "game_status_published", "inside_the_noise_band", "verification_status",
}


def cell(key: str, value: str):
    v = "" if value is None else str(value)
    if key in _PILL_COLUMNS and v:
        return badges(v, STATUS_PILL)
    if key.endswith("_url") or key == "url":
        if v.startswith("http"):
            return f'<a href="{esc(v)}" target="_blank" rel="noopener nofollow">{esc(short_url(v))}</a>'
        return '<span class="blank">UNVERIFIED</span>' if not v else esc(v)
    if v == "":
        return '<span class="blank">—</span>'
    if key in ("requirement", "rule_text", "detail", "consequence", "action", "note",
               "interpretation", "claim", "what_we_have", "what_is_missing",
               "cheapest_discovery_route", "options", "recommended_path",
               "what_would_change_the_call", "number_that_would_clear_it",
               "question", "suggestion", "status_note", "verification_note",
               "verification_status", "why_withheld", "inputs", "requirement",
               "definition", "roi_status", "proper_score_status", "market_line_status",
               "difference_status", "delta_status", "status_this_desk", "registration",
               "what_would_change_our_mind_down", "what_would_change_our_mind_up",
               "used_for", "units", "model_inputs", "depth_status", "pairing",
               "rule", "sample_window", "gates_failed", "blocking_gate", "title", "measurement",
               "staking_note"):
        return f'<span class="wrap">{esc(v)}</span>'
    return esc(v)


def render_table(table_id, rows, columns, note="", empty="No rows.", extra_sources=(),
                 source_label=None):
    """source_label: for tables whose rows are decisions or definitions rather
    than claims about the world, the last cell says so instead of pretending to
    carry a source."""
    if not rows:
        return f'<p class="empty">{esc(empty)}</p>'
    thead = "".join(f"<th>{esc(label(c))}</th>" for c in columns) + "<th>Source</th>"
    body = []
    for r in rows:
        tds = "".join(f"<td>{cell(c, r.get(c, ''))}</td>" for c in columns)
        if source_label:
            tds += f'<td><span class="blank">{esc(source_label)}</span></td>'
        else:
            tds += f"<td>{source_cell(r, extra_sources)}</td>"
        body.append(f"<tr>{tds}</tr>")
    filt = (f'<input class="filter" type="search" placeholder="Filter rows…" '
            f'data-table="{esc(table_id)}" aria-label="Filter this table">')
    count = f'<p class="table-note">{len(rows)} rows{(" — " + esc(note)) if note else ""}</p>'
    return (f'<div class="tablewrap">{count}{filt}'
            f'<table id="{esc(table_id)}"><thead><tr>{thead}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def kpi(items):
    cards = "".join(
        f'<div class="card"><span class="kpi-value">{esc(v)}</span>'
        f'<span class="kpi-label">{esc(l)}</span></div>' for v, l in items)
    return f'<div class="kpis">{cards}</div>'


def page_styles():
    return ""


CSS = """
:root{
  --bg:#0e1116; --panel:#161b22; --panel2:#1c232c; --line:#2a323d;
  --ink:#e6edf3; --muted:#9aa7b4; --accent:#4cc2ff; --ok:#3fb950; --warn:#d29922;
  --bad:#f85149; --blank:#8b949e;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header.top{background:linear-gradient(180deg,#111823,#0e1116);border-bottom:1px solid var(--line);
  padding:18px 22px;position:sticky;top:0;z-index:20}
header.top h1{margin:0;font-size:17px;letter-spacing:.02em}
header.top .sub{color:var(--muted);font-size:12.5px;margin-top:3px}
.shell{display:grid;grid-template-columns:236px minmax(0,1fr);gap:0;align-items:start}
nav.side{border-right:1px solid var(--line);padding:16px 10px 40px;position:sticky;top:70px;
  height:calc(100vh - 70px);overflow:auto}
nav.side a{display:block;padding:7px 10px;border-radius:6px;color:var(--muted);font-size:13.5px}
nav.side a:hover{background:var(--panel);color:var(--ink);text-decoration:none}
nav.side a.on{background:#1d2b38;color:var(--ink);font-weight:600}
nav.side .grp{color:#6e7b8b;font-size:11px;text-transform:uppercase;letter-spacing:.08em;
  padding:14px 10px 6px}
main{padding:22px 26px 80px;min-width:0;max-width:1500px}
h2{margin:26px 0 8px;font-size:19px}
h2:first-child{margin-top:4px}
h3{margin:20px 0 6px;font-size:15px;color:var(--ink)}
p{color:#c9d4de;max-width:100ch}
p.lead{color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin:14px 0 6px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 15px;
  display:flex;flex-direction:column;gap:5px}
.kpi-value{font-size:25px;font-weight:650;letter-spacing:-.01em}
.kpi-label{color:var(--muted);font-size:12px;line-height:1.35}
.callout{border-left:3px solid var(--accent);background:var(--panel);padding:12px 15px;
  border-radius:0 8px 8px 0;margin:14px 0}
.callout.warn{border-color:var(--warn)}
.callout.bad{border-color:var(--bad)}
.callout.ok{border-color:var(--ok)}
.tablewrap{margin:12px 0 22px;background:var(--panel);border:1px solid var(--line);
  border-radius:10px;padding:12px 13px 4px;overflow:auto}
.table-note{color:var(--muted);font-size:12px;margin:0 0 8px}
input.filter{width:100%;max-width:340px;margin-bottom:10px;padding:7px 10px;border-radius:7px;
  border:1px solid var(--line);background:#0d1218;color:var(--ink);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:left;padding:6px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{position:sticky;top:0;background:var(--panel2);color:#b9c6d3;font-weight:600;
  white-space:nowrap;z-index:2}
tbody tr:hover{background:#1a212b}
td .wrap{display:block;max-width:52ch;white-space:normal;color:#c9d4de}
td.num{font-variant-numeric:tabular-nums}
.pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11.5px;font-weight:600;
  border:1px solid transparent;white-space:nowrap}
.pill.ok{background:rgba(63,185,80,.14);color:#7ee787;border-color:rgba(63,185,80,.35)}
.pill.warn{background:rgba(210,153,34,.14);color:#e3b341;border-color:rgba(210,153,34,.35)}
.pill.bad{background:rgba(248,81,73,.14);color:#ff7b72;border-color:rgba(248,81,73,.35)}
.pill.mute{background:#222a33;color:#9aa7b4;border-color:#2f3944}
.pill.blank2{background:#222a33;color:#8b949e;border-color:#2f3944}
.blank{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11.5px;font-weight:700;
  background:#242c36;color:#8b949e;border:1px dashed #46515e;white-space:nowrap}
.empty{color:var(--muted);font-style:italic}
ul.tight{padding-left:20px;max-width:100ch}
ul.tight li{margin:4px 0;color:#c9d4de}
footer{color:#6e7b8b;font-size:12px;padding:20px 26px;border-top:1px solid var(--line)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px}
@media(max-width:900px){
  .shell{grid-template-columns:1fr}
  nav.side{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line);
    display:flex;flex-wrap:wrap;gap:4px}
  nav.side .grp{display:none}
  main{padding:16px}
}
"""

JS = """
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('input.filter').forEach(function (input) {
    var table = document.getElementById(input.getAttribute('data-table'));
    if (!table) return;
    var rows = Array.prototype.slice.call(table.tBodies[0].rows);
    var note = table.parentNode.querySelector('.table-note');
    var total = rows.length;
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      rows.forEach(function (tr) {
        var hit = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
        tr.style.display = hit ? '' : 'none';
        if (hit) shown++;
      });
      if (note) note.textContent = q ? (shown + ' of ' + total + ' rows shown') : (total + ' rows');
    });
  });
});
"""


def layout(active: str, title: str, lead: str, body: str, manifest: dict) -> str:
    nav = []
    for href, text in NAV:
        cls = "on" if href == active else ""
        nav.append(f'<a class="{cls}" href="{href}">{text}</a>')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — OWN5 NFL decision desk ({SESSION})</title>
<style>{CSS}</style></head>
<body>
<header class="top">
  <h1>OWN5 · NFL decision-readiness desk</h1>
  <div class="sub">Session {SESSION} · built {esc(manifest.get('build_utc',''))} · every table row links to
  the official page it was read from; anything that cannot be sourced is left blank and flagged.</div>
</header>
<div class="shell">
<nav class="side">
  <div class="grp">Read first</div>
  {''.join(nav[:5])}
  <div class="grp">Evidence</div>
  {''.join(nav[5:14])}
  <div class="grp">Registers</div>
  {''.join(nav[14:])}
</nav>
<main>
<h2>{esc(title)}</h2>
<p class="lead">{esc(lead)}</p>
{body}
</main>
</div>
<footer>OWN5 · {SESSION} · Tables are generated from CSVs that are rebuilt deterministically by
<code>engine.py</code>; the row-level source proof is re-run on every build by <code>verify.py</code>.</footer>
<script>{JS}</script>
</body></html>
"""


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------

def build_pages(manifest: dict):
    rep = json.loads((DATA / "build_report.json").read_text(encoding="utf-8"))
    mc = rep["model_card"]
    pages = {}

    def add(name, title, lead, body):
        pages[name] = layout(name, title, lead, body, manifest)

    # ---------------- index ----------------
    req = rows_of("requirements.csv")
    counts = {"met": 0, "partial": 0, "blocked": 0}
    for r in req:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    flagged = rows_of("flagged.csv")
    blocking = [f for f in flagged if f["severity"].startswith("blocking")]
    idx = [
        kpi([
            (rep["official_finals"], "official 2026 finals in the results feed"),
            (f"{rep['spotcheck_matched']}/{rep['spotcheck_games']}",
             "feed rows re-read from the official week pages and matching"),
            (f"{rep['std_exact']}/32", "clubs whose game-by-game record reconciles to the official standings"),
            (rep["originated_markets"], "markets originated for week 11 (side, total, moneyline)"),
            (rep["certified"], "strategies certified — none can pass the gates"),
            (len(blocking), "blocking data gaps, each with the number that would clear it"),
        ]),
        '<div class="callout bad"><strong>Read this before anything else.</strong> '
        'This desk can originate its own lines but cannot yet grade them, because no official or '
        'licensed market price exists anywhere in this repository. An aggregator reference line '
        'without a timestamp is held by a parallel desk, and an untimestamped number cannot be an '
        'opening or a closing price. Every price column on this site is blank and flagged '
        'rather than filled with a guess. The <a href="questions.html">questions register</a> says what '
        'is missing and the cheapest way to get it; the <a href="suggestions.html">suggestions register</a> '
        'sets out the paths a reviewer chooses between. Nothing on those two pages has been built.</div>',
        "<h3>Decision readiness: one row per requirement</h3>",
        '<p class="lead">Every requirement from the brief, with the gate that blocks it and the '
        'number that would clear it. This is requirement R-22 and it is the table to work from.</p>',
        render_table("t-req", req,
                     ["requirement_id", "requirement", "status", "blocking_gate",
                      "number_that_would_clear_it", "page"],
                     note="status is this desk's status for the 2026 season"),
        "<h3>Blocking gaps</h3>",
        render_table("t-flag", blocking,
                     ["flag_id", "area", "title", "consequence", "action", "status"],
                     note="the gaps that stop a strategy being certified"),
    ]
    add("index.html", "Overview", "What this desk has, what it cannot do yet, and the exact number "
        "that would change that.", "".join(idx))

    # ---------------- executive summary ----------------
    std = rows_of("standings_official.csv")
    top_rating = rows_of("team_ratings.csv")
    exec_body = [
        kpi([
            (rep["official_finals"], "official finals (weeks 1–10)"),
            (rep["corpus_weeks_1_9"], "completed games in the pre-registered backtest corpus (weeks 1–9)"),
            (rep["week10_finals"], "week-10 finals captured"),
            (rep["pending_week10"], "week-10 games still unfinished at capture"),
            (rep["clubs_parsed"], "clubs with a parsed official depth chart (of 32)"),
            (rep["depth_slots"], "published depth slots transcribed"),
            (rep["injury_rows"], "rows in the week-10 injury report"),
            (rep["audit_checks"], "line-by-line checks against official sources"),
        ]),
        "<h3>What was done this session</h3>",
        '<ul class="tight">'
        f"<li>Six official captures were read on 2026-11-15: league standings, the week-11 schedule, the "
        f"week-10 results page, the week-10 injury report, a five-week spot-check of the results feed, "
        f"and 31 of 32 club depth charts. Each is listed with its URL and capture time on the "
        f"<a href=\"sources.html\">sources page</a>.</li>"
        f"<li>The carried-forward results feed was re-checked against the official week pages: "
        f"{rep['spotcheck_matched']} of {rep['spotcheck_games']} re-read rows agreed, and the feed "
        f"reconciles to the official standings for {rep['std_exact']} of 32 clubs "
        f"(<a href=\"results.html\">results</a>).</li>"
        f"<li>Injury designations were read twice, two days apart, and "
        f"{rep['injury_sample_mismatched']} rows were observed to change between the two official "
        f"reads — direct evidence that the report is a series, not a weekly snapshot "
        f"(<a href=\"injuries.html\">injuries</a>).</li>"
        f"<li>{rep['originated_markets']} markets were originated for week 11 in the required order — "
        f"side, then total, then moneyline — from a rating model fitted on "
        f"{rep['official_finals']} official margins "
        f"(<a href=\"lines.html\">originated lines</a>).</li>"
        f"<li>Every depth slot was transcribed, replacements named, and a "
        f"{rep['matchup_rows']}-row offence-versus-defence deficiency matrix built for the week-11 "
        f"slate (<a href=\"matchup.html\">matchup matrix</a>).</li>"
        "</ul>",
        "<h3>The three findings that matter</h3>",
        f'<div class="callout bad"><strong>1. There is no price data, so nothing can be graded.</strong> '
        f'nfl.com publishes no spreads, totals or moneylines, and no operator price has been read into '
        f'this repository; a parallel desk searched the same pages and reached the same conclusion. '
        f'The only price-like rows anywhere in the repo are aggregator reference lines of unknown '
        f'timestamp, which cannot be an opening or a closing number. '
        f'Of {rep["price_snapshot_rows"]} price-snapshot rows this desk needs, only '
        f'{rep["price_snapshots_populated"]} could be filled — and those are our own model outputs, not '
        f'market prices. ROI, closing line value and the residual against the market are undefined, so '
        f'the staking leaderboard is empty by design and no strategy can be certified.</div>',
        f'<div class="callout warn"><strong>2. Home-field advantage is not established in this sample.</strong> '
        f'The model fits home field at {mc["hfa_points"]:.2f} points per game with a 95% interval of '
        f'{mc["hfa_ci95_low"]:.2f} to {mc["hfa_ci95_high"]:.2f} on {rep["official_finals"]} official games. '
        f'The interval contains zero. Any strategy that leans on home field is leaning on a number this '
        f'sample cannot support.</div>',
        f'<div class="callout warn"><strong>3. Neither totals estimator beats the naive baseline, and '
        f'the first run that said otherwise was wrong.</strong> Fitted on prior weeks only, estimator A '
        f'has a walk-forward mean absolute error of {mc["oos_total_mae_a"]:.2f} points and estimator B '
        f'{mc["oos_total_mae_b"]:.2f}, against a league-average baseline of '
        f'{mc["oos_total_mae_baseline"]:.2f}. An earlier run of this build appeared to show estimator B '
        f'winning by about a point; that was leakage, because it was fitted on the full-season '
        f'standings, which contain the game being predicted (flag F-18). Both estimators stay published '
        f'side by side with the gap column, as the brief asks, and neither is collapsed until the '
        f'pre-registered comparison fires.</div>',
        "<h3>Model card</h3>",
        render_table("t-card", rows_of("model_card.csv"), ["item", "value", "note"]),
        "<h3>Walk-forward by week</h3>",
        '<p class="lead">Every game is predicted from a model fitted only on the weeks before it. '
        'Weeks 2 and 3 are included for completeness but are fitted on one and two rounds of games '
        'respectively, which is why their margin error is large.</p>',
        render_table("t-wf", rows_of("walkforward_by_week.csv"),
                     ["week", "games_evaluated", "side_picks_correct", "side_hit_rate", "margin_mae",
                      "total_mae_estimator_a", "total_mae_estimator_b",
                      "total_mae_league_average_baseline"]),
        "<h3>Standings as published today</h3>",
        render_table("t-std", std,
                     ["team", "club", "w", "l", "t", "pct", "pf", "pa", "net", "pf_per_game",
                      "pa_per_game", "net_per_game", "win_pct"]),
        "<h3>Team ratings</h3>",
        '<p class="lead">Ratings are a least-squares fit on every official margin, so each one is '
        'already adjusted for the opponents that team played. They are shrunk toward zero by a ridge '
        'penalty of 1.0 point squared (flagged as F-17) because the early-season schedule does not '
        'separate home advantage from team strength without it.</p>',
        render_table("t-rating", top_rating,
                     ["team", "club", "rating_points", "games_played", "pf_per_game", "pa_per_game",
                      "team_game_total_avg", "shrunk_total_tendency"]),
    ]
    add("executive-summary.html", "Executive summary",
        "The important details: what the official sources say, what the model says, and what is "
        "missing.", "".join(exec_body))

    # ---------------- requirements ----------------
    add("requirements.html", "Requirements register",
        "Every requirement line from the brief, in order, with the gate that blocks it and the "
        "number that would clear it.",
        kpi([(counts.get("met", 0), "met"), (counts.get("partial", 0), "partial"),
             (counts.get("blocked", 0), "blocked"),
             (len(req), "requirement lines in the brief")])
        + render_table("t-req-all", req,
                       ["requirement_id", "requirement", "status", "blocking_gate",
                        "number_that_would_clear_it", "page"]))

    # ---------------- questions ----------------
    q = rows_of("questions.csv")
    add("questions.html", "Questions register",
        "What we have, what we do not, whether it blocks a decision, and the cheapest way to find "
        "the missing piece.",
        kpi([(len(q), "questions"),
             (sum(1 for r in q if r["blocking"] == "blocking"), "blocking"),
             (sum(1 for r in q if r["blocking"] != "blocking"), "non-blocking")])
        + render_table("t-q", q, ["question_id", "question", "what_we_have", "what_is_missing",
                                  "blocking", "cheapest_discovery_route"]))

    # ---------------- suggestions ----------------
    sg = rows_of("suggestions.csv")
    add("suggestions.html", "Suggestions register",
        "Paths to improve the site and the desk, written as options for a reviewer to choose "
        "between. Nothing in this register has been built.",
        '<div class="callout warn">Every row here is a decision, not a change. The recommended path '
        'is stated, the condition that would change the recommendation is stated, and the decision '
        'status is AWAITING DECISION until someone chooses.</div>'
        + kpi([(len(sg), "suggestions"),
               (sum(1 for r in sg if r["decision_status"] == "AWAITING DECISION"), "awaiting decision"),
               (sum(1 for r in sg if "IMPLEMENTED" in r["decision_status"]), "implemented as a rule"),
               (sum(1 for r in sg if r["decision_status"] == "DEFERRED"), "deferred")])
        + render_table("t-s", sg, ["suggestion_id", "suggestion", "options", "recommended_path",
                                   "what_would_change_the_call", "decision_status", "note"],
                       source_label="DECISION — makes no claim about the world"))

    # ---------------- results ----------------
    feed = rows_of("results_feed.csv")
    pending = rows_of("results_pending.csv")
    recon = rows_of("standings_reconciliation.csv")
    bye = rows_of("bye_weeks_2026.csv")
    add("results.html", "Results feed",
        "Every completed 2026 game we hold, each one read from an official week page, plus the "
        "reconciliation of those games to the official standings.",
        kpi([(len(feed), "finals"), (rep["corpus_weeks_1_9"], "in the weeks 1–9 corpus"),
             (rep["spotcheck_games"], "re-read this session"),
             (f"{rep['std_exact']}/32", "clubs reconciling to the standings"),
             (len(pending), "games unfinished at capture")])
        + '<div class="callout">Rows marked <em>session-verified</em> were read from the official week '
          'page by this session today. Rows marked <em>carried-forward</em> were transcribed by an '
          'earlier session from the same official pages and have not been re-read; '
          f'{rep["spotcheck_games"]} of them were spot-checked and every one agreed.</div>'
        + "<h3>Completed games</h3>"
        + render_table("t-feed", feed,
                       ["game_id", "week", "kickoff_date", "away", "away_score", "home",
                        "home_score", "home_margin", "total_points", "result", "neutral_site",
                        "verification", "verification_note"])
        + "<h3>Unfinished at capture</h3>"
        + '<p class="lead">Week 10 was still being played when it was captured. These scores are blank '
          'on purpose: a value that has not been published cannot be filled in.</p>'
        + render_table("t-pend", pending,
                       ["game_id", "week", "kickoff_date", "away", "home", "away_score",
                        "home_score", "status"])
        + "<h3>Reconciliation to the official standings</h3>"
        + '<p class="lead">The game-by-game record implied by the feed, against the record nfl.com '
          'publishes. Where they differ, the difference is the games still in progress at capture.</p>'
        + render_table("t-recon", recon,
                       ["team", "club", "official_w", "official_l", "official_t", "official_pf",
                        "official_pa", "feed_w", "feed_l", "feed_t", "feed_pf", "feed_pa",
                        "delta_w", "delta_l", "delta_t", "delta_pf", "delta_pa", "verdict"])
        + "<h3>Bye weeks</h3>"
        + render_table("t-bye", bye, ["week", "teams_on_bye", "count"]))

    # ---------------- slate ----------------
    slate = rows_of("slate_wk11.csv")
    add("slate.html", "Week 11 slate",
        "Every week-11 fixture as nfl.com publishes it, with the venue and whether the site is "
        "neutral.",
        kpi([(len(slate), "fixtures"), (rep["originated_markets"], "markets originated"),
             ("6", "clubs on bye")])
        + '<div class="callout warn">Minnesota at San Francisco is played at Estadio Banorte in '
          'Mexico City. It is a neutral site and is excluded from the home-field term in every '
          'market we originate for it.</div>'
        + render_table("t-slate", slate,
                       ["game_id", "date", "kickoff_et", "away", "home", "venue", "network",
                        "neutral_site"]))

    # ---------------- lines ----------------
    mk = rows_of("originated_markets.csv")
    steps = rows_of("origination_steps.csv")
    add("lines.html", "Originated lines",
        "Our own lines for week 11, originated side first, then total, then moneyline. The market "
        "column is blank because no market price exists to put in it.",
        '<div class="callout bad">The market line, the difference and the closing-line value are '
        'undefined. They are published blank and flagged rather than estimated. This is flag F-01 '
        'and it is the single blocking gap on this desk.</div>'
        + kpi([(len(mk), "markets"), ("13", "sides"), ("13", "totals"), ("13", "moneylines"),
               ("0", "market prices available")])
        + "<h3>The three steps, in the order the brief requires</h3>"
        + render_table("t-steps", steps,
                       ["market_id", "step", "market_type", "instruction", "depends_on"])
        + "<h3>Originated markets</h3>"
        + render_table("t-mk", mk,
                       ["matchup", "kickoff_date", "kickoff_et", "market_type",
                        "origination_order", "model_line", "model_total_estimator_b",
                        "total_estimator_gap_b_minus_a", "market_line", "market_line_status",
                        "difference_model_minus_market", "model_price_american", "units",
                        "model_inputs", "snapshot_utc"])
        + "<h3>Model card and walk-forward</h3>"
        + render_table("t-card2", rows_of("model_card.csv"), ["item", "value", "note"])
        + render_table("t-wf2", rows_of("walkforward_by_week.csv"),
                       ["week", "games_evaluated", "side_picks_correct", "side_hit_rate",
                        "margin_mae", "total_mae_estimator_a", "total_mae_estimator_b",
                        "total_mae_league_average_baseline"])
        + "<h3>Team ratings behind the side and the moneyline</h3>"
        + render_table("t-rate2", rows_of("team_ratings.csv"),
                       ["team", "club", "rating_points", "games_played", "pf_per_game",
                        "pa_per_game", "team_game_total_avg", "shrunk_total_tendency"]))

    # ---------------- price store ----------------
    ps = rows_of("price_snapshots.csv")
    schema = rows_of("price_store_schema.csv")
    add("price-store.html", "Price store",
        "The four price slots every graded bet needs. Only our own model output exists today; the "
        "market slots are empty and are not filled with a substitute.",
        kpi([(len(ps), "snapshot rows"),
             (sum(1 for r in ps if r["value"]), "populated"),
             (sum(1 for r in ps if not r["value"]), "empty")])
        + "<h3>Schema</h3>"
        + render_table("t-pss", schema,
                       ["slot", "what_it_holds", "required", "populated_this_build", "status"],
                       source_label="SCHEMA — describes a slot, not a value")
        + "<h3>Snapshot rows</h3>"
        + render_table("t-ps", ps,
                       ["market_id", "snapshot_type", "value", "captured_utc", "price_american",
                        "status", "source_tier"]))

    # ---------------- depth ----------------
    depth = rows_of("depth_slots.csv")
    repl = rows_of("replacement_depth.csv")
    avail = rows_of("team_availability.csv")
    add("depth.html", "Depth charts and replacements",
        "Every published depth slot, the replacement we can name from the club's own chart, and the "
        "per-club view of what is missing.",
        kpi([(rep["clubs_parsed"], "clubs parsed (of 32)"), (rep["depth_slots"], "slots"),
             (rep["shared_rank1_slots"], "slots with two 1st-string players"),
             (rep["empty_first_string_slots"], "slots with an empty 1st string"),
             (len(repl), "starters out with a named replacement")])
        + '<div class="callout warn">Clubs publish these charts themselves and label them '
          '"unofficial". They are an official club publication, but they are not the league\'s '
          'game-day starter list, so a replacement here is never reported as an announced starter.</div>'
        + "<h3>Per-club availability</h3>"
        + render_table("t-avail", avail,
                       ["team", "club", "depth_slots_parsed", "depth_status",
                        "players_listed_on_report", "game_status_published", "starters_out",
                        "replacements_named", "slots_with_no_replacement_published", "players_out",
                        "players_questionable", "net_injury_count", "status_note"])
        + "<h3>Replacement depth</h3>"
        + '<p class="lead">A starter is only counted as out where the league report publishes a game '
          'status of Out for a player the club lists as a first-string at that position. The '
          'replacement is the next name on the club\'s own chart, skipping anyone else who is also '
          'out.</p>'
        + render_table("t-repl", repl,
                       ["team", "unit", "position", "starter_named_by_club", "starter_game_status",
                        "replacement_named_by_club", "replacement_depth_string",
                        "depth_of_replacement_label", "rungs_down",
                        "compounding_replacement_also_out", "cascade_skipped",
                        "replacement_on_injury_report", "no_backup_published", "as_of"])
        + "<h3>Every published slot</h3>"
        + render_table("t-depth", depth,
                       ["team", "unit", "position", "rank1", "rank2", "rank3", "rank4",
                        "shared_rank1", "empty_first_string", "as_of_published", "status"]))

    # ---------------- injuries ----------------
    inj = rows_of("injuries.csv")
    delta = rows_of("injury_delta.csv")
    add("injuries.html", "Injury report",
        "The week-10 report as published, the cross-check against the earlier read, and every value "
        "that changed between the two.",
        kpi([(len(inj), "rows"), (rep["injury_sample_checked"], "re-read this session"),
             (rep["injury_sample_matched"], "agreed with the earlier read"),
             (rep["injury_sample_mismatched"], "changed between the two reads"),
             (len(delta), "fields that changed")])
        + '<div class="callout warn">The week-11 report is not published: '
          '<code>/injuries/league/2026/reg11</code> serves the week-10 report, the week selector '
          'stops at week 10, and the Minnesota–San Francisco game centre says the injury report is '
          'not available. Week 11 adjustments therefore cannot be made from an official source.</div>'
        + "<h3>What changed between the two official reads</h3>"
        + '<p class="lead">The same page read on 2026-11-13 by an earlier session and on 2026-11-15 by '
          'this one. These rows are the evidence that the report is a series, not a snapshot — and '
          'the reason the injury signal has to be a surprise, not a level.</p>'
        + render_table("t-delta", delta,
                       ["team", "player", "field", "value_read_2026_11_13", "value_read_2026_11_15"])
        + "<h3>The report</h3>"
        + render_table("t-inj", inj,
                       ["team", "player", "position", "injury", "practice_status", "game_status",
                        "week", "captured_utc", "read_by", "crosscheck_vs_carried_forward",
                        "delta_status"]))

    # ---------------- matchup ----------------
    mm = rows_of("matchup_deficiency.csv")
    add("matchup.html", "Matchup deficiency matrix",
        "One row per offensive unit against the defensive unit that faces it, with the depth string "
        "of each side taken from the clubs' own charts.",
        kpi([(len(mm), "pairings"), ("13", "fixtures"),
             (sum(1 for r in mm if r["flag"].startswith("DEFICIENCY")), "flagged as a deficiency"),
             (sum(1 for r in mm if r["flag"] == "even"), "even")])
        + '<p class="lead">The gap is the defender\'s depth string minus the offensive player\'s. A '
          'positive gap means the offence is facing a deeper-string defender than it is fielding '
          'itself; a negative gap means the defence it faces is thinner than the offence. Depth here '
          'is what the club publishes, not what was observed on the field.</p>'
        + render_table("t-mm", mm,
                       ["matchup", "offence_team", "defence_team", "pairing", "offence_position",
                        "offence_player", "offence_depth_string", "defence_position",
                        "defence_player", "defence_depth_string",
                        "depth_gap_defence_minus_offence", "flag"]))

    # ---------------- strategies ----------------
    st = rows_of("strategies.csv")
    ctl = rows_of("controls.csv")
    add("strategies.html", "Strategies",
        "Ten pre-registered families. The rule text is frozen before the evaluation window opens "
        "and the commit hash is the registration.",
        kpi([(len(st), "families"),
             (sum(1 for r in st if r["division"] == "Singles"), "singles"),
             (sum(1 for r in st if r["division"] != "Singles"), "parlays / prop combos"),
             (rep["certified"], "certified")])
        + '<div class="callout">Backtest numbers are shown for measurement and are never counted '
          'towards promotion. A family is promoted only on prospective bets taken after its rule was '
          'frozen, and only after gates G1–G8 pass.</div>'
        + render_table("t-st", st,
                       ["family_id", "name", "division", "rule_text", "sample_window", "n", "hits",
                        "hit_rate", "wilson_lo", "wilson_hi", "binomial_p", "holm_p",
                        "measurement", "roi", "roi_status", "gates_failed", "certified",
                        "what_would_change_our_mind_down", "what_would_change_our_mind_up",
                        "registration"])
        + "<h3>Control baselines</h3>"
        + render_table("t-ctl", ctl,
                       ["control_id", "control", "n", "expected_hit_rate", "observed_hit_rate",
                        "note"]))

    # ---------------- gates ----------------
    gm = rows_of("gate_matrix.csv")
    add("gates.html", "Validation gates",
        "The gates a strategy must pass to be certified, the demotion triggers that send a live one "
        "back to paper, and the gate-by-gate matrix.",
        kpi([(len(rows_of("gates.csv")), "gates"), (len(rows_of("demotion_gate.csv")), "demotion triggers"),
             (sum(1 for r in gm if r["status"] == "PASS"), "gate checks passing"),
             (sum(1 for r in gm if r["status"] == "FAIL"), "gate checks failing")])
        + render_table("t-gates", rows_of("gates.csv"),
                       ["gate_id", "name", "requirement", "metric", "threshold", "status_this_desk"])
        + "<h3>Demotion triggers</h3>"
        + render_table("t-dem", rows_of("demotion_gate.csv"),
                       ["trigger_id", "name", "rule", "window"])
        + "<h3>Gate matrix</h3>"
        + render_table("t-gm", gm, ["family_id", "gate_id", "gate_name", "observed", "status"]))

    # ---------------- leaderboard ----------------
    sig = rows_of("leaderboard_signal.csv")
    stak = rows_of("leaderboard_staking.csv")
    div = rows_of("leaderboard_divisions.csv")
    add("leaderboard.html", "Leaderboard",
        "Signal and staking are scored on separate boards so a staking run cannot mask a bad signal. "
        "Both are empty of certified entries.",
        kpi([(len(sig), "families measured"), (rep["certified"], "certified"),
             (len(stak), "staking rows"), (len(div), "divisions")])
        + '<div class="callout bad">The staking board is empty by design. Staking needs a price, a '
          'stake size and settlement rules; none of the three exists, so a family cannot be certified '
          'on the staking axis at all.</div>'
        + "<h3>Divisions</h3>"
        + render_table("t-div", div, ["division", "definition", "families_entered", "status"],
                       source_label="DEFINITION — makes no claim about the world")
        + "<h3>Signal board</h3>"
        + '<p class="lead">Ranked on the interval, not on win rate alone. No proper score against a '
          'benchmark can be computed while there is no market price, so the binomial interval is '
          'what is shown and the proper-score column says so.</p>'
        + render_table("t-sig", sig,
                       ["rank", "family_id", "division", "n", "hit_rate", "wilson_lo", "wilson_hi",
                        "binomial_p", "holm_p", "proper_score_status", "certified"])
        + "<h3>Staking board</h3>"
        + render_table("t-stak", stak,
                       ["family_id", "division", "n", "stake", "roi", "clv", "drawdown", "status"]))

    # ---------------- correlations ----------------
    add("correlations.html", "Correlations",
        "Only correlations whose inputs are official are published. Third-party aggregator values "
        "are withheld and listed separately with n and tier.",
        kpi([(len(rows_of("correlations.csv")), "published"),
             (len(rows_of("correlations_withheld.csv")), "withheld")])
        + render_table("t-corr", rows_of("correlations.csv"),
                       ["correlation_id", "variable_a", "variable_b", "n", "r", "ci95_lo",
                        "ci95_hi", "input_tier", "inputs"])
        + "<h3>Withheld</h3>"
        + '<p class="lead">These numbers exist elsewhere in this repository. They are not reproduced '
          'as usable values because their inputs are an aggregator, not an official source, or '
          'because no source exists at all.</p>'
        + render_table("t-wit", rows_of("correlations_withheld.csv"),
                       ["id", "quantity", "value_published_elsewhere", "n_published_elsewhere",
                        "input_tier", "published_by", "why_withheld"],
                       source_label="WITHHELD — the input is not an official source"))

    # ---------------- luck ----------------
    add("luck.html", "Removal of luck",
        "How much of each club's record survives a luck test, and how big a sample a real edge "
        "needs before it can be distinguished from noise.",
        kpi([("32", "clubs"), ("2.37", "Pythagorean exponent (a modelling choice, F-14)"),
             (rep["official_finals"], "games in the sample")])
        + '<div class="callout warn">The Pythagorean exponent of 2.37 is an industry convention, not '
          'a league-published number. It is labelled as a modelling choice everywhere it is used.</div>'
        + render_table("t-luck", rows_of("luck_panel.csv"),
                       ["team", "club", "games", "actual_wins", "actual_win_pct",
                        "pythagorean_expected_wins", "luck_wins_actual_minus_expected",
                        "close_game_share", "binomial_sd_wins", "binomial_95_low",
                        "binomial_95_high", "inside_the_noise_band"])
        + "<h3>How much evidence is enough?</h3>"
        + render_table("t-power", rows_of("luck_power.csv"),
                       ["true_hit_rate", "bets_to_demonstrate_skill_80pct_power",
                        "chance_a_coin_flip_shows_55pct_over_200_bets", "note"]))

    # ---------------- flagged ----------------
    add("flagged.html", "Flagged for review",
        "Every irregularity and every value we could not confirm, with the source link and the "
        "action that would clear it.",
        kpi([(len(flagged), "flags"), (len(blocking), "blocking"),
             (sum(1 for f in flagged if f["severity"] == "review"), "review"),
             (sum(1 for f in flagged if f["severity"] == "non-blocking"), "non-blocking")])
        + render_table("t-flagged", flagged,
                       ["flag_id", "severity", "area", "title", "detail", "consequence", "action",
                        "status"]))

    # ---------------- sources ----------------
    add("sources.html", "Sources",
        "Every page this desk read, when it was read, what it was used for, and how many rows it "
        "contributed.",
        render_table("t-src", rows_of("sources.csv"),
                     ["source_id", "publisher", "title", "url", "tier", "fetched_utc", "used_for",
                      "rows_contributed", "verification_status"])
        + "<h3>Capture ledger</h3>"
        + '<p class="lead">SHA-256 of every official capture held in <code>data/official/</code>.</p>'
        + render_table("t-man", rows_of("manifest.csv"),
                       ["path", "bytes", "sha256", "captured"],
                       source_label="LEDGER ROW — the hash is the provenance"))

    # ---------------- audit ----------------
    audit = rows_of("repo_audit.csv")
    add("audit.html", "Repo audit",
        "Line by line: every claim carried forward from an earlier session, re-checked against the "
        "official source today.",
        kpi([(len(audit), "checks"), (rep["audit_matched"], "matched"),
             (sum(1 for r in audit if r["result"].startswith("DIFFERS - FULLY EXPLAINED")),
              "differed, fully explained"),
             (sum(1 for r in audit if r["result"].startswith("CHANGED BETWEEN")),
              "changed between two official reads")])
        + render_table("t-audit", audit,
                       ["check_id", "area", "claim", "official_value_today",
                        "carried_forward_value", "result", "interpretation"]))

    # ---------------- verification ----------------
    add("verification.html", "How this desk verifies",
        "The rules this desk is held to, and what is re-proven on every build.",
        '<div class="callout"><strong>Rule 1.</strong> Every body row on every page ends in a source '
        'cell: a link to the official page the value was read from, or an explicit UNVERIFIED badge. '
        '<code>verify.py</code> walks the generated HTML — not the CSVs — and fails the build if a '
        'row has neither.</div>'
        '<div class="callout"><strong>Rule 2.</strong> A value that cannot be confirmed from an '
        'official source is left blank and flagged. It is never inferred, never averaged in and '
        'never carried over from a third party.</div>'
        '<div class="callout"><strong>Rule 3.</strong> The whole desk rebuilds deterministically from '
        'the pinned captures. Running the build twice must produce byte-identical output, and the '
        'committed artefacts must match, so a silent drift fails the workflow.</div>'
        '<div class="callout"><strong>Rule 4.</strong> Internal links are checked. A page that links '
        'to a page that was not generated fails the build.</div>'
        + "<h3>What is checked on this build</h3>"
        + kpi([(rep["audit_checks"], "line-by-line checks"),
               (rep["spotcheck_games"], "feed rows re-read from official pages"),
               (rep["injury_sample_checked"], "injury rows re-read"),
               (f"{rep['std_exact']}/32", "clubs reconciled to the standings")])
        + "<h3>Capture ledger</h3>"
        + render_table("t-man2", rows_of("manifest.csv"), ["path", "bytes", "sha256", "captured"],
                       source_label="LEDGER ROW — the hash is the provenance"))

    return pages


def render(manifest: dict):
    pages = build_pages(manifest)
    for name, html_text in pages.items():
        (ROOT / name).write_text(html_text, encoding="utf-8")
    return sorted(pages)

#!/usr/bin/env python3
"""Deterministic static-site builder for desk 6cbf25fa (NFL Price & Ledger Desk).

No network, no clock, no git: every timestamp shown on a page comes from a
committed data file (read_utc / opened_utc).  Pages are plain HTML + one CSS
file; no JavaScript is required to read any content.
"""
import csv
import hashlib
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
D = os.path.join(ROOT, "data", "nfl-desk-6cbf25fa")
OUT = HERE


def e(v):
    return html.escape(str(v), quote=True)


def read_csv_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


REPO_BLOB = "https://github.com/sassnarep3-star/Own5/blob/main/"


def linkify(url):
    """Repo-relative paths must become absolute GitHub blob URLs, otherwise
    they resolve relative to the desk directory on Pages and break (R17-class
    defect found live after the first deploy)."""
    u = (url or "").strip()
    if not u:
        return u
    if u.startswith("http://") or u.startswith("https://") or u.startswith("#"):
        return u
    return REPO_BLOB + u


def blank_td(flag):
    return f'<td class="blank" title="Unverified or intentionally withheld: {e(flag)}">— <span class="flagref">{e(flag)}</span></td>'


def table(caption, headers, rows, cls="data"):
    head = "".join(f"<th scope='col'>{e(h)}</th>" for h in headers)
    body = "".join(f"<tr>{''.join(str(c) for c in r)}</tr>" for r in rows)
    return (f'<div class="tablewrap"><table class="{cls}"><caption>{e(caption)}</caption>'
            f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")


NAV = [
    ("index.html", "Home & decision readiness"),
    ("lines.html", "Week 11 originated lines"),
    ("snapshots.html", "Price-snapshot store"),
    ("ratings.html", "Model, inputs & ratings"),
    ("results.html", "Verified results & standings"),
    ("ledger.html", "Injury point-in-time ledger"),
    ("suggestions.html", "Suggestions (for review)"),
    ("questions.html", "Questions & missing information"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources"),
]


def page(title, h1, lead, body, active):
    nav = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{e(label)}</a>'
        for href, label in NAV)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · NFL Price &amp; Ledger Desk (6cbf25fa)</title>
<link rel="stylesheet" href="style.css"></head>
<body>
<header class="top">
  <div class="brand">NFL PRICE &amp; LEDGER DESK <span class="sid">session 6cbf25fa</span></div>
  <div class="stamp">Reads stamped 2026-11-18 · repository <a href="https://github.com/sassnarep3-star/Own5">sassnarep3-star/Own5</a></div>
</header>
<nav class="nav">{nav}</nav>
<main>
  <h1>{e(h1)}</h1>
  <p class="lead">{lead}</p>
  {body}
</main>
<footer>
  <p>Blank cells are unverified or intentionally withheld — they are never filled in. Every row links to an official source or carries a flag id published on the <a href="flagged.html">Flagged for Review</a> page.</p>
  <p>Research only. Nothing here is a recommendation to bet; no rewards, staking or ROI claims are made from this desk.</p>
</footer>
</body></html>
"""


def badge(text, cls):
    return f'<span class="badge {cls}">{e(text)}</span>'


def status_badge(status):
    s = status.lower()
    if s.startswith("met") or s.startswith("fixed") or s.startswith("resolved"):
        return badge(status, "ok")
    if s.startswith("unmet") or s.startswith("blocking"):
        return badge(status, "bad")
    return badge(status, "warn")


def build_index():
    ready = read_csv_rows(os.path.join(D, "readiness.csv"))
    rows = []
    for r in ready:
        rows.append("".join([
            f"<td><strong>{e(r['id'])}</strong></td>",
            f"<td>{e(r['requirement'])}</td>",
            f"<td>{status_badge(r['status'])}</td>",
            f"<td>{e(r['blocking_gate'])}</td>",
            f"<td>{e(r['number_to_clear'])}</td>",
            f"<td>{e(r['observed_number'])}</td>",
            f"<td><a href=\"{e(linkify(r['source_url']))}\">source ↗</a></td>",
        ]))
    model = read_json(os.path.join(D, "model_inputs.json"))
    r = model["ratings"]
    body = f"""
<section class="cards">
  <div class="card"><div class="k">Corpus</div><div class="v">{model['corpus_games']} games</div><div class="s">verified finals weeks 1-10</div></div>
  <div class="card"><div class="k">Markets originated</div><div class="v">39</div><div class="s">13 games × side/total/ML, opened 2026-11-18</div></div>
  <div class="card"><div class="k">Standings cross-check</div><div class="v">0 mismatches</div><div class="s">32 clubs vs game-derived records</div></div>
  <div class="card"><div class="k">Injury deltas</div><div class="v">456</div><div class="s">between 2026-11-12 and 2026-11-18 reads</div></div>
</section>
<section>
<h2>Decision-readiness table</h2>
<p>One row per requirement this desk touches or inherits: the gate that blocks it and the number that would clear it. Inherited blockers are marked with their owner scope. (Replaces nothing: the origin desk's 80-row table remains authoritative for its own scope.)</p>
{table("Decision readiness: requirement → blocking gate → number to clear → observed", ["Req", "Requirement", "Status", "Blocking gate", "Number to clear", "Observed", "Evidence"], rows)}
</section>
<section>
<h2>Model summary (pre-registered spec v1)</h2>
{table("Frozen estimates published with their sample size", ["Estimate", "Value", "n", "Note"], [
  ["League mean points / team-game", f"{r['league_mean_points_per_team_game']:.2f}", model['corpus_games'], "weeks 1-10 finals"],
  ["Home-field advantage (one-pass)", f"{r['hfa_points']:+.2f} pts", r['hfa_n_home_games'], "location=Home games; ±2σ band includes 0 (F-P08)"],
  ["Residual σ", f"{r['sigma_points']:.2f} pts", r['sigma_n_games'], "margin residuals, all games"],
  ["Empirical tie rate", f"{r['tie_rate']:.4f}", model['corpus_games'], f"ties observed: {r['ties']}"],
])}
<p class="note">Spec: <a href="https://github.com/sassnarep3-star/Own5/blob/main/research/nfl-6cbf25fa/model_spec.md">research/nfl-6cbf25fa/model_spec.md</a> (sha256 <code>{model['spec_sha256'][:16]}…</code>, recorded in model_inputs.json). Inputs: <a href="https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-desk-6cbf25fa/model_inputs.json">model_inputs.json</a>.</p>
</section>"""
    return page("Home", "NFL Price & Ledger Desk",
                "Session 6cbf25fa. Own prices, immutable snapshots, deltas not levels. Built from officially sourced numbers only; every row source-linked or blank-and-flagged.",
                body, "index.html")


def build_lines():
    lines = read_csv_rows(os.path.join(D, "lines_week11.csv"))
    by_game = {}
    for ln in lines:
        by_game.setdefault((ln["game_id"], ln["away_team"], ln["home_team"], ln["neutral_site"],
                            ln["kickoff_as_printed"], ln["network_as_printed"], ln["official_game_url"]), []).append(ln)
    rows = []
    for (gid, a, h, neu, ko, net, url), ms in sorted(by_game.items()):
        m = {x["market_type"]: x for x in ms}
        side, tot, ml = m["side"], m["total"], m["moneyline"]
        neu_cell = " <span class='flagref'>neutral site</span>" if neu == "yes" else ""
        rows.append("".join([
            f"<td><a href='{e(url)}'>{e(a)} @ {e(h)}</a>{neu_cell}</td>",
            f"<td>{e(ko)} {e(net)}</td>",
            f"<td>{e(side['fair_value_rounded'])} <span class='un'>(fair {float(side['fair_value_unrounded']):+.2f})</span></td>",
            f"<td>{e(tot['fair_value_rounded'])} <span class='un'>(fair {float(tot['fair_value_unrounded']):.2f})</span></td>",
            f"<td>{e(ml['fair_value_rounded'])} / {e((ml['notes'].split('away (American) = ')[1] if 'away (American) = ' in ml['notes'] else '').split(';')[0])}</td>",
            f"<td>{float(ml['p_home_win']):.3f} / {float(ml['p_away_win']):.3f} / {float(ml['p_push']):.3f}</td>",
            blank_td("market line: F-P01"),
            blank_td("residual: F-P01"),
            f"<td><a href='https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-desk-6cbf25fa/model_inputs.json'>inputs ↗</a></td>",
        ]))
    body = f"""
<p class="lead-in">Fair lines originated 2026-11-18T03:55:13Z under the frozen spec (side → total → moneyline).
<mark>The Week 11 official injury report had not been published at read time (F-P02), so these lines are availability-blind.</mark>
Market and residual columns are blank and flagged — there is no verified operator price source (F-P01); they are never inferred.</p>
{table("Week 11 originated markets (39 rows in lines_week11.csv; 13 games × 3 markets)", ["Game (official)", "Kickoff / net", "Fair spread (rounded, unrounded)", "Fair total", "Fair ML home / away", "p home / away / push", "Market line", "Residual", "Inputs"], rows)}
<p class="note">Every market row also exists as an immutable opening snapshot on the <a href="snapshots.html">price-snapshot store</a> page. Rounding: side/total to nearest 0.5 (halves away from zero); ML to integer American odds (F-P12).</p>"""
    return page("Week 11 originated lines", "Week 11 originated lines — fair first, market blank",
                "The model's fair number is published. The market's number is not (no verified source). The difference is therefore blank, not zero.",
                body, "lines.html")


def build_snapshots():
    snaps = read_csv_rows(os.path.join(D, "price_snapshots.csv"))
    sums = {}
    for l in open(os.path.join(HERE, "raw", "SHA256SUMS.txt")).read().strip().splitlines():
        h, name = l.split()
        sums[name] = h
    rows = []
    for s in snaps:
        rows.append("".join([
            f"<td><code>{e(s['market_id'])}</code></td>",
            f"<td>{e(s['away_team'])} @ {e(s['home_team'])}</td>",
            f"<td>{e(s['market_type'])} {e(s['direction'])}</td>",
            f"<td>{e(s['opened_utc'])}</td>",
            f"<td>{e(s['opening_fair_rounded'])}</td>",
            blank_td("closing: pending (game not completed)"),
            f"<td>{badge(s['status'], 'warn')}</td>",
            f"<td><code>{e(s['inputs_sha256'][:12])}…</code></td>",
        ]))
    raw_rows = table("SHA256SUMS of this desk's official-source extracts", ["Extract file", "SHA256"],
                     [[f"<code>{e(name)}</code>", f"<code>{e(h)}</code>"] for name, h in sorted(sums.items())])
    body = f"""
<section>
<h2>Policy (frozen in the pre-registered spec)</h2>
<ul>
<li>One immutable row per market we originate, written at origination time with <code>opened_utc</code>.</li>
<li>Closing columns stay blank until the game completes; closings come only from official results and never from inference. Status changes <code>open → closed</code> only then.</li>
<li>Market prices are separate columns and stay blank until a verified operator source exists (F-P01).</li>
<li>Every row references <code>inputs_sha256</code> — the exact frozen inputs (ratings, HFA, σ, tie rate, corpus n) behind the opening number.</li>
</ul>
{table("Price-snapshot store — opening capture (data/nfl-desk-6cbf25fa/price_snapshots.csv)", ["Market id", "Game", "Market", "Opened (UTC)", "Opening fair (rounded)", "Closing fair", "Status", "Inputs sha"], rows)}
</section>
<section>
<h2>Capture hashes (extract-level; see F-P09)</h2>
{raw_rows}
<p class="note">Raw extracts live in <a href="https://github.com/sassnarep3-star/Own5/tree/main/nfl-desk-6cbf25fa/raw">nfl-desk-6cbf25fa/raw/</a> with <code>MANIFEST.json</code> (URLs, chunk counts, read stamps).</p>
</section>"""
    return page("Price-snapshot store", "Price-snapshot store — immutable, hashed, closings pending",
                "Openings are frozen now; closings are a post-kickoff event, not a prediction.",
                body, "snapshots.html")


def build_ratings():
    model = read_json(os.path.join(D, "model_inputs.json"))
    r = model["ratings"]
    rows = []
    for t in sorted(r["games_played"], key=lambda x: (-(r["offensive_deviation"][x] - r["defensive_effectiveness"][x]), x)):
        rows.append("".join([
            f"<td><strong>{e(t)}</strong></td>",
            f"<td>{r['offensive_deviation'][t]:+.2f}</td>",
            f"<td>{r['defensive_effectiveness'][t]:+.2f}</td>",
            f"<td>{r['offensive_deviation'][t] - r['defensive_effectiveness'][t]:+.2f}</td>",
            f"<td>{r['games_played'][t]}</td>",
        ]))
    body = f"""
<section>
<h2>Pre-registered specification (v1, frozen)</h2>
<ul>
<li>Corpus: {model['corpus_games']} verified finals — weeks 1-9 from the pinned, sha256-verified nflverse snapshot; week 10 from the official NFL.com scores page read 2026-11-18.</li>
<li>Two opponent-adjustment iterations (recentered); one-pass HFA on location=Home games only (n={r['hfa_n_home_games']}); HFA = 0 at neutral sites (MIN@SF Mexico City confirmed via the official game centre).</li>
<li>σ = residual std of margins over all {r['sigma_n_games']} games; p(home) = Φ(m/σ) scaled by (1 − empirical tie rate).</li>
<li>Week 11 availability is NOT a feature (F-P02). Injury/depth ablation is future work once the report publishes (S-P04/Q-P04).</li>
</ul>
<p class="note">Full spec: <a href="https://github.com/sassnarep3-star/Own5/blob/main/research/nfl-6cbf25fa/model_spec.md">model_spec.md</a> — frozen before any Week 11 result exists. Changing it requires a new version and a new snapshot.</p>
</section>
<section>
<h2>Team ratings (opponent-adjusted deviations, points per game vs league mean)</h2>
{table("Ratings stored in model_inputs.json (sha256 recorded on every originated row)", ["Team", "Offensive deviation o", "Defensive effectiveness e", "Net strength o−e", "Games (n)"], rows)}
<p class="note">L (league mean points per team-game) = {r['league_mean_points_per_team_game']:.2f}. Net strength figures are model inputs, not predictions.</p>
</section>"""
    return page("Model & ratings", "Model, inputs & ratings — probability plus inputs",
                "Everything the model used is stored and hashed; nothing is asserted that the corpus cannot support.",
                body, "ratings.html")


def build_results():
    res = read_csv_rows(os.path.join(D, "results_week10.csv"))
    checks = _standings_checks()
    rrows = []
    for g in res:
        winner = g["home_team"] if int(g["home_score"]) > int(g["away_score"]) else (
            g["away_team"] if int(g["away_score"]) > int(g["home_score"]) else "TIE")
        rrows.append("".join([
            f"<td><a href='{e(g['source_url'])}'>{e(g['away_team'])} @ {e(g['home_team'])}</a></td>",
            f"<td>{e(g['away_score'])} – {e(g['home_score'])}</td>",
            f"<td>{e(winner)}</td>",
            f"<td>{e(g['printed_section'])}</td>",
            f"<td>{e(g['neutral_site'])}</td>",
        ]))
    crows = []
    for c in checks:
        crows.append("".join([
            f"<td>{e(c['team'])}</td>",
            f"<td>{e(c['page_wlt'])}</td>",
            f"<td>{e(c['computed_wlt'])}</td>",
            f"<td>{badge(c['wlt_match'], 'ok' if c['wlt_match'] == 'yes' else 'bad')}</td>",
            f"<td>{c['page_pf']} / {c['computed_pf']} · {c['page_pa']} / {c['computed_pa']} · {c['page_net']} / {c['computed_net']}</td>",
            f"<td>{badge(c['pf_pa_net_match'], 'ok' if c['pf_pa_net_match'] == 'yes' else 'bad')}</td>",
        ]))
    body = f"""
<section>
<h2>Verified Week 10 results (ingested into the ratings corpus)</h2>
{table("Week 10 finals from the official NFL.com scores page (read 2026-11-18T03:55:13Z)", ["Game", "Final", "Winner", "Printed section", "Neutral site"], rrows)}
<p class="note">Byes as printed on the same page: CHI, DEN, PHI, TB. The Munich game (NE@DET) is printed as an International Game and excluded from HFA.</p>
</section>
<section>
<h2>Standings cross-check (official page vs game-derived records, 32 clubs)</h2>
{table("Every published standings value is verified against the results corpus", ["Team", "Page W-L-T", "Computed W-L-T", "Match", "Page / computed PF · PA · NET", "PF/PA/NET match"], crows)}
<p class="note">Only W-L-T, PCT, PF, PA and NET are published from the standings page; the remaining printed columns are ambiguous (F-P05) and stay raw in the CSV.</p>
</section>"""
    return page("Verified results", "Verified results & standings — the results feed",
                "Week 10 finals are ingested with per-game official links; the standings page is cross-checked line by line against game-derived records.",
                body, "results.html")


def _standings_checks():
    """Recompute the cross-check rows (same logic as pipeline) for the page."""
    import gzip
    rows = list(csv.DictReader(gzip.open(os.path.join(ROOT, "data", "decision-desk", "raw", "games.csv.gz"), "rt")))
    st = {}
    for r in rows:
        if r["season"] != "2026" or r["game_type"] != "REG" or int(r["week"]) > 9 or r["home_score"] == "":
            continue
        h, a = ("LAR" if r["home_team"] == "LA" else r["home_team"]), ("LAR" if r["away_team"] == "LA" else r["away_team"])
        st.setdefault(h, [0, 0, 0, 0, 0])
        st.setdefault(a, [0, 0, 0, 0, 0])
        hs, as_ = int(r["home_score"]), int(r["away_score"])
        st[h][3] += hs; st[h][4] += as_; st[a][3] += as_; st[a][4] += hs
        st[h][0 if hs > as_ else 2 if hs == as_ else 1] += 1
        st[a][0 if as_ > hs else 2 if hs == as_ else 1] += 1
    for g in read_csv_rows(os.path.join(D, "results_week10.csv")):
        h = "LAR" if g["home_team"] == "LA" else ("ARI" if g["home_team"] == "AZ" else g["home_team"])
        a = "LAR" if g["away_team"] == "LA" else ("ARI" if g["away_team"] == "AZ" else g["away_team"])
        st.setdefault(h, [0, 0, 0, 0, 0]); st.setdefault(a, [0, 0, 0, 0, 0])
        hs, as_ = int(g["home_score"]), int(g["away_score"])
        st[h][3] += hs; st[h][4] += as_; st[a][3] += as_; st[a][4] += hs
        st[h][0 if hs > as_ else 2 if hs == as_ else 1] += 1
        st[a][0 if as_ > hs else 2 if hs == as_ else 1] += 1
    out = []
    for r in read_csv_rows(os.path.join(D, "standings_2026-11-18.csv")):
        code = {"LA": "LAR", "AZ": "ARI"}.get(r["team_code"], r["team_code"])
        cells = r["raw_cells_as_printed"].split(" | ")
        w, l, t = int(cells[0]), int(cells[1]), int(cells[2])
        pf, pa, net = int(cells[4]), int(cells[5]), int(cells[6])
        c = st.get(code, [0, 0, 0, 0, 0])
        out.append({
            "team": code,
            "page_wlt": f"{w}-{l}-{t}", "computed_wlt": f"{c[0]}-{c[1]}-{c[2]}",
            "wlt_match": "yes" if (w, l, t) == (c[0], c[1], c[2]) else "NO",
            "page_pf": pf, "computed_pf": c[3], "page_pa": pa, "computed_pa": c[4],
            "page_net": net, "computed_net": c[3] - c[4],
            "pf_pa_net_match": "yes" if (pf, pa, net) == (c[3], c[4], c[3] - c[4]) else "NO",
        })
    return out


def build_ledger():
    reads = read_csv_rows(os.path.join(D, "injury_reads", "reads.csv"))
    deltas = read_csv_rows(os.path.join(D, "injury_reads", "deltas_2026-11-12_to_2026-11-18.csv"))
    counts = {}
    for d in deltas:
        counts[d["change_type"]] = counts.get(d["change_type"], 0) + 1
    rrows = []
    for r in reads:
        rrows.append("".join([
            f"<td><strong>{e(r['read_id'])}</strong></td>",
            f"<td><code>{e(r['captured_utc'])}</code></td>",
            f"<td>{e(r['row_count'])}</td>",
            f"<td>{e(r['teams_in_capture'])}</td>",
            f"<td>{e(r['captured_by'])}</td>",
            f"<td>{e(r['storage'])}</td>",
            f"<td><a href='{e(r['source_url'])}'>source ↗</a></td>",
        ]))
    from collections import Counter
    dc = Counter(d["change_type"] for d in deltas)
    notable = [d for d in deltas if d["change_type"] == "game_status_changed" and d["value_this_read"] == "Out"]
    nrow_limit = 40
    drows = []
    for d in deltas[:nrow_limit]:
        drows.append("".join([
            f"<td>{e(d['change_type'])}</td>",
            f"<td>{e(d['team_code'])}</td>",
            f"<td>{e(d['player'])}</td>",
            f"<td>{e(d['position'])}</td>",
            f"<td>{e(d['field'])}</td>",
            f"<td>{e(d['value_prior_read']) if d['value_prior_read'] else '—'}</td>",
            f"<td>{e(d['value_this_read']) if d['value_this_read'] else '—'}</td>",
            f"<td><code>{e(d['prior_read_utc'])}</code></td>",
        ]))
    body = f"""
<section>
<h2>Reads (clock-stamped, immutable)</h2>
{table("Two stamped reads currently in the ledger", ["Read", "Captured (UTC)", "Rows", "Teams", "Captured by", "Storage", "Source"], rrows)}
<p class="note">Level data stays in the raw captures; everything published below is a <strong>delta</strong>, never a level. The requested reg11 URL served Week 10 content at read time (F-P02/F-P03).</p>
</section>
<section>
<h2>Deltas between the two reads</h2>
{table("Change counts between 2026-11-12T16:52:39Z and 2026-11-18T03:55:13Z", ["Change type", "Count"], [f"<tr><td>{e(k)}</td><td>{v}</td></tr>" for k, v in sorted(dc.items(), key=lambda kv: -kv[1])])}
<p>Designation-to-<strong>Out</strong> moves between reads: {len(notable)} players. First {nrow_limit} of {len(deltas)} delta rows shown (full file:
<a href="https://github.com/sassnarep3-star/Own5/blob/main/data/nfl-desk-6cbf25fa/injury_reads/deltas_2026-11-12_to_2026-11-18.csv">deltas_2026-11-12_to_2026-11-18.csv</a>):</p>
{table("Player-level deltas (both read stamps on every row)", ["Change", "Team", "Player", "Pos", "Field", "Prior read", "This read", "Prior read (UTC)"], drows)}
</section>"""
    return page("Injury ledger", "Injury point-in-time ledger — deltas, never levels",
                "Every read carries its clock time; every published value is the change between two stamped reads.",
                body, "ledger.html")


def _register_page(fname, title, h1, lead, headers, key_map, note=""):
    rows = []
    for r in read_csv_rows(os.path.join(D, fname)):
        rows.append("".join([
            f"<td><strong>{e(r[key_map[0]])}</strong></td>",
        ] + [f"<td>{e(r[k])}</td>" for k in key_map[1:-1]] + [
            f"<td><a href=\"{e(linkify(r[key_map[-1]]))}\">source ↗</a></td>" if not r[key_map[-1]].startswith("http") else f"<td><a href=\"{e(r[key_map[-1]])}\">source ↗</a></td>",
        ]))
    body = f"{note}{table(title, headers, rows)}"
    return page(title.split('(')[0].strip(), h1, lead, body, fname.replace('.csv', '.html'))


def build_flagged():
    rows = []
    for f in read_csv_rows(os.path.join(D, "flagged.csv")):
        sev_cls = {"BLOCKING": "bad", "REVIEW": "warn"}.get(f["severity"], "warn")
        rows.append("".join([
            f"<td><strong>{e(f['flag_id'])}</strong> {badge(f['severity'], sev_cls)}</td>",
            f"<td>{e(f['issue'])}</td>",
            f"<td>{e(f['finding'])}</td>",
            f"<td>{e(f['affected_scope'])}</td>",
            f"<td>{e(f['status'])}</td>",
            f"<td><a href=\"{e(linkify(f['source_url']))}\">source ↗</a></td>",
            f"<td>{e(f['notes'])}</td>",
        ]))
    body = f"""
<p class="lead-in">Published openly and non-blocking for the merge, per the repository rules. Blocking items gate
<em>decisions</em> (pricing, ranking), not publication of this evidence desk.</p>
{table("Flagged for Review (data/nfl-desk-6cbf25fa/flagged.csv)", ["Flag", "Issue", "Finding", "Scope", "Status", "Source", "Notes"], rows)}"""
    return page("Flagged for Review", "Flagged for Review",
                "Irregularities and unverified blanks, with sources, so review can happen after publication.",
                body, "flagged.html")


def build_sources():
    rows = []
    for s in read_csv_rows(os.path.join(D, "sources.csv")):
        rows.append("".join([
            f"<td><strong>{e(s['s_id'])}</strong></td>",
            f"<td>{e(s['publisher'])}</td>",
            f"<td>{e(s['description'])}</td>",
            f"<td><a href='{e(s['url'])}'>{e(s['url'])}</a></td>",
            f"<td><code>{e(s['read_utc'])}</code></td>",
            f"<td>{e(s['used_for'])}</td>",
        ]))
    body = table("Source register (data/nfl-desk-6cbf25fa/sources.csv)", ["Id", "Publisher", "Description", "URL", "Read (UTC)", "Used for"], rows)
    return page("Sources", "Sources — every read, stamped",
                "Official publishers only for league facts; the pinned nflverse snapshot is marked as an aggregator and hash-verified.",
                body, "sources.html")


def build_suggestions():
    rows = []
    for s in read_csv_rows(os.path.join(D, "suggestions.csv")):
        rows.append("".join([
            f"<td><strong>{e(s['s_id'])}</strong></td>",
            f"<td>{e(s['problem'])}</td>",
            f"<td>{e(s['recommendation'])}</td>",
            f"<td>{e(s['expected_impact_on_decisions'])}</td>",
            f"<td>{e(s['effort'])}</td>",
            f"<td>{e(s['confidence'])}</td>",
            f"<td>{badge(s['decision_status'], 'warn')}</td>",
            f"<td><a href=\"{e(linkify(s['source_url']))}\">evidence ↗</a></td>",
        ]))
    body = f"""
<p class="lead-in">Reviewable before implementation: each suggestion names the problem, the change, its expected
effect on decision-making, cost and confidence. <strong>None is implemented outside this desk's namespace;
each needs an owner session to claim it in COORDINATION.md.</strong></p>
{table("Suggestions register (for review)", ["Id", "Problem", "Recommendation", "Expected impact on decisions", "Effort", "Confidence", "State", "Evidence"], rows)}"""
    return page("Suggestions", "Suggestions — reviewed before any change",
                "Improvements for decision-making, each with problem, proposal, impact, effort and confidence.",
                body, "suggestions.html")


def build_questions():
    rows = []
    for q in read_csv_rows(os.path.join(D, "questions.csv")):
        rows.append("".join([
            f"<td><strong>{e(q['q_id'])}</strong></td>",
            f"<td>{e(q['question'])}</td>",
            f"<td>{e(q['why_it_blocks_decisions'])}</td>",
            f"<td>{e(q['information_needed'])}</td>",
            f"<td>{e(q['where_to_get_it_officially'])}</td>",
            f"<td>{badge(q['status'], 'warn')}</td>",
            f"<td><a href=\"{e(linkify(q['source_url']))}\">source ↗</a></td>",
        ]))
    body = f"""
<p class="lead-in">The clear list of questions, information and answers that must be addressed before a decision can
reasonably be made from what we have — and do not have. Each question names where the missing information can be
sourced officially.</p>
{table("Questions &amp; missing information register", ["Id", "Question", "Why it blocks decisions", "Information needed", "Where to get it officially", "Status", "Source"], rows)}"""
    return page("Questions", "Questions & missing information",
                "What we do not know, why it blocks a decision, and where the answer must come from.",
                body, "questions.html")


PAGES = {
    "index.html": build_index,
    "lines.html": build_lines,
    "snapshots.html": build_snapshots,
    "ratings.html": build_ratings,
    "results.html": build_results,
    "ledger.html": build_ledger,
    "flagged.html": build_flagged,
    "sources.html": build_sources,
    "suggestions.html": build_suggestions,
    "questions.html": build_questions,
}


def main():
    written = []
    for name, fn in PAGES.items():
        p = os.path.join(OUT, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(fn())
        written.append(name)
    print(f"wrote {len(written)} pages: {', '.join(written)}")


if __name__ == "__main__":
    main()

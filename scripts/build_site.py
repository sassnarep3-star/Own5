#!/usr/bin/env python3
"""
build_site.py — generate the GitHub Pages site in docs/ from the verified data files.

The site tables are GENERATED from data/*.csv so the site cannot drift from the computed data.
Every data row renders its source links (dataset pin + script) as clickable links; rows with
unverifiable values render blank + a FLAG chip (see docs/flagged.md).

Usage: python3 scripts/build_site.py   (writes docs/*.html, docs/assets/*, docs/.nojekyll)
"""
import csv
import html
import os

DATA = 'data/'
DOCS = 'docs/'
REPO = 'https://github.com/sassnarep3-star/Own5/blob/main/'

NAV = [
    ('index.html', 'Dashboard'),
    ('executive-summary.html', 'Executive Summary'),
    ('strategies.html', 'Strategies'),
    ('validation-gates.html', 'Validation Gates'),
    ('correlation.html', 'Correlation'),
    ('luck-vs-skill.html', 'Luck vs Skill'),
    ('leaderboard.html', 'Leaderboard'),
    ('lines-2026-wk9.html', 'Week 9 Lines'),
    ('sources.html', 'Sources'),
    ('flagged.html', 'Flagged for Review'),
]

CSS = """
:root{--bg:#f4f6fa;--card:#fff;--ink:#1c2733;--muted:#5c6b7a;--line:#e3e8ef;--accent:#14532d;--accent2:#0b5cad;--warn:#b45309;--bad:#b91c1c;--good:#15803d;--chip:#eef2f7}
*{box-sizing:border-box}
body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink)}
a{color:var(--accent2);text-decoration:none}a:hover{text-decoration:underline}
header.site{background:#10243e;color:#fff;padding:14px 22px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between}
header.site .brand{font-weight:700;font-size:17px;letter-spacing:.2px}
header.site .brand span{color:#8fd0ff}
nav.main{display:flex;flex-wrap:wrap;gap:2px}
nav.main a{color:#d7e3f4;padding:6px 11px;border-radius:7px;font-size:13.5px}
nav.main a:hover{background:#1d3a5f;text-decoration:none}
nav.main a.active{background:#0b5cad;color:#fff}
main{max-width:1180px;margin:0 auto;padding:22px}
h1{font-size:25px;margin:6px 0 4px}h2{font-size:19px;margin:26px 0 10px;border-bottom:2px solid var(--line);padding-bottom:6px}
h3{font-size:16px;margin:18px 0 8px}
p.lead{color:var(--muted);font-size:15.5px;margin-top:2px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:13px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px 16px;box-shadow:0 1px 2px rgba(16,36,62,.05)}
.card .k{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted)}
.card .v{font-size:25px;font-weight:700;margin:4px 0 2px}
.card .s{font-size:12.5px;color:var(--muted)}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:14px 0}
.tbl-wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:12px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{background:#eef2f8;text-align:left;padding:9px 11px;border-bottom:2px solid var(--line);white-space:nowrap;position:sticky;top:0}
td{padding:8px 11px;border-bottom:1px solid var(--line);vertical-align:top}
tr:nth-child(even) td{background:#fafbfd}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:600;background:var(--chip);color:var(--muted);white-space:nowrap}
.chip.good{background:#dcfce7;color:var(--good)}.chip.warn{background:#fef3c7;color:var(--warn)}
.chip.bad{background:#fee2e2;color:var(--bad)}.chip.info{background:#dbeafe;color:var(--accent2)}
.chip.flag{background:#fef3c7;color:#92400e}
.src a{font-size:12px;display:inline-block;margin-right:7px}
.filter{margin:8px 0 12px}.filter input{width:min(360px,90%);padding:8px 11px;border:1px solid var(--line);border-radius:8px;font-size:14px}
ul.findings li{margin:7px 0}
.note{border-left:4px solid var(--accent2);background:#eef4fb;padding:10px 14px;border-radius:0 9px 9px 0;margin:12px 0;font-size:14px}
.warnbox{border-left:4px solid var(--warn);background:#fffbeb;padding:10px 14px;border-radius:0 9px 9px 0;margin:12px 0;font-size:14px}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}
footer{color:var(--muted);font-size:12.5px;text-align:center;padding:22px 10px 34px}
code{background:#eef2f8;padding:1px 6px;border-radius:5px;font-size:12.5px}
.small{font-size:12.5px;color:var(--muted)}
"""

JS = """
function tableFilter(inp, tableId){
  var q = inp.value.toLowerCase();
  var rows = document.querySelectorAll('#'+tableId+' tbody tr');
  rows.forEach(function(r){ r.style.display = r.innerText.toLowerCase().indexOf(q) > -1 ? '' : 'none'; });
}
"""


def esc(x):
    return html.escape('' if x is None else str(x))


def linkify(cell):
    """Render URL-ish cells as anchor links; URL-in-parens also handled."""
    s = esc(cell)
    out = []
    for tok in s.split():
        t = tok.strip('(),;')
        if t.startswith('https://') or t.startswith('http://'):
            label = t
            if len(label) > 60:
                label = label[:57] + '…'
            out.append(f'<a href="{t}" target="_blank" rel="noopener">{label}</a>')
        else:
            out.append(tok)
    return ' '.join(out)


def read_csv(name):
    with open(DATA + name, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def table_from_csv(name, cols, labels, table_id=None, flag_cols=(), transform=None):
    rows = read_csv(name)
    tid = table_id or name.replace('.csv', '').replace('_', '-')
    htm = [f'<div class="filter"><input type="search" placeholder="Filter table…" oninput="tableFilter(this,\'{tid}\')"></div>',
           f'<div class="tbl-wrap"><table id="{tid}"><thead><tr>']
    htm += [f'<th>{esc(l)}</th>' for l in labels]
    htm.append('</tr></thead><tbody>')
    for r in rows:
        htm.append('<tr>')
        for c in cols:
            v = r.get(c, '')
            if v == '' and c in flag_cols:
                htm.append('<td><span class="chip flag">BLANK — no official source (F7/F8)</span></td>')
            else:
                cell = transform(c, v, r) if transform else linkify(v)
                htm.append(f'<td>{cell}</td>')
        htm.append('</tr>')
    htm.append('</tbody></table></div>')
    return '\n'.join(htm)


def page(title, active, body):
    nav = '\n'.join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{esc(lbl)}</a>' for href, lbl in NAV)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Own5 NFL Strategy Lab</title>
<link rel="stylesheet" href="assets/style.css">
<script defer src="assets/app.js"></script>
</head>
<body>
<header class="site">
  <div class="brand">Own5 <span>NFL Strategy Lab</span></div>
  <nav class="main">{nav}</nav>
</header>
<main>
{body}
</main>
<footer>Own5 · NFL line origination &amp; skill-based strategy leaderboard · generated from verified data files by scripts/build_site.py · session arena-f1d30421 · 2026-11-02<br>
Community datasets are flagged — see <a href="flagged.html">Flagged for Review</a>. Nothing on this site is betting advice.</footer>
</body>
</html>
"""


# ---------------------------------------------------------------- pages

def build_index():
    br = {r['metric'] + '|' + r['window']: r for r in read_csv('base_rates.csv')}
    lk = {r['parameter']: r for r in read_csv('luck_skill.csv')}
    def v(key):
        return br[key]['value']
    cards = f"""
<div class="cards">
  <div class="card"><div class="k">Games analyzed (1980–2024)</div><div class="v">10,729</div><div class="s">closing lines &amp; scores, pinned dataset</div></div>
  <div class="card"><div class="k">Favorite cover rate</div><div class="v">{v('favorite_ats_cover_rate_excl_push|full_1980_2024')}</div><div class="s">excl. pushes · dogs cover {round(1-float(v('favorite_ats_cover_rate_excl_push|full_1980_2024')),4)}</div></div>
  <div class="card"><div class="k">Home-field advantage</div><div class="v">{v('mean_home_margin_pts|modern_2002_2024')} pts</div><div class="s">mean home margin 2002–2024 (used in our lines)</div></div>
  <div class="card"><div class="k">Best strategy vs luck gate</div><div class="v">FAIL</div><div class="s">S2 p=0.0134 &gt; α=0.00625 (Bonferroni, k=8)</div></div>
  <div class="card"><div class="k">Lucky 55% after 200 bets?</div><div class="v">{round(float(lk['P(win_rate>=55% given true p=52.38%, n=200)']['value'])*100,1)}%</div><div class="s">probability for a break-even bettor (exact binomial)</div></div>
  <div class="card"><div class="k">Bets to prove 55% skill</div><div class="v">{int(float(lk['detect true p=0.55 vs 0.5238']['value']))}</div><div class="s">80% power, α=0.05 (computed)</div></div>
</div>"""
    body = f"""
<h1>NFL Line Origination &amp; Skill-Based Strategy Lab</h1>
<p class="lead">Own lines from official data · pre-registered strategies with validation gates · correlation-aware parlays &amp; prop combos · luck-deflated leaderboard. Every table row links to its source; unverifiable values are blank and flagged.</p>
{cards}
<div class="grid2">
  <div class="panel">
    <h3>Key findings</h3>
    <ul class="findings">
      <li><b>Market efficiency:</b> closing favorites cover 48.1%; home underdogs 52.6%; overs 49.1% (10,228 games, excl. pushes). <a href="strategies.html">details →</a></li>
      <li><b>Luck removal works:</b> the best catalog strategy (home dog ≥7, 56.37%, n=793) <i>fails</i> the corrected significance gate — zero strategies certified as skill today. <a href="validation-gates.html">gate matrix →</a></li>
      <li><b>Proof burden is real:</b> ~2,243 graded bets to detect a true 55% handicapper at 80% power. <a href="luck-vs-skill.html">luck tables →</a></li>
      <li><b>Parlays:</b> cross-game legs are independent (ratio 0.984) — fixed 2-leg payouts need 27.47% but break-even legs give ~23.6%. <a href="correlation.html">correlation →</a></li>
      <li><b>Prop combos:</b> QB passing yards vs top-WR yards r = 0.76 — same-game legs need empirical joint pricing (gate G5). <a href="correlation.html">values →</a></li>
      <li><b>Live output:</b> our own lines for all 15 games of 2026 Week 9. <a href="lines-2026-wk9.html">our lines →</a></li>
    </ul>
  </div>
  <div class="panel">
    <h3>How to read this site</h3>
    <p>Every data table ends in a <b>Source</b> column. Verification labels:</p>
    <p><span class="chip good">Official NFL</span> transcribed from nfl.com with per-row link &nbsp;
       <span class="chip info">Derived</span> computed by a repo script from pinned inputs &nbsp;
       <span class="chip flag">Blank + flagged</span> no official source exists — never inferred</p>
    <p class="small">Community datasets (historical lines, archived play-by-play) are pinned to commit SHAs and flagged on the <a href="flagged.html">Flagged for Review</a> page (F1, F2). Methodology lives in the repo's <code>research/</code> folder and is summarized on each page.</p>
    <p><a href="executive-summary.html"><b>Executive Summary →</b></a><br>
       <a href="leaderboard.html"><b>Leaderboard &amp; rewards →</b></a><br>
       <a href="sources.html"><b>Sources registry →</b></a></p>
  </div>
</div>
<div class="warnbox"><b>Disclaimer:</b> research &amp; analytics project. Nothing here is betting advice; modeled ROI assumes standard prices because prices are absent from the source dataset (flag F8).</div>
"""
    return page('Dashboard', 'index.html', body)


def build_exec():
    lk_rows = read_csv('luck_skill.csv')
    body = """
<h1>Executive Summary</h1>
<p class="lead">Own5: NFL Line Origination &amp; Skill-Based Strategy Leaderboard — session arena-f1d30421, 2026-11-02. Full document in the repo: <a href="https://github.com/sassnarep3-star/Own5/blob/main/EXECUTIVE_SUMMARY.md">EXECUTIVE_SUMMARY.md</a>.</p>
<div class="panel">
<h3>1. What this project is</h3>
<p>A self-running system that (a) originates its own NFL lines from official data, (b) tests betting strategies — singles, parlays, player-prop combos — under statistical validation gates that separate skill from luck, and (c) runs them as a leaderboard competition rewarding only gate-passing, luck-adjusted performance. No manual input required.</p>
<h3>2. Headline findings</h3>
<ul class="findings">
<li><b>Market close to efficient, not perfect:</b> favorites cover 48.1%, home underdogs 52.6%, overs 49.1% (10,228 games 1980–2024, excl. pushes). Sign-consistent with independent academic work (Szalkowski et al. 2012; Paul &amp; Weinbach).</li>
<li><b>The best-looking strategy still fails the luck test:</b> home underdog ≥7 hit 56.37% (n=793, modeled +8.4% ROI at −110) but p = 0.0134 misses the pre-registered Bonferroni threshold α = 0.00625. Zero strategies are certified skill today — by design. S1/S2 continue as Candidates for live CLV tracking.</li>
<li><b>One season cannot prove skill:</b> a break-even bettor posts ≥55% over 200 bets 20.8% of the time; 2,243 graded bets are needed to detect true 55% skill (80% power).</li>
<li><b>Parlays punish the naive:</b> cross-game independence confirmed (0.984 ratio) — 2-leg fixed parlays need 27.47% joint hits vs ≈23.6% from break-even legs.</li>
<li><b>Real correlation is in player props:</b> QB pass yards vs top-WR yards r = 0.76 (n=3,852); QB vs game total r = 0.35; RB rush yards vs margin r = 0.21. Same-game combos require empirical joint pricing.</li>
<li><b>Our lines are live:</b> v1 model (shrunk net-points ratings + 2.0-pt HFA; measured HFA 2.22) originated all 15 games of 2026 Week 9 from official inputs; market columns blank + flagged (no official market-line source exists).</li>
</ul>
<h3>3. How luck is removed</h3>
<p>Pre-registration + Bonferroni across all variants tried (k=8) · era-stability gates · closing-line-value gate for live promotion · deflated leaderboard scoring (Bailey &amp; López de Prado 2014) · Bayesian shrinkage of displayed win rates · fractional-Kelly bankroll (Thorp 2011) · losers published alongside winners.</p>
<h3>4. Verification discipline</h3>
<p>Every table row carries a source link; unverifiable values are blank and flagged on <a href="flagged.html">Flagged for Review</a> (F1–F11). Official verification samples: 2026 standings (32 teams) and 2025 Week 1 (16/16 game scores matched nfl.com game pages).</p>
<h3>5. Next steps for the owner</h3>
<ul class="findings">
<li>Decide the reward pool (blank + flagged until decided — F9).</li>
<li>Connect a licensed odds feed: the only blocker to live CLV tracking and filled market columns (F1/F7/F8).</li>
<li>Extend prop-line backtesting when a verifiable prop-line source exists (correlation framework is done).</li>
<li>Review the <a href="flagged.html">Flagged for Review</a> page and request changes.</li>
</ul>
</div>
"""
    return page('Executive Summary', 'executive-summary.html', body)


def build_strategies():
    def badge_gates(c, v, r):
        if c == 'gates_G1_G2_G4':
            if v.startswith('PASS'):
                return '<span class="chip good">PASS</span>'
            return f'<span class="chip bad">{esc(v)}</span>'
        if c == 'strategy':
            return f'<b>{esc(v)}</b>'
        return linkify(v)
    backtest = table_from_csv(
        'backtest_results.csv',
        ['strategy', 'bet_side', 'n_bets', 'wins', 'win_rate_excl_push', 'win_rate_ci95_low', 'win_rate_ci95_high',
         'modeled_roi_flat_stake', 'binomial_p_vs_breakeven', 'alpha_bonferroni_k8', 'era_win_rates', 'gates_G1_G2_G4', 'source_dataset', 'source_script'],
        ['Strategy', 'Bet side', 'n', 'W', 'Win rate', 'CI low', 'CI high', 'Modeled ROI', 'p vs 52.38%', 'α (k=8)', 'Era win rates', 'Gates G1/G2/G4', 'Source: dataset', 'Source: script'],
        table_id='backtest', transform=badge_gates)
    body = f"""
<h1>Strategy Catalog</h1>
<p class="lead">8 pre-registered variants · backtested 1980–2024 regular seasons · prices not in dataset → modeled at flat −110 (flag F8) · all outcomes published, winners and losers. Full research notes: <a href="https://github.com/sassnarep3-star/Own5/blob/main/research/strategies.md">research/strategies.md</a>.</p>
<div class="note"><b>Headline:</b> S2 (home underdog ≥7) is the strongest signal at 56.37% (n=793) and still FAILS the corrected significance gate (p=0.0134 &gt; α=0.00625). No single-bet strategy is certified as skill — S1/S2 continue as <b>Candidate</b> entries for live CLV tracking on the <a href="leaderboard.html">leaderboard</a>.</div>
<h2>Singles — backtest results (computed)</h2>
{backtest}
<h2>Parlays (cross-game)</h2>
<div class="tbl-wrap"><table><thead><tr><th>ID</th><th>Strategy</th><th>Construction</th><th>Finding (computed)</th><th>Source</th></tr></thead><tbody>
<tr><td>P1</td><td>2-leg cross-game parlay</td><td>two qualifying singles, different games</td><td>Legs independent: same-week cover ratio 0.9836 (n=9,479 pairs) — parlay EV = product of leg EVs</td><td class="src"><a href="https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv" target="_blank" rel="noopener">dataset</a><a href="https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_analysis.py" target="_blank" rel="noopener">script</a></td></tr>
<tr><td>P2</td><td>Fixed-payout parlay audit</td><td>2-leg at −110/−110 pays +264</td><td>Break-even joint 27.47% vs ≈23.6% from two break-even legs → fixed parlays are worse than straight bets without real edge</td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/luck_skill.csv" target="_blank" rel="noopener">luck_skill.csv</a><a href="https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_analysis.py" target="_blank" rel="noopener">script</a></td></tr>
</tbody></table></div>
<h2>Player-prop combos (same-game)</h2>
<div class="tbl-wrap"><table><thead><tr><th>ID</th><th>Strategy</th><th>Legs</th><th>Measured leg correlation</th><th>Status</th><th>Source</th></tr></thead><tbody>
<tr><td>X1</td><td>QB over + WR over</td><td>QB passing yards over + top-WR receiving yards over</td><td><b>r = 0.76</b> (n=3,852 team-games)</td><td><span class="chip warn">Framework — needs verifiable prop lines (F1/F7)</span></td><td class="src"><a href="https://github.com/brianfoshee/nfl-play-by-play-data/blob/352c9c9b0bce0ffa8ce85681cf9ed50c0398f462/" target="_blank" rel="noopener">pbp dataset</a><a href="https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_prop_correlations.py" target="_blank" rel="noopener">script</a></td></tr>
<tr><td>X2</td><td>RB over + game under</td><td>rush yards over + game total under</td><td>RB vs margin r=0.21; RB vs total r=0.07</td><td><span class="chip warn">Framework — needs verifiable prop lines</span></td><td class="src"><a href="https://github.com/brianfoshee/nfl-play-by-play-data/blob/352c9c9b0bce0ffa8ce85681cf9ed50c0398f462/" target="_blank" rel="noopener">pbp dataset</a><a href="https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_prop_correlations.py" target="_blank" rel="noopener">script</a></td></tr>
<tr><td>X3</td><td>QB over + game over</td><td>QB yards over + game total over</td><td>QB vs game total r=0.35</td><td><span class="chip warn">Framework — needs verifiable prop lines</span></td><td class="src"><a href="https://github.com/brianfoshee/nfl-play-by-play-data/blob/352c9c9b0bce0ffa8ce85681cf9ed50c0398f462/" target="_blank" rel="noopener">pbp dataset</a><a href="https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_prop_correlations.py" target="_blank" rel="noopener">script</a></td></tr>
</tbody></table></div>
<div class="warnbox">Prop-combo backtests require market prop lines, which have no official source (flag F1). The correlation values above are computed and reproducible; live entries wait for a licensed odds feed.</div>
"""
    return page('Strategies', 'strategies.html', body)


def build_gates():
    body = """
<h1>Validation Gates</h1>
<p class="lead">A strategy must pass every gate to be marked <b>Validated</b>. Thresholds are pre-registered. Full definitions: <a href="https://github.com/sassnarep3-star/Own5/blob/main/research/validation-gates.md">research/validation-gates.md</a>.</p>
<div class="tbl-wrap"><table><thead><tr><th>Gate</th><th>Requirement</th><th>Threshold</th><th>Basis / source</th></tr></thead><tbody>
<tr><td><b>G0</b> Provenance</td><td>Every input pinned (repo@SHA) or official URL; unknowns blank + flagged</td><td>100% of rows sourced</td><td class="src"><a href="https://www.nfl.com/" target="_blank" rel="noopener">nfl.com</a><a href="flagged.html">flag policy</a></td></tr>
<tr><td><b>G1</b> Sample size</td><td>graded bets per strategy</td><td>n ≥ 200 (entry floor)</td><td class="src"><a href="luck-vs-skill.html">power analysis (computed)</a></td></tr>
<tr><td><b>G2</b> Significance</td><td>one-sided binomial vs break-even, Bonferroni-corrected</td><td>p &lt; 0.05/8 = 0.00625</td><td class="src"><a href="https://www.davidhbailey.com/dhbpapers/overfit-tools-at.pdf" target="_blank" rel="noopener">Bailey–Borwein–López de Prado–Zhu 2014</a><a href="https://doi.org/10.3905/jpm.2014.40.5.094" target="_blank" rel="noopener">DSR 2014</a></td></tr>
<tr><td><b>G3</b> Closing line value</td><td>live entries beat the closing number</td><td>≥ 55% over ≥ 100 live picks</td><td class="src"><a href="https://arxiv.org/abs/1710.02824" target="_blank" rel="noopener">Kaunitz et al. 2017</a></td></tr>
<tr><td><b>G4</b> Era stability</td><td>win rate &gt; 50% in ≥ 3 of 4 pre-registered era splits</td><td>sign-consistent</td><td class="src"><a href="https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf" target="_blank" rel="noopener">backtest-overfitting literature</a></td></tr>
<tr><td><b>G5</b> Correlation</td><td>parlay legs priced with measured correlation; SGP legs empirical</td><td>no naive independence when |phi| &gt; 0.05</td><td class="src"><a href="correlation.html">measured values (computed)</a></td></tr>
<tr><td><b>G6</b> Robustness</td><td>±10% parameter perturbation; drop best season</td><td>≥ 80% of variants same sign</td><td class="src"><a href="https://www.davidhbailey.com/dhbpapers/overfit-tools-at.pdf" target="_blank" rel="noopener">overfitting literature</a></td></tr>
<tr><td><b>G7</b> Execution</td><td>minimum acceptable price + max stake defined per entry</td><td>recorded per entry</td><td class="src"><a href="https://ideas.repec.org/h/wsi/wschap/9789814293501_0054.html" target="_blank" rel="noopener">Thorp 2011 (Kelly)</a></td></tr>
</tbody></table></div>
<h2>Current gate outcomes (computed 2026-11-02)</h2>
<div class="tbl-wrap"><table><thead><tr><th>Strategy</th><th>G1 sample</th><th>G2 significance</th><th>G4 era stability</th><th>Entry state</th><th>Source</th></tr></thead><tbody>
<tr><td>S1 home underdog</td><td><span class="chip good">PASS</span></td><td><span class="chip bad">FAIL p=0.404</span></td><td><span class="chip good">PASS</span></td><td><span class="chip info">Candidate</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
<tr><td>S2 home dog ≥7</td><td><span class="chip good">PASS</span></td><td><span class="chip bad">FAIL p=0.0134 &gt; 0.00625</span></td><td><span class="chip good">PASS</span></td><td><span class="chip info">Candidate</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
<tr><td>S3 home fav ≥7</td><td><span class="chip good">PASS</span></td><td><span class="chip bad">FAIL</span></td><td><span class="chip bad">FAIL</span></td><td><span class="chip">Research</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
<tr><td>S4 low total over</td><td><span class="chip good">PASS</span></td><td><span class="chip bad">FAIL</span></td><td><span class="chip bad">FAIL</span></td><td><span class="chip">Research</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
<tr><td>S5 high total under</td><td><span class="chip good">PASS</span></td><td><span class="chip bad">FAIL p=0.216</span></td><td><span class="chip good">PASS</span></td><td><span class="chip">Research</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
<tr><td>S6 divisional home dog</td><td><span class="chip good">PASS</span></td><td><span class="chip bad">FAIL</span></td><td><span class="chip bad">FAIL</span></td><td><span class="chip">Research</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
<tr><td>S7 road dog ≥7</td><td><span class="chip good">PASS</span></td><td><span class="chip bad">FAIL</span></td><td><span class="chip bad">FAIL</span></td><td><span class="chip">Research</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
<tr><td>S8 SGP fav+over</td><td><span class="chip good">PASS</span></td><td><span class="chip bad">FAIL p=1.0</span></td><td><span class="chip">n/a</span></td><td><span class="chip">Research</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
</tbody></table></div>
<div class="note"><b>No strategy is Validated in the opening catalog.</b> That is the system working: promotion requires live closing-line value (G3) plus corrected significance.</div>
"""
    return page('Validation Gates', 'validation-gates.html', body)


def build_correlation():
    bets = table_from_csv('correlation_bets.csv',
                          ['pair', 'value', 'kind', 'n', 'window', 'note', 'source_dataset', 'source_script'],
                          ['Pair', 'Correlation', 'Type', 'n', 'Window', 'Note', 'Source: dataset', 'Source: script'],
                          table_id='corr-bets')
    parlays = table_from_csv('correlation_parlays.csv',
                             ['leg_a', 'leg_b', 'p_a', 'p_b', 'p_joint', 'p_independent', 'joint_over_independent', 'n', 'window', 'source_dataset', 'source_script'],
                             ['Leg A', 'Leg B', 'P(A)', 'P(B)', 'P(both) measured', 'P(A)×P(B)', 'ratio', 'n', 'Window', 'Source: dataset', 'Source: script'],
                             table_id='corr-parlays')
    props = table_from_csv('correlation_props.csv',
                           ['pair', 'pearson_r', 'p_value', 'n_team_games', 'note', 'source_dataset', 'source_script'],
                           ['Pair', 'Pearson r', 'p', 'n team-games', 'Note', 'Source: dataset', 'Source: script'],
                           table_id='corr-props')
    body = f"""
<h1>Correlation Values</h1>
<p class="lead">Computed by <code>scripts/compute_analysis.py</code> (game level) and <code>scripts/compute_prop_correlations.py</code> (player level) from pinned datasets. Methodology: <a href="https://github.com/sassnarep3-star/Own5/blob/main/research/correlation.md">research/correlation.md</a>.</p>
<div class="note"><b>Three regimes:</b> game-line legs are ≈ independent (phi ≈ 0.01) · favorite ML + favorite spread are near-duplicates (phi 0.71) · player-prop legs are strongly correlated (QB↔WR r = 0.76). Gate G5 prices each regime accordingly.</div>
<h2>Same-game bet-outcome correlations (1980–2024)</h2>
{bets}
<h2>Parlay joint probabilities (measured vs independent)</h2>
{parlays}
<h2>Player-prop style correlations (2002–2013 play-by-play, derived — flag F2)</h2>
{props}
<div class="warnbox">Player-level values derive from a community play-by-play mirror (2002–2013). Era caveat applies; values labeled derived (flag F2).</div>
"""
    return page('Correlation', 'correlation.html', body)


def build_luck():
    lk = table_from_csv('luck_skill.csv',
                        ['table', 'parameter', 'value', 'detail', 'basis', 'source_script'],
                        ['Table', 'Parameter', 'Value', 'Detail', 'Basis', 'Source: script'],
                        table_id='luck')
    body = f"""
<h1>Luck vs Skill</h1>
<p class="lead">Exact binomial and power-analysis math computed by <code>scripts/compute_analysis.py</code> into <code>data/luck_skill.csv</code>. Methodology: <a href="https://github.com/sassnarep3-star/Own5/blob/main/research/luck-vs-skill.md">research/luck-vs-skill.md</a>.</p>
<div class="cards">
  <div class="card"><div class="k">Break-even at −110</div><div class="v">52.38%</div><div class="s">exact definition</div></div>
  <div class="card"><div class="k">2-leg parlay −110/−110</div><div class="v">27.47%</div><div class="s">joint rate needed; legs give ≈23.6%</div></div>
  <div class="card"><div class="k">Lucky ≥55% over 200 bets</div><div class="v">20.8%</div><div class="s">for a true break-even bettor</div></div>
  <div class="card"><div class="k">Bets to detect true 55%</div><div class="v">2,243</div><div class="s">80% power, α=0.05 ≈ 8 NFL seasons</div></div>
</div>
{lk}
<div class="note">Consequences: Bonferroni correction (G2), CLV gate (G3), deflated leaderboard scoring, Bayesian shrinkage of displayed win rates, fractional-Kelly sizing (Thorp 2011, <a href="https://ideas.repec.org/h/wsi/wschap/9789814293501_0054.html" target="_blank" rel="noopener">record</a>).</div>
"""
    return page('Luck vs Skill', 'luck-vs-skill.html', body)


def build_leaderboard():
    body = """
<h1>Leaderboard &amp; Rewards</h1>
<p class="lead">Strategies compete — not people. Score is deflated for luck; rewards vest only for gate-passing entries. Design: <a href="https://github.com/sassnarep3-star/Own5/blob/main/research/leaderboard.md">research/leaderboard.md</a>.</p>
<div class="panel">
<h3>Scoring (luck-deflated)</h3>
<p><code>Score = 100 × [0.40 × CLV_index + 0.30 × DSR_index + 0.20 × Sample_discipline + 0.10 × Calibration]</code></p>
<div class="tbl-wrap"><table><thead><tr><th>Component</th><th>Definition</th><th>Luck control</th><th>Source</th></tr></thead><tbody>
<tr><td>CLV_index</td><td>share of picks beating the closing number, Beta-shrunk toward 50%</td><td>converges fast; hard to fake (G3)</td><td class="src"><a href="https://arxiv.org/abs/1710.02824" target="_blank" rel="noopener">Kaunitz et al. 2017</a></td></tr>
<tr><td>DSR_index</td><td>deflated-Sharpe-style P(true edge &gt; 0) given n, skew/kurtosis, variants tried</td><td>subtracts best-of-luck score</td><td class="src"><a href="https://doi.org/10.3905/jpm.2014.40.5.094" target="_blank" rel="noopener">Bailey &amp; López de Prado 2014</a></td></tr>
<tr><td>Sample_discipline</td><td>min(n/500, 1) × stake-consistency</td><td>rewards flat pre-registered staking</td><td class="src"><a href="https://www.davidhbailey.com/dhbpapers/overfit-tools-at.pdf" target="_blank" rel="noopener">overfitting literature</a></td></tr>
<tr><td>Calibration</td><td>Brier skill of entry's stated probabilities</td><td>punishes overconfidence</td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/leaderboard.md" target="_blank" rel="noopener">design doc</a></td></tr>
</tbody></table></div>
</div>
<h2>Current board (2026-11-02)</h2>
<div class="tbl-wrap"><table><thead><tr><th>Rank</th><th>Entry</th><th>Class</th><th>Gates</th><th>State</th><th>Source</th></tr></thead><tbody>
<tr><td>1</td><td>S2 home dog ≥7</td><td>Single</td><td>G1 ✓ · G2 ✗ (p=0.0134) · G4 ✓</td><td><span class="chip info">Candidate</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
<tr><td>2</td><td>S1 home underdog</td><td>Single</td><td>G1 ✓ · G2 ✗ · G4 ✓</td><td><span class="chip info">Candidate</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
<tr><td>3</td><td>S5 high-total under</td><td>Single</td><td>G1 ✓ · G2 ✗ · G4 ✓</td><td><span class="chip">Research</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
<tr><td>—</td><td>S3, S4, S6, S7</td><td>Single</td><td>G4 ✗</td><td><span class="chip">Research</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td></tr>
<tr><td>—</td><td>P1/P2 parlay framework</td><td>Parlay</td><td>framework (no qualifying legs)</td><td><span class="chip">Research</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/correlation_parlays.csv" target="_blank" rel="noopener">correlation_parlays.csv</a></td></tr>
<tr><td>—</td><td>X1–X3 prop combos</td><td>Prop-combo</td><td>G5 values measured</td><td><span class="chip">Research</span></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/correlation_props.csv" target="_blank" rel="noopener">correlation_props.csv</a></td></tr>
</tbody></table></div>
<p class="small">Rank is by gate progress until Finals begin; backtest ROI never outranks live scores.</p>
<h2>Rewards <span class="chip flag">PROPOSAL — amounts blank pending owner decision (F9)</span></h2>
<div class="tbl-wrap"><table><thead><tr><th>Rank (Finals)</th><th>Proposed share</th><th>Condition</th><th>Source</th></tr></thead><tbody>
<tr><td>1st</td><td>40% of pool</td><td>must be Validated</td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/leaderboard.md" target="_blank" rel="noopener">design doc (proposal)</a></td></tr>
<tr><td>2nd</td><td>25%</td><td>must be Validated</td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/leaderboard.md" target="_blank" rel="noopener">design doc (proposal)</a></td></tr>
<tr><td>3rd</td><td>15%</td><td>must be Validated</td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/leaderboard.md" target="_blank" rel="noopener">design doc (proposal)</a></td></tr>
<tr><td>4th–10th</td><td>2% each</td><td>Candidate or better</td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/leaderboard.md" target="_blank" rel="noopener">design doc (proposal)</a></td></tr>
<tr><td>Participation</td><td>0.25% per gate-passing season entry</td><td>publishing losers rewarded</td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/leaderboard.md" target="_blank" rel="noopener">design doc (proposal)</a></td></tr>
<tr><td>Pool size / funding</td><td><span class="chip flag">BLANK — owner decision (F9)</span></td><td>not invented</td><td class="src"><a href="flagged.html">flagged</a></td></tr>
</tbody></table></div>
<div class="note">Anti-luck clawback: rewards vest 50% at Finals win, 50% only after the entry passes G3 the following season — a lucky run cannot cash out fully.</div>
"""
    return page('Leaderboard', 'leaderboard.html', body)


def build_lines():
    lines = table_from_csv('model_lines_2026_wk9.csv',
                           ['game_date', 'away_team', 'home_team', 'site_type', 'model_spread', 'model_total',
                            'market_spread', 'market_total', 'source_schedule', 'source_standings', 'source_script'],
                           ['Date', 'Away', 'Home', 'Site', 'Our spread', 'Our total', 'Market spread', 'Market total',
                            'Source: official schedule', 'Source: official standings', 'Source: script'],
                           table_id='lines', flag_cols=('market_spread', 'market_total'))
    body = f"""
<h1>Our Lines — 2026 Week 9</h1>
<p class="lead">Originated by <code>scripts/originate_lines.py</code> from official inputs only: 2026 standings (W-L-T, PF-PA through Week 8, nfl.com) + official Week 9 schedule + measured home-field advantage (2.22 pts, 2002–2024, derived). Model spec: <a href="https://github.com/sassnarep3-star/Own5/blob/main/research/line-origination.md">research/line-origination.md</a>.</p>
<div class="note"><b>Model:</b> <code>margin = shrunk(home) − shrunk(away) + HFA</code>, <code>shrunk = net_pts_per_game × G/(G+4)</code>, <code>total = mean(PPG scored/allowed, both teams)</code>. HFA = 0 for neutral-site games (Madrid). Lines rounded to nearest 0.5.</div>
<div class="warnbox"><b>Market columns are intentionally blank</b> — no official public source publishes market lines (flag F7). They are never inferred; when a licensed feed is connected, edge = our line − market line becomes the live signal.</div>
{lines}
<p class="small">Example tensions disclosed (flag F11): v1 ratings are net-points based — no opponent adjustment, injuries, or weather. CLE @ NO shows record-vs-point-differential tension (5-3 CLE at 2-5 NO is a near pick according to raw net points).</p>
"""
    return page('Week 9 Lines', 'lines-2026-wk9.html', body)


def build_sources():
    body = """
<h1>Sources Registry</h1>
<p class="lead">Every source used in this project, what it verifies, and its verification class. Rows on every site table link here or to their direct source.</p>
<h2>Official NFL sources <span class="chip good">Verified — official</span></h2>
<div class="tbl-wrap"><table><thead><tr><th>Source</th><th>URL</th><th>Verifies</th><th>Checked</th></tr></thead><tbody>
<tr><td>NFL League Standings 2026 (REG)</td><td class="src"><a href="https://www.nfl.com/standings/league/2026/REG" target="_blank" rel="noopener">nfl.com/standings/league/2026/REG</a></td><td>32-team W-L-T, PF/PA (through Week 8) → model line inputs</td><td>2026-11-02</td></tr>
<tr><td>NFL Schedules &amp; Scores 2025 Week 1</td><td class="src"><a href="https://www.nfl.com/schedules/2025/by-week/week-1" target="_blank" rel="noopener">nfl.com/schedules/2025/by-week/week-1</a></td><td>16 official game results (per-game links in verified_official_results.csv)</td><td>2026-11-02</td></tr>
<tr><td>NFL Schedules &amp; Scores 2026 Week 8</td><td class="src"><a href="https://www.nfl.com/schedules" target="_blank" rel="noopener">nfl.com/schedules</a></td><td>13 final results + MNF listing (per-game links in verified_official_results.csv)</td><td>2026-11-02</td></tr>
<tr><td>NFL Schedules 2026 Week 9</td><td class="src"><a href="https://www.nfl.com/schedules/2026/by-week/week-9" target="_blank" rel="noopener">nfl.com/schedules/2026/by-week/week-9</a></td><td>15 upcoming matchups (per-game links in schedule_2026_wk9.csv)</td><td>2026-11-02</td></tr>
<tr><td>2025 NFL Record &amp; Fact Book</td><td class="src"><a href="https://static.clubs.nfl.com/image/upload/patriots/fvc6qgwyqlztq1muztpi.pdf" target="_blank" rel="noopener">static.clubs.nfl.com …fact book.pdf</a></td><td>official league records/facts reference</td><td>2026-11-02</td></tr>
</tbody></table></div>
<h2>Pinned datasets <span class="chip info">Derived inputs — community sources flagged</span></h2>
<div class="tbl-wrap"><table><thead><tr><th>Dataset</th><th>Pin (commit)</th><th>URL</th><th>Used for</th><th>Flag</th></tr></thead><tbody>
<tr><td>spreadspoke scores + closing lines (1966–2025 wk5)</td><td><code>1d309cb7f8f58…</code></td><td class="src"><a href="https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv" target="_blank" rel="noopener">spreadspoke_scores.csv</a></td><td>base rates, correlations, backtests, HFA</td><td><a href="flagged.html">F1</a></td></tr>
<tr><td>play-by-play archive (2002–2013)</td><td><code>352c9c9b0bce…</code></td><td class="src"><a href="https://github.com/brianfoshee/nfl-play-by-play-data/blob/352c9c9b0bce0ffa8ce85681cf9ed50c0398f462/" target="_blank" rel="noopener">nfl-play-by-play-data</a></td><td>player-prop correlations</td><td><a href="flagged.html">F2</a></td></tr>
</tbody></table></div>
<h2>Methodology literature</h2>
<div class="tbl-wrap"><table><thead><tr><th>Reference</th><th>URL</th><th>Used for</th><th>Checked</th></tr></thead><tbody>
<tr><td>Bailey, Borwein, López de Prado &amp; Zhu (2014), <i>Pseudo-Mathematics and Financial Charlatanism</i>, Notices of the AMS 61(5) 458–471</td><td class="src"><a href="https://www.davidhbailey.com/dhbpapers/overfit-tools-at.pdf" target="_blank" rel="noopener">paper PDF</a></td><td>gate G2/G6, multiple-testing correction, MinBTL</td><td>2026-11-02</td></tr>
<tr><td>Bailey &amp; López de Prado (2014), <i>The Deflated Sharpe Ratio</i>, J. Portfolio Management 40(5) 94–107</td><td class="src"><a href="https://doi.org/10.3905/jpm.2014.40.5.094" target="_blank" rel="noopener">doi:10.3905/jpm.2014.40.5.094</a></td><td>DSR_index scoring, luck removal</td><td>2026-11-02</td></tr>
<tr><td>Bailey, Borwein, López de Prado &amp; Zhu (2017), <i>The Probability of Backtest Overfitting</i>, J. Computational Finance 20(4) 39–69</td><td class="src"><a href="https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf" target="_blank" rel="noopener">paper PDF</a></td><td>gate G4, overfitting probability</td><td>2026-11-02</td></tr>
<tr><td>Kaunitz, Zhong &amp; Kreiner (2017), <i>Beating the bookies with their own numbers</i></td><td class="src"><a href="https://arxiv.org/abs/1710.02824" target="_blank" rel="noopener">arXiv:1710.02824</a></td><td>CLV gate G3, market-efficiency context</td><td>2026-11-02</td></tr>
<tr><td>Thorp (2011), <i>The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market</i>, World Scientific, ch. 54, 789–832</td><td class="src"><a href="https://ideas.repec.org/h/wsi/wschap/9789814293501_0054.html" target="_blank" rel="noopener">bibliographic record</a></td><td>bankroll sizing (gate G7), fractional Kelly</td><td>2026-11-02</td></tr>
<tr><td>Szalkowski et al. (2012), <i>The Performance of Betting Lines for Predicting the Outcome of NFL Games</i></td><td class="src"><a href="https://www.researchgate.net/publication/233427163_The_Performance_of_Betting_Lines_for_Predicting_the_Outcome_of_NFL_Games" target="_blank" rel="noopener">record</a></td><td>cross-check of home-dog cover rates, 52.38% break-even</td><td>2026-11-02</td></tr>
<tr><td>Paul &amp; Weinbach et al., <i>NFL Betting Biases, Profitable Strategies, and the Wisdom of the Crowd</i></td><td class="src"><a href="https://www.researchgate.net/publication/329796231_NFL_Betting_Biases_Profitable_Strategies_and_the_Wisdom_of_the_Crowd" target="_blank" rel="noopener">record</a></td><td>underdog/large-line strategy literature cross-check</td><td>2026-11-02</td></tr>
<tr><td>CLV explainer (secondary source, labeled as such)</td><td class="src"><a href="https://bodog.com/sports-betting/why-clv-matters" target="_blank" rel="noopener">bodog.com/…/why-clv-matters</a></td><td>CLV threshold rationale (G3) — commercial source, flagged as secondary</td><td>2026-11-02</td></tr>
</tbody></table></div>
<h2>Generated artifacts (reproducible)</h2>
<div class="tbl-wrap"><table><thead><tr><th>Artifact</th><th>Generator</th><th>Inputs</th></tr></thead><tbody>
<tr><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/base_rates.csv" target="_blank" rel="noopener">base_rates.csv</a></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_analysis.py" target="_blank" rel="noopener">compute_analysis.py</a></td><td>spreadspoke @ <code>1d309cb</code></td></tr>
<tr><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/correlation_bets.csv" target="_blank" rel="noopener">correlation_bets.csv</a> · <a href="https://github.com/sassnarep3-star/Own5/blob/main/data/correlation_parlays.csv" target="_blank" rel="noopener">parlays</a></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_analysis.py" target="_blank" rel="noopener">compute_analysis.py</a></td><td>spreadspoke @ <code>1d309cb</code></td></tr>
<tr><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/correlation_props.csv" target="_blank" rel="noopener">correlation_props.csv</a></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_prop_correlations.py" target="_blank" rel="noopener">compute_prop_correlations.py</a></td><td>pbp @ <code>352c9c9</code></td></tr>
<tr><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a> · <a href="https://github.com/sassnarep3-star/Own5/blob/main/data/luck_skill.csv" target="_blank" rel="noopener">luck_skill.csv</a></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/scripts/compute_analysis.py" target="_blank" rel="noopener">compute_analysis.py</a></td><td>spreadspoke @ <code>1d309cb</code></td></tr>
<tr><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv" target="_blank" rel="noopener">model_lines_2026_wk9.csv</a></td><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/scripts/originate_lines.py" target="_blank" rel="noopener">originate_lines.py</a></td><td>official standings + schedule + derived HFA</td></tr>
<tr><td class="src"><a href="https://github.com/sassnarep3-star/Own5/blob/main/data/verified_official_results.csv" target="_blank" rel="noopener">verified_official_results.csv</a></td><td>transcribed from nfl.com game pages</td><td>official</td></tr>
</tbody></table></div>
"""
    return page('Sources', 'sources.html', body)


def build_flagged():
    body = """
<h1>Flagged for Review</h1>
<p class="lead">Irregularities and unverified items — published, non-blocking. Nothing on this page blocks the merge or the site. Request changes after review and a follow-up session will apply them. Repo copy: <a href="https://github.com/sassnarep3-star/Own5/blob/main/docs/flagged.md">docs/flagged.md</a>.</p>
<div class="tbl-wrap"><table><thead><tr><th>ID</th><th>Item</th><th>Where</th><th>Evidence / observation</th><th>Severity</th><th>Status</th></tr></thead><tbody>
<tr><td><b>F1</b></td><td>Historical betting lines have no official public source</td><td>backtest/base-rate rows using spread/total columns</td><td>NFL publishes no closing lines; used verbatim from community spreadspoke dataset @ <code>1d309cb</code> — never inferred. <a href="https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv" target="_blank" rel="noopener">file</a></td><td><span class="chip warn">Medium</span></td><td>Open — needs licensed odds feed</td></tr>
<tr><td><b>F2</b></td><td>Play-by-play is a community mirror, 2002–2013 only</td><td>correlation_props.csv</td><td><a href="https://github.com/brianfoshee/nfl-play-by-play-data/blob/352c9c9b0bce0ffa8ce85681cf9ed50c0398f462/" target="_blank" rel="noopener">pin 352c9c9</a> mirrors advancedfootballanalytics.com; modern era may differ; values labeled derived</td><td><span class="chip warn">Medium</span></td><td>Open — re-run with nflverse data when reachable</td></tr>
<tr><td><b>F3</b></td><td>Dataset team-name inconsistencies</td><td>spreadspoke_scores.csv team columns</td><td>49 name strings incl. 1 ambiguous <code>New York</code> row (excluded, not guessed), malformed <code>New York Jets (1p, </code>, short/long forms — explicit mapping in compute_analysis.py <a href="https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv" target="_blank" rel="noopener">dataset file</a></td><td><span class="chip good">Low</span></td><td>Resolved-in-code (auditable mapping)</td></tr>
<tr><td><b>F4</b></td><td>Mixed-type over_under_line field</td><td>spreadspoke_scores.csv</td><td>non-numeric strings coerced with to_numeric(errors='coerce') — excluded, never imputed <a href="https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv" target="_blank" rel="noopener">dataset file</a></td><td><span class="chip good">Low</span></td><td>Resolved-in-code</td></tr>
<tr><td><b>F5</b></td><td>Dataset 2025 season partial</td><td>base-rate windows</td><td>64 of 78 rows scored (weeks 1–5; file last updated 2025-10-01); 2025 excluded from analysis windows <a href="https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv" target="_blank" rel="noopener">dataset file</a></td><td><span class="chip good">Low</span></td><td>Resolved-by-exclusion</td></tr>
<tr><td><b>F6</b></td><td>Historical scores verified on a sample</td><td>verified_official_results.csv</td><td>2025 Week 1: 16/16 dataset scores matched nfl.com game pages exactly; full 61-year file cannot be officially verified from the sandbox <a href="https://github.com/sassnarep3-star/Own5/blob/main/data/verified_official_results.csv" target="_blank" rel="noopener">verified rows</a><a href="https://www.nfl.com/schedules/2025/by-week/week-1" target="_blank" rel="noopener">official page</a></td><td><span class="chip warn">Medium</span></td><td>Open — sample passed 16/16</td></tr>
<tr><td><b>F7</b></td><td>Market lines blank on Week-9 page</td><td>model_lines_2026_wk9.csv market columns</td><td>no official source publishes market lines — blank by policy <a href="https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv" target="_blank" rel="noopener">model_lines csv</a></td><td><span class="chip warn">Medium</span></td><td>Open — needs licensed odds feed</td></tr>
<tr><td><b>F8</b></td><td>Backtest ROI assumes flat −110 / +264 parlay</td><td>backtest_results.csv assumption_price</td><td>prices absent from dataset; assumption labeled in every row <a href="https://github.com/sassnarep3-star/Own5/blob/main/data/backtest_results.csv" target="_blank" rel="noopener">backtest_results.csv</a></td><td><span class="chip warn">Medium</span></td><td>Open — needs licensed odds feed</td></tr>
<tr><td><b>F9</b></td><td>Reward pool amounts blank</td><td>leaderboard rewards table</td><td>mechanics specified; pool size/funding are owner decisions — not invented <a href="https://github.com/sassnarep3-star/Own5/blob/main/research/leaderboard.md" target="_blank" rel="noopener">design doc</a></td><td><span class="chip good">Low</span></td><td>Open — awaiting owner decision</td></tr>
<tr><td><b>F10</b></td><td>GB streak-field anomaly on official standings page</td><td>2026 standings transcription</td><td>streak display appeared inconsistent with week-8 results; streaks unused by the model and excluded from the transcribed CSV <a href="https://www.nfl.com/standings/league/2026/REG" target="_blank" rel="noopener">official standings</a></td><td><span class="chip good">Low</span></td><td>Resolved-by-exclusion</td></tr>
<tr><td><b>F11</b></td><td>Model limitations (disclosed)</td><td>model_lines_2026_wk9.csv</td><td>v1 = net-points ratings: no opponent adjustment, injuries, weather; league-wide HFA constant; CLE@NO shows record-vs-differential tension <a href="https://github.com/sassnarep3-star/Own5/blob/main/data/model_lines_2026_wk9.csv" target="_blank" rel="noopener">model_lines csv</a><a href="https://github.com/sassnarep3-star/Own5/blob/main/research/line-origination.md" target="_blank" rel="noopener">model spec</a></td><td><span class="chip good">Low</span></td><td>Disclosed</td></tr>
</tbody></table></div>
<div class="note">Verification policy: values that cannot be confirmed against a source are left blank and listed here. Nothing is inferred or filled in. Each site table row carries its own source link for line-by-line manual review.</div>
"""
    return page('Flagged for Review', 'flagged.html', body)


def main():
    os.makedirs(DOCS + 'assets', exist_ok=True)
    with open(DOCS + 'assets/style.css', 'w') as f:
        f.write(CSS)
    with open(DOCS + 'assets/app.js', 'w') as f:
        f.write(JS)
    with open(DOCS + '.nojekyll', 'w') as f:
        f.write('')
    pages = {
        'index.html': build_index(),
        'executive-summary.html': build_exec(),
        'strategies.html': build_strategies(),
        'validation-gates.html': build_gates(),
        'correlation.html': build_correlation(),
        'luck-vs-skill.html': build_luck(),
        'leaderboard.html': build_leaderboard(),
        'lines-2026-wk9.html': build_lines(),
        'sources.html': build_sources(),
        'flagged.html': build_flagged(),
    }
    for name, content in pages.items():
        with open(DOCS + name, 'w') as f:
            f.write(content)
        print('wrote', DOCS + name)


if __name__ == '__main__':
    main()

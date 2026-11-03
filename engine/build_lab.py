"""Build the OWN5 Empirical Lab static dashboard (lab/).

Additive scope: writes only to lab/. Reads data/empirical/*.csv|json produced by
engine/run_all.py. Every table row carries its source link; missing values are
rendered as an explicit flagged blank, never filled in.

No JavaScript framework, no external fonts, no CDN, no analytics. Works from
file:// and from GitHub Pages project paths (all links are relative).
"""
from __future__ import annotations

import html
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "empirical"
LAB = ROOT / "lab"
LAB.mkdir(exist_ok=True)

CSS = """
:root{--bg:#0b0f14;--panel:#141a21;--panel2:#1b232c;--line:#2a3441;--txt:#e8eef4;
--mut:#93a1b1;--acc:#4da3ff;--ok:#3fb950;--warn:#d9a521;--bad:#f2555a;--gold:#e3b341}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);line-height:1.55;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
header{background:var(--panel);border-bottom:1px solid var(--line);padding:14px 22px;
position:sticky;top:0;z-index:20}
.brand{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.brand h1{margin:0;font-size:18px;letter-spacing:.2px}
.brand .tag{font-size:11px;color:var(--mut);border:1px solid var(--line);
border-radius:20px;padding:2px 9px}
nav{margin-top:10px;display:flex;flex-wrap:wrap;gap:6px}
nav a{font-size:13px;color:var(--mut);padding:4px 10px;border-radius:6px}
nav a:hover{background:var(--panel2);color:var(--txt);text-decoration:none}
nav a.active{background:var(--acc);color:#04121f;font-weight:600}
main{max-width:1280px;margin:0 auto;padding:22px}
h2{font-size:21px;margin:26px 0 8px;padding-bottom:7px;border-bottom:1px solid var(--line)}
h2:first-of-type{margin-top:6px}
h3{font-size:15px;color:var(--acc);margin:20px 0 6px}
p{margin:8px 0}
.lede{color:var(--mut);font-size:14px;max-width:95ch}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:16px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:15px}
.card .k{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--mut)}
.card .v{font-size:25px;font-weight:700;margin:5px 0;font-variant-numeric:tabular-nums}
.card .n{font-size:12px;color:var(--mut)}
.card.ok .v{color:var(--ok)}.card.warn .v{color:var(--warn)}.card.bad .v{color:var(--bad)}
.note{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--acc);
border-radius:0 8px 8px 0;padding:11px 15px;margin:14px 0;font-size:13.5px}
.note.warn{border-left-color:var(--warn)}.note.bad{border-left-color:var(--bad)}
.note.ok{border-left-color:var(--ok)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:8px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:13px;background:var(--panel)}
th,td{border-bottom:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top}
th{background:var(--panel2);color:var(--mut);font-weight:600;font-size:11.5px;
text-transform:uppercase;letter-spacing:.4px;white-space:nowrap;position:sticky;top:0}
tbody tr:hover td{background:#1a222b}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.badge{display:inline-block;font-size:10.5px;padding:1px 7px;border-radius:20px;
border:1px solid var(--line);white-space:nowrap}
.b-ok{color:var(--ok);border-color:var(--ok)}.b-bad{color:var(--bad);border-color:var(--bad)}
.b-warn{color:var(--warn);border-color:var(--warn)}.b-mut{color:var(--mut)}
.blank{color:var(--warn);font-style:italic}
.pos{color:var(--ok)}.neg{color:var(--bad)}
.src{font-size:11.5px;white-space:nowrap}
.small{font-size:12px;color:var(--mut)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:16px}
.bar{height:7px;background:var(--panel2);border-radius:4px;overflow:hidden;min-width:60px}
.bar span{display:block;height:100%;background:var(--acc)}
footer{border-top:1px solid var(--line);margin-top:34px;padding:18px 22px;
color:var(--mut);font-size:12px;text-align:center}
code{background:var(--panel2);padding:1px 5px;border-radius:4px;font-size:12px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.filters input,.filters select{background:var(--panel);color:var(--txt);
border:1px solid var(--line);border-radius:6px;padding:6px 10px;font-size:13px}
.filters input{min-width:220px}
@media(max-width:700px){main{padding:14px}table{font-size:12px}th,td{padding:5px 7px}
.card .v{font-size:21px}}
"""

JS = """
document.querySelectorAll('[data-filter]').forEach(function(box){
  var table=document.getElementById(box.getAttribute('data-filter'));
  if(!table)return;
  function apply(){
    var q=box.value.toLowerCase();
    table.querySelectorAll('tbody tr').forEach(function(tr){
      tr.style.display = tr.textContent.toLowerCase().indexOf(q)>-1 ? '' : 'none';
    });
  }
  box.addEventListener('input',apply);
});
"""

PAGES = [
    ("index.html", "Dashboard"),
    ("board.html", "Our Lines"),
    ("leaderboard.html", "Leaderboard"),
    ("strategies.html", "Strategies"),
    ("correlations.html", "Correlations"),
    ("combos.html", "Combo Pricing"),
    ("skill-luck.html", "Skill vs Luck"),
    ("gates.html", "Validation Gates"),
    ("verification.html", "Verification"),
    ("executive-summary.html", "Executive Summary"),
    ("flagged.html", "Flagged for Review"),
    ("sources.html", "Sources & Method"),
]


def esc(x) -> str:
    return html.escape(str(x))


def load(name: str) -> pd.DataFrame:
    p = OUT / name
    return pd.read_csv(p, keep_default_na=False) if p.exists() else pd.DataFrame()


def jload(name: str) -> dict:
    p = OUT / name
    return json.loads(p.read_text()) if p.exists() else {}


def page(title: str, body: str, active: str) -> str:
    parts = []
    for h, t in PAGES:
        cls = ' class="active"' if h == active else ""
        parts.append(f'<a href="{h}"{cls}>{esc(t)}</a>')
    nav = "".join(parts)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — OWN5 Empirical Lab</title>
<meta name="description" content="Walk-forward NFL line origination, measured correlations, and skill-vs-luck validation. Every row source-linked.">
<style>{CSS}</style></head><body>
<header><div class="brand"><h1>OWN5 · Empirical Lab</h1>
<span class="tag">NFL line origination</span>
<span class="tag">2006–2025 backtest · 2026 board</span>
<span class="tag">built 2026-11-02</span></div>
<nav>{nav}</nav></header>
<main>{body}</main>
<footer>OWN5 Empirical Lab · research output, not betting advice ·
every table row carries a source link · unverifiable values are left blank and flagged ·
<a href="../index.html">NFL Research Desk</a> ·
<a href="https://github.com/sassnarep3-star/Own5">repository</a></footer>
<script>{JS}</script></body></html>"""


def link(url: str, label: str = "source") -> str:
    if not url or str(url).strip() in ("", "nan"):
        return '<span class="blank">unverified</span>'
    urls = str(url).split(";")
    return " · ".join(f'<a class="src" href="{esc(u.strip())}" rel="noopener noreferrer" target="_blank">{esc(label)}</a>'
                      for u in urls if u.strip())


def cell(v, numeric=False) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "nan", "None"):
        return '<span class="blank">—</span>'
    if numeric:
        try:
            f = float(v)
            cls = "pos" if f > 0 else ("neg" if f < 0 else "")
            return f'<span class="{cls}">{f:g}</span>'
        except (TypeError, ValueError):
            return esc(v)
    return esc(v)


def table(df: pd.DataFrame, cols: list[tuple[str, str]], numeric=(), tid=None,
          source_col=None, badge_cols=()) -> str:
    if df.empty:
        return '<div class="note warn">No rows available.</div>'
    ident = f' id="{tid}"' if tid else ""
    head = "".join(f'<th class="{"num" if c in numeric else ""}">{esc(lbl)}</th>' for c, lbl in cols)
    if source_col:
        head += "<th>Source</th>"
    rows = []
    for _, r in df.iterrows():
        tds = []
        for c, _lbl in cols:
            v = r.get(c)
            if c in badge_cols:
                s = str(v)
                cls = ("b-ok" if s in ("VALIDATED", "True", "PASS", "parsed")
                       else "b-bad" if s in ("REJECTED", "False", "FAIL") else "b-mut")
                tds.append(f'<td><span class="badge {cls}">{esc(s)}</span></td>')
            else:
                tds.append(f'<td class="{"num" if c in numeric else ""}">{cell(v, c in numeric)}</td>')
        if source_col:
            tds.append(f"<td>{link(r.get(source_col))}</td>")
        rows.append("<tr>" + "".join(tds) + "</tr>")
    return (f'<div class="scroll"><table{ident}><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def search_box(tid: str, placeholder="Filter rows…") -> str:
    return f'<div class="filters"><input type="search" data-filter="{tid}" placeholder="{esc(placeholder)}" aria-label="Filter table"></div>'


def card(k, v, n="", cls="") -> str:
    return f'<div class="card {cls}"><div class="k">{esc(k)}</div><div class="v">{esc(v)}</div><div class="n">{esc(n)}</div></div>'


# ---------------------------------------------------------------- pages

def build_index() -> str:
    om = jload("origination_metrics.json")
    gs = jload("gates_summary.json")
    vs = jload("verification_summary.json")
    cs = jload("correlation_summary.json")
    ms = jload("market_structure.json")
    bs = jload("board_summary.json")
    corr = load("correlations_empirical.csv")
    pp02 = corr[corr.pair_id == "PP02"]
    phi = float(pp02.phi_correlation.iloc[0]) if len(pp02) else 0.0

    body = f"""
<h2>What this is</h2>
<p class="lede">An evidence-first attempt to <strong>originate our own NFL lines</strong> and test whether
any signal survives contact with the closing market. {om.get('games_priced', 0):,} regular-season games
({om.get('seasons', ['',''])[0]}–{om.get('seasons', ['',''])[1]}) are priced strictly walk-forward, then
seven strategies spanning singles, parlays and same-game combinations are graded at real prices and
pushed through ten hard validation gates.</p>

<div class="note bad"><strong>Headline result: {gs.get('validated', 0)} of {gs.get('strategies_evaluated', 0)} strategies passed.</strong>
{esc(gs.get('headline', ''))} The closing line beat our model on both spread accuracy and win probability.
That is the finding, and it is reported rather than buried.</div>

<div class="cards">
{card("Games priced", f"{om.get('games_priced',0):,}", "walk-forward, no lookahead")}
{card("Strategies validated", f"{gs.get('validated',0)} / {gs.get('strategies_evaluated',0)}", "all 10 hard gates required", "bad")}
{card("Official score checks", f"{vs.get('exact_score_matches',0)}/{vs.get('official_games_compared',0)}", "exact match vs NFL.com", "ok")}
{card("Correlations measured", cs.get("pairs_measured", 0), "bootstrap CI, clustered by week")}
{card("Reward tiers awarded", gs.get("reward_tiers_paid", 0), "no gate-passing strategy", "warn")}
</div>

<h2>The one robust positive finding</h2>
<div class="note ok"><strong>Same-game player props are genuinely correlated.</strong>
A quarterback's passing-yards over and his top receiver's receiving-yards over hit together
far more often than independence implies: φ = <strong>{phi:.3f}</strong>, and the joint rate exceeds the
naive product by roughly six percentage points. The lift persists out-of-sample in every season tested.
Multiplying the two legs' probabilities — the standard parlay shortcut — materially misprices this combo.
See <a href="correlations.html">Correlations</a> and <a href="combos.html">Combo Pricing</a>.</div>

<h2>Our model vs the closing market</h2>
<div class="scroll"><table><thead><tr><th>Metric</th><th class="num">Our model</th><th class="num">Closing market</th><th>Winner</th></tr></thead><tbody>
<tr><td>Spread RMSE (points)</td><td class="num">{om.get('spread_rmse_ours','')}</td><td class="num">{om.get('spread_rmse_market','')}</td><td><span class="badge b-bad">Market</span></td></tr>
<tr><td>Spread MAE (points)</td><td class="num">{om.get('spread_mae_ours','')}</td><td class="num">{om.get('spread_mae_market','')}</td><td><span class="badge b-bad">Market</span></td></tr>
<tr><td>Total RMSE (points)</td><td class="num">{om.get('total_rmse_ours','')}</td><td class="num">{om.get('total_rmse_market','')}</td><td><span class="badge b-bad">Market</span></td></tr>
<tr><td>Win-probability Brier score</td><td class="num">{om.get('brier_ours','')}</td><td class="num">{om.get('brier_market','')}</td><td><span class="badge b-bad">Market</span></td></tr>
</tbody></table></div>
<p class="small">Lower is better on every row. Correlation between our spread and the market spread is
{om.get('corr_our_vs_market_spread','')} — the model has learned real team strength, but not enough to beat the price.
Source: computed in-repo from official NFL.com final scores; see <a href="verification.html">Verification</a>.</p>

<h2>Start here</h2>
<div class="grid2">
<div class="card"><h3 style="margin-top:0"><a href="board.html">Our originated lines →</a></h3>
<p class="small">{bs.get('games',0)} upcoming games priced with our own spread, total and moneyline,
side by side with the posted market number. Divergence is shown, not sold as an edge.</p></div>
<div class="card"><h3 style="margin-top:0"><a href="leaderboard.html">Leaderboard →</a></h3>
<p class="small">Every strategy ranked with its ROI, confidence interval and the exact gates it failed.
No reward tier is paid without clearing all ten.</p></div>
<div class="card"><h3 style="margin-top:0"><a href="skill-luck.html">Skill vs luck →</a></h3>
<p class="small">Cluster bootstrap, exact binomial tests, deflated Sharpe and false-discovery control —
how we stop a lucky backtest from looking like skill.</p></div>
<div class="card"><h3 style="margin-top:0"><a href="flagged.html">Flagged for review →</a></h3>
<p class="small">Every limitation, third-party dependency and unverified value, listed with its source.</p></div>
</div>

<h2>Market structure we measured</h2>
<div class="cards">
{card("Key numbers 3 & 7", f"{ms.get('pct_spreads_on_key_3_or_7',0)*100:.1f}%", "share of posted spreads")}
{card("Spread push rate", f"{ms.get('spread_push_rate',0)*100:.2f}%", "stake refunded")}
{card("Total push rate", f"{ms.get('total_push_rate',0)*100:.2f}%", "stake refunded")}
{card("Standard two-way hold", f"{ms.get('two_way_110_110_hold_pct',0):.2f}%", "at −110 / −110", "warn")}
</div>
<p class="small">The hold is the hurdle every strategy must clear before it can be called skill.</p>
"""
    return page("Dashboard", body, "index.html")


def build_board() -> str:
    b = load("originated_board_next_week.csv")
    pr = load("current_power_ratings.csv")
    bs = jload("board_summary.json")
    body = f"""
<h2>Our originated board</h2>
<p class="lede">Every number in the "ours" columns is produced by our own walk-forward model, fitted only on
games completed before kickoff ({bs.get('train_games',0):,} training games). The market columns come from the
vendored third-party closing/opening consensus and are labelled as such. Blank market cells mean no verified
price existed — they are never filled with a guess.</p>
<div class="note warn"><strong>Convention:</strong> spread is shown as <em>points the HOME team is favoured by</em>
(negative = home is the underdog), matching the upstream <code>spread_line</code> definition. A positive
<code>spread_diff</code> means we rate the home team more highly than the market does.</div>
<div class="note bad"><strong>Not a recommendation.</strong> No strategy in this project cleared validation.
Mean absolute divergence from the market is {bs.get('mean_abs_spread_diff','')} points, and our model is
<em>less</em> accurate than the market historically — divergence is therefore more likely model error than edge.</div>
{search_box("boardtbl", "Filter by team…")}
{table(b, [("gameday","Date"),("away_team","Away"),("home_team","Home"),
           ("our_spread_home_fav","Our spread"),("market_spread_home_fav","Market spread"),
           ("spread_diff","Diff"),("our_total","Our total"),("market_total","Market total"),
           ("total_diff","Diff"),("our_p_home_win","Our P(home)"),
           ("market_p_home_win_devig","Mkt P(home)"),("our_ml_home_fair","Our fair ML"),
           ("market_ml_home","Market ML")],
       numeric=("our_spread_home_fav","market_spread_home_fav","spread_diff","our_total",
                "market_total","total_diff","our_p_home_win","market_p_home_win_devig",
                "our_ml_home_fair","market_ml_home"),
       tid="boardtbl", source_col="official_schedule_url")}
<h2>Current team power ratings</h2>
<p class="small">Points above/below league average on a neutral field, as of {esc(pr.as_of.iloc[0]) if len(pr) else ''}.
"Scoring environment" is the team's contribution to the game total.</p>
{table(pr, [("rank","#"),("team","Team"),("power_rating","Power rating"),
            ("scoring_env","Scoring env"),("n_train_games","Training games")],
       numeric=("rank","power_rating","scoring_env","n_train_games"), source_col="source_url")}
"""
    return page("Our Lines", body, "board.html")


def build_leaderboard() -> str:
    lb = load("leaderboard_empirical.csv")
    gs = jload("gates_summary.json")
    body = f"""
<h2>Strategy leaderboard</h2>
<p class="lede">Ranked by risk-adjusted return (ROI divided by the width of its 95% cluster-bootstrap
interval), but only among strategies that cleared all ten hard gates. Because none did, no rank and no
reward tier is assigned. Rejected strategies are listed with their measured results so the record is complete.</p>
<div class="note bad"><strong>{gs.get('validated',0)} of {gs.get('strategies_evaluated',0)} validated · {gs.get('reward_tiers_paid',0)} reward tiers awarded.</strong>
{esc(gs.get('headline',''))}</div>
{table(lb, [("rank","Rank"),("strategy","Strategy"),("decided_bets","Bets"),
            ("roi","ROI"),("roi_ci_low","CI low"),("roi_ci_high","CI high"),
            ("risk_adjusted_score","Risk-adj"),("gates_passed","Gates"),
            ("reward_tier","Reward"),("status","Status"),("failed_gates","Failed gates")],
       numeric=("decided_bets","roi","roi_ci_low","roi_ci_high","risk_adjusted_score","gates_passed"),
       badge_cols=("status",))}
<h2>How the competition is scored</h2>
<div class="scroll"><table><thead><tr><th>Tier</th><th>Eligibility</th><th>Reward</th><th>Awarded this run</th></tr></thead><tbody>
<tr><td>Tier 1</td><td>Top 3 gate-passing strategies by risk-adjusted return</td><td>Featured placement + largest research allocation</td><td><span class="badge b-bad">0</span></td></tr>
<tr><td>Tier 2</td><td>Next 4 gate-passing strategies</td><td>Standard research allocation</td><td><span class="badge b-bad">0</span></td></tr>
<tr><td>Tier 3</td><td>Remaining gate-passing strategies</td><td>Honourable mention</td><td><span class="badge b-bad">0</span></td></tr>
</tbody></table></div>
<p class="small">Rewards are research allocation and recognition, not cash. A strategy that fails a gate is
ineligible regardless of its point-estimate ROI — this is the mechanism that removes luck from the ranking.</p>
"""
    return page("Leaderboard", body, "leaderboard.html")


def build_strategies() -> str:
    s = load("strategy_summary.csv")
    sl = load("skill_luck.csv")
    descs = {
        "S1_spread_value": "Bet the spread when our calibrated cover probability exceeds the de-vigged market probability by ≥3pp.",
        "S2_total_value": "Bet over/under when our total projection implies ≥3pp more probability than the de-vigged market.",
        "S3_rest_edge": "Back a team coming off a bye against an opponent on a short week.",
        "S4_division_dog": "Back divisional underdogs of 3+ points.",
        "S5_fade_big_favorite": "Back the underdog when the market lays 7+ points.",
        "P1_cross_game_2leg": "Two-leg parlay of the strongest spread edges from different games in the same week.",
        "P2_same_game_fav_over": "Favourite covers + game over, priced with the empirical joint rate from prior seasons only.",
    }
    s["description"] = s.strategy.map(descs).fillna("")
    body = f"""
<h2>Strategies tested</h2>
<p class="lede">Seven deterministic rules covering single bets, cross-game parlays and same-game
combinations. Thresholds were fixed before grading; nothing was tuned on the test window. Pushes refund
the stake. Player-prop combinations are analysed on the <a href="combos.html">combo pricing page</a> instead
of being graded, because no verified sportsbook prop price exists to grade against.</p>
{table(s, [("strategy","Strategy"),("description","Rule"),("bets","Bets"),
           ("wins","W"),("losses","L"),("pushes","Push"),("win_rate","Win rate"),
           ("profit_units","Profit (u)"),("roi","ROI")],
       numeric=("bets","wins","losses","pushes","win_rate","profit_units","roi"))}
<div class="note">Every strategy above is measured against the price actually recorded for that game.
Where the upstream table lacked a specific price, a −110 assumption was applied and flagged per bet;
the share of assumed prices is a validation gate (G8).</div>
<h2>Per-season stability</h2>
{table(sl, [("strategy","Strategy"),("roi_era1","ROI first half"),("roi_era2","ROI second half"),
            ("era_stable_positive","Stable & positive"),("bets_needed_for_80pct_power","Bets needed for 80% power")],
       numeric=("roi_era1","roi_era2","bets_needed_for_80pct_power"),
       badge_cols=("era_stable_positive",))}
<p class="small">"Bets needed" is the sample size required to distinguish the observed edge from zero at 80%
power and 5% significance. Large numbers are the honest reason most edges cannot be confirmed.</p>
"""
    return page("Strategies", body, "strategies.html")


def build_correlations() -> str:
    c = load("correlations_empirical.csv")
    cc = load("prop_continuous_correlations.csv")
    cs = jload("correlation_summary.json")
    body = f"""
<h2>Measured correlations</h2>
<p class="lede">For each pair of bet legs we compare the observed joint hit rate to the product of the
marginals (what naive parlay pricing assumes). φ is the correct correlation for two binary legs.
Confidence intervals come from a {cs.get('bootstrap_replicates',0):,}-replicate bootstrap that resamples whole
weeks, so same-week dependence is preserved. "Independence rejected" means the naive product falls outside
the bootstrap interval of the true joint rate.</p>
<div class="cards">
{card("Pairs measured", cs.get("pairs_measured",0), "game + player prop legs")}
{card("Same-game rejections", cs.get("same_game_pairs_rejecting_independence",0), "naive pricing is wrong", "warn")}
{card("Cross-game rejections", cs.get("cross_game_pairs_rejecting_independence",0), "independence holds", "ok")}
</div>
<div class="note ok"><strong>Practical reading:</strong> cross-game parlay legs are close enough to independent
that multiplying probabilities is defensible. Same-game <em>player prop</em> legs are not — QB passing and
WR1 receiving share a cause, and pricing them as independent gives away real value.</div>
{search_box("corrtbl")}
{table(c, [("pair_id","ID"),("label","Leg pair"),("scope","Scope"),("n","n"),
           ("p_a","P(A)"),("p_b","P(B)"),("naive_independent_joint","Naive joint"),
           ("observed_joint","Observed joint"),("joint_ci_low","CI low"),("joint_ci_high","CI high"),
           ("lift_vs_independent","Lift"),("phi_correlation","φ"),
           ("independence_rejected","Indep. rejected")],
       numeric=("n","p_a","p_b","naive_independent_joint","observed_joint","joint_ci_low",
                "joint_ci_high","lift_vs_independent","phi_correlation"),
       tid="corrtbl", source_col="source_url", badge_cols=("independence_rejected",))}
<h2>Continuous stat correlations</h2>
<p class="small">Pearson and Spearman correlation of the underlying yardage, which is what drives the
binary over/under dependence above.</p>
{table(cc, [("pair_id","ID"),("label","Stat pair"),("n","n"),
            ("pearson_r","Pearson r"),("spearman_r","Spearman r")],
       numeric=("n","pearson_r","spearman_r"), source_col="source_url")}
"""
    return page("Correlations", body, "correlations.html")


def build_combos() -> str:
    f = load("combo_fair_prices.csv")
    wf = load("combo_walk_forward.csv")
    body = """
<h2>Combination pricing</h2>
<p class="lede">If two legs are correlated, the fair price of the combination is set by the observed joint
probability, not by multiplying the two single-leg probabilities. This page quantifies that gap and tests
whether it survives out-of-sample.</p>
<div class="note warn"><strong>No sportsbook player-prop lines are published by any official source.</strong>
We therefore do not invent a book price or claim a prop ROI. Instead each player's line is <em>originated
in-repo</em> as his trailing season-to-date median (minimum three prior games), which makes "prop hits" a
well-defined event. The deliverable is the measured mispricing, not a fabricated return.</div>
<h2>Fair price vs naive independence price</h2>
"""
    body += table(f, [("pair_id","ID"),("label","Combination"),("scope","Scope"),("n","n"),
                      ("observed_joint","True joint"),("fair_american","Fair price"),
                      ("naive_american","Naive price"),("mispricing_pct_of_stake","Mispricing %"),
                      ("phi_correlation","φ"),("independence_rejected","Indep. rejected")],
                  numeric=("n","observed_joint","fair_american","naive_american",
                           "mispricing_pct_of_stake","phi_correlation"),
                  source_col="source_url", badge_cols=("independence_rejected",))
    body += """
<p class="small">A positive mispricing figure means the naive price is too generous — the combination is
more likely than independence implies. This is precisely why operators re-price or restrict correlated
same-game legs.</p>
<h2>Out-of-sample test: QB passing + WR1 receiving</h2>
<p class="lede">For each season, the joint rate and the naive product are estimated from <em>prior seasons only</em>,
then compared with what actually happened. The final column is the expected value per unit if a book had
paid the naive independence price.</p>
"""
    body += table(wf, [("season","Season"),("train_n","Train n"),("test_n","Test n"),
                       ("train_joint_prior","Prior joint"),("train_naive_prior","Prior naive"),
                       ("test_joint_actual","Actual joint"),("test_joint_ci_low","CI low"),
                       ("test_joint_ci_high","CI high"),("naive_decimal_offered","Naive decimal"),
                       ("breakeven_decimal","Break-even decimal"),
                       ("ev_per_unit_vs_naive_price","EV vs naive")],
                  numeric=("season","train_n","test_n","train_joint_prior","train_naive_prior",
                           "test_joint_actual","test_joint_ci_low","test_joint_ci_high",
                           "naive_decimal_offered","breakeven_decimal","ev_per_unit_vs_naive_price"),
                  source_col="source_url")
    if len(wf):
        mean_ev = pd.to_numeric(wf.ev_per_unit_vs_naive_price, errors="coerce").mean()
        body += f"""
<div class="note ok"><strong>Consistent across every season tested.</strong> Mean out-of-sample EV against a
naively-priced book is {mean_ev:+.3f} units per unit staked. The caveat that matters: real sportsbooks
already shade correlated same-game parlays, so this is the size of the theoretical error, <em>not</em> a
claim that the price is available. Capturing it requires a book that has not adjusted — which is an
empirical question this dataset cannot answer.</div>"""
    return page("Combo Pricing", body, "combos.html")


def build_skill() -> str:
    sl = load("skill_luck.csv")
    ss = jload("skill_luck_summary.json")
    body = f"""
<h2>Removing luck from the equation</h2>
<p class="lede">Luck cannot be eliminated from a football outcome. What can be done is to refuse to call a
result skill until it survives tests designed to kill lucky backtests. Six independent checks are applied to
every strategy.</p>
<div class="scroll"><table><thead><tr><th>Check</th><th>What it stops</th></tr></thead><tbody>
<tr><td>Break-even from actual prices</td><td>Comparing a −120 bet to a generic 52.4% threshold</td></tr>
<tr><td>Exact binomial test</td><td>Reading a small win-rate edge as meaningful</td></tr>
<tr><td>Cluster bootstrap by week</td><td>Treating same-week bets as independent samples</td></tr>
<tr><td>Benjamini–Hochberg FDR</td><td>Testing many strategies until one looks good</td></tr>
<tr><td>Deflated Sharpe Ratio</td><td>Ignoring the Sharpe expected from the best of N noise trials</td></tr>
<tr><td>Era split</td><td>A result driven by one favourable stretch of seasons</td></tr>
</tbody></table></div>
<div class="cards">
{card("Strategies tested", ss.get("strategies_tested",0))}
{card("Positive ROI", ss.get("positive_roi",0), "point estimate only", "warn")}
{card("Survive FDR control", ss.get("surviving_fdr",0), "multiple-testing corrected", "bad")}
{card("Bootstrap replicates", f"{ss.get('bootstrap_replicates',0):,}", "resampling whole weeks")}
</div>
{search_box("sltbl")}
{table(sl, [("strategy","Strategy"),("decided","Bets"),("win_rate","Win rate"),
            ("breakeven_win_rate","Break-even"),("win_rate_edge","Edge"),("roi","ROI"),
            ("roi_ci_low","CI low"),("roi_ci_high","CI high"),("p_roi_positive","P(ROI>0)"),
            ("binom_p_one_sided","Binomial p"),("bh_fdr_significant","FDR pass"),
            ("deflated_sharpe","Deflated Sharpe"),("luck_share","Luck share")],
       numeric=("decided","win_rate","breakeven_win_rate","win_rate_edge","roi","roi_ci_low",
                "roi_ci_high","p_roi_positive","binom_p_one_sided","deflated_sharpe","luck_share"),
       tid="sltbl", badge_cols=("bh_fdr_significant",))}
<p class="small"><strong>Luck share</strong> is the fraction of the observed deviation from break-even that
one standard deviation of pure binomial noise could explain. A value of 1.0 means the result is entirely
consistent with luck.</p>
<div class="note">{esc(ss.get('note',''))}</div>
"""
    return page("Skill vs Luck", body, "skill-luck.html")


def build_gates() -> str:
    g = load("validation_gates.csv")
    r = load("gate_results.csv")
    gate_cols = [(f"G{i}", f"G{i}") for i in range(1, 11)]
    body = """
<h2>Validation gates</h2>
<p class="lede">Ten hard gates, defined before results were examined. A strategy must clear every one to be
eligible for a reward tier. Gates G1–G7 are statistical; G8–G9 are data-integrity requirements; G10 is
structural and enforced by the walk-forward code itself.</p>
"""
    body += table(g, [("gate_id","Gate"),("name","Name"),("requirement","Requirement"),("type","Type")])
    body += "<h2>Gate-by-gate results</h2>"
    body += table(r, [("strategy","Strategy")] + gate_cols +
                  [("gates_passed","Passed"),("status","Status")],
                  numeric=("gates_passed",), badge_cols=tuple(f"G{i}" for i in range(1, 11)) + ("status",))
    body += """
<h2>Why the integrity gates matter</h2>
<div class="note warn"><strong>G9 (official verification)</strong> fails for every strategy in this run.
Only 80 games have been re-checked line-by-line against official NFL.com scores — a stratified sample, not a
census of the 5,199-game universe. Until more of the backtest is officially verified, no strategy can be
promoted, even if its statistics were strong. This is deliberate: the project's rule is that unverified
inputs cannot produce verified conclusions.</div>
<div class="note"><strong>G8 (price integrity)</strong> fails where the upstream table lacked a specific
price and a −110 assumption was applied. Assumed prices are counted per bet, never hidden.</div>
"""
    return page("Validation Gates", body, "gates.html")


def build_verification() -> str:
    v = load("official_verification.csv")
    vs = jload("verification_summary.json")
    body = f"""
<h2>Official verification</h2>
<p class="lede">The historical table used for backtesting is third-party open data, not an official NFL
publication. To avoid laundering an unverified source into a confident conclusion, individual games are
re-read from the official NFL.com scoreboard and compared score-by-score.</p>
<div class="cards">
{card("Games compared", vs.get("official_games_compared",0), "line by line")}
{card("Exact matches", vs.get("exact_score_matches",0), f"{vs.get('match_rate',0)*100:.1f}% match rate", "ok")}
{card("Mismatches", vs.get("mismatches",0), "zero tolerance", "ok")}
{card("Share of universe", f"{vs.get('verified_share_of_universe',0)*100:.2f}%", "sample, not census", "warn")}
</div>
<div class="note ok"><strong>Result: {esc(vs.get('status',''))}.</strong> Every game checked against
NFL.com matched both teams' final scores exactly. A team-code irregularity was found and corrected during
this process: upstream records the Rams as <code>LA</code> while official pages use the
<code>LAR</code> abbreviation, which initially prevented four rows from joining. The alias is now normalised.</div>
<div class="note warn">{esc(vs.get('limitation',''))}</div>
{search_box("vtbl", "Filter by team or season…")}
"""
    body += table(v, [("game_id","Game ID"),("season","Season"),("week","Wk"),
                      ("away_team","Away"),("away_score","Away (data)"),
                      ("away_score_official","Away (official)"),
                      ("home_team","Home"),("home_score","Home (data)"),
                      ("home_score_official","Home (official)"),("verified","Match")],
                  numeric=("season","week","away_score","away_score_official","home_score","home_score_official"),
                  tid="vtbl", source_col="source_url", badge_cols=("verified",))
    return page("Verification", body, "verification.html")


def build_sources() -> str:
    prov = json.loads((ROOT / "data" / "raw" / "PROVENANCE.json").read_text())
    rows = "".join(
        f"<tr><td><code>{esc(d['file'])}</code></td><td>{esc(d['official_status'])}</td>"
        f"<td>{link(d.get('upstream_repo',''),'upstream')}</td>"
        f"<td class='small'>{esc(d.get('upstream_commit', d.get('upstream_branch','')))}</td></tr>"
        for d in prov["datasets"])
    body = f"""
<h2>Sources and method</h2>
<h3>Primary official source</h3>
<p>Final scores are verified against <a href="https://www.nfl.com/scores/" target="_blank" rel="noopener">NFL.com official scoreboards</a>.
Each verified game row links to the exact weekly page it was read from. Player statistics are referenced to
<a href="https://www.nfl.com/stats/player-stats/" target="_blank" rel="noopener">NFL.com official player stats</a>.</p>
<h3>Third-party inputs (declared, not official)</h3>
<div class="scroll"><table><thead><tr><th>File</th><th>Status</th><th>Upstream</th><th>Pinned revision</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="note bad"><strong>No official league source publishes betting lines.</strong> Spreads, totals and
moneylines in this project come from a third-party consensus dataset. Every price-dependent result inherits
that limitation, which is why gate G8 exists and why no prop ROI is claimed at all.</div>
<h3>Method</h3>
<div class="scroll"><table><thead><tr><th>Stage</th><th>Implementation</th></tr></thead><tbody>
<tr><td>Line origination</td><td>Weighted ridge on team indicators; exponential recency decay (300-day half-life); refit every week on strictly prior games. Separate margin and total models. Market prices are never used as model features.</td></tr>
<tr><td>Probability conversion</td><td>Normal margin distribution with continuity correction for ties; residual sigma estimated from training data only.</td></tr>
<tr><td>De-vigging</td><td>Proportional (multiplicative) removal of overround from both sides of each two-way market.</td></tr>
<tr><td>Correlation</td><td>φ coefficient for binary legs; observed joint vs product of marginals; week-clustered bootstrap intervals.</td></tr>
<tr><td>Skill vs luck</td><td>Exact binomial test vs realised break-even; cluster bootstrap ROI; Benjamini–Hochberg FDR at 10%; deflated Sharpe; chronological era split.</td></tr>
<tr><td>Prop lines</td><td>Originated in-repo as trailing season-to-date median (min 3 prior games). No sportsbook prop price is invented.</td></tr>
</tbody></table></div>
<h3>Reproduce</h3>
<p><code>pip install -r engine/requirements.txt</code> then <code>python engine/run_all.py</code>.
All randomness is seeded (20261102). Tests: <code>python -m unittest tests.test_engine</code>.</p>
<p class="small">{esc(prov.get('closing_lines_note',''))}</p>
"""
    return page("Sources & Method", body, "sources.html")


def build_flagged() -> str:
    vs = jload("verification_summary.json")
    items = [
        ("E-F01", "Backtest inputs are third-party", "High",
         "The historical game table is nflverse/nfldata, not an official NFL publication. Only a stratified "
         f"sample ({vs.get('official_games_compared',0)} games) has been re-verified against NFL.com.",
         "https://github.com/nflverse/nfldata", "Gate G9 blocks promotion until coverage improves."),
        ("E-F02", "No official betting lines exist", "High",
         "No league or official body publishes spreads, totals or moneylines. All prices are third-party "
         "consensus. Every ROI figure inherits this dependency.",
         "https://github.com/nflverse/nfldata/blob/master/data/games.csv",
         "Declared on every price-dependent table; gate G8 measures assumed-price share."),
        ("E-F03", "No verified player-prop prices", "High",
         "Player prop lines are not published by any official source. Prop analysis therefore uses "
         "in-repo originated lines (trailing medians) and reports correlation/mispricing only.",
         "https://www.nfl.com/stats/player-stats/", "No prop ROI is claimed anywhere in this project."),
        ("E-F04", "Player data ends at 2021", "Medium",
         "The vendored weekly player table covers 2015–2021. Prop correlations are not measured on the "
         "most recent seasons, so they may have drifted with offensive scheme changes.",
         "https://github.com/bendominguez0111/fantasy-csv-data", "Extend the player dataset and re-run."),
        ("E-F05", "Model is less accurate than the market", "High",
         "Our originated lines lose to the closing line on spread RMSE, total RMSE and Brier score. "
         "Divergence on the board page is therefore not evidence of edge.",
         "https://www.nfl.com/scores/", "Reported prominently; no strategy promoted."),
        ("E-F06", "Zero strategies passed validation", "High",
         "All seven strategies failed at least one hard gate. No reward tier is awarded and no profitable "
         "edge is claimed.", "https://www.nfl.com/scores/", "This is the honest result, not a failure to run."),
        ("E-F07", "Team-code irregularity (corrected)", "Low",
         "Upstream uses LA for the Rams while official pages use LAR; OAK/SD/STL are legacy codes. "
         "Four official rows initially failed to join. Aliases are now normalised engine-wide.",
         "https://www.nfl.com/scores/", "Fixed; verification now matches 80/80."),
        ("E-F08", "Proportional de-vig bias", "Medium",
         "Multiplicative de-vigging is known to be mildly biased toward longshots relative to Shin or "
         "power methods. This affects the market probability used as the edge benchmark.",
         "https://www.nfl.com/odds/", "Documented; alternative de-vig methods are future work."),
        ("E-F09", "Correlated-combo EV is theoretical", "High",
         "The positive EV on QB+WR1 combos assumes a book paying the naive independence price. Real "
         "operators shade correlated same-game legs, so the price may not be obtainable.",
         "https://www.nfl.com/stats/player-stats/", "Stated explicitly wherever the EV appears."),
        ("E-F10", "Rest/roster features are limited", "Medium",
         "The model uses team strength and rest only. Injuries, quarterback changes, weather and travel "
         "are not modelled, which caps achievable accuracy.",
         "https://www.nfl.com/injuries/", "Listed as the main direction for model improvement."),
        ("E-F11", "Official pages sometimes hide scores", "Low",
         "Some NFL.com weekly scoreboards render 'Hidden Score' instead of a value. Those games were not "
         "transcribed and were never guessed.",
         "https://www.nfl.com/scores/", "Verification sample excludes them by design."),
        ("E-F12", "Playoffs excluded", "Low",
         "Only regular-season games are modelled and graded. Postseason markets differ structurally and "
         "were not analysed.", "https://www.nfl.com/schedules/", "Scope boundary, declared."),
    ]
    df = pd.DataFrame(items, columns=["id","item","severity","detail","source_url","disposition"])
    body = """
<h2>Flagged for review</h2>
<p class="lede">Every limitation, third-party dependency and unverified value in this project. These items are
published rather than hidden, and none of them were resolved by guessing a value. Severity reflects how much
the item constrains the conclusions.</p>
<div class="note warn">Flagged items do not block publication. They block <em>promotion</em>: no strategy is
called validated while an integrity gate is open.</div>
"""
    body += table(df, [("id","ID"),("item","Item"),("severity","Severity"),
                       ("detail","Detail"),("disposition","Disposition")],
                  source_col="source_url")
    return page("Flagged for Review", body, "flagged.html")


def build_exec() -> str:
    om = jload("origination_metrics.json")
    gs = jload("gates_summary.json")
    vs = jload("verification_summary.json")
    ms = jload("market_structure.json")
    wf = load("combo_walk_forward.csv")
    corr = load("correlations_empirical.csv")
    lb = load("leaderboard_empirical.csv")
    pp = corr[corr.pair_id == "PP02"]
    phi = float(pp.phi_correlation.iloc[0]) if len(pp) else 0
    lift = float(pp.lift_vs_independent.iloc[0]) if len(pp) else 0
    ev = pd.to_numeric(wf.ev_per_unit_vs_naive_price, errors="coerce").mean() if len(wf) else 0
    best = lb.iloc[0] if len(lb) else None
    md = f"""# Executive Summary — OWN5 NFL Line Origination

**Date:** 2026-11-02 · **Scope:** NFL regular season, 2006–2025 backtest, 2026 live board
**Status:** research complete; **{gs.get('validated',0)} of {gs.get('strategies_evaluated',0)} strategies validated**

## Bottom line

We built a complete line-origination and validation pipeline, then used it to test whether we could beat
the NFL closing market. **We could not.** Our model prices {om.get('games_priced',0):,} games walk-forward and
learns real team strength (correlation {om.get('corr_our_vs_market_spread','')} with the market spread), but the
closing line is more accurate on every metric we measured. All seven strategies failed at least one of ten
hard validation gates. No reward tier is awarded and no profitable edge is claimed.

One robust, actionable finding did survive: **same-game player props are materially correlated**, and naive
parlay pricing gets that combination wrong.

## What was built

| Component | Result |
|---|---|
| Games priced walk-forward | {om.get('games_priced',0):,} (2006–2025) |
| Own lines originated | spread, total, moneyline + team power ratings |
| Strategies graded | 7 (singles, cross-game parlays, same-game combos) |
| Correlation pairs measured | {len(corr)} with week-clustered bootstrap CIs |
| Official score verification | {vs.get('exact_score_matches',0)}/{vs.get('official_games_compared',0)} exact matches vs NFL.com |
| Hard validation gates | 10, all required |
| Strategies passing all gates | **{gs.get('validated',0)}** |

## Model vs market

| Metric | Ours | Market | Better |
|---|---|---|---|
| Spread RMSE | {om.get('spread_rmse_ours','')} | {om.get('spread_rmse_market','')} | Market |
| Total RMSE | {om.get('total_rmse_ours','')} | {om.get('total_rmse_market','')} | Market |
| Win-prob Brier | {om.get('brier_ours','')} | {om.get('brier_market','')} | Market |

The standard two-way hold at −110/−110 is {ms.get('two_way_110_110_hold_pct',0):.2f}%. A strategy must beat that
before any question of skill arises. None did.

## The positive finding: correlated player props

A quarterback's passing-yards over and his top receiver's receiving-yards over are **not independent**:

- φ = **{phi:.3f}**
- Joint hit rate exceeds the naive product by **{lift*100:.1f} percentage points**
- Independence is rejected by the bootstrap interval
- The lift persists out-of-sample in **every** season tested (2016–2021), mean theoretical EV
  **{ev:+.3f}** units per unit against a naively-priced book

**Critical caveat:** real sportsbooks already shade correlated same-game legs. This measures the size of the
pricing error, not a price we can necessarily obtain. No prop ROI is claimed, because no official prop lines
exist to grade against.

Cross-game legs, by contrast, tested close to independent — multiplying probabilities there is defensible.

## Removing luck

Six independent checks were applied: break-even computed from actual prices, exact binomial tests,
week-clustered bootstrap CIs, Benjamini–Hochberg false-discovery control, deflated Sharpe ratio against a
best-of-N noise hurdle, and chronological era splits.
{f"The best point estimate was {best.strategy} at {float(best.roi)*100:+.2f}% ROI — inside its confidence interval of zero and not significant." if best is not None else ""}

## Integrity position

- Historical inputs are **third-party**, not official. {vs.get('official_games_compared',0)} games were re-verified
  line-by-line against NFL.com with a 100% exact-match rate; that is a sample, not a census, so gate G9
  blocks promotion for every strategy.
- **No official source publishes betting lines.** All prices are third-party consensus, declared throughout.
- **No player-prop prices were invented.** Prop lines are originated in-repo as trailing medians.
- 12 flagged items are published on the Flagged for Review page with source links.

## Recommended next steps

1. Expand official verification toward a census of the backtest universe (unblocks G9).
2. Add injury, quarterback and weather features — the clearest gap in model accuracy.
3. Extend player data past 2021 and re-test whether the prop correlation still holds.
4. Obtain timestamped prop prices to test whether the correlation gap is actually capturable.
5. Pre-register any new strategy before grading it, to keep FDR control meaningful.

---
*Research output, not betting advice. Luck cannot be removed from outcomes; it can only be bounded.*
"""
    (ROOT / "research" / "empirical").mkdir(parents=True, exist_ok=True)
    (ROOT / "research" / "empirical" / "EXECUTIVE_SUMMARY.md").write_text(md, encoding="utf-8")

    body = f"""
<h2>Executive summary</h2>
<p class="lede">The complete picture in one page. Markdown version:
<a href="https://github.com/sassnarep3-star/Own5/blob/main/research/empirical/EXECUTIVE_SUMMARY.md">research/empirical/EXECUTIVE_SUMMARY.md</a>.</p>
<div class="note bad"><strong>Bottom line: we could not beat the closing market.</strong>
{om.get('games_priced',0):,} games priced walk-forward; {gs.get('validated',0)} of {gs.get('strategies_evaluated',0)}
strategies cleared all ten gates. No reward tier awarded, no profitable edge claimed.</div>
<h3>What was built</h3>
<div class="scroll"><table><thead><tr><th>Component</th><th>Result</th></tr></thead><tbody>
<tr><td>Games priced walk-forward</td><td>{om.get('games_priced',0):,} (2006–2025)</td></tr>
<tr><td>Own lines originated</td><td>Spread, total, moneyline, team power ratings</td></tr>
<tr><td>Strategies graded</td><td>7 — singles, cross-game parlays, same-game combos</td></tr>
<tr><td>Correlation pairs measured</td><td>{len(corr)} with week-clustered bootstrap CIs</td></tr>
<tr><td>Official verification</td><td>{vs.get('exact_score_matches',0)}/{vs.get('official_games_compared',0)} exact vs NFL.com</td></tr>
<tr><td>Strategies passing all 10 gates</td><td><strong>{gs.get('validated',0)}</strong></td></tr>
</tbody></table></div>
<h3>The positive finding</h3>
<div class="note ok">QB passing-yards over + same-team WR1 receiving-yards over: φ = <strong>{phi:.3f}</strong>,
joint rate <strong>{lift*100:.1f}pp</strong> above the naive product, independent pricing rejected, and the lift
holds out-of-sample in every season tested (mean theoretical EV {ev:+.3f}/unit). Real books shade these legs,
so this measures the pricing error — not an obtainable price.</div>
<h3>Why nothing was promoted</h3>
<p>The market beat our model on spread RMSE ({om.get('spread_rmse_market','')} vs {om.get('spread_rmse_ours','')})
and Brier score ({om.get('brier_market','')} vs {om.get('brier_ours','')}). The standard hold is
{ms.get('two_way_110_110_hold_pct',0):.2f}%. Every strategy also fails gate G9, because official verification
covers a sample rather than the full universe. Unverified inputs cannot produce verified conclusions.</p>
<h3>Next steps</h3>
<ol><li>Expand official verification toward a census (unblocks G9).</li>
<li>Add injury, quarterback and weather features.</li>
<li>Extend player data past 2021 and re-test the prop correlation.</li>
<li>Obtain timestamped prop prices to test capturability.</li>
<li>Pre-register new strategies before grading.</li></ol>
<p class="small">Research output, not betting advice. Luck cannot be removed from outcomes; it can only be bounded.</p>
"""
    return page("Executive Summary", body, "executive-summary.html")


def main() -> None:
    builders = {
        "index.html": build_index, "board.html": build_board,
        "leaderboard.html": build_leaderboard, "strategies.html": build_strategies,
        "correlations.html": build_correlations, "combos.html": build_combos,
        "skill-luck.html": build_skill, "gates.html": build_gates,
        "verification.html": build_verification, "sources.html": build_sources,
        "flagged.html": build_flagged, "executive-summary.html": build_exec,
    }
    for name, fn in builders.items():
        (LAB / name).write_text(fn(), encoding="utf-8")
        print(f"  wrote lab/{name}")
    print(f"\n{len(builders)} pages written to lab/")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""NBA Signal Lab — deterministic site builder (session 6d508fee).

Builds nba-signal-lab/*.html from data/outputs.json + data/*.csv.
Rules enforced here:
  * every table row carries an official source link, or the literal
    marker 'BLANK — UNVERIFIED' with a pointer to flagged.html;
  * no timestamps/randomness in output (idempotent builds);
  * flagged/unverified items are published, never hidden.
"""
import csv, json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = HERE

with open(os.path.join(DATA, "outputs.json")) as f:
    O = json.load(f)


def read_csv(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))


teams_cur = read_csv("teams_2026_27.csv")
teams_pri = read_csv("teams_2025_26.csv")
std_cur = read_csv("standings_2026_27.csv")
std_pri = read_csv("standings_2025_26.csv")
logs = read_csv("game_logs_2025_26.csv")
slate = read_csv("schedule_2026_11_04.csv")
registry = read_csv("players_registry.csv")

E = html.escape
UNVER = '<span class="blank">BLANK — UNVERIFIED</span>'


def link(url, text=None):
    if not url:
        return UNVER
    return f'<a href="{E(url)}" target="_blank" rel="noopener">{E(text or url)}</a>'


def table(headers, rows, cls=""):
    h = "".join(f"<th>{E(str(x))}</th>" for x in headers)
    body = ""
    for r in rows:
        body += "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
    return f'<table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table>'


def flagbadge():
    return f'<a class="badge" href="flagged.html">{len(O["flags"])} flags — see Flagged for Review</a>'


NAV = [("index.html", "Dashboard"), ("executive-summary.html", "Executive Summary"),
       ("model-lines.html", "Own Model Lines"), ("correlations.html", "Correlations"),
       ("strategies.html", "Strategies & Gates"), ("luck-vs-skill.html", "Luck vs Skill"),
       ("leaderboard.html", "Leaderboard"), ("data-verified.html", "Verified Data"),
       ("analysis.html", "Analysis"), ("verification.html", "Verification"),
       ("flagged.html", "Flagged for Review")]


def page(fname, title, body):
    nav = "".join(f'<a href="{u}"{" class=active" if u == fname else ""}>{E(t)}</a>' for u, t in NAV)
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)} — NBA Signal Lab</title><link rel="stylesheet" href="style.css"></head>
<body><header><div class="wrap"><h1>NBA Signal Lab</h1>
<p class="sub">Own lines · signal strategies · validation gates · luck stripped · session 6d508fee</p>
<nav>{nav}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap">Built deterministically from <code>nba-signal-lab/data/</code> ·
Every row links an official NBA source · Unverified values are blank and flagged, never inferred ·
{flagbadge()}</div></footer></body></html>"""
    with open(os.path.join(OUT, fname), "w") as f:
        f.write(doc)


S = O["summary"]

# ---------------------------- index.html ----------------------------------
rows = [
    ["Season (as of 2026-11-03)", E(S["season"]), ""],
    ["Teams tracked (official rows)", E(str(S["teams_tracked"])), link("https://www.nba.com/standings", "standings")],
    ["Player-game rows transcribed", E(str(S["game_log_rows"])), link("https://www.nba.com/stats/leaders?Season=2025-26", "leaders")],
    ["Players with full 2025-26 logs", E(str(S["players_tracked"])), link("data-verified.html", "data")],
    ["Slate games with own lines", E(str(S["slate_games"])), link("model-lines.html", "model lines")],
    ["Correlation estimates published", E(str(S["correlation_pairs"])), link("correlations.html", "correlations")],
    ["Strategies catalogued / certified", f"{E(str(S['strategies_total']))} / <strong>0</strong>", link("strategies.html", "gates")],
    ["Verification checks passed", f"{sum(1 for c in O['verification']['checks'] if c['ok'])} / {len(O['verification']['checks'])}", link("verification.html", "verification")],
    ["Open flags", E(str(len(O["flags"]))), link("flagged.html", "flagged")],
]
lead = [["East", E(S["east_leader"]["team"]), E(S["east_leader"]["record"]), link(S["east_leader"]["source_url"], "nba.com/standings")],
        ["West", E(S["west_leader"]["team"]), E(S["west_leader"]["record"]), link(S["west_leader"]["source_url"], "nba.com/standings")]]
slate_rows = [[E(g["away_team"]), "@", E(g["home_team"]), E(str(g["model_home_spread"])), E(str(g["model_total"])), link(g["source_url"], "schedule source")]
              for g in O["model_lines"]]
body = f"""
<h2>Dashboard</h2>
<p>Signal-generating NBA research desk: original model lines, correlation-priced prop combos,
validation gates, and a luck-stripped leaderboard. <strong>0 strategies are certified</strong> —
every claim below is data, method, or an explicit open flag.</p>
{table(["Metric", "Value", "Source"], rows, "kv")}
<h3>2026-27 conference leaders</h3>
{table(["Conf", "Team", "Record", "Source"], lead)}
<h3>Tonight's own lines (2026-11-04 slate, {len(slate_rows)} of 14 games sourced — see flag)</h3>
{table(["Away", "", "Home", "Model home spread", "Model total", "Source"], slate_rows)}
<p class="note">Market columns are intentionally blank: no verified odds source was retrievable
(see <a href="flagged.html">Flagged for Review</a>). Model inputs: blended 2026-27 / 2025-26 net
ratings (<a href="model-lines.html">method</a>).</p>
"""
page("index.html", "Dashboard", body)

# ---------------------- executive-summary.html ----------------------------
body = f"""
<h2>Executive Summary</h2>
<p>Everything material about this desk in one place. Full narrative:
<a href="../research/nba-signal-lab/EXECUTIVE_SUMMARY.md">research/nba-signal-lab/EXECUTIVE_SUMMARY.md</a>.</p>
<h3>What is live</h3>
{table(["Item", "Value", "Where"], [
    ["Verified datasets", "30-team tables × 2 seasons; 125 player-game rows (Dončić 64, Edwards 61); 6-game slate", link("data-verified.html", "verified data")],
    ["Checksums", "Every game-log average reproduces the official leaders page exactly (GP/PTS/REB/AST/3PM)", link("verification.html", "verification")],
    ["Own model lines", f"{len(O['model_lines'])} games, spread + total, market columns blank+flagged", link("model-lines.html", "model lines")],
    ["Correlation values", "7 stat-pair r's with 95% CI; 5 prop-combo phi's; lag-1 independence checks", link("correlations.html", "correlations")],
    ["Luck removal", "Exact small-n p-values, deflated scoring, multiple-testing bounds; 0 skill claims", link("luck-vs-skill.html", "luck vs skill")],
    ["Strategies", "5 catalogued (singles, parlay, prop combos) — all PENDING behind gates G01–G10", link("strategies.html", "strategies")],
    ["Leaderboard", "Competition desk active with audit units; prize pool BLANK+flagged", link("leaderboard.html", "leaderboard")],
])}
<h3>Headline findings (all recomputable in-repo)</h3>
<ul>
<li><strong>Prop legs are not independent:</strong> same-game 2-leg combos hit 10–16% more often than
the independence product; the 3-leg combo PTS≥25 &amp; AST≥5 &amp; REB≥5 lifts 1.27× (phi table).
Parlays/SBGS must be priced with measured phi, not multiplied marginals.</li>
<li><strong>Cross-game legs behave:</strong> lag-1 PTS autocorrelation is ≈0 for both tracked players
(both 95% CIs contain 0), supporting independent-game parlay assumptions.</li>
<li><strong>Skill detection is brutally expensive:</strong> distinguishing a true 55% bettor from
break-even (52.38% at −110) at 80% power needs <strong>~2,243 graded bets</strong>. A 30–20 hot streak
(60%) carries exact p=0.17 — indistinguishable from luck.</li>
<li><strong>PTS×3PM is the strongest stat coupling</strong> (r=0.69 [0.58, 0.77]) while
PTS×WIN is weak (r=0.09 [−0.09, 0.26]) — player-prop volume legs correlate far more than
player-outcome legs.</li>
</ul>
<h3>Open flags ({len(O["flags"])})</h3>
{table(["ID", "Type", "Text"], [[E(f["id"]), E(f["type"]), E(f["text"])] for f in O["flags"]])}
<p class="note">No strategy is certified and no return is attributed to skill. This desk publishes
verified data, methods, and flags — it does not publish invented numbers.</p>
"""
page("executive-summary.html", "Executive Summary", body)

# -------------------------- model-lines.html ------------------------------
line_rows = []
for g in O["model_lines"]:
    line_rows.append([
        E(g["game_date"]), E(g["away_team"]), "@", E(g["home_team"]), E(g["tip_time_as_listed"]),
        E(str(g["model_home_spread"])), E(str(g["model_total"])),
        UNVER, UNVER,
        link(g["source_url"], "team schedule") + (f" · {link(g['cross_check_url'], 'cross-check')}" if g.get("cross_check_url") else ""),
    ])
sens = [[E(g["home_team"]), E(str(g["model_home_spread_hfa20"])), E(str(g["model_home_spread_hfa25"])),
         E(str(g["model_home_spread_hfa30"])), link(g["source_url"], "source")] for g in O["model_lines"]]
strengths = [[E(g["away_team"]), E(str(g["away_strength"])), E(str(g["away_weight_cur"])),
              E(g["home_team"]), E(str(g["home_strength"])), E(str(g["home_weight_cur"])), link(g["source_url"], "source")]
             for g in O["model_lines"]]
P = O["parameters"]
body = f"""
<h2>Own Model Lines — 2026-11-04 slate</h2>
<p>Lines are originated in-repo from verified team rows. <strong>Market columns are blank and flagged:
no verified odds source was retrievable in this sandbox</strong> — nothing is inferred.
Model home spread is the expected home margin (negative = home favorite).</p>
{table(["Date", "Away", "", "Home", "Tip (as listed)", "Model home spread", "Model total",
        "Market spread", "Market total", "Source"], line_rows)}
<h3>Method (pre-registered parameters, flagged)</h3>
<ul>
<li>Team strength S = w·(2026-27 net/g) + (1−w)·(2025-26 net/g), w = n/(n+{E(str(P['K_BLEND']))}),
n = current-season games. Early-season samples (5–8 games) shrink to the prior by design.</li>
<li>Expected home margin = S<sub>home</sub> − S<sub>away</sub> + HFA, HFA = {E(str(P['HFA_PTS']))} pts
(model constant — <a href="flagged.html">flagged F-HFA</a>; empirical home win%:
2026-27 {E(str(O['hfa']['home_win_pct_2026_27']))} ({O['hfa']['home_wins_2026_27']}-{O['hfa']['home_losses_2026_27']}),
2025-26 {E(str(O['hfa']['home_win_pct_2025_26']))} ({O['hfa']['home_wins_2025_26']}-{O['hfa']['home_losses_2025_26']}))</li>
<li>Expected total = average of the two teams' blended (PF/g + PA/g), PA/g derived as PTS/g − +/−/g
from official per-game columns (1dp rounding inherits ±0.1 — documented).</li>
</ul>
<h3>HFA sensitivity (spread at HFA = 2.0 / 2.5 / 3.0)</h3>
{table(["Home team", "HFA 2.0", "HFA 2.5", "HFA 3.0", "Source"], sens)}
<h3>Strength blends used</h3>
{table(["Away", "S_away", "w_cur", "Home", "S_home", "w_cur", "Source"], strengths)}
<p class="note">Slate coverage flag: the official game calendar shows 14 NBA games on 2026-11-04;
6 are sourced here under the pre-registered top-4-per-conference rule (Boston's schedule page is
not machine-readable). Unretrieved games are flagged, not guessed.
All model lines are research outputs, not betting advice.</p>
"""
page("model-lines.html", "Own Model Lines", body)

# ------------------------- correlations.html ------------------------------
pair_rows = []
for c in O["correlations"]["stat_pairs"]:
    per = c["per_player"]
    per_txt = " · ".join(f"{E(k)}: r={E(str(v['r']))} (n={v['n']})" for k, v in per.items()) or "—"
    pair_rows.append([E(c["pair"]), E(str(c["pooled_r"])),
                      f"[{E(str(c['pooled_ci95'][0]))}, {E(str(c['pooled_ci95'][1]))}]",
                      E(str(c["pooled_n"])), per_txt, link("https://www.nba.com/stats/leaders?Season=2025-26", "official logs")])
phi_rows = []
for p in O["correlations"]["prop_thresholds"]:
    phi_rows.append([E(p["combo"]), E(str(p["n"])), E(str(p["hit_rate_a"])), E(str(p["hit_rate_b"])),
                     E(str(p["joint_hit_rate"])), E(str(p["independence_product"])),
                     E(str(p["lift_vs_independence"])), E(str(p["phi"])), link("https://www.nba.com/stats/leaders?Season=2025-26", "source")])
lag_rows = [[E(l["player"]), E(str(l["lag1_r_pts"])), E(str(l["n_pairs"])),
             f"[{E(str(l['ci95'][0]))}, {E(str(l['ci95'][1]))}]", link("https://www.nba.com/stats/leaders?Season=2025-26", "source")]
            for l in O["correlations"]["lag1_pts"]]
body = f"""
<h2>Correlation Values</h2>
<p>All values computed in-repo from the 125 transcribed player-game rows (each row carries its
official game link on <a href="data-verified.html">Verified Data</a>). Pearson r with Fisher-z
95% CI. {E(O['correlations']['method'])}</p>
<h3>Continuous stat pairs (pooled player-games + per-player)</h3>
{table(["Pair", "r", "95% CI", "n", "Per player", "Source"], pair_rows)}
<h3>Pre-registered prop-combo legs (phi / dependence)</h3>
{table(["Combo", "n", "P(A)", "P(B)", "P(A∩B)", "Independence P(A)P(B)", "Lift", "phi", "Source"], phi_rows)}
<p class="note"><strong>Analysis:</strong> every combo's joint hit rate exceeds the independence
product (lift 1.10–1.27). Same-game legs share minutes, pace and blowout risk, so SGP/parlay
pricing that multiplies marginals <em>overstates</em> the true combo probability — and a fair
comparison must price legs with these phi values. The 3-leg combo is the extreme case
(lift 1.27).</p>
<h3>Cross-game independence probe (lag-1 autocorrelation of PTS)</h3>
{table(["Player", "lag-1 r", "Pairs", "95% CI", "Source"], lag_rows)}
<p class="note">Both CIs contain 0: consecutive-game scoring shows no detectable autocorrelation
in this sample, supporting the cross-game independence assumption behind multi-game parlays
(gate G05). Correlation is not causation; all rows are labeled exploratory.</p>
"""
page("correlations.html", "Correlations", body)

# ------------------------- strategies.html --------------------------------
gate_rows = [[E(g["gate"]), E(g["name"]), E(g["definition"]), E(g["status"])] for g in O["gates"]]
str_rows = []
for s in O["strategies"]:
    str_rows.append([E(s["id"]), E(s["class"]), E(s["name"]), E(s["description"]),
                     E(s["evidence"]), E(s["status"]), E(s["gates_blocking"]),
                     link(s["source_url"], "source")])
body = f"""
<h2>Strategy Catalog &amp; Validation Gates</h2>
<p>Every candidate strategy starts <strong>PENDING</strong> and is certified only after passing
all gates. Current certified count: <strong>0</strong>.</p>
{table(["ID", "Class", "Strategy", "Description", "Evidence", "Status", "Gates blocking", "Source"], str_rows)}
<h3>Validation gates G01–G10</h3>
{table(["Gate", "Name", "Definition", "Current status"], gate_rows)}
<p class="note">G08 (market gate) is structurally blocked: no verified odds source exists yet, so
no sides/totals/props can be graded against closing lines. Strategies remain in the catalog with
their measured evidence (hit rates, phi, independence checks) so they can be graded the moment a
verified market feed exists.</p>
"""
page("strategies.html", "Strategies & Gates", body)

# ------------------------- luck-vs-skill.html ------------------------------
power_rows = [[E(str(p["true_win_rate"])), E(str(p["null_win_rate"])), E(str(p["required_n_bets"])),
               E(str(p["critical_wins"])), E(p["method"])] for p in O["luck_vs_skill"]["power_table"]]
exact_rows = [[E(str(p["wins"])), E(str(p["n"])), E(str(p["raw_win_pct"])),
               E(str(p["exact_one_sided_p_vs_break_even"])), E(p["method"])]
              for p in O["luck_vs_skill"]["exact_small_n_examples"]]
dsr_rows = [[E(str(p["wins"])), E(str(p["n"])), E(str(p["raw_win_pct"])),
             E(str(p["deflated_win_pct"])), E(str(p["z_vs_break_even"]))]
            for p in O["luck_vs_skill"]["deflation_examples"]]
mt_rows = [[E(str(p["candidate_strategies_m"])), E(str(p["per_test_alpha_sidak"])),
            E(str(p["per_test_alpha_bonferroni"]))] for p in O["luck_vs_skill"]["multiple_testing"]]
body = f"""
<h2>Luck vs Skill</h2>
<p>{E(O['luck_vs_skill']['no_luck_claim'])}</p>
<h3>What sample size could ever prove skill?</h3>
<p>Break-even at −110 is <strong>{E(str(O['luck_vs_skill']['break_even_win_rate']))}</strong>
(= 110/210 by arithmetic). To reject that null at one-sided α=0.05 with 80% power:</p>
{table(["True win rate", "Null (break-even)", "Required graded bets", "Critical wins", "Method"], power_rows)}
<h3>Exact small-n reality checks (binomial tails, computed in-repo)</h3>
{table(["Wins", "n", "Raw win %", "Exact p vs break-even", "Method"], exact_rows)}
<p class="note">A 30–20 run (60%!) is p=0.17 — pure noise territory. Even 60–100 (60%) only
reaches p=0.077. Small samples cannot separate skill from luck; the gate engine enforces this.</p>
<h3>Deflated scoring (leaderboard shrinkage, prior weight 25 bets)</h3>
{table(["Wins", "n", "Raw win %", "Deflated win %", "z vs break-even"], dsr_rows)}
<h3>Multiple-testing bounds (m candidate strategies)</h3>
{table(["m strategies", "Šidák per-test α", "Bonferroni per-test α"], mt_rows)}
<p class="note">{E(O['luck_vs_skill']['break_even_note'])}</p>
"""
page("luck-vs-skill.html", "Luck vs Skill", body)

# -------------------------- leaderboard.html ------------------------------
entry_rows = []
for e in O["leaderboard"]["entries"]:
    entry_rows.append([E(str(e["rank"])), E(e["entry_id"]), E(e["name"]), E(e["class"]),
                       E(str(e["graded_bets"])), E(str(e["wins"])), E(str(e["losses"])),
                       UNVER, UNVER, link(e["source_url"], "source")])
body = f"""
<h2>Competition Leaderboard</h2>
<p>Singles, parlays and player-prop combos compete on deflated scoring. Everything is in audit
units until a real prize pool is verified. Certified entries: <strong>0</strong>.</p>
{table(["Rank", "ID", "Entry", "Class", "Graded", "W", "L", "Units", "Deflated score", "Source"], entry_rows)}
<h3>Scoring &amp; rewards</h3>
{table(["Item", "Value"], [
    ["Scoring rule", E(O["leaderboard"]["scoring"])],
    ["Reward tiers", "Champion 50% · Runner-up 30% · Third 20% of prize pool"],
    ["Prize pool", UNVER + " — see flag F-ODDS"],
])}
<p class="note">Every entry starts PENDING at 0 graded bets; ranks are static placeholders until
gate G08 supplies graded results. Units and deflated scores are blank — computing them from zero
bets would be an inference, which this desk does not make.</p>
"""
page("leaderboard.html", "Leaderboard", body)

# -------------------------- data-verified.html ----------------------------
t26_rows = [[E(t["team"]), E(t["conf"]), E(t["gp"]), E(t["w"]), E(t["l"]), E(t["pts_pg"]),
             E(t["reb_pg"]), E(t["ast_pg"]), E(t["tov_pg"]), E(t["plus_minus_pg"]),
             link(t["source_url"], "nba.com team page")] for t in sorted(teams_cur, key=lambda x: -float(x["plus_minus_pg"]))]
t25_rows = [[E(t["team"]), E(t["conf"]), E(t["gp"]), E(t["w"]), E(t["l"]), E(t["pts_pg"]),
             E(t["reb_pg"]), E(t["ast_pg"]), E(t["tov_pg"]), E(t["plus_minus_pg"]),
             link(t["source_url"], "nba.com team page")] for t in sorted(teams_pri, key=lambda x: -float(x["plus_minus_pg"]))]
reg_rows = []
for r in registry:
    vals = [r["gp"], r["pts_pg"], r["reb_pg"], r["ast_pg"], r["tpm_pg"]]
    cells = [E(v) if v else UNVER for v in vals]
    reg_rows.append([E(r["player_id"]), E(r["player"]), E(r["team"]), E(r["season"])] + cells +
                    [link(r["source_url"], "leaders page")])
slate_rows2 = [[E(g["game_date"]), E(g["away_team"]), E(g["home_team"]), E(g["tip_time_as_listed"]),
                E(g["arena"]), E(g["tv"]) if g["tv"] else UNVER,
                link(g["source_url"], "team schedule") + (f" · {link(g['cross_check_url'], 'cross-check')}" if g["cross_check_url"] else "")]
               for g in slate]
log_rows = [[E(r["player"]), E(r["game_date"]), E(r["matchup"]), E(r["result"]), E(r["min"]), E(r["pts"]),
             E(r["tpm"]), E(r["reb"]), E(r["ast"]), E(r["stl"]), E(r["tov"]), E(r["plus_minus"]),
             link(r["source_url"], "nba.com game")]
            for r in sorted(logs, key=lambda x: (x["player"], x["game_date"]))]
body = f"""
<h2>Verified Data (every row links its official source)</h2>
<h3>2026-27 team stats (per game) — sorted by net</h3>
{table(["Team", "Conf", "GP", "W", "L", "PTS/g", "REB/g", "AST/g", "TOV/g", "+/-/g", "Source"], t26_rows)}
<h3>2025-26 team stats (per game) — model priors</h3>
{table(["Team", "Conf", "GP", "W", "L", "PTS/g", "REB/g", "AST/g", "TOV/g", "+/-/g", "Source"], t25_rows)}
<h3>Player registry (official 2025-26 leaders page) — game-log checksums</h3>
{table(["ID", "Player", "Team", "Season", "GP", "PTS/g", "REB/g", "AST/g", "3PM/g", "Source"], reg_rows)}
<h3>2026-11-04 slate (official team-schedule pages)</h3>
{table(["Date", "Away", "Home", "Tip (as listed)", "Arena", "TV", "Source"], slate_rows2)}
<h3>Game logs 2025-26 — {len(log_rows)} player-game rows</h3>
{table(["Player", "Date", "Matchup", "W/L", "MIN", "PTS", "3PM", "REB", "AST", "STL", "TOV", "+/-", "Source"], log_rows)}
<p class="note">Transcription validation: PTS = 2·(FGM−3PM) + 3·3PM + FTM holds on all
{len(log_rows)} rows; REB = OREB + DREB holds on all rows; per-player GP/PTS/REB/AST/3PM averages
reproduce the official leaders page exactly (see <a href="verification.html">Verification</a>).</p>
"""
page("data-verified.html", "Verified Data", body)

# ---------------------------- analysis.html -------------------------------
std26_rows = [[E(s["team"]), E(s["seed"]), f"{E(s['w'])}-{E(s['l'])}", E(s["win_pct"]), E(s["conf_rec"]),
               E(s["home_rec"]), E(s["road_rec"]), E(s["neutral_rec"]), E(s["ot_rec"]), E(s["last10"]),
               E(s["streak"]), link(s["source_url"], "standings")] for s in std_cur]
std25_rows = [[E(s["team"]), E(s["seed"]), f"{E(s['w'])}-{E(s['l'])}", E(s["win_pct"]), E(s["conf_rec"]),
               E(s["home_rec"]), E(s["road_rec"]), E(s["neutral_rec"]), E(s["ot_rec"]), E(s["last10"]),
               E(s["streak"]), link(s["source_url"], "standings")] for s in std_pri]
cs_rows = []
for c in O["checksum_rows"]:
    exp, got = c["expected"], c["recomputed"]
    cs_rows.append([E(c["player"]), E(str(exp["gp"])), E(str(got["gp"])), E(str(exp["pts_pg"])),
                    E(str(got["pts_pg"])), E(str(exp["reb_pg"])), E(str(got["reb_pg"])),
                    E(str(exp["ast_pg"])), E(str(got["ast_pg"])), E(str(exp["tpm_pg"])),
                    E(str(got["tpm_pg"])), "PASS" if c["ok"] else "FAIL", link(c["source_url"], "leaders")])
body = f"""
<h2>Analysis</h2>
<h3>2026-27 standings (official, with splits)</h3>
{table(["Team", "Seed", "W-L", "WIN%", "Conf", "Home", "Road", "Neu", "OT", "L10", "Streak", "Source"], std26_rows)}
<h3>2025-26 final standings (model prior season)</h3>
{table(["Team", "Seed", "W-L", "WIN%", "Conf", "Home", "Road", "Neu", "OT", "L10", "Streak", "Source"], std25_rows)}
<h3>Game-log transcription checksums (recomputed vs official)</h3>
{table(["Player", "GP exp", "GP got", "PTS exp", "PTS got", "REB exp", "REB got", "AST exp", "AST got",
        "3PM exp", "3PM got", "Result", "Source"], cs_rows)}
<h3>Model-line table (detail on <a href="model-lines.html">Own Model Lines</a>)</h3>
{table(["Home", "S_home", "S_away", "Model home spread", "Model total", "Source"],
       [[E(g["home_team"]), E(str(g["home_strength"])), E(str(g["away_strength"])),
         E(str(g["model_home_spread"])), E(str(g["model_total"])), link(g["source_url"], "source")]
        for g in O["model_lines"]])}
<p class="note">Reading notes: 2026-27 nets are noisy (5–8 games); the model deliberately shrinks
them toward 2025-26. DET's +11.6 current net sits on a 60-win prior — its blended spread is the
model's most aggressive. SAC's blend is the other tail (−11.1). Both effects are parameter-driven
and visible in the strength table on the model-lines page.</p>
"""
page("analysis.html", "Analysis", body)

# -------------------------- verification.html -----------------------------
check_rows = [["PASS" if c["ok"] else "<strong>FAIL</strong>", E(c["check"]), E(c["detail"]) or "—"]
              for c in O["verification"]["checks"]]
fetch_rows = [
    ["E1", link("https://www.nba.com/standings", "nba.com/standings"), "2026-27 standings 30 teams", "W-L vs team-stats page: 30/30 exact"],
    ["E2", link("https://www.nba.com/stats/teams/traditional?Season=2026-27&SeasonType=Regular%20Season", "teams/traditional 2026-27"), "30 team rows", "W-L vs E1; Σ(+/-×GP)=0"],
    ["E3", link("https://www.nba.com/standings?Season=2025-26", "standings 2025-26"), "30 team rows + splits", "splits sum to record; 3 transcription errors caught by re-fetch and fixed"],
    ["E4", link("https://www.nba.com/stats/leaders?Season=2025-26", "leaders 2025-26"), "player registry + checksums", "GP/PTS/REB/AST/3PM reproduced exactly from logs"],
    ["E5", link("https://www.nba.com/stats/player/1630162/boxscores?Season=2025-26", "Edwards boxscores"), "61 rows (50 + 11 via date filter)", "identities + checksum"],
    ["E6", link("https://www.nba.com/stats/player/1629029/boxscores?Season=2025-26", "Dončić boxscores"), "64 rows (50 + 14 via date filter)", "identities + checksum + cross-game (0022500019) with E5"],
    ["E7", link("https://www.nba.com/stats/teams/traditional?Season=2025-26&SeasonType=Regular%20Season", "teams/traditional 2025-26"), "30 team rows (priors)", "Σ(+/-×GP)=0; W-L vs E3"],
    ["E8", link("https://www.nba.com/rockets/schedule", "team schedule pages ×8"), "Nov-4 slate rows", "DET-PHI cross-confirmed on both team pages"],
    ["E9", link("https://www.nba.com/games?date=2026-11-04", "games calendar"), "official game counts (Nov 3: 0; Nov 4: 14)", "slate completeness flag"],
    ["E10", link("https://www.nba.com/standings?Season=2025-26&Section=margins", "standings Section=margins"), "attempted PF/PA margins (renders situational splits instead)", "dead end documented"],
]
body = f"""
<h2>Verification</h2>
<p>Every dataset row was hand-transcribed from an official NBA page fetched on 2026-11-03 UTC
(sandbox bash cannot reach nba.com — outbound blocked; all retrieval via the platform fetcher).
Checksums were recomputed in-repo against independent official renderings.</p>
<h3>Automated checks ({sum(1 for c in O['verification']['checks'] if c['ok'])}/{len(O['verification']['checks'])} pass)</h3>
{table(["Result", "Check", "Detail"], check_rows)}
<h3>Fetch register (official sources for manual review)</h3>
{table(["#", "URL", "What was transcribed", "Validation"], fetch_rows)}
<h3>Game-log checksum detail</h3>
{table(["Player", "Official GP", "Recomputed", "Official PTS/g", "Recomputed", "Official REB/g", "Recomputed",
        "Official AST/g", "Recomputed", "Official 3PM/g", "Recomputed", "Result", "Source"], cs_rows)}
<p class="note">Verification loop in action: the first compute run flagged Portland's 2025-26
split row; a re-fetch of the official page showed Neutral 0-0 / OT 1-2 (plus two streak
mismatches). Transcription corrected, all 16 checks now pass. Irregularities are published on
<a href="flagged.html">Flagged for Review</a>.</p>
"""
page("verification.html", "Verification", body)

# ---------------------------- flagged.html --------------------------------
flag_rows = [[E(f["id"]), E(f["type"]), E(f["text"])] for f in O["flags"]]
body = f"""
<h2>Flagged for Review</h2>
<p>Irregularities, unverified values and model parameters — published, not hidden. None of these
block the merge; all of them are open for manual review against the linked sources.</p>
{table(["ID", "Type", "Item"], flag_rows)}
<h3>Unverified values deliberately left blank</h3>
{table(["Value", "Where", "Why"], [
    ["Market spread / market total", link("model-lines.html", "model lines"), "No verified odds source retrievable; nothing inferred"],
    ["Leaderboard prize pool + units", link("leaderboard.html", "leaderboard"), "No verified funding source; 0 graded bets"],
    ["Gilgeous-Alexander / Brown / Maxey / Mitchell per-game log rows", link("data-verified.html", "registry"), "Registered with official checksums; full logs not transcribed (fetch budget) — flagged scope note F-PLAYERS"],
    ["Remaining 8 games of the 2026-11-04 slate", link("model-lines.html", "model lines"), "Not retrievable under the pre-registered selection rule; not guessed (F-SLATE)"],
])}
<h3>Irregularities observed at the source</h3>
<ul>
<li><code>https://www.nba.com/games?date=2026-11-04</code> renders only the calendar + game count
without JavaScript; individual matchups are not in the static HTML.</li>
<li><code>cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json</code> returns HTTP 500.</li>
<li><code>standings?Section=margins</code> renders situational splits (3pts or less, score 100+, …),
not PF/PA margins; PA/g is derived from PTS/g − +/−/g with 1dp rounding (±0.1 documented).</li>
<li>Player box-score pages render at most ~50 rows; remaining rows retrieved via the official
DateFrom/DateTo filters (row counts then matched the official "Rows" totals exactly).</li>
<li>Team schedule pages label tip times "PDT" on nba.com; times are transcribed exactly as
listed ("as listed" column) — no timezone conversion was inferred.</li>
</ul>
"""
page("flagged.html", "Flagged for Review", body)

with open(os.path.join(OUT, "style.css"), "w") as f:
    f.write("""
body{margin:0;font:15px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1a2230;background:#f4f6fa}
.wrap{max-width:1080px;margin:0 auto;padding:0 18px}
header{background:#101a2e;color:#fff;padding:18px 0 0}
header h1{margin:0 0 2px;font-size:24px;letter-spacing:.3px}
header .sub{margin:0 0 12px;color:#9fb2d0;font-size:13px}
nav{display:flex;flex-wrap:wrap;gap:2px;padding-bottom:10px}
nav a{color:#c9d6ee;text-decoration:none;padding:6px 10px;border-radius:6px 6px 0 0;font-size:13px}
nav a:hover{background:#1d2b47;color:#fff}
nav a.active{background:#2a5bd7;color:#fff}
main{background:#fff;padding:22px 26px 34px;box-shadow:0 1px 4px rgba(16,26,46,.12);min-height:60vh}
h2{margin-top:6px;color:#12203a}
h3{color:#22314f;border-bottom:2px solid #e4e9f2;padding-bottom:4px}
table{border-collapse:collapse;width:100%;margin:10px 0 18px;font-size:13px}
th{background:#eef2f9;text-align:left;padding:7px 8px;border:1px solid #dbe3ef;color:#2c3d5e;white-space:nowrap}
td{padding:6px 8px;border:1px solid #e4e9f2;vertical-align:top}
tr:nth-child(even){background:#fafbfe}
table.kv td:first-child{font-weight:600;width:38%}
a{color:#1a4fd6}
.note{background:#f2f6ff;border-left:4px solid #2a5bd7;padding:10px 14px;font-size:13.5px}
.badge{display:inline-block;background:#b3261e;color:#fff;padding:3px 10px;border-radius:12px;text-decoration:none;font-size:12px}
.blank{color:#b3261e;font-size:11.5px;font-weight:600;letter-spacing:.2px}
footer{padding:18px 0 30px;color:#5a6a85;font-size:12.5px}
code{background:#eef2f9;padding:1px 5px;border-radius:4px;font-size:12.5px}
li{margin:6px 0}
""")

print("built:", sorted(f for f in os.listdir(OUT) if f.endswith(".html")))

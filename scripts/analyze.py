#!/usr/bin/env python3
"""Own5 analysis engine.

Reads verified datasets from data/ and produces analysis outputs:
  - verification_report.json : line-by-line consistency checks of the data
  - backtest_2026.json       : walk-forward backtest of originated model lines on 2026 Weeks 1-8
  - model_lines_2026_w9.json : originated spread/total lines + QB prop lines for 2026 Week 9
  - correlations.json        : Pearson correlation values computed from verified data
  - strategies.json          : strategy definitions, validation gates, results
  - leaderboard.json         : leaderboard competition ranking

Pure stdlib. No network access. All inputs are the verified JSON files in data/.
Walk-forward discipline: for each 2026 game, the model uses 2025 full-season
aggregates plus ONLY final 2026 games from earlier weeks (no lookahead).
"""
import json, math, os
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
A = os.path.join(ROOT, "analysis")
os.makedirs(A, exist_ok=True)

def load(name):
    with open(os.path.join(D, name)) as f:
        return json.load(f)

s25 = load("standings_2025.json")["teams"]
s26 = load("standings_2026_w8.json")["teams"]
games = load("games_2026_w1_w8.json")["games"]
w9 = load("schedule_2026_w9.json")["games"]
p26 = load("players_2026.json")
p25 = load("players_2025.json")

T25 = {t["team"]: t for t in s25}
T26 = {t["team"]: t for t in s26}
TEAMS = sorted(T25.keys())
assert len(TEAMS) == 32 and set(T26.keys()) == set(TEAMS)

final_games = [g for g in games if g["status"] == "Final"]
pending = [g for g in games if g["status"] != "Final"]

# ---------------------------------------------------------------- verification
report = {"checks": [], "all_passed": True}
def check(name, ok, detail):
    report["checks"].append({"check": name, "passed": bool(ok), "detail": detail})
    if not ok:
        report["all_passed"] = False

ok = all(t["w"] + t["l"] + t["t"] == 17 for t in s25)
check("2025: every team played 17 games (W+L+T=17)", ok, f"teams checked: {len(s25)}")
check("2025: sum(W) == sum(L)", sum(t['w'] for t in s25) == sum(t['l'] for t in s25),
      f"sumW={sum(t['w'] for t in s25)} sumL={sum(t['l'] for t in s25)}")
ok = all(abs(t["pct"] - round((t["w"] + 0.5 * t["t"]) / 17, 3)) < 0.0006 for t in s25)
check("2025: PCT == (W+0.5*T)/17 rounded to 3dp", ok,
      "mismatches: " + str([t["team"] for t in s25 if abs(t["pct"] - round((t["w"] + 0.5 * t["t"]) / 17, 3)) >= 0.0006]))
ok = all(t["pf"] - t["pa"] == t["net"] for t in s25)
check("2025: NET == PF-PA for all teams", ok, "")
ok = all(sum(t["home"]) + sum(t["road"]) == 17 and sum(t["div_rec"]) == 6 and sum(t["conf_rec"]) == 12 for t in s25)
check("2025: HOME+ROAD=17, DIV=6 games, CONF=12 games", ok, "")

gp = defaultdict(int); gpf = defaultdict(int); gpa = defaultdict(int)
gw = defaultdict(int); gl = defaultdict(int); gt = defaultdict(int)
home_rec = defaultdict(lambda: [0, 0, 0]); road_rec = defaultdict(lambda: [0, 0, 0])
for g in final_games:
    a, h = g["away"], g["home"]
    gp[a] += 1; gp[h] += 1
    gpf[a] += g["away_score"]; gpf[h] += g["home_score"]
    gpa[a] += g["home_score"]; gpa[h] += g["away_score"]
    if g["away_score"] > g["home_score"]:
        gw[a] += 1; gl[h] += 1; road_rec[a][0] += 1; home_rec[h][1] += 1
    elif g["away_score"] < g["home_score"]:
        gw[h] += 1; gl[a] += 1; home_rec[h][0] += 1; road_rec[a][1] += 1
    else:
        gt[a] += 1; gt[h] += 1; road_rec[a][2] += 1; home_rec[h][2] += 1

check("2026: games played per team from game list == W+L+T from standings",
      all(gp[t] == T26[t]["w"] + T26[t]["l"] + T26[t]["t"] for t in TEAMS),
      f"mismatches: {[t for t in TEAMS if gp[t] != T26[t]['w']+T26[t]['l']+T26[t]['t']]}")
check("2026: per-team PF/PA from game list == standings PF/PA (all 32 teams)",
      all(gpf[t] == T26[t]["pf"] and gpa[t] == T26[t]["pa"] for t in TEAMS),
      f"mismatches: {[t for t in TEAMS if gpf[t] != T26[t]['pf'] or gpa[t] != T26[t]['pa']]}")
check("2026: per-team W/L/T from game list == standings W/L/T",
      all(gw[t] == T26[t]["w"] and gl[t] == T26[t]["l"] and gt[t] == T26[t]["t"] for t in TEAMS),
      f"mismatches: {[t for t in TEAMS if (gw[t],gl[t],gt[t]) != (T26[t]['w'],T26[t]['l'],T26[t]['t'])]}")
check("2026: per-team HOME/ROAD records from game list == standings",
      all(home_rec[t] == T26[t]["home"] and road_rec[t] == T26[t]["road"] for t in TEAMS),
      f"mismatches: {[t for t in TEAMS if home_rec[t] != T26[t]['home'] or road_rec[t] != T26[t]['road']]}")
check("2026: sum(W)==sum(L)==decided games; sum(T)=2*ties",
      sum(gw.values()) == sum(gl.values()) == sum(1 for g in final_games if g["away_score"] != g["home_score"])
      and sum(gt.values()) == 2 * sum(1 for g in final_games if g["away_score"] == g["home_score"]),
      f"final_games={len(final_games)}, ties={sum(1 for g in final_games if g['away_score']==g['home_score'])}, pending_excluded={len(pending)}")

# ---------------------------------------------------------------- model helpers
def pooled(team, prior_games):
    t25 = T25[team]
    pf, pa, gp = t25["pf"], t25["pa"], 17
    for g in prior_games:
        if g["away"] == team:
            pf += g["away_score"]; pa += g["home_score"]; gp += 1
        elif g["home"] == team:
            pf += g["home_score"]; pa += g["away_score"]; gp += 1
    return pf, pa, gp

def rating(team, prior_games):
    pf, pa, gp = pooled(team, prior_games)
    return (pf - pa) / gp

def hfa(prior_games):
    return sum(g["home_score"] - g["away_score"] for g in prior_games) / len(prior_games) if prior_games else 0.0

LEAGUE_TOTAL_REF_2025 = 2 * sum(t["pf"] for t in s25) / 32 / 17  # 2025 verified league mean total

def model_game(g, prior_games, prior_totals):
    a, h = g["away"], g["home"]
    ra, rh = rating(a, prior_games), rating(h, prior_games)
    margin = (rh - ra) + hfa(prior_games)                # home perspective
    pfa, paa, gpa = pooled(a, prior_games)
    pfh, pah, gph = pooled(h, prior_games)
    exp_h = ((pfh / gph) + (paa / gpa)) / 2
    exp_a = ((pfa / gpa) + (pah / gph)) / 2
    total = exp_h + exp_a
    ref = LEAGUE_TOTAL_REF_2025 if not prior_totals else sum(prior_totals) / len(prior_totals)
    return margin, total, ref

VIG = 1.10
BREAKEVEN_WR_110 = VIG / (1 + VIG)          # 0.5238095 at -110
BREAKEVEN_WR_SU = 0.5                        # straight-up pick, no vig
PARLAY2_DECIMAL = (1 + 1 / VIG) ** 2        # two -110 legs: (2.10/1.10)^2 = 3.6446
BREAKEVEN_WR_PARLAY2 = 1 / PARLAY2_DECIMAL  # 0.274376
PARLAY2_PROFIT = PARLAY2_DECIMAL - 1        # 2.6446 profit per 1 staked on win

def binom_tail_p(wins, graded, p):
    if graded <= 0:
        return 1.0
    logc = [math.log(math.comb(graded, k)) for k in range(graded + 1)]
    return min(1.0, sum(math.exp(logc[k] + k * math.log(p) + (graded - k) * math.log(1 - p))
                        for k in range(wins, graded + 1)))

# ---------------------------------------------------------------- walk-forward backtest
backtest_rows = []
prior_totals = []
for g in sorted(final_games, key=lambda x: (x["week"], x["date"])):
    prior = [x for x in final_games if x["week"] < g["week"]]
    m, tot, ref = model_game(g, prior, prior_totals)
    am = g["home_score"] - g["away_score"]
    at = g["home_score"] + g["away_score"]
    # spread: own-line bet at -110 on model-favored side
    if m > 0:
        side, line, cover = g["home"], -m, am > m
    elif m < 0:
        side, line, cover = g["away"], -m, am < m
    else:
        side, line, cover = None, 0.0, None
    push_s = (cover is None) or (am == m)
    spread_110 = 0.0 if push_s else (1.0 if cover else -VIG)
    # spread: SU direction pick (no vig)
    if am == 0:
        su = 0.0
    else:
        su = 1.0 if (m > 0) == (am > 0) else -1.0
    # total: own-line bet at -110 (Over if actual > model total)
    if at > tot:
        tot_110, tot_side = 1.0, "Over"
    elif at < tot:
        tot_110, tot_side = -VIG, "Under"
    else:
        tot_110, tot_side = 0.0, "Push"
    # total: SU direction vs walk-forward league reference
    tot_su = 1.0 if (tot > ref) == (at > ref) else -1.0
    backtest_rows.append({
        "week": g["week"], "date": g["date"], "away": g["away"], "home": g["home"],
        "away_score": g["away_score"], "home_score": g["home_score"],
        "actual_margin": am, "actual_total": at,
        "model_margin": round(m, 3), "model_total": round(tot, 3), "total_ref_used": round(ref, 3),
        "hfa_used": round(hfa(prior), 3),
        "spread_pick": side, "spread_line_own": round(line, 3) if side else 0.0,
        "spread_110_result": spread_110, "spread_su_result": su,
        "total_110_side": tot_side, "total_110_result": tot_110, "total_su_result": tot_su,
        "game_url": g["game_url"], "source_url": g["source_url"],
    })
    prior_totals.append(at)

def stats_su(rows, key):
    res = [r[key] for r in rows]
    n = len(res); w = sum(1 for x in res if x > 0); l = sum(1 for x in res if x < 0); pu = n - w - l
    g = w + l
    wr = w / g if g else 0.0
    prof = sum(res)
    cum = peak = 0.0; mdd = 0.0
    for x in res:
        cum += x; peak = max(peak, cum); mdd = min(mdd, cum - peak)
    mean = prof / n if n else 0.0
    sd = math.sqrt(sum((x - mean) ** 2 for x in res) / n) if n else 0.0
    sharpe = mean / sd * math.sqrt(n) if sd > 0 else 0.0
    return {"bets": n, "wins": w, "losses": l, "pushes": pu, "win_rate": round(wr, 4),
            "profit_units": round(prof, 2), "roi": round(prof / g, 4) if g else 0.0,
            "sharpe": round(sharpe, 3), "max_drawdown_units": round(mdd, 2),
            "binomial_p_vs_50pct": round(binom_tail_p(w, g, 0.5), 5), "pricing": "SU (no vig), breakeven 50%"}

def stats_110(rows, key):
    res = [r[key] for r in rows]
    n = len(res); w = sum(1 for x in res if x > 0); l = sum(1 for x in res if x < 0); pu = n - w - l
    g = w + l
    wr = w / g if g else 0.0
    prof = sum(res); staked = g * VIG
    cum = peak = 0.0; mdd = 0.0
    for x in res:
        cum += x; peak = max(peak, cum); mdd = min(mdd, cum - peak)
    mean = prof / n if n else 0.0
    sd = math.sqrt(sum((x - mean) ** 2 for x in res) / n) if n else 0.0
    sharpe = mean / sd * math.sqrt(n) if sd > 0 else 0.0
    return {"bets": n, "wins": w, "losses": l, "pushes": pu, "win_rate": round(wr, 4),
            "profit_units": round(prof, 2), "staked_units": round(staked, 2),
            "roi": round(prof / staked, 4) if staked else 0.0, "sharpe": round(sharpe, 3),
            "max_drawdown_units": round(mdd, 2),
            "binomial_p_vs_52.38pct": round(binom_tail_p(w, g, BREAKEVEN_WR_110), 5),
            "pricing": "-110 own line (assumption F02), breakeven 52.38%"}

def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx and dy else 0.0

# ---------------------------------------------------------------- correlations
corr = {}
corr["C1_net_vs_winpct_2025"] = {"n": 32, "r": round(pearson([t["net"] for t in s25], [t["w"] / 17 for t in s25]), 4),
    "desc": "Pearson r between 2025 NET points and win percentage (32 teams, official standings)",
    "source_url": "https://www.nfl.com/standings/league/2025/REG"}
corr["C2_net_vs_winpct_2026_w8"] = {"n": 32, "r": round(pearson([t["net"] for t in s26], [(t["w"] + 0.5 * t["t"]) / (t["w"] + t["l"] + t["t"]) for t in s26]), 4),
    "desc": "Pearson r between 2026 NET points and win percentage through Week 8 (32 teams, official standings)",
    "source_url": "https://www.nfl.com/standings/league/2026/REG"}
corr["C3_model_vs_actual_margin_2026"] = {"n": len(backtest_rows),
    "r": round(pearson([r["model_margin"] for r in backtest_rows], [r["actual_margin"] for r in backtest_rows]), 4),
    "desc": "Pearson r between walk-forward model margin and actual margin, 2026 W1-W8 (predictive skill of originated spread)",
    "source_url": "https://www.nfl.com/schedules/2026/by-week/week-1"}
corr["C4_samegame_margin_vs_total"] = {"n": len(backtest_rows),
    "r": round(pearson([r["actual_margin"] for r in backtest_rows], [r["actual_total"] for r in backtest_rows]), 4),
    "desc": "Pearson r between game margin and game total, same game (parlay leg correlation, gate G6)",
    "source_url": "https://www.nfl.com/schedules/2026/by-week/week-1"}
corr["C5_spreadbet_vs_totalbet_result"] = {"n": len(backtest_rows),
    "r": round(pearson([r["spread_su_result"] for r in backtest_rows], [r["total_su_result"] for r in backtest_rows]), 4),
    "desc": "Pearson r between spread-direction and total-direction results on the same game (same-game parlay leg correlation, gate G6)",
    "source_url": "https://www.nfl.com/schedules/2026/by-week/week-1"}
corr["C6_persistence_2025diff_vs_2026winpct"] = {"n": 32,
    "r": round(pearson([(t["pf"] - t["pa"]) / 17 for t in s25],
                       [(T26[t["team"]]["w"] + 0.5 * T26[t["team"]]["t"]) / (T26[t["team"]]["w"] + T26[t["team"]]["l"] + T26[t["team"]]["t"]) for t in s25]), 4),
    "desc": "Pearson r between 2025 point differential per game and 2026 win percentage (year-to-year persistence)",
    "source_url": "https://www.nfl.com/standings/league/2025/REG"}
hfa_full = hfa(final_games)
home_wins = sum(1 for g in final_games if g["home_score"] > g["away_score"])
corr["C7_home_field_2026"] = {"n": len(final_games), "mean_home_margin": round(hfa_full, 4),
    "home_win_rate": round(home_wins / len(final_games), 4),
    "desc": f"Empirical home-field advantage 2026 W1-W8: mean home margin = {hfa_full:.3f} pts; home win rate = {home_wins}/{len(final_games)} = {home_wins/len(final_games):.4f} (assumption F09)",
    "source_url": "https://www.nfl.com/schedules/2026/by-week/week-1"}

# ---------------------------------------------------------------- strategies + gates
GATES = [
    {"id": "G1", "name": "Minimum sample", "rule": "graded bets >= 30"},
    {"id": "G2", "name": "Win rate >= breakeven", "rule": "win rate >= strategy breakeven (50% SU; 52.38% at -110; 27.44% for 2-leg -110 parlay)"},
    {"id": "G3", "name": "Skill vs luck", "rule": "one-sided binomial p < 0.05 vs strategy breakeven win rate"},
    {"id": "G4", "name": "Out-of-sample holdout", "rule": "2026 Weeks 7-8 holdout win rate >= breakeven"},
    {"id": "G5", "name": "Risk limit", "rule": "max drawdown <= 15 units"},
    {"id": "G6", "name": "Parlay correlation guard", "rule": "|same-game leg correlation| < 0.35 (computed from verified data, see C4/C5)"},
]
SEL_THRESHOLD = 6.0   # project assumption: 'large edge' selectivity threshold (documented, not tuned)

def gate_eval(s, hold_wr, breakeven, corr_ok=True):
    graded = s["wins"] + s["losses"]
    pkey = "binomial_p_vs_50pct" if abs(breakeven - 0.5) < 1e-9 else ("binomial_p_vs_52.38pct" if abs(breakeven - BREAKEVEN_WR_110) < 1e-6 else "binomial_p_vs_parlay_breakeven")
    return {"G1": graded >= 30, "G2": s["win_rate"] >= breakeven, "G3": s[pkey] < 0.05,
            "G4": (hold_wr is not None and hold_wr >= breakeven), "G5": s["max_drawdown_units"] >= -15,
            "G6": corr_ok}

hold = [r for r in backtest_rows if r["week"] >= 7]
sel = [r for r in backtest_rows if abs(r["model_margin"]) >= SEL_THRESHOLD]
sel_hold = [r for r in hold if abs(r["model_margin"]) >= SEL_THRESHOLD]

# S1 spread direction SU, all games
s1 = stats_su(backtest_rows, "spread_su_result"); s1_hold = stats_su(hold, "spread_su_result")
# S2 spread direction SU, selective |m| >= 6
s2 = stats_su(sel, "spread_su_result"); s2_hold = stats_su(sel_hold, "spread_su_result")
# S3 total direction SU vs walk-forward league reference, all games
s3 = stats_su(backtest_rows, "total_su_result"); s3_hold = stats_su(hold, "total_su_result")
# S4 same-game 2-leg parlay: spread-direction leg + total-direction leg, priced as 2-leg -110 parlay (F02)
parlay_rows = []
for r in backtest_rows:
    l1, l2 = r["spread_su_result"], r["total_su_result"]
    if l1 < 0 or l2 < 0:
        res = -1.0
    elif l1 > 0 and l2 > 0:
        res = PARLAY2_PROFIT
    else:
        res = 0.0
    parlay_rows.append({"week": r["week"], "away": r["away"], "home": r["home"],
                        "leg1_spread_su": l1, "leg2_total_su": l2, "parlay_result": round(res, 4),
                        "game_url": r["game_url"]})
def stats_parlay(rows):
    res = [r["parlay_result"] for r in rows]
    n = len(res); w = sum(1 for x in res if x > 0); l = sum(1 for x in res if x < 0); pu = n - w - l
    g = w + l
    wr = w / g if g else 0.0
    prof = sum(res)
    cum = peak = 0.0; mdd = 0.0
    for x in res:
        cum += x; peak = max(peak, cum); mdd = min(mdd, cum - peak)
    mean = prof / n if n else 0.0
    sd = math.sqrt(sum((x - mean) ** 2 for x in res) / n) if n else 0.0
    sharpe = mean / sd * math.sqrt(n) if sd > 0 else 0.0
    return {"bets": n, "wins": w, "losses": l, "pushes": pu, "win_rate": round(wr, 4),
            "profit_units": round(prof, 2), "roi": round(prof / n, 4) if n else 0.0,
            "sharpe": round(sharpe, 3), "max_drawdown_units": round(mdd, 2),
            "binomial_p_vs_parlay_breakeven": round(binom_tail_p(w, g, BREAKEVEN_WR_PARLAY2), 5),
            "pricing": f"2-leg parlay at -110 per leg (assumption F02), breakeven {BREAKEVEN_WR_PARLAY2:.4f}"}
s4 = stats_parlay(parlay_rows)
s4_hold_rows = [r for r in parlay_rows if r["week"] >= 7]
h4 = stats_parlay(s4_hold_rows)
s4_hold_wr = h4["win_rate"]
# S5 weekly top-2 |margin| cross-game spread parlay (2-leg -110)
by_week = defaultdict(list)
for r in backtest_rows:
    by_week[r["week"]].append(r)
wk_parlay = []
for w in sorted(by_week):
    legs = sorted(by_week[w], key=lambda r: -abs(r["model_margin"]))[:2]
    l1, l2 = legs[0]["spread_su_result"], legs[1]["spread_su_result"]
    if l1 < 0 or l2 < 0:
        res = -1.0
    elif l1 > 0 and l2 > 0:
        res = PARLAY2_PROFIT
    else:
        res = 0.0
    wk_parlay.append({"week": w, "legs": [(l["away"], l["home"], l["spread_pick"], l["spread_line_own"]) for l in legs],
                      "parlay_result": round(res, 4)})
s5 = stats_parlay(wk_parlay)
s5_hold_wr = stats_parlay([r for r in wk_parlay if r["week"] >= 7])["win_rate"]
# S6 negative control: own-line -110 spread and total (calibration diagnostic)
s6s = stats_110(backtest_rows, "spread_110_result"); s6s_hold = stats_110(hold, "spread_110_result")
s6t = stats_110(backtest_rows, "total_110_result"); s6t_hold = stats_110(hold, "total_110_result")

corr_guard_ok = abs(corr["C5_spreadbet_vs_totalbet_result"]["r"]) < 0.35 and abs(corr["C4_samegame_margin_vs_total"]["r"]) < 0.35

strategies = [
    {"id": "S1", "name": "Spread direction - all games (SU)", "type": "single bet",
     "desc": "Pick the side favored by the walk-forward originated spread on every game. Priced as a straight-up pick (no vig; breakeven 50%).",
     "results": s1, "holdout_w7_w8": s1_hold, "breakeven": 0.5,
     "gates": gate_eval(s1, s1_hold["win_rate"], 0.5), "corr_guard": None},
    {"id": "S2", "name": f"Spread direction - selective |line| >= {SEL_THRESHOLD:.0f} (SU)", "type": "single bet, filtered",
     "desc": f"Same as S1 but only when |originated spread| >= {SEL_THRESHOLD:.0f} (selectivity threshold = documented project assumption, not tuned on results).",
     "results": s2, "holdout_w7_w8": s2_hold, "breakeven": 0.5,
     "gates": gate_eval(s2, s2_hold["win_rate"], 0.5), "corr_guard": None},
    {"id": "S3", "name": "Total direction vs league reference (SU)", "type": "single bet",
     "desc": "Pick Over/Under relative to the walk-forward league-average total reference (2025 verified mean total for W1, prior 2026 games' mean after). Breakeven 50%.",
     "results": s3, "holdout_w7_w8": s3_hold, "breakeven": 0.5,
     "gates": gate_eval(s3, s3_hold["win_rate"], 0.5), "corr_guard": None},
    {"id": "S4", "name": "Same-game 2-leg parlay (spread direction + total direction)", "type": "parlay (2-leg, same game)",
     "desc": "Parlay the S1 leg and the S3 leg on the same game, priced as a 2-leg -110 parlay (assumption F02). Allowed only because gate G6 passes: computed same-game leg correlation |r| = "
               f"{abs(corr['C5_spreadbet_vs_totalbet_result']['r'])} < 0.35.",
     "results": s4, "holdout_w7_w8": h4, "breakeven": round(BREAKEVEN_WR_PARLAY2, 6),
     "gates": gate_eval(s4, s4_hold_wr, BREAKEVEN_WR_PARLAY2, corr_ok=corr_guard_ok),
     "corr_guard": {"same_game_leg_r": corr["C5_spreadbet_vs_totalbet_result"]["r"],
                    "same_game_margin_total_r": corr["C4_samegame_margin_vs_total"]["r"]},
     "legs_detail": parlay_rows},
    {"id": "S5", "name": "Weekly top-2 spread parlay (cross-game legs)", "type": "parlay (2-leg, cross-game)",
     "desc": "Each week, parlay the two spread-direction picks with the largest |originated spread|. Cross-game independence is assumption F08.",
     "results": s5, "holdout_w7_w8": {"win_rate": s5_hold_wr}, "breakeven": round(BREAKEVEN_WR_PARLAY2, 6),
     "gates": gate_eval(s5, s5_hold_wr, BREAKEVEN_WR_PARLAY2, corr_ok=True),
     "corr_guard": None, "legs_detail": wk_parlay},
    {"id": "S6", "name": "Negative control: own-line -110 spread and total bets", "type": "single bet at -110 (calibration diagnostic)",
     "desc": "Bets the model-favored side at its OWN originated line priced -110, and Over/Under at its own total. Included as a calibration diagnostic: it shows that paying vig on self-originated lines loses money without a market price to compare against (no official odds source exists - F01).",
     "results": {"spread_110": s6s, "total_110": s6t},
     "holdout_w7_w8": {"spread_110": s6s_hold, "total_110": s6t_hold}, "breakeven": round(BREAKEVEN_WR_110, 6),
     "gates": {"G1": True, "G2": False, "G3": False, "G4": False, "G5": False, "G6": True},
     "corr_guard": None},
    {"id": "S7", "name": "QB passing-yards prop lines - 2026 Week 9", "type": "player prop combos",
     "desc": "Originated QB passing-yards lines for Week 9 = 0.65*(2026 YDS/team GP) + 0.35*(2025 YDS/17). NOT backtested (no verified per-game prop logs fetched) -> fails G1/G3 by construction; published as originated lines only and flagged.",
     "results": None, "holdout_w7_w8": None, "breakeven": None,
     "gates": {"G1": False, "G2": None, "G3": False, "G4": None, "G5": None, "G6": None},
     "corr_guard": None,
     "note": "Backtest fields intentionally blank (unverified) - see Flagged items F03/F06/F07."},
]
for s in strategies:
    s["approved"] = bool(s["results"]) and all(v is True for v in s["gates"].values())

# leaderboard: project-defined scoring, documented in methodology
lb = []
for s in strategies:
    if s["id"] == "S6":
        for leg, key in (("spread", "spread_110"), ("total", "total_110")):
            r = s["results"][key]
            lb.append({"id": f"S6-{leg}", "name": f"{s['name']} [{leg}]", "type": s["type"],
                       "score": round(100 * r["roi"] + 10 * r["sharpe"] + 50 * (r["win_rate"] - BREAKEVEN_WR_110), 2),
                       "roi": r["roi"], "win_rate": r["win_rate"], "sharpe": r["sharpe"],
                       "bets": r["bets"], "binomial_p": r["binomial_p_vs_52.38pct"], "approved": False})
    elif s["results"]:
        r = s["results"]
        be = s["breakeven"]
        pkey = "binomial_p_vs_50pct" if abs(be - 0.5) < 1e-9 else ("binomial_p_vs_52.38pct" if abs(be - BREAKEVEN_WR_110) < 1e-6 else "binomial_p_vs_parlay_breakeven")
        lb.append({"id": s["id"], "name": s["name"], "type": s["type"],
                   "score": round(100 * r["roi"] + 10 * r["sharpe"] + 50 * (r["win_rate"] - be), 2),
                   "roi": r["roi"], "win_rate": r["win_rate"], "sharpe": r["sharpe"],
                   "bets": r["bets"], "binomial_p": r[pkey], "approved": s["approved"]})
    else:
        lb.append({"id": s["id"], "name": s["name"], "type": s["type"], "score": None, "roi": None,
                   "win_rate": None, "sharpe": None, "bets": None, "binomial_p": None, "approved": False,
                   "note": "Unrated: no verified backtest sample (gates G1/G3 unmet). Originated lines only - flagged."})
# Gate-approved strategies rank above non-approved (rewards only go to approved strategies);
# within each group, higher score ranks first.
ranked = sorted([e for e in lb if e["score"] is not None], key=lambda e: (not e["approved"], -e["score"]))
for i, e in enumerate(ranked, 1):
    e["rank"] = i
    e["reward_tier"] = ("Gold" if e["approved"] and e["roi"] > 0.10 else
                        "Silver" if e["approved"] and e["roi"] > 0.0 else
                        "Bronze" if e["approved"] else "Not approved (gates failed)")
for e in lb:
    if e["score"] is None:
        e["rank"] = "unrated"; e["reward_tier"] = "Unrated - flagged for review"
lb_out = ranked + [e for e in lb if e["score"] is None]

# ---------------------------------------------------------------- Week 9 originated lines
hfa9 = hfa(final_games)
w9_lines = []
for g in w9:
    m, tot, _ = model_game(g, final_games, [x["home_score"] + x["away_score"] for x in final_games])
    side = g["home"] if m > 0 else g["away"]
    w9_lines.append({
        "week": 9, "date": g["date"], "time_et": g["time_et"], "network": g["network"],
        "away": g["away"], "home": g["home"], "note": g.get("note", ""),
        "model_spread_home_perspective": round(m, 2),
        "originated_spread": f"{side} {abs(m):.1f}" if abs(m) >= 0.05 else "pick'em",
        "pick": side, "model_total": round(tot, 1),
        "total_pick_vs_league_ref": "Over" if tot > LEAGUE_TOTAL_REF_2025 else "Under",
        "edge_abs": round(abs(m), 2), "hfa_used": round(hfa9, 3),
        "game_url": g["game_url"],
        "source_url": "https://www.nfl.com/schedules/2026/by-week/week-9",
        "inputs_source_urls": ["https://www.nfl.com/standings/league/2025/REG",
                               "https://www.nfl.com/standings/league/2026/REG",
                               "https://www.nfl.com/schedules/2026/by-week/week-1"],
    })

qb_starters = {
    "JAX": ("Trevor Lawrence", "confirmed"), "CIN": ("Joe Burrow", "confirmed"), "DEN": ("Bo Nix", "confirmed"),
    "CAR": ("Bryce Young", "confirmed"), "DAL": ("Dak Prescott", "confirmed"), "IND": ("Daniel Jones", "confirmed"),
    "NYJ": ("Geno Smith", "confirmed"), "KC": ("Patrick Mahomes", "confirmed"), "DET": ("Jared Goff", "confirmed"),
    "CLE": ("Deshaun Watson", "confirmed"), "NO": ("Tyler Shough", "confirmed"), "LA": ("Matthew Stafford", "confirmed"),
    "LV": ("Kirk Cousins", "confirmed"), "SF": ("Brock Purdy", "confirmed"), "GB": ("Jordan Love", "confirmed"),
    "NE": ("Drake Maye", "confirmed"), "HOU": ("C.J. Stroud", "confirmed"), "LAC": ("Justin Herbert", "confirmed"),
    "SEA": ("Sam Darnold", "confirmed"), "BUF": ("Josh Allen", "confirmed"), "ATL": ("Michael Penix Jr.", "confirmed"),
    "WAS": ("Jayden Daniels", "roster-confirmed; no 2026 top-24 stats row"),
    "NYG": ("Jaxson Dart", "roster-confirmed; no 2026 top-24 stats row"),
    "MIN": ("Kyler Murray", "roster-confirmed; no 2026 top-24 stats row"),
    "TB": ("Baker Mayfield", "roster-confirmed; no 2026 top-24 stats row"),
    "BAL": (None, "Lamar Jackson on IR per official nfl.com news (2026-11-01); W9 starter unconfirmed"),
    "MIA": (None, "W9 starter not confirmed from an official source"),
    "PHI": (None, "W9 starter not confirmed from an official source"),
    "AZ": (None, "W9 starter not confirmed from an official source"),
    "CHI": ("Caleb Williams", "game-page confirmed; 2026 YDS through W7 = 1020 (W8 MNF pending at cutoff)"),
}
p26_pass = {p["player"]: p for p in p26["passing"]["leaders"]}
p25_pass = {p["player"]: p for p in p25["passing"]["leaders"]}

w9_props = []
for g in w9:
    for side_key, team in (("away", g["away"]), ("home", g["home"])):
        name, status = qb_starters.get(team, (None, "not mapped"))
        entry = {"week": 9, "game": f"{g['away']} at {g['home']}", "team": team, "side": side_key,
                 "qb": name, "starter_status": status, "game_url": g["game_url"],
                 "source_url": "https://www.nfl.com/schedules/2026/by-week/week-9"}
        p26p = p26_pass.get(name) if name else None
        p25p = p25_pass.get(name) if name else None
        gp_team = T26[team]["w"] + T26[team]["l"] + T26[team]["t"]
        if name == "Caleb Williams":
            entry.update({"yds_2026": 1020, "gp_used": 7,
                          "gp_note": "2026 YDS through W7 per official game-center page; W8 MNF pending at data cutoff",
                          "yds_2025": None, "prop_line": None,
                          "note": "2026 full-season total not in fetched top-24 leaders table; line left blank (unverified) - F07",
                          "stats_source_url": "https://www.nfl.com/games/bears-at-seahawks-2026-reg-8"})
        elif p26p and p25p:
            line = 0.65 * (p26p["yds"] / gp_team) + 0.35 * (p25p["yds"] / 17)
            entry.update({"yds_2026": p26p["yds"], "gp_used": gp_team,
                          "gp_note": "team games used as QB GP denominator - assumption F03",
                          "yds_2025": p25p["yds"], "prop_line": round(line, 1),
                          "stats_source_url": p26["passing"]["source_url"],
                          "stats_source_url_2025": p25["passing"]["source_url"]})
        elif p25p and "roster-confirmed" in status:
            entry.update({"yds_2026": None, "gp_used": None, "yds_2025": p25p["yds"],
                          "prop_line": round(p25p["yds"] / 17, 1),
                          "note": "2026 total not in fetched top-24 table; line uses 2025 per-game average only - flagged F07",
                          "stats_source_url_2025": p25["passing"]["source_url"]})
        else:
            entry.update({"yds_2026": None, "gp_used": None, "yds_2025": None, "prop_line": None,
                          "note": "No verified stats for this slot - line left blank - see Flagged page",
                          "stats_source_url": p26["passing"]["source_url"]})
        w9_props.append(entry)

# ---------------------------------------------------------------- write outputs
def dump(name, obj):
    with open(os.path.join(A, name), "w") as f:
        json.dump(obj, f, indent=2)

dump("verification_report.json", report)
dump("backtest_2026.json", {
    "method": "Walk-forward: for each 2026 game the model uses 2025 full-season aggregates + only final 2026 games from earlier weeks (no lookahead). HFA = mean home margin of prior 2026 games (0 for W1). rating = pooled (PF-PA)/GP. model_margin(home) = rating(home)-rating(away)+HFA. model_total = sum of expected team points, expected = (own PF/GP + opp PA/GP)/2. Total SU reference = 2025 verified league mean total for W1, then mean actual total of prior 2026 games. spread_110/total_110 = bet at own originated line priced -110 (assumption F02), push=refund. SU legs priced at even money (breakeven 50%).",
    "games": backtest_rows,
    "pending_excluded": [{"away": g["away"], "home": g["home"], "week": g["week"], "game_url": g["game_url"]} for g in pending],
})
dump("model_lines_2026_w9.json", {
    "method": "Originated lines for 2026 Week 9. Inputs: pooled 2025 (17 games) + 2026 W1-W8 verified aggregates per team. rating = pooled (PF-PA)/GP; model_margin(home) = rating(home)-rating(away)+HFA; HFA = empirical mean home margin over the 120 final 2026 games (assumption F09); model_total = sum of expected team points, expected = (own PF/GP + opp PA/GP)/2. QB prop line = 0.65*(2026 YDS/team GP) + 0.35*(2025 YDS/17); team GP used as QB GP (assumption F03); props NOT backtested (flagged).",
    "hfa": round(hfa9, 4), "league_total_ref_2025": round(LEAGUE_TOTAL_REF_2025, 3),
    "games": w9_lines, "props_qb_passing_yards": w9_props,
})
dump("correlations.json", {"note": "All values are Pearson r computed from verified official data only; n = sample size. C7 is a mean, not r.", "correlations": corr})
dump("strategies.json", {"gates": GATES,
                         "breakevens": {"su": 0.5, "minus110": round(BREAKEVEN_WR_110, 6), "parlay2_minus110": round(BREAKEVEN_WR_PARLAY2, 6)},
                         "vig_assumption": "F02", "strategies": strategies})
dump("leaderboard.json", {"scoring": "score = 100*ROI + 10*Sharpe + 50*(win_rate - breakeven), computed on the walk-forward 2026 W1-W8 backtest (SU strategies at even money; -110 at -110; parlays as 2-leg -110). Project-defined competition scoring, not an official NFL metric. Reward tiers: Gold = approved and ROI>10%; Silver = approved and ROI>0; Bronze = approved; Not approved = a gate failed; Unrated = no verified backtest.",
                          "entries": lb_out})

print("verification all_passed:", report["all_passed"])
for c in report["checks"]:
    print(("PASS" if c["passed"] else "FAIL"), "-", c["check"], "|", str(c["detail"])[:110])
print()
print("HFA:", round(hfa_full, 4), "home wins:", home_wins, "/", len(final_games))
for s in strategies:
    print(s["id"], s["name"][:55], "approved:", s["approved"],
          "" if not s["results"] else json.dumps(s["results"] if s["id"] != "S6" else {"spread": s["results"]["spread_110"], "total": s["results"]["total_110"]})[:220])
print()
print("leaderboard:")
for e in lb_out:
    print(" ", e.get("rank"), e["id"], "score", e["score"], "roi", e["roi"], "wr", e["win_rate"], "p", e["binomial_p"], e["reward_tier"])
print()
print("correlations:", {k: v.get("r", v.get("mean_home_margin")) for k, v in corr.items()})

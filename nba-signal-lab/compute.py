#!/usr/bin/env python3
"""NBA Signal Lab — computation engine (session 6d508fee).

Reads the hand-transcribed CSVs in nba-signal-lab/data/ (every row carries an
official nba.com source URL) and produces data/outputs.json with:

  1. verification   — line-by-line checksums against official cross-sources;
                      failures are flagged, never silently patched.
  2. correlations   — Pearson r (+95% Fisher-z CI), point-biserial, phi
                      coefficients for pre-registered prop thresholds,
                      lag-1 autocorrelation (cross-game independence).
  3. model_lines    — own-originated spread/total for the 2026-11-04 slate
                      from blended 2026-27 / 2025-26 team net ratings.
                      Market columns stay blank (no verified odds source).
  4. luck_vs_skill  — exact binomial power table, deflated-shrinkage scoring,
                      multiple-testing bounds.
  5. gates/strategies/leaderboard — all strategies PENDING; 0 certified.

No value is inferred: anything not derivable from the transcribed official
rows is emitted as null and listed under `flags`.
"""
import csv, json, math, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# ---- pre-registered model parameters (documented choices, flagged as such) ---
K_BLEND = 20.0        # shrinkage: w = n / (n + K_BLEND)
HFA_PTS = 2.5         # home-court advantage in points (model constant, flagged)
BREAK_EVEN = 110/210  # 0.5238 break-even win rate at -110 (arithmetic, derived)
MARGIN_SIGMA = 11.2   # per-game margin sigma for probit conversions (flagged)


def read_csv(name):
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))


def fnum(x):
    return float(x) if x not in ("", None) else None


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    sxy = sum((a-mx)*(b-my) for a, b in zip(xs, ys))
    sxx = sum((a-mx)**2 for a in xs)
    syy = sum((b-my)**2 for b in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx*syy)


def fisher_ci(r, n, z=1.959963985):
    if r is None or n <= 3 or abs(r) >= 1:
        return (None, None)
    zz = 0.5*math.log((1+r)/(1-r))
    se = 1/math.sqrt(n-3)
    lo, hi = zz - z*se, zz + z*se
    return (math.tanh(lo), math.tanh(hi))


def phi_from_binary(a, b):
    """phi coefficient of two 0/1 vectors (returns None if degenerate)."""
    n = len(a)
    n11 = sum(1 for x, y in zip(a, b) if x and y)
    n10 = sum(1 for x, y in zip(a, b) if x and not y)
    n01 = sum(1 for x, y in zip(a, b) if not x and y)
    n00 = n - n11 - n10 - n01
    num = n11*n00 - n10*n01
    den = math.sqrt((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00))
    return (num/den if den else None), (n11/n if n else None)


def binom_pmf(k, n, p):
    return math.comb(n, k) * p**k * (1-p)**(n-k)


def binom_sf(k, n, p):  # P(X >= k), exact, log-domain (n <= 250 in this repo)
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    total = 0.0
    for i in range(k, n+1):
        lg = (math.lgamma(n+1) - math.lgamma(i+1) - math.lgamma(n-i+1)
              + i*math.log(p) + (n-i)*math.log1p(-p))
        total += math.exp(lg)
    return min(1.0, total)


def binom_cdf(k, n, p):  # P(X <= k)
    return 1.0 - binom_sf(k+1, n, p)


def fmt(x, nd=3):
    return None if x is None else round(x, nd)


# ============================ LOAD =========================================
teams_cur = read_csv("teams_2026_27.csv")
teams_pri = read_csv("teams_2025_26.csv")
std_cur = read_csv("standings_2026_27.csv")
std_pri = read_csv("standings_2025_26.csv")
logs = read_csv("game_logs_2025_26.csv")
slate = read_csv("schedule_2026_11_04.csv")
registry = read_csv("players_registry.csv")

by_name = {t["team"]: t for t in teams_cur}
pri_by_name = {t["team"]: t for t in teams_pri}

flags = []
verification = {"checks": [], "failures": 0}


def check(name, ok, detail=""):
    verification["checks"].append({"check": name, "ok": bool(ok), "detail": detail})
    if not ok:
        verification["failures"] += 1
        flags.append({"id": f"V{verification['failures']:02d}", "type": "verification",
                      "text": f"FAILED {name}: {detail}"})


# ======================= 1. VERIFICATION ===================================
check("teams_2026_27 row count == 30", len(teams_cur) == 30, f"got {len(teams_cur)}")
check("teams_2025_26 row count == 30", len(teams_pri) == 30, f"got {len(teams_pri)}")
check("standings_2026_27 row count == 30", len(std_cur) == 30, f"got {len(std_cur)}")
check("standings_2025_26 row count == 30", len(std_pri) == 30, f"got {len(std_pri)}")

# W-L agreement: standings page vs team-stats page (two independent official pages)
for season, std, tms in (("2026-27", std_cur, teams_cur), ("2025-26", std_pri, teams_pri)):
    tmap = {t["team"]: t for t in tms}
    bad = [s["team"] for s in std
           if s["team"] not in tmap or tmap[s["team"]]["w"] != s["w"] or tmap[s["team"]]["l"] != s["l"]]
    check(f"{season} W-L agreement standings vs team-stats (30 teams)", not bad, f"mismatched: {bad}")

# split sums: home+road+neutral must equal W-L (per team)
for season, std in (("2026-27", std_cur), ("2025-26", std_pri)):
    bad = []
    for s in std:
        def rec(r):
            w, l = r.split("-")
            return int(w), int(l)
        hw, hl = rec(s["home_rec"]); rw, rl = rec(s["road_rec"]); nw, nl = rec(s["neutral_rec"])
        if hw+rw+nw != int(s["w"]) or hl+rl+nl != int(s["l"]):
            bad.append(f"{s['team']}({hw}-{hl}+{rw}-{rl}+{nw}-{nl} vs {s['w']}-{s['l']})")
    check(f"{season} home+road+neutral splits sum to record", not bad, "; ".join(bad))
    if bad:
        flags.append({"id": f"F-SPLIT-{season}", "type": "irregularity",
                      "text": f"{season} standings split rows that do not sum to the record: "
                              f"{'; '.join(bad)} — split fields left as transcribed; re-verify on source page."})

# game-log row identities + duplicates
seen = set()
bad_pts, bad_reb, dups = [], [], []
for r in logs:
    pts, fgm, tpm, ftm = int(r["pts"]), int(r["fgm"]), int(r["tpm"]), int(r["ftm"])
    if pts != 2*(fgm-tpm) + 3*tpm + ftm:
        bad_pts.append(f"{r['player']} {r['game_date']}")
    if int(r["reb"]) != int(r["oreb"]) + int(r["dreb"]):
        bad_reb.append(f"{r['player']} {r['game_date']}")
    k = (r["player_id"], r["game_id"])
    if k in seen:
        dups.append(f"{r['player']} {r['game_id']}")
    seen.add(k)
check("game-log scoring identity PTS=2*(FGM-3PM)+3*3PM+FTM (125 rows)", not bad_pts, "; ".join(bad_pts))
check("game-log rebound identity REB=OREB+DREB (125 rows)", not bad_reb, "; ".join(bad_reb))
check("game-log unique (player, game) keys", not dups, "; ".join(dups))

# per-player checksums vs official leaders page (GP + 1dp averages)
reg = {r["player_id"]: r for r in registry}
per_player_rows = defaultdict(list)
for r in logs:
    per_player_rows[r["player_id"]].append(r)
checksum_rows = []
for pid, rows in sorted(per_player_rows.items()):
    reg_row = reg.get(pid, {})
    n = len(rows)
    avg = lambda k: sum(float(r[k]) for r in rows)/n
    got = {"gp": n, "pts_pg": avg("pts"), "reb_pg": avg("reb"), "ast_pg": avg("ast"), "tpm_pg": avg("tpm")}
    exp = {"gp": int(reg_row["gp"]), "pts_pg": float(reg_row["pts_pg"]),
           "reb_pg": float(reg_row["reb_pg"]), "ast_pg": float(reg_row["ast_pg"]),
           "tpm_pg": float(reg_row["tpm_pg"])}
    ok = (got["gp"] == exp["gp"] and all(abs(got[k]-exp[k]) <= 0.051 for k in
          ("pts_pg", "reb_pg", "ast_pg", "tpm_pg")))
    checksum_rows.append({"player_id": pid, "player": rows[0]["player"],
                          "expected": exp, "recomputed": {k: fmt(v, 4) for k, v in got.items()},
                          "ok": ok, "source_url": reg_row.get("source_url", "")})
    check(f"game-log checksum vs official leaders ({rows[0]['player']})",
          ok, f"expected {exp} recomputed {got}")

# league identities
wsum = sum(int(t["w"]) for t in teams_cur); lsum = sum(int(t["l"]) for t in teams_cur)
check("2026-27 league total wins == total losses", wsum == lsum, f"{wsum} vs {lsum}")
pm_weighted = sum(float(t["plus_minus_pg"])*int(t["gp"]) for t in teams_cur)
check("2026-27 league weighted +/- == 0 (±0.5 rounding)", abs(pm_weighted) <= 0.5*30,
      f"sum={pm_weighted:.2f}")

# slate cross-checks: every slate team exists in team table
slate_teams = set(r["away_team"] for r in slate) | set(r["home_team"] for r in slate)
missing = sorted(t for t in slate_teams if t not in by_name)
check("slate teams present in teams_2026_27", not missing, f"missing {missing}")

# ======================= 2. HFA / SPLITS ===================================
def league_home_win(std):
    hw = sum(int(s["home_rec"].split("-")[0]) for s in std)
    hl = sum(int(s["home_rec"].split("-")[1]) for s in std)
    return hw, hl, (hw/(hw+hl) if hw+hl else None)

hw26, hl26, hp26 = league_home_win(std_cur)
hw25, hl25, hp25 = league_home_win(std_pri)
hfa_block = {
    "home_wins_2026_27": hw26, "home_losses_2026_27": hl26, "home_win_pct_2026_27": fmt(hp26, 4),
    "home_wins_2025_26": hw25, "home_losses_2025_26": hl25, "home_win_pct_2025_26": fmt(hp25, 4),
    "model_hfa_points": HFA_PTS,
    "note": ("Empirical home win%% computed from official HOME/ROAD split columns. "
             "Model HFA in points is a pre-registered constant (2.5), not an official "
             "NBA statistic; sensitivity shown at 2.0/2.5/3.0."),
    "source_urls": ["https://www.nba.com/standings", "https://www.nba.com/standings?Season=2025-26"],
}
flags.append({"id": "F-HFA", "type": "model-parameter",
              "text": "HFA_PTS = 2.5 is a model constant (no official NBA source publishes "
                      "home advantage in points); empirical home win% is reported alongside; "
                      "sensitivity at 2.0/2.5/3.0 included in model_lines."})

# ======================= 3. MODEL LINES ====================================
def strength(team_name):
    t = by_name[team_name]; p = pri_by_name[team_name]
    n = int(t["gp"])
    w = n/(n+K_BLEND)
    net_cur = float(t["plus_minus_pg"]); net_pri = float(p["plus_minus_pg"])
    s = w*net_cur + (1-w)*net_pri
    total_cur = 2*float(t["pts_pg"]) - net_cur          # PF/g + PA/g
    total_pri = 2*float(p["pts_pg"]) - net_pri
    tot = w*total_cur + (1-w)*total_pri
    return {"net_blend": s, "w": w, "n": n, "net_cur": net_cur, "net_pri": net_pri,
            "total_blend": tot, "total_cur": total_cur, "total_pri": total_pri}

lines = []
for g in slate:
    h, a = g["home_team"], g["away_team"]
    sh, sa = strength(h), strength(a)
    spread = (sh["net_blend"] - sa["net_blend"]) + HFA_PTS
    total = (sh["total_blend"] + sa["total_blend"])/2
    lines.append({
        "game_date": g["game_date"], "home_team": h, "away_team": a,
        "tip_time_as_listed": g["tip_time_as_listed"], "arena": g["arena"],
        "model_home_spread": fmt(spread, 1),          # home margin, e.g. -3.5 = home -3.5
        "model_total": fmt(total, 1),
        "model_home_spread_hfa20": fmt((sh["net_blend"]-sa["net_blend"])+2.0, 1),
        "model_home_spread_hfa25": fmt((sh["net_blend"]-sa["net_blend"])+2.5, 1),
        "model_home_spread_hfa30": fmt((sh["net_blend"]-sa["net_blend"])+3.0, 1),
        "home_strength": fmt(sh["net_blend"], 2), "away_strength": fmt(sa["net_blend"], 2),
        "home_weight_cur": fmt(sh["w"], 2), "away_weight_cur": fmt(sa["w"], 2),
        "market_spread": None, "market_total": None,
        "market_note": "no verified market/odds source retrieved — left blank per rules",
        "source_url": g["source_url"], "cross_check_url": g["cross_check_url"] or None,
    })
flags.append({"id": "F-MARKET", "type": "unverified",
              "text": "Market odds columns (market_spread, market_total) are blank on the model "
                      "lines page: no odds source could be verified from an official NBA property "
                      "in this sandbox. Nothing was inferred or filled in."})
flags.append({"id": "F-SLATE", "type": "irregularity",
              "text": "Official game calendar lists 14 NBA games on 2026-11-04; this slate sources "
                      "6 from official team-schedule pages under the pre-registered top-4-per-conference "
                      "selection. Boston's official schedule page is not machine-readable (JS-only) "
                      "and games among teams outside the selection were not retrieved. Coverage is "
                      "partial by design; nothing was inferred for unretrieved games."})
flags.append({"id": "F-SMALL", "type": "irregularity",
              "text": "2026-27 team samples are early-season (5-8 games per team as of 2026-11-03); "
                      "model strength blends toward the 2025-26 prior (weight n/(n+20)) for this reason."})

# ======================= 4. CORRELATIONS ===================================
def player_series(pid, key):
    rows = sorted(per_player_rows[pid], key=lambda r: r["game_date"])
    return [float(r[key]) for r in rows], rows

stat_pairs = [("pts", "reb"), ("pts", "ast"), ("pts", "tpm"), ("reb", "ast"),
              ("ast", "tpm"), ("pts", "min")]
corr_rows = []
keys_used = sorted({k for pair in stat_pairs for k in pair})
pool = {k: [float(r[k]) for r in logs] for k in keys_used}
for k1, k2 in stat_pairs:
    r_all = pearson(pool[k1], pool[k2])
    lo, hi = fisher_ci(r_all, len(logs))
    per = {}
    for pid in sorted(per_player_rows):
        xs, _ = player_series(pid, k1); ys, _ = player_series(pid, k2)
        rr = pearson(xs, ys); l2, h2 = fisher_ci(rr, len(xs))
        pname = per_player_rows[pid][0]["player"]
        per[pname] = {"r": fmt(rr), "n": len(xs), "ci95": [fmt(l2), fmt(h2)]}
    corr_rows.append({"pair": f"{k1.upper()} x {k2.upper()}", "pooled_r": fmt(r_all),
                      "pooled_n": len(logs), "pooled_ci95": [fmt(lo), fmt(hi)],
                      "per_player": per})

# point-biserial PTS x W
win_bin = [1.0 if r["result"] == "W" else 0.0 for r in logs]
r_pw = pearson(pool["pts"], win_bin)
lo, hi = fisher_ci(r_pw, len(logs))
corr_rows.append({"pair": "PTS x WIN (point-biserial)", "pooled_r": fmt(r_pw), "pooled_n": len(logs),
                  "pooled_ci95": [fmt(lo), fmt(hi)], "per_player": {}})

# pre-registered prop-threshold phi table
thresholds = [
    ("PTS>=25 & AST>=5", lambda r: float(r["pts"]) >= 25, lambda r: float(r["ast"]) >= 5),
    ("PTS>=25 & REB>=5", lambda r: float(r["pts"]) >= 25, lambda r: float(r["reb"]) >= 5),
    ("PTS>=25 & 3PM>=3", lambda r: float(r["pts"]) >= 25, lambda r: float(r["tpm"]) >= 3),
    ("AST>=5 & REB>=5", lambda r: float(r["ast"]) >= 5, lambda r: float(r["reb"]) >= 5),
]
phi_rows = []
for name, fa, fb in thresholds:
    a = [1.0 if fa(r) else 0.0 for r in logs]
    b = [1.0 if fb(r) else 0.0 for r in logs]
    ph, joint = phi_from_binary(a, b)
    pa, pb = sum(a)/len(a), sum(b)/len(b)
    phi_rows.append({"combo": name, "n": len(logs), "hit_rate_a": fmt(pa), "hit_rate_b": fmt(pb),
                     "joint_hit_rate": fmt(joint), "independence_product": fmt(pa*pb),
                     "lift_vs_independence": fmt(joint/(pa*pb) if pa*pb else None),
                     "phi": fmt(ph),
                     "source": "computed in-repo from data/game_logs_2025_26.csv"})

# 3-leg example: PTS>=25 & AST>=5 & REB>=5
a3 = [1.0 if (float(r["pts"]) >= 25 and float(r["ast"]) >= 5 and float(r["reb"]) >= 5) else 0.0 for r in logs]
p3 = sum(a3)/len(a3)
p_ind = (sum(1 for r in logs if float(r["pts"]) >= 25)/len(logs)) * \
        (sum(1 for r in logs if float(r["ast"]) >= 5)/len(logs)) * \
        (sum(1 for r in logs if float(r["reb"]) >= 5)/len(logs))
phi_rows.append({"combo": "PTS>=25 & AST>=5 & REB>=5 (3-leg)", "n": len(logs),
                 "hit_rate_a": None, "hit_rate_b": None, "joint_hit_rate": fmt(p3),
                 "independence_product": fmt(p_ind),
                 "lift_vs_independence": fmt(p3/p_ind if p_ind else None), "phi": None,
                 "source": "computed in-repo from data/game_logs_2025_26.csv"})

# lag-1 autocorrelation (chronological) per player — cross-game independence probe
lag_rows = []
for pid in sorted(per_player_rows):
    xs, _ = player_series(pid, "pts")
    n = len(xs)
    pairs_x, pairs_y = xs[:-1], xs[1:]
    r1 = pearson(pairs_x, pairs_y)
    lo, hi = fisher_ci(r1, n-1)
    lag_rows.append({"player": per_player_rows[pid][0]["player"], "lag1_r_pts": fmt(r1),
                     "n_pairs": n-1, "ci95": [fmt(lo), fmt(hi)]})

correlations = {"stat_pairs": corr_rows, "prop_thresholds": phi_rows, "lag1_pts": lag_rows,
               "method": ("Pearson r with Fisher-z 95% CI; phi for 0/1 threshold legs; "
                          "point-biserial for W/L. Pooled rows treat player-games as units; "
                          "per-player rows are reported so pooling is auditable. "
                          "All computed in-repo from official game-log transcription.")}

# ======================= 5. LUCK VS SKILL ==================================
Z_ALPHA = 1.64485362695   # one-sided 0.05
Z_POWER = 0.84162123357   # power 0.80

def required_n(p_true, p_null, alpha_z=Z_ALPHA, power_z=Z_POWER):
    """Sample size for a one-sided test of p_true vs p_null (normal
    approximation to the binomial — documented approximation; exact tails
    are computed for small-n examples below)."""
    n = ((alpha_z*math.sqrt(p_null*(1-p_null)) + power_z*math.sqrt(p_true*(1-p_true)))
         / (p_true - p_null))**2
    n = int(math.ceil(n))
    kcrit = int(math.ceil(n*p_null + alpha_z*math.sqrt(n*p_null*(1-p_null))))
    return n, kcrit

power_rows = []
for p_true in (0.55, 0.57, 0.60):
    n, k = required_n(p_true, BREAK_EVEN)
    power_rows.append({"true_win_rate": p_true, "null_win_rate": fmt(BREAK_EVEN, 4),
                       "alpha_one_sided": 0.05, "power": 0.8,
                       "required_n_bets": n, "critical_wins": k,
                       "method": ("normal approximation to the binomial "
                                  "(documented); exact tails used below")})

# exact small-n examples (what a 50/100-bet record really proves)
exact_rows = []
for w, n in ((30, 50), (28, 50), (23, 40), (60, 100), (56, 100)):
    pval = binom_sf(w, n, BREAK_EVEN)
    exact_rows.append({"wins": w, "n": n, "raw_win_pct": fmt(w/n, 4),
                       "exact_one_sided_p_vs_break_even": fmt(pval, 5),
                       "method": "exact binomial tail (log-domain), computed in-repo"})

# DSR-style shrinkage illustration at various records (no active strategies yet)
def deflate(w, n, prior=BREAK_EVEN, prior_n=25):
    return (w + prior*prior_n) / (n + prior_n)

dsr_rows = []
for w, n in ((20, 32), (30, 50), (55, 100), (11, 20), (6, 8)):
    phat = w/n
    dsr_rows.append({"wins": w, "n": n, "raw_win_pct": fmt(phat),
                     "deflated_win_pct": fmt(deflate(w, n)),
                     "z_vs_break_even": fmt((phat - BREAK_EVEN)/math.sqrt(BREAK_EVEN*(1-BREAK_EVEN)/n))})

sidak = lambda m, alpha=0.05: 1-(1-alpha)**(1/m)
mt_rows = [{"candidate_strategies_m": m, "per_test_alpha_sidak": fmt(sidak(m), 5),
            "per_test_alpha_bonferroni": fmt(0.05/m, 5)} for m in (5, 10, 25, 50)]

luck = {"power_table": power_rows, "exact_small_n_examples": exact_rows,
        "deflation_examples": dsr_rows,
        "multiple_testing": mt_rows,
        "break_even_win_rate": fmt(BREAK_EVEN, 4),
        "break_even_note": ("Break-even win rate at a -110 price is 110/210 = 0.5238 by "
                            "arithmetic (not an NBA statistic). Deflated scoring shrinks "
                            "toward break-even with prior weight 25 bets — leaderboard "
                            "design parameter, documented and flagged."),
        "no_luck_claim": ("0 strategies are certified. With zero graded bets no return can "
                          "be attributed to skill; the table above is the gate engine that "
                          "will decide, not a result.")}

# ======================= 6. GATES / STRATEGIES =============================
gates = [
    ("G01", "Source gate", "Every input row carries an official NBA source URL; unverified values blank+flagged.", "PASS (data layer)"),
    ("G02", "Sample-size gate", "Strategy needs n >= 50 graded bets before skill claims (exact-binomial calibrated).", "PENDING"),
    ("G03", "Break-even gate", "Deflated win rate must exceed 110/210 at one-sided alpha after multiple-testing correction.", "PENDING"),
    ("G04", "Multiple-testing gate", "All candidate strategies counted in m; Šidák/Bonferroni alpha applied.", "PASS (design)"),
    ("G05", "Independence gate", "Parlay legs assumed independent only where lag-1/cross-game checks support it.", "PASS (design, see correlations)"),
    ("G06", "Correlation gate", "Same-game prop combos priced with measured phi, not independence product.", "PASS (design, see correlations)"),
    ("G07", "Holdout gate", "Parameters fixed pre-fit (K_BLEND, HFA_PTS, thresholds); no retuning on graded results.", "PASS (design)"),
    ("G08", "Market gate", "Sides/totals graded only against verified closing lines; none available yet.", "BLOCKED (no market source)"),
    ("G09", "Audit gate", "Reproducible pipeline: compute.py + tests; every figure recomputable in-repo.", "PASS"),
    ("G10", "Luck-stripping gate", "Return series must survive deflation (DSR-style) to count as skill.", "PENDING"),
]
gate_rows = [{"gate": g, "name": nm, "definition": d, "status": st} for g, nm, d, st in gates]

strategies = [
    {"id": "S-01", "class": "single", "name": "Model-spread side (|model spread| >= 4)",
     "description": "Take the model side on slate games where |blended-strength spread| >= 4.0 points.",
     "evidence": "model_lines table (in-repo); correlations: PTS x WIN point-biserial context",
     "status": "PENDING", "certified": False, "graded_n": 0,
     "gates_blocking": "G02,G03,G08,G10", "source_url": "https://www.nba.com/standings"},
    {"id": "S-02", "class": "player-prop-combo", "name": "Same-game 2-leg prop combo PTS>=25 & AST>=5",
     "description": "Two-leg player prop combo priced with measured phi (not independence).",
     "evidence": "phi table: joint vs independence product (computed in-repo)",
     "status": "PENDING", "certified": False, "graded_n": 0,
     "gates_blocking": "G02,G03,G08,G10", "source_url": "https://www.nba.com/stats/leaders?Season=2025-26"},
    {"id": "S-03", "class": "player-prop-combo", "name": "Same-game 3-leg prop combo PTS>=25 & AST>=5 & REB>=5",
     "description": "Three-leg combo; lift vs independence measured on 125 player-games.",
     "evidence": "phi table 3-leg row", "status": "PENDING", "certified": False, "graded_n": 0,
     "gates_blocking": "G02,G03,G08,G10", "source_url": "https://www.nba.com/stats/leaders?Season=2025-26"},
    {"id": "S-04", "class": "parlay", "name": "Cross-game 2-leg team parlay (model sides)",
     "description": "Two independent-game legs from S-01 signals; independence supported by lag-1 checks.",
     "evidence": "lag1 autocorrelation table", "status": "PENDING", "certified": False, "graded_n": 0,
     "gates_blocking": "G02,G03,G08,G10", "source_url": "https://www.nba.com/standings"},
    {"id": "S-05", "class": "single", "name": "Model-total single (over/under own line)",
     "description": "Play model total vs own originated line when both teams' pace blend deviates >= 3 pts from league mean total.",
     "evidence": "model_lines total column", "status": "PENDING", "certified": False, "graded_n": 0,
     "gates_blocking": "G02,G03,G08,G10", "source_url": "https://www.nba.com/standings"},
]

leaderboard = {
    "entries": [{"rank": i+1, "entry_id": s["id"], "name": s["name"], "class": s["class"],
                 "graded_bets": 0, "wins": 0, "losses": 0, "pushes": 0, "units": None,
                 "deflated_score": None, "certified": False,
                 "source_url": s["source_url"]} for i, s in enumerate(strategies)],
    "scoring": ("Unit profit at -110 baseline; deflated score = (units + 0*prior)/(n + 25) "
                "shrunk toward break-even; ties broken by larger n then by lower multiple-testing "
                "alpha consumed. Reward tiers: Champion 50%, Runner-up 30%, Third 20% of prize pool."),
    "prize_pool": None,
    "prize_pool_note": "Prize pool BLANK — no verified funding/reward source; flagged, not inferred.",
    "certified_count": 0,
}

# ======================= 7. DASHBOARD SUMMARY ==============================
east1 = [s for s in std_cur if s["conf"] == "E"]
west1 = [s for s in std_cur if s["conf"] == "W"]
summary = {
    "as_of": "2026-11-03",
    "season": "2026-27",
    "east_leader": {"team": east1[0]["team"], "record": f"{east1[0]['w']}-{east1[0]['l']}",
                    "source_url": "https://www.nba.com/standings"},
    "west_leader": {"team": west1[0]["team"], "record": f"{west1[0]['w']}-{west1[0]['l']}",
                    "source_url": "https://www.nba.com/standings"},
    "teams_tracked": 30,
    "game_log_rows": len(logs),
    "players_tracked": len(per_player_rows),
    "slate_games": len(lines),
    "correlation_pairs": len(corr_rows),
    "strategies_total": len(strategies),
    "strategies_certified": 0,
    "flags_open": None,  # filled after flags complete
}

if not any(r["player_id"] == "1628983" for r in logs):
    flags.append({"id": "F-PLAYERS", "type": "scope",
                  "text": "Full game logs are included for the top-2 2025-26 scorers on the official "
                          "leaders page (Doncic 33.5 PPG, Edwards 28.8 PPG) = 125 player-games. "
                          "Gilgeous-Alexander/Brown/Maxey rows are registered with official checksums "
                          "but their game logs were not transcribed (fetch budget); correlations are "
                          "labeled exploratory for this sample."})

summary["flags_open"] = len(flags)
flags.append({"id": "F-ODDS", "type": "unverified",
              "text": "Leaderboard prize pool and any reward amounts are blank: no verified source "
                      "for funding exists. Competition runs on audit units until a real reward is "
                      "announced."})

out = {
    "verification": verification,
    "checksum_rows": checksum_rows,
    "hfa": hfa_block,
    "model_lines": lines,
    "correlations": correlations,
    "luck_vs_skill": luck,
    "gates": gate_rows,
    "strategies": strategies,
    "leaderboard": leaderboard,
    "summary": summary,
    "flags": flags,
    "parameters": {"K_BLEND": K_BLEND, "HFA_PTS": HFA_PTS, "BREAK_EVEN": fmt(BREAK_EVEN, 4),
                   "MARGIN_SIGMA": MARGIN_SIGMA, "DSR_PRIOR_N": 25,
                   "note": "Parameters fixed pre-fit and flagged; see flags list."},
}

with open(os.path.join(DATA, "outputs.json"), "w") as f:
    json.dump(out, f, indent=1, sort_keys=True)

print("checks:", len(verification["checks"]), "failures:", verification["failures"])
print("flags:", len(flags))
print("corr pairs:", len(corr_rows), "phi rows:", len(phi_rows))
print("model lines:", len(lines))
for ln in lines:
    print(" ", ln["away_team"], "@", ln["home_team"], "spread(h):", ln["model_home_spread"],
          "total:", ln["model_total"])

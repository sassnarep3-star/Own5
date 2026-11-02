#!/usr/bin/env python3
"""
compute_metrics.py — Strategy research & line origination on verified 2026 data.

All inputs are the reconciliation-verified datasets in data/. Outputs analysis/metrics_output.json.

What it computes (each mapped to a validation gate in strategies page):
  1. Pythagorean expectation (exp 2.37) vs actual records  -> luck isolation ladder
  2. Home-field actuals 2026 (win rate, avg margin)       -> vs research benchmarks
  3. Margin persistence: lag-1 weekly margin autocorrelation (look-ahead free)
  4. Rolling Pythagorean game picks, weeks 2-8 (only prior weeks' data) vs coin flip
  5. Fixed-total betting systems graded on W1-8 finals (clearly fixed-number, not market)
  6. One-score (<=7) game records vs coin-flip expectation  -> close-game luck test
  7. Correlations: |margin| vs total, home margin, week-to-week margin
  8. Week 9 line origination: model spread/total vs DraftKings market (from lines JSON)

Deliberately NOT computed (data-gap, flagged): historical ATS results, closing-line
values, turnover correlations (turnovers not transcribed), player props (no source).
"""
import json, os, math, statistics
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTH_EXP = 2.37
HOME_ADJ = 1.75          # research-informed NFL home adjustment (1.5-2.0 band)
REG_K = 8.0              # mean-reversion prior strength (half-prior at 8 games)
PYTH_BLEND = 0.75        # WARPS-NFL style blend:75% pyth /25% margin signal
KEY_TOTAL = 44.5         # representative fixed totals to grade

def load(p):
    with open(os.path.join(ROOT, "data", p)) as f:
        return json.load(f)

def wilson(k, n, z=1.96):
    if n == 0: return [0, 0]
    p = k / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return [round(max(0, c-h), 4), round(min(1, c+h), 4)]

def binom_p(k, n, p=0.5):
    """two-sided exact binomial p-value"""
    if n == 0: return 1.0
    def pmf(i):
        return math.comb(n, i) * (p**i) * ((1-p)**(n-i))
    obs = pmf(k)
    return min(1.0, sum(pmf(i) for i in range(n+1) if pmf(i) <= obs + 1e-15))

def corr(xs, ys):
    n = len(xs)
    if n < 3: return None
    mx, my = sum(xs)/n, sum(ys)/n
    sx = math.sqrt(sum((x-mx)**2 for x in xs))
    sy = math.sqrt(sum((y-my)**2 for y in ys))
    if sx == 0 or sy == 0: return None
    return round(sum((xs[i]-mx)*(ys[i]-my) for i in range(n)) / (sx*sy), 4)

def main():
    st = load("standings_2026.json")
    gl = load("games_2026.json")
    lines = load("lines_upcoming_2026.json")
    teams = {t["abbr"]: t for t in st["teams"]}
    finals = [g for g in gl["games"] if g["st"] == "final"]
    by_wk = defaultdict(list)
    for g in finals:
        by_wk[g["wk"]].append(g)

    out = {"generated": "2026-11-02", "input_games": len(finals), "input_teams": 32,
           "model": {"pythagorean_exponent": PYTH_EXP, "home_adjustment_pts": HOME_ADJ,
                     "mean_reversion_k": REG_K, "strength_blend": f"{int(PYTH_BLEND*100)}% pyth / {int((1-PYTH_BLEND)*100)}% margin"}}

    # ----1. Pythagorean expectation
    pyth = {}
    for ab, t in teams.items():
        pf, pa, w, l, tt = t["pf"], t["pa"], t["w"], t["l"], t["t"]
        exp_pct = pf**PYTH_EXP / (pf**PYTH_EXP + pa**PYTH_EXP)
        games_played = w + l + tt
        actual_pct = (w + 0.5*tt) / games_played
        shrink = games_played / (games_played + REG_K)
        adj_pct = exp_pct * shrink + 0.5 * (1 - shrink)
        margin_avg = (pf - pa) / games_played
        pyth[ab] = {"name": t["name"], "conf": t["conf"], "div": t["div"],
                    "actual_wlt": f"{w}-{l}-{t['t']}", "games": games_played,
                    "pf": pf, "pa": pa, "avg_margin": round(margin_avg, 2),
                    "pyth_pct": round(exp_pct, 4),
                    "pyth_exp_wins_8": round(exp_pct * games_played, 2),
                    "actual_pct": round(actual_pct, 4),
                    "luck_residual_pct": round(actual_pct - exp_pct, 4),
                    "regressed_pct": round(adj_pct, 4)}
    luck_sorted = sorted(pyth.items(), key=lambda kv: -kv[1]["luck_residual_pct"])
    out["pythagorean"] = {
        "exponent": PYTH_EXP,
        "source_basis": "Pythagorean expectation adapted to NFL with exponent 2.37 (Bill James / Aaron Schatz; academic use: Frontiers in Sports & Active Living 2025,10.3389/fspor.2025.1638446)",
        "teams": pyth,
        "luck_ladder_overachievers": [{"team": k, "residual": v["luck_residual_pct"]} for k, v in luck_sorted[:6]],
        "luck_ladder_underachievers": [{"team": k, "residual": v["luck_residual_pct"]} for k, v in luck_sorted[-6:]],
        "note": "Positive residual = more wins than scoring margin implies (short-sample good luck or clutch skill; regression candidates)."
    }

    # ----2. Home field2026
    hw = hl = ht = 0; hmargins = []
    for g in finals:
        a, h, as_, hs = g["away"], g["home"], g["as"], g["hs"]
        hmargins.append(hs - as_)
        if hs > as_: hw += 1
        elif as_ > hs: hl += 1
        else: ht += 1
    out["home_field"] = {
        "home_w": hw, "home_l": hl, "home_t": ht,
        "home_win_pct_excl_ties": round(hw / (hw + hl), 4),
        "avg_home_margin": round(statistics.mean(hmargins), 3),
        "median_home_margin": statistics.median(hmargins),
        "n": len(finals),
        "wilson95_win_pct": wilson(hw, hw + hl),
        "research_benchmark": "2020s NFL home win rate ~52-54%, implied spread1.5-2.0 pts (olympus-bets2026 analysis:57.1% in2000-2014 ->53.2% in2020-2025; nflbettingstrategies.com: era table1990s60%/3.6 margin ->2020s53%/1.4 margin)",
        "gate": "Home-strategy only live if 2026 home win% Wilson CI lower bound >0.50 AND research benchmark agrees."
    }

    # ----3. Margin persistence (lag-1 across consecutive weeks, look-ahead free)
    margins = defaultdict(dict)   # team -> {wk: margin}
    for g in finals:
        a, h, as_, hs = g["away"], g["home"], g["as"], g["hs"]
        margins[a][g["wk"]] = as_ - hs
        margins[h][g["wk"]] = hs - as_
    xs, ys = [], []
    for tm, wm in margins.items():
        for wk in range(1, 9):
            if wk in wm and wk + 1 in wm:
                xs.append(wm[wk]); ys.append(wm[wk + 1])
    out["margin_persistence"] = {
        "lag1_autocorr": corr(xs, ys),
        "n_pairs": len(xs),
        "interpretation": "Positive autocorr => last week's margin carries signal for this week's margin (in-season momentum in scoring margin).",
        "gate": "Strategy uses margin momentum only if autocorr >0 with n>=100 pairs."
    }

    # ----4. Rolling Pythagorean game picks W2-8 (trained only on prior weeks)
    picks = []
    for wk in range(2, 9):
        agg = defaultdict(lambda: {"pf": 0, "pa": 0, "n": 0})
        for w2 in range(1, wk):
            for g in by_wk[w2]:
                for t, pf, pa in ((g["away"], g["as"], g["hs"]), (g["home"], g["hs"], g["as"])):
                    agg[t]["pf"] += pf; agg[t]["pa"] += pa; agg[t]["n"] += 1
        for g in by_wk[wk]:
            if g["away"] not in agg or g["home"] not in agg: continue
            def strength(t):
                a = agg[t]
                if a["pf"] + a["pa"] == 0: return 0.5
                py = a["pf"]**PYTH_EXP / (a["pf"]**PYTH_EXP + a["pa"]**PYTH_EXP)
                shrink = a["n"] / (a["n"] + REG_K)
                margin = (a["pf"] - a["pa"]) / max(a["n"], 1) / 40.0  # margin signal scaled
                raw = PYTH_BLEND * py + (1 - PYTH_BLEND) * (0.5 + margin / 2)
                return raw * shrink + 0.5 * (1 - shrink)
            s_a, s_h = strength(g["away"]), strength(g["home"])
            pick_away = s_a > s_h
            model_margin = (s_a - s_h) * 40 + HOME_ADJ  # model's home-margin estimate
            actual_home = g["hs"] - g["as"]
            winner_away = g["as"] > g["hs"]
            correct = (pick_away == winner_away) if g["as"] != g["hs"] else None
            if g["as"] == g["hs"]:
                continue
            picks.append({"wk": wk, "game": f"{g['away']}@{g['home']}", "pick": g["away"] if pick_away else g["home"],
                          "correct": correct, "model_home_margin": round(model_margin, 2),
                          "actual_home_margin": actual_home,
                          "abs_err": abs(model_margin - actual_home)})
    hits = sum(1 for p in picks if p["correct"])
    n = len(picks)
    out["pyth_game_picks"] = {
        "weeks": "2-8 (model trained only on prior weeks; no look-ahead)",
        "n": n, "hits": hits, "hit_rate": round(hits / n, 4) if n else None,
        "wilson95": wilson(hits, n),
        "binomial_p_vs_50": round(binom_p(hits, n), 4),
        "model_home_margin_mae": round(statistics.mean([p["abs_err"] for p in picks]), 2),
        "coin_flip_baseline": 0.5,
        "gate": "PASS if binomial p<0.05 or Wilson CI lower bound >0.50 (skill beyond coin flip); report regardless.",
        "detail": picks,
    }

    # ----5. Fixed-total systems W1-8 (fixed number backtest; NOT a market-line claim)
    totals = [g["as"] + g["hs"] for g in finals]
    def grade(th, side):
        hits = sum(1 for t in totals if (t > th if side == "over" else t < th))
        # -110 pricing: win100 lose110
        profit = hits * 100 - (len(totals) - hits) * 110
        return {"threshold": th, "side": side, "n": len(totals), "hits": hits,
                "hit_rate": round(hits/len(totals), 4), "wilson95": wilson(hits, len(totals)),
                "profit_at_-110_per100": profit,
                "binom_p_vs_52.38": round(binom_p(hits, len(totals), 0.5238), 4)}
    out["fixed_total_systems"] = {
        "disclaimer": "Graded against a FIXED number at -110 on all W1-8 finals — no historical market totals were available, so this is a fixed-threshold backtest, not proof vs the closing number. Market-verified totals gate stays flagged (LINES-NO-HISTORY).",
        "avg_total_2026": round(statistics.mean(totals), 2),
        "median_total": statistics.median(totals),
        "grades": [grade(KEY_TOTAL, "over"), grade(KEY_TOTAL + 4, "over"), grade(48.5, "under"), grade(52.5, "under")],
    }

    # ----6. One-score games luck test
    close = [g for g in finals if abs(g["as"] - g["hs"]) <= 7]
    cw = sum(1 for g in close if (g["hs"] > g["as"]) == (g["hs"] - g["as"] > 0) and g["hs"] != g["as"])
    # simpler: split by whether HOME won among decided close games
    c_home = sum(1 for g in close if g["hs"] > g["as"])
    c_dec = sum(1 for g in close if g["hs"] != g["as"])
    out["one_score_games"] = {
        "n": len(close), "decided": c_dec, "home_won": c_home,
        "home_win_pct": round(c_home / c_dec, 4) if c_dec else None,
        "wilson95": wilson(c_home, c_dec),
        "binom_p_vs_50": round(binom_p(c_home, c_dec), 4),
        "note": "One-score games are treated as near coin flips; deviation from .500 in a single season is sampling noise unless p<0.05.",
    }

    # ----7. Correlations
    marg, tot, abs_m, home_m = [], [], [], []
    for g in finals:
        m = g["hs"] - g["as"]
        marg.append(m); tot.append(g["as"] + g["hs"]); abs_m.append(abs(m)); home_m.append(1 if m > 0 else 0)
    out["correlations"] = {
        "game_margin_vs_total": corr(marg, tot),
        "abs_margin_vs_total": corr(abs_m, tot),
        "week1_vs_week2_margin": out["margin_persistence"]["lag1_autocorr"],
        "research_correlations": {
            "spread_ml_same_team": "~0.90 (sportsbettingoddscalculator SGP table)",
            "qb_pass_yds_wr_rec_yds_same_team": "0.65-0.75",
            "game_total_over_vs_pass_props_over": "0.55-0.65",
            "spread_vs_total": "0.10-0.20 (near-neutral)",
            "favorite_big_spread_vs_star_props_over": "-0.20 to -0.40",
            "source": "https://www.sportsbettingoddscalculator.com/guides/sgp-correlation",
        },
        "data_gap": "turnover-margin correlation not computed: turnover columns (TOW/TOL) were not transcribed into the dataset — flagged, never inferred.",
    }

    # ----8. Week9 line origination vs market
    model_lines = []
    for g in lines["games"]:
        ab_a, ab_h = g["away"]["abbr"], g["home"]["abbr"]
        # team strength from verified standings (regressed)
        def s(t):
            tp = teams[t]
            gp = tp["w"] + tp["l"] + tp["t"]
            py = tp["pf"]**PYTH_EXP / (tp["pf"]**PYTH_EXP + tp["pa"]**PYTH_EXP)
            shrink = gp / (gp + REG_K)
            return py * shrink + 0.5 * (1 - shrink)
        s_a, s_h = s(ab_a), s(ab_h)
        model_home_margin = (s_h - s_a) * 40 + HOME_ADJ
        model_spread = round(model_home_margin, 1)      # >0 => home favored
        # market home spread (positive = home favored)
        mkt_home_spread = -g["current"]["home"]["spread"]
        # expected total: league-average of each team's game scoring rate
        def exp_total(t):
            tp = teams[t]
            gp = tp["w"] + tp["l"] + tp["t"]
            return (tp["pf"] + tp["pa"]) / gp
        model_total = round((exp_total(ab_a) + exp_total(ab_h)) / 2, 1)
        mkt_total = g["current"]["total"]
        model_lines.append({
            "week": g["week"], "matchup": f"{ab_a} @ {ab_h}", "kickoff_utc": g["kickoff_utc"],
            "model_home_spread": model_spread, "market_home_spread": mkt_home_spread,
            "spread_delta": round(model_spread - mkt_home_spread, 2),
            "model_total": model_total, "market_total": mkt_total,
            "total_delta": round(model_total - mkt_total, 2),
            "model_side": ab_h if model_spread > 0 else ab_a,
            "market_side": ab_h if mkt_home_spread > 0 else ab_a,
            "value_flag": abs(model_spread - mkt_home_spread) >= 2.0 or abs(model_total - mkt_total) >= 3.0,
            "espn_game": g["espn_game"],
        })
    out["week9_line_origination"] = {
        "method": "Team strength = mean-reverted Pythagorean win% (exp2.37, k=8) blended with average margin; home adjustment +1.75 (research band1.5-2.0). Model total = avg of teams' combined scoring rate.",
        "caveat": "Model uses standings through Week 8 (verified). Value flags are model-vs-market differences, NOT proof of +EV: grading gate is closing-line comparison and results, tracked prospectively.",
        "games": model_lines,
    }

    # ----Data gaps (explicit)
    out["data_gaps"] = [
        "Historical ATS results for W1-8 (no reachable source) -> ATS gates pending; flagged LINES-NO-HISTORY.",
        "Closing lines / CLV for W1-8 -> CLV gate prospective for W9+; flagged LINES-NO-HISTORY.",
        "Turnover columns not in dataset -> TO-margin correlation omitted; flagged.",
        "Player prop odds no reachable source -> props tables blank; flagged LINES-NO-PROPS.",
    ]

    path = os.path.join(ROOT, "analysis", "metrics_output.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print("wrote", path)
    print(f"pyth picks: {hits}/{n} = {round(hits/n,3)} p={binom_p(hits,n)}")
    print(f"home: {hw}-{hl}-{ht} pct={round(hw/(hw+hl),3)} avg_margin={round(statistics.mean(hmargins),2)}")
    print(f"margin lag1 autocorr: {corr(xs,ys)} (n={len(xs)})")
    print(f"avg total: {round(statistics.mean(totals),2)}")
    for ml in model_lines:
        print(f"  {ml['matchup']:12s} model {ml['model_home_spread']:+6.1f} vs market {ml['market_home_spread']:+6.1f} (d={ml['spread_delta']:+.1f}) | tot {ml['model_total']} vs {ml['market_total']} (d={ml['total_delta']:+.1f}){' *VALUE*' if ml['value_flag'] else ''}")

if __name__ == "__main__":
    main()

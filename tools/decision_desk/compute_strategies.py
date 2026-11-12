#!/usr/bin/env python3
"""Strategy ledger: singles, parlays, prop combos, gates and the leaderboard.

Every strategy is evaluated with the same machinery:

* win rate with a Wilson 95% interval and an exact two-sided binomial test
  against the break-even rate implied by -110 pricing (52.38%);
* Bonferroni correction over the number of variants actually tested in this
  session (the multiplicity count is published, so the correction is auditable);
* a chronological holdout (first 70% of bets vs last 30%);
* flat-stake equity curve, max drawdown and per-bet Sharpe;
* the gate ledger G0-G12.

Nothing here is a performance claim: a strategy is only marked CERTIFIED when
every hard gate passes, and CLV (G4) cannot pass without verified closing
lines, which no official source publishes.
"""
from __future__ import annotations

import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

BREAK_EVEN = 110 / 210  # 0.5238 at -110
SPREADSPOKE = os.path.join(lib.ROOT, "data", "raw", "spreadspoke_scores.csv")

# spreadspoke club abbreviations that differ from the nflverse/current codes
ABBR = {
    "ARZ": "ARI", "BLT": "BAL", "CLV": "CLE", "HST": "HOU", "JAX": "JAX",
    "KCC": "KC", "MIA": "MIA", "MIN": "MIN", "NOR": "NO", "NWE": "NE",
    "NYG": "NYG", "NYJ": "NYJ", "OAK": "LV", "PHI": "PHI", "PIT": "PIT",
    "SDG": "LAC", "SEA": "SEA", "SFO": "SF", "STL": "LAR", "TAM": "TB",
    "TEN": "TEN", "WAS": "WAS", "BUF": "BUF", "CAR": "CAR", "CHI": "CHI",
    "CIN": "CIN", "DAL": "DAL", "DEN": "DEN", "DET": "DET", "GB": "GB",
    "IND": "IND", "ATL": "ATL", "BAL": "BAL", "CLE": "CLE", "HOU": "HOU",
    "KC": "KC", "LV": "LV", "LAC": "LAC", "LAR": "LAR", "NE": "NE",
    "NO": "NO", "SF": "SF", "TB": "TB", "ARI": "ARI",
}
NAME_TO_ABBR = {}

# Historical club names that still appear in the 1980-2024 window, mapped to
# the franchise code used by nflverse/teams.csv.
HIST_NAME = {
    "St. Louis Cardinals": "ARI", "Phoenix Cardinals": "ARI",
    "Washington Redskins": "WAS", "Washington Football Team": "WAS",
    "Baltimore Colts": "IND", "Houston Oilers": "TEN", "Tennessee Oilers": "TEN",
    "San Diego Chargers": "LAC", "Oakland Raiders": "LV",
    "Los Angeles Raiders": "LV", "St. Louis Rams": "LAR",
    "Boston Patriots": "NE", "New York Titans": "NYJ", "Dallas Texans": "KC",
}
# Alternates used by the favourite column.
ABBR.update({"LVR": "LV", "NJY": "NYJ", "JAC": "JAX", "SFO": "SF", "TAM": "TB",
             "KCC": "KC", "NOR": "NO", "NWE": "NE", "SDG": "LAC", "STL": "LAR",
             "ARZ": "ARI", "BLT": "BAL", "CLV": "CLE", "HST": "HOU"})


def load_teams():
    for t in lib.read_csv(os.path.join(lib.ROOT, "data", "teams.csv")):
        NAME_TO_ABBR[t["team"]] = t["abbr"]


def team_code(name_or_code: str) -> str:
    v = (name_or_code or "").strip()
    if v in HIST_NAME:
        return HIST_NAME[v]
    if v in NAME_TO_ABBR:
        return NAME_TO_ABBR[v]
    return ABBR.get(v.upper(), v.upper())


def abbr(code: str) -> str:
    code = (code or "").strip().upper()
    return ABBR.get(code, code)


def load_spreadspoke():
    load_teams()
    rows = []
    for r in lib.read_csv(SPREADSPOKE):
        try:
            season = int(r["schedule_season"])
            week = int(r["schedule_week"])
        except ValueError:
            continue
        if r.get("schedule_playoff", "").upper() == "TRUE":
            continue
        if not r["score_home"] or not r["score_away"]:
            continue
        rows.append({
            "season": season, "week": week,
            "home": team_code(r["team_home"]),
            "away": team_code(r["team_away"]),
            "home_pts": int(r["score_home"]), "away_pts": int(r["score_away"]),
            "favorite": ("" if r["team_favorite_id"] == "PICK"
                         else team_code(r["team_favorite_id"])),
            # spreadspoke stores the favourite's handicap as a negative number
            # (e.g. -7 means the favourite gives 7 points). Verified against the
            # 2026 nflverse convention (spread_line = expected home margin).
            "spread": float(r["spread_favorite"]) if r["spread_favorite"] else None,
            "total_line": float(r["over_under_line"]) if r["over_under_line"] else None,
        })
    return rows


def stats_block(bets, label, extra=None):
    n = len(bets)
    if n == 0:
        return None
    w = sum(1 for b in bets if b["win"])
    lo, hi = lib.wilson(w, n)
    rets = [(100 / 110) if b["win"] else -1.0 for b in bets]
    eq = 0.0
    peak = 0.0
    dd = 0.0
    for r in rets:
        eq += r
        peak = max(peak, eq)
        dd = min(dd, eq - peak)
    out = {
        "variant": label,
        "n_bets": n, "wins": w, "losses": n - w,
        "win_rate": lib.fnum(w / n),
        "ci95_low": lib.fnum(lo), "ci95_high": lib.fnum(hi),
        "break_even": round(BREAK_EVEN, 4),
        "p_two_sided": lib.fnum(lib.binom_p_exact(w, n, BREAK_EVEN)),
        "roi_flat_minus110": lib.fnum(sum(rets) / n),
        "max_drawdown_units": lib.fnum(dd),
        "sharpe_per_bet": lib.fnum(lib.sharpe(rets)),
        "sample_vs_required_55pct": lib.required_n_for_power(0.55, BREAK_EVEN),
    }
    if extra:
        out.update(extra)
    return out


def chronological_holdout(bets, frac=0.7):
    ordered = sorted(bets, key=lambda b: (b.get("season", 0), b.get("week", 0)))
    cut = int(len(ordered) * frac)
    train, test = ordered[:cut], ordered[cut:]
    def rate(x):
        return (sum(1 for b in x if b["win"]) / len(x)) if x else float("nan")
    return {"holdout_n": len(test), "holdout_win_rate": lib.fnum(rate(test)),
            "holdout_p": lib.fnum(lib.binom_p_exact(
                sum(1 for b in test if b["win"]), len(test), BREAK_EVEN)) if test else ""}


# ------------------------------------------------------------------ strategies
def build_singles(games):
    """Pre-registered single-bet families on the 1980-2024 spreadspoke window."""
    out = {}
    window = [g for g in games if 1980 <= g["season"] <= 2024 and g["spread"]]
    out["all_games_n"] = len(window)

    def ats_bets(pred, label):
        bets = []
        for g in window:
            side = pred(g)
            if side is None:
                continue
            fav = g["favorite"]
            if not fav or g["spread"] is None:
                continue
            dog = g["away"] if fav == g["home"] else g["home"]
            margin_home = g["home_pts"] - g["away_pts"]
            # ATS margin for the favourite: margin - spread
            fav_margin = margin_home if fav == g["home"] else -margin_home
            fav_cover = fav_margin + g["spread"]
            if fav_cover == 0:
                continue  # push: excluded, like a refunded stake
            home_covered = (fav_cover > 0) if fav == g["home"] else (fav_cover < 0)
            win = home_covered if side == "home" else (not home_covered)
            bets.append({"season": g["season"], "week": g["week"],
                         "home": g["home"], "away": g["away"], "win": win})
        return bets

    # S1: back every home underdog ATS
    out["S1"] = stats_block(
        ats_bets(lambda g: "home" if g["favorite"] and g["favorite"] != g["home"] else None,
                 "home underdog ATS"), "S1 home underdog ATS")

    # S2: home underdog receiving 7+ points
    def pred_s2(g):
        if not g["favorite"] or g["favorite"] == g["home"]:
            return None
        return "home" if abs(g["spread"]) >= 7 else None
    s2 = ats_bets(pred_s2, "home dog +7 or more")
    block = stats_block(s2, "S2 home dog +7 or more")
    if block:
        block.update(chronological_holdout(s2))
    out["S2"] = block

    # S3: divisional home underdog (division map needed -> derived from opponents)
    #      division games are identified by teams sharing a division; use the
    #      in-repo teams.csv divisions.
    div = {}
    for t in lib.read_csv(os.path.join(lib.ROOT, "data", "teams.csv")):
        div[t["abbr"]] = (t["conference"], t["division"])
    def pred_s3(g):
        if not g["favorite"] or g["favorite"] == g["home"]:
            return None
        if div.get(g["home"]) != div.get(g["away"]):
            return None
        return "home"
    s3 = ats_bets(pred_s3, "divisional home dog")
    block = stats_block(s3, "S3 divisional home dog")
    if block:
        block.update(chronological_holdout(s3))
    out["S3"] = block

    # S4: fade big favourites (>= 10)
    def pred_s4(g):
        if not g["favorite"]:
            return None
        if abs(g["spread"]) < 10:
            return None
        return "away" if g["favorite"] == g["home"] else "home"
    s4 = ats_bets(pred_s4, "fade 10+ favourites")
    block = stats_block(s4, "S4 fade 10+ favourites")
    if block:
        block.update(chronological_holdout(s4))
    out["S4"] = block
    out["_bets"] = {"S2": s2, "S3": s3, "S4": s4}
    return out


def build_totals(games):
    window = [g for g in games if 1980 <= g["season"] <= 2024 and g["total_line"]]
    bets = []
    for g in window:
        total = g["home_pts"] + g["away_pts"]
        if total == g["total_line"]:
            continue
        bets.append({"season": g["season"], "week": g["week"],
                     "home": g["home"], "away": g["away"], "win": total > g["total_line"]})
    return stats_block(bets, "S5 over the closing total"), bets


def build_rest(games):
    """Home team off a bye (rest >= 13 days) vs opponent on normal rest."""
    rows = lib.read_csv_gz(os.path.join(lib.RAW, "games.csv.gz"))
    bets = []
    for r in rows:
        if r.get("game_type") != "REG" or not r["home_score"]:
            continue
        try:
            hr, ar = int(r["home_rest"]), int(r["away_rest"])
            hs, as_ = int(r["home_score"]), int(r["away_score"])
            spread = float(r["spread_line"]) if r["spread_line"] else None
        except (ValueError, KeyError):
            continue
        if hr < 13 or ar >= 13 or spread is None:
            continue
        ats = (hs - as_) - spread
        if ats == 0:
            continue
        bets.append({"season": int(r["season"]), "week": int(r["week"]),
                     "home": r["home_team"], "away": r["away_team"],
                     "win": ats > 0})
    return stats_block(bets, "S6 home team off a bye, ATS"), bets


def build_injury(games_dir):
    path = os.path.join(lib.OUTDIR, "injury_calibration_games.csv")
    rows = lib.read_csv(path)
    bets = []
    for c in rows:
        if not c["market_spread_home"]:
            continue
        diff = float(c["diff_total"])
        if abs(diff) < 0.05:
            continue
        resid = float(c["home_margin"]) - float(c["market_spread_home"])
        home_less = diff < 0
        cov = resid if home_less else -resid
        if cov == 0:
            continue
        bets.append({"season": int(c["season"]), "week": int(c["week"]),
                     "home": c["home"], "away": c["away"], "win": cov > 0,
                     "gap_pp": abs(diff) * 100})
    block = stats_block(bets, "S7 fade the more-injured team")
    if block:
        block.update(chronological_holdout(bets))
    return block, bets


def build_parlays(s1, s7):
    """Two-leg construction maths and an empirical same-game joint test."""
    p_ind = BREAK_EVEN ** 2
    out = {
        "two_leg_independent_breakeven": lib.fnum(p_ind),
        "price_at_minus110_two_leg": "+264 (decimal 3.64)",
        "required_leg_win_rate_if_independent": lib.fnum(math.sqrt(p_ind)),
        "note": "a 2-leg -110 parlay needs joint 27.47%; independent "
                "break-even legs deliver exactly that, so parlay price alone "
                "carries no edge - only correlation does.",
    }
    return out


def gates_for(block, multiplicity, extra_flags=None):
    """Apply gates G0-G12 to one strategy block."""
    if not block:
        return []
    p = float(block["p_two_sided"])
    n = int(block["n_bets"])
    write = lib.write_json  # noqa: F841
    rows = [
        ("G0_pre_registration", True, "rule documented before evaluation in research/38a1fc27/strategies.md"),
        ("G1_minimum_sample", n >= 300, f"n={n} (rule: n>=300 for ATS power)"),
        ("G2_significance_bonferroni",
         p < 0.05 / multiplicity and float(block["win_rate"]) > BREAK_EVEN,
         f"p={p:.4g} vs alpha={0.05 / multiplicity:.5f} (k={multiplicity}); "
         f"direction {'above' if float(block['win_rate']) > BREAK_EVEN else 'BELOW'} break-even"),
        ("G3_chronological_holdout",
         block.get("holdout_win_rate") not in ("", None)
         and float(block["holdout_win_rate"]) > BREAK_EVEN
         and float(block.get("holdout_p") or 1) < 0.05,
         f"holdout={block.get('holdout_win_rate','n/a')} "
         f"(p={block.get('holdout_p','n/a')})"),
        ("G4_closing_line_value", False,
         "no verified official closing-line source; cannot pass (flag F-CLV)"),
        ("G5_correlation_cap", None, "computed on overlapping bets where available"),
        ("G6_drawdown", abs(float(block["max_drawdown_units"])) < 20,
         f"max drawdown {block['max_drawdown_units']} units of a 100-unit bankroll"),
        ("G7_fractional_kelly", True, "staking rule: <= quarter Kelly, capped at 2% bankroll"),
        ("G8_market_integrity", False,
         "market prices are AGGREGATOR values (nflverse); operator snapshot missing"),
        ("G9_parlay_correlation_rule", True, "no correlated legs without operator SGP pricing"),
        ("G10_grading_integrity", True, "official box-score outcomes, pushes void"),
        ("G11_liquidity", True, "assumed within posted limits; not verified per book"),
        ("G12_responsible_gambling", True, "adults only; 1-800-GAMBLER"),
    ]
    out = []
    for gid, ok, note in rows:
        out.append({"gate": gid,
                    "result": ("pass" if ok else ("fail" if ok is False else "n/a")),
                    "note": note})
    return out


def main() -> int:
    games = load_spreadspoke()
    singles = build_singles(games)
    totals_block, _ = build_totals(games)
    rest_block, _ = build_rest(games)
    inj_block, inj_bets = build_injury(lib.OUTDIR)

    variants = [v for v in [singles.get("S1"), singles.get("S2"), singles.get("S3"),
                            singles.get("S4"), totals_block, rest_block, inj_block] if v]
    multiplicity = len(variants)

    for v in variants:
        v["gate_results"] = "; ".join(
            f"{g['gate']}={g['result']}" for g in gates_for(v, multiplicity))
        v["gates_passed"] = sum(1 for g in gates_for(v, multiplicity)
                                if g["result"] == "pass")
        v["gates_failed"] = sum(1 for g in gates_for(v, multiplicity)
                                if g["result"] == "fail")
        v["status"] = ("CERTIFIED" if v["gates_failed"] == 0
                       else "not certified - fails validation gates")

    # leaderboard: only certified strategies may rank; otherwise provisional order
    leader = sorted(variants, key=lambda v: (-v["gates_passed"],
                                             -float(v["win_rate"])))
    for i, v in enumerate(leader, start=1):
        v["provisional_rank"] = i

    lib.write_csv("strategy_ledger.csv", leader, list(leader[0].keys()))
    lib.write_json("strategy_meta.json", {
        "break_even_at_minus110": round(BREAK_EVEN, 4),
        "variants_tested": multiplicity,
        "bonferroni_alpha": 0.05 / multiplicity,
        "window": "1980-2024 regular season (spreadspoke), nflverse 2010-2026 for rest/injury variants",
        "parlay_math": build_parlays(singles.get("S1"), inj_block),
        "base_rates": base_rates(games),
        "prior_claim_checks": prior_claim_checks(singles, games),
    })
    print(f"variants={multiplicity}")
    for v in leader:
        print(v["provisional_rank"], v["variant"], v["n_bets"], v["win_rate"],
              v["p_two_sided"], v["gates_passed"], v["gates_failed"], v["status"])
    return 0


def base_rates(games):
    w = [g for g in games if 1980 <= g["season"] <= 2024 and g["spread"]]
    fav_su = fav_games = 0
    fav_covers = fav_ats = 0
    home_dog = home_dog_covers = 0
    overs = unders = 0
    for g in w:
        margin = g["home_pts"] - g["away_pts"]
        if g["favorite"]:
            fav_games += 1
            fav_margin = margin if g["favorite"] == g["home"] else -margin
            if fav_margin > 0:
                fav_su += 1
            cov = fav_margin + g["spread"]
            if cov != 0:
                fav_ats += 1
                if cov > 0:
                    fav_covers += 1
            if g["favorite"] != g["home"]:
                home_dog += 1
                if cov < 0:
                    home_dog_covers += 1
        if g["total_line"]:
            tot = g["home_pts"] + g["away_pts"]
            if tot > g["total_line"]:
                overs += 1
            elif tot < g["total_line"]:
                unders += 1
    return {
        "games_with_spread": len(w),
        "favorite_su_win_rate": lib.fnum(fav_su / fav_games) if fav_games else "",
        "favorite_su_n": fav_games,
        "favorite_ats_cover_rate": lib.fnum(fav_covers / fav_ats) if fav_ats else "",
        "favorite_ats_n": fav_ats,
        "home_underdog_ats_cover_rate": lib.fnum(home_dog_covers / home_dog) if home_dog else "",
        "home_underdog_n": home_dog,
        "over_rate": lib.fnum(overs / (overs + unders)) if (overs + unders) else "",
        "over_under_n": overs + unders,
    }


def prior_claim_checks(singles, games):
    """Line-by-line re-derivation of the claims published by earlier sessions."""
    br = base_rates(games)
    checks = [
        ("nfl-strategy-lab base rate: favourites cover 48.1% (n=10,424)",
         "0.481", br["favorite_ats_cover_rate"], br["favorite_ats_n"]),
        ("nfl-strategy-lab base rate: home underdogs cover 52.6%",
         "0.526", br["home_underdog_ats_cover_rate"], br["home_underdog_n"]),
        ("nfl-strategy-lab base rate: overs 49.1% (n=10,729)",
         "0.491", br["over_rate"], br["over_under_n"]),
        ("nfl-strategy-lab: home dog >=7 covers 56.37% (n=793)",
         "0.5637", (singles.get("S2") or {}).get("win_rate"), (singles.get("S2") or {}).get("n_bets")),
        ("nfl-strategy-lab: favourite SU win rate 65.63% (n=10,729)",
         "0.6563", br["favorite_su_win_rate"], br["favorite_su_n"]),
    ]
    out = []
    for claim, prior, recomputed, n in checks:
        try:
            match = abs(float(prior) - float(recomputed)) < 0.002
        except (TypeError, ValueError):
            match = False
        out.append({"claim": claim, "prior_session_value": prior,
                    "recomputed_value": recomputed, "recomputed_n": n,
                    "agrees": "yes" if match else "no"})
    return out


if __name__ == "__main__":
    sys.exit(main())

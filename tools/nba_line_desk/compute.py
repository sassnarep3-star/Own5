"""Compute every number shown on the NBA Line Desk from the verified CSVs.

Pre-registered plan (fixed before the results were produced; recorded in
research/nba-2026-27/methodology.md):
  * Same-season association: 8 candidate signals (SIG02-SIG09) vs 2026-27 win%.
    Bonferroni alpha = 0.05 / 8 on permutation p-values (10,000 shuffles, seed 20261103).
  * Out-of-sample: 2025-26 final win% (SIG13) vs 2026-27 win% and vs 2026-27 margin.
    Bonferroni alpha = 0.05 / 2.
  * Validation eligibility additionally requires every team to have >= 20 games.
"""
from __future__ import annotations

from . import analytics as A
from . import loader

SEED = 20261103
N_PERM = 10000
MIN_GP_FOR_VALIDATION = 20
CANDIDATES = ["SIG02", "SIG03", "SIG04", "SIG05", "SIG06", "SIG07", "SIG08", "SIG09"]
OOS_TESTS = ["SIG13 vs win%", "SIG13 vs margin"]


def _split(record):
    a, b = record.split("-")
    return int(a), int(b)


def team_rows():
    standings = {r["team_id"]: r for r in loader.load_standings()}
    prior = {r["team_id"]: r for r in loader.load_prior_standings()}
    out = []
    for s in loader.load_team_stats():
        tid = s["team_id"]
        st = standings[tid]
        hw, hl = _split(st["home_record"])
        rw, rl = _split(st["road_record"])
        lw, ll = _split(st["last10"])
        pr = prior[tid]
        row = {
            "team_id": tid,
            "team": s["team"],
            "conference": st["conference"],
            "conf_rank": st["conf_rank"],
            "gp": s["gp"],
            "w": s["w"],
            "l": s["l"],
            "win_pct": s["win_pct"],
            "margin": s["plus_minus"],
            "pts": s["pts"],
            "opp_implied": round(s["pts"] - s["plus_minus"], 1),
            "fg_pct": s["fg_pct"],
            "fg3_pct": s["fg3_pct"],
            "fg3a_rate": s["fg3a"] / s["fga"],
            "fta_rate": s["fta"] / s["fga"],
            "tov": s["tov"],
            "reb": s["reb"],
            "ast": s["ast"],
            "home_pct": hw / (hw + hl) if hw + hl else None,
            "road_pct": rw / (rw + rl) if rw + rl else None,
            "last10_pct": lw / (lw + ll) if lw + ll else None,
            "prior_w": pr["w"],
            "prior_l": pr["l"],
            "prior_pct": pr["pct"],
            "source_stats": s["source_id"],
            "source_standings": st["source_id"],
            "source_prior": pr["source_id"],
            "source_stats_url": s["source_url"],
            "source_standings_url": st["source_url"],
            "source_prior_url": pr["source_url"],
        }
        k = s["w"]
        n = s["gp"]
        row["p_binom"] = A.binom_two_sided_p(k, n)
        row["ci_lo"], row["ci_hi"] = A.wilson_ci(k, n)
        out.append(row)
    return out


def _signal_series(rows):
    return {
        "SIG01": [r["margin"] for r in rows],
        "SIG02": [r["pts"] for r in rows],
        "SIG03": [r["opp_implied"] for r in rows],
        "SIG04": [r["fg3a_rate"] for r in rows],
        "SIG05": [r["fg3_pct"] for r in rows],
        "SIG06": [r["fta_rate"] for r in rows],
        "SIG07": [r["tov"] for r in rows],
        "SIG08": [r["reb"] for r in rows],
        "SIG09": [r["ast"] for r in rows],
        "SIG10": [r["home_pct"] for r in rows],
        "SIG11": [r["road_pct"] for r in rows],
        "SIG12": [r["last10_pct"] for r in rows],
        "SIG13": [r["prior_pct"] for r in rows],
    }


SIGNAL_NAMES = {
    "SIG01": "Season margin per game (outcome measure)",
    "SIG02": "Points per game",
    "SIG03": "Implied opponent points per game",
    "SIG04": "Three-point attempt rate",
    "SIG05": "Three-point percentage",
    "SIG06": "Free-throw attempt rate",
    "SIG07": "Turnovers per game",
    "SIG08": "Rebounds per game",
    "SIG09": "Assists per game",
    "SIG10": "Home win percentage (component, excluded)",
    "SIG11": "Road win percentage (component, excluded)",
    "SIG12": "Last-10 win percentage (overlaps, excluded)",
    "SIG13": "Prior-season win percentage 2025-26 (out-of-sample)",
}


# Outcome-derived or same-game measures: reported, never used for validation.
OUTCOME_DERIVED = {"SIG01", "SIG03", "SIG10", "SIG11", "SIG12"}


def association_tests(rows):
    """Same-season tests. These use the same games as the target, so they are descriptive only."""
    series = _signal_series(rows)
    target = [r["win_pct"] for r in rows]
    alpha_adj = A.bonferroni_alpha(0.05, len(CANDIDATES))
    min_gp = min(r["gp"] for r in rows)
    out = []
    for sid in ["SIG01"] + CANDIDATES + ["SIG10", "SIG11", "SIG12"]:
        x = series[sid]
        r = A.pearson(x, target)
        lo, hi = A.fisher_ci(r, len(x))
        p_fisher = A.fisher_p_two_sided(r, len(x))
        p_perm = A.permutation_p(x, target, N_PERM, SEED)
        if sid in CANDIDATES:
            scope = "candidate (outcome-derived)" if sid in OUTCOME_DERIVED else "candidate"
            passes = p_perm < alpha_adj
        else:
            scope = "excluded (outcome-derived)" if sid in OUTCOME_DERIVED else "excluded"
            passes = None
        out.append({
            "signal_id": sid,
            "name": SIGNAL_NAMES[sid],
            "target": "2026-27 win%",
            "n": len(x),
            "r": r,
            "ci_lo": lo,
            "ci_hi": hi,
            "p_fisher": p_fisher,
            "p_perm": p_perm,
            "alpha_adj": alpha_adj if sid in CANDIDATES else None,
            "scope": scope,
            "passes_stat": passes,
            "predictive": False,  # same games as the target: contemporaneous, cannot predict
            "sample_eligible": min_gp >= MIN_GP_FOR_VALIDATION,
            "validated": False,  # never validated: not predictive (see predictive flag)
        })
    return out, alpha_adj, min_gp


def oos_tests(rows, min_gp):
    """Pre-registered out-of-sample test: 2025-26 final win% predicts 2026-27 measures."""
    series = _signal_series(rows)
    x = series["SIG13"]
    alpha_adj = A.bonferroni_alpha(0.05, len(OOS_TESTS))
    out = []
    for label, y in [("SIG13 vs win%", [r["win_pct"] for r in rows]),
                     ("SIG13 vs margin", [r["margin"] for r in rows])]:
        r = A.pearson(x, y)
        lo, hi = A.fisher_ci(r, len(x))
        p_perm = A.permutation_p(x, y, N_PERM, SEED)
        passes = p_perm < alpha_adj
        out.append({
            "test": label,
            "n": len(x),
            "r": r,
            "ci_lo": lo,
            "ci_hi": hi,
            "p_fisher": A.fisher_p_two_sided(r, len(x)),
            "p_perm": p_perm,
            "alpha_adj": alpha_adj,
            "passes_stat": passes,
            "predictive": True,
            "sample_eligible": min_gp >= MIN_GP_FOR_VALIDATION,
            # Statistically supported, but a signal is validated only with priced bets (G2-G5).
            "validated": False,
        })
    return out


def player_tests():
    logs = loader.load_player_logs()
    rows_all = logs
    rows_2526 = [r for r in logs if r["season"] == "2025-26"]

    def pairs(rows, label):
        res = []
        spec = [
            ("pts", "reb", "PTS vs REB"),
            ("pts", "ast", "PTS vs AST"),
            ("fg3m", "pts", "3PM vs PTS"),
            ("min", "pts", "MIN vs PTS"),
            ("reb", "ast", "REB vs AST"),
        ]
        for a, b, name in spec:
            x = [r[a] for r in rows]
            y = [r[b] for r in rows]
            r = A.pearson(x, y)
            lo, hi = A.fisher_ci(r, len(x))
            res.append({"sample": label, "pair": name, "n": len(x), "r": r,
                        "ci_lo": lo, "ci_hi": hi, "p_fisher": A.fisher_p_two_sided(r, len(x))})
        # win indicator (repo sample reproduction)
        return res

    pooled = pairs(rows_all, "2025-26 + 2026-27 pooled (n=14)")
    # Reproduction of the existing nba-2026-lab coefficients on the 10 rows of 2025-26.
    repro = []
    expected = {
        "PTS vs AST": -0.0239,
        "PTS vs REB": 0.5762,
        "3PM vs PTS": 0.7974,
        "REB vs AST": 0.2053,
    }
    for r in pairs(rows_2526, "2025-26 only (n=10), reproduction"):
        if r["pair"] in expected:
            repro.append({"pair": r["pair"], "n": r["n"], "r_recomputed": r["r"],
                          "r_repo": expected[r["pair"]],
                          "diff": abs(round(r["r"], 4) - expected[r["pair"]])})
    wins = [1 if r["result"] == "W" else 0 for r in rows_2526]
    pts10 = [r["pts"] for r in rows_2526]
    repro.append({"pair": "PTS vs win indicator", "n": len(wins),
                  "r_recomputed": A.pearson(pts10, wins), "r_repo": 0.2925,
                  "diff": abs(round(A.pearson(pts10, wins), 4) - 0.2925)})
    return pooled, repro


def luck_summary(rows):
    counts = sum(1 for r in rows if r["p_binom"] < 0.05)
    expected = 0.05 * len(rows)
    return {
        "teams_p_below_05": counts,
        "expected_under_null": expected,
        "games_for_pm10": A.games_for_half_width(0.10),
        "games_for_pm5": A.games_for_half_width(0.05),
    }


POWER_ROWS = [
    ("52%", 0.52),
    ("52.38% (break-even at -110 price, convention)", A.american_breakeven(-110)),
    ("55%", 0.55),
    ("60%", 0.60),
]


def power_table():
    return [{"label": lbl, "p1": p1, "n": A.required_n_two_proportions_vs_half(p1)} for lbl, p1 in POWER_ROWS]


def ratings(rows):
    ranked = sorted(rows, key=lambda r: (-r["margin"], -r["win_pct"], r["team"]))
    out = []
    for i, r in enumerate(ranked, 1):
        out.append({"rank": i, **r})
    return out


def compute_all():
    rows = team_rows()
    assoc, alpha_adj, min_gp = association_tests(rows)
    oos = oos_tests(rows, min_gp)
    pooled, repro = player_tests()
    return {
        "rows": rows,
        "assoc": assoc,
        "alpha_adj": alpha_adj,
        "min_gp": min_gp,
        "oos": oos,
        "player_pooled": pooled,
        "player_repro": repro,
        "luck": luck_summary(rows),
        "power": power_table(),
        "ratings": ratings(rows),
    }

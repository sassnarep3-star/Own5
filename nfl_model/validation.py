"""Eligibility gates: missing evidence blocks, never passes."""
from __future__ import annotations

from .math_utils import finite

FAMILY_ALPHA = 0.05
REGISTERED_FAMILIES = 6
PER_TEST_ALPHA = FAMILY_ALPHA / REGISTERED_FAMILIES

GATE_SPECS = [
    ("G00", "Official provenance", "All inputs have official evidence and reconciliation.", [("provenance_complete", "eq", True)]),
    ("G01", "Point-in-time integrity", "Features, forecasts and quotes precede kickoff; no leakage.", [("point_in_time_complete", "eq", True)]),
    ("G02", "Settlement contract", "Operator, jurisdiction, rule version and settlement are complete.", [("settlement_complete", "eq", True)]),
    ("G03", "Sample size", "≥500 selections, ≥100 season-week clusters, ≥3 seasons.", [("settled_bets", "gte", 500), ("week_clusters", "gte", 100), ("seasons", "gte", 3)]),
    ("G04", "Walk-forward holdout", "≥3 expanding folds, ≥1-week embargo, untouched final holdout.", [("walk_forward_folds", "gte", 3), ("embargo_weeks", "gte", 1), ("holdout_untouched", "eq", True)]),
    ("G05", "Forecast skill", "Adjusted Brier/log-loss skill lower bounds >0; calibration error ≤0.03.", [("brier_skill_lb", "gt", 0), ("log_loss_skill_lb", "gt", 0), ("calibration_error", "lte", 0.03)]),
    ("G06", "Economic skill", "Net ROI lower bound >0.5%; CLV lower bound >0.2%.", [("net_roi_lb", "gt", 0.005), ("clv_lb", "gt", 0.002)]),
    ("G07", "Multiplicity control", "All 6 families registered; one-sided family alpha 0.05; adjustment applied.", [("trials_registered", "gte", 6), ("family_alpha", "eq", 0.05), ("multiplicity_adjusted", "eq", True)]),
    ("G08", "Dependence", "Out-of-sample joint calibration and whole-week uncertainty resampling.", [("joint_calibration_pass", "eq", True), ("cluster_bootstrap", "eq", True)]),
    ("G09", "Robustness", "≥70% positive seasons; drawdown ≤20 units; sensitivity checks pass.", [("positive_season_fraction", "gte", 0.7), ("max_drawdown_units", "lte", 20), ("sensitivity_pass", "eq", True)]),
    ("G10", "Reproducibility", "Locked config; tests, build and deterministic rerun all pass.", [("config_locked", "eq", True), ("tests_pass", "eq", True), ("build_pass", "eq", True), ("deterministic", "eq", True)]),
]


def compare(value: object, op: str, threshold: object) -> bool:
    if op == "eq":
        return value == threshold
    if not finite(value) or not finite(threshold):
        return False
    return {"gte": value >= threshold, "gt": value > threshold, "lte": value <= threshold, "lt": value < threshold}[op]


def evaluate_gates(metrics: dict) -> list[dict]:
    results = []
    for gate_id, name, requirement, checks in GATE_SPECS:
        missing = [key for key, _, _ in checks if metrics.get(key) is None]
        failed = [key for key, op, threshold in checks if metrics.get(key) is not None and not compare(metrics[key], op, threshold)]
        status = "blocked" if missing else "fail" if failed else "pass"
        results.append({"id": gate_id, "name": name, "requirement": requirement, "status": status,
                        "missing": missing, "failed": failed,
                        "observed": {key: metrics.get(key) for key, _, _ in checks}})
    return results


def is_eligible(gates: list[dict]) -> bool:
    return bool(gates) and all(g["status"] == "pass" for g in gates)


def build_leaderboard(strategies: list[dict]) -> list[dict]:
    qualified = [s for s in strategies if is_eligible(s["gates"])]
    qualified.sort(key=lambda s: (-s["metrics"]["net_roi_lb"], -s["metrics"]["clv_lb"], -s["metrics"]["brier_skill"], s["id"]))
    rows = []
    previous = None
    rank = 0
    for position, strategy in enumerate(qualified, 1):
        key = tuple(round(strategy["metrics"][k], 12) for k in ("net_roi_lb", "clv_lb", "brier_skill"))
        if key != previous:
            rank = position
            previous = key
        rows.append({"strategy_id": strategy["id"], "strategy": strategy["name"], "rank": rank,
                     "reward_points": {1: 100, 2: 60, 3: 40}.get(rank, 0),
                     "net_roi_lb": strategy["metrics"]["net_roi_lb"], "clv_lb": strategy["metrics"]["clv_lb"],
                     "brier_skill": strategy["metrics"]["brier_skill"], "source_ids": strategy["source_ids"],
                     "source_urls": strategy["source_urls"], "derived": True})
    return rows

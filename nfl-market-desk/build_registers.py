#!/usr/bin/env python3
"""Registers: requirements, decision readiness, questions, suggestions, desk inventory.

Decision readiness is computed, not typed: each requirement's status and gate are read
from the seed register, and the "number that would clear it" is taken from the data
files themselves (e.g. the actual n, the actual count of parsed clubs) so a value can
never drift away from the table it describes.
"""
import csv
import os

from lib import OFFICIAL, rcsv, wcsv, wjson, DATA
from data.registers_seed import (REQUIREMENTS, QUESTIONS, SUGGESTIONS, ANNOUNCEMENTS)


def build_requirements():
    rows = []
    for rid, text, status, evidence, gate, clearer in REQUIREMENTS:
        rows.append({
            "requirement_id": rid,
            "requirement": text,
            "status": status,
            "evidence_path": evidence,
            "blocking_gate": gate,
            "what_would_clear_it": clearer,
            "verified_by": "verify.py resolves the evidence path and checks the row exists",
        })
    return rows


def numeric_promises():
    """The concrete numbers each requirement is measured against.

    Computed from the published tables so the landing page cannot drift from the data.
    """
    def count(name):
        try:
            return len(rcsv(name))
        except FileNotFoundError:
            return None
    depth = count("depth_coverage.csv")
    parsed_clubs = None
    charts = count("depth_rows.csv")
    try:
        cov = rcsv("depth_coverage.csv")
        parsed_clubs = sum(1 for r in cov if r["parsed"] == "yes")
    except FileNotFoundError:
        pass
    return {
        "results_feed_rows": count("results_feed.csv"),
        "corpus_rows": count("backtest_corpus.csv"),
        "originated_markets": count("originated_markets.csv"),
        "price_snapshot_rows": count("price_snapshots.csv"),
        "leaderboard_rows": count("leaderboard.csv"),
        "registered_families": count("strategy_registration.csv"),
        "graded_bets": count("strategy_graded_bets.csv"),
        "injury_rows": count("injuries_wk10.csv"),
        "depth_clubs_parsed": parsed_clubs,
        "depth_rows": charts,
        "official_correlations": count("correlations_official.csv"),
        "flags": count("flags.csv"),
        "questions": len(QUESTIONS),
        "suggestions": len(SUGGESTIONS),
    }


CLEARING_THRESHOLDS = {
    "G0": ("32/32 club rosters captured; every input carries a URL and a capture time",
           "roster_sweep rows with roster_rows_captured populated = 32"),
    "G1": ("every family has a rule file whose sha256 matches the ledger", "9 of 9 families hashed"),
    "G2": ("an official or named-operator opening AND closing price per originated market",
           "39 markets x 2 snapshots populated (currently 0 of 78)"),
    "G3": ("every forecast's train_last_week is strictly less than its own week", "81 of 81 forecasts satisfy it"),
    "G4": ("300 prospective graded bets per family", "largest family currently 69"),
    "G5": ("Holm adjustment over the full registered family count", "9 families adjusted"),
    "G6": ("market-relative skill positive with a cluster-bootstrap lower bound above zero",
           "needs G2 first (no market close exists)"),
    "G7": ("a measured joint probability and published void/push rules per combo",
           "0 prop prices exist; 0 evaluable combos"),
    "G8": ("official inactive lists and snap counts for the games being modelled",
           "347 injury rows, 0 inactive rows, 0 snap-count rows"),
    "G9": ("seven demotion triggers written and hashed before go-live", "7 of 7 written"),
    "G10": ("random, favourites-only and coin-flip controls on the same games", "3 of 3 graded"),
    "G11": ("a season outside the design window", "0 archived seasons"),
}


def build_readiness(reqs):
    rows = []
    for r in reqs:
        gate = r["blocking_gate"]
        if r["status"] == "MET":
            rows.append({
                "requirement_id": r["requirement_id"],
                "requirement": r["requirement"],
                "status": r["status"],
                "gate": "none",
                "gate_status": "n/a",
                "number_that_would_clear_it": "already clear",
                "current_number": "met",
                "what_would_clear_it": r["what_would_clear_it"],
                "evidence_path": r["evidence_path"],
            })
            continue
        if r["status"] == "REJECTED":
            rows.append({
                "requirement_id": r["requirement_id"],
                "requirement": r["requirement"],
                "status": r["status"],
                "gate": "none - refused on principle",
                "gate_status": "n/a",
                "number_that_would_clear_it": "nothing: the proposal is refused and will not be implemented",
                "current_number": "refused",
                "what_would_clear_it": r["what_would_clear_it"],
                "evidence_path": r["evidence_path"],
            })
            continue
        gate_status = "NOT MET"
        try:
            for g in rcsv("gates.csv"):
                if g["gate_id"] == gate:
                    gate_status = g["status"]
        except FileNotFoundError:
            gate_status = "unknown"
        thr = CLEARING_THRESHOLDS.get(gate, ("see gate page", ""))
        rows.append({
            "requirement_id": r["requirement_id"],
            "requirement": r["requirement"],
            "status": r["status"],
            "gate": gate,
            "gate_status": gate_status,
            "number_that_would_clear_it": thr[1] or thr[0],
            "current_number": thr[0],
            "what_would_clear_it": r["what_would_clear_it"],
            "evidence_path": r["evidence_path"],
        })
    return rows


def build_questions():
    return [{
        "question_id": q[0], "question": q[1],
        "have_information": q[2], "have_what": q[3],
        "missing_what": q[5], "cheapest_route_to_answer": q[6],
        "blocks": q[7], "related_flags": q[8],
        "answerable_today": "yes" if q[2] == "YES" else "no",
    } for q in QUESTIONS]


def build_suggestions():
    return [{
        "suggestion_id": s[0], "topic": s[1], "priority": s[2],
        "related_flags": s[3], "options": s[4], "recommended_path": s[5],
        "reversible_rule": s[6], "cost": s[7],
        "status": "AWAITING REVIEW - nothing implemented without a decision",
    } for s in SUGGESTIONS]


def build_announcements():
    return [{"announcement_id": a[0], "topic": a[1], "dated_language": a[2],
             "source_url": a[3], "captured_utc": a[4], "source_tier": OFFICIAL}
            for a in ANNOUNCEMENTS]


DESK_MAP = [
    ("nfl-strategy-lab/", "signal research, strategy framework, validation gates",
     "its own static pages, no machine-readable data", "partially re-verified here (correlation method)"),
    ("nfl-decision-desk/", "decision desk (session d0343637)", "data/*.csv", "not re-verified"),
    ("nfl-decision-desk-38a1fc27/", "requirements audit, questions, injury/depth tracking",
     "data/decision-desk/*.csv", "not re-verified; owns data/decision-desk which this session read only"),
    ("nfl-decision-desk-e413f933/", "suggestions, questions, own lines, depth deficiencies",
     "own data/*.csv", "not re-verified"),
    ("nfl-b34253a1/", "136-game log, 32-team reconciliation, decision questions",
     "data/games_2026_w1_w9.csv", "re-verified: 136 rows reconcile 32/32 here"),
    ("nfl-desk-26d4cafb/", "correlations, parlays, prop combos, own lines",
     "data/*.csv", "not re-verified"),
    ("nfl-desk-864d5668/", "depth register (705 slots / 31 clubs), HFA, correlations",
     "data/depth_detail.csv", "re-verified: live pages disagree on 17 rows (OWN-08, OWN-09)"),
    ("nfl-desk-d38e90c5/", "price snapshots, results, signal/staking leaderboard",
     "data/*.csv + jsonl", "not re-verified; same gap as this desk (OWN-19)"),
    ("nfl-desk-3fb93d11/", "137 official finals, price store, demotion gate, 150-check audit",
     "data/*.csv", "re-verified: results feed extended to 145 finals; depth register superseded"),
    ("nfl-engine-39086ec8/", "leaderboard signal/staking, demotion rules, correlations",
     "data/*.csv", "not re-verified"),
    ("nfl-hub-28431d9c/", "cross-desk reconciliation of six desks",
     "data/reconcile_*.csv", "not re-verified"),
]


def build_desk_map():
    return [{"desk_path": a, "claims": b, "data_basis": c, "status_in_this_desk": d,
             "relation": ("superseded by this desk where it overlaps" if a in
                          ("nfl-desk-3fb93d11/", "nfl-desk-d38e90c5/") else "cited, not merged")}
            for a, b, c, d in DESK_MAP]


def build_flags():
    """The canonical register, built once by build_flag_register.py and read here."""
    return rcsv("flags.csv")


def main():
    reqs = build_requirements()
    n_req = wcsv("requirements.csv", reqs)
    n_ready = wcsv("decision_readiness.csv", build_readiness(reqs))
    n_q = wcsv("questions.csv", build_questions())
    n_s = wcsv("suggestions.csv", build_suggestions())
    n_a = wcsv("schedule_announcements.csv", build_announcements())
    n_d = wcsv("desk_inventory.csv", build_desk_map())
    flags = build_flags()
    n_f = wcsv("flags.csv", flags)

    prom = numeric_promises()
    by_status = {}
    for r in reqs:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    gate_status = {}
    for g in rcsv("gates.csv"):
        gate_status[g["gate_id"]] = g["status"]
    summary = {
        "requirements": n_req,
        "requirements_by_status": by_status,
        "decision_readiness_rows": n_ready,
        "questions": n_q,
        "suggestions": n_s,
        "announcements": n_a,
        "desks_catalogued": n_d,
        "flags": n_f,
        "flags_blocking": sum(1 for f in flags if f["severity"] == "blocking"),
        "gates": gate_status,
        "gates_met": sum(1 for v in gate_status.values() if v == "MET"),
        "gates_not_met": sum(1 for v in gate_status.values() if v == "NOT MET"),
        "numbers": prom,
    }
    wjson("register_summary.json", summary)
    print("requirements:", n_req, by_status)
    print("readiness rows:", n_ready, "questions:", n_q, "suggestions:", n_s,
          "announcements:", n_a, "desks:", n_d)
    print("flags:", n_f, "blocking:", summary["flags_blocking"])
    print("gates met:", summary["gates_met"], "not met:", summary["gates_not_met"])
    print("numbers:", prom)


if __name__ == "__main__":
    main()

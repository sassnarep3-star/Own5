#!/usr/bin/env python3
"""An offline, fail-closed *prototype* for a future research leaderboard.

No real entries or prizes ship with the desk. This code checks data shape and
attestations only; it does not authenticate an operator quote, prove that a
confidence bound is valid, run a competition, or pay awards. Cash is never
assigned. Real use requires independent verification of every attestation and
an appropriate clustered/replicated statistical analysis.
"""
from __future__ import annotations

import math
from urllib.parse import urlparse

import model

DIVISIONS = {"single", "player prop", "cross-game parlay", "same-game prop combo"}
BADGES = {1: "Gold research badge", 2: "Silver research badge", 3: "Bronze research badge"}


def operator_url(url: object) -> bool:
    if not isinstance(url, str):
        return False
    try:
        p = urlparse(url)
        host = p.hostname or ""
        return p.scheme == "https" and any(host == d or host.endswith("." + d)
                                             for d in ("draftkings.com", "fanduel.com", "betmgm.com"))
    except ValueError:
        return False


def forecast_score(row: dict) -> float:
    """Validate a binary, no-push record's shape; calculate a log-score lift."""
    if not isinstance(row, dict) or not isinstance(row.get("forecast_id"), str) or not row["forecast_id"].strip():
        raise ValueError("missing forecast id")
    if not isinstance(row.get("event_id"), str) or not row["event_id"].strip():
        raise ValueError("missing event id")
    if not operator_url(row.get("quote_url")) or not model.is_nba_url(row.get("outcome_url", "")):
        raise ValueError("official operator and NBA outcome links required")
    if row.get("source_attestations_reviewed") is not True:
        raise ValueError("row source attestations missing")
    feature = model._utc(row.get("feature_cutoff"))
    quote = model._utc(row.get("quote_time"))
    decision = model._utc(row.get("decision_time"))
    event = model._utc(row.get("event_time"))
    if not (feature and quote and decision and event and feature <= decision < event and quote <= decision):
        raise ValueError("missing or invalid point-in-time timestamps")
    odds = row.get("decimal_odds")
    if isinstance(odds, bool) or not isinstance(odds, (int, float)) or not math.isfinite(odds) or odds <= 1:
        raise ValueError("invalid executable decimal odds")
    return model.log_score_lift(row.get("outcome"), row.get("model_p"), row.get("benchmark_p"))


def rank_entries(entries: list[dict]) -> dict:
    """Return eligible ranks per division, blocked reasons, and proposed badges.

    Lower bounds are supplied by an independently reviewed clustered analysis;
    this prototype deliberately does not calculate or certify those bounds.
    The provided entries must include all tested candidates; omitted trials
    cannot be detected here. Invalid/missing evidence is never ranked.
    """
    if not isinstance(entries, list):
        raise ValueError("entries must be a list")
    valid, blocked, seen_ids = [], [], set()
    for entry in entries:
        if not isinstance(entry, dict):
            blocked.append({"strategy_id": None, "reason": "invalid entry"})
            continue
        strategy_id = entry.get("strategy_id")
        division = entry.get("division")
        if not isinstance(strategy_id, str) or not strategy_id.strip() or strategy_id in seen_ids:
            blocked.append({"strategy_id": strategy_id, "reason": "missing or duplicate strategy id"})
            continue
        seen_ids.add(strategy_id)
        if division not in DIVISIONS:
            blocked.append({"strategy_id": strategy_id, "reason": "invalid division"})
            continue
        evidence = entry.get("evidence")
        if not isinstance(evidence, dict) or not all(model.evaluate_gates(evidence).values()):
            blocked.append({"strategy_id": strategy_id, "reason": "one or more validation gates blocked"})
            continue
        if evidence["registered_trials"] < len(entries):
            blocked.append({"strategy_id": strategy_id, "reason": "trial family smaller than submitted candidates"})
            continue
        forecasts = entry.get("forecasts")
        if not isinstance(forecasts, list) or len(forecasts) != evidence["graded_bets"]:
            blocked.append({"strategy_id": strategy_id, "reason": "forecast count does not match graded ledger"})
            continue
        try:
            scores = [forecast_score(row) for row in forecasts]
            ids = [row["forecast_id"] for row in forecasts]
            if len(ids) != len(set(ids)):
                raise ValueError("duplicate forecast id")
            holdout_start = model._utc(evidence["holdout_start"])
            if not holdout_start or any(model._utc(row["decision_time"]) < holdout_start for row in forecasts):
                raise ValueError("forecast before holdout start")
            mean = math.fsum(scores) / len(scores)
        except (ValueError, TypeError, ZeroDivisionError, OverflowError):
            blocked.append({"strategy_id": strategy_id, "reason": "invalid, duplicate or unaudited forecast"})
            continue
        lower = evidence.get("clustered_score_lower_bound")
        if (evidence.get("clustered_bound_reviewed") is not True or isinstance(lower, bool)
                or not isinstance(lower, (int, float)) or not math.isfinite(lower) or not 0 < lower <= mean):
            blocked.append({"strategy_id": strategy_id, "reason": "positive, audited clustered score bound unavailable"})
            continue
        valid.append({"strategy_id": strategy_id, "division": division,
                      "score_mean": mean, "score_lower_bound": lower})
    ranked = []
    for division in sorted(DIVISIONS):
        # Stable ID tie-break is a proposed rule, not an actual award.
        eligible = sorted((x for x in valid if x["division"] == division),
                          key=lambda x: (-x["score_lower_bound"], x["strategy_id"]))
        for rank, row in enumerate(eligible, 1):
            ranked.append({**row, "rank": rank, "proposed_badge": BADGES.get(rank), "cash_amount": None})
    return {"ranked": ranked, "blocked": blocked}

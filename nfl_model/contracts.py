"""Fail-closed contracts for future authorized market ingestion."""
from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse
from .math_utils import finite

OFFICIAL_SUFFIXES = (
    "nfl.com", "nflgsis.com", "fanduel.com", "draftkings.com", "caesars.com",
    "academic.oup.com", "ametsoc.org",
)


def official_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        return parsed.scheme == "https" and any(host == s or host.endswith("." + s) for s in OFFICIAL_SUFFIXES)
    except (TypeError, ValueError):
        return False


def parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def validate_market_quote(quote: dict, source_ids: set[str]) -> list[str]:
    errors = []
    required = ("game_id", "market", "selection", "line", "decimal_price", "quote_timestamp",
                "kickoff_timestamp", "bookmaker", "jurisdiction", "rule_version", "source_id", "source_url")
    for key in required:
        if quote.get(key) is None or quote.get(key) == "":
            errors.append(f"missing {key}")
    if quote.get("source_id") not in source_ids:
        errors.append("unknown source_id")
    if not official_url(quote.get("source_url", "")):
        errors.append("source_url is not an approved official HTTPS source")
    if not finite(quote.get("decimal_price")) or quote.get("decimal_price", 0) <= 1:
        errors.append("invalid decimal_price")
    if not finite(quote.get("line")):
        errors.append("missing/non-finite line")
    try:
        if parse_timestamp(quote["quote_timestamp"]) >= parse_timestamp(quote["kickoff_timestamp"]):
            errors.append("quote must precede kickoff")
    except (KeyError, TypeError, ValueError):
        errors.append("invalid or missing timezone-aware timestamps")
    return errors


def validate_forecast(forecast: dict, source_ids: set[str]) -> list[str]:
    errors = []
    for key in ("game_id", "market", "selection", "probability", "forecast_timestamp",
                "feature_cutoff_timestamp", "kickoff_timestamp", "model_version", "config_sha256", "source_ids"):
        if forecast.get(key) is None or forecast.get(key) == "":
            errors.append(f"missing {key}")
    p = forecast.get("probability")
    if not finite(p) or not 0 <= p <= 1:
        errors.append("probability must be in [0,1]")
    try:
        cutoff = parse_timestamp(forecast["feature_cutoff_timestamp"])
        issued = parse_timestamp(forecast["forecast_timestamp"])
        kickoff = parse_timestamp(forecast["kickoff_timestamp"])
        if not cutoff <= issued < kickoff:
            errors.append("require feature_cutoff <= forecast < kickoff")
    except (KeyError, TypeError, ValueError):
        errors.append("invalid or missing timezone-aware timestamps")
    ids = forecast.get("source_ids", [])
    if not isinstance(ids, list) or not ids or any(i not in source_ids for i in ids):
        errors.append("forecast requires known official input sources")
    return errors


def validate_settlement(settlement: dict, source_ids: set[str]) -> list[str]:
    errors = []
    for key in ("ticket_id", "operator", "rule_version", "outcome", "stake", "profit", "source_id", "source_url"):
        if settlement.get(key) is None or settlement.get(key) == "":
            errors.append(f"missing {key}")
    if settlement.get("outcome") not in {"win", "loss", "push", "void"}:
        errors.append("invalid outcome")
    if settlement.get("source_id") not in source_ids or not official_url(settlement.get("source_url", "")):
        errors.append("settlement requires a known official source")
    if not finite(settlement.get("stake")) or settlement.get("stake", -1) < 0 or not finite(settlement.get("profit")):
        errors.append("invalid stake/profit")
    return errors

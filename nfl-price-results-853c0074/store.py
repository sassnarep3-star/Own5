#!/usr/bin/env python3
"""Append-only, fail-closed NFL quote/result store. Standard library only."""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SCHEMAS = {
    "price_snapshots.csv": [
        "origin_id", "event_id", "market_type", "market_id", "selection_id",
        "phase", "line", "odds_american", "book", "jurisdiction",
        "captured_at_utc", "source_updated_at_utc", "source_url", "source_hash_sha256",
        "verified_status", "flag_id",
    ],
    "market_settlements.csv": [
        "origin_id", "event_id", "market_type", "market_id", "selection_id",
        "settlement", "settled_at_utc", "book", "jurisdiction", "rules_url",
        "source_url", "source_hash_sha256", "verified_status", "flag_id",
    ],
    "graded_bets.csv": [
        "bet_id", "origin_id", "event_id", "market_id", "selection_id", "book", "jurisdiction",
        "stake_units", "accepted_odds_american", "accepted_price_source_url", "settlement", "net_return_units",
        "settlement_source_url", "rules_url", "verified_status", "flag_id",
    ],
}
VALID_MARKETS = {"side", "total", "moneyline", "player_prop", "parlay", "prop_combo"}
VALID_PHASES = {"opening", "closing", "intermediate"}
VALID_SETTLEMENTS = {"won", "lost", "push", "void", "half_won", "half_lost"}

class StoreError(ValueError):
    pass

def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)

def _utc(value: str, field: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StoreError(f"{field} must be an ISO-8601 timestamp with timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise StoreError(f"{field} must be explicitly UTC (Z or +00:00)")
    return parsed

def _ensure_csv(path: Path, columns: list[str]) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as stream:
            csv.writer(stream, lineterminator="\n").writerow(columns)
    with path.open(newline="", encoding="utf-8") as stream:
        header = next(csv.reader(stream), [])
    if header != columns:
        raise StoreError(f"schema mismatch in {path.name}: expected {columns}, found {header}")

def initialize() -> None:
    for filename, columns in SCHEMAS.items():
        _ensure_csv(DATA / filename, columns)

def audit_snapshot_pairs(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Report originated quote keys missing either opening or closing evidence."""
    grouped: dict[tuple[str, ...], set[str]] = {}
    fields=("origin_id","event_id","market_type","market_id","selection_id","book","jurisdiction")
    for row in rows:
        key=tuple(row[k] for k in fields)
        grouped.setdefault(key,set()).add(row["phase"])
    incomplete=[]
    for key,phases in sorted(grouped.items()):
        missing=[phase for phase in ("opening","closing") if phase not in phases]
        if missing:
            incomplete.append({**dict(zip(fields,key)),"missing_phases":";".join(missing)})
    return incomplete

def append_price(record: dict[str, str]) -> None:
    initialize()
    required = SCHEMAS["price_snapshots.csv"]
    missing = [key for key in required if not record.get(key, "").strip() and key not in {"line", "source_updated_at_utc", "source_hash_sha256", "flag_id"}]
    if missing:
        raise StoreError("required price fields missing: " + ", ".join(missing))
    if record["market_type"] not in VALID_MARKETS:
        raise StoreError("unsupported market_type")
    if record["phase"] not in VALID_PHASES:
        raise StoreError("phase must be opening, intermediate or closing")
    if not _valid_url(record["source_url"]):
        raise StoreError("source_url must be an HTTPS source link")
    _utc(record["captured_at_utc"], "captured_at_utc")
    if record.get("source_updated_at_utc"):
        _utc(record["source_updated_at_utc"], "source_updated_at_utc")
    if record.get("line"):
        try: float(record["line"])
        except ValueError as exc: raise StoreError("line must be numeric or blank") from exc
    try:
        odds = int(record["odds_american"])
        if odds == 0: raise ValueError
    except ValueError as exc:
        raise StoreError("odds_american must be a non-zero integer") from exc
    if record.get("source_hash_sha256") and (len(record["source_hash_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in record["source_hash_sha256"].lower())):
        raise StoreError("source_hash_sha256 must be a 64-character hex digest")
    if record["verified_status"] not in {"verified", "unverified", "source_pending"}:
        raise StoreError("verified_status must be verified, unverified, or source_pending")
    path = DATA / "price_snapshots.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    natural_key = (record["origin_id"], record["event_id"], record["market_id"], record["selection_id"], record["book"], record["jurisdiction"], record["phase"], record["captured_at_utc"])
    for old in rows:
        key = tuple(old[k] for k in ("origin_id", "event_id", "market_id", "selection_id", "book", "jurisdiction", "phase", "captured_at_utc"))
        if key == natural_key:
            raise StoreError("duplicate snapshot key; store is append-only")
    with path.open("a", newline="", encoding="utf-8") as stream:
        csv.DictWriter(stream, fieldnames=required, lineterminator="\n").writerow({k: record.get(k, "") for k in required})

def append_settlement(record: dict[str, str]) -> None:
    initialize()
    required = SCHEMAS["market_settlements.csv"]
    missing = [key for key in required if not record.get(key, "").strip() and key not in {"source_hash_sha256", "flag_id"}]
    if missing:
        raise StoreError("required settlement fields missing: " + ", ".join(missing))
    if record["market_type"] not in VALID_MARKETS or record["settlement"] not in VALID_SETTLEMENTS:
        raise StoreError("unknown market type or settlement state")
    if not _valid_url(record["source_url"]) or not _valid_url(record["rules_url"]):
        raise StoreError("both official settlement result and applicable rules require HTTPS source URLs")
    _utc(record["settled_at_utc"], "settled_at_utc")
    if record["verified_status"] != "verified":
        raise StoreError("settlements are accepted only after source verification")
    path = DATA / "market_settlements.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    key = tuple(record[k] for k in ("origin_id", "event_id", "market_id", "selection_id", "book", "jurisdiction"))
    if any(tuple(row[k] for k in ("origin_id", "event_id", "market_id", "selection_id", "book", "jurisdiction")) == key for row in rows):
        raise StoreError("settlement already exists for market/selection/book/jurisdiction")
    with path.open("a", newline="", encoding="utf-8") as stream:
        csv.DictWriter(stream, fieldnames=required, lineterminator="\n").writerow({k: record.get(k, "") for k in required})

def _net_return(stake: float, odds: int, settlement: str) -> float:
    profit = stake * (odds / 100 if odds > 0 else 100 / abs(odds))
    return {"won": profit, "lost": -stake, "push": 0.0, "void": 0.0,
            "half_won": profit / 2, "half_lost": -stake / 2}[settlement]

def append_graded_bet(bet: dict[str, str]) -> None:
    """Append a ticket only when its exact source-verified settlement exists."""
    initialize()
    required_input = ("bet_id", "origin_id", "event_id", "market_id", "selection_id", "book", "jurisdiction", "stake_units", "accepted_odds_american", "accepted_price_source_url")
    missing=[key for key in required_input if not bet.get(key, "").strip()]
    if missing: raise StoreError("required graded-bet fields missing: " + ", ".join(missing))
    stake=float(bet["stake_units"]); odds=int(bet["accepted_odds_american"])
    if stake<=0 or odds==0: raise StoreError("stake must be positive and American odds non-zero")
    if not _valid_url(bet["accepted_price_source_url"]): raise StoreError("accepted price requires an HTTPS evidence URL")
    settlements=_read(DATA/"market_settlements.csv")
    key=(bet["origin_id"],bet["event_id"],bet["market_id"],bet["selection_id"],bet["book"],bet["jurisdiction"])
    matches=[r for r in settlements if (r["origin_id"],r["event_id"],r["market_id"],r["selection_id"],r["book"],r["jurisdiction"])==key and r["verified_status"]=="verified"]
    if len(matches)!=1: raise StoreError("exactly one verified market settlement is required")
    settled=matches[0]
    net=_net_return(stake,odds,settled["settlement"])
    row={"bet_id":bet["bet_id"],"origin_id":bet["origin_id"],"event_id":bet["event_id"],"market_id":bet["market_id"],"selection_id":bet["selection_id"],"book":bet["book"],"jurisdiction":bet["jurisdiction"],"stake_units":str(stake),"accepted_odds_american":str(odds),"accepted_price_source_url":bet["accepted_price_source_url"],"settlement":settled["settlement"],"net_return_units":format(net,".10g"),"settlement_source_url":settled["source_url"],"rules_url":settled["rules_url"],"verified_status":"verified","flag_id":""}
    path=DATA/"graded_bets.csv"
    with path.open(newline="",encoding="utf-8") as stream: rows=list(csv.DictReader(stream))
    if any(r["bet_id"]==row["bet_id"] for r in rows): raise StoreError("duplicate bet_id; graded ledger is append-only")
    with path.open("a",newline="",encoding="utf-8") as stream:csv.DictWriter(stream,fieldnames=SCHEMAS["graded_bets.csv"],lineterminator="\n").writerow(row)

def evaluate(graded_rows: list[dict[str, str]]) -> dict[str, float | int | None]:
    """ROI only from rows explicitly graded against official results and rules."""
    eligible = [r for r in graded_rows if r.get("verified_status") == "verified"
                and r.get("settlement_source_url") and _valid_url(r["settlement_source_url"])
                and r.get("accepted_price_source_url") and _valid_url(r["accepted_price_source_url"])
                and r.get("rules_url") and _valid_url(r["rules_url"])
                and r.get("settlement") in VALID_SETTLEMENTS]
    if len(eligible) != len(graded_rows):
        raise StoreError("refusing to calculate ROI: one or more graded bets lack verified sourced settlement")
    stake_total = net_total = 0.0
    for row in eligible:
        stake = float(row["stake_units"])
        odds = int(row["accepted_odds_american"])
        if stake <= 0 or odds == 0:
            raise StoreError("stake must be positive and American odds non-zero")
        expected = _net_return(stake, odds, row["settlement"])
        if row.get("net_return_units") and abs(float(row["net_return_units"]) - expected) > 1e-9:
            raise StoreError("recorded net return does not reconcile to stake, odds and settlement")
        stake_total += stake
        net_total += expected
    return {"bets": len(eligible), "staked_units": stake_total, "net_units": net_total,
            "roi_pct": (100 * net_total / stake_total) if stake_total else None}

def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="create empty append-only store tables")
    sub.add_parser("roi", help="calculate ROI from verified graded_bets.csv rows")
    args = parser.parse_args()
    initialize()
    if args.command == "roi":
        result = evaluate(_read(DATA / "graded_bets.csv"))
        print(json.dumps(result, sort_keys=True))
    else:
        print("initialized; no price snapshots or market settlements are fabricated")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

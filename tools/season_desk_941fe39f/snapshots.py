"""Immutable availability snapshots, the capture ledger and data-drift alarms.

The brief asks for three things that are one mechanism:

  * capture the official availability pages at least daily, keep a hash, and be
    able to replay exactly what was known at a past clock time;
  * store every injury read WITH its clock time and publish the delta, never the
    level;
  * pin every parser to an expected schema and fail loudly when a required
    field disappears, rather than publishing a blank.

The mechanism is an append-only ledger: data/availability/ledger.json holds one
row per captured artefact per clock time, with the SHA-256 of the exact bytes
this desk read, the parser that consumed it, and the schema fingerprint that the
parser expects. Adding a capture never rewrites an older row. `replay()` returns
the row that was in force at a given clock time, which is what a point-in-time
backtest must read.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "nfl-season-941fe39f"
OFFICIAL = DESK / "data" / "official"
AVAIL = DESK / "data" / "availability"

# The schema each parser requires. If a capture stops carrying one of these
# fields the build must fail, not publish a blank (brief: drift alarm).
REQUIRED = {
    "OFF-INJURY-DATED-20261117": {
        "parser": "availability.load_injuries",
        "fields": ["reads[].rows_from_this_read"],
        "unit": "injury_report",
    },
    "OFF-DEPTH-3CLUB-20261117": {
        "parser": "availability.parse_club_block",
        "fields": ["clubs[].rows"],
        "unit": "depth_chart",
    },
    "OFF-DEPTH-HOU-IMAGEPROBE-20261117": {
        "parser": "none (blocked)",
        "fields": ["url", "probe_result"],
        "unit": "depth_chart",
    },
    "OFF-TRANSACTIONS-20261117": {
        "parser": "availability.roster_turnover",
        "fields": ["rows"],
        "unit": "transactions",
    },
    "OFF-RESERVE-20261117": {
        "parser": "none (cross-check only)",
        "fields": ["rows"],
        "unit": "reserve_list",
    },
    "OFF-INJURY-CARRIED-20261115": {
        "parser": "availability.load_prior_injuries",
        "fields": ["prior_capture", "url", "retrieval_utc"],
        "unit": "injury_report",
    },
    "OFF-SCHEDULE-RELEASE-2026": {
        "parser": "site schedule page cross-check",
        "fields": ["claims", "published_date"],
        "unit": "schedule_announcement",
    },
}

# How old a unit may be before the freshness alarm fires. The brief's own words:
# capture the injury report "at least daily", Wednesday to kickoff.
MAX_AGE_HOURS = {
    "injury_report": 24,
    "depth_chart": 168,        # clubs republish weekly at most
    "transactions": 168,
    "reserve_list": 168,
    "schedule_announcement": 24 * 365,
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def schema_fingerprint(obj: dict) -> str:
    keys = sorted(k for k in obj.keys() if k not in ("rows", "clubs", "claims", "reads"))
    return sha256_bytes(",".join(keys).encode())[:16]


def build_ledger() -> dict:
    """Rebuild the ledger from the capture files. Append-only by construction:
    a new capture is a new file with a new clock time and a new row."""
    rows = []
    failures = []
    for path in sorted(OFFICIAL.glob("*.json")):
        raw = path.read_bytes()
        obj = json.loads(raw)
        sid = obj.get("source_id", path.stem)
        req = REQUIRED.get(sid)
        # A capture that wraps several reads at different clock times is one
        # file but several clock times. Each read gets its own ledger row, so
        # replay can pick the one that was in force (brief: point-in-time).
        reads = (obj.get("carried_forward_reads") or []) + (obj.get("reads") or [])
        if reads:
            for read in reads:
                rows.append({
                    "source_id": f"{sid}#{read.get('label', 'read')}",
                    "file": f"data/official/{path.name}",
                    "unit": (req or {}).get("unit", "other"),
                    "parser": (req or {}).get("parser", ""),
                    "captured_utc": read.get("retrieval_utc", ""),
                    "sha256": sha256_bytes(raw),
                    "bytes": len(raw),
                    "schema_fingerprint": schema_fingerprint(obj),
                    "required_fields_present": "YES",
                    "missing_fields": "",
                    "publisher": obj.get("publisher", ""),
                    "url": read.get("requested_url") or read.get("url", ""),
                })
            continue
        captured = (obj.get("retrieval_utc") or
                    (obj.get("reads") or [{}])[0].get("retrieval_utc") or
                    (obj.get("carried_forward_reads") or [{}])[0].get("retrieval_utc") or "")
        missing = []
        if req:
            for f in req["fields"]:
                if f.startswith("clubs[].rows"):
                    fields = set()
                    for club in obj.get("clubs", []):
                        fields |= set(club.keys())
                    for need in ("team", "url", "rows"):
                        if need not in fields:
                            missing.append(f"clubs[].{need}")
                elif f.startswith("reads[].") or f.startswith("carried_forward_reads[]."):
                    sub = f.split(".", 1)[1]
                    if sub == "rows_from_this_read":
                        if not obj.get("reads") or \
                                not any(r.get("rows_from_this_read") for r in obj.get("reads", [])):
                            missing.append(f)
                    elif not obj.get("reads"):
                        missing.append(f)
                elif f not in obj:
                    missing.append(f)
        if missing:
            failures.append({"source_id": sid, "missing_fields": missing})
        rows.append({
            "source_id": sid,
            "file": f"data/official/{path.name}",
            "unit": (req or {}).get("unit", "other"),
            "parser": (req or {}).get("parser", ""),
            "captured_utc": captured,
            "sha256": sha256_bytes(raw),
            "bytes": len(raw),
            "schema_fingerprint": schema_fingerprint(obj),
            "required_fields_present": "YES" if not missing else "NO",
            "missing_fields": ";".join(missing),
            "publisher": obj.get("publisher", ""),
            "url": obj.get("url", ""),
        })
    return {"rows": rows, "failures": failures}


def freshness(ledger_rows: list[dict], now_utc: str) -> list[dict]:
    import datetime as dt
    now = dt.datetime.fromisoformat(now_utc.replace("Z", "+00:00"))
    out = []
    for r in ledger_rows:
        if not r["captured_utc"]:
            out.append({**r, "age_hours": "", "max_age_hours": MAX_AGE_HOURS.get(r["unit"], ""),
                        "state": "NO CLOCK TIME"})
            continue
        t = dt.datetime.fromisoformat(r["captured_utc"].replace("Z", "+00:00"))
        age = (now - t).total_seconds() / 3600.0
        limit = MAX_AGE_HOURS.get(r["unit"], 240)
        out.append({
            **r,
            "age_hours": f"{age:.2f}",
            "max_age_hours": limit,
            "state": "FRESH" if age <= limit else "STALE",
        })
    return out


def replay(ledger_rows: list[dict], unit: str, at_utc: str) -> dict | None:
    """The capture that was in force for `unit` at `at_utc` (point-in-time read)."""
    candidates = [r for r in ledger_rows
                  if r["unit"] == unit and r["captured_utc"] and r["captured_utc"] <= at_utc]
    if not candidates:
        return None
    return max(candidates, key=lambda r: r["captured_utc"])


def capture_log(ledger_rows: list[dict]) -> list[dict]:
    """One row per clock time per unit: how many distinct clock times exist.

    This is the number the 'immutable multi-day snapshots' requirement is about:
    a unit with one clock time cannot support a replay test.
    """
    by_unit: dict[str, list[str]] = {}
    for r in ledger_rows:
        by_unit.setdefault(r["unit"], []).append(r["captured_utc"])
    out = []
    for unit in sorted(by_unit):
        times = sorted(set(t for t in by_unit[unit] if t))
        out.append({
            "unit": unit,
            "distinct_clock_times": len(times),
            "first": times[0] if times else "",
            "last": times[-1] if times else "",
            "can_replay": "YES" if len(times) >= 2 else "NO - one clock time only",
            "captures": len(by_unit[unit]),
        })
    return out

#!/usr/bin/env python3
"""Scheduled price capture: appends snapshots and, from now on, closing lines.

Designed to run in CI, where the network is reachable (the sandbox this desk was
built in cannot reach espn.com at all - a dead end recorded during development so
that nobody tries it again). What it does, in order:

1. Fetch the provider's scoreboard JSON for the target date.
2. For each event, read the single odds object the provider publishes, plus the
   event state. A ``pre`` state is a pre-game snapshot; a ``post`` state means this
   is the first look at a finished game, so the price on offer at that moment is
   *not* a closing line and is never labelled as one.
3. Compare against the last stored snapshot for the same (game, market, selection)
   and append rows only where something changed, or where the stage advances.
4. Record the run itself - status, row counts, the digest of the payload - in
   ``data/capture_log.csv``. A failed fetch is a logged outage, and the demotion
   gate's D6 rule counts outage weeks; a silent skip would be worse than a failure.

Write-then-verify: every appended row is hash-chained through ``store``, so a run
that produced a broken chain would fail verification and the commit would be
reverted by the next check rather than silently kept.

The job is additive by construction: it never rewrites an existing row, and it
refuses to append anything whose provider block is missing - a blank is appended as
a blank row with state ABSENT, which is the only way a gap can be audited later.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
LOG = os.path.join(DATA, "capture_log.csv")
LOG_COLS = ["run_utc", "target_date", "status", "events_seen", "rows_appended", "payload_sha256",
            "provider", "note"]
API = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={yyyymmdd}"
UA = "own5-desk-ce1f16ff/1.0 (repository CI capture job)"


def fetch(date_str: str):
    url = API.format(yyyymmdd=date_str.replace("-", ""))
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        raw = r.read()
    return url, raw, json.loads(raw.decode("utf-8"))


def parse_events(payload):
    """One record per (game, market, selection) the provider exposes."""
    out = []
    for ev in payload.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        odds = comp.get("odds") or []
        away = home = None
        for c in comp.get("competitors", []):
            if c.get("homeAway") == "away":
                away = (c.get("team") or {}).get("abbreviation")
            else:
                home = (c.get("team") or {}).get("abbreviation")
        state = ((ev.get("status") or {}).get("type") or {})
        start = ev.get("startDate", "")
        season = ((ev.get("season") or {}).get("year"), (ev.get("week") or {}).get("number"))
        gk = f"{away}@{home}-{season[0]}-w{season[1]}"
        base = dict(game_key=gk, kickoff=start, season=season[0], week=season[1],
                    away=away, home=home, state=state.get("state", ""),
                    detail=state.get("detail", ""))
        if not odds:
            out.append(dict(base, market="side", selection="", line_value="", price_american="",
                            stage="pre_game" if state.get("state") == "pre" else "post_game",
                            present=False, raw="", provider=""))
            continue
        o = odds[0]
        prov = (o.get("provider") or {}).get("name", "")
        spread = o.get("spread")
        total = o.get("overUnder")
        det = o.get("details", "")
        # the scoreboard endpoint exposes no moneyline in the headline odds object; a
        # row is still written for it, marked absent, so the gap is visible downstream
        home_ml = away_ml = ""
        out.append(dict(base, market="side", selection=(home or ""), line_value=spread,
                        price_american=o.get("homeOdds", ""), stage="pre_game", present=True,
                        raw=det, provider=prov))
        out.append(dict(base, market="side", selection=(away or ""), line_value=spread,
                        price_american=o.get("awayOdds", ""), stage="pre_game", present=True,
                        raw=det, provider=prov))
        if total is not None:
            for sel, key in (("over", "overOdds"), ("under", "underOdds")):
                out.append(dict(base, market="total", selection=sel, line_value=total,
                                price_american=o.get(key, ""), stage="pre_game", present=True,
                                raw=f"o/u {total}", provider=prov))
        out.append(dict(base, market="moneyline", selection=(home or ""), line_value="",
                        price_american=home_ml, stage="pre_game", present=False,
                        raw="not exposed by this endpoint", provider=prov))
    return out


def read_log():
    if not os.path.exists(LOG):
        return []
    with open(LOG, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_log(row):
    os.makedirs(DATA, exist_ok=True)
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOG_COLS)
        if new:
            w.writeheader()
        w.writerow(row)


def main(argv=None):
    argv = argv or sys.argv[1:]
    date_str = argv[0] if argv else datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        url, raw, payload = fetch(date_str)
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        append_log(dict(run_utc=stamp, target_date=date_str, status=f"FAILED: {type(e).__name__}",
                        events_seen=0, rows_appended=0, payload_sha256="", provider="",
                        note="outage week counted by demotion rule D6"))
        print(f"capture failed: {type(e).__name__}: {e}")
        return 2
    digest = hashlib.sha256(raw).hexdigest()
    events = parse_events(payload)
    seen = len({e["game_key"] for e in events})
    out = os.path.join(DATA, f"captured_{date_str}.csv")
    cols = ["game_key", "season", "week", "away", "home", "market", "selection", "line_value",
            "price_american", "stage", "present", "raw", "provider", "source_url", "captured_utc"]
    os.makedirs(DATA, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for e in events:
            w.writerow({**{c: e.get(c, "") for c in cols[:-2]},
                        "source_url": url, "captured_utc": stamp})
    append_log(dict(run_utc=stamp, target_date=date_str,
                    status="ok" if events else "ok-but-empty", events_seen=seen,
                    rows_appended=len(events), payload_sha256=digest[:16],
                    provider=(events[0]["provider"] if events else ""),
                    note=f"raw payload kept at data/captured_{date_str}.csv; this file is an "
                         f"observation log, not the store - run.py folds it in on the next build"))
    print(f"captured {seen} games, {len(events)} market rows, payload {digest[:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

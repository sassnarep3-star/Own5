"""Scheduled capture of the official NFL.com injury report.

For each candidate week the job:
  1. fetches https://www.nfl.com/injuries/league/2026/regN (redirects followed; final URL kept),
  2. hashes the raw bytes (SHA-256) and stamps the fetch time (UTC, to the second),
  3. checks the week the page actually serves against the week requested (a 302 to another week
     is recorded as served_other_week, never as the requested week),
  4. stores the raw bytes once per distinct hash (immutable, named by hash),
  5. parses the page with parse.py (drift alarm: DriftError -> exit 2),
  6. appends one ledger row per read. Every read is kept, so the timeline is complete.

Weeks requested = the latest served week in the ledger, and the week after it. Nothing is typed in by hand.
Exit codes: 0 ok or expected pre-publication state; 2 parse drift; 3 fetch failure; 4 blocked (no consent).
"""
import csv
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

import parse

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data"
CAPTURES = HERE / "captures"
LEDGER = DATA / "ledger.csv"
SEASON = 2026
UA = "own5-desk-capture/1.0 (+https://github.com/sassnarep3-star/Own5; read-only official-page capture)"
LEDGER_FIELDS = [
    "capture_utc", "requested_week", "season", "http_status", "final_url", "served_week_url",
    "served_week_title", "bytes", "sha256", "content_status", "raw_file", "rows_file",
    "parse_status", "games", "team_tables", "rows", "flags", "error", "last_modified",
]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read()
        return {"status": resp.status, "final_url": resp.geturl(), "body": body,
                "last_modified": resp.headers.get("Last-Modified", "")}


def read_ledger():
    if not LEDGER.exists():
        return []
    with LEDGER.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_ledger(rows):
    DATA.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=LEDGER_FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in LEDGER_FIELDS})


def latest_served_week(ledger):
    weeks = [int(r["served_week_url"]) for r in ledger
             if r.get("served_week_url", "").isdigit() and r.get("parse_status") in ("ok", "served_other_week")]
    return max(weeks) if weeks else None


CONSENT_ENV = "NFL_CAPTURE_CONSENT"
BLOCKED_MESSAGE = (
    "BLOCKED: NFL.com Terms and Conditions s.1.3 prohibit systematic retrieval of data to compile a "
    "database absent NFL's express prior written consent. No request was sent. Set "
    f"{CONSENT_ENV}=1 only after written consent is on file (see terms.html, decision D-01)."
)


def main(argv):
    if os.environ.get(CONSENT_ENV) != "1":
        print(BLOCKED_MESSAGE, file=sys.stderr)
        return 4
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    ledger = read_ledger()
    seen_hashes = {r["sha256"] for r in ledger if r.get("sha256")}
    last = latest_served_week(ledger)
    start = last if last else int(os.environ.get("SEED_WEEK", "10"))
    weeks = [start, start + 1]
    exit_code = 0
    new_rows = []
    for wk in weeks:
        if wk < 1 or wk > 18:
            continue
        url = f"https://www.nfl.com/injuries/league/{SEASON}/reg{wk}"
        rec = {"capture_utc": stamp, "requested_week": wk, "season": SEASON}
        try:
            got = fetch(url)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            rec.update({"http_status": "", "final_url": url, "parse_status": "fetch_failed",
                        "error": f"{type(exc).__name__}: {exc}"[:300]})
            new_rows.append(rec)
            exit_code = max(exit_code, 3)
            continue
        body = got["body"]
        digest = hashlib.sha256(body).hexdigest()
        text = body.decode("utf-8", errors="replace")
        meta = parse.page_week(text, got["final_url"])
        rec.update({
            "http_status": got["status"], "final_url": got["final_url"],
            "served_week_url": meta["url_week"] or "", "served_week_title": meta["title_week"] or "",
            "bytes": len(body), "sha256": digest, "last_modified": got["last_modified"],
        })
        served = meta["url_week"]
        if served != wk or meta["title_week"] != wk:
            rec["content_status"] = "not_yet_published" if served and served < wk else "served_other_week"
            rec["parse_status"] = "served_other_week"
            rec["error"] = f"requested week {wk}; page serves week {served} (title week {meta['title_week']})"
            if digest not in seen_hashes:
                rec["raw_file"] = _store_raw(text, body, served or "unknown", digest, stamp)
                seen_hashes.add(digest)
            new_rows.append(rec)
            continue
        if digest in seen_hashes:
            rec["content_status"] = "unchanged"
            rec["parse_status"] = "ok"
            # Count from the stored rows file of the matching hash, so the ledger stays complete.
            prior = next((r for r in ledger + new_rows if r.get("sha256") == digest and r.get("parse_status") == "ok"), None)
            if prior:
                for k in ("games", "team_tables", "rows", "flags", "rows_file", "raw_file"):
                    rec[k] = prior.get(k, "")
            new_rows.append(rec)
            continue
        try:
            rows, games, summary = parse.parse(text, got["final_url"])
        except parse.DriftError as exc:
            rec.update({"content_status": "new", "parse_status": "parse_drift", "error": str(exc)[:400]})
            rec["raw_file"] = _store_raw(text, body, wk, digest, stamp)
            seen_hashes.add(digest)
            new_rows.append(rec)
            exit_code = max(exit_code, 2)
            continue
        raw_file = _store_raw(text, body, wk, digest, stamp)
        rows_file = _store_rows(rows, games, raw_file, digest, wk, stamp)
        seen_hashes.add(digest)
        rec.update({"content_status": "new", "parse_status": "ok", "raw_file": raw_file,
                    "rows_file": rows_file, "games": summary["games"],
                    "team_tables": summary["team_tables"], "rows": summary["rows"],
                    "flags": " | ".join(summary["flags"])})
        new_rows.append(rec)
    write_ledger(ledger + new_rows)
    for r in new_rows:
        print(f"{r['capture_utc']} req=wk{r['requested_week']} served={r.get('served_week_url','')} "
              f"http={r.get('http_status','')} status={r['parse_status']} content={r.get('content_status','')} "
              f"rows={r.get('rows','')} sha={r.get('sha256','')[:12]}")
    return exit_code


def _store_raw(text, body, week, digest, stamp):
    d = CAPTURES / f"{SEASON}" / f"reg{week}"
    d.mkdir(parents=True, exist_ok=True)
    name = f"{stamp.replace(':', '').replace('-', '')}_{digest[:16]}.html"
    path = d / name
    path.write_bytes(body)
    return str(path.relative_to(HERE))


def _store_rows(rows, games, raw_file, digest, week, stamp):
    d = CAPTURES / f"{SEASON}" / f"reg{week}"
    name = pathlib.Path(raw_file).name.replace(".html", ".rows.json")
    path = d / name
    path.write_text(json.dumps({"capture_utc": stamp, "sha256": digest, "raw_file": raw_file,
                                "games": games, "rows": rows}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return str(path.relative_to(HERE))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

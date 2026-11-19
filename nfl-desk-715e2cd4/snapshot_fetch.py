"""Scheduled immutable availability capture (bytes + hashes, no parsing).

This is the automation half of the availability requirement. It fetches the
official pages listed below, stores the *raw bytes* gzipped under
data/capture_store/<UTC stamp>/<slug>.html.gz, and appends one row per capture to
data/capture_store/index.csv with the sha256, byte length, HTTP status and the
fetch clock.

Deliberate limits:
  * It never parses a value out of the HTML. Parsing is what turns a capture into
    a claim, and claims are made only in pipeline.py from hand-verified extracts.
  * It fails soft per URL: a 403 or a timeout is recorded as such and the run
    continues, so a blocked source cannot silently look like "no change".
  * A re-fetch whose bytes are identical to the most recent capture of the same
    URL is recorded as UNCHANGED, not as a new revision.

Run: python3 snapshot_fetch.py [--stamp 2026-11-20T14:00:00Z]
"""

import argparse
import csv
import gzip
import hashlib
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "data", "capture_store")
INDEX = os.path.join(STORE, "index.csv")
UA = ("Mozilla/5.0 (compatible; Own5-availability-capture/1.0; "
      "+https://github.com/sassnarep3-star/Own5)")

TARGETS = [
    ("injury-report-reg11", "https://www.nfl.com/injuries/league/2026/reg11"),
    ("injury-report-reg10", "https://www.nfl.com/injuries/league/2026/reg10"),
    ("standings-2026-reg", "https://www.nfl.com/standings/league/2026/REG"),
    ("schedule-week-11", "https://www.nfl.com/schedules/2026/by-week/week-11"),
    ("transactions", "https://www.nfl.com/transactions/"),
]


def last_hash_by_url():
    out = {}
    if not os.path.exists(INDEX):
        return out
    with open(INDEX, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("status") == "OK":
                out[r["url"]] = r["sha256"]
    return out


def append(rows):
    new = not os.path.exists(INDEX)
    os.makedirs(STORE, exist_ok=True)
    with open(INDEX, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        if new:
            w.writerow(["capture_id", "slug", "url", "fetched_utc", "http_status",
                        "bytes", "sha256", "file", "status", "note"])
        for r in rows:
            w.writerow(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stamp", default=None)
    ap.add_argument("--timeout", type=int, default=25)
    a = ap.parse_args()
    stamp = a.stamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    day = stamp[:10]
    existing = 0
    if os.path.exists(INDEX):
        with open(INDEX, encoding="utf-8") as fh:
            existing = sum(1 for _ in csv.DictReader(fh))
    seen = last_hash_by_url()
    outdir = os.path.join(STORE, day)
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for i, (slug, url) in enumerate(TARGETS, 1):
        cid = "A%04d" % (existing + i)
        status, blobbytes, note = "", b"", ""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                       "Accept": "text/html,*/*"})
            with urllib.request.urlopen(req, timeout=a.timeout) as resp:
                status = str(resp.status)
                blobbytes = resp.read()
        except urllib.error.HTTPError as e:
            status = str(e.code)
            note = "http error: %s" % e.reason
        except Exception as e:                      # noqa: BLE001 - fail soft by design
            status = "ERR"
            note = "%s: %s" % (type(e).__name__, e)
        if status != "200" or not blobbytes:
            rows.append([cid, slug, url, stamp, status, 0, "", "", "FAILED", note])
            continue
        digest = hashlib.sha256(blobbytes).hexdigest()
        rel = os.path.join("capture_store", day, "%s.html.gz" % slug)
        path = os.path.join(STORE, day, "%s.html.gz" % slug)
        with gzip.open(path, "wb", compresslevel=9) as fh:
            fh.write(blobbytes)
        if seen.get(url) == digest:
            rows.append([cid, slug, url, stamp, status, len(blobbytes), digest, rel,
                         "UNCHANGED", "identical bytes to the most recent capture"])
        else:
            rows.append([cid, slug, url, stamp, status, len(blobbytes), digest, rel,
                         "OK", "new or changed bytes" if seen.get(url) else "first capture"])
        seen[url] = digest
    append(rows)
    ok = sum(1 for r in rows if r[8] == "OK")
    un = sum(1 for r in rows if r[8] == "UNCHANGED")
    bad = sum(1 for r in rows if r[8] == "FAILED")
    print("capture %s: %d new/changed, %d unchanged, %d failed" % (stamp, ok, un, bad))
    for r in rows:
        print("  %-24s %-10s %s" % (r[1], r[8], r[9][:70]))
    # never fail the run for a blocked source; the ledger records the failure
    return 0


if __name__ == "__main__":
    sys.exit(main())

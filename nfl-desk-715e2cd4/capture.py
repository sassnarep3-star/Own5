"""Availability capture ledger helper (frozen-schema, hash-on-write).

This module does NOT fetch anything: network fetching is done by the operator's
page-read tool and pasted into raw/. What it does is make every capture
reproducible and tamper-evident:

  * computes the sha256 of each raw extract,
  * refuses to append a capture whose hash already exists for the same URL and
    day (a no-op capture is not a delta),
  * writes data/capture_log.csv as an append-only series.

Run after pasting a new raw extract:
    python3 capture.py --dataset "Week 11 injury report" \
        --url "https://www.nfl.com/injuries/league/2026/reg11" \
        --file raw/injuries_2026_reg11.txt --stamp 2026-11-20T14:00:00Z
"""
import argparse, csv, hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "data", "capture_log.csv")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--stamp", required=True)
    a = ap.parse_args()
    path = a.file if os.path.isabs(a.file) else os.path.join(HERE, a.file)
    if not os.path.exists(path):
        print("capture REFUSED: %s does not exist" % path)
        return 2
    digest = sha256(path)
    day = a.stamp[:10]
    existing = []
    if os.path.exists(LOG):
        with open(LOG, encoding="utf-8") as fh:
            existing = list(csv.DictReader(fh))
    for r in existing:
        if r["url"] == a.url and r["retrieved_utc"][:10] == day:
            if r["sha256"] == digest:
                print("capture SKIPPED: identical bytes already logged for %s on %s" % (a.url, day))
                return 0
            print("capture CONFLICT: %s already changed once on %s; log it as a revision, "
                  "do not overwrite" % (a.url, day))
            return 3
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        if new:
            w.writerow(["capture_id", "dataset", "url", "retrieved_utc", "file", "sha256", "bytes"])
        cid = "P%03d" % (len(existing) + 1)
        w.writerow([cid, a.dataset, a.url, a.stamp, os.path.relpath(path, HERE), digest,
                    os.path.getsize(path)])
    print("capture LOGGED: %s %s" % (cid, digest[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

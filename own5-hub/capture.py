#!/usr/bin/env python3
"""Immutable daily capture of official NFL pages (stdlib only).

For each official page: fetch the bytes, hash the raw bytes (sha256), store a gzip copy under
captures/raw/<name>/<UTC stamp>.html.gz (never overwritten), and append one row to captures/manifest.csv.
Structural pins are checked on the raw bytes. A failed pin is recorded in the manifest AND makes the
process exit 1, so the scheduled job fails loudly instead of publishing a blank.

Sources (all official NFL pages):
  injuries   https://www.nfl.com/injuries/                       (current injury report)
  standings  https://www.nfl.com/standings/league/2026/REG      (league standings)
  reserve    https://www.nfl.com/transactions/league/reserve-list/<YYYY>/<MM>  (reserve list, current month)
"""
import csv, datetime as dt, gzip, hashlib, os, re, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "captures", "raw")
MANIFEST = os.path.join(HERE, "captures", "manifest.csv")
UA = "Mozilla/5.0 (compatible; Own5-capture/1.0; +https://github.com/sassnarep3-star/Own5)"
FIELDS = ["captured_utc", "name", "url", "http_status", "bytes", "sha256_raw", "raw_file",
          "pins_passed", "pins_detail"]


def pins_for(name, body: str):
    """Return (passed: bool, detail: str). Pins are structural, not content-judgements."""
    checks = []
    if name == "injuries":
        checks = [("title_week", bool(re.search(r"Injuries\s*-\s*WEEK\s*\d+", body, re.I)) or "2026 NFL Injury Report" in body),
                  ("practice_status_header", "Practice Status" in body),
                  ("game_status_header", "Game Status" in body),
                  ("player_rows>=100", len(re.findall(r"/players/", body)) >= 100)]
    elif name == "standings":
        checks = [("club_logos>=32", len(re.findall(r"clubs/logos/", body)) >= 32),
                  ("pf_pa_header", ("PF" in body and "PA" in body))]
    elif name == "reserve":
        checks = [("reserve_rows_header", "Reserve/Injured" in body or "Reserve/Injured" in body.replace("&#x2F;", "/")
                   or "reserve-list" in body)]
    failed = [c for c, ok in checks if not ok]
    detail = "ok" if not failed else "FAILED:" + ";".join(failed)
    return (not failed), detail


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read()


def main():
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    month = now.strftime("%Y/%m")
    targets = [
        ("injuries", "https://www.nfl.com/injuries/"),
        ("standings", "https://www.nfl.com/standings/league/2026/REG"),
        ("reserve", f"https://www.nfl.com/transactions/league/reserve-list/{month}"),
    ]
    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    new_manifest = not os.path.exists(MANIFEST)
    rows, all_ok = [], True
    for name, url in targets:
        status, body, err = None, b"", ""
        try:
            status, body = fetch(url)
        except urllib.error.HTTPError as e:
            status, err = e.code, str(e)
        except Exception as e:  # network or TLS failure is recorded, never silently dropped
            err = repr(e)
        sha = hashlib.sha256(body).hexdigest() if body else ""
        raw_rel = ""
        if body:
            d = os.path.join(RAW, name)
            os.makedirs(d, exist_ok=True)
            raw_rel = os.path.relpath(os.path.join(d, f"{stamp}.html.gz"), HERE).replace(os.sep, "/")
            p = os.path.join(HERE, raw_rel)
            if os.path.exists(p):
                raise SystemExit(f"refusing to overwrite immutable capture {p}")
            with gzip.open(p, "wb", mtime=0) as f:
                f.write(body)
        ok, detail = (False, "no body: " + (err or f"http {status}"))
        if body and status == 200:
            ok, detail = pins_for(name, body.decode("utf-8", "replace"))
        all_ok = all_ok and ok
        rows.append({"captured_utc": now.isoformat().replace("+00:00", "Z"), "name": name, "url": url,
                     "http_status": status if status is not None else "", "bytes": len(body),
                     "sha256_raw": sha, "raw_file": raw_rel, "pins_passed": "yes" if ok else "no",
                     "pins_detail": detail})
    with open(MANIFEST, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_manifest:
            w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['name']:10s} http={r['http_status']} bytes={r['bytes']} sha256={r['sha256_raw'][:16]} pins={r['pins_passed']} {r['pins_detail']}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

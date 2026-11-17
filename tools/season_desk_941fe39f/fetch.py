"""Corpus fetcher for the 941fe39f NFL Season Desk.

This module does ONE thing: prove where the corpus came from. It never parses a
value out of thin air and it never invents a number.

Two classes of input:

1. PINNED CORPUS (downloaded here, hashed here)
   nflverse publishes the league's own gamebooks (NFLGSIS statistics, nflverse
   `pbp`/`stats_*`) and the operator closing lines as CSV, under CC-BY-4.0.
   The whole `nfldata` repository is fetched as a single tarball at a *pinned
   commit* and stored under data/corpus/raw/. Every downstream table is
   regenerated from that tarball, so the backtest corpus is reproducible by
   anyone, from a hash we publish.

2. OFFICIAL CAPTURES (read with the sandbox fetcher, transcribed to JSON)
   nfl.com is not reachable with TLS from the execution sandbox (documented by
   the e46fb855 session and re-confirmed here), so pages fetched with the
   sandbox fetcher are transcribed into data/official/*.json by
   tools/season_desk_941fe39f/capture_official.py. Each capture records URL,
   retrieval UTC and the transcription method.

Run:  python3 tools/season_desk_941fe39f/fetch.py --check
      python3 tools/season_desk_941fe39f/fetch.py --download   (needs network)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESK = ROOT / "nfl-season-941fe39f"
RAW = DESK / "data" / "corpus" / "raw"
TARBALL = RAW / "nfldata_e045566e.tar.gz"

# Pinned nfldata commit. Fetched 2026-11-17; the commit is the one that was
# HEAD of nflverse/nfldata at that moment (verified against api.github.com,
# see data/corpus/PROVENANCE.md).
NFLDATA_COMMIT = "e045566ea9f90e3aa15b3b43d87df4ea63d0fae2"
NFLDATA_COMMIT_DATE = "2026-11-17T00:35:18Z"
NFLDATA_URL = f"https://codeload.github.com/nflverse/nfldata/tar.gz/{NFLDATA_COMMIT}"
NFLDATA_SHA256 = "9a6a736819bd6587f135d0995778c23ef9e51a9587d9e901f5dc84072504462c"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    print(f"GET {NFLDATA_URL}")
    req = urllib.request.Request(
        NFLDATA_URL,
        headers={"User-Agent": "Own5-season-desk/1.0 (research; reproducible corpus)"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = resp.read()
    TARBALL.write_bytes(body)
    digest = hashlib.sha256(body).hexdigest()
    print(f"  wrote {TARBALL.relative_to(ROOT)}  {len(body):,} bytes  sha256={digest}")
    if digest != NFLDATA_SHA256:
        print(f"  !! digest differs from the pinned value {NFLDATA_SHA256}")
        print("     nflverse re-writes history by publishing a new commit; a new")
        print("     commit means a new pin. Record the new sha256 in this file and")
        print("     in data/corpus/PROVENANCE.md before rebuilding.")
        return
    print("  digest matches the pin")


def check() -> int:
    if not TARBALL.exists():
        print(f"MISSING {TARBALL.relative_to(ROOT)}")
        return 1
    digest = sha256_file(TARBALL)
    ok = digest == NFLDATA_SHA256
    print(f"{'OK ' if ok else 'BAD'} {TARBALL.relative_to(ROOT)} sha256={digest}")
    print(f"    pin={NFLDATA_SHA256} commit={NFLDATA_COMMIT} ({NFLDATA_COMMIT_DATE})")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--download" in sys.argv:
        download()
        sys.exit(check())
    if "--check" in sys.argv:
        sys.exit(check())
    print(__doc__)

"""Read the repository's pinned inputs, record their digests, and expose rows.

This desk never edits those files. It reads them, records a sha256 of what it
actually consumed in ``data/input_register.csv``, and compares that digest with
the digest the owning session recorded (``data/decision-desk/raw/provenance.json``)
and with the *live* upstream release asset digest returned by the GitHub API when
that register is present. A mirror that has moved upstream is reported, not
silently re-read.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os

DESK = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DESK)   # repository root
DATA = os.path.join(DESK, "data")

PINNED = {
    "nflverse_games": "data/decision-desk/raw/games.csv.gz",
    "nflverse_injuries_2026": "data/decision-desk/raw/injuries_2026.csv.gz",
    "nflverse_injuries_2025": "data/decision-desk/raw/injuries_2025.csv.gz",
    "nflverse_injuries_2024": "data/decision-desk/raw/injuries_2024.csv.gz",
    "nflverse_snap_counts_2026": "data/decision-desk/raw/snap_counts_2026.csv.gz",
    "nflverse_snap_counts_2025": "data/decision-desk/raw/snap_counts_2025.csv.gz",
    "nflverse_snap_counts_2024": "data/decision-desk/raw/snap_counts_2024.csv.gz",
    "spreadspoke_scores": "data/raw/spreadspoke_scores.csv",
    "slate_2026_vendored": "nfl-desk-ce1f16ff/pinned/slate_2026_vendored.csv",
    "injuries_wk10_official_vendored": "nfl-desk-ce1f16ff/pinned/injuries_wk10_official.csv",
    "depth_charts_vendored": "nfl-desk-ce1f16ff/pinned/depth_charts_2026_11_13.csv",
}
UPSTREAM = {
    "nflverse_games": ("https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv.gz",
                       "schedules", "games.csv.gz"),
    "nflverse_injuries_2026": ("https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_2026.csv.gz",
                               "injuries", "injuries_2026.csv.gz"),
    "nflverse_snap_counts_2026": ("https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_2026.csv.gz",
                                  "snap_counts", "snap_counts_2026.csv.gz"),
    "spreadspoke_scores": ("https://github.com/tobycrabtree/spreadspoke/blob/1d309cb7f8f58a9eceb36293979dbcb1af70db94/spreadspoke_scores.csv",
                           None, None),
}
# Recorded 2026-11-14 from https://api.github.com/repos/<repo>/releases/tags/<tag>
# (MK-S-12). Values are the live digest of the asset at the time of this session;
# they are constants so the build stays deterministic.
LIVE_UPSTREAM_DIGESTS = {
    "nflverse_games": ("d6b2eb30f3aa3ab6075f0aa9b93263dfa8685f4309e41f075f933a429ab50d7b", 516930),
    "nflverse_injuries_2026": ("6e56f7302777a9cf2933045ddbe54ff8cbdbfeb007feac0cb1d65adb2528869a", 68014),
    "nflverse_snap_counts_2026": ("7dd345c4e0a55ce8441a59d0e83420492f18bc4887e894f00fab6d0290c31208", 241157),
}
MANIFEST = os.path.join(DESK, "pinned", "vendor_manifest.json")
SPREADSPOKE_BLOB_SHA = "dd3c3cdb6d3e5c1f68f2ed9ddaaf68c70cb8ce28"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha(path):
    """git hash-object equivalent: sha1('blob %d\\0' + bytes)."""
    data = open(path, "rb").read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def read_gz_csv(rel):
    p = os.path.join(ROOT, rel)
    with gzip.open(p, "rt", encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.DictReader(f))


def read_csv(rel):
    with open(os.path.join(ROOT, rel), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def provenance_recorded():
    p = os.path.join(ROOT, "data/decision-desk/raw/provenance.json")
    if not os.path.exists(p):
        return {}
    d = json.load(open(p, encoding="utf-8"))
    out = {}
    for a in d.get("assets", []):
        out[a.get("committed_as", "")] = a.get("sha256", "")
    out["__retrieved_utc__"] = d.get("retrieved_utc", "")
    return out


def register():
    """Digest table for every file this desk consumes -> data/input_register.csv.

    ``pin_check`` answers one question: is what I am about to read the same bytes
    somebody else pinned and signed? For nflverse mirrors that is the digest the
    owning session recorded; for the spreadspoke dataset it is the git blob SHA of
    the pinned upstream commit; for this desk's vendored copies it is the digest
    written at vendor time.
    """
    rec = provenance_recorded()
    man = {}
    if os.path.exists(MANIFEST):
        for f, info in json.load(open(MANIFEST, encoding="utf-8")).get("files", {}).items():
            man[os.path.basename(f)] = info
    rows = []
    for key, rel in PINNED.items():
        p = os.path.join(ROOT, rel)
        exists = os.path.exists(p)
        local = sha256_file(p) if exists else ""
        size = os.path.getsize(p) if exists else ""
        owner_rec = rec.get(rel, "")
        if owner_rec:
            pin_status = ("MATCHES owner's recorded digest" if local == owner_rec
                          else "DIFFERS from owner's recorded digest")
        elif key == "spreadspoke_scores" and exists:
            blob = git_blob_sha(p)
            pin_status = ("git blob SHA == upstream blob at pinned commit"
                          if blob == SPREADSPOKE_BLOB_SHA
                          else "git blob SHA differs from upstream blob")
        elif exists and os.path.basename(p) in man:
            want = man[os.path.basename(p)].get("sha256", "")
            pin_status = ("vendored copy matches the digest recorded at vendor time"
                          if want and want == local
                          else ("vendored copy DIFFERS from its vendor manifest digest" if want
                                else "vendored copy - no digest recorded for this file"))
        elif exists:
            pin_status = "no owner digest on record"
        else:
            pin_status = "MISSING"
        live = LIVE_UPSTREAM_DIGESTS.get(key)
        if live:
            drift = ("upstream asset digest differs from pinned copy (asset republished)"
                     if local != live[0] else "upstream asset digest matches pinned copy")
        else:
            drift = ""
        up = UPSTREAM.get(key, ("", None, None))
        origin = man.get(os.path.basename(p), {}).get("from", "")
        rows.append({
            "input_key": key,
            "path": rel,
            "bytes": size,
            "sha256_local": local,
            "owner_recorded_sha256": owner_rec,
            "pin_check": pin_status,
            "upstream_url": up[0] or origin,
            "upstream_drift": drift,
            "kind": "AGGREGATOR" if key.startswith("nflverse") else
                    ("THIRD-PARTY" if key == "spreadspoke_scores" else "VENDORED-OFFICIAL"),
        })
    os.makedirs(DATA, exist_ok=True)
    cols = list(rows[0].keys())
    with open(os.path.join(DATA, "input_register.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return rows


def games_2026():
    rows = read_gz_csv(PINNED["nflverse_games"])
    return [r for r in rows if r.get("season") == "2026"]


def games_window(seasons=("2021", "2022", "2023", "2024", "2025")):
    rows = read_gz_csv(PINNED["nflverse_games"])
    return [r for r in rows if r.get("season") in seasons and r.get("game_type") == "REG"]


def injuries(week=None, seasons=("2024", "2025", "2026")):
    out = []
    for key, rel in ((k, v) for k, v in PINNED.items() if k.startswith("nflverse_injuries")):
        season = key.rsplit("_", 1)[1]
        if season not in seasons:
            continue
        for r in read_gz_csv(rel):
            if r.get("season") != season:
                continue
            if week is not None and r.get("week") != str(week):
                continue
            out.append(r)
    return out


def snaps(seasons=("2024", "2025", "2026")):
    out = []
    for key, rel in ((k, v) for k, v in PINNED.items() if k.startswith("nflverse_snap_counts")):
        season = key.rsplit("_", 1)[1]
        if season not in seasons:
            continue
        for r in read_gz_csv(rel):
            if r.get("season") in seasons:
                out.append(r)
    return out


if __name__ == "__main__":
    for row in register():
        print(row["input_key"], row["pin_check"], "|", row["upstream_drift"])

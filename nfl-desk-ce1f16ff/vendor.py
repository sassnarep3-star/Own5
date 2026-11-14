"""Vendor the official transcriptions this desk depends on into ``pinned/``.

Run once, by hand or by an agent: ``python3 vendor.py``. It is deliberately NOT
part of ``run.py``: this desk reads only its own pinned copies afterwards, so a
later edit by another session cannot silently move the ground under a published
table. ``verify.py`` re-checks that every pinned file still matches the digest
recorded here.

Everything copied was itself transcribed from an official page by the named
source; nothing in this file invents a value. If a source file is missing the
script says so and writes no partial copy.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PIN = os.path.join(HERE, "pinned")
MANIFEST = os.path.join(PIN, "vendor_manifest.json")
VENDOR_UTC = "2026-11-14T21:55Z"

SIBLING_RAW = "nfl-desk-864d5668/raw_inputs.py"
COPIES = [
    ("nfl-desk-864d5668/data/injuries.csv", "injuries_wk10_official.csv",
     "Official 2026 Week 10 league injury report (nfl.com/injuries/league/2026/reg10) "
     "transcribed row by row by session 864d5668 on 2026-11-13"),
    ("nfl-desk-864d5668/data/depth_detail.csv", "depth_charts_2026_11_13.csv",
     "Official club /team/depth-chart pages, transcribed by session 864d5668 on 2026-11-13 "
     "(31 of 32 clubs; Houston publishes an image only and is blank there)"),
]


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def vendor_slate():
    src = os.path.join(ROOT, SIBLING_RAW)
    if not os.path.exists(src):
        return None, None
    spec = importlib.util.spec_from_file_location("sibling_raw_inputs", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = os.path.join(PIN, "slate_2026_vendored.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["week", "away", "home", "away_pts", "home_pts", "date", "neutral_label", "source_url"])
        for wk, aw, hm, ap, hp, dt, neu in mod.LEDGER:
            w.writerow([wk, aw, hm, "" if ap is None else ap, "" if hp is None else hp,
                        dt, neu or "", mod.LEDGER_SRC.get(wk, mod.W % wk)])
    outb = os.path.join(PIN, "byes_2026_vendored.csv")
    with open(outb, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["week", "team"])
        for wk, teams in sorted(mod.BYES.items()):
            for t in sorted(teams):
                w.writerow([wk, t])
    return out, outb


def main():
    os.makedirs(PIN, exist_ok=True)
    files = {}
    for rel, dst, note in COPIES:
        src = os.path.join(ROOT, rel)
        if not os.path.exists(src):
            print(f"SKIP {rel} (missing)")
            continue
        data = open(src, "rb").read()
        with open(os.path.join(PIN, dst), "wb") as f:
            f.write(data)
        files[f"pinned/{dst}"] = {"from": rel, "sha256_of_source": sha256_file(src),
                                  "sha256": hashlib.sha256(data).hexdigest(), "note": note}
        print(f"vendored {rel} -> pinned/{dst} ({len(data)} bytes)")

    slate, byes = vendor_slate()
    if slate:
        for p, label in ((slate, "slate_2026_vendored.csv"), (byes, "byes_2026_vendored.csv")):
            files[f"pinned/{label}"] = {
                "from": SIBLING_RAW,
                "sha256_of_source": sha256_file(os.path.join(ROOT, SIBLING_RAW)),
                "sha256": sha256_file(p),
                "note": "extracted verbatim from the sibling session's pinned official transcription"}
            print(f"vendored {SIBLING_RAW} -> pinned/{label}")

    manifest = {"vendored_utc": VENDOR_UTC, "session": "ce1f16ff", "files": files}
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
        f.write("\n")
    print("manifest written:", MANIFEST)


if __name__ == "__main__":
    main()

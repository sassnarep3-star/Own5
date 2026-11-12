#!/usr/bin/env python3
"""Export the authored registries (requirements, suggestions, questions,
flags, sources) and the per-strategy gate matrix to CSV, with a per-row
source link so the provenance rule holds for them too."""
from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content  # noqa: E402
import lib  # noqa: E402

DD = "https://github.com/sassnarep3-star/Own5/blob/main/data/decision-desk/"
DOC = "https://github.com/sassnarep3-star/Own5/blob/main/research/38a1fc27/"


def dump(name, rows, fields):
    path = os.path.join(lib.OUTDIR, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


def main() -> int:
    dump("requirements.csv",
         [{**r, "source_url": DOC + "requirements.md"} for r in content.REQUIREMENTS],
         ["id", "requirement", "status", "how", "gap", "evidence", "source_url"])
    dump("suggestions.csv",
         [{**r, "source_url": DD + "suggestions.csv"} for r in content.SUGGESTIONS],
         ["id", "title", "problem", "recommendation", "impact", "effort", "confidence",
          "evidence", "decision", "owner", "review_test", "source_url"])
    dump("questions.csv",
         [{**r, "source_url": DD + "questions.csv"} for r in content.QUESTIONS],
         ["id", "question", "why", "have", "missing", "resolve", "blocks", "status",
          "related", "source_url"])
    dump("flagged.csv",
         [{**r, "source_url": r["source"]} for r in content.FLAGS],
         ["id", "item", "severity", "detail", "action", "source", "source_url"])
    dump("sources.csv",
         [{**r, "source_url": r["url"]} for r in content.SOURCES],
         ["id", "name", "tier", "url", "used", "retrieval", "source_url"])

    ledger = lib.read_csv(os.path.join(lib.OUTDIR, "strategy_ledger.csv"))
    rows = []
    for r in ledger:
        parts = [p for p in (r.get("gate_results") or "").split(";") if "=" in p]
        for part in parts:
            gate, _, result = part.partition("=")
            rows.append({"strategy": r["variant"], "gate": gate.strip(),
                         "result": result.strip(),
                         "note": next((n.strip() for n in (r.get("gate_results") or "").split(";")
                                       if n.strip().startswith(gate.strip() + "=")), ""),
                         "source_url": DD + "strategy_ledger.csv"})
    dump("gate_matrix.csv", rows, ["strategy", "gate", "result", "note", "source_url"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

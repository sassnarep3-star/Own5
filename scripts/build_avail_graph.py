#!/usr/bin/env python3
"""Normalize the official Week 10 injury-report capture and derive the A3 ledgers.

This is the generator for task A3.  It is deterministic: no clock, no network, no
git.  Everything it writes is derived from two committed inputs.

Inputs
------
  data/avail-graph/injury_report_all_2026-11-18.csv
      The capture itself: a field-by-field transcription of the official NFL
      Week 10 injury report (https://www.nfl.com/injuries/league/2026/reg10).
      Hand-transcribed because the sandbox cannot reach the host; the URL and
      the read window are recorded on every row.

  nfl-market-desk/data/injuries_wk10.csv
      The committed 2026-11-15 read of the same official page, already in the
      repository.  It is the "before" side of the delta.

Outputs
-------
  data/avail-graph/injury_designations_2026-11-18.csv
      The designated subset of the capture (Out / Doubtful / Questionable).

  data/avail-graph/injury_delta.csv
      The substantive row-level difference between the two reads.

  data/avail-graph/injury_delta_normalised.csv
      An explicit audit of every difference that the comparison NORMALISES AWAY
      and that therefore does not appear in the delta above.  See the
      "normalisation audit" section below - this file exists because a delta
      that hides normalised differences is not a complete diff.

  data/avail-graph/provenance.csv
      SHA-256 / size ledger for the capture and every file derived from it.

Usage
-----
  python3 scripts/build_avail_graph.py
"""
from __future__ import annotations

import csv
import hashlib
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "avail-graph"
BASELINE = ROOT / "nfl-market-desk" / "data" / "injuries_wk10.csv"

CAPTURE = DATA / "injury_report_all_2026-11-18.csv"
DESIGNATIONS = DATA / "injury_designations_2026-11-18.csv"
DELTA = DATA / "injury_delta.csv"
DELTA_NORMALISED = DATA / "injury_delta_normalised.csv"
PROVENANCE = DATA / "provenance.csv"

SOURCE_URL = "https://www.nfl.com/injuries/league/2026/reg10"
CAPTURED_UTC = "2026-11-18T03:40:00Z"
METHOD = "fetch_page read of the official page (8 chunks), transcribed field by field"

# The fields compared between the two reads.
COMPARED = ("injury_description", "practice_status", "game_status")

# The literal token the committed baseline uses for "the official page printed
# no injury here".  The 2026-11-18 capture uses an empty cell for the same
# thing.  The two are equal in meaning, so the comparison normalises them.
BLANK_TOKEN = "BLANK"

DELTA_NOTE = "adjudicated against the official page re-read on 2026-11-18"

DELIM_NOTE = ("the comma separating two injury names is canonicalised to ', ' "
              "before comparison")


# --------------------------------------------------------------------------
# normalisation
# --------------------------------------------------------------------------
def blank_equivalent(value: str) -> str:
    """An empty cell and the literal token BLANK mean the same thing."""
    v = value.strip()
    return "" if v == BLANK_TOKEN else v


def canonical_delimiters(value: str) -> str:
    """Canonicalise the separator between two injury names.

    The official page prints more than one injury for some players and
    separates them with a comma.  Comparing the raw strings would make the
    separator's whitespace look like a change, so the separator is
    canonicalised to ", " before the two reads are compared.  The ORDER of the
    injury names is preserved: "Not injury related - personal matter, Knee" is
    not the same string as "Knee, Not injury related - personal matter".
    """
    v = blank_equivalent(value)
    if not v:
        return ""
    parts = [p.strip() for p in v.split(",") if p.strip()]
    return ", ".join(parts)


def canonical(value: str) -> str:
    """The form used for the comparison of both textual fields."""
    return canonical_delimiters(value)


def sha256(path: pathlib.Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def write_csv(path: pathlib.Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> None:
    capture_rows = list(csv.DictReader(CAPTURE.open()))
    baseline_rows = list(csv.DictReader(BASELINE.open()))

    capture_fields = list(capture_rows[0].keys())
    capture_by = {(r["club"], r["player"]): r for r in capture_rows}
    baseline_by = {(r["club"], r["player"]): r for r in baseline_rows}

    # ---- 1. the designated subset of the capture ------------------------
    designated = [r for r in capture_rows if r["game_status"].strip() != BLANK_TOKEN]
    write_csv(DESIGNATIONS, capture_fields, designated)

    # ---- 2. the substantive delta ---------------------------------------
    # Only players present in BOTH reads can be compared.  A player in one
    # read and not the other is not a field change; it is a roster change and
    # is reported as such rather than being silently dropped.
    only_capture = sorted(set(capture_by) - set(baseline_by))
    only_baseline = sorted(set(baseline_by) - set(capture_by))

    delta_rows: list[dict] = []
    normalised_rows: list[dict] = []

    # The delta follows the order of the 2026-11-15 read, so that the two
    # ledgers can be read side by side in report order.
    compared_keys = [k for k in ((r["club"], r["player"]) for r in baseline_rows)
                     if k in capture_by]
    for key in compared_keys:
        club, player = key
        old = baseline_by[key]
        new = capture_by[key]
        for field in COMPARED:
            old_raw = old[field]
            new_raw = new[field]
            if old_raw == new_raw:
                continue
            old_canon = canonical(old_raw)
            new_canon = canonical(new_raw)
            if old_canon == new_canon:
                # The two values differ only in a way the comparison
                # normalises away.  Record it explicitly.
                if blank_equivalent(old_raw) == blank_equivalent(new_raw):
                    klass = "empty-vs-literal-BLANK"
                    normalisation = ("an empty injury cell and the literal token BLANK "
                                     "both mean the official page listed no injury")
                else:
                    klass = "delimiter-only"
                    normalisation = ("the comma separating two injury names is "
                                     "canonicalised to ', ' before comparison")
                normalised_rows.append({
                    "club": club,
                    "player": player,
                    "field": field,
                    "value_2026_11_15": old_raw,
                    "value_2026_11_18": new_raw,
                    "difference_class": klass,
                    "normalisation_applied": normalisation,
                    "canonical_value": new_canon,
                    "effect_on_delta": "normalised away; not a substantive change",
                    "source_url": SOURCE_URL,
                })
                continue
            delta_rows.append({
                "club": club,
                "player": player,
                "field": field,
                "value_2026_11_15": old_raw,
                "value_2026_11_18": new_raw,
                "change": "changed",
                "note": DELTA_NOTE,
                "source_url": SOURCE_URL,
            })

    write_csv(DELTA, ["club", "player", "field", "value_2026_11_15",
                      "value_2026_11_18", "change", "note", "source_url"], delta_rows)

    # ---- 2b. the rows where the normalisation is load-bearing ------------
    # The official page prints more than one injury for some players and
    # separates the names with a comma.  The comparison above canonicalises
    # that separator, so for these rows the comparison depends on the
    # canonical form.  They are listed here even when the two reads are
    # currently byte-identical, because a reader has to be able to see WHICH
    # rows the normalisation is applied to - not only the ones where it
    # happened to bite.
    for key in compared_keys:
        club, player = key
        old_raw = baseline_by[key]["injury_description"]
        new_raw = capture_by[key]["injury_description"]
        if "," not in old_raw and "," not in new_raw:
            continue
        if old_raw == new_raw:
            continue
        normalised_rows.append({
            "club": club,
            "player": player,
            "field": "injury_description",
            "value_2026_11_15": old_raw,
            "value_2026_11_18": new_raw,
            "difference_class": "delimiter-only",
            "normalisation_applied": DELIM_NOTE,
            "canonical_value": canonical(new_raw),
            "effect_on_delta": "normalised away; not a substantive change",
            "source_url": SOURCE_URL,
        })
    # Rows that are byte-identical today but are still compared on the
    # canonical form are appended with their own audit class.
    load_bearing = []
    for key in compared_keys:
        club, player = key
        old_raw = baseline_by[key]["injury_description"]
        new_raw = capture_by[key]["injury_description"]
        if "," not in old_raw and "," not in new_raw:
            continue
        if old_raw != new_raw:
            continue
        load_bearing.append({
            "club": club,
            "player": player,
            "field": "injury_description",
            "value_2026_11_15": old_raw,
            "value_2026_11_18": new_raw,
            "difference_class": "multi-injury (delimiter canonicalised)",
            "normalisation_applied": DELIM_NOTE,
            "canonical_value": canonical(new_raw),
            "effect_on_delta": ("the two reads are byte-identical today; this row is "
                                "compared on the canonical form, so a change in the "
                                "separator's whitespace could never register"),
            "source_url": SOURCE_URL,
        })
    normalised_rows.extend(load_bearing)

    write_csv(DELTA_NORMALISED, ["club", "player", "field", "value_2026_11_15",
                                 "value_2026_11_18", "difference_class",
                                 "normalisation_applied", "canonical_value",
                                 "effect_on_delta", "source_url"], normalised_rows)

    # ---- 3. provenance --------------------------------------------------
    prov_rows = []
    for path, note in (
        (CAPTURE, "full all-player read of the official Week 10 injury report; "
                  "hash covers the stored extract, not the server response bytes"),
        (DESIGNATIONS, "designated-only subset (Out/Doubtful/Questionable) of the "
                       "same read; hash covers the stored extract, not the server "
                       "response bytes"),
        (DELTA, "row-level difference between the 2026-11-15 committed read and the "
                "2026-11-18 read; hash covers the stored extract, not the server "
                "response bytes"),
        (DELTA_NORMALISED, "audit of the differences the comparison normalises away "
                           "(empty-vs-literal-BLANK and delimiter-only); these do not "
                           "appear in the delta; hash covers the stored extract"),
    ):
        digest, size = sha256(path)
        prov_rows.append({
            "file": str(path.relative_to(ROOT)),
            "sha256": digest,
            "bytes": size,
            "source_url": SOURCE_URL,
            "captured_utc": CAPTURED_UTC,
            "method": METHOD,
            "note": note,
        })
    write_csv(PROVENANCE, ["file", "sha256", "bytes", "source_url", "captured_utc",
                            "method", "note"], prov_rows)

    # ---- 4. self-check --------------------------------------------------
    multi = [r for r in capture_rows if "," in r["injury_description"]]
    print(f"capture rows         : {len(capture_rows)}")
    print(f"designated rows      : {len(designated)}")
    print(f"delta rows           : {len(delta_rows)}")
    print(f"normalised-away rows : {len(normalised_rows)}")
    print(f"  of which delimiter-only      : "
          f"{sum(1 for r in normalised_rows if r['difference_class'] == 'delimiter-only')}")
    print(f"  of which empty-vs-BLANK      : "
          f"{sum(1 for r in normalised_rows if r['difference_class'] == 'empty-vs-literal-BLANK')}")
    print(f"multi-injury rows in the capture: {len(multi)}")
    print(f"players only in the 2026-11-18 read : {len(only_capture)} "
          f"{only_capture if only_capture else ''}")
    print(f"players only in the 2026-11-15 read : {len(only_baseline)} "
          f"{only_baseline if only_baseline else ''}")

    assert len(capture_rows) == 347, len(capture_rows)
    assert len(designated) == 171, len(designated)
    assert len(delta_rows) == 6, len(delta_rows)
    assert not only_capture and not only_baseline, (only_capture, only_baseline)
    print("self-check passed")


if __name__ == "__main__":
    main()

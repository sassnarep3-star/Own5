"""Market view: the price store, the open/pre-game tables, and the gap report.

Three jobs.

1. ``build_store`` writes ``data/price_snapshots.csv`` (schema and hash chain in
   ``store.py``) - the snapshot store the project was asked for, holding opening
   and pre-game numbers for every originated market, with the closing stage left
   to the scheduled capture job.

2. ``line_sheet`` writes ``data/line_sheet.csv``. Requirement: model fair line,
   market line and difference are three separate column groups, in the mandated
   origination order (side, total, moneyline). Nothing here averages a fair line
   into a market line, and nothing fills a missing market number with a guess: a
   gap renders as a gap and is counted in the register.

3. ``gap_report`` writes ``data/market_gaps.csv`` - one row per
   (game, market, stage) cell, saying whether it is present, blank or absent from
   the source, and what the desk intends to do about it. The closing-line rows are
   the reason no CLV claim exists anywhere in this build.
"""
from __future__ import annotations

import csv
import os

import statslib as st
import store
import originate
from pinned import capture as cap

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

SHEET_COLS = [
    "game_key", "week", "date", "away", "home", "neutral", "origination_order",
    # --- stage 1: side
    "fair_spread_home", "model_expected_margin_home", "model_sd_margin", "fair_home_ml_stage1",
    "market_spread_home", "market_home_price", "market_away_price", "market_opening_spread_home",
    "diff_spread_pts", "diff_spread_ticks",
    # --- stage 2: total
    "fair_total", "model_expected_total", "market_total", "market_over_price", "market_under_price",
    "market_opening_total", "diff_total_pts", "move_total_open_to_pre_pts",
    # --- stage 3: moneyline
    "model_p_home_ml", "model_p_away_ml", "model_p_tie", "fair_home_ml", "fair_away_ml",
    "market_home_ml", "market_away_ml", "market_p_home_novig",
    "diff_home_ml_prob", "model_fair_hold_pct", "market_hold_pct",
    # --- provenance
    "market_provider", "market_stage", "market_captured_at", "market_source_url",
    "official_slate_url", "verification_tier", "note",
]


def build_store():
    rows = store.build_rows()
    n = store.write(rows)
    ok, problems, n_rows, head = store.check_chain(rows)
    with open(os.path.join(DATA, "store_meta.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item", "value"])
        w.writerow(["rows", n_rows])
        w.writerow(["head_hash", head])
        w.writerow(["chain_valid", "yes" if ok else "no: " + "; ".join(problems[:3])])
        for lineage in ("CAPTURE", "CI", "MIRROR-PINNED"):
            w.writerow([f"rows_{lineage}", sum(1 for r in rows if r["lineage"] == lineage)])
        for stage in ("opening", "pre_game", "closing", "undocumented"):
            w.writerow([f"rows_{stage}", sum(1 for r in rows if r["line_stage"] == stage)])
    return rows, ok, problems


def line_sheet():
    """Fair vs market vs difference, one row per originated game, in origination order."""
    fair = originate.originate_slate()[0]
    rows = []
    for f in fair:
        d = dict(
            game_key=f["game_key"], week=f["week"], date=f["date"], away=f["away"], home=f["home"],
            neutral=f["neutral"],
            origination_order="1 side -> 2 total -> 3 moneyline (derived from 1, not refitted)",
            fair_spread_home=f["fair_spread_home"],
            model_expected_margin_home=f["model_expected_margin_home"],
            model_sd_margin=f["model_sd_margin"],
            fair_home_ml_stage1=f["fair_home_ml"],
            market_spread_home=f["market_spread_home"], market_home_price=f["market_home_spread_price"],
            market_away_price=f["market_away_spread_price"],
            market_opening_spread_home=f["market_opening_spread_home"],
            diff_spread_pts=f["diff_spread_pts"],
            diff_spread_ticks=("" if f["diff_spread_pts"] in ("", None)
                               else round(float(f["diff_spread_pts"]) / 0.5, 1)),
            fair_total=f["fair_total"], model_expected_total=f["model_expected_total"],
            market_total=f["market_total"], market_over_price=f["market_over_price"],
            market_under_price=f["market_under_price"], market_opening_total=f["market_opening_total"],
            diff_total_pts=f["diff_total_pts"],
            move_total_open_to_pre_pts=_move(f),
            model_p_home_ml=f["model_p_home_ml"], model_p_away_ml=f["model_p_away_ml"],
            model_p_tie=f["model_p_tie"], fair_home_ml=f["fair_home_ml"],
            fair_away_ml=f["fair_away_ml"],
            market_home_ml=f["market_home_ml"],
            market_away_ml=f["market_away_ml"], market_p_home_novig=f["market_p_home_novig"],
            diff_home_ml_prob=f["diff_home_ml_prob"],
            model_fair_hold_pct=0.0, market_hold_pct=f["market_hold_pct"],
            market_provider=f["market_provider"], market_stage=f["market_stage"],
            market_captured_at=f["market_captured_at"], market_source_url=f["market_source_url"],
            official_slate_url=f["official_url"],
            verification_tier=("MODEL=official-reconciled feed; MARKET=OPERATOR (DraftKings via ESPN); "
                               "DIFFERENCE=cross-tier, so it is a comparison, not an official number"
                               if f["market_provider"] else "MODEL ONLY - no market number captured"),
            note=cap.PRICE_NOTES.get(f["game_key"].rsplit("-", 2)[0], ""))
        # the model's own no-vig hold is zero by construction: state it so the
        # comparison against the market hold is not mistaken for a fairer price
        rows.append(d)
    with open(os.path.join(DATA, "line_sheet.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SHEET_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in SHEET_COLS})
    return rows


def _move(f):
    """Open -> pre-game move on the total, in points, only where both stages exist."""
    a, b = f.get("market_opening_total"), f.get("market_total")
    if a in ("", None) or b in ("", None):
        return ""
    return round(float(b) - float(a), 2)


def gap_report(rows):
    """Market coverage by game and stage. Absent is written as absent."""
    g = originate.originate_slate()[0]
    out = []
    for f in g:
        gk = f["game_key"]
        site_g = f["game_key"].rsplit("-", 2)[0]
        for mkt, stage, present in (
            ("side", "opening", f["market_opening_spread_home"] not in ("", None)),
            ("side", "pre_game", f["market_spread_home"] not in ("", None)),
            ("side", "closing", False),
            ("total", "opening", f["market_opening_total"] not in ("", None)),
            ("total", "pre_game", f["market_total"] not in ("", None)),
            ("total", "closing", False),
            ("moneyline", "opening", False),
            ("moneyline", "pre_game", f["market_home_ml"] not in ("", None)),
            ("moneyline", "closing", False)):
            plan = ("capture at kickoff by the scheduled job (the page's own final state before "
                    "the game starts)" if stage == "closing" else
                    ("not published by the source page at all - see question MK-Q-01 on where a "
                     "true opening moneyline could legitimately come from"
                     if stage == "opening" and mkt == "moneyline" else "captured"))
            out.append(dict(week=f["week"], game_key=gk, market=mkt, stage=stage,
                            state=("present" if present else "ABSENT FROM SOURCE"),
                            provider=(f["market_provider"] or "n/a"),
                            captured_at=(f["market_captured_at"] or ""),
                            plan=plan,
                            source=(f["market_source_url"] or cap.URLS["CAP-03"])))
    with open(os.path.join(DATA, "market_gaps.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["week", "game_key", "market", "stage", "state", "provider",
                                          "captured_at", "plan", "source"])
        w.writeheader()
        w.writerows(out)
    return out


def store_coverage(rows):
    """Summary the gates consume: how many closing snapshots exist, per game."""
    stages = {}
    for r in rows:
        stages[r["line_stage"]] = stages.get(r["line_stage"], 0) + 1
    games = {r["game_key"] for r in rows if r["lineage"] in ("CAPTURE", "CI")}
    return dict(rows=len(rows), stages=stages, capture_games=len(games),
                closing_rows=stages.get("closing", 0))


def write():
    srows, ok, problems = build_store()
    import results_feed
    results_feed.game_conditions()
    sheet = line_sheet()
    gaps = gap_report(srows)
    cov = store_coverage(srows)
    with open(os.path.join(DATA, "market_summary.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item", "value", "note"])
        w.writerow(["store rows", cov["rows"], "hash chain valid: " + ("yes" if ok else "NO")])
        for k, v in sorted(cov["stages"].items()):
            w.writerow([f"rows_stage_{k}", v, ""])
        w.writerow(["games with an operator snapshot", cov["capture_games"],
                    "13 of the 14 Week-10 games plus 3 Week-11 games carried a price on the page"])
        w.writerow(["fair-vs-market rows with a market number",
                    sum(1 for r in sheet if r["market_spread_home"] not in ("", None)),
                    f"{len(sheet) - sum(1 for r in sheet if r['market_spread_home'] not in ('', None))}"
                    " rows priced with no market number to compare against"])
        w.writerow(["closing snapshots", cov["closing_rows"],
                    "zero, so no CLV claim is made anywhere in this build (gate V-08 BLOCKED BY DATA)"])
    return dict(store=cov, chain_ok=ok, chain_problems=problems, sheet=len(sheet), gaps=len(gaps))


if __name__ == "__main__":
    print(write())

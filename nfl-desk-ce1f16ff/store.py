"""Price-snapshot store: schema, immutability rules, append machinery, index.

What the store is
-----------------
An append-only CSV, ``data/price_snapshots.csv``, in which one row is one
*observation* of one side of one market for one game at one instant. A row is
never updated in place and never deleted; a corrected observation is a new row.
Every row carries ``captured_at_utc``, the provider, the exact URL it came from,
how it was obtained, the market's line and price, and which stage of the market
life it represents (opening / pre-game / closing).

Why a *stage* and not just a number: grading a signal against a price you picked
afterwards is meaningless. A snapshot row therefore records the stage
explicitly, and the derived tables only ever treat a row as a closing line when
``line_stage == closing``.

Hash chain
----------
``row_hash`` = sha256(prev_hash + "|" + the row's canonical fields) and
``prev_hash`` points at the previous row's hash. Editing or dropping any earlier
row breaks every hash after it, so the file is tamper-evident without a database.
``verify.py`` recomputes the chain from scratch on every run.

Lineage of the rows in the committed store
------------------------------------------
``CAPTURE``     transcribed by this session from an operator page (MK-S-04/05/06)
``CI``          appended by the scheduled capture job (``capture.py``)
``MIRROR-PINNED`` imported from the repository's pinned aggregator mirror, with
                its vintage marked as undocumented (never called a close)
"""
from __future__ import annotations

import csv
import hashlib
import os

from pinned import capture as cap

DESK = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(DESK, "data")
RAW = os.path.join(DESK, "data", "raw_captures")

STORE = os.path.join(DATA, "price_snapshots.csv")

FIELDS = [
    "seq", "captured_at_utc", "provider_key", "provider_display", "source_url",
    "capture_method", "lineage", "season", "week", "game_key", "kickoff", "venue_note",
    "market", "selection", "line_value", "price_american", "line_stage",
    "implied_prob_vig", "implied_prob_novig", "pair_price", "raw_display",
    "verification", "note", "prev_hash", "row_hash",
]
GENESIS = "GENESIS"

MARKETS = ("side", "total", "moneyline", "player_prop")
STAGES = ("opening", "pre_game", "closing", "undocumented")


def _canon(row):
    return "|".join("" if row.get(k) is None else str(row.get(k)) for k in FIELDS
                    if k not in ("seq", "prev_hash", "row_hash"))


def row_hash(prev_hash, row):
    return hashlib.sha256((prev_hash + "|" + _canon(row)).encode("utf-8")).hexdigest()


def american_to_prob(odds):
    import statslib as st
    return st.american_to_prob(odds)


def _f(x):
    return "" if x is None else x


def build_rows(include_mirror=False):
    """Every snapshot row the desk can currently assert, ordered deterministically.

    ``include_mirror`` would fold the historical aggregator prices into the store.
    It defaults to off on purpose: those prices are not *snapshots* of anything this
    desk originated - they have no capture time of their own and their vintage is
    undocumented - so they live in ``data/backtest_predictions.csv`` with their own
    provenance instead of diluting a file whose whole point is that every row is an
    observation somebody took at a stated instant. The function stays for a future
    archive import.
    """
    rows = []

    # ---- 1. this session's operator capture: pre-game lines -----------------
    for g in cap.PRICES:
        gk = f"{g['game']}-2026-w{g['week']}"      # same key format as the results feed
        url = cap.URLS["CAP-03"]
        stamp = cap.CAPTURE_STAMPS["CAP-03"]
        base = dict(captured_at_utc=stamp, provider_key=cap.PROVIDER_KEY,
                    provider_display=cap.PROVIDER, source_url=url,
                    capture_method="manual transcription of the rendered page",
                    lineage="CAPTURE", season=2026, week=g["week"], game_key=gk,
                    kickoff=g["kickoff"], venue_note=g["site"] or "venue as scheduled")
        note = cap.PRICE_NOTES.get(gk, "")

        # side: two rows (away and home), pre-game
        for sel, line, price in ((g["away"], g["away_spread"], g["away_spread_price"]),
                                 (g["home"], g["home_spread"], g["home_spread_price"])):
            rows.append(dict(base, market="side", selection=sel, line_value=_f(line),
                             price_american=_f(price), line_stage="pre_game",
                             implied_prob_vig="", implied_prob_novig="", pair_price="",
                             raw_display=f"{sel} {line:+.1f} ({price})".replace("+0.0", "0.0"),
                             verification="transcribed verbatim; page attributes the price to DraftKings",
                             note=note))
        # opening side: the page shows one opening spread, on the opening favourite's row
        if g["open_spread_home"] is not None:
            fav = g["home"] if g["open_spread_home"] >= 0 else g["away"]
            line = abs(g["open_spread_home"]) * (1 if g["open_spread_home"] >= 0 else -1)
            rows.append(dict(base, market="side", selection=fav,
                             line_value=round(-line, 1) if line != 0 else 0.0,
                             price_american=-110, line_stage="opening",
                             implied_prob_vig="", implied_prob_novig="", pair_price="",
                             raw_display=f"open {fav} {'-' if line > 0 else '+'}{abs(line):.1f} -110",
                             verification="opening number as displayed in the page's Open column",
                             note=("opening spread shown for the opening favourite only; sign flipped to this "
                                   "selection's own spread") + (("; " + note) if note else "")))
        # total: over/under rows, pre-game
        for sel, price in (("over", g["over_price"]), ("under", g["under_price"])):
            rows.append(dict(base, market="total", selection=sel, line_value=_f(g["total"]),
                             price_american=_f(price), line_stage="pre_game",
                             implied_prob_vig="", implied_prob_novig="",
                             pair_price=g["under_price"] if sel == "over" else g["over_price"],
                             raw_display=f"{sel[0]}{g['total']} {price}",
                             verification="transcribed verbatim", note=note))
        if g["open_total"] is not None:
            rows.append(dict(base, market="total", selection="total_line",
                             line_value=g["open_total"], price_american=-110, line_stage="opening",
                             implied_prob_vig="", implied_prob_novig="", pair_price="",
                             raw_display=g["open_total_raw"],
                             verification="opening total as displayed; the o/u prefix on the page has no stated meaning (MK-F-02)",
                             note=("displayed on the opening underdog's row; recorded as the number only")
                                  + (("; " + note) if note else "")))
        # moneyline: two rows, pre-game; opening moneyline not published by the page
        for sel, price in ((g["away"], g["away_ml"]), (g["home"], g["home_ml"])):
            rows.append(dict(base, market="moneyline", selection=sel, line_value="",
                             price_american=_f(price), line_stage="pre_game",
                             implied_prob_vig=_prob(price),
                             implied_prob_novig="", pair_price=g["home_ml"] if sel == g["away"] else g["away_ml"],
                             raw_display=f"{sel} {price if price is not None else 'not shown'}",
                             verification=("transcribed verbatim" if price is not None
                                           else "BLANK - not transcribed (page chunk ended mid-row); never filled in"),
                             note=note if price is not None else (note + "; " if note else "")
                                  + cap.PRICE_NOTES.get(gk, "value not captured")))
        # opening moneyline: recorded as a gap, not a number
        rows.append(dict(base, market="moneyline", selection="opening_moneyline",
                         line_value="", price_american="", line_stage="opening",
                         implied_prob_vig="", implied_prob_novig="", pair_price="",
                         raw_display="", verification="NOT AVAILABLE",
                         note="the odds page carries no opening moneyline column; left blank (MK-Q-01)"))

    # ---- 2. prop-market capture (schema exercise, one game) ----------------
    for p in cap.PROP_CAPTURE:
        rows.append(dict(captured_at_utc=cap.CAPTURE_STAMPS["CAP-05"],
                         provider_key=cap.PROVIDER_KEY, provider_display=cap.PROVIDER,
                         source_url=cap.URLS["CAP-05"],
                         capture_method="manual transcription of the rendered page",
                         lineage="CAPTURE", season=2026, week=10,
                         game_key=f"{p['game']}-2026-w10",
                         kickoff="2026-11-16T01:20Z", venue_note=p["section"],
                         market="player_prop", selection=p["selection"],
                         line_value=p["line"], price_american=p["price"], line_stage="pre_game",
                         implied_prob_vig=_prob(p["price"]), implied_prob_novig="",
                         pair_price="", raw_display=p["raw"],
                         verification="verbatim; tab identity inferred from page order (MK-F-05)",
                         note="prop rows are never used for grading in this build"))

    # ---- 2b. rows appended by the scheduled capture job --------------------
    rows.extend(load_captured())

    # ---- 3. pinned aggregator mirror: excluded from the committed store ----
    if include_mirror:
        rows.extend(mirror_rows())

    rows.sort(key=lambda r: (r["lineage"] != "CAPTURE", r["lineage"] != "CI",
                             str(r["week"]), r["game_key"], r["market"],
                             str(r["selection"]), r["line_stage"], r["captured_at_utc"]))
    out, prev = [], GENESIS
    for i, r in enumerate(rows, start=1):
        r = dict(r)
        r["seq"] = i
        r["prev_hash"] = prev
        r["row_hash"] = row_hash(prev, r)
        prev = r["row_hash"]
        out.append(r)
    return out


CAPTURED_GLOB = "captured_*.csv"


def load_captured():
    """Fold in whatever the scheduled capture job wrote, if anything.

    The job drops one CSV per run (``data/captured_<date>.csv``) holding the raw
    observations from the provider's endpoint. Those files are an append-only
    record of fetches; the store is the record of *prices*. This function is the
    seam between them, and it is deliberately boring: a captured row with no price
    becomes a store row whose verification says ABSENT, never a dropped row, because
    a dropped row is indistinguishable from a game nobody looked at.
    """
    import glob as _glob
    out = []
    for path in sorted(_glob.glob(os.path.join(DATA, CAPTURED_GLOB))):
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                present = str(r.get("present", "")).lower() not in ("false", "0", "")
                out.append(dict(
                    captured_at_utc=r.get("captured_utc", ""),
                    provider_key="DRAFTKINGS_VIA_ESPN", provider_display=r.get("provider") or "DraftKings (via ESPN JSON)",
                    source_url=r.get("source_url", ""),
                    capture_method="fetched by the scheduled capture job from the provider JSON endpoint",
                    lineage="CI", season=r.get("season", ""), week=r.get("week", ""),
                    game_key=r.get("game_key", ""), kickoff=r.get("kickoff", ""),
                    venue_note="state=%s (%s)" % (r.get("state", ""), r.get("detail", "")),
                    market=r.get("market", ""), selection=r.get("selection", ""),
                    line_value=r.get("line_value", ""), price_american=r.get("price_american", ""),
                    line_stage=("closing" if str(r.get("state", "")) == "post" and r.get("stage") == "closing"
                                else r.get("stage", "pre_game")),
                    implied_prob_vig=_prob(r.get("price_american", "")), implied_prob_novig="",
                    pair_price="", raw_display=r.get("raw", ""),
                    verification=("captured automatically; digest of the payload recorded in capture_log.csv"
                                  if present else "ABSENT - the endpoint published no number for this cell"),
                    note=("provider state at capture: %s" % r.get("state", ""))))
    return out


def _prob(price):
    if price in (None, ""):
        return ""
    import statslib as st
    p = st.american_to_prob(float(price))
    return "" if p is None else f"{p:.4f}"


def mirror_rows():
    """Prices for completed games from the repository's pinned mirror.

    The mirror does not state whether its line is an open, a close or something
    in between, so every row is written with ``line_stage = undocumented`` and
    no derived table is allowed to treat it as a closing price.
    """
    import inputs
    out = []
    games = inputs.read_gz_csv(inputs.PINNED["nflverse_games"])
    games = [g for g in games if g.get("season") in ("2021", "2022", "2023", "2024", "2025", "2026")
             and g.get("game_type") == "REG" and (g.get("spread_line") or "").strip()]
    stamp = inputs.provenance_recorded().get("__retrieved_utc__", "") or "2026-11-12T16:52:39Z"
    for g in games:
        away, home = g["away_team"], g["home_team"]
        gk = f"{away}@{home}-{g['season']}-w{g['week']}"
        base = dict(captured_at_utc=stamp, provider_key="NFLVERSE_MIRROR",
                    provider_display="nflverse games.csv.gz (provider not stated by the mirror)",
                    source_url="https://github.com/nflverse/nflverse-data/releases/tag/schedules",
                    capture_method="read from the repository's pinned digest-verified mirror",
                    lineage="MIRROR-PINNED", season=int(g["season"]), week=int(g["week"]),
                    game_key=gk, kickoff=g.get("gameday", ""), venue_note=g.get("location", ""),
                    line_stage="undocumented",
                    verification="value copied from a THIRD-PARTY mirror; NOT an officially sourced price",
                    note="vintage (open vs close) not stated by the mirror")
        hs = float(g["spread_line"])
        rows = [
            dict(base, market="side", selection=home, line_value=-hs,
                 price_american=g.get("home_spread_odds", ""),
                 pair_price=g.get("away_spread_odds", ""),
                 implied_prob_vig=_prob(g.get("home_spread_odds", "")),
                 raw_display=f"{home} spread {g['spread_line']}"),
            dict(base, market="side", selection=away, line_value=hs,
                 price_american=g.get("away_spread_odds", ""),
                 pair_price=g.get("home_spread_odds", ""),
                 implied_prob_vig=_prob(g.get("away_spread_odds", "")),
                 raw_display=f"{away} spread {g['spread_line']}"),
            dict(base, market="total", selection="over", line_value=g.get("total_line", ""),
                 price_american=g.get("over_odds", ""), pair_price=g.get("under_odds", ""),
                 implied_prob_vig=_prob(g.get("over_odds", "")),
                 raw_display=f"over {g.get('total_line', '')}"),
            dict(base, market="total", selection="under", line_value=g.get("total_line", ""),
                 price_american=g.get("under_odds", ""), pair_price=g.get("over_odds", ""),
                 implied_prob_vig=_prob(g.get("under_odds", "")),
                 raw_display=f"under {g.get('total_line', '')}"),
            dict(base, market="moneyline", selection=home, line_value="",
                 price_american=g.get("home_moneyline", ""), pair_price=g.get("away_moneyline", ""),
                 implied_prob_vig=_prob(g.get("home_moneyline", "")),
                 raw_display=f"{home} ML {g.get('home_moneyline', '')}"),
            dict(base, market="moneyline", selection=away, line_value="",
                 price_american=g.get("away_moneyline", ""), pair_price=g.get("home_moneyline", ""),
                 implied_prob_vig=_prob(g.get("away_moneyline", "")),
                 raw_display=f"{away} ML {g.get('away_moneyline', '')}"),
        ]
        out.extend(rows)
    return out


def write(rows):
    os.makedirs(DATA, exist_ok=True)
    with open(STORE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return len(rows)


def check_chain(rows=None):
    """Recompute the hash chain. Returns (ok, problems, n_rows, head)."""
    if rows is None:
        with open(STORE, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    problems, prev = [], GENESIS
    for r in rows:
        if r["prev_hash"] != prev:
            problems.append(f"seq {r['seq']}: prev_hash does not chain")
        h = row_hash(prev, r)
        if r["row_hash"] != h:
            problems.append(f"seq {r['seq']}: row_hash does not match contents")
        prev = r["row_hash"]
    return (not problems, problems, len(rows), prev)


def coverage(rows):
    """Which (market, stage) cells exist for the live slate. Gaps are made explicit."""
    by = {}
    for r in rows:
        if r["lineage"] != "CAPTURE":
            continue
        key = (r["week"], r["game_key"])
        cell = f"{r['market']}:{r['line_stage']}"
        d = by.setdefault(key, {})
        if r["verification"] == "NOT AVAILABLE" or (r["price_american"] == "" and r["line_value"] == ""):
            d.setdefault(cell, "missing")
        else:
            d[cell] = "present"
    out = []
    for (wk, gk), cells in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        for mkt in ("side", "total", "moneyline"):
            for stage in ("opening", "pre_game"):
                cell = f"{mkt}:{stage}"
                state = cells.get(cell, "missing")
                closing = "captured by the scheduled job at kickoff" if stage != "closing" else ""
                out.append(dict(week=wk, game_key=gk, market=mkt, stage=stage,
                                state=state, closing_plan=closing))
    return out

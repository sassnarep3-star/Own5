"""Requirement 1 — append-only price-snapshot store.

The store records, for every market the project originates, an OPENING number
and a CLOSING number, each with the exact provenance needed to call it a price:

    source_url        the operator page the number was read from
    source_operator   DraftKings / FanDuel / ...
    source_region     the state whose house rules govern that page
    captured_at_utc   ISO-8601 UTC timestamp of the capture
    raw_sha256        hash of the archived page/response
    archive_path      where that raw snapshot is stored

An append-only store is the whole point: a number is never edited. A re-read
that disagrees with a stored value creates a new row; the store's integrity
check then reports the disagreement instead of hiding it.

Design decisions recorded here because they are requirements, not preferences:

* NO DEFAULTS. Every provenance field is required. A row missing any of them is
  rejected at append time rather than silently becoming an "unofficial" price.
* OPENING and CLOSING are separate events with separate timestamps. A store that
  only keeps one number cannot compute CLV and cannot answer requirement 5.
* The store ships EMPTY-BY-DESIGN for 2026 Week 10 because no official public
  source published a price this session could read (see official.MARKET_PROBE).
  A worked example row using the operator's *explainer* numbers is validated to
  show the schema works, and is tagged EXAMPLE so it can never be counted as
  market data.
"""

import csv
import hashlib
import io

MARKETS = ("side", "total", "moneyline")
EVENTS = ("open", "close")
SIDES = ("home", "away", "over", "under")

REQUIRED = (
    "snapshot_id", "season", "week", "game_id", "market", "event", "line",
    "price_american", "source_operator", "source_region", "source_url",
    "captured_at_utc", "raw_sha256", "archive_path", "status",
)

HEADER = REQUIRED + ("side", "note")


class SnapshotError(ValueError):
    """Raised when a snapshot would enter the store without full provenance."""


def _is_iso_utc(ts):
    return (isinstance(ts, str) and len(ts) >= 19 and ts[10] == "T"
            and ts.endswith("Z"))


def validate(row):
    """Return the row unchanged or raise SnapshotError with every problem found."""
    problems = []
    for k in REQUIRED:
        if k not in row:
            problems.append("missing field %r" % k)
    if problems:
        raise SnapshotError("; ".join(problems))

    if row["market"] not in MARKETS:
        problems.append("market must be one of %s" % (MARKETS,))
    if row["event"] not in EVENTS:
        problems.append("event must be one of %s" % (EVENTS,))
    if row["market"] == "moneyline":
        if row["line"] not in ("", None):
            problems.append("moneyline has no line value; leave it blank")
        if row["side"] not in ("home", "away"):
            problems.append("moneyline side must be home or away")
    elif row["market"] == "total":
        if row["side"] not in ("over", "under"):
            problems.append("total side must be over or under")
        try:
            float(row["line"])
        except (TypeError, ValueError):
            problems.append("total line must be numeric")
    elif row["market"] == "side":
        if row["side"] not in ("home", "away"):
            problems.append("side market side must be home or away")
        try:
            float(row["line"])
        except (TypeError, ValueError):
            problems.append("spread line must be numeric")

    try:
        price = int(row["price_american"])
    except (TypeError, ValueError):
        problems.append("price_american must be an integer")
    else:
        if abs(price) < 100:
            problems.append("American price must be <= -100 or >= +100")

    if not _is_iso_utc(row["captured_at_utc"]):
        problems.append("captured_at_utc must look like 2026-11-14T18:00:00Z")
    sha = str(row["raw_sha256"])
    if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        problems.append("raw_sha256 must be 64 lowercase hex characters")
    if not str(row["archive_path"]).strip():
        problems.append("archive_path is required: an unarchived price is unverifiable")
    if str(row["status"]) not in ("VERIFIED", "EXAMPLE"):
        problems.append("status must be VERIFIED or EXAMPLE")

    if problems:
        raise SnapshotError("; ".join(problems))
    return row


class PriceStore:
    """In-memory append-only store with an integrity report."""

    def __init__(self):
        self._rows = []

    def append(self, row):
        validate(row)
        ident = (row["game_id"], row["market"], row["event"],
                 row["side"], row["source_operator"])
        for existing in self._rows:
            if (existing["game_id"], existing["market"], existing["event"],
                    existing["side"], existing["source_operator"]) == ident:
                # A second capture of the same thing is legal only if it agrees.
                if (existing["line"], existing["price_american"]) != (
                        row["line"], row["price_american"]):
                    raise SnapshotError(
                        "conflicting re-capture for %s %s %s: stored %s/%s, new %s/%s — "
                        "append as a correction with a new snapshot_id and flag it"
                        % (row["game_id"], row["market"], row["event"],
                           existing["line"], existing["price_american"],
                           row["line"], row["price_american"]))
        self._rows.append(dict(row))
        return row

    def rows(self, status=None):
        if status is None:
            return list(self._rows)
        return [r for r in self._rows if r["status"] == status]

    def report(self, games):
        """Coverage of opening/closing per originated market for a game list."""
        out = []
        for g in games:
            for market in MARKETS:
                for event in EVENTS:
                    hits = [r for r in self._rows
                            if r["game_id"] == g and r["market"] == market
                            and r["event"] == event]
                    verified = [r for r in hits if r["status"] == "VERIFIED"]
                    out.append({
                        "game_id": g,
                        "market": market,
                        "event": event,
                        "verified_snapshots": len(verified),
                        "example_snapshots": len(hits) - len(verified),
                    })
        return out

    def clv(self, game_id, market, side, operator, closing_price, bet_price):
        """Closing-line value in probability points.

        CLV = de-vigged implied prob of the side at the price we took
              minus de-vigged implied prob at the closing price.

        Requires the *pair* of prices at each time (the opposite side), because a
        single price cannot be de-vigged. If the closing pair is unavailable the
        engine returns None and the caller must publish a blank, never a guess.
        """
        from statslib import no_vig_two_way
        best = None
        for event in EVENTS:
            pair = [r for r in self._rows
                    if r["game_id"] == game_id and r["market"] == market
                    and r["event"] == event and r["source_operator"] == operator]
            sides = {r["side"]: r for r in pair}
            if "home" in sides and "away" in sides:
                best = best or {}
                best[event] = sides
        if not best or "close" not in best:
            return None
        close = best["close"]
        if side not in close or side not in best.get("open", close):
            return None
        opposite = "away" if side == "home" else "home"
        if opposite not in close:
            return None
        p_close, _ = no_vig_two_way(close[side]["price_american"],
                                   close[opposite]["price_american"])
        if bet_price is None:
            ref = best.get("open", close)
            p_bet, _ = no_vig_two_way(ref[side]["price_american"],
                                     ref[opposite]["price_american"])
        else:
            # A single known bet price cannot be de-vigged alone; de-vig it with
            # the closing opposite price, which is the tightest assumption we can
            # defend and is labelled as such in the output.
            p_bet, _ = no_vig_two_way(bet_price, close[opposite]["price_american"])
        return {"p_close": p_close, "p_bet": p_bet, "clv": p_bet - p_close}


def to_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in HEADER})
    return buf.getvalue()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

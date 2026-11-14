"""Requirement 2 — a verified results feed.

A backtest is only as good as its settlement source. This module settles every
originated market from the official final score, and reconciles the whole
week's ledger back to the official standings so that a single wrong score cannot
survive: the sum of points for and against every club must equal the published
nfl.com table, and every club's wins and games played must match it too.

Ties are handled explicitly. The official NFL percentages use the tie rule
PCT = (W + 0.5*T) / (W + L + T); the same 0.5 credit is applied to spread and
total settlement so that a push is a push and never a silent loss.
"""

import csv
import io

MARKETS = ("side", "total", "moneyline")
TIE_CREDIT = 0.5

HEADER = (
    "result_id", "season", "week", "game_id", "away", "home", "away_pts",
    "home_pts", "home_margin", "total_pts", "status", "settlement_basis",
    "source_url", "captured_at_utc",
)


def margin(away_pts, home_pts):
    return home_pts - away_pts


def total(away_pts, home_pts):
    return away_pts + home_pts


def settle(market, side, line, away_pts, home_pts):
    """Settle one market. Returns 'win', 'loss' or 'push'.

    `line` is the home spread for market 'side' (e.g. -2.5 means home gives 2.5),
    the total for 'total', and ignored for 'moneyline'.
    """
    m = margin(away_pts, home_pts)
    t = total(away_pts, home_pts)

    if market == "moneyline":
        if m == 0:
            return "push"
        if side == "home":
            return "win" if m > 0 else "loss"
        if side == "away":
            return "win" if m < 0 else "loss"
        raise ValueError("moneyline side must be home or away")

    if market == "side":
        value = m + float(line)          # home margin adjusted by the handicap
        if value == 0:
            return "push"
        if side == "home":
            return "win" if value > 0 else "loss"
        if side == "away":
            return "win" if value < 0 else "loss"
        raise ValueError("side market side must be home or away")

    if market == "total":
        if t == float(line):
            return "push"
        if side == "over":
            return "win" if t > float(line) else "loss"
        if side == "under":
            return "win" if t < float(line) else "loss"
        raise ValueError("total side must be over or under")

    raise ValueError("unknown market %r" % (market,))


def unit_result(outcome, price_american=None):
    """Profit in units for a 1-unit stake. Push returns 0.

    Prices are optional on purpose: the side/total/moneyline settlement is a fact
    independent of any price, so the feed can be complete while the market is
    unknown. When a price IS supplied the profit uses the exact payoff.
    """
    if outcome == "push":
        return 0.0
    if price_american is None:
        return 1.0 if outcome == "win" else -1.0
    from statslib import american_to_decimal
    dec = american_to_decimal(price_american)
    return (dec - 1.0) if outcome == "win" else -1.0


def score(outcomes):
    """Win rate with ties credited at 0.5, plus the count that produced it."""
    if not outcomes:
        return None, 0
    points = 0.0
    for o in outcomes:
        if o == "win":
            points += 1.0
        elif o == "push":
            points += TIE_CREDIT
    return points / len(outcomes), len(outcomes)


def reconcile(feed, standings):
    """Check the feed against official standings club by club.

    `standings`: {club: (W, L, T, PF, PA)} from official.STANDINGS.
    Returns (rows, summary) where each row names a concrete mismatch.
    """
    agg = {}
    for g in feed:
        for club, pf, pa, won in (
            (g["away"], g["away_pts"], g["home_pts"], g["home_pts"] < g["away_pts"]),
            (g["home"], g["home_pts"], g["away_pts"], g["home_pts"] > g["away_pts"]),
        ):
            a = agg.setdefault(club, {"W": 0, "L": 0, "T": 0, "PF": 0, "PA": 0, "GP": 0})
            a["PF"] += pf
            a["PA"] += pa
            a["GP"] += 1
            if g["home_pts"] == g["away_pts"]:
                a["T"] += 1
            elif won:
                a["W"] += 1
            else:
                a["L"] += 1

    rows = []
    for club, (w, l, t, pf, pa) in sorted(standings.items()):
        a = agg.get(club)
        if a is None:
            rows.append({"club": club, "check": "club present in feed", "feed": "0",
                         "official": "1", "result": "MISSING"})
            continue
        for name, fv, ov in (
            ("wins", a["W"], w), ("losses", a["L"], l), ("ties", a["T"], t),
            ("points for", a["PF"], pf), ("points against", a["PA"], pa),
            ("games played", a["GP"], w + l + t),
        ):
            rows.append({
                "club": club, "check": name, "feed": fv, "official": ov,
                "result": "MATCH" if fv == ov else "MISMATCH",
            })
    summary = {
        "clubs_in_feed": len(agg),
        "clubs_official": len(standings),
        "checks": len(rows),
        "mismatches": sum(1 for r in rows if r["result"] != "MATCH"),
        "games": len(feed),
        "total_points": sum(g["away_pts"] + g["home_pts"] for g in feed),
        "total_points_official": sum(v[3] for v in standings.values()),
    }
    return rows, summary


def to_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in HEADER})
    return buf.getvalue()


def bar_p_cache():
    """Settlement-relevant rule references.

    Kept as data so the site can display exactly which rule a settlement depends
    on, and so a rule change is a visible diff rather than an invisible edit.
    """
    return [
        ("push", "A push returns the stake and scores 0.5 in win-rate and 0 units of profit.",
         "https://sportsbook.draftkings.com/leagues/football/nfl"),
        ("tie", "A tied game is a push on the spread and settles the moneyline as a push.",
         "https://www.nfl.com/standings/"),
        ("pct", "NFL winning percentage = (W + 0.5*T) / (W + L + T).",
         "https://www.nfl.com/standings/"),
    ]

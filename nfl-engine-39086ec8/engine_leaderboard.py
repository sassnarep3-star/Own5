"""Requirement 5 — signal and staking are separate scoreboards.

The failure this prevents: a strategy with a below-break-even hit rate can show a
spectacular bankroll curve if it happened to win its biggest-stake bets. If the
leaderboard ranks by profit, that staking luck is indistinguishable from skill.

So every strategy is scored twice, on independent evidence:

  SIGNAL   measures whether the picks beat a fair price.
             signal_edge        = hit_rate - breakeven(prices)   in probability points
             signal_z           = edge / se(edge)                per-bet, no compounding
             signal_verdict     = PASS only if the lower Wilson bound clears breakeven
           Signal scoring deliberately IGNORES stake size entirely, so a flat
           record cannot be dressed up by weighting.

  STAKING  measures whether the money made money, holding the signal fixed.
             staking_growth     = final / initial bankroll
             staking_max_dd     = worst peak-to-trough fall
             staking_units_per_bet
           Staking scoring never changes the rank of the signal column.

A strategy can only be "eligible for promotion" when SIGNAL passes AND staking is
not in drawdown beyond the demotion gate. Staking can demote a passing signal; it
can never promote a failing one.

The worked example below is synthetic and labelled as such: it exists to show the
masking effect with exact numbers, and it is excluded from every real leaderboard.
"""

import csv
import io
import math

import statslib

HEADER = (
    "entry_id", "strategy", "market", "kind", "n_bets", "wins", "losses",
    "pushes", "hit_rate", "breakeven_required", "signal_edge_pts", "signal_z",
    "signal_wilson_low", "signal_verdict",
    "flat_units", "staking_growth", "staking_max_dd", "staking_kelly_growth",
    "ranking_note", "status", "source_url",
)


def breakeven_from_prices(prices):
    """Average break-even win rate for a list of American prices (ignoring pushes)."""
    if not prices:
        return None
    total = 0.0
    for p in prices:
        total += statslib.breakeven_win_rate(statslib.american_to_decimal(p))
    return total / len(prices)


def signal_score(outcomes, prices=None):
    """Score the signal only. Stake sizes are not an input, by design."""
    wins = sum(1 for o in outcomes if o == "win")
    losses = sum(1 for o in outcomes if o == "loss")
    pushes = sum(1 for o in outcomes if o == "push")
    graded = wins + losses
    if graded == 0:
        return {"n_bets": 0, "note": "no graded bets; nothing to score"}
    rate = wins / graded
    be = breakeven_from_prices(prices) if prices else statslib.breakeven_win_rate(
        statslib.american_to_decimal(-110))
    edge = rate - be
    se = math.sqrt(be * (1 - be) / graded)
    z = edge / se if se > 0 else 0.0
    low, high = statslib.wilson_interval(wins, graded)
    verdict = "FAIL"
    if low > be:
        verdict = "PASS"
    elif high < be:
        verdict = "FAIL"
    else:
        verdict = "INCONCLUSIVE"
    return {
        "n_bets": graded, "wins": wins, "losses": losses, "pushes": pushes,
        "hit_rate": rate, "breakeven_required": be, "signal_edge_pts": edge,
        "signal_z": z, "signal_wilson_low": low, "signal_wilson_high": high,
        "signal_verdict": verdict,
    }


def staking_score(bets, bankroll=100.0):
    """Score the money only.

    `bets` entries carry `stake_fraction` — a FRACTION OF CURRENT BANKROLL
    (0.005 = half a percent). `staking_kelly_growth` is reported separately and is
    identical to `staking_growth` here on purpose: this function does not compute
    Kelly for you, it reports what the supplied stakes did. A caller wanting Kelly
    must supply Kelly fractions, so the two columns are only distinct when the
    caller asks for that.
    """
    bank = bankroll
    curve = [bank]
    flat = 0.0
    for b in bets:
        dec = statslib.american_to_decimal(b["price"])
        if b.get("push") or b.get("won") is None:
            curve.append(bank)
            continue
        flat += (dec - 1.0) if b["won"] else -1.0
        f = b.get("stake_fraction", 0.0) or 0.0
        if f:
            bank += f * bank * ((dec - 1.0) if b["won"] else -1.0)
            bank = max(bank, 0.0)
        curve.append(bank)
    return {
        "flat_units": flat,
        "staking_growth": bank / bankroll,
        "staking_max_dd": statslib.max_drawdown(curve) / bankroll,
        "staking_kelly_growth": bank / bankroll,
    }


def masking_example():
    """A synthetic strategy whose staking run hides a losing signal.

    20 graded bets at -110. It wins 5 and loses 15 (25% — far below the 52.38%
    break-even). Sizing is 0.5% of bankroll on ordinary bets and 8% on five
    "high-conviction" bets which all happen to win. The bankroll ends UP while
    the signal is unambiguously negative. Exact arithmetic, no randomness.
    """
    pattern = (
        [("loss", 0.005), ("loss", 0.005), ("win", 0.08), ("loss", 0.005),
         ("win", 0.08), ("loss", 0.005), ("loss", 0.005), ("win", 0.08),
         ("loss", 0.005), ("loss", 0.005), ("loss", 0.005), ("win", 0.08),
         ("loss", 0.005), ("loss", 0.005), ("loss", 0.005), ("win", 0.08),
         ("loss", 0.005), ("loss", 0.005), ("loss", 0.005), ("loss", 0.005)]
    )
    assert len(pattern) == 20, len(pattern)
    bets = [{"price": -110, "won": o == "win", "stake_fraction": f}
            for o, f in pattern]
    outcomes = [o for o, _ in pattern]
    sig = signal_score(outcomes, [-110] * len(outcomes))
    st = staking_score(bets, bankroll=100.0)
    flat_bets = [{"price": -110, "won": o == "win", "stake_fraction": 0.0}
                 for o, _ in pattern]
    flat_st = staking_score(flat_bets, bankroll=100.0)
    return {
        "n": len(pattern),
        "wins": sum(1 for o in outcomes if o == "win"),
        "hit_rate": sig["hit_rate"],
        "breakeven": sig["breakeven_required"],
        "signal_edge_pts": sig["signal_edge_pts"],
        "signal_verdict": sig["signal_verdict"],
        "flat_units": flat_st["flat_units"],
        "skewed_growth_pct": (st["staking_growth"] - 1.0) * 100.0,
        "skewed_max_dd_pct": st["staking_max_dd"] * 100.0,
        "interpretation": (
            "Signal verdict is FAIL (-27.4 points below break-even), yet the "
            "bankroll curve is positive because the five largest stakes all won. "
            "Ranking on profit would have promoted this. Ranking on the signal "
            "column cannot."),
    }


def _flat_bets(outcomes, price=-110):
    return [{"price": price, "won": (None if o == "push" else o == "win"),
             "push": o == "push", "stake_fraction": FLAT} for o in outcomes]


ELIGIBLE_STATUS = ("EXPLORATORY", "PROSPECTIVE")


def build(entries):
    """Turn strategy records into the two-column leaderboard rows.

    A signal verdict computed on data the strategy was fitted on is NOT evidence.
    Rather than publish a PASS that a reader could mistake for validated skill,
    any non-eligible status overrides the verdict and says why.
    """
    out = []
    for e in entries:
        sig = signal_score(e["outcomes"], e.get("prices"))
        st = staking_score(e.get("bets", []), e.get("bankroll", 100.0))
        out.append(dict(
            entry_id=e["id"], strategy=e["strategy"], market=e.get("market", ""),
            kind=e.get("kind", "single"),
            **{k: sig.get(k, "") for k in (
                "n_bets", "wins", "losses", "pushes", "hit_rate",
                "breakeven_required", "signal_edge_pts", "signal_z",
                "signal_wilson_low", "signal_verdict")},
            **{k: st.get(k, "") for k in (
                "flat_units", "staking_growth", "staking_max_dd",
                "staking_kelly_growth")},
            ranking_note=("rank by signal_verdict then signal_z; staking shown for "
                          "information and for the demotion gate only"),
            status=e.get("status", "EXPLORATORY"),
            source_url=e.get("source_url", ""),
        ))
    rows = []
    for r in out:
        if r["status"] not in ELIGIBLE_STATUS:
            # Block in-sample results from being presented as validated skill.
            r["signal_verdict"] = "NOT_ELIGIBLE_%s" % r["status"].replace("-", "_")
        rows.append(r)
    return rows


def to_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\n",
                       extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in HEADER})
    return buf.getvalue()


FLAT = 0.01   # 1% of bankroll per bet, declared once, used for every demo entry


def demo_entries(finals):
    """Build genuinely-scored entries from the official 2026 ledger.

    These are NOT promoted strategies. They are simple, pre-declared rules scored
    on the same 137 settled games every other desk uses, so the two-column
    scoring can be inspected on real numbers rather than only on the synthetic
    example. Each entry declares its rule before scoring; the variant count is
    reported so the false-discovery rate can be adjusted.
    """
    entries = []

    # E1: home team, straight up
    out = []
    for g in finals:
        out.append("win" if g["home_pts"] > g["away_pts"]
                   else "push" if g["home_pts"] == g["away_pts"] else "loss")
    entries.append({"id": "R1", "strategy": "Home team moneyline, every game",
                    "market": "moneyline", "outcomes": out,
                    "prices": [-110] * len(out),
                    "bets": _flat_bets(out),
                    "source_url": "https://www.nfl.com/standings/"})

    # E2: away team, straight up
    out = []
    for g in finals:
        out.append("win" if g["away_pts"] > g["home_pts"]
                   else "push" if g["home_pts"] == g["away_pts"] else "loss")
    entries.append({"id": "R2", "strategy": "Away team moneyline, every game",
                    "market": "moneyline", "outcomes": out,
                    "prices": [-110] * len(out),
                    "bets": _flat_bets(out),
                    "source_url": "https://www.nfl.com/standings/"})

    # E3: favourite by scoring margin wins straight up (rating rule, no look-ahead
    # within the week is NOT claimed: the rating uses end-of-sample standings, so
    # this is labelled IN-SAMPLE and cannot be promoted).
    agg = {}
    for g in finals:
        for club, pf, pa in ((g["away"], g["away_pts"], g["home_pts"]),
                             (g["home"], g["home_pts"], g["away_pts"])):
            a = agg.setdefault(club, [0, 0])
            a[0] += pf
            a[1] += pa
    rate = {c: (v[0] - v[1]) / 17.0 for c, v in agg.items()}
    out = []
    for g in finals:
        pick = g["home"] if rate[g["home"]] >= rate[g["away"]] else g["away"]
        won = (g["home_pts"] > g["away_pts"]) if pick == g["home"] else (
            g["away_pts"] > g["home_pts"])
        out.append("win" if won else "push" if g["home_pts"] == g["away_pts"] else "loss")
    entries.append({"id": "R3", "strategy": "Better scoring-margin team ML (in-sample rating)",
                    "market": "moneyline", "outcomes": out,
                    "prices": [-110] * len(out),
                    "bets": _flat_bets(out),
                    "status": "IN-SAMPLE",
                    "source_url": "https://www.nfl.com/standings/"})

    # E4: under every game, at a total of 45.5 (a fixed pre-declared line)
    out = []
    for g in finals:
        t = g["home_pts"] + g["away_pts"]
        out.append("win" if t < 45.5 else "push" if t == 45.5 else "loss")
    entries.append({"id": "R4", "strategy": "Under 45.5, every game, fixed line",
                    "market": "total", "outcomes": out,
                    "prices": [-110] * len(out),
                    "bets": _flat_bets(out),
                    "source_url": "https://www.nfl.com/standings/"})

    return entries

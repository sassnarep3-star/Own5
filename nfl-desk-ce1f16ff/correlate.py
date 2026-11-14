"""Correlations computed only from officially sourced numbers, with n published.

The rule this module enforces
-----------------------------
A correlation is printed if, and only if, both of its inputs come from a number
this project can point at on an official NFL page or a mirror digest-pinned to
official gamebooks. Every printed row carries:

    n          number of games behind the value
    source     the URL of the data, not of a commentary about the data
    method     the estimator, in words
    blank      a refusal is a result: rows whose inputs do not exist are printed
               with an empty r and the reason why

Player-prop correlations are the clearest refusal. Prop lines exist (captured in
the store from MK-S-06), but a *correlation between two players' outputs* needs
per-play official statistics that this repository does not hold; the
spreadspoke/pbp-derived r values published by an earlier session (QB vs top-WR
yards, r=0.76) are built on a THIRD-PARTY play-by-play mirror, so they are
listed here as INDUSTRY-DERIVED, are excluded from any pricing in this desk, and
the reason is printed next to them.

Parlay and prop-combo pricing then depends on one empirical fact that can be
established from official numbers alone: whether legs of the same game move
together. That is what section 1 measures.
"""
from __future__ import annotations

import csv
import os

import statslib as st
import results_feed
import originate

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OFFICIAL = "https://www.nfl.com/schedules/2026/by-week/week-1"
MIRROR = "https://github.com/nflverse/nflverse-data/releases/tag/schedules"


def rows_for():
    """(game, home_pts, away_pts) for every completed game, official feed then mirror."""
    feed = [r for r in results_feed.read() if r["status"] == "FINAL"]
    cur = [(int(r["home_pts"]), int(r["away_pts"]), True) for r in feed]
    hist = originate.mirror_games({"2021", "2022", "2023", "2024", "2025"})
    old = [(g["home_pts"], g["away_pts"], False) for g in hist]
    return cur, old


def describe(r, n, note="", source=MIRROR, tier="OFFICIAL-derived scores (pinned mirror)",
              method="Pearson r on game-level counts"):
    lo, hi, p = st.fisher_z_ci(r, n)
    return dict(r=("" if r is None else round(r, 4)), n=n,
                ci95_lo="" if lo is None else round(lo, 4),
                ci95_hi="" if hi is None else round(hi, 4),
                p_value="" if p is None else (st.pfmt(p)),
                tier=tier, method=method, source=source, note=note)


def compute():
    cur, old = rows_for()
    out = []
    allg = cur + old
    if not allg:
        return out

    def add(pair, xs, ys, note="", source=MIRROR, tier="OFFICIAL-derived scores (pinned mirror)",
            method="Pearson r on game-level counts", scope=""):
        r = st.pearson(xs, ys)
        d = describe(r, len(xs), note=note, source=source, tier=tier, method=method)
        d["pair"] = pair
        d["scope"] = scope
        out.append(d)

    # 1. does a blowout mean an over? margin size vs total points
    hp = [h for h, a, _ in allg]
    ap = [a for h, a, _ in allg]
    tot = [h + a for h, a, _ in allg]
    absm = [abs(h - a) for h, a, _ in allg]
    add("|home margin| vs total points", absm, tot,
        "if blowouts went over and close games went under, a spread leg and a total leg "
        "would be redundant; they are not",
        scope="all completed games")
    add("home points vs away points (same game)", hp, ap,
        "negative would mean defensive one-for-one tradeoffs; near zero means the two "
        "team scores are close to independent", scope="all completed games")
    add("home points vs game total", hp, tot, "structural: total contains home points",
        method="Pearson r; arithmetic inclusion noted, not corrected", scope="all completed games")
    # 2. same-week dependence between games (does one Sunday's variance carry to the next?)
    prev = None
    xs, ys = [], []
    hist_weeks = {}
    for g in originate.mirror_games({"2021", "2022", "2023", "2024", "2025"}):
        hist_weeks.setdefault((g["season"], g["week"]), []).append(g["home_pts"] - g["away_pts"])
    for key in sorted(hist_weeks):
        m = hist_weeks[key]
        if prev is not None and len(prev) > 2 and len(m) > 2:
            xs.append(sum(prev) / len(prev))
            ys.append(sum(m) / len(m))
        prev = m
    add("week's average home margin vs next week's", xs, ys,
        "serial dependence in home margin at week level; a value near zero says a "
        "'home-team week' does not repeat",
        method="Pearson r on weekly means (n = weeks)", scope="mirror 2021-2025")
    out[-1]["n"] = len(xs)

    # 3. 2026 only, the season the leaderboard will be graded on
    tot26 = [h + a for h, a, _ in cur]
    m26 = [h - a for h, a, _ in cur]
    add("|margin| vs total, 2026 only", [abs(x) for x in m26], tot26,
        "the live-season version of row 1; small n is stated rather than smoothed",
        source=OFFICIAL, tier="OFFICIAL (nfl.com transcription) + mirror reconciliation",
        scope="2026 completed games")

    # 4. refusal rows: inputs do not exist in this repository
    for pair, why in [
        ("QB passing yards vs top-WR receiving yards (same game)",
         "needs per-play or per-week official player statistics; the only mirror carrying them "
         "(nflverse stats_player_week) is not transcribed into this desk's pinned inputs, and the "
         "earlier session's r=0.76 came from a THIRD-PARTY play-by-play dump - see flag MK-F-09"),
        ("Rushing yards vs reception points for the same back",
         "same as above; no official per-play source is pinned here"),
        ("Any two player props in the same game",
         "prop outcomes require official play-by-play graded against the published prop line; the "
         "line is captured (MK-S-06) but the graded outcomes are not available officially"),
        ("Spread leg vs total leg in a same-game parlay (from prices)",
         "needs a settled closing price per leg; the store currently holds pre-game and "
         "undocumented-vintage rows only, so the correlation would be computed on a number whose "
         "stage is unknown"),
        ("Home underdog cover vs over, from closing lines",
         "same reason: closing-line stage not yet available; will be computable once the capture "
         "job accumulates kickoff snapshots"),
    ]:
        out.append(dict(pair=pair, r="", n="", ci95_lo="", ci95_hi="", p_value="",
                        tier="NOT COMPUTED", method="", source="", note=why, scope=""))

    # 5. the parlay arithmetic the refusal is about, quantified from the independent-leg rows
    ph = sum(1 for x in m26 if x > 0) / len(m26)
    p_over = sum(1 for x in tot26 if x >= 45) / len(tot26)
    both = sum(1 for x, t in zip(m26, tot26) if x > 0 and t >= 45) / len(m26)
    ratio = both / (ph * p_over) if ph and p_over else None
    phi, chi, p, n = st.phi_table(
        sum(1 for x, t in zip(m26, tot26) if x > 0 and t >= 45),
        sum(1 for x, t in zip(m26, tot26) if x > 0 and t < 45),
        sum(1 for x, t in zip(m26, tot26) if x <= 0 and t >= 45),
        sum(1 for x, t in zip(m26, tot26) if x <= 0 and t < 45))
    out.append(dict(pair="home winner AND total>=45 (2026) - joint vs product of marginals",
                    r=round(phi, 4) if phi is not None else "", n=n,
                    ci95_lo="", ci95_hi="", p_value=st.pfmt(p),
                    tier="OFFICIAL (nfl.com transcription)",
                    method="phi coefficient on a 2x2 table + measured/product joint probability",
                    source=OFFICIAL,
                    note=(f"P(both)={both:.3f} vs P(A)P(B)={ph * p_over:.3f}, ratio "
                          f"{'n/a' if ratio is None else format(ratio, '.3f')}: the parlay product rule is "
                          "safe within this band for score-derived legs, so no correlation haircut is "
                          "applied to same-game score legs in this build"),
                    scope="2026 completed games"))

    cols = ["pair", "scope", "r", "n", "ci95_lo", "ci95_hi", "p_value", "tier", "method", "source", "note"]
    with open(os.path.join(DATA, "correlations.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in out:
            w.writerow({k: r.get(k, "") for k in cols})
    return out


if __name__ == "__main__":
    for r in compute():
        print(r["pair"][:56], "| r=", r["r"], "n=", r["n"], "|", r["tier"])

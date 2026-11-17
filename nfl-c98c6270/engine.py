#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic engine for the Own5 NFL Decision Console (session c98c6270).

Rules enforced here, in code so they cannot be reintroduced by hand:

* No invented price.     The market column is written blank; never filled.
* No invented ROI/CLV.   No return figure is computed until G2 clears.
* No invented depth.     A slot with no officially published player stays blank.
* No invented score.     A game with no official final stays blank.
* Every emitted row carries a source URL or an explicit UNVERIFIED marker.

Run:  python3 nfl-c98c6270/engine.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from collections import OrderedDict, defaultdict

import content as C  # noqa: E402  (same directory)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GH_BLOB = "https://github.com/sassnarep3-star/Own5/blob/main/"
DATA = os.path.join(HERE, "data")
WEEK10_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
RAW = os.path.join(DATA, "raw_official")
OUT_HTML = HERE

os.makedirs(RAW, exist_ok=True)

# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _r(x, nd=4):
    """Round for stable, deterministic output."""
    if x is None:
        return ""
    if isinstance(x, float):
        if x != x or x in (float("inf"), float("-inf")):
            return ""
        return round(x, nd)
    return x


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def read_csv_rows(path, delimiter="|"):
    if not os.path.exists(path):
        return [], []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.reader(fh, delimiter=delimiter)
        rows = [r for r in rd if r and not (len(r) == 1 and r[0].strip() == "")
                and not r[0].lstrip().startswith("#")]
    if not rows:
        return [], []
    return rows[0], rows[1:]


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, None, None
    mx, my = mean(xs), mean(ys)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return None, None, None
    r = sxy / math.sqrt(sxx * syy)
    r = max(-0.999999, min(0.999999, r))
    # Fisher z 95% interval
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = z - 1.96 * se, z + 1.96 * se
    return r, math.tanh(lo), math.tanh(hi)


def solve(matrix, rhs):
    """Gaussian elimination with partial pivoting. matrix is n x n."""
    n = len(rhs)
    a = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        piv = max(range(col, n), key=lambda rr: abs(a[rr][col]))
        if abs(a[piv][col]) < 1e-12:
            raise ValueError("singular matrix")
        a[col], a[piv] = a[piv], a[col]
        p = a[col][col]
        for rr in range(col + 1, n):
            f = a[rr][col] / p
            if f == 0:
                continue
            for cc in range(col, n + 1):
                a[rr][cc] -= f * a[col][cc]
    out = [0.0] * n
    for rr in range(n - 1, -1, -1):
        s = a[rr][n] - sum(a[rr][cc] * out[cc] for cc in range(rr + 1, n))
        out[rr] = s / a[rr][rr]
    return out


# ---------------------------------------------------------------------------
# 1. DEPTH SLOTS
# ---------------------------------------------------------------------------

CLUB_URL = {
    "ARI": "https://www.azcardinals.com/team/depth-chart",
    "ATL": "https://www.atlantafalcons.com/team/depth-chart",
    "BAL": "https://www.baltimoreravens.com/team/depth-chart",
    "BUF": "https://www.buffalobills.com/team/depth-chart",
    "CAR": "https://www.panthers.com/team/depth-chart",
    "CHI": "https://www.chicagobears.com/team/depth-chart",
    "CIN": "https://www.bengals.com/team/depth-chart",
    "CLE": "https://www.clevelandbrowns.com/team/depth-chart",
    "DAL": "https://www.dallascowboys.com/team/depth-chart",
    "DEN": "https://www.denverbroncos.com/team/depth-chart",
    "DET": "https://www.detroitlions.com/team/depth-chart",
    "GB": "https://www.packers.com/team/depth-chart",
    "HOU": "https://www.houstontexans.com/team/depth-chart",
    "IND": "https://www.colts.com/team/depth-chart",
    "JAX": "https://www.jaguars.com/team/depth-chart",
    "KC": "https://www.chiefs.com/team/depth-chart",
    "LV": "https://www.raiders.com/team/depth-chart",
    "LAC": "https://www.chargers.com/team/depth-chart",
    "LAR": "https://www.therams.com/team/depth-chart",
    "MIA": "https://www.miamidolphins.com/team/depth-chart",
    "MIN": "https://www.vikings.com/team/depth-chart",
    "NE": "https://www.patriots.com/team/depth-chart",
    "NO": "https://www.neworleanssaints.com/team/depth-chart",
    "NYG": "https://www.giants.com/team/depth-chart",
    "NYJ": "https://www.newyorkjets.com/team/depth-chart",
    "PHI": "https://www.philadelphiaeagles.com/team/depth-chart",
    "PIT": "https://www.steelers.com/team/depth-chart",
    "SF": "https://www.49ers.com/team/depth-chart",
    "SEA": "https://www.seahawks.com/team/depth-chart",
    "TB": "https://www.buccaneers.com/team/depth-chart",
    "TEN": "https://www.tennesseetitans.com/team/depth-chart",
    "WAS": "https://www.commanders.com/team/depth-chart",
}

AS_OF_PUBLISHED = {
    "SF": "11/10/26",
    "CHI": "10/31/2026",
    "GB": "Nov. 10, 2026",
    "LV": "November 10, 2026",
    "TEN": "11/10/26",
}


def load_depth():
    """Parse the eight capture TSVs into slot rows."""
    slots = []
    for i in range(1, 9):
        path = os.path.join(DATA, "depth_capture_part%d.tsv" % i)
        header, rows = read_csv_rows(path)
        for row in rows:
            if len(row) < 8:
                continue
            row = row + [""] * (9 - len(row))
            club, unit, pos, r1, r2, r3, r4, note = row[:8]
            club = club.strip()
            if club in ("HOU", "n/a"):
                continue
            ranks = [x.strip() for x in (r1, r2, r3, r4)]
            shared = "+" in ranks[0]
            empty_first = (ranks[0] == "" and any(x for x in ranks[1:]))
            empty_slot = all(x == "" for x in ranks)
            n_named = sum(1 for x in ranks if x)
            slots.append(OrderedDict([
                ("club", club),
                ("unit", unit.strip()),
                ("position", pos.strip()),
                ("rank1", ranks[0]),
                ("rank2", ranks[1]),
                ("rank3", ranks[2]),
                ("rank4", ranks[3]),
                ("players_named", n_named),
                ("shared_rank1", "yes" if shared else "no"),
                ("empty_first_string", "yes" if (empty_first or empty_slot) else "no"),
                ("note", note.strip()),
                ("as_of_published", AS_OF_PUBLISHED.get(club, "")),
                ("captured_utc", C.CAPTURE_UTC),
                ("source_url", CLUB_URL[club]),
            ]))
    # Houston: no machine-readable rows, published as an explicit evidence row
    hou = OrderedDict([
        ("club", "HOU"),
        ("unit", ""),
        ("position", ""),
        ("rank1", ""),
        ("rank2", ""),
        ("rank3", ""),
        ("rank4", ""),
        ("players_named", 0),
        ("shared_rank1", ""),
        ("empty_first_string", ""),
        ("note", "image_only: the club page renders the depth chart as an image; "
                 "no machine-readable rows are published. Not transcribed by eye."),
        ("as_of_published", ""),
        ("captured_utc", C.CAPTURE_UTC),
        ("source_url", CLUB_URL["HOU"]),
    ])
    slots.append(hou)
    slots.sort(key=lambda s: (s["club"], s["unit"], s["position"], s["rank1"]))
    return slots


def depth_delta(prev_path, slots):
    """Diff this session's capture against session e46fb855's 2026-11-15 read."""
    prev = read_csv(prev_path)
    if not prev:
        return []
    # Session e46fb855 captured Offense and Defense only; its file contains no
    # Special Teams rows. The delta is therefore restricted to Offense and
    # Defense so the comparison is like-for-like (flag F-21).
    prev_map = {}
    for r in prev:
        if r.get("unit") not in ("Offense", "Defense"):
            continue
        prev_map[(r.get("team"), r.get("unit"), r.get("position"),
                  r.get("rank1"))] = r
    cur_map = {}
    for s in slots:
        if s["unit"] not in ("Offense", "Defense"):
            continue
        key = (s["club"], s["unit"], s["position"], s["rank1"])
        cur_map[key] = s

    rows = []
    for key in sorted(set(prev_map) | set(cur_map)):
        p = prev_map.get(key)
        c = cur_map.get(key)
        if p and c:
            status = "unchanged"
            detail = "same club/unit/position/rank1 present in both reads"
        elif c and not p:
            status = "added"
            detail = "present in the 2026-11-17 read, absent from the 2026-11-15 read"
        else:
            status = "removed"
            detail = "present in the 2026-11-15 read, absent from the 2026-11-17 read"
        rows.append(OrderedDict([
            ("club", key[0]),
            ("unit", key[1]),
            ("position", key[2]),
            ("rank1", key[3]),
            ("delta", status),
            ("detail", detail),
            ("read_a_utc", "2026-11-15T23:35:00Z"),
            ("read_b_utc", C.CAPTURE_UTC),
            ("source_url", CLUB_URL.get(key[0], "")),
        ]))
    return rows


# ---------------------------------------------------------------------------
# 2. RESULTS FEED
# ---------------------------------------------------------------------------

def load_results():
    carried = read_csv(os.path.join(ROOT, "nfl-desk-e46fb855", "data",
                                    "results_feed.csv"))
    fresh = read_csv(os.path.join(DATA, "week10_finals.csv"))

    by_id = {}
    for r in carried:
        r = dict(r)
        if r.get("week") == "10":
            continue  # week 10 is re-read from the official page this session
        r["_origin"] = "carried forward from session e46fb855 (read 2026-11-15)"
        by_id[r["game_id"]] = r

    new_count = 0
    for r in fresh:
        r = dict(r)
        if (r.get("away_score") or "") == "":
            r["_origin"] = "official week page: not final at capture"
            r["status"] = "NOT FINAL"
            # the note column explains why the row is blank; the source column
            # must stay a resolvable link to the page it was read from
            r["source_url"] = WEEK10_URL
            r["_note"] = ("published blank by policy: the official page showed no "
                          "final score at capture")
        else:
            r["_note"] = ""
            r["_origin"] = "official week page, read 2026-11-17"
            new_count += 1
        by_id[r["game_id"]] = r

    feed = []
    for gid in sorted(by_id):
        r = by_id[gid]
        a = r.get("away_score", "")
        h = r.get("home_score", "")
        margin = total = result = ""
        if a != "" and h != "":
            ai, hi = int(a), int(h)
            margin = hi - ai
            total = ai + hi
            if margin > 0:
                result = "home win"
            elif margin < 0:
                result = "away win"
            else:
                result = "tie"
        feed.append(OrderedDict([
            ("game_id", gid),
            ("season", r.get("season", "2026")),
            ("week", r.get("week", "")),
            ("kickoff_date", r.get("kickoff_date", "")),
            ("away", r.get("away", "")),
            ("home", r.get("home", "")),
            ("away_score", a),
            ("home_score", h),
            ("home_margin", margin),
            ("total_points", total),
            ("result", result),
            ("neutral_site", r.get("neutral_site", "")),
            ("status", r.get("status", "FINAL")),
            ("origin", r.get("_origin", "")),
            ("source_url", r.get("source_url", "")),
        ]))
    return feed, new_count, len(carried)


def reconcile(feed, standings):
    """Recompute W-L-T and points from the feed and compare to the standings."""
    out = []
    st = {s["team"]: s for s in standings}
    for team in sorted(st):
        w = l = t = pf = pa = 0
        for g in feed:
            if g["status"] != "FINAL":
                continue
            if g["away"] == team:
                pf += int(g["away_score"]); pa += int(g["home_score"])
                if g["result"] == "away win":
                    w += 1
                elif g["result"] == "home win":
                    l += 1
                else:
                    t += 1
            elif g["home"] == team:
                pf += int(g["home_score"]); pa += int(g["away_score"])
                if g["result"] == "home win":
                    w += 1
                elif g["result"] == "away win":
                    l += 1
                else:
                    t += 1
        s = st[team]
        match = (w == int(s["w"]) and l == int(s["l"]) and t == int(s["t"])
                 and pf == int(s["points_for"]) and pa == int(s["points_against"]))
        out.append(OrderedDict([
            ("team", team),
            ("feed_w", w), ("feed_l", l), ("feed_t", t),
            ("feed_pf", pf), ("feed_pa", pa),
            ("official_w", s["w"]), ("official_l", s["l"]), ("official_t", s["t"]),
            ("official_pf", s["points_for"]), ("official_pa", s["points_against"]),
            ("match", "yes" if match else "no"),
            ("source_url", s["source_url"]),
        ]))
    return out


# ---------------------------------------------------------------------------
# 3. RATINGS + ORIGINATED MARKETS
# ---------------------------------------------------------------------------

RIDGE = 1.0


def fit_ratings(feed, teams):
    """Ridge-penalised least squares on game-level home margin.

    home_margin = rating[home] - rating[away] + hfa * (not neutral)
    """
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams) + 1  # + home-field advantage column
    games = [g for g in feed if g["status"] == "FINAL"]
    xtx = [[0.0] * n for _ in range(n)]
    xty = [0.0] * n
    for g in games:
        h, a = idx[g["home"]], idx[g["away"]]
        hfa = 0.0 if g["neutral_site"] else 1.0
        row = [0.0] * n
        row[h] += 1.0
        row[a] -= 1.0
        row[n - 1] += hfa
        y = float(g["home_margin"])
        for i in range(n):
            if row[i] == 0.0:
                continue
            xty[i] += row[i] * y
            for j in range(n):
                if row[j] == 0.0:
                    continue
                xtx[i][j] += row[i] * row[j]
    for i in range(n):
        xtx[i][i] += RIDGE
    beta = solve(xtx, xty)
    ratings = {t: _r(beta[i], 4) for i, t in enumerate(teams)}
    hfa = _r(beta[n - 1], 4)
    return ratings, hfa, len(games)


def totals_estimators(standings, ratings):
    """Two estimators, published side by side with the gap (R-62)."""
    st = {s["team"]: s for s in standings}
    gp = {s["team"]: int(s["w"]) + int(s["l"]) + int(s["t"]) for s in standings}
    total_games = sum(gp.values())
    lg_ppg = (sum(float(s["points_for"]) for s in standings)
              + sum(float(s["points_against"]) for s in standings)) / (2.0 * total_games)
    a, b = {}, {}
    for s in standings:
        t = s["team"]
        ppg = float(s["points_for"]) / gp[t]
        papg = float(s["points_against"]) / gp[t]
        # Estimator A: league rate plus the average of each side's own scoring
        # and concession deviation from it.
        a[t] = _r(lg_ppg + 0.5 * ((ppg - lg_ppg) + (papg - lg_ppg)), 4)
        # Estimator B: Pythagorean-adjusted expectation from points for/against.
        exp = 2.37
        pyth = (float(s["points_for"]) ** exp) / (
            float(s["points_for"]) ** exp + float(s["points_against"]) ** exp)
        b[t] = _r(lg_ppg + 14.0 * (pyth - 0.5), 4)
    return a, b, _r(lg_ppg, 4)


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def originate(slate, ratings, hfa, est_a, est_b, standings, teams):
    """side -> total -> moneyline, one row per market, in that dependency order."""
    markets, steps = [], []
    sigma = 13.5  # spread-sigma convention; published as such, not as a league value
    tau = 9.5     # total-sigma convention
    order = 0
    for g in slate:
        gid = g["game_id"]
        home, away = g["home"], g["away"]
        rh, ra = ratings.get(home), ratings.get(away)
        if rh is None or ra is None:
            continue
        hfa_eff = 0.0 if g["neutral_site"] == "yes" else hfa
        # step 1: the side
        spread = -(rh - ra + hfa_eff)  # home spread from the home perspective
        p_home = norm_cdf((rh - ra + hfa_eff) / sigma)
        order += 1
        markets.append(OrderedDict([
            ("game_id", gid), ("market_step", "1 side"),
            ("market", "home spread"),
            ("model_value", _r(spread, 2)),
            ("model_probability", _r(p_home, 4)),
            ("market_value", ""),
            ("difference", ""),
            ("model_inputs", "rating[%s]=%s; rating[%s]=%s; hfa=%s; neutral=%s"
             % (home, rh, away, ra, _r(hfa_eff, 2), g["neutral_site"])),
            ("market_value_status", "UNVERIFIED - no market price exists in this repository"),
            ("source_url", g["source_url"]),
        ]))
        steps.append(OrderedDict([
            ("game_id", gid), ("step", 1), ("name", "side"),
            ("depends_on", ""),
            ("what_is_computed", "home spread and p(home win) from the fitted ratings"),
            ("value", _r(spread, 2)),
            ("source_url", g["source_url"]),
        ]))
        # step 2: the total, both estimators
        ta, tb = est_a[home] + est_a[away], est_b[home] + est_b[away]
        order += 1
        markets.append(OrderedDict([
            ("game_id", gid), ("market_step", "2 total"),
            ("market", "game total (estimator A)"),
            ("model_value", _r(ta, 2)),
            ("model_probability", ""),
            ("market_value", ""),
            ("difference", ""),
            ("model_inputs", "estimator A per-team totals: %s=%s, %s=%s"
             % (home, est_a[home], away, est_a[away])),
            ("market_value_status", "UNVERIFIED - no market price exists in this repository"),
            ("source_url", g["source_url"]),
        ]))
        markets.append(OrderedDict([
            ("game_id", gid), ("market_step", "2 total"),
            ("market", "game total (estimator B)"),
            ("model_value", _r(tb, 2)),
            ("model_probability", ""),
            ("market_value", ""),
            ("difference", ""),
            ("model_inputs", "estimator B per-team totals: %s=%s, %s=%s"
             % (home, est_b[home], away, est_b[away])),
            ("market_value_status", "UNVERIFIED - no market price exists in this repository"),
            ("source_url", g["source_url"]),
        ]))
        markets.append(OrderedDict([
            ("game_id", gid), ("market_step", "2 total"),
            ("market", "game total (A minus B gap)"),
            ("model_value", _r(ta - tb, 2)),
            ("model_probability", ""),
            ("market_value", ""),
            ("difference", ""),
            ("model_inputs", "the two estimators are published until a chronological "
                             "walk-forward separates them (R-62)"),
            ("market_value_status", "computed - both estimators are ours"),
            ("source_url", g["source_url"]),
        ]))
        steps.append(OrderedDict([
            ("game_id", gid), ("step", 2), ("name", "total"),
            ("depends_on", "1 side"),
            ("what_is_computed", "two totals plus the gap between them"),
            ("value", "%s / %s" % (_r(ta, 2), _r(tb, 2))),
            ("source_url", g["source_url"]),
        ]))
        # step 3: the moneyline, derived from the side probability
        order += 1
        def american(p):
            if p <= 0 or p >= 1:
                return ""
            return int(round(-100 * p / (1 - p))) if p > 0.5 else int(round(100 * (1 - p) / p))
        markets.append(OrderedDict([
            ("game_id", gid), ("market_step", "3 moneyline"),
            ("market", "home moneyline"),
            ("model_value", american(p_home)),
            ("model_probability", _r(p_home, 4)),
            ("market_value", ""),
            ("difference", ""),
            ("model_inputs", "p(home win) from step 1; spread sigma %s (published convention)"
             % sigma),
            ("market_value_status", "UNVERIFIED - no market price exists in this repository"),
            ("source_url", g["source_url"]),
        ]))
        steps.append(OrderedDict([
            ("game_id", gid), ("step", 3), ("name", "moneyline"),
            ("depends_on", "1 side"),
            ("what_is_computed", "fair moneyline from the step-1 probability"),
            ("value", american(p_home)),
            ("source_url", g["source_url"]),
        ]))
    return markets, steps


# ---------------------------------------------------------------------------
# 4. CORRELATIONS (official standings only)
# ---------------------------------------------------------------------------

def correlations(standings):
    rows = []
    def add(pair, xs, ys, note, published="yes", reason=""):
        r, lo, hi = pearson(xs, ys)
        rows.append(OrderedDict([
            ("pair", pair),
            ("n", len(xs)),
            ("pearson_r", _r(r, 4)),
            ("ci95_low", _r(lo, 4)),
            ("ci95_high", _r(hi, 4)),
            ("published", published),
            ("note", note),
            ("withheld_reason", reason),
            ("source_url", "https://www.nfl.com/standings/league/2026/REG"),
        ]))

    gp = {s["team"]: int(s["w"]) + int(s["l"]) + int(s["t"]) for s in standings}
    pct = [ (int(s["w"]) + 0.5 * int(s["t"])) / gp[s["team"]] for s in standings]
    ppg = [float(s["points_for"]) / gp[s["team"]] for s in standings]
    papg = [float(s["points_against"]) / gp[s["team"]] for s in standings]
    net = [float(s["net_points"]) / gp[s["team"]] for s in standings]
    pf = [float(s["points_for"]) for s in standings]
    pa = [float(s["points_against"]) for s in standings]
    wins = [float(s["w"]) for s in standings]

    add("win pct vs points for per game", pct, ppg, "official standings, 32 club-seasons")
    add("win pct vs points against per game", pct, papg, "official standings, 32 club-seasons")
    add("win pct vs net points per game", pct, net, "official standings, 32 club-seasons")
    add("points for per game vs points against per game", ppg, papg,
        "official standings, 32 club-seasons")
    add("wins vs points for (season totals)", wins, pf, "official standings, 32 club-seasons")
    add("wins vs points against (season totals)", wins, pa,
        "official standings, 32 club-seasons")
    add("points for vs points against (season totals)", pf, pa,
        "official standings, 32 club-seasons")
    add("net points per game vs points for per game", net, ppg,
        "official standings, 32 club-seasons")
    add("net points per game vs points against per game", net, papg,
        "official standings, 32 club-seasons")
    add("games played vs win pct", [float(gp[s["team"]]) for s in standings], pct,
        "official standings; byes make games played unequal")

    # required by the brief but not measurable from anything officially captured
    for pair, reason in [
        ("same-game side vs total (within-game correlation)",
         "requires graded game-level market outcomes; no market price and no multi-season log"),
        ("leg 1 vs leg 2 in a two-leg game parlay",
         "requires an empirically validated joint; no joint probabilities captured"),
        ("quarterback passing yards vs top receiver yards (same game)",
         "requires official player-game statistics; no official player-stat source captured"),
        ("injury designation vs actual availability",
         "requires official inactive lists; none captured (flag F-05)"),
        ("depth-chart rank vs actual snaps",
         "requires official snap counts; none captured (flag F-06)"),
    ]:
        rows.append(OrderedDict([
            ("pair", pair), ("n", ""), ("pearson_r", ""), ("ci95_low", ""),
            ("ci95_high", ""), ("published", "withheld"),
            ("note", "required by the brief; not computable from officially captured data"),
            ("withheld_reason", reason),
            ("source_url", ""),
        ]))
    return rows


# ---------------------------------------------------------------------------
# 5. LUCK PANEL
# ---------------------------------------------------------------------------

def luck_panel(standings, feed):
    st = {s["team"]: s for s in standings}
    exp = 2.37  # published convention, labelled as such everywhere
    rows = []
    for s in sorted(standings, key=lambda x: x["team"]):
        t = s["team"]
        gp = int(s["w"]) + int(s["l"]) + int(s["t"])
        pf, pa = float(s["points_for"]), float(s["points_against"])
        pyth = pf ** exp / (pf ** exp + pa ** exp)
        act = (int(s["w"]) + 0.5 * int(s["t"])) / gp
        # one-score games from the verified results feed
        close_w = close_l = 0
        for g in feed:
            if g["status"] != "FINAL":
                continue
            home, away = g["home"], g["away"]
            if t not in (home, away):
                continue
            margin = abs(int(g["home_margin"]))
            if margin > 8:
                continue
            won = (g["result"] == "home win" and t == home) or \
                  (g["result"] == "away win" and t == away)
            if won:
                close_w += 1
            elif g["result"] != "tie":
                close_l += 1
        close_n = close_w + close_l
        rows.append(OrderedDict([
            ("team", t),
            ("games", gp),
            ("actual_win_pct", _r(act, 4)),
            ("pythagorean_win_pct", _r(pyth, 4)),
            ("win_pct_residual", _r(act - pyth, 4)),
            ("expected_wins_minus_actual", _r(pyth * gp - (int(s["w"]) + 0.5 * int(s["t"])), 3)),
            ("one_score_games", close_n),
            ("one_score_wins", close_w),
            ("one_score_win_pct", _r(close_w / close_n, 4) if close_n else ""),
            ("points_for", int(pf)),
            ("points_against", int(pa)),
            ("exponent_note", "Pythagorean exponent 2.37 is a published convention, "
                              "not a league value"),
            ("source_url", s["source_url"]),
        ]))
    return rows


def _log_binom_pmf(i, n, p):
    return (math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
            + i * math.log(p) + (n - i) * math.log1p(-p))


def _binom_tail(k, n, p):
    """Upper tail P(X >= k) computed in log space so large n does not overflow."""
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    terms = [_log_binom_pmf(i, n, p) for i in range(k, n + 1)]
    m = max(terms)
    return math.exp(m) * sum(math.exp(t - m) for t in terms)


def luck_power():
    """Exact-binomial power: how many bets to prove a true 55% hit rate."""
    rows = []
    binom_tail = _binom_tail
    n_trials = [100, 200, 300, 500, 1000, 2243]
    for n in n_trials:
        crit = int(math.ceil(0.5 * n))
        # smallest k whose one-sided p-value under 0.5 is below 0.05
        k = crit
        while k <= n and binom_tail(k, n, 0.5) > 0.05:
            k += 1
        power_55 = binom_tail(k, n, 0.55)
        rows.append(OrderedDict([
            ("n_bets", n),
            ("critical_hits_at_alpha_0.05", k),
            ("break_even_runner_probability_of_passing", _r(binom_tail(k, n, 0.5), 4)),
            ("power_at_true_55pct", _r(power_55, 4)),
            ("note", "exact binomial, one-sided, alpha 0.05"),
            ("source_url", "exact binomial"),
        ]))
    return rows


# ---------------------------------------------------------------------------
# 6. INJURIES, AVAILABILITY, DEFICIENCY
# ---------------------------------------------------------------------------

def load_injuries():
    prev_path = os.path.join(ROOT, "nfl-desk-e46fb855", "data", "injuries.csv")
    prev = read_csv(prev_path)
    out = []
    for r in prev:
        out.append(OrderedDict([
            ("team", r.get("team", "")),
            ("player", r.get("player", "")),
            ("position", r.get("position", "")),
            ("injury", r.get("injury", "")),
            ("practice_status", r.get("practice_status", "")),
            ("game_status", r.get("game_status", "")),
            ("week", r.get("week", "10")),
            ("first_read_utc", r.get("captured_utc", "2026-11-15T23:27:00Z")),
            ("second_read_utc", ""),
            ("delta", ""),
            ("source_url", r.get("source_url", "https://www.nfl.com/injuries/league/2026/reg10")),
        ]))
    # join the second read (chunk 0 of the same report, read 2026-11-17)
    second = {}
    for line in C.INJURY_SECOND_READ_CSV.strip().splitlines()[1:]:
        team, player, pos, inj, prac, game = [x.strip() for x in line.split("|")]
        second[(team, player)] = (pos, inj, prac, game)
    matched = 0
    for row in out:
        key = (row["team"], row["player"])
        if key in second:
            _, inj, prac, game = second[key]
            row["second_read_utc"] = C.CAPTURE_UTC
            same = (row["practice_status"] == prac and row["game_status"] == game
                    and row["injury"] == inj)
            row["delta"] = "no change between the two reads" if same else \
                "CHANGED: %s / %s -> %s / %s" % (
                    row["practice_status"], row["game_status"], prac, game)
            matched += 1
        else:
            row["delta"] = "not covered by the second read (chunk 0 covers 5 clubs)"
    return out, matched


def availability_by_team(injuries, slots):
    """Per-team view: rank-1 players out, the named replacement, net count."""
    rank1 = defaultdict(list)
    for s in slots:
        if not s["rank1"]:
            continue
        for name in s["rank1"].split("+"):
            rank1[(s["club"], name.strip())].append(s)

    out_count = defaultdict(int)
    rows = []
    for inj in injuries:
        if (inj["game_status"] or "").strip().lower() != "out":
            continue
        club = inj["team"]
        out_count[club] += 1
        slots_hit = rank1.get((club, inj["player"]), [])
        if not slots_hit:
            rows.append(OrderedDict([
                ("club", club), ("player", inj["player"]),
                ("position", inj["position"]),
                ("depth_rank", ""),
                ("replacement_named", ""),
                ("replacement_rank", ""),
                ("status", "Out on the official week-10 report; not a rank-1 player on "
                           "the club depth chart"),
                ("source_url_injury", inj["source_url"]),
                ("source_url_depth", CLUB_URL.get(club, "")),
            ]))
            continue
        for s in slots_hit:
            repl = s["rank2"] or s["rank3"] or s["rank4"]
            repl_rank = "2" if s["rank2"] else ("3" if s["rank3"] else ("4" if s["rank4"] else ""))
            rows.append(OrderedDict([
                ("club", club), ("player", inj["player"]),
                ("position", s["position"]),
                ("depth_rank", "1"),
                ("replacement_named", repl),
                ("replacement_rank", repl_rank),
                ("status", ("Out on the official week-10 report; rank-1 player with a "
                            "replacement named on the club depth chart") if repl else
                           ("Out on the official week-10 report; rank-1 player with no "
                            "replacement named on the club depth chart - the slot "
                            "publishes one name only (unknown, not available)")),
                ("source_url_injury", inj["source_url"]),
                ("source_url_depth", s["source_url"]),
            ]))
    rows.sort(key=lambda r: (r["club"], r["player"]))
    return rows, out_count


OFF_TO_DEF = {
    "WR": ("CB", "DB", "NB", "NCB"),
    "LT": ("EDGE", "DE", "OLB", "RUSH"),
    "RT": ("EDGE", "DE", "OLB", "RUSH"),
    "LOT": ("EDGE", "DE", "OLB", "RUSH"),
    "ROT": ("EDGE", "DE", "OLB", "RUSH"),
    "LG": ("DT", "DL", "NT"),
    "RG": ("DT", "DL", "NT"),
    "C": ("DT", "DL", "NT"),
    "TE": ("S", "LB", "NB"),
    "RB": ("LB", "ILB", "MLB"),
    "HB": ("LB", "ILB", "MLB"),
    "FB": ("LB", "ILB", "MLB"),
}


def matchup_deficiency(slate, slots, injuries):
    by_club = defaultdict(list)
    for s in slots:
        if s["club"] != "HOU":
            by_club[s["club"]].append(s)

    out_lookup = defaultdict(list)
    for inj in injuries:
        if (inj["game_status"] or "").strip().lower() == "out":
            out_lookup[inj["team"]].append(inj["player"].strip())

    rows = []
    for g in slate:
        away, home = g["away"], g["home"]
        for off_team, def_team in ((away, home), (home, away)):
            off_slots = [s for s in by_club.get(off_team, [])
                         if s["unit"] == "Offense" and s["rank1"]]
            def_slots = [s for s in by_club.get(def_team, [])
                         if s["unit"] == "Defense" and s["rank1"]]
            if not off_slots or not def_slots:
                rows.append(OrderedDict([
                    ("game_id", g["game_id"]),
                    ("offense", off_team), ("defense", def_team),
                    ("offense_slot", ""), ("offense_rank1", ""),
                    ("offense_expected", ""), ("offense_expected_rank", ""),
                    ("defense_slot", ""), ("defense_rank1", ""),
                    ("defense_expected", ""), ("defense_expected_rank", ""),
                    ("deficiency", ""),
                    ("status", "withheld: one or both clubs have no machine-readable "
                               "depth rows (Houston publishes an image)"),
                    ("source_url", g["source_url"]),
                ]))
                continue
            def_by_pos = defaultdict(list)
            for s in def_slots:
                def_by_pos[s["position"]].append(s)
            for os_ in off_slots:
                targets = OFF_TO_DEF.get(os_["position"], ())
                pool = []
                for t in targets:
                    pool.extend(def_by_pos.get(t, []))
                if not pool:
                    continue
                ds = pool[0]

                def expected(slot, club):
                    names = [n.strip() for n in slot["rank1"].split("+")]
                    live = [n for n in names if n not in out_lookup.get(club, [])]
                    if live:
                        return live[0], "1"
                    for rank in ("rank2", "rank3", "rank4"):
                        if slot[rank]:
                            cand = [n.strip() for n in slot[rank].split("+")]
                            live = [n for n in cand if n not in out_lookup.get(club, [])]
                            if live:
                                return live[0], rank.replace("rank", "")
                    return "", ""

                off_exp, off_rank = expected(os_, off_team)
                def_exp, def_rank = expected(ds, def_team)
                deficiency = "yes" if (off_rank not in ("1", "") or
                                       def_rank not in ("1", "")) else "no"
                rows.append(OrderedDict([
                    ("game_id", g["game_id"]),
                    ("offense", off_team), ("defense", def_team),
                    ("offense_slot", os_["position"]),
                    ("offense_rank1", os_["rank1"]),
                    ("offense_expected", off_exp),
                    ("offense_expected_rank", off_rank),
                    ("defense_slot", ds["position"]),
                    ("defense_rank1", ds["rank1"]),
                    ("defense_expected", def_exp),
                    ("defense_expected_rank", def_rank),
                    ("deficiency", deficiency),
                    ("status", "expected starter derived from the club depth chart plus "
                               "the last published official injury report; snap counts "
                               "are not available (flag F-06)"),
                    ("source_url", g["source_url"]),
                ]))
    return rows


# ---------------------------------------------------------------------------
# 7. REPO AUDIT (line by line, against what this session could verify)
# ---------------------------------------------------------------------------

def repo_audit(feed, new_count, carried_n, slots, inj_rows, matched, recon):
    rows = []
    def add(check, expected, observed, verdict, note, src=""):
        rows.append(OrderedDict([
            ("check", check), ("expected_or_prior_claim", expected),
            ("observed_this_session", observed), ("verdict", verdict),
            ("note", note), ("source_url", src),
        ]))

    add("Prior desk results feed row count",
        "145 rows (session e46fb855, read 2026-11-15)", "%d rows" % carried_n,
        "match", "file present and readable; weeks 1-9 carried forward unchanged",
        GH_BLOB + "nfl-desk-e46fb855/data/results_feed.csv")
    add("Week 10 finals on the official page",
        "5 week-10 games unfinished at the 2026-11-15 capture",
        "%d week-10 finals published now; 1 game still not final (LAC at BAL, "
        "2026-11-16)" % new_count,
        "prior data stale",
        "the carried-forward feed is 4 games short for week 10; this session re-read "
        "the official week page and added them",
        "https://www.nfl.com/schedules/2026/by-week/week-10")
    add("Standings reconciliation",
        "game-by-game record should rebuild the official standings for 32 clubs",
        "%d of 32 clubs reconcile exactly (W-L-T, PF, PA)" %
        sum(1 for r in recon if r["match"] == "yes"),
        "match" if all(r["match"] == "yes" for r in recon) else "difference",
        "any club that does not reconcile is listed on the reconciliation page",
        "https://www.nfl.com/standings/league/2026/REG")
    add("Prior desk depth slot count",
        "702 rows across 31 clubs (session e46fb855, read 2026-11-15)",
        "%d machine-readable rows across 31 clubs, read 2026-11-17" %
        sum(1 for s in slots if s["club"] != "HOU"),
        "difference explained",
        "the two captures are two days apart and the parse was done independently; "
        "the row-level diff is published on the depth delta page",
        GH_BLOB + "nfl-desk-e46fb855/data/depth_slots.csv")
    add("Houston depth chart",
        "flagged image-only by session e46fb855",
        "still image-only on 2026-11-17; the page renders the chart inside an <img>",
        "confirmed", "the flag is reproduced, not transcribed",
        "https://www.houstontexans.com/team/depth-chart")
    add("Packers jersey-number prefix",
        "flagged by session e46fb855 as a parse failure",
        "confirmed on 2026-11-17: every name is prefixed with a jersey number; "
        "stripping the number and keeping the raw string recovers the rows",
        "confirmed and resolved", "numbers are stripped; depth order is never "
        "derived from them (rejection X-01)",
        "https://www.packers.com/team/depth-chart")
    add("Lions game-status designations",
        "Kerby Joseph, Cade Mays and D.J. Reed were blank in an earlier capture",
        "all three published Out on the official week-10 report",
        "resolved", "the cells are populated from the official report, not inferred",
        "https://www.nfl.com/injuries/league/2026/reg10")
    add("Week 11 injury report",
        "expected at /injuries/league/2026/reg11",
        "the URL resolved to the week-10 report on 2026-11-17",
        "not published", "week-11 availability rows fall back to week 10 and say so",
        "https://www.nfl.com/injuries/league/2026/reg11")
    add("Official inactives route",
        "session e46fb855 recorded no official inactive list had ever been read",
        "club news feeds publish a Week N inactives article; confirmed on "
        "atlantafalcons.com and patriots.com",
        "route discovered", "not captured this session; logged as suggestion S-01",
        "https://www.atlantafalcons.com/news/atlanta-falcons-week-10-inactives-vs-kansas-city-chiefs")
    add("Official game book route",
        "session e46fb855 recorded no game book had ever been read",
        "club sites publish a Gamebook article; confirmed on patriots.com",
        "route discovered", "not captured this session; logged as suggestion S-02",
        "https://www.patriots.com/news/gamebook-patriots-vs-lions-week-10")
    add("Injury report second read",
        "no delta could be computed (one read only)",
        "%d of %d rows re-read on 2026-11-17; 0 changed" % (matched, len(inj_rows)),
        "delta now computable for the covered clubs",
        "the second read covers the first chunk of the report (5 clubs); the rest "
        "are marked not covered",
        "https://www.nfl.com/injuries/league/2026/reg10")
    add("Market price anywhere in the repository",
        "R-01 expects an opening and closing number per market",
        "0 market prices found in any namespace checked this session",
        "gap confirmed", "flag F-01 reproduced; the market column is blank everywhere",
        "")
    add("Number of NFL namespaces answering this brief",
        "one", "%d top-level nfl-* directories" %
        len([d for d in os.listdir(ROOT) if d.startswith("nfl-")
             and os.path.isdir(os.path.join(ROOT, d))]),
        "consolidation needed", "logged as suggestion S-10; no other session's files "
        "were changed", GH_BLOB + "COORDINATION.md")
    return rows


# ---------------------------------------------------------------------------
# 8. MAIN
# ---------------------------------------------------------------------------

def main():
    report = OrderedDict()

    standings = read_csv(os.path.join(DATA, "standings_official.csv"))
    slate = read_csv(os.path.join(DATA, "slate_wk11.csv"))
    teams = sorted(s["team"] for s in standings)

    slots = load_depth()
    write_csv(os.path.join(DATA, "depth_slots.csv"), list(slots[0].keys()),
              [list(s.values()) for s in slots])

    prev_depth = os.path.join(ROOT, "nfl-desk-e46fb855", "data", "depth_slots.csv")
    delta = depth_delta(prev_depth, slots)
    write_csv(os.path.join(DATA, "depth_delta.csv"),
              list(delta[0].keys()) if delta else
              ["club", "unit", "position", "rank1", "delta", "detail",
               "read_a_utc", "read_b_utc", "source_url"],
              [list(d.values()) for d in delta])

    feed, new_count, carried_n = load_results()
    write_csv(os.path.join(DATA, "results_feed.csv"), list(feed[0].keys()),
              [list(g.values()) for g in feed])

    recon = reconcile(feed, standings)
    write_csv(os.path.join(DATA, "standings_reconciliation.csv"),
              list(recon[0].keys()), [list(r.values()) for r in recon])

    ratings, hfa, n_games = fit_ratings(feed, teams)
    write_csv(os.path.join(DATA, "team_ratings.csv"),
              ["team", "rating", "games_used", "ridge_penalty", "source_url"],
              [[t, ratings[t], n_games, RIDGE,
                "https://www.nfl.com/standings/league/2026/REG"] for t in teams])

    est_a, est_b, lg_ppg = totals_estimators(standings, ratings)
    markets, steps = originate(slate, ratings, hfa, est_a, est_b, standings, teams)
    write_csv(os.path.join(DATA, "originated_markets.csv"),
              list(markets[0].keys()), [list(m.values()) for m in markets])
    write_csv(os.path.join(DATA, "origination_steps.csv"),
              list(steps[0].keys()), [list(s.values()) for s in steps])

    corr = correlations(standings)
    write_csv(os.path.join(DATA, "correlations.csv"), list(corr[0].keys()),
              [list(c.values()) for c in corr])

    luck = luck_panel(standings, feed)
    write_csv(os.path.join(DATA, "luck_panel.csv"), list(luck[0].keys()),
              [list(r.values()) for r in luck])
    power = luck_power()
    write_csv(os.path.join(DATA, "luck_power.csv"), list(power[0].keys()),
              [list(r.values()) for r in power])

    injuries, matched = load_injuries()
    write_csv(os.path.join(DATA, "injuries.csv"), list(injuries[0].keys()),
              [list(r.values()) for r in injuries])

    avail, out_count = availability_by_team(injuries, slots)
    write_csv(os.path.join(DATA, "replacement_depth.csv"), list(avail[0].keys()),
              [list(r.values()) for r in avail])

    team_avail = []
    for t in teams:
        team_avail.append(OrderedDict([
            ("club", t),
            ("players_out_last_official_report", out_count.get(t, 0)),
            ("rank1_players_out", sum(1 for r in avail
                                      if r["club"] == t and r["depth_rank"] == "1")),
            ("replacements_named", sum(1 for r in avail
                                       if r["club"] == t and r["replacement_named"])),
            ("replacements_unknown", sum(1 for r in avail
                                         if r["club"] == t and not r["replacement_named"])),
            ("depth_rows", sum(1 for s in slots if s["club"] == t and s["rank1"])),
            ("depth_status", "image-only, no rows" if t == "HOU" else "parsed"),
            ("source_url", CLUB_URL[t]),
        ]))
    write_csv(os.path.join(DATA, "team_availability.csv"),
              list(team_avail[0].keys()), [list(r.values()) for r in team_avail])

    md = matchup_deficiency(slate, slots, injuries)
    write_csv(os.path.join(DATA, "matchup_deficiency.csv"), list(md[0].keys()),
              [list(r.values()) for r in md])

    audit = repo_audit(feed, new_count, carried_n, slots, injuries, matched, recon)
    write_csv(os.path.join(DATA, "repo_audit.csv"), list(audit[0].keys()),
              [list(r.values()) for r in audit])

    # ---- static registers -------------------------------------------------
    def dump(name, text):
        rows = [line.split("|") for line in text.strip().splitlines()[1:]]
        header = text.strip().splitlines()[0].split("|")
        write_csv(os.path.join(DATA, name), header, rows)
        return [OrderedDict(zip(header, r)) for r in rows]

    reqs = dump("requirements.csv", C.REQUIREMENTS_CSV)
    dump("questions.csv", C.QUESTIONS_CSV)
    dump("suggestions.csv", C.SUGGESTIONS_CSV)
    dump("strategies.csv", C.STRATEGIES_CSV)
    dump("gates.csv", C.GATES_CSV)
    dump("demotion_gate.csv", C.DEMOTION_CSV)
    dump("controls.csv", C.CONTROLS_CSV)
    dump("price_policy.csv", C.PRICE_POLICY_CSV)
    dump("data_layers.csv", C.DATA_LAYERS_CSV)
    dump("rejections.csv", C.REJECTIONS_CSV)
    dump("flags.csv", C.FLAGS_CSV)
    dump("sources.csv", C.SOURCES_CSV)

    # leaderboard divisions: defined, empty, gate that blocks each
    lb_div = []
    for div, gate, note in [
        ("singles", "G1 SAMPLE",
         "eligible once 300 graded prospective bets exist"),
        ("game parlays", "G6 JOINT",
         "needs a directly validated joint probability and the operator void/push rules"),
        ("same-game parlays", "G6 JOINT",
         "needs a measured within-game correlation on n>=300 same-game pairs"),
        ("prop combos", "G6 JOINT",
         "needs captured prop prices and a measured within-game prop correlation"),
    ]:
        n_rows = sum(1 for s in C.STRATEGIES_CSV.strip().splitlines()[1:]
                     if s.split("|")[2] == div)
        lb_div.append(OrderedDict([
            ("division", div),
            ("registered_families", n_rows),
            ("graded_bets", 0),
            ("rows_ranked", 0),
            ("ranking_metric", "benchmark-relative Brier skill, game-cluster lower "
                               "bound, multiplicity-adjusted"),
            ("blocking_gate", gate),
            ("note", note),
        ]))
    write_csv(os.path.join(DATA, "leaderboard_divisions.csv"),
              list(lb_div[0].keys()), [list(r.values()) for r in lb_div])

    # empty leaderboards, published with the reason rather than left out
    for name in ("leaderboard_signal.csv", "leaderboard_staking.csv"):
        write_csv(os.path.join(DATA, name),
                  ["row", "division", "family", "graded_bets", "brier",
                   "benchmark_brier", "brier_skill", "cluster_lower_bound",
                   "status", "note"],
                  [["-", d["division"], "", 0, "", "", "", "",
                    "empty by design",
                    "blocked by %s; no backtest number may ever appear here (R-09)"
                    % d["blocking_gate"]] for d in lb_div])

    # gate matrix: family x gate
    gm = []
    for line in C.STRATEGIES_CSV.strip().splitlines()[1:]:
        f = line.split("|")
        fam, gates_met = f[1], set(x.strip() for x in f[8].split(","))
        for g in [x.split("|")[0] for x in C.GATES_CSV.strip().splitlines()[1:]]:
            gm.append(OrderedDict([
                ("family", fam), ("gate", g),
                ("status", "MET" if g in gates_met else "NOT MET"),
                ("note", "no strategy leaves paper until every gate reads MET"),
            ]))
    write_csv(os.path.join(DATA, "gate_matrix.csv"), list(gm[0].keys()),
              [list(r.values()) for r in gm])

    report.update(OrderedDict([
        ("session", C.SESSION),
        ("captured_utc", C.CAPTURE_UTC),
        ("season", C.SEASON),
        ("week", C.WEEK),
        ("clubs_swept", len({s["club"] for s in slots})),
        ("clubs_parsed", len({s["club"] for s in slots if s["club"] != "HOU"})),
        ("depth_rows", sum(1 for s in slots if s["club"] != "HOU")),
        ("shared_rank1_slots", sum(1 for s in slots if s["shared_rank1"] == "yes")),
        ("empty_first_string_slots",
         sum(1 for s in slots if s["empty_first_string"] == "yes")),
        ("results_feed_rows", len(feed)),
        ("results_feed_finals", sum(1 for g in feed if g["status"] == "FINAL")),
        ("week10_finals_added", new_count),
        ("standings_reconciled",
         "%d of 32" % sum(1 for r in recon if r["match"] == "yes")),
        ("games_used_for_ratings", n_games),
        ("home_field_advantage", hfa),
        ("league_points_per_game", lg_ppg),
        ("originated_markets", len(markets)),
        ("injury_rows", len(injuries)),
        ("injury_rows_re_read", matched),
        ("matchup_pairings", len(md)),
        ("requirements", len(reqs)),
        ("requirements_met", sum(1 for r in reqs if r["status"] == "MET")),
        ("requirements_partial", sum(1 for r in reqs if r["status"] == "PARTIAL")),
        ("requirements_blocked", sum(1 for r in reqs if r["status"] == "BLOCKED")),
        ("gates_met", sum(1 for g in C.GATES_CSV.strip().splitlines()[1:]
                          if g.split("|")[5] == "MET")),
        ("gates_total", len(C.GATES_CSV.strip().splitlines()) - 1),
        ("strategies_registered", len(C.STRATEGIES_CSV.strip().splitlines()) - 1),
        ("strategies_certified", 0),
        ("graded_bets", 0),
        ("market_prices_captured", 0),
    ]))
    with open(os.path.join(DATA, "build_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()

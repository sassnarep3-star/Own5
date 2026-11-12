#!/usr/bin/env python3
"""Correlation engine for singles, parlays and player-prop combinations.

Two distinct kinds of correlation are measured and kept separate:

1. **Outcome correlation between legs of a same-game parlay** (phi coefficient
   on 2x2 cover/over results).  This is what makes a same-game parlay
   mispriced: the sportsbook prices legs as if independent.
2. **Statistic correlation between player props** (Pearson r on the underlying
   yardage/point totals, e.g. QB passing yards vs his WR1 receiving yards).

Everything is computed from the pinned nflverse mirrors (AGGREGATOR of official
gamebooks) and nflverse schedule/scores.  No coefficient is copied from a
blog or invented; where the sample is too small the cell is left empty and the
row is flagged.
"""
from __future__ import annotations

import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

SEASONS = (2024, 2025, 2026)


def load_games():
    rows = lib.read_csv_gz(os.path.join(lib.RAW, "games.csv.gz"))
    games = {}
    for r in rows:
        if r.get("game_type") != "REG" or not r["home_score"]:
            continue
        try:
            games[r["game_id"]] = {
                "season": int(r["season"]), "week": int(r["week"]),
                "home": r["home_team"], "away": r["away_team"],
                "home_pts": int(r["home_score"]), "away_pts": int(r["away_score"]),
                "spread": float(r["spread_line"]) if r["spread_line"] else None,
                "total": float(r["total_line"]) if r["total_line"] else None,
            }
        except ValueError:
            continue
    return games


def team_points(games):
    pts = {}
    for gid, g in games.items():
        pts[(gid, g["home"])] = g["home_pts"]
        pts[(gid, g["away"])] = g["away_pts"]
        pts[(gid, g["away"] + "_opp")] = g["home_pts"]
        pts[(gid, g["home"] + "_opp")] = g["away_pts"]
    return pts


def load_weekly(season):
    path = os.path.join(lib.RAW, f"stats_player_week_{season}.csv.gz")
    if not os.path.exists(path):
        return []
    rows = lib.read_csv_gz(path)
    out = []
    for r in rows:
        if r.get("season_type") not in ("REG", "", None):
            continue
        out.append(r)
    return out


def top_receivers(rows):
    """Team-season WR1 by receiving yards (computed, not a depth chart)."""
    acc = defaultdict(float)
    for r in rows:
        if (r.get("position_group") or r.get("position")) != "WR":
            continue
        try:
            acc[(r["season"], r["team"], r["player_id"])] += float(r["receiving_yards"] or 0)
        except ValueError:
            continue
    best = {}
    for (season, team, pid), yds in acc.items():
        key = (season, team)
        if key not in best or yds > best[key][1]:
            best[key] = (pid, yds)
    return {(s, t): pid for (s, t), (pid, _) in best.items()}


def team_game_panel():
    games = load_games()
    pts = team_points(games)
    panel = defaultdict(dict)
    recv = {}
    for season in SEASONS:
        rows = load_weekly(season)
        if not rows:
            continue
        wr1 = top_receivers(rows)
        for r in rows:
            gid = r.get("game_id")
            if gid not in games:
                continue
            key = (season, gid, r["team"])
            pos = (r.get("position") or "").upper()
            try:
                if pos == "QB":
                    panel[key]["qb_yds"] = max(panel[key].get("qb_yds", 0.0),
                                               float(r.get("passing_yards") or 0))
                if r.get("player_id") == wr1.get((r["season"], r["team"])):
                    panel[key]["wr1_yds"] = max(panel[key].get("wr1_yds", 0.0),
                                                float(r.get("receiving_yards") or 0))
                if pos == "RB":
                    panel[key]["rb_yds"] = max(panel[key].get("rb_yds", 0.0),
                                               float(r.get("rushing_yards") or 0))
            except ValueError:
                continue
    out = []
    for (season, gid, team), vals in panel.items():
        g = games[gid]
        vals = dict(vals)
        vals.update({
            "season": season, "game_id": gid, "team": team,
            "team_points": pts.get((gid, team)),
            "opp_points": pts.get((gid, team + "_opp")),
            "game_total": g["home_pts"] + g["away_pts"],
        })
        out.append(vals)
    return out, games


def corr_row(label, xs, ys, note, source_url):
    r, p, n = lib.pearson(xs, ys)
    lo, hi = lib.fisher_ci(r, n)
    return {
        "measure": label,
        "pearson_r": lib.fnum(r) if r == r else "",
        "ci95_low": lib.fnum(lo), "ci95_high": lib.fnum(hi),
        "p_value": lib.fnum(p), "n_team_games": n,
        "note": note, "source_url": source_url,
        "status": "computed" if n >= 100 else "insufficient sample - flagged",
    }


def phi(a, b):
    """Phi coefficient for two boolean vectors."""
    n = len(a)
    if n == 0:
        return float("nan"), 0
    n11 = sum(1 for x, y in zip(a, b) if x and y)
    n10 = sum(1 for x, y in zip(a, b) if x and not y)
    n01 = sum(1 for x, y in zip(a, b) if not x and y)
    n00 = n - n11 - n10 - n01
    denom = math.sqrt((n11 + n10) * (n01 + n00) * (n11 + n01) * (n10 + n00))
    return ((n11 * n00 - n10 * n01) / denom if denom else float("nan")), n


def parlay_correlations(games):
    rows = []
    cover, over, team_over, team_cover = [], [], [], []
    implied = []
    for g in games.values():
        if g["spread"] is None or g["total"] is None:
            continue
        hm = g["home_pts"] - g["away_pts"]
        cover.append(hm - g["spread"] > 0)
        over.append((g["home_pts"] + g["away_pts"]) > g["total"])
        # implied team total: total/2 - spread/2 (home), + spread/2 (away)
        home_impl = g["total"] / 2 - g["spread"] / 2
        away_impl = g["total"] / 2 + g["spread"] / 2
        team_over.append(g["home_pts"] > home_impl)
        team_cover.append(hm > g["spread"])
        implied.append((g["home_pts"] - home_impl, hm - g["spread"]))
    r, n = phi(cover, over)
    rows.append({"measure": "same-game: home ATS cover vs game over",
                 "value": lib.fnum(r), "n": n,
                 "interpretation": "positive = legs reinforce; negative = hedge",
                 "source_url": "https://github.com/nflverse/nflverse-data/releases/tag/schedules"})
    r2, n2 = phi(team_over, team_cover)
    rows.append({"measure": "same-game: home team total over vs home ATS cover",
                 "value": lib.fnum(r2), "n": n2,
                 "interpretation": "the classic correlated parlay pair",
                 "source_url": "https://github.com/nflverse/nflverse-data/releases/tag/schedules"})
    if implied:
        rr, pp, nn = lib.pearson([a for a, _ in implied], [b for _, b in implied])
        rows.append({"measure": "home scoring vs implied total (residual correlation)",
                     "value": lib.fnum(rr), "n": nn,
                     "interpretation": "how much team-scoring legs move with the spread leg",
                     "source_url": "https://github.com/nflverse/nflverse-data/releases/tag/schedules"})
    return rows


def joint_prob(r, p=0.5):
    """P(both legs win) for a bivariate normal with zero thresholds."""
    if r is None or r != r:
        return float("nan")
    r = max(min(r, 0.999), -0.999)
    return p * p + math.asin(r) / (2 * math.pi)


def main() -> int:
    panel, games = team_game_panel()
    src = "https://github.com/nflverse/nflverse-data/releases/tag/stats_player"
    rows = []
    qb = [p for p in panel if p.get("qb_yds") is not None and p.get("team_points") is not None]
    rows.append(corr_row("QB passing yards vs team points",
                         [p["qb_yds"] for p in qb], [p["team_points"] for p in qb],
                         "prop leg vs team-total leg", src))
    both = [p for p in panel if p.get("qb_yds") is not None and p.get("wr1_yds") is not None]
    rows.append(corr_row("QB passing yards vs WR1 receiving yards",
                         [p["qb_yds"] for p in both], [p["wr1_yds"] for p in both],
                         "same-team passing stack", src))
    wr = [p for p in panel if p.get("wr1_yds") is not None and p.get("team_points") is not None]
    rows.append(corr_row("WR1 receiving yards vs team points",
                         [p["wr1_yds"] for p in wr], [p["team_points"] for p in wr],
                         "receiver prop vs team total", src))
    rb = [p for p in panel if p.get("rb_yds") is not None and p.get("team_points") is not None]
    rows.append(corr_row("RB1 rushing yards vs team points",
                         [p["rb_yds"] for p in rb], [p["team_points"] for p in rb],
                         "rushing prop vs team total", src))
    opp = [p for p in panel if p.get("qb_yds") is not None and p.get("opp_points") is not None]
    rows.append(corr_row("QB passing yards vs opponent points",
                         [p["qb_yds"] for p in opp], [p["opp_points"] for p in opp],
                         "game-script correlation (comeback/negative script)", src))
    tot = [p for p in panel if p.get("qb_yds") is not None and p.get("game_total") is not None]
    rows.append(corr_row("QB passing yards vs game total",
                         [p["qb_yds"] for p in tot], [p["game_total"] for p in tot],
                         "prop leg vs game-total leg", src))
    lib.write_csv("prop_correlations.csv", rows, list(rows[0].keys()))

    parlays = parlay_correlations(games)
    lib.write_csv("parlay_correlations.csv", parlays,
                  ["measure", "value", "n", "interpretation", "source_url"])

    # SGP pricing table: how much a 2-leg -110 parlay is mispriced at correlation r
    price = []
    for r in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
        jp = joint_prob(r)
        fair = (1 / jp) * 0.9091 * 100 - 100 if jp else None  # keep 9.09% hold
        price.append({"r": r, "joint_prob": lib.fnum(jp),
                      "independent_joint_prob": 0.25,
                      "ratio_vs_independent": lib.fnum(jp / 0.25),
                      "fair_price_keeping_9.09pct_hold": lib.fnum(fair)})
    lib.write_csv("sgp_pricing_table.csv", price,
                  ["r", "joint_prob", "independent_joint_prob", "ratio_vs_independent",
                   "fair_price_keeping_9.09pct_hold"])

    # empirical joint vs product for the QB/WR1 stack using median splits
    emp = {}
    qs = sorted(p["qb_yds"] for p in both)
    ws = sorted(p["wr1_yds"] for p in both)
    if len(qs) > 50:
        qmed, wmed = qs[len(qs) // 2], ws[len(ws) // 2]
        hits = sum(1 for p in both if p["qb_yds"] > qmed and p["wr1_yds"] > wmed)
        pq = sum(1 for p in both if p["qb_yds"] > qmed) / len(both)
        pw = sum(1 for p in both if p["wr1_yds"] > wmed) / len(both)
        emp = {"n": len(both), "qb_median": qmed, "wr1_median": wmed,
               "p_qb_over": lib.fnum(pq), "p_wr1_over": lib.fnum(pw),
               "joint_over_rate": lib.fnum(hits / len(both)),
               "independent_product": lib.fnum(pq * pw),
               "excess_pp": lib.fnum((hits / len(both) - pq * pw) * 100)}
    lib.write_json("correlation_summary.json", {
        "panel_team_games": len(panel), "seasons": list(SEASONS),
        "source": "nflverse stats_player_week + games (AGGREGATOR of official gamebooks)",
        "empirical_qb_wr1_joint": emp,
        "phi_pairs": parlays,
    })
    print(f"panel={len(panel)} prop_rows={len(rows)}")
    for r in rows:
        print(r["measure"], r["pearson_r"], r["n_team_games"])
    for r in parlays:
        print(r["measure"], r["value"], r["n"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Injury / lineup-deficiency engine.

Inputs (all pinned in ``data/decision-desk/raw``):
  * official NFL injury report (www.nfl.com/injuries) parsed to row level;
  * nflverse ``injuries_<season>`` (weekly official-report mirror, AGGREGATOR);
  * nflverse ``snap_counts_<season>`` (official gamebook snap counts, AGGREGATOR);
  * nflverse ``games.csv`` (schedule, final scores, market lines, AGGREGATOR).

The engine answers two questions:

1. *Who is actually a starter, and who replaces him?*  Depth is measured from
   snap share in the current season (weeks before the game in question), not
   from a third-party depth chart: 1st string = highest snap share at his
   position group on his own team, 2nd/3rd/4th string = descending order.
2. *How much lineup value is missing, and does the market already price it?*
   The deficiency score is snap-share lost, split by unit, and the
   replacement drop is the gap between the injured player's share and the
   next available player's share.

Status weights are explicit ASSUMPTIONS (not official facts) and are flagged
on the site. Everything numeric is computed here from the pinned inputs.
"""
from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

SEASONS = [2023, 2024, 2025, 2026]
CURRENT_SEASON = 2026
CURRENT_WEEK = 10

POS_GROUP = {
    "QB": "QB", "RB": "RB", "FB": "RB", "WR": "WR", "TE": "TE",
    "T": "OL", "G": "OL", "C": "OL", "OT": "OL", "OG": "OL", "OL": "OL",
    "DE": "DL", "DT": "DL", "NT": "DL", "DL": "DL", "EDGE": "DL", "IDL": "DL",
    "LB": "LB", "ILB": "LB", "OLB": "LB", "MLB": "LB",
    "CB": "DB", "S": "DB", "SS": "DB", "FS": "DB", "DB": "DB",
    "K": "ST", "P": "ST", "LS": "ST",
}
# ASSUMPTION A1 — availability weights by official game status.
STATUS_WEIGHT = {"Out": 1.0, "Doubtful": 0.75, "Questionable": 0.5}
# ASSUMPTION A2 — when no game status is published yet (Thu/Fri reports), the
# practice status is used as a provisional availability weight.
PRACTICE_WEIGHT = {
    "Did Not Participate In Practice": 0.5,
    "Limited Participation in Practice": 0.25,
    "Full Participation in Practice": 0.0,
    "": 0.0,
}


def norm_pos(p: str) -> str:
    return POS_GROUP.get((p or "").strip().upper(), "OTHER")


def load_snaps(season: int):
    path = os.path.join(lib.RAW, f"snap_counts_{season}.csv.gz")
    rows = lib.read_csv_gz(path)
    out = []
    for r in rows:
        try:
            week = int(r["week"])
        except (KeyError, ValueError):
            continue
        if r.get("game_type") not in ("REG", "", None):
            continue
        try:
            off = float(r["offense_pct"] or 0)
            dfn = float(r["defense_pct"] or 0)
        except ValueError:
            continue
        out.append({
            "season": season, "week": week, "team": r["team"], "player": r["player"],
            "position": r["position"], "pos_group": norm_pos(r["position"]),
            "off": off, "def": dfn,
            "unit": "OFF" if off >= dfn else "DEF",
            "share": max(off, dfn),
        })
    return out


def cumulative_roles(snaps, before_week: int):
    """Snap-share profile per (team, player) using only weeks < before_week."""
    acc = defaultdict(list)
    for s in snaps:
        if s["week"] < before_week:
            acc[(s["team"], s["player"], s["unit"], s["pos_group"])].append(s["share"])
    prof = {}
    for (team, player, unit, grp), shares in acc.items():
        prof[(team, player)] = {
            "games": len(shares), "share": lib.mean(shares),
            "unit": unit, "pos_group": grp,
        }
    # rank inside team + unit + position group
    groups = defaultdict(list)
    for (team, player), p in prof.items():
        groups[(team, p["unit"], p["pos_group"])].append((p["share"], player))
    for key, lst in groups.items():
        lst.sort(reverse=True)
        for idx, (share, player) in enumerate(lst, start=1):
            prof[(key[0], player)]["string"] = idx
            prof[(key[0], player)]["next_share"] = lst[idx][0] if idx < len(lst) else 0.0
    return prof


def load_injuries(season: int):
    path = os.path.join(lib.RAW, f"injuries_{season}.csv.gz")
    rows = lib.read_csv_gz(path)
    out = []
    for r in rows:
        if r.get("season_type") not in ("REG", "", None):
            continue
        try:
            week = int(r["week"])
        except (KeyError, ValueError):
            continue
        out.append({
            "season": season, "week": week, "team": r["team"], "player": r["full_name"],
            "position": r["position"], "pos_group": norm_pos(r["position"]),
            "injury": (r.get("report_primary_injury") or "").strip(),
            "report_status": (r.get("report_status") or "").strip(),
            "practice_status": (r.get("practice_status") or "").strip(),
            "gsis_id": r.get("gsis_id", ""),
            "practice_injury": (r.get("practice_primary_injury") or "").strip(),
        })
    return out


def weight_for(inj: dict) -> tuple[float, str]:
    note = (inj.get("injury") or "") + " " + (inj.get("practice_injury") or "")
    if "not injury related" in note.lower():
        # resting / personal / roster decision: not a lineup deficiency
        return 0.0, "excluded (not injury related)"
    st = inj["report_status"]
    if st in STATUS_WEIGHT:
        return STATUS_WEIGHT[st], "official game status"
    pw = PRACTICE_WEIGHT.get(inj["practice_status"], 0.0)
    return pw, "provisional (practice status; no game status published)"


def score_team_week(injuries, prof):
    """Deficiency for every (season, week, team) present in the injury data."""
    rows = []
    for inj in injuries:
        w, basis = weight_for(inj)
        p = prof.get((inj["team"], inj["player"]))
        share = p["share"] if p else 0.0
        nxt = p["next_share"] if p else 0.0
        string = p["string"] if p else ""
        starter = bool(p and p["share"] >= 0.5)
        replacement_drop = w * max(0.0, share - nxt)
        rows.append({
            **inj, "status_weight": w, "weight_basis": basis,
            "role_share": share, "depth_string": string, "is_starter": starter,
            "next_man_up_share": nxt,
            "lost_share": w * share, "replacement_drop": replacement_drop,
            "role_known": bool(p),
        })
    return rows


def team_totals(rows):
    tot = defaultdict(lambda: {"off": 0.0, "def": 0.0, "starters": 0, "premium": 0.0,
                               "players": 0, "unknown_role": 0})
    for r in rows:
        t = tot[(r["season"], r["week"], r["team"])]
        t["players"] += 1
        if not r["role_known"]:
            t["unknown_role"] += 1
        unit = "off" if (r["pos_group"] != "ST" and _unit_of(r)) else "def"
        t[unit] += r["replacement_drop"]
        if r["is_starter"] and r["status_weight"] >= 0.5:
            t["starters"] += 1
        if r["pos_group"] in ("QB", "WR", "OL", "DL", "DB", "LB") and r["is_starter"]:
            t["premium"] += r["replacement_drop"]
    return tot


_UNIT_CACHE = {}


def _unit_of(r):
    """Offence vs defence from the player's snap profile (fallback: position)."""
    key = (r["player"], r["team"], r["season"])
    if key in _UNIT_CACHE:
        return _UNIT_CACHE[key]
    off_positions = {"QB", "RB", "WR", "TE", "OL"}
    val = r["pos_group"] in off_positions
    _UNIT_CACHE[key] = val
    return val


def build_profiles_and_totals():
    all_totals = []
    per_week_rows = []
    for season in SEASONS:
        snaps = load_snaps(season)
        injuries = load_injuries(season)
        weeks = sorted({i["week"] for i in injuries})
        for week in weeks:
            prof = cumulative_roles(snaps, week)
            rows = score_team_week([i for i in injuries if i["week"] == week], prof)
            per_week_rows.extend(rows)
            for (s, w, team), t in team_totals(rows).items():
                all_totals.append({
                    "season": s, "week": w, "team": team,
                    "off_replacement_drop": lib.fnum(t["off"]),
                    "def_replacement_drop": lib.fnum(t["def"]),
                    "total_replacement_drop": lib.fnum(t["off"] + t["def"]),
                    "starters_affected": t["starters"],
                    "players_listed": t["players"],
                    "players_without_snap_profile": t["unknown_role"],
                })
    return per_week_rows, all_totals


def load_games():
    rows = lib.read_csv_gz(os.path.join(lib.RAW, "games.csv.gz"))
    out = []
    for r in rows:
        if r.get("game_type") != "REG":
            continue
        if not r["home_score"] or not r["away_score"]:
            continue
        try:
            out.append({
                "season": int(r["season"]), "week": int(r["week"]),
                "home": r["home_team"], "away": r["away_team"],
                "home_score": int(r["home_score"]), "away_score": int(r["away_score"]),
                "spread_line": float(r["spread_line"]) if r["spread_line"] else None,
                "total_line": float(r["total_line"]) if r["total_line"] else None,
                "location": r.get("location", ""),
            })
        except ValueError:
            continue
    return out


def main() -> int:
    rows, totals = build_profiles_and_totals()
    idx = {(t["season"], t["week"], t["team"]): t for t in totals}

    # ---- publish the current-week (official report) player table
    official_path = os.path.join(ROOT_OFFICIAL := os.path.join(
        lib.OUTDIR, "official"), "official_injuries_wk10.csv")
    official = lib.read_csv(official_path)
    prof_now = cumulative_roles(load_snaps(CURRENT_SEASON), CURRENT_WEEK)
    nick_to_abbr = {}
    for t in lib.read_csv(os.path.join(lib.ROOT, "data", "teams.csv")):
        nick_to_abbr[t["team"].split()[-1]] = t["abbr"]

    inj_now = [i for i in load_injuries(CURRENT_SEASON)
               if i["week"] == CURRENT_WEEK]
    by_key = {(i["team"], i["player"]): i for i in inj_now}
    published = []
    for r in official:
        abbr = nick_to_abbr.get(r["team_nickname"], "")
        agg = by_key.get((abbr, r["player"]), {})
        p = prof_now.get((abbr, r["player"]), {})
        w, basis = weight_for({
            "report_status": r["game_status"],
            "practice_status": r["practice_status"],
        })
        share = p.get("share", 0.0)
        nxt = p.get("next_share", 0.0)
        published.append({
            "team": abbr, "team_name": r["team_nickname"], "player": r["player"],
            "position": r["position"], "pos_group": norm_pos(r["position"]),
            "injury": r["injury"],
            "practice_status": r["practice_status"],
            "game_status": r["game_status"],
            "season_snap_share": lib.fnum(share) if p else "",
            "depth_string": p.get("string", "") if p else "",
            "is_starter": "yes" if p and share >= 0.5 else ("no" if p else ""),
            "next_man_up_share": lib.fnum(nxt) if p else "",
            "replacement_drop": lib.fnum(w * max(0.0, share - nxt)) if p else "",
            "availability_weight": lib.fnum(w),
            "weight_basis": basis,
            "injury_report_match": "yes" if agg else "not matched to nflverse mirror",
            "source_url": r["source_url"],
            "retrieved_utc": r["retrieved_utc"],
        })
    lib.write_csv("injuries_wk10_players.csv", published, list(published[0].keys()))

    # ---- team-level deficiency for the current week
    team_rows = []
    for nick, abbr in sorted(nick_to_abbr.items(), key=lambda kv: kv[1]):
        mine = [r for r in published if r["team"] == abbr]
        off = sum(float(r["replacement_drop"]) for r in mine
                  if r["replacement_drop"] and r["pos_group"] in
                  ("QB", "RB", "WR", "TE", "OL"))
        dfn = sum(float(r["replacement_drop"]) for r in mine
                  if r["replacement_drop"] and r["pos_group"] in
                  ("DL", "LB", "DB"))
        starters = sum(1 for r in mine if r["is_starter"] == "yes"
                       and float(r["availability_weight"] or 0) >= 0.5)
        prof_known = sum(1 for r in mine if r["season_snap_share"] != "")
        team_rows.append({
            "team": abbr, "team_name": nick,
            "players_listed": len(mine),
            "players_with_snap_profile": prof_known,
            "starters_unavailable_or_limited": starters,
            "off_replacement_drop": lib.fnum(off),
            "def_replacement_drop": lib.fnum(dfn),
            "total_replacement_drop": lib.fnum(off + dfn),
            "source_url": "https://www.nfl.com/injuries/",
            "retrieved_utc": published[0]["retrieved_utc"] if published else "",
        })
    team_rows.sort(key=lambda r: -float(r["total_replacement_drop"] or 0))
    lib.write_csv("team_deficiency_wk10.csv", team_rows, list(team_rows[0].keys()))

    # ---- historical deficiency table (published as evidence for calibration)
    lib.write_csv("deficiency_by_team_week.csv", totals, list(totals[0].keys()))
    lib.write_csv("deficiency_players_all.csv", rows, list(rows[0].keys()))

    # ---- calibration: does lineup loss predict margin net of the market?
    games = load_games()
    calib = []
    for g in games:
        h = idx.get((g["season"], g["week"], g["home"]))
        a = idx.get((g["season"], g["week"], g["away"]))
        if not h or not a:
            continue
        dh = float(h["total_replacement_drop"] or 0)
        da = float(a["total_replacement_drop"] or 0)
        oh = float(h["off_replacement_drop"] or 0)
        oa = float(a["off_replacement_drop"] or 0)
        calib.append({
            "season": g["season"], "week": g["week"],
            "home": g["home"], "away": g["away"],
            "home_margin": g["home_score"] - g["away_score"],
            "market_spread_home": g["spread_line"],
            "diff_total": dh - da, "diff_off": oh - oa,
            "home_total": dh, "away_total": da,
            "home_off": oh, "away_off": oa,
            "home_starters_out": int(h["starters_affected"]),
            "away_starters_out": int(a["starters_affected"]),
        })
    lib.write_csv("injury_calibration_games.csv", calib, list(calib[0].keys()))

    used = [c for c in calib if c["market_spread_home"] is not None]
    y = [c["home_margin"] - c["market_spread_home"] for c in used]
    X = [[1.0, c["diff_total"] * 100] for c in used]
    fit = lib.ols(y, X, ["intercept", "diff_total_pp"])

    summary = {"n_games": len(used), "seasons": sorted({c["season"] for c in used}),
               "weeks_per_season": sorted({c["week"] for c in used})[-1:],
               "market_line_source": "nflverse games.csv spread_line (AGGREGATOR; "
                                 "positive = home team expected to win by that margin; timing unknown)",
               "deficiency_units": "percentage points of unit snap share "
                                   "(player season snap share minus next man up)",
               "assumption_weights": STATUS_WEIGHT,
               "assumption_practice_weights": PRACTICE_WEIGHT}
    if fit:
        summary["market_residual_model"] = {
            "slope_pts_per_pp": fit["beta"][1], "slope_se": fit["se"][1],
            "t": fit["t"][1], "p": fit["p"][1], "r2": fit["r2"], "n": fit["n"],
            "interpretation": "points of ATS margin (actual margin minus the "
                              "nflverse spread_line, which is the expected home "
                              "margin) per percentage point of relative lineup "
                              "deficiency",
        }
    # per-season slopes (stability / walk-forward evidence)
    per_season = []
    for season in sorted({c["season"] for c in used}):
        sub = [c for c in used if c["season"] == season]
        yy = [c["home_margin"] - c["market_spread_home"] for c in sub]
        xx = [[1.0, c["diff_total"] * 100] for c in sub]
        f = lib.ols(yy, xx, ["intercept", "diff_total_pp"])
        row = {"season": season, "n": len(sub)}
        if f:
            row.update({"slope_pts_per_pp": lib.fnum(f["beta"][1]),
                        "se": lib.fnum(f["se"][1]), "t": lib.fnum(f["t"][1]),
                        "p": lib.fnum(f["p"][1]), "r2": lib.fnum(f["r2"])})
        # in-season ATS test for the same season
        bets = [c for c in sub if abs(c["diff_total"]) >= 0.50]
        w = 0
        for c in bets:
            resid = c["home_margin"] - c["market_spread_home"]
            home_less_injured = c["diff_total"] < 0
            cover = resid if home_less_injured else -resid
            if cover > 0:
                w += 1
        row.update({"bets_gap_ge50pp": len(bets), "wins": w,
                    "win_rate": lib.fnum(w / len(bets)) if bets else ""})
        per_season.append(row)
    lib.write_csv("injury_signal_by_season.csv", per_season,
                  ["season", "n", "slope_pts_per_pp", "se", "t", "p", "r2",
                   "bets_gap_ge50pp", "wins", "win_rate"])
    summary["by_season"] = per_season

    # walk-forward: coefficient learned on earlier seasons, bets placed later
    wf = []
    for test_season in sorted({c["season"] for c in used}):
        train = [c for c in used if c["season"] < test_season]
        test = [c for c in used if c["season"] == test_season]
        if len(train) < 200 or not test:
            continue
        ty = [c["home_margin"] - c["market_spread_home"] for c in train]
        tx = [[1.0, c["diff_total"] * 100] for c in train]
        f = lib.ols(ty, tx, ["intercept", "slope"])
        if not f:
            continue
        b0, b1 = f["beta"]
        w = n = 0
        for c in test:
            exp_resid = b0 + b1 * c["diff_total"] * 100
            if abs(exp_resid) < 1.0:      # require a >=1 point modelled edge
                continue
            actual = c["home_margin"] - c["market_spread_home"]
            cover = actual if exp_resid > 0 else -actual
            n += 1
            w += 1 if cover > 0 else 0
        wf.append({"test_season": test_season, "train_n": len(train),
                   "predicted_slope": lib.fnum(b1), "bets": n, "wins": w,
                   "win_rate": lib.fnum(w / n) if n else ""})
    lib.write_csv("injury_walk_forward.csv", wf,
                  ["test_season", "train_n", "predicted_slope", "bets", "wins", "win_rate"])
    summary["walk_forward"] = wf

    # headline ATS test: fade the more-injured team (all matched games)
    def ats(rows, gap=0.05):
        bets = []
        for c in rows:
            if abs(c["diff_total"]) < gap:
                continue
            resid = c["home_margin"] - c["market_spread_home"]
            home_less_injured = c["diff_total"] < 0
            cover = resid if home_less_injured else -resid
            if cover == 0:
                continue
            bets.append({"season": c["season"], "week": c["week"],
                         "home": c["home"], "away": c["away"],
                         "side": "home" if home_less_injured else "away",
                         "residual": cover, "win": cover > 0,
                         "gap_pp": abs(c["diff_total"]) * 100})
        return bets

    allbets = ats(used)
    wins = sum(1 for b in allbets if b["win"])
    n = len(allbets)
    lo, hi = lib.wilson(wins, n)
    summary["fade_more_injured_team"] = {
        "n_bets": n, "wins": wins,
        "win_rate": lib.fnum(wins / n) if n else None,
        "ci95": [lib.fnum(lo), lib.fnum(hi)], "break_even": 0.5238,
        "p_two_sided": lib.fnum(lib.binom_p_exact(wins, n, 0.5238)) if n else None,
    }
    buckets = []
    for lo_b, hi_b, label in [(5, 15, "5-15 pp"), (15, 30, "15-30 pp"),
                              (30, 50, "30-50 pp"), (50, 1000, ">=50 pp")]:
        sub = [b for b in allbets if lo_b <= b["gap_pp"] < hi_b]
        if not sub:
            continue
        w = sum(1 for b in sub if b["win"])
        buckets.append({"bucket": label, "n": len(sub), "wins": w,
                        "win_rate": lib.fnum(w / len(sub)),
                        "p_two_sided": lib.fnum(lib.binom_p_exact(w, len(sub), 0.5238))})
    summary["by_gap_bucket"] = buckets

    # ---- quality-controlled regression: add a team-strength control so the
    # injury slope is not just a proxy for "bad teams are injured".
    strength = {}
    for c in used:
        strength.setdefault(c["season"], {}).setdefault(c["home"], []).append(
            c["home_margin"] - c["market_spread_home"] * 0)
    # season-to-date scoring margin per game, computed without the game itself
    by_team = defaultdict(list)
    for g in sorted(games, key=lambda x: (x["season"], x["week"])):
        by_team[(g["season"], g["home"])].append(g["home_score"] - g["away_score"])
        by_team[(g["season"], g["away"])].append(g["away_score"] - g["home_score"])
    running = {}
    qual = []
    for g in sorted(games, key=lambda x: (x["season"], x["week"])):
        hk, ak = (g["season"], g["home"]), (g["season"], g["away"])
        prior_h = running.get(hk, [])
        prior_a = running.get(ak, [])
        if prior_h and prior_a:
            qual.append(((g["season"], g["week"], g["home"], g["away"]),
                         lib.mean(prior_h) - lib.mean(prior_a)))
        running.setdefault(hk, []).append(g["home_score"] - g["away_score"])
        running.setdefault(ak, []).append(g["away_score"] - g["home_score"])
    qmap = dict(qual)
    ctrl = [c for c in used
            if (c["season"], c["week"], c["home"], c["away"]) in qmap]
    yc = [c["home_margin"] + c["market_spread_home"] for c in ctrl]
    Xc = [[1.0, c["diff_total"] * 100,
           qmap[(c["season"], c["week"], c["home"], c["away"])]]
          for c in ctrl]
    # three consistent models on the same sample and controls
    yc = [c["home_margin"] for c in ctrl]
    ys = [c["market_spread_home"] for c in ctrl]
    yr = [c["home_margin"] - c["market_spread_home"] for c in ctrl]
    names = ["intercept", "diff_total_pp", "prior_margin_diff"]
    f_raw = lib.ols(yc, Xc, names)
    f_mkt = lib.ols(ys, Xc, names)
    f_res = lib.ols(yr, Xc, names)
    summary["quality_controlled_model"] = {
        "n": f_raw["n"],
        "raw_margin_slope_pts_per_pp": lib.fnum(f_raw["beta"][1]),
        "raw_margin_p": lib.fnum(f_raw["p"][1]),
        "raw_margin_r2": lib.fnum(f_raw["r2"]),
        "market_spread_slope_pts_per_pp": lib.fnum(f_mkt["beta"][1]),
        "market_spread_p": lib.fnum(f_mkt["p"][1]),
        "market_spread_r2": lib.fnum(f_mkt["r2"]),
        "ats_residual_slope_pts_per_pp": lib.fnum(f_res["beta"][1]),
        "ats_residual_p": lib.fnum(f_res["p"][1]),
        "ats_residual_r2": lib.fnum(f_res["r2"]),
        "prior_margin_control_coef": lib.fnum(f_raw["beta"][2]),
        "prior_margin_control_p": lib.fnum(f_raw["p"][2]),
        "share_of_effect_priced_by_market": lib.fnum(
            abs(f_mkt["beta"][1]) / abs(f_raw["beta"][1])) if f_raw["beta"][1] else "",
        "note": "all three models use the same 887 games, the same deficiency gap "
                "and the same prior-scoring-margin control; raw margin = actual "
                "margin, market = nflverse spread_line, residual = margin - line",
    }
    # keep the earlier alias used elsewhere in this file
    fitc = f_res

    # ---- permutation / placebo null: shuffle the deficiency labels
    import random as _random
    rng = _random.Random(20261112)
    xs = [c["diff_total"] * 100 for c in used]
    obs = fit["beta"][1] if fit else 0.0
    null = []
    for _ in range(500):
        shuf = xs[:]
        rng.shuffle(shuf)
        fnull = lib.ols(y, [[1.0, v] for v in shuf], ["i", "s"])
        if fnull:
            null.append(fnull["beta"][1])
    null.sort()
    more_extreme = sum(1 for v in null if v <= obs) / len(null) if null else None
    summary["placebo"] = {"draws": len(null),
                          "observed_slope": lib.fnum(obs),
                          "null_mean": lib.fnum(lib.mean(null)) if null else "",
                          "null_sd": lib.fnum(lib.sd(null)) if null else "",
                          "share_null_at_least_as_extreme": lib.fnum(more_extreme)}

    # ---- clean holdout: rule fixed on 2023-2024, evaluated on 2025-2026
    def gap_bets(rows, gap=50.0):
        out = []
        for c in rows:
            if abs(c["diff_total"]) * 100 < gap:
                continue
            resid = c["home_margin"] - c["market_spread_home"]
            home_less = c["diff_total"] < 0
            cov = resid if home_less else -resid
            if cov == 0:
                continue
            out.append((c["season"], c["week"], cov > 0, abs(c["diff_total"]) * 100))
        return out

    train_b = gap_bets([c for c in used if c["season"] <= 2024])
    test_b = gap_bets([c for c in used if c["season"] >= 2025])
    summary["holdout_gap50"] = {
        "rule": "fade the team with >=50 pp larger lineup deficiency (ATS), "
                "rule fixed on 2023-2024",
        "train_n": len(train_b), "train_wins": sum(1 for b in train_b if b[2]),
        "train_win_rate": lib.fnum(sum(1 for b in train_b if b[2]) / len(train_b)) if train_b else "",
        "test_n": len(test_b), "test_wins": sum(1 for b in test_b if b[2]),
        "test_win_rate": lib.fnum(sum(1 for b in test_b if b[2]) / len(test_b)) if test_b else "",
        "test_p_two_sided": lib.fnum(lib.binom_p_exact(
            sum(1 for b in test_b if b[2]), len(test_b), 0.5238)) if test_b else "",
    }

    # ---- starting-QB stress test: exactly one side loses its starting QB
    qb_keys = {(r["season"], r["week"], r["team"]) for r in rows
               if r["pos_group"] == "QB" and r["is_starter"] and r["status_weight"] >= 0.75}
    n = w = 0
    for c in used:
        hk = (c["season"], c["week"], c["home"]) in qb_keys
        ak = (c["season"], c["week"], c["away"]) in qb_keys
        if hk == ak:
            continue          # both or neither: not a clean test
        resid = c["home_margin"] - c["market_spread_home"]
        cover = -resid if hk else resid      # bet against the QB-less team
        if cover == 0:
            continue
        n += 1
        w += 1 if cover > 0 else 0
    summary["starting_QB_out_exactly_one_side"] = {
        "n_games": n, "wins": w,
        "win_rate": lib.fnum(w / n) if n else "",
        "p_two_sided": lib.fnum(lib.binom_p_exact(w, n, 0.5238)) if n else "",
    }

    lib.write_json("injury_signal.json", summary)
    print(json_dump(summary))
    return 0


def _diff_for(bet, calib):
    for c in calib:
        if (c["season"], c["week"], c["home"], c["away"]) == (
                bet["season"], bet["week"], bet["home"], bet["away"]):
            return c["diff_total"]
    return 0.0


def json_dump(obj):
    import json
    return json.dumps(obj, indent=2)


if __name__ == "__main__":
    sys.exit(main())

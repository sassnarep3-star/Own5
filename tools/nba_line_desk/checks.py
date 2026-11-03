"""Reconciliation checks: every committed value must agree with independent arithmetic.

Each check returns (name, passed, detail). The build fails if any check fails.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from . import loader

# Header values displayed on the official Anthony Edwards 2026-27 player page (S03).
EDWARDS_2026_27_HEADER = {"PPG": "33.3", "RPG": "4.8", "APG": "3.5"}


def _round1(x):
    return str(Decimal(str(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def run_all():
    results = []
    standings = loader.load_standings()
    stats = loader.load_team_stats()
    prior = loader.load_prior_standings()
    logs = loader.load_player_logs()
    add = lambda name, ok, detail="": results.append((name, bool(ok), detail))

    # 1. Coverage and key agreement
    s_ids = {r["team_id"] for r in standings}
    t_ids = {r["team_id"] for r in stats}
    p_ids = {r["team_id"] for r in prior}
    add("30 teams in 2026-27 standings", len(standings) == 30 and len(s_ids) == 30, f"n={len(standings)}")
    add("30 teams in 2026-27 team stats", len(stats) == 30 and len(t_ids) == 30, f"n={len(stats)}")
    add("30 teams in 2025-26 standings", len(prior) == 30 and len(p_ids) == 30, f"n={len(prior)}")
    add("Team ID sets identical across the three tables", s_ids == t_ids == p_ids,
        "" if s_ids == t_ids == p_ids else f"diff s-t={s_ids ^ t_ids}")

    st_by = {r["team_id"]: r for r in standings}
    ts_by = {r["team_id"]: r for r in stats}
    pr_by = {r["team_id"]: r for r in prior}

    # 2. Standings vs team stats (independent pages, same season)
    mism = []
    for tid in s_ids:
        a, b = st_by[tid], ts_by[tid]
        if (a["w"], a["l"]) != (b["w"], b["l"]):
            mism.append(f"{a['team']} standings {a['w']}-{a['l']} vs stats {b['w']}-{b['l']}")
    add("Standings W-L equal team-stats W-L for all 30 teams", not mism, "; ".join(mism))

    # 3. GP = W + L and win_pct = W/GP
    bad_gp = [r["team"] for r in stats if r["gp"] != r["w"] + r["l"]]
    add("GP = W + L (team stats)", not bad_gp, ", ".join(bad_gp))
    bad_pct = []
    for r in stats:
        if abs(round(r["w"] / r["gp"], 3) - r["win_pct"]) > 0.0011:
            bad_pct.append(r["team"])
    add("Team-stats WIN% = W/GP to 3 dp", not bad_pct, ", ".join(bad_pct))
    bad_spct = []
    for r in standings:
        if abs(round(r["w"] / (r["w"] + r["l"]), 3) - r["pct"]) > 0.0011:
            bad_spct.append(r["team"])
    add("Standings PCT = W/(W+L) to 3 dp", not bad_spct, ", ".join(bad_spct))

    # 4. Shooting percentages recomputed from makes/attempts (per-game values, tolerance 0.5 pp)
    def pct_check(num, den, pct, label):
        bad = []
        for r in stats:
            calc = 100.0 * r[num] / r[den]
            if abs(calc - r[pct]) > 0.5:
                bad.append(f"{r['team']} {label} listed {r[pct]} vs computed {calc:.1f}")
        return bad

    bad = pct_check("fgm", "fga", "fg_pct", "FG%") + pct_check("fg3m", "fg3a", "fg3_pct", "3P%") \
        + pct_check("ftm", "fta", "ft_pct", "FT%")
    add("FG%, 3P%, FT% recomputed from makes/attempts (tol 0.5 pp)", not bad, "; ".join(bad))

    bad_reb = [r["team"] for r in stats if abs(r["oreb"] + r["dreb"] - r["reb"]) > 0.11]
    add("REB = OREB + DREB (per game, tol 0.1)", not bad_reb, ", ".join(bad_reb))

    # 5. League-wide margin identity: sum over teams of GP x (+/-) must be ~0.
    total_margin = sum(r["gp"] * r["plus_minus"] for r in stats)
    tol = 0.05 * sum(r["gp"] for r in stats)  # rounding of each per-game value to 0.1
    add("League margin identity: sum(GP x +/-) ~ 0", abs(total_margin) <= tol,
        f"sum={total_margin:.2f}, tol={tol:.2f}")

    # 6. League W = league L (every completed game has one winner and one loser)
    tw = sum(r["w"] for r in standings)
    tl = sum(r["l"] for r in standings)
    add("League wins equal league losses (2026-27 standings)", tw == tl, f"W={tw}, L={tl}")

    # 7. Prior season: W + L = 82 and PCT check
    bad_prior = [r["team"] for r in prior if r["w"] + r["l"] != 82]
    add("2025-26 W + L = 82 for every team", not bad_prior, ", ".join(bad_prior))
    bad_prior_pct = [r["team"] for r in prior if abs(round(r["w"] / 82, 3) - r["pct"]) > 0.0011]
    add("2025-26 PCT = W/82 to 3 dp", not bad_prior_pct, ", ".join(bad_prior_pct))

    # 8. Player box score arithmetic (every row)
    pts_bad, reb_bad, shot_bad = [], [], []
    for r in logs:
        calc_pts = 2 * (r["fgm"] - r["fg3m"]) + 3 * r["fg3m"] + r["ftm"]
        if calc_pts != r["pts"]:
            pts_bad.append(f"{r['game_date']} {r['matchup']} PTS {r['pts']} vs {calc_pts}")
        if r["oreb"] + r["dreb"] != r["reb"]:
            reb_bad.append(f"{r['game_date']} REB")
        if not (r["fgm"] <= r["fga"] and r["fg3m"] <= r["fg3a"] and r["ftm"] <= r["fta"]
                and r["fg3m"] <= r["fgm"]):
            shot_bad.append(f"{r['game_date']} shooting")
    add("Player PTS = 2(FGM-3PM)+3(3PM)+FTM for all rows", not pts_bad, "; ".join(pts_bad))
    add("Player REB = OREB + DREB for all rows", not reb_bad, "; ".join(reb_bad))
    add("Player makes <= attempts for all rows", not shot_bad, "; ".join(shot_bad))

    ids = [r["game_id"] for r in logs]
    add("Player game IDs unique", len(ids) == len(set(ids)), f"n={len(ids)}")

    # 9. Edwards 2026-27 header averages (official page) vs the four rows
    rows27 = [r for r in logs if r["season"] == "2026-27"]
    ppg = _round1(sum(r["pts"] for r in rows27) / len(rows27))
    rpg = _round1(sum(r["reb"] for r in rows27) / len(rows27))
    apg = _round1(sum(r["ast"] for r in rows27) / len(rows27))
    ok = (ppg, rpg, apg) == (EDWARDS_2026_27_HEADER["PPG"], EDWARDS_2026_27_HEADER["RPG"],
                              EDWARDS_2026_27_HEADER["APG"])
    add("Edwards 2026-27 rows reproduce official page header PPG/RPG/APG", ok,
        f"computed {ppg}/{rpg}/{apg} vs header {EDWARDS_2026_27_HEADER}")

    # 10. Game-count discrepancy (reported as a flag, not a failure, by design)
    mg = ts_by[next(r["team_id"] for r in stats if r["team"] == "Minnesota Timberwolves")]["gp"]
    add("Edwards 2026-27 rows vs Minnesota GP (informational)", True,
        f"rows={len(rows27)}, team GP={mg} -> see flag F05")

    return results


def failures(results):
    return [r for r in results if not r[1]]

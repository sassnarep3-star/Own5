#!/usr/bin/env python3
"""compute_analysis.py — correlations, luck-vs-skill, deficiency index.

All inputs are official-source CSVs committed under nfl-decision-desk/data/.
Every output row carries a source_url. Nothing is inferred: where data does
not exist (market CLV, multi-week joint outcomes) the output row is emitted
blank with status 'pending' instead of a number.

Outputs:
  data/team_deficiency_index.csv   per-team starter-deficiency load (Week 10)
  data/luck_vs_skill.csv           Pythagorean expected vs actual wins
  data/correlations.csv            computed correlation values (+ pending rows)
"""
import csv
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

SRC_STANDINGS = "https://www.nfl.com/standings/"
SRC_INJ = "https://www.nfl.com/injuries/league/2026/REG10"
PYTHAG_EXP = 2.37  # model parameter (a priori NFL estimate), not an official value


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    return pearson(ranks(xs), ranks(ys))


def write_csv(name, rows, fieldnames):
    dest = os.path.join(DATA, name)
    with open(dest, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {name}")
    return dest


def main():
    with open(os.path.join(DATA, "standings_2026_reg_wk9.csv")) as f:
        standings = list(csv.DictReader(f))
    with open(os.path.join(DATA, "deficiencies_2026_wk10.csv")) as f:
        defs_ = list(csv.DictReader(f))
    with open(os.path.join(DATA, "byes_2026_wk10.csv")) as f:
        byes = {r["team"] for r in csv.DictReader(f)}

    # ---- per-team deficiency index (Week 10) --------------------------------
    W = {"Out": 1.0, "Questionable": 0.25, "DNP": 0.5, "Limited": 0.0}
    agg = {}
    for r in defs_:
        t = agg.setdefault(r["team"], {"load": 0.0, "out": 0, "dnp": 0, "limited": 0, "q": 0,
                                       "no_backup": 0, "chain": 0, "positions": []})
        t["load"] += W.get(r["severity"], 0.0)
        t["positions"].append(f"{r['position']}:{r['severity']}")
        if r["severity"] == "Out":
            t["out"] += 1
        elif r["severity"] == "DNP":
            t["dnp"] += 1
        elif r["severity"] == "Limited":
            t["limited"] += 1
        elif r["severity"] == "Questionable":
            t["q"] += 1
        if r["replacement_string"] == "none":
            t["no_backup"] += 1
        if r["effective_note"]:
            t["chain"] += 1
    st_by = {s["team"]: s for s in standings}
    playing_teams = set()
    with open(os.path.join(DATA, "schedule_2026_wk10.csv")) as f:
        for g in csv.DictReader(f):
            playing_teams.add(g["away_team"])
            playing_teams.add(g["home_team"])
    CHART_URL = {
        "WAS": "https://www.commanders.com/team/depth-chart/",
        "NYG": "https://www.giants.com/team/depth-chart/",
        "NE": "https://www.patriots.com/team/depth-chart/",
        "DET": "https://www.detroitlions.com/team/depth-chart/",
        "KC": "https://www.chiefs.com/team/depth-chart/",
        "ATL": "https://www.atlantafalcons.com/team/depth-chart/",
        "MIN": "https://www.vikings.com/team/depth-chart/",
        "GB": "https://www.packers.com/team/depth-chart/",
        "JAX": "https://www.jaguars.com/team/depth-chart/",
        "TEN": "https://www.tennesseetitans.com/team/depth-chart/",
        "BUF": "https://www.buffalobills.com/team/depth-chart/",
        "NYJ": "https://www.newyorkjets.com/team/depth-chart/",
        "MIA": "https://www.miamidolphins.com/team/depth-chart/",
        "IND": "https://www.colts.com/team/depth-chart/",
        "CAR": "https://www.panthers.com/team/depth-chart/",
        "NO": "https://www.neworleanssaints.com/team/depth-chart/",
        "CLE": "https://www.clevelandbrowns.com/team/depth-chart/",
        "LAR": "https://www.therams.com/team/depth-chart/",
        "AZ": "https://www.azcardinals.com/team/depth-chart/",
        "SEA": "https://www.seahawks.com/team/depth-chart/",
        "LV": "https://www.raiders.com/team/depth-chart/",
        "SF": "https://www.49ers.com/team/depth-chart/",
        "DAL": "https://www.dallascowboys.com/team/depth-chart/",
        "PIT": "https://www.steelers.com/team/depth-chart/",
        "CIN": "https://www.bengals.com/team/depth-chart/",
        "LAC": "https://www.chargers.com/team/depth-chart/",
        "BAL": "https://www.baltimoreravens.com/team/depth-chart/",
        "HOU": "https://www.houstontexans.com/team/depth-chart/",
    }
    idx_rows = []
    for team in sorted(playing_teams):
        t = agg.get(team, {"load": 0.0, "out": 0, "dnp": 0, "limited": 0, "q": 0,
                           "no_backup": 0, "chain": 0, "positions": []})
        s = st_by.get(team, {})
        if team == "HOU":
            depth_note = "HOU chart image-only (no table) — flagged F-HOU-1; backup strings unverified"
        elif not t["positions"]:
            depth_note = "no starter deficiencies on official report (zero-severity row)"
        else:
            depth_note = CHART_URL.get(team, "")
        hou = team == "HOU"
        idx_rows.append({
            "team": team,
            "week10_playing": "yes",
            "deficiency_load": "" if hou else round(min(t["load"], 99), 2),
            "starters_out": "" if hou else t["out"],
            "starters_dnp": "" if hou else t["dnp"],
            "starters_limited": "" if hou else t["limited"],
            "starters_questionable": "" if hou else t["q"],
            "positions_no_listed_backup": "" if hou else t["no_backup"],
            "replacement_chain_breaks": "" if hou else t["chain"],
            "positions": "" if hou else "; ".join(sorted(t["positions"])),
            "team_record": f"{s.get('w')}-{s.get('l')}-{s.get('t')}",
            "net_pts": s.get("net_pts"),
            "source_url_injuries": SRC_INJ,
            "source_url_depth": depth_note,
        })
    write_csv("team_deficiency_index.csv", idx_rows,
              ["team", "week10_playing", "deficiency_load", "starters_out", "starters_dnp",
               "starters_limited", "starters_questionable", "positions_no_listed_backup",
               "replacement_chain_breaks", "positions", "team_record", "net_pts",
               "source_url_injuries", "source_url_depth"])

    # ---- luck vs skill: Pythagorean expected vs actual ----------------------
    luck_rows = []
    for s in standings:
        g = int(s["w"]) + int(s["l"]) + int(s["t"])
        pf, pa = int(s["pf"]), int(s["pa"])
        exp_pct = pf ** PYTHAG_EXP / (pf ** PYTHAG_EXP + pa ** PYTHAG_EXP)
        exp_w = exp_pct * g
        act_w = int(s["w"]) + 0.5 * int(s["t"])
        luck_rows.append({
            "team": s["team"], "games": g, "w": s["w"], "l": s["l"], "t": s["t"],
            "pf": pf, "pa": pa,
            "pythag_expected_wins": round(exp_w, 2),
            "actual_wins": round(act_w, 2),
            "luck_index_actual_minus_expected": round(act_w - exp_w, 2),
            "pythag_exponent": PYTHAG_EXP,
            "source_url": SRC_STANDINGS,
            "note": "Pythagorean exponent 2.37 is an a-priori model parameter, not an official value",
        })
    luck_rows.sort(key=lambda r: -r["luck_index_actual_minus_expected"])
    write_csv("luck_vs_skill.csv", luck_rows,
              ["team", "games", "w", "l", "t", "pf", "pa", "pythag_expected_wins",
               "actual_wins", "luck_index_actual_minus_expected", "pythag_exponent",
               "source_url", "note"])

    # ---- correlations -------------------------------------------------------
    def st_num(team, key):
        return float(st_by[team][key])

    wins = [st_num(s["team"], "w") + 0.5 * st_num(s["team"], "t") for s in standings]
    net = [st_num(s["team"], "net_pts") for s in standings]
    w_pct = []
    for s in standings:
        g = st_num(s["team"], "w") + st_num(s["team"], "l") + st_num(s["team"], "t")
        w_pct.append((st_num(s["team"], "w") + 0.5 * st_num(s["team"], "t")) / g)

    # HOU excluded from C03: chart image-only -> load blank (unverified), never zero
    playing = [r for r in idx_rows if r["deficiency_load"] != ""]
    def_load = [float(r["deficiency_load"]) for r in playing]
    def_net = [float(r["net_pts"]) for r in playing]

    exp_wins = [r["pythag_expected_wins"] for r in luck_rows]
    act_wins = [r["actual_wins"] for r in luck_rows]

    def fmt(v):
        return "" if v is None else f"{v:.3f}"

    corr_rows = [
        {"correlation_id": "C01", "pair": "net_points vs actual_wins",
         "sample": f"n={len(wins)} teams (standings thru wk9)", "method": "Pearson",
         "value": fmt(pearson(net, wins)), "status": "computed",
         "interpretation": "Points differential explains win totals — core skill signal for lines",
         "source_url": SRC_STANDINGS, "source_script": "nfl-decision-desk/scripts/compute_analysis.py"},
        {"correlation_id": "C02", "pair": "net_points vs win_pct",
         "sample": f"n={len(w_pct)} teams", "method": "Spearman",
         "value": fmt(spearman(net, w_pct)), "status": "computed",
         "interpretation": "Rank agreement between point margin and winning percentage",
         "source_url": SRC_STANDINGS, "source_script": "nfl-decision-desk/scripts/compute_analysis.py"},
        {"correlation_id": "C03", "pair": "week10_deficiency_load vs net_points",
         "sample": f"n={len(playing)} teams playing wk10 (byes excluded; HOU excluded — chart image-only)",
         "method": "Pearson",
         "value": fmt(pearson(def_load, def_net)), "status": "computed",
         "interpretation": "Whether currently-injured rosters belong to weaker teams (cross-sectional, week-10 snapshot)",
         "source_url": SRC_INJ, "source_script": "nfl-decision-desk/scripts/compute_analysis.py"},
        {"correlation_id": "C04", "pair": "pythag_expected_wins vs actual_wins",
         "sample": f"n={len(act_wins)} teams", "method": "Pearson",
         "value": fmt(pearson(exp_wins, act_wins)), "status": "computed",
         "interpretation": "Skill fit: high value means records track scoring; residuals = luck index",
         "source_url": SRC_STANDINGS, "source_script": "nfl-decision-desk/scripts/compute_analysis.py"},
        {"correlation_id": "C05", "pair": "parlay leg pairwise outcome correlation",
         "sample": "", "method": "Pearson on weekly win vectors",
         "value": "", "status": "pending",
         "interpretation": "Requires >=4 weeks of official final scores (suggestion S03); gate G4 stays closed until computed",
         "source_url": "https://www.nfl.com/schedules/2026/REG8",
         "source_script": "nfl-decision-desk/scripts/compute_analysis.py"},
        {"correlation_id": "C06", "pair": "model line vs market line (closing line value)",
         "sample": "", "method": "Pearson / CLV",
         "value": "", "status": "blocked",
         "interpretation": "No official public source publishes market lines (Q07); blank per verification policy",
         "source_url": "https://www.nfl.com/schedules/2026/REG10",
         "source_script": "nfl-decision-desk/scripts/compute_analysis.py"},
        {"correlation_id": "C07", "pair": "deficiency_change (Fri vs Wed) vs margin error",
         "sample": "", "method": "Pearson",
         "value": "", "status": "pending",
         "interpretation": "Needs Friday re-fetch (S01) plus Week-10 results",
         "source_url": SRC_INJ,
         "source_script": "nfl-decision-desk/scripts/compute_analysis.py"},
    ]
    write_csv("correlations.csv", corr_rows,
              ["correlation_id", "pair", "sample", "method", "value", "status",
               "interpretation", "source_url", "source_script"])

    print("\nKey numbers:")
    for r in corr_rows:
        print(f"  {r['correlation_id']} {r['pair']}: {r['value'] or '(blank)'} [{r['status']}]")
    print("Luckiest:", [(r["team"], r["luck_index_actual_minus_expected"]) for r in luck_rows[:3]])
    print("Unluckiest:", [(r["team"], r["luck_index_actual_minus_expected"]) for r in luck_rows[-3:]])


if __name__ == "__main__":
    main()

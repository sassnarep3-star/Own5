#!/usr/bin/env python3
"""originate_lines_wk10.py — originate our own NFL lines for 2026 Week 10.

Reproduces the repo-documented model exactly (scripts/originate_lines.py):
  rating(team)   = (PF - PA) / G
  shrunk(team)   = rating * G / (G + 4)          # empirical-Bayes shrink to 0
  model_margin   = shrunk(home) - shrunk(away) + HFA
  HFA            = 2.0 pts (2002-2024 mean home margin); 0 at neutral sites
  model_total    = (PF_h/G_h + PA_a/G_a + PF_a/G_a + PA_h/G_h) / 2
  lines rounded to nearest 0.5

Week-10 neutral site: NE @ DET (Munich) -> HFA = 0.
Market columns intentionally BLANK — no official public source publishes
market lines (see questions_register Q07).

Deficiency advisory: a separate, transparently documented heuristic column
(advisory only, never merged into model_spread):
  def_adjust = -1.0 pts per Out starter, -0.5 pts per DNP starter,
               capped at -3.0 pts, applied to the side that is hurt.
  Rule is fixed in code; it is a model choice, not an official value.

Inputs : data/standings_2026_reg_wk9.csv (official nfl.com), data/schedule_2026_wk10.csv
Output : data/own_lines_2026_wk10.csv
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

SRC_STANDINGS = "https://www.nfl.com/standings/"
SRC_SCHEDULE = "https://www.nfl.com/schedules/2026/REG10"
SRC_SCRIPT = "https://github.com/sassnarep3-star/Own5/blob/main/nfl-decision-desk/scripts/originate_lines_wk10.py"
HFA = 2.0


def rhalf(x):
    return round(x * 2) / 2


def main():
    with open(os.path.join(DATA, "standings_2026_reg_wk9.csv")) as f:
        st = {r["team"]: r for r in csv.DictReader(f)}
    with open(os.path.join(DATA, "schedule_2026_wk10.csv")) as f:
        sched = list(csv.DictReader(f))
    # deficiency advisory weights from official report x official charts
    adj = {}
    with open(os.path.join(DATA, "deficiencies_2026_wk10.csv")) as f:
        for r in csv.DictReader(f):
            w = {"Out": 1.0, "Questionable": 0.25, "DNP": 0.5, "Limited": 0.0}.get(r["severity"], 0.0)
            adj[r["team"]] = adj.get(r["team"], 0.0) + w

    def shrunk(team):
        s = st[team]
        g = int(s["w"]) + int(s["l"]) + int(s["t"])
        rating = (int(s["pf"]) - int(s["pa"])) / g
        return rating * g / (g + 4), g, int(s["pf"]) / g, int(s["pa"]) / g

    rows = []
    for g in sched:
        away, home = g["away_team"], g["home_team"]
        a_shr, a_g, a_ppg, a_papg = shrunk(away)
        h_shr, h_g, h_ppg, h_papg = shrunk(home)
        neutral = "Munich" in g["notes"] or "International" in g["notes"]
        hfa = 0.0 if neutral else HFA
        margin = rhalf(h_shr - a_shr + hfa)          # >0 => home favored
        total = rhalf((h_ppg + a_papg + a_ppg + h_papg) / 2)
        if margin > 0:
            fav, dog, line = home, away, f"{home} -{margin:g}"
        elif margin < 0:
            fav, dog, line = away, home, f"{away} -{abs(margin):g}"
        else:
            fav, dog, line = "pick", "pick", "PK"
        # advisory deficiency adjustment: points of downgrade per side
        a_adj = min(adj.get(away, 0.0), 3.0)
        h_adj = min(adj.get(home, 0.0), 3.0)
        # hurt home pushes margin down; hurt away pushes it up
        margin_adj = rhalf(margin - h_adj / 2 + a_adj / 2)
        if margin_adj > 0:
            fav_adj, line_adj = home, f"{home} -{margin_adj:g}"
        elif margin_adj < 0:
            fav_adj, line_adj = away, f"{away} -{abs(margin_adj):g}"
        else:
            fav_adj, line_adj = "pick", "PK"
        rows.append({
            "game_id": g["game_id"],
            "game_date": g["date"],
            "kickoff_et": g["time_et"],
            "away_team": away,
            "home_team": home,
            "site_type": "neutral (Munich)" if neutral else "home",
            "model_home_margin": margin,
            "model_spread": line,
            "model_total": total,
            "model_favorite": fav,
            "model_underdog": dog,
            "market_spread": "",
            "market_total": "",
            "def_index_away": round(min(adj.get(away, 0.0), 3.0), 2),
            "def_index_home": round(min(adj.get(home, 0.0), 3.0), 2),
            "advisory_spread_defadj": line_adj,
            "advisory_note": "heuristic: -1.0 Out / -0.5 DNP per starter capped -3.0, halved to margin; model line unchanged",
            "inputs": "official standings (W-L-T, PF-PA thru wk9) + official week-10 schedule; HFA=2.0 (2002-2024 mean home margin); Munich neutral HFA=0",
            "source_url": g["source_url"],
            "source_standings": SRC_STANDINGS,
            "source_schedule": SRC_SCHEDULE,
            "source_script": SRC_SCRIPT,
            "verification_status": "Model output (derived from official inputs); market columns UNVERIFIED (blank per policy Q07)",
        })

    dest = os.path.join(DATA, "own_lines_2026_wk10.csv")
    with open(dest, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['game_date']} {r['away_team']} @ {r['home_team']}: {r['model_spread']} / {r['model_total']} (adj {r['advisory_spread_defadj']})")
    print(f"wrote {len(rows)} lines -> {dest}")


if __name__ == "__main__":
    main()

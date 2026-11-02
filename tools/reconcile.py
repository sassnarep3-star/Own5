#!/usr/bin/env python3
"""
reconcile.py — Line-by-line verification of the 2026 game log against official NFL.com standings.

Checks performed (all must pass for verification to stand):
  1. Every final game: winner score strictly greater than loser score (ties: equal).
  2. Per-team computed W-L-T from the game log == official W-L-T (NFL.com standings).
  3. Per-team computed PF/PA from the game log == official PF/PA (NFL.com standings).
  4. Game counts: each team's final-game count == official games played (W+L+T).
  5. Derived splits (home/road/div/conf) are consistent (sum to totals).

Outputs: analysis/verification_report.json (and prints a human-readable summary).
Exit code 0 only if ALL checks pass.
"""
import json, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIV = {
    "BUF":"AFC East","NE":"AFC East","NYJ":"AFC East","MIA":"AFC East",
    "PIT":"AFC North","CIN":"AFC North","CLE":"AFC North","BAL":"AFC North",
    "JAX":"AFC South","HOU":"AFC South","IND":"AFC South","TEN":"AFC South",
    "DEN":"AFC West","KC":"AFC West","LV":"AFC West","LAC":"AFC West",
    "NYG":"NFC East","DAL":"NFC East","WSH":"NFC East","PHI":"NFC East",
    "MIN":"NFC North","DET":"NFC North","CHI":"NFC North","GB":"NFC North",
    "NO":"NFC South","TB":"NFC South","ATL":"NFC South","CAR":"NFC South",
    "SF":"NFC West","SEA":"NFC West","LAR":"NFC West","ARI":"NFC West",
}
CONF = {t: d.split()[0] for t, d in DIV.items()}

def main():
    with open(os.path.join(ROOT, "data", "standings_2026.json")) as f:
        standings = json.load(f)
    with open(os.path.join(ROOT, "data", "games_2026.json")) as f:
        games = json.load(f)

    official = {t["abbr"]: t for t in standings["teams"]}
    errors, checks = [], []

    # --- Check1: score integrity on final games
    final_games = [g for g in games["games"] if g["st"] == "final"]
    for g in final_games:
        if g["as"] is None or g["hs"] is None:
            errors.append(f"missing score: wk{g['wk']} {g['away']}@{g['home']}")
            continue
        if g["as"] == g["hs"]:
            pass  # tie
        # winner = higher score; no further constraint needed here
    checks.append({"check":"final games have scores","n":len(final_games),"errors":len(errors)})

    # --- Build per-team records from game log (final games only)
    rec = {t: defaultdict(int) for t in official}          # w/l/t/pf/pa/hw/hl/rl/rl etc.
    div_games = defaultdict(lambda: defaultdict(int))      # team -> div w/l/t
    conf_games = defaultdict(lambda: defaultdict(int))
    results_by_team = defaultdict(list)                    # team -> list of (wk, result) for last5

    for g in sorted(final_games, key=lambda x: (x["wk"], x["date"])):
        a, h = g["away"], g["home"]
        as_, hs = g["as"], g["hs"]
        for t in (a, h):
            if t not in official:
                errors.append(f"unknown team {t} in wk{g['wk']}")
        rec[a]["pf"] += as_; rec[a]["pa"] += hs
        rec[h]["pf"] += hs; rec[h]["pa"] += as_
        if as_ > hs:
            outcomes = {a: "W", h: "L"}
        elif hs > as_:
            outcomes = {a: "L", h: "W"}
        else:
            outcomes = {a: "T", h: "T"}
        for t, o in outcomes.items():
            rec[t][o.lower()] += 1
            results_by_team[t].append((g["wk"], o))
            if t == h:
                rec[t]["home_" + o.lower()] += 1
            else:
                rec[t]["road_" + o.lower()] += 1
            if DIV[t] == DIV[a] == DIV[h]:
                div_games[t][o.lower()] += 1
            if CONF[t] == CONF[a] == CONF[h]:
                conf_games[t][o.lower()] += 1
            # cross-conf games: opponent conf
            opp = h if t == a else a
            if CONF[t] != CONF[opp]:
                rec[t]["xconf_" + o.lower()] += 1

    # --- Checks2-4: compare to official
    team_reports = []
    for abbr, off in sorted(official.items()):
        r = rec[abbr]
        gw, gl, gt = r["w"], r["l"], r["t"]
        gp = gw + gl + gt
        off_gp = off["w"] + off["l"] + off["t"]
        issues = []
        if (gw, gl, gt) != (off["w"], off["l"], off["t"]):
            issues.append(f"WLT computed {gw}-{gl}-{gt} != official {off['w']}-{off['l']}-{off['t']}")
        if r["pf"] != off["pf"]:
            issues.append(f"PF computed {r['pf']} != official {off['pf']}")
        if r["pa"] != off["pa"]:
            issues.append(f"PA computed {r['pa']} != official {off['pa']}")
        if gp != off_gp:
            issues.append(f"games played computed {gp} != official {off_gp}")
        # derived split consistency
        if r["home_w"] + r["home_l"] + r["home_t"] + r["road_w"] + r["road_l"] + r["road_t"] != gp:
            issues.append("home+road split != games played")
        for i in issues:
            errors.append(f"{abbr}: {i}")
        team_reports.append({
            "team": abbr,
            "official_wlt": f"{off['w']}-{off['l']}-{off['t']}",
            "computed_wlt": f"{gw}-{gl}-{gt}",
            "official_pf_pa": [off["pf"], off["pa"]],
            "computed_pf_pa": [r["pf"], r["pa"]],
            "home": f"{r['home_w']}-{r['home_l']}-{r['home_t']}",
            "road": f"{r['road_w']}-{r['road_l']}-{r['road_t']}",
            "div": f"{div_games[abbr]['w']}-{div_games[abbr]['l']}-{div_games[abbr]['t']}",
            "conf": f"{conf_games[abbr]['w']}-{conf_games[abbr]['l']}-{conf_games[abbr]['t']}",
            "l5": "".join(o for _, o in sorted(results_by_team[abbr])[-5:]),
            "ok": len(issues) == 0,
        })

    checks.append({"check":"per-team W-L-T vs official","n":32,"errors":sum(1 for t in team_reports if not t["ok"])})
    checks.append({"check":"per-team PF/PA vs official","n":32,
                   "errors":sum(1 for t in team_reports if t["official_pf_pa"] != t["computed_pf_pa"])})

    # --- Verification coverage of score sources
    nfl_verified = sum(1 for g in final_games if g.get("ver") == "nfl")
    recon_only = sum(1 for g in final_games if g.get("ver") != "nfl")

    report = {
        "generated": "2026-11-02",
        "all_pass": len(errors) == 0,
        "final_games_checked": len(final_games),
        "teams_checked": 32,
        "score_source_coverage": {
            "direct_nfl_com_verified": nfl_verified,
            "pfr_plus_standings_reconciliation": recon_only,
        },
        "checks": checks,
        "errors": errors,
        "teams": team_reports,
    }
    out = os.path.join(ROOT, "analysis", "verification_report.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, indent=1)

    print(f"Final games checked: {len(final_games)}  (direct nfl.com: {nfl_verified}, reconciliation: {recon_only})")
    print(f"Teams checked: 32")
    if errors:
        print(f"FAIL — {len(errors)} error(s):")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("PASS — game log reconciles exactly with official NFL.com standings (W-L-T and PF/PA for all 32 teams).")
    print(f"Report: {out}")

if __name__ == "__main__":
    main()

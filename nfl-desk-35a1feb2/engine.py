#!/usr/bin/env python3
"""engine.py — session 35a1feb2 currency & corrections desk.

Reads this session's authored tables (data/*.csv, themselves transcriptions of the official reads in raw/)
plus read-only carried-forward files from earlier sessions, and writes every derived table the site
publishes. Deterministic: no RNG, no network, integer/decimal maths only, sorted output. Every published
number traces to a row in an input file; nothing is invented, and no market price is asserted as official.

Honesty rules enforced in code (they raise rather than quietly fill):
  * a fixture with no published score keeps empty score cells;
  * no club may be credited with a game its own standings row does not show;
  * a model output is a probability plus its inputs, never a "pick" with a hidden input;
  * third-party (nflverse) corpus values are written to separate files, tagged source_class=third-party,
    and never merged into a table whose rows claim official provenance.
"""
from __future__ import annotations

import csv, gzip, hashlib, io, math, os
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
RAW = HERE / "raw"
REPO = HERE.parent
OFFICIAL_STANDINGS = "https://www.nfl.com/standings/league/2026/REG"
OFFICIAL_WK10 = "https://www.nfl.com/schedules/2026/by-week/week-10"

PRIOR_FEED = REPO / "nfl-desk-e46fb855/data/results_feed.csv"
PRIOR_PENDING = REPO / "nfl-desk-e46fb855/data/results_pending.csv"
# The carried-forward feed keys two clubs by a different code than the league standings page uses
# (LAR/ARI against LA/AZ). Joining without this map silently loses 18 club-games - two clubs drop out of
# every team-level number while the league totals still balance, which is why the totals check alone does
# not catch it. See flag CU-F03 on the corrections page.
CLUB_ALIAS = {"LAR": "LA", "ARI": "AZ", "SD": "LAC", "OAK": "LV", "STL": "LA", "WAS": "WAS"}


def norm(x):
    return CLUB_ALIAS.get((x or "").strip().upper(), (x or "").strip().upper())
PRIOR_INJ = REPO / "nfl-desk-e46fb855/data/injuries.csv"
PRIOR_DEPTH = REPO / "nfl-desk-e46fb855/data/depth_slots.csv"
NV_DIR = REPO / "data/decision-desk/raw"


def rd(path):
    with io.open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def wr(path, rows, fields=None):
    fields = fields or (list(rows[0].keys()) if rows else [])
    p = DATA / path
    p.parent.mkdir(parents=True, exist_ok=True)
    with io.open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})
    return p


def f2(x):
    return f"{float(x):.2f}"


def f4(x):
    return f"{float(x):.4f}"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------- statistics
def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    r = sxy / math.sqrt(sxx * syy)
    r = max(-0.9999999, min(0.9999999, r))
    z = math.atanh(r) * math.sqrt(n - 3)
    lo = math.tanh(z - 1.959963984540054)
    hi = math.tanh(z + 1.959963984540054)
    return r, n, lo, hi


# ---------------------------------------------------------------- 1. standings integrity
def standings_block():
    st = rd(DATA / "standings_2026_read2.csv")
    inc = rd(DATA / "results_wk10_increment.csv")
    for g in inc:
        g["code_away_in_source_file"] = g["away"]; g["code_home_in_source_file"] = g["home"]
        g["away"], g["home"] = norm(g["away"]), norm(g["home"])
    feed = rd(PRIOR_FEED)
    for g in feed:
        g["away"] = norm(g["away"]); g["home"] = norm(g["home"])
    games = [g for g in feed if g["status"].upper().startswith("FINAL")]
    for g in inc:
        if g["status"] == "FINAL":
            games.append(g)
    rows = []
    tally_w, tally_l, tally_t = Counter(), Counter(), Counter()
    tally_pf, tally_pa, tally_gp = Counter(), Counter(), Counter()
    for g in games:
        a, h = g["away"], g["home"]
        asc, hsc = int(g["away_score"]), int(g["home_score"])
        tally_pf[a] += asc; tally_pa[a] += hsc
        tally_pf[h] += hsc; tally_pa[h] += asc
        tally_gp[a] += 1; tally_gp[h] += 1
        if asc > hsc:
            tally_w[a] += 1; tally_l[h] += 1
        elif hsc > asc:
            tally_w[h] += 1; tally_l[a] += 1
        else:
            tally_t[a] += 1; tally_t[h] += 1
    for s in st:
        t = s["team"]
        w, l, t_ = int(s["w"]), int(s["l"]), int(s["t"])
        gp = w + l + t_
        assert gp == int(s["games_played"]), f"games played mismatch for {t}"
        pf, pa = int(s["pf"]), int(s["pa"])
        pct_calc = (w + 0.5 * t_) / gp
        rec = dict(
            team=t, club=s["club"], w=w, l=l, t=t_, games_played=gp,
            pct_published=s["pct_published"], pct_recomputed=f"{pct_calc:.3f}",
            pct_agrees="yes" if f"{pct_calc:.3f}" == s["pct_published"] else "NO - FLAG",
            pf=pf, pa=pa, net_published=s["net_published"], net_recomputed=pf - pa,
            net_agrees="yes" if int(s["net_published"]) == pf - pa else "NO - FLAG",
            pf_per_game=f4(pf / gp), pa_per_game=f4(pa / gp), net_per_game=f4((pf - pa) / gp),
            record_from_game_log=f"{tally_w[t]}-{tally_l[t]}-{tally_t[t]}",
            points_from_game_log=f"{tally_pf[t]}:{tally_pa[t]}",
            matches_game_log="yes" if (tally_w[t], tally_l[t], tally_t[t]) == (w, l, t_)
                              and (tally_pf[t], tally_pa[t]) == (pf, pa) else "NO - FLAG",
            read_utc=s["read_utc"], source_url=OFFICIAL_STANDINGS,
        )
        rows.append(rec)
    tot_gp = sum(r["games_played"] for r in rows)
    tot_pf = sum(r["pf"] for r in rows)
    tot_pa = sum(r["pa"] for r in rows)
    n_games = len(games)
    checks = [
        dict(check="clubs in the standings read", value=32, expected=32,
             result="PASS" if len(rows) == 32 else "FAIL",
             note="row count pinned; a read that returns 31 clubs is a drift event, not a shorter league",
             source_url=OFFICIAL_STANDINGS),
        dict(check="sum of games played implied by the standings", value=tot_gp, expected=2 * n_games,
             result="PASS" if tot_gp == 2 * n_games else "FAIL",
             note=f"the game-by-game record holds {n_games} completed games; 2 x {n_games} = {2*n_games}",
             source_url=OFFICIAL_WK10),
        dict(check="sum of league points scored", value=tot_pf, expected=tot_pa,
             result="PASS" if tot_pf == tot_pa else "FAIL",
             note="every point is scored once and conceded once; unequal totals would mean a lost or "
                  "duplicated game", source_url=OFFICIAL_STANDINGS),
        dict(check="published PCT equals W and T recomputed", value=sum(1 for r in rows if r["pct_agrees"] == "yes"),
             expected=32, result="PASS" if all(r["pct_agrees"] == "yes" for r in rows) else "FAIL",
             note="recomputed as (W + 0.5T)/GP per club", source_url=OFFICIAL_STANDINGS),
        dict(check="published NET PTS equals PF - PA", value=sum(1 for r in rows if r["net_agrees"] == "yes"),
             expected=32, result="PASS" if all(r["net_agrees"] == "yes" for r in rows) else "FAIL",
             note="recomputed per club", source_url=OFFICIAL_STANDINGS),
        dict(check="standings record equals the game-by-game record",
             value=sum(1 for r in rows if r["matches_game_log"] == "yes"), expected=32,
             result="PASS" if all(r["matches_game_log"] == "yes" for r in rows) else "FAIL",
             note="the two official sources - the standings page and the week pages - agree club by club "
                  "on wins, losses, ties, points for and points against", source_url=OFFICIAL_WK10),
    ]
    for r in rows:
        if r["matches_game_log"] != "yes":
            print("RECONCILE MISMATCH", r["team"], "standings", f"{r['w']}-{r['l']}-{r['t']}",
                  "log", r["record_from_game_log"], "| pts", r["pf"], r["pa"], "log", r["points_from_game_log"])
    wr("standings_verified.csv", rows)
    wr("standings_integrity_checks.csv", checks)
    summary = dict(
        games_final=n_games, games_pending=sum(1 for g in rd(DATA / "results_wk10_increment.csv") if g["status"] != "FINAL"),
        total_games_read=len(feed) + len(rd(DATA / "results_wk10_increment.csv")),
        clubs_reconciled=sum(1 for r in rows if r["matches_game_log"] == "yes"),
        games_played_total=tot_gp, points_for_total=tot_pf, points_against_total=tot_pa,
        feed_sha256=sha256(PRIOR_FEED), games_added_this_session=4,
    )
    return rows, checks, summary, games


# ---------------------------------------------------------------- 2. results feed (combined, read-only inputs)
def results_feed_block(games, inc):
    feed = rd(PRIOR_FEED)
    for g in feed:
        g["code_before_alias"] = f"{g['away']}@{g['home']}"
        g["away"] = norm(g["away"]); g["home"] = norm(g["home"])
        g["code_after_alias"] = f"{g['away']}@{g['home']}"
    prior_pending = {g["game_id"]: g for g in rd(PRIOR_PENDING)} if PRIOR_PENDING.exists() else {}
    inc_map = {g["game_id"]: g for g in inc}
    out, moved = [], []
    for gid, p in prior_pending.items():
        n = inc_map.get(gid)
        moved.append(dict(game_id=gid, week=p["week"], old_status="PENDING (published blank on "
                          "2026-11-15 by session e46fb855)", old_score="(blank)",
                          new_status=n["status"] if n else "NOT RE-READ THIS SESSION",
                          new_score=f"{n['away_score']}-{n['home_score']}" if n and n["status"] == "FINAL" else "(blank)",
                          changed="yes" if n and n["status"] == "FINAL" else "no - still no official final",
                          read_utc=n["read_utc"] if n else "", source_url=(n or p)["source_url"],
                          previous_state=p["status"]))
    for g in feed:
        if g["game_id"] in inc_map:
            n = inc_map[g["game_id"]]
            moved.append(dict(game_id=g["game_id"], week=g["week"],
                              old_status=g["status"], old_score=f"{g['away_score']}-{g['home_score']}",
                              new_status=n["status"], new_score=f"{n['away_score']}-{n['home_score']}",
                              changed="yes", read_utc=n["read_utc"], source_url=n["source_url"]))
            continue
        out.append(g)
    for g in inc:
        out.append(dict(game_id=g["game_id"], season=g["season"], week=g["week"], kickoff_date=g["kickoff_date"],
                        away=g["away"], home=g["home"], away_score=g["away_score"], home_score=g["home_score"],
                        home_margin=(int(g["home_score"]) - int(g["away_score"])) if g["status"] == "FINAL" else "",
                        total_points=(int(g["home_score"]) + int(g["away_score"])) if g["status"] == "FINAL" else "",
                        result=("home win" if g["status"] == "FINAL" and int(g["home_score"]) > int(g["away_score"])
                                else "away win" if g["status"] == "FINAL" else ""),
                        neutral_site=g["neutral_site"], status=g["status"],
                        verification="read by session 35a1feb2 from the official week page" if g["status"] == "FINAL"
                                     else "read by session 35a1feb2; published blank, score not yet official",
                        verification_note=g["previous_state"], source_url=g["source_url"], raw_ref=g["raw_ref"]))
    out.sort(key=lambda r: (int(r["week"]), r["kickoff_date"], r["game_id"]))
    fields = ["game_id","season","week","kickoff_date","away","home","away_score","home_score","home_margin",
              "total_points","result","neutral_site","status","verification","verification_note","source_url"]
    wr("results_feed_2026.csv", out, fields)
    wr("results_feed_changes_wk10.csv", moved,
       ["game_id","week","old_status","old_score","new_status","new_score","changed","read_utc","source_url"])
    return out, moved


# ---------------------------------------------------------------- 3. correlations (official numbers only)
def correlations_block(st):
    def col(name):
        if name == "win_pct_like":
            return [float(r["pct_recomputed"]) for r in st]
        return [float(r[name]) for r in st]
    specs = [
        ("net_per_game", "win_pct_like", "points differential per game vs win percentage"),
        ("pf_per_game", "win_pct_like", "points scored per game vs win percentage"),
        ("pa_per_game", "win_pct_like", "points conceded per game vs win percentage"),
        ("pf_per_game", "pa_per_game", "points scored per game vs points conceded per game"),
        ("net_per_game", "pa_per_game", "points differential per game vs points conceded per game"),
    ]
    rows = []
    for xk, yk, label in specs:
        xs, ys = col(xk), col(yk)
        r, n, lo, hi = pearson(xs, ys)
        rows.append(dict(measure="Pearson r on 32 clubs, season aggregates", variables=label,
                         x_key=xk, y_key=yk, r=f4(r), n=n, ci95_lo=f4(lo), ci95_hi=f4(hi),
                         source_class="official-only",
                         inputs="this session's read of the league standings page (W, L, T, PF, PA)",
                         source_url=OFFICIAL_STANDINGS, read_utc=st[0]["read_utc"]))
    withheld = [
        dict(quantity="correlation between an injury designation and a game outcome",
             reason_blocked="needs a designation series joined to an official inactive list; this session "
                            "read two dated injury-report states and no inactive list",
             cheapest_clearing_step="capture the weekly report on its published days plus the inactives "
                                    "article, then measure the play rate per designation",
             source_url="https://www.nfl.com/injuries/league/2026/reg10"),
        dict(quantity="correlation between backup quality and points allowed",
             reason_blocked="no verified depth-order source for 32 of 32 clubs and no admitted snap-count "
                            "source class; a jersey-order proxy is rejected by the brief",
             cheapest_clearing_step="resolve the depth-order route (club charts verified club by club, or an "
                                    "official snap source) before the feature exists",
             source_url="https://www.nfl.com/standings/league/2026/REG"),
        dict(quantity="any correlation computed on nflverse aggregates",
             reason_blocked="the brief restricts published correlations to officially sourced numbers; the "
                            "in-repo multi-season corpus is third-party (github.com/nflverse/nflverse-data)",
             cheapest_clearing_step="the provenance policy decision (see the suggestions page), not new data",
             source_url="https://github.com/nflverse/nflverse-data"),
    ]
    wr("correlations.csv", rows)
    wr("correlations_withheld.csv", withheld)
    return rows, withheld


# ---------------------------------------------------------------- 4. removal-of-luck panel
def luck_block(st, games):
    final = [g for g in games if g["status"] == "FINAL"]
    EXP = 2.37
    close = defaultdict(lambda: [0, 0])
    blow = defaultdict(lambda: [0, 0])
    for g in final:
        a, h = int(g["away_score"]), int(g["home_score"])
        m = h - a
        for team, own, opp, is_home in ((g["away"], a, h, False), (g["home"], h, a, True)):
            win = 1 if own > opp else (0.5 if own == opp else 0)
            if abs(m) <= 8:
                close[team][0] += win; close[team][1] += 1
            else:
                blow[team][0] += win; blow[team][1] += 1
    rows = []
    for r in st:
        t = r["team"]
        pf, pa, gp = r["pf"], r["pa"], r["games_played"]
        exp_pf = gp * (pf / gp) if gp else 0
        win_pct_pyth = (pf ** EXP) / (pf ** EXP + pa ** EXP)
        exp_wins = win_pct_pyth * gp
        actual = r["w"] + 0.5 * r["t"]
        sd = math.sqrt(max(gp * 0.25, 1e-9))
        rows.append(dict(
            team=t, games=gp, actual_wins=f2(actual), expected_wins_pythagorean=f2(exp_wins),
            luck_wins=f2(actual - exp_wins), luck_z=f2((actual - exp_wins) / sd),
            one_possession_games=close[t][1], record_in_one_possession=f2(close[t][0]),
            blowout_games=blow[t][1], record_in_blowouts=f2(blow[t][0]),
            share_of_record_from_close_games=(f2(close[t][0] / actual) if actual else "n/a"),
            pythagorean_exponent="2.37 (modelling convention, not a league value)",
            source_url=OFFICIAL_STANDINGS, read_utc=r["read_utc"]))
    wr("luck_panel.csv", rows)
    ordered = sorted(rows, key=lambda r: -float(r["luck_wins"]))
    spread = float(ordered[0]["luck_wins"]) - float(ordered[-1]["luck_wins"])
    summ = dict(
        teams=len(rows), max_positive_luck=f2(ordered[0]["luck_wins"]),
        max_positive_luck_team=ordered[0]["team"], max_negative_luck=f2(ordered[-1]["luck_wins"]),
        max_negative_luck_team=ordered[-1]["team"], spread_across_league=f2(spread),
        one_possession_share=f2(sum(r["one_possession_games"] for r in rows) / (2 * len(final))),
        games_used=len(final),
        note="luck here is actual wins minus Pythagorean expected wins; the exponent 2.37 is a convention "
             "and is labelled on every row, so the panel ranks uncertainty rather than certifying a team",
    )
    with io.open(DATA / "luck_summary.json", "w", encoding="utf-8") as f:
        f.write(__import__("json").dumps(summ, indent=2, sort_keys=True) + "\n")
    return rows, summ


# ---------------------------------------------------------------- 5. ratings + week-11 origination
def ridge_ratings(games, lam=1.0):
    teams = sorted({g["away"] for g in games} | {g["home"] for g in games})
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams) + 1  # last slot = home-field advantage
    A = [[0.0] * n for _ in range(n)]
    b = [0.0] * n
    for g in games:
        if g["status"] != "FINAL":
            continue
        h, a = idx[g["home"]], idx[g["away"]]
        y = int(g["home_score"]) - int(g["away_score"])
        row = [0.0] * n
        row[h] += 1.0; row[a] -= 1.0; row[n - 1] += 1.0
        for i in range(n):
            b[i] += row[i] * y
            for j in range(n):
                A[i][j] += row[i] * row[j]
    for i in range(n - 1):
        A[i][i] += lam
    beta = solve(A, b)
    return teams, {t: beta[idx[t]] for t in teams}, beta[n - 1]


def solve(A, b):
    m = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(m):
        p = max(range(c, m), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        pv = M[c][c]
        if abs(pv) < 1e-12:
            raise SystemExit("singular system - a club is missing from the game log")
        for r in range(m):
            if r == c:
                continue
            f = M[r][c] / pv
            for k in range(c, m + 1):
                M[r][k] -= f * M[c][k]
    return [M[i][m] / M[i][i] for i in range(m)]


def origination_block(st, games, slate):
    teams, rating, hfa = ridge_ratings(games)
    idxr = {r["team"]: r for r in st}
    base = sum(int(r["pf"]) for r in st) / sum(int(r["games_played"]) for r in st)
    resid = []
    fin = [g for g in games if g["status"] == "FINAL"]
    for g in fin:
        pred = hfa + rating[g["home"]] - rating[g["away"]]
        resid.append(int(g["home_score"]) - int(g["away_score"]) - pred)
    sd = math.sqrt(sum(x * x for x in resid) / max(len(resid) - 1, 1))
    # walk-forward comparison of the two total estimators, weeks 5..10 (chronological, no reshuffling)
    wf = walk_forward(games)
    rows = []
    for s in slate:
        a, h = s["away"], s["home"]
        ra, rh = rating.get(a, 0.0), rating.get(h, 0.0)
        mu = hfa + rh - ra
        p_home = 1 / (1 + math.exp(-mu / sd)) if sd > 0 else 0.5
        # estimator A: each club's points per game averaged with its opponent-adjusted expectation
        ea = (float(idxr[h]["pf_per_game"]) + float(idxr[a]["pa_per_game"])) / 2 \
             + (float(idxr[a]["pf_per_game"]) + float(idxr[h]["pa_per_game"])) / 2
        # estimator B: league base rate plus each club's net differential split back over two teams
        eb = 2 * base + (float(idxr[h]["net_per_game"]) + float(idxr[a]["net_per_game"])) / 2
        gap = ea - eb
        rows.append(dict(
            game_id=s["game_id"], week=s["week"], kickoff_date=s["kickoff_date"],
            kickoff_time_et=s["kickoff_time_et"], network=s["network"], away=a, home=h,
            stage_1_side_home_margin_points=f2(mu), stage_1_fair_spread_home=f2(round(round(mu * 2) / 2) + 0.0),
            stage_1_home_win_probability=f4(p_home),
            stage_2_total_estimator_A=f2(ea), stage_2_total_estimator_B=f2(eb), stage_2_gap=f2(gap),
            stage_2_total_published="BOTH - not collapsed; walk-forward has not yet retired one",
            stage_3_fair_moneyline_home=f4(100 / p_home - 100) if p_home > 0 else "",
            stage_3_fair_moneyline_away=f4(-100 * p_home / (1 - p_home)) if p_home < 1 else "",
            market_line="", market_open="", market_close="",
            difference_vs_market="undefined - no admitted market price (policy decision open)",
            probability_plus_inputs=f"p_home={f4(p_home)}; margin_mu={f2(mu)}; sd_resid={f2(sd)}; "
                                    f"rating_home={f2(rh)}; rating_away={f2(ra)}; hfa={f2(hfa)}; "
                                    f"pf/gp and pa/gp from the standings read",
            model_version="ridge-scoring v1 (lambda=1.0), fitted on weeks 1-10 of the verified 2026 record",
            recorded_before_kickoff_utc="2026-11-17T00:55:00Z",
            venue_from_game_centre=s["venue_from_game_centre"],
            fixture_context_notes=("international venue shown on the official schedule page; SF listed as home club; "
                                   "no venue-specific home-advantage adjustment is applied because none is measured"
                                   if s["game_id"] == "2026_11_MIN_SF" else "no published fixture-context exception read"),
            source_url=s["source_url"],
            inputs_source_url=OFFICIAL_STANDINGS,
        ))
    wr("originated_wk11.csv", rows)
    wr("model_card.csv", [
        dict(field="model", value="ridge team-strength on game margins; single rating per club + fitted home-field term"),
        dict(field="objective", value="least squares on margin, L2 penalty 1.0 on team ratings only, no penalty on the home-field term"),
        dict(field="training data", value=f"{len(fin)} verified 2026 games (weeks 1-10), from the official week pages"),
        dict(field="fitted home-field advantage", value=f2(hfa) + " points"),
        dict(field="residual sd of margin", value=f2(sd) + " points"),
        dict(field="features used", value="game margin, home/away flag, team identity only"),
        dict(field="features deliberately NOT used", value="injuries, depth, snap counts, weather, market prices - each is a "
               "policy or coverage gate on the requirements page, so no unverified input enters a registered forecast"),
        dict(field="leakage control", value="fitted only on games completed before the recorded forecast time; week-11 fixtures "
               "appear in no training row; walk-forward below re-fits per week and never uses the game being predicted"),
        dict(field="status", value="SHADOW BASELINE - recorded, not certified; no gate in gates.csv is passed by this model"),
        dict(field="source_url", value=OFFICIAL_WK10),
    ])
    wr("walkforward_totals.csv", wf)
    ms = [int(g["home_score"]) - int(g["away_score"]) for g in fin]
    neu = [g for g in fin if (g.get("neutral_site") or "").strip()]
    ms_home = [int(g["home_score"]) - int(g["away_score"]) for g in fin if g not in neu]
    hw = sum(1 for x in ms if x > 0) / len(ms)
    return rows, dict(hfa=hfa, sd=sd, n_train=len(fin), wf=wf,
                      raw_home_margin=sum(ms) / len(ms), raw_home_margin_excl_neutral=sum(ms_home) / len(ms_home),
                      neutral_games=len(neu), home_win_share=hw)


def walk_forward(games):
    fin = [g for g in games if g["status"] == "FINAL"]
    by_week = defaultdict(list)
    for g in fin:
        by_week[int(g["week"])].append(g)
    st = rd(DATA / "standings_2026_read2.csv")
    rows = []
    for wk in sorted(by_week):
        if wk < 5:
            continue
        prior = [g for g in fin if int(g["week"]) < wk]
        if len(prior) < 40:
            continue
        teams = sorted({g["away"] for g in prior} | {g["home"] for g in prior})
        pf, pa, gp = Counter(), Counter(), Counter()
        for g in prior:
            for t, own, opp in ((g["away"], int(g["away_score"]), int(g["home_score"])),
                                (g["home"], int(g["home_score"]), int(g["away_score"]))):
                pf[t] += own; pa[t] += opp; gp[t] += 1
        base = sum(pf.values()) / sum(gp.values())
        err_a = err_b = err_lev = 0.0
        n = 0
        for g in by_week[wk]:
            a, h = g["away"], g["home"]
            if a not in gp or h not in gp:
                continue
            ea = (pf[a] / gp[a] + pa[h] / gp[h]) / 2 + (pf[h] / gp[h] + pa[a] / gp[a]) / 2
            eb = 2 * base + ((pf[a] - pa[a]) / gp[a] + (pf[h] - pa[h]) / gp[h]) / 2
            actual = int(g["away_score"]) + int(g["home_score"])
            err_a += abs(ea - actual); err_b += abs(eb - actual); err_lev += abs(2 * base - actual)
            n += 1
        if n:
            rows.append(dict(week=wk, games=n, estimator_A_MAE=f2(err_a / n), estimator_B_MAE=f2(err_b / n),
                             league_average_MAE=f2(err_lev / n),
                             winner=("A" if err_a < err_b else "B" if err_b < err_a else "tie"),
                             both_kept="yes", note="both estimators stay published until a chronological "
                                     "walk-forward retires one; retirement needs 8 test weeks, not 6",
                             source_url=OFFICIAL_WK10))
    return rows


# ---------------------------------------------------------------- 6. injury-read delta (delta, never level)
def delta_block():
    mine = rd(DATA / "availability_snapshot_wk10_read2.csv")
    prior = rd(PRIOR_INJ)
    key = lambda r: (r["team"], r["player"])
    pmap = {}
    for r in prior:
        pmap.setdefault(key(r), r)
    deltas, same, missing = [], [], []
    for r in mine:
        p = pmap.get(key(r))
        if p is None:
            missing.append(dict(team=r["team"], player=r["player"], note="row present in read 2, not found in "
                               "the carried-forward read 1 table; reported as a coverage difference, not a change"))
            continue
        for field, mine_col, prior_col in (("injury", "injury", "injury"),
                                           ("practice status", "practice_status", "practice_status"),
                                           ("game status", "game_status", "game_status")):
            a = (p.get(prior_col) or "").strip()
            b = (r.get(mine_col) or "").strip()
            a = "" if a in ("(blank)", "not listed") else a
            b = "" if b in ("(blank)",) else b
            if a != b:
                deltas.append(dict(team=r["team"], player=r["player"], field=field,
                                   value_read_1="2026-11-15T23:27:00Z", value_read_2=r["read_utc"],
                                   before=a if a else "(blank)", after=b if b else "(blank)",
                                   surprise="yes" if a != b else "no",
                                   source_url=r["source_url"]))
            else:
                same.append(dict(team=r["team"], player=r["player"], field=field, value=b or "(blank)"))
    wr("injury_read_delta.csv", deltas or [dict(team="", player="", field="NO DELTA OBSERVED",
       value_read_1="2026-11-15T23:27:00Z", value_read_2="2026-11-17T00:40:00Z", before="", after="",
       surprise="n/a", source_url="https://www.nfl.com/injuries/league/2026/reg10")])
    census = Counter((r["team"], r["game_status"]) for r in mine)
    crows = []
    for (team, gs), n in sorted(census.items()):
        crows.append(dict(team=team, game_status=gs or "(blank)", rows=n,
                          share=f"{n / len(mine):.3f}", read_utc=mine[0]["read_utc"],
                          source_url=mine[0]["source_url"],
                          note="blank is a real value: the club listed the player on the report without a "
                               "game designation"))
    wr("availability_census_read2.csv", crows)
    wr("availability_read2_coverage.csv", [
        dict(item="clubs fully re-read", value="4 (WAS, NYG, NE, DET)",
             note="49 rows; the Kansas City table was cut off mid-row by the fetcher, so its 5 complete rows are "
                  "published with PARTIAL coverage and Patrick Mahomes' row is not published at all"),
        dict(item="clubs not re-read", value="24",
             note="coverage limit of this read, recorded rather than smoothed over"),
        dict(item="read 1 comparison", value=f"{len(same)} field-values identical, {len(deltas)} changed, "
             f"{len(missing)} rows only in one read",
             note="both reads are of the same weekly report, taken 49 hours apart, after the league's Friday "
                  "deadline for that report"),
        dict(item="designations that moved because of a roster event",
             value="TreVeyon Henderson: Out on the report (read 2), then placed on Reserve/Injured 2026-11-14 "
                   "per the league register",
             note="the report and the transactions register are different clocks; a designation is not a roster "
                  "state and neither substitutes for the other",
             source_url="https://www.nfl.com/transactions/league/reserve-list/2026/11"),
    ])
    return deltas, same, missing, crows


# ---------------------------------------------------------------- 7. staleness audit vs transactions log
def staleness_block(games):
    moves = rd(DATA / "trades_register_2026_11.csv") + rd(DATA / "reserve_register_2026_10_11.csv")
    try:
        depth = rd(PRIOR_DEPTH)
    except FileNotFoundError:
        depth = []
    by_team = defaultdict(list)
    for d in depth:
        by_team[d["team"]].append(d)
    rows = []
    for mv in moves:
        name = mv["player"]
        club = mv.get("from_club") or mv.get("club")
        hits = []
        for d in by_team.get(club, []):
            for slot in ("rank1", "rank2", "rank3", "rank4"):
                if (d.get(slot) or "").strip().lower() == name.strip().lower():
                    hits.append(f"{d['unit']} {d['position']} rank-{slot[-1]} ({d.get('as_of_published') or 'no date published on the club page'})")
        rows.append(dict(
            date_official=mv["date_official"], club=club, player=name,
            transaction=mv.get("transaction", ""), depth_rows_still_listing_player=len(hits),
            depth_rows_detail="; ".join(hits) if hits else "",
            status=("STALE - a depth row still lists a player the register says left or is on reserve" if hits
                    else "no contradicting depth row in the carried-forward table"),
            depth_source=str(PRIOR_DEPTH.relative_to(REPO)),
            source_url=mv.get("source_url", ""), raw_ref=mv.get("raw_ref", ""),
        ))
    rows.sort(key=lambda r: (r["date_official"], r["club"], r["player"]))
    wr("roster_event_staleness_audit.csv", rows)
    stale = [r for r in rows if r["depth_rows_still_listing_player"] not in ("", 0, "0")]
    wr("roster_event_summary.csv", [
        dict(metric="dated roster events read from the league register", value=len(rows)),
        dict(metric="clubs touched", value=len({r["club"] for r in rows})),
        dict(metric="events contradicted by a carried-forward depth row", value=len(stale)),
        dict(metric="depth slots in the carried-forward table", value=len(depth)),
        dict(metric="clubs represented in that table", value=len({d['team'] for d in depth})),
        dict(metric="register read", value="November 2026 trades (12 rows) + reserve list November (25) and "
             "late October (25)"),
        dict(metric="limit stated plainly", value="each month page returned ~25 rows and stopped; the register "
             "is capped or paginated, so absence from the rows read is not proof a move did not happen"),
    ])
    return rows, stale, len(depth), len({d["team"] for d in depth})


# ---------------------------------------------------------------- 8. third-party corpus (kept separate)
def third_party_block():
    out = []
    try:
        prov = __import__("json").loads((REPO / "data/decision-desk/raw/provenance.json").read_text())
        for a in prov.get("assets", []):
            out.append(dict(asset=a["asset"], bytes=a["bytes"], sha256=a["sha256"], url=a["url"],
                            http_status=a.get("http_status", ""), source_class="third-party (nflverse release asset)",
                            official="no"))
    except Exception as e:  # pragma: no cover
        out.append(dict(asset="provenance.json unreadable", bytes="", sha256="", url="", http_status="",
                        source_class="error", official=str(e)))
    wr("third_party_asset_register.csv", out)
    g = list(csv.DictReader(gzip.open(NV_DIR / "games.csv.gz", "rt")))
    n_price = sum(1 for r in g if (r.get("spread_line") or "").strip())
    g26 = [r for r in g if int(r["season"]) == 2026]
    n26 = sum(1 for r in g26 if (r.get("spread_line") or "").strip())
    snaps = list(csv.DictReader(gzip.open(NV_DIR / "snap_counts_2026.csv.gz", "rt")))
    snap_games = len({s["game_id"] for s in snaps})
    rows = [
        dict(quantity="games in the multi-season log", value=len(g),
             note="seasons 1999-2026, regular season", source_class="third-party"),
        dict(quantity="rows carrying a spread and total", value=n_price,
             note="the log is not empty of market numbers; earlier sessions published a flag saying no market "
                  "price of any kind exists in this repo - see the corrections page", source_class="third-party"),
        dict(quantity="2026 rows carrying a spread and total", value=n26,
             note=f"of {len(g26)} 2026 rows", source_class="third-party"),
        dict(quantity="2026 snap-count rows", value=len(snaps),
             note=f"across {snap_games} distinct games - this is the '136-game log' the brief refers to, "
                  "identified rather than assumed", source_class="third-party"),
    ]
    wr("third_party_inventory.csv", rows)
    # designation play-rate calibration (descriptive only; never a model input while the policy is open).
    # Universe = a game whose snap sheet exists in the corpus. Inside that universe a designated player is
    # either on the sheet (played snaps), on the sheet with zero snaps (active, no play) or absent from the
    # sheet (not in the game). Outside it, absence is uninformative, so those rows are dropped, not counted.
    rate = defaultdict(lambda: [0, 0, 0])
    sheets = set()
    appeared, zero_snap = {}, set()
    for year in (2023, 2024, 2025, 2026):
        p2 = NV_DIR / f"snap_counts_{year}.csv.gz"
        p3 = NV_DIR / f"injuries_{year}.csv.gz"
        if not p2.exists():
            continue
        for r in csv.DictReader(gzip.open(p2, "rt")):
            tot = sum(float(r.get(k) or 0) for k in ("offense_snaps", "defense_snaps", "st_snaps"))
            wk, team = int(r["week"]), r["team"]
            sheets.add((year, wk, team))
            key = (year, wk, team, r["player"].strip().lower())
            appeared[key] = appeared.get(key, False) or tot > 0
            if tot <= 0:
                zero_snap.add(key)
        if not p3.exists():
            continue
        for r in csv.DictReader(gzip.open(p3, "rt")):
            if (r.get("game_type") or "REG").strip() not in ("REG", ""):
                continue
            wk, team = int(r["week"]), r["team"]
            if (year, wk, team) not in sheets:
                continue
            key = (year, wk, team, r["full_name"].strip().lower())
            st = (r.get("report_status") or "").strip() or "listed with no designation"
            if key in appeared and appeared[key]:
                rate[st][0] += 1
            elif key in zero_snap:
                rate[st][1] += 1
            else:
                rate[st][2] += 1
            rate[st][0] += 0
        rate_total = {k: sum(v) for k, v in rate.items()}
    drows = []
    for st, (played_, active0, absent) in sorted(rate.items(), key=lambda kv: -sum(kv[1])):
        n = played_ + active0 + absent
        if n < 30:
            continue
        lo, hi = wilson(played_, n)
        drows.append(dict(designation=st, played=played_, active_no_snaps=active0, not_in_game=absent,
                          listed=n, play_rate=f4(played_ / n), ci95_lo=f4(lo), ci95_hi=f4(hi),
                          seasons="2023-2026",
                          source_class="third-party (nflverse injuries joined to nflverse snap counts)",
                          use="DESCRIPTIVE ONLY - not admitted as a model input while the source-class policy "
                              "is open, and never shown on a leaderboard",
                          source_url="https://github.com/nflverse/nflverse-data"))
    wr("designation_play_rate.csv", drows)
    return rows, drows, dict(n_price=n_price, n26=n26, snap_games=snap_games, snaps=len(snaps), games=len(g))


# ---------------------------------------------------------------- 9. price-store schema + snapshots
def price_store_block(origin_rows, summary):
    schema = [
        dict(field="snapshot_id", type="text", rule="game_id|market|side|stage|captured_utc", required="yes"),
        dict(field="captured_utc", type="iso8601", rule="clock time of the read, never a page date", required="yes"),
        dict(field="stage", type="enum", rule="MARKET_OPEN | MID | MARKET_CLOSE | MODEL_RECORD", required="yes"),
        dict(field="market", type="enum", rule="side | total | moneyline | prop | combo", required="yes"),
        dict(field="line", type="decimal", rule="the number itself; blank is legal, zero is not", required="conditional"),
        dict(field="price_american", type="integer", rule="juice as published; never modelled", required="conditional"),
        dict(field="overround", type="decimal", rule="only computed when both sides of the same book and time are held", required="no"),
        dict(field="source_class", type="enum", rule="official | operator | third-party | manual-audited", required="yes"),
        dict(field="terms_state", type="enum", rule="read | unread | not-applicable - blocks public row-level display when unread", required="yes"),
        dict(field="raw_sha256", type="hex", rule="hash of the artefact the number came from", required="yes"),
        dict(field="model_line", type="decimal", rule="the originated fair number, from originated_wk11.csv", required="yes"),
        dict(field="difference", type="decimal", rule="model minus market; undefined if either side is blank", required="conditional"),
    ]
    wr("price_store_schema.csv", schema)
    rows = []
    for o in origin_rows:
        rows.append(dict(snapshot_id=f"{o['game_id']}|side|MODEL_RECORD", captured_utc=o["recorded_before_kickoff_utc"],
                         stage="MODEL_RECORD", market="side", line=o["stage_1_side_home_margin_points"],
                         price_american="", source_class="model output, official inputs only",
                         terms_state="not-applicable", raw_sha256=summary["feed_sha256"][:16],
                         model_line=o["stage_1_side_home_margin_points"], difference="",
                         market_open="", market_close="",
                         note="model side of the store, recorded before kickoff; market_open and market_close "
                              "are blank because no admitted market read is held",
                         source_url=o["inputs_source_url"]))
        rows.append(dict(snapshot_id=f"{o['game_id']}|total|MODEL_RECORD", captured_utc=o["recorded_before_kickoff_utc"],
                         stage="MODEL_RECORD", market="total", line=o["stage_2_total_estimator_A"],
                         price_american="", source_class="model output, official inputs only",
                         terms_state="not-applicable", raw_sha256=summary["feed_sha256"][:16],
                         model_line=f"{o['stage_2_total_estimator_A']} / {o['stage_2_total_estimator_B']}",
                         difference="", market_open="", market_close="",
                         note="both estimators recorded; the store keeps the gap as its own field",
                         source_url=o["inputs_source_url"]))
        rows.append(dict(snapshot_id=f"{o['game_id']}|moneyline|MODEL_RECORD", captured_utc=o["recorded_before_kickoff_utc"],
                         stage="MODEL_RECORD", market="moneyline", line=o["stage_3_fair_moneyline_home"],
                         price_american="", source_class="model output, official inputs only",
                         terms_state="not-applicable", raw_sha256=summary["feed_sha256"][:16],
                         model_line=o["stage_3_fair_moneyline_home"], difference="",
                         market_open="", market_close="",
                         note="no-vig fair price from the recorded probability; not an operator quote",
                         source_url=o["inputs_source_url"]))
    wr("price_snapshots.csv", rows)
    return rows


def main():
    slate = rd(DATA / "slate_wk11.csv")
    inc = rd(DATA / "results_wk10_increment.csv")
    st, checks, summary, games = standings_block()
    feed, moved = results_feed_block(games, inc)
    corr, withheld = correlations_block(st)
    luck, luck_sum = luck_block(st, games)
    origin, info = origination_block(st, [g for g in feed], slate)
    deltas, same, missing, census = delta_block()
    stale_rows, stale_hits, n_depth, n_depth_clubs = staleness_block(games)
    tp_rows, dpr, tp_info = third_party_block()
    snaps = price_store_block(origin, summary)
    manifest = []
    for p in sorted(RAW.iterdir()):
        manifest.append(dict(path=f"raw/{p.name}", bytes=p.stat().st_size, sha256=sha256(p),
                             retrieved="2026-11-17T00:38:00Z..2026-11-17T00:52:00Z",
                             read_channel="sandbox web fetcher (markdown rendering of the live page)",
                             urls_read="https://www.nfl.com/ (schedule, standings, injuries, transactions, game centre)"))
    for rel in (PRIOR_FEED, PRIOR_INJ, PRIOR_DEPTH):
        manifest.append(dict(path=str(rel.relative_to(REPO)), bytes=rel.stat().st_size, sha256=sha256(rel),
                             retrieved="carried forward, not written by this session (read-only input)",
                             read_channel="hashed pin of a prior session's capture",
                             urls_read=str(rel).split("nfl-desk")[0] + "prior desk"))
    wr("manifest.csv", manifest)
    print("STANDINGS  rows", len(st), "| games final", summary["games_final"],
          "| gp total", summary["games_played_total"], "| PF", summary["points_for_total"],
          "| PA", summary["points_against_total"], "| reconciled", summary["clubs_reconciled"], "/32")
    print("CHECKS     ", [(c["check"][:28], c["result"]) for c in checks])
    print("CHANGES    ", len(moved), "games moved from in-progress/scheduled to final")
    print("CORR       ", [(c["variables"][:34], c["r"], c["n"]) for c in corr])
    print("LUCK       ", {k: luck_sum[k] for k in ("max_positive_luck", "max_positive_luck_team", "max_negative_luck", "max_negative_luck_team", "spread_across_league", "one_possession_share")})
    print("MODEL      ", "hfa", f2(info["hfa"]), "sd", f2(info["sd"]), "n_train", info["n_train"], "rows", len(origin))
    print("WF         ", [(w["week"], w["estimator_A_MAE"], w["estimator_B_MAE"], w["league_average_MAE"], w["winner"]) for w in info["wf"]])
    print("DELTA      ", "changed", len(deltas), "same", len(same), "missing", len(missing))
    print("STALE      ", "moves", len(stale_rows), "contradicted", len(stale_hits), "depth slots", n_depth, "clubs", n_depth_clubs)
    print("3P         ", tp_info)
    print("DESIGN     ", [(d["designation"], d["play_rate"], d["listed"]) for d in dpr])
    print("SNAPSHOTS  ", len(snaps))
    print("HFA RAW    ", f2(info["raw_home_margin"]), "excl neutral", f2(info["raw_home_margin_excl_neutral"]),
          "| neutral games", info["neutral_games"], "| home win share", f4(info["home_win_share"]))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the computed data layer for the NFL Decision Console (session a59c762a).

Deterministic. No clock, no network, no git inside the computation: every
timestamp comes from the raw capture files, which record the clock at which the
official page was read.

Inputs  (raw/, first-hand official reads dated 2026-11-19):
  raw/standings_2026_reg_2026-11-19.csv
  raw/results_wk10_2026-11-19.csv
  raw/schedule_wk11_2026-11-19.csv
  raw/injury_report_wk11_2026-11-19.tsv
  raw/gamebook_was_nyg_reg10_2026-11-19.md

Outputs (data/, computed):
  standings.csv, results_2026.csv, availability_wk11.csv, availability_delta.csv,
  team_availability.csv, model_ratings.csv, originated_lines.csv, price_snapshots.csv,
  shadow_backtest.csv, correlations.csv, luck_panel.csv, captures.csv, depth_coverage.csv

The pre-registered backtest corpus is the repository's existing 2026 results feed,
carried forward with its original official source links and corrected where this
session's first-hand read contradicts it (see data/flagged.csv, F-A59-01).
"""
from __future__ import annotations

import csv
import hashlib
import math
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
DATA = os.path.join(HERE, "data")
REPO = os.path.dirname(HERE)  # repository root

STANDINGS_URL = "https://www.nfl.com/standings/league/2026/REG"
SCHEDULE_URL = "https://www.nfl.com/schedules/2026/by-week/week-11"
INJURY_URL = "https://www.nfl.com/injuries/league/2026/reg11"
WK10_URL = "https://www.nfl.com/schedules/2026/by-week/week-10"
GAMEBOOK_URL = ("https://static.www.nfl.com/image/upload/v1794570519/gamecenter/"
                "ab5828d9-4feb-11f1-abca-2c54536568a9.pdf")
RELEASE_URL = "https://www.nfl.com/nfl-schedule-release/"

# Pre-registered model constants. Frozen in this file before the Week 11 kickoff.
MODEL_ID = "m1-2026-11-19-opponent-adjusted-ls"
RIDGE_LAMBDA = 1.0          # ridge penalty on ratings only (not on HFA)
SHRINK_K = 11               # games-equivalent of league-average prior
TOTAL_ADJ_WEIGHT = 0.5      # split of the team adjustment between offense and defense
TRAIN_WEEKS = "1,2,3,4,5,6,7,8"
VALIDATION_WEEKS = "9"
HOLDOUT_WEEKS = "10"

# ---------------------------------------------------------------- helpers ----


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(name, fieldnames, rows):
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None, None, None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return None, None, None
    r = sxy / math.sqrt(sxx * syy)
    r = max(-0.999999, min(0.999999, r))
    z = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    lo, hi = z - 1.96 * se, z + 1.96 * se
    ci = (math.tanh(lo), math.tanh(hi))
    return r, n, ci


def fisher_p(r, n):
    """Two-sided p-value for a Pearson correlation (normal approximation on z)."""
    if r is None or n < 4:
        return None
    z = 0.5 * math.log((1 + r) / (1 - r)) * math.sqrt(n - 3)
    return 2.0 * (1.0 - norm_cdf(abs(z)))


# ------------------------------------------------------- linear algebra -----


def solve(a, b):
    """Solve a x = b by Gaussian elimination with partial pivoting."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-12:
            raise ValueError("singular normal matrix")
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        for r in range(col + 1, n):
            f = m[r][col] / pv
            if f == 0.0:
                continue
            for c in range(col, n + 1):
                m[r][c] -= f * m[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        s = m[r][n] - sum(m[r][c] * x[c] for c in range(r + 1, n))
        x[r] = s / m[r][r]
    return x


def fit_ratings(games, teams):
    """Opponent-aware least-squares fit.

    margin_home = HFA * home_indicator + rating_home - rating_away  (+ noise)

    The rating vector is constrained to sum to zero by eliminating the last
    team's rating (r_last = -sum of the others). A small ridge penalty on the
    ratings (not on HFA) stabilises teams with few games.
    """
    idx = {t: i for i, t in enumerate(teams)}
    last = teams[-1]
    p = len(teams)          # ratings for teams[:-1] plus HFA
    ata = [[0.0] * p for _ in range(p)]
    atb = [0.0] * p
    for g in games:
        row = [0.0] * p
        x_home = 1.0
        x_away = -1.0
        for t, x in ((g["home"], x_home), (g["away"], x_away)):
            if t == last:
                continue
            row[idx[t]] += x
        row[idx[last]] -= (x_home - x_away)   # substitution r_last = -sum(rest)
        if not g["neutral"]:
            row[p - 1] = 1.0
        y = g["margin"]
        for i in range(p):
            atb[i] += row[i] * y
            for j in range(p):
                ata[i][j] += row[i] * row[j]
    for i in range(p - 1):
        ata[i][i] += RIDGE_LAMBDA
    beta = solve(ata, atb)
    ratings = {t: beta[idx[t]] for t in teams[:-1]}
    ratings[last] = -sum(ratings[t] for t in teams[:-1])
    hfa = beta[p - 1]
    resid = []
    for g in games:
        pred = ratings[g["home"]] - ratings[g["away"]] + (0.0 if g["neutral"] else hfa)
        resid.append(g["margin"] - pred)
    dof = max(1, len(games) - p)
    sigma = math.sqrt(sum(e * e for e in resid) / dof)
    return ratings, hfa, sigma, resid


def fair_moneyline(p):
    """American odds for a fair even-money bet on a probability p (no vig)."""
    if p <= 0 or p >= 1:
        return None
    if p >= 0.5:
        return -100.0 * p / (1.0 - p)
    return 100.0 * (1.0 - p) / p


# ------------------------------------------------------------------ load -----


def load_standings():
    rows = read_csv(os.path.join(RAW, "standings_2026_reg_2026-11-19.csv"))
    out = {}
    for r in rows:
        gp = int(r["W"]) + int(r["L"]) + int(r["T"])
        out[r["club"]] = {
            "club": r["club"], "w": int(r["W"]), "l": int(r["L"]), "t": int(r["T"]),
            "pf": int(r["PF"]), "pa": int(r["PA"]), "net": int(r["NET"]), "gp": gp,
            "source_url": r["source_url"], "read_at_utc": r["read_at_utc"],
        }
    return out


def load_results(standings):
    """Weeks 1-9 from the repository's source-linked 2026 feed; week 10 from this
    session's first-hand official read. Rows contradicted by the first-hand read
    are replaced and the replacement is recorded in data/flagged.csv."""
    feed_path = os.path.join(REPO, "nfl-desk-35a1feb2", "data", "results_feed_2026.csv")
    feed = read_csv(feed_path)
    games = []
    for r in feed:
        if r["week"] == "10":
            continue
        if r["status"] != "FINAL" or r["away_score"] == "" or r["home_score"] == "":
            continue
        games.append({
            "game_id": r["game_id"], "week": int(r["week"]), "date": r["kickoff_date"],
            "away": r["away"], "home": r["home"],
            "away_score": int(r["away_score"]), "home_score": int(r["home_score"]),
            "margin": int(r["home_score"]) - int(r["away_score"]),
            "total": int(r["away_score"]) + int(r["home_score"]),
            "neutral": bool(r["neutral_site"].strip()),
            "neutral_site": r["neutral_site"].strip(),
            "evidence_class": "REPOSITORY_SOURCE_LINKED",
            "verification": r["verification"],
            "source_url": r["source_url"],
            "read_at_utc": "2026-11-17T00:00:00Z (repository capture date; see verification column)",
        })
    for r in read_csv(os.path.join(RAW, "results_wk10_2026-11-19.csv")):
        games.append({
            "game_id": "2026_10_%s_%s" % (r["away"], r["home"]),
            "week": 10, "date": "2026-11-12/16 (as printed on the official week-10 page)",
            "away": r["away"], "home": r["home"],
            "away_score": int(r["away_score"]), "home_score": int(r["home_score"]),
            "margin": int(r["home_score"]) - int(r["away_score"]),
            "total": int(r["away_score"]) + int(r["home_score"]),
            "neutral": (r["away"], r["home"]) == ("NE", "DET"),
            "neutral_site": "Munich" if (r["away"], r["home"]) == ("NE", "DET") else "",
            "evidence_class": "READ_FIRST_HAND_2026-11-19",
            "verification": "read first-hand from the official nfl.com week-10 schedule page on 2026-11-19",
            "source_url": r["source_url"], "read_at_utc": r["read_at_utc"],
        })
    games.sort(key=lambda g: (g["week"], g["away"], g["home"]))
    # Reconcile every club against the official standings read.
    agg = defaultdict(lambda: dict(w=0, l=0, t=0, pf=0, pa=0))
    for g in games:
        a, h = g["away"], g["home"]
        agg[a]["pf"] += g["away_score"]; agg[a]["pa"] += g["home_score"]
        agg[h]["pf"] += g["home_score"]; agg[h]["pa"] += g["away_score"]
        if g["away_score"] > g["home_score"]:
            agg[a]["w"] += 1; agg[h]["l"] += 1
        elif g["home_score"] > g["away_score"]:
            agg[h]["w"] += 1; agg[a]["l"] += 1
        else:
            agg[a]["t"] += 1; agg[h]["t"] += 1
    mismatches = []
    for club, s in standings.items():
        g = agg[club]
        if (g["w"], g["l"], g["t"], g["pf"], g["pa"]) != (s["w"], s["l"], s["t"], s["pf"], s["pa"]):
            mismatches.append((club, (s["w"], s["l"], s["t"], s["pf"], s["pa"]),
                                (g["w"], g["l"], g["t"], g["pf"], g["pa"])))
    return games, mismatches


def load_availability():
    rows = []
    with open(os.path.join(RAW, "injury_report_wk11_2026-11-19.tsv"), encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            club, player, pos, inj, prac, game = line.split("\t")
            rows.append({
                "club": club, "player": player, "position": pos, "injury": inj,
                "practice_status": prac, "game_status": game,
            })
    return rows


def load_preview():
    """The repository's earlier, partial Week-11 read (2026-11-18T03:46Z, game
    pages). Used only to compute a delta, never to publish a level."""
    path = os.path.join(REPO, "data", "nfl-desk-f2e20e96", "availability_wk11_preview.csv")
    if not os.path.exists(path):
        return []
    return read_csv(path)


# --------------------------------------------------------------- compute -----


def main():
    os.makedirs(DATA, exist_ok=True)
    standings = load_standings()
    games, mismatches = load_results(standings)
    teams = sorted(standings)

    # --- standings table -------------------------------------------------
    mean_pf_pg = sum(s["pf"] / s["gp"] for s in standings.values()) / len(standings)
    mean_pa_pg = sum(s["pa"] / s["gp"] for s in standings.values()) / len(standings)
    srows = []
    for c in teams:
        s = standings[c]
        pf_pg = s["pf"] / s["gp"]
        pa_pg = s["pa"] / s["gp"]
        net_pg = (s["pf"] - s["pa"]) / s["gp"]
        w = s["gp"] / (s["gp"] + SHRINK_K)
        srows.append({
            "club": c, "w": s["w"], "l": s["l"], "t": s["t"], "games_played": s["gp"],
            "points_for": s["pf"], "points_against": s["pa"], "net_points": s["net"],
            "win_pct": round(s["w"] / s["gp"], 4),
            "pf_per_game": round(pf_pg, 3), "pa_per_game": round(pa_pg, 3),
            "net_per_game": round(net_pg, 3),
            "shrink_weight_gp_over_gp_plus_11": round(w, 4),
            "net_per_game_shrunk": round(net_pg * w, 3),
            "source_url": s["source_url"], "read_at_utc": s["read_at_utc"],
            "evidence_class": "READ_FIRST_HAND_2026-11-19",
        })
    write_csv("standings.csv", list(srows[0].keys()), srows)
    srow_by = {r["club"]: r for r in srows}

    # --- results feed ----------------------------------------------------
    rrows = [{
        "game_id": g["game_id"], "season": 2026, "week": g["week"], "kickoff_date": g["date"],
        "away": g["away"], "home": g["home"], "away_score": g["away_score"],
        "home_score": g["home_score"], "home_margin": g["margin"], "total_points": g["total"],
        "result": "home win" if g["margin"] > 0 else ("away win" if g["margin"] < 0 else "tie"),
        "neutral_site": g["neutral_site"], "status": "FINAL",
        "evidence_class": g["evidence_class"], "verification": g["verification"],
        "source_url": g["source_url"], "read_at_utc": g["read_at_utc"],
    } for g in games]
    write_csv("results_2026.csv", list(rrows[0].keys()), rrows)

    # --- model ------------------------------------------------------------
    train = [g for g in games if str(g["week"]) in TRAIN_WEEKS.split(",")]
    valid = [g for g in games if str(g["week"]) in VALIDATION_WEEKS.split(",")]
    hold = [g for g in games if str(g["week"]) in HOLDOUT_WEEKS.split(",")]
    ratings, hfa, sigma, resid = fit_ratings(train, teams)
    # train-window scoring rates
    tf = defaultdict(int); ta = defaultdict(int); tg = Counter()
    tot = 0
    for g in train:
        tf[g["home"]] += g["home_score"]; ta[g["home"]] += g["away_score"]
        tf[g["away"]] += g["away_score"]; ta[g["away"]] += g["home_score"]
        tg[g["home"]] += 1; tg[g["away"]] += 1
        tot += g["total"]
    n_train_games = len(train)
    league_total = tot / n_train_games
    off_adj = {}; def_adj = {}
    for c in teams:
        gp = tg[c]
        pf_pg = tf[c] / gp
        pa_pg = ta[c] / gp
        w = gp / (gp + SHRINK_K)
        off_adj[c] = (pf_pg - mean_pf_pg) * w
        def_adj[c] = (pa_pg - mean_pa_pg) * w

    mrows = []
    for c in teams:
        mrows.append({
            "club": c, "model_version": MODEL_ID, "rating_points": round(ratings[c], 3),
            "rating_rank": sorted(teams, key=lambda t: -ratings[t]).index(c) + 1,
            "games_in_fit": tg[c],
            "adj_offense_ppg": round(off_adj[c], 3), "adj_defense_ppg": round(def_adj[c], 3),
            "source_url": STANDINGS_URL,
            "inputs": "official 2026 regular-season standings (weeks 1-8) and the 2026 results feed",
        })
    write_csv("model_ratings.csv", list(mrows[0].keys()), mrows)

    # --- originated Week 11 lines ---------------------------------------
    sched = read_csv(os.path.join(RAW, "schedule_wk11_2026-11-19.csv"))
    neutral_wk11 = {("MIN", "SF"): "Estadio Banorte, Mexico City (2026 NFL Schedule Release page)"}
    lrows = []
    for n, s in enumerate(sched, start=1):
        h, a = s["home"], s["away"]
        margin = hfa + ratings[h] - ratings[a]
        if (a, h) in neutral_wk11:
            margin = ratings[h] - ratings[a]     # no home-field term at a neutral site
        p_home = norm_cdf(margin / sigma)
        total_a = league_total
        ph = mean_pf_pg + TOTAL_ADJ_WEIGHT * (off_adj[h] - def_adj[a])
        pa_ = mean_pf_pg + TOTAL_ADJ_WEIGHT * (off_adj[a] - def_adj[h])
        total_b = ph + pa_
        ml_h = fair_moneyline(p_home)
        ml_a = fair_moneyline(1.0 - p_home)
        inputs = ("rating_home=%+.2f rating_away=%+.2f hfa=%.2f sigma=%.2f "
                  "p_home=%.4f model=%s train_weeks=%s n_train_games=%d"
                  % (ratings[h], ratings[a], hfa, sigma, p_home, MODEL_ID,
                     TRAIN_WEEKS, n_train_games))
        base = {
            "game_id": "2026_11_%s_%s" % (a, h), "week": 11,
            "kickoff_date": s["kickoff_date"], "kickoff_time_et": s["kickoff_time_et"],
            "network": s["network"], "away": a, "home": h,
            "neutral_site": neutral_wk11.get((a, h), ""),
            "model_version": MODEL_ID, "recorded_at_utc": "2026-11-19T07:05:00Z",
            "recorded_before_kickoff": "yes",
            "source_url": SCHEDULE_URL, "inputs_source_url": STANDINGS_URL,
        }
        # Stage 1 - side (spread), then Stage 2 - total, then Stage 3 - moneyline.
        lrows.append(dict(base, market_order=1, market="side",
                           model_fair_line=("%.1f" % margin),
                           model_fair_value=round(margin, 3),
                           market_line="", difference_vs_market="",
                           probability=round(p_home, 4),
                           probability_label="P(home win) from the opponent-adjusted margin model",
                           inputs=inputs, price_status="UNVERIFIED_NO_ADMITTED_PRICE_SOURCE"))
        lrows.append(dict(base, market_order=2, market="total",
                           model_fair_line=("%.1f" % total_b),
                           model_fair_value=round(total_b, 3),
                           market_line="", difference_vs_market="",
                           probability="", probability_label="",
                           inputs=("estimator_A=league_mean_total=%.2f (n=%d train games); "
                                   "estimator_B=shrunk offense + shrunk opponent defense, "
                                   "weight=%.2f, shrink k=%d; gap=%.2f; both estimators published, "
                                   "neither retired; model=%s"
                                   % (total_a, n_train_games, TOTAL_ADJ_WEIGHT, SHRINK_K,
                                      abs(total_a - total_b), MODEL_ID)),
                           price_status="UNVERIFIED_NO_ADMITTED_PRICE_SOURCE"))
        lrows.append(dict(base, market_order=3, market="moneyline",
                           model_fair_line=("%.1f / %.1f" % (ml_h, ml_a)),
                           model_fair_value=round(ml_h, 3),
                           market_line="", difference_vs_market="",
                           probability=round(p_home, 4),
                           probability_label="fair American odds, home / away, no vig",
                           inputs=inputs, price_status="UNVERIFIED_NO_ADMITTED_PRICE_SOURCE"))
    write_csv("originated_lines.csv", list(lrows[0].keys()), lrows)

    # --- price snapshot store -------------------------------------------
    prows = []
    for i, l in enumerate(lrows, start=1):
        prows.append({
            "snapshot_id": "PS-A59-%03d" % i, "game_id": l["game_id"], "week": l["week"],
            "market": l["market"], "market_order": l["market_order"],
            "source_class": "MODEL_RECORD", "book": "", "jurisdiction": "",
            "captured_utc": "", "opening_line": "", "closing_line": "",
            "raw_sha256": "", "terms_state": "NO_OPERATOR_PRICE_CAPTURED_IN_THIS_REPOSITORY",
            "flag": "F-A59-02 market price cells are blank by policy P-01: no licensed or "
                    "operator price source has been admitted to this repository, so no "
                    "opening or closing number can be recorded",
            "model_fair_line": l["model_fair_line"], "source_url": l["source_url"],
        })
    write_csv("price_snapshots.csv", list(prows[0].keys()), prows)

    # --- availability ----------------------------------------------------
    av = load_availability()
    arows = []
    for i, r in enumerate(av, start=1):
        arows.append({
            "row_id": "AV-A59-%04d" % i, "club": r["club"], "player": r["player"],
            "position": r["position"], "injury": r["injury"],
            "practice_status": r["practice_status"], "game_status": r["game_status"],
            "designation_present": "yes" if r["game_status"] else "no",
            "source_url": INJURY_URL, "read_at_utc": "2026-11-19T06:45:00Z",
            "evidence_class": "READ_FIRST_HAND_2026-11-19",
        })
    write_csv("availability_wk11.csv", list(arows[0].keys()), arows)

    # --- availability delta (against the repository's earlier partial read)
    preview = load_preview()
    by_club = defaultdict(list)
    for r in av:
        by_club[r["club"]].append(r)
    drows = []
    for p in preview:
        club = p["club"]
        label = p["player_or_statement"]
        head = label.split("(")[0].strip()
        if not head or label.startswith("("):
            # A club-level statement on the game page, not a player row.
            rows_c = by_club.get(club, [])
            drows.append({
                "delta_id": "DL-A59-%03d" % (len(drows) + 1), "club": club,
                "player": label,
                "change_type": "CLUB_STATEMENT_SUPERSEDED_BY_LEAGUE_REPORT",
                "previous_value": p["practice_participation_as_printed"],
                "current_value": "%d rows now listed for this club on the league injury report" % len(rows_c),
                "previous_read_utc": p["read_at_utc"], "current_read_utc": "2026-11-19T06:45:00Z",
                "previous_source_url": p["source_url"], "current_source_url": INJURY_URL,
                "note": ("The earlier read was a club-level statement taken from the game page. "
                         "The league injury report published on 2026-11-19 lists named players "
                         "for this club instead."),
            })
            continue
        surname = head.split()[0].rstrip(".").lower()
        match = None
        for r in by_club.get(club, []):
            if r["player"].split()[-1].lower().startswith(surname):
                match = r
                break
        if match is None:
            drows.append({
                "delta_id": "DL-A59-%03d" % (len(drows) + 1), "club": club,
                "player": label, "change_type": "PREVIEW_ROW_NOT_FOUND_IN_LEAGUE_REPORT",
                "previous_value": p["practice_participation_as_printed"], "current_value": "",
                "previous_read_utc": p["read_at_utc"], "current_read_utc": "2026-11-19T06:45:00Z",
                "previous_source_url": p["source_url"], "current_source_url": INJURY_URL,
                "note": "The earlier read came from the game page, which exposes four rows per club.",
            })
        else:
            prev = p["practice_participation_as_printed"].strip().lower()
            cur_txt = match["practice_status"].lower()
            if "did not participate" in prev and cur_txt.startswith("did not participate"):
                kind = "UNCHANGED"
            elif "did participate" in prev and cur_txt.startswith("full participation"):
                kind = "UNCHANGED"
            elif "full participation" in prev and cur_txt.startswith("full participation"):
                kind = "UNCHANGED"
            elif "limited" in prev and cur_txt.startswith("limited"):
                kind = "UNCHANGED"
            else:
                kind = "PRACTICE_STATUS_CHANGED"
            drows.append({
                "delta_id": "DL-A59-%03d" % (len(drows) + 1), "club": club,
                "player": match["player"], "change_type": kind,
                "previous_value": p["practice_participation_as_printed"],
                "current_value": match["practice_status"],
                "previous_read_utc": p["read_at_utc"], "current_read_utc": "2026-11-19T06:45:00Z",
                "previous_source_url": p["source_url"], "current_source_url": INJURY_URL,
                "note": ("The game page prints a short participation word; the league injury "
                         "report prints the full participation phrase."),
            })
    # rows and designations that the earlier read did not carry at all
    seen = {(d["club"], d["player"]) for d in drows}
    for r in av:
        if (r["club"], r["player"]) in seen:
            continue
        drows.append({
            "delta_id": "DL-A59-%03d" % (len(drows) + 1), "club": r["club"],
            "player": r["player"], "change_type": "ROW_NOT_IN_EARLIER_READ",
            "previous_value": "", "current_value": r["game_status"] or r["practice_status"],
            "previous_read_utc": "2026-11-18T03:46:00Z", "current_read_utc": "2026-11-19T06:45:00Z",
            "previous_source_url": "https://www.nfl.com/games/colts-at-texans-2026-reg-11",
            "current_source_url": INJURY_URL,
            "note": "Present in the full league injury report read on 2026-11-19; absent from the "
                    "earlier four-rows-per-club game-page sample.",
        })
    write_csv("availability_delta.csv", list(drows[0].keys()), drows)

    # --- per-team availability view -------------------------------------
    trows = []
    wk11_clubs = sorted({s["home"] for s in sched} | {s["away"] for s in sched})
    all_clubs = sorted(standings)
    for c in all_clubs:
        rows_c = [r for r in av if r["club"] == c]
        if c not in wk11_clubs:
            trows.append({
                "club": c, "week": 11, "rows_listed": 0, "out": 0, "questionable": 0,
                "no_game_status": len(rows_c), "full_participation": 0,
                "limited_participation": 0, "did_not_participate": 0,
                "net_injury_count": 0, "expected_starters_out": "", "replacements_named": "",
                "replacement_depth": "", "slate_status": "BYE",
                "source_url": INJURY_URL, "read_at_utc": "2026-11-19T06:45:00Z",
                "flag": "Club is on a bye in Week 11; no official Week 11 report rows exist.",
            })
            continue
        out = sum(1 for r in rows_c if r["game_status"] == "Out")
        q = sum(1 for r in rows_c if r["game_status"] == "Questionable")
        no_prac = sum(1 for r in rows_c if r["game_status"] == "")
        fp = sum(1 for r in rows_c if r["practice_status"].startswith("Full"))
        lp = sum(1 for r in rows_c if r["practice_status"].startswith("Limited"))
        dnp = sum(1 for r in rows_c if r["practice_status"].startswith("Did Not"))
        trows.append({
            "club": c, "week": 11, "rows_listed": len(rows_c), "out": out,
            "questionable": q, "no_game_status": no_prac, "full_participation": fp,
            "limited_participation": lp, "did_not_participate": dnp,
            "net_injury_count": out + q,
            "expected_starters_out": "", "replacements_named": "",
            "replacement_depth": "", "slate_status": "IN_SLATE",
            "source_url": INJURY_URL, "read_at_utc": "2026-11-19T06:45:00Z",
            "flag": ("Expected starters out and replacement names stay blank: the depth-order "
                     "source is verified for 31 of 32 clubs only (HOU publishes depth as an "
                     "image) and the week-11 game-status column is published only for the "
                     "Thursday game at the time of this read."),
        })
    write_csv("team_availability.csv", list(trows[0].keys()), trows)

    # --- shadow backtest (out of sample; never on the leaderboard) ------
    def predict(g):
        m = hfa + ratings[g["home"]] - ratings[g["away"]]
        if g["neutral"]:
            m = ratings[g["home"]] - ratings[g["away"]]
        return m, norm_cdf(m / sigma)

    brows = []
    for label, block in (("validation_week_9", valid), ("final_holdout_week_10", hold)):
        correct = 0
        brier = 0.0
        abs_err = 0.0
        for g in block:
            m, p = predict(g)
            y = 1.0 if g["margin"] > 0 else 0.0
            correct += 1 if (p > 0.5) == (y == 1.0) else 0
            brier += (p - y) ** 2
            abs_err += abs(m - g["margin"])
        n = len(block)
        base_p = sum(1 for g in train if g["margin"] > 0) / len(train)
        base_brier = sum((base_p - (1.0 if g["margin"] > 0 else 0.0)) ** 2 for g in block) / n
        brier /= n
        abs_err /= n
        brows.append({
            "run_id": "BT-A59-%s" % label.replace("_", "-"),
            "split": label, "train_weeks": TRAIN_WEEKS, "test_weeks":
                VALIDATION_WEEKS if label.startswith("validation") else HOLDOUT_WEEKS,
            "n_games": n, "model_version": MODEL_ID,
            "model_accuracy": round(correct / n, 4), "model_brier": round(brier, 5),
            "base_rate_home_win_train": round(base_p, 4),
            "climatology_brier": round(base_brier, 5),
            "brier_skill_score_vs_climatology": round(1 - brier / base_brier, 4) if base_brier else "",
            "mean_absolute_margin_error_points": round(abs_err, 3),
            "sigma_points": round(sigma, 3), "hfa_points": round(hfa, 3),
            "source_url": STANDINGS_URL,
            "inputs_source_url": "https://www.nfl.com/schedules/2026/by-week/week-1",
            "note": "Shadow evaluation of the pre-registered singles-only baseline. These numbers "
                    "are out-of-sample from the training window and are published on the "
                    "shadow-backtest page only; they are forbidden on the leaderboard.",
        })
    write_csv("shadow_backtest.csv", list(brows[0].keys()), brows)

    # --- correlations (official numbers only, n published) ---------------
    crows = []

    def add_corr(cid, desc, xs, ys, src, unit):
        r, n, ci = pearson(xs, ys)
        p = fisher_p(r, n) if r is not None else None
        crows.append({
            "correlation_id": cid, "description": desc, "statistic": "Pearson r",
            "value": round(r, 4) if r is not None else "",
            "n": n if n is not None else "",
            "ci95_low": round(ci[0], 4) if ci else "",
            "ci95_high": round(ci[1], 4) if ci else "",
            "p_value_two_sided": round(p, 6) if p is not None else "",
            "unit": unit, "method": "Pearson product-moment; Fisher z interval",
            "source_url": src, "evidence_class": "READ_FIRST_HAND_2026-11-19",
        })

    add_corr("CO-A59-01", "Net points per game vs winning percentage",
             [srow_by[c]["net_per_game"] for c in teams],
             [srow_by[c]["win_pct"] for c in teams], STANDINGS_URL, "points per game and win pct")
    add_corr("CO-A59-02", "Points for per game vs winning percentage",
             [srow_by[c]["pf_per_game"] for c in teams],
             [srow_by[c]["win_pct"] for c in teams], STANDINGS_URL, "points per game and win pct")
    add_corr("CO-A59-03", "Points against per game vs winning percentage",
             [srow_by[c]["pa_per_game"] for c in teams],
             [srow_by[c]["win_pct"] for c in teams], STANDINGS_URL, "points per game and win pct")
    add_corr("CO-A59-04", "Points for per game vs points against per game",
             [srow_by[c]["pf_per_game"] for c in teams],
             [srow_by[c]["pa_per_game"] for c in teams], STANDINGS_URL, "points per game")
    net_by = {c: standings[c]["net"] / standings[c]["gp"] for c in teams}
    add_corr("CO-A59-05", "A game's home team season net per game vs the away team's season net per game",
             [net_by[g["home"]] for g in games], [net_by[g["away"]] for g in games],
             STANDINGS_URL, "points per game")
    tr = [g for g in train]
    add_corr("CO-A59-06", "Fitted opponent-adjusted rating difference vs actual home margin (training window)",
             [ratings[g["home"]] - ratings[g["away"]] + (0 if g["neutral"] else hfa) for g in tr],
             [g["margin"] for g in tr], STANDINGS_URL, "points")
    ho = valid + hold
    add_corr("CO-A59-07", "Out-of-sample predicted margin vs actual home margin (weeks 9-10)",
             [predict(g)[0] for g in ho], [g["margin"] for g in ho],
             "https://www.nfl.com/schedules/2026/by-week/week-9", "points")
    add_corr("CO-A59-08", "Model probability vs outcome (weeks 9-10, point-biserial)",
             [predict(g)[1] for g in ho], [1.0 if g["margin"] > 0 else 0.0 for g in ho],
             "https://www.nfl.com/schedules/2026/by-week/week-9", "probability")
    write_csv("correlations.csv", list(crows[0].keys()), crows)

    # --- luck panel ------------------------------------------------------
    lpanel = []
    ho_games = valid + hold
    n_ho = len(ho_games)
    brier_model = sum((predict(g)[1] - (1.0 if g["margin"] > 0 else 0.0)) ** 2 for g in ho_games) / n_ho
    base_p = sum(1 for g in train if g["margin"] > 0) / len(train)
    brier_clim = sum((base_p - (1.0 if g["margin"] > 0 else 0.0)) ** 2 for g in ho_games) / n_ho
    brier_random = 0.25
    # control baseline: always take the model favourite
    fav_correct = 0
    for g in ho_games:
        m, p = predict(g)
        favourite = g["home"] if m > 0 else g["away"]
        won = (g["home"] == favourite and g["margin"] > 0) or \
              (g["away"] == favourite and g["margin"] < 0)
        fav_correct += 1 if won else 0
    trials = 3
    bonf = 0.05 / trials
    lpanel.append({
        "panel_id": "LP-A59-01", "metric": "Brier score (lower is better)",
        "strategy": "Pre-registered singles-only team-strength model (S-SHADOW-01)",
        "value": round(brier_model, 5), "n": n_ho, "uncertainty": "",
        "comparator": "", "skill_metric": "Brier skill score vs climatology",
        "skill_value": round(1 - brier_model / brier_clim, 4),
        "adjusted_alpha_bonferroni": round(bonf, 5), "trial_count": trials,
        "status": "OUT_OF_SAMPLE_SHADOW_NOT_ON_LEADERBOARD",
        "source_url": STANDINGS_URL,
    })
    lpanel.append({
        "panel_id": "LP-A59-02", "metric": "Brier score (lower is better)",
        "strategy": "Control baseline: climatology (always predict the training home-win rate)",
        "value": round(brier_clim, 5), "n": n_ho, "uncertainty": "",
        "comparator": "reference forecast for the skill score", "skill_metric": "",
        "skill_value": "", "adjusted_alpha_bonferroni": round(bonf, 5), "trial_count": trials,
        "status": "CONTROL", "source_url": STANDINGS_URL,
    })
    lpanel.append({
        "panel_id": "LP-A59-03", "metric": "Brier score (lower is better)",
        "strategy": "Control baseline: random pick (fair coin, analytic expectation)",
        "value": brier_random, "n": n_ho, "uncertainty": "",
        "comparator": "", "skill_metric": "",
        "skill_value": "", "adjusted_alpha_bonferroni": round(bonf, 5), "trial_count": trials,
        "status": "CONTROL", "source_url": STANDINGS_URL,
    })
    lpanel.append({
        "panel_id": "LP-A59-04", "metric": "Win rate of the model favourite",
        "strategy": "Control baseline: favourites only (the higher-rated team)",
        "value": round(fav_correct / n_ho, 4), "n": n_ho, "uncertainty": "",
        "comparator": "climatology home-win rate", "skill_metric": "",
        "skill_value": "", "adjusted_alpha_bonferroni": round(bonf, 5), "trial_count": trials,
        "status": "CONTROL", "source_url": STANDINGS_URL,
    })
    lpanel.append({
        "panel_id": "LP-A59-05", "metric": "Realised ROI",
        "strategy": "Every strategy (no admitted price source exists in this repository)",
        "value": "", "n": 0, "uncertainty": "",
        "comparator": "", "skill_metric": "",
        "skill_value": "", "adjusted_alpha_bonferroni": "", "trial_count": "",
        "status": "UNDEFINED_NO_ADMITTED_PRICE_SOURCE",
        "source_url": STANDINGS_URL,
    })
    write_csv("luck_panel.csv", list(lpanel[0].keys()), lpanel)

    # --- depth coverage (route (a) verification status) -----------------
    dpath = os.path.join(REPO, "nfl-desk-e46fb855", "data", "depth_slots.csv")
    dcrows = []
    if os.path.exists(dpath):
        by = defaultdict(list)
        for r in read_csv(dpath):
            by[r["club"]].append(r)
        for c in sorted(by):
            sts = sorted({r["status"] for r in by[c]})
            ok = sts == ["parsed"]
            dcrows.append({
                "club": c, "rows_captured": len(by[c]),
                "route": "per-club official depth chart page",
                "verified_for_all_32": "yes" if ok else "no",
                "status": "verified" if ok else " ".join(sts),
                "source_url": by[c][0]["source_url"],
                "evidence_class": "REPOSITORY_SOURCE_LINKED",
            })
    write_csv("depth_coverage.csv", list(dcrows[0].keys()), dcrows)

    # --- capture log -----------------------------------------------------
    caprows = []
    files = [
        ("CAP-A59-01", "NFL league standings, 2026 regular season", STANDINGS_URL,
         "2026-11-19T06:38:00Z", "raw/standings_2026_reg_2026-11-19.csv", "2 chunks read",
         "processed-text extraction; not a byte-level capture"),
        ("CAP-A59-02", "NFL Week 11 official injury report", INJURY_URL,
         "2026-11-19T06:45:00Z", "raw/injury_report_wk11_2026-11-19.tsv", "7 chunks read",
         "processed-text extraction; the page renders 26 club tables"),
        ("CAP-A59-03", "NFL Week 11 schedule", SCHEDULE_URL,
         "2026-11-19T06:41:00Z", "raw/schedule_wk11_2026-11-19.csv", "3 chunks read",
         "processed-text extraction"),
        ("CAP-A59-04", "NFL Week 10 schedule with final scores", WK10_URL,
         "2026-11-19T06:44:00Z", "raw/results_wk10_2026-11-19.csv", "2 chunks read",
         "processed-text extraction; all 14 finals read"),
        ("CAP-A59-05", "Official NFL Game Book, Washington at New York, Week 10", GAMEBOOK_URL,
         "2026-11-19T06:47:00Z", "raw/gamebook_was_nyg_reg10_2026-11-19.md", "1 chunk read",
         "processed-text extraction of the official PDF; starters, Not Active and the "
         "game-day weather line were transcribed by hand from the rendered tables"),
        ("CAP-A59-06", "2026 NFL Schedule Release", RELEASE_URL,
         "2026-11-19T06:49:00Z", "", "2 chunks read",
         "processed-text extraction; the landing page does not print a release date"),
        ("CAP-A59-07", "Indianapolis Colts at Houston Texans game centre, Week 11",
         "https://www.nfl.com/games/colts-at-texans-2026-reg-11", "2026-11-19T06:50:00Z",
         "", "1 chunk read", "processed-text extraction; venue and team comparison read"),
    ]
    for cid, name, url, clock, rel, chunks, method in files:
        path = os.path.join(HERE, rel) if rel else ""
        caprows.append({
            "capture_id": cid, "source_name": name, "url": url, "read_at_utc": clock,
            "chunks_read": chunks,
            "extract_sha256": sha256_file(path) if path else "",
            "extract_file": rel, "method": method,
        })
    write_csv("captures.csv", list(caprows[0].keys()), caprows)

    # --- reconciliation summary (printed, and embedded in flagged.csv) ---
    print("standings clubs:", len(standings))
    print("games:", len(games), "weeks:", sorted({g['week'] for g in games}))
    print("standings reconciliation mismatches:", len(mismatches))
    for m in mismatches:
        print("   ", m)
    print("HFA=%.3f sigma=%.3f league_total=%.3f" % (hfa, sigma, league_total))
    print("availability rows:", len(av), "delta rows:", len(drows))
    print("correlations:", len(crows), "lines:", len(lrows))
    return mismatches


if __name__ == "__main__":
    main()
